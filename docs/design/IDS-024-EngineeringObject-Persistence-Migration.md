# IDS-024 — EngineeringObject Persistence Migration

## Status

Approved

## Governing Baseline

- PATCH-024 Approved;
- AR-024 PASS;
- EDS-024 Accepted;
- EDS-024 Review PASS;
- current EngineeringObject SQLAlchemy model;
- current Alembic head `b2022c0202f2`.

## Exact Authorized File Set

Create exactly:

- `backend/migrations/versions/e02400000001_engineering_objects_table.py`

No existing file may be modified. No second file is authorized.

## Revision Contract

- revision: `e02400000001`;
- down revision: `b2022c0202f2`;
- branch labels: none;
- dependencies: none;
- one `upgrade()` and one `downgrade()`;
- no application-model import from the migration;
- deterministic literal DDL matching EDS-024.

## Implementation Contract

Upgrade shall create exactly the EDS-024 table, named constraints, and four
indexes. Controlled values shall use String columns plus the exact approved
check constraints. Foreign-key names and ON DELETE RESTRICT behavior shall
match the model. Server defaults shall exist only for lifecycle, authority
standing, version, created timestamp, and updated timestamp.

Downgrade shall drop the four named indexes and then
`engineering_objects`. It shall not modify any other relation.

## Validation Contract

Before execution, verify the target is an explicitly approved isolated test
database at head `b2022c0202f2`. Then validate:

1. static revision identifiers and scope;
2. upgrade to `e02400000001`;
3. one Alembic head;
4. exact columns, types, nullability, defaults, primary key, five foreign keys,
   ten named checks, and four named indexes;
5. accepted and rejected constraint cases;
6. downgrade to `b2022c0202f2`;
7. absence of only `engineering_objects` after downgrade;
8. re-upgrade and schema equivalence;
9. focused EngineeringObject model/migration tests;
10. complete backend regression.

## Rollback

Before commit, remove the uncommitted revision file to roll back source. In the
approved isolated database only, downgrade one revision. No destructive
downgrade is authorized where EngineeringObject data must be retained.

## Stop Conditions

Stop for any expanded file set, revision-parent mismatch, schema mismatch,
additional object, existing target table, nonempty target data concern,
migration divergence, regression, or non-isolated database.

## Approval

IDS-024 is approved for IRR review. It grants no migration-execution authority
outside an approved isolated validation database.

