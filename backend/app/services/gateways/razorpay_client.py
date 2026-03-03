"""
Razorpay Gateway Client — India payments.

Handles:
  - Order creation (server-to-server)
  - Payment signature verification
  - Webhook signature verification
  - Refund initiation

Requires: pip install razorpay
"""

import hashlib
import hmac
import logging
from datetime import datetime, timezone, timedelta

import razorpay

from app.core.payment_config import get_payment_settings

logger = logging.getLogger(__name__)

settings = get_payment_settings()


class RazorpayClient:
    """Wrapper around the Razorpay Python SDK."""

    def __init__(self):
        self._client: razorpay.Client | None = None

    @property
    def client(self) -> razorpay.Client:
        if self._client is None:
            if not settings.RAZORPAY_KEY_ID or not settings.RAZORPAY_KEY_SECRET:
                raise RuntimeError(
                    "Razorpay credentials not configured. "
                    "Set RAZORPAY_KEY_ID and RAZORPAY_KEY_SECRET in .env"
                )
            self._client = razorpay.Client(
                auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)
            )
        return self._client

    def create_order(
        self,
        amount_paise: int,
        currency: str = "INR",
        receipt: str | None = None,
        notes: dict | None = None,
    ) -> dict:
        """
        Create a Razorpay order.
        Args:
            amount_paise: Amount in smallest unit (paise for INR).
            currency: ISO 4217 currency code.
            receipt: Internal reference (order_number).
            notes: Optional key-value metadata.
        Returns:
            Razorpay order dict with 'id', 'amount', 'currency', 'status'.
        """
        payload = {
            "amount": amount_paise,
            "currency": currency,
            "receipt": receipt or "",
            "payment_capture": 1,  # auto-capture
        }
        if notes:
            payload["notes"] = notes

        try:
            order = self.client.order.create(data=payload)
            logger.info(
                "Razorpay order created: %s (amount: %d %s)",
                order["id"], amount_paise, currency,
            )
            return order
        except Exception as e:
            logger.error("Razorpay order creation failed: %s", str(e))
            raise

    def verify_payment_signature(
        self,
        razorpay_order_id: str,
        razorpay_payment_id: str,
        razorpay_signature: str,
    ) -> bool:
        """
        Verify the signature returned by Razorpay modal on client side.
        This is a secondary check — primary confirmation is via webhook.
        """
        try:
            self.client.utility.verify_payment_signature({
                "razorpay_order_id": razorpay_order_id,
                "razorpay_payment_id": razorpay_payment_id,
                "razorpay_signature": razorpay_signature,
            })
            return True
        except razorpay.errors.SignatureVerificationError:
            logger.warning(
                "Razorpay signature verification failed for order %s",
                razorpay_order_id,
            )
            return False

    @staticmethod
    def verify_webhook_signature(body: bytes, signature: str) -> bool:
        """Verify Razorpay webhook signature (HMAC-SHA256)."""
        if not settings.RAZORPAY_WEBHOOK_SECRET:
            logger.error("RAZORPAY_WEBHOOK_SECRET not configured")
            return False

        expected = hmac.new(
            key=settings.RAZORPAY_WEBHOOK_SECRET.encode("utf-8"),
            msg=body,
            digestmod=hashlib.sha256,
        ).hexdigest()

        return hmac.compare_digest(expected, signature)

    def fetch_payment(self, payment_id: str) -> dict:
        """Fetch payment details from Razorpay."""
        try:
            return self.client.payment.fetch(payment_id)
        except Exception as e:
            logger.error("Razorpay fetch payment %s failed: %s", payment_id, str(e))
            raise

    def create_refund(
        self,
        payment_id: str,
        amount_paise: int | None = None,
        notes: dict | None = None,
    ) -> dict:
        """
        Initiate a refund via Razorpay.
        Args:
            payment_id: Razorpay payment ID (pay_XXXX).
            amount_paise: Partial refund amount. None = full refund.
        """
        payload = {}
        if amount_paise is not None:
            payload["amount"] = amount_paise
        if notes:
            payload["notes"] = notes

        try:
            refund = self.client.payment.refund(payment_id, payload)
            logger.info(
                "Razorpay refund created: %s for payment %s",
                refund.get("id"), payment_id,
            )
            return refund
        except Exception as e:
            logger.error("Razorpay refund failed for payment %s: %s", payment_id, str(e))
            raise

    def create_qr_code(self, amount_paise: int, description: str, notes: dict = None) -> dict:
        """Create a UPI QR code for scan-to-pay."""
        payload = {
            "type": "upi_qr",
            "name": "Ashmi Store",
            "usage": "single_use",
            "fixed_amount": True,
            "payment_amount": amount_paise,
            "description": description,
            "close_by": int((datetime.now(timezone.utc) + timedelta(minutes=5)).timestamp()),
        }
        if notes:
            payload["notes"] = notes
        return self.client.qrcode.create(payload)

    def fetch_order_payments(self, razorpay_order_id: str) -> dict:
        """Fetch all payments for a Razorpay order (for UPI polling)."""
        return self.client.order.payments(razorpay_order_id)


# Singleton
razorpay_client = RazorpayClient()
