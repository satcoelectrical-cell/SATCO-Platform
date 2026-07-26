# PATCH-017.3 — PATCH-017 Final Recovery and Stabilization

Version: 1.0
Status: Completed
Date: 2026-07-26

## Objective

Complete and stabilize the functionality already intended by PATCH-017 without beginning PATCH-018 feature development.

## Scope

PATCH-017.3:

- Repairs the Project service/repository integration.
- Restores Project filtering, sorting, and pagination.
- Adds controlled Project and customer-relationship not-found behavior.
- Audits Project CREATE, UPDATE, and DELETE operations.
- Preserves Customer and Contact auditing.
- Preserves `CustomerService.get_detail()` as isolated, deprecated internal behavior while moving its database access into the repository layer.
- Prevents public registration from selecting a role.
- Assigns the engineer role to public registrations server-side.
- Validates supported roles centrally.
- Changes login credentials from URL query parameters to OAuth2 form data.
- Protects search with access-token authentication.
- Adds PostgreSQL-backed regression tests.

## Exclusions

PATCH-017.3 does not:

- Begin PATCH-018.
- Add project files, milestones, dashboards, workflows, or other Project Management Enhancement features.
- Change the application database schema.
- Add or run a migration.
- Add a second database backend.
- Restructure dependency files.
- Add refresh-token rotation, soft deletion, UUIDs, or API version-prefix changes.

## Acceptance Criteria

- Project list, create, update, and delete operations use `ProjectRepository`.
- Project customer/status filtering, sorting, and pagination work.
- Missing Projects and customer relationships return controlled HTTP 404 responses.
- Project CREATE, UPDATE, and DELETE each create an audit record with useful entity details.
- Existing Customer and Contact audit behavior continues to work.
- Public registration rejects role input and creates engineer users.
- Login accepts OAuth2 form credentials and no longer accepts credentials through URL query parameters.
- Search requires a valid access token.
- Engineer users cannot delete Projects or read audit logs.
- Admin users can delete Projects and read audit logs.
- All mandatory regression tests pass against the existing Docker PostgreSQL service.
- Backend startup, PostgreSQL connectivity, source compilation, and targeted API validation pass.

## Security Impact

- Removes client-controlled public role assignment.
- Centralizes validation of supported role values.
- Prevents credentials from being supplied in the login URL.
- Prevents unauthenticated access to CRM search results.
- Preserves admin-only Project deletion and audit-log access.

## API Impact

### Intentional Changes

- `POST /auth/register` rejects a `role` field; the server assigns `engineer`.
- `POST /auth/login` accepts `application/x-www-form-urlencoded` OAuth2 password form data.
- `GET /search/` requires bearer-token authentication.

### Restored Behavior

- `GET /projects/` restores pagination, customer/status filtering, and sorting.
- Project create/update/delete operations no longer call removed repository functions.
- Missing Project and relationship cases return HTTP 404 instead of unhandled failures.

Endpoint paths and successful response shapes otherwise remain unchanged.

## Database Impact

No application schema changes or migrations are required.

Regression tests use a dedicated `satco_platform_patch0173_test` database in the existing Docker PostgreSQL service. The test configuration must refuse mutation tests unless that exact database name is used. Existing `satco_platform` data must not be modified.

## Dependency Impact

The existing dependency-file structure remains unchanged.

`pytest` and `httpx` are test execution tools required in the Docker validation environment. They are installed ephemerally for validation and are not added to `requirements.txt` or a new requirements file.

## Test Strategy

Regression tests cover:

- Registration and OAuth2 form login
- Role-injection prevention
- Authentication failures and inactive users
- Admin versus engineer authorization
- Customer CRUD, missing records, pagination, search, and audit events
- Contact CRUD, relationship validation, filtering, missing records, and audit events
- Project CRUD, relationship validation, filtering, sorting, pagination, missing records, authorization, and audit events
- Admin-only audit-log access
- Search authentication and existing result behavior

Tests run against PostgreSQL through FastAPI dependency overrides. Test tables and mutations are isolated in the dedicated PATCH-017.3 test database.

## Exit Criteria

PATCH-017 is marked complete only when:

- Implementation matches this definition.
- All automated tests pass in Docker.
- Backend startup and PostgreSQL connectivity pass.
- Targeted API checks pass.
- Source compilation passes.
- Documentation matches implementation.
- The implementation report records exact commands and results.

If any exit criterion fails, PATCH-017 remains incomplete and not production ready.
