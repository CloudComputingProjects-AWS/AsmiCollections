"""
FX Rate Service - daily exchange rate sync and Postgres-backed caching.

Uses Open Exchange Rates API when configured. Stores shared cache snapshots in
the fx_rates table so local and AWS environments use Postgres as the only
application datastore.
"""

import logging
from datetime import datetime, timedelta, timezone
from decimal import Decimal

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.payment_config import get_payment_settings
from app.models.models import FXRate

logger = logging.getLogger(__name__)

settings = get_payment_settings()


class FXRateService:
    """Fetches, stores, and provides exchange rates from Postgres."""

    OPEN_EXCHANGE_URL = "https://openexchangerates.org/api/latest.json"
    API_BASE_CURRENCY = "USD"

    def __init__(self, db: AsyncSession):
        self.db = db

    async def fetch_rates_from_api(self) -> dict[str, float]:
        """Fetch latest rates from Open Exchange Rates, whose free API is USD based."""
        if not settings.OPEN_EXCHANGE_RATES_APP_ID:
            logger.warning("OPEN_EXCHANGE_RATES_APP_ID not set, using fallback rates")
            return self._fallback_rates()

        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(
                self.OPEN_EXCHANGE_URL,
                params={"app_id": settings.OPEN_EXCHANGE_RATES_APP_ID},
            )
            resp.raise_for_status()
            data = resp.json()
            return data.get("rates", {})

    async def sync_rates(self) -> dict[str, float]:
        """Fetch rates and store a shared cache snapshot in Postgres."""
        source = "openexchangerates"
        try:
            rates = await self.fetch_rates_from_api()
        except Exception as exc:
            logger.error("FX rate fetch failed: %s - using cached/fallback", str(exc))
            cached = await self._get_cached_rates(include_expired=True)
            if cached:
                return cached["rates"]
            rates = self._fallback_rates()
            source = "fallback"
        else:
            if not settings.OPEN_EXCHANGE_RATES_APP_ID:
                source = "fallback"

        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(seconds=settings.FX_RATE_CACHE_TTL_SECONDS)

        self.db.add(
            FXRate(
                base_currency=self.API_BASE_CURRENCY,
                rates=rates,
                source=source,
                fetched_at=now,
                expires_at=expires_at,
                created_at=now,
            )
        )
        await self.db.flush()

        logger.info("FX rates synced: %d currencies", len(rates))
        return rates

    async def get_rate(
        self, from_currency: str, to_currency: str,
    ) -> tuple[Decimal, str, datetime, datetime]:
        """
        Get exchange rate between two currencies.
        Returns: (rate, source, fetched_at, expires_at).
        """
        from_currency = from_currency.upper()
        to_currency = to_currency.upper()

        if from_currency == to_currency:
            now = datetime.now(timezone.utc)
            return Decimal("1.0"), "identity", now, now

        cached = await self._get_cached_rates()
        if not cached:
            await self.sync_rates()
            cached = await self._get_cached_rates()

        if not cached:
            raise RuntimeError("Unable to fetch FX rates")

        rates = cached["rates"]
        source = cached["source"]
        fetched_at = cached["fetched_at"]
        expires_at = cached["expires_at"]

        from_rate = Decimal(str(rates.get(from_currency, 1)))
        to_rate = Decimal(str(rates.get(to_currency, 1)))

        if from_rate == 0:
            raise ValueError(f"No rate found for {from_currency}")

        rate = to_rate / from_rate
        return rate, source, fetched_at, expires_at

    async def lock_rate_for_checkout(
        self, base_currency: str, target_currency: str,
    ) -> dict:
        """Lock an FX rate for a checkout session."""
        rate, source, fetched_at, expires_at = await self.get_rate(
            base_currency,
            target_currency,
        )
        return {
            "rate": rate,
            "source": source,
            "fetched_at": fetched_at,
            "expires_at": expires_at,
            "base_currency": base_currency,
            "target_currency": target_currency,
        }

    async def _get_cached_rates(self, include_expired: bool = False) -> dict | None:
        now = datetime.now(timezone.utc)
        stmt = (
            select(FXRate)
            .where(FXRate.base_currency == self.API_BASE_CURRENCY)
            .order_by(FXRate.fetched_at.desc())
            .limit(1)
        )

        if not include_expired:
            stmt = stmt.where(FXRate.expires_at > now)

        result = await self.db.execute(stmt)
        row = result.scalar_one_or_none()
        if not row:
            return None

        return {
            "rates": row.rates,
            "source": row.source,
            "fetched_at": row.fetched_at,
            "expires_at": row.expires_at,
        }

    @staticmethod
    def _fallback_rates() -> dict[str, float]:
        """Hardcoded fallback used only when API and Postgres cache are unavailable."""
        return {
            "USD": 1.0,
            "INR": 83.50,
            "EUR": 0.92,
            "GBP": 0.79,
            "AUD": 1.53,
            "CAD": 1.36,
            "JPY": 150.0,
            "SGD": 1.34,
            "AED": 3.67,
        }


def get_fx_service(db: AsyncSession) -> FXRateService:
    return FXRateService(db=db)
