"""
Pydantic schemas for authentication & user management.
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, model_validator


# ──────────────── Auth Request Schemas ────────────────

class WhatsAppActivationUpdate(BaseModel):
    whatsapp_number: str | None = Field(None, max_length=20)
    whatsapp_country_code: str | None = Field(None, max_length=5)
    whatsapp_opt_in: bool

    @model_validator(mode="after")
    def validate_whatsapp_consent(self):
        if not self.whatsapp_opt_in:
            self.whatsapp_number = None
            self.whatsapp_country_code = None
            return self
        number = (self.whatsapp_number or "").strip()
        code = (self.whatsapp_country_code or "").strip()
        if not number.isascii() or not number.isdigit() or not 8 <= len(number) <= 15:
            raise ValueError("Enter a valid WhatsApp number without the country code")
        if not code.startswith("+") or not code[1:].isascii() or not code[1:].isdigit() or not 1 <= len(code[1:]) <= 3 or code[1] == "0":
            raise ValueError("Enter a valid country code")
        if len(code[1:] + number) > 15:
            raise ValueError("WhatsApp number including country code cannot exceed 15 digits")
        self.whatsapp_number = number
        self.whatsapp_country_code = code
        return self


class UserRegisterRequest(WhatsAppActivationUpdate):
    whatsapp_opt_in: bool = False
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)
    phone: str = Field(min_length=8, max_length=15, pattern=r"^[0-9]+$")
    country_code: str = Field(pattern=r"^\+[1-9][0-9]{0,2}$")
    terms_accepted: bool = Field(..., description="Must be True")
    privacy_accepted: bool = Field(..., description="Must be True")
    marketing_email: bool = False
    marketing_sms: bool = False

    @model_validator(mode="after")
    def validate_whatsapp_consent(self):
        if len(self.country_code) - 1 + len(self.phone) > 15:
            raise ValueError("Phone number including country code cannot exceed 15 digits")
        # Registration uses the account phone for WhatsApp, never a second input.
        self.whatsapp_number = self.phone if self.whatsapp_opt_in else None
        self.whatsapp_country_code = self.country_code if self.whatsapp_opt_in else None
        return self


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
    totp_enabled: bool | None = False
    created_at: datetime
    whatsapp_number: str | None = None
    whatsapp_country_code: str | None = None
    whatsapp_wa_id: str | None = None
    whatsapp_opt_in: bool = False
    whatsapp_activation_status: str = "not_started"

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
