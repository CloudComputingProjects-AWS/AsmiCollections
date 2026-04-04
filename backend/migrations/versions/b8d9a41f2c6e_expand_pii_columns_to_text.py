"""expand PII columns from fixed String(...) to Text, so ciphertext fits safely."""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "b8d9a41f2c6e"
down_revision: Union[str, None] = "44600a47af5d"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column("users", "phone", existing_type=sa.String(length=20), type_=sa.Text(), existing_nullable=True)
    op.alter_column("user_addresses", "phone", existing_type=sa.String(length=20), type_=sa.Text(), existing_nullable=True)
    op.alter_column("user_addresses", "address_line_1", existing_type=sa.String(length=500), type_=sa.Text(), existing_nullable=False)
    op.alter_column("user_addresses", "address_line_2", existing_type=sa.String(length=500), type_=sa.Text(), existing_nullable=True)


def downgrade() -> None:
    op.alter_column("user_addresses", "address_line_2", existing_type=sa.Text(), type_=sa.String(length=500), existing_nullable=True)
    op.alter_column("user_addresses", "address_line_1", existing_type=sa.Text(), type_=sa.String(length=500), existing_nullable=False)
    op.alter_column("user_addresses", "phone", existing_type=sa.Text(), type_=sa.String(length=20), existing_nullable=True)
    op.alter_column("users", "phone", existing_type=sa.Text(), type_=sa.String(length=20), existing_nullable=True)
