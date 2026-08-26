# PATCH-048 Batch 2 — Authorized File Manifest

## Control

| Field | Value |
|---|---|
| Batch | 2 — Governed Project Context Composition and Thin Transport |
| Prerequisite | Batch 1 ACCEPTED / COMPLETE |
| Alembic | Must remain sole head `e04700000001` |
| Implementation authority | NOT GRANTED by this manifest |
| Batch 3 | NOT STARTED / NOT GRANTED |

This manifest authorizes no implementation by itself.

## Exact implementation boundary

| Path | State | Batch 2 purpose | Required evidence |
|---|---|---|---|
| `backend/app/schemas/project_context.py` | MODIFY | Add only the accepted assembled-result, section-item and transport request/response discriminated DTOs missing from Batch 1. Retain all closed Batch 1 values. | Result closure; no-payload protected/invalid/unavailable variants. |
| `backend/app/ports/project_context.py` | MODIFY | Add explicit, individually named typed owner read protocols for Project Basis, Execution, Deliverable, Project Control, Engineering Object, Evidence, Supporting File, Technical Report and Organizational Memory. Retain the two Batch 1 Context ports. | No generic resolver/dictionary loader; exact <=100 page contracts. |
| `backend/app/adapters/project_context.py` | NEW | Nine individually named narrow adapters over public owner application services for every remaining composition owner path; fixed section-specific projections and state translation only. | No foreign repository/ORM/Session/UoW access; owner-scope and no-raw-identity/storage projection tests. |
| `backend/app/services/project_context_service.py` | NEW | Request-time `assemble_project_context` orchestration only: Project/Workspace gate; fixed ten-section order; 13-call cap; state/partiality/observation/truncation/byte-limit calculation; authenticated continuation issuance/verification. | Ten sections/states; all-unavailable; observations; bounds; response bytes; no EKG traversal. |
| `backend/app/dependencies/project_context.py` | NEW | Request-scoped composition root: wire canonical public application services, named source adapters, composer and server-trusted actor/Organization outside transport. | One composition path; no client-derived authority; router has no persistence/UoW/policy construction. |
| `backend/app/api/v1/routers/project_context.py` | NEW | One thin authenticated Project Context read route; parse accepted request, obtain composed application, invoke `assemble_project_context`, serialize closed results. | Pre-read invalid/protected outcomes; no source composition or authorization policy in router. |
| `backend/app/main.py` | MODIFY | Register the Project Context router exactly once. | Route presence only; no other route/surface change. |
| `backend/tests/test_project_context_service.py` | NEW | Service-level composition evidence for all ten source paths, ordering, 13 calls, state translation, partiality, observations, bytes and no totals. | Satisfies core composition/bounds evidence. |
| `backend/tests/test_project_context_security.py` | NEW | Authorization-before-disclosure, tenant/project/workspace protection, Human/raw-storage exclusion, token tamper/context/expiry and all-unavailable evidence. | Protected disclosure and cursor security evidence. |
| `backend/tests/test_project_context_api.py` | NEW | Thin authenticated route, trusted actor/Organization, closed transport result, selection/page validation and registration evidence. | API/composition evidence; no EKG route. |

No other production or test file is authorized. In particular, the accepted
Batch 1 Context adapter files are reused unchanged; no existing canonical owner
service, repository, model, migration, UoW, EKG service/router, frontend or
Batch 3 surface is authorized. `backend/app/services/engineering_context_relationship_service.py`
remains excluded because it has unrelated local work.

## Reconciled named owner-path mapping

The one authorized adapter module contains these separately typed, explicitly
named owner adapters; it is a file consolidation only, never a shared source
authority or generic dispatch mechanism.

| Context section | Authorized adapter / canonical public owner boundary |
|---|---|
| Project Basis | `project_context.py` / `ProjectFoundationService.get(project_id, actor)` |
| Execution | `project_context.py` / `EngineeringExecutionPlanService.get(project_id, actor)` |
| Deliverables | `project_context.py` / `EngineeringDeliverableService.list(project_id, actor)` |
| Project Controls | `project_context.py` / `ProjectControlService.list(kind, project_id, actor)` for fixed risk, issue, human_decision and change calls |
| Engineering Objects | `project_context.py` / `EngineeringObjectService.list(project_id, filters, page, size, actor, context)` |
| Evidence | `project_context.py` / `EvidenceService.list(project_id, filters, page, size, actor)` |
| Supporting Files | `project_context.py` / `SupportingFileService.list_metadata(actor_id, scope, lifecycle, limit, continuation)` |
| Accepted Technical Reports | `project_context.py` / `TechnicalReportService.list_reports(actor, criteria)` |
| Active Organizational Memory | `project_context.py` / `OrganizationalMemoryService.list_active(actor, request)` |

Engineering Context remains `backend/app/adapters/engineering_context_project_context.py`
over `EngineeringContextService.list_for_scope(...)`, created and accepted in
Batch 1. The Batch 1 Engineering Context Relationship adapter is not a Context
composition source and remains deferred to Batch 3 relationship/EKG work.

### Dependency-root construction boundary

`backend/app/dependencies/project_context.py` may instantiate the existing
canonical Engineering Object, Evidence and Technical Report application
services with their established SQLAlchemy UoW/policy/validator/clock
collaborators. This is infrastructure wiring inside the authorized request-
scoped composition root, following the accepted Engineering Knowledge Graph
and Organizational Memory dependency precedents. It is not foreign persistence
access by Project Context application logic.

The constructed canonical services retain all owner authorization and data
access. Only those public service methods may be passed to the separately named
Project Context adapters. Repositories, ORM models, Sessions, UoWs, policies
and validators may not escape the dependency root or be imported by the
adapters, composer or router. The dependency root may not reproduce owner
authorization/business logic, introduce a service locator, or create a second
canonical implementation.

## Fixed Batch 2 behavior and boundaries

The implementation must compose exactly these ten sections in canonical order:
`project_basis`, `execution`, `deliverables`, `project_controls`,
`engineering_context`, `engineering_objects`, `evidence`, `supporting_files`,
`technical_reports`, and `organizational_memory`. Capture, Journal and
Interface Commitments are excluded.

Before any source disclosure it must authenticate, derive trusted Organization,
authorize Project and optional Workspace, validate request/token, then invoke
the fixed typed owner port. Available, empty, not-established,
not-disclosed and unavailable translate exactly as IDS-048; nonavailable
sections expose no count, item, timestamp, token, truncation or reason.
Complete-within-bounds requires every selected section safe and untruncated;
partial requires at least one safe observation plus unavailable, not-disclosed
or truncated state; all unsafe sources return payload-free unavailable.

Calls are fixed at <=13: the one Project/Workspace authorization gate is the
Project Basis owner-read slot, plus the remaining eight non-control owner-read
slots and four ordered Project Control reads (risk, issue, human_decision,
change). Thus the nine non-control slots include the Project Basis gate; it is
never an additional fourteenth call.
Requested sections are 1..10; source pages are <=100; serialized UTF-8 response
is <=512 KiB; continuation is <=4096 characters, AES-GCM authenticated,
canonical base64url, purpose-bound `project-context-continuation:v1`, and
expires after 15 minutes. It binds actor, Organization, Project, Workspace,
exact selection/page/order, operation and last evaluated key, and is rejected
payload-free before an owner read if malformed, noncanonical, tampered, expired
or context-mismatched.

## Focused validation and adjacent regression

The three authorized tests must prove all 25 enumerated Batch 2 manifest
properties: all ten typed sections; ordering/selection; call/page/byte/token
bounds; all five source states; complete/partial/all-unavailable;
non-atomic observations; authorization before source/count/token/provenance
disclosure; no totals/Human/raw-storage leakage; tenant/project protection; thin
transport; and no EKG traversal. The smallest adjacent regression is
`backend/tests/test_organizational_memory_pagination.py`, which protects the
accepted AES-GCM cursor precedent; it is regression-only and is not modified.

## Stop conditions and exclusions

Stop if a source requires foreign persistence access, an accepted
Architecture/EDS/IDS change, a non-isolable collision in a listed modified file,
a migration/persistence/UoW/idempotency/outbox/cache, any generic source loader,
or any EKG expansion/frontend/AI/PATCH-049 behavior. No direct source ORM,
repository, Session, UoW or table use is permitted in composer, adapters or
router. Router owns neither policy nor composition.

## Manifest decision

Initial independent manifest review PASS was followed by preflight discoveries
`B2-MAJ-02` and `B2-MAJ-03`, corrected by reconciled owner mapping and the
explicit existing composition-root precedent above. Focused independent re-review:
**PASS** (Critical 0, Major 0, Minor 0). This manifest is **ACCEPTED / COMPLETE
— RECONCILED**. Batch 2 is **ELIGIBLE FOR IMPLEMENTATION** only under separate
Human implementation authority.

## Prerequisite reconciliation — Human accepted

Human acceptance records the minimal owner-boundary prerequisite without
changing EDS, Technical Report ownership, authorization, or persistence.
The Batch 2 production/test boundary expands from ten to fourteen files only:
`backend/app/ports/technical_report.py`,
`backend/app/services/technical_report_service.py`,
`backend/tests/test_technical_report_service.py`, and
`backend/tests/test_technical_report_security.py` are authorized to provide
the typed, bounded, accepted-only Technical Report safe summary consumed by
the existing Project Context adapter. It exposes only report identity, scope,
version, accepted digest/timestamp and purpose; it exposes no content, Human,
provenance, storage or total. Supporting File test composition may use the
existing in-memory private-store test precedent only; production composition
remains the existing private-store configuration. No migration is authorized.
