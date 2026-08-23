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
: "${SATCO_OBJECT_RECOVERY_MANIFEST:?protected object inventory manifest required}"
command -v pg_dump >/dev/null
command -v age >/dev/null

umask 077
mkdir -p "$SATCO_BACKUP_TARGET_DIR"
set_id="$(python3 -c 'import uuid; print(uuid.uuid4())')"
started="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
plain="$(mktemp)"
object_plain="$(mktemp)"
trap 'rm -f "$plain" "$object_plain"' EXIT HUP INT TERM
encrypted="$SATCO_BACKUP_TARGET_DIR/$set_id.pgcustom.age"
object_encrypted="$SATCO_BACKUP_TARGET_DIR/$set_id.object-inventory.v1.json.age"
PGURL="$(cat "$BACKUP_DATABASE_URL_FILE")"
pg_dump --dbname="$PGURL" --format=custom --file="$plain"
age -r "$SATCO_BACKUP_ENCRYPTION_RECIPIENT" -o "$encrypted" "$plain"
python3 - "$SATCO_OBJECT_RECOVERY_MANIFEST" "$object_plain" <<'PY'
import datetime as dt, json, pathlib, re, sys
source, target = map(pathlib.Path, sys.argv[1:])
payload = json.loads(source.read_text(encoding="utf-8"))
assert set(payload) == {"schema", "cutoff_at", "entries"}
assert payload["schema"] == "supporting-file-object-inventory.v1"
dt.datetime.fromisoformat(payload["cutoff_at"].replace("Z", "+00:00"))
assert isinstance(payload["entries"], list)
previous = None
for entry in payload["entries"]:
    assert set(entry) == {"key_hash", "provider_version", "byte_size", "content_digest"}
    assert re.fullmatch(r"[0-9a-f]{64}", entry["key_hash"])
    assert isinstance(entry["provider_version"], str) and 1 <= len(entry["provider_version"]) <= 160
    assert isinstance(entry["byte_size"], int) and 1 <= entry["byte_size"] <= 26214400
    assert re.fullmatch(r"[0-9a-f]{64}", entry["content_digest"])
    key = (entry["key_hash"], entry["provider_version"])
    assert previous is None or previous < key
    previous = key
target.write_text(json.dumps(payload, sort_keys=True, separators=(",", ":")), encoding="utf-8")
PY
age -r "$SATCO_BACKUP_ENCRYPTION_RECIPIENT" -o "$object_encrypted" "$object_plain"
digest="$(sha256sum "$encrypted" | awk '{print $1}')"
object_digest="$(sha256sum "$object_encrypted" | awk '{print $1}')"
object_values="$(python3 - "$object_plain" <<'PY'
import json, sys
p=json.load(open(sys.argv[1], encoding='utf-8'))
print(p['cutoff_at'], len(p['entries']))
PY
)"
object_cutoff="${object_values%% *}"
object_count="${object_values#* }"
finished="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
python3 - "$SATCO_BACKUP_TARGET_DIR/$set_id.recovery-set.v1.json" "$set_id" "$started" "$finished" "$encrypted" "$digest" "$object_encrypted" "$object_digest" "$object_cutoff" "$object_count" "$SATCO_DEPLOYMENT_ID" "$SATCO_RELEASE_ID" "$SATCO_CONFIGURATION_ID" "$SATCO_EXPECTED_ALEMBIC_HEAD" "$SATCO_BACKUP_ENCRYPTION_KEY_REFERENCE" "$SATCO_OPERATIONAL_ACTOR_ID" <<'PY'
import json, pathlib, sys
path, set_id, started, finished, artifact, digest, object_artifact, object_digest, object_cutoff, object_count, deployment, release, config, head, key_ref, actor = sys.argv[1:]
pathlib.Path(path).write_text(json.dumps({
  "recovery_set_id": set_id, "started_at": started, "finished_at": finished,
  "deployment_id": deployment, "release_id": release,
  "configuration_id": config, "alembic_head": head,
  "database_artifact": pathlib.Path(artifact).name,
  "encrypted_artifact_id": pathlib.Path(artifact).name,
  "database_sha256": digest, "database_cutoff_at": object_cutoff,
  "database_status": "sealed", "encryption_key_reference": key_ref,
  "integrity_verification": "sha256", "operational_actor_id": actor,
  "job_id": set_id, "object_component": "inventory_manifest",
  "object_inventory_artifact": pathlib.Path(object_artifact).name,
  "object_inventory_sha256": object_digest,
  "object_cutoff_at": object_cutoff, "object_count": int(object_count),
  "object_status": "sealed",
  "verification_state": "sealed"
}, sort_keys=True, separators=(",", ":")), encoding="utf-8")
PY
rm -f "$plain" "$object_plain"
trap - EXIT HUP INT TERM
printf '%s\n' "$set_id"
