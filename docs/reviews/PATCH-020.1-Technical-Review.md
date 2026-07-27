# PATCH-020.1 Technical Review

## Status

Technical Validation Complete — Awaiting Final Review Approval

## Review Scope

This review covers only PATCH-020.1 Engineering Workspace Core:

- governed Discipline and Workspace Status enums;
- Workspace and collaborator persistence;
- schemas, repositories, services, routers, and exceptions;
- current-role permissions;
- lifecycle, archive, restore, and optimistic concurrency;
- centralized audit integration;
- Universal Search integration;
- Project deletion history guard;
- OpenAPI documentation;
- tests;
- Alembic revision `a20c1e0201f0`;
- approved PATCH-020.1 documentation.

Engineering Context, Engineering Execution Plan, Engineering Health, Workspace
Readiness, AI Insights, Human Review, ENSE, Engineering Decision Log,
Engineering Memory, Knowledge Graph, frontend, tasks, files, notifications,
calendar, workflow, and AI integration remain excluded.

## Governance Review

- ADR-014 status is Accepted.
- EDS-020.1 is Approved, implemented, and validated.
- The implementation follows the canonical Engineering Workspace definition.
- No Product Bible or Foundation document was modified.
- Human engineering authority is unchanged.
- No later PATCH-020 concept is represented as implemented.

## Domain Review

The implementation preserves:

- exactly six governed Disciplines;
- one permanent Workspace identity per Project and Discipline;
- a system-derived display name;
- no editable name field;
- explicit creation;
- required owner;
- optional primary assignee;
- minimal collaborator membership without member roles;
- explicit lifecycle transitions;
- archive as a lifecycle state coupled to `archived_at`;
- restore of the same identity;
- no physical Workspace deletion;
- integer optimistic concurrency.

Workspace Status remains distinct from Project Status and all future readiness,
health, and review concepts.

## Persistence Review

Alembic revision `a20c1e0201f0` is additive after `f18a1c0e2026`.

It creates:

- `engineering_workspaces`;
- `engineering_workspace_members`.

Catalog inspection confirmed:

- required and optional nullability;
- server defaults;
- named primary keys;
- permanent Project/Discipline uniqueness;
- composite membership uniqueness;
- governed Discipline and status checks;
- positive version check;
- archive/status consistency;
- restrictive foreign keys;
- authorization and lookup indexes.

No existing Project row is backfilled or mutated.

`alembic current`, `heads`, `history`, and `check` passed in the isolated
validation schema. SQLAlchemy metadata matches the database.

## Permission Review

The persisted RBAC remains `admin` and `engineer`.

- Admins may access and govern all Workspaces.
- Engineers create Workspaces only for Projects they own.
- Visibility derives from Project ownership/assignment or Workspace
  ownership/assignment/collaboration.
- Owner transfer requires admin or Project-owner authority.
- Primary assignment and collaborator management require admin, Project owner,
  or Workspace owner authority.
- Lifecycle, archive, and restore require governance authority.
- Cross-Project identifiers are hidden where disclosure would leak existence.

No expanded role system was introduced.

## Lifecycle and Concurrency Review

The accepted lifecycle is enforced in the service. Archive and restore use
explicit endpoints and require reasons. Completed Workspace reopening also
requires a reason.

Every metadata, assignment, collaborator, transition, archive, or restore
mutation uses a required positive expected version. Successful mutations
increment the integer version. Stale requests return a controlled conflict.

## Audit Review

The centralized Audit Service records:

- creation;
- metadata updates;
- owner changes;
- primary-assignee changes;
- collaborator additions and removals;
- status transitions;
- archive;
- restore.

Evidence includes actor, Workspace, Project, relevant before/after values,
reason where required, timestamp, and resulting version. Direct validation
confirms invalid assignments, stale-version conflicts, and rejected lifecycle
transitions do not emit audit evidence.

## Search Review

Universal Search remains the single search subsystem.

Workspace discovery supports:

- Discipline and derived display name;
- Project name;
- exact or partial Project Code;
- status;
- owner;
- primary assignee.

Archived Workspaces are excluded. Workspace authorization is applied before
pagination and totals. Existing Customer, Contact, Project, and Project Code
search behavior remains compatible.

## API and OpenAPI Review

The API exposes:

- create and list Project Workspaces;
- retrieve and update Workspace metadata;
- lifecycle transition;
- archive;
- restore;
- collaborator add and remove.

Every Workspace endpoint documents success and applicable `401`, `403`, `404`,
`409`, and `422` responses. The search endpoint includes a Workspace-result
example. No unavailable future capability appears in responses.

## Test Evidence

Focused PATCH-020.1 validation:

```text
54 passed
```

Complete backend PostgreSQL regression:

```text
83 passed
```

Category evidence:

- lifecycle, repository, and concurrency: 26 passed in the core module;
- permission and assignment boundaries: 17 passed;
- mutation audit and rollback: 2 passed;
- Universal Search: 2 passed;
- direct PostgreSQL migration and constraints: 7 passed.

The 47 added collected cases close every gap recorded by the prior review.
Failed mutations, concurrency conflicts, and rejected lifecycle transitions
leave audit counts unchanged. Authorization is applied before search totals and
pagination. Invalid Discipline, status, version, archive-state, Workspace
identity, and membership identity are rejected by PostgreSQL.

## Warnings

Non-blocking existing warnings remain:

- Starlette `TestClient` and HTTPX compatibility deprecation;
- Pydantic class-based configuration deprecations in existing schemas;
- existing `datetime.utcnow()` default deprecations.

## Technical Verdict

**PASS — TECHNICAL VALIDATION COMPLETE**

The implemented behavior is bounded, migration-reproducible,
permission-scoped, audit-integrated, and compatible with the current regression
suite. No production behavior change was required during final coverage.
PATCH-020.1 is ready for final review approval and remains unstaged.
