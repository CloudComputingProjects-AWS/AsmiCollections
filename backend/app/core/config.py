"""
Application configuration via environment variables.
Uses pydantic-settings for validation and type coercion.
"""

from functools import lru_cache
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # ──────────────── Application ────────────────
    APP_NAME: str = "Apparel Portal API"
    APP_VERSION: str = "2.5.0"
    DEBUG: bool = False
    ENVIRONMENT: str = "development"

    # ──────────────── Database (PostgreSQL) ────────────────
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/apparel_portal"
    DATABASE_URL_SYNC: str = "postgresql+psycopg2://postgres:postgres@localhost:5432/apparel_portal"
    DB_POOL_SIZE: int = 20
    DB_MAX_OVERFLOW: int = 10
    DB_ECHO: bool = False

    # ──────────────── Redis ────────────────
    REDIS_URL: str = "redis://localhost:6379/0"

    # ──────────────── Auth / JWT ────────────────
    SECRET_KEY: str = "CHANGE-THIS-TO-A-RANDOM-SECRET-IN-PRODUCTION"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # ──────────────── Password Hashing ────────────────
    BCRYPT_ROUNDS: int = 12

    # ──────────────── AWS ────────────────
    AWS_REGION: str = "ap-south-1"
    AWS_ACCESS_KEY_ID: str = ""
    AWS_SECRET_ACCESS_KEY: str = ""
    S3_BUCKET_NAME: str = "apparel-portal-assets"
    S3_BUCKET_INVOICES: str = "apparel-portal-invoices"
    CLOUDFRONT_DOMAIN: str = ""

    # ──────────────── Payment Gateways ────────────────
    RAZORPAY_KEY_ID: str = ""
    RAZORPAY_KEY_SECRET: str = ""
    RAZORPAY_WEBHOOK_SECRET: str = ""
    STRIPE_SECRET_KEY: str = ""
    STRIPE_PUBLISHABLE_KEY: str = ""
    STRIPE_WEBHOOK_SECRET: str = ""

    # ──────────────── FX Rates & Payment Behaviour ────────────────
    OPEN_EXCHANGE_RATES_APP_ID: str = ""
    BASE_CURRENCY: str = "INR"
    FX_RATE_CACHE_TTL_SECONDS: int = 86400
    RESERVATION_EXPIRY_MINUTES: int = 10
    PAYMENT_RETRY_MAX: int = 3

    # ──────────────── Email ────────────────
    SMTP_HOST: str = "email-smtp.ap-south-1.amazonaws.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    FROM_EMAIL: str = "noreply@yourstore.com"

    # ──────────────── Encryption (PII at rest) ────────────────
    PII_ENCRYPTION_KEY: str = ""  # AES-256 key, base64 encoded

    # ──────────────── Business Config ────────────────
    SELLER_NAME: str = "YourStore Pvt Ltd"
    SELLER_GSTIN: str = ""
    SELLER_ADDRESS: str = ""
    SELLER_STATE: str = "Maharashtra"
    SELLER_STATE_CODE: str = "27"
    DEFAULT_CURRENCY: str = "INR"
    STOCK_RESERVATION_MINUTES: int = 10

    # ──────────────── Rate Limiting ────────────────
    RATE_LIMIT_AUTH: int = 5        # requests per minute on auth endpoints
    RATE_LIMIT_API: int = 300       # requests per minute on general API

    # ──────────────── CORS ────────────────
    CORS_ORIGINS: list[str] = ["http://localhost:3000", "http://localhost:5173"]

    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    return Settings()
