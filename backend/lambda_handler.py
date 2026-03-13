"""
AWS Lambda entry point for the Ashmiwebportal FastAPI application.

PERFORMANCE OPTIMIZATION:
  Module-level imports are kept minimal (stdlib + mangum only).
  The full FastAPI app (app.main) is imported LAZILY on first invocation.
  This moves ~3.5s of import time from the init phase (10s hard limit)
  into the first request's execution phase (30s timeout).

  Init phase:  stdlib + mangum + config = ~1.5s (safe at 512MB)
  First request: app.main import + Mangum wrap + handle = ~6s (within 30s)
  Subsequent requests: ~50ms (app already loaded, reused across invocations)

Two invocation modes:
  1. HTTP requests (via API Gateway HTTP API)
     -> Mangum wraps the full FastAPI ASGI app.
  2. Scheduled events (via AWS EventBridge)
     -> Payload contains {"task": "<task_name>"}
     -> Routes to the appropriate background job function.

Handler path for Lambda configuration: lambda_handler.handler
"""

import asyncio
import json

from mangum import Mangum

# Lazy-loaded references — populated on first invocation
_mangum_handler = None
_app = None


def _ensure_app():
    """
    Import app.main and create Mangum handler on first call.
    This runs ONCE per Lambda container, during the first request.
    Subsequent invocations reuse the cached references.
    """
    global _mangum_handler, _app

    if _mangum_handler is not None:
        return

    from app.main import app
    _app = app
    _mangum_handler = Mangum(app, lifespan="off")


def handler(event: dict, context) -> dict:
    """
    Unified Lambda entry point.
    Detects EventBridge scheduled events by presence of 'task' key.
    All other events are forwarded to Mangum (HTTP requests).
    """
    import logging
    import traceback

    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    # EventBridge scheduled task detection -- does NOT need full app
    if "task" in event:
        return _run_background_task(event["task"])

    # HTTP request -- ensure app is loaded, then delegate to Mangum
    try:
        _ensure_app()
        return _mangum_handler(event, context)
    except Exception as e:
        logger.error("Handler exception: %s", str(e))
        logger.error("Full traceback:\n%s", traceback.format_exc())
        return {
            "statusCode": 500,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"error": "Internal server error", "detail": str(e)})
        }


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
            "body": json.dumps({"error": "Unknown task: " + task_name}),
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

async def _task_release_reservations():
    """Release expired stock reservations. EventBridge: every 60 seconds."""
    from app.jobs.reservation_expiry import release_expired_reservations

    await release_expired_reservations()





async def _task_fx_rate_sync():
    """Sync FX rates from external provider. EventBridge: daily."""
    from app.jobs.fx_rate_sync import sync_fx_rates

    await sync_fx_rates()





async def _task_process_deletions():
    """Process pending account deletions after 30-day grace period."""
    from app.jobs.deletion_job import run_deletion_processor
    await run_deletion_processor()
