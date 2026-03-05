"""
AWS Lambda entry point for the Ashmiwebportal FastAPI application.

Two invocation modes:
  1. HTTP requests (via API Gateway HTTP API)
     → Mangum wraps the full FastAPI ASGI app.
     → All 147 routes, all middleware (CORS, auth, RBAC, PII, audit) execute identically.

  2. Scheduled events (via AWS EventBridge)
     → Payload contains {"task": "<task_name>"}
     → Routes to the appropriate background job function.
     → Three scheduled tasks:
         release_reservations  — every 60s  (stock reservation expiry)
         fx_rate_sync          — daily       (FX rate refresh)
         process_deletions     — daily       (DPDP account deletion processor)

Handler path for Lambda configuration: lambda_handler.handler
"""

import asyncio
import json

from mangum import Mangum

from app.main import app

# HTTP API Gateway handler — wraps entire FastAPI app
# lifespan="off" required: Lambda manages lifecycle, not ASGI
_mangum_handler = Mangum(app, lifespan="off")


def handler(event: dict, context) -> dict:
    """
    Unified Lambda entry point.
    Detects EventBridge scheduled events by presence of 'task' key.
    All other events are forwarded to Mangum (HTTP requests).
    """
    # EventBridge scheduled task detection
    if "task" in event:
        return _run_background_task(event["task"])

    # HTTP request via API Gateway — delegate to Mangum
    return _mangum_handler(event, context)


def _run_background_task(task_name: str) -> dict:
    """
    Route EventBridge task payloads to the correct background job.

    EventBridge rule targets use payload:
      {"task": "release_reservations"}
      {"task": "fx_rate_sync"}
      {"task": "process_deletions"}
    """
    task_map = {
        "release_reservations": _task_release_reservations,
        "fx_rate_sync": _task_fx_rate_sync,
        "process_deletions": _task_process_deletions,
    }

    task_fn = task_map.get(task_name)
    if not task_fn:
        return {
            "statusCode": 400,
            "body": json.dumps({"error": f"Unknown task: {task_name}"}),
        }

    try:
        asyncio.run(task_fn())
        return {
            "statusCode": 200,
            "body": json.dumps({"task": task_name, "status": "completed"}),
        }
    except Exception as exc:
        return {
            "statusCode": 500,
            "body": json.dumps({"task": task_name, "error": str(exc)}),
        }


# --------------- Background Task Functions ---------------

async def _task_release_reservations() -> None:
    """Release expired stock reservations. EventBridge: every 60 seconds."""
    from app.core.database import async_session_factory
    from app.jobs.reservation_expiry import release_expired_reservations

    async with async_session_factory() as session:
        await release_expired_reservations(session)
        await session.commit()


async def _task_fx_rate_sync() -> None:
    """Sync FX rates from external provider. EventBridge: daily."""
    from app.core.database import async_session_factory
    from app.jobs.fx_rate_sync import sync_fx_rates

    async with async_session_factory() as session:
        await sync_fx_rates(session)
        await session.commit()


async def _task_process_deletions() -> None:
    """Process pending account deletions after 30-day grace period. EventBridge: daily."""
    from app.core.database import async_session_factory
    from app.jobs.account_deletion import process_pending_deletions

    async with async_session_factory() as session:
        await process_pending_deletions(session)
        await session.commit()
