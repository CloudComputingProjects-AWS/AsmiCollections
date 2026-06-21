"""
FX Rate Sync - background job for daily exchange rate refresh.
Schedule: Daily at 00:00 UTC

Usage:
  Standalone:  python -m app.jobs.fx_rate_sync
  APScheduler: scheduler.add_job(sync_fx_rates, 'cron', hour=0, minute=0)
"""

import asyncio
import logging
from datetime import datetime, timezone

from app.core.database import async_session_factory
from app.services.fx_rate_service import get_fx_service

logger = logging.getLogger(__name__)


async def sync_fx_rates():
    """Fetch latest FX rates and cache them in Postgres."""
    logger.info("FX rate sync started at %s", datetime.now(timezone.utc).isoformat())
    async with async_session_factory() as db:
        fx_service = get_fx_service(db)
        try:
            rates = await fx_service.sync_rates()
            await db.commit()
            logger.info("FX rate sync completed: %d currencies updated", len(rates))
            return rates
        except Exception as exc:
            await db.rollback()
            logger.error("FX rate sync FAILED: %s", str(exc))
            raise


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(sync_fx_rates())
