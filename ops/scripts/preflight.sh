#!/usr/bin/env sh
set -eu

: "${SATCO_EXPECTED_ALEMBIC_HEAD:?required}"
: "${SATCO_RELEASE_MANIFEST_PATH:?required}"
: "${ALEMBIC_DATABASE_URL_FILE:?required}"
: "${SATCO_RUNTIME_DATABASE_ROLE:?required}"
: "${MIGRATION_DATABASE_ROLE:?required}"
: "${SATCO_REGISTRY_INSTALLER_DATABASE_ROLE:=satco_registry_installer}"
: "${SATCO_PREFLIGHT_PHASE:=after}"
case "$SATCO_PREFLIGHT_PHASE" in before|after) ;; *) exit 64 ;; esac

test -r "$SATCO_RELEASE_MANIFEST_PATH"
test -r "$ALEMBIC_DATABASE_URL_FILE"
export ALEMBIC_DATABASE_URL="$(cat "$ALEMBIC_DATABASE_URL_FILE")"
export RUNTIME_DATABASE_ROLE="$SATCO_RUNTIME_DATABASE_ROLE"
test "$SATCO_RUNTIME_DATABASE_ROLE" != "$MIGRATION_DATABASE_ROLE"

if [ "$SATCO_PREFLIGHT_PHASE" = "before" ]; then
  : "${SATCO_RUNTIME_DB_PASSWORD_FILE:?required}"
  : "${SATCO_REGISTRY_INSTALLER_DB_PASSWORD_FILE:?required}"
  : "${SATCO_PREUPGRADE_RECOVERY_SET_MANIFEST:?required}"
  test -r "$SATCO_RUNTIME_DB_PASSWORD_FILE"
  test -r "$SATCO_REGISTRY_INSTALLER_DB_PASSWORD_FILE"
  test -r "$SATCO_PREUPGRADE_RECOVERY_SET_MANIFEST"
  python3 - "$SATCO_PREUPGRADE_RECOVERY_SET_MANIFEST" <<'PY'
import json, sys
payload = json.load(open(sys.argv[1], encoding="utf-8"))
assert payload.get("verification_state") == "verified"
assert payload.get("database_status") == "verified"
assert isinstance(payload.get("database_sha256"), str) and len(payload["database_sha256"]) == 64
PY
  python3 - "$SATCO_RUNTIME_DATABASE_ROLE" "$SATCO_RUNTIME_DB_PASSWORD_FILE" <<'PY'
import pathlib, sys
import psycopg2
from psycopg2 import sql

role, password_path = sys.argv[1:]
password = pathlib.Path(password_path).read_text(encoding="utf-8").strip()
assert role == "satco_runtime" and len(password) >= 16
connection = psycopg2.connect(__import__("os").environ["ALEMBIC_DATABASE_URL"])
connection.autocommit = True
try:
    with connection.cursor() as cursor:
        cursor.execute("SELECT rolsuper, rolcreatedb, rolcreaterole, rolreplication, rolbypassrls FROM pg_roles WHERE rolname=%s", (role,))
        state = cursor.fetchone()
        if state is None:
            cursor.execute(
                sql.SQL("CREATE ROLE {} LOGIN NOINHERIT NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION NOBYPASSRLS PASSWORD %s").format(sql.Identifier(role)),
                (password,),
            )
        else:
            assert not any(state)
            cursor.execute(sql.SQL("ALTER ROLE {} PASSWORD %s").format(sql.Identifier(role)), (password,))
finally:
    connection.close()
PY
  python3 - "$SATCO_REGISTRY_INSTALLER_DATABASE_ROLE" "$SATCO_REGISTRY_INSTALLER_DB_PASSWORD_FILE" <<'PY'
import pathlib, sys
import psycopg2
from psycopg2 import sql
role, password_path = sys.argv[1:]
password = pathlib.Path(password_path).read_text(encoding="utf-8").strip()
assert role == "satco_registry_installer" and len(password) >= 16
connection = psycopg2.connect(__import__("os").environ["ALEMBIC_DATABASE_URL"])
connection.autocommit = True
try:
    with connection.cursor() as cursor:
        cursor.execute("SELECT rolsuper, rolcreatedb, rolcreaterole, rolreplication, rolbypassrls FROM pg_roles WHERE rolname=%s", (role,))
        state = cursor.fetchone()
        if state is None:
            cursor.execute(sql.SQL("CREATE ROLE {} LOGIN NOINHERIT NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION NOBYPASSRLS PASSWORD %s").format(sql.Identifier(role)), (password,))
        else:
            assert not any(state)
            cursor.execute(sql.SQL("ALTER ROLE {} PASSWORD %s").format(sql.Identifier(role)), (password,))
finally:
    connection.close()
PY
fi

if [ "$SATCO_EXPECTED_ALEMBIC_HEAD" = "e05100000001" ] || [ "$SATCO_EXPECTED_ALEMBIC_HEAD" = "e05100000002" ]; then
  : "${PATCH051_REQUIRE_PREFLIGHT:?required}"
  : "${PATCH051_REQUIRE_DIGEST:?required}"
  test -r "$PATCH051_REQUIRE_PREFLIGHT"
  test "$(wc -c < "$PATCH051_REQUIRE_PREFLIGHT" | tr -d ' ')" -gt 2
fi

heads="$(alembic heads)"
head_count="$(printf '%s\n' "$heads" | grep -c '(head)' || true)"
test "$head_count" -eq 1
printf '%s\n' "$heads" | grep -q "$SATCO_EXPECTED_ALEMBIC_HEAD"
if [ "$SATCO_PREFLIGHT_PHASE" = "after" ]; then
  alembic current | grep -q "$SATCO_EXPECTED_ALEMBIC_HEAD"
else
  # A first supported deployment may have no current revision yet; Alembic
  # must still be able to inspect it without stamping or direct repair.
  alembic current >/dev/null
fi
printf '%s\n' "preflight-$SATCO_PREFLIGHT_PHASE-pass"
