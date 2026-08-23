# Implementation Plan-044 — Project Definition, Scope, Inputs & Lifecycle Foundation

## 1. Status

**ACCEPTED / COMPLETE.** Independent Plan Review is PASS. Four small,
dependency-ordered batches implement the accepted PATCH/Architecture/EDS/IDS.
Each batch requires an exact Authorized File Manifest, implementation,
Independent Review and Human acceptance before the next batch.

The dirty worktree contains unrelated Human changes. Every manifest uses exact
path/hunk allow-lists and never cleans, resets, stashes or stages those changes.

## 2. Batch 1 — Contracts and persistence foundation (S01–S04)

- **S01:** closed enums, commands, read/result schemas, ports and exceptions.
- **S02:** Project Foundation ORM/domain records and pure stage/readiness rules.
- **S03:** migration `e04400000001`, tables/constraints/functions/triggers,
  owner/runtime grants and exact ORM parity.
- **S04:** no-commit repository/UoW, deterministic locking/query/reorder and
  shared Audit staging.

Expected production CREATE surfaces:
`backend/app/enums/project_foundation.py`,
`backend/app/models/project_foundation.py`,
`backend/app/schemas/project_foundation.py`,
`backend/app/ports/project_foundation.py`,
`backend/app/exceptions/project_foundation.py`,
`backend/app/repositories/project_foundation_repository.py`,
`backend/app/repositories/project_foundation_unit_of_work.py`, and
`backend/migrations/versions/e04400000001_project_foundation.py`.
MODIFY model/enum exports only. Modify exact migration-head/operations test
expectations that currently name `e04300000001`; preserve every historical
parent assertion.

Expected tests: contract/schema/domain, migration/direct-SQL/role, repository
and transaction suites. Evidence covers all closed validation, absent legacy
root, input/stage machines, schema matrix, direct-SQL scope/source/history
bypass, reorder concurrency, rollback, upgrade/downgrade/re-upgrade, sole head,
role drift, static imports and scope scan.

Stop for head drift, an ungoverned role/schema change, accepted-design change,
foreign canonical persistence access or later-batch behavior.

## 3. Batch 2 — Canonical integration and application service (S05–S08)

- **S05:** context-specific Evidence and Supporting File application-service
  adapters for exact authorization/current-standing and candidate listing.
- **S06:** Project visibility/mutation policy and request-scoped composition.
- **S07:** definition/input commands, source rechecks, readiness and stage
  transition orchestration.
- **S08:** atomic Audit/rollback/concurrency and protected result translation.

Expected production CREATE surfaces:
`backend/app/adapters/project_foundation.py`,
`backend/app/services/project_foundation_service.py`, and
`backend/app/dependencies/project_foundation.py`. MODIFY only Batch-1 ports/
repository/UoW if implementation-facing closure requires it.

Expected tests: service, source integration, transaction, security and
concurrency. Use actual canonical service instances for both source classes;
recording doubles are supplemental only. Prove current-source revocation,
same-Project/Organization/Workspace, mutation matrix, final recheck ordering,
one-winner transitions and atomic Audit.

Stop for direct Evidence/Supporting File repository/ORM/Session access,
unsupported canonical response context, invented authority, separate
authoritative transaction or IDS change.

## 4. Batch 3 — Thin API and bounded Project experience (S09–S12)

- **S09:** thin authenticated eight-route router and registration.
- **S10:** typed frontend client and Project Foundation read/edit composition.
- **S11:** required-input/source candidate and stage/readiness interactions.
- **S12:** loading/protected/invalid/conflict/unavailable, accessibility,
  responsive and real-data-only experience.

Expected backend CREATE surface:
`backend/app/api/v1/routers/project_foundation.py`; MODIFY `backend/app/main.py`.
Expected frontend MODIFY surfaces: `frontend/src/api/types.ts`,
`frontend/src/api/client.ts`, `frontend/src/pages/ProjectsPage.tsx`, and
`frontend/src/styles.css`; CREATE
`frontend/src/components/ProjectFoundationPanel.tsx`.

Expected tests: backend API/composition/security and frontend Project
Foundation/workflow/API/accessibility/responsive suites. Prove all eight routes,
trusted context, payload-free protected results, no raw internal-ID entry,
truthful legacy empty state, valid complete flow, narrow/wide layouts and no
fake production records.

Stop for router-owned ORM/UoW/policy, client-derived authority, new navigation,
Wizard/Command Center leakage, fake data or any PATCH-045+ behavior.

## 5. Batch 4 — Regression and final evidence (S13–S15)

- **S13:** focused Project Foundation validation, adjacent Project/Workspace/
  Evidence/Supporting File/auth/Audit/migration regressions, full backend and
  frontend regression, sole head, static/import/type/build, exact scope,
  secret/fake-data and QG-M1.
- **S14:** reproducible implementation validation evidence preserving all
  review/remediation history.
- **S15:** Independent Final Implementation Review artifact and PATCH readiness
  metadata only.

Expected docs: CREATE
`docs/reviews/PATCH-044-Implementation-Validation-Evidence.md` and
`docs/reviews/FR-044-Project-Definition-Scope-Inputs-Lifecycle-Foundation.md`;
MODIFY only `docs/patches/PATCH-044.md`. No production/test remediation is
allowed in this batch without reopening the affected accepted batch.

Stop on any failed gate, unrepeatable evidence, unresolved Critical/Major,
scope contamination or technical change requirement.

## 6. Global review gates

Every batch runs focused tests, relevant accepted-batch regressions,
static/import validation, prohibited-pattern/scope checks and `git diff
--check`. Every initial FAIL, remediation and re-review remains standalone and
traceable. No batch carries an unresolved Major forward.

After Batch 4: Independent Final Review, Human QG-11, QG-12 exact delivery
boundary/hygiene, bounded commit/push, remote `0/0`, documentation-only closure
and separate closure commit/push. PATCH-045 remains unregistered.
