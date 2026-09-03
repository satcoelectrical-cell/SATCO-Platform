"""PATCH-051 nullable Workspace binding compatibility shadows.

Revision ID: e05100000002
Revises: e05100000001
"""

import hashlib
import json
import os
from pathlib import Path

from alembic import op
import sqlalchemy as sa

revision = "e05100000002"
down_revision = "e05100000001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    _require_preflight()
    op.add_column("engineering_workspaces", sa.Column("canonical_discipline_id", sa.String(64), nullable=True, comment="PATCH-051 raw discipline remains authoritative until M3"))
    op.add_column("engineering_workspaces", sa.Column("package_binding_state", sa.String(40), nullable=True))
    op.add_column("engineering_workspaces", sa.Column("bound_package_key", sa.String(64), nullable=True))
    op.add_column("engineering_workspaces", sa.Column("bound_project_configuration_revision", sa.BigInteger(), nullable=True))
    op.create_check_constraint("ck_dp_workspace_binding_state", "engineering_workspaces", "package_binding_state IS NULL OR package_binding_state IN ('OPERATIONAL_PACKAGE_BOUND','FUTURE_UNAVAILABLE_UNBOUND','LEGACY_UNRESOLVED')")
    op.create_check_constraint("ck_dp_workspace_binding_pair", "engineering_workspaces", "(bound_package_key IS NULL AND bound_project_configuration_revision IS NULL) OR (bound_package_key IS NOT NULL AND bound_project_configuration_revision IS NOT NULL)")
    op.create_foreign_key("fk_dp_workspace_exact_selection", "engineering_workspaces", "project_package_configuration_selections", ["project_id", "bound_project_configuration_revision", "bound_package_key"], ["project_id", "configuration_revision", "package_key"], ondelete="RESTRICT", postgresql_not_valid=True)
    op.create_index("uq_dp_workspace_project_canonical", "engineering_workspaces", ["project_id", "canonical_discipline_id"], unique=True, postgresql_where=sa.text("canonical_discipline_id IS NOT NULL"))
    op.create_index("ix_dp_workspace_project_state_id", "engineering_workspaces", ["project_id", "package_binding_state", "id"])
    op.create_index("ix_dp_workspace_bound_revision_key", "engineering_workspaces", ["bound_project_configuration_revision", "bound_package_key"])


def downgrade() -> None:
    _require_preflight()
    bind = op.get_bind()
    if bind.execute(sa.text("SELECT EXISTS (SELECT 1 FROM engineering_workspaces WHERE canonical_discipline_id IS NOT NULL OR package_binding_state IS NOT NULL OR bound_package_key IS NOT NULL OR bound_project_configuration_revision IS NOT NULL)")).scalar_one():
        raise RuntimeError("PATCH-051 M2 downgrade is allowed only before shadow values are used")
    op.drop_index("ix_dp_workspace_bound_revision_key", table_name="engineering_workspaces")
    op.drop_index("ix_dp_workspace_project_state_id", table_name="engineering_workspaces")
    op.drop_index("uq_dp_workspace_project_canonical", table_name="engineering_workspaces")
    op.drop_constraint("fk_dp_workspace_exact_selection", "engineering_workspaces", type_="foreignkey")
    op.drop_constraint("ck_dp_workspace_binding_pair", "engineering_workspaces", type_="check")
    op.drop_constraint("ck_dp_workspace_binding_state", "engineering_workspaces", type_="check")
    for column in ("bound_project_configuration_revision", "bound_package_key", "package_binding_state", "canonical_discipline_id"):
        op.drop_column("engineering_workspaces", column)


def _require_preflight() -> None:
    path = os.environ.get("PATCH051_REQUIRE_PREFLIGHT")
    digest = os.environ.get("PATCH051_REQUIRE_DIGEST")
    if not path or not digest or len(digest) != 64:
        raise RuntimeError("PATCH-051 migration requires a preflight artifact and digest")
    try:
        raw = Path(path).read_bytes()
        payload = json.loads(raw)
    except (OSError, ValueError) as exc:
        raise RuntimeError("PATCH-051 preflight artifact is unreadable") from exc
    if hashlib.sha256(raw).hexdigest() != digest or payload.get("overall") != "PASS":
        raise RuntimeError("PATCH-051 preflight artifact is not an approved PASS")
