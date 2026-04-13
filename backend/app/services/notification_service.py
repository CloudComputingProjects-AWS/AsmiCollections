"""
Notification Service for order lifecycle emails.
"""

import asyncio
import logging
import os
import re
from html import escape
from pathlib import Path
from uuid import UUID

import boto3
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.models import Invoice, Order, User
from app.utils.email_sender import send_email as smtp_send_email

logger = logging.getLogger(__name__)


class NotificationService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def send_order_confirmation(self, order_id: UUID) -> bool:
        """Send order confirmation email with attached invoice PDF."""
        order, user, invoice = await self._load_order_user_invoice(order_id)
        if not order or not user or not invoice:
            logger.warning("Order confirmation email skipped for order %s", order_id)
            return False

        attachment = await self._build_invoice_attachment(invoice)
        if not attachment:
            logger.warning(
                "Order confirmation email skipped for order %s because invoice attachment could not be loaded",
                order_id,
            )
            return False

        subject = f"Order Confirmed - {order.order_number}"
        customer_name = escape(user.first_name or "Customer")
        order_number = escape(order.order_number)
        invoice_number = escape(invoice.invoice_number)
        total_amount = escape(f"{order.currency} {order.grand_total}")

        html_body = (
            "<html><body style=\"font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; color: #111827;\">"
            "<h2 style=\"margin-bottom: 8px;\">Your order is confirmed</h2>"
            f"<p>Hi {customer_name},</p>"
            "<p>Thank you for shopping with Ashmi Collections. Your payment was successful and your order has been confirmed.</p>"
            "<div style=\"background: #F9FAFB; border: 1px solid #E5E7EB; border-radius: 8px; padding: 16px; margin: 24px 0;\">"
            f"<p style=\"margin: 0 0 8px 0;\"><strong>Order number:</strong> {order_number}</p>"
            f"<p style=\"margin: 0 0 8px 0;\"><strong>Invoice number:</strong> {invoice_number}</p>"
            f"<p style=\"margin: 0;\"><strong>Total paid:</strong> {total_amount}</p>"
            "</div>"
            "<p>Your invoice PDF is attached to this email for your records.</p>"
            "<p>Thank you for shopping with us.</p>"
            "</body></html>"
        )
        text_body = (
            f"Hi {user.first_name or 'Customer'},\n\n"
            f"Your payment was successful and order {order.order_number} is confirmed.\n"
            f"Invoice number: {invoice.invoice_number}\n"
            f"Total paid: {order.currency} {order.grand_total}\n\n"
            "Your invoice PDF is attached to this email.\n\n"
            "Thank you for shopping with us."
        )

        return await self._send_email(
            to=user.email,
            subject=subject,
            body=html_body,
            text_body=text_body,
            attachments=[attachment],
        )

    async def send_shipping_notification(self, order_id: UUID, tracking_url: str | None = None) -> bool:
        """Notify customer that order has been shipped."""
        order, user = await self._load_order_user(order_id)
        if not user:
            return False

        subject = f"Order Shipped - {order.order_number}"
        body = (
            f"Hi {user.first_name or 'Customer'},\n\n"
            f"Your order {order.order_number} has been shipped!\n"
        )
        if tracking_url:
            body += f"Track your order: {tracking_url}\n"
        body += "\nThank you for shopping with us!"

        return await self._send_email(user.email, subject, body, text_body=body)

    async def send_delivery_notification(self, order_id: UUID) -> bool:
        """Notify customer that order has been delivered."""
        order, user = await self._load_order_user(order_id)
        if not user:
            return False

        subject = f"Order Delivered - {order.order_number}"
        body = (
            f"Hi {user.first_name or 'Customer'},\n\n"
            f"Your order {order.order_number} has been delivered!\n\n"
            f"We hope you love your purchase. If you need to return any items, "
            f"you can do so from your order details page within the return window.\n\n"
            f"Thank you!"
        )

        return await self._send_email(user.email, subject, body, text_body=body)

    async def send_return_approved_notification(self, order_id: UUID, pickup_date=None) -> bool:
        """Notify customer that return has been approved."""
        order, user = await self._load_order_user(order_id)
        if not user:
            return False

        subject = f"Return Approved - {order.order_number}"
        body = (
            f"Hi {user.first_name or 'Customer'},\n\n"
            f"Your return request for order {order.order_number} has been approved.\n"
        )
        if pickup_date:
            body += f"Pickup scheduled for: {pickup_date}\n"
        body += "\nPlease keep the items ready for pickup."

        return await self._send_email(user.email, subject, body, text_body=body)

    async def send_return_rejected_notification(self, order_id: UUID, reason: str | None = None) -> bool:
        """Notify customer that return has been rejected."""
        order, user = await self._load_order_user(order_id)
        if not user:
            return False

        subject = f"Return Update - {order.order_number}"
        body = (
            f"Hi {user.first_name or 'Customer'},\n\n"
            f"We were unable to approve the return for order {order.order_number}.\n"
        )
        if reason:
            body += f"Reason: {reason}\n"
        body += "\nPlease contact support if you have questions."

        return await self._send_email(user.email, subject, body, text_body=body)

    async def send_refund_notification(self, order_id: UUID, amount=None) -> bool:
        """Notify customer that refund has been processed."""
        order, user = await self._load_order_user(order_id)
        if not user:
            return False

        subject = f"Refund Processed - {order.order_number}"
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

        return await self._send_email(user.email, subject, body, text_body=body)

    async def send_cancellation_notification(self, order_id: UUID) -> bool:
        """Notify customer that order has been cancelled."""
        order, user = await self._load_order_user(order_id)
        if not user:
            return False

        subject = f"Order Cancelled - {order.order_number}"
        body = (
            f"Hi {user.first_name or 'Customer'},\n\n"
            f"Your order {order.order_number} has been cancelled.\n"
            f"If payment was made, a refund will be processed within 5-7 business days.\n\n"
            f"Thank you!"
        )

        return await self._send_email(user.email, subject, body, text_body=body)

    async def _send_email(
        self,
        to: str,
        subject: str,
        body: str,
        text_body: str | None = None,
        attachments: list[dict] | None = None,
    ) -> bool:
        """Send email through the project's real SMTP sender."""
        return await smtp_send_email(
            to_email=to,
            subject=subject,
            html_body=body,
            text_body=text_body,
            attachments=attachments,
        )

    async def send_sms(self, phone: str, message: str) -> bool:
        """
        Send SMS via MSG91 or Twilio.
        Stub - replace with actual API.
        """
        provider = os.getenv("SMS_PROVIDER", "stub")
        logger.info(f"[SMS STUB] To: {phone} | Message: {message[:100]}...")
        return True

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

    async def _load_order_user_invoice(self, order_id: UUID) -> tuple:
        """Load order, associated user, and generated invoice."""
        order, user = await self._load_order_user(order_id)
        if not order or not user:
            return None, None, None

        result = await self.db.execute(
            select(Invoice).where(Invoice.order_id == order_id)
        )
        invoice = result.scalar_one_or_none()
        return order, user, invoice

    async def _build_invoice_attachment(self, invoice: Invoice) -> dict | None:
        """Build attachment payload from stored invoice PDF."""
        if not invoice.pdf_url:
            return None

        pdf_bytes = await self._load_invoice_bytes(invoice.pdf_url)
        if not pdf_bytes:
            return None

        return {
            "filename": f"{invoice.invoice_number}.pdf",
            "content": pdf_bytes,
            "content_type": "application/pdf",
        }

    async def _load_invoice_bytes(self, pdf_url: str) -> bytes | None:
        """Load invoice bytes from local storage or S3-backed URL."""
        if pdf_url.startswith("http"):
            bucket, key = self._resolve_s3_location(pdf_url)
            if not bucket or not key:
                logger.error("Unsupported invoice URL for attachment: %s", pdf_url)
                return None
            return await self._download_s3_object(bucket, key)

        pdf_path = Path(pdf_url)
        if not pdf_path.exists():
            logger.error("Invoice file missing for attachment: %s", pdf_url)
            return None
        return pdf_path.read_bytes()

    def _resolve_s3_location(self, pdf_url: str) -> tuple[str | None, str | None]:
        """Resolve bucket and key from the invoice URL shapes generated in this app."""
        cloudfront_domain = os.getenv("CLOUDFRONT_DOMAIN", "")
        if cloudfront_domain:
            prefix = f"https://{cloudfront_domain}/"
            if pdf_url.startswith(prefix):
                return os.getenv("S3_BUCKET_NAME", ""), pdf_url[len(prefix):]

        match = re.match(
            r"https://([^/]+)\.s3(?:\.[a-z0-9-]+)?\.amazonaws\.com/(.+)",
            pdf_url,
        )
        if match:
            return match.group(1), match.group(2)

        return None, None

    async def _download_s3_object(self, bucket: str, key: str) -> bytes | None:
        """Download invoice bytes from S3 without blocking the event loop."""
        def _sync_download() -> bytes:
            client = boto3.client("s3", region_name=os.getenv("AWS_REGION", "ap-south-1"))
            response = client.get_object(Bucket=bucket, Key=key)
            return response["Body"].read()

        try:
            return await asyncio.to_thread(_sync_download)
        except Exception as exc:
            logger.error(
                "Failed to download invoice attachment from s3://%s/%s: %s",
                bucket,
                key,
                exc,
            )
            return None
