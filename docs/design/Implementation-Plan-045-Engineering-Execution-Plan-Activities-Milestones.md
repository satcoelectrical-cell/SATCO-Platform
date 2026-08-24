# Implementation Plan-045 — Engineering Execution Plan, Activities & Milestones

## Status

**ACCEPTED / COMPLETE.** Four independently reviewable batches implement only
IDS-045. Each requires an exact manifest before code changes.

## Batch 1 — Contracts and persistence foundation

Create execution enums, models, schemas/results, ports/exceptions, repository,
Alembic `e04500000001` and focused contract/model/migration/repository/role
tests. Establish exact tables, constraints, revision/history immutability,
dependency/tenant guards and no-commit repository reads/writes. Exclude
application orchestration, canonical adapters, API and UI. Stop if head is not
e044, DB guards require an accepted-design change, or foreign persistence is
needed.

## Batch 2 — Canonical composition, UoW and commands

Create only the Plan authorization/Foundation-read adapters, UoW and service,
then focused service/transaction/security/integration tests. Implement
establish, activity create/update/transition, dependencies and milestones;
final Foundation/parent/Workspace/authority checks; audit, idempotency,
expected-version locking and rollback. Exclude reads beyond command return,
transport and UI. Stop if a direct Foundation repository/Session or new role is
required.

## Batch 3 — Protected reads and transport/frontend

Add bounded Plan read service/repository support, request-scoped dependency,
thin eight-route router/main registration, typed frontend client/types, one
Project-detail Execution Plan component/styles and API/security/frontend tests.
Prove auth/context, protected outcomes, real data, accessibility/responsive
behavior, rationale controls and absence of raw IDs. Exclude dashboards,
schedule/Gantt, generic task boards and all PATCH-046+ work.

## Batch 4 — Final evidence

Run focused tests, adjacent Project/Foundation/Workspace/Audit regressions,
one backend suite, one frontend suite, migration/role checks, static/type/build,
security/non-disclosure, fake-data/scope/secret checks and QG-M1. Create only
validation/final-review evidence and PATCH status readiness artifacts. Any
failure requiring a product/design change stops the batch.

## Cross-batch requirements

Every batch performs focused test then smallest relevant adjacent regression,
independent review, remediation/re-review if needed and Human acceptance before
the next manifest. No batch may alter unrelated dirty work, introduce an outbox
without an async consumer, use noncanonical parent access, or implement
PATCH-046+ capabilities.
