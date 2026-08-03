# EDS-028 — Universal Engineering Capture Foundation

## 1. Document Control

| Field | Value |
|---|---|
| Document ID | EDS-028 |
| Related PATCH | PATCH-028 v1.0 |
| Version | 0.1 |
| Status | ACCEPTED |
| Architecture | Docs-First / Domain-oriented modular architecture |
| Date | 2026-08-02 |

This EDS closes the engineering behavior required before IDS-028. It does not
authorize backend, migration, API, or test implementation.

### Approval Record

| Authority | Decision | Date |
|---|---|---|
| Product Owner | Accepted | 2026-08-02 |
| Architecture Guardian | Accepted | 2026-08-02 |

## 2. Governing Baseline

- SATCO Constitution and Engineering Intelligence Manifesto v1.0;
- accepted ADR-021 Engineering Intelligence Core Business Capability;
- PATCH-028 and AR-028 PASS;
- Engineering Intelligence Architecture v0.1;
- completed PATCH-023 through PATCH-027;
- Governance Model, Development Lifecycle, Framework v1.1, and QG-M1.

## 3. Engineering Design Objective

Define one independent aggregate that preserves bounded textual Engineering
Experience at its Project/work origin, with trusted Human provenance and
history, while making it impossible to confuse Capture with truth, Evidence,
approval, knowledge, recommendation, or Organizational Memory.

## 4. Aggregate and Layer Ownership

`EngineeringExperienceCapture` is a separate Aggregate Root. It owns:

- immutable UUID identity;
- immutable Organization, Project, optional Workspace, optional discipline,
  optional Engineering Object reference, original content, source kind,
  optional source reference, and Creator;
- lifecycle, supersession reference, version, timestamps, and Domain Events;
- content, context-shape, lifecycle, no-op, and supersession invariants;
- explicit commands and exactly-once version advancement.

Application owns:

- authenticated actor and active Organization derivation;
- authorization-before-disclosure;
- Project, Workspace, discipline, Engineering Object, and replacement
  reference validation;
- effective visibility policy;
- idempotency orchestration;
- Unit of Work coordination;
- Audit and Domain Event outbox recording;
- authorized response mapping.

Repositories own persistence only. Infrastructure implements inward-owned
ports. FastAPI transport validates syntax and maps stable contracts. Domain and
Application do not depend on FastAPI, HTTP, SQLAlchemy Session, Alembic, or
concrete infrastructure.

## 5. Aggregate State

| Field | Contract |
|---|---|
| `id` | immutable UUID |
| `organization_id` | immutable UUID, trusted active Organization |
| `project_id` | immutable positive integer, mandatory in Version 1 |
| `workspace_id` | immutable nullable positive integer |
| `discipline` | immutable nullable approved `Discipline`; derived from Workspace when present |
| `engineering_object_id` | immutable nullable EngineeringObject UUID |
| `source_kind` | immutable closed Version-1 value |
| `original_content` | immutable normalized Unicode text, 1–10,000 characters |
| `source_reference` | immutable nullable normalized text, 1–512 characters when present |
| `creator_id` | immutable authenticated active Human User integer |
| `lifecycle` | `captured`, `withdrawn`, or `superseded` |
| `superseded_by_capture_id` | nullable UUID; required only when superseded |
| `version` | positive integer, starts at 1 |
| `created_at` | immutable timezone-aware timestamp from trusted Clock |
| `updated_at` | timezone-aware timestamp from trusted Clock |

The aggregate owns no approval standing, reviewer, approver, confidence,
knowledge status, evidence standing, AI metadata, file metadata, tags, free-text
classification, or separately persisted confidentiality label.

## 6. Project, Workspace, Discipline, and Object Context

### Project requirement

Every Version-1 Capture is Project-scoped. Organization-wide Capture is
deferred because its applicability, confidentiality, ownership, and reuse
boundary are not yet sufficiently constrained.

The Project must:

- exist inside the authenticated active Organization;
- be visible to the actor;
- permit the actor to create or view Capture for the requested operation.

### Workspace and discipline

Workspace is optional for genuinely Project-wide experience. When present:

- it must belong to the same Project;
- the actor must be authorized in that Workspace;
- `discipline` is derived from the Workspace and cannot be supplied or changed
  independently by the client.

When Workspace is absent, discipline is null. Version 1 does not accept a
client-supplied Project-wide discipline because that would assert discipline
context without a governed Workspace boundary.

### Engineering Object reference

An optional Engineering Object reference is allowed only when:

- Workspace is present;
- the object belongs to the same Organization, Project, and Workspace;
- the object is visible to the actor;
- the object's discipline is compatible with the Workspace discipline;
- the object is not physically deleted or inaccessible under its governed
  lifecycle/visibility policy.

The reference provides subject context. It does not create an
EngineeringRelationship and does not mutate the object.

### Cross-scope prohibition

Cross-Organization, cross-Project, and cross-Workspace Capture context is
prohibited in Version 1. A Project-wide Capture cannot reference a Workspace or
object indirectly through source metadata.

## 7. Closed Source-Kind Vocabulary

| Value | Exact meaning |
|---|---|
| `observation` | a Human-observed engineering condition or occurrence |
| `question` | an unresolved engineering question |
| `assumption` | an explicitly identified working assumption, not a fact |
| `rationale` | reasoning expressed for consideration, not approval |
| `discussion_note` | a Human record of relevant engineering discussion |
| `correspondence_note` | experience derived from correspondence, with optional source reference |
| `field_note` | experience arising from site, inspection, installation, or commissioning activity |
| `review_note` | a review observation that is not itself a formal approval result |
| `outcome` | a recorded engineering outcome without declaring universal applicability |
| `lesson_candidate` | a possible lesson requiring later Human Review before reuse as knowledge |
| `external_record_note` | textual experience derived from an external record without copying managed content |

The vocabulary describes origin/intent, not truth or authority. Free-text,
tenant-defined, plugin-defined, and AI-inferred values are prohibited.

## 8. Text Normalization and Preservation

Before aggregate creation, the application contract performs deterministic
syntax normalization:

1. require a Unicode string;
2. convert CRLF and CR line endings to LF;
3. reject prohibited NUL/control characters except LF and horizontal tab;
4. trim leading and trailing Unicode whitespace from the complete value;
5. require 1–10,000 Unicode code points after normalization;
6. preserve internal whitespace, line breaks, wording, spelling, and language.

The normalized result becomes `original_content` and is immutable. SATCO does
not silently rewrite grammar, translate, summarize, redact, or enrich it.

`source_reference`, when present, is trimmed, must contain 1–512 Unicode code
points, must not contain NUL or line breaks, and is preserved as supplied after
normalization. It is an opaque citation/reference string, not a URL guarantee,
file locator, content ownership claim, or Evidence record.

Content hashing, duplicate detection by text similarity, automatic redaction,
language detection, and encryption policy beyond existing platform/database
controls are deferred.

## 9. Lifecycle and Transition Matrix

Lifecycle records whether the captured record remains usable as an active
capture record. It does not represent truth, Evidence standing, review,
approval, or knowledge authority.

| From | Allowed target | Command | Required information |
|---|---|---|---|
| creation | `captured` | `CreateEngineeringExperienceCapture` | content, source kind, Project, optional context/reference |
| `captured` | `withdrawn` | `WithdrawEngineeringExperienceCapture` | expected version and rationale |
| `captured` | `superseded` | `SupersedeEngineeringExperienceCapture` | expected version, rationale, replacement Capture UUID |
| `withdrawn` | none | — | terminal |
| `superseded` | none | — | terminal |

Every unlisted transition and self-transition is prohibited. Physical delete,
restore, generic lifecycle transition, generic update, and content edit are
prohibited.

Withdrawal states that the original capture should not be used as an active
input; it does not erase or falsify history. Supersession states that a separate
Capture provides the corrected or replacement expression. Neither operation
changes the original content or provenance.

## 10. Supersession Contract

The replacement Capture must:

- be distinct from the original;
- exist and remain lifecycle `captured`;
- have the same Organization, Project, Workspace, discipline, and Engineering
  Object context as the original;
- be visible to the authenticated actor;
- have been created before the supersession command commits;
- not already be superseded or withdrawn;
- not create a supersession cycle.

One active Capture may supersede at most one direct predecessor in Version 1.
A predecessor may be superseded exactly once. Supersession chains are allowed
but must be acyclic and bounded to a maximum validation depth of 20. Branching
and merging supersession graphs are prohibited.

Creating the replacement and superseding the predecessor are separate explicit
commands. The original supersession command atomically changes only the
predecessor Aggregate and records its Audit/Event/idempotency outcome after the
Application layer validates the replacement. It never mutates the replacement.

## 11. Commands and Idempotency

### CreateEngineeringExperienceCapture

Client may supply:

- Project ID;
- optional Workspace ID;
- optional Engineering Object UUID;
- source kind;
- original content;
- optional source reference;
- correlation UUID;
- idempotency UUID.

Server derives identity, Organization, Creator, discipline, lifecycle
`captured`, version 1, and timestamps. Creation accepts no expected version.

### WithdrawEngineeringExperienceCapture

Requires Capture UUID, positive expected version, rationale of 1–1000
characters, correlation UUID, and idempotency UUID. Only lifecycle `captured`
is eligible.

### SupersedeEngineeringExperienceCapture

Requires Capture UUID, distinct replacement Capture UUID, positive expected
version, rationale of 1–1000 characters, correlation UUID, and idempotency UUID.
Only lifecycle `captured` is eligible.

### Idempotency

Idempotency is scoped by Organization, authenticated actor, command type, and
idempotency UUID. Exact committed replay returns the previously authorized
result. Reuse with different normalized command content returns Idempotency
Conflict. Failed/uncommitted attempts do not create a successful replay record.

Every successful post-creation command increments aggregate version exactly
once. A no-op, stale version, invalid transition, invalid replacement, or
unauthorized command changes no state.

## 12. Responsibility and Human Authority

Creator is the authenticated Human who explicitly submits creation and is
immutable. Version 1 defines no separate steward, reviewer, or approver on the
Capture aggregate.

Only Creator or an authorized Human role with Project/Workspace capture
management permission may withdraw or supersede. Exact role/permission tokens
must be selected in IDS from existing authorization conventions; no client may
supply an actor or role.

AI, provider output, background automation, service accounts acting without an
accountable Human command, and inferred user identity cannot create, withdraw,
or supersede a Capture in Version 1.

Capture creation means only that the Human submitted the recorded expression.
It is not Human Approval of the engineering meaning.

## 13. Authorization, Confidentiality, and Disclosure

No independent confidentiality field is persisted in Version 1. Effective
visibility is the deny-by-default intersection of:

- authenticated active Organization access;
- Project visibility and operation permission;
- Workspace visibility and operation permission when scoped;
- referenced Engineering Object visibility when present;
- Capture lifecycle policy for the operation.

Authorization occurs before disclosure of Capture existence, UUID, content,
source reference, Creator, context identifiers, lifecycle, counts, or query
membership. Any inaccessible constituent returns Protected Not Found for
single-resource operations. List queries omit unauthorized records and totals
count only fully visible results.

Partial redaction is prohibited because content without its governed context
could mislead. Authorized responses return the complete bounded Capture view;
unauthorized responses return none of it.

Audit, Domain Events, logs, errors, idempotency conflict diagnostics, and
telemetry must not include `original_content` or `source_reference`. They may
carry Capture UUID, trusted scope identifiers, source kind, lifecycle, version,
actor, correlation, and timestamps only within their authorized operational
boundary.

## 14. Persistence and Atomicity

PostgreSQL is authoritative. One additive Alembic revision shall create:

- one Capture aggregate table;
- one Capture Domain Event outbox table;
- one Capture idempotency-result table;
- approved constraints and indexes only.

The existing Audit relation is reused through `entity_uuid`; no Audit schema
change is authorized by this EDS.

One SQLAlchemy-backed Unit of Work and one PostgreSQL transaction atomically
persist:

- aggregate insert or compare-and-change update;
- one accountable Audit record;
- durable Domain Events;
- idempotency outcome.

Repositories never authorize, commit, publish, perform generic updates, or
physically delete. Event publication occurs only after commit from the durable
outbox and cannot reapply the command.

Expected-version persistence must distinguish Protected Not Found from Version
Conflict without disclosing inaccessible existence.

## 15. Domain Events

Required past-tense events:

- `EngineeringExperienceCaptured`;
- `EngineeringExperienceCaptureWithdrawn`;
- `EngineeringExperienceCaptureSuperseded`.

Events include event/aggregate UUID, trusted Organization/Project/optional
Workspace/object scope, source kind, lifecycle, version, actor, correlation,
occurred-at, and replacement UUID when applicable. They exclude original
content, source reference, rationale text, secrets, provider data, and Evidence
payloads.

## 16. Required Ports

- `EngineeringExperienceCaptureRepository`;
- `EngineeringExperienceCaptureUnitOfWork`;
- `CaptureAuthorizationPolicy`;
- `CaptureContextValidator`;
- `CaptureSupersessionValidator`;
- `AuditRecorder`;
- `DomainEventRecorder`;
- `IdempotencyStore`;
- `Clock`.

IDS shall determine reuse versus specialization of existing generic protocols
without allowing Domain/Application to depend on concrete adapters.

## 17. Query Boundary

Approved query capabilities:

- get one authorized Capture by UUID;
- list Captures for one authorized Project;
- list Captures for one authorized Workspace;
- filter lists by lifecycle, source kind, Creator, and exact Engineering Object
  UUID;
- deterministic ordering by `created_at DESC, id DESC`;
- cursor or approved repository-standard pagination with maximum page size 100;
- retrieve a bounded supersession chain up to depth 20.

Queries are authorization-filtered before results/counts. Free-text search,
semantic search, similarity, cross-Project aggregation, arbitrary query
languages, analytics, and unbounded traversal are prohibited.

## 18. Transport Boundary

Conceptually approved endpoints, subject to exact IDS contracts:

- `POST /engineering-experience-captures`;
- `GET /engineering-experience-captures/{capture_id}`;
- `GET /projects/{project_id}/engineering-experience-captures`;
- `GET /engineering-workspaces/{workspace_id}/engineering-experience-captures`;
- `POST /engineering-experience-captures/{capture_id}/withdraw`;
- `POST /engineering-experience-captures/{capture_id}/supersede`;
- `GET /engineering-experience-captures/{capture_id}/supersession-chain`.

No PUT, generic PATCH, DELETE, upload, attachment, bulk import, AI, review,
approval, publish, or memory endpoint is allowed.

Responses include only authorized scalar state and deterministic
`allowed_actions`. `allowed_actions` explains current possibilities and is not
an authorization grant.

## 19. Stable Error Categories

- Validation Error;
- Authentication Required;
- Authorization Denied where policy permits disclosure;
- Protected Not Found;
- Version Conflict;
- Idempotency Conflict;
- Invalid Lifecycle Transition;
- Invalid Capture Context;
- Invalid Supersession;
- Duplicate Supersession;
- Supersession Cycle;
- Content Limit Exceeded;
- Internal Server Error.

Exact stable codes and HTTP mapping belong to IDS-028. Errors do not echo
original content, source reference, inaccessible identifiers, or internal
details.

## 20. Performance and Bounds

- original content maximum: 10,000 Unicode code points;
- source reference maximum: 512;
- rationale maximum: 1,000;
- page size maximum: 100;
- supersession-chain depth maximum: 20;
- all Project/Workspace lists require bounded pagination;
- indexes must support Organization/Project/Workspace scope, deterministic
  order, lifecycle/source-kind filtering, Creator/object filtering, and active
  supersession validation;
- performance tests must prove bounded query count and no per-result
  authorization/query amplification beyond the approved policy approach.

Exact latency thresholds require IDS to use the existing performance harness
and environment conventions rather than inventing an unrepeatable number.

## 21. Migration and Rollback

One additive revision is parented to the actual single Alembic head verified at
IRR. Upgrade creates only approved Capture/outbox/idempotency structures.
Downgrade removes only those structures and owned indexes/constraints.

Required evidence:

- upgrade, downgrade, and re-upgrade;
- clean-chain upgrade from base;
- one linear head;
- metadata/schema agreement;
- no modification of completed migration history;
- isolated test database only;
- no development/staging/production migration without separate authority.

## 22. Testing Requirements

### Domain and schema

- every invariant and lifecycle path;
- immutable content/provenance/context;
- normalization and bounds, including Unicode/control characters;
- closed source-kind vocabulary;
- no-op and terminal-state behavior;
- supersession compatibility, uniqueness, chain, and cycle limits;
- request rejection of trusted server-managed values.

### Repository and transaction

- full rehydration;
- expected-version compare-and-change;
- protected scope;
- deterministic bounded queries;
- atomic aggregate/Audit/outbox/idempotency success and staged rollback;
- exact idempotent replay and conflicting reuse;
- no content/reference leakage into Audit/events/logs.

### Application, API, and security

- trusted Organization/Creator/discipline derivation;
- Project/Workspace/Object compatibility;
- operation-specific authorization and protected-not-found;
- list/count visibility and cross-scope denial;
- stable errors and explicit endpoints;
- content returned only to fully authorized actors;
- AI/automation cannot issue authoritative commands.

### Migration and regression

- full migration sequence in an isolated database;
- focused Capture tests;
- authentication, Organization, Project, Workspace, EngineeringObject,
  Relationship, Evidence, and complete backend regression suites;
- no test weakening or skipped failure.

## 23. Manifesto Principle-to-Behavior Map

| Principle | Required EDS behavior |
|---|---|
| Engineering First | Only Engineering Experience in governed Project context is captured. |
| Capture Once | Original normalized content is immutable and later correction supersedes it. |
| Human Authority | Authenticated Human command; capture grants no approval or truth. |
| Engineering Context Is Sacred | Trusted Organization/Project/Workspace/discipline/object provenance remains attached. |
| Evidence Before Assumption | `assumption` is explicit; Capture remains distinct from Evidence/fact. |
| Context Before Recommendation | No recommendation exists; later use must resolve governed context. |
| Intelligence Before Automation | No autonomous capture, AI action, review, or publishing. |
| Explainability | Creator, origin, source reference, context, lifecycle, version, and history are traceable. |
| Provider Independence | No provider field, identity, state, or dependency exists. |
| Organizational Ownership | PostgreSQL canonical state is Organization-scoped and policy-controlled. |
| Continuous Evolution | Withdrawal and acyclic supersession preserve prior records. |

## 24. Explicit Non-Scope

All PATCH-028 non-scope remains binding, including files/OCR/document content,
Inbox UI, Human Review workflow, Evidence conversion, AI Author, approval,
publishing, Organizational Memory, automation, connectors, semantic/vector/
graph technology, frontend, cross-scope sharing, and unrelated refactoring.

Additionally excluded:

- Organization-wide Capture;
- manual Project-wide discipline assertion;
- tags, comments, reactions, collaboration threads, drafts, or autosave;
- persisted confidentiality classification;
- content encryption/redaction redesign;
- bulk commands and physical deletion.

## 25. Definition of Done for Design

EDS-028 is design-complete when:

- independent EDS Review is PASS;
- Product Owner and Architecture Guardian accept the behavioral contract;
- every AR-028 required decision is closed;
- QG-M1 principle coverage is PASS;
- IDS can define exact files/schema/API/tests without inventing behavior.

## 26. Current State

```text
EDS technical completeness: COMPLETE
Independent EDS Review: PASS
Human EDS acceptance: ACCEPTED
Manifesto Compliance: PASS
Manifesto Alignment Verified: NO
QG-M1 Readiness Result: PENDING
PATCH-028 implementation: NOT READY
```

## 27. Revision History

| Version | Date | Description |
|---|---|---|
| 0.1 | 2026-08-02 | Initial complete Engineering Experience Capture behavioral design. |
