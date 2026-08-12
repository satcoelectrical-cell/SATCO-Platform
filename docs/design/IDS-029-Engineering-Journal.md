# IDS-029 — Engineering Journal

## 1. Implementation Architecture Contract and Boundaries

### 1.1 Document Control

| Field | Value |
|---|---|
| Document ID | IDS-029 |
| Related PATCH | PATCH-029 — Engineering Journal |
| Related EDS | EDS-029 — Accepted |
| Design scope | Sections 1–8 — Complete implementation specification |
| Status | ACCEPTED / COMPLETE — PROJECT IDENTITY AMENDMENT PASS |
| Classification | Incremental implementation specification |
| Architecture style | Docs-First / layered modular architecture |
| Implementation authority | NOT GRANTED |
| Human EDS Acceptance | PASS |
| IDS-029 Design Authorization | GRANTED |
| Independent IDS Review | PASS |
| Human IDS Acceptance | PASS |
| Implementation Plan Design | AUTHORIZED |
| Focused Project Identity Amendment | PASS |
| Implementation-Plan-029 | ACCEPTED / EXECUTABLE |
| Human Implementation Plan Acceptance | PASS |
| Permission for IRR-029 | GRANTED |
| IRR-029 | PENDING REPEATED REVIEW |

This IDS translates accepted EDS-029 architecture into an exact implementation specification. Section 1 establishes boundaries only. It does not authorize implementation, repository modification, migration, commit, push, or deployment.

### 1.2 Governing Sources

IDS-029 is subordinate to:

1. SATCO Constitution;
2. Engineering Intelligence Manifesto v1.0;
3. accepted SATCO Architecture and ADRs;
4. Governance Model and Roadmap;
5. PATCH-029;
6. AR-029 PASS;
7. accepted EDS-029;
8. completed PATCH-028 Universal Capture contracts;
9. current repository boundaries.

If this IDS conflicts with an accepted higher authority, the higher authority governs and IDS-029 returns to review.

### 1.3 Implementation Objective

Implement Engineering Journal as the default authenticated Human Engineering Workspace over existing Universal Capture.

The implementation must:

- compose authorized canonical Capture information;
- expose exactly the six approved Journal views;
- preserve canonical Capture UUID, provenance, context, version, lifecycle, and history;
- derive membership deterministically from authorized canonical state;
- protect views, items, counts, metadata, and navigation;
- support workspace continuity and stable canonical navigation;
- degrade safely when a future canonical capability is unavailable;
- remain presentation-only.

The implementation must not create a Journal source of truth.

### 1.4 Application Boundary

Engineering Journal introduces one bounded read-oriented application boundary:

```text
Authenticated Journal request
        ↓
Engineering Journal application boundary
        ↓
Authorization and scope resolution
        ↓
Approved canonical application contracts
        ↓
Deterministic Journal composition
        ↓
Authorized Journal DTO
```

The Journal application boundary owns:

- use-case orchestration;
- trusted active-Organization resolution;
- authorization-before-disclosure;
- governed Project and optional Workspace context resolution;
- selection of the requested approved view;
- deterministic view composition;
- protected count calculation;
- unavailable-capability representation;
- canonical navigation metadata;
- response DTO assembly.

It does not own:

- canonical Capture queries independently of the approved Capture application contract;
- Capture commands or lifecycle transitions;
- aggregate mutation;
- persistence;
- transactions that modify engineering state;
- Review, publication, Organizational Memory, Knowledge Graph, or AI decisions.

### 1.5 Layer Responsibilities

| Layer | IDS-029 responsibility |
|---|---|
| Transport | Accept Journal requests, validate transport syntax, invoke the application boundary, and map protected outcomes |
| Application | Resolve trusted scope, authorize, query canonical application contracts, compose views, calculate authorized counts, and map DTOs |
| Domain | No Journal domain Aggregate or lifecycle is introduced |
| Ports | Define inward-owned read contracts required for canonical composition |
| Infrastructure | Adapt approved canonical application capabilities without becoming an authority source |
| Persistence | No Journal persistence component exists |
| Presentation consumer | Render the returned Journal workspace without creating canonical state |

Dependencies point inward toward application-owned contracts. Canonical Capture must not depend on Engineering Journal.

### 1.6 Canonical Capability Boundary

Universal Capture remains the sole source of truth for:

- Capture UUID;
- original content;
- source kind and source reference;
- Creator;
- Organization and Project;
- optional Workspace, discipline, and Engineering Object context;
- lifecycle;
- version;
- timestamps;
- withdrawal and supersession history;
- replacement and supersession-chain identity.

Engineering Journal must consume this information through an approved Capture application read contract.

Journal must not:

- query Capture tables directly;
- define a second Capture repository;
- copy Capture rows into Journal-owned storage;
- cache Capture information as authority;
- translate canonical UUIDs into Journal identifiers;
- reinterpret `captured`, `withdrawn`, or `superseded`;
- mutate a Capture while composing a view.

### 1.7 Aggregate Interactions

Engineering Journal introduces no Aggregate and owns no aggregate transaction.

Permitted aggregate interaction is limited to authorized read representations obtained through canonical application boundaries.

| Journal behavior | Aggregate interaction |
|---|---|
| New Capture | Delegates the Human to the existing Universal Capture creation authority; Journal creates no aggregate |
| Inbox | Reads authorized canonical Captures with lifecycle `captured` |
| Drafts | No aggregate interaction; canonical draft authority is unavailable |
| Under Review | No aggregate interaction; Engineering Review authority is unavailable |
| Published | No aggregate interaction; publication and Organizational Memory authorities are unavailable |
| Superseded | Reads authorized canonical Captures with lifecycle `superseded` and only authorized chain information |
| Item inspection | Resolves the canonical Capture through its approved application boundary |
| Refresh | Repeats authorized canonical reads; performs no aggregate command |

Journal must never load an Aggregate for mutation or call Aggregate transition methods.

### 1.8 Read-Model Boundary

The Journal read model is an application response projection. It is:

- noncanonical;
- read-only;
- deterministic;
- authorization-filtered;
- reconstructible from canonical sources;
- disposable;
- incapable of becoming engineering authority.

It may represent:

- active workspace context;
- requested Journal view;
- authorized view members;
- protected authorized totals;
- canonical Capture summaries;
- canonical lifecycle and version indicators;
- navigation references using canonical identities;
- authorized empty states;
- filtered-empty states;
- unavailable future capabilities.

It must not contain:

- Journal record identifiers;
- persisted membership state;
- read/unread or triage authority;
- Journal-owned timestamps or lifecycle;
- inferred Review or publication status;
- inferred graph relationships;
- AI classifications or recommendations;
- hidden-record totals;
- authorization diagnostics;
- canonical plaintext duplicated for persistence.

### 1.9 Approved View Availability

| View | IDS-029 behavior | Canonical authority |
|---|---|---|
| New Capture | Present an authorized navigation/action entry to existing Capture creation | Universal Capture |
| Inbox | Compose authorized active Captures | Universal Capture lifecycle `captured` |
| Drafts | Return explicit capability-unavailable semantics | No approved authority |
| Under Review | Return explicit capability-unavailable semantics | Future Engineering Review |
| Published | Return explicit capability-unavailable semantics | Future Review and Organizational Memory |
| Superseded | Compose authorized superseded Captures | Universal Capture lifecycle `superseded` |

No additional Journal view is authorized.

Unavailable views must not return synthetic records, inferred membership, or a zero count that implies an active canonical capability.

### 1.10 State and Ownership Boundaries

Engineering Journal owns only presentation composition.

It owns no:

- database table;
- ORM model;
- repository;
- Unit of Work;
- migration;
- Aggregate;
- lifecycle;
- durable membership;
- canonical count;
- canonical navigation history;
- Review state;
- publication state;
- Organizational Memory state;
- Knowledge Graph state;
- AI state.

Temporary noncanonical presentation preferences remain outside canonical engineering state and cannot affect authorization, membership, lifecycle, identity, provenance, or context.

### 1.11 Transaction Boundary

Journal composition is read-only.

Each Journal query must:

1. resolve the current authenticated actor and trusted active Organization;
2. authorize the requested governed scope;
3. obtain authorized canonical information;
4. compose the response without mutation;
5. return no canonical write side effects.

Journal composition must not:

- begin a write-oriented Unit of Work;
- commit or roll back canonical changes;
- create Audit or outbox records merely because a view was opened;
- coordinate transactions across bounded contexts;
- combine New Capture creation with Journal composition in one transaction.

Canonical commands initiated through New Capture remain owned atomically by the existing Universal Capture Unit of Work.

### 1.12 Dependency Direction

Permitted direction:

```text
Journal router
    ↓
Journal application service
    ↓
Journal-owned canonical read ports
    ↓
Approved canonical application adapters
```

Prohibited direction:

```text
Universal Capture → Engineering Journal
Canonical Aggregate → Journal DTO
Journal → canonical repository/table
Journal ↔ canonical bounded context
```

The Journal transport may depend on Journal DTOs and the Journal application
boundary. Request-scoped infrastructure composition may construct approved
adapters for that boundary.

Transport remains prohibited from:

- querying persistence directly;
- treating database sessions as an authority source;
- bypassing Journal-owned application ports;
- depending directly on ORM models or canonical repositories for business
  behavior;
- invoking aggregate mutation methods.

### 1.13 Security Boundary

The application boundary must enforce:

- active-user verification;
- active Organization membership;
- trusted selected Organization;
- Organization-scoped Project resolution;
- optional Workspace authorization;
- optional Engineering Object authorization;
- Capture-level authorization;
- authorization before view membership;
- authorization before count calculation;
- authorization before canonical navigation disclosure;
- protected-not-found behavior;
- reauthorization during refresh and deep-link resolution;
- omission of unauthorized records without count leakage.

Previously returned presentation state, navigation history, filters, or canonical identifiers grant no continuing access.

### 1.14 Future Capability Boundary

Future Engineering Review, Engineering Knowledge Graph, Organizational Memory, draft authority, or additional Journal views may integrate only after:

- separate PATCH registration;
- accepted architecture and EDS;
- an explicit canonical owner;
- an approved application contract;
- exact authorization and protected-disclosure rules;
- deterministic membership and precedence rules;
- backward-compatibility review.

IDS-029 does not pre-authorize files, adapters, DTO fields, routes, persistence, or behavior for those capabilities.

### 1.15 Explicit Non-Goals

Section 1 does not authorize or specify:

- exact files;
- router paths or HTTP methods;
- detailed DTO fields;
- repository method signatures;
- dependency-provider functions;
- pagination mechanics;
- performance thresholds;
- implementation Sprints;
- tests or Quality Gate commands;
- database schema;
- migrations;
- frontend implementation;
- implementation code.

These matters may be defined only in later accepted IDS-029 sections.

### 1.16 Section Decision

```text
Application boundary: DEFINED
Canonical Capture authority: PRESERVED
Journal role: PRESENTATION ONLY
Journal Aggregate: NONE
Journal persistence: NONE
Journal lifecycle: NONE
Journal write transaction: NONE
Review authority: NOT INTRODUCED
Organizational Memory authority: NOT INTRODUCED
Engineering Knowledge Graph authority: NOT INTRODUCED
AI behavior: NONE
Dependency direction: INWARD / ONE-WAY
Shared-table ownership: PROHIBITED
Implementation authorization: NOT GRANTED
Section 1 architecture acceptance: PASS
```

## 2. Application Services and Orchestration

### 2.1 Application-Service Boundary

IDS-029 defines one Journal application boundary:

`EngineeringJournalApplication`

It orchestrates read-only Human workspace use cases over approved canonical application contracts.

It owns:

- trusted request-context orchestration;
- authorization-before-disclosure;
- approved-view selection;
- canonical read orchestration;
- deterministic composition;
- protected counts;
- empty and unavailable-state selection;
- safe navigation projection;
- response DTO assembly.

It owns no:

- canonical business state;
- Aggregate;
- Repository;
- Unit of Work;
- lifecycle transition;
- durable Journal state;
- Review, publication, Organizational Memory, Knowledge Graph, or AI decision.

### 2.2 Application Services

The application boundary is separated into the following responsibilities:

| Component | Responsibility |
|---|---|
| `EngineeringJournalApplication` | Entry point for Journal use cases |
| `EngineeringJournalScopeResolver` | Resolve authenticated Human, active Organization, Project, and optional governed context |
| `EngineeringJournalViewComposer` | Compose one approved view from authorized canonical projections |
| `EngineeringJournalCountComposer` | Produce protected authorized counts |
| `EngineeringJournalNavigationComposer` | Produce stable canonical navigation and safe return metadata |
| `EngineeringJournalAvailabilityPolicy` | Identify currently available and unavailable views from approved capability authority |
| `EngineeringJournalProjectionMapper` | Convert authorized canonical read results into noncanonical Journal DTOs |

These names specify responsibilities, not required implementation classes. Implementations may combine responsibilities only when the separation of authorization, canonical reads, composition, and projection remains testable.

### 2.3 Use Cases

#### Open Default Workspace

Purpose:

- establish the authenticated engineer’s default Journal workspace;
- resolve the trusted active Organization;
- select Inbox as the default member-bearing view;
- return an authorized Journal composition.

The use case must not infer a Project when multiple authorized Projects are possible. It may require an existing trusted workspace context before member-bearing information is disclosed.
#### Default Workspace Without Trusted Project Context

When no single trusted Project context is already established:

- Engineering Journal must not infer or auto-select a Project;
- Inbox members and counts must not be queried;
- the application may return only an authorized workspace shell and a protected
  Project-selection projection containing Projects the actor is authorized to
  access;
- hidden Projects, counts, or alternatives must not be disclosed;
- member-bearing views begin only after explicit selection or restoration of a
  trusted Project context.


#### Open Journal View

Purpose:

- open one of the six approved views;
- authorize its governed scope;
- obtain canonical information where authority exists;
- return the appropriate available, empty, filtered-empty, or unavailable representation.

#### Refresh Journal View

Purpose:

- reauthorize the complete request;
- reread current canonical state;
- recompute membership and counts;
- discard stale presentation assumptions;
- return the latest authorized deterministic composition.

Refresh is the same authorization and composition use case as opening a view. It is not a canonical command.

#### Resolve Journal Navigation

Purpose:

- construct authorized navigation metadata for a canonical Capture or owning capability;
- preserve canonical identity;
- preserve a safe return context;
- avoid disclosing inaccessible destinations.

Navigation resolution does not open, mutate, or authorize the destination permanently.

#### Present New Capture Entry

Purpose:

- determine whether the Human may access canonical Capture creation for the governed context;
- return navigation to the existing Universal Capture creation authority.

Journal must not create Capture itself or coordinate the Capture transaction.

### 2.4 View Use-Case Matrix

| View | Application behavior |
|---|---|
| New Capture | Authorize context and compose navigation to existing Capture creation |
| Inbox | Read and compose authorized canonical Captures with lifecycle `captured` |
| Drafts | Compose explicit capability-unavailable state |
| Under Review | Compose explicit capability-unavailable state |
| Published | Compose explicit capability-unavailable state |
| Superseded | Read and compose authorized canonical Captures with lifecycle `superseded` |

No use case may infer records for unavailable views.

Withdrawn Captures are not placed into an unapproved Journal view.

### 2.5 Request Flow

Every Journal request follows this order:

```text
1. Receive authenticated request context
2. Resolve active Human
3. Resolve trusted active Organization
4. Validate requested Journal view
5. Resolve and authorize Project scope
6. Resolve optional Workspace and Engineering Object scope
7. Determine canonical capability availability
8. Read only authorized canonical information
9. Apply canonical-state precedence
10. Determine deterministic view membership
11. Calculate authorized counts
12. Compose navigation metadata
13. Select content, empty, filtered-empty, or unavailable result
14. Map the final Journal DTO
```

No item, identifier, count, membership, relationship, or navigation destination may be resolved for disclosure before its required authorization step.

### 2.6 Read Orchestration

Read orchestration must:

- use Journal-owned outbound read ports;
- obtain canonical Capture information through an approved application adapter;
- request only the lifecycle and governed scope needed by the selected view;
- maintain deterministic ordering;
- apply authorization before count and projection;
- tolerate concurrent canonical-state changes;
- omit records that cease to qualify or become inaccessible;
- avoid coordinating canonical writes;
- avoid querying canonical persistence directly.

A read result is input to composition, not authority owned by Journal.

If a canonical capability is unavailable, orchestration must not retry through an unauthorized source, query its persistence directly, or reconstruct its state from another capability.

### 2.7 Dependency Injection

Dependency Injection supplies the Journal application boundary with:

- authenticated request-context provider;
- trusted active-Organization resolver;
- scope-authorization adapter;
- canonical Capture read adapter;
- canonical navigation-authorization adapter;
- capability-availability policy;
- projection and composition collaborators;
- approved clock or request-time context only if later required for noncanonical response metadata.

Dependency Injection must not supply:

- a Journal repository;
- a Journal Unit of Work;
- Journal ORM models;
- a writable canonical repository;
- a Journal database table;
- an AI provider;
- an Engineering Review or Organizational Memory adapter before separate approval.

### 2.8 Composition Root

The request-scoped composition root may construct approved infrastructure adapters and connect them to Journal-owned application ports.

It may use request-scoped infrastructure resources to construct those adapters, including existing infrastructure required by canonical application boundaries.

It must not:

- treat a database session as an authority source;
- expose infrastructure resources to Journal business orchestration;
- allow transport to query persistence;
- bypass Journal-owned application ports;
- inject ORM models or canonical repositories into transport;
- create bidirectional dependencies;
- introduce Journal transaction ownership.

Permitted direction:

```text
Transport
   ↓
Request-scoped composition root
   ↓
EngineeringJournalApplication
   ↓
Journal-owned ports
   ↓
Approved canonical application adapters
```

### 2.9 Error and Outcome Ownership

The application boundary owns stable Journal outcomes for:

- protected not found;
- unsupported Journal view;
- authorized empty result;
- filtered-empty result;
- capability unavailable;
- invalid noncanonical presentation criteria.

It must not expose:

- canonical repository errors;
- database errors;
- authorization diagnostics;
- hidden identifiers;
- hidden totals;
- capability-internal exceptions;
- plaintext from inaccessible Captures.

Capability unavailable is not equivalent to protected not found or authorized empty.

### 2.10 Application Invariants

1. Every use case is read-only except delegation to the existing independent Capture creation authority.
2. Every request resolves trusted Organization scope before canonical reads.
3. Authorization precedes membership, counting, projection, and navigation.
4. Application orchestration depends only on Journal-owned ports.
5. Journal never invokes canonical Aggregate mutation methods.
6. Journal owns no transaction commit or rollback.
7. View composition is deterministic for identical authorized inputs.
8. Presentation criteria cannot change canonical membership.
9. Unavailable authority is never inferred or fabricated.
10. Refresh performs complete reauthorization.
11. Protected records are omitted without count or diagnostic leakage.
12. Canonical Capture identity and state remain unchanged.
13. The application boundary introduces no Review, Organizational Memory, Knowledge Graph, or AI behavior.
14. Transport and infrastructure concerns do not enter application decisions.
15. Section 2 grants no implementation authority.

### 2.11 Section Decision

```text
Journal application boundary: DEFINED
Use cases: DEFINED
Request flow: DEFINED
Read orchestration: READ-ONLY
Dependency Injection boundary: DEFINED
Composition root: REQUEST-SCOPED / AUTHORITY-NEUTRAL
Journal transaction ownership: NONE
Canonical mutation authority: NONE
Implementation authorization: NOT GRANTED
Section 2 architecture acceptance: PASS
```

## 3. Read Ports and Canonical Contracts

### 3.1 Port Ownership

Journal application owns the abstractions it requires to compose the workspace.

Infrastructure and canonical capabilities implement or adapt to these abstractions. Canonical domains must not import Journal ports.

The required conceptual ports are:

| Port | Purpose |
|---|---|
| `EngineeringJournalScopeAuthorizationPort` | Resolve and authorize governed Journal scope |
| `EngineeringJournalProjectSelectionPort` | Return a bounded protected projection of Projects already authorized to the actor inside the trusted active Organization |
| `EngineeringJournalCaptureReadPort` | Return authorized canonical Capture projections |
| `EngineeringJournalCaptureNavigationPort` | Resolve authorized canonical Capture navigation |
| `EngineeringJournalCapabilityAvailabilityPort` | Report whether an approved canonical capability is available for composition |
| `EngineeringJournalFutureCapabilityReadPort` | Reserved contract category requiring separate approval before any implementation |

The future-capability port category grants no present implementation authority.

### 3.2 Scope Authorization Port

The scope authorization contract accepts:

- authenticated actor identity;
- trusted active Organization identity;
- optional requested Project identity;
- optional Workspace identity;
- optional Engineering Object identity;
- requested Journal view.

It returns either:

- an authorized immutable Journal scope projection, whose Project is absent only for the Project-less shell; or
- protected not found.

An authorized scope projection may contain only the canonical identifiers and governed context required for subsequent reads.

The port must verify:

- active Human status;
- active Organization status;
- active Organization membership;
- Project ownership by the active Organization;
- actor access to the Project;
- Workspace membership in the same Project when present;
- actor access to the Workspace;
- Engineering Object membership in the same authorized context when present;
- compatible discipline context.

It must not trust a client-provided Organization identity.

The Project-selection port is used only when the authorized scope contains no
Project. It accepts the authenticated actor, trusted active Organization, a
positive page number, and a page size from 1 through 100. It returns only a
bounded page of Projects that the actor is already authorized to access, with
the canonical Project identifier and approved display name, ordered by display
name and then canonical Project identifier. It returns no inaccessible Project,
global total, membership diagnostic, or suggested cross-Organization scope.
Selection of a Project causes the complete scope-authorization operation to run
again; a selection projection is never an access grant.

The Project identifier is represented exactly as defined by the canonical
Project capability. Engineering Journal owns no Project identity format and
must neither redefine nor transform it.

### 3.3 Canonical Capture Read Port

The Capture read port represents an approved application-level read contract over Universal Capture.

Its conceptual operation is:

```text
read authorized Capture page
for:
- authenticated actor
- trusted authorized scope
- required canonical lifecycle
- approved presentation criteria
- bounded result window
```

It returns one `EngineeringJournalCapturePageResult` containing:

- authorized canonical Capture projections;
- `authorized_total`, calculated after authorization and lifecycle membership
  but before temporary presentation filtering;
- `filtered_total`, calculated after the closed presentation filter and before
  pagination;
- `visible_total`, equal to the returned page length;
- deterministic continuation information where required;
- no inaccessible records or hidden totals.

The three totals and page members must be produced by the same bounded
canonical application operation. The Journal must not derive either protected
total by loading an unbounded result set. When no filter is active,
`filtered_total` equals `authorized_total`.

The port must not expose:

- ORM entities;
- repository sessions;
- unfiltered global query results;
- cross-Organization candidates;
- records awaiting later Journal-side authorization;
- database-specific expressions;
- write methods;
- commit or rollback behavior.

### 3.4 Canonical Capture Projection Contracts

Journal uses two separate conceptual projections supplied through the approved
Universal Capture application boundary.

#### Capture List/Summary Projection

The list/summary projection contains only the minimum authorized fields required
for Journal navigation and Human identification:

- canonical Capture UUID;
- Project identity;
- optional Workspace identity;
- canonical discipline when required for context;
- optional Engineering Object identity when required for navigation;
- source kind;
- canonical lifecycle;
- version;
- creation and update timestamps;
- minimal authorized Creator identification when required;
- authorized navigation identity.

Full original content and source reference are not required in list results.
Complete Creator details, rationale, and related sensitive fields must not be
requested merely to compose a list.

#### Capture Inspection/Detail Projection

The inspection/detail projection may contain, after explicit item-level
authorization:

- every authorized list/summary field;
- original content;
- source reference;
- authorized Creator details;
- complete permitted canonical context;
- authorized supersession and replacement information.

Both projections remain owned by Universal Capture. For PATCH-029, the
Journal-owned Capture read adapter is an authorized application-level extension
over the canonical Capture application service: it maps canonical authorized
read results into these projections and may add only the bounded projection and
count behavior defined here. It may not query Capture persistence, import the
Capture repository, change Capture DTOs, or transfer canonical ownership.
Sensitive fields may be
omitted according to canonical authorization. Field omission must not disclose
that protected data exists and must not be interpreted as a canonical null.

No plaintext Capture content, source reference, or rationale may enter counts,
navigation metadata, errors, logs, diagnostics, or unavailable/empty-state
DTOs.
### 3.5 Repository Contracts

IDS-029 introduces no Journal repository contract.

Journal must not define:

- `EngineeringJournalRepository`;
- Journal persistence methods;
- saved view-membership methods;
- read/unread persistence;
- workspace-preference persistence;
- Journal-specific count tables;
- Journal cache-as-authority contracts.

Canonical repositories remain private implementation details of their owning capabilities.

An infrastructure adapter may use an approved canonical application service that itself uses canonical repositories. Journal transport and application orchestration must not access those repositories directly.

### 3.6 Canonical Read Boundaries

Canonical read boundaries must guarantee:

1. Organization scope is applied before record resolution.
2. Project scope is resolved within the trusted Organization.
3. Optional Workspace and Engineering Object filters cannot widen scope.
4. Lifecycle filtering uses Universal Capture canonical values.
5. Authorization is applied before returning candidates to Journal.
6. Totals represent only the authorized result set.
7. Deterministic ordering uses canonical values without changing authority.
8. Concurrent lifecycle or authorization changes cannot leave stale results authoritative.
9. A requested Capture UUID is resolved only inside its authorized scope.
10. Supersession-chain members are authorized independently.

Journal may perform presentation filtering only on the already authorized canonical projection. It must not use presentation filtering as authorization.

### 3.7 Authorization Contracts

The authorization contracts distinguish:

| Contract outcome | Meaning |
|---|---|
| Authorized | The actor may receive the requested canonical projection |
| Protected not found | The resource is absent or unauthorized; the cause is not disclosed |
| Capability unavailable | The required canonical capability has no approved active contract |
| Invalid presentation criteria | Noncanonical sorting, filtering, grouping, or view selection is invalid without revealing canonical information |

Authorization contracts must not return:

- boolean existence indicators for protected resources;
- denial reasons containing protected scope information;
- unauthorized resource metadata;
- pre-authorization counts;
- alternative Organization suggestions;
- hidden membership hints.

### 3.8 Protected Disclosure Contracts

Protected disclosure applies to:

- workspace scope;
- view availability where availability could reveal protected configuration;
- item membership;
- item fields;
- counts;
- replacement identity;
- supersession-chain members;
- navigation targets;
- future capability state;
- diagnostics and errors.

The protected-not-found contract must be stable across:

- missing resource;
- inactive actor;
- disabled Organization;
- nonmember Organization;
- cross-Organization access;
- cross-Project access;
- cross-Workspace access;
- cross-Engineering-Object access;
- revoked access;
- inaccessible related resource.

Transport mapping is defined later and must not change this application meaning.

### 3.9 Capability Availability Contract

Capability availability is architecture-controlled, not inferred from data.

For PATCH-029:

| Capability/View | Availability |
|---|---|
| Universal Capture / New Capture | Available subject to authorization |
| Universal Capture / Inbox | Available subject to authorization |
| Universal Capture / Superseded | Available subject to authorization |
| Draft authority / Drafts | Unavailable |
| Engineering Review / Under Review | Unavailable |
| Organizational Memory publication / Published | Unavailable |

An unavailable capability:

- produces no member query;
- produces no synthetic record;
- produces no authoritative zero count;
- creates no fallback repository lookup;
- cannot borrow state from Capture or another capability.

### 3.10 Repository and Port Invariants

1. Journal owns its application ports.
2. Journal owns no repository or persistence port.
3. Canonical repositories remain private to canonical capabilities.
4. No port exposes ORM models or database sessions.
5. No global Capture lookup is permitted.
6. Canonical reads are Organization- and Project-scoped.
7. Authorization filtering occurs before results reach composition.
8. Protected totals accompany only authorized result sets.
9. Journal cannot invoke canonical write methods.
10. Infrastructure adapters cannot become business authority.
11. Missing capability adapters cannot be replaced by inferred data.
12. Ports preserve canonical identity, provenance, context, version, and history.
13. Dependency direction remains one-way.
14. No shared-table ownership is introduced.
15. Section 3 grants no implementation authority.

### 3.11 Section Decision

```text
Journal-owned read ports: DEFINED
Journal repository: NONE
Canonical repositories: PRIVATE TO OWNERS
ORM/session exposure: PROHIBITED
Authorization contract: DEFINED
Protected disclosure contract: DEFINED
Global Capture lookup: PROHIBITED
Canonical write access: PROHIBITED
Implementation authorization: NOT GRANTED
Section 3 architecture acceptance: PASS
```

## 4. DTO and Projection Architecture

### 4.1 DTO Boundary

Journal DTOs are immutable application and transport-neutral projections of authorized canonical information.

They:

- carry no behavior;
- own no canonical state;
- are not ORM models;
- are not Aggregates;
- are not persistence records;
- do not determine authorization;
- do not initiate lifecycle transitions;
- do not become input to canonical business decisions.

Exact serialization and transport mapping remain outside this section.

### 4.2 Controlled DTO Vocabularies

#### Journal View

The closed PATCH-029 view vocabulary is:

- `new_capture`;
- `inbox`;
- `drafts`;
- `under_review`;
- `published`;
- `superseded`.

No alias or additional value is authorized.

#### View Availability

- `available`;
- `unavailable`.

Availability does not imply authorization to a particular item.

#### Workspace Result State

- `content`;
- `authorized_empty`;
- `filtered_empty`;
- `capability_unavailable`.

Protected not found is an application outcome and is not a successful workspace DTO state.

#### Navigation Target Kind

- `journal_view`;
- `canonical_capture`;
- `canonical_capability`.

No URL, router path, framework identifier, or provider-specific value belongs to this vocabulary.

### 4.3 Workspace Composition DTO

`EngineeringJournalWorkspaceDTO` contains:

| Field | Contract |
|---|---|
| `view` | One approved Journal view |
| `availability` | View availability |
| `result_state` | One successful workspace result state |
| `scope` | Authorized workspace-scope DTO |
| `view_content` | View DTO appropriate to the selected view |
| `navigation` | Authorized navigation collection |
| `presentation` | Applied noncanonical presentation criteria |
| `canonical_freshness` | Highest disclosed canonical Capture version in the returned page, or absent when the response contains no Capture member |

`canonical_freshness` is a presentation hint only. It uses only versions already
authorized in the returned page, is recalculated for every response, and must
not introduce a Journal version, claim global synchronization, or expose a
version belonging to an omitted item.

### 4.4 Workspace Scope DTO

`EngineeringJournalScopeDTO` contains only authorized context:

- Organization UUID;
- optional Project identifier;
- optional Workspace identifier;
- optional discipline;
- optional Engineering Object UUID.

Rules:

- Organization is derived from trusted authenticated context;
- absent Project denotes only the authorized Project-less shell;
- Project is mandatory for member-bearing PATCH-029 views;
- when Project is absent, Workspace, discipline, and Engineering Object are also absent;
- optional context must remain inside the same canonical scope;
- omission due to authorization must not be represented as canonical absence;
- the DTO grants no future access.

The Project-less shell may additionally contain a
`EngineeringJournalProjectSelectionPageDTO` with bounded authorized Project
choices. Each choice contains only the canonical Project identifier and approved
display name. The page contains page number, page size, returned-item count, and
whether another page exists; it contains no global or unauthorized total. This
DTO is absent after a Project has been selected.

The Project identifier is represented exactly as defined by the canonical
Project capability. Engineering Journal owns no Project identity format and
must neither redefine nor transform it.

### 4.5 View DTOs

#### New Capture View DTO

Contains:

- availability;
- authorized current scope;
- canonical Capture creation navigation;
- no item collection;
- no count;
- no draft state.

#### Inbox View DTO

Contains:

- ordered authorized Capture item DTOs;
- protected authorized count DTO;
- presentation criteria;
- successful empty state when applicable.

Every member must have canonical lifecycle `captured`.

#### Drafts View DTO

Contains:

- `capability_unavailable`;
- no members;
- no authoritative count;
- no inferred draft metadata.

#### Under Review View DTO

Contains:

- `capability_unavailable`;
- no members;
- no authoritative count;
- no reviewer, Review, or decision metadata.

#### Published View DTO

Contains:

- `capability_unavailable`;
- no members;
- no authoritative count;
- no publication, approval, or Organizational Memory metadata.

#### Superseded View DTO

Contains:

- ordered authorized superseded Capture item DTOs;
- protected authorized count DTO;
- presentation criteria;
- successful empty state when applicable.

Every member must have canonical lifecycle `superseded`.

### 4.6 Capture Projection DTOs

#### Engineering Journal Capture List Item DTO

`EngineeringJournalCaptureListItemDTO` is a minimal Journal projection of an
authorized canonical Capture. It may contain:

- canonical Capture UUID;
- Project identifier;
- optional Workspace identifier;
- optional discipline;
- optional Engineering Object UUID;
- source kind;
- minimal authorized Creator identification when required;
- canonical lifecycle;
- version;
- creation and update timestamps;
- authorized navigation metadata.

Full original content, source reference, complete Creator details, rationale,
and related sensitive fields are not required in list results.

#### Engineering Journal Capture Detail DTO

`EngineeringJournalCaptureDetailDTO` is returned only after explicit item-level
authorization. It may contain:

- every authorized list-item field;
- authorized original content;
- authorized source reference;
- authorized Creator details;
- complete permitted canonical context;
- authorized replacement UUID and supersession information.

Neither DTO may contain:

- Journal ID;
- Journal lifecycle;
- saved membership;
- read/unread or triage state;
- inferred title or summary presented as canonical;
- Review state;
- publication standing;
- Organizational Memory standing;
- inferred Knowledge Graph relationships;
- AI-derived fields;
- authorization diagnostics.

Where the canonical contract omits a protected field, the Journal DTO must not
convert that omission into a false canonical value or disclose that protected
data exists.

Plaintext content, source reference, and rationale are prohibited from count,
navigation, error, log, diagnostic, and unavailable/empty-state DTOs.
### 4.7 Count DTO

`EngineeringJournalCountDTO` contains:

| Field | Contract |
|---|---|
| `authorized_total` | Total authorized canonical members before temporary presentation filtering |
| `filtered_total` | Total authorized members after valid temporary filtering and before pagination |
| `visible_total` | Number of items included in the current bounded page or window |
| `is_authoritative_for_scope` | True only when scope and capability are authorized and available |

Rules:

- all totals are computed after authorization;
- `visible_total` must never be used as `filtered_total` or `authorized_total`;
- pagination must not change `authorized_total` or `filtered_total`;
- `filtered_total` equals `authorized_total` when no filter is active;
- unavailable views receive no count DTO;
- protected-not-found outcomes receive no count DTO;
- hidden records affect no disclosed total;
- `visible_total` never exceeds a calculated `filtered_total` or
  `authorized_total`;
- no approximate or global total is permitted;
- count values are noncanonical presentation projections;
- no plaintext Capture content, source reference, or rationale may enter a
  count DTO.

Filtered-result metadata may indicate that presentation criteria produce no
visible items without disclosing excluded or unauthorized records.
### 4.8 Empty-State DTO

`EngineeringJournalEmptyStateDTO` contains:

- result-state value;
- safe Human-facing semantic category;
- whether noncanonical presentation criteria are active;
- permitted recovery-navigation choices.

It must not contain:

- protected identifiers;
- hidden totals;
- denial reason;
- inaccessible scope metadata;
- inferred capability records;
- implementation diagnostics.

Behavior:

| State | DTO rule |
|---|---|
| Authorized empty | Allowed only after scope authorization and available canonical query |
| Filtered empty | Allowed only after authorization and application of valid presentation criteria |
| Capability unavailable | Identifies unavailable authority without implying records exist |
| Protected not found | No successful empty-state DTO is returned |

### 4.9 Navigation DTO

`EngineeringJournalNavigationDTO` contains:

| Field | Contract |
|---|---|
| `target_kind` | Controlled navigation target kind |
| `canonical_target_id` | Canonical identifier when authorized and applicable |
| `target_view` | Approved Journal view when the target is another Journal view |
| `return_context` | Minimal noncanonical context required for a safe Journal return |
| `requires_reauthorization` | Always true for canonical-resource and cross-capability destinations |

It must not contain:

- invented Journal resource identifiers;
- unauthorized destination identifiers;
- hard-coded transport paths;
- router names;
- database keys unrelated to canonical identity;
- embedded access grants;
- protected content in return context.

A navigation DTO describes a possible destination. It does not prove access to that destination.

### 4.10 Presentation Criteria DTO

`EngineeringJournalPresentationDTO` is a closed contract containing only:

| Field | Allowed values and bounds |
|---|---|
| `sort` | `created_at_desc` only for PATCH-029 |
| `source_kind` | Optional exact canonical source-kind value already accepted by Universal Capture |
| `discipline` | Optional exact canonical discipline value inside the authorized scope |
| `page` | Positive integer; default `1` |
| `size` | Integer from `1` through `100`; default `20` |
| `layout` | `list` only for PATCH-029 |

Grouping and free-text filtering are not authorized in PATCH-029. Multiple
filters use logical AND. Filters operate only inside the authorized lifecycle
membership of the selected view. Unknown fields, unsupported values, repeated
scalar fields, and incoherent criteria produce `invalid_presentation_criteria`.

These criteria:

- do not change canonical membership;
- do not affect authorization;
- do not persist engineering state;
- do not create a Journal lifecycle;
- cannot introduce free-text authority classification;
- cannot request cross-Organization scope;
- cannot select an unapproved Journal view.

No Implementation Plan or transport may add criteria or values to this closed
contract.

### 4.11 Projection Rules

1. Project only from already authorized canonical projections.
2. Preserve canonical Capture UUID exactly.
3. Preserve canonical lifecycle terminology.
4. Preserve Organization, Project, Workspace, discipline, and Engineering Object meaning.
5. Preserve provenance, version, and timestamps without reinterpretation.
6. Include only fields necessary for the selected Journal view.
7. Omit inaccessible fields without revealing that protected content exists.
8. Never derive canonical state from DTO values.
9. Never use DTOs as Aggregate commands.
10. Never persist Journal DTOs as canonical records.
11. Apply deterministic ordering to equivalent authorized inputs.
12. Recompose after refresh rather than treating an earlier DTO as authority.
13. Unavailable capabilities produce unavailable DTOs, not inferred member DTOs.
14. Protected outcomes produce no success DTO.
15. Cross-capability DTO fields require separately approved canonical contracts.

### 4.12 DTO Invariants

1. DTOs are immutable, behavior-free projections.
2. DTOs contain no ORM entities or database sessions.
3. DTOs preserve canonical identity without aliases.
4. Workspace DTOs represent exactly one selected view.
5. New Capture contains no members or count.
6. Inbox contains only authorized `captured` Captures.
7. Superseded contains only authorized `superseded` Captures.
8. Drafts, Under Review, and Published are unavailable under PATCH-029.
9. Counts include authorized records only.
10. Protected not found is never represented as authorized empty.
11. Navigation always requires destination reauthorization.
12. Presentation criteria remain noncanonical.
13. DTOs introduce no Review, publication, Organizational Memory, Knowledge Graph, or AI authority.
14. DTOs define no API, database, or persistence contract.
15. Section 4 grants no implementation authority.

### 4.13 Section Decision

```text
Workspace DTO architecture: DEFINED
View DTO architecture: DEFINED
Navigation DTO architecture: DEFINED
Count protection DTO: DEFINED
Empty-state DTO: DEFINED
Canonical identity preservation: REQUIRED
ORM/session exposure: PROHIBITED
Journal-owned canonical state: NONE
API/database/persistence design: NOT INCLUDED
Implementation authorization: NOT GRANTED
Sections 2–4 architecture acceptance: PASS
```

## 5. Security and Authorization Architecture

### 5.1 Security Objective

Engineering Journal is an authorization-constrained, read-only presentation boundary.

Every workspace result must be composed from:

- an authenticated active Human;
- a trusted active Organization membership;
- an authorized Project context when member-bearing views are requested;
- independently authorized optional Workspace and Engineering Object context;
- authorized canonical Capture projections;
- approved capability contracts.

Previously visible information, deep links, temporary presentation state, cached projections, and client-supplied identifiers provide no continuing authority.

### 5.2 Trusted Actor and Organization Context

The authenticated context must establish:

- active User identity;
- active User status;
- active Organization identity;
- active Organization status;
- active Organization Membership;
- current selected Organization derived from trusted server-side context.

Journal must not:

- accept `organization_id` as client-trusted authority;
- infer Organization from a Project, Workspace, Capture, or URL;
- fall back to another Organization;
- disclose available Organizations through an authorization failure;
- reuse a revoked Organization context.

Inactive Users, disabled Organizations, and nonmembers receive protected behavior before workspace information is disclosed.

### 5.3 Project Context

Member-bearing Journal views require one explicit or safely restored trusted Project context.

When no single trusted Project is established:

- Journal must not infer or auto-select a Project;
- Capture members and counts must not be queried;
- the application may return only an authorized workspace shell;
- the shell may contain a protected Project-selection projection;
- the projection contains only Projects the actor is authorized to access;
- hidden Projects, hidden alternatives, and cross-Organization totals are omitted;
- member-bearing views begin only after explicit selection or trusted restoration.

A Project identifier supplied during navigation is a lookup candidate, not authority. It must be resolved inside the trusted active Organization before any Project-dependent information is disclosed.

### 5.4 Workspace, Discipline, and Engineering Object Scope

Optional scope must narrow the authorized Project; it must never widen it.

A Workspace must:

- exist in the trusted Organization;
- belong to the authorized Project;
- be accessible to the actor;
- provide the canonical discipline context.

An Engineering Object must:

- exist within the same Organization, Project, and Workspace;
- be accessible to the actor;
- remain compatible with the governed discipline;
- be resolved without global lookup.

Discipline is canonical context derived through existing governed capabilities. Journal must not accept discipline as independent authorization evidence or reclassify Capture records.

### 5.5 Authorization-Before-Disclosure Flow

Every Journal operation follows this security order:

```text
1. Authenticate actor
2. Verify active actor
3. Resolve trusted active Organization
4. Verify active Organization and Membership
5. Resolve requested view
6. Resolve Project inside the trusted Organization
7. Resolve optional Workspace inside the Project
8. Resolve optional Engineering Object inside the Workspace
9. Determine canonical capability availability
10. Query authorized canonical members
11. Apply field-level disclosure
12. Calculate authorized counts
13. Compose navigation
14. Return the protected Journal projection
```

No later stage may execute when an earlier required security stage fails.

### 5.6 Protected-Not-Found Behavior

Protected not found is the stable application outcome for an absent or unauthorized protected resource.

It applies to:

- Project;
- Workspace;
- Engineering Object;
- Capture;
- replacement Capture;
- supersession-chain member;
- deep-link target;
- future capability resource;
- cross-Organization resource;
- cross-Project resource;
- cross-Workspace resource;
- revoked resource.

The outcome must not disclose:

- whether the resource exists;
- its identifier or canonical state;
- its Journal membership;
- whether it contributes to a count;
- the owning Organization or Project;
- the actor or role associated with it;
- whether denial resulted from inactivity, nonmembership, scope mismatch, or absence.

Protected not found is not represented as an authorized empty-state DTO.

### 5.7 Count Protection

All count values are calculated after authorization.

Count semantics are:

| Count | Meaning |
|---|---|
| `authorized_total` | Total authorized canonical members before temporary noncanonical presentation filtering |
| `filtered_total` | Total authorized members after valid temporary filtering and before pagination |
| `visible_total` | Number of items included in the current bounded page or window |

Rules:

- `visible_total` never substitutes for `filtered_total` or `authorized_total`;
- pagination changes only `visible_total`;
- pagination must not change `authorized_total` or `filtered_total`;
- `filtered_total` equals `authorized_total` when no filter is active;
- unavailable and protected-not-found outcomes expose no count DTO;
- hidden records affect no disclosed total;
- a Project-less workspace shell queries no Capture count;
- no approximate, global, cached-as-authority, or pre-authorization count is permitted.

### 5.8 Field-Level Disclosure

Two distinct canonical Capture projections are required.

#### List/Summary Projection

The list projection contains only the minimum authorized fields required for:

- canonical identification;
- view membership;
- safe Human recognition;
- canonical lifecycle visibility;
- stable navigation.

Full original content, source reference, complete Creator details, rationale, and sensitive related metadata are not required and must not be included by default.

#### Inspection/Detail Projection

The detail projection may include authorized:

- original content;
- source reference;
- Creator details;
- complete permitted context;
- canonical version and lifecycle;
- permitted supersession information.

Detail fields require explicit item authorization after scope authorization.

Field omission must not reveal that protected information exists. Omitted protected data must not be converted into a false canonical null or diagnostic flag.

Plaintext Capture content, source reference, rationale, and other protected engineering text must never enter:

- count DTOs;
- navigation metadata;
- empty or unavailable states;
- authorization errors;
- transport errors;
- logs;
- diagnostics;
- tracing attributes;
- exception messages.

### 5.9 Deep-Link Reauthorization

Every deep link must:

1. authenticate the current actor;
2. resolve the current trusted Organization;
3. resolve the canonical target inside its governed scope;
4. reauthorize every disclosed resource;
5. preserve canonical UUID identity;
6. return protected not found when absent or unauthorized.

A deep link does not carry authorization from the session that created or previously opened it.

Return-context information must contain no protected Capture plaintext or embedded access grant.

### 5.10 Refresh Reauthorization

Refresh repeats the complete security and composition flow.

It must:

- revalidate actor and Organization status;
- revalidate Membership;
- revalidate Project, Workspace, and Engineering Object scope;
- reread current canonical state;
- reapply field-level disclosure;
- recompute membership and counts;
- remove revoked or no-longer-qualifying items;
- avoid preserving stale projections as authority.

Concurrent changes may cause an item to move, disappear, or become protected. Journal must not disclose the protected cause when the actor is no longer authorized.

### 5.11 Unavailable-Capability Protection

Drafts, Under Review, and Published remain unavailable until their canonical capabilities are separately approved.

Unavailable views:

- issue no member query;
- expose no count DTO;
- return no inferred record;
- expose no placeholder authority;
- do not query another capability as fallback;
- do not disclose whether hypothetical future records exist;
- carry no Review, publication, memory, graph, or AI metadata.

Capability unavailability may be reported only as a safe architectural condition, not as protected resource existence.

### 5.12 Security Invariants

1. Authorization always precedes disclosure.
2. Organization identity is trusted only from authenticated active context.
3. Member-bearing views require trusted Project context.
4. No global Project, Workspace, Engineering Object, or Capture lookup is allowed.
5. Optional context only narrows authorized scope.
6. Each canonical resource is independently authorized.
7. Counts are calculated only from authorized members.
8. Field-level disclosure follows least disclosure.
9. List projections do not require full sensitive content.
10. Detail projections require explicit item authorization.
11. Protected not found is stable across absence and denial.
12. Deep links and refresh always reauthorize.
13. Revocation overrides previous visibility.
14. Unavailable capabilities expose no members or counts.
15. No protected plaintext enters counts, navigation, errors, logs, diagnostics, or empty states.
16. Journal presentation grants no canonical command authority.
17. Journal introduces no persistence, Aggregate, Repository, Unit of Work, lifecycle, Review, Organizational Memory, Knowledge Graph, or AI authority.

### 5.13 Section Decision

```text
Trusted actor and Organization context: REQUIRED
Client-trusted Organization identity: PROHIBITED
Trusted Project context for member views: REQUIRED
Authorization before disclosure: REQUIRED
Protected not found: REQUIRED
Field-level disclosure: DEFINED
Count protection: DEFINED
Deep-link reauthorization: REQUIRED
Refresh reauthorization: REQUIRED
Unavailable-capability protection: REQUIRED
Security authority expansion: NONE
Implementation authorization: NOT GRANTED
```

## 6. Transport, Performance, and Operational Boundaries

### 6.1 Transport Responsibility

The Engineering Journal transport boundary may:

- validate transport-level syntax;
- obtain authenticated request context;
- invoke the Journal application boundary;
- pass temporary noncanonical presentation criteria;
- map stable application outcomes;
- return approved DTO projections.

Transport must not:

- contain view-membership business rules;
- resolve Organization authority independently;
- query persistence;
- access canonical repositories;
- receive ORM models;
- calculate authorization or canonical totals;
- infer unavailable capability state;
- invoke Capture Aggregate mutation;
- own transaction boundaries.

### 6.2 Router Boundary

The Journal router boundary is limited to these read-only operations:

| Method and path | Purpose | Success contract |
|---|---|---|
| `GET /api/v1/engineering-journal` | Obtain the authorized workspace shell; an optional `project_id` selects trusted Project context | `EngineeringJournalWorkspaceDTO` |
| `GET /api/v1/engineering-journal/views/{view}` | Obtain or refresh one approved Journal view in authorized scope | `EngineeringJournalWorkspaceDTO` |
| `GET /api/v1/engineering-journal/captures/{capture_id}` | Obtain one explicitly authorized canonical Capture detail projection | `EngineeringJournalCaptureDetailDTO` |

The workspace-shell operation returns the bounded Project-selection projection
when `project_id` is absent. `workspace_id` and `engineering_object_id` are
optional query refinements but are invalid when `project_id` is absent. View
requests accept only the closed presentation criteria in Section 4.10.
Navigation metadata is embedded in successful DTOs and has no separate route.
Refresh repeats the same `GET` operation and has no separate route or command.

New Capture creation remains at the existing Universal Capture transport boundary. Journal may expose authorized navigation to it but must not duplicate that command route.

No routes for Review, publication, Organizational Memory, Knowledge Graph mutation, AI, or additional Journal views are authorized.

### 6.3 Request-Scoped Composition

The request-scoped composition root constructs:

- authenticated-context adapter;
- trusted scope-authorization adapter;
- canonical Capture read adapter;
- canonical navigation adapter;
- capability-availability policy;
- Journal application service;
- DTO projection collaborators.

Request-scoped infrastructure may be used to construct approved adapters.

It must not:

- treat a database session as authority;
- expose sessions to transport business behavior;
- permit direct persistence queries;
- bypass Journal-owned ports;
- inject canonical repositories or ORM entities into transport;
- create a Journal Unit of Work;
- retain protected engineering state beyond the request as authority.

### 6.4 Stable Outcome Mapping

Transport must map application outcomes consistently:

| Application outcome | Transport meaning |
|---|---|
| Successful workspace content | Authorized Journal projection |
| Authorized empty | Authorized available view with no qualifying members |
| Filtered empty | Authorized view with no members matching valid temporary criteria |
| Capability unavailable | Required canonical authority is unavailable |
| Protected not found | Resource absent or unauthorized without distinction |
| Invalid presentation criteria | Safe validation failure without canonical disclosure |

Stable HTTP mapping is:

| Application outcome | HTTP status |
|---|---|
| Successful workspace content, authorized empty, or filtered empty | `200` |
| Capability unavailable | `200` with `capability_unavailable` workspace state |
| Protected not found | `404` with the existing protected-not-found error envelope |
| Invalid presentation criteria | `422` with the existing validation-error envelope |

All successful bodies serialize only the DTO fields defined by this IDS.
Transport must use the repository's existing error-envelope convention and
must not introduce Journal-specific disclosure fields.

Infrastructure, database, repository, and authorization diagnostics must not cross the transport boundary.

### 6.5 Pagination and Bounded Queries

Member-bearing views must use bounded queries.

Baseline bounds:

- default page size: 20;
- maximum page size: 100;
- page number: positive integer;
- no unbounded member list;
- no unbounded Project-selection list;
- no unbounded supersession traversal through Journal composition.

Pagination must:

- occur after trusted scope establishment;
- preserve deterministic ordering;
- leave `authorized_total` unchanged;
- leave `filtered_total` unchanged;
- set `visible_total` to the current returned item count;
- avoid disclosing hidden records through page metadata.

A request beyond the authorized result range returns an authorized empty page without implying hidden records.

### 6.6 Deterministic Ordering

For Inbox and Superseded, the canonical ordering contract is:

```text
created_at descending
then canonical Capture UUID descending as deterministic tie-breaker
```

Temporary approved ordering may alter presentation only when:

- it operates on authorized canonical fields;
- it remains deterministic;
- it cannot widen scope;
- it cannot expose omitted sensitive fields;
- it does not change membership or totals.

Ordering by hidden fields, plaintext content, source reference, authorization standing, or inferred authority is prohibited.

### 6.7 Performance Boundaries

Journal composition must satisfy these structural performance boundaries:

- Project-less workspace shell performs no Capture member or count query;
- unavailable views perform no canonical member or count query;
- one member-bearing page request uses one bounded canonical page operation
  returning `authorized_total`, `filtered_total`, and `visible_total`;
- list projection must not trigger one canonical request per item;
- field-level list projection must not load detail-only plaintext solely for list rendering;
- detail inspection resolves one explicitly requested Capture inside authorized scope;
- related-resource indicators must not introduce unbounded traversal;
- maximum returned member count is 100;
- composition must remain deterministic without in-memory loading of an unbounded authorized result set.

Numeric latency objectives require runtime measurement and an approved implementation plan; this IDS does not invent infrastructure-independent latency guarantees.

### 6.8 Partial Capability Degradation

If an optional canonical capability is unavailable:

- available Universal Capture views remain usable;
- only remaining authorized canonical information is presented;
- unavailable projections are explicitly identified as unavailable;
- no fallback source is queried;
- no previous projection is preserved as authority;
- no fabricated membership or count is returned;
- failure remains isolated from canonical Capture meaning.

Universal Capture unavailability prevents Capture-backed member composition but does not authorize cached or duplicated Journal state.

### 6.9 Concurrency and Freshness

Journal has no write concurrency contract because it owns no writes.

For reads:

- canonical version and lifecycle take precedence over earlier projection state;
- refresh must reflect the latest authorized canonical response available to the request;
- an item changed concurrently may move, disappear, or become protected;
- stale projection must never become business authority;
- detail inspection must not infer that a previously listed version remains current;
- totals and returned items must come from a canonical read contract with defined consistency semantics;
- Journal must not reconcile conflicting canonical states through presentation decisions.

Specific database isolation and locking strategies remain owned by canonical capabilities.

### 6.10 Logging and Diagnostics Restrictions

Journal logs and diagnostics may contain only operationally necessary non-sensitive information.

They must not contain:

- original Capture content;
- source reference;
- withdrawal or supersession rationale;
- protected Creator details;
- hidden Project, Workspace, Engineering Object, Capture, or replacement identifiers;
- unauthorized totals;
- complete DTO payloads;
- authorization-denial details that reveal protected scope;
- request parameters containing protected engineering plaintext.

Safe operational correlation may use approved correlation identifiers that do not encode engineering content or authority.

Errors must use stable categories and must not include repository queries, database values, adapter internals, or protected plaintext.

### 6.11 No Journal Write Transaction

Journal workspace operations:

- create no Journal transaction;
- perform no commit;
- own no rollback;
- write no Audit record merely because a view was opened;
- emit no domain event or outbox event;
- create no idempotency record;
- coordinate no cross-capability transaction.

New Capture creation remains a separate canonical command owned atomically by the existing Universal Capture Unit of Work.

### 6.12 Operational Invariants

1. Router behavior remains thin and transport-only.
2. Composition is request-scoped.
3. Stable application outcomes are transport-neutral.
4. Every list is bounded.
5. Ordering is deterministic.
6. List reads avoid per-item canonical queries.
7. Detail plaintext is not required for list projection.
8. Partial failure cannot fabricate authority.
9. Current canonical state overrides stale presentation.
10. Diagnostics exclude protected plaintext.
11. Journal creates no write transaction.
12. No operational mechanism becomes canonical authority.
13. No API, persistence, migration, or implementation file is authorized by this section.

### 6.13 Section Decision

```text
Transport boundary: DEFINED
Router responsibility: THIN / READ-ONLY
Request-scoped composition: REQUIRED
Stable outcomes: DEFINED
Default page size: 20
Maximum page size: 100
Deterministic ordering: REQUIRED
Partial degradation: REQUIRED
Freshness authority: CANONICAL STATE
Protected logging: REQUIRED
Journal write transaction: NONE
Implementation authorization: NOT GRANTED
```

## 7. Testing Strategy and Quality Gates

### 7.1 Testing Objective

Testing must prove behavior, boundaries, disclosure safety, and architectural compliance.

Source inspection alone is insufficient when behavioral evidence is required. Tests must not depend on execution order, shared mutable state, or development/deployment data.

### 7.2 Unit Tests

Unit tests must cover:

- approved view vocabulary;
- view-availability policy;
- canonical membership rules;
- canonical-state precedence;
- deterministic composition;
- deterministic ordering;
- DTO mapping;
- list/detail field separation;
- count DTO invariants;
- empty-state selection;
- navigation metadata;
- presentation-criteria validation;
- prohibited unavailable-view inference.

Unit tests require no Journal persistence because none is authorized.

### 7.3 Application Tests

Application tests must cover:

- default workspace shell;
- explicit trusted Project selection;
- safe restoration of trusted Project context;
- Inbox composition;
- Superseded composition;
- unavailable Drafts;
- unavailable Under Review;
- unavailable Published;
- refresh recomposition;
- detail inspection;
- protected navigation;
- graceful partial composition;
- adapter failure isolation;
- deterministic repeated requests.

Mocks or fakes must implement Journal-owned ports and must not introduce repository or ORM dependencies into the application layer.

### 7.4 Project-Less Workspace Tests

Required cases:

1. no trusted Project context returns only an authorized workspace shell;
2. no Capture member query occurs;
3. no Capture count query occurs;
4. no Project is inferred or auto-selected;
5. authorized Project-selection projection contains only authorized Projects;
6. hidden Projects and counts are omitted;
7. one available Project is not silently selected;
8. member-bearing views begin only after explicit selection or trusted restoration;
9. cross-Organization Project candidates remain protected;
10. a revoked restored Project context is rejected safely.

### 7.5 View-Membership Tests

Required cases:

- canonical `captured` Capture appears in Inbox;
- canonical `superseded` Capture appears in Superseded;
- withdrawn Capture appears in no approved member-bearing view;
- New Capture has no members or count;
- Drafts has no members;
- Under Review has no members;
- Published has no members;
- Journal interaction does not change membership;
- temporary presentation criteria do not change canonical membership;
- concurrent canonical-state change recomputes membership;
- one primary view applies unless explicitly governed otherwise;
- no additional Journal view is accepted.

### 7.6 Count-Semantics Tests

Required cases:

- `authorized_total` includes all authorized canonical members before temporary filtering;
- `filtered_total` includes filtered authorized members before pagination;
- `filtered_total` equals `authorized_total` when no filter is active;
- `visible_total` equals the current returned item count;
- `visible_total` never substitutes for another total;
- pagination does not alter `authorized_total`;
- pagination does not alter `filtered_total`;
- hidden records affect no total;
- protected-not-found exposes no count DTO;
- unavailable view exposes no count DTO;
- Project-less shell performs no Capture count;
- authorized empty may return zero only after authorization;
- filtered empty remains distinguishable from authorized empty.

### 7.7 List and Detail Disclosure Tests

Required cases:

- list projection includes only minimum authorized identification and navigation fields;
- list projection does not require full original content;
- list projection does not require source reference;
- list projection does not expose full Creator details;
- explicit authorized inspection may expose permitted detail fields;
- unauthorized inspection returns protected not found;
- field omission does not disclose that protected data exists;
- no plaintext content or source reference enters count DTOs;
- no plaintext enters navigation metadata;
- no plaintext enters empty or unavailable states;
- no plaintext enters errors, logs, or diagnostics.

### 7.8 Cross-Scope Denial Tests

Tests must deny without disclosure:

- inactive User;
- disabled Organization;
- nonmember Organization;
- cross-Organization Project;
- cross-Project Workspace;
- cross-Workspace Engineering Object;
- cross-Organization Capture;
- cross-Project Capture;
- cross-Workspace Capture;
- inaccessible replacement Capture;
- inaccessible supersession-chain member;
- revoked Project context;
- revoked deep-link destination.

Same-Organization and same-governed-scope success cases are required for every corresponding denial path.

### 7.9 Protected-Not-Found Matrix

The same protected outcome must be verified for:

| Resource operation | Missing | Unauthorized | Cross-scope | Revoked |
|---|---:|---:|---:|---:|
| Project context | Required | Required | Required | Required |
| Workspace context | Required | Required | Required | Required |
| Engineering Object context | Required | Required | Required | Required |
| Capture inspection | Required | Required | Required | Required |
| Capture navigation | Required | Required | Required | Required |
| Replacement navigation | Required | Required | Required | Required |
| Supersession-chain navigation | Required | Required | Required | Required |

Tests must verify absence of protected identifiers, counts, membership hints, and denial reasons.

### 7.10 Unavailable-View Tests

For Drafts, Under Review, and Published, tests must prove:

- explicit capability-unavailable outcome;
- no member query;
- no count query;
- no synthetic zero;
- no inferred records;
- no Review, publication, memory, graph, or AI metadata;
- no fallback to Capture lifecycle;
- no plaintext;
- no authority-bearing navigation.

### 7.11 Deep-Link and Refresh Tests

Deep-link tests must prove:

- canonical UUID preservation;
- current actor reauthorization;
- current Organization reauthorization;
- Project and optional context reauthorization;
- protected-not-found after revocation;
- no embedded access grant;
- safe return context without protected plaintext.

Refresh tests must prove:

- complete reauthorization;
- latest canonical lifecycle is reflected;
- changed membership moves or removes an item;
- changed counts are recomputed;
- revoked records disappear;
- protected causes remain undisclosed;
- stale DTO state is not reused as authority.

### 7.12 Transport Tests

Transport tests must cover:

- thin delegation to Journal application;
- authenticated context requirement;
- safe validation of view and presentation criteria;
- stable mapping of content, empty, filtered-empty, unavailable, and protected outcomes;
- DTO response boundary;
- no ORM or repository exposure;
- no canonical exception leakage;
- no protected plaintext in errors;
- no unauthorized routes or mutation operations;
- existing Universal Capture creation authority remains separate.

Exact routes and serialization require later implementation authorization and must remain bounded by accepted IDS behavior.

### 7.13 Integration Tests

Integration tests must verify:

- request-scoped dependency composition;
- Journal-owned port usage;
- canonical Capture adapter behavior;
- Organization- and Project-scoped reads;
- bounded pagination;
- accurate authorized totals;
- deterministic ordering;
- minimal list projection;
- authorized detail projection;
- no Journal writes;
- no Audit, outbox, or idempotency writes from Journal reads;
- partial capability degradation;
- current repository router registration without unrelated-module modification.

### 7.14 Performance Tests

Performance evidence must prove structurally:

- no Capture query for Project-less shell;
- no member or count query for unavailable views;
- bounded page size;
- no N+1 canonical read for list items;
- detail fields are not loaded solely for list projection;
- deterministic query count for equivalent requests;
- no unbounded in-memory result loading;
- full page of 100 authorized members remains within the approved bounded query contract.

Runtime latency thresholds may be authorized only by an executable Implementation Plan based on measured repository conditions.

### 7.15 Exact-Scope and Prohibited-Pattern Checks

Static and behavioral checks must verify absence of:

- Journal ORM model;
- Journal migration;
- Journal database table;
- Journal repository;
- Journal Unit of Work;
- Journal Aggregate;
- Journal lifecycle;
- direct persistence query from transport or application;
- canonical repository injection into transport;
- global Capture lookup;
- client-trusted Organization identity;
- additional Journal views;
- Review commands or authority;
- publication or Organizational Memory commands;
- Knowledge Graph mutation or inferred authority;
- AI provider or AI behavior;
- protected plaintext in operational outputs;
- unrelated module modification.

### 7.16 Regression Strategy

Validation order:

1. static compilation and contract checks;
2. focused unit tests;
3. application and port tests;
4. security and disclosure tests;
5. transport tests;
6. integration tests;
7. performance-boundary tests;
8. adjacent Universal Capture, Project, Workspace, Engineering Object, Relationship, and Evidence regressions;
9. complete backend regression in one process;
10. deterministic reordered focused-suite execution;
11. repository diff and authorized-file verification.

No development or deployment migration is required or authorized.

### 7.17 Quality Gates

| Gate | Requirement |
|---|---|
| QG-M1 | Manifesto Alignment PASS at IDS, Sprint, and Final checkpoints |
| QG-6 | Domain boundary PASS: no Journal Aggregate or lifecycle introduced |
| QG-7 | Persistence boundary PASS: no Journal persistence, Repository, Unit of Work, table, or migration |
| QG-8 | Application and Security PASS: orchestration, authorization, protected disclosure, counts, and field minimization |
| QG-9 | Transport PASS: thin boundary, stable outcomes, DTO safety, no unauthorized operations |
| QG-10 | Regression PASS: focused, adjacent, and full backend regression with deterministic shared-process behavior |
| QG-11 | Human Final Review PASS after independent implementation review |
| QG-12 | Delivery Authorization PASS before commit or push |

QG-7 is satisfied through positive boundary evidence and prohibited-pattern verification, not by creating persistence tests for nonexistent Journal storage.

### 7.18 Section Decision

```text
Testing strategy: COMPLETE
Behavioral security evidence: REQUIRED
Project-less shell tests: REQUIRED
Membership tests: REQUIRED
Count semantics tests: REQUIRED
List/detail disclosure tests: REQUIRED
Protected-not-found matrix: REQUIRED
Unavailable-view tests: REQUIRED
Deep-link/refresh tests: REQUIRED
Full regression: REQUIRED
QG-M1: REQUIRED
Implementation authorization: NOT GRANTED
```

## 8. Sprint and Delivery Design

### 8.1 Delivery Objective

Deliver Engineering Journal as a bounded, read-only Human workspace over Universal Capture while preserving all accepted EDS and IDS boundaries.

Delivery must introduce no Journal persistence, Aggregate, lifecycle, Repository, Unit of Work, migration, Review authority, Organizational Memory authority, Knowledge Graph authority, AI behavior, or additional view.

### 8.2 Dependency Order

Implementation must follow this order:

```text
Contracts and DTO boundaries
        ↓
Read ports and canonical adapters
        ↓
Application orchestration and authorization
        ↓
Request-scoped dependency composition
        ↓
Transport boundary and router registration
        ↓
Security, integration, and performance evidence
        ↓
Independent Final Review
        ↓
Human QG-11
        ↓
QG-12 Delivery Authorization
```

No later Sprint may compensate for an unaccepted earlier boundary.

### 8.3 Sprint 1 — Contracts and Projection Foundation

#### Objective

Establish Journal-owned read contracts and noncanonical DTO boundaries without transport or persistence.

#### Deliverable Categories

- controlled six-view vocabulary;
- availability and result-state vocabulary;
- workspace and scope DTOs;
- list/summary Capture projection;
- inspection/detail Capture projection;
- count DTO with three-level semantics;
- empty and unavailable-state DTOs;
- navigation DTO;
- temporary presentation-criteria DTO;
- Journal-owned read and authorization ports;
- capability-availability contract;
- unit tests and prohibited-pattern checks.

#### Entry Gate

- IDS-029 accepted;
- executable Implementation Plan accepted;
- IRR-029 readiness PASS;
- exact file set authorized;
- QG-M1 Sprint checkpoint PASS.

#### Exit Gate

- contract tests pass;
- DTO invariants pass;
- list/detail separation passes;
- count semantics pass;
- no persistence or authority expansion detected;
- independent Sprint review PASS.

### 8.4 Sprint 2 — Application Composition and Security

#### Objective

Implement read-only Journal orchestration, trusted scope resolution, view composition, and protected disclosure.

#### Deliverable Categories

- Engineering Journal application boundary;
- Project-less workspace shell;
- protected Project-selection projection;
- Inbox composition;
- Superseded composition;
- unavailable Drafts, Under Review, and Published behavior;
- deterministic membership and ordering;
- protected counts;
- detail inspection orchestration;
- deep-link navigation composition;
- refresh reauthorization;
- graceful partial capability degradation;
- request-scoped dependency composition;
- application, security, and performance-boundary tests.

#### Entry Gate

- Sprint 1 PASS;
- accepted contracts unchanged;
- authorized canonical adapters available;
- QG-M1 Sprint checkpoint PASS.

#### Exit Gate

- application tests pass;
- Project-less behavior passes;
- cross-scope denial matrix passes;
- protected-not-found matrix passes;
- count protection passes;
- field-level disclosure passes;
- no Journal write side effects;
- adjacent regression passes;
- independent Sprint review PASS.

### 8.5 Sprint 3 — Transport and Final Integration

#### Objective

Expose the accepted Journal application behavior through a thin transport boundary and complete final evidence.

#### Deliverable Categories

- Journal transport DTO mapping;
- thin router boundary;
- router registration;
- authenticated dependency wiring;
- stable outcome mapping;
- bounded pagination;
- transport tests;
- end-to-end Journal integration tests;
- prohibited-route checks;
- logging and diagnostic plaintext-exclusion tests;
- complete backend regression;
- exact-scope validation;
- independent final implementation review package.

#### Entry Gate

- Sprint 2 PASS;
- no unresolved security findings;
- QG-M1 Sprint checkpoint PASS.

#### Exit Gate

- QG-8 Application and Security PASS;
- QG-9 Transport PASS;
- QG-10 Regression PASS;
- QG-M1 Final PASS;
- no unauthorized files or semantic expansion;
- Independent Final Review PASS;
- ready for Human QG-11.

### 8.6 Exact Deliverable Categories

Implementation authorization, when separately granted, may cover only:

- Journal controlled vocabularies;
- Journal transport-neutral DTOs;
- Journal application ports;
- canonical read adapters;
- Journal application orchestration;
- request-scoped dependency composition;
- thin Journal transport boundary;
- router registration;
- focused Journal tests;
- necessary direct documentation status updates.

This IDS does not itself authorize exact files. The executable Implementation Plan must map every category to an exact repository file set before IRR-029 can grant implementation readiness.

### 8.7 Independent Review Readiness

The implementation becomes ready for Independent Final Review only after evidence confirms:

- all three Sprints PASS;
- exact approved file scope;
- no architectural scope expansion;
- canonical Capture ownership preserved;
- no Journal persistence or write transaction;
- authorization-before-disclosure;
- protected count semantics;
- list/detail disclosure separation;
- deep-link and refresh reauthorization;
- unavailable-view safety;
- deterministic composition and ordering;
- focused, adjacent, and full regression PASS;
- QG-M1 Final PASS.

### 8.8 Human QG-11 Readiness

Human QG-11 may begin only after Independent Final Review PASS.

The Human review must verify:

- engineering usefulness and Human-first workflow;
- exact PATCH-029 scope;
- EDS and IDS compliance;
- Manifesto alignment;
- canonical authority preservation;
- security and disclosure behavior;
- no unauthorized implementation files;
- no hidden persistence or authority;
- regression evidence;
- delivery scope readiness.

### 8.9 QG-12 Delivery Boundary

QG-12 may authorize only the exact reviewed file set that passed QG-11.

QG-12 must separately state:

- authorized commit scope;
- commit authorization;
- push authorization;
- migration authorization;
- excluded files;
- delivery evidence required for closure.

Commit and push remain prohibited before QG-12 PASS.

No development or deployment migration belongs to PATCH-029.

### 8.10 Explicit Non-Goals

PATCH-029 delivery must not include:

- Journal persistence;
- Journal Aggregate;
- Journal Repository;
- Journal Unit of Work;
- Journal lifecycle;
- saved read/unread or triage state;
- durable presentation preferences;
- new database schema;
- migration;
- Capture lifecycle changes;
- new Capture commands;
- Review workflow or authority;
- publication or Organizational Memory behavior;
- Knowledge Graph expansion or mutation;
- AI integration or provider dependency;
- additional Journal views;
- unrelated frontend or backend modules;
- Infrastructure redesign;
- production or deployment actions.

### 8.11 Migration Posture

```text
Journal schema migration: NOT REQUIRED
Development migration: NOT AUTHORIZED
Deployment migration: NOT AUTHORIZED
Existing canonical data migration: NOT REQUIRED
Project data modification: NOT AUTHORIZED
Organization data modification: NOT AUTHORIZED
```

Any finding that appears to require Journal persistence or migration returns to architecture review rather than expanding implementation scope.

### 8.12 Delivery Risks and Controls

| Risk | Required control |
|---|---|
| Journal becomes a second source of truth | No persistence, Repository, Unit of Work, Aggregate, or canonical DTO reuse |
| Project inferred without trusted context | Project-less shell and explicit trusted selection |
| Hidden records leak through totals | Three-level authorized count semantics and security tests |
| Sensitive plaintext appears in lists or diagnostics | Minimal list projection and plaintext-exclusion matrix |
| Transport gains business behavior | Thin router and Journal-owned application ports |
| Canonical repository becomes shared | Canonical application adapter boundary |
| Stale presentation becomes authority | Refresh reauthorization and canonical-state precedence |
| Future views fabricate authority | Explicit unavailable behavior and no member queries |
| Delivery expands scope | Exact file authorization, independent review, QG-11, and QG-12 |

### 8.13 Section Decision

```text
Sprint count: THREE
Dependency order: DEFINED
Sprint entry/exit gates: DEFINED
Exact deliverable categories: DEFINED
Exact file authorization: DEFERRED TO IMPLEMENTATION PLAN
Independent review readiness: DEFINED
Human QG-11 readiness: DEFINED
QG-12 boundary: DEFINED
Journal migration: NOT REQUIRED / NOT AUTHORIZED
Implementation authorization: NOT GRANTED
```

## Final IDS Decision

### Architecture Completeness

IDS-029 Sections 1–8 completely translate accepted EDS-029 into a bounded implementation specification for Engineering Journal.

The specification defines:

- application boundaries;
- read-only use cases;
- canonical read ports;
- absence of Journal repositories;
- DTO and projection contracts;
- authorization and protected disclosure;
- request-scoped dependency composition;
- transport and operational boundaries;
- performance constraints;
- testing strategy;
- Quality Gates;
- Sprint and delivery boundaries.

### Implementation-Specification Completeness

The specification is complete for Independent IDS Review.

It intentionally defers:

- exact repository file authorization;
- executable validation commands;
- measured latency thresholds;
- implementation sequencing at file level;
- commit and delivery scope.

Those belong to the separately governed executable Implementation Plan and IRR-029. Their deferral grants no implementation discretion to change IDS semantics.

### Remaining Assumptions

- Universal Capture remains the accepted PATCH-028 canonical baseline.
- Existing authenticated Organization context remains authoritative.
- Existing Project, Workspace, discipline, and Engineering Object authorization contracts remain available.
- The Journal-owned Capture read adapter uses the approved canonical Capture
  application boundary and supplies only the bounded projection and count
  extension defined in Sections 3.3 and 3.4, without direct persistence access
  or transfer of repository ownership.
- Draft, Engineering Review, Published Organizational Memory, and AI authorities remain unavailable.
- No Journal persistence or migration is required.
- Human EDS Acceptance, IDS design authorization, Independent IDS Review PASS,
  and Human IDS Acceptance are recorded. Implementation Plan design is
  authorized, but implementation remains unauthorized.

If an assumption fails, IDS-029 returns to architecture review.

### Risks

The principal risks are:

- accidental direct repository reuse;
- Project inference without trusted context;
- unauthorized totals;
- excessive sensitive fields in list projections;
- protected plaintext leakage;
- transport-layer business logic;
- stale projections treated as authority;
- future capability state inferred before approval;
- exact implementation scope expanding beyond PATCH-029.

Sections 1–8 define controls and required evidence for each risk.

### Final Decision

```text
IDS-029 completion status: ACCEPTED / COMPLETE
Completed scope: SECTIONS 1–8
Consistency with accepted EDS-029: PASS
Manifesto alignment: PASS
Universal Capture canonical authority: PRESERVED
Engineering Journal role: READ-ONLY / PRESENTATION-ONLY
Journal Aggregate: NONE
Journal Repository: NONE
Journal Unit of Work: NONE
Journal persistence: NONE
Journal lifecycle: NONE
Review authority: NOT INTRODUCED
Organizational Memory authority: NOT INTRODUCED
Engineering Knowledge Graph authority: NOT INTRODUCED
AI behavior: NONE
Direct persistence access: PROHIBITED
Client-trusted Organization identity: PROHIBITED
Unauthorized counts: PROHIBITED
Protected plaintext leakage: PROHIBITED
Journal migration: NOT REQUIRED / NOT AUTHORIZED
Remaining Findings: NONE
Independent IDS Review: PASS
Human IDS Acceptance: PASS
Focused Project Identity Amendment: PASS
Internal consistency review: PASS
IDS contract consistency review: PASS
Implementation Plan dependency review: PASS — RECONCILED
Permission for Implementation Plan Design: GRANTED
Implementation-Plan-029: ACCEPTED / EXECUTABLE
Human Implementation Plan Acceptance: PASS
Permission for IRR-029: GRANTED
IRR-029: PENDING REPEATED REVIEW
Sprint 1: NOT YET AUTHORIZED
Implementation authority: NOT GRANTED
```
