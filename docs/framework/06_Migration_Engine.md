# SATCO Implementation Framework v1.1 — Migration Engine

## 1. Purpose

The Migration Engine governs every database schema change under ADR-012 and the
SATCO Development Lifecycle.

## 2. Authority

Alembic is the exclusive schema authority. SQLAlchemy metadata is the mapping
and comparison target, not a schema bootstrap mechanism. Application startup
and test import shall not call `create_all()` to mask migration gaps.

## 3. Migration Readiness

A migration may be implemented only when the approved PATCH/EDS/IDS defines:

- exact parent revision and single-head expectation;
- exact tables, columns, types, defaults, nullability, indexes, checks,
  uniqueness, and foreign keys;
- enum storage strategy;
- existing-data/backfill behavior;
- upgrade and downgrade ownership;
- compatibility and rollback strategy;
- exact model and migration file set;
- isolated validation database requirements.

Missing data semantics or constraints are blockers.

## 4. Revision Rules

- Use one new additive revision unless the IDS explicitly requires otherwise.
- `down_revision` equals the approved current head at readiness.
- Never create a second head accidentally.
- Never rewrite applied history, stamp over failure, or renumber a revision
  except through explicit ADR-controlled authority.
- Preserve UUID/integer identity and existing data exactly as governed.
- Do not add fields, constraints, indexes, or tables “for future use.”

## 5. Upgrade Rules

`upgrade()` creates or changes only approved objects. Use explicit names and
PostgreSQL-compatible behavior. Foreign-key deletion behavior, server defaults,
partial indexes, checks, and enum values must match the current approved ORM
model and IDS.

Runtime services shall not execute migrations automatically.

## 6. Downgrade and Rollback

Downgrade is validated in an isolated disposable database and reverses only
objects owned by that revision. It must not modify unrelated tables or erase
pre-PATCH data.

Production rollback follows approved backup/restore or a data-preserving
forward repair. Destructive downgrade after authoritative data exists requires
separate explicit approval.

## 7. Mandatory Validation Sequence

1. Confirm one current head and intended parent.
2. Compile/import migration and registered model metadata.
3. Upgrade an approved existing baseline to the new revision.
4. Inspect exact tables, columns, constraints, indexes, and foreign keys.
5. Run Alembic model/schema drift detection.
6. Downgrade to the parent in the isolated database.
7. Verify only revision-owned objects were removed.
8. Re-upgrade to the new head.
9. Create a genuinely empty dedicated PostgreSQL database.
10. Run `alembic upgrade head` through the complete history.
11. Verify the recorded head and schema.
12. Remove the disposable database with explicit destructive authority.
13. Run focused persistence tests and full regression.

## 8. Test Database Rules

- Database name must be explicitly approved and guarded.
- Bootstrap resolves the repository head dynamically; obsolete revisions shall
  not be hardcoded as the permanent expected head.
- Clean-chain tests and compatibility tests use separate controlled fixtures.
- Tests never fall back to development or production databases.
- Database creation/deletion and migrations outside isolated tests require
  explicit authorization.

## 9. Migration Stop Conditions

Stop for multiple heads, unknown parent, model/schema disagreement, ambiguous
enum handling, destructive unapproved behavior, missing backfill semantics,
unrelated DDL, inability to run from an empty database, downgrade damage, or
regression failure.

## 10. Completion Evidence

Record revision, parent, one-head result, upgrade/downgrade/re-upgrade outcome,
clean-chain outcome, drift result, schema inspection, focused tests, and full
regression.
