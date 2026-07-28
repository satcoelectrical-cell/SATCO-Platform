# PATCH-022.1 Core Enumerations and Contracts

## Status

Implemented and Validated

## Purpose

Define the controlled backend vocabulary and shared contracts required by the
Engineering Knowledge Graph persistence layer.

This stage establishes stable enum and contract boundaries before SQLAlchemy
models or Alembic migrations are introduced.

## Scope

PATCH-022.1 shall define controlled values for:

- Engineering Object families;
- engineering disciplines;
- lifecycle states;
- authority standing;
- confidentiality levels;
- relationship families;
- context types;
- identifier kinds;
- responsibility roles.

It shall also define shared validation contracts for:

- positive optimistic versions;
- immutable UUID identity;
- normalized external identifiers;
- directional Relationships;
- explicit scope;
- Human responsibility.

## Non-Scope

PATCH-022.1 shall not implement:

- SQLAlchemy models;
- database tables;
- Alembic migrations;
- repositories;
- services;
- APIs;
- graph traversal;
- AI behavior;
- Digital Twin behavior.

## Engineering Object Families

Version 1 shall support controlled families equivalent to:

- instrumentation;
- electrical;
- automation;
- shared.

Future families require a governed EKG extension.

## Engineering Disciplines

Version 1 shall support controlled disciplines equivalent to:

- instrumentation;
- electrical;
- industrial automation;
- shared engineering.

## Lifecycle States

The initial controlled lifecycle vocabulary shall consider:

- proposed;
- active;
- superseded;
- withdrawn;
- retired.

Final persistence use remains subject to implementation validation.

## Authority Standing

The initial controlled authority vocabulary shall consider:

- draft;
- proposed;
- reviewed;
- approved;
- disputed;
- rejected.

Only authorized Human approval may create approved authority standing.

## Confidentiality Levels

The initial controlled confidentiality vocabulary shall consider:

- organization;
- customer;
- project;
- workspace;
- restricted.

Authorization shall be enforced before disclosure.

## Relationship Families

Version 1 shall support controlled relationship families equivalent to:

- structural;
- physical;
- electrical;
- instrumentation;
- automation;
- evidence;
- dependency;
- governance.

## Identifier Kinds

Version 1 shall support controlled identifier kinds equivalent to:

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

## Responsibility Roles

Version 1 shall support controlled responsibility roles equivalent to:

- creator;
- owner;
- steward;
- discipline owner;
- reviewer;
- approver;
- assignee;
- source authority.

AI and anonymous actors shall not hold accountable engineering roles.

## Contract Rules

Shared backend contracts shall enforce:

- UUID identity;
- positive integer version;
- explicit Organization scope;
- explicit Project scope when applicable;
- explicit Workspace scope when applicable;
- normalized controlled values;
- immutable primary identity;
- directional source and target identity;
- non-empty engineering purpose where required;
- Human responsibility for authoritative knowledge.

## Implementation Direction

Controlled values should be implemented through Python enum types or other
finite typed contracts.

Free-text values shall not replace controlled vocabulary.

The contracts shall remain reusable by:

- schemas;
- SQLAlchemy models;
- services;
- repositories;
- migrations;
- tests.

## Completion Gate

PATCH-022.1 is complete only after:

- the controlled vocabulary is approved;
- enum names and values are stable;
- compatibility with PATCH-021 is validated;
- static tests pass;
- import tests pass;
- no database schema is created;
- Product Owner approval is recorded.

## Implementation Result

PATCH-022.1 delivered:

- controlled Engineering Object family enums;
- controlled discipline enums;
- lifecycle enums;
- authority-standing enums;
- confidentiality enums;
- Relationship-family enums;
- identifier-kind enums;
- responsibility-role enums;
- shared enum exports;
- enum contract tests.

No database model, table, or migration was introduced.

## Validation Result

The focused backend test completed successfully:

- 5 tests passed;
- enum values are stable;
- enum values are normalized;
- approved authority standing is explicit;
- AI and anonymous actors are excluded from accountable responsibility roles.

## Product Owner Boundary

Version 1 remains focused on:

- Electrical Engineering;
- Instrumentation Engineering;
- Industrial Automation;
- required shared Engineering Objects.

Future domains remain governed extensions.
