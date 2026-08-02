# IDS-026 — Engineering Relationship Engine

## Status

Approved

## Purpose

Define the exact implementation boundary for approved PATCH-026. Implementation
shall not change an unlisted file or behavior without returning to governance.

## Governing Baseline

- approved PATCH-026
- accepted EDS-026 and PASS review
- AR-026 PASS
- PATCH-021.2 Engineering Relationship Vocabulary
- EngineeringObject Blueprint v1.0
- completed PATCH-023, PATCH-024, and PATCH-025
- Governance Model and Development Lifecycle

## Exact Authorized File Set

Modified files:

- `backend/app/enums/__init__.py`
- `backend/app/models/__init__.py`
- `backend/app/schemas/__init__.py`
- `backend/app/main.py`
- `backend/migrations/env.py`

New files:

- `backend/app/enums/engineering_relationship.py`
- `backend/app/models/engineering_relationship.py`
- `backend/app/models/engineering_relationship_command.py`
- `backend/app/schemas/engineering_relationship.py`
- `backend/app/ports/engineering_relationship.py`
- `backend/app/repositories/engineering_relationship_repository.py`
- `backend/app/repositories/engineering_relationship_unit_of_work.py`
- `backend/app/services/engineering_relationship_service.py`
- `backend/app/exceptions/engineering_relationship.py`
- `backend/app/api/v1/routers/engineering_relationships.py`
- `backend/migrations/versions/e02600000001_engineering_relationship_engine.py`
- `backend/tests/test_engineering_relationship_aggregate.py`
- `backend/tests/test_engineering_relationship_schemas.py`
- `backend/tests/test_engineering_relationship_repository.py`
- `backend/tests/test_engineering_relationship_service.py`
- `backend/tests/test_engineering_relationship_api.py`
- `backend/tests/test_engineering_relationship_transaction.py`
- `backend/tests/test_engineering_relationship_migration.py`
- `backend/tests/test_engineering_relationship_security.py`
- `backend/tests/test_engineering_relationship_traversal.py`

No other source, migration, test, configuration, or documentation file is
authorized during implementation.

## Aggregate and Enum Contract

Enums shall contain exactly the EDS-026 families, creatable types, and lifecycle
values and reuse EngineeringAuthorityStanding. No free-text or inverse-label
type is accepted.

Aggregate fields are:

- id UUID primary key;
- organization_id UUID;
- project_id positive integer;
- workspace_id positive integer derived from source object;
- source_object_id and target_object_id immutable UUIDs;
- relationship_family and relationship_type controlled strings;
- lifecycle and authority_standing controlled strings;
- evidence_references JSON array of unique UUID strings;
- version positive integer;
- creator_id and steward_id positive integers;
- reviewer_id and approver_id nullable positive integers;
- created_at and updated_at timezone-aware timestamps.

Creation starts proposed/draft/version 1. Commands and rules are exactly those
in EDS-026. Aggregate methods never query, authorize, transact, or depend on
frameworks.

## Schemas and Command Envelope

Pydantic v2 and ConfigDict are mandatory. Requests use extra=forbid; responses
use from_attributes where appropriate.

- create: source_object_id, target_object_id, relationship_family,
  relationship_type, optional steward_id, Evidence UUIDs, rationale;
- submission/review/approval/dispute/rejection: expected_version, rationale,
  Evidence UUIDs when applicable;
- lifecycle transition: target lifecycle, expected_version, rationale,
  replacement_relationship_id only for supersession, Evidence UUIDs;
- steward transfer: steward_id, expected_version, rationale;
- filters: family, type, lifecycle, authority, direction, workspace;
- pagination: page >=1 and size 1–100;
- traversal: direction, approved filters, max_depth 1–5, max_results 1–100,
  optional continuation token.

Actor, Organization, Reviewer ID, Approver ID, scope,
correlation ID, and idempotency ID are trusted server-derived/header context
and never arbitrary body fields. Mutation requests require correlation and
idempotency UUID headers.

`relationship_family` and `relationship_type` are both mandatory controlled
request values and form the canonical vocabulary discriminator. Neither may be
derived from the other. Every response, filter, command DTO, Domain Event,
Audit detail, and idempotency fingerprint carries both values. The pairs
(`instrumentation`, `monitored_by`) and (`automation`, `monitored_by`) are
valid and semantically distinct; `monitored_by` without a family is invalid.

Responses expose only authorized scalar state: id, Organization/Project/
Workspace IDs, source/target UUIDs, family, type, lifecycle, authority,
Evidence UUIDs, version, Creator/Steward/Reviewer/Approver
IDs, timestamps, and deterministic allowed_actions. allowed_actions is derived
from current state and operation-specific policy and grants no authority by
itself. List responses use items, total, page, size. Traversal responses
contain authorized nodes, relationships, bounded depth, truncation flag, and
continuation token without protected counts.

## Repository, Policies, and Unit of Work

Repository provides add, complete authorized-scope rehydration, expected-version
persistence, active-identity duplicate lookup, endpoint list, bounded
neighborhood, and bounded path operations. It never authorizes, commits,
publishes, performs generic update, or deletes.

ReferenceValidator loads both EngineeringObjects within actor Organization and
verifies lifecycle, authority qualification, same Project, Workspace policy,
classification compatibility, and visibility without transferring authority.
EvidenceValidator and ResponsibilityValidator apply EDS-026. AuthorizationPolicy
is deny-by-default and computes relationship visibility as the intersection of
both endpoint, every Evidence item, and applicable Workspace visibility. It
must complete these decisions before any relationship disclosure, return
Protected Not Found when any constituent is inaccessible, and must not emit a
persisted or response confidentiality label. CycleDetector uses
same-family/type-pair authorized reachability and the transaction advisory lock
for the approved acyclic set.

One UnitOfWork owns one Session and exposes repository, AuditRecorder,
DomainEventRecorder, and IdempotencyStore. It alone commits or rolls back.

## Migration Scope

Revision `e02600000001` has sole parent `e02700000001` and creates only:

1. `engineering_relationships` with the Aggregate fields above.
2. `engineering_relationship_outbox` with UUID id/event_id/aggregate_id,
   positive aggregate_version, event_type, schema_version, JSON payload,
   occurred_at, published_at, and created_at.
3. `engineering_relationship_idempotency` with UUID id, actor_id,
   command_type, idempotency_id, request_fingerprint, status, aggregate_id,
   authorized JSON result, and timestamps.

Foreign keys reference organizations, projects, engineering_workspaces,
engineering_objects, and users with RESTRICT behavior. Checks enforce approved
controlled values, positive version, source != target, family/type
compatibility, responsibility separation when populated, idempotency status,
and positive event version.

A partial unique index enforces the active identity on Organization, Project,
Workspace, source, target, family, and type where lifecycle is
proposed/current.
Indexes cover source and target within Organization/Project/Workspace,
type/lifecycle filters, outbox unpublished order, and idempotency lookup.
Cycle enforcement remains transactionally serialized application/repository
logic because SQL checks cannot express reachability.

Downgrade drops only these three tables and their owned indexes/constraints.
It does not change EngineeringObject, Organization, Workspace, Audit, or
existing PATCH-023 persistence. Clean upgrade, downgrade, and re-upgrade are
mandatory in an isolated database.

## Application Commands

Service methods map one-to-one to:

- CreateEngineeringRelationship
- SubmitEngineeringRelationshipForReview
- ReviewEngineeringRelationship
- ApproveEngineeringRelationship
- DisputeEngineeringRelationship
- RejectEngineeringRelationship
- TransitionEngineeringRelationshipLifecycle
- TransferEngineeringRelationshipSteward
- authorized get/list/neighborhood/path queries.

Every operation obtains trusted actor context, authorizes before disclosure,
validates references/policy, checks idempotency, invokes one Aggregate Root
command, stages all atomic effects, commits once, and maps authorized state.
Services do not duplicate aggregate transition rules.

## API Endpoints

- `POST /engineering-relationships` — create, HTTP 201.
- `GET /engineering-relationships/{relationship_id}`.
- `GET /engineering-objects/{object_id}/relationships`.
- `GET /engineering-objects/{object_id}/relationship-neighborhood`.
- `GET /engineering-objects/{object_id}/relationship-paths` with required
  target_object_id.
- `POST /engineering-relationships/{relationship_id}/submissions`.
- `POST /engineering-relationships/{relationship_id}/reviews`.
- `POST /engineering-relationships/{relationship_id}/approvals`.
- `POST /engineering-relationships/{relationship_id}/disputes`.
- `POST /engineering-relationships/{relationship_id}/rejections`.
- `POST /engineering-relationships/{relationship_id}/lifecycle-transitions`.
- `POST /engineering-relationships/{relationship_id}/steward-transfers`.

No PUT, generic PATCH, DELETE, bulk mutation, arbitrary traversal, or
unrestricted query endpoint is permitted.

## Stable Errors

- syntax/type/coherence or invalid reference → 422
  ENGINEERING_RELATIONSHIP_VALIDATION_ERROR;
- authorized disclosed denial → 403
  ENGINEERING_RELATIONSHIP_AUTHORIZATION_DENIED;
- absent/inaccessible relationship, endpoint, or path subject → 404 Protected
  Not Found with ENGINEERING_RELATIONSHIP_NOT_FOUND;
- active identity duplicate → 409 ENGINEERING_RELATIONSHIP_DUPLICATE;
- prohibited cycle → 409 ENGINEERING_RELATIONSHIP_CYCLE_REJECTED;
- stale expected version → 409 ENGINEERING_RELATIONSHIP_VERSION_CONFLICT;
- changed idempotency fingerprint → 409
  ENGINEERING_RELATIONSHIP_IDEMPOTENCY_CONFLICT;
- invalid lifecycle/authority/no-op → 409
  ENGINEERING_RELATIONSHIP_INVALID_DOMAIN_TRANSITION;
- unexpected failure → 500 ENGINEERING_RELATIONSHIP_INTERNAL_SERVER_ERROR
  without protected details.

## Tests and Validation

The exact test files cover aggregate matrices and invariants, enum/schema
strictness, repository rehydration/duplicates/concurrency, service ordering,
API/error contracts, atomic rollback, idempotency, migration/model match,
organization/project/workspace security, authorization-before-disclosure,
bounded traversal correctness/cycle safety/pagination/performance, existing
EngineeringObject/authentication tests, and full backend regression.

## Stop Conditions

Stop for an unlisted file/table/field/type/command/endpoint, non-EngineeringObject
endpoint, cross-Organization/Project link, unapproved cross-Workspace type,
weaker authorization, missing expected version, extra version increment,
non-atomic effect, generic update, physical delete, unbounded query, migration
drift, or failing regression.

## Approval

IDS-026 is approved for the exact contract above, but implementation remains
subject to an executable Implementation Plan-026 and IRR-026 READY verdict.
