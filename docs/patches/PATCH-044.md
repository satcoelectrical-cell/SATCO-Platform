# PATCH-044 — Project Definition, Scope, Inputs & Lifecycle Foundation

## Document control

| Field | Value |
|---|---|
| Status | DONE / CLOSED |
| Architecture / QG-M1 | PASS / ACCEPTED |
| EDS-044 | ACCEPTED / COMPLETE |
| IDS-044 | ACCEPTED / COMPLETE |
| Implementation Plan-044 | ACCEPTED / COMPLETE |
| IRR-044 | PASS |
| Implementation authority | BATCHES 1–4 EXECUTED / ACCEPTED / COMPLETE |
| Delivery / closure | PASS / COMPLETE — CLOSED |
| Registered after | PATCH-043 DONE / CLOSED |

## Purpose

SATCO currently represents canonical Project identity, Customer, Organization,
ownership, assignment, dates, status, progress and Engineering Workspaces, but
does not represent the governed engineering basis needed to explain what a
Project is, why it exists, what work is in or out of scope, which inputs are
required, whether those inputs are usable, which engineering stage is current,
or what bounded basis will later support completion.

PATCH-044 adds that foundation to the existing canonical Project. It does not
create a second Project aggregate or a generic project-management workflow.

## Accepted capability boundary

The V1 capability provides:

- a Project-owned definition containing purpose and engineering basis;
- ordered in-scope and out-of-scope statements;
- ordered bounded completion-basis criteria, without closeout execution;
- Project-owned required-input definitions with closed standing;
- satisfaction through an independently authorized canonical available
  Supporting File or current Evidence record in the same Project;
- a Project engineering-stage foundation and immutable transition history;
- derived target-stage readiness with explicit blockers;
- Human-authorized, rationale-bearing stage transitions;
- protected Project-foundation reads and mutations;
- a bounded, accessible and responsive Project Manager experience using only
  real API data.

Existing Projects remain valid. Absence of a Project foundation is reported as
`basis_not_established`; migration does not invent definition, scope, inputs,
readiness, stage completion or Human acceptance.

## Ownership and authority

Project remains the sole canonical owner of Project identity, tenant,
Customer, lifecycle and the new foundation. Foundation records are subordinate
Project-owned state. Engineering Workspace remains the operational discipline
aggregate and is not duplicated.

Supporting File and Evidence remain canonical in their owning capabilities.
An input stores only a governed reference to one exact authorized source; it
does not copy content or transfer ownership. Current source authorization and
standing are rechecked before disclosure, readiness use and transition.

Organization and actor are derived from authenticated server context. Project
tenant ownership is immutable and checked before existence or state
disclosure. Read authority follows the current canonical Project/Workspace
visibility boundary. Mutation authority follows existing Project update
authority: Organization admin, Project owner or Project primary assignee.
Scope assignment alone does not create authority.

## Lifecycle and readiness

Project status remains the existing canonical lifecycle (`new`,
`in_progress`, `on_hold`, `completed`, `cancelled`). The separate engineering
stage is exactly:

`definition -> preparation -> execution -> verification -> completion_readiness`

Adjacent backward movement is permitted through an explicit authorized Human
transition and rationale. Forward movement requires derived readiness. A
readiness result is advisory decision support; it never mutates stage. Project
`completed` and `cancelled` states are read-only for the foundation.

Required-input standing is exactly `missing`, `received`,
`clarification_required`, or `not_applicable`. Creation begins as `missing`.
`received` requires one exact canonical source. `not_applicable` and
`clarification_required` require a Human rationale. A received declaration
remains auditable, while loss of current source standing or authorization
blocks effective readiness and protects the source reference.

## Explicitly deferred

PATCH-045 Engineering Execution; PATCH-046 Deliverable Control; PATCH-047
Risks, Issues, Decisions and Change Impact; PATCH-048 Project Context/EKG;
PATCH-049 Completeness Intelligence; PATCH-050 Engineering Guidance;
PATCH-051–054 Procurement/Supply; PATCH-055 Engineering Health; PATCH-056 Cost;
PATCH-057 FAT/SAT execution; PATCH-058 Closeout; PATCH-059 Notifications;
PATCH-060 Wizard; PATCH-061 final Command Center composition; PATCH-062
Licensing; PATCH-063 remote qualification; PATCH-064 Proposal/Contract;
PATCH-065 n8n/website integration; tasks, milestones, schedules, generic BPM,
generic EDMS, AI-authored scope/readiness/transition, automatic stage changes,
and fake production evidence are not part of PATCH-044.

## Dependencies

- PATCH-018.1 / ADR-011 canonical Project core;
- PATCH-020 / ADR-014 Engineering Workspace ownership boundary;
- PATCH-025 trusted Organization context;
- ADR-022 immutable Project Organization ownership;
- PATCH-027 Evidence and PATCH-043 Supporting File application boundaries;
- PATCH-038 Customer-to-Project tenant invariant;
- PATCH-041 active Organization/User administration;
- current sole Alembic head `e04300000001`.

## Governance registration

The Human-frozen Commercial V1 roadmap after PATCH-043 assigns PATCH-044 this
exact capability and keeps PATCH-045 through PATCH-065 separate. The mixed
Roadmap and Governance registry files contain unrelated local edits, so this
standalone record is the authoritative bounded registration and does not
overwrite those hunks. PATCH-045 is not registered by this record.

## Post-delivery governance closure

- Batches 1–4: ACCEPTED / COMPLETE
- Independent Final Implementation Review: PASS
- QG-M1: PASS
- Human QG-11: PASS
- QG-12 bounded delivery: PASS
- Delivery commit: `ebfbecd58e100308d006f3e08032cd2e5ff87f65`
- Delivery remote verification: PASS; divergence `0/0`
- Critical/Major findings: all resolved; historical FAIL → remediation →
  re-review evidence preserved
- Deferred PATCH-045+ boundary: preserved
- Final status: **DONE / CLOSED**

This documentation-only closure conveys no PATCH-045 registration,
architecture, design, implementation or delivery authority. Commercial V1
Release Certification has not been performed.
