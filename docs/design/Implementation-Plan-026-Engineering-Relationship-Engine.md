# Implementation Plan-026 — Engineering Relationship Engine

## Status

**EXECUTABLE**

## Governing Baseline

- approved PATCH-026;
- accepted EDS-026 and PASS EDS Review;
- approved IDS-026;
- AR-026 PASS;
- completed PATCH-023 EngineeringObject Application Layer;
- completed PATCH-024 EngineeringObject Persistence Migration;
- completed PATCH-025 Authenticated Organization Context;
- approved PATCH-021.2 Engineering Relationship Vocabulary;
- current Governance Model and Development Lifecycle.

All dependencies are satisfied. The exact implementation boundary is the
IDS-026 file set. This plan grants no authority outside that boundary.

## Preconditions

Before the first source edit:

1. confirm implemented PATCH-027 and single Alembic head `e02700000001`;
2. confirm the dedicated test database identity and current revision;
3. confirm the worktree and preserve unrelated user changes;
4. confirm every proposed edit is listed by IDS-026;
5. stop if the approved model, enum, API, migration, or test contract cannot be
   implemented without changing an authoritative document.

## Exact Implementation Sequence

### Checkpoint 1 — Domain Contracts

1. Add only the approved relationship family/type/lifecycle enums and exports.
2. Add command, result, Domain Event, actor, authorization, and metadata DTOs.
3. Add the EngineeringRelationship Aggregate Root with the approved immutable
   identity/endpoints, state, transition matrices, responsibility separation,
   Evidence requirements, self-link/duplicate inputs, and version behavior.
4. Add aggregate tests covering every permitted and prohibited lifecycle and
   authority transition, every acyclic/allowed-cycle class, no-op handling,
   immutable fields, events, and exactly one version increment.
5. Run aggregate and enum tests. Do not proceed on failure.

### Checkpoint 2 — Application Contracts

1. Add strict Pydantic v2 request, response, filter, pagination, and traversal
   schemas using ConfigDict and existing enums.
2. Add the exact inward-owned ports from IDS-026.
3. Add the stable EngineeringRelationship exception hierarchy and codes.
4. Add schema tests for extra-field rejection, trusted-context exclusion,
   positive expected versions, Evidence UUID uniqueness, pagination, traversal
   limits, responses, and stable errors.
5. Run Checkpoints 1–2 tests. Do not proceed on failure.

### Checkpoint 3 — Persistence Model and Migration

1. Add the approved SQLAlchemy models and only the approved model exports.
2. Add revision `e02600000001_engineering_relationship_engine.py`.
3. Set `down_revision` exactly to `e02700000001`.
4. Create only `engineering_relationships`,
   `engineering_relationship_outbox`, and
   `engineering_relationship_idempotency`, with the exact IDS-026 columns,
   checks, foreign keys, partial uniqueness, and indexes.
5. Reuse `audit_logs.entity_uuid` unchanged.
6. Add the minimum model import to Alembic metadata.
7. Add migration/model-schema tests.
8. Validate migration order in an isolated database:
   - verify current revision `e02700000001`;
   - upgrade to `e02600000001`;
   - verify one Alembic head and exact model/schema agreement;
   - downgrade to `e02700000001`;
   - verify only the three PATCH-026 tables are removed;
   - re-upgrade to `e02600000001`;
   - create a clean isolated database and run upgrade from base to head.
9. Do not execute development, staging, or production migrations.

### Checkpoint 4 — Repository and Atomic Unit of Work

1. Implement complete authorized-scope rehydration, creation,
   expected-version persistence, active-identity duplicate lookup, direct
   endpoint lists, and bounded neighborhood/path repository queries.
2. Implement transaction-scoped cycle serialization and same-type reachability
   for the approved acyclic set.
3. Implement one SQLAlchemy Unit of Work sharing one Session across repository,
   AuditRecorder, DomainEventRecorder, and IdempotencyStore.
4. Ensure repositories never authorize, commit, publish, generically update, or
   physically delete.
5. Add repository, concurrency, duplicate, cycle, idempotency, and atomic
   rollback tests.
6. Run Checkpoints 1–4 and migration tests. Do not proceed on failure.

### Checkpoint 5 — Application Service and Policies

1. Implement the eight canonical command methods and authorized read/list/
   neighborhood/path queries.
2. Implement only the approved AuthorizationPolicy, endpoint/Evidence/
   responsibility validators, CycleDetector, and Clock adapters.
3. Enforce trusted Organization context, same Project, approved cross-Workspace
   types, and the derived-access intersection across both endpoints, all
   Evidence, and applicable Workspaces before disclosure; use
   protected-not-found for any inaccessible constituent and persist no
   confidentiality label.
4. Invoke exactly one Aggregate Root command per mutation.
5. Atomically stage relationship state, Audit, outbox events, and idempotency
   outcome, then commit once through UnitOfWork.
6. Add service, visibility, security isolation, concurrency, idempotency,
   Evidence/responsibility, and transaction tests.
7. Run Checkpoints 1–5. Do not proceed on failure.

### Checkpoint 6 — Transport and Registration

1. Add only the approved EngineeringRelationship router and request-scoped
   dependency wiring.
2. Build AuthenticatedActor exclusively from trusted PATCH-025 context.
3. Add the twelve IDS-026 endpoints, stable error mapping, authorized scalar
   responses, deterministic allowed_actions, pagination, filters, and bounded
   traversal parameters.
4. Register only the EngineeringRelationship router in the application.
5. Prove no PUT, generic PATCH, DELETE, bulk mutation, arbitrary query, or
   unbounded traversal route exists.
6. Add endpoint and traversal tests.
7. Run all PATCH-026 tests. Do not proceed on failure.

### Checkpoint 7 — Final Validation and Handoff

1. Run formatting/static checks used by the repository on every IDS-026 file.
2. Run all PATCH-026 unit and schema tests.
3. Run repository, service, endpoint, migration, transaction, authorization,
   security, concurrency, idempotency, cycle, and traversal tests.
4. Run all EngineeringObject and authenticated-organization tests.
5. Run all existing engineering-context relationship tests to prove no naming
   or route collision.
6. Run the complete backend regression suite.
7. Confirm Alembic has one head and the isolated validation database is at
   `e02600000001`.
8. Review the final diff against the exact IDS-026 file set.
9. Record results; do not commit, push, deploy, or migrate a non-isolated
   environment.

## Validation Sequence

The validation order is mandatory:

1. compile/import and static checks;
2. aggregate and enum tests;
3. schema and exception tests;
4. migration upgrade/model comparison/downgrade/re-upgrade/clean creation;
5. repository and cycle/concurrency tests;
6. Unit of Work, Audit, outbox, idempotency, and rollback tests;
7. service, authorization, visibility, and security tests;
8. API and bounded-traversal tests;
9. EngineeringObject and PATCH-025 regressions;
10. engineering-context relationship regressions;
11. complete backend regression;
12. final Alembic-head and diff-scope verification.

A later step does not waive an earlier failure.

## Regression Strategy

Regression is layered to isolate failures while preserving a final
repository-wide gate. PATCH-026 tests run first, followed by direct dependency
tests, adjacent relationship-module tests, and the complete backend suite.
Existing tests shall not be weakened, skipped, rewritten to hide failures, or
pointed at an unapproved schema. Any regression attributable to PATCH-026 is a
release blocker. A pre-existing failure must be evidenced, shown unrelated,
and returned to governance; it cannot be silently accepted.

## Rollback Strategy

Before authoritative relationship data exists, rollback consists of:

1. stop application use of PATCH-026 endpoints;
2. roll back the bounded application changes;
3. in the isolated validation environment only, downgrade
   `e02600000001` to `e02700000001`;
4. verify all pre-PATCH tables and data are unchanged;
5. rerun the pre-PATCH regression suite.

After authoritative relationship data exists, destructive downgrade is not an
automatic rollback. Disable new PATCH-026 traffic, preserve all three
PATCH-026 tables, capture diagnostics, and use a separately approved
data-preserving forward repair or migration plan. Physical deletion of
relationship history is never a rollback mechanism.

## Implementation Checkpoints and Approval Evidence

| Checkpoint | Required evidence | Exit condition |
|---|---|---|
| CP1 Domain | aggregate/enum tests | all commands and matrices pass |
| CP2 Contracts | schema/port/error tests | transport-independent contracts pass |
| CP3 Migration | upgrade/downgrade/clean/model match | one correct linear head |
| CP4 Persistence | repository/cycle/UoW tests | concurrency and atomicity pass |
| CP5 Application | service/security tests | authorization and orchestration pass |
| CP6 Transport | endpoint/traversal tests | exact API contract passes |
| CP7 Release Gate | dependency and full regression | zero blocking failures and exact diff |

Checkpoint evidence is cumulative. Any failed exit condition stops later work.

## Stop Conditions

Stop and return to the earliest affected governance gate for:

- an unlisted file, table, field, enum, type, command, endpoint, or dependency;
- a required change to PATCH-023, PATCH-024, PATCH-025, EngineeringObject, Core,
  or an unrelated module;
- a second Alembic head or parent other than `e02700000001`;
- cross-Organization/Project behavior or an unapproved cross-Workspace type;
- a non-EngineeringObject relationship endpoint;
- a weaker authorization, confidentiality, Evidence, responsibility, duplicate,
  cycle, concurrency, idempotency, Audit, event, or atomicity rule;
- generic update, physical delete, unbounded traversal, or arbitrary graph edge;
- AI-originated mutation without explicit authenticated engineer command;
- migration/model drift or any blocking focused/regression failure.

## Execution Authorization

This plan is **EXECUTABLE** only within approved IDS-026 and IRR-026. It does
not authorize commit, push, deployment, or migration outside the isolated test
environment.
