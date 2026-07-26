"""create customers table

Revision ID: c1ca2821f651
Revises: d25733017b10
Create Date: 2026-07-24 04:27:31.109956

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c1ca2821f651'
down_revision: Union[str, Sequence[str], None] = 'd25733017b10'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create Customers."""
    op.create_table(
        "customers",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("company", sa.String(), nullable=True),
        sa.Column("phone", sa.String(), nullable=True),
        sa.Column("email", sa.String(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=True,
        ),
        sa.PrimaryKeyConstraint("id", name="customers_pkey"),
    )
    op.create_index(
        "ix_customers_id",
        "customers",
        ["id"],
    )


def downgrade() -> None:
    """Drop Customers."""
    op.drop_index(
        "ix_customers_id",
        table_name="customers",
    )
    op.drop_table("customers")
