# ADR-012: Alembic Schema Ownership and Historical Repair

## Status

Accepted

## Date

2026-07-26

## Related PATCH

PATCH-019 — Production Infrastructure Hardening

## Context

SATCO Platform currently has two competing schema creation mechanisms:

- Alembic migration revisions
- SQLAlchemy `Base.metadata.create_all()` during application and test import

The runtime `create_all()` path has masked gaps in the committed Alembic
history. Three foundational revisions are no-ops, no committed revision creates
the Users table, and later revisions assume tables and legacy columns that the
chain does not create.

The existing development database is stamped at `d8271b8f1a29`, but its schema
was partly created outside Alembic. In particular,
`project_code_sequences` exists even though the pending
`f18a1c0e2026` migration is intended to create it.

PATCH-019 must make a fresh database reproducible while preserving compatibility
with databases already stamped past the defective historical revisions.

## Problem

The current system cannot guarantee:

- That `alembic upgrade head` succeeds on an empty PostgreSQL database
- That an Alembic revision accurately represents the database schema
- That importing the API is read-only with respect to schema
- That tests validate migration history rather than model-generated tables
- That the pending Project Core migration can run against the existing
  development database

Blindly replacing the history with a new baseline or restamping the development
database would risk losing the relationship between existing data and recorded
revision state.

## Decision

### Alembic Is the Exclusive Schema Authority

Alembic is the only supported mechanism for creating, altering, or removing
application schema objects.

After PATCH-019:

- Application import does not execute schema DDL.
- Test import does not execute schema DDL from ORM metadata.
- SQLAlchemy metadata remains the ORM mapping and Alembic comparison target.
- Deployments migrate the database before starting the corresponding
  application version.
- The API process does not automatically run Alembic.
- Missing or outdated schema is an operational deployment failure.

### Controlled Historical Revision Repair

The existing revision identifiers and linear dependency graph are retained.
The historical no-op revisions are repaired in place with the minimum DDL
needed to reproduce the schema contract implied by their names and downstream
revisions.

This is an explicit exception to the normal rule that applied migration files
are immutable. It is permitted because:

- The current chain is not executable from a fresh database.
- Alembic records revision identifiers, not file checksums.
- Existing databases stamped past these revisions will not replay them.
- Fresh databases require the repaired source to reach the current head.
- A separate compatibility path will validate already-stamped databases.

Historical repairs must not introduce current/future domain fields early.
They reproduce the legacy schema at each revision boundary.

### Users Table Placement

The root foundation revision `d25733017b10` creates the Users table in addition
to the legacy Projects table.

This placement is chosen because:

- There is no existing users-table revision to repair.
- The Users table must exist before the PATCH-018.1 owner/assignee foreign keys.
- Adding a new revision after `f18a1c0e2026` would be too late.
- Inserting a new revision identifier into the historical graph would require
  rewriting downstream `down_revision` references and create a second history
  interpretation for already-stamped databases.

The root revision remains a foundation boundary even though its historical
filename mentions Projects.

### Existing-Database Compatibility

Historical revisions are never forced to replay on a database already stamped
past them.

Compatibility is handled at the first pending revision:

- Validate the recorded starting revision.
- Inspect legacy objects before mutation.
- Reconcile only known objects created by the former `create_all()` behavior.
- Preserve rows and valid sequence/counter values.
- Stop with a controlled error on unknown or incompatible structures.

No deployment may use `alembic stamp` to skip failed work without separate
architecture and database approval.

### `project_code_sequences` Reconciliation

Revision `f18a1c0e2026` supports two starting states:

1. Table absent: create the approved table.
2. Compatible table present: validate and normalize it without dropping data.

For a compatible pre-existing table, the migration:

- Requires integer `year` and `last_value` columns.
- Requires non-null values and unique years.
- Rejects `last_value < 1`.
- Removes the unintended auto-increment default from `year`.
- Ensures the approved primary key and check constraint.
- Initializes counters using the greatest existing valid value and backfilled
  Project value for each year.

An incompatible object causes the migration to fail before Project mutation.

### Downgrade Ownership

Production rollback uses application rollback plus database restore from an
approved backup when schema reversal is required.

Alembic downgrade remains a validation tool for isolated disposable databases
and requires destructive approval.

For `f18a1c0e2026`, downgrade removes the final
`project_code_sequences` object as defined by PATCH-018.1, regardless of whether
the upgrade created or reconciled it. This matches the existing PATCH-018.1
downgrade contract and is not authorized for routine production rollback.

### Test Database Policy

Migration and regression tests use PostgreSQL only.

- Each mutation suite requires an explicitly named dedicated database.
- Tests fail before import when the configured database name is not approved.
- Tests do not fall back to `satco_platform`.
- Fresh-chain tests start from an empty dedicated database.
- Compatibility tests use a separately controlled baseline fixture.
- Database deletion requires separate destructive approval.

## Deployment Contract

The supported release order is:

```text
backup and preflight
    -> alembic upgrade head
        -> schema verification
            -> start new backend version
                -> API health validation
```

The backend must not be used as a migration runner. Docker Compose or deployment
automation may invoke an explicit migration command, but normal API startup
does not.

## Alternatives

### Keep `create_all()` as a Fallback

Rejected because it hides migration defects and makes schema state dependent on
application import order.

### Add Only a New Repair Revision After Current Head

Rejected because the broken fresh chain cannot reach that revision, and the
pending `f18a1c0e2026` migration already fails when its expected prerequisites
are absent or its sequence table already exists.

### Replace History With One New Baseline

Rejected because blindly stamping existing databases would sever the auditable
revision path and could accept incompatible schemas.

### Insert a New Users Revision Into Historical Order

Rejected because it would change downstream graph references and create an
ambiguous history for already-stamped databases.

### Drop and Recreate the Development Database

Rejected because development data must be preserved and destructive replacement
is not necessary.

### Use SQLite for Migration Tests

Rejected because PATCH-019 depends on PostgreSQL DDL, catalogs, transactional
behavior, constraints, and Project Code upserts.

### Run Alembic Automatically on API Startup

Rejected because multiple application replicas could race, startup would gain
schema mutation authority, and deployment failures would become less explicit.

## Consequences

### Positive

- Fresh PostgreSQL databases become reproducible.
- Schema changes have one auditable execution authority.
- Application and test imports become schema read-only.
- Migration gaps can no longer be masked by model metadata.
- Existing development data and revision identity are preserved.
- Deployment ordering becomes explicit.

### Negative

- Historical migration sources are intentionally changed after some databases
  have recorded those revision identifiers.
- Fresh and already-stamped paths require separate validation.
- Deployments must include an explicit migration step.
- Application startup will no longer self-heal a missing schema.
- The pending Project migration gains compatibility complexity.

## Implementation Constraints

PATCH-019 must not:

- Add platform features.
- Expand domain models.
- Add APIs.
- Change business permissions or lifecycle behavior.
- Drop or recreate the development database.
- Replay repaired historical revisions against already-stamped databases.
- Use `create_all()` as migration or test setup.
- Run database mutations without explicit approval.

## Validation Requirements

- Fresh database upgrades from base to head.
- Repaired intermediate baseline matches its documented contract.
- Existing-baseline fixtures upgrade to head without row loss.
- Both absent and compatible pre-existing sequence-table paths pass.
- Invalid compatibility states fail transactionally.
- Application import on an empty schema creates no tables.
- Complete PostgreSQL regression suite passes.
- Development database remains unchanged unless separately approved.
