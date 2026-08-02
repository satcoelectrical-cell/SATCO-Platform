# IDS-025 — Authenticated Organization Context

## Status

Approved

## Exact Authorized File Set

Create:

- `backend/app/models/organization.py`
- `backend/app/exceptions/organization_context.py`
- `backend/migrations/versions/e02500000001_authenticated_organization_context.py`
- `backend/tests/test_authenticated_organization_context.py`

Modify:

- `backend/app/models/__init__.py`
- `backend/app/dependencies/auth.py`

No other file is authorized.

## Persistence Contract

`organizations`:

- `id`: UUID primary key;
- `is_active`: non-null Boolean, default true;
- `created_at`, `updated_at`: non-null timezone-aware timestamps.

`user_organization_memberships`:

- `user_id`: User foreign key, RESTRICT, composite primary key;
- `organization_id`: Organization UUID foreign key, RESTRICT, composite primary key;
- `is_enabled`: non-null Boolean, default true;
- `is_selected`: non-null Boolean, default false;
- `created_at`, `updated_at`: non-null timezone-aware timestamps;
- check constraint `NOT is_selected OR is_enabled`;
- partial unique index on `user_id WHERE is_selected`.

## Dependency Contract

Add a parallel `get_current_user_organization_context` dependency. It reuses
`get_current_user`, queries selected membership joined to Organization, and
requires membership enabled and Organization active. It returns an immutable
context containing the current User and Organization UUID.

It raises `ActiveOrganizationContextRequired`, status 403, code
`ACTIVE_ORGANIZATION_CONTEXT_REQUIRED`, for zero or non-unique valid selection.
It accepts no Organization argument from transport.

## Migration Contract

Revision `e02500000001` uses the repository head present at implementation as
its sole parent. Upgrade creates only the two tables and selected-membership
index. Downgrade removes only those objects.

## Tests

Cover valid resolution, absent membership, disabled membership, inactive
Organization, multiple-selection database prevention, client input
irrelevance, and cross-Organization denial.

## Approval

IDS-025 is approved for IRR-025.
