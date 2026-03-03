"""
Payment Repository — Database operations for payment processing.

Handles:
  - payment_events (webhook idempotency)
  - FX rate storage/retrieval
  - Refund record CRUD
  - Order payment field updates
  - Stock deduction
  - Reservation management
  - Order status history
"""

import hashlib
import json
from datetime import datetime, timezone
from decimal import Decimal
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload


class PaymentRepository:
    """Data access layer for payment-related tables."""

    def __init__(self, db: AsyncSession):
        self.db = db

    # ────────────────────────────────────────────────
    # PAYMENT EVENTS (Webhook Idempotency)
    # ────────────────────────────────────────────────

    async def find_payment_event(self, gateway_event_id: str):
        """Check if a webhook event has already been processed."""
        from app.models.models import PaymentEvent

        result = await self.db.execute(
            select(PaymentEvent).where(
                PaymentEvent.gateway_event_id == gateway_event_id
            )
        )
        return result.scalar_one_or_none()

    async def create_payment_event(
        self,
        gateway: str,
        gateway_event_id: str,
        event_type: str,
        payload: dict,
        order_id: UUID | None = None,
    ):
        """Record a webhook event for idempotency tracking."""
        from app.models.models import PaymentEvent

        payload_hash = hashlib.sha256(
            json.dumps(payload, sort_keys=True, default=str).encode()
        ).hexdigest()

        event = PaymentEvent(
            gateway=gateway,
            gateway_event_id=gateway_event_id,
            event_type=event_type,
            payload_hash=payload_hash,
            order_id=order_id,
            processed=False,
        )
        self.db.add(event)
        await self.db.flush()
        return event

    async def mark_event_processed(self, event_id: UUID):
        """Mark a payment event as successfully processed."""
        from app.models.models import PaymentEvent

        await self.db.execute(
            update(PaymentEvent)
            .where(PaymentEvent.id == event_id)
            .values(
                processed=True,
                processed_at=datetime.now(timezone.utc),
            )
        )

    # ────────────────────────────────────────────────
    # ORDER PAYMENT FIELDS
    # ────────────────────────────────────────────────

    async def get_order(self, order_id: UUID):
        """Fetch order by ID."""
        from app.models.models import Order

        result = await self.db.execute(
            select(Order).where(Order.id == order_id)
        )
        return result.scalar_one_or_none()

    async def get_order_with_items(self, order_id: UUID):
        """Fetch order with items eagerly loaded."""
        from app.models.models import Order

        result = await self.db.execute(
            select(Order)
            .options(selectinload(Order.items))
            .where(Order.id == order_id)
        )
        return result.scalar_one_or_none()

    async def update_order_payment(
        self,
        order_id: UUID,
        *,
        payment_status: str,
        payment_gateway: str | None = None,
        payment_method: str | None = None,
        payment_gateway_order_id: str | None = None,
        payment_gateway_txn_id: str | None = None,
        order_status: str | None = None,
    ):
        """Update order payment fields after gateway response."""
        from app.models.models import Order

        values = {
            "payment_status": payment_status,
            "updated_at": datetime.now(timezone.utc),
        }
        if payment_gateway:
            values["payment_gateway"] = payment_gateway
        if payment_method:
            values["payment_method"] = payment_method
        if payment_gateway_order_id:
            values["payment_gateway_order_id"] = payment_gateway_order_id
        if payment_gateway_txn_id:
            values["payment_gateway_txn_id"] = payment_gateway_txn_id
        if order_status:
            values["order_status"] = order_status

        await self.db.execute(
            update(Order)
            .where(Order.id == order_id)
            .values(**values)
        )

    async def update_order_upi_vpa(self, order_id: UUID, vpa: str):
        """Store UPI VPA on order for receipts."""
        from app.models.models import Order

        await self.db.execute(
            update(Order)
            .where(Order.id == order_id)
            .values(upi_vpa=vpa, updated_at=datetime.now(timezone.utc))
        )

    async def lock_fx_rate_on_order(
        self,
        order_id: UUID,
        fx_rate: Decimal,
        fx_source: str,
        currency: str,
    ):
        """Lock the FX rate on an order at checkout time."""
        from app.models.models import Order

        await self.db.execute(
            update(Order)
            .where(Order.id == order_id)
            .values(
                fx_rate_used=fx_rate,
                fx_rate_source=fx_source,
                fx_locked_at=datetime.now(timezone.utc),
                currency=currency,
                updated_at=datetime.now(timezone.utc),
            )
        )

    # ────────────────────────────────────────────────
    # INVENTORY RESERVATIONS
    # ────────────────────────────────────────────────

    async def get_reservations_for_order(self, order_id: UUID):
        """Fetch all held reservations for an order."""
        from app.models.models import InventoryReservation

        result = await self.db.execute(
            select(InventoryReservation).where(
                InventoryReservation.order_id == order_id,
                InventoryReservation.status == "held",
            )
        )
        return result.scalars().all()

    async def release_reservations(self, order_id: UUID):
        """Release all held reservations for an order (payment failed)."""
        from app.models.models import InventoryReservation

        await self.db.execute(
            update(InventoryReservation)
            .where(
                InventoryReservation.order_id == order_id,
                InventoryReservation.status == "held",
            )
            .values(status="released")
        )

    async def confirm_reservations(self, order_id: UUID):
        """Confirm reservations (payment success)."""
        from app.models.models import InventoryReservation

        await self.db.execute(
            update(InventoryReservation)
            .where(
                InventoryReservation.order_id == order_id,
                InventoryReservation.status == "held",
            )
            .values(status="confirmed")
        )

    # ────────────────────────────────────────────────
    # STOCK DEDUCTION
    # ────────────────────────────────────────────────

    async def deduct_stock_for_order(self, order_id: UUID):
        """
        Permanently deduct stock for all items in an order.
        Uses SELECT FOR UPDATE to prevent race conditions.
        """
        from app.models.models import OrderItem, ProductVariant

        items_result = await self.db.execute(
            select(OrderItem).where(OrderItem.order_id == order_id)
        )
        items = items_result.scalars().all()

        for item in items:
            if item.product_variant_id:
                variant_result = await self.db.execute(
                    select(ProductVariant)
                    .where(ProductVariant.id == item.product_variant_id)
                    .with_for_update()
                )
                variant = variant_result.scalar_one_or_none()
                if variant:
                    variant.stock_quantity = max(
                        0, variant.stock_quantity - item.quantity
                    )

    # ────────────────────────────────────────────────
    # REFUNDS
    # ────────────────────────────────────────────────

    async def create_refund(
        self,
        order_id: UUID,
        amount: Decimal,
        currency: str,
        refund_method: str,
        initiated_by: UUID,
        return_id: UUID | None = None,
        gateway_refund_id: str | None = None,
    ):
        """Create a refund record."""
        from app.models.models import Refund

        refund = Refund(
            order_id=order_id,
            return_id=return_id,
            amount=amount,
            currency=currency,
            status="initiated",
            refund_method=refund_method,
            initiated_by=initiated_by,
            gateway_refund_id=gateway_refund_id,
        )
        self.db.add(refund)
        await self.db.flush()
        return refund

    async def update_refund_status(
        self,
        refund_id: UUID,
        status: str,
        gateway_refund_id: str | None = None,
    ):
        """Update refund status after gateway response."""
        from app.models.models import Refund

        values = {"status": status}
        if gateway_refund_id:
            values["gateway_refund_id"] = gateway_refund_id
        if status == "completed":
            values["completed_at"] = datetime.now(timezone.utc)

        await self.db.execute(
            update(Refund)
            .where(Refund.id == refund_id)
            .values(**values)
        )

    # ────────────────────────────────────────────────
    # ORDER STATUS HISTORY
    # ────────────────────────────────────────────────

    async def add_status_history(
        self,
        order_id: UUID,
        from_status: str | None,
        to_status: str,
        changed_by: UUID | None = None,
        reason: str | None = None,
    ):
        """Record an order status transition in the audit trail."""
        from app.models.models import OrderStatusHistory

        entry = OrderStatusHistory(
            order_id=order_id,
            from_status=from_status,
            to_status=to_status,
            changed_by=changed_by,
            change_reason=reason,
        )
        self.db.add(entry)
        await self.db.flush()
        return entry

    # ────────────────────────────────────────────────
    # USER LOOKUP (for prefill)
    # ────────────────────────────────────────────────

    async def get_user(self, user_id: UUID):
        """Fetch user by ID."""
        from app.models.models import User

        result = await self.db.execute(
            select(User).where(User.id == user_id)
        )
        return result.scalar_one_or_none()
