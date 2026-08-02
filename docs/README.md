# SATCO Foundation v1.1 Documentation Guide

**Version:** 1.1

**Foundation Status:** Certified and Stable

## Purpose

This guide explains the authority, hierarchy, and recommended reading paths for
SATCO documentation. It connects constitutional, product, architecture,
experience, governance, PATCH, and implementation records.

## Scope

This hierarchy governs documents under `docs/`. It does not replace any
governing document or authorize implementation.

## Foundation v1.1

SATCO Foundation v1.1 is the certified documentation foundation that governs
future development.

It consists of:

- **Constitution:** `00_Constitution.md`
- **Product Bible:** `10_Engineering_Philosophy.md` through
  `17_SATCO_Product_Blueprint.md`
- **Architecture:** `01_Architecture.md` and accepted records under `adr/`
- **Experience:** `18_Experience_Bible.md` and accepted records under `xdr/`
- **Governance:** `19_Governance_Model.md`, this guide, and
  `09_Codex_Guidelines.md`
- **Implementation Framework:** `framework/00_Framework_Constitution.md`
  through `framework/09_Framework_Roadmap.md`
- **Delivery context:** roadmap, PATCH definitions, implementation plans, and
  review records

Foundation completion means the governing structure is ready. It does not mean
that future product capabilities have been implemented.

Certified and Stable means:

- Foundation v1.1 is the governing baseline for feature development.
- Routine PATCH work must not directly rewrite foundational documents.
- A foundational change must first be justified by an approved ADR or XDR
  appropriate to the decision.
- Approved foundational changes are released through a new Foundation version.
- Stable does not prohibit governed evolution; it prohibits uncontrolled
  modification.

## Documentation Hierarchy

The mandatory authority hierarchy is:

```text
Constitution

↓

Product Bible

↓

ADR

↓

Experience Bible

↓

XDR

↓

PATCH

↓

Implementation
```

### Constitution

`00_Constitution.md` defines the highest mission and responsibility boundaries.

### Product Bible

`10_Engineering_Philosophy.md` through `17_SATCO_Product_Blueprint.md`
define permanent product identity, philosophy, AI behavior, knowledge, and
product rules.

### ADR

Accepted records under `adr/` define binding architecture within their scope.
`01_Architecture.md` is the platform architecture baseline interpreted through
the Constitution, Product Bible, and accepted ADRs.

### Experience Bible

`18_Experience_Bible.md` defines permanent experience philosophy subordinate to
the Constitution, Product Bible, and accepted ADRs.

### XDR

Accepted records under `xdr/` define durable experience decisions subordinate
to all higher governance.

### PATCH

Records under `patches/` authorize bounded changes. A PATCH cannot create
permanent architecture or experience governance by implication.

### Implementation

Implementation realizes an approved PATCH and every applicable higher-level
decision. It has no authority to reinterpret missing or conflicting governance.

### Supporting Documents

The roadmap, technical blueprints, coding standards, workflow guidance,
implementation plans, and review reports provide planning, constraints, and
evidence. They do not override the mandatory authority hierarchy.

The SATCO Implementation Framework v1.1 is the mandatory execution standard
used after an IRR grants `READY FOR IMPLEMENTATION`. It consolidates procedure
without changing the authority hierarchy.

## Relationships Among Foundation Layers

- **Constitution** establishes why SATCO exists and preserves human engineering
  responsibility.
- **Product Bible** defines what SATCO is and how it creates engineering value.
- **Architecture** defines durable domain and technical structure through the
  baseline architecture and accepted ADRs.
- **Experience** defines how that governed product and architecture should be
  understood and used through the Experience Bible and accepted XDRs.
- **Governance** defines how decisions move through authority, approval,
  conflict resolution, change, and versioning.
- **Implementation** realizes an approved PATCH without changing higher-level
  meaning.

Governance administers the hierarchy. It is not an authority above the
Constitution.

## Conflict Resolution

When two documents appear to conflict:

1. confirm that both statements apply to the same scope;
2. identify hierarchy level and record status;
3. apply the higher-authority document;
4. check for explicit supersession within the same record type;
5. distinguish permanent governance from PATCH-specific evidence;
6. stop implementation and request resolution if the conflict remains.

No contributor or AI agent may silently reconcile contradictory guidance.

## Mandatory Governance Reading Order

Every future PATCH begins with:

```text
Product Bible v1.0
(begin with docs/README.md and
docs/17_SATCO_Product_Blueprint.md)

↓

docs/00_Constitution.md

↓

docs/10_Engineering_Philosophy.md

↓

Relevant accepted ADRs

↓

docs/01_Architecture.md

↓

docs/18_Experience_Bible.md

↓

Relevant accepted XDRs

↓

docs/19_Governance_Model.md

↓

docs/09_Codex_Guidelines.md

↓

docs/02_Roadmap.md

↓

Requested PATCH
```

This operational reading sequence is compatible with
`09_Codex_Guidelines.md`. Reading order does not alter authority: the
Constitution remains the highest governing document and the mandatory hierarchy
defined above controls conflict resolution.

Workflow, coding, database, backend, AI, review, and implementation documents
must also be read whenever their scope is affected.

## Canonical Product Terminology

The following terms are permanent and should retain this capitalization when
they name SATCO product concepts:

- Engineering Workspace
- Engineering Execution Plan
- Engineering Knowledge Graph
- Engineering Memory
- Engineering Health
- Engineering Copilot
- Engineering Reasoning
- Engineering Impact Analysis
- AI Confidence
- Human Review
- Engineering Context

Generic language may remain lowercase when it does not name the governed
concept. New synonyms must not be introduced when a canonical term applies.

## Reading Paths by Role

### New Developers

1. Mandatory governance reading order.
2. `05_Coding_Standards.md`.
3. `06_Database_Blueprint.md` and `07_Backend_Blueprint.md`.
4. `08_AI_Development_Workflow.md`.
5. Relevant ADRs, XDRs, and review history.

New developers should understand the product responsibility boundary before
learning implementation conventions.

### Architects

1. `00_Constitution.md`.
2. Full Product Bible: `10_Engineering_Philosophy.md` through
   `17_SATCO_Product_Blueprint.md`.
3. All accepted ADRs.
4. `18_Experience_Bible.md` and relevant accepted XDRs.
5. `01_Architecture.md`, `03_AI_Brain.md`, and domain blueprints.
6. `19_Governance_Model.md`, `02_Roadmap.md`, and relevant PATCH reviews.

Architects are responsible for resolving cross-document implications and
recording new architectural decisions explicitly.

### AI Agents

1. Mandatory governance reading order.
2. `13_AI_Behavior_Guide.md`.
3. `16_AI_Feature_Framework.md`.
4. `14_Engineering_Knowledge_Model.md`.
5. `15_User_Experience_Philosophy.md` and `18_Experience_Bible.md`.
6. Every scope-relevant technical blueprint, ADR, and XDR.

AI agents must preserve Human Review, show uncertainty, and never interpret
their own output as engineering approval.

### Product Owners

1. `00_Constitution.md`.
2. `17_SATCO_Product_Blueprint.md`.
3. `11_Product_Vision.md` and `12_Product_Principles.md`.
4. `10_Engineering_Philosophy.md`.
5. `18_Experience_Bible.md` and `19_Governance_Model.md`.
6. `02_Roadmap.md`.
7. Relevant ADRs, XDRs, PATCH definitions, and final reports.

Product decisions should be evaluated by engineering value, risk reduction,
coherence, and long-term product identity.

### Engineering Managers

1. `00_Constitution.md`.
2. `17_SATCO_Product_Blueprint.md`.
3. `10_Engineering_Philosophy.md`.
4. `11_Product_Vision.md`.
5. `14_Engineering_Knowledge_Model.md`.
6. `15_User_Experience_Philosophy.md`.
7. `18_Experience_Bible.md`.
8. Relevant ADRs, XDRs, and workflow documents.

Engineering managers should focus on responsibility, Engineering Execution
Plan governance, Engineering Health, review, readiness, and organizational
learning.

### Codex

1. Follow the mandatory governance reading order exactly.
2. Read all documents named by the user.
3. Read every additional document whose scope may be changed.
4. Verify whether an ADR and/or XDR is required before implementation.
5. Apply `19_Governance_Model.md`.
6. Follow `09_Codex_Guidelines.md` for approvals, validation, documentation,
   and Git operations.

Codex must not treat a PATCH as permission to exceed its declared scope.

### Future Contributors

1. Begin with this guide and the mandatory governance reading order.
2. Select the role path closest to the intended contribution.
3. Review the latest relevant ADRs, XDRs, and PATCH reports.
4. Preserve canonical terminology and documentation hierarchy.
5. Request clarification before introducing a conflicting interpretation.

## Design Rules for Documentation

- State a document’s purpose, scope, authority, and relationship to existing
  governance.
- Use canonical product terminology.
- Record architectural decisions in ADRs, not only in PATCH reports.
- Record durable experience decisions in XDRs, not only in PATCH reports.
- Keep XDRs subordinate to accepted ADRs and the Experience Bible.
- Keep implementation details out of permanent product-governance documents.
- Keep PATCH scope bounded and verifiable.
- Distinguish proposed, accepted, implemented, validated, and superseded states.
- Preserve decision history rather than rewriting it without explanation.
- Link recommendations to governing principles and evidence.

## Future Implications

Every future PATCH must use this hierarchy and reading order. Documentation
growth should strengthen a coherent body of governance rather than create
parallel definitions. If a new permanent concept is required, it must be
aligned with the Product Bible and introduced through the appropriate
ADR, Experience Bible, XDR, and PATCH process.
