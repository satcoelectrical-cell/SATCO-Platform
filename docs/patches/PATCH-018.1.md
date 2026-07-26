# PATCH-018.1 — Project Core Enhancement

Version: 1.0
Status: Proposed — Awaiting Implementation Approval
Date: 2026-07-26

## Objective

Enhance the existing Project domain into a complete, validated core entity while preserving the current layered FastAPI architecture and existing Project APIs where practical.

PATCH-018.1 is limited to Project identity and human-facing reference, lifecycle, priority, ownership, primary assignment, dates, progress, permissions, persistence, auditing, search compatibility, and regression coverage.

## Scope

PATCH-018.1 defines and, after approval, implements:

- An expanded Project data model
- A unique human-facing Project Code
- Project lifecycle rules
- Project priority
- Project ownership
- Optional Project assignment
- Planned start and target completion dates
- Actual completion timestamp
- Progress percentage
- Project validation
- Project permissions
- Project API contracts
- Repository and service behavior
- Project audit details
- A backward-compatible database migration
- PostgreSQL regression tests

## Exclusions

PATCH-018.1 must not add:

- Milestones
- Tasks
- Activities
- Files
- Comments
- Dashboard functionality
- AI features
- Workflow engine functionality
- Notifications
- Project members or teams
- New authentication roles
- API version-prefix changes
- Soft deletion
- UUID migration

## Architecture Decision

PATCH-018.1 introduces architectural decisions for the Project data model, lifecycle, ownership, assignment, and permissions.

Before implementation is finalized, create:

```text
docs/adr/ADR-011-Project-Core-Domain.md
```

ADR-011 must include:

- Context
- Problem
- Decision
- Alternatives
- Consequences
- Related PATCH

## Project Data Model

### Existing Fields Preserved

| Field | Type | Null | Default | Notes |
|---|---|---:|---|---|
| `id` | Integer | No | Sequence | Existing primary key; UUID conversion is out of scope |
| `project_code` | String(32) | No | Server-generated | Unique, indexed, immutable human-facing reference |
| `name` | String(200) | No | None | Human-readable Project name |
| `customer_id` | Integer FK | No | None | Existing Customer relationship |
| `status` | String(32) | No | `new` | Existing lifecycle value |
| `created_at` | Timestamp | No | Current UTC time | Existing creation timestamp |

### New Fields

| Field | Type | Null | Default | Purpose |
|---|---|---:|---|---|
| `description` | Text | Yes | `NULL` | Project summary and scope |
| `priority` | String(16) | No | `medium` | Operational priority |
| `owner_id` | Integer FK to `users.id` | Yes | Acting user for new Projects | Accountable owner; nullable only for migrated legacy records |
| `primary_assignee_id` | Integer FK to `users.id` | Yes | `NULL` | Primary assigned engineer |
| `start_date` | Date | Yes | `NULL` | Planned Project start |
| `target_completion_date` | Date | Yes | `NULL` | Planned completion |
| `completed_at` | Timestamp | Yes | `NULL` | Actual lifecycle completion time |
| `progress` | Integer | No | `0` | Completion percentage from 0 through 100 |
| `updated_at` | Timestamp | No | Current UTC time | Last modification time |

## Required Fields

API creation requires:

- `name`
- `customer_id`

The service supplies:

- `project_code = SAT-PRJ-YYYY-NNNN`
- `status = new`
- `priority = medium`
- `owner_id = current_user.id`
- `progress = 0`

Optional creation fields:

- `description`
- `priority`
- `primary_assignee_id`
- `start_date`
- `target_completion_date`

Only an administrator may create a Project for another owner. Engineer-created Projects are always owned by the acting engineer.

## Status Enum

The existing values remain unchanged:

```text
new
in_progress
on_hold
completed
cancelled
```

### Lifecycle Transitions

| Current | Allowed next states |
|---|---|
| `new` | `in_progress`, `on_hold`, `cancelled` |
| `in_progress` | `on_hold`, `completed`, `cancelled` |
| `on_hold` | `in_progress`, `cancelled` |
| `completed` | None |
| `cancelled` | None |

Submitting the current status again is treated as an idempotent update.

Reopening a completed or cancelled Project is not included. A future PATCH may define an admin-only reopen operation.

## Priority Enum

```text
low
medium
high
critical
```

Default:

```text
medium
```

Priority affects ordering and reporting only. PATCH-018.1 does not add notification, escalation, or workflow behavior.

## Ownership and Primary Assignment

### Owner

- Every newly created Project has an owner.
- Engineer-created Projects are owned by the creator.
- An administrator may specify another active user as owner.
- An owner must be an active `admin` or `engineer`.
- Migrated legacy Projects may temporarily have `owner_id = NULL`.

### Primary Assignee

- `primary_assignee_id` is optional.
- A primary assignee must be an active `admin` or `engineer`.
- Project owners and administrators may assign or unassign a Project.
- Assignment represents one primary responsible user, not Project membership.

Project members, teams, and multiple assignees are out of scope. The API and relationship names are exclusively `primary_assignee_id` and `primary_assignee`.

## Project Code

`project_code` is the immutable human-facing Project reference. The existing integer `id` remains the internal primary key and existing API path identifier.

Format:

```text
SAT-PRJ-YYYY-NNNN
```

Example:

```text
SAT-PRJ-2026-0001
```

Rules:

- `SAT` is the fixed platform prefix.
- `PRJ` is the fixed Project entity prefix.
- `YYYY` is the UTC Project creation year.
- `NNNN` is a zero-padded yearly sequence beginning at `0001`.
- The sequence resets each year.
- Clients cannot submit or modify `project_code`.
- The database enforces uniqueness and provides a unique index.
- Values beyond 9999 expand naturally rather than reusing a code.

The entity prefix establishes a platform-wide identifier strategy for future references such as:

```text
SAT-CUS-2026-0001
SAT-DOC-2026-0001
SAT-TSK-2026-0001
SAT-INV-2026-0001
```

PATCH-018.1 implements only the `PRJ` Project prefix.

### Generation and Concurrency Protection

Create a PostgreSQL counter table named `project_code_sequences` with:

- `year` — Integer primary key
- `last_value` — Integer, required

Within the same database transaction as Project creation:

1. Determine the current UTC year.
2. Atomically insert the yearly row with `last_value = 1`, or increment it using `INSERT ... ON CONFLICT ... DO UPDATE`.
3. Obtain the allocated number with `RETURNING last_value`.
4. Format the Project Code as `SAT-PRJ-{year}-{last_value:04d}`.
5. Insert the Project.

PostgreSQL row-level conflict handling serializes allocations for a year. The unique database constraint on `projects.project_code` is final duplicate protection. Reading the current maximum code is prohibited.

### Legacy Backfill

The migration:

1. Adds nullable `project_code`.
2. Groups existing Projects by UTC creation year; a legacy null `created_at` uses the migration execution year.
3. Orders each year by `created_at` with nulls last, then `id`.
4. Uses a PostgreSQL window function to assign deterministic yearly sequence values.
5. Initializes each yearly counter to the greatest backfilled sequence.
6. Verifies that no null or duplicate code remains.
7. Makes `project_code` non-null and applies its unique constraint/index.

Backfill preserves integer IDs and existing relationships.

## Date Rules

- `start_date` is optional.
- `target_completion_date` is optional.
- When both exist, target completion must be on or after start date.
- `completed_at` is controlled by the service and cannot be supplied by clients.
- Moving to `completed` sets `completed_at` to the current UTC time.
- Non-completed Projects have `completed_at = NULL`.

## Progress Rules

- Progress must be an integer from 0 through 100.
- Progress is manually maintained in PATCH-018.1 under the approved permission rules.
- New Projects default to 0.
- Moving to `completed` sets progress to 100.
- A Project cannot have progress 100 unless its status is `completed`.
- A completed Project must have progress 100.
- Cancelling a Project preserves its last progress value.
- Progress changes do not automatically change status except that completion is controlled by the explicit status transition.

In a future Milestone/Task patch, progress may become system-derived from child entities. The `progress` field and its 0–100 API contract remain unchanged during that future transition. PATCH-018.1 does not implement Milestones or Tasks.

## Validation Rules

- `name` is trimmed and must contain 1–200 characters.
- `description` is optional and limited to 5,000 characters.
- Customer must exist.
- Owner and primary assignee must exist, be active, and have a supported internal role.
- `project_code` is server-generated, immutable, unique, and read-only.
- Status must be a `ProjectStatus`.
- Priority must be a `ProjectPriority`.
- Progress must be between 0 and 100.
- Target completion cannot precede start date.
- Lifecycle transition must be allowed.
- `completed_at` is server-controlled.
- Empty updates are rejected with HTTP 400.
- Invalid relationships return HTTP 404.
- Permission failures return HTTP 403.
- Validation failures return HTTP 422 or HTTP 400 according to whether they are schema-level or business-level.

## Permission Matrix

| Operation | Admin | Engineer |
|---|---:|---:|
| List Projects | Allow | Allow |
| View Project | Allow | Allow |
| Create Project | Allow | Allow |
| Choose owner during create | Allow | Own user only |
| Update descriptive fields | Allow | Owner or primary assignee |
| Change status/progress/dates/priority | Allow | Owner or primary assignee |
| Assign/unassign user | Allow | Owner |
| Transfer ownership | Allow | Deny |
| Delete Project | Allow | Deny |
| View Project audit through audit API | Allow | Deny |

### Legacy Compatibility

Existing Projects with `owner_id = NULL` remain updateable by authenticated engineers until an administrator assigns an owner. This compatibility exception prevents existing records from becoming inaccessible immediately after migration.

## API Behavior

Existing base path is preserved:

```text
/projects
```

### Endpoints

| Method | Endpoint | Behavior |
|---|---|---|
| `POST` | `/projects/` | Create Project |
| `GET` | `/projects/` | Paginated/filterable/sortable list |
| `GET` | `/projects/{project_id}` | Retrieve one Project |
| `PUT` | `/projects/{project_id}` | Partial update using existing PUT compatibility |
| `DELETE` | `/projects/{project_id}` | Admin-only deletion |

### List Query Parameters

Existing parameters remain:

- `page`
- `size`
- `customer_id`
- `status`
- `sort_by`
- `order`

New parameters:

- `priority`
- `owner_id`
- `primary_assignee_id`
- `project_code` exact or partial match
- `start_date_from`
- `start_date_to`
- `target_date_from`
- `target_date_to`

New sortable fields:

- `priority`
- `progress`
- `start_date`
- `target_completion_date`
- `updated_at`
- `project_code`

Unsupported filter, sort, status, priority, or order values return HTTP 422 rather than silently falling back.

## Search Compatibility

Authenticated Project search continues to match Project names and additionally matches `project_code`.

- Exact Project Code search is supported.
- Partial Project Code search is supported.
- Existing partial Project name search is preserved.
- The Search module is extended only where required to add the Project Code predicate.
- Search response Project references include `project_code`.

The Search module is not otherwise redesigned.

## Schemas

### ProjectCreate

Client fields:

- `name`
- `customer_id`
- `description`
- `priority`
- `owner_id`
- `primary_assignee_id`
- `start_date`
- `target_completion_date`

The service controls status, progress, completion timestamp, and default owner.

`project_code` is server-generated and is not accepted by ProjectCreate.

### ProjectUpdate

Optional fields:

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

`completed_at`, `created_at`, and `updated_at` are read-only.

`project_code` is immutable and is not accepted by ProjectUpdate.

### ProjectResponse

Includes:

- `project_code`
- All Project scalar fields
- Existing short Customer representation
- Short owner representation or `null`
- Short primary assignee representation as `primary_assignee` or `null`

Short user representation:

- `id`
- `username`
- `full_name`

## OpenAPI Examples

PATCH-018.1 adds schema and route-level OpenAPI examples without globally refactoring unrelated API documentation.

At minimum:

| Endpoint | Request | Success | Validation | 401 | 403 | 404 |
|---|---:|---:|---:|---:|---:|---:|
| `POST /projects/` | Yes | Yes | Yes | Yes | Where applicable | Related entity |
| `GET /projects/` | Query example | Yes | Yes | Yes | Where applicable | N/A |
| `GET /projects/{project_id}` | Path example | Yes | Yes | Yes | Where applicable | Yes |
| `PUT /projects/{project_id}` | Yes | Yes | Yes | Yes | Yes | Yes |
| `DELETE /projects/{project_id}` | Path example | Yes | Validation where applicable | Yes | Yes | Yes |

Examples include:

- `project_code`
- Customer
- Owner
- `primary_assignee`
- Status
- Priority
- Start and target dates
- Completion timestamp
- Progress

Request examples never accept `project_code` or `completed_at`.

## Repository Design

`ProjectRepository` remains session-bound.

Responsibilities:

- Retrieve a Project by ID.
- Build list queries.
- Apply supported filters.
- Apply allow-listed sorting.
- Apply deterministic secondary ID sorting.
- Allocate Project Codes with an atomic PostgreSQL yearly-counter upsert.
- Retrieve Projects by internal ID and exact Project Code.
- Create, update, and delete Project records.
- Eager-load Customer, owner, and primary assignee for API responses.

The repository does not:

- Decide permissions.
- Validate lifecycle transitions.
- Create audit records.
- Interpret business rules.

## Service Design

`ProjectService` owns:

- Customer validation.
- Owner/primary-assignee validation.
- Server-side Project Code allocation orchestration.
- Permission decisions.
- Lifecycle transition validation.
- Date and progress cross-field validation.
- Server-controlled defaults.
- Completion timestamp behavior.
- Audit event construction.
- Structured create/update/delete logging with `project_code`.
- Repository orchestration.

Routers remain limited to:

- Request validation.
- Authentication dependencies.
- Service invocation.
- Mapping controlled domain results to HTTP responses.

## Audit Behavior

Existing Project audit actions remain:

- `CREATE`
- `UPDATE`
- `DELETE`

Audit details include:

- Project Code
- Project name
- Customer ID
- Status
- Priority
- Owner ID
- Primary assignee ID
- Progress
- Start date
- Target completion date
- Completed timestamp

UPDATE audit details also include:

- Changed field names
- Before values for changed fields
- After values for changed fields

Sensitive user credentials are never included.

## Database Migration Strategy

Create one new Alembic revision after:

```text
d8271b8f1a29
```

Upgrade sequence:

1. Create `project_code_sequences`.
2. Add nullable `project_code`.
3. Backfill deterministic yearly Project Codes using a PostgreSQL window function.
4. Initialize yearly counters from backfilled maximum values.
5. Verify Project Code completeness and uniqueness.
6. Make `project_code` non-null and add its unique constraint/index.
7. Add nullable `description`.
8. Add `priority` with temporary server default `medium`.
9. Add nullable `owner_id`.
10. Add nullable `primary_assignee_id`.
11. Add nullable `start_date`.
12. Add nullable `target_completion_date`.
13. Add nullable `completed_at`.
14. Add `progress` with temporary server default `0`.
15. Add `updated_at` with a database current-time default.
16. Add owner and primary-assignee foreign keys to `users.id`.
17. Add indexes for status, priority, owner, primary assignee, and date filters.
18. Add a `^SAT-PRJ-[0-9]{4}-[0-9]{4,}$` Project Code format check plus status, priority, and progress constraints.
19. Validate existing status data before applying its check constraint.
20. Preserve nullable owner for existing rows.
21. Remove temporary application-independent defaults only where model defaults should control future writes.

No existing Project is deleted.

Downgrade removes only PATCH-018.1 indexes, constraints, foreign keys, columns, and `project_code_sequences`. It loses Project Codes and new metadata. Reapplying the migration may assign different legacy codes, so downgrade requires explicit destructive-action approval.

### Migration Prerequisite

The historical migration chain has known gaps, including creation migrations that contain `pass` and no committed users-table migration. PATCH-018.1 must validate the new revision against:

- The existing SATCO development schema
- A dedicated PostgreSQL test database representing the current baseline

PATCH-018.1 must not silently repair unrelated historical migrations. If the new migration cannot be safely applied because of baseline defects, implementation stops and the blocker is reported for a separately approved patch.

## Backward Compatibility

Preserved:

- Existing endpoint paths
- Existing status values
- Existing create fields
- Existing update fields
- Existing list parameters
- Existing pagination response
- Admin-only delete
- Integer Project IDs
- Existing Project name search

Additive response fields are introduced.

### Explicit Behavior Changes

- `GET /projects/{project_id}` is added.
- `project_code` becomes the immutable human-facing reference while integer IDs remain internal identifiers.
- New Projects receive owner, priority, progress, and updated timestamp defaults.
- Invalid sort/order/filter values return validation errors instead of fallback behavior.
- Status transitions become enforced.
- Engineers can update owned, assigned, or legacy unowned Projects rather than every owned Project indiscriminately.
- Empty updates return HTTP 400.
- A completed Project always has progress 100.

No URL or existing field is removed.

## Regression Test Requirements

Tests must run against the existing Docker PostgreSQL service and a dedicated PATCH-018.1 test database.

Required coverage:

- Migration upgrade on a current baseline
- Migration downgrade SQL/behavior in an isolated database
- Existing Project create/list/update/delete compatibility
- Project detail endpoint
- Default values
- Every status transition
- Invalid status transitions
- Every priority value
- Invalid priority
- Owner defaults and admin ownership override
- Owner transfer permissions
- Assignment and unassignment
- Inactive/unsupported primary-assignee rejection
- `SAT-PRJ-YYYY-NNNN` Project Code format and fixed entity prefix
- Project Code server-only behavior and immutability
- Project Code uniqueness
- Project Code yearly sequencing and reset
- Legacy Project Code backfill
- Concurrent Project creation without duplicate codes
- Date validation
- Progress boundaries and completion behavior
- Every permission-matrix operation
- Legacy unowned Project compatibility
- All list filters
- All supported sort fields and directions
- Invalid filters/sorts
- Project CREATE/UPDATE/DELETE audits
- Before/after UPDATE audit details
- Missing Project, Customer, owner, and primary-assignee behavior
- Exact and partial authenticated Project Code search
- Existing Project name search
- OpenAPI examples for all Project endpoints and error classes
- Existing Customer, Contact, authentication, search, and audit regressions

## Risks

- Historical migration gaps may prevent clean migration testing.
- New foreign keys depend on the existing users table.
- Ownership restrictions can change engineer update behavior.
- Lifecycle enforcement can reject updates previously accepted.
- Additive response relationships can cause N+1 queries without eager loading.
- Date/time consistency is currently mixed across models.
- Audit details become larger.
- Project Code allocation adds a PostgreSQL counter table and requires Project creation to share its transaction.
- Annual sequence values beyond 9999 expand beyond four digits while remaining unique.
- Downgrade discards new Project metadata.

## Rollback Plan

- Do not migrate until implementation, migration review, and isolated PostgreSQL tests pass.
- Back up the target database before an approved migration.
- Use the Alembic downgrade only after explicit approval.
- Downgrade only the PATCH-018.1 revision.
- Preserve existing Project rows and original columns.
- If application validation fails before migration, revert only PATCH-018.1 code and documentation.
- Never reset the repository or delete Docker volumes.

## Acceptance Criteria

- ADR-011 is accepted.
- New Project fields and enums match this specification.
- Existing Project endpoints remain operational.
- Project detail endpoint works.
- Lifecycle, dates, progress, ownership, assignment, and permissions are enforced.
- Migration preserves existing Project records.
- Audit records include required metadata and UPDATE diffs.
- Project Codes are unique, indexed, immutable, safely allocated under concurrency, and backfilled for legacy rows.
- Existing Project name search and new exact/partial Project Code search pass.
- OpenAPI examples cover all Project endpoints and applicable success/error responses.
- PostgreSQL automated and regression tests pass.
- Docker startup, PostgreSQL connectivity, API validation, security validation, and source compilation pass.
- Documentation and review reports are complete.
- No temporary files remain.
- `git diff --check` passes.

## Exit Criteria

PATCH-018.1 is complete only when:

- Implementation is complete.
- ADR review is complete.
- Independent Codex and ChatGPT reviews are complete.
- Migration validation passes without modifying unapproved data.
- Docker validation passes.
- Automated, regression, API, and security tests pass.
- Documentation is synchronized.
- Technical Review, Final Report, Lessons Learned, and Future Recommendations exist under `docs/reviews/`.
- No temporary files remain.
- Commit is created after explicit approval.
- Working tree is clean.

Otherwise:

```text
PATCH STATUS = INCOMPLETE
```

## Future Recommendations

- Project members and multi-user teams
- Project milestones
- Project tasks and activities
- Project files and comments
- Project dashboards
- Notifications and priority escalation
- Project workflow engine
- Soft deletion
- UUID public identifiers
- Admin-only reopen operation for terminal Projects
- Atomic business and audit transactions
- Historical Alembic baseline repair
