# EDS-028 — Independent Design Review

## 1. Review Control

| Field | Value |
|---|---|
| Reviewed document | `docs/design/EDS-028-Universal-Engineering-Capture-Foundation.md` v0.1 |
| Related PATCH | PATCH-028 |
| Review status | COMPLETE |
| Technical verdict | PASS |
| Manifesto Compliance | PASS |
| Human EDS acceptance | ACCEPTED after technical review |
| Reviewer | Codex, independent technical design reviewer |
| Date | 2026-08-02 |

This review verifies design completeness. Product Owner and Architecture
Guardian acceptance was subsequently recorded on 2026-08-02. Implementation
still requires approved IDS, plan, and READY IRR.

## 2. Review Method

The EDS was checked against PATCH-028, AR-028 required decisions, ADR-021,
Engineering Intelligence Architecture, completed PATCH-023 through PATCH-027,
current repository conventions, Framework v1.1, and QG-M1.

## 3. Required-Decision Closure

| AR-028 requirement | Result | EDS decision |
|---|---|---|
| Lifecycle and authority | PASS | `captured → withdrawn|superseded`; no approval authority |
| Explicit commands | PASS | create, withdraw, supersede only |
| Text/reference limits | PASS | normalized 1–10,000 content; optional 1–512 reference |
| Closed origin vocabulary | PASS | eleven exact source-kind values |
| Organization-wide policy | PASS | deferred; Project mandatory in Version 1 |
| Context compatibility | PASS | optional Workspace; discipline derived; object requires same Workspace |
| Confidentiality | PASS | constituent visibility intersection; no persisted label |
| Responsibility | PASS | immutable Human Creator; authorized Human management only |
| Correction/history | PASS | immutable original; terminal withdrawal; bounded acyclic supersession |
| Duplicate/idempotency | PASS | explicit uniqueness and exact replay semantics |
| Atomicity/events | PASS | aggregate, Audit, outbox, idempotency in one transaction |
| API/error boundary | PASS | explicit bounded endpoints and stable categories |
| Migration/rollback/tests | PASS | additive revision and complete validation matrix |
| QG-M1 mapping | PASS | all eleven principles mapped to behavior |

No AR-028 design decision remains delegated to implementation.

## 4. Architecture Findings

### Aggregate coherence

**PASS**

The aggregate owns only captured expression, trusted context/provenance,
lifecycle, history, and version. Review, Evidence, knowledge, AI, publishing,
and memory authority remain outside the consistency boundary.

### Immutability and correction

**PASS**

Deterministic normalization occurs before creation; canonical original content
then becomes immutable. Correction requires a separate compatible Capture and
explicit supersession. Terminal withdrawal/supersession preserve history.

### Context integrity

**PASS**

Project is mandatory, avoiding premature Organization-wide reuse. Workspace is
optional only for Project-wide experience. Discipline derives from Workspace,
and Engineering Object context requires exact same scope. Cross-scope context
is prohibited.

### Supersession safety

**PASS**

Distinct replacement, identical scope, active lifecycle, one predecessor, one
replacement link, no branching/merging, acyclic validation, and depth 20 make
the history deterministic and bounded. Application validation does not expand
either aggregate.

### Security and confidentiality

**PASS**

Authorization-before-disclosure, protected-not-found, constituent visibility,
no partial redaction, bounded authorized counts, and exclusion of content from
Audit/events/logs close the primary leakage risks without inventing a new
confidentiality field.

### Human and AI boundary

**PASS**

Only authenticated accountable Humans issue commands. Capture authenticates
submission, not engineering meaning. No AI/provider metadata or autonomous
command exists.

### Persistence and layer discipline

**PASS**

The design follows the established aggregate/application/port/infrastructure/
transport boundaries, PostgreSQL/Alembic authority, optimistic concurrency,
idempotency, atomic Unit of Work, outbox, Audit, and repository restrictions.

### Implementability

**PASS**

IDS-028 can now specify exact enums, aggregate/schema/service/repository/router,
migration, permissions, errors, dependency wiring, and tests without inventing
engineering behavior.

## 5. Manifesto Compliance

| Principle | Result |
|---|---|
| Engineering First | PASS |
| Capture Once | PASS |
| Human Authority | PASS |
| Engineering Context Is Sacred | PASS |
| Evidence Before Assumption | PASS |
| Context Before Recommendation | PASS |
| Intelligence Before Automation | PASS |
| Explainability | PASS |
| Provider Independence | PASS |
| Organizational Ownership | PASS |
| Continuous Evolution | PASS |

**Manifesto Compliance: PASS**

No principle is weakened to satisfy another. No unresolved Manifesto conflict
remains at EDS level.

## 6. Required IDS Constraints

IDS-028 must:

1. use exact EDS fields, vocabulary, lifecycle, commands, limits, and events;
2. define the precise source file, migration, table, constraint, index, route,
   permission, stable error, and test boundary;
3. reuse existing ports/conventions only where their contracts match;
4. prohibit content/reference/rationale leakage into Audit, event payloads,
   logs, errors, and idempotency conflict diagnostics;
5. define transaction-scoped supersession uniqueness/cycle protection;
6. define exact protected-not-found and list/count authorization behavior;
7. parent migration to the verified current single head at IRR;
8. include focused, adjacent, security, migration, atomicity, performance, and
   full backend regression commands;
9. preserve every PATCH/EDS non-scope;
10. map every file/test to the Manifesto Alignment Record.

## 7. Open Gates

- IDS-028 is absent;
- Implementation Plan-028 is absent;
- IRR-028 is absent;
- QG-M1 readiness remains PENDING.

## 8. Verdict

**EDS-028 TECHNICAL REVIEW: PASS**

**Manifesto Compliance: PASS**

The design is ready for Human acceptance and subsequent IDS drafting.

```text
Manifesto Alignment Verified: NO
QG-M1 Readiness Result: PENDING
PATCH-028 implementation: NOT READY
```

## 9. Revision History

| Version | Date | Description |
|---|---|---|
| 1.0 | 2026-08-02 | Independent EDS technical review PASS. |
