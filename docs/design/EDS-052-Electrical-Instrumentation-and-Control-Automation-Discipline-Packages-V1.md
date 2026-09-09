# EDS-052 — Electrical, Instrumentation, and Control & Automation Discipline Packages V1

## 1. Status, authority, and verdict

| Field | Value |
|---|---|
| Date | 2026-09-04 |
| PATCH | PATCH-052 — Electrical, Instrumentation, and Control & Automation Discipline Packages V1 |
| Human EDS design authority | **GRANTED** |
| Architecture basis | Architecture-052 **ACCEPTED / COMPLETE** |
| ADR basis | ADR-025 **ACCEPTED**; ADR-024 **ACCEPTED** |
| PATCH-051 | **DONE / CLOSED** |
| Independent EDS candidate | PASS / ACCEPTED-CANDIDATE / READY FOR HUMAN EDS ACCEPTANCE |
| Independent EDS review | **PASS**; Critical/Major/Minor/Observation `0/0/0/1` |
| Documentation remediation cycles | `0 of 3` |
| Human EDS-052 acceptance | **PASS / ACCEPTED on 2026-09-04** |
| EDS-052 | **ACCEPTED** |
| IDS-052 | AUTHORIZED FOR DESIGN |
| Implementation Plan-052 | NOT STARTED / NOT AUTHORIZED |
| Production/test implementation | NOT AUTHORIZED / NONE CREATED OR MODIFIED BY THIS EDS RUN |
| Migration | NOT AUTHORIZED / NONE CREATED / NONE EXECUTED |
| Alembic source head | Sole `e05100000006` |
| PATCH-053+ | NOT STARTED / NOT AUTHORIZED |
| Commercial V1 roadmap | HUMAN-FROZEN / UNCHANGED |

This candidate translates accepted Architecture-052 into implementation-ready
engineering contracts. It does not record Human EDS acceptance, authorize IDS,
choose implementation files, allocate a migration revision, or change any
accepted upstream contract. Normative terms **MUST**, **MUST NOT**, **SHALL**,
**SHALL NOT**, and **EXACTLY** are binding on later IDS and implementation.

## 2. Repository reconciliation and design posture

Direct repository inspection established the following current facts:

1. PATCH-051 is `DONE / CLOSED`; its Registry/configuration, Workspace binding,
   standing, canonicalization, compatibility, Audit, entitlement seam, and
   frontend trust-boundary implementation is present.
2. ADR-025 is Accepted; Architecture-052 is Accepted/Complete; PATCH-052 is
   Registered/Open.
3. No EDS-052, IDS-052, Implementation Plan-052, PATCH-052 source release,
   operational descriptor, adapter, component, production/test implementation,
   or migration existed before this artifact.
4. `release_051_core_v1.py` still declares an empty operational Registry;
   the static adapter table and trusted frontend component map remain empty.
5. existing EKG vocabulary has every accepted V1 Object type except
   `electrical_feeder` and `electrical_power_source`; it has all required
   Relationship types and all ADR-025 Identifier kinds but no Identifier owner.
6. Context subjects are currently only `project|workspace|discipline`; the
   `engineering_object` subject and reference are absent.
7. Object, Relationship, Capture, and Deliverable roots have no package-origin
   fields. Evidence remains an independent owner and needs none.
8. Technical Report historical bases are V1 for Capture/Object/Relationship;
   Python/Pydantic unions and PostgreSQL validation do not accept the required
   package-origin V2 locators.
9. the migration graph has sole head `e05100000006`; no PATCH-052 migration
   exists; PATCH-053 has not begun; staged files are zero.
10. unrelated tracked and untracked work was identified and is outside this
    EDS. It is neither evidence of PATCH-052 implementation nor modified here.

Where accepted Architecture exceeds present code, this EDS states a later
requirement. It never silently weakens Architecture to fit current code.
`IDS051-OBS-01` remains open, non-blocking, and owned by later deployment
evidence; this EDS neither resolves nor fabricates that evidence.

## 3. System boundary and invariant hierarchy

PATCH-052 instantiates the accepted PATCH-051 Core with exactly three
operational packages in one release. Authority resolves in this order:

`owner data authorization AND trusted Registry capability AND Organization
enablement AND exact Project selection/profile AND Workspace binding or
authorized applicability AND membership standing AND entitlement decision AND
package operation policy`.

No predicate grants another. Canonical owners remain:

| Concern | Authoritative owner |
|---|---|
| Registry, release membership, profile, compatibility | PATCH-051 source Registry and derived projection |
| Project selection and Workspace binding | PATCH-051 configuration services |
| Objects / Relationships | existing EKG aggregates |
| Engineering Identifiers | ADR-025 Engineering Identifier aggregate |
| Capture | Engineering Experience Capture aggregate |
| Context | Engineering Context aggregate |
| Evidence | Evidence aggregate and Human standing |
| Deliverables and revisions | Engineering Deliverable aggregate |
| Technical Reports | Technical Report aggregate and Human acceptance |
| Organizational Memory | explicit Human admission from one accepted Report |
| Audit | existing centralized/owner transaction paths |

There is no package-owned fact store, rule-result store, copied Context store,
parallel Object graph, or direct package-to-Memory path.

## 4. Shared operational package contract

An operational package is one immutable descriptor in source release
`patch-052.eic-v1`, one exact `EXECUTABLE_SUPPORTED` release membership, and one
statically registered precompiled adapter. It MUST include finite catalogs,
rules, workflow declarations, one compiled component key, conformance vectors,
origin semantics, resource declarations, and fail-closed readiness. Descriptor
or conformance presence alone is not operational.

All descriptors have `schema_version=1`, `package_version=1.0.0`,
`core_contract_versions=(1,)`, empty dependencies/conflicts, and ordinary
contributions with `schema_version=1`, `version=1.0.0`, and `owner=PACKAGE`.
The single existing taxonomy family contribution is `owner=CORE`.

| PackageKey | Primary DisciplineId | adapter_id | EntitlementKey | display name | component/route/navigation key |
|---|---|---|---|---|---|
| `electrical` | `electrical` | `discipline.electrical.v1` | `discipline.electrical` | Electrical V1 | `workspace.electrical.v1` |
| `instrumentation` | `instrumentation` | `discipline.instrumentation.v1` | `discipline.instrumentation` | Instrumentation V1 | `workspace.instrumentation.v1` |
| `control_automation` | `control_automation` | `discipline.control_automation.v1` | `discipline.control_automation` | Control & Automation V1 | `workspace.control_automation.v1` |

The profile is exactly `commercial_v1.eic@1.0.0`, Core contract `1`, empty
`required_interface_ids`, and aggregate resource ceiling `190`. It permits
exactly seven non-empty selections: the three singles, three pairs, and the
E/I/C triple, all at `1.0.0`. Their aggregate units are respectively
Electrical `62`, Instrumentation `60`, Control `68`, E+I `122`, E+C `130`,
I+C `128`, and E+I+C `190`. Canonical source assembly computes descriptor,
combination, profile, selection-set, and Registry digests; no caller or author
handwrites an authoritative digest.

Every package declares:

- one taxonomy family at ordinal 1;
- two role requirements, mutate then evaluate, for `(admin,engineer)` and the
  existing owner predicates;
- matching authorization declarations using composition `intersection`;
- one deliberately non-executing standards hook and one deliberately
  non-executing cross-discipline interface;
- exactly five deterministic rule hooks;
- one frontend key with visibility `effective_package_authorized`; and
- thirteen package conformance declarations.

The standards hooks use `{PackageKey}.standards_applicability@1.0.0`, schemas
`package.standards_applicability_input.v1` and
`package.standards_applicability_output.v1`, `max_results=0`, `timeout_ms=1`,
and no executor. Interfaces are `electrical.power_supply_interface`
Electrical-to-Instrumentation `provides`, `instrumentation.signal_interface`
Instrumentation-to-Control `provides`, and
`control_automation.command_interface` Control-to-Electrical `constrains`;
each is `1.0.0` with null consistency/change-impact hooks and zero traversal.

The contribution inventory and resource-unit arithmetic are exact:

| Count | Electrical | Instrumentation | Control & Automation |
|---|---:|---:|---:|
| taxonomy / Objects / Relationships | 1 / 8 / 7 | 1 / 8 / 5 | 1 / 7 / 13 |
| Context / inputs / Deliverables | 5 / 9 / 4 | 5 / 9 / 4 | 5 / 9 / 5 |
| Evidence / deterministic rules | 4 / 5 | 4 / 5 | 4 / 5 |
| standards / interfaces / roles / authorization | 1 / 1 / 2 / 2 | 1 / 1 / 2 / 2 | 1 / 1 / 2 / 2 |
| migration compatibility / conformance | 0 / 13 | 0 / 13 | 0 / 13 |
| aggregate units | **62** | **60** | **68** |

## 5. Exact Object, Context/input, and Identifier-kind catalogs

Object declaration IDs are `{PackageKey}.object.{object_type}` in listed
ordinal order. Lifecycle is `engineering_object.lifecycle.v1`; authority is
`owner.engineering_object.mutate`. Each new package-origin Object MUST be
created atomically with the listed primary Identifier kind.

| Package | Exact Object types in ordinal order | Existing/additive | Required primary kind |
|---|---|---|---|
| Electrical | `motor`, `transformer`, `mcc`, `switchgear`, `electrical_panel`, `electrical_cable`, `electrical_feeder`, `electrical_power_source` | first six existing; last two PATCH-052 additive | respectively `equipment_number`, `equipment_number`, `panel_number`, `panel_number`, `panel_number`, `cable_number`, `feeder_number`, `equipment_number` |
| Instrumentation | `instrument`, `transmitter`, `analyzer`, `flowmeter`, `control_valve`, `instrument_loop`, `junction_box`, `instrument_panel` | all existing | respectively `tag_number`, `tag_number`, `tag_number`, `tag_number`, `tag_number`, `loop_number`, `panel_number`, `panel_number` |
| Control & Automation | `plc`, `dcs_controller`, `esd_controller`, `control_cabinet`, `io_channel`, `hmi`, `control_logic` | all existing | respectively `equipment_number`, `equipment_number`, `equipment_number`, `panel_number`, `controlled_external_key`, `panel_number`, `system_identifier` |

Electrical `electrical_feeder` is one independently identified incoming or
outgoing feeder. `electrical_power_source` is the abstract upstream supply only
when an existing concrete `transformer` is inaccurate. Neither implies a
generator, UPS, vendor, procurement, or calculation workflow.

The Context base declarations are exact:

| Package | Base IDs in ordinal order | Subject/storage/cardinality |
|---|---|---|
| Electrical | `system_voltage_basis`, `load_duty_basis`, `source_feeder_basis`, `protection_basis`, `earthing_basis` | voltage and source-feeder: Workspace, respectively qualified value/fact, max 1; other three: Object, respectively qualified value/fact/fact, max 64 |
| Instrumentation | `measurement_service`, `operating_range`, `design_conditions`, `signal_basis`, `loop_basis` | all Object, max 64; operating range/design conditions are qualified values, others facts |
| Control & Automation | `control_philosophy_basis`, `io_allocation_basis`, `alarm_interlock_basis`, `cause_effect_basis`, `availability_redundancy_basis` | philosophy and availability: Workspace facts, max 1; other three: Object facts, max 64 |

Each fully qualified base is `{PackageKey}.{base}`. Its Context declaration is
`{base_id}.context` with `context_kind_id={base_id}`,
`value_schema_id={base_id}.v1`, exactly the stated subject, and `required=true`.
Its Context input is `{base_id}.input`, same ordinal, `source_kind=context`,
`input_type_id={base_id}`, `required=true`, and the stated occurrence bound.
Object cardinality is independently evaluated for every applicable Object;
one Object never satisfies another.

Required Context mapping by Object is exact:

- Electrical motor/cable: all five; transformer/MCC/switchgear/panel: voltage,
  load, protection, earthing; feeder: voltage, source-feeder, protection; power
  source: voltage, source-feeder.
- Instrumentation sensing/final-element types: all five; loop: measurement,
  signal, loop; junction box/panel: signal, loop.
- Control controllers/cabinet/I/O: philosophy, I/O allocation,
  alarm-interlock, availability; HMI: philosophy, alarm-interlock,
  availability; logic: philosophy, alarm-interlock, cause-effect.

## 6. Exact Relationship catalog and endpoint tuples

Relationship declarations are version `1.0.0`, `owner=PACKAGE`, use lifecycle
`engineering_relationship.lifecycle.v1`, and are `many_to_one` unless stated.
Both endpoints MUST be independently authorized before package resolution.
Abbreviations below mean exact machine types; comma-separated lists expand
only to the finite Cartesian product shown.

| Declaration (ordinal) | Exact source -> target | Direction / cross-Workspace |
|---|---|---|
| `electrical.relationship.powered_by` (1) | motor, mcc, switchgear, electrical_panel, electrical_cable, electrical_feeder -> electrical_power_source, transformer, switchgear, mcc, electrical_panel | directed / no |
| `electrical.relationship.protected_by` (2) | motor, transformer, mcc, electrical_panel, electrical_cable, electrical_feeder -> switchgear, mcc, electrical_panel | directed / no |
| `electrical.relationship.isolated_by` (3) | motor, transformer, mcc, electrical_panel, electrical_cable, electrical_feeder -> switchgear, mcc, electrical_panel, electrical_feeder | directed / no |
| `electrical.relationship.earthed_through` (4) | all eight Electrical types -> electrical_cable | directed / no |
| `electrical.relationship.connected_to_busbar` (5) | transformer, electrical_cable, electrical_feeder -> switchgear, mcc, electrical_panel | directed / no |
| `electrical.relationship.controlled_by_feeder` (6) | motor, electrical_panel, electrical_cable -> electrical_feeder | directed / no |
| `electrical.relationship.backed_up_by_ups` (7) | motor, mcc, switchgear, electrical_panel -> electrical_power_source | directed / no; target role asserts UPS without a UPS type |
| `instrumentation.relationship.transmits_to` (1) | transmitter, analyzer, flowmeter -> junction_box, instrument_panel | directed / no |
| `instrumentation.relationship.connected_to_loop` (2) | instrument, transmitter, analyzer, flowmeter, control_valve -> instrument_loop | directed / no |
| `instrumentation.relationship.connected_to_io_channel` (3) | instrument, transmitter, analyzer, flowmeter, control_valve -> io_channel | directed / yes |
| `instrumentation.relationship.provides_feedback_to` (4) | instrument, transmitter, analyzer, flowmeter -> instrument_loop, instrument_panel, io_channel | directed / yes only for io_channel |
| `instrumentation.relationship.calibrated_against` (5) | instrument, transmitter, analyzer, flowmeter, control_valve -> instrument, analyzer | directed / no |
| `control_automation.relationship.controlled_by` (1) | hmi, io_channel, control_logic -> plc, dcs_controller, esd_controller | directed / no |
| `control_automation.relationship.commands` (2) | plc, dcs_controller, esd_controller, control_logic -> io_channel, control_valve, motor | directed / yes only for non-Automation target |
| `control_automation.relationship.receives_signal_from` (3) | plc, dcs_controller, esd_controller, io_channel -> instrument, transmitter, analyzer, flowmeter, io_channel | directed / yes only for Instrumentation target |
| `control_automation.relationship.sends_signal_to` (4) | plc, dcs_controller, esd_controller, io_channel -> hmi, io_channel, control_valve | directed / yes only for Instrumentation target |
| `control_automation.relationship.implemented_in` (5) | control_logic -> plc, dcs_controller, esd_controller | directed / no |
| `control_automation.relationship.interlocked_with` (6) | control_logic, plc, dcs_controller, esd_controller -> same four-type set | bidirectional, many-to-many / no |
| `control_automation.relationship.trips` (7) | esd_controller, control_logic -> motor, control_valve, plc, dcs_controller | directed / yes only for non-Automation target |
| `control_automation.relationship.initiates` (8) | plc, dcs_controller, esd_controller, control_logic -> control_logic | directed / no |
| `control_automation.relationship.inhibits` (9) | control_logic, plc, dcs_controller, esd_controller -> control_logic | directed / no |
| `control_automation.relationship.participates_in_sequence` (10) | all seven Automation types -> control_logic | directed, many-to-many / no |
| `control_automation.relationship.monitored_by` (11) | plc, dcs_controller, esd_controller, io_channel, control_logic -> hmi | directed / no |
| `control_automation.relationship.generates_alarm_for` (12) | plc, dcs_controller, esd_controller, control_logic -> hmi, motor, control_valve, instrument, transmitter | directed / yes only for non-Automation target |
| `control_automation.relationship.executes_logic_for` (13) | plc, dcs_controller, esd_controller -> control_logic, motor, control_valve | directed / yes only for non-Automation target |

Instrumentation Core relations `measures`, `receives_process_input_from`,
`actuates`, `positioned_by`, `monitored_by`, and `compensated_by` remain
readable but are not package-mediated V1 mutations. Exact tuples live in a
source-controlled adapter allow-list keyed by package/version/declaration; they
do not require a PATCH-051 descriptor-shape amendment. No tuple authorizes
graph traversal, inference, propagation, or cross-package rule invocation.

## 7. Deliverable and Evidence declaration contract

All four Evidence-backed input declarations per package are `required=false`,
`source_kind=evidence`, `max_occurrences=8`, ordinals 6..9. The first three use
`engineering_record`, `minimum_count=1`, operation
`{PackageKey}.evaluate_readiness`, and `human_verification_required=true`.
The fourth uses `human_review`, `minimum_count=1`, operation
`{PackageKey}.deliverable_issue`, and Human verification.

| Package | Evidence requirement IDs in ordinal order |
|---|---|
| Electrical | `electrical.voltage_source_basis_evidence`, `electrical.load_basis_evidence`, `electrical.protection_feeder_basis_evidence`, `electrical.deliverable_review_evidence` |
| Instrumentation | `instrumentation.measurement_process_basis_evidence`, `instrumentation.range_condition_basis_evidence`, `instrumentation.loop_calibration_basis_evidence`, `instrumentation.deliverable_review_evidence` |
| Control & Automation | `control_automation.control_philosophy_evidence`, `control_automation.io_allocation_evidence`, `control_automation.cause_effect_interlock_evidence`, `control_automation.deliverable_review_evidence` |

Deliverable IDs are `{PackageKey}.deliverable.{type}`, in table order,
`human_acceptance_required=true`. Input aliases E1..E5, I1..I5, C1..C5 mean
the five Context inputs in section 5 order; EE/IE/CE1..3 mean the first three
Evidence inputs above.

| Package / deliverable type | Exact required inputs | Output representations |
|---|---|---|
| Electrical `electrical_load_list` | E1,E2,EE1,EE2 | `spreadsheet` |
| Electrical `single_line_diagram` | E1,E3,E4,E5,EE1,EE3 | `cad,document,eplan` |
| Electrical `electrical_cable_schedule` | E1,E2,E3,E4,E5,EE2,EE3 | `eplan,spreadsheet` |
| Electrical `electrical_equipment_datasheet` | E1,E2,E4,E5,EE1,EE2,EE3 | `document` |
| Instrumentation `instrument_index` | I1,I4,I5,IE1 | `spreadsheet` |
| Instrumentation `instrument_datasheet` | I1,I2,I3,I4,IE1,IE2 | `document` |
| Instrumentation `instrument_loop_diagram` | I1,I4,I5,IE1,IE3 | `cad,document` |
| Instrumentation `instrument_io_list` | I1,I4,I5,IE1 | `spreadsheet` |
| Control `control_io_list` | C1,C2,C5,CE1,CE2 | `spreadsheet` |
| Control `control_narrative` | C1,C3,C4,C5,CE1,CE3 | `document` |
| Control `cause_effect_matrix` | C1,C3,C4,CE1,CE3 | `document,spreadsheet` |
| Control `alarm_interlock_schedule` | C1,C2,C3,C4,CE1,CE2,CE3 | `spreadsheet` |
| Control `control_system_architecture_diagram` | C1,C2,C5,CE1,CE2 | `cad,document` |

Readiness for one Deliverable uses exactly its row, including only the selected
eligible Evidence IDs. Package readiness uses the stable ordered union for the
requested Deliverables. There is no universal three-Evidence gate. The fourth
Evidence item never participates in ready-for-review; it applies only to issue
of the exact already Human-reviewed revision.

`human_verification_required=true` means the Evidence is `lifecycle=current`,
its `source_standing=current`, and its transition to current was performed by
an owner-authorized Human recorded in the existing Evidence event/Audit path.
For the fourth item, `source_kind=human_review`, `source_reference` is the
canonical lower-case Deliverable UUID, and `source_revision` is the canonical
lower-case UUID of that exact Deliverable revision. This closed use of existing
Evidence fields supplies an explicit durable revision reference without adding
package authority or a parallel Evidence link store. The first three items use
`source_kind=engineering_record` and retain their owner-controlled source
reference/revision semantics.

## 8. Engineering Identifier integration

ADR-025 controls without reinterpretation. `EngineeringIdentifier` is a
separate EKG-adjacent aggregate root, not an Object child or package record. Its
exact ordered durable V1 fields are:

`identifier_id, engineering_object_id, organization_id, project_id,
workspace_id, identifier_kind, display_value, normalized_value,
normalization_algorithm_version, issuing_scope_kind, issuing_scope_value,
lifecycle, authority_standing, primary_role, evidence_references, version,
predecessor_identifier_id, successor_identifier_id, creator_id, steward_id,
reviewer_id, approver_id, created_at, updated_at, origin_package_key,
origin_project_configuration_revision, origin_declaration_id`.

The identifier is UUID-rooted and references exactly one immutable Object UUID.
Scope fields are non-null, immutable, and coherent with that Object. Kind is
the existing `EngineeringIdentifierKind`. Display and normalized values are
1..128 Unicode scalar values. The server alone computes normalized value using
Unicode NFKC, Unicode trim, internal Unicode-whitespace collapse to U+0020,
then default Unicode casefold; empty, control, unassigned, or overlength output
is rejected. Algorithm identity is fixed
`satco_identifier_nfkc_casefold_v1`.

V1 package creation derives `issuing_scope_kind=project` and decimal Project ID
as `issuing_scope_value`. Lifecycle is `current|superseded|withdrawn`; standing
is `draft|proposed|reviewed|approved|disputed|rejected`; role is
`primary|alternate`; Evidence references are 0..8 unique UUID-sorted handles.

The current uniqueness key is exactly `(organization_id, project_id,
issuing_scope_kind, issuing_scope_value, identifier_kind, normalized_value)`.
An Object has 0..16 current Identifiers and unbounded retained historical rows
through bounded pagination. A package-origin Object atomically completes
creation with exactly one current primary of its declared required kind and may
later have at most fifteen alternates. A seventeenth current Identifier fails
atomically. Exactly one current primary exists for every package-origin Object;
Core/legacy Objects may have zero. Equal normalized values are allowed across
different kinds, issuing scopes, Projects, or Organizations.

Correction creates a new current successor and atomically supersedes/links the
predecessor. Lineage is same-scope, same-Object, acyclic, non-branching, and
non-merging. Withdrawal retains the row. No created Identifier is physically
deleted. Primary reassignment locks/rechecks the complete current set, changes
versions atomically, and cannot grant approval or leave a package-origin Object
without a primary. Every operation authorizes Project, Workspace, Object, and
Identifier before values, matches, conflicts, counts, lineage, standing, or
origin are disclosed.

## 9. Durable, derivable, and Audit provenance

New package-defined Objects, Relationships, package-mediated Captures,
Deliverables, and Identifiers created in the package-mediated Object transaction
MUST own the all-or-none non-null immutable origin triple:

`origin_package_key, origin_project_configuration_revision,
origin_declaration_id`.

The declaration carried by each origin is exact: Object and its same-transaction
primary Identifier use `{PackageKey}.object.{object_type}`; Relationship uses
the exact section-6 Relationship declaration; Capture uses the initiating
`{base_or_evidence_id}.input`; Deliverable uses
`{PackageKey}.deliverable.{deliverable_type}`. No aggregate may borrow a
declaration from a different descriptor, Project revision, or owner operation.

It is assigned by the server from the authorized immutable Project selection,
not accepted from the client or reconstructed from current Workspace state.
The aggregate's Project/Workspace plus the triple MUST resolve to the exact
selection and declaration and remain immutable across Organization/Project
reconfiguration, Workspace rebind, release/standing transition, package
upgrade, and rule transition. An origin-bearing Object cannot be reclassified
to another package/declaration/family/discipline/type; an origin-bearing
Deliverable cannot change discipline/type. Supersession/new creation is used.

Legacy records have three nulls and present as `legacy_unattributed`. They are
never classified by type-string matching or current binding. Context and
Evidence do not gain origin merely by satisfying a package input. No backfill
is permitted.

| Provenance class | Exact content |
|---|---|
| Durable aggregate-owned | package key, Project configuration revision, declaration ID |
| Derivable immutable | package version and descriptor digest from exact selection; Registry digest and profile/combination identity from revision/profile; declaration/rule version from retained descriptor |
| Audit-only operation | exact package/version/descriptor; Registry digest where current execution, standing, projection, compatibility, configuration, readiness, or drift applies; origin revision; Organization configuration version/selection digest where applicable; declaration and rule identity/version; result/source-version digest; aggregate ID and before/after version; actor; correlation; causation; outcome and safe reason |
| Not historical origin | current Workspace binding, current Registry standing, copied whole descriptor, current Organization configuration |

Audit facts are captured at operation time from the authorized immutable
snapshot and never reconstructed later. No protected values or full descriptor
are written to Audit. Successful owner mutations, owner history/outbox, and
Audit commit atomically. Denials follow existing security Audit policy without
tenant or source disclosure.

## 10. Configuration, Workspace, and standing semantics

PATCH-051 remains authoritative:

`Organization configuration -> immutable Project revision/profile/exact
selection -> derived Workspace binding -> effective state`.

Membership standing belongs to `(RegistryDigest, PackageKey, PackageVersion)`,
never the descriptor. `EXECUTABLE_SUPPORTED` is necessary but insufficient for
new selection/execution. `HISTORICAL_READ_ONLY` prohibits new selection,
configuration/reconfiguration to that version, operational Workspace creation
or binding, package-mediated Object/Relationship/Capture/Identifier/Deliverable
mutation, and rule execution. It preserves owner-authorized historical
interpretation using retained revisions/descriptors.

Workspace rebind updates current execution eligibility but never rewrites
aggregate origin. `control_automation` mappings remain boundary-specific and
exact: Workspace/API raw legacy `control`; EKG/Capture/Report discipline
`industrial_automation`; Object family `automation`; Guidance category
`automation_and_control`. Raw history is preserved; there is no fuzzy,
case-insensitive, or global alias mapping.

## 11. Canonical owner workflow contracts

### 11.1 Object and Relationship

Package-mediated Object creation MUST authorize the owner scope first, resolve
an `OPERATIONAL_PACKAGE_BOUND` exact revision, validate finite type membership,
run the mapped integrity gate, and atomically create the Object, required
primary Identifier, immutable origins, owner event/outbox, and Audit. Any
failure rolls back all writes. Legacy Object adoption/reclassification is not a
package operation.

Relationship creation independently authorizes the relationship scope and
both endpoints before package/catalog lookup, validates existing owner family/
type rules and the exact adapter tuple, records immutable origin, and commits
with owner Audit. It creates no inferred edge and performs no traversal.

### 11.2 Capture

Capture is an affordance/source workflow. A package operation may preselect a
trusted input declaration and create an otherwise canonical Capture carrying
origin. Capture text, Human authorship, lifecycle, and source reference remain
Capture-owned. Capture existence never satisfies an input. Only a later
separately authorized canonical Context or Evidence record mapped by the exact
declaration can satisfy it. Historical Captures resolve origin read-only;
missing execution standing disables package action but not authorized owner
read.

### 11.3 Context/input

Context gains subject kind `engineering_object` and nullable
`subject_engineering_object_id: UUID`. The closed shape requires exactly that
field non-null and Project/Workspace/Discipline subject fields null for this
kind. A restrictive Object FK plus database/service coherence MUST reject
Organization, Project, or Workspace mismatch. Subject uniqueness and lookup
indexes include the Object UUID. Create/read/list/history authorizes both
Context and Object before disclosure. Object deletion/mutation never deletes
or mutates Context. Because other subject columns are nullable, later physical
design MUST use shape-specific unique indexes or equivalent NULL-safe
enforcement; ordinary nullable composite uniqueness is insufficient. Logical
identity remains one `(context_id, engineering_object)` subject reference.

Assessment input is an explicitly selected stable UUID-ordered set, not an
implicit whole Workspace assertion. It consumes current/historical owner
projections and source versions. `partial`, protected, stale, unavailable, or
truncated projections produce `INDETERMINATE`; they never mean `missing`.

### 11.4 Evidence

Rules receive only authorized Evidence handles and bounded safe metadata.
Evidence source kind, standing, lifecycle, supporting-file access, and Human
verification remain Evidence-owned. Packages cannot inspect files by a new
path, fabricate Evidence, approve Evidence, or convert hidden Evidence into an
absence finding.

### 11.5 Deliverable

Package-declared Deliverables carry root origin; canonical revisions and
external-authoring authorities remain unchanged. The ready-for-review gate
checks the exact revision and section-7 required inputs. It does not mark the
revision reviewed. The separate issue gate requires that same revision already
be owner/Human `reviewed` plus one current Human-verified fourth Evidence item
explicitly referencing it. It does not itself review, approve, or issue; the
owner transition remains authoritative. This ordering prevents circular
readiness/review dependencies.

### 11.6 Technical Report V2 and Organizational Memory

V1 locators remain byte-immutable. Package-origin sources use only these exact
required Python/domain/Pydantic field orders:

- `CaptureHistoricalBasisV2`: `basis_schema_version, source_category,
  capture_id, source_version, organization_id, project_id, workspace_id,
  origin_package_key, origin_project_configuration_revision,
  origin_declaration_id, discipline, engineering_object_id, source_kind,
  original_content, source_reference, creator_id, lifecycle, created_at`.
- `EngineeringObjectHistoricalBasisV2`: `basis_schema_version,
  source_category, engineering_object_id, source_version, organization_id,
  customer_id, project_id, workspace_id, origin_package_key,
  origin_project_configuration_revision, origin_declaration_id, identifiers,
  family, discipline, object_type, subtype, lifecycle, authority_standing,
  creator_id, steward_id`.
- `EngineeringRelationshipHistoricalBasisV2`: `basis_schema_version,
  source_category, engineering_relationship_id, source_version,
  organization_id, project_id, workspace_id, origin_package_key,
  origin_project_configuration_revision, origin_declaration_id,
  source_object_id, target_object_id, relationship_family, relationship_type,
  lifecycle, authority_standing, evidence_references, creator_id, steward_id,
  reviewer_id, approver_id`.

All use `basis_schema_version=2`; source categories and inherited field types,
bounds, enums, normalization, and nullability remain V1. Nullable fields are
Capture `workspace_id`, `discipline`, `engineering_object_id`, and
`source_reference`; Object `customer_id` and constant-null `subtype`; and
Relationship `reviewer_id`/`approver_id`. All other fields are non-null. The
origin triple is non-null and resolves coherently. Extra keys are forbidden.

Object `identifiers` is a non-null 1..16 array of the complete locked/rechecked
current set. Every item contains exactly, in order: `identifier_id,
identifier_version, identifier_kind, display_value, normalized_value,
normalization_algorithm_version, issuing_scope_kind, issuing_scope_value,
lifecycle, authority_standing, primary_role, evidence_references,
predecessor_identifier_id, successor_identifier_id, creator_id, steward_id,
reviewer_id, approver_id, created_at, updated_at, origin_package_key,
origin_project_configuration_revision, origin_declaration_id`. It has exactly
one primary; every item is current; successor is null; Evidence UUIDs are
unique/lexical; array order is primary before alternate, then kind, normalized
value, UUID. Snapshot origins are either all null or coherent/all non-null.

Draft construction locks/rechecks Object version and complete current
Identifier set. Acceptance re-authorizes and rechecks Object version, every
Identifier ID/version, and complete-set equality in the acceptance transaction;
any change makes the basis stale. Accepted snapshots never perform live
Identifier lookup. Capture/Relationship V2 have no identifiers. Evidence
locators are unchanged; Deliverable and rule finding are not new source types.

Canonical JSON remains UTF-8 lexical-key serialization, while semantic arrays
keep defined order. Existing SHA-256 integrity/historical-basis digests cover
the complete V2 bytes. Human Report acceptance is unchanged. Organizational
Memory remains an explicit Human admission from one accepted Report and only
inherits its immutable projection/manifest; packages never write Memory.

## 12. Deterministic rule execution contract

Each hook is an exact source declaration mapped to a precompiled trusted
implementation by `(PackageKey, PackageVersion, hook_id, hook_version)`. The
server-owned enforcement matrix, never adapter output, assigns
`VALIDATION_BLOCKING` or `GUIDANCE_ONLY`. Unknown mappings are Guidance-only or
unavailable as the requested gate requires; no rule can expand owner authority.

| Package | Exact hook IDs in ordinal order |
|---|---|
| Electrical | `electrical.object_relationship_integrity`; `electrical.required_input_completeness`; `electrical.source_feeder_connectivity`; `electrical.evidence_sufficiency`; `electrical.deliverable_readiness` |
| Instrumentation | `instrumentation.object_relationship_integrity`; `instrumentation.required_input_completeness`; `instrumentation.loop_signal_connectivity`; `instrumentation.evidence_sufficiency`; `instrumentation.deliverable_readiness` |
| Control & Automation | `control_automation.object_relationship_integrity`; `control_automation.required_input_completeness`; `control_automation.io_logic_connectivity`; `control_automation.evidence_sufficiency`; `control_automation.deliverable_readiness` |

| Suffix (all `1.0.0`) | Input/output schemas | Gate and exact bounds |
|---|---|---|
| `object_relationship_integrity` | `package.object_relationship_validation.v1` -> `package.validation_result.v1` | package-mediated Object/Relationship create only; 64 Objects, 128 Relationships, 256 KiB input, 16 findings, 64 KiB output, 50 ms |
| `required_input_completeness` | `package.input_completeness.v1` -> `package.assessment_result.v1` | readiness only; 64 Objects, 322 Context, 24 Evidence, 384 KiB, 32 findings, 64 KiB, 100 ms |
| Electrical `source_feeder_connectivity`; Instrumentation `loop_signal_connectivity`; Control `io_logic_connectivity` | `package.relationship_completeness.v1` -> `package.assessment_result.v1` | readiness only; 64 Objects, 128 Relationships, 256 KiB, 32 findings, 64 KiB, 100 ms |
| `evidence_sufficiency` | `package.evidence_sufficiency.v1` -> `package.assessment_result.v1` | readiness only; 24 Evidence, 32 Deliverables, 128 KiB, 32 findings, 64 KiB, 100 ms |
| `deliverable_readiness` | `package.deliverable_readiness.v1` or `package.deliverable_issue.v1` -> `package.validation_result.v1` | ready-for-review: 64 Objects/322 Context/24 Evidence/32 Deliverables, 384 KiB, 32 findings, 64 KiB, 100 ms; issue: exact revision/8 review Evidence, 64 KiB, 8 findings, 32 KiB, 100 ms |

Exact hook IDs prepend the package key. Input envelopes contain only
server-derived scope/revision/observation interval, bounded already-authorized
typed projections with IDs/versions and availability flags, and exact required
catalog declarations. Output is a closed ordered `PASS|FINDINGS|INDETERMINATE|
UNAVAILABLE` result with package/rule provenance, selectors, observation
interval, bounded findings, limitations, and canonical result digest. Ordering
is hook ordinal, finding code, stable source selector. Equal versioned input is
byte-deterministic.

Rules are one bounded pass with monotonic timeout, no recursion, continuation,
network, file, subprocess, database/session/repository handle, prompt, URL,
arbitrary expression, or cross-package call. Results are ephemeral. A
materially relied-on owner mutation records safe rule/result identity in Audit;
findings are never canonical Report sources.

`eval`, `exec`, runtime `compile`, dynamic imports, entry points, directory
scanning, uploaded Python/JavaScript/WASM/native content, customer scripts,
descriptor SQL/shell/templates, remote registries/downloads, runtime code
generation, and descriptor component paths are prohibited.

## 13. API contract requirements

Later IDS MAY choose route grouping but MUST expose these closed logical
operations through existing owner services rather than parallel package CRUD:

| Operation | Authoritative request selectors | Required safe result |
|---|---|---|
| capability discovery/catalog | authorized Project or Workspace; cursor/limit where catalog is paged | server-derived effective state, safe display metadata, finite catalog options, allowed actions, revision; no descriptor body |
| package readiness assessment | Workspace, explicit sorted unique Object IDs (0..64), Deliverable IDs (0..32), expected configuration revision | closed result/status, safe ordered findings/limitations, observation interval, origin/rule identity, source-version digest |
| package-mediated Object create | existing owner Object fields, primary `display_value`, expected scope/version, rationale/idempotency; server derives the declaration-required Identifier kind | canonical Object plus Identifier identities/versions and origin presentation |
| package-mediated Relationship create | existing owner fields/endpoints and expected versions, rationale/idempotency | canonical Relationship identity/version and origin presentation |
| package-mediated Capture create | canonical Capture input plus trusted catalog selection, rationale/idempotency | canonical Capture identity/version and origin presentation |
| package-declared Deliverable create/readiness/issue gate | canonical owner fields/revision, selected declaration, expected versions, rationale/idempotency | canonical Deliverable/revision and separate gate result |
| Identifier create/read/list/history/resolve/supersede/withdraw/reassign-primary | typed owner selectors, expected versions, bounded cursor/limit, rationale/idempotency | owner DTO with allowed actions; protected/not-found for hidden, missing, or ambiguous resolution |

Requests MUST NOT accept authoritative Organization/tenant identity, descriptor
or Registry digest, standing, profile/combination authority, origin triple,
normalized Identifier value, authorization facts, actor identity, result digest,
or frontend component path. PackageKey/version, when present as a selector,
MUST be validated against the server-derived exact Project/Workspace revision
and cannot override it. Actor/tenant/correlation are trusted server/header
context under existing policy.

Mutation DTOs are `extra=forbid`, versioned, idempotent where the owner already
requires it, and use optimistic versions. Collection responses use stable
ordering and scope-bound opaque cursors. Descriptor catalogs and assessment
envelopes are not client-submitted. Limits are enforced before repository/rule
work. Existing package configuration endpoints and owner APIs remain
authoritative; PATCH-052 adds capabilities without weakening them.

Pagination and response bounds are exact: the existing supported-package page
remains `limit 1..50`; one package capability response returns its complete
intrinsically bounded catalog (at most 8 Objects, 13 Relationships, 9 inputs,
5 Deliverables, 4 Evidence declarations, and 5 rules) with no continuation;
the complete current Identifier set returns 0..16 in canonical order with no
continuation; Identifier history uses an opaque scope-bound cursor, default 50
and maximum 100; assessment has no continuation and is bounded by section 20.
No API may page a rule envelope into multiple executions or follow a returned
continuation inside one assessment.

Transport behavior is: authentication failure `401`; authorization/tenant or
ambiguous protected selector `404`; malformed/overbound request `422` unless
the accepted assessment contract requires a successful `INDETERMINATE`
resource result; state/version/configuration/standing conflict `409`; Registry,
adapter, rule, or readiness infrastructure unavailable `503`. Responses MUST
not expose hidden IDs, counts, catalog membership, package state, source
absence, collision candidates, or findings.

## 14. Frontend contract

Exactly three bundled components populate the existing frozen trusted map:
`workspace.electrical.v1`, `workspace.instrumentation.v1`, and
`workspace.control_automation.v1`. They share a shell but preserve discipline
terminology and journeys. The server supplies authorized effective state,
allowed actions, safe catalogs, requirement status, origin presentation, and
bounded results. The client never decides package validity or hardcodes a
literal discipline as enablement authority.

Each component provides Overview; Objects; Relationships; Inputs/Context;
Evidence & Deliverables; deterministic Guidance; and links to Capture and
Technical Reports. Controls derive only from allowed actions. Electrical uses
source/feeder/MCC/motor/cable language; Instrumentation uses instrument/loop/
range/signal/calibration language; Control uses exact controller/cabinet/I/O/
HMI/logic and legacy translation language.

| Server/source state | Required presentation |
|---|---|
| `OPERATIONAL_AVAILABLE` | ordinary authorized UI only when readiness also passes |
| `FUTURE_UNAVAILABLE` | truthful unavailable discipline; no package execution |
| `HISTORICAL_ONLY` | authorized records as `historical_read_only`; no mutation/rules |
| `LEGACY_UNRESOLVED` | raw accepted identity; no fabricated package |
| source metadata `partial` | deterministically force operation `INDETERMINATE`; never display PASS/FINDINGS |
| protected/not-found | render no surface, facts, count, state, or retry detail that discloses existence |

Keyboard, screen-reader, focus, responsive, RTL, loading, empty, stale,
conflict, unavailable, timeout, safe retry, and unknown-key failure evidence is
required. No descriptor HTML, executable code, import, URL, or raw generic
string editor may become the primary operational experience.

## 15. Authorization, tenant isolation, and non-disclosure

Authorization occurs before package metadata resolution or source disclosure.
Object and Context authorization includes their owning Project/Workspace;
Relationship includes both endpoints; Capture, Evidence, Deliverable, Report,
and every assessment projection use their existing owner policies. A partial
authorized projection can be reported only as a safe limitation. Package
enablement, binding, standing, entitlement, Identifier primary/approval, and
configuration never grant data access or Human authority.

Cross-tenant and unauthorized selectors converge on protected/not-found and
must disclose no difference among absent, inaccessible, ambiguous, disabled,
or incompatible records. Historical origin is resolved only after owner
authorization; it may expose the retained label/version required to interpret
that record, never unrelated current configuration.

## 16. Readiness contract

Operational readiness is non-empty and fail-closed. It verifies exact source
release/canonical bytes/expected Registry digest; all three descriptors,
adapters, capability IDs, membership standings, profile and seven combinations;
source/projection parity; catalog-to-owner mapping including the two Electrical
types and Identifier model; origin schema and retained historical resolution;
Object Context subject; every rule/schema/resource mapping; three compiled
components; all conformance identities/digests; database constraints,
ownership, grants, triggers, and accepted non-commercial entitlement adapter.

Readiness returns only a safe overall failure externally. It MUST NOT install,
repair, backfill, activate, change standing/configuration, or write evidence.
Missing current execution material blocks execution; missing required retained
history blocks affected historical interpretation and writes. No descriptor,
component, or test PASS alone establishes readiness.

## 17. Conformance manifest and exact inventory

`ConformanceVectorV1` has exact field order:

`schema_version, vector_id, subject_kind, subject_id, release_id,
package_selection, descriptor_digest_selector, scenario_purpose, fixture_id,
setup_preconditions, authoritative_inputs, operation_id, executor_reference,
expected_result, expected_provenance, authorization_expectation,
tenant_expectation, historical_expectation, failure_expectation`.

Every field is present/non-null. `schema_version=1`; release is
`patch-052.eic-v1`; subject kind is
`package_declaration|release_combination`; IDs are distinct dotted IDs 1..128.
Maps/enums are closed canonical data. `operation_id` and `executor_reference`
select only precompiled harness functions. There is no code, expression,
import, SQL, template, prompt, URL, or executable path.

Each descriptor has the thirteen suffixes, in order:
`registration_projection`, `organization_project_configuration`,
`workspace_binding`, `object_workflow`, `relationship_workflow`,
`context_input`, `evidence_expectation`, `deterministic_rule`,
`deliverable_expectation`, `audit_provenance`, `authorization_negative`,
`tenant_negative`, `historical_read_only`. Declaration ID is
`{P}.conformance.{suffix}` and vector ID is
`patch_052.{P}.v1.{suffix}`. That is exactly 39 package vectors.

The explicit package vector inventory is:

| Package | Exact vector IDs in authoritative order |
|---|---|
| Electrical | `patch_052.electrical.v1.registration_projection`; `patch_052.electrical.v1.organization_project_configuration`; `patch_052.electrical.v1.workspace_binding`; `patch_052.electrical.v1.object_workflow`; `patch_052.electrical.v1.relationship_workflow`; `patch_052.electrical.v1.context_input`; `patch_052.electrical.v1.evidence_expectation`; `patch_052.electrical.v1.deterministic_rule`; `patch_052.electrical.v1.deliverable_expectation`; `patch_052.electrical.v1.audit_provenance`; `patch_052.electrical.v1.authorization_negative`; `patch_052.electrical.v1.tenant_negative`; `patch_052.electrical.v1.historical_read_only` |
| Instrumentation | `patch_052.instrumentation.v1.registration_projection`; `patch_052.instrumentation.v1.organization_project_configuration`; `patch_052.instrumentation.v1.workspace_binding`; `patch_052.instrumentation.v1.object_workflow`; `patch_052.instrumentation.v1.relationship_workflow`; `patch_052.instrumentation.v1.context_input`; `patch_052.instrumentation.v1.evidence_expectation`; `patch_052.instrumentation.v1.deterministic_rule`; `patch_052.instrumentation.v1.deliverable_expectation`; `patch_052.instrumentation.v1.audit_provenance`; `patch_052.instrumentation.v1.authorization_negative`; `patch_052.instrumentation.v1.tenant_negative`; `patch_052.instrumentation.v1.historical_read_only` |
| Control & Automation | `patch_052.control_automation.v1.registration_projection`; `patch_052.control_automation.v1.organization_project_configuration`; `patch_052.control_automation.v1.workspace_binding`; `patch_052.control_automation.v1.object_workflow`; `patch_052.control_automation.v1.relationship_workflow`; `patch_052.control_automation.v1.context_input`; `patch_052.control_automation.v1.evidence_expectation`; `patch_052.control_automation.v1.deterministic_rule`; `patch_052.control_automation.v1.deliverable_expectation`; `patch_052.control_automation.v1.audit_provenance`; `patch_052.control_automation.v1.authorization_negative`; `patch_052.control_automation.v1.tenant_negative`; `patch_052.control_automation.v1.historical_read_only` |

The seven combined vector IDs are exactly:

1. `patch_052.eic_v1.combination.electrical`
2. `patch_052.eic_v1.combination.instrumentation`
3. `patch_052.eic_v1.combination.control_automation`
4. `patch_052.eic_v1.combination.electrical_instrumentation`
5. `patch_052.eic_v1.combination.electrical_control_automation`
6. `patch_052.eic_v1.combination.instrumentation_control_automation`
7. `patch_052.eic_v1.combination.electrical_instrumentation_control_automation`

Thus the authoritative inventory is **46 vectors: 39 package + 7 combined**.
The common fixture uses Organization UUID `00000000-0000-0000-0000-000000000001`,
Project `101`, Electrical/Instrumentation/Control Workspaces `201/202/203`,
engineer `301`, unauthorized same-tenant actor `302`, foreign Organization UUID
`00000000-0000-0000-0000-000000000002`, foreign Project/Workspace `102/204`,
and observation interval `2026-01-01T00:00:00.000000Z` through
`2026-01-01T00:05:00.000000Z`. Correlation UUID is
`00000000-0000-0000-0000-000000009001`.

Object UUID final-four ranges are Electrical `0101..0108`, Instrumentation
`0201..0208`, and Control `0301..0307` in descriptor order, expanded against
`00000000-0000-0000-0000-000000000000`. Relationship ranges start
`1101/1201/1301`, Context `2101/2201/2301`, Evidence `3101/3201/3301`, and
Deliverable `4101/4201/4301`, incremented by declaration ordinal. Authorized
legacy cross-discipline Core Objects are `0901` motor, `0902` control_valve,
`0903` instrument, `0904` transmitter, and `0905` io_channel.

Object/Relationship fixtures are proposed/draft version 1; Identifier fixtures
current/draft version 1; Context current version 1; Evidence created at version
1 then current version 2; Deliverables planned version 1 with draft revision 1
unless the issue case transitions that exact revision. Numeric fixtures are
Electrical `400 V` and `10 kW`, Instrumentation `0..100 kPa`, and Control
availability `dual`; fact values are their exact base IDs. Evidence is current
and Human-verified. Primary examples are `M-101`, `FT-101`, and `DCS-101`.
Context source is `fixture://{base_id}`; Evidence source is
`fixture://{requirement_id}` with revision `1`; these are inert strings and are
never dereferenced.

| Package | Exact Object/display slice | Representative relationships in declaration order | Inputs |
|---|---|---|---|
| Electrical | all 8: `motor=M-101`, `transformer=TR-101`, `mcc=MCC-101`, `switchgear=SWG-101`, `electrical_panel=PNL-101`, `electrical_cable=CBL-101`, `electrical_feeder=FDR-101`, `electrical_power_source=SRC-101` | feeder powered_by source; motor protected_by switchgear; transformer isolated_by switchgear; mcc earthed_through cable; transformer connected_to_busbar mcc; motor controlled_by_feeder feeder; mcc backed_up_by_ups source | all applicable E1..E5; EE1..EE4; all four exact Deliverable rows |
| Instrumentation | all 8: `instrument=PT-101`, `transmitter=FT-101`, `analyzer=AT-101`, `flowmeter=FE-101`, `control_valve=FV-101`, `instrument_loop=FIC-101`, `junction_box=JB-101`, `instrument_panel=IP-101` | transmitter transmits_to junction box; flowmeter connected_to_loop loop; valve connected_to_io_channel legacy 0905; transmitter provides_feedback_to loop; instrument calibrated_against analyzer | all applicable I1..I5; IE1..IE4; all four exact Deliverable rows |
| Control & Automation | all 7: `plc=PLC-101`, `dcs_controller=DCS-101`, `esd_controller=ESD-101`, `control_cabinet=CC-101`, `io_channel=IO-101`, `hmi=HMI-101`, `control_logic=CL-101` | hmi controlled_by dcs; logic commands I/O; I/O receives_signal_from legacy 0904; I/O sends_signal_to legacy 0902; logic implemented_in dcs; plc interlocked_with esd; esd trips legacy 0901; plc initiates logic; esd inhibits logic; hmi participates_in_sequence logic; dcs monitored_by hmi; logic generates_alarm_for hmi; dcs executes_logic_for logic | all applicable C1..C5; CE1..CE4; all five exact Deliverable rows |

Each package's thirteen vectors have this exact structured meaning:

| Suffix | Setup/operation | Exact result/failure boundary |
|---|---|---|
| `registration_projection` | install exact release and descriptor/adapter; `registry.project` | canonical projection equality; byte drift is `INVALID_DESCRIPTOR` |
| `organization_project_configuration` | enable and pin revision 1/profile; `configuration.resolve` | exact selection/digests and `OPERATIONAL_AVAILABLE`; incompatible selector fails closed |
| `workspace_binding` | bind Workspace to revision 1; `workspace.resolve_effective` | `OPERATIONAL_PACKAGE_BOUND` plus compiled key; stale revision conflicts |
| `object_workflow` | create every listed Object plus required primary/origin; `owner.object.create` | Object/Identifier version 1; wrong/missing kind or type rolls back |
| `relationship_workflow` | exact representative endpoints; `owner.relationship.create` | origin-bearing version-1 edge; undeclared pair rolls back |
| `context_input` | all applicable Context; `{P}.evaluate_readiness` | complete ordered bases; omitted is FINDINGS, protected/truncated is INDETERMINATE |
| `evidence_expectation` | exact per-Deliverable Evidence selection; `{P}.evidence_sufficiency` | PASS without universal extras; selected missing is FINDINGS, hidden is INDETERMINATE |
| `deterministic_rule` | complete, omit first input, mark partial, force timeout; `{P}.evaluate_readiness` | `PASS,FINDINGS,INDETERMINATE,UNAVAILABLE`, stable reason, no mutation |
| `deliverable_expectation` | every exact row; ready-for-review and issue subcase | exact revision passes; missing row input rolls back; issue needs reviewed revision + fourth Evidence |
| `audit_provenance` | rely materially on one result; `audit.read` | section-9 exact safe event fields; identity mismatch fails conformance |
| `authorization_negative` | actor 302 lacks Workspace/source access | protected/not-found; no payload/count/finding |
| `tenant_negative` | actor in first Organization supplies foreign scope | protected/not-found; no existence signal |
| `historical_read_only` | rebind revision 2, old membership historical | exact revision-1 origin, read-only, no mutation/rule; current substitution fails |

All ordinary cases use authorized actor 301 and same tenant, except the two
negative rows. Expected provenance includes release, package/version,
descriptor digest, revision 1, declaration, Registry digest where current
execution applies, correlation, and aggregate/result versions. Combined
vectors install the same exact release, select exactly the named sorted set,
run compatibility/effective-state resolution, and assert `compatible=true`,
profile `commercial_v1.eic@1.0.0`, computed digests, no collision, the exact
aggregate units, and zero cross-package rule invocation/traversal. Unknown or
eighth combinations, digest drift, or units over 190 fail closed.

`expected_result_digest` is a source constant equal to lowercase SHA-256 of
canonical expected-result JSON. Registry assembly rejects missing, placeholder,
or mismatched values. The trusted harness requires canonical byte equality and
digest equality, not only PASS/FAIL. Future IDS MUST mechanically materialize
the accepted Architecture-052 fixture UUIDs, values, order, and negative cases
without inventing or dropping a vector.

## 18. Persistence verdict and required extensions

**Verdict C — EXISTING PERSISTENCE + BOUNDED PROVENANCE EXTENSION.** Existing
Registry/configuration projection, canonical owner stores, Report snapshots,
and Memory manifests remain authoritative. No package database or result store
is permitted.

A later separately authorized Batch-2 cutover MUST deliver these logical
schema requirements:

1. add `electrical_feeder` and `electrical_power_source` to the EKG Object enum,
   family map, application validation, database CHECK, API schema, and
   projections; no other type is added;
2. add nullable origin triple fields to canonical Object, Relationship,
   Capture, Deliverable, and Identifier roots, with an all-null/all-non-null
   check, immutable update guard, and coherent restrictive reference to
   `(project_id, configuration_revision, package_key)`; existing rows remain
   null;
3. add the ADR-025 Identifier root, immutable/versioned history, idempotency,
   transactional outbox/Audit integration, restrictive Object/scope/Evidence/
   actor/lineage references, current scoped-uniqueness index, current-primary
   uniqueness, and Object-scoped transaction guard for the 16/current-primary
   invariants;
4. extend Context subject enum/shape with `engineering_object` and
   `subject_engineering_object_id`, restrictive Object FK, scope-coherence
enforcement, subject uniqueness/lookup, authorization, projection, and
history parity;
5. add V2 Capture/Object/Relationship domain/Pydantic/repository/API/Memory
   readers and replace the hard-coded PostgreSQL historical-basis validators
   with closed V1-or-corresponding-V2 branches; no Report table source FK or
   new source type is added; and
6. extend existing owner history/outbox/Audit payload validation and necessary
   lookup/authorization indexes without changing owner transaction authority.

The later schema MUST make package-origin Object plus primary-Identifier
creation one transaction; prevent direct/bypass origin or classification
mutation; prevent Identifier physical deletion, seventeenth current row,
multiple current primaries, cross-scope lineage, and uniqueness races; and keep
accepted Report/Memory bytes and digests unchanged.

## 19. Migration requirements and legacy semantics

Migration ownership is Batch 2 and requires later Human authority and an exact
manifest. This EDS allocates no revision number or file. The migration SHOULD
be additive where possible and MUST descend linearly from the then-current sole
head. It MUST preflight source/deployed heads, enum/check contents, row shapes,
roles/grants, validator identities, and deployed-data anomalies before writes.

Legacy semantics are exact:

- existing owner rows retain null origin and are `legacy_unattributed`;
- no type, name, Identifier-looking text, current binding, current Project
  selection, or Registry membership may fabricate origin or Identifier;
- existing Context subjects remain unchanged;
- existing Report V1 locators, accepted snapshots, canonical bytes, SHA-256
  digests, and Memory manifests are never rewritten;
- no package-origin classification is inferred during upgrade;
- any future adoption needs separate governed Human authority, Evidence,
  rationale, owner command, and Audit, and cannot claim historical package
  creation.

Required proof uses isolated real PostgreSQL and covers fresh-install/upgrade
convergence, linear head, downgrade/recovery or explicitly guarded forward
recovery, transactional rollback, constraints/indexes/triggers/roles/grants,
legacy-null reads, no row/digest rewrite, all Identifier invariants/races,
Object-subject coherence/history, old-origin resolution across multiple
rebinds/releases, Report Python/Pydantic/repository/SQL/Memory V1/V2 golden
parity, and zero prepared transactions/clean session state. Deployment-specific
census/qualification remains `IDS051-OBS-01`.

## 20. Resource and performance contract

| Resource | Exact bound |
|---|---:|
| selected Objects / Relationships | 64 / 128 |
| selected Deliverables | 32 |
| readiness Evidence / issue Evidence | 24 / 8 |
| Context projections | Electrical 322; Instrumentation 320; Control 130; shared ceiling 322 |
| Context / Object / Relationship projection bytes | 768 / 384 / 320 each |
| Evidence / Deliverable projection bytes | 512 / 512 each |
| envelope/catalog/availability overhead | 32 KiB |
| readiness envelope | 384 KiB |
| adapter memory class | `bounded_4mib` |
| adapter timeout class | `bounded_100ms` |
| hooks per operation / dependency traversal | 5 / 0 depth and 0 visits |
| combined ordered findings | 128 after stable de-duplication |
| chunk/continuation inside one rule evaluation | none |

Overscope or a permitted selection that cannot fit MUST deterministically
return `INDETERMINATE` with safe `scope_exceeds_limit` or
`projection_exceeds_limit`; a blocking mutation fails closed. It never returns
a partial PASS or truncates required Context for an otherwise permitted scope.

Later evidence MUST prove bounded query counts independent of hidden tenant
data; index-supported plans for origin resolution, Identifier uniqueness/current
set/history, Object Context lookup, Evidence/Deliverable selection, and Report
acceptance recheck; no N+1 query by Object/Identifier/Context; stable ordering;
timeout enforcement; maximum envelopes/findings; and representative p95/plan
evidence in a controlled environment. This EDS invents no latency target beyond
accepted PATCH-051 gates and the exact per-rule timeouts above.

## 21. Closed failure semantics

| Category | Required meaning/behavior |
|---|---|
| `unavailable` | missing/drifted Registry, adapter, rule, component, schema, historical material, or entitlement dependency; no repair |
| `protected_not_found` | unauthorized, foreign, absent, or ambiguous protected selector; no differentiating detail |
| `historical_read_only` | retained authorized origin readable; no selection, mutation, configuration, or rule execution |
| `incompatible` | exact selection/profile/dependency/resource contract rejected; no partial configuration |
| `invalid_configuration` | missing/incoherent Organization/Project/Workspace selection or binding |
| `missing_required_context` | fully observed authorized scope lacks a required Context; FINDINGS or blocking gate failure as mapped |
| `indeterminate` | source partial/protected/stale/truncated or bounded evaluation cannot truthfully decide |
| `resource_limit_exceeded` | accepted count/byte/time/finding boundary exceeded; no partial PASS |
| `rule_failure` | timeout, exception, output/schema/digest mismatch; unavailable/rollback at blocking gate |
| `stale_configuration` | expected revision/head/Workspace binding changed; conflict and complete retry |
| `provenance_mismatch` | origin cannot resolve/cohere with retained selection/declaration; fail closed |
| `readiness_failure` | any readiness dimension fails; safe overall unavailable and no repair |

Existing `DisciplinePackageReasonCode` values are reused wherever equivalent,
including `registry_unavailable`, `historical_only`, `profile_not_allowed`,
`migration_required`, `migration_incompatible`, `resource_limit_exceeded`, and
`legacy_unresolved`. Later IDS may map internal detail to the safe categories
but may not broaden disclosure or collapse `missing` and `indeterminate`.

## 22. Human and AI authority

AI is optional, assistive, separately authorized, and non-authoritative. It
cannot become a rule executor, fabricate Context/Evidence/Identifiers/origin,
approve engineering, accept Reports, issue Deliverables, or admit Memory.

Deterministic rules are machine-executed but not Human-authoritative. Blocking
is limited to the exact requested package-mediated mutation/readiness gate.
Human/owner authority controls Evidence standing, Deliverable review and issue,
Identifier review/approval, engineering approval, Technical Report acceptance,
and Organizational Memory admission. Package state never grants engineering
authority. No autonomous approval or publication exists.

Electrical excludes load-flow, short-circuit, sizing, settings, final design,
CAD/EPLAN/ETAP authoring, vendor selection, and procurement. Instrumentation
excludes sizing/selection, approved datasheet/loop generation, vendors, and
procurement. Control excludes PLC/DCS/SIS/ESD/HMI/SCADA code/configuration,
safety-logic decisions, autonomous logic approval, and deeper Control Systems
Intelligence. Cross-discipline reasoning remains PATCH-053; standards behavior
PATCH-054; all other PATCH-055..060 boundaries remain frozen.

## 23. Five-batch EDS boundary

| Batch | EDS responsibility | Explicit stop boundary |
|---|---|---|
| 1 — Shared Operational Release / Integration Preparation | source release structure, three descriptor/adapter identities, seven combinations, shared catalog/evaluation/provenance/API/readiness/conformance contracts; migration design only | cannot claim an operational vertical; no schema or vertical implementation |
| 2 — Electrical V1 + shared additive cutover | complete Electrical workflows/component plus separately authorized shared Object-type, origin, Identifier, Object-Context, and Report V2 cutover used by all packages | no calculations/tools/procurement; no migration without later exact authority |
| 3 — Instrumentation V1 | complete Instrumentation catalog, owner integrations, rules, component, and representative evidence reusing Batch-2 schema | no new domain store, sizing/selection/document generation |
| 4 — Control & Automation V1 | complete exact-legacy catalog, owner integrations, rules, component, and representative evidence | no code/config generation or autonomous logic authority |
| 5 — Combined Release / Conformance | all seven combinations, integrated navigation/effective state, full 46-vector/security/history/performance/accessibility/RTL/regression evidence | no cross-discipline reasoning or PATCH-053+ pull-forward |

Every batch later requires its own accepted IDS/Plan authority, exact file
manifest, independent review, and Human gate. No later-batch work is pulled
forward merely because shared contracts are defined here.

## 24. Traceability matrix

| EDS requirement | Architecture-052 | ADR/Core reuse | Batch | Future IDS/evidence obligation |
|---|---|---|---:|---|
| operational package/static trust | §§4–8,16–17 | ADR-024; EDS/IDS-051 | 1 | exact release/adapter assembly; no dynamic path tests |
| release/profile/seven combinations | §§5,12.1 | PATCH-051 Registry/compatibility | 1,5 | canonical digest and seven-vector parity |
| exact E/I/C Object catalogs | §§9–12.1 | existing EKG vocabulary | 2–4 | enum/catalog/owner mapping positive and negative |
| two additive Electrical types | §§9.1,19 | EKG owner | 2 | application/SQL CHECK/fresh+upgrade proof |
| exact Relationship tuples | §12.2, §14 | Relationship owner | 2–4 | endpoint/authorization/cross-Workspace matrix |
| Context/input declarations | §§12.1,15 | Context owner; ADR-015 activation | 2–4 | subject shape/coherence/history/partiality |
| selective Evidence readiness | §§12.1,15 | Evidence owner | 2–4 | every Deliverable row; no universal gate |
| Deliverable/review/issue gates | §§12.1,12.4,15 | Deliverable owner | 2–4 | same-revision Human review evidence |
| Identifier aggregate/cardinality | §§12.3,19,23 | ADR-025 | 2 | lifecycle, races, uniqueness, report snapshots |
| durable origin triple | §18 | ADR-024 provenance | 2–4 | immutability, coherence, no backfill, rebind history |
| derivable/Audit provenance | §§18.2,22 | PATCH-051 Audit | 1–5 | exact operation-time event fields/atomicity |
| configuration/standing | §§5,18,21,25 | EDS/IDS-051 | 1,5 | effective/historical/stale/drift cases |
| Object/Relationship workflow | §§13–14 | canonical owner services | 2–4 | atomic owner mutation and tenant negatives |
| Capture affordance boundary | §§13,15 | Capture owner | 2–4 | Capture alone never satisfies input |
| Report V2/Memory | §23 | Report/Memory owners; ADR-023 | 2 | V1/V2 Python/SQL/Memory golden parity |
| deterministic rules/bounds | §§12.4,16–17 | static adapter seam | 1–5 | schema/digest/order/timeout/resource cases |
| API/server authority | §§13,21,29 | PATCH-051 APIs | 1–5 | auth-first, forbidden-input, pagination tests |
| three frontend components | §24 | trusted empty component map | 2–5 | a11y/RTL/state/unknown-key evidence |
| readiness | §25 | PATCH-051 readiness | 1–5 | non-empty drift/schema/grant/conformance checks |
| 39+7 manifests | §12.5 | conformance primitive | 1–5 | exact structured fixtures and digest equality |
| persistence verdict/extensions | §19 | existing owner stores | 2 | separately authorized additive cutover |
| legacy/no-backfill migration | §19 | PATCH-051 migration rules | 2 | real PostgreSQL fresh/upgrade/recovery proof |
| Human/AI authority | §§13,16,23,30 | accepted owner/Human contracts | all | negative authority/AI-unavailable evidence |
| roadmap/firewalls | §§27–30 | Human-frozen roadmap | all | no PATCH-053+ symbols/behavior |

Every material A–T contract is represented. Omission of any row or its future
evidence is a blocking IDS/implementation review finding; this matrix is not an
implementation manifest.

## 25. EDS acceptance criteria and governance disposition

EDS-052 passes independent review only if it preserves accepted Architecture,
ADR-025, ADR-024, and PATCH-051; freezes exact catalogs/tuples/cardinality/
provenance/V2 orders/46 vectors/resource limits; defines truthful additive
persistence and no-backfill migration semantics; preserves authorization and
Human authority; and creates no IDS, Plan, source/test, migration, database, or
PATCH-053+ work.

The fresh independent review records **PASS** with Critical/Major/Minor `0/0/0`
and one inherited Observation (`IDS051-OBS-01`). No documentation-remediation
cycle was required. Under the explicit Human statement recorded in
`EDS-052-Electrical-Instrumentation-and-Control-Automation-Discipline-Packages-V1-Human-Acceptance.md`,
EDS-052 is now **ACCEPTED**. Acceptance changes governance status only and does
not authorize implementation, migration, staging, commit, push, or PATCH-053+.
This current governed sequence separately authorizes IDS-052 design.

```text
EDS-052: ACCEPTED
PATCH-052: REGISTERED / OPEN
IDS-052: AUTHORIZED FOR DESIGN
IMPLEMENTATION: NOT AUTHORIZED
```
