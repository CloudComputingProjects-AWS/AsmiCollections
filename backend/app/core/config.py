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
    DATABASE_URL_PARAM: str = ""
    DATABASE_URL_SYNC_PARAM: str = ""
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
    IMAGE_CALLBACK_SECRET_PARAM: str = ""

    # ────────────────── Password Hashing ──────────────────
    BCRYPT_ROUNDS: int = 12

    # ────────────────── AWS ──────────────────
    AWS_REGION: str = ""

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
    "*.execute-api.ap-southeast-1.amazonaws.com",
    ]
    ENABLE_SECURITY_HEADERS: bool = True
    ENABLE_HSTS: bool = False
    @property
    def aws_region_effective(self) -> str:
        return self.AWS_REGION or "ap-south-1"
    @staticmethod
    @lru_cache()
    def _get_ssm_parameter(parameter_name: str, region_name: str) -> str:
        import boto3

        client = boto3.client("ssm", region_name=region_name)
        response = client.get_parameter(
            Name=parameter_name,
            WithDecryption=True,
        )
        return response["Parameter"]["Value"]

    def _resolve_secret(self, direct_value: str, parameter_name: str, setting_name: str) -> str:
        if direct_value:
            return direct_value

        if parameter_name:
            return self._get_ssm_parameter(parameter_name, self.aws_region_effective)

        raise ValueError(
            f"{setting_name} is not configured. "
            f"Set either {setting_name} or its corresponding _PARAM setting."
        )

    @property
    def resolved_database_url(self) -> str:
        return self._resolve_secret(
            self.DATABASE_URL,
            self.DATABASE_URL_PARAM,
            "DATABASE_URL",
        )

    @property
    def resolved_database_url_sync(self) -> str:
        return self._resolve_secret(
            self.DATABASE_URL_SYNC,
            self.DATABASE_URL_SYNC_PARAM,
            "DATABASE_URL_SYNC",
        )

    @property
    def resolved_image_callback_secret(self) -> str:
        return self._resolve_secret(
            self.IMAGE_CALLBACK_SECRET,
            self.IMAGE_CALLBACK_SECRET_PARAM,
            "IMAGE_CALLBACK_SECRET",
        )
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "forbid"


@lru_cache()
def get_settings() -> Settings:
    return Settings()


