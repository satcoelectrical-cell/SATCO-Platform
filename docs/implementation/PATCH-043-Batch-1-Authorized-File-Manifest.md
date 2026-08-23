# PATCH-043 Batch 1 Authorized File Manifest

## Authority and scope

Human PATCH-043 implementation authority is granted. This manifest authorizes
only Batch 1/S01–S04: closed contracts, pure Asset Aggregate, persistence
foundation, migration and no-commit repository. It excludes adapters, object
credentials, streaming, scanner, service orchestration, routes, Report/Memory
integration and frontend.

## Authorized files

CREATE:

- `backend/app/enums/supporting_file.py` — closed lifecycle, reservation,
  scan and media vocabulary.
- `backend/app/exceptions/supporting_file.py` — stable domain exceptions.
- `backend/app/models/supporting_file_command.py` — value objects, canonical
  serialization/digest and pure command/event contracts.
- `backend/app/models/supporting_file.py` — Aggregate and ORM records.
- `backend/app/schemas/supporting_file.py` — closed transport-neutral DTOs.
- `backend/app/ports/supporting_file.py` — inward repository and collaborator
  protocols.
- `backend/app/repositories/supporting_file_repository.py` — no-commit,
  deterministic persistence mapping.
- `backend/migrations/versions/e04300000001_supporting_files.py` — additive
  parented migration and DB guards.
- `backend/tests/test_supporting_file_contracts.py`
- `backend/tests/test_supporting_file_aggregate.py`
- `backend/tests/test_supporting_file_schemas.py`
- `backend/tests/test_supporting_file_migration.py`
- `backend/tests/test_supporting_file_database_roles.py`
- `backend/tests/test_supporting_file_repository.py`

MODIFY:

- `backend/app/enums/__init__.py`, `backend/app/models/__init__.py`,
  `backend/migrations/env.py` — necessary package/metadata registration only.
- `backend/app/models/evidence.py` — durable one-way link sealing marker only.
- `backend/tests/test_onboarding_migration.py`,
  `backend/tests/test_organizational_memory_migration.py`,
  `backend/tests/test_technical_report_migration.py`,
  `backend/tests/test_customer_organization_migration.py`,
  `backend/tests/test_operations_config.py`,
  `backend/tests/test_operations_health.py`,
  `backend/tests/test_operations_security.py` — exact head expectation only,
  preserving historic e041 parent/history assertions.

## Preconditions and acceptance

Verified parent is `e04100000001`. Batch accepts only if contracts reject
invalid scope/name/type/digest/key/lifecycle; Aggregate preserves byte metadata
and terminal lifecycle; direct SQL guards/role policy/migration graph are
covered; repository never commits; and all focused plus adjacent migration
tests pass.

## Stop conditions

Stop for head drift, accepted contract change, external object/scanner need,
foreign canonical persistence access, a shared role/DDL change outside this
manifest, or any Batch 2+ behavior. `git diff --check` and exact path scope are
mandatory.
