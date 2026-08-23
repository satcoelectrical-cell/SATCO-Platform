#!/usr/bin/env sh
set -eu

: "${SATCO_BACKUP_TARGET_DIR:?independent mounted target required}"
: "${SATCO_BACKUP_ENCRYPTION_RECIPIENT:?required}"
: "${SATCO_BACKUP_ENCRYPTION_KEY_REFERENCE:?required}"
: "${SATCO_DEPLOYMENT_ID:?required}"
: "${SATCO_RELEASE_ID:?required}"
: "${SATCO_CONFIGURATION_ID:?required}"
: "${SATCO_EXPECTED_ALEMBIC_HEAD:?required}"
: "${SATCO_OPERATIONAL_ACTOR_ID:?required}"
: "${BACKUP_DATABASE_URL_FILE:?recovery-only database URL file required}"
command -v pg_dump >/dev/null
command -v age >/dev/null

umask 077
mkdir -p "$SATCO_BACKUP_TARGET_DIR"
set_id="$(python3 -c 'import uuid; print(uuid.uuid4())')"
started="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
plain="$(mktemp)"
trap 'rm -f "$plain"' EXIT HUP INT TERM
encrypted="$SATCO_BACKUP_TARGET_DIR/$set_id.pgcustom.age"
PGURL="$(cat "$BACKUP_DATABASE_URL_FILE")"
pg_dump --dbname="$PGURL" --format=custom --file="$plain"
age -r "$SATCO_BACKUP_ENCRYPTION_RECIPIENT" -o "$encrypted" "$plain"
digest="$(sha256sum "$encrypted" | awk '{print $1}')"
finished="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
python3 - "$SATCO_BACKUP_TARGET_DIR/$set_id.recovery-set.v1.json" "$set_id" "$started" "$finished" "$encrypted" "$digest" "$SATCO_DEPLOYMENT_ID" "$SATCO_RELEASE_ID" "$SATCO_CONFIGURATION_ID" "$SATCO_EXPECTED_ALEMBIC_HEAD" "$SATCO_BACKUP_ENCRYPTION_KEY_REFERENCE" "$SATCO_OPERATIONAL_ACTOR_ID" <<'PY'
import json, pathlib, sys
path, set_id, started, finished, artifact, digest, deployment, release, config, head, key_ref, actor = sys.argv[1:]
pathlib.Path(path).write_text(json.dumps({
  "recovery_set_id": set_id, "started_at": started, "finished_at": finished,
  "deployment_id": deployment, "release_id": release,
  "configuration_id": config, "alembic_head": head,
  "database_artifact": pathlib.Path(artifact).name,
  "encrypted_artifact_id": pathlib.Path(artifact).name,
  "database_sha256": digest, "database_cutoff_at": finished,
  "database_status": "sealed", "encryption_key_reference": key_ref,
  "integrity_verification": "sha256", "operational_actor_id": actor,
  "job_id": set_id, "object_component": "not_applicable",
  "verification_state": "sealed"
}, sort_keys=True, separators=(",", ":")), encoding="utf-8")
PY
rm -f "$plain"
trap - EXIT HUP INT TERM
printf '%s\n' "$set_id"
