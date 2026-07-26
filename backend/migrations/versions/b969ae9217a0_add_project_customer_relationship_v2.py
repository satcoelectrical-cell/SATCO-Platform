"""add project customer relationship v2

Revision ID: b969ae9217a0
Revises: 46350c98183b
Create Date: 2026-07-24 07:33:12.125595

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b969ae9217a0'
down_revision: Union[str, Sequence[str], None] = '46350c98183b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Replace the legacy customer name with a Customer foreign key."""
    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1
                FROM projects AS project
                WHERE (
                    SELECT COUNT(*)
                    FROM customers AS customer
                    WHERE customer.name = project.customer
                ) <> 1
            ) THEN
                RAISE EXCEPTION
                    'Project customer values must map to exactly one Customer';
            END IF;
        END
        $$;
        """
    )

    op.add_column(
        "projects",
        sa.Column("customer_id", sa.Integer(), nullable=True),
    )

    op.execute(
        """
        UPDATE projects
        SET customer_id = customers.id
        FROM customers
        WHERE projects.customer = customers.name
        """
    )

    op.create_foreign_key(
        "fk_projects_customer_id",
        "projects",
        "customers",
        ["customer_id"],
        ["id"],
    )

    op.alter_column(
        "projects",
        "customer_id",
        existing_type=sa.Integer(),
        nullable=False,
    )

    op.drop_column("projects", "customer")


def downgrade() -> None:
    """Restore the legacy customer name representation."""
    op.add_column(
        "projects",
        sa.Column("customer", sa.String(), nullable=True),
    )
    op.execute(
        """
        UPDATE projects
        SET customer = customers.name
        FROM customers
        WHERE projects.customer_id = customers.id
        """
    )
    op.drop_constraint(
        "fk_projects_customer_id",
        "projects",
        type_="foreignkey",
    )
    op.drop_column("projects", "customer_id")
