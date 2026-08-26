# PATCH-048 Batch 1 — Authorized File Manifest

## 1. Control

| Field | Value |
|---|---|
| PATCH | PATCH-048 — Governed Project Context Assembly & EKG Read Expansion |
| Batch | 1 — Typed Contracts and Owner Read-Port Prerequisites |
| Governing Architecture / EDS / IDS / Plan | ACCEPTED / COMPLETE |
| IRR-048 | PASS |
| Manifest status | ACCEPTED / COMPLETE |
| Batch 1 implementation authority | GRANTED / COMPLETE |
| Batch 2 authority | NOT STARTED / NOT GRANTED |
| Migration authority | NOT REQUIRED / NOT GRANTED |
| Date | 2026-08-25 |

Creating or accepting this manifest does not authorize implementation.

## 2. Exact implementation boundary

The implementation boundary is exactly seven new files:

| Path | State | Batch 1 responsibility | IDS traceability / focused evidence |
|---|---|---|---|
| backend/app/schemas/project_context.py | NEW | Frozen closed contracts: trusted actor/scope, ten section values/envelopes, availability/overall/authority/temporal values, provenance, continuation/truncation, 18 typed node selectors/projections, exact relation discriminators, and payload-free protected/invalid/unavailable results. | DTO closure, allow-lists, Human identity exclusion, selector/result/provenance tests. |
| backend/app/ports/project_context.py | NEW | Protocol-only typed owner read contracts and closed owner results for Context assembly prerequisites plus Context/Context Relationship single-read and incident-read seams. No orchestration or I/O. | Port signatures/results, no universal resolver/dictionary contract tests. |
| backend/app/adapters/engineering_context_project_context.py | NEW | Owner-specific adapter over the public EngineeringContextService only; narrow its authorized current list/single Context responses into Batch-048 typed owner results. | Canonical selector/scope preservation, protected/unavailable translation, no repository/Session import. |
| backend/app/adapters/engineering_context_relationship_project_context.py | NEW | Owner-specific adapter over the public EngineeringContextRelationshipService only; narrow exact current Context Relationship incident results for later Batch 3. | Exact four meanings/endpoints, protected owner result, no generic graph traversal/import. |
| backend/tests/test_project_context_contracts.py | NEW | Test closed schema/port contracts only. | Ten sections; 18 nodes; closed relations; selectors; results; Human identity exclusion; no generic/untyped contract. |
| backend/tests/test_engineering_context_project_context_port.py | NEW | Focused owner-boundary tests for the Context adapter. | Typed projection, trusted Project/Workspace propagation, owner protected/unavailable behavior, no direct persistence. |
| backend/tests/test_engineering_context_relationship_project_context_port.py | NEW | Focused owner-boundary tests for the Context Relationship adapter. | Four meanings, eligible endpoint kinds, protected behavior, deterministic bounded owner page contract. |

No existing production/test file is authorized for modification. In particular,
backend/app/services/engineering_context_relationship_service.py is excluded
because it contains unrelated local work. The adapters must call public owner
application-service methods only; they may not reconstruct owner authorization,
instantiate repositories, access ORM models, Session/UoW/tables or inspect
foreign persistence.

The owner-specific adapter files are necessary now because IDS-048 requires
typed Engineering Context current/single-node and Context Relationship incident
read boundaries before later composition/expansion. They are not parallel
canonical capabilities: the existing owner services remain the sole authority.

## 3. Scope and exclusions

Batch 1 may define and adapt only prerequisites. It may not implement Project
Context assembly, source orchestration, state calculation, observation handling,
response-byte enforcement, continuation issuance/verification, transport/routes,
router composition, EKG dispatch/expansion, relation traversal orchestration,
target reauthorization, frontend/UI, persistence, migration, UoW, idempotency,
outbox, generic resolver/graph infrastructure, AI or PATCH-049 behavior.

The ten section discriminators are exactly project_basis, execution,
deliverables, project_controls, engineering_context, engineering_objects,
evidence, supporting_files, technical_reports and organizational_memory. Capture,
Journal and Interface Commitment are absent.

The node allow-list is exactly project, workspace, execution_plan, activity,
milestone, deliverable, deliverable_revision, risk, issue, human_decision,
change, change_impact, engineering_object, engineering_context, evidence,
supporting_file, technical_report and organizational_memory. Foundation is not a
node and has no synthetic identity. Relationship vocabulary is exactly IDS-048;
there is no wildcard relation or universal node/edge loader.

## 4. Prerequisites and focused validation

All prerequisite governance artifacts are accepted and IRR-048 is PASS.
Alembic remains e04700000001; Batch 1 authorizes no migration.

After separate implementation authority, run only:

- the three new focused Batch 1 tests;
- the smallest adjacent owner regressions, without modifying them:
  backend/tests/test_engineering_context_core.py and
  backend/tests/test_engineering_context_relationship_core.py;
- static/import and prohibited-pattern checks confirming no SQLAlchemy,
  repository, Session, UoW, router, FastAPI, persistence, mutation, generic
  resolver, graph traversal or AI imports/behavior; and
- git diff --check.

The implementation must prove closed DTO/result semantics, exact allow-lists,
canonical selector preservation, typed owner-port behavior, payload-free
protected results, default Human identity exclusion and no persistence/mutation.
It must not run broad backend/frontend suites in Batch 1.

## 5. Stop conditions

Stop and report BLOCKED if any file outside this seven-file boundary is required;
if a typed owner port requires modifying the mixed unrelated relationship service
rather than using the permitted owner adapter; if the public owner service cannot
safely provide its typed projection without repository/ORM/Session/UoW access;
if an accepted IDS contract must change; if persistence/migration, generic graph
or PATCH-049 behavior becomes necessary; or if focused validation cannot be
corrected within this boundary.

## 6. Review and authority decision

Independent manifest review found the seven-file boundary necessary and
sufficient. It preserves canonical owner boundaries, isolates unrelated work,
and defers all Batch 2–4 work.

Batch 1 Manifest: ACCEPTED / COMPLETE.
Batch 1: ACCEPTED / COMPLETE after separate Human implementation authority,
focused validation, independent review and Human acceptance. Batch 2 remains
NOT STARTED / NOT GRANTED.
