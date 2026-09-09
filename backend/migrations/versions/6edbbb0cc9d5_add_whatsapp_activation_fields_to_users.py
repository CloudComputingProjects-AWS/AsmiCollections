"""add whatsapp activation fields to users

Revision ID: 6edbbb0cc9d5
Revises: c9f1a2d4e7b8
Create Date: 2026-09-02 22:04:27.505607
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers
revision: str = "6edbbb0cc9d5"
down_revision: Union[str, None] = 'c9f1a2d4e7b8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("users", sa.Column("whatsapp_number", sa.Text(), nullable=True))
    op.add_column("users", sa.Column("whatsapp_country_code", sa.String(length=5), nullable=True))
    op.add_column("users", sa.Column("whatsapp_wa_id", sa.Text(), nullable=True))
    op.add_column("users", sa.Column("whatsapp_opt_in", sa.Boolean(), nullable=False, server_default=sa.false()))
    op.add_column("users", sa.Column("whatsapp_verified", sa.Boolean(), nullable=False, server_default=sa.false()))
    op.add_column(
        "users",
        sa.Column(
            "whatsapp_activation_status",
            sa.String(length=30),
            nullable=False,
            server_default="not_started",
        ),
    )
    
    op.create_check_constraint(
        "ck_users_whatsapp_activation_status",
        "users",
        "whatsapp_activation_status IN ('not_started', 'pending_verification', 'active', 'opted_out')",
    )
    op.create_index(
        "ix_users_whatsapp_activation_status",
        "users",
        ["whatsapp_activation_status"],
    )


def downgrade() -> None:
    pass
