# PATCH-045 Batch 1 Authorized File Manifest

## Authority

Batch 1 preparation is complete. This manifest authorizes implementation only
after the standing Human Batch 1 implementation authority is applied.

## Exact boundary

| Path | Action | Responsibility |
|---|---|---|
| `backend/app/enums/engineering_execution_plan.py` | CREATE | closed execution enums/helpers |
| `backend/app/models/engineering_execution_plan.py` | CREATE | ORM metadata and pure transition/config helpers |
| `backend/app/schemas/engineering_execution_plan.py` | CREATE | closed DTO/result validation |
| `backend/app/ports/engineering_execution_plan.py` | CREATE | typed Plan/authorization/Foundation contracts only |
| `backend/app/exceptions/engineering_execution_plan.py` | CREATE | closed domain errors |
| `backend/app/repositories/engineering_execution_plan_repository.py` | CREATE | no-commit persistence/locks/ordered reads |
| `backend/migrations/versions/e04500000001_engineering_execution_plan.py` | CREATE | e044-parented DDL, triggers, role guards |
| `backend/tests/test_execution_plan_contracts.py` | CREATE | contracts/normalization/prohibited cases |
| `backend/tests/test_execution_plan_migration.py` | CREATE | migration/head/DDL/direct-SQL guards |
| `backend/tests/test_execution_plan_repository.py` | CREATE | no-commit/config/repository behavior |
| `backend/tests/test_execution_plan_database_roles.py` | CREATE | owner/runtime role isolation |

## Scope and prerequisites

Parent sole head must be `e04400000001`; migration parent is exactly that
revision. This batch may create only empty Plan subordinate persistence and
contracts. It requires no Foundation direct access and must not touch Project,
Foundation, Workspace or canonical foreign persistence.

Focused evidence covers enum/union closure; 0/1 Plan identity; tenant,
revision/history, date/bound, same-Plan link, cycle and terminal direct-SQL
rejection; role ownership; deterministic ordered repository output; and no
commit behavior.

## Exclusions and stop conditions

No UoW/service/canonical adapter/API/frontend/composition, command execution,
read application behavior, AI, schedule, generic task, outbox or PATCH-046+
capability. Stop if Alembic head differs, a guard needs an accepted
architecture/IDS change, a foreign table must be changed, or any file outside
this list is required.
