# PATCH-045 Batch 3 Authorized File Manifest

## Exact boundary

| Path | Action | Responsibility |
|---|---|---|
| `backend/app/dependencies/engineering_execution_plan.py` | CREATE | request-scoped composition outside router |
| `backend/app/api/v1/routers/engineering_execution_plan.py` | CREATE | eight thin authenticated routes |
| `backend/app/main.py` | MODIFY | one router registration |
| `backend/tests/test_execution_plan_api.py` | CREATE | route/auth/result evidence |
| `backend/tests/test_execution_plan_security.py` | MODIFY | real composition/context/non-disclosure evidence |
| `frontend/src/api/types.ts` | MODIFY | typed execution DTOs |
| `frontend/src/api/client.ts` | MODIFY | typed eight API calls |
| `frontend/src/components/EngineeringExecutionPlanPanel.tsx` | CREATE | accessible Project-detail execution UI |
| `frontend/src/pages/ProjectsPage.tsx` | MODIFY | bounded panel integration |
| `frontend/src/styles.css` | MODIFY | logical responsive/RTL-safe presentation |
| `frontend/src/test/engineering-execution-plan.test.tsx` | CREATE | real response/state/accessibility evidence |

## Scope

Composition creates the Plan service/UoW/parent policy/Foundation application
adapter outside transport. Router only parses accepted DTOs, obtains the
request-scoped app, calls a one-to-one service operation and maps closed
results. UI exposes no raw IDs/actor/Organization fields and uses only API
responses and existing Project owner/assignee/Workspace options.

## Evidence / exclusions / stop

Prove all eight routes, 401, tenant injection denial, payload-free protected
results, conflict/invalid/unavailable mapping, no router Session/UoW/policy,
responsive/accessibility/rationale controls and real-data-only UI. Exclude
new backend command/persistence semantics, Gantt, schedule, generic tasks,
dashboard redesign, AI/Deliverable/Risk or PATCH-046+. Stop for any accepted
contract change, router-owned infrastructure, raw identifier requirement or
out-of-boundary file.
