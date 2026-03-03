"""
Password Reset Service.
Handles forgot-password and reset-password flows.

Flow:
  1. User submits email → generate reset token → store hash → send email
  2. User clicks link with token → submit new password → verify token → update hash
  3. On password change → revoke all refresh tokens (security)
"""

import secrets
from datetime import datetime, timedelta, timezone

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password, hash_token
from app.models.models import RefreshToken, User


class PasswordResetError(Exception):
    def __init__(self, message: str, status_code: int = 400):
        self.message = message
        self.status_code = status_code
        super().__init__(message)


# We reuse email_verifications table with a different approach:
# Store reset tokens in a dedicated table for clarity.
# For Phase 1, we use a simple in-memory structure and DB approach.

from app.models.models import EmailVerification  # reuse table structure


class PasswordResetService:

    TOKEN_EXPIRY_MINUTES = 30

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_reset_token(self, email: str) -> tuple[str | None, str | None]:
        """
        Create a password reset token for the given email.
        Returns (raw_token, user_email) or (None, None) if user not found.
        We always return success to the caller to prevent email enumeration.
        """
        result = await self.db.execute(
            select(User).where(
                User.email == email.lower().strip(),
                User.is_active == True,
                User.deleted_at.is_(None),
            )
        )
        user = result.scalar_one_or_none()

        if not user:
            return None, None  # Don't reveal user doesn't exist

        # Generate token
        raw_token = secrets.token_urlsafe(32)
        token_hash_value = hash_token(raw_token)
        expires_at = datetime.now(timezone.utc) + timedelta(
            minutes=self.TOKEN_EXPIRY_MINUTES
        )

        # Store as email verification entry (reusing table)
        # In production, you may want a dedicated password_resets table
        verification = EmailVerification(
            user_id=user.id,
            token_hash=token_hash_value,
            expires_at=expires_at,
        )
        self.db.add(verification)
        return raw_token, user.email

    async def reset_password(self, token: str, new_password: str) -> None:
        """
        Verify reset token and update user's password.
        Also revokes all refresh tokens for security.
        """
        token_hash_value = hash_token(token)
        now = datetime.now(timezone.utc)

        # Find valid token
        result = await self.db.execute(
            select(EmailVerification).where(
                EmailVerification.token_hash == token_hash_value,
                EmailVerification.verified_at.is_(None),
                EmailVerification.expires_at > now,
            )
        )
        verification = result.scalar_one_or_none()

        if not verification:
            raise PasswordResetError(
                "Invalid or expired reset token.", status_code=400
            )

        # Mark token as used
        verification.verified_at = now

        # Update password
        user_result = await self.db.execute(
            select(User).where(User.id == verification.user_id)
        )
        user = user_result.scalar_one_or_none()
        if not user:
            raise PasswordResetError("User not found.", status_code=404)

        user.password_hash = hash_password(new_password)
        user.updated_at = now

        # Revoke all refresh tokens (security: password changed)
        token_result = await self.db.execute(
            select(RefreshToken).where(
                RefreshToken.user_id == user.id,
                RefreshToken.revoked_at.is_(None),
            )
        )
        for rt in token_result.scalars().all():
            rt.revoked_at = now
