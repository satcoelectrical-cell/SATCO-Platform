# PATCH-046 Batch 1 — Authorized File Manifest

**Accepted / complete.** Contracts and persistence foundation only.

Authorized CREATE/MODIFY: deliverable enums, exceptions, models, schemas,
repository, migration `e04600000001`, contract/migration/repository-role tests,
and exact historical migration-head test assertions. These files establish
Deliverable/Revision identity, immutable history, idempotency/outbox and
database guards. No service orchestration, adapters, API, frontend, Evidence
mutation, file storage or PATCH-047+ behavior is authorized.

Prerequisites: PATCH-045 sole head `e04500000001`; current Project/Workspace,
Execution and Supporting File tables. Stop if a foreign aggregate needs direct
persistence ownership or the migration changes existing facts.
