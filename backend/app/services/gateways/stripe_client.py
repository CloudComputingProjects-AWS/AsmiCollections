"""
Stripe Gateway Client — Global payments.

Handles:
  - PaymentIntent creation
  - Webhook signature verification
  - Refund initiation

Requires: pip install stripe
"""

import logging

import stripe

from app.core.payment_config import get_payment_settings

logger = logging.getLogger(__name__)

settings = get_payment_settings()


class StripeClient:
    """Wrapper around the Stripe Python SDK."""

    def __init__(self):
        self._initialized = False

    def _ensure_init(self):
        if not self._initialized:
            if not settings.STRIPE_SECRET_KEY:
                raise RuntimeError(
                    "Stripe credentials not configured. "
                    "Set STRIPE_SECRET_KEY in .env"
                )
            stripe.api_key = settings.STRIPE_SECRET_KEY
            self._initialized = True

    def create_payment_intent(
        self,
        amount_cents: int,
        currency: str = "usd",
        metadata: dict | None = None,
        receipt_email: str | None = None,
    ) -> stripe.PaymentIntent:
        """
        Create a Stripe PaymentIntent.
        Args:
            amount_cents: Amount in smallest unit (cents for USD).
            currency: ISO 4217 lowercase currency code.
            metadata: Key-value pairs (order_id, order_number, etc.).
        Returns:
            Stripe PaymentIntent object with client_secret.
        """
        self._ensure_init()

        try:
            intent = stripe.PaymentIntent.create(
                amount=amount_cents,
                currency=currency.lower(),
                automatic_payment_methods={"enabled": True},
                metadata=metadata or {},
                receipt_email=receipt_email,
            )
            logger.info(
                "Stripe PaymentIntent created: %s (amount: %d %s)",
                intent.id, amount_cents, currency,
            )
            return intent
        except stripe.error.StripeError as e:
            logger.error("Stripe PaymentIntent creation failed: %s", str(e))
            raise

    @staticmethod
    def verify_webhook(payload: bytes, sig_header: str) -> stripe.Event:
        """
        Verify and construct a Stripe webhook event.
        Raises:
            stripe.error.SignatureVerificationError: If signature invalid.
        """
        if not settings.STRIPE_WEBHOOK_SECRET:
            raise RuntimeError("STRIPE_WEBHOOK_SECRET not configured")

        event = stripe.Webhook.construct_event(
            payload=payload,
            sig_header=sig_header,
            secret=settings.STRIPE_WEBHOOK_SECRET,
        )
        return event

    def fetch_payment_intent(self, intent_id: str) -> stripe.PaymentIntent:
        """Retrieve a PaymentIntent by ID."""
        self._ensure_init()
        try:
            return stripe.PaymentIntent.retrieve(intent_id)
        except stripe.error.StripeError as e:
            logger.error("Stripe fetch intent %s failed: %s", intent_id, str(e))
            raise

    def create_refund(
        self,
        payment_intent_id: str,
        amount_cents: int | None = None,
        reason: str = "requested_by_customer",
        metadata: dict | None = None,
    ) -> stripe.Refund:
        """
        Initiate a refund via Stripe.
        Args:
            payment_intent_id: Stripe PaymentIntent ID (pi_XXXX).
            amount_cents: Partial refund amount. None = full refund.
        """
        self._ensure_init()

        params = {
            "payment_intent": payment_intent_id,
            "reason": reason,
            "metadata": metadata or {},
        }
        if amount_cents is not None:
            params["amount"] = amount_cents

        try:
            refund = stripe.Refund.create(**params)
            logger.info(
                "Stripe refund created: %s for intent %s",
                refund.id, payment_intent_id,
            )
            return refund
        except stripe.error.StripeError as e:
            logger.error("Stripe refund failed for intent %s: %s", payment_intent_id, str(e))
            raise


# Singleton
stripe_client = StripeClient()
