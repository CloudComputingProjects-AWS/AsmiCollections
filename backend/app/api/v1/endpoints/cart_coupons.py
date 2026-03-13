"""
Cart & Coupon API Ã¢â‚¬â€ Phase 6.
Cart: /api/v1/cart/ (auth required)
Coupons: /api/v1/coupons/ (apply = auth, admin CRUD = admin)
"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.middleware.auth import get_current_user, require_role
from app.models.models import User
from app.schemas.auth import MessageResponse
from app.schemas.cart_coupon import (
    ApplyCouponRequest,
    CartAddRequest,
    CartMergeRequest,
    CartResponse,
    CartUpdateRequest,
    CouponApplyResult,
    CouponCreate,
    CouponResponse,
    CouponUpdate,
)
from app.services.cart_coupon_service import (
    CartCouponError,
    CartService,
    CouponService,
)

# Ã¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢Â
# CART ROUTER (auth required)
# Ã¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢Â

cart_router = APIRouter(prefix="/cart", tags=["Cart"])


def _handle_error(e: CartCouponError):
    raise HTTPException(status_code=e.status_code, detail=e.message)


@cart_router.get("", response_model=CartResponse)
async def get_cart(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Get current user's cart with enriched item details."""
    service = CartService(db)
    return await service.get_cart(user.id)


@cart_router.post("/add", response_model=CartResponse)
async def add_to_cart(
    data: CartAddRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Add item to cart. Merges quantity if variant already in cart."""
    service = CartService(db)
    try:
        result = await service.add_item(user.id, data.variant_id, data.quantity)
        await db.commit()
        return result
    except CartCouponError as e:
        _handle_error(e)


@cart_router.put("/{variant_id}", response_model=CartResponse)
async def update_cart_item(
    variant_id: UUID,
    data: CartUpdateRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Update quantity of a cart item."""
    service = CartService(db)
    try:
        result = await service.update_item(user.id, variant_id, data.quantity)
        await db.commit()
        return result
    except CartCouponError as e:
        _handle_error(e)


@cart_router.delete("/{variant_id}", response_model=CartResponse)
async def remove_cart_item(
    variant_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Remove item from cart."""
    service = CartService(db)
    try:
        result = await service.remove_item(user.id, variant_id)
        await db.commit()
        return result
    except CartCouponError as e:
        _handle_error(e)


@cart_router.delete("", response_model=MessageResponse)
async def clear_cart(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Clear all items from cart."""
    service = CartService(db)
    await service.clear_cart(user.id)
    await db.commit()
    return MessageResponse(message="Cart cleared.")


@cart_router.post("/merge", response_model=CartResponse)
async def merge_guest_cart(
    data: CartMergeRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Merge guest localStorage cart into server-side cart on login."""
    service = CartService(db)
    result = await service.merge_guest_cart(user.id, data.items)
    await db.commit()
    return result


@cart_router.get("/count")
async def get_cart_count(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Get cart item count for header badge."""
    service = CartService(db)
    count = await service.get_item_count(user.id)
    return {"count": count}


# Ã¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢Â
# COUPON Ã¢â‚¬â€ CUSTOMER FACING
# Ã¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢Â

coupon_router = APIRouter(prefix="/coupons", tags=["Coupons"])


@coupon_router.post("/apply", response_model=CouponApplyResult)
async def apply_coupon(
    data: ApplyCouponRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """
    Validate and apply coupon code.
    Checks: active, dates, min order, usage limits, per-user limit.
    """
    # Get cart subtotal
    cart_service = CartService(db)
    cart = await cart_service.get_cart(user.id)

    if not cart["items"]:
        raise HTTPException(status_code=400, detail="Cart is empty.")

    coupon_service = CouponService(db)
    result = await coupon_service.apply_coupon(
        user.id, data.code, cart["subtotal"]
    )
    await db.commit()
    return result


# Ã¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢Â
# COUPON Ã¢â‚¬â€ ADMIN CRUD
# Ã¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢Â

admin_coupon_router = APIRouter(prefix="/admin/coupons", tags=["Admin Ã¢â‚¬â€ Coupons"])
product_mgr = require_role("product_manager", "admin")


@admin_coupon_router.get("", response_model=list[CouponResponse])
async def list_coupons(
    active_only: bool = False,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(product_mgr),
):
    """List all coupons."""
    service = CouponService(db)
    return await service.list_coupons(active_only)


@admin_coupon_router.post("", response_model=CouponResponse, status_code=201)
async def create_coupon(
    data: CouponCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(product_mgr),
):
    """Create a new coupon."""
    service = CouponService(db)
    try:
        coupon = await service.create_coupon(data)
        await db.commit()
        return coupon
    except CartCouponError as e:
        _handle_error(e)


@admin_coupon_router.put("/{coupon_id}", response_model=CouponResponse)
async def update_coupon(
    coupon_id: UUID,
    data: CouponUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(product_mgr),
):
    """Update a coupon."""
    service = CouponService(db)
    try:
        coupon = await service.update_coupon(coupon_id, data)
        await db.commit()
        return coupon
    except CartCouponError as e:
        _handle_error(e)


@admin_coupon_router.delete("/{coupon_id}", response_model=MessageResponse)
async def delete_coupon(
    coupon_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(product_mgr),
):
    """Soft-delete a coupon."""
    service = CouponService(db)
    try:
        await service.delete_coupon(coupon_id)
        await db.commit()
        return MessageResponse(message="Coupon soft-deleted.")
    except CartCouponError as e:
        _handle_error(e)

