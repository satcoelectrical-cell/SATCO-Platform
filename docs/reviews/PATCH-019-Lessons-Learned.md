# PATCH-019 Lessons Learned

**Project:** SATCO Platform
**Patch:** PATCH-019 — Production Infrastructure Hardening
**Date:** 2026-07-26

## 1. Runtime Schema Creation Masks Migration Failure

`create_all()` allowed the application to run while the migration chain could
not initialize an empty database. A healthy running container is not evidence
that migration history is reproducible.

## 2. Revision Identity and Schema State Are Different

The development database was stamped at `d8271b8f1a29`, but it contained a
table intended for the next revision. Compatibility planning must inspect the
actual catalog rather than trust the revision number alone.

## 3. Historical Repair Requires Two Validation Paths

Changing no-op historical revisions repairs fresh initialization, but databases
already stamped past those revisions never replay them. Fresh and existing
baseline upgrades therefore require separate tests.

## 4. Implicit Integer Primary-Key Behavior Matters

An integer primary key implicitly acquired a PostgreSQL sequence default. The
Project Code counter year is a business key, not an generated identity, so
`autoincrement=False` must be explicit in both model and migration.

## 5. Alembic Metadata Must Import Every Model

Importing only the `app.models` package did not register its model tables.
Explicit model-module imports are required for complete foreign-key resolution
and reliable `alembic check`.

## 6. Counters Must Never Regress During Reconciliation

Backfilled Project Codes may have a lower maximum than a pre-existing valid
counter. Reconciliation must use the greatest value so future allocations
cannot reuse previously reserved numbers.

## 7. Application Import Should Be Observable as Read-Only

Comparing schema table counts before and after importing `app.main` provided
direct evidence that startup no longer emits schema DDL.

## 8. Exact Database Guards Remain Essential

Environment-driven migration configuration is safer only when mutation tests
retain an exact approved database-name guard and never fall back to the
development database.
