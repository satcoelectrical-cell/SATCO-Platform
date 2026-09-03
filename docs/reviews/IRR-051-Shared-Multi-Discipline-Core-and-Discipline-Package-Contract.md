# IRR-051 — Shared Multi-Discipline Core & Discipline Package Contract

## 1. Review control and verdict

| Field | Result |
|---|---|
| PATCH | PATCH-051 — Shared Multi-Discipline Core & Discipline Package Contract |
| Authority | **HUMAN INDEPENDENT IMPLEMENTATION READINESS REVIEW-051 AUTHORITY: GRANTED** |
| Mode | Independent Implementation Readiness Review only |
| Verdict | **FAIL / STOPPED** |
| Critical / Major / Minor / Observation | **0 / 2 / 0 / 0** |
| Implementation Plan state reviewed | PROPOSED / COMPLETE / READY FOR INDEPENDENT IMPLEMENTATION READINESS REVIEW |
| Implementation Plan final review state | **PROPOSED / NOT IMPLEMENTATION-READY** |
| Implementation | **NOT AUTHORIZED** |
| Migration creation / execution | **NOT AUTHORIZED / NOT AUTHORIZED** |

The accepted Architecture, ADR, EDS and IDS remain coherent and implementable.
The five-Batch Plan faithfully carries most of that basis into repository work,
but two material Plan-level omissions prevent a bounded implementation agent
from completing the accepted cross-process serialization and database-principal
bootstrap without reconstructing security-critical decisions. This review does
not amend or Human-accept the Plan and grants no execution authority.

## 2. Inputs and repository baseline

The review inspected PATCH-051, accepted Architecture-051, ADR-024, accepted
EDS-051 and focused persistence reconciliation, accepted IDS-051, relevant
review/remediation/Human-acceptance chronology, Implementation-Plan-051, and the
actual backend/frontend/test/deployment topology.

Repository evidence confirms:

- synchronous SQLAlchemy `SessionLocal` with `autocommit=False`;
- mutable authority on actual User, membership, Organization and Project rows;
- current onboarding lock-order adaptations identified by the IDS;
- current committing generic Audit helper and a viable narrow staging addition;
- existing one-Workspace-per-Project-and-Discipline uniqueness;
- real PostgreSQL integration/concurrency patterns through `TEST_DATABASE_URL`;
- migration/runtime separation in `backend/migrations/env.py`;
- runtime role provisioning in `postgres/init/001_satco_database_roles.sh`
  and `ops/scripts/preflight.sh`;
- no current `satco_registry_installer` provisioning or secret wiring;
- all planned CREATE application paths are absent and correctly located;
- all planned MODIFY application/frontend paths exist; and
- sole repository Alembic head `e04700000001`, with no PATCH-051 migration.

The planned linear chain remains mechanically possible:

~~~text
e04700000001
→ e05100000001
→ e05100000002
→ e05100000003
~~~

## 3. Traceability and five-Batch dependency review

All accepted functional obligations have a named owner: identity/contracts,
source Registry, canonicalization/digests, compatibility, projection and
historical resolution, Organization/Project configuration, Workspace binding,
UoW/authority/Audit, preflight, migrations, API/frontend, conformance, tenant
security, bounds and preservation.

The Batch DAG is otherwise valid:

1. Batch 1 supplies pure contracts/source Registry/conformance.
2. Batch 2 supplies models, projection, UoW, Audit staging, role validation,
   preflight and M1/M2.
3. Batch 3 consumes those foundations for guarded configuration/binding/M3.
4. Batch 4 consumes stable services for API/frontend integration.
5. Batch 5 validates the complete product surface.

No functional Batch depends on an application artifact introduced later.
Batch-level manifest review, separate Human authority, focused evidence,
independent review and Human acceptance are explicitly required before the
next Batch.

## 4. Readiness results

| Area | Result | Independent review |
|---|---|---|
| Batch 1 / identity / contracts | PASS | Typed identities, strict descriptors/contributions, static adapters and seams resolve to accepted EDS/IDS details; no operational package is introduced. |
| Registry digest semantics | PASS | Registry, descriptor, selected-set, profile and combination digests remain distinct; NFC canonical JSON/SHA-256 ownership is in Core. |
| Compatibility | PASS | Core range, dependencies, conflicts, allow-lists, profiles, collisions, migration guards, budgets and closed fail-safe reasons are accepted and test-owned. |
| M1 persistence | PASS | Twelve-table model and reconciled semantic-profile/release-membership keys are fixed; exact Project provenance is available from IDS. |
| R1/R2 profile case | PASS | One P/D semantic row, separate immutable R1/P and R2/P memberships, exact historical lookup, no overwrite. |
| M2 | PASS | Pure additive nullable Workspace shadows, NOT VALID FK/index/check setup, no backfill/cutover. |
| M3 | PASS | Writer drain, six exact mappings, counted chunked backfill, validation, enforcement/triggers and STOP conditions are fixed; no fabricated config/binding. |
| Live preflight | PASS | Read-only repeatable-read evidence, digest, Human/operator review and wrapper verification provide a downstream owner for IDS051-OBS-01. |
| Migration authority boundary | PASS | Creation and execution remain separately authorized; the Plan does not infer live execution. |
| Registry projection | PASS | Source is authority; projection install/reconcile/activate, drift, current pointer and historical retention are fixed. |
| DB privilege matrix | PASS | Migration owner, installer and runtime permissions are exact; no customer/runtime projection authorship. |
| Role bootstrap integration | **FAIL — IRR051-MAJ-02** | Required installer provisioning/secret delivery has no executable repository or external operations owner in the Plan manifest. |
| Advisory guard | **FAIL — IRR051-MAJ-01** | Plan omits the accepted immutable lock identity and does not explicitly require SHARED mode for each runtime configuration mutation. |
| UoW / Session boundary | PASS | Fresh Session per attempt, one outer completion owner, same connection and new retry are concrete. |
| Authorization / revocation / deadlock | PASS subject to MAJ-01 | User → membership → Organization prefix, Project/resource locks, ascending User/Workspace order and two legal revocation schedules are clear; no row-lock cycle found. |
| Organization/Project configuration | PASS subject to MAJ-01 | Authority, exact pin/provenance, immutable history, compatibility, rebind, Audit, retry and completion are defined. |
| Workspace binding / invariant | PASS | Project-derived E/I/C binding, future-unavailable and unresolved states preserve unique Project/Discipline ownership. |
| Legacy translation | PASS | Source-qualified exact mappings preserve `control`, `industrial_automation`, `automation` and `automation_and_control` distinctions; no fuzzy/global rewrite. |
| Audit | PASS | Tenant package Audit and generic Workspace Audit stage without completion in the same guarded transaction; legacy committing helper is explicitly excluded. |
| API / frontend | PASS | Ten accepted routes and server-derived typed UI surfaces are available from accepted IDS; no operational package route/UI. |
| Tenant isolation | PASS | Scope ordering, composite FKs, tenant Audit, protected 404 and negative tests have concrete owners. |
| Resource bounds | PASS | EDS/IDS exact registered/executable, selection, graph, byte and contribution bounds are assigned to schemas/Core/services/tests with no silent truncation. |
| Historical preservation | PASS | Releases, memberships, revisions, raw Workspace identity, Report, Memory and Audit remain immutable/retained. |
| Recovery | PASS | Empty-only early downgrade is distinguished from forward repair after use; no destructive head rewind/history deletion. |
| Test manifest | PASS | Registry/digests/compatibility/projection/configuration/Workspace/transaction/security/roles/legacy/migrations/frontend/performance are covered. |
| PostgreSQL evidence | PASS | Plan expressly requires two independent PostgreSQL Sessions/barriers; role/advisory/concurrency evidence is PostgreSQL-specific and cannot be satisfied by SQLite. |
| Manifest reality | FAIL only as MAJ-02 | Application paths are valid; the missing installer deployment/provisioning path is material. |
| Alembic reality | PASS | Sole head and proposed three-revision linear chain have no collision. |
| Human/PATCH boundary | PASS | No autonomous engineering authority or PATCH-052–060 pull-forward. |

## 5. Finding register

### IRR051-MAJ-01 — Accepted advisory guard identity and runtime mode are not carried into the Plan

**Severity:** MAJOR / BLOCKING.

**Plan statement:** Implementation-Plan-051 sections 3 and 5 require a
“Registry advisory guard”, same checked-out connection and exclusive installer
activation, but do not state the fixed two-key PostgreSQL identity, the exact
shared/exclusive SQL operations, or that every Organization configuration,
Project configuration/rebind and guarded Workspace-create transaction takes the
SHARED guard before any other SQL/DB lock.

**Accepted design evidence:** IDS-051 section 11 fixes
`acquire_package_registry_guard(session, mode: SHARED | EXCLUSIVE)`,
`SET LOCAL lock_timeout = '5s'` as the first statement, shared
`pg_advisory_xact_lock_shared` versus exclusive `pg_advisory_xact_lock`,
and immutable keys `(1396790339, 51)`. EDS-051 section 21.1 requires exclusive
projection install/activation and shared runtime configuration locks held
through commit.

**Risk:** a bounded implementation agent could select another key, use
exclusive runtime locking, omit shared locking on one guarded mutation, or
acquire it after protected SQL. Different workers/jobs would then fail to
serialize Registry activation against validation/configuration commit,
reopening the accepted cross-process consistency defect.

**Minimum remediation:** a focused Plan amendment must carry the exact helper
contract, `(1396790339, 51)`, 5-second local timeout/first-SQL rule, EXCLUSIVE
installer activation, SHARED Organization/Project/rebind/Workspace-create
guard, same Session/connection and transaction-held release semantics into the
Batch 2 foundation, Batch 3 flows, focused tests and acceptance criteria. No
Architecture/ADR/EDS/IDS change is required.

### IRR051-MAJ-02 — Installer-principal bootstrap has no executable Plan owner or authorized path

**Severity:** MAJOR / BLOCKING.

**Plan statement:** section 5 says “External provisioning makes” the
migration/schema, `satco_registry_installer` and `satco_runtime` roles and
secrets, then M1 applies grants. The production/test manifests contain no
deployment/provisioning artifact or explicit governed external runbook/evidence
owner for creating the installer role and delivering its deployment-only
credential before M1/installer use.

**Repository evidence:** `postgres/init/001_satco_database_roles.sh` provisions
only `satco_runtime`. `ops/scripts/preflight.sh` operationally creates or
validates only `satco_runtime`. `docker-compose.yml` and
`docker-compose.production.yml` wire runtime and migration credentials but no
Registry-installer credential/service/job. M1 requires the role to pre-exist and
the FastAPI process must never receive its secret.

**Risk:** an implementation constrained to the Plan manifest cannot establish
the prerequisite in actual dev/test/production topology. M1 will fail on a
missing role, or an implementer will invent an ad hoc role/secret path that may
leak installer authority into runtime, bypass NOINHERIT constraints, or evade
review and reproducibility.

**Minimum remediation:** the focused Plan amendment must assign one exact
governed owner before M1: either add repository-conventional provisioning,
secret/config and controlled installer-job paths to Batch 2 manifests, or name
a separately governed external provisioning artifact/operator procedure with
exact preconditions and evidence. It must require fail-closed absence, exact
`LOGIN NOINHERIT NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION
NOBYPASSRLS`, separation from runtime/migration, no FastAPI secret exposure,
and real-PostgreSQL bootstrap/grant tests. No Architecture/ADR/EDS/IDS change
is required.

## 6. Finding counts and disposition

| Classification | Count |
|---|---:|
| Critical | 0 |
| Major | 2 |
| Minor | 0 |
| Observation | 0 |
| Blocking findings | 2 |
| Non-blocking findings | 0 |

`IDS051-OBS-01` remains **OPEN / NON-BLOCKING / DOWNSTREAM IMPLEMENTATION /
DEPLOYMENT EVIDENCE OBLIGATION**. The Plan assigns its preflight mechanism
correctly; no live evidence is fabricated and the Observation is not resolved
by this review.

## 7. Verdict and authority

**IRR-051: FAIL / STOPPED.**

Implementation-Plan-051 remains **PROPOSED / NOT IMPLEMENTATION-READY**.
Implementation is not eligible for Human implementation authority until
`IRR051-MAJ-01` and `IRR051-MAJ-02` receive minimum focused Plan
remediation and an independent focused re-review closes both with Critical and
Major counts zero.

No upstream reconciliation is required. Architecture-051, ADR-024, EDS-051,
focused persistence reconciliation and IDS-051 remain accepted. PATCH-051
remains REGISTERED / OPEN; PATCH-052 remains NOT STARTED; the Commercial V1
roadmap remains HUMAN-FROZEN / UNCHANGED.

The exact next resume point is separately granted **focused
Implementation-Plan-051 remediation authority limited to IRR051-MAJ-01 and
IRR051-MAJ-02**. This review grants no remediation, Plan acceptance,
implementation, migration creation/execution, deployment, PATCH closure or
PATCH-052 authority.
