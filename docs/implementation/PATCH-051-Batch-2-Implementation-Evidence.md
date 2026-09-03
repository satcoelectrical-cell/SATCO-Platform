# PATCH-051 Batch-2 implementation evidence

## Authority and boundary

Batch-2 implementation and creation of only `e05100000001` and
`e05100000002` were authorized. Neither migration was executed. M3 was not
created and Batch 3/PATCH-052 work was not started.

## Implemented manifest

Created production artifacts are the Discipline Package SQLAlchemy models,
strict projection DTOs, non-completing repository and UoW, Registry projection
service, deployment-only Registry installer, read-only preflight census, and
the two authorized migrations. Modified artifacts register metadata, provide
the guard and runtime readiness boundary, add non-completing generic Audit
staging, register Alembic metadata, and wire the bootstrap/preflight/Compose
role and secret interfaces.

M1 defines the accepted twelve empty tables: six Registry projection/profile
tables and six organization/project/package-Audit tables. It preserves semantic
profile identity `(profile_id, profile_digest)`, Registry/profile membership
`(registry_digest, profile_id)` with the carried digest, exact Project
provenance, composite tenant keys, immutable-history triggers, a deferred
selection-cardinality check, and fixed role grants. M2 is nullable-only and
adds no backfill, validation, `NOT NULL`, raw-discipline rewrite, or M3 logic.

## Authority and safety evidence

The runtime role is granted read-only projection access in M1. The installer
is separately bootstrapped as `satco_registry_installer`, receives only
projection `SELECT`, `INSERT`, and `UPDATE (is_current)`, and is isolated from
the HTTP backend secret set. Login creation is in bootstrap/preflight source,
not Alembic. `stage_audit_log()` adds an Audit row without commit or rollback.
The same-session advisory helper uses `(1396790339, 51)`, sends
`SET LOCAL lock_timeout = '5s'` before the requested shared/exclusive advisory
transaction lock, and the UoW retains one outer completion owner.

The preflight CLI opens an explicit read-only, repeatable-read, deferrable
transaction and emits canonical JSON/SHA-256. It fails closed for a query
failure, head mismatch, unsupported/null Workspace values, duplicate mapping
candidates, project-orphaned Workspaces, or unavailable Registry source.

## Validation actually performed

- Python bytecode compilation for new/modified Batch-2 Python artifacts: pass.
- Shell syntax for role bootstrap and operational preflight scripts: pass.
- SQLAlchemy model import and twelve-table metadata assertion in the existing
  backend container: pass.
- Alembic graph inspection only: `e05100000002 (head)`.
- Focused static assertions for projection identity, migration chain/M2 shape,
  preflight hashing, role-source references, and guard constants: pass.
- `git diff --check`: pass.

## Explicitly unavailable evidence

No Alembic upgrade/downgrade, live migration SQL, schema DDL, Registry
installation, role-grant behavior test, or advisory-lock concurrency test was
run. The repository's PostgreSQL test bootstrap would upgrade the test schema;
that is outside the granted migration-execution authority. Therefore real
PostgreSQL behavior and live-data census evidence are **NOT VERIFIED**, not a
PASS claim. This is the open Batch-2 acceptance blocker and preserves
`IDS051-OBS-01`.

## Isolated PostgreSQL validation — 2026-08-30

Human authority subsequently permitted migration execution only on the
repository-designated local Compose test database
`satco_platform_patch02022_test`. Read-only identity checks established that it
is distinct from `satco_platform`, owned by the local schema-owner role, named
by the repository's test guard, and began at `e04700000001`. No production,
customer, or governed operational database was contacted.

The M1 missing-installer-role negative case failed closed before schema
creation. The restricted installer login was then provisioned externally for
this isolated test only. With PASS read-only preflight artifacts, M1 and M2
executed to `e05100000002`. Live inspection confirmed all 12 M1 tables, the
four nullable M2 columns, M2 checks/FK/indexes, semantic profile and
release/profile PK shapes, and the `NOT VALID` binding FK. A final census
reported PASS at `e05100000002`, zero Workspace rows and zero non-null shadows.

Real PostgreSQL probes passed for semantic-profile reuse across two Registry
releases, invalid Project Registry/profile provenance rejection, cross-tenant
Audit rejection, runtime projection-mutation denial, installer forbidden
DELETE/tenant-write denial, wrong-role installer failure, installer install /
activation / idempotent re-install, exact shared/exclusive advisory-lock
interaction on `(1396790339, 51)`, first-SQL timeout ordering, and staged Audit
rollback. The safe M2 downgrade/re-upgrade path passed before any shadow value
was used. M1 downgrade was not forced after Registry data existed; the accepted
forward-recovery policy remains intact.

A controlled real two-session exclusive-lock wait reached the governed
five-second timeout, raised an error, and rolled back the waiting transaction
without writes (`guard-timeout-rollback-ok`).

Two bounded validation remediations were required: direct CLI import bootstrap
and a non-completing flush before same-UoW activation. Both were rerun against
the isolated database and passed. The fixture-backed command
`python -m pytest -q tests/test_discipline_package_projection.py
tests/test_discipline_package_migration.py tests/test_discipline_package_preflight.py
tests/test_discipline_package_transaction.py` passed **5 tests**.

The final isolated-test census artifact is
`/tmp/patch051-preflight/patch051-isolated-final-7eb659744a08e060a65defa64a9968ef.json`
with SHA-256
`16d2ea304aec2ab2f82b3e06597b0758fbbf4c748e55e3b5e2657889ccfe923d`.
It is isolated-test evidence only and does not close the later deployment
obligation `IDS051-OBS-01`.
