# PATCH-026 — Engineering Relationship Engine

## 1. Document Control

| Field | Value |
|---|---|
| Document ID | PATCH-026 |
| Title | Engineering Relationship Engine |
| Status | Approved — IRR-026 Ready for Implementation |
| Owner | SATCO Platform Architecture Team |
| Architecture Style | Docs-First Architecture |
| Implementation | Authorized by IRR-026 |
| Decision Date | 2026-08-01 |

## 2. Objective

Deliver a governed EngineeringRelationship aggregate and application boundary
connecting two EngineeringObject UUIDs without expanding either
EngineeringObject consistency boundary.

## 3. Governing Documents

- SATCO Governance Model
- SATCO Development Lifecycle
- EngineeringObject Blueprint v1.0
- PATCH-021.2 Engineering Relationship Vocabulary
- PATCH-023 EngineeringObject Application Layer
- PATCH-024 EngineeringObject Persistence Migration
- PATCH-025 Authenticated Organization Context
- docs/02_Roadmap_v1.md

## 4. Approved Scope

PATCH-026 includes:

- an independently identified EngineeringRelationship Aggregate Root;
- immutable source and target EngineeringObject UUIDs;
- the closed Version 1 vocabulary and semantics in EDS-026;
- explicit direction, lifecycle, authority, responsibility, Evidence, scope,
  version, and history;
- self-link, duplicate, invalid-link, and approved cycle prevention;
- deny-by-default authorization before disclosure;
- optimistic concurrency and stable conflicts;
- idempotent commands;
- atomic relationship, Audit, Domain Event outbox, and idempotency persistence
  through one Unit of Work and one PostgreSQL transaction;
- inward-owned repository, policy, validation, cycle, clock, recorder, and Unit
  of Work ports;
- explicit application commands and HTTP contracts;
- bounded direct, neighborhood, and path queries;
- one additive migration;
- focused unit, migration, integration, security, performance, and regression
  tests.

## 5. Explicit Non-Scope

- arbitrary unrestricted graph edges;
- cross-organization relationships;
- cross-project relationships in Version 1;
- Evidence or Human/User records as relationship endpoints;
- AI-created relationships without an explicit authenticated engineer command;
- semantic or vector search;
- graph database adoption;
- generic update;
- physical deletion;
- frontend implementation;
- unrelated refactoring.

## 6. Approved Relationship Boundary

Every PATCH-026 relationship connects exactly two EngineeringObject UUIDs. The
source states the engineering subject and the target states the engineering
object completing the approved predicate. Direction is authoritative; reverse
navigation is a derived read view and never creates another relationship.

PATCH-021.2 Evidence-family meanings that require a document, review, decision,
or other Evidence aggregate are represented by typed Evidence UUID references,
not relationship endpoints. Governance-family meanings that require a Human,
role, Organization, policy, or confidentiality subject are represented by
responsibility, authorization, and scope fields, not relationship endpoints.
Neither family exposes a creatable PATCH-026 edge type in Version 1.

The mandatory creatable vocabulary is the closed EDS-026 set selected only from
PATCH-021.2 candidate types. Its canonical discriminator is the ordered
`(relationship_family, relationship_type)` pair. A type token without its
family is invalid and shall not be inferred. Unlisted or free-text pairs are
invalid.

## 7. Scope Rules

Both endpoint objects and the relationship shall belong to the authenticated
actor's active Organization. Cross-organization and cross-project
relationships are denied.

Same-workspace relationships are allowed when the actor is authorized for the
operation and both endpoints. Cross-workspace relationships are allowed only
within the same Project for the exact EDS-026 type allowlist, require
authorization to both Workspaces, and use the source object's Workspace as the
governing relationship Workspace. This grants no cross-workspace membership.

PATCH-026 persists no relationship confidentiality label. Effective relationship
confidentiality is the intersection of the existing visibility decisions for
both endpoint EngineeringObjects, every referenced Evidence item, and both
applicable Workspaces. Authorization is operation-specific, scope-aware, and
deny-by-default. Every constituent must be visible to the actor before the
relationship or any relationship-derived identifier, count, or path is
disclosed. Failure of any constituent visibility decision returns Protected Not
Found. No partial redaction is authorized because it could distort engineering
meaning. Clients cannot supply or lower this derived access classification.

## 8. Lifecycle, Authority, and Responsibility

Lifecycle states and their complete matrix are defined by EDS-026. Creation
starts at lifecycle `proposed`, authority `draft`, and version 1. A
relationship may become `current` only after approved authority and required
Evidence.

Creator is the authenticated creating engineer and immutable. Steward defaults
to Creator and may transfer only to an active authorized engineer in scope.
Reviewer and Approver are recorded only by their explicit authenticated
commands. Reviewer and Approver must be distinct; Approver must also be
distinct from Creator. AI and automation cannot occupy any accountable role or
issue an authoritative command.

## 9. Mutation Guarantees

Creation accepts no expected version. Every post-creation command requires a
positive expected version, uses compare-and-change persistence, and increments
version exactly once on success. Stale state returns Version Conflict without
state change.

Idempotency is scoped by actor, command type, and idempotency UUID. Exact
committed replay returns the recorded authorized result. Reuse with different
content returns Idempotency Conflict.

One Unit of Work atomically persists aggregate state, an accountable Audit
record using `entity_uuid`, durable Domain Event outbox records, and the
idempotency result. Failure rolls back all effects. Audit and Domain Events are
not substitutes.

## 10. API and Query Boundary

Only the explicit commands and query endpoints in IDS-026 are approved. No
generic PUT/PATCH, physical DELETE, arbitrary query language, or unbounded
traversal is permitted.

Traversal is read-only, PostgreSQL-backed, cycle-safe, authorization-filtered
edge-by-edge and node-by-node, deterministically ordered, paginated, and capped
at depth 5 and 100 returned relationships per request.

## 11. Dependencies

- completed PATCH-023 EngineeringObject Application Layer;
- completed PATCH-024 EngineeringObject Persistence Migration;
- completed PATCH-025 Authenticated Organization Context;
- implemented PATCH-027 Evidence Foundation;
- approved PATCH-021.2 Engineering Relationship Vocabulary;
- accepted EDS-026 and PASS review;
- AR-026 PASS;
- approved IDS-026;
- executable Implementation Plan-026;
- IRR-026 READY FOR IMPLEMENTATION.

## 12. Acceptance Criteria

- only the EDS-026 vocabulary is creatable;
- all lifecycle, authority, responsibility, Evidence, scope, duplicate, and
  cycle rules are aggregate/application enforced as assigned;
- authorization precedes disclosure;
- cross-organization and cross-project links are denied;
- concurrency, idempotency, Audit, events, and transaction atomicity pass;
- model and migration match exactly;
- explicit APIs and bounded queries satisfy IDS-026;
- no generic update or physical delete exists;
- focused and complete regression suites pass.

## 13. Implementation Authorization

**NOT AUTHORIZED UNTIL IRR-026 IS READY FOR IMPLEMENTATION**

## 14. Revision History

| Version | Date | Description |
|---|---|---|
| 0.1 | 2026-08-01 | Initial blocked draft |
| 1.0 | 2026-08-01 | Contract blockers closed and PATCH approved |
