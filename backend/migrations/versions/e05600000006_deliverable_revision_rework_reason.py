"""Prospective Deliverable revision reasons and explicit rework resolution.

Revision ID: e05600000006
Revises: e05600000005
"""
from alembic import op
import sqlalchemy as sa

revision = "e05600000006"
down_revision = "e05600000005"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("engineering_deliverable_history", sa.Column("revision_reason", sa.String(32), nullable=True))
    op.add_column("engineering_deliverable_history", sa.Column("rework_resolution_rationale", sa.String(2000), nullable=True))
    op.create_check_constraint(
        "ck_deliverable_history_revision_reason", "engineering_deliverable_history",
        "revision_reason IS NULL OR revision_reason IN ('normal_revision','corrective_rework','review_return_rework','change_driven_revision')",
    )
    op.create_check_constraint(
        "ck_deliverable_history_reason_creation_only", "engineering_deliverable_history",
        "revision_reason IS NULL OR event_type IN ('deliverable_created','revision_created')",
    )
    op.create_check_constraint(
        "ck_deliverable_rework_resolution_event", "engineering_deliverable_history",
        "event_type <> 'rework_resolved' OR (revision_id IS NOT NULL AND revision_reason IS NULL AND revision_target_standing IS NULL AND workspace_scope_recorded = true)",
    )
    op.create_check_constraint(
        "ck_deliverable_rework_resolution_rationale", "engineering_deliverable_history",
        "(event_type = 'rework_resolved' AND rework_resolution_rationale IS NOT NULL AND length(btrim(rework_resolution_rationale)) BETWEEN 1 AND 2000) OR (event_type <> 'rework_resolved' AND rework_resolution_rationale IS NULL)",
    )
    op.create_index(
        "uq_deliverable_rework_resolution", "engineering_deliverable_history",
        ["revision_id"], unique=True,
        postgresql_where=sa.text("event_type = 'rework_resolved'"),
    )


def downgrade():
    if op.get_bind().execute(sa.text(
        "SELECT EXISTS (SELECT 1 FROM engineering_deliverable_history WHERE revision_reason IS NOT NULL OR event_type = 'rework_resolved')"
    )).scalar_one():
        raise RuntimeError("Cannot discard Deliverable rework classification or resolution history")
    op.drop_index("uq_deliverable_rework_resolution", table_name="engineering_deliverable_history")
    op.drop_constraint("ck_deliverable_rework_resolution_rationale", "engineering_deliverable_history")
    op.drop_constraint("ck_deliverable_rework_resolution_event", "engineering_deliverable_history")
    op.drop_constraint("ck_deliverable_history_reason_creation_only", "engineering_deliverable_history")
    op.drop_constraint("ck_deliverable_history_revision_reason", "engineering_deliverable_history")
    op.drop_column("engineering_deliverable_history", "revision_reason")
    op.drop_column("engineering_deliverable_history", "rework_resolution_rationale")
