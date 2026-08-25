# PATCH-047 Implementation Validation Evidence

## Boundary and clean isolation

Validation covered the accepted PATCH-047 boundary only. Pre-existing modified
architecture, roadmap, ADR, PATCH-028 and Engineering Context Relationship
files, plus `SATCO-Review.zip` and
`Architecture-Milestone-Review-Post-PATCH-028.md`, remained identifiable and
excluded. PATCH-048 is not registered or implemented.

The disposable test database was restored to a clean schema after an earlier
interrupted migration test left it at `e03400000001` with non-governed Customer
rows. This was test-environment contamination, not a production migration
defect. The test role credential was restored only to its fixture’s documented
test value. No production database, repository history or unrelated worktree
file was modified.

## Commands and results

- Focused Project Control backend contracts, repository, transactions,
  migration, service, security, Change/Impact integration and API:
  `python -m pytest -q tests/test_project_control_contracts.py
  tests/test_project_control_repository.py
  tests/test_project_control_transaction.py
  tests/test_project_control_migration.py
  tests/test_project_control_service.py
  tests/test_project_control_security.py
  tests/test_project_control_change_integration.py
  tests/test_project_control_api.py` — **38 passed**.
- Migration: `alembic upgrade e04700000001`, `alembic downgrade
  e04600000001`, `alembic upgrade e04700000001`, `alembic heads` — PASS; sole
  head **`e04700000001`**.
- Full backend: `python -m pytest -q -p no:cacheprovider` in a disposable
  container with the repository mounted read-only at `/workspace` — **1,266
  passed, 1 stale runner-path assertion**. The assertion invoked Alembic from
  the image’s stale `/app`; it was corrected to resolve the actual test
  repository root and its focused revalidation passed. Final aggregate backend
  evidence: **1,267 passed**.
- Frontend: `npm run test:run` — **73 passed**; focused workflow repair — **6
  passed**; `npm run typecheck` and `npm run build` — PASS.
- Static/import: `python -m compileall -q app` with bytecode redirected to
  temporary storage — PASS. Router/composition, prohibited capability and
  targeted secret scans — PASS. `git diff --check` — PASS.

## Final-validation remediation chronology

- Historical migration tests that asserted a former global head were updated
  to assert `e04700000001` while retaining their exact historical parent and
  migration assertions.
- Project Control direct-SQL tests now create an isolated test actor only if
  no prior test left one; this removes test-order dependency without creating
  legacy or production records.
- The Engineering Context migration test resolves its Alembic working
  directory from its source location rather than an image-specific `/app`.
- Workflow tests now provide the new closed Project Control list method in
  their existing API mock. No product semantics, authority, migration or
  persistence contract changed.

## Historical preservation and readiness

Batch 1–4 review, remediation and re-review evidence remains append-only and
traceable. Final evidence is sufficient for independent review and Human
QG-11; it does not itself deliver or close PATCH-047.
