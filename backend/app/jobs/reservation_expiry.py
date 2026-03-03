"""
Reservation Expiry Job — Release expired stock reservations.
Schedule: Every 60 seconds

When a user initiates checkout, stock is reserved for 10 minutes.
If payment is not completed, this job releases the reservation
and restores the stock_quantity on the product_variant.
"""

import asyncio
import logging
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import async_session_factory

logger = logging.getLogger(__name__)


async def release_expired_reservations():
    """Find all held reservations past their expiry and release them."""
    async with async_session_factory() as db:
        try:
            from app.models.models import InventoryReservation, ProductVariant

            now = datetime.now(timezone.utc)

            result = await db.execute(
                select(InventoryReservation).where(
                    InventoryReservation.status == "held",
                    InventoryReservation.expires_at < now,
                )
            )
            expired = result.scalars().all()

            if not expired:
                return 0

            released_count = 0
            for reservation in expired:
                variant_result = await db.execute(
                    select(ProductVariant)
                    .where(ProductVariant.id == reservation.variant_id)
                    .with_for_update()
                )
                variant = variant_result.scalar_one_or_none()
                if variant:
                    variant.stock_quantity += reservation.reserved_qty

                reservation.status = "released"
                released_count += 1

            await db.commit()

            if released_count > 0:
                logger.info("Released %d expired reservations, stock restored", released_count)
            return released_count

        except Exception as e:
            await db.rollback()
            logger.error("Reservation release job failed: %s", str(e))
            raise


async def run_periodic(interval_seconds: int = 60):
    """Run the reservation release job periodically as a background task."""
    logger.info("Reservation expiry job started (interval: %ds)", interval_seconds)
    while True:
        try:
            await release_expired_reservations()
        except Exception as e:
            logger.error("Reservation job error: %s", str(e))
        await asyncio.sleep(interval_seconds)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(run_periodic())
