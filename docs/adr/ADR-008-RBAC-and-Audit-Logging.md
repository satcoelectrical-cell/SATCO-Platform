# ADR-008: RBAC and Audit Logging Architecture

## Status
Accepted

## Date
2026-07-25

## Related Implementation
Commit:
Implement RBAC protected project deletion with audit logging


# 1. Context

SATCO Platform is an AI-powered engineering management platform.

As the platform grows, access control and operational traceability become critical requirements.

The system must guarantee:

- Secure authentication
- Role based authorization
- Protection of sensitive operations
- Complete history of important actions
- Accountability for user activities


# 2. Authentication Architecture

SATCO Platform uses JWT based authentication.

Authentication flow:

User
 |
 v
Login Endpoint
 |
 v
Credential Validation
 |
 v
JWT Access Token + Refresh Token
 |
 v
Protected API Resources


Current implementation:

- JWT Access Token
- JWT Refresh Token
- User identity extraction from token
- Protected FastAPI routes


# 3. Authorization Architecture (RBAC)

SATCO Platform uses Role Based Access Control.

Current roles:


## Admin Role

The administrator has full system privileges.

Permissions:

- Create projects
- Update projects
- Delete projects
- Manage system resources
- Perform administrative operations


## Engineer Role

Engineering users operate within project workflows.

Permissions:

- View projects
- Create engineering data
- Update assigned engineering information


Restrictions:

- Cannot delete projects
- Cannot execute administrative operations


# 4. Protected Operations

Sensitive endpoints must validate user permissions before execution.

Example:

DELETE /projects/{project_id}


Required permission:

admin role only


Unauthorized behavior:

Engineer attempting delete:

HTTP 403 Forbidden


Authorized behavior:

Admin attempting delete:

HTTP 200 Success


# 5. Audit Logging Architecture

SATCO Platform records important user activities.

The audit system provides:

- Who performed the action
- What action happened
- Which entity was affected
- When the operation occurred
- Additional operation details


# 6. Audit Database Design

Table:

audit_logs


Fields:

- id
- user_id
- action
- entity
- entity_id
- details
- created_at


Example:

{
  "user_id": 1,
  "action": "DELETE",
  "entity": "PROJECT",
  "entity_id": 12,
  "details": {
      "project_name": "AUDIT FINAL DELETE TEST"
  }
}


# 7. Current Backend Implementation

Implemented modules:

Authentication:

- JWT authentication
- Login endpoint
- Refresh token mechanism


Authorization:

- Role dependency
- Admin permission validation
- Protected project deletion


Audit:

- AuditLog database model
- Audit migration
- Audit service
- Delete project audit record creation


# 8. Database Migration

Migration:

d8271b8f1a29_create_audit_logs_table


Database:

PostgreSQL


# 9. Architecture Principles

All future modules must follow:

- Security first
- Permission validation before execution
- Critical actions must be auditable
- Database is the source of truth
- AI suggestions require human approval


# 10. Future Evolution

Audit system will evolve into an event-driven architecture.

Future events:

PROJECT_CREATED

PROJECT_UPDATED

PROJECT_DELETED

CUSTOMER_CREATED

CUSTOMER_UPDATED

DOCUMENT_GENERATED

AI_APPROVAL

EMAIL_SENT

WORKFLOW_EXECUTED


Future goal:

Create a centralized SATCO Event and Audit Service.


# 11. Architectural Impact

This decision establishes the foundation for:

- Enterprise security
- Compliance readiness
- User accountability
- AI operation traceability
- Multi-user collaboration


All future SATCO Platform services must integrate with this architecture.
