# PATCH-027 — Evidence Foundation

## Document Control

| Field | Value |
|---|---|
| Document ID | PATCH-027 |
| Status | DONE |
| Owner | SATCO Platform Architecture Team |
| Implementation | Completed, validated, committed, and pushed |
| Decision Date | 2026-08-01 |

## Objective

Provide the minimum governed Evidence aggregate, persistence, validation, and
application boundary required by PATCH-026.

## Governing Documents

- SATCO Governance Model and Development Lifecycle
- EngineeringObject Blueprint v1.0, Sections 2 and 8.2.3
- PATCH-026 Engineering Relationship Engine
- PATCH-025 Authenticated Organization Context

## Scope

- immutable Evidence UUID identity;
- trusted Organization scope and optional Project/Workspace scope;
- lifecycle, positive version, immutable Creator, and timestamps;
- bounded source/reference metadata: source kind, source reference, source
  revision, source standing, effective date, and supported engineering fact;
- deny-by-default visibility and authorization before disclosure;
- repository, application service, validator port/adapter, and focused API;
- optimistic concurrency, Audit, Domain Events, idempotency, and one atomic
  Unit of Work;
- one additive migration and focused/full regression tests.

## Evidence Contract

Lifecycle is `proposed`, `current`, `withdrawn`, `superseded`, or `rejected`.
Creation starts proposed/version 1. Allowed transitions are proposed to current,
withdrawn, or rejected; current to withdrawn or superseded; withdrawn to
proposed. Superseded and rejected are terminal. Every unlisted/self transition
is prohibited. Only current Evidence with source standing `current` is
acceptable authoritative support.

Source kinds are the closed metadata values `engineering_record`,
`external_reference`, `human_review`, `technical_decision`,
`standard_reference`, `inspection_record`, and `commissioning_record`.
PATCH-027 stores a reference/citation and metadata only; it never stores or
manages source content.

Workspace scope requires Project scope and the Workspace must belong to that
Project. Organization-wide Evidence has neither Project nor Workspace.
Project-wide Evidence has Project but no Workspace. Workspace Evidence is
compatible only with that Workspace. For a PATCH-026 cross-Workspace
relationship, Workspace Evidence is compatible only when scoped to the source
or target Workspace. Cross-Project use is denied.

## Validation Contract for PATCH-026

`EvidenceValidator` shall validate every referenced UUID for existence,
authorization/visibility, lifecycle `current`, source standing `current`, same
Organization, and compatible Project/Workspace scope. Validation occurs before
relationship disclosure or mutation and returns no Evidence content.

## Non-Scope

- document management, upload, parsing, or file storage;
- AI-generated Evidence;
- semantic/vector search;
- unrestricted cross-Project Evidence;
- Evidence as a PATCH-026 relationship endpoint;
- generic update or physical delete;
- frontend or unrelated refactoring.

## Atomicity and History

Every mutation requires correlation/idempotency metadata; post-creation
mutations require positive expected version and increment exactly once. One
Unit of Work and PostgreSQL transaction persist Evidence, Audit using
`entity_uuid`, outbox events, and idempotency outcome. Failure rolls back all.

## Approval and Authorization

PATCH-027 is approved. Implementation was limited to approved IDS-027 and
authorized by IRR-027 READY FOR IMPLEMENTATION.

## Completion Status

Framework v1.1 QG-1 through QG-11 are satisfied by the approved governance and
design chain, completed Evidence Foundation implementation, successful
migration upgrade/downgrade and clean-database migration validation, passing
Evidence tests and full backend regression, and the recorded absence of
remaining blockers.

QG-12 is satisfied by commit `f9d244c`, which records completion of PATCH-023
through PATCH-027, and by verified publication of that commit to
`origin/patch-022.3a-development-infrastructure`. Local HEAD and remote-tracking
HEAD matched at review, and the pre-review working tree was clean.

PATCH-027 is `DONE`. This status reconciliation records existing Commit and
Push evidence and does not alter implementation history.

## Revision History

| Version | Date | Description |
|---|---|---|
| 1.0 | 2026-08-01 | Approved bounded Evidence prerequisite |
| 1.1 | 2026-08-02 | Recorded implementation completion and validation with Commit and Push gates pending. |
| 1.2 | 2026-08-02 | Recorded QG-12 Commit and Push evidence and finalized PATCH-027 as DONE. |
