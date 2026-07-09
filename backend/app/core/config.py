"""
Application configuration via environment variables.
Uses pydantic-settings for validation and type coercion.

S20 Audit (05-Mar-2026) — 3 confirmed orphaned settings removed:
  DEFAULT_CURRENCY       — never referenced anywhere in codebase
  STOCK_RESERVATION_MINUTES — never referenced anywhere in codebase
  S3_BUCKET_INVOICES     — never referenced anywhere in codebase
All other settings verified active via full codebase search.
"""

from functools import lru_cache
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # ────────────────── Application ──────────────────
    APP_NAME: str = ""
    APP_VERSION: str = ""
    DEBUG: bool = False
    ENVIRONMENT: str = ""
    FRONTEND_URL: str = "http://localhost:3000"

    # ────────────────── Database (PostgreSQL) ──────────────────
    DATABASE_URL: str = ""
    DATABASE_URL_SYNC: str = ""
    DB_POOL_SIZE: int = 20
    DB_MAX_OVERFLOW: int = 10
    DB_ECHO: bool = False

    # ────────────────── Auth / JWT ──────────────────
    SECRET_KEY: str 
    JWT_ALGORITHM: str = ""
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

      # ────────────────── Auth Image callback ──────────────────
    IMAGE_CALLBACK_SECRET: str = ""

    # ────────────────── Password Hashing ──────────────────
    BCRYPT_ROUNDS: int = 12

    # ────────────────── AWS ──────────────────
    # AWS_REGION: auto-injected by Lambda runtime
    # S3_BUCKET_NAME: defined in Lambda env vars
    # CLOUDFRONT_DOMAIN: read via os.getenv() in pdf_generator.py

    # ────────────────── Payment Gateways ──────────────────
    RAZORPAY_KEY_ID: str = ""
    RAZORPAY_KEY_SECRET: str = ""
    RAZORPAY_WEBHOOK_SECRET: str = ""
    STRIPE_SECRET_KEY: str = ""
    STRIPE_PUBLISHABLE_KEY: str = ""
    STRIPE_WEBHOOK_SECRET: str = ""

    # ────────────────── FX Rates ──────────────────
    # Note: BASE_CURRENCY, RESERVATION_EXPIRY_MINUTES, PAYMENT_RETRY_MAX
    # are defined in payment_config.py (PaymentSettings class) — not here.
    OPEN_EXCHANGE_RATES_APP_ID: str = ""
    FX_RATE_CACHE_TTL_SECONDS: int = 86400

    # ────────────────── Email ──────────────────
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    FROM_EMAIL: str = ""

    # ────────────────── Encryption (PII at rest) ──────────────────
    PII_ENCRYPTION_KEY: str = ""  # AES-256 key, base64 encoded
    


    # ────────────────── Business Config ──────────────────
    # SELLER_* values are first-boot defaults only.
    # At runtime, seller info is read from the store_settings table (admin-editable).
    SELLER_NAME: str = ""
    SELLER_GSTIN: str = ""
    SELLER_ADDRESS: str = ""
    SELLER_STATE: str = ""
    SELLER_STATE_CODE: str = "27"

    # ────────────────── Rate Limiting ──────────────────
    # RATE_LIMIT_AUTH: int = 5        # requests per minute on auth endpoints
    # RATE_LIMIT_API: int = 300       # requests per minute on general API
    # AWS edge/API protection verification
    AWS_REGION: str = ""
    API_GATEWAY_ID: str = ""
    API_GATEWAY_STAGE: str = ""
    EXPECTED_API_THROTTLE_BURST: int = 10
    EXPECTED_API_THROTTLE_RATE: float = 5.0
    # ────────────────── CORS ──────────────────
    CORS_ORIGINS: list[str] = []
    # Security headers / host validation
    TRUSTED_HOSTS: list[str] = [
    "localhost",
    "127.0.0.1",
    "*.execute-api.ap-south-1.amazonaws.com",
    ]
    ENABLE_SECURITY_HEADERS: bool = True
    ENABLE_HSTS: bool = False
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "forbid"


@lru_cache()
def get_settings() -> Settings:
    return Settings()

