# EDS-044 — Project Definition, Scope, Inputs & Lifecycle Foundation

## 1. Status and authority

**ACCEPTED / COMPLETE.** This EDS is limited to accepted Architecture-044.
Independent EDS Review is PASS and Human EDS Acceptance is recorded. Exact
persistence and transport mechanisms are delegated to IDS-044.

## 2. Canonical behavior

### 2.1 Foundation availability

Every current canonical Project may have zero or one Project Foundation. A
successful authorized read returns either:

- `basis_not_established`, containing Project identity and allowed action only;
  or
- `established`, containing the current versioned foundation.

Absence is not an error and carries no inferred stage, scope, inputs, readiness
or acceptance. First authorized definition update establishes the foundation at
stage `definition`, version 1, and records actor/time. The Project's existing
status and progress do not change.

### 2.2 Definition, scope and completion basis

An establishment/update command supplies:

- non-empty purpose, maximum 2,000 characters;
- non-empty engineering basis, maximum 5,000 characters;
- 1–50 unique ordered in-scope statements, each 1–1,000 characters;
- 0–50 unique ordered out-of-scope statements, each 1–1,000 characters;
- 1–50 unique ordered completion-basis criteria, each 1–1,000 characters;
- expected foundation version (`0` only for establishment);
- Human rationale, 1–2,000 characters.

Whitespace is trimmed and line endings normalized; technical meaning is never
summarized, translated or AI-authored. Ordinals are contiguous from zero.
Duplicates after normalization are invalid. The command atomically replaces
the definition-owned scope and criteria collection. It is allowed only while
Project status is `new`, `in_progress`, or `on_hold` and stage is `definition`
or `preparation`.

Completion criteria are definitions only. They have no satisfied, approved,
accepted or closeout state.

### 2.3 Required-input definition

Each input has server-generated UUID, Project/Organization, title (1–200),
optional description (maximum 2,000), unique contiguous ordinal, required-by
stage, standing, version, attribution and timestamps. A Project has at most 100
inputs. Title uniqueness is case-insensitive after trim within a Project.

Create requires title, description, required-by stage, ordinal, expected
foundation version and rationale. The input starts `missing`, version 1. Input
definition may be changed only while standing is `missing` or
`clarification_required`; title, description, due stage and ordinal changes
require expected input and foundation versions plus rationale. Reordering is a
single bounded operation that supplies every input identity exactly once.
Inputs are never hard-deleted in V1.

### 2.4 Required-input standing machine

Closed standing transitions are:

```text
missing -> received | clarification_required | not_applicable
clarification_required -> missing | received | not_applicable
received -> missing | clarification_required
not_applicable -> missing | clarification_required
```

Every transition requires expected input/foundation versions and Human
rationale. `received` additionally requires exactly one source reference;
other target standings require no source and atomically clear any prior current
source reference. A previous link remains represented in shared Audit but is
not a current satisfaction source.

`not_applicable` means an authorized Human has judged the defined expectation
not applicable; it is effective satisfaction for readiness. It is not deletion
or automatic inference. `clarification_required` and `missing` always block
applicable target-stage readiness.

### 2.5 Canonical source satisfaction

Source kind is exactly `supporting_file` or `evidence`.

For Supporting File, the exact source must be visible through the canonical
Supporting File application boundary, belong to the same Organization and
Project, optionally belong to a Workspace of that Project, and be `available`.
For Evidence, the exact source must be visible through the canonical Evidence
application boundary, belong to the same Organization and exact Project,
optionally belong to a Workspace of that Project, and be `current`.

Source version is captured with identity and optional Workspace at declaration.
No filename, bytes, source reference, supported fact or content is copied to
Project Foundation. Source selectors list only independently authorized
current sources. Client-supplied Organization is prohibited; raw source UUID
typing is not part of the frontend.

Current-source reauthorization occurs before source identity disclosure,
readiness evaluation and stage transition. A changed/withdrawn/non-current or
no-longer-authorized source yields a safe effective condition
`source_reauthorization_required`; it blocks readiness. The persisted Human
standing remains `received` until a Human changes it, preserving history.

### 2.6 Stage machine

Engineering stage is distinct from Project status:

```text
definition <-> preparation <-> execution <-> verification
           <-> (adjacent only) completion_readiness
```

The actual adjacency is linear; no skip is permitted. Forward transitions
require readiness for the target. Backward transitions require rationale and
authority but not readiness. Stage transition requires expected foundation
version. A same-stage request is invalid, not an idempotent transition.

Forward readiness is `ready` only when:

1. the foundation is established;
2. definition/scope/completion collections satisfy Section 2.2;
3. at least one required input exists;
4. every input whose required-by stage is at or before the target is either:
   - `not_applicable`; or
   - `received` with a currently authorized, exact-scope, eligible canonical
     source.

The read result exposes only authorized Project-owned blockers:
`definition_incomplete`, `scope_incomplete`, `completion_basis_incomplete`,
`required_inputs_not_defined`, `input_missing`, `input_clarification_required`,
or `input_source_reauthorization_required`. It may include the Project-owned
input UUID/title for an authorized Project reader, but never an unauthorized
source identity or denial reason. Readiness is computed on demand and is not a
persisted approval or score.

Stage transition performs source and authority rechecks after locking and
immediately before mutation. Success increments foundation version and writes
one immutable transition record with previous/new stage, actor, rationale and
timestamp in the same transaction.

### 2.7 Project status interaction

Foundation reads are allowed for visible Projects in any existing status.
Mutations are rejected for `completed` or `cancelled` Projects. `on_hold` does
not erase or fabricate stage readiness; authorized Humans may maintain the
basis and move stage while the Project is on hold. PATCH-044 never changes
Project status/progress or declares Project completion.

## 3. Authorization and disclosure

### 3.1 Trusted context

Actor and active Organization are derived from authenticated server context.
Project is resolved by `(organization_id, project_id)` before foundation access.
Workspace identity is never a tenant source.

### 3.2 Operation matrix

| Operation | Organization admin | Project owner | primary assignee | authorized Workspace participant |
|---|---:|---:|---:|---:|
| read foundation/readiness | yes | yes | yes | yes |
| list source candidates | yes, subject to source policy | yes, subject to source policy | yes, subject to source policy | only exact authorized Workspace/source |
| establish/edit definition/scope/criteria | yes | yes | yes | no |
| create/edit/reorder/transition input | yes | yes | yes | no |
| transition Project engineering stage | yes | yes | yes | no |

User and membership must be active. Legacy unowned-Project update behavior is
not extended to this new governed foundation; such Projects require admin or
primary-assignee mutation until an owner is assigned.

### 3.3 Closed outcomes

Application results are closed:

- operation-specific `success`;
- payload-free `protected_not_found` for missing, cross-tenant, forbidden or
  independently unauthorized source;
- payload-free `invalid_request` for malformed/invalid state/transition;
- payload-free `version_conflict` for stale expected version or concurrent
  winner;
- payload-free `unavailable` for canonical dependency or transaction failure.

Transport maps these without exception detail. Lists expose visible source
candidates only and no hidden/global total. Audit and logs contain no protected
source content or unbounded request body.

## 4. Read composition

An established read contains definition, scope, completion criteria, ordered
inputs, current stage, foundation version, allowed actions and readiness for the
next forward stage. Input response contains standing and safe current-source
summary only when independently authorized. Safe source summary is kind,
identity, version and Workspace; it contains no file name/content or Evidence
fact/reference. Unauthorized summary is absent and effective source condition
is generic.

Source-candidate queries are explicit by kind and optional authorized Workspace,
bounded to 1–50, deterministic by canonical time then identity, and return
visible items only. They call existing canonical services; no Project-owned
foreign repository query is allowed.

## 5. Reliability, Audit and concurrency

All mutations use one request-scoped PostgreSQL transaction. Foundation root is
locked before child mutation. Expected foundation/input versions distinguish
concurrency from authorization denial. Repository methods never commit.

Shared `AuditLog` action/category values are bounded `CREATE`, `UPDATE`, or
`TRANSITION`, entity `PROJECT_FOUNDATION`, Project integer entity identity, and
details limited to operation, versions, safe changed categories, stage/standing,
input UUID where applicable, and bounded rationale. Audit persistence failure
rolls back the primary mutation. No post-rollback rejection Audit is required.

No outbox is created because the accepted V1 has no asynchronous consumer.
Later event publication cannot be inferred from Audit.

## 6. API behavior

Authenticated V1 routes are exactly:

- `GET /projects/{project_id}/foundation`;
- `PUT /projects/{project_id}/foundation`;
- `POST /projects/{project_id}/foundation/inputs`;
- `PUT /projects/{project_id}/foundation/inputs/{input_id}`;
- `POST /projects/{project_id}/foundation/inputs/reorder`;
- `POST /projects/{project_id}/foundation/inputs/{input_id}/transitions`;
- `POST /projects/{project_id}/foundation/stage-transitions`;
- `GET /projects/{project_id}/foundation/source-candidates`.

No delete, generic workflow, batch mutation, raw tenant, approval, completion,
task, milestone or deliverable route exists.

## 7. Frontend behavior

Project detail displays one `Project Foundation` section. Not-established state
explains that no basis has been recorded and offers establishment only when the
server allows it. Established state displays/edit definition, scope and
completion criteria; input list and standing controls; authorized source
selectors; current stage; next-stage readiness; blockers; and explicit
rationale-bearing stage movement.

UI sends no actor/Organization and never interprets local state as authority.
It renders loading, truthful empty, protected, invalid, conflict, unavailable
and success states. It has accessible labels/fieldset/legend, keyboard use,
focus-visible feedback, status announcements and responsive stacking. No
generated examples or illustrative scenario data appear in production.

## 8. Backward compatibility

No Project row or current API contract changes. Empty new tables make every
legacy Project valid and readable as `basis_not_established`. Existing clients
continue to work. New functionality is additive and does not alter Project,
Workspace, Evidence or Supporting File state.

## 9. Explicit exclusions

The complete Architecture-044 deferred list is preserved. AI may not author,
approve, infer or transition any foundation state. No task/milestone,
deliverable, risk/change, Project Context, completeness intelligence,
procurement, execution plan, FAT/SAT execution, closeout, Wizard or Command
Center composition is introduced.
