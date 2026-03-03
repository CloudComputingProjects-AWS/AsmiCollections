"""
Shipping Service — Shipment management and courier integration.
Phase 10 — V2.5 Blueprint

Integrates with:
  - Shiprocket / Delhivery (India)
  - FedEx / DHL (Global)

Currently implements the local DB management layer.
Courier API calls are stubbed for easy integration.
"""

import logging
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.models import Order, Shipment

logger = logging.getLogger(__name__)


class ShippingServiceError(Exception):
    def __init__(self, message: str, status_code: int = 400):
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class ShippingService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_shipment(
        self,
        order_id: UUID,
        courier_partner: str,
        tracking_number: str | None = None,
        awb_number: str | None = None,
        weight_grams: int | None = None,
        estimated_delivery=None,
    ) -> Shipment:
        """Create a shipment record for an order."""
        # Verify order exists and is in correct state
        result = await self.db.execute(
            select(Order).where(Order.id == order_id)
        )
        order = result.scalar_one_or_none()
        if not order:
            raise ShippingServiceError("Order not found", 404)

        if order.order_status not in ("processing", "confirmed"):
            raise ShippingServiceError(
                f"Cannot create shipment for order in '{order.order_status}' state. "
                "Order must be in 'processing' or 'confirmed' state."
            )

        # Check existing shipment
        existing = await self.db.execute(
            select(Shipment).where(Shipment.order_id == order_id)
        )
        if existing.scalar_one_or_none():
            raise ShippingServiceError("Shipment already exists for this order")

        # Create via courier API (stubbed)
        courier_response = await self._create_courier_shipment(
            order, courier_partner, weight_grams
        )

        shipment = Shipment(
            order_id=order_id,
            courier_partner=courier_partner,
            tracking_number=tracking_number or courier_response.get("tracking_number"),
            awb_number=awb_number or courier_response.get("awb_number"),
            status="created",
            estimated_delivery=estimated_delivery,
            weight_grams=weight_grams,
            shipping_label_url=courier_response.get("label_url"),
            tracking_url=courier_response.get("tracking_url"),
        )
        self.db.add(shipment)
        await self.db.flush()

        logger.info(f"Shipment created for order {order.order_number}: {courier_partner}")
        return shipment

    async def update_shipment(
        self,
        shipment_id: UUID,
        **kwargs,
    ) -> Shipment:
        """Update shipment details (tracking, status, etc.)."""
        result = await self.db.execute(
            select(Shipment).where(Shipment.id == shipment_id)
        )
        shipment = result.scalar_one_or_none()
        if not shipment:
            raise ShippingServiceError("Shipment not found", 404)

        for key, value in kwargs.items():
            if value is not None and hasattr(shipment, key):
                setattr(shipment, key, value)

        shipment.updated_at = datetime.now(timezone.utc)
        await self.db.flush()
        return shipment

    async def mark_shipped(self, shipment_id: UUID) -> Shipment:
        """Mark shipment as picked up / in transit."""
        result = await self.db.execute(
            select(Shipment).where(Shipment.id == shipment_id)
        )
        shipment = result.scalar_one_or_none()
        if not shipment:
            raise ShippingServiceError("Shipment not found", 404)

        shipment.status = "in_transit"
        shipment.shipped_at = datetime.now(timezone.utc)
        shipment.updated_at = datetime.now(timezone.utc)
        await self.db.flush()
        return shipment

    async def mark_delivered(self, shipment_id: UUID) -> Shipment:
        """Mark shipment as delivered."""
        result = await self.db.execute(
            select(Shipment).where(Shipment.id == shipment_id)
        )
        shipment = result.scalar_one_or_none()
        if not shipment:
            raise ShippingServiceError("Shipment not found", 404)

        shipment.status = "delivered"
        shipment.delivered_at = datetime.now(timezone.utc)
        shipment.updated_at = datetime.now(timezone.utc)
        await self.db.flush()
        return shipment

    async def get_shipment_by_order(self, order_id: UUID) -> Shipment | None:
        """Get shipment for an order."""
        result = await self.db.execute(
            select(Shipment).where(Shipment.order_id == order_id)
        )
        return result.scalar_one_or_none()

    async def list_shipments(
        self,
        page: int = 1,
        page_size: int = 20,
        status: str | None = None,
        courier: str | None = None,
    ) -> tuple[list[Shipment], int]:
        """List shipments with filtering."""
        query = select(Shipment)
        count_query = select(func.count(Shipment.id))

        conditions = []
        if status:
            conditions.append(Shipment.status == status)
        if courier:
            conditions.append(Shipment.courier_partner == courier)

        if conditions:
            query = query.where(and_(*conditions))
            count_query = count_query.where(and_(*conditions))

        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0

        offset = (page - 1) * page_size
        query = query.order_by(Shipment.created_at.desc()).offset(offset).limit(page_size)

        result = await self.db.execute(query)
        shipments = result.scalars().all()
        return shipments, total

    # ──────────────── Courier API Stubs ────────────────

    async def _create_courier_shipment(
        self, order: Order, courier: str, weight_grams: int | None
    ) -> dict:
        """
        Stub: Create shipment via courier API.
        Replace with actual Shiprocket/Delhivery/FedEx/DHL integration.
        """
        logger.info(f"[STUB] Creating {courier} shipment for {order.order_number}")

        if courier.lower() in ("shiprocket", "delhivery"):
            return await self._shiprocket_create(order, weight_grams)
        elif courier.lower() in ("fedex", "dhl"):
            return await self._fedex_create(order, weight_grams)
        else:
            return {"tracking_number": None, "awb_number": None}

    async def _shiprocket_create(self, order: Order, weight_grams: int | None) -> dict:
        """
        Stub: Shiprocket API integration.
        POST https://apiv2.shiprocket.in/v1/external/orders/create/adhoc
        """
        # TODO: Implement actual API call
        # import httpx
        # async with httpx.AsyncClient() as client:
        #     response = await client.post(
        #         "https://apiv2.shiprocket.in/v1/external/orders/create/adhoc",
        #         headers={"Authorization": f"Bearer {SHIPROCKET_TOKEN}"},
        #         json={...}
        #     )
        logger.info(f"[STUB] Shiprocket shipment for order {order.order_number}")
        return {
            "tracking_number": None,
            "awb_number": None,
            "label_url": None,
            "tracking_url": None,
        }

    async def _fedex_create(self, order: Order, weight_grams: int | None) -> dict:
        """Stub: FedEx/DHL API integration."""
        logger.info(f"[STUB] FedEx shipment for order {order.order_number}")
        return {
            "tracking_number": None,
            "awb_number": None,
            "label_url": None,
            "tracking_url": None,
        }

    async def sync_tracking_status(self, shipment_id: UUID) -> Shipment:
        """
        Stub: Poll courier API for tracking updates.
        Called by background job every 30 minutes.
        """
        result = await self.db.execute(
            select(Shipment).where(Shipment.id == shipment_id)
        )
        shipment = result.scalar_one_or_none()
        if not shipment:
            raise ShippingServiceError("Shipment not found", 404)

        # TODO: Call courier tracking API based on shipment.courier_partner
        # Update shipment.status, estimated_delivery, etc.
        logger.info(f"[STUB] Syncing tracking for {shipment.tracking_number}")
        return shipment
