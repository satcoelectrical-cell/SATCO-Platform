# PATCH-044 Batch 1 Authorized File Manifest

## Authority and scope

Batch 1 — Contracts and Persistence Foundation, S01–S04. Preparation and
implementation are authorized by the standing PATCH-044 Human authority. No
Batch 2+ capability is authorized.

## Production boundary

CREATE:

- `backend/app/enums/project_foundation.py` — closed enums/stage rank;
- `backend/app/models/project_foundation.py` — exact four ORM records;
- `backend/app/schemas/project_foundation.py` — closed command/read/results;
- `backend/app/ports/project_foundation.py` — repository/UoW/source/policy ports;
- `backend/app/exceptions/project_foundation.py` — internal closed failures;
- `backend/app/repositories/project_foundation_repository.py` — no-commit
  persistence and deterministic queries;
- `backend/app/repositories/project_foundation_unit_of_work.py` — one-Session
  UoW and bounded shared Audit staging;
- `backend/migrations/versions/e04400000001_project_foundation.py` — additive
  schema, guards, roles and downgrade.

MODIFY:

- `backend/app/enums/__init__.py` — exports only;
- `backend/app/models/__init__.py` — metadata registration only.

## Test boundary

CREATE:

- `backend/tests/test_project_foundation_contracts.py`;
- `backend/tests/test_project_foundation_domain.py`;
- `backend/tests/test_project_foundation_migration.py`;
- `backend/tests/test_project_foundation_repository.py`.

MODIFY only exact authoritative-head assertions:

- `backend/tests/test_engineering_experience_capture_migration.py`;
- `backend/tests/test_onboarding_migration.py`;
- `backend/tests/test_technical_report_migration.py`;
- `backend/tests/test_customer_organization_migration.py`;
- `backend/tests/test_organizational_memory_migration.py`;
- `backend/tests/test_supporting_file_migration.py`;
- `backend/tests/test_operations_config.py`;
- `backend/tests/test_operations_health.py`;
- `backend/tests/test_operations_security.py`.

Historical e043 revision/parent assertions must remain. No generic head check
may replace an exact assertion.

## Evidence

Closed DTO negative probes; absent-root truthfulness; state/stage/readiness
rules; exact schema matrix; upgrade/downgrade/re-upgrade; sole head; direct-SQL
tenant/source/history/ordinal guards; runtime ownership/grants; repository
no-commit/locking/reorder; rollback/Audit staging; adjacent migration regression;
static imports, prohibited-pattern scan and `git diff --check`.

## Prohibited responsibilities

No canonical source adapter, application service, authorization orchestration,
router, main registration, frontend, foreign repository access, task,
deliverable, risk, graph, AI, Wizard, closeout, fake data, Batch 2+ or PATCH-045.

## Stop conditions

Stop for non-e043 head, accepted-design change, new shared DB role/schema,
unavoidable out-of-boundary file, source mutation authority, repository commit,
or any direct-SQL guard that cannot enforce the IDS contract.
