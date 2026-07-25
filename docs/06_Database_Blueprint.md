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
