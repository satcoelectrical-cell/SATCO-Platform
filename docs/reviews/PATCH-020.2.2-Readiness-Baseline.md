# PATCH-020.2.2 Readiness Baseline

## Status

Operational readiness evidence captured.

## Purpose

This document closes only the operational blockers recorded by the initial
PATCH-020.2.2 Implementation Readiness Review. It records the approved
accountability, file and test inventory, isolated database, mandatory guard,
migration baseline, regression baseline, development fingerprint, performance
conditions, exact command manifest, and execution environment.

It contains no production code, test, migration, API, schema, repository, or
service implementation and does not itself authorize implementation.

## Accountability

| Responsibility | Accountable party |
| --- | --- |
| Implementation Agent | Codex |
| Architecture and Product Reviewer | ChatGPT |
| Final Approval Authority | Repository Owner |
| Migration and Database Execution Authority | Repository Owner |
| Final Commit and Push Authority | Repository Owner |

These are software-delivery responsibilities. Engineering judgment and
engineering approval remain human responsibilities.

## Approved Implementation Inventory

The accepted Implementation Plan records the exact bounded source and test
inventory. It permits:

- dedicated relationship and Interface Commitment enum, model, exception,
  repository, and service modules;
- enum and model exports;
- metadata registration only if required by the existing convention;
- the focused test configuration guard;
- seven responsibility-based focused test modules;
- one additive Alembic revision generated from the approved base;
- lifecycle-required PATCH-020.2.2 evidence documents.

It explicitly excludes schemas, routers, application-router registration,
frontend work, Search integration, role changes, generic audit changes,
unrelated models, and unrelated tests. The migration filename and identifier
must be generated during the separately authorized migration phase rather
than invented during readiness closure.

## Validation Database

The approved database was absent before closure and was created once from
PostgreSQL `template0`:

```text
satco_platform_patch02022_test
```

No development data was copied and no migration was run.

Post-creation read-only verification:

| Check | Result |
| --- | --- |
| `current_database()` | `satco_platform_patch02022_test` |
| Public base tables | `0` |
| `alembic_version` table | absent |
| Copied development data | none |
| PostgreSQL volume operation | none |
| Upgrade or downgrade | none |

The database is empty and isolated from `satco_platform`.

## Mandatory Database-Name Guard

Every PATCH-020.2.2 PostgreSQL-specific migration, test, integrity, or
performance command must first open the configured validation connection and
assert:

```text
current_database() = 'satco_platform_patch02022_test'
```

The canonical guard command is recorded in the accepted Implementation Plan.
It requires an exact match and exits nonzero for a different, empty,
unavailable, or ambiguous database. URL-text inspection and pattern matching
do not satisfy the guard. A prior successful guard cannot authorize a later
command; the guard is rerun immediately before each PostgreSQL-specific
action.

Readiness evidence:

- the live validation connection returned exactly
  `satco_platform_patch02022_test`;
- the same guard against `satco_platform` raised
  `database guard rejected satco_platform`;
- both guard checks were read-only;
- no development mutation followed either check.

The read-only development fingerprint is the only approved exception that
connects to `satco_platform`, and it cannot share an execution command with a
migration or test.

## Migration Baseline

Read-only repository and database evidence:

| Item | Value |
| --- | --- |
| Repository Alembic head | `c2021f0c0a01` |
| Repository head count | `1` |
| Expected PATCH-020.2.2 base | `c2021f0c0a01` |
| Development database revision | `d8271b8f1a29` |
| Validation database revision | none |
| Repository history | one linear eight-revision chain |
| PATCH-020.2.2 migration | absent |
| Readiness upgrade or downgrade | none |

The recorded linear chain is:

```text
<base>
d25733017b10
c1ca2821f651
46350c98183b
b969ae9217a0
d8271b8f1a29
f18a1c0e2026
a20c1e0201f0
c2021f0c0a01
```

Any future PATCH-020.2.2 revision must have `c2021f0c0a01` as its immediate
base. A changed or branched head returns to readiness review.

## Pre-implementation Regression Baseline

The complete existing backend suite ran against the previously migrated,
isolated PATCH-020.2.1 validation database. No PATCH-020.2.2 production, test,
or migration artifact existed.

Exact command:

```bash
docker exec -e TEST_DATABASE_URL=postgresql://satco:satco_password@postgres:5432/satco_platform_patch02021_test satco-backend python -m pytest -q
```

Result:

| Measure | Result |
| --- | ---: |
| Collected | `120` |
| Passed | `120` |
| Failed | `0` |
| Skipped | `0` |
| Warnings | `596` |
| Duration | `44.18s` |

Warning baseline:

- Starlette TestClient deprecation: `1`;
- Pydantic class-configuration deprecations: `2`;
- SQLAlchemy `datetime.utcnow` deprecations: `593`.

These warnings are pre-existing and non-blocking for readiness. New warning
families or increases require explanation during implementation validation.

## Development Database Fingerprint

The fingerprint procedure reads only database identity, Alembic revision,
public table count, and governed row counts. It reads no row content and
performs no mutation.

Baseline:

| Item | Value |
| --- | ---: |
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
| Engineering Workspace tables | `0` |
| Engineering Context tables | `0` |
| PATCH-020.2.2 relationship or commitment tables | `0` |

Canonical value:

```text
database=satco_platform|revision=d8271b8f1a29|table_count=7|alembic_version=1|audit_logs=11|contacts=2|customers=5|project_code_sequences=0|projects=7|users=2|engineering_workspace_tables=0|engineering_context_tables=0|patch02022_tables=0
```

SHA-256:

```text
7668614e6c6a40ca9d10f7a9530aaa1a348c5d6d862d876c04d758b25e517995
```

The exact comparison procedure is:

1. query the same fields read-only in the same order;
2. render the canonical value with identical field names and separators;
3. calculate SHA-256 over the canonical value with no trailing newline;
4. compare both the full canonical value and hash;
5. block Final Review for any difference until separately explained and
   approved.

The fingerprint was unchanged after validation-database creation and the
pre-implementation regression.

## Focused Test Inventory

| Future module | Sole primary responsibility |
| --- | --- |
| `backend/tests/test_engineering_context_relationship_core.py` | Relationship identity, taxonomy, endpoints, lifecycle, withdrawal, restoration, duplicates, and bounded retrieval |
| `backend/tests/test_interface_commitment_lifecycle.py` | Complete permitted and prohibited commitment transitions, provider and consumer changes, delivery, fulfilment, withdrawal, restoration, rejection, dispute, and supersession |
| `backend/tests/test_engineering_context_relationship_permissions.py` | Capability matrix, confidentiality, cross-Project and cross-Workspace denial, transitive-access denial, and protected-identifier non-disclosure |
| `backend/tests/test_engineering_context_relationship_audit.py` | Mandatory material events, success evidence, forced audit failure, failed-mutation atomicity, and rollback |
| `backend/tests/test_engineering_context_relationship_concurrency.py` | One-winner optimistic concurrency for every required relationship and commitment mutation |
| `backend/tests/test_engineering_context_relationship_migration.py` | Model/database compatibility, migration replay, restrictive references, no backfill, and direct PostgreSQL rejection |
| `backend/tests/test_engineering_context_relationship_performance.py` | Deterministic corpus construction, measured operations, query counts, p95 limits, and confidentiality-preserving performance |

Existing Core Context, Workspace Core, Search, OpenAPI, audit, authentication,
Project, and complete backend suites remain regression responsibilities and
must not be weakened.

## Exact Validation Command Manifest

The accepted Implementation Plan contains the exact canonical guard, syntax,
mapper, import, OpenAPI, Alembic, focused, PostgreSQL, performance, regression,
fingerprint, diff, marker, whitespace, and cache commands.

Command readiness is complete subject to these execution gates:

- migration commands remain prohibited until migration execution is
  separately approved;
- future focused commands become executable only after the approved files
  exist;
- every PostgreSQL-specific command must pass the exact-name guard;
- the canonical validation URL is the only test and migration target;
- development access remains limited to the read-only fingerprint;
- generated caches are removed only after results are captured.

No command in the manifest authorizes implementation or migration by itself.

## Performance Conditions

The approved deterministic corpus uses seed `202022` and contains:

- `10,000` governed relationships;
- `2,500` Interface Commitments;
- `5` Customers;
- `10` Projects;
- `60` Workspaces, six per Project and covering all current Disciplines;
- `40%` Project-scoped and `60%` Workspace-scoped relationships;
- an even distribution across the four accepted relationship meanings;
- `90%` current and `10%` withdrawn relationships;
- commitments distributed as evenly as possible across accepted states;
- `80%` ordinary and `20%` restricted source confidentiality;
- even accepted criticality distribution;
- `20%` reassessment-needed standing;
- no cross-Project provider and consumer pair.

Each operation receives five unmeasured warm-ups and thirty measured samples.
Results must report p50, p95, maximum, query count, page size, actor, and
result.

Environment-specific p95 limits:

| Operation | Maximum p95 |
| --- | ---: |
| Relationship creation | `150 ms` |
| Authorized relationship detail | `100 ms` |
| One-hop bounded traversal, page size 50 | `200 ms` |
| Project-scoped relationship listing, page size 50 | `200 ms` |
| Workspace-scoped relationship listing, page size 50 | `200 ms` |
| Interface Commitment detail | `100 ms` |
| Scoped commitment listing, page size 50 | `200 ms` |
| Relationship versioned update | `150 ms` |
| Commitment versioned update | `150 ms` |
| Synchronized concurrency-conflict pair | `300 ms` |

These limits apply only to the recorded Docker Compose workstation,
deterministic corpus, software versions, and operations. They are not
universal performance claims. The corpus was not loaded during readiness
closure.

## Environment Baseline

Execution environment:

| Component | Version |
| --- | --- |
| Host platform | macOS workspace using Docker Desktop |
| Python | `3.12.13` |
| FastAPI | `0.140.0` |
| SQLAlchemy | `2.0.51` |
| Alembic | `1.18.5` |
| PostgreSQL | `17.10` |
| pytest | `9.1.1` |
| Docker Engine client | `29.6.2` |
| Docker Compose | `v5.3.1` |
| Backend execution | `satco-backend` container, working directory `/app` |
| PostgreSQL execution | `satco-postgres` container |
| Validation database | `satco_platform_patch02022_test` |

Version changes that can affect migration, mapper, test, or performance
behavior must be recorded with later results.

## Cache Cleanup

Generated `.pytest_cache`, `__pycache__`, `.pyc`, and `.pyo` artifacts under
`backend/` were removed after evidence capture. No source or user artifact was
removed.

## Remaining Risks

- performance limits are bounded to the recorded environment and synthetic
  corpus;
- the migration filename and revision identifier cannot exist until the
  separately authorized migration phase;
- authorization and confidentiality remain high-risk implementation areas;
- relationship persistence must not become a generic graph;
- Interface Commitment lifecycle must not become workflow;
- source changes and withdrawn standing require complete reassessment and
  audit evidence.

These are implementation and validation risks, not open operational readiness
blockers.

## Readiness Closure Result

The initial IRR operational blockers are closed:

- the Implementation Plan is Accepted;
- accountability is explicit;
- the bounded implementation and focused-test inventory is approved;
- the empty isolated validation database exists;
- the exact-name guard accepts validation and rejects development;
- repository and development migration baselines are recorded;
- the complete pre-implementation regression passes;
- the development fingerprint and comparison method are recorded;
- the command manifest is executable at its applicable lifecycle gates;
- deterministic performance conditions and limits are explicit;
- environment versions are recorded.

A repeated IRR is required. Only that gate may return
**READY FOR IMPLEMENTATION**.
