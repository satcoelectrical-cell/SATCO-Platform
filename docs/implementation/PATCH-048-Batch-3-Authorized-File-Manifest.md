# PATCH-048 Batch 3 Authorized File Manifest — Bounded One-Hop EKG Expansion

## Authority and fixed scope

This manifest is prepared after Batch 1 and Batch 2 acceptance. It authorizes
only a later separately-approved implementation of the accepted read-only
`get_context_node` and `expand_one_hop` operations. It creates no aggregate,
source fact, persistence state, transaction, cache, mutation, migration, Audit,
outbox, idempotency, AI reasoning, frontend, or PATCH-049 capability.

The traversal is exactly one hop. It starts from one allowed node, reads only
the applicable fixed owner incident readers, independently authorizes each
relation and target before projection, and never reads a target's relations.

## Exact implementation allow-list

| Path | State | Batch 3 responsibility | Explicitly prohibited |
|---|---|---|---|
| `backend/app/schemas/project_context.py` | MODIFY | Add frozen, extra-forbidden get-node/one-hop request, typed node/edge projection, discriminated result, bounded page/continuation and truncation DTOs for the accepted 18 nodes and closed relationship vocabulary. | Generic node/edge payloads, depth, filters, totals, content, Human identity, raw file storage, AI fields. |
| `backend/app/ports/project_context.py` | MODIFY | Add only named owner-specific graph-read protocols and fixed graph-owner seam; each accepts trusted actor/scope and typed selector/request. | Universal resolver, raw SQL/filter/Session/UoW/repository inputs, mutation ports. |
| `backend/app/adapters/project_context.py` | MODIFY | Extend the existing named canonical adapters with narrow single-node and incident-relation translations for Project/Workspace, Execution, Deliverable, Control, Engineering Object/Relationship, Evidence/File, Technical Report and Memory. | Foreign persistence, inferred relationships, service-local authorization duplication, untyped source forwarding. |
| `backend/app/services/project_context_service.py` | MODIFY | Implement fixed 18-node dispatch and bounded one-hop orchestration: start authorization, fixed applicable-reader order, candidate normalization/dedupe/order, relation/target reauthorization, last-evaluated continuation and byte bound. | Second hop, recursion, target enrichment, mutation/cache/persistence/UoW/Audit/outbox/idempotency. |
| `backend/app/dependencies/project_context.py` | MODIFY | Wire existing request-scoped canonical public services/adapters into the graph-owner seam outside transport. | Router ownership, direct source repository/ORM access from graph application logic, new authority. |
| `backend/app/api/v1/routers/project_context.py` | MODIFY | Add only authenticated thin get-node and related-one-hop route extensions under the existing Project Context route family, with closed result translation. | Policy, Session/UoW/repository construction, arbitrary relation/depth routes. |
| `backend/tests/test_project_context_contracts.py` | MODIFY | Assert closed 18-node/relationship/request/result DTO and port allow-lists, payload-free variants and forbidden fields. | Broad owner tests or implementation. |
| `backend/tests/test_project_context_graph.py` | CREATE | Focused node-dispatch, edge matrix, one-hop/candidate/call-bound/order/continuation/truncation/byte-limit evidence. | Multi-hop, graph persistence or synthetic owner authority. |
| `backend/tests/test_project_context_security.py` | MODIFY | Prove start/relation/target authorization-before-disclosure, Organization/Project/Workspace denial, stale/deleted/foreign suppression and no Human/storage/count leakage. | Mutation/security redesign. |
| `backend/tests/test_project_context_api.py` | MODIFY | Prove two thin graph transport extensions, authentication/trusted context, closed protected/invalid/unavailable serialization and prohibited routes. | Frontend/API redesign. |
| `backend/tests/test_project_context_service.py` | MODIFY | Retain Batch 2 behavior and add composer-regression evidence for graph continuation purpose isolation and no impact on ten-section assembly. | Batch 4 frontend behavior. |

No other production or test file is authorized. The accepted Batch 1
Engineering Context and Context Relationship adapters/ports are reused
unchanged. `backend/app/services/engineering_context_relationship_service.py`
is excluded: it has unrelated dirty work and is already consumed only through
the accepted Batch 1 public adapter.

## Fixed canonical-owner matrix

The sole node allow-list is: Project, Workspace, Execution Plan, Activity,
Milestone, Deliverable, Deliverable Revision, Risk, Issue, Human Decision,
Change, Change Impact, Engineering Object, Engineering Context, Evidence,
Supporting File, exact accepted Technical Report, and active Organizational
Memory. Foundation, Capture, Journal, Interface Commitment, discipline,
external source and every other selector are invalid.

Each node is obtained only from the owning public application-service boundary:
Project/Workspace; Execution; Deliverable; Project Control; Engineering Object;
Engineering Context; Evidence/File; Technical Report; Organizational Memory.
Engineering Relationship and Context Relationship are edges only. A foreign
Organization/Project or incompatible Workspace owner response becomes a
payload-free protected outcome before projection.

The closed vocabulary is: current accepted Engineering Relationship
family/type pairs; `context_requires`, `context_provided_by`,
`context_consumed_by`, `context_potentially_affects`; `plan_activity`,
`plan_milestone`, `activity_dependency`, `milestone_activity`,
`deliverable_activity`, `deliverable_milestone`, `deliverable_revision`,
`revision_representation`, `decision_successor`, `change_successor`,
`change_impact`, `impact_target`, `evidence_supporting_file`,
`report_evidence_provenance`, `report_object_provenance`, and
`memory_source_report`. No membership/common-scope/time/text/provenance-derived
or inferred relation is permitted. Impact targets are only Activity, Milestone,
Deliverable, Deliverable Revision, Evidence or Supporting File.

## Authorization, traversal and bound contract

1. Authenticate and derive trusted actor/Organization, then validate the
   closed selector/request/continuation before an owner read.
2. Authorize and resolve the start node before its existence, kind, edge or
   count is disclosed.
3. Invoke only applicable readers in this fixed order: Engineering Relationship,
   Context Relationship, Execution, Deliverable, Project Control, Evidence/File,
   Technical Report, Organizational Memory.
4. Normalize/dedupe by source kind/selector, relation kind/selector and target
   kind/selector; use deterministic canonical ordering; authorize the relation
   and independently authorize the target before projecting the pair.
5. Stop after one hop. Do not query target relations or enrich targets.

The fixed budget is one start read + at most eight incident readers + at most
91 target reads = at most 100 owner calls. Candidate edges, visible edges,
visible targets and page size are each <=91. Reader pages are <=91. Response
serialization is <=512 KiB; records are never cut. The continuation is the
canonical unpadded base64url AES-GCM form, <=4096 characters, versioned,
purpose-bound separately from assembly, actor/Organization/Project/Workspace/
relation-direction-page-order-bound, 15-minute expiring and anchored to the
last evaluated canonical key. Denied candidates advance the evaluated anchor;
there are no totals, fallbacks or skip/duplicate behavior.

Protected start/relation/target outcomes expose no identity, existence, kind,
standing, count, ordinal, lineage, provenance, reason, exception or token
plaintext. Invalid and unavailable variants are likewise payload-free. Typed
provenance contains only owner-exposed safe selector/version/standing/timestamp
metadata, authority and temporal classification; it contains no Human identity,
report body, file object key/path/private URL/bytes, or raw persistence fields.

## Focused evidence and stop conditions

Focused evidence must cover all 18 node dispatches; Foundation/unsupported
rejection; every closed edge family; start/edge/target reauthorization;
tenant/project/workspace/stale/deleted suppression; relation/target no-count
non-disclosure; no second hop/inferred edge; 91/100/512KiB bounds; canonical
dedupe/order; continuation tamper/context/expiry/last-evaluated/truncation; and
the existing Batch 2 assembly regression. Adjacent regression is limited to
Engineering Object, Engineering Relationship and Context Relationship focused
tests named in the implementation review, plus the existing Project Context
focused tests when touched.

Stop before implementation if any path needs foreign persistence access, an
owner API not already available through the accepted canonical application
boundary, Architecture/EDS/IDS change, a migration, an additional file, generic
graph/security infrastructure, hidden authority, second-hop behavior, frontend,
AI, or PATCH-049 work.

## Manifest decision

Independent manifest review: **PASS**. Critical: 0. Major: 0. Minor: 0.
This manifest is **ACCEPTED / COMPLETE** and grants no implementation authority.

## Append-only B3-CRIT-01 prerequisite reconciliation

The original eleven-file manifest remains historically preserved. During
implementation preflight, `B3-CRIT-01` proved that exact owner-safe reads were
missing for Activity, Milestone, Change Impact, Project and Workspace. The
following eighteen files are added solely to establish those canonical reads:

| Path | State | Exact prerequisite responsibility |
|---|---|---|
| `backend/app/schemas/engineering_execution_plan.py` | MODIFY | Closed Activity and Milestone graph-summary result DTOs using the already accepted node fields. |
| `backend/app/services/engineering_execution_plan_service.py` | MODIFY | Exact authorized UUID reads for Activity and Milestone under trusted Organization/Project scope. |
| `backend/app/ports/engineering_execution_plan.py` | MODIFY | Add the exact owner-internal Milestone repository selector signature; Activity exact lookup already exists. |
| `backend/app/repositories/engineering_execution_plan_repository.py` | MODIFY | Implement exact Milestone UUID + Plan + Organization lookup without scanning plan children. |
| `backend/tests/test_execution_plan_repository.py` | MODIFY | Prove exact Milestone selector scope and no broad-list fallback. |
| `backend/tests/test_execution_plan_service.py` | MODIFY | Exact selector/projection/current-standing and no-list-scan evidence. |
| `backend/tests/test_execution_plan_security.py` | MODIFY | Protected foreign Organization/Project/Workspace and no-Human disclosure evidence. |
| `backend/app/schemas/project_control.py` | MODIFY | Closed Change Impact graph-summary result DTO. |
| `backend/app/services/project_control_service.py` | MODIFY | Exact authorized Change Impact UUID read through the canonical Project Control UoW. |
| `backend/tests/test_project_control_service.py` | MODIFY | Exact Impact selector/projection/standing/target-kind evidence. |
| `backend/tests/test_project_control_security.py` | MODIFY | Protected owner/scope/target disclosure evidence. |
| `backend/app/schemas/project.py` | MODIFY | Closed Project graph-safe summary: ID, code, name and lifecycle status only. |
| `backend/app/services/project_service.py` | MODIFY | Exact actor-authorized Project summary read under trusted Organization. |
| `backend/tests/test_project_core.py` | MODIFY | Exact Project summary, active-actor authorization and forbidden Human/detail fields. |
| `backend/app/schemas/engineering_workspace.py` | MODIFY | Closed Workspace graph-safe summary: ID, Project, discipline and status only. |
| `backend/app/services/engineering_workspace_service.py` | MODIFY | Exact existing-visibility-authorized Workspace summary without broad response fields. |
| `backend/tests/test_engineering_workspace_core.py` | MODIFY | Exact selector/projection and canonical Project association evidence. |
| `backend/tests/test_engineering_workspace_permissions.py` | MODIFY | Protected Organization/Project/Workspace and Human-field exclusion evidence. |

The reconciled implementation/test allow-list is exactly **29 files**: the
original eleven plus these eighteen. No other file is authorized. The safe
reads are implementation-only extensions of existing owner authority; they do
not reopen Architecture/EDS, transfer authority, create graph-owned facts, or
change persistence. The focused IDS/Plan clarification names the methods for
determinism without changing accepted semantics.

Focused independent manifest re-review: **PASS**. Critical: 0. Major: 0.
`B3-CRIT-01` is **RESOLVED** at the prerequisite/manifest level. Batch 3 may
resume implementation only under the standing authority already granted; no
implementation is performed by this reconciliation.

## Append-only B3-CRIT-02 Deliverable Revision owner-read reconciliation

Implementation preflight discovered that the accepted Deliverable Revision
node requires an exact canonical revision-UUID read, while the Deliverable
owner previously exposed only current-deliverable and bounded history reads.
Project Context may not scan history or access Deliverable persistence.

The following five owner-side files are therefore added to the accepted Batch
3 boundary:

| Path | State | Exact prerequisite responsibility |
|---|---|---|
| `backend/app/schemas/engineering_deliverable.py` | MODIFY | Closed Deliverable Revision graph-safe summary with no Supporting File or Human identity. |
| `backend/app/repositories/engineering_deliverable_repository.py` | MODIFY | Exact revision UUID + Organization selector; no generic query or history scan. |
| `backend/app/services/engineering_deliverable_service.py` | MODIFY | Canonical owner-authorized exact revision read with Project/Workspace and existing file-visibility protection. |
| `backend/tests/test_engineering_deliverable_contracts.py` | MODIFY | Exact safe-field and forbidden-field contract evidence. |
| `backend/tests/test_engineering_deliverable_service.py` | MODIFY | Current/historical exact-read, protected scope, owner linkage, no-scan and no-mutation evidence. |

The reconciled implementation/test allow-list is exactly **34 files**: the
previously reconciled twenty-nine plus these five. This extension changes no
Architecture/EDS authority, persistence identity, migration, mutation or
Deliverable ownership. `B3-CRIT-02` is **RESOLVED** at the prerequisite and
manifest level.

## Append-only B3-MAJ-01 explicit relation-owner reconciliation

Focused implementation review found that Evidence/File and reverse Technical
Report provenance incidence were not available as bounded public owner reads.
Returning empty readers would silently weaken the accepted relationship
vocabulary; foreign persistence access is prohibited. The following ten files
are added for narrow read-only canonical relation contracts and evidence:

| Path | State | Responsibility |
|---|---|---|
| `backend/app/schemas/evidence.py` | MODIFY | Closed Evidence/Supporting File graph-link DTO/page. |
| `backend/app/repositories/evidence_repository.py` | MODIFY | Exact bounded link-table selectors owned by Evidence. |
| `backend/app/services/evidence_service.py` | MODIFY | Authorized forward/reverse incident reads. |
| `backend/tests/test_evidence_service.py` | MODIFY | Authorization, bound and no-mutation evidence. |
| `backend/tests/test_evidence_repository.py` | MODIFY | Exact deterministic selector evidence. |
| `backend/app/ports/technical_report.py` | MODIFY | Closed report-provenance graph-link contract and repository port. |
| `backend/app/repositories/technical_report_repository.py` | MODIFY | Exact accepted-report provenance incidence selector. |
| `backend/app/services/technical_report_service.py` | MODIFY | Bounded authorized provenance incidence read. |
| `backend/tests/test_technical_report_service.py` | MODIFY | Owner authorization/bound/read-only evidence. |
| `backend/tests/test_technical_report_security.py` | MODIFY | Human/content/protected-field exclusion evidence. |

Deliverable Revision representation incidence and Project Control graph-safe
summaries remain inside their already authorized owner files. The exact final
Batch 3 implementation/test allow-list is **44 files**. No migration, mutation,
new identity, authority change, generic graph platform or PATCH-049 scope is
introduced. `B3-MAJ-01` is **RESOLVED**.

## Append-only B3-MAJ-03 incident-read closure

Final conformance review found that Execution, Deliverable, Project Control and
reverse Organizational Memory adapters still derived some incident edges from
whole-owner list results. That was read-only, but it was not the exact
owner-specific incident boundary required by EDS/IDS-048 and could omit a valid
reverse edge outside the first generic list page.

The following five additional owner-side files are authorized:

| Path | State | Exact responsibility |
|---|---|---|
| `backend/app/schemas/organizational_memory.py` | MODIFY | Closed active Memory/source-report graph-link page with no retained content, Human identity or provenance payload. |
| `backend/app/repositories/organizational_memory_repository.py` | MODIFY | Exact bounded active source-report incidence selector. |
| `backend/app/services/organizational_memory_service.py` | MODIFY | Current-authorized source-report graph read with source reauthorization before each Memory link. |
| `backend/tests/test_organizational_memory_service.py` | MODIFY | Exact incidence, current reauthorization and protected-denial evidence. |
| `backend/app/repositories/project_control_repository.py` | MODIFY | Exact predecessor, impact and impact-target incidence selectors under Organization/Project scope. |

Execution and Deliverable schema/repository/service/test files, Project Control
schema/service/test files, the Project Context adapter and graph test are already
authorized above. Their use is narrowed to typed exact incident reads. Generic
owner lists are prohibited for EKG relation derivation.

The final reconciled Batch 3 implementation/test allow-list is **49 files**.
No schema migration, mutation contract, persistence ownership, Audit, outbox,
idempotency, AI, multi-hop or PATCH-049 capability is added.
