# Implementation Plan-046 — Engineering Deliverable Register & External-Tool Document Control

## Status

**ACCEPTED / COMPLETE.** Four independently reviewable batches implement only
IDS-046.

## Batch 1 — Contracts, aggregate and persistence

Create deliverable enums/models/schemas/ports/exceptions, migration,
repository and focused contract/model/migration/role tests. Establish exact
scope/revision/history/idempotency/outbox guards. Exclude service, canonical
adapters, API and UI.

## Batch 2 — Commands, canonical integration and reliability

Create Project/Execution/Supporting-File adapters, UoW and service. Implement
create/update, new revision and transition with final authority/file rechecks,
Audit/outbox/idempotency/concurrency/rollback. Exclude broad reads, transport
and UI.

## Batch 3 — Reads, transport and Project UI

Add protected list/get/history, continuation validation, request-scoped
composition, thin routes/main registration and a real-data Project Deliverable
Register component/types/client/styles with backend/API/frontend tests. Exclude
dashboard redesign, generic EDMS and PATCH-047+.

## Batch 4 — Final evidence

Run focused and adjacent regressions, one backend suite, one frontend suite,
migration round trip/sole head, type/build/static/security/scope/secret checks.
Create validation/final-review evidence only. Any design-required failure stops
the batch.

Every batch requires a manifest, independent review, remediation/re-review and
Human acceptance before the next one.
