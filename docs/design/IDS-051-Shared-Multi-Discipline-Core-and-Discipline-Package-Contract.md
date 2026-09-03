# IDS-051 — Shared Multi-Discipline Core & Discipline Package Contract

## 1. Status, authority and bounded verdict

| Field | Value |
|---|---|
| PATCH | PATCH-051 — Shared Multi-Discipline Core & Discipline Package Contract |
| Human IDS design authority | **HUMAN IDS-051 DESIGN AUTHORITY: GRANTED** |
| ADR basis | ADR-024 `ACCEPTED` |
| Architecture basis | Architecture-051 `ACCEPTED / COMPLETE`; Gate `PASS / ACCEPTED` |
| EDS basis | EDS-051 `ACCEPTED / COMPLETE WITH FOCUSED RECONCILIATION`; Gate `PASS / ACCEPTED` |
| Minimum focused authorization remediation authority | **HUMAN MINIMUM FOCUSED IDS-051 AUTHORIZATION REMEDIATION AUTHORITY: GRANTED** |
| Human IDS Acceptance | **HUMAN IDS-051 ACCEPTANCE: PASS / GRANTED** |
| IDS-051 | **ACCEPTED / COMPLETE** |
| IDS Gate | **PASS / ACCEPTED** |
| Independent IDS review | FAIL / STOPPED; Critical/Major/Minor/Observation `0/3/1/1` |
| Focused IDS remediation | **PASS / COMPLETE** (historical); first re-review retained `IDS051-MAJ-02`; `IDS051-MAJ-01`, `IDS051-MAJ-03`, `IDS051-MIN-01` remain RESOLVED / CLOSED |
| Focused Independent IDS re-review | **FAIL / STOPPED**; new Critical/Major/Minor/Observation `0/1/0/0`; `IDS051-FRR-MAJ-01` |
| Focused authorization remediation | **PASS / COMPLETE**; `IDS051-MAJ-02` and `IDS051-FRR-MAJ-01` RESOLVED |
| Second Focused Independent IDS re-review | **PASS / ACCEPTED**; scoped findings RESOLVED / CLOSED; new Critical/Major/Minor/Observation `0/0/0/0` |
| Implementation Plan | NOT STARTED / ELIGIBLE FOR SEPARATE HUMAN DESIGN AUTHORITY |
| Implementation / migrations | NOT AUTHORIZED / NOT CREATED |
| PATCH-052 | NOT STARTED |

**HUMAN IDS-051 ACCEPTANCE: PASS / GRANTED.** The Human accepts the final
reviewed IDS after the Second Focused Independent IDS Re-review `PASS /
ACCEPTED`, with final Critical/Major/Minor/new Observation `0/0/0/0`, no
blocking finding and no required further IDS amendment. IDS-051 is
**ACCEPTED / COMPLETE** and its IDS Gate is **PASS / ACCEPTED**. This records
acceptance only: Implementation Plan-051 is eligible for separately granted
Human design authority but remains not started; implementation, migrations,
deployment, PATCH closure and PATCH-052 remain unauthorized or unstarted.

The focused authorization remediation remains `PASS / COMPLETE`. It closed
the remaining `IDS051-MAJ-02` / `IDS051-FRR-MAJ-01` blocker by holding mutable
User, membership and Organization authority stable through guarded commit. It
did not change Architecture-051, ADR-024 or EDS-051. Both the initial
Independent IDS Review and first Focused Independent IDS Re-review `FAIL /
STOPPED` records remain immutable historical evidence.

The initial Independent EDS Review `FAIL / STOPPED`, its findings
`EDS051-MAJ-01`, `EDS051-MAJ-02`, `EDS051-MAJ-03`, `EDS051-MIN-01`, focused
remediation and the Focused Independent EDS Re-review `PASS / ACCEPTED` remain
historical evidence. All four findings remain `RESOLVED / CLOSED` and are not
reopened by repository inspection.

The Independent IDS Review `FAIL / STOPPED` found `IDS051-MAJ-01` profile/
release persistence cardinality, `IDS051-MAJ-02` guarded Session/UoW/Audit
composition, `IDS051-MAJ-03` Registry projection DB authority,
`IDS051-MIN-01` Workspace-selectable count wording and `IDS051-OBS-01` future
deployment evidence. Under explicit Human focused authorities, the EDS root
cause and all three IDS Major findings are resolved below. The first focused
re-review nevertheless found that the `IDS051-MAJ-02` authorization reread was
not commit-stable and registered `IDS051-FRR-MAJ-01`. This second focused
remediation resolves that one remainder only. The Minor remains closed; the
Observation remains open/non-blocking and no evidence is fabricated.

## 2. Actual repository baseline

Inspection on 2026-08-29 establishes:

| Concern | Actual repository evidence | IDS reuse decision |
|---|---|---|
| Backend structure | `backend/app/{models,repositories,services,schemas,ports,adapters,dependencies,api/v1/routers}` | use the existing layered root-router pattern; add no parallel application architecture |
| Session | `backend/app/core/database.py` exposes synchronous SQLAlchemy `SessionLocal`; SQL queries autobegin; request authorization already queries before mutation service entry | request Session is read/auth composition only; each guarded mutation/retry owns a fresh `SessionLocal` Session through a PATCH-051 UoW and receives only the identity/context DTO, never request-bound ORM objects or permission results |
| Project | `models/project.py`, `repositories/project_repository.py`, `services/project_service.py`, `schemas/project.py`, `routers/projects.py` | Project remains exact package-selection authority; existing Project owner policy is composed |
| Workspace | `models/engineering_workspace.py` uses `discipline String(32)`, six closed values and unique `(project_id, discipline)` | add four accepted fields and derived binding behavior; preserve raw field and existing owner/membership rules |
| Authorization persistence | `models/user.py`: `users.is_active`, `role`, `auth_version`, `version`; `models/organization.py`: `user_organization_memberships(user_id, organization_id)`, `is_enabled`, `is_selected`, `version`, and `organizations.is_active`; `dependencies/auth.py` performs request-time checks | request results establish identity only; guarded writes lock and reread the exact rows below |
| Organization | `models/organization.py`; active membership derived by `dependencies/auth.py` | Organization ID is bounded request context, never proof of current authority |
| Revocation | `services/onboarding_service.py::mutate_member()` changes `User.role`, `User.is_active`/`auth_version` and membership enable/selection/version; password/credential flows also increment `auth_version`; no production Organization-disable service exists | serialize on the same authority rows and narrowly normalize mixed multi-row lock order; add no authorization framework |
| Audit | `models/audit_log.py`; `services/audit_service.create_audit_log()` calls `commit()`; generic reader is global | create scoped append-only package Audit; add a narrow non-committing generic Audit staging function for guarded Workspace creation while leaving unrelated committing callers unchanged |
| Database roles | Alembic requires migration and runtime roles to differ; protected capabilities use explicit `REVOKE`/column grants and role tests | retain schema ownership with migration principal, provision a separate Registry installer principal outside Alembic, and make ordinary runtime projection access SELECT-only |
| Existing owners | Context, Objects, Relationships, Interface Commitments, Evidence, Reports, Memory and Guidance have separate models/services/ports | integrate through declarations/ports only; no duplicate stores |
| Readiness | `main.py` startup hook and `/health/ready`; `core/operations.py` provides existing operational readiness | add a package Registry readiness provider and compose it without disclosing details |
| Frontend | `frontend/src/api/{client,types}.ts`; `pages/ProjectsPage.tsx`; `pages/OrganizationAdminPage.tsx` | add typed client/state and bounded panels; keep compiled component mapping |
| Workspace UI | `ProjectsPage.tsx` offers electrical, mechanical, instrumentation, civil and process | replace literal selector with effective server state and restore Control & Automation |
| Tests | capability-specific backend suites plus `frontend/src/test` | create bounded PATCH-051 suites and narrowly extend Workspace/Project regressions |
| Alembic | `backend/migrations`; local `backend/.venv/bin/alembic heads` | current sole head is **`e04700000001`**; future linear revisions are exactly `e05100000001..3` |

No production descriptor for Electrical, Instrumentation or Control &
Automation exists. A valid PATCH-051 release may therefore assemble an empty
operational Registry and must not manufacture operational availability.

## 3. Allowed dependency direction and circular-import controls

The only allowed direction is:

```text
identity + strict contracts + contribution protocols
  -> canonicalization + trusted source Registry + static adapter table
  -> pure compatibility evaluator
  -> persistence repositories/UoW
  -> Registry and configuration application services
  -> Project/Workspace composition + authorization dependencies
  -> FastAPI routers
  -> TypeScript API client/types
  -> precompiled frontend components/pages
```

Rules:

- `discipline_packages/` imports no ORM model, router, tenant repository,
  frontend symbol or customer configuration.
- ORM models import only Core database/types/enums, never services or routers.
- repositories and Audit staging helpers contain SQLAlchemy operations but no
  authorization decisions, digest authority, commit or rollback.
- the outer guarded service retry owns UoW creation; only the UoW may begin,
  commit or roll back; routers translate transport only.
- descriptors depend on frozen contracts and identity types only; Registry
  source authority never depends on its database projection.
- contribution ports expose bounded declarations; existing aggregate services
  remain authoritative and never import package adapters directly.
- the frontend consumes effective server state and maps allow-listed keys; it
  never computes compatibility, authority, version selection or digests.
- entitlement is a port dependency after data/configuration predicates; no
  PATCH-059 implementation leaks into Core.

To avoid cycles, `identity.py`, `contracts.py` and `contributions.py` are leaf
modules. `registry.py` receives the adapter table as an argument.
`compatibility.py` consumes immutable DTOs. `discipline_package_service.py`
depends on repository and ports through constructor protocols.
`dependencies/discipline_package.py` is the sole concrete composition root.
Existing Project/Workspace services receive factories/ports, not a live
request Session. Frozen actor/scope DTOs cross from request authorization into
guarded services; ORM objects do not. The package service never imports those
services.

## 4. Concrete implementation component map

| Action | Exact proposed file | Responsibility and allowed dependencies | Forbidden responsibility |
|---|---|---|---|
| CREATE | `backend/app/discipline_packages/__init__.py` | stable public Core exports only | assembly side effects |
| CREATE | `backend/app/discipline_packages/identity.py` | validated value objects for all EDS identity, revision and digest types | ORM, tenant state, generic digest alias |
| CREATE | `backend/app/discipline_packages/contracts.py` | strict/frozen descriptor, manifest, profile, selection, provenance and resource DTOs | runtime imports, DB access, executable content |
| CREATE | `backend/app/discipline_packages/contributions.py` | bounded taxonomy/object/relationship/Context/input/deliverable/Evidence/rule/standards/interface/role/auth/frontend/resource/migration/conformance schemas | operational package content or aggregate ownership |
| CREATE | `backend/app/discipline_packages/canonical.py` | NFC validation, canonical JSON and semantically typed SHA-256 functions | permissive normalization or tenant access |
| CREATE | `backend/app/discipline_packages/registry.py` | deterministic assembly, validation, release/profile indexing and historical source lookup | DB projection authority, scanning, plugins or network |
| CREATE | `backend/app/discipline_packages/compatibility.py` | pure ordered compatibility evaluation and closed reason codes | AI, I/O, mutation or authorization |
| CREATE | `backend/app/discipline_packages/legacy.py` | exact source-qualified legacy translation | fuzzy/global mapping or writes |
| CREATE | `backend/app/discipline_packages/conformance.py` | reusable descriptor/package conformance harness | operational packages or test-only production registration |
| CREATE | `backend/app/discipline_packages/descriptors/__init__.py` | explicit immutable release table | directory scanning |
| CREATE | `backend/app/discipline_packages/descriptors/releases/__init__.py` | explicit release-ID-to-manifest map retaining historical releases | “latest” alias or dynamic discovery |
| CREATE | `backend/app/discipline_packages/descriptors/releases/release_051_core_v1.py` | empty-operational-package PATCH-051 source manifest and expected digest | E/I/C behavior |
| CREATE | `backend/app/enums/discipline_package.py` | persistence/transport closed states and actions | identity validation or policy |
| CREATE | `backend/app/schemas/discipline_package.py` | all accepted strict API DTOs and opaque cursor envelopes | actor/Organization input fields |
| CREATE | `backend/app/models/discipline_package.py` | twelve reconciled tables only | canonicalization, commits or authorization |
| CREATE | `backend/app/ports/discipline_package.py` | contribution ports, entitlement port, migration guard and deployment support protocols | concrete signed entitlement logic |
| CREATE | `backend/app/adapters/discipline_package_registry.py` | explicit static adapter table, source release loader, `NOT_REQUIRED` entitlement adapter | entry points, customer adapters, runtime download |
| CREATE | `backend/app/repositories/discipline_package_repository.py` | guarded Registry/configuration queries, row locks, immutable inserts, scoped Audit reads | commit, policy or digest acceptance |
| CREATE | `backend/app/repositories/discipline_package_unit_of_work.py` | create/close one fresh Session per attempt; begin/commit/rollback; expose repositories and same-Session advisory guard | request Session reuse, nested transaction completion or independent Audit commit |
| CREATE | `backend/app/services/discipline_package_registry_service.py` | installer-principal install/reconcile/activate projection, historical validation, readiness and role/grant status | tenant Audit, runtime-principal projection mutation or automatic deployment retry |
| CREATE | `backend/app/services/discipline_package_service.py` | supported/effective/applicability reads, preflight and authorization-neutral orchestration | Project/Workspace owner policy |
| CREATE | `backend/app/services/discipline_package_configuration_service.py` | Organization replace, Project configure/remove, atomic Workspace rebind and package Audit | entitlement implementation or independent Workspace selection |
| CREATE | `backend/app/dependencies/discipline_package.py` | trusted actor/scope composition, source-owner guards and service construction | permission union or global mutable singleton state |
| CREATE | `backend/app/exceptions/discipline_package.py` | closed domain-to-safe transport exceptions | foreign identifiers or descriptor details |
| CREATE | `backend/app/api/v1/routers/discipline_packages.py` | accepted thin routes only | transactions, compatibility or new endpoints |
| CREATE | `backend/scripts/discipline_package_preflight.py` | read-only live census and signed/digested JSON artifact generation | mutation or invented PASS |
| CREATE | `backend/scripts/discipline_package_registry.py` | deployment-only install/reconcile/activate CLI using the externally supplied Registry-installer credential and exclusive UoW | HTTP exposure, schema migration or runtime credential reuse |
| MODIFY | `backend/app/models/{__init__.py,project.py,engineering_workspace.py}` | model registration, supporting composite keys and four Workspace fields | owner changes |
| MODIFY | `backend/app/repositories/{project_repository.py,engineering_workspace_repository.py}` | exact scope/lock/binding primitives only | package policy or commit |
| MODIFY | `backend/app/services/engineering_workspace_service.py` | delegate create binding/applicability to package configuration service in same UoW | choosing a PackageVersion |
| MODIFY | `backend/app/schemas/engineering_workspace.py` | additive canonical/binding/provenance output fields | independent package input |
| MODIFY | `backend/app/api/v1/routers/engineering_workspaces.py` | inject request-scoped package composition; preserve routes | duplicate applicability endpoint |
| MODIFY | `backend/app/core/{database.py,operations.py}` | advisory helper primitive and package readiness composition | process-local guard or detail disclosure |
| MODIFY | `backend/app/{main.py,core/config.py}` | router registration, startup assembly settings and validation | environment-selected manifests |
| MODIFY | `backend/app/services/audit_service.py` | add `stage_audit_log()` that adds and optionally flushes without transaction completion; preserve `create_audit_log()` behavior for unrelated callers | global Audit rewrite or commit inside guarded staging |
| MODIFY | `backend/migrations/env.py` | register PATCH-051 model metadata for later authorized migrations | migration execution |

`project_service.py`, `project_repository.py`, `schemas/project.py` and
`routers/projects.py` remain otherwise unchanged because accepted configuration
routes live in the package router/service. Existing Project read/write
authority is reused through ports/repository queries.

## 5. Identity, descriptor, Registry and canonicalization design

`identity.py` defines distinct frozen string/int wrappers for `DisciplineId`,
`PackageKey`, `PackageVersion`, `CoreContractVersion`,
`CompatibilityProfileId`, `EntitlementKey`, `RegistryReleaseId`,
`RegistryDigest`, `DescriptorDigest`, `SelectedDescriptorSetDigest`,
`CompatibilityProfileDigest`, `CompatibilityCombinationDigest`,
`ConfigurationRevision` and `ConfigurationVersion`. Construction applies the
accepted lexical/range rules; cross-type equality is false and serializers use
explicit field names.

`contracts.py` and `contributions.py` use Pydantic frozen models with
`extra="forbid"`, fixed `schema_version=1`, closed literals, immutable tuples
and all EDS bounds. `DisciplinePackageDescriptorV1` contains declarative data
only. Static hook IDs must exist in the adapter capability set and must equal
the descriptor declaration exactly.

`canonical.py` rejects non-NFC input, floats, duplicate semantic members,
unknown fields, insignificant nulls and unordered set representations. It
serializes UTF-8 compact JSON with code-point-sorted keys and documented
array identities. Separate digest functions return separate wrapper types.

Assembly flow in `registry.py` is exact:

1. load the build-selected source release from the explicit Python table;
2. validate manifest and descriptor schemas/bounds;
3. validate exact static adapter registration;
4. deterministically sort descriptors/profiles/members;
5. canonicalize descriptors, combinations, profiles and manifest;
6. compute typed digests and compare embedded expected values;
7. validate identities, dependencies/conflicts, collisions and graph bounds;
8. validate compatibility combinations and resource totals;
9. construct an immutable `TrustedDisciplinePackageRegistryV1`; and
10. hand it to projection reconciliation/readiness.

Any error is a typed `RegistryAssemblyError` with a safe reason code. Startup
logs only release ID, correlation ID and safe code; HTTP readiness emits only
`not_ready`. There is no runtime plugin discovery, import path in a descriptor,
network fetch, expression evaluation or database-originated source Registry.

## 6. Historical Registry anchoring and projection reconciliation

`descriptors/releases/__init__.py` is an append-only explicit mapping from
`RegistryReleaseId` to an immutable source manifest module. Every retained
module carries release ID, Core version, typed RegistryDigest, sorted
descriptor digests, profile digests, membership standings and adapter IDs.
Removal is forbidden while any Project revision or Workspace provenance
references its digest.

The build's expected release ID/digest is source-controlled configuration, not
an environment override. Historical resolution uses stored
`observed_registry_digest` to locate the retained DB projection, then resolves
that digest to the retained source manifest and revalidates exact bytes. It
never substitutes current release material.

`discipline_package_registry_service.py` provides:

- `install_release_projection(registry, correlation_id)`: exclusive guarded
  deployment operation under the Registry-installer principal; insert missing
  immutable release/descriptor/package-membership/semantic-profile/profile-
  membership/member rows, compare the complete row set and atomically activate;
- `reconcile_current_projection(registry)`: read-only exact canonical JSON,
  digest, FK and row-set comparison; for every release it compares exact
  release/profile membership triples separately from referenced semantic
  profile bytes/members; missing, extra or changed is drift;
- `resolve_historical(registry_digest)`: revalidate retained source plus
  projection by release row -> exact release/profile membership -> semantic
  profile/members; returns historical DTOs only, never consults the current
  pointer and never supplies adapters for execution;
- `readiness_status()`: current assembly/projection/Core-contract result plus
  required historical-anchor availability; safe boolean/reason category.

Projection installation preserves all prior releases. Only `is_current` is
mutable. Registry install/activation writes deployment structured evidence
after commit through the existing operational/deployment boundary; it never
writes `package_configuration_audit_events`.

If R1 and R2 contain unchanged semantic profile P/D, R2 installation verifies
and reuses the one immutable `(profile_id,profile_digest)` semantic row and its
member rows, then inserts distinct membership `(R2,P,D)`. It never updates
`(R1,P,D)`. An existing P/D with different canonical bytes or reconstructed
members is drift; a missing, extra or wrong release membership is drift even
when P/D exists globally.

Missing current material or drift is startup/readiness failure and blocks
configuration/execution. Missing historical material referenced by active
data also fails readiness. Missing material referenced only by quarantined
historical data permits startup solely in governed read-only recovery mode;
the affected read returns a safe unavailable provenance state and no adapter
executes.

## 7. Deterministic compatibility evaluator

`compatibility.py` exposes
`evaluate_package_compatibility(CompatibilityInputV1) -> CompatibilityEvaluationV1`.
It is pure and evaluates in this frozen order:

1. lexical identity and one-version-per-key uniqueness;
2. current membership and `EXECUTABLE_SUPPORTED` standing;
3. Organization enablement;
4. Core contract compatibility;
5. sorted dependency traversal, depth at most 4 and visits at most 32;
6. declared conflicts;
7. exact profile combination match by recomputed combination digest;
8. taxonomy and contribution collision sets;
9. migration guard facts; and
10. aggregate resource budgets.

It returns `COMPATIBLE`, `INCOMPATIBLE` or `UNAVAILABLE`, normalized selections,
four authoritative provenance digests and sorted unique accepted EDS reason
codes. The combination digest remains internal. It performs no database I/O,
adapter execution, AI call, authorization or mutation.

## 8. Persistence implementation map — twelve new tables

All models live in `models/discipline_package.py`; all reads/writes are owned by
`discipline_package_repository.py`. The Registry service exclusively writes
tables 1–6 through the deployment-only installer UoW, the configuration
service writes 7–12 through the ordinary runtime UoW, and the read service
reads bounded projections.

| # | Table; lifecycle/authority | PK, tenant key and important integrity | Read/write owner |
|---:|---|---|---|
| 1 | `discipline_package_registry_releases`; append-only except current pointer; derived | PK `registry_digest`; unique `release_id`; partial unique current; Core/digest checks | Registry service / Registry repository |
| 2 | `discipline_package_descriptors`; immutable derived | PK `(package_key,package_version)`; unique digest and provenance triple | Registry service / Registry repository |
| 3 | `discipline_package_registry_memberships`; immutable per release | PK `(registry_digest,package_key,package_version)`; release/descriptor FKs; standing check; lookup index | Registry service / Registry repository |
| 4 | `discipline_package_compatibility_profiles`; immutable semantic derived projection | PK `(profile_id,profile_digest)`; canonical `profile_json`; no release column; digest check | Registry installer / Registry repository |
| 5 | `discipline_package_registry_profile_memberships`; immutable release provenance | PK `(registry_digest,profile_id)`; unique `(registry_digest,profile_id,profile_digest)`; release and semantic-profile FKs; reverse index `(profile_id,profile_digest,registry_digest)` | Registry installer / Registry repository |
| 6 | `discipline_package_compatibility_members`; immutable semantic derived projection | PK `(profile_id,profile_digest,combination_digest,package_key)`; exact semantic-profile/descriptor FKs; digest and lookup indexes | Registry installer / Registry repository |
| 7 | `organization_package_configuration_heads`; mutable head | PK/tenant key `organization_id`; Organization RESTRICT FK; nonnegative version | Configuration service / repository |
| 8 | `organization_package_selections`; retained ENABLED/DISABLED state | PK/tenant key `(organization_id,package_key,package_version)`; descriptor FK; version/state checks; tenant-leading index | Configuration service / repository |
| 9 | `project_package_configuration_revisions`; immutable | PK `(project_id,configuration_revision)`; tenant key `organization_id`; composite Project/Organization FK; release FK; `(observed_registry_digest,profile_id,profile_digest)` FK to exact release/profile membership; positive revision | Configuration service / repository |
| 10 | `project_package_configuration_selections`; immutable | PK `(project_id,configuration_revision,package_key)`; revision and exact descriptor FKs; 1..8 enforced by deferred constraint trigger | Configuration service / repository |
| 11 | `project_package_configuration_heads`; mutable head only | PK `project_id`; tenant key `organization_id`; composite Project/Organization and immutable revision FKs; nonnegative version | Configuration service / repository |
| 12 | `package_configuration_audit_events`; append-only | UUID PK; leading `organization_id`; composite Project/Organization and Workspace/Project FKs when present; bounded metadata/category/action checks; two accepted tenant indexes | configuration service writes; admin-only scoped repository reads |

The source manifests remain authoritative for tables 1–6. The database rows
are derived projection only. Tables 7–12 and Project/Workspace heads are
customer-configuration authority under Human actions. Repository methods never
commit/rollback and never accept untrusted tenant IDs.

Profile materialization groups members by `combination_digest`, recomputes the
sorted exact combination, rejects duplicate PackageKeys, checks 1..8 members
and 1..32 unique combinations, then compares the complete grouped set to
source `profile_json`. No ordinal is persisted and no hidden choice remains.
Materialization inserts semantic profile/member content once; each release
inserts its own immutable membership. Project provenance resolves the exact
membership triple before semantic reconstruction.

## 9. Workspace field and consistency map

`models/engineering_workspace.py` adds exactly:

| Field | Migration state | Final behavior | Owner/exposure |
|---|---|---|---|
| `canonical_discipline_id VARCHAR(64)` | nullable shadow in M2 | null only for `LEGACY_UNRESOLVED`; exact canonical identity otherwise | written only by migration/translation or creation service; exposed additively in Workspace and applicability DTOs |
| `package_binding_state VARCHAR(40)` | nullable in M2, NOT NULL in M3 | accepted three-state check | configuration/Workspace creation service writes; all authorized Workspace reads expose |
| `bound_package_key VARCHAR(64)` | nullable | non-null only when operationally bound | derived by service from current Project selection; never request input |
| `bound_project_configuration_revision BIGINT` | nullable | non-null only when operationally bound; exact composite Project-selection FK | derived by service; returned as provenance |

The raw `discipline` remains unchanged and write-compatible. The existing
schema response adds the four fields plus resolved package version,
descriptor digest and effective standing where authorized. Create DTO retains
only legacy `discipline`; no package key/version/revision input is added.

The final DB invariant is enforced by a `DEFERRABLE INITIALLY DEFERRED`
constraint trigger on insert or changes to `project_id`, canonical discipline,
binding state/key/revision and by a complementary trigger on Project head
advance. At commit it proves:

- each operational row has canonical ID, key and revision, maps exact
  Discipline-to-key, resolves a selection and equals the Project current head;
- future-unavailable rows have canonical ID and null binding fields;
- unresolved rows have all three canonical/binding values null; and
- advancing a Project head leaves no operational Workspace on another
  revision.

The trigger is defense in depth, not orchestration. It is installed only in M3
after exact backfill, validation and writer control, avoiding transient false
positives. Transaction tests force constraints immediate before commit and
verify stale/partial states fail.

## 10. Exact legacy translation owner

`legacy.py` exposes:

```text
translate_legacy_identity(source_contract, raw_value)
  -> CanonicalLegacyIdentity(canonical_discipline_id, disposition,
                             eligible_package_key, raw_value)
  | UnresolvedLegacyIdentity(source_contract, raw_value)
```

Mappings are exact and case-sensitive: Workspace `electrical`,
`instrumentation`, `control`, `mechanical`, `civil`, `process`; EKG
`industrial_automation` and `shared_engineering`; object/relationship
`automation`, Guidance `automation_and_control`, and object `shared` retain
their source-qualified accepted dispositions. `control` maps to canonical
`control_automation` while raw `control` remains stored. Unknown values return
unresolved with raw bytes/text preserved. New Workspace writes accept only the
existing enum. Unit vectors cover every mapping plus whitespace, case,
substring, Unicode-confusable and unknown negatives. There is no fuzzy match.

## 11. Advisory serialization helper

`core/database.py` gains a narrowly typed helper used through the PATCH-051
UoW:

```text
acquire_package_registry_guard(session, mode: SHARED | EXCLUSIVE)
```

It requires `session.in_transaction()`, first executes
`SET LOCAL lock_timeout = '5s'`, then exactly one parameterized call:

- shared: `SELECT pg_advisory_xact_lock_shared(:namespace, :contract)`;
- exclusive: `SELECT pg_advisory_xact_lock(:namespace, :contract)`;

with `(1396790339, 51)`. SQLAlchemy operational timeout/deadlock/serialization
errors translate to `RegistryGuardTimeout`/`ConcurrentPackageUpdate`. Release
is automatic on transaction commit/rollback; explicit unlock and process-local
substitution are prohibited.

Configuration service owns at most two full-transaction retries after rollback,
with a newly created UoW/Session per attempt, guard reacquisition and all reads
repeated. Registry activation never retries internally; the deployment
orchestrator owns retry. In each guarded Session, `SET LOCAL lock_timeout` and
the advisory-lock statement are the first SQL statements. The guard is the
first acquired DB lock.

### 11.1 Concrete guarded UoW and Session ownership

Request dependencies may use the request `Session` to authenticate and derive
active Organization context. Before a guarded service is called they convert
the result to a frozen scalar request-identity DTO containing only actor ID,
requested Organization ID, the credential `auth_version` verified for this
request, and an optional request/correlation ID. The credential version is the
stable claim bound to the presented token; current database `User.auth_version`
remains mutable authority and is reread below. Role, permission decisions,
account-active results, membership enable/selection results, membership
version and source-owner decisions are prohibited DTO fields. No request-bound
ORM instance or Session enters the mutation service, and the DTO never
authorizes a mutation.

Each outer mutation service receives a UoW factory backed by `SessionLocal`.
For every attempt it creates one new `SqlAlchemyDisciplinePackageUnitOfWork`,
which creates one new Session, enters one explicit transaction, binds all
repositories/staging helpers to that Session and closes it after commit or
rollback. That Session's checked-out connection acquires and retains the
transaction advisory guard and performs every protected query, lock, insert,
update and Audit stage. Acquiring the guard through another Session/connection,
returning the connection early or moving writes to the request Session is
prohibited.

Only the UoW outer context may call `commit()` or `rollback()`. Repositories,
authorization adapters, compatibility helpers, Workspace helpers and Audit
staging functions may add/flush/raise but may not begin, commit or roll back.
Flush is permitted only for server-generated identity/FK ordering and does not
end the transaction. Any exception escapes to the outer service, which rolls
back the whole attempt. A successful response is converted to a detached DTO
before the UoW closes.

The service-level retry loop catches only the accepted timeout/deadlock/
serialization categories after the failed UoW has rolled back and closed. It
creates a completely new UoW/Session for each of at most two retries and
repeats guard acquisition, actor/scope revalidation, Registry reads, row locks,
compatibility and all writes. It never continues a failed Session or retries
from a savepoint/partially used transaction. Exhaustion maps to safe
`409 CONCURRENT_UPDATE`.

### 11.2 Commit-stable guarded authority loader

Actual authorization facts are classified as follows:

| Class | Exact PATCH-051 facts |
|---|---|
| A — stable request identity/context | `actor_id`, requested `organization_id`, request credential `auth_version` claim and optional request/correlation ID; none is a permission result |
| B — mutable authority requiring commit stability | `users.is_active`, `users.role`, `users.auth_version` (`users.version` is its mutation/CAS metadata); exact `user_organization_memberships.is_enabled`, `is_selected`, `version`; `organizations.is_active` |
| C — resource authority stabilized by accepted resource locks | `projects.organization_id`, `projects.owner_id` on the target Project `FOR UPDATE`; existing Workspace `project_id`, owner/assignment and binding state on ascending-ID Workspace `FOR UPDATE` locks where read by rebind |
| D — irrelevant to these mutations | `users.activation_pending`; candidate owner/assignee/collaborator validity is write validation, not actor authority; Workspace owner/member state does not authorize Organization configuration, Project configuration/rebind or creation of a not-yet-existing Workspace |

`GuardedDisciplinePackageAuthorityLoader` is a narrow non-completing
collaborator owned by
`backend/app/repositories/discipline_package_unit_of_work.py`. It receives the
stable DTO and the already-open guarded Session; it never opens a Session and
never begins, commits or rolls back. Immediately after the shared Registry
advisory guard, it performs three separate, deterministic
`SELECT ... FOR UPDATE` reads:

1. exact `User.id == actor_id`;
2. exact `UserOrganizationMembership` primary key
   `(actor_id, requested_organization_id)`; and
3. exact `Organization.id == requested_organization_id`.

The User-first order is intentional repository reconciliation, not a generic
RBAC convention: role, account activity and credential invalidation share the
User row, while membership and Organization authority are later exact-scope
rows. The guarded loader then requires membership `is_enabled` and
`is_selected`, User `is_active`, equality between the request credential
version and locked `User.auth_version`, an operation-permitted current live
`User.role` (`admin` or `engineer` as applicable), and active Organization. It
reads current User/membership versions
from the locked rows for transaction-local evidence but never compares them to
a frozen cross-Session permission snapshot. The returned authority context is
transaction-local, may expose only those locked values required by the caller,
and is invalid after UoW completion.

There is no separate role-assignment table: `users.role` is the sole actual
role row, so the User lock is sufficient and no duplicate role lock exists.
There is no separate mutable source-owner policy row for these PATCH-051
mutations. Organization configuration is admin-only. Project configuration,
removal, rebind and Workspace creation use `projects.owner_id` as the only
non-admin source-owner predicate, and the accepted target Project
`FOR UPDATE` lock stabilizes both owner and Organization relationship through
commit. Project rebind does not authorize from Workspace ownership; its
Workspace locks stabilize affected resource/binding state only.

All guarded mutation paths use this one order:

```text
Registry advisory guard
-> actor User FOR UPDATE
-> actor UserOrganizationMembership FOR UPDATE
-> Organization FOR UPDATE
-> Registry projection validation
-> Organization configuration head/selections
-> Project FOR UPDATE
-> Project configuration head FOR UPDATE
-> affected Workspaces FOR UPDATE by ascending ID
-> writes
-> Audit staging
-> outer UoW commit
```

Operations omit later rows they do not use but never invert the prefix or
acquire an earlier authority row after a Project/Workspace lock. The
`FOR UPDATE` authority locks conflict with every PostgreSQL UPDATE/DELETE of
the same rows and remain held through final commit/rollback. Therefore exactly
two legal linearizations exist: if a guarded mutation obtains the authority
locks first, it commits under then-current authority and revocation waits; if
revocation locks/updates first, the guarded loader waits, rereads the committed
revocation, and fails before configuration/Workspace/binding/Audit-success
writes. A revocation may never commit first while a later mutation commits
from stale pre-revocation authority.

Actual compatibility impact is narrow. `OnboardingService.mutate_member()` and
`issue_reset()` currently lock membership before User and must change to the
User -> membership prefix; `complete_credential()` already uses User ->
membership -> Organization and User-only password change needs no adaptation.
For an admin-removal invariant, the repository's existing
`active_admin_count()` takes multiple User locks only after the target locks;
the adapted member mutation must instead lock the target plus active-admin User
rows as one ascending-`User.id` set, derive the count from that locked set, and
only then lock the target membership. This prevents two concurrent admin
removals from acquiring User rows in opposite order. No production
Organization-disable service exists; a future path updates/locks the same
Organization row and therefore conflicts directly.
Existing Project owner transfer ultimately updates the same `projects` row;
PostgreSQL serializes it against the guarded Project `FOR UPDATE`, and it must
not acquire package locks before that update. No broader onboarding,
authorization or Project redesign is authorized.

### 11.3 Existing Audit helper classification

`services.audit_service.create_audit_log()` currently adds a generic Audit row,
calls `session.commit()` and refreshes it. It is therefore **MUST NOT BE CALLED
INSIDE A GUARDED UOW**. Its unrelated legacy callers and behavior remain
unchanged.

The same module gains narrow `stage_audit_log(session, ...)`, classified **SAFE
STAGING HELPER**: it adds the existing `AuditLog`, flushes only when its integer
ID is required, and never begins, commits or rolls back. Guarded Workspace
creation calls this staging variant. Package Audit is staged by
`discipline_package_repository.py` in the same Session and follows the same
non-completion rule. Helper failure raises to the outer UoW and rolls back
Workspace, binding and both Audit rows.

## 12. Organization configuration algorithm

`replace_organization_configuration(actor, request)` in
`discipline_package_configuration_service.py`:

1. authenticate/derive initial Organization context on the request Session and
   freeze only the section 11.1 request-identity DTO;
2. validate strict bounded desired set and rationale without DB mutation;
3. create a fresh UoW, begin its sole transaction and acquire the shared
   Registry guard first;
4. invoke the guarded authority loader in User, membership, Organization order
   and require current active selected membership, active matching credential,
   live `admin` role and active Organization before any protected disclosure;
5. read current Registry digest/projection and fail on drift;
6. lock or create the Organization head `FOR UPDATE` (version 0 if absent),
   then lock retained selections in key/version order;
7. compare `expected_configuration_version`;
8. evaluate every requested exact version for current executable standing,
   static availability, compatibility and resource bounds; Organization
   availability does not call or enforce the separate entitlement predicate;
9. insert/update retained rows: desired are ENABLED; previously enabled omitted
   are DISABLED; never-seen omitted rows are absent;
10. increment the head once;
11. stage one bounded `ORG_CONFIGURATION` Audit event in the same Session; and
12. commit once and return reread provenance.

An identical request at the already advanced expected version is a version
conflict, not implicit replay; no idempotency key exists in accepted EDS.
Concurrent replacements serialize on the head. Project changes take
`FOR SHARE` on Organization head/selections, preventing enablement change
between validation and commit. Audit failure rolls back all state.

## 13. Project configuration and atomic rebind algorithms

`replace_project_configuration(actor, project_id, request)` owns this exact
flow for both `NOT_CONFIGURED -> CONFIGURED` and
`CONFIGURED -> CONFIGURED`:

1. validate request bounds; outer retry creates a fresh UoW/Session and begins
   its sole transaction;
2. acquire shared Registry guard first;
3. lock/revalidate exact User, membership and Organization authority rows in
   section 11.2 order; require current role `admin` or defer the owner branch to
   the locked Project; no frozen role or membership result is consulted;
4. read/lock current Registry projection for guarded validation;
5. lock Organization configuration head/selections `FOR SHARE`;
6. resolve tenant scope without disclosure, then lock Project `FOR UPDATE` and
   require `project.organization_id == actor.organization_id` plus current
   locked-role admin or `project.owner_id == actor.id`;
7. lock Project configuration head `FOR UPDATE` when present;
8. lock every current `OPERATIONAL_PACKAGE_BOUND` Workspace by ascending ID;
9. compare expected version and evaluate the target exact set/profile;
10. validate every affected Workspace against same target key, canonical
   Discipline, executable standing and migration guard;
11. allocate `max(configuration_revision)+1`, insert the immutable revision
    and 1..8 exact selection rows with recomputed digests;
12. update every affected Workspace revision pointer to the new revision;
13. advance/insert the Project head and configuration version;
14. stage one Project Audit and one bounded Workspace rebind event per
    affected row, at most six, without transaction completion; and
15. commit once, the sole linearization point.

Initial configuration has no operational Workspaces under PATCH-051 and
creates the head/revision without inventing binding. Every configured-to-
configured change treats all operational Workspaces as affected, even a
profile-only or unrelated addition. One invalid Workspace raises
`WORKSPACE_REBIND_INCOMPATIBLE` and rolls back revision, selections, all
bindings, head and Audit.

Removal locks the same scope and is permitted only with zero operationally
bound Workspace. It deletes only the head, retains revisions/selections and
writes one Audit. Rollback/downgrade submits an exact prior set through the
same algorithm and creates a new forward revision; a head pointer never moves
backward. Project rebinding is not a separate authorization path: it uses this
same guarded authority prefix, Project owner check, head/Workspace lock order,
Audit staging and one commit.

## 14. Workspace creation integration

`EngineeringWorkspaceService.create` becomes the outer retry/transaction owner
for this route and receives the PATCH-051 UoW factory plus a frozen actor DTO,
not the request Session. Each attempt creates a fresh UoW and acquires the
shared guard on its Session before any protected SQL. Using repositories bound
to that same Session, it first invokes the guarded authority loader; reads the
guarded Registry and Organization configuration; locks Project and current
Project head in the frozen order; revalidates tenant scope and live-role admin
or locked Project-owner authority; then checks duplicate Workspace, owner,
assignee and collaborators. It derives applicability, inserts Workspace and
members, stages generic Workspace Audit through `stage_audit_log`, stages a
package binding event when bound, and invokes the UoW's one final commit. No
request-Session role, membership or permission decision is consulted.

Its guarded create path does not call current `_audit_and_commit()` or
`create_audit_log()`. Existing non-PATCH-051 Workspace mutations retain their
current behavior outside this UoW. Applicability states remain:

- `electrical`, `instrumentation`, `control`: require configured Project,
  current executable Organization-enabled exact selection, compatible profile,
  matching canonical Discipline and migration guard; insert raw legacy value,
  canonical ID, `OPERATIONAL_PACKAGE_BOUND`, derived key and current Project
  revision. Because PATCH-051 ships no operational package, these normally
  return `PACKAGE_CONFIGURATION_REQUIRED` or unavailable until PATCH-052.
- `mechanical`, `civil`, `process`: retain existing create authorization but
  insert canonical ID with `FUTURE_UNAVAILABLE_UNBOUND` and null bindings.
- unknown legacy rows may be read as `LEGACY_UNRESOLVED`; new unknown writes
  remain rejected by the existing enum/schema.

The creation transaction takes the shared guard, authority locks, current
Registry and Organization-configuration reads, Project/head locks, then
inserts. A Project rebind cannot overtake it, and a concurrent revocation can
produce only the two section 11.2 serialized outcomes. Unique
`(project_id,discipline)` or canonical uniqueness violation maps to
`409 WORKSPACE_ALREADY_EXISTS`. Workspace never chooses, accepts or stores an
independent PackageVersion. Any authorization, validation, flush, staged-Audit
or commit failure rolls back Workspace, members, binding and both Audit rows.

## 15. Package configuration Audit design

`PackageConfigurationAuditEvent` is append-only and written only by the
configuration UoW. Event categories/writers are:

| Category | Writer/actions | Cardinality |
|---|---|---|
| `ORG_CONFIGURATION` | Organization replace; enable/disable | one summary event per commit |
| `PROJECT_CONFIGURATION` | configure/reconfigure/unconfigure/upgrade/downgrade/rollback | one event per Project authority change |
| `WORKSPACE_BINDING` | controlled bind or atomic rebind | at most one per affected Workspace, at most six per commit |

Fields follow accepted EDS exactly. Metadata is a closed schema containing at
most sorted changed keys, safe reason, action class and rationale digest; JSON
serialized size is capped at 8 KiB. No engineering payload, descriptor JSON,
secret, foreign fact or hidden collision operand is admitted.

`GET /organizations/current/discipline-package-configuration/audit` uses only
`(organization_id, occurred_at DESC, event_id DESC)`, an integrity-protected
15-minute opaque cursor bound to tenant/filter/limit, and limit 1..100. It is
active-Organization admin only. Global Registry installation/activation is
excluded and recorded only in source manifest, release row and deployment
operations attestation.

## 16. Authorization composition and entitlement seam

`dependencies/discipline_package.py` composes, never unions, predicates in this
order: existing OAuth authentication; `AuthenticatedOrganizationContext`;
existing Project/Workspace scope/visibility (protected 404); existing source
aggregate owner policy; Registry deployment support; Organization selection;
Project exact configuration; Workspace applicability; entitlement port; then
Core owner/adapter execution.

For reads, existing request-Session composition remains. For every guarded
write, the request composition yields identity/context only and section 11.2 is
the authoritative mutation-time check. Admin checks use locked
`User.role` only; Project mutation uses that live `admin` value or locked
`project.owner_id == actor.id`. A request-time or frozen role/membership result
cannot authorize. Workspace reads reuse current Workspace visibility. No
discovery route exposes tenant configuration.

The Core port is exactly:

```text
evaluate(trusted_organization_id, trusted_deployment_id, package_key,
         entitlement_key, operation) -> NOT_REQUIRED|PERMITTED|DENIED|UNAVAILABLE
```

`adapters/discipline_package_registry.py` supplies
`NonCommercialEntitlementAdapter` returning `NOT_REQUIRED`. It is invoked after
data authorization and configuration. Its test seam is constructor injection
in dependencies/service tests. PATCH-059 may replace/compose it without
changing identity or callers. No signed entitlement, seat, billing, grace or
license format is implemented.

## 17. Accepted API implementation map

All endpoints are implemented in
`api/v1/routers/discipline_packages.py`, use schemas from
`schemas/discipline_package.py`, request-scoped services from
`dependencies/discipline_package.py`, and repository/UoW files above.

| Endpoint | Service/transaction owner | Authorization and response/error behavior |
|---|---|---|
| `GET /discipline-packages/supported` | read service; no write transaction | authenticated active-org; current executable summaries only; limit 1..50/keyset; current RegistryDigest |
| `GET /organizations/current/discipline-package-configuration` | read service | active-org admin; bounded enabled/disabled rows |
| `PUT /organizations/current/discipline-package-configuration` | configuration service/UoW | active-org admin; full replacement; safe 409/422/503 |
| `GET /organizations/current/discipline-package-configuration/audit` | scoped Audit repository | active-org admin; limit 1..100, category filter, opaque cursor |
| `GET /projects/{id}/discipline-package-configuration` | read service | authorized Project reader; protected 404; exact head provenance |
| `PUT /projects/{id}/discipline-package-configuration` | configuration service/UoW | admin or Project owner; atomic revision/rebind |
| `DELETE /projects/{id}/discipline-package-configuration` | configuration service/UoW | admin or owner; body request; reject bound Workspace |
| `POST /projects/{id}/discipline-package-configuration/preflight` | read/preflight service | admin or owner; deterministic result; no mutation |
| `GET /projects/{id}/effective-discipline-packages` | read service | authorized Project reader; six Workspace-selectable canonical states maximum; reserved `shared_engineering` excluded |
| `GET /workspaces/{id}/package-applicability` | read service | authorized Workspace reader; protected 404; authorized provenance only |

Routers contain no commit, row lock or digest computation. Existing exception
handler is extended through `SatcoException` subclasses. No endpoint beyond the
accepted EDS is introduced; Registry synchronization remains a deployment
service/CLI operation, not HTTP.

## 18. Frontend implementation map

| Action | File | Exact role |
|---|---|---|
| MODIFY | `frontend/src/api/types.ts` | strict unions for supported/configuration/effective/applicability/Audit DTOs and named provenance digests |
| MODIFY | `frontend/src/api/client.ts` | ten accepted methods; safe closed-result parsing; no digest calculation |
| CREATE | `frontend/src/components/OrganizationPackageConfigurationPanel.tsx` | admin bounded full-set enable/disable UI with expected version/rationale and conflict refresh |
| CREATE | `frontend/src/components/ProjectPackageConfigurationPanel.tsx` | Project owner/admin exact profile/selection preflight and replace/remove UI |
| CREATE | `frontend/src/components/EffectiveDisciplinePackagesPanel.tsx` | truthful six-Workspace-selectable-Discipline state and safe provenance display; no `shared_engineering` Workspace option |
| CREATE | `frontend/src/disciplinePackages/components.tsx` | source-controlled allow-list from descriptor keys to bundled components; unknown key -> no render + safe telemetry |
| MODIFY | `frontend/src/pages/OrganizationAdminPage.tsx` | render Organization configuration panel for admins |
| MODIFY | `frontend/src/pages/ProjectsPage.tsx` | load effective state, render Project configuration/effective panels, replace literal Workspace selector |
| MODIFY | `frontend/src/styles.css` | scoped responsive/logical/RTL-safe styles and disabled/unavailable states |

The selector shows Electrical, Instrumentation, Control & Automation,
Mechanical, Civil and Process, with outbound compatibility values
`electrical`, `instrumentation`, `control`, `mechanical`, `civil`, `process`.
E/I/C create is disabled unless server action codes permit it. Future and
unresolved states remain visible only when authorized. Errors never echo
foreign IDs or raw server detail. Descriptor metadata supplies only allow-listed
keys; there are no dynamic imports, URLs, HTML or executable descriptor data.

## 19. Contribution contracts and existing aggregate integration

`contributions.py` owns closed bounded schemas for taxonomy, objects,
relationships, Context, inputs, deliverables, Evidence, deterministic rules,
standards hooks, cross-discipline interfaces, roles, authorization,
frontend metadata, resources, migration compatibility, `EntitlementKey` and
conformance evidence. `ports/discipline_package.py` defines provider-neutral
read-only declaration protocols.

| Existing capability | Minimal PATCH-051 seam | Existing authoritative owner preserved |
|---|---|---|
| Context | `PackageContextContributionPort` returns classification/requirement declarations | `EngineeringContextService` and Context stores |
| Engineering Objects | `PackageObjectContributionPort` returns trusted metadata; existing DB vocabulary still gates writes | `EngineeringObjectService`/aggregate |
| Relationships | `PackageRelationshipContributionPort` returns allowed declarations | `EngineeringRelationshipService`/aggregate |
| Interface Commitments | `PackageInterfaceDeclarationPort` returns interface declarations only | `InterfaceCommitment`; PATCH-053 owns reasoning |
| Evidence | `PackageEvidenceRequirementPort` declares requirements | Evidence aggregate/repository and its authorization |
| Technical Reports | additive package-causal provenance DTO may be supplied to future report inputs | Technical Report aggregate, Human acceptance and accepted digest |
| Organizational Memory | no direct package admission; accepted Report boundary only | Organizational Memory service/aggregate |
| Guidance | `PackageRuleContributionPort` resolves static deterministic hook IDs | Guidance remains advisory and authoritative for its outputs |

No PATCH-051 store duplicates these aggregates. No current hard-coded Object or
Relationship constraint is relaxed by declaration alone. Operational catalog
values require later accepted package design/migration.

## 20. Readiness and startup design

Startup in `main.py` explicitly assembles the source Registry, validates static
adapters and registers an immutable in-process Registry object. Package
readiness is composed into `core/operations.py` and `/health/ready` without
details.

| Condition | Startup/readiness result |
|---|---|
| descriptor/schema/digest/adapter/Core-contract failure | startup fatal; process does not serve |
| source Registry assembly failure | startup fatal |
| runtime principal owns/can mutate projection, has forbidden role authority, or expected ownership/grants/triggers differ | startup/readiness failure; package and configuration writes blocked |
| Registry installer principal/grants invalid | deployment CLI exits before lock/write; running application remains on prior projection |
| current DB projection missing/drifted | process may start for diagnostics, readiness 503; configure/execute 503 |
| missing current release | readiness 503 and package operations blocked |
| historical release needed by active data missing | readiness 503; no interpretation/execute |
| retained historical release valid, standing historical-only | startup/readiness may pass; authorized read only, execution blocked |
| historical-only quarantined source missing during declared recovery mode | safe read unavailable for affected records; global mode remains read-only/not ready for writes |

Configuration includes only safe timeouts and embedded expected release
identity. Environment variables cannot point to arbitrary descriptor modules or
change RegistryDigest. The FastAPI environment contains no Registry-installer
credential; that credential exists only in the controlled deployment job.

## 21. Transaction, lock and completion matrix

Every row uses one newly created UoW Session per attempt. The advisory guard,
all protected reads/writes and Audit staging share that Session/connection.
Only the named outer UoW commits/rolls back; every helper is non-completing.

| Operation | Stable request identity | Guarded authority rows | Resource locks after authority prefix | Audit/helper policy | Retry owner | Completion / linearization |
|---|---|---|---|---|---|---|
| projection install | deployment release identity; no request actor | none; EXCLUSIVE advisory guard first | release, descriptor, package membership, semantic profile, release/profile membership and member rows in canonical key order | no tenant Audit; deployment evidence only after commit; repositories never commit | none internally; deployment operator restarts whole operation | installer UoW commit |
| Registry activation | deployment target digest; no request actor | none; EXCLUSIVE advisory guard first | current then target release ordered by digest | deployment evidence after commit only; never tenant Audit | none internally; deployment operator retries a new UoW | installer UoW commit changing only current pointer |
| Organization replacement | actor ID, Organization ID, credential version, correlation ID | SHARED guard; User -> membership -> Organization, each `FOR UPDATE`; require enabled/selected, active/version-current/live admin, active | Registry; Organization head/selections `FOR UPDATE` ordered | stage one scoped package event; no generic committing helper | configuration service, max two whole-attempt retries with fresh locks and reread | runtime UoW commit; revocation either waits behind authority locks or wins first and causes denial |
| Project initial configure/remove | same bounded identity DTO | same three-row authority prefix; live role only | Registry; Org head/selections `FOR SHARE`; Project `FOR UPDATE` supplies tenant/owner authority; Project head when present | stage one Project event | configuration service, max two new-UoW retries with no reused authority context | runtime UoW commit under locked authority, or no write after revocation-first |
| Project update/rebind | same bounded identity DTO | same three-row authority prefix; live role only | Registry; Org configuration; Project; Project head; operational Workspaces `FOR UPDATE` ascending ID | stage one Project plus at most six Workspace events | configuration service, max two fresh-UoW retries | one runtime UoW commit; owner transfer/revocation serializes before or after it |
| Workspace create | same bounded identity DTO | same three-row authority prefix; live role only | Registry; Org configuration; Project `FOR UPDATE` supplies tenant/owner authority; Project head; matching selection; insert Workspace/members | use `stage_audit_log`, never `_audit_and_commit`/`create_audit_log`; stage binding event when bound | Workspace service, max two fresh-UoW retries for accepted concurrency errors | one runtime UoW commit, or revocation-first denial with no Workspace/Audit success |

Deadlock review fixes one universal prefix: advisory guard, actor User,
composite actor membership, Organization, Registry, Organization configuration,
Project, Project head, then Workspace IDs ascending. Activation takes no tenant
locks; Organization replacement takes no Project/Workspace locks; no guarded
path acquires User/membership after a resource lock. The actual combined
revocation/reset paths identified in section 11.2 must conform, and multi-User
admin-removal locks are ascending before membership. User-only password change,
Organization-only UPDATE and Project-owner UPDATE each touch a compatible
subset and cannot form a reverse-order cycle. Project owner transfer's UPDATE
blocks on the same Project row, and it acquires no package row afterward. Thus
User disable, membership disable/deselect, role change, Organization disable,
Organization configuration, Project configuration/rebind and Workspace create
have no specified lock-order cycle.

### 21.1 Projection and configuration authority matrix

| Authority | Credential/ownership | Permitted | Prohibited |
|---|---|---|---|
| source Registry | reviewed application release | define immutable descriptors, profiles, release membership and expected digests | DB/customer authorship, runtime discovery or tenant mutation |
| migration/schema owner | existing Alembic principal from `ALEMBIC_DATABASE_URL`, distinct from runtime/installer | own schema/tables/functions/triggers; execute migrations; apply M1 grants/revokes | normal request handling, Registry activation or tenant configuration |
| Registry projection installer | externally provisioned dedicated login `satco_registry_installer`; deployment CLI secret only | SELECT/INSERT on six projection tables; UPDATE only `discipline_package_registry_releases.is_current`; acquire exclusive guard | schema ownership/create, tenant configuration/Audit mutation, DELETE/TRUNCATE/REFERENCES/TRIGGER, broad runtime use |
| ordinary runtime application | existing restricted `satco_runtime` credential | SELECT all six projection tables; accepted tenant configuration/Audit operations; acquire shared guard | any INSERT/UPDATE/DELETE on Registry projection, activation, schema/role management |

Deployment provisioning, not Alembic, creates login principals and secrets.
M1 requires the fixed roles to exist, retains all new object ownership with the
migration/schema owner, revokes projection privileges from `PUBLIC`,
`satco_runtime` and `satco_registry_installer`, then grants the exact matrix.
It grants neither role schema `CREATE`, object ownership, role membership nor
superuser/bypass/createdb/createrole authority. No default privilege is needed
because the three fixed migrations enumerate every PATCH-051 object.

Runtime projection privileges are exactly `SELECT` on releases, descriptors,
package memberships, semantic profiles, release/profile memberships and
profile members; INSERT/UPDATE/DELETE are absent. Installer privileges are
exactly `SELECT, INSERT` on those six tables plus column-level
`UPDATE (is_current)` on releases; DELETE is absent everywhere. Direct EXECUTE
on integrity/immutability trigger functions is revoked from `PUBLIC`, runtime
and installer. Trigger enforcement remains active under schema-owner ownership.

`core/database.py` adds `validate_discipline_package_runtime_boundary()` and
package readiness invokes it when PATCH-051 persistence is enabled. It verifies
runtime current user, owner separation, forbidden role flags/membership/schema
CREATE, exact six-table SELECT-only privileges, absent projection mutation,
expected tables/FKs/triggers and non-executable guard functions. Failure is
startup/readiness-safe `not_ready` with no grant detail.

`backend/scripts/discipline_package_registry.py` constructs a separate Engine
only from deployment-supplied Registry DB host/port/name/user plus a password
file; it requires current user `satco_registry_installer`, distinct from
runtime/migration owners, verifies the same forbidden flags and exact installer
grants, then creates the installer UoW. Credentials are never loaded by the
FastAPI runtime or logged. Installer validation failure performs no projection
write and exits nonzero. Integration/security tests prove runtime projection
mutation denial, installer insert/activation success, guarded activation,
runtime configuration success with read-only projection and reproducible M1
grants.

## 22. Composite tenant-key design

M1 adds supporting uniqueness, preserving existing PKs:

- `UNIQUE projects(id, organization_id)`;
- `UNIQUE engineering_workspaces(id, project_id)`; and
- `UNIQUE project_package_configuration_revisions(project_id,
  organization_id, configuration_revision)` in addition to its accepted PK.

It then enforces:

- Project revisions/heads and Audit `(project_id, organization_id)` reference
  `projects(id, organization_id)`;
- Audit `(workspace_id, project_id)` references
  `engineering_workspaces(id, project_id)` when Workspace is non-null;
- Project heads `(project_id, organization_id, current_revision)` reference
  the tenant-consistent revision triple;
- Workspace binding `(project_id,
  bound_project_configuration_revision,bound_package_key)` references exact
  Project selections; and
- an Audit Workspace requires non-null Project via a check, making the two
  composite FKs transitively prove Organization/Project/Workspace coherence.

Organization tables lead with direct `organization_id` FKs. These constraints,
not application filters alone, prevent cross-tenant association. Model
`__table_args__` mirrors every named constraint.

## 23. Migration `e05100000001` — Registry, configuration and Audit

File (future only):
`backend/migrations/versions/e05100000001_registry_configuration_audit.py`,
`down_revision="e04700000001"`.

Upgrade:

1. require sole repository/deployed head `e04700000001`, PostgreSQL required
   extensions/types and a PASS census artifact matching DB identity/head;
2. add supporting unique `(projects.id,organization_id)` and
   `(engineering_workspaces.id,project_id)` keys;
3. create all twelve tables in dependency order with the PKs/FKs/checks,
   partial-current uniqueness and tenant indexes from sections 8/22: semantic
   profile PK `(profile_id,profile_digest)`, release/profile membership PK
   `(registry_digest,profile_id)`, unique release/profile/digest triple,
   release and semantic-profile FKs, reverse membership index, unchanged member
   PK and Project-revision FK to the exact membership triple;
4. install immutability triggers for descriptor, package/release-profile
   membership, semantic profile/member, revision/selection and package Audit
   rows, permitting only the documented release current pointer, heads and
   Organization selection states to mutate;
5. install a deferred constraint trigger proving each Project revision has
   1..8 exact selections and tenant-consistent head provenance;
6. require externally provisioned `satco_runtime` and
   `satco_registry_installer`; retain ownership with the Alembic migration
   principal; revoke all projection rights from `PUBLIC` and both principals;
   grant runtime SELECT-only on all six projection tables; grant installer
   SELECT/INSERT on all six plus `UPDATE(is_current)` on releases; revoke
   DELETE/TRUNCATE/REFERENCES/TRIGGER and direct trigger-function execution;
   grant runtime exact tenant rights: SELECT/INSERT/UPDATE on Organization
   heads/selections, SELECT/INSERT on Project revisions/selections and package
   Audit, and SELECT/INSERT/UPDATE/DELETE on Project heads (DELETE supports
   accepted unconfigure); no installer tenant-table privilege; and
7. create no Organization or Project configuration and no Registry release.

Postconditions: twelve tables/constraints/indexes/ownership/grants exactly
match metadata and the authority matrix; all twelve new tables are empty;
runtime projection mutation negatives and installer privilege preflight pass;
prior tables/checksums are unchanged. Projection installation is a separate
guarded deployment-CLI step after M1.

Downgrade is safe only while every new table is empty and no projection was
installed. Otherwise forward recovery is mandatory. It may drop empty new
tables/triggers and the two unused supporting unique keys; it never changes
legacy data.

## 24. Migration `e05100000002` — Workspace binding shadow

File (future only):
`backend/migrations/versions/e05100000002_workspace_binding_shadow.py`,
`down_revision="e05100000001"`.

Upgrade adds the four nullable Workspace columns; accepted state checks and
the composite binding FK as `NOT VALID`; partial unique
`(project_id,canonical_discipline_id) WHERE canonical_discipline_id IS NOT
NULL`; lookup indexes for `(project_id,package_binding_state,id)` and bound
revision/key; and raw-value-preserving comments/metadata. It does not backfill,
validate, set NOT NULL or change the legacy discipline constraint.

Preconditions: M1 at head, exact source Registry installed and reconciled,
PASS census still matches current counts, compatibility-capable application can
read null shadows, and no unsupported writer exists. Postcondition: old and new
application reads remain possible; all new columns are null; no existing row
is rewritten.

Focused remediation impact: **NONE**. M2 has no profile/release FK or DB-role
decision beyond depending on reconciled M1.

Downgrade is safe only before any shadow/binding value or dependent Audit/
Project configuration exists. Otherwise keep columns and forward-recover.

## 25. Migration `e05100000003` — Exact backfill and cutover

File (future only):
`backend/migrations/versions/e05100000003_workspace_binding_cutover.py`,
`down_revision="e05100000002"`.

Upgrade requires a drained/read-only writer window and an unexpired matching
census artifact. It:

1. locks the migration scope with governed timeouts;
2. updates Workspaces in indexed ascending-ID chunks using only the six exact
   mappings;
3. sets canonical values and `FUTURE_UNAVAILABLE_UNBOUND` for every recognized
   existing row; fabricates no Project selection/binding;
4. asserts per-value and total affected counts equal the preflight artifact,
   rejects unknown/null/duplicate-canonical candidates and verifies historical
   owner checksums;
5. validates M2 FKs/checks and the partial unique index;
6. sets `package_binding_state NOT NULL`;
7. installs the conditional state check and the deferred Workspace/current-head
   constraint triggers; and
8. forces validation, records schema evidence and leaves raw `discipline` and
   its check intact.

Postconditions: every Workspace is one accepted state; all six known values
round-trip; no operational binding exists solely because of migration; unknown
count is zero; prior Report/Memory/Evidence/generic Audit checksums match.

Downgrade after cutover may remove/defer M3 trigger and NOT NULL enforcement
only if the older application can safely read shadows. It must not erase
canonical values, binding provenance, Project history or package Audit.
Destructive removal after use is forbidden; forward recovery is mandatory.

Focused remediation impact: **NONE**. M3 has no profile/release FK and consumes
the guarded UoW foundation already established before Batch 3.

## 26. Live census preflight and migration consumption

`backend/scripts/discipline_package_preflight.py` is a read-only CLI using an
explicit database URL/role and `REPEATABLE READ, READ ONLY, DEFERRABLE`. It
executes no DDL/DML and emits canonical JSON plus SHA-256 at
`artifacts/patch-051/preflight/<deployment-id>-<db-fingerprint>.json` outside
source control.

Artifact fields are schema version, deployment/database fingerprint, Alembic
head, transaction timestamp, query/tool commit digest, distinct Workspace
discipline values/counts, nulls, duplicate canonical candidates, Project/
Workspace orphans, Engineering Object `(discipline,family,object_type)` counts,
Context/EKG/relationship relevant raw identities, constraints/definitions,
rows affected by M2/M3, accepted Report/Memory/Evidence/generic Audit counts and
checksums, historical Registry source availability, findings and overall
`PASS|FAIL`.

PASS requires head `e04700000001` before M1 (then the exact expected predecessor
for M2/M3), only six Workspace values, no null/unknown value, no canonical
duplicate within a Project, no cross-scope orphan, compatible PostgreSQL
constraint/trigger support, all referenced historical sources resolvable and
counts internally consistent. Any unknown, stale artifact, head mismatch,
count drift or query failure is FAIL.

Each migration is invoked by a deployment wrapper with explicit
`--require-preflight <artifact> --require-digest <sha256>`. The revision
recomputes DB fingerprint/head and required counts in its transaction and stops
on mismatch. This operationalizes `EDS051-OBS-01` without claiming a future
deployment census exists today.

## 27. Cutover choreography and recovery

The future authorized release sequence is fixed:

1. run and Human/operator-review the read-only census; stop on FAIL;
2. deploy compatibility-capable application version A that reads absent/null
   shadows, continues legacy writes and keeps package routes disabled;
3. drain writers or enter governed read-only mode; verify no old writer;
4. execute M1;
5. deployment job supplies the dedicated Registry-installer credential to the
   non-HTTP CLI, validates exact grants, assembles the authoritative release,
   acquires the exclusive guard on the installer UoW connection and installs/
   reconciles its projection; readiness remains gated and FastAPI never
   receives that credential;
6. execute M2;
7. rerun/revalidate census and exact counts; execute M3 backfill/validation;
8. deploy/cut over application version B that requires final fields and enables
   accepted package APIs, still with zero operational packages;
9. validate source/projection/historical anchors, triggers, tenant negatives,
   routes, performance and readiness;
10. restore writers only after all checks PASS and record deployment evidence.

If M1/M2 fails before writes, rollback empty structures is allowed. After any
projection/configuration/binding/Audit use, keep schema, disable configuration/
execution, retain current/old source releases and forward-fix. Registry
activation failure preserves old current. Application rollback must understand
new nullable/final columns. Project/package rollback is a new audited forward
revision, never history deletion or pointer rewind.

## 28. Test implementation and conformance map

| Future file | Required coverage |
|---|---|
| `backend/tests/test_discipline_package_contracts.py` | identity/SemVer/NFC/strict descriptor/contribution/resource bounds and provenance type separation |
| `backend/tests/test_discipline_package_registry.py` | assembly order, empty release, adapters, dependencies/collisions, digest golden vectors, historical anchors |
| `backend/tests/test_discipline_package_projection.py` | R1/R2 reuse of unchanged P/D, distinct memberships/no overwrite, complete semantic-plus-membership row comparison, drift, standing and activation |
| `backend/tests/test_discipline_package_compatibility.py` | frozen order, profile combinations/cardinality, closed reasons, budgets/migration guards |
| `backend/tests/test_discipline_package_service.py` | Organization/Project state, remove/rollback, effective/applicability, historical reads |
| `backend/tests/test_discipline_package_transaction.py` | same-Session/connection guard affinity; membership/User/Organization `FOR UPDATE` locks retained to final commit; exact global lock order; inner-commit prohibition; fresh-UoW/reacquired-authority retries; Registry races; two-schedule revocation serialization; Workspace-create, Organization-config and atomic rebind/Audit full rollback |
| `backend/tests/test_discipline_package_audit.py` | tenant scope, event bounds, pagination/cursor, atomicity and exclusion of global Registry events |
| `backend/tests/test_discipline_package_api.py` | all accepted endpoints, bounds, provenance and safe errors |
| `backend/tests/test_discipline_package_security.py` | authorization order, identity-only DTO, frozen role prohibited, stale request Session rejected, current role/auth-version/membership/Organization checks, protected 404, cross-tenant negatives, no permission union/disclosure/injection |
| `backend/tests/test_discipline_package_migration.py` | all three revisions, exact backfill/counts, composite FKs, triggers, downgrade/forward recovery |
| `backend/tests/test_discipline_package_preflight.py` | read-only enforcement, census vectors, artifact digest/staleness and fail-closed consumption |
| `backend/tests/test_discipline_package_conformance.py` | descriptor/package fixtures, prohibited executable content, collisions and compatibility vectors |
| `backend/tests/test_discipline_package_performance.py` | 4 MiB startup <1s, compatibility p95 <50ms, effective p95 <200ms, Audit p95 <300ms and query plans |
| `backend/tests/test_discipline_package_database_roles.py` | reproducible M1 ownership/grants; runtime six-table SELECT-only and mutation denial; installer exact insert/current-pointer update; no broad flags/schema/tenant authority; runtime configuration still works |
| `backend/tests/test_engineering_workspace_{core,migration,permissions}.py` | additive fields, creation states, Control mapping and owner policy regression |
| `frontend/src/test/discipline-packages.test.tsx` | admin/Project panels, selector, Control, future/unresolved/historical states, unknown key safety |
| `frontend/src/test/{api,organization-admin,workflows}.test.tsx` | client parsing, admin placement and whole Project workflow regression |

The conformance harness accepts a descriptor, explicit static adapter and
vectors. It validates schema/digests, contribution counts/bytes, adapter
capability equality, prohibited code/import/URL/HTML fields, collision
namespaces, authorization declarations, resource declarations, migration
compatibility and exact package-version/profile vectors. A future PATCH-052
package cannot enter the release table until the harness and golden digests
pass. Harness fixtures are never production descriptors.

Projection/conformance vectors additionally install R1/P/D then R2/P/D,
assert one semantic profile/member set and two immutable membership rows,
exercise Project triple-FK acceptance/rejection, and prove historical lookup
does not consult the current pointer. Transaction doubles fail if a repository
or staging helper invokes commit/rollback; forced Audit/flush/commit failures
prove one rollback, and retry spies prove a new Session/connection/guard per
attempt.

Focused transaction/security vectors use two independent PostgreSQL Sessions
and barriers, not only mocks, and cover:

1. **User disable wins:** `mutate_member()` locks/commits account disable and
   `auth_version` increment first; guarded Organization config, Project config/
   rebind and Workspace create wait, reread, fail, and persist no success Audit
   or engineering/configuration change.
2. **Mutation wins:** each guarded mutation locks authority first, completes
   and commits; the revocation UPDATE is demonstrably blocked until afterward,
   then commits as the valid later linearization.
3. **Membership disable/deselect wins:** the composite membership UPDATE
   commits first; guarded mutation observes disabled/unselected state and
   writes nothing.
4. **Role removal wins:** live `users.role` changes from `admin` to `engineer`
   first; admin-only Organization configuration fails, and Project/Workspace
   mutations succeed only if the locked Project-owner branch independently
   authorizes the actor.
5. **Stale request Session:** it observed valid admin/active/selected state,
   then role, membership, account, credential version or Organization state
   changes before the guarded locks; the guarded Session rejects without using
   the stale request result.
6. **Retry after authority change:** attempt one receives an accepted
   serialization/deadlock conflict; authority is revoked before retry; the new
   UoW reacquires all locks and fails authorization rather than reusing the
   prior transaction-local context.
7. **Workspace-create race:** revocation-first leaves no Workspace, member,
   binding, generic Audit or package Audit; mutation-first blocks revocation
   until the one create commit.
8. **Project-rebind/owner-transfer races:** revocation or owner transfer first
   causes the guarded rebind to reread the locked authority/Project and deny;
   rebind-first holds authority, Project and ordered Workspace locks until all
   revision/binding/Audit writes commit, then the later change proceeds.
9. **Organization-config race:** revocation-first leaves no head, selection,
   revision or success Audit change; mutation-first commits under valid locked
   authority and revocation follows.

The Organization-deactivation branch is exercised with a direct test fixture
UPDATE because the actual repository has `organizations.is_active` but no
production disable service. It proves the same-row serialization without
inventing that service. Every denial assertion also proves no successful
configuration/binding Audit event; no new security-Audit subsystem is added.

## 29. Resource, failure and security enforcement

Resource limits are enforced redundantly: Pydantic collection/string bounds at
source load and API input; canonical byte sizes before hashing; Registry graph
and contribution totals during assembly; database/check constraints for row
shape; service selection/event/page bounds; query `LIMIT`; adapter timeout
classes; and controlled performance/query-plan gates. No path truncates a
semantic set silently.

| Domain condition | Safe exception/HTTP mapping |
|---|---|
| invalid descriptor/adapter/Core | startup error; readiness 503 |
| projection drift/missing current | `REGISTRY_UNAVAILABLE`, 503 |
| malformed/bound-exceeding request | `INVALID_PACKAGE_CONFIGURATION`, 422 |
| expected version mismatch | `CONFIGURATION_VERSION_CONFLICT`, 409 |
| unsupported/historical selection | `PACKAGE_VERSION_UNAVAILABLE`, 409 |
| incompatible/resource/profile/migration | accepted safe reason codes, 409 |
| missing Project configuration | `PACKAGE_CONFIGURATION_REQUIRED`, 409 |
| bound removal/rebind failure | `BOUND_WORKSPACE_EXISTS` / `WORKSPACE_REBIND_INCOMPATIBLE`, 409 |
| unique Workspace race | `WORKSPACE_ALREADY_EXISTS`, 409 |
| guard/serialization exhausted | `CONCURRENT_UPDATE`, 409 |
| request credential version no longer current | existing invalid-authentication behavior, 401; no resource lookup |
| inactive actor | existing inactive-user behavior, 403; no resource lookup |
| missing/disabled/deselected membership or inactive Organization | `ACTIVE_ORGANIZATION_CONTEXT_REQUIRED`, 403; no hidden resource/package fact |
| foreign/inaccessible scope | protected 404 before package fact |
| authenticated same-scope role failure | `CONFIGURATION_ADMIN_REQUIRED`, 403 |
| future/unresolved GET | truthful 200 state; mutations 409 |

Security controls include reviewed immutable source, typed digest separation,
static adapters, least-privilege projection roles, active-org derivation,
composite tenant FKs, ordered intersecting authorization, exact legacy mapping,
bounded Audit, forward-only rollback, precompiled frontend keys, shared/exclusive
database guard and deferred Workspace consistency. Logs/telemetry use safe
codes/correlation IDs and never foreign configuration or descriptor contents.
An authority failure rolls back the guarded attempt and emits no successful
Organization-configuration, Project-configuration, Workspace-binding or
generic Workspace-create Audit. PATCH-051 adds no denial/security Audit path;
if an existing outer security seam records a denied request, it remains outside
the guarded success transaction and must retain existing non-disclosure rules.

## 30. Implementation batches

Five bounded batches are proposed; each requires separately accepted
Implementation Plan and batch authority.

### Batch 1 — Core contracts, source Registry and conformance

Scope: identity, contracts/contributions, canonicalization, explicit empty
release, static adapters, Registry assembly, compatibility, legacy translator,
entitlement port and conformance foundations. Production: new
`discipline_packages/*`, enums, port and adapter. Tests: contracts, Registry,
compatibility and conformance. Migrations: none. Dependency: accepted IDS/Plan.
Acceptance: digest golden vectors, profile cardinality, empty release, no
runtime discovery, closed reasons/resource bounds and historical source lookup
PASS. Recovery: code-only rollback retaining source release modules.

### Batch 2 — Persistence, preflight, M1/M2 and Registry projection

Scope: twelve models including normalized release/profile membership,
repository/UoW factory, same-Session advisory helper, Registry installer CLI
and service, read-only preflight, exact runtime/installer authority validation,
M1/M2 and model/migration registration. Tests: cross-release projection,
migration, preflight, database-role and guard/UoW foundations. Migrations:
`e05100000001` and `e05100000002`, created but not executed without separate
migration authority. Dependency: Batch 1. Acceptance: metadata/DB parity,
R1/R2 semantic-profile reuse with distinct memberships, composite tenant keys,
twelve-empty-table invariant, reproducible grants, runtime projection mutation
denied, controlled installer activation allowed, connection-affine guard,
projection drift/readiness, historical retention and null-shadow compatibility
PASS. Recovery: only empty downgrade; otherwise forward recovery.

### Batch 3 — Configuration, Audit, Workspace binding and M3

Scope: configuration/read services, Organization/Project algorithms, exact
legacy backfill, four Workspace fields, atomic rebind, deferred consistency,
M3, guarded authority loading, guarded Workspace creation, non-committing
generic/package Audit staging, narrow onboarding multi-row lock-order
compatibility and existing Workspace composition. Tests: service, transaction,
focused revocation races, Audit, Workspace and migration cutover. Dependency:
Batches 1–2, including accepted UoW/role foundations, plus reviewed PASS census
for any execution environment. Acceptance: every guarded mutation holds exact
membership/User/Organization authority through commit; both revocation-first
and mutation-first schedules pass; stale request/retry authority is rejected;
one invalid Workspace rolls back all authority/Audit; create/Audit failure
leaves no Workspace; Registry race serializes; no cross-tenant FK; exact
six-value backfill and no fabricated operational binding. Recovery: disable
writes and forward-repair; never delete used history.

### Batch 4 — API, authorization and readiness/startup

Scope: schemas, exceptions, dependency composition, router, main/config/
operations integration and Project/Workspace applicability reads. Tests: API,
security, readiness and performance. Migration: none beyond dependency on M3.
Acceptance: ten accepted routes, protected 404 ordering, admin/owner policy,
bounded cursors, safe errors and startup/readiness matrix PASS. Recovery:
disable router/package writes while retaining readable schema/history.

### Batch 5 — Frontend and whole-PATCH regression

Scope: API types/client, three panels, compiled component allow-list,
Organization/Projects placement, effective selector and styles. Tests: frontend
package suite plus API/admin/workflow regressions; whole backend PATCH-051,
QG-M1 and conformance/performance runs. Migration: none. Dependency: Batches
1–4. Acceptance: Control & Automation visible, unavailable/historical/unresolved
truthful, no dynamic code, safe conflicts/errors, accessibility/responsiveness
and complete accepted EDS trace PASS. Recovery: revert UI exposure while server
contracts/history remain intact.

## 31. Exact future manifests

### Production file manifest

Create:

- `backend/app/discipline_packages/__init__.py`
- `backend/app/discipline_packages/identity.py`
- `backend/app/discipline_packages/contracts.py`
- `backend/app/discipline_packages/contributions.py`
- `backend/app/discipline_packages/canonical.py`
- `backend/app/discipline_packages/registry.py`
- `backend/app/discipline_packages/compatibility.py`
- `backend/app/discipline_packages/legacy.py`
- `backend/app/discipline_packages/conformance.py`
- `backend/app/discipline_packages/descriptors/__init__.py`
- `backend/app/discipline_packages/descriptors/releases/__init__.py`
- `backend/app/discipline_packages/descriptors/releases/release_051_core_v1.py`
- `backend/app/enums/discipline_package.py`
- `backend/app/schemas/discipline_package.py`
- `backend/app/models/discipline_package.py`
- `backend/app/ports/discipline_package.py`
- `backend/app/adapters/discipline_package_registry.py`
- `backend/app/exceptions/discipline_package.py`
- `backend/app/repositories/discipline_package_repository.py`
- `backend/app/repositories/discipline_package_unit_of_work.py`
- `backend/app/services/discipline_package_registry_service.py`
- `backend/app/services/discipline_package_service.py`
- `backend/app/services/discipline_package_configuration_service.py`
- `backend/app/dependencies/discipline_package.py`
- `backend/app/api/v1/routers/discipline_packages.py`
- `backend/scripts/discipline_package_preflight.py`
- `backend/scripts/discipline_package_registry.py`
- `frontend/src/components/OrganizationPackageConfigurationPanel.tsx`
- `frontend/src/components/ProjectPackageConfigurationPanel.tsx`
- `frontend/src/components/EffectiveDisciplinePackagesPanel.tsx`
- `frontend/src/disciplinePackages/components.tsx`

Modify:

- `backend/app/core/config.py`
- `backend/app/core/database.py`
- `backend/app/core/operations.py`
- `backend/app/main.py`
- `backend/app/enums/__init__.py`
- `backend/app/schemas/__init__.py`
- `backend/app/models/__init__.py`
- `backend/app/models/project.py`
- `backend/app/models/engineering_workspace.py`
- `backend/app/repositories/onboarding_repository.py`
- `backend/app/repositories/project_repository.py`
- `backend/app/repositories/engineering_workspace_repository.py`
- `backend/app/services/onboarding_service.py`
- `backend/app/services/engineering_workspace_service.py`
- `backend/app/services/audit_service.py`
- `backend/app/schemas/engineering_workspace.py`
- `backend/app/api/v1/routers/engineering_workspaces.py`
- `backend/migrations/env.py`
- `frontend/src/api/types.ts`
- `frontend/src/api/client.ts`
- `frontend/src/pages/OrganizationAdminPage.tsx`
- `frontend/src/pages/ProjectsPage.tsx`
- `frontend/src/styles.css`

### Test file manifest

Create:

- `backend/tests/test_discipline_package_contracts.py`
- `backend/tests/test_discipline_package_registry.py`
- `backend/tests/test_discipline_package_projection.py`
- `backend/tests/test_discipline_package_compatibility.py`
- `backend/tests/test_discipline_package_service.py`
- `backend/tests/test_discipline_package_transaction.py`
- `backend/tests/test_discipline_package_audit.py`
- `backend/tests/test_discipline_package_api.py`
- `backend/tests/test_discipline_package_security.py`
- `backend/tests/test_discipline_package_migration.py`
- `backend/tests/test_discipline_package_preflight.py`
- `backend/tests/test_discipline_package_conformance.py`
- `backend/tests/test_discipline_package_performance.py`
- `backend/tests/test_discipline_package_database_roles.py`
- `frontend/src/test/discipline-packages.test.tsx`

Modify:

- `backend/tests/test_engineering_workspace_core.py`
- `backend/tests/test_engineering_workspace_migration.py`
- `backend/tests/test_engineering_workspace_permissions.py`
- `frontend/src/test/api.test.ts`
- `frontend/src/test/organization-admin.test.tsx`
- `frontend/src/test/workflows.test.tsx`

Read-only regressions cover Project, Context, Objects, Relationships, Evidence,
Reports, Memory, Guidance, operations/readiness and all migrations.

No new authorization production file is required. The already-created-in-plan
`backend/app/repositories/discipline_package_unit_of_work.py` owns the guarded
authority loader alongside its guarded Session. The only added modifications
are `backend/app/repositories/onboarding_repository.py` and
`backend/app/services/onboarding_service.py`, limited to making member mutation
and reset locking follow User -> membership -> Organization and replacing the
late admin-count lock with one ascending-ID target/active-admin User lock set
before membership. Existing future transaction and security test files own all
focused race vectors, so the test manifest gains no new path.

### Migration manifest

Exactly three future files, and no others:

- `backend/migrations/versions/e05100000001_registry_configuration_audit.py`
- `backend/migrations/versions/e05100000002_workspace_binding_shadow.py`
- `backend/migrations/versions/e05100000003_workspace_binding_cutover.py`

None is created or executed by IDS design.

## 32. EDS observation closure map

| Observation | Implementation component | Migration/preflight | Validation evidence | Batch |
|---|---|---|---|---|
| `EDS051-OBS-01` live deployed-data census | read-only `discipline_package_preflight.py` and artifact validator | required before M1 and revalidated before M2/M3; unknowns stop | future deployment-specific canonical JSON/digest plus preflight tests; **not complete today** | 2/3 |
| `EDS051-OBS-02` historical Registry anchoring | explicit retained source release table, historical resolver and readiness | M1 projection retains immutable releases; preflight checks every referenced digest | golden source/projection vectors, missing-anchor readiness and historical-read tests | 1/2/4 |
| `EDS051-OBS-03` cutover choreography | operations readiness, compatibility-capable A/B application and deployment runbook sequence | exact M1 -> projection -> M2 -> backfill/M3 order with writer drain | future deployment attestation, head/count/checksum/readiness evidence; **not executed today** | 2–5 |
| `EDS051-OBS-04` composite tenant keys | supporting Project/Workspace unique keys and composite FKs | M1 constraint ownership; M2 binding FK validation; M3 final trigger | migration introspection and cross-tenant negative tests | 2/3 |

## 33. Critical implementation risks and open questions

| Risk | Frozen mitigation / stop condition |
|---|---|
| deployed values differ from repository assumptions | mandatory fail-closed census; Human remediation before migration |
| old writers cannot tolerate shadows/final state | A/B deployment and verified writer drain |
| projection/source drift | exact row/hash reconciliation and readiness failure |
| deadlock or stale authority | identity-only request DTO; membership/User/Organization `FOR UPDATE` prefix retained through commit; Project/Workspace resource locks; one frozen order and whole-transaction retry with authority reread |
| cross-tenant association | composite DB FKs plus protected authorization tests |
| historical source accidentally removed | append-only explicit release table and reference/readiness gate |
| trigger false positive during cutover | install only after exact backfill and force validation in controlled window |
| aggregate ownership erosion | typed ports, no parallel stores and owner-preservation regressions |
| PATCH-052 content leaks into Core | empty production descriptor and conformance firewall |

Open implementation-design questions: **NONE**. Deployment-specific census
results, release identifiers/digests for later operational packages and actual
execution timing are evidence/authority inputs, not unresolved IDS decisions.
Any future contradiction in repository/deployment evidence stops the applicable
batch and returns to governed design; implementation must not improvise.

## 34. PATCH boundary and Human authority preservation

PATCH-051 supplies Core contracts and seams only. It contains no operational
Electrical, Instrumentation or Control & Automation descriptor, rule, catalog,
workflow or UI behavior. Boundaries remain:

| Future boundary | PATCH-051 seam only; prohibited pull-forward |
|---|---|
| PATCH-052 | descriptor/conformance entry point only; no E/I/C operational package content |
| PATCH-053 | typed interface declarations only; no cross-discipline reasoning, propagation or conflict resolution |
| PATCH-054 | standards hook IDs only; no standards corpus, applicability or compliance behavior |
| PATCH-055 | Evidence requirement declarations only; no Evidence Workbench |
| PATCH-056 | contract extension seams only; no methods/systems product behavior |
| PATCH-057 | compiled frontend metadata keys only; no future product-experience expansion |
| PATCH-058 | existing authentication/active-Organization composition only; no commercial security redesign |
| PATCH-059 | entitlement port plus `NOT_REQUIRED` adapter only; no signed entitlement enforcement |
| PATCH-060 | readiness/deployment evidence seam only; no deployment qualification implementation |

Human engineering authority, existing aggregate ownership and accepted Report/
Memory/Evidence decisions remain authoritative. This IDS grants no autonomous
package approval, acceptance, procurement, vendor selection, authoritative
BOM/MTO/BOQ, conflict resolution or mutation of accepted authority.

## 35. Review readiness and exact stop point

This twice-remediated IDS specifies module ownership, dependency direction, all
twelve tables, four Workspace fields, three migrations, composite tenant keys,
transactions/locks, ten accepted endpoints, frontend behavior, readiness,
cutover, recovery, test/conformance ownership and five implementation batches.
A later Implementation Plan needs only to authorize exact sequencing/manifests;
it must not invent schema, mutable authority facts, authority rows, lock order,
request/guarded Session boundaries, revocation linearization, retry authority,
race tests, API, ownership or security decisions.

Implementation Plan readiness answer: **YES**. The Second Focused Independent
IDS Re-review is `PASS / ACCEPTED` and Human IDS Acceptance is `PASS /
GRANTED`; Implementation Plan-051 is therefore eligible for separate Human
design authority but remains `NOT STARTED`. A future Plan can sequence
execution without inventing cross-release profile persistence,
Session or transaction ownership, commit/rollback or Audit staging semantics,
commit-stable authorization, retry ownership, Registry mutation authority,
grants, or the deployment/runtime principal boundary.

`IDS051-MAJ-01`, `IDS051-MAJ-02`, `IDS051-FRR-MAJ-01` and `IDS051-MAJ-03` are
**RESOLVED**. `IDS051-MAJ-01` and `IDS051-MAJ-03` remain **RESOLVED / CLOSED**
without redesign.
`IDS051-MIN-01` is **RESOLVED / CLOSED** by consistently bounding Workspace-
selectable states at six and excluding reserved `shared_engineering`.
`IDS051-OBS-01` remains **OPEN / NON-BLOCKING** because live deployment census,
query-plan, role-introspection and cutover attestations are future evidence.
New Critical/Major/Minor/Observation findings introduced by remediation are
`0/0/0/0`.

IDS-051 is **ACCEPTED / COMPLETE** and its IDS Gate is **PASS / ACCEPTED**.
The initial Independent IDS Review and first Focused Independent IDS Re-review
remain `FAIL / STOPPED`; the Second Focused Independent IDS Re-review remains
`PASS / ACCEPTED`. `IDS051-OBS-01` remains `OPEN / NON-BLOCKING / DOWNSTREAM
IMPLEMENTATION / DEPLOYMENT EVIDENCE OBLIGATION` and does not reopen IDS. The
exact next resume point is separately granted Human Implementation Plan-051
design authority. Do not create that Plan, begin implementation, create/execute
migrations, close PATCH-051 or begin PATCH-052 in this operation.
