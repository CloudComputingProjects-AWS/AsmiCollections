# Customer sends “Hello”
#         ↓
# WhatsApp receives it
#         ↓
# Meta sends POST /api/v1/whatsapp/webhook
#         ↓
# receive_whatsapp_webhook() runs
#         ↓
# verify_meta_signature() checks authenticity
#         ↓
# JSON is parsed
#         ↓
# get_safe_event_summary() creates a safe log entry
#         ↓
# Backend returns HTTP 200

import hashlib
import hmac
import json
import logging
from typing import Any

from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import PlainTextResponse

from app.core.config import get_settings



logger = logging.getLogger(__name__)
# Create a group of WhatsApp-related API routes.
router = APIRouter(prefix="/whatsapp", tags=["whatsapp"])

# Determine whether an incoming POST request really came from Meta.
# Without this check, anybody on the internet could send a fake WhatsApp request to the endpoint.
# Inputs
# - raw_body: The exact webhook request body received from Meta.
# - signature_header: The signature Meta placed in X-Hub-Signature-256.
# - app_secret: The secret belonging to AshmiClothing Customer Support.
def verify_meta_signature(
    raw_body: bytes,
    signature_header: str,
    app_secret: str,
) -> bool:
    """Verify that a webhook POST request was signed by Meta."""
    if not signature_header.startswith("sha256="):
        return False
    expected_signature = "sha256=" + hmac.new(
        app_secret.encode("utf-8"),
        raw_body,
        hashlib.sha256,
    ).hexdigest()
    # It then compares:Signature calculated by our backend
    #             versus
    # Signature supplied by Meta
    return hmac.compare_digest(expected_signature, signature_header)

# Create a small, non-sensitive description of the webhook for application logs.
def get_safe_event_summary(payload: dict[str, Any]) -> dict[str, Any]:
    """Return non-sensitive event metadata suitable for application logs."""
    # payload is the WhatsApp webhook JSON converted into a Python dictionary.
    entries = payload.get("entry", [])
    fields: set[str] = set()

    for entry in entries:
        if not isinstance(entry, dict):
            continue
        
        for change in entry.get("changes", []):
            if isinstance(change, dict) and isinstance(change.get("field"), str):
                fields.add(change["field"])
    # {
    # "object": "whatsapp_business_account",
    # "entry_count": 1,
    # "fields": ["messages"]
    # }
    # This tells us:“A WhatsApp message event arrived.”
    return {
        "object": payload.get("object"),
        "entry_count": len(entries),
        "fields": sorted(fields),
    }

# Operation 1: Meta verifies our webhook URL once
# Meta ──GET request──> verify_whatsapp_webhook()
# the complete address becomes:/api/v1/whatsapp/webhook
# The function:
# 1. Loads our expected verification token.
# 2. Confirms hub.mode equals subscribe.
# 3. Compares Meta’s token with our configured token.
# 4. Rejects the request with 403 when they do not match.
# 5. Returns hub.challenge exactly when everything matches.
@router.get("/webhook", response_class=PlainTextResponse)
async def verify_whatsapp_webhook(
    mode: str | None = Query(default=None, alias="hub.mode"),
    verify_token: str | None = Query(default=None, alias="hub.verify_token"),
    challenge: str | None = Query(default=None, alias="hub.challenge"),
) -> PlainTextResponse:
    """Complete Meta's one-time callback URL verification handshake."""
    settings = get_settings()
    expected_token = settings.resolved_meta_whatsapp_webhook_verify_token

    token_matches = (
        verify_token is not None
        and hmac.compare_digest(verify_token, expected_token)
    )

    if mode != "subscribe" or not token_matches:
        raise HTTPException(status_code=403, detail="Webhook verification failed")

    if challenge is None:
        raise HTTPException(status_code=400, detail="Missing hub.challenge")

    return PlainTextResponse(content=challenge, status_code=200)

# Operation 2: Meta delivers customer messages repeatedly
# Meta ──POST request──> receive_whatsapp_webhook()
#                            │
#                            └──> verify_meta_signature()

@router.post("/webhook")
async def receive_whatsapp_webhook(request: Request) -> dict[str, str]:
    """Authenticate and acknowledge an incoming WhatsApp webhook event."""
    settings = get_settings()
    raw_body = await request.body()
    signature = request.headers.get("X-Hub-Signature-256", "")

    if not verify_meta_signature(
        raw_body,
        signature,
        settings.resolved_meta_whatsapp_app_secret,
    ):
        logger.warning("Rejected WhatsApp webhook with invalid signature")
        raise HTTPException(status_code=403, detail="Invalid webhook signature")

    try:
        payload = json.loads(raw_body)
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=400, detail="Invalid JSON") from exc

    if not isinstance(payload, dict):
        raise HTTPException(status_code=400, detail="Invalid webhook payload")

    logger.info("Received WhatsApp webhook: %s", get_safe_event_summary(payload))

    return {"status": "received"}