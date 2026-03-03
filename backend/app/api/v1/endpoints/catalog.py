"""
Public Catalog API â€” /api/v1/catalog/
Phase 4: Browsing, filtering, search, product detail.
Most endpoints are public (no auth required).
"""

from decimal import Decimal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.catalog import (
    AutocompleteItem,
    CatalogListResponse,
    CategoryPublic,
    FilterOptionsResponse,
    LandingPageResponse,
    ProductDetailResponse,
    PublicProductListItem,
    PublicProductImage,
    PublicVariant,
    ColorOption,
)
from app.schemas.product import (
    AttributeDefinitionResponse,
    SizeGuideResponse,
)
from app.services.catalog_service import CatalogService, CatalogServiceError

router = APIRouter(prefix="/catalog", tags=["Public Catalog"])


def _handle_error(e: CatalogServiceError):
    raise HTTPException(status_code=e.status_code, detail=e.message)


# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# LANDING PAGE
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•


@router.get("/landing")
async def get_landing_page(db: AsyncSession = Depends(get_db)):
    """
    Landing page data: featured products + category cards by gender.
    Public endpoint â€” no auth required.
    """
    service = CatalogService(db)
    data = await service.get_landing_data()
    return {
        "featured_products": [
            PublicProductListItem.model_validate(p) for p in data["featured_products"]
        ],
        "categories_by_gender": {
            gender: [CategoryPublic.model_validate(c) for c in cats]
            for gender, cats in data["categories_by_gender"].items()
        },
        "all_categories": [
            CategoryPublic.model_validate(c) for c in data["all_categories"]
        ],
    }


# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# CATEGORY BROWSING
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•


@router.get("/categories", response_model=list[CategoryPublic])
async def browse_categories(
    gender: str | None = None,
    age_group: str | None = None,
    parent_id: UUID | None = None,
    db: AsyncSession = Depends(get_db),
):
    """Browse categories. Gender â†’ Age Group â†’ Subcategory grid."""
    service = CatalogService(db)
    cats = await service.browse_categories(
        gender=gender,
        age_group=age_group,
        parent_id=str(parent_id) if parent_id else None,
    )
    return cats


@router.get("/categories/{slug}", response_model=CategoryPublic)
async def get_category_by_slug(
    slug: str,
    db: AsyncSession = Depends(get_db),
):
    """Get category by slug."""
    service = CatalogService(db)
    try:
        return await service.get_category_by_slug(slug)
    except CatalogServiceError as e:
        _handle_error(e)


# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# PRODUCT LISTING WITH FILTERS
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•


@router.get("/products", response_model=CatalogListResponse)
async def list_products(
    request: Request,
    # Category
    category_id: UUID | None = None,
    gender: str | None = None,
    age_group: str | None = None,
    # Standard filters
    size: str | None = None,
    color: str | None = None,
    price_min: Decimal | None = None,
    price_max: Decimal | None = None,
    brand: str | None = None,
    min_rating: int | None = Query(None, ge=1, le=5),
    # Search
    search: str | None = None,
    # Sort
    sort: str = Query("newest", pattern="^(newest|price_asc|price_desc|name_asc|name_desc)$"),
    # Pagination
    page: int = Query(1, ge=1),
    page_size: int = Query(24, ge=1, le=100),
    # DB
    db: AsyncSession = Depends(get_db),
):
    """
    Product listing with full filter support.

    Apparel attribute filters via query params prefixed with 'attr.':
      ?attr.material=Cotton&attr.fit=Regular&attr.sleeve_type=Full

    Standard filters: size, color, price_min/max, brand, min_rating.
    Sort: newest, price_asc, price_desc, name_asc, name_desc.
    """
    # Extract JSONB attribute filters from query params (attr.key=value)
    attribute_filters = {}
    for key, value in request.query_params.items():
        if key.startswith("attr."):
            attr_key = key[5:]  # Remove 'attr.' prefix
            attribute_filters[attr_key] = value

    service = CatalogService(db)
    result = await service.list_products(
        category_id=str(category_id) if category_id else None,
        gender=gender,
        age_group=age_group,
        size=size,
        color=color,
        price_min=price_min,
        price_max=price_max,
        brand=brand,
        min_rating=min_rating,
        attribute_filters=attribute_filters if attribute_filters else None,
        search=search,
        sort=sort,
        page=page,
        page_size=page_size,
    )

    return CatalogListResponse(
        items=[PublicProductListItem.model_validate(p) for p in result["items"]],
        total=result["total"],
        page=result["page"],
        page_size=result["page_size"],
        total_pages=result["total_pages"],
    )


# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# PRODUCT DETAIL
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•


@router.get("/products/slug/{slug}")
async def get_product_by_slug(
    slug: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Product detail by slug. Returns full data for PDP:
    product, images (srcset URLs), variants, ratings, sizes, colors.
    """
    service = CatalogService(db)
    try:
        data = await service.get_product_by_slug(slug)
        return {
            "product": PublicProductListItem.model_validate(data["product"]),
            "avg_rating": data["avg_rating"],
            "review_count": data["review_count"],
            "available_sizes": data["available_sizes"],
            "available_colors": data["available_colors"],
            "images": [PublicProductImage.model_validate(i) for i in data["images"]],
            "variants": [PublicVariant.model_validate(v) for v in data["variants"]],
        }
    except CatalogServiceError as e:
        _handle_error(e)


@router.get("/products/{product_id}")
async def get_product_by_id(
    product_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Product detail by ID."""
    service = CatalogService(db)
    try:
        data = await service.get_product_by_id(product_id)
        return {
            "product": PublicProductListItem.model_validate(data["product"]),
            "avg_rating": data["avg_rating"],
            "review_count": data["review_count"],
            "available_sizes": data["available_sizes"],
            "available_colors": data["available_colors"],
            "images": [PublicProductImage.model_validate(i) for i in data["images"]],
            "variants": [PublicVariant.model_validate(v) for v in data["variants"]],
        }
    except CatalogServiceError as e:
        _handle_error(e)


# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# VARIANT STOCK CHECK
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•


@router.get("/variants/{variant_id}/stock")
async def check_variant_stock(
    variant_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Check stock availability for a specific variant."""
    service = CatalogService(db)
    try:
        return await service.check_variant_stock(variant_id)
    except CatalogServiceError as e:
        _handle_error(e)


# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# SIZE GUIDE (public)
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•


@router.get("/size-guide/{category_id}", response_model=list[SizeGuideResponse])
async def get_size_guide(
    category_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get size guide for a category (modal on PDP)."""
    service = CatalogService(db)
    return await service.get_size_guide(category_id)


# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# FILTER OPTIONS
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•


@router.get("/filters")
async def get_filter_options(
    category_id: UUID | None = None,
    gender: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    """
    Get all available filter values for the filter sidebar.
    Returns: brands, sizes, colors, filterable attributes with options.
    """
    service = CatalogService(db)
    cat_str = str(category_id) if category_id else None

    brands = await service.get_available_brands()
    sizes = await service.get_available_sizes(cat_str, gender=gender)
    colors = await service.get_available_colors(cat_str, gender=gender)
    attributes = await service.get_filterable_attributes(cat_str)

    return {
        "brands": brands,
        "sizes": sizes,
        "colors": colors,
        "attributes": [
            {
                "key": a.attribute_key,
                "display_name": a.display_name,
                "input_type": a.input_type,
                "options": a.options or [],
            }
            for a in attributes
        ],
    }


# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# SEARCH AUTOCOMPLETE
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•


@router.get("/search/autocomplete", response_model=list[AutocompleteItem])
async def search_autocomplete(
    q: str = Query(..., min_length=2, max_length=100),
    limit: int = Query(8, ge=1, le=20),
    db: AsyncSession = Depends(get_db),
):
    """Search autocomplete dropdown. Min 2 chars."""
    service = CatalogService(db)
    return await service.search_autocomplete(q, limit)


# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# FILTERABLE ATTRIBUTES (public)
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•


@router.get("/attributes", response_model=list[AttributeDefinitionResponse])
async def get_filterable_attributes(
    category_id: UUID | None = None,
    db: AsyncSession = Depends(get_db),
):
    """Get filterable attribute definitions for filter sidebar auto-generation."""
    service = CatalogService(db)
    return await service.get_filterable_attributes(
        str(category_id) if category_id else None
    )


# ---- Public Shipping Config (no auth required) ----
@router.get("/shipping-config", tags=["Catalog"])
async def get_public_shipping_config(db: AsyncSession = Depends(get_db)):
    """Public endpoint: returns shipping fee and free-shipping threshold for cart display."""
    from app.services.store_settings_service import StoreSettingsService
    return await StoreSettingsService.get_shipping_config_static(db)
