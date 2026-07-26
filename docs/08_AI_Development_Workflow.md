# SATCO AI Development Workflow

Version: 1.0

---

# 1. Purpose

This document defines the official AI-assisted software development workflow for SATCO Platform.

The purpose is to create a controlled, repeatable and production-ready development process using AI assistance.

Every SATCO development patch must follow this workflow.

---

# 2. Core Principle: Docs First Architecture

The /docs directory is the official Source of Truth.

No implementation should start before reviewing the related documentation.

The development order is:

Documentation
        |
        ↓
Architecture Validation
        |
        ↓
Implementation
        |
        ↓
Testing
        |
        ↓
Documentation Update
        |
        ↓
Git Commit

If an implementation decision changes architecture, the documentation must be updated before finalizing the patch.

---

# 3. SATCO Platform Development Philosophy

SATCO Platform follows:

- Modular Architecture
- Production Ready Development
- Clean Code Principles
- Security First Approach
- Documentation Driven Development
- Patch Based Development

Every patch must be:

- Planned
- Implemented
- Tested
- Documented
- Committed

---

# 4. AI Responsibilities

## ChatGPT Responsibilities

ChatGPT is responsible for:

- System architecture decisions
- Feature planning
- Patch definition
- Technical strategy
- Code review
- Development guidance
- Final approval process


## Codex Responsibilities

Codex acts as:

- Senior Software Engineer
- Backend Developer
- Code Reviewer
- Testing Assistant
- Documentation Assistant

Codex must understand the project before making changes.

Codex must not introduce undocumented architecture.

---

# 5. Standard Patch Workflow

Every patch follows this lifecycle:


PATCH Definition

↓

Documentation Review

↓

Repository Analysis

↓

Implementation Planning

↓

Approval

↓

Automatic Code Implementation

↓

Testing

↓

Documentation Update

↓

Git Commit

↓

Final Report


---

# 6. Patch Analysis Phase

Before writing code Codex must:

1. Inspect the repository structure.

2. Read relevant files inside /docs.

3. Understand existing architecture.

4. Identify affected modules.

5. Identify database changes.

6. Identify API changes.

7. Identify security implications.

8. Identify required tests.


The output of this phase must include:

- Implementation plan
- Files to create
- Files to modify
- Database impact
- API impact
- Testing strategy

---

# 7. Patch Implementation Phase

After approval Codex must:

- Create required files automatically.
- Modify existing files automatically.
- Follow existing architecture.
- Reuse existing components.
- Avoid duplicate logic.
- Maintain backward compatibility.
- Follow coding standards.
- Keep the project modular.


The developer should not manually create files unless specifically required.

---

# 8. Database Rules

For database changes:

Codex must:

- Update models.
- Create migrations when required.
- Validate relationships.
- Preserve existing data.
- Test database compatibility.


---

# 9. API Rules

For API changes:

Codex must:

- Update schemas.
- Update services.
- Update repositories.
- Update routers.
- Maintain authentication.
- Maintain authorization.
- Test endpoints.


---

# 10. Testing Requirements

Every patch must be tested.

Required validation:

- Docker environment validation
- Backend startup
- Database connection
- API endpoint tests
- Authentication tests
- Authorization tests
- Regression tests


A patch is NOT complete until tests pass.

---

# 11. Git Rules

Before committing:


Run:

git status


Requirements:

- No unrelated changes.
- No unfinished files.
- Clean working tree.


Commit format:


PATCH-XXX: Description


Example:


PATCH-018: Project Management Enhancement


---

# 12. Final Patch Report Format

After completion Codex must provide:


PATCH STATUS:

COMPLETED / FAILED


Implemented Changes:

-


Files Created:

-


Files Modified:

-


Database Changes:

-


API Changes:

-


Tests Executed:

-


Test Results:

-


Git Commit:

-


Production Readiness:

READY / NOT READY


---

# 13. Master Codex Execution Prompt


You are the Lead Software Engineer for SATCO Platform.


Project:

SATCO Platform


Main Rule:

The /docs directory is the official Source of Truth.


Before any implementation:

1. Read related documentation.
2. Understand current architecture.
3. Follow existing design decisions.
4. Do not introduce undocumented architecture.


Development Rules:

- Create files automatically when required.
- Modify files automatically when required.
- Do not ask the developer to manually copy code into files.
- Keep architecture clean.
- Reuse existing modules.
- Avoid duplicate functionality.
- Maintain production quality.
- Do not modify unrelated files.


Task:


PATCH-XXX:

<TITLE>


Objective:


<DESCRIPTION>


Execution:


Phase 1:

Analyze the repository and documentation.


Phase 2:

Prepare implementation plan.


Phase 3:

Implement the complete patch.


Phase 4:

Run all required tests.


Phase 5:

Fix all discovered issues.


Phase 6:

Prepare final delivery report.


The final result must be:

- Fully implemented
- Tested
- Documented
- Integrated
- Production ready


Do not stop at code generation.

The goal is a completed SATCO patch ready for the next development phase.

