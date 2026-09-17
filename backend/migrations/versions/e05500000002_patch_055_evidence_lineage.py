"""PATCH-055 bounded Evidence replacement-lineage forward repair.

Revision ID: e05500000002
Revises: e05500000001
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
revision = "e05500000002"
down_revision = "e05500000001"
branch_labels = None
depends_on = None

def upgrade():
    op.add_column("evidence", sa.Column("replacement_evidence_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.create_foreign_key("fk_evidence_replacement_evidence_id", "evidence", "evidence", ["replacement_evidence_id"], ["id"], ondelete="RESTRICT")
    op.create_index("ix_evidence_replacement_evidence_id", "evidence", ["replacement_evidence_id"], unique=False)

def downgrade():
    op.drop_index("ix_evidence_replacement_evidence_id", table_name="evidence")
    op.drop_constraint("fk_evidence_replacement_evidence_id", "evidence", type_="foreignkey")
    op.drop_column("evidence", "replacement_evidence_id")
