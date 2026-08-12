# Implementation Plan-029 — Engineering Journal

## 1. Planning Foundation

### 1.1 Document Control

| Field | Value |
|---|---|
| Document ID | Implementation-Plan-029 |
| Related PATCH | PATCH-029 — Engineering Journal |
| Related EDS | EDS-029 — ACCEPTED / COMPLETE |
| Related IDS | IDS-029 — ACCEPTED / COMPLETE |
| Plan version | 0.2 |
| Publication scope | SECTIONS 1–8 COMPLETE |
| Plan status | ACCEPTED / EXECUTABLE |
| Planning authority | GRANTED |
| Independent Complete-Plan Review | PASS AFTER FOCUSED AMENDMENT |
| Human Implementation Plan Acceptance | PASS |
| Permission for IRR-029 | GRANTED |
| IRR-029 | PASS / READY FOR IMPLEMENTATION |
| Implementation execution | SPRINTS 1–3 COMPLETE / PASS |
| Independent Final Implementation Review | PASS |
| Human QG-11 | PASS |
| Permission for QG-12 | GRANTED |
| QG-12 | PASS |
| QG-12 delivery authorization | GRANTED FOR EXACT REVIEWED 21-FILE MANIFEST |
| Implementation authority | GRANTED BY IRR-029 / EXECUTED / HUMAN-ACCEPTED |
| Migration | NOT REQUIRED / NOT EXECUTED |
| Delivery commit | `b7fb8d4412d6b7528365f19b1418926aaa716686` |
| Push and remote verification | PASS / DIVERGENCE 0/0 |
| PATCH status | DONE / CLOSED |
| Date | 2026-08-03 |

This document is the subordinate execution-planning record for PATCH-029. This
publication contains Sections 1–8. It establishes the complete proposed plan and
grants no authority to implement, modify source code, create implementation
artifacts, create or execute migrations, commit, push, or deploy.

### 1.2 Governing Authorities

Implementation-Plan-029 is governed, in descending authority, by:

1. the SATCO Constitution;
2. SATCO Engineering Intelligence Manifesto v1.0;
3. accepted SATCO Architecture and applicable accepted ADRs;
4. the SATCO Governance Model and official Development Lifecycle;
5. the authoritative Roadmap and PATCH registry within their governed scope;
6. PATCH-029 — Engineering Journal;
7. AR-029 `PASS` and Human Architecture Acceptance `PASS`;
8. EDS-029 `ACCEPTED / COMPLETE`;
9. IDS-029 `ACCEPTED / COMPLETE`;
10. the completed Independent IDS Review and Human IDS Acceptance;
11. the current repository state.

This plan may sequence and constrain accepted design. It may not reinterpret,
weaken, broaden, or supersede a governing authority. Any conflict, omission, or
repository condition that prevents exact execution returns the plan to
architecture review.

### 1.3 Planning Principles

Planning shall:

- remain Docs-First and evidence-based;
- preserve the exact PATCH-029 boundary;
- treat Universal Capture as the sole canonical Capture authority;
- keep Engineering Journal read-only and presentation-only;
- preserve Human-first workflow and Human authority;
- preserve authorization-before-disclosure and protected-not-found behavior;
- preserve protected counts and list/detail disclosure separation;
- preserve the Project-less workspace shell without inferring Project scope;
- maintain inward dependency direction and request-scoped composition;
- use the current repository only to map accepted contracts, never to redefine
  them;
- stop when execution would require an authority not granted by accepted EDS-029
  and IDS-029.

Planning completeness must be demonstrated through explicit traceability,
bounded delivery sequencing, validation evidence, and review. Convenience does
not justify architectural expansion.

### 1.4 Delivery Philosophy

PATCH-029 delivery shall add the smallest coherent presentation capability that
realizes the accepted Journal design over existing canonical application
contracts. Delivery must preserve existing behavior and isolate Journal
composition from canonical ownership.

Progress is incremental and gate-controlled. A later delivery stage may begin
only when its prerequisites and the preceding stage's evidence are accepted.
Partial completion does not grant authority to expose incomplete behavior,
simulate unavailable capabilities, or bypass a governing boundary.

The Journal shall remain reconstructible from current authorized canonical
state. Delivery must not introduce duplicated Capture state, durable Journal
state, or an alternative authority path.

### 1.5 Overall Sprint Strategy

The executable plan will use a dependency-ordered, bounded Sprint sequence
derived from IDS-029. Each Sprint will have an explicit entry gate, exit gate,
review checkpoint, authorized boundary, validation obligation, and stop
condition.

Sprint boundaries separate concerns sufficiently to prove architecture before
integration while preserving end-to-end traceability. No Sprint may borrow
authority, scope, or artifacts from a later Sprint. Sections 4–6 define exactly
three Sprints, and Sections 7–8 define their cumulative validation, review,
delivery, and closure obligations.

### 1.6 Quality Gate Philosophy

Quality Gates are cumulative evidence boundaries, not procedural formalities.
Passing a later gate does not waive an earlier failure. A gate passes only when
its required architectural, security, behavioral, regression, scope, and
governance evidence is complete and reproducible.

The plan shall preserve the accepted IDS-029 Quality Gate model, including
Manifesto alignment, exact-boundary verification, authorization and disclosure
safety, dependency-direction protection, regression integrity, independent
review, Human acceptance, and final delivery authorization. Gate evidence must
reflect the actual repository state under review.

No plan status, test result, or review outcome alone grants implementation
authority. Implementation may begin only after the complete plan is accepted
and IRR-029 records `READY FOR IMPLEMENTATION` under the governing lifecycle.

### 1.7 Relationship to EDS-029 and IDS-029

EDS-029 defines the accepted Engineering Journal architecture, Human workflow,
authority boundaries, view meaning, and canonical relationships. IDS-029
defines the accepted application, port, projection, security, transport,
performance, testing, Quality Gate, and delivery contracts.

Implementation-Plan-029 is subordinate to both. It may translate those
contracts into executable sequencing, repository boundaries, validation, and
handoff evidence only after the corresponding plan sections are reviewed. It
must not create product meaning, architecture, API semantics, DTO semantics,
authority, or persistence assumptions.

Where EDS-029 states architectural intent and IDS-029 states an exact contract,
the plan must satisfy both. If the current repository cannot do so without a
contract change, planning stops and the affected governing document returns to
its approval path.

### 1.8 Explicit Non-Goals

Implementation-Plan-029 does not authorize or plan:

- a Journal Aggregate, Repository, Unit of Work, persistence model, table,
  migration, or independent lifecycle;
- duplication, replacement, forking, or caching-as-authority of Universal
  Capture;
- Capture mutation or alteration of completed PATCH-028 contracts by
  implication;
- Review, approval, rejection, qualification, publication, or Organizational
  Memory authority;
- Engineering Knowledge Graph behavior or expansion;
- AI behavior, provider integration, generation, classification,
  recommendation, or autonomous action;
- a separate Knowledge Inbox capability;
- additional Journal views, generic operations, or unrelated refactoring;
- implementation source, APIs, DTOs, routes, tests, migrations, delivery
  artifacts, commits, pushes, or deployments within Section 1.

### 1.9 Planning Constraints

1. Only accepted governing documents and the current repository may inform the
   plan.
2. Universal Capture identity, provenance, context, version, lifecycle, and
   history remain canonical and unchanged.
3. Journal composition remains read-only, presentation-only, request-scoped,
   and nonpersistent.
4. Authorization precedes every disclosure of scope, view availability, item,
   field, count, navigation target, and related identity.
5. Protected-not-found semantics remain stable across missing and unauthorized
   resources.
6. Counts remain post-authorization projections with the exact accepted IDS-029
   meanings.
7. List and detail projections remain separate, and list composition must not
   require detail-only plaintext.
8. Project-less shell behavior must not infer a Project or query Capture
   members or counts.
9. Universal Capture and other canonical capabilities must never depend on
   Engineering Journal.
10. Transport remains thin and cannot acquire application, authorization, or
    canonical authority.
11. No future capability may be simulated when its canonical authority is
    unavailable.
12. Sections 1–8 require complete-plan architecture review and Human acceptance
    before IRR-029 may be created.
13. Implementation Plan-029 remains non-executable until Sections 1–8 are
    reviewed and accepted.
14. Implementation remains prohibited until IRR-029 explicitly records `READY
    FOR IMPLEMENTATION`.

### 1.10 Section 1 Decision

```text
Publication scope: SECTIONS 1–8 COMPLETE
Section 1 completeness: COMPLETE — PROPOSED
Governing authority chain: DEFINED
Planning principles: DEFINED
Delivery philosophy: DEFINED
Sprint count and sequencing: THREE / DEFINED IN SECTIONS 4–6
Exact files: DEFINED IN SECTION 3
Transport contract mapping: DEFINED IN SECTION 6
Implementation tasks: DEFINED IN SECTIONS 4–6
Validation: DEFINED IN SECTION 7
Implementation Plan status: ACCEPTED / EXECUTABLE
Human Implementation Plan Acceptance: PASS
Permission for IRR-029: GRANTED
Permission for complete-plan review: GRANTED
Implementation authority: NOT GRANTED
```

## 2. Repository Inventory and Dependency Mapping

### 2.1 Inventory Basis

This inventory maps accepted IDS-029 contracts to the current repository. It
records existing capabilities and bounded gaps only. It does not authorize an
implementation edit, infer missing behavior, or transfer canonical ownership
to Engineering Journal.

### 2.2 Current Relevant Backend Structure

| Existing area | Current role relevant to PATCH-029 |
|---|---|
| `backend/app/models/engineering_experience_capture.py` | Canonical Universal Capture Aggregate and persisted state; read-only dependency and prohibited from modification |
| `backend/app/models/engineering_experience_capture_command.py` | Canonical Capture command and internal actor contracts; Journal must not reuse or modify them as its identity contract |
| `backend/app/enums/engineering_experience_capture.py` | Canonical Capture lifecycle and source-kind vocabulary |
| `backend/app/schemas/engineering_experience_capture.py` | Existing full Capture request, response, filter, list, and supersession-chain contracts |
| `backend/app/ports/engineering_experience_capture.py` | Canonical Capture repository and application-policy contracts |
| `backend/app/repositories/engineering_experience_capture_repository.py` | Organization- and Project-scoped canonical persistence reads and writes; currently returns full Aggregate rows and one total |
| `backend/app/repositories/engineering_experience_capture_unit_of_work.py` | Existing Capture authorization, context validation, and transactional write composition |
| `backend/app/services/engineering_experience_capture_service.py` | Canonical authorized Capture application boundary for read, list, create, withdraw, supersede, and chain operations |
| `backend/app/api/v1/routers/engineering_experience_captures.py` | Existing Universal Capture transport, including the canonical New Capture destination |
| `backend/app/models/project.py` | Canonical Project state and Organization ownership; prohibited from modification |
| `backend/app/repositories/project_repository.py` | Existing Organization-scoped Project queries; currently lacks a bounded actor-authorized selection query |
| `backend/app/services/project_service.py` | Existing canonical Project application boundary; currently exposes Organization-scoped listing rather than the protected Project-selection projection required by IDS-029 |
| `backend/app/models/engineering_workspace.py` | Canonical Workspace state and membership used by existing authorization policies; prohibited from modification |
| `backend/app/services/engineering_workspace_service.py` | Existing authorized Workspace application behavior; no Journal behavior belongs here |
| `backend/app/dependencies/auth.py` | Trusted authenticated User and active Organization context required by Journal transport; reusable unchanged |
| `backend/app/exceptions/handlers.py` | Existing stable SATCO exception envelope handling; reusable unchanged |
| `backend/app/main.py` | Application router registration point |
| `backend/tests/` | Existing Capture, authentication, Organization, Project, Workspace, Engineering Object, Relationship, Evidence, Audit, and regression evidence |

There is no existing Engineering Journal module, Aggregate, Repository, Unit of
Work, persistence model, migration, service, schema, port, adapter, router, or
test file.

### 2.3 Existing Universal Capture Contracts

The following existing contracts remain canonical and reusable:

- canonical Capture UUID, Project, optional Workspace, discipline, optional
  Engineering Object, source kind, lifecycle, version, timestamps, Creator,
  source reference, content, and supersession identity;
- `EngineeringExperienceCaptureService.get` for authorized detail resolution;
- Project- and Workspace-scoped canonical list authorization behavior;
- `SqlAlchemyCaptureAuthorizationPolicy` scope rules;
- `SqlAlchemyCaptureContextValidator` Project, Workspace, discipline, and
  Engineering Object compatibility rules;
- protected-not-found behavior and the existing SATCO error envelope;
- canonical New Capture route and command authority;
- deterministic Capture ordering by `created_at` and UUID.

Journal must consume these meanings through Journal-owned ports and bounded
adapters. It must not call a Capture command, construct a Capture Unit of Work,
or reinterpret canonical lifecycle values.

### 2.4 Reusable Authorization and Context Components

| Existing component | Permitted reuse |
|---|---|
| `get_current_user_organization_context` | Build the trusted request actor and active Organization scope; client input cannot replace it |
| Journal-owned authenticated-actor projection | Carry only actor identifier and trusted server-derived Organization identifier; canonical adapters translate it privately into their own actor contracts |
| Capture authorization policy behavior | Preserve active User, active Organization membership, Project, Workspace, Engineering Object, and role-sensitive access semantics through canonical application contracts |
| Capture context validation behavior | Validate optional Workspace and Engineering Object refinements within the selected Project |
| Project ownership and Workspace membership models | Remain canonical inputs behind existing application and policy boundaries; never exposed to Journal application code as ORM state |
| `SatcoException` handling | Preserve stable protected-not-found and validation envelopes at transport |

Reuse is behavioral and contract-bound. Journal application code may depend
only on Journal-owned ports and transport-neutral DTOs. Concrete canonical
services and persistence collaborators may be connected only inside the
request-scoped infrastructure composition boundary.

The Journal actor contract is `EngineeringJournalAuthenticatedActor`, owned by
`backend/app/schemas/engineering_journal.py`. It contains only the authenticated
actor identifier and trusted active Organization identifier. Neither value may
come from Journal request bodies, query parameters, or path parameters.
Canonical adapters may translate this neutral projection into their producing
capability's private actor type. Journal must not reuse
`EngineeringExperienceCaptureActor`, and canonical command models must not be
modified merely to serve Journal.

### 2.5 Required Contract Extensions

The current repository requires exactly two bounded read extensions to satisfy
accepted IDS-029 without direct persistence access or excess disclosure.

#### Canonical Capture Read Extension

The existing Capture list returns full Capture responses, including plaintext
content and source reference, and exposes one `total`. IDS-029 requires a
minimal list projection and one bounded result containing
`authorized_total`, `filtered_total`, and `visible_total`.

The permitted extension shall:

- add a canonical application-level bounded read operation used through the
  Journal-owned Capture read port;
- select only IDS-029 list fields for list composition;
- calculate both protected pre-filter and post-filter totals without loading an
  unbounded result set;
- retain existing Organization, Project, Workspace, Engineering Object,
  lifecycle, and actor authorization;
- leave existing Capture DTOs, routes, commands, Aggregate, lifecycle, writes,
  Unit of Work, and persistence semantics unchanged.

Universal Capture owns the application result contracts it produces:

- `EngineeringExperienceCaptureSummaryResult`;
- `EngineeringExperienceCaptureDetailResult`;
- `EngineeringExperienceCaptureReadPageResult`.

They reside in `backend/app/schemas/engineering_experience_capture.py` and are
returned only by the canonical Capture application service. The page result
contains typed summary items, `authorized_total`, `filtered_total`,
`visible_total`, page, and size. These types contain no ORM rows, untyped
mappings, Journal DTOs, or Journal presentation state. Existing Capture DTOs
and routes remain unchanged.

A request-scoped Journal Capture adapter may internally construct the existing
canonical Capture service and the `uow_factory` that service requires. The
resulting canonical Capture Unit of Work remains private to Universal Capture.
Journal owns no Unit of Work or transaction and cannot access, commit, roll
back, coordinate, or expose the canonical Unit of Work. These read operations
must produce no Audit record, outbox event, idempotency record, Aggregate
mutation, flush, commit, or other canonical write effect.

#### Protected Project-Selection Extension

The existing Project list is Organization-scoped but does not provide the
actor-authorized, bounded Project-selection projection required for the
Project-less Journal shell.

The permitted extension shall:

- add one bounded canonical Project application read operation;
- apply the existing Project/Workspace access rules before returning a choice;
- return only the canonical Project identifier and approved display name,
  preserving its representation exactly as defined by the canonical Project
  capability without redefinition or transformation;
- use deterministic display-name and identifier ordering;
- expose no inaccessible Project, hidden total, membership reason, or
  cross-Organization suggestion;
- leave existing Project endpoints, DTOs, mutation behavior, persistence
  semantics, and authorization rules unchanged.

The one canonical application-owned contract is
`ProjectService.list_authorized_selection`. It accepts the canonical
capability's actor context, trusted server-derived Organization scope, positive
page, and size from `1` through `100`. It owns application authorization and
adapts existing Project, Workspace, and membership visibility behavior without
depending on Universal Capture or duplicating policy in Journal.

Project owns `ProjectAuthorizedSelectionItem` and
`ProjectAuthorizedSelectionPage` in `backend/app/schemas/project.py`. The item
contains only canonical Project identifier and approved display name. The page
contains typed items, page, size, `visible_total`, and `has_more`; it contains no
global or hidden total. It contains no ORM row, untyped mapping, Journal DTO, or
authorization diagnostic.

For more than 100 authorized Projects, the client requests the next positive
page with the same bounded size. Ordering is display name ascending and then
canonical Project identifier ascending. Every page request rebuilds trusted
Organization and actor context and reauthorizes visibility. Page continuation
cannot change Organization or actor scope, and the Journal never automatically
selects a Project.

Neither extension creates a Journal repository or permits Journal application
code to import a canonical repository.

### 2.6 Dependency Order

```text
Accepted Journal vocabularies and DTO contracts
        ↓
Journal-owned ports and stable application outcomes
        ↓
Bounded canonical Capture and Project read extensions
        ↓
Journal infrastructure adapters over canonical application boundaries
        ↓
Journal application composition and security
        ↓
Request-scoped transport composition and router registration
        ↓
Focused, adjacent, and complete regression evidence
```

Universal Capture, Project, Workspace, Engineering Object, authentication, and
Organization capabilities never depend on Engineering Journal.

### 2.7 Confirmed Implementation Blockers

No confirmed implementation blocker remains in the approved Sections 1–4
planning boundary.

The following current-state differences are planned later-Sprint dependencies,
not blockers or authority to improvise:

1. the current Capture list contract loads detail-only plaintext and returns
   only one total;
2. the current Project list contract does not express actor-authorized Project
   selection for the Project-less shell.

The focused IDS-029 amendment resolves Project identity by requiring Journal to
preserve the identifier exactly as defined by the canonical Project capability.
Journal owns no identity format and no Project migration, UUID addition, model
change, or translation identity is required or authorized.

The two bounded read extensions remain ordered dependencies for later
composition. If either cannot be implemented using only the exact files and
semantics authorized in Section 3, work stops and returns to architecture
review.

### 2.8 Prohibited Reuse Patterns

The implementation must not:

- import a canonical repository, ORM model, SQLAlchemy Session, or Unit of Work
  into Journal schemas, ports, or application service;
- query Capture, Project, Workspace, Engineering Object, membership, or User
  tables from Journal application or transport;
- reuse the full Capture list response and discard plaintext only after it has
  been loaded for Journal listing;
- expose ProjectService Organization-wide results as authorized Journal
  Project choices;
- instantiate the Capture Unit of Work as a Journal transaction boundary;
- call Capture create, withdraw, supersede, or any other mutation from Journal;
- import Journal contracts into canonical Domain or model modules;
- treat router dependency wiring as authorization;
- convert protected absence into an empty result;
- persist DTOs, view membership, counts, preferences, navigation, freshness, or
  capability availability;
- add a Journal Repository, Unit of Work, Aggregate, table, migration, or cache
  as authority.

### 2.9 Section 2 Decision

```text
Repository inventory: COMPLETE
Canonical dependencies: IDENTIFIED
Reusable security/context behavior: IDENTIFIED
Required bounded read extensions: TWO
Unresolved Sprint 1 blocker: NONE
Later-Sprint bounded read dependencies: RECORDED
Direct persistence workaround: PROHIBITED
Architecture expansion: NONE
Implementation authority: NOT GRANTED
```

## 3. Exact Delivery Scope

### 3.1 Scope Rule

The files below are the complete PATCH-029 implementation boundary proposed for
review. Every file is mandatory; none is optional or speculative. No file may
be substituted, added, or removed without plan amendment, architecture review,
and acceptance before implementation.

### 3.2 Exact Files to Create

| File | Purpose | IDS-029 traceability |
|---|---|---|
| `backend/app/enums/engineering_journal.py` | Closed six-view, availability, result-state, navigation-target, presentation-sort, and layout vocabularies | 4.2, 4.10, 8.3 |
| `backend/app/schemas/engineering_journal.py` | Neutral authenticated-actor projection and strict transport-neutral workspace, scope, Journal projection, count, empty-state, navigation, and presentation DTOs; no canonical service result ownership | 3.1–3.10, 4.1–4.11, 5.1–5.8, 8.3 |
| `backend/app/ports/engineering_journal.py` | Journal-owned scope authorization, Project selection, Capture read, Capture navigation, and capability-availability ports with exact request/result/outcome contracts | 3.1–3.10, 5.1–5.6, 8.3 |
| `backend/app/exceptions/engineering_journal.py` | Stable protected-not-found, invalid-presentation, and internal capability outcome categories without protected diagnostics | 3.7–3.8, 5.6, 6.4 |
| `backend/app/adapters/__init__.py` | Declare the infrastructure-adapter package boundary without exports or behavior | 1.5, 2.8, 3.1, 6.3 |
| `backend/app/adapters/engineering_journal.py` | Adapt approved canonical Capture and Project application reads to Journal-owned ports without direct persistence or ownership transfer | 3.2–3.6, 5.2–5.5, 6.3, 8.4 |
| `backend/app/services/engineering_journal_service.py` | Read-only Journal orchestration, deterministic view composition, protected counts, unavailable views, detail inspection, navigation, and freshness mapping | 1.4, 2.1–2.9, 5.1–5.13, 8.4 |
| `backend/app/api/v1/routers/engineering_journal.py` | Thin three-operation Journal transport and request-scoped composition | 6.1–6.4, 6.12, 8.5 |
| `backend/tests/test_engineering_journal_contracts.py` | Vocabulary, DTO, port-shape, count, projection-separation, and prohibited-dependency evidence | 7.2–7.7, 7.14, 8.3 |
| `backend/tests/test_engineering_journal_service.py` | View membership, Project-less shell, unavailable capability, detail, navigation, refresh, ordering, and composition evidence | 7.3–7.5, 7.8–7.11, 8.4 |
| `backend/tests/test_engineering_journal_security.py` | Authorization-before-disclosure, protected-not-found, count protection, field disclosure, cross-scope, and plaintext-exclusion evidence | 7.4–7.10, 7.15, 8.4 |
| `backend/tests/test_engineering_journal_api.py` | Exact route, validation, response, outcome mapping, request-scoped composition, and prohibited-route evidence | 7.12, 7.14–7.15, 8.5 |
| `backend/tests/test_engineering_journal_performance.py` | Bounded operation, query-count, no-N+1, list-field minimization, and Project-less/unavailable no-query evidence | 6.5–6.7, 7.13, 8.4–8.5 |

### 3.3 Exact Files Permitted to Modify

| File | Permitted change only | IDS-029 traceability |
|---|---|---|
| `backend/app/ports/engineering_experience_capture.py` | Add the minimum canonical repository-side read contract needed to support a bounded minimal projection and protected three-total result; no write-port change | 3.3–3.6, 6.7 |
| `backend/app/schemas/engineering_experience_capture.py` | Add canonical typed Capture summary, detail, and paginated read result contracts; preserve every existing Capture DTO | 3.3–3.4, 4.6–4.7, 6.7 |
| `backend/app/repositories/engineering_experience_capture_repository.py` | Add the bounded selected-field and protected-count query behind the canonical application boundary; no commit, authorization, generic update, or existing-method change | 3.3–3.6, 6.5–6.7 |
| `backend/app/services/engineering_experience_capture_service.py` | Add the authorized application-level minimal list read consumed by the Journal adapter; preserve all existing methods and DTOs | 1.6, 3.3–3.4, 5.2–5.3 |
| `backend/app/repositories/project_repository.py` | Add one bounded deterministic query supporting actor-authorized Project choices; no mutation or existing-query change | 3.2, 4.4, 5.3, 6.5 |
| `backend/app/schemas/project.py` | Add canonical typed actor-authorized Project-selection item and bounded page results; preserve every existing Project DTO | 3.2, 4.4, 5.3, 6.5 |
| `backend/app/services/project_service.py` | Add one protected application-level Project-selection read that applies existing access rules and returns only the approved choice projection | 3.2, 4.4, 5.3 |
| `backend/app/main.py` | Import and register only the Engineering Journal router | 6.2–6.3, 8.5 |

### 3.4 Files Explicitly Prohibited

The following files and file groups are outside PATCH-029 implementation scope:

- every file under `backend/app/models/`;
- every file under `backend/migrations/`;
- `backend/app/repositories/engineering_experience_capture_unit_of_work.py`;
- `backend/app/api/v1/routers/engineering_experience_captures.py`;
- `backend/app/dependencies/auth.py`;
- `backend/app/services/engineering_workspace_service.py`;
- `backend/app/repositories/engineering_workspace_repository.py`;
- every existing API router other than the single registration line permitted
  in `backend/app/main.py`;
- every existing test file;
- every frontend, AI, Knowledge Graph, Review, Organizational Memory, search,
  audit, Evidence, Relationship, and unrelated Core module.

No model export, schema export, enum export, port export, metadata import,
migration environment, configuration, dependency module, or test bootstrap
change is authorized.

### 3.5 Cross-File Traceability

| Accepted IDS capability | Authorized realization |
|---|---|
| Controlled Journal vocabulary | Journal enum, schema, and contract-test files |
| Transport-neutral projections | Journal schema and contract-test files |
| Journal-owned ports | Journal port and contract-test files |
| Neutral Journal actor | Journal schema and port files; private translation inside canonical adapters |
| Canonical minimal Capture read | Canonical Capture schema/port/repository/service files plus Journal adapter; result ownership remains Universal Capture |
| Project-less protected Project selection | Canonical Project schema/repository/service files plus Journal adapter; result ownership and visibility remain Project |
| Read-only application composition | Journal service and service/security/performance tests |
| Request-scoped composition | Journal adapter and router |
| Thin transport and stable outcomes | Journal router, API tests, and one `main.py` registration |
| Security and disclosure evidence | Contract, service, security, API, and performance tests |
| Persistence, migration, mutation, or independent authority | No authorized file |

### 3.6 Scope Decision

```text
Files to create: THIRTEEN
Files permitted to modify: EIGHT
Optional files: NONE
Speculative files: NONE
Journal model files: NONE
Journal repository files: NONE
Journal Unit of Work files: NONE
Migration files: NONE
Existing test modifications: NONE
Canonical result-contract files: TWO MODIFIED / OWNERSHIP PRESERVED
Scope expansion authority: NONE
Implementation authority: NOT GRANTED
```

## 4. Sprint 1 Execution Plan — Contracts and Projection Foundation

### 4.1 Objective

Establish the complete framework-independent Journal vocabulary,
transport-neutral DTOs, stable outcomes, and inward-owned read ports required
by accepted IDS-029. Sprint 1 introduces no adapter, application service,
transport, canonical contract extension, persistence, or integration behavior.

### 4.2 Entry Gates

Sprint 1 implementation may begin only when all are true:

1. Sections 1–4 of Implementation-Plan-029 have passed architecture review and
   Human acceptance;
2. the remaining Implementation Plan sections are complete and the full plan
   is accepted as executable;
3. IRR-029 records QG-M1 Readiness `PASS` and `READY FOR IMPLEMENTATION`;
4. PATCH-029, EDS-029, and IDS-029 remain accepted and unchanged in meaning;
5. the exact Section 3 file boundary is authorized;
6. current repository and worktree state are recorded without modifying or
   absorbing unrelated changes;
7. no unresolved blocker or superseding governance decision exists;
8. the focused IDS-029 Project-identity amendment remains accepted and Journal
   preserves the canonical Project identifier without transformation.

Failure of any entry gate stops Sprint 1 before source modification.

### 4.3 Exact Deliverables

Sprint 1 may create only:

- `backend/app/enums/engineering_journal.py`;
- `backend/app/schemas/engineering_journal.py`;
- `backend/app/ports/engineering_journal.py`;
- `backend/app/exceptions/engineering_journal.py`;
- `backend/tests/test_engineering_journal_contracts.py`.

Sprint 1 modifies no existing file. Its deliverables are limited to:

- the six approved Journal views;
- approved availability, result-state, navigation-target, sort, and layout
  vocabularies;
- the neutral `EngineeringJournalAuthenticatedActor` projection containing only
  actor identifier and trusted active Organization identifier;
- immutable strict DTOs for workspace, optional-Project scope, bounded Project
  selection, list/detail Capture projections, protected counts, empty and
  unavailable states, navigation, presentation criteria, and Capture page
  results;
- Journal-owned scope authorization, Project selection, Capture read, Capture
  navigation, and capability-availability port contracts;
- stable Journal application outcomes with no protected diagnostics;
- focused contract evidence.

### 4.4 Ordered Implementation Tasks

1. Define only the closed IDS-029 vocabularies with no aliases or additional
   values.
2. Define the strict immutable neutral Journal actor projection without any
   canonical command-model dependency.
3. Define strict immutable primitive and scope DTOs, including Project absence
   only for the Project-less shell.
4. Define Journal-side Project-selection projection DTOs without claiming
   ownership of the canonical Project result contract or exposing a hidden or
   global total.
5. Define minimal Capture list and authorized Capture detail Journal DTOs as separate
   types.
6. Define the three-level count DTO and enforce deterministic relationships
   among `authorized_total`, `filtered_total`, and `visible_total`.
7. Define empty, unavailable, navigation, freshness, and workspace-composition
   DTOs.
8. Define the closed presentation criteria, defaults, bounds, logical-AND
   filter meaning, and rejection of unknown criteria.
9. Define Journal-owned read ports with exact neutral actor, scope, request, result,
   and protected outcome types; expose no ORM, Session, repository, Unit of
   Work, or framework type.
10. Define stable Journal exceptions and safe messages consistent with the
   existing SATCO exception envelope.
11. Add the focused contract tests and run the Sprint 1 validation sequence.

No task may introduce application orchestration, adapter implementation,
canonical service calls, route behavior, or persistence.

### 4.5 Exact Tests

`backend/tests/test_engineering_journal_contracts.py` must prove:

1. the view vocabulary contains exactly `new_capture`, `inbox`, `drafts`,
   `under_review`, `published`, and `superseded`;
2. availability, result-state, navigation-target, sort, and layout vocabularies
   contain only IDS-029 values;
3. every request and DTO forbids unknown fields and validates bounds;
4. Project may be absent only in a Project-less shell and all subordinate scope
   is then absent;
5. member-bearing content requires an authorized Project scope;
6. Project-selection pages are bounded, deterministic in shape, and contain no
   global total or access diagnostic;
7. list projections cannot contain original content, source reference,
   rationale, complete Creator detail, or authorization diagnostics;
8. detail projections are distinct and may carry only explicitly authorized
   detail fields;
9. `authorized_total`, `filtered_total`, and `visible_total` reject negative or
   incoherent combinations;
10. no-filter count semantics require `filtered_total` to equal
    `authorized_total`;
11. unavailable views and protected-not-found outcomes cannot carry count or
    member disclosure;
12. presentation defaults are page `1`, size `20`, `created_at_desc`, and
    `list`;
13. page size above `100`, nonpositive page or size, grouping, free text,
    unsupported sort/layout, unknown fields, and incoherent criteria fail;
14. freshness contains only authorized returned-page version information and is
    absent without Capture members;
15. navigation grants no access and requires reauthorization for canonical or
    cross-capability destinations;
16. Journal port definitions contain no concrete infrastructure or framework
    dependency;
17. the Journal actor contains only actor and trusted Organization identifiers,
    and imports no canonical command actor;
18. stable exception codes and status meanings match IDS-029 without protected
    identifiers or diagnostics;
19. DTOs are nonpersistent and contain no Journal identity, lifecycle, Review,
    Organizational Memory, Knowledge Graph, or AI field.

### 4.6 Static and Prohibited-Pattern Checks

Sprint 1 validation must include:

- Python compile and import checks for the five Sprint 1 files;
- exact enum-member inspection;
- Pydantic schema inspection for strictness, immutability, and field boundary;
- type-hint inspection for complete port request/result contracts;
- search proving no import of `fastapi`, `sqlalchemy`, `Session`, Alembic,
  canonical repository implementations, or Unit of Work implementations in
  Journal enums, schemas, ports, or exceptions;
- search proving no `commit`, `rollback`, `flush`, `add`, `delete`, generic
  update, SQL expression, route decorator, or HTTP dependency exists in Sprint
  1 production files;
- search proving no Journal Aggregate, Repository, Unit of Work, ORM table,
  lifecycle, Review, Organizational Memory, Knowledge Graph, or AI authority is
  declared;
- QG-6 positive evidence: exact type and import inspection proves no Journal
  Aggregate class, aggregate command, or Journal lifecycle vocabulary exists;
- QG-7 positive evidence: exact file, import, and metadata inspection proves no
  Journal persistence, Repository, Unit of Work, table, ORM model, migration,
  commit, rollback, flush, or database session exists;
- exact diff-scope verification against the five Sprint 1 files;
- `git diff --check` for the Sprint 1 boundary.

### 4.7 Exit Gates

Sprint 1 passes only when:

- all exact contract tests pass;
- compile and import checks pass;
- controlled vocabularies exactly match IDS-029;
- Project-less and member-bearing scope invariants pass;
- count semantics pass;
- list/detail separation passes;
- stable protected outcomes pass;
- QG-6 no Journal Aggregate or lifecycle is `PASS`;
- QG-7 no Journal persistence boundary is `PASS`;
- all static and prohibited-pattern checks pass;
- no file outside the five-file Sprint 1 boundary changed for Sprint 1;
- QG-M1 Sprint checkpoint passes;
- Independent Sprint 1 Review records `PASS`;
- no blocker remains for the accepted Sprint 1 contract boundary.

Passing Sprint 1 does not authorize Sprint 2 or implementation beyond the
Sprint 1 boundary.

### 4.8 Stop Conditions

Stop Sprint 1 immediately if:

- an accepted view, DTO, count, scope, presentation, outcome, or port contract
  is ambiguous or contradictory;
- Project-less behavior requires Project inference;
- list DTOs require detail-only plaintext;
- a protected outcome requires existence or authorization diagnostics;
- a port requires ORM, Session, repository implementation, Unit of Work,
  FastAPI, HTTP, or persistence knowledge;
- a Journal Aggregate, Repository, Unit of Work, persistence model, migration,
  lifecycle, or durable preference appears necessary;
- a new vocabulary value, view, capability, or authority appears necessary;
- any Sprint 1 test, static check, QG-M1 checkpoint, or exact-scope check fails;
- implementation would modify an existing file or create a sixth Sprint 1 file;
- current repository state conflicts with an accepted authority.

No workaround may be invented inside Sprint 1. The finding returns to the
appropriate architecture or governance review.

### 4.9 Expected Output

```text
Sprint 1 implementation status: PASS or BLOCKED
Files created: EXACTLY FIVE OR NONE
Files modified: NONE
Contract tests: PASS or BLOCKED
Static architecture checks: PASS or BLOCKED
Prohibited-pattern checks: PASS or BLOCKED
QG-M1 Sprint checkpoint: PASS or BLOCKED
QG-6 no Aggregate/lifecycle: PASS or BLOCKED
QG-7 no persistence boundary: PASS or BLOCKED
Independent Sprint 1 Review: PASS or NOT PERMITTED
Remaining findings: EXPLICIT
Permission to begin Sprint 2: NOT GRANTED BY SECTION 4
```

### 4.10 Sections 2–4 Decision

```text
Repository inventory: COMPLETE — PROPOSED
Exact delivery scope: COMPLETE — PROPOSED
Sprint 1 execution plan: COMPLETE — PROPOSED
Sprint 1 planning status: UNBLOCKED / PROPOSED
Confirmed blocker: NONE
Later Sprint plans: DEFINED IN SECTIONS 5–6
Implementation Plan status: ACCEPTED / EXECUTABLE
Permission for complete-plan review: GRANTED
Implementation authority: NOT GRANTED
```

## 5. Sprint 2 Execution Plan — Application Composition and Security

### 5.1 Objective

Implement the bounded canonical read extensions, Journal-owned infrastructure
adapters, and read-only Journal application composition required by IDS-029.
Sprint 2 must prove authorization-before-disclosure, protected counts,
Project-less behavior, list/detail separation, deterministic composition, and
the absence of Journal persistence or write authority.

### 5.2 Entry Gates

Sprint 2 may begin only when:

1. Sprint 1 exit gates and Independent Sprint 1 Review are `PASS`;
2. Sprint 1 contracts remain unchanged and match accepted IDS-029;
3. the focused IDS-029 Project-identity amendment remains accepted;
4. the exact Section 3 file boundary remains authorized;
5. the current repository still exposes the canonical dependencies inventoried
   in Section 2;
6. both bounded read extensions can be implemented without changing canonical
   Domain models, existing DTOs, routes, mutations, or persistence semantics;
7. QG-M1 Sprint checkpoint is `PASS`;
8. no unresolved blocker, unrelated worktree overlap, or superseding authority
   exists.

### 5.3 Exact Deliverables

Sprint 2 shall deliver:

- a bounded minimal canonical Capture list read with protected
  `authorized_total`, `filtered_total`, and `visible_total`;
- a bounded actor-authorized canonical Project-selection read;
- Journal-owned adapters over those canonical application reads;
- trusted scope authorization for selected Project and optional Workspace and
  Engineering Object context;
- the Project-less workspace shell and protected Project-selection projection;
- New Capture navigation to existing Universal Capture authority;
- Inbox membership from authorized canonical `captured` Captures;
- Superseded membership from authorized canonical `superseded` Captures;
- explicit unavailable results for Drafts, Under Review, and Published;
- authorized Capture detail inspection using the separate detail projection;
- deterministic ordering, navigation, freshness, empty-state, and count
  composition;
- reauthorization on every detail, navigation, and refresh operation;
- safe partial-capability behavior;
- focused service, security, and structural performance evidence.

Sprint 2 creates no transport route, router registration, Journal write,
transaction boundary, Audit record, Domain Event, or idempotency record.

### 5.4 Ordered Implementation Tasks

1. Add the minimal canonical Capture repository read signature without changing
   existing write or list contracts.
2. Add typed Capture-owned summary, detail, and paginated read results without
   reusing Journal DTOs or changing existing Capture DTOs.
3. Implement selected-field Capture reads and separate protected pre-filter and
   post-filter counts using bounded database operations and existing scope
   predicates.
4. Add the canonical Capture application read operation that authorizes before
   returning the minimal neutral projection and totals.
5. Add Project-owned typed selection-item and bounded-page results without
   Journal DTO reuse, ORM rows, or untyped mappings.
6. Add the bounded Project repository query using existing Project/Workspace
   visibility rules and canonical identifier representation.
7. Add `ProjectService.list_authorized_selection` as the sole canonical
   application owner of actor-authorized Project selection and bounded
   continuation.
8. Establish the infrastructure-adapter package and implement Journal-owned
   port adapters over the two canonical application boundaries, including
   private translation from the neutral Journal actor.
9. Construct the canonical Capture service and its private `uow_factory` only
   inside the request-scoped Capture adapter; expose no Unit of Work to Journal
   service or transport and produce no write effect.
10. Implement trusted scope resolution and ensure optional refinements can only
   narrow the selected Project.
11. Implement the Project-less shell with bounded Project pages, reauthorization
    on every page, no hidden/global total, and no automatic selection.
12. Implement deterministic New Capture, Inbox, Superseded, and unavailable-view
   composition.
13. Implement separate authorized detail inspection, canonical navigation,
    freshness, empty-state, and protected-count mapping.
14. Implement refresh and deep-link reauthorization through the same read use
    cases.
15. Add service, security, and performance tests; run the full Sprint 2
    validation ladder.

Exactly one canonical page operation may serve a member-bearing Journal page.
Journal application code must not import or receive canonical repositories,
ORM rows, Sessions, or Unit of Work implementations.

### 5.5 Authorized File Scope for Sprint 2

Created:

- `backend/app/adapters/__init__.py`;
- `backend/app/adapters/engineering_journal.py`;
- `backend/app/services/engineering_journal_service.py`;
- `backend/tests/test_engineering_journal_service.py`;
- `backend/tests/test_engineering_journal_security.py`;
- `backend/tests/test_engineering_journal_performance.py`.

Modified:

- `backend/app/ports/engineering_experience_capture.py`;
- `backend/app/schemas/engineering_experience_capture.py`;
- `backend/app/repositories/engineering_experience_capture_repository.py`;
- `backend/app/services/engineering_experience_capture_service.py`;
- `backend/app/repositories/project_repository.py`;
- `backend/app/schemas/project.py`;
- `backend/app/services/project_service.py`.

Sprint 2 may also read, but not modify, the five completed Sprint 1 files and
all canonical dependencies. No other file is authorized.

### 5.6 Exact Tests

`backend/tests/test_engineering_journal_service.py` must prove:

- Project-less shell composition and bounded authorized Project choices;
- deterministic continuation beyond 100 authorized Projects with fresh
  authorization, unchanged actor/Organization scope, no hidden total, and no
  automatic Project selection;
- no Project inference or Capture member/count read without Project selection;
- selected Project and optional Workspace/Engineering Object scope narrowing;
- New Capture returns navigation only and performs no command;
- exact six-view behavior;
- Inbox contains only authorized `captured` Captures;
- Superseded contains only authorized `superseded` Captures;
- withdrawn Captures appear in no member-bearing PATCH-029 view;
- Drafts, Under Review, and Published are explicitly unavailable with no member
  or count query;
- deterministic `created_at` then canonical UUID ordering;
- authorized-empty and filtered-empty remain distinct;
- the three count values follow accepted semantics;
- detail uses the detail projection and independently reauthorizes;
- navigation and refresh reauthorize and never preserve stale authority;
- freshness uses only versions disclosed in the returned page;
- optional capability degradation does not fabricate members, counts, or
  authority;
- every Journal operation remains read-only.
- canonical Capture reads may privately use the Capture service's Unit of Work
  factory but expose no Unit of Work and create no Audit, outbox, idempotency,
  commit, rollback, or write effect.

`backend/tests/test_engineering_journal_security.py` must prove:

- inactive User, missing/disabled membership, inactive Organization,
  nonmember, and cross-Organization requests disclose nothing;
- cross-Project, cross-Workspace, cross-Engineering-Object, and revoked access
  use protected not found;
- unauthorized Project choices are omitted without hidden totals;
- unauthorized Capture items, fields, counts, replacement identities, and
  navigation targets are omitted;
- list and detail authorization are independent;
- supersession-chain identities are independently authorized where disclosed;
- protected missing and unauthorized outcomes are indistinguishable;
- source content, source reference, rationale, hidden identifiers, hidden
  totals, Creator detail, and denial diagnostics do not enter errors, logs, or
  diagnostics;
- temporary filtering never widens authorization;
- no Journal read creates an Audit, outbox, idempotency, or other write.

`backend/tests/test_engineering_journal_performance.py` must prove the
structural performance checks in Section 5.8.

### 5.7 Security and Disclosure Checks

Sprint 2 security review must verify:

1. trusted actor and active Organization originate only from the accepted
   authentication context;
2. authorization completes before scope, availability, item, count, field,
   navigation, or related identity disclosure;
3. Project selection is actor-authorized and bounded;
4. Workspace and Engineering Object refinement never widens Project scope;
5. `authorized_total` and `filtered_total` are calculated only over authorized
   canonical membership;
6. list projection never requests or loads detail-only plaintext solely for
   Journal presentation;
7. detail plaintext is returned only after explicit current item
   authorization;
8. protected omission is not converted into canonical null or an existence
   signal;
9. unavailable capability state cannot imply protected record existence;
10. no exception or log exposes persistence, authorization, or protected
    context diagnostics.
11. neutral Journal actor translation occurs only inside canonical adapters and
    never changes canonical command models.

### 5.8 Performance Checks

Required structural performance evidence is:

- Project-less shell: zero Capture member and count operations;
- unavailable view: zero canonical member and count operations;
- member-bearing page: exactly one bounded canonical page operation returning
  members and all three totals;
- Project selection: one bounded authorized page operation with maximum size
  `100` and no unbounded total disclosure;
- list composition: no per-item canonical lookup and no detail-only plaintext
  load;
- detail inspection: one explicitly scoped canonical detail operation;
- returned member count never exceeds `100`;
- no unbounded in-memory authorization, filter, count, or supersession
  traversal;
- equivalent authorized inputs produce deterministic ordering and output.
- each Project continuation page reauthorizes the actor and cannot widen actor
  or trusted Organization scope.

Runtime latency thresholds are not invented. Any measured performance concern
must be reported without weakening the structural contract.

### 5.9 Exit Gates

Sprint 2 passes only when:

- Sprint 1 and all Sprint 2 tests pass;
- both canonical read extensions preserve existing Capture and Project
  behavior;
- Project-less, membership, unavailable-view, empty-state, count, detail,
  navigation, refresh, and degradation tests pass;
- the complete authorization and protected-not-found matrix passes;
- list/detail disclosure and plaintext-exclusion checks pass;
- structural performance checks pass;
- no Journal write, persistence, transaction, Aggregate, Repository, Unit of
  Work, migration, or lifecycle exists;
- QG-6 proves no Journal Aggregate or lifecycle;
- QG-7 proves no Journal persistence, Repository, Unit of Work, table, ORM
  model, or migration;
- Capture, authentication, Organization, Project, Workspace, and Engineering
  Object adjacent regressions pass;
- exact Sprint 2 file scope and prohibited-pattern checks pass;
- QG-M1 Sprint checkpoint and Independent Sprint 2 Review are `PASS`.

Passing Sprint 2 does not authorize Sprint 3 or transport exposure.

### 5.10 Stop Conditions

Stop Sprint 2 if:

- a canonical read extension requires changing a model, migration, existing
  DTO, route, mutation, lifecycle, or authorization meaning;
- Journal application or transport would need direct repository, ORM, Session,
  or Unit of Work access;
- Project selection cannot be actor-authorized without disclosing broader
  Organization membership;
- the three protected totals cannot be produced without unbounded loading or
  post-disclosure authorization;
- list composition requires original content, source reference, rationale, or
  another detail-only field;
- a view requires unavailable Review, Organizational Memory, Knowledge Graph,
  or AI authority;
- any read produces a write side effect;
- a required change falls outside the exact Sprint 2 scope;
- any focused, adjacent, security, performance, QG-M1, or scope gate fails.

### 5.11 Expected Output

```text
Sprint 2 implementation status: PASS or BLOCKED
Files created: EXACTLY SIX OR NONE
Files modified: EXACTLY SEVEN OR NONE
Service tests: PASS or BLOCKED
Security tests: PASS or BLOCKED
Performance checks: PASS or BLOCKED
Sprint 1 regression: PASS or BLOCKED
Adjacent regression: PASS or BLOCKED
QG-M1 Sprint checkpoint: PASS or BLOCKED
QG-6 no Aggregate/lifecycle: PASS or BLOCKED
QG-7 no persistence boundary: PASS or BLOCKED
Independent Sprint 2 Review: PASS or NOT PERMITTED
Remaining findings: EXPLICIT
Permission to begin Sprint 3: NOT GRANTED BY SECTION 5
```

## 6. Sprint 3 Execution Plan — Transport and Final Integration

### 6.1 Objective

Expose the accepted Journal read behavior through the exact thin transport
boundary, compose dependencies per request, register only the Journal router,
and complete endpoint, integration, security, regression, and final-scope
evidence.

### 6.2 Entry Gates

Sprint 3 may begin only when:

1. Sprint 1 and Sprint 2 exit gates and independent reviews are `PASS`;
2. accepted Journal contracts and the exact file boundary remain unchanged;
3. both canonical read extensions are verified and available through
   Journal-owned adapters;
4. no unresolved security, disclosure, performance, or regression finding
   remains;
5. QG-M1 Sprint checkpoint is `PASS`;
6. the current application route set and worktree are recorded;
7. no superseding authority or unrelated file overlap exists.

### 6.3 Exact Deliverables

Sprint 3 shall deliver only:

- the exact three read-only Journal operations accepted by IDS-029;
- trusted authenticated actor construction from the existing server-side
  Organization context;
- request-scoped adapter and application-service composition;
- strict query/path validation and approved DTO response mapping;
- stable `200`, protected `404`, and validation `422` outcome mapping;
- router registration in the existing application;
- endpoint and integration evidence;
- prohibited-route, plaintext-exclusion, OpenAPI, exact-scope, adjacent, and
  complete backend regression evidence.

New Capture creation remains on the existing Universal Capture route. Refresh
repeats the same read operation. Navigation remains response metadata. Neither
receives a Journal command route.

### 6.4 Ordered Implementation Tasks

1. Implement the thin Journal router with only the three accepted `GET`
   operations and approved query criteria.
2. Build the trusted Journal actor exclusively from
   `get_current_user_organization_context`.
3. Compose canonical services, Journal adapters, and Journal application
   service per request without exposing Session or repository objects to
   transport behavior.
4. Map successful content, authorized empty, filtered empty, and capability
   unavailable to accepted DTOs.
5. Map missing and unauthorized resources to the existing protected-not-found
   envelope and invalid presentation criteria to the existing validation
   envelope.
6. Register only the Journal router in `backend/app/main.py`.
7. Add endpoint tests for workspace shell, every approved view, Capture detail,
   refresh behavior, pagination, filters, Project-less behavior, and stable
   errors.
8. Add integration assertions for authorization, counts, field disclosure,
   request-scoped composition, no writes, and canonical New Capture navigation.
9. Validate OpenAPI, prohibited routes, static boundaries, exact file scope,
   adjacent regressions, and full backend regression.
10. Assemble the Independent Final Review evidence package without committing
    or pushing.

### 6.5 Authorized File Scope for Sprint 3

Created:

- `backend/app/api/v1/routers/engineering_journal.py`;
- `backend/tests/test_engineering_journal_api.py`.

Modified:

- `backend/app/main.py`.

Sprint 3 may read but not modify all completed Sprint 1 and Sprint 2 files. No
other file is authorized.

### 6.6 Transport and Integration Tests

`backend/tests/test_engineering_journal_api.py` must prove:

- `GET /api/v1/engineering-journal` returns an authorized Project-less shell or
  selected-Project workspace as applicable;
- `GET /api/v1/engineering-journal/views/{view}` accepts exactly the six views
  and returns the accepted workspace DTO;
- `GET /api/v1/engineering-journal/captures/{capture_id}` returns only the
  separately authorized detail DTO;
- optional `project_id`, `workspace_id`, and `engineering_object_id` follow the
  accepted coherence rules;
- presentation defaults and all bounds are enforced;
- unsupported view, criteria, repeated scalar criteria, incoherent scope, and
  malformed identifiers return stable safe validation outcomes;
- protected missing and unauthorized scope or Capture return the same protected
  `404` envelope;
- content, authorized empty, filtered empty, and capability unavailable return
  the accepted `200` states;
- page and count serialization preserve exact meanings;
- Project-less responses disclose only bounded authorized Project choices;
- list responses exclude detail-only fields;
- detail, refresh, and navigation require current reauthorization;
- request-scoped composition does not retain protected state;
- no Journal read creates Audit, outbox, idempotency, or other persistence;
- existing Universal Capture creation navigation remains canonical and
  unchanged.

### 6.7 Prohibited-Route Checks

OpenAPI and route inspection must prove the absence of:

- `POST`, `PUT`, `PATCH`, or `DELETE` under `/api/v1/engineering-journal`;
- a separate refresh endpoint;
- a separate navigation endpoint;
- Journal Capture creation, withdrawal, supersession, or lifecycle endpoints;
- generic update, physical delete, bulk mutation, saved-state, read/unread,
  triage, preference, count, or cache endpoints;
- Review, approval, publication, Organizational Memory, Knowledge Graph, or AI
  endpoints;
- an additional Journal view or alias;
- duplicate registration of the Universal Capture creation route.

### 6.8 Full Regression

Sprint 3 validation proceeds in this order:

1. Sprint 1 contract tests;
2. Sprint 2 service, security, and performance tests;
3. Sprint 3 API tests;
4. all Universal Capture tests;
5. authentication and active-Organization-context tests;
6. Project and Workspace tests;
7. Engineering Object, Relationship, Evidence, and Audit tests;
8. application import, route, and OpenAPI inspection;
9. complete backend regression in one process;
10. final exact-file and prohibited-pattern verification.

A later pass does not waive an earlier failure. Existing tests may not be
weakened, skipped, reordered to hide shared-state failure, or redirected to an
unapproved database.

### 6.9 Exit Gates

Sprint 3 passes only when:

- all focused and integration tests pass;
- all prohibited-route checks pass;
- authorization, protected-not-found, counts, list/detail separation,
  Project-less behavior, refresh, and navigation evidence passes at transport;
- no protected plaintext appears in errors, logs, diagnostics, or non-detail
  responses;
- QG-8 Application and Security, QG-9 Transport, QG-10 Regression, and QG-M1
  Final are `PASS`;
- QG-6 no Journal Aggregate or lifecycle and QG-7 no Journal persistence
  boundary are reverified `PASS` against the final diff;
- adjacent and full backend regression complete with zero failures;
- application startup and OpenAPI inspection pass;
- the final backend diff contains exactly the twenty-one Section 3 files and no
  prohibited file;
- no migration exists or has been created or executed;
- Independent Final Review records `PASS` and the package is ready for Human
  QG-11.

### 6.10 Stop Conditions

Stop Sprint 3 if:

- transport requires business, membership, authorization, count, or canonical
  interpretation logic;
- an endpoint beyond the exact three accepted reads appears necessary;
- trusted Organization scope would come from client input;
- router composition exposes repository, ORM, Session, or Unit of Work objects
  as application authority;
- protected outcomes cannot use the existing stable envelopes;
- a route permits mutation, generic update, delete, Review, publication,
  Knowledge Graph, Organizational Memory, or AI behavior;
- any implementation or test file outside Sprint 3 scope changes;
- any focused, integration, OpenAPI, prohibited-route, adjacent, full
  regression, QG-M1, or exact-scope check fails.

### 6.11 Expected Output

```text
Sprint 3 implementation status: PASS or BLOCKED
Files created: EXACTLY TWO OR NONE
Files modified: EXACTLY ONE OR NONE
API tests: PASS or BLOCKED
Prohibited routes: ABSENT or BLOCKED
Adjacent regression: PASS or BLOCKED
Full backend regression: PASS or BLOCKED
QG-8/QG-9/QG-10/QG-M1 Final: PASS or BLOCKED
QG-6/QG-7 Final: PASS or BLOCKED
Independent Final Review: PASS or NOT PERMITTED
Human QG-11 readiness: READY or NOT READY
Remaining findings: EXPLICIT
```

## 7. Validation and Review Plan

### 7.1 Validation Environment

All database-backed validation must run only through the repository's isolated
test database guard targeting `satco_platform_patch02022_test`. No development,
staging, or production migration is required or authorized. Tests may allow the
existing bootstrap to verify the current repository Alembic head; PATCH-029
must create or execute no migration.

The commands below run from the repository root against the existing
`satco-backend` container and current test environment.

### 7.2 Focused Validation Commands

Sprint 1:

```text
docker exec satco-backend python -m pytest -q tests/test_engineering_journal_contracts.py
```

Sprint 2:

```text
docker exec satco-backend python -m pytest -q tests/test_engineering_journal_contracts.py tests/test_engineering_journal_service.py tests/test_engineering_journal_security.py tests/test_engineering_journal_performance.py
```

Sprint 3 and complete PATCH-029 focused validation:

```text
docker exec satco-backend python -m pytest -q tests/test_engineering_journal_contracts.py tests/test_engineering_journal_service.py tests/test_engineering_journal_security.py tests/test_engineering_journal_performance.py tests/test_engineering_journal_api.py
```

Every command must complete with zero failed, skipped, xfailed, or unexpectedly
xpassed PATCH-029 tests.

### 7.3 Adjacent Regression Scope

The mandatory adjacent regression command is:

```text
docker exec satco-backend python -m pytest -q tests/test_engineering_experience_capture_aggregate.py tests/test_engineering_experience_capture_schemas.py tests/test_engineering_experience_capture_repository.py tests/test_engineering_experience_capture_service.py tests/test_engineering_experience_capture_security.py tests/test_engineering_experience_capture_performance.py tests/test_engineering_experience_capture_transaction.py tests/test_engineering_experience_capture_api.py tests/test_engineering_experience_capture_migration.py tests/test_auth.py tests/test_authenticated_organization_context.py tests/test_project_core.py tests/test_project_organization_scope.py tests/test_project_permissions.py tests/test_projects.py tests/test_engineering_workspace_core.py tests/test_engineering_workspace_permissions.py tests/test_engineering_object_api.py tests/test_engineering_object_service.py tests/test_engineering_relationship_service.py tests/test_engineering_relationship_api.py tests/test_evidence_service.py tests/test_evidence_api.py tests/test_audit_logs.py
```

If an exact named adjacent file is absent when execution begins, work stops for
plan reconciliation; it must not be silently omitted or replaced.

### 7.4 Full Backend Regression

The complete backend suite must run once in a single process:

```text
docker exec satco-backend python -m pytest -q
```

The gate requires zero failures and preservation of deterministic shared-test
state before and after PATCH-029 suites.

### 7.5 Static Checks

Required static validation is:

```text
docker exec satco-backend python -m compileall -q app tests/test_engineering_journal_contracts.py tests/test_engineering_journal_service.py tests/test_engineering_journal_security.py tests/test_engineering_journal_performance.py tests/test_engineering_journal_api.py
docker exec satco-backend python -c "from app.main import app; assert app.openapi()"
git diff --check
```

Review must also inspect import direction, strict DTO configuration, complete
type hints, route methods, stable exception mapping, and canonical identifier
preservation.

QG-6 and QG-7 require executable structural checks against the actual diff:

```text
test ! -e backend/app/models/engineering_journal.py
test ! -e backend/app/repositories/engineering_journal_repository.py
test ! -e backend/app/repositories/engineering_journal_unit_of_work.py
test -z "$(find backend/migrations -type f -iname '*journal*' -print)"
```

Positive QG-6 evidence consists of the exact Journal enum/schema/port/service
inventory and tests demonstrating that all views are derived projections over
canonical state and that no Journal Aggregate command or lifecycle exists.
Positive QG-7 evidence consists of the exact backend manifest, module-import
inspection, SQLAlchemy metadata inspection, Alembic revision inventory, and
no-write tests demonstrating that Journal owns no persistence boundary.

### 7.6 Exact-File Verification

Before each Sprint and final review, record:

```text
git status --short
git diff --name-only
git diff --stat
```

The final backend change set must equal the thirteen created and eight modified
files in Section 3. Unrelated pre-existing worktree changes must remain excluded
from PATCH-029 review and delivery. A missing, substituted, or additional
backend file is a blocker.

### 7.7 Prohibited-Pattern Scans

Review must use repository search to prove:

- no Journal model, table, migration, Repository, Unit of Work, commit,
  rollback, write command, lifecycle, or durable state;
- no `EngineeringExperienceCaptureActor` import in Journal schemas, ports, or
  application service;
- no ORM row, untyped mapping, or Journal DTO used as a canonical Project or
  Capture application result;
- no Project visibility rule duplicated in Journal;
- no Capture Unit of Work exposed to Journal service or transport and no read
  Audit, outbox, idempotency, or canonical write effect;
- no direct persistence or canonical repository import in Journal application
  or transport;
- no `POST`, `PUT`, `PATCH`, or `DELETE` Journal route;
- no detail-only plaintext field in Journal list, count, navigation, empty,
  unavailable, error, log, or diagnostic contracts;
- no client-trusted Organization identity;
- no Review, Organizational Memory, Knowledge Graph, or AI behavior;
- no new view, alias, generic operation, or physical delete;
- no modification outside the exact file boundary.

Search findings require semantic inspection; a textual match is not waived
without documented evidence that it is a test assertion, prohibition, or safe
contract reference.

### 7.8 Independent Final Review Package

The package must contain:

- accepted PATCH-029, AR-029, EDS-029, IDS-029, and executable
  Implementation-Plan-029 references;
- IRR-029 `READY FOR IMPLEMENTATION` evidence that preceded implementation;
- Sprint 1–3 entry, exit, QG-M1, and independent-review records;
- final exact file manifest and diff statistics;
- focused and adjacent command results;
- full backend regression result;
- route/OpenAPI and prohibited-route evidence;
- authorization, protected-not-found, count, list/detail, Project-less,
  plaintext-exclusion, and no-write evidence;
- static, dependency-direction, and prohibited-pattern results;
- explicit QG-6 and QG-7 positive and prohibited-pattern evidence;
- confirmation that no migration was created or executed;
- remaining findings and rollback/stop evidence, if any.

Independent Final Review must return `PASS` before Human QG-11 may begin.

### 7.9 Human QG-11 Readiness

Human QG-11 is ready only when:

- Independent Final Review is `PASS`;
- all accepted Human-first Journal behavior is demonstrable;
- Universal Capture authority and canonical identifiers are preserved;
- authorization and protected disclosure evidence is complete;
- every focused, adjacent, and full regression gate is `PASS`;
- the final diff matches the exact approved file set;
- no hidden persistence, write authority, future capability, migration, or
  unresolved finding remains.
- QG-6 and QG-7 are `PASS` against the final reviewed diff.

Human QG-11 records acceptance of the actual implementation and reviewed file
set. It does not itself authorize commit or push.

### 7.10 QG-12 Readiness

QG-12 may begin only after Human QG-11 `PASS`. Its evidence must identify the
exact reviewed delivery manifest, final validation results, excluded unrelated
files, target branch, and required remote verification.

QG-12 must separately decide commit and push authority. It cannot authorize a
migration because PATCH-029 contains none. Before QG-12 authorization, commit,
push, deployment, and release closure remain prohibited.

### 7.11 Section 7 Decision

```text
Focused validation: DEFINED
Adjacent regression: DEFINED
Full backend regression: DEFINED
Static and exact-file checks: DEFINED
Prohibited-pattern scans: DEFINED
QG-6 no Aggregate/lifecycle gate: DEFINED
QG-7 no persistence boundary gate: DEFINED
Independent Final Review package: DEFINED
Human QG-11 readiness: DEFINED
QG-12 readiness: DEFINED
Validation execution: NOT AUTHORIZED BY THIS PLAN ALONE
Implementation authority: NOT GRANTED
```

## 8. Final Delivery and Closure Plan

### 8.1 Exact Delivery Sequence

PATCH-029 delivery must proceed in this order:

1. complete and accept the entire Implementation Plan;
2. obtain IRR-029 QG-M1 Readiness `PASS` and `READY FOR IMPLEMENTATION`;
3. implement and independently review Sprint 1;
4. implement and independently review Sprint 2;
5. implement Sprint 3 and complete focused, adjacent, full regression, static,
   OpenAPI, prohibited-pattern, and exact-file validation;
6. obtain Independent Final Review `PASS`;
7. obtain Human QG-11 `PASS` against the actual implementation and manifest;
8. obtain explicit QG-12 commit and push authorization for the exact reviewed
   manifest;
9. create one bounded PATCH-029 commit containing only authorized files;
10. push only to the explicitly authorized current development branch;
11. verify local commit SHA equals the remote branch SHA;
12. record delivery evidence and reconcile PATCH-029 governance status;
13. close PATCH-029 only when all completion evidence is accepted and no
    blocker remains.

No step may be reordered or inferred from a later approval. Failure after a
source edit returns to the last accepted checkpoint. Failure after commit but
before verified push leaves delivery incomplete and must be reported without
creating an additional unapproved commit.

### 8.2 Commit and Push Authorization Boundary

Implementation-Plan-029 grants no commit or push authority.

Commit is permitted only when QG-12 explicitly identifies:

- the exact thirteen created and eight modified backend files from Section 3;
- the accepted implementation and validation evidence;
- unrelated files that must remain excluded;
- the authorized commit action and target branch.

Push is permitted only when QG-12 separately authorizes push of that exact
commit. The pushed SHA must equal the locally reviewed SHA and the remote branch
must be verified after push.

No migration file, database action, deployment action, unrelated documentation,
pre-existing worktree change, or later capability may enter the PATCH-029
delivery commit. If the reviewed manifest changes after QG-11 or QG-12, delivery
authorization is void and the affected review gates must repeat.

### 8.3 Closure Conditions

PATCH-029 may be marked `DONE / CLOSED` only when:

- all three Sprints and required Quality Gates are `PASS`;
- Independent Final Review, Human QG-11, and QG-12 are `PASS`;
- focused, adjacent, and full backend regression evidence has zero failures;
- exact-file and prohibited-pattern evidence is complete;
- one bounded commit and verified authorized push are recorded;
- Universal Capture remains canonical;
- Journal remains read-only, presentation-only, and nonpersistent;
- no migration was created or executed;
- no unresolved architecture, security, regression, scope, or delivery finding
  remains;
- the authoritative PATCH registry, Roadmap, PATCH-029 record, and required
  review evidence are reconciled without rewriting implementation history.

### 8.4 Final Plan Decision

```text
Implementation-Plan-029 content: SECTIONS 1–8 COMPLETE
Implementation Plan status: ACCEPTED / EXECUTABLE
Sprint sequence: THREE / DEPENDENCY ORDERED
Exact backend file boundary: TWENTY-ONE
Migration: NONE / NOT AUTHORIZED
Implementation authority: NOT GRANTED
Repeated complete-plan review: PASS
Human Implementation Plan Acceptance: PASS
Plan execution status: EXECUTABLE SUBJECT TO IRR-029
Permission for Human Plan Acceptance: COMPLETED / PASS
Permission to create IRR-029: GRANTED
Commit and push authority: NOT GRANTED
```
