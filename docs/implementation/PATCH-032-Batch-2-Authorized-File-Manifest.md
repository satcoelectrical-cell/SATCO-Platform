# PATCH-032 — Batch 2 Authorized File Manifest

## 1. Document Control

| Field | Value |
|---|---|
| Document ID | PATCH-032-B2-MANIFEST |
| Related PATCH | PATCH-032 — Technical Report |
| Batch | Batch 2 — Credential and Persistence Foundation |
| Status | AUTHORIZED / READY FOR IMPLEMENTATION |
| Human authority | GRANTED |
| Governing ADR | ADR-023 — ACCEPTED / AUTHORITATIVE |
| Governing EDS | EDS-032 — ACCEPTED / COMPLETE |
| Governing IDS | IDS-032 — ACCEPTED / COMPLETE |
| Governing plan | Implementation-Plan-032 — ACCEPTED / COMPLETE |
| Governing readiness review | IRR-032 — PASS / READY FOR IMPLEMENTATION |
| Batch 1 | ACCEPTED / COMPLETE |
| PATCH-032 overall | IN PROGRESS |
| Migration execution authority | NOT GRANTED |
| Commit / push authority | NOT GRANTED |
| Batch 3 authority | NOT GRANTED |
| Date | 2026-08-09 |

## 2. Authority Boundary

The Human authority grants preparation and implementation of Batch 2 only.
This manifest is the exact file boundary for Implementation-Plan-032 steps S06
through S08. It authorizes credential and database-role separation, the bounded
Technical Report persistence mapping and migration, database-enforced accepted-
state immutability, and focused Batch 2 evidence. It does not authorize Batch 3,
migration execution against development or deployment databases, commit, push,
deployment, or changes outside this manifest.

Batch 1 remains accepted and complete. Its domain contracts remain
authoritative. Batch 2 may add only the persistence mappings that the accepted
IDS and plan assign to the already approved Aggregate and command-support
surfaces; it shall not reopen or redesign Batch 1 semantics.

For avoidance of doubt, Batch 2 authorizes persistence-only Technical Report
outbox and idempotency infrastructure: tables, schema and SQLAlchemy mappings,
migration fields, constraints, indexes, ownership/grants, and database-level
tests. It does not authorize outbox emission, dispatch or workers,
application-layer event publishing, idempotency request orchestration or
command handling, Unit of Work coordination, service/API use, or background
processing. Those behaviors remain deferred to their separately authorized
later batches.

## 3. Verified Repository Assumptions

Repository inspection established the following facts before implementation:

- the working repository is `/Users/mac/Projects/SATCO-Platform` on branch
  `patch-022.3a-development-infrastructure`;
- the Alembic graph has exactly one head: `e02800000001`;
- the Batch 1 Technical Report Aggregate, commands, schemas, ports, exceptions,
  enums, and focused tests exist in the current working tree;
- `backend/app/core/database.py` constructs the runtime engine from
  `DATABASE_*` credentials;
- `backend/migrations/env.py` accepts `ALEMBIC_DATABASE_URL` but currently falls
  back to runtime `DATABASE_*` credentials;
- `docker-compose.yml` currently supplies the shared `satco` credential to both
  PostgreSQL administration and backend runtime;
- `backend/tests/conftest.py` currently maps the isolated test URL into both
  runtime and Alembic settings;
- no repository-managed restricted runtime-role initialization script exists;
- the authorized Batch 2 migration, role script, and two focused test files do
  not yet exist; and
- the working tree contains pre-existing changes. Implementation must preserve
  them and verify the Batch 2 diff against this manifest without absorbing
  unrelated work.

The migration parent shall be `e02800000001` only if the mandatory immediate
pre-creation verification still reports it as the sole head. Any different or
multiple head is a stop condition and requires governance reconciliation.

## 4. Exact Authorized File Boundary

### 4.1 Production Files Authorized

Exactly five production files are authorized:

| Path | State | Exact authorized purpose |
|---|---|---|
| `backend/app/models/technical_report.py` | Existing / modify | Add only the SQLAlchemy Technical Report root and provenance mappings required by IDS-032 while preserving the accepted Aggregate behavior and fields. |
| `backend/app/models/technical_report_command.py` | Existing / modify | Add only the approved durable Domain Event outbox and idempotency-result mappings; preserve the accepted command and historical-basis contracts. |
| `backend/app/models/__init__.py` | Existing / modify | Add only model-discovery imports required for Technical Report metadata registration. |
| `backend/app/core/config.py` | Existing / modify | Add only typed runtime database-role configuration and fail-closed role-separation settings required by IDS-032. |
| `backend/app/core/database.py` | Existing / modify | Construct the restricted runtime engine and enforce the approved fail-closed runtime-role and Technical Report enforcement preflight. |

No repository, Unit of Work, service, AI adapter, API router, or application
composition file is authorized in Batch 2.

### 4.2 Migration Files Authorized

Exactly two migration surfaces are authorized:

| Path | State | Exact authorized purpose |
|---|---|---|
| `backend/migrations/env.py` | Existing / modify | Require the explicit schema-owner `ALEMBIC_DATABASE_URL`, reject runtime-role use, and register only the model metadata required by the bounded migration. |
| `backend/migrations/versions/e03200000001_technical_reports.py` | New / create | One bounded revision, parented to the immediately reverified sole head, containing only approved Technical Report tables, constraints, indexes, trigger functions, triggers, grants, revokes, upgrade, and downgrade. |

No existing migration may be rewritten. No second revision is authorized.

### 4.3 Configuration and Environment Surfaces Authorized

Exactly six configuration/environment surfaces are authorized:

| Path | State | Exact authorized purpose |
|---|---|---|
| `backend/app/core/config.py` | Existing / modify | Separate and validate restricted runtime settings. |
| `backend/app/core/database.py` | Existing / modify | Apply runtime identity and privilege preflight. |
| `backend/migrations/env.py` | Existing / modify | Enforce explicit schema-owner migration identity. |
| `backend/tests/conftest.py` | Existing / modify | Provide isolated, distinct schema-owner and restricted-runtime fixtures while preserving the dedicated test-database guard and deterministic cleanup. |
| `docker-compose.yml` | Existing / modify | Wire separate runtime and migration credentials and the clean-database initialization mount without embedding deployment secrets. |
| `postgres/init/001_satco_database_roles.sh` | New / create | Provision the restricted `satco_runtime` role only for clean repository-managed local/test PostgreSQL initialization. |

The count is six exact file surfaces, five existing and one new. Configuration
authority is limited to database identity separation and Batch 2 validation; no
unrelated application, network, deployment, or secret-management change is
authorized.

### 4.4 Test Files Authorized

Exactly three test files are authorized:

| Path | State | Exact authorized purpose |
|---|---|---|
| `backend/tests/conftest.py` | Existing / modify | Isolated owner/runtime fixtures, repository-head bootstrap, cleanup, and the existing destructive-target guard. |
| `backend/tests/test_technical_report_migration.py` | New / create | Upgrade, downgrade, clean creation, parent/head, schema/model parity, constraints, indexes, triggers, and accepted-state immutability evidence. |
| `backend/tests/test_technical_report_database_roles.py` | New / create | Distinct identity, ownership, grants, forbidden privileges, bypass denial, trigger protection, and fail-closed preflight evidence. |

No Batch 1 test file is authorized for opportunistic remediation.

## 5. Existing Files Permitted to Modify

The complete existing-file modification boundary is:

1. `backend/app/models/technical_report.py`
2. `backend/app/models/technical_report_command.py`
3. `backend/app/models/__init__.py`
4. `backend/app/core/config.py`
5. `backend/app/core/database.py`
6. `backend/migrations/env.py`
7. `backend/tests/conftest.py`
8. `docker-compose.yml`

## 6. New Files Permitted to Create

The complete new-file boundary is:

1. `backend/migrations/versions/e03200000001_technical_reports.py`
2. `postgres/init/001_satco_database_roles.sh`
3. `backend/tests/test_technical_report_migration.py`
4. `backend/tests/test_technical_report_database_roles.py`

No alternate filename, additional migration, helper module, fixture module, or
generated implementation artifact is implicitly authorized.

## 7. Credential and Role Separation Boundary

The schema owner and runtime application are different PostgreSQL identities.
The schema-owner identity is supplied only through explicit
`ALEMBIC_DATABASE_URL`, owns the Technical Report tables, functions, and
triggers, and is never used by backend runtime. The runtime identity is supplied
through `DATABASE_*` and is non-owner, `NOSUPERUSER`, `NOBYPASSRLS`,
`NOCREATEDB`, and `NOCREATEROLE`; it shall not be a member of the schema-owner
role and shall have no DDL, ownership, trigger-management, privilege-escalation,
or `session_replication_role` capability.

`postgres/init/001_satco_database_roles.sh` may provision `satco_runtime` only
for a clean repository-managed local or isolated test database. Existing and
deployed environments require an owner-operated equivalent. Alembic shall not
create login secrets, assume superuser access, or fall back to runtime
credentials. Secrets remain environment/deployment owned and shall not be
committed.

Runtime startup and focused tests fail closed when the identities are equal,
the runtime identity is privileged or owns protected objects, or the required
Technical Report triggers are absent or disabled once the capability is
enabled. The current shared `satco` credential is a prerequisite defect to be
corrected, never an accepted alternative.

## 8. Technical Report Persistence Boundary

The single migration and model mappings may represent only the accepted
Technical Report root, typed provenance/reliance records, Domain Event outbox,
and idempotency result. They shall persist exactly the IDS-032-approved identity,
Organization, Workspace, optional Project, purpose, Human Owner, lifecycle,
draft revision and content, Preliminary Engineering Assessment qualification,
predecessor traceability, aggregate version, immutable accepted snapshot and
acceptance metadata, typed source locator/history/integrity information, and
timestamps.

The migration shall add only the approved foreign keys, nullability, checks,
unique constraints, indexes, UUID handling, trigger functions, triggers,
revokes, and grants. It shall not modify another canonical capability, create a
generic source repository, create a new Audit table, add publication or
supersession semantics, or introduce application-layer persistence behavior.
Existing `audit_logs` remains the Audit persistence authority; Audit integration
is not implemented until its authorized later batch.

The outbox and idempotency authorization in this section is structural only.
No application command may emit or publish an outbox event, reserve or replay
an idempotency request, coordinate either record through a Unit of Work, or
expose either capability through a service, API, worker, or background process
in Batch 2.

## 9. Accepted-State Immutability Preparation Boundary

Schema-owner-owned trigger functions and root/provenance triggers shall permit
draft creation, draft revision, and one coherent `draft → accepted` transition.
After acceptance they shall deny runtime root update/delete and provenance
insert/update/delete. Parent-row locking must make provenance enforcement safe
under concurrency. Runtime shall not execute protected functions directly,
disable or replace triggers, alter ownership, or bypass enforcement.

Accepted content, exact accepted version, acceptance identity/time/rationale,
accepted provenance and reliance, and all other acceptance-defining elements
remain immutable. Batch 2 prepares and proves this database boundary; it does
not implement acceptance orchestration, repository behavior, or a correction
workflow.

## 10. Batch 1 Dependencies and Deferred Minors

Batch 1 is `ACCEPTED / COMPLETE`. Its enums, exceptions, Aggregate, commands,
historical value contracts, schemas, ports, and focused tests satisfy the entry
dependency for S06–S08.

`B1-MIN-01` and `B1-MIN-02` remain `ACCEPTED / DEFERRED — NON-BLOCKING` and
traceable through the Batch 1 Independent Review and Human Acceptance record.
Batch 2 does not authorize changes to `backend/app/schemas/technical_report.py`
or Batch 1 test files, and it does not authorize opportunistic correction of
either finding. If a persistence mapping cannot be implemented without changing
those accepted Batch 1 contracts, work must stop for an explicit bounded
authority decision.

## 11. Ordered Batch 2 Execution

1. Reverify the exact file manifest, sole Alembic head, isolated test database,
   and credential assumptions.
2. Implement S06 role-separated local/test and runtime configuration within the
   authorized configuration surfaces.
3. Prove distinct schema-owner/runtime identities and fail-closed negative cases
   before exposing Technical Report persistence.
4. Add the approved SQLAlchemy persistence mappings without changing Aggregate
   semantics.
5. Create the one bounded S07 migration with the immediately verified head as
   parent, including the authorized persistence-only outbox and idempotency
   tables/mappings.
6. Add S08 constraints, schema-owner-owned immutability functions/triggers,
   revokes, and minimum runtime grants in that same migration.
7. Run isolated upgrade, clean creation, role/grant, immutability, model/schema
   drift, and downgrade validation. Do not execute a development, staging, or
   production migration.
8. Run Batch 1 regression, required adjacent migration/configuration regression,
   static compilation, exact-scope verification, prohibited-pattern scans, and
   `git diff --check`.
9. Stop and package evidence for an independent Batch 2 review. Do not begin
   Batch 3, commit, or push.

## 12. Batch 2 Stop Conditions

Batch 2 must stop without workaround if any of the following occurs:

- the Alembic graph does not have exactly one head immediately before revision
  creation, or that head differs from the manifest assumption;
- any required change falls outside the exact authorized file boundary;
- role separation requires weakening the restricted runtime boundary, sharing
  schema-owner credentials, committing secrets, or assuming runtime superuser;
- migration or model mapping requires a field, constraint, lifecycle,
  provenance type, authority, or semantic change not approved by IDS-032;
- accepted-state immutability cannot be enforced for both ORM and direct SQL
  writes with an independently owned trigger boundary;
- runtime can own protected objects, bypass/disable triggers, execute protected
  trigger functions, perform DDL, or elevate privileges;
- upgrade, clean creation, downgrade, grant, constraint, trigger, drift, or
  isolated role tests fail;
- Batch 1 regression fails or either deferred Minor would have to be changed;
- a repository, Unit of Work, service, API, AI, Audit integration, or other
  Batch 3-or-later behavior becomes necessary; or
- persistence-only outbox/idempotency structure cannot be kept separate from
  deferred behavioral or application integration; or
- unrelated worktree content cannot be excluded and preserved safely.

## 13. Exit and Authority State

Batch 2 is ready for implementation only within this manifest. Completion
requires all S06–S08 focused evidence, the Batch 1 regression, exact-scope and
static checks, and an independent Batch 2 review. Passing Batch 2 does not grant
Batch 3, migration execution, commit, push, or deployment authority.
