# PATCH-033 — Batch 2 Authorized File Manifest

## 1. Document Control

| Field | Value |
|---|---|
| PATCH | PATCH-033 — Engineering Knowledge Graph Integration |
| Batch | Batch 2 — Canonical Composition and Application |
| Steps | S02–S03 |
| Batch 1 status | ACCEPTED / COMPLETE |
| Preparation authority | GRANTED |
| Batch 2 implementation authority | NOT GRANTED |
| Batch 3 authority | NOT GRANTED |
| Manifest status | COMPLETE — READY FOR HUMAN BATCH 2 IMPLEMENTATION AUTHORITY |

This manifest authorizes no implementation by itself. It fixes the maximum
file boundary that a later explicit Human Batch 2 implementation decision may
authorize.

## 2. Governing Boundary

Batch 2 implements only the accepted executable V1 composition for one
`engineering_object` node and one `get_node` operation. It establishes trusted
actor and server-derived Organization context, performs one authorized
canonical Engineering Object read, checks supplied optional Project/Workspace
criteria against the already-authorized canonical response, and maps that
response to the closed projection contract created in Batch 1.

It owns no canonical authority, persistence, transaction, state, lifecycle,
Audit, idempotency, concurrency, outbox, or write behavior.

## 3. Exact Authorized File Boundary

### 3.1 Production files

| Operation | Exact path | Step | Exact purpose |
|---|---|---|---|
| CREATE | `backend/app/adapters/engineering_knowledge_graph.py` | S02 | Implement the Batch 1 trusted-context decision and single authorized canonical Engineering Object read ports. Translate the neutral `GraphActor` into the existing canonical read actor/context at the approved adapter boundary; translate canonical protected/unavailable outcomes into the closed Batch 1 outcomes; compare optional Project/Workspace scope only to the authorized `EngineeringObjectResponse`. It may call canonical application/read boundaries only and may not access repositories, ORM rows, Sessions, UoWs, routers, or Project/Workspace persistence or infer separate Project/Workspace authority. |
| CREATE | `backend/app/services/engineering_knowledge_graph_service.py` | S03 | Implement only `GraphReadService.get_node`: trusted-context decision first, at most one authorized canonical read, optional scope equality after authorized resolution and before projection, exact canonical-field projection plus discriminator-only `node_type`, and closed payload-free result mapping. It contains no transport, persistence, transaction, or deferred graph behavior. |

### 3.2 Test files

| Operation | Exact path | Step | Exact purpose |
|---|---|---|---|
| CREATE | `backend/tests/test_engineering_knowledge_graph_service.py` | S02–S03 | Prove orchestration order, exact call bounds, one-node projection parity, optional Project/Workspace equality, all four closed results, exception/outcome translation, read-only behavior, and absence of synthesis or additional canonical calls. |
| CREATE | `backend/tests/test_engineering_knowledge_graph_security.py` | S02–S03 | Prove inactive actor, invalid/inactive Organization context, membership denial, canonical protected result, cross-Organization and optional Project/Workspace mismatch equivalence, authorization-before-disclosure, payload-free protected outcomes, protected-value exclusion from errors/logs/diagnostics, and unavailable behavior. Use typed fakes at the accepted inward boundaries; real HTTP authentication belongs to Batch 3. |

No existing production, test, schema, port, canonical Engineering Object, or
configuration file is authorized for modification in Batch 2.

## 4. S02 / S03 Mapping

### S02 — Trusted Context and Engineering Object Adapter

- establish the trusted actor and server-derived Organization decision before
  any canonical object read;
- translate `GraphActor` only at the canonical adapter boundary;
- call the existing authorized Engineering Object application read exactly
  once at most;
- preserve canonical authorization and protected-not-found behavior;
- compare optional `GraphScope.project_id` and `workspace_id` only with the
  corresponding fields on an authorized canonical response;
- convert a mismatch to the same payload-free protected result without
  revealing the authorized response or the mismatched field;
- translate canonical capability unavailability to the closed payload-free
  unavailable result.

S02 must not add a Project or Workspace authority adapter, query canonical
persistence, reuse a transport router as an application boundary, or change
the Engineering Object service or contracts.

### S03 — Node-only Application Service

- implement only `get_node(actor, scope, request)`;
- return `invalid_request` without a canonical read when the trusted request
  cannot satisfy the closed request contract;
- return `protected_not_found` for trusted-context denial, canonical protected
  outcomes, or optional Project/Workspace mismatch;
- return `unavailable` for canonical capability unavailability;
- on success construct exactly one `GraphNodeProjection` by copying the
  authorized `EngineeringObjectResponse` fields without derivation or stronger
  validation and adding only the closed `engineering_object` discriminator;
- perform no write and create no Audit, event, idempotency, transaction, cache,
  or graph-owned state effect.

## 5. Prerequisites and Dependencies

All of the following must remain true at implementation start:

1. Batch 1 is Human ACCEPTED / COMPLETE.
2. The accepted Batch 1 schemas and ports remain unchanged and importable.
3. `EngineeringObjectResponse` retains the accepted field/type/optionality
   contract used by `GraphNodeProjection`.
4. The existing Engineering Object application service continues to expose
   one authorization-aware `get` operation returning
   `EngineeringObjectResponse` or its protected canonical exception.
5. Existing authenticated Organization context establishes active User,
   active Organization, and active membership from server-trusted state.
6. No Project/Workspace authorization beyond equality with the authorized
   object response is required by the accepted IDS and plan.
7. No repository, database, migration, configuration, router, or main
   registration change is needed.

## 6. Required Test and Evidence Expectations

Batch 2 evidence must materially prove:

1. invalid trusted actor/Organization decisions cause zero Engineering Object
   reads;
2. all other paths make no more than one authorized canonical object read;
3. projection construction occurs only after trusted-context and canonical
   authorization success;
4. supplied Project/Workspace values are checked only after authorized
   resolution and before projection;
5. absent Project/Workspace criteria impose no additional filter;
6. Organization, Project, and Workspace mismatches are non-disclosing and
   result-equivalent to nonexistent/inaccessible nodes where applicable;
7. exact projection field values and types equal the authorized canonical
   response, with `node_type` used only as a discriminator;
8. success contains exactly one node and no additional envelope data;
9. `protected_not_found`, `invalid_request`, and `unavailable` remain
   payload-free and reject extra fields;
10. protected identifiers/fields and denial causes do not enter results,
    exceptions, logs, or diagnostics;
11. canonical protected and unavailable exceptions/outcomes are translated
    deterministically;
12. reads cause no mutation, commit, rollback ownership, Audit, idempotency,
    outbox, cache, or other side effect;
13. service and adapter imports point inward to Batch 1 contracts and outward
    only through the approved canonical application boundary;
14. Batch 1 contract tests and relevant Engineering Object service/schema
    regressions remain passing;
15. static/import validation, exact-file verification, prohibited-pattern
    scans, and `git diff --check` pass.

Expected focused commands include:

```text
python -m pytest -q tests/test_engineering_knowledge_graph_contracts.py tests/test_engineering_knowledge_graph_service.py tests/test_engineering_knowledge_graph_security.py
python -m pytest -q tests/test_engineering_object_schemas.py tests/test_engineering_object_service.py
python -m compileall -q app/adapters/engineering_knowledge_graph.py app/services/engineering_knowledge_graph_service.py tests/test_engineering_knowledge_graph_service.py tests/test_engineering_knowledge_graph_security.py
git diff --check
```

Environment-specific canonical regression commands may use the repository's
established test environment but may not weaken, skip, or replace the focused
evidence.

## 7. Explicitly Prohibited and Out of Scope

Batch 2 may not create or modify:

- any router, `backend/app/main.py`, transport DTO, route registration, or API
  test;
- Batch 1 schemas, ports, or contract tests;
- any Engineering Object production or test file;
- repositories, ORM models, tables, migrations, Sessions, UoWs, configuration,
  credentials, roles, workers, caches, Audit, idempotency, or outbox surfaces;
- edges, relationship semantics, traversal, paths, pagination, continuation,
  provenance, additional node types, frontier reads, or batch reads;
- graph mutations, writes, lifecycle, authoritative state, or transactions;
- frontend, semantic/vector search, Organizational Memory, Digital Twin,
  Technical Proposal Review, or autonomous AI behavior.

## 8. Stop Conditions

Stop Batch 2 without redesign or workaround if any of the following occurs:

1. implementation needs a file outside the exact four-file boundary;
2. a Batch 1 contract or accepted PATCH/EDS/IDS/plan contract must change;
3. the canonical Engineering Object read is not authorization-aware or cannot
   return the accepted response without direct persistence access;
4. trusted User/Organization/membership context cannot be consumed without
   transport ownership or duplicated authorization logic;
5. a separate or inferred Project/Workspace authority is required;
6. more than one canonical read, a batch/frontier operation, or a deferred
   graph capability is required;
7. optional scope checking would occur before canonical authorization or would
   disclose response content on mismatch;
8. the adapter/service must own a Session, repository, UoW, transaction, write,
   Audit, idempotency, outbox, or cache;
9. protected outcomes cannot remain payload-free and equivalent;
10. focused, adjacent, static, scope, or whitespace validation fails and the
    correction requires an unauthorized file.

## 9. Scope Verification

The implementation review must verify that the Batch 2 diff contains exactly
the four CREATE paths in §3 and no MODIFY path. Prohibited-pattern checks must
inspect production modules for router/FastAPI imports, persistence/ORM/Session
or UoW ownership, write verbs, batch/list/traversal/edge/continuation/provenance
contracts, and direct Project/Workspace authority. Test-only terms used to
assert prohibitions are not production capability leakage.

## 10. Authority State

Batch 2 implementation authority: NOT GRANTED

Batch 3 authority: NOT GRANTED

The exact next action is a separate Human decision granting or denying Batch 2
implementation authority against this manifest.
