# PATCH-047 Batch 1 — Authorized File Manifest

## Scope

Foundation/persistence only: closed domain contracts; separate Risk, Issue,
Decision, Change and Change Impact roots; append-only history, idempotency and
outbox records; no-commit repository/UoW foundation; and migration from
`e04600000001`.

## Authorized files

- CREATE `backend/app/enums/project_control.py` — closed standings/target kinds.
- CREATE `backend/app/models/project_control.py` — roots and persistence facts.
- CREATE `backend/app/schemas/project_control.py` — DTOs, commands/results.
- CREATE `backend/app/repositories/project_control_repository.py` — no-commit persistence.
- CREATE `backend/app/repositories/project_control_unit_of_work.py` — single-session boundary.
- CREATE `backend/migrations/versions/e04700000001_project_controls.py` — tables, constraints, indexes and ownership guards.
- CREATE `backend/tests/test_project_control_contracts.py` — contract/state tests.
- CREATE `backend/tests/test_project_control_migration.py` — upgrade/downgrade/head/no-backfill tests.
- CREATE `backend/tests/test_project_control_repository.py` — persistence/ordering/concurrency foundation tests.

## Exclusions and stop conditions

No canonical target adapter, application service, router, composition, UI,
foreign persistence access, blocker mutation, graph expansion or PATCH-048
behavior. Stop for an accepted-contract change, unsupported target authority,
or out-of-boundary file. Focused tests plus the smallest migration/Project
adjacent regression are required before independent review.
