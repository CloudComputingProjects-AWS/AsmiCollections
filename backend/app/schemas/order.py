"""
Pydantic schemas for Checkout, Orders & State Machine — Phase 7.
"""
from datetime import datetime
from decimal import Decimal
from uuid import UUID
from pydantic import BaseModel, Field


# ══════════════════════════════════════════
# ADDRESS (for checkout)
# ══════════════════════════════════════════

class AddressCreate(BaseModel):
    label: str = Field(..., pattern="^(home|office|other)$")
    full_name: str = Field(..., max_length=200)
    phone: str = Field(..., max_length=20)
    address_line_1: str = Field(..., max_length=500)
    address_line_2: str | None = Field(None, max_length=500)
    city: str = Field(..., max_length=100)
    state: str = Field(..., max_length=100)
    postal_code: str = Field(..., max_length=20)
    country: str = Field(default="India", max_length=100)
    is_default: bool = False

class AddressResponse(BaseModel):
    id: UUID
    label: str
    full_name: str | None
    phone: str | None
    address_line_1: str
    address_line_2: str | None
    city: str
    state: str
    postal_code: str
    country: str
    is_default: bool
    class Config:
        from_attributes = True


# ══════════════════════════════════════════
# CHECKOUT / ORDER CREATION
# ══════════════════════════════════════════

class CheckoutRequest(BaseModel):
    shipping_address_id: UUID
    billing_address_id: UUID | None = None  # defaults to shipping
    payment_method: str | None = Field(None, max_length=20)
    payment_gateway: str | None = Field(None, pattern="^(razorpay|stripe)$")
    coupon_code: str | None = Field(None, max_length=50)
    notes: str | None = None
    currency: str = Field(default="INR", max_length=3)

class TaxBreakdown(BaseModel):
    hsn_code: str | None
    taxable_amount: Decimal
    cgst_rate: Decimal = Decimal("0")
    cgst_amount: Decimal = Decimal("0")
    sgst_rate: Decimal = Decimal("0")
    sgst_amount: Decimal = Decimal("0")
    igst_rate: Decimal = Decimal("0")
    igst_amount: Decimal = Decimal("0")
    total_tax: Decimal = Decimal("0")

class OrderItemResponse(BaseModel):
    id: UUID
    product_title_snapshot: str
    brand_snapshot: str | None
    size_snapshot: str | None
    color_snapshot: str | None
    sku_snapshot: str
    image_url_snapshot: str | None
    hsn_code_snapshot: str | None
    quantity: int
    unit_price: Decimal
    tax_rate: Decimal
    tax_amount: Decimal
    line_total: Decimal
    class Config:
        from_attributes = True

class OrderResponse(BaseModel):
    id: UUID
    order_number: str
    user_id: UUID
    subtotal: Decimal
    tax_amount: Decimal
    cgst_amount: Decimal
    sgst_amount: Decimal
    igst_amount: Decimal
    shipping_fee: Decimal
    discount_amount: Decimal
    grand_total: Decimal
    currency: str
    order_status: str
    payment_status: str
    payment_method: str | None
    coupon_code_snapshot: str | None
    shipping_name: str | None
    shipping_city: str | None
    shipping_state: str | None
    shipping_country: str | None
    created_at: datetime
    updated_at: datetime
    items: list[OrderItemResponse] = []
    class Config:
        from_attributes = True

class OrderSummaryResponse(BaseModel):
    """Pre-checkout order summary with tax breakdown."""
    items: list[dict]
    subtotal: Decimal
    tax_breakdown: list[TaxBreakdown]
    total_tax: Decimal
    shipping_fee: Decimal
    discount_amount: Decimal
    grand_total: Decimal
    currency: str


# ══════════════════════════════════════════
# ORDER STATE MACHINE
# ══════════════════════════════════════════

class OrderTransitionRequest(BaseModel):
    new_status: str
    reason: str | None = None

class StatusHistoryItem(BaseModel):
    id: UUID
    from_status: str | None
    to_status: str
    changed_by: UUID | None
    change_reason: str | None
    created_at: datetime
    class Config:
        from_attributes = True

class OrderTimelineResponse(BaseModel):
    order_id: UUID
    order_number: str
    current_status: str
    history: list[StatusHistoryItem]
