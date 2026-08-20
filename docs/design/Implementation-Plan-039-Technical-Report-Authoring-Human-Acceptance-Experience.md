# Implementation-Plan-039 — Technical Report Authoring & Human Acceptance Experience

## Status and Scope

Status: **ACCEPTED / COMPLETE** after Independent Plan Review PASS and standing
Human acceptance. Four independently reviewable batches implement only the
accepted IDS-039. No migration is planned.

## Batch 1 — Contextual Capture Provenance Foundation (S01–S02)

- S01 adds strict source-candidate response contracts and an application-owned
  adapter over the canonical Capture application service.
- S02 adds the authenticated bounded read route and backend evidence for scope,
  lifecycle, deterministic identity/digest, bounds, and non-disclosure.

Expected production surfaces: Technical Report schema/router plus one adapter.
Expected tests: focused productization/security API tests and PATCH-032/Capture
regressions. Stop for direct foreign persistence, unsupported Capture context,
contract change, partial disclosure, or migration need.

## Batch 2 — Report Authoring and Revision Experience (S03–S05)

- S03 extends frontend typed API contracts for candidates, Report details, and
  existing mutation endpoints.
- S04 replaces manual-ID Report summary UI with authorized Project/Workspace
  selectors, source selection, draft authoring, detail, and revision.
- S05 adds Project/Capture contextual entry and focused workflow/security tests.

Expected surfaces: frontend types/client, Reports page, Project page, routes,
styles, and focused tests. Stop for browser-generated provenance, invented
authority, new backend mutation, fake production data, or inaccessible flow.

## Batch 3 — Human Acceptance and Continuation (S06–S08)

- S06 implements explicit exact-revision acceptance review and immutable
  accepted rendering.
- S07 deep-links real Command Center Report rows and preserves Project/
  Workspace continuation.
- S08 verifies stale conflict, protected outcomes, AI/Human separation, and
  accepted-control absence.

Expected surfaces remain the Batch 2 frontend modules and focused tests. Stop
for synthesized rationale/confirmation, accepted editing, synthetic review
state/count, or authorization in presentation.

## Batch 4 — UX Hardening and Final Evidence (S09–S11)

- S09 validates accessibility, responsive composition, bounded requests,
  performance, real-data-only, and exact scope.
- S10 runs focused backend/frontend, adjacent, full backend, full frontend,
  build/type/static, security, secrets, and diff checks.
- S11 packages review/validation evidence and final-review readiness.

Only manifests, review/evidence, PATCH status, and strictly necessary existing
test/frontend surfaces may change. Any technical failure requiring broader
design stops the batch; ordinary defects return to their owning batch.

## Dependency and Review Rules

Batches execute 1→2→3→4. Each has an exact Authorized File Manifest,
implementation, focused validation, Independent Review, remediation/re-review
loop, and Human Batch Acceptance. Memory mutation, Report AI, broad provenance,
Context/Evidence workbenches, migration/persistence, publication, generic
workflow, and PATCH-040 are excluded from every batch.
