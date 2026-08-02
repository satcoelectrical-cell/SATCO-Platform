# SATCO Implementation Framework v1.1 — Sprint Engine

## 1. Purpose

The Sprint Engine partitions one approved PATCH into small, dependency-ordered,
independently verifiable execution units without changing PATCH scope.

## 2. Selection Principles

- Select from the approved IDS and Implementation Plan; never invent a sprint.
- Prefer the smallest unit that creates a coherent testable boundary.
- Inner contracts precede outer adapters.
- Persistence precedes transport when transport requires durable behavior.
- A prerequisite PATCH remains separate from its consumer PATCH.
- A sprint inherits every PATCH non-scope and stop condition.

## 3. Standard Sprint Classes

### Sprint 0 — Readiness

Documentation and environment only: governance closure, compatibility policy,
prerequisite PATCH, EDS/IDS/IRR, exact file set, and repository health.

Exit: `READY FOR IMPLEMENTATION`.

### Sprint 1 — Foundation

Typical scope:

- controlled enums and shared types;
- Aggregate Root/model and explicit commands;
- Pydantic request/response/filter/pagination contracts;
- stable exceptions;
- inward-owned ports/interfaces;
- aggregate and schema tests.

Prohibited: concrete repository/service/router/DI/migration unless IDS assigns
one of them to the Foundation sprint.

### Sprint 2 — Application and Persistence

Typical scope:

- repository implementation;
- Unit of Work;
- Audit, Domain Event outbox, and idempotency adapters;
- application service and policy/reference adapters;
- optimistic concurrency;
- authorized query/traversal contracts;
- additive migration and persistence tests.

Prohibited: transport and route registration unless IDS assigns them here.

### Sprint 3 — Transport and Final Integration

Typical scope:

- API router and stable error mapping;
- request-scoped dependency composition;
- router registration;
- endpoint/security/integration tests;
- dependency regressions and full backend regression.

Exit: `IMPLEMENTATION COMPLETE`, `IMPLEMENTATION COMPLETE — DELIVERY
AUTHORIZATION PENDING`, or `BLOCKED`. PATCH `DONE` additionally requires the
separately authorized delivery gate after all sprints.

### Specialized Sprint

Migration-only, infrastructure, frontend, AI, analytics, or documentation
PATCHes use the same gates but select deliverables from their approved IDS.
The names above are patterns, not permission to add irrelevant layers.

## 4. Sprint Selection Algorithm

1. Read the Implementation Plan checkpoint order.
2. Mark already completed and validated deliverables.
3. Identify the earliest incomplete dependency.
4. Select all inseparable deliverables needed for one coherent validation gate.
5. Exclude downstream deliverables.
6. Declare exact files and validation commands.
7. Stop if the selected sprint requires an unauthorized prerequisite.

## 5. Checkpoint Contract

Each sprint checkpoint defines:

- governing inputs;
- exact files and behaviors;
- explicit non-scope;
- entry conditions;
- test and validation evidence;
- rollback boundary;
- stop conditions;
- exit state.

No checkpoint is complete merely because files exist.

## 6. Cross-Sprint Integrity

- Later sprints may not rewrite approved earlier contracts for convenience.
- A proven implementation defect may be corrected only within IDS authority and
  must rerun all affected earlier tests.
- A required semantic change returns to the earliest documentation gate.
- Migration parentage uses the actual approved head at execution readiness.
- Transport composition must use completed inner ports; it shall not bypass
  them.

## 7. Sprint DONE Criteria

A sprint is DONE when its exact deliverables exist, focused tests pass,
architecture boundaries remain intact, no unauthorized diff exists, migration
state is correct where applicable, and no sprint blocker remains. PATCH DONE
still requires the final quality gates after all sprints.
