# PATCH-019 Implementation Plan

**Patch:** PATCH-019 — Production Infrastructure Hardening
**Status:** Proposed / Awaiting Approval
**Date:** 2026-07-26
**Source of Truth:** `/docs`

## 1. Executive Summary

PATCH-019 will remove runtime SQLAlchemy schema creation and establish Alembic
as the only supported schema creation/evolution mechanism.

The implementation must satisfy two different starting states:

```text
Fresh PostgreSQL database
    -> repaired historical chain
    -> f18a1c0e2026
    -> head

Existing development database at d8271b8f1a29
    -> compatibility-aware f18a1c0e2026
    -> head
```

The existing database path is complicated by a
`project_code_sequences` table created by former application startup rather
than Alembic. The migration must validate and reuse that object safely.

No implementation begins until this plan and ADR-012 are approved.

## Approval Policy

- Automatically perform eligible read-only repository, Docker, and database
  inspection where the environment supports automatic approval.
- Request manual approval only before mutating operations.
- Database mutations, Alembic execution, dependency changes, destructive
  actions, Git commits, and Git pushes always require explicit approval.

## Scope Guard

PATCH-019 is limited exclusively to Production Infrastructure Hardening:

- No new platform features.
- No domain model expansion.
- No API additions.
- No unrelated refactors.

Any discovery outside schema ownership, migration reproducibility, deployment
ordering, or directly required PostgreSQL validation must be documented for a
future patch rather than implemented here.

## 2. Governance and Architectural Constraints

PATCH-019 follows:

- `docs/00_Constitution.md`
- `docs/01_Architecture.md`
- `docs/02_Roadmap.md`
- `docs/05_Coding_Standards.md`
- `docs/06_Database_Blueprint.md`
- `docs/07_Backend_Blueprint.md`
- `docs/08_AI_Development_Workflow.md`
- `docs/09_Codex_Guidelines.md`
- `docs/patches/PATCH-019.md`

PostgreSQL remains the structured-data source of truth. Alembic becomes the
schema-definition execution authority. SQLAlchemy models remain ORM mappings
and Alembic metadata input.

## 3. Assessment Findings

### Application and Test Bootstrap

Schema DDL currently executes during import in:

- `backend/app/main.py`
- `backend/tests/conftest.py`

This behavior can:

- Hide missing migrations.
- Create partial schemas before Alembic runs.
- Change a database merely by importing the application.
- Make test results dependent on model metadata rather than migration history.

### Migration Chain

| Revision | Current behavior | Required PATCH-019 behavior |
|---|---|---|
| `d25733017b10` | No-op | Create root legacy prerequisites, including Users and legacy Projects |
| `c1ca2821f651` | No-op | Create Customers |
| `46350c98183b` | No-op | Create Contacts and Customer FK |
| `b969ae9217a0` | Assumes missing legacy tables/column | Convert legacy Project customer value to required `customer_id` |
| `d8271b8f1a29` | Creates Audit Logs with incompatible user nullability | Create the approved baseline Audit schema |
| `f18a1c0e2026` | Assumes sequence table is absent | Support absent or compatible pre-existing sequence table |

### Existing Development Database

Read-only assessment:

```text
alembic_version = d8271b8f1a29
```

Present tables:

- `users`
- `customers`
- `contacts`
- `projects`
- `audit_logs`
- `project_code_sequences`
- `alembic_version`

Important differences:

- Project Core columns are not yet applied.
- `projects.status` is still nullable.
- `audit_logs.user_id` is nullable.
- `project_code_sequences` exists before its Alembic revision.
- Its `year` column has a model-created sequence default.
- Its primary key/check naming differs from the PATCH-018.1 migration contract.

PATCH-019 planning performed no database mutation.

## 4. ADR Plan

Create:

```text
docs/adr/ADR-012-Alembic-Schema-Ownership-and-Historical-Repair.md
```

ADR sections:

- Context
- Decision
- Schema ownership
- Historical revision repair policy
- Existing-database compatibility policy
- Migration-before-startup deployment contract
- Test database policy
- Consequences
- Rejected alternatives
- Rollback and operational guidance

Rejected alternatives to document:

- Continue using `create_all()` as a fallback.
- Generate one model-derived baseline and stamp all existing databases blindly.
- Drop/recreate the development schema.
- Add a new repair revision after `f18a1c0e2026` while leaving the earlier chain
  unable to reach it.
- Introduce SQLite for migration tests.

## 5. Detailed Implementation Sequence

### Phase 1 — Approvals and Safety Baseline

1. Approve PATCH-019 and ADR-012.
2. Confirm a clean Git worktree and exact HEAD.
3. Reinspect Docker/PostgreSQL connectivity read-only.
4. Capture the development revision, schema catalog, object definitions,
   sequences, and row-count fingerprint.
5. Define exact dedicated database names for:
   - Fresh-chain validation
   - Existing-baseline compatibility validation
6. Request approval before creating either database.

No development mutation occurs in this phase.

### Phase 2 — Define the Baseline Contract

Create a reviewed table-by-table contract for the schema immediately before
`f18a1c0e2026`.

#### Users

Required baseline fields:

- `id`
- `email`
- `username`
- `hashed_password`
- `full_name`
- `role`
- `is_active`
- `created_at`

Preserve existing unique email/username indexes and model-compatible
nullability/defaults.

#### Customers

Required baseline fields:

- `id`
- `name`
- `company`
- `phone`
- `email`
- `created_at`

#### Contacts

Required baseline fields:

- `id`
- `customer_id`
- `first_name`
- `last_name`
- `position`
- `mobile`
- `phone`
- `email`
- `notes`
- `created_at`

Include the Customer foreign key and required indexes.

#### Legacy Projects

Before `b969ae9217a0`:

- `id`
- `name`
- `customer`
- `status`
- `created_at`

After `b969ae9217a0`:

- Replace `customer` with required `customer_id`.
- Preserve all Project rows.
- Fail safely when a legacy Project customer cannot be resolved.

#### Audit Logs

Required fields:

- `id`
- `user_id`
- `action`
- `entity`
- `entity_id`
- `details`
- `created_at`

ADR-012 must decide whether the reproducible baseline follows current live/model
nullable `user_id` behavior or whether a separately validated backfill is
required. The default recommendation is compatibility with the current
live/model nullable contract because tightening it would be a business/schema
change beyond infrastructure repair.

### Phase 3 — Repair Historical Revisions

Modify only the DDL needed for chain reproducibility:

1. `d25733017b10`
   - Create Users.
   - Create the legacy Projects table expected by later revisions.
   - Add matching downgrade order.
2. `c1ca2821f651`
   - Create Customers.
3. `46350c98183b`
   - Create Contacts and its Customer relationship.
4. `b969ae9217a0`
   - Validate legacy customer mappings.
   - Add/backfill/enforce `customer_id`.
   - Use explicit constraint names.
   - Provide a deterministic downgrade.
5. `d8271b8f1a29`
   - Align Audit Logs with the approved baseline contract.

Rules:

- Do not add final Project Core columns early.
- Do not make historical revisions conditionally skip missing core tables on a
  fresh database.
- Use explicit names for constraints and indexes.
- Make upgrade/downgrade ordering respect foreign keys.
- Do not run repaired historical revisions against the development database.

### Phase 4 — Harden `f18a1c0e2026`

Add a compatibility preflight for `project_code_sequences`.

Absent-table path:

- Create the table with the approved primary key and check constraint.

Present-table path:

- Verify exactly one integer `year` column and one integer `last_value` column.
- Verify `year` and `last_value` are non-null.
- Validate all existing rows.
- Remove an unintended sequence/default from `year` if present.
- Reconcile primary-key and check-constraint naming without dropping data.
- Preserve the greatest valid counter for each year.

Both paths then continue through the existing Project Code backfill.

The migration must also:

- Stop on invalid status/name values.
- Preserve Project rows.
- Avoid lowering counters.
- Remain transactional.
- Keep the approved PATCH-018.1 downgrade semantics, with explicit handling for
  whether the sequence table pre-existed.

Because downgrade ownership of a pre-existing table is ambiguous, ADR-012 must
choose one of:

- Track migration-created versus reused state using migration logic and
  preserve reused tables on downgrade.
- Define downgrade as removing the PATCH-018.1 final object regardless of
  origin, allowed only in disposable validation databases.

The recommended production policy is no automatic downgrade; restore from
backup when rollback requires schema reversal.

### Phase 5 — Remove Runtime Schema Creation

Update `backend/app/main.py`:

- Remove `Base` and `engine` imports used only by schema creation.
- Remove `Base.metadata.create_all(bind=engine)`.
- Retain model/router imports only where application registration needs them.
- Do not add automatic `alembic upgrade` on import.

Update `backend/tests/conftest.py`:

- Remove test `create_all()`.
- Preserve the exact dedicated-database name guard.
- Require the database to be migrated to the expected head before collection.
- Fail with a controlled message when schema/revision is missing.

### Phase 6 — Alembic Configuration Hardening

Review:

- `backend/alembic.ini`
- `backend/migrations/env.py`
- `backend/app/core/config.py`
- `backend/app/core/database.py`
- Docker execution commands

Implementation goals:

- Explicit target URL for every migration command.
- Environment-driven Docker/test database selection.
- No accidental fallback from a missing test URL to `satco_platform`.
- Consistent model imports for Alembic metadata.
- Optional transaction-per-migration configuration only if required and
  documented.

Do not combine general settings refactoring with this work.

### Phase 7 — Migration Test Infrastructure

Add PostgreSQL migration tests that do not import `app.main` before migration.

Required tests:

1. Empty database has no application tables.
2. Importing the application does not create tables.
3. Upgrade base to `d8271b8f1a29`.
4. Validate the pre-PATCH-018.1 baseline contract.
5. Upgrade base to head.
6. Validate final schema parity.
7. Seed controlled baseline rows and upgrade to head.
8. Verify row preservation.
9. Verify absent sequence-table path.
10. Verify compatible pre-existing sequence-table path.
11. Verify counter values never decrease.
12. Verify incompatible sequence-table structure fails safely.
13. Verify invalid legacy customer mappings fail safely.
14. Verify expected downgrades only in an isolated database after approval.

Tests must never drop a database without destructive approval.

### Phase 8 — Regression and Runtime Validation

Run:

- Complete PostgreSQL regression suite
- Authentication/RBAC tests
- Customer tests
- Contact tests
- Project Core tests
- Project permission tests
- Project migration tests
- Search tests
- Audit tests
- OpenAPI validation
- Source compilation
- `git diff --check`

Docker sequence:

1. Apply Alembic migrations to the dedicated runtime validation database.
2. Start the backend against the migrated database.
3. Verify root and OpenAPI endpoints.
4. Verify protected endpoints and database connectivity.
5. Confirm application startup emitted no schema DDL.

### Phase 9 — Existing Development Compatibility

Before any development migration, stop and request separate approval.

If approved:

1. Capture a fresh fingerprint.
2. Back up the development database.
3. Confirm revision `d8271b8f1a29`.
4. Run compatibility preflight only.
5. Review preflight results.
6. Request a separate migration approval.
7. Apply `alembic upgrade head`.
8. Verify revision, rows, Project Codes, counters, constraints, indexes, and
   API startup.

PATCH-019 planning does not authorize these actions.

### Phase 10 — Documentation and Final Review

Update after implementation:

- `docs/02_Roadmap.md`
- `docs/06_Database_Blueprint.md`
- `docs/07_Backend_Blueprint.md`
- `docs/09_Codex_Guidelines.md` only if the approved operational workflow
  requires clarification
- `docs/patches/PATCH-019.md`

Create:

- `docs/reviews/PATCH-019-Technical-Review.md`
- `docs/reviews/PATCH-019-Final-Report.md`
- `docs/reviews/PATCH-019-Lessons-Learned.md`
- `docs/reviews/PATCH-019-Future-Recommendations.md`

Then perform final repository review before requesting Git approval.

## 6. Expected Files

### Create

- `docs/adr/ADR-012-Alembic-Schema-Ownership-and-Historical-Repair.md`
- Fresh/baseline migration test modules under `backend/tests/`
- Four PATCH-019 final review documents

Exact test filenames will be finalized during approved implementation planning
before edits.

### Modify

- `backend/app/main.py`
- `backend/tests/conftest.py`
- `backend/alembic.ini` if required by the approved URL strategy
- `backend/migrations/env.py`
- `backend/migrations/versions/d25733017b10_create_projects_table.py`
- `backend/migrations/versions/c1ca2821f651_create_customers_table.py`
- `backend/migrations/versions/46350c98183b_create_contacts_table.py`
- `backend/migrations/versions/b969ae9217a0_add_project_customer_relationship_v2.py`
- `backend/migrations/versions/d8271b8f1a29_create_audit_logs_table.py`
- `backend/migrations/versions/f18a1c0e2026_enhance_project_core.py`
- Approved blueprint, roadmap, patch, and workflow documentation

No router, service, repository, schema, or business model change is planned
unless validation proves a migration/model mismatch that cannot be resolved
without one. Such a discovery requires a plan update and approval.

## 7. Rollback Plan

### Before Development Migration

- Revert only approved PATCH-019 files.
- Dedicated validation databases remain isolated.
- Do not touch development data.

### After Development Migration

- Stop the new application version.
- Restore the previous application version.
- Prefer database restore from the approved backup over an unreviewed
  downgrade.
- Run a downgrade only with separate destructive approval and only after its
  isolated validation has passed.

### Failure Policy

- Never invoke `create_all()` as recovery.
- Never stamp past a failed migration without diagnosis and approval.
- Never drop/recreate the development schema.
- Stop on schema ambiguity or unexpected live objects.

## 8. Acceptance Test Matrix

| Area | Validation | Expected result |
|---|---|---|
| Fresh DB | `alembic upgrade head` | Success |
| Fresh DB | Final revision | `f18a1c0e2026` or approved PATCH-019 head |
| Schema ownership | Import `app.main` on empty DB | No tables created |
| Historical chain | Base to `d8271b8f1a29` | Baseline schema complete |
| Existing baseline | Seeded baseline to head | Rows preserved |
| Sequence absent | Upgrade | Table created correctly |
| Sequence present | Upgrade | Compatible table reused/reconciled |
| Counter safety | Existing values | Never reduced |
| Invalid structure | Upgrade | Controlled failure, no partial mutation |
| Regression | Full PostgreSQL suite | Pass |
| Docker | Migrated startup | Pass |
| Security/audit | Existing contracts | Pass |
| Development safety | Before/after fingerprint | Unchanged unless separately approved |
| Repository | `git diff --check` | Pass |

## 9. Definition of Done

- ADR-012 approved and implemented.
- Fresh PostgreSQL initialization uses Alembic only.
- Existing-baseline upgrade path is proven.
- Runtime and test `create_all()` calls are removed.
- Migration configuration cannot silently target development during tests.
- Schema parity validation passes.
- Full regression and runtime validation passes.
- Development database remains untouched unless separately approved.
- Documentation and final reviews are complete.
- Final repository review finds no unintended files or artifacts.
- Git actions occur only after approval.

## 10. Approval Gates

Separate approval is required before:

1. Creating ADR-012.
2. Editing source or migration files.
3. Creating dedicated PostgreSQL databases.
4. Running any SQL mutation or Alembic command.
5. Testing downgrade behavior.
6. Rebuilding Docker images.
7. Backing up or migrating the development database.
8. Removing any database or volume.
9. Staging changes.
10. Committing changes.
11. Pushing changes.

## 11. Planning Exit Criteria

Planning is complete when:

- This patch definition and plan exist.
- The current chain and development compatibility state are documented.
- Required ADR work is identified.
- No implementation, migration creation, database mutation, staging, commit, or
  push has occurred.
- The repository is returned to the user for approval.
