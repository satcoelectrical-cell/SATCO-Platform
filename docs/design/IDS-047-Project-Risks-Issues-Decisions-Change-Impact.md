# IDS-047 — Project Risks, Issues, Decisions & Change Impact

## Closed contracts

`Risk|Issue|Decision|Change` requests contain trusted `actor`, Project id,
optional Workspace id, bounded text, rationale, expected version and UUID
idempotency key. Read/mutation unions are `success | protected_not_found |
invalid_request | version_conflict | idempotency_conflict | unavailable`;
all non-success payloads are empty. Links use closed target kinds
`foundation|activity|milestone|deliverable|deliverable_revision|evidence|supporting_file`.

Risk standing is `open|treated|accepted|closed`; Issue standing is
`open|resolved|closed`; Decision standing is `draft|accepted|superseded`; Change
standing is `recorded|confirmed|withdrawn`; impact standing is
`potential|confirmed`. Reopen, acceptance, confirmation, closure and explicit
supersession requests require expected version and Human rationale. A successor
does not supersede by creation. Decisions and Change facts are append-only;
corrections make a new row and retain a zero-or-one predecessor link.

## Persistence and invariants

Each root table has UUID PK, Organization/Project/Workspace FK, standing,
version, actor/timestamps and current facts; append-only history, idempotency
and outbox tables are scoped likewise. A `project_change_impacts` table is
unique on Change plus target kind/id and stores potential/confirmed standing.
DB constraints enforce same root scope, bounded enums, immutable history and
expected-version update. The service validates every target through the owning
Foundation, Execution, Deliverable, Evidence or Supporting File application
boundary before persistence and disclosure; no foreign repository/Session is
permitted. The migration parent is `e04600000001`; no backfill.

Each mutation reserves a scoped idempotency key before the final Project and
target reauthorization, stages root/history/Audit/outbox/replay facts in one
UoW, checks expected version and commits once. Duplicate or supersession races
yield one winner; fingerprint mismatch is an idempotency conflict. Failure
rolls back primary facts; bounded rejection Audit is isolated afterwards.

Transport obtains trusted actor/Organization context only through the existing
request composition root and delegates to an application service. The Project
UI consumes closed results only; it carries no trusted IDs, authority or
derived hidden counts.

## Verification

Tests must prove state transitions, cross-Organization protection, no blocker
mutation, version/idempotency races, Audit/outbox rollback, target
reauthorization, migration downgrade/re-upgrade, UI no-fake-data and exact
route surface.

## Focused target-contract reconciliation — 2026-08-24

This section supersedes only the earlier inclusion of `foundation` and the
earlier generic Foundation target-validation statement. It preserves all other
accepted IDS contracts and records `B3-CRIT-01` rather than rewriting it.

### Closed selector and persistence representation

`ImpactTargetKind` is exactly `activity | milestone | deliverable |
deliverable_revision | evidence | supporting_file`. `ImpactCommand.target_id`
remains UUID and is interpreted only as the identity type owned by the selected
kind. This enum also closes every other PATCH-047 typed target link;
`foundation` and `project` are rejected before any canonical call.

`project_change_impacts.target_kind VARCHAR(32)` and `target_id UUID` remain
coherent for all supported kinds. Uniqueness remains `(change_id, target_kind,
target_id)`. No migration shape, existing root/history/idempotency/outbox
contract, or accepted Batch 1/2 behavior changes. Batch 3 must align the closed
schema/enum and application validation with this narrowed set; it must not add
a Foundation mapping table, synthetic UUID, generic selector JSON, or foreign
FK authority. No Foundation impact rows exist because target integration has
not started and the migration performed no backfill.

### Exact canonical validation dispatch

After Project/Change authorization and idempotency reservation, the final
target recheck immediately before staging is exactly:

| Kind | Canonical application call | Exact authorized selection |
|---|---|---|
| `activity` | `EngineeringExecutionPlanService.get(project_id, actor)` | one matching `ExecutionActivityDTO.id` in the bounded established-plan response |
| `milestone` | `EngineeringExecutionPlanService.get(project_id, actor)` | one matching `ExecutionMilestoneDTO.id` in the bounded established-plan response |
| `deliverable` | `EngineeringDeliverableService.get(project_id, deliverable_id, actor)` | returned `DeliverableDTO.id == target_id` |
| `deliverable_revision` | `EngineeringDeliverableService.history(project_id, deliverable_id, actor)` using the owning deliverable context supplied by the command | exactly one returned `DeliverableRevisionDTO.id == target_id`; no partial history is accepted |
| `evidence` | `EvidenceService.get(evidence_id, actor)` | returned identity equals target and response Project/Organization scope matches |
| `supporting_file` | `SupportingFileService.get_metadata(actor_id, trusted scope, asset_id)` | returned asset identity and Organization/Project/Workspace equal the trusted selector context |

The Deliverable Revision command therefore carries its owning
`deliverable_id: UUID` as required selector context in addition to
`target_id`; this context is verified against the canonical history response
and is not a second target identity. Activity/Milestone selection uses a single
authorized bounded plan response, not Execution repositories. All dispatches
use trusted actor/Organization and explicit Project; Workspace selector context
is untrusted until it equals the authorized canonical response.

Exactly one canonical response may be used per target validation. No target is
persisted or disclosed unless one exact authorized match is returned and its
Organization/Project/Workspace intersection is valid. Zero or multiple exact
matches, unavailable/non-established canonical state, malformed response, or
scope mismatch fail closed. Unsupported kind yields payload-free
`invalid_request`; missing/denied/scope-mismatched supported target yields
payload-free `protected_not_found`; dependency failure yields payload-free
`unavailable`. No target fields or candidate counts accompany failure.

### Foundation and Project handling

Project Foundation is selected canonically by integer `project_id` and is not
an independently addressable aggregate. PATCH-047 does not persist it as an
Impact target. A Foundation-affecting change is represented by the enclosing
Project-scoped Change's bounded Human statement/rationale; this conveys no
separate link or Foundation disclosure. The existing Project authorization is
still final-rechecked for every Change operation. Typed affected-aspect
metadata or heterogeneous selectors require later governance.

### Reconciled verification obligations

Focused tests must reject `foundation`, `project`, unknown, malformed, missing,
denied and cross-scope targets without disclosure; prove exact selection for
all six supported kinds through real canonical application services; prove
bounded Activity/Milestone response selection and exact Deliverable Revision
owner/revision matching; prohibit canonical repositories/ORM/Session/UoW
imports; and preserve all accepted Batch 1/2 domain, persistence, transaction,
Audit, outbox and idempotency evidence.
