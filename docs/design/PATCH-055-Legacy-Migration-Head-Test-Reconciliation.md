# PATCH-055 — Legacy Migration Head Test Reconciliation

Status: HUMAN ACCEPTED / COMPLETE
Date: 2026-09-17

## Finding

Final PATCH-055 regression exposed legacy migration tests that hard-code `e05400000006` as the repository/test-database head. The current governed chain has advanced additively through `e05500000001` to sole head `e05500000002`; `tests/conftest.py` already derives `TEST_DATABASE_REVISION` dynamically from Alembic.

These assertions protect historical parentage, but their hard-coded *current head* value is stale after an additive successor PATCH. They do not indicate a PATCH-055 runtime or schema failure.

## Narrow reconciliation

Preserve every historical parent/down-revision assertion. Replace only assertions that equate the repository/current test head with `e05400000006` by the dynamic `TEST_DATABASE_REVISION`, or by `e05500000002` only where the test specifically verifies the PATCH-055 tip.

The explicit PATCH-054 lineage assertions such as `e05400000006 -> e05400000005` remain unchanged. Downgrade/upgrade tests that intentionally exercise a historical PATCH-054 boundary remain unchanged unless final cleanup must restore the current repository head.

## Authorized test-only boundary after Human acceptance

Only the stale current-head assertions in existing backend migration tests may be edited. No production model, service, router, schema, migration, frontend, accepted ADR/EDS semantic, or customer/production database may be changed by this reconciliation.

Qualification must rerun the affected migration tests and then the complete backend suite against the disposable PATCH-055 PostgreSQL database. Zero failure is required before Whole-PATCH Final Review/QG-M1/QG-11.

No staging, commit, push, deploy, QG-11 acceptance, QG-12, PATCH-055 closure, or PATCH-056 authority is granted here.
