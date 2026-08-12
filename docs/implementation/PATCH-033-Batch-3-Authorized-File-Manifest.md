# PATCH-033 — Batch 3 Authorized File Manifest

## 1. Document Control

| Field | Value |
|---|---|
| PATCH | PATCH-033 — Engineering Knowledge Graph Integration |
| Batch | Batch 3 — Transport Integration |
| Steps | S04–S05 |
| Batches 1–2 | ACCEPTED / COMPLETE |
| Preparation authority | GRANTED |
| Batch 3 implementation authority | NOT GRANTED |
| Batch 4 authority | NOT GRANTED |
| Manifest status | COMPLETE — READY FOR HUMAN BATCH 3 IMPLEMENTATION AUTHORITY |

This manifest grants no implementation authority. It defines the maximum exact
file boundary for a later separately authorized Batch 3 implementation.

## 2. Exact Authorized File Boundary

### 2.1 Production files

| Operation | Exact path | Step | Exact purpose |
|---|---|---|---|
| CREATE | `backend/app/api/v1/routers/engineering_knowledge_graph.py` | S04 | Add one thin authenticated `get_node` transport, request-scoped composition of the accepted Batch 2 adapters/service, optional Project/Workspace criteria, and serialization of application-owned closed results. Organization authority must come only from the existing server-derived authenticated Organization context. The router may not own authorization, projection, persistence, or transaction rules. |
| CREATE | `backend/app/dependencies/engineering_knowledge_graph.py` | S04 | Own request-scoped composition outside transport: construct the canonical Engineering Object service with its private infrastructure, compose the accepted EKG adapters/service, and derive `GraphActor` only from trusted authenticated Organization context. Expose one injectable application dependency to the router without transferring canonical ownership. |
| MODIFY | `backend/app/main.py` | S04 | Import and register only the accepted Engineering Knowledge Graph router. No other application registration or behavior may change. |

### 2.2 Test files

| Operation | Exact path | Step | Exact purpose |
|---|---|---|---|
| CREATE | `backend/tests/test_engineering_knowledge_graph_api.py` | S04–S05 | Prove the one-route HTTP contract, request-scoped composition, real authentication/Organization context, stable success and payload-free protected/invalid/unavailable serialization, optional scope criteria, and prohibited-route surface. |
| MODIFY | `backend/tests/test_engineering_knowledge_graph_security.py` | S05 | Extend Batch 2 evidence through the real authenticated transport boundary for active/inactive User, active/disabled or nonmember Organization, cross-Organization and optional Project/Workspace mismatch, nonexistent/inaccessible equivalence, plaintext exclusion, call bounds, and read-only behavior. Preserve all existing Batch 2 security evidence. |

No other production, test, documentation, configuration, migration, or
canonical-capability file is authorized for Batch 3 implementation.

## 3. S04 / S05 Mapping

### S04 — Thin Transport and Request-scoped Composition

- expose exactly one read operation for one Engineering Object node;
- use `GET /engineering-knowledge-graph/nodes/{node_id}` as the sole V1 graph
  route;
- accept optional `project_id` and `workspace_id` criteria only; never accept
  Organization or actor identity as client authority;
- obtain active authenticated User and selected active Organization membership
  only from `get_current_user_organization_context`;
- construct `GraphActor` and `GraphScope.organization_id` only from that trusted
  dependency;
- obtain the accepted canonical Engineering Object service, Batch 2 adapters,
  and graph service from the dedicated request-scoped composition dependency;
- delegate all authorization, canonical reading, scope equality, projection,
  and closed-outcome decisions to the application boundary;
- serialize application-owned `GraphNodeResult` variants without adding
  diagnostic, identity, count, or partial-node fields;
- register only this router in `main.py`.

Transport mapping must remain stable and explicit. Success returns the exact
one-node projection. Protected-not-found, invalid-request, and unavailable
responses remain payload-free apart from their closed status discriminator.
The router must not translate one protected case differently from another.

### S05 — Focused Application and Security Evidence

- rerun Batch 1–2 contract, service, and security suites;
- exercise actual authentication and selected Organization resolution through
  the HTTP dependency chain;
- prove active/inactive User, inactive Organization, disabled membership,
  nonmember/no-selected membership, cross-Organization, optional cross-Project
  and cross-Workspace, nonexistent/inaccessible, and unavailable outcomes;
- prove trusted-context denial causes zero canonical object reads;
- prove a valid trusted context causes at most one authorized canonical read;
- prove optional Project/Workspace mismatch is evaluated only after the
  authorized response, consumes one canonical read, and discloses no node;
- prove exact projection parity and discriminator-only `node_type` on success;
- prove response, error, log, and diagnostic plaintext exclusion;
- prove no state, Audit, idempotency, outbox, transaction, or write side effect;
- prove all prohibited graph routes are absent.

S05 creates no validation-evidence or final-review document. Batch 4 owns S06
and S07 regression/final-evidence packaging.

## 4. Prerequisites and Dependencies

Implementation may start only while all of these remain true:

1. Batches 1 and 2 are Human ACCEPTED / COMPLETE.
2. Batch 1 DTO/port contracts and Batch 2 adapter/service behavior remain
   unchanged and passing.
3. The existing authenticated Organization dependency continues to establish
   an active User and exactly one enabled selected membership in an active
   Organization.
4. Existing Engineering Object request-scoped composition can construct its
   canonical authorization-aware read without any canonical modification.
5. The composition dependency translates trusted context into `GraphActor`;
   the router derives `GraphScope.organization_id` from that actor without
   client-supplied Organization authority.
6. Optional Project/Workspace behavior remains equality-only against the
   already-authorized canonical response.
7. No persistence, migration, configuration, schema, service, adapter, port,
   or canonical contract modification is required.

## 5. Required Transport and Security Evidence

Batch 3 focused validation must include:

1. Batch 1 contract tests;
2. Batch 2 service and security tests;
3. Batch 3 API tests using actual token authentication and Organization-context
   resolution, with database/session boundaries overridden only where required
   for isolation;
4. exact success response parity with `EngineeringObjectResponse` plus only the
   closed `engineering_object` discriminator;
5. payload-free protected-not-found, invalid-request, and unavailable response
   bodies;
6. identical protected response shape for nonexistent, inaccessible, revoked,
   and cross-scope cases;
7. stable HTTP mapping without internal exception text, SQL, stack traces,
   protected identifiers, or canonical body fields;
8. zero/one canonical-read instrumentation and authorization-before-projection;
9. request-scoped dependency construction with no shared mutable authority;
10. absence of list, edge, traversal, path, search, pagination, continuation,
    provenance, additional-node, batch-read, and write routes;
11. no production import of canonical repositories, ORM models, Sessions,
    UoWs, Project/Workspace authority services, or deferred graph contracts;
12. relevant authentication/Organization and Engineering Object API/service
    regressions;
13. static compilation/import checks, exact-file verification,
    prohibited-pattern scans, route-surface inspection, and
    `git diff --check`.

Expected focused commands include:

```text
python -m pytest -q tests/test_engineering_knowledge_graph_contracts.py tests/test_engineering_knowledge_graph_service.py tests/test_engineering_knowledge_graph_security.py tests/test_engineering_knowledge_graph_api.py
python -m pytest -q tests/test_auth.py tests/test_authenticated_organization_context.py tests/test_engineering_object_api.py tests/test_engineering_object_service.py
python -m compileall -q app/api/v1/routers/engineering_knowledge_graph.py app/main.py tests/test_engineering_knowledge_graph_api.py tests/test_engineering_knowledge_graph_security.py
git diff --check
```

Exact adjacent filenames must follow current repository reality; missing named
examples do not authorize creating or modifying an adjacent test. Repository
test-environment setup may be used but tests may not be weakened or skipped.

## 6. Explicit Prohibitions

Batch 3 may not create or modify:

- Batch 1 schemas, ports, or contract tests;
- Batch 2 adapters, service, or service tests;
- any canonical Engineering Object, authentication, Organization, Project, or
  Workspace production or test surface;
- any repository, model, table, migration, Session/UoW contract,
  configuration, role, credential, worker, cache, Audit, idempotency, or outbox
  surface;
- any graph state, mutation, lifecycle, transaction, or write behavior;
- any batch read, additional node, edge, relationship frontier, traversal,
  path, pagination, continuation, provenance, search, or aggregate operation;
- any S06/S07 validation-evidence, final-review, delivery, or closure artifact;
- frontend, graph database, semantic/vector search, Organizational Memory,
  autonomous AI, Digital Twin, or Technical Proposal Review behavior.

## 7. Stop Conditions

Stop without workaround or redesign if:

1. implementation requires a file outside the exact five-file boundary;
2. an accepted PATCH/EDS/IDS/plan or Batch 1–2 contract must change;
3. the router must implement authorization, optional scope equality, projection,
   canonical exception policy, persistence, or transaction logic;
4. Organization or actor authority must be accepted from client input;
5. request-scoped composition requires direct canonical repository/ORM/Session
   access from transport rather than approved application construction;
6. a second graph route or operation is required;
7. a protected result cannot retain its closed payload-free shape;
8. real authentication/Organization evidence cannot be produced within the
   authorized tests and existing dependencies;
9. any deferred graph capability, persistence/write surface, or graph-owned
   state becomes necessary;
10. focused or adjacent validation fails and correction requires an
    unauthorized file;
11. exact-scope, prohibited-pattern, route-surface, static/import, or whitespace
    validation fails;
12. S06/S07 or Batch 4 work would be required to claim Batch 3 completion.

## 8. Exact Scope Checks

The Batch 3 diff must contain exactly the three CREATE and two MODIFY paths in
§2. Review must confirm that `main.py` changes consist only of router import and
registration, and that the existing security test changes only extend focused
EKG evidence. Production scans must reject authorization policy in transport,
direct persistence, graph writes, additional routes, batch/deferred DTOs or
operations, client-trusted Organization fields, and hidden diagnostic payloads.

Unrelated worktree changes remain outside this manifest and must not be staged,
altered, or attributed to Batch 3.

## 9. Authority State

Batch 3 implementation authority: NOT GRANTED

Batch 4 authority: NOT GRANTED

The exact next action is a separate Human Batch 3 implementation-authority
decision against this manifest.
