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
