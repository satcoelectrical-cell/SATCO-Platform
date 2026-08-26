# EDS-048 — Governed Project Context Assembly & EKG Read Expansion

## 1. Document control

| Field | Value |
|---|---|
| Related PATCH | PATCH-048 — Governed Project Context Assembly & EKG Read Expansion |
| Governing Architecture | Architecture-048 — ACCEPTED / COMPLETE |
| QG-M1 | PASS |
| Status | ACCEPTED / COMPLETE after focused amendment and re-review |
| EDS design authority | GRANTED |
| Independent EDS Review | PASS after focused amendment and re-review |
| Human EDS Acceptance | PASS |
| IDS-048 | NOT STARTED |
| IDS-048 design authority | GRANTED |
| Implementation authority | NOT AUTHORIZED |
| Date | 2026-08-25 |

## 2. Purpose and externally observable boundary

EDS-048 defines two read-only application capabilities:

1. `get_project_context`, which composes requested typed sections for one
   authorized Project and optional authorized Workspace; and
2. EKG node read plus `expand_one_hop`, which returns only explicit authorized
   canonical relationships and authorized target nodes.

No operation mutates a canonical source or PATCH-048 state. PATCH-048 owns the
composition contracts, ordering, bounds, observation semantics and protected
translation only. It owns no Aggregate, relationship, persistence, graph
store, cache of protected facts, transaction, UoW, Audit domain, idempotent
command or outbox event.

## 3. Closed Project Context source allow-list

`ProjectContextSectionKind` is exactly:

1. `project_basis`;
2. `execution`;
3. `deliverables`;
4. `project_controls`;
5. `engineering_context`;
6. `engineering_objects`;
7. `evidence`;
8. `supporting_files`;
9. `technical_reports`;
10. `organizational_memory`.

No wildcard, plug-in source, arbitrary source string or generic “all Project
records” source exists. Duplicate requested sections are invalid. Capture is
excluded because raw/provisional experience is not approved Project Context by
mere Project membership. Engineering Journal is excluded because it is a
presentation-only view without independent canonical identity. Engineering
Relationships and Context Relationships are edge sources, not Project Context
sections. Interface Commitments are excluded until their owner exposes a typed
protected read projection appropriate for cross-domain composition.

### 3.1 Section contents

| Section | Exact V1 content |
|---|---|
| `project_basis` | authorized Project identity/code/name/lifecycle plus Project-keyed Foundation availability, purpose, engineering basis, current stage/readiness, ordered in/out scope, completion basis and Required Project Inputs; no synthetic Foundation identity |
| `execution` | current Plan availability/identity/version, Activities, Milestones, explicit dependencies, local blocker state and owner-derived progress; structural revision history excluded |
| `deliverables` | Deliverable control identity/metadata/current standing and current Revision control metadata, external authoring authority and representation-availability indicator; no authored file content or private storage reference |
| `project_controls` | Risks, Issues, Human Decisions and Changes plus Change Impacts; root standing determines current/historical classification; append-only event history is not bulk-composed |
| `engineering_context` | current Engineering Context only, using the typed projection in §5.5; withdrawn Context requires a separate owner-authorized historical node read |
| `engineering_objects` | authorized Engineering Object projections already permitted by the canonical owner; no relationship inference |
| `evidence` | current authorized Evidence metadata only; Evidence remains evidence, not approval or knowledge |
| `supporting_files` | available authorized Supporting File metadata only; no bytes, object key, storage path, private URL or scan internals |
| `technical_reports` | exact Human-accepted Technical Report records and safe current-version metadata only; drafts, rejected versions and report body are excluded |
| `organizational_memory` | active authorized Organizational Memory metadata only after current source reauthorization; admitted snapshot body and historical inspection are excluded |

An item excluded by lifecycle/standing is not silently replaced by a historical
version. Direct owner-authorized detail/history operations remain available
under their own contracts and do not become PATCH-048 authority.

## 4. Common read contracts

### 4.1 Trusted context

`ProjectContextActor` contains positive `actor_id` and server-derived
`organization_id: UUID`. `ProjectContextScope` contains positive `project_id`
and optional positive `workspace_id`. Organization is never accepted from the
request. Workspace is independently authorized and must belong to the same
Project and Organization.

`ProjectContextRequest` contains:

- `scope: ProjectContextScope`;
- one to ten distinct `ProjectContextSectionRequest` values;
- each section request has one closed section kind, an IDS-bounded positive
  page size, optional integrity-protected continuation and an optional
  owner-supported current-standing filter;
- no client authority, source identity list, raw repository filter or free-form
  relationship query.

### 4.2 Closed top-level results

`ProjectContextResult` is exactly:

- `success(envelope: ProjectContextEnvelope)`;
- payload-free `protected_not_found`;
- payload-free `invalid_request`;
- payload-free `unavailable`.

Unauthorized/inactive actor, Organization mismatch, unauthorized Project or
invalid Workspace scope returns `protected_not_found` before any section is
evaluated or disclosed. Unsupported source/filter/token shape is
`invalid_request`. Failure before any requested section can be safely observed
is `unavailable`.

### 4.3 Envelope and section state

`ProjectContextEnvelope` contains only:

- trusted Project and optional Workspace navigation projection;
- `observation_started_at` and `observation_completed_at`;
- `observation_status: complete_within_bounds | partial`;
- requested section results in the request's canonical section order.

It contains no global Context version, hidden/global total, “Project
completeness” score, missing-information conclusion or cross-source transaction
identifier.

Each requested section result has its public requested section kind and exactly
one state:

- `available`: typed visible items, visible-item count, `truncated`, optional
  continuation and section observation time;
- `empty`: source was authorized and established/listable but yielded no
  visible current fact;
- `not_established`: the authorized canonical owner expressly returned its
  accepted absence state (only Foundation or Execution Plan may use this);
- `not_disclosed`: source-family authorization did not permit section
  disclosure; no identity, existence, count, denial reason or continuation;
- `unavailable`: the public source family could not be observed; no identity,
  count, exception or partial source payload.

`complete_within_bounds` means every requested section is `available`, `empty`
or `not_established`, no section is truncated, and all returned items were
authorized during the request interval. It does not mean the Project is
complete. `partial` means at least one section was safely evaluated and at
least one section is truncated, not disclosed or unavailable. If none can be
safely evaluated because of dependency failure, the top-level result is the
payload-free `unavailable` variant.

The `not_disclosed` state reveals only the requested public section taxonomy,
not whether a protected record exists. An authorized zero-row result is
`empty`; a section denial can never be translated into `empty`.

## 5. Explicit typed source read ports

Every port is inward-owned, request-scoped and typed. Every owner result is a
closed union of its success/empty/not-established, payload-free protected and
payload-free unavailable variants. Ports return immutable DTOs, never mappings,
ORM rows, Sessions, repositories or UoWs.

### 5.1 Project/Foundation

`ProjectBasisContextReadPort.get_authorized_basis(actor, scope)` returns
`ProjectBasisProjection`: Project ID/code/name/status, Foundation
`established | not_established`, Foundation version when present, purpose,
engineering basis, stage/readiness, typed ordered scope/completion/input items,
and source-reauthorization state already approved by PATCH-044. Project and
Foundation authorize first. Foundation provenance is `(project, project_id,
foundation_version)` and has no UUID.

Classification: Human-authoritative Project/Foundation facts; readiness is an
owner-derived interpretation of those facts.

### 5.2 Engineering Execution

`ExecutionContextReadPort.get_authorized_plan(actor, scope)` returns the
canonical `plan_not_established` or `ExecutionContextProjection`: Plan UUID and
version; bounded typed Activity and Milestone projections; explicit Activity
dependency pairs; local blocker fields; and `ExecutionProgressProjection`
containing numerator, denominator and deterministic percent. Ordering is
owner ordinal then canonical UUID. The port enforces current Project/Workspace
visibility.

Classification: Plan/Activity facts are Human-authoritative; Milestone standing
and progress are derived; blockers are Human-recorded local execution facts.

### 5.3 Deliverables

`DeliverableContextReadPort.list_authorized_deliverables(actor, scope, page)`
returns bounded `DeliverableContextProjection` items: UUID, Project/Workspace,
code, title, discipline/type, purpose, standing, version, Activity/Milestone
links, responsibility when independently disclosable, target date,
`external_authority`, and current Revision UUID/sequence/external label/
standing/version/timestamps plus `representation_available`. It returns no
Supporting File identity until that target is independently authorized.

Classification: SATCO control facts are Human-authoritative;
`external_authority` marks authored content as external-tool-authored.

### 5.4 Project Controls

`ProjectControlContextReadPort.list_authorized_controls(actor, scope, kind,
page)` accepts only `risk | issue | human_decision | change`. It returns bounded
typed root projections with canonical UUID, standing, version, safe statement/
control fields, predecessor selector where applicable, and typed Change Impact
children. Human identity fields are excluded from PATCH-048 section, node and
edge projections. Owner detail APIs retain their accepted attribution behavior.
Impact target identity is disclosed only after target authorization.

Root and impact ordering follows canonical owner ordering. Terminal Risk/
Issue, superseded Decision and withdrawn Change are marked `historical`; no
history entry count is exposed.

Classification: controls and potential/confirmed Impacts are Human-recorded or
Human-authoritative exactly according to PATCH-047 standing; terminal records
retain historical classification.

### 5.5 Engineering Context typed-port prerequisite

`EngineeringContextContextReadPort.list_authorized_current(actor, scope,
page)` is a required owner-side application contract. It returns
`EngineeringContextProjection` with:

- positive integer canonical Context ID and owner-issued opaque `context_key`;
- kind, Project/Workspace scope, authority, current lifecycle, purpose, version
  and source timestamps;
- exactly one typed payload variant:
  `SubjectReferenceProjection`, `QualifiedFactProjection`,
  `QualifiedEngineeringValueProjection`, `AssumptionProjection`, or
  `SourceEvidenceReferenceProjection`;
- bounded typed subject references;
- bounded typed source references containing only canonical owner fields and
  only after source/confidentiality authorization.

The projection must not expose the current service's dictionary response. The
composer may not access `EngineeringContextRepository` or its Session. Until
this owner-side port exists and is independently verified, the section returns
`unavailable`; it is never populated by persistence fallback.

Classification follows canonical Context authority: authoritative or
engineer-verified facts are Human-authoritative; assumptions are
contextual/advisory and must remain visibly assumptions.

### 5.6 Engineering Objects

`EngineeringObjectContextReadPort.list_authorized_objects(actor, scope, page)`
returns bounded exact canonical Engineering Object safe fields: UUID,
Organization/Project/Workspace, family, discipline, object type/subtype,
lifecycle, authority standing, version and canonical timestamps. It returns no
body or inferred display meaning.

Classification follows canonical authority standing; Project grouping is
contextual and creates no edge.

### 5.7 Evidence

`EvidenceContextReadPort.list_authorized_current(actor, scope, page)` returns
bounded current Evidence UUID, Project/Workspace, kind, current standing,
version, safe source reference and canonical timestamps permitted by the
Evidence owner. Supported facts/content and protected Human identities are
excluded from the default projection.

Classification: `canonical_evidence`; Evidence is not approval or accepted
knowledge.

### 5.8 Supporting Files

`SupportingFileContextReadPort.list_authorized_available(actor, scope, page)`
returns bounded available asset UUID, Project/Workspace, safe filename/media/
size metadata, lifecycle, version and canonical timestamps. It exposes no
object key, storage path, signed URL, scanner internals or file bytes.

Classification: source material; authored-content authority is not transferred
to SATCO by storage.

### 5.9 Technical Reports

`TechnicalReportContextReadPort.list_authorized_accepted(actor, scope, page)`
returns bounded exact Human-accepted report UUID, Project/Workspace, report
type/title or purpose fields already authorized by the owner, accepted exact
version identity/digest, standing and accepted timestamp. Draft/rejected body,
AI proposal and protected provenance identities are excluded.

Classification: Human-authoritative only for the exact accepted version; report
acceptance is not Organizational Memory admission.

### 5.10 Organizational Memory

`OrganizationalMemoryContextReadPort.list_authorized_active(actor, scope,
page)` returns bounded active Memory UUID, source report UUID/version only when
independently disclosable, Project/Workspace/audience scope, active standing,
version, limitations indicator and admitted timestamp. The owner performs
current source/provenance/linked-Human reauthorization. Snapshot body and
historical records are excluded.

Classification: Human-admitted Organizational Memory; context inclusion is not
reuse approval and never revives withdrawn/superseded memory.

### 5.11 Closed EKG owner-port matrix

EKG reads reuse the section projections above but require explicit owner-side
single-node and incident-edge operations. No generic node/edge resolver exists.
Every method returns its own typed closed union of `resolved` or `page`,
payload-free `protected`, payload-free `invalid` and payload-free `unavailable`.

| Owning capability | Exact EKG read responsibility |
|---|---|
| Project/Workspace | `ProjectWorkspaceGraphReadPort.get_authorized_project` and `get_authorized_workspace`; resolves only positive integer Project/Workspace selectors inside trusted scope; exposes no membership roster or Human identity |
| Engineering Execution | `ExecutionGraphReadPort.get_authorized_plan`, `get_authorized_activity`, `get_authorized_milestone`, and `list_authorized_incident_edges`; incident edges are only plan/activity, plan/milestone, dependency and milestone/activity edges from §7.3 |
| Engineering Deliverable | `DeliverableGraphReadPort.get_authorized_deliverable`, `get_authorized_revision`, and `list_authorized_incident_edges`; only deliverable/activity, deliverable/milestone, deliverable/revision and revision/representation edges |
| Project Control | `ProjectControlGraphReadPort.get_authorized_risk`, `get_authorized_issue`, `get_authorized_decision`, `get_authorized_change`, `get_authorized_impact`, and `list_authorized_incident_edges`; only successor, change/impact and impact/target edges |
| Engineering Object | `EngineeringObjectGraphReadPort.get_authorized_object`; exact canonical object response narrowed by §6.1 |
| Engineering Relationship | `EngineeringRelationshipGraphReadPort.list_authorized_incident`; accepts one Engineering Object selector, exact family/type filters and direction; independently authorizes relationship and both object endpoints |
| Engineering Context | `EngineeringContextGraphReadPort.get_authorized_context`; uses the typed Context projection in §5.5 and never the concrete Session service response |
| Engineering Context Relationship | `EngineeringContextRelationshipGraphReadPort.list_authorized_incident`; exact four meanings and Project/Workspace/Context endpoint kinds only |
| Evidence/Supporting File | `EvidenceFileGraphReadPort.get_authorized_evidence`, `get_authorized_supporting_file`, and `list_authorized_incident`; only explicit Evidence/Supporting File links |
| Technical Report | `TechnicalReportGraphReadPort.get_authorized_accepted_report` and `list_authorized_provenance_edges`; only report/evidence and report/object edges from exact accepted report provenance |
| Organizational Memory | `OrganizationalMemoryGraphReadPort.get_authorized_active_memory` and `get_authorized_source_report_edge`; current source reauthorization precedes Memory or edge disclosure |

Each incident-edge port evaluates only relationships owned by that row's
capability. The composer calls only ports applicable to the authorized start
kind and requested relationship filter. It does not probe every capability,
discover ports dynamically, inspect arbitrary UUIDs or treat one owner's denial
as another owner's authorization. IDS-048 must assign exact per-port call and
candidate bounds and prove no foreign persistence access.

## 6. Closed EKG node allow-list

`ContextNodeKind` is exactly:

- `project` — positive integer Project ID;
- `workspace` — positive integer Workspace ID;
- `execution_plan`, `activity`, `milestone` — canonical UUID;
- `deliverable`, `deliverable_revision` — canonical UUID;
- `risk`, `issue`, `human_decision`, `change`, `change_impact` — canonical UUID;
- `engineering_object` — canonical UUID;
- `engineering_context` — positive integer canonical Context ID;
- `evidence`, `supporting_file`, `technical_report`,
  `organizational_memory` — canonical UUID.

Node lookup requires a discriminated `ContextNodeSelector`; a UUID or integer
without its kind is invalid. Project Foundation is projected only under its
parent Project section and is never a node. Engineering Relationship and
Context Relationship are edges, not nodes. Capture, Journal, Interface
Commitment, discipline and external-source endpoints are not V1 nodes.

Node success contains the kind/selector, minimum safe owner-approved fields,
`FactProvenance`, authority/temporal classification and canonical navigation
reference. Unsupported kind is payload-free `invalid_request`; missing,
inaccessible or cross-scope node is payload-free `protected_not_found`.

### 6.1 Closed node projection fields

Node DTOs are closed PATCH-048 types. They do not automatically inherit new
fields later added to a canonical response.

| Node kind | Exact V1 safe fields in addition to kind/selector/provenance/classification/navigation |
|---|---|
| `project` | Project code, name and lifecycle/status |
| `workspace` | Project ID, discipline and Workspace status |
| `execution_plan` | Project ID, Plan version and established standing |
| `activity` | Plan ID, Project/optional Workspace, title, ordinal, standing, version, target date and blocker-present indicator; blocker rationale excluded |
| `milestone` | Plan ID, Project, title, ordinal, derived standing and target date |
| `deliverable` | Project/optional Workspace, code, title, discipline, type, control standing, version, external authority and target date |
| `deliverable_revision` | owning Deliverable UUID, sequence, external label, control standing, version and representation-available indicator |
| `risk` | Project/optional Workspace, category, likelihood, impact, standing and version; statement/rationale/disposition excluded from graph node |
| `issue` | Project/optional Workspace, severity, standing and version; statement/observed context/disposition excluded |
| `human_decision` | Project/optional Workspace, standing, version and predecessor-present indicator; statement/rationale/alternatives/Human identities excluded |
| `change` | Project/optional Workspace, standing, version and predecessor-present indicator; statement/rationale/Human identities excluded |
| `change_impact` | owning Change UUID, target kind only after target authorization, standing and confirmed/potential classification; statement and Human identity excluded |
| `engineering_object` | Organization/Project/Workspace, family, discipline, object type/subtype, lifecycle, authority standing, version and canonical timestamps; this is a closed narrowed subset of the authorized PATCH-033 projection |
| `engineering_context` | Project/optional Workspace, kind, authority, lifecycle, version and typed-payload-present indicator; purpose, Context payload, source keys, limitations and Human identities excluded from graph node |
| `evidence` | Project/optional Workspace, Evidence kind, current standing, version and canonical timestamps; supported fact/content excluded |
| `supporting_file` | Project/optional Workspace, safe filename, media type, byte size, lifecycle, version and canonical timestamps; object/storage/scanner fields excluded |
| `technical_report` | Project/Workspace, report type/title or purpose, exact accepted version identity/digest, standing and accepted timestamp; body/proposal/Human identities excluded |
| `organizational_memory` | Project/Workspace, active standing, version, limitations-present indicator and admitted timestamp; snapshot body, audience membership and Human identities excluded |

Foundation fields never appear as a separate node. Statements and other richer
section fields remain available only from the independently authorized section
or canonical owner detail operation. All raw actor, owner, steward, reviewer,
approver, responsible, accepted-by, confirmed-by and admitting-Human identities
are excluded from PATCH-048 node/edge projections.

## 7. Closed relationship allow-list

Every edge has `relationship_kind`, canonical direction, source selector,
target selector, relationship owner/source, canonical relationship identity
when the owner has one, current/historical standing, source version/timestamp
when available and safe provenance. No edge owns or copies source content.

### 7.1 Engineering Relationship vocabulary

`engineering_relationship` is permitted only for an exact owner-validated
family/type pair:

| Family | Exact permitted types |
|---|---|
| `structural` | `part_of`, `belongs_to_system`, `belongs_to_subsystem`, `belongs_to_package`, `grouped_with`, `installed_in`, `located_in` |
| `physical` | `connected_to`, `mounted_on`, `connected_through`, `mechanically_coupled_to`, `terminated_at`, `routed_through`, `shares_enclosure_with` |
| `electrical` | `powered_by`, `protected_by`, `isolated_by`, `earthed_through`, `connected_to_busbar`, `controlled_by_feeder`, `backed_up_by_ups` |
| `instrumentation` | `measures`, `transmits_to`, `receives_process_input_from`, `connected_to_loop`, `connected_to_io_channel`, `actuates`, `positioned_by`, `monitored_by`, `provides_feedback_to`, `compensated_by`, `calibrated_against` |
| `automation` | `controlled_by`, `commands`, `receives_signal_from`, `sends_signal_to`, `implemented_in`, `interlocked_with`, `trips`, `initiates`, `inhibits`, `participates_in_sequence`, `monitored_by`, `generates_alarm_for`, `executes_logic_for` |
| `dependency` | `depends_on`, `affects`, `enables`, `prevents`, `constrains`, `replaces`, `supersedes`, `derived_from` |

Endpoints are Engineering Objects. Direction is stored source → target. Current
relationships are default; proposed/rejected/withdrawn/superseded edges require
an explicit owner-authorized historical request.

### 7.2 Context Relationship vocabulary

`context_requires`, `context_provided_by`, `context_consumed_by` and
`context_potentially_affects` map exactly to the owner meanings `requires`,
`provided_by`, `consumed_by`, `potentially_affects`. Only Project, Workspace and
Engineering Context endpoints are V1 eligible. Discipline and external-source
endpoints are excluded. Direction is stored source → target. Only current edges
are returned by default.

`EngineeringContextRelationshipGraphReadPort.list_authorized_incident(actor,
scope, selector, direction, page)` is a required typed owner-side port. It
returns typed edge projections, not mappings, and independently authorizes the
relationship and both endpoints. Direct relationship repository/Session access
is prohibited.

### 7.3 Project execution, deliverable and control edges

| Relationship kind | Canonical owner and direction |
|---|---|
| `plan_activity` | Engineering Execution Plan → Activity |
| `plan_milestone` | Engineering Execution Plan → Milestone |
| `activity_dependency` | predecessor Activity → dependent Activity |
| `milestone_activity` | Milestone → included Activity |
| `deliverable_activity` | Deliverable → linked Activity |
| `deliverable_milestone` | Deliverable → linked Milestone |
| `deliverable_revision` | Deliverable → its Revision |
| `revision_representation` | Deliverable Revision → independently authorized Supporting File |
| `decision_successor` | predecessor Human Decision → explicit successor Decision |
| `change_successor` | predecessor Change → explicit successor Change; existence does not itself change standing |
| `change_impact` | Change → owned Change Impact |
| `impact_target` | Change Impact → exact target kind: Activity, Milestone, Deliverable, Deliverable Revision, Evidence or Supporting File |

These edges are projected only from the owning canonical response. Shared
Project membership never substitutes for the explicit stored link.

### 7.4 Evidence, report and memory traceability edges

| Relationship kind | Canonical owner and direction |
|---|---|
| `evidence_supporting_file` | Evidence/link owner: Evidence → Supporting File |
| `report_evidence_provenance` | Technical Report: Report → Evidence |
| `report_object_provenance` | Technical Report: Report → Engineering Object |
| `memory_source_report` | Organizational Memory: Memory → exact accepted source Technical Report |

These edges require independent target authorization and an owner-exposed typed
relationship. Capture provenance and Engineering Relationship-as-provenance are
excluded because Capture and relationship records are not V1 node kinds.
Provenance co-occurrence never creates an edge.

No Project-membership edge, Workspace-membership edge, timestamp/text/similarity
edge, common-file/common-actor edge, AI edge or generic relation exists.

## 8. One-hop expansion contract

`ExpandOneHopRequest` contains trusted scope, one authorized start selector,
zero or more distinct relationship kinds from §7, direction
`outgoing | incoming | both`, an IDS-bounded page size and optional protected
continuation. It contains no depth parameter.

The application performs exactly:

1. authorize Organization, Project and optional Workspace scope;
2. authorize and resolve the start node;
3. intersect requested kinds with the exact kinds allowed for that node kind;
4. obtain a bounded deterministic incident-edge candidate page only from each
   owning typed relationship port;
5. authorize each relationship and target independently;
6. project only authorized edges and authorized target nodes;
7. stop without resolving relationships from returned targets.

Incoming navigation does not reverse canonical direction; it only selects edges
whose target is the start node. `both` is the deterministic union of authorized
incoming and outgoing candidates. A returned target receives no hidden
second-hop enrichment.

Different non-null Workspace endpoints and all cross-Project/
cross-Organization edges are excluded. A Project-scoped endpoint and one
Workspace endpoint may relate only where the canonical owner expressly permits
that exact relationship and the actor is authorized to the Workspace.

Denied edges/targets are omitted without identity, ordinal, count, relation
kind or denial-source disclosure. If the start node is protected, the entire
result is payload-free `protected_not_found`.

## 9. Determinism, bounds and continuation

The exact section count is bounded by the ten closed section kinds; each may
appear at most once. EDS fixes these further invariants and delegates numerical
operational maxima to IDS-048 because current owners have different accepted
bounds:

- each section page and one-hop request has an explicit hard candidate-scan,
  canonical-call, visible-item, relationship and response-byte maximum;
- the effective maximum never exceeds the smallest applicable canonical owner
  maximum;
- no unbounded fallback, “fetch all”, recursive call or client-increased hard
  maximum exists;
- ordering is owner ordinal where authoritative, then canonical kind and stable
  encoded canonical selector; edge ordering is source kind/selector,
  relationship owner/kind/canonical semantic/direction, target kind/selector,
  canonical edge identity;
- pagination anchor is the last evaluated canonical ordering key, including
  omitted protected candidates;
- continuation is opaque, authenticated, expiring and bound to actor,
  Organization, Project, Workspace, operation, section/relationship filters,
  ordering version and last evaluated key;
- visible count counts only returned items; no hidden/global/authorized total;
- `truncated=true` means the requested view is not complete within the current
  bounds, without revealing whether additional candidates are hidden or
  visible;
- an invalid, expired, tampered or context-mismatched token returns payload-free
  `invalid_request` before source read or disclosure.

IDS-048 must select exact numeric limits from existing owner limits and verify
worst-case composition size; it may narrow but not make these operations
unbounded.

## 10. Non-atomic observation semantics

Project Context is not a cross-domain transaction or snapshot. The composer
records request start/end observation timestamps and a per-section observation
time. Every fact carries canonical version, standing and source timestamp only
where its owner actually provides them. Absence of a version is explicit; the
composer never invents one.

Sources may change between section reads. The envelope therefore means “these
facts were independently authorized and observed during this interval.” It
does not assert simultaneous state, repeatable-read consistency or a Project
Context version. A continuation starts a new observation interval and
reauthorizes current sources; previous pages grant no access and may reflect an
earlier source version.

If a source changes while read:

- an owner-provided version conflict/retry signal may be retried only within
  the IDS-bounded read budget;
- otherwise the affected section is `unavailable` or the operation returns
  payload-free `unavailable` when no section is safely usable;
- the composer never merges different versions of one canonical record into a
  single projection and never substitutes cached/history data.

## 11. Authorization and protected behavior matrix

| Condition | Externally observable behavior |
|---|---|
| unauthorized/inactive Project or Organization mismatch | payload-free `protected_not_found`; no section read |
| unauthorized start node | payload-free `protected_not_found`; no edge read |
| invalid/unauthorized Workspace scope | payload-free `protected_not_found` |
| source section denied after Project authorization | section `not_disclosed`; no identity/count/reason; envelope `partial` |
| inaccessible referenced target | omit edge and target; no hidden count/ordinal/reason |
| cross-Organization edge | treat as protected and omit; security log may record safe category |
| cross-Project or prohibited cross-Workspace edge | omit as protected; never return endpoint metadata |
| unsupported node/relationship/section | payload-free `invalid_request` |
| source unavailable with other usable sections | section `unavailable`; envelope `partial` |
| all requested sources unavailable | payload-free `unavailable` |
| malformed/tampered continuation | payload-free `invalid_request` before source access |

Authorization always precedes existence, field, standing, history, edge,
target, count, truncation-specific detail and continuation disclosure. A
Project-authorized actor does not automatically gain Evidence, file, report,
memory, Context, object or relationship authority.

## 12. Provenance and authority classification

Every fact/node has `FactProvenance`:

- closed owning capability/source kind;
- canonical selector in that owner's exact type;
- canonical version/standing/source timestamp when present;
- composer `observed_at`;
- `authority_class` and `temporal_class`.

Every edge additionally has relationship owner, exact relationship kind,
canonical relationship selector when present, canonical direction and source
version/standing/timestamp when present. Missing owner fields remain absent;
the composer cannot manufacture them.

`authority_class` is exactly:

- `human_authoritative`;
- `external_tool_authored`;
- `canonical_evidence`;
- `derived`;
- `contextual_advisory`.

`temporal_class` is `current | historical`. Owner lifecycle/standing remains a
separate exact field. Derived execution progress is never Human-authored;
Context assumptions remain advisory; Evidence is not approval; EKG navigation
does not prove causality; grouping does not approve a fact; accepted Technical
Report and admitted Memory retain their distinct Human authorities.

## 13. Read logging and privacy

PATCH-048 introduces no new read-Audit domain. Existing security/operational
logging may record actor, trusted Organization, operation, Project, optional
Workspace, requested public source/relationship categories, correlation ID,
bounded result category, timing and safe failure category where policy permits.

Logs must never store section payloads, Context statements/values/assumptions,
report/memory/file content, object-store identifiers, continuation tokens,
hidden identities/counts, denied endpoint metadata, credentials or exception
details. Logging failure cannot cause protected payload disclosure.

## 14. Frontend-observable semantics

The future Project Engineering Context surface can rely on:

- ten typed source sections with explicit authority and temporal classification;
- `empty`, `not_established`, `not_disclosed`, `unavailable`, available and
  truncated states;
- top-level `complete_within_bounds | partial` without a completeness score;
- current-versus-historical standing where the source supports it;
- authorized one-hop related facts with canonical direction and provenance;
- payload-free protected/invalid/unavailable top-level outcomes.

The UI must not turn `partial` into Project incompleteness, hidden-item counts,
an error reason or an AI warning. It uses real API facts, no raw IDs as required
Human input, no fake totals, no generic graph editor and no recommendation/chat
surface. Accessibility, responsive stacking, direction-neutral layout and
isolated display strings remain required; English remains current.

## 15. Backward compatibility

Legacy absence is truthful:

- no Foundation or Plan → owner-returned `not_established`;
- no Deliverables/Controls/Context/Objects/Evidence/Files/accepted Reports/
  active Memory → authorized `empty`;
- no explicit relationships → empty one-hop result.

No record, edge, status, Context version, accepted report, Memory admission or
legacy backfill is fabricated. PATCH-033 `engineering_object/get_node` remains
compatible and independently usable.

## 16. Future Intelligence seam

PATCH-049+ may consume only the same typed `ProjectContextResult`, node and
one-hop edge contracts under a freshly authorized actor/service context. It may
not obtain raw repositories, Sessions, protected continuations or broader
tenant scope. The source/authority/temporal/provenance distinctions remain
attached so later analysis can explain its evidence and limitations.

PATCH-048 performs no completeness or missing-information analysis, question
generation, recommendation, health score, material direction, semantic/vector
search, AI inference, AI-authored relationship or autonomous mutation.

## 17. EDS invariants

1. Context never becomes canonical source authority.
2. Every owner retains mutation and lifecycle authority.
3. No synthetic identity exists; Foundation has only `project_id`.
4. No foreign repository, ORM, Session or UoW access is permitted.
5. Authorization precedes every source, target, field, count and continuation.
6. No relationship is inferred from membership, similarity or co-occurrence.
7. One-hop is an exact maximum; no second-hop enrichment or depth parameter.
8. Cross-source assembly is explicitly non-transactional.
9. Partiality, empty, not-established, not-disclosed and unavailable are
   distinct without revealing protected existence.
10. Candidate, call, response and result bounds plus truncation are explicit.
11. No AI authority or autonomous behavior exists.
12. No PATCH-049 capability exists.
13. Legacy facts are never fabricated or backfilled.
14. External professional tools retain authored-content authority.
15. Journal, Capture, Interface Commitment and unsupported kinds remain outside
    the closed V1 allow-lists.
16. PostgreSQL and source capabilities remain SSOT; no graph-owned persistence
    or cache becomes authority.

## 18. IDS-048 obligations

IDS-048 must define exact immutable DTOs/unions, owner-port method signatures,
safe field optionality, node/edge compatibility matrix, numeric bounds,
continuation cryptography/expiry, ordering keys, call/scan budgets, partiality
algorithm, failure translation, request-scoped composition, thin transport,
frontend API contracts and a verification matrix. It must prove the new typed
Engineering Context and Context Relationship read ports or exclude those
sources from implementation. It may not change this EDS's allow-lists,
authority, one-hop or non-atomic semantics without renewed governance.

## 19. Deferred scope

Deferred are source mutation, graph editing/persistence/database, recursive or
multi-hop traversal, generic source registration, Capture/Journal/Interface
Commitment nodes, completeness and missing-information intelligence,
recommendations/material direction, AI, embeddings/vector/semantic search,
cross-Organization sharing, generic PM/BPM/EDMS, external-tool authoring,
control-system generation, translation completion and all PATCH-049+ work.
