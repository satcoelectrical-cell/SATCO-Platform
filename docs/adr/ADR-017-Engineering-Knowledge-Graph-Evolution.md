# ADR-017 Engineering Knowledge Graph Evolution

## Status

Accepted

## Context

During implementation of PATCH-022, the Engineering Workspace,
Engineering Context, and Context Relationship foundations were completed
before introducing the Engineering Object aggregate.

This implementation order proved beneficial because workspaces define the
engineering collaboration boundary, contexts capture engineering knowledge,
and relationships establish graph connectivity.

The original PATCH-022.2 document no longer reflects the implemented
foundation.

## Decision

PATCH-022 shall be interpreted as the following evolution:

- PATCH-022.1 — Contracts & Controlled Enumerations
- PATCH-022.2 — Engineering Foundation
- PATCH-022.3 — Engineering Object Aggregate
- PATCH-022.4 — Object Identifiers
- PATCH-022.5 — Engineering Relationships
- PATCH-022.6 — Repository Layer
- PATCH-022.7 — Service Layer
- PATCH-022.8 — API Layer

Engineering Workspace, Engineering Context, and Context Relationship
constitute the Engineering Foundation.

EngineeringObject becomes the central Aggregate Root of the Engineering
Knowledge Graph.

All engineering entities—including instruments, motors, valves,
documents, drawings, loops, PLCs, cables, packages, and future engineering
assets—shall ultimately be represented as Engineering Objects.

## Consequences

The current implementation remains valid.

No rollback is required.

Future development shall extend the existing foundation instead of replacing
it.

Documentation shall be updated to align with this evolution before further
implementation.
