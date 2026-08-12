# PATCH-033 — Batch 1 Authorized File Manifest

## 1. Manifest Control

| Field | Value |
|---|---|
| Related PATCH | PATCH-033 — Engineering Knowledge Graph Integration |
| Authorized batch | Batch 1 — Contracts and Projection Foundation |
| Implementation step | S01 only |
| Governing EDS | EDS-033 — ACCEPTED / COMPLETE |
| Governing IDS | IDS-033 — ACCEPTED / COMPLETE |
| Governing plan | Implementation-Plan-033 — ACCEPTED / COMPLETE |
| IRR-033 | PASS / Batch 1 READY |
| Human Batch 1 preparation authority | GRANTED |
| Manifest status | COMPLETE / READY FOR HUMAN IMPLEMENTATION AUTHORITY |
| Batch 1 implementation authority | NOT GRANTED |
| Batch 2 authority | NOT GRANTED |
| Migration authority | NOT REQUIRED / NOT GRANTED |
| Commit / push authority | NOT GRANTED |
| Date | 2026-08-12 |

This manifest defines the exact prospective S01 implementation boundary. Its
creation does not authorize implementation.

## 2. S01 Scope

Batch 1 may define only the closed executable Version-1 contracts for:

- `GraphActor {actor_id: int, organization_id: UUID}`;
- `GraphScope {organization_id: UUID, project_id: int | None, workspace_id:
  int | None}`;
- `GraphNodeRequest {node_id: UUID}`;
- the exact immutable `GraphNodeProjection` mapped from the canonical
  `EngineeringObjectResponse`, with `node_type` only as
  `Literal["engineering_object"]`;
- the closed `GraphNodeResult` variants: one-node `success`, payload-free
  `protected_not_found`, payload-free `invalid_request`, and payload-free
  `unavailable`;
- the single authorized Engineering Object read port, trusted-context/scope
  decision port, and `get_node` service protocol;
- contract-only evidence for field parity, optionality, cardinality,
  non-disclosure, and prohibited deferred contracts.

S01 contains no adapter, service implementation, router, registration,
canonical-capability change, or runtime composition.

## 3. Exact Authorized Production Files

| Path | State | S01 purpose |
|---|---|---|
| `backend/app/schemas/engineering_knowledge_graph.py` | CREATE | Define only the strict, frozen executable-V1 actor, scope, request, projection, canonical-read result, scope decision, and graph result DTOs. Preserve exact `EngineeringObjectResponse` field types and optionality; reject extra fields. |
| `backend/app/ports/engineering_knowledge_graph.py` | CREATE | Define Protocols only for trusted-context/scope decision, one authorized canonical Engineering Object read, and `GraphReadService.get_node`. Import typed DTOs; contain no implementation, persistence, batch, or deferred contract. |

Production file count: **2**.

No existing production file is authorized for modification. In particular,
`backend/app/schemas/__init__.py` and `backend/app/ports/__init__.py` remain
unchanged because direct capability-module imports are sufficient and no
accepted S01 requirement needs package exports.

## 4. Exact Authorized Test File

| Path | State | S01 purpose |
|---|---|---|
| `backend/tests/test_engineering_knowledge_graph_contracts.py` | CREATE | Prove exact DTO and Protocol closure, canonical field parity, discriminator-only `node_type`, four result variants, payload-free failures, one-node cardinality, strict request/scope shapes, and absence of batch/deferred contracts. |

Test file count: **1**.

Test helpers must remain local to this file. No existing test file may be
modified.

## 5. Exact Three-file Boundary

```text
CREATE backend/app/schemas/engineering_knowledge_graph.py
CREATE backend/app/ports/engineering_knowledge_graph.py
CREATE backend/tests/test_engineering_knowledge_graph_contracts.py
```

The subsequent implementation may create or modify exactly these three files
only after separate Human Batch 1 implementation authority is granted.

## 6. Prerequisites and Dependencies

| Prerequisite | Evidence | Status |
|---|---|---|
| PATCH-033 architecture | Accepted; QG-M1 PASS | SATISFIED |
| EDS-033 | ACCEPTED / COMPLETE | SATISFIED |
| IDS-033 | ACCEPTED / COMPLETE; final Independent re-review PASS; Human Acceptance PASS | SATISFIED |
| Implementation-Plan-033 | ACCEPTED / COMPLETE; Independent re-review PASS; Human Acceptance PASS | SATISFIED |
| IRR-033 | PASS; Batch 1 READY | SATISFIED |
| Canonical response | `backend/app/schemas/engineering_object.py::EngineeringObjectResponse` exists with every accepted field/type | SATISFIED |
| Enum types | Current Engineering Object enums exist and are importable | SATISFIED |
| Python/Pydantic/typing conventions | Existing schema and Protocol modules establish conventions | SATISFIED |
| Persistence/migration | Not required by S01 | SATISFIED |

Batch 1 depends only on accepted documentation, standard typing/UUID/datetime,
Pydantic v2, current Engineering Object response/enums, and existing Protocol
conventions. It does not depend on an EKG adapter, service implementation,
router, database, migration, or deferred canonical read prerequisite.

## 7. Contract and Acceptance Checks

A separately authorized Batch 1 implementation must prove:

1. `GraphActor` has exactly `actor_id: int` and `organization_id: UUID`;
2. `GraphScope` has exactly `organization_id: UUID`, `project_id: int | None`,
   and `workspace_id: int | None`;
3. `GraphNodeRequest` has exactly `node_id: UUID`;
4. `GraphNodeProjection` contains exactly:
   `node_type`, `node_id`, `organization_id`, `customer_id`, `project_id`,
   `workspace_id`, `family`, `discipline`, `object_type`, `subtype`,
   `lifecycle`, `authority_standing`, `version`, `creator_id`, `steward_id`,
   `created_at`, and `updated_at`;
5. all projection fields except `node_type` have exact canonical
   `EngineeringObjectResponse` types and optionality, with no stronger
   constraints or derived values;
6. `node_type` is exactly `Literal["engineering_object"]` and is documented as
   a response-contract discriminator rather than canonical Engineering Object
   data;
7. success contains exactly one projection;
8. `protected_not_found`, `invalid_request`, and `unavailable` are closed,
   payload-free results;
9. the canonical read port is single-node only and returns only resolved,
   protected, or unavailable typed results;
10. `get_node` is the only graph-service operation declared;
11. all DTOs reject extra fields and expose no protected diagnostic or denial
    source; and
12. static inspection proves no batch, edge, traversal, path, pagination,
    continuation, provenance, additional-node, persistence, transaction, or
    write contract exists.

Required validation after separately authorized implementation:

```text
python -m pytest -q tests/test_engineering_knowledge_graph_contracts.py
python -m compileall -q app/schemas/engineering_knowledge_graph.py app/ports/engineering_knowledge_graph.py
git diff --check
```

Validation must run from the repository's established backend environment.
Exact three-file scope and prohibited-pattern scans are mandatory.

## 8. Explicitly Prohibited Work

Batch 1 does not authorize:

- `backend/app/adapters/engineering_knowledge_graph.py`;
- `backend/app/services/engineering_knowledge_graph_service.py`;
- `backend/app/api/v1/routers/engineering_knowledge_graph.py`;
- modification of `backend/app/main.py` or package initializers;
- exception modules or additional production/test helpers;
- changes to Engineering Object, authentication, Organization, Project, or
  Workspace contracts or behavior;
- edges, relationship frontiers, traversal, paths, depth, breadth, fan-out,
  cycles, pagination, continuation, provenance, Evidence projection,
  additional node types, or batch reads;
- graph Aggregate, model, Repository, Unit of Work, Session, table, migration,
  cache, lifecycle, command, mutation, Audit, idempotency, concurrency, outbox,
  transaction, or any canonical write;
- Batch 2–4 work, full transport, delivery, commit, push, or deployment.

## 9. Stop Conditions

Implementation must stop and report the conflict if:

- any file outside the exact three-file boundary is required;
- any accepted actor, scope, request, projection, result, or port contract is
  missing, contradictory, or requires redesign;
- exact canonical field parity requires transformation, derivation, stronger
  constraints, or a canonical schema change;
- a batch read, adapter implementation, service behavior, transport behavior,
  persistence access, or deferred capability becomes necessary;
- a non-success result requires a payload, diagnostic, identifier, count, or
  denial source;
- compilation, focused tests, prohibited-pattern scans, exact-scope checks, or
  `git diff --check` fails and cannot be corrected within the same three files;
  or
- implementation authority, Batch 2 authority, or another governance gate is
  missing.

## 10. Readiness and Authority Decision

Repository assumptions and S01 dependencies are satisfied. The exact
three-file boundary is sufficient and minimal.

```text
Batch 1 manifest: COMPLETE
Batch 1 implementation readiness: READY
Batch 1 implementation authority: NOT GRANTED
Batch 2 authority: NOT GRANTED
Migration authority: NOT REQUIRED / NOT GRANTED
Commit / push authority: NOT GRANTED
```

The exact next action is Human review and an explicit bounded Batch 1
implementation-authority decision.
