# PATCH-022.2 Engineering Object Persistence

## Status

Draft

## Purpose

Implement the first persistent aggregate of the Engineering Knowledge Graph.

PATCH-022.2 introduces the backend persistence model for Engineering Objects
while preserving every architectural constraint approved in PATCH-021.

## Approved Inputs

PATCH-022.2 is governed by:

- PATCH-021 Engineering Knowledge Graph Architecture;
- PATCH-022 Backend Foundation;
- PATCH-022.1 Core Enumerations and Contracts.

## Scope

PATCH-022.2 shall implement only:

- Engineering Object SQLAlchemy model;
- immutable UUID identity;
- scope fields;
- classification fields;
- lifecycle persistence;
- authority standing;
- optimistic version;
- Human responsibility fields;
- timestamps.

PATCH-022.2 shall not implement:

- Engineering Relationships;
- Engineering Context;
- identifier persistence;
- repositories;
- services;
- APIs;
- AI behavior.

## Aggregate Root

EngineeringObject is the Aggregate Root.

Every mutation affecting Engineering Object identity or metadata shall pass
through this aggregate.

No external component may directly mutate internal aggregate state.

## Mandatory Identity

Every Engineering Object shall contain:

- immutable UUID primary key;
- Organization scope;
- Customer scope when applicable;
- Project scope;
- Workspace scope;
- optimistic version;
- lifecycle state;
- authority standing.

Engineering identity shall never depend upon engineering tag numbers.

## Classification

Version 1 classification shall include:

- Engineering Object Family;
- Engineering Discipline;
- Engineering Object Type;
- optional controlled subtype.

Classification values shall use PATCH-022.1 controlled enums wherever
applicable.

## Responsibility

Engineering Objects shall preserve:

- creator;
- steward;
- creation timestamp;
- modification timestamp.

Anonymous responsibility is prohibited.

## Version-1 Boundary

PATCH-022.2 shall introduce only the Engineering Object persistence model.

No Alembic migration shall be created until the model passes review.
