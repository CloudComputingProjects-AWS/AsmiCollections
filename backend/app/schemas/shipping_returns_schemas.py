"""
Pydantic schemas for Shipping, Returns & Refunds.
Phase 10 — V2.5 Blueprint
"""

from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field


# ════════════════════════════════════════════════
# SHIPPING SCHEMAS
# ════════════════════════════════════════════════


class ShipmentCreateRequest(BaseModel):
    """Admin creates shipment for an order."""
    order_id: UUID
    courier_partner: str = Field(..., max_length=50)
    tracking_number: str | None = Field(None, max_length=200)
    awb_number: str | None = Field(None, max_length=100)
    weight_grams: int | None = None
    estimated_delivery: date | None = None


class ShipmentUpdateRequest(BaseModel):
    """Update shipment tracking info."""
    tracking_number: str | None = None
    awb_number: str | None = None
    status: str | None = None
    tracking_url: str | None = None
    estimated_delivery: date | None = None
    shipping_label_url: str | None = None


class ShipmentResponse(BaseModel):
    id: UUID
    order_id: UUID
    courier_partner: str
    tracking_number: str | None = None
    awb_number: str | None = None
    status: str
    estimated_delivery: date | None = None
    shipped_at: datetime | None = None
    delivered_at: datetime | None = None
    weight_grams: int | None = None
    shipping_label_url: str | None = None
    tracking_url: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ════════════════════════════════════════════════
# RETURN SCHEMAS
# ════════════════════════════════════════════════


class ReturnRequestCreate(BaseModel):
    """Customer requests a return."""
    order_id: UUID
    order_item_id: UUID
    reason: str = Field(..., max_length=50)
    reason_detail: str | None = Field(None, max_length=1000)
    return_type: str = Field(..., pattern="^(exchange)$")
    quantity: int = Field(..., ge=1)


class ReturnActionRequest(BaseModel):
    """Admin approves/rejects a return."""
    action: str = Field(..., pattern="^(approve|reject)$")
    admin_notes: str | None = None
    pickup_date: date | None = None


class ReturnReceiveRequest(BaseModel):
    """Admin marks return as received."""
    admin_notes: str | None = None


class ReturnResponse(BaseModel):
    id: UUID
    order_id: UUID
    order_item_id: UUID
    user_id: UUID
    reason: str
    reason_detail: str | None = None
    return_type: str
    status: str
    quantity: int
    approved_by: UUID | None = None
    admin_notes: str | None = None
    pickup_date: date | None = None
    received_at: datetime | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ReturnListResponse(BaseModel):
    returns: list[ReturnResponse]
    total: int
    page: int
    page_size: int


# ════════════════════════════════════════════════
# REFUND SCHEMAS
# ════════════════════════════════════════════════


class RefundInitiateRequest(BaseModel):
    """Admin initiates a refund."""
    return_id: UUID | None = None
    order_id: UUID
    amount: Decimal = Field(..., gt=0)
    refund_method: str = Field(default="original", max_length=20)
    reason: str = Field(default="Customer return", max_length=500)


class RefundResponse(BaseModel):
    id: UUID
    return_id: UUID | None = None
    order_id: UUID
    gateway_refund_id: str | None = None
    amount: Decimal
    currency: str
    status: str
    refund_method: str | None = None
    initiated_by: UUID | None = None
    completed_at: datetime | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class RefundListResponse(BaseModel):
    refunds: list[RefundResponse]
    total: int
    page: int
    page_size: int


# ════════════════════════════════════════════════
# EMAIL NOTIFICATION SCHEMA
# ════════════════════════════════════════════════


class NotificationResult(BaseModel):
    """Result of sending a notification."""
    success: bool
    channel: str  # 'email' | 'sms'
    recipient: str | None = None
    message: str | None = None
