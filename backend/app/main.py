"""
Main FastAPI application — Apparel Portal API V2.5
Entry point: uvicorn app.main:app --reload
"""

import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_v1_router
from app.core.config import get_settings
from app.core.database import init_db
from app.middleware.audit_log import AdminAuditLogMiddleware
from app.middleware.rate_limiter import RateLimitMiddleware
from app.api.v1.endpoints.payments import (
    router as payment_router,
    webhook_router,
    admin_payment_router,
)
from app.jobs.reservation_expiry import run_periodic as reservation_cleanup_job

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    if settings.ENVIRONMENT == "development":
        await init_db()

    # Start background job: release expired stock reservations every 60s
    reservation_task = asyncio.create_task(
        reservation_cleanup_job(interval_seconds=60)
    )

    yield

    # Shutdown: cancel background tasks
    reservation_task.cancel()
    try:
        await reservation_task
    except asyncio.CancelledError:
        pass


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="E-Commerce Apparel Portal API — India + Global",
    docs_url="/docs" if settings.ENVIRONMENT != "production" else None,
    redoc_url="/redoc" if settings.ENVIRONMENT != "production" else None,
    lifespan=lifespan,
)

# ──────────────── Middleware Stack ────────────────
# Order matters: outermost middleware runs first

# 1. CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 2. Rate Limiting (Redis-backed)
app.add_middleware(RateLimitMiddleware)

# 3. Admin Audit Logging
app.add_middleware(AdminAuditLogMiddleware)

# ──────────────── Routes ────────────────
app.include_router(api_v1_router)
app.include_router(payment_router)
app.include_router(webhook_router)
app.include_router(admin_payment_router)


@app.get("/health", tags=["Health"])
async def health_check():
    return {
        "status": "healthy",
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
    }
