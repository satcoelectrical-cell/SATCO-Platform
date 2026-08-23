#!/usr/bin/env sh
set -eu
: "${SATCO_COMPATIBLE_ROLLBACK:?explicit boolean required}"
if [ "$SATCO_COMPATIBLE_ROLLBACK" != "true" ]; then
  printf '%s\n' 'rollback-requires-isolated-recovery-set-restore' >&2
  exit 65
fi
"$(dirname "$0")/set-ops-mode.sh" read_only
printf '%s\n' 'compatible-artifact-rollback-ready'
