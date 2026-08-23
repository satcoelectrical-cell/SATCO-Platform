# PATCH-042 Batch 3 Authorized File Manifest

Scope: migration preflight, backup/recovery-set/restore scripts, RPO mode,
upgrade/rollback orchestration, and isolated fixture validation.

Authorized: CREATE `ops/scripts/preflight.sh`, `backup.sh`, `restore-verify.sh`,
`set-ops-mode.sh`, `upgrade.sh`, `rollback.sh`, `backend/tests/test_operations_recovery.py`;
MODIFY `backend/app/core/operations.py` and Batch-1 tests only for dual write
gate. Focused final-readiness reconciliation also authorizes MODIFY
`docker-compose.production.yml`, `ops/nginx/default.conf`,
`backend/app/core/config.py`, `backend/tests/test_production_topology.py`, and
`backend/tests/test_operations_config.py` solely to mount and enforce the same
signed recovery mode at both the edge and backend. No Alembic migration is
authorized.

Prohibited: runtime backup credentials, schema stamping, direct DB repair, object
domain behavior. Stop if safe read-only cannot be enforced.
