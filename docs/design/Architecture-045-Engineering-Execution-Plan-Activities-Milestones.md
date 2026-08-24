# Architecture-045 — Engineering Execution Plan, Activities & Milestones

## 1. Status

**ACCEPTED / COMPLETE.** This bounded architecture applies the accepted
Commercial V1 roadmap, ADR-011, ADR-013, ADR-014, ADR-022 and PATCH-044. It
authorizes EDS-045 only.

## 2. Repository discovery and ownership decision

The current `Project` owns identity, immutable Organization/Customer,
Project-status lifecycle and legacy manual `progress`. PATCH-044 added the
subordinate Foundation, which owns purpose, engineering basis, scope, required
inputs, completion-basis definitions and separate engineering stage/readiness.
Workspaces own discipline-local operational context. No canonical execution
activity, milestone or dependency model exists. Existing Project `progress`
cannot truthfully represent execution facts.

PATCH-045 introduces one Project-subordinate `EngineeringExecutionPlan` root.
It is not a second Project, a schedule, a Workspace, a deliverable register,
Risk/Issue aggregate or generic task board. The root owns plan configuration,
immutable configuration revisions, Activity and Milestone identities,
activity-dependency edges and append-only execution history. Its Organization
must equal its parent Project at every database and application boundary.

## 3. Plan, Activity and Milestone model

One current Plan may exist for each Project; no migration backfill occurs.
Absence reads as `plan_not_established`, not an inferred plan or zero progress.
Establishment requires an established PATCH-044 Foundation and an authorized
Human rationale. A structural plan change appends an immutable Plan revision;
prior revisions are historical explanation, not alternative current authority.

An Activity is an engineering-specific bounded unit of execution, containing
title, optional engineering description, optional Project Workspace context,
ordered ordinal, optional target date, optional active Organization-member
responsible Human, Human-authored completion basis and current standing. It
does not own a deliverable, document, risk, decision, resource allocation,
effort estimate or arbitrary percent.

Activity standing is exactly:

`planned -> ready -> in_progress -> completed`, with `blocked` available from
planned/ready/in_progress and return to the previous executable state only by
an explicit Human rationale; `cancelled` is terminal. Completion is permitted
only after dependencies are effectively completed or cancelled and carries a
bounded Human completion rationale. A blocker carries bounded local text only;
future PATCH-047 may independently link Risk/Issue authority without changing
this V1 model.

A Milestone is a non-actionable checkpoint with title, bounded completion
basis, optional target date and an ordered set of same-Plan Activity links.
Its display standing is derived: `not_ready`, `blocked`, or `achieved`.
Achievement follows all linked required activities being completed; a milestone
cannot be manually marked complete and cannot act as a generic task.

Dependencies are directed same-Plan Activity edges. Self-dependency, duplicate
edge, cross-tenant/project edge and a cycle are invalid. A dependency prevents
the dependent Activity from `ready`, `in_progress` or `completed` until its
predecessor is effectively completed. The V1 dependency graph has no critical
path, duration, schedule or resource optimization.

## 4. Completion and progress

Plan progress is derived at read time as completed non-cancelled Activities /
all non-cancelled Activities, rounded deterministically to a 0–100 integer;
the response also reports numerator and denominator. No Activity state silently
changes Project status, Project `progress`, Foundation stage, completion
criterion, deliverable acceptance or closeout. `completion_readiness` and
future Project completion may consume the facts later, but PATCH-045 makes no
such transition.

## 5. Authority, scope and disclosure

Trusted authentication supplies actor and Organization. Project must be loaded
within Organization before disclosure. Current Project read authority may see
the Plan. Existing Project mutation authority (admin, owner, primary assignee)
governs all Plan mutations. A responsible Human must be active in the same
Organization and, where Workspace is selected, be authorized under that
Workspace's current context; responsibility does not grant mutation authority.
Project terminal states are read-only. Closed results are `success`,
`protected_not_found`, `invalid_request`, `version_conflict` and `unavailable`.
Protected results contain no identity, count, dependency, blocker, milestone,
progress or denial detail.

## 6. Reliability, history and migration

PostgreSQL is authoritative. The root, revisions, activities, milestones,
links, dependencies, activity history and AuditLog are persisted in one
request-scoped UoW; repositories never commit. Expected root/activity versions
and deterministic locks provide one-winner mutation behavior. Database guards
enforce Organization/Project coherence, valid enum/length/date fields,
dependency uniqueness/cycle prohibition, immutable history and terminal
transition safety. The migration creates empty subordinate records only:
legacy Projects read `plan_not_established` and no Foundation/Project value is
invented. An outbox is not introduced because V1 has no asynchronous consumer;
adding one requires a separately governed need.

## 7. UX and extension seams

The Project detail UI receives one bounded Engineering Execution surface with
empty/loading/protected/error/success states, activity/milestone hierarchy,
dependency/blocker visibility, derived progress and rationale-bearing Human
actions. It uses real API data only, labels controls, preserves keyboard use,
does not require raw identifiers, stacks responsively and avoids
direction-dependent layout. Strings remain isolated in UI code; persisted
domain values are closed English-neutral identifiers.

PATCH-046 may attach deliverables; PATCH-047 may resolve blockers through
canonical Risk/Issue records; PATCH-048/049/050 may read execution facts as
context/advice. None gains ownership or is implemented here.

## 8. Architecture review conditions

This design preserves: Project and Foundation authority; one Project Plan;
immutable structural/execution history; explicit Human authority; derived
progress; advisory-only AI; no generic PM/schedule model; and all deferred
boundaries.
