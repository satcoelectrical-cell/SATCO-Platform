# PATCH-022.3 Engineering Object Aggregate

## Status

Approved for Implementation

## Purpose

Introduce EngineeringObject as the central Aggregate Root of the SATCO
Engineering Knowledge Graph.

EngineeringObject represents a governed engineering entity whose identity is
independent from tag numbers, document numbers, vendor references, and other
mutable identifiers.

## Approved Inputs

PATCH-022.3 is governed by:

- PATCH-021 Engineering Knowledge Graph Architecture;
- PATCH-021.5 Physical Data Model;
- PATCH-022 Backend Foundation;
- PATCH-022.1 Core Enumerations and Contracts;
- PATCH-022.2 Engineering Foundation;
- ADR-017 Engineering Knowledge Graph Evolution.

## Scope

PATCH-022.3 shall implement only:

- Engineering Object SQLAlchemy model;
- immutable UUID identity;
- scope fields;
- classification fields;
- lifecycle persistence;
- authority standing;
- optimistic version;
- creator responsibility;
- steward responsibility;
- creation timestamp;
- modification timestamp;
- model registration;
- model-level validation constraints.

PATCH-022.3 shall not implement:

- Engineering Object identifiers;
- Engineering Object relationships;
- repository operations;
- service operations;
- API endpoints;
- AI behavior;
- graph traversal;
- search indexing;
- Alembic migration before model review.

## Aggregate Root

EngineeringObject is the Aggregate Root.

Every future mutation affecting Engineering Object identity, classification,
scope, lifecycle, authority, responsibility, or metadata shall pass through
the aggregate and its approved service boundary.

No router, repository consumer, automation, or AI component may directly
mutate internal aggregate state.

Lifecycle transition, authority transition, reclassification, and steward
transfer rules belong to explicit `EngineeringObject` Aggregate Root
operations. The application service may orchestrate these commands but shall
not duplicate transition policy, implement aggregate invariants, or mutate
aggregate fields directly.

## Identity

Every Engineering Object shall contain an immutable UUID primary key.

Engineering identity shall never depend upon:

- engineering tag number;
- equipment number;
- drawing number;
- document number;
- vendor reference;
- customer reference;
- temporary project code;
- database sequence visible to users.

Identifiers shall be modeled separately in a future registered PATCH.

## Scope

Version 1 Engineering Object scope shall include:

- organization scope;
- customer scope when applicable;
- project scope;
- workspace scope.

Until an Organization aggregate is introduced, organization scope shall be
represented through an explicit non-null organization UUID value without a
foreign-key dependency.

Customer scope may be nullable when the Engineering Object is internal and
not associated with a Customer.

Project and Workspace scope are mandatory for PATCH-022.3.

## Classification

Version 1 classification shall include:

- Engineering Object Family;
- Engineering Discipline;
- Engineering Object Type;
- optional controlled subtype.

Controlled classification values shall use PATCH-022.1 enums wherever an
approved enum exists.

Free-text duplication of controlled values is prohibited.

## Lifecycle

Engineering Object lifecycle shall use the approved controlled lifecycle enum.

Lifecycle persistence shall not perform physical deletion.

Lifecycle transitions shall be enforced by explicit `EngineeringObject`
Aggregate Root operations introduced through the approved Blueprint command
contract. A service may coordinate the operation but shall not decide the
transition or mutate lifecycle state directly.

## Authority Standing

Engineering Object authority standing shall use the approved controlled
authority enum.

Authority standing indicates the governance strength and reliability of the
Engineering Object record.

Authority standing shall not be inferred or changed automatically by AI.

Authority transitions shall occur only through an explicit
`EngineeringObject` Aggregate Root operation. Reclassification and steward
transfer shall likewise use their explicit aggregate operations so that all
approved invariants remain inside the Aggregate Root.

## Optimistic Concurrency

Every Engineering Object shall contain a positive optimistic version.

The initial version shall be 1.

Every approved mutation shall increment the version exactly once.

PATCH-022.3 persists the version field but does not yet implement mutation
services.

## Responsibility

Every Engineering Object shall preserve:

- creator user identity;
- steward user identity;
- creation timestamp;
- modification timestamp.

Creator identity is immutable after creation.

Steward identity may change only through the explicit approved
`EngineeringObject` steward-transfer operation orchestrated by the application
service.

Anonymous responsibility is prohibited.

## Timestamps

Creation and modification timestamps shall be generated consistently with the
existing SATCO persistence conventions.

The modification timestamp shall change whenever an approved persistent
mutation occurs.

## Database Constraints

The model shall enforce, at minimum:

- immutable UUID primary key;
- non-null organization scope;
- non-null project scope;
- non-null workspace scope;
- non-null classification;
- non-null lifecycle state;
- non-null authority standing;
- positive optimistic version;
- non-null creator;
- non-null steward;
- non-null timestamps.

Foreign keys shall preserve referential integrity for existing Customer,
Project, Workspace, and User entities.

## Model Review Gate

No Alembic migration shall be created until the Engineering Object model has
been reviewed against:

- PATCH-021.5 Physical Data Model;
- PATCH-022.1 controlled enums;
- existing SQLAlchemy conventions;
- existing foreign-key types;
- existing timestamp conventions;
- existing naming conventions;
- current PostgreSQL constraints.

## Acceptance Criteria

PATCH-022.3 model design is accepted when:

- the model imports successfully;
- SQLAlchemy metadata includes the engineering_objects table;
- all required controlled enums are used correctly;
- UUID identity is immutable by design;
- scope fields match existing entity key types;
- responsibility fields reference authenticated Users;
- optimistic version defaults to 1;
- required database constraints are declared;
- no repository, service, router, identifier, relationship, or AI behavior is
  introduced;
- automated tests for model metadata and constraints pass.

## Outcome

PATCH-022.3 establishes EngineeringObject as the central persistent Aggregate
Root.

A future registered PATCH shall introduce external and engineering identifiers
without changing Engineering Object identity.
