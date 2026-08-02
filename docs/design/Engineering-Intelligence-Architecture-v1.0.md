# SATCO Engineering Intelligence Architecture

## 1. Document Control

| Field | Value |
|---|---|
| Document | Engineering Intelligence Architecture |
| Version | 0.1 |
| Status | PROPOSED — NOT IMPLEMENTATION AUTHORITY |
| Architecture style | Docs-First Architecture |
| Owner | SATCO Product Owner / Architecture Guardian |
| Date | 2026-08-02 |
| Review | `docs/reviews/Engineering-Intelligence-Architecture-Review.md` |

This document proposes a durable capability architecture. It does not approve
PATCH-028, define an implementation file set, authorize schema or API changes,
or modify any completed PATCH contract.

## 2. Governing Authority

This proposal is subordinate to, and shall be interpreted through:

1. `docs/00_Constitution.md`;
2. `docs/Engineering_Intelligence_Manifesto.md` v1.0;
3. the Product Bible, `docs/10_Engineering_Philosophy.md` through
   `docs/17_SATCO_Product_Blueprint.md`;
4. `docs/01_Architecture.md` and accepted ADRs;
5. `docs/19_Governance_Model.md` and `docs/20_Development_Lifecycle.md`;
6. SATCO Implementation Framework v1.1;
7. completed PATCH-023 through PATCH-027 and their accepted design and review
   records.

When this proposal conflicts with a higher authority, the higher authority
governs and this proposal returns to architecture discovery.

## 3. Problem and Architectural Intent

SATCO already has governed foundations for Engineering Objects, Engineering
Relationships, Evidence, authenticated Organization scope, Project and
Workspace context, optimistic concurrency, accountability, and bounded graph
queries. Those foundations describe important parts of Engineering Knowledge,
but they do not yet define one platform-level owner for the complete journey
from Engineering Experience to reviewed Organizational Memory.

Without that ownership boundary, future Engineering, Technical Procurement,
Maintenance, Methods & Systems, and other modules could create separate
capture, knowledge, evidence, or memory systems. That would fragment context,
duplicate records, weaken provenance, and contradict Capture Once.

The proposed intent is therefore:

> Engineering Intelligence is a Core Business Capability of SATCO Platform,
> not a feature of an individual domain module and not an AI subsystem.

It owns the canonical capability boundaries through which governed Engineering
Experience becomes reviewed, reusable Engineering Knowledge. Domain modules
contribute and consume through explicit ports and governed extensions; they do
not fork the capability or own parallel knowledge stores.

## 4. Architecture Decision Proposed

### 4.1 Core Business Capability

Engineering Intelligence is proposed as the platform capability responsible
for the canonical meaning and lifecycle of:

- captured Engineering Experience;
- Engineering Knowledge and its authority state;
- Engineering Context used to interpret that knowledge;
- Engineering Evidence references and their supporting role;
- governed Engineering Relationships;
- review, approval, rejection, qualification, and supersession history;
- Engineering Organizational Memory;
- provenance, rationale, uncertainty, and explanation attached to knowledge.

Ownership means responsibility for canonical contracts, lifecycle semantics,
policy boundaries, and extension rules. It does not mean that all concepts
belong in one aggregate, service, table, database, or deployable component.
Existing aggregate boundaries remain independent.

### 4.2 Module Relationship

Engineering, Technical Procurement, Maintenance, Methods & Systems, and future
approved applications are capability clients. Subject to Version-1 scope and
Product Owner approval, a module may:

- submit experience through an approved Capture port;
- add domain context through governed Engineering Objects and Relationships;
- attach or reference Evidence through approved contracts;
- request authorized knowledge, context, or review state;
- present approved knowledge in a domain-specific experience;
- propose a governed extension without changing the Core.

A module shall not:

- create a parallel authoritative knowledge base or organizational memory;
- copy canonical knowledge into a module-owned source of truth;
- redefine evidence, approval, provenance, or authority semantics;
- bypass Human Review;
- create customer-specific or module-specific Core forks;
- treat AI output as approved Engineering Knowledge;
- weaken Organization, Project, Workspace, discipline, or confidentiality
  boundaries.

### 4.3 Relationship to Existing Platform Core

Engineering Intelligence is a business capability within SATCO Platform. It
uses shared platform capabilities such as identity, authentication,
authorization, Organization tenancy, persistence, Audit, Domain Events,
idempotency, and provider integration. It does not absorb or duplicate those
platform responsibilities.

The architecture therefore has three cooperating areas:

```text
SATCO Platform
├── Platform Core
│   ├── Identity and authenticated Organization context
│   ├── Authorization, Audit, transactions, events, and idempotency
│   └── PostgreSQL and shared infrastructure
├── Engineering Intelligence Core Business Capability
│   ├── Universal Capture and Engineering Journal
│   ├── Intake and contextualization
│   ├── Engineering Knowledge Graph
│   ├── Intelligence Authoring
│   ├── Human Review and Approval
│   ├── Publishing and responsible reuse
│   └── Engineering Organizational Memory
└── Engineering Applications
    ├── Engineering disciplines
    ├── Technical Procurement
    └── future Product-Owner-approved modules
```

The diagram expresses responsibility, not deployment topology.

## 5. Capability Map

### 5.1 Universal Capture and Engineering Journal

Provides one trusted entry boundary for Engineering Experience at its source.
Capture preserves original form, provenance, actor, time, Organization and
available Project/Workspace/discipline scope. Capture creates a governed
record; it does not declare the content correct, current, approved, or reusable.

### 5.2 Intake and Contextualization

Classifies captured material without replacing the original, identifies
missing or conflicting context, and associates it with governed Engineering
Objects, Evidence references, relationships, lifecycle context, and authority
boundaries. The Knowledge Inbox is a conceptual work queue inside this
capability, not a second source of truth.

### 5.3 Engineering Knowledge Graph

Connects Engineering Objects, Relationships, Evidence, captured experience,
decisions, standards, and approved memory through explicit, typed, scoped, and
reviewable meanings. PostgreSQL remains the Version-1 structured System of
Record. A graph or vector database is not authorized by this proposal.

### 5.4 Engineering Intelligence Author

Produces traceable drafts and interpretations from authorized context. It
preserves source references, assumptions, uncertainty, limitations, and the
distinction between fact, inference, recommendation, and decision. It cannot
approve its output or write directly to trusted Organizational Memory.

### 5.5 Human Review and Approval

Is the permanent trust boundary. Qualified Humans explicitly approve, qualify,
reject, return, or supersede proposed understanding within a stated scope.
Silence, system processing, repeated use, or AI confidence is never approval.

### 5.6 Publishing and Responsible Reuse

Makes reviewed understanding available to authorized consumers while carrying
its scope, evidence, approval state, limitations, version, and supersession
status. Presentation may vary by application, but canonical meaning and
identity remain unchanged.

### 5.7 Engineering Organizational Memory

Retains approved Engineering Experience and its context, rationale,
responsibility, evidence, outcomes, and history. Provisional, rejected, and
superseded material remains distinguishable and auditable; it is not silently
presented as current approved knowledge.

### 5.8 AI Gateway

AI integration is an outward adapter used by authoring, analysis, retrieval,
and explanation capabilities. Providers receive only authorized, minimized
context and return advisory results. Provider-specific identifiers and output
must not become the canonical identity or authority of Engineering Knowledge.

## 6. Canonical Transformation Flow

```text
Engineering Work
    ↓
Original Capture
    ↓
Contextualization and governed connection
    ↓
Draft interpretation / authoring
    ↓
Explicit Human Review
    ├── return, reject, or qualify
    └── approve within bounded context
            ↓
Published knowledge / Organizational Memory
            ↓
Authorized reuse in Engineering Work
            ↓
New experience, evidence, correction, or supersession
```

Each stage must preserve traceability to the preceding stage. Enrichment adds
meaning without overwriting the original capture. Correction and supersession
create history; they do not erase it.

## 7. Aggregate and Consistency Boundaries

This proposal preserves the independent aggregates established by completed
PATCHes:

- `EngineeringObject` remains the central EKG entity Aggregate Root;
- `EngineeringRelationship` remains an independent directional assertion
  between two Engineering Object UUIDs;
- `Evidence` remains an independent aggregate and is referenced rather than
  used as a relationship endpoint;
- Project, Engineering Workspace, Engineering Context, identity, and
  Organization membership retain their existing boundaries.

Future Capture, Review, Knowledge Publication, and Organizational Memory
aggregates require separate ADR/EDS decisions. This document deliberately
does not assign fields, tables, endpoints, commands, event schemas, lifecycle
matrices, or transaction boundaries to those future aggregates.

Cross-aggregate workflows shall use application orchestration and governed
ports. They shall not expand one aggregate merely to obtain atomic convenience.
Where a future PATCH requires atomic state, Audit, Domain Events, and
idempotency, one explicit Unit of Work and one PostgreSQL transaction shall be
designed and reviewed for that PATCH.

## 8. Information Authority and State

The architecture distinguishes at least these meanings:

| Meaning | Authority |
|---|---|
| Original capture | Authentic record of what was captured, not proof of truth |
| Context association | Governed assertion subject to scope and review |
| Evidence reference | Support candidate governed by Evidence standing and compatibility |
| Draft interpretation | Advisory and non-authoritative |
| Human-reviewed result | Explicit review outcome with accountable actor |
| Approved knowledge | Trusted only within recorded scope, conditions, and time |
| Organizational Memory | Durable governed record, including history and supersession |

No state transition may collapse these meanings into one generic status.
Exact lifecycle vocabularies remain a future design decision.

## 9. Security, Confidentiality, and Responsibility

- Authentication and trusted active Organization derivation occur before use
  of Engineering Intelligence capabilities.
- Authorization is operation-specific, scope-aware, and deny-by-default before
  identifiers, state, counts, relationships, drafts, or memory are disclosed.
- Effective visibility cannot be lower than the intersection of every
  constituent source, Engineering Object, Evidence item, Workspace, and
  governing policy.
- Cross-Organization knowledge flow is prohibited unless a future accepted ADR
  and approved governance explicitly define it.
- Cross-Project and cross-Workspace use requires explicit reviewed policy; it
  shall not be inferred from technical reachability.
- Creator, steward, reviewer, approver, and other accountable roles must be
  authenticated Humans where professional responsibility is asserted.
- AI and automation cannot occupy an accountable Human role.
- Protected-not-found behavior must prevent existence and graph-shape leakage.

## 10. Data, Integration, and Provider Boundaries

- PostgreSQL remains the primary structured System of Record.
- File storage may retain source content only through a separately governed
  document/content architecture; PATCH-027 Evidence remains reference metadata.
- Search indexes, embeddings, vector stores, graph stores, and model caches are
  derived or complementary stores only after an accepted ADR. They cannot
  become the sole holder of canonical engineering meaning or approval state.
- All domain modules and user experiences integrate through explicit
  application ports and stable contracts, not shared-table ownership.
- AI providers are replaceable outward dependencies behind provider-neutral
  ports. Prompts, model output, and provider conversation state are not the
  System of Record.
- External enterprise systems remain complementary. Integration shall preserve
  source identity, provenance, and ownership rather than silently copying
  external state into approved knowledge.

## 11. Manifesto Alignment

| Principle | Architectural support |
|---|---|
| Engineering First | Capability value is measured by stronger understanding, responsibility, risk control, and learning. |
| Capture Once | One original governed capture is enriched and reused without canonical duplication. |
| Human Authority | Explicit Human Review is the trust boundary; AI cannot approve. |
| Engineering Context Is Sacred | Scope, provenance, time, responsibility, and conditions travel with knowledge. |
| Evidence Before Assumption | Facts, Evidence, inference, uncertainty, and missing information remain distinct. |
| Context Before Recommendation | Authoring follows authorized contextualization and states limitations. |
| Intelligence Before Automation | The proposal defines understanding and trust before automated action. |
| Explainability | Drafts and published knowledge retain basis, assumptions, limitations, and review needs. |
| Provider Independence | AI is an outward adapter; providers own neither identity nor authority. |
| Organizational Ownership | Canonical knowledge and memory remain Organization-governed SATCO records. |
| Continuous Evolution | Correction, qualification, and supersession preserve prior history. |

## 12. Compatibility with Completed PATCH-023 through PATCH-027

- PATCH-023 supplies the EngineeringObject application boundary and approved
  Domain-to-Transport dependency direction.
- PATCH-024 supplies reproducible EngineeringObject persistence.
- PATCH-025 supplies trusted authenticated Organization context.
- PATCH-026 supplies governed, directional, scoped Engineering Relationships
  with bounded traversal.
- PATCH-027 supplies independent Evidence metadata and validation.

This proposal consumes those completed foundations without changing their
models, schemas, APIs, migrations, status, or acceptance evidence. It does not
retroactively classify captured content, create knowledge records, or infer
approval from existing objects, relationships, or evidence.

## 13. Explicit Non-Scope

This proposal does not authorize:

- PATCH-028 implementation or any backend/frontend change;
- database, migration, API, event, schema, command, or error contracts;
- document upload, parsing, OCR, file storage, or content management;
- autonomous capture, approval, publishing, or engineering action;
- AI-created authoritative facts, Evidence, relationships, or decisions;
- graph database, vector database, semantic search, or model selection;
- replacement of ERP, CMMS, SAP, Primavera, EDMS, or project systems;
- activation of Maintenance, Methods & Systems, or other deferred modules;
- modification of completed PATCH-023 through PATCH-027 contracts;
- modification of the certified Foundation through implication.

## 14. Required Decisions Before PATCH-028

The following must be resolved through governance before implementation:

1. accept, revise, or reject this proposed capability and ownership boundary;
2. record the durable ownership and module-dependency decision in an Accepted
   ADR, or explicitly designate an approved equivalent architectural authority;
3. complete Manifesto Governance Integration so PATCH, AR, EDS/IDS, IRR, Sprint,
   and Quality Gate artifacts have mandatory, consistent Manifesto checks;
4. register PATCH-028 in the authoritative PATCH registry and Roadmap with a
   bounded Version-1 problem, scope, non-scope, dependencies, and Product Owner
   approval;
5. select the first thin vertical slice; this proposal does not assume that
   every capability in Section 5 belongs in PATCH-028;
6. produce and approve the required AR, EDS, EDS Review, IDS, Implementation
   Plan, and IRR for that slice;
7. define exact lifecycle, authority, confidentiality, retention, correction,
   and supersession contracts for any new aggregate;
8. resolve document/content ownership if the slice stores source content rather
   than PATCH-027 Evidence references;
9. verify the current repository and environment against the approved IDS.

## 15. Architecture Readiness State

**Architecture proposal:** COMPLETE FOR HUMAN DECISION

**Architecture authority:** NOT YET ACCEPTED

**PATCH-028 implementation readiness:** NOT READY

No implementation may begin from this document alone.

## 16. Revision History

| Version | Date | Description |
|---|---|---|
| 0.1 | 2026-08-02 | Initial Docs-First Engineering Intelligence capability architecture proposal. |
