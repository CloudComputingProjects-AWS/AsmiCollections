"""
User Profile & Address endpoints — /api/v1/user/
"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.middleware.auth import get_current_user
from app.models.models import User, UserAddress
from app.schemas.auth import (
    AddressCreate,
    AddressResponse,
    AddressUpdate,
    ChangePasswordRequest,
    MessageResponse,
    UserProfileUpdate,
    UserResponse,
)
from app.core.security import hash_password, verify_password

router = APIRouter(prefix="/user", tags=["User Profile"])


@router.get("/profile", response_model=UserResponse)
async def get_profile(user: User = Depends(get_current_user)):
    return user


@router.put("/profile", response_model=UserResponse)
async def update_profile(
    data: UserProfileUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    update_data = data.model_dump(exclude_unset=True)
    if not update_data:
        raise HTTPException(400, "No fields to update")

    for key, value in update_data.items():
        setattr(user, key, value)

    await db.commit()
    await db.refresh(user)
    return user


@router.put("/change-password", response_model=MessageResponse)
async def change_password(
    data: ChangePasswordRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if not verify_password(data.current_password, user.password_hash):
        raise HTTPException(400, "Current password is incorrect")

    user.password_hash = hash_password(data.new_password)

    # Revoke all refresh tokens on password change
    from app.services.auth_service import AuthService
    service = AuthService(db)
    await service.logout(user.id)

    await db.commit()
    return MessageResponse(message="Password changed. Please login again.")


# ──────────────── Addresses ────────────────

@router.get("/addresses", response_model=list[AddressResponse])
async def list_addresses(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(UserAddress).where(
            UserAddress.user_id == user.id,
            UserAddress.deleted_at.is_(None),
        ).order_by(UserAddress.is_default.desc(), UserAddress.created_at.desc())
    )
    return result.scalars().all()


@router.post("/addresses", response_model=AddressResponse, status_code=201)
async def add_address(
    data: AddressCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # Enforce max 2 addresses per customer
    count_result = await db.execute(
        select(func.count()).select_from(UserAddress).where(
            UserAddress.user_id == user.id,
            UserAddress.deleted_at.is_(None),
        )
    )
    if count_result.scalar() >= 2:
        raise HTTPException(400, "Maximum 2 addresses allowed (shipping + billing)")
    # If setting as default, unset others
    if data.is_default:
        await db.execute(
            update(UserAddress)
            .where(UserAddress.user_id == user.id)
            .values(is_default=False)
        )

    address = UserAddress(user_id=user.id, **data.model_dump())
    db.add(address)
    await db.commit()
    await db.refresh(address)
    return address


@router.put("/addresses/{address_id}", response_model=AddressResponse)
async def update_address(
    address_id: UUID,
    data: AddressUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(UserAddress).where(
            UserAddress.id == address_id,
            UserAddress.user_id == user.id,
            UserAddress.deleted_at.is_(None),
        )
    )
    address = result.scalar_one_or_none()
    if not address:
        raise HTTPException(404, "Address not found")

    update_data = data.model_dump(exclude_unset=True)

    if update_data.get("is_default"):
        await db.execute(
            update(UserAddress)
            .where(UserAddress.user_id == user.id)
            .values(is_default=False)
        )

    for key, value in update_data.items():
        setattr(address, key, value)

    await db.commit()
    await db.refresh(address)
    return address


@router.delete("/addresses/{address_id}", response_model=MessageResponse)
async def delete_address(
    address_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    from datetime import datetime, timezone
    result = await db.execute(
        select(UserAddress).where(
            UserAddress.id == address_id,
            UserAddress.user_id == user.id,
            UserAddress.deleted_at.is_(None),
        )
    )
    address = result.scalar_one_or_none()
    if not address:
        raise HTTPException(404, "Address not found")

    # Soft delete
    address.deleted_at = datetime.now(timezone.utc)
    await db.commit()
    return MessageResponse(message="Address deleted")
