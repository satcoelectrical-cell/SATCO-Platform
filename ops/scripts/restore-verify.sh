#!/usr/bin/env sh
set -eu

: "${SATCO_RECOVERY_SET_MANIFEST:?required}"
: "${SATCO_BACKUP_TARGET_DIR:?required}"
: "${SATCO_RESTORE_DATABASE_URL_FILE:?isolated restore database required}"
: "${SATCO_EXPECTED_ALEMBIC_HEAD:?required}"
command -v age >/dev/null
command -v pg_restore >/dev/null
command -v psql >/dev/null

artifact_and_digest="$(python3 - "$SATCO_RECOVERY_SET_MANIFEST" <<'PY'
import json, sys
p=json.load(open(sys.argv[1], encoding='utf-8'))
assert p["object_component"] == "inventory_manifest"
assert p["object_status"] == "sealed"
assert p["database_cutoff_at"] == p["object_cutoff_at"]
assert p["verification_state"] == "sealed"
assert p["integrity_verification"] == "sha256"
print(p["database_artifact"], p["database_sha256"], p["object_inventory_artifact"], p["object_inventory_sha256"])
PY
)"
set -- $artifact_and_digest
artifact="$1"; expected_digest="$2"; object_artifact="$3"; expected_object_digest="$4"
test -f "$SATCO_BACKUP_TARGET_DIR/$artifact"
test -f "$SATCO_BACKUP_TARGET_DIR/$object_artifact"
test "$(sha256sum "$SATCO_BACKUP_TARGET_DIR/$artifact" | awk '{print $1}')" = "$expected_digest"
test "$(sha256sum "$SATCO_BACKUP_TARGET_DIR/$object_artifact" | awk '{print $1}')" = "$expected_object_digest"
test -n "${SATCO_RESTORE_AGE_IDENTITY_FILE:-}" || exit 64
plain="$(mktemp)"
object_plain="$(mktemp)"
database_objects="$(mktemp)"
trap 'rm -f "$plain" "$object_plain" "$database_objects"' EXIT HUP INT TERM
age -d -i "$SATCO_RESTORE_AGE_IDENTITY_FILE" -o "$plain" "$SATCO_BACKUP_TARGET_DIR/$artifact"
age -d -i "$SATCO_RESTORE_AGE_IDENTITY_FILE" -o "$object_plain" "$SATCO_BACKUP_TARGET_DIR/$object_artifact"
pg_restore --list "$plain" >/dev/null
restore_url="$(cat "$SATCO_RESTORE_DATABASE_URL_FILE")"
pg_restore --exit-on-error --no-owner --no-privileges --dbname="$restore_url" "$plain"
restored_head="$(psql "$restore_url" -Atc 'SELECT version_num FROM alembic_version')"
test "$restored_head" = "$SATCO_EXPECTED_ALEMBIC_HEAD"
psql "$restore_url" -At -F '|' -c "SELECT storage_key,object_version,byte_size,content_digest FROM supporting_file_assets ORDER BY storage_key,object_version" > "$database_objects"
python3 - "$object_plain" "$database_objects" <<'PY'
import hashlib, json, pathlib, sys
manifest=json.loads(pathlib.Path(sys.argv[1]).read_text(encoding='utf-8'))
assert set(manifest) == {'schema','cutoff_at','entries'}
assert manifest['schema'] == 'supporting-file-object-inventory.v1'
actual=[]
for line in pathlib.Path(sys.argv[2]).read_text(encoding='utf-8').splitlines():
    if line:
        storage_key, version, size, digest = line.split('|')
        key_hash = hashlib.sha256(storage_key.encode('utf-8')).hexdigest()
        actual.append({'key_hash':key_hash,'provider_version':version,'byte_size':int(size),'content_digest':digest})
actual.sort(key=lambda item: (item['key_hash'], item['provider_version']))
assert actual == manifest['entries']
PY
python3 - "$SATCO_RECOVERY_SET_MANIFEST" <<'PY'
import datetime as dt, json, os, pathlib, sys, tempfile
path = pathlib.Path(sys.argv[1])
payload = json.loads(path.read_text(encoding="utf-8"))
payload["database_status"] = "verified"
payload["object_status"] = "verified"
payload["verification_state"] = "verified"
payload["verified_at"] = dt.datetime.now(dt.timezone.utc).isoformat()
with tempfile.NamedTemporaryFile("w", dir=path.parent, delete=False, encoding="utf-8") as stream:
    stream.write(json.dumps(payload, sort_keys=True, separators=(",", ":")))
    temporary = pathlib.Path(stream.name)
os.chmod(temporary, 0o600)
os.replace(temporary, path)
PY
rm -f "$plain" "$object_plain" "$database_objects"
trap - EXIT HUP INT TERM
printf '%s\n' 'restore-artifact-pass'
