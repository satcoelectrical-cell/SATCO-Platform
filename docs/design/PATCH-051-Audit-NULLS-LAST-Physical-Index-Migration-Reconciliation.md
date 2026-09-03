# PATCH-051 Audit NULLS-LAST Physical-Index Migration Reconciliation

## Status and authority

| Field | Value |
|---|---|
| Scope | B5-MAJ-02 physical Audit index ordering and migration-history reconciliation only |
| Human authority | **HUMAN PATCH-051 B5-MAJ-02 MIGRATION-CORRECTION RECONCILIATION AUTHORITY: GRANTED** |
| Result | **PASS / ACCEPTED / COMPLETE** |
| Production implementation authority | NOT GRANTED BY THIS RECORD |
| Migration creation/execution authority | NOT GRANTED BY THIS RECORD |
| Current source Alembic head | `e05100000004` |
| B5-MAJ-02 | OPEN; remediation path resolved only |
| Batch 5 | NOT ACCEPTED |
| PATCH-051 | OPEN |

This append-only reconciliation preserves Architecture-051, ADR-024,
EDS-051, its focused persistence reconciliation, IDS-051,
Implementation-Plan-051, the Audit historical unknown-data reconciliation,
M1 through M4, and the chronological Batch-5 evidence. It decides only the
governed migration-history remedy for the proven physical index-ordering
defect. It creates or executes no migration, changes no production code or
database, accepts no Batch, and grants no PATCH-052 authority.

## Accepted contract

The controlling Audit historical unknown-data reconciliation makes null
placement explicit. The two accepted physical indexes are exactly:

```text
(organization_id, occurred_at DESC NULLS LAST, event_id DESC)
(organization_id, project_id, occurred_at DESC NULLS LAST, event_id DESC)
```

The known-time segment is separately constrained by `occurred_at IS NOT NULL`
and ordered by `occurred_at DESC, event_id DESC`; the historical-unknown-time
segment is separately constrained by `occurred_at IS NULL` and ordered by
`event_id DESC`. The explicit physical `NULLS LAST` contract remains
authoritative even though known-time results contain no null timestamp.

Architecture-051 requires additive, exact migration and immutable historical
meaning. ADR-024 requires additive, attributable reconciliation without
rewriting Audit history. EDS-051 and IDS-051 require the two tenant-leading
timestamp indexes and forward recovery after use. The later focused Audit
reconciliation controls the null-placement detail and authorizes no change to
those higher-level decisions.

## Proven M4 source defect

`e05100000004_audit_time_correlation.py` creates both indexes with
`occurred_at DESC` and does not state `NULLS LAST`. PostgreSQL's default for a
descending btree key is `NULLS FIRST`. Therefore a fresh M3-to-M4 migration
from the current repository source does not create the accepted physical
ordering.

This is a migration-source defect. It is not a reason to pretend M4 always
contained `NULLS LAST`, and it is not corrected by changing documentation or
the query alone.

## Source and installed-schema divergence

Read-only catalog inspection of the authorized isolated database
`satco_platform_patch02022_test` at revision `e05100000004` found both named
indexes physically defined with `occurred_at DESC NULLS LAST`. The current M4
source would instead reproduce implicit `DESC NULLS FIRST`. Thus:

```text
current M4 source -> NULLS FIRST
authorized installed M4 schema -> NULLS LAST
accepted final contract -> NULLS LAST
```

The installed schema is not evidence that M4 source always contained the
accepted definition. Chronology and the source/installed divergence remain
explicit until a forward correction becomes the sole head.

## Planner evidence interpretation

The preserved Batch-5 evidence records a 10,103-row analyzed multi-tenant
fixture where the organization-known-time query produced a sequential scan
plus sort instead of the expected organization index plan.

Focused diagnosis then compared the accepted predicates and ordering on
bounded rollback-only fixtures. With current statistics and 110,103 rows,
PostgreSQL still selected the overlapping organization-project index through
a bitmap path and added a sort for the organization query. A source-M4-shaped
probe confirmed that raw `DESC` definitions are implicit `NULLS FIRST`.
Changing only the query to explicit `NULLS LAST` could not eliminate the sort
against those source-M4 definitions. The evidence therefore excludes tiny
cardinality and stale/missing `ANALYZE` as the complete root cause.

The planner is behaving correctly: an index cannot supply a requested null
ordering different from its physical ordering. Representative future proof
must use fresh statistics, the exact production-shaped query, both accepted
indexes, and must demonstrate index usability and sort elimination without
using disabled sequential scans as primary evidence.

## Migration-history decision

Rewriting M4 is not allowed. M4 has already been executed, contains truthful
historical conversion and guard semantics, and is an accepted chronological
fact. Rewriting an executed revision would make one revision identifier mean
different DDL in different environments and would conceal the discovered
source/installed divergence. That conflicts with the accepted additive,
attributable and forward-recovery policies.

The correct governed remedy is one forward corrective migration:

```text
revision:      e05100000005
down_revision: e05100000004
purpose:       reconcile only the two physical Audit index orderings
```

No second migration and no substantive redesign are required. M5 is eligible
for separate Human migration-creation authority; this record does not create
or execute it.

## Exact allowed M5 scope

An authorized M5 upgrade may only replace the two existing indexes, retaining
their names and creating these exact definitions:

```sql
CREATE INDEX ix_dp_audit_organization_occurred_event
ON package_configuration_audit_events
(organization_id, occurred_at DESC NULLS LAST, event_id DESC);

CREATE INDEX ix_dp_audit_organization_project_occurred_event
ON package_configuration_audit_events
(organization_id, project_id, occurred_at DESC NULLS LAST, event_id DESC);
```

The replacement must occur in the migration's controlled transactional
boundary. It adds no third index, table, column, constraint, trigger, function,
grant, business state or cursor state. It performs no Audit-row DML and does
not change `occurred_at`, `correlation_id`, metadata, event identity, tenant
keys, immutability or the current-insert guard. Migration tests must compare
row counts and durable original/new values before and after upgrade and
downgrade.

On an environment produced by current M4 source, M5 changes `NULLS FIRST` to
`NULLS LAST`. On the authorized isolated database, where the physical indexes
already have `NULLS LAST`, M5 deliberately replaces them with equivalent
definitions and advances the revision to record the authoritative correction.
Both paths then converge at the same source head and physical schema.

## Production query alignment

The organization known-time production query currently orders with
SQLAlchemy `.desc()` only. The separately authorized implementation must make
the accepted null placement explicit:

```text
WHERE organization_id = :organization_id
  AND occurred_at IS NOT NULL
ORDER BY occurred_at DESC NULLS LAST, event_id DESC
LIMIT :bounded_limit
```

This is implementation alignment with the accepted contract, not an API or
architecture redesign. The known-time continuation remains:

```text
occurred_at < :time
OR (occurred_at = :time AND event_id < :event_id)
```

It is compatible with the descending composite index and needs no cursor
format or state-machine change. The historical segment remains a separate
query and cannot be combined with the known-time predicate.

There is currently no separate Project-scoped Audit-list endpoint/query in
the production router. No new endpoint is authorized or required. Future
representative proof of the second accepted index uses the accepted internal
shape:

```text
WHERE organization_id = :organization_id
  AND project_id = :project_id
  AND occurred_at IS NOT NULL
ORDER BY occurred_at DESC NULLS LAST, event_id DESC
LIMIT :bounded_limit
```

If a governed Project-scoped reader is later implemented, it must use that
shape after Project authorization and protected-not-found ordering.

## Downgrade semantics

M5 downgrade restores the exact source-defined M4 index state and no other
state:

```text
(organization_id, occurred_at DESC, event_id DESC)
(organization_id, project_id, occurred_at DESC, event_id DESC)
```

In PostgreSQL those definitions mean descending `NULLS FIRST`. The downgrade
must not remove M4 columns, alter or delete Audit rows, touch triggers/guards,
restore the obsolete organization-only index, or invent a third state. This
is migration-topology reversibility only; it is not a claim that a
`NULLS LAST`-aligned application can safely remain deployed after downgrade.
Operational downgrade still requires the accepted compatibility, writer-drain
and application sequencing policy. Forward recovery remains preferred after
use.

## Convergence proof obligations

After separately authorized implementation:

1. fresh install traverses M1, M2, M3, defective historical M4, then M5 and
   ends at the exact accepted `NULLS LAST` definitions;
2. an upgrade from an M4/source-produced `NULLS FIRST` schema replaces both
   indexes and preserves every Audit value/object outside those indexes;
3. the authorized installed M4/`NULLS LAST` schema also traverses M5 and ends
   with the same definitions and revision;
4. M5 downgrade restores exact M4 source definitions;
5. re-upgrade restores exact M5 definitions;
6. representative analyzed organization and organization-project query plans
   use the respective named indexes and eliminate an unintended sort; and
7. functional pagination, cursor binding, tenant negatives, transactional
   Audit, immutable history and insert-guard regressions remain green.

## Upstream impact and boundaries

Architecture-051 requires no change. ADR-024 requires no change. EDS-051 and
IDS-051 require no redesign or semantic amendment: their accepted
tenant-leading timestamp-index intent remains intact, and the focused Audit
historical reconciliation already supplies the exact `NULLS LAST` detail.
This record is a downstream append-only migration-history reconciliation.

There is no data migration, Audit semantic change, cursor redesign, retention
change, authorization change, runtime grant change, PATCH-052 capability or
new index. Production query alignment and M5 creation remain separate,
explicitly bounded implementation actions.

## Governance outcome

Historical migration truth is preserved, the exact accepted index contract is
retained, one forward M5 is sufficient, and fresh/upgrade paths can converge
on one schema without changing Audit data or semantics.

PATCH-051 AUDIT NULLS-LAST MIGRATION RECONCILIATION:
PASS / ACCEPTED / COMPLETE

B5-MAJ-02:
OPEN / REMEDIATION PATH RESOLVED

Corrective M5:
ELIGIBLE FOR SEPARATE HUMAN AUTHORITY

Batch 5:
NOT YET ACCEPTED

PATCH-051:
OPEN
