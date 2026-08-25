# PATCH-047 Batch 3 — Authorized File Manifest

## Authority and scope

Batch 3 is limited to accepted Change and Change Impact application behavior
after the `B3-CRIT-01` target-identity reconciliation. Batch 1–2 remain
accepted and unchanged. Batch 4 transport/UI, PATCH-048, AI, Foundation target
identity, migrations, and foreign persistence access are excluded.

## Authorized implementation boundary

| Path | Action | Responsibility | Prohibited responsibility |
|---|---|---|---|
| `backend/app/enums/project_control.py` | MODIFY | Remove `foundation` from the closed target enum. | New target kinds or heterogeneous selectors. |
| `backend/app/schemas/project_control.py` | MODIFY | Closed Change/Impact commands and result unions, including Deliverable Revision owning-deliverable selector context. | Transport DTOs or client authority. |
| `backend/app/repositories/project_control_repository.py` | MODIFY | Scoped no-commit Change/Impact reads and row locks. | Foreign canonical reads or commit. |
| `backend/app/services/project_control_service.py` | MODIFY | Change creation/correction/lifecycle, potential/confirmed Impact, authorization, idempotency, Audit/outbox and same-UoW orchestration. | Router, composition, AI authority, generic tickets. |
| `backend/app/adapters/project_control_targets.py` | CREATE | Six-kind target-specific calls through canonical application services and closed translation. | ORM/Session/repository access, Foundation mapping, generic resolver. |
| `backend/tests/test_project_control_contracts.py` | MODIFY | Closed Change/Impact and unsupported-kind contract evidence. | Broad regression. |
| `backend/tests/test_project_control_service.py` | MODIFY | Change, successor, Impact, replay and scope behavior. | Transport testing. |
| `backend/tests/test_project_control_transaction.py` | MODIFY | Real-UoW rollback, idempotency, Audit/outbox and concurrency evidence. | Non-Batch-3 services. |
| `backend/tests/test_project_control_security.py` | MODIFY | Target authorization, protected non-disclosure and non-mutation evidence. | UI/API behavior. |
| `backend/tests/test_project_control_change_integration.py` | CREATE | Canonical target adapter request/response dispatch for all six kinds. | Foreign persistence fixtures. |
| `docs/reviews/PATCH-047-Batch-3-Manifest-Review.md` | CREATE | Independent manifest review and any finding chronology. | Implementation acceptance. |
| `docs/reviews/PATCH-047-Batch-3-Implementation-Review.md` | CREATE | Independent implementation review and re-review chronology. | Batch 4 review. |
| `docs/reviews/PATCH-047-Batch-3-Human-Acceptance.md` | CREATE | Human acceptance only after focused PASS and zero Critical/Major. | Further authority. |
| `docs/patches/PATCH-047.md` | MODIFY | Record Batch 3 acceptance and retain Batch 4 as not started. | Delivery, closure, or Batch 4 authority. |

## Dependencies and evidence

The migration remains `e04700000001` with no backfill or amendment. The
existing Project Control UoW is the sole transaction boundary and its
repository remains no-commit. Target validation is permitted only through
Engineering Execution Plan, Engineering Deliverable, Evidence, and Supporting
File application boundaries. The six supported UUID kinds are Activity,
Milestone, Deliverable, Deliverable Revision, Evidence and Supporting File.

Focused evidence must prove Change creation, immutable successor correction,
explicit withdrawal/supersession behavior, potential versus explicit Human
confirmation, exact replay/conflict, target non-mutation, same-scope checks,
payload-free protected/invalid/unavailable outcomes, direct Audit/outbox/
idempotency rollback, and lock-based duplicate/confirmation races. Each target
kind requires one material canonical-dispatch success case; unsupported
Foundation/Project/generic kinds require closed rejection. Adjacent evidence is
limited to Batch 1 persistence, Batch 2 Risk/Issue/Decision, Execution,
Deliverable, Evidence and Supporting File reads.

## Stop conditions and scope checks

Stop for a required Foundation UUID, mapping table, generic resolver,
heterogeneous selector, foreign repository/ORM/Session/UoW access, migration
change, accepted-contract change, target disclosure before authorization, or
any Batch 4/PATCH-048 requirement. Scope checks must fail any router,
dependency composition, API route, frontend, AI, graph/context, Foundation
target, or foreign persistence import in Batch 3 production surfaces.
