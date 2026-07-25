# ADR-009: Audit Service Expansion and Audit Query API

## Status

Accepted

## Date

2026-07-25


# Context

SATCO Platform requires complete operational traceability.

The initial audit implementation records project deletion events.

As the platform grows, all critical business operations must be recorded and accessible through a controlled interface.


# Decision

The Audit module will be expanded into a centralized service.


# Audit Events

The system will record:

- PROJECT_CREATED
- PROJECT_UPDATED
- PROJECT_DELETED
- CUSTOMER_CREATED
- CUSTOMER_UPDATED
- DOCUMENT_GENERATED
- AI_APPROVAL
- EMAIL_SENT
- WORKFLOW_EXECUTED


# Audit Query API

A protected API will provide audit history.


Endpoint:

GET /audit-logs/


Access:

Admin only


Features:

- Pagination
- Sorting
- Future filtering support


# Security

Audit data contains sensitive operational information.

Rules:

- Engineers cannot access audit logs
- Administrators can review audit history


# Architecture Impact

This creates the foundation for:

- Enterprise compliance
- User accountability
- AI operation tracking
- Future event-driven architecture


All future modules should integrate with the Audit Service.
