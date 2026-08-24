# PATCH-045 Batch 4 Authorized File Manifest

## Purpose

Focused final validation, evidence and final-review readiness only. This batch
does not add capability.

## Exact boundary

| Path | Action | Responsibility |
|---|---|---|
| `docs/reviews/PATCH-045-Implementation-Validation-Evidence.md` | CREATE | reproducible final validation matrix and results |
| `docs/reviews/FR-045-Engineering-Execution-Plan-Activities-Milestones.md` | CREATE | independent final-review record and QG-11/QG-12 readiness |
| `docs/reviews/PATCH-045-QG-11-Human-Acceptance.md` | CREATE | standalone Human QG-11 evidence |
| `docs/patches/PATCH-045.md` | MODIFY | status through final-review readiness only |
| `backend/tests/test_customer_organization_migration.py` | MODIFY | preserve PATCH-041 lineage checks while advancing its sole-head assertion to e045 |
| `backend/tests/test_onboarding_migration.py` | MODIFY | preserve PATCH-041 lineage checks while advancing its sole-head assertion to e045 |
| `backend/tests/test_supporting_file_migration.py` | MODIFY | preserve PATCH-043 lineage checks while advancing its sole-head assertion to e045 |
| `backend/tests/test_project_foundation_migration.py` | MODIFY | preserve PATCH-044 parentage checks while advancing its repository-head assertion to e045 |
| `backend/tests/test_technical_report_migration.py` | MODIFY | advance the current-chain assertion to e045 only |
| `backend/tests/test_organizational_memory_migration.py` | MODIFY | advance the current-chain assertion to e045 only |
| `backend/tests/test_operations_config.py` | MODIFY | expect the current production migration head e045 in test manifests only |
| `backend/tests/test_operations_health.py` | MODIFY | expect the current production migration head e045 in test manifests only |
| `frontend/src/test/workflows.test.tsx` | MODIFY | add the new bounded Execution Plan read to the pre-existing Project workspace mock |

## Required evidence

Run once after all focused evidence is green: PATCH-045 backend and frontend
tests; migration downgrade/upgrade/re-upgrade and single e045 head; relevant
Project/Foundation/Workspace/Capture/Report/Memory regressions; full backend;
full frontend; frontend typecheck/build; static/import, authorization,
non-disclosure, no-fake-data, exact-scope, prohibited-pattern, secret and
`git diff --check` checks.

## Stop conditions

Stop for a failed gate or a required production/test/design change. Do not
deliver, commit, push or close PATCH-045 in this batch. Do not implement
PATCH-046 or any deferred capability.

The eight test-only additions reconcile obsolete exact-head expectations found
by the one final broad regression. They do not weaken head checks, alter a
historical migration assertion, or change production semantics.
