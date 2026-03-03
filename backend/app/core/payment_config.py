"""
Payment gateway configuration for Razorpay (India) and Stripe (Global).

Environment variables required:
  RAZORPAY_KEY_ID        - Razorpay API key id
  RAZORPAY_KEY_SECRET    - Razorpay API key secret
  RAZORPAY_WEBHOOK_SECRET - Razorpay webhook secret
  STRIPE_SECRET_KEY      - Stripe secret key
  STRIPE_PUBLISHABLE_KEY - Stripe publishable key
  STRIPE_WEBHOOK_SECRET  - Stripe webhook endpoint secret
  OPEN_EXCHANGE_RATES_APP_ID - For FX rate sync
  BASE_CURRENCY          - Default: INR
"""

from functools import lru_cache

from pydantic_settings import BaseSettings


class PaymentSettings(BaseSettings):
    """Payment-specific settings, loaded from environment."""

    # ── Razorpay (India) ──
    RAZORPAY_KEY_ID: str = ""
    RAZORPAY_KEY_SECRET: str = ""
    RAZORPAY_WEBHOOK_SECRET: str = ""

    # ── Stripe (Global) ──
    STRIPE_SECRET_KEY: str = ""
    STRIPE_PUBLISHABLE_KEY: str = ""
    STRIPE_WEBHOOK_SECRET: str = ""

    # ── Currency & FX ──
    BASE_CURRENCY: str = "INR"
    OPEN_EXCHANGE_RATES_APP_ID: str = ""
    FX_RATE_CACHE_TTL_SECONDS: int = 86400  # 24 hours

    # ── Payment behaviour ──
    RESERVATION_EXPIRY_MINUTES: int = 10
    PAYMENT_RETRY_MAX: int = 3

    # ── Supported payment methods by country ──
    INDIA_METHODS: list[str] = [
        "upi", "netbanking", "debit_card", "credit_card"
    ]
    GLOBAL_METHODS: list[str] = [
        "credit_card", "debit_card", "apple_pay", "google_pay"
    ]

    class Config:
        env_file = ".env"
        extra = "ignore"


@lru_cache()
def get_payment_settings() -> PaymentSettings:
    return PaymentSettings()
