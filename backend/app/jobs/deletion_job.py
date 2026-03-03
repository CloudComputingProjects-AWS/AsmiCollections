"""
Account Deletion Background Job — Phase 12.

Runs daily to process accounts whose 30-day grace period has expired.
Anonymizes user data per DPDP/GDPR requirements.

Register in app startup or scheduler (e.g., APScheduler, BullMQ equivalent).
"""

from __future__ import annotations

import asyncio
import logging
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import async_session_factory
from app.services.privacy_service import PrivacyService

logger = logging.getLogger(__name__)


async def run_deletion_processor() -> int:
    """
    Process all expired account deletion requests.

    Returns the number of accounts anonymized.
    Called by scheduler — creates its own DB session.
    """
    logger.info("Starting account deletion processor...")
    async with async_session_factory() as db:
        service = PrivacyService(db)
        try:
            count = await service.process_expired_deletions()
            logger.info("Account deletion processor complete: %d processed", count)
            return count
        except Exception:
            logger.exception("Account deletion processor failed")
            await db.rollback()
            return 0


async def schedule_deletion_processor(interval_hours: int = 24):
    """
    Simple async loop scheduler for deletion processing.
    Runs every `interval_hours` hours.

    For production, replace with APScheduler or Celery beat.
    """
    while True:
        try:
            await run_deletion_processor()
        except Exception:
            logger.exception("Deletion processor scheduler error")
        await asyncio.sleep(interval_hours * 3600)
