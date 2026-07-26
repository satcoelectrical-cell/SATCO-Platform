# PATCH-019 — Production Infrastructure Hardening

**Status:** Planning
**Date:** 2026-07-26
**Source of Truth:** `/docs`

## Purpose

PATCH-019 makes Alembic the exclusive authority for creating and evolving the
SATCO Platform PostgreSQL schema.

The patch removes runtime schema creation through
`Base.metadata.create_all()`, repairs the committed Alembic chain so a fresh
PostgreSQL database can upgrade from zero to head, and preserves compatibility
with the existing development database.

PATCH-019 is infrastructure hardening only. It does not add product features or
change approved business behavior.

## Context

The current application imports SQLAlchemy models and executes:

```python
Base.metadata.create_all(bind=engine)
```

when `app.main` is imported. The test bootstrap performs the same operation.
This makes schema ownership ambiguous and masks defects in the migration chain.

The committed migration chain is:

```text
d25733017b10
    -> c1ca2821f651
        -> 46350c98183b
            -> b969ae9217a0
                -> d8271b8f1a29
                    -> f18a1c0e2026
```

Known defects:

- `d25733017b10_create_projects_table.py` is a no-op.
- `c1ca2821f651_create_customers_table.py` is a no-op.
- `46350c98183b_create_contacts_table.py` is a no-op.
- No committed revision creates the `users` table.
- `b969ae9217a0` assumes legacy `projects`, `customers`, and
  `projects.customer` objects that the chain never creates.
- `d8271b8f1a29` does not match the live/model nullability of
  `audit_logs.user_id`.
- Application startup has created schema objects outside Alembic.
- Tests create tables from model metadata rather than proving migration
  reproducibility.

The development database is currently stamped at:

```text
d8271b8f1a29
```

It contains current foundation tables created partly outside Alembic. It also
contains a model-created `project_code_sequences` table although
`f18a1c0e2026` has not been applied. That table must be reconciled safely when
the pending Project Core migration runs.

## Objectives

1. Remove application and test dependency on `Base.metadata.create_all()`.
2. Make Alembic the single source of truth for schema creation and evolution.
3. Make `alembic upgrade head` initialize a fresh PostgreSQL database.
4. Preserve all existing development data and the current revision path.
5. Make the pending Project Core migration compatible with the existing
   development schema created under the former startup behavior.
6. Add automated PostgreSQL coverage for fresh initialization and existing
   baseline upgrade.
7. Document the operational migration-before-startup contract.

## In Scope

- Historical migration-chain repair required for reproducible initialization
- A committed users-table creation path
- Foundation migrations for Users, Customers, Contacts, legacy Projects, and
  Audit Logs
- Compatibility hardening of `f18a1c0e2026`
- Removal of `create_all()` from application startup
- Removal of `create_all()` from test bootstrap
- Alembic environment/configuration hardening needed for dedicated test
  databases and deployment
- Fresh-database migration tests
- Current-baseline-to-head migration tests
- Model-to-migration schema parity checks for current tables
- Docker/backend startup validation after explicit migration
- Documentation updates required by PATCH-019

## Out of Scope

- New business entities or API endpoints
- Project, Customer, Contact, User, or Audit feature changes
- Repository/service/router refactors unrelated to schema ownership
- UUID conversion
- Soft deletion
- API versioning
- CI/CD implementation
- Database engine changes
- SQLite or non-PostgreSQL tests
- Automatic migration execution during normal API import
- Destructive cleanup of the development database
- Rewriting Git history

## Required Architecture Decision

PATCH-019 requires a new ADR:

```text
docs/adr/ADR-012-Alembic-Schema-Ownership-and-Historical-Repair.md
```

ADR-012 must approve:

- Alembic as the exclusive schema authority.
- Explicit migration-before-application-startup deployment ordering.
- Controlled repair of historical no-op revisions.
- Compatibility rules for databases already stamped past repaired revisions.
- The prohibition on runtime `create_all()` in production and tests.
- The policy for idempotent reconciliation of objects previously created by
  `create_all()`.

ADR-012 must be approved before implementation begins.

## Schema Ownership Contract

After PATCH-019:

- Application import never creates or alters tables.
- Test import never creates or alters tables from model metadata.
- `alembic upgrade head` is the supported schema initialization command.
- Deployment applies migrations before starting the new application version.
- A missing or outdated schema is an operational deployment error, not a
  condition repaired by the API process.
- SQLAlchemy model metadata remains the ORM mapping and Alembic autogenerate
  comparison target, but it is not an execution path for schema creation.

## Migration Strategy

### 1. Preserve Revision Identity and Order

Existing revision identifiers and the linear revision graph remain unchanged.
No database is restamped to a fabricated revision, and no applied revision is
downgraded as part of normal deployment.

### 2. Repair the Fresh-Database Path

The historical no-op revisions will receive the minimum DDL required to make
their documented sequence executable:

- The root foundation revision creates the legacy schema prerequisites,
  including Users and the legacy Project table required by later revisions.
- The Customer revision creates Customers.
- The Contact revision creates Contacts with its Customer foreign key.
- The Project/Customer relationship revision migrates the legacy Project
  customer representation to `customer_id`.
- The Audit revision creates Audit Logs with the compatibility contract
  approved by ADR-012.

Repairs must reproduce the schema expected immediately before
`f18a1c0e2026`, not the final model schema. PATCH-018.1 remains responsible for
Project Core enhancement.

### 3. Preserve Already-Stamped Databases

Databases stamped at `d8271b8f1a29` have already passed the repaired
historical revisions. Alembic will not replay them. Compatibility is therefore
implemented in the first pending migration, not by forcing historical
re-execution.

Before any approved development migration:

- Verify the exact Alembic revision.
- Record table, column, constraint, index, sequence, and row-count snapshots.
- Validate all preconditions without mutation.
- Take a backup under the deployment procedure.

### 4. Reconcile `project_code_sequences`

`f18a1c0e2026` must support both approved starting states:

1. Fresh Alembic baseline where `project_code_sequences` does not exist.
2. Existing development baseline where `create_all()` already created it.

The migration must:

- Create the table when absent.
- When present, validate its columns and data before reuse.
- Reconcile model-created defaults, primary-key naming, and the required
  `last_value >= 1` constraint.
- Never drop a populated compatible table.
- Stop with a controlled error when an incompatible structure or invalid data
  is found.
- Initialize/backfill yearly counters without reducing an existing valid
  counter.

### 5. Remove Runtime Creation

Remove `Base.metadata.create_all()` and imports used only for that call from:

- `backend/app/main.py`
- `backend/tests/conftest.py`

Test setup must require a dedicated PostgreSQL database already migrated to the
expected revision.

### 6. Configuration

Alembic must receive the target PostgreSQL URL from explicit environment/test
configuration without silently defaulting mutation commands to the development
database.

The implementation must retain a hard test-database name guard and must not
introduce credentials into source beyond the existing local development
contract.

## Backward Compatibility

Preserved:

- Existing development data
- Existing table and column names
- Existing revision identifiers
- Existing API behavior
- Existing Project Core migration semantics
- Existing Docker PostgreSQL service

Intentional operational change:

- Starting the API no longer repairs or initializes schema objects.
- New and test databases must be migrated explicitly before application use.

## Risks

| Risk | Mitigation |
|---|---|
| Repaired historical revisions differ from live baseline | Compare fresh pre-`f18` schema with an approved baseline contract |
| Existing database is stamped past repaired revisions | Never replay old revisions; validate and reconcile in the pending migration |
| Pre-existing `project_code_sequences` causes duplicate-table failure | Conditional, validated reuse in `f18a1c0e2026` |
| Existing counter values are lost or reduced | Preserve populated compatible rows and use maximum-safe initialization |
| Application starts before migration | Document and validate explicit migration-before-startup ordering |
| Tests accidentally target development | Exact database-name guard and explicit URL |
| Removing `create_all()` exposes hidden migration defects | Fresh PostgreSQL upgrade and full regression tests are release gates |
| Historical downgrade becomes unsafe | Validate downgrade only in isolated disposable test databases with approval |
| Scope expands into model cleanup | Restrict changes to migration reproducibility and schema ownership |

## Rollback

Application rollback:

1. Stop the PATCH-019 application version.
2. Restore the prior application image/code.
3. Do not automatically downgrade the database.

Database rollback:

- Historical repaired revisions are not replayed on existing databases, so
  their source repair requires no production downgrade.
- Any new compatibility revision or modified pending migration must define and
  test its downgrade in an isolated database.
- A production downgrade requires separate destructive approval and a verified
  backup.
- If a migration fails, rely on PostgreSQL transactional DDL where supported,
  inspect the failed state, and stop rather than using `create_all()`.

Fresh-environment rollback:

- Discard only the dedicated disposable validation database after separate
  approval.
- Do not delete the development database or Docker volume.

## Testing Requirements

All mutation tests use dedicated PostgreSQL databases with exact-name safety
guards.

Required validation:

- Upgrade an empty PostgreSQL database from base to head.
- Verify every expected table, column, constraint, foreign key, index, and
  Alembic revision.
- Upgrade a current-baseline fixture at `d8271b8f1a29` to head.
- Validate both absent and pre-existing compatible
  `project_code_sequences` cases.
- Preserve controlled Users, Customers, Contacts, Projects, and Audit Logs.
- Verify Project Code backfill and counters.
- Confirm invalid compatibility states fail safely.
- Confirm application import creates no schema.
- Confirm test import creates no schema.
- Run the complete PostgreSQL regression suite.
- Run source compilation, Docker startup, connectivity, API, security, audit,
  and `git diff --check` validation.

## Acceptance Criteria

- Alembic alone creates a fresh current schema.
- No production or test code calls `Base.metadata.create_all()`.
- Fresh `alembic upgrade head` succeeds on PostgreSQL.
- The resulting schema matches the approved current model contract.
- Existing development-baseline fixtures upgrade without data loss.
- A pre-existing compatible `project_code_sequences` table is reconciled
  without deletion or counter regression.
- Invalid legacy states fail before destructive mutation.
- Application startup succeeds after migration and does not emit DDL.
- Application startup against an unmigrated database does not create tables.
- Complete PostgreSQL regression tests pass.
- Documentation describes the operational migration contract.
- No unrelated implementation or schema change is introduced.
- No development database mutation occurs without separate approval.
- `git diff --check` passes.

## Definition of Done

PATCH-019 is done only when:

- ADR-012 is approved.
- Historical migration repairs are reviewed.
- Fresh-database migration validation passes.
- Existing-baseline compatibility validation passes.
- `create_all()` is absent from application and test execution paths.
- Model/migration schema parity is documented and validated.
- Full PostgreSQL regression, API, security, audit, Docker, and compilation
  checks pass.
- Required technical review, final report, lessons learned, and future
  recommendations are complete.
- Roadmap and backend/database blueprints are synchronized.
- No temporary artifacts or debug code remain.
- Final repository review passes.
- Git staging and commit occur only after approval.

Otherwise:

```text
PATCH STATUS = INCOMPLETE
```

## Approval Gates

Manual approval is required before:

- Creating ADR-012
- Editing migration or source files
- Creating dedicated test databases
- Running SQL mutations or Alembic upgrades/downgrades
- Docker rebuilds
- Development database backup or migration
- Destructive cleanup
- Git staging
- Git commit
- Git push
