# ADR-021 — Engineering Intelligence Core Business Capability

## Status

Accepted

## Date

2026-08-02

## Decision Owners

- Product Owner
- Architecture Guardian

## Approval Record

| Authority | Decision | Date |
|---|---|---|
| Product Owner | Approved proposed direction and continuation | 2026-08-02 |
| Architecture Guardian | Accepted | 2026-08-02 |

The accepted decision establishes architectural authority. It does not by
itself authorize any implementation PATCH.

## Context

SATCO Foundation v1.2 defines Engineering Intelligence as a permanent
organizational capability. The repository already contains governed
Engineering Object, Engineering Relationship, Evidence, Engineering Context,
Workspace, Project, and authenticated Organization foundations.

The platform architecture does not yet assign one durable business-capability
owner to the transformation of Engineering Experience into reviewed,
traceable, reusable Engineering Knowledge. Without that ownership boundary,
Engineering, Technical Procurement, Maintenance, Methods & Systems, or future
modules could create parallel capture systems, knowledge stores, evidence
semantics, or organizational memories. That would duplicate canonical records,
fragment context, and violate Capture Once and the EKG Open Extension Principle.

The detailed proposal and independent technical review are recorded in:

- `docs/design/Engineering-Intelligence-Architecture-v1.0.md`;
- `docs/reviews/Engineering-Intelligence-Architecture-Review.md`.

## Proposed Decision

Engineering Intelligence shall be a Core Business Capability of SATCO
Platform. It shall not be owned by an individual engineering application,
domain module, AI provider, or user interface.

Engineering Intelligence owns the canonical capability contracts and lifecycle
semantics for:

- captured Engineering Experience;
- Engineering Knowledge and its authority state;
- Engineering Context used to interpret knowledge;
- the meaning and use of Engineering Evidence;
- governed Engineering Relationships;
- review, approval, rejection, qualification, and supersession history;
- Engineering Organizational Memory;
- provenance, rationale, uncertainty, and explanation.

This ownership is semantic and architectural. It does not place all concepts in
one aggregate, schema, service, database, or deployable component. Existing
aggregate and consistency boundaries remain unchanged unless a future Accepted
ADR and approved PATCH explicitly change them.

## Module Dependency Rule

Engineering applications and Product-Owner-approved future modules are
contributors and consumers of Engineering Intelligence.

They may contribute experience, objects, relationships, evidence references,
and domain context through governed ports. They may consume authorized context,
review state, approved knowledge, and Organizational Memory through stable
contracts.

They shall not:

- own a parallel authoritative Engineering Knowledge system;
- duplicate canonical identity or approved knowledge into a module source of
  truth;
- redefine evidence, provenance, review, approval, or supersession semantics;
- bypass Human Review or lower confidentiality;
- fork Engineering Intelligence Core or EKG Core;
- make AI/provider state authoritative.

## Relationship to Platform Core

Engineering Intelligence uses, but does not duplicate, shared Platform Core
capabilities including identity, authentication, active Organization context,
authorization, PostgreSQL persistence, Audit, Domain Events, idempotency,
transactions, configuration, and provider integration.

Source dependencies shall continue to point inward. Domain and application
contracts must not depend on transport frameworks, concrete persistence, or a
specific AI provider.

## Human Authority and Trust Boundary

Original capture is not approved knowledge. Evidence is not approval. AI
interpretation is not a decision. Repetition, elapsed time, or system
processing is not approval.

Explicit, accountable, context-bounded Human Review is the permanent boundary
through which proposed understanding may become trusted Organizational Memory.
AI and automation cannot occupy an accountable engineering role.

## Data and Provider Authority

PostgreSQL remains the Version-1 structured System of Record. Search indexes,
embeddings, graph stores, vector stores, model caches, and provider conversation
state may be introduced only through separately accepted architecture and
shall remain derived or complementary. They cannot become the sole holder of
canonical identity, context, approval, or engineering authority.

AI providers are replaceable outward dependencies. Engineering Knowledge,
context, history, and authority remain governed and owned by the Organization.

## Compatibility

This decision is additive and compatible with:

- the Constitution and Engineering Intelligence Manifesto v1.0;
- ADR-013 AI Engineering Copilot Architecture;
- ADR-014 and ADR-015 Workspace and Context boundaries;
- ADR-016 Dual-Use Platform Operating Model;
- both ADR-017 records concerning modularity and EKG evolution;
- ADR-018 Engineering Intelligence Product Vision;
- ADR-019 Version-1 Product Scope Policy;
- ADR-020 EKG Open Extension Principle;
- completed PATCH-023 through PATCH-027.

It does not modify any completed aggregate, schema, API, migration, test, or
PATCH acceptance record.

## Consequences

### Positive

- one canonical Engineering Intelligence architecture serves every module;
- Capture Once can be enforced across application boundaries;
- knowledge, evidence, context, and memory retain shared meaning;
- AI providers and domain modules remain replaceable and bounded;
- future domains extend Core without forking it;
- Human authority remains explicit and reviewable.

### Constraints

- domain modules must integrate through governed ports;
- new knowledge capabilities require explicit lifecycle and authority design;
- module-local convenience stores cannot become authoritative;
- cross-scope reuse requires reviewed authorization and confidentiality policy;
- implementation must proceed through bounded PATCH/EDS/IDS/IRR chains.

## Alternatives Considered

### Knowledge ownership per module

Rejected because it duplicates canonical knowledge, fragments provenance, and
violates Capture Once and open extension.

### AI Brain owns Engineering Knowledge

Rejected because AI is an implementation capability and replaceable adapter,
not an engineering authority or System of Record.

### One monolithic Engineering Intelligence aggregate

Rejected because semantic ownership does not justify combining independent
consistency boundaries.

### Continue without an explicit owner

Rejected because implementation PATCHes would be forced to invent durable
cross-module ownership decisions.

## Explicit Non-Authorization

This Proposed ADR does not authorize PATCH-028, backend or frontend changes,
schema or migration work, AI integration, a graph/vector database, document
content management, or activation of deferred modules.

## Acceptance Gate

This ADR becomes `Accepted` only after:

1. Product Owner approval;
2. Architecture Guardian approval;
3. confirmation that its architecture review remains PASS;
4. registration of the accepted decision in required architecture guidance;
5. no unresolved conflict with the certified Foundation.

The acceptance gate is satisfied. Implementation still requires its own
approved PATCH/EDS/IDS/plan/IRR chain.

## Revision History

| Version | Date | Description |
|---|---|---|
| 0.1 | 2026-08-02 | Initial proposed Core Business Capability ownership decision. |
| 1.0 | 2026-08-02 | Accepted by Product Owner and Architecture Guardian. |
