# SATCO Platform Database Blueprint

Version: 1.0
Status: Active
Last Updated: 2026-07-25

---

# Purpose

This document defines the long-term database architecture of SATCO Platform.

The database is designed to support an AI-assisted Engineering Platform.

---

# Core Domains

## Identity

- Users
- Roles
- Permissions

---

## CRM

- Companies
- Customers
- Contacts

---

## Projects

- Projects
- Project Members
- Project Milestones
- Project Status
- Project Files

### PATCH-018.1 Project Core

Project remains internally identified by integer `id`.

The human-facing Project reference is:

```text
SAT-PRJ-YYYY-NNNN
```

`project_code` is required, unique, indexed, immutable, and generated server-side with a concurrency-safe PostgreSQL yearly sequence.

Project core fields include:

- Customer
- Description
- Status
- Priority
- Owner
- Primary assignee
- Start date
- Target completion date
- Completion timestamp
- Progress
- Created and updated timestamps

The approved primary assignment names are:

- `primary_assignee_id`
- `primary_assignee`

Progress is manually maintained in PATCH-018.1 and may become system-derived in a future Milestone/Task patch without renaming the field.

---

## Engineering

- Disciplines
- Engineering Documents
- Document Types
- Engineering Notes
- Engineering Reviews
- Engineering Standards

---

## AI Brain

- AI Jobs
- AI Analyses
- AI Conversations
- AI Prompts
- AI Responses
- AI Contexts

---

## Knowledge Base

- Lessons Learned
- Best Practices
- Templates
- Prompt Library
- Engineering Rules

---

## Automation

- Tasks
- Activities
- Notifications
- Workflow Jobs
- Scheduled Jobs

---

## Audit

- Logs
- Audit Trail
- User Activity

---

# Database Principles

- PostgreSQL is the Single Source of Truth.
- Alembic is the exclusive authority for schema creation and evolution.
- Application and test imports must not create or alter schema objects.
- Database migrations run explicitly before the matching application version starts.
- Soft Delete whenever possible.
- UUID for public identifiers.
- Timestamps on every table.
- Relationships must use Foreign Keys.
- No duplicated business data.
- Every AI result must be traceable.

---

# Schema Management

## PATCH-019 Production Infrastructure Hardening

Status:

Completed

The complete PostgreSQL schema must be reproducible through:

```text
alembic upgrade head
```

Rules:

- `Base.metadata.create_all()` is not an application or test schema-management mechanism.
- SQLAlchemy metadata defines ORM mappings and supplies Alembic comparison metadata.
- Fresh PostgreSQL databases upgrade from the first committed revision to head.
- Existing databases retain their revision identity and use validated compatibility paths.
- Deployments apply migrations before starting the corresponding backend version.
- Normal backend startup never runs Alembic automatically.
- Migration and regression mutation tests require explicitly named dedicated PostgreSQL databases.
- Tests must never silently fall back to the development database.

Historical revision repair is governed by:

```text
ADR-012 — Alembic Schema Ownership and Historical Repair
```

---

# Naming Convention

Tables:
snake_case

Columns:
snake_case

Primary Key:
id

Foreign Keys:
xxx_id

Created:
created_at

Updated:
updated_at

Deleted:
deleted_at

---

END OF DATABASE BLUEPRINT
