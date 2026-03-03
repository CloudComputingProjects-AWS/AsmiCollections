"""
Privacy & Data Compliance Endpoints — Phase 12.

Routes:
  GET    /api/v1/user/consents          — View current consents
  PUT    /api/v1/user/consents          — Update consent preferences
  POST   /api/v1/user/delete-account    — Request account deletion
  POST   /api/v1/user/cancel-deletion   — Cancel during grace period
  GET    /api/v1/user/deletion-status   — Check deletion request status
  GET    /api/v1/user/data-export       — Download personal data (GDPR/DPDP)
  POST   /api/v1/user/cookie-consent    — Store cookie consent preferences

DPDP Act 2023 (India) + GDPR (EU) compliant.
"""

from __future__ import annotations

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.middleware.auth import get_current_user
from app.models.models import User
from app.schemas.privacy_schemas import (
    CancelDeletionOut,
    ConsentItemOut,
    ConsentsListOut,
    ConsentUpdateOut,
    ConsentUpdateRequest,
    CookieConsentOut,
    CookieConsentRequest,
    DataExportOut,
    DeleteAccountOut,
    DeleteAccountRequest,
    DeletionStatusOut,
)
from app.services.privacy_service import PrivacyService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/user", tags=["Privacy & Consent"])


def _get_client_ip(request: Request) -> Optional[str]:
    """Extract client IP from request."""
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    if request.client:
        return request.client.host
    return None


# ════════════════════════════════════════════════
# 1. VIEW CONSENTS
# ════════════════════════════════════════════════

@router.get(
    "/consents",
    response_model=ConsentsListOut,
    summary="View current consent preferences",
    description="Returns the latest consent status for each consent type.",
)
async def get_consents(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = PrivacyService(db)
    consents = await service.get_user_consents(current_user.id)
    return ConsentsListOut(
        consents=[ConsentItemOut.model_validate(c) for c in consents]
    )


# ════════════════════════════════════════════════
# 2. UPDATE CONSENTS
# ════════════════════════════════════════════════

@router.put(
    "/consents",
    response_model=ConsentUpdateOut,
    summary="Update consent preferences",
    description=(
        "Update optional consents (marketing_email, marketing_sms, cookie_analytics). "
        "Required consents (terms_of_service, privacy_policy) cannot be revoked. "
        "Each change creates an append-only audit record with IP and user-agent."
    ),
)
async def update_consents(
    body: ConsentUpdateRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = PrivacyService(db)
    updates = [item.model_dump() for item in body.consents]

    new_records = await service.update_consents(
        user_id=current_user.id,
        updates=updates,
        ip_address=_get_client_ip(request),
        user_agent=request.headers.get("user-agent"),
    )
    await db.commit()

    # Refresh all consents for response
    all_consents = await service.get_user_consents(current_user.id)
    return ConsentUpdateOut(
        updated=len(new_records),
        consents=[ConsentItemOut.model_validate(c) for c in all_consents],
    )


# ════════════════════════════════════════════════
# 3. REQUEST ACCOUNT DELETION
# ════════════════════════════════════════════════

@router.post(
    "/delete-account",
    response_model=DeleteAccountOut,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Request account deletion",
    description=(
        "Initiates a 30-day grace period for account deletion. "
        "If active orders exist, the grace period starts after estimated delivery. "
        "During the grace period, the user can cancel the request. "
        "After the grace period, the account is anonymized permanently."
    ),
)
async def request_delete_account(
    body: DeleteAccountRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if not body.confirm:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You must confirm the deletion by setting confirm=true.",
        )

    service = PrivacyService(db)
    try:
        deletion_req = await service.request_account_deletion(
            user_id=current_user.id,
            reason=body.reason,
        )
        await db.commit()
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e),
        )

    return DeleteAccountOut(
        id=deletion_req.id,
        status=deletion_req.status,
        grace_ends_at=deletion_req.grace_ends_at,
        message=(
            f"Account deletion scheduled. Your data will be permanently "
            f"removed after {deletion_req.grace_ends_at.strftime('%d %b %Y')}. "
            f"You can cancel this request before then."
        ),
    )


# ════════════════════════════════════════════════
# 4. CANCEL ACCOUNT DELETION
# ════════════════════════════════════════════════

@router.post(
    "/cancel-deletion",
    response_model=CancelDeletionOut,
    summary="Cancel account deletion",
    description="Cancel a pending account deletion during the grace period.",
)
async def cancel_deletion(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = PrivacyService(db)
    try:
        result = await service.cancel_account_deletion(current_user.id)
        await db.commit()
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    return CancelDeletionOut(**result)


# ════════════════════════════════════════════════
# 5. DELETION STATUS
# ════════════════════════════════════════════════

@router.get(
    "/deletion-status",
    response_model=Optional[DeletionStatusOut],
    summary="Check account deletion status",
    description="Returns the latest deletion request status, if any.",
)
async def get_deletion_status(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = PrivacyService(db)
    req = await service.get_deletion_status(current_user.id)
    if not req:
        return None
    return DeletionStatusOut(
        id=req.id,
        status=req.status,
        reason=req.reason,
        requested_at=req.requested_at,
        grace_ends_at=req.grace_ends_at,
        completed_at=req.completed_at,
    )


# ════════════════════════════════════════════════
# 6. DATA EXPORT (GDPR / DPDP)
# ════════════════════════════════════════════════

@router.get(
    "/data-export",
    response_model=DataExportOut,
    summary="Export personal data",
    description=(
        "Download all personal data as JSON. "
        "GDPR Article 20 (Right to data portability) and "
        "DPDP Act (Right to access personal data)."
    ),
)
async def export_data(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = PrivacyService(db)
    try:
        data = await service.export_user_data(current_user.id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    return data


# ════════════════════════════════════════════════
# 7. COOKIE CONSENT
# ════════════════════════════════════════════════

@router.post(
    "/cookie-consent",
    response_model=CookieConsentOut,
    summary="Store cookie consent preferences",
    description=(
        "Store cookie consent from the frontend banner. "
        "Essential cookies are always required. "
        "Analytics and marketing cookies are optional."
    ),
)
async def store_cookie_consent(
    body: CookieConsentRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = PrivacyService(db)
    stored = await service.store_cookie_consent(
        user_id=current_user.id,
        analytics=body.analytics,
        marketing=body.marketing,
        ip_address=_get_client_ip(request),
        user_agent=request.headers.get("user-agent"),
    )
    await db.commit()
    return CookieConsentOut(
        message="Cookie consent preferences saved.",
        consents_stored=stored,
    )
