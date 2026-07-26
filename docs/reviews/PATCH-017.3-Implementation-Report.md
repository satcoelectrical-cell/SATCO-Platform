# PATCH-017.3 Implementation Report

**Project:** SATCO Platform
**Patch:** PATCH-017.3 — PATCH-017 Final Recovery and Stabilization
**Date:** 2026-07-26
**Source of Truth:** `/docs`

## PATCH STATUS

**COMPLETED**

All PATCH-017.3 acceptance and exit criteria passed. No Git commit has been created.

## Implemented Changes

- Repaired the Project service/repository contract by using the existing session-bound `ProjectRepository`.
- Restored Project pagination, customer filtering, status filtering, and sorting.
- Added deterministic secondary ordering by Project ID.
- Added Project customer validation during create and customer reassignment.
- Added controlled 404 behavior for missing Projects and missing customer relationships.
- Added Project CREATE, UPDATE, and DELETE audit events.
- Added Project audit details containing name, customer ID, status, and UPDATE changed fields.
- Preserved Customer and Contact audit behavior.
- Added Contact customer validation during creation.
- Added controlled Customer update/delete missing-record behavior.
- Preserved `CustomerService.get_detail()` as deprecated/internal behavior.
- Moved customer-detail database access into `CustomerRepository`.
- Removed duplicate Customer router imports.
- Prevented public registration from accepting a role.
- Assigned the engineer role to public registrations server-side.
- Added central Role value validation.
- Changed login to OAuth2 password form data.
- Protected Search with access-token authentication.
- Added PostgreSQL-backed endpoint regression tests.
- Synchronized the Roadmap, Backend Blueprint, authentication ADRs, and audit ADR.

## Files Created

- `backend/tests/conftest.py`
- `backend/tests/test_auth.py`
- `backend/tests/test_customers.py`
- `backend/tests/test_contacts.py`
- `backend/tests/test_projects.py`
- `backend/tests/test_audit_logs.py`
- `backend/tests/test_search.py`
- `docs/patches/PATCH-017.3.md`
- `docs/reviews/PATCH-017.3-Implementation-Plan.md`
- `docs/reviews/PATCH-017.3-Implementation-Report.md`
- `docs/reviews/PATCH-017-Technical-Review.md`

The implementation plan and original technical review were created and approved before Phase 2.

## Files Modified

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
- `docs/02_Roadmap.md`
- `docs/07_Backend_Blueprint.md`
- `docs/adr/ADR-004.md`
- `docs/adr/ADR-005.md`
- `docs/adr/ADR-010-Universal-Audit-Integration.md`

## Database Changes

Application/development database:

- No schema changes.
- No migrations.
- No development data deletion or reset.

Test infrastructure:

- Created `satco_platform_patch0173_test` in the existing Docker PostgreSQL service.
- Test configuration refuses to run unless `TEST_DATABASE_URL` targets that exact database name.
- Automated mutation tests ran only in the dedicated test database.
- The test database was not dropped because deletion was not authorized.

## Dependency Changes

- No dependency files were added or modified.
- `backend/requirements.txt` is unchanged.
- `pytest 9.1.1` and `httpx 0.28.1` were installed only inside a disposable Docker test container.

## API Changes

| Endpoint | PATCH-017.3 behavior |
|---|---|
| `POST /auth/register` | Rejects extra fields including `role`; assigns `engineer` server-side |
| `POST /auth/login` | Accepts OAuth2 `application/x-www-form-urlencoded` credentials |
| `GET /search/` | Requires a JWT access token |
| `POST /projects/` | Validates customer and writes CREATE audit |
| `GET /projects/` | Supports pagination, customer/status filters, and sorting |
| `PUT /projects/{id}` | Returns controlled 404s and writes UPDATE audit |
| `DELETE /projects/{id}` | Remains admin-only, returns controlled 404, and writes DELETE audit |
| `PUT /customers/{id}` | Missing Customer returns 404 |
| `DELETE /customers/{id}` | Missing Customer returns 404 |
| `POST /contacts/` | Missing Customer returns 404 |

## Security Corrections

- Removed client-controlled role assignment from public registration.
- Assigned the least-privileged supported public role (`engineer`) server-side.
- Centralized validation of supported role values.
- Removed login credentials from URL query parameters.
- Protected internal CRM/Project search results with JWT authentication.
- Preserved admin-only Project deletion.
- Preserved admin-only audit-log access.
- Confirmed refresh tokens cannot authorize protected endpoints.

## Tests Executed

### Docker Service Check

```bash
docker compose ps
```

Result:

- `satco-backend`: running
- `satco-postgres`: running

### Dedicated Test Database Check and Creation

```bash
docker compose exec -T postgres \
  psql -U satco -d postgres -X -tAc \
  "SELECT 1 FROM pg_database
   WHERE datname = 'satco_platform_patch0173_test';"
```

Initial result:

- Database did not exist.

```bash
docker compose exec -T postgres \
  createdb -U satco satco_platform_patch0173_test
```

Result:

- Dedicated test database created successfully.

### Full PostgreSQL Regression Suite

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

Test coverage includes:

- Registration and OAuth2 login
- Role-injection prevention
- Duplicate registration and authentication failures
- Missing, invalid, refresh, unknown-subject, and inactive-user tokens
- Central unsupported-role validation
- Admin versus engineer authorization
- Customer CRUD, missing records, pagination/search, and audits
- Preserved customer detail helper
- Contact CRUD, filtering, customer validation, missing records, and audits
- Project CRUD, filters, sorting, pagination, relationship validation, missing records, authorization, and audits
- Admin-only audit-log access
- Search authentication and existing result behavior

Warnings:

- Starlette reports a TestClient/httpx deprecation.
- Existing Pydantic class-based configuration is deprecated.
- Existing `datetime.utcnow()` model defaults are deprecated.

These warnings did not fail the suite and are pre-existing technical debt outside PATCH-017.3.

### Source Compilation

```bash
docker compose exec -T backend \
  python -m compileall -q app tests
```

Result:

- Passed with no output or compilation errors.

### PostgreSQL Connectivity

```bash
docker compose exec -T postgres \
  psql -U satco -d satco_platform -X -tAc "SELECT 1;"
```

Result:

```text
1
```

### Backend Restart

```bash
docker compose restart backend
```

Result:

- Backend restarted successfully.

### Targeted Live API Validation

Read-only requests were executed against `http://127.0.0.1:8000`.

Results:

```text
GET  /                         -> 200
GET  /openapi.json             -> 200
GET  /customers/               -> 401 without token
GET  /search/?q=test           -> 401 without token
POST /auth/login?username=...  -> 422
```

### Diff Validation

```bash
git diff --check
```

Result:

- Passed with no whitespace errors.

## Test Results

All mandatory PATCH-017.3 tests and validation checks passed.

## Remaining Issues

No remaining issue blocks PATCH-017.3.

Known out-of-scope technical debt remains:

- Historical Alembic migrations do not fully reproduce the current schema.
- Business entity and audit commits are not yet one atomic transaction.
- Pydantic class-based configuration has deprecation warnings.
- Models use deprecated naive `datetime.utcnow()` defaults.
- The API remains unversioned despite its directory structure.
- The project still lacks committed dependency pinning and CI.

These items require separately approved future work and were not expanded into PATCH-018 during this patch.

## Production Readiness

**READY for PATCH-017.3 scope and commit review.**

This statement means the approved stabilization patch passed its acceptance criteria. It does not claim that the complete SATCO Platform is ready for external production deployment.

## Git

No commit was created.

Proposed commit message:

```text
PATCH-017.3: Final recovery and stabilization
```

Explicit approval is required before committing. No push is authorized.
