"""
Privacy & Compliance Service — Phase 12.

Implements:
  - Consent management (view, update, audit trail)
  - Account deletion (request, cancel, grace period, anonymization)
  - Data export (GDPR Article 20 / DPDP Act)
  - Cookie consent handling
  - Background job: process expired grace-period deletions
"""

from __future__ import annotations

import logging
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any, Optional
from uuid import UUID

from sqlalchemy import and_, delete, func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.models import (
    AccountDeletionRequest,
    Cart,
    CartItem,
    Order,
    RefreshToken,
    Review,
    User,
    UserAddress,
    UserConsent,
)

logger = logging.getLogger(__name__)

# Grace period in days before account is anonymized
GRACE_PERIOD_DAYS = 30

# Active order statuses that block immediate deletion
ACTIVE_ORDER_STATUSES = {
    "placed", "confirmed", "processing", "shipped", "out_for_delivery",
}

# Consent types that CANNOT be revoked (required for service)
REQUIRED_CONSENTS = {"terms_of_service", "privacy_policy", "data_processing"}

# Consent types that CAN be toggled by user
OPTIONAL_CONSENTS = {"marketing_email", "marketing_sms", "cookie_analytics"}


class PrivacyService:
    """Handles all privacy and data compliance operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    # ════════════════════════════════════════════════
    # 1. CONSENT MANAGEMENT
    # ════════════════════════════════════════════════

    async def get_user_consents(self, user_id: UUID) -> list[UserConsent]:
        """Get all consent records for a user (latest per type)."""
        # Subquery: latest consent per type
        subq = (
            select(
                UserConsent.consent_type,
                func.max(UserConsent.created_at).label("latest"),
            )
            .where(UserConsent.user_id == user_id)
            .group_by(UserConsent.consent_type)
            .subquery()
        )

        result = await self.db.execute(
            select(UserConsent)
            .join(
                subq,
                and_(
                    UserConsent.consent_type == subq.c.consent_type,
                    UserConsent.created_at == subq.c.latest,
                    UserConsent.user_id == user_id,
                ),
            )
            .order_by(UserConsent.consent_type)
        )
        return list(result.scalars().all())

    async def update_consents(
        self,
        user_id: UUID,
        updates: list[dict[str, Any]],
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> list[UserConsent]:
        """
        Update optional consent preferences.
        Creates new consent records (append-only audit trail).
        """
        now = datetime.now(timezone.utc)
        new_records: list[UserConsent] = []

        for item in updates:
            consent_type = item["consent_type"]
            granted = item["granted"]

            # Block revocation of required consents
            if consent_type in REQUIRED_CONSENTS and not granted:
                logger.warning(
                    "Attempt to revoke required consent %s by user %s",
                    consent_type, user_id,
                )
                continue

            # Only allow known optional types
            if consent_type not in OPTIONAL_CONSENTS:
                continue

            consent = UserConsent(
                user_id=user_id,
                consent_type=consent_type,
                granted=granted,
                granted_at=now if granted else None,
                revoked_at=now if not granted else None,
                ip_address=ip_address,
                user_agent=user_agent,
                version="2.1",
                created_at=now,
            )
            self.db.add(consent)
            new_records.append(consent)

        await self.db.flush()
        logger.info("Updated %d consents for user %s", len(new_records), user_id)
        return new_records

    # ════════════════════════════════════════════════
    # 2. ACCOUNT DELETION — REQUEST
    # ════════════════════════════════════════════════

    async def request_account_deletion(
        self,
        user_id: UUID,
        reason: Optional[str] = None,
    ) -> AccountDeletionRequest:
        """
        Request account deletion with 30-day grace period.
        If active orders exist, grace period starts after last order delivery.
        """
        # Check for existing pending/grace_period request
        existing = await self.db.execute(
            select(AccountDeletionRequest).where(
                AccountDeletionRequest.user_id == user_id,
                AccountDeletionRequest.status.in_(["pending", "grace_period"]),
            )
        )
        if existing.scalar_one_or_none():
            raise ValueError("An active deletion request already exists.")

        # Check for active orders
        active_orders = await self.db.execute(
            select(Order).where(
                Order.user_id == user_id,
                Order.order_status.in_(ACTIVE_ORDER_STATUSES),
            )
        )
        active_list = list(active_orders.scalars().all())

        now = datetime.now(timezone.utc)

        if active_list:
            # Grace period starts 30 days after estimated last delivery
            # Use latest order's created_at + 14 days as estimate
            latest_order_date = max(o.created_at for o in active_list)
            estimated_delivery = latest_order_date + timedelta(days=14)
            grace_ends = estimated_delivery + timedelta(days=GRACE_PERIOD_DAYS)
        else:
            grace_ends = now + timedelta(days=GRACE_PERIOD_DAYS)

        deletion_request = AccountDeletionRequest(
            user_id=user_id,
            reason=reason,
            status="grace_period",
            requested_at=now,
            grace_ends_at=grace_ends,
        )
        self.db.add(deletion_request)

        # Mark user
        await self.db.execute(
            update(User)
            .where(User.id == user_id)
            .values(
                deletion_requested_at=now,
                deletion_scheduled_at=grace_ends,
            )
        )

        await self.db.flush()
        logger.info(
            "Account deletion requested for user %s, grace ends %s",
            user_id, grace_ends.isoformat(),
        )
        return deletion_request

    # ════════════════════════════════════════════════
    # 3. ACCOUNT DELETION — CANCEL
    # ════════════════════════════════════════════════

    async def cancel_account_deletion(self, user_id: UUID) -> dict[str, str]:
        """Cancel a pending deletion request during grace period."""
        result = await self.db.execute(
            select(AccountDeletionRequest).where(
                AccountDeletionRequest.user_id == user_id,
                AccountDeletionRequest.status.in_(["pending", "grace_period"]),
            )
        )
        request = result.scalar_one_or_none()
        if not request:
            raise ValueError("No active deletion request found.")

        request.status = "cancelled"

        # Clear user deletion markers
        await self.db.execute(
            update(User)
            .where(User.id == user_id)
            .values(
                deletion_requested_at=None,
                deletion_scheduled_at=None,
            )
        )

        await self.db.flush()
        logger.info("Account deletion cancelled for user %s", user_id)
        return {"message": "Account deletion cancelled.", "status": "cancelled"}

    # ════════════════════════════════════════════════
    # 4. ACCOUNT DELETION — GET STATUS
    # ════════════════════════════════════════════════

    async def get_deletion_status(
        self, user_id: UUID,
    ) -> Optional[AccountDeletionRequest]:
        """Get current deletion request status."""
        result = await self.db.execute(
            select(AccountDeletionRequest)
            .where(AccountDeletionRequest.user_id == user_id)
            .order_by(AccountDeletionRequest.requested_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    # ════════════════════════════════════════════════
    # 5. ANONYMIZATION — Background Job
    # ════════════════════════════════════════════════

    async def process_expired_deletions(self) -> int:
        """
        Background job: anonymize accounts whose grace period has expired.
        Called by scheduler (e.g., daily cron).

        Returns count of accounts processed.
        """
        now = datetime.now(timezone.utc)
        processed = 0

        # Find expired grace-period requests
        result = await self.db.execute(
            select(AccountDeletionRequest).where(
                AccountDeletionRequest.status == "grace_period",
                AccountDeletionRequest.grace_ends_at <= now,
            )
        )
        expired_requests = list(result.scalars().all())

        for req in expired_requests:
            try:
                await self._anonymize_user(req.user_id, req)
                processed += 1
            except Exception:
                logger.exception(
                    "Failed to anonymize user %s", req.user_id,
                )

        if processed:
            await self.db.commit()
            logger.info("Processed %d account deletions", processed)

        return processed

    async def _anonymize_user(
        self,
        user_id: UUID,
        deletion_request: AccountDeletionRequest,
    ) -> None:
        """
        Anonymize a user account per DPDP/GDPR requirements.

        RETAINS: orders, invoices, payment records (legal requirement).
        DELETES: addresses, wishlist, cart, refresh tokens.
        ANONYMIZES: email, name, phone, password.
        """
        now = datetime.now(timezone.utc)
        anonymized_email = f"deleted_user_{user_id}@anonymized.local"
        random_password = secrets.token_hex(32)

        # 1. Anonymize user record
        await self.db.execute(
            update(User)
            .where(User.id == user_id)
            .values(
                email=anonymized_email,
                first_name="Deleted",
                last_name="User",
                phone=None,
                password_hash=random_password,
                is_active=False,
                deleted_at=now,
                email_verified=False,
                totp_secret=None,
                totp_enabled=False,
            )
        )

        # 2. Delete personal data (not legally required to retain)
        # Addresses
        await self.db.execute(
            delete(UserAddress).where(UserAddress.user_id == user_id)
        )

        # Wishlist
        await self.db.execute(
        )

        # Cart + cart items (cascade)
        cart_result = await self.db.execute(
            select(Cart).where(Cart.user_id == user_id)
        )
        cart = cart_result.scalar_one_or_none()
        if cart:
            await self.db.execute(
                delete(CartItem).where(CartItem.cart_id == cart.id)
            )
            await self.db.execute(
                delete(Cart).where(Cart.id == cart.id)
            )

        # Refresh tokens
        await self.db.execute(
            delete(RefreshToken).where(RefreshToken.user_id == user_id)
        )

        # 3. Update deletion request
        deletion_request.status = "completed"
        deletion_request.completed_at = now
        deletion_request.anonymized_fields = {
            "email": True,
            "first_name": True,
            "last_name": True,
            "phone": True,
            "password_hash": True,
            "addresses": "deleted",
            "wishlist": "deleted",
            "cart": "deleted",
            "refresh_tokens": "deleted",
            "retained": ["orders", "invoices", "payment_events", "refunds"],
        }

        await self.db.flush()
        logger.info("User %s anonymized successfully", user_id)

    # ════════════════════════════════════════════════
    # 6. DATA EXPORT (GDPR Article 20 / DPDP)
    # ════════════════════════════════════════════════

    async def export_user_data(self, user_id: UUID) -> dict[str, Any]:
        """
        Export all personal data for a user as JSON.
        GDPR Article 20: Right to data portability.
        DPDP Act: Right to access personal data.
        """
        now = datetime.now(timezone.utc)

        # User profile
        user_result = await self.db.execute(
            select(User).where(User.id == user_id)
        )
        user = user_result.scalar_one_or_none()
        if not user:
            raise ValueError("User not found.")

        user_data = {
            "id": str(user.id),
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "phone": user.phone,
            "country_code": user.country_code,
            "email_verified": user.email_verified,
            "created_at": user.created_at.isoformat() if user.created_at else None,
        }

        # Addresses
        addr_result = await self.db.execute(
            select(UserAddress).where(
                UserAddress.user_id == user_id,
                UserAddress.deleted_at.is_(None),
            )
        )
        addresses = [
            {
                "label": a.label,
                "full_name": a.full_name,
                "phone": a.phone,
                "address_line_1": a.address_line_1,
                "address_line_2": a.address_line_2,
                "city": a.city,
                "state": a.state,
                "postal_code": a.postal_code,
                "country": a.country,
                "is_default": a.is_default,
            }
            for a in addr_result.scalars().all()
        ]

        # Consents
        consents = await self.get_user_consents(user_id)
        consent_data = [
            {
                "consent_type": c.consent_type,
                "granted": c.granted,
                "granted_at": c.granted_at.isoformat() if c.granted_at else None,
                "revoked_at": c.revoked_at.isoformat() if c.revoked_at else None,
                "version": c.version,
            }
            for c in consents
        ]

        # Orders (summary only — no internal IDs)
        order_result = await self.db.execute(
            select(Order).where(Order.user_id == user_id)
            .order_by(Order.created_at.desc())
        )
        orders = [
            {
                "order_number": o.order_number,
                "order_status": o.order_status,
                "grand_total": float(o.grand_total) if o.grand_total else None,
                "currency": o.currency,
                "created_at": o.created_at.isoformat() if o.created_at else None,
            }
            for o in order_result.scalars().all()
        ]

        # Wishlist
        wish_result = await self.db.execute(
        )
        wishlist = [
            {
                "product_id": str(w.product_id),
                "added_at": w.added_at.isoformat() if w.added_at else None,
            }
            for w in wish_result.scalars().all()
        ]

        # Reviews
        review_result = await self.db.execute(
            select(Review).where(Review.user_id == user_id)
        )
        reviews = [
            {
                "product_id": str(r.product_id),
                "rating": r.rating,
                "title": r.title,
                "comment": r.comment,
                "fit_feedback": r.fit_feedback,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            }
            for r in review_result.scalars().all()
        ]

        return {
            "exported_at": now.isoformat(),
            "user": user_data,
            "addresses": addresses,
            "consents": consent_data,
            "orders": orders,
            "wishlist": wishlist,
            "reviews": reviews,
        }

    # ════════════════════════════════════════════════
    # 7. COOKIE CONSENT
    # ════════════════════════════════════════════════

    async def store_cookie_consent(
        self,
        user_id: Optional[UUID],
        analytics: bool,
        marketing: bool,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> int:
        """
        Store cookie consent preferences.
        Can be called for both authenticated and guest users.
        For guests, user_id will be None (consent stored on frontend only).
        """
        if not user_id:
            return 0  # Guest — handled by frontend cookie

        now = datetime.now(timezone.utc)
        stored = 0

        # Cookie analytics consent
        consent_analytics = UserConsent(
            user_id=user_id,
            consent_type="cookie_analytics",
            granted=analytics,
            granted_at=now if analytics else None,
            revoked_at=now if not analytics else None,
            ip_address=ip_address,
            user_agent=user_agent,
            version="1.0",
            created_at=now,
        )
        self.db.add(consent_analytics)
        stored += 1

        # Marketing cookie consent (future-proofing)
        if marketing:
            consent_marketing = UserConsent(
                user_id=user_id,
                consent_type="cookie_marketing",
                granted=marketing,
                granted_at=now,
                ip_address=ip_address,
                user_agent=user_agent,
                version="1.0",
                created_at=now,
            )
            self.db.add(consent_marketing)
            stored += 1

        await self.db.flush()
        logger.info("Stored %d cookie consents for user %s", stored, user_id)
        return stored
