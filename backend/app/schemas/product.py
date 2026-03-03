"""
Pydantic schemas for Admin Product Management Ã¢â‚¬â€ Phase 2.
Covers: Categories, Products, Variants, Attributes, Inventory, Size Guides.
"""

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field


# Ã¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢Â
# ATTRIBUTE DEFINITIONS
# Ã¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢Â

class AttributeDefinitionCreate(BaseModel):
    attribute_key: str = Field(..., max_length=50, pattern="^[a-z_]+$")
    display_name: str = Field(..., max_length=100)
    input_type: str = Field(..., pattern="^(text|select|multiselect)$")
    options: list[str] | None = None
    is_filterable: bool = False
    is_required: bool = False
    sort_order: int = 0
    category_ids: list[UUID] | None = None


class AttributeDefinitionUpdate(BaseModel):
    display_name: str | None = Field(None, max_length=100)
    input_type: str | None = Field(None, pattern="^(text|select|multiselect)$")
    options: list[str] | None = None
    is_filterable: bool | None = None
    is_required: bool | None = None
    sort_order: int | None = None
    category_ids: list[UUID] | None = None


class AttributeDefinitionResponse(BaseModel):
    id: UUID
    attribute_key: str
    display_name: str
    input_type: str
    options: list[str] | None
    is_filterable: bool
    is_required: bool
    sort_order: int
    category_ids: list[UUID] | None
    created_at: datetime

    class Config:
        from_attributes = True


# Ã¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢Â
# CATEGORIES
# Ã¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢Â

class CategoryCreate(BaseModel):
    name: str = Field(..., max_length=100)
    slug: str = Field(..., max_length=100, pattern="^[a-z0-9-]+$")
    gender: str = Field(..., pattern="^(men|women|boys|girls|unisex)$")
    age_group: str = Field(..., pattern="^(infant|kids|teen|adult|senior)$")
    parent_category_id: UUID | None = None
    image_url: str | None = Field(None, max_length=1000)
    description: str | None = None
    sort_order: int = 0
    is_active: bool = True


class CategoryUpdate(BaseModel):
    name: str | None = Field(None, max_length=100)
    slug: str | None = Field(None, max_length=100, pattern="^[a-z0-9-]+$")
    gender: str | None = Field(None, pattern="^(men|women|boys|girls|unisex)$")
    age_group: str | None = Field(None, pattern="^(infant|kids|teen|adult|senior)$")
    parent_category_id: UUID | None = None
    image_url: str | None = Field(None, max_length=1000)
    description: str | None = None
    sort_order: int | None = None
    is_active: bool | None = None


class CategoryResponse(BaseModel):
    id: UUID
    name: str
    slug: str
    gender: str
    age_group: str
    parent_category_id: UUID | None
    image_url: str | None
    description: str | None
    sort_order: int
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


# Ã¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢Â
# PRODUCTS
# Ã¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢Â

class ProductCreate(BaseModel):
    title: str = Field(..., max_length=500)
    slug: str = Field(..., max_length=500, pattern="^[a-z0-9-]+$")
    description: str | None = None
    category_id: UUID
    brand: str | None = Field(None, max_length=200)
    base_price: Decimal = Field(..., gt=0, max_digits=12, decimal_places=2)
    sale_price: Decimal | None = Field(None, ge=0, max_digits=12, decimal_places=2)
    hsn_code: str | None = Field(None, max_length=20)
    gst_rate: Decimal = Field(default=Decimal("0"), ge=0, max_digits=4, decimal_places=2)
    tags: list[str] | None = None
    attributes: dict = Field(default_factory=dict)
    is_active: bool = True
    is_featured: bool = False
    meta_title: str | None = Field(None, max_length=200)
    meta_description: str | None = Field(None, max_length=500)


class ProductUpdate(BaseModel):
    title: str | None = Field(None, max_length=500)
    slug: str | None = Field(None, max_length=500, pattern="^[a-z0-9-]+$")
    description: str | None = None
    category_id: UUID | None = None
    brand: str | None = Field(None, max_length=200)
    base_price: Decimal | None = Field(None, gt=0, max_digits=12, decimal_places=2)
    sale_price: Decimal | None = Field(None, ge=0, max_digits=12, decimal_places=2)
    hsn_code: str | None = Field(None, max_length=20)
    gst_rate: Decimal | None = Field(None, ge=0, max_digits=4, decimal_places=2)
    tags: list[str] | None = None
    attributes: dict | None = None
    is_active: bool | None = None
    is_featured: bool | None = None
    meta_title: str | None = Field(None, max_length=200)
    meta_description: str | None = Field(None, max_length=500)


class ProductVariantInline(BaseModel):
    """Variant data used when creating/updating variants inline with a product."""
    size: str | None = Field(None, max_length=20)
    color: str | None = Field(None, max_length=50)
    color_hex: str | None = Field(None, max_length=7, pattern="^#[0-9A-Fa-f]{6}$")
    sku: str | None = Field(None, max_length=100)  # auto-generated if null
    stock_quantity: int = Field(default=0, ge=0)
    price_override: Decimal | None = Field(None, ge=0, max_digits=12, decimal_places=2)
    weight_grams: int | None = Field(None, ge=0)
    is_active: bool = True


class ProductImageResponse(BaseModel):
    id: UUID
    original_url: str
    processed_url: str | None
    thumbnail_url: str | None
    medium_url: str | None
    alt_text: str | None
    is_primary: bool
    sort_order: int
    processing_status: str

    class Config:
        from_attributes = True


class ProductVariantResponse(BaseModel):
    id: UUID
    product_id: UUID
    size: str | None
    color: str | None
    color_hex: str | None
    sku: str
    stock_quantity: int
    price_override: Decimal | None
    weight_grams: int | None
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class ProductResponse(BaseModel):
    id: UUID
    title: str
    slug: str
    description: str | None
    category_id: UUID
    brand: str | None
    base_price: Decimal
    sale_price: Decimal | None
    base_currency: str
    hsn_code: str | None
    gst_rate: Decimal
    tags: list[str] | None
    attributes: dict
    is_active: bool
    is_featured: bool
    meta_title: str | None
    meta_description: str | None
    created_at: datetime
    updated_at: datetime
    variants: list[ProductVariantResponse] = []
    images: list[ProductImageResponse] = []

    class Config:
        from_attributes = True


class ProductListResponse(BaseModel):
    """Lightweight product for list views."""
    id: UUID
    title: str
    slug: str
    brand: str | None
    base_price: Decimal
    sale_price: Decimal | None
    category_id: UUID
    is_active: bool
    is_featured: bool
    created_at: datetime
    variant_count: int = 0
    total_stock: int = 0
    primary_image_url: str | None = None

    class Config:
        from_attributes = True


# Ã¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢Â
# PRODUCT VARIANTS (standalone CRUD)
# Ã¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢Â

class VariantCreate(BaseModel):
    product_id: UUID
    size: str | None = Field(None, max_length=20)
    color: str | None = Field(None, max_length=50)
    color_hex: str | None = Field(None, max_length=7, pattern="^#[0-9A-Fa-f]{6}$")
    sku: str | None = Field(None, max_length=100)
    stock_quantity: int = Field(default=0, ge=0)
    price_override: Decimal | None = Field(None, ge=0, max_digits=12, decimal_places=2)
    weight_grams: int | None = Field(None, ge=0)
    is_active: bool = True


class VariantUpdate(BaseModel):
    size: str | None = Field(None, max_length=20)
    color: str | None = Field(None, max_length=50)
    color_hex: str | None = Field(None, max_length=7, pattern="^#[0-9A-Fa-f]{6}$")
    stock_quantity: int | None = Field(None, ge=0)
    price_override: Decimal | None = Field(None, ge=0, max_digits=12, decimal_places=2)
    weight_grams: int | None = Field(None, ge=0)
    is_active: bool | None = None


# Ã¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢Â
# INVENTORY
# Ã¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢Â

class InventoryUpdateRequest(BaseModel):
    stock_quantity: int = Field(..., ge=0)


class InventoryBulkUpdateItem(BaseModel):
    variant_id: UUID
    stock_quantity: int = Field(..., ge=0)


class InventoryBulkUpdateRequest(BaseModel):
    items: list[InventoryBulkUpdateItem]


class LowStockResponse(BaseModel):
    variant_id: UUID
    product_id: UUID
    product_title: str
    sku: str
    size: str | None
    color: str | None
    stock_quantity: int


# Ã¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢Â
# SIZE GUIDES
# Ã¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢Â

class SizeGuideCreate(BaseModel):
    category_id: UUID
    size_label: str = Field(..., max_length=10)
    chest_cm: Decimal | None = Field(None, max_digits=5, decimal_places=1)
    waist_cm: Decimal | None = Field(None, max_digits=5, decimal_places=1)
    hip_cm: Decimal | None = Field(None, max_digits=5, decimal_places=1)
    length_cm: Decimal | None = Field(None, max_digits=5, decimal_places=1)


class SizeGuideResponse(BaseModel):
    id: UUID
    category_id: UUID | None
    size_label: str | None
    chest_cm: Decimal | None
    waist_cm: Decimal | None
    hip_cm: Decimal | None
    length_cm: Decimal | None

    class Config:
        from_attributes = True


# Ã¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢Â
# PAGINATION
# Ã¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢Â

class PaginatedResponse(BaseModel):
    items: list
    total: int
    page: int
    page_size: int
    total_pages: int


# Ã¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢Â
# PHASE 13G: ADMIN BULK & DUPLICATION
# Ã¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢Â

class BulkProductItem(BaseModel):
    """Single product with inline variants for bulk creation."""
    title: str = Field(..., max_length=500)
    slug: str | None = Field(None, max_length=500, pattern=r"^[a-z0-9-]+$")
    description: str | None = None
    category_id: UUID
    brand: str | None = Field(None, max_length=200)
    base_price: Decimal = Field(..., gt=0, max_digits=12, decimal_places=2)
    sale_price: Decimal | None = Field(None, ge=0, max_digits=12, decimal_places=2)
    hsn_code: str | None = Field(None, max_length=20)
    gst_rate: Decimal = Field(default=Decimal("0"), ge=0, max_digits=4, decimal_places=2)
    tags: list[str] | None = None
    attributes: dict = Field(default_factory=dict)
    is_active: bool = True
    is_featured: bool = False
    meta_title: str | None = Field(None, max_length=200)
    meta_description: str | None = Field(None, max_length=500)
    variants: list[ProductVariantInline] = Field(default_factory=list)


class BulkProductCreateRequest(BaseModel):
    """Bulk create products across multiple categories in a single API call."""
    products: list[BulkProductItem] = Field(..., min_length=1, max_length=50)


class BulkProductCreateResponse(BaseModel):
    created: int
    failed: int
    results: list[dict]


class ProductDuplicateRequest(BaseModel):
    """Clone a product to a different category with auto-mapped sizes."""
    target_category_id: UUID
    new_title: str | None = Field(None, max_length=500)
    new_slug: str | None = Field(None, max_length=500, pattern=r"^[a-z0-9-]+$")
    map_sizes: bool = True


class ProductDuplicateResponse(BaseModel):
    original_product_id: UUID
    new_product_id: UUID
    new_title: str
    new_slug: str
    target_category_id: UUID
    variants_created: int
    size_mappings_applied: list[dict]


class SizeMappingResponse(BaseModel):
    """Size mapping configuration for cross-category duplication."""
    source_type: str
    target_type: str
    mappings: dict[str, str]
