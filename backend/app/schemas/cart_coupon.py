"""
Pydantic schemas for Cart & Coupons — Phase 6.
"""

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field


# ══════════════════════════════════════════
# CART
# ══════════════════════════════════════════

class CartAddRequest(BaseModel):
    variant_id: UUID
    quantity: int = Field(default=1, ge=1, le=20)


class CartUpdateRequest(BaseModel):
    quantity: int = Field(..., ge=1, le=20)


class CartMergeItem(BaseModel):
    variant_id: UUID
    quantity: int = Field(..., ge=1, le=20)


class CartMergeRequest(BaseModel):
    """Guest cart items to merge on login."""
    items: list[CartMergeItem]


class CartItemResponse(BaseModel):
    id: UUID
    variant_id: UUID
    quantity: int
    # Enriched fields
    product_id: UUID | None = None
    product_title: str | None = None
    product_slug: str | None = None
    brand: str | None = None
    size: str | None = None
    color: str | None = None
    color_hex: str | None = None
    sku: str | None = None
    unit_price: Decimal | None = None
    sale_price: Decimal | None = None
    line_total: Decimal | None = None
    stock_quantity: int | None = None
    in_stock: bool = True
    image_url: str | None = None


class CartResponse(BaseModel):
    items: list[CartItemResponse]
    item_count: int
    subtotal: Decimal
    currency: str = "INR"


# ══════════════════════════════════════════
# COUPONS
# ══════════════════════════════════════════

class CouponCreate(BaseModel):
    code: str = Field(..., max_length=50)
    description: str | None = Field(None, max_length=500)
    type: str = Field(..., pattern="^(flat|percent)$")
    value: Decimal = Field(..., gt=0, max_digits=12, decimal_places=2)
    min_order_value: Decimal = Field(default=Decimal("0"), ge=0)
    max_discount: Decimal | None = Field(None, ge=0)
    usage_limit: int | None = Field(None, ge=1)
    per_user_limit: int = Field(default=1, ge=1)
    applicable_categories: list[UUID] | None = None
    starts_at: datetime
    expires_at: datetime
    is_active: bool = True


class CouponUpdate(BaseModel):
    description: str | None = Field(None, max_length=500)
    type: str | None = Field(None, pattern="^(flat|percent)$")
    value: Decimal | None = Field(None, gt=0)
    min_order_value: Decimal | None = Field(None, ge=0)
    max_discount: Decimal | None = Field(None, ge=0)
    usage_limit: int | None = Field(None, ge=1)
    per_user_limit: int | None = Field(None, ge=1)
    applicable_categories: list[UUID] | None = None
    starts_at: datetime | None = None
    expires_at: datetime | None = None
    is_active: bool | None = None


class CouponResponse(BaseModel):
    id: UUID
    code: str
    description: str | None
    type: str
    value: Decimal
    min_order_value: Decimal
    max_discount: Decimal | None
    usage_limit: int | None
    used_count: int
    per_user_limit: int
    applicable_categories: list[UUID] | None
    starts_at: datetime
    expires_at: datetime
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class ApplyCouponRequest(BaseModel):
    code: str = Field(..., max_length=50)


class CouponApplyResult(BaseModel):
    valid: bool
    message: str
    coupon_id: UUID | None = None
    discount_amount: Decimal = Decimal("0")
    coupon_code: str | None = None
    coupon_type: str | None = None
