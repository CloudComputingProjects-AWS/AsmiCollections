"""
Pydantic schemas for Payment Integration (Phase 8).

Covers:
  - Gateway selection
  - Razorpay order creation / verification
  - Stripe PaymentIntent creation
  - Webhook payloads
  - FX rate locking
  - Payment status responses
"""

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field


# ────────────────────────────────────────────────────────
# GATEWAY SELECTION
# ────────────────────────────────────────────────────────

class PaymentMethodsResponse(BaseModel):
    """Available payment methods based on user country."""
    gateway: str                        # 'razorpay' | 'stripe'
    methods: list[str]                  # e.g. ['upi', 'netbanking', 'credit_card']
    currency: str                       # 'INR' | 'USD' | etc.
    fx_rate: Decimal | None = None
    fx_rate_locked_at: datetime | None = None


class GatewaySelectionRequest(BaseModel):
    """Client sends country/region to get available methods."""
    country_code: str = Field(..., max_length=5, examples=["IN", "US", "GB"])


# ────────────────────────────────────────────────────────
# RAZORPAY
# ────────────────────────────────────────────────────────

class RazorpayCreateOrderRequest(BaseModel):
    """Initiate Razorpay payment for an order."""
    order_id: UUID
    payment_method: str | None = None


class RazorpayCreateOrderResponse(BaseModel):
    """Returned to frontend to open Razorpay modal."""
    razorpay_order_id: str
    razorpay_key_id: str
    amount: int                         # in paise
    currency: str
    order_id: UUID
    prefill_name: str | None = None
    prefill_email: str | None = None
    prefill_phone: str | None = None


class RazorpayVerifyRequest(BaseModel):
    """Client-side verification after Razorpay modal success."""
    razorpay_order_id: str
    razorpay_payment_id: str
    razorpay_signature: str
    order_id: UUID


class RazorpayVerifyResponse(BaseModel):
    verified: bool
    order_id: UUID
    order_status: str
    message: str


# ────────────────────────────────────────────────────────
# STRIPE
# ────────────────────────────────────────────────────────

class StripeCreateIntentRequest(BaseModel):
    """Initiate Stripe PaymentIntent for an order."""
    order_id: UUID
    payment_method: str | None = None


class StripeCreateIntentResponse(BaseModel):
    """Returned to frontend for Stripe Elements."""
    client_secret: str
    stripe_publishable_key: str
    amount: int                         # in cents
    currency: str
    order_id: UUID


# ────────────────────────────────────────────────────────
# WEBHOOK SCHEMAS (internal use)
# ────────────────────────────────────────────────────────

class WebhookEventRecord(BaseModel):
    """Represents a row in payment_events for idempotency."""
    id: UUID
    gateway: str
    gateway_event_id: str
    event_type: str
    payload_hash: str | None = None
    order_id: UUID | None = None
    processed: bool = False
    processed_at: datetime | None = None
    created_at: datetime


# ────────────────────────────────────────────────────────
# FX RATES
# ────────────────────────────────────────────────────────

class FXRateResponse(BaseModel):
    """FX rate locked for a checkout session."""
    base_currency: str
    target_currency: str
    rate: Decimal
    source: str
    fetched_at: datetime
    expires_at: datetime


class FXRateLockRequest(BaseModel):
    """Lock an FX rate for checkout."""
    target_currency: str = Field(..., max_length=3, examples=["USD", "EUR", "GBP"])


# ────────────────────────────────────────────────────────
# PAYMENT STATUS
# ────────────────────────────────────────────────────────

class PaymentStatusResponse(BaseModel):
    """Current payment status for an order."""
    order_id: UUID
    payment_status: str
    payment_gateway: str | None = None
    payment_method: str | None = None
    gateway_txn_id: str | None = None
    amount: Decimal
    currency: str
    paid_at: datetime | None = None


# ────────────────────────────────────────────────────────
# REFUND
# ────────────────────────────────────────────────────────

class RefundInitiateRequest(BaseModel):
    """Admin initiates refund for an order."""
    order_id: UUID
    amount: Decimal | None = None       # None = full refund
    reason: str = Field(..., min_length=5, max_length=500)


class RefundResponse(BaseModel):
    refund_id: UUID
    order_id: UUID
    gateway_refund_id: str | None = None
    amount: Decimal
    currency: str
    status: str
    created_at: datetime


# ────────────────────────────────────────────────────────
# UPI PAYMENT (Phase 13G)
# ────────────────────────────────────────────────────────

class UpiCollectRequest(BaseModel):
    """Initiate UPI collect flow — user enters their VPA."""
    order_id: UUID
    vpa: str = Field(
        ...,
        min_length=3,
        max_length=50,
        pattern=r"^[a-zA-Z0-9._-]+@[a-zA-Z]{2,}$",
        examples=["user@paytm", "9876543210@ybl"],
        description="UPI Virtual Payment Address",
    )


class UpiCollectResponse(BaseModel):
    """Response after initiating UPI collect."""
    razorpay_order_id: str
    razorpay_payment_id: str | None = None
    order_id: UUID
    vpa: str
    status: str
    message: str
    poll_url: str


class UpiQrRequest(BaseModel):
    """Request QR code for scan-to-pay."""
    order_id: UUID


class UpiQrResponse(BaseModel):
    """QR code data for UPI scan-to-pay."""
    qr_code_url: str
    razorpay_order_id: str
    order_id: UUID
    amount: int
    currency: str
    expires_at: datetime
    poll_url: str


class UpiPollResponse(BaseModel):
    """Polling response for UPI payment status."""
    order_id: UUID
    payment_status: str
    razorpay_payment_id: str | None = None
    upi_vpa: str | None = None
    message: str
