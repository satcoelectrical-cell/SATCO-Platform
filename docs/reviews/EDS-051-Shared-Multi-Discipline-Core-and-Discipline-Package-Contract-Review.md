# EDS-051 Independent Engineering Design Review

## 1. Review authority, target and verdict

| Field | Result |
|---|---|
| Human authority | HUMAN INDEPENDENT EDS-051 REVIEW AUTHORITY: GRANTED |
| Target | `docs/design/EDS-051-Shared-Multi-Discipline-Core-and-Discipline-Package-Contract.md` |
| Architecture basis | Architecture-051 `ACCEPTED / COMPLETE`; Architecture Gate `PASS / ACCEPTED` |
| ADR basis | ADR-024 `Accepted` plus applicable accepted ADRs |
| Independent verdict | **FAIL / STOPPED** |
| Critical / Major / Minor / Observation | **0 / 3 / 1 / 4** |
| Human EDS acceptance eligibility | **NOT ELIGIBLE** pending focused remediation and focused independent re-review |

This is an independent EDS review only. It does not amend EDS-051, modify the
accepted Architecture or ADR, Human-accept the EDS, authorize IDS,
Implementation Plan, implementation, migration or PATCH-052, or alter the
Human-frozen Commercial V1 roadmap.

## 2. Independent evidence verification

The review challenged EDS-051 against PATCH-051, accepted Architecture-051 and
ADR-024, Architecture review/remediation/re-review and Human acceptance,
accepted ADR-010/012/014/015/016/020/021/022/023, and current repository
models, migrations, services, authorization, Audit, engineering capability
owners, frontend and tests.

Repository evidence independently confirms:

- the migration graph contains 25 revisions in one linear chain with sole head
  `e04700000001` and no branch head;
- `projects.organization_id` is non-null, but `projects` does not currently
  declare a unique `(id, organization_id)` target;
- `engineering_workspaces` has the closed six-value legacy Discipline check,
  uniqueness `(project_id, discipline)`, no Organization column and no package
  binding fields;
- active Organization is server-derived, and existing Workspace creation uses
  active-Organization Project resolution plus admin/Project-owner authority;
- generic `audit_logs` has no Organization leading key and the current admin
  listing is global; and
- the current frontend selector and workflow tests demonstrate the legacy
  Workspace creation contract, including the known omission of Control from
  the selector.

No live governed customer database was available. The review did not fabricate
data evidence; it assessed whether the EDS makes a live census fail-closed.

## 3. Architecture and ADR conformance

EDS-051 conforms in its primary decisions:

- Discipline and Package are separate typed identities;
- descriptors and static SATCO adapters are source/release authority;
- database registry state is declared derived and non-customer-editable;
- Project owns exact versions and `NOT_CONFIGURED` remains valid;
- Workspace has bound/future-unavailable/unresolved states and no independent
  version input;
- legacy mapping is source-qualified and exact;
- accepted historical artifacts and aggregate ownership remain preserved;
- authorization, configuration and entitlement are separate; and
- the Human-authority and PATCH-052 through PATCH-060 firewalls remain intact.

The findings below do not require an Architecture or ADR change. They require
the EDS to make its own physical and transactional design internally complete.

## 4. Review results by design area

| Area | Result |
|---|---|
| physical footprint | CONDITIONALLY JUSTIFIED — releases/descriptors/memberships, Organization configuration, immutable Project revisions/selections/heads and scoped Audit each have distinct purposes; profile membership needs correction under `EDS051-MAJ-01` |
| source registry authority | PASS — static source, embedded release binding, canonical bytes, collision validation and no runtime plugin path |
| database projection | PASS WITH FINDING — remains derived, but profile projection cardinality is internally inconsistent |
| digest/provenance separation | PASS — Registry, Descriptor, selected-set and profile digest inputs and fields are separate |
| version lifecycle | PASS — executable and historical standing, explicit upgrades/downgrades and no `latest`; subject to atomic Workspace inheritance correction |
| Organization configuration | PASS — Organization-leading state, admin mutation, expected version, retained disabled state and atomic Audit; not entitlement/data authorization |
| Project configuration | PASS WITH FINDING — valid absent head, immutable nonempty revisions and forward rollback are sound; transition propagation is incomplete |
| Workspace binding | FAIL — `EDS051-MAJ-02` permits current Project/Workspace version divergence if implemented literally |
| legacy reconciliation | PASS — all discovered values have source-qualified exact dispositions; no fuzzy/global normalization |
| migration sequence | PASS WITH OBSERVATION — linear three-stage expansion is feasible; writer-drain/cutover choreography remains an IDS obligation |
| live census | PASS — inability to inspect live data now is non-blocking because preflight is mandatory and unknowns stop migration |
| backfill truthfulness | PASS — no Project configuration/binding is fabricated; future and unresolved states remain truthful |
| rollback/recovery | PASS WITH OBSERVATION — forward recovery and non-destructive history are correct; deployment compatibility must be made operationally exact |
| compatibility engine | PASS — deterministic, bounded, closed reason codes, no AI or arbitrary expressions |
| API surface | PASS — the ten endpoints have distinct discovery/configuration/preflight/effective/applicability/Audit purposes and bounded strict DTOs |
| authorization ordering | PASS — engineering-data/source-owner authorization precedes sensitive package facts; predicates intersect rather than union |
| scoped package Audit | PASS WITH MINOR — separate persistence is justified and resolves the generic Audit tenant defect; one global event category conflicts with its Organization-only schema |
| contribution contract | PASS — closed, bounded seams without PATCH-052 operational content |
| frontend | PASS — effective server state and compiled component keys; truthful unavailable state and Control reconciliation |
| aggregate ownership | PASS — Context, Objects, Relationships, Interface Commitments, Evidence, Reports, Memory and Guidance retain authority |
| standards/cross-discipline seams | PASS — typed declarations only; no later-PATCH reasoning/retrieval behavior |
| entitlement seam | PASS — replaceable Core port and current `NOT_REQUIRED` adapter do not grant other predicates |
| resource bounds | PASS — finite, enforceable and sufficient for Commercial V1; different arbitrary limits are not required |
| concurrency | FAIL — registry pointer/configuration serialization is incomplete under `EDS051-MAJ-03` |
| failure semantics | PASS — infrastructure failure is separated from expected unavailable domain states |
| tests/conformance/security | PASS WITH OBSERVATIONS — categories and threats are complete; focused vectors follow from the findings |
| Human authority/PATCH boundary | PASS |
| IDS implementability | **NOT READY** until the three Major choices are removed from IDS discretion |

## 5. Finding register

### EDS051-MAJ-01 — Compatibility profile projection cannot represent every permitted profile

**Severity:** Major — blocking.

**Evidence:** EDS section 4 permits one `CompatibilityProfileV1` to contain
`1..32` exact package combinations. Section 6 defines
`discipline_package_compatibility_members` with primary key
`(profile_id, profile_digest, package_key)` and one exact package version per
row. No combination identity/ordinal exists.

**Impact:** If two allowed combinations in one profile contain different
versions of the same PackageKey, the proposed primary key cannot store both.
The implementation must either discard projection facts, contradict the
profile JSON, or invent an unstated rule that one profile has at most one
version per PackageKey across every combination. That changes database
integrity, canonical profile meaning and compatibility evaluation and cannot be
left to IDS.

**Minimum required remediation:** Freeze one coherent physical rule. Either
(a) constrain a profile to one exact version universe per PackageKey and define
its combinations as subsets, with schema/conformance enforcement, or (b)
represent combination identity in the profile projection and Project binding.
Remove any projection table that has no distinct integrity purpose. Preserve
source descriptor/profile authority and existing digest separation.

### EDS051-MAJ-02 — Project version changes do not define atomic Workspace rebinding

**Severity:** Major — blocking.

**Evidence:** EDS sections 8–9 make Project head the current exact-version
authority while each bound Workspace stores
`bound_project_configuration_revision`. Section 21 says upgrades lock bound
Workspaces and validate migration guards, but never requires affected Workspace
rows to advance to the new revision or defines which rows advance.

**Impact:** A transaction can move the Project head to revision N+1 while an
affected Workspace continues resolving package key/version through revision N.
That makes the Workspace's persisted pointer a conflicting effective version
authority and violates accepted Project ownership and Workspace inheritance.
Rollback has the same ambiguity. Locking alone does not restore the invariant.

**Minimum required remediation:** Define one atomic transition for Project
configure/reconfigure/upgrade/downgrade/rollback that identifies every affected
bound Workspace, validates all migration guards, advances its derived binding
to the new Project revision where its effective package selection changes, and
commits the Project head, Workspace bindings and scoped Audit together. Define
unchanged-selection behavior and preserve old operational-record provenance in
the owning historical records/revisions, not by leaving a conflicting current
Workspace binding.

### EDS051-MAJ-03 — Registry release switching can race a configuration commit

**Severity:** Major — blocking.

**Evidence:** EDS section 4 gives registry synchronization an advisory lock and
atomic current-pointer switch. Section 21 gives configuration transactions a
read/digest check and a final recheck, but does not acquire the same advisory
lock, an incompatible row lock, or serializable isolation that couples the
last standing check to commit.

**Impact:** Under ordinary PostgreSQL `READ COMMITTED`, configuration can
validate release A, release synchronization can commit B (making a selected
version historical/unsupported), and configuration can then commit a new
Project selection observed against A. A pre-commit query without a protecting
lock still has a check-to-commit race. This violates the rule that new
selections use the current executable registry standing.

**Minimum required remediation:** Specify one shared serialization mechanism
between current-release installation and Organization/Project configuration
transactions: the same advisory lock, a current-pointer row lock with
incompatible lock modes, or serializable transactions with bounded retry. The
release digest and standing validated must remain current through the
configuration commit's linearization point.

### EDS051-MIN-01 — Global registry projection event is incompatible with Organization-scoped Audit

**Severity:** Minor — non-blocking by itself, but should be corrected in the
focused amendment because it affects Audit truthfulness.

**Evidence:** `package_configuration_audit_events.organization_id` is mandatory,
but the same table declares category/action `REGISTRY_PROJECTION` /
`projection_install`. Registry installation is release-wide, not an
Organization configuration event.

**Impact:** Implementing the event requires a fabricated Organization, event
duplication per tenant or omission despite the declared category. Any of the
first two weakens Audit meaning or isolation.

**Minimum correction:** Remove global registry installation from the tenant
configuration Audit vocabulary. If operational registry installation evidence
is required, use separately governed deployment/operations evidence without a
fabricated tenant. Keep Organization/Project/Workspace configuration events in
the scoped table.

## 6. Non-blocking IDS observations

- `EDS051-OBS-01` — the mandatory deployed-data census must publish exact
  distinct Workspace values, Engineering Object discipline/family/type tuples,
  relevant free-text identities, null/invalid states, constraints and affected
  counts. Unknown or divergent state stops the migration. No live evidence is
  asserted by this review.
- `EDS051-OBS-02` — source/release retention must prove that every Project-
  referenced historical descriptor and profile remains anchored by a
  source-controlled release artifact; rehashing mutable database JSON alone
  must not turn the projection into historical authority.
- `EDS051-OBS-03` — IDS/Implementation Plan must define expand/dual-write/
  validate/cutover deployment ordering, including draining old Workspace
  writers before the binding-state NOT NULL cutover and proving previous-reader
  compatibility or an explicit maintenance window.
- `EDS051-OBS-04` — the migration manifest must name the supporting candidate
  keys needed by composite tenant FKs, including Project `(id,
  organization_id)` and any Workspace/Project identity used by scoped Audit;
  separate valid FKs must not substitute for parent/child Organization
  equality under ADR-022.

These observations do not independently block EDS acceptance once the Major
findings are resolved. They are mandatory IDS evidence/constraint obligations
and may be verified in the focused re-review where the amendment touches them.

## 7. Observation verification

| Architecture obligation | Review result |
|---|---|
| `A051-OBS-01` executable vs historical lifecycle | **VERIFIED / RESOLVED** — standing, selection prohibition, interpretation and no implicit upgrade are explicit |
| `A051-OBS-02` Organization-scoped package Audit | **VERIFIED / RESOLVED** for configuration events — separate scoped store/read is justified; `EDS051-MIN-01` removes the unrelated global event |
| `A051-OBS-03` digest/provenance separation | **VERIFIED / RESOLVED** — release, descriptor, selected set and profile provenance are distinct |

## 8. Security and historical-integrity conclusion

The EDS adequately addresses source/descriptor/database tampering, digest
confusion, cross-tenant enumeration, configuration privilege escalation,
permission union, alias abuse, collision, exhaustion, downgrade abuse,
frontend disclosure and tenant Audit disclosure at the contract level.

The blocking concurrency findings are security/integrity findings rather than
hardening preferences: they prevent a stale or independently retained version
from becoming newly authoritative. The focused corrections must add negative
conformance vectors for profile projection, release-switch/configuration races
and Project-upgrade/Workspace-binding races.

## 9. Required amendment and re-review boundary

Required EDS amendments are limited to:

1. resolve `EDS051-MAJ-01` profile/projection cardinality;
2. resolve `EDS051-MAJ-02` atomic Project-to-Workspace binding transition;
3. resolve `EDS051-MAJ-03` registry/configuration serialization; and
4. correct `EDS051-MIN-01` global event placement while the Audit section is
   open.

No Architecture-051 or ADR-024 amendment is required. No broad redesign,
operational package content, commercial entitlement design, implementation or
migration is authorized. After a separately authorized focused EDS remediation,
only a focused independent re-review of the changed contracts and their direct
conformance vectors is required; another broad EDS review is not recommended.

## 10. Exact governance state and next action

| Governance item | State after this review |
|---|---|
| PATCH-051 | REGISTERED / OPEN |
| Architecture-051 | ACCEPTED / COMPLETE |
| Architecture Gate | PASS / ACCEPTED |
| ADR-024 | ACCEPTED |
| EDS-051 | INDEPENDENT REVIEW `FAIL / STOPPED`; remains PROPOSED, not Human-accepted |
| Critical / Major / Minor / Observation | `0 / 3 / 1 / 4` |
| Human EDS acceptance | NOT ELIGIBLE |
| IDS-051 | NOT STARTED |
| Implementation / migration | NOT AUTHORIZED / NOT CREATED |
| PATCH-052 | NOT STARTED |
| Commercial V1 roadmap | HUMAN-FROZEN / UNCHANGED |

The exact next resume point is separately authorized focused EDS-051
remediation limited to `EDS051-MAJ-01` through `EDS051-MAJ-03` and
`EDS051-MIN-01`, followed by focused independent re-review. Stop before Human
EDS acceptance, IDS, Implementation Plan, implementation, migrations or
PATCH-052.
