#!/usr/bin/env python3
"""Read-only PATCH-051 deployment census; it never executes DDL or DML."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy import create_engine, text


EXPECTED_HEAD = "e04700000001"
KNOWN_DISCIPLINES = frozenset({"civil", "control", "mechanical", "electrical", "instrumentation", "process"})


def _canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode("utf-8")


def census(database_url: str, expected_head: str = EXPECTED_HEAD, registry_manifest: str | None = None) -> dict[str, object]:
    engine = create_engine(database_url)
    findings: list[str] = []
    try:
        with engine.connect().execution_options(isolation_level="AUTOCOMMIT") as connection:
            connection.execute(text("BEGIN TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY DEFERRABLE"))
            try:
                head = connection.execute(text("SELECT version_num FROM alembic_version")).scalar_one()
                rows = connection.execute(text("SELECT discipline, count(*) FROM engineering_workspaces GROUP BY discipline ORDER BY discipline")).all()
                nulls = connection.execute(text("SELECT count(*) FROM engineering_workspaces WHERE discipline IS NULL")).scalar_one()
                duplicate_candidates = connection.execute(text("SELECT count(*) FROM (SELECT project_id, discipline FROM engineering_workspaces GROUP BY project_id, discipline HAVING count(*) > 1) x")).scalar_one()
                project_orphans = connection.execute(text("SELECT count(*) FROM engineering_workspaces w LEFT JOIN projects p ON p.id=w.project_id WHERE p.id IS NULL")).scalar_one()
                fingerprint = connection.execute(text("SELECT md5(current_database() || ':' || inet_server_addr()::text || ':' || inet_server_port()::text)")).scalar_one()
                constraints = connection.execute(text("SELECT coalesce(string_agg(conname, ',' ORDER BY conname), '') FROM pg_constraint WHERE conrelid='engineering_workspaces'::regclass")).scalar_one()
                workspace_total_count = connection.execute(text("SELECT count(*) FROM engineering_workspaces")).scalar_one()
                workspace_checksum = connection.execute(text("SELECT coalesce(md5(string_agg(id::text || ':' || project_id::text || ':' || discipline, ',' ORDER BY id)), '') FROM engineering_workspaces")).scalar_one()
            finally:
                connection.execute(text("ROLLBACK"))
    except Exception as exc:
        return {"schema_version": 1, "overall": "FAIL", "findings": ["query_failure"], "error_category": type(exc).__name__}
    values = {str(value): count for value, count in rows}
    source_available = False
    if registry_manifest:
        try:
            source = json.loads(Path(registry_manifest).read_text(encoding="utf-8"))
            source_available = isinstance(source, dict) and isinstance(source.get("release_id"), str)
        except (OSError, ValueError):
            source_available = False
    if head != expected_head:
        findings.append("head_mismatch")
    if nulls or set(values).difference(KNOWN_DISCIPLINES):
        findings.append("unsupported_workspace_discipline")
    if duplicate_candidates:
        findings.append("duplicate_canonical_candidate")
    if project_orphans:
        findings.append("workspace_project_orphan")
    if not source_available:
        findings.append("historical_registry_source_unavailable")
    return {
        "schema_version": 1, "overall": "PASS" if not findings else "FAIL", "findings": findings,
        "database_fingerprint": fingerprint, "alembic_head": head,
        "transaction_at": datetime.now(timezone.utc).isoformat(), "workspace_disciplines": values,
        "workspace_null_count": nulls, "duplicate_canonical_candidates": duplicate_candidates,
        "workspace_project_orphans": project_orphans, "workspace_constraints": constraints,
        "workspace_total_count": workspace_total_count,
        "workspace_checksum": workspace_checksum,
        "historical_registry_source_available": source_available,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--database-url", required=True)
    parser.add_argument("--deployment-id", required=True)
    parser.add_argument("--output-dir", default="artifacts/patch-051/preflight")
    parser.add_argument("--expected-head", default=EXPECTED_HEAD)
    parser.add_argument("--registry-manifest", required=True)
    args = parser.parse_args()
    payload = census(args.database_url, args.expected_head, args.registry_manifest)
    payload["tool_commit"] = os.environ.get("GIT_COMMIT", "unknown")
    encoded = _canonical(payload)
    digest = hashlib.sha256(encoded).hexdigest()
    directory = Path(args.output_dir)
    directory.mkdir(parents=True, exist_ok=True)
    filename = f"{args.deployment_id}-{payload.get('database_fingerprint', 'unavailable')}.json"
    path = directory / filename
    path.write_bytes(encoded)
    print(json.dumps({"artifact": str(path), "sha256": digest, "overall": payload["overall"]}, separators=(",", ":")))
    return 0 if payload["overall"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
