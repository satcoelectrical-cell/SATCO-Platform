# EngineeringObject Blueprint

Version: 1.0  
Status: Approved  
Last Updated: 2026-07-29

## Table of Contents

1. [Section 1 — Document Control, Purpose, Scope, and Authority](#section-1--document-control-purpose-scope-and-authority)
2. [Section 2 — Ubiquitous Language and Aggregate Boundary](#section-2--ubiquitous-language-and-aggregate-boundary)
3. [Section 3 — Identity, Scope, and Classification](#section-3--identity-scope-and-classification)
4. [Section 4 — Aggregate State and Invariants](#section-4--aggregate-state-and-invariants)
5. [Section 5 — Lifecycle and Authority State Machines](#section-5--lifecycle-and-authority-state-machines)
6. [Section 6 — Responsibility, Governance, and Human Authority](#section-6--responsibility-governance-and-human-authority)
7. [Section 7 — Commands, Mutation Rules, and Domain Events](#section-7--commands-mutation-rules-and-domain-events)
8. [Section 8 — Engineering Knowledge Graph Integration Boundaries](#section-8--engineering-knowledge-graph-integration-boundaries)
9. [Section 9 — Clean Architecture Ports and Dependency Rules](#section-9--clean-architecture-ports-and-dependency-rules)
10. [Section 10 — Persistence and Transaction Contract](#section-10--persistence-and-transaction-contract)
11. [Section 11 — Authorization, Confidentiality, and Audit](#section-11--authorization-confidentiality-and-audit)
12. [Section 12 — Validation and Architecture Approval](#section-12--validation-and-architecture-approval)

# Section 1 — Document Control, Purpose, Scope, and Authority

Revision: 1

## 1.1 Document Control

| Field | Contract |
|---|---|
| Title | EngineeringObject Blueprint |
| Version | 1.0 |
| Status | Draft — Pending Section Approval and Architecture Review |
| Document class | Architecture Blueprint |
| Aggregate | `EngineeringObject` |
| Bounded context | Engineering Knowledge Graph Core |
| Implementation authority | None |
| Required next gate | Independent Architecture Review |
| System of record | PostgreSQL |
| Governing method | DDD, Clean Architecture, Engineering Knowledge Graph, enterprise governance |

## 1.2 Purpose

This Blueprint defines the official architecture contract for the `EngineeringObject` Aggregate Root.

It shall establish:

- the aggregate boundary and ownership of invariants;
- stable identity independent of mutable engineering identifiers;
- organization, customer, project, and workspace scoping;
- controlled classification, lifecycle, and authority semantics;
- human responsibility and governance boundaries;
- permitted mutation paths and concurrency rules;
- integration boundaries with identifiers, relationships, context, evidence, audit, and future EKG extensions;
- the contracts against which implementation and validation must be reviewed.

This Blueprint defines domain and architecture behavior. It does not provide implementation code.

## 1.3 Architectural Vision

SATCO is being built as an Engineering Knowledge Platform, not merely as a CRUD application.

The platform must preserve the identity, meaning, provenance, relationships, responsibility, lifecycle, and history of engineering knowledge. Its architecture must enable governed engineering context, traceability, organizational learning, and responsible assistance while keeping engineering judgment under human authority.

`EngineeringObject` provides the stable domain foundation on which that connected and governed engineering knowledge can evolve.

## 1.4 Architectural Position

`EngineeringObject` is the central Aggregate Root for governed engineering entities in the SATCO Engineering Knowledge Graph Core.

It is object-centric, not document-centric. Documents, tags, vendor references, customer references, and other identifiers may describe, identify, or provide evidence for an Engineering Object, but none of them constitutes its primary identity.

The aggregate protects its own identity, scope, classification, lifecycle, authority standing, responsibility, and governed metadata. External components may request changes but may not directly mutate aggregate state.

## 1.5 In Scope

Blueprint v1.0 governs:

- immutable UUID aggregate identity;
- explicit organization scope;
- optional customer scope;
- mandatory project and workspace scope;
- controlled family, discipline, type, and subtype classification;
- lifecycle state;
- authority standing;
- positive optimistic version;
- creator and steward responsibility;
- creation and modification timestamps;
- aggregate invariants;
- creation and mutation semantics;
- domain-event obligations;
- authorization, audit, transaction, and concurrency boundaries;
- future integration contracts for identifiers and EKG relationships.

Version 1 remains limited to:

- Electrical Engineering;
- Instrumentation Engineering;
- Industrial Automation;
- required shared Engineering Objects.

## 1.6 Explicitly Out of Scope

Blueprint v1.0 does not authorize or define:

- implementation code;
- database migrations;
- API endpoint shapes;
- UI behavior;
- graph traversal algorithms;
- semantic or vector search;
- autonomous AI mutation;
- AI-created engineering approval;
- Engineering Digital Twin behavior;
- unrestricted custom object families or disciplines;
- future domains such as Mechanical, Process, HSE, Maintenance, Reliability, or Asset Integrity;
- physical deletion of authoritative engineering history.

Identifiers and relationships are adjacent aggregates or governed records. Their detailed implementation belongs to later contracts; this Blueprint defines only the boundary by which they may reference or interact with `EngineeringObject`.

## 1.7 Governing Authority and Precedence

This Blueprint derives authority from:

1. the SATCO Platform Constitution;
2. the active SATCO Platform Architecture;
3. approved Architecture Decision Records;
4. approved PATCH documents;
5. accepted architecture and technical reviews;
6. accepted Blueprints and domain contracts applicable to the Engineering Knowledge Graph;
7. implemented and validated foundation contracts applicable to the aggregate.

The Blueprint shall not create a permanent architectural dependency on specific PATCH numbers. PATCH documents provide governed design and delivery inputs, while this Blueprint preserves the durable aggregate contract beyond individual implementation increments.

If this Blueprint conflicts with the Constitution or an approved ADR, the higher-order document governs and the Blueprint must be corrected before implementation.

Any material inconsistency among governing inputs must be recorded and resolved during Architecture Review.

## 1.8 Non-Negotiable Principles

- Human engineers retain engineering judgment and approval authority.
- AI is advisory and may not become an accountable actor.
- PostgreSQL remains the structured system of record.
- Aggregate identity is immutable and independent of external identifiers.
- Controlled vocabulary cannot be replaced by arbitrary free text.
- Authorization occurs before disclosure or mutation.
- Governed mutations are attributable to an authenticated human actor.
- Audit and state mutation must form one atomic outcome.
- Optimistic concurrency prevents silent lost updates.
- Authoritative history is preserved; ordinary physical deletion is prohibited.
- Future domains extend the EKG through governed contracts and may not fork or redesign the EKG Core.
- No implementation may begin until the completed Blueprint passes Architecture Review and receives explicit approval.

# Section 2 — Ubiquitous Language and Aggregate Boundary

Revision: 0

## 2.1 Purpose

This section establishes the canonical domain language and consistency boundary of the `EngineeringObject` Aggregate Root.

The terms defined here shall be used consistently across domain design, architecture reviews, implementation planning, validation, APIs, persistence mappings, and future Engineering Knowledge Graph extensions.

Implementation-specific terminology shall not redefine these domain meanings.

## 2.2 Ubiquitous Language

### Engineering Object

An **Engineering Object** is a governed engineering entity with stable identity, engineering meaning, lifecycle, responsibility, scope, and traceability.

An Engineering Object may represent:

- physical equipment;
- instrumentation;
- electrical equipment;
- automation equipment;
- engineering systems;
- project engineering entities;
- governed engineering concepts;
- shared engineering entities required by the approved Version-1 disciplines.

An Engineering Object is not merely a database row, document, file, tag, extracted text fragment, or user-interface record.

### EngineeringObject Aggregate Root

The **EngineeringObject Aggregate Root** is the sole authoritative entry point for creating or changing aggregate-owned state.

It protects the Engineering Object’s:

- immutable identity;
- scope;
- classification;
- lifecycle state;
- authority standing;
- optimistic version;
- creator responsibility;
- steward responsibility;
- governed metadata;
- timestamps.

The terms **Engineering Object** and `EngineeringObject` refer to the same domain concept. The spaced form expresses the business concept; the code-style form identifies the aggregate contract.

### Engineering Object Identity

**Engineering Object Identity** is the immutable internal UUID that preserves continuity throughout the object’s lifecycle.

Identity remains unchanged when an external identifier, label, classification, lifecycle state, authority standing, steward, or connected evidence changes.

### Engineering Identifier

An **Engineering Identifier** is a governed identifier used by engineers, customers, vendors, manufacturers, documents, or external systems to refer to an Engineering Object.

Examples include:

- tag number;
- equipment number;
- loop number;
- cable number;
- panel number;
- feeder number;
- system identifier;
- vendor reference;
- manufacturer model reference;
- controlled external key.

An Engineering Identifier does not constitute Engineering Object Identity.

Identifier ownership, uniqueness, lifecycle, evidence, and persistence belong to a separately governed contract.

### Scope

**Scope** defines the authorized organizational and project boundary within which an Engineering Object exists and may be disclosed or changed.

For Blueprint v1.0, aggregate scope consists of:

- Organization;
- Customer, when applicable;
- Project;
- Engineering Workspace.

Discipline is classification, not a substitute for access scope.

### Organization Scope

**Organization Scope** identifies the platform-operating organization that governs the Engineering Object.

It is mandatory even while the Organization aggregate remains outside the current implementation boundary.

### Customer Scope

**Customer Scope** identifies the applicable customer boundary.

It may be absent only when the Engineering Object is legitimately internal and not associated with a customer.

Absence of Customer scope does not remove Organization, Project, or Workspace scope.

### Project Scope

**Project Scope** identifies the governed engineering undertaking to which the Engineering Object belongs.

Project scope is mandatory in Blueprint v1.0.

Similarity between objects in different Projects does not create shared identity, authorization, or evidence applicability.

### Engineering Workspace Scope

**Engineering Workspace Scope** identifies the controlled collaboration boundary within a Project and discipline.

Workspace scope is mandatory in Blueprint v1.0.

The Engineering Object references a Workspace but does not own or control the Workspace aggregate.

### Classification

**Classification** expresses the governed engineering kind and professional context of an Engineering Object.

Classification consists of:

- Engineering Object Family;
- Engineering Discipline;
- Engineering Object Type;
- optional controlled subtype.

Classification shall use approved controlled vocabulary where such vocabulary exists.

Classification is not identity and must not be used as an authorization shortcut.

### Engineering Object Family

An **Engineering Object Family** is the highest approved Version-1 classification boundary.

Approved families are:

- instrumentation;
- electrical;
- automation;
- shared.

A new family is an EKG extension and requires governance approval.

### Engineering Discipline

An **Engineering Discipline** identifies the professional engineering domain responsible for the object’s engineering context.

Approved Version-1 disciplines are:

- instrumentation;
- electrical;
- industrial automation;
- shared engineering.

Discipline does not itself grant ownership, approval authority, or access.

### Engineering Object Type

An **Engineering Object Type** identifies the governed kind of Engineering Object within its family and discipline.

An object type shall not be invented through arbitrary free text.

The approved object-type vocabulary may evolve only through a governed extension that preserves compatibility with the EKG Core.

### Controlled Subtype

A **Controlled Subtype** provides optional additional classification below the Engineering Object Type.

A subtype may refine meaning but shall not contradict the object’s family, discipline, or type.

### Lifecycle State

**Lifecycle State** represents where the Engineering Object stands in its governed existence.

Lifecycle is distinct from authority, review, approval, confidentiality, and physical deletion.

Changing lifecycle state does not create a new Engineering Object identity.

### Authority Standing

**Authority Standing** represents the governance strength and reliability of the Engineering Object record.

Authority standing is distinct from lifecycle state.

It shall not be inferred from repetition, document presence, lifecycle state, AI confidence, or relationship count. Approved authority standing may result only from an authorized human-governed process.

### Responsibility

**Responsibility** identifies accountable human association with the Engineering Object.

Blueprint v1.0 preserves:

- Creator;
- Steward.

Responsibility is distinct from authentication, authorization, discipline, ownership of connected aggregates, and formal engineering approval.

### Creator

The **Creator** is the authenticated Human actor accountable for creating the Engineering Object record.

Creator responsibility is immutable after creation.

### Steward

The **Steward** is the authenticated Human actor currently accountable for maintaining the governed integrity of the Engineering Object.

Stewardship may change only through an approved aggregate operation.

Stewardship does not automatically grant engineering approval authority.

### Optimistic Version

The **Optimistic Version** is the positive aggregate version used to detect concurrent modification.

The initial version is `1`.

Each successful governed mutation changes the version exactly once. A rejected or failed operation does not change it.

### Governed Mutation

A **Governed Mutation** is an authorized request that successfully changes aggregate-owned state while preserving all invariants, responsibility, audit, and concurrency requirements.

Direct field modification is not a governed mutation.

### Evidence

**Evidence** is a governed source that supports an engineering fact, classification, authority claim, or decision.

Evidence may reference an Engineering Object, but authoritative Evidence remains outside the EngineeringObject aggregate unless a future accepted contract explicitly assigns ownership otherwise.

AI output alone is not authoritative engineering Evidence.

### Engineering Relationship

An **Engineering Relationship** is a governed, directional, traceable engineering statement connecting a source Engineering Object to a target Engineering Object.

An Engineering Relationship has its own identity, lifecycle, responsibility, authority, and version. It is not internal mutable state of either connected EngineeringObject aggregate.

### Engineering Context

**Engineering Context** is a governed unit of engineering knowledge, constraint, observation, understanding, or decision support surrounding Engineering Objects and their relationships.

Engineering Context is a separate aggregate. It may include or reference an Engineering Object without becoming part of that object’s consistency boundary.

### Domain Event

A **Domain Event** is an immutable record that a governed domain fact has occurred as the result of a successful aggregate operation.

A Domain Event reports an accepted state transition. It does not authorize the transition and is not a substitute for Audit.

### Audit Record

An **Audit Record** is the durable accountability record of an attempted or completed governed action.

Audit and Domain Events serve different purposes: Audit establishes accountability; Domain Events communicate accepted domain facts.

## 2.3 Aggregate Consistency Boundary

The EngineeringObject aggregate is the immediate transactional consistency boundary for aggregate-owned state.

Within one successful governed mutation, the system shall preserve consistency among:

- identity;
- scope;
- classification;
- lifecycle state;
- authority standing;
- responsibility;
- optimistic version;
- governed timestamps;
- required Audit outcome;
- resulting Domain Events.

An aggregate instance shall never be observable in a partially mutated state.

## 2.4 Aggregate-Owned State

The EngineeringObject Aggregate Root exclusively owns:

- its immutable UUID;
- its approved scope references;
- its controlled classification;
- its lifecycle state;
- its authority standing;
- its optimistic version;
- its creator identity;
- its steward identity;
- its creation timestamp;
- its modification timestamp;
- aggregate-level validation of those values;
- authorization of its permitted domain transitions after the applicable actor and policy context are supplied.

No repository, API adapter, automation, AI component, event consumer, importer, or external service may bypass the Aggregate Root to change this state.

## 2.5 Referenced but Externally Owned Concepts

The EngineeringObject aggregate may reference, but does not own:

- Organization;
- Customer;
- Project;
- Engineering Workspace;
- User or Human actor;
- Engineering Identifier;
- Engineering Relationship;
- Engineering Context;
- Evidence;
- Document;
- Requirement;
- Standard;
- Technical Decision;
- Audit records;
- external system records.

Deleting, archiving, renaming, or changing a referenced entity shall not silently mutate the Engineering Object or transfer ownership of its invariants.

Referential validity and cross-aggregate policy shall be coordinated through approved application services and persistence constraints.

## 2.6 Aggregate Boundary Rules

1. An Engineering Object is created and mutated only through its Aggregate Root.
2. No external identifier may replace or alter the immutable internal UUID.
3. The aggregate shall not embed the mutable state of Project, Workspace, Customer, User, Evidence, Context, Identifier, or Relationship records.
4. A relationship between two Engineering Objects shall not merge their consistency boundaries.
5. A shared document or identifier shall not merge Engineering Objects.
6. Cross-Project similarity shall not create shared identity.
7. Cross-aggregate operations shall use explicit application orchestration and shall not rely on hidden side effects.
8. The aggregate shall reject state that violates its own invariants.
9. The aggregate shall not make database, transport, user-interface, or AI-provider decisions.
10. The aggregate shall not infer Human approval, authority, or responsibility.
11. The aggregate shall not physically delete authoritative engineering history.
12. Domain events shall be produced only for successful governed changes.
13. Failed or rejected operations shall leave aggregate state and version unchanged.
14. External consumers may observe aggregate state only through authorized contracts.

## 2.7 Aggregate Size and Design Discipline

`EngineeringObject` shall remain a focused aggregate, not a container for the entire Engineering Knowledge Graph.

Identifiers, relationships, context, evidence, documents, and other connected knowledge shall remain separately governed so that:

- aggregate transactions remain bounded;
- concurrency conflicts remain meaningful;
- authorization rules remain explicit;
- graph growth does not enlarge one object’s consistency boundary;
- lifecycle and responsibility remain owned by the correct domain concept;
- future modules can extend the EKG without redesigning the core aggregate.

References between aggregates shall use stable identities. Connected graph meaning shall be assembled outside the EngineeringObject aggregate through authorized application and query boundaries.

## 2.8 Boundary Acceptance Conditions

This section is satisfied when the architecture confirms that:

- `EngineeringObject` is the sole owner of its protected state;
- UUID identity is distinct from every engineering identifier;
- lifecycle and authority are distinct concepts;
- creator and steward are accountable Human responsibilities;
- Project and Workspace are referenced scopes, not child entities;
- identifiers, relationships, context, and evidence remain outside the aggregate boundary;
- no graph-wide transaction is required to mutate one Engineering Object;
- no infrastructure or AI concern enters the domain model;
- future EKG extensions can reference the aggregate without changing its identity or core boundary.

# Section 3 — Identity, Scope, and Classification

Revision: 0

## 3.1 Purpose

This section defines the domain contract for identifying, scoping, and classifying an Engineering Object.

These rules ensure that every Engineering Object:

- retains stable identity throughout its lifecycle;
- exists within an explicit authorized boundary;
- carries governed engineering classification;
- cannot be mistaken for an external identifier, document, or display label;
- remains compatible with future governed EKG extensions.

## 3.2 Identity Contract

Every Engineering Object shall have exactly one immutable internal identity.

The identity shall:

- be represented by a UUID;
- be assigned when the aggregate is created;
- remain unchanged for the aggregate’s entire existence;
- remain unique within the SATCO Platform;
- have no embedded business meaning;
- remain independent of database ordering and deployment topology;
- remain independent of Organization, Customer, Project, and Workspace identifiers;
- remain independent of classification;
- remain independent of lifecycle and authority standing;
- remain independent of all external engineering identifiers.

A missing, malformed, or reassigned UUID invalidates the aggregate.

## 3.3 Identity Continuity

The Engineering Object retains the same identity when any permitted mutable attribute changes, including:

- engineering identifier;
- external reference;
- classification, when an approved reclassification operation permits it;
- lifecycle state;
- authority standing;
- steward;
- governed metadata;
- connected Evidence;
- connected Engineering Context;
- connected Engineering Relationships.

A change in description, understanding, evidence, or responsibility does not by itself create a new Engineering Object.

A replacement object, materially distinct engineering entity, or explicit supersession may require a new Engineering Object identity. That determination must be made through a governed domain operation and shall not be inferred from a renamed tag, revised document, changed vendor reference, or modified display label.

## 3.4 Identity Prohibitions

The following shall never serve as the Engineering Object’s primary identity:

- tag number;
- equipment number;
- loop number;
- cable number;
- panel number;
- feeder number;
- system or subsystem identifier;
- drawing or document number;
- vendor reference;
- manufacturer model;
- customer reference;
- file name;
- document title;
- display label;
- temporary project code;
- user-interface wording;
- database row position;
- user-visible sequence number.

No importer, integration, repository, migration, or user interface may silently replace internal identity with one of these values.

## 3.5 External Identifier Resolution

External identifiers may be used to locate a candidate Engineering Object only through a governed identifier-resolution process.

Resolution shall consider:

- identifier kind;
- normalized value;
- issuing scope;
- Organization;
- Project;
- Workspace when applicable;
- lifecycle and effective standing;
- authorization;
- ambiguity.

An external identifier match shall not override the UUID identity contract.

If resolution produces no match or multiple authorized matches, the system shall report the condition explicitly. It shall not silently select an Engineering Object or create shared identity.

The detailed Engineering Identifier contract remains outside Blueprint v1.0.

## 3.6 Scope Contract

Every Engineering Object in Blueprint v1.0 shall carry explicit scope comprising:

| Scope dimension | Requirement | Meaning |
|---|---:|---|
| Organization | Mandatory | Governing platform-operator boundary |
| Customer | Conditional | Applicable customer boundary |
| Project | Mandatory | Governed engineering undertaking |
| Engineering Workspace | Mandatory | Controlled Project collaboration boundary |

Scope is part of the aggregate’s governed state.

Scope determines domain applicability and contributes to authorization, but scope alone does not grant access.

## 3.7 Organization Scope

Organization scope shall:

- be present when the aggregate is created;
- identify exactly one governing Organization;
- remain explicit even before an Organization aggregate is introduced;
- prevent accidental cross-organization identity or disclosure;
- be validated against the authenticated operating context;
- be consistent with every referenced Project, Workspace, Customer, and responsible Human actor.

Organization scope shall not be inferred from a user interface, deployment, database connection, or external identifier.

An Engineering Object cannot exist without Organization scope.

## 3.8 Customer Scope

Customer scope shall be present when the Engineering Object is associated with customer-governed work or information.

Customer scope may be absent only when:

- the Engineering Object is legitimately internal;
- no Customer owns or governs its applicable engineering context;
- Project and Workspace scope remain valid;
- applicable authorization and confidentiality rules permit the absence.

A nullable Customer scope does not mean public, globally reusable, or cross-customer information.

Where Customer scope is present, it shall be consistent with the Project and Organization boundaries.

## 3.9 Project Scope

Project scope is mandatory for Blueprint v1.0.

Project scope shall:

- identify exactly one Project;
- belong to the same Organization scope as the Engineering Object;
- be compatible with Customer scope when Customer scope is present;
- define the primary engineering undertaking in which the object is governed;
- prevent automatic identity sharing across Projects;
- remain explicit in all authorized aggregate access and mutation contexts.

An Engineering Object resembling an object in another Project remains a distinct Engineering Object unless a future approved architecture explicitly introduces a different shared-knowledge model.

## 3.10 Engineering Workspace Scope

Workspace scope is mandatory for Blueprint v1.0.

The referenced Engineering Workspace shall:

- belong to the same Project;
- belong to the same Organization;
- be compatible with the Engineering Object’s discipline;
- be active or otherwise permitted to receive the operation;
- be visible to the authenticated actor performing the operation.

Workspace scope establishes the immediate collaboration boundary. It does not transfer ownership of the Engineering Object to the Workspace aggregate.

## 3.11 Scope Coherence Invariants

An Engineering Object is valid only when all applicable scope references describe one coherent authorized boundary.

At minimum:

1. Organization scope is present.
2. Project scope is present.
3. Workspace scope is present.
4. The Project belongs to the stated Organization.
5. The Workspace belongs to the stated Project and Organization.
6. Customer scope, when present, is compatible with the Project and Organization.
7. The actor is authorized within the applicable scope before disclosure or mutation.
8. Scope references do not contradict classification or responsibility requirements.
9. Scope cannot be assembled from entities belonging to different Organizations or Projects.
10. Missing scope cannot be substituted with a default, wildcard, or inferred global scope.

Cross-scope violations shall be rejected explicitly.

## 3.12 Scope Mutation

Scope changes are identity-preserving only when an approved domain operation determines that the same engineering entity continues to exist within the new scope.

A scope change shall not be treated as ordinary field editing.

Any future scope-transfer operation must define:

- required authorization;
- source and target scope validation;
- Customer applicability;
- Workspace and discipline compatibility;
- effects on identifiers;
- effects on relationships and context;
- evidence applicability;
- confidentiality consequences;
- responsibility transfer;
- Audit requirements;
- Domain Events;
- concurrency handling.

Until such an operation is approved, direct changes to Organization, Project, or Workspace scope are prohibited.

No cross-Organization scope transfer is authorized by Blueprint v1.0.

## 3.13 Classification Contract

Every Engineering Object shall have a complete governed classification consisting of:

| Classification dimension | Requirement |
|---|---:|
| Engineering Object Family | Mandatory |
| Engineering Discipline | Mandatory |
| Engineering Object Type | Mandatory |
| Controlled Subtype | Optional |

Classification expresses what the Engineering Object is. It does not establish identity, authority, approval, ownership, or access.

## 3.14 Engineering Object Family

Blueprint v1.0 permits these controlled families:

- instrumentation;
- electrical;
- automation;
- shared.

The family shall:

- use an approved controlled value;
- remain compatible with the selected discipline and object type;
- reject arbitrary user-defined alternatives;
- be validated when the aggregate is created;
- change only through an approved reclassification operation.

Future families require a governed EKG extension and must not alter the meaning of existing values.

## 3.15 Engineering Discipline

Blueprint v1.0 permits these controlled disciplines:

- instrumentation;
- electrical;
- industrial automation;
- shared engineering.

The discipline shall:

- use an approved controlled value;
- be compatible with the selected family and type;
- be compatible with the referenced Workspace;
- identify engineering context without implying authority or access;
- change only through an approved reclassification operation.

A shared object may use shared engineering only where its meaning genuinely crosses or supports the approved disciplines. “Shared” shall not be used to bypass classification or scope rules.

## 3.16 Engineering Object Type

Engineering Object Type shall identify the governed kind of Engineering Object within the approved family and discipline.

The type shall:

- be non-empty;
- use an approved controlled vocabulary;
- have stable semantic meaning;
- be compatible with family and discipline;
- be validated at aggregate creation;
- avoid customer-specific or project-specific code forks;
- avoid arbitrary free-text invention.

Version-1 object types may include governed types from the approved Instrumentation, Electrical, Automation, and Shared families.

The Blueprint does not convert the illustrative object lists in earlier design documents into an unrestricted implementation registry. The authoritative Version-1 type catalog must be finite, governed, and validated before implementation.

## 3.17 Controlled Subtype

A subtype is optional.

When present, it shall:

- come from an approved controlled vocabulary or governed extension point;
- refine, not replace, the Engineering Object Type;
- remain compatible with family, discipline, and type;
- not contain an external identifier disguised as classification;
- not create a new unapproved object family;
- not change authorization or authority standing by itself.

Absence of a subtype is valid when the Engineering Object Type provides sufficient meaning.

## 3.18 Classification Coherence

The combination of family, discipline, type, and subtype shall represent one coherent engineering concept.

The aggregate shall reject combinations that are:

- unknown;
- internally contradictory;
- outside the approved Version-1 disciplines;
- based only on arbitrary free text;
- incompatible with Workspace discipline;
- aliases that duplicate an existing governed type without approval;
- attempts to introduce a deferred domain;
- attempts to encode lifecycle, authority, scope, or identifiers as classification.

Classification validation shall be deterministic and explainable.

## 3.19 Reclassification

Reclassification is a governed mutation, not ordinary metadata editing.

A future approved reclassification operation shall determine whether:

- the same engineering entity remains represented;
- the target classification is permitted;
- the Workspace remains compatible;
- existing identifiers remain applicable;
- relationships and context remain semantically valid;
- Evidence supports the change;
- authority standing requires reconsideration;
- Human review is required;
- the change must emit a Domain Event;
- the optimistic version increments exactly once.

Reclassification shall never change the Engineering Object UUID.

Blueprint v1.0 does not authorize unrestricted reclassification.

## 3.20 Creation Validity

A new Engineering Object is valid only when:

- a valid immutable UUID is assigned;
- Organization scope is present;
- Project scope is present;
- Workspace scope is present;
- Customer scope is valid when applicable;
- all scope references are coherent;
- family is controlled and approved;
- discipline is controlled and approved;
- type is controlled and approved;
- subtype is valid when present;
- classification is internally coherent;
- classification is compatible with Workspace discipline;
- creator and steward are authenticated Human actors;
- the initial lifecycle and authority standing are valid;
- optimistic version begins at `1`;
- creation and modification timestamps are established consistently;
- applicable authorization and Audit requirements are satisfied.

Failure of any mandatory condition shall reject creation without producing a partially valid aggregate.

## 3.21 Architecture Review Note

Project Scope being mandatory is accepted for Blueprint v1.0 to support the initial SATCO MVP.

This decision may be revisited in a future Blueprint revision if shared engineering knowledge outside project boundaries becomes a product requirement.

This note does not alter the mandatory Project-scope contract in Blueprint v1.0.

## 3.22 Acceptance Conditions

This section is satisfied when Architecture Review confirms that:

- internal UUID is the sole primary Engineering Object identity;
- external identifiers cannot alter aggregate identity;
- all mandatory scope dimensions are explicit;
- Customer scope remains conditional without becoming global scope;
- scope references form one coherent Organization–Project–Workspace boundary;
- unauthorized or ambiguous cross-scope behavior is rejected;
- classification uses controlled vocabulary;
- family, discipline, type, and subtype remain distinct;
- classification does not imply authority or access;
- scope and classification changes cannot bypass governed aggregate operations;
- future extensions can add governed vocabulary without redesigning the EKG Core.

# Section 4 — Aggregate State and Invariants

## 4.1 Aggregate State Model

Revision: 0

The state of an `EngineeringObject` is the complete authoritative domain state governed by one aggregate instance at a specific optimistic version.

The aggregate state shall be modeled as the following conceptual composition:

\[
EngineeringObjectState =
Identity +
Scope +
Classification +
Governance +
Responsibility +
Concurrency +
TemporalMetadata
\]

This expression is a domain contract, not a persistence schema.

### 4.1.1 State Components

| Component | Aggregate-owned content | State character |
|---|---|---|
| Identity | Internal Engineering Object UUID | Immutable |
| Scope | Approved scope references defined by Section 3 | Governed; direct editing prohibited |
| Classification | Approved classification defined by Section 3 | Governed |
| Governance | Lifecycle state and authority standing | Governed |
| Responsibility | Creator and current steward | Creator immutable; steward governed |
| Concurrency | Positive optimistic version | Monotonically increasing |
| Temporal metadata | Creation and modification timestamps | System-governed |

Every aggregate instance shall contain a complete and internally consistent value for each mandatory component.

The absence of a mandatory component represents invalid aggregate state, not a partially created Engineering Object.

### 4.1.2 Authoritative State

Aggregate-owned state is authoritative only when it:

- resulted from successful aggregate creation or a permitted aggregate operation;
- satisfies all applicable invariants;
- was accepted under the expected optimistic version;
- completed within the required transaction boundary;
- preserves accountable Human responsibility;
- has the required Audit outcome;
- is durably persisted as one consistent aggregate version.

A requested, proposed, calculated, imported, or AI-suggested value is not authoritative aggregate state until accepted through the governed mutation path.

### 4.1.3 Current State and Historical State

The **current state** is the latest successfully committed aggregate version.

A **historical state** is an earlier committed version or an immutable reconstruction of that version from governed history.

Historical state shall:

- remain distinguishable from current state;
- never be overwritten and presented as if it had always been current;
- preserve the responsibility and time associated with the historical change;
- remain available to authorized Audit and traceability processes where required.

A historical state is not independently mutable. Any new change operates against the current aggregate version.

### 4.1.4 Proposed State

A **proposed state** is the candidate result of applying a command to the current state.

Proposed state:

- is not authoritative;
- must remain invisible as current state until validation and transaction completion;
- shall be evaluated against aggregate invariants;
- shall not increment the persisted version unless accepted;
- shall not emit a committed Domain Event unless accepted;
- shall not create a successful-mutation Audit outcome unless accepted.

Rejection of proposed state leaves the current state unchanged.

### 4.1.5 Derived Information

Derived information may be calculated from aggregate state but is not aggregate-owned authoritative state unless a future accepted Blueprint explicitly promotes it.

Examples include:

- display formatting;
- reverse relationship views;
- graph neighborhoods;
- search projections;
- readiness indicators;
- engineering-health indicators;
- AI summaries;
- similarity scores;
- inferred classifications;
- inferred risks;
- reporting labels.

Derived information shall:

- identify its source aggregate version when version sensitivity is material;
- be recomputable without changing the aggregate;
- never silently replace authoritative state;
- never create lifecycle, authority, responsibility, or approval standing;
- remain subject to authorization before disclosure.

### 4.1.6 Referenced State

Information owned by another aggregate or governed record is **referenced state**.

Referenced state may be consulted to validate or authorize an Engineering Object operation, but it does not become internally owned merely because the aggregate refers to it.

The aggregate shall retain only the stable references and aggregate-owned facts permitted by its contract.

Changes in referenced state shall not silently rewrite the Engineering Object. If a referenced change requires an Engineering Object response, that response must occur through an explicit governed operation.

### 4.1.7 Transient Operation Context

The following may be required to evaluate an operation but shall not become aggregate state solely because they were supplied to that operation:

- authenticated actor context;
- authorization decision;
- request correlation information;
- expected version;
- policy evaluation;
- reference-validation results;
- current time supplied by an approved clock;
- supporting Evidence supplied for evaluation;
- AI recommendations;
- transport metadata.

Transient operation context shall not be serialized as aggregate-owned domain state unless another approved contract explicitly requires it.

Information needed for accountability may instead be preserved in Audit records or Domain Event metadata under their respective contracts.

### 4.1.8 State Transition Form

Every attempted mutation shall conceptually follow:

\[
CurrentState + Command + AuthorizedContext
\rightarrow
\begin{cases}
NewState + DomainEvents + AuditOutcome \\
Rejection + UnchangedState + AuditOutcome
\end{cases}
\]

A successful transition shall be atomic.

A transition shall never produce:

- persisted partial state;
- more than one aggregate version increment;
- committed events for an uncommitted state;
- an authoritative state change without its required Audit outcome;
- a successful state change from a stale expected version.

### 4.1.9 State Encapsulation

Aggregate state shall not expose unrestricted mutation.

External layers may:

- submit commands;
- provide authorized operation context;
- retrieve permitted representations;
- persist or rehydrate aggregate state through approved ports;
- publish committed Domain Events.

External layers shall not:

- assign aggregate fields directly;
- construct invalid intermediate state and persist it;
- bypass aggregate transition rules;
- treat persistence models as unrestricted domain mutation objects;
- infer accepted state from an uncommitted event or API response;
- use AI output as an automatic state transition.

### 4.1.10 Review Criteria

Section 4.1 is acceptable when Architecture Review confirms that:

- aggregate-owned, referenced, derived, historical, proposed, and transient state are clearly distinguished;
- only successfully committed aggregate state is authoritative;
- proposed or rejected state cannot leak as current state;
- external aggregate state is referenced rather than absorbed;
- derived and AI-generated information cannot silently alter authoritative state;
- state transitions preserve atomic state, version, Audit, and Domain Event outcomes;
- aggregate state remains encapsulated behind governed operations.

## 4.2 Aggregate Invariants

Revision: 0

An `EngineeringObject` is valid only when all applicable invariants hold. Creation, rehydration, and mutation shall reject invalid state.

### 4.2.1 Intrinsic Invariants

The aggregate shall enforce:

1. Identity is a valid, immutable UUID.
2. Mandatory state defined by Sections 3 and 4.1 is present.
3. Controlled values belong to approved vocabularies.
4. Classification is internally coherent.
5. Lifecycle and authority standing remain distinct.
6. Creator is present and immutable.
7. Steward is present.
8. Optimistic version is positive.
9. Creation timestamp is immutable.
10. Modification timestamp is not earlier than creation.
11. Authoritative state is not physically deleted through an ordinary domain operation.

### 4.2.2 Contextual Invariants

The application boundary shall validate before mutation:

- scope-reference existence and coherence;
- Workspace compatibility;
- authenticated Human responsibility;
- actor authorization;
- permitted lifecycle and authority transitions;
- applicable Evidence or approval requirements;
- expected optimistic version.

Validated context shall be supplied to the aggregate through explicit contracts. The aggregate shall not query infrastructure directly.

### 4.2.3 Mutation Invariants

A successful mutation shall:

- begin from the current expected version;
- pass all applicable validation;
- preserve identity and immutable state;
- increment version exactly once;
- update the modification timestamp;
- produce only the Domain Events required by the accepted change;
- commit state, required Audit, and event-recording obligations atomically.

A rejected mutation shall preserve state and version.

### 4.2.4 Rehydration Invariant

Persistence may rehydrate only a complete valid aggregate.

Invalid persisted data shall raise an integrity failure. Rehydration shall not:

- invent defaults;
- repair state silently;
- bypass controlled vocabulary;
- emit Domain Events;
- increment version;
- update timestamps.

Repair requires a separately authorized corrective workflow.

### 4.2.5 Cross-Aggregate Boundary

`EngineeringObject` enforces its own invariants only.

Rules requiring current state from another aggregate shall be coordinated by an application service. Cross-aggregate validation shall not expand the EngineeringObject transaction boundary or allow direct mutation of another aggregate.

### 4.2.6 Invariant Failure Contract

Invariant failure shall:

- reject the operation explicitly;
- identify the violated contract without disclosing unauthorized data;
- leave authoritative state unchanged;
- produce no committed domain-change event;
- preserve required attempt-level Audit evidence.

### 4.2.7 Review Criteria

Section 4.2 is acceptable when:

- intrinsic and contextual invariants are separated;
- invalid state cannot be created, rehydrated, or persisted silently;
- successful mutation preserves atomicity and one version increment;
- rejected mutation leaves state unchanged;
- cross-aggregate validation remains outside the aggregate;
- corrective repair requires explicit authorization.

## 4.3 Aggregate State Exposure

Revision: 0

Aggregate state shall be exposed through immutable, authorized representations. Consumers shall not receive mutable access to aggregate internals.

### 4.3.1 State Representation

An exposed representation shall:

- identify the Engineering Object UUID;
- identify the represented optimistic version;
- contain only authorized fields;
- preserve controlled-value semantics;
- distinguish authoritative values from derived information;
- avoid exposing persistence-specific behavior.

Representations are views of state, not mutation interfaces.

### 4.3.2 Snapshot Semantics

A state snapshot represents one committed aggregate version.

Snapshots shall:

- remain internally consistent;
- never combine fields from different versions;
- identify staleness when material;
- remain immutable after publication;
- not imply that referenced aggregates share the same version.

### 4.3.3 Disclosure Boundary

Authorization shall be evaluated before state disclosure.

A consumer shall not infer unauthorized information from:

- object existence;
- scope references;
- classification;
- lifecycle or authority standing;
- responsibility identities;
- error details;
- relationship counts.

Redaction shall not produce a representation that misstates engineering meaning. When safe representation is impossible, access shall be denied.

### 4.3.4 Change Representation

A successful mutation may expose a change result containing:

- aggregate identity;
- previous version;
- new version;
- accepted operation type;
- resulting authorized representation;
- correlation reference.

The result shall not expose internal mutable state or uncommitted events.

### 4.3.5 Read Models

Read models and graph projections may optimize retrieval but are not authoritative aggregate state.

They shall:

- preserve source identity and version;
- tolerate defined projection delay;
- never authorize mutation;
- never override the System of Record;
- be rebuilt from governed authoritative data.

### 4.3.6 Review Criteria

Section 4.3 is acceptable when:

- exposed state is immutable and versioned;
- authorization precedes disclosure;
- snapshots cannot mix aggregate versions;
- redaction cannot distort engineering meaning;
- read models remain non-authoritative;
- no exposed representation permits direct mutation.

# Section 5 — Lifecycle and Authority State Machines

## 5.1 Lifecycle State Machine

Revision: 0

Lifecycle state records the governed existence of an Engineering Object. It does not represent authority, approval, confidentiality, or operational equipment status.

### 5.1.1 States

| State | Meaning |
|---|---|
| `proposed` | Created but not yet active for normal engineering use |
| `active` | Current within its governed scope |
| `superseded` | Replaced by a newer governed Engineering Object |
| `withdrawn` | Removed from current use without erasing history |
| `retired` | Permanently closed from normal use |

Initial lifecycle state shall be `proposed`.

### 5.1.2 Permitted Transitions

| From | To |
|---|---|
| `proposed` | `active`, `withdrawn` |
| `active` | `superseded`, `withdrawn`, `retired` |
| `withdrawn` | `proposed` |
| `superseded` | `retired` |
| `retired` | None |

Any transition not listed is prohibited in Blueprint v1.0.

### 5.1.3 Transition Contract

Every lifecycle transition shall:

- use an explicit aggregate operation;
- require the current expected version;
- require an authenticated, authorized Human actor;
- include a non-empty engineering rationale;
- satisfy applicable Evidence and review policy;
- preserve identity and history;
- increment version exactly once;
- update modification time;
- create required Audit and Domain Event records atomically.

Lifecycle shall never change through field assignment, import side effects, relationship changes, elapsed time, or AI inference.

### 5.1.4 Supersession

Transition to `superseded` shall identify the replacement Engineering Object.

The replacement shall:

- be distinct from the superseded object;
- exist within an authorized compatible scope;
- be suitable for the stated engineering purpose.

The supersession relationship remains governed outside this aggregate. Failure to establish the required governed reference shall reject the transition.

### 5.1.5 Withdrawal and Reactivation

Withdrawal preserves identity and history.

Reactivation is limited to:

\[
withdrawn \rightarrow proposed
\]

The object must pass current validation and governance before returning to `active`. Direct `withdrawn → active` transition is prohibited.

### 5.1.6 Retirement

`retired` is terminal in Blueprint v1.0.

Retirement shall not physically delete the Engineering Object or its governed history. Reuse requires a new Engineering Object identity.

### 5.1.7 Review Criteria

Section 5.1 is acceptable when:

- lifecycle meanings are distinct and controlled;
- only listed transitions are permitted;
- initial state is `proposed`;
- supersession requires a governed replacement;
- withdrawal is reversible only through `proposed`;
- retirement is terminal;
- no AI or external component may change lifecycle automatically.

## 5.2 Authority State Machine

Revision: 0

Authority standing records the governance strength of an Engineering Object record. It does not represent lifecycle state or broader deliverable approval.

### 5.2.1 States

| State | Meaning |
|---|---|
| `draft` | Not submitted for governed assessment |
| `proposed` | Submitted for assessment |
| `reviewed` | Evaluated by an authorized Human reviewer |
| `approved` | Granted authoritative standing by an authorized Human process |
| `disputed` | Authority is formally challenged or materially uncertain |
| `rejected` | Denied authoritative standing |

Initial authority standing shall be `draft`.

### 5.2.2 Permitted Transitions

| From | To |
|---|---|
| `draft` | `proposed` |
| `proposed` | `reviewed`, `disputed`, `rejected` |
| `reviewed` | `approved`, `proposed`, `disputed`, `rejected` |
| `approved` | `proposed`, `disputed` |
| `disputed` | `proposed`, `reviewed`, `rejected` |
| `rejected` | `draft` |

Any transition not listed is prohibited in Blueprint v1.0.

### 5.2.3 Transition Contract

Every authority transition shall:

- use an explicit aggregate operation;
- require the expected version;
- require an authenticated, authorized Human actor;
- record rationale and applicable Evidence;
- preserve prior standing in governed history;
- increment version exactly once;
- produce required Audit and Domain Event records atomically.

AI, automation, document presence, elapsed time, or relationship count shall not promote authority standing.

### 5.2.4 Human Authority

Only an authorized Human process may transition an object to `reviewed` or `approved`.

Reviewer competence, approver authority, and separation-of-duty requirements shall be validated by application policy before the aggregate accepts the transition.

`approved` applies only to the Engineering Object record within its defined scope. It does not automatically approve connected objects, relationships, documents, deliverables, or Projects.

### 5.2.5 Material Change

A material change to an object with `reviewed` or `approved` standing shall invalidate its previous standing.

The mutation shall transition authority to `proposed` within the same atomic operation unless a stricter policy requires rejection.

Non-material changes may preserve standing only when an approved policy explicitly classifies them as non-material.

### 5.2.6 Dispute and Rejection

A dispute shall prevent the object from being represented as unqualified authoritative knowledge.

Resolving a dispute requires reassessment through `proposed` or `reviewed`, or termination through `rejected`.

A rejected object may return only to `draft`, where correction must occur before resubmission.

### 5.2.7 Lifecycle Interaction

Lifecycle and authority transitions are evaluated independently.

A lifecycle change shall not automatically grant authority. Policies may require authority downgrade or reassessment when lifecycle changes, but no transition may imply Human approval without the required Human action.

### 5.2.8 Review Criteria

Section 5.2 is acceptable when:

- authority standing remains distinct from lifecycle and deliverable approval;
- only authorized Humans may establish reviewed or approved standing;
- material change invalidates prior standing;
- disputed knowledge cannot appear unqualified;
- rejected records require correction before resubmission;
- connected records receive no authority by implication.

# Section 6 — Responsibility, Governance, and Human Authority

## 6.1 Responsibility Model

Revision: 0

Every Engineering Object shall preserve explicit, accountable Human responsibility.

Blueprint v1.0 stores two aggregate responsibility roles:

| Role | Requirement | Mutability |
|---|---:|---|
| Creator | Mandatory | Immutable |
| Steward | Mandatory | Governed transfer only |

Other roles may participate through authorization, review, Audit, or connected governance records without becoming aggregate-owned state.

### 6.1.1 Creator

The Creator is the authenticated Human accountable for establishing the Engineering Object record.

Creator identity shall:

- be recorded at creation;
- match the authorized creation context;
- remain immutable;
- remain preserved after withdrawal, supersession, or retirement.

Delegated execution shall not replace the accountable Human with an AI or anonymous actor.

### 6.1.2 Steward

The Steward is the authenticated Human currently accountable for maintaining aggregate integrity.

The Steward shall:

- be valid within the applicable scope;
- be authorized for the object’s discipline and Workspace;
- remain identifiable throughout the object lifecycle;
- not gain formal approval authority solely through stewardship.

Creator and Steward may be the same Human when policy permits.

### 6.1.3 Stewardship Transfer

Stewardship transfer shall:

- use an explicit aggregate operation;
- identify the authorized initiating Human;
- validate the new Steward;
- require the current expected version;
- preserve prior stewardship in Audit history;
- increment aggregate version exactly once;
- emit the required Domain Event atomically.

Transfer shall not alter identity, scope, classification, lifecycle, or authority standing unless a separate approved operation requires it.

### 6.1.4 Participating Roles

The following roles may contribute to governance without becoming stored aggregate responsibility in Blueprint v1.0:

- owner;
- discipline owner;
- reviewer;
- approver;
- assignee;
- source authority.

Their authority shall come from approved policy and scope, not from self-declaration or aggregate field assignment.

### 6.1.5 Prohibited Responsibility

The following shall not hold accountable Engineering Object roles:

- AI models or agents;
- anonymous actors;
- unauthenticated users;
- shared credentials;
- external systems;
- background jobs.

Automation may execute an authorized workflow only when the accountable Human and initiating context remain traceable.

### 6.1.6 Responsibility Continuity

An Engineering Object shall never be left without a valid Steward.

Loss of Steward eligibility shall trigger a governed reassignment process. It shall not:

- erase prior responsibility;
- assign AI automatically;
- select an arbitrary replacement;
- physically delete the object;
- silently change authority standing.

### 6.1.7 Review Criteria

Section 6.1 is acceptable when:

- Creator and Steward are mandatory;
- Creator remains immutable;
- Steward changes only through governed transfer;
- stewardship does not imply approval authority;
- participating roles remain policy-governed;
- AI, anonymous actors, and technical processes cannot hold accountable roles;
- every mutation remains attributable to an authenticated Human.

## 6.2 Human Authority Boundary

Revision: 0

Engineering judgment, review, approval, dispute resolution, and accountability remain Human responsibilities.

### 6.2.1 Authority Sources

Permission to act shall derive from approved policy evaluated against:

- authenticated Human identity;
- Organization, Project, and Workspace scope;
- assigned role;
- engineering discipline;
- operation type;
- current aggregate state;
- required competence or approval authority.

Possession of aggregate data does not grant authority to mutate it.

### 6.2.2 Separation of Concepts

The architecture shall keep these concepts distinct:

| Concept | Meaning |
|---|---|
| Authentication | Confirms actor identity |
| Authorization | Permits a specific operation |
| Responsibility | Records accountable association |
| Review | Records governed Human evaluation |
| Approval | Records an authorized Human decision |
| Authority standing | Represents governance strength of the object record |

No concept shall automatically imply another.

### 6.2.3 Human Decision Requirement

The following require an authorized Human decision:

- establishing `reviewed` or `approved` authority standing;
- resolving a dispute;
- accepting material reclassification;
- authorizing lifecycle activation, supersession, or retirement;
- transferring stewardship;
- accepting an engineering-significant AI recommendation;
- overriding a governed validation or policy, where override is permitted.

Each decision shall preserve actor, time, scope, rationale, and applicable Evidence.

### 6.2.4 AI Boundary

AI may:

- recommend;
- classify provisionally;
- identify inconsistencies;
- summarize Evidence;
- suggest transitions;
- explain likely impact.

AI shall not:

- hold an accountable role;
- authorize an operation;
- approve engineering knowledge;
- resolve disputes;
- perform an unreviewed authoritative mutation;
- conceal uncertainty or Human provenance.

AI-originated proposals shall remain identifiable after Human review.

### 6.2.5 Automation Boundary

Automation may execute deterministic workflow steps only when:

- an authorized Human action or approved policy initiated the workflow;
- the accountable Human remains traceable;
- all aggregate invariants are enforced;
- automation cannot create Human approval by inference;
- failure leaves authoritative state unchanged.

Technical execution identity shall be recorded separately from accountable Human identity when both are relevant.

### 6.2.6 Separation of Duties

Policy may require different Humans for creation, stewardship, review, or approval.

Where separation of duties applies:

- self-approval shall be rejected;
- role eligibility shall be validated before mutation;
- reassignment shall not bypass the restriction;
- emergency override requires explicit authority and enhanced Audit.

Blueprint v1.0 does not mandate universal separation of duties; it preserves the enforcement boundary.

### 6.2.7 Review Criteria

Section 6.2 is acceptable when:

- authentication, authorization, responsibility, review, approval, and authority standing remain distinct;
- defined engineering decisions require Human authority;
- AI remains advisory;
- automation cannot manufacture approval;
- separation-of-duty policy can be enforced without changing the aggregate;
- accountable and technical actors remain traceable.

# Section 7 — Commands, Mutation Rules, and Domain Events

## 7.1 Command Contract

Revision: 0

A command expresses an authorized request to create or change one `EngineeringObject`. It is an intent, not authoritative state or evidence that a change occurred.

### 7.1.1 Command Envelope

Every command shall provide:

- command type;
- target Engineering Object UUID, except creation;
- authenticated accountable Human actor;
- authorization context;
- expected aggregate version, except creation;
- non-empty rationale;
- correlation identifier;
- idempotency identifier;
- operation-specific values;
- Evidence references when required.

Missing or invalid command context shall cause rejection before mutation.

### 7.1.2 Blueprint v1.0 Commands

The aggregate contract permits:

- `CreateEngineeringObject`;
- `ReclassifyEngineeringObject`;
- `TransitionEngineeringObjectLifecycle`;
- `TransitionEngineeringObjectAuthority`;
- `TransferEngineeringObjectSteward`.

Additional commands require Blueprint or approved extension review.

Generic field-update commands are prohibited.

### 7.1.3 Command Handling

Command handling shall:

1. authenticate the accountable Human;
2. authorize the requested operation;
3. load required referenced state;
4. load or create the aggregate;
5. validate the expected version;
6. invoke one explicit aggregate operation;
7. validate resulting invariants;
8. persist state, Audit, and event obligations atomically;
9. return an authorized result.

Transport adapters and repositories shall not contain command policy or domain transition logic.

### 7.1.4 Idempotency

Repeated delivery of the same idempotency identifier within the same command scope shall not apply the mutation more than once.

A repeated command with conflicting content shall be rejected.

Idempotency shall not bypass optimistic concurrency or authorization.

### 7.1.5 Rejection

A command shall be rejected when:

- authentication or authorization fails;
- the target is unavailable within authorized scope;
- expected version is stale;
- requested transition is prohibited;
- required rationale or Evidence is missing;
- scope or classification validation fails;
- an aggregate invariant would be violated;
- idempotency content conflicts.

Rejection shall leave aggregate state unchanged and preserve required attempt-level Audit evidence.

### 7.1.6 Command Boundary

A command shall target one EngineeringObject aggregate.

Cross-aggregate prerequisites may be validated by the application service, but the command shall not directly mutate:

- Engineering Identifiers;
- Engineering Relationships;
- Engineering Context;
- Evidence;
- Project;
- Workspace;
- User records.

Multi-aggregate workflows require explicit orchestration and separate aggregate commands.

### 7.1.7 Review Criteria

Section 7.1 is acceptable when:

- commands represent intent rather than completed facts;
- the command set is explicit and bounded;
- generic field updates are prohibited;
- authorization and concurrency precede mutation;
- idempotency prevents duplicate application;
- one command targets one aggregate;
- adapters and repositories cannot perform domain mutations directly.

## 7.2 Mutation Rules

Revision: 0

All aggregate changes shall occur through the commands approved in Section 7.1.

### 7.2.1 Mutation Matrix

| Command | Permitted aggregate change |
|---|---|
| `CreateEngineeringObject` | Establish initial aggregate state |
| `ReclassifyEngineeringObject` | Change approved classification values |
| `TransitionEngineeringObjectLifecycle` | Apply one permitted lifecycle transition |
| `TransitionEngineeringObjectAuthority` | Apply one permitted authority transition |
| `TransferEngineeringObjectSteward` | Replace the current Steward |

No command may alter immutable identity, Creator, or creation timestamp.

### 7.2.2 Mutation Sequence

A mutation shall:

1. validate command context;
2. confirm current expected version;
3. validate operation-specific policy;
4. calculate proposed state;
5. enforce aggregate invariants;
6. record required Domain Events;
7. increment version once;
8. set modification time;
9. commit state, Audit, and event obligations atomically.

Failure at any step shall leave authoritative state unchanged.

### 7.2.3 Creation

Creation shall:

- establish all mandatory initial state;
- set lifecycle to `proposed`;
- set authority standing to `draft`;
- set optimistic version to `1`;
- assign Creator and Steward;
- set creation and modification timestamps consistently.

Creation shall fail as one unit. Partial aggregate creation is prohibited.

### 7.2.4 Reclassification

Reclassification shall:

- validate the complete target classification;
- preserve UUID and scope;
- record the prior and resulting classification;
- require rationale and applicable Evidence;
- reassess authority standing.

A material reclassification of a `reviewed` or `approved` object shall transition authority standing to `proposed` atomically.

### 7.2.5 Lifecycle and Authority Mutation

Lifecycle and authority commands shall use only the transitions approved in Section 5.

A command may not use one state machine to bypass the other. Any policy-required companion change shall be explicit, validated, and atomic.

### 7.2.6 Stewardship Mutation

Stewardship transfer shall preserve Creator and prior responsibility history.

The new Steward shall be valid and authorized before the aggregate changes.

### 7.2.7 No-Op Mutation

A command that produces no state change shall not:

- increment version;
- update modification time;
- emit a domain-change event;
- report a successful mutation.

An exact idempotent retry shall return the recorded prior outcome without reapplying it.

### 7.2.8 Compound Mutation

One command may change multiple aggregate-owned values only when those changes are required to preserve an approved invariant.

Incidental or unrelated changes shall use separate commands.

Required companion changes shall share one version increment, Audit transaction, and event set.

### 7.2.9 Time and Determinism

The aggregate shall receive time through an approved clock contract.

Given the same current state and validated command context, mutation decisions shall be deterministic. Infrastructure state, AI output, and wall-clock access shall not create hidden transition behavior.

### 7.2.10 Review Criteria

Section 7.2 is acceptable when:

- each command has a bounded mutation purpose;
- immutable state cannot change;
- creation is atomic;
- material reclassification triggers authority reassessment;
- no-op commands do not create false history;
- companion changes occur only to preserve invariants;
- one successful command produces one version increment.

## 7.3 Domain Event Contract

Revision: 0

A Domain Event records a committed Engineering Object fact. It does not authorize mutation or replace Audit.

### 7.3.1 Event Types

Blueprint v1.0 defines:

- `EngineeringObjectCreated`;
- `EngineeringObjectReclassified`;
- `EngineeringObjectLifecycleTransitioned`;
- `EngineeringObjectAuthorityTransitioned`;
- `EngineeringObjectStewardTransferred`.

A compound mutation shall emit each event required to describe its accepted domain facts.

### 7.3.2 Event Envelope

Every event shall include:

- immutable event UUID;
- event type;
- event schema version;
- Engineering Object UUID;
- resulting aggregate version;
- occurrence timestamp;
- accountable Human actor;
- correlation identifier;
- causation identifier;
- applicable scope metadata;
- operation-specific payload.

Payload shall contain only the minimum information required to represent the change.

### 7.3.3 Event Production

Events shall:

- originate from a successful aggregate operation;
- describe past-tense facts;
- be immutable;
- use the same transaction as aggregate state and required Audit recording;
- become publishable only after commit;
- preserve per-aggregate version order.

Rejected, failed, and no-op commands shall not produce domain-change events.

### 7.3.4 Delivery

Event publication shall support at-least-once delivery.

Consumers shall:

- process events idempotently;
- tolerate redelivery;
- detect unsupported schema versions;
- avoid assuming global ordering;
- use aggregate UUID and version for per-object ordering;
- never mutate the source aggregate directly.

Publication failure after commit shall be recoverable without repeating the aggregate mutation.

### 7.3.5 Security Boundary

Event disclosure shall follow the Engineering Object’s authorization and confidentiality policy.

Events shall not expose:

- unauthorized scope information;
- unnecessary personal information;
- confidential Evidence content;
- secrets or credentials;
- hidden aggregate internals.

Event transport does not grant consumer authorization.

### 7.3.6 Evolution

Event schemas shall be versioned and backward-compatible for supported consumers.

Breaking semantic changes require:

- a new event schema version or event type;
- consumer impact review;
- migration or compatibility strategy;
- Architecture Review approval.

Published event history shall not be rewritten.

### 7.3.7 Audit Distinction

Domain Events communicate accepted domain facts.

Audit records preserve accountability for attempted and completed operations, including rejected attempts where required.

One shall not be reconstructed or treated as a substitute for the other.

### 7.3.8 Review Criteria

Section 7.3 is acceptable when:

- events represent committed past-tense facts;
- event and aggregate versions remain correlated;
- atomic recording prevents lost events;
- consumers support idempotent at-least-once delivery;
- rejected operations emit no domain-change events;
- event disclosure remains authorized;
- Domain Events and Audit remain distinct.

# Section 8 — Engineering Knowledge Graph Integration Boundaries

## 8.1 Engineering Object Graph Participation

Revision: 0

An Engineering Object is a stable node identity in the Engineering Knowledge Graph. Graph participation does not expand the aggregate boundary.

### 8.1.1 Node Identity

The graph shall reference an Engineering Object only by its immutable UUID.

Tags, labels, document numbers, and external identifiers may support discovery but shall not become graph node identity.

### 8.1.2 Connectivity Ownership

`EngineeringObject` shall not own adjacency lists or embedded graph edges.

Connectivity belongs to governed Engineering Relationship records that preserve:

- independent identity;
- explicit source and target UUIDs;
- direction;
- engineering meaning;
- scope;
- lifecycle;
- authority;
- responsibility;
- version.

Creating or removing a Relationship shall not directly mutate either connected Engineering Object.

### 8.1.3 Reference Validation

Before accepting an Engineering Relationship, the relationship boundary shall validate that each referenced Engineering Object:

- exists;
- is visible to the accountable actor;
- is within a permitted compatible scope;
- is in a lifecycle state allowed by relationship policy;
- satisfies required classification constraints.

This validation shall not transfer Engineering Object ownership or authority to the Relationship aggregate.

### 8.1.4 Graph Meaning

Graph meaning shall come from governed directional Relationships, not inferred proximity or co-occurrence.

Reverse navigation, graph neighborhoods, and path results are derived views. They shall not create additional authoritative Relationships.

### 8.1.5 Lifecycle and Authority Effects

Engineering Object lifecycle and authority standing shall qualify graph use.

Graph consumers shall not present:

- withdrawn, superseded, or retired objects as unqualified current knowledge;
- disputed or rejected objects as approved knowledge;
- connected objects as sharing lifecycle or authority standing.

A change in object standing does not silently rewrite connected Relationships. Required relationship reassessment shall occur through separate governed operations.

### 8.1.6 Consistency Boundary

A mutation to one Engineering Object shall not require a graph-wide transaction.

Cross-aggregate workflows shall use explicit orchestration, version-aware validation, and recoverable follow-up actions where immediate atomicity is unnecessary.

No graph consumer may bypass the EngineeringObject command boundary.

### 8.1.7 Persistence Direction

PostgreSQL remains the authoritative store for Version 1.

Graph projections or future graph technologies may optimize traversal but shall:

- preserve Engineering Object UUIDs;
- remain reconstructable;
- remain non-authoritative;
- enforce authorization before disclosure;
- require a separate architectural decision before becoming a system of record.

### 8.1.8 Review Criteria

Section 8.1 is acceptable when:

- immutable UUID is the graph node identity;
- Relationships own connectivity;
- graph participation does not enlarge the aggregate;
- derived traversal creates no authoritative facts;
- lifecycle and authority qualify graph interpretation;
- object mutation requires no graph-wide transaction;
- PostgreSQL remains authoritative.

## 8.2 Adjacent Knowledge Integration

Revision: 0

Engineering Identifiers, Engineering Context, and Evidence integrate through stable Engineering Object UUID references. They remain outside the aggregate boundary.

### 8.2.1 Engineering Identifiers

Identifier records shall:

- reference exactly one Engineering Object UUID;
- preserve identifier kind, normalized value, display value, issuing scope, lifecycle, and standing;
- enforce uniqueness within the approved identifier scope;
- preserve history when replaced or superseded;
- never replace internal object identity.

Changing an identifier shall not increment the Engineering Object version unless aggregate-owned state also changes.

### 8.2.2 Engineering Context

Engineering Context may include or reference an Engineering Object without copying its authoritative state.

Context membership shall:

- reference the Engineering Object UUID;
- preserve Context-owned scope, purpose, lifecycle, authority, and responsibility;
- validate access to both records;
- avoid transferring authority or approval between them.

Removing Context membership shall not delete or mutate the Engineering Object.

### 8.2.3 Evidence

Evidence references shall identify:

- Evidence identity;
- source revision;
- source standing;
- applicable scope;
- effective date when material;
- supported engineering fact.

Evidence content shall remain owned by its authoritative source.

Missing, withdrawn, superseded, unauthorized, or out-of-scope Evidence shall not be presented as current authoritative support.

### 8.2.4 Authority Isolation

Authority shall not propagate by connection.

An approved Engineering Object does not automatically approve:

- its identifiers;
- connected Context;
- supporting Evidence;
- connected Relationships;
- other Engineering Objects.

The reverse is also prohibited.

### 8.2.5 Update Propagation

Changes in adjacent records may create reassessment work but shall not silently mutate the Engineering Object.

Any required response shall use:

- an explicit command;
- current-version validation;
- authorized Human responsibility;
- applicable Audit and Domain Events.

### 8.2.6 Failure Isolation

Failure to update an adjacent projection or integration shall not corrupt committed Engineering Object state.

Recoverable integration work shall retain correlation, retry safely, and remain visible to operational monitoring.

### 8.2.7 Review Criteria

Section 8.2 is acceptable when:

- adjacent knowledge references immutable object identity;
- identifiers cannot replace UUID identity;
- Context membership does not duplicate aggregate state;
- Evidence retains source ownership and revision;
- authority never propagates by association;
- adjacent changes cannot silently mutate the aggregate;
- integration failures remain recoverable and isolated.

# Section 9 — Clean Architecture Ports and Dependency Rules

## 9.1 Dependency Direction

Revision: 0

EngineeringObject behavior shall follow the Clean Architecture dependency rule: outer layers may depend on inner contracts; inner layers shall not depend on outer implementations.

### 9.1.1 Logical Layers

| Layer | Responsibility |
|---|---|
| Domain | Aggregate state, invariants, transitions, Domain Events |
| Application | Command orchestration, authorization coordination, transactions |
| Ports | Repository, Audit, event publication, clock, and policy contracts |
| Infrastructure | PostgreSQL, SQLAlchemy, messaging, identity, and external integrations |
| Transport | HTTP, jobs, importers, and user-interface adapters |

This is a logical separation. Blueprint v1.0 does not require unnecessary duplicate models or services.

### 9.1.2 Dependency Rules

- Domain depends only on domain contracts and controlled vocabulary.
- Application depends on Domain and Ports.
- Infrastructure implements Ports.
- Transport invokes Application contracts.
- Domain and Application shall not depend on FastAPI, SQLAlchemy sessions, HTTP, message brokers, or AI providers.
- Infrastructure shall not redefine domain policy.
- Transport shall not contain aggregate mutation logic.

### 9.1.3 Domain Isolation

The aggregate shall not:

- open transactions;
- query repositories;
- evaluate transport data;
- read system time directly;
- publish events directly;
- call AI or external services;
- inspect database-specific state.

Required context shall be supplied through explicit application and port contracts.

### 9.1.4 Application Boundary

The application layer shall coordinate:

- authentication and authorization results;
- reference validation;
- aggregate loading;
- command execution;
- transaction completion;
- Audit recording;
- durable event recording;
- authorized response mapping.

It shall not bypass aggregate methods or duplicate aggregate invariants.

### 9.1.5 Adapter Boundary

Adapters shall translate external representations into approved application contracts.

Adapters may validate syntax and transport requirements but shall not decide:

- lifecycle transitions;
- authority standing;
- reclassification validity;
- stewardship eligibility;
- engineering approval.

### 9.1.6 Persistence Pragmatism

The implementation may use SQLAlchemy-compatible mappings without introducing a second domain model when one model can preserve the dependency rules and aggregate encapsulation.

Framework convenience shall not permit direct mutation outside approved application and aggregate boundaries.

### 9.1.7 Review Criteria

Section 9.1 is acceptable when:

- dependencies point toward domain policy;
- the Domain remains framework-independent;
- Application owns orchestration;
- Infrastructure implements explicit Ports;
- adapters perform translation rather than engineering decisions;
- Clean Architecture does not create unnecessary MVP duplication;
- ORM convenience cannot bypass aggregate rules.

## 9.2 Required Ports

Revision: 0

Application workflows shall depend on explicit inward-owned Ports. Ports define required capabilities, not infrastructure technology.

### 9.2.1 MVP Port Set

| Port | Required capability |
|---|---|
| Engineering Object Repository | Load, add, and persist one aggregate |
| Unit of Work | Commit or roll back one mutation outcome |
| Authorization Policy | Decide whether an actor may perform an operation |
| Reference Validator | Validate required external identities and scope coherence |
| Audit Recorder | Record accountable attempts and outcomes |
| Domain Event Recorder | Durably record events for post-commit publication |
| Idempotency Store | Prevent duplicate command application |
| Clock | Supply controlled UTC time |
| UUID Generator | Supply new immutable identities |

Additional Ports require a demonstrated use case.

### 9.2.2 Repository Port

The repository shall:

- resolve aggregates by immutable UUID and authorized scope;
- return complete aggregate state;
- distinguish not-found from version conflict without leaking unauthorized existence;
- add new aggregates;
- persist accepted aggregate changes;
- enforce expected-version writes.

The repository shall not:

- decide domain transitions;
- authorize operations;
- perform generic field updates;
- commit transactions independently;
- publish Domain Events.

### 9.2.3 Unit of Work Port

The Unit of Work shall coordinate atomic persistence of:

- aggregate state;
- required Audit outcome;
- idempotency result;
- durable Domain Events.

Commit failure shall leave no partial authoritative outcome.

### 9.2.4 Policy and Reference Ports

Authorization Policy shall return an explicit decision for the actor, operation, scope, and current state.

Reference Validator shall confirm required external facts without transferring their ownership into the aggregate.

Neither Port may mutate the Engineering Object.

### 9.2.5 Audit and Event Ports

Audit Recorder and Domain Event Recorder shall remain separate contracts even when they share one transaction.

- Audit records attempts and accountability.
- Domain Events record committed domain facts.
- Event publication occurs only after successful commit.

### 9.2.6 Deterministic Utility Ports

Clock and UUID Generator shall be supplied to the application boundary.

They shall support deterministic testing and prevent hidden infrastructure access from the Domain.

### 9.2.7 Port Failure Contract

Port failures shall:

- use explicit typed outcomes;
- preserve transaction atomicity;
- avoid exposing infrastructure-specific errors beyond the adapter boundary;
- remain distinguishable from domain rejection;
- support safe retry only where idempotency permits.

### 9.2.8 Review Criteria

Section 9.2 is acceptable when:

- the MVP Port set is minimal and explicit;
- repositories remain persistence-only;
- one Unit of Work preserves mutation atomicity;
- policy and reference validation remain external to the aggregate;
- Audit and Domain Events remain distinct;
- time and identity generation are deterministic;
- infrastructure failures cannot leak into domain semantics.

# Section 10 — Persistence and Transaction Contract

## 10.1 Relational Persistence Contract

Revision: 0

PostgreSQL shall persist Engineering Object authoritative state in a dedicated `engineering_objects` relation.

### 10.1.1 Persisted State

The relation shall persist:

- immutable Engineering Object UUID;
- approved scope references;
- approved classification;
- lifecycle state;
- authority standing;
- optimistic version;
- Creator identity;
- Steward identity;
- creation timestamp;
- modification timestamp.

Core aggregate state shall use explicit typed columns, not an unvalidated JSON document.

### 10.1.2 Identity and References

- Engineering Object UUID is the primary key.
- Organization UUID is mandatory and explicit.
- Customer reference is nullable.
- Project and Workspace references are mandatory.
- Creator and Steward references are mandatory.
- Existing entities shall use compatible key types and foreign keys.
- Organization UUID shall remain non-null without a foreign key until an approved Organization aggregate exists.

External identifiers shall not be stored as the primary key or embedded into immutable identity.

### 10.1.3 Controlled Values

Family, discipline, lifecycle, and authority standing shall use approved controlled contracts.

Object type and subtype shall use the approved governed vocabulary.

Persistence shall reject unknown, malformed, or incompatible values before they become authoritative state.

### 10.1.4 Database Constraints

The database shall enforce where technically applicable:

- non-null mandatory state;
- UUID primary-key uniqueness;
- referential integrity;
- positive optimistic version;
- valid controlled values;
- timestamp presence;
- subtype nullability;
- compatible physical key types.

Domain and application validation remain mandatory even when equivalent database constraints exist.

### 10.1.5 Immutability

UUID, Creator, and creation timestamp are immutable.

Ordinary persistence operations shall not:

- replace these values;
- physically delete authoritative rows;
- bypass optimistic concurrency;
- update aggregate fields outside an approved mutation.

Corrective data repair requires a separately authorized workflow.

### 10.1.6 Timestamps

Timestamps shall:

- use the existing SATCO UTC convention;
- be timezone-aware;
- be assigned through the approved Clock boundary;
- remain consistent with the committed aggregate version.

Database defaults may protect integrity but shall not create conflicting domain time.

### 10.1.7 Index Direction

Indexes shall support authorized MVP access by:

- immutable UUID;
- Organization and Project;
- Project and Workspace;
- classification;
- lifecycle and authority standing where required by approved queries.

Indexes shall not substitute for authorization or create a second identity contract.

### 10.1.8 Metadata Registration

The persistence model shall be registered consistently with SATCO metadata and migration conventions.

Model registration alone shall not authorize migration creation or execution.

### 10.1.9 Review Criteria

Section 10.1 is acceptable when:

- one dedicated relation preserves aggregate state;
- UUID remains the sole primary identity;
- mandatory references and responsibility are constrained;
- controlled values cannot degrade into arbitrary storage;
- optimistic version is positive;
- immutable fields and authoritative history are protected;
- persistence remains compatible with existing SATCO conventions.

## 10.2 Transaction and Concurrency Contract

Revision: 0

One successful Engineering Object command shall produce one atomic transaction outcome.

### 10.2.1 Successful Transaction

The Unit of Work shall atomically persist:

- aggregate creation or state change;
- one optimistic version result;
- successful-operation Audit record;
- idempotency outcome;
- durable Domain Events.

Failure of any required write shall roll back the entire transaction.

### 10.2.2 Optimistic Concurrency

Mutation commands shall provide the expected aggregate version.

Persistence shall apply a compare-and-change rule equivalent to:

- target UUID matches;
- persisted version equals expected version;
- resulting version equals expected version plus one.

No matching current version means the mutation did not occur.

### 10.2.3 Conflict Handling

A version conflict shall:

- return an explicit concurrency outcome;
- leave persisted state unchanged;
- emit no domain-change event;
- not overwrite newer state;
- not be retried automatically against refreshed state.

The caller may reload, reassess, and submit a new command with a new idempotency identifier.

Conflict responses shall not disclose an object outside authorized scope.

### 10.2.4 Creation Conflict

Creation shall fail if the UUID already exists.

External-identifier conflicts are governed by the separate Identifier contract and shall not redefine Engineering Object identity.

### 10.2.5 Rejected and Failed Attempts

A domain or authorization rejection shall not open or commit an aggregate mutation transaction.

Required attempt-level Audit may be recorded independently.

If infrastructure failure rolls back a transaction, a failure Audit record may be written afterward through a separate recoverable operation. It shall not claim that mutation succeeded.

### 10.2.6 Event Publication

Durable Domain Events shall be recorded in the successful transaction and published after commit.

Publication failure shall:

- not roll back committed aggregate state;
- retain the event for retry;
- not reapply the command;
- remain operationally observable.

### 10.2.7 Transaction Boundary

A normal command transaction shall contain one EngineeringObject aggregate.

Referenced aggregates may be validated but shall not be mutated in the same command transaction.

Distributed transactions are not required for Blueprint v1.0.

### 10.2.8 Isolation

The selected database isolation and write strategy shall prevent:

- lost updates;
- partial state;
- duplicate command application;
- events without committed state;
- successful Audit without committed state.

Correctness shall not depend on process-local locks.

### 10.2.9 Review Criteria

Section 10.2 is acceptable when:

- aggregate, Audit, idempotency, and events commit atomically;
- expected-version writes prevent lost updates;
- conflicts never overwrite current state;
- retries require explicit reassessment;
- failed transactions cannot appear successful;
- event publication is recoverable after commit;
- one transaction remains bounded to one aggregate.

# Section 11 — Authorization, Confidentiality, and Audit

## 11.1 Authorization Contract

Revision: 0

Every Engineering Object operation shall be explicitly authorized. Default outcome is denial.

### 11.1.1 Authorization Inputs

Authorization shall evaluate:

- authenticated Human identity;
- requested operation;
- Organization, Project, and Workspace scope;
- Customer scope when applicable;
- actor roles and discipline;
- current lifecycle and authority standing;
- target state when a mutation is requested;
- applicable separation-of-duty policy.

Creation shall be evaluated against the proposed scope and classification.

### 11.1.2 Authorization Order

Authorization shall occur:

1. before object disclosure;
2. before reference resolution that could reveal protected existence;
3. before aggregate mutation;
4. again when a target-state change alters applicable policy.

Domain validation shall not be used to leak unauthorized information.

### 11.1.3 Operation-Specific Decisions

Authorization shall be specific to the requested action.

Permission to read does not imply permission to:

- create;
- reclassify;
- transition lifecycle;
- transition authority;
- transfer stewardship;
- inspect Audit history.

Permission for one Engineering Object does not imply permission for connected objects.

### 11.1.4 Scope Enforcement

Repository and application boundaries shall enforce compatible authorized scope.

Cross-Organization mutation is prohibited.

Cross-Project or cross-Workspace access requires an explicit approved policy; graph connectivity alone shall never grant access.

### 11.1.5 Decision Contract

The Authorization Policy Port shall return:

- allow or deny;
- applicable policy reference;
- decision context required for Audit;
- any required Human role or separation-of-duty condition.

The aggregate shall receive only validated authorization context and shall not query identity infrastructure.

### 11.1.6 Denial Behavior

Authorization denial shall:

- leave aggregate state unchanged;
- emit no Domain Event;
- create required security Audit evidence;
- avoid confirming protected object existence;
- return a stable application-level outcome.

### 11.1.7 Policy Change

Authorization is evaluated at operation time.

A previous decision, cached representation, Steward assignment, or prior access shall not guarantee future authorization.

### 11.1.8 Emergency Override

Emergency override is permitted only when an approved governance policy defines:

- eligible Human authority;
- allowed operations;
- required rationale;
- time limitation;
- enhanced Audit;
- mandatory follow-up review.

No implicit administrator bypass is permitted.

### 11.1.9 Review Criteria

Section 11.1 is acceptable when:

- authorization is deny-by-default;
- disclosure is authorized before existence is revealed;
- decisions are operation- and scope-specific;
- graph connections grant no transitive access;
- policy remains outside the aggregate;
- denial produces no mutation or Domain Event;
- emergency override is explicit and auditable.

## 11.2 Confidentiality Contract

Revision: 0

Confidentiality shall be enforced before Engineering Object disclosure, traversal, export, or mutation.

Blueprint v1.0 does not add a separate aggregate-owned confidentiality field. Effective confidentiality derives from approved scope and authorization policy.

### 11.2.1 Controlled Levels

Policy may use the approved levels:

- `organization`;
- `customer`;
- `project`;
- `workspace`;
- `restricted`.

These levels describe disclosure boundaries and shall not imply lifecycle, authority, or approval.

### 11.2.2 Effective Confidentiality

The application boundary shall determine effective confidentiality from:

- Engineering Object scope;
- actor authorization;
- Customer applicability;
- Workspace restrictions;
- connected source restrictions when their information is requested;
- explicit restricted-access policy.

When multiple restrictions apply, the most restrictive applicable rule governs.

### 11.2.3 Disclosure Rules

Confidentiality shall apply to:

- aggregate representations;
- object-existence responses;
- search and graph results;
- Domain Events;
- Audit access;
- exports;
- logs and diagnostics;
- derived or AI-generated outputs.

Derived information shall retain restrictions from its authoritative sources.

### 11.2.4 Cross-Scope Use

Information shall not cross Organization, Customer, Project, or Workspace boundaries merely because:

- objects are similar;
- identifiers match;
- a Relationship exists;
- a user accessed related information elsewhere;
- AI considers the information relevant.

Cross-scope use requires explicit policy and authorization.

### 11.2.5 Redaction

Redaction may remove protected fields only when the remaining representation is accurate and useful.

The system shall deny disclosure when redaction would:

- misstate engineering meaning;
- conceal material uncertainty;
- imply unsupported authority;
- reveal protected existence indirectly.

### 11.2.6 Restricted Information

`restricted` information requires explicit authorization beyond ordinary scope membership.

Restricted content shall not appear in general search, graph traversal, logs, events, or AI context unless the consuming operation is separately authorized.

### 11.2.7 Future Per-Object Classification

A future requirement for independently persisted per-object confidentiality requires a Blueprint revision and Architecture Review.

Such a revision shall define ownership, mutation, downgrade controls, Audit, migration, and interaction with scope policy.

### 11.2.8 Review Criteria

Section 11.2 is acceptable when:

- confidentiality is enforced without expanding current aggregate state;
- approved levels remain available to policy;
- the most restrictive applicable rule governs;
- derived and AI outputs preserve source restrictions;
- graph connectivity grants no disclosure;
- redaction cannot distort engineering meaning;
- per-object confidentiality requires future explicit approval.

# Section 12 — Validation and Architecture Approval

Revision: 0

This section defines the final acceptance contract for EngineeringObject Blueprint v1.0.

## 12.1 Blueprint Validation

Architecture Review shall verify:

| Area | Required result |
|---|---|
| Aggregate boundary | One focused consistency boundary |
| Identity | Immutable UUID independent of external identifiers |
| Scope | Coherent Organization–Project–Workspace boundary |
| Classification | Controlled and internally compatible |
| State | Complete, encapsulated, and versioned |
| Lifecycle | Only approved transitions permitted |
| Authority | Human-governed and distinct from lifecycle |
| Responsibility | Immutable Creator and one governed Steward |
| Commands | Explicit, authorized, and aggregate-specific |
| Domain Events | Atomic, immutable, and post-commit publishable |
| EKG integration | References do not expand aggregate ownership |
| Dependencies | Domain remains framework-independent |
| Persistence | PostgreSQL constraints preserve aggregate validity |
| Concurrency | Expected-version writes prevent lost updates |
| Security | Authorization precedes disclosure and mutation |
| Confidentiality | Most restrictive applicable policy governs |
| Audit | Accountability remains distinct from Domain Events |

Any material failure blocks approval.

## 12.2 Architecture Conformance Evidence

The Architecture Review package shall include:

- the complete Blueprint;
- governing-document traceability;
- aggregate boundary review;
- lifecycle and authority transition review;
- command-to-event traceability;
- invariant-to-enforcement mapping;
- persistence constraint review;
- authorization and confidentiality review;
- transaction-failure analysis;
- deferred-scope confirmation;
- recorded Architecture Review notes and resolutions.

## 12.3 Implementation Validation Contract

A future implementation shall demonstrate:

- aggregate creation with valid initial state;
- rejection of invalid or incomplete state;
- immutable identity, Creator, and creation timestamp;
- controlled classification enforcement;
- permitted and prohibited state transitions;
- material-change authority reassessment;
- governed Steward transfer;
- optimistic concurrency conflict rejection;
- idempotent command handling;
- atomic state, Audit, idempotency, and event persistence;
- recoverable post-commit event publication;
- authorization before disclosure and mutation;
- confidentiality enforcement;
- metadata and database-constraint conformance;
- no direct mutation through repositories or adapters;
- full regression compatibility.

Validation evidence shall include focused tests, integration tests, migration checks when applicable, and Architecture Review of any deviation.

## 12.4 Deferred Scope

Blueprint v1.0 does not authorize:

- external identifier implementation;
- Engineering Relationship implementation;
- graph traversal algorithms;
- semantic or vector search;
- Engineering Digital Twin behavior;
- autonomous AI mutation;
- additional engineering domains;
- cross-Organization transfer;
- independently persisted per-object confidentiality;
- unrestricted reclassification;
- physical deletion of authoritative history.

Deferred capabilities require the approved Docs-First workflow.

## 12.5 Architecture Review Decision

The reviewer shall issue one verdict:

- `PASS`;
- `PASS WITH CONDITIONS`;
- `FAIL`.

The review shall record:

- findings;
- required corrections;
- accepted risks;
- deferred recommendations;
- approval authority;
- decision date.

`PASS WITH CONDITIONS` authorizes implementation only after all blocking conditions are closed.

## 12.6 Implementation Gate

Implementation may begin only when:

1. all Blueprint sections are approved;
2. the consolidated Blueprint is accepted as the architecture contract;
3. Architecture Review records `PASS`, or closes all blocking conditions;
4. Product Owner implementation approval is explicit;
5. the implementation PATCH remains within Blueprint v1.0 scope.

Blueprint approval does not authorize migration execution, Git operations, deployment, or scope expansion.

## 12.7 Change Control

After final approval, a material change to identity, scope, aggregate ownership, lifecycle, authority, responsibility, commands, events, persistence, security, or deferred scope requires:

- documented rationale;
- impact analysis;
- Blueprint revision;
- renewed Architecture Review;
- explicit approval before implementation.

Editorial corrections that do not change architectural meaning may follow normal documentation governance.

## 12.8 Final Acceptance Criteria

EngineeringObject Blueprint v1.0 is complete when:

- Sections 1–12 are approved;
- all Architecture Review notes are recorded;
- no unresolved contradiction remains;
- deferred scope is preserved;
- the final Architecture Review verdict is recorded;
- the official document is placed under `/docs` as the architecture contract.
