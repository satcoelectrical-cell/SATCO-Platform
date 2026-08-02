# IDS-023 — EngineeringObject Application Layer

## Status

Approved

## Purpose

Define the exact implementation contract for PATCH-023. Implementation shall
not change any file outside this IDS without returning to governance.

## Governing Baseline

- approved EngineeringObject Blueprint v1.0;
- PATCH-022.3;
- approved PATCH-023 and PATCH-023.1;
- AR-023 PASS;
- accepted EDS-023 and EDS-023 Review;
- current Governance Model and Development Lifecycle.
- implemented PATCH-025 trusted Organization-context contract.

## Exact Authorized File Set

Modified files:

- `backend/app/models/engineering_object.py`
- `backend/app/models/audit_log.py`
- `backend/app/models/__init__.py`
- `backend/app/schemas/__init__.py`
- `backend/app/main.py`

New files:

- `backend/app/models/engineering_object_command.py`
- `backend/app/ports/__init__.py`
- `backend/app/ports/engineering_object.py`
- `backend/app/schemas/engineering_object.py`
- `backend/app/repositories/engineering_object_repository.py`
- `backend/app/repositories/engineering_object_unit_of_work.py`
- `backend/app/services/engineering_object_service.py`
- `backend/app/exceptions/engineering_object.py`
- `backend/app/api/v1/routers/engineering_objects.py`
- `backend/migrations/versions/e02300000001_engineering_object_command_persistence.py`
- `backend/tests/test_engineering_object_aggregate_commands.py`
- `backend/tests/test_engineering_object_schemas.py`
- `backend/tests/test_engineering_object_repository.py`
- `backend/tests/test_engineering_object_service.py`
- `backend/tests/test_engineering_object_api.py`
- `backend/tests/test_engineering_object_transaction.py`

No other source, migration, test, configuration, or documentation file is
authorized during implementation.

## Aggregate Contract

`EngineeringObject` receives only `create`, `reclassify`,
`transition_lifecycle`, `transition_authority`, and `transfer_steward` command
operations. Identity, Creator, creation timestamp, persisted field definitions,
and approved invariants remain unchanged. The operations consume validated
command context and controlled time, return required Domain Events, and never
open transactions or query infrastructure.

## Schemas

Pydantic v2 with `ConfigDict` is mandatory. Request models use
`extra="forbid"`; response models use `from_attributes=True` where applicable.
Enums are imported from `app.enums`.

Authorized schemas:

- `EngineeringObjectBase`: family, discipline, object_type.
- `EngineeringObjectCreate`: project_id, family, discipline, object_type,
  optional steward_id, non-empty rationale, optional Evidence references.
- `ReclassifyEngineeringObjectRequest`: complete target classification,
  positive expected_version, rationale, Evidence references.
- `TransitionEngineeringObjectLifecycleRequest`: target lifecycle, positive
  expected_version, rationale, Evidence references, replacement UUID only when
  required by supersession.
- `TransitionEngineeringObjectAuthorityRequest`: target authority standing,
  positive expected_version, rationale, Evidence references.
- `TransferEngineeringObjectStewardRequest`: target steward_id, positive
  expected_version, rationale.
- `EngineeringObjectResponse`: all approved aggregate fields as scalar IDs and
  controlled enums.
- `EngineeringObjectListResponse`: items, total, page, size.

Correlation identifier and idempotency identifier are required transport
headers. Actor and authorization contexts are derived from trusted server-side
dependencies and never accepted as arbitrary body fields.

The router shall obtain `AuthenticatedActor.organization_id` exclusively from
the PATCH-025 dependency. Missing, disabled, ambiguous, or inaccessible active
membership prevents service invocation and returns the stable PATCH-025 error.

## Repository and Unit of Work

`EngineeringObjectRepository` provides authorized-scope load, scoped list,
add, complete rehydration, and expected-version persistence. Compare-and-change
matches aggregate UUID and expected version. No matching version returns a
conflict without mutation.

The Unit of Work begins one transaction and exposes Repository, AuditRecorder,
DomainEventRecorder, and IdempotencyStore implementations sharing one Session.
Only UnitOfWork commits or rolls back.

Audit recording uses `entity="ENGINEERING_OBJECT"` and `entity_uuid`. Audit
details contain authorized command, scope, rationale, actor, correlation,
idempotency, prior/result version, and bounded before/after facts.

Outbox and idempotency payloads must not contain unauthorized or confidential
Evidence content.

## Application Service Commands

The service exposes one method per canonical command plus authorized get/list
queries. Each command performs this order:

1. obtain authenticated actor and command metadata;
2. obtain an AuthorizationPolicy decision before disclosure;
3. validate Project, Workspace, Customer, Organization, User, and Evidence
   references as applicable;
4. reserve or replay-check the idempotency key;
5. load or create one aggregate;
6. validate expected version for post-creation commands;
7. invoke exactly one Aggregate Root command;
8. stage aggregate, Audit, outbox events, and idempotency outcome;
9. commit once through UnitOfWork;
10. reload and map only authorized response state.

The service does not encode transition matrices or mutate ORM fields directly.

### ReferenceValidator Compatibility Contract

ReferenceValidator shall resolve exactly one visible Workspace within the
selected Project using this immutable compatibility mapping:

- `instrumentation` → `instrumentation`;
- `electrical` → `electrical`;
- `industrial_automation` → `control`.

Resolution shall fail without disclosure when the Workspace is absent,
ambiguous, outside the Project, inactive for the operation, or inaccessible to
the actor. Authorization remains operation-specific and is evaluated before
disclosure. The mapping grants no membership or cross-Workspace access.

`shared_engineering` has no compatible Workspace in the current model.
ReferenceValidator shall reject creation and reclassification to that
discipline with the stable Validation Error category. It shall not select an
arbitrary discipline Workspace, combine memberships, or create a Workspace.
Support requires separately approved shared-workspace governance and is not an
implementation choice within IDS-023.

## API Endpoints

- `POST /engineering-objects` → CreateEngineeringObject, HTTP 201.
- `GET /engineering-objects/{object_id}` → authorized current state.
- `GET /projects/{project_id}/engineering-objects` → authorized paginated list.
- `POST /engineering-objects/{object_id}/reclassifications`.
- `POST /engineering-objects/{object_id}/lifecycle-transitions`.
- `POST /engineering-objects/{object_id}/authority-transitions`.
- `POST /engineering-objects/{object_id}/steward-transfers`.

No PUT, generic PATCH, or DELETE route is permitted.

## Authorization and Visibility

Every operation calls AuthorizationPolicy with actor, operation, scope,
current state, and target state. Default is deny. Repository filtering and
application decisions must agree. Inaccessible UUIDs return Protected Not
Found. Authorization Denied is used only when disclosure of the resource and
the denial is itself authorized.

## Concurrency and Idempotency

Creation has no expected version. Each post-creation mutation requires a
positive expected version and increments once. Version conflict rolls back and
stages no success Audit, event, or idempotency success result.

Idempotency uniqueness is actor plus command type plus key. An exact committed
retry returns the authorized recorded outcome without mutation. Reuse with a
different request fingerprint returns Idempotency Conflict.

## Stable Error Mapping

- request syntax/type/coherence → 422 Validation Error;
- authorized policy denial → 403 Authorization Denied;
- absent or inaccessible resource → 404 Protected Not Found;
- stale expected version → 409 Version Conflict;
- conflicting idempotency reuse → 409 Idempotency Conflict;
- prohibited aggregate transition → 409 Invalid Domain Transition;
- unexpected failure → 500 Internal Server Error without protected details.

## Migration Contract

Revision `e02300000001` is additive and has the current repository head as its
single down revision. It adds nullable `audit_logs.entity_uuid`, the outbox
relation, and the idempotency relation with required indexes, checks, foreign
keys where compatible, and uniqueness. It changes no EngineeringObject column.

Downgrade removes only these additions and is exercised only in the isolated
PATCH-023 validation database after confirming no required production data is
at risk.

## Test Contract

- aggregate command transitions, invariants, immutable fields, versions, and
  events;
- schema extra-field rejection, enum typing, command envelopes, and responses;
- authorized scope, complete rehydration, filtering, and compare-and-change;
- service ordering, deny-by-default policy, reference validation, and no direct
  mutation;
- endpoint success and stable error mapping;
- atomic rollback when Audit, outbox, idempotency, or aggregate persistence
  fails;
- idempotent retry and conflicting reuse;
- migration upgrade, constraints, downgrade, and re-upgrade;
- complete backend regression.

## Stop Conditions

Stop and return to IDS governance if implementation requires an unlisted file,
new persisted EngineeringObject field, new command, generic update, physical
delete, authorization redesign, non-atomic outcome, additional migration, or
weaker Blueprint invariant.

## Approval

IDS-023 is approved for the exact file set and behavior above, subject to an
IRR-023 verdict of `READY FOR IMPLEMENTATION`.
