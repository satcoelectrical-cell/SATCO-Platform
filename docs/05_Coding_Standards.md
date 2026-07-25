# SATCO Platform Coding Standards

Version: 1.0
Status: Active
Last Updated: 2026-07-25

---

# Goal

Maintain a clean, scalable and enterprise-grade codebase.

---

# General Principles

- Readability over cleverness.
- Simplicity over complexity.
- Explicit is better than implicit.
- Small reusable modules.
- Single Responsibility Principle.
- SOLID principles.
- Clean Architecture.

---

# Backend

Language:

Python 3.13+

Framework:

FastAPI

ORM:

SQLAlchemy

Validation:

Pydantic

Database:

PostgreSQL

---

# Folder Structure

app/

api/

core/

db/

models/

schemas/

services/

repositories/

ai/

workflows/

utils/

tests/

---

# API Rules

- RESTful APIs
- Versioned endpoints
- JSON only
- Consistent response format

Example:

{
    "success": true,
    "data": {},
    "message": ""
}

---

# Service Layer

Business logic MUST NOT exist inside API routes.

Routes only:

- Validate Request
- Call Service
- Return Response

---

# Repository Layer

Database access belongs ONLY to repositories.

No SQL inside Services.

---

# AI Layer

All AI functionality must exist inside:

app/ai/

Modules include:

context/

prompts/

router/

planner/

reviewer/

knowledge/

analyzer/

---

# Logging

Every important action must be logged.

Examples:

Project Created

AI Started

AI Finished

File Uploaded

Document Reviewed

---

# Error Handling

Never expose internal errors.

Return meaningful API messages.

Log complete stack traces internally.

---

# Testing

Every new module should include tests.

Prefer automated testing.

---

# Documentation

Every architectural decision must be documented before implementation.

---

# Git

Small commits.

Meaningful commit messages.

Feature branches.

Pull Requests before merge.

---

# Rule

No code may violate this document.

