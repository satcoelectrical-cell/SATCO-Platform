# PATCH-018.1 Future Recommendations

**Project:** SATCO Platform
**Patch:** PATCH-018.1 — Project Core Enhancement
**Date:** 2026-07-26

These recommendations are outside PATCH-018.1 and require separately approved
work.

## Priority 1 — Reproducible Database Baseline

- Repair the historical Alembic chain so a new PostgreSQL database can upgrade
  from zero to head.
- Add the missing users-table migration.
- Replace no-op Customer, Contact, and Project creation revisions.
- Stop relying on application-startup `Base.metadata.create_all`.
- Add CI migration tests for both empty-database and current-baseline upgrades.

## Priority 2 — Transaction and Concurrency Integrity

- Persist each business mutation and its audit event in one transaction.
- Add optimistic concurrency/version fields for Project updates.
- Define retry behavior for serialization, deadlock, and unique-conflict
  failures.
- Add load tests for high-contention Project Code allocation.

## Priority 3 — Test Infrastructure

- Add pinned development/test dependencies.
- Run PostgreSQL regression tests in CI.
- Provision an isolated database or schema per CI job.
- Automate fixture cleanup while retaining a hard database-name safety guard.
- Treat framework deprecation warnings as tracked maintenance work.

## Priority 4 — Time and Schema Modernization

- Replace naive `datetime.utcnow()` defaults with timezone-aware UTC values.
- Migrate remaining Pydantic class-based configuration to `ConfigDict`.
- Add explicit database validation for completion timestamp invariants if that
  becomes a cross-client persistence requirement.

## Priority 5 — Project Domain Expansion

- Add soft deletion and archival.
- Add UUID public identifiers while retaining integer internal keys.
- Add Project membership and team assignment.
- Add Milestones and Tasks that derive the existing `progress` field.
- Add Activities, Files, Comments, notifications, and dashboards in separate
  patches.
- Add an approved administrative workflow for reopening terminal Projects.

## Deployment Recommendation

Before applying `f18a1c0e2026` outside the dedicated test database:

1. Back up the target PostgreSQL database.
2. Confirm it is stamped at `d8271b8f1a29`.
3. Run preflight queries for invalid/null Project statuses and names.
4. Apply the migration during an approved deployment window.
5. Verify Project counts, backfilled codes, counters, constraints, and indexes.
6. Deploy application code only with the migrated schema.
