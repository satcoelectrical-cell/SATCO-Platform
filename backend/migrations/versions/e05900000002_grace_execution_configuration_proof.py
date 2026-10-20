"""PATCH-059 durable configuration proof for GRACE execution.

Revision ID: e05900000002
Revises: e05900000001
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "e05900000002"
down_revision = "e05900000001"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "commercial_package_configuration_proofs",
        sa.Column(
            "organization_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("organizations.id", ondelete="RESTRICT"),
            primary_key=True,
        ),
        sa.Column("deployment_id", sa.String(200), primary_key=True),
        sa.Column("package_key", sa.String(64), primary_key=True),
        sa.Column(
            "configured_before",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.Column(
            "recorded_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.CheckConstraint(
            "configured_before <= recorded_at",
            name="ck_commercial_package_configuration_proof_time_order",
        ),
    )

    op.create_index(
        "ix_commercial_package_configuration_proof_org_deployment",
        "commercial_package_configuration_proofs",
        ["organization_id", "deployment_id"],
    )

    op.execute("""
    GRANT SELECT, INSERT, UPDATE ON commercial_package_configuration_proofs TO satco_runtime;
    """)


def downgrade():
    bind = op.get_bind()
    has_rows = bind.execute(
        sa.text(
            "SELECT EXISTS "
            "(SELECT 1 FROM commercial_package_configuration_proofs)"
        )
    ).scalar_one()

    if has_rows:
        raise RuntimeError(
            "Cannot discard PATCH-059 commercial package configuration proof"
        )

    op.execute("""
    REVOKE ALL ON commercial_package_configuration_proofs FROM satco_runtime;
    """)

    op.drop_index(
        "ix_commercial_package_configuration_proof_org_deployment",
        table_name="commercial_package_configuration_proofs",
    )
    op.drop_table("commercial_package_configuration_proofs")
