# PATCH-054 — Final Regression Reconciliation Review

**Date:** 2026-09-14
**Qualified immutable tip:** `2dc792c5e6800b2668676c17abfae9aa5a4fc807`
**Purpose:** classify full-backend regression failures before QG-11

## Fresh regression result

On an isolated Git archive of the qualified tip:

- PATCH-054 focused backend: **65/65 PASS**
- cumulative standards/report-standards surface: **180/180 PASS**
- full frontend: **136/136 PASS** across 29 files
- frontend typecheck: **PASS**
- production frontend build: **PASS**
- full backend: **1852 PASS / 17 FAIL**

QG-11 remains blocked because Whole-PATCH qualification requires zero applicable full-regression failures.
## Failure classification

### A. Stale repository-head assumptions

Twelve failures are from historical tests that still assume `e05300000002` is the current repository/database head after PATCH-054 advanced the sole head to `e05400000006`.

Affected areas include PATCH-053 cross-discipline migration/conformance and earlier migration-lineage tests for customer organization, deliverables, execution plan, onboarding, organizational memory, PATCH-052, project controls, project foundation and supporting files.

These tests must preserve their historical migration-under-test revision and parent assertions while deriving or separately asserting the repository's current sole head. Blindly replacing every historical `e05300000002` token with `e05400000006` is prohibited.

### B. Host/export harness assumptions

Five failures are harness portability failures:

- `test_engineering_context_migration.py` invokes bare `alembic` and hard-codes `cwd="/app"`;
- three parameterized `test_technical_report_database_roles.py` vectors invoke bare `alembic`.

The isolated export uses the repository venv directly, so those assumptions do not hold. The remediation must invoke Alembic through the active Python environment and use the actual repository/backend root rather than an environment-specific `/app` path.
## Governance disposition

This is a test/harness reconciliation only. No production code, migration, schema, API, behavior, PATCH-055 scope, or accepted engineering semantics are implicated by the 17 failures.

**Independent finding:** one blocking Major remains at final-regression level.

`P054-FRR-MAJ-02 — Historical regression tests/harness are not reconciled to the current PATCH-054 head and isolated qualification environment.`

**Disposition:** OPEN / BLOCKING / TEST-ONLY RECONCILIATION REQUIRED.

The next safe action is a separately Human-authorized, test-only remediation over the exact failing test paths, followed by a fresh full-backend regression from an immutable tip. QG-11 cannot be recommended PASS before that rerun is zero-failure.

## Implementation and validation update

Human authorization was granted for the exact 13-file test-only boundary. Focused validation completed in two bounded groups: **123/123 PASS** and **196/196 PASS**, for **319/319 PASS** total. A clean archive of base tip `2dc792c5e6800b2668676c17abfae9aa5a4fc807` was overlaid with only those 13 test changes; full backend regression then completed **1870/1870 PASS** with no failures.

`P054-FRR-MAJ-02` is therefore **RESOLVED / CLOSED** at implementation and pre-commit qualification level. No production source, migration, schema, API or behavior changed.
