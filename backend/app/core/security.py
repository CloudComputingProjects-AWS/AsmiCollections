"""
Security utilities: password hashing, JWT creation/verification.
"""

import uuid
from datetime import datetime, timedelta, timezone
import hashlib
from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import get_settings

settings = get_settings()

# ──────────────── Password Hashing ────────────────
pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__rounds=settings.BCRYPT_ROUNDS,
)


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


# ──────────────── JWT Tokens ────────────────
def create_access_token(
    user_id: str,
    role: str,
    expires_delta: timedelta | None = None,
) -> str:
    now = datetime.now(timezone.utc)
    expire = now + (
        expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    payload = {
        "sub": user_id,
        "role": role,
        "type": "access",
        "exp": expire,
        "iat": now,
        "jti": str(uuid.uuid4()),
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def create_refresh_token(
    user_id: str,
    family_id: str | None = None,
) -> tuple[str, str, datetime]:
    """Returns (token_string, family_id, expires_at)."""
    family = family_id or str(uuid.uuid4())
    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(
        days=settings.REFRESH_TOKEN_EXPIRE_DAYS
    )
    payload = {
        "sub": user_id,
        "type": "refresh",
        "family": family,
        "exp": expires_at,
        "iat": now,
        "jti": str(uuid.uuid4()),
    }
    token = jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return token, family, expires_at


def decode_token(token: str) -> dict | None:
    """Decode and verify a JWT token. Returns payload or None."""
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )
        return payload
    except JWTError:
        return None


def hash_token(token: str) -> str:
    """SHA-256 hash for storing refresh tokens securely."""
    return hashlib.sha256(token.encode()).hexdigest()
