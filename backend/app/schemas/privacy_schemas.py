"""
Pydantic schemas for Privacy & Data Compliance — Phase 12.
Covers: Consent management, account deletion, data export.
DPDP Act 2023 (India) + GDPR (EU) compliant.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, Field


# ════════════════════════════════════════════════
# CONSENT SCHEMAS
# ════════════════════════════════════════════════

class ConsentItemOut(BaseModel):
    """Single consent record for display."""
    id: UUID
    consent_type: str
    granted: bool
    granted_at: Optional[datetime] = None
    revoked_at: Optional[datetime] = None
    version: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class ConsentsListOut(BaseModel):
    """All consents for a user."""
    consents: list[ConsentItemOut]


class ConsentUpdateItem(BaseModel):
    """Single consent update request."""
    consent_type: str = Field(
        ...,
        pattern=r"^(marketing_email|marketing_sms|cookie_analytics)$",
        description="Only optional consents can be updated. "
                    "terms_of_service and privacy_policy cannot be revoked.",
    )
    granted: bool


class ConsentUpdateRequest(BaseModel):
    """Batch consent update."""
    consents: list[ConsentUpdateItem] = Field(
        ..., min_length=1, max_length=10,
        description="List of consent preferences to update.",
    )


class ConsentUpdateOut(BaseModel):
    """Response after updating consents."""
    updated: int
    consents: list[ConsentItemOut]


# ════════════════════════════════════════════════
# ACCOUNT DELETION SCHEMAS
# ════════════════════════════════════════════════

class DeleteAccountRequest(BaseModel):
    """Request account deletion."""
    reason: Optional[str] = Field(
        None, max_length=1000,
        description="Optional reason for deletion.",
    )
    confirm: bool = Field(
        ...,
        description="Must be True to confirm deletion request.",
    )


class DeleteAccountOut(BaseModel):
    """Response after requesting deletion."""
    id: UUID
    status: str
    grace_ends_at: datetime
    message: str


class CancelDeletionOut(BaseModel):
    """Response after cancelling deletion."""
    message: str
    status: str


class DeletionStatusOut(BaseModel):
    """Current deletion request status."""
    id: UUID
    status: str
    reason: Optional[str] = None
    requested_at: datetime
    grace_ends_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


# ════════════════════════════════════════════════
# DATA EXPORT SCHEMAS
# ════════════════════════════════════════════════

class DataExportOut(BaseModel):
    """Full personal data export (GDPR Article 20 / DPDP)."""
    exported_at: datetime
    user: dict[str, Any]
    addresses: list[dict[str, Any]]
    consents: list[dict[str, Any]]
    orders: list[dict[str, Any]]
    wishlist: list[dict[str, Any]]
    reviews: list[dict[str, Any]]


# ════════════════════════════════════════════════
# COOKIE CONSENT SCHEMAS
# ════════════════════════════════════════════════

class CookieConsentRequest(BaseModel):
    """Cookie consent from frontend banner."""
    essential: bool = Field(True, description="Always true — required.")
    analytics: bool = Field(False, description="Google Analytics, etc.")
    marketing: bool = Field(False, description="Retargeting pixels, etc.")


class CookieConsentOut(BaseModel):
    """Response after setting cookie consent."""
    message: str
    consents_stored: int
