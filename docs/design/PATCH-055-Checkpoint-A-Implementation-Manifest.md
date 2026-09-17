# PATCH-055 Checkpoint A — Implementation Manifest

## 1. Authority state

Date: 2026-09-14.

Upstream authority is complete through IRR-055: ADR-028, EDS-055, IDS-055, and Implementation-Plan-055 are Human accepted; QG-4 PASS; QG-5 PASS; QG-M1 Readiness PASS; IRR-055 states `READY FOR IMPLEMENTATION`.

This manifest defines Checkpoint A only. It does not authorize Checkpoints B–D, frontend work, export/recovery transport, staging, commit, push, deployment, PATCH-056+, or physical disposition.

## 2. Fresh preflight evidence

Repository HEAD: `405600cdd2b2fbab6f7f1e5afc555ad28bc40a2a`.

Branch: `patch-022.3a-development-infrastructure`.

Working tree before this manifest: 143 status entries; unrelated dirty work must remain untouched.

Executable migration preflight: `cd backend && uv run alembic heads` -> exactly `e05400000006 (head)`.

All planned new PATCH-055 Checkpoint-A backend/test files were absent at preflight.

## 3. Checkpoint-A purpose

Implement only the accepted retention domain/persistence foundation: closed vocabularies, typed RetentionSubject, deterministic digests, validation primitives, persistence models, and additive migration foundation required for later application-service work.

## 4. Exact production file manifest

New files authorized for Checkpoint A:

- `backend/app/enums/retention.py`
- `backend/app/models/retention.py`
- `backend/app/models/retention_command.py`
- `backend/app/schemas/retention.py`
- `backend/migrations/versions/e05500000001_patch_055_retention_foundation.py`

Existing production file permitted to change:

- `backend/app/models/__init__.py` — model registration/import only, if required by migration/model discovery.

No repository, UoW, service, dependency, router, main-router composition, port, frontend, Evidence, or Supporting File production file is authorized in Checkpoint A.

## 5. Exact test/evidence manifest

New test file authorized:

- `backend/tests/test_patch055_retention_migration.py`

The broader `test_patch055_commercial_evidence_retention.py` belongs to later Checkpoint B/C qualification and is not authorized in A.

Checkpoint-A evidence may use disposable PostgreSQL only. No production/customer database or live object storage is permitted.

## 6. Required Checkpoint-A qualification

Before Checkpoint-A review, prove:

- migration revision is exactly `e05500000001` with parent `e05400000006`;
- repository has one Alembic head after migration creation;
- additive schema creates only the eight IDS-frozen PATCH-055 tables;
- no fabricated legacy retention backfill;
- exact key types, foreign keys, indexes, check constraints, one-current-head rule, and at-most-one-active-hold rule;
- retention and hold digest fields and revision/predecessor topology match accepted IDS;
- fresh install and populated historical upgrade on disposable PostgreSQL;
- safe empty-footprint downgrade/re-upgrade qualification and refusal/forward-repair behavior where state would be destroyed;
- focused migration tests PASS;
- `git diff --check` PASS for exact Checkpoint-A paths;
- no unrelated dirty file is staged, rewritten, or included in evidence.

## 7. Stop conditions

STOP rather than improvise if implementation requires any file outside section 4/5, changes accepted ADR/EDS/IDS semantics, changes migration parent/head topology, requires destructive historical rewrite, creates automatic physical deletion authority, or collides with unrelated dirty work.

Checkpoint-A completion does not authorize Checkpoint B. It requires independent Checkpoint-A review and separate Human acceptance.

## 8. Human implementation authority

Status: **READY FOR HUMAN CHECKPOINT-A IMPLEMENTATION AUTHORIZATION**.

No Checkpoint-A production/test/migration implementation has been created by this manifest.

## 9. Human Checkpoint-A implementation authorization

Human Implementation Authority decision: **AUTHORIZED / BOUNDED TO CHECKPOINT A**.

Authorization date: 2026-09-14.

Authorized scope is exactly sections 3–6 of this manifest: retention domain/persistence foundation, the one additive `e05500000001` migration, and Checkpoint-A migration qualification tests.

This authority does not extend to Checkpoints B–D, service/UoW/API/frontend implementation, production/customer database mutation, staging, commit, push, deployment, or PATCH-056+.
