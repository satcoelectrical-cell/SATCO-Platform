# PATCH-047 B3 Target Identity Reconciliation

## Preserved implementation-time finding

`B3-CRIT-01` — **initial status: BLOCKING / CRITICAL.** Batch 3 correctly
stopped before manifest creation because accepted IDS-047 declared
`foundation` to be a UUID Change Impact target while canonical Project
Foundation has no independent UUID. No Batch 3 file was created, no foreign
persistence was accessed, and no identity was invented.

## Repository-grounded finding

Architecture/EDS/IDS-044 and the implemented Foundation root agree:
`project_foundations.project_id INTEGER` is both primary key and canonical
selector. Foundation is one-to-one subordinate Project state, not an
independently addressable aggregate. `ProjectFoundationService.get(project_id,
actor)` can authorize and return exactly one established Foundation, but it
cannot translate a nonexistent Foundation UUID.

The UUID-only target abstraction was over-broad only because it included a
domain without UUID identity. Activity, Milestone, Deliverable, Deliverable
Revision, Evidence and Supporting File do own UUID identities. Activity and
Milestone are exactly selectable from the authorized bounded Execution Plan
application response. Deliverable has exact get; its Revision is exactly
selectable from protected history. Evidence and Supporting File have exact
authorized reads.

## Options evaluated

| Option | Identity/authority result | Persistence and compatibility | Decision |
|---|---|---|---|
| A — Project target plus typed Foundation aspect | Semantically sound, but introduces a Project selector/aspect contract not accepted in V1 | Requires heterogeneous/int selector or additional typed state | Defer |
| B — typed Project/Foundation selector by `project_id` | Preserves PATCH-044 identity but makes targets heterogeneous | Requires contract and persistence redesign after accepted Batch 1 | Defer |
| C — new Foundation UUID | Artificial identity without PATCH-044 product justification; risks authority theft | Requires PATCH-044 and migration redesign | Rejected |
| D — narrow to canonically addressable UUID targets | Preserves every owning aggregate and current authorization boundary | Existing UUID persistence remains coherent; no data rewrite | Selected |

Option D is the smallest semantically correct resolution. A Foundation-affecting
change remains a Project-scoped Human-authored Change. It needs no independent
Impact child merely to repeat Project scope. Typed Project/Foundation aspects
may be governed later if product evidence requires them.

Across the required criteria, A and B preserve canonical identity and could be
authorized through the Project/Foundation application boundary, but both add a
new heterogeneous selector, persistence representation and disclosure contract;
that is backward-incompatible with accepted Batch 1 and prematurely consumes a
PATCH-048 design choice. C has the highest complexity and risk: it changes
PATCH-044 aggregate semantics solely to satisfy PATCH-047's shape. D preserves
aggregate authority, current application authorization, protected
non-disclosure and the existing database shape; because Batch 3 never started,
the narrowing removes no persisted capability or legacy data. It does not block
future Engineering Intelligence: a later governed Project-aspect model can be
added from product requirements rather than an artificial identity.

## PATCH-044 impact assessment

No PATCH-044 amendment is required. Its Project-owned Foundation identity,
authorization, lifecycle and persistence remain authoritative and unchanged.
The correction is wholly within PATCH-047's target model.

## Canonical and security consequences

All supported target resolution remains application-only, target-specific,
same-Organization/same-Project and Workspace-compatible. Unsupported kinds are
invalid without a canonical call. Missing/denied or mismatched supported
targets are protected; dependency failures are unavailable. No result leaks a
candidate, count, ordinal, target identity or internal exception. Links remain
non-owning and non-mutating.

## Resolution and chronology

Focused Architecture, EDS, IDS and Plan amendments were independently
re-reviewed with Critical: 0 and Major: 0 and accepted under standing Human
governance authority. The focused Batch 3 IRR prerequisite is PASS.

`B3-CRIT-01` — **RESOLVED.** Batch 3 is eligible for manifest preparation only.
Batch 3 implementation, Batch 4 and PATCH-048 remain unauthorized/not started.
