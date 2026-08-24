# EDS-045 — Engineering Execution Plan, Activities & Milestones

## 1. Status and authority

**ACCEPTED / COMPLETE.** Applies Architecture-045 only. Exact schemas, table
DDL, ports, serialization and route mechanics are delegated to IDS-045.

## 2. Canonical root and availability

An authorized current Project has zero or one current Engineering Execution
Plan. Absence returns successful `plan_not_established`, never a synthetic
empty plan/progress. First establishment requires an established PATCH-044
Foundation, non-terminal Project, expected Plan version `0` and a 1–2,000
character Human rationale. It creates the root at version 1 plus an immutable
empty structural revision. The Plan has no competing Project identity and
copies its Organization solely for tenant enforcement.

The root contains no alternate Project purpose, scope, stage, completion
criteria, Project status or manual Project progress. It stores only bounded
execution-plan configuration/history.

## 3. Activity contract

A Plan has 0–200 Activities. Creation/update uses a bounded Human rationale,
the expected Plan version, and (for update) expected Activity version. Fields:

| Field | Rule |
|---|---|
| identity | server UUID, immutable |
| title | normalized 1–200, unique case-insensitively in a Plan |
| description | optional normalized 1–2,000 |
| ordinal | unique contiguous `0..n-1` |
| workspace | optional current Workspace of same Project/Organization |
| responsible Human | optional Project owner or primary assignee only; it grants no authority |
| target date | optional date, planning aid only |
| completion basis | normalized 1–2,000 Human-authored statement |
| standing | `planned`, `ready`, `in_progress`, `blocked`, `completed`, `cancelled` |

Standing begins `planned`. `ready`/`in_progress`/`completed` require every
incoming dependency to be completed or cancelled; `blocked` requires a 1–2,000
character local blocker rationale; `completed` requires a 1–2,000 character
Human completion rationale; `cancelled` requires a Human rationale and is
terminal. Returning from `blocked` requires rationale and may target only its
remembered prior executable standing. A completion attestation is an execution
fact, not deliverable approval, Project completion, safety certification or AI
authority. Every standing change appends immutable Activity history.

## 4. Milestone contract

A Plan has 0–50 Milestones. A Milestone is a checkpoint, never an activity or
generic task. It has immutable UUID, title (1–200, unique case-insensitively),
completion basis (1–2,000), optional target date, ordinal and an ordered
0–200 distinct Activity link set. Structural create/update requires expected
Plan version and Human rationale and produces a Plan revision. Its read-only
standing is derived: `achieved` only when every linked Activity is completed;
`blocked` when a linked Activity is blocked; otherwise `not_ready`.

## 5. Dependency, blocker, completion and progress

The entire directed edge set is replaced atomically by an authorized Human
command with expected Plan version/rationale. It contains at most 500 edges,
is same-Plan, has no self/duplicate edge and is acyclic. The repository and DB
must reject a cycle. Local Activity blocker text is not a Risk/Issue/Decision
and no foreign risk identity is introduced.

Derived execution progress is `floor(100 * completed / non_cancelled)`; an
empty denominator exposes `0`, with numerator/denominator. It is calculated
from current Activity facts, not user-entered, and never writes Project
`progress`. Activity/milestone facts may inform future completion work but do
not satisfy Foundation criteria, transition Foundation stage or complete the
Project.

## 6. Authorization and protected results

The trusted actor and Organization are server-derived. Project lookup within
Organization precedes all Plan disclosure. Current Project read authority may
read; Organization admin, Project owner and primary assignee mutate. Terminal
Projects are Plan read-only. Workspace references are independently checked
against the same Project/Organization. A responsible Human must currently be
the Project owner or primary assignee; no broad member picker or new role is
introduced.

Every command carries a rationale; client actor, Organization and authority
are ignored. Results are closed: `success`, `protected_not_found`,
`invalid_request`, `version_conflict`, `idempotency_conflict`, `unavailable`.
All non-success protected results are payload-free. Unauthorized state never
discloses Plan existence, counts, activity/milestone identity, dependency,
blocker, progress or source detail.

## 7. Reliability, idempotency and audit

Structural mutations and activity transitions use one request-scoped UoW,
same database Session, expected versions, deterministic UUID locking and no
repository commit. `Idempotency-Key` is required for mutations; the
Organization/actor/operation/request-fingerprint-key binding permits one
bounded replay of the original safe success result, rejects a fingerprint
mismatch and reauthorizes before replay. The stored replay payload contains
only operation, IDs, versions, standing and schema version—no rationale,
blocker, description or completion-basis plaintext.

The root/revision/activities/milestones/links/dependencies/history,
idempotency record and shared AuditLog persist atomically. Audit stores action,
Project/root UUID, actor, versions and bounded changed-field categories only.
No outbox is required because V1 has no asynchronous consumer. Any failure
rolls back all primary records; no post-rollback rejection Audit is required
by existing Project Foundation patterns.

## 8. Persistence and historical rules

The migration creates only empty Plan-subordinate tables. Database constraints
and owned trigger/functions enforce Organization/Project equality, valid
enums/lengths, immutable identity/history, terminal standing protection,
same-Plan links/dependencies, dependency acyclicity, unique active root and
revision sequencing. Runtime uses the restricted role; schema objects belong
to `satco`. Direct SQL cannot write protected history or alter functions.

Every structural mutation stores a canonical deterministic configuration JSON
revision containing activity/milestone configuration, links and dependency
edges, ordered by ordinals/UUIDs and excluding mutable execution standing.
This preserves ADR-014 immutable plan-version meaning without treating an
Activity fact as a rewritten plan definition.

## 9. UX

The authenticated Project detail UI provides a truthful empty Plan action,
plan state/progress, activity hierarchy/actions, milestone checkpoint view,
dependency/blocker visibility and explicit Human rationale forms. It exposes
no raw actor, Organization, Workspace or Activity ID entry; responsibility is
chosen only from the visible Project owner/primary-assignee context and
Workspace from authorized current Project Workspaces. UI strings are local to
components, layout uses logical/flexible CSS, dates are structured ISO values,
and all states are accessible/responsive. Production uses real API responses
only.

## 10. Deferred boundary

No deliverables/document control, risk/issue/decision authority, schedule/Gantt,
resource or HR management, generic task/BPM engine, notifications, AI-created
or AI-approved execution, Project completion, FAT/SAT, Wizard, Engineering
Health, procurement, semantic/vector work or localization rollout.
