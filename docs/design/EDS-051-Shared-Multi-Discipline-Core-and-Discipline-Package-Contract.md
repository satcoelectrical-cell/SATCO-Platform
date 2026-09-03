# EDS-051 — Shared Multi-Discipline Core & Discipline Package Contract

## 1. Status, authority and verdict

| Field | Value |
|---|---|
| PATCH | PATCH-051 — Shared Multi-Discipline Core & Discipline Package Contract |
| Human design authority | HUMAN EDS-051 DESIGN AUTHORITY: GRANTED |
| Architecture basis | Architecture-051 `ACCEPTED / COMPLETE`; Architecture Gate `PASS / ACCEPTED` |
| ADR basis | ADR-024 `Accepted` |
| Initial independent EDS review | FAIL / STOPPED; Critical/Major/Minor/Observation `0/3/1/4` |
| Focused remediation authority | HUMAN FOCUSED EDS-051 REMEDIATION AUTHORITY: GRANTED |
| Focused independent EDS re-review | PASS / ACCEPTED; all four findings RESOLVED / CLOSED; new findings `0/0/0/0` |
| Human EDS acceptance | HUMAN EDS-051 ACCEPTANCE: PASS / GRANTED |
| EDS status / Gate | **ACCEPTED / COMPLETE**; **PASS / ACCEPTED** |
| IDS-051 | NOT STARTED / ELIGIBLE FOR SEPARATE HUMAN DESIGN AUTHORITY |
| Implementation / migration | NOT AUTHORIZED / NOT CREATED |
| PATCH-052 | NOT STARTED |

This Human-accepted EDS translates the accepted architecture into an
implementation-ready design. Acceptance does not alter Architecture-051 or
ADR-024, grant IDS or implementation authority, or introduce an operational
Discipline Package. The Human-frozen Commercial V1 roadmap is unchanged.

The three inherited observations are resolved as follows:

| Obligation | Binding EDS resolution |
|---|---|
| `A051-OBS-01` | Registry membership has closed standing `EXECUTABLE_SUPPORTED` or `HISTORICAL_READ_ONLY`; only the first is selectable/executable. |
| `A051-OBS-02` | Package configuration uses a new Organization-keyed, append-only audit store and scoped query; the generic global `audit_logs` listing is not reused. |
| `A051-OBS-03` | `RegistryDigest`, per-version `DescriptorDigest`, selected-descriptor-set digest and compatibility-profile digest have distinct types, canonical inputs and storage. |

The focused remediation resolved `EDS051-MAJ-01`, `EDS051-MAJ-02`,
`EDS051-MAJ-03` and `EDS051-MIN-01` without changing an accepted Architecture
or ADR decision. The initial independent review remains preserved as
historical evidence; the focused independent re-review is `PASS / ACCEPTED`,
and explicit Human acceptance records this EDS as `ACCEPTED / COMPLETE`.

## 2. Repository evidence and governing invariants

Repository inspection establishes these facts:

- the manually verified Alembic graph is one linear chain with sole head
  `e04700000001` (`e04700000001_project_controls.py`); the local `alembic`
  executable and a running database were unavailable, so a live deployed-data
  census remains a mandatory migration preflight;
- `engineering_workspaces.discipline` is `String(32)` with values
  `electrical`, `instrumentation`, `control`, `mechanical`, `civil`, `process`
  and uniqueness `(project_id, discipline)`;
- Project creation does not require a Workspace or package configuration;
- the current generic `audit_logs` record has no `organization_id`, and its
  admin listing is global;
- active Organization context is server-derived; current application roles are
  `admin` and `engineer`, and Project ownership is an existing authority rule;
- the frontend Workspace selector omits backend-supported `control`; and
- Context, Engineering Objects, Relationships, Interface Commitments,
  Evidence, Technical Reports, Organizational Memory and Guidance already have
  accepted owners that a package must not replace.

The design therefore freezes these invariants:

1. Discipline, Package, taxonomy family and presentation category are separate
   namespaces even where literals coincide.
2. Project is the only exact package-version selection authority.
3. Workspace identity remains one `(Project, Discipline)` and never becomes a
   version selector.
4. Registry/configuration/entitlement/data authorization are independent
   predicates; no predicate grants another.
5. Historical records are interpreted by their original contract. No accepted
   Report, Memory, Evidence or generic Audit record is rewritten.
6. Package declarations are bounded data plus statically registered SATCO
   adapters, never executable customer content or runtime plugins.

## 3. Canonical physical identity types

Core exposes distinct frozen value objects. Persistence and transport may use
the same primitive, but code must not compare different semantic types without
an explicit mapping.

| Type | Physical/API representation | Validation |
|---|---|---|
| `DisciplineId` | `VARCHAR(64)` / string | `^[a-z][a-z0-9_]{0,63}$`; Core catalog only |
| `PackageKey` | `VARCHAR(64)` / string | same lexical rule; registry catalog only |
| `PackageVersion` | `VARCHAR(32)` / string | canonical SemVer 2 `major.minor.patch[-prerelease]`; core numbers `0..999999` with no leading zero; prerelease identifiers `1..16` ASCII alphanumeric/hyphen chars, numeric identifiers no leading zero; build metadata prohibited |
| `CoreContractVersion` | `SMALLINT` / integer | `1..32767`; PATCH-051 establishes `1` |
| `CompatibilityProfileId` | `VARCHAR(64)` / string | `^[a-z][a-z0-9_.-]{0,63}$` |
| `EntitlementKey` | `VARCHAR(128)` / string | `^[a-z][a-z0-9_.-]{0,127}$` |
| `RegistryDigest` | `CHAR(64)` / lowercase string | SHA-256 hex; release manifest only |
| `DescriptorDigest` | `CHAR(64)` / lowercase string | SHA-256 hex; exactly one descriptor |
| `SelectedDescriptorSetDigest` | `CHAR(64)` / lowercase string | SHA-256 hex; ordered Project selection set |
| `CompatibilityProfileDigest` | `CHAR(64)` / lowercase string | SHA-256 hex; exactly one profile definition |
| `CompatibilityCombinationDigest` | `CHAR(64)` / lowercase string | SHA-256 hex; one canonical allowed combination inside one profile; internal relational identity, never a substitute for profile provenance |
| `ConfigurationRevision` | `BIGINT` / integer | `1..9223372036854775807`; immutable Project revision |
| `ConfigurationVersion` | `BIGINT` / integer | `0..9223372036854775807`; optimistic Organization/head version |
| `RegistryReleaseId` | `VARCHAR(64)` / string | `^[a-z0-9][a-z0-9_.-]{0,63}$`; source release label |

Digest fields use separate wrapper classes and schema names. A generic
`digest` field is prohibited. UUIDs identify Organizations, audit events and
correlations; existing integer identifiers continue to identify Projects,
Workspaces and Users. Display names are UTF-8 strings, trimmed, NFC normalized,
`1..120` characters, and are never identifiers.

## 4. Trusted source registry and release assembly

### 4.1 Authority and representation

The authoritative registry is a source-controlled immutable tuple of strict
`DisciplinePackageDescriptorV1` values plus an explicit adapter table in the
application composition root. Descriptors are code-reviewed declarative data
under `backend/app/discipline_packages/descriptors/`; the static table maps
exact `(PackageKey, PackageVersion, adapter_id)` triples to precompiled
SATCO-owned adapters.

Assembly must not use Python entry points, directory scanning, `importlib`,
environment-provided import paths, database discovery, network retrieval,
customer files, scripts, expression evaluation or runtime code download. The
PATCH-051 production release may legitimately contain zero operational package
descriptors. Test fixtures are never registered in production assembly.

`RegistryReleaseManifestV1` contains exactly `schema_version=1`, release ID,
Core contract version, sorted descriptor-digest/adapter registrations, sorted
compatibility profiles and each membership standing. A build embeds its
expected RegistryDigest and deployment may install only that embedded
manifest. No environment value may substitute a different manifest.

`CompatibilityProfileV1` contains profile ID/version, Core contract version, a
set of `1..32` exact package combinations (each `1..8` members), aggregate
resource ceilings, optional required interface IDs and its profile digest. One
combination contains at most one exact version of a PackageKey. The same
PackageKey may occur at different exact versions in different combinations.
The profile has no wildcard version, `latest`, expression or executable
predicate.

### 4.2 Canonical bytes and validation

Canonical JSON is UTF-8, NFC-normalized, object keys sorted by Unicode code
point, compact separators, lowercase enumerations, integer numbers only, and
no floats, timestamps, insignificant nulls or duplicate keys. Arrays whose
schema identifies a set are sorted by their documented identity tuple; arrays
whose order is meaningful include a unique integer `ordinal` and are serialized
by it. Digests use SHA-256 over these bytes.

Profile member and combination ordering is not semantic. Each combination is
canonicalized as the sorted array of `{package_key, package_version,
descriptor_digest}` ordered by that tuple. `CompatibilityCombinationDigest` is
SHA-256 over those canonical combination bytes. Duplicate PackageKeys inside a
combination and duplicate combination digests inside a profile are rejected.
The profile canonical form sorts combinations by their combination digest and
includes each digest plus its full canonical member array. The
`CompatibilityProfileDigest` covers that complete form; adding, removing or
changing any member changes both the affected combination digest and profile
digest. No member or combination ordinal is persisted because ordering carries
no meaning.

Startup constructs the registry, then validates in this order:

1. schema version, lexical types, exact bounds and unknown-field rejection;
2. unique package/version, descriptor digest and adapter registration;
3. canonical Discipline mapping and Core contract support;
4. contribution identity collisions with Core and all other descriptors;
5. dependency/conflict referential validity and absence of self-dependency;
6. acyclic dependency graph and maximum depth;
7. profile membership and allow-listed package combinations;
8. resource-budget totals and static adapter capability equality;
9. canonical descriptor, profile and release digests; and
10. exact equality with the installed database projection.

Any invalid source descriptor prevents application readiness. Any missing,
extra or differing current projection row prevents package configuration and
package execution and makes readiness fail. Historical read endpoints may use
retained immutable projection rows only after their stored digest revalidates;
they never execute adapters under drift.

Registry synchronization is a release/deployment operation, not an HTTP API.
It uses the cross-process serialization protocol in section 21, inserts an
immutable release and its rows, compares every digest, and atomically switches
the one `is_current` row. Source remains authority; customer roles have no
write path. Installation/activation evidence belongs to the release projection
and deployment operations evidence described in section 16, never to a
fabricated Organization Audit event.

## 5. Package version lifecycle (`A051-OBS-01`)

`PackageVersionStanding` is closed:

- `EXECUTABLE_SUPPORTED`: present in the current trusted release, adapter
  registered, compatible with the deployed Core and eligible for new selection
  and execution subject to every later authorization predicate.
- `HISTORICAL_READ_ONLY`: retained with descriptor/provenance for authorized
  interpretation, but ineligible for new selection, Project reconfiguration,
  Workspace creation or package-owned mutation/execution.

Standing belongs to a registry-release membership, not the immutable
descriptor. Moving a version out of support requires a new registry release;
the prior release and descriptor remain. Existing Project revisions remain
interpretable through stored descriptor/profile digests. Their structurally
bound Workspaces remain bound for provenance, while effective state reports
`HISTORICAL_READ_ONLY` and all package-owned writes fail with
`PACKAGE_VERSION_HISTORICAL_ONLY`.

Upgrade and downgrade are explicit Project revision operations. Each requires
current Organization enablement, executable standing, compatibility preflight,
expected head version, Human rationale, migration-compatibility declaration
and atomic Audit. There is no `latest` alias. A downgrade is allowed only when
the target descriptor explicitly accepts the source version, all selected
packages/profile accept the resulting set, and a package migration guard proves
no persisted package-owned data needs a newer schema. Otherwise it fails
closed. Rollback creates a new revision selecting the prior exact versions; it
never moves a head pointer backward or deletes history.

## 6. Registry database projection

All registry tables are server-written, append-only except the current-release
pointer, and unavailable to customer mutation APIs.

| Table | Required columns and constraints |
|---|---|
| `discipline_package_registry_releases` | `registry_digest CHAR(64) PK`, `release_id VARCHAR(64) UNIQUE NOT NULL`, `core_contract_version SMALLINT NOT NULL`, `manifest_json JSONB NOT NULL`, `installed_at TIMESTAMPTZ NOT NULL`, `is_current BOOLEAN NOT NULL`; digest/core checks; unique partial index where current |
| `discipline_package_descriptors` | composite PK `(package_key, package_version)`; `primary_discipline_id`, `core_contract_version`, `descriptor_digest CHAR(64) UNIQUE`, `descriptor_json JSONB`, `adapter_id VARCHAR(128)`, `entitlement_key`, `created_at`; exact lexical/digest checks; additional unique `(package_key, package_version, descriptor_digest)` for provenance FKs; immutable |
| `discipline_package_registry_memberships` | PK `(registry_digest, package_key, package_version)`; FKs to release and descriptor; `standing VARCHAR(32)` check in two states; indexes `(registry_digest, standing, package_key, package_version)` |
| `discipline_package_compatibility_profiles` | PK `(profile_id, profile_digest)`; `registry_digest` FK, `profile_json JSONB`, `created_at`; unique `(registry_digest, profile_id)` and `(registry_digest, profile_id, profile_digest)` plus digest checks |
| `discipline_package_compatibility_members` | one row per exact member per allowed combination; columns `profile_id`, `profile_digest`, `combination_digest CHAR(64)`, `package_key`, `package_version`, `descriptor_digest`; PK `(profile_id, profile_digest, combination_digest, package_key)`; FK `(profile_id, profile_digest)` to profile and `(package_key, package_version, descriptor_digest)` to descriptor; digest checks; index `(profile_id, profile_digest, combination_digest, package_key, package_version)` and lookup index `(package_key, package_version)` |

Database roles deny direct mutation to application/customer roles other than
the release synchronization path. A current-release membership may reference
an old descriptor without altering it. Projection comparison hashes canonical
stored JSON, compares row sets and verifies foreign keys—not merely row counts.
Projection validation groups member rows by combination digest, recomputes each
digest from its sorted exact members, rejects a duplicate PackageKey within a
combination, rejects duplicate semantic combinations before insertion, enforces
`1..8` members and `1..32` combinations, and compares the complete grouped row
set to authoritative profile JSON. Different combinations may therefore carry
different versions of the same PackageKey without PK collision or member
collapse. The table remains a derived integrity projection, not compatibility
authority.

## 7. Organization package configuration

Organization configuration is an administrative availability policy, not an
entitlement, data permission or assertion that a package is deployed.

| Table | Required columns and constraints |
|---|---|
| `organization_package_configuration_heads` | `organization_id UUID PK/FK organizations ON DELETE RESTRICT`, `configuration_version BIGINT NOT NULL DEFAULT 0`, `updated_by_id` FK users, `updated_at`; nonnegative check |
| `organization_package_selections` | PK `(organization_id, package_key, package_version)`; `state` check `ENABLED`/`DISABLED`; descriptor composite FK; `configuration_version BIGINT NOT NULL`, actor/timestamps; index `(organization_id, state, package_key)` |

Absence of a head is equivalent to version `0` and no enabled selection. A
disabled row is retained so an administrator can distinguish explicit disable
from never configured; it cannot be selected by a new Project. Multiple exact
versions of one package may be enabled to support controlled upgrades, within
bounds. Disabling a version used by a Project blocks new configuration and
package-owned mutations but preserves authorized historical reads. It does not
delete or silently rewrite Project configuration.

Only an authenticated `admin` in the active server-derived Organization may
read or mutate this configuration. Mutations replace the full bounded desired
enabled set, require `expected_configuration_version`, and lock the head. A
previously enabled row omitted from the desired set becomes `DISABLED`, never
deleted; never-seen omitted versions receive no row. Disabled history is not
resubmitted and the GET may return at most the registry-wide 32 retained rows.
A mismatch is `409 CONFIGURATION_VERSION_CONFLICT`. Audit insertion is in the
same transaction; Audit failure rolls back the mutation.

## 8. Project package configuration

Project state is derived, never duplicated as a mutable enum:

- no head row = `NOT_CONFIGURED`, zero selections and no profile;
- head row to an immutable nonempty revision = `CONFIGURED`.

| Table | Required columns and constraints |
|---|---|
| `project_package_configuration_revisions` | PK `(project_id, configuration_revision)`; `organization_id UUID NOT NULL`, profile ID/digest, observed registry digest, selected-set digest, `created_by_id`, `rationale VARCHAR(2000)`, `created_at`; composite FKs `(project_id, organization_id)` to Project and `(observed_registry_digest, profile_id, profile_digest)` to profile, plus release FK; revision positive |
| `project_package_configuration_selections` | PK `(project_id, configuration_revision, package_key)`; exact `package_version`, `descriptor_digest`; FK to revision and composite FK to descriptor; unique descriptor-set member |
| `project_package_configuration_heads` | `project_id` PK/FK Project `ON DELETE RESTRICT`, `organization_id`, `current_revision`, `configuration_version`, actor/timestamps; composite FK to immutable revision; unique/project-org consistency and nonnegative version checks |

Each revision has `1..8` selections, exactly one version per key, one applicable
profile and digests recomputed in the transaction. A deferred constraint
trigger rejects empty revisions or selections whose Organization is wrong.
Rows are immutable; updates insert revision `max+1` and advance the head.

The selected exact set must match exactly one authoritative allowed combination
inside the selected profile. Matching recomputes the combination digest from
the Project selections and resolves it against the derived profile members.
The combination digest is an internal validation key: Project persistence and
public DTOs continue to carry the full exact selections, selected-set digest
and profile ID/digest, which together reproduce the choice without adding a
caller-selectable combination authority.

Creation/update requires current Organization enablement, current executable
standing, successful compatibility evaluation and no migration guard failure.
The actor must be active-Organization admin or existing Project owner. Removing
configuration is allowed only when no Workspace is structurally package-bound;
it deletes only the head and writes an Audit event, retaining every revision.
Rollback is the same validated operation using a prior revision as input and
creates new history.

Every configured-to-configured change—including upgrade, downgrade, rollback,
profile-only change and unrelated package addition—treats all current
`OPERATIONAL_PACKAGE_BOUND` Workspaces in the Project as affected. This
conservative rule keeps every current derived binding on the Project head and
avoids an IDS decision about whether a profile change is material to one
Workspace. For every affected Workspace, the target revision must contain its
same `bound_package_key`, that selection must exactly map to the Workspace's
canonical Discipline, and the full target configuration must remain executable,
Organization-enabled and compatible. A version change also requires its
migration guard. A target that removes a bound key, makes it historical-only or
cannot migrate is rejected; configuration change never converts the Workspace
to future-unavailable or unresolved.

In the single transaction defined in section 21, the service inserts the new
immutable revision and selections, updates every affected Workspace's
`bound_project_configuration_revision` to that new revision (the package key
remains derived and unchanged), advances the Project head, writes one Project
configuration Audit event plus one bounded Workspace binding event per affected
Workspace, and commits. There are at most seven affected Workspaces under the
Core Discipline catalog. If any validation, Workspace update or Audit insert
fails, the entire transaction rolls back; the old Project head, every old
Workspace binding and all prior immutable revisions remain authoritative.

## 9. Workspace binding and lifecycle

The existing Workspace gains these fields:

| Column | Type/nullability | Meaning |
|---|---|---|
| `canonical_discipline_id` | `VARCHAR(64) NULL` during transition, final conditional | exact canonical shadow; not a PackageKey |
| `package_binding_state` | `VARCHAR(40) NULL` during backfill, then NOT NULL | `OPERATIONAL_PACKAGE_BOUND`, `FUTURE_UNAVAILABLE_UNBOUND`, `LEGACY_UNRESOLVED` |
| `bound_package_key` | `VARCHAR(64) NULL` | derived selected Project package key |
| `bound_project_configuration_revision` | `BIGINT NULL` | immutable Project selection revision |

The existing `discipline` column remains the raw legacy/API-compatible value.
Workspace does not store an independently editable version. For a bound row,
the composite FK `(project_id, bound_project_configuration_revision,
bound_package_key)` resolves exact package version and descriptor digest from
the Project selection. This is derived provenance, not a second authority.

For a `CONFIGURED` Project, every `OPERATIONAL_PACKAGE_BOUND` Workspace must
reference the Project head's `current_revision`. This is enforced by the
application transaction and verified by a deferred database constraint trigger
before commit. The trigger also proves that the referenced head revision
contains the Workspace package key. Immutable historical Project selections
and package-causal operational records preserve prior provenance; the current
Workspace pointer is not retained on an old revision for that purpose.

Checks require:

- `OPERATIONAL_PACKAGE_BOUND`: canonical Discipline, package key and revision
  all non-null; key maps exactly to the Discipline; Project selection exists;
- `FUTURE_UNAVAILABLE_UNBOUND`: canonical Discipline non-null and both binding
  fields null; and
- `LEGACY_UNRESOLVED`: canonical Discipline and both binding fields null.

The existing unique `(project_id, discipline)` is retained during compatibility.
A new partial unique index `(project_id, canonical_discipline_id)` where the
canonical value is non-null enforces one Workspace per canonical Discipline.

New E/I/C Workspace creation requires a configured Project with the matching
executable package and creates a bound row inheriting the head revision.
PATCH-051 has no operational packages, so it cannot fabricate such execution.
Mechanical/Civil/Process may remain truthfully future-unavailable if existing
Workspace creation policy permits them. No new unresolved value is accepted.
Project reconfiguration never selects or updates binding fields for
`FUTURE_UNAVAILABLE_UNBOUND` or `LEGACY_UNRESOLVED` rows.

## 10. Exact legacy reconciliation

Mappings are keyed by the owning source contract; matching is exact and
case-sensitive. There is no trim-and-guess, case fold, substring, similarity or
global replacement.

| Source contract/value | Canonical disposition |
|---|---|
| Workspace `electrical` | `DisciplineId(electrical)`; eligible for PackageKey `electrical` only through explicit Project selection |
| Workspace `instrumentation` | `DisciplineId(instrumentation)`; eligible for PackageKey `instrumentation` only through explicit selection |
| Workspace `control` | `DisciplineId(control_automation)`; raw `control` retained; eligible for PackageKey `control_automation` |
| Workspace `mechanical` / `civil` / `process` | same canonical Discipline; `FUTURE_UNAVAILABLE_UNBOUND` |
| EKG `industrial_automation` | exact bridge to `DisciplineId(control_automation)`; raw EKG identity unchanged |
| Object/relationship family `automation` | remains taxonomy family `automation`; never a Discipline/Package alias |
| Guidance category `automation_and_control` | remains advisory category; never a Discipline/Package alias |
| EKG `shared_engineering` | reserved Core Discipline classification, not a commercial package |
| Object family `shared` | remains Core taxonomy family, not a package |
| unknown bounded legacy free text in free-text owners | unresolved in its owning record; no Workspace binding fabricated |

Reads continue returning the legacy `discipline` field and add canonical and
binding fields. Writes during the transition accept only the old closed
Workspace vocabulary; `control_automation` is not written into the legacy
column. New package APIs use canonical types only. Retirement of the legacy
field requires a later accepted migration after: all deployed censuses contain
no unknown Workspace value, all supported clients consume canonical fields,
two released compatibility cycles have elapsed, and historical snapshot
readers remain versioned. Retirement never rewrites accepted snapshots.

Existing exact E/I/C Workspaces backfill canonical identity but initially
remain `FUTURE_UNAVAILABLE_UNBOUND`. They become operationally bound only in a
separately authorized, audited transition when an exact executable Project
selection exists and package migration/conformance succeeds. Unknown values
remain `LEGACY_UNRESOLVED`; future Disciplines remain unbound.

## 11. Migration design (files not created)

The future migration chain is linear and fixed relative to current sole head:

1. `e05100000001_registry_configuration_audit`, `down_revision=e04700000001`:
   create registry projection, Organization/Project configuration, package Audit
   and supporting constraints/indexes, including the combination-digest profile
   membership PK in section 6; no configuration rows are fabricated.
2. `e05100000002_workspace_binding_shadow`, down revision `e05100000001`:
   add the four nullable Workspace shadow/binding columns, indexes and
   `NOT VALID` composite foreign keys/checks; preserve legacy check/column.
3. `e05100000003_workspace_binding_cutover`, down revision `e05100000002`:
   run exact set-based backfill, reject unexpected counts, validate constraints,
   set `package_binding_state NOT NULL`, install conditional checks and install
   the deferred bound-Workspace/current-Project-head consistency trigger.

Before M1, a read-only preflight records DB revision, all distinct values and
counts for every discovered discipline-bearing column, duplicate canonical
Workspace candidates, orphan Organizations/Projects/Workspaces, accepted
Report/Memory/Audit counts and checksums, and PostgreSQL constraint capability.
Any unknown Workspace value or duplicate caused by `control` reconciliation is
a stop condition requiring explicit Human remediation; it is not guessed.

Backfill eligibility is exact:

- six current Workspace values receive the canonical shadow mapping in section
  10;
- all receive `FUTURE_UNAVAILABLE_UNBOUND` initially because PATCH-051 installs
  no operational package and no Project selection may be invented;
- a later controlled bind may affect only exact `electrical`,
  `instrumentation`, or `control` rows with an existing exact executable Project
  selection and successful package migration guard;
- future Disciplines remain unbound and unknowns remain unresolved.

Migrations use chunked indexed updates, deterministic primary-key order,
statement/lock timeouts and count assertions. No accepted Report JSON, Memory
projection, Evidence, generic Audit details, EKG raw identity or Guidance value
is rewritten. The legacy Workspace check is retained through PATCH-051.

Rollback before cutover drops only empty/unreferenced new structures. After
configuration/binding writes, rollback is application-first: restore code able
to read new columns, mark packages historical, and create audited forward
revisions. Destructive downgrade is prohibited if a Project revision,
Workspace binding or package Audit references the structures. M3 downgrade may
remove validation/not-null only; it must not erase shadows or history.

## 12. Digest and provenance separation (`A051-OBS-03`)

| Provenance | Canonical input | Stored/emitted at |
|---|---|---|
| `RegistryDigest` | release ID, Core version, sorted descriptor digests, profile digests, adapter IDs and per-version standing | release PK; Project revision observed release; API registry metadata; Audit |
| `DescriptorDigest` | one complete canonical `DisciplinePackageDescriptorV1` | descriptor row; each Project selection; effective Project/Workspace provenance |
| `SelectedDescriptorSetDigest` | sorted array of `{package_key, package_version, descriptor_digest}` | Project revision; effective response; Audit |
| `CompatibilityProfileDigest` | one complete canonical profile including allowed exact member combinations and constraints | profile row; Project revision; effective response; Audit |

`CompatibilityCombinationDigest` is a subordinate internal relational key for
one member set inside a profile. It is stored only on the derived compatibility
member rows and used during exact combination matching. It is not Registry,
descriptor, selected-set or profile provenance, is not accepted from clients
and is not emitted as a substitute for any of the four authoritative provenance
fields above.

An unrelated registry addition changes `RegistryDigest` but does not change an
unchanged descriptor, selected set or profile digest. One selected package has
both its `DescriptorDigest` and the set digest; neither is called a registry
digest. APIs use the exact field names above. Conformance vectors must include
empty registry, one package, ordering permutations, Unicode rejection/normal-
ization, profile-only change and unrelated-package addition.

## 13. Deterministic compatibility engine

`evaluate_package_compatibility(input) -> CompatibilityEvaluationV1` is a pure,
non-AI operation over validated in-memory registry values and a bounded
persistence summary.

Input contains current RegistryDigest/CoreContractVersion, sorted requested
exact selections, profile ID/digest, enabled Organization selection set,
existing Project selection (if any), migration-guard facts and aggregate
resource counters. Caller-supplied Organization identity is never trusted.

Evaluation order is fixed: lexical/uniqueness; current membership/standing;
Organization enablement; Core version; dependencies; conflicts; exact
profile/allow-list; taxonomy/contribution collisions; migration compatibility;
aggregate resource budgets. Dependency traversal is key/version sorted, depth
limited to 4, and visits at most 32 versions.

Profile/allow-list evaluation canonicalizes the requested exact member set,
recomputes its combination digest and requires exactly one matching combination
under the source-authoritative profile. Zero matches is
`PROFILE_NOT_ALLOWED`; duplicate source combinations invalidate registry
startup rather than producing an ambiguous runtime result.

Output has `decision` (`COMPATIBLE`, `INCOMPATIBLE`, `UNAVAILABLE`), normalized
selections, all four provenance digests, and sorted unique reason codes. It
contains no hidden foreign configuration. Closed reason codes are:

`REGISTRY_UNAVAILABLE`, `REGISTRY_DRIFT`, `UNSUPPORTED_VERSION`,
`HISTORICAL_ONLY`, `ORGANIZATION_DISABLED`, `CORE_CONTRACT_MISMATCH`,
`MISSING_DEPENDENCY`, `DECLARED_CONFLICT`, `PROFILE_NOT_ALLOWED`,
`TAXONOMY_COLLISION`, `CONTRIBUTION_COLLISION`, `MIGRATION_REQUIRED`,
`MIGRATION_INCOMPATIBLE`, and `RESOURCE_LIMIT_EXCEEDED`.

Invalid registry state is `UNAVAILABLE`; an invalid prospective set is
`INCOMPATIBLE`. The engine evaluates no expressions and performs no network,
database mutation, adapter execution or probabilistic reasoning.

## 14. Concrete API contracts

All routes use the repository's existing root-style FastAPI composition.
Schemas are strict, reject unknown fields and never accept actor/Organization
identity. Lists have stable keyset order and opaque cursors.

| Method/route | Authority | Request | Success |
|---|---|---|---|
| `GET /discipline-packages/supported` | authenticated active-org member | query `cursor?`, `limit=50` (`1..50`) | current executable package summaries and current `registry_digest`; never Organization configuration |
| `GET /organizations/current/discipline-package-configuration` | active-org admin | none | head version and enabled/disabled exact selections |
| `PUT /organizations/current/discipline-package-configuration` | active-org admin | `expected_configuration_version`, full desired enabled `selections[0..16]`, `rationale[1..2000]` | new version/configuration plus provenance |
| `GET /organizations/current/discipline-package-configuration/audit` | active-org admin | cursor, `limit 1..100`, optional event category | Organization-only minimized events |
| `GET /projects/{project_id}/discipline-package-configuration` | authorized Project reader | none | `NOT_CONFIGURED` or immutable head selection/profile provenance |
| `PUT /projects/{project_id}/discipline-package-configuration` | active-org admin or Project owner | expected version, profile ID, `selections[1..8]`, rationale | new immutable revision/head and compatibility result |
| `DELETE /projects/{project_id}/discipline-package-configuration` | active-org admin or Project owner | expected version and rationale | `NOT_CONFIGURED`; only when no bound Workspace |
| `POST /projects/{project_id}/discipline-package-configuration/preflight` | active-org admin or Project owner | prospective profile/selections, no actor/org | deterministic compatibility result; no mutation |
| `GET /projects/{project_id}/effective-discipline-packages` | authorized Project reader | none | effective states for all canonical Workspace-selectable Disciplines |
| `GET /workspaces/{workspace_id}/package-applicability` | authorized Workspace reader | none | legacy value, canonical Discipline, binding state and authorized package provenance |

The strict response/request DTOs are:

- `PackageSelectionV1(package_key, package_version)`; server responses add the
  exact `descriptor_digest` and standing.
- `SupportedPackageSummaryV1(package_key, package_version,
  primary_discipline_id, display_name, standing, core_contract_version,
  descriptor_digest, entitlement_key, frontend_metadata)` and
  `SupportedPackagePageV1(registry_digest, items, next_cursor?)`.
- `OrganizationPackageConfigurationV1(organization_id,
  configuration_version, enabled_selections, disabled_selections,
  registry_digest, updated_at)`; Organization ID is output only.
- `OrganizationPackageConfigurationReplaceV1(expected_configuration_version,
  enabled_selections, rationale)`.
- `ProjectPackageConfigurationV1(state, project_id, organization_id,
  configuration_version, configuration_revision?, profile_id?,
  profile_digest?, registry_digest?, selected_descriptor_set_digest?,
  selections, created_at?)`. All optional provenance is null and selections
  empty only for `NOT_CONFIGURED`.
- `ProjectPackageConfigurationReplaceV1(expected_configuration_version,
  profile_id, selections, rationale)` and
  `ProjectPackageConfigurationRemoveV1(expected_configuration_version,
  rationale)`.
- `CompatibilityPreflightV1(profile_id, selections)` and
  `CompatibilityEvaluationV1(decision, normalized_selections,
  registry_digest?, selected_descriptor_set_digest?, profile_digest?,
  reason_codes)`.
- `EffectiveDisciplinePackageV1(discipline_id, display_name, availability,
  allowed_actions, binding_state?, package_key?, package_version?,
  descriptor_digest?, project_configuration_revision?)` and its Project list,
  bounded to the seven Core catalog Disciplines.
- `WorkspacePackageApplicabilityV1(workspace_id, project_id,
  legacy_discipline, canonical_discipline_id?, binding_state,
  package_key?, package_version?, descriptor_digest?,
  project_configuration_revision?, effective_standing?)`.
- `PackageConfigurationAuditPageV1(items, next_cursor?)`, where each item is
  the minimized section-16 event schema and never contains descriptor JSON.

Dates are RFC 3339 UTC, enumeration literals are uppercase as defined here,
and every digest has its semantically named field. The opaque cursor binds
Organization, filters, sort key and page size with server integrity protection;
it expires after 15 minutes and cannot be replayed for another scope.

Focused remediation adds no request or response field. A caller still selects
a profile and exact packages; Core derives the matching combination internally.
Project/Workspace responses continue exposing the new current Project revision
after an atomic rebind, so a committed response cannot describe a stale
Workspace pointer.

Supported summaries expose only current release product metadata and compiled
frontend keys, not another tenant's enablement. Historical descriptors are
returned only as provenance referenced by an authorized Project/Workspace, not
through general discovery.

Errors use existing HTTP semantics plus a stable safe `code`:

- `401` unauthenticated;
- protected `404` for foreign/inaccessible Project/Workspace/Organization;
- `403 CONFIGURATION_ADMIN_REQUIRED` only after same-scope existence and role
  are established;
- `409` for version conflict, historical/unsupported selection, missing Project
  configuration, incompatible set, bound-workspace removal or unavailable
  discipline;
- `422 INVALID_PACKAGE_CONFIGURATION` for malformed bounded input; and
- `503 REGISTRY_UNAVAILABLE` only for invalid/drifted trusted infrastructure.

Expected future-unavailable and unresolved GET states return `200` with their
truthful state, not `500`. Error bodies contain no foreign keys, versions,
configuration facts or collision operands.

## 15. Authorization composition and non-disclosure

Every operation applies predicates in this order, stopping on failure:

1. authenticate trusted principal;
2. derive active Organization from authenticated server context;
3. resolve and authorize Project/Workspace engineering-data scope, returning
   protected not-found before package facts;
4. authorize source-owner aggregate operation (Context/Object/etc.);
5. verify trusted registry deployment support and exact version standing;
6. verify Organization configuration;
7. verify Project exact selection/profile;
8. verify Workspace applicability/binding when scoped to a Workspace;
9. call the future entitlement predicate where the operation declares it; and
10. invoke the owning Core service or statically registered package adapter.

Organization-admin role checks occur after active Organization derivation.
Package discovery cannot enumerate tenant configuration. Enabling a package
does not grant Project, Workspace, Object, Evidence, Report, Memory or source-
owner access. Multiple package permissions intersect; they are never unioned
to broaden data authority.

## 16. Organization-scoped package Audit (`A051-OBS-02`)

Create `package_configuration_audit_events`, not a JSON convention on the
current generic global listing:

| Column | Contract |
|---|---|
| `event_id` | UUID PK, server-generated |
| `organization_id` | UUID FK NOT NULL; leading tenant key |
| `project_id`, `workspace_id` | existing ID types, nullable, Organization-consistent FKs |
| `actor_user_id` | existing User FK NOT NULL |
| `category` | `ORG_CONFIGURATION`, `PROJECT_CONFIGURATION`, `WORKSPACE_BINDING` |
| `action` | closed values enable/disable/configure/reconfigure/unconfigure/upgrade/downgrade/rollback/bind/rebind |
| `outcome` | `SUCCEEDED`; rejected attempts go to security telemetry, not transaction Audit |
| package fields | nullable exact key/version; no generic overloaded identity |
| provenance | separately named registry, descriptor-set and profile digests |
| versions | nullable before/after configuration versions/revisions |
| `metadata` | bounded JSONB, canonical minimized keys only |
| `correlation_id`, `occurred_at` | UUID and server UTC timestamp |

Indexes are `(organization_id, occurred_at DESC, event_id DESC)` and
`(organization_id, project_id, occurred_at DESC, event_id DESC)`. Metadata may
contain sorted changed package keys, safe reason code and rationale digest; it
must not contain engineering content, report/evidence bodies, foreign tenant
facts, secrets, tokens, full descriptors or hidden collision operands.

Organization configuration Audit is readable only by active-org admin. Project
configuration history is visible through the Project configuration response to
an authorized Project reader, while the Audit endpoint itself remains admin-
only. Audit insertion shares the mutation transaction and failure rolls back
the mutation. There is no delete/update API. Retention must be at least the
lifetime of referenced Project configuration and cannot remove events required
to interpret retained revisions; a later global retention policy may archive
whole Organization-scoped events without exposing them.

This tenant table contains only truthfully Organization-scoped configuration
and binding events. Registry installation, activation and current-release
switch are global deployment lifecycle facts and must never be copied once per
Organization or assigned a fabricated Organization ID. Their durable release
provenance is the source-controlled `RegistryReleaseManifestV1`, the installed
`discipline_package_registry_releases` row and its activation transaction;
their operational event evidence is the deployment orchestrator's structured
release log/attestation carrying release ID, RegistryDigest, actor/service
identity, correlation ID, outcome and UTC time. That evidence is not exposed by
the tenant Audit API. PATCH-051 adds no second global Audit table; PATCH-060 may
govern longer-term deployment qualification/retention without changing this
tenant boundary.

## 17. Descriptor and contribution contract

`DisciplinePackageDescriptorV1` is strict/frozen and contains:

- `schema_version=1`, package key/version, primary Discipline, Core contract
  range, display metadata, EntitlementKey and adapter ID;
- dependencies and conflicts as exact package/version ranges from a closed
  comparator vocabulary (no arbitrary expressions);
- closed contribution sections: taxonomy families, object types, relationship
  types, Context subject/contribution kinds, engineering input declarations,
  deliverable declarations, Evidence requirements, deterministic rule hook
  IDs, standards applicability hook IDs, cross-discipline interface
  declarations, Human role requirements, authorization requirement IDs,
  frontend metadata, resource declaration, migration compatibility and
  conformance evidence;
- each declaration has stable typed ID, version, owner, ordinal where ordered,
  display metadata and the minimum schema-specific fields; unknown fields fail.

Hook IDs resolve only through the descriptor's statically registered adapter.
Descriptors contain no code, import path, SQL, URL fetch, template expression,
prompt, arbitrary regex or executable UI. PATCH-051's production descriptor set
does not populate Electrical, Instrumentation or Control operational behavior.

Every contributed item contains `id` (the section's typed ID),
`schema_version=1`, `ordinal` (`1..section limit`), display name and optional
description. Section-specific fields are closed:

| Section | Additional exact fields |
|---|---|
| taxonomy family | parent family ID or null; owner `CORE`/`PACKAGE`; collision namespace |
| object type | family ID; lifecycle ID; required Context kind IDs; authority requirement IDs |
| relationship type | source/target object-family sets; direction; cardinality; lifecycle ID |
| Context contribution | Context kind ID; allowed subject kinds; value schema ID; required/optional |
| engineering input | input type ID; Context/Evidence source kind; required/optional; max occurrences |
| deliverable | deliverable type ID; required input IDs; output representation IDs; Human acceptance requirement |
| Evidence requirement | evidence kind; minimum count; applicable operation ID; Human verification required boolean |
| deterministic rule hook | hook ID/version; input/output schema IDs; max findings; timeout milliseconds |
| standards hook | exact `StandardsApplicabilityHookV1` shape in section 20 |
| cross-discipline interface | exact `InterfaceDeclarationV1` shape in section 20 |
| role requirement | operation ID; accepted existing Human role IDs; minimum authority predicate ID |
| authorization requirement | operation ID; source-owner policy ID; package policy ID; composition is intersection |
| frontend metadata | precompiled route/component/navigation keys; visibility predicate ID; no path/code |
| resource declaration | nonnegative integer counters for every tabled budget; adapter timeout/memory class IDs |
| migration compatibility | exact from/to versions; direction; migration guard ID; reversible boolean |
| conformance evidence | vector ID; contract/suite version; expected-result digest; reviewed source reference |

Item IDs are `1..128` characters matching `^[a-z][a-z0-9_.-]*$`;
descriptions are at most 2,000 characters; collections are duplicate-free and
sorted. Collision namespaces are explicit (`discipline`, `taxonomy_family`,
`object_type`, `relationship_type`, `context_kind`, `rule_hook`,
`interface_type`, `frontend_key`), so equal text in unrelated namespaces is
not a collision and equal identity in one namespace is.

The following conservative Commercial V1 limits apply per registry release
unless stated otherwise:

| Resource | Limit |
|---|---:|
| all registered descriptor versions / executable versions | 32 / 16 |
| descriptor canonical bytes / total registry canonical bytes | 256 KiB / 4 MiB |
| profiles / combinations per profile / selected packages per combination or Project | 32 / 32 / 8 |
| dependencies / conflicts per descriptor | 8 / 8 |
| dependency depth / graph visits | 4 / 32 |
| taxonomy families / object types / relationship types per descriptor | 32 / 256 / 128 |
| Context kinds / engineering inputs / deliverables | 64 / 128 / 128 |
| Evidence requirements / deterministic rule hooks | 64 / 128 |
| standards hooks / cross-discipline interfaces | 32 / 128 |
| role requirements / authorization requirements | 32 / 32 |
| frontend routes / navigation items / component keys | 32 / 32 / 64 |
| migration compatibility entries / conformance vectors | 16 / 256 |
| Organization selections / Project selections | 16 / 8 |
| metadata description / rationale | 2,000 chars / 2,000 chars |
| API list page supported / Audit | 50 / 100 |

These limits cover the three planned V1 packages with substantial headroom
while bounding startup, graph and payload work. A source release exceeding any
registry/contribution limit fails validation/readiness. A request exceeding a
configuration/API bound is `422`; an otherwise valid combination exceeding an
aggregate budget is `409 RESOURCE_LIMIT_EXCEEDED`. Results are never silently
truncated except cursor-paginated list endpoints.

## 18. Frontend contract

The effective response contains, per canonical Discipline:
`discipline_id`, server display label, availability (`OPERATIONAL_AVAILABLE`,
`FUTURE_UNAVAILABLE`, `HISTORICAL_ONLY`, `LEGACY_UNRESOLVED`), allowed action
codes, optional authorized package summary/provenance, and only precompiled
`frontend_component_keys`/`route_keys`.

A source-controlled frontend map resolves keys to bundled SATCO components.
Unknown keys render no component and emit safe telemetry. Descriptors cannot
supply import paths, source, HTML, JavaScript, URLs, bundles or customer UI.

The Projects page must replace its five-value literal selector with the
effective Project response. It must show Electrical, Instrumentation, Control &
Automation, Mechanical, Civil and Process truthfully; Control is no longer
omitted. E/I/C create actions are disabled with a safe configuration-required
reason until operationally available. Future Disciplines remain visible only
as unavailable when authorized, never presented as operational. During the
compatibility window, outbound legacy Workspace create values remain
`electrical`, `instrumentation`, `control`, `mechanical`, `civil`, `process`.

## 19. Existing capability integration ports

Core owns these provider-neutral, typed ports; package adapters return bounded
declarations or validation findings and never repositories/sessions:

- `PackageContextContributionPort`: declares classifications/requirements;
  Context service retains subject, observation and authorization authority.
- `PackageObjectContributionPort`: declares trusted type/family metadata;
  Engineering Object service retains canonical aggregate ownership.
- `PackageRelationshipContributionPort`: declares allowed typed relations;
  Relationship service retains endpoint and lifecycle validation.
- `PackageInterfaceDeclarationPort`: exposes typed interface/dependency/
  consistency/change-impact declarations; Interface Commitment remains the
  authoritative record and PATCH-053 owns reasoning.
- `PackageEvidenceRequirementPort`: declares evidence requirements only;
  Evidence remains canonical and authorization-scoped.
- `PackageRuleContributionPort`: invokes only static deterministic hook IDs;
  Guidance remains advisory and its accepted authority is unchanged.

PATCH-051 does not relax existing hard-coded Object/Relationship database
constraints merely because a descriptor declares a value. A later operational
package migration must add a trusted catalog/projection and constraint change
under its own accepted design before such a value becomes writable.

Package provenance DTOs may be attached additively to future generated
Evidence/Report inputs when materially causal: exact Project revision,
PackageKey/version, DescriptorDigest, profile digest and RegistryDigest
observed. They do not replace source provenance. Technical Report Human
acceptance and accepted report digests remain authoritative; no accepted report
snapshot is changed. Organizational Memory admits only through its accepted
Report boundary. Packages create no parallel Evidence, Report, Memory, Context,
Object, Relationship or Guidance store.

## 20. Future seams only

Standards hooks are only
`StandardsApplicabilityHookV1(hook_id, version, input_schema_id,
output_schema_id, max_results, timeout_ms)` resolved to static adapters. They
contain no registry, clause, document, retrieval or compliance logic; PATCH-054
owns those capabilities.

Cross-discipline declarations are only
`InterfaceDeclarationV1(interface_type_id, source_discipline_id,
target_discipline_id, dependency_kind, consistency_check_id?,
change_impact_hook_id?, version)`. They perform no graph reasoning, conflict
resolution or change propagation; PATCH-053 owns behavior.

The Core-owned future entitlement port is:

```text
evaluate(
  trusted_organization_id,
  trusted_deployment_id,
  package_key,
  entitlement_key,
  operation: CONFIGURE | EXECUTE | HISTORICAL_READ
) -> NOT_REQUIRED | PERMITTED | DENIED | UNAVAILABLE
```

PATCH-051 supplies only a source-controlled non-commercial adapter returning
`NOT_REQUIRED`; it defines no signed format, seat, billing, validity or grace
logic. The port runs after data authorization and configuration and can never
grant them. A future `DENIED` blocks configure/execute but not authorized
historical interpretation; `UNAVAILABLE` fails closed for configure/execute and
returns a safe expected-unavailable state. PATCH-059 alone may replace the
adapter and define commercial enforcement.

## 21. Transactions and concurrency

### 21.1 Cross-process Registry/configuration guard

All processes sharing the PostgreSQL database use the same immutable two-key
transaction advisory-lock identity `(1396790339, 51)`, where `1396790339` is
the signed 32-bit namespace key for SATCO package governance and `51` is the
PATCH contract key. A process-local mutex is prohibited.

- A Registry projection install/activation transaction first calls
  `pg_advisory_xact_lock(1396790339, 51)` in **exclusive** mode. While holding
  it, the transaction validates and writes the derived release projection,
  verifies source digests, marks exactly the prior current row false and the
  new row true, binds the deployment correlation ID to the release row, and
  commits. The Registry switch linearizes at that database commit. Only after
  commit may the orchestrator emit successful activation evidence; rollback
  leaves the former release current and emits only a failed-attempt operations
  record, never a successful switch.
- Every Organization configuration mutation and every Project configuration/
  rebind mutation first calls
  `pg_advisory_xact_lock_shared(1396790339, 51)`. While holding it through
  commit, the transaction reads the one current Registry row/digest, validates
  standing and compatibility, performs its writes and scoped Audit, and
  commits. Its authority change linearizes at that database commit. The shared
  lock prevents an exclusive Registry switch between validation and commit;
  different configuration transactions may still proceed subject to their
  tenant/Project row locks.

Transaction-scoped locks release automatically on commit or rollback and work
across API workers, deployment jobs and hosts connected to the same database.
Both Registry switch and configuration paths set the governed database
`lock_timeout` to 5 seconds before acquisition. Configuration timeout,
serialization or deadlock failure retries the complete transaction at most two
times, reacquiring the guard and rereading all state; the third failure is safe
`409 CONCURRENT_UPDATE` with no partial mutation. Registry activation does not
retry inside the transaction: it rolls back, preserves the old current release,
marks the deployment attempt failed in operations evidence and requires an
operator/orchestrator retry.

### 21.2 Global lock order

No path may acquire these resources in another order:

1. Registry/configuration advisory guard: exclusive for Registry switch,
   shared for configuration;
2. current Registry release/projection rows (read for configuration; ordered
   writes for Registry activation);
3. Organization configuration head and selections: `FOR UPDATE` for an
   Organization replacement, `FOR SHARE` for a Project change;
4. Project row, then Project configuration head `FOR UPDATE`;
5. current `OPERATIONAL_PACKAGE_BOUND` Workspaces ordered by Workspace ID;
6. new immutable Project revision/selections, current Workspace binding rows,
   Project head, then scoped Audit inserts.

Registry activation never attempts an Organization, Project, Workspace or
tenant Audit lock while holding the exclusive guard. Configuration never
upgrades the shared guard to exclusive. Organization replacement takes no
Project/Workspace locks; its `FOR UPDATE` Organization head conflicts with a
Project change's `FOR SHARE`, ensuring Organization enablement cannot change
mid-Project commit. These rules prevent a deterministic inverse lock cycle.

### 21.3 Organization and Workspace creation transactions

Organization replacement compares expected version, validates the complete
new set against the guarded current Registry, updates selections/head and
appends Organization Audit in one transaction.

Workspace creation acquires the shared guard, guarded Registry and Organization
reads, then locks the Project/head and resolves the matching current selection.
It inserts the Workspace with the same head revision and relies on both
canonical and legacy uniqueness. A unique race becomes
`409 WORKSPACE_ALREADY_EXISTS`; it cannot insert against a superseded Project
head.

### 21.4 Atomic Project/Workspace rebind

After expected-version validation, a Project configuration transaction locks
all current `OPERATIONAL_PACKAGE_BOUND` Workspaces in ID order and treats them
all as affected. It evaluates the full target configuration and every
Workspace-specific exact key/Discipline/migration invariant before inserting
authority changes. If any Workspace lacks a valid target selection or guard,
the transaction returns `409 WORKSPACE_REBIND_INCOMPATIBLE` and changes
nothing.

On success it inserts revision N+1 and all selections, updates every affected
Workspace's derived revision pointer to N+1, advances the Project head, inserts
the Project and per-Workspace Audit events, and commits once. The database
commit is the single linearization point. Readers observe either the complete
old head/bindings or complete new head/bindings. The deferred consistency
trigger rejects a commit where an operational Workspace is stale, a Workspace
rebinding lacks the corresponding head/selection, or a Project head advances
without all operational bindings. Rollback restores all uncommitted changes;
immutable revision N and its old bindings remain authoritative. Forward
rollback to an earlier package set uses this same N+2 transaction, never a
pointer rewind.

Audit uses the caller's unit of work and must not call the current helper that
commits independently. No Audit success row can commit without its authority
change, and an Audit failure aborts the same transaction.

## 22. Failure semantics

| Condition | Required behavior |
|---|---|
| invalid/tampered descriptor or adapter mismatch | fail startup/readiness; no package configure/execute |
| DB projection mismatch | `503 REGISTRY_UNAVAILABLE`; historical projection reads only if retained row digest validates |
| unsupported/historical-only new selection | safe `409`; no mutation |
| incompatible package set/resource overrun | deterministic `409` plus safe reason codes |
| unauthorized or foreign configuration | `401`, protected `404`, or same-scope `403`; no package facts |
| unresolved legacy identity | read `LEGACY_UNRESOLVED`; block binding/execution, not historical read |
| missing Project configuration | `409 PACKAGE_CONFIGURATION_REQUIRED` for operational create/execute |
| future-unavailable Workspace | read `200 FUTURE_UNAVAILABLE`; operational mutation `409` |
| current non-commercial entitlement adapter | `NOT_REQUIRED`; no commercial claim |
| future entitlement unavailable | fail closed configure/execute; authorized historical read remains available |
| package Audit insert failure | rollback configuration/binding mutation |
| profile combination duplicate/member collision | fail registry startup/projection install; no configuration path |
| one affected Workspace cannot rebind | `409 WORKSPACE_REBIND_INCOMPATIBLE`; rollback Project revision, all Workspace updates and Audit |
| advisory guard timeout/configuration serialization exhaustion | retry whole transaction at most twice, then `409 CONCURRENT_UPDATE`; no stale commit |
| Registry activation guard timeout/failure | rollback activation, retain old current release, failed operations evidence; deployment retry required |

## 23. Security threat review

| Threat | Control |
|---|---|
| source/descriptor tampering | reviewed immutable source, canonical digest, static adapter equality, release binding |
| database projection tampering | row-set/hash verification, restricted roles, readiness failure |
| cross-tenant enumeration/frontend disclosure | active-org derivation, data authorization before package facts, protected 404, scoped responses |
| configuration privilege escalation | admin/Project-owner checks, trusted actor, optimistic version, atomic Audit |
| permission union | ordered intersection of independent predicates; package never grants source access |
| identity/contribution collision | typed namespaces, exact source maps, whole-registry collision validation |
| digest confusion | separate types, fields, tables and canonical inputs; negative conformance vectors |
| resource exhaustion | numeric descriptor, graph, payload, page and retry bounds; startup rejection |
| legacy alias abuse | source-qualified exact mapping; no fuzzy/global mapping; raw preservation |
| Audit disclosure | Organization-leading key/index, admin-only scoped endpoint, minimized schema |
| rollback/downgrade abuse | explicit compatibility/migration guards, new revision, Audit; never head rewind |
| frontend code injection | precompiled allow-list keys only; no descriptor code/import/HTML |
| stale Workspace authority | all operational bindings advance atomically with the Project head; deferred consistency trigger |
| Registry/configuration race | shared/exclusive database transaction advisory guard across all processes |

## 24. Future test and conformance design

IDS-051 must turn these acceptance vectors into tests without reducing them:

1. value-object positive/negative boundaries and cross-type non-equality;
2. canonical JSON/digest golden vectors, permutation stability and semantic
   separation for all four provenance digests plus subordinate combination-
   digest vectors;
3. empty registry success; duplicate/collision/bad adapter/dependency cycle/
   depth/resource/tamper failures; multiple combinations with one PackageKey at
   different versions across combinations; duplicate member and duplicate
   semantic-combination rejection;
4. source-to-projection exact match and missing/extra/changed row failure;
5. executable versus historical lifecycle, exact selection, explicit upgrade,
   constrained downgrade and forward rollback revision; version change with
   multiple affected Workspaces; one invalid Workspace rolling back the whole
   Project/head/binding/Audit transaction;
6. Organization admin-only configuration, version races, disable-in-use,
   tenant isolation, atomic package Audit and concurrent Registry switch versus
   Organization configuration commit;
7. valid empty Project, nonempty configured Project, invalid empty revision,
   profile mismatch and bound-Workspace unconfigure rejection;
8. one Workspace per canonical Discipline, inherited Project version, no
   independent override, concurrent Project configuration attempts,
   concurrent creation and upgrade/create serialization, and Registry switch
   versus Project/rebind commit with no stale or partial Workspace state;
9. every exact legacy mapping, raw round-trip, no fuzzy/case mapping, future
   unbound and unresolved read/block behavior;
10. migration preflight stop vectors, six-value backfill counts, constraint
    validation, downgrade safety and historical Report/Memory/Audit checksums;
11. every API success/error/auth-order path, cursor bounds and non-disclosure;
12. deterministic compatibility reason/order vectors and worst-case bound;
13. frontend Control reconciliation, unavailable truth, compiled key allow-list
    and unknown-key safe rendering;
14. owner-preservation tests for Context/Object/Relationship/Interface/
    Evidence/Report/Memory/Guidance;
15. tenant Audit vectors proving authority/Audit rollback atomicity and that
    global Registry lifecycle evidence never appears in Organization Audit; and
16. package conformance fixtures proving a descriptor cannot register until all
    schema, static adapter, budget, authorization, provenance, migration and
    negative security vectors pass.

Expected performance gates on representative PostgreSQL data are: registry
validation of maximum 4 MiB manifest under 1 second at startup; compatibility
evaluation p95 under 50 ms CPU; effective Project state p95 under 200 ms; and
100-event scoped Audit page p95 under 300 ms. IDS must define the controlled
environment and query-plan assertions; failure blocks implementation acceptance
rather than weakening limits.

## 25. Expected implementation and test manifest

This is a forecast for later IDS/Implementation Plan authorization, not current
write authority.

Expected new production modules:

- `backend/app/discipline_packages/contracts.py`
- `backend/app/discipline_packages/registry.py`
- `backend/app/discipline_packages/descriptors/__init__.py`
- `backend/app/enums/discipline_package.py`
- `backend/app/schemas/discipline_package.py`
- `backend/app/models/discipline_package.py`
- `backend/app/ports/discipline_package.py`
- `backend/app/adapters/discipline_package_registry.py`
- `backend/app/repositories/discipline_package_repository.py`
- `backend/app/services/discipline_package_service.py`
- `backend/app/dependencies/discipline_package.py`
- `backend/app/api/v1/routers/discipline_packages.py`

Expected modified production files are `backend/app/core/config.py`,
`backend/app/main.py`, model/enum/schema package `__init__.py` registries, the
existing Engineering Workspace model/schema/repository/service/router, the
Project repository/service/schema/router where configuration composition
requires it, and `frontend/src/api/client.ts`, `frontend/src/api/types.ts`,
`frontend/src/pages/ProjectsPage.tsx`. No existing aggregate store changes
owner.

Expected future test files are:

- `backend/tests/test_discipline_package_contracts.py`
- `backend/tests/test_discipline_package_registry.py`
- `backend/tests/test_discipline_package_projection.py`
- `backend/tests/test_discipline_package_compatibility.py`
- `backend/tests/test_discipline_package_service.py`
- `backend/tests/test_discipline_package_api.py`
- `backend/tests/test_discipline_package_security.py`
- `backend/tests/test_discipline_package_migration.py`
- `backend/tests/test_discipline_package_conformance.py`
- `backend/tests/test_discipline_package_performance.py`
- narrowly bounded changes to existing Workspace service/API/security tests
- `frontend/src/test/discipline-packages.test.tsx` and narrowly bounded
  Workspace workflow-test changes.

Expected future migrations are exactly the three named in section 11. Exact
authorized manifests remain an IDS/Implementation Plan decision; this forecast
grants no write authority.

## 26. Human authority and PATCH firewalls

No Package may autonomously approve engineering, accept Reports, admit Memory,
procure, purchase, select vendors, create an authoritative BOM/MTO/BOQ, mutate
accepted authority or resolve engineering/cross-discipline conflicts.

This EDS defines seams only and does not design or implement operational scope
owned by PATCH-052 (E/I/C packages), PATCH-053 (cross-discipline reasoning),
PATCH-054 (standards intelligence), PATCH-055 (Evidence Workbench), PATCH-056
(Methods & Systems), PATCH-057 (Product Experience), PATCH-058 (commercial
authentication/security), PATCH-059 (signed entitlements) or PATCH-060
(deployment qualification).

## 27. Risks, evidence prerequisites and review gate

Focused remediation disposition:

| Finding | Status | Binding resolution |
|---|---|---|
| `EDS051-MAJ-01` | **RESOLVED** | combination-digest member identity supports multiple exact combinations/versions without PK collapse; source profile remains authority |
| `EDS051-MAJ-02` | **RESOLVED** | every operational Workspace advances atomically with a new Project revision or the whole change rolls back |
| `EDS051-MAJ-03` | **RESOLVED** | one PostgreSQL transaction advisory-lock identity serializes Registry switch against every configuration commit across processes |
| `EDS051-MIN-01` | **RESOLVED** | tenant Audit contains no global Registry event; global lifecycle evidence remains release/deployment provenance |

| Risk/evidence prerequisite | Required disposition before implementation |
|---|---|
| no live deployed-data census in EDS environment | IDS/migration manifest must attach per-deployment preflight evidence; unknowns stop |
| current enum/check proliferation | IDS traces each existing constraint/API owner; no global string rewrite |
| registry projection operational complexity | conformance and drift/readiness tests must pass before any descriptor ships |
| historical version support burden | retained descriptor/profile fixtures and historical read tests are release gates |
| cross-capability ownership erosion | port-level dependency checks and owner-preservation tests are mandatory |

The initial review observations remain non-blocking downstream obligations:
live deployed-data census evidence, historical source/release anchoring,
application/migration cutover choreography and exact composite tenant-key/
constraint implementation. This focused amendment creates no additional work
for them and does not change their disposition.

There are no open blocking design questions and no new Critical or Major
finding introduced by remediation. The focused independent re-review verified
the four resolutions and directly impacted persistence, migration, transaction,
Audit and conformance text as `PASS / ACCEPTED`. Human EDS Acceptance is `PASS /
GRANTED`; EDS-051 is **ACCEPTED / COMPLETE** and its EDS Gate is **PASS /
ACCEPTED**. IDS-051 is only eligible for separate Human design authority;
implementation, migrations and PATCH-052 remain unauthorized.

## 28. Exact next resume point

Stop after Human EDS acceptance. The exact next resume point is separately
granted **Human IDS-051 design authority**. IDS eligibility is not authority:
do not begin IDS-051, implementation planning, implementation, migrations or
PATCH-052.

## 29. Append-only focused persistence reconciliation

Under **HUMAN FOCUSED EDS-051 PERSISTENCE RECONCILIATION AUTHORITY: GRANTED**,
the persistence root cause of Independent IDS finding `IDS051-MAJ-01` is
resolved by the binding focused reconciliation:

`EDS-051-Shared-Multi-Discipline-Core-and-Discipline-Package-Contract-Focused-Persistence-Reconciliation.md`.

This append-only reconciliation supersedes only the incompatible profile-table
cardinality in sections 6, 8 and 11:

- `discipline_package_compatibility_profiles` retains semantic PK
  `(profile_id, profile_digest)` and no longer owns one `registry_digest`;
- new immutable derived table
  `discipline_package_registry_profile_memberships` has PK
  `(registry_digest, profile_id)`, unique
  `(registry_digest, profile_id, profile_digest)`, and FKs to Registry release
  and semantic profile;
- compatibility-member PK remains
  `(profile_id, profile_digest, combination_digest, package_key)`;
- Project revision FK `(observed_registry_digest, profile_id, profile_digest)`
  targets the new release-membership triple; and
- M1 creates twelve PATCH-051 tables. M2 and M3 remain unchanged.

ProfileDigest remains semantic-content-derived; RegistryDigest remains
release-derived. Source Registry authority, derived projection status,
historical anchoring, public APIs, Architecture-051 and ADR-024 are unchanged.

**FOCUSED EDS-051 PERSISTENCE RECONCILIATION: PASS / COMPLETE.** EDS-051
remains **ACCEPTED / COMPLETE WITH FOCUSED RECONCILIATION** and Human EDS
Acceptance remains valid. `IDS051-MAJ-01` is **EDS ROOT CAUSE RESOLVED / READY
FOR IDS REMEDIATION RECONCILIATION**. The Independent IDS-051 Review remains
`FAIL / STOPPED`; `IDS051-MAJ-02`, `IDS051-MAJ-03`, `IDS051-MIN-01` and
`IDS051-OBS-01` are not changed here.

The exact next resume point is separately authorized focused IDS-051
remediation. Implementation Plan, implementation, migrations and PATCH-052
remain unauthorized/not started.
