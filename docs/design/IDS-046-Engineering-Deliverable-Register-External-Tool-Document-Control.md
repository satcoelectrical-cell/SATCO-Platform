# IDS-046 — Engineering Deliverable Register & External-Tool Document Control

## Status

**ACCEPTED / COMPLETE.** Exact implementation design for PATCH-046 V1.

## Closed contracts

`DeliverableActor(actor_id, organization_id)` is trusted context only.
`DeliverableScope(project_id, workspace_id?)` requires same-Organization
Project/Workspace authorization. `ExternalAuthority` is closed to `cad`,
`eplan`, `etap`, `spreadsheet`, `document`, `vendor_tool`, `other`.
`DeliverableStanding` is `planned|in_preparation|ready_for_review|reviewed|
issued|withdrawn|cancelled`; `RevisionStanding` is `draft|ready_for_review|
reviewed|issued|superseded|withdrawn`.

Create/update fields: code 1–64, title 1–200, discipline/type 1–80, purpose
optional <=2000, responsible_user_id optional positive integer, target_date
optional date, workspace/activity/milestone optional identity, external
authority and explicit Human rationale 1–2000. Revision fields: external label
1–80, optional source reference <=512, optional Supporting File UUID, target
standing when transitioning, expected deliverable/revision version and rationale.
All models forbid extras and canonical text normalization only normalizes line
endings and trim; it does not transform engineering meaning.

Closed outcomes are `success`, `protected_not_found`, `invalid_request`,
`version_conflict`, `idempotency_conflict`, `unavailable`. Protected/invalid/
unavailable outcomes are payload-free. Read success has exact summary/detail
and immutable history DTOs; counts are visible-only. List order is
`(target_date ASC NULLS LAST, code ASC, id ASC)`, page size 1–100, bounded
opaque continuation tied to actor/scope/query and expiry.

## Persistence and enforcement

Migration parent is `e04500000001`. Tables are `engineering_deliverables`,
`engineering_deliverable_revisions`, `engineering_deliverable_history`,
`engineering_deliverable_idempotency` and `engineering_deliverable_outbox`.
Database constraints enforce tenant/project/workspace coherence, unique
case-folded Project code, one current revision, monotonic sequence, immutable
historical revisions, legal standing changes and valid same-Project execution
references. Runtime role has DML-only grants; schema owner controls DDL,
functions and triggers. Repository never commits.

Every mutation obtains deterministic locks by UUID, checks expected version,
reserves/replays idempotency, rechecks Project authority and Supporting File
visibility immediately before mutation, stages history/Audit/outbox/replay,
flushes and commits once. Failure rolls back all primary state. Audit records
bounded category/version facts only and never file/object/reason plaintext.

## Integration and verification

Project/Execution/Suppporting-File authority is consumed through adapters or
application boundaries, never their repositories or Sessions. Tests must prove
tenant isolation, transition/immutability and direct SQL guards, concurrency,
replay, audit/rollback, file protected access, truthful absent legacy Project,
pagination bounds, API context/serialization, real-data frontend and external
authoring non-claim. No Evidence mutation/link, transmittal, authoring or
PATCH-047+ endpoint exists.
