# PATCH-018.1 Implementation Plan

**Patch:** PATCH-018.1 — Project Core Enhancement
**Status:** Proposed — Awaiting Implementation Approval
**Date:** 2026-07-26
**Source of Truth:** `/docs`

## Executive Summary

PATCH-018.1 enhances only the existing Project domain. It adds Project metadata, lifecycle enforcement, priority, ownership, primary assignment, dates, progress, permissions, auditing, a safe additive migration, and PostgreSQL regression coverage.

No implementation file has been modified during planning. No migration has been created or run.

## Repository Health

Phase 1 checks:

- Git working tree: clean
- Branch: `main`, one local governance commit ahead of `origin/main`
- Required documentation: available
- Required database environment configuration: present
- Backend Docker container: running
- PostgreSQL Docker container: running
- PostgreSQL connectivity: `SELECT 1` passed

## Architecture Review

Current Project flow:

```text
Project Router
    ↓
ProjectService
    ↓
ProjectRepository
    ↓
Project SQLAlchemy Model
    ↓
PostgreSQL
```

PATCH-018.1 retains this architecture.

New architectural decisions require:

```text
docs/adr/ADR-011-Project-Core-Domain.md
```

Implementation must not be finalized until ADR-011 is reviewed and accepted.

## Exact Scope

- Expand the existing Project model.
- Add a unique, immutable, server-generated Project Code.
- Preserve existing Project identity and Customer relationship.
- Define Project status lifecycle.
- Add Project priority.
- Add accountable owner.
- Add optional primary assignee.
- Add planned start and target completion dates.
- Add actual completion timestamp.
- Add progress percentage.
- Add cross-field validation.
- Add Project permission rules.
- Add single-Project retrieval.
- Extend Project filtering and sorting.
- Expand Project audit details.
- Create one additive Project migration.
- Extend PostgreSQL tests.

## Exclusions

- Milestones
- Tasks
- Activities
- Files
- Comments
- Dashboard
- AI functionality
- Workflow engine
- Notifications
- Project members
- Multiple assignees
- New roles
- Soft deletion
- UUID migration
- API version changes
- Historical migration-chain repair

## Project Data Model

| Field | Database type | Required for new records | Client writable | Default |
|---|---|---:|---:|---|
| `id` | Integer PK | Yes | No | Generated |
| `project_code` | String(32), unique/indexed | Yes | No | Server-generated `SAT-PRJ-YYYY-NNNN` |
| `name` | String(200) | Yes | Yes | None |
| `description` | Text | No | Yes | `NULL` |
| `customer_id` | Integer FK | Yes | Yes | None |
| `status` | String(32) | Yes | Update only | `new` |
| `priority` | String(16) | Yes | Yes | `medium` |
| `owner_id` | Integer FK | New records | Restricted | Acting user |
| `primary_assignee_id` | Integer FK | No | Restricted | `NULL` |
| `start_date` | Date | No | Yes | `NULL` |
| `target_completion_date` | Date | No | Yes | `NULL` |
| `completed_at` | Timestamp | No | No | `NULL` |
| `progress` | Integer | Yes | Update only | `0` |
| `created_at` | Timestamp | Yes | No | Current UTC |
| `updated_at` | Timestamp | Yes | No | Current UTC |

Legacy rows may retain `owner_id = NULL` until explicitly assigned.

## Field Definitions and Validation

### Name

- Trim whitespace.
- Minimum one character after trimming.
- Maximum 200 characters.

### Description

- Optional.
- Maximum 5,000 characters.
- Empty string is normalized to `NULL`.

### Customer

- Required.
- Must reference an existing Customer.

### Owner

- Required for new records.
- Must reference an active internal user.
- Engineer create defaults to current user.
- Admin may choose another active owner.
- Owner transfer is admin-only.

### Primary Assignee

- Optional.
- Must reference an active internal user.
- Admin or owner may assign/unassign.

### Dates

- Dates use ISO `YYYY-MM-DD` at the API boundary.
- Target completion must be on or after start date.
- Either date may be independently null.

### Progress

- Integer.
- Range 0–100.
- Defaults to 0.
- Manually maintained in PATCH-018.1 under the permission matrix.
- Completed forces 100.
- Non-completed cannot be 100.

The `progress` name and 0–100 contract are stable. A future Milestone/Task patch may derive progress from child entities without renaming the field. PATCH-018.1 does not implement Milestones or Tasks.

### Project Code

- Database type: `String(32)`.
- Required, unique, and indexed.
- Generated server-side and client read-only.
- Immutable after creation.
- Included in Project responses, list/detail views, audit snapshots, search, logs, and documentation references.
- Existing integer `id` remains the internal primary key.

Format:

```text
SAT-PRJ-YYYY-NNNN
```

Example:

```text
SAT-PRJ-2026-0001
```

`SAT` is the platform prefix and `PRJ` is the Project entity prefix. This is forward-compatible with future entity identifiers such as `SAT-CUS-...`, `SAT-DOC-...`, `SAT-TSK-...`, and `SAT-INV-...`; those identifiers are not implemented in PATCH-018.1.

Generation uses a PostgreSQL `project_code_sequences` table keyed by UTC year. Project creation atomically inserts or increments the yearly counter with `INSERT ... ON CONFLICT ... DO UPDATE ... RETURNING`. The returned value is formatted as `SAT-PRJ-{year}-{value:04d}`, and the Project insert shares the same transaction. A unique constraint on `projects.project_code` provides final duplicate protection. Reading the current maximum Project Code is prohibited.

Legacy Projects are backfilled deterministically by UTC creation year, `created_at`, and `id`. A legacy null `created_at` uses the migration execution year and sorts after dated rows. Yearly counters are initialized to each backfilled yearly maximum.

## Status Enum

Existing enum values remain:

- `new`
- `in_progress`
- `on_hold`
- `completed`
- `cancelled`

Transition matrix:

| From | To |
|---|---|
| `new` | `in_progress`, `on_hold`, `cancelled` |
| `in_progress` | `on_hold`, `completed`, `cancelled` |
| `on_hold` | `in_progress`, `cancelled` |
| `completed` | None |
| `cancelled` | None |

Same-status updates are idempotent.

## Priority Enum

Create:

```text
backend/app/enums/project_priority.py
```

Values:

- `low`
- `medium`
- `high`
- `critical`

Default:

```text
medium
```

## Relationships

```text
Customer 1 ─── * Project
User     1 ─── * Project (owner)
User     1 ─── * Project (primary assignee)
```

Relationships:

- `Project.customer`
- `Project.owner`
- `Project.primary_assignee`

The two User relationships must specify their foreign keys explicitly to avoid ambiguity.

No reverse User collection is required for PATCH-018.1.

The API and relationship names are exclusively:

- `primary_assignee_id`
- `primary_assignee`

Multiple assignees and Project members remain out of scope.

## Permission Matrix

| Action | Admin | Engineer |
|---|---:|---:|
| List | Allow | Allow |
| Get detail | Allow | Allow |
| Create | Allow | Allow |
| Set another owner at create | Allow | Deny |
| Update owned Project | Allow | Allow |
| Update assigned Project | Allow | Allow |
| Update legacy unowned Project | Allow | Allow |
| Update unrelated owned Project | Allow | Deny |
| Assign/unassign | Allow | Owner only |
| Transfer owner | Allow | Deny |
| Delete | Allow | Deny |
| Query audit log | Allow | Deny |

Authorization belongs in `ProjectService`; routers continue to provide the authenticated user.

## API Endpoints

### Existing

```text
POST   /projects/
GET    /projects/
PUT    /projects/{project_id}
DELETE /projects/{project_id}
```

### New

```text
GET /projects/{project_id}
```

### List Filters

- `customer_id`
- `status`
- `priority`
- `owner_id`
- `primary_assignee_id`
- `project_code` for exact or partial matching
- `start_date_from`
- `start_date_to`
- `target_date_from`
- `target_date_to`

### Sort Fields

- `name`
- `created_at`
- `updated_at`
- `status`
- `priority`
- `progress`
- `start_date`
- `target_completion_date`
- `project_code`

Sort order:

- `asc`
- `desc`

Invalid enum, sort, or order input returns HTTP 422.

## Schemas

### ProjectCreate

- `name`
- `customer_id`
- `description`
- `priority`
- `owner_id`
- `primary_assignee_id`
- `start_date`
- `target_completion_date`

`project_code` is not accepted by ProjectCreate.

### ProjectUpdate

- `name`
- `customer_id`
- `description`
- `status`
- `priority`
- `owner_id`
- `primary_assignee_id`
- `start_date`
- `target_completion_date`
- `progress`

`project_code` is not accepted by ProjectUpdate and cannot be changed.

### ProjectResponse

- `project_code`
- Existing scalar fields
- New scalar fields
- Short Customer
- Short owner
- Short primary assignee as `primary_assignee`

### ProjectQuery

Use typed FastAPI query parameters with enums or literals for:

- Status
- Priority
- Sort field
- Sort order

## Repository Design

Extend `ProjectRepository.get_all()` with:

- Typed filters
- Allow-listed sorting
- Date ranges
- Eager loading
- Deterministic secondary ID ordering
- Exact/partial Project Code filtering where applicable

Add a repository Project Code allocator using the atomic PostgreSQL yearly-counter upsert.

Extend `get_by_id()` to eager-load:

- Customer
- Owner
- Primary assignee

Add exact Project Code retrieval for internal and search use.

Keep create/update/delete persistence responsibilities.

Repository methods do not implement lifecycle or authorization rules.

## Service Design

Extend `ProjectService` with:

- `get_detail()`
- `_validate_user()`
- `_validate_dates()`
- `_validate_progress()`
- `_validate_transition()`
- `_can_update()`
- `_can_assign()`
- `_can_transfer_owner()`
- Server-controlled owner/default handling
- Server-controlled Project Code allocation
- Completion timestamp handling
- Audit before/after snapshot handling
- Structured Project create/update/delete logs containing `project_code`

Use explicit domain exceptions or controlled service results for:

- Project not found
- Related entity not found
- Forbidden operation
- Invalid transition
- Invalid cross-field state

No direct SQL is added to the service.

## Audit Behavior

CREATE details:

- Full non-sensitive Project snapshot including Project Code and primary assignee

UPDATE details:

- Project identity
- Changed fields
- `before` values
- `after` values

DELETE details:

- Final non-sensitive Project snapshot including Project Code and primary assignee

Serialize:

- Enums as their values
- Dates/timestamps as ISO strings

Audit actions remain `CREATE`, `UPDATE`, and `DELETE`.

Project Code is included in Project logs and every audit snapshot.

## OpenAPI Example Design

Add focused schema and route examples for:

- `POST /projects/`
- `GET /projects/`
- `GET /projects/{project_id}`
- `PUT /projects/{project_id}`
- `DELETE /projects/{project_id}`

Coverage includes request, success, validation error, unauthorized, forbidden, and not-found examples wherever applicable.

Examples include `project_code`, owner, `primary_assignee`, status, priority, dates, and progress. Request examples exclude server-controlled `project_code` and `completed_at`.

No unrelated API documentation is refactored.

Canonical create/update request example:

```json
{
  "name": "PLC Modernization",
  "description": "Replace the legacy control system.",
  "customer_id": 12,
  "priority": "high",
  "primary_assignee_id": 8,
  "start_date": "2026-08-01",
  "target_completion_date": "2026-11-30"
}
```

Canonical Project success example used by create, list, detail, and update documentation:

```json
{
  "id": 42,
  "project_code": "SAT-PRJ-2026-0001",
  "name": "PLC Modernization",
  "description": "Replace the legacy control system.",
  "customer": {"id": 12, "name": "Example Customer"},
  "status": "in_progress",
  "priority": "high",
  "owner": {"id": 3, "username": "owner", "full_name": "Project Owner"},
  "primary_assignee": {"id": 8, "username": "engineer", "full_name": "Primary Engineer"},
  "start_date": "2026-08-01",
  "target_completion_date": "2026-11-30",
  "completed_at": null,
  "progress": 35,
  "created_at": "2026-07-26T06:00:00Z",
  "updated_at": "2026-08-15T10:30:00Z"
}
```

Canonical error examples:

```json
{"detail": [{"loc": ["body", "progress"], "msg": "Input should be less than or equal to 100", "type": "less_than_equal"}]}
```

```json
{"detail": "Not authenticated"}
```

```json
{"detail": "Permission denied"}
```

```json
{"detail": "Project not found"}
```

DELETE success example:

```json
{"message": "Project deleted successfully", "project_id": 42, "project_code": "SAT-PRJ-2026-0001"}
```

## Search Compatibility

Modify only the Project predicate and Project result representation in the existing Search module:

- Preserve Project name search.
- Add exact Project Code search.
- Add partial Project Code search.
- Include `project_code` in Project search results and human-facing references.
- Preserve authentication and all Customer/Contact search behavior.

## Migration Plan

Create one Alembic revision:

```text
backend/migrations/versions/<revision>_enhance_project_core.py
```

Down revision:

```text
d8271b8f1a29
```

Upgrade:

1. Validate existing status values.
2. Create `project_code_sequences`.
3. Add nullable `project_code`.
4. Backfill deterministic yearly codes using a PostgreSQL window function.
5. Initialize yearly counters to backfilled maximum values.
6. Verify Project Code completeness and uniqueness.
7. Make Project Code non-null and add its unique constraint/index.
8. Add remaining new columns.
9. Backfill `priority = medium`.
10. Backfill `progress = 0`.
11. Backfill `updated_at` from `created_at` or current UTC.
12. Keep legacy `owner_id` null.
13. Add owner and primary-assignee foreign keys to users.
14. Add Project Code, enum, and progress check constraints.
15. Add filter indexes.
16. Preserve every existing Project row.

Downgrade:

1. Drop PATCH-018.1 indexes.
2. Drop PATCH-018.1 constraints.
3. Drop owner/primary-assignee foreign keys.
4. Drop PATCH-018.1 columns.
5. Drop `project_code_sequences`.

Migration execution requires separate manual approval.

Downgrade execution is destructive to new Project metadata and requires separate destructive-action approval.

Downgrade removes Project Codes. Reapplying the migration may generate different legacy codes, which is an explicit rollback risk.

## Backward Compatibility

Preserved:

- Existing paths
- Existing status values
- Existing basic request fields
- Existing pagination response
- Existing admin-only delete behavior
- Existing integer IDs
- Existing Project name search

Intentional changes:

- Adds detail endpoint.
- Adds immutable Project Code as the human-facing reference.
- Adds response fields.
- Enforces lifecycle transitions.
- Enforces ownership-based update permissions.
- Rejects invalid sort/order instead of fallback.
- Rejects empty updates.
- Completed status forces 100% progress.

Migration guidance:

- Apply the new Alembic revision before deploying new application code.
- Existing rows remain valid with nullable owner.
- Assign owners progressively after deployment.
- Roll back application code before an approved downgrade.

## Test Strategy

All backend tests use the existing Docker PostgreSQL service.

Use a dedicated:

```text
satco_platform_patch0181_test
```

Test safety:

- Refuse to run mutation tests against another database name.
- Never use the development database for mutations.
- Do not introduce SQLite.
- Do not drop the test database without approval.

## Test Cases

### Migration

- Upgrade from current baseline.
- Existing Project rows preserved.
- Defaults/backfills correct.
- Constraints present.
- Foreign keys present.
- Indexes present.
- Downgrade validated only in isolated test database after approval.

### Model and Schema

- `SAT-PRJ-YYYY-NNNN` Project Code format and fixed Project entity prefix.
- Project Code is server-only and immutable.
- Project Code unique constraint/index.
- Yearly sequencing and reset.
- Legacy backfill.
- Concurrent creation produces no duplicate codes.
- Required fields.
- Defaults.
- Name trimming and lengths.
- Description length.
- All enum values.
- Progress boundaries.
- Date serialization.
- Read-only completion/timestamp fields.

### Lifecycle

- Every allowed transition.
- Every prohibited transition.
- Idempotent status update.
- Completed sets progress 100 and completion timestamp.
- Cancelled preserves progress.

### Relationships

- Missing Customer.
- Missing owner.
- Missing primary assignee.
- Inactive owner/primary assignee.
- Owner default.
- Admin owner override.
- Assignment and unassignment.

### Permissions

- Every permission-matrix row for admin.
- Every permission-matrix row for engineer.
- Owned Project update.
- Assigned Project update.
- Unrelated Project denial.
- Legacy unowned Project compatibility.

### API

- Create.
- List.
- Detail.
- Update.
- Delete.
- Existing request compatibility.
- Every filter.
- Every sort field.
- Both sort directions.
- Invalid filter/sort/order.
- Pagination.
- 404/403/400/422 behavior.
- OpenAPI request, success, validation, unauthorized, forbidden, and not-found examples.

### Audit

- CREATE snapshot.
- UPDATE changed fields.
- UPDATE before/after values.
- DELETE snapshot.
- Acting user and Project ID.
- No password/hash leakage.

### Regression

- Authentication.
- RBAC.
- Customers.
- Contacts.
- Search.
- Exact Project Code search.
- Partial Project Code search.
- Existing Project name search.
- Audit-log API.
- Existing PATCH-017.3 Project tests.

## Exact Files to Create

### Architecture and Patch Documentation

- `docs/adr/ADR-011-Project-Core-Domain.md`
- `docs/reviews/PATCH-018.1-Technical-Review.md`
- `docs/reviews/PATCH-018.1-Final-Report.md`
- `docs/reviews/PATCH-018.1-Lessons-Learned.md`
- `docs/reviews/PATCH-018.1-Future-Recommendations.md`

### Backend

- `backend/app/enums/project_priority.py`
- `backend/migrations/versions/<revision>_enhance_project_core.py`
- `backend/tests/test_project_core.py`
- `backend/tests/test_project_permissions.py`
- `backend/tests/test_project_migration.py`

The Alembic revision identifier will be generated during implementation after approval.

## Exact Files to Modify

### Documentation

- `docs/patches/PATCH-018.1.md`
- `docs/reviews/PATCH-018.1-Implementation-Plan.md`
- `docs/02_Roadmap.md`
- `docs/06_Database_Blueprint.md`
- `docs/07_Backend_Blueprint.md`

### Backend

- `backend/app/enums/__init__.py`
- `backend/app/models/project.py`
- `backend/app/schemas/project.py`
- `backend/app/repositories/project_repository.py`
- `backend/app/services/project_service.py`
- `backend/app/api/v1/routers/projects.py`
- `backend/app/exceptions/project.py`
- `backend/app/repositories/search_repository.py`
- `backend/app/schemas/search.py`
- `backend/tests/conftest.py`
- `backend/tests/test_projects.py`
- `backend/tests/test_search.py`

No Customer, Contact, AI, workflow, milestone, task, activity, file, comment, or dashboard implementation file is in scope.

## Implementation Sequence

1. Create and approve ADR-011.
2. Update Project documentation before code.
3. Add priority enum and schemas.
4. Add model fields and relationships.
5. Create migration without running it.
6. Extend repository queries.
7. Extend service validation and permissions.
8. Extend router API.
9. Add PostgreSQL tests.
10. Request migration/test database approvals.
11. Validate migration in isolated PostgreSQL.
12. Run complete Docker regression suite.
13. Run API and security validation.
14. Produce required reviews.
15. Complete independent AI reviews.
16. Request Git staging and commit approval.

## Risks

| Risk | Mitigation |
|---|---|
| Historical migration gaps | Validate current baseline first; stop rather than repair out of scope |
| User FK unavailable in clean chain | Validate live/current baseline; document blocker |
| Ownership breaks engineer access | Legacy-null compatibility; explicit permission tests |
| Invalid existing status | Preflight query before constraint |
| N+1 response queries | Eager-load three relationships |
| Date/time inconsistency | Use UTC timestamps and ISO API serialization |
| Audit payload growth | Record only Project fields and changed values |
| Project Code allocation contention | Atomic yearly-row upsert; one transaction; unique constraint |
| Legacy Project Code backfill | Deterministic year/creation/ID ordering and pre-constraint validation |
| Sequence exceeds 9999 | Permit additional digits while retaining `SAT-PRJ-YYYY-` and uniqueness |
| Downgrade data loss | Require explicit destructive approval |
| Scope expansion | Record discoveries under Future Recommendations |

## Rollback Plan

- No migration before all code and migration tests pass.
- Take a database backup before approved deployment migration.
- Roll back application deployment before database downgrade.
- Downgrade only the PATCH-018.1 revision.
- Require manual approval before downgrade.
- Preserve existing Project rows and original fields.
- Do not delete test/development databases or Docker volumes.
- Revert only PATCH-018.1 files if implementation fails before migration.
- Do not rewrite Git history.

## Acceptance Criteria

- Scope and exclusions remain intact.
- ADR-011 is accepted.
- Model, enums, schemas, repository, service, router, migration, audit, and tests match the patch definition.
- Existing APIs remain compatible except documented changes.
- Existing Project records survive migration.
- Permission matrix is enforced.
- Lifecycle and cross-field validation are enforced.
- `primary_assignee_id` and `primary_assignee` naming is used consistently.
- Project Codes are unique, indexed, immutable, concurrency-safe, and backfilled.
- Project Code exact/partial search and existing Project name search pass.
- OpenAPI examples cover all Project endpoints and applicable error cases.
- PostgreSQL migration and regression tests pass.
- Docker, API, security, and source validation pass.
- Documentation is synchronized.
- All review documents exist.
- No temporary/debug files remain.
- `git diff --check` passes.

## Exit Criteria

PATCH-018.1 is complete only if:

- Implementation completed.
- Docker validation passed.
- Automated tests passed.
- Regression tests passed.
- API validation passed.
- Security validation completed.
- Migration validation passed.
- Documentation updated.
- Review documents generated.
- Codex and ChatGPT reviews completed.
- No temporary files remain.
- `git diff --check` passes.
- Commit created after approval.
- Working tree clean.

Otherwise:

```text
PATCH STATUS = INCOMPLETE
```

## Future Recommendations

- Repair the historical Alembic baseline in a separate patch.
- Add atomic Project mutation and audit transactions.
- Add soft deletion.
- Add UUID public identifiers.
- Add Project membership and teams.
- Add admin-only terminal-state reopening.
- Add milestone, task, activity, file, comment, and dashboard features only in separately approved patches.
- Add notifications and priority escalation.
- Add workflow automation.
- Add optimistic concurrency/version fields.
- Add Project archival independently from deletion.

## Approval Gates

Manual approval is required before:

- Editing or creating implementation files
- Creating ADR-011 and implementation review documents
- Creating the migration file
- Creating the PostgreSQL test database
- Running any SQL mutation or migration
- Persistent dependency changes
- Docker rebuilds affecting development
- Deleting files or data
- Git add
- Git commit
- Git push

PATCH-018.1 implementation must not begin until this plan receives explicit approval.
