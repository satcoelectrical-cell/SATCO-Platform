# Implementation-Plan-051 — Shared Multi-Discipline Core & Discipline Package Contract

## 1. Status and authority

| Field | Value |
|---|---|
| Human design authority | **HUMAN IMPLEMENTATION PLAN-051 DESIGN AUTHORITY: GRANTED** |
| Focused remediation authority | **HUMAN FOCUSED IMPLEMENTATION-PLAN-051 REMEDIATION AUTHORITY: GRANTED** |
| Historical IRR-051 | **FAIL / STOPPED**; `IRR051-MAJ-01` and `IRR051-MAJ-02` only |
| Focused remediation verdict | **PASS / COMPLETE**; both findings remediated and ready for independent focused re-review |
| Plan status | **PROPOSED / FOCUSED REMEDIATION COMPLETE / READY FOR FOCUSED INDEPENDENT IRR RE-REVIEW** |
| Inputs | Accepted Architecture-051, ADR-024, EDS-051 and focused persistence reconciliation, IDS-051, reviews and Human acceptances |
| PATCH state | PATCH-051 remains **REGISTERED / OPEN** |
| Execution authority | Implementation, migration creation and migration execution are **NOT AUTHORIZED** |
| Next PATCH | PATCH-052 remains **NOT STARTED** |

This is implementation planning only. It establishes the trusted Core contract/configuration foundation—not Electrical, Instrumentation, or Control & Automation operational packages, which remain PATCH-052 work. Each future Batch needs its exact authorized file manifest, independent manifest review, Human implementation authority, bounded implementation, focused evidence, independent implementation review, remediation where necessary, and Human Batch Acceptance.

## 2. Fixed accepted basis and repository reconciliation

Discipline and Discipline Package remain separate typed concepts. The source-controlled Registry is authoritative; the database Registry is an immutable derived projection. Static SATCO-reviewed adapters are compiled into a release: no runtime plugins, uploaded executable code/scripts/SQL, remote Registry, or customer executable bundle. Every selection is an exact package-version pin; implicit latest is prohibited. Compatibility is deterministic and fail-closed.

Organization configuration is distinct from entitlement. PATCH-051 supplies only the `NOT_REQUIRED` entitlement adapter; PATCH-059 owns enforcement. Project state is `NOT_CONFIGURED` or `CONFIGURED`; Workspace states are `OPERATIONAL_PACKAGE_BOUND`, `FUTURE_UNAVAILABLE_UNBOUND`, and `LEGACY_UNRESOLVED`. The existing one Workspace per Project and Discipline invariant remains. E/I/C Workspaces inherit a Project-selected exact version; future disciplines can be valid and unbound. Legacy translation is exact only, never fuzzy/global. No backfill fabricates Project configuration or operational binding. Historical Report, Memory, Audit and raw identity remain preserved.

Standards are applicability-hook identity only; cross-discipline is declaration/interface only. Resource caps are enforced at schemas, canonicalization, Registry assembly, services/queries, Audit and performance gates. No package can approve engineering, admit Memory, accept Reports, procure, select vendors, create authoritative BOM/MTO/BOQ, or resolve conflicts.

The implementation roots are `backend/app`, `backend/migrations/versions`, `backend/scripts`, `backend/tests`, `frontend/src`, and `frontend/src/test`. `backend/app/core/database.py` supplies `SessionLocal`. Existing authentication can derive Organization context, but guarded writes retain only frozen actor User ID, Organization ID, credential `auth_version`, optional correlation ID. Actual mutable authority: `User.is_active`, `User.role`, `User.auth_version`, membership `is_enabled/is_selected`, Organization `is_active`.

`OnboardingService.mutate_member()` and `issue_reset()` presently lock membership before User; only those narrow paths change. `complete_credential()` already has User → membership → Organization. `ProjectRepository.update()` modifies the same Project row later locked by package flows. `EngineeringWorkspaceService` uses committing generic Audit behavior. `services.audit_service.create_audit_log()` commits and is prohibited inside guarded UoW; legacy callers retain existing behavior.

The confirmed sole Alembic head is `e04700000001`; no PATCH-051 migration exists. Exactly three future revisions are fixed: `e05100000001` from `e04700000001`, `e05100000002`, and `e05100000003`.

## 3. Common UoW, authorization, Audit and recovery rules

### 3.1 Exact Registry/configuration advisory-guard contract

`acquire_package_registry_guard(session, mode: SHARED | EXCLUSIVE)` is a
narrow helper in `backend/app/core/database.py`. Its immutable,
non-configurable PostgreSQL two-key identity is **`(1396790339, 51)`**, the
PATCH-051 Discipline Package Registry/configuration serialization domain. It
must never derive a key dynamically, use a process-local mutex, or use
session-lifetime `pg_advisory_lock`/`pg_advisory_lock_shared`.

For every caller the fresh UoW owns one outer transaction and its checked-out
SQLAlchemy Session/connection. The first SQL on that connection is exactly
`SET LOCAL lock_timeout = '5s'`; the second is the mode-specific transaction
lock. No identity, authority, Registry, resource, compatibility, Audit, flush
or other SQL may precede them. The helper opens no Session/connection, starts
no transaction, uses no autocommit, and never commits or rolls back.

| Exact operation | Guard SQL / mode | Session, protected scope and completion |
|---|---|---|
| Registry projection installation, reconciliation that writes, or current-release activation | `SELECT pg_advisory_xact_lock(1396790339, 51)` / **EXCLUSIVE** | Deployment-only installer UoW; after timeout and before every projection read/write, validates source/projection and writes only permitted immutable rows/current pointer; installer UoW alone commits/rolls back and transaction completion releases the lock. |
| Organization package configuration replace | `SELECT pg_advisory_xact_lock_shared(1396790339, 51)` / **SHARED** | Runtime guarded UoW; before User/membership/Organization and configuration-head locks; held through selection/history/Audit commit. |
| Project initial configuration, configuration replace/revision/rebind, and configuration removal | `SELECT pg_advisory_xact_lock_shared(1396790339, 51)` / **SHARED** | Runtime guarded UoW; before authority, Organization configuration, Project/head and ordered Workspace locks; held through revision/head/binding/Audit commit. |
| `EngineeringWorkspaceService.create()` when package applicability/binding is derived, and every PATCH-051 controlled Workspace package-binding mutation | `SELECT pg_advisory_xact_lock_shared(1396790339, 51)` / **SHARED** | Runtime guarded UoW; before authority, Registry/configuration and Project/head/resource locks; held through Workspace/binding/generic/package Audit commit. |

Read-only Registry discovery and non-PATCH-051 legacy Workspace mutations do
not acquire a package guard. These are the complete PATCH-051 runtime
mutations that derive committed state from current Registry/configuration;
no other runtime mutation may derive such state without first being added to
this table with the **SHARED** guard. The universal guarded prefix is:

```text
fresh UoW/Session -> begin outer transaction -> SET LOCAL lock_timeout = '5s'
-> advisory xact guard -> User -> membership -> Organization
-> Registry/configuration -> Project -> Project head
-> Workspaces by ascending ID -> writes -> staged Audit -> outer commit/rollback
```

An EXCLUSIVE activation/install first makes a runtime SHARED operation wait,
then reread the new current Registry before validation. A runtime SHARED
operation first makes activation wait through its commit/rollback. Thus no
runtime configuration can validate one current release and commit derived state
after another became current. PostgreSQL lock-timeout, deadlock or serialization
failure fails closed: the outer UoW rolls back, writes no protected state and
retains no success Audit. The configuration/Workspace outer retry performs at
most two complete fresh attempts; each restarts at the timeout statement,
reacquires the guard/authority/resource locks and rereads Registry/configuration.
Registry activation has no internal retry; the deployment orchestrator starts a
new installer UoW.

### 3.2 Deployment principal bootstrap and installer-secret boundary

Batch 2 extends the existing deployment/database bootstrap rather than creating
a parallel framework. `postgres/init/001_satco_database_roles.sh` owns clean
database initialization of both restricted fixed login roles.
`ops/scripts/preflight.sh`, in its existing `before` phase and under the
schema/migration credential, owns create-or-validate of both roles for existing
databases before Alembic runs. It is deployment bootstrap, not Alembic: the
migration only requires roles and applies object grants/revokes. Missing or
invalid fixed roles make preflight fail closed; M1 must not dynamically create
login roles, and its required-role/GRANT failure also rolls the migration back.

Both paths enforce `satco_runtime` under its existing contract and
`satco_registry_installer` as a direct deployment CLI login with
`LOGIN NOINHERIT NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION NOBYPASSRLS`,
no unintended `pg_auth_members` membership, no schema CREATE, no object
ownership and no application/table privilege before M1. The installer has no
historical DELETE authority and receives only M1's exact projection grants.

`docker-compose.production.yml` owns the protected secret-file interface:
`registry_installer_db_password` is sourced from
`SATCO_REGISTRY_INSTALLER_DB_PASSWORD_FILE`, mounted read-only only into the
migration bootstrap job and a new deployment-only `registry-installer` job.
The ordinary backend, frontend and operations-monitor services receive neither
the secret nor its environment variable. The job invokes
`backend/scripts/discipline_package_registry.py` using the installer identity
and `SATCO_REGISTRY_INSTALLER_DATABASE_PASSWORD_FILE`; no password is logged,
rendered to frontend/configuration output, persisted in Registry/Audit, or
committed to source control. `docker-compose.yml` and the init script preserve
the same local/bootstrap role shape; test bootstrap follows the same shape.

The deployment order is fixed:

```text
database/deployment bootstrap
-> create or validate satco_registry_installer and secret
-> create or validate existing satco_runtime
-> before-phase role/preflight evidence
-> Alembic M1 grants/revokes
-> installer privilege self-check -> runtime privilege/readiness check
-> Registry projection installation -> Registry activation
-> later runtime configuration
```

Before an installer write, the CLI checks `current_user`, `pg_roles`,
`pg_auth_members`, schema privilege, six-table SELECT/INSERT, column-level
`UPDATE(is_current)`, denied DELETE/broad UPDATE and absent tenant configuration
authority using PostgreSQL privilege introspection; mismatch exits before lock
or write. Runtime readiness analogously proves the `satco_runtime` identity,
attributes/membership/schema restrictions, projection SELECT and absent
INSERT/UPDATE/DELETE while retaining accepted tenant configuration rights; it
uses introspection rather than mutation to prove denial where possible.

The before-phase bootstrap emits a canonical, secret-free operations evidence
record at `artifacts/patch-051/roles/<deployment-id>-<db-fingerprint>.json`
outside source control. It records deployment/tool identity, role existence and
attributes, membership absence, secret-file presence (never value), M1
prerequisite state and later installer/runtime validation outcomes. The
deployment preflight/review owner retains it with the migration census artifact.
This supports implementation/review evidence only; representative production
qualification remains PATCH-060 and `IDS051-OBS-01` remains open.

Create `SqlAlchemyDisciplinePackageUnitOfWork` in `backend/app/repositories/discipline_package_unit_of_work.py`, constructed from `SessionLocal`. Every guarded attempt creates a fresh Session, starts one outer transaction, obtains advisory guard on that same checked-out connection, binds all repositories/staging helpers, and has exactly one outer commit/rollback owner. Repositories, authorization, compatibility, Workspace helpers and Audit staging may add/flush/raise only. Retry only accepted timeout/deadlock/serialization failures, at most two retries, each with fresh UoW/Session/connection/guard and all reads repeated; exhaustion is `409 CONCURRENT_UPDATE`. Registry activation has no internal retry.

~~~text
Registry advisory guard
→ actor User FOR UPDATE
→ exact UserOrganizationMembership FOR UPDATE
→ Organization FOR UPDATE
→ Registry/configuration state
→ Project FOR UPDATE
→ Project head FOR UPDATE
→ affected Workspaces FOR UPDATE by ascending ID
→ writes → staged Audit → outer commit
~~~

The guarded loader receives only frozen identity—not request Session/ORM, role, membership, or a prior permission result. It requires active User, matching locked auth version, current allowed role, enabled/selected membership and active Organization. Project paths require locked tenant/owner predicates; Workspace ownership is not authority. Multi-admin removal locks the target and active-admin User set in ascending User-ID before membership locks. Revocation-first makes mutation reread/reject with no protected write/Audit; mutation-first commits under locked current authority before later revocation. A direct fixture update tests Organization deactivation because no production disable service exists.

Add `stage_audit_log(session, ...)` next to the legacy committing generic helper. It adds/optionally flushes but never completes. Package Audit stages in the same Session. Guarded Workspace create uses staging, never `_audit_and_commit()` or `create_audit_log()`. Any authority, validation, flush, Audit or commit failure rolls configuration/revision/binding/Workspace and success Audit back atomically. After new schema/projection/configuration/binding/Audit is used, recovery is forward-only: preserve history and repair by new audited forward revision.

## 4. Batch 1 — Core contract, trusted Registry and conformance

**Objective:** build pure deterministic Core identity, strict contracts/contributions, canonicalization/digests, explicit empty release, static adapters/source Registry, compatibility, exact legacy translator, conformance and entitlement/standards/cross-discipline seams. No DB dependency where unnecessary.

| Action | Exact files |
|---|---|
| CREATE production | `backend/app/discipline_packages/{__init__,identity,contracts,contributions,canonical,registry,compatibility,legacy,conformance}.py`; `backend/app/discipline_packages/descriptors/__init__.py`; `backend/app/discipline_packages/descriptors/releases/__init__.py`; `backend/app/discipline_packages/descriptors/releases/release_051_core_v1.py`; `backend/app/enums/discipline_package.py`; `backend/app/ports/discipline_package.py`; `backend/app/adapters/discipline_package_registry.py`; `backend/app/exceptions/discipline_package.py` |
| MODIFY production | `backend/app/enums/__init__.py` |
| CREATE tests | `backend/tests/test_discipline_package_contracts.py`; `test_discipline_package_registry.py`; `test_discipline_package_compatibility.py`; `test_discipline_package_conformance.py` |
| MODIFY tests / migrations | none |

Define canonical Discipline, PackageKey, SemVer, Core-contract, Registry/descriptor/profile/combination digest types with NFC canonical JSON/SHA-256 and non-interchangeable provenance types. Assemble source releases in fixed order. Strict schemas reject unknown executable fields, collisions, unsupported dependency/conflict/allow-list/taxonomy/migration/resource declarations. Evaluator returns accepted closed reason codes. Exact translator recognizes only accepted values including `control`, `industrial_automation`, `automation`, `automation_and_control`; unknown stays unresolved. `NonCommercialEntitlementAdapter` returns `NOT_REQUIRED`.

Focused tests: Registry/descriptor/selected-set/profile/combination digest golden vectors and semantic separation; duplicate/collision rejection; core version/dependency/conflict/allow-list/taxonomy/migration/resource vectors; empty release/profile cardinality; static-only adapters; historical source resolution; no runtime discovery; prohibited executable/URL/HTML/import fields; byte/count caps. Acceptance requires pure tests and no DB. Exclusions: models/UoW/projection/configuration/Audit/migration/API/frontend/operational packages/enforcement. Recovery is code-only. Independent review checks deterministic source authority and PATCH-052 firewall.

## 5. Batch 2 — Persistence, Registry projection, UoW and DB authority

**Objective:** add twelve-table persistence, derived Registry projection, installer/runtime DB authority, UoW/advisory/Audit-staging foundations and live preflight. M1/M2 are created only after future migration-creation authority and not executed.

| Action | Exact files |
|---|---|
| CREATE production | `backend/app/models/discipline_package.py`; `backend/app/schemas/discipline_package.py`; `backend/app/repositories/discipline_package_repository.py`; `backend/app/repositories/discipline_package_unit_of_work.py`; `backend/app/services/discipline_package_registry_service.py`; `backend/scripts/discipline_package_preflight.py`; `backend/scripts/discipline_package_registry.py`; `backend/migrations/versions/e05100000001_registry_configuration_audit.py`; `backend/migrations/versions/e05100000002_workspace_binding_shadow.py` |
| MODIFY production / operations | `backend/app/core/{config,database,operations}.py`; `backend/app/models/__init__.py`; `backend/app/schemas/__init__.py`; `backend/app/services/audit_service.py`; `backend/migrations/env.py`; `postgres/init/001_satco_database_roles.sh`; `ops/scripts/preflight.sh`; `docker-compose.yml`; `docker-compose.production.yml` |
| CREATE tests | `backend/tests/test_discipline_package_projection.py`; `test_discipline_package_migration.py`; `test_discipline_package_preflight.py`; `test_discipline_package_database_roles.py`; `test_discipline_package_transaction.py` |
| MODIFY tests | `backend/tests/conftest.py`; `backend/tests/test_production_topology.py`; `backend/tests/test_operations_recovery.py` |

Sequence: register all metadata; implement repositories/UoW/same-connection PostgreSQL guard; source-to-projection assembly, drift/readiness and non-HTTP installer; then M1/M2 plus test matrix. M1 (`e05100000001`, down revision `e04700000001`) creates exactly six Registry projection and six Organization/Project/Audit tables. It includes semantic profile `(profile_id, profile_digest)`, release/profile membership `(registry_digest, profile_id)`, membership `profile_digest`, exact triple `(registry_digest, profile_id, profile_digest)`, profile-member PK `(profile_id, profile_digest, combination_digest, package_key)`, accepted Project/Workspace tenant keys, immutability/deferred triggers, indexes/checks and grants. All 12 tables start empty; it creates no release or tenant configuration.

M2 (`e05100000002`) adds nullable Workspace shadows/bindings, accepted checks, NOT VALID composite binding FK, partial canonical uniqueness and lookup indexes only. It does not backfill, validate, set NOT NULL, rewrite rows, or change raw discipline constraint.

The exact principal/bootstrap owner is section 3.2: clean bootstrap extends
`postgres/init/001_satco_database_roles.sh`; established deployment bootstrap
extends `ops/scripts/preflight.sh`; Compose owns protected installer-secret
mounting and deployment-only installer job wiring. M1 keeps ownership with the
migration principal, requires both fixed roles to pre-exist, revokes
broad/PUBLIC rights, grants runtime SELECT only on six projections and installer
SELECT/INSERT plus `UPDATE(is_current)` only. No DELETE/TRUNCATE/schema/
trigger-function/historical mutation; installer gets no tenant-table privilege.
Installer validates grants, takes the exact exclusive guard and
installs/reconciles without deleting history.

**Preflight / IDS051-OBS-01:** `backend/scripts/discipline_package_preflight.py` uses explicit read-only role/URL and `REPEATABLE READ, READ ONLY, DEFERRABLE`, no DDL/DML, emitting canonical JSON/SHA-256 outside source at `artifacts/patch-051/preflight/<deployment-id>-<db-fingerprint>.json`. It records tool/commit, DB fingerprint/head/time, Workspace values/counts/nulls, exact mapping candidates/duplicates, Project/Workspace orphans, raw identity counts, checksums, constraints, affected counts, historical anchors, findings and PASS/FAIL. Unknown/null/duplicate/orphan/missing source/unsupported constraint/stale artifact/head or count drift/query failure STOPs. A Human/operator reviews matching unexpired PASS; wrapper arguments `--require-preflight <artifact> --require-digest <sha256>` are required before each migration. This plans downstream evidence without claiming live evidence now.

`backend/tests/test_discipline_package_transaction.py` owns two-independent-
PostgreSQL-Session/barrier evidence for the exact `(1396790339, 51)` key,
EXCLUSIVE installer lock, SHARED runtime lock, shared/shared coexistence,
exclusive/shared serialization, same-connection affinity, transaction-
completion release, five-second `SET LOCAL` timeout, timeout fail-closed,
fresh-retry guard reacquisition, and Batch-3 Organization/Project/rebind/
guarded-Workspace-binding mutations using SHARED. It also proves no protected
writes or success Audit survives a timeout. `backend/tests/
test_discipline_package_database_roles.py` owns role/bootstrap/grant evidence:
required-role absence makes M1 fail closed; attributes/membership/ownership/
schema-create and historical-DELETE denials; installer intended insert/current-
pointer update; runtime SELECT/mutation denial; wrong installer identity or
privilege failure; and secret non-disclosure. The projection, preflight and
migration test files own metadata/DB parity, R1/R2 semantic-profile reuse with
immutable memberships, drift/current activation/historical reconstruction,
empty tables, preflight read-only/digest/staleness/fail-closed and M1/M2
upgrade/empty-only downgrade. No SQLite substitute is accepted for lock or
role evidence. Acceptance requires all, composite tenant keys, reproducible
bootstrap/grants, exact guard and timeout behavior, installer-only
install/activation, runtime read-only projection, secret boundary and
null-shadow compatibility. Exclusions:
config/binding/cutover/API/frontend/operational packages. Empty-only downgrade
otherwise forward recovery. Review checks tables, role/bootstrap/grants,
migration predecessors, UoW/guard and preflight.

## 6. Batch 3 — Configuration, binding and guarded authorization

**Objective:** implement Organization/Project configuration, immutable revisions/effective state, Workspace binding and M3 cutover; adapt only actual Onboarding, Workspace and Audit seams required for commit-stable authority.

| Action | Exact files |
|---|---|
| CREATE production | `backend/app/services/discipline_package_service.py`; `backend/app/services/discipline_package_configuration_service.py`; `backend/migrations/versions/e05100000003_workspace_binding_cutover.py` |
| MODIFY production | `backend/app/models/{project,engineering_workspace}.py`; `backend/app/repositories/{project_repository,engineering_workspace_repository,onboarding_repository}.py`; `backend/app/services/{onboarding_service,engineering_workspace_service,audit_service}.py`; `backend/app/schemas/engineering_workspace.py` |
| CREATE tests | `backend/tests/test_discipline_package_service.py`; `test_discipline_package_audit.py` |
| MODIFY tests | `backend/tests/test_discipline_package_transaction.py`; `test_engineering_workspace_core.py`; `test_engineering_workspace_migration.py`; `test_engineering_workspace_permissions.py`; `test_discipline_package_migration.py` |

`replace_organization_configuration()` validates a bounded set, starts guarded UoW, locks guard/User/membership/Organization, requires current selected active admin, locks Organization head/selections, compares expected version, validates exact Registry standing/compatibility/resources, marks desired ENABLED and omitted enabled selections DISABLED, advances one head and stages one Audit. It does not enforce entitlement.

`replace_project_configuration()` locks Organization config for share, Project, Project head and all bound Workspaces ascending after authority prefix. Current admin or locked Project owner is required. It writes next immutable revision with 1..8 exact selections, rebinds all operational Workspaces atomically, advances head and stages Project plus at most six Workspace events. One invalid Workspace rolls all back. Removal requires zero bound Workspaces, deletes only head; rollback is a new forward revision.

Guarded `EngineeringWorkspaceService.create()` owns retry/transaction for this path and receives frozen DTO/UoW, never request permission. E/I/C requires configured executable compatible exact selection but normally remains unavailable before PATCH-052. Future disciplines become `FUTURE_UNAVAILABLE_UNBOUND`; legacy unknown read is `LEGACY_UNRESOLVED`; no new unknown/independent version. `mutate_member()` and `issue_reset()` change to User → membership → Organization; multi-admin lock set is ascending User IDs before membership. Legacy `create_audit_log()` stays out of guarded path.

M3 (`e05100000003`, from M2) is created only under future authority. In drained/read-only writer window with matching unexpired preflight, it locks scope and processes ascending ID chunks using only six mappings. Recognized rows receive canonical identity plus `FUTURE_UNAVAILABLE_UNBOUND`; no config/binding is fabricated. It verifies counts/checksums, rejects unknown/null/duplicates, validates M2 objects, makes state NOT NULL, installs deferred triggers and retains raw discipline/check. Post-use recovery is forward-only.

Use two independent PostgreSQL Sessions/barriers for User disable, membership disable/deselect, role change, stale request/auth-version, retry-after-revocation, Workspace create, Project rebind/owner-transfer and Organization config races. Every Organization replace, Project configure/remove/rebind, guarded Workspace create and PATCH-051 binding mutation proves the SHARED guard was acquired after the five-second transaction-local timeout and before authority/resource locks; it proves fresh retry reacquires both. Prove revocation-first no protected write/success Audit and mutation-first serialized commit. Fixture Organization disable covers same row. Test project/config/binding states, no latest, historical revisions, inherited/future/unresolved, exact/no fuzzy/no fabricated legacy, M3 keys/counts/triggers and workspace regressions.

Acceptance requires exact SHARED guard before authority/resource locks through final commit, timeout/fresh-retry semantics, both activation/revocation schedules, atomic Audit rollback/rebind, no stale Registry/configuration commit, no cross-tenant key, exact backfill and no fabricated operational binding. Exclude API/frontend, operational packages, enforcement, broad auth redesign and execution. Review checks exact affected functions/UoW/Audit/lock/M3 and two-session evidence.

## 7. Batch 4 — API, frontend and product integration

**Objective:** expose only accepted Registry/configuration/applicability product surfaces after Batch 3; no new package capability or operational package UX.

| Action | Exact files |
|---|---|
| CREATE production | `backend/app/dependencies/discipline_package.py`; `backend/app/api/v1/routers/discipline_packages.py`; `frontend/src/components/OrganizationPackageConfigurationPanel.tsx`; `frontend/src/components/ProjectPackageConfigurationPanel.tsx`; `frontend/src/components/EffectiveDisciplinePackagesPanel.tsx`; `frontend/src/disciplinePackages/components.tsx` |
| MODIFY production | `backend/app/main.py`; `backend/app/core/{config,operations}.py`; `backend/app/api/v1/routers/engineering_workspaces.py`; `frontend/src/api/{types,client}.ts`; `frontend/src/pages/{OrganizationAdminPage,ProjectsPage}.tsx`; `frontend/src/styles.css` |
| CREATE tests | `backend/tests/test_discipline_package_api.py`; `test_discipline_package_security.py`; `test_discipline_package_performance.py`; `frontend/src/test/discipline-packages.test.tsx` |
| MODIFY tests | `frontend/src/test/api.test.ts`; `frontend/src/test/organization-admin.test.tsx`; `frontend/src/test/workflows.test.tsx` |

Schemas are strict; dependencies compose existing auth/context/scope, never union permission. Router implements only accepted IDS routes: supported Registry discovery, effective state, Organization configuration read/replace/Audit, Project preflight/read/replace/remove and Workspace applicability/read. Writes pass identity-only DTO to guarded service. Reads preserve protected-404 ordering and bounded cursors. Startup/readiness fails closed on source/projection standing.

Typed client and panels live only in Organization Admin/Projects. A precompiled trusted component-key allow-list has no dynamic import/eval/code. UI renders server facts only: pins/preflight, Control selector reconciliation, truthful future-unavailable/legacy-unresolved/historical state, safe errors. Include semantic/keyboard/focus/live-state accessibility, responsive/RTL-ready styles. Exclude fake fallbacks, execution, approval, procurement, licensing and operational E/I/C UX.

Acceptance: all accepted routes, current authority/admin-owner policy, protected 404, bounded/safe responses, no cross-tenant discovery/inference, readiness/performance, parsing/placement/selector/unknown-key truthfulness/accessibility. Read-only adjacent Project/Context/Objects/Relationships/Evidence/Reports/Memory/Guidance/operations/workspace regressions. Recovery disables route/writes or UI while retaining history. Review checks route/UI boundary/no dynamic disclosure.

## 8. Batch 5 — Conformance, readiness and full reconciliation

**Objective:** reconcile all accepted invariants without closing PATCH-051.

Run `backend/tests/test_discipline_package_{contracts,registry,projection,compatibility,service,transaction,audit,api,security,migration,preflight,conformance,performance,database_roles}.py`, Workspace core/migration/permission regressions, and `frontend/src/test/{discipline-packages,api,organization-admin,workflows}.test.tsx`. Focused first, then smallest adjacent tests, then final full backend/frontend, typecheck, production build, static/import/diff, source/projection readiness, conformance, query plans and Alembic sole-head/exact-three-file validation.

Validate Registry/profile/projection/historical reconstruction, resource caps, tenant isolation/non-inference, authorization-before-disclosure, every revocation/retry/Audit schedule, preflight consumption, three migration upgrades, forward recovery, frontend regression and readiness. Gates: 4 MiB startup <1s, compatibility p95 <50ms, effective p95 <200ms, Audit p95 <300ms. PASS requires focused/adjacent evidence, role/security negatives, migration/cutover proof and static/type/build with no Critical/Major finding. It does not deploy, execute migration, close PATCH-051 or start PATCH-052.

## 9. Future migration choreography and boundaries

Future deployment sequence: (1) database/deployment bootstrap creates or
validates the installer principal and protected secret, then `satco_runtime`;
(2) run and Human/operator-review PASS preflight; (3) deploy compatibility
application A with routes disabled; (4) drain writers/read-only and verify;
(5) execute M1 with artifact/digest; (6) installer self-check and runtime
privilege/readiness check both pass; (7) installer takes the exclusive guard,
installs the projection and activates it; (8) execute M2; (9) revalidate
census then M3; (10) deploy compatibility application B/enables accepted APIs;
(11) validate anchors/triggers/tenant routes/performance/readiness before
writers resume. Empty M1/M2 failures may roll back; activation keeps old
current; after use recover forward. This is IDS051-OBS-01 downstream
completion, not a claim evidence exists.

No material implementation decision remains: identity, persistence, compatibility, role/lock/UoW/Audit ownership, migration sequencing, legacy behavior, API/UI and recovery are fixed. No upstream reconciliation is required.

Excluded: execution now; PATCH-052 packages; PATCH-053 cross-discipline reasoning; 054 standards intelligence; 055 Evidence Workbench; 056 Methods & Systems; 057 Product Experience expansion; 058 commercial authentication/security; 059 signed entitlements; 060 deployment qualification. The Commercial V1 roadmap remains HUMAN-FROZEN / UNCHANGED.

The exact next gate is an **Independent Implementation Readiness Review**. Only its PASS and separate Human implementation plus Batch-1 manifest authority may begin work. This plan grants no implementation, migration creation/execution, deployment or PATCH-052 authority.
