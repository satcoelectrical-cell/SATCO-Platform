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
- Soft Delete whenever possible.
- UUID for public identifiers.
- Timestamps on every table.
- Relationships must use Foreign Keys.
- No duplicated business data.
- Every AI result must be traceable.

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
