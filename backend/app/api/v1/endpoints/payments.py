"""
Payment API Endpoints — Phase 8.

Routes:
  POST /api/v1/payments/methods          — Get available methods by country
  POST /api/v1/payments/razorpay/create  — Create Razorpay order
  POST /api/v1/payments/razorpay/verify  — Client-side signature verify
  POST /api/v1/payments/stripe/create    — Create Stripe PaymentIntent
  GET  /api/v1/payments/:order_id/status — Check payment status
  POST /api/v1/payments/fx-rate          — Lock FX rate for checkout

  POST /api/v1/webhooks/razorpay         — Razorpay webhook (no auth)
  POST /api/v1/webhooks/stripe           — Stripe webhook (no auth)

  POST /api/v1/admin/payments/refund     — Admin initiate refund
"""

import json
import logging
from datetime import timedelta
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.middleware.auth import get_current_user, require_role
from app.schemas.payment import (
    FXRateLockRequest,
    FXRateResponse,
    GatewaySelectionRequest,
    PaymentMethodsResponse,
    PaymentStatusResponse,
    RazorpayCreateOrderRequest,
    RazorpayCreateOrderResponse,
    RazorpayVerifyRequest,
    RazorpayVerifyResponse,
    RefundInitiateRequest,
    RefundResponse,
    StripeCreateIntentRequest,
    StripeCreateIntentResponse,
    UpiCollectRequest,
    UpiCollectResponse,
    UpiQrRequest,
    UpiQrResponse,
    UpiPollResponse,
)
from app.services.gateways.razorpay_client import razorpay_client
from app.core.payment_config import get_payment_settings
from app.services.gateways.stripe_client import stripe_client
from app.services.payment_service import PaymentService, PaymentServiceError

logger = logging.getLogger(__name__)

# ────────────────────────────────────────────────────────
# ROUTER SETUP
# ────────────────────────────────────────────────────────

router = APIRouter(prefix="/api/v1", tags=["payments"])
webhook_router = APIRouter(prefix="/api/v1/webhooks", tags=["webhooks"])
admin_payment_router = APIRouter(
    prefix="/api/v1/admin/payments", tags=["admin-payments"]
)


# ────────────────────────────────────────────────────────
# DEPENDENCIES
# ────────────────────────────────────────────────────────

def get_payment_service(db: AsyncSession = Depends(get_db)) -> PaymentService:
    """Factory for PaymentService with DB session."""
    return PaymentService(db=db)


# ════════════════════════════════════════════════════════
# PUBLIC PAYMENT ENDPOINTS (Authenticated user)
# ════════════════════════════════════════════════════════

@router.post(
    "/payments/methods",
    response_model=PaymentMethodsResponse,
    summary="Get available payment methods",
)
async def get_payment_methods(
    body: GatewaySelectionRequest,
    svc: PaymentService = Depends(get_payment_service),
):
    """Returns available payment methods and gateway based on user country."""
    result = svc.select_gateway(body.country_code)
    return PaymentMethodsResponse(**result)


@router.post(
    "/payments/razorpay/create",
    response_model=RazorpayCreateOrderResponse,
    summary="Create Razorpay order for payment",
)
async def create_razorpay_order(
    body: RazorpayCreateOrderRequest,
    current_user=Depends(get_current_user),
    svc: PaymentService = Depends(get_payment_service),
):
    """Create a Razorpay order. Returns params for the Razorpay frontend modal."""
    try:
        result = await svc.create_razorpay_order(
            order_id=body.order_id,
            user_id=current_user.id,
        )
        return RazorpayCreateOrderResponse(**result)
    except PaymentServiceError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post(
    "/payments/razorpay/verify",
    response_model=RazorpayVerifyResponse,
    summary="Verify Razorpay payment signature (client-side)",
)
async def verify_razorpay_payment(
    body: RazorpayVerifyRequest,
    current_user=Depends(get_current_user),
    svc: PaymentService = Depends(get_payment_service),
):
    """Secondary verification after Razorpay modal success."""
    try:
        result = await svc.verify_razorpay_payment(
            razorpay_order_id=body.razorpay_order_id,
            razorpay_payment_id=body.razorpay_payment_id,
            razorpay_signature=body.razorpay_signature,
            order_id=body.order_id,
        )
        return RazorpayVerifyResponse(**result)
    except PaymentServiceError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post(
    "/payments/stripe/create",
    response_model=StripeCreateIntentResponse,
    summary="Create Stripe PaymentIntent",
)
async def create_stripe_intent(
    body: StripeCreateIntentRequest,
    current_user=Depends(get_current_user),
    svc: PaymentService = Depends(get_payment_service),
):
    """Create a Stripe PaymentIntent. Returns client_secret for Stripe Elements."""
    try:
        result = await svc.create_stripe_intent(
            order_id=body.order_id,
            user_id=current_user.id,
        )
        return StripeCreateIntentResponse(**result)
    except PaymentServiceError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get(
    "/payments/{order_id}/status",
    response_model=PaymentStatusResponse,
    summary="Check payment status for an order",
)
async def get_payment_status(
    order_id: UUID,
    current_user=Depends(get_current_user),
    svc: PaymentService = Depends(get_payment_service),
):
    """Returns current payment status, gateway, and transaction details."""
    try:
        result = await svc.get_payment_status(
            order_id=order_id, user_id=current_user.id,
        )
        return PaymentStatusResponse(**result)
    except PaymentServiceError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post(
    "/payments/fx-rate",
    response_model=FXRateResponse,
    summary="Lock FX rate for checkout",
)
async def lock_fx_rate(
    body: FXRateLockRequest,
    current_user=Depends(get_current_user),
    svc: PaymentService = Depends(get_payment_service),
):
    """Lock an exchange rate for a checkout session (INR → target currency)."""
    try:
        rate_info = await svc.fx_service.lock_rate_for_checkout(
            base_currency="INR", target_currency=body.target_currency,
        )
        return FXRateResponse(
            base_currency=rate_info["base_currency"],
            target_currency=rate_info["target_currency"],
            rate=rate_info["rate"],
            source=rate_info["source"],
            fetched_at=rate_info["fetched_at"],
            expires_at=rate_info["fetched_at"] + timedelta(hours=24),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"FX rate fetch failed: {str(e)}")


# ════════════════════════════════════════════════════════

# ---- CHECKOUT CONFIG (Strategy 1 - KEY_ID via backend only) --------

@router.get(
    "/payments/checkout-config",
    summary="Get Razorpay public key for checkout (authenticated only)",
    tags=["UPI Payments"],
)
async def get_checkout_config(
    current_user=Depends(get_current_user),
):
    """
    Returns Razorpay public key_id to authenticated users only.
    Strategy 1: KEY_ID never stored in frontend code/bundle/.env.
    Served dynamically at payment time to authenticated users.
    """
    ps = get_payment_settings()
    if not ps.RAZORPAY_KEY_ID:
        raise HTTPException(
            status_code=503,
            detail="Payment gateway not configured",
        )
    return {"key_id": ps.RAZORPAY_KEY_ID}


# UPI PAYMENT ENDPOINTS (Phase 13G)
# ════════════════════════════════════════════════════════

@router.post(
    "/payments/upi/collect",
    response_model=UpiCollectResponse,
    summary="Initiate UPI collect payment (enter VPA)",
    tags=["UPI Payments"],
)
async def upi_collect(
    body: UpiCollectRequest,
    current_user=Depends(get_current_user),
    svc: PaymentService = Depends(get_payment_service),
):
    """User enters UPI ID (VPA) to receive collect request on their UPI app."""
    try:
        result = await svc.create_upi_collect(
            order_id=body.order_id,
            user_id=current_user.id,
            vpa=body.vpa,
        )
        return UpiCollectResponse(**result)
    except PaymentServiceError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post(
    "/payments/upi/qr",
    response_model=UpiQrResponse,
    summary="Generate UPI QR code for scan-to-pay",
    tags=["UPI Payments"],
)
async def upi_qr(
    body: UpiQrRequest,
    current_user=Depends(get_current_user),
    svc: PaymentService = Depends(get_payment_service),
):
    """Generate QR code for UPI scan-to-pay."""
    try:
        result = await svc.create_upi_qr(
            order_id=body.order_id,
            user_id=current_user.id,
        )
        return UpiQrResponse(**result)
    except PaymentServiceError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get(
    "/payments/{order_id}/upi-poll",
    response_model=UpiPollResponse,
    summary="Poll UPI payment status",
    tags=["UPI Payments"],
)
async def upi_poll(
    order_id: UUID,
    current_user=Depends(get_current_user),
    svc: PaymentService = Depends(get_payment_service),
):
    """Frontend polls this every 3s to check UPI payment confirmation."""
    try:
        result = await svc.poll_upi_status(
            order_id=order_id,
            user_id=current_user.id,
        )
        return UpiPollResponse(**result)
    except PaymentServiceError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ════════════════════════════════════════════════════════
# WEBHOOK ENDPOINTS (No auth — verified by signature)
# ════════════════════════════════════════════════════════

@webhook_router.post("/razorpay", summary="Razorpay webhook handler", status_code=200)
async def razorpay_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """
    Receives Razorpay webhook events.
    CRITICAL: Always return 200 to prevent Razorpay retries on processing errors.
    """
    body = await request.body()
    signature = request.headers.get("X-Razorpay-Signature", "")

    if not razorpay_client.verify_webhook_signature(body, signature):
        logger.warning("Razorpay webhook signature verification failed")
        raise HTTPException(status_code=400, detail="Invalid signature")

    event_data = json.loads(body)
    svc = PaymentService(db=db)
    try:
        result = await svc.process_razorpay_webhook(event_data)
        return result
    except Exception as e:
        logger.error("Razorpay webhook error: %s", str(e))
        return {"status": "error", "detail": "Processing failed, will retry"}


@webhook_router.post("/stripe", summary="Stripe webhook handler", status_code=200)
async def stripe_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """
    Receives Stripe webhook events.
    CRITICAL: Always return 200 to prevent Stripe retries.
    """
    body = await request.body()
    sig_header = request.headers.get("Stripe-Signature", "")

    try:
        event = stripe_client.verify_webhook(body, sig_header)
    except Exception as e:
        logger.warning("Stripe webhook verification failed: %s", str(e))
        raise HTTPException(status_code=400, detail="Invalid signature")

    svc = PaymentService(db=db)
    try:
        result = await svc.process_stripe_webhook(event)
        return result
    except Exception as e:
        logger.error("Stripe webhook error: %s", str(e))
        return {"status": "error", "detail": "Processing failed, will retry"}


# ════════════════════════════════════════════════════════
# ADMIN PAYMENT ENDPOINTS
# ════════════════════════════════════════════════════════

@admin_payment_router.post(
    "/refund",
    response_model=RefundResponse,
    summary="Initiate refund for an order",
)
async def admin_initiate_refund(
    body: RefundInitiateRequest,
    current_user=Depends(require_role("order_manager", "finance_manager", "admin")),
    svc: PaymentService = Depends(get_payment_service),
):
    """Admin (OrderManager/FinanceManager/Admin) initiates a refund."""
    try:
        result = await svc.initiate_refund(
            order_id=body.order_id,
            amount=body.amount,
            reason=body.reason,
            admin_id=current_user.id,
        )
        return RefundResponse(**result)
    except PaymentServiceError as e:
        raise HTTPException(status_code=400, detail=str(e))
