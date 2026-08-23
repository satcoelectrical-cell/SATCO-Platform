# IDS-044 — Project Definition, Scope, Inputs & Lifecycle Foundation

## 1. Status

**ACCEPTED / COMPLETE.** Independent IDS Review is PASS. This IDS closes the
implementable V1 contracts of PATCH/Architecture/EDS-044. It authorizes no
implementation outside separately accepted batch manifests.

## 2. Closed types

### 2.1 Enums and value domains

```text
ProjectFoundationAvailability = basis_not_established | established
ProjectScopeKind = in_scope | out_of_scope
ProjectEngineeringStage = definition | preparation | execution |
                          verification | completion_readiness
ProjectInputStanding = missing | received | clarification_required |
                       not_applicable
ProjectInputSourceKind = supporting_file | evidence
ProjectFoundationOutcome = success | protected_not_found | invalid_request |
                           version_conflict | unavailable
ReadinessState = ready | blocked | not_applicable
ReadinessBlockerCode = definition_incomplete | scope_incomplete |
  completion_basis_incomplete | required_inputs_not_defined | input_missing |
  input_clarification_required | input_source_reauthorization_required
```

Stage rank is definition=0, preparation=1, execution=2, verification=3,
completion_readiness=4. Only absolute rank delta 1 is a transition.

### 2.2 Trusted actor

`ProjectFoundationActor(actor_id: int>0, organization_id: UUID)` is frozen,
extra-forbidden and constructed only by request composition from authenticated
Organization context.

## 3. Persistence contract

Migration revision is `e04400000001`, parent `e04300000001` and must be the
sole head.

### 3.1 `project_foundations`

| Column | Type | Rule |
|---|---|---|
| project_id | INTEGER PK, FK projects.id RESTRICT | canonical identity |
| organization_id | UUID NOT NULL FK organizations.id RESTRICT | equals Project Organization |
| purpose | VARCHAR(2000) NOT NULL | trimmed non-empty |
| engineering_basis | VARCHAR(5000) NOT NULL | trimmed non-empty |
| stage | VARCHAR(32) NOT NULL default `definition` | closed enum |
| version | INTEGER NOT NULL default 1 | >=1 |
| established_by_id | INTEGER NOT NULL FK users.id RESTRICT | immutable |
| established_at | TIMESTAMPTZ NOT NULL | immutable |
| updated_by_id | INTEGER NOT NULL FK users.id RESTRICT | current attribution |
| updated_at | TIMESTAMPTZ NOT NULL | current attribution |

Index `(organization_id, project_id)`. A constraint trigger checks parent
Project Organization equality and rejects insert/update when parent status is
`completed` or `cancelled` except that a status change performed by the
canonical Project capability does not rewrite foundation state. Immutable
columns project_id/organization_id/established attribution cannot change.

### 3.2 `project_scope_items`

UUID PK; `project_id` FK; copied Organization; `kind VARCHAR(16)`; `statement
VARCHAR(1000)`; `ordinal SMALLINT`; created/updated attribution/time. Closed
kind, ordinal 0–49, trimmed non-empty. Unique `(project_id, kind, ordinal)` and
case-insensitive unique `(project_id, kind, lower(statement))`. Index
`(organization_id, project_id, kind, ordinal)`. Parent-scope trigger enforces
Organization equality.

### 3.3 `project_completion_criteria`

UUID PK; Project/Organization; `statement VARCHAR(1000)`; ordinal SMALLINT;
created/updated attribution/time. Ordinal 0–49 and trimmed non-empty. Unique
Project ordinal and case-insensitive statement. Parent-scope trigger applies.
There is deliberately no standing/approval/completion column.

### 3.4 `project_required_inputs`

| Column | Type | Rule |
|---|---|---|
| id | UUID PK | server generated |
| project_id / organization_id | INTEGER / UUID NOT NULL | parent scoped |
| title | VARCHAR(200) NOT NULL | trimmed |
| description | VARCHAR(2000) NULL | trimmed or null |
| ordinal | SMALLINT NOT NULL | 0–99 |
| required_by_stage | VARCHAR(32) NOT NULL | closed stage |
| standing | VARCHAR(32) NOT NULL default `missing` | closed standing |
| source_kind | VARCHAR(32) NULL | paired closed kind |
| source_id | UUID NULL | paired exact identity |
| source_version | INTEGER NULL | paired, >=1 |
| source_workspace_id | INTEGER NULL FK engineering_workspaces.id RESTRICT | paired optional |
| standing_rationale | VARCHAR(2000) NOT NULL | bounded Human rationale |
| standing_changed_by_id | INTEGER NOT NULL FK users.id | attribution |
| standing_changed_at | TIMESTAMPTZ NOT NULL | attribution |
| version | INTEGER NOT NULL default 1 | >=1 |
| created/updated fields | actor/time NOT NULL | attribution |

Unique `(project_id, ordinal)` and `(project_id, lower(title))`; indexes on
Project ordering and source identity. Source fields are all null unless
standing=`received`, and source kind/id/version are all required when received.
`source_workspace_id` is optional only for a received source. The direct-SQL
constraint trigger checks:

- parent Organization equality;
- source UUID exists in the exact canonical table selected by kind;
- source Organization and Project equal the input;
- stored source version equals current canonical version;
- Supporting File standing is `available`;
- Evidence lifecycle is `current`;
- stored Workspace equals the canonical source Workspace and that Workspace
  belongs to the Project;
- unsupported kind is rejected.

The trigger is defense in depth and grants no disclosure. Application
authorization must already have succeeded.

### 3.5 `project_stage_history`

UUID PK; Project/Organization; `from_stage` nullable only for establishment;
`to_stage` closed; `foundation_version>=1`; actor FK; rationale VARCHAR(2000);
transitioned_at TIMESTAMPTZ; unique `(project_id, foundation_version)` and index
by Project/time/id. Trigger permits INSERT only to runtime and rejects UPDATE or
DELETE. It validates parent Organization, stage adjacency (or null->definition)
and exact root stage/version parity at deferred constraint time.

### 3.6 Runtime ownership and grants

Migration/schema owner owns tables, functions and triggers. Runtime receives
SELECT/INSERT and only required UPDATE columns. Runtime receives DELETE only
on `project_scope_items` and `project_completion_criteria`, because the accepted
bounded replace operation must be able to reduce those Project-owned current
collections atomically. It receives no DELETE on the foundation root, required
inputs or stage history, and no TRUNCATE/TRIGGER/REFERENCES/DDL/function EXECUTE
authority. Stage history is SELECT/INSERT only.
Tests inspect exact object schema, function signatures, trigger/table binding,
owner and grants and fail on drift.

## 4. Closed DTOs

All Pydantic models use `extra='forbid'`; read DTOs are frozen.

### 4.1 Commands

- `PutProjectFoundation(expected_version ge 0, purpose, engineering_basis,
  in_scope: tuple[1..50], out_of_scope: tuple[0..50], completion_criteria:
  tuple[1..50], rationale)`; strings are ordered values, not client identities.
- `CreateProjectInput(expected_foundation_version>=1, title, description,
  ordinal 0..99, required_by_stage, rationale)`.
- `UpdateProjectInput(expected_foundation_version>=1, expected_input_version>=1,
  title, description, ordinal, required_by_stage, rationale)`; all definition
  fields are required to avoid ambiguous patch semantics.
- `ReorderProjectInputs(expected_foundation_version>=1, ordered_input_ids:
  tuple[1..100 unique], rationale)`.
- `TransitionProjectInput(expected_foundation_version>=1,
  expected_input_version>=1, target_standing, source_kind?, source_id?,
  source_workspace_id?, rationale)` with exact source pairing. Workspace is the
  selector context required by the current canonical Supporting File service;
  it is not trusted and must match the authorized canonical response.
- `TransitionProjectStage(expected_foundation_version>=1, target_stage,
  rationale)`.
- `ListProjectInputSourceCandidates(kind, workspace_id?, limit 1..50)`.

Every rationale is trimmed 1–2,000. Tuple order is canonical; duplicate
normalized statements/IDs are rejected.

### 4.2 Read models

`ProjectFoundationNotEstablished(outcome='success', availability, project_id,
allowed_actions)` contains no stage/readiness.

`ProjectFoundationEstablished(outcome='success', availability, project_id,
version, purpose, engineering_basis, stage, in_scope, out_of_scope,
completion_criteria, inputs, next_stage_readiness, allowed_actions,
established_at, updated_at)`.

Each scope/criterion item has identity, ordinal and statement. Each input has
identity, title, description, ordinal, required stage, declared standing,
effective source condition (`not_required`, `authorized_current`, or
`source_reauthorization_required`), optional safe source, version and
attribution timestamps. Safe source contains kind, UUID, exact version and
optional Workspace only.

`ProjectStageReadiness(state, target_stage?, blockers tuple[0..100])`; blocker
contains code plus optional Project-owned input_id/title only.

Source candidate contains kind, source UUID, version, optional Workspace and a
safe display label already authorized by the canonical service. Candidate page
contains items and `visible_count==len(items)` only; no total.

### 4.3 Result unions

Every operation returns an exact discriminated union with `outcome`:

- read/put/input create/update/reorder/input transition/stage transition/source
  candidates each have an operation-specific success;
- shared protected, invalid, conflict and unavailable variants contain only
  the discriminator.

No exception string is part of a result.

## 5. Domain and application ports

### 5.1 Inward service

`ProjectFoundationApplication` exposes `get`, `put`, `create_input`,
`update_input`, `reorder_inputs`, `transition_input`, `transition_stage`, and
`list_source_candidates`. All accept the trusted actor and explicit Project.

### 5.2 Outward ports

- `ProjectFoundationRepository`: scoped root get/lock/create/update;
  deterministic child load/replace/add/update/reorder; history append; no
  commit.
- `ProjectFoundationAuthorization`: `can_read(actor, project)` and
  `can_mutate(actor, project)` implementing the EDS matrix.
- `ProjectInputSourceAuthorization`: `authorize_exact(actor, project_id, kind,
  source_id, workspace_id)` and bounded `list_authorized(...)`; each delegates to the current
  canonical Evidence or Supporting File application service, never its
  repository/ORM/Session.
- `ProjectFoundationClock`: aware UTC now.
- `ProjectFoundationUnitOfWork`: one Session, repository, Audit stage,
  `commit/rollback`, context manager.

Canonical source failures translate: missing/denied -> protected; dependency
failure -> unavailable; malformed/non-current/cross-scope -> protected.

## 6. Transaction sequencing

### 6.1 Definition/input mutation

1. authenticate and derive actor/Organization;
2. resolve Project inside Organization and apply operation authority;
3. open one UoW and lock Project/Foundation as applicable;
4. verify Project mutable status and expected versions;
5. validate full command and current child set;
6. for received transition, authorize exact canonical source before and again
   after the foundation lock immediately before persistence;
7. stage root/children and increment foundation version once; input mutation
   increments input version once where applicable;
8. stage bounded shared Audit;
9. flush so DB guards run;
10. commit once; on any failure rollback all and return closed outcome.

### 6.2 Stage transition

Steps 1–4, then compute target readiness from the locked state. Reauthorize
every due received source in deterministic `(ordinal,id)` order, maximum 100
calls. If any blocker exists, invalid. Mutate root, append exact history, Audit,
flush and commit once. Concurrent requests have one winner.

Idempotency storage is not added: commands have no external side effect or
asynchronous consumer, and expected versions make retries deterministic as
success-or-conflict. Introducing a replay table would store redundant
governance state without an accepted need. Transport must refetch on conflict.

## 7. API and composition

The eight EDS routes are implemented by one thin authenticated router. A
request-scoped dependency constructs the Project Foundation service/UoW,
authorization policy and canonical source adapters. The router parses,
delegates once and serializes the closed result. It imports no ORM model,
Session, repository or policy implementation.

HTTP status remains 200 for application closed outcomes so payload shapes are
stable; authentication failure remains 401. Transport validation failures are
translated to `{'outcome':'invalid_request'}` without Pydantic/domain detail.
The source-candidate query is GET and read-only. No raw Organization/actor is a
request field.

## 8. Migration and model registration

Migration imports no application code, creates functions before triggers,
applies schema-owner ownership and runtime grants, and downgrade removes only
PATCH-044 objects in dependency order. ORM metadata matches DB types,
nullability, FKs, indexes and constraints. `models/__init__.py` registers the
four models for Alembic/test metadata; `enums/__init__.py` exports the closed
enums.

## 9. Verification matrix

| Invariant | Required executable evidence |
|---|---|
| legacy truthfulness | absent root returns not-established; migration creates none |
| contracts | extra fields, invalid enums, lengths, duplicate/order/cardinality rejected |
| tenant | cross-Organization Project/source protected; no identity/count detail |
| authority | admin/owner/assignee mutation; Workspace member read-only; inactive denied |
| scope/source | available File/current Evidence accepted; cross-Project/Workspace mismatch, withdrawn/non-current/unsupported rejected |
| source revocation | declared received remains history but readiness blocks and source summary is protected |
| input machine | every valid edge; every invalid edge; source field pairing |
| definition | atomic replace, normalized uniqueness, edit-stage restriction |
| readiness | due-stage rank, blockers, at least one input, no autonomous mutation |
| stage | adjacency, forward gate, backward rationale, one-winner stale version |
| DB guards | direct-SQL parent/source/standing/workspace/ordinal/immutable history bypass rejected |
| transaction | injected child/Audit/flush failures roll back root/history/input |
| roles | exact owner/grants/function/trigger drift and runtime DDL/history mutation denial |
| API | eight routes, auth, trusted context, discriminator-only protected/invalid/conflict/unavailable |
| UI | real API, not-established/established, input/source/stage flow, loading/error/protected/conflict, accessibility/responsive/no fake data |
| regression | Project/Workspace/Evidence/Supporting File/auth/Audit/migration plus full backend/frontend |

## 10. Explicit exclusions

No outbox, deletion, batch mutation, generic workflow configuration, source
content copy, AI decision, task/milestone/deliverable/risk/change/context graph,
completion execution, Wizard or any PATCH-045–065 behavior.
