# PATCH-054 Project Applicability Foundation Schema Reconciliation

Status: **GOVERNED BOUNDED SCHEMA CORRECTION IMPLEMENTED**

Baseline commit: `fa384b85e58c5b504b76f732be07382ef51d2eaf`

Protected migrations retained unchanged: `e05400000001`, `e05400000002`,
`e05400000003`

Additive corrective migration: `e05400000004`

Corrective parent: `e05400000003`

## Confirmed schema gap

The immutable original foundation created only the preliminary applicability
row (`edition`, `role`, `status`, predecessor/version, actor/time).  IDS-054
section 7.5 and EDS-054 require the accepted Project applicability lifecycle
to retain Human provenance/rationale, attributable origin, advisory-candidate
provenance, mandatory-basis evidence, a digest, explicit current/successor
state, and predecessor compare-and-set evidence.  They also require database
enforcement of Project/Organization consistency, current Human declaration
heads, immutable history, the 64-head limit, and narrow runtime grants.

This is a physical foundation partitioning gap, not an ADR, EDS, or IDS
semantic gap.  The Implementation Plan reconciliation is append-only through
this record; the untracked accepted Plan artifact is deliberately not rewritten.

## Exact bounded correction

`e05400000004` is a single linear successor that converts the empty pre-Batch-3
applicability table to the exact IDS-054 7.5 shape, preserving the repository's
actual integer `projects.id` and `users.id` foreign-key types.  It adds only:

- candidate designation and attributable package-candidate reference;
- Human rationale code/text and origin reference;
- mandatory source kind/reference/digest;
- expected predecessor revision, successor, current flag, revision, and
  applicability digest;
- exact status/role, candidate, declaration, mandatory, digest, tenant/Project,
  current-head, lineage, immutable-history, and 64-current-head enforcement;
- fixed-search-path non-public trigger functions and the narrow runtime
  `SELECT`, `INSERT`, and retirement-linkage update grants.

The accepted package candidate contract contains richer candidate metadata than
the exact IDS-054 table columns.  This correction deliberately persists only
the authorized `source_candidate_reference` at this layer; it does not invent
JSON, package, workspace, descriptor, or configuration columns.  Future
authorized Batch-3 orchestration remains responsible for constructing and
validating that reference from the exact package candidate contract.

The migration refuses a non-`e05400000003` predecessor and refuses a non-empty
pre-Batch-3 applicability table.  Its downgrade is permitted only while no
applicability history exists; it never deletes or rewrites retained history.

The accepted physical sequence is now:

```text
e05400000001 -> e05400000002 -> e05400000003 -> e05400000004
  -> future Batch-4 Technical Report integration migration (unassigned)
```

`e05400000004` is a foundation reconciliation, not the governance-semantic
Batch-3 or Batch-4 migration designation.

## Explicit exclusions and gate

No Batch-3 adapter, descriptor, package hook, application service, API route,
outbox behavior, candidate emission, Human declaration workflow, or regression
suite was implemented.  No Batch 4+, PATCH-055+, frontend, deployment, or push
is included.

- ADR reopen required: **NO**
- EDS reopen required: **NO**
- IDS reopen required: **NO**
- Implementation Plan reconciliation required: **YES — satisfied by this
  append-only reconciliation record**
- Historical migrations modified: **NO**
- Future Batch-3 implementation authorized by this record: **NO**
- Next gate: Human acceptance of this correction before any Batch-3 work
