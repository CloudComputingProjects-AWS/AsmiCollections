"""
Pydantic schemas for authentication & user management.
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


# ──────────────── Auth Request Schemas ────────────────

class UserRegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)
    phone: str | None = Field(None, max_length=20)
    country_code: str | None = Field(None, max_length=5)
    terms_accepted: bool = Field(..., description="Must be True")
    privacy_accepted: bool = Field(..., description="Must be True")
    marketing_email: bool = False
    marketing_sms: bool = False


class UserLoginRequest(BaseModel):
    email: EmailStr
    password: str


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str = Field(min_length=8, max_length=128)


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str = Field(min_length=8, max_length=128)


class EmailVerifyRequest(BaseModel):
    token: str


class OTPVerifyRequest(BaseModel):
    email: EmailStr
    otp: str = Field(min_length=6, max_length=6, pattern=r"^\d{6}$")


class ResendOTPRequest(BaseModel):
    email: EmailStr


# ──────────────── Auth Response Schemas ────────────────

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class UserResponse(BaseModel):
    id: UUID
    email: str
    first_name: str | None
    last_name: str | None
    phone: str | None
    country_code: str | None
    role: str
    email_verified: bool
    is_active: bool
    totp_enabled: bool = False
    created_at: datetime

    class Config:
        from_attributes = True


class MessageResponse(BaseModel):
    message: str


# ──────────────── User Profile Schemas ────────────────

class UserProfileUpdate(BaseModel):
    first_name: str | None = Field(None, max_length=100)
    last_name: str | None = Field(None, max_length=100)
    phone: str | None = Field(None, max_length=20)
    country_code: str | None = Field(None, max_length=5)



class AddressUpdate(BaseModel):
    label: str | None = Field(None, pattern="^(home|office|other)$")
    full_name: str | None = Field(None, max_length=200)
    phone: str | None = Field(None, max_length=20)
    address_line_1: str | None = Field(None, max_length=500)
    address_line_2: str | None = Field(None, max_length=500)
    city: str | None = Field(None, max_length=100)
    state: str | None = Field(None, max_length=100)
    postal_code: str | None = Field(None, max_length=20)
    country: str | None = Field(None, max_length=100)
    is_default: bool | None = None

    class Config:
        from_attributes = True
