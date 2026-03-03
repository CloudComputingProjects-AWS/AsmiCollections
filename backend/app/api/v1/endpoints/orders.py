"""
Checkout & Order API â€” Phase 7.
User: /api/v1/orders/, /api/v1/checkout/, /api/v1/addresses/
Admin: /api/v1/admin/orders/
"""
import math
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.middleware.auth import get_current_user, require_role
from app.models.models import User, UserAddress
from app.schemas.auth import MessageResponse
from app.schemas.order import (
    AddressCreate, AddressResponse, CheckoutRequest, OrderResponse,
    OrderSummaryResponse, OrderTransitionRequest, OrderTimelineResponse,
    OrderItemResponse, StatusHistoryItem,
)
from app.schemas.product import PaginatedResponse
from app.services.order_service import OrderService, OrderServiceError
from sqlalchemy import select

# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# ADDRESS ROUTER
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

address_router = APIRouter(prefix="/addresses", tags=["Addresses"])

def _handle(e: OrderServiceError):
    raise HTTPException(status_code=e.status_code, detail=e.message)


@address_router.get("", response_model=list[AddressResponse])
async def list_addresses(db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    result = await db.execute(select(UserAddress).where(UserAddress.user_id == user.id, UserAddress.deleted_at.is_(None)))
    return list(result.scalars().all())


@address_router.post("", response_model=AddressResponse, status_code=201)
async def create_address(data: AddressCreate, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    addr = UserAddress(user_id=user.id, **data.model_dump())
    db.add(addr)
    await db.commit()
    await db.refresh(addr)
    return addr


@address_router.put("/{address_id}", response_model=AddressResponse)
async def update_address(address_id: UUID, data: AddressCreate, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    result = await db.execute(select(UserAddress).where(UserAddress.id == address_id, UserAddress.user_id == user.id, UserAddress.deleted_at.is_(None)))
    addr = result.scalar_one_or_none()
    if not addr:
        raise HTTPException(404, "Address not found.")
    for k, v in data.model_dump().items():
        setattr(addr, k, v)
    await db.commit()
    return addr


@address_router.delete("/{address_id}", response_model=MessageResponse)
async def delete_address(address_id: UUID, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    result = await db.execute(select(UserAddress).where(UserAddress.id == address_id, UserAddress.user_id == user.id, UserAddress.deleted_at.is_(None)))
    addr = result.scalar_one_or_none()
    if not addr:
        raise HTTPException(404, "Address not found.")
    addr.soft_delete()
    await db.commit()
    return MessageResponse(message="Address deleted.")


# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# CHECKOUT ROUTER
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

checkout_router = APIRouter(prefix="/checkout", tags=["Checkout"])


@checkout_router.post("/summary", response_model=OrderSummaryResponse)
async def get_order_summary(data: CheckoutRequest, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    """Pre-checkout order summary with full tax breakdown."""
    service = OrderService(db)
    try:
        return await service.get_order_summary(user.id, data.shipping_address_id, data.coupon_code)
    except OrderServiceError as e:
        _handle(e)


@checkout_router.post("/place-order", response_model=OrderResponse)
async def place_order(data: CheckoutRequest, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    """
    Place order: validate cart, lock stock, reserve inventory,
    calculate GST, create order with snapshots, clear cart.
    """
    service = OrderService(db)
    try:
        order = await service.place_order(user.id, data)
        await db.commit()
        return await service.get_order(order.id, user.id)
    except OrderServiceError as e:
        _handle(e)


# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# USER ORDERS
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

order_router = APIRouter(prefix="/orders", tags=["Orders"])


@order_router.get("", response_model=PaginatedResponse)
async def list_my_orders(page: int = Query(1, ge=1), page_size: int = Query(10, ge=1, le=50),
    db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    service = OrderService(db)
    orders, total = await service.list_user_orders(user.id, page, page_size)
    return PaginatedResponse(
        items=[OrderResponse.model_validate(o) for o in orders],
        total=total, page=page, page_size=page_size,
        total_pages=math.ceil(total / page_size) if total else 0,
    )


@order_router.get("/{order_id}", response_model=OrderResponse)
async def get_my_order(order_id: UUID, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    service = OrderService(db)
    try:
        return await service.get_order(order_id, user.id)
    except OrderServiceError as e:
        _handle(e)


@order_router.get("/{order_id}/timeline", response_model=OrderTimelineResponse)
async def get_order_timeline(order_id: UUID, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    """User-facing order status timeline."""
    service = OrderService(db)
    try:
        return await service.get_order_timeline(order_id, user.id)
    except OrderServiceError as e:
        _handle(e)


@order_router.post("/{order_id}/cancel", response_model=OrderResponse)
async def cancel_order(order_id: UUID, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    """Cancel order (only if placed/confirmed/processing)."""
    service = OrderService(db)
    try:
        order = await service.get_order(order_id, user.id)
        order = await service.transition_order(order.id, "cancelled", user.id, "Cancelled by customer")
        await db.commit()
        return await service.get_order(order.id, user.id)
    except OrderServiceError as e:
        _handle(e)


# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# ADMIN ORDERS
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

admin_order_router = APIRouter(prefix="/admin/orders", tags=["Admin â€” Orders"])
order_mgr = require_role("order_manager", "admin")


@admin_order_router.get("", response_model=PaginatedResponse)
async def admin_list_orders(status: str | None = None, page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db), user: User = Depends(order_mgr)):
    service = OrderService(db)
    orders, total = await service.admin_list_orders(status, page, page_size)
    return PaginatedResponse(
        items=[OrderResponse.model_validate(o) for o in orders],
        total=total, page=page, page_size=page_size,
        total_pages=math.ceil(total / page_size) if total else 0,
    )


@admin_order_router.get("/{order_id}", response_model=OrderResponse)
async def admin_get_order(order_id: UUID, db: AsyncSession = Depends(get_db), user: User = Depends(order_mgr)):
    service = OrderService(db)
    try:
        return await service.get_order(order_id)
    except OrderServiceError as e:
        _handle(e)


@admin_order_router.put("/{order_id}/transition", response_model=OrderResponse)
async def admin_transition_order(order_id: UUID, data: OrderTransitionRequest,
    db: AsyncSession = Depends(get_db), user: User = Depends(order_mgr)):
    """State machine enforced status transition."""
    service = OrderService(db)
    try:
        order = await service.transition_order(order_id, data.new_status, user.id, data.reason)
        await db.commit()
        return await service.get_order(order.id)
    except OrderServiceError as e:
        _handle(e)


@admin_order_router.get("/{order_id}/history")
async def admin_order_history(order_id: UUID, db: AsyncSession = Depends(get_db), user: User = Depends(order_mgr)):
    service = OrderService(db)
    try:
        return await service.get_order_timeline(order_id)
    except OrderServiceError as e:
        _handle(e)
