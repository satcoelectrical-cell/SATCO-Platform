# PATCH-045 Batch 2 Authorized File Manifest

## Exact boundary

| Path | Action | Responsibility |
|---|---|---|
| `backend/app/adapters/engineering_execution_plan.py` | CREATE | Project authorization and Foundation application-boundary adapters |
| `backend/app/repositories/engineering_execution_plan_unit_of_work.py` | CREATE | single Session/UoW and Audit staging |
| `backend/app/services/engineering_execution_plan_service.py` | CREATE | establish/mutation/final checks/idempotency/reliability |
| `backend/app/repositories/engineering_execution_plan_repository.py` | MODIFY | command persistence/helpers only |
| `backend/app/ports/engineering_execution_plan.py` | MODIFY | exact service/UoW contracts if required |
| `backend/tests/test_execution_plan_service.py` | CREATE | commands/state/derived facts |
| `backend/tests/test_execution_plan_transaction.py` | CREATE | UoW/audit/rollback/idempotency/concurrency |
| `backend/tests/test_execution_plan_security.py` | CREATE | authorization/protected results/final rechecks |
| `backend/tests/test_execution_plan_integration.py` | CREATE | real Project/Foundation/Workspace boundary evidence |

## Scope

Implements commands and bounded read DTO assembly only. It must call the
accepted Project Foundation application boundary rather than query Foundation
persistence. It may query the parent Project/Workspace as a subordinate
Plan authorization policy but may not construct a foreign repository/Session.
One Plan UoW owns execution persistence/Audit/idempotency and never commits in
the repository. No router/frontend, schedule/generic PM, deliverable/risk/AI
or PATCH-046+ surface is permitted.

## Evidence and stop conditions

Prove final authorization/Foundation/Workspace checks, terminal/read-only,
same UoW, expected versions, one-winner conflict, idempotent replay/fingerprint
conflict, immutable revisions/history, derived progress/milestones and rollback
without partial state. Stop if Foundation application contracts cannot provide
establishment safely, a direct foreign repository/Session is needed, or an
accepted IDS rule needs change.
