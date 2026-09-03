"""PATCH-051 Registry projection, configuration, and package Audit foundation.

Revision ID: e05100000001
Revises: e04700000001
"""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "e05100000001"
down_revision = "e04700000001"
branch_labels = None
depends_on = None

_PROJECTION_TABLES = (
    "discipline_package_registry_releases", "discipline_package_descriptors",
    "discipline_package_registry_memberships", "discipline_package_compatibility_profiles",
    "discipline_package_registry_profile_memberships", "discipline_package_compatibility_members",
)


def _require_preflight() -> None:
    """Require a reviewed, digest-bound read-only census supplied by the wrapper."""

    artifact_path = os.environ.get("PATCH051_REQUIRE_PREFLIGHT")
    expected_digest = os.environ.get("PATCH051_REQUIRE_DIGEST")
    if not artifact_path or not expected_digest or len(expected_digest) != 64:
        raise RuntimeError("PATCH-051 migration requires a preflight artifact and digest")
    try:
        raw = Path(artifact_path).read_bytes()
        artifact = json.loads(raw)
    except (OSError, ValueError) as exc:
        raise RuntimeError("PATCH-051 preflight artifact is unreadable") from exc
    if hashlib.sha256(raw).hexdigest() != expected_digest or artifact.get("overall") != "PASS":
        raise RuntimeError("PATCH-051 preflight artifact is not an approved PASS")


def _require_roles() -> None:
    op.execute("""
DO $$ BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname='satco_runtime')
     OR NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname='satco_registry_installer') THEN
    RAISE EXCEPTION 'PATCH-051 required database roles are absent';
  END IF;
END $$;
""")


def upgrade() -> None:
    _require_preflight()
    _require_roles()
    op.create_unique_constraint("uq_projects_id_organization", "projects", ["id", "organization_id"])
    op.create_unique_constraint("uq_engineering_workspaces_id_project", "engineering_workspaces", ["id", "project_id"])

    op.create_table(
        "discipline_package_registry_releases",
        sa.Column("registry_digest", sa.String(64), primary_key=True),
        sa.Column("release_id", sa.String(64), nullable=False, unique=True),
        sa.Column("core_contract_version", sa.Integer(), nullable=False),
        sa.Column("is_current", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("manifest_json", postgresql.JSONB(), nullable=False),
        sa.CheckConstraint("length(registry_digest)=64", name="ck_dp_release_digest"),
    )
    op.create_index("uq_dp_release_current", "discipline_package_registry_releases", ["is_current"], unique=True, postgresql_where=sa.text("is_current"))
    op.create_table(
        "discipline_package_descriptors",
        sa.Column("package_key", sa.String(64), primary_key=True),
        sa.Column("package_version", sa.String(32), primary_key=True),
        sa.Column("descriptor_digest", sa.String(64), nullable=False, unique=True),
        sa.Column("primary_discipline_id", sa.String(64), nullable=False),
        sa.Column("adapter_id", sa.String(128), nullable=False),
        sa.Column("standing", sa.String(40), nullable=False),
        sa.Column("descriptor_json", postgresql.JSONB(), nullable=False),
    )
    op.create_table(
        "discipline_package_registry_memberships",
        sa.Column("registry_digest", sa.String(64), sa.ForeignKey("discipline_package_registry_releases.registry_digest", ondelete="RESTRICT"), primary_key=True),
        sa.Column("package_key", sa.String(64), primary_key=True),
        sa.Column("package_version", sa.String(32), primary_key=True),
        sa.Column("standing", sa.String(40), nullable=False),
        sa.ForeignKeyConstraint(["package_key", "package_version"], ["discipline_package_descriptors.package_key", "discipline_package_descriptors.package_version"], ondelete="RESTRICT"),
        sa.CheckConstraint("standing IN ('executable_supported','historical_read_only')", name="ck_dp_membership_standing"),
    )
    op.create_table(
        "discipline_package_compatibility_profiles",
        sa.Column("profile_id", sa.String(64), primary_key=True),
        sa.Column("profile_digest", sa.String(64), primary_key=True),
        sa.Column("profile_json", postgresql.JSONB(), nullable=False),
    )
    op.create_table(
        "discipline_package_registry_profile_memberships",
        sa.Column("registry_digest", sa.String(64), sa.ForeignKey("discipline_package_registry_releases.registry_digest", ondelete="RESTRICT"), primary_key=True),
        sa.Column("profile_id", sa.String(64), primary_key=True),
        sa.Column("profile_digest", sa.String(64), nullable=False),
        sa.ForeignKeyConstraint(["profile_id", "profile_digest"], ["discipline_package_compatibility_profiles.profile_id", "discipline_package_compatibility_profiles.profile_digest"], ondelete="RESTRICT"),
        sa.UniqueConstraint("registry_digest", "profile_id", "profile_digest", name="uq_dp_release_profile_digest"),
    )
    op.create_index("ix_dp_profile_release", "discipline_package_registry_profile_memberships", ["profile_id", "profile_digest", "registry_digest"])
    op.create_table(
        "discipline_package_compatibility_members",
        sa.Column("profile_id", sa.String(64), primary_key=True),
        sa.Column("profile_digest", sa.String(64), primary_key=True),
        sa.Column("combination_digest", sa.String(64), primary_key=True),
        sa.Column("package_key", sa.String(64), primary_key=True),
        sa.Column("package_version", sa.String(32), nullable=False),
        sa.Column("descriptor_digest", sa.String(64), nullable=False),
        sa.ForeignKeyConstraint(["profile_id", "profile_digest"], ["discipline_package_compatibility_profiles.profile_id", "discipline_package_compatibility_profiles.profile_digest"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["package_key", "package_version"], ["discipline_package_descriptors.package_key", "discipline_package_descriptors.package_version"], ondelete="RESTRICT"),
    )
    op.create_table(
        "organization_package_configuration_heads",
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("organizations.id", ondelete="RESTRICT"), primary_key=True),
        sa.Column("configuration_version", sa.BigInteger(), nullable=False, server_default="0"),
        sa.CheckConstraint("configuration_version >= 0", name="ck_dp_org_head_version"),
    )
    op.create_table(
        "organization_package_selections",
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("organizations.id", ondelete="RESTRICT"), primary_key=True),
        sa.Column("package_key", sa.String(64), primary_key=True),
        sa.Column("package_version", sa.String(32), primary_key=True),
        sa.Column("state", sa.String(16), nullable=False),
        sa.Column("configuration_version", sa.BigInteger(), nullable=False),
        sa.ForeignKeyConstraint(["package_key", "package_version"], ["discipline_package_descriptors.package_key", "discipline_package_descriptors.package_version"], ondelete="RESTRICT"),
        sa.CheckConstraint("state IN ('enabled','disabled')", name="ck_dp_org_selection_state"),
    )
    op.create_table(
        "project_package_configuration_revisions",
        sa.Column("project_id", sa.Integer(), primary_key=True),
        sa.Column("configuration_revision", sa.BigInteger(), primary_key=True),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("observed_registry_digest", sa.String(64), nullable=False),
        sa.Column("profile_id", sa.String(64), nullable=False),
        sa.Column("profile_digest", sa.String(64), nullable=False),
        sa.Column("rationale", sa.String(2000), nullable=False),
        sa.ForeignKeyConstraint(["project_id", "organization_id"], ["projects.id", "projects.organization_id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["observed_registry_digest", "profile_id", "profile_digest"], ["discipline_package_registry_profile_memberships.registry_digest", "discipline_package_registry_profile_memberships.profile_id", "discipline_package_registry_profile_memberships.profile_digest"], ondelete="RESTRICT"),
        sa.UniqueConstraint("project_id", "organization_id", "configuration_revision", name="uq_dp_project_revision_tenant"),
        sa.CheckConstraint("configuration_revision >= 1", name="ck_dp_project_revision"),
    )
    op.create_table(
        "project_package_configuration_selections",
        sa.Column("project_id", sa.Integer(), primary_key=True),
        sa.Column("configuration_revision", sa.BigInteger(), primary_key=True),
        sa.Column("package_key", sa.String(64), primary_key=True),
        sa.Column("package_version", sa.String(32), nullable=False),
        sa.Column("descriptor_digest", sa.String(64), nullable=False),
        sa.ForeignKeyConstraint(["project_id", "configuration_revision"], ["project_package_configuration_revisions.project_id", "project_package_configuration_revisions.configuration_revision"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["package_key", "package_version"], ["discipline_package_descriptors.package_key", "discipline_package_descriptors.package_version"], ondelete="RESTRICT"),
    )
    op.create_table(
        "project_package_configuration_heads",
        sa.Column("project_id", sa.Integer(), primary_key=True),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("current_revision", sa.BigInteger(), nullable=False),
        sa.Column("configuration_version", sa.BigInteger(), nullable=False, server_default="0"),
        sa.ForeignKeyConstraint(["project_id", "organization_id", "current_revision"], ["project_package_configuration_revisions.project_id", "project_package_configuration_revisions.organization_id", "project_package_configuration_revisions.configuration_revision"], ondelete="RESTRICT"),
        sa.CheckConstraint("configuration_version >= 0", name="ck_dp_project_head_version"),
    )
    op.create_table(
        "package_configuration_audit_events",
        sa.Column("event_id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("organizations.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("project_id", sa.Integer()), sa.Column("workspace_id", sa.Integer()),
        sa.Column("actor_user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("category", sa.String(32), nullable=False), sa.Column("action", sa.String(32), nullable=False),
        sa.Column("metadata_json", postgresql.JSONB(), nullable=False),
        sa.ForeignKeyConstraint(["project_id", "organization_id"], ["projects.id", "projects.organization_id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["workspace_id", "project_id"], ["engineering_workspaces.id", "engineering_workspaces.project_id"], ondelete="RESTRICT"),
        sa.CheckConstraint("workspace_id IS NULL OR project_id IS NOT NULL", name="ck_dp_audit_workspace_project"),
    )
    op.create_index("ix_dp_audit_organization", "package_configuration_audit_events", ["organization_id"])
    op.execute("""
CREATE FUNCTION satco_dp_immutable() RETURNS trigger LANGUAGE plpgsql AS $$ BEGIN RAISE EXCEPTION 'PATCH-051 immutable history'; END $$;
CREATE FUNCTION satco_dp_release_mutable() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
 IF NEW.registry_digest IS DISTINCT FROM OLD.registry_digest OR NEW.release_id IS DISTINCT FROM OLD.release_id
    OR NEW.core_contract_version IS DISTINCT FROM OLD.core_contract_version OR NEW.manifest_json IS DISTINCT FROM OLD.manifest_json THEN
   RAISE EXCEPTION 'PATCH-051 Registry release is immutable except current pointer';
 END IF;
 RETURN NEW;
END $$;
CREATE FUNCTION satco_dp_selection_count() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
 IF (SELECT count(*) FROM project_package_configuration_selections WHERE project_id=NEW.project_id AND configuration_revision=NEW.configuration_revision) NOT BETWEEN 1 AND 8 THEN RAISE EXCEPTION 'project selection count must be 1..8'; END IF;
 RETURN NULL;
END $$;
CREATE TRIGGER trg_dp_descriptors_immutable BEFORE UPDATE OR DELETE ON discipline_package_descriptors FOR EACH ROW EXECUTE FUNCTION satco_dp_immutable();
CREATE TRIGGER trg_dp_release_pointer_only BEFORE UPDATE ON discipline_package_registry_releases FOR EACH ROW EXECUTE FUNCTION satco_dp_release_mutable();
CREATE TRIGGER trg_dp_release_immutable BEFORE DELETE ON discipline_package_registry_releases FOR EACH ROW EXECUTE FUNCTION satco_dp_immutable();
CREATE TRIGGER trg_dp_memberships_immutable BEFORE UPDATE OR DELETE ON discipline_package_registry_memberships FOR EACH ROW EXECUTE FUNCTION satco_dp_immutable();
CREATE TRIGGER trg_dp_profiles_immutable BEFORE UPDATE OR DELETE ON discipline_package_compatibility_profiles FOR EACH ROW EXECUTE FUNCTION satco_dp_immutable();
CREATE TRIGGER trg_dp_profile_memberships_immutable BEFORE UPDATE OR DELETE ON discipline_package_registry_profile_memberships FOR EACH ROW EXECUTE FUNCTION satco_dp_immutable();
CREATE TRIGGER trg_dp_profile_members_immutable BEFORE UPDATE OR DELETE ON discipline_package_compatibility_members FOR EACH ROW EXECUTE FUNCTION satco_dp_immutable();
CREATE TRIGGER trg_dp_revisions_immutable BEFORE UPDATE OR DELETE ON project_package_configuration_revisions FOR EACH ROW EXECUTE FUNCTION satco_dp_immutable();
CREATE TRIGGER trg_dp_selections_immutable BEFORE UPDATE OR DELETE ON project_package_configuration_selections FOR EACH ROW EXECUTE FUNCTION satco_dp_immutable();
CREATE TRIGGER trg_dp_audit_immutable BEFORE UPDATE OR DELETE ON package_configuration_audit_events FOR EACH ROW EXECUTE FUNCTION satco_dp_immutable();
CREATE CONSTRAINT TRIGGER trg_dp_selection_count AFTER INSERT ON project_package_configuration_selections DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION satco_dp_selection_count();
CREATE CONSTRAINT TRIGGER trg_dp_revision_selection_count AFTER INSERT ON project_package_configuration_revisions DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION satco_dp_selection_count();
""")
    _apply_grants()


def _apply_grants() -> None:
    tables = ", ".join(f"public.{table}" for table in _PROJECTION_TABLES)
    op.execute(f"REVOKE ALL ON TABLE {tables} FROM PUBLIC, satco_runtime, satco_registry_installer")
    op.execute(f"GRANT SELECT ON TABLE {tables} TO satco_runtime")
    op.execute(f"GRANT SELECT, INSERT ON TABLE {tables} TO satco_registry_installer")
    op.execute("GRANT UPDATE (is_current) ON public.discipline_package_registry_releases TO satco_registry_installer")
    op.execute("GRANT SELECT, INSERT, UPDATE ON organization_package_configuration_heads, organization_package_selections TO satco_runtime")
    op.execute("GRANT SELECT, INSERT ON project_package_configuration_revisions, project_package_configuration_selections, package_configuration_audit_events TO satco_runtime")
    op.execute("GRANT SELECT, INSERT, UPDATE, DELETE ON project_package_configuration_heads TO satco_runtime")
    op.execute("REVOKE ALL ON organization_package_configuration_heads, organization_package_selections, project_package_configuration_revisions, project_package_configuration_selections, project_package_configuration_heads, package_configuration_audit_events FROM satco_registry_installer")
    op.execute("REVOKE EXECUTE ON FUNCTION satco_dp_immutable(), satco_dp_release_mutable(), satco_dp_selection_count() FROM PUBLIC, satco_runtime, satco_registry_installer")


def downgrade() -> None:
    _require_preflight()
    for table in (
        "discipline_package_registry_releases", "discipline_package_descriptors", "discipline_package_registry_memberships",
        "discipline_package_compatibility_profiles", "discipline_package_registry_profile_memberships", "discipline_package_compatibility_members",
        "organization_package_configuration_heads", "organization_package_selections", "project_package_configuration_revisions",
        "project_package_configuration_selections", "project_package_configuration_heads", "package_configuration_audit_events",
    ):
        count = op.get_bind().execute(sa.text(f"SELECT count(*) FROM {table}")).scalar_one()
        if count:
            raise RuntimeError("PATCH-051 downgrade is allowed only while all new tables are empty")
    op.execute("DROP FUNCTION IF EXISTS satco_dp_selection_count() CASCADE; DROP FUNCTION IF EXISTS satco_dp_release_mutable() CASCADE; DROP FUNCTION IF EXISTS satco_dp_immutable() CASCADE")
    for table in ("package_configuration_audit_events", "project_package_configuration_heads", "project_package_configuration_selections", "project_package_configuration_revisions", "organization_package_selections", "organization_package_configuration_heads", "discipline_package_compatibility_members", "discipline_package_registry_profile_memberships", "discipline_package_compatibility_profiles", "discipline_package_registry_memberships", "discipline_package_descriptors", "discipline_package_registry_releases"):
        op.drop_table(table)
    op.drop_constraint("uq_engineering_workspaces_id_project", "engineering_workspaces", type_="unique")
    op.drop_constraint("uq_projects_id_organization", "projects", type_="unique")
