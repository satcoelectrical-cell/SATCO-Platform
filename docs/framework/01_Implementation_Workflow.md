# SATCO Implementation Framework v1.1 — Implementation Workflow

## 1. Purpose

This document defines the single end-to-end workflow invoked by the instruction
`Implement PATCH-XXX`.

## 2. Invocation Contract

That instruction authorizes Codex to execute only when the repository already
contains an unambiguous approved chain. Codex shall resolve `PATCH-XXX` through
the authoritative PATCH registry and shall not infer a similarly named record.

The short instruction expands to:

```text
Resolve authority → Verify readiness → Inspect scoped state → Select sprint
→ Declare exact files → Implement → Validate → Review → Report state
```

It never implicitly authorizes commit, push, deployment, production migration,
secret changes, data deletion, or scope expansion.

## 3. Mandatory Governance Flow

Before source change, verify:

1. PATCH identifier and registry scope agree.
2. PATCH is approved with explicit scope and non-scope.
3. Required Architecture Review is PASS.
4. The PATCH contains a Manifesto Alignment Record and the Architecture Review
   records `Manifesto Compliance: PASS`.
5. EDS is accepted and its review passes, including affected-principle coverage.
6. IDS is approved and defines an exact file/table/API/test and Manifesto
   traceability boundary.
7. Implementation Plan is executable and includes QG-M1 checkpoints.
8. IRR says `READY FOR IMPLEMENTATION`, `Manifesto Alignment Verified: YES`,
   and `QG-M1 Readiness Result: PASS`.
9. All prerequisite PATCHes are complete at their required versions.
10. Current repository state still matches the IRR assumptions.

Failure of any item returns `NOT READY` or `BLOCKED`; no code is written.

## 4. Execution Lifecycle

### Phase A — Resolve

- Read repository governance and documentation hierarchy.
- Resolve the certified Manifesto version and accepted Manifesto Alignment
  Record.
- Resolve the PATCH, related ADR/XDR/Blueprint, EDS, IDS, reviews, plan, and IRR.
- Establish authority order and explicit supersession.
- Record open assumptions; assumptions that change behavior are blockers.

### Phase B — Inspect

- Inspect only relevant repository modules and conventions.
- Check worktree state and preserve unrelated changes.
- Identify current Alembic heads, test database guard, runtime environment, and
  adjacent regression suites.
- Compare repository reality with the approved IDS.

### Phase C — Bound

- Produce the exact files to create and modify before implementation.
- Map every file to one IDS deliverable.
- Map every affected behavior to its approved Manifesto/EDS evidence.
- Confirm prohibited files, behaviors, routes, tables, and operations.
- Stop if a required file is not authorized.

### Phase D — Sprint

- Select the smallest independently verifiable sprint using `02_Sprint_Engine`.
- Implement domain/contracts before adapters, adapters before transport.
- Complete each checkpoint before moving outward.
- Re-evaluate QG-M1 at every Sprint checkpoint and stop on new conflict.

### Phase E — Validate

- Run the validation ladder in `04_Validation_Engine`.
- Apply the testing matrix in `05_Testing_Engine`.
- Apply `06_Migration_Engine` when schema is affected.
- Repeat affected validation after every correction.

### Phase F — Review

- Compare final diff with IDS file scope and PATCH non-scope.
- Compare the final diff with the accepted Manifesto Alignment Record.
- Verify architecture, security, backward compatibility, migration, and tests.
- Perform independent review when required.
- Record unresolved warnings and blockers honestly.

### Phase G — Complete

- Apply `08_Quality_Gates`.
- Update only documentation authorized by the PATCH or completion policy.
- Return the prescribed completion report.
- Commit/push only through separately authorized lifecycle gates.

Phase G may declare `IMPLEMENTATION COMPLETE` after QG-1 through QG-11 pass.
It may declare the PATCH `DONE` only after the separately authorized Commit and
Push gates complete and QG-12 passes. When Commit or Push authority has not
been granted, the truthful terminal report is `IMPLEMENTATION COMPLETE —
DELIVERY AUTHORIZATION PENDING`, not `PATCH DONE`.

## 5. Architecture Verification

Every implementation must prove:

- Aggregate Root owns invariants, lifecycle decisions, state mutation, version
  advancement, and Domain Event creation where governed.
- Application Service owns orchestration, authorization coordination, reference
  validation, one explicit command invocation, Unit of Work coordination, and
  authorized mapping.
- Ports are owned by inner layers.
- Infrastructure implements ports and contains framework-specific persistence.
- Transport validates syntax and maps stable contracts; it does not own domain
  behavior.
- Dependency direction remains Domain → Application → Ports → Infrastructure →
  Transport in conceptual outward flow, while source dependencies point inward.

Domain and Application shall not depend on FastAPI, HTTP, SQLAlchemy Session,
Alembic, or concrete infrastructure implementations unless an approved legacy
contract explicitly governs otherwise.

## 6. Layer Rules

### Aggregate

- Explicit commands only; no generic field mutation.
- Immutable identity and approved immutable references remain immutable.
- Validate domain invariants and reject no-ops where governed.
- A successful mutation advances version exactly once.
- Produce past-tense Domain Events without publishing them.

### Repository

- Load only the scope requested by the Application boundary.
- Rehydrate complete aggregate state.
- Add/query and compare-and-change expected-version persistence only.
- Never authorize, commit, publish, invoke transport, or perform generic update.

### Application Service

- Obtain trusted actor/context through ports or trusted transport composition.
- Authorize before disclosure.
- Validate references and policy outside the Aggregate.
- Invoke exactly one Aggregate command for one mutation capability.
- Coordinate atomic persistence, Audit, outbox, and idempotency.
- Never mutate ORM fields directly or duplicate transition matrices.

### API

- Use explicit command/query endpoints and strict request schemas.
- Never accept trusted actor, Organization, system defaults, audit metadata, or
  other server-managed values from clients.
- Enforce stable errors, bounded filtering/pagination/traversal, and protected
  not-found where approved.
- No generic PUT/PATCH or physical DELETE unless explicitly approved.

## 7. Security and Accountability Workflow

For every operation:

1. authenticate;
2. derive trusted active Organization/scope server-side;
3. apply operation-specific, scope-aware, deny-by-default authorization;
4. use protected-not-found before disclosure when required;
5. validate references and derived visibility;
6. invoke the domain command or authorized query;
7. persist accountability atomically where governed;
8. map only authorized scalar state and deterministic `allowed_actions`.

`allowed_actions` is explanatory output, not an authorization grant.

## 8. Completion Report

Unless the PATCH defines a stricter format, return:

```text
Implementation Status
Manifesto Alignment
QG-M1 Result
Files Created
Files Modified
Tests Added
Validation Results
Remaining Blockers
PATCH Status: IMPLEMENTATION COMPLETE — DELIVERY AUTHORIZATION PENDING, DONE,
or BLOCKED
```

The report must distinguish passed tests, warnings, skipped checks, environment
limits, and unresolved failures.
