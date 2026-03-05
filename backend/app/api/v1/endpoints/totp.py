"""
2FA API Endpoints — Admin TOTP two-factor authentication.

Routes:
  POST /api/v1/auth/2fa/setup          — Generate TOTP secret + QR URI
  POST /api/v1/auth/2fa/verify-setup   — Confirm setup with TOTP code
  POST /api/v1/auth/2fa/validate       — Validate TOTP during login (step 2)
  POST /api/v1/auth/2fa/disable        — Disable 2FA
  GET  /api/v1/auth/2fa/status         — Check 2FA status

SECURITY (Updated 05-Mar-2026 S20):
  - /2fa/validate sets tokens as httpOnly cookies (not JSON body)
  - SameSite policy is environment-aware — identical logic to auth.py:
      development  -> SameSite=Strict,  Secure=False  (local machine)
      aws_dev      -> SameSite=None,    Secure=True   (cross-origin S3 + API GW)
      production   -> SameSite=Strict,  Secure=True   (CloudFront same-domain)
"""

import io
import base64
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.database import get_db
from app.core.security import create_access_token, create_refresh_token, hash_token
from app.middleware.auth import get_current_user
from app.models.models import RefreshToken, User
from app.services.totp_service import TwoFactorError, TwoFactorService

router = APIRouter(prefix="/auth/2fa", tags=["Two-Factor Authentication"])
settings = get_settings()


# ────────────────────────────────────────────────────────────────
# SCHEMAS
# ────────────────────────────────────────────────────────────────

class TOTPCodeRequest(BaseModel):
    totp_code: str = Field(..., min_length=6, max_length=6, pattern=r"^\d{6}$")


class TOTPLoginRequest(BaseModel):
    """Step 2 of 2FA login: user_id from partial token + TOTP code."""
    user_id: UUID
    totp_code: str = Field(..., min_length=6, max_length=6, pattern=r"^\d{6}$")


class TOTPSetupResponse(BaseModel):
    secret: str
    provisioning_uri: str
    qr_code_base64: str | None = None
    message: str


class TOTPStatusResponse(BaseModel):
    totp_enabled: bool
    is_admin: bool
    requires_2fa: bool


class MessageResponse(BaseModel):
    message: str


# ────────────────────────────────────────────────────────────────
# COOKIE HELPER — mirrors auth.py exactly, keep in sync
# ────────────────────────────────────────────────────────────────

def _get_cookie_security_params() -> tuple[str, bool]:
    """
    Return (samesite, secure) based on ENVIRONMENT setting.

    development  -> ("strict", False)  — local machine, same-origin HTTP
    aws_dev      -> ("none",   True)   — cross-origin: S3 + API Gateway
    production   -> ("strict", True)   — CloudFront same-domain, HTTPS
    """
    env = settings.ENVIRONMENT.lower()
    if env == "development":
        return "strict", False
    elif env == "aws_dev":
        return "none", True
    else:
        return "strict", True


# ────────────────────────────────────────────────────────────────
# ENDPOINTS
# ────────────────────────────────────────────────────────────────

@router.post("/setup", response_model=TOTPSetupResponse)
async def setup_2fa(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Generate TOTP secret and provisioning URI.
    Admin scans the QR with Google Authenticator / Authy."""
    service = TwoFactorService(db)
    try:
        result = await service.setup_2fa(user.id)
        await db.commit()
        qr_b64 = _generate_qr_base64(result["provisioning_uri"])
        return TOTPSetupResponse(
            secret=result["secret"],
            provisioning_uri=result["provisioning_uri"],
            qr_code_base64=qr_b64,
            message=result["message"],
        )
    except TwoFactorError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


@router.post("/verify-setup", response_model=MessageResponse)
async def verify_setup(
    data: TOTPCodeRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Confirm 2FA setup by verifying a TOTP code from the authenticator app.
    After this, 2FA is enforced on all future logins."""
    service = TwoFactorService(db)
    try:
        result = await service.verify_setup(user.id, data.totp_code)
        await db.commit()
        return MessageResponse(message=result["message"])
    except TwoFactorError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


@router.post("/validate")
async def validate_totp_login(
    data: TOTPLoginRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Step 2 of admin login: validate TOTP code and issue full tokens.

    Flow:
      1. Normal /auth/login returns {"requires_2fa": True, "user_id": "..."}
      2. Frontend calls this endpoint with user_id + TOTP code
      3. On success: sets access_token + refresh_token as httpOnly cookies

    SECURITY (S20): Tokens set as httpOnly cookies, NOT returned in JSON body.
    SameSite policy is environment-aware — matches _get_cookie_security_params in auth.py.
    """
    service = TwoFactorService(db)
    try:
        await service.validate_totp(data.user_id, data.totp_code)

        from sqlalchemy import select
        result = await db.execute(
            select(User).where(User.id == data.user_id)
        )
        user = result.scalar_one_or_none()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        access_token = create_access_token(str(user.id), user.role)
        refresh_token_str, family_id, expires_at = create_refresh_token(str(user.id))

        rt = RefreshToken(
            user_id=user.id,
            token_hash=hash_token(refresh_token_str),
            family_id=family_id,
            expires_at=expires_at,
        )
        db.add(rt)
        await db.commit()

        samesite, secure = _get_cookie_security_params()

        totp_response = JSONResponse(
            status_code=200,
            content={
                "token_type": "bearer",
                "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            },
        )
        totp_response.set_cookie(
            key="access_token",
            value=access_token,
            httponly=True,
            secure=secure,
            samesite=samesite,
            max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            path="/",
        )
        totp_response.set_cookie(
            key="refresh_token",
            value=refresh_token_str,
            httponly=True,
            secure=secure,
            samesite=samesite,
            max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
            path="/api/v1/auth",
        )
        return totp_response
    except TwoFactorError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


@router.post("/disable", response_model=MessageResponse)
async def disable_2fa(
    data: TOTPCodeRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Disable 2FA. Requires current TOTP code for confirmation."""
    service = TwoFactorService(db)
    try:
        result = await service.disable_2fa(user.id, data.totp_code)
        await db.commit()
        return MessageResponse(message=result["message"])
    except TwoFactorError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


@router.get("/status", response_model=TOTPStatusResponse)
async def get_2fa_status(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Check if 2FA is enabled for the current user."""
    service = TwoFactorService(db)
    result = await service.get_2fa_status(user.id)
    return TOTPStatusResponse(**result)


# ────────────────────────────────────────────────────────────────
# QR CODE HELPER
# ────────────────────────────────────────────────────────────────

def _generate_qr_base64(uri: str) -> str | None:
    """Generate QR code as base64 PNG string."""
    try:
        import qrcode
        qr = qrcode.QRCode(version=1, box_size=10, border=4)
        qr.add_data(uri)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        buffer.seek(0)
        return base64.b64encode(buffer.getvalue()).decode("ascii")
    except ImportError:
        return None
