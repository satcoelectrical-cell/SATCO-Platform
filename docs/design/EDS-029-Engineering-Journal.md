# EDS-029 — Engineering Journal

## 1. Engineering Journal Architecture Contract

### 1.1 Document Control

| Field | Value |
|---|---|
| Document ID | EDS-029 |
| Related PATCH | PATCH-029 — Engineering Journal |
| Design scope | Sections 1–8 — Complete Engineering Journal Architecture |
| Status | ACCEPTED / COMPLETE |
| Capability | Engineering Journal |
| Phase | Phase 2 Engineering Intelligence |
| Architecture style | Docs-First / Human-first Workspace |
| Implementation authority | NOT GRANTED |
| Architecture Review | AR-029 PASS |
| Manifesto Compliance | PASS |
| Human Architecture Acceptance | PASS |
| Independent EDS Review | PASS |
| Human EDS Acceptance | PASS |

This section defines architectural meaning only. It does not design or
authorize implementation, API contracts, database structures, migrations,
Review workflow, AI behavior, commit, push, or deployment.

### 1.2 Design Objective

Engineering Journal is the Human-first daily workspace through which engineers
access and organize authorized Universal Capture records.

Engineering Journal is the default landing workspace presented to authenticated
engineers. It serves as the primary daily engineering workspace while remaining
independent from canonical engineering authority.

Engineering Journal:

- owns no persistence;
- owns no aggregate or canonical lifecycle;
- creates no copy of Capture content;
- introduces no independent Knowledge Inbox;
- introduces no Review, publication, Organizational Memory, Knowledge Graph,
  or AI authority;
- derives every visible item and state from an approved canonical authority;
- preserves authorization before disclosure.

Universal Capture remains the canonical source for Capture identity, content,
provenance, engineering context, version, lifecycle, and history.

### 1.3 Bounded-Context Responsibility

Engineering Journal owns only:

- Human workspace composition;
- work-view semantics;
- authorized projection of canonical records;
- navigation between views and canonical resources;
- presentation of authority state without changing that state;
- protected item and count disclosure;
- explicit indication when a downstream canonical capability is unavailable.

Engineering Journal does not own:

- Capture records or lifecycle;
- drafts as durable records;
- review submissions or decisions;
- approval or rejection;
- publication transitions;
- Organizational Memory;
- Engineering Relationships or Knowledge Graph semantics;
- AI-generated content or recommendations;
- independent user-maintained Journal state.

A Journal view is a read-oriented interpretation of canonical authority. It is
never evidence of authority by itself.

### 1.4 Architectural Invariants

1. A Journal item always represents an existing canonical record.
2. Canonical Capture UUID remains the item identity.
3. Journal must not issue a second identity for the same Capture.
4. Capture content, provenance, context, version, lifecycle, and history remain
   unchanged.
5. View membership must be deterministic from canonical state and authorized
   context.
6. A record may appear in more than one view only when the documented canonical
   rules explicitly permit it.
7. Presentation state must never be persisted as canonical engineering state by
   Journal.
8. Absence from a view must not imply absence from the platform.
9. Counts must be calculated only after authorization filtering.
10. Unauthorized scopes, records, identifiers, memberships, and counts must not
    be disclosed.
11. Journal must not infer Review, publication, knowledge, or memory authority.
12. When a required future authority does not exist, the corresponding view
    remains explicitly unavailable or empty; Journal must not simulate that
    authority.
13. Every navigation operation must reauthorize access against the current
    authenticated Organization and governed Project/Workspace boundaries.
14. Client-provided Organization identity is never trusted as an authority
    source.
15. Journal may provide temporary noncanonical presentation preferences (sorting,
    filtering, grouping, layout, or similar workspace preferences). These
    preferences are not canonical engineering state, create no engineering
    authority, and never affect Capture identity, lifecycle, context, provenance,
    authorization, Review, Organizational Memory, or Knowledge Graph semantics.

### 1.5 Approved Work Views

#### New Capture

| Concern | Contract |
|---|---|
| Purpose | Provide the Human entry point for creating a new canonical Universal Capture record. |
| Canonical authority | Universal Capture creation contract. |
| Membership rule | This is an action-oriented workspace view, not a stored collection. It has no independent members. After successful Capture creation, the resulting canonical Capture may enter Inbox according to its canonical lifecycle and authorization state. |
| Authorization rule | The Human actor must be active and authorized for the selected Organization, Project, optional Workspace, and optional Engineering Object context before any scoped information is disclosed or Capture creation is permitted. |
| Protected-count behavior | No item count is defined. The view must not expose counts or existence information for inaccessible Projects, Workspaces, objects, or Captures. |
| Navigation behavior | Navigation may begin from an authorized context. Successful creation navigates using the canonical Capture UUID and preserved context. No Journal identity is created. |

#### Inbox

| Concern | Contract |
|---|---|
| Purpose | Present authorized active Capture records that remain available for Human attention without declaring them reviewed, approved, published, or reusable knowledge. |
| Canonical authority | Universal Capture. |
| Membership rule | A record is included only when its canonical Capture lifecycle is `captured`, it remains accessible to the actor, and no approved downstream canonical authority places it in a later governed state. Until such downstream authorities exist, Inbox is the Human work view for authorized active Captures. |
| Authorization rule | Membership is evaluated only after authenticated Organization, Project, Workspace, Engineering Object, and record-level authorization. |
| Protected-count behavior | The count includes only records the actor is currently authorized to access. No global, pre-filter, cross-Organization, cross-Project, or hidden-record total may be exposed. An inaccessible scope receives protected-not-found behavior, not a revealing zero count. |
| Navigation behavior | Navigation opens the canonical Capture through its UUID after fresh authorization. Journal may present its context and history but cannot mutate canonical meaning through navigation. |

Inbox is exclusively an Engineering Journal view. It is not an independent
bounded context, service, aggregate, persistence model, API authority, or PATCH.

#### Drafts

| Concern | Contract |
|---|---|
| Purpose | Reserve a Human workspace view for canonical draft material when a future approved capability defines and owns draft authority. |
| Canonical authority | No approved canonical draft authority exists within PATCH-029. Universal Capture does not equate `captured` with `draft`. |
| Membership rule | No record may be classified as Draft solely by Journal. Until a separately approved canonical draft authority exists, membership is empty or the view is explicitly unavailable. |
| Authorization rule | When a future authority exists, both the underlying Capture and the canonical draft resource must be authorized before membership or content is disclosed. |
| Protected-count behavior | Before canonical authority exists, no synthetic count is produced. After future integration, only jointly authorized records may contribute to the count. |
| Navigation behavior | Before canonical authority exists, navigation communicates unavailability without manufacturing a draft resource. Future navigation must preserve the originating Capture UUID, provenance, context, version, and history. |

#### Under Review

| Concern | Contract |
|---|---|
| Purpose | Present records that a future Engineering Review capability has canonically accepted into an active Human Review process. |
| Canonical authority | Future Engineering Review bounded context. |
| Membership rule | Membership requires an explicit canonical active-review state from Engineering Review. Journal cannot submit, approve, reject, return, qualify, or transition a record. Until Engineering Review exists, membership is empty or explicitly unavailable. |
| Authorization rule | The actor must be authorized for both the underlying Capture and the Review resource. Reviewer identity, review existence, and review state are protected information. |
| Protected-count behavior | Counts include only jointly authorized active Review resources. Hidden Reviews and inaccessible Captures must not affect disclosed totals. |
| Navigation behavior | Navigation may open an authorized Review workspace while retaining a traceable link to the canonical Capture UUID. Journal cannot perform Review decisions. |

#### Published

| Concern | Contract |
|---|---|
| Purpose | Present material that a future canonical authority has explicitly approved for governed publication or responsible reuse. |
| Canonical authority | Future Engineering Review decision together with the future Organizational Memory publication authority. |
| Membership rule | Membership requires an explicit canonical publication state. Capture existence, repeated use, Journal placement, or Review initiation is insufficient. Until the required authorities exist, membership is empty or explicitly unavailable. |
| Authorization rule | The actor must be authorized to access the underlying Capture and the published Organizational Memory representation within its approved scope and limitations. |
| Protected-count behavior | Only authorized published resources contribute to the displayed count. Journal must not disclose hidden publication existence, totals, or authority state. |
| Navigation behavior | Navigation opens the canonical published representation and preserves traceability to the originating Capture UUID, provenance, context, versions, Review decision, and history. |

#### Superseded

| Concern | Contract |
|---|---|
| Purpose | Allow Humans to inspect Capture records that have been canonically replaced while preserving historical traceability. |
| Canonical authority | Universal Capture supersession lifecycle and supersession chain. |
| Membership rule | A Capture is included only when its canonical lifecycle is `superseded`. Journal must not infer supersession from similarity, chronology, links, or user preference. |
| Authorization rule | The actor must be authorized to access the superseded Capture. Navigation to a replacement or supersession chain independently requires authorization for every disclosed record. |
| Protected-count behavior | The count includes only authorized superseded Captures. Inaccessible predecessors, replacements, chain members, and cross-scope records must not be counted or disclosed. |
| Navigation behavior | Navigation preserves the original Capture UUID and immutable history. Replacement and chain navigation use canonical Capture identities and protected-not-found behavior for inaccessible members. |

### 1.6 View Authority Summary

| Journal view | Canonical authority | PATCH-029 availability |
|---|---|---|
| New Capture | Universal Capture creation contract | Available as a Human action surface |
| Inbox | Universal Capture active lifecycle | Available |
| Drafts | Future canonical draft authority | Empty or explicitly unavailable |
| Under Review | Future Engineering Review | Empty or explicitly unavailable |
| Published | Future Engineering Review and Organizational Memory | Empty or explicitly unavailable |
| Superseded | Universal Capture supersession lifecycle | Available |

The presence of all six views in the Journal information architecture does not
authorize Journal to fabricate states for capabilities that have not yet been
approved.

### 1.7 Dependency Direction

The permitted dependency direction is:

```text
Engineering Journal
        ↓
Application-owned read contracts
        ↓
Universal Capture and other approved canonical authorities
```

Future integrations may extend the read side as follows:

```text
Engineering Journal
├── Universal Capture
├── Engineering Review
├── Engineering Knowledge Graph
└── Organizational Memory
```

The following directions are prohibited:

- Universal Capture depending on Engineering Journal;
- canonical aggregates importing Journal concepts;
- Journal directly owning or changing downstream authority state;
- Journal coupling canonical capabilities through shared persistence;
- Journal bypassing application authorization boundaries;
- future AI providers becoming a Journal or Capture dependency.

Engineering Journal composes authorized information. Canonical capabilities
remain independently governed and do not depend on Journal presentation.

### 1.8 Future Integration Boundaries

#### Engineering Review

Engineering Review will own Review submission, active Review state, reviewer
authority, decisions, qualifications, rejection, return, and approval history.

Journal may display authorized Review state and navigate to Review. It may not
own or execute Review decisions.

#### Engineering Knowledge Graph

Engineering Knowledge Graph will own governed relationship semantics and graph
traversal authority.

Journal may present authorized contextual connections associated with a
Capture. It may not create relationships by view placement, infer graph truth,
or treat navigation links as governed Engineering Relationships.

#### Organizational Memory

Organizational Memory will own trusted publication, responsible reuse, approved
scope, limitations, and memory lifecycle.

Journal may display authorized published material and trace it back to Capture
and Review history. It may not publish, approve, or promote Capture directly
into Organizational Memory.

Future bounded capabilities may contribute additional Journal work views only
through approved canonical authorities and explicit application contracts.
Engineering Journal must never invent view authority, shared persistence
ownership, or independent lifecycle semantics.

### 1.9 Identity, Provenance, Context, Version, and History Preservation

Every Journal representation must retain or resolve through the canonical
source:

- Capture UUID;
- Human Creator identity subject to authorization;
- Organization and Project scope;
- optional Workspace and Engineering Object context;
- discipline derived through its canonical context;
- source kind and source reference;
- original Capture content;
- creation and update timestamps;
- current canonical version;
- lifecycle state;
- withdrawal or supersession history;
- supersession references and chain;
- future Review and publication provenance when those authorities exist.

Journal must not rewrite, summarize, replace, detach, flatten, or silently omit
canonical meaning in a way that changes the engineering record.

### 1.10 Manifesto Alignment

This design preserves:

- **Engineering First:** the workspace is organized around Human Engineering
  Work.
- **Capture Once:** Journal reuses canonical Capture identity and content.
- **Human Authority:** no Review or publication authority is inferred.
- **Engineering Context Is Sacred:** governed Organization, Project, Workspace,
  discipline, and object context remain attached.
- **Evidence Before Assumption:** Journal placement does not transform
  experience into evidence or fact.
- **Intelligence Before Automation:** the Human workflow precedes AI, which
  remains out of scope.
- **Organizational Ownership:** authorization and disclosure remain
  Organization-scoped.
- **Traceability and Accountability:** provenance, version, lifecycle, and
  history remain canonical and navigable.

### 1.11 Section Decision

```text
Bounded-context definition: PROPOSED
Persistence ownership: NONE
Canonical Capture ownership: PRESERVED
Review authority: NOT INTRODUCED
AI dependency: NONE
API/database/implementation design: NOT INCLUDED
Architecture Acceptance: PASS
```

## 2. Engineering Journal Workspace Behavior

### 2.1 Human Workflow Philosophy

Engineering Journal is the default Human Engineering Workspace for deliberate,
context-aware interaction with authorized Engineering Experience. It supports
Human attention and continuity of work; it does not automate engineering
judgment or convert presentation activity into canonical authority.

The workspace follows these principles:

- the Human engineer remains the initiating and interpreting authority;
- original Capture is preserved before any later interpretation or reuse;
- canonical context and lifecycle meaning take precedence over convenience;
- the workspace presents what is known without manufacturing missing state;
- Journal organization assists attention but never asserts truth, Evidence,
  approval, publication, or Organizational Memory standing;
- actions belonging to future bounded capabilities remain unavailable until
  those capabilities and their Human authority contracts are approved;
- Intelligence Before Automation governs every workspace evolution.

### 2.2 Workspace Navigation Principles

The six approved views form one coherent workspace over canonical authorities:

- **New Capture** is the Human entry surface for initiating canonical Capture;
- **Inbox** presents authorized active Captures requiring Human attention;
- **Drafts** represents future canonically governed draft work and remains empty
  or explicitly unavailable until that authority exists;
- **Under Review** represents future canonically active Review work and remains
  empty or explicitly unavailable until Engineering Review exists;
- **Published** represents future canonically published material and remains
  empty or explicitly unavailable until its governing authorities exist;
- **Superseded** presents authorized Captures whose canonical lifecycle is
  `superseded`.

Navigation must:

1. preserve the current authenticated Organization boundary;
2. preserve relevant Project, optional Workspace, discipline, and Engineering
   Object context when the destination permits it;
3. use canonical identity when navigating to an item;
4. reauthorize the destination independently before disclosure;
5. distinguish an unavailable capability from an authorized view with no
   members;
6. avoid implying that moving between screens changes canonical state;
7. allow the Human to return to the originating authorized workspace context
   without creating a Journal-owned history record.

Temporary noncanonical presentation sorting, filtering, grouping, layout, or similar
preferences may alter presentation only. They do not alter membership,
authority, canonical ordering, context, or lifecycle.

Every Engineering Journal view shall support stable deep-link navigation to
canonical Capture resources without creating alternative identities, duplicated
resources, or navigation-owned engineering state. Every deep link must
reauthorize the current actor and scope before disclosing the canonical
resource.

### 2.3 User Interaction Model

The Journal interaction model consists of four architectural interaction types:

| Interaction | Architectural meaning |
|---|---|
| Enter a view | Request an authorized projection of canonical records for the current governed context. |
| Inspect an item | Open an authorized representation resolved through the canonical UUID and current canonical state. |
| Initiate New Capture | Enter the Human Capture flow governed entirely by Universal Capture. |
| Navigate to a canonical capability | Leave or extend the Journal presentation boundary and enter an independently authorized canonical capability. |

Selecting, opening, sorting, filtering, grouping, or leaving an item does not:

- acknowledge or dismiss canonical Engineering Experience;
- change Capture lifecycle or version;
- create a draft;
- initiate or decide a Review;
- publish material;
- create Organizational Memory;
- create or modify a Knowledge Graph relationship;
- constitute engineering approval or acceptance.

Journal must communicate canonical state and the authority behind it in a form
that does not confuse presentation availability with engineering standing.

After an authorized action or navigation completes, the engineer should remain
within the Engineering Journal workspace whenever the relevant authority
remains within Journal. Navigation to another bounded capability shall occur
only when canonical authority belongs to that capability, while preserving a
safe return path to Journal.

### 2.4 View Transitions

Journal defines navigation between views, not lifecycle transitions. An item
changes view membership only when its canonical authority changes the state
from which membership is derived.

| Observed workspace movement | Required canonical cause | Journal authority |
|---|---|---|
| New Capture to Inbox | Successful creation of an authorized canonical Capture with lifecycle `captured` | Reflect only |
| Inbox to Drafts | Future canonical draft authority establishes qualifying draft state | None; unavailable in PATCH-029 |
| Inbox or Drafts to Under Review | Future Engineering Review establishes active Review state | None; unavailable in PATCH-029 |
| Under Review to Published | Future Review and publication authorities establish publishable and published state | None; unavailable in PATCH-029 |
| Inbox to Superseded | Universal Capture canonically supersedes the Capture | Reflect only |
| Any view to no visible membership | Canonical state no longer qualifies, access is revoked, governing context changes, or the record becomes inaccessible | Reflect only; disclose no cause that is itself unauthorized |

No drag, drop, menu choice, selection, or navigation gesture may independently
perform one of these movements. A future capability may expose its own governed
Human command, but Journal view movement remains a consequence rather than the
authority for that command.

Withdrawal does not create an additional Journal view. A withdrawn Capture is
not placed into another approved view unless a future approved canonical
authority and PATCH explicitly establish a qualifying rule.

### 2.5 Cross-View Consistency Rules

1. Every representation of the same Capture uses the same canonical UUID.
2. Canonical content, provenance, context, lifecycle, version, and history must
   have the same meaning in every view.
3. A view-specific label must not override or rename canonical lifecycle or
   authority state.
4. Membership is recalculated from the same canonical authority rules whenever
   the same governed context is evaluated.
5. Sorting, filtering, grouping, and layout must not change canonical
   membership or disclosed counts.
6. A record must not remain presented under a stale authority label after the
   workspace has learned of a newer canonical version.
7. When multiple canonical authorities eventually contribute to a view, all
   required authorization and membership conditions must hold before the item
   is disclosed.
8. An inaccessible related resource must not be exposed through badges, counts,
   labels, navigation targets, placeholders, or inferred transitions.
9. Empty, unavailable, and access-protected states remain semantically distinct.
10. Journal must not reconcile conflicting canonical authorities by inventing a
    preferred state; the conflict must remain undisclosed where required or be
    represented as unavailable for governed Human resolution by the owning
    capability.

### 2.6 Refresh Behavior

Refresh means obtaining a current authorized workspace projection from the
relevant canonical authorities. It is not a Journal lifecycle event and creates
no engineering record.

On refresh, Journal must conceptually:

1. re-establish the current authenticated Human and active Organization scope;
2. re-evaluate authorization before resolving membership, items, or counts;
3. re-evaluate view membership from current canonical state;
4. present the current canonical version and lifecycle meaning;
5. remove records that are no longer authorized or no longer qualify;
6. include newly authorized qualifying records without creating Journal copies;
7. preserve temporary presentation preferences only when doing so does not
   disclose or retain protected engineering information.

A previously visible item is not guaranteed to remain visible. Refresh must not
reveal whether disappearance resulted from deletion, lifecycle change,
supersession, context change, membership change, or access revocation when the
Human is no longer authorized to know that cause.

Journal must not claim real-time completeness, create a synchronization
authority, or silently treat a stale projection as canonical. The detailed
delivery, timing, caching, and synchronization mechanisms are implementation
concerns and are not defined by this EDS.

Refresh operations must tolerate concurrent canonical-state changes.
Engineering Journal shall reflect the latest authorized canonical state and
must not preserve stale presentation state as engineering authority. If view
membership changes during refresh, the item shall move, disappear, or become
protected according to the latest canonical state and authorization.

### 2.7 Authorization Behavior

Authorization precedes every workspace disclosure, including:

- view availability within a governed scope;
- item membership;
- item content and metadata;
- view and filtered counts;
- canonical state labels;
- related-resource indicators;
- navigation destinations;
- refresh results.

Journal derives Organization context only from the authenticated active
membership boundary. It does not trust a client-selected Organization identity
as authorization evidence.

Project, optional Workspace, discipline, Engineering Object, Capture, and any
future Review, Knowledge Graph, or Organizational Memory boundary must be
authorized through their owning canonical capability. Authorization in one
view or for one resource never grants access to another view, related resource,
replacement Capture, supersession-chain member, or future capability.

For protected resources and scopes, Journal uses protected-not-found behavior.
It must not disclose existence, membership, count contribution, identifier,
state, provenance, relationship, or the reason access was denied.

Access revocation takes precedence over previously obtained presentation state.
Temporary noncanonical presentation preferences must not preserve protected content or act as
an authorization cache.

### 2.8 Empty-State Behavior

Journal distinguishes four non-content states:

| State | Meaning | Required presentation semantics |
|---|---|---|
| Authorized empty | The Human is authorized for the scope, the canonical capability is available, and no authorized records satisfy membership. | May state that no qualifying items are currently available. |
| Filtered empty | Authorized records may exist, but none satisfy temporary presentation filters. | May indicate that the current presentation preferences produce no visible results without disclosing hidden records. |
| Capability unavailable | The canonical authority required for the view has not been approved or is not available. | Must identify the view as unavailable; must not present a synthetic zero, placeholder record, or implied future state. |
| Protected not found | The requested scope, item, or destination is absent or unauthorized. | Must not distinguish absence from denial or disclose counts, identifiers, state, or membership. |

An empty state must not encourage bypassing governed context, creating duplicate
Capture records, or treating Capture as reviewed or published knowledge.

New Capture may remain available only when the Human is authorized to create a
canonical Capture in the current context. Its availability must not imply that
the current Inbox or any future view contains records.

### 2.9 Future Extensibility

Future bounded capabilities may contribute additional Journal work views or
extend the authority behind an approved view only when all of the following are
true:

- the capability and view semantics are separately approved through SATCO
  governance;
- one explicit canonical authority owns the contributed state;
- integration occurs through an explicit application-owned contract;
- dependency direction remains from Journal toward that contract;
- canonical identity, provenance, context, version, and history remain
  traceable;
- authorization-before-disclosure and protected-count behavior are preserved;
- Journal gains no shared persistence ownership or independent lifecycle;
- the extension does not reinterpret an existing view by implication;
- unavailable authorities remain visibly unavailable rather than simulated.

Future Review, Engineering Knowledge Graph, and Organizational Memory
capabilities may enrich workspace projection and navigation only within their
approved authority. AI remains outside Engineering Journal and cannot become a
condition for navigation, membership, refresh, authorization, or workspace
operation.

### 2.10 Workspace Invariants

1. Engineering Journal remains the default Human Engineering Workspace, not a
   canonical engineering authority.
2. Universal Capture remains canonical for Capture identity, content,
   provenance, context, version, lifecycle, and history.
3. Journal owns no persistence, aggregate, lifecycle, or durable engineering
   state.
4. The workspace contains only the six currently approved views.
5. View membership is derived from current canonical authority and never from
   presentation gestures.
6. Navigation never constitutes a canonical transition.
7. Refresh reauthorizes before disclosure and cannot preserve revoked access.
8. Items, metadata, membership, counts, and destinations are protected equally.
9. Empty, filtered-empty, unavailable, and protected-not-found states are not
   interchangeable.
10. Temporary presentation preferences affect presentation only.
11. Journal introduces no Review authority or Review command.
12. Journal introduces no publication or Organizational Memory authority.
13. Journal introduces no Engineering Knowledge Graph authority.
14. Journal introduces no AI dependency, recommendation, or autonomous action.
15. No behavior in this section authorizes an API, database, migration,
    implementation mechanism, commit, push, or deployment.

### 2.11 Section Decision

```text
Human workflow behavior: PROPOSED
Workspace navigation: DEFINED
View movement authority: CANONICAL AUTHORITIES ONLY
Persistence ownership: NONE
Review authority: NOT INTRODUCED
Organizational Memory authority: NOT INTRODUCED
AI dependency: NONE
API/database/implementation design: NOT INCLUDED
Architecture Acceptance: PASS
```

## 3. Engineering Journal View Semantics

### 3.1 Semantic Foundation

Engineering Journal views are authorized Human-work projections over canonical
engineering state. They do not constitute records, aggregates, lifecycle
states, queues, folders, classifications, or independent sources of truth.

Universal Capture is the sole source of truth for Capture identity, content,
provenance, context, version, lifecycle, withdrawal, and supersession. Where a
future approved bounded capability owns an additional state, that state remains
owned by that capability and can influence Journal presentation only through an
explicit application contract. Journal never becomes the source of that state.

Entry and exit describe changes in view eligibility. They are consequences of
canonical state and current authorization, not Journal commands or transitions.

### 3.2 New Capture

| Semantic concern | Contract |
|---|---|
| Canonical authority | Universal Capture creation authority. Journal provides only the Human entry surface. |
| Entry conditions | The authenticated active Human is authorized to initiate Capture in the current Organization and selected Project, with any optional Workspace and Engineering Object context independently authorized. |
| Exit conditions | The Human leaves the entry surface, creation is cancelled, authorization or context ceases to be valid, or Universal Capture completes canonical creation. |
| Membership rules | New Capture is an action-oriented view and has no record membership. In-progress presentation input is not canonical engineering state and must not be represented as a Capture before canonical creation succeeds. |
| Visibility rules | The entry surface and available context are visible only within scopes in which the Human may create Capture. Inaccessible Projects, Workspaces, Engineering Objects, and related metadata are not disclosed. |
| Authorization behavior | Authorization precedes disclosure of contextual choices and is re-evaluated before canonical creation. Prior navigation or view access provides no creation authority. |
| Cross-view relationships | Successful creation may make the canonical Capture eligible for Inbox. New Capture does not place records directly into Drafts, Under Review, Published, or Superseded. |
| State ownership | Universal Capture owns the created record. Journal owns no draft, partial-Capture, submission, or creation lifecycle state. Temporary input is noncanonical presentation state only. |
| Navigation authority | Journal may navigate to the canonical Capture UUID after successful creation and fresh authorization. Cancellation or completion may safely return the Human to the prior authorized Journal context. |
| Future integration points | Future approved contextual capabilities may supply authorized navigation context, but may not alter Universal Capture creation authority or create an alternative Capture identity. |

### 3.3 Inbox

| Semantic concern | Contract |
|---|---|
| Canonical authority | Universal Capture active lifecycle and current governed context. |
| Entry conditions | A canonical Capture exists with lifecycle `captured`, satisfies the current authorized scope, and is not governed into another mutually exclusive Journal view by a future approved authority. |
| Exit conditions | The Capture is withdrawn or superseded, access is revoked, its governed context no longer matches, or a future approved canonical authority establishes a mutually exclusive later state. |
| Membership rules | Inbox contains only authorized active Captures eligible for Human attention. Journal interaction, ordering, filtering, grouping, opening, or elapsed time cannot create or remove membership. |
| Visibility rules | Only authorized Capture identity, content, provenance, context, version, lifecycle, and permitted related indicators may be shown. Hidden records must not influence disclosed membership or counts. |
| Authorization behavior | Organization, Project, optional Workspace, Engineering Object, Capture, and any displayed related authority are independently checked before disclosure. Protected-not-found applies to inaccessible scope and item access. |
| Cross-view relationships | A newly created canonical Capture may enter Inbox. A canonically superseded Capture exits Inbox and may enter Superseded. Future canonical draft or Review state may cause exit only under an approved exclusivity rule. |
| State ownership | Universal Capture owns all Capture state. Journal owns no inbox assignment, read/unread state, triage state, acceptance state, or durable attention marker. |
| Navigation authority | Journal may open or deep-link to the canonical Capture UUID after current authorization. Navigation never acknowledges, accepts, edits, or transitions the Capture. |
| Future integration points | Engineering Review, Engineering Knowledge Graph, and Organizational Memory may contribute authorized indicators or later-state eligibility through explicit contracts without changing Capture ownership. |

### 3.4 Drafts

| Semantic concern | Contract |
|---|---|
| Canonical authority | No canonical draft authority is approved within PATCH-029. Universal Capture lifecycle `captured` is not draft authority. |
| Entry conditions | None within PATCH-029. Future entry requires a separately approved canonical capability to create an authorized draft state linked to a canonical Capture. |
| Exit conditions | None within PATCH-029. Future exit must be determined by the owning canonical draft authority, authorization loss, or governed context change. |
| Membership rules | The view remains empty or explicitly unavailable until canonical draft authority exists. Journal must not infer draft membership from source kind, age, content, interaction, Capture lifecycle, or presentation preferences. |
| Visibility rules | Unavailability may be stated without implying that draft records exist. Future draft identity, content, state, and counts are disclosed only when both the draft resource and its underlying Capture are authorized. |
| Authorization behavior | Journal has no authority to expose hypothetical draft state. Future access requires authorization through both Universal Capture and the owning draft capability. |
| Cross-view relationships | No current transition to or from Drafts exists. Future relationships with Inbox and Under Review require explicit approved canonical rules and must not be inferred by Journal. |
| State ownership | Future bounded draft capability only. Journal owns no draft record, version, save state, editing lifecycle, or durable work-in-progress state. |
| Navigation authority | Until an authority exists, the view communicates unavailability and provides no draft destination. Future navigation must enter the owning capability when its authority is required and preserve a safe return path. |
| Future integration points | A separately governed Human authoring or draft capability may contribute membership through an explicit application contract while preserving the originating Capture UUID, provenance, context, version, and history. |

### 3.5 Under Review

| Semantic concern | Contract |
|---|---|
| Canonical authority | Future Engineering Review bounded context. Universal Capture and Journal do not own Review state. |
| Entry conditions | None within PATCH-029. Future entry requires an explicit authorized active-Review state established by Engineering Review for material traceable to a canonical Capture. |
| Exit conditions | None within PATCH-029. Future exit occurs only when Engineering Review changes its canonical state, access is revoked, or governed context no longer qualifies. |
| Membership rules | The view remains empty or explicitly unavailable until Engineering Review exists. Opening, selecting, annotating, or positioning an item in Journal cannot initiate Review. |
| Visibility rules | Review existence, reviewer identity, Review state, decision data, related counts, and underlying Capture are disclosed only when authorized by their respective owners. |
| Authorization behavior | Access requires current authorization to the underlying Capture and the canonical Review resource. Authorization to Capture alone does not disclose that a Review exists. |
| Cross-view relationships | Future movement from Inbox or Drafts requires canonical Review entry. Future movement toward Published requires separate canonical Review and publication outcomes. Journal performs none of these transitions. |
| State ownership | Engineering Review exclusively owns submission, assignment, active Review, return, qualification, approval, rejection, and Review history. |
| Navigation authority | Journal may navigate to Engineering Review only after authorization because the governing authority lies outside Journal. The canonical Capture UUID and a safe return path remain traceable. |
| Future integration points | Engineering Knowledge Graph may expose authorized governed context, and Organizational Memory may consume approved outcomes later; neither changes Engineering Review ownership. |

### 3.6 Published

| Semantic concern | Contract |
|---|---|
| Canonical authority | Future approved Review decision and Organizational Memory publication authority. Capture existence or Review activity alone is insufficient. |
| Entry conditions | None within PATCH-029. Future entry requires explicit authorized publication state under its approved scope, limitations, version, and Human authority. |
| Exit conditions | None within PATCH-029. Future exit is governed only by the publication or Organizational Memory authority, authorization loss, supersession of the published resource, or governed scope change. |
| Membership rules | The view remains empty or explicitly unavailable until the required authorities exist. Journal must not infer publication from repeated use, approval-like language, Capture source kind, visibility, Review progress, or user action. |
| Visibility rules | Published representation, status, scope, limitations, approval provenance, and counts are visible only when both the underlying Capture lineage and published resource are authorized. |
| Authorization behavior | Authorization is independently enforced by Universal Capture and the publication or Organizational Memory authority. Public-looking presentation does not override Organization, Project, confidentiality, or reuse boundaries. |
| Cross-view relationships | Future entry may follow an authorized completed Review but is not an automatic consequence of Review completion. Supersession of a Capture does not by itself define the lifecycle of a separately governed published resource. |
| State ownership | Future Organizational Memory or approved publishing capability exclusively owns publication and responsible-reuse state. Journal owns no publish, unpublish, approve, distribute, or memory lifecycle. |
| Navigation authority | Journal may navigate to the canonical published representation when authorized and must preserve traceability to Capture and Review lineage. Publication actions remain in the owning capability. |
| Future integration points | Engineering Review supplies governed Human decisions; Engineering Knowledge Graph may supply authorized relationships; Organizational Memory supplies publication and reuse authority. |

### 3.7 Superseded

| Semantic concern | Contract |
|---|---|
| Canonical authority | Universal Capture lifecycle and canonical supersession chain. |
| Entry conditions | An authorized canonical Capture has lifecycle `superseded`. |
| Exit conditions | Authorization is revoked or the Capture no longer qualifies under its canonical state or governed context. Journal defines no exit command and cannot restore or alter the terminal Capture lifecycle. |
| Membership rules | Membership follows only canonical lifecycle `superseded`. Similar text, newer records, relationship links, user preference, or chronology cannot establish supersession. |
| Visibility rules | The superseded Capture is independently authorized. A replacement or chain member is disclosed only when separately authorized; otherwise its existence and identity remain protected. |
| Authorization behavior | Organization, Project, optional Workspace, Engineering Object, original Capture, replacement, and every requested chain member are evaluated before disclosure. Protected-not-found applies at each boundary. |
| Cross-view relationships | A canonically superseded Capture exits Inbox and enters Superseded when authorized. Its active replacement may independently qualify for Inbox. The two records retain distinct canonical UUIDs and histories. |
| State ownership | Universal Capture exclusively owns supersession lifecycle, replacement reference, version advancement, and history. Journal owns no replace, restore, chain-edit, or supersession state. |
| Navigation authority | Journal may open the superseded Capture and authorized portions of its canonical chain. Deep links preserve canonical UUIDs and reauthorize every destination. |
| Future integration points | Engineering Review, Engineering Knowledge Graph, or Organizational Memory may later represent their own governed response to Capture supersession, but Journal cannot infer or synchronize those states as authority. |

### 3.8 Cross-View Invariants

1. Every visible item resolves to a canonical resource and retains its canonical
   identity.
2. Journal creates no view-owned copy, alias identity, lifecycle, queue state,
   or durable membership record.
3. Membership is evaluated from current canonical state only after current
   authorization.
4. A presentation action never changes canonical eligibility.
5. Counts are derived only from authorized members of the requested view.
6. Temporary sorting, filtering, grouping, layout, and navigation history do
   not change membership.
7. Deep links reauthorize and resolve canonical identity; they do not preserve
   former visibility as authority.
8. Canonical content, provenance, context, version, lifecycle, and history keep
   the same meaning across every view.
9. A view whose canonical authority does not exist remains empty or explicitly
   unavailable and cannot borrow authority from another view.
10. Journal never exposes a hidden resource indirectly through membership,
    counts, badges, relationships, transition indicators, or navigation.
11. Withdrawal does not create an unapproved Journal view or alternate
    membership.
12. Review, publication, Organizational Memory, Knowledge Graph, and AI meaning
    cannot be inferred from Journal placement.

Except where explicitly authorized by canonical authority, a Capture shall have
one primary Engineering Journal work view at any point in time. Temporary
overlap is permitted only during canonical state transitions that are
explicitly defined by the owning canonical authority. Engineering Journal shall
never create or infer overlapping membership independently.

### 3.9 Canonical-State Precedence

When presentation state and canonical state differ, canonical state always
prevails. Journal must discard or revise the presentation according to the
latest authorized canonical state.

Precedence is evaluated in this order:

1. current actor, active Organization, and resource authorization;
2. existence and accessibility of the canonical resource;
3. canonical Capture lifecycle, version, and governed context;
4. any separately approved canonical authority required by the view;
5. deterministic view-membership rules;
6. temporary presentation preferences.

No lower-precedence concern may override a higher one. In particular,
presentation preferences, cached projection, prior visibility, navigation
origin, or user expectation cannot override authorization or canonical state.

If multiple canonical authorities are eventually required and their states are
incomplete, conflicting, or inaccessible, Journal must not invent a resolved
state. The item is omitted, protected, or the capability is represented as
unavailable according to the applicable authorized contract.

### 3.10 Conflicting Membership Prevention

The default Journal rule is that Inbox, Drafts, Under Review, Published, and
Superseded are mutually exclusive primary work views for a given canonical
Capture lineage at a given authorized evaluation point. New Capture has no item
membership and therefore does not conflict with them.

Conflicts are prevented as follows:

1. `superseded` canonical Capture lifecycle has precedence for that Capture and
   excludes it from Inbox;
2. withdrawn Capture is excluded from all currently approved member-bearing
   views unless a future approved rule explicitly provides otherwise;
3. active `captured` state may qualify for Inbox only when no approved later
   canonical state requires exclusive placement;
4. Drafts, Under Review, and Published cannot receive members until their
   canonical authorities and precedence rules are separately approved;
5. a future capability must declare whether its contributed state replaces or
   supplements existing eligibility before Journal may present it;
6. Journal must not resolve conflicts using timestamps, visual priority,
   noncanonical presentation state, last navigation, or duplicated membership records;
7. where an approved future experience intentionally permits secondary
   visibility, one view must remain the declared primary work view and every
   secondary appearance must retain identical canonical identity and authority
   labeling.

No future extension may silently change these precedence or exclusivity rules.

### 3.11 Future Extensibility Without Canonical Ownership Change

A future bounded capability may contribute a new approved view or extend an
existing view only through a separately governed architecture decision and an
explicit application-owned contract.

Every extension must define:

- its canonical authority and state owner;
- exact entry, exit, membership, and conflict-precedence rules;
- required joint authorization with Universal Capture;
- protected item and count behavior;
- canonical identity and lineage preservation;
- navigation into and safely back from the owning capability;
- behavior when its authority is absent, unavailable, stale, or inaccessible.

An extension must not:

- transfer Capture ownership away from Universal Capture;
- give Journal persistence or lifecycle ownership;
- use a view as the canonical record of engineering state;
- introduce shared-table or client-owned canonical state;
- reinterpret an existing view without explicit governance;
- make Review, publication, Organizational Memory, Knowledge Graph, or AI state
  a Journal-owned concern;
- create alternative identities or duplicate canonical resources.

Future Journal work views shall extend, but never reinterpret, the semantics of
existing approved views. Existing view meaning, authority, and membership rules
remain backward compatible. Additional views may be introduced only through
newly approved canonical authorities and explicit application contracts.

### 3.12 Section Decision

```text
View semantics: PROPOSED
Approved views: SIX / NO ADDITIONS
Universal Capture authority: PRESERVED
Journal persistence ownership: NONE
Journal lifecycle ownership: NONE
Review authority: NOT INTRODUCED
Organizational Memory authority: NOT INTRODUCED
AI behavior: NONE
API/database/implementation design: NOT INCLUDED
Architecture Acceptance: PASS
```
## 4. Engineering Journal Composition Model

### 4.1 Composition Objective

Engineering Journal composes authorized information from canonical capabilities
into one coherent Human Engineering Workspace. Composition changes how
information is presented together; it does not change who owns the information,
where canonical state lives, or which capability has authority to interpret or
transition that state.

Universal Capture remains the sole source of truth for Capture identity,
content, provenance, context, version, lifecycle, withdrawal, supersession, and
history. Journal owns no persistence, Aggregate, lifecycle, or canonical
engineering state.

### 4.2 Workspace Composition Model

The workspace is an authorized presentation composition with three conceptual
parts:

```text
Authenticated Human and active governed scope
                    ↓
Approved application contracts to canonical capabilities
                    ↓
Engineering Journal presentation composition
```

The authenticated Human and active Organization establish the outer disclosure
boundary. Project, optional Workspace, discipline, Engineering Object, Capture,
and future capability boundaries further constrain what may participate in the
composition.

Journal may arrange authorized information into the six approved work views,
item representations, contextual indicators, counts, and navigation choices.
These arrangements are presentation constructs. They do not become durable
engineering records, canonical classifications, or authority-bearing state.

### 4.3 Canonical Information Composition

Composition begins with canonical information and retains its ownership:

| Information | Canonical owner | Journal composition authority |
|---|---|---|
| Capture identity, original content, source, Creator, context, version, lifecycle, and history | Universal Capture | Present an authorized representation without changing meaning |
| Project and Workspace context | Their existing canonical platform capabilities | Present only authorized context attached to the Capture |
| Discipline | Canonical governed Workspace/Capture context | Present the derived canonical value; do not reclassify |
| Engineering Object context | Engineering Object capability | Present an authorized reference; do not copy or mutate the object |
| Supersession and replacement lineage | Universal Capture | Present only authorized chain members and protected gaps |
| Review state and decisions | Future Engineering Review | No current composition; future authorized presentation only |
| Governed graph relationships | Future or approved Engineering Knowledge Graph authority | No new graph authority; future authorized presentation only |
| Published Organizational Memory | Future Organizational Memory | No current composition; future authorized presentation only |

Journal must preserve the difference between source information, contextual
reference, derived presentation, and canonical authority. Co-location within a
workspace does not merge those meanings.

### 4.4 Read-Model Composition

An Engineering Journal read model is a noncanonical, presentation-oriented
projection assembled from authorized canonical information. It exists to make
Human work understandable and navigable; it is not an Aggregate, System of
Record, materialized authority, or independent lifecycle.

The read model may contain only information required to present:

- the active governed workspace context;
- one of the six approved view meanings;
- authorized view membership and protected counts;
- canonical Capture identity and permitted Capture attributes;
- authorized contextual references and authority labels;
- canonical freshness and version indicators;
- safe navigation to a canonical resource or owning capability;
- explicit unavailable states for capabilities that do not yet exist.

Read-model composition must not:

- create a Journal identifier for a canonical resource;
- persist or duplicate canonical Capture state;
- become the source of view membership;
- resolve canonical conflicts through presentation logic;
- infer Review, publication, memory, graph, or AI meaning;
- preserve previously authorized information after access is revoked;
- represent temporary preferences as engineering state.

The lifecycle, transport, caching, storage, update, and delivery mechanisms of a
read model are implementation concerns and are not defined or authorized here.

### 4.5 Canonical Dependency Boundaries

Composition occurs only through approved application contracts owned at the
appropriate application boundary. Journal depends inward on those contracts;
canonical capabilities do not depend on Journal.

```text
Engineering Journal presentation
              ↓
Approved application composition contracts
              ↓
Canonical capability application boundaries
              ↓
Canonical domain ownership
```

The following are prohibited:

- bidirectional bounded-context dependencies;
- a canonical capability importing Journal view or presentation semantics;
- Journal reaching around an application contract to obtain canonical state;
- shared-table ownership or direct cross-capability persistence coupling;
- Journal coordinating canonical writes or lifecycle transitions;
- one capability treating a Journal projection as authoritative input;
- transferring authority merely because information is displayed together.

Future capabilities must expose only the information and authority semantics
approved for Journal composition. Journal must remain able to omit an
unavailable capability without changing Universal Capture ownership.

### 4.6 Information Ownership

Every composed information element retains one identifiable canonical owner.
Journal may know the source and authority label needed for safe presentation,
but it does not acquire ownership by reading, arranging, filtering, grouping,
counting, or linking that information.

Ownership rules are:

1. Universal Capture exclusively owns all Capture state.
2. Existing platform capabilities retain ownership of Organization, Project,
   Workspace, identity, discipline, and Engineering Object context.
3. Engineering Review will exclusively own Review state and Human decisions.
4. Engineering Knowledge Graph will own governed graph relationship semantics.
5. Organizational Memory will own approved publication and responsible-reuse
   state.
6. No information has two canonical owners.
7. When ownership is ambiguous, Journal must not compose the information as
   authoritative.
8. Journal must not create a fallback copy when a canonical owner is
   unavailable.

### 4.7 Presentation Ownership

Journal owns the presentation semantics of the Human workspace, limited to:

- the arrangement and labeling of the six approved views;
- workspace continuity and safe return navigation;
- ordering and grouping of authorized representations;
- temporary noncanonical presentation sorting, filtering, grouping, and layout preferences;
- distinction among authorized empty, filtered empty, capability unavailable,
  and protected-not-found states;
- clear attribution of canonical authority;
- presentation of freshness without claiming canonical ownership.

Presentation ownership does not include ownership of the represented content,
membership cause, canonical order, engineering classification, lifecycle,
Review standing, publication standing, graph meaning, or memory standing.

Journal labels and visual grouping must not alter canonical terminology or
suggest a higher authority than the source provides.

### 4.8 State Ownership

Journal owns no canonical or durable engineering state. State relevant to
composition falls into two categories:

| State category | Owner and rule |
|---|---|
| Canonical engineering state | Owned exclusively by the applicable canonical capability and accessed only through an approved application contract |
| Temporary presentation state | May exist for the current Human workspace experience but creates no canonical identity, authority, lifecycle, entitlement, or durable engineering meaning |

Temporary presentation state may influence what the Human currently sees. It
must never influence:

- authorization;
- canonical Capture identity or membership eligibility;
- Capture lifecycle, version, provenance, context, or history;
- Review or publication state;
- Organizational Memory;
- Engineering Knowledge Graph semantics;
- future canonical capability decisions.

Previously composed state never proves current access or current canonical
truth. Reauthorization and canonical-state precedence always apply.

### 4.9 Cross-Capability Composition

Cross-capability composition presents related authorized information without
merging bounded contexts.

For each participating capability, Journal must:

1. identify the canonical owner;
2. use an approved application contract;
3. authorize the Human and governed scope before disclosure;
4. preserve canonical identity and authority labeling;
5. include only information necessary for the approved Journal purpose;
6. tolerate absence or inaccessibility without inventing substitute state;
7. navigate to the owning capability when an authoritative action belongs
   there;
8. preserve a safe return path to Journal when authorized;
9. avoid turning contextual association into a governed relationship.

Current composition authority is limited to Universal Capture and already
approved contextual platform capabilities. Future Engineering Review,
Engineering Knowledge Graph, and Organizational Memory information remains
unavailable until its capability, authority semantics, and Journal application
contract are separately approved.

Journal introduces no AI composition, AI enrichment, AI classification, AI
recommendation, or provider dependency.

If a canonical capability is temporarily unavailable, Engineering Journal shall
degrade gracefully by presenting only the remaining authorized canonical
information. Journal shall never fabricate, infer, or preserve unavailable
canonical authority. Missing canonical projections shall be explicitly
identified as unavailable.

### 4.10 Projection Rules

Every Journal projection must satisfy all of the following:

1. **Authorized source:** each information element comes from an authorized
   canonical capability through an approved application contract.
2. **Canonical identity:** canonical UUIDs and identifiers remain unchanged;
   Journal creates no alias identity.
3. **Minimal disclosure:** only information necessary for the approved view and
   current Human purpose is included.
4. **Context preservation:** Organization, Project, optional Workspace,
   discipline, Engineering Object, and provenance meanings are not detached or
   widened.
5. **Current authority:** authorization and canonical state are evaluated before
   membership, item, count, or navigation disclosure.
6. **Deterministic membership:** view placement follows the approved semantic
   rules and canonical-state precedence.
7. **Protected composition:** inaccessible records and related resources leave
   no revealing identifiers, counts, badges, gaps, or diagnostics.
8. **Freshness honesty:** presentation must not portray stale composition as
   canonical authority.
9. **No semantic enrichment:** Journal does not infer truth, Evidence standing,
   Review status, publication status, graph meaning, or knowledge authority.
10. **No write-back implication:** projection or interaction does not imply a
    canonical state transition.
11. **Traceable navigation:** a visible canonical resource can be navigated by
    stable identity only after destination reauthorization.
12. **Unavailable-authority safety:** missing future capability information is
    shown as unavailable or omitted, never fabricated.

### 4.11 Composition Invariants

1. Universal Capture remains the sole source of truth for Capture.
2. Journal owns no persistence, Aggregate, lifecycle, or canonical state.
3. Journal composition is presentation-only and Human-oriented.
4. Composition occurs only through approved application contracts.
5. Canonical capability dependency on Journal is prohibited.
6. Bidirectional bounded-context dependency is prohibited.
7. Shared-table ownership and direct persistence coupling are prohibited.
8. Canonical state is never copied to create an alternative source of truth.
9. Every composed element retains one canonical owner.
10. Authorization precedes composition, membership, counting, and navigation.
11. Canonical-state precedence overrides temporary presentation state.
12. Cross-capability display does not create cross-capability authority.
13. Journal owns no Review, publication, Organizational Memory, or Engineering
    Knowledge Graph authority.
14. Journal contains no AI behavior or provider dependency.
15. Composition does not authorize implementation, API, database, persistence,
    migration, commit, push, or deployment decisions.

Given the same authenticated actor, authorization scope, canonical state, and
approved application contracts, Engineering Journal composition shall always
produce the same workspace representation. Journal composition must be
deterministic and shall not introduce presentation-owned business decisions.

### 4.12 Future Composition Extensibility

A future canonical capability may participate in Journal composition only after
separate governance approval defines:

- its canonical owner and bounded-context boundary;
- the precise information eligible for presentation;
- its application composition contract;
- joint authorization and protected-disclosure rules;
- identity, provenance, context, version, and history preservation;
- freshness and unavailable-authority semantics;
- view eligibility and conflict precedence, when applicable;
- navigation to and from the owning capability.

Future composition may add authorized information or approved views, but must
not reinterpret existing view meaning, transfer canonical ownership, introduce
shared persistence, or make Journal a required dependency of the canonical
capability.

An extension must remain removable from Journal presentation without damaging,
deleting, or changing canonical state. Failure or absence of an optional future
composition source must not corrupt Universal Capture meaning or create a
Journal-owned substitute.

### 4.13 Section Decision

```text
Composition model: PROPOSED
Composition role: PRESENTATION ONLY
Universal Capture authority: PRESERVED
Approved application contracts: REQUIRED
Journal persistence ownership: NONE
Journal Aggregate ownership: NONE
Journal lifecycle ownership: NONE
Review authority: NOT INTRODUCED
Organizational Memory authority: NOT INTRODUCED
Engineering Knowledge Graph authority: NOT INTRODUCED
AI behavior: NONE
Shared-table ownership: PROHIBITED
Bidirectional bounded-context dependency: PROHIBITED
API/database/implementation design: NOT INCLUDED
Architecture Acceptance: PASS
```
## 5. Authorization and Protected Disclosure Model

### 5.1 Authorization Model

Engineering Journal is an authorization-constrained presentation boundary. It
does not grant access by displaying a workspace, remembering prior visibility,
accepting a navigation target, or composing information from multiple
capabilities.

Authorization is evaluated from the authenticated active Human and trusted
active Organization membership. Every additional governed boundary is then
evaluated by its canonical owner, including Project, optional Workspace,
discipline, Engineering Object, Capture, supersession-chain member, and any
future Review, Knowledge Graph, or Organizational Memory resource.

Authorization follows these rules:

1. authorization precedes existence disclosure;
2. authorization is evaluated before view membership and count calculation;
3. authorization to a container does not imply authorization to every item;
4. authorization to one item does not imply authorization to a related item;
5. authorization to Capture does not imply authority for Review, graph, or
   Organizational Memory information;
6. prior authorization does not establish present authorization;
7. Journal presentation and temporary noncanonical presentation state provide no entitlement;
8. client-supplied Organization identity is never trusted as authority.

### 5.2 Protected Disclosure

Protected disclosure applies uniformly to views, items, metadata, counts,
relationships, authority labels, navigation destinations, and unavailable
canonical projections.

When a requested resource is absent or unauthorized, Journal must use
protected-not-found semantics and must not distinguish between those causes.
Journal must not disclose:

- whether the protected resource exists;
- its canonical identifier, title, content, provenance, context, or lifecycle;
- whether it belongs to a Journal view;
- whether it contributes to a count;
- whether it has a replacement, predecessor, Review, relationship, or published
  representation;
- the identity or role of another actor associated with it;
- the specific authorization rule that rejected access;
- diagnostic detail from which protected engineering information can be
  inferred.

Graceful partial composition does not weaken protected disclosure. A missing
projection may be identified as unavailable only when that statement does not
reveal the existence or state of a protected resource.

### 5.3 Visibility Rules

Journal visibility is the intersection of:

```text
Authenticated active Human
∩ active Organization membership
∩ governed Project scope
∩ optional Workspace/Object scope
∩ canonical resource authorization
∩ approved view-membership rule
∩ any additional canonical capability authorization
```

Only the resulting authorized projection may be presented. Temporary filtering,
sorting, grouping, layout, prior navigation, deep links, and workspace continuity
cannot widen this intersection.

Visibility must be independently evaluated for:

- each view;
- each member-bearing item;
- each displayed attribute;
- each related-resource indicator;
- each predecessor, replacement, or chain member;
- each future capability projection;
- each navigation destination.

Authorized context may be minimized for presentation, but it must never be
detached or widened in a way that changes engineering meaning.

### 5.4 Count Protection

Journal counts are protected projections, not public metadata or canonical
state. A count is produced only after the requested scope, view, and candidate
members have been authorized.

Count rules are:

1. only authorized qualifying items contribute;
2. global or pre-authorization totals are prohibited;
3. hidden items must not influence totals, subtotals, badges, ranges, page
   information, or filtered-result indicators;
4. inaccessible scopes use protected-not-found semantics rather than a
   revealing zero;
5. an authorized empty view may disclose zero only after scope authorization;
6. an unavailable future capability must not expose a synthetic zero that
   implies authority or completeness;
7. filtered counts must remain based on the already authorized member set;
8. concurrent authorization or canonical-state changes require counts to
   reflect the latest authorized composition;
9. approximate, inferred, cached-as-authority, or cross-scope counts are
   prohibited.

### 5.5 Navigation Authorization

Every navigation boundary is a new disclosure decision. A stable deep link,
workspace return path, or previously opened item never carries authorization
forward as proof.

Navigation must:

- preserve canonical identity without creating a Journal alias;
- reauthorize the current Human and active Organization;
- reauthorize Project, optional Workspace, Engineering Object, Capture, and
  destination capability boundaries;
- protect inaccessible destinations with protected-not-found behavior;
- disclose only the authorized portion of a supersession chain or related
  context;
- enter another bounded capability when canonical authority belongs there;
- preserve a safe return path without retaining protected resource content;
- avoid leaking protected identifiers through navigation labels, history,
  breadcrumbs, or inferred destination availability.

Navigation into Engineering Review, Engineering Knowledge Graph, or
Organizational Memory remains unavailable until the respective capability and
its application contract are approved.

### 5.6 Workspace Security Invariants

1. Authorization always precedes disclosure.
2. Active Organization scope is trusted only from authenticated membership.
3. No global Capture lookup or cross-Organization composition is permitted.
4. Every canonical capability enforces its own resource authority.
5. Journal view access grants no canonical command authority.
6. Items, attributes, counts, memberships, relationships, and destinations are
   protected equally.
7. Protected-not-found behavior prevents absence-versus-denial disclosure.
8. Refresh and deep-link access reauthorize against current state.
9. Revocation overrides prior visibility and temporary presentation state.
10. Partial composition never fabricates or preserves unavailable authority.
11. Presentation preferences cannot change authorization or retain protected
    engineering information as canonical state.
12. Journal emits no Review, publication, memory, graph, or AI authority.
13. Security semantics do not depend on a particular API, database, transport,
    persistence mechanism, or implementation technology.

### 5.7 Section Decision

```text
Authorization model: DEFINED
Authorization before disclosure: REQUIRED
Protected-not-found: REQUIRED
Count protection: REQUIRED
Navigation reauthorization: REQUIRED
Client-trusted Organization authority: PROHIBITED
Journal security authority expansion: NONE
API/database/implementation design: NOT INCLUDED
```

## 6. Integration Architecture

### 6.1 Integration Model

Engineering Journal integrates as a presentation consumer of canonical
capabilities. Integration occurs only through separately approved application
contracts and preserves inward dependency toward canonical application and
domain ownership.

```text
Engineering Journal
        ↓
Journal-owned composition expectations
        ↓
Approved application contracts
        ↓
Canonical capability boundaries
```

This model expresses architectural dependency and responsibility, not an API,
transport, deployment, process, or persistence topology.

Universal Capture is the current canonical integration and remains the sole
source of truth for Capture. Future capability integration is inactive until
its architecture and application contract are approved.

### 6.2 Engineering Review Integration

Future Engineering Review will exclusively own:

- Review submission and eligibility;
- reviewer and authority assignment;
- active Review state;
- return, qualification, approval, and rejection decisions;
- Human rationale and Review history.

Journal may eventually compose only the authorized information needed to:

- determine whether an item qualifies for Under Review presentation;
- display an authorized Review state and authority attribution;
- navigate the Human into Engineering Review;
- retain traceability to the originating canonical Capture;
- return safely to the relevant Journal context.

Journal must not submit, assign, approve, reject, return, qualify, or transition
a Review. Under Review remains unavailable until Engineering Review supplies an
approved canonical authority and application contract.

### 6.3 Engineering Knowledge Graph Integration

Future or separately approved Engineering Knowledge Graph capability owns
governed relationship semantics and authorized traversal. Journal may
eventually present minimal authorized contextual connections that help a Human
understand the current Capture.

Journal must not:

- create or mutate Engineering Relationships;
- infer a governed relationship from co-presentation or navigation;
- treat visual adjacency as graph meaning;
- widen graph traversal beyond authorized context;
- use graph information to manufacture Journal membership or engineering
  authority unless an explicit future rule is approved;
- become a graph source of truth.

Graph absence or unavailability must degrade gracefully without changing
Capture meaning or preventing authorized Capture presentation.

### 6.4 Organizational Memory Integration

Future Organizational Memory will exclusively own governed publication,
responsible reuse, approved scope, limitations, memory version, and memory
lifecycle.

Journal may eventually compose authorized published representations and their
traceable lineage for the Published view. Journal may navigate to the owning
capability but cannot publish, unpublish, distribute, approve, qualify, or
promote Capture into Organizational Memory.

Published remains unavailable until Human Review and Organizational Memory
authorities establish the required canonical state and application contracts.
Capture existence, repeated use, Journal visibility, or Review activity never
implies publication.

### 6.5 Future Capability Integration Contracts

Every future capability must receive separate governance approval before it can
participate in Journal composition. Its architectural contract must define:

1. the canonical capability and state owner;
2. the exact information eligible for Journal presentation;
3. the Human and scope authorization boundaries;
4. protected-disclosure and count rules;
5. canonical identity and lineage correlation;
6. view-entry, exit, precedence, and exclusivity semantics where applicable;
7. canonical freshness and unavailable-capability behavior;
8. navigation into and safely back from the owning capability;
9. failure isolation and graceful partial composition;
10. backward compatibility with existing approved view semantics;
11. explicit confirmation that Journal gains no persistence or lifecycle
    ownership.

An integration contract conveys information for presentation. It does not
transfer canonical authority or authorize Journal to perform the owning
capability's commands.

### 6.6 Dependency Rules

1. Journal may depend only on approved application contracts.
2. Canonical domains and Aggregates must not depend on Journal.
3. Bidirectional bounded-context dependency is prohibited.
4. Direct persistence access across capability boundaries is prohibited.
5. Shared-table ownership and shared canonical state are prohibited.
6. Journal view semantics must not enter canonical domain models.
7. A future capability must remain operationally and semantically canonical
   without Journal.
8. Removal of an optional composition source must not alter Capture state.
9. Failure of one optional capability must not manufacture state in another.
10. Cross-capability identity correlation preserves canonical identifiers and
    creates no Journal identity.
11. Journal cannot coordinate multi-capability canonical lifecycle transitions.
12. AI and provider contracts are outside PATCH-029 and cannot become an
    integration dependency.

### 6.7 Section Decision

```text
Integration style: PRESENTATION CONSUMER
Universal Capture integration: CANONICAL / REQUIRED
Engineering Review integration: FUTURE / NOT AUTHORIZED
Engineering Knowledge Graph integration: FUTURE / NOT AUTHORIZED
Organizational Memory integration: FUTURE / NOT AUTHORIZED
Approved application contracts: REQUIRED
Bidirectional dependency: PROHIBITED
Shared persistence: PROHIBITED
API/database/implementation design: NOT INCLUDED
```

## 7. Governing Architecture and Evolution

### 7.1 Architectural Invariants

1. Engineering Journal is the default Human Engineering Workspace.
2. Universal Capture remains the sole canonical source for Capture.
3. Journal owns presentation composition only.
4. Journal owns no persistence, Aggregate, lifecycle, or canonical state.
5. Canonical Capture UUID, provenance, context, version, and history are
   preserved.
6. View membership is deterministic from current authorized canonical state.
7. One primary work view applies unless a canonical authority explicitly
   defines temporary overlap.
8. Journal never creates or infers overlapping membership independently.
9. Authorization precedes items, attributes, membership, counts, and navigation.
10. Canonical-state precedence overrides presentation state.
11. Composition occurs only through approved application contracts.
12. Canonical capabilities never depend on Journal.
13. Shared-table ownership, bidirectional dependency, and canonical-state
    duplication are prohibited.
14. Journal owns no Review, publication, Organizational Memory, or Engineering
    Knowledge Graph authority.
15. Journal contains no AI behavior or provider dependency.
16. Intelligence Before Automation remains a permanent evolution constraint.

### 7.2 Manifesto Compliance

| Manifesto principle | EDS-029 compliance |
|---|---|
| Engineering First | Journal is shaped around daily Human Engineering Work and continuity rather than administrative reporting. |
| Capture Once | All Journal representations retain canonical Universal Capture identity and original meaning without duplication. |
| Human Authority | Journal creates no Review, approval, publication, or autonomous authority. |
| Engineering Context Is Sacred | Organization, Project, optional Workspace, discipline, Engineering Object, provenance, version, and history remain governed and attached. |
| Evidence Before Assumption | View placement and composition never promote experience into fact, Evidence, or approved knowledge. |
| Context Before Recommendation | Journal introduces no recommendation behavior and never detaches information from governed context. |
| Intelligence Before Automation | Human workflow is designed before automation; AI is excluded. |
| Explainability | Canonical authority, provenance, state, limitations, and unavailability remain distinguishable and traceable. |
| Provider Independence | Journal contains no model, provider, or technology dependency. |
| Organizational Ownership | Trusted active Organization scope and protected disclosure govern all workspace information. |
| Continuous Evolution | Canonical version, history, correction, and supersession remain intact while view semantics evolve through governance. |

```text
QG-M1 Manifesto Alignment: PASS
```

### 7.3 Evolution Strategy

Journal evolves through additive, Docs-First capability integration:

1. preserve approved view and authority semantics;
2. register the future capability and canonical owner;
3. complete Architecture Review and Manifesto review;
4. define the canonical capability before Journal presentation integration;
5. define explicit authorization, precedence, and failure semantics;
6. extend Journal through an approved application contract;
7. verify backward compatibility and protected disclosure;
8. keep the extension removable without changing canonical state.

Evolution must increase Human understanding without transferring authority to
presentation or automation.

### 7.4 Backward Compatibility

Existing approved view meaning, canonical authority, membership rules,
authorization behavior, protected counts, and navigation semantics form the
compatibility baseline.

Future evolution must not:

- reinterpret an existing view by implication;
- change a Capture UUID or create a Journal alias;
- reclassify existing Captures using presentation state;
- turn unavailable views into inferred states;
- weaken protected-not-found or authorization-before-disclosure;
- make a new optional capability required for authorized Universal Capture
  presentation;
- remove canonical provenance, context, version, or history;
- convert temporary presentation preferences into durable engineering state.

Any intentional semantic change requires a new approved governance decision and
must explicitly address compatibility and migration of meaning. This EDS does
not design or authorize a data migration.

### 7.5 Future Extensibility

Future capabilities may add approved information or work views when they:

- own their canonical state outside Journal;
- integrate through an explicit approved application contract;
- preserve dependency direction and failure isolation;
- define deterministic membership and canonical precedence;
- preserve protected disclosure and organizational scope;
- remain compatible with Universal Capture identity and lineage;
- extend rather than reinterpret existing semantics;
- introduce no shared-table ownership or Journal lifecycle;
- remain independent of AI unless a later separately governed capability
  explicitly authorizes advisory integration.

No future extensibility clause in EDS-029 pre-authorizes Engineering Review,
Engineering Knowledge Graph, Organizational Memory, AI Capture Assistant, an
additional view, an implementation, or a future PATCH.

### 7.6 Prohibited Architectural Patterns

- Journal-owned Capture copies or alternative Capture identities;
- Journal Aggregate, canonical lifecycle, or durable engineering state;
- shared-table ownership or direct cross-capability persistence access;
- bidirectional or cyclic bounded-context dependencies;
- canonical capabilities importing Journal view semantics;
- presentation actions functioning as canonical commands;
- client-owned Organization authority or client-owned canonical state;
- global Capture lookup before trusted scope resolution;
- counts calculated before authorization filtering;
- revealing absence-versus-denial behavior;
- inferred Review, approval, publication, memory, graph, truth, or Evidence
  standing;
- stale, cached, or previously visible presentation treated as authority;
- silent conflict resolution between canonical capabilities;
- unavailable capability state fabricated from another source;
- new views introduced without a canonical owner and governance approval;
- AI classification, recommendation, authoring, decision, or provider coupling;
- API, database, migration, transport, or framework choice embedded as
  architectural meaning.

### 7.7 Section Decision

```text
Architectural invariants: DEFINED
Manifesto compliance: PASS
Evolution model: DOCS-FIRST / ADDITIVE
Backward compatibility: REQUIRED
Canonical ownership change: PROHIBITED
Prohibited patterns: DEFINED
Implementation authority: NOT GRANTED
```

## 8. Architecture Summary and Readiness

### 8.1 Architecture Summary

Engineering Journal is the default Human Engineering Workspace over Universal
Capture. It organizes authorized canonical Engineering Experience into six
approved work views without becoming a source of truth, Aggregate, lifecycle,
Review authority, publication authority, Organizational Memory, Knowledge
Graph, or AI capability.

The architecture establishes:

- presentation-only bounded-context responsibility;
- exact semantics for New Capture, Inbox, Drafts, Under Review, Published, and
  Superseded;
- deterministic canonical-state precedence and primary-view exclusivity;
- noncanonical read-model composition through approved application contracts;
- authorization-before-disclosure for views, items, counts, and navigation;
- protected-not-found behavior and graceful partial composition;
- one-way dependency toward canonical capabilities;
- additive future integration without canonical ownership transfer;
- full alignment with the Engineering Intelligence Manifesto v1.0.

### 8.2 Decision Record

| Decision | Result |
|---|---|
| Journal role | Default Human Engineering Workspace and presentation-only bounded context |
| Capture authority | Universal Capture remains the sole source of truth for Capture |
| Journal persistence | None |
| Journal Aggregate | None |
| Journal lifecycle | None |
| Approved views | New Capture, Inbox, Drafts, Under Review, Published, Superseded |
| Currently authoritative member-bearing views | Inbox and Superseded through Universal Capture |
| Future-authority views | Drafts, Under Review, and Published remain empty or explicitly unavailable |
| Review authority | Outside Journal; future Engineering Review only |
| Knowledge Graph authority | Outside Journal |
| Organizational Memory authority | Outside Journal |
| AI behavior | Excluded |
| Composition boundary | Approved application contracts only |
| Dependency direction | Journal toward canonical application boundaries; never bidirectional |
| Security model | Authorization before disclosure and protected-not-found |
| Evolution model | Docs-First, additive, governed, backward-compatible |

### 8.3 Risks

| Risk | Architectural control |
|---|---|
| Journal becomes a second source of truth | Prohibit persistence, Aggregate ownership, canonical copies, and view-owned lifecycle |
| View labels imply unavailable authority | Keep Drafts, Under Review, and Published empty or explicitly unavailable until canonical owners exist |
| Unauthorized existence leaks through counts or navigation | Apply authorization before membership/counting and protected-not-found at every destination |
| Stale presentation is treated as current authority | Canonical-state precedence, reauthorization, refresh freshness, and deterministic recomposition |
| Cross-capability composition creates tight coupling | One-way approved application contracts, graceful partial composition, and no shared tables |
| Future capability reinterprets existing views | Require additive governance, compatibility, explicit precedence, and canonical ownership |
| Workspace convenience weakens context | Preserve Organization, Project, Workspace, discipline, Engineering Object, provenance, and history |
| Automation displaces Human judgment | Preserve Intelligence Before Automation and exclude AI from PATCH-029 |

### 8.4 Assumptions

- PATCH-028 Universal Capture remains the approved canonical Capture baseline.
- Authenticated active Organization context and existing governed Project,
  Workspace, discipline, and Engineering Object boundaries remain authoritative.
- Canonical Capture UUID, provenance, lifecycle, version, withdrawal, and
  supersession contracts remain stable for PATCH-029 design.
- Future Review, Knowledge Graph, Organizational Memory, and draft authorities
  do not yet exist within PATCH-029.
- An unavailable future capability is not equivalent to an authorized empty
  result.
- Application contracts can preserve bounded-context direction without
  transferring ownership; their implementation form is intentionally undefined.
- Sections 1 through 4 remain the approved foundation for this completion.

If an assumption changes, the affected architecture returns to Docs-First
review before IDS or implementation authorization.

### 8.5 Future Work

After independent EDS review and Human acceptance, the next governance work may
define IDS-029 and an implementation plan, but only through separate explicit
authorization.

Future product capabilities remain separately governed:

- Engineering Review;
- Engineering Knowledge Graph;
- Organizational Memory;
- AI Capture Assistant;
- any canonical draft or authoring capability;
- any additional Journal view.

This list records integration direction only. It does not authorize their
design, scope, implementation, API, persistence, migration, or delivery.

### 8.6 Readiness Statement

Sections 1 through 8 form a complete Engineering Journal architecture within
PATCH-029 scope. The design defines bounded-context responsibility, view
semantics, composition, authorization, integration, evolution, risks, and
governing invariants without entering implementation design.

No unresolved architecture finding currently prevents Independent EDS Review.
Implementation remains unauthorized until the remaining SATCO governance chain
is completed.

## Final EDS Decision

```text
EDS-029 completion status: COMPLETE — INDEPENDENT EDS REVIEW PASS
Completed design scope: SECTIONS 1–8
Architecture Review: PASS
Human Architecture Acceptance: PASS
Universal Capture authority: PRESERVED
Engineering Journal role: PRESENTATION-ONLY HUMAN WORKSPACE
Persistence/Aggregate/lifecycle ownership: NONE
Review authority: NOT INTRODUCED
Organizational Memory authority: NOT INTRODUCED
Engineering Knowledge Graph authority: NOT INTRODUCED
AI behavior: NONE
Manifesto compliance: PASS
Independent EDS Review: PASS
Human EDS Acceptance: PASS
Remaining Findings: NONE
EDS Readiness: ACCEPTED / COMPLETE
Permission to proceed to IDS-029: GRANTED
IDS-029 design authority: GRANTED
Implementation/API/database/migration authority: NOT GRANTED
```
