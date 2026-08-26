# IDS-048 — Governed Project Context Assembly and EKG Read Expansion

## Document control

| Field | Value |
|---|---|
| PATCH / Architecture / EDS | PATCH-048 / Architecture-048 ACCEPTED / EDS-048 ACCEPTED |
| Status | ACCEPTED / COMPLETE after independent review |
| Independent IDS Review | PASS |
| Human IDS Acceptance | PASS |
| Implementation Plan authority | GRANTED only |
| Implementation, migration and IRR | NOT AUTHORIZED |
| Alembic head | e04700000001 |

## Exact V1 boundary and contracts

PATCH-048 is read-only request-time composition: assemble_project_context,
get_context_node and expand_one_hop. It owns neither aggregate nor source fact.
It adds no persistence, migration, cache of canonical truth, transaction/UoW,
idempotency, outbox, Audit domain, graph store, AI authority, synthetic identity
or source mutation.

All new contracts are frozen typed DTOs with extra fields forbidden. No generic
JSON/dictionary DTO, reflection, arbitrary source field or universal resolver
exists. ProjectContextActor is positive actor_id plus server-derived Organization
UUID. ProjectContextScope is positive project_id plus optional positive workspace_id.
ProjectContextRequest is scope plus 1..10 SectionRequests; a request with omitted
sections becomes all ten in canonical order. SectionRequest is closed section
enum, page_size and optional opaque continuation. Duplicate/noncanonical
selection, unsupported filter or malformed continuation is payload-free
invalid_request before an owner read.

The exact section enum is project_basis, execution, deliverables,
project_controls, engineering_context, engineering_objects, evidence,
supporting_files, technical_reports and organizational_memory. ProjectContextResult
is exactly success, protected_not_found, invalid_request or unavailable. The last
three are discriminator-only. SectionEnvelope is exactly available(items,
visible_count, truncated, continuation, observed_at), empty, not_established,
not_disclosed or unavailable. Visible count equals returned item count, never a
total. Only Foundation/Execution may be not_established. Nonavailable states have
no item, count, timestamp, token, truncation or reason.

FactProvenance is typed owner kind, typed selector, owner version/standing/source
timestamp only if exposed, observed_at, authority classification and temporal
classification. Authority is exactly human_authoritative,
external_tool_authored, canonical_evidence, derived or contextual_advisory;
temporal is current or historical. Human identities, raw storage keys/private
URLs, content/body, rationale, exception detail and token plaintext are excluded.

## Ten-section owner-port matrix

The composer depends only on typed owner ports, never foreign repositories, ORM,
Sessions, UoWs or tables.

| Section | Current owner boundary | Typed PATCH-048 port / bound | Translation / prerequisite |
|---|---|---|---|
| project_basis | ProjectFoundationService.get(project_id, actor) | ProjectBasisContextReadPort.get_authorized_basis(actor, scope); one | explicit absence not_established; protected not_disclosed; narrow adapter |
| execution | EngineeringExecutionPlanService.get(project_id, actor) | ExecutionContextReadPort.get_authorized_plan(actor, scope); one plan, <=200 Activities, <=50 Milestones, <=500 dependencies | explicit plan absence not_established |
| deliverables | EngineeringDeliverableService.list(project_id, actor) | DeliverableContextReadPort.list_authorized_deliverables(actor, scope, page); <=100 | zero empty; typed paging/projection adapter |
| project_controls | ProjectControlService.list(kind, project_id, actor) | ProjectControlContextReadPort.list_authorized_controls(actor, scope, kind, page); risk, issue, decision publicly human_decision, change; <=100/kind, <=100 impacts/change | narrowed typed projection |
| engineering_context | EngineeringContextService.list_for_scope(project_id, workspace_id, current_user, page, size) | EngineeringContextContextReadPort.list_authorized_current(actor, scope, page); <=100 | required thin owner-side typed read port; current dict/Session response is not safe cross-domain contract |
| engineering_objects | EngineeringObjectService.list(project_id, filters, page, size, actor, context) | EngineeringObjectContextReadPort.list_authorized_objects(actor, scope, page); <=100 | exact safe PATCH-033 subset |
| evidence | EvidenceService.list(project_id, filters, page, size, actor) | EvidenceContextReadPort.list_authorized_current(actor, scope, page); <=100 | narrowed typed adapter |
| supporting_files | SupportingFileService.list_metadata(actor_id, scope, lifecycle, limit, continuation) | SupportingFileContextReadPort.list_authorized_available(actor, scope, page); <=100 | reuse authenticated owner cursor |
| technical_reports | TechnicalReportService.list_reports(actor, criteria) | TechnicalReportContextReadPort.list_authorized_accepted(actor, scope, page); <=100 | accepted-only criteria/projection |
| organizational_memory | OrganizationalMemoryService.list_active(actor, request) | OrganizationalMemoryContextReadPort.list_authorized_active(actor, scope, page); <=100 | Memory owner reauthorizes current source/provenance |

Every port has typed success/protected/unavailable outcomes and checks trusted
Organization, Project and optional Workspace before facts/count/token. Protected
maps to not_disclosed, never empty. The maximum composition budget is 13 calls:
one Project/Workspace gate, nine non-control section reads and four controls
ordered risk, issue, human_decision, change. A declared transient retry replaces
rather than increases a source slot.

## Context assembly and source states

Algorithm: validate request/token; authenticate/derive Organization; authorize
Project and optional Workspace; record observation_started_at; invoke selected
ports in canonical section order; authorize every owner item before narrow
projection; enforce bounds/last-evaluated continuation; record completion and
calculate observation state.

Nonzero authorized owner page is available; authorized zero is empty; explicit
Foundation/Plan absence is not_established; owner protected is not_disclosed;
source failure is unavailable. Invalid owner request construction is top-level
invalid_request. Complete_within_bounds requires all requested sections
available/empty/not_established and untruncated. Partial requires one safe
observation plus unavailable/not_disclosed/truncated. If no section can be safely
observed because all dependencies fail, return payload-free unavailable.

Context is non-atomic. Each safe result has observed_at and owner-exposed
version/standing/timestamp only when present. No cross-domain lock, transaction,
cache or Context version exists. Existing infrastructure has no cross-owner
timeout system; IDS adds none. ASGI cancellation is inherited and owner faults
translate to unavailable.

Application serialization enforces 524288 UTF-8 bytes. This is enforceable at
the composition/response boundary; no generic platform response limiter exists.
A record is never cut: the affected section is unavailable/partial, or whole
response unavailable when no safe section remains.

## Exact 18-node matrix

Get node returns node(NodeProjection), protected_not_found, invalid_request or
unavailable. Non-node variants are payload-free; fields are only accepted EDS
safe fields plus typed provenance/classification/navigation.

| Kind / selector | Exact owner port | Scope/current rule | Incident families |
|---|---|---|---|
| project / positive int | ProjectWorkspaceGraphReadPort.get_authorized_project via ProjectService.get_by_id | Organization + exact Project | Context Relationship |
| workspace / positive int | ProjectWorkspaceGraphReadPort.get_authorized_workspace via EngineeringWorkspaceService.get | same Project/Organization/authorized Workspace | Context Relationship |
| execution_plan / UUID | ExecutionGraphReadPort.get_authorized_plan | exact Project/current established | execution |
| activity / UUID | ExecutionGraphReadPort.get_authorized_activity | same Project/Workspace when present | execution, impact target |
| milestone / UUID | ExecutionGraphReadPort.get_authorized_milestone | same Project | execution, impact target |
| deliverable / UUID | DeliverableGraphReadPort.get_authorized_deliverable | same Project/Workspace | deliverable |
| deliverable_revision / UUID | DeliverableGraphReadPort.get_authorized_revision | owning deliverable same scope | deliverable, impact target |
| risk / UUID | ProjectControlGraphReadPort.get_authorized_risk | owner current/historical semantics | none |
| issue / UUID | ProjectControlGraphReadPort.get_authorized_issue | owner current/historical semantics | none |
| human_decision / UUID | ProjectControlGraphReadPort.get_authorized_decision | historical only explicit owner mode | decision successor |
| change / UUID | ProjectControlGraphReadPort.get_authorized_change | historical only explicit owner mode | change successor, impact |
| change_impact / UUID | ProjectControlGraphReadPort.get_authorized_impact | owning Change same scope | impact target |
| engineering_object / UUID | CanonicalEngineeringObjectReadAdapter.get_authorized over EngineeringObjectService.get | PATCH-033 Org/Project/Workspace parity | Engineering Relationship, report provenance |
| engineering_context / positive int | EngineeringContextGraphReadPort.get_authorized_context | required typed owner port/current default | Context Relationship |
| evidence / UUID | EvidenceFileGraphReadPort.get_authorized_evidence | same trusted scope | file, report, impact |
| supporting_file / UUID | EvidenceFileGraphReadPort.get_authorized_supporting_file | same trusted scope | file, revision, impact |
| technical_report / UUID | TechnicalReportGraphReadPort.get_authorized_accepted_report | exact accepted version/current authority | report, memory |
| organizational_memory / UUID | OrganizationalMemoryGraphReadPort.get_authorized_active_memory | active after owner reauthorization | memory source |

Foundation is never a node. Engineering Relationship and Context Relationship
are edges. Capture, Journal, Interface Commitment, discipline and external source
are invalid. A foreign Organization/Project or incompatible Workspace owner
response is protected before projection.

## Relationship matrix, one-hop, bounds and continuation

The only relations are current Engineering Relationship enum pairs in accepted
structural, physical, electrical, instrumentation, automation and dependency
families; Context meanings requires/provided_by/consumed_by/potentially_affects;
and plan_activity, plan_milestone, activity_dependency, milestone_activity,
deliverable_activity, deliverable_milestone, deliverable_revision,
revision_representation, decision_successor, change_successor, change_impact,
impact_target, evidence_supporting_file, report_evidence_provenance,
report_object_provenance and memory_source_report.

Their exact owner ports are EngineeringRelationshipGraphReadPort,
EngineeringContextRelationshipGraphReadPort, ExecutionGraphReadPort,
DeliverableGraphReadPort, ProjectControlGraphReadPort, EvidenceFileGraphReadPort,
TechnicalReportGraphReadPort and OrganizationalMemoryGraphReadPort. The Context
Relationship port is a required thin typed owner-side port because the existing
concrete service exposes dict/Session-oriented results. Impact targets are only
Activity, Milestone, Deliverable, Deliverable Revision, Evidence or Supporting
File. Target authorization precedes edge/target disclosure; denied/stale/deleted/
foreign target omits both without count/reason. No wildcard or generic loader.

ExpandOneHopRequest has trusted scope, one typed selector, distinct closed
relation keys, outgoing/incoming/both, page size 1..91 and opaque continuation.
No depth, arbitrary predicate, enrichment or recursion exists. It validates and
scope-authorizes, resolves the start node, selects only applicable readers in
fixed order Engineering Relationship, Context Relationship, Execution,
Deliverable, Project Control, Evidence/File, Technical Report, Memory, normalizes
and dedupes candidates by source kind/selector, relation kind/selector and target
kind/selector, resumes after last evaluated key, reauthorizes relation and target,
projects authorized pair, and stops without reading target relations.

There are at most eight incident-reader calls. Fixed budget: one start read,
eight readers and 91 target reads equals 100 owner calls. Candidates examined,
visible edges, visible targets and page size are each <=91; reader pages are
capped at 91. Section pages remain <=100 subject to lower owner caps. No hidden
total/fallback exists.

Reuse Organizational Memory/Supporting File cursor precedent: AES-GCM, canonical
unpadded base64url with strict decode/re-encode equality, versioned payload,
15-minute expiry, maximum 4096 characters and distinct SECRET_KEY purpose suffix
project-context-continuation:v1. It binds version, operation, actor,
Organization, Project, Workspace, exact filter/direction/page/order, issued/
expiry and last evaluated key. Tampered/noncanonical/expired/mismatched token is
payload-free invalid_request before owner access; it never grants access or logs.

## Authorization, cross-scope, provenance and logging

Call order: authenticate; trusted actor/Organization; Project/Workspace
authorization; owner read; item/edge/target authorization; narrow projection;
continuation. Router parses transport only and owns no policy, repo, Session or
UoW. Foreign Organization/Project, incompatible Workspace, malformed selector,
stale/deleted target, unauthorized historical target and inconsistent owner
response fail closed. Cross-Organization/Project edges and two-distinct-Workspace
edges are omitted; a Project endpoint may attach to one Workspace only where its
canonical relation expressly permits it.

Protected scope/start is payload-free protected_not_found. Malformed/unsupported/
token is payload-free invalid_request. Dependency failure before safe observation
is payload-free unavailable. A denied section is not_disclosed. Nothing protected
leaks existence, identity, standing, timestamp, count, truncation, relation kind,
ordinal, reason or exception. Provenance is only owner-exposed data; none is
invented. Existing safe operational logging may include correlation/actor/
Organization/operation/scope/public category/result class/timing, never payload,
Human identity, content, storage data, hidden data, token/credential/exception.

## Transport, frontend, file map, migration and tests

Later thin authenticated routes are:
GET /api/v1/projects/{project_id}/engineering-context
GET /api/v1/projects/{project_id}/engineering-context/nodes/{node_kind}/{selector}
GET /api/v1/projects/{project_id}/engineering-context/nodes/{node_kind}/{selector}/related

Workspace/section/relation/direction/page/token are closed validated inputs; actor
and Organization are server-derived. Closed application result discriminators
serialize one-to-one. Request-scoped composition is a dependency module, not a
router. Likely later surfaces are project-context schemas/ports/services/adapters,
owner Context/Context Relationship port adapters, dependency/router/main,
focused tests and frontend API/types/Project components/styles. None is
authorized by this IDS.

Frontend uses typed real API data only: accessible cards and truthful loading,
empty, not_established, not_disclosed, unavailable, partial/truncated states,
keyboard pagination and responsive stacking. No manual raw IDs, fake data/totals,
graph editor, AI or recommendation is allowed.

No migration: PATCH-048 owns no persistent state and must not create e048. Alembic
stays sole head e04700000001. Any schema need is a hard stop.

Later focused tests cover all sections/states/partial/unavailable, auth before
reads, tenant/project/workspace isolation, no totals, both typed owner-port
additions, 18 nodes/Foundation exclusion, closed relations/no second hop,
target/stale/cross-scope denial, exact bounds/last-evaluated continuation,
provenance/Human exclusion, no persistence/mutation, thin API and accessible
responsive real-data UI. Likely sequence only: contracts/owner ports; Context
composition/transport; EKG expansion; frontend/final validation. This is not an
Implementation Plan.

Stop if a typed owner port cannot be provided without foreign persistence, a
relation cannot be owner-read, owner limits cannot be honored, persistence/ADR/
new security subsystem is needed, or an authorized boundary cannot isolate
unrelated work.

## Focused implementation clarification — exact owner-safe graph reads

Implementation preflight found that four accepted node families lacked an
exact public owner read even though their canonical identity, authorization,
lifecycle and projection semantics were already fixed. The following methods
are the only prerequisite additions; they do not change ownership or authority:

- `EngineeringExecutionPlanService.get_activity_graph_summary(actor,
  project_id, activity_id)` returns the exact accepted Activity node fields;
- `EngineeringExecutionPlanService.get_milestone_graph_summary(actor,
  project_id, milestone_id)` returns the exact accepted Milestone node fields;
- `ProjectControlService.get_change_impact_graph_summary(actor, project_id,
  impact_id)` returns the exact accepted Change Impact node fields;
- `ProjectService.get_authorized_graph_summary(actor, project_id)` returns
  project ID/code/name/lifecycle status only;
- `EngineeringWorkspaceService.get_authorized_graph_summary(workspace_id,
  current_user)` returns workspace ID, Project ID, discipline and status only.

Each method performs its canonical owner authorization before existence or
field disclosure and returns a frozen, extra-forbidden safe DTO or the owner's
payload-free protected/unavailable result. Execution reads use exact UUID
repository selectors inside the canonical Execution UoW; Change Impact uses an
exact UUID selector inside the canonical Project Control UoW. Project and
Workspace reads retain their existing active actor, Organization, Project and
Workspace visibility rules. No list scan, Human identity, hidden total,
mutation, new persistence, generic graph authority or foreign access is added.


## Focused amendment: exact DTO and relationship closure

The initial IDS review identified that a reference to EDS safe fields was not
enough to make implementation mechanical. This amendment closes that issue
without changing any accepted Architecture or EDS behavior.

### Exact owner-port result signatures

Every owner port named in the prior sections returns only one of:
OwnerResolved[T], OwnerPage[T], OwnerProtected, OwnerInvalid, OwnerUnavailable.
OwnerProtected, OwnerInvalid and OwnerUnavailable have no payload. OwnerPage has
items, has_more, last_evaluated_key and observed_at only; it has no total.
Page selectors are exact ProjectContextActor plus ProjectContextScope plus the
closed page request. Single-node ports use actor, scope and the discriminated
selector for their listed node kind. Incident ports use actor, scope, start
selector, closed direction and a closed page request. No port accepts ORM
filters, field names, raw SQL, Session or a universal identity.

### Exact section item DTOs

ProjectBasisItem has project_id, project_code, project_name, project_status,
foundation_established, foundation_version optional, purpose optional,
engineering_basis optional, current_stage optional, readiness optional,
ordered_in_scope tuple, ordered_out_scope tuple, completion_basis optional and
required_project_inputs tuple.

ExecutionPlanItem has plan_id, project_id, plan_version, standing,
activities tuple of ExecutionActivityItem, milestones tuple of
ExecutionMilestoneItem, dependencies tuple of ActivityDependencyItem and
progress. ExecutionActivityItem has activity_id, plan_id, project_id,
workspace_id optional, title, ordinal, standing, version, target_date optional,
blocker_present. ExecutionMilestoneItem has milestone_id, plan_id, project_id,
title, ordinal, standing, target_date optional. ActivityDependencyItem has
predecessor_activity_id and dependent_activity_id. Progress has numerator,
denominator and percent.

DeliverableItem has deliverable_id, project_id, workspace_id optional, code,
title, discipline, deliverable_type, purpose optional, standing, version,
activity_ids tuple, milestone_ids tuple, target_date optional,
external_authority, current_revision optional. DeliverableRevisionItem has
revision_id, deliverable_id, sequence, external_label optional, standing,
version, representation_available.

ProjectControlItem is discriminated risk, issue, human_decision or change and
has control_id, project_id, workspace_id optional, standing, version,
temporal_class, predecessor_present. Risk adds category, likelihood, impact;
Issue adds severity; Decision and Change add no statement/rationale/identity
fields. ChangeImpactItem has impact_id, change_id, target_kind optional only
after target authorization, standing and impact_class potential or confirmed.
It has no target ID until it is independently projected as an authorized node.

EngineeringContextItem has context_id, context_key, project_id, workspace_id
optional, kind, authority, lifecycle, version, purpose optional, created_at
optional, updated_at optional, typed_payload, subject_references and
source_references. Typed payload is exactly one SubjectReferencePayload,
QualifiedFactPayload, QualifiedEngineeringValuePayload, AssumptionPayload or
SourceEvidenceReferencePayload; all are closed typed fields exposed by the
owner and no raw owner map. EngineeringObjectItem has object_id, organization_id,
project_id, workspace_id optional, family, discipline, object_type, object_subtype,
lifecycle, authority_standing, version, created_at, updated_at. EvidenceItem has
evidence_id, project_id, workspace_id optional, evidence_kind, standing, version,
safe_source_reference optional, created_at, updated_at. SupportingFileItem has
asset_id, project_id, workspace_id optional, filename, media_type, byte_size,
lifecycle, version, created_at, updated_at. TechnicalReportItem has report_id,
project_id, workspace_id, report_type, title_or_purpose optional,
accepted_version_id, accepted_digest, standing, accepted_at. OrganizationalMemoryItem
has memory_id, project_id, workspace_id, source_report_id optional,
source_report_version optional, standing, version, limitations_present, admitted_at.

### Exact node DTOs

NodeProjection is a discriminated union with common node_kind, selector,
navigation(Project/Workspace typed IDs), FactProvenance, authority_class and
temporal_class. It is precisely one of:

| Node kind | Exact additional typed fields |
|---|---|
| project | project_code, project_name, lifecycle_status |
| workspace | project_id, discipline, workspace_status |
| execution_plan | project_id, plan_version, established_standing |
| activity | plan_id, project_id, workspace_id optional, title, ordinal, standing, version, target_date optional, blocker_present |
| milestone | plan_id, project_id, title, ordinal, standing, target_date optional |
| deliverable | project_id, workspace_id optional, code, title, discipline, deliverable_type, standing, version, external_authority, target_date optional |
| deliverable_revision | deliverable_id, sequence, external_label optional, standing, version, representation_available |
| risk | project_id, workspace_id optional, category, likelihood, impact, standing, version |
| issue | project_id, workspace_id optional, severity, standing, version |
| human_decision | project_id, workspace_id optional, standing, version, predecessor_present |
| change | project_id, workspace_id optional, standing, version, predecessor_present |
| change_impact | change_id, target_kind optional, standing, impact_class |
| engineering_object | organization_id, project_id, workspace_id optional, family, discipline, object_type, object_subtype, lifecycle, authority_standing, version, created_at, updated_at |
| engineering_context | project_id, workspace_id optional, context_kind, authority, lifecycle, version, typed_payload_present |
| evidence | project_id, workspace_id optional, evidence_kind, standing, version, created_at, updated_at |
| supporting_file | project_id, workspace_id optional, filename, media_type, byte_size, lifecycle, version, created_at, updated_at |
| technical_report | project_id, workspace_id, report_type, title_or_purpose optional, accepted_version_id, accepted_digest, standing, accepted_at |
| organizational_memory | project_id, workspace_id, standing, version, limitations_present, admitted_at |

Every field has the exact scalar/enum/UUID/positive-int type from the listed
owner DTO. Optional means absent, never an inferred empty/default value. No
node can inherit a later source DTO field.

### Exact Engineering Relationship vocabulary

The closed Engineering Relationship pair enum is exactly:

- structural: part_of, belongs_to_system, belongs_to_subsystem,
  belongs_to_package, grouped_with, installed_in, located_in;
- physical: connected_to, mounted_on, connected_through,
  mechanically_coupled_to, terminated_at, routed_through,
  shares_enclosure_with;
- electrical: powered_by, protected_by, isolated_by, earthed_through,
  connected_to_busbar, controlled_by_feeder, backed_up_by_ups;
- instrumentation: measures, transmits_to, receives_process_input_from,
  connected_to_loop, connected_to_io_channel, actuates, positioned_by,
  monitored_by, provides_feedback_to, compensated_by, calibrated_against;
- automation: controlled_by, commands, receives_signal_from, sends_signal_to,
  implemented_in, interlocked_with, trips, initiates, inhibits,
  participates_in_sequence, monitored_by, generates_alarm_for,
  executes_logic_for;
- dependency: depends_on, affects, enables, prevents, constrains, replaces,
  supersedes, derived_from.

A pair is family plus one member of that family. It may join only two authorized
Engineering Object nodes and uses the stored canonical source-to-target
direction. The implementation cannot interpret similarly named types from a
different family as a valid relation.
