# PATCH-017.3 — Final Recovery and Stabilization

## Phase 1 Implementation Plan

**Project:** SATCO Platform
**Patch:** PATCH-017.3
**Title:** PATCH-017 Final Recovery and Stabilization
**Source of Truth:** `/docs`
**Plan date:** 2026-07-26
**Current status:** Approved and implemented; validation completed

## Executive Summary

PATCH-017.3 will repair and stabilize the authentication, CRM, project, search, RBAC, and audit functionality already intended by PATCH-017. It will not begin PATCH-018 or introduce new project-management features.

The principal implementation defect is the broken project service/repository contract introduced by PATCH-017.2. The existing `ProjectRepository` class replaced module-level repository functions, while `project_service.py` continued calling the removed functions. PATCH-017.3 will update the project service to use the class correctly and restore list, create, update, delete, filtering, sorting, and pagination behavior.

The patch will also complete project CREATE/UPDATE/DELETE auditing, repair unfinished PATCH-017 code, close the public role-registration vulnerability, protect search, move login credentials out of URL query parameters, and add an isolated automated regression suite.

No application or development-database schema changes and no migrations are planned. All regression tests will run against the existing Docker PostgreSQL service used by SATCO Platform. Tests will use a dedicated PATCH-017.3 test database within that PostgreSQL environment so application development data is not changed and no second database backend is introduced. Test tables are temporary validation infrastructure inside that dedicated database and are not application migration changes.

## Source-of-Truth Review

Phase 1 reviewed:

- `docs/00_Constitution.md`
- `docs/01_Architecture.md`
- `docs/02_Roadmap.md`
- `docs/05_Coding_Standards.md`
- `docs/06_Database_Blueprint.md`
- `docs/07_Backend_Blueprint.md`
- `docs/08_AI_Development_Workflow.md`
- `docs/reviews/PATCH-017-Technical-Review.md`
- All ADR files in `docs/adr/`
- Relevant routers, services, repositories, schemas, models, permissions, dependencies, and configuration
- Current Git state
- Current Docker test dependency availability

The implementation plan follows the documented router/service/repository/model architecture and does not introduce a new framework.

## Scope Boundary

PATCH-017.3 will:

- Repair existing project CRUD integration.
- Restore already intended project query behavior.
- Complete project audit coverage.
- Repair unfinished PATCH-017 code.
- Correct critical authentication and authorization defects.
- Establish regression tests for existing CRM and project behavior.
- Validate the result in Docker.
- Update PATCH-017 documentation and status.

PATCH-017.3 will not:

- Begin PATCH-018 Project Management Enhancement.
- Add files, milestones, dashboards, workflows, or other project-management features.
- Add an `/api/v1` route prefix.
- Add refresh-token rotation or session management.
- Add role-management APIs.
- Add soft deletion or UUID identifiers.
- Repair the complete historical Alembic chain.
- Change the database schema.
- Run migrations.
- Delete, reset, or rewrite existing development data.
- Introduce a new repository or authorization framework.
- Rewrite Git history.
- Commit or push changes without explicit approval.

## Implementation Plan

### 1. Document PATCH-017.3 Before Implementation

Create an official patch definition containing:

- Objective
- Bounded scope
- Current defects
- Acceptance criteria
- Exit criteria
- Security impact
- API impact
- Database impact
- Test strategy
- Explicit exclusions

Update the Roadmap to identify PATCH-017 as incomplete and recovery in progress. PATCH-017 will only be marked complete after all implementation, test, Docker, API, and documentation exit criteria pass.

Update the relevant authentication and audit documentation to state that:

- Public registrations always receive the engineer role.
- Client-supplied registration roles are rejected.
- Login uses OAuth2 password form data.
- Search requires authentication.
- Project CREATE, UPDATE, and DELETE operations are audited.

### 2. Repair the Project Service/Repository Integration

Convert `project_service.py` to use the existing session-bound `ProjectRepository` class consistently.

Restore repository support for:

- Pagination
- Customer ID filtering
- Project status filtering
- Sorting by the previously intended fields:
  - `name`
  - `created_at`
  - `status`
- Ascending order
- Descending order
- Deterministic default ordering

Project service behavior will include:

- Customer existence validation during project creation.
- Customer existence validation when an update changes `customer_id`.
- Controlled missing-project behavior for update and delete.
- CREATE audit events.
- UPDATE audit events.
- DELETE audit events.
- Useful audit details including project name, customer ID, status, and changed fields where appropriate.

Project routers will:

- Instantiate the repaired project service with the request database session.
- Pass the authenticated user ID into project create, update, and delete operations.
- Translate expected missing-resource results into controlled HTTP 404 responses.
- Preserve admin-only project deletion.
- Preserve existing successful response shapes where practical.

### 3. Repair Unfinished PATCH-017 Code

Preserve the currently unused and undocumented `CustomerService.get_detail()` method for future implementation.

The method will be isolated and repaired rather than removed:

- Mark it as deprecated/internal until a documented router and response schema are approved.
- Move its direct customer/contact database query into `CustomerRepository`.
- Make the service delegate to the repository.
- Preserve its current return shape for compatibility.
- Return `None` for a missing customer.
- Do not expose a new API endpoint in PATCH-017.3.

Additional bounded cleanup:

- Remove the broken direct model/query dependency from the service.
- Remove duplicate imports in the customer router.
- Add controlled 404 behavior for missing customer update operations.
- Add controlled 404 behavior for missing customer delete operations.
- Add customer relationship validation during contact creation.
- Preserve existing customer audit behavior.
- Preserve existing contact audit behavior.
- Remove only obvious inconsistencies in files already touched by PATCH-017.3.

This work will not become a broad repository or response-format refactor.

### 4. Apply Critical Security Corrections

#### Public Registration

Separate the public registration request schema from the persisted user role.

The revised flow will:

1. Accept only public account fields.
2. Reject extra fields, including `role`.
3. Assign the engineer role server-side.
4. Validate the assigned role through the existing central `Role` enum.
5. Persist the validated role.
6. Continue returning role in `UserResponse`.

There will be no public or authenticated admin-role creation API in this patch.

#### Login

Change `/auth/login` from URL query parameters to the standard OAuth2 password form contract:

```http
POST /auth/login
Content-Type: application/x-www-form-urlencoded

username=engineer&password=secret
```

The endpoint path and token response will remain unchanged.

This is an intentional API compatibility change because credentials in URL query parameters can be recorded in logs, browser history, proxies, and monitoring systems.

#### Search Authentication

Require a valid access token for:

```text
GET /search/
```

Search query and response behavior will otherwise remain unchanged.

#### Central Role Validation

Reuse `app.permissions.roles.Role` as the central role definition.

Role-related changes will:

- Avoid defining a second role enum.
- Validate roles passed to role dependencies.
- Use `Role.ADMIN.value` and `Role.ENGINEER.value` rather than scattered string literals where touched.
- Reject unsupported role configuration rather than silently accepting it.

No new authorization framework will be introduced.

### 5. Establish PATCH-017 Regression Tests

Tests will use:

- `pytest`
- FastAPI `TestClient`
- `httpx`
- The existing Docker PostgreSQL service
- A dedicated `satco_platform_patch0173_test` database in that service
- SQLAlchemy dependency overrides
- PostgreSQL foreign-key and transaction behavior

The test application will exercise the real:

- Routers
- Authentication dependencies
- Services
- Repositories
- Models
- Schemas
- JWT generation and validation
- RBAC behavior
- Audit behavior

An admin fixture will be inserted directly into the dedicated PostgreSQL test database because public registration will correctly be unable to create administrators.

This strategy:

- Uses the same PostgreSQL backend and Docker environment as SATCO Platform.
- Does not modify the `satco_platform` development database.
- Does not introduce SQLite or another database backend.
- Does not require a migration.
- Provides deterministic setup and teardown.
- Supports endpoint-level regression testing.
- Keeps test mutations isolated in a clearly named test database.
- Uses per-test transaction rollback where practical and only cleans test-owned data.

### 6. Docker and Targeted Validation

After implementation:

1. Confirm the existing backend and PostgreSQL containers are running.
2. Confirm the backend container starts successfully.
3. Confirm the PostgreSQL container remains available.
4. Confirm PostgreSQL connectivity with a read-only query.
5. Run the complete automated test suite in Docker.
6. Run Python source compilation.
7. Run targeted read-only checks against the running API.
8. Fix failures caused by PATCH-017.3.
9. Re-run the complete test suite after repairs.
10. Create the implementation report using exact commands and results.

Mutation-oriented API tests will run only against `satco_platform_patch0173_test` in the existing Docker PostgreSQL service.

Read-only live-stack validation will include:

- `GET /` returns HTTP 200.
- `GET /openapi.json` returns HTTP 200.
- Protected endpoints reject missing credentials.
- Search rejects missing credentials.
- Login query-parameter usage no longer authenticates.
- PostgreSQL answers a read-only connectivity query.

## Exact Files to Create

### Documentation

- `docs/patches/PATCH-017.3.md`
- `docs/reviews/PATCH-017.3-Implementation-Report.md`

The implementation report will be created during final validation. It will state `INCOMPLETE` unless all exit criteria pass.

### Automated Tests

- `backend/tests/conftest.py`
- `backend/tests/test_auth.py`
- `backend/tests/test_customers.py`
- `backend/tests/test_contacts.py`
- `backend/tests/test_projects.py`
- `backend/tests/test_audit_logs.py`
- `backend/tests/test_search.py`

## Exact Files to Modify

### Documentation

- `docs/02_Roadmap.md`
- `docs/07_Backend_Blueprint.md`
- `docs/adr/ADR-004.md`
- `docs/adr/ADR-005.md`
- `docs/adr/ADR-010-Universal-Audit-Integration.md`

### API and Security

- `backend/app/api/v1/routers/auth.py`
- `backend/app/api/v1/routers/customers.py`
- `backend/app/api/v1/routers/contacts.py`
- `backend/app/api/v1/routers/projects.py`
- `backend/app/api/v1/routers/search.py`
- `backend/app/dependencies/auth.py`
- `backend/app/schemas/user.py`
- `backend/app/services/user_service.py`
- `backend/app/repositories/user_repository.py`
- `backend/app/permissions/roles.py`

### CRM and Projects

- `backend/app/repositories/project_repository.py`
- `backend/app/repositories/customer_repository.py`
- `backend/app/services/project_service.py`
- `backend/app/services/customer_service.py`
- `backend/app/services/contact_service.py`

## API Behavior Changes

| Endpoint | Current behavior | PATCH-017.3 behavior |
|---|---|---|
| `POST /auth/register` | Accepts client-controlled `role` | Rejects `role`; server assigns `engineer` |
| `POST /auth/login` | Reads credentials from URL query parameters | Reads OAuth2 form data |
| `GET /search/` | Public | Requires access token |
| `POST /projects/` | Broken repository call; no project audit | Works, validates customer, records CREATE audit |
| `GET /projects/` | Broken repository call | Restores pagination, filters, and sorting |
| `PUT /projects/{id}` | Broken repository call; no project audit | Works, validates relationships, controlled 404, records UPDATE audit |
| `DELETE /projects/{id}` | Broken repository call | Works, controlled 404, remains admin-only, records DELETE audit |
| `PUT /customers/{id}` | Missing customer can produce response validation failure | Missing customer returns 404 |
| `DELETE /customers/{id}` | Reports success for missing customer | Missing customer returns 404 |
| `POST /contacts/` | Relies on database failure for missing customer | Missing customer returns controlled 404 |

Endpoint paths and successful response models will otherwise remain compatible.

## Security Changes

### Registration Hardening

- Remove role selection from public registration.
- Reject attempted role injection.
- Assign engineer role server-side.
- Validate the assigned role centrally.
- Preserve role in authenticated/internal user representation.

### Credential Handling

- Remove username/password from login URL parameters.
- Use OAuth2-compatible form data.
- Keep the existing token response.

### Search Protection

- Require access-token authentication before returning CRM search results.

### Role Validation

- Reuse the existing `Role` enum.
- Validate dependency configuration centrally.
- Avoid unsupported or misspelled role values.

### Preserved Authorization

- Engineers remain able to use normal authenticated CRM/project operations.
- Project deletion remains admin-only.
- Audit-log access remains admin-only.
- Refresh tokens remain invalid for protected resource access.

## Dependency Changes

The running backend container currently does not contain `pytest` or `httpx`.

PATCH-017.3 will not create `requirements-dev.txt` and will not modify `backend/requirements.txt`. The current dependency-file structure will remain unchanged.

Additional tools required only to execute the regression suite are:

- `pytest`
- `httpx`

These test tools will be installed ephemerally in a disposable Docker backend test container or the currently running development container for the duration of validation. They will not be recorded as a project dependency change in this patch.

Any package download requiring network access will use the normal approval mechanism. The implementation report will record the exact package-installation and test commands used.

No new runtime framework or production service will be added.

## Planned Test Cases

### Registration and Login

- Successful public registration returns a user.
- Public registration assigns the engineer role.
- Submitted `role=admin` is rejected.
- Submitted unsupported role is rejected as an extra public field.
- Duplicate email returns a controlled error.
- Duplicate username returns a controlled error.
- Valid OAuth2 form login returns access and refresh tokens.
- Invalid username returns 401.
- Invalid password returns 401.
- Query-parameter login no longer authenticates.

### Authentication Failures

- Missing access token returns 401.
- Malformed token returns 401.
- Unknown token subject returns 401.
- Refresh token used as an access token returns 401.
- Inactive user is rejected.

### Admin Versus Engineer Authorization

- Engineer cannot delete a project.
- Admin can delete a project.
- Engineer cannot access audit logs.
- Admin can access audit logs.
- Invalid configured role requirements are rejected centrally.

### Customer CRUD and Missing Records

- Authenticated customer creation succeeds.
- Customer listing succeeds.
- Customer search succeeds.
- Customer pagination works.
- Customer update succeeds.
- Missing customer update returns 404.
- Customer deletion succeeds.
- Missing customer deletion returns 404.
- Customer CREATE audit remains present.
- Customer UPDATE audit remains present.
- Customer DELETE audit remains present.

### Contact CRUD and Customer Validation

- Contact creation with an existing customer succeeds.
- Contact creation with a missing customer returns 404.
- Contact retrieval succeeds.
- Contact listing succeeds.
- Contact customer filtering works.
- Contact update succeeds.
- Missing contact update returns 404.
- Contact deletion succeeds.
- Missing contact deletion returns 404.
- Contact CREATE audit remains present.
- Contact UPDATE audit remains present.
- Contact DELETE audit remains present.

### Project CRUD, Filtering, Sorting, and Pagination

- Project creation with a valid customer succeeds.
- Project creation with a missing customer returns 404.
- Project listing succeeds.
- Project pagination returns correct page and size.
- Project customer filtering works.
- Project status filtering works.
- Project sorting by name works.
- Project sorting by creation date works.
- Project sorting by status works.
- Ascending ordering works.
- Descending ordering works.
- Project update succeeds.
- Project customer reassignment to an existing customer succeeds.
- Project reassignment to a missing customer returns 404.
- Missing project update returns 404.
- Engineer project deletion returns 403.
- Admin project deletion succeeds.
- Missing project deletion returns 404.

### Project Audit Events

- Project CREATE writes an audit event.
- Project UPDATE writes an audit event.
- Project DELETE writes an audit event.
- Audit events contain the acting user ID.
- Audit events contain the project ID.
- CREATE details contain useful project metadata.
- UPDATE details identify useful project metadata and changed fields.
- DELETE details preserve entity information after deletion.

### Audit-Log Access

- Missing authentication returns 401.
- Engineer access returns 403.
- Admin access succeeds.
- Audit results are paginated.
- Project audit events are returned.
- Existing customer audit events are returned.
- Existing contact audit events are returned.

### Search Authentication

- Search without authentication returns 401.
- Search with an invalid token returns 401.
- Authenticated search succeeds.
- Existing customer results are preserved.
- Existing contact results are preserved.
- Existing project results are preserved.

## Docker Validation Commands and Steps

Exact commands may be adjusted only if the environment requires an equivalent non-destructive form. Planned validation includes:

```bash
docker compose ps
```

```bash
docker compose exec -T postgres \
  psql -U satco -d postgres -X \
  -c "SELECT 1 FROM pg_database WHERE datname = 'satco_platform_patch0173_test';"
```

```bash
docker compose exec -T postgres \
  psql -U satco -d postgres -X \
  -c "CREATE DATABASE satco_platform_patch0173_test;"
```

The database-creation command will run only when the read-only existence check confirms the dedicated test database is absent. It creates a new test-owned database and does not alter `satco_platform`.

Because the regular backend image does not include the test tools, tests will run in a disposable backend container without changing dependency files:

```bash
docker compose run --rm backend sh -c \
  "python -m pip install pytest httpx && \
   TEST_DATABASE_URL=postgresql://satco:satco_password@postgres:5432/satco_platform_patch0173_test \
   python -m pytest -q"
```

Source validation:

```bash
docker compose exec -T backend python -m compileall -q app tests
```

PostgreSQL connectivity:

```bash
docker compose exec -T postgres \
  psql -U satco -d satco_platform -X -c "SELECT 1;"
```

Targeted live API checks:

```bash
curl -sS -o /dev/null -w "%{http_code}\n" \
  http://127.0.0.1:8000/
```

```bash
curl -sS -o /dev/null -w "%{http_code}\n" \
  http://127.0.0.1:8000/openapi.json
```

```bash
curl -sS -o /dev/null -w "%{http_code}\n" \
  http://127.0.0.1:8000/search/?q=test
```

Expected unauthenticated search status:

```text
401
```

Mutation-oriented API validation will be performed against the dedicated PostgreSQL test database, not the `satco_platform` development database.

## Risks and Mitigations

### Risk: Login Compatibility Break

Clients currently sending login credentials as query parameters will need to send form data.

Mitigation:

- Keep the endpoint path unchanged.
- Keep the token response unchanged.
- Document the change before implementation.
- Add regression tests for the new form contract.
- Confirm query-parameter authentication is disabled.

### Risk: Registration Compatibility Break

Clients currently sending a role field will receive HTTP 422.

Mitigation:

- Document that role assignment is server-controlled.
- Preserve all normal public registration fields.
- Preserve role in the response.
- Test both valid registration and attempted role injection.

### Risk: Search Becomes Protected

Unauthenticated callers will receive HTTP 401.

Mitigation:

- This is an intentional security correction aligned with protected CRM data.
- Keep the endpoint path, parameters, and authenticated response behavior unchanged.
- Update ADR and backend documentation.

### Risk: Project Query Semantics

Restoring filters and sorting could differ from behavior before PATCH-017.2.

Mitigation:

- Restore only the fields visible in the existing router and pre-PATCH-017.2 repository history.
- Add explicit tests for every supported filter/sort option.
- Retain existing default query parameters.

### Risk: Test Database Isolation

The test suite will share the existing PostgreSQL server process with the development database.

Mitigation:

- Use the explicit database name `satco_platform_patch0173_test`.
- Refuse to run mutation tests when the configured database name is not the expected test name.
- Never point test dependency overrides at `satco_platform`.
- Create tables only in the dedicated test database.
- Use transaction rollback and test-owned cleanup.
- Do not drop the database without a separate destructive-action approval.
- Confirm development-table row counts are not used or changed by the test setup.

### Risk: Docker Dependency Installation

Installing `pytest` and `httpx` may require network access and could lengthen test execution.

Mitigation:

- Keep dependency files unchanged.
- Install `pytest` and `httpx` only for the validation run.
- Use a disposable Docker test container when practical.
- Request network approval if required.

### Risk: Existing Untracked Documentation

`docs/reviews/PATCH-017-Technical-Review.md` is currently untracked.

Mitigation:

- Preserve it unchanged.
- Do not overwrite or remove it.
- Include it accurately in final Git status reporting.

### Risk: Scope Expansion

Testing may reveal debt outside PATCH-017.3, including migration defects or response-format inconsistencies.

Mitigation:

- Fix only failures caused by or directly blocking mandatory PATCH-017.3 behavior.
- Record unrelated findings as remaining issues.
- Do not begin PATCH-018 work.
- Ask for approval if a broad refactor or migration becomes necessary.

## Rollback Considerations

No migration or schema rollback is planned because PATCH-017.3 does not change the database schema.

Before implementation:

- Capture `git status`.
- Preserve all pre-existing user changes.
- Identify every PATCH-017.3 file explicitly.

If implementation must be rolled back:

- Revert only PATCH-017.3-created files and PATCH-017.3 hunks.
- Do not use `git reset --hard`.
- Do not use destructive checkout commands against the repository.
- Do not delete or reset PostgreSQL data.
- Do not remove the existing technical review.
- Request approval before any destructive rollback action.

Docker rollback:

- Rebuilding or recreating the backend container does not alter the bound PostgreSQL data directory.
- The PostgreSQL container and volume will not be recreated or removed.
- `docker compose down -v`, volume deletion, and database resets are prohibited.
- A disposable test container may be removed automatically without affecting application data.

API rollback:

- If form login, protected search, or registration validation causes an unexpected blocking regression, the patch remains `INCOMPLETE`.
- Compatibility will not be restored by reintroducing insecure query credentials or public role selection without explicit architectural approval.

## Acceptance Criteria

PATCH-017.3 implementation is acceptable when:

- Project CRUD calls the existing `ProjectRepository` class correctly.
- Project pagination, filtering, and sorting work.
- Missing projects and missing customer relationships produce controlled responses.
- Project CREATE, UPDATE, and DELETE generate audit records.
- Customer and contact audit behavior remains functional.
- `CustomerService.get_detail()` is preserved, isolated as deprecated/internal behavior, and delegates database access to `CustomerRepository`.
- Duplicate PATCH-017 imports and direct related inconsistencies are removed.
- Public registration cannot select admin or another role.
- Public registration assigns engineer server-side.
- Role values are centrally validated.
- Login credentials use form data rather than URL parameters.
- Search requires authentication.
- All mandatory regression tests exist and pass.
- Backend starts in Docker.
- PostgreSQL connectivity passes.
- Targeted API validation passes.
- Documentation matches the implemented behavior.

## Exit Criteria

PATCH-017 will not be marked complete unless:

- The full automated suite passes in Docker.
- Targeted API validation passes.
- Python source compilation passes.
- PostgreSQL connectivity passes.
- No PATCH-017.3 regression remains.
- No unrelated source files were changed.
- The implementation report contains exact commands and results.
- Git diff and status are reviewed.
- No migration was required.
- No existing data was deleted or reset.

If any required criterion fails, the implementation report will state:

```text
PATCH STATUS: INCOMPLETE
PRODUCTION READINESS: NOT READY
```

## Approval Gates

### Gate 1 — Implementation Approval

Current gate.

No implementation or documentation changes beyond this plan document may begin until the user approves this Phase 1 plan.

### Gate 2 — Expanded Scope Approval

Stop and request approval if implementation requires:

- A migration
- A database schema change
- A broad architectural refactor
- A destructive action
- Changes outside the listed files
- Changes that begin PATCH-018

### Gate 3 — Destructive Action Approval

Explicit approval is required before:

- Deleting data
- Resetting a database
- Removing a Docker volume
- Destructive Git operations
- Replacing existing user work

No such action is planned.

### Gate 4 — Git Commit Approval

After successful implementation and validation:

- Show exact files created.
- Show exact files modified.
- Show API and security changes.
- Show test commands and results.
- Show remaining issues.
- Show `git diff --stat`.
- Show `git status`.
- Propose:

```text
PATCH-017.3: Final recovery and stabilization
```

Wait for explicit user approval before committing.

### Gate 5 — Push Approval

No GitHub push is authorized by this patch. A commit approval does not authorize a push.

## Planned Final Delivery Format

The final delivery will report:

```text
PATCH STATUS:
COMPLETED or INCOMPLETE

Implemented Changes:
- Exact list

Files Created:
- Exact list

Files Modified:
- Exact list

API Changes:
- Exact list

Security Corrections:
- Exact list

Tests Executed:
- Commands and results

Remaining Issues:
- Exact list, or None

Production Readiness:
READY or NOT READY

Git:
- Git diff summary
- Git status
- Proposed commit message
```

No commit will be made before explicit approval.
