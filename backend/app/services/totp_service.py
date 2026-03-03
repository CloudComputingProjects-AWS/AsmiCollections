"""
Admin 2FA Service â€” TOTP-based two-factor authentication.

Blueprint ref: Phase 2 â€” "Admin login with 2FA (TOTP)"

Flow:
  1. Admin calls POST /api/v1/auth/2fa/setup â†’ gets secret + QR provisioning URI
  2. Admin scans QR with Google Authenticator / Authy
  3. Admin calls POST /api/v1/auth/2fa/verify-setup with TOTP code â†’ 2FA enabled
  4. On next login: if totp_enabled=True, login returns partial token
  5. Admin calls POST /api/v1/auth/2fa/validate with TOTP code â†’ full tokens issued
  6. Admin can disable 2FA via POST /api/v1/auth/2fa/disable

Requires: pip install pyotp qrcode[pil]
"""

import logging
from uuid import UUID

import pyotp
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.models.models import User

logger = logging.getLogger(__name__)
settings = get_settings()

# Admin roles that require 2FA
ADMIN_ROLES = {"admin", "product_manager", "order_manager", "finance_manager"}


class TwoFactorError(Exception):
    def __init__(self, message: str, status_code: int = 400):
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class TwoFactorService:
    """TOTP-based two-factor authentication for admin accounts."""

    def __init__(self, db: AsyncSession):
        self.db = db

    def is_admin_role(self, role: str) -> bool:
        """Check if the role requires 2FA."""
        return role in ADMIN_ROLES

    async def setup_2fa(self, user_id: UUID) -> dict:
        """
        Generate a new TOTP secret for the user.
        Returns secret + provisioning URI for QR code generation.
        Does NOT enable 2FA until verify_setup is called.
        """
        user = await self._get_user(user_id)

        if not self.is_admin_role(user.role):
            raise TwoFactorError("2FA is only available for admin accounts")

        if getattr(user, "totp_enabled", False):
            raise TwoFactorError(
                "2FA is already enabled. Disable it first to re-setup."
            )

        # Generate a new secret
        secret = pyotp.random_base32()

        # Store secret (not yet enabled)
        user.totp_secret = secret
        user.totp_enabled = False
        await self.db.flush()

        # Generate provisioning URI for QR code
        totp = pyotp.TOTP(secret)
        provisioning_uri = totp.provisioning_uri(
            name=user.email,
            issuer_name=settings.APP_NAME,
        )

        logger.info("2FA setup initiated for user %s", user_id)

        return {
            "secret": secret,
            "provisioning_uri": provisioning_uri,
            "message": "Scan the QR code with your authenticator app, "
                       "then call verify-setup with a valid TOTP code.",
        }

    async def verify_setup(self, user_id: UUID, totp_code: str) -> dict:
        """
        Verify the TOTP code after setup to enable 2FA.
        This confirms the user has correctly configured their authenticator.
        """
        user = await self._get_user(user_id)

        if not user.totp_secret:
            raise TwoFactorError("No 2FA setup found. Call setup first.")

        if getattr(user, "totp_enabled", False):
            raise TwoFactorError("2FA is already enabled.")

        totp = pyotp.TOTP(user.totp_secret)

        # Allow 1 window of clock skew (30 seconds)
        if not totp.verify(totp_code, valid_window=1):
            raise TwoFactorError("Invalid TOTP code. Please try again.")

        user.totp_enabled = True
        await self.db.flush()

        logger.info("2FA enabled for user %s", user_id)

        return {
            "totp_enabled": True,
            "message": "Two-factor authentication is now enabled.",
        }

    async def validate_totp(self, user_id: UUID, totp_code: str) -> bool:
        """
        Validate a TOTP code during login.
        Returns True if valid, raises error if invalid.
        """
        user = await self._get_user(user_id)

        if not getattr(user, "totp_enabled", False) or not user.totp_secret:
            raise TwoFactorError("2FA is not enabled for this account")

        totp = pyotp.TOTP(user.totp_secret)

        if not totp.verify(totp_code, valid_window=1):
            raise TwoFactorError("Invalid TOTP code", status_code=401)

        logger.info("2FA validated for user %s", user_id)
        return True

    async def disable_2fa(self, user_id: UUID, totp_code: str) -> dict:
        """
        Disable 2FA for a user. Requires current TOTP code for confirmation.
        """
        user = await self._get_user(user_id)

        if not getattr(user, "totp_enabled", False):
            raise TwoFactorError("2FA is not currently enabled")

        totp = pyotp.TOTP(user.totp_secret)
        if not totp.verify(totp_code, valid_window=1):
            raise TwoFactorError("Invalid TOTP code. Cannot disable 2FA.")

        user.totp_secret = None
        user.totp_enabled = False
        await self.db.flush()

        logger.info("2FA disabled for user %s", user_id)

        return {
            "totp_enabled": False,
            "message": "Two-factor authentication has been disabled.",
        }

    async def get_2fa_status(self, user_id: UUID) -> dict:
        """Check if 2FA is enabled for a user."""
        user = await self._get_user(user_id)
        return {
            "totp_enabled": getattr(user, "totp_enabled", False),
            "is_admin": self.is_admin_role(user.role),
            "requires_2fa": self.is_admin_role(user.role),
        }

    async def is_2fa_required(self, user: User) -> bool:
        """Check if login requires 2FA step."""
        return (
            self.is_admin_role(user.role)
            and getattr(user, "totp_enabled", False)
            and user.totp_secret is not None
        )

    async def _get_user(self, user_id: UUID) -> User:
        result = await self.db.execute(
            select(User).where(User.id == user_id)
        )
        user = result.scalar_one_or_none()
        if not user:
            raise TwoFactorError("User not found", status_code=404)
        return user
