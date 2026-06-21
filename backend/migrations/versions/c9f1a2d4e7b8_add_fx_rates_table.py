"""add fx_rates table"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "c9f1a2d4e7b8"
down_revision: Union[str, None] = "b8d9a41f2c6e"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "fx_rates",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("base_currency", sa.String(length=3), nullable=False),
        sa.Column("rates", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("source", sa.String(length=100), nullable=False),
        sa.Column("fetched_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_fx_rates_base_currency"), "fx_rates", ["base_currency"], unique=False)
    op.create_index(op.f("ix_fx_rates_expires_at"), "fx_rates", ["expires_at"], unique=False)
    op.create_index("idx_fx_rates_base_expires", "fx_rates", ["base_currency", "expires_at"], unique=False)


def downgrade() -> None:
    op.drop_index("idx_fx_rates_base_expires", table_name="fx_rates")
    op.drop_index(op.f("ix_fx_rates_expires_at"), table_name="fx_rates")
    op.drop_index(op.f("ix_fx_rates_base_currency"), table_name="fx_rates")
    op.drop_table("fx_rates")
