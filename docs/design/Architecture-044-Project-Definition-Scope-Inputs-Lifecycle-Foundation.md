# Architecture-044 — Project Definition, Scope, Inputs & Lifecycle Foundation

## 1. Decision status

**ACCEPTED / COMPLETE.** Independent Architecture Review and QG-M1 are PASS.
The Human Architecture Acceptance is recorded separately. This architecture
authorizes design only; implementation remains governed by IRR and exact batch
manifests.

## 2. Repository discovery

### 2.1 Current Project ownership

The canonical `Project` owns server-generated identity and Project Code,
immutable Organization, Customer, name/description, status, priority, owner,
primary assignee, dates, progress and audit-backed mutation. Its status machine
already governs Project lifecycle. PATCH-044 does not replace it.

### 2.2 Current Workspace ownership

Engineering Workspace owns discipline-local identity, ownership, membership,
status and operational engineering context. It belongs to exactly one Project
and does not own Project scope, Project stage or Project-wide required inputs.

### 2.3 Existing approximations and gaps

Project description approximates a summary but cannot distinguish purpose from
engineering basis. Status/progress are not engineering stage/readiness.
Workspace status is discipline-local. Supporting File is immutable material
file authority; Evidence is governed metadata authority. Neither is a Project
input requirement. No current table/API/UI owns Project-wide scope, required
input standing, stage readiness, or a completion basis.

### 2.4 Safe future primitives

Project, Workspace, Engineering Object/Relationship, Evidence and Supporting
File identities remain reusable canonical context, but PATCH-044 uses only
Project/Workspace visibility and bounded Evidence/Supporting File source
authorization. It does not expand EKG or build Project Context.

## 3. Architectural decision

### 3.1 Project-owned subordinate foundation

Project Definition is a versioned subordinate component of the canonical
Project, keyed one-to-one by Project identity. It owns:

- purpose and engineering-basis text;
- current Project engineering stage;
- ordered scope statements;
- ordered completion-basis criteria;
- Project-owned required-input definitions;
- immutable stage-transition history.

It is not a competing Project aggregate, Workspace, execution plan, schedule,
task board, deliverable register or workflow engine. Its Organization is copied
for tenant enforcement and must equal its parent Project.

The relational model is preferred over an untyped JSON document because scope,
input standing, ordering, source linkage, stage and concurrency are canonical
invariants.

### 3.2 Definition and scope

Purpose answers why the Project exists. Engineering basis states the bounded
engineering undertaking in Human-authored terms. Scope is an ordered set of
typed `in_scope` and `out_of_scope` statements. At least one `in_scope`
statement is required to establish the basis; out-of-scope statements are
optional. Statements are not deliverables, tasks, risks or graph objects.

Definition/scope/completion-basis edits are allowed only in `definition` or
`preparation`. Later correction requires an explicit Human stage move back to
`preparation`, preserving transition history. This prevents silent
post-execution scope rewriting without inventing change-control capability.

### 3.3 Required Project Inputs

Required inputs are Project-owned expectations: title, description, ordered
position, stage by which they are required, standing and attribution. They do
not own file bytes, evidence facts, captures or deliverables.

Standing is closed:

- `missing`: expected but no usable accepted source is declared;
- `received`: a Human declares receipt through one exact current canonical
  source;
- `clarification_required`: material arrived or was considered but a bounded
  Human rationale identifies what must be clarified;
- `not_applicable`: an authorized Human explicitly determines the expectation
  does not apply and supplies rationale.

New inputs begin `missing`. `received` requires exactly one source of kind
`supporting_file` or `evidence`. Supporting File must be `available`; Evidence
must be `current`. The source must have the same Organization and Project;
optional Workspace is accepted only when it belongs to that Project and the
actor is authorized there. Source content is not copied. Unsupported source
kinds are rejected.

A stored received declaration is immutable audit history, not permanent proof
of availability. Current source standing and authorization are rechecked for
readiness and protected source disclosure. Withdrawal, lifecycle change or
authorization revocation makes the input effectively blocking without silently
rewriting its Human-declared standing. A Human may then provide another source
or change standing with rationale.

### 3.4 Stage and readiness

Project status remains lifecycle. Project engineering stage is distinct and
exactly ordered:

1. `definition`;
2. `preparation`;
3. `execution`;
4. `verification`;
5. `completion_readiness`.

Only adjacent transitions are allowed. Forward transition requires:

- established definition and engineering basis;
- at least one in-scope statement;
- at least one completion-basis criterion;
- at least one required-input definition;
- every input required by the target stage to be effectively satisfied by an
  authorized current source or explicit `not_applicable` determination.

`missing`, `clarification_required`, inaccessible or non-current received
sources are blockers. Backward transition requires authority and rationale but
not readiness. The application returns explicit safe blocker categories. It
never transitions automatically, infers Human acceptance, or treats a score as
authority.

The final stage means only that the recorded foundation is ready for future
completion/closeout work. It does not complete the Project, accept deliverables,
perform FAT/SAT or implement PATCH-058.

### 3.5 Bounded completion basis

Completion-basis criteria are ordered Human-authored statements describing the
future conditions against which completion can be judged. PATCH-044 records no
criterion execution, pass/fail, approval, acceptance certificate, handover or
closeout state. Downstream PATCHes may reference but cannot retroactively
invent these criteria.

## 4. Authorization and protected disclosure

Authentication and active Organization are server-derived. Project is queried
inside that Organization before any foundation existence, count, stage, input,
scope, source or readiness disclosure.

Read uses established Project visibility: Organization admin, Project owner or
primary assignee, or an authorized participant in a Project Workspace.
Mutation uses existing Project update authority: Organization admin, Project
owner or primary assignee. Completed/cancelled Projects are foundation read-only.
Every mutation carries an expected version where applicable and a bounded
Human rationale; actor, Organization and authority are never accepted from the
client.

Source authorization is independent. A Project-authorized reader does not gain
Supporting File/Evidence authority. Unauthorized source identifiers and details
are omitted; the Project input may safely report `source_reauthorization_required`
because the input itself is Project-owned and authorized. Cross-Organization or
cross-Project references return the same payload-free protected result as
missing references.

Closed outcomes are success, `protected_not_found`, `invalid_request`,
`version_conflict`, and `unavailable`. Protected outcomes disclose only their
discriminator.

## 5. Reliability and history

PostgreSQL is the SSOT. Mutations use one request-scoped transaction and one
Session. Repositories do not commit. Optimistic version checks and deterministic
row locking provide one-winner behavior. Definition/scope/criteria replacement,
input state changes, stage history and shared `AuditLog` persist atomically.

Audit records actor, operation, Project, safe changed-field categories,
previous/new version, stage/standing and bounded rationale. It does not copy
Supporting File content, Evidence supported facts, credentials or exception
details. Stage history is append-only and database-protected. Domain outbox is
not required in V1 because PATCH-044 has no asynchronous consumer or autonomous
transition; adding one requires separately governed need.

## 6. Backward compatibility and migration

The migration creates only empty subordinate tables and guards. It performs no
Project backfill. A Project without a foundation reads successfully as
`basis_not_established`, with no scope, inputs, stage or readiness claim. First
authorized definition mutation creates the component at `definition` stage and
records actor/time/Audit.

Existing Project, Workspace, Capture, Evidence, Supporting File, Report, Memory
and AI behavior is unchanged. Project deletion remains blocked by Workspace
history; a Project foundation is subordinate and cannot weaken existing delete
rules.

## 7. Product experience

The current Project detail page gains a bounded Project Foundation surface:

- truthful not-established action;
- purpose and engineering basis editor;
- ordered in/out scope and completion criteria;
- required inputs with state, due stage and canonical source selection;
- current stage, readiness blockers and explicit Human transition;
- loading, protected, invalid, conflict, unavailable, empty and success states.

No raw Organization, Project, Workspace, Evidence or Supporting File identifier
entry is presented. Authorized existing source selectors provide choices.
Keyboard labels, focus, live feedback, touch targets, text wrapping, responsive
stacking and no horizontal overflow are required. Production UI uses no fake
counts, inputs, readiness or engineering evidence.

## 8. Deferred boundary

All PATCH-045–065 capabilities named in PATCH-044 remain deferred. In
particular: no tasks, milestones, deliverables, risks, issues, decisions,
change impact, Project Context expansion, completeness AI, engineering
guidance, procurement, cost, FAT/SAT execution, closeout, Wizard, final Command
Center, licensing, remote qualification, proposal, automation, generic BPM,
automatic completeness or AI authority.

## 9. Architecture-discovery answers

A–F are resolved by Sections 2 and 3. G: Project-owned subordinate relational
components. H: Required inputs are owned by Project. I: expectations reference
but do not own Supporting File/Evidence; they are neither deliverables nor
Captures. J: the four closed standings in 3.3. K: readiness is derived; only an
authorized Human transition changes stage. L: criteria definitions only. M:
definition, scope, inputs, stage, blockers and completion basis. N: absence is
truthful not-established state. O: tenant-first and independent source
authorization with protected outcomes.
