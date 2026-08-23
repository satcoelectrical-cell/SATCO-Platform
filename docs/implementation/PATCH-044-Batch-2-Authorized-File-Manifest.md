# PATCH-044 Batch 2 Authorized File Manifest

## Scope

Batch 2 — Canonical Integration and Application Service, S05–S08.

CREATE:

- `backend/app/adapters/project_foundation.py` — Evidence/Supporting File
  application-service adapter only;
- `backend/app/services/project_foundation_service.py` — accepted commands,
  reads, readiness, final rechecks and closed results;
- `backend/app/dependencies/project_foundation.py` — request-scoped policy,
  source services and one-UoW composition;
- `backend/tests/test_project_foundation_service.py`;
- `backend/tests/test_project_foundation_integration.py`;
- `backend/tests/test_project_foundation_security.py`;
- `backend/tests/test_project_foundation_transaction.py`.

MODIFY only when required for accepted collaborator closure:

- `backend/app/ports/project_foundation.py`;
- `backend/app/repositories/project_foundation_repository.py`;
- `backend/app/repositories/project_foundation_unit_of_work.py`;
- `backend/tests/test_project_foundation_contracts.py`.

No router/main/frontend. Canonical adapters may call only existing Evidence and
Supporting File service methods. They may not import foreign repositories,
models, UoWs or Sessions. Evidence must be current; Supporting File available;
scope/context and authorization are exact.

Evidence: all mutation/read states; real canonical service integration;
Project policy rows; source revocation/non-disclosure; readiness and final
recheck; one-winner concurrency; Audit/rollback. Stop for unsupported canonical
context, invented authority, foreign persistence, extra Session, design change
or Batch 3+ need.
