# Architecture-051 — Shared Multi-Discipline Core & Discipline Package Contract

## 1. Document control and authority

| Field | Value |
|---|---|
| PATCH | PATCH-051 — Shared Multi-Discipline Core & Discipline Package Contract |
| Mode | Architecture complete; Human Architecture Acceptance governance reconciliation |
| Preparation/remediation authority | HUMAN PATCH-051 ARCHITECTURE DISCOVERY / DESIGN and focused remediation authority: GRANTED |
| Status | ACCEPTED / COMPLETE |
| Original independent review | FAIL / STOPPED / historical evidence preserved |
| Focused independent re-review | PASS / ACCEPTED; `A051-MAJ-01` RESOLVED / CLOSED |
| ADR-024 | ACCEPTED |
| Human Architecture acceptance | PASS / GRANTED |
| EDS-051 | NOT STARTED / ELIGIBLE FOR SEPARATE HUMAN DESIGN AUTHORITY |
| IDS-051 | NOT STARTED |
| Implementation | NOT AUTHORIZED |
| Migration | NOT AUTHORIZED |
| PATCH-052 | NOT STARTED |
| Commercial V1 roadmap | HUMAN-FROZEN / UNCHANGED |

This artifact defines Architecture only. It creates no executable package,
production behavior, database change, test change, entitlement enforcement or
later-stage authority.

The focused amendment reconciles only Project package-configuration
cardinality, Workspace binding states and their legacy transition rules. Its
focused independent re-review and subsequent Human Architecture Acceptance are
PASS. Acceptance does not authorize EDS, IDS, implementation, migration or
PATCH-052.

## 2. Architecture Discovery verdict

**PASS — A coherent trusted Discipline Package architecture is feasible, but
PATCH-051 will require later persistence, API and compatibility work.**

The repository has a strong reusable Core: Organization, Customer, Project,
single-discipline Workspace, Engineering Context, Engineering Objects,
Relationships, Interface Commitments, Evidence, Technical Reports,
Organizational Memory, Project Context, Completeness, Guidance, Audit and
authorization. The missing boundary is one stable package identity and
configuration contract.

Current discipline meaning is fragmented across two closed enums, database
CHECK constraints, explicit compatibility maps, free-text fields, historical
JSON snapshots and frontend literals. The fragments are reconcilable because
the accepted owners and scopes are explicit. They are not interchangeable and
must not be normalized by string replacement alone.

The independent review identified one blocking contradiction in the original
configuration cardinality. Sections 18 through 25 now distinguish a valid
unconfigured Project from configured Projects and distinguish package-backed
Workspaces from truthful future-unavailable and unresolved states.

## 3. Sources and discovery method

Discovery inspected the current repository and accepted governance, including:

- `backend/app/enums/discipline.py` and
  `backend/app/enums/engineering_knowledge.py`;
- Workspace, Context, Context Relationship, Engineering Object, Capture,
  Deliverable, Report, Memory and Audit models, schemas, services and ports;
- Alembic revisions `a20c1e0201f0`, `c2021f0c0a01`, `b2022c0202f2`,
  `e02400000001`, `e02800000001`, `e03200000001` and `e04600000001`;
- Project Context, Completeness and Guidance integration surfaces;
- frontend API types, Project/Workspace creation, filters, navigation and
  tests;
- operational configuration and release artifacts;
- ADR-014, ADR-015, both ADR-017 records, ADR-016, ADR-020, ADR-021,
  EngineeringObject Blueprint v1.0 and the accepted PATCH-023 compatibility
  review.

This is a repository inventory, not a live customer-database census. EDS must
require a read-only preflight over every deployed database before any migration
manifest can be accepted.

## 4. Repository Discipline identity inventory

| Representation | Current values / shape | Persistence | Exposure | Current meaning |
|---|---|---|---|---|
| Workspace `Discipline` enum | `electrical`, `instrumentation`, `control`, `mechanical`, `civil`, `process` | `engineering_workspaces.discipline`; CHECK and unique `(project_id, discipline)` | Workspace API, OpenAPI, search, frontend | Operational Workspace classification |
| `EngineeringDiscipline` enum | `instrumentation`, `electrical`, `industrial_automation`, `shared_engineering` | Engineering Objects; Capture snapshots; accepted Report provenance JSON | Engineering Object APIs and Report source contracts | EKG professional-domain classification |
| Engineering Object family | `instrumentation`, `electrical`, `automation`, `shared` | `engineering_objects.family`; CHECK | Engineering Object and EKG APIs | Object taxonomy family, not Discipline identity |
| Workspace/Object compatibility | `instrumentation→instrumentation`, `electrical→electrical`, `industrial_automation→control`; shared rejected | Code-owned maps in Object/Capture adapters | Application behavior | Explicit bridge between the two enums |
| Context discipline subject | Workspace `Discipline` values at service boundary | `engineering_context_subject_references.discipline`; DB checks only non-null by kind | Context responses | Discipline-scoped Context subject |
| Context Relationship discipline endpoint | non-empty free text, length bounded by column | `source_discipline` / `target_discipline` | Relationship responses | Historical discipline selector with no controlled vocabulary |
| Capture discipline | translated Workspace value; only E/I/control map | `engineering_experience_captures.discipline` | Capture, Journal, AI and Report-source APIs | Denormalized EKG-compatible scope snapshot |
| Deliverable discipline | arbitrary non-empty text up to 80 characters | `engineering_deliverables.discipline` | Deliverable API/frontend | Human-entered classification label, not proven package identity |
| Technical Report Capture basis | nullable `EngineeringDiscipline` | accepted JSONB snapshot with schema/check validation | Report provenance | Immutable historical Capture classification |
| Technical Report Object basis | required `EngineeringDiscipline` | accepted JSONB snapshot with schema/check validation | Report provenance | Immutable historical Object classification |
| Organizational Memory | no direct discipline field; retains accepted Report projection and provenance | immutable Memory projection/manifest | Memory APIs | Inherits accepted Report scope and historical source meaning |
| Evidence / Supporting File | Organization/Project/Workspace scope; no discipline field | canonical Evidence/file records | Evidence/file APIs | Scope derives through authorized Workspace when present |
| Project Context | discipline is a bounded string in several projections | request-time only | Project Context/frontend | Pass-through of owning capability meaning |
| Engineering Journal | nullable string filters/projections | no independent discipline source of truth | Journal APIs | Presentation over canonical Capture/other sources |
| Guidance material category | `instrumentation_measurement`, `electrical_power_or_interconnection`, `automation_and_control` | request-time derived; no Guidance persistence | Guidance API/frontend | Advisory material category, not Discipline or Package identity |
| Audit | discipline sometimes appears inside generic JSON `details` | `audit_logs.details` | admin Audit API | Historical event metadata, not canonical identity |
| Frontend Workspace selection | hard-coded E/I/mechanical/civil/process; omits `control` | frontend source only | Project page | Incomplete presentation of backend Workspace enum |
| Frontend types | most `discipline` fields are plain `string` | none | TypeScript contracts | Does not preserve controlled identity |
| Operations/configuration | no Discipline Package registry or package configuration | none | none | Capability absent |

## 5. Legacy identity conflict map

| Existing identity | Classification | Semantic disposition | Canonical mapping / treatment |
|---|---|---|---|
| `electrical` | persisted, API-visible, canonical in both vocabularies | Electrical professional domain | `DisciplineId=electrical`; Package `electrical` when configured |
| `instrumentation` | persisted, API-visible, canonical in both vocabularies | Instrumentation professional domain | `DisciplineId=instrumentation`; Package `instrumentation` when configured |
| `control` | persisted Workspace value and frontend/test value | Operational Control Workspace | legacy alias to `DisciplineId=control_automation`; raw historical value retained |
| `industrial_automation` | persisted Object/Capture/Report value and API enum | Existing EKG name for the Control & Automation domain | legacy alias to `DisciplineId=control_automation`; old APIs and snapshots retain it |
| `automation` | persisted Engineering Object/Relationship family | Taxonomy/relationship family, not a Discipline | retained as family key; declared by Control & Automation package; never globally renamed as a discipline |
| `automation_and_control` | Guidance material category | Advisory material grouping | retained as category; package declaration attributes it to `control_automation` |
| `shared_engineering` | persisted EKG discipline and Report snapshot value | Core-owned cross-discipline classification | reserved Core `DisciplineId=shared_engineering`; no commercial package and no automatic Workspace creation |
| `shared` | persisted Engineering Object family | Core/shared taxonomy family | retained as family; not a package alias |
| `mechanical` | persisted/accepted Workspace identity; future package placeholder | Valid existing discipline, not Commercial V1 operational package | canonical `DisciplineId=mechanical`; package unavailable until future governance |
| `civil` | persisted/accepted Workspace identity; future package placeholder | Existing Civil discipline identity | canonical `DisciplineId=civil`; future display/package scope may say Civil / Structural only through later governance |
| `process` | persisted/accepted Workspace identity; future package placeholder | Valid existing discipline, not Commercial V1 operational package | canonical `DisciplineId=process`; package unavailable until future governance |
| free-text Context Relationship discipline | persisted historical selector | Meaning may be valid, misspelled or customer-specific | exact accepted aliases map; all other values remain `legacy_unresolved` and require Human reconciliation |
| free-text Deliverable discipline | persisted Human label | Classification label may not equal Workspace or package | never bulk-reinterpreted; workspace-linked records may gain a separate canonical binding; ambiguous records require Human action |

No alias changes the stored meaning of an accepted historical record. A
canonical interpretation is additional governed metadata with provenance, not
a destructive rewrite.

## 6. Current persistence constraints

1. `engineering_workspaces.discipline` is `VARCHAR(32)`, constrained to six
   values and permanently unique with Project.
2. `engineering_objects.family`, `discipline` and `object_type` are each
   constrained, and family–discipline and family–type combinations are hard
   coded in application and database constraints.
3. `engineering_experience_captures.discipline` is a nullable denormalized
   string. Application mapping supports only Electrical, Instrumentation and
   Control Workspaces.
4. Context subject discipline is persisted but only the service enforces the
   Workspace enum; the database enforces shape, not vocabulary.
5. Context Relationship discipline endpoints are persisted free text.
6. Deliverable discipline is persisted free text with only a length constraint.
7. accepted Report JSON constraints explicitly recognize the four existing
   `EngineeringDiscipline` values. Accepted snapshots and their digests are
   immutable authority evidence.
8. Organization and Project have no package-configuration relationship.
9. Workspace has no package key or package-version binding.
10. Audit has no typed package identity; its generic JSON details already
    preserve historical Workspace discipline in some events.

These constraints make later migrations necessary. They do not justify
altering existing revisions or records.

## 7. Current API and frontend constraints

- Workspace create/list/filter APIs expose the six-value Workspace enum.
- Engineering Object create/filter/reclassify APIs expose the separate
  four-value `EngineeringDiscipline` enum.
- Capture returns the translated EKG value, not the Workspace value.
- Context Relationship accepts arbitrary discipline text.
- Deliverable creation accepts arbitrary discipline text.
- Project Context passes several discipline strings through without one common
  type.
- Journal filters use nullable strings.
- frontend types reduce controlled backend identities to `string`.
- Project Workspace creation hard-codes five values and omits Control despite
  backend support.
- frontend labels render raw values in several places.
- no authenticated effective-package query exists for navigation or creation.

Existing V1 clients therefore require a compatibility period. Old fields must
not silently return a different string such as replacing `control` with
`control_automation` or `industrial_automation` in place.

## 8. Core architecture assessment

The correct architecture is a **trusted modular package kernel**, not a generic
plugin framework and not three hard-coded product branches. Core continues to
own identity types, package registry contracts, configuration resolution,
authorization composition, conformance, resource bounds and common
integration ports. Packages own bounded declarations and SATCO-reviewed domain
implementations.

Existing canonical capabilities retain their data and lifecycle ownership.
Packages contribute through their public application contracts and may not
import foreign repositories, sessions, routers or persistence models as a
shortcut.

## 9. Definition of Discipline

A **Discipline** is a stable, governed professional-engineering classification
used to scope responsibility, Workspace identity and engineering meaning. It
is not a commercial SKU, installed software component, authorization grant,
Human role, taxonomy family or entitlement.

`DisciplineId` is a typed Core-owned identifier. Initial reconciled identifiers
are:

- `electrical`;
- `instrumentation`;
- `control_automation`;
- `mechanical`;
- `civil`;
- `process`; and
- reserved Core classification `shared_engineering`.

Only the first three have commercially operational V1 packages planned in
PATCH-052. Piping and HSE / Process Safety demonstrate future extensibility but
receive no identifier or operational standing until separately governed.

## 10. Definition of Discipline Package

A **Discipline Package** is a trusted, versioned SATCO capability bundle that
declares and implements bounded engineering contributions for one primary
Discipline under the Core package contract. It is a product/capability concept,
not a Workspace, tenant configuration row, runtime engineering record, Python
plugin, database schema fork or entitlement token.

The PATCH-052 package keys are fixed for architectural interoperability:

- `electrical`;
- `instrumentation`;
- `control_automation`.

Each declares its `primary_discipline_id`. A future separately governed
package may contribute shared or cross-discipline behavior, but cannot change
the meaning of an existing Discipline or Package key.

## 11. Discipline-versus-Package identity decision

Discipline and Package identity are **separate typed namespaces**, even when
their initial string values match.

This separation is mandatory because:

- a valid Discipline can exist without an installed/enabled package;
- a package is versioned while a Discipline identity is stable;
- package availability and commercial entitlement must not redefine
  engineering meaning;
- `shared_engineering` is a Core classification without a commercial package;
- future governed packages may span or support more than one Discipline.

Code must not compare an untyped string to infer equality across the two
namespaces. The Package descriptor explicitly declares the mapping.

## 12. Canonical identity model

Core owns distinct immutable value types:

| Type | Example | Rule |
|---|---|---|
| `DisciplineId` | `control_automation` | stable engineering meaning; never versioned |
| `PackageKey` | `control_automation` | stable capability identity; typed separately |
| `PackageVersion` | `1.0.0` | immutable semantic version of declarations/behavior |
| `CoreContractVersion` | `1` | version of the Core-owned package contract |
| `RegistryDigest` | SHA-256 | deterministic identity of the trusted registry set |
| `DescriptorDigest` | SHA-256 | deterministic identity of one package descriptor/version |
| `EntitlementKey` | `discipline.control_automation` | stable future PATCH-059 attachment key |
| `CompatibilityProfileId` | governed identifier | identity for an explicitly supported package combination |

Machine identifiers use lowercase ASCII controlled values, are never display
labels and are never customer-editable. Display names and localization are
trusted metadata and can change without changing identity.

## 13. Package version model

`PackageVersion` uses `MAJOR.MINOR.PATCH` semantics:

- MAJOR may require explicit data/config migration and cannot be selected by a
  Project without a governed compatibility/upgrade path;
- MINOR may add backward-compatible declarations/capabilities;
- PATCH may correct behavior without changing declared semantic meaning or
  persisted contract shape.

The registry records compatibility rather than assuming SemVer alone proves
it. Projects pin an exact package version. There is no implicit “latest”
upgrade. A package version change requires authorized preflight, compatibility
validation, explicit Human action, Audit and rollback evidence.

Historical engineering records remain readable with the descriptor/version
under which their package-dependent meaning was created. Accepted Reports,
Memory, Audit and provenance never inherit a new meaning merely because a
package is upgraded.

## 14. Trusted Package Registry architecture

The authoritative Package Registry is immutable, source-controlled,
version-controlled and release-bound. It consists of Core-validated package
descriptors and explicit SATCO-owned adapter registrations. Deterministic
ordering and canonical serialization produce descriptor and registry digests.

The database may contain a read-only **installed registry projection** with
package key, version, contract version and digests for referential integrity,
configuration and historical readability. That projection is derived from the
trusted release and is not a customer-editable package registry. Startup and
readiness fail closed if code registry, release manifest and installed
projection disagree.

Every release retains the historical descriptors required to read supported
pinned and historical data. Runtime discovery from directories, Python entry
points, environment-provided module names, database code, uploaded files or
network registries is prohibited.

## 15. Core-owned contract

Core owns:

- all identity/version/digest value types;
- descriptor schema and validation;
- registry assembly and deterministic digest;
- configuration hierarchy and effective-package resolution;
- compatibility evaluation;
- authorization-before-disclosure composition;
- closed contribution categories and their ports;
- stable integration contracts to Context, Objects, Relationships, Evidence,
  Reports, Memory, Guidance, Audit and frontend metadata;
- resource-limit categories and enforcement;
- conformance harness and result contract;
- safe failure states;
- legacy alias classification and translation rules; and
- the future entitlement-decision seam.

Core does not own discipline-specific engineering rules or operational
taxonomy content.

## 16. Package-owned declaration contract

One immutable descriptor version may declare, where applicable:

- package key, primary Discipline, display identity and version;
- supported Core contract range and descriptor digest;
- taxonomy families and stable Engineering Object types;
- relationship families/types and compatibility constraints;
- Context contribution declarations;
- required/optional input declarations;
- deliverable declarations;
- Evidence requirement declarations;
- deterministic rule identifiers and bounded hook registrations;
- standards-applicability hook identifiers;
- cross-discipline interface/dependency declarations;
- Human role requirements and explicit authority limitations;
- operation-level authorization requirements;
- trusted frontend route/capability/component keys;
- resource-limit requests within Core maxima;
- migration/read/backward-compatibility declarations;
- entitlement key; and
- conformance evidence identity.

Declarations are data and references to precompiled, explicitly registered
SATCO-owned adapters. They cannot contain executable source, SQL, templates
that execute code, component URLs or arbitrary import paths.

## 17. Configuration and runtime-data separation

The architecture keeps five models distinct:

| Model | Owner | Mutability / authority |
|---|---|---|
| Core package contract | Core source/release | changed only through governed Core version |
| Package declarations | trusted package source/release | immutable per PackageVersion |
| Organization/Project/Workspace configuration | canonical persisted configuration | explicit authorized Human/configuration operations |
| Runtime engineering data | existing canonical capability owners/package domains | governed domain lifecycles |
| Commercial entitlement state | future PATCH-059 | signed commercial authorization decision |

No descriptor row is runtime engineering data. No engineering record enables a
package. No configuration row grants access to protected data. No entitlement
owns engineering meaning.

## 18. Configuration hierarchy

```text
Platform-supported package versions (trusted release registry)
    ↓ subset and compatible
Organization-configured packages (administrative product configuration)
    ↓ optional until a package-dependent transition
Project NOT_CONFIGURED, or CONFIGURED with exact package versions + profile
    ↓ for package-backed Workspace creation/execution only
Workspace binding state and package applicability (single Discipline)
    ↓ after independent authorization
Authorized package capability and engineering data
```

Project existence and future-unavailable Workspace existence do not imply an
effective package. An effective package exists only when every required layer
succeeds for a package-dependent operation. A failure is unavailable/
unsupported, never authorization.

## 19. Organization configuration model

An Organization configuration records the package keys/versions the
Organization administrator has configured for engineering use, their state,
version, rationale, actor and Audit history. It is a subset of the
deployment-supported registry.

This is architectural product configuration, not final commercial activation.
Disabling a package prevents new package-dependent mutations and new Project
selection but preserves authorized historical read/export. Organization
configuration is disclosed only after Organization administration
authorization; cross-tenant package configuration is never enumerable.

## 20. Project configuration model

A Project has one of two explicit package-configuration states:

- **`NOT_CONFIGURED`:** zero selected Discipline Packages and no compatibility
  profile. This is valid for a newly created or otherwise empty Project,
  including a Project with zero Workspaces. It is also valid when a Project
  contains only future-unavailable or unresolved Workspaces that cannot imply
  a package selection. Project existence never fabricates package
  configuration.
- **`CONFIGURED`:** one or more compatible Organization-configured packages,
  with each exact `PackageVersion` pinned by the Project and with an applicable
  compatibility profile and selected-configuration provenance.

The repository workflow creates a Project independently before Workspace
creation. Configuration therefore becomes mandatory at the package-dependent
transition, not at Project creation. Creating an Electrical, Instrumentation
or Control & Automation operational Workspace requires the Project already to
be `CONFIGURED` with the exact compatible package for that Discipline.
Executing any package-owned contribution likewise requires the applicable
Project selection. A Project may be configured before that transition, but an
empty Project is not required to be configured.

The Project is the sole package-version selection authority. Release-wide
registry identity may be retained as drift evidence, while reproducibility is
based on the selected descriptor set and compatibility-profile provenance;
exact digest fields and canonical bytes remain EDS work.

Configuration change requires an active authorized Project, Human rationale,
optimistic concurrency, package compatibility validation, impact/preflight and
Audit. Removal or upgrade cannot orphan an active Workspace or make historical
engineering unreadable. The Project remains the aggregation boundary for
multiple discipline Workspaces and later cross-discipline behavior.

## 21. Workspace model

The accepted ADR-014 invariant remains: one immutable Workspace identity per
Project and Discipline, with no nested Workspaces. PATCH-051 does not convert a
Workspace into a multi-package container.

Every exactly recognized Workspace retains exactly one canonical Discipline;
an unresolved legacy Workspace retains its raw identity until Human
reconciliation. Its package compatibility/binding state is exactly one of:

- **`OPERATIONAL_PACKAGE_BOUND`:** an Electrical, Instrumentation or Control &
  Automation Workspace whose operational package is supported and selected by
  its Project. Its package key and exact version are inherited from the
  Project configuration. The Workspace cannot select, override or upgrade a
  version independently.
- **`FUTURE_UNAVAILABLE_UNBOUND`:** a recognized canonical Discipline for
  which no operational package is available, including Mechanical, Civil and
  Process under the current roadmap. The Workspace has no fabricated
  `PackageKey`, remains historically/Core-readable and authorization-safe, and
  cannot execute package-owned operational capabilities.
- **`LEGACY_UNRESOLVED`:** a legacy Workspace identity for which exact
  canonical mapping is impossible. Its raw identity remains readable under
  existing authorization, it has no fabricated package binding, and new
  package-dependent mutation fails closed pending Human reconciliation.

These are architecture terms; exact enum, schema and transition names belong
to EDS. Workspace binding/configuration history may persist the effective
Project pin as derived provenance without becoming a second version authority.
Project-wide and Core shared engineering remain outside a fabricated shared
Workspace.

Cross-discipline intelligence later operates at Project level across separately
authorized Workspace projections and declared interfaces. This preserves
source/consumer accountability and avoids unioning Workspace permissions.

## 22. Runtime engineering data separation

Runtime facts stay with their accepted owner. Where package-dependent meaning
is material, new records carry only stable package key/version and declaration
or rule identity needed for provenance. They do not copy the whole descriptor.

Packages may own new discipline-specific aggregates in later PATCHes, but
those aggregates use shared Organization/Project/Workspace identity,
authorization, Evidence, Audit and integration ports. A package must not create
a parallel Project, Workspace, Context, Evidence, Report, Memory or EKG Core.

## 23. Package compatibility model

Compatibility is an explicit deterministic registry decision over:

- each PackageVersion's Core contract range;
- declared dependencies and conflicts;
- supported pairwise/multi-package combinations;
- taxonomy and relationship-key collisions;
- configuration and data migration prerequisites;
- read/write compatibility; and
- resource budgets.

Commercial V1 defines explicit profiles for each E/I/C package alone, each
Human-approved combination and integrated E/I/C. A combination is a normalized
set plus profile/digest, not a new implicit “super package.” Unknown
combinations fail closed. Registry load and every configuration mutation rerun
the same pure compatibility evaluation.

Configuration cardinality is part of compatibility evaluation. Project
`NOT_CONFIGURED` and Workspace `FUTURE_UNAVAILABLE_UNBOUND` are valid states,
not compatibility errors, but neither authorizes or enables package
contributions. `LEGACY_UNRESOLVED` remains historically readable and fails
closed for new package-dependent mutation. Only `OPERATIONAL_PACKAGE_BOUND`
may execute package-owned capabilities, subject to every independent
authorization, support, configuration and future-entitlement predicate.

## 24. Legacy mapping strategy

Core owns a versioned `LegacyDisciplineMap` whose entries declare source
contract, raw identity, intended canonical Discipline, confidence class and
write/read policy. Exact accepted mappings are deterministic; free text is not
normalized by case folding, substring matching or similarity.

Mapping classes are:

- `exact_canonical`;
- `exact_legacy_alias`;
- `future_unavailable_discipline`;
- `core_shared_classification`; and
- `legacy_unresolved`.

Old APIs continue to read/write their accepted legacy vocabulary during the
governed compatibility period through boundary translators. New Core/package
contracts use canonical IDs. Alias telemetry contains only safe counts and
contract identifiers, never cross-tenant data or protected text.

Future legacy writes are state-aware. Creation of an E/I/C operational
Workspace through either a canonical or legacy contract must resolve by the
exact source-contract mapping and requires the compatible Project-selected
package/version. A legacy alias cannot bypass that gate or create an
independent Workspace version choice. A recognized future-unavailable
Discipline may remain representable as `FUTURE_UNAVAILABLE_UNBOUND` under the
existing Workspace lifecycle, without a package key or package capability.
Writers must not create new ambiguous aliases; unknown free text cannot create
a canonical Workspace or package binding.

## 25. Migration architecture

Later implementation requires an additive, measured sequence:

1. **Preflight:** inventory every value, constraint, accepted snapshot,
   foreign-key relationship and deployed row count; stop on unknown meaning.
2. **Add:** create trusted registry projection and Organization/Project/package
   configuration persistence; add canonical shadow/binding fields and history
   without dropping legacy fields.
3. **Backfill:** apply only exact governed mappings. Only exact recognized
   E/I/C identities may receive a canonical package binding, and only through
   the compatible exact Project pin established by the controlled migration.
   Mechanical, Civil, Process and other recognized future-unavailable
   Disciplines remain explicitly unbound. Unknown free-text identities remain
   `legacy_unresolved`. Retain raw values; perform no similarity matching,
   fabricated `PackageKey` assignment or global semantic replacement.
4. **Dual contracts:** dual-read and bounded dual-write canonical metadata
   while old APIs preserve their original values.
5. **Validate:** prove referential, tenant, package-combination, snapshot,
   Audit and rollback invariants before tightening constraints.
6. **Cut over:** make canonical package-aware contracts authoritative for new
   operations; keep historical compatibility readers.
7. **Retire writes only:** any removal of legacy write paths or columns is a
   separately reviewed later step. Accepted historical payloads are never
   rewritten merely to simplify storage.

Exact tables, columns, migrations and batch boundaries belong to EDS/IDS and
later implementation authority.

## 26. Rollback and historical compatibility

- Migrations must be additive until the previous application version can read
  and operate safely.
- A pre-cutover rollback restores prior writers without discarding canonical
  shadow data.
- Post-cutover downgrade is allowed only when registry and data preflight prove
  the target release can read all configured package/data versions.
- Package-version rollback is explicit, compatibility-declared and audited; it
  is never a string change.
- Accepted Report snapshots/digests and Memory projections/manifests are
  immutable.
- Historical Audit JSON and raw legacy discipline strings remain unchanged.
- Disabled/expired/future-unavailable packages preserve authorized historical
  read/export.
- Unknown mappings fail closed for new mutation but remain readable with an
  honest legacy/unresolved presentation.

## 27. Package conformance model

Every package version must pass the Core harness for:

1. descriptor schema, canonical serialization and digest vectors;
2. key/version uniqueness and immutable primary Discipline;
3. Core contract compatibility;
4. taxonomy and relationship collision safety;
5. finite contribution declarations and resource limits;
6. deterministic rule purity, ordering and bounded results;
7. Organization/Project/Workspace configuration invariants;
8. authorization-before-disclosure and tenant-negative cases;
9. safe Evidence/Report/Memory/Guidance integration;
10. compatible package combinations;
11. upgrade, downgrade/read and migration declarations;
12. Audit minimization and stable identity;
13. truthful frontend metadata; and
14. prohibited dynamic execution/import behavior.

PATCH-051 implementation may use a non-operational test-only reference package
fixture to prove Core conformance. PATCH-052 must make each E/I/C package and
every supported combination pass the same harness. A conformance PASS does not
grant engineering or implementation authority.

## 28. Authorization model

For a package-dependent operation, the following predicates are separate and
ordered:

1. actor is authenticated in one active Organization;
2. actor is authorized for the requested Project/Workspace/operation;
3. package exists in the trusted deployment registry;
4. package is configured for the Organization;
5. the Project is `CONFIGURED` and the exact package/version is selected and
   compatible;
6. the Workspace is `OPERATIONAL_PACKAGE_BOUND` to that inherited Project pin,
   or the package applies to the authorized Project-level operation;
7. future entitlement decision permits commercial use; and
8. owning capability authorizes each underlying engineering fact.

Passing predicates 3–7 never grants predicate 2 or 8. Data authorization is
performed before payload disclosure and before package-specific counts,
versions or configuration are revealed. A package cannot extend RBAC by
declaration; it references Core-recognized operation requirements.

Core-authorized historical reads of `FUTURE_UNAVAILABLE_UNBOUND` and
`LEGACY_UNRESOLVED` Workspaces do not pretend to pass package predicates.
Their absence of a package binding neither grants access nor makes an
otherwise authorized historical record unreadable.

## 29. Security and non-disclosure model

- Tenant scope is server-derived; Organization IDs are not accepted as
  package-selection authority.
- Project and Workspace configuration queries use protected/not-found
  minimization.
- Cross-tenant package sets, versions, counts, failures and compatibility
  details are not disclosed.
- Registry metadata exposed to ordinary users is limited to authorized
  effective capabilities and safe display metadata.
- Configuration state cannot be used to enumerate inaccessible Projects,
  Workspaces, Evidence, Reports or Memory.
- Package contributions receive typed authorized projections, never foreign
  repositories or raw sessions.
- Hidden or truncated inputs cannot be inferred as absent by a package rule.
- Package/version keys are untrusted request data until parsed, bounded and
  resolved inside authorized scope.
- Internal registry mismatch, entitlement state and adapter failures map to
  safe unavailable/protected outcomes without implementation details.

## 30. Audit identity model

New package/configuration Audit events use stable `package_key`, exact
`package_version`, selected descriptor/profile provenance, release-wide
registry digest where relevant as drift evidence, configuration version, safe
scope selectors, actor, action, outcome and rationale where required. These
digest roles remain distinct. Package rule events may record stable rule/
declaration identity and digest, not raw protected inputs or full descriptors.

Historical Audit details retain their raw `control` or other legacy values.
Readers may add an explicitly labelled canonical interpretation but cannot
rewrite stored history. Audit listings remain authorization-minimized; failed
cross-tenant requests never reveal package configuration.

EDS must establish a durable transactional Organization-scoped write/read
boundary for package-configuration Audit. The current generic Audit listing
must not be reused unchanged as that boundary merely because Organization
identity could be placed inside untyped details.

## 31. Context integration

Context remains owned by its accepted capability. New package-aware Context
contracts use canonical Discipline and optional package provenance. Existing
Workspace and discipline subjects remain readable through the legacy map.
Free-text Context Relationship endpoints are reconciled only by exact mappings
or Human action.

Packages declare bounded Context contribution kinds and consume authorized
Context through public ports. They cannot mutate Context directly, invent a
source authority or treat package configuration as Context truth.

## 32. Engineering Object integration

Engineering Object identity/lifecycle/authority remain Core EKG concerns.
Packages declare governed families, types and their primary Discipline
compatibility. Existing `automation` family and `industrial_automation`
classification retain historical/API meaning while their canonical package
provenance is Control & Automation.

The hard-coded family/type/discipline CHECKs require later safe evolution to a
trusted catalog/projection model or equivalently strong governed integrity.
No package may invent arbitrary object types at runtime. `shared_engineering`
remains Core-controlled and cannot bypass the single-Workspace authorization
decision.

## 33. Relationship and Interface integration

The existing Relationship engines own edge identity, lifecycle, authority and
authorization. Packages may declare supported relationship meanings/types and
cross-discipline interface roles through closed keys. They cannot create
unbounded vocabularies or bypass endpoint authorization.

Interface Commitments remain Human-governed dependencies. Package declarations
may describe provider/consumer expectations but cannot acknowledge, fulfill,
reject or supersede a commitment. Later PATCH-053 may consume these declared
seams without changing Core ownership.

## 34. Evidence integration

Evidence and Supporting Files retain their accepted Organization/Project/
Workspace ownership and authorization. A package may declare required Evidence
kinds, standing, sufficiency expectations and eligible attachment points. It
cannot declare Evidence authoritative, read inaccessible files or create a
parallel evidence store.

Package-dependent outputs reference canonical safe Evidence handles only after
owner authorization. Absence, protected state and insufficiency remain
distinct.

## 35. Technical Report integration

New Report provenance schemas may record package key/version, descriptor/rule
identity and canonical Discipline where material. Existing accepted Capture and
Object basis schema V1 values remain valid and immutable. Report acceptance
continues to be an explicit Human operation; package configuration or upgrade
cannot revise an accepted Report.

Loss of current package availability must not erase authorized historical
Report read/export or its exact legacy basis.

## 36. Organizational Memory integration

Memory continues to admit only accepted Report material through its governed
Human boundary. It preserves the accepted projection, manifest and source
digests. New package provenance may enter only through an accepted Report
snapshot contract; a package cannot write directly to Memory.

Package upgrade, disablement or entitlement change never reinterprets admitted
Memory. Current reuse may be limited when required capability or authorization
is unavailable, while historical meaning remains visible.

## 37. Guidance integration

PATCH-050's deterministic catalog, safe Evidence and Human-advisory boundaries
remain valid. A package may later register finite deterministic rule
contributions through a Core-owned pure evaluation port with stable rule ID,
version, applicability, inputs, outputs, bounds and provenance.

`automation_and_control` remains a Guidance material category, not a package
key. Package rules cannot create authoritative BOMs, alter source facts, call
AI autonomously or start loops. AI enhancement stays separately requested and
subordinate to deterministic results.

## 38. Standards hook seam

A package may declare stable standards-applicability hook identifiers,
applicability input types and expected citation-purpose categories. The hook is
only a future integration seam.

PATCH-051 does not create a standards registry, retrieve content, select an
edition, store clauses, validate citations or approve compliance. Those remain
PATCH-054.

## 39. Cross-discipline seam

Packages may declare typed interface roles, dependency meanings, consistency
input/output contracts, change-impact relationship kinds and Evidence/Guidance
linkage. The Project compatibility profile provides the package-set identity.

PATCH-051 performs no cross-package traversal or reasoning. PATCH-053 must
authorize each source/target independently, use bounded explicit relationships
and preserve conflicts for Human resolution.

## 40. Frontend Package contract

Core exposes an authenticated effective-capability projection after scope
authorization. Safe metadata includes canonical package key, display label,
version, capability keys and trusted navigation/contribution keys applicable
to that scope.

Frontend contributions select only precompiled, source-reviewed routes and
components from a closed Core registry. Database/customer configuration cannot
supply component code, URLs, import paths, HTML or scripts.

Project/Workspace creation must derive E/I/C operational options from
authorized effective Project configuration instead of hard-coded literals.
Recognized future-unavailable Disciplines remain representable without being
presented as package-backed choices. Legacy Workspaces show their historical
identity plus safe canonical label/compatibility state. Hidden or disabled
packages do not produce revealing counts. PATCH-057 retains full Commercial
Product Experience responsibility.

## 41. Resource-bound model

Core defines finite maxima for:

- packages and retained versions per release;
- Organization and Project package selections;
- descriptor size and metadata lengths;
- declarations per contribution category;
- object/relationship/input/deliverable/Evidence/rule/interface hooks;
- frontend contribution keys;
- compatibility profiles and dependency depth;
- result items, pages and continuation state; and
- package evaluation time/call budgets.

EDS fixes numeric values from evidence. Registry construction, configuration
mutation and request execution fail closed when bounds are exceeded. Package
rules cannot recurse, start autonomous loops, cause unbounded cross-package
traversal or infer hidden totals.

## 42. Arbitrary plugin prevention

Explicitly prohibited are:

- customer or tenant executable plugins;
- `importlib`/entry-point/directory discovery driven by runtime data;
- uploaded Python, JavaScript, WebAssembly or native binaries;
- arbitrary scripts, shell commands or SQL;
- database-stored executable expressions;
- customer-provided frontend bundles/components;
- remote package registries or runtime code download; and
- descriptors that name arbitrary executable symbols.

Safe extensibility is source-reviewed SATCO code plus immutable declarative
descriptors, explicit composition-root registration, closed ports, migration
review, release provenance and conformance evidence. A new package extends
governed catalogs and adapters without forking Core.

## 43. Human authority preservation

A package cannot independently:

- approve engineering or professional design;
- accept or revise Technical Reports;
- admit or mutate accepted Organizational Memory;
- approve Evidence standing;
- procure, purchase or select vendors;
- create an authoritative BOM/MTO/BOQ;
- change a Human Decision or Interface Commitment standing; or
- resolve cross-discipline conflicts autonomously.

Package outputs declare their authority class. Advisory or derived output may
enter an authoritative workflow only through that workflow's existing explicit
Human operation.

## 44. PATCH-052 readiness

PATCH-052 can instantiate the same contract three times:

| Package | Primary Discipline | Existing legacy sources retained | Package-owned future content |
|---|---|---|---|
| Electrical | `electrical` | Workspace/Object `electrical` | Electrical taxonomy, inputs, deliverables, Evidence and deterministic rules |
| Instrumentation | `instrumentation` | Workspace/Object `instrumentation` | Instrument taxonomy, inputs, deliverables, Evidence and deterministic rules |
| Control & Automation | `control_automation` | Workspace `control`; Object/Capture/Report `industrial_automation`; family `automation`; Guidance category `automation_and_control` | Control/automation taxonomy, inputs, deliverables, Evidence and deterministic rules |

Each package and every supported combination uses one registry, configuration,
authorization, conformance and frontend contract. PATCH-052 need not redesign
Core and must not duplicate it.

## 45. PATCH-059 compatibility

Each descriptor exposes one stable `EntitlementKey`. Effective-package
resolution contains a Core-owned `EntitlementDecisionPort` whose current
PATCH-051 implementation boundary is a non-commercial configuration decision.

PATCH-059 may later supply signed, rollback-resistant decisions for package,
seat, validity, grace and support/update rights without changing Discipline,
Package, Project or Workspace identity. Entitlement can restrict new use but
cannot grant data authorization or erase authorized historical read/export.

PATCH-051 implements no signing, seats, validity, grace, activation, billing or
license storage.

## 46. Architecture decisions requiring ADR

Before EDS-051 acceptance, one new cross-cutting ADR is required:

**Accepted ADR-024 — Trusted Discipline Package Identity, Registry &
Configuration Architecture.**

It must freeze the separate Discipline/Package namespaces, trusted release
registry, persisted registry projection, configuration hierarchy, single-
package decision for package-backed Workspaces, explicit unconfigured and
unbound states, Project-owned version inheritance, version/compatibility
model, legacy-preservation policy, static contribution mechanism and PATCH-059
seam.

ADR-014's one Workspace per Project/Discipline, ADR-016's one product/no forks,
ADR-020's open governed extension, ADR-021's shared Engineering Intelligence
ownership and both ADR-017 one-product/licensing decisions remain preserved.
No accepted ADR is silently superseded by this artifact.

## 47. Expected persistence and migration impact

Later implementation is expected to require:

- trusted installed package-version registry projection;
- Organization package configuration and history;
- optional Project package/version selection, compatibility profile and
  history, including the valid `NOT_CONFIGURED` state;
- Workspace canonical Discipline and explicit bound/unbound/unresolved state
  history, with derived package provenance only where applicable;
- canonical shadow/provenance fields where package-dependent meaning requires;
- evolution of Workspace and Engineering Object constraints;
- compatibility handling for Capture, Context and free-text Deliverable data;
- a new Report provenance schema version for new package-aware sources while
  preserving accepted V1 JSON; and
- typed minimized package/configuration Audit identity.

The exact number and shape of tables/columns/migrations are intentionally not
fixed at Architecture level. At least one migration is likely; none is created
or authorized here.

## 48. Critical architectural risks and controls

| Risk | Required control |
|---|---|
| silent reinterpretation of `control`/`industrial_automation` | typed exact alias map, raw history retained, no global string replacement |
| accepted Report/Memory digest breakage | immutable V1 snapshots; additive new provenance schema only |
| package configuration becomes authorization | ordered independent authorization and effective-capability predicates |
| registry/code/database drift | release-bound digests, startup/readiness fail-closed validation |
| arbitrary plugin framework | static explicit registration; no runtime code loading or executable descriptors |
| enum/CHECK migration outage | deployed-data preflight, additive shadow model, dual-read/write and rollback evidence |
| package upgrade changes engineering meaning | exact project pin, explicit compatibility/preflight/Human action and historical descriptor retention |
| empty Projects force fabricated configuration | valid `NOT_CONFIGURED` Project state; configuration gated at package-dependent transition |
| future Disciplines receive unsupported packages | explicit `FUTURE_UNAVAILABLE_UNBOUND` state with no package capability |
| Workspace becomes a second version authority | exact version inherited from Project; Workspace provenance is derived only |
| shared scope unions permissions | single-package Workspace; Project-level cross-discipline reads authorize every source separately |
| future packages force Core fork | closed stable ports plus governed descriptor/catalog extension and conformance |
| frontend reveals configuration | authorized effective projection, protected minimization and closed component registry |
| unbounded contributions/traversal | Core maxima, finite declarations, bounded ports and no autonomous loops |

## 49. Open questions and EDS handoff

There are **no blocking Architecture questions**. EDS must close these bounded
implementation decisions after Architecture/ADR acceptance:

1. exact physical table/column/index/constraint names;
2. measured row counts and distinct deployed legacy values;
3. exact numeric registry/contribution/configuration limits;
4. canonical serialization bytes and digest test vectors;
5. exact API compatibility fields, routes and deprecation evidence;
6. migration batches, lock/transaction strategy and rollback checkpoints;
7. retained historical descriptor/version policy per supported release;
8. exact compatibility profile vocabulary for E/I/C combinations;
9. exact finite schema/state names and transition mechanics for
   `NOT_CONFIGURED`, `CONFIGURED`, `OPERATIONAL_PACKAGE_BOUND`,
   `FUTURE_UNAVAILABLE_UNBOUND` and `LEGACY_UNRESOLVED`;
10. exact safe Audit event schemas and an Organization-scoped transactional
    Audit persistence/read contract;
11. executable/supported versus historical-read-only PackageVersion standing;
12. release-wide registry digest, selected descriptor-set digest and
    compatibility-profile provenance representation; and
13. exact conformance fixture and negative-test matrix.

If deployed data contains an unclassified discipline value or accepted history
that the additive strategy cannot preserve, EDS must stop for governed
reconciliation rather than guess.

## 50. Architecture documentation manifest

The minimum Architecture manifest is this single artifact:

- `docs/design/Architecture-051-Shared-Multi-Discipline-Core-and-Discipline-Package-Contract.md`.

The PATCH registration and Human-frozen roadmap require no reconciliation.
ADR-024 is accepted and provides the required durable decision authority. The
PATCH registration and Human-frozen roadmap require no reconciliation. No
historical CLOSED PATCH record is modified.

## 51. Architecture review and acceptance outcome

The amended artifact passed the focused independent Architecture re-review of
`A051-MAJ-01` because it:

- inventories actual identity/persistence/API/frontend conflicts;
- defines Discipline and Package separately;
- resolves canonical identity, version, registry and configuration hierarchy;
- permits an unconfigured empty Project and gates configuration at the E/I/C
  package-dependent Workspace transition;
- preserves future-unavailable and unresolved Workspaces without fabricated
  package identity while keeping exact Project version authority;
- preserves the accepted Workspace model and Human authority;
- provides explicit legacy/migration/rollback safety;
- closes authorization, non-disclosure and arbitrary-plugin boundaries;
- prepares PATCH-052, PATCH-053, PATCH-054 and PATCH-059 seams without
  implementing them; and
- identifies the ADR and EDS decisions still required.

The original independent review remains preserved as `FAIL / STOPPED`
historical evidence. The focused independent re-review is `PASS / ACCEPTED`,
`A051-MAJ-01` is `RESOLVED / CLOSED`, ADR-024 is `ACCEPTED`, and Human
Architecture-051 Acceptance is `PASS / GRANTED`. Architecture-051 is
`ACCEPTED / COMPLETE`.

## 52. Exact governance state

| Governance item | State |
|---|---|
| PATCH-050 | DONE / CLOSED |
| PATCH-051 | REGISTERED / OPEN |
| Original Independent Architecture Review | FAIL / STOPPED / historical evidence preserved |
| Focused Independent Architecture re-review | PASS / ACCEPTED |
| A051-MAJ-01 | RESOLVED / CLOSED |
| ADR-024 | ACCEPTED |
| Architecture-051 | ACCEPTED / COMPLETE |
| Architecture Gate | PASS / ACCEPTED |
| Human Architecture acceptance | PASS / GRANTED |
| EDS-051 | NOT STARTED / ELIGIBLE FOR SEPARATE HUMAN DESIGN AUTHORITY |
| IDS-051 | NOT STARTED |
| Implementation | NOT AUTHORIZED |
| Migration | NOT AUTHORIZED |
| PATCH-052 | NOT STARTED |
| Commercial V1 roadmap | HUMAN-FROZEN / UNCHANGED |

Exact next resume point: separately authorized Human EDS-051 design authority.
EDS, IDS, implementation, migration and PATCH-052 do not begin through this
Architecture Acceptance reconciliation.
