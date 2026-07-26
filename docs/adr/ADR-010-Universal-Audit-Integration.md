# ADR-010: Universal Audit Integration

## Status
Accepted

## Context

SATCO Platform requires a centralized audit mechanism to track
important user actions across business entities.

The initial implementation introduced audit logging for protected
project deletion operations.

As the platform grows, audit logging must become a reusable service
integrated with multiple domain services.

## Decision

Audit logging will be handled through a centralized Audit Service.

Business services are responsible for triggering audit events after
successful operations.

The Audit Service will store:

- User identity
- Action type
- Entity type
- Entity identifier
- Metadata/details
- Timestamp

## Supported Actions

Initial supported actions:

- CREATE
- UPDATE
- DELETE

Initial entities:

- Projects
- Customers
- Contacts

## PATCH-017.3 Required Coverage

The initial entities must record all three supported actions:

| Entity | CREATE | UPDATE | DELETE |
|---|---:|---:|---:|
| Project | Required | Required | Required |
| Customer | Required | Required | Required |
| Contact | Required | Required | Required |

Project audit details must preserve useful entity information, including the Project name, customer identifier, and status where available. UPDATE events should identify changed fields.

Business services trigger audit events only after the corresponding operation succeeds.

## Architecture

Request

↓

API Router

↓

Service Layer

↓

Repository Layer

↓

Audit Service

↓

audit_logs table


## Benefits

- Centralized history tracking
- Better accountability
- Future activity timeline support
- Easier compliance reporting
- Foundation for AI-assisted operational insights

## Future Extension

The audit system may later support:

- Change diff tracking
- Before/after values
- AI-generated summaries
- Project activity timeline
