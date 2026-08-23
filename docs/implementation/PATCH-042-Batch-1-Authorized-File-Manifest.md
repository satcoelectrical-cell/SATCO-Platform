# PATCH-042 Batch 1 Authorized File Manifest

Scope: production configuration, release identity, generic health, protected
operations diagnostics, and request write-mode gate only.

Authorized: MODIFY `backend/app/core/config.py`, `backend/app/core/database.py`,
`backend/app/main.py`; CREATE `backend/app/core/operations.py`,
`backend/app/api/v1/routers/operations.py`, `ops/release-manifest.v1.schema.json`,
`ops/release-manifest.example.v1.json`, `backend/tests/test_operations_config.py`,
`backend/tests/test_operations_health.py`.

Prohibited: Compose/edge/TLS, backups, migration, object data plane, business
domain semantics, PATCH-043. Stop for EDS/IDS change, unsafe health disclosure,
or need for a migration.
