# PATCH-051 Audit NULLS-LAST Physical-Index Migration Reconciliation — Focused Independent Review

## Review authority and boundary

This is the focused independent review of the design/governance-only
`PATCH-051 Audit NULLS-LAST Physical-Index Migration Reconciliation`. It does
not create or execute M5, change production code, rewrite M4, accept Batch 5,
perform a Whole-PATCH review, perform QG-11/QG-12, close PATCH-051 or begin
PATCH-052.

The review independently inspected Architecture-051, ADR-024, EDS-051, the
focused EDS persistence reconciliation, IDS-051, Implementation-Plan-051, the
Audit historical unknown-data reconciliation and its review, chronological
Batch-5 evidence/review, M1 through M4, the Audit model/query/cursor
implementation, the source Alembic graph, the installed isolated-schema
catalog evidence and the bounded planner/statistics evidence.

## Contract and migration-history review

The accepted physical contract is unambiguous:

```text
(organization_id, occurred_at DESC NULLS LAST, event_id DESC)
(organization_id, project_id, occurred_at DESC NULLS LAST, event_id DESC)
```

M4 source omits `NULLS LAST`; PostgreSQL therefore creates descending keys
with default `NULLS FIRST`. The authorized installed test database at M4 has
`NULLS LAST`, so the reconciliation correctly records, rather than conceals,
source/installed divergence.

Rewriting executed M4 would make the same revision identifier describe
different DDL across environments and would violate the accepted additive,
attributable and forward-recovery policies. The reconciliation correctly
rejects M4 rewrite.

One forward migration is sufficient. Proposed revision `e05100000005` with
`down_revision = "e05100000004"` can replace only the two named indexes with
the exact accepted definitions. No new table, column, constraint, trigger,
function, grant, data value or third index is needed. Both a fresh source
installation and either observed M4 starting state converge after M5 on one
revision and one physical schema.

## Query, cursor and planner review

The production organization known-time query must state
`occurred_at DESC NULLS LAST, event_id DESC` explicitly. That aligns the query
with the accepted index and changes no response, segment, cursor envelope or
authorization contract. The existing descending keyset continuation is
compatible and needs no redesign. The historical-unknown segment remains
isolated.

No Project-scoped Audit-list query currently exists in the router. The
reconciliation correctly authorizes no new endpoint while requiring future
M5 proof of the second physical index with the representative
Organization-plus-Project known-time shape.

The planner analysis is sufficient for governance disposition. The original
small analyzed fixture alone did not prove a production defect, but the later
larger analyzed probes demonstrated the null-order/source mismatch and
unintended sort. The reconciliation does not weaken acceptance, require an
irrational tiny-table plan or rely on disabled sequential scans as PASS proof.

## Historical, security and recovery review

M5 requires no data migration. Audit event IDs, tenant/project/workspace
scope, timestamps, correlations, metadata and historical nulls remain
unchanged. M4's immutable-row trigger and current-insert guard remain
installed and unchanged. Transactional Audit, tenant isolation and
authorization-before-disclosure semantics are unaffected.

The proposed downgrade correctly restores the exact M4 source-defined index
state—implicit descending `NULLS FIRST`—without touching M4 columns, data,
triggers or guards. It does not misrepresent that state as the accepted final
contract or claim unrestricted operational rollback safety.

## Upstream reconciliation review

No Architecture or ADR change is required. No EDS/IDS redesign or semantic
amendment is required because the accepted tenant-leading timestamp-index
intent remains unchanged and the focused Audit reconciliation already fixes
explicit `NULLS LAST`. The new artifact is appropriately append-only and
preserves prior failures and chronology.

No substantive redesign and no second migration are required.

## Findings

Critical: **0**

Major: **0**

Minor: **0**

Observation: **0**

## Verdict

The reconciliation preserves historical migration truth, fixes the exact
governed remedy at one forward M5, defines exact upgrade/downgrade and
query-alignment boundaries, and enables fresh/upgrade source-schema
convergence without introducing new Audit semantics.

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
