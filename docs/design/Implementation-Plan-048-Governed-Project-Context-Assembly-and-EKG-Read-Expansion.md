# Implementation-Plan-048 — Governed Project Context Assembly and EKG Read Expansion

## 1. Control and authority

| Field | Value |
|---|---|
| Related PATCH | PATCH-048 |
| Governing architecture / EDS / IDS | ACCEPTED / COMPLETE |
| Status | ACCEPTED / COMPLETE after independent Plan Review |
| Implementation Plan authority | Granted by Human IDS Acceptance |
| IRR-048 authority | GRANTED only after this Plan acceptance |
| Implementation / migration authority | NOT AUTHORIZED |
| Alembic head | e04700000001 |

This Plan implements only the read-only accepted boundary: governed Project
Context assembly, bounded one-hop EKG read expansion, and the corresponding
Project Engineering Context UI. It creates no aggregate, source ownership,
mutation, persistence, migration, transaction/UoW, idempotency/outbox, AI,
generic graph, semantic/vector search or PATCH-049 behavior.

Each batch must receive its own Authorized File Manifest immediately before
implementation. The families below are planning surfaces only, not authorization.

## 2. Dependency order and common rules

Four batches are the smallest safe sequence:

1. contracts and owner-side prerequisites;
2. Project Context composition and its transport;
3. one-hop EKG expansion and its transport extension;
4. frontend integration and final composition evidence.

Batch 1 is prerequisite for Batches 2 and 3. Batch 2 establishes typed Context
data that Batch 4 consumes. Batch 3 establishes typed EKG data that Batch 4
consumes. Batch 4 starts only after Batches 1 to 3 have independent acceptance.

All batches use trusted authentication and server-derived Organization context;
call an owner application port before projection; never access a foreign
repository, ORM, Session, table or UoW. Protected results are discriminator-only
at top level and no hidden/global/authorized total is returned. No batch adds an
e048 migration: Alembic must remain sole head e04700000001.

During each batch run focused tests plus only the smallest relevant adjacent
regression. Do not run full backend/frontend suites or repeated production
builds. Each batch ends with independent review; Critical/Major findings require
in-scope remediation, focused rerun and re-review before Human Batch Acceptance.

## 3. Batch 1 — Typed contracts and canonical owner-port prerequisites

### Scope

Create closed Project Context schemas/enums/results and owner-port protocols:
the ten section request/envelope contracts; availability, authority, temporal and
provenance types; truncation/opaque-continuation metadata; exact 18 node
selectors/projections; exact relationship discriminators; typed owner result
unions; Project/Workspace scope actor contracts; and no-payload protected,
invalid and unavailable results.

Create narrow owner-side application read adapters/ports where current canonical
service output is not a safe cross-domain boundary. This includes Engineering
Context current-list/single-node and Engineering Context Relationship incident
read ports, because their current services expose dict/Session-facing methods.
Use the existing Project/Foundation, Execution, Deliverable, Project Control,
Engineering Object/Relationship, Evidence, Supporting File, Technical Report and
Organizational Memory application service boundaries through typed adapters. Do
not construct composition/orchestration, continuation issuance, EKG expansion,
transport, UI or persistence.

### Expected file families

| Family | Expected new/modified surface |
|---|---|
| backend contracts | project-context schema/enums and typed port module |
| owner adapters | narrow adapters for owner-service response narrowing; Engineering Context and Context Relationship typed owner port surfaces |
| existing owner service/contracts | only the smallest owner-side type exposure necessary to avoid dict/Session cross-domain output |
| focused tests | Project Context contract, owner-port, Context/Context Relationship port and security/non-disclosure tests |

No router, dependency composition, main registration, database model, repository,
migration, frontend or PATCH-049 file is permitted.

### Acceptance and focused evidence

Prove frozen DTO closure, ten-section and 18-node allow-list closure, exact
relation discriminator closure, selector typing, Human-identity exclusion,
payload-free protected/invalid/unavailable variants, owner-port result closure,
and no direct foreign persistence import. Run focused contract/port/security tests
and the smallest Context/Context Relationship contract regression.

## 4. Batch 2 — Governed Project Context composition and thin transport

### Scope

Create request-scoped Project Context composer and the thin authenticated context
route/dependency wiring. Implement assemble_project_context only: Project/
Workspace gate, ten section port composition, canonical section ordering, source
state translation, per-request/per-section observation timestamps, non-atomic
partiality, 13-call cap, source page limits, truncation, last-evaluated
continuation, 512 KiB response guard, and closed transport translation.

The continuation reuses the existing authenticated AES-GCM cursor precedent with
canonical base64url, distinct purpose binding, 15-minute expiry, maximum 4096
characters, actor/Organization/Project/Workspace/filter/page/order binding, and
pre-read invalid-token failure. It has no hidden total and no cache/snapshot.

### Expected file families

| Family | Expected new/modified surface |
|---|---|
| backend application | Project Context composer/service and canonical source adapters |
| composition / transport | request-scoped dependency, Project Context router and one main registration |
| contracts | only additive transport request/response schemas required by Batch 1 contracts |
| focused tests | context service, source-state, continuation, API, security and composition tests |

The only initial route is the Project Context read. Node/related EKG routes,
generic graph logic, frontend, persistence/migration and AI are excluded.

### Acceptance and focused evidence

Prove all ten section paths; available/empty/not_established/not_disclosed/
unavailable; complete_within_bounds/partial/all-unavailable; scope authorization
before source read; no hidden total; canonical ordering; truncation/last-
evaluated continuation; tamper/context/expiry rejection; response byte limit;
and non-atomic observations. Run only focused context/API/security tests and
smallest owner-service/continuation adjacent regressions.

## 5. Batch 3 — Bounded one-hop EKG expansion and target reauthorization

### Focused prerequisite reconciliation

Before the existing Batch 3 workstreams, add the five IDS-named owner-safe
exact reads for Activity, Milestone, Change Impact, Project and Workspace in
their canonical services and closed DTO modules, with focused owner
service/security evidence. These reads precede and remain independent of
Project Context graph adapters. They add no owner mutation, persistence or
migration and may not be replaced by list scanning or foreign repository
access.

### Scope

Add exact 18-node dispatch, exact owner-specific single-node and incident-edge
reads, get-node and related-node thin route extensions, closed relation matrix,
start authorization, owner relation read, target reauthorization, strict
cross-Organization/Project/Workspace guards, stale/deleted target protection,
candidate dedupe/order, last-evaluated continuation, one-hop stop and limits:
one start plus at most eight incident readers plus at most 91 targets, never more
than 100 owner calls; candidates/visible edges/visible targets/page size each
at most 91; response at most 512 KiB.

Use only the owner paths established by IDS: Project/Workspace; Execution;
Deliverable; Project Control; Engineering Object and Engineering Relationship;
Engineering Context and Engineering Context Relationship; Evidence/File;
Technical Report; Organizational Memory. No universal resolver, wildcard
relationship, depth parameter, recursive helper, target enrichment, inferred
edge, source mutation or graph persistence is permitted.

### Expected file families

| Family | Expected new/modified surface |
|---|---|
| backend application | EKG read/expansion service and owner-specific graph adapters |
| contracts | additive exact node/edge request/result contracts from Batch 1 only |
| composition / transport | Project Context dependency/router extension only |
| focused tests | node dispatch, edge matrix, expansion/bounds/continuation/security/API tests |

No frontend work, migration/persistence, Context source expansion beyond accepted
ports, generic graph subsystem, AI or PATCH-049 work is permitted.

### Acceptance and focused evidence

Prove every supported node maps to its canonical owner; Foundation is rejected as
a node; every allowed family is owner-read; unsupported node/relation is invalid;
no wildcard/second hop/inferred edge; starting/target authorization precedes
projection; foreign tenant/project/workspace, stale/deleted targets and protected
relations leak no fact/count; exact call/candidate/result bounds and continuation
avoid skips/duplicates. Run focused graph/security/API tests and the smallest
Engineering Object/Relationship/Context relationship adjacent regressions.

## 6. Batch 4 — Project Engineering Context frontend and final composition evidence

### Scope

Add the Project Engineering Context route/surface using only typed Batches 2 and
3 API clients. Render ten section cards, authority and temporal labels,
provenance permitted by the API, truthful available/empty/not-established/
not-disclosed/unavailable/partial/truncated/loading/error/protected states,
continuation controls and bounded one-hop related navigation.

The UI is keyboard-operable, uses semantic landmarks/headings/statuses and
focus-visible controls, stacks responsively, and remains i18n/RTL-ready through
isolated display strings and direction-neutral layout. It uses real returned
data only and does not ask a Human to enter raw internal IDs.

Excluded: graph editor/designer/canvas, AI chat/recommendations, completeness or
missing-information analysis, metrics/totals, semantic/vector search, fake data,
Persian/Arabic translation and all PATCH-049 behavior.

### Expected file families

| Family | Expected new/modified surface |
|---|---|
| frontend API | typed Project Context API types and client methods |
| frontend product | Project page route/surface, Context section/related-node components and styles |
| frontend tests | component/API state, accessibility, responsive and real-data-only tests |
| final evidence | PATCH-048 validation/review governance artifacts only after all implementation batches pass |

Backend implementation is not broadened except an in-scope contract correction
proven necessary by focused integration evidence. No migration is allowed.

### Acceptance and focused evidence

Prove ten typed sections, truthful states/no fake totals, API protected state
non-disclosure, continuation UX, related one-hop navigation, no raw-ID input,
semantic accessibility, keyboard operation, responsive layout and no AI/editor
scope. Run focused frontend tests and the smallest Project-page/API adjacent
regression. No full frontend build/suite occurs until final validation.

## 7. Final validation and governance gates

After all four batches are accepted, run once:

- complete PATCH-048 focused backend suite, owner-port contracts, section/state/
  bound/cursor/node/edge/one-hop/target-authorization/tenant/project/
  non-disclosure/Human-exclusion evidence;
- full backend suite once;
- focused frontend suite, full frontend suite once, typecheck and production
  build once;
- verify sole Alembic head e04700000001 and no PATCH-048 migration;
- static/import, exact-scope, secret/non-disclosure and fake-production-data
  checks; and
- git diff --check.

Final evidence must preserve batch review/remediation chronology. Independent
final review follows its own later authority; this Plan grants none of it.

## 8. Batch gates and hard stops

For every batch, the separately created manifest defines exact files, acceptance
criteria, focused validation, smallest adjacent regression, independent review,
amendment/re-review and Human acceptance. A batch cannot advance with a Critical
or Major finding.

Stop if a batch needs to change Architecture/EDS/IDS, source persistence/migration,
a port beyond the accepted owner-side addition, a generic graph/security
subsystem, hidden authority, or PATCH-049 behavior. Preserve unrelated work
throughout.
