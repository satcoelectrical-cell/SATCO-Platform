# PATCH-020.2.1 Readiness Baseline

## Status

Operational readiness evidence captured.

## Purpose

This report records the pre-implementation environment, migration, regression,
and development-database fingerprint baseline for PATCH-020.2.1.

It does not authorize implementation and contains no production code, test,
migration, interface, or data-design change.

## Accountability

| Responsibility | Accountable role |
| --- | --- |
| Implementation Agent | Codex |
| Architecture and Product Reviewer | ChatGPT |
| Final Approval Authority | Repository Owner |
| Migration and Database Execution Authority | Repository Owner |
| Final Commit and Push Authority | Repository Owner |

These are software-delivery responsibilities only. Engineering judgment and
engineering approval remain human responsibilities under SATCO governance.

## Validation Database

The approved dedicated database was absent before readiness closure and was
created once:

```text
satco_platform_patch02021_test
```

Post-creation read-only verification:

- exact current database: `satco_platform_patch02021_test`;
- public table count: `0`;
- `alembic_version`: absent;
- development data copied: none;
- migration run: none;
- PostgreSQL volume created, deleted, or replaced: none.

The database remains empty and isolated from `satco_platform`.

## Database-Name Guard

Every PATCH-020.2.1 migration and PostgreSQL test command must query
`current_database()` through the same connection configuration used by the
command and require the exact result:

```text
satco_platform_patch02021_test
```

Any other, empty, unavailable, or ambiguous value exits nonzero before the
guarded action. Pattern matching and URL-text inspection do not satisfy the
guard.

Readiness validation confirmed that the exact live name is accepted and a
non-matching development name is rejected before any guarded action. Both
checks were read-only.

The exact guarded commands are permanent in
`docs/design/Implementation-Plan-020.2.1-Core-Context-Foundation.md`.

## Migration Baseline

- repository Alembic head: `a20c1e0201f0`;
- repository heads count: `1`;
- expected PATCH-020.2.1 base: `a20c1e0201f0`;
- development database revision: `d8271b8f1a29`;
- history: one linear seven-revision chain from base to head;
- readiness upgrade or downgrade run: none;
- PATCH-020.2.1 migration created: none.

## Pre-implementation Regression

The complete existing suite ran against the established isolated
`patch0201_validation` schema at repository head `a20c1e0201f0`.

Exact successful command:

```bash
docker exec -e PGOPTIONS=-csearch_path=patch0201_validation -e TEST_DATABASE_URL=postgresql://satco:satco_password@postgres:5432/satco_platform_patch019_test satco-backend python -m pytest -q
```

Result:

- collected: `83`;
- passed: `83`;
- failed: `0`;
- skipped: `0`;
- warnings: `289`;
- duration: `21.89s`.

Warning baseline:

- Starlette TestClient deprecation: `1`;
- Pydantic class-configuration deprecations: `2`;
- SQLAlchemy `datetime.utcnow` deprecations: `286`.

An earlier default-schema attempt stopped during collection because the prior
isolated database’s public schema remained below the required Workspace Core
head. It ran no test and changed no data.

## Development Database Fingerprint

The fingerprint reads only database identity, migration revision, table count,
and row counts. It does not inspect row content.

Baseline:

| Item | Value |
| --- | --- |
| Database | `satco_platform` |
| Alembic revision | `d8271b8f1a29` |
| Public table count | `7` |
| `alembic_version` rows | `1` |
| `audit_logs` rows | `11` |
| `contacts` rows | `2` |
| `customers` rows | `5` |
| `project_code_sequences` rows | `0` |
| `projects` rows | `7` |
| `users` rows | `2` |
| Engineering Context tables | `0` |

Canonical value:

```text
database=satco_platform|revision=d8271b8f1a29|table_count=7|alembic_version=1|audit_logs=11|contacts=2|customers=5|project_code_sequences=0|projects=7|users=2|engineering_context_tables=0
```

SHA-256:

```text
a5c31884adf1faa73e638311ba437d7dcf3013857fca3aa9450c00abe2640b7d
```

The same procedure and hash were repeated after database creation, regression,
and cache cleanup. The result was unchanged.

Future validation must compare both canonical value and hash after all
isolated work. A mismatch blocks Final Review.

## Performance Validation Conditions

Approved conditions:

- deterministic 10,000-element representative dataset;
- dedicated isolated database only;
- no development or production data;
- bounded detail, Project page, Workspace page, successful update, and stale
  update categories;
- at least one warm-up and 30 measured iterations per category;
- p50, p95, maximum, query count, target, and pass or fail result;
- repeatable guarded command recorded in the Implementation Plan;
- results apply only to the tested environment, version, dataset, and
  operation.

The performance dataset was not created or loaded during readiness closure.

## Cache Cleanup

Generated `.pytest_cache`, `__pycache__`, `.pyc`, and `.pyo` artifacts under
`backend/` were removed after the baseline run.

## Readiness Result

The following former operational blockers are closed:

- accountable roles;
- dedicated empty validation database;
- exact database-name guard behavior;
- repository and development migration baseline;
- pre-implementation complete regression baseline;
- development fingerprint procedure and hash;
- exact future validation commands;
- performance-validation conditions.

No implementation or migration was created. Repeated IRR remains required
before implementation.
