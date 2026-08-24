# PATCH-045 — Engineering Execution Plan, Activities & Milestones

## Document control

| Field | Value |
|---|---|
| Status | DONE / CLOSED |
| Architecture / QG-M1 | PASS / ACCEPTED |
| EDS-045 | ACCEPTED / COMPLETE |
| IDS-045 | ACCEPTED / COMPLETE |
| Implementation authority | COMPLETE — delivery not yet granted |
| Registered after | PATCH-044 DONE / CLOSED |

## Delivery and closure

- QG-M1: PASS; Human QG-11: PASS; QG-12 bounded delivery: PASS.
- Batches 1–4: ACCEPTED / COMPLETE; no unresolved Critical or Major finding.
- Delivery commit: `e9e5f29775d727f20a35bfaba7ff3f914c264925`.
- Remote verification: PASS; divergence after delivery: `0/0`.
- PATCH-046 remains unregistered. All deferred boundaries remain deferred.

## Purpose

PATCH-045 turns the Project Foundation into a bounded, human-governed
Engineering Execution Plan. It supplies engineering-specific activities,
milestones, dependency and blocker visibility, truthful derived progress and
completion basis without becoming a generic task manager, schedule, workflow
engine or Project lifecycle replacement.

## Accepted architecture boundary

- One Project-owned Engineering Execution Plan root exists at most once for a
  Project and belongs to the same immutable Organization.
- The Plan owns plan configuration/version history, activities, milestones,
  dependency relations and execution-history facts. Project continues to own
  identity, Customer, Organization, status, manual legacy progress and the
  PATCH-044 Foundation; Workspace continues to own discipline-local context.
- Activities are bounded engineering work records, not generic tasks. Their
  closed execution standing is `planned`, `ready`, `in_progress`, `blocked`,
  `completed` or `cancelled`; authoritative change requires an authorized
  Human, expected version and rationale. Completion requires a recorded
  Human completion basis.
- Milestones are non-actionable engineering checkpoints with a Human-authored
  completion basis. Their achieved state is derived only from their linked
  activities' current completion facts; they are not independent tasks.
- Dependencies are directed, same-Project activity-to-activity relations and
  must be acyclic. A blocked activity stores only bounded local blocker
  wording; it neither creates nor substitutes for a future Risk/Issue record.
- Execution progress is derived from current non-cancelled activities and is
  returned as a separate explainable execution value. PATCH-045 does not write
  the existing Project `progress`, complete the Project, approve deliverables
  or make schedule/contractual claims.
- Plan structural revisions are append-only snapshots. Activity state history
  is append-only. PostgreSQL tenant, dependency, immutability and transition
  guards are authoritative.

## Authority and security

Actor and Organization are server-derived. Read authority follows current
Project visibility. Mutation authority follows current Project update
authority: Organization admin, Project owner or primary assignee. Every
mutation carries a bounded Human rationale and expected version. Project
Foundation must be established before a Plan can be established; completed or
cancelled Projects are read-only. Protected outcomes expose only their closed
discriminator and authorization occurs before existence, activity, milestone,
blocker, dependency, count or progress disclosure.

## User experience

The Project detail experience will receive an accessible, responsive,
real-data-only Execution Plan surface: truthful empty state, plan purpose,
activities, milestones, blockers, dependencies, derived progress and explicit
Human actions. Canonical identities are selected from authorized context or
hidden; no raw tenant/source identifier entry is exposed. New UI remains
English, responsive and direction-neutral/RTL-safe without implementing the
future localization capability.

## Explicit exclusions

No PATCH-046+ behavior: deliverables/document control, risks/issues/decisions,
change control, procurement, HR/resource scheduling, generic PM/BPM, Gantt or
contractual schedule, FAT/SAT, Wizard, Engineering Health, notifications,
semantic/vector search, autonomous AI, AI approval, localization completion,
frontend fixture data or PATCH-046 registration.

## Dependencies

PATCH-044 Project/Foundation, ADR-011 Project core, ADR-014 Workspace and
execution-plan boundary, ADR-022 Project Organization ownership, PATCH-025
trusted Organization context, PATCH-041 membership administration, the shared
AuditLog pattern and sole current Alembic head `e04400000001`.

## Registration basis

The Human-frozen Commercial V1 roadmap records PATCH-045 as the next candidate.
Mixed registry files contain unrelated local changes, so this standalone
record is append-only and does not rewrite those hunks. PATCH-046 is not
registered by this record.
