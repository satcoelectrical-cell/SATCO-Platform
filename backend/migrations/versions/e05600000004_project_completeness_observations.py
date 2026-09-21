"""Prospective owner-owned Project Completeness observations.

Revision ID: e05600000004
Revises: e05600000003
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "e05600000004"
down_revision = "e05600000003"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "project_completeness_observations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("organizations.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("project_id", sa.Integer(), sa.ForeignKey("projects.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("workspace_id", sa.Integer(), sa.ForeignKey("engineering_workspaces.id", ondelete="RESTRICT"), nullable=True),
        sa.Column("actor_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("observation_version", sa.Integer(), nullable=False),
        sa.Column("method_version", sa.String(64), nullable=False),
        sa.Column("catalog_digest", sa.String(64), nullable=False),
        sa.Column("source_digest", sa.String(64), nullable=False),
        sa.Column("source_cutoff", sa.DateTime(timezone=True), nullable=False),
        sa.Column("observed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("assessment_status", sa.String(32), nullable=False),
        sa.Column("classifications_json", postgresql.JSONB(), nullable=False),
        sa.Column("limitations_json", postgresql.JSONB(), nullable=False),
        sa.UniqueConstraint("organization_id", "project_id", "workspace_id", "actor_id", "method_version", "catalog_digest", "source_digest", name="uq_project_completeness_observation_source"),
    )
    op.create_index(
        "uq_project_completeness_project_source", "project_completeness_observations",
        ["organization_id", "project_id", "actor_id", "method_version", "catalog_digest", "source_digest"],
        unique=True, postgresql_where=sa.text("workspace_id IS NULL"),
    )
    op.create_index(
        "ix_project_completeness_observation_history", "project_completeness_observations",
        ["organization_id", "project_id", "workspace_id", "actor_id", "source_cutoff", "id"],
    )
    op.execute("GRANT SELECT, INSERT ON project_completeness_observations TO satco_runtime")


def downgrade():
    bind = op.get_bind()
    if bind.execute(sa.text("SELECT EXISTS (SELECT 1 FROM project_completeness_observations)")).scalar_one():
        raise RuntimeError("Cannot discard recorded Project Completeness observations")
    op.drop_index("ix_project_completeness_observation_history", table_name="project_completeness_observations")
    op.drop_index("uq_project_completeness_project_source", table_name="project_completeness_observations")
    op.drop_table("project_completeness_observations")
