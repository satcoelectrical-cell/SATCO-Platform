# SATCO Implementation Framework v1.1 — Validation Engine

## 1. Purpose

The Validation Engine defines the ordered evidence required to move from an
authorized change to a completion claim.

## 2. Validation Ladder

Run from cheapest and most local to broadest and most expensive:

1. file-scope and diff inspection;
2. syntax, compile, import, and formatting checks;
3. enum, schema, aggregate, and pure-unit tests;
4. repository, policy, and service tests;
5. migration/schema tests where applicable;
6. transaction, concurrency, Audit, event, and idempotency tests;
7. API, authorization, visibility, and security tests;
8. direct prerequisite and adjacent-module regressions;
9. full backend or affected product regression;
10. final Alembic-head, diff-scope, and repository-state verification.

A later pass never waives an earlier failure.

## 3. Entry Validation

Before implementation verify:

- expected repository/worktree identity;
- required documentation availability and status;
- exact authorized file list;
- relevant runtime/tool versions;
- Docker/service health when required;
- dedicated test database identity;
- current migration head(s);
- baseline focused/regression state when risk warrants it.

## 4. Architecture Validation

Validate responsibilities, dependency direction, explicit commands, invariant
ownership, repository/service boundaries, authorization-before-disclosure,
Audit ownership, Domain Event ownership, idempotency, Unit of Work, optimistic
concurrency, and modular extension boundaries.

## 5. Documentation Validation

- All referenced documents exist at the exact path.
- Status and approval records agree.
- PATCH scope and non-scope match EDS, IDS, plan, and IRR.
- Exact files/tables/routes/tests are complete.
- Migration parent reflects the approved current chain.
- No lower document reverses authority direction.
- Revision histories record material corrections.

## 6. Implementation Validation

- Every diff line maps to an approved deliverable.
- No unrelated user changes are altered.
- Public contracts preserve compatibility unless breaking change is approved.
- Trusted values are server-derived.
- Inner layers remain framework-independent.
- Error responses do not disclose internals or protected existence.
- Query limits and pagination are enforced.

## 7. Data and Transaction Validation

For governed mutation verify:

- one command causes one aggregate version increment;
- stale expected version changes no state;
- exact idempotent replay returns the committed authorized result;
- conflicting reuse returns the stable conflict;
- aggregate state, Audit, outbox, and idempotency outcome share one transaction;
- any staged failure rolls back every effect;
- repositories never commit or publish.

## 8. Evidence Recording

Record command, environment, scope, result counts, warnings, skipped checks,
revision/head, and failure details. “Tests pass” without identifiable scope and
result is insufficient.

## 9. Correction Loop

On failure:

1. identify whether cause is implementation, environment, test, migration, or
   governing contract;
2. correct only within authority;
3. rerun the failing test;
4. rerun every affected lower validation layer;
5. rerun required final regressions;
6. do not weaken tests to manufacture a pass.

## 10. Validation Outcomes

- PASS: all required checks pass with no blocking warning.
- PASS WITH COMMENTS: only when the governing review permits non-blocking,
  explicitly owned comments; this never substitutes for READY or DONE.
- FAIL: at least one required check fails.
- BLOCKED: validation cannot proceed safely without new authority or external
  state.
