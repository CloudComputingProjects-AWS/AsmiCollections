"""
Authentication service — handles registration, login, token management.
Business logic layer (Controller → Service → Repository pattern).
"""

from datetime import datetime, timezone
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
from app.models.models import RefreshToken, User, UserConsent
from app.schemas.auth import UserRegisterRequest

settings = get_settings()
ADMIN_2FA_ROLES = {"admin", "product_manager", "order_manager", "finance_manager"}


class AuthServiceError(Exception):
    def __init__(self, message: str, status_code: int = 400):
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class AuthService:
    def __init__(self, db: AsyncSession):
        self.db = db

    @staticmethod
    def _normalize_phone(phone: str | None, country_code: str | None) -> str | None:
        if not phone:
            return None

        phone_digits = phone.strip()
        if not phone_digits:
            return None

        cc = (country_code or "+91").strip()
        if phone_digits.startswith("+"):
            return phone_digits
        return f"{cc}{phone_digits}"

    async def _customer_phone_exists(self, normalized_phone: str) -> bool:
        # Equality queries won't work once phone is encrypted with random nonces.
        result = await self.db.execute(
            select(User.phone).where(
                User.role == "customer",
                User.deleted_at.is_(None),
                User.phone.is_not(None),
            )
        )
        return any(phone == normalized_phone for phone in result.scalars().all())

    async def register(
        self, data: UserRegisterRequest, ip_address: str, user_agent: str
    ) -> User:
        """Register a new user with consent tracking."""
        if not data.terms_accepted or not data.privacy_accepted:
            raise AuthServiceError("Terms of Service and Privacy Policy must be accepted")

        normalized_phone = self._normalize_phone(data.phone, data.country_code)

        existing_email = await self.db.execute(
            select(User).where(User.email == data.email.lower())
        )
        email_taken = existing_email.scalar_one_or_none() is not None

        phone_taken = False
        if normalized_phone:
            phone_taken = await self._customer_phone_exists(normalized_phone)

        if email_taken and phone_taken:
            raise AuthServiceError("Email and Phone number already registered", 409)
        if email_taken:
            raise AuthServiceError("Email already registered", 409)
        if phone_taken:
            raise AuthServiceError("Phone number already registered", 409)

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
        await self.db.flush()

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

        return user

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

        requires_admin_totp = (
            user.role in ADMIN_2FA_ROLES
            and getattr(user, "totp_enabled", False)
            and user.totp_secret is not None
        )

        if requires_admin_totp:
            return user, None, None

        access_token = create_access_token(str(user.id), user.role)
        refresh_token_str, family_id, expires_at = create_refresh_token(str(user.id))

        rt = RefreshToken(
            user_id=user.id,
            token_hash=hash_token(refresh_token_str),
            family_id=family_id,
            expires_at=expires_at,
        )
        self.db.add(rt)

        return user, access_token, refresh_token_str

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

        result = await self.db.execute(
            select(RefreshToken).where(
                RefreshToken.token_hash == token_hash,
                RefreshToken.user_id == user_id,
            )
        )
        stored = result.scalar_one_or_none()

        if not stored:
            await self._revoke_token_family(family_id)
            raise AuthServiceError("Refresh token reuse detected. All sessions revoked.", 401)

        if stored.revoked_at is not None:
            await self._revoke_token_family(family_id)
            raise AuthServiceError("Refresh token reuse detected. All sessions revoked.", 401)

        if stored.expires_at < datetime.now(timezone.utc):
            raise AuthServiceError("Refresh token expired", 401)

        stored.revoked_at = datetime.now(timezone.utc)

        user_result = await self.db.execute(
            select(User).where(User.id == user_id, User.is_active.is_(True))
        )
        user = user_result.scalar_one_or_none()
        if not user:
            raise AuthServiceError("User not found", 401)

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
