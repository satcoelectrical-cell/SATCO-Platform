# ADR-022 — Project Organization Ownership

## Status

Accepted

## Date

2026-08-02

## Decision Owners

- Product Owner;
- Architecture Guardian;
- Repository/Data Owner for existing Project ownership mapping.

## Approval Record

| Authority | Decision | Date |
|---|---|---|
| Product Owner | Accepted | 2026-08-02 |
| Architecture Guardian | Accepted | 2026-08-02 |
| Repository/Data Owner | Architecture accepted; existing-data mapping pending inventory decision | 2026-08-02 |

## Context

PATCH-025 introduced trusted active Organization context for authenticated
Users. EngineeringObject, EngineeringRelationship, Evidence, and the proposed
EngineeringExperienceCapture carry Organization scope. The existing Project
aggregate and `projects` table do not.

As a result, SATCO cannot prove that a Project referenced by an
Organization-scoped aggregate belongs to the actor's active Organization.
Project owner, primary assignee, Workspace membership, Customer, or an optional
Engineering Object cannot substitute for Project tenant ownership.

This gap blocked PATCH-028 Sprint 2 before persistence implementation. The
evidence is recorded in
`docs/reviews/PATCH-028-Sprint-2-Project-Organization-Blocker.md`.

## Proposed Decision

Every Project shall have exactly one immutable owning Organization.

Project Organization ownership shall:

- be represented by a non-null Organization UUID on the Project aggregate and
  authoritative `projects` relation;
- be derived server-side from the authenticated actor's active Organization at
  Project creation;
- never be accepted from an ordinary client request body, query parameter,
  unsigned header, or unverified claim;
- remain immutable for Version 1;
- govern Project lookup, listing, mutation, Search, Workspace access, and every
  dependent aggregate reference;
- precede disclosure of Project existence, identifiers, state, counts, or
  dependent resources;
- prohibit cross-Organization Project references and reassignment.

## Aggregate and Dependency Consequences

Project owns its Organization identity. Child or dependent capabilities may
copy the immutable Organization UUID for scoped persistence and performance,
but Application validation must prove equality with the referenced Project.

Workspace remains a Project child and derives Organization from Project. A
separately persisted Workspace Organization UUID is not introduced by this
decision unless a later accepted design proves it necessary.

EngineeringObject, EngineeringRelationship, Evidence, Context, Capture,
Search, and future modules must validate their Project references against
Project Organization ownership. They shall not infer tenant ownership from
Users, Customers, Workspaces, or other optional objects.

## Existing Data Decision

No existing Project may be assigned to an Organization by assumption.

Before a NOT NULL constraint is applied, a governed Project Ownership Inventory
must identify every existing Project and exactly one approved Organization UUID.
Each mapping requires attributable approval by the Repository/Data Owner or
other designated Human authority.

Owner/assignee membership, selected active membership, Customer association,
or most-frequent usage may be used as review evidence but cannot automatically
become the authoritative mapping.

Zero, duplicate, conflicting, missing, inactive, or unapproved mappings block
migration. The migration shall fail safely rather than invent ownership.

The exact delivery mechanism for the approved mapping—revision-owned static
mapping for a bounded known dataset, separately governed pre-migration data
step, or an approved empty-database assertion—must be selected by EDS/IDS after
inventory evidence is available. Production data must not be embedded in
documentation or source without explicit data-governance approval.

## Migration Principle

The final schema must have:

- `projects.organization_id` non-null;
- FK to `organizations.id` with RESTRICT behavior;
- an Organization-scoped Project identity/index strategy;
- no interval in an accepted final state where unowned Projects are valid.

A safe implementation may use an additive-expand, approved-backfill,
validate, and constrain sequence inside one PATCH or governed sub-stages. It
shall support clean-database upgrade and existing-data upgrade. Downgrade or
forward repair must not silently discard ownership or governed history.

## Authorization Principle

Every Project operation follows:

1. authenticate;
2. derive active Organization;
3. query Project within that Organization;
4. apply operation-specific role/ownership/assignment policy;
5. return Protected Not Found before cross-Organization disclosure;
6. persist Audit/accountability where governed.

User assignment supplements but never defines tenant ownership.

## Compatibility

The decision is additive and aligns with:

- Constitution Single Source of Truth and modularity;
- Manifesto Engineering Context Is Sacred and Organizational Ownership;
- PATCH-025 authenticated Organization context;
- ADR-016 dual-use operating model;
- ADR-020 open extension;
- existing Project identity and Project Code semantics.

Existing APIs may preserve response compatibility by adding Organization only
to trusted internal state. Client-controlled Organization input is prohibited.
Any user-facing response change requires explicit IDS authorization.

## Alternatives Rejected

### User membership defines Project Organization

Rejected because Users may belong to multiple Organizations and assignment is
not ownership.

### Workspace or Engineering Object inference

Rejected because Project-wide capabilities may have neither, and inconsistent
children would make ownership ambiguous.

### Independent Organization IDs only on child aggregates

Rejected because separate valid foreign keys do not prove parent/child tenant
compatibility.

### Organization-optional Project

Rejected because it preserves the ambiguity and weakens deny-by-default tenant
isolation.

### Automatic heuristic backfill

Rejected because Evidence Before Assumption prohibits invented tenant
ownership.

## Consequences

### Positive

- Project becomes a trustworthy tenant boundary;
- dependent aggregates can validate same-Organization Project context;
- Project queries and Search can prevent cross-tenant disclosure;
- PATCH-028 Sprint 2 can enforce its accepted EDS after the prerequisite;
- future modules receive one stable ownership contract.

### Costs and constraints

- existing Project data requires inventory and Human mapping approval;
- Project repository/service/API/search tests require revalidation;
- dependent domains require impact analysis and regression;
- migration cannot proceed while any Project mapping is unresolved;
- Project transfer between Organizations remains prohibited in Version 1.

## Explicit Non-Authorization

This Accepted ADR does not authorize schema changes, data backfill, Project API
changes, migration execution, PATCH-028 continuation, commit, push, or
deployment.

## Acceptance Gate

The ADR becomes Accepted only after Product Owner and Architecture Guardian
approval. Existing-data migration readiness additionally requires Repository/
Data Owner approval of a complete Project Ownership Inventory.

## Revision History

| Version | Date | Description |
|---|---|---|
| 0.1 | 2026-08-02 | Initial proposed immutable Project Organization ownership decision. |
