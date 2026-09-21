"""Bind derived PATCH-056 rows to the actor who saw the canonical sources.

Revision ID: e05600000007
Revises: e05600000006
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "e05600000007"
down_revision = "e05600000006"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("engineering_performance_snapshots", sa.Column("actor_id", sa.Integer(), nullable=False, server_default="0"))
    op.add_column("engineering_performance_snapshots", sa.Column("source_handles_json", postgresql.JSONB(), nullable=True))
    op.add_column("engineering_performance_snapshots", sa.Column("recomputation_reason", sa.String(32), nullable=False, server_default="legacy_unclassified"))
    op.add_column("engineering_next_action_projections", sa.Column("actor_id", sa.Integer(), nullable=False, server_default="0"))

    op.drop_index("uq_eng_perf_snapshot_project_repro", table_name="engineering_performance_snapshots")
    op.drop_constraint("uq_eng_perf_snapshot_repro", "engineering_performance_snapshots", type_="unique")
    op.create_unique_constraint(
        "uq_eng_perf_snapshot_repro", "engineering_performance_snapshots",
        ["organization_id", "project_id", "workspace_id", "actor_id", "indicator_id",
         "indicator_version", "window_start", "window_end", "source_digest", "calculation_version"],
    )
    op.create_index(
        "uq_eng_perf_snapshot_project_repro", "engineering_performance_snapshots",
        ["organization_id", "project_id", "actor_id", "indicator_id", "indicator_version",
         "window_start", "window_end", "source_digest", "calculation_version"],
        unique=True, postgresql_where=sa.text("workspace_id IS NULL"),
    )

    op.drop_index("uq_eng_next_action_project_key", table_name="engineering_next_action_projections")
    op.drop_constraint("uq_eng_next_action_scope_key", "engineering_next_action_projections", type_="unique")
    op.create_unique_constraint(
        "uq_eng_next_action_scope_key", "engineering_next_action_projections",
        ["organization_id", "project_id", "workspace_id", "actor_id", "action_key"],
    )
    op.create_index(
        "uq_eng_next_action_project_key", "engineering_next_action_projections",
        ["organization_id", "project_id", "actor_id", "action_key"],
        unique=True, postgresql_where=sa.text("workspace_id IS NULL"),
    )


def downgrade():
    # Historical unbound rows can remain, but actor-bound rows cannot be safely
    # collapsed into the old cross-actor unique key or read policy.
    op.execute("""
        DO $$ BEGIN
          IF EXISTS (SELECT 1 FROM engineering_performance_snapshots WHERE actor_id <> 0)
             OR EXISTS (SELECT 1 FROM engineering_next_action_projections WHERE actor_id <> 0)
          THEN RAISE EXCEPTION 'actor-bound PATCH-056 projections require explicit disposition'; END IF;
        END $$
    """)
    op.drop_index("uq_eng_next_action_project_key", table_name="engineering_next_action_projections")
    op.drop_constraint("uq_eng_next_action_scope_key", "engineering_next_action_projections", type_="unique")
    op.create_unique_constraint(
        "uq_eng_next_action_scope_key", "engineering_next_action_projections",
        ["organization_id", "project_id", "workspace_id", "action_key"],
    )
    op.create_index(
        "uq_eng_next_action_project_key", "engineering_next_action_projections",
        ["organization_id", "project_id", "action_key"], unique=True,
        postgresql_where=sa.text("workspace_id IS NULL"),
    )
    op.drop_index("uq_eng_perf_snapshot_project_repro", table_name="engineering_performance_snapshots")
    op.drop_constraint("uq_eng_perf_snapshot_repro", "engineering_performance_snapshots", type_="unique")
    op.create_unique_constraint(
        "uq_eng_perf_snapshot_repro", "engineering_performance_snapshots",
        ["organization_id", "project_id", "workspace_id", "indicator_id", "indicator_version",
         "window_start", "window_end", "source_digest", "calculation_version"],
    )
    op.create_index(
        "uq_eng_perf_snapshot_project_repro", "engineering_performance_snapshots",
        ["organization_id", "project_id", "indicator_id", "indicator_version",
         "window_start", "window_end", "source_digest", "calculation_version"],
        unique=True, postgresql_where=sa.text("workspace_id IS NULL"),
    )
    op.drop_column("engineering_next_action_projections", "actor_id")
    op.drop_column("engineering_performance_snapshots", "source_handles_json")
    op.drop_column("engineering_performance_snapshots", "recomputation_reason")
    op.drop_column("engineering_performance_snapshots", "actor_id")
