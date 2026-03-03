"""
FX Rate Service — Daily exchange rate sync and caching.

Uses Open Exchange Rates API (free tier: 1000 requests/month).
Caches rates in Redis with configurable TTL.
"""

import json
import logging
from datetime import datetime, timezone
from decimal import Decimal

import httpx

from app.core.payment_config import get_payment_settings

logger = logging.getLogger(__name__)

settings = get_payment_settings()

_rate_cache: dict[str, dict] = {}


class FXRateService:
    """Fetches, caches, and provides exchange rates."""

    OPEN_EXCHANGE_URL = "https://openexchangerates.org/api/latest.json"

    def __init__(self, redis_client=None):
        self.redis = redis_client

    async def fetch_rates_from_api(self) -> dict[str, float]:
        """Fetch latest rates from Open Exchange Rates (base USD)."""
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
        """Fetch rates and store in cache. Called by daily cron."""
        try:
            rates = await self.fetch_rates_from_api()
        except Exception as e:
            logger.error("FX rate fetch failed: %s — using cached/fallback", str(e))
            rates = await self._get_cached_rates()
            if not rates:
                rates = self._fallback_rates()
            return rates

        cache_payload = {
            "rates": rates,
            "fetched_at": datetime.now(timezone.utc).isoformat(),
            "source": "openexchangerates",
        }

        if self.redis:
            try:
                await self.redis.set(
                    "fx_rates:latest",
                    json.dumps(cache_payload),
                    ex=settings.FX_RATE_CACHE_TTL_SECONDS,
                )
            except Exception as e:
                logger.warning("Redis FX cache write failed: %s", str(e))

        _rate_cache["latest"] = cache_payload
        logger.info("FX rates synced: %d currencies", len(rates))
        return rates

    async def get_rate(
        self, from_currency: str, to_currency: str,
    ) -> tuple[Decimal, str, datetime]:
        """
        Get exchange rate between two currencies.
        Returns: (rate, source, fetched_at)
        """
        if from_currency.upper() == to_currency.upper():
            return Decimal("1.0"), "identity", datetime.now(timezone.utc)

        cached = await self._get_cached_rates()
        if not cached:
            await self.sync_rates()
            cached = await self._get_cached_rates()

        if not cached:
            raise RuntimeError("Unable to fetch FX rates")

        rates = cached["rates"]
        source = cached.get("source", "openexchangerates")
        fetched_at = datetime.fromisoformat(cached["fetched_at"])

        from_rate = Decimal(str(rates.get(from_currency.upper(), 1)))
        to_rate = Decimal(str(rates.get(to_currency.upper(), 1)))

        if from_rate == 0:
            raise ValueError(f"No rate found for {from_currency}")

        rate = to_rate / from_rate
        return rate, source, fetched_at

    async def lock_rate_for_checkout(
        self, base_currency: str, target_currency: str,
    ) -> dict:
        """Lock an FX rate for a checkout session."""
        rate, source, fetched_at = await self.get_rate(base_currency, target_currency)
        return {
            "rate": rate,
            "source": source,
            "fetched_at": fetched_at,
            "base_currency": base_currency,
            "target_currency": target_currency,
        }

    async def _get_cached_rates(self) -> dict | None:
        if self.redis:
            try:
                data = await self.redis.get("fx_rates:latest")
                if data:
                    return json.loads(data)
            except Exception:
                pass
        return _rate_cache.get("latest")

    @staticmethod
    def _fallback_rates() -> dict[str, float]:
        """Hardcoded fallback (approximate). Used only when API + cache both fail."""
        return {
            "USD": 1.0, "INR": 83.50, "EUR": 0.92, "GBP": 0.79,
            "AUD": 1.53, "CAD": 1.36, "JPY": 150.0, "SGD": 1.34, "AED": 3.67,
        }


def get_fx_service(redis_client=None) -> FXRateService:
    return FXRateService(redis_client=redis_client)
