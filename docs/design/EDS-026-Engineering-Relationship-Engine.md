# EDS-026 — Engineering Relationship Engine

## Status

Accepted

## Purpose

Define the complete engineering design for PATCH-026 without implementation.

## Governing Baseline

- approved PATCH-026
- PATCH-021.2 Engineering Relationship Vocabulary
- EngineeringObject Blueprint v1.0
- PATCH-023, PATCH-024, and PATCH-025
- Governance Model and Development Lifecycle

## Architecture and Aggregate Ownership

EngineeringRelationship is a separate Aggregate Root. It owns immutable UUID
identity, immutable source and target EngineeringObject UUIDs, relationship
family/type, governing Organization/Project/Workspace scope, lifecycle,
authority standing, Evidence UUID references,
Creator, Steward, Reviewer, Approver, positive version, timestamps, invariants,
and Domain Events.

EngineeringObject remains the node identity owner. Relationship operations
never mutate endpoint objects. Domain owns invariants, state transitions,
version advancement, and events. Application owns authentication context,
authorization coordination, reference and cycle validation, Unit of Work, and
authorized mapping. Infrastructure implements inward-owned ports. Transport is
FastAPI. Domain and Application do not depend on HTTP, FastAPI, SQLAlchemy
Session, Alembic, or infrastructure implementations.

## Closed Version 1 Vocabulary

Only the following snake-case family/type pairs, all selected from PATCH-021.2,
are creatable. The ordered pair is the canonical vocabulary identifier; type
tokens are not globally unique. The source is the subject of each predicate
and the target is its object.

| Family | Type | Exact meaning |
|---|---|---|
| structural | part_of | source is a constituent of target |
| structural | belongs_to_system | source belongs to the target system object |
| structural | belongs_to_subsystem | source belongs to the target subsystem object |
| structural | belongs_to_package | source belongs to the target package object |
| structural | grouped_with | source is explicitly grouped with target without composition |
| structural | installed_in | source is installed within target |
| structural | located_in | source's governed engineering location is target |
| physical | connected_to | source has direct physical connection to target |
| physical | mounted_on | source is physically mounted on target |
| physical | connected_through | source is physically connected through target |
| physical | mechanically_coupled_to | source is mechanically coupled to target |
| physical | terminated_at | source physically terminates at target |
| physical | routed_through | source is physically routed through target |
| physical | shares_enclosure_with | source and target share an enclosure |
| electrical | powered_by | source receives electrical power from target |
| electrical | protected_by | source is electrically protected by target |
| electrical | isolated_by | source is electrically isolated by target |
| electrical | earthed_through | source is earthed through target |
| electrical | connected_to_busbar | source is electrically connected to target busbar |
| electrical | controlled_by_feeder | source is controlled by target feeder |
| electrical | backed_up_by_ups | source receives backup power from target UPS |
| instrumentation | measures | source measures the process/property represented by target |
| instrumentation | transmits_to | source transmits an instrumentation signal to target |
| instrumentation | receives_process_input_from | source receives process input from target |
| instrumentation | connected_to_loop | source participates in target instrument loop |
| instrumentation | connected_to_io_channel | source connects to target I/O channel |
| instrumentation | actuates | source actuates target |
| instrumentation | positioned_by | source position is controlled by target |
| instrumentation | monitored_by | source is monitored by target |
| instrumentation | provides_feedback_to | source provides feedback to target |
| instrumentation | compensated_by | source measurement/control is compensated by target |
| instrumentation | calibrated_against | source is calibrated against target reference object |
| automation | controlled_by | source behavior is controlled by target |
| automation | commands | source issues a control command to target |
| automation | receives_signal_from | source receives an automation signal from target |
| automation | sends_signal_to | source sends an automation signal to target |
| automation | implemented_in | source logic/function is implemented in target |
| automation | interlocked_with | source participates in an interlock with target |
| automation | trips | source initiates a trip of target |
| automation | initiates | source initiates target action/sequence |
| automation | inhibits | source inhibits target action |
| automation | participates_in_sequence | source participates in target sequence |
| automation | monitored_by | source is monitored by target automation object |
| automation | generates_alarm_for | source generates an alarm for target |
| automation | executes_logic_for | source executes control logic for target |
| dependency | depends_on | source operation or validity depends on target |
| dependency | affects | source has governed engineering impact on target |
| dependency | enables | source enables target behavior |
| dependency | prevents | source prevents target behavior |
| dependency | constrains | source constrains target behavior/design |
| dependency | replaces | source replaces target without asserting lifecycle change |
| dependency | supersedes | source supersedes target under governed lifecycle evidence |
| dependency | derived_from | source engineering meaning is derived from target |

`contains`, `feeds`, `supplied_from`, `measured_by`, `required_by`,
`affected_by`, and other inverse candidates remain derived reverse labels,
not creatable edge types. This prevents two authoritative records for one fact.

Evidence-family and Governance-family candidates do not connect two
EngineeringObjects consistently. They are not creatable edge types in
PATCH-026. Evidence is represented by typed Evidence UUID references;
governance is represented by scope, roles, confidentiality, authorization, and
Audit. Adding non-EngineeringObject endpoints requires a later PATCH.

The two `monitored_by` pairs are intentionally distinct:

- (`instrumentation`, `monitored_by`) records instrumentation observation or
  measurement monitoring;
- (`automation`, `monitored_by`) records monitoring performed by an automation
  system or automation object.

Commands always carry both family and type and use one command semantic for all
pairs. Family is never derived from type. Responses and events always return
both values.

## Direction, Reverse Navigation, and Duplicates

All stored relationships are directional, including connection/grouping
meanings. Reverse navigation may render the approved human-readable inverse but
returns the same relationship UUID and stored source/target. It never inserts a
reciprocal edge.

The active uniqueness identity is Organization, Project, governing Workspace,
source UUID, target UUID, relationship family, and relationship type while lifecycle is
`proposed` or `current`. Creating the same identity returns Duplicate
Relationship. An exact idempotent retry returns its prior result. Reciprocal
source/target is distinct only for a creatable directional predicate; it is
never auto-created. A reverse-label equivalent is rejected because inverse
labels are not creatable types.

## Self-Link and Cycle Policy

Self-links are prohibited for every type.

Cycle validation is performed within the same relationship family/type pair and
same Organization/Project. Composite cycles across different pairs are not
inferred in Version 1.

The following types are acyclic:
`part_of`, `belongs_to_system`, `belongs_to_subsystem`,
`belongs_to_package`, `installed_in`, `located_in`, `powered_by`,
`protected_by`, `isolated_by`, `earthed_through`,
`controlled_by_feeder`, `backed_up_by_ups`, `implemented_in`,
`depends_on`, `enables`, `prevents`, `constrains`, `replaces`,
`supersedes`, and `derived_from`.

For those types, a candidate source-to-target edge is rejected when an
authorized bounded reachability check finds a path from target back to source.
The Unit of Work obtains a transaction-scoped PostgreSQL advisory lock keyed by
Organization, Project, relationship family, and relationship type before cycle
check and insert.

All other approved types permit non-self cyclic topologies because physical
rings, signal feedback, monitoring, grouping, coupling, and engineering
interaction loops may be legitimate. They remain subject to duplicate and
scope rules.

## Lifecycle and Complete Transition Matrix

Lifecycle values are `proposed`, `current`, `superseded`, `withdrawn`,
and `rejected`.

| From | Allowed targets |
|---|---|
| proposed | current, withdrawn, rejected |
| current | superseded, withdrawn |
| withdrawn | proposed |
| superseded | none |
| rejected | none |

Every unlisted transition and every self-transition is rejected. Transition to
`current` requires authority `approved`, at least one valid Evidence UUID,
and visible valid endpoints. Transition to `superseded` requires a distinct
current replacement relationship UUID with compatible scope and meaning.
Withdrawal requires rationale. Restoration to proposed re-enters review and
sets authority to draft. Superseded and rejected are terminal; physical delete
is prohibited.

Authority uses the existing EngineeringAuthorityStanding values:
`draft`, `proposed`, `reviewed`, `approved`, `disputed`, and
`rejected`.

| From | Explicit command and target |
|---|---|
| draft | SubmitEngineeringRelationshipForReview → proposed |
| proposed | ReviewEngineeringRelationship → reviewed; RejectEngineeringRelationship → rejected |
| reviewed | ApproveEngineeringRelationship → approved; RejectEngineeringRelationship → rejected |
| approved | DisputeEngineeringRelationship → disputed |
| disputed | ReviewEngineeringRelationship → reviewed; RejectEngineeringRelationship → rejected |
| rejected | none |

Authority rejection also moves lifecycle to `rejected`. No generic authority
transition is exposed.

## Evidence and Responsibilities

Creation may be proposed without Evidence. At least one unique syntactically
valid Evidence UUID, visible in the same Organization and permitted Project
scope, is required before review and throughout `current` lifecycle.
Approval requires the Reviewer to confirm Evidence adequacy. Evidence payloads
are not copied into relationship, Audit, event, or idempotency records. Missing,
inaccessible, withdrawn, or scope-incompatible Evidence rejects review/current
transition. AI output alone is never adequate Evidence; an authenticated
engineer must explicitly submit the command and approved governed Evidence.

Creator is immutable authenticated actor. Steward defaults to Creator; an
alternate or transfer target must be an active authorized engineer with access
to governing and both endpoint Workspaces. Reviewer is the authenticated actor
of the successful review command. Approver is the authenticated actor of the
successful approval command. Reviewer and Approver must differ; Approver must
differ from Creator. Reviewer and Approver cannot be client-supplied IDs.

## Scope, Confidentiality, and Authorization

Organization is derived from PATCH-025. Both endpoints, Evidence, responsible
Humans, and relationship must be in that Organization. Cross-organization and
cross-project relationships are denied for every Version 1 type.

Same-workspace links are allowed. Cross-workspace links within the same Project
are allowed only for physical, electrical, instrumentation, automation, and
dependency families; structural links require the same Workspace. Actor must
be authorized for both endpoints and both Workspaces. Governing Workspace is
derived from the source object.

No confidentiality label is owned or persisted by EngineeringRelationship in
Version 1. Effective confidentiality is a deterministic access classification
computed for each operation as the intersection of the existing authorization
and visibility decisions for the source EngineeringObject, target
EngineeringObject, every referenced Evidence item, the source Workspace, and,
for cross-Workspace relationships, the target Workspace. The relationship is
visible only when every constituent is visible to the actor for the requested
operation. Authorization is deny-by-default and precedes disclosure of the
relationship, endpoints, identifiers, counts, or traversal paths. Any failed
constituent decision produces Protected Not Found and no partial relationship
redaction is permitted. Query totals count only fully authorized results.

This policy adds no confidentiality field to EngineeringObject, Evidence,
EngineeringWorkspace, or EngineeringRelationship. A persisted independent
classification or redaction policy requires a separate approved PATCH and
Architecture Review.

## Extension Rules

The closed Version 1 enums shall not accept database-configured, tenant-defined,
plugin-defined, or free-text relationship pairs. A future pair requires a new
approved PATCH and Product Owner decision defining its existing or new family,
exact source-target semantics, direction and inverse display, endpoint kinds,
scope, Evidence, responsibility, confidentiality, uniqueness, cycle class,
lifecycle applicability, migration, API compatibility, and tests.

Extensions are additive and shall not reinterpret an existing family/type pair,
weaken historical validation, or add
domain-specific behavior to Core. Removal or semantic change requires a
versioned migration and backward-compatibility plan. Module-specific types
remain owned by their module and integrate through the relationship ports.

A future approved family may reuse an existing type token because the family
is its semantic namespace. Such reuse adds a new pair without changing stored
values, API meaning, or behavior of any existing pair.

## Commands and Atomicity

Canonical commands are:

- `CreateEngineeringRelationship`
- `SubmitEngineeringRelationshipForReview`
- `ReviewEngineeringRelationship`
- `ApproveEngineeringRelationship`
- `DisputeEngineeringRelationship`
- `RejectEngineeringRelationship`
- `TransitionEngineeringRelationshipLifecycle`
- `TransferEngineeringRelationshipSteward`

Creation has no expected version. Every other command requires positive
expected_version, non-empty rationale, correlation UUID, idempotency UUID, and
Evidence references where required. Each invokes one Aggregate Root method and
increments version exactly once.

Idempotency scope is actor, command type, and key. Exact committed replay
returns the recorded authorized response; changed fingerprint returns
Idempotency Conflict.

One Unit of Work and PostgreSQL transaction atomically persist relationship
state, Audit using entity_uuid, outbox Domain Events, and idempotency outcome.
Failure rolls back all. Events are past-tense committed facts and publish only
after commit. Audit separately records accountability.

## Bounded Queries

Direct endpoint lists are paginated at default 20 and maximum 100.
Neighborhood and path queries require max_depth 1–5 and max_results 1–100,
defaulting to depth 1 and 20 results. Ordering is relationship UUID ascending
after relationship type, source UUID, and target UUID. Queries accept only
approved family/type, lifecycle, direction (`incoming`, `outgoing`,
`both`), and Workspace filters.

Every visited edge and node is authorized before disclosure. Traversal is
cycle-safe and may return a continuation token. No arbitrary query language,
unlimited depth, unauthorized count, or graph-wide export is allowed.

## Ports and Persistence

Required inward-owned ports are EngineeringRelationshipRepository, UnitOfWork,
AuthorizationPolicy, EngineeringObjectReferenceValidator, EvidenceValidator,
ResponsibilityValidator, CycleDetector, AuditRecorder, DomainEventRecorder,
IdempotencyStore, and Clock.

PostgreSQL is authoritative. One additive migration creates only
`engineering_relationships`, `engineering_relationship_outbox`, and
`engineering_relationship_idempotency`, with exact IDS-026 fields,
constraints, foreign keys, partial uniqueness, and indexes. It reuses
`audit_logs.entity_uuid` unchanged.

## Acceptance

EDS-026 is accepted subject to EDS Review PASS, IDS-026 approval, executable
Implementation Plan-026, AR-026 PASS, and IRR-026 readiness.
