# Implementation-Plan-055 — Commercial Evidence Workbench & Minimum Retention Governance

## 1. Status and authority

| Field | Value |
|---|---|
| Date | 2026-09-14 |
| PATCH | PATCH-055 — Commercial Evidence Workbench & Minimum Retention Governance |
| PATCH state | REGISTERED / OPEN |
| ADR-028 | HUMAN ACCEPTED / AUTHORITATIVE |
| EDS-055 | HUMAN ACCEPTED / AUTHORITATIVE |
| IDS-055 | HUMAN ACCEPTED / AUTHORITATIVE; QG-4 PASS |
| Plan candidate | DRAFT / UNDER INDEPENDENT READINESS REVIEW |
| Implementation | NOT STARTED / NOT AUTHORIZED |
| Migration | REQUIRED BY IDS; NOT CREATED / NOT EXECUTED |
| Required migration | `e05500000001`, parent `e05400000006` subject to sole-head preflight |
| Stage / commit / push | NOT AUTHORIZED |
| PATCH-056+ | NOT STARTED / NOT AUTHORIZED |

This Plan converts accepted IDS-055 into bounded executable checkpoints only. It does not change ADR/EDS/IDS semantics and grants no implementation authority.

## 2. Readiness preflight

Before any implementation authority, record repository HEAD/branch/status and preserve every unrelated dirty hunk. Confirm `e05400000006` remains the sole Alembic head. If the head differs, STOP and return to IDS/Plan reconciliation; do not create a merge revision.

Confirm PostgreSQL test infrastructure, private Supporting File object-store test double, existing Evidence/Supporting File authorization seams, and frontend Project route composition are available. Production/customer databases and live object storage are forbidden for qualification.

## 3. Exact change boundary

Create only the backend files named by accepted IDS-055 section 31.6, plus its one migration. Existing backend modifications are limited to `backend/app/main.py` and `backend/app/models/__init__.py`. Existing Evidence and Supporting File backend owners are consumed unchanged.

Create only the frontend files named by IDS-055 section 31.6. Existing frontend modifications are limited to `frontend/src/components/SupportingEvidencePanel.tsx` and `frontend/src/pages/ProjectsPage.tsx`.

Test paths are exactly `backend/tests/test_patch055_commercial_evidence_retention.py`, `backend/tests/test_patch055_retention_migration.py`, and `frontend/src/test/evidence-workbench-retention.test.tsx`.

No opportunistic refactor, generic EDMS work, OCR/extraction, physical purge, new role, new Evidence lifecycle, Report/Memory rewrite, or PATCH-056 work is permitted.

## 4. Checkpoint A — domain and persistence foundation

Implement closed retention/hold/disposition/export/recovery vocabularies, typed RetentionSubject, canonical digests, strict DTO/domain validation, and `RetentionGovernanceHeadV1` projection contract.

Create only the eight PATCH-055 persistence tables frozen by IDS-055. Reuse shared AuditLog. The migration remains additive and creates no legacy retention history.

Qualification must prove fresh install, populated upgrade, exact constraints/indexes, one current head, at-most-one active hold, safe rollback/forward-repair behavior, re-upgrade, and one Alembic head.

## 5. Checkpoint B — application governance and security

Implement repository/UoW/service composition with authorization-before-lookup, server-derived Organization scope, exact Project/Workspace predicates, expected-version concurrency, three-attempt bounded retry where applicable, and capability-owned idempotency/outbox atomicity.

Implement retention policy replacement, append-only hold placement/release, deterministic eligibility, Human disposition decision, legacy `not_established`, and fail-safe `indeterminate`. No operation may delete bytes or mutate Evidence standing, accepted Report provenance, or Memory provenance.

Focused exit: retention/hold/security/concurrency/idempotency vectors pass on isolated PostgreSQL; foreign/forbidden/protected-absent cases are disclosure-equivalent; audit/outbox contains safe metadata only.

## 6. Checkpoint C — transport, export, and recovery

Expose only the exact IDS routes/DTOs/status mapping and `Idempotency-Key` header contract. Implement Workbench composition without raw-ID entry.

Implement private governed export with 1 MiB streaming chunks, existing per-file byte bound, aggregate export bound, exact digest/byte receipt, current reauthorization, and protected content route. Object-store coordinates never enter public DTO/Audit/outbox/logs.

Implement one-subject recovery through the accepted resolver seam. Recovery restores availability only; unavailable/unrecoverable bytes preserve safe historical provenance and never revive withdrawn/superseded Evidence.

Focused exit: all XRC and transport/security cases pass, including integrity mismatch, revocation, unavailable content, export limit, and no locator disclosure.

## 7. Checkpoint D — Evidence Workbench frontend

Compose Supporting File intake/scanner state, proposed Evidence creation/linkage, Human Evidence lifecycle, lineage/reliance, retention/hold/disposition, export, and recovery in the Project/Workspace experience.

Server state is authoritative. Every authority mutation success rereads; conflict forces reread before resubmit; unavailable/indeterminate never renders optimistic success. Scanner availability is visibly distinct from Evidence currentness, historical Report reliance, and disposition eligibility.

Prove keyboard operation, visible focus, semantic labels, live-region behavior, responsive layout, Persian RTL, Project switch data clearing, and no raw UUID typing.

## 8. Exact conformance and regression execution

The frozen manifest remains exactly 48 vectors: 42 backend and 6 frontend, with IDs and semantics unchanged from EDS/IDS. Canonical fixtures and focused commands are those frozen by IDS-055 section 31.8.

After focused PASS, run full backend regression and full frontend Vitest, typecheck, and build. Migration qualification uses disposable PostgreSQL only. Record commands, environment, revision/head, counts, exit codes, failures, and limitations; no PASS may be inferred or fabricated.

QG-M1 Readiness and final implementation review must explicitly assess all eleven Manifesto principles. Human authority, Engineering-first truth, tenant ownership, evidence-before-assumption, explainability, and intelligence-before-automation are blocking principles for this PATCH.

## 9. Operational, rollback, and stop conditions

Implement only safe capability metrics/logging frozen by IDS-055. No metric/log label may contain subject UUID, filename, rationale, storage key, protected content, credentials, or token. Readiness requires observability for conflicts, active holds, indeterminate eligibility, export/recovery outcomes, and outbox health.

Application rollback disables PATCH-055 route/UI composition without deleting retention history. Live/customer schema rollback must not destroy populated PATCH-055 state; use governed forward-repair. Physical deletion remains outside PATCH-055.

STOP immediately on: Alembic parent/head drift; need for a file outside the accepted change boundary; need to change ADR/EDS/IDS semantics; cross-Organization disclosure; accepted Report/Memory provenance mutation; automatic purge path; destructive migration requirement; unresolved Critical/Major review finding; or unrelated dirty-work collision that cannot be isolated.

## 10. Git and delivery protection

Before each future implementation checkpoint record `git status --short` and fingerprints of shared dirty files. Stage only exact authorized paths/hunks; never `git add .` or `git add -A`. Compare cached diff against the accepted manifest and preserve unrelated work byte-for-byte where feasible.

This Plan authorizes no staging, commit, or push. QG-11 and QG-12 remain separate future gates.

## 11. Human checkpoint model

After Plan independent review, explicit Human Plan acceptance is required. Then QG-5 IRR must independently state exactly `READY FOR IMPLEMENTATION` with QG-M1 Readiness PASS before any implementation authority can be requested.

Implementation should proceed in checkpoints A–D with focused evidence and review at each boundary; a checkpoint does not authorize the next merely by completing tests. Final PATCH completion/delivery remains governed by QG-10, QG-11, QG-M1 Final, QG-12, and separate Human authority.

## 12. Human Plan acceptance

Human Plan Authority decision: **PASS / ACCEPTED / COMPLETE**.

Acceptance date: 2026-09-14.

The Human reviewer accepted Implementation-Plan-055 after the independent Plan review reported Critical/Major/Minor `0/0/0` with one non-blocking environment observation. That observation is resolved for readiness by executable repository evidence: from `backend`, `uv run alembic heads` reports exactly `e05400000006 (head)`.

This acceptance authorizes preparation and independent execution of the PATCH-055 Implementation Readiness Review only. It does not authorize implementation, migration creation/execution, database mutation, staging, commit, push, deployment, or PATCH-056+ work.

**Implementation-Plan-055: HUMAN ACCEPTED / COMPLETE**
