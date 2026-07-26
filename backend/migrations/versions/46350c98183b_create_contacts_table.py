"""create contacts table

Revision ID: 46350c98183b
Revises: c1ca2821f651
Create Date: 2026-07-24 04:43:20.851741

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '46350c98183b'
down_revision: Union[str, Sequence[str], None] = 'c1ca2821f651'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create Contacts."""
    op.create_table(
        "contacts",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("customer_id", sa.Integer(), nullable=False),
        sa.Column("first_name", sa.String(), nullable=False),
        sa.Column("last_name", sa.String(), nullable=True),
        sa.Column("position", sa.String(), nullable=True),
        sa.Column("mobile", sa.String(), nullable=True),
        sa.Column("phone", sa.String(), nullable=True),
        sa.Column("email", sa.String(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(
            ["customer_id"],
            ["customers.id"],
            name="fk_contacts_customer_id_customers",
        ),
        sa.PrimaryKeyConstraint("id", name="contacts_pkey"),
    )
    op.create_index(
        "ix_contacts_id",
        "contacts",
        ["id"],
    )


def downgrade() -> None:
    """Drop Contacts."""
    op.drop_index(
        "ix_contacts_id",
        table_name="contacts",
    )
    op.drop_table("contacts")
