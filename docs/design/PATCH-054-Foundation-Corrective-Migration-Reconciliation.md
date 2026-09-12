# PATCH-054 Foundation Corrective Migration Reconciliation

Status: GOVERNED BOUNDED RECONCILIATION IMPLEMENTED

Baseline commit: `fa14af7cc8c04caa9401812fb9d5f71e8e91e001`

Existing foundation migration: `e05400000001` (immutable)

Corrective migration: `e05400000002`

Corrective parent: `e05400000001`

## Decision

The implementation gap is physical migration partitioning only. ADR-027,
EDS-054, and IDS-054 semantics remain unchanged and require no reopening.
Implementation Plan-054 requires this append-only reconciliation because its
single original foundation migration did not grant the narrow Batch-2 runtime
operations, protect source/assertion/verification history, or enforce the
accepted 32-assertion ceiling.

The accepted physical sequence is now:

```text
e05400000001 (Foundation Migration A; immutable)
  -> e05400000002 (PATCH-054 Foundation Corrective Migration)
  -> future Batch-4 Technical Report integration migration (unassigned)
```

`e05400000002` is not the governance-semantic “Migration 2” assigned to
Batch 4. It is a prerequisite correction that completes the already accepted
standards foundation before Batch 2 may resume.

## Exact bounded corrective scope

- Narrow runtime column/table privileges for source snapshots, assertions,
  and verification events; installer remains denied.
- Fixed-search-path, non-public trigger functions enforcing immutable source
  snapshots, immutable assertion canonical meaning, and immutable verification
  history.
- Transaction-serialized enforcement of at most 32 assertions per snapshot.
- Existing accepted assertion/source checks and tenant/project/snapshot
  consistency constraints needed by that enforcement boundary.
- A retained-data downgrade guard; empty-schema downgrade returns exactly to
  `e05400000001`.

No Batch-2 provider, retrieval, object-store, handle, assertion service/API, or
vector behavior is implemented. No Project applicability, package integration,
Technical Report provenance, legacy guard, AI, frontend, PATCH-053 adapter, or
PATCH-055+ work is included.

## Reopen disposition

- ADR reopen required: NO
- EDS reopen required: NO
- IDS reopen required: NO
- Implementation Plan reconciliation required: YES — satisfied by this
  append-only record; accepted Plan history is not rewritten.

Batch 2 remains stopped pending Human acceptance of this reconciliation and
corrective-migration evidence. Batch 3+, the future Batch-4 Report migration,
and PATCH-055+ remain not started and not authorized.
