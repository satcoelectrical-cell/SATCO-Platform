"""PATCH-051 exact Workspace shadow cutover and final consistency guards.

Revision ID: e05100000003
Revises: e05100000002
"""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path

from alembic import op
import sqlalchemy as sa

revision = "e05100000003"
down_revision = "e05100000002"
branch_labels = None
depends_on = None


_MAPPINGS = {
    "electrical": "electrical",
    "instrumentation": "instrumentation",
    "control": "control_automation",
    "mechanical": "mechanical",
    "civil": "civil",
    "process": "process",
}


def upgrade() -> None:
    payload = _require_preflight()
    bind = op.get_bind()
    bind.execute(sa.text("SET LOCAL lock_timeout = '5s'"))
    bind.execute(sa.text("SET LOCAL statement_timeout = '60s'"))
    bind.execute(sa.text("LOCK TABLE engineering_workspaces IN SHARE ROW EXCLUSIVE MODE"))
    unknown = bind.execute(sa.text(
        "SELECT count(*) FROM engineering_workspaces "
        "WHERE discipline IS NULL OR discipline NOT IN ('electrical','instrumentation','control','mechanical','civil','process')"
    )).scalar_one()
    if unknown:
        raise RuntimeError("PATCH-051 M3 refuses unknown or null legacy Workspace disciplines")
    duplicates = bind.execute(sa.text(
        "SELECT count(*) FROM (SELECT project_id, discipline FROM engineering_workspaces "
        "GROUP BY project_id, discipline HAVING count(*) > 1) duplicates"
    )).scalar_one()
    if duplicates:
        raise RuntimeError("PATCH-051 M3 refuses duplicate canonical candidates")
    counts = dict(bind.execute(sa.text("SELECT discipline, count(*) FROM engineering_workspaces GROUP BY discipline")).all())
    if counts != payload["workspace_disciplines"] or sum(counts.values()) != payload["workspace_total_count"]:
        raise RuntimeError("PATCH-051 M3 census changed before cutover")
    checksum = bind.execute(sa.text("SELECT coalesce(md5(string_agg(id::text || ':' || project_id::text || ':' || discipline, ',' ORDER BY id)), '') FROM engineering_workspaces")).scalar_one()
    if checksum != payload["workspace_checksum"]:
        raise RuntimeError("PATCH-051 M3 Workspace checksum changed before cutover")
    malformed_exact_binding = bind.execute(sa.text(
        "SELECT count(*) FROM engineering_workspaces w "
        "WHERE w.bound_package_key IS NOT NULL AND NOT EXISTS ("
        "SELECT 1 FROM project_package_configuration_selections s "
        "WHERE s.project_id=w.project_id "
        "AND s.configuration_revision=w.bound_project_configuration_revision "
        "AND s.package_key=w.bound_package_key)"
    )).scalar_one()
    if malformed_exact_binding:
        raise RuntimeError("PATCH-051 M3 refuses malformed M2 exact-selection bindings")
    populated_shadow = bind.execute(sa.text(
        "SELECT count(*) FROM engineering_workspaces WHERE "
        "canonical_discipline_id IS NOT NULL OR package_binding_state IS NOT NULL "
        "OR bound_package_key IS NOT NULL OR bound_project_configuration_revision IS NOT NULL"
    )).scalar_one()
    if populated_shadow:
        raise RuntimeError("PATCH-051 M3 requires untouched M2 Workspace shadows")
    affected = 0
    for raw, canonical in _MAPPINGS.items():
        last_id = 0
        while True:
            ids = list(bind.execute(sa.text(
                "SELECT id FROM engineering_workspaces WHERE discipline=:raw "
                "AND canonical_discipline_id IS NULL AND id>:last_id ORDER BY id "
                "LIMIT 500 FOR UPDATE"
            ), {"raw": raw, "last_id": last_id}).scalars())
            if not ids:
                break
            result = bind.execute(sa.text(
                "UPDATE engineering_workspaces SET canonical_discipline_id=:canonical, "
                "package_binding_state='FUTURE_UNAVAILABLE_UNBOUND', "
                "bound_package_key=NULL, bound_project_configuration_revision=NULL "
                "WHERE id = ANY(:ids)"
            ), {"ids": ids, "canonical": canonical})
            if result.rowcount != len(ids):
                raise RuntimeError("PATCH-051 M3 chunk affected-count mismatch")
            affected += result.rowcount
            last_id = ids[-1]
    if affected != payload["workspace_total_count"]:
        raise RuntimeError("PATCH-051 M3 total affected-count mismatch")
    remaining = bind.execute(sa.text(
        "SELECT count(*) FROM engineering_workspaces WHERE canonical_discipline_id IS NULL OR package_binding_state IS NULL"
    )).scalar_one()
    if remaining:
        raise RuntimeError("PATCH-051 M3 backfill did not cover every Workspace")
    bind.execute(sa.text("ALTER TABLE engineering_workspaces VALIDATE CONSTRAINT fk_dp_workspace_exact_selection"))
    op.alter_column("engineering_workspaces", "package_binding_state", nullable=False)
    op.execute("""
CREATE FUNCTION satco_dp_workspace_binding_guard() RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE current_revision bigint;
BEGIN
  IF NEW.package_binding_state='OPERATIONAL_PACKAGE_BOUND' THEN
    IF NEW.canonical_discipline_id IS NULL OR NEW.bound_package_key IS NULL OR NEW.bound_project_configuration_revision IS NULL THEN RAISE EXCEPTION 'operational Workspace requires exact package binding'; END IF;
    SELECT head.current_revision INTO current_revision FROM project_package_configuration_heads AS head WHERE head.project_id=NEW.project_id;
    IF current_revision IS NULL OR current_revision<>NEW.bound_project_configuration_revision OR NOT EXISTS (SELECT 1 FROM project_package_configuration_selections s WHERE s.project_id=NEW.project_id AND s.configuration_revision=NEW.bound_project_configuration_revision AND s.package_key=NEW.bound_package_key) THEN RAISE EXCEPTION 'Workspace binding must equal current Project selection'; END IF;
  ELSIF NEW.package_binding_state='FUTURE_UNAVAILABLE_UNBOUND' THEN
    IF NEW.canonical_discipline_id IS NULL OR NEW.bound_package_key IS NOT NULL OR NEW.bound_project_configuration_revision IS NOT NULL THEN RAISE EXCEPTION 'future Workspace must be unbound'; END IF;
  ELSIF NEW.package_binding_state='LEGACY_UNRESOLVED' THEN
    IF NEW.canonical_discipline_id IS NOT NULL OR NEW.bound_package_key IS NOT NULL OR NEW.bound_project_configuration_revision IS NOT NULL THEN RAISE EXCEPTION 'unresolved Workspace must retain no derived identity'; END IF;
  ELSE RAISE EXCEPTION 'unknown Workspace binding state'; END IF;
  RETURN NULL;
END $$;
CREATE FUNCTION satco_dp_project_head_binding_guard() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
  IF EXISTS (SELECT 1 FROM engineering_workspaces w WHERE w.project_id=NEW.project_id AND w.package_binding_state='OPERATIONAL_PACKAGE_BOUND' AND w.bound_project_configuration_revision<>NEW.current_revision) THEN RAISE EXCEPTION 'Project head advance leaves stale Workspace binding'; END IF;
  RETURN NULL;
END $$;
CREATE CONSTRAINT TRIGGER trg_dp_workspace_binding_guard AFTER INSERT OR UPDATE OF project_id,canonical_discipline_id,package_binding_state,bound_package_key,bound_project_configuration_revision ON engineering_workspaces DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION satco_dp_workspace_binding_guard();
CREATE CONSTRAINT TRIGGER trg_dp_project_head_binding_guard AFTER INSERT OR UPDATE OF current_revision ON project_package_configuration_heads DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION satco_dp_project_head_binding_guard();
REVOKE EXECUTE ON FUNCTION satco_dp_workspace_binding_guard(), satco_dp_project_head_binding_guard() FROM PUBLIC, satco_runtime, satco_registry_installer;
""")
    bind.execute(sa.text("SET CONSTRAINTS ALL IMMEDIATE"))


def downgrade() -> None:
    # After any cutover value is written, accepted recovery is forward-only.
    used = op.get_bind().execute(sa.text("SELECT EXISTS (SELECT 1 FROM engineering_workspaces WHERE canonical_discipline_id IS NOT NULL OR package_binding_state IS NOT NULL)" )).scalar_one()
    if used:
        raise RuntimeError("PATCH-051 M3 downgrade is forbidden after cutover; recover forward")
    op.execute("DROP FUNCTION IF EXISTS satco_dp_project_head_binding_guard() CASCADE; DROP FUNCTION IF EXISTS satco_dp_workspace_binding_guard() CASCADE")
    op.alter_column("engineering_workspaces", "package_binding_state", nullable=True)


def _require_preflight() -> dict[str, object]:
    path = os.environ.get("PATCH051_REQUIRE_PREFLIGHT")
    digest = os.environ.get("PATCH051_REQUIRE_DIGEST")
    if not path or not digest or len(digest) != 64:
        raise RuntimeError("PATCH-051 M3 requires a preflight artifact and digest")
    try:
        raw = Path(path).read_bytes()
        payload = json.loads(raw)
    except (OSError, ValueError) as exc:
        raise RuntimeError("PATCH-051 M3 preflight artifact is unreadable") from exc
    required = {"workspace_disciplines", "workspace_total_count", "workspace_checksum", "workspace_null_count", "duplicate_canonical_candidates", "workspace_project_orphans", "historical_registry_source_available"}
    if hashlib.sha256(raw).hexdigest() != digest or payload.get("overall") != "PASS" or payload.get("alembic_head") != "e05100000002" or not required.issubset(payload) or payload.get("workspace_null_count") != 0 or payload.get("duplicate_canonical_candidates") != 0 or payload.get("workspace_project_orphans") != 0 or payload.get("historical_registry_source_available") is not True:
        raise RuntimeError("PATCH-051 M3 preflight artifact is not a matching PASS")
    if not isinstance(payload["workspace_disciplines"], dict) or not isinstance(payload["workspace_total_count"], int) or not isinstance(payload["workspace_checksum"], str):
        raise RuntimeError("PATCH-051 M3 preflight artifact has invalid census fields")
    return payload
