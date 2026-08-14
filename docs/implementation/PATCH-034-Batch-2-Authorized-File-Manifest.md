# PATCH-034 — Batch 2 Authorized File Manifest

## 1. Manifest Control

| Field | Value |
|---|---|
| Related PATCH | PATCH-034 — Engineering Organizational Memory |
| Authorized batch | Batch 2 — Credential and Persistence Foundation |
| Implementation steps | S03–S04 only |
| Batch 1 | ACCEPTED / COMPLETE |
| Governing EDS | EDS-034 — ACCEPTED / COMPLETE |
| Governing IDS | IDS-034 — ACCEPTED / COMPLETE |
| Governing plan | Implementation-Plan-034 — ACCEPTED / COMPLETE |
| IRR-034 | PASS |
| Human Batch 2 preparation authority | GRANTED |
| Human manifest reconciliation and focused-remediation authority | GRANTED |
| Manifest status | RECONCILED / IMPLEMENTATION VALIDATION IN PROGRESS |
| Batch 2 implementation authority | GRANTED — S03–S04 and focused reconciliation only |
| Batch 3 and later authority | NOT GRANTED |
| Commit / push authority | NOT GRANTED |
| Date | 2026-08-13 |

This manifest records the exact implementation boundary; authority remains
limited to the stated S03–S04 and focused-reconciliation responsibilities.

The initial six-file boundary was reconciled after implementation validation
identified one existing Technical Report regression that asserted the obsolete
repository head. The only added authority is the exact assertion-only update
to `backend/tests/test_technical_report_migration.py`; its PATCH-032 migration
history and all other behavior remain unchanged.

## 2. Verified Repository Assumptions

The repository has one Alembic head:

```text
e03200000001 (head)
```

The Batch-2 revision is therefore fixed as `e03400000001`, with
`down_revision = "e03200000001"`. It must remain the sole repository head.
There is no PATCH-033 migration and no missing intermediate migration.

The existing migration boundary already requires an explicit
`ALEMBIC_DATABASE_URL`, derives its schema-owner role from that URL, requires a
distinct runtime role, and fails when the roles coincide. Current repository
and isolated-test conventions use schema owner `satco` and restricted runtime
role `satco_runtime`. The test bootstrap already creates/verifies the runtime
role and upgrades dynamically to the current repository head. Consequently:

- `backend/migrations/env.py` requires no change;
- `backend/tests/conftest.py` requires no change;
- no environment, secret, credential, container, or deployment file is in the
  Batch-2 boundary; and
- no shared Audit table/schema change is required. Existing `audit_logs` is a
  referenced dependency only.

The root foreign key to `technical_reports.id` is an accepted referential
constraint. It grants no Organizational Memory code access to the Technical
Report ORM, repository, Session, or UoW and authorizes no foreign-table
mutation.

## 3. Exact Authorized File Boundary

### 3.1 Production and Migration Files

| Path | Action | Step | Exact responsibility and necessity | Dependencies | Prohibited responsibilities |
|---|---|---|---|---|---|
| `backend/migrations/versions/e03400000001_organizational_memory.py` | CREATE | S03 | Add and reversibly remove the four accepted tables: `organizational_memories`, `organizational_memory_standing_history`, `organizational_memory_events_outbox`, and `organizational_memory_idempotency`; exact columns, defaults, FKs, checks, unique/partial indexes, canonical JSON/digest validators, lineage/root/history/side-record functions and triggers, ownership, revocations, and least-privilege runtime grants. Required because all authoritative direct-SQL invariants and role ownership originate at the database boundary. | Parent `e03200000001`; PostgreSQL digest support already present; accepted Batch-1 contracts; existing Organization, Workspace, Project, User, Technical Report, and Audit schema. | No canonical-table mutation; no Audit schema change; no data backfill from Technical Reports; no service/UoW behavior; no outbox dispatch; no configuration or credential creation; no second head. |
| `backend/app/core/database.py` | MODIFY | S03 | Add the minimum fail-closed Organizational Memory runtime/schema-owner verifier: distinct roles, runtime role attributes/membership/schema authority, required tables/functions/triggers, exact ownership, exact table/column grants, forbidden DDL/DELETE/TRIGGER/function execution, and enabled-guard checks. Required by IDS-034 startup/deployment role-boundary enforcement. | Existing `runtime_database_url` and Technical Report verifier convention; S03 migration-owned objects. | No credential values or fallback shared role; no connection/session redesign; no Technical Report semantic change; no application authorization or command behavior. |
| `backend/app/repositories/organizational_memory_repository.py` | CREATE | S04 | Define the SQLAlchemy persistence records/mappings local to the memory repository boundary and implement the accepted no-commit repository: add root, scoped/source lookup, expected-version standing persistence, append-only history staging, and canonical ordered active-candidate reads using `ActiveMemoryCriteria`/`MemoryCandidatePage`. Required because the accepted plan assigns all Batch-2 mapping and repository implementation to S04 and authorizes no separate ORM file. | Batch-1 Aggregate, value records, and repository port; completed S03 schema. | No commit or transaction ownership; no authorization/final-recheck policy; no Audit/outbox/idempotency collaborator implementation; no Technical Report/provenance repository access; no application reads/pagination loop/token handling; no service/router/composition behavior. |

Production/migration file count: **3**.

### 3.2 Test Files

| Path | Action | Step | Exact responsibility and necessity | Dependencies | Prohibited responsibilities |
|---|---|---|---|---|---|
| `backend/tests/test_organizational_memory_migration.py` | CREATE | S03–S04 | Prove revision/head/round-trip, exact schema/functions/triggers/indexes/FKs/checks, canonical JSON/digest validation, root/history/outbox/idempotency constraints, and the complete owner/direct-SQL bypass matrix. | Owner-engine and dynamic-head fixtures already provided by existing `conftest.py`; S03 migration. | No shared fixture modification, application service tests, canonical adapters, or foreign-table mutation beyond bounded fixtures. |
| `backend/tests/test_organizational_memory_database_roles.py` | CREATE | S03 | Prove schema-owner/runtime identity and attributes, ownership, exact grants, runtime DDL/DELETE/trigger-disable/function-execution denial, permitted bounded DML, and fail-closed startup verification. | Existing isolated schema-owner/runtime test convention; `app/core/database.py`; S03 migration. | No secrets/config changes, role weakening, role creation in production configuration, or application authorization testing. |
| `backend/tests/test_organizational_memory_repository.py` | CREATE | S04 | Prove root/history mapping, exact round-trip, source uniqueness, scoped lookup, expected-version persistence, canonical active ordering/candidate bounds, no-commit behavior, and repository/direct-SQL parity including concurrent uniqueness. | S03 schema; Batch-1 Aggregate/contracts; S04 repository. | No UoW orchestration, success/rejection Audit behavior, idempotency replay, outbox dispatch, canonical adapters, protected application pagination, API, or later-batch behavior. |
| `backend/tests/test_technical_report_migration.py` | MODIFY | S03 regression reconciliation | Change only the exact repository-head assertion from the former PATCH-032 head to the new authoritative `e03400000001` head. Required to preserve the existing PATCH-032 migration regression after the linear PATCH-034 migration. | Existing PATCH-032 migration tests; completed S03 migration. | No changes to PATCH-032 downgrade/re-upgrade targets, schema assertions, migration-history evidence, or any other Technical Report behavior. |

Test file count: **4**.

### 3.3 Complete Reconciled Seven-file Boundary

```text
MODIFY backend/app/core/database.py
CREATE backend/app/repositories/organizational_memory_repository.py
CREATE backend/migrations/versions/e03400000001_organizational_memory.py
CREATE backend/tests/test_organizational_memory_migration.py
CREATE backend/tests/test_organizational_memory_database_roles.py
CREATE backend/tests/test_organizational_memory_repository.py
MODIFY backend/tests/test_technical_report_migration.py
```

No other file may be created, modified, staged, or committed under Batch 2.

## 4. S03 / S04 Mapping

### S03 — Migration, Schema, and Role Boundary

S03 is limited to:

- the linear `e03200000001 -> e03400000001` migration;
- exact root/history/outbox/idempotency tables and reversible downgrade;
- accepted constraints, indexes, FKs, validators, functions, triggers, ownership,
  revocations, and grants;
- schema-owner `satco` versus runtime `satco_runtime` separation without shared
  credentials; and
- fail-closed runtime verification and focused migration/role evidence.

S03 creates persistence structure only. The outbox and idempotency tables are
authorized persistence foundations, not behavioral integration.

### S04 — Repository and Direct-SQL Invariants

S04 is limited to:

- mapping between accepted Batch-1 Aggregates/value records and the S03 schema;
- root insertion and scoped/source lookup;
- expected-version persistence of the only accepted active-to-terminal changes;
- append-only standing-history staging;
- bounded candidate retrieval in canonical
  `(admitted_at DESC, memory_id ASC)` order; and
- repository, concurrency/uniqueness, and direct-SQL invariant evidence.

S04 does not implement application-level authorized result construction,
pagination/continuation loops, transaction/UoW ownership, or command execution.

## 5. Exact Persistence and Role Evidence Expectations

A separately authorized Batch-2 implementation must materially prove:

1. `alembic heads` reports only `e03400000001` after creation; its parent is
   exactly `e03200000001`; upgrade, downgrade to the parent, and re-upgrade are
   reproducible.
2. All IDS-034 §16.1 columns, PostgreSQL types, nullability, defaults, FKs,
   checks, unique constraints, partial indexes, ordering indexes, and
   non-cascading ownership relationships are exact.
3. The five immutable JSON validators and four guard functions have the exact
   accepted signatures, are schema-owner-owned, are not alterable/executable by
   runtime, and reject unknown/missing keys, invalid types/literals, oversized
   payloads, noncanonical content, digest incoherence, and mismatched
   operation/result discriminators.
4. Direct SQL cannot insert a terminal root, mutate immutable root fields,
   reactivate/retarget terminal roots, delete roots/history, forge/out-of-order
   history, mutate protected outbox/idempotency fields, or bypass canonical
   uniqueness.
5. Predecessor/successor and replacement guards reject self/cyclic, missing,
   cross-Organization, cross-Workspace, null-unsafe cross-Project,
   source-equal, audience-broadening, terminal, wrongly linked, and reused
   replacement cases; explicit supersession accepts only the exact active
   linked successor.
6. Projection/manifest/source/scope/digest and initial/terminal history
   coherence remain identical through ORM and direct SQL paths.
7. Runtime is distinct from schema owner, is non-owner/non-superuser with
   `NOCREATEDB`, `NOCREATEROLE`, `NOINHERIT`, and `NOBYPASSRLS`, and has only
   the accepted table/column privileges. Runtime cannot DDL, DELETE, alter or
   disable triggers/functions, obtain ownership, or execute protected helper
   functions.
8. The repository never commits, obeys expected-version one-winner behavior,
   maps all closed fields without semantic transformation, and returns at most
   the requested candidate bound in deterministic canonical order.
9. Outbox and idempotency verification is persistence-only: exact closed,
   bounded, versioned, plaintext-free records and guards are proven without
   dispatch, replay orchestration, or service usage.
10. Existing Batch-1 focused tests and relevant Technical Report
    migration/role/repository regressions remain passing.

Expected validation includes focused migration, database-role, repository, and
direct-SQL tests; Batch-1 regression; relevant Technical Report persistence
regression; static/import checks; exact-file/prohibited-pattern checks; and
`git diff --check`.

## 6. Dependencies and Prerequisites

| Dependency | Status |
|---|---|
| PATCH-034 Architecture / EDS-034 / IDS-034 / Implementation-Plan-034 | ACCEPTED / SATISFIED |
| IRR-034 | PASS / SATISFIED |
| Batch 1 S01–S02 contracts and Aggregate | ACCEPTED / COMPLETE |
| One linear current Alembic head | `e03200000001` / VERIFIED |
| Distinct migration/runtime role convention | `satco` / `satco_runtime` / VERIFIED |
| Existing Organization, Workspace, Project, User, Technical Report, and shared Audit schema | PRESENT / SATISFIED |
| Canonical foreign application adapters | NOT REQUIRED by S03–S04 |
| Memory UoW/application orchestration | DEFERRED; NOT REQUIRED by S03–S04 |

## 7. Explicit Exclusions and Scope Control

Batch 2 prohibits:

- changes to any Batch-1 contract, schema, Aggregate, enum, port, exception, or
  test file;
- Technical Report, Capture, Evidence, Engineering Object, or Engineering
  Relationship adapters, repositories, ORM records, UoWs, Sessions, services,
  policies, or tests;
- concrete memory UoW, final-recheck, Audit recorder, rejection-Audit recorder,
  idempotency store/replay, outbox recorder/dispatch, clock, or command behavior;
- application `admit`, `create_successor`, `withdraw`, `supersede`, active read,
  history read, list/pagination, authorization, protected-result translation,
  or transaction orchestration;
- router, API, dependency composition, `app/main.py`, frontend/UI, AI/Copilot,
  semantic/vector/graph retrieval, or other deferred PATCH-034 capability;
- modifications to `backend/tests/conftest.py`, `backend/migrations/env.py`,
  environment/secrets/configuration, shared Audit schema, or existing
  migrations; and
- Batch 3–7 implementation, evidence packaging, delivery, or closure work.

Only the seven exact paths in §3.3 are authorized. Tests may create bounded data
through existing fixtures but may not alter unrelated test infrastructure.

## 8. Stop Conditions

Implementation must stop and report `BLOCKED` if:

- repository head is no longer exactly one `e03200000001` parent before the
  migration is created, or the proposed migration would create parallel heads;
- migration and runtime roles coincide, the runtime role must own protected
  objects, or accepted least-privilege grants cannot support repository DML;
- a shared schema, existing migration, environment, secret, credential,
  `conftest.py`, or Alembic environment change becomes necessary;
- any accepted IDS column, constraint, JSON validator, trigger predicate,
  ownership rule, or role grant is contradictory or requires invention;
- a direct-SQL path can bypass immutable history, terminal standing,
  uniqueness, lineage/replacement, scope/audience, or side-record integrity;
- S04 requires direct access to canonical Technical Report/provenance
  persistence or mutation of a foreign canonical table;
- implementation needs UoW transaction ownership, application authorization,
  protected result behavior, reads/pagination orchestration, adapters, API, UI,
  AI, or another Batch 3–7 responsibility;
- any path outside the exact reconciled seven-file boundary must change; or
- focused, adjacent persistence regression, role, static/scope, or
  `git diff --check` validation fails and cannot be corrected inside this
  boundary.

## 9. Readiness and Authority

Repository assumptions, the linear migration predecessor, role separation,
Batch-1 dependencies, and the reconciled seven-file S03–S04 boundary are verified.

```text
Batch 2 manifest: COMPLETE
Batch 2 implementation readiness: READY
Batch 2 implementation authority: NOT GRANTED
Batch 3 authority: NOT GRANTED
Later Batch authority: NOT GRANTED
Commit / push authority: NOT GRANTED
```

The exact next action is focused validation of the reconciled Batch 2 boundary,
followed by Independent Batch 2 implementation review if every gate passes.
