# EDS-051 Focused Independent Engineering Design Re-review

## 1. Authority, scope and verdict

| Field | Result |
|---|---|
| Human authority | HUMAN FOCUSED INDEPENDENT EDS-051 RE-REVIEW AUTHORITY: GRANTED |
| Target | `docs/design/EDS-051-Shared-Multi-Discipline-Core-and-Discipline-Package-Contract.md` |
| Historical review | `FAIL / STOPPED`; Critical/Major/Minor/Observation `0/3/1/4` |
| Focused scope | `EDS051-MAJ-01`, `EDS051-MAJ-02`, `EDS051-MAJ-03`, `EDS051-MIN-01` and direct consistency surfaces only |
| Focused verdict | **PASS / ACCEPTED** |
| New Critical / Major / Minor / Observation | **0 / 0 / 0 / 0** |
| EDS-051 Human acceptance eligibility | **ELIGIBLE FOR HUMAN EDS ACCEPTANCE** |

This is not another broad EDS review. Unrelated passing conclusions were not
reopened. This artifact does not amend EDS-051 or the historical review,
Human-accept the EDS, authorize IDS, Implementation Plan, implementation or
migration, begin PATCH-052, or alter Architecture-051, ADR-024 or the
Human-frozen Commercial V1 roadmap.

## 2. EDS051-MAJ-01 — profile membership cardinality

**RESOLVED / CLOSED.**

The remediated relational member identity is:

```text
PK (profile_id, profile_digest, combination_digest, package_key)
FK (profile_id, profile_digest)
    -> discipline_package_compatibility_profiles
FK (package_key, package_version, descriptor_digest)
    -> discipline_package_descriptors
```

The profile model is coherent:

- each combination contains at most one exact version per PackageKey;
- the same PackageKey can carry a different version in another combination
  because that combination has a different canonical digest;
- the PK rejects duplicate PackageKey membership within one combination;
- source validation rejects duplicate semantic combinations before projection,
  and grouped projection validation recomputes the combination digest;
- member order is non-semantic and canonicalized by PackageKey, version and
  DescriptorDigest; combination order is non-semantic and canonicalized by
  combination digest;
- CompatibilityProfileDigest covers the sorted full member arrays and their
  combination digests, so any membership change changes profile provenance;
- the Project-selected set must match exactly one source-authoritative allowed
  combination; and
- the member table remains a release-installed derived integrity projection,
  never a customer-editable registry or compatibility authority.

The referenced profile PK and descriptor unique triple make both composite FKs
relationally valid. The lookup/index shape matches the corrected PK. M1 can
create this design without adding a migration stage or new authority table.
`CompatibilityCombinationDigest` is internal and cannot substitute for
Registry, Descriptor, selected-set or profile provenance.

## 3. EDS051-MAJ-02 — atomic Project/Workspace rebinding

**RESOLVED / CLOSED.**

Every current `OPERATIONAL_PACKAGE_BOUND` Workspace in a changed configured
Project is deterministically affected, regardless of whether only a profile or
an unrelated package changed. This conservative rule removes materiality
judgment from IDS and keeps every derived binding on the current Project head.

The transaction establishes the accepted authority invariant:

1. acquire the shared Registry/configuration guard;
2. read the guarded current Registry;
3. lock Organization state, Project, Project head and every operational
   Workspace in Workspace-ID order;
4. validate the complete target set and each Workspace's exact PackageKey,
   canonical Discipline, executable standing, Organization enablement,
   compatibility and migration guard;
5. insert one immutable Project revision and its exact selections;
6. advance every affected Workspace's derived revision pointer;
7. advance the Project head;
8. insert one Project event and at most seven Workspace rebind events; and
9. commit once.

Project remains sole version authority. Workspace keeps only the key/revision
needed to resolve the Project selection and cannot choose a version. One
invalid Workspace returns `WORKSPACE_REBIND_INCOMPATIBLE` and rolls back the
revision, every binding, head and Audit. Future-unavailable and unresolved rows
are explicitly excluded and remain truthful. Forward rollback uses the same
new-revision transaction, never a head rewind.

The deferred consistency trigger is coherent defense in depth: at commit, each
operational Workspace must reference the current Project head and a selection
for its PackageKey. It does not replace application validation or locking. No
partial rebind, Workspace-only rebind or Project-only head advance can commit.

## 4. EDS051-MAJ-03 — Registry/configuration serialization

**RESOLVED / CLOSED.**

The fixed PostgreSQL two-key transaction advisory-lock identity
`(1396790339, 51)` provides database-wide, cross-process serialization for all
workers/deployment jobs sharing the SATCO database:

- Registry install/activation obtains
  `pg_advisory_xact_lock(1396790339, 51)` exclusively;
- Organization and Project/rebind mutations obtain
  `pg_advisory_xact_lock_shared(1396790339, 51)`; and
- every path acquires the guard before current-Registry, tenant, Project or
  Workspace locks and holds it through transaction completion.

An exclusive activation cannot linearize while a shared configuration commit
is in flight. A configuration cannot validate R1, allow R2 to become current,
then commit newly against R1. If activation wins first, the later configuration
reads and validates R2. The configuration commit and Registry activation commit
are their respective linearization points.

The lock graph has no designed inversion: Registry activation takes no tenant,
Project, Workspace or tenant-Audit lock; configuration never upgrades shared to
exclusive; Organization replacement and Project change use compatible global
order and conflicting `FOR UPDATE`/`FOR SHARE` Organization locks; Project and
Workspace locks are then ordered. A process-local mutex is neither used nor
sufficient.

Five-second lock timeout and complete-transaction retry do not weaken the
invariant. Configuration retries at most twice from fresh guarded state and
then returns safe conflict. Activation failure/timeout rolls back, leaves the
prior release current and requires deployment retry. Transaction-scoped
advisory locks release on commit/rollback, so no timeout path permits stale
authority.

### Race exercise

| Case | Verified outcome |
|---|---|
| Project shared guard first; activation requests exclusive | activation waits; Project validates/rebinds/Audits/commits, then activation may switch |
| Activation exclusive first; Project requests shared | Project waits, then reads and validates the newly current release |
| Two changes to one Project | Project/head row locks plus expected-version check serialize; stale attempt safely conflicts |
| Multiple Workspaces; one migration guard fails | no revision, binding, head or Audit commits |
| Activation times out | activation transaction rolls back; prior release remains current |
| Configuration exhausts timeout/retry | safe `CONCURRENT_UPDATE`; no stale or partial commit |

## 5. EDS051-MIN-01 — tenant/global Audit boundary

**RESOLVED / CLOSED.**

`package_configuration_audit_events` now contains only truthful
`ORG_CONFIGURATION`, `PROJECT_CONFIGURATION` and `WORKSPACE_BINDING` events.
`REGISTRY_PROJECTION`, `projection_install` and equivalent global lifecycle
events are absent. No Organization ID is fabricated or replicated across
tenants.

Global Registry evidence is truthfully owned by the source release manifest,
installed Registry release/provenance and deployment orchestrator's structured
release evidence. It is not exposed by the tenant Audit endpoint. Configuration
and bounded Workspace rebind Audit uses the mutation unit of work, contains
minimized scope/version/provenance metadata and rolls back with the authority
change. `A051-OBS-02` remains resolved.

## 6. Direct consistency review

| Surface | Result |
|---|---|
| persistence | PASS — corrected profile PK/FKs/indexes are consistent; four Workspace fields remain non-conflicting; deferred trigger agrees with current-head semantics |
| migration | PASS — M1 creates corrected membership key, M2 remains additive, M3 installs consistency enforcement only after backfill/validation; sequence remains `e05100000001` → `e05100000002` → `e05100000003` |
| API/DTO | PASS — no new route or caller-selected combination; internal match is server-derived; responses resolve the committed current binding |
| Audit | PASS — at most seven rebind events per Project change; tenant scope is truthful; no success event survives rollback |
| digest semantics | PASS — subordinate combination digest is unambiguous and does not disturb the four accepted provenance roles |
| conformance design | PASS — covers multiple combinations/versions, duplicate rejection, multi-Workspace success/rollback, Project/Organization Registry races, both acquisition orderings, timeout/retry, Audit atomicity and global-event exclusion |
| live census/cutover/composite keys | unchanged non-blocking downstream obligations |

The future IDS must instantiate the already-required race vectors with both
shared-first and exclusive-first scheduling and the specified timeout/retry
outcomes. That is test decomposition, not an unresolved EDS decision.

## 7. Architecture, ADR and observation disposition

No new Architecture or ADR decision was introduced. Project remains exact
version authority; Workspace inheritance, registry source authority, derived
projection, static adapters, lifecycle, typed provenance, authorization order,
tenant isolation, Human authority, entitlement seam, resource bounds and later
PATCH firewalls remain unchanged.

- Architecture-051: **CONFORMS / NO AMENDMENT REQUIRED**.
- ADR-024: **CONFORMS / NO AMENDMENT REQUIRED**.
- `A051-OBS-01`, `A051-OBS-02`, `A051-OBS-03`: remain **RESOLVED**.
- Existing review observations `EDS051-OBS-01` through `EDS051-OBS-04`: remain
  non-blocking downstream obligations; none became false or blocking.
- New Critical/Major/Minor/Observation: **0/0/0/0**.

## 8. Final finding register and governance result

| Finding | Focused re-review status |
|---|---|
| `EDS051-MAJ-01` | **RESOLVED / CLOSED** |
| `EDS051-MAJ-02` | **RESOLVED / CLOSED** |
| `EDS051-MAJ-03` | **RESOLVED / CLOSED** |
| `EDS051-MIN-01` | **RESOLVED / CLOSED** |

Blocking findings: **0**. New non-blocking findings: **0**. Required further
EDS amendment: **NONE**. Another broad EDS review is neither required nor
recommended.

Focused Independent EDS-051 Re-review: **PASS / ACCEPTED**.

EDS-051 is **ELIGIBLE FOR HUMAN EDS ACCEPTANCE**. This eligibility is not Human
acceptance and grants no IDS, Implementation Plan, production/test/migration,
implementation or PATCH-052 authority.

The exact next resume point is a separately governed Human EDS-051 Acceptance
decision. Stop before Human acceptance is supplied; do not begin IDS,
Implementation Plan, implementation, migration or PATCH-052.
