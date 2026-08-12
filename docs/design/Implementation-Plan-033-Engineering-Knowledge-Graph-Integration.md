# Implementation-Plan-033 — Engineering Knowledge Graph Integration

## 1. Document Control

| Field | Value |
|---|---|
| Document ID | Implementation-Plan-033 |
| Related PATCH | PATCH-033 — Engineering Knowledge Graph Integration |
| Governing EDS | EDS-033 — ACCEPTED / COMPLETE |
| Governing IDS | IDS-033 — ACCEPTED / COMPLETE |
| Plan version | 1.0 |
| Status | ACCEPTED / COMPLETE |
| Human IDS Acceptance | PASS |
| Planning authority | GRANTED |
| Independent Plan Review | PASS after focused amendment and re-review |
| Human Plan Acceptance | PASS |
| Permission for IRR-033 | GRANTED |
| IRR-033 | PENDING RE-REVIEW |
| Implementation authority | NOT GRANTED |
| Migration authority | NOT REQUIRED / NOT GRANTED |
| Commit / push authority | NOT GRANTED |
| Date | 2026-08-12 |

This plan translates only the accepted executable IDS-033 Version-1 contract
into dependency-ordered work. It grants no implementation authority.

## 2. Governing Boundary and Repository Reality

Authority applies in this order: accepted PATCH-033, accepted EDS-033,
accepted IDS-033, preserved PATCH-033 reviews, current canonical repository
contracts, and SATCO repository conventions.

The executable boundary contains one node type, `engineering_object`, and one
operation, `get_node`. The current Engineering Object application capability
already provides an authorized single-object read returning
`EngineeringObjectResponse`. It applies its canonical authorization policy and
protected-not-found behavior before returning that response. Trusted current
User and server-derived Organization context are available through the current
authentication dependency. Repository inspection does not establish a neutral
`GraphActor`-compatible exact-scope authorization contract in the current
Project or Workspace application boundaries; this plan neither assumes nor
invents one.

No accepted contract requires a change to Engineering Object, Project,
Workspace, authentication, persistence, or transaction behavior. V1 first
establishes the trusted actor and server-derived Organization context, then
uses the existing authorized Engineering Object read. That canonical read
authorizes visibility in the object's actual Project and Workspace scope. If
optional `GraphScope.project_id` or `GraphScope.workspace_id` is supplied, EKG
compares it to the corresponding field of the already authorized canonical
response before constructing any graph projection. A mismatch produces the
same payload-free protected outcome and discloses no canonical response field.
No separate Project/Workspace authority is inferred. Direct repository, ORM,
Session, or Unit-of-Work access is prohibited. If this sequence cannot be used
without changing a canonical contract, work stops for architecture
reconciliation.

Dependency direction is:

```text
closed EKG DTOs and inward ports
→ canonical application adapters
→ node-only EKG service
→ thin transport and request-scoped composition
→ focused evidence
→ adjacent and full regression
→ independent review and Human governance
```

## 3. Executable V1 and Deferred Separation

### 3.1 Executable PATCH-033 V1

- `GraphActor {actor_id: int, organization_id: UUID}`;
- `GraphScope {organization_id: UUID, project_id: int | None, workspace_id:
  int | None}`;
- `GraphNodeRequest {node_id: UUID}`;
- `GraphReadService.get_node(actor, scope, request) -> GraphNodeResult`;
- one authorized canonical Engineering Object read;
- one successful `GraphNodeProjection`, with exact
  `EngineeringObjectResponse` field parity and `node_type` solely as
  `Literal["engineering_object"]` contract discriminator;
- payload-free `protected_not_found`, `invalid_request`, and `unavailable`;
- authorization-before-disclosure, read-only execution, and bounded calls.

### 3.2 Deferred / Non-blocking Future Prerequisites

Edges, relationship frontiers, traversal, paths, depth, breadth, fan-out,
cycles, pagination, continuation, provenance, Evidence projection, additional
node types, batch reads, and graph-owned state remain deferred. They create no
production file, port, DTO, route, test acceptance gate, or implementation
task in this plan. Future work requires separate canonical prerequisites,
focused IDS amendment and acceptance, a revised plan, and new implementation
authority.

### 3.3 Validation, Review, and Closure

Validation proves only the executable V1 boundary. Independent implementation
review, Human quality-gate acceptance, delivery authorization, commit, push,
and PATCH closure remain separate governance actions and are not granted by
this plan.

## 4. Expected Repository Surfaces

These are planning surfaces, not an authorized file manifest. Each
implementation batch requires a separately accepted exact-file manifest.

### 4.1 Expected production surfaces

| Expected path | Status | Exact purpose |
|---|---|---|
| `backend/app/schemas/engineering_knowledge_graph.py` | CREATE | Closed actor, scope, request, projection, and result DTOs with exact canonical field types |
| `backend/app/ports/engineering_knowledge_graph.py` | CREATE | Trusted-context decision, single-node canonical read, and graph read service protocols only |
| `backend/app/adapters/engineering_knowledge_graph.py` | CREATE | Trusted-context and authorized Engineering Object adapters plus pre-projection optional scope equality; no Project/Workspace authority or persistence access |
| `backend/app/services/engineering_knowledge_graph_service.py` | CREATE | Authorization-first `get_node` orchestration and exact projection mapping |
| `backend/app/api/v1/routers/engineering_knowledge_graph.py` | CREATE | Thin authenticated node-read transport and result serialization |
| `backend/app/main.py` | MODIFY | Register only the accepted EKG router |

No enum, model, repository, Unit of Work, migration, table, configuration,
Audit, outbox, idempotency, cache, worker, command, or mutation surface is
expected or permitted.

### 4.2 Expected test and evidence surfaces

| Expected path | Status | Exact evidence purpose |
|---|---|---|
| `backend/tests/test_engineering_knowledge_graph_contracts.py` | CREATE | DTO closure, exact field parity, discriminator-only `node_type`, closed results, prohibited fields |
| `backend/tests/test_engineering_knowledge_graph_service.py` | CREATE | One-node success, orchestration, scope matching, result mapping, read-only behavior |
| `backend/tests/test_engineering_knowledge_graph_security.py` | CREATE | Authentication, Organization/membership, cross-scope equivalence, non-disclosure, bounded calls |
| `backend/tests/test_engineering_knowledge_graph_api.py` | CREATE | Real request context, thin transport, stable outcome serialization, prohibited routes |
| `docs/reviews/PATCH-033-Implementation-Validation-Evidence.md` | CREATE in final validation batch only | Exact commands, results, scope scans, QG-M1 and regression evidence |

Existing canonical tests are regression inputs and are not expected to be
modified. A need to modify them is a stop condition unless separately reviewed
and authorized.

## 5. Dependency-Ordered Steps

### S01 — Closed Contract Foundation

- **Purpose:** Define the complete executable V1 actor, scope, request,
  projection, four result variants, and inward protocols.
- **Production surface:** EKG schemas and ports only. Canonical exceptions are
  translated by adapters into the accepted closed result variants; EKG defines
  no separate exception surface.
- **Test/evidence surface:** Contract tests proving exact types, optionality,
  cardinality, discriminator semantics, excess-field rejection, and absence of
  deferred DTOs and ports.
- **Dependencies:** Accepted IDS-033 and current `EngineeringObjectResponse`.
- **Security obligations:** Organization is trusted/server-derived;
  non-success results are payload-free; no client authority field exists.
- **Acceptance criteria:** `node_id` remains UUID; every canonical field has
  exact type parity; success has exactly one node; no batch contract exists.
- **Stop conditions:** Any field needs derivation, stronger validation than the
  canonical response, deferred data, or a canonical contract modification.

### S02 — Trusted Context and Engineering Object Adapter

- **Purpose:** Establish trusted actor/server-derived Organization context,
  invoke the existing authorized Engineering Object single read, and compare
  any supplied optional Project/Workspace scope to the authorized response
  before graph projection.
- **Production surface:** EKG adapter module only.
- **Test/evidence surface:** Adapter fakes/contract evidence for active and
  inactive actors, Organization membership/state, canonical protected reads,
  optional exact Project/Workspace matching and mismatch, and capability
  unavailability.
- **Dependencies:** S01; existing trusted authentication/Organization context
  and authorized Engineering Object application read.
- **Security obligations:** Trusted actor and Organization are established
  first. No projection occurs until the canonical object read authorizes
  visibility. Optional scope values must equal the authorized response;
  mismatches are protected and expose no response field or denial source.
- **Acceptance criteria:** An invalid trusted actor/Organization decision
  performs zero object reads. Otherwise exactly one authorized canonical read
  is permitted. Optional scope mismatch occurs only after that authorized read
  and before projection. No Project/Workspace adapter or persistence access is
  introduced.
- **Stop conditions:** The sequence requires a separate Project/Workspace
  authority, direct repository/ORM access, a canonical service change, or a
  batch/frontier operation.

### S03 — Node-only Application Service

- **Purpose:** Implement the single `get_node` orchestration and exact mapping
  from an authorized `EngineeringObjectResponse` to `GraphNodeProjection`.
- **Production surface:** EKG application service only.
- **Test/evidence surface:** Service and security tests for success and every
  closed result, scope matching, authorization order, call counts, projection
  parity, side-effect absence, and unavailable collaborators.
- **Dependencies:** S01–S02.
- **Security obligations:** Fail closed; missing and inaccessible are
  equivalent; protected, invalid and unavailable results disclose no payload;
  logs/errors contain no protected values.
- **Acceptance criteria:** Exactly one-node success; `node_type` is added only
  as the closed discriminator; canonical values are copied without synthesis;
  no mutation, transaction, Audit, idempotency, outbox, or concurrency effect.
- **Stop conditions:** A second graph operation, second node type, deferred
  concept, canonical write, or unbounded/additional canonical call is needed.

### S04 — Thin Transport and Request-scoped Composition

- **Purpose:** Expose only the accepted node read through authenticated,
  request-scoped composition.
- **Production surface:** EKG router and router registration in `main.py`.
- **Test/evidence surface:** API tests using trusted authentication and
  Organization context; stable success/protected/invalid/unavailable response
  bodies; prohibited-route verification.
- **Dependencies:** S01–S03.
- **Security obligations:** Transport owns no authorization, projection,
  persistence, or transaction rule; it cannot accept Organization authority;
  it serializes application-owned outcomes only.
- **Acceptance criteria:** One node-read route only; response mapping preserves
  payload-free failures; no route for list, edge, traversal, search, or write.
- **Stop conditions:** Transport must infer authority, query persistence,
  construct canonical state, or add an unaccepted operation.

### S05 — Focused Application and Security Evidence

- **Purpose:** Close executable-V1 behavioral evidence before broad regression.
- **Production surface:** None unless an authorized focused test proves a
  defect inside the same batch manifest.
- **Test/evidence surface:** Contract, service, security, and API suites.
- **Dependencies:** S01–S04.
- **Security obligations:** Prove active/inactive actor, active/disabled or
  nonmember Organization, cross-Organization, optional cross-Project and
  cross-Workspace, nonexistent/inaccessible object equivalence, field and
  plaintext exclusion, and authorization-before-disclosure.
- **Acceptance criteria:** Exact projection parity; deterministic four-outcome
  behavior; one bounded scope decision and at most one object read; denied
  trusted actor/Organization causes zero object reads; optional Project or
  Workspace mismatch consumes one authorized object read but returns no
  projection; authoritative state remains unchanged.
- **Stop conditions:** Any failure requires a file outside the authorized
  batch, a canonical contract change, or deferred capability behavior.

### S06 — Regression, Static, and Scope Evidence

- **Purpose:** Demonstrate compatibility and exact scope before final review.
- **Production surface:** None.
- **Test/evidence surface:** Adjacent authentication/Organization, Project,
  Workspace, Engineering Object, Engineering Relationship, Evidence, Capture,
  Journal, and Technical Report regressions; full backend regression; static
  compilation/import checks; prohibited-pattern and exact-file scans; route
  surface check; `git diff --check`; final QG-M1 assessment.
- **Dependencies:** S05 PASS.
- **Security obligations:** Verify no persistence access, graph writes,
  deferred DTO/ports/routes, hidden totals, protected diagnostics, or
  client-trusted Organization scope.
- **Acceptance criteria:** All focused and required regressions pass with zero
  failures; no unauthorized file; no prohibited pattern; QG-M1 PASS.
- **Stop conditions:** Any failed validation, scope drift, stale governance,
  unrelated included change, or need for remediation during evidence packaging.

### S07 — Independent Review and Human Gate Package

- **Purpose:** Package immutable evidence for Independent Final Implementation
  Review and later Human quality gates without promoting authority.
- **Production surface:** None.
- **Test/evidence surface:** Validation evidence document containing commands,
  counts, environment, exact file boundary, findings disposition, deferred
  exclusions, and QG-M1 result.
- **Dependencies:** S06 PASS.
- **Security obligations:** Evidence contains no credentials or protected
  engineering content.
- **Acceptance criteria:** Reviewers can independently reproduce scope and
  results; deferred prerequisites remain explicitly non-blocking.
- **Stop conditions:** Missing evidence, unresolved finding, inconsistent
  governance state, or failed final review.

## 6. Independently Authorized Batch Strategy

### Batch 1 — Contracts and Projection Foundation (`S01`)

Creates only closed DTO, port, and contract-test surfaces. Exit
requires independent confirmation of canonical field parity, four outcomes,
single-node cardinality, and absence of batch/deferred contracts.

### Batch 2 — Canonical Composition and Application (`S02–S03`)

Creates adapters and the node-only service plus focused service/security tests.
Entry requires accepted Batch 1. Exit requires independent confirmation of
authorization-before-disclosure, scope matching, bounded calls, read-only
behavior, and protected equivalence.

### Batch 3 — Transport Integration (`S04–S05`)

Creates the thin router, registers it, and completes API/security evidence.
Entry requires accepted Batch 2. Exit requires independent confirmation of
request-scoped composition, stable result mapping, real authentication context,
and absence of prohibited routes or deferred behavior.

### Batch 4 — Regression and Final Evidence (`S06–S07`)

Runs adjacent/full regression and static/scope checks, records QG-M1 evidence,
and packages final review material. It permits no new production behavior.
Delivery, commit, push, and closure require later separate Human authority.

Each batch requires its own Human implementation authority and exact-file
manifest after the preceding batch is independently and Human accepted. No
later batch is implicitly authorized.

## 7. Required Validation Evidence

The final evidence package must record exact commands and results for:

1. EKG contract tests;
2. EKG service tests;
3. EKG security/non-disclosure tests;
4. EKG API and request-context tests;
5. canonical Engineering Object projection parity;
6. bounded-call instrumentation: invalid trusted actor/Organization causes zero
   object reads; otherwise at most one authorized object read; optional
   Project/Workspace mismatch returns protected after that read and before
   projection;
7. authoritative-state before/after equality and no-write proof;
8. prohibited route, import, persistence, model, repository, UoW, migration,
   Audit, idempotency, outbox, edge, traversal, pagination, continuation,
   provenance, batch, and additional-node scans;
9. adjacent canonical regressions listed in S06;
10. full backend regression;
11. static compilation and import validation;
12. exact authorized-file verification;
13. `git diff --check`;
14. final Manifesto/QG-M1 traceability assessment.

No test may weaken or skip an existing canonical regression. Database
migration execution is neither required nor authorized because PATCH-033 V1
creates no persistence.

## 8. Global Stop Conditions and Plan Decision

All work stops if:

- current boundaries cannot establish trusted actor/Organization context,
  authorize one Engineering Object in its canonical scope, and compare supplied
  optional Project/Workspace values before projection without architecture or
  canonical-contract changes;
- exact projection parity cannot be maintained;
- any edge, traversal, path, pagination, continuation, provenance, batch read,
  relationship frontier, or additional node type becomes necessary;
- any graph-owned state, mutation, persistence, transaction, lifecycle, Audit,
  concurrency, idempotency, outbox, migration, or cache is proposed;
- an implementation batch requires an unlisted surface before manifest
  reconciliation and Human authority;
- validation fails, protected information is disclosed, or scope expands.

Repository inspection found no current blocker to implementing the accepted
single-node V1 through existing canonical application boundaries.

```text
Implementation-Plan-033: ACCEPTED / COMPLETE
Independent Plan Review: PASS AFTER FOCUSED AMENDMENT AND RE-REVIEW
Human Plan Acceptance: PASS
Permission for IRR-033: GRANTED
IRR-033: PENDING RE-REVIEW
Executable scope: SINGLE ENGINEERING OBJECT NODE / GET_NODE ONLY
Deferred prerequisites: PRESERVED / NON-BLOCKING
Implementation authority: NOT GRANTED
Migration authority: NOT REQUIRED / NOT GRANTED
Commit / push authority: NOT GRANTED
```
