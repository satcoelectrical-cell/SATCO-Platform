# Implementation Plan 028 — Universal Engineering Capture Foundation

## 1. Document Control

| Field | Value |
|---|---|
| Related PATCH | PATCH-028 |
| Related IDS | IDS-028 v0.1 Approved |
| Version | 0.1 |
| Status | ACCEPTED — EXECUTABLE |
| Date | 2026-08-02 |

This plan partitions the approved IDS into three dependency-ordered Sprints.
Execution remains prohibited until Human plan acceptance and IRR-028
`READY FOR IMPLEMENTATION`.

### Approval Record

| Authority | Decision | Date |
|---|---|---|
| Product Owner | Accepted | 2026-08-02 |
| Architecture Guardian | Accepted | 2026-08-02 |

## 2. Verified Planning Baseline

- repository commit at planning: `86c034664f9db35d9817814964af42648365c36c`;
- branch: `patch-022.3a-development-infrastructure`;
- one Alembic head: `e02810000001`;
- application import succeeds and currently exposes 15 routes;
- existing Evidence/Relationship focused suite contains 40 discovered test
  functions by source inspection;
- the current worktree contains only the approved PATCH-028 documentation set;
- test guard requires database name `satco_platform_patch02022_test`.

IRR must revalidate commit/worktree compatibility and Alembic head immediately
before implementation.

## 3. Exact Global File Boundary

Only the 25 backend files listed in IDS-028 Section 3 are authorized: five
modified and twenty created. Each Sprint below narrows that boundary. No Sprint
may borrow a downstream file for convenience.

## 4. Sprint 1 — Domain and Contracts

### Objective

Implement the complete framework-independent Capture vocabulary, command/event
contracts, Aggregate Root, strict schemas, stable exceptions, and inward-owned
ports.

### Files

Modified:

- `backend/app/enums/__init__.py`;
- `backend/app/models/__init__.py`;
- `backend/app/schemas/__init__.py`.

Created:

- `backend/app/enums/engineering_experience_capture.py`;
- `backend/app/models/engineering_experience_capture.py`;
- `backend/app/models/engineering_experience_capture_command.py`;
- `backend/app/schemas/engineering_experience_capture.py`;
- `backend/app/ports/engineering_experience_capture.py`;
- `backend/app/exceptions/engineering_experience_capture.py`;
- `backend/tests/test_engineering_experience_capture_aggregate.py`;
- `backend/tests/test_engineering_experience_capture_schemas.py`.

### Implementation order

1. controlled enums and qualified exports;
2. immutable actor/metadata/command/result/event types and outbox/idempotency
   ORM declarations;
3. normalization helpers and Aggregate Root commands/invariants;
4. strict Pydantic requests/responses/filters;
5. stable exceptions;
6. inward-owned Protocols;
7. aggregate and schema tests.

### Validation

- compile/import only the new inner modules;
- exact enum/value checks;
- all lifecycle/terminal/no-op/version/event tests;
- Unicode, newline, control-character, and code-point-bound tests;
- immutable trusted-field and generic-mutation absence checks;
- schema extra-field rejection;
- static import review proving no FastAPI/HTTP/Session/Alembic dependency in
  Domain/Application contracts;
- QG-M1 checkpoint against Capture Once, Human Authority, Context, Evidence,
  Explainability, and Provider Independence.

### Exit

Sprint 1 PASS requires focused domain/schema tests, exact diff scope, no
blocking warning, and QG-M1 checkpoint PASS.

## 5. Sprint 2 — Persistence, Migration, and Atomicity

### Objective

Implement repository, context/supersession policy adapters, Unit of Work,
outbox/idempotency/Audit persistence, additive migration, concurrency safety,
and persistence validation.

### Files

Modified:

- `backend/migrations/env.py`.

Created:

- `backend/app/repositories/engineering_experience_capture_repository.py`;
- `backend/app/repositories/engineering_experience_capture_unit_of_work.py`;
- `backend/migrations/versions/e02800000001_engineering_experience_capture.py`;
- `backend/tests/test_engineering_experience_capture_repository.py`;
- `backend/tests/test_engineering_experience_capture_transaction.py`;
- `backend/tests/test_engineering_experience_capture_migration.py`;
- `backend/tests/test_engineering_experience_capture_security.py`;
- `backend/tests/test_engineering_experience_capture_performance.py`.

### Entry checks

- Sprint 1 PASS;
- Alembic still reports exactly `e02810000001` as the sole head;
- isolated test URL resolves specifically to
  `satco_platform_patch02022_test`;
- current database identity guard passes before migration/test work.

### Implementation order

1. migration with exact tables/constraints/indexes and parent;
2. metadata imports;
3. repository scoped queries and expected-version persistence;
4. context and authorization adapters;
5. advisory-lock supersession validator;
6. Audit/outbox/idempotency adapters and Unit of Work;
7. repository, transaction, migration, security, and performance tests.

### Migration sequence

In an approved isolated database only:

1. record current database name and revision;
2. upgrade to head;
3. validate exact schema, checks, FKs, indexes, and one head;
4. downgrade one revision;
5. verify removal of only the three Capture tables;
6. re-upgrade to head;
7. run clean-chain upgrade from base in a disposable isolated database or
   equivalent approved clean-schema harness;
8. compare SQLAlchemy metadata and migrated schema;
9. restore the ordinary test database to head.

### Atomicity and concurrency checkpoints

- success commits aggregate/Audit/outbox/idempotency together;
- staged failures roll back all four effects;
- stale expected version changes no state;
- exact replay returns only after current reauthorization;
- conflicting replay returns stable conflict without plaintext;
- concurrent supersession attempts cannot branch or merge;
- chain depth/cycle validation is bounded;
- list/count queries are fully authorized and have bounded query counts;
- no content/reference/rationale exists in Audit, events, errors, or logs.

### Exit

Sprint 2 PASS requires migration, repository, transaction, concurrency,
security, performance, and Sprint 1 regressions PASS with QG-M1 checkpoint
PASS.

## 6. Sprint 3 — Application, Transport, and Final Integration

### Objective

Implement application orchestration, explicit HTTP boundary, dependency
composition, route registration, complete security behavior, and regression.

### Files

Modified:

- `backend/app/main.py`.

Created:

- `backend/app/services/engineering_experience_capture_service.py`;
- `backend/app/api/v1/routers/engineering_experience_captures.py`;
- `backend/tests/test_engineering_experience_capture_service.py`;
- `backend/tests/test_engineering_experience_capture_api.py`.

### Implementation order

1. service normalization/fingerprint/authorization/validation/command/UoW
   orchestration;
2. authorized response and `allowed_actions` mapping;
3. seven explicit endpoints and request-scoped composition;
4. one router registration;
5. service/API/security integration tests;
6. adjacent and complete regression.

### Validation ladder

1. imports and application startup;
2. service focused tests;
3. API focused tests and OpenAPI route/method inspection;
4. all nine Capture test files;
5. authentication and Organization-context tests;
6. Project and Workspace tests;
7. EngineeringObject, Relationship, and Evidence tests;
8. full backend suite with zero failures;
9. final Alembic head/schema verification;
10. exact diff and prohibited-file/route/content-leak searches;
11. `git diff --check`;
12. QG-M1 Final comparison against the actual diff.

### Exit

Sprint 3 PASS requires every IDS acceptance criterion, all applicable QG-6
through QG-10 evidence, and no unresolved warning affecting engineering meaning,
security, history, or authority.

## 7. Test Environment Contract

Use only the guarded isolated PostgreSQL test database:

```text
postgresql://satco:satco_password@postgres:5432/
satco_platform_patch02022_test
```

The actual environment variable is one uninterrupted URL. The line break above
is documentation formatting only. Before destructive migration tests, verify
`current_database()` equals `satco_platform_patch02022_test`. Development,
staging, production, or any database without the exact test suffix is
prohibited.

## 8. Regression Matrix

| Risk | Required suite |
|---|---|
| authenticated Organization derivation | `test_authenticated_organization_context.py`, auth tests |
| Project/Workspace visibility | Project and Engineering Workspace permission/core tests |
| Object compatibility | EngineeringObject model/service/repository/API tests |
| Evidence distinction | all Evidence tests |
| graph/relationship regression | all EngineeringRelationship tests |
| Audit and transaction | Capture transaction plus existing Audit tests |
| migration lineage | Capture migration plus existing migration tests |
| application integration | full backend suite |

No existing test or fixture file may be modified. Test failures caused by a
real contract conflict return to governance; they are not waived or weakened.

## 9. Checkpoint Reporting

After every Sprint record:

- exact files created/modified;
- focused test command and pass/fail counts;
- warnings/skips/environment limitations;
- migration/head state where applicable;
- QG-M1 principle evidence;
- remaining blockers;
- next authorized Sprint or stop decision.

## 10. Rollback

### Sprint 1

Remove only new Capture inner-layer files and their new qualified exports.

### Sprint 2

In a disposable isolated test database, downgrade only
`e02800000001`; remove only new persistence files and metadata imports. Never
destroy governed non-test Capture data.

### Sprint 3

Remove router registration, router, service, and their focused tests while
preserving completed inner/persistence work if forward repair is governed.

No broad reset, checkout, migration-history rewrite, or unrelated-file
replacement is allowed.

## 11. Stop Conditions

- any IRR precondition becomes false;
- a required file is outside IDS Section 3;
- migration head changes or branches;
- isolated test identity cannot be proven;
- current code contradicts an EDS/IDS semantic decision;
- full authorized list totals require unbounded or leaky behavior;
- supersession races cannot be serialized safely;
- content/reference/rationale leakage appears;
- any focused, security, migration, atomicity, adjacent, or full regression
  check fails and cannot be corrected within authority;
- Manifesto Alignment becomes PENDING or FAIL.

## 12. Completion and Delivery

After implementation and validation:

1. create independent Final Review;
2. require QG-M1 Final PASS and Human QG-11 PASS;
3. update PATCH/Registry/Roadmap completion evidence only under lifecycle policy;
4. declare `IMPLEMENTATION COMPLETE — DELIVERY AUTHORIZATION PENDING` when
   QG-1 through QG-11 pass;
5. commit/push only after separate explicit authority;
6. declare DONE only when QG-12 remote evidence passes.

## 13. Current State

```text
Plan technical completeness: COMPLETE
Human Plan acceptance: ACCEPTED
Execution authorization: READY — RESUME AT SPRINT 2
```

## 14. Revision History

| Version | Date | Description |
|---|---|---|
| 0.1 | 2026-08-02 | Initial three-Sprint executable implementation plan. |
| 0.2 | 2026-08-03 | Focused lineage amendment updated the verified sole head and Capture migration parent baseline to e02810000001; execution order, scope, behavior, architecture, files, and stop conditions unchanged. |
