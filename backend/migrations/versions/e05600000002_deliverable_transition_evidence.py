"""Canonical Deliverable owner evidence for future revision standing transitions.

Revision ID: e05600000002
Revises: e05600000001
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "e05600000002"
down_revision = "e05600000001"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("engineering_deliverable_history", sa.Column("revision_target_standing", sa.String(32), nullable=True))
    op.add_column("engineering_deliverable_history", sa.Column("superseded_revision_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column("engineering_deliverable_history", sa.Column("superseded_target_standing", sa.String(32), nullable=True))
    op.add_column("engineering_deliverable_history", sa.Column("workspace_id_at_event", sa.Integer(), nullable=True))
    op.add_column("engineering_deliverable_history", sa.Column("workspace_scope_recorded", sa.Boolean(), nullable=True))
    op.create_foreign_key("fk_deliverable_history_superseded_revision", "engineering_deliverable_history", "engineering_deliverable_revisions", ["superseded_revision_id"], ["id"], ondelete="RESTRICT")
    op.create_foreign_key("fk_deliverable_history_event_workspace", "engineering_deliverable_history", "engineering_workspaces", ["workspace_id_at_event"], ["id"], ondelete="RESTRICT")
    op.create_check_constraint("ck_deliverable_history_revision_target", "engineering_deliverable_history", "revision_target_standing IS NULL OR revision_target_standing IN ('draft','ready_for_review','reviewed','issued','superseded','withdrawn')")
    op.create_check_constraint("ck_deliverable_history_supersession_evidence", "engineering_deliverable_history", "(superseded_revision_id IS NULL AND superseded_target_standing IS NULL) OR (superseded_revision_id IS NOT NULL AND superseded_target_standing = 'superseded')")
    op.create_check_constraint("ck_deliverable_history_scope_recorded", "engineering_deliverable_history", "workspace_scope_recorded IS NULL OR workspace_scope_recorded = true")
    op.create_check_constraint("ck_deliverable_history_transition_scope", "engineering_deliverable_history", "(revision_target_standing IS NULL AND superseded_revision_id IS NULL) OR workspace_scope_recorded = true")


def downgrade():
    bind = op.get_bind()
    if bind.execute(sa.text("SELECT EXISTS (SELECT 1 FROM engineering_deliverable_history WHERE revision_target_standing IS NOT NULL OR superseded_revision_id IS NOT NULL)" )).scalar_one():
        raise RuntimeError("Cannot discard recorded canonical Deliverable transition evidence")
    op.drop_constraint("ck_deliverable_history_transition_scope", "engineering_deliverable_history", type_="check")
    op.drop_constraint("ck_deliverable_history_scope_recorded", "engineering_deliverable_history", type_="check")
    op.drop_constraint("ck_deliverable_history_supersession_evidence", "engineering_deliverable_history", type_="check")
    op.drop_constraint("ck_deliverable_history_revision_target", "engineering_deliverable_history", type_="check")
    op.drop_constraint("fk_deliverable_history_event_workspace", "engineering_deliverable_history", type_="foreignkey")
    op.drop_constraint("fk_deliverable_history_superseded_revision", "engineering_deliverable_history", type_="foreignkey")
    op.drop_column("engineering_deliverable_history", "workspace_scope_recorded")
    op.drop_column("engineering_deliverable_history", "workspace_id_at_event")
    op.drop_column("engineering_deliverable_history", "superseded_target_standing")
    op.drop_column("engineering_deliverable_history", "superseded_revision_id")
    op.drop_column("engineering_deliverable_history", "revision_target_standing")
