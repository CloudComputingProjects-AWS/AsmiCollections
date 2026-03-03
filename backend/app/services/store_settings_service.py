"""
Store Settings Service — Phase 13H.
Business logic for store-level configuration (merchant UPI VPA).
"""

import re
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.models import StoreSetting, StoreSettingsAudit

# Same VPA regex as customer UPI validation (from Phase 13G)
VPA_REGEX = re.compile(r"^[a-zA-Z0-9._-]+@[a-zA-Z]{2,}$")

MERCHANT_UPI_KEY = "merchant_upi_vpa"


class SettingsServiceError(Exception):
    def __init__(self, message: str, status_code: int = 400):
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class StoreSettingsService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_merchant_upi_vpa(self) -> dict:
        """Retrieve the current merchant UPI VPA setting."""
        result = await self.db.execute(
            select(StoreSetting).where(StoreSetting.setting_key == MERCHANT_UPI_KEY)
        )
        setting = result.scalar_one_or_none()
        if not setting:
            return {
                "merchant_upi_vpa": None,
                "description": "Not configured",
                "updated_at": None,
            }
        return {
            "merchant_upi_vpa": setting.setting_value,
            "description": setting.description,
            "updated_at": setting.updated_at,
        }

    async def update_merchant_upi_vpa(
        self, new_vpa: str, admin_id: UUID
    ) -> dict:
        """
        Update the merchant UPI VPA.
        Validates VPA format, creates audit trail entry.
        """
        # Validate VPA format
        new_vpa = new_vpa.strip()
        if not new_vpa:
            raise SettingsServiceError("Merchant UPI VPA cannot be empty.")
        if len(new_vpa) < 4 or len(new_vpa) > 50:
            raise SettingsServiceError(
                "Merchant UPI VPA must be between 4 and 50 characters."
            )
        if not VPA_REGEX.match(new_vpa):
            raise SettingsServiceError(
                f"Invalid UPI VPA format: '{new_vpa}'. "
                "Expected format: username@bankhandle (e.g., ashmistore@razorpay)"
            )

        # Get current setting
        result = await self.db.execute(
            select(StoreSetting).where(StoreSetting.setting_key == MERCHANT_UPI_KEY)
        )
        setting = result.scalar_one_or_none()

        old_value = None

        if setting:
            old_value = setting.setting_value
            if old_value == new_vpa:
                raise SettingsServiceError(
                    "New VPA is the same as the current one. No change made."
                )
            setting.setting_value = new_vpa
            setting.updated_by = admin_id
        else:
            # Create the setting if it doesn't exist
            setting = StoreSetting(
                setting_key=MERCHANT_UPI_KEY,
                setting_value=new_vpa,
                description="Merchant UPI VPA for customer payments",
                updated_by=admin_id,
            )
            self.db.add(setting)

        # Create audit trail entry
        audit = StoreSettingsAudit(
            setting_key=MERCHANT_UPI_KEY,
            old_value=old_value,
            new_value=new_vpa,
            changed_by=admin_id,
        )
        self.db.add(audit)
        await self.db.flush()

        return {
            "merchant_upi_vpa": new_vpa,
            "previous_vpa": old_value,
            "updated_by": str(admin_id),
            "message": "Merchant UPI VPA updated successfully.",
        }

    async def get_upi_audit_trail(self, limit: int = 5) -> list[dict]:
        """Get the last N merchant UPI VPA changes."""
        result = await self.db.execute(
            select(StoreSettingsAudit)
            .where(StoreSettingsAudit.setting_key == MERCHANT_UPI_KEY)
            .order_by(StoreSettingsAudit.changed_at.desc())
            .limit(limit)
        )
        rows = result.scalars().all()
        return [
            {
                "id": str(r.id),
                "old_value": r.old_value,
                "new_value": r.new_value,
                "changed_by": str(r.changed_by),
                "changed_at": r.changed_at,
            }
            for r in rows
        ]

    @staticmethod
    async def get_merchant_vpa_value(db: AsyncSession) -> str | None:
        """
        Static helper for payment service to read the merchant VPA.
        Returns the VPA string or None if not configured.
        """
        result = await db.execute(
            select(StoreSetting.setting_value).where(
                StoreSetting.setting_key == MERCHANT_UPI_KEY
            )
        )
        row = result.scalar_one_or_none()
        return row

    # ---- Shipping Config (added by shipping feature script) ----

    async def get_setting_value(self, key: str) -> str | None:
        """Generic: retrieve any store_settings value by key."""
        result = await self.db.execute(
            select(StoreSetting.setting_value).where(
                StoreSetting.setting_key == key
            )
        )
        return result.scalar_one_or_none()

    async def get_shipping_config(self) -> dict:
        """Return shipping fee and free-shipping threshold."""
        fee = await self.get_setting_value("shipping_fee")
        threshold = await self.get_setting_value("free_shipping_threshold")
        return {
            "shipping_fee": float(fee) if fee else 79.0,
            "free_shipping_threshold": float(threshold) if threshold else 999.0,
        }

    async def update_shipping_config(
        self, shipping_fee: float, free_shipping_threshold: float, admin_id
    ) -> dict:
        """Update shipping fee and threshold. Audit-logged."""
        from uuid import UUID as _UUID
        admin_uuid = admin_id if isinstance(admin_id, _UUID) else _UUID(str(admin_id))

        for key, new_val in [
            ("shipping_fee", str(shipping_fee)),
            ("free_shipping_threshold", str(free_shipping_threshold)),
        ]:
            result = await self.db.execute(
                select(StoreSetting).where(StoreSetting.setting_key == key)
            )
            setting = result.scalar_one_or_none()
            old_val = setting.setting_value if setting else None

            if setting:
                setting.setting_value = new_val
                setting.updated_by = admin_uuid
            else:
                setting = StoreSetting(
                    setting_key=key,
                    setting_value=new_val,
                    description=f"Shipping config: {key}",
                    updated_by=admin_uuid,
                )
                self.db.add(setting)

            audit = StoreSettingsAudit(
                setting_key=key,
                old_value=old_val,
                new_value=new_val,
                changed_by=admin_uuid,
            )
            self.db.add(audit)

        await self.db.flush()
        return {
            "shipping_fee": shipping_fee,
            "free_shipping_threshold": free_shipping_threshold,
            "message": "Shipping configuration updated successfully.",
        }

    @staticmethod
    async def get_shipping_config_static(db) -> dict:
        """Static helper for CartPage public endpoint."""
        svc = StoreSettingsService(db)
        return await svc.get_shipping_config()

    # ---- Seller / Business Config ----

    async def get_seller_config(self) -> dict:
        """Return all seller configuration fields."""
        keys = ["seller_name", "seller_gstin", "seller_address", "seller_state", "seller_state_code"]
        result = {}
        for k in keys:
            val = await self.get_setting_value(k)
            result[k] = val or ""
        return result

    async def update_seller_config(self, data: dict, admin_id) -> dict:
        """Update seller config fields. Audit-logged."""
        from uuid import UUID as _UUID
        admin_uuid = admin_id if isinstance(admin_id, _UUID) else _UUID(str(admin_id))
        allowed = ["seller_name", "seller_gstin", "seller_address", "seller_state", "seller_state_code"]
        for key in allowed:
            if key not in data:
                continue
            new_val = str(data[key]).strip()
            result = await self.db.execute(
                select(StoreSetting).where(StoreSetting.setting_key == key)
            )
            setting = result.scalar_one_or_none()
            old_val = setting.setting_value if setting else None
            if setting:
                setting.setting_value = new_val
                setting.updated_by = admin_uuid
            else:
                setting = StoreSetting(
                    setting_key=key, setting_value=new_val,
                    description=f"Seller config: {key}", updated_by=admin_uuid,
                )
                self.db.add(setting)
            audit = StoreSettingsAudit(
                setting_key=key, old_value=old_val, new_value=new_val, changed_by=admin_uuid,
            )
            self.db.add(audit)
        await self.db.flush()
        return {**await self.get_seller_config(), "message": "Seller configuration updated successfully."}

    @staticmethod
    async def get_seller_state_static(db) -> str:
        """Static helper for order_service to read seller_state."""
        svc = StoreSettingsService(db)
        val = await svc.get_setting_value("seller_state")
        return val if val else ""
