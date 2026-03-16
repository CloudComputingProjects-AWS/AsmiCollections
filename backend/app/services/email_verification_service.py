"""
Email Verification Service.
Handles sending OTP verification codes and verifying them.

Flow:
  1. On registration -> generate 6-digit OTP -> store hash in email_verifications -> send OTP email
  2. User enters OTP on verify-otp page -> POST /verify-email with email+OTP -> mark email_verified = True
"""

import random
import secrets
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_token
from app.models.models import EmailVerification, User


class EmailVerificationError(Exception):
    def __init__(self, message: str, status_code: int = 400):
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class EmailVerificationService:

    OTP_EXPIRY_MINUTES = 10
    OTP_LENGTH = 6

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_verification(self, user_id) -> str:
        """
        Create a 6-digit OTP for a user.
        Returns the raw OTP (to be sent via email).
        """
        # Invalidate any existing unused tokens/OTPs
        result = await self.db.execute(
            select(EmailVerification).where(
                EmailVerification.user_id == user_id,
                EmailVerification.verified_at.is_(None),
            )
        )
        for old_token in result.scalars().all():
            old_token.expires_at = datetime.now(timezone.utc)  # expire immediately

        # Generate 6-digit OTP (zero-padded)
        raw_otp = str(random.randint(0, 999999)).zfill(self.OTP_LENGTH)
        otp_hash = hash_token(raw_otp)
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=self.OTP_EXPIRY_MINUTES)

        verification = EmailVerification(
            user_id=user_id,
            token_hash=otp_hash,
            expires_at=expires_at,
        )
        self.db.add(verification)
        return raw_otp

    async def verify_email(self, email: str, otp: str) -> User:
        """
        Verify a user's email using the OTP.
        Looks up user by email, then checks OTP hash match.
        Returns the verified user.
        """
        # Find user by email
        user_result = await self.db.execute(
            select(User).where(User.email == email)
        )
        user = user_result.scalar_one_or_none()
        if not user:
            raise EmailVerificationError(
                "No account found with this email.", status_code=404
            )

        if user.email_verified:
            raise EmailVerificationError(
                "Email is already verified.", status_code=400
            )

        otp_hash = hash_token(otp)
        now = datetime.now(timezone.utc)

        result = await self.db.execute(
            select(EmailVerification).where(
                EmailVerification.user_id == user.id,
                EmailVerification.token_hash == otp_hash,
                EmailVerification.verified_at.is_(None),
                EmailVerification.expires_at > now,
            )
        )
        verification = result.scalar_one_or_none()

        if not verification:
            raise EmailVerificationError(
                "Invalid or expired OTP. Please request a new one.", status_code=400
            )

        # Mark OTP as used
        verification.verified_at = now

        # Mark user email as verified
        user.email_verified = True
        return user

    async def resend_verification(self, user_id) -> str:
        """
        Resend OTP. Returns new raw OTP.
        Checks if already verified.
        """
        user_result = await self.db.execute(
            select(User).where(User.id == user_id)
        )
        user = user_result.scalar_one_or_none()
        if not user:
            raise EmailVerificationError("User not found.", status_code=404)
        if user.email_verified:
            raise EmailVerificationError("Email already verified.", status_code=400)

        return await self.create_verification(user_id)

    async def verify_email_by_token(self, token: str) -> User:
        """
        Verify email using legacy token link (backward compatibility).
        Raises EmailVerificationError on invalid/expired token.
        Returns the verified user.
        """
        from app.models.models import EmailVerification
        token_hash = hash_token(token)
        now = datetime.now(timezone.utc)

        result = await self.db.execute(
            select(EmailVerification).where(
                EmailVerification.token_hash == token_hash,
                EmailVerification.verified_at.is_(None),
                EmailVerification.expires_at > now,
            )
        )
        verification = result.scalar_one_or_none()
        if not verification:
            raise EmailVerificationError(
                "Invalid or expired verification token.", status_code=400
            )

        verification.verified_at = now

        user_result = await self.db.execute(
            select(User).where(User.id == verification.user_id)
        )
        user = user_result.scalar_one_or_none()
        if not user:
            raise EmailVerificationError("User not found.", status_code=404)

        user.email_verified = True
        return user

    async def resend_verification_by_email(self, email: str) -> tuple[str, "User"]:
        """
        Resend OTP by email address (no auth required).
        Returns (raw_otp, user).
        """
        user_result = await self.db.execute(
            select(User).where(User.email == email)
        )
        user = user_result.scalar_one_or_none()
        if not user:
            raise EmailVerificationError("No account found with this email.", status_code=404)
        if user.email_verified:
            raise EmailVerificationError("Email is already verified.", status_code=400)

        otp = await self.create_verification(user.id)
        return otp, user
