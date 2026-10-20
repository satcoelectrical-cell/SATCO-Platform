"""PATCH-059 commercial package, seats and signed-entitlement persistence.

Revision ID: e05900000001
Revises: e05800000001
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "e05900000001"
down_revision = "e05800000001"
branch_labels = None
depends_on = None

def upgrade():
    op.create_table(
        "commercial_entitlement_states",
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("organizations.id", ondelete="RESTRICT"), primary_key=True),
        sa.Column("deployment_id", sa.String(200), primary_key=True),
        sa.Column("entitlement_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("accepted_revision", sa.BigInteger(), nullable=False),
        sa.Column("canonical_payload_digest", sa.String(64), nullable=False),
        sa.Column("key_id", sa.String(120), nullable=False),
        sa.Column("issuer", sa.String(200), nullable=False),
        sa.Column("issued_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("not_before", sa.DateTime(timezone=True), nullable=False),
        sa.Column("valid_until", sa.DateTime(timezone=True), nullable=False),
        sa.Column("grace_until", sa.DateTime(timezone=True), nullable=False),
        sa.Column("support_until", sa.DateTime(timezone=True)),
        sa.Column("package_keys", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("seat_capacity", sa.Integer(), nullable=False),
        sa.Column("baseline_release_sequence", sa.BigInteger(), nullable=False),
        sa.Column("max_release_sequence", sa.BigInteger(), nullable=False),
        sa.Column("last_trusted_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("accepted_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("accepted_by_user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL")),
        sa.Column("time_untrusted_at", sa.DateTime(timezone=True)),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.CheckConstraint("accepted_revision >= 1", name="ck_commercial_entitlement_state_revision"),
        sa.CheckConstraint("seat_capacity >= 1", name="ck_commercial_entitlement_state_capacity"),
        sa.CheckConstraint("baseline_release_sequence >= 1 AND max_release_sequence >= baseline_release_sequence", name="ck_commercial_entitlement_state_release_range"),
        sa.CheckConstraint("issued_at <= not_before AND not_before <= valid_until AND valid_until <= grace_until", name="ck_commercial_entitlement_state_time_order"),
        sa.CheckConstraint("char_length(canonical_payload_digest) = 64", name="ck_commercial_entitlement_state_digest"),
    )
    op.create_index("ix_commercial_entitlement_state_entitlement", "commercial_entitlement_states", ["entitlement_id", "accepted_revision"])

    op.create_table(
        "commercial_entitlement_activations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("organizations.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("deployment_id", sa.String(200), nullable=False),
        sa.Column("entitlement_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("revision", sa.BigInteger(), nullable=False),
        sa.Column("canonical_payload_digest", sa.String(64), nullable=False),
        sa.Column("key_id", sa.String(120), nullable=False),
        sa.Column("outcome", sa.String(32), nullable=False),
        sa.Column("reason_code", sa.String(80)),
        sa.Column("accepted_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("actor_user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL")),
        sa.Column("correlation_id", sa.String(120)),
        sa.CheckConstraint("revision >= 1", name="ck_commercial_entitlement_activation_revision"),
        sa.CheckConstraint("char_length(canonical_payload_digest) = 64", name="ck_commercial_entitlement_activation_digest"),
    )
    op.create_index("ix_commercial_entitlement_activation_org_time", "commercial_entitlement_activations", ["organization_id", "deployment_id", "accepted_at"])

    op.create_table(
        "commercial_seat_assignments",
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("deployment_id", sa.String(200), primary_key=True),
        sa.Column("user_id", sa.Integer(), primary_key=True),
        sa.Column("state", sa.String(16), nullable=False),
        sa.Column("assigned_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("assigned_by_user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_by_user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL")),
        sa.ForeignKeyConstraint(["user_id", "organization_id"], ["user_organization_memberships.user_id", "user_organization_memberships.organization_id"], name="fk_commercial_seat_membership", ondelete="RESTRICT"),
        sa.CheckConstraint("state IN ('ASSIGNED','RESERVED','RETAINED')", name="ck_commercial_seat_state"),
    )
    op.create_index("ix_commercial_seat_org_state", "commercial_seat_assignments", ["organization_id", "deployment_id", "state"])

    op.execute("""
    GRANT SELECT, INSERT, UPDATE ON commercial_entitlement_states TO satco_runtime;
    GRANT SELECT, INSERT ON commercial_entitlement_activations TO satco_runtime;
    GRANT SELECT, INSERT, UPDATE, DELETE ON commercial_seat_assignments TO satco_runtime;
    """)

def downgrade():
    protected_tables = (
        "commercial_entitlement_states",
        "commercial_entitlement_activations",
        "commercial_seat_assignments",
    )
    bind = op.get_bind()
    for table_name in protected_tables:
        has_rows = bind.execute(
            sa.text(f"SELECT EXISTS (SELECT 1 FROM {table_name})")
        ).scalar_one()
        if has_rows:
            raise RuntimeError(
                f"Cannot discard PATCH-059 commercial entitlement state from {table_name}"
            )

    op.execute("""
    REVOKE ALL ON commercial_seat_assignments FROM satco_runtime;
    REVOKE ALL ON commercial_entitlement_activations FROM satco_runtime;
    REVOKE ALL ON commercial_entitlement_states FROM satco_runtime;
    """)

    op.drop_index("ix_commercial_seat_org_state", table_name="commercial_seat_assignments")
    op.drop_table("commercial_seat_assignments")
    op.drop_index("ix_commercial_entitlement_activation_org_time", table_name="commercial_entitlement_activations")
    op.drop_table("commercial_entitlement_activations")
    op.drop_index("ix_commercial_entitlement_state_entitlement", table_name="commercial_entitlement_states")
    op.drop_table("commercial_entitlement_states")
