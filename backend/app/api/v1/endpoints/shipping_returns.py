"""
Shipping, Returns & Refunds API Endpoints â€” Phase 10
V2.5 Blueprint

Routes:
  Customer:
    POST /api/v1/returns                         â†’ Request return
    GET  /api/v1/returns                         â†’ My returns

  Admin (OrderManager):
    POST /api/v1/admin/shipments                 â†’ Create shipment
    GET  /api/v1/admin/shipments                 â†’ List shipments
    GET  /api/v1/admin/shipments/:id             â†’ Shipment detail
    PUT  /api/v1/admin/shipments/:id             â†’ Update shipment
    POST /api/v1/admin/shipments/:id/ship        â†’ Mark shipped (triggers order transition)
    POST /api/v1/admin/shipments/:id/deliver     â†’ Mark delivered (triggers order transition)
    GET  /api/v1/admin/returns                   â†’ List all returns
    GET  /api/v1/admin/returns/:id               â†’ Return detail
    POST /api/v1/admin/returns/:id/action        â†’ Approve/reject
    POST /api/v1/admin/returns/:id/receive       â†’ Mark received (restocks)
    POST /api/v1/admin/refunds                   â†’ Initiate refund
    GET  /api/v1/admin/refunds                   â†’ List refunds
"""

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.middleware.auth import get_current_user, require_role
from app.models.models import User
from app.schemas.shipping_returns_schemas import (
    RefundInitiateRequest,
    RefundListResponse,
    RefundResponse,
    ReturnActionRequest,
    ReturnListResponse,
    ReturnReceiveRequest,
    ReturnRequestCreate,
    ReturnResponse,
    ShipmentCreateRequest,
    ShipmentResponse,
    ShipmentUpdateRequest,
)
from app.services.notification_service import NotificationService
from app.services.return_service import ReturnService, ReturnServiceError
from app.services.shipping_service import ShippingService, ShippingServiceError

# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# CUSTOMER ROUTES
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

customer_returns_router = APIRouter(prefix="/returns", tags=["Returns"])


@customer_returns_router.post("", response_model=ReturnResponse)
async def request_return(
    data: ReturnRequestCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Customer requests a return/exchange for a delivered order item."""
    service = ReturnService(db)
    try:
        return_req = await service.request_return(
            user_id=user.id,
            order_id=data.order_id,
            order_item_id=data.order_item_id,
            reason=data.reason,
            reason_detail=data.reason_detail,
            return_type=data.return_type,
            quantity=data.quantity,
        )
        await db.commit()
        return ReturnResponse.model_validate(return_req)
    except ReturnServiceError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


@customer_returns_router.get("", response_model=ReturnListResponse)
async def my_returns(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List customer's own return requests."""
    service = ReturnService(db)
    returns, total = await service.list_returns(
        page=page, page_size=page_size, user_id=user.id
    )
    return ReturnListResponse(
        returns=[ReturnResponse.model_validate(r) for r in returns],
        total=total, page=page, page_size=page_size,
    )


# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# ADMIN: SHIPPING
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

admin_shipping_router = APIRouter(
    prefix="/admin/shipments",
    tags=["Admin Shipping"],
)
order_mgr = require_role("order_manager", "admin")


@admin_shipping_router.post("", response_model=ShipmentResponse)
async def create_shipment(
    data: ShipmentCreateRequest,
    user: User = Depends(order_mgr),
    db: AsyncSession = Depends(get_db),
):
    """Create shipment for an order."""
    service = ShippingService(db)
    try:
        shipment = await service.create_shipment(
            order_id=data.order_id,
            courier_partner=data.courier_partner,
            tracking_number=data.tracking_number,
            awb_number=data.awb_number,
            weight_grams=data.weight_grams,
            estimated_delivery=data.estimated_delivery,
        )
        await db.commit()
        return ShipmentResponse.model_validate(shipment)
    except ShippingServiceError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


@admin_shipping_router.get("")
async def list_shipments(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: str | None = None,
    courier: str | None = None,
    user: User = Depends(order_mgr),
    db: AsyncSession = Depends(get_db),
):
    """List all shipments."""
    service = ShippingService(db)
    shipments, total = await service.list_shipments(
        page=page, page_size=page_size, status=status, courier=courier
    )
    return {
        "shipments": [ShipmentResponse.model_validate(s) for s in shipments],
        "total": total, "page": page, "page_size": page_size,
    }


@admin_shipping_router.get("/{shipment_id}", response_model=ShipmentResponse)
async def get_shipment(
    shipment_id: UUID,
    user: User = Depends(order_mgr),
    db: AsyncSession = Depends(get_db),
):
    """Get shipment details."""
    service = ShippingService(db)
    shipment = await service.get_shipment_by_order(shipment_id)
    if not shipment:
        # Try by shipment ID directly
        from sqlalchemy import select
        from app.models.models import Shipment
        result = await db.execute(select(Shipment).where(Shipment.id == shipment_id))
        shipment = result.scalar_one_or_none()
    if not shipment:
        raise HTTPException(status_code=404, detail="Shipment not found")
    return ShipmentResponse.model_validate(shipment)


@admin_shipping_router.put("/{shipment_id}", response_model=ShipmentResponse)
async def update_shipment(
    shipment_id: UUID,
    data: ShipmentUpdateRequest,
    user: User = Depends(order_mgr),
    db: AsyncSession = Depends(get_db),
):
    """Update shipment tracking info."""
    service = ShippingService(db)
    try:
        shipment = await service.update_shipment(
            shipment_id, **data.model_dump(exclude_none=True)
        )
        await db.commit()
        return ShipmentResponse.model_validate(shipment)
    except ShippingServiceError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


@admin_shipping_router.post("/{shipment_id}/ship", response_model=ShipmentResponse)
async def mark_shipped(
    shipment_id: UUID,
    user: User = Depends(order_mgr),
    db: AsyncSession = Depends(get_db),
):
    """Mark shipment as shipped. Transitions order: processing â†’ shipped."""
    service = ShippingService(db)
    try:
        shipment = await service.mark_shipped(shipment_id)

        # Transition order via state machine
        from app.services.order_state_machine import can_transition
        from app.models.models import Order, OrderStatusHistory
        from sqlalchemy import select

        result = await db.execute(select(Order).where(Order.id == shipment.order_id))
        order = result.scalar_one_or_none()
        if order and can_transition(order.order_status, "shipped"):
            old = order.order_status
            order.order_status = "shipped"
            db.add(OrderStatusHistory(
                order_id=order.id, from_status=old,
                to_status="shipped", changed_by=user.id,
                change_reason="Shipment marked as shipped",
            ))

            # Send notification
            notif = NotificationService(db)
            await notif.send_shipping_notification(order.id, shipment.tracking_url)

        await db.commit()
        return ShipmentResponse.model_validate(shipment)
    except ShippingServiceError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


@admin_shipping_router.post("/{shipment_id}/deliver", response_model=ShipmentResponse)
async def mark_delivered(
    shipment_id: UUID,
    user: User = Depends(order_mgr),
    db: AsyncSession = Depends(get_db),
):
    """Mark shipment as delivered. Transitions order through delivery states."""
    service = ShippingService(db)
    try:
        shipment = await service.mark_delivered(shipment_id)

        from app.services.order_state_machine import can_transition
        from app.models.models import Order, OrderStatusHistory
        from sqlalchemy import select

        result = await db.execute(select(Order).where(Order.id == shipment.order_id))
        order = result.scalar_one_or_none()
        if order:
            # shipped â†’ out_for_delivery â†’ delivered
            transitions = []
            if order.order_status == "shipped" and can_transition("shipped", "out_for_delivery"):
                transitions.append(("shipped", "out_for_delivery"))
            if can_transition(transitions[-1][1] if transitions else order.order_status, "delivered"):
                prev = transitions[-1][1] if transitions else order.order_status
                transitions.append((prev, "delivered"))

            for from_s, to_s in transitions:
                order.order_status = to_s
                db.add(OrderStatusHistory(
                    order_id=order.id, from_status=from_s,
                    to_status=to_s, changed_by=user.id,
                    change_reason="Shipment delivered",
                ))

            notif = NotificationService(db)
            await notif.send_delivery_notification(order.id)

        await db.commit()
        return ShipmentResponse.model_validate(shipment)
    except ShippingServiceError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# ADMIN: RETURNS
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

admin_returns_router = APIRouter(
    prefix="/admin/returns",
    tags=["Admin Returns"],
)


@admin_returns_router.get("", response_model=ReturnListResponse)
async def list_returns(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: str | None = None,
    user: User = Depends(order_mgr),
    db: AsyncSession = Depends(get_db),
):
    """List all return requests."""
    service = ReturnService(db)
    returns, total = await service.list_returns(
        page=page, page_size=page_size, status=status
    )
    return ReturnListResponse(
        returns=[ReturnResponse.model_validate(r) for r in returns],
        total=total, page=page, page_size=page_size,
    )


@admin_returns_router.get("/{return_id}", response_model=ReturnResponse)
async def get_return_detail(
    return_id: UUID,
    user: User = Depends(order_mgr),
    db: AsyncSession = Depends(get_db),
):
    """Get return request details."""
    service = ReturnService(db)
    try:
        return_req = await service.get_return(return_id)
        return ReturnResponse.model_validate(return_req)
    except ReturnServiceError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


@admin_returns_router.post("/{return_id}/action", response_model=ReturnResponse)
async def return_action(
    return_id: UUID,
    data: ReturnActionRequest,
    user: User = Depends(order_mgr),
    db: AsyncSession = Depends(get_db),
):
    """Approve or reject a return request."""
    service = ReturnService(db)
    notif = NotificationService(db)
    try:
        if data.action == "approve":
            return_req = await service.approve_return(
                return_id, user.id, data.admin_notes, data.pickup_date
            )
            await notif.send_return_approved_notification(
                return_req.order_id, data.pickup_date
            )
        else:
            return_req = await service.reject_return(
                return_id, user.id, data.admin_notes
            )
            await notif.send_return_rejected_notification(
                return_req.order_id, data.admin_notes
            )
        await db.commit()
        return ReturnResponse.model_validate(return_req)
    except ReturnServiceError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


@admin_returns_router.post("/{return_id}/receive", response_model=ReturnResponse)
async def receive_return(
    return_id: UUID,
    data: ReturnReceiveRequest | None = None,
    user: User = Depends(order_mgr),
    db: AsyncSession = Depends(get_db),
):
    """Mark return as received. Restocks the variant."""
    service = ReturnService(db)
    try:
        return_req = await service.receive_return(
            return_id, user.id,
            admin_notes=data.admin_notes if data else None,
        )
        await db.commit()
        return ReturnResponse.model_validate(return_req)
    except ReturnServiceError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# ADMIN: REFUNDS
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

admin_refunds_router = APIRouter(
    prefix="/admin/refunds",
    tags=["Admin Refunds"],
)


@admin_refunds_router.post("", response_model=RefundResponse)
async def initiate_refund(
    data: RefundInitiateRequest,
    user: User = Depends(require_role("order_manager", "finance_manager", "admin")),
    db: AsyncSession = Depends(get_db),
):
    """Initiate refund via payment gateway. Auto-generates credit note."""
    service = ReturnService(db)
    notif = NotificationService(db)
    try:
        refund = await service.initiate_refund(
            order_id=data.order_id,
            amount=data.amount,
            admin_id=user.id,
            return_id=data.return_id,
            refund_method=data.refund_method,
            reason=data.reason,
        )
        await notif.send_refund_notification(data.order_id, data.amount)
        await db.commit()
        return RefundResponse.model_validate(refund)
    except ReturnServiceError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


@admin_refunds_router.get("", response_model=RefundListResponse)
async def list_refunds(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: str | None = None,
    order_id: UUID | None = None,
    user: User = Depends(require_role("order_manager", "finance_manager", "admin")),
    db: AsyncSession = Depends(get_db),
):
    """List all refunds."""
    service = ReturnService(db)
    refunds, total = await service.list_refunds(
        page=page, page_size=page_size, status=status, order_id=order_id
    )
    return RefundListResponse(
        refunds=[RefundResponse.model_validate(r) for r in refunds],
        total=total, page=page, page_size=page_size,
    )
