# SATCO Backend Blueprint

Version: 1.0
Status: Active
Last Updated: 2026-07-25

---

# Goal

Build a scalable, maintainable and modular backend using FastAPI.

---

# Folder Structure

app/

api/

core/

config/

db/

models/

schemas/

repositories/

services/

ai/

jobs/

workflows/

storage/

auth/

permissions/

utils/

tests/

---

# Layer Responsibilities

## API

Receive requests.

Return responses.

No business logic.

---

## Services

Business logic.

Project workflow.

Engineering logic.

AI orchestration.

---

## Repositories

Database access only.

---

## Models

SQLAlchemy models.

---

## Schemas

Pydantic request/response models.

---

## AI

Context Builder

Prompt Builder

AI Router

Engineering Analyzer

Planner

Reviewer

Knowledge Manager

---

## Jobs

Background processing.

Long-running AI tasks.

Document analysis.

---

## Storage

File upload.

File versioning.

Document retrieval.

---

# Auth

Authentication.

Authorization.

JWT.

---

# Authentication Architecture

SATCO Platform uses JWT-based authentication as the foundation of user identity management.

Authentication is implemented as an independent security layer and is separated from API routes.

---

# Authentication Flow

Client

↓

API Router

↓

Service Layer

↓

Repository Layer

↓

Database

---

# Password Security

Rules:

- Raw passwords are never stored.
- Passwords are hashed before database persistence.
- Password verification is performed through secure hash comparison.

Implementation:

pwdlib[argon2]

---

# Token Strategy

SATCO Platform uses two JWT token types.

## Access Token

Purpose:

- API request authorization.
- Short-term identity validation.
- Protecting API endpoints.

Usage:

Authorization: Bearer <access_token>

---

## Refresh Token

Purpose:

- Session renewal.
- Generating new access tokens.
- Maintaining user sessions.

---

# Authentication Dependency

JWT validation is handled by:

app/dependencies/auth.py

Responsibilities:

- Extract Bearer token.
- Validate JWT signature.
- Validate token type.
- Extract user identity.
- Protect API endpoints.

---

# Authorization Foundation

Authentication provides the foundation for future Role-Based Access Control (RBAC).

Future structure:

User

↓

Role

↓

Permissions

---

Planned roles:

- admin
- engineer
- project_manager
- customer

---

# Architectural Rules

Business logic belongs ONLY inside Services.

Database logic belongs ONLY inside Repositories.

Authentication logic must remain separated from business logic.

---

# Patch-016 Implementation Status

Completed:

- User registration
- Password hashing
- Password verification
- JWT access token generation
- JWT refresh token generation
- JWT validation dependency
- Protected endpoint support

---

# PATCH-017.3 Security and Stabilization Contract

Status:

Completed

## Public Registration

Public registration accepts user identity and password fields only.

Rules:

- Public clients cannot select a role.
- Public registrations receive the `engineer` role server-side.
- Supported persisted roles are validated through the central Role enum.
- Administrative role assignment requires a future protected administration workflow and is not part of PATCH-017.3.

## Login Request

`POST /auth/login` uses the OAuth2 password form contract:

```text
Content-Type: application/x-www-form-urlencoded
```

Credentials must not be accepted through URL query parameters.

## Protected Search

`GET /search/` requires a valid JWT access token because search results contain protected CRM and Project information.

## Project Service

Project business logic uses the session-bound `ProjectRepository`.

Supported Project list behavior:

- Pagination
- Customer filtering
- Status filtering
- Sorting by name, created time, or status
- Ascending or descending order

Project CREATE, UPDATE, and DELETE operations must:

- Validate referenced Customers.
- Return controlled missing-resource responses.
- Record audit events after successful operations.

## PATCH-017.3 Testing

Regression tests use the existing Docker PostgreSQL service and a dedicated PATCH-017.3 test database.

SQLite or another database backend must not be introduced.

The application dependency structure remains unchanged; test tools are installed ephemerally during validation.

---

# PATCH-018.1 Project Core Contract

Status:

Completed

## Project Reference

Projects use:

```text
SAT-PRJ-YYYY-NNNN
```

as their immutable human-facing reference. Integer `id` remains the internal primary key and route identifier.

Project Codes are allocated with a PostgreSQL atomic yearly counter and protected by a unique database constraint.

## Project Layers

Router:

- Typed query and request validation
- Authentication
- OpenAPI examples
- Controlled HTTP responses

Service:

- Lifecycle rules
- Ownership and primary-assignment permissions
- Relationship validation
- Date/progress validation
- Project Code orchestration
- Audit snapshots and structured logs

Repository:

- PostgreSQL Project Code allocation
- Persistence
- Filtering and allow-listed sorting
- Eager loading
- Exact Project Code retrieval

## Project Relationships

- Required Customer
- Owner
- Optional primary assignee

The only primary-assignment API names are:

- `primary_assignee_id`
- `primary_assignee`

## Project Search

Authenticated Project search supports:

- Existing Project name matching
- Exact Project Code matching
- Partial Project Code matching

## Project Progress

Progress is manually maintained from 0 through 100 in PATCH-018.1. Completed Projects have progress 100; non-completed Projects cannot have progress 100.

A future Milestone/Task patch may derive the existing `progress` field from child entities.

## Project API Documentation

All Project endpoints include focused OpenAPI examples for successful and applicable validation, authentication, authorization, and missing-resource responses.

---

# PATCH-019 Production Infrastructure Hardening

Status:

Completed

## Schema Ownership

Alembic is the exclusive schema creation and evolution authority.

The backend must not call:

```python
Base.metadata.create_all()
```

Application import and startup are schema read-only. Missing or outdated schema is a deployment error and is not repaired by the API process.

## Deployment Order

The supported deployment sequence is:

```text
Database backup and preflight
    -> alembic upgrade head
        -> schema verification
            -> backend startup
                -> API health validation
```

Alembic does not run automatically during normal backend startup.

## Migration Configuration

Migration commands require either:

- `ALEMBIC_DATABASE_URL`, or
- the complete `DATABASE_HOST`, `DATABASE_PORT`, `DATABASE_USER`, `DATABASE_PASSWORD`, and `DATABASE_NAME` settings.

Test execution retains an exact dedicated-database name guard and requires the database to be migrated to the expected head before test collection.

## Reproducibility

The repaired migration chain creates:

- Users
- Customers
- Contacts
- Legacy Projects and Customer relationship
- Audit Logs
- PATCH-018.1 Project Core schema

from an empty PostgreSQL database without model-driven schema creation.

Existing databases already stamped past repaired historical revisions do not replay those revisions. The first pending migration validates and reconciles known compatible objects created by the former startup behavior.

Architecture and compatibility policy are defined by:

```text
ADR-012 — Alembic Schema Ownership and Historical Repair
```
