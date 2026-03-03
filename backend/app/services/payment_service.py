"""
Payment Service — Core business logic for Phase 8.

Orchestrates:
  1. Gateway selection (country → Razorpay or Stripe)
  2. Payment initiation (create Razorpay order / Stripe PaymentIntent)
  3. Client-side verification (Razorpay signature)
  4. Webhook processing with idempotency
  5. State machine transition on success/failure
  6. Stock deduction on success
  7. Reservation release on failure
  8. Refund initiation
"""

import logging
from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.payment_config import get_payment_settings
from app.repositories.payment_repository import PaymentRepository
from app.services.gateways.razorpay_client import razorpay_client
from app.services.gateways.stripe_client import stripe_client
from app.services.fx_rate_service import get_fx_service
from app.services.store_settings_service import StoreSettingsService

logger = logging.getLogger(__name__)

settings = get_payment_settings()


class PaymentServiceError(Exception):
    """Base error for payment service."""
    pass


class PaymentService:
    """Stateless service — injected with a DB session per request."""

    def __init__(self, db: AsyncSession, redis_client=None):
        self.db = db
        self.repo = PaymentRepository(db)
        self.fx_service = get_fx_service(redis_client)

    # ════════════════════════════════════════════════
    # 1. GATEWAY SELECTION
    # ════════════════════════════════════════════════

    def select_gateway(self, country_code: str) -> dict:
        """Route user to correct payment gateway based on country."""
        country = country_code.upper()
        if country == "IN":
            return {
                "gateway": "razorpay",
                "methods": settings.INDIA_METHODS,
                "currency": "INR",
            }
        return {
            "gateway": "stripe",
            "methods": settings.GLOBAL_METHODS,
            "currency": "USD",
        }

    # ════════════════════════════════════════════════
    # 2. RAZORPAY: CREATE ORDER
    # ════════════════════════════════════════════════

    async def create_razorpay_order(self, order_id: UUID, user_id: UUID) -> dict:
        """Create a Razorpay order for the given internal order."""
        order = await self.repo.get_order(order_id)
        if not order:
            raise PaymentServiceError(f"Order {order_id} not found")
        if str(order.user_id) != str(user_id):
            raise PaymentServiceError("Order does not belong to this user")
        if order.order_status != "placed":
            raise PaymentServiceError(
                f"Cannot initiate payment for order in '{order.order_status}' status"
            )
        if order.payment_status not in ("pending", "failed"):
            raise PaymentServiceError(
                f"Payment already in '{order.payment_status}' state"
            )

        amount_paise = int(
            (order.grand_total * 100).to_integral_value(rounding=ROUND_HALF_UP)
        )

        rz_order = razorpay_client.create_order(
            amount_paise=amount_paise,
            currency=order.currency or "INR",
            receipt=order.order_number,
            notes={"order_id": str(order_id), "order_number": order.order_number},
        )

        await self.repo.update_order_payment(
            order_id=order_id,
            payment_status="pending",
            payment_gateway="razorpay",
            payment_gateway_order_id=rz_order["id"],
        )
        await self.db.flush()

        user = await self.repo.get_user(user_id)

        return {
            "razorpay_order_id": rz_order["id"],
            "razorpay_key_id": settings.RAZORPAY_KEY_ID,
            "amount": amount_paise,
            "currency": order.currency or "INR",
            "order_id": order_id,
            "prefill_name": f"{user.first_name or ''} {user.last_name or ''}".strip() if user else None,
            "prefill_email": user.email if user else None,
            "prefill_phone": user.phone if user else None,
        }

    # ════════════════════════════════════════════════
    # 3. RAZORPAY: CLIENT-SIDE VERIFICATION
    # ════════════════════════════════════════════════

    async def verify_razorpay_payment(
        self,
        razorpay_order_id: str,
        razorpay_payment_id: str,
        razorpay_signature: str,
        order_id: UUID,
    ) -> dict:
        """Secondary verification after Razorpay modal success."""
        verified = razorpay_client.verify_payment_signature(
            razorpay_order_id=razorpay_order_id,
            razorpay_payment_id=razorpay_payment_id,
            razorpay_signature=razorpay_signature,
        )

        if verified:
            # Call central payment success handler (idempotent -
            # safe if webhook also fires in production).
            # Transitions: placed -> confirmed, deducts stock.
            await self._handle_payment_success(
                order_id=order_id,
                gateway="razorpay",
                gateway_txn_id=razorpay_payment_id,
                payment_method="upi",
            )
            await self.db.flush()
            return {
                "verified": True,
                "order_id": order_id,
                "order_status": "confirmed",
                "payment_status": "paid",
                "status": "success",
                "message": "Payment verified and confirmed.",
            }

        return {
            "verified": False,
            "order_id": order_id,
            "order_status": "placed",
            "payment_status": "pending",
            "status": "failed",
            "message": "Payment signature verification failed.",
        }

    # ════════════════════════════════════════════════
    # 4. STRIPE: CREATE PAYMENT INTENT
    # ════════════════════════════════════════════════

    async def create_upi_collect(self, order_id: UUID, user_id: UUID, vpa: str) -> dict:
        """Initiate UPI collect request via Razorpay."""
        order = await self.repo.get_order(order_id)
        if not order:
            raise PaymentServiceError(f"Order {order_id} not found")
        if str(order.user_id) != str(user_id):
            raise PaymentServiceError("Order does not belong to this user")
        if order.order_status != "placed":
            raise PaymentServiceError(
                f"Cannot initiate payment for order in '{order.order_status}' status"
            )
        if order.payment_status not in ("pending", "failed"):
            raise PaymentServiceError(
                f"Payment already in '{order.payment_status}' state"
            )

        amount_paise = int(
            (order.grand_total * 100).to_integral_value(rounding=ROUND_HALF_UP)
        )

        rz_order_id = order.payment_gateway_order_id
        if not rz_order_id:
            rz_order = razorpay_client.create_order(
                amount_paise=amount_paise,
                currency=order.currency or "INR",
                receipt=order.order_number,
                notes={"order_id": str(order_id), "order_number": order.order_number},
            )
            rz_order_id = rz_order["id"]

        await self.repo.update_order_payment(
            order_id=order_id,
            payment_status="pending",
            payment_gateway="razorpay",
            payment_method="upi",
            payment_gateway_order_id=rz_order_id,
        )
        await self.repo.update_order_upi_vpa(order_id, vpa)
        await self.db.flush()

        # Read configured merchant VPA from store_settings (Phase 13H)
        merchant_vpa = await StoreSettingsService.get_merchant_vpa_value(self.db)

        return {
            "razorpay_order_id": rz_order_id,
            "razorpay_payment_id": None,
            "order_id": order_id,
            "vpa": vpa,
            "merchant_vpa": merchant_vpa,
            "status": "pending",
            "message": "UPI collect request initiated. Approve on your UPI app.",
            "poll_url": f"/api/v1/payments/{order_id}/upi-poll",
        }

    async def create_upi_qr(self, order_id: UUID, user_id: UUID) -> dict:
        """Generate a UPI QR code for scan-to-pay via Razorpay."""
        order = await self.repo.get_order(order_id)
        if not order:
            raise PaymentServiceError(f"Order {order_id} not found")
        if str(order.user_id) != str(user_id):
            raise PaymentServiceError("Order does not belong to this user")
        if order.order_status != "placed":
            raise PaymentServiceError(
                f"Cannot initiate payment for order in '{order.order_status}' status"
            )
        if order.payment_status not in ("pending", "failed"):
            raise PaymentServiceError(
                f"Payment already in '{order.payment_status}' state"
            )

        amount_paise = int(
            (order.grand_total * 100).to_integral_value(rounding=ROUND_HALF_UP)
        )

        rz_order_id = order.payment_gateway_order_id
        if not rz_order_id:
            rz_order = razorpay_client.create_order(
                amount_paise=amount_paise,
                currency=order.currency or "INR",
                receipt=order.order_number,
                notes={"order_id": str(order_id), "order_number": order.order_number},
            )
            rz_order_id = rz_order["id"]

        qr_data = razorpay_client.create_qr_code(
            amount_paise=amount_paise,
            description=f"Order {order.order_number}",
            notes={"order_id": str(order_id)},
        )

        # Read configured merchant VPA from store_settings (Phase 13H)
        merchant_vpa = await StoreSettingsService.get_merchant_vpa_value(self.db)

        await self.repo.update_order_payment(
            order_id=order_id,
            payment_status="pending",
            payment_gateway="razorpay",
            payment_method="upi",
            payment_gateway_order_id=rz_order_id,
        )
        await self.db.flush()

        from datetime import timedelta
        expires = datetime.now(timezone.utc) + timedelta(minutes=5)

        return {
            "qr_code_url": qr_data.get("image_url", ""),
            "razorpay_order_id": rz_order_id,
            "order_id": order_id,
            "amount": amount_paise,
            "currency": order.currency or "INR",
            "merchant_vpa": merchant_vpa,
            "expires_at": expires,
            "poll_url": f"/api/v1/payments/{order_id}/upi-poll",
        }

    async def poll_upi_status(self, order_id: UUID, user_id: UUID) -> dict:
        """Poll Razorpay for UPI payment status."""
        order = await self.repo.get_order(order_id)
        if not order:
            raise PaymentServiceError(f"Order {order_id} not found")
        if str(order.user_id) != str(user_id):
            raise PaymentServiceError("Order does not belong to this user")

        if order.payment_status == "paid":
            return {
                "order_id": order_id,
                "payment_status": "paid",
                "razorpay_payment_id": order.payment_gateway_txn_id,
                "upi_vpa": order.upi_vpa,
                "message": "Payment successful!",
            }
        if order.payment_status == "failed":
            return {
                "order_id": order_id,
                "payment_status": "failed",
                "razorpay_payment_id": None,
                "upi_vpa": order.upi_vpa,
                "message": "Payment failed. Please retry.",
            }

        rz_order_id = order.payment_gateway_order_id
        if rz_order_id:
            try:
                rz_payments = razorpay_client.fetch_order_payments(rz_order_id)
                for payment in rz_payments.get("items", []):
                    if payment.get("status") == "captured":
                        vpa = payment.get("vpa", order.upi_vpa)
                        await self._handle_payment_success(
                            order_id=order_id,
                            gateway="razorpay",
                            gateway_txn_id=payment["id"],
                            payment_method="upi",
                        )
                        if vpa:
                            await self.repo.update_order_upi_vpa(order_id, vpa)
                        await self.db.flush()
                        return {
                            "order_id": order_id,
                            "payment_status": "paid",
                            "razorpay_payment_id": payment["id"],
                            "upi_vpa": vpa,
                            "message": "Payment successful!",
                        }
                    elif payment.get("status") == "failed":
                        await self._handle_payment_failure(
                            order_id=order_id, gateway="razorpay"
                        )
                        await self.db.flush()
                        return {
                            "order_id": order_id,
                            "payment_status": "failed",
                            "razorpay_payment_id": payment["id"],
                            "upi_vpa": order.upi_vpa,
                            "message": "Payment failed. Please retry.",
                        }
            except Exception as e:
                logger.warning("UPI poll check failed for order %s: %s", order_id, str(e))

        return {
            "order_id": order_id,
            "payment_status": "pending",
            "razorpay_payment_id": None,
            "upi_vpa": order.upi_vpa,
            "message": "Waiting for UPI payment confirmation...",
        }

    # ════════════════════════════════════════════════
    # 4b. STRIPE: CREATE PAYMENT INTENT
    # ════════════════════════════════════════════════

    async def create_stripe_intent(self, order_id: UUID, user_id: UUID) -> dict:
        """Create a Stripe PaymentIntent for the given order."""
        order = await self.repo.get_order(order_id)
        if not order:
            raise PaymentServiceError(f"Order {order_id} not found")
        if str(order.user_id) != str(user_id):
            raise PaymentServiceError("Order does not belong to this user")
        if order.order_status != "placed":
            raise PaymentServiceError(
                f"Cannot initiate payment for order in '{order.order_status}' status"
            )
        if order.payment_status not in ("pending", "failed"):
            raise PaymentServiceError(
                f"Payment already in '{order.payment_status}' state"
            )

        target_currency = order.currency or "USD"
        if target_currency.upper() == "INR":
            amount_decimal = order.grand_total
        else:
            if order.fx_rate_used and order.fx_rate_used != Decimal("1.0"):
                amount_decimal = order.grand_total * order.fx_rate_used
            else:
                rate_info = await self.fx_service.lock_rate_for_checkout(
                    base_currency="INR", target_currency=target_currency,
                )
                amount_decimal = order.grand_total * rate_info["rate"]
                await self.repo.lock_fx_rate_on_order(
                    order_id=order_id,
                    fx_rate=rate_info["rate"],
                    fx_source=rate_info["source"],
                    currency=target_currency,
                )

        amount_cents = int(
            (amount_decimal * 100).to_integral_value(rounding=ROUND_HALF_UP)
        )

        user = await self.repo.get_user(user_id)

        intent = stripe_client.create_payment_intent(
            amount_cents=amount_cents,
            currency=target_currency.lower(),
            metadata={"order_id": str(order_id), "order_number": order.order_number},
            receipt_email=user.email if user else None,
        )

        await self.repo.update_order_payment(
            order_id=order_id,
            payment_status="pending",
            payment_gateway="stripe",
            payment_gateway_order_id=intent.id,
        )
        await self.db.flush()

        return {
            "client_secret": intent.client_secret,
            "stripe_publishable_key": settings.STRIPE_PUBLISHABLE_KEY,
            "amount": amount_cents,
            "currency": target_currency.lower(),
            "order_id": order_id,
        }

    # ════════════════════════════════════════════════
    # 5. WEBHOOK PROCESSING (RAZORPAY)
    # ════════════════════════════════════════════════

    async def process_razorpay_webhook(self, event_data: dict) -> dict:
        """Process Razorpay webhook event with idempotency."""
        event_type = event_data.get("event", "")
        payload = event_data.get("payload", {})
        entity = payload.get("payment", {}).get("entity", {})
        gateway_event_id = entity.get("id", "")

        if not gateway_event_id:
            logger.warning("Razorpay webhook missing payment ID")
            return {"status": "ignored", "reason": "no_payment_id"}

        # Idempotency check
        existing = await self.repo.find_payment_event(gateway_event_id)
        if existing and existing.processed:
            logger.info("Razorpay event %s already processed, skipping", gateway_event_id)
            return {"status": "duplicate", "event_id": gateway_event_id}

        # Extract order_id from notes
        order_id = None
        notes = entity.get("notes", {})
        order_id_str = notes.get("order_id")
        if order_id_str:
            try:
                order_id = UUID(order_id_str)
            except ValueError:
                pass

        event_record = existing or await self.repo.create_payment_event(
            gateway="razorpay",
            gateway_event_id=gateway_event_id,
            event_type=event_type,
            payload=event_data,
            order_id=order_id,
        )
        await self.db.flush()

        try:
            if event_type == "payment.captured":
                payment_method = entity.get("method", "unknown")
                await self._handle_payment_success(
                    order_id=order_id, gateway="razorpay",
                    gateway_txn_id=gateway_event_id,
                    payment_method=payment_method,
                )
                # Store UPI VPA from webhook if available
                if payment_method == "upi" and order_id:
                    vpa = entity.get("vpa")
                    if vpa:
                        await self.repo.update_order_upi_vpa(order_id, vpa)
            elif event_type == "payment.failed":
                await self._handle_payment_failure(order_id=order_id, gateway="razorpay")
            elif event_type == "refund.processed":
                refund_entity = payload.get("refund", {}).get("entity", {})
                await self._handle_refund_webhook(
                    gateway_refund_id=refund_entity.get("id"), status="completed",
                )
            else:
                logger.info("Razorpay event type '%s' not handled", event_type)

            await self.repo.mark_event_processed(event_record.id)
            await self.db.flush()
            return {"status": "processed", "event_type": event_type}

        except Exception as e:
            logger.error("Razorpay webhook processing failed for %s: %s", gateway_event_id, str(e))
            raise

    # ════════════════════════════════════════════════
    # 6. WEBHOOK PROCESSING (STRIPE)
    # ════════════════════════════════════════════════

    async def process_stripe_webhook(self, event: object) -> dict:
        """Process Stripe webhook event with idempotency."""
        event_type = event.type
        event_id = event.id

        existing = await self.repo.find_payment_event(event_id)
        if existing and existing.processed:
            logger.info("Stripe event %s already processed, skipping", event_id)
            return {"status": "duplicate", "event_id": event_id}

        order_id = None
        data_object = event.data.object
        metadata = getattr(data_object, "metadata", {}) or {}
        order_id_str = metadata.get("order_id")
        if order_id_str:
            try:
                order_id = UUID(order_id_str)
            except ValueError:
                pass

        event_record = existing or await self.repo.create_payment_event(
            gateway="stripe",
            gateway_event_id=event_id,
            event_type=event_type,
            payload={"id": event_id, "type": event_type},
            order_id=order_id,
        )
        await self.db.flush()

        try:
            if event_type == "payment_intent.succeeded":
                payment_method_type = "card"
                if hasattr(data_object, "payment_method_types"):
                    types = data_object.payment_method_types
                    payment_method_type = types[0] if types else "card"
                await self._handle_payment_success(
                    order_id=order_id, gateway="stripe",
                    gateway_txn_id=data_object.id,
                    payment_method=payment_method_type,
                )
            elif event_type == "payment_intent.payment_failed":
                await self._handle_payment_failure(order_id=order_id, gateway="stripe")
            elif event_type == "charge.refunded":
                await self._handle_refund_webhook(
                    gateway_refund_id=data_object.id, status="completed",
                )
            else:
                logger.info("Stripe event type '%s' not handled", event_type)

            await self.repo.mark_event_processed(event_record.id)
            await self.db.flush()
            return {"status": "processed", "event_type": event_type}

        except Exception as e:
            logger.error("Stripe webhook processing failed for %s: %s", event_id, str(e))
            raise

    # ════════════════════════════════════════════════
    # 7. PAYMENT SUCCESS HANDLER
    # ════════════════════════════════════════════════

    async def _handle_payment_success(
        self, order_id: UUID | None, gateway: str,
        gateway_txn_id: str, payment_method: str,
    ):
        """
        Central handler for payment success from any gateway.
          1. State Machine: placed → confirmed
          2. Deduct stock permanently
          3. Confirm reservation
          4. Update payment fields
          5. Log in order_status_history
        """
        if not order_id:
            logger.error("Payment success webhook has no order_id in metadata")
            return

        order = await self.repo.get_order(order_id)
        if not order:
            logger.error("Order %s not found for payment success", order_id)
            return

        if order.payment_status == "paid":
            logger.info("Order %s already marked paid, skipping", order_id)
            return

        from app.services.order_state_machine import validate_transition

        current_status = order.order_status
        try:
            validate_transition(current_status, "confirmed")
        except Exception as e:
            logger.error(
                "Cannot transition order %s from %s to confirmed: %s",
                order_id, current_status, str(e),
            )
            await self.repo.update_order_payment(
                order_id=order_id, payment_status="paid",
                payment_gateway=gateway, payment_gateway_txn_id=gateway_txn_id,
                payment_method=payment_method,
            )
            return

        await self.repo.deduct_stock_for_order(order_id)
        await self.repo.confirm_reservations(order_id)
        await self.repo.update_order_payment(
            order_id=order_id, payment_status="paid",
            payment_gateway=gateway, payment_gateway_txn_id=gateway_txn_id,
            payment_method=payment_method, order_status="confirmed",
        )
        await self.repo.add_status_history(
            order_id=order_id, from_status=current_status, to_status="confirmed",
            changed_by=None,
            reason=f"Payment confirmed via {gateway} ({gateway_txn_id})",
        )

        logger.info("Order %s payment SUCCESS: %s → confirmed, stock deducted", order_id, current_status)


        # ── Step 6: Generate Invoice (Phase 9) ──
        try:
            from app.services.invoice_service import InvoiceService
            invoice_svc = InvoiceService(self.db)
            await invoice_svc.generate_invoice(order_id)
            logger.info("Invoice generated for order %s", order_id)
        except Exception as inv_err:
            logger.error("Invoice generation failed for order %s: %s", order_id, str(inv_err))
            # Non-fatal: order is already confirmed and paid
            await self.db.rollback()
            # Admin can regenerate via POST /api/v1/admin/invoices/{order_id}/regenerate

    # ════════════════════════════════════════════════
    # 8. PAYMENT FAILURE HANDLER
    # ════════════════════════════════════════════════

    async def _handle_payment_failure(self, order_id: UUID | None, gateway: str):
        """Release reservation and mark payment failed."""
        if not order_id:
            logger.error("Payment failure webhook has no order_id")
            return

        order = await self.repo.get_order(order_id)
        if not order:
            logger.error("Order %s not found for payment failure", order_id)
            return

        await self.repo.release_reservations(order_id)
        await self.repo.update_order_payment(order_id=order_id, payment_status="failed")
        logger.info("Order %s payment FAILED via %s: reservations released", order_id, gateway)

    # ════════════════════════════════════════════════
    # 9. REFUND WEBHOOK HANDLER
    # ════════════════════════════════════════════════

    async def _handle_refund_webhook(self, gateway_refund_id: str | None, status: str):
        """Update refund record when gateway confirms refund completion."""
        if not gateway_refund_id:
            return

        from app.models.models import Refund
        from sqlalchemy import select

        result = await self.db.execute(
            select(Refund).where(Refund.gateway_refund_id == gateway_refund_id)
        )
        refund = result.scalar_one_or_none()
        if refund:
            await self.repo.update_refund_status(refund_id=refund.id, status=status)
            logger.info("Refund %s updated to %s via webhook", gateway_refund_id, status)

    # ════════════════════════════════════════════════
    # 10. REFUND INITIATION (Admin-triggered)
    # ════════════════════════════════════════════════

    async def initiate_refund(
        self, order_id: UUID, amount: Decimal | None,
        reason: str, admin_id: UUID,
    ) -> dict:
        """Admin initiates a refund for an order."""
        order = await self.repo.get_order(order_id)
        if not order:
            raise PaymentServiceError(f"Order {order_id} not found")
        if order.payment_status != "paid":
            raise PaymentServiceError(
                f"Cannot refund order with payment_status '{order.payment_status}'"
            )

        refund_amount = amount or order.grand_total
        gateway = order.payment_gateway
        gateway_txn_id = order.payment_gateway_txn_id

        if not gateway or not gateway_txn_id:
            raise PaymentServiceError("Order has no payment gateway info — cannot process refund")

        gateway_refund_id = None

        if gateway == "razorpay":
            amount_paise = int(
                (refund_amount * 100).to_integral_value(rounding=ROUND_HALF_UP)
            )
            rz_refund = razorpay_client.create_refund(
                payment_id=gateway_txn_id,
                amount_paise=amount_paise if amount else None,
                notes={"order_id": str(order_id), "reason": reason},
            )
            gateway_refund_id = rz_refund.get("id")

        elif gateway == "stripe":
            amount_cents = int(
                (refund_amount * 100).to_integral_value(rounding=ROUND_HALF_UP)
            )
            stripe_refund = stripe_client.create_refund(
                payment_intent_id=order.payment_gateway_order_id,
                amount_cents=amount_cents if amount else None,
                reason="requested_by_customer",
                metadata={"order_id": str(order_id)},
            )
            gateway_refund_id = stripe_refund.id
        else:
            raise PaymentServiceError(f"Unknown gateway: {gateway}")

        refund = await self.repo.create_refund(
            order_id=order_id, amount=refund_amount,
            currency=order.currency or "INR", refund_method=gateway,
            initiated_by=admin_id, gateway_refund_id=gateway_refund_id,
        )

        await self.repo.update_order_payment(
            order_id=order_id, payment_status="refund_initiated",
        )
        await self.db.flush()

        logger.info(
            "Refund initiated for order %s: %s %s via %s (gateway: %s)",
            order_id, refund_amount, order.currency, gateway, gateway_refund_id,
        )

        return {
            "refund_id": refund.id, "order_id": order_id,
            "gateway_refund_id": gateway_refund_id, "amount": refund_amount,
            "currency": order.currency or "INR", "status": "initiated",
            "created_at": refund.created_at,
        }

    # ════════════════════════════════════════════════
    # 11. PAYMENT STATUS CHECK
    # ════════════════════════════════════════════════

    async def get_payment_status(self, order_id: UUID, user_id: UUID) -> dict:
        """Get current payment status for an order."""
        order = await self.repo.get_order(order_id)
        if not order:
            raise PaymentServiceError(f"Order {order_id} not found")
        if str(order.user_id) != str(user_id):
            raise PaymentServiceError("Order does not belong to this user")

        return {
            "order_id": order_id,
            "payment_status": order.payment_status,
            "payment_gateway": order.payment_gateway,
            "payment_method": order.payment_method,
            "gateway_txn_id": order.payment_gateway_txn_id,
            "amount": order.grand_total,
            "currency": order.currency or "INR",
            "paid_at": None,
        }
