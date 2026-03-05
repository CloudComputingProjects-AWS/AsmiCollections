"""
Database engine and session factory.
Uses async SQLAlchemy with asyncpg driver for PostgreSQL.

Pool strategy is environment-aware via ENVIRONMENT setting in .env:

  development   — Local machine (Docker PostgreSQL)
    - AsyncAdaptedQueuePool: pool_size and max_overflow from config
    - SSL: disabled (local Docker Postgres does not use SSL)
    - pool_pre_ping: enabled (detects stale connections in long dev sessions)

  aws_dev       — AWS Lambda dev stage (Neon PostgreSQL)
    - NullPool: Lambda must not hold connections between invocations
    - SSL: required (Neon mandates SSL on all connections)
    - pool_size / max_overflow: not applicable to NullPool

  production    — AWS Lambda prod stage (Neon PostgreSQL or RDS)
    - NullPool: same reason as aws_dev
    - SSL: required (both Neon and RDS require SSL in production)

IMPORTANT — Neon connection string:
  Use the DIRECT connection string from Neon dashboard (NOT the -pooler endpoint).
  asyncpg prepared statement cache conflicts with PgBouncer transaction mode.
  Format: postgresql+asyncpg://user:pass@ep-xxx.ap-south-1.aws.neon.tech/dbname

IMPORTANT — RDS migration path (when traffic justifies it):
  pg_dump from Neon, pg_restore to RDS, update DATABASE_URL in Lambda env vars only.
  Zero code changes required in this file. Under 1 hour total.
"""

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.pool import AsyncAdaptedQueuePool, NullPool

from app.core.config import get_settings

settings = get_settings()


def _build_engine():
    """
    Build async engine with pool strategy and SSL config based on ENVIRONMENT.

    ENVIRONMENT values (set in backend/.env or Lambda environment variables):
      development  — local Docker Postgres, AsyncAdaptedQueuePool, no SSL
      aws_dev      — Lambda + Neon dev, NullPool, SSL required
      production   — Lambda + Neon/RDS prod, NullPool, SSL required
    """
    env = settings.ENVIRONMENT.lower()

    if env == "development":
        # Local machine — persistent process, use connection pool, no SSL
        return create_async_engine(
            settings.DATABASE_URL,
            poolclass=AsyncAdaptedQueuePool,
            pool_size=settings.DB_POOL_SIZE,
            max_overflow=settings.DB_MAX_OVERFLOW,
            pool_pre_ping=True,
            echo=settings.DB_ECHO,
        )

    else:
        # aws_dev or production — Lambda invocations must not hold connections.
        # NullPool: each request opens and closes its own connection.
        # SSL required for both Neon and RDS.
        return create_async_engine(
            settings.DATABASE_URL,
            poolclass=NullPool,
            echo=settings.DB_ECHO,
            connect_args={"ssl": "require"},
        )


engine = _build_engine()

# Session factory
async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models."""
    pass


async def get_db() -> AsyncSession:
    """FastAPI dependency: yields a DB session per request."""
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db():
    """Create all tables (use Alembic in production instead)."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
