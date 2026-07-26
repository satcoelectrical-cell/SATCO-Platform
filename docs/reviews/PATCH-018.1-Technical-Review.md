# PATCH-018.1 Technical Review

**Project:** SATCO Platform
**Patch:** PATCH-018.1 — Project Core Enhancement
**Review date:** 2026-07-26
**Source of Truth:** `/docs`
**Git commit:** Not created

## Review Outcome

**APPROVED FOR FINAL COMMIT REVIEW**

PATCH-018.1 implements the approved Project Core domain contract across the
model, schemas, repository, service, API, migration, search, permissions,
audit behavior, documentation, and PostgreSQL tests.

The review found one database-contract defect during migration validation:
`projects.status` remained nullable in the migrated schema. The migration now
sets the column to `NOT NULL`, the ORM and database check constraint explicitly
require a status, and the update schema rejects an explicit JSON `null`.

## Architecture

The implementation preserves the existing FastAPI layering:

```text
Project router
    -> Project service
        -> Project repository
            -> PostgreSQL
```

- Routers provide typed request/query validation and authenticated users.
- Lifecycle, relationship, permission, and cross-field rules remain in the
  service.
- Project persistence, filtering, eager loading, exact-code retrieval, and
  atomic yearly Project Code allocation remain in the repository.
- Integer `id` remains the internal identifier.
- `project_code` is the immutable human-facing reference.

No Milestone, Task, Activity, File, Comment, Dashboard, AI, or workflow
implementation was introduced.

## Database Review

Revision `f18a1c0e2026`, based on `d8271b8f1a29`, was replayed successfully
against an isolated current-baseline schema in
`satco_platform_patch0181_test`.

Validated behavior:

- Existing Project rows are preserved.
- Legacy Project Codes are deterministic by UTC year, creation time, and ID.
- Null legacy creation timestamps use the migration year.
- Yearly counters are initialized to each backfilled maximum.
- New codes use an atomic PostgreSQL yearly-counter upsert.
- Project Codes are non-null, unique, indexed, and format constrained.
- Status is non-null and lifecycle-value constrained.
- Priority, progress, completion/progress, and date-order checks exist.
- Customer, owner, and primary-assignee foreign keys exist.
- Approved Project filter indexes exist.

The historical migration chain still cannot build the current baseline from
an empty database because early creation revisions are no-ops and no committed
users-table migration exists. PATCH-018.1 correctly does not repair that
unrelated historical defect.

## API and Domain Review

Validated Project behavior includes:

- Create, list, detail, update, and admin-only delete
- Server-generated immutable Project Code
- Exact and partial Project Code search
- Existing Project-name search compatibility
- Typed filtering, sorting, and pagination
- Owner and primary-assignee relationships
- Owner, assignee, admin, and legacy-unowned permissions
- Approved status-transition matrix
- Completed status forcing progress 100
- Date and progress validation
- Controlled missing-resource and forbidden responses
- Project create/update/delete audit snapshots
- Project Code in audit and search representations
- OpenAPI request/response examples and server-only fields

## Security and Audit

- All Project and search operations remain authenticated.
- Engineers cannot transfer ownership or delete Projects.
- Engineers may update only owned, assigned, or legacy-unowned Projects.
- Assignment remains limited to admins and owners.
- Audit-log querying remains admin-only.
- Audit snapshots contain Project data without password/hash fields.

## Test Review

The complete PostgreSQL suite passed:

```text
29 passed, 66 warnings in 5.13s
```

The explicit Project, permission, migration, search, and audit group passed:

```text
12 passed, 47 warnings in 3.13s
```

Test isolation was strengthened so regression tests do not assume an empty
dedicated database. The concurrency test now uses committed fixtures visible
to worker connections, validates sequence values relative to the existing
yearly counter, and removes its own Project/Customer fixtures.

## Technical Debt

The following items are non-blocking and outside PATCH-018.1:

- Repair the historical Alembic baseline.
- Remove application-startup `Base.metadata.create_all`.
- Make business mutation and audit persistence one transaction.
- Replace deprecated naive `datetime.utcnow()` defaults.
- Migrate remaining Pydantic class-based configurations.
- Add pinned test dependencies and CI execution.
