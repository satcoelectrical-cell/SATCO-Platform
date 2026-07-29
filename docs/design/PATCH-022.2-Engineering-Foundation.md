# PATCH-022.2 Engineering Foundation

## Status

Implemented

## Purpose

Establish the operational foundation required by the Engineering Knowledge
Graph before introducing the Engineering Object aggregate.

PATCH-022.2 defines the collaboration, context, relationship, responsibility,
lifecycle, and persistence boundaries on which future Engineering Objects
shall operate.

## Approved Inputs

PATCH-022.2 is governed by:

- PATCH-021 Engineering Knowledge Graph Architecture;
- PATCH-021.5 Physical Data Model;
- PATCH-022 Backend Foundation;
- PATCH-022.1 Core Enumerations and Contracts;
- ADR-017 Engineering Knowledge Graph Evolution.

## Implemented Scope

PATCH-022.2 includes:

- Engineering Workspace persistence;
- Engineering Workspace lifecycle;
- Workspace ownership and assignment;
- Workspace collaborators;
- optimistic concurrency control;
- Engineering Context persistence;
- Engineering Context lifecycle;
- Engineering Context Relationships;
- Human responsibility and accountability;
- audit-compatible timestamps;
- repository and service foundations;
- authenticated Workspace APIs;
- Alembic migrations.

## Engineering Workspace

Engineering Workspace defines the controlled collaboration boundary for
engineering work performed within a Project and Discipline.

A Workspace preserves:

- project identity;
- discipline;
- display name;
- description;
- lifecycle status;
- owner;
- primary assignee;
- collaborators;
- optimistic version;
- archive state;
- creation timestamp;
- modification timestamp.

Workspace identity shall remain stable throughout its lifecycle.

Archiving shall preserve history and shall not physically delete engineering
knowledge.

## Engineering Context

Engineering Context represents a governed unit of engineering knowledge,
understanding, constraint, observation, decision support, or contextual
information.

Engineering Context is not the Engineering Object aggregate.

It provides knowledge surrounding Engineering Objects and future graph
relationships.

Context identity shall remain stable and shall preserve:

- scope;
- lifecycle;
- authority;
- responsibility;
- timestamps;
- relationship connectivity.

## Context Relationships

Context Relationships establish controlled graph connectivity between
Engineering Context records.

Relationships shall preserve:

- source identity;
- target identity;
- relationship type;
- authority standing;
- lifecycle state;
- responsibility;
- timestamps.

Relationships shall not silently modify the identity or lifecycle of their
connected records.

## Responsibility

Anonymous creation or mutation is prohibited.

Every governed mutation shall preserve the responsible authenticated Human
actor through the applicable service boundary.

## Persistence Boundary

Direct mutation outside the approved service and aggregate boundaries is
prohibited.

Repositories manage persistence operations.

Services enforce lifecycle, authorization, validation, responsibility, and
business rules.

API routers shall remain transport adapters and shall not contain domain
logic.

## Version-1 Boundary

PATCH-022.2 does not introduce:

- Engineering Object persistence;
- Engineering Object identifiers;
- Engineering Object relationships;
- AI behavior;
- graph traversal services;
- semantic search;
- automated engineering judgment.

These capabilities belong to later PATCH-022 increments.

## Validation

PATCH-022.2 is considered implemented when:

- migrations are applied successfully;
- the database revision matches the current Alembic head;
- authenticated Workspace operations succeed;
- optimistic version conflicts are rejected;
- lifecycle transitions are enforced;
- archive and restore preserve identity and history;
- unauthorized mutations are rejected;
- repository and service boundaries remain intact.

## Outcome

PATCH-022.2 establishes the Engineering Foundation.

PATCH-022.3 shall introduce the Engineering Object aggregate on top of this
foundation without replacing or invalidating existing Workspace, Context, or
Relationship capabilities.
