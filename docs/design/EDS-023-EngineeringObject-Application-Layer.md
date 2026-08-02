# EDS-023 — EngineeringObject Application Layer

## Status

Accepted

## Purpose

Define the complete engineering design for PATCH-023 without implementing
source code. This EDS is subordinate to the EngineeringObject Blueprint,
PATCH-023, and PATCH-023.1.

## Governing Documents

- EngineeringObject Blueprint v1.0
- PATCH-022.3 Engineering Object Aggregate
- PATCH-023 EngineeringObject Application Layer
- PATCH-023.1 EngineeringObject API Contract
- AR-023 final Architecture Review
- SATCO Governance Model
- SATCO Development Lifecycle

## Scope

- five explicit Aggregate Root commands;
- Pydantic v2 request and response contracts;
- inward-owned application ports;
- repository and application-service boundaries;
- authenticated, deny-by-default authorization and visibility;
- optimistic concurrency;
- atomic aggregate, Audit, outbox, and idempotency persistence;
- explicit HTTP command/query contracts;
- stable application errors;
- focused unit, integration, migration, and regression validation.

## Non-Scope

- generic update;
- physical delete;
- arbitrary scope transfer;
- identifier or relationship management;
- search, bulk operations, frontend, or AI behavior;
- changes to persisted EngineeringObject fields or approved invariants;
- database changes beyond the approved Audit UUID reference, outbox,
  idempotency relation, and one additive migration;
- domain-specific coupling added to platform Core.

## Architecture

The Domain owns state, invariants, transitions, version advancement, and
Domain Event production. The Application Layer owns orchestration,
authorization coordination, reference validation, Unit of Work coordination,
and authorized mapping. Ports are inward-owned contracts. Infrastructure
implements ports. FastAPI remains a Transport adapter.

Domain and Application shall not depend on FastAPI, HTTP, SQLAlchemy Session,
or infrastructure implementations.

Authenticated actor Organization scope is supplied only by the trusted
PATCH-025 authentication dependency after active membership resolution. No
EngineeringObject request value may define or override that scope.

## Aggregate Commands

The only authorized Aggregate Root commands are:

- `create`;
- `reclassify`;
- `transition_lifecycle`;
- `transition_authority`;
- `transfer_steward`.

Each operation enforces Blueprint invariants, produces required Domain Events,
and advances version exactly once for a successful post-creation mutation.
Generic mutation and direct service-layer field assignment are prohibited.

## Creation Design

- Organization comes from the authenticated actor's active Organization scope.
- Project is client-selected and must be accessible.
- Workspace is resolved within that Project and compatible Discipline and must
  be explicitly authorized.
- Customer is derived from Project and may be null for an internal Project.
- Creator is the authenticated actor.
- Steward defaults to Creator; a requested alternate Steward requires an
  explicit AuthorizationPolicy allow decision and valid active reference.
- Lifecycle starts as `proposed`, authority as `draft`, and version as `1`.

### Workspace-Discipline Compatibility

ReferenceValidator shall apply this closed matrix:

| EngineeringObject discipline | Workspace discipline |
|---|---|
| `instrumentation` | `instrumentation` |
| `electrical` | `electrical` |
| `industrial_automation` | `control` |
| `shared_engineering` | No current compatible Workspace |

The `industrial_automation` to `control` mapping reconciles the approved EKG
classification vocabulary with the existing operational Workspace vocabulary;
it renames neither enum and creates no additional discipline.

The current single-Workspace foreign key cannot express explicitly authorized
multi-discipline/shared Workspace scope. Multiple Workspace memberships remain
independent authorization scopes and shall never be combined implicitly.
Therefore creation or reclassification to `shared_engineering` is rejected by
application reference validation until a dedicated shared-workspace capability
defines identity, scope, membership, authorization, and migration behavior.

## Application Ports

- `UnitOfWork`
- `EngineeringObjectRepository`
- `AuditRecorder`
- `DomainEventRecorder`
- `IdempotencyStore`
- `AuthorizationPolicy`
- `ReferenceValidator`
- `Clock`

The Repository loads complete aggregates within authorized scope and performs
expected-version persistence. It does not authorize, commit, publish events,
or perform generic updates.

## Atomic Persistence Design

One SQLAlchemy-backed Unit of Work owns one PostgreSQL transaction. A
successful command writes aggregate state, Audit evidence, outbox events, and
the idempotency outcome before one commit. Failure rolls back all four.

The additive persistence design is limited to:

- nullable UUID `audit_logs.entity_uuid`;
- `engineering_object_outbox`, containing durable event identity, aggregate
  UUID/version, event type, payload, occurrence time, and publication state;
- `engineering_object_idempotency`, containing actor, command, key, request
  fingerprint, status, aggregate UUID, authorized outcome, and timestamps;
- uniqueness preventing replay of the same actor/command/idempotency key.

Outbox publication occurs only after commit. Publication failure retains the
record for retry and does not reapply the command.

## Authorization and Visibility

Authorization is deny-by-default, operation-specific, scope-aware, and
evaluated before disclosure and mutation. AuthorizationPolicy consumes actor,
operation, scope, current state, and target state. It does not mutate the
aggregate. An inaccessible object produces Protected Not Found without
revealing existence.

## Validation Ownership

- Transport: syntax, types, required fields, request coherence.
- Application: authentication context, authorization, visibility, reference
  validity, idempotency, orchestration.
- Aggregate: classification compatibility, lifecycle and authority rules,
  invariants, command state change, version advancement.
- Persistence: foreign keys, controlled constraints, uniqueness, and
  compare-and-change enforcement.

## API Design

Queries:

- `GET /engineering-objects/{object_id}`
- `GET /projects/{project_id}/engineering-objects`

Commands:

- `POST /engineering-objects`
- `POST /engineering-objects/{object_id}/reclassifications`
- `POST /engineering-objects/{object_id}/lifecycle-transitions`
- `POST /engineering-objects/{object_id}/authority-transitions`
- `POST /engineering-objects/{object_id}/steward-transfers`

No PUT, generic PATCH, or DELETE endpoint is authorized.

## Error Contract

Stable categories are Validation Error, Authorization Denied, Protected Not
Found, Version Conflict, Idempotency Conflict, Invalid Domain Transition, and
Internal Server Error. Error mapping shall not reveal protected existence.

## Acceptance Criteria

- all five commands remain aggregate-owned;
- every post-creation mutation uses expected-version persistence;
- stale commands preserve state and emit no success Audit or Domain Event;
- duplicate idempotency delivery does not reapply a command;
- aggregate, Audit, outbox, and idempotency writes are atomic;
- unauthorized reads and mutations disclose no protected state;
- no generic update or physical delete exists;
- focused tests and the complete regression suite pass.

## Approval

EDS-023 is accepted subject to the independent EDS-023 Review and the exact
IDS-023 implementation boundary.
