"""Activate WhatsApp consent without separate number verification.

Revision ID: d713ab924e60
Revises: 6edbbb0cc9d5
"""
from alembic import op
import sqlalchemy as sa

revision = "d713ab924e60"
down_revision = "6edbbb0cc9d5"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
        UPDATE users
        SET whatsapp_activation_status = CASE
            WHEN whatsapp_opt_in THEN 'active' ELSE 'not_started' END
        WHERE whatsapp_activation_status = 'pending_verification'
    """)
    op.drop_constraint("ck_users_whatsapp_activation_status", "users", type_="check")
    op.create_check_constraint(
        "ck_users_whatsapp_activation_status", "users",
        "whatsapp_activation_status IN ('not_started', 'active', 'opted_out')",
    )
    op.drop_column("users", "whatsapp_verified")


def downgrade() -> None:
    # Historical verification evidence cannot be reconstructed from consent.
    op.add_column("users", sa.Column("whatsapp_verified", sa.Boolean(), nullable=False, server_default=sa.false()))
    op.drop_constraint("ck_users_whatsapp_activation_status", "users", type_="check")
    op.create_check_constraint(
        "ck_users_whatsapp_activation_status", "users",
        "whatsapp_activation_status IN ('not_started', 'pending_verification', 'active', 'opted_out')",
    )
