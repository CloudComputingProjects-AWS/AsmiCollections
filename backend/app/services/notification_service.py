"""
Notification Service — Email & SMS notifications for order lifecycle events.
Phase 10 — V2.5 Blueprint

Stubs for AWS SES / SendGrid (email) and MSG91 / Twilio (SMS).
Replace stubs with actual API calls when ready.
"""

import logging
import os
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.models import Order, User

logger = logging.getLogger(__name__)


class NotificationService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def send_order_confirmation(self, order_id: UUID) -> bool:
        """Send order confirmation email with invoice link."""
        order, user = await self._load_order_user(order_id)
        if not user:
            return False

        subject = f"Order Confirmed — {order.order_number}"
        body = (
            f"Hi {user.first_name or 'Customer'},\n\n"
            f"Your order {order.order_number} has been confirmed!\n"
            f"Total: {order.currency} {order.grand_total}\n\n"
            f"You can download your invoice from your order details page.\n\n"
            f"Thank you for shopping with us!"
        )

        return await self._send_email(user.email, subject, body)

    async def send_shipping_notification(self, order_id: UUID, tracking_url: str | None = None) -> bool:
        """Notify customer that order has been shipped."""
        order, user = await self._load_order_user(order_id)
        if not user:
            return False

        subject = f"Order Shipped — {order.order_number}"
        body = (
            f"Hi {user.first_name or 'Customer'},\n\n"
            f"Your order {order.order_number} has been shipped!\n"
        )
        if tracking_url:
            body += f"Track your order: {tracking_url}\n"
        body += "\nThank you for shopping with us!"

        return await self._send_email(user.email, subject, body)

    async def send_delivery_notification(self, order_id: UUID) -> bool:
        """Notify customer that order has been delivered."""
        order, user = await self._load_order_user(order_id)
        if not user:
            return False

        subject = f"Order Delivered — {order.order_number}"
        body = (
            f"Hi {user.first_name or 'Customer'},\n\n"
            f"Your order {order.order_number} has been delivered!\n\n"
            f"We hope you love your purchase. If you need to return any items, "
            f"you can do so from your order details page within the return window.\n\n"
            f"Thank you!"
        )

        return await self._send_email(user.email, subject, body)

    async def send_return_approved_notification(self, order_id: UUID, pickup_date=None) -> bool:
        """Notify customer that return has been approved."""
        order, user = await self._load_order_user(order_id)
        if not user:
            return False

        subject = f"Return Approved — {order.order_number}"
        body = (
            f"Hi {user.first_name or 'Customer'},\n\n"
            f"Your return request for order {order.order_number} has been approved.\n"
        )
        if pickup_date:
            body += f"Pickup scheduled for: {pickup_date}\n"
        body += "\nPlease keep the items ready for pickup."

        return await self._send_email(user.email, subject, body)

    async def send_return_rejected_notification(self, order_id: UUID, reason: str | None = None) -> bool:
        """Notify customer that return has been rejected."""
        order, user = await self._load_order_user(order_id)
        if not user:
            return False

        subject = f"Return Update — {order.order_number}"
        body = (
            f"Hi {user.first_name or 'Customer'},\n\n"
            f"We were unable to approve the return for order {order.order_number}.\n"
        )
        if reason:
            body += f"Reason: {reason}\n"
        body += "\nPlease contact support if you have questions."

        return await self._send_email(user.email, subject, body)

    async def send_refund_notification(self, order_id: UUID, amount=None) -> bool:
        """Notify customer that refund has been processed."""
        order, user = await self._load_order_user(order_id)
        if not user:
            return False

        subject = f"Refund Processed — {order.order_number}"
        body = (
            f"Hi {user.first_name or 'Customer'},\n\n"
            f"Your refund for order {order.order_number} has been processed.\n"
        )
        if amount:
            body += f"Amount: {order.currency} {amount}\n"
        body += (
            "\nThe refund will reflect in your account within 5-7 business days.\n\n"
            "Thank you!"
        )

        return await self._send_email(user.email, subject, body)

    async def send_cancellation_notification(self, order_id: UUID) -> bool:
        """Notify customer that order has been cancelled."""
        order, user = await self._load_order_user(order_id)
        if not user:
            return False

        subject = f"Order Cancelled — {order.order_number}"
        body = (
            f"Hi {user.first_name or 'Customer'},\n\n"
            f"Your order {order.order_number} has been cancelled.\n"
            f"If payment was made, a refund will be processed within 5-7 business days.\n\n"
            f"Thank you!"
        )

        return await self._send_email(user.email, subject, body)

    # ──────────────── Email Backend (Stub) ────────────────

    async def _send_email(self, to: str, subject: str, body: str) -> bool:
        """
        Send email via AWS SES or SendGrid.
        Currently a stub — replace with actual implementation.
        """
        provider = os.getenv("EMAIL_PROVIDER", "stub")

        if provider == "ses":
            return await self._send_via_ses(to, subject, body)
        elif provider == "sendgrid":
            return await self._send_via_sendgrid(to, subject, body)
        else:
            # Stub: log the email
            logger.info(f"[EMAIL STUB] To: {to} | Subject: {subject}")
            logger.debug(f"[EMAIL STUB] Body: {body[:200]}...")
            return True

    async def _send_via_ses(self, to: str, subject: str, body: str) -> bool:
        """AWS SES integration stub."""
        try:
            # import aioboto3
            # session = aioboto3.Session()
            # async with session.client("ses", region_name="ap-south-1") as ses:
            #     await ses.send_email(
            #         Source=os.getenv("EMAIL_FROM", "noreply@yourstore.com"),
            #         Destination={"ToAddresses": [to]},
            #         Message={
            #             "Subject": {"Data": subject},
            #             "Body": {"Text": {"Data": body}},
            #         },
            #     )
            logger.info(f"[SES STUB] Email to {to}: {subject}")
            return True
        except Exception as e:
            logger.error(f"SES email failed: {e}")
            return False

    async def _send_via_sendgrid(self, to: str, subject: str, body: str) -> bool:
        """SendGrid integration stub."""
        logger.info(f"[SENDGRID STUB] Email to {to}: {subject}")
        return True

    # ──────────────── SMS Backend (Stub) ────────────────

    async def send_sms(self, phone: str, message: str) -> bool:
        """
        Send SMS via MSG91 or Twilio.
        Stub — replace with actual API.
        """
        provider = os.getenv("SMS_PROVIDER", "stub")
        logger.info(f"[SMS STUB] To: {phone} | Message: {message[:100]}...")
        return True

    # ──────────────── Helper ────────────────

    async def _load_order_user(self, order_id: UUID) -> tuple:
        """Load order and associated user."""
        result = await self.db.execute(
            select(Order).where(Order.id == order_id)
        )
        order = result.scalar_one_or_none()
        if not order:
            logger.warning(f"Order {order_id} not found for notification")
            return None, None

        result = await self.db.execute(
            select(User).where(User.id == order.user_id)
        )
        user = result.scalar_one_or_none()
        return order, user
