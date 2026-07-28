# SATCO Platform Architecture

Version: 1.0
Status: Active
Last Updated: 2026-07-25

---

# High Level Architecture

```
                    +----------------------+
                    |      Customer        |
                    +----------+-----------+
                               |
                               v
                    +----------------------+
                    |      WordPress       |
                    | Website & Forms      |
                    +----------+-----------+
                               |
                               v
                    +----------------------+
                    |      FastAPI API     |
                    |   SATCO Backend      |
                    +----------+-----------+
                               |
          +--------------------+--------------------+
          |                    |                    |
          v                    v                    v
+----------------+   +------------------+   +------------------+
| PostgreSQL DB  |   |   File Storage   |   |       n8n        |
+----------------+   +------------------+   +------------------+
          |
          |
          v
+--------------------------------------------------------------+
|                    SATCO AI Brain                            |
+--------------------------------------------------------------+
|                                                              |
|  Context Builder                                             |
|  Prompt Builder                                              |
|  AI Router                                                   |
|  Knowledge Manager                                           |
|  Engineering Analyzer                                        |
|  Engineering Planner                                         |
|  Document Reviewer                                           |
|  PLC Assistant                                               |
|  Commissioning Assistant                                     |
|                                                              |
+-----------------------------+--------------------------------+
                              |
                              v
                      +---------------+
                      |  OpenAI API   |
                      +---------------+

```

---

# Main Modules

## CRM

Responsible for:

- Customers
- Companies
- Contacts
- Projects
- Tasks
- Activities

---

## AI Brain

Responsible for:

- Engineering Analysis
- Prompt Generation
- Context Building
- Technical Review
- AI Communication

---

## Knowledge Base

Stores:

- Lessons Learned
- Company Standards
- Engineering Knowledge
- Project Experience

---

## Prompt Library

Stores all engineering prompts.

Examples:

- Compressor Analysis
- PLC Review
- Instrument Review
- FAT
- SAT
- Commissioning

---

## Project Workflow Engine

Responsible for:

- Project States
- Engineering Workflow
- Task Generation
- Notifications

---

## AI Independence

The platform must never depend on a single AI provider.

Current Provider:

- OpenAI

Future Providers:

- Azure OpenAI
- Anthropic
- Google Gemini
- Local LLM

---

## Dual-Use Platform Operating Model

SATCO Platform supports both SATCO Engineering as an internal service-delivery
operator and external engineering organizations as independent platform
operators. The platform shall remain operator-neutral and shall not require
separate internal and commercial codebases.

The governing decision is defined in
`docs/adr/ADR-016-Dual-Use-Platform-Operating-Model.md`.

---

---

## Product Governance and Modular Capability Strategy

SATCO Platform is developed first for the real operational needs of SATCO
Engineering.

Version 1 remains focused on:

- Electrical Engineering;
- Instrumentation Engineering;
- Industrial Automation;
- Technical Procurement;
- Vendor Technical Proposal Review;
- Engineering Context;
- approved Engineering Intelligence capabilities.

SATCO is an Engineering Intelligence Platform that works beside engineers.

SATCO does not replace accountable engineering judgment, and it is not
intended to replace existing ERP, CMMS, Primavera, SAP, EDMS, or enterprise
project-management systems.

The engineer remains responsible for final engineering decisions.

The platform shall preserve architectural readiness for future optional
modules without implementing those modules before Product Owner approval.

Future commercial customers may activate only the modules they purchase or
are authorized to evaluate.

Commercial modularity shall use Organization-scoped Module Entitlements
rather than:

- customer-specific source-code forks;
- separate product architectures;
- duplicated domain models;
- manually altered customer builds;
- deployment-specific business rules.

SATCO Engineering may use the complete capability set required for its own
operations.

Every future capability requires explicit Product Owner approval before it
enters the Roadmap or implementation lifecycle.

Related governing decisions:

- ADR-016 Dual-Use Platform Operating Model;
- ADR-017 Modular Product Licensing Architecture;
- ADR-018 Engineering Intelligence Product Vision;
- ADR-019 Version-1 Product Scope Policy.

---

END OF ARCHITECTURE
