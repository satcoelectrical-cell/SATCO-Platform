# PATCH-023 — EngineeringObject Application Layer

## 1. Document Control

| Field | Value |
|-------|-------|
| Document ID | PATCH-023 |
| Title | EngineeringObject Application Layer |
| Status | Approved — Implementation Authorized by IRR-023 |
| Owner | SATCO Platform Architecture Team |
| Architecture Style | Docs-First Architecture |
| Implementation | Authorized within the approved IDS-023 file set |
| Last Updated | 2026-08-01 |

## 2. Status

This document defines the implementation requirements for the EngineeringObject Application Layer.

Backend implementation is authorized only within the approved IDS-023 file set
and IRR-023 readiness decision.

## 3. Objective

The objective of PATCH-023 is to introduce the complete EngineeringObject Application Layer while preserving the existing approved Domain Model.

This PATCH defines the required application components, implementation boundaries, acceptance criteria, and implementation authorization process before any backend code is created.

## 4. Governing Documents

The implementation of this PATCH shall comply with the following governing documents:

- SATCO Constitution
- System Architecture
- Coding Standards
- EngineeringObject Blueprint
- Approved Architecture Decision Records (ADRs)
- Current EngineeringObject Domain Model

## 5. Architectural Context

EngineeringObject is the central engineering entity within the SATCO Platform domain.

This PATCH introduces only the Application Layer responsible for orchestrating EngineeringObject use cases.

The approved Domain Model, persistence model, and database schema are outside the scope of this PATCH and shall remain unchanged.

Dependency direction is:

```text
Domain
↓
Application
↓
Ports
↓
Infrastructure
↓
Transport
```

Domain and Application shall never depend on:

- FastAPI
- SQLAlchemy Session
- HTTP
- Infrastructure implementations

## 6. Scope

EngineeringObject Application Layer includes:

- Pydantic request schemas
- Pydantic response schemas
- Repository implementation
- Application service layer
- API router
- Dependency injection wiring
- Router registration
- Application-layer validation
- Unit and integration tests related to the application layer
- minimum persistence additions required for atomic command outcomes

Required application ports are:

- UnitOfWork
- EngineeringObjectRepository
- AuditRecorder
- DomainEventRecorder
- IdempotencyStore
- AuthorizationPolicy
- ReferenceValidator
- Clock

Every successful mutation shall atomically persist the EngineeringObject
aggregate state, required Audit outcome, Domain Events, and idempotency
outcome through the UnitOfWork.

The approved persistence approach uses one SQLAlchemy-backed UnitOfWork and one
PostgreSQL transaction. The transaction shall write:

- the EngineeringObject aggregate state;
- one accountable Audit record using a nullable UUID entity reference;
- durable Domain Event outbox records;
- the command idempotency result.

The minimum authorized persistence additions are:

- one nullable `entity_uuid` column on the existing `audit_logs` relation;
- one `engineering_object_outbox` relation;
- one `engineering_object_idempotency` relation;
- one additive Alembic migration covering only these additions.

No component may commit independently inside this transaction. Event
publication occurs after commit from the durable outbox and shall not reapply
the command.

The Application Service shall:

- obtain the authenticated actor;
- coordinate authorization;
- validate referenced identities and scope;
- load the aggregate within authorized scope;
- invoke one explicit EngineeringObject aggregate command;
- coordinate the atomic UnitOfWork;
- coordinate Audit, Domain Event, and idempotency persistence;
- map only authorized state into the response.

The Application Service shall not:

- implement aggregate transition rules;
- directly mutate ORM fields;
- commit through repositories;
- expose unauthorized state.

## 7. Explicit Non-Scope

This PATCH explicitly excludes:

- Changes to existing persisted EngineeringObject fields or approved invariants
- Database changes beyond the three approved atomic-command persistence additions
- SQLAlchemy persisted-field changes beyond the nullable Audit UUID reference and the two approved command-record models
- Alembic migrations beyond the single approved additive PATCH-023 migration
- Authentication redesign
- Authorization redesign
- Frontend implementation
- AI module implementation

Adding the explicit Aggregate Root command operations required by the approved
EngineeringObject Blueprint is permitted and required. Generic mutation
remains prohibited.

The approved Aggregate Root operations are:

- `create`;
- `reclassify`;
- `transition_lifecycle`;
- `transition_authority`;
- `transfer_steward`.

These operations may be added to the existing EngineeringObject Aggregate
Root. Existing persisted EngineeringObject fields, approved invariants, and
unrelated Domain Model structure shall remain unchanged.

## 8. Dependencies

Implementation depends on:

- Approved EngineeringObject Blueprint
- PATCH-023.1 EngineeringObject API Contract, as a subordinate dependency
- Approved Architecture Review
- Existing EngineeringObject Domain Model
- Existing Repository Architecture
- SATCO Coding Standards
- Approved ADRs
- implemented PATCH-025 Authenticated Organization Context

Authority is one-way:

```text
EngineeringObject Blueprint
→ PATCH-023 EngineeringObject Application Layer
→ PATCH-023.1 EngineeringObject API Contract
```

Authority shall never flow in the reverse direction.

## 9. Deliverables

The expected deliverables are:

- EngineeringObject schemas
- EngineeringObject repository
- EngineeringObject service
- EngineeringObject API router
- Router registration
- UnitOfWork
- EngineeringObjectRepository port and implementation
- AuditRecorder
- DomainEventRecorder
- IdempotencyStore
- AuthorizationPolicy
- ReferenceValidator
- Clock
- EngineeringObject Domain Event outbox persistence
- EngineeringObject idempotency-result persistence
- nullable UUID Audit entity reference
- one additive Alembic migration for the approved atomic persistence additions
- Automated tests
- Updated implementation documentation

The EngineeringObject repository contract shall:

- load only authorized scope;
- fully rehydrate the EngineeringObject aggregate;
- perform expected-version persistence;
- never perform authorization decisions;
- never commit transactions;
- never publish Domain Events;
- never perform generic update operations.

## 10. Acceptance Criteria

Implementation is accepted only if all of the following are satisfied:

- All application-layer components compile successfully.
- Existing EngineeringObject Domain Model remains unchanged.
- No database schema modifications are introduced.
- Repository follows the approved repository architecture.
- Service layer contains business orchestration only.
- API endpoints conform to the approved API contract.
- Unit tests pass.
- Integration tests pass.
- Existing functionality remains unaffected.
- Repository loading is restricted to authorized scope.
- Repository operations fully rehydrate the EngineeringObject aggregate.
- Repository mutations use expected-version persistence.
- Repository operations perform no authorization decisions, transaction commits, Domain Event publication, or generic updates.
- Every successful mutation atomically persists aggregate state, Audit, Domain Events, and its idempotency outcome.
- Application services invoke one explicit Aggregate Root command and do not duplicate aggregate rules or directly mutate ORM fields.

## 11. Risks and Constraints

The following constraints apply:

- Docs-First Architecture is mandatory.
- No implementation before formal approval.
- Domain Model modifications are prohibited.
- Architectural decisions require documented approval.
- Backward compatibility shall be preserved.
- Existing coding standards shall be followed.

## 12. Approval Gates

Implementation may begin only after approval of:

- EngineeringObject Blueprint
- Architecture Review
- PATCH-023
- Engineering Design Specification (EDS)
- Interface Design Specification (IDS)
- Implementation Readiness Review (IRR)

## 13. Implementation Authorization

Status:

READY FOR IMPLEMENTATION

Authorization is limited to the approved IDS-023 file set and IRR-023 decision.

## 14. Implementation Strategy

Implementation sequence:

1. Aggregate command methods
2. Atomic persistence migration and models
3. Ports and schemas
4. Repository and Unit of Work adapters
5. Application Service
6. API Router and registration
7. Tests
8. Validation
9. Documentation Update

## 15. Future Phases

Future enhancements may include:

- Advanced search
- Bulk operations
- Version history
- AI-assisted engineering workflows

## 16. Revision History

| Version | Date | Description |
|---------|------|-------------|
| 0.1 | YYYY-MM-DD | Initial draft |
| 1.0 | 2026-08-01 | Approved contract and IRR-023 implementation authorization |
