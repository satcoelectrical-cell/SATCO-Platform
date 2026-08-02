# PATCH-024 — EngineeringObject Persistence Migration

## Document Control

| Field | Value |
|---|---|
| Document ID | PATCH-024 |
| Status | Approved |
| Owner | SATCO Platform Architecture Team |
| Implementation | Authorized only by IRR-024 |
| Decision Date | 2026-08-01 |

## Purpose

Create the missing `engineering_objects` table required by the approved
PATCH-022.3 SQLAlchemy model so that PATCH-023 persistence can proceed.

## Governing Documents

- SATCO Governance Model
- SATCO Development Lifecycle
- EngineeringObject Blueprint v1.0
- PATCH-022.3 Engineering Object Aggregate
- PATCH-023 EngineeringObject Application Layer
- EDS-023
- IDS-023
- the approved current `EngineeringObject` SQLAlchemy model
- Alembic head `b2022c0202f2`

## Scope

PATCH-024 authorizes exactly one additive Alembic revision that:

- uses `b2022c0202f2` as its sole parent;
- creates the `engineering_objects` table;
- creates only the columns, nullability, string-backed controlled-enum checks,
  classification checks, foreign keys, defaults, and indexes already declared
  by the approved model;
- provides an upgrade that creates the table and its approved indexes;
- provides a downgrade that drops only the table and its table-owned indexes.

## Non-Scope

- changing the EngineeringObject SQLAlchemy model;
- changing Domain fields, meanings, invariants, commands, or state machines;
- creating PostgreSQL enum types;
- adding fields, constraints, indexes, triggers, sequences, or relationships
  not declared by the current model;
- data backfill or transformation;
- Audit, outbox, idempotency, repository, service, router, or API work;
- modifying another table;
- executing any migration against development, staging, or production.

## Dependencies

PATCH-024 depends on the approved PATCH-022.3 model and the repository schema at
the single Alembic head `b2022c0202f2`. PATCH-023 persistence depends on
successful completion of PATCH-024.

## Deliverable

The only implementation deliverable is:

- `backend/migrations/versions/e02400000001_engineering_objects_table.py`

No other implementation file is authorized.

## Acceptance Criteria

- the revision identifier is `e02400000001`;
- `down_revision` is exactly `b2022c0202f2`;
- upgrade creates exactly the approved table contract;
- downgrade removes exactly that table and its table-owned indexes;
- upgrade, downgrade, and re-upgrade pass in an approved isolated database;
- SQLAlchemy metadata and migrated PostgreSQL schema agree;
- all model and migration tests pass;
- Alembic reports one linear head after upgrade;
- no unrelated schema or source change is present.

## Approval Gates

Implementation requires PATCH approval, Architecture Review PASS, accepted
EDS-024, approved IDS-024, an executable Implementation Plan-024, and IRR-024
`READY FOR IMPLEMENTATION`.

## Authorization

Implementation is authorized only within the exact IDS-024 file boundary and
IRR-024. Migration execution remains separately controlled and is not
authorized for development, staging, or production environments.

## Revision History

| Version | Date | Description |
|---|---|---|
| 1.0 | 2026-08-01 | Approved bounded persistence-migration PATCH |

