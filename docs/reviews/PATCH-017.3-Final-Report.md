# PATCH-017.3 Final Report

**Project:** SATCO Platform
**Patch:** PATCH-017.3 — PATCH-017 Final Recovery and Stabilization
**Date:** 2026-07-26
**Source of Truth:** `/docs`
**Git commit:** Not created

## PATCH STATUS

**COMPLETED**

All approved PATCH-017.3 implementation, documentation, automated testing, Docker validation, PostgreSQL connectivity, source compilation, and targeted API criteria passed.

No migration, destructive action, Git commit, or Git push was performed.

## Production Readiness

**READY for PATCH-017.3 scope and commit review.**

This means the approved recovery and stabilization scope passed its acceptance criteria. It does not claim that the complete SATCO Platform is ready for external production deployment.

## Tests

### Docker Services

Command:

```bash
docker compose ps
```

Result:

- `satco-backend`: running
- `satco-postgres`: running

### PostgreSQL Regression Test Environment

The approved dedicated database was created in the existing Docker PostgreSQL service:

```text
satco_platform_patch0173_test
```

The test configuration refuses to run mutation tests unless `TEST_DATABASE_URL` targets that exact database name.

No existing `satco_platform` development data was changed or deleted. The dedicated test database remains present because deletion was not authorized.

### Full Automated Regression Suite

Command:

```bash
docker compose run --rm \
  -e TEST_DATABASE_URL=postgresql://satco:satco_password@postgres:5432/satco_platform_patch0173_test \
  backend sh -c \
  'python -m pip install pytest httpx && python -m pytest -q'
```

Result:

```text
22 passed, 44 warnings in 2.93s
```

The suite covers:

- Public registration
- Server-assigned engineer role
- Admin self-registration prevention
- Duplicate email and username handling
- OAuth2 form login
- Invalid login
- Rejection of query-parameter login
- Missing and invalid tokens
- Refresh-token rejection at protected endpoints
- Unknown token subjects
- Inactive users
- Central unsupported-role validation
- Engineer versus admin authorization
- Customer CRUD, searching, pagination, missing records, and audits
- Preserved Customer detail helper
- Contact CRUD, customer validation, filtering, missing records, and audits
- Project CRUD, relationship validation, filtering, sorting, pagination, missing records, authorization, and audits
- Admin-only audit-log access
- Search authentication and result preservation

Warnings were limited to:

- A Starlette TestClient/httpx deprecation
- Existing Pydantic class-based configuration deprecations
- Existing naive `datetime.utcnow()` deprecations

These warnings did not fail the suite and are outside the approved PATCH-017.3 scope.

### Source Compilation

Command:

```bash
docker compose exec -T backend \
  python -m compileall -q app tests
```

Result:

```text
PASSED
```

### PostgreSQL Connectivity

Command:

```bash
docker compose exec -T postgres \
  psql -U satco -d satco_platform -X -tAc "SELECT 1;"
```

Result:

```text
1
```

### Targeted Live API Validation

The backend was restarted before live validation.

Results:

```text
GET  /                         -> 200
GET  /openapi.json             -> 200
GET  /customers/               -> 401 without token
GET  /search/?q=test           -> 401 without token
POST /auth/login?username=...  -> 422
```

### Diff Validation

Command:

```bash
git diff --check
```

Result:

```text
PASSED
```

## Files Modified

### Backend

- `backend/app/api/v1/routers/auth.py`
- `backend/app/api/v1/routers/contacts.py`
- `backend/app/api/v1/routers/customers.py`
- `backend/app/api/v1/routers/projects.py`
- `backend/app/api/v1/routers/search.py`
- `backend/app/dependencies/auth.py`
- `backend/app/permissions/roles.py`
- `backend/app/repositories/customer_repository.py`
- `backend/app/repositories/project_repository.py`
- `backend/app/repositories/user_repository.py`
- `backend/app/schemas/user.py`
- `backend/app/services/contact_service.py`
- `backend/app/services/customer_service.py`
- `backend/app/services/project_service.py`
- `backend/app/services/user_service.py`

### Documentation

- `docs/02_Roadmap.md`
- `docs/07_Backend_Blueprint.md`
- `docs/adr/ADR-004.md`
- `docs/adr/ADR-005.md`
- `docs/adr/ADR-010-Universal-Audit-Integration.md`

## Files Created

### Tests

- `backend/tests/conftest.py`
- `backend/tests/test_auth.py`
- `backend/tests/test_customers.py`
- `backend/tests/test_contacts.py`
- `backend/tests/test_projects.py`
- `backend/tests/test_audit_logs.py`
- `backend/tests/test_search.py`

### Patch Documentation and Reviews

- `docs/patches/PATCH-017.3.md`
- `docs/reviews/PATCH-017-Technical-Review.md`
- `docs/reviews/PATCH-017.3-Implementation-Plan.md`
- `docs/reviews/PATCH-017.3-Implementation-Report.md`
- `docs/reviews/PATCH-017.3-Final-Report.md`

## API Changes

| Endpoint | Final behavior |
|---|---|
| `POST /auth/register` | Rejects extra fields including `role`; assigns `engineer` server-side |
| `POST /auth/login` | Accepts OAuth2 `application/x-www-form-urlencoded` credentials |
| `GET /search/` | Requires a valid JWT access token |
| `POST /projects/` | Validates Customer and records a CREATE audit event |
| `GET /projects/` | Supports pagination, Customer/status filters, and sorting |
| `PUT /projects/{id}` | Validates relationships, returns controlled 404s, and records UPDATE audit |
| `DELETE /projects/{id}` | Remains admin-only, returns controlled 404, and records DELETE audit |
| `PUT /customers/{id}` | Returns 404 for a missing Customer |
| `DELETE /customers/{id}` | Returns 404 for a missing Customer |
| `POST /contacts/` | Returns 404 when the referenced Customer does not exist |

Successful endpoint paths and response models otherwise remain compatible.

## Security Changes

- Removed client-controlled role assignment from public registration.
- Public registrations receive the least-privileged supported role, `engineer`, server-side.
- Added central validation of supported role values.
- Removed login credentials from URL query parameters.
- Changed login to the OAuth2 password form contract.
- Protected internal CRM and Project search results with JWT authentication.
- Preserved admin-only Project deletion.
- Preserved admin-only audit-log access.
- Confirmed refresh tokens cannot authorize protected endpoints.

## Remaining Issues

No issue blocks PATCH-017.3.

Known out-of-scope technical debt remains:

- Historical Alembic migrations do not fully reproduce the current database schema.
- Business mutations and audit writes are not yet one atomic transaction.
- Some Pydantic schemas use deprecated class-based configuration.
- Models use deprecated naive `datetime.utcnow()` defaults.
- API routes remain unversioned.
- Dependencies are unpinned.
- CI/CD is not configured.

These items require separately approved future work. PATCH-018 was not started.

## Git Diff

Current tracked diff summary before adding untracked files:

```text
20 files changed, 431 insertions(+), 175 deletions(-)
```

Tracked diff details:

```text
 backend/app/api/v1/routers/auth.py              |  12 +-
 backend/app/api/v1/routers/contacts.py          |  14 +-
 backend/app/api/v1/routers/customers.py         |  18 +-
 backend/app/api/v1/routers/projects.py          |  88 ++++++----
 backend/app/api/v1/routers/search.py            |   3 +
 backend/app/dependencies/auth.py                |   9 +-
 backend/app/permissions/roles.py                |  12 ++
 backend/app/repositories/customer_repository.py |  10 ++
 backend/app/repositories/project_repository.py  |  39 ++++-
 backend/app/repositories/user_repository.py     |   9 +-
 backend/app/schemas/user.py                     |  25 +--
 backend/app/services/contact_service.py         |   8 +
 backend/app/services/customer_service.py        |  17 +-
 backend/app/services/project_service.py         | 219 +++++++++++++++---------
 backend/app/services/user_service.py            |   6 +-
 docs/02_Roadmap.md                              |  29 ++--
 docs/07_Backend_Blueprint.md                    |  61 ++++++-
 docs/adr/ADR-004.md                             |   6 +
 docs/adr/ADR-005.md                             |   7 +
 docs/adr/ADR-010-Universal-Audit-Integration.md |  14 ++
```

The diff summary does not count untracked test and documentation files until they are staged.

## Git Status

Current status:

```text
 M backend/app/api/v1/routers/auth.py
 M backend/app/api/v1/routers/contacts.py
 M backend/app/api/v1/routers/customers.py
 M backend/app/api/v1/routers/projects.py
 M backend/app/api/v1/routers/search.py
 M backend/app/dependencies/auth.py
 M backend/app/permissions/roles.py
 M backend/app/repositories/customer_repository.py
 M backend/app/repositories/project_repository.py
 M backend/app/repositories/user_repository.py
 M backend/app/schemas/user.py
 M backend/app/services/contact_service.py
 M backend/app/services/customer_service.py
 M backend/app/services/project_service.py
 M backend/app/services/user_service.py
 M docs/02_Roadmap.md
 M docs/07_Backend_Blueprint.md
 M docs/adr/ADR-004.md
 M docs/adr/ADR-005.md
 M docs/adr/ADR-010-Universal-Audit-Integration.md
?? backend/tests/
?? docs/patches/
?? docs/reviews/
```

No files are staged.

No commit has been created.

Proposed commit message:

```text
PATCH-017.3: Final recovery and stabilization
```

Explicit approval is required before committing. No GitHub push is authorized.
