# Implementation Plan-027 — Evidence Foundation

## Status

**EXECUTABLE**

## Sequence and Checkpoints

1. Confirm single Alembic head `e02500000001` and isolated test database.
2. Implement enums, command DTOs, Aggregate Root, schemas, exceptions, and unit
   tests.
3. Implement models and migration `e02700000001` with parent `e02500000001`;
   validate clean upgrade, downgrade, re-upgrade, and model/schema match.
4. Implement ports, repository, validator, Unit of Work, Audit/outbox/
   idempotency adapters, and atomic/concurrency tests.
5. Implement service, authorization/compatibility validation, API, dependency
   wiring, registration, and focused security/API tests.
6. Run all Evidence tests, PATCH-023/PATCH-025/PATCH-026 Sprint-1 tests, then
   full backend regression and verify one Alembic head.

Each step is a stop checkpoint. No later success waives an earlier failure.

## Rollback

Before authoritative data, disable routes, revert bounded code, downgrade only
the isolated database to `e02500000001`, and run pre-PATCH regression. After
data exists, preserve Evidence and use separately approved forward repair;
physical deletion is not rollback.

## Stop Conditions

Stop for scope expansion, unavailable dependency, unlisted file/schema change,
authorization weakness, non-atomic effect, migration mismatch, or any blocking
focused/regression failure. Do not commit, push, deploy, or run production
migrations.
