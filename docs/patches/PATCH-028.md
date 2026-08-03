# PATCH-028 — Universal Engineering Capture Foundation

## 1. Document Control

| Field | Value |
|---|---|
| Document ID | PATCH-028 |
| Status | DELIVERY AUTHORIZED — COMMIT AND PUSH EXECUTION PENDING |
| Owner | SATCO Product Owner / Platform Architecture |
| Architecture style | Docs-First Architecture |
| Product scope | Version 1 Engineering Intelligence |
| Decision date | 2026-08-02 |

This PATCH authorizes architecture and design documentation only. Backend,
schema, migration, API, and runtime implementation remain unauthorized until
an accepted EDS, PASS EDS Review, approved IDS, executable Implementation Plan,
and IRR `READY FOR IMPLEMENTATION` exist.

## 2. Engineering Problem

Engineering Experience is created continuously in observations, questions,
assumptions, rationale, decisions, outcomes, and lessons. Today SATCO has
governed Engineering Objects, Relationships, Evidence references, Context,
Workspace, Project, and Organization foundations, but it has no canonical
capture boundary that preserves Engineering Experience at its source.

Without a Universal Capture foundation, future modules would have to store
experience in separate notes, conversations, evidence records, or domain-owned
knowledge stores. That would force later reconstruction, obscure provenance,
and violate Capture Once.

## 3. Objective

Introduce the smallest governed Version-1 foundation for capturing bounded
textual Engineering Experience in its original form, with trusted provenance
and engineering scope, without treating capture as fact, Evidence, approved
knowledge, decision, or Organizational Memory.

## 4. Governing Documents

- SATCO Platform Constitution;
- Engineering Intelligence Manifesto v1.0;
- SATCO Product Bible;
- `docs/adr/ADR-021-Engineering-Intelligence-Core-Business-Capability.md`;
- accepted ADR-013 through ADR-020 where relevant;
- `docs/design/Engineering-Intelligence-Architecture-v1.0.md`;
- SATCO Governance Model and Development Lifecycle;
- SATCO Implementation Framework v1.1 and QG-M1;
- completed PATCH-023 through PATCH-027.

## 5. Manifesto Alignment Record

### Manifesto Reference

`docs/Engineering_Intelligence_Manifesto.md` v1.0

### Supported Principles

- Engineering First;
- Capture Once;
- Engineering Context Is Sacred;
- Evidence Before Assumption;
- Organizational Ownership;
- Continuous Evolution.

### Affected Principles

- Capture Once;
- Human Authority;
- Engineering Context Is Sacred;
- Evidence Before Assumption;
- Context Before Recommendation;
- Organizational Ownership;
- Continuous Evolution.

### Preserved Principles

- Engineering First;
- Intelligence Before Automation;
- Explainability;
- Provider Independence.

### Engineering Intelligence Contribution

PATCH-028 gives Engineering Work one governed point of origin. It preserves
what was expressed, who captured it, when it was captured, where it applies,
and how it entered SATCO so later contextualization and review begin from the
original record rather than a reconstructed copy.

### Known Tensions and Risks

- storing text can be mistaken for declaring it true;
- editable notes could erase original meaning;
- broad capture could expose confidential engineering context;
- client-controlled identity or scope could corrupt provenance;
- duplicating PATCH-027 Evidence semantics could create conflicting authority;
- premature review, AI, publishing, or memory behavior could expand scope.

The design must make these distinctions explicit and enforce deny-by-default
scope before implementation readiness.

## 6. Approved Architecture Scope

PATCH-028 design shall define:

- an independently identified `EngineeringExperienceCapture` Aggregate Root;
- immutable UUID identity;
- bounded textual original content stored by SATCO;
- optional bounded `source_reference` metadata;
- trusted Organization and authenticated Human Creator provenance;
- optional Project, Workspace, Discipline, and Engineering Object context;
- capture origin/type vocabulary suitable for Version 1;
- explicit lifecycle and version semantics;
- correction or supersession without overwriting original content;
- confidentiality/visibility and authorization-before-disclosure;
- optimistic concurrency for post-creation commands;
- idempotency, Audit, Domain Events, and atomic persistence;
- explicit commands and bounded authorized queries;
- one additive Alembic migration;
- focused aggregate, schema, repository, service, API, security, transaction,
  migration, and regression tests.

EDS-028 must decide exact vocabularies, lifecycle matrices, limits, context
compatibility, responsibility, and operation boundaries. This PATCH does not
delegate those decisions to implementation.

## 7. Semantic Boundaries

An Engineering Experience Capture is:

- an authentic record of what an accountable Human submitted to SATCO;
- preserved with original content and provenance;
- contextual but not necessarily complete or correct;
- available only within authorized scope;
- eligible for later enrichment and review through separately governed
  capabilities.

It is not, merely by existing:

- an engineering fact;
- PATCH-027 Evidence or proof;
- an approved decision or recommendation;
- authoritative Engineering Knowledge;
- published Organizational Memory;
- an AI conclusion;
- approval of any engineering action.

No status name or API response may blur these distinctions.

## 8. Content and Source Decision

Version 1 stores bounded textual original content inside the Capture aggregate.
The content becomes immutable after creation. Correction creates an explicit
new or superseding governed record; it does not edit the original expression.

An optional bounded `source_reference` may identify the external or existing
source from which the experience arose. It is provenance metadata, not managed
content and not Evidence authority.

Binary content, file uploads, document bodies, attachments, OCR, parsing, and
document-management lifecycle are outside PATCH-028.

## 9. Scope and Context Rules

- Organization is mandatory and derived from authenticated active membership.
- Creator is the authenticated Human and immutable.
- Project is optional only if EDS proves an Organization-wide capture use case.
- Workspace requires Project and must belong to that Project.
- Discipline and Engineering Object references require compatible governed
  scope and authorization.
- clients cannot provide trusted Organization, Creator, approval, authority,
  lifecycle defaults, Audit metadata, or timestamps.
- cross-Organization capture or disclosure is prohibited.
- cross-Project or cross-Workspace reuse is prohibited unless a future
  accepted design explicitly authorizes it.

## 10. History and Mutation Rules

- original content and original provenance are immutable;
- physical deletion is prohibited;
- generic PUT/PATCH is prohibited;
- post-creation mutation uses explicit commands and expected version;
- every successful mutation increments version exactly once;
- corrections, withdrawal, rejection, or supersession preserve history;
- one Unit of Work and PostgreSQL transaction persist aggregate state, Audit,
  Domain Events, and idempotency outcome where governed;
- AI and automation cannot issue an authoritative Human command.

## 11. Dependencies

- PATCH-025 authenticated Organization context;
- PATCH-023 application/port/UoW conventions;
- PATCH-024 EngineeringObject persistence;
- PATCH-026 relationship and protected-disclosure conventions where referenced;
- PATCH-027 Evidence semantic separation;
- accepted ADR-021 ownership boundary;
- PATCH-028.0 QG-M1 governance integration.

## 12. Explicit Non-Scope

- Knowledge Inbox user interface;
- Engineering Intelligence Author or AI processing;
- Human Review workflow beyond preserving capture authority boundaries;
- approval, publishing, or Organizational Memory;
- conversion of Capture into Evidence, fact, decision, or approved knowledge;
- autonomous or background capture;
- email/chat/file ingestion connectors;
- document upload, binary storage, OCR, parsing, or attachment management;
- semantic search, embeddings, vector database, or graph database;
- new generic Knowledge Base;
- cross-Organization or unrestricted cross-Project sharing;
- frontend implementation;
- changes to completed PATCH-023 through PATCH-027 contracts;
- unrelated refactoring.

## 13. Required Deliverables

Before implementation:

- AR-028 Manifesto Compliance PASS;
- accepted EDS-028 and independent review PASS;
- approved IDS-028 with exact files, contracts, migration, tests, and errors;
- executable Implementation Plan-028;
- IRR-028 with `Manifesto Alignment Verified: YES`, QG-M1 Readiness PASS, and
  `READY FOR IMPLEMENTATION`.

Implementation deliverables remain provisional until IDS approval.

## 14. Architecture Acceptance Criteria

- Capture is an independent aggregate and does not expand EngineeringObject or
  Evidence consistency boundaries;
- original text and provenance cannot be overwritten;
- Capture is never represented as fact, Evidence, approval, or knowledge;
- scope, confidentiality, and authorization precede disclosure;
- Human Creator and trusted Organization are server-derived;
- correction and supersession preserve history;
- AI/provider behavior is absent and cannot become authority;
- content/file/document non-scope is unambiguous;
- every affected Manifesto principle has explicit design coverage;
- no backend implementation begins before READY IRR.

## 15. QG-M1 Readiness State

```text
Manifesto Compliance: PASS at AR-028
Manifesto Alignment Verified: YES — PATCH-028.1 prerequisite closed
QG-M1 Readiness Result: PASS
QG-M1 Final Result: PASS
```

## 16. Current Authorization

**Sprints 1, 2, and 3 PASS. Independent Final Review and Human QG-11 PASS.
QG-7 through QG-11 and QG-M1 Final PASS. Full regression: 414 passed, 0
failed.**

**Backend implementation: COMPLETE. Commit and push are authorized but not
executed. QG-12 evidence remains pending. Development/deployment migration is
not authorized and was not executed.**

## 17. Revision History

| Version | Date | Description |
|---|---|---|
| 0.1 | 2026-08-02 | Initial Universal Engineering Capture Foundation contract. |
| 1.0 | 2026-08-02 | Product Owner scope approval and AR-028 architecture PASS recorded. |
| 1.1 | 2026-08-03 | PATCH-028.1 closure removed the Organization ownership blocker; focused IRR found the IDS/Plan migration baseline stale, so readiness remains withheld pending a lineage-only amendment. |
| 2.0 | 2026-08-03 | Recorded completed Sprints, 414-test regression, Independent Final Review PASS, Human QG-11 PASS, QG-M1 Final PASS, and bounded commit/push authorization; delivery execution and QG-12 evidence pending. |
