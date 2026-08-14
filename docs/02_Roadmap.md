# SATCO Platform Development Roadmap

Version: 1.0
Status: Active
Last Updated: 2026-07-25

---

# Project Vision

Build an AI-assisted Engineering Platform for Industrial Automation, Electrical, Instrumentation and Control Engineering.

The goal is NOT automatic engineering.

The goal is Engineering Assistance.

---

# Current Project Status

Current Roadmap Position:

PATCH-036 SATCO Web Application & Engineering Dashboard is DONE / CLOSED after
QG-M1, Human QG-11, bounded QG-12 delivery, push, and remote verification PASS.

Latest Completed Capability:

PATCH-036 — SATCO Web Application & Engineering Dashboard — DONE / CLOSED.

Next Conceptual Capability:

PATCH-037 remains unregistered and has not begun. No later capability receives
authority from PATCH-036 closure.
PATCH-030 and PATCH-031 remain
intentionally unregistered PATCH identifiers; their existing EDS identifiers
retain their separate historical meanings.

Executable PATCH:

No later PATCH is executable under PATCH-036 authority.

---

# Development Phases

| Phase | Name | Status |
|--------|------|--------|
| 1 | Foundation | 🟢 In Progress |
| 2 | Core Backend | ⬜ Planned |
| 3 | CRM | ⬜ Planned |
| 4 | Project Management | ⬜ Planned |
| 5 | AI Brain (Core) | ⬜ Planned |
| 6 | Document Analysis | ⬜ Planned |
| 7 | Engineering Copilot | ⬜ Planned |
| 8 | Knowledge Base | ⬜ Planned |
| 9 | Automation & Workflow | ⬜ Planned |
| 10 | Commercial Release | ⬜ Planned |

---

# Phase 1 — Foundation

Status:

In Progress

Tasks

[x] Docker

[x] PostgreSQL

[x] FastAPI

[x] Basic Project Structure

[x] Documentation Structure

[x] Alembic schema ownership and reproducible migrations (PATCH-019)

[ ] Git Standards

[ ] CI/CD

[ ] Logging

[ ] Configuration Management

---

# Phase 2 — Core Backend

- [x] Authentication foundation
- [x] Users foundation
- [x] Basic roles and permissions
- [x] Protected CRM endpoints
- [x] Audit logging foundation
- [x] PATCH-017.3 final recovery and stabilization
- [ ] API Structure completion
- [ ] Error Handling completion

---

# Phase 3 — CRM

- [x] Customers CRUD foundation

- Companies

- [x] Contacts CRUD foundation

- Activities

- Tasks

---

# Phase 4 — Project Management

- [x] Projects CRUD foundation
- [x] PATCH-018.1 Project Core Enhancement

- Files

- Milestones

- Project Dashboard

---

# Phase 5 — AI Brain

- Context Builder

- Prompt Builder

- AI Router

- Knowledge Manager

- Engineering Analyzer

- Planner

- Reviewer

---

# Phase 6 — Document Analysis

- PDF Analysis

- Datasheet Extraction

- Drawing Review

- Instrument Review

- Electrical Review

---

# Phase 7 — Engineering Copilot

- [x] Engineering Workspace Core implementation and isolated validation

- PLC Assistant

- Instrument Assistant

- Electrical Assistant

- Commissioning Assistant

- Troubleshooting Assistant

---

# Phase 8 — Knowledge Base

- Lessons Learned

- Company Standards

- Engineering Templates

- Prompt Library

---

# Phase 9 — Automation

- n8n

- Notifications

- Email

- Task Automation

- Workflow Engine

---

# Phase 10 — Commercial Release

- UI Polish

- Performance

- Security

- Deployment

- Customer Documentation

---

# Rule

Every completed task must update this roadmap.

No feature may be implemented without appearing in this roadmap.

---

## PATCH-020.3 Product Governance Update

### Status

Accepted

### Purpose

Establish the product-governance rules that control all future Engineering
Intelligence and module development.

### Approved Version-1 Direction

Version 1 is built first for SATCO Engineering and remains focused on:

- Electrical Engineering;
- Instrumentation Engineering;
- Industrial Automation;
- Technical Procurement;
- Vendor Technical Proposal Review;
- Engineering Context;
- approved Engineering Intelligence capabilities.

### Governance Deliverables

- ADR-017 Modular Product Licensing Architecture;
- ADR-018 Engineering Intelligence Product Vision;
- ADR-019 Version-1 Product Scope Policy;
- Constitution product-governance principles;
- Architecture product-governance section;
- Roadmap scope and approval gates.

### Product Rules

- Engineering judgment remains with the engineer.
- AI assists and does not replace accountable engineers.
- SATCO complements existing enterprise systems.
- Version 1 is completed before broader organizational expansion.
- Architectural readiness does not authorize implementation.
- Every new capability requires explicit Product Owner approval.
- Every capability must solve a real daily engineering problem.
- Build depth before breadth.

### Deferred Areas

The following areas remain deferred unless separately approved:

- Maintenance;
- Methods and Systems;
- HSE;
- Operations;
- Reliability;
- Asset Integrity;
- Human Resources;
- Finance;
- generic enterprise workflow;
- enterprise project-management replacement;
- engineering disciplines outside Version 1.

### Completion Gate

PATCH-020.3 is complete only after:

- all three ADRs are validated;
- Constitution changes are validated;
- Architecture changes are validated;
- Roadmap changes are validated;
- `git diff --check` passes;
- the Product Owner approves the final document set;
- a documentation-only commit is created and pushed.

---

---

## PATCH-021 Engineering Knowledge Graph Foundation

### Status

Architecture Accepted

### Completed Design Stages

- PATCH-021.1 Engineering Object Model;
- PATCH-021.2 Engineering Relationship Vocabulary;
- PATCH-021.3 Engineering Context Model;
- PATCH-021.4 Engineering Knowledge Graph Rules;
- PATCH-021.5 Physical Data Model.

### Approved Implementation Direction

- PostgreSQL remains the Version-1 System of Record.
- Engineering Objects, Relationships, and Contexts are separate aggregates.
- Primary identities use immutable UUID values.
- Engineering identifiers remain governed external identifiers.
- Relationships remain directional.
- Context membership remains explicit.
- Optimistic concurrency is mandatory.
- Mutation and Audit remain atomic.
- Ordinary deletion of authoritative engineering history is prohibited.
- Repository boundaries remain persistence-only.
- Application services enforce engineering rules.
- Database changes require Alembic migrations.
- Graph traversal remains bounded, scoped, and authorization-aware.

### Next Stage

Proceed to the bounded backend implementation lifecycle for the Engineering
Knowledge Graph foundation.

Graph databases, vector databases, Engineering Digital Twin behavior, and
autonomous AI reasoning remain deferred.

---

## PATCH-028 Universal Engineering Capture Foundation

### Status

DELIVERY AUTHORIZED — COMMIT AND PUSH EXECUTION PENDING

### Version-1 Objective

Establish one governed point of origin for bounded textual Engineering
Experience with immutable original content, trusted Human/Organization
provenance, optional governed Project/Workspace/discipline/object context, and
history-preserving correction or supersession.

### Scope Boundary

- Capture is not fact, Evidence, approval, knowledge, or Organizational Memory.
- PostgreSQL remains the structured System of Record.
- Binary files, uploads, OCR, document management, Inbox UI, AI Author, Human
  Review workflow, publishing, semantic/vector search, and graph databases are
  deferred.
- No implementation begins before accepted EDS/IDS and IRR READY.

### Next Stage

Create and push the bounded authorized PATCH-028 delivery commit, verify local
and remote equality, then record QG-12 PASS and DONE/CLOSED. Development and
deployment migration remain separately unauthorized.

### Registered Prerequisite — PATCH-028.1

`PATCH-028.1 — Project Organization Ownership` is registered as the bounded
prerequisite. ADR-022 and the architecture are accepted. Read-only discovery
found seven legacy Projects in a database at revision `d8271b8f1a29` with no
Organization baseline. The Repository/Data Owner approved preserving all seven
Projects and mapping them non-destructively to a migration-owned default
Organization. EDS-028.1 is accepted and independently reviewed PASS. The
existing `admin@satco.com` User is explicitly approved as the sole bootstrap
member; the engineer User must remain unchanged. IDS-028.1 is accepted after
independent review PASS. Implementation Plan-028.1 is now proposed with
technical PASS and is Human-accepted. Focused IRR-028.1 authorized scoped
implementation and isolated validation. Its three implementation Sprints now
pass, including protected Organization-scoped dependent loaders and a complete
backend regression of 381 passed and 0 failed. Focused IDS Amendment 2 added
exactly five related runtime/test files, its independent review passed, and the
repeated Human QG-11 passed without semantic scope expansion. Commit
`f58b2ebcf0df4f143729c76e6d43349dc298b6c4`, push, remote verification, and
QG-12 all pass; PATCH-028.1 is DONE/CLOSED. Development and deployment
migration remain unauthorized and unexecuted. These changes satisfy PATCH-028.1 only;
PATCH-028 Capture persistence, application, and transport are implementation
complete with 414 backend tests passing and no remaining finding. Commit and
push are authorized but not executed.
