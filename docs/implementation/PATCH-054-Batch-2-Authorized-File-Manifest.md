# PATCH-054 — Batch 2 Authorized File Manifest

Status: **RECONCILED / IMPLEMENTATION NOT STARTED**

Authority: Human-authorized PATCH-054 Batch-2 manifest reconciliation only.
The accepted ADR-027, EDS-054, IDS-054, Implementation Plan-054, and Batch-1
history remain authoritative and are not reopened by this record.

## Original bounded Batch-2 boundary

The original Batch-2 boundary contains the four primary paths and the shared
hunks assigned to Batch 2 by the accepted IDS/Plan.  Responsibilities below
are limited to SRC-01..02, AST-01..03, the 19 Batch-2 vectors, and their focused
Level A/B/C evidence.

| # | Action | Exact path | Narrow Batch-2 responsibility |
|---:|---|---|---|
| 1 | MODIFY | `backend/app/schemas/standards.py` | Strict source, display, assertion, and safe result contracts |
| 2 | MODIFY | `backend/app/models/standards.py` | Source snapshot and assertion read projections only |
| 3 | MODIFY | `backend/app/models/standards_command.py` | Immutable Batch-2 command/value records only |
| 4 | MODIFY | `backend/app/ports/standards.py` | Provider, object-store, and Batch-2 persistence protocols |
| 5 | MODIFY | `backend/app/repositories/standards_repository.py` | Scoped source/assertion persistence and protected resolver call |
| 6 | MODIFY | `backend/app/repositories/standards_unit_of_work.py` | Accepted three-phase transaction, locks, Audit/outbox/idempotency |
| 7 | MODIFY | `backend/app/services/standards_service.py` | Deterministic bounded retrieval/display/assertion lifecycle |
| 8 | MODIFY | `backend/app/dependencies/standards.py` | Batch-2 composition and authorization policy only |
| 9 | MODIFY | `backend/app/api/v1/routers/standards.py` | SRC-01..02 and AST-01..03 routes only |
| 10 | MODIFY | `backend/app/standards/providers.py` | Static allowlisted provider bindings only |
| 11 | CREATE | `backend/app/adapters/standard_source_object_store.py` | Narrow private exact-key object wrapper |
| 12 | CREATE | `backend/app/adapters/standard_source_providers.py` | Official/licensed/customer source adapters only |
| 13 | MODIFY | `backend/app/core/config.py` | False-by-default provider/object/key settings and safe validation |
| 14 | MODIFY | `backend/tests/test_standards_service.py` | Batch-2 deterministic rules and UoW evidence |
| 15 | MODIFY | `backend/tests/test_standards_repository.py` | Scope, locks, persistence, Audit/outbox/idempotency evidence |
| 16 | MODIFY | `backend/tests/test_standards_security.py` | Rights, tenant, handle, DB, and unsafe-content attacks |
| 17 | MODIFY | `backend/tests/test_standards_api.py` | Exact SRC/AST route and safe failure contracts |
| 18 | CREATE | `backend/tests/test_standards_retrieval.py` | Provider/object/handle/integrity/limit evidence |
| 19 | CREATE | `backend/tests/test_standards_assertions.py` | Assertion lifecycle and rights propagation evidence |

No other original Batch-2 implementation path is authorized.

## Append-only reconciliation — B2-054-MAJ-02

Pre-implementation inspection confirmed that accepted Batch-2 semantics require
signed, actor/Organization/Project/operation/purpose/rights-version-bound opaque
handles, but `backend/app/standards/handles.py` was incorrectly assigned only
to B1/B4/B5 in the frozen path ownership.  Implementing that accepted Batch-2
behavior in dependencies, schemas, adapters, or another substitute module
would violate the canonical ownership boundary.

The reconciled manifest adds exactly one path:

| Action | Exact path | Strictly limited responsibility |
|---|---|---|
| MODIFY | `backend/app/standards/handles.py` | Implement only the accepted Batch-2 signed opaque source/snapshot/assertion handle codec and verification boundary, plus application-side protected provider-token seal/open using domain-separated AES-GCM key derivation and authenticated associated data; include exact actor, Organization, Project, operation, purpose, rights version/digest, key version, expiry, provider, source, and integrity bindings. |

The original 19 paths remain unchanged.  The reconciled future Batch-2
implementation/test boundary is **20 paths**.  This reconciliation does not
implement the codec or any Batch-2 behavior; implementation requires its
separate governed authority and must use the repository's protected database
resolver rather than direct ciphertext SELECT.

## Mandatory firewalls and stop conditions

- No arbitrary URL, browser, scraper, whole-standard repository, public object
  URL, generic raw-file endpoint, live provider in tests, or automatic retry.
- No plaintext source/provider handle, object key, credential, rights term,
  prompt, excerpt, or unsafe provider error in API, log, Audit, outbox, or
  idempotency payloads.
- No assertion self-verification, AI call, applicability/package behavior,
  Technical Report integration, frontend, Batch 3+, PATCH-055+, deployment,
  push, or accepted design rewrite.
- Stop for any additional path, semantic change, protected-column direct
  runtime SELECT, loss of fail-closed behavior, or inability to prove the exact
  8-fragment, 8192-byte item, 32768-byte aggregate, and 32-assertion bounds.

## Reconciliation disposition

- ADR reopening: **NO**
- EDS reopening: **NO**
- IDS reopening: **NO**
- Implementation Plan reopening: **NO**
- Append-only Batch-2 manifest reconciliation: **YES — this record**
- Batch-2 implementation: **NOT STARTED by this reconciliation**
- Batch 3 / PATCH-055 authority: **NONE**
