# IDS-028 Test-Isolation Amendment — Independent Focused Review

## Review Control

| Field | Value |
|---|---|
| Related PATCH | PATCH-028 |
| Amendment scope | One existing test file only |
| Result | PASS |
| Date | 2026-08-03 |

## Authorized File

- `backend/tests/test_patch_028_1_migration.py`

No other backend, migration, runtime, configuration, or test file is included.

## Finding Reviewed

The PATCH-028.1 downgrade test removes the persistent test Organization during
an in-process migration sequence. A separately launched migration suite passes,
but the shared process state becomes order-dependent. This conflicts with the
Testing Engine requirement that tests be deterministic, isolated, repeatable,
and responsible for disposable-resource cleanup.

## Amendment Boundaries

The authorized remediation may only:

- own the disposable database state used by this test module;
- restore repository Alembic head in every success and failure path;
- restore the persistent test Organization required by the guarded test
  environment;
- retain every existing downgrade, preservation, rollback, and migration-head
  assertion.

It may not edit a production migration, weaken or skip an assertion, change
runtime behavior, conceal migration failure, introduce ordering requirements,
touch development/deployment databases, or expand PATCH-028 semantics.

## Independent Decision

**PASS.** One test-file amendment is the smallest coherent correction. It
repairs validation determinism without modifying the migration or product
contract and strengthens Evidence Before Completion and Continuous Evolution.

```text
Manifesto Alignment Verified: YES
QG-M1 amendment result: PASS
Test-only remediation implementation: AUTHORIZED
Development/deployment migration: NOT AUTHORIZED
Commit/push: NOT AUTHORIZED
Sprint 3: NOT AUTHORIZED UNTIL VALIDATION AND RE-REVIEW
```
