"""
Pydantic schemas for Public Catalog — Phase 4.
"""

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel


class PublicProductImage(BaseModel):
    id: UUID
    processed_url: str | None
    medium_url: str | None
    thumbnail_url: str | None
    original_url: str
    alt_text: str | None
    is_primary: bool
    sort_order: int

    class Config:
        from_attributes = True


class PublicVariant(BaseModel):
    id: UUID
    size: str | None
    color: str | None
    color_hex: str | None
    sku: str
    stock_quantity: int
    price_override: Decimal | None
    is_active: bool

    class Config:
        from_attributes = True


class PublicProductListItem(BaseModel):
    id: UUID
    title: str
    slug: str
    brand: str | None
    base_price: Decimal
    sale_price: Decimal | None
    base_currency: str
    category_id: UUID
    is_featured: bool
    attributes: dict
    created_at: datetime
    images: list[PublicProductImage] = []
    variants: list[PublicVariant] = []

    class Config:
        from_attributes = True


class ColorOption(BaseModel):
    color: str
    color_hex: str | None
    in_stock: bool


class ProductDetailResponse(BaseModel):
    product: PublicProductListItem
    avg_rating: float | None
    review_count: int
    available_sizes: list[str]
    available_colors: list[ColorOption]
    images: list[PublicProductImage]
    variants: list[PublicVariant]


class CatalogListResponse(BaseModel):
    items: list[PublicProductListItem]
    total: int
    page: int
    page_size: int
    total_pages: int


class CategoryPublic(BaseModel):
    id: UUID
    name: str
    slug: str
    gender: str
    age_group: str
    parent_category_id: UUID | None
    image_url: str | None
    description: str | None

    class Config:
        from_attributes = True


class LandingPageResponse(BaseModel):
    featured_products: list[PublicProductListItem]
    categories_by_gender: dict[str, list[CategoryPublic]]
    all_categories: list[CategoryPublic]


class AutocompleteItem(BaseModel):
    title: str
    slug: str
    brand: str | None


class FilterOptionsResponse(BaseModel):
    brands: list[str]
    sizes: list[str]
    colors: list[dict]
    attributes: list[dict]
