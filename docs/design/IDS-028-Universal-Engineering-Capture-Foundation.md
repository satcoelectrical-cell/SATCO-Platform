# IDS-028 — Universal Engineering Capture Foundation

## 1. Document Control

| Field | Value |
|---|---|
| Document ID | IDS-028 |
| Related PATCH | PATCH-028 v1.0 |
| Related EDS | EDS-028 v0.1 Accepted |
| Version | 0.1 |
| Status | APPROVED |
| Classification | Exact backend implementation contract |
| Date | 2026-08-02 |

This IDS defines the complete implementation boundary. It does not authorize
implementation until Human approval, an accepted executable Implementation
Plan, and IRR-028 `READY FOR IMPLEMENTATION`.

### Approval Record

| Authority | Decision | Date |
|---|---|---|
| Product Owner | Approved | 2026-08-02 |
| Architecture Guardian | Approved | 2026-08-02 |

## 2. Repository Baseline

At IDS preparation:

- branch: `patch-022.3a-development-infrastructure`;
- Alembic reports one head: `e02810000001`;
- `e02810000001` descends from `e02600000001` and PATCH-027 revision
  `e02700000001`;
- PATCH-023 through PATCH-027 implementation patterns exist;
- Pydantic v2, SQLAlchemy, FastAPI, PostgreSQL, and existing authenticated
  Organization context remain the implementation baseline.

The migration parent is an IRR-time assertion. If the single head changes,
implementation stops and IDS migration assumptions are re-reviewed.

## 3. Exact Authorized File Set

### Modified files

1. `backend/app/enums/__init__.py`
2. `backend/app/models/__init__.py`
3. `backend/app/schemas/__init__.py`
4. `backend/app/main.py`
5. `backend/migrations/env.py`
6. `backend/tests/test_patch_028_1_migration.py` (test-only deterministic
   isolation remediation; no production migration behavior change)

### Created files

1. `backend/app/enums/engineering_experience_capture.py`
2. `backend/app/models/engineering_experience_capture.py`
3. `backend/app/models/engineering_experience_capture_command.py`
4. `backend/app/schemas/engineering_experience_capture.py`
5. `backend/app/ports/engineering_experience_capture.py`
6. `backend/app/repositories/engineering_experience_capture_repository.py`
7. `backend/app/repositories/engineering_experience_capture_unit_of_work.py`
8. `backend/app/services/engineering_experience_capture_service.py`
9. `backend/app/exceptions/engineering_experience_capture.py`
10. `backend/app/api/v1/routers/engineering_experience_captures.py`
11. `backend/migrations/versions/e02800000001_engineering_experience_capture.py`
12. `backend/tests/test_engineering_experience_capture_aggregate.py`
13. `backend/tests/test_engineering_experience_capture_schemas.py`
14. `backend/tests/test_engineering_experience_capture_repository.py`
15. `backend/tests/test_engineering_experience_capture_service.py`
16. `backend/tests/test_engineering_experience_capture_api.py`
17. `backend/tests/test_engineering_experience_capture_transaction.py`
18. `backend/tests/test_engineering_experience_capture_migration.py`
19. `backend/tests/test_engineering_experience_capture_security.py`
20. `backend/tests/test_engineering_experience_capture_performance.py`

No other backend, migration, test, or configuration file is authorized.
Lifecycle documentation may be updated only under completion policy after
validation.

The authorization for `backend/tests/test_patch_028_1_migration.py` is limited
to making the migration test own and restore its disposable state in every
success and failure path. It must preserve every existing downgrade assertion
and leave the guarded isolated test database at repository Alembic head with
the persistent test Organization available. It does not authorize a production
migration edit, weaker assertion, skip, ordering dependency, runtime change, or
PATCH-028.1 semantic change.

### Focused Security-Evidence Remediation Authorization

The following already-approved test files are authorized for behavioral
security and disclosure evidence only:

- `backend/tests/test_engineering_experience_capture_security.py`;
- `backend/tests/test_engineering_experience_capture_service.py`;
- `backend/tests/test_engineering_experience_capture_transaction.py`;
- `backend/tests/test_engineering_experience_capture_api.py`.

They must prove inactive User, disabled/nonmember Organization,
cross-Project/Workspace/Engineering-Object denial; protected-not-found for get,
withdraw, supersede, and supersession chain; omission of unauthorized list rows
with accurate authorized totals; replay reauthorization after access
revocation without stored-content disclosure; and runtime absence of Capture
content, source reference, and rationale from Audit, outbox, API errors, logs,
idempotency conflicts, and diagnostics.

Only if those tests expose a defect, the following already-approved runtime
files may receive the smallest correction necessary to satisfy the existing
contract:

- `backend/app/services/engineering_experience_capture_service.py`;
- `backend/app/repositories/engineering_experience_capture_repository.py`;
- `backend/app/repositories/engineering_experience_capture_unit_of_work.py`;
- `backend/app/api/v1/routers/engineering_experience_captures.py`.

This conditional authority permits no new route, schema, migration, aggregate
contract, scope, authorization category, disclosure behavior, or transaction
boundary. Repository no-commit and Unit-of-Work transaction ownership remain
mandatory. Existing tests may not be weakened, skipped, or replaced by source
inspection where behavioral evidence is required.

## 4. Controlled Enumerations

`backend/app/enums/engineering_experience_capture.py` defines only:

```text
EngineeringExperienceCaptureLifecycle
  CAPTURED = "captured"
  WITHDRAWN = "withdrawn"
  SUPERSEDED = "superseded"

EngineeringExperienceSourceKind
  OBSERVATION = "observation"
  QUESTION = "question"
  ASSUMPTION = "assumption"
  RATIONALE = "rationale"
  DISCUSSION_NOTE = "discussion_note"
  CORRESPONDENCE_NOTE = "correspondence_note"
  FIELD_NOTE = "field_note"
  REVIEW_NOTE = "review_note"
  OUTCOME = "outcome"
  LESSON_CANDIDATE = "lesson_candidate"
  EXTERNAL_RECORD_NOTE = "external_record_note"
```

Both use `StrEnum`. `backend/app/enums/__init__.py` exports them using their
qualified names. No aliases, free-text fallback, database enum type, authority
standing, or AI/provider enum is authorized.

## 5. Domain Command and Event Contracts

`engineering_experience_capture_command.py` owns immutable dataclasses and
durable command-record models analogous to, but not copied blindly from,
PATCH-027:

- `EngineeringExperienceCaptureActor(actor_id, organization_id)`;
- `EngineeringExperienceCaptureMetadata(actor, rationale, correlation_id,
  idempotency_id, command_id)`;
- `CreateEngineeringExperienceCapture`;
- `WithdrawEngineeringExperienceCapture`;
- `SupersedeEngineeringExperienceCapture`;
- `EngineeringExperienceCaptureEvent`;
- `EngineeringExperienceCaptureResult`;
- `EngineeringExperienceCaptureOutcome`;
- domain errors for version mismatch, invalid transition, invalid content,
  invalid context shape, and invalid supersession;
- `EngineeringExperienceCaptureOutbox` ORM model;
- `EngineeringExperienceCaptureIdempotency` ORM model.

Creation metadata rationale uses exact normalized value `capture submitted` and
is server-derived; the create request does not accept rationale. Withdraw and
supersede accept a Human rationale of 1–1000 code points.

Event payloads use scalar identifiers/state only and must not contain original
content, source reference, or rationale.

## 6. Aggregate Model Contract

`engineering_experience_capture.py` defines one SQLAlchemy/domain Aggregate
Root mapped to `engineering_experience_captures` with exactly the EDS fields.

### Columns

| Column | PostgreSQL/SQLAlchemy contract |
|---|---|
| `id` | UUID primary key, application-generated |
| `organization_id` | UUID, FK `organizations.id`, RESTRICT, non-null |
| `project_id` | Integer, FK `projects.id`, RESTRICT, non-null |
| `workspace_id` | Integer, FK `engineering_workspaces.id`, RESTRICT, nullable |
| `discipline` | String(32), nullable |
| `engineering_object_id` | UUID, FK `engineering_objects.id`, RESTRICT, nullable |
| `source_kind` | String(32), non-null |
| `original_content` | Text, non-null |
| `source_reference` | String(512), nullable |
| `creator_id` | Integer, FK `users.id`, RESTRICT, non-null |
| `lifecycle` | String(16), non-null, server/application default `captured` |
| `superseded_by_capture_id` | UUID, self-FK RESTRICT, nullable |
| `version` | Integer, non-null, server/application default 1 |
| `created_at` | timezone-aware timestamp, non-null |
| `updated_at` | timezone-aware timestamp, non-null |

### Database checks

- lifecycle belongs to the exact closed set;
- source kind belongs to the exact closed set;
- version is at least 1;
- updated timestamp is not earlier than created timestamp;
- Workspace null implies discipline and Engineering Object are null;
- Workspace non-null implies discipline non-null;
- Engineering Object non-null implies Workspace non-null;
- lifecycle `superseded` iff replacement UUID is non-null;
- replacement UUID differs from aggregate UUID;
- `char_length(original_content)` is between 1 and 10,000;
- source reference is null or its length is between 1 and 512.

Database checks complement rather than replace aggregate/application
validation. Cross-table context compatibility remains application-owned.

### Aggregate methods

- `create(command, now)`;
- `withdraw(command, now)`;
- `supersede(command, now)`.

No generic setter, generic transition, edit, restore, or delete method exists.
Every successful post-creation command advances version exactly once and emits
one past-tense event.

## 7. Text Normalization Contract

A single pure helper owned by the domain model module implements the exact EDS
normalization for content, source reference, and rationale. Schemas enforce
coarse lengths; the domain is authoritative for normalized code-point limits
and control-character rejection.

Fingerprinting uses normalized command data. It must never log or expose the
preimage. A SHA-256 request fingerprint may represent content in the
idempotency table; plaintext content/reference/rationale must not be stored in
the idempotency request record.

## 8. Persistence Tables and Constraints

### `engineering_experience_captures`

Uses Section 6 columns/checks plus these indexes:

- `ix_experience_captures_project_order` on
  `(organization_id, project_id, created_at DESC, id DESC)`;
- `ix_experience_captures_workspace_order` on
  `(organization_id, project_id, workspace_id, created_at DESC, id DESC)`;
- `ix_experience_captures_lifecycle_kind` on
  `(organization_id, project_id, lifecycle, source_kind)`;
- `ix_experience_captures_creator` on
  `(organization_id, project_id, creator_id)`;
- `ix_experience_captures_object` on
  `(organization_id, engineering_object_id)` with a partial predicate for
  non-null object references;
- unique partial `uq_experience_captures_replacement` on
  `superseded_by_capture_id` where non-null, preventing one replacement from
  superseding multiple predecessors.

### `engineering_experience_capture_outbox`

Columns: UUID primary key, unique event UUID, aggregate UUID FK RESTRICT,
positive aggregate version, event type String(96), schema version integer
fixed to 1, JSON payload, occurred/published/created timestamps. Unique
`(aggregate_id, aggregate_version, event_type)` prevents duplicate durable
events for one transition.

### `engineering_experience_capture_idempotency`

Columns: UUID primary key, Organization UUID FK RESTRICT, actor integer FK
RESTRICT, command type String(64), idempotency UUID, SHA-256 fingerprint
String(64), status `pending|completed`, aggregate UUID FK RESTRICT nullable
until completion, JSON authorized result, created/updated timestamps.

Unique scope is `(organization_id, actor_id, command_type, idempotency_id)`.
Stored result contains only the authorized response required for exact replay.

## 9. Migration Contract

Revision ID is exactly `e02800000001`. Its sole parent is
`e02810000001`. IRR must re-run `alembic heads`; any different or multiple head
blocks implementation and requires contract re-review.

Upgrade creates exactly the three Section 8 tables, owned indexes, FKs, checks,
and unique constraints. Downgrade removes only those structures in dependency
order. It does not modify existing tables or data.

`backend/migrations/env.py` imports both new ORM modules for metadata discovery.
No historical migration edit, merge revision, PostgreSQL enum, trigger,
function, sequence, data backfill, or production execution is authorized.

## 10. Context and Supersession Validators

The SQLAlchemy adapter in
`engineering_experience_capture_unit_of_work.py` validates:

- active authenticated User and Organization context;
- Project exists in the active Organization and is visible/authorized;
- Workspace exists in that Project and is visible/authorized;
- discipline is derived from Workspace `Discipline` and persisted as its exact
  string value;
- Engineering Object exists in the same Organization/Project/Workspace and is
  visible;
- Workspace-to-object discipline mapping is exact:
  `electrical → electrical`, `instrumentation → instrumentation`, and
  `control → industrial_automation`;
- other Workspace disciplines cannot receive an Engineering Object reference
  under Version-1 EKG object scope;
- replacement Capture is distinct, `captured`, fully visible, same exact
  Organization/Project/Workspace/discipline/object context, and unused as a
  replacement;
- bounded predecessor traversal to depth 20 proves no cycle and no branching.

Supersession validation and compare-and-change execute inside the same Unit of
Work. The adapter acquires a transaction-scoped PostgreSQL advisory lock keyed
by Organization, Project, and replacement Capture UUID before uniqueness/cycle
validation and update, preventing concurrent branching/merging.

## 11. Authorization Contract

The Capture authorization adapter uses existing User role, Project ownership/
primary assignment, Workspace ownership/primary assignment/membership, and
Engineering Object visibility conventions.

- active `admin` may create/read/list/manage within the active Organization;
- active `engineer` may create Project-wide Capture only when Project owner or
  primary assignee;
- active `engineer` may create Workspace Capture when Project owner/primary
  assignee, Workspace owner/primary assignee, or enabled Workspace member;
- read/list requires the same applicable Project/Workspace visibility and
  Engineering Object visibility when referenced;
- withdraw/supersede requires Creator plus current scope access, or active
  `admin` in the same Organization;
- no other role or inactive User is authorized;
- authorization precedes disclosure and reference error differentiation.

No global `permissions.py` change is authorized; operation-specific policy
stays behind the inward-owned Capture port.

## 12. Inward-Owned Ports and Unit of Work

`ports/engineering_experience_capture.py` defines Protocols for:

- repository add/scoped get/scoped Project list/scoped Workspace list/
  expected-version persist/bounded predecessor traversal/replacement-use check;
- operation-specific authorization;
- context validation;
- supersession validation;
- Audit recorder;
- Domain Event recorder;
- idempotency store;
- Unit of Work;
- Clock.

The Unit of Work exposes Capture repository, Audit, events, and idempotency and
owns commit/rollback. Repositories never authorize, commit, publish, or delete.

## 13. Repository Contract

`SqlAlchemyEngineeringExperienceCaptureRepository`:

- loads only by aggregate UUID plus Organization UUID;
- applies Project/Workspace/filter bounds before pagination;
- orders lists by `created_at DESC, id DESC`;
- supports lifecycle, source kind, Creator, and exact object filters;
- performs expected-version compare-and-change for lifecycle, replacement,
  version, and updated timestamp only;
- never updates immutable fields;
- checks replacement use and traverses supersession through bounded SQL/data
  access without unbounded recursion;
- returns raw scoped candidates to Application policy filtering without
  claiming authorization.

List response totals must describe fully authorized results. The implementation
must not return an unfiltered database total when row-level constituent policy
could remove records. IDS permits either authorization-aware query filtering or
a bounded two-phase candidate window proven complete by tests; N+1 policy
queries are prohibited.

## 14. Application Service Contract

Service methods:

- `create(data, actor, correlation_id, idempotency_id)`;
- `get(capture_id, actor)`;
- `list_project(project_id, filters, pagination, actor)`;
- `list_workspace(workspace_id, filters, pagination, actor)`;
- `withdraw(capture_id, data, actor, correlation_id, idempotency_id)`;
- `supersede(capture_id, data, actor, correlation_id, idempotency_id)`;
- `supersession_chain(capture_id, actor)`.

Mutation sequence is authenticate/derive scope, normalize/fingerprint,
authorize-before-disclosure, validate context/replacement, resolve/reserve
idempotency, invoke exactly one aggregate command, expected-version persist,
stage Audit/events/result, commit, and map authorized response.

The service cannot mutate ORM fields, duplicate transition rules, expose
content in errors/logs/events/Audit, publish events, or commit through a
repository.

`allowed_actions` is computed from lifecycle, Creator/admin status, and current
constituent authorization. It contains only `withdraw` and/or `supersede` when
currently allowed; it is not an authorization grant.

## 15. Pydantic Schema Contract

All schemas use Pydantic v2 `ConfigDict(extra="forbid")`.

### Create request

- `project_id: int` greater than zero;
- optional `workspace_id: int` greater than zero;
- optional `engineering_object_id: UUID`;
- `source_kind` controlled enum;
- `original_content: str` coarse max 10,000;
- optional `source_reference: str` coarse max 512.

It rejects Organization, discipline, Creator, lifecycle, replacement, version,
timestamps, authority, approval, AI/provider, Audit, and event fields.

### Withdraw request

- positive `expected_version`;
- rationale 1–1000.

### Supersede request

- positive `expected_version`;
- distinct `replacement_capture_id: UUID`;
- rationale 1–1000.

### Filters/pagination

- optional lifecycle, source kind, positive Creator ID, object UUID;
- page/size or existing approved pagination shape with maximum size 100;
- no sort expression, free text, arbitrary field, cross-Project, or
  confidentiality filter.

### Response

Returns exact aggregate scalar state, complete original content/source
reference only after full authorization, and deterministic `allowed_actions`.
List and supersession-chain wrappers are bounded and contain no unauthorized
total or identifier.

## 16. HTTP Contract

Router prefix uses the exact EDS paths:

- `POST /engineering-experience-captures` → 201;
- `GET /engineering-experience-captures/{capture_id}` → 200;
- `GET /projects/{project_id}/engineering-experience-captures` → 200;
- `GET /engineering-workspaces/{workspace_id}/engineering-experience-captures`
  → 200;
- `POST /engineering-experience-captures/{capture_id}/withdraw` → 200;
- `POST /engineering-experience-captures/{capture_id}/supersede` → 200;
- `GET /engineering-experience-captures/{capture_id}/supersession-chain` → 200.

Mutations require `X-Correlation-ID` and `Idempotency-Key` UUID headers.
Authentication uses PATCH-025 active Organization context. Dependency
composition is request-scoped; Unit of Work sessions are separate and bounded.

`backend/app/main.py` imports and registers exactly one new router. No PUT,
PATCH, DELETE, upload, bulk, search, AI, review, approval, publish, or memory
route is authorized.

## 17. Stable Error Contract

`exceptions/engineering_experience_capture.py` defines errors with prefix
`ENGINEERING_EXPERIENCE_CAPTURE_`:

| Code suffix | HTTP |
|---|---:|
| `VALIDATION_ERROR` | 422 |
| `AUTHORIZATION_DENIED` | 403, only when policy permits disclosure |
| `NOT_FOUND` | 404 protected |
| `VERSION_CONFLICT` | 409 |
| `IDEMPOTENCY_CONFLICT` | 409 |
| `INVALID_LIFECYCLE_TRANSITION` | 409 |
| `INVALID_CONTEXT` | 422 |
| `INVALID_SUPERSESSION` | 409 |
| `DUPLICATE_SUPERSESSION` | 409 |
| `SUPERSESSION_CYCLE` | 409 |
| `CONTENT_LIMIT_EXCEEDED` | 422 |
| `INTERNAL_ERROR` | 500 |

Existing generic `SatcoException` handling is reused; handlers are not
modified. Messages never echo content, source reference, rationale, protected
IDs, or internal exceptions.

## 18. Audit, Events, Logging, and Replay Safety

Audit entity is exactly `ENGINEERING_EXPERIENCE_CAPTURE` with `entity_uuid`.
Audit details include command, trusted scope, lifecycle transition, versions,
actor, correlation/idempotency identifiers, replacement UUID when authorized,
and timestamps. They exclude content, source reference, and rationale text.

Outbox payload follows EDS Section 15 and uses schema version 1. Idempotency
authorized result may contain the response needed for replay, including content
only because replay is re-authorized before return; conflict/errors never
disclose stored result. If actor authorization has changed since the original
command, replay returns protected failure rather than historical content.

Application and adapter logging must use identifiers/status only. Tests shall
inspect Audit/outbox/idempotency/log records for prohibited plaintext.

## 19. Test File Responsibilities

- aggregate: commands, lifecycle, version, events, immutability, normalization,
  terminal states, supersession invariants;
- schemas: strict fields, bounds, trusted-field rejection, UUID/positive values;
- repository: scoped load/list/order/filter/count, immutable persistence,
  expected version, replacement use, bounded chain;
- service: orchestration, derivation, authorization, validators, allowed
  actions, exact replay/conflict;
- API: every route/status/header/error and prohibited methods/routes;
- transaction: atomic success and staged rollback for aggregate/Audit/outbox/
  idempotency, concurrency, advisory-lock supersession races;
- migration: parent/revision, upgrade/downgrade/re-upgrade, clean chain, single
  head, schema/model agreement, constraints/indexes;
- security: cross-Organization/Project/Workspace/Object denial,
  protected-not-found, list/count leakage, inactive/nonmember roles, replay
  reauthorization, plaintext leakage;
- performance: bounded Project/Workspace lists, policy query counts,
  supersession depth, maximum page/content behavior.

Existing full backend regression is required but no existing test file may be
modified or weakened.

## 20. Validation Commands and Evidence

Implementation Plan may refine environment commands but must include:

- import/compile validation for every new module;
- focused tests for all nine new test files;
- adjacent authentication, Organization, Project, Workspace,
  EngineeringObject, Relationship, and Evidence tests;
- migration heads/history/current, upgrade/downgrade/re-upgrade and clean-chain
  validation in the approved isolated database;
- complete backend regression with zero failures;
- exact diff/file-scope review;
- schema/model comparison;
- prohibited-route/file/content-leak searches;
- `git diff --check`;
- QG-M1 final comparison with the actual diff.

## 21. Rollback and Forward Repair

Before delivery, prove:

- application rollback removes router registration and new modules only;
- database downgrade removes only the three Capture tables and owned objects;
- no governed Capture data exists before destructive downgrade outside an
  explicitly approved disposable test database;
- deployed environments with real Capture data require data-preserving forward
  repair rather than unapproved downgrade/data deletion;
- no historical migration rewrite is used.

## 22. Manifesto/File Traceability

| Principle group | Primary implementation evidence |
|---|---|
| Capture Once / Continuous Evolution | aggregate, command model, migration constraints, supersession tests |
| Human Authority / Evidence Before Assumption | trusted actor service/router, vocabulary, schemas, security tests |
| Engineering Context Is Sacred / Organizational Ownership | context validator, FKs, authorization, repository scope tests |
| Context Before Recommendation / Intelligence Before Automation | prohibited routes/fields and API tests |
| Explainability | provenance fields, events without content, history queries/tests |
| Provider Independence | absence of provider contracts/dependencies verified by diff review |
| Engineering First | Project-scoped APIs and acceptance/regression evidence |

## 23. Explicit Prohibitions

- any file outside Section 3;
- any field, table, route, command, event, error, or enum outside this IDS;
- Organization-wide or cross-scope Capture;
- client-provided trusted discipline/Organization/Creator/system state;
- content editing, restore, physical delete, generic mutation;
- content/reference/rationale in Audit/events/logs/errors;
- Evidence, approval, knowledge, AI, publishing, memory, file/OCR/search behavior;
- weakened authorization, tests, or migration history;
- commit, push, deployment, or protected-environment migration without separate
  authority.

## 24. Stop Conditions

Stop and return to governance if:

- Human IDS approval, plan acceptance, or READY IRR is absent;
- Alembic head differs from the approved IRR baseline;
- current source requires an unlisted file or semantic change;
- existing Workspace/Object discipline conventions cannot implement the exact
  mapping safely;
- complete authorized list totals cannot be produced without unbounded work;
- supersession concurrency cannot be protected inside one transaction;
- content leakage is found in any accountability/operational record;
- migration, security, atomicity, performance, adjacent, or full regression
  validation fails.

## 25. Current State

```text
EDS acceptance: ACCEPTED
IDS technical completeness: COMPLETE
IDS Human approval: APPROVED
Implementation Plan: ACCEPTED
Manifesto Alignment Verified: YES
QG-M1 Readiness Result: PASS
IRR-028: READY FOR IMPLEMENTATION — LINEAGE AMENDMENT REVIEWED
PATCH-028 implementation: READY TO RESUME AT SPRINT 2
```

## 26. Revision History

| Version | Date | Description |
|---|---|---|
| 0.1 | 2026-08-02 | Initial exact backend implementation contract. |
| 0.2 | 2026-08-03 | Focused lineage amendment replaced superseded head/parent e02600000001 with delivered single head e02810000001; no semantic, architecture, behavior, scope, file-set, or implementation change. |
| 0.3 | 2026-08-03 | Focused test-only amendment authorized exactly test_patch_028_1_migration.py to restore deterministic isolated-database state while preserving downgrade assertions; no runtime, migration, behavior, architecture, or PATCH scope change. |
| 0.4 | 2026-08-03 | Focused security-evidence amendment authorized four existing test files and conditional minimal correction in four existing runtime files; no semantic, endpoint, schema, migration, aggregate, or architecture expansion. |
