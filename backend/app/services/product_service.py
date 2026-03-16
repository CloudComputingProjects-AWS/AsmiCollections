"""
Product Management Service â€” Phase 2.
Business logic for: Categories, Products, Variants, Attributes, Inventory, Size Guides.
Controller â†’ Service â†’ Repository pattern (service layer).
"""

import uuid
from datetime import datetime, timezone

from slugify import slugify
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.models import (
    AttributeDefinition,
    Category,
    Product,
    ProductImage,
    ProductVariant,
    SizeGuide,
)
from app.schemas.product import (
    CategoryCreate,
    CategoryUpdate,
    ProductCreate,
    ProductUpdate,
    VariantCreate,
    VariantUpdate,
)


class ProductServiceError(Exception):
    def __init__(self, message: str, status_code: int = 400):
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class ProductService:
    def __init__(self, db: AsyncSession):
        self.db = db

    # â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
    # ATTRIBUTE DEFINITIONS
    # â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

    async def list_attribute_definitions(self, filterable_only: bool = False) -> list:
        query = select(AttributeDefinition).order_by(AttributeDefinition.sort_order)
        if filterable_only:
            query = query.where(AttributeDefinition.is_filterable.is_(True))
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def create_attribute_definition(self, data) -> AttributeDefinition:
        existing = await self.db.execute(
            select(AttributeDefinition).where(
                AttributeDefinition.attribute_key == data.attribute_key
            )
        )
        if existing.scalar_one_or_none():
            raise ProductServiceError(
                f"Attribute key '{data.attribute_key}' already exists.", 409
            )

        attr = AttributeDefinition(
            attribute_key=data.attribute_key,
            display_name=data.display_name,
            input_type=data.input_type,
            options=data.options,
            is_filterable=data.is_filterable,
            is_required=data.is_required,
            sort_order=data.sort_order,
            category_ids=data.category_ids,
        )
        self.db.add(attr)
        await self.db.flush()
        return attr

    async def update_attribute_definition(self, attr_id, data) -> AttributeDefinition:
        result = await self.db.execute(
            select(AttributeDefinition).where(AttributeDefinition.id == attr_id)
        )
        attr = result.scalar_one_or_none()
        if not attr:
            raise ProductServiceError("Attribute definition not found.", 404)

        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(attr, key, value)
        await self.db.flush()
        return attr

    async def delete_attribute_definition(self, attr_id) -> None:
        result = await self.db.execute(
            select(AttributeDefinition).where(AttributeDefinition.id == attr_id)
        )
        attr = result.scalar_one_or_none()
        if not attr:
            raise ProductServiceError("Attribute definition not found.", 404)
        await self.db.delete(attr)

    # â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
    # CATEGORIES
    # â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

    async def list_categories(
        self, gender: str | None = None, age_group: str | None = None, active_only: bool = True
    ) -> list:
        query = select(Category).where(Category.deleted_at.is_(None))
        if gender:
            query = query.where(Category.gender == gender)
        if age_group:
            query = query.where(Category.age_group == age_group)
        if active_only:
            query = query.where(Category.is_active.is_(True))
        query = query.order_by(Category.sort_order, Category.name)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_category(self, category_id) -> Category:
        result = await self.db.execute(
            select(Category).where(
                Category.id == category_id, Category.deleted_at.is_(None)
            )
        )
        cat = result.scalar_one_or_none()
        if not cat:
            raise ProductServiceError("Category not found.", 404)
        return cat

    async def create_category(self, data: CategoryCreate) -> Category:
        # Check slug uniqueness
        existing = await self.db.execute(
            select(Category).where(Category.slug == data.slug)
        )
        if existing.scalar_one_or_none():
            raise ProductServiceError(f"Slug '{data.slug}' already exists.", 409)

        cat = Category(
            name=data.name,
            slug=data.slug,
            gender=data.gender,
            age_group=data.age_group,
            parent_category_id=data.parent_category_id,
            image_url=data.image_url,
            description=data.description,
            sort_order=data.sort_order,
            is_active=data.is_active,
        )
        self.db.add(cat)
        await self.db.flush()
        return cat

    async def update_category(self, category_id, data: CategoryUpdate) -> Category:
        cat = await self.get_category(category_id)
        update_data = data.model_dump(exclude_unset=True)

        if "slug" in update_data:
            existing = await self.db.execute(
                select(Category).where(
                    Category.slug == update_data["slug"],
                    Category.id != category_id,
                )
            )
            if existing.scalar_one_or_none():
                raise ProductServiceError(f"Slug '{update_data['slug']}' already exists.", 409)

        for key, value in update_data.items():
            setattr(cat, key, value)
        await self.db.flush()
        return cat

    async def delete_category(self, category_id) -> None:
        cat = await self.get_category(category_id)
        cat.soft_delete()

    # â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
    # PRODUCTS
    # â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

    async def list_products(
        self,
        page: int = 1,
        page_size: int = 20,
        category_id: str | None = None,
        brand: str | None = None,
        is_active: bool | None = None,
        is_featured: bool | None = None,
        search: str | None = None,
    ) -> tuple[list, int]:
        query = (
            select(Product)
            .where(Product.deleted_at.is_(None))
            .options(selectinload(Product.variants), selectinload(Product.images))
        )

        if category_id:
            query = query.where(Product.category_id == category_id)
        if brand:
            query = query.where(Product.brand.ilike(f"%{brand}%"))
        if is_active is not None:
            query = query.where(Product.is_active == is_active)
        if is_featured is not None:
            query = query.where(Product.is_featured == is_featured)
        if search:
            query = query.where(
                Product.title.ilike(f"%{search}%")
                | Product.description.ilike(f"%{search}%")
            )

        # Count
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.db.execute(count_query)
        total = total_result.scalar()

        # Paginate
        query = query.order_by(Product.created_at.desc())
        query = query.offset((page - 1) * page_size).limit(page_size)
        result = await self.db.execute(query)
        products = list(result.scalars().unique().all())

        return products, total

    async def get_product(self, product_id) -> Product:
        result = await self.db.execute(
            select(Product)
            .where(Product.id == product_id, Product.deleted_at.is_(None))
            .options(selectinload(Product.variants), selectinload(Product.images))
        )
        product = result.scalar_one_or_none()
        if not product:
            raise ProductServiceError("Product not found.", 404)
        return product

    async def create_product(self, data: ProductCreate, variants: list | None = None) -> Product:
        # Auto-generate slug from title if not provided
        base_slug = data.slug if data.slug else slugify(data.title)
        slug = await self._ensure_unique_slug(base_slug)
        data = data.model_copy(update={"slug": slug})

        # Verify category exists
        cat_result = await self.db.execute(
            select(Category).where(
                Category.id == data.category_id, Category.deleted_at.is_(None)
            )
        )
        if not cat_result.scalar_one_or_none():
            raise ProductServiceError("Category not found.", 404)

        product = Product(
            title=data.title,
            slug=data.slug,
            description=data.description,
            category_id=data.category_id,
            brand=data.brand,
            base_price=data.base_price,
            sale_price=data.sale_price,
            hsn_code=data.hsn_code,
            gst_rate=data.gst_rate,
            tags=data.tags,
            attributes=data.attributes,
            is_active=data.is_active,
            is_featured=data.is_featured,
            meta_title=data.meta_title,
            meta_description=data.meta_description,
        )
        self.db.add(product)
        await self.db.flush()

        # Create variants if provided
        if variants:
            for v_data in variants:
                sku = v_data.sku or self._generate_sku(
                    data.brand or "PRD", v_data.size, v_data.color
                )
                variant = ProductVariant(
                    product_id=product.id,
                    size=v_data.size,
                    color=v_data.color,
                    color_hex=v_data.color_hex,
                    sku=sku,
                    stock_quantity=v_data.stock_quantity,
                    price_override=v_data.price_override,
                    weight_grams=v_data.weight_grams,
                    is_active=v_data.is_active,
                )
                self.db.add(variant)
            await self.db.flush()

        return product

    async def update_product(self, product_id, data: ProductUpdate) -> Product:
        product = await self.get_product(product_id)
        update_data = data.model_dump(exclude_unset=True)

        if "slug" in update_data:
            existing = await self.db.execute(
                select(Product).where(
                    Product.slug == update_data["slug"],
                    Product.id != product_id,
                )
            )
            if existing.scalar_one_or_none():
                raise ProductServiceError(f"Slug '{update_data['slug']}' already exists.", 409)

        for key, value in update_data.items():
            setattr(product, key, value)
        product.updated_at = datetime.now(timezone.utc)
        await self.db.flush()
        return product

    async def delete_product(self, product_id) -> None:
        product = await self.get_product(product_id)
        product.soft_delete()
        # Also soft-delete variants
        for v in product.variants:
            v.soft_delete()

    # â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
    # PRODUCT VARIANTS
    # â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

    async def create_variant(self, data: VariantCreate) -> ProductVariant:
        # Verify product exists
        await self.get_product(data.product_id)

        sku = data.sku or self._generate_sku("PRD", data.size, data.color)

        # Check SKU uniqueness
        existing = await self.db.execute(
            select(ProductVariant).where(ProductVariant.sku == sku)
        )
        if existing.scalar_one_or_none():
            raise ProductServiceError(f"SKU '{sku}' already exists.", 409)

        variant = ProductVariant(
            product_id=data.product_id,
            size=data.size,
            color=data.color,
            color_hex=data.color_hex,
            sku=sku,
            stock_quantity=data.stock_quantity,
            price_override=data.price_override,
            weight_grams=data.weight_grams,
            is_active=data.is_active,
        )
        self.db.add(variant)
        await self.db.flush()
        return variant

    async def update_variant(self, variant_id, data: VariantUpdate) -> ProductVariant:
        result = await self.db.execute(
            select(ProductVariant).where(
                ProductVariant.id == variant_id,
                ProductVariant.deleted_at.is_(None),
            )
        )
        variant = result.scalar_one_or_none()
        if not variant:
            raise ProductServiceError("Variant not found.", 404)

        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(variant, key, value)
        await self.db.flush()
        return variant

    async def delete_variant(self, variant_id) -> None:
        result = await self.db.execute(
            select(ProductVariant).where(
                ProductVariant.id == variant_id,
                ProductVariant.deleted_at.is_(None),
            )
        )
        variant = result.scalar_one_or_none()
        if not variant:
            raise ProductServiceError("Variant not found.", 404)
        variant.soft_delete()

    # â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
    # INVENTORY
    # â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

    async def list_inventory(
        self,
        page: int = 1,
        page_size: int = 25,
        search: str | None = None,
        low_stock_only: bool = False,
        low_stock_threshold: int = 10,
    ) -> tuple[list[dict], int]:
        """
        List all product variants with parent product info for the
        admin inventory page.  Returns (items, total_count).
        """
        base = (
            select(ProductVariant, Product)
            .join(Product, ProductVariant.product_id == Product.id)
            .where(
                ProductVariant.deleted_at.is_(None),
                Product.deleted_at.is_(None),
            )
        )

        if search:
            base = base.where(
                Product.title.ilike(f"%{search}%")
                | ProductVariant.sku.ilike(f"%{search}%")
                | Product.brand.ilike(f"%{search}%")
            )

        if low_stock_only:
            base = base.where(
                ProductVariant.stock_quantity <= low_stock_threshold
            )

        # Total count
        count_q = select(func.count()).select_from(base.subquery())
        total = (await self.db.execute(count_q)).scalar() or 0

        # Paginated results
        query = (
            base.order_by(Product.title, ProductVariant.size)
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        rows = (await self.db.execute(query)).all()

        items = [
            {
                "id": str(v.id),
                "product_id": str(p.id),
                "product_title": p.title,
                "brand": p.brand,
                "sku": v.sku,
                "size": v.size,
                "color": v.color,
                "color_hex": v.color_hex,
                "stock_quantity": v.stock_quantity,
                "price_override": float(v.price_override) if v.price_override else None,
                "is_active": v.is_active,
            }
            for v, p in rows
        ]
        return items, total

    async def update_stock(self, variant_id, new_quantity: int) -> ProductVariant:
        result = await self.db.execute(
            select(ProductVariant).where(
                ProductVariant.id == variant_id,
                ProductVariant.deleted_at.is_(None),
            )
        )
        variant = result.scalar_one_or_none()
        if not variant:
            raise ProductServiceError("Variant not found.", 404)
        variant.stock_quantity = new_quantity
        await self.db.flush()
        return variant

    async def bulk_update_stock(self, items: list) -> list:
        updated = []
        for item in items:
            variant = await self.update_stock(item.variant_id, item.stock_quantity)
            updated.append(variant)
        return updated

    async def get_low_stock_variants(self, threshold: int = 10) -> list:
        result = await self.db.execute(
            select(ProductVariant, Product)
            .join(Product, ProductVariant.product_id == Product.id)
            .where(
                ProductVariant.stock_quantity <= threshold,
                ProductVariant.deleted_at.is_(None),
                Product.deleted_at.is_(None),
                ProductVariant.is_active.is_(True),
            )
            .order_by(ProductVariant.stock_quantity.asc())
        )
        rows = result.all()
        return [
            {
                "variant_id": v.id,
                "product_id": p.id,
                "product_title": p.title,
                "sku": v.sku,
                "size": v.size,
                "color": v.color,
                "stock_quantity": v.stock_quantity,
            }
            for v, p in rows
        ]

    # â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
    # SIZE GUIDES
    # â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

    async def list_size_guides(self, category_id) -> list:
        result = await self.db.execute(
            select(SizeGuide)
            .where(SizeGuide.category_id == category_id)
            .order_by(SizeGuide.size_label)
        )
        return list(result.scalars().all())

    async def create_size_guide(self, data) -> SizeGuide:
        guide = SizeGuide(
            category_id=data.category_id,
            size_label=data.size_label,
            chest_cm=data.chest_cm,
            waist_cm=data.waist_cm,
            hip_cm=data.hip_cm,
            length_cm=data.length_cm,
        )
        self.db.add(guide)
        await self.db.flush()
        return guide

    async def delete_size_guide(self, guide_id) -> None:
        result = await self.db.execute(
            select(SizeGuide).where(SizeGuide.id == guide_id)
        )
        guide = result.scalar_one_or_none()
        if not guide:
            raise ProductServiceError("Size guide entry not found.", 404)
        await self.db.delete(guide)

    # â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
    # PHASE 13G: SIZE MAPPING CONFIG
    # â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

    SIZE_MAPPINGS = {
        "standard_to_kids": {
            "XS": "4-6", "S": "7-9", "M": "10-12", "L": "13-15", "XL": "16+",
        },
        "kids_to_standard": {
            "4-6": "XS", "7-9": "S", "10-12": "M", "13-15": "L", "16+": "XL",
        },
        "standard_to_waist": {
            "XS": "26", "S": "28", "M": "30", "L": "32", "XL": "34", "XXL": "36", "XXXL": "38",
        },
        "waist_to_standard": {
            "26": "XS", "28": "S", "30": "M", "32": "L", "34": "XL", "36": "XXL", "38": "XXXL",
        },
    }

    STANDARD_SIZES = ["S", "M", "L", "XL"]
    KIDS_SIZES = ["4-6", "7-9", "10-12", "13-15", "16+"]
    WAIST_SIZES = ["26", "28", "30", "32", "34", "36", "38"]

    @staticmethod
    def get_size_type(gender: str) -> str:
        """Determine size type from gender."""
        if gender in ("boys", "girls"):
            return "kids"
        return "standard"

    @classmethod
    def map_size(cls, size: str, source_gender: str, target_gender: str) -> str:
        """Map a size from one gender's sizing to another."""
        if not size:
            return size

        source_type = cls.get_size_type(source_gender)
        target_type = cls.get_size_type(target_gender)

        if source_type == target_type:
            return size

        mapping_key = f"{source_type}_to_{target_type}"
        mappings = cls.SIZE_MAPPINGS.get(mapping_key, {})
        return mappings.get(size.upper(), size)

    @classmethod
    def get_suggested_sizes(cls, gender: str) -> list[str]:
        """Return suggested sizes for a gender."""
        if gender in ("boys", "girls"):
            return cls.KIDS_SIZES
        return cls.STANDARD_SIZES

    @classmethod
    def get_size_mappings(cls, source_type: str, target_type: str) -> dict:
        """Get size mapping dictionary."""
        mapping_key = f"{source_type}_to_{target_type}"
        return cls.SIZE_MAPPINGS.get(mapping_key, {})

    # â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
    # PHASE 13G: BULK CREATE PRODUCTS
    # â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

    async def bulk_create_products(self, products_data: list) -> dict:
        """
        Create multiple products with inline variants in a single transaction.
        Each item in products_data is a BulkProductItem.
        """
        results = []
        created = 0
        failed = 0

        for idx, item in enumerate(products_data):
            try:
                # Verify category exists
                cat_result = await self.db.execute(
                    select(Category).where(
                        Category.id == item.category_id,
                        Category.deleted_at.is_(None),
                    )
                )
                cat = cat_result.scalar_one_or_none()
                if not cat:
                    results.append({
                        "index": idx, "status": "failed",
                        "error": f"Category {item.category_id} not found",
                    })
                    failed += 1
                    continue

                # Generate slug if not provided
                slug = item.slug or slugify(item.title)
                slug = await self._ensure_unique_slug(slug)
                product = Product(
                    title=item.title,
                    slug=slug,
                    description=item.description,
                    category_id=item.category_id,
                    brand=item.brand,
                    base_price=item.base_price,
                    sale_price=item.sale_price,
                    hsn_code=item.hsn_code,
                    gst_rate=item.gst_rate,
                    tags=item.tags,
                    attributes=item.attributes,
                    is_active=item.is_active,
                    is_featured=item.is_featured,
                    meta_title=item.meta_title,
                    meta_description=item.meta_description,
                )
                self.db.add(product)
                await self.db.flush()

                # Create variants
                variant_count = 0
                for v_data in (item.variants or []):
                    sku = v_data.sku or self._generate_sku(
                        item.brand or "PRD", v_data.size, v_data.color,
                    )
                    # Ensure SKU uniqueness
                    sku_check = await self.db.execute(
                        select(ProductVariant).where(ProductVariant.sku == sku)
                    )
                    if sku_check.scalar_one_or_none():
                        sku = f"{sku}-{uuid.uuid4().hex[:4].upper()}"

                    variant = ProductVariant(
                        product_id=product.id,
                        size=v_data.size,
                        color=v_data.color,
                        color_hex=v_data.color_hex,
                        sku=sku,
                        stock_quantity=v_data.stock_quantity,
                        price_override=v_data.price_override,
                        weight_grams=v_data.weight_grams,
                        is_active=v_data.is_active,
                    )
                    self.db.add(variant)
                    variant_count += 1

                await self.db.flush()
                created += 1
                results.append({
                    "index": idx, "status": "created",
                    "product_id": str(product.id), "title": product.title,
                    "slug": product.slug, "variants_created": variant_count,
                })

            except Exception as e:
                failed += 1
                results.append({
                    "index": idx, "status": "failed",
                    "error": str(e),
                })

        return {"created": created, "failed": failed, "results": results}

    # â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
    # PHASE 13G: DUPLICATE PRODUCT
    # â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

    async def duplicate_product(
        self, product_id, target_category_id, new_title: str | None = None,
        new_slug: str | None = None, map_sizes: bool = True,
    ) -> dict:
        """Clone a product to a different category with auto-mapped size variants."""
        source = await self.get_product(product_id)

        # Get source category for gender
        source_cat = await self.db.execute(
            select(Category).where(Category.id == source.category_id)
        )
        source_cat = source_cat.scalar_one_or_none()
        if not source_cat:
            raise ProductServiceError("Source product category not found.", 404)

        # Get target category
        target_cat = await self.db.execute(
            select(Category).where(
                Category.id == target_category_id,
                Category.deleted_at.is_(None),
            )
        )
        target_cat = target_cat.scalar_one_or_none()
        if not target_cat:
            raise ProductServiceError("Target category not found.", 404)

        # Generate title and slug
        title = new_title or f"{source.title} ({target_cat.gender.capitalize()})"
        slug = new_slug or slugify(title)
        slug = await self._ensure_unique_slug(slug)

        # Create duplicated product
        new_product = Product(
            title=title,
            slug=slug,
            description=source.description,
            category_id=target_category_id,
            brand=source.brand,
            base_price=source.base_price,
            sale_price=source.sale_price,
            hsn_code=source.hsn_code,
            gst_rate=source.gst_rate,
            tags=source.tags,
            attributes=source.attributes,
            is_active=source.is_active,
            is_featured=False,
            meta_title=source.meta_title,
            meta_description=source.meta_description,
        )
        self.db.add(new_product)
        await self.db.flush()

        # Duplicate variants with size mapping
        size_mappings_applied = []
        variants_created = 0

        for v in source.variants:
            if v.deleted_at is not None:
                continue

            new_size = v.size
            if map_sizes and v.size:
                new_size = self.map_size(v.size, source_cat.gender, target_cat.gender)
                if new_size != v.size:
                    size_mappings_applied.append({
                        "original": v.size, "mapped": new_size,
                    })

            sku = self._generate_sku(source.brand or "PRD", new_size, v.color)
            sku_check = await self.db.execute(
                select(ProductVariant).where(ProductVariant.sku == sku)
            )
            if sku_check.scalar_one_or_none():
                sku = f"{sku}-{uuid.uuid4().hex[:4].upper()}"

            new_variant = ProductVariant(
                product_id=new_product.id,
                size=new_size,
                color=v.color,
                color_hex=v.color_hex,
                sku=sku,
                stock_quantity=0,
                price_override=v.price_override,
                weight_grams=v.weight_grams,
                is_active=True,
            )
            self.db.add(new_variant)
            variants_created += 1

        await self.db.flush()

        return {
            "original_product_id": str(product_id),
            "new_product_id": str(new_product.id),
            "new_title": new_product.title,
            "new_slug": new_product.slug,
            "target_category_id": str(target_category_id),
            "variants_created": variants_created,
            "size_mappings_applied": size_mappings_applied,
        }

    # â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
    # BULK CSV UPLOAD
    # â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

    async def bulk_create_from_csv(self, rows: list[dict]) -> dict:
        """
        Process CSV rows. Each row = one product or variant.
        Returns {created: int, errors: [{row: int, error: str}]}
        """
        created = 0
        errors = []

        for idx, row in enumerate(rows, start=2):  # row 1 = header
            try:
                title = row.get("title", "").strip()
                if not title:
                    errors.append({"row": idx, "error": "Title is required"})
                    continue

                slug = row.get("slug") or slugify(title)
                slug = await self._ensure_unique_slug(slug)

                base_price = row.get("base_price")
                if not base_price:
                    errors.append({"row": idx, "error": "base_price is required"})
                    continue

                category_id = row.get("category_id")
                if not category_id:
                    errors.append({"row": idx, "error": "category_id is required"})
                    continue

                product = Product(
                    title=title,
                    slug=slug,
                    description=row.get("description"),
                    category_id=category_id,
                    brand=row.get("brand"),
                    base_price=base_price,
                    sale_price=row.get("sale_price"),
                    hsn_code=row.get("hsn_code"),
                    gst_rate=row.get("gst_rate", 0),
                    tags=row.get("tags", "").split(",") if row.get("tags") else None,
                    attributes=row.get("attributes", {}),
                    is_active=str(row.get("is_active", "true")).lower() == "true",
                )
                self.db.add(product)
                await self.db.flush()

                # Create variant if size/color/sku present
                sku = row.get("sku")
                size = row.get("size")
                color = row.get("color")
                if sku or size or color:
                    sku = sku or self._generate_sku(
                        row.get("brand", "PRD"), size, color
                    )
                    variant = ProductVariant(
                        product_id=product.id,
                        size=size,
                        color=color,
                        color_hex=row.get("color_hex"),
                        sku=sku,
                        stock_quantity=int(row.get("stock_quantity", 0)),
                        price_override=row.get("price_override"),
                        weight_grams=int(row.get("weight_grams", 0)) if row.get("weight_grams") else None,
                    )
                    self.db.add(variant)

                created += 1
            except Exception as e:
                errors.append({"row": idx, "error": str(e)})

        return {"created": created, "errors": errors}

    # â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
    # HELPERS
    # â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•


    async def _ensure_unique_slug(self, base_slug: str) -> str:
        """Return a unique product slug by appending counter if collision found."""
        slug = base_slug
        counter = 1
        while True:
            existing = await self.db.execute(
                select(Product).where(Product.slug == slug)
            )
            if not existing.scalar_one_or_none():
                return slug
            slug = f"{base_slug}-{counter}"
            counter += 1

    @staticmethod
    def _generate_sku(brand: str, size: str | None, color: str | None) -> str:
        parts = [brand[:3].upper()]
        if size:
            parts.append(size.upper())
        if color:
            parts.append(color[:3].upper())
        parts.append(uuid.uuid4().hex[:6].upper())
        return "-".join(parts)
