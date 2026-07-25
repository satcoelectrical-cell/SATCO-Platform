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

END OF ARCHITECTURE
