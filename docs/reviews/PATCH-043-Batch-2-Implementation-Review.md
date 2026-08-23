# PATCH-043 Batch 2 Independent Implementation Review

## Verdict

**PASS — Batch 2 ACCEPTED / COMPLETE.**

## Scope reviewed

S05–S08 only: private object-store/scanner adapters, Supporting File data-plane
service, same-session UoW, reservation/finalization/withdrawal, bounded
reconciliation, idempotency, Audit and outbox. No Evidence/Technical Report/
Organizational Memory integration, read/download routes, transport, frontend or
Batch 3 capability was introduced.

## Findings and disposition

| ID | Severity | Finding | Disposition |
|---|---|---|---|
| B2-MAJ-01 | Major | The initial real-race test used prerequisite data held in the fixture transaction, so independent PostgreSQL worker sessions could not be relied upon to observe it. | **RESOLVED**: the test creates committed isolated Organization/Project/reservation setup, synchronizes two independent sessions with a barrier, and exercises the real UoW, repository and unique idempotency constraint. |
| B2-MIN-01 | Minor | Test cleanup/global assertions were not aligned with immutable durable test records. | **RESOLVED**: assertions now bind to the generated Project/actor scope; the real race uses an isolated Organization and does not weaken immutable-asset guards. |

## Independent evidence

- real PostgreSQL same-key concurrent finalization: **1 passed**;
- complete focused Batch 2 Supporting File suite: **24 passed**;
- evidence includes one effective Asset mutation, one completed
  `SupportingFileIdempotencyRecord`, one `SupportingFileOutboxRecord`, and one
  `AuditLog` for two concurrent same-key/same-fingerprint requests;
- losing request resolves to the authorized persisted replay with no escaped
  `IntegrityError`; cross-Organization replay remains protected;
- first execution, exact replay, fingerprint conflict, scan/quarantine,
  object-key, rollback, Audit failure, outbox failure and reconciliation paths
  are covered by the focused suite;
- static compilation: PASS; Alembic sole head: `e04300000001`; `git diff
  --check`: PASS.

## Boundary result

Database uniqueness remains the correctness boundary; no process-local lock,
mock session or sequential substitute is used for concurrency proof. Repository
commit ownership remains absent and the real `SqlAlchemySupportingFileUnitOfWork`
keeps the asset, idempotency, Audit and outbox writes atomic. The private key,
digest, scanner and quarantine rules remain unchanged. No Critical or unresolved
Major finding remains.

## Acceptance record

Standing Human implementation authority accepts Batch 2 after this independent
review. Batch 3 is not started and has no authority.

## Append-only implementation-time reopening

The preceding PASS reflected the evidence then reviewed and is preserved. A
subsequent IDS-conformance audit identified **B2-RR-MAJ-01** (missing accepted
authenticated scanner-principal/result-recording/retry contract) and
**B2-RR-MAJ-02** (engine/signature fields lacked an authenticated provider
result boundary). Batch 2 was reopened and is **NOT ACCEPTED** until a fresh
independent PASS against the focused IDS amendment. This does not rewrite the
earlier review.

## Focused scanner-security re-review disposition

The standalone focused re-review records **PASS** with B2-RR-MAJ-01 and
B2-RR-MAJ-02 resolved by authenticated scanner-principal, provider-attestation,
replay, bounded-retry and real persistence evidence. Batch 2 is again
**ACCEPTED / COMPLETE** under standing Human authority.
