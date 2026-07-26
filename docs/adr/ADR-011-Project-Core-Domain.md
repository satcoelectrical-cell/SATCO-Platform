# ADR-011: Project Core Domain

## Status

Proposed — Awaiting Independent Architecture Review

## Date

2026-07-26

## Related PATCH

PATCH-018.1 — Project Core Enhancement

## Context

The current Project entity contains only an integer ID, name, Customer relationship, status, and creation timestamp. SATCO requires a stable Project core before adding future milestones, tasks, files, activities, dashboards, workflow, or AI capabilities.

Future SATCO entities will require human-readable identifiers. Project ownership, one primary assignment, lifecycle state, priority, dates, and progress also need explicit semantics.

## Problem

The existing Project domain lacks:

- A human-facing immutable reference
- Priority
- Ownership and primary assignment
- Planned and actual dates
- Progress
- Lifecycle transition rules
- Field-level authorization
- Complete audit snapshots
- Concurrency-safe identifier generation

Using the internal integer ID as the business reference would expose persistence identity and make a future cross-entity identifier convention harder to introduce.

## Decision

### Identifier

Projects receive a server-generated, immutable Project Code:

```text
SAT-PRJ-YYYY-NNNN
```

Example:

```text
SAT-PRJ-2026-0001
```

- `SAT` identifies the SATCO platform.
- `PRJ` identifies the Project entity.
- `YYYY` is the UTC creation year.
- `NNNN` is a zero-padded yearly sequence beginning at 0001.
- Integer `id` remains the internal primary key and API path identifier.
- `project_code` is required, unique, indexed, client read-only, and the human-facing reference.

Project Code allocation uses a PostgreSQL yearly counter table and atomic `INSERT ... ON CONFLICT ... DO UPDATE ... RETURNING` within the Project creation transaction. A unique database constraint provides final duplicate protection. Reading a maximum existing code is prohibited.

The prefix strategy allows future identifiers such as `SAT-CUS`, `SAT-DOC`, `SAT-TSK`, and `SAT-INV` without renaming Project references.

### Core Fields

Projects add:

- Description
- Priority
- Owner
- Primary assignee
- Start date
- Target completion date
- Actual completion timestamp
- Progress
- Updated timestamp

The relationship/API names are:

- `primary_assignee_id`
- `primary_assignee`

Multiple assignees and Project members are explicitly deferred.

### Lifecycle

Statuses remain:

- `new`
- `in_progress`
- `on_hold`
- `completed`
- `cancelled`

Allowed transitions:

- `new` → `in_progress`, `on_hold`, `cancelled`
- `in_progress` → `on_hold`, `completed`, `cancelled`
- `on_hold` → `in_progress`, `cancelled`
- `completed` and `cancelled` are terminal

### Progress

Progress remains an integer from 0 to 100 and is manually maintained in PATCH-018.1. Completed Projects are forced to 100; non-completed Projects cannot be 100.

A future Milestone/Task patch may derive progress from child entities without renaming the field or changing its 0–100 API contract.

### Permissions

- Admins can manage all Project fields and delete Projects.
- Engineers can create Projects and own their creations.
- Owners and primary assignees can update permitted Project fields.
- Owners and admins can change primary assignment.
- Only admins can transfer ownership.
- Legacy Projects without owners remain updateable by engineers until assigned.

### Auditing

CREATE and DELETE audits contain full non-sensitive Project snapshots. UPDATE audits contain changed fields and before/after values. Every snapshot includes Project Code.

## Alternatives

### Use Integer ID as Human Reference

Rejected because it exposes internal persistence identity and provides no entity-specific SATCO identifier strategy.

### Generate Code from Current Maximum

Rejected because concurrent requests can allocate the same code.

### Use UUID as Project Code

Rejected for PATCH-018.1 because the Database Blueprint still requires a future coordinated UUID strategy, and UUIDs are less usable as human references.

### Use Multiple Assignees Now

Rejected as premature scope expansion. Project membership and multiple assignments require a separate domain design.

### Derive Progress Now

Rejected because Milestones and Tasks do not exist. Manual progress preserves a stable field until child entities are approved.

## Consequences

### Positive

- Stable human-facing Project references
- Forward-compatible cross-entity prefix convention
- Concurrency-safe yearly sequence allocation
- Explicit Project accountability
- Validated lifecycle and progress
- Better filtering, auditing, search, and API documentation

### Negative

- Project creation depends on PostgreSQL-specific atomic upsert behavior.
- A yearly counter row can become a concurrency hotspot.
- Ownership rules intentionally tighten engineer update access.
- Migration backfill and downgrade require care.
- Audit payloads become larger.
- The API gains additive fields and new validation errors.

## Implementation Constraint

PATCH-018.1 must not add Milestones, Tasks, Activities, Files, Comments, Dashboard, AI, Notifications, Workflow, Project members, or multiple assignees.

