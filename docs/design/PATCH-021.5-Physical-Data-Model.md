# PATCH-021.5 Physical Data Model

## Status

Accepted for Implementation Planning

## Purpose

Translate the approved Engineering Knowledge Graph domain model into a
physical data-model direction suitable for PostgreSQL implementation.

This document defines persistence boundaries only.

It does not authorize production implementation.

## Approved Inputs

PATCH-021.5 builds on:

- PATCH-021.1 Engineering Object Model;
- PATCH-021.2 Engineering Relationship Vocabulary;
- PATCH-021.3 Engineering Context Model;
- PATCH-021.4 Engineering Knowledge Graph Rules;
- ADR-020 EKG Open Extension Principle.

## Storage Strategy

PostgreSQL shall remain the System of Record for Version 1.

The first EKG implementation shall not require a separate graph database.

Graph behavior shall be represented through governed relational entities,
directional relationships, indexed scope fields, and controlled traversal.

A future graph-storage technology may be evaluated only through a separate
architectural decision.

## Core Persistence Areas

Version 1 shall consider the following persistence areas:

- Engineering Object identity;
- Engineering Object classification;
- Engineering Object scope;
- Engineering Relationships;
- Engineering Context;
- Evidence references;
- Human responsibility;
- lifecycle state;
- optimistic versioning;
- Audit integration.

## Aggregate Direction

The preliminary aggregate boundaries are:

- Engineering Object Aggregate;
- Engineering Relationship Aggregate;
- Engineering Context Aggregate.

Evidence, responsibility, lifecycle, and version information shall belong to
the aggregate that governs the corresponding engineering fact.

Final aggregate contracts require separate detailed design approval.

## Primary Identity Strategy

Every primary EKG entity shall have:

- an internal immutable UUID;
- explicit Organization scope;
- explicit Project scope when applicable;
- a positive optimistic version;
- creation timestamp;
- last-modified timestamp;
- accountable creator;
- accountable current steward.

External identifiers such as tag number, loop number, cable number, panel
number, or Vendor reference shall not replace the internal UUID.

## Version-1 Boundary

PATCH-021.5 shall define only the physical data-model architecture.

It shall not implement:

- SQLAlchemy models;
- Alembic migrations;
- repositories;
- services;
- APIs;
- graph traversal;
- AI behavior;
- frontend behavior;
- Engineering Digital Twin behavior.

## Engineering Object Persistence

The Engineering Object Aggregate shall preserve:

- immutable internal UUID;
- Organization identity;
- Customer identity when applicable;
- Project identity;
- Workspace identity;
- object family;
- object type;
- discipline;
- controlled subtype;
- primary display label;
- external engineering identifiers;
- lifecycle state;
- authority standing;
- confidentiality;
- optimistic version;
- creator;
- steward;
- creation timestamp;
- modification timestamp.

External identifiers shall be stored separately from immutable identity.

A change to a tag number, loop number, cable number, panel number, or Vendor
reference shall not change the internal Engineering Object identity.

## Engineering Object Identifier Model

An Engineering Object may have multiple governed identifiers.

Candidate identifier kinds include:

- tag number;
- equipment number;
- loop number;
- cable number;
- panel number;
- feeder number;
- system identifier;
- subsystem identifier;
- Vendor reference;
- manufacturer model reference;
- controlled external key.

Identifier records shall preserve:

- identifier kind;
- normalized value;
- display value;
- issuing scope;
- effective standing;
- source Evidence;
- version;
- lifecycle.

Uniqueness shall be enforced within the approved scope for each identifier
kind.

## Engineering Relationship Persistence

The Engineering Relationship Aggregate shall preserve:

- immutable internal UUID;
- Organization identity;
- Project identity;
- Workspace identity;
- source Engineering Object UUID;
- target Engineering Object UUID;
- approved Relationship type;
- Relationship family;
- direction;
- engineering purpose;
- lifecycle state;
- authority standing;
- confidentiality;
- supporting Evidence;
- optimistic version;
- creator;
- steward;
- creation timestamp;
- modification timestamp.

Source and target shall remain explicit.

Reverse traversal shall be derived from the governed directional record and
shall not require a duplicate authoritative row.

## Relationship Integrity

The physical model shall reject:

- missing source;
- missing target;
- invalid Relationship type;
- unauthorized cross-Project scope;
- prohibited self-reference;
- duplicate current Relationship identity;
- stale-version mutation;
- deletion of authoritative history.

Relationship uniqueness shall include sufficient scope and meaning fields to
prevent accidental duplicate authoritative facts.

## Engineering Context Persistence

The Engineering Context Aggregate shall preserve:

- immutable internal UUID;
- Organization identity;
- Customer identity when applicable;
- Project identity;
- Workspace identity;
- discipline;
- Context type;
- engineering purpose;
- authority standing;
- lifecycle state;
- confidentiality;
- optimistic version;
- accountable owner;
- reviewer when required;
- approver when required;
- creation timestamp;
- modification timestamp.

Context membership shall connect governed Engineering Objects,
Relationships, Evidence, Requirements, and Decisions without duplicating their
authoritative identities.

## Evidence Reference Persistence

EKG aggregates shall reference governed Evidence without duplicating the
authoritative Evidence record.

An Evidence reference shall preserve:

- Evidence identity;
- Evidence type;
- source revision;
- source standing;
- Project scope;
- confidentiality;
- effective date;
- relationship to the supported fact.

Evidence replacement or supersession shall preserve historical references.

An Evidence reference shall not become authoritative when the referenced
source is missing, unauthorized, withdrawn, or outside the permitted scope.

## Responsibility Persistence

Accountable Human responsibility shall be represented explicitly.

Candidate responsibility roles include:

- creator;
- owner;
- steward;
- discipline owner;
- reviewer;
- approver;
- assignee;
- source authority.

The persistence model shall not assign accountable engineering roles to AI,
service accounts, or anonymous actors.

Responsibility history shall remain traceable after reassignment.

## Lifecycle Persistence

Lifecycle values shall use controlled finite vocabularies.

Lifecycle persistence shall preserve:

- current state;
- previous state;
- transition reason;
- responsible actor;
- transition time;
- supporting Evidence;
- expected version.

Withdrawal and supersession shall remain distinct from deletion.

Authoritative EKG records shall not be physically deleted through ordinary
application workflows.

## Optimistic Concurrency

Every mutable authoritative EKG aggregate shall contain a positive optimistic
version.

A mutation shall provide the expected current version.

The mutation shall succeed only when the stored version matches the expected
version.

A successful mutation shall increment the version exactly once.

A stale mutation shall fail without overwriting newer engineering knowledge.

## Audit Integration

Authoritative mutation and Audit creation shall occur within one transaction.

The Audit record shall preserve:

- actor identity;
- action;
- aggregate type;
- aggregate identity;
- previous version;
- resulting version;
- reason;
- scope;
- timestamp;
- outcome.

A successful mutation without successful Audit persistence is prohibited.

A failed mutation shall not produce a misleading successful Audit record.

## Confidentiality Persistence

Confidentiality shall be represented as governed data rather than UI-only
behavior.

The physical model shall support:

- Organization isolation;
- Customer isolation;
- Project isolation;
- Workspace isolation;
- discipline restrictions;
- restricted Evidence;
- protected external identifiers;
- least-privilege traversal.

Authorization filtering shall occur before disclosure, counting, pagination,
search, traversal, or AI retrieval.

## Proposed Relational Structures

Version 1 may use relational structures equivalent to:

- engineering_objects;
- engineering_object_identifiers;
- engineering_relationships;
- engineering_contexts;
- engineering_context_members;
- engineering_evidence_links;
- engineering_responsibilities.

Exact table names remain subject to detailed implementation design.

Shared Core entities such as Organizations, Customers, Projects, Workspaces,
Users, and Audit records shall be referenced rather than duplicated.

## Engineering Object Table Direction

The Engineering Object persistence structure shall include fields equivalent
to:

- id;
- organization_id;
- customer_id when applicable;
- project_id;
- workspace_id;
- object_family;
- object_type;
- discipline;
- subtype;
- display_label;
- lifecycle;
- authority_standing;
- confidentiality;
- version;
- created_by;
- steward_id;
- created_at;
- updated_at.

The physical implementation shall use explicit foreign keys and controlled
enums or governed lookup values where appropriate.

## Identifier Table Direction

Engineering Object identifiers shall use a separate structure containing
fields equivalent to:

- id;
- engineering_object_id;
- identifier_kind;
- normalized_value;
- display_value;
- issuing_scope;
- lifecycle;
- evidence_id when applicable;
- version;
- created_at;
- updated_at.

A scoped uniqueness constraint shall prevent duplicate current identifiers
where the approved identifier policy requires uniqueness.

## Relationship Table Direction

The Engineering Relationship persistence structure shall include fields
equivalent to:

- id;
- organization_id;
- project_id;
- workspace_id;
- source_object_id;
- target_object_id;
- relationship_family;
- relationship_type;
- engineering_purpose;
- lifecycle;
- authority_standing;
- confidentiality;
- version;
- created_by;
- steward_id;
- created_at;
- updated_at.

Source and target foreign keys shall reference governed Engineering Objects.

## Context Table Direction

The Engineering Context persistence structure shall include fields equivalent
to:

- id;
- organization_id;
- customer_id when applicable;
- project_id;
- workspace_id;
- discipline;
- context_type;
- engineering_purpose;
- lifecycle;
- authority_standing;
- confidentiality;
- version;
- owner_id;
- reviewer_id when required;
- approver_id when required;
- created_at;
- updated_at.

Context membership shall use explicit association records rather than
uncontrolled serialized lists.

## Index Strategy

Version-1 indexing shall support:

- scoped Engineering Object lookup;
- external identifier lookup;
- object-family and object-type filtering;
- discipline filtering;
- source Relationship traversal;
- target Relationship traversal;
- Relationship type filtering;
- Context membership lookup;
- lifecycle filtering;
- authority-standing filtering;
- confidentiality-aware retrieval;
- optimistic version mutation.

Index design shall be validated against actual query plans and measured
performance tests.

## Constraint Strategy

The physical model shall use database constraints where practical to enforce:

- required scope;
- positive versions;
- valid foreign keys;
- valid source and target;
- controlled lifecycle;
- controlled authority standing;
- required responsible actors;
- scoped identifier uniqueness;
- scoped current-Relationship uniqueness;
- timestamp integrity.

Application validation shall complement database constraints but shall not
replace critical database integrity.

## Repository Boundaries

Version 1 shall preserve separate repository boundaries for:

- Engineering Objects;
- Engineering Object Identifiers;
- Engineering Relationships;
- Engineering Contexts.

Repositories shall provide persistence operations only.

Repositories shall not own:

- authorization policy;
- Human approval;
- engineering validation;
- AI reasoning;
- cross-aggregate orchestration;
- Audit business decisions.

Services shall enforce use-case rules before invoking repositories.

## Service Transaction Boundary

Application services shall control transaction boundaries for authoritative
mutations.

A transaction may include:

- aggregate validation;
- optimistic-version verification;
- persistence mutation;
- Evidence linkage;
- responsibility update;
- lifecycle transition;
- Audit creation.

All authoritative effects shall commit or roll back together.

## Graph Traversal Strategy

Version-1 graph traversal shall use PostgreSQL queries over directional
Relationship records.

Initial traversal shall be bounded by:

- authorized Organization;
- authorized Project;
- authorized Workspace;
- approved Relationship families;
- maximum traversal depth;
- maximum result count;
- confidentiality filters.

Unlimited recursive traversal shall not be exposed through ordinary APIs.

A separate graph database shall not be introduced without measured evidence
that PostgreSQL is insufficient.

## Query and Pagination Rules

List and traversal queries shall support:

- deterministic ordering;
- bounded page size;
- stable pagination;
- authorization-aware totals;
- lifecycle filters;
- authority-standing filters;
- discipline filters;
- object-type filters;
- Relationship-type filters.

Counts and pagination metadata shall not disclose unauthorized records.

## Migration Strategy

The implementation phase shall introduce schema changes through Alembic.

Migration requirements shall include:

- deterministic revision chain;
- upgrade from the current head;
- downgrade to the previous approved revision;
- fresh-database upgrade;
- rollback and reapplication;
- constraint validation;
- index validation;
- existing-data safety;
- PostgreSQL compatibility.

Manual production schema mutation is prohibited.

## Test Strategy

Physical data-model implementation shall include tests for:

- schema creation;
- migration upgrade and downgrade;
- foreign-key integrity;
- scoped uniqueness;
- positive-version enforcement;
- stale-version rejection;
- lifecycle constraints;
- prohibited deletion;
- Audit atomicity;
- authorization-before-disclosure;
- bounded traversal;
- pagination;
- concurrent one-winner mutation;
- query instrumentation.

Tests shall verify actual database behavior rather than declared constants.

## Performance Direction

Version-1 performance validation shall measure:

- Engineering Object lookup;
- identifier lookup;
- outgoing Relationship traversal;
- incoming Relationship traversal;
- Context membership retrieval;
- filtered pagination;
- optimistic mutation;
- concurrent conflict behavior;
- query counts;
- execution duration.

Performance optimization shall not weaken integrity, authorization,
confidentiality, Evidence, versioning, or Audit.

## Deferred Storage Capabilities

The following remain deferred:

- separate graph database;
- vector database;
- semantic embeddings;
- real-time telemetry storage;
- time-series operational data;
- Engineering Digital Twin state;
- Maintenance history;
- HSE domain data;
- Methods and Systems domain data;
- generic enterprise asset management.

Deferred capabilities require separate Product Owner approval and accepted
architecture documents.

## Product Owner Decisions Required

Before implementation begins, the Product Owner shall approve:

1. PostgreSQL as the Version-1 System of Record.
2. The three preliminary aggregate boundaries.
3. Immutable UUID primary identity.
4. Separate Engineering Object identifier records.
5. Directional Relationship persistence.
6. Explicit Context membership records.
7. Positive optimistic versions.
8. Atomic mutation and Audit behavior.
9. Ordinary deletion prohibition.
10. Repository and service boundaries.
11. Bounded PostgreSQL graph traversal.
12. Deferred graph and vector databases.

## Success Criteria

PATCH-021.5 is ready for implementation planning only when:

- persistence areas are approved;
- aggregate boundaries are approved;
- UUID identity is accepted;
- scope fields are mandatory;
- identifier uniqueness is governed;
- Relationship direction is preserved;
- Context membership is explicit;
- optimistic concurrency is mandatory;
- Audit is atomic;
- confidentiality is stored and enforced;
- database constraints protect critical integrity;
- repository boundaries are accepted;
- PostgreSQL traversal remains bounded;
- migration and test strategies are accepted;
- Product Owner approval is recorded.

## Final Direction

PostgreSQL shall remain the Version-1 System of Record.

The EKG shall use relational persistence with governed directional
Relationships and explicit Context membership.

The physical model shall protect engineering identity, meaning, Evidence,
Human responsibility, version history, confidentiality, and Audit integrity.

Implementation begins only after final Product Owner approval.

## Product Owner Approval

The Product Owner approves this design for Version 1.

Version 1 remains focused on:

- Electrical Engineering;
- Instrumentation Engineering;
- Industrial Automation;
- shared Engineering Objects required by those disciplines.

Maintenance, Methods and Systems, HSE, Mechanical, Process, Reliability,
Asset Integrity, and other future domains remain deferred.

This approval authorizes the next implementation-planning stage but does not
authorize uncontrolled implementation outside the accepted EKG architecture.
