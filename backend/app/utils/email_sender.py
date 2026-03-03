"""
Email Sender Utility.
Abstraction over SMTP/SES for sending transactional emails.

Phase 1: SMTP-based (works with AWS SES SMTP, SendGrid, or local dev).
Phase 2+: Switch to boto3 SES SDK for production.
"""

import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from app.core.config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)


async def send_email(
    to_email: str,
    subject: str,
    html_body: str,
    text_body: str | None = None,
) -> bool:
    """
    Send a transactional email.
    Returns True on success, False on failure (non-blocking).
    """
    if settings.ENVIRONMENT == "development" and not settings.SMTP_USER:
        # In dev without SMTP config, just log the email
        logger.info(f"[DEV EMAIL] To: {to_email} | Subject: {subject}")
        logger.info(f"[DEV EMAIL] Body preview: {html_body[:200]}...")
        return True

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = settings.FROM_EMAIL
        msg["To"] = to_email

        if text_body:
            msg.attach(MIMEText(text_body, "plain"))
        msg.attach(MIMEText(html_body, "html"))

        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
            server.starttls()
            if settings.SMTP_USER and settings.SMTP_PASSWORD:
                server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            server.sendmail(settings.FROM_EMAIL, to_email, msg.as_string())

        logger.info(f"Email sent to {to_email}: {subject}")
        return True
    except Exception as e:
        logger.error(f"Failed to send email to {to_email}: {e}")
        return False


async def send_otp_email(to_email: str, otp: str) -> bool:
    """Send 6-digit OTP verification email."""
    subject = "Your Verification Code - Ashmi Collections"
    html_body = f"""
    <html>
    <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
        <h2 style="color: #333;">Verify Your Email Address</h2>
        <p>Thank you for registering with Ashmi Collections! Use the code below to verify your email:</p>
        <div style="text-align: center; margin: 30px 0;">
            <div style="display: inline-block; background-color: #F3F4F6; border: 2px solid #D1D5DB;
                        border-radius: 8px; padding: 20px 40px; font-size: 32px; font-weight: bold;
                        letter-spacing: 8px; color: #111827;">
                {otp}
            </div>
        </div>
        <p style="color: #666; font-size: 14px;">
            This code expires in <strong>10 minutes</strong>.
        </p>
        <p style="color: #999; font-size: 12px;">
            If you didn't create an account, please ignore this email.
        </p>
    </body>
    </html>
    """
    text_body = f"Your Ashmi Collections verification code is: {otp}. This code expires in 10 minutes."
    return await send_email(to_email, subject, html_body, text_body)


async def send_verification_email(to_email: str, token: str, base_url: str = "http://localhost:3000") -> bool:
    """Send email verification link (legacy - kept for backward compatibility)."""
    verify_url = f"{base_url}/verify-email?token={token}"
    subject = "Verify Your Email - Ashmi Collections"
    html_body = f"""
    <html>
    <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
        <h2>Verify Your Email Address</h2>
        <p>Thank you for registering! Please click the button below to verify your email:</p>
        <p style="text-align: center; margin: 30px 0;">
            <a href="{verify_url}"
               style="background-color: #4F46E5; color: white; padding: 12px 30px;
                      text-decoration: none; border-radius: 6px; font-weight: bold;">
                Verify Email
            </a>
        </p>
        <p style="color: #666; font-size: 14px;">
            Or copy this link: {verify_url}
        </p>
        <p style="color: #999; font-size: 12px;">
            This link expires in 24 hours. If you didn't create an account, ignore this email.
        </p>
    </body>
    </html>
    """
    return await send_email(to_email, subject, html_body)


async def send_password_reset_email(to_email: str, token: str, base_url: str = "http://localhost:3000") -> bool:
    """Send password reset link."""
    reset_url = f"{base_url}/reset-password?token={token}"
    subject = "Reset Your Password - Ashmi Collections"
    html_body = f"""
    <html>
    <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
        <h2>Reset Your Password</h2>
        <p>We received a request to reset your password. Click below to set a new password:</p>
        <p style="text-align: center; margin: 30px 0;">
            <a href="{reset_url}"
               style="background-color: #DC2626; color: white; padding: 12px 30px;
                      text-decoration: none; border-radius: 6px; font-weight: bold;">
                Reset Password
            </a>
        </p>
        <p style="color: #666; font-size: 14px;">
            Or copy this link: {reset_url}
        </p>
        <p style="color: #999; font-size: 12px;">
            This link expires in 30 minutes. If you didn't request this, ignore this email.
        </p>
    </body>
    </html>
    """
    return await send_email(to_email, subject, html_body)
