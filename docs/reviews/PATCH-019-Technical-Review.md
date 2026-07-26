# PATCH-019 Technical Review

**Project:** SATCO Platform
**Patch:** PATCH-019 — Production Infrastructure Hardening
**Review date:** 2026-07-26
**Source of Truth:** `/docs`
**Git commit:** Not created

## Review Outcome

**APPROVED FOR FINAL REPOSITORY REVIEW**

PATCH-019 establishes Alembic as the exclusive schema creation and evolution
authority. The application and test bootstrap no longer call
`Base.metadata.create_all()`, the historical revision chain initializes a fresh
PostgreSQL database, and the pending Project Core migration reconciles the
known schema produced by the former startup behavior.

## Scope Review

The implementation is limited to Production Infrastructure Hardening:

- No platform feature was added.
- No domain field was added.
- No API was added.
- No router, service, repository, permission, or lifecycle behavior changed.
- PostgreSQL remains the only test and production database.

## Architecture Review

ADR-012 defines the final ownership contract:

```text
Alembic
    -> creates and evolves PostgreSQL schema

SQLAlchemy metadata
    -> maps schema and provides Alembic comparison metadata

Application startup
    -> assumes a migrated schema and emits no DDL
```

Normal backend startup does not run Alembic. Deployments must migrate and verify
the database before starting the corresponding application version.

## Migration-Chain Review

The revision identifiers and linear chain remain intact:

```text
d25733017b10
    -> c1ca2821f651
        -> 46350c98183b
            -> b969ae9217a0
                -> d8271b8f1a29
                    -> f18a1c0e2026
```

Repairs:

- `d25733017b10` creates Users and the legacy Project schema.
- `c1ca2821f651` creates Customers.
- `46350c98183b` creates Contacts and its Customer foreign key.
- `b969ae9217a0` validates and migrates the legacy Project Customer name to
  `customer_id`.
- `d8271b8f1a29` creates Audit Logs with live/model-compatible nullability.
- `f18a1c0e2026` supports absent or compatible pre-existing
  `project_code_sequences` tables.

Existing databases stamped past repaired historical revisions do not replay
them. Compatibility logic is confined to the first pending revision.

## Compatibility Review

The existing development schema was reproduced in the isolated
`patch019_compat` schema at `d8271b8f1a29`.

Controlled fixtures included:

- 1 User
- 1 Customer
- 1 Contact
- 2 legacy Projects
- 1 Audit Log
- Existing Project Code counters for 2024 and 2025

Upgrade results:

- All fixture rows were preserved.
- Project Codes became `SAT-PRJ-2024-0001` and
  `SAT-PRJ-2024-0002`.
- The existing 2024 counter remained 7 rather than regressing to 2.
- The existing 2025 counter remained 3.
- The unintended `year` sequence default was removed.
- Primary-key and check-constraint naming was normalized.

## Schema Parity Review

Both corrected validation schemas reported:

```text
f18a1c0e2026 (head)
```

`alembic check` reported:

```text
No new upgrade operations detected.
```

Validated schema elements include:

- Tables and columns
- PostgreSQL types
- Nullability
- Defaults
- Primary and unique constraints
- Check constraints
- Customer, owner, and primary-assignee foreign keys
- Approved indexes
- Project Code counters and format

## Runtime and Test Review

Application import against the isolated migrated schema preserved the table
count:

```text
before import = 7
after import  = 7
```

The complete PostgreSQL regression suite passed:

```text
29 passed, 66 warnings in 4.80s
```

Warnings are existing Starlette/httpx, Pydantic configuration, and naive UTC
datetime deprecations. They do not block PATCH-019.

## Development Database Safety

The development database was never migrated or mutated.

Final read-only fingerprint:

```text
revision=d8271b8f1a29
projects=7
customers=5
users=2
```

## Technical Debt

Non-blocking future work:

- Add migration validation to CI.
- Pin development/test dependencies.
- Replace deprecated Pydantic class configuration.
- Replace naive `datetime.utcnow()` defaults.
- Add an explicit deployment migration job to production automation.
