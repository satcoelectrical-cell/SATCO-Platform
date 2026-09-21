"""Human-authorized Execution owner prerequisite: future milestone completion evidence.

Revision ID: e05600000000
Revises: e05500000002
"""
from alembic import op
import sqlalchemy as sa

revision = "e05600000000"
down_revision = "e05500000002"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("engineering_execution_milestones", sa.Column("actual_completed_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("engineering_execution_milestones", sa.Column("completion_source_kind", sa.String(32), nullable=True))
    op.add_column("engineering_execution_milestones", sa.Column("completion_source_ref", sa.String(128), nullable=True))
    op.create_check_constraint(
        "ck_execution_milestone_completion_evidence_pair",
        "engineering_execution_milestones",
        "(actual_completed_at IS NULL AND completion_source_kind IS NULL AND completion_source_ref IS NULL) "
        "OR (actual_completed_at IS NOT NULL AND completion_source_kind IS NOT NULL AND completion_source_ref IS NOT NULL)",
    )


def downgrade():
    bind = op.get_bind()
    column_exists = bind.execute(sa.text("""
        SELECT EXISTS (
            SELECT 1 FROM information_schema.columns
            WHERE table_schema = current_schema()
              AND table_name = 'engineering_execution_milestones'
              AND column_name = 'actual_completed_at'
        )
    """)).scalar_one()
    if column_exists and bind.execute(sa.text(
        "SELECT EXISTS (SELECT 1 FROM engineering_execution_milestones WHERE actual_completed_at IS NOT NULL)"
    )).scalar_one():
        raise RuntimeError("Cannot discard recorded canonical milestone completion evidence")
    # The disposable test DB may still carry the pre-prerequisite e056 draft.
    op.execute("ALTER TABLE engineering_execution_milestones DROP CONSTRAINT IF EXISTS ck_execution_milestone_completion_evidence_pair")
    op.execute("ALTER TABLE engineering_execution_milestones DROP COLUMN IF EXISTS completion_source_ref")
    op.execute("ALTER TABLE engineering_execution_milestones DROP COLUMN IF EXISTS completion_source_kind")
    op.execute("ALTER TABLE engineering_execution_milestones DROP COLUMN IF EXISTS actual_completed_at")
