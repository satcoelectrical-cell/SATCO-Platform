# PATCH-023 EngineeringObject Application Layer Implementation Plan

## Status

Approved

## Authority

This plan implements only the approved IDS-023. It grants no authority beyond
the exact file set, migration, tests, and commands listed there.

## Sequence

1. Confirm the repository baseline, active Alembic head, and isolated
   PATCH-023 test database.
2. Add the five Aggregate Root command methods and focused aggregate tests.
3. Add outbox/idempotency models, Audit UUID reference, registration, and the
   single migration.
4. Add application ports and Pydantic v2 schemas.
5. Add Repository and UnitOfWork adapters without independent commits.
6. Add Application Service orchestration and stable exceptions.
7. Add API router and register it in `app.main`.
8. Run focused tests, transaction-failure tests, and migration validation.
9. Run the complete backend regression suite.
10. Produce validation evidence and stop for Final Review before Commit.

## Validation Commands

Run only against the dedicated PATCH-023 test database after verifying its
exact name and isolation:

```text
docker exec satco-backend python -m compileall app tests
docker exec satco-backend python -m pytest -q tests/test_engineering_object_aggregate_commands.py tests/test_engineering_object_schemas.py tests/test_engineering_object_repository.py tests/test_engineering_object_service.py tests/test_engineering_object_api.py tests/test_engineering_object_transaction.py
docker exec satco-backend alembic current
docker exec satco-backend alembic heads
docker exec satco-backend alembic check
docker exec satco-backend python -m pytest -q
```

Migration upgrade, downgrade, and re-upgrade commands require the approved
isolated database-name guard and repository-owner database authorization.

## Required Evidence

- exact database identity and starting revision;
- one linear Alembic head;
- model/migration agreement;
- focused test results;
- direct constraint and transaction rollback evidence;
- complete regression results;
- unchanged development-database fingerprint;
- diff restricted to the IDS file set.

## Rollback

Before Commit, code rollback removes only PATCH-023 additions and restores only
PATCH-023 modifications. In the isolated database, downgrade removes only
revision `e02300000001`. No development, staging, or production database is
changed without separate authorization. Published or production command data
requires backup-and-restore planning rather than destructive downgrade.

## Stop Conditions

Stop immediately for any IDS file-set expansion, second migration, persisted
EngineeringObject field change, generic update, physical delete, missing
atomicity, authorization ambiguity, protected-data disclosure, migration-head
divergence, or regression failure.

## Completion Gate

Implementation is complete only after focused validation, migration evidence,
full regression, repository-scope review, and Final Review PASS. Commit and
Push remain separately authorized.
