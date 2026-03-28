"""
Admin Settings API Ã¢â‚¬â€ /api/v1/admin/settings/
Phase 13H: Admin Merchant UPI Configuration.
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field, field_validator
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime as dt

import re

from app.core.database import get_db
from app.middleware.auth import require_role
from app.models.models import User
from app.services.store_settings_service import (
    StoreSettingsService,
    SettingsServiceError,
)

router = APIRouter(
    prefix="/admin/settings",
    tags=["Admin Ã¢â‚¬â€ Store Settings"],
)

admin_only = require_role("admin")

VPA_REGEX = re.compile(r"^[a-zA-Z0-9._-]+@[a-zA-Z]{2,}$")


# Ã¢â€â‚¬Ã¢â€â‚¬ Schemas Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬

class MerchantUpiResponse(BaseModel):
    merchant_upi_vpa: str | None
    description: str | None = None
    updated_at: dt | None = None

    class Config:
        from_attributes = True


class MerchantUpiUpdateRequest(BaseModel):
    merchant_upi_vpa: str = Field(
        ..., min_length=4, max_length=50,
        description="Merchant UPI VPA (e.g., ashmistore@razorpay)",
        examples=["ashmistore@razorpay", "ashmi@ybl"],
    )

    @field_validator("merchant_upi_vpa")
    @classmethod
    def validate_vpa_format(cls, v: str) -> str:
        v = v.strip()
        if not VPA_REGEX.match(v):
            raise ValueError(
                f"Invalid UPI VPA format: '{v}'. "
                "Expected: username@bankhandle"
            )
        return v


class MerchantUpiUpdateResponse(BaseModel):
    merchant_upi_vpa: str
    previous_vpa: str | None
    updated_by: str
    message: str


class UpiAuditEntry(BaseModel):
    id: str
    old_value: str | None
    new_value: str | None
    changed_by: str
    changed_at: dt | None

    class Config:
        from_attributes = True


# Ã¢â€â‚¬Ã¢â€â‚¬ Endpoints Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬


@router.get(
    "/upi",
    response_model=MerchantUpiResponse,
    summary="Get current merchant UPI VPA",
)
async def get_merchant_upi(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(admin_only),
):
    """Retrieve the current merchant UPI Virtual Payment Address."""
    service = StoreSettingsService(db)
    return await service.get_merchant_upi_vpa()


@router.put(
    "/upi",
    response_model=MerchantUpiUpdateResponse,
    summary="Update merchant UPI VPA",
)
async def update_merchant_upi(
    data: MerchantUpiUpdateRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(admin_only),
):
    """
    Update the store's merchant UPI VPA.
    All future UPI payments will be routed to the new address.
    Existing completed payments are not affected.
    Audit-logged: records old Ã¢â€ â€™ new VPA, admin, timestamp.
    """
    service = StoreSettingsService(db)
    try:
        result = await service.update_merchant_upi_vpa(
            new_vpa=data.merchant_upi_vpa,
            admin_id=user.id,
        )
        await db.commit()
        return MerchantUpiUpdateResponse(**result)
    except SettingsServiceError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


@router.get(
    "/upi/audit",
    response_model=list[UpiAuditEntry],
    summary="Get merchant UPI change history",
)
async def get_upi_audit_trail(
    limit: int = 5,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(admin_only),
):
    """Returns the last N merchant UPI VPA changes with timestamps."""
    service = StoreSettingsService(db)
    return await service.get_upi_audit_trail(limit=limit)


# ---- Shipping Config Schemas ----

class ShippingConfigResponse(BaseModel):
    shipping_fee: float
    free_shipping_threshold: float

class ShippingConfigUpdateRequest(BaseModel):
    shipping_fee: float = Field(..., ge=0, le=10000, description="Shipping fee in INR")
    free_shipping_threshold: float = Field(..., ge=0, le=100000, description="Min order for free shipping")

class ShippingConfigUpdateResponse(BaseModel):
    shipping_fee: float
    free_shipping_threshold: float
    message: str


# ---- Shipping Config Endpoints ----

@router.get(
    "/shipping",
    response_model=ShippingConfigResponse,
    summary="Get shipping configuration",
)
async def get_shipping_config(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(admin_only),
):
    """Retrieve current shipping fee and free-shipping threshold."""
    service = StoreSettingsService(db)
    return await service.get_shipping_config()


@router.put(
    "/shipping",
    response_model=ShippingConfigUpdateResponse,
    summary="Update shipping configuration",
)
async def update_shipping_config(
    data: ShippingConfigUpdateRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(admin_only),
):
    """Update shipping fee and free-shipping threshold. Audit-logged."""
    service = StoreSettingsService(db)
    try:
        result = await service.update_shipping_config(
            shipping_fee=data.shipping_fee,
            free_shipping_threshold=data.free_shipping_threshold,
            admin_id=user.id,
        )
        await db.commit()
        return ShippingConfigUpdateResponse(**result)
    except SettingsServiceError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)

# ---- Seller / Business Config ----

class SellerConfigResponse(BaseModel):
    seller_name: str = ""
    seller_gstin: str = ""
    seller_address: str = ""
    seller_state: str = ""
    seller_state_code: str = ""

class SellerConfigUpdateRequest(BaseModel):
    seller_name: str = Field(..., min_length=1, max_length=200)
    seller_gstin: str = Field("", max_length=15,description="Optional GSTIN - if provided must be exactly 15 characters")
    seller_address: str = Field(..., min_length=1, max_length=500)
    seller_state: str = Field(..., min_length=1, max_length=100)
    seller_state_code: str = Field(..., min_length=1, max_length=5)

class SellerConfigUpdateResponse(BaseModel):
    seller_name: str
    seller_gstin: str
    seller_address: str
    seller_state: str
    seller_state_code: str
    message: str

@router.get("/seller", response_model=SellerConfigResponse, summary="Get seller/business configuration")
async def get_seller_config(db: AsyncSession = Depends(get_db), user: User = Depends(admin_only)):
    service = StoreSettingsService(db)
    return await service.get_seller_config()

@router.put("/seller", response_model=SellerConfigUpdateResponse, summary="Update seller/business configuration")
async def update_seller_config(data: SellerConfigUpdateRequest, db: AsyncSession = Depends(get_db), user: User = Depends(admin_only)):
    service = StoreSettingsService(db)
    try:
        result = await service.update_seller_config(data.model_dump(), admin_id=user.id)
        await db.commit()
        return SellerConfigUpdateResponse(**result)
    except SettingsServiceError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


# ---- Contact Config ----

class ContactConfigResponse(BaseModel):
    store_email: str
    store_whatsapp: str


class ContactConfigUpdateRequest(BaseModel):
    store_email: str = Field("", max_length=100)
    store_whatsapp: str = Field("", max_length=15)


class ContactConfigUpdateResponse(BaseModel):
    message: str
    store_email: str
    store_whatsapp: str


@router.get("/settings/contact", response_model=ContactConfigResponse, summary="Get store contact configuration")
async def get_contact_config(db: AsyncSession = Depends(get_db), user: User = Depends(admin_only)):
    service = StoreSettingsService(db)
    data = await service.get_contact_config()
    return ContactConfigResponse(**data)


@router.put("/settings/contact", response_model=ContactConfigUpdateResponse, summary="Update store contact configuration")
async def update_contact_config(request: ContactConfigUpdateRequest, db: AsyncSession = Depends(get_db), user: User = Depends(admin_only)):
    service = StoreSettingsService(db)
    try:
        result = await service.update_contact_config(
            store_email=request.store_email,
            store_whatsapp=request.store_whatsapp,
            admin_id=user.id,
        )
        await db.commit()
        return ContactConfigUpdateResponse(**result)
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=str(e))

