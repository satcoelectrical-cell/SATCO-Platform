#!/usr/bin/env sh
set -eu
script_dir="$(dirname "$0")"
: "${SATCO_BACKUP_TARGET_DIR:?required}"
: "${ALEMBIC_DATABASE_URL_FILE:?required}"
export ALEMBIC_DATABASE_URL="$(cat "$ALEMBIC_DATABASE_URL_FILE")"
heads="$(alembic heads)"
test "$(printf '%s\n' "$heads" | grep -c '(head)' || true)" -eq 1
printf '%s\n' "$heads" | grep -q "${SATCO_EXPECTED_ALEMBIC_HEAD:?required}"
set_id="$(sh "$script_dir/backup.sh")"
export SATCO_RECOVERY_SET_MANIFEST="$SATCO_BACKUP_TARGET_DIR/$set_id.recovery-set.v1.json"
sh "$script_dir/restore-verify.sh"
export SATCO_PREUPGRADE_RECOVERY_SET_MANIFEST="$SATCO_RECOVERY_SET_MANIFEST"
SATCO_PREFLIGHT_PHASE=before sh "$script_dir/preflight.sh"
sh "$script_dir/set-ops-mode.sh" read_only
alembic upgrade "${SATCO_EXPECTED_ALEMBIC_HEAD:?required}"
SATCO_PREFLIGHT_PHASE=after sh "$script_dir/preflight.sh"
printf '%s\n' 'upgrade-ready-for-human-reopen'
