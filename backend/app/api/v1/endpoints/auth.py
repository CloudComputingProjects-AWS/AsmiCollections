"""
Auth API endpoints -- /api/v1/auth/
Includes: register, login (with 2FA support), refresh, logout, me,
          email verification (OTP), forgot password, reset password.

SECURITY (Updated 05-Mar-2026 S20):
  - access_token: httpOnly cookie, path="/", SameSite=environment-aware
  - refresh_token: httpOnly cookie, path="/api/v1/auth", SameSite=environment-aware
  - NEITHER token is returned in JSON response body
  - refresh_token cookie path is restricted so it is only sent on auth endpoints

SameSite policy by ENVIRONMENT value:
  development  â€” SameSite=Strict,  Secure=False  (local machine, same-origin HTTP)
  aws_dev      â€” SameSite=None,    Secure=True   (cross-origin: S3 + API Gateway)
  production   â€” SameSite=Strict,  Secure=True   (same-origin via CloudFront)
"""

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.security import decode_token
from sqlalchemy import select
from app.core.config import get_settings
from app.core.database import get_db
from app.middleware.auth import get_current_user
from app.models.models import User
from app.core.security import hash_token
from app.models.models import EmailVerification
from datetime import datetime, timezone
from app.schemas.auth import (
    EmailVerifyRequest,
    ForgotPasswordRequest,
    MessageResponse,
    OTPVerifyRequest,
    ResendOTPRequest,
    ResetPasswordRequest,
    TokenResponse,
    UserLoginRequest,
    UserRegisterRequest,
    UserResponse,
)
from app.services.auth_service import AuthService, AuthServiceError
from app.services.email_verification_service import (
    EmailVerificationService,
    EmailVerificationError,
)
from app.services.password_reset_service import PasswordResetService, PasswordResetError
from app.utils.email_sender import send_otp_email, send_password_reset_email, send_verification_email

router = APIRouter(prefix="/auth", tags=["Authentication"])
settings = get_settings()


# --------------- Cookie Helper ---------------

def _get_cookie_security_params() -> tuple[str, bool]:
    """
    Return (samesite, secure) tuple based on ENVIRONMENT setting.

    development  -> ("strict", False)
      Local machine. Frontend (localhost:3000) and backend (localhost:8000)
      are same-origin context. HTTP is fine. SameSite=Strict is most secure.

    aws_dev      -> ("none", True)
      S3 frontend (*.s3-website.amazonaws.com) and API Gateway
      (*.execute-api.amazonaws.com) are different domains. Browsers silently
      drop SameSite=Strict cookies on cross-origin requests â€” every
      authenticated API call returns 401. SameSite=None; Secure=True is
      required. API Gateway always provides HTTPS so Secure=True is safe.

    production   -> ("strict", True)
      CloudFront dual-origin serves both frontend and API on the same domain.
      Cross-origin issue does not exist. SameSite=Strict is restored.
      HTTPS enforced by CloudFront.

    Any unrecognised value defaults to strictest setting (strict + True).
    """
    env = settings.ENVIRONMENT.lower()
    if env == "development":
        return "strict", False
    elif env == "aws_dev":
        return "none", True
    else:
        # production or any unrecognised value
        return "strict", True


def _set_auth_cookies(response: Response, access_token: str, refresh_token: str) -> None:
    """Set both access_token and refresh_token as httpOnly cookies.

    - access_token: path="/" (sent on all API calls)
    - refresh_token: path="/api/v1/auth" (sent only on auth endpoints â€” refresh, logout)
    """
    samesite, secure = _get_cookie_security_params()

    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=secure,
        samesite=samesite,
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        path="/",
    )
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=secure,
        samesite=samesite,
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
        path="/api/v1/auth",
    )


def _clear_auth_cookies(response: Response) -> None:
    """Clear both auth cookies with matching security params."""
    samesite, secure = _get_cookie_security_params()
    response.delete_cookie("access_token", path="/", secure=secure, samesite=samesite)
    response.delete_cookie("refresh_token", path="/api/v1/auth", secure=secure, samesite=samesite)

@router.post("/register", response_model=UserResponse, status_code=201)
async def register(
    data: UserRegisterRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Register a new customer account with consent tracking. Sends 6-digit OTP to email."""
    service = AuthService(db)
    ip = request.client.host if request.client else "unknown"
    ua = request.headers.get("user-agent", "")

    try:
        user = await service.register(data, ip_address=ip, user_agent=ua)
        await db.flush()

        # Send OTP verification email
        ev_service = EmailVerificationService(db)
        otp = await ev_service.create_verification(user.id)
        await db.commit()

        await send_otp_email(user.email, otp)

        return user
    except AuthServiceError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


@router.post("/login")
async def login(
    data: UserLoginRequest,
    response: Response,
    db: AsyncSession = Depends(get_db),
):
    """Authenticate user and return JWT tokens as httpOnly cookies.
    No tokens in JSON body â€” both are httpOnly cookies."""
    service = AuthService(db)
    try:
        user, access_token, refresh_token = await service.login(
            data.email, data.password
        )
        await db.commit()

        # 2FA required -- password verified but TOTP code needed
        if access_token is None:
            return JSONResponse(
                status_code=200,
                content={
                    "requires_2fa": True,
                    "user_id": str(user.id),
                    "message": "Please provide your TOTP code to complete login.",
                },
            )

        # Set BOTH tokens as httpOnly cookies â€” nothing in JSON body
        login_response = JSONResponse(
            status_code=200,
            content={
                "token_type": "bearer",
                "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            },
        )
        _set_auth_cookies(login_response, access_token, refresh_token)
        return login_response
    except AuthServiceError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


@router.post("/refresh")
async def refresh_token_endpoint(
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
):
    """Rotate refresh token and issue new access token.
    Reads refresh_token from httpOnly cookie (not request body)."""
    service = AuthService(db)

    # Read refresh token from cookie
    token_from_cookie = request.cookies.get("refresh_token")
    if not token_from_cookie:
        raise HTTPException(status_code=401, detail="Refresh token missing")

    try:
        new_access, new_refresh = await service.rotate_refresh_token(
            token_from_cookie
        )
        await db.commit()

        refresh_response = JSONResponse(
            status_code=200,
            content={
                "token_type": "bearer",
                "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            },
        )
        _set_auth_cookies(refresh_response, new_access, new_refresh)
        return refresh_response
    except AuthServiceError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


@router.post("/logout", response_model=MessageResponse)
async def logout(
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
):
    """Revoke all refresh tokens and clear both auth cookies.
    Handles case where token is already expired -- still clears cookies."""
   

    # Always clear BOTH cookies regardless of auth status
    _clear_auth_cookies(response)

    # Try to revoke refresh tokens if user is authenticated
    try:
        token = request.cookies.get("access_token")
        if token:
            payload = decode_token(token)
            if payload and payload.get("type") == "access":
                user_id = payload.get("sub")
                result = await db.execute(
                    select(User).where(User.id == user_id)
                )
                user = result.scalar_one_or_none()
                if user:
                    service = AuthService(db)
                    await service.logout(user.id)
                    await db.commit()
    except Exception:
        pass

    return MessageResponse(message="Logged out successfully")


@router.get("/me", response_model=UserResponse)
async def get_me(user: User = Depends(get_current_user)):
    """Get current authenticated user profile."""
    return user


# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€ Email Verification (OTP) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€


@router.post("/verify-email", response_model=MessageResponse)
async def verify_email_otp(
    data: OTPVerifyRequest,
    db: AsyncSession = Depends(get_db),
):
    """Verify email address using 6-digit OTP sent to email."""
    service = EmailVerificationService(db)
    try:
        user = await service.verify_email(data.email, data.otp)
        await db.commit()
        return MessageResponse(message=f"Email {user.email} verified successfully.")
    except EmailVerificationError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


@router.post("/verify-email-token", response_model=MessageResponse)
async def verify_email_token(
    data: EmailVerifyRequest,
    db: AsyncSession = Depends(get_db),
):
    """Legacy: Verify email address using token link (backward compatibility)."""
    service = EmailVerificationService(db)
    try:
        user = await service.verify_email_by_token(data.token)
        await db.commit()
        return MessageResponse(message=f"Email {user.email} verified successfully.")
    except EmailVerificationError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


@router.post("/resend-otp", response_model=MessageResponse)
async def resend_otp(
    data: ResendOTPRequest,
    db: AsyncSession = Depends(get_db),
):
    """Resend OTP verification email by email address (no auth required)."""
    service = EmailVerificationService(db)
    try:
        otp, user = await service.resend_verification_by_email(data.email)
        await db.commit()
        await send_otp_email(user.email, otp)
        return MessageResponse(message="A new OTP has been sent to your email.")
    except EmailVerificationError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


@router.post("/resend-verification", response_model=MessageResponse)
async def resend_verification(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Resend OTP verification email for current authenticated user."""
    service = EmailVerificationService(db)
    try:
        otp = await service.resend_verification(user.id)
        await db.commit()
        await send_otp_email(user.email, otp)
        return MessageResponse(message="Verification OTP sent.")
    except EmailVerificationError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€ Forgot / Reset Password â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€


@router.post("/forgot-password", response_model=MessageResponse)
async def forgot_password(
    data: ForgotPasswordRequest,
    db: AsyncSession = Depends(get_db),
):
    """Request a password reset link. Always returns success (prevents email enumeration)."""
    service = PasswordResetService(db)
    token, email = await service.create_reset_token(data.email)
    await db.commit()

    if token and email:
        await send_password_reset_email(email, token)

    return MessageResponse(
        message="If an account with that email exists, a reset link has been sent."
    )


@router.post("/reset-password", response_model=MessageResponse)
async def reset_password(
    data: ResetPasswordRequest,
    db: AsyncSession = Depends(get_db),
):
    """Reset password using token from email."""
    service = PasswordResetService(db)
    try:
        await service.reset_password(data.token, data.new_password)
        await db.commit()
        return MessageResponse(message="Password reset successfully. Please login with your new password.")
    except PasswordResetError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
