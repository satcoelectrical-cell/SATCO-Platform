# PATCH-051 Batch-2 focused PostgreSQL re-review

## Verdict

**PASS / ACCEPTED / COMPLETE** for Batch-2 implementation.

The former blocker `B2-051-MAJ-01` is **resolved / closed**. The evidence was
obtained exclusively from the repository-designated local disposable test
database `satco_platform_patch02022_test`, not `satco_platform` or any customer
or operational database.

## Evidence reviewed

- M1 fail-closed when `satco_registry_installer` was absent; external bootstrap
  then enabled M1 with no Alembic login creation.
- M1/M2 executed through `e04700000001 -> e05100000001 -> e05100000002`.
- Live schema inspection proved 12 M1 tables, normalized semantic-profile and
  release/profile identities, four nullable M2 columns, expected states,
  checks, indexes and the unvalidated exact Workspace-binding FK.
- Synthetic PostgreSQL probes proved R1/R2 semantic-profile reuse, exact
  Project provenance rejection and cross-tenant composite-key rejection.
- Runtime mutation was denied; installer installation/current activation,
  idempotent reconciliation, and forbidden installer writes were proven.
- Two real independent PostgreSQL sessions proved the exact advisory key,
  shared coexistence, exclusive conflict, post-rollback release, and the
  `SET LOCAL lock_timeout = '5s'` first-SQL contract.
- A controlled conflicting exclusive lock timed out after the five-second
  transaction-local limit and the waiting transaction rolled back without a
  protected write.
- Audit staging flushed only under its caller-owned transaction and disappeared
  after rollback. M2 safe downgrade/re-upgrade passed before shadow use.

## Bounded remediation

Two implementation-only corrections were made and revalidated: direct CLI
module-path bootstrap, and a non-completing projection flush before
same-UoW activation. Both are inside Batch-2 scope; no migration definition,
M3, Batch-3 behavior or PATCH-052 code was added.

## Finding register

| ID | Severity | Status |
|---|---:|---|
| B2-051-MAJ-01 | Major | Resolved / closed by isolated PostgreSQL evidence |
| B2-051-OBS-01 | Observation | Resolved for isolated test only |
| IDS051-OBS-01 | Observation | Open; deployment-specific census remains a later obligation |

New findings: Critical 0, Major 0, Minor 0, Observation 1.

Batch 3 is eligible only for separate Human authority. It is not authorized by
this review, and no further migration execution is authorized beyond the
isolated validation already performed.
