# IDS-045 — Engineering Execution Plan, Activities & Milestones

## 1. Status

**ACCEPTED / COMPLETE.** This implementation design realizes accepted
PATCH-045/Architecture-045/EDS-045. It creates no PATCH-046+ capability.

## 2. Closed domain contracts

### Value sets

- `ExecutionActivityStanding`: `planned`, `ready`, `in_progress`, `blocked`,
  `completed`, `cancelled`.
- `ExecutionMilestoneStanding`: `not_ready`, `blocked`, `achieved` (read-only).
- `ExecutionOperation`: `establish_plan`, `create_activity`,
  `update_activity`, `transition_activity`, `replace_dependencies`,
  `create_milestone`, `update_milestone`.

`ExecutionActor(actor_id: int, organization_id: UUID)` is trusted only.
`ExecutionScope(organization_id, project_id)` has no client actor/tenant field.
All rationale/completion/blocker text normalizes trimmed Unicode line endings
and applies EDS length bounds. UUID, date, duplicate, ordinal and exact
collection bounds fail as `invalid_request`.

### Read DTOs

`ExecutionPlanAbsent(project_id, availability='plan_not_established')` and
`ExecutionPlanEstablished(project_id, plan_id, version, activities,
milestones, dependencies, progress)` form `ExecutionPlanReadResult`.
Activities expose identity, title, optional description/workspace/responsible
display slot, ordinal, target date, completion basis, standing, version,
bounded blocker presence/text only to authorized Project readers and derived
dependency-ready status. Milestones expose identity/title/basis/target date,
ordinal, linked activity IDs only after that Plan is authorized, and derived
standing. Progress exposes exactly `completed_count`, `eligible_count` and
`percent`; no hidden totals exist.

### Mutation DTOs/results

Commands each include `expected_plan_version` where structural; activity update
and transition additionally include `expected_activity_version`.

| Command | Required body beyond version/rationale | Success result |
|---|---|---|
| establish plan | `expected_plan_version=0` | Plan ID/version |
| create activity | title, description?, workspace?, responsible?, ordinal, target_date?, completion_basis | Plan version + activity |
| update activity | exact mutable fields | Plan/activity version + activity |
| transition activity | target standing, completion/blocker rationale when required | activity version + standing |
| replace dependencies | canonical ordered unique `(predecessor_id, dependent_id)` list | Plan version + edge count |
| create milestone | title, basis, target date?, ordinal, ordered activity IDs | Plan version + milestone |
| update milestone | exact mutable fields/ordered activity IDs | Plan version + milestone |

Each outward command result is a closed union of exactly `success`,
`protected_not_found`, `invalid_request`, `version_conflict`,
`idempotency_conflict`, `unavailable`. Only success carries data. No result
maps a version conflict to protected absence.

## 3. Persistence contract

Migration `e04500000001` has parent `e04400000001` and creates:

| Table | Canonical contents / key guards |
|---|---|
| `engineering_execution_plans` | UUID PK; unique `project_id`; Organization FK; root version >=1; established/updated actor/time |
| `engineering_execution_plan_revisions` | UUID PK; Plan/Organization; unique `(plan_id, revision_number)`; immutable canonical JSON config and SHA-256 digest; actor/rationale/time |
| `engineering_execution_activities` | UUID PK; Plan/Project/Organization; title/ordinal uniqueness; optional Workspace/responsible; standing/version; current blocker and blocked-return standing; completion basis; timestamps |
| `engineering_execution_activity_history` | UUID PK; Activity/Plan/Organization; unique `(activity_id, activity_version)`; from/to standing, bounded rationale, actor/time; append-only |
| `engineering_execution_milestones` | UUID PK; Plan/Project/Organization; title/ordinal uniqueness; basis/target date; timestamps |
| `engineering_execution_milestone_activities` | composite milestone/activity PK; same Plan/Organization/Project trigger and unique ordinal |
| `engineering_execution_dependencies` | UUID PK; Plan/Organization; unique predecessor/dependent; no self; same Plan trigger plus recursive cycle guard |
| `engineering_execution_idempotency` | UUID PK; Organization/actor/operation/key unique; fingerprint digest; bounded <=1KiB JSON replay; created time |

`Project` FK is RESTRICT. Plan/child Organization FKs are RESTRICT. Activity
Workspace FK is RESTRICT and a trigger checks Workspace's Project/Organization.
Responsible Human may be only `projects.owner_id` or `primary_assignee_id` at
write time; a trigger enforces the relation. A Plan mutation stored procedure
or trigger validates parent Project/Organization and Foundation existence.

Database functions owned by `satco` validate plan hierarchy, transition
standing, dependency acyclicity, milestones links and revision digest/JSON
shape. History/revision rows reject UPDATE/DELETE. Runtime `satco_runtime` has
DML only on operational tables and EXECUTE only to owned validation functions;
it cannot alter table/trigger/function or write history except through the
valid transition path. Model metadata mirrors widths, nullability, indexes,
FKs, checks and named constraints.

## 4. Serialization/revision/idempotency

`canonical_plan_config_v1` is UTF-8 JSON, sorted keys, compact separators and
sorted Activity/Milestone/edge lists by `(ordinal,id)` or UUID edge pair. It
contains structural fields/links only, never Activity current standing,
blocker, completion rationale, source content, user names or Audit details.
Digest is lowercase SHA-256 hex. A revision's JSON/digest is never recomputed
after insert.

Mutation requires `Idempotency-Key` UUID. Fingerprint is SHA-256 of operation,
trusted scope and canonical command JSON. Stored replay payload has schema
`execution.idempotency.v1`, operation, result discriminator, Plan ID, root
version, optional Activity/Milestone UUID, optional standing and no plaintext
rationale/basis/description/blocker. Current authority is rechecked before a
matching replay. Same key/fingerprint returns stable original success after
later transitions; differing fingerprint returns `idempotency_conflict`.

## 5. Ports/UoW/application

`ExecutionPlanAuthorizationPort` provides Project read/mutate checks, terminal
status, Project owner/assignee and same-Project Workspace validation without
transport policy. `ProjectFoundationReadPort` calls the accepted Foundation
application boundary to determine only established/non-terminal eligibility;
it never accesses Foundation repositories/Session. `ExecutionPlanRepository`
is no-commit and owns Plan persistence/locks/config snapshots/query. The
`SqlAlchemyExecutionPlanUnitOfWork` owns exactly one Session, repository and
shared Audit staging; commit/rollback is application-owned.

`EngineeringExecutionPlanService` orders: trusted scope → parent read/mutate
authorization → idempotency reservation → final Foundation/Project/Workspace/
authority recheck → deterministic Plan/activity UUID locks → expected-version
check → mutation/revision/history/Audit/replay staging → one commit. Integrity
errors map deterministically to version conflict or invalid request; unknown
dependency failures map to payload-free unavailable. Repositories never call
commit and transport creates neither Session/repository/UoW/policy.

## 6. Routes and frontend contract

Router prefix is `/projects/{project_id}/execution-plan`; exactly eight routes:
GET Plan; PUT establish; POST Activity; PUT Activity; POST Activity transition;
PUT dependencies; POST Milestone; PUT Milestone. All require authentication
and carry only accepted DTO fields. HTTP maps protected to 404, invalid to 422,
version/idempotency conflict to 409 and unavailable to 503; application payload
does not expose protected data.

Request-scoped composition builds the Plan service, UoW factory, Project
authorization adapter and Foundation read adapter outside router. The frontend
adds one `EngineeringExecutionPlanPanel` to Project detail and typed client
calls. It renders real authorized results; no raw IDs, fixtures, client-derived
actor/Organization, optimistic fake progress or AI action. Controls use labels,
live status, visible rationale textareas, logical CSS properties and responsive
stacking.

## 7. Verification matrix

- contracts: every enum/union/bound/normalization/closed outcome;
- migration: head, upgrade/downgrade/re-upgrade, role grants, immutable
  revision/history, direct-SQL tenant/dependency/cycle/transition attempts;
- service: Foundation prerequisite, terminal Project, auth/protected results,
  idempotency/replay/conflict, same-UoW Audit/rollback, version/concurrency;
- integration: Project/Workspace/Foundation application-boundary calls only;
- API: all eight routes, auth/tenant injection/protected payloads;
- frontend: empty/loading/protected/error/success, accessibility, responsive,
  rationale, source-free controls and real-data-only behavior;
- regressions: Project/Foundation/Workspace/Audit and full final suites.

## 8. Deferred

No generic Task entity, schedule, Gantt, resource allocation, critical path,
deliverable, Risk/Issue/Decision, completion execution, AI authority,
notification, localization rollout, semantic search or PATCH-046 registration.
