"""Engineering Relationship Engine.

Revision ID: e02600000001
Revises: e02700000001
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "e02600000001"
down_revision = "e02700000001"
branch_labels = None
depends_on = None

FAMILY_TYPES = {
    "structural": ("part_of", "belongs_to_system", "belongs_to_subsystem", "belongs_to_package", "grouped_with", "installed_in", "located_in"),
    "physical": ("connected_to", "mounted_on", "connected_through", "mechanically_coupled_to", "terminated_at", "routed_through", "shares_enclosure_with"),
    "electrical": ("powered_by", "protected_by", "isolated_by", "earthed_through", "connected_to_busbar", "controlled_by_feeder", "backed_up_by_ups"),
    "instrumentation": ("measures", "transmits_to", "receives_process_input_from", "connected_to_loop", "connected_to_io_channel", "actuates", "positioned_by", "monitored_by", "provides_feedback_to", "compensated_by", "calibrated_against"),
    "automation": ("controlled_by", "commands", "receives_signal_from", "sends_signal_to", "implemented_in", "interlocked_with", "trips", "initiates", "inhibits", "participates_in_sequence", "monitored_by", "generates_alarm_for", "executes_logic_for"),
    "dependency": ("depends_on", "affects", "enables", "prevents", "constrains", "replaces", "supersedes", "derived_from"),
}

def _quoted(values): return ", ".join(f"'{value}'" for value in values)
def _pair_check():
    return " OR ".join(
        f"(relationship_family = '{family}' AND relationship_type IN ({_quoted(types)}))"
        for family, types in FAMILY_TYPES.items()
    )

def upgrade():
    op.create_table(
        "engineering_relationships",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("organizations.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("project_id", sa.Integer(), sa.ForeignKey("projects.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("workspace_id", sa.Integer(), sa.ForeignKey("engineering_workspaces.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("source_object_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("engineering_objects.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("target_object_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("engineering_objects.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("relationship_family", sa.String(32), nullable=False),
        sa.Column("relationship_type", sa.String(64), nullable=False),
        sa.Column("lifecycle", sa.String(16), server_default="proposed", nullable=False),
        sa.Column("authority_standing", sa.String(16), server_default="draft", nullable=False),
        sa.Column("evidence_references", sa.JSON(), nullable=False),
        sa.Column("version", sa.Integer(), server_default="1", nullable=False),
        sa.Column("creator_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("steward_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("reviewer_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="RESTRICT")),
        sa.Column("approver_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="RESTRICT")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint(f"relationship_family IN ({_quoted(FAMILY_TYPES)})", name="ck_engineering_relationships_family"),
        sa.CheckConstraint(f"relationship_type IN ({_quoted(sorted({item for values in FAMILY_TYPES.values() for item in values}))})", name="ck_engineering_relationships_type"),
        sa.CheckConstraint(_pair_check(), name="ck_engineering_relationships_family_type"),
        sa.CheckConstraint("lifecycle IN ('proposed','current','superseded','withdrawn','rejected')", name="ck_engineering_relationships_lifecycle"),
        sa.CheckConstraint("authority_standing IN ('draft','proposed','reviewed','approved','disputed','rejected')", name="ck_engineering_relationships_authority"),
        sa.CheckConstraint("source_object_id <> target_object_id", name="ck_engineering_relationships_distinct_endpoints"),
        sa.CheckConstraint("version >= 1", name="ck_engineering_relationships_version"),
        sa.CheckConstraint("reviewer_id IS NULL OR approver_id IS NULL OR reviewer_id <> approver_id", name="ck_engineering_relationships_review_approval_separation"),
        sa.CheckConstraint("approver_id IS NULL OR approver_id <> creator_id", name="ck_engineering_relationships_creator_approval_separation"),
        sa.CheckConstraint("updated_at >= created_at", name="ck_engineering_relationships_timestamp_order"),
    )
    op.create_index("ix_engineering_relationships_source_scope", "engineering_relationships", ["organization_id", "project_id", "workspace_id", "source_object_id"])
    op.create_index("ix_engineering_relationships_target_scope", "engineering_relationships", ["organization_id", "project_id", "workspace_id", "target_object_id"])
    op.create_index("ix_engineering_relationships_vocabulary_lifecycle", "engineering_relationships", ["relationship_family", "relationship_type", "lifecycle"])
    op.create_index(
        "uq_engineering_relationships_active_identity", "engineering_relationships",
        ["organization_id", "project_id", "workspace_id", "source_object_id", "target_object_id", "relationship_family", "relationship_type"],
        unique=True, postgresql_where=sa.text("lifecycle IN ('proposed','current')"),
    )
    op.create_table(
        "engineering_relationship_outbox",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("event_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("aggregate_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("engineering_relationships.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("aggregate_version", sa.Integer(), nullable=False),
        sa.Column("event_type", sa.String(96), nullable=False),
        sa.Column("schema_version", sa.Integer(), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("published_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("event_id", name="uq_engineering_relationship_outbox_event"),
        sa.CheckConstraint("aggregate_version >= 1", name="ck_engineering_relationship_outbox_version"),
    )
    op.create_index("ix_engineering_relationship_outbox_unpublished", "engineering_relationship_outbox", ["published_at", "occurred_at"])
    op.create_table(
        "engineering_relationship_idempotency",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("actor_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("command_type", sa.String(80), nullable=False),
        sa.Column("idempotency_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("request_fingerprint", sa.String(64), nullable=False),
        sa.Column("status", sa.String(16), server_default="pending", nullable=False),
        sa.Column("aggregate_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("engineering_relationships.id", ondelete="RESTRICT")),
        sa.Column("result", sa.JSON()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("actor_id", "command_type", "idempotency_id", name="uq_engineering_relationship_idempotency_scope"),
        sa.CheckConstraint("status IN ('pending','completed')", name="ck_engineering_relationship_idempotency_status"),
    )
    op.create_index("ix_engineering_relationship_idempotency_lookup", "engineering_relationship_idempotency", ["actor_id", "command_type", "idempotency_id"])

def downgrade():
    op.drop_index("ix_engineering_relationship_idempotency_lookup", table_name="engineering_relationship_idempotency")
    op.drop_table("engineering_relationship_idempotency")
    op.drop_index("ix_engineering_relationship_outbox_unpublished", table_name="engineering_relationship_outbox")
    op.drop_table("engineering_relationship_outbox")
    op.drop_index("uq_engineering_relationships_active_identity", table_name="engineering_relationships")
    op.drop_index("ix_engineering_relationships_vocabulary_lifecycle", table_name="engineering_relationships")
    op.drop_index("ix_engineering_relationships_target_scope", table_name="engineering_relationships")
    op.drop_index("ix_engineering_relationships_source_scope", table_name="engineering_relationships")
    op.drop_table("engineering_relationships")
