# PATCH-042 Full-Regression Fixture Reconciliation

Date: 2026-08-22
Disposition: bounded test-only reconciliation; no PATCH-042 product semantics.

The full backend regression initially failed in
`test_concurrent_updates_have_one_winner_and_one_audit`. Its standalone Session
created a `Customer` after PATCH-038 made `Customer.organization_id` non-null
and foreign-key protected, but—unlike the shared `db_session` fixture—it did
not create the referenced canonical test Organization first. PostgreSQL
correctly rejected that stale fixture.

The correction creates the already-established test Organization
`02810000-0000-4000-8000-000000000001` before the standalone Customer. It does
not weaken the foreign key, bypass tenant ownership, fabricate a production
Organization, or modify production/domain behavior.

Evidence:

- before correction: targeted test FAIL with
  `fk_customers_organization_id_organizations` foreign-key violation;
- after correction: targeted test PASS;
- owning `test_engineering_context_core.py` module: 8 passed;
- likely adjacent standalone Customer fixtures: 28 passed.

The fixture is historically owned by the interaction between the pre-existing
engineering-context concurrency test and accepted PATCH-038 Customer tenancy.
It is excluded from PATCH-042 production semantics but included in the bounded
validation delivery boundary because it is required for truthful full-suite
evidence.

The first resumed full-suite runner also produced one environment-only failure
in `test_engineering_context_database_contract`. That test intentionally runs
`alembic heads` from `/app`; the disposable runner mounted current source at
`/workspace/backend` but still had a pre-PATCH-041 image tree at `/app`. The
live test database was at `e04100000001`, while that stale image tree reported
`e03800000001`. Mounting the same current repository backend at the test's
explicit `/app` path made the unchanged exact-head assertion pass (1 passed).
No migration test, migration artifact, or production behavior was changed for
this runner-isolation correction.
