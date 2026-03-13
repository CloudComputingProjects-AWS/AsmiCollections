"""
Seed script Ã¢â‚¬â€ populates role_permissions and invoice_sequences.
Run once after database migration.

Usage: python -m app.utils.seed
"""

import asyncio

from sqlalchemy import select, text
from app.core.database import async_session_factory, engine, Base
from app.models.models import RolePermission, InvoiceSequence


# Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬ RBAC Permissions Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬
ROLE_PERMISSIONS = [
    # Admin: full access (checked via role == 'admin' bypass, but seed for completeness)
    ("admin", "all", "all"),

    # Product Manager
    ("product_manager", "products", "create"),
    ("product_manager", "products", "read"),
    ("product_manager", "products", "update"),
    ("product_manager", "products", "delete"),
    ("product_manager", "categories", "create"),
    ("product_manager", "categories", "read"),
    ("product_manager", "categories", "update"),
    ("product_manager", "categories", "delete"),
    ("product_manager", "inventory", "read"),
    ("product_manager", "inventory", "update"),
    ("product_manager", "attributes", "create"),
    ("product_manager", "attributes", "read"),
    ("product_manager", "attributes", "update"),
    ("product_manager", "coupons", "create"),
    ("product_manager", "coupons", "read"),
    ("product_manager", "coupons", "update"),
    ("product_manager", "coupons", "delete"),
    ("product_manager", "reviews", "read"),
    ("product_manager", "reviews", "update"),
    ("product_manager", "size_guides", "create"),
    ("product_manager", "size_guides", "read"),
    ("product_manager", "size_guides", "update"),

    # Order Manager
    ("order_manager", "orders", "read"),
    ("order_manager", "orders", "update"),
    ("order_manager", "shipments", "create"),
    ("order_manager", "shipments", "read"),
    ("order_manager", "shipments", "update"),
    ("order_manager", "returns", "read"),
    ("order_manager", "returns", "update"),
    ("order_manager", "refunds", "create"),
    ("order_manager", "refunds", "read"),

    # Finance Manager
    ("finance_manager", "invoices", "read"),
    ("finance_manager", "credit_notes", "read"),
    ("finance_manager", "orders", "read"),
    ("finance_manager", "refunds", "read"),
    ("finance_manager", "refunds", "update"),
    ("finance_manager", "reports", "read"),
]


async def seed_permissions(session):
    """Insert RBAC permissions if not already present."""
    existing = await session.execute(select(RolePermission))
    if existing.scalars().first():
        print("  [SKIP] role_permissions already seeded")
        return

    for role, resource, action in ROLE_PERMISSIONS:
        session.add(RolePermission(role=role, resource=resource, action=action))
    print(f"  [OK] Seeded {len(ROLE_PERMISSIONS)} role permissions")


async def seed_invoice_sequences(session):
    """Seed invoice sequence counters for current financial year."""
    existing = await session.execute(select(InvoiceSequence))
    if existing.scalars().first():
        print("  [SKIP] invoice_sequences already seeded")
        return

    from datetime import datetime
    now = datetime.now()
    # India FY: April-March. If month >= April, FY is current-next, else prev-current
    if now.month >= 4:
        fy = f"{now.year}-{str(now.year + 1)[2:]}"
    else:
        fy = f"{now.year - 1}-{str(now.year)[2:]}"

    session.add(InvoiceSequence(financial_year=fy, document_type="invoice", last_number=0))
    session.add(InvoiceSequence(financial_year=fy, document_type="credit_note", last_number=0))
    print(f"  [OK] Seeded invoice sequences for FY {fy}")


async def run_seed():
    print("=" * 50)
    print("  Database Seed Script")
    print("=" * 50)
    print()

    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("[OK] Tables created/verified")

    async with async_session_factory() as session:
        await seed_permissions(session)
        await seed_invoice_sequences(session)
        await session.commit()

    print()
    print("[OK] Seed complete!")


if __name__ == "__main__":
    asyncio.run(run_seed())
