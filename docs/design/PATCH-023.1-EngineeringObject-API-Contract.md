# PATCH-023.1 — EngineeringObject API Contract

## 1. Document Control

| Field | Value |
|-------|-------|
| Document ID | PATCH-023.1 |
| Title | EngineeringObject API Contract |
| Status | Approved |
| Owner | SATCO Platform Architecture Team |
| Architecture Style | Docs-First Architecture |
| Implementation | Authorized through PATCH-023 and IRR-023 |
| Last Updated | 2026-08-01 |

## 2. Status

This document defines the proposed API contract for the EngineeringObject Application Layer.

Its purpose is to establish the request, response, validation, visibility, and command boundaries before implementation begins.

Implementation is authorized only through the approved PATCH-023, IDS-023,
and IRR-023 scope.

## 3. Purpose

This document specifies the external application-facing contract for EngineeringObject.

It defines:

- Request contracts
- Response contracts
- Command boundaries
- Validation rules
- Visibility rules
- Error contracts
- Compatibility requirements

This document does not define implementation details.

## 4. Governing Documents

This document is governed by:

- SATCO Constitution
- System Architecture
- Coding Standards
- EngineeringObject Blueprint
- PATCH-023 EngineeringObject Application Layer
- Approved ADRs
- Current EngineeringObject Domain Model

## 5. Architectural Context

EngineeringObject is the primary engineering aggregate of the SATCO Platform.

This API Contract defines how authorized clients interact with the EngineeringObject Application Layer.

The Domain Model remains the source of truth for business rules and invariants.

This API Contract shall not redefine, weaken, or bypass approved domain behavior.

## 6. Scope

This document specifies only:

- API request contracts
- API response contracts
- Explicit command boundaries
- Validation rules
- Visibility rules
- Error contracts
- Compatibility requirements

Implementation details, persistence behavior, database changes, and frontend behavior remain outside the scope of this document.

## 7. API Design Principles

The EngineeringObject API shall follow these principles:

- Command / Query Separation (lightweight CQRS)
- No generic update endpoint
- Explicit business commands
- Immutable object identity
- Domain Model remains the source of truth
- Application Layer orchestrates business use cases
- API shall not bypass domain invariants

## 8. Create Contract

The Create Contract accepts only client-supplied engineering classification data.

Client-supplied fields:

- project_id
- family
- discipline
- object_type
- steward_id (optional and subject to explicit authorization)

System-managed fields:

- id
- organization_id
- customer_id
- workspace_id
- subtype
- lifecycle
- authority_standing
- version
- creator_id
- created_at
- updated_at

Creation derivation rules are:

- organization_id is derived from the authenticated actor's active organization scope;
- workspace_id is resolved from an explicitly authorized Workspace within the selected Project and compatible Discipline;
- customer_id is derived from the Project and may be null for an internal Project;
- creator_id is the authenticated actor;
- steward_id defaults to the authenticated actor unless an explicitly authorized steward_id is supplied;
- lifecycle is initialized to the approved Blueprint default `proposed`;
- authority_standing is initialized to the approved Blueprint default `draft`;
- version is initialized to `1`.

Workspace compatibility is deterministic:

| EngineeringObject discipline | Required Workspace discipline | Creation status |
|---|---|---|
| `instrumentation` | `instrumentation` | Permitted when scope and authorization pass |
| `electrical` | `electrical` | Permitted when scope and authorization pass |
| `industrial_automation` | `control` | Permitted when scope and authorization pass |
| `shared_engineering` | None in the current Workspace model | Deferred and rejected |

`industrial_automation` is the EngineeringObject classification term for the
operational discipline represented by the existing `control` Workspace.

The current model cannot represent a shared or multi-Workspace scope because
one EngineeringObject has one mandatory `workspace_id` and every Workspace has
one governed discipline. Membership in multiple Workspaces does not create a
shared Workspace and shall not grant cross-discipline access. Creation of a
`shared_engineering` EngineeringObject is rejected until a dedicated shared-
workspace capability is separately approved.

Clients shall not provide organization_id, customer_id, workspace_id,
creator_id, lifecycle, authority_standing, version, created_at, or updated_at.

The client shall not provide any system-managed field.

## 9. Update Contract

Generic update operations are prohibited.

The API shall not expose:

PUT /engineering-objects/{id}

PATCH /engineering-objects/{id}

EngineeringObject modifications shall be expressed through explicit business commands only.

## 10. Read Contract

A Read response returns the current EngineeringObject state.

Responses expose identifiers for related entities.

Nested aggregate representations are outside the scope of Version 1.

## 11. List Contract

List responses follow the standard SATCO pagination contract.

Response format:

- items
- total
- page
- size

Filtering and sorting shall be defined independently of the response format.

## 12. Command Boundaries

The following business commands are approved:

- CreateEngineeringObject
- ReclassifyEngineeringObject
- TransitionEngineeringObjectLifecycle
- TransitionEngineeringObjectAuthority
- TransferEngineeringObjectSteward

Each command represents a single business capability.

No generic field mutation endpoint is permitted.

Every command shall use the approved command envelope:

- authenticated actor context;
- authorization context;
- target object UUID where applicable;
- expected_version for all post-creation mutations;
- non-empty rationale;
- correlation identifier;
- idempotency identifier;
- Evidence references where required.

Authenticated actor identity is supplied by the authentication boundary and
shall not be accepted as an arbitrary client-supplied creator_id.

Creation does not accept expected_version.

Mandatory optimistic concurrency applies to every post-creation mutation command:

- a positive expected_version is required for every post-creation mutation command;
- persistence shall use compare-and-change semantics;
- each successful mutation shall increment the version exactly once;
- aggregate state shall remain unchanged on a version conflict;
- a version conflict shall produce an explicit concurrency-conflict outcome.
- a stale expected_version shall return the approved Version Conflict outcome.

## 13. Validation Rules

Validation ownership is separated as follows:

- Transport owns syntax, types, required fields, and request coherence.
- Application owns authorization, visibility, reference validation,
  idempotency, and command coordination.
- The EngineeringObject Aggregate Root owns classification compatibility,
  lifecycle rules, authority rules, aggregate invariants, and version
  advancement.

Minimum validation requirements:

- project_id shall reference an existing accessible project.
- family shall be a valid EngineeringObjectFamily.
- discipline shall be a valid EngineeringDiscipline.
- object_type shall be a valid EngineeringObjectType.
- customer_id shall never be accepted from clients.
- workspace_id shall never be accepted from clients.
- System-managed fields shall never be client-supplied.
- Business invariants remain the responsibility of the Domain Model.
- ReferenceValidator shall use the approved Workspace compatibility matrix and
  shall reject missing, ambiguous, inactive, inaccessible, cross-Project, or
  incompatible Workspace resolution.
- `shared_engineering` creation and reclassification shall return a validation
  failure while no dedicated shared Workspace capability exists.

## 14. Visibility Rules

The API shall expose only approved public fields.

Internal implementation details shall never be exposed.

The following fields are read-only:

- id
- organization_id
- version
- creator_id
- steward_id
- lifecycle
- authority_standing
- created_at
- updated_at

Authorization is deny-by-default, operation-specific, and scope-aware.

Authorization shall occur before disclosure and before mutation. Permission to
perform one operation does not imply permission to perform another operation.

Objects outside the actor's authorized scope shall not disclose their
existence and shall use the approved Protected Not Found outcome.

## 15. Error Handling

The API shall return standardized error responses.

Validation failures shall return validation errors.

Business rule violations shall return domain errors.

Unexpected failures shall return internal server errors.

The error response format shall follow the SATCO API standard.

The existing API error format shall represent these standardized categories:

- Authorization denied
- Protected Not Found
- Version Conflict
- Idempotency Conflict
- Invalid Domain Transition

## 16. Compatibility Rules

Backward compatibility shall be preserved for all published API contracts.

Breaking API changes require:

- A new PATCH document
- Architecture Review
- Explicit approval before implementation

## 17. Approval Gates

Implementation is authorized only after approval of:

- EngineeringObject Blueprint
- PATCH-023.1 EngineeringObject API Contract
- PATCH-023 EngineeringObject Application Layer
- AR-023 Architecture Review
- IRR-023 Implementation Readiness Review

## 18. Revision History

| Version | Date | Description |
|---------|------|-------------|
| 0.1 | YYYY-MM-DD | Initial API Contract |
| 1.0 | 2026-08-01 | Approved creation, concurrency, and command contract |
