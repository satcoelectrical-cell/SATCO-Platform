# Implementation Plan-047

1. **Foundation/persistence:** separate Risk/Issue/Decision/Change/Impact
   contracts, models, history/outbox/idempotency, `e04600000001` migration and
   repository constraints with migration/repository tests. No service/router/UI.
2. **Application/integration:** one UoW, commands/reads, authorization,
   canonical target rechecks and closed results with service/security tests. No
   router/UI or foreign persistence access.
3. **Transport/UI:** request composition, thin authenticated routes and one
   contextual Project control panel with API/frontend tests. No graph expansion.
4. **Final evidence:** focused/adjacent/full regression, migration, scope and
   final governance evidence only after all prior batches are accepted.

Each batch requires an exact manifest, independent review and Human acceptance.
Stop for an accepted-contract conflict, foreign persistence access, security
leak, or PATCH-048 requirement.

## Focused Batch 3 reconciliation — 2026-08-24

`B3-CRIT-01` does not reorder the plan or reopen accepted Batches 1–2. The
remaining application/integration work must implement Change/Impact against
only the six reconciled UUID target kinds: Activity, Milestone, Deliverable,
Deliverable Revision, Evidence and Supporting File. Its manifest may include
the minimum existing PATCH-047 contract surfaces required to remove
`foundation`, add Deliverable Revision owner-selector context, and implement
target-specific canonical application adapters and focused tests.

No Foundation adapter, identity mapping, migration change, generic resolver,
foreign persistence access, transport/UI, or PATCH-048 work is planned. Batch
3 must stop if any listed canonical application response cannot prove exact
identity and trusted scope without a foreign repository read. Transport/UI and
final-evidence sequencing remain unchanged.
