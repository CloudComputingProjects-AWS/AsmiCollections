"""
Authentication service — handles registration, login, token management.
Business logic layer (Controller → Service → Repository pattern).
"""

from datetime import datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.security import (
    create_access_token,
    create_refresh_token,
    hash_password,
    hash_token,
    verify_password,
)
from app.models.models import EmailVerification, RefreshToken, User, UserConsent
from app.schemas.auth import UserRegisterRequest

settings = get_settings()


class AuthServiceError(Exception):
    def __init__(self, message: str, status_code: int = 400):
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class AuthService:

    def __init__(self, db: AsyncSession):
        self.db = db

    # ──────────────── Registration ────────────────

    async def register(
        self, data: UserRegisterRequest, ip_address: str, user_agent: str
    ) -> User:
        """Register a new user with consent tracking."""
        # Validate required consents
        if not data.terms_accepted or not data.privacy_accepted:
            raise AuthServiceError("Terms of Service and Privacy Policy must be accepted")

        # Normalize phone: concatenate country_code + phone digits
        normalized_phone = None
        if data.phone:
            phone_digits = data.phone.strip()
            if phone_digits:
                country_code = (data.country_code or "+91").strip()
                # Remove any leading + from phone digits if user accidentally included it
                if phone_digits.startswith("+"):
                    normalized_phone = phone_digits
                else:
                    normalized_phone = country_code + phone_digits

        # Check duplicate email
        existing_email = await self.db.execute(
            select(User).where(User.email == data.email.lower())
        )
        email_taken = existing_email.scalar_one_or_none() is not None

        # Check duplicate phone (customer accounts only, skip if phone not provided)
        phone_taken = False
        if normalized_phone:
            existing_phone = await self.db.execute(
                select(User).where(
                    User.phone == normalized_phone,
                    User.role == "customer",
                    User.deleted_at.is_(None),
                )
            )
            phone_taken = existing_phone.scalar_one_or_none() is not None

        # Raise combined error if any duplicates found
        if email_taken and phone_taken:
            raise AuthServiceError("Email and Phone number already registered", 409)
        if email_taken:
            raise AuthServiceError("Email already registered", 409)
        if phone_taken:
            raise AuthServiceError("Phone number already registered", 409)

        # Create user (email_verified defaults to False -- OTP verification required)
        user = User(
            email=data.email.lower(),
            password_hash=hash_password(data.password),
            first_name=data.first_name,
            last_name=data.last_name,
            phone=normalized_phone,
            country_code=(data.country_code or "+91").strip(),
            role="customer",
        )
        self.db.add(user)
        await self.db.flush()  # get user.id

        # Record consents (V2.5 — DPDP/GDPR compliance)
        consents = [
            UserConsent(
                user_id=user.id,
                consent_type="terms_of_service",
                granted=True,
                granted_at=datetime.now(timezone.utc),
                ip_address=ip_address,
                user_agent=user_agent,
                version="1.0",
            ),
            UserConsent(
                user_id=user.id,
                consent_type="privacy_policy",
                granted=True,
                granted_at=datetime.now(timezone.utc),
                ip_address=ip_address,
                user_agent=user_agent,
                version="1.0",
            ),
            UserConsent(
                user_id=user.id,
                consent_type="marketing_email",
                granted=data.marketing_email,
                granted_at=datetime.now(timezone.utc) if data.marketing_email else None,
                ip_address=ip_address,
                user_agent=user_agent,
            ),
            UserConsent(
                user_id=user.id,
                consent_type="marketing_sms",
                granted=data.marketing_sms,
                granted_at=datetime.now(timezone.utc) if data.marketing_sms else None,
                ip_address=ip_address,
                user_agent=user_agent,
            ),
        ]
        self.db.add_all(consents)

        # OTP verification email is sent by the endpoint layer (auth.py)
        # email_verified remains False until OTP is verified

        return user

    # ──────────────── Login (with 2FA support) ────────────────

    async def login(self, email: str, password: str) -> tuple[User, str | None, str | None]:
        """
        Authenticate user. Returns (user, access_token, refresh_token).
        If 2FA is enabled: returns (user, None, None) — caller must handle 2FA step.
        Raises AuthServiceError on failure.
        """
        result = await self.db.execute(
            select(User).where(
                User.email == email.lower(),
                User.is_active.is_(True),
                User.deleted_at.is_(None),
            )
        )
        user = result.scalar_one_or_none()

        if not user or not verify_password(password, user.password_hash):
            raise AuthServiceError("Invalid email or password", 401)

        # Check if 2FA is required (admin with TOTP enabled)
        if getattr(user, "totp_enabled", False) and user.totp_secret:
            # Password verified, but 2FA needed — return no tokens
            return user, None, None

        # No 2FA — issue tokens directly
        access_token = create_access_token(str(user.id), user.role)
        refresh_token_str, family_id, expires_at = create_refresh_token(str(user.id))

        # Store refresh token hash
        rt = RefreshToken(
            user_id=user.id,
            token_hash=hash_token(refresh_token_str),
            family_id=family_id,
            expires_at=expires_at,
        )
        self.db.add(rt)

        return user, access_token, refresh_token_str

    # ──────────────── Token Rotation ────────────────

    async def rotate_refresh_token(self, old_token: str) -> tuple[str, str]:
        """
        Rotate refresh token (issue new pair, revoke old).
        Implements family-based theft detection.
        Returns (new_access_token, new_refresh_token).
        """
        from app.core.security import decode_token

        payload = decode_token(old_token)
        if not payload or payload.get("type") != "refresh":
            raise AuthServiceError("Invalid refresh token", 401)

        user_id = payload["sub"]
        family_id = payload["family"]
        token_hash = hash_token(old_token)

        # Find stored token
        result = await self.db.execute(
            select(RefreshToken).where(
                RefreshToken.token_hash == token_hash,
                RefreshToken.user_id == user_id,
            )
        )
        stored = result.scalar_one_or_none()

        if not stored:
            # Token not found — possible theft. Revoke entire family.
            await self._revoke_token_family(family_id)
            raise AuthServiceError("Refresh token reuse detected. All sessions revoked.", 401)

        if stored.revoked_at is not None:
            # Already revoked — theft detected. Revoke entire family.
            await self._revoke_token_family(family_id)
            raise AuthServiceError("Refresh token reuse detected. All sessions revoked.", 401)

        if stored.expires_at < datetime.now(timezone.utc):
            raise AuthServiceError("Refresh token expired", 401)

        # Revoke old token
        stored.revoked_at = datetime.now(timezone.utc)

        # Get user for role info
        user_result = await self.db.execute(
            select(User).where(User.id == user_id, User.is_active.is_(True))
        )
        user = user_result.scalar_one_or_none()
        if not user:
            raise AuthServiceError("User not found", 401)

        # Issue new pair (same family)
        new_access = create_access_token(str(user.id), user.role)
        new_refresh_str, _, new_expires = create_refresh_token(str(user.id), family_id)

        new_rt = RefreshToken(
            user_id=user.id,
            token_hash=hash_token(new_refresh_str),
            family_id=family_id,
            expires_at=new_expires,
        )
        self.db.add(new_rt)

        return new_access, new_refresh_str

    # ──────────────── Logout ────────────────

    async def logout(self, user_id: UUID) -> None:
        """Revoke all refresh tokens for user."""
        result = await self.db.execute(
            select(RefreshToken).where(
                RefreshToken.user_id == user_id,
                RefreshToken.revoked_at.is_(None),
            )
        )
        tokens = result.scalars().all()
        now = datetime.now(timezone.utc)
        for token in tokens:
            token.revoked_at = now

    # ──────────────── Internal ────────────────

    async def _revoke_token_family(self, family_id: str) -> None:
        """Revoke all tokens in a family (theft detection)."""
        result = await self.db.execute(
            select(RefreshToken).where(
                RefreshToken.family_id == family_id,
                RefreshToken.revoked_at.is_(None),
            )
        )
        tokens = result.scalars().all()
        now = datetime.now(timezone.utc)
        for token in tokens:
            token.revoked_at = now
