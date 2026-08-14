# PATCH-034 Batch 6 Authorized File Manifest

## 1. Authority and Scope

| Item | State |
|---|---|
| PATCH | PATCH-034 — Engineering Organizational Memory |
| Batch | Batch 6 — Transport Integration |
| Steps | S13–S14 only |
| Batches 1–5 | HUMAN ACCEPTED / COMPLETE |
| Human Batch 6 preparation authority | GRANTED |
| Batch 6 implementation authority | NOT GRANTED |
| Batch 7 authority | NOT GRANTED |

This manifest is the complete and exclusive Batch 6 implementation boundary.
It grants no implementation authority. Batch 6 may begin only after separate
Human implementation authority for this exact boundary.

## 2. Repository and Dependency Assessment

Accepted Batches 1–5 already provide the seven closed application operations,
strict request/result schemas, Organizational Memory service, same-Session UoW,
canonical Technical Report and provenance adapters, mutation reliability,
protected reads, and bounded continuation behavior required by S13–S14.

The current repository has an authenticated, server-derived Organization
dependency and established request-scoped composition and router-registration
patterns. Therefore Batch 6 requires no accepted domain/application contract,
canonical capability, persistence, migration, role, credential, or
configuration change.

## 3. Exact Authorized File Boundary

### 3.1 Production

| File | Action | Step | Authorized responsibility | Why required | Prohibited responsibility |
|---|---|---|---|---|---|
| `backend/app/dependencies/organizational_memory.py` | CREATE | S13 | Define the request-scoped application composition root. Obtain the authenticated User and server-derived selected Organization context; construct `MemoryActor`; privately compose the accepted Organizational Memory UoW factory, post-rollback rejection-Audit collaborator, accepted Technical Report reader, four canonical provenance application services/adapters, clock, and accepted `OrganizationalMemoryService`; expose one application-owned dependency to transport. | S13 requires infrastructure and canonical-service construction outside the router while preserving request scope and canonical ownership. | No HTTP parsing/serialization; no new authority rule; no client-derived Organization; no direct foreign canonical repository/ORM/UoW access; no new transaction, persistence, lifecycle, digest, pagination, or result semantics; no shared mutable request authority. |
| `backend/app/api/v1/routers/organizational_memory.py` | CREATE | S14 | Expose only the seven accepted V1 operations—`admit`, `get_active`, `list_active`, `inspect_history`, `create_successor`, `withdraw`, and `supersede`. Parse strict transport inputs and required correlation/idempotency metadata, obtain the S13 application dependency, derive all actor/Organization authority from it, invoke exactly one corresponding application method, and serialize only the accepted closed result schema. | S14 requires a thin authenticated HTTP boundary for the complete accepted V1 application surface. | No Session/repository/UoW/policy/canonical-service construction; no authorization, projection, digest, lifecycle, idempotency, pagination, continuation, or transaction policy; no client actor/Organization authority; no generic update/delete, search, publication, governance-audit, or deferred endpoint. |
| `backend/app/main.py` | MODIFY | S14 | Import and register only the Organizational Memory router. | The accepted routes must be reachable through the existing application entry point. | No unrelated router, middleware, configuration, startup, database, or application behavior change. |

### 3.2 Tests

| File | Action | Step | Authorized responsibility | Why required | Prohibited responsibility |
|---|---|---|---|---|---|
| `backend/tests/test_organizational_memory_api.py` | CREATE | S13–S14 | Prove real authentication and selected-Organization context, request-scoped composition, exact methods/routes/request shapes, all seven application delegations, exact success/result serialization, stable payload-free protected outcomes, mutation metadata handling, continuation pass-through, positive disclosure boundaries, and prohibited-route absence. | The accepted Plan assigns focused API and transport-contract evidence to a dedicated suite. | No production-policy substitute; no migration/schema testing; no Batch 7 evidence packaging; no frontend, AI, search, or deferred behavior. |
| `backend/tests/test_organizational_memory_security.py` | MODIFY | S13–S14 | Extend accepted security evidence through the real HTTP/authentication boundary: inactive/unauthenticated User, inactive Organization, disabled/unselected/nonmember context, cross-Organization/client-context conflict, Project/Workspace/audience/source/provenance denial, revocation, payload-free protected mapping, plaintext/diagnostic exclusion, and preservation of mutation/read authorization semantics. | Existing application security evidence must remain true at the transport boundary. | No accepted authorization-policy change; no new roles; no weakening of prior tests; no direct foreign persistence; no Batch 7 or deferred capability evidence. |

The exact Batch 6 implementation boundary is:

```text
CREATE backend/app/dependencies/organizational_memory.py
CREATE backend/app/api/v1/routers/organizational_memory.py
MODIFY backend/app/main.py
CREATE backend/tests/test_organizational_memory_api.py
MODIFY backend/tests/test_organizational_memory_security.py
```

No other production, test, documentation, migration, configuration, or
canonical-capability file is authorized for Batch 6 implementation.

## 4. S13 and S14 Mapping

### S13 — Request-scoped Application Composition

- use the existing authenticated Organization-context dependency as the sole
  source of User and Organization authority;
- construct `MemoryActor(actor_id=context.user.id,
  organization_id=context.organization_id)` only from trusted server state;
- keep construction of Session/UoW, repositories, authorization policy,
  post-rollback Audit, canonical services, adapters, and clock exclusively in
  the dependency/composition module;
- provide the router one request-scoped application object containing only the
  accepted Organizational Memory service and trusted actor/context needed to
  build existing commands and read requests;
- preserve canonical-service-owned read-only UoWs and one authoritative
  Organizational Memory transaction for mutations; and
- introduce no ambient/global mutable actor, Organization, Session, service,
  continuation, or authority state.

### S14 — Thin Authenticated API

The router exposes only these accepted operations:

1. `admit`;
2. `get_active`;
3. `list_active`;
4. `inspect_history`;
5. `create_successor`;
6. `withdraw`; and
7. `supersede`.

Exact HTTP paths/methods may follow repository REST conventions but must be
one-to-one with these operations, must use the existing strict Batch 1 request
schemas, and may not add alternate or generic mutation routes. Organization and
actor identity are never accepted as client authority. Any Organization field
present in an existing request shape is checked against and replaced/derived
from trusted server context before application invocation.

Transport maps each application-owned result only to its corresponding closed
response union. `protected_not_found`, `invalid_request`, `unavailable`, and
other accepted operation-specific outcomes contain only their discriminator;
transport adds no reason, identity, standing, count, path, provenance,
exception, or diagnostic. Continuation strings are passed unchanged between
the accepted list request/result contracts; the router does not inspect,
construct, or authorize them.

## 5. Prerequisites and Dependencies

Implementation may start only while all of the following remain true:

1. PATCH-034 Architecture, EDS-034, IDS-034, Implementation-Plan-034, and
   IRR-034 remain accepted and technically unchanged.
2. Batches 1–5 remain Human ACCEPTED / COMPLETE with every Critical/Major
   review finding resolved.
3. Batch 1 strict commands, read requests, schemas, result unions, actor, and
   scope contracts remain authoritative and require no change.
4. Batch 2 repository, migration, runtime-role, DB-guard, and no-commit
   boundaries remain unchanged.
5. Batch 3 canonical integrations remain the exclusive Technical Report and
   provenance application boundaries; no foreign persistence access is needed.
6. Batch 4 UoW, command, final-recheck, Audit/outbox/idempotency/rollback, and
   optimistic-concurrency behavior remains unchanged.
7. Batch 5 read authorization, source revocation, history protection,
   all-or-nothing provenance, continuation, and bounded-query behavior remains
   unchanged.
8. Existing `get_current_user_organization_context` continues to establish an
   authenticated active User and enabled selected membership in an active
   Organization.
9. Existing request-scoped constructors can compose all accepted canonical
   application services without modifying their production files.

## 6. Required Composition, Authentication, and API Evidence

Batch 6 focused evidence must materially prove:

1. the router imports or receives no SQLAlchemy `Session`, `SessionLocal`, ORM
   model, repository, UoW, authorization-policy implementation, reference
   validator, or canonical infrastructure implementation;
2. only `backend/app/dependencies/organizational_memory.py` owns request-scoped
   Organizational Memory/canonical composition;
3. each request receives a fresh application composition and no authority or
   transaction state is shared across requests;
4. actual JWT authentication and selected Organization resolution feed the
   application actor; unauthenticated, inactive, disabled, unselected,
   nonmember, and cross-Organization cases fail before application disclosure;
5. client input cannot select or override actor or Organization authority;
6. each of the seven routes delegates to exactly one matching application
   service operation with exact accepted request fields and metadata;
7. every success response exactly matches its accepted schema, including
   standing-specific history and visible-only list results;
8. all closed protected/error variants preserve exact discriminator-only
   payloads and stable mapping without internal exception text or protected
   plaintext;
9. current-source revocation, provenance all-or-nothing behavior, audience and
   scope denial, linked-Human protection, version/idempotency conflicts, and
   pagination/continuation behavior are not reinterpreted by transport;
10. mutation routes preserve correlation/idempotency requirements and expose
    no transport-owned retry, transaction, Audit, or outbox behavior;
11. prohibited route inspection confirms absence of generic update/delete,
    governance-audit, search, semantic/vector, AI, publication, cross-
    Organization, additional-source, bulk/batch, or deferred endpoints; and
12. Batches 1–5 focused regressions, static/import checks, route scans,
    exact-file/prohibited-pattern checks, and `git diff --check` pass.

## 7. Explicit Exclusions and Scope Control

Batch 6 may not create, modify, or claim:

- any Batch 1–5 domain model, schema, port, exception, adapter, service,
  repository, UoW, migration, DB role, or focused test except the exact
  security-test extension listed in Section 3;
- any canonical Technical Report, Capture, Evidence, Engineering Object,
  Engineering Relationship, authentication, Organization, Project, or
  Workspace production/test contract;
- direct foreign repository/ORM/Session/UoW access from Organizational Memory
  transport or adapters;
- router-owned authorization, source/provenance resolution, lifecycle,
  projection, digest, standing, concurrency, idempotency, Audit, outbox,
  rollback, pagination, continuation, or persistence logic;
- Batch 7 regression, QG-M1, validation-evidence, final-review, delivery, or
  closure work;
- frontend/UI, AI/Copilot, semantic/vector/relevance search, embeddings, graph
  expansion/ranking, other admission sources, multi-source synthesis, cross-
  Organization sharing, autonomous admission/reuse, enterprise boards,
  EDS-030/031 behavior, or any other deferred capability; or
- canonical ownership or authority changes.

Scope validation must compare the implementation diff to the five paths in
Section 3, inspect router and dependency imports, enumerate registered routes,
and reject any unrelated hunk, transport policy, foreign persistence import,
client-trusted authority, new result semantic, deferred route, or Batch 7
artifact. Unrelated worktree changes remain untouched and outside Batch 6.

## 8. Stop Conditions

Stop Batch 6 immediately and report BLOCKED if:

1. an accepted PATCH/EDS/IDS/Plan or Batch 1–5 contract must change;
2. any file outside the exact five-file boundary is required;
3. the router must import/construct a Session, repository, UoW, policy,
   validator, canonical service infrastructure, or persistence collaborator;
4. actor or Organization authority must be accepted from client input;
5. accepted canonical services cannot be composed request-scoped without
   foreign persistence access or canonical production changes;
6. a route cannot map one-to-one to an accepted operation/result union without
   inventing transport semantics;
7. a protected outcome cannot remain discriminator-only and non-disclosing;
8. authentication or Organization-context denial occurs after application
   disclosure;
9. read revocation, provenance, linked identity, pagination, continuation,
   concurrency, idempotency, or mutation semantics would be reimplemented or
   weakened in transport;
10. a generic mutation, governance-audit, search, frontend, AI, deferred, or
    other non-V1 route becomes necessary;
11. any Batch 7 validation/evidence work is required to claim Batch 6 complete;
12. focused/API/security or relevant Batch 1–5 regression fails and repair
    requires an unauthorized file; or
13. static/import, route-surface, exact-scope, prohibited-pattern, or
    `git diff --check` validation fails.

## 9. Readiness and Authority

The accepted contracts and completed Batches 1–5 support S13–S14 within the
exact five-file boundary above.

Batch 6 implementation readiness: READY

Batch 6 implementation authority: NOT GRANTED

Batch 7 authority: NOT GRANTED

Exact next governance action: Human review of this manifest and, if accepted,
separate Batch 6 implementation authority for the exact five-file boundary.
