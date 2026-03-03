"""
Returns & Refunds Service — Full lifecycle management.
Phase 10 — V2.5 Blueprint

Handles:
  - Customer return requests
  - Admin approve/reject returns
  - Admin mark return received → restock
  - Refund initiation via Razorpay/Stripe
  - Credit note auto-generation on refund
  - Order state machine transitions for return flow
"""

import logging
from datetime import datetime, timezone
from decimal import Decimal
from uuid import UUID

from sqlalchemy import and_, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.models import (
    CreditNote,
    Invoice,
    Order,
    OrderItem,
    OrderStatusHistory,
    ProductVariant,
    Refund,
    Return,
    User,
)
from app.services.order_state_machine import can_transition, ORDER_TRANSITIONS

logger = logging.getLogger(__name__)


class ReturnServiceError(Exception):
    def __init__(self, message: str, status_code: int = 400):
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class ReturnService:
    def __init__(self, db: AsyncSession):
        self.db = db

    # ──────────────── Customer: Request Return ────────────────

    async def request_return(
        self,
        user_id: UUID,
        order_id: UUID,
        order_item_id: UUID,
        reason: str,
        reason_detail: str | None,
        return_type: str,
        quantity: int,
    ) -> Return:
        """Customer requests a return/exchange for a delivered order item."""
        # 1. Verify order exists and belongs to user
        result = await self.db.execute(
            select(Order).where(
                and_(Order.id == order_id, Order.user_id == user_id)
            )
        )
        order = result.scalar_one_or_none()
        if not order:
            raise ReturnServiceError("Order not found", 404)

        if order.order_status != "delivered":
            raise ReturnServiceError(
                "Returns can only be requested for delivered orders"
            )

        # 2. Verify order item
        result = await self.db.execute(
            select(OrderItem).where(
                and_(
                    OrderItem.id == order_item_id,
                    OrderItem.order_id == order_id,
                )
            )
        )
        order_item = result.scalar_one_or_none()
        if not order_item:
            raise ReturnServiceError("Order item not found", 404)

        if quantity > order_item.quantity:
            raise ReturnServiceError(
                f"Return quantity ({quantity}) exceeds ordered quantity ({order_item.quantity})"
            )

        # 3. Check for existing return on this item
        existing = await self.db.execute(
            select(Return).where(
                and_(
                    Return.order_item_id == order_item_id,
                    Return.status.notin_(["rejected"]),
                )
            )
        )
        if existing.scalar_one_or_none():
            raise ReturnServiceError("A return request already exists for this item")

        # 4. Create return request
        return_req = Return(
            order_id=order_id,
            order_item_id=order_item_id,
            user_id=user_id,
            reason=reason,
            reason_detail=reason_detail,
            return_type=return_type,
            status="requested",
            quantity=quantity,
        )
        self.db.add(return_req)
        await self.db.flush()

        # 5. Transition order status
        await self._transition_order(order, "return_requested", user_id)

        logger.info(
            f"Return requested: order={order.order_number}, "
            f"item={order_item.sku_snapshot}, qty={quantity}"
        )
        return return_req

    # ──────────────── Admin: Approve / Reject ────────────────

    async def approve_return(
        self,
        return_id: UUID,
        admin_id: UUID,
        admin_notes: str | None = None,
        pickup_date=None,
    ) -> Return:
        """Admin approves a return request."""
        return_req = await self._get_return(return_id)

        if return_req.status != "requested":
            raise ReturnServiceError(
                f"Cannot approve return in '{return_req.status}' status"
            )

        return_req.status = "approved"
        return_req.approved_by = admin_id
        return_req.admin_notes = admin_notes
        return_req.pickup_date = pickup_date
        return_req.updated_at = datetime.now(timezone.utc)
        await self.db.flush()

        # Transition order
        order = await self._get_order(return_req.order_id)
        await self._transition_order(order, "return_approved", admin_id)

        logger.info(f"Return {return_id} approved by admin {admin_id}")
        return return_req

    async def reject_return(
        self,
        return_id: UUID,
        admin_id: UUID,
        admin_notes: str | None = None,
    ) -> Return:
        """Admin rejects a return request."""
        return_req = await self._get_return(return_id)

        if return_req.status != "requested":
            raise ReturnServiceError(
                f"Cannot reject return in '{return_req.status}' status"
            )

        return_req.status = "rejected"
        return_req.approved_by = admin_id
        return_req.admin_notes = admin_notes
        return_req.updated_at = datetime.now(timezone.utc)
        await self.db.flush()

        # Transition order
        order = await self._get_order(return_req.order_id)
        await self._transition_order(order, "return_rejected", admin_id)

        logger.info(f"Return {return_id} rejected by admin {admin_id}")
        return return_req

    # ──────────────── Admin: Receive Return ────────────────

    async def receive_return(
        self,
        return_id: UUID,
        admin_id: UUID,
        admin_notes: str | None = None,
    ) -> Return:
        """Admin marks return as received. Triggers restock."""
        return_req = await self._get_return(return_id)

        if return_req.status != "approved":
            raise ReturnServiceError(
                f"Cannot receive return in '{return_req.status}' status"
            )

        return_req.status = "received"
        return_req.received_at = datetime.now(timezone.utc)
        if admin_notes:
            return_req.admin_notes = admin_notes
        return_req.updated_at = datetime.now(timezone.utc)
        await self.db.flush()

        # Restock the variant
        await self._restock_variant(return_req.order_item_id, return_req.quantity)

        # Transition order
        order = await self._get_order(return_req.order_id)
        await self._transition_order(order, "return_received", admin_id)

        logger.info(f"Return {return_id} received, stock restored")
        return return_req

    # ──────────────── Restock ────────────────

    async def _restock_variant(self, order_item_id: UUID, quantity: int):
        """Restore stock to the product variant."""
        result = await self.db.execute(
            select(OrderItem).where(OrderItem.id == order_item_id)
        )
        order_item = result.scalar_one_or_none()
        if not order_item or not order_item.product_variant_id:
            logger.warning(f"Cannot restock: variant not found for item {order_item_id}")
            return

        await self.db.execute(
            update(ProductVariant)
            .where(ProductVariant.id == order_item.product_variant_id)
            .values(stock_quantity=ProductVariant.stock_quantity + quantity)
        )
        logger.info(
            f"Restocked variant {order_item.product_variant_id}: +{quantity}"
        )

    # ──────────────── Refund ────────────────

    async def initiate_refund(
        self,
        order_id: UUID,
        amount: Decimal,
        admin_id: UUID,
        return_id: UUID | None = None,
        refund_method: str = "original",
        reason: str = "Customer return",
    ) -> Refund:
        """
        Initiate refund via payment gateway.
        Auto-generates credit note after successful refund.
        """
        order = await self._get_order(order_id)

        if amount > order.grand_total:
            raise ReturnServiceError(
                f"Refund amount ({amount}) exceeds order total ({order.grand_total})"
            )

        # Create refund record
        refund = Refund(
            return_id=return_id,
            order_id=order_id,
            amount=amount,
            currency=order.currency or "INR",
            status="initiated",
            refund_method=refund_method,
            initiated_by=admin_id,
        )
        self.db.add(refund)
        await self.db.flush()

        # Process via payment gateway
        gateway_refund_id = await self._process_gateway_refund(order, amount)
        if gateway_refund_id:
            refund.gateway_refund_id = gateway_refund_id
            refund.status = "processed"
            refund.completed_at = datetime.now(timezone.utc)
        else:
            refund.status = "pending"
            logger.warning(f"Gateway refund pending for order {order.order_number}")

        await self.db.flush()

        # Auto-generate credit note
        try:
            await self._generate_credit_note(order, refund, reason)
        except Exception as e:
            logger.error(f"Credit note generation failed: {e}")

        # Transition order to refunded
        await self._transition_order(order, "refunded", admin_id)

        logger.info(
            f"Refund {refund.id} initiated: {amount} {order.currency} "
            f"for order {order.order_number}"
        )
        return refund

    async def _process_gateway_refund(
        self, order: Order, amount: Decimal
    ) -> str | None:
        """
        Process refund through the original payment gateway.
        Returns gateway_refund_id or None.
        """
        gateway = order.payment_gateway

        if gateway == "razorpay" and order.payment_gateway_txn_id:
            return await self._razorpay_refund(
                order.payment_gateway_txn_id, amount, order.currency or "INR"
            )
        elif gateway == "stripe" and order.payment_gateway_txn_id:
            return await self._stripe_refund(
                order.payment_gateway_txn_id, amount, order.currency or "INR"
            )
        else:
            logger.warning(f"No gateway configured for order {order.order_number}")
            return None

    async def _razorpay_refund(
        self, payment_id: str, amount: Decimal, currency: str
    ) -> str | None:
        """Refund via Razorpay API."""
        try:
            from app.services.gateways.razorpay_client import razorpay_client

            if razorpay_client is None:
                logger.warning("[STUB] Razorpay client not configured")
                return None

            # Razorpay expects amount in paise
            amount_paise = int(amount * 100)
            refund = razorpay_client.payment.refund(
                payment_id,
                {"amount": amount_paise},
            )
            logger.info(f"Razorpay refund: {refund.get('id')}")
            return refund.get("id")
        except Exception as e:
            logger.error(f"Razorpay refund failed: {e}")
            return None

    async def _stripe_refund(
        self, payment_intent_id: str, amount: Decimal, currency: str
    ) -> str | None:
        """Refund via Stripe API."""
        try:
            import stripe
            import os

            stripe.api_key = os.getenv("STRIPE_SECRET_KEY", "")
            if not stripe.api_key:
                logger.warning("[STUB] Stripe key not configured")
                return None

            # Stripe expects amount in smallest unit
            amount_cents = int(amount * 100)
            refund = stripe.Refund.create(
                payment_intent=payment_intent_id,
                amount=amount_cents,
            )
            logger.info(f"Stripe refund: {refund.id}")
            return refund.id
        except Exception as e:
            logger.error(f"Stripe refund failed: {e}")
            return None

    # ──────────────── Credit Note Auto-Generation ────────────────

    async def _generate_credit_note(
        self, order: Order, refund: Refund, reason: str
    ):
        """Auto-generate credit note on refund using Invoice Service."""
        from app.services.invoice_service import InvoiceService

        inv_service = InvoiceService(self.db)

        # Find the original invoice
        invoice = await inv_service.get_invoice_by_order(order.id)
        if not invoice:
            logger.warning(f"No invoice found for order {order.order_number}, skipping CN")
            return

        # Calculate tax components proportionally
        if order.grand_total > 0:
            ratio = refund.amount / order.grand_total
        else:
            ratio = Decimal("1")

        subtotal = (order.subtotal * ratio).quantize(Decimal("0.01"))
        cgst = ((order.cgst_amount or Decimal("0")) * ratio).quantize(Decimal("0.01"))
        sgst = ((order.sgst_amount or Decimal("0")) * ratio).quantize(Decimal("0.01"))
        igst = ((order.igst_amount or Decimal("0")) * ratio).quantize(Decimal("0.01"))

        await inv_service.generate_credit_note(
            invoice_id=invoice.id,
            reason=reason,
            subtotal=subtotal,
            cgst_amount=cgst,
            sgst_amount=sgst,
            igst_amount=igst,
            return_id=refund.return_id,
            refund_id=refund.id,
        )

    # ──────────────── Listings ────────────────

    async def list_returns(
        self,
        page: int = 1,
        page_size: int = 20,
        status: str | None = None,
        user_id: UUID | None = None,
    ) -> tuple[list[Return], int]:
        """List returns with filters."""
        query = select(Return)
        count_query = select(func.count(Return.id))

        conditions = []
        if status:
            conditions.append(Return.status == status)
        if user_id:
            conditions.append(Return.user_id == user_id)

        if conditions:
            query = query.where(and_(*conditions))
            count_query = count_query.where(and_(*conditions))

        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0

        offset = (page - 1) * page_size
        query = query.order_by(Return.created_at.desc()).offset(offset).limit(page_size)

        result = await self.db.execute(query)
        returns = result.scalars().all()
        return returns, total

    async def list_refunds(
        self,
        page: int = 1,
        page_size: int = 20,
        status: str | None = None,
        order_id: UUID | None = None,
    ) -> tuple[list[Refund], int]:
        """List refunds with filters."""
        query = select(Refund)
        count_query = select(func.count(Refund.id))

        conditions = []
        if status:
            conditions.append(Refund.status == status)
        if order_id:
            conditions.append(Refund.order_id == order_id)

        if conditions:
            query = query.where(and_(*conditions))
            count_query = count_query.where(and_(*conditions))

        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0

        offset = (page - 1) * page_size
        query = query.order_by(Refund.created_at.desc()).offset(offset).limit(page_size)

        result = await self.db.execute(query)
        refunds = result.scalars().all()
        return refunds, total

    async def get_return(self, return_id: UUID) -> Return:
        """Get a single return request."""
        return await self._get_return(return_id)

    # ──────────────── Helpers ────────────────

    async def _get_return(self, return_id: UUID) -> Return:
        result = await self.db.execute(
            select(Return).where(Return.id == return_id)
        )
        return_req = result.scalar_one_or_none()
        if not return_req:
            raise ReturnServiceError("Return not found", 404)
        return return_req

    async def _get_order(self, order_id: UUID) -> Order:
        result = await self.db.execute(
            select(Order).where(Order.id == order_id)
        )
        order = result.scalar_one_or_none()
        if not order:
            raise ReturnServiceError("Order not found", 404)
        return order

    async def _transition_order(
        self, order: Order, new_status: str, changed_by: UUID
    ):
        """Transition order status via state machine."""
        if not can_transition(order.order_status, new_status):
            logger.warning(
                f"Cannot transition order {order.order_number}: "
                f"{order.order_status} → {new_status}"
            )
            return

        old_status = order.order_status
        order.order_status = new_status
        order.updated_at = datetime.now(timezone.utc)

        # Record in history
        history = OrderStatusHistory(
            order_id=order.id,
            from_status=old_status,
            to_status=new_status,
            changed_by=changed_by,
            change_reason=f"Return flow: {new_status}",
        )
        self.db.add(history)
        await self.db.flush()
