"""
Public Catalog Service — Phase 4.
Handles: Category browsing, product listing with filters,
         JSONB attribute filtering, full-text search, product detail.
All public-facing (no admin auth required).
"""

import math
from decimal import Decimal

from sqlalchemy import Float, Integer, and_, cast, func, or_, select, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.models import (
    AttributeDefinition,
    Category,
    Product,
    ProductImage,
    ProductVariant,
    Review,
    SizeGuide,
)


# ── Custom size sort order (logical, not alphabetical) ──
_SIZE_ORDER = {
    # Standard apparel
    "XS": 0, "S": 1, "M": 2, "L": 3, "XL": 4, "XXL": 5, "XXXL": 6,
    # Age groups (kids)
    "4-6": 10, "7-9": 11, "10-12": 12, "13-15": 13, "16+": 14,
    # Waist sizes
    "26": 20, "28": 21, "30": 22, "32": 23, "34": 24, "36": 25, "38": 26,
}


def _sort_sizes(sizes: list[str]) -> list[str]:
    """Sort sizes in logical order: S→XL, 4-6→16+, 26→38. Unknown sizes go last alphabetically."""
    return sorted(sizes, key=lambda s: (_SIZE_ORDER.get(s, 999), s))


class CatalogServiceError(Exception):
    def __init__(self, message: str, status_code: int = 400):
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class CatalogService:
    def __init__(self, db: AsyncSession):
        self.db = db

    # ══════════════════════════════════════
    # LANDING PAGE DATA
    # ══════════════════════════════════════

    async def get_landing_data(self) -> dict:
        """
        Returns data for the landing page:
        - Featured products (is_featured=True, limit 8)
        - Category cards grouped by gender
        """
        # Featured products
        featured_q = (
            select(Product)
            .where(
                Product.is_featured == True,
                Product.is_active == True,
                Product.deleted_at.is_(None),
            )
            .options(selectinload(Product.images), selectinload(Product.variants))
            .limit(8)
        )
        featured_result = await self.db.execute(featured_q)
        featured = list(featured_result.scalars().unique().all())

        # Categories grouped by gender
        cat_q = (
            select(Category)
            .where(Category.is_active == True, Category.deleted_at.is_(None))
            .order_by(Category.sort_order, Category.name)
        )
        cat_result = await self.db.execute(cat_q)
        categories = list(cat_result.scalars().all())

        gender_groups = {}
        for cat in categories:
            gender_groups.setdefault(cat.gender, []).append(cat)

        return {
            "featured_products": featured,
            "categories_by_gender": gender_groups,
            "all_categories": categories,
        }

    # ══════════════════════════════════════
    # CATEGORY BROWSING
    # ══════════════════════════════════════

    async def browse_categories(
        self,
        gender: str | None = None,
        age_group: str | None = None,
        parent_id: str | None = None,
    ) -> list:
        """Browse categories by gender → age group → subcategory."""
        query = select(Category).where(
            Category.is_active == True, Category.deleted_at.is_(None)
        )
        if gender:
            query = query.where(Category.gender == gender)
        if age_group:
            query = query.where(Category.age_group == age_group)
        if parent_id:
            query = query.where(Category.parent_category_id == parent_id)
        else:
            # Top-level categories only if no parent specified
            if not gender and not age_group:
                query = query.where(Category.parent_category_id.is_(None))

        query = query.order_by(Category.sort_order, Category.name)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_category_by_slug(self, slug: str) -> Category:
        result = await self.db.execute(
            select(Category).where(
                Category.slug == slug,
                Category.is_active == True,
                Category.deleted_at.is_(None),
            )
        )
        cat = result.scalar_one_or_none()
        if not cat:
            raise CatalogServiceError("Category not found.", 404)
        return cat

    # ══════════════════════════════════════
    # PRODUCT LISTING WITH FILTERS
    # ══════════════════════════════════════

    async def list_products(
        self,
        # Category filters
        category_id: str | None = None,
        gender: str | None = None,
        age_group: str | None = None,
        # Standard filters
        size: str | None = None,
        color: str | None = None,
        price_min: Decimal | None = None,
        price_max: Decimal | None = None,
        brand: str | None = None,
        min_rating: int | None = None,
        # JSONB attribute filters (dict: {key: value})
        attribute_filters: dict | None = None,
        # Search
        search: str | None = None,
        # Sort
        sort: str = "newest",
        # Pagination
        page: int = 1,
        page_size: int = 24,
    ) -> dict:
        """
        Main product listing with all filter types.
        Supports JSONB attribute filtering via GIN index.

        Performance note (Session 5, Feb 21 2026):
        Count query is built SEPARATELY without selectinload to avoid
        materializing eager-loaded relations in a subquery.
        """
        # ══ Build shared filter conditions ══
        base_conditions = [
            Product.is_active == True,
            Product.deleted_at.is_(None),
        ]
        needs_category_join = False

        # ── Category filters ──
        if category_id:
            base_conditions.append(Product.category_id == category_id)
        if gender or age_group:
            needs_category_join = True
            if gender:
                base_conditions.append(Category.gender == gender)
            if age_group:
                base_conditions.append(Category.age_group == age_group)

        # ── Standard filters ──
        if brand:
            base_conditions.append(Product.brand.ilike(f"%{brand}%"))

        if price_min is not None:
            base_conditions.append(
                func.coalesce(Product.sale_price, Product.base_price) >= price_min
            )
        if price_max is not None:
            base_conditions.append(
                func.coalesce(Product.sale_price, Product.base_price) <= price_max
            )

        # ── Size/Color filters (require variant subquery) ──
        variant_subquery_clause = None
        if size or color:
            variant_conditions = [
                ProductVariant.deleted_at.is_(None),
                ProductVariant.is_active == True,
                ProductVariant.stock_quantity > 0,
            ]
            if size:
                variant_conditions.append(ProductVariant.size == size)
            if color:
                variant_conditions.append(ProductVariant.color.ilike(f"%{color}%"))

            variant_sq = (
                select(ProductVariant.product_id)
                .where(and_(*variant_conditions))
                .distinct()
                .subquery()
            )
            variant_subquery_clause = Product.id.in_(select(variant_sq))

        # ── JSONB attribute filters (V2.5 key feature) ──
        jsonb_conditions = []
        if attribute_filters:
            for attr_key, attr_value in attribute_filters.items():
                jsonb_conditions.append(
                    Product.attributes[attr_key].astext.ilike(f"%{attr_value}%")
                )

        # ── Full-text search ──
        search_condition = None
        if search:
            search_term = search.strip()
            search_condition = or_(
                Product.title.ilike(f"%{search_term}%"),
                Product.description.ilike(f"%{search_term}%"),
                Product.brand.ilike(f"%{search_term}%"),
                Product.tags.any(search_term),
            )

        # ── Rating filter ──
        rating_subquery_clause = None
        if min_rating:
            rating_sq = (
                select(Review.product_id)
                .group_by(Review.product_id)
                .having(func.avg(cast(Review.rating, Float)) >= min_rating)
                .subquery()
            )
            rating_subquery_clause = Product.id.in_(select(rating_sq))

        # ══════════════════════════════════════
        # COUNT QUERY — lightweight, NO selectinload
        # ══════════════════════════════════════
        count_query = select(func.count(Product.id)).where(*base_conditions)
        if needs_category_join:
            count_query = count_query.join(Category, Product.category_id == Category.id)
        if variant_subquery_clause is not None:
            count_query = count_query.where(variant_subquery_clause)
        for jc in jsonb_conditions:
            count_query = count_query.where(jc)
        if search_condition is not None:
            count_query = count_query.where(search_condition)
        if rating_subquery_clause is not None:
            count_query = count_query.where(rating_subquery_clause)

        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0

        # ══════════════════════════════════════
        # DATA QUERY — with selectinload for paginated results only
        # ══════════════════════════════════════
        data_query = (
            select(Product)
            .where(*base_conditions)
            .options(selectinload(Product.images), selectinload(Product.variants))
        )
        if needs_category_join:
            data_query = data_query.join(Category, Product.category_id == Category.id)
        if variant_subquery_clause is not None:
            data_query = data_query.where(variant_subquery_clause)
        for jc in jsonb_conditions:
            data_query = data_query.where(jc)
        if search_condition is not None:
            data_query = data_query.where(search_condition)
        if rating_subquery_clause is not None:
            data_query = data_query.where(rating_subquery_clause)

        # ── Sort ──
        effective_price = func.coalesce(Product.sale_price, Product.base_price)
        sort_map = {
            "newest": Product.created_at.desc(),
            "price_asc": effective_price.asc(),
            "price_desc": effective_price.desc(),
            "name_asc": Product.title.asc(),
            "name_desc": Product.title.desc(),
        }
        order_clause = sort_map.get(sort, Product.created_at.desc())
        data_query = data_query.order_by(order_clause)

        # ── Pagination ──
        data_query = data_query.offset((page - 1) * page_size).limit(page_size)
        result = await self.db.execute(data_query)
        products = list(result.scalars().unique().all())

        return {
            "items": products,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": math.ceil(total / page_size) if total > 0 else 0,
        }

    # ══════════════════════════════════════
    # PRODUCT DETAIL
    # ══════════════════════════════════════

    async def get_product_by_slug(self, slug: str) -> dict:
        """
        Get full product detail by slug.
        Returns product + variants + images + avg rating + review count.
        """
        result = await self.db.execute(
            select(Product)
            .where(
                Product.slug == slug,
                Product.is_active == True,
                Product.deleted_at.is_(None),
            )
            .options(selectinload(Product.images), selectinload(Product.variants))
        )
        product = result.scalar_one_or_none()
        if not product:
            raise CatalogServiceError("Product not found.", 404)

        # Get avg rating and review count
        rating_result = await self.db.execute(
            select(
                func.avg(cast(Review.rating, Float)).label("avg_rating"),
                func.count(Review.id).label("review_count"),
            ).where(
                Review.product_id == product.id,
                Review.is_approved == True,
            )
        )
        rating_row = rating_result.one()

        # Filter active, non-deleted, in-stock variants
        active_variants = [
            v for v in product.variants
            if v.is_active and v.deleted_at is None
        ]

        # Get available sizes and colors
        available_sizes = _sort_sizes(list(set(v.size for v in active_variants if v.size)))
        available_colors = []
        seen_colors = set()
        for v in active_variants:
            if v.color and v.color not in seen_colors:
                seen_colors.add(v.color)
                available_colors.append({
                    "color": v.color,
                    "color_hex": v.color_hex,
                    "in_stock": any(
                        sv.stock_quantity > 0 for sv in active_variants if sv.color == v.color
                    ),
                })

        # Sort images by sort_order
        sorted_images = sorted(product.images, key=lambda i: i.sort_order)

        return {
            "product": product,
            "avg_rating": round(float(rating_row.avg_rating), 1) if rating_row.avg_rating else None,
            "review_count": rating_row.review_count or 0,
            "available_sizes": available_sizes,
            "available_colors": available_colors,
            "images": sorted_images,
            "variants": active_variants,
        }

    async def get_product_by_id(self, product_id) -> dict:
        """Get product detail by ID."""
        result = await self.db.execute(
            select(Product)
            .where(
                Product.id == product_id,
                Product.is_active == True,
                Product.deleted_at.is_(None),
            )
            .options(selectinload(Product.images), selectinload(Product.variants))
        )
        product = result.scalar_one_or_none()
        if not product:
            raise CatalogServiceError("Product not found.", 404)
        return await self.get_product_by_slug(product.slug)

    # ══════════════════════════════════════
    # VARIANT STOCK CHECK
    # ══════════════════════════════════════

    async def check_variant_stock(self, variant_id) -> dict:
        """Check stock for a specific variant."""
        result = await self.db.execute(
            select(ProductVariant).where(
                ProductVariant.id == variant_id,
                ProductVariant.deleted_at.is_(None),
            )
        )
        variant = result.scalar_one_or_none()
        if not variant:
            raise CatalogServiceError("Variant not found.", 404)
        return {
            "variant_id": str(variant.id),
            "sku": variant.sku,
            "stock_quantity": variant.stock_quantity,
            "in_stock": variant.stock_quantity > 0,
        }

    # ══════════════════════════════════════
    # SIZE GUIDE (public)
    # ══════════════════════════════════════

    async def get_size_guide(self, category_id) -> list:
        result = await self.db.execute(
            select(SizeGuide)
            .where(SizeGuide.category_id == category_id)
            .order_by(SizeGuide.size_label)
        )
        return list(result.scalars().all())

    # ══════════════════════════════════════
    # FILTERABLE ATTRIBUTES (public)
    # ══════════════════════════════════════

    async def get_filterable_attributes(self, category_id: str | None = None) -> list:
        """
        Get attribute definitions marked as filterable.
        Frontend uses this to auto-generate filter sidebar.
        """
        query = (
            select(AttributeDefinition)
            .where(AttributeDefinition.is_filterable == True)
            .order_by(AttributeDefinition.sort_order)
        )
        result = await self.db.execute(query)
        attrs = list(result.scalars().all())

        # If category_id specified, filter by applicable categories
        if category_id:
            attrs = [
                a for a in attrs
                if a.category_ids is None or category_id in [str(c) for c in (a.category_ids or [])]
            ]

        return attrs

    # ══════════════════════════════════════
    # SEARCH AUTOCOMPLETE
    # ══════════════════════════════════════

    async def search_autocomplete(self, query_str: str, limit: int = 8) -> list:
        """
        Quick search for autocomplete dropdown.
        Returns product titles + slugs matching the query.
        """
        if not query_str or len(query_str) < 2:
            return []

        result = await self.db.execute(
            select(Product.title, Product.slug, Product.brand)
            .where(
                Product.is_active == True,
                Product.deleted_at.is_(None),
                or_(
                    Product.title.ilike(f"%{query_str}%"),
                    Product.brand.ilike(f"%{query_str}%"),
                ),
            )
            .limit(limit)
        )
        rows = result.all()
        return [
            {"title": r.title, "slug": r.slug, "brand": r.brand}
            for r in rows
        ]

    # ══════════════════════════════════════
    # AVAILABLE FILTER VALUES
    # ══════════════════════════════════════

    async def get_available_brands(self) -> list[str]:
        """Get distinct brands for filter sidebar."""
        result = await self.db.execute(
            select(Product.brand)
            .where(
                Product.is_active == True,
                Product.deleted_at.is_(None),
                Product.brand.isnot(None),
            )
            .distinct()
            .order_by(Product.brand)
        )
        return [r[0] for r in result.all() if r[0]]

    async def get_available_sizes(self, category_id: str | None = None, gender: str | None = None) -> list[str]:
        """Get distinct sizes for filter sidebar. Scoped by gender when provided."""
        query = (
            select(ProductVariant.size)
            .join(Product, ProductVariant.product_id == Product.id)
            .where(
                ProductVariant.deleted_at.is_(None),
                ProductVariant.is_active == True,
                ProductVariant.size.isnot(None),
                Product.is_active == True,
                Product.deleted_at.is_(None),
            )
            .distinct()
        )
        if category_id:
            query = query.where(Product.category_id == category_id)
        if gender:
            query = query.join(Category, Product.category_id == Category.id).where(Category.gender == gender)
        result = await self.db.execute(query)
        return _sort_sizes([r[0] for r in result.all() if r[0]])

    async def get_available_colors(self, category_id: str | None = None, gender: str | None = None) -> list[dict]:
        """Get distinct colors with hex codes for filter sidebar. Scoped by gender when provided."""
        query = (
            select(ProductVariant.color, ProductVariant.color_hex)
            .join(Product, ProductVariant.product_id == Product.id)
            .where(
                ProductVariant.deleted_at.is_(None),
                ProductVariant.is_active == True,
                ProductVariant.color.isnot(None),
                Product.is_active == True,
                Product.deleted_at.is_(None),
            )
            .distinct()
        )
        if category_id:
            query = query.where(Product.category_id == category_id)
        if gender:
            query = query.join(Category, Product.category_id == Category.id).where(Category.gender == gender)
        result = await self.db.execute(query)
        return [{"color": r[0], "color_hex": r[1]} for r in result.all() if r[0]]
