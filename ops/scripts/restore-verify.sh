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
assert p["object_component"] in ("not_applicable", "verified_empty")
assert p["verification_state"] == "sealed"
assert p["integrity_verification"] == "sha256"
print(p["database_artifact"], p["database_sha256"])
PY
)"
artifact="${artifact_and_digest%% *}"
expected_digest="${artifact_and_digest#* }"
test -f "$SATCO_BACKUP_TARGET_DIR/$artifact"
test "$(sha256sum "$SATCO_BACKUP_TARGET_DIR/$artifact" | awk '{print $1}')" = "$expected_digest"
test -n "${SATCO_RESTORE_AGE_IDENTITY_FILE:-}" || exit 64
plain="$(mktemp)"
trap 'rm -f "$plain"' EXIT HUP INT TERM
age -d -i "$SATCO_RESTORE_AGE_IDENTITY_FILE" -o "$plain" "$SATCO_BACKUP_TARGET_DIR/$artifact"
pg_restore --list "$plain" >/dev/null
restore_url="$(cat "$SATCO_RESTORE_DATABASE_URL_FILE")"
pg_restore --exit-on-error --no-owner --no-privileges --dbname="$restore_url" "$plain"
restored_head="$(psql "$restore_url" -Atc 'SELECT version_num FROM alembic_version')"
test "$restored_head" = "$SATCO_EXPECTED_ALEMBIC_HEAD"
python3 - "$SATCO_RECOVERY_SET_MANIFEST" <<'PY'
import datetime as dt, json, os, pathlib, sys, tempfile
path = pathlib.Path(sys.argv[1])
payload = json.loads(path.read_text(encoding="utf-8"))
payload["database_status"] = "verified"
payload["verification_state"] = "verified"
payload["verified_at"] = dt.datetime.now(dt.timezone.utc).isoformat()
with tempfile.NamedTemporaryFile("w", dir=path.parent, delete=False, encoding="utf-8") as stream:
    stream.write(json.dumps(payload, sort_keys=True, separators=(",", ":")))
    temporary = pathlib.Path(stream.name)
os.chmod(temporary, 0o600)
os.replace(temporary, path)
PY
rm -f "$plain"
trap - EXIT HUP INT TERM
printf '%s\n' 'restore-artifact-pass'
