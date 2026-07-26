# PATCH-019 Future Recommendations

**Project:** SATCO Platform
**Patch:** PATCH-019 — Production Infrastructure Hardening
**Date:** 2026-07-26

These recommendations are outside PATCH-019 and require separately approved
work.

## Priority 1 — Deployment Automation

- Add an explicit migration job before backend rollout.
- Require database backup and preflight evidence.
- Block backend deployment when Alembic current does not equal head.
- Add post-migration schema and API health checks.

## Priority 2 — Continuous Integration

- Create a new PostgreSQL database per CI migration job.
- Run `alembic upgrade head` from zero.
- Run `alembic check`.
- Run the complete PostgreSQL regression suite.
- Validate the existing-baseline compatibility fixture.
- Preserve exact database-name safety guards.

## Priority 3 — Dependency Management

- Pin runtime and test dependency versions.
- Add pytest and the supported Starlette HTTP test client to an explicit
  development dependency group.
- Define a controlled dependency upgrade process.

## Priority 4 — Deprecation Cleanup

- Replace naive `datetime.utcnow()` defaults with timezone-aware UTC values.
- Replace remaining Pydantic class-based configuration with `ConfigDict`.
- Resolve the Starlette HTTP-client compatibility warning.

## Priority 5 — Migration Operations

- Add a documented backup restoration drill.
- Add migration duration and lock monitoring.
- Define operational handling for failed transactional and non-transactional
  DDL.
- Add a policy for future historical migration immutability now that the chain
  is reproducible.

## Validation Environment Cleanup

The dedicated database and isolated schemas remain present because deletion was
not authorized. Remove them only under a separately approved destructive
cleanup action.
