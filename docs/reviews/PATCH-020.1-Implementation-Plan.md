# PATCH-020.1 Implementation Plan

## Status

Implemented — Additional EDS Test Coverage Required

## Purpose

This plan defines the bounded sequence for implementing the Engineering
Workspace Core described by
`docs/design/EDS-020.1-Engineering-Workspace-Core.md`.

It is a planning artifact only. It does not authorize source, migration,
database, dependency, Git, or deployment changes.

## Governing Baseline

The plan follows SATCO Foundation v1.0, accepted ADR-013, accepted ADR-014,
PATCH-020, its Architecture Review, and EDS-020.1.

The permanent boundary remains:

> SATCO does not perform engineering.
>
> SATCO helps engineers perform engineering better.

## Repository Assessment

### Repository State

- Branch: `main`
- Repository was clean before this approved documentation phase.
- Local branch was seven commits ahead of `origin/main`.
- No push is authorized.
- Current committed Alembic head is `f18a1c0e2026`.
- `docs/design/` did not previously exist.

### Existing Project Core

Project currently provides:

- integer primary key and immutable Project Code;
- required Customer;
- owner and optional primary assignee;
- governed status and priority strings;
- lifecycle validation;
- dates, completion timestamp, and progress;
- repository/service/router separation;
- audit snapshots;
- authenticated list, detail, create, update, and delete;
- exact and partial Project Code search;
- PostgreSQL constraints and regression tests.

Project physical deletion is currently available to administrators. PATCH-020.1
must add a conflict guard when any Workspace history exists while preserving
existing behavior for Projects without Workspaces.

### Existing Users and RBAC

- Persisted roles are `admin` and `engineer`.
- Public registration always assigns `engineer`.
- User activity and current internal role are validated for Project
  assignments.
- No Project membership table or generic capability framework exists.

PATCH-020.1 must not add persisted roles. Initial Workspace capabilities are
derived from current role, Project ownership/assignment, Workspace
ownership/assignment, and minimal collaborator membership.

### Existing Audit

- `AuditLog` stores actor, action, entity, entity ID, JSON details, and time.
- `create_audit_log` is the centralized write integration.
- Current repositories and audit service commit separately.
- Audit log access is administratively protected.

Workspace implementation must reuse this service and preserve action-specific
before/after evidence. Bounded transaction orchestration is required so a
successful Workspace mutation does not silently lack its required audit event.
Universal audit redesign is out of scope.

### Existing Universal Search

- Search is JWT-protected.
- Customers, Projects, and Contacts are returned in separate collections.
- Project search covers name, Project Code, and status.
- Authorization currently protects the endpoint but does not filter Project
  results by Project participation.

Workspace search must add a typed `workspaces` collection without changing
existing Project Code results. Workspace results require authorization
filtering before counts and pagination.

### Existing Persistence and Migrations

- SQLAlchemy declarative models use PostgreSQL.
- Alembic imports model modules explicitly into target metadata.
- Alembic is the exclusive schema authority.
- The repaired chain initializes a fresh PostgreSQL database from zero.
- Tests require an explicitly named dedicated PostgreSQL database at the
  expected migration head.

PATCH-020.1 requires one additive revision after `f18a1c0e2026` and no model-
driven schema creation.

### Existing Test Architecture

Tests use:

- FastAPI `TestClient`;
- a dedicated PostgreSQL database;
- outer transactions with savepoint-aware sessions;
- real authentication;
- current migration-head validation before collection;
- API, permission, audit, migration, search, and concurrency coverage.

No SQLite path is acceptable.

## Current Compatibility Boundaries

Implementation must preserve:

- Project integer route identity;
- Project Code format, allocation, immutability, and search;
- Customer, owner, and primary-assignee behavior;
- existing Project lifecycle and progress;
- existing endpoints and response shapes;
- `admin` and `engineer` persisted roles;
- authentication and token behavior;
- existing CRM and audit behavior;
- Universal Search collections and matching;
- PostgreSQL-only tests;
- Alembic-only schema creation;
- startup without `Base.metadata.create_all()`.

The single intentional existing-behavior change is:

- administrator Project deletion returns a controlled conflict if Workspace
  history exists.

## Decisions Finalized

1. Workspace is a Project child aggregate and operational boundary.
2. One immutable Workspace identity exists per Project and Discipline.
3. Initial Disciplines are governed strings enforced by Python enum, Pydantic,
   OpenAPI, and PostgreSQL check constraint.
4. Initial values are electrical, instrumentation, control, mechanical, civil,
   and process.
5. Workspace name is derived from Discipline and is not persisted or editable.
6. Status values are draft, active, on_hold, under_review, completed, and
   archived.
7. Archived is a lifecycle status; `archived_at` is its coupled timestamp.
8. Owner is required; primary assignee is optional.
9. A minimal membership table represents collaborators without member roles.
10. Workspace creation is explicit; Project creation generates nothing.
11. Archived Workspaces are restored, never replaced.
12. Physical Workspace deletion is unavailable.
13. Integer optimistic concurrency protects every mutation.
14. Current RBAC is scoped through Project and Workspace relationships.
15. Universal Search is extended, not replaced.
16. Workspace mutations reuse centralized audit.
17. One additive Alembic migration follows `f18a1c0e2026`.
18. No existing Project rows are changed or backfilled.

## Unresolved Questions

No question blocks implementation of the approved MVP contract.

The following are deliberately deferred rather than unresolved within
PATCH-020.1:

- administration or localization of Disciplines;
- additional RBAC personas;
- Workspace-specific collaborator roles;
- multiple Workspaces for one Project/Discipline;
- editable display aliases;
- archived Workspace search;
- formal retention administration;
- frontend Engineering Cockpit behavior;
- Engineering Context and all later PATCH-020 concepts.

Any attempt to include these requires separate governance and scope approval.

## Exact Files to Create

- `backend/app/enums/discipline.py`
- `backend/app/enums/workspace_status.py`
- `backend/app/models/engineering_workspace.py`
- `backend/app/schemas/engineering_workspace.py`
- `backend/app/repositories/engineering_workspace_repository.py`
- `backend/app/services/engineering_workspace_service.py`
- `backend/app/api/v1/routers/engineering_workspaces.py`
- `backend/app/exceptions/engineering_workspace.py`
- `backend/migrations/versions/a20c1e0201f0_create_engineering_workspace_core.py`
- `backend/tests/test_engineering_workspace_core.py`
- `backend/tests/test_engineering_workspace_permissions.py`
- `backend/tests/test_engineering_workspace_migration.py`
- `backend/tests/test_engineering_workspace_search.py`
- `backend/tests/test_engineering_workspace_audit.py`

The migration revision identifier must be generated by Alembic during the
separately approved implementation phase and then recorded exactly.

## Exact Files to Modify

- `backend/app/enums/__init__.py`
- `backend/app/models/__init__.py`
- `backend/app/main.py`
- `backend/app/repositories/project_repository.py`
- `backend/app/services/project_service.py`
- `backend/app/repositories/search_repository.py`
- `backend/app/services/search_service.py`
- `backend/app/api/v1/routers/search.py`
- `backend/app/schemas/search.py`
- `backend/migrations/env.py`
- `backend/tests/conftest.py`
- `backend/tests/test_projects.py`
- `backend/tests/test_search.py`

Implementation completion documentation is not pre-authorized. Exact review
documents and authoritative status updates require a later approval.

No frontend file is in scope.

## Migration Plan

### Revision

- Base the new revision on `f18a1c0e2026`.
- Maintain one linear Alembic head.
- Import the Workspace model module into Alembic target metadata.

### Upgrade

1. Create `engineering_workspaces`.
2. Add named Project and User foreign keys.
3. Add permanent Project/Discipline uniqueness.
4. Add named Discipline, status, version, and archive-state checks.
5. Add authorization and filter indexes.
6. Create `engineering_workspace_members`.
7. Add composite primary key, named foreign keys, and User indexes.

The upgrade creates no Workspace rows and modifies no Project data.

### Downgrade

1. Drop membership indexes and table.
2. Drop Workspace indexes and table.

Downgrade is destructive to PATCH-020.1 records and may run only in a dedicated
isolated validation environment after explicit approval.

## Test Plan

### Unit and Service Behavior

- creation and default state;
- Discipline and relationship validation;
- duplicate rejection;
- lifecycle matrix;
- Project-state restrictions;
- assignment and membership semantics;
- archive and restore;
- Project deletion guard;
- optimistic concurrency;
- no audit on failed mutation.

### Repository Behavior

- scoped retrieval;
- filters and deterministic pagination;
- archived visibility;
- concurrent uniqueness;
- version compare-and-update;
- membership uniqueness and history existence.

### API Behavior

- all endpoint success responses;
- JWT authentication;
- current-role authorization;
- cross-Project non-disclosure;
- request validation;
- not found and conflict behavior;
- OpenAPI schemas and examples;
- allowed actions.

### Regression

Run the complete PostgreSQL suite after targeted tests pass. Existing
authentication, CRM, Project, Project Core, Project permission, migration,
audit, and search tests must remain green.

## Database Validation Plan

Use only an explicitly approved dedicated PATCH-020.1 PostgreSQL test database
or isolated schemas inside it.

Validate:

1. full migration replay from zero to the new head;
2. upgrade from `f18a1c0e2026`;
3. Alembic `current` and `heads`;
4. preservation of all existing Project rows;
5. both new tables and every expected column;
6. primary keys, foreign keys, indexes, checks, uniqueness, defaults, and
   nullability;
7. invalid Discipline, status, version, and archive-state rejection;
8. duplicate Project/Discipline rejection under concurrency;
9. restrictive Project/User deletion;
10. safe isolated downgrade and re-upgrade if separately approved;
11. model/schema parity;
12. application startup at the migrated head.

The development database must never be used or mutated.

## API Validation Plan

Validate through authenticated targeted requests:

- create and duplicate conflict;
- list filters and archived behavior;
- visible and hidden retrieval;
- metadata and assignment update;
- each lifecycle path;
- archive and restore;
- collaborator add/remove;
- stale version conflict;
- Project deletion guard;
- validation, authentication, authorization, not-found, and conflict shapes;
- OpenAPI examples for every applicable response.

## Audit Validation Plan

For each successful mutation verify:

- expected action;
- correct actor;
- entity and Workspace ID;
- Project ID;
- relevant before/after values;
- reason where required;
- resulting version;
- timestamp.

Verify failed authorization, validation, uniqueness, state, and concurrency
operations create no audit event.

## Search Validation Plan

Validate:

- `workspace` and `all` search types;
- Discipline and derived display-name discovery;
- Project name and exact/partial Project Code discovery;
- owner and assignee discovery;
- Workspace Status discovery;
- archived exclusion;
- authentication;
- per-Workspace authorization before pagination and totals;
- preservation of Customer, Contact, Project, and Project Code behavior.

## Implementation Sequence

### Phase 1 — Approval and Baseline

1. Approve EDS-020.1 and this implementation plan.
2. Reconfirm clean repository scope and current head.
3. Reinspect the exact files immediately before editing.

### Phase 2 — Domain Contracts

4. Add Discipline and Workspace Status enums.
5. Add Workspace and membership models.
6. Add domain errors.
7. Add Pydantic request and response schemas.
8. Run source compilation and metadata inspection without schema mutation.

### Phase 3 — Persistence and Services

9. Add the Workspace repository.
10. Add Workspace lifecycle, authorization, assignment, membership,
    concurrency, and audit service behavior.
11. Add the Project Workspace-history deletion guard.
12. Run targeted non-database static validation.

### Phase 4 — HTTP and Search

13. Add Workspace router and register it.
14. Extend Universal Search.
15. Add OpenAPI examples and allowed-actions responses.
16. Validate generated OpenAPI without database mutation where possible.

### Phase 5 — Tests

17. Add core, permission, audit, search, and migration tests.
18. Update shared test migration-head guard and existing focused regressions.
19. Run test discovery and source compilation.

### Phase 6 — Migration

20. Request separate approval to create the Alembic revision.
21. Create and statically inspect the additive migration.
22. Run syntax validation and `git diff --check`.
23. Request separate approval for dedicated database creation and migration
    execution.

### Phase 7 — PostgreSQL Validation

24. Replay the fresh chain.
25. Validate current-baseline compatibility.
26. Inspect schema constraints and parity.
27. Run targeted Workspace tests.
28. Run the complete PostgreSQL regression suite.

### Phase 8 — Runtime and Review

29. Validate Docker backend startup without schema creation.
30. Run targeted API, permission, audit, search, and OpenAPI checks.
31. Run source compilation and `git diff --check`.
32. Remove only approved temporary test artifacts.
33. Request approval for completion documentation.
34. Perform final repository review.
35. Request independent approval for Git staging and commit.

## Approval Gates

Manual approval is required before:

- any implementation or test file creation/edit;
- migration creation or modification;
- SQL mutation;
- database or schema creation;
- Alembic upgrade or downgrade;
- persistent dependency change;
- Docker rebuild;
- completion-document edits;
- artifact deletion;
- staging;
- commit;
- push;
- destructive action.

Eligible read-only inspections run automatically.

## Risk Controls

| Risk | Control |
|---|---|
| Scope expansion | Exact file list and explicit later-capability exclusions |
| Cross-Project leakage | Repository filtering plus negative permission tests |
| Duplicate identity | Database unique constraint plus concurrency tests |
| History loss | No Workspace delete, restrictive FK, Project deletion guard |
| State confusion | Dedicated status enum and archive coupling constraint |
| Stale update | Required integer expected version |
| Invalid User assignments | Active internal User validation |
| Audit gaps | Mutation/audit transaction boundary and failure tests |
| Search regressions | Additive result contract and full regression suite |
| Migration incompatibility | Fresh replay and current-head upgrade paths |
| RBAC overreach | No new roles; relationship-scoped current roles |
| Premature domain growth | No Context, Plan, Health, AI, Review, or ENSE fields |

## Rollback Controls

- Before migration, revert only approved PATCH-020.1 changes.
- After additive migration, prefer application rollback while retaining tables.
- Execute downgrade only under separate approval and only where loss of
  Workspace data is explicitly acceptable.
- Never remove Workspace history merely to restore prior Project deletion.
- Do not change or replay historical migrations.

## Final Implementation Readiness Verdict

**READY FOR IMPLEMENTATION APPROVAL**

ADR-014 is Accepted, the MVP decisions are bounded, the exact implementation
surface is identified, compatibility and rollback boundaries are explicit,
and validation covers migration, authorization, audit, search, concurrency,
API, OpenAPI, Docker startup, and the complete PostgreSQL regression suite.

Implementation remains prohibited until the Product Owner explicitly approves
the implementation phase and its first mutation gate.
