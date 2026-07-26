# SATCO Product Bible v1.0 Documentation Guide

**Version:** 1.0

**Certification:** Certified

## Purpose

This guide explains the authority, hierarchy, and recommended reading paths for
SATCO documentation. It helps every contributor begin with the correct product
and architectural context before interpreting a PATCH or changing the platform.

## Scope

This hierarchy governs documents under `docs/`. It describes how governing
documents relate to architectural decisions, blueprints, roadmaps, PATCHes, and
review records. It does not replace the authority of the Constitution or an
accepted ADR.

## Documentation Hierarchy

SATCO documentation is interpreted in the following order of authority:

1. **Constitution**
   - `00_Constitution.md`
   - Permanent mission, responsibility boundaries, and highest product rules.
2. **Master Product Governance**
   - `17_SATCO_Product_Blueprint.md`
   - Unified product identity, philosophy, lifecycle, and design rules.
3. **Product Bible**
   - `10_Engineering_Philosophy.md`
   - `11_Product_Vision.md`
   - `12_Product_Principles.md`
   - `13_AI_Behavior_Guide.md`
   - `14_Engineering_Knowledge_Model.md`
   - `15_User_Experience_Philosophy.md`
   - `16_AI_Feature_Framework.md`
   - Permanent domain-specific governance subordinate to the Constitution and
     interpreted through the master blueprint.
4. **Accepted Architecture Decision Records**
   - `adr/`
   - Binding architectural decisions within their stated scope. A later
     accepted ADR may supersede an earlier ADR explicitly. Any decision that
     changes permanent Product Bible governance must update the affected
     governing documents through an approved architectural process and may
     never override the Constitution.
5. **Platform Architecture and Operational Governance**
   - `01_Architecture.md`
   - `03_AI_Brain.md`
   - `04_Project_Workflow.md`
   - `05_Coding_Standards.md`
   - `06_Database_Blueprint.md`
   - `07_Backend_Blueprint.md`
   - `08_AI_Development_Workflow.md`
   - `09_Codex_Guidelines.md`
6. **Roadmap**
   - `02_Roadmap.md`
   - Approved direction and sequencing. The roadmap does not override
     architecture or product governance.
7. **PATCH Definitions**
   - `patches/`
   - Bounded change authorization interpreted through every higher governing
     layer.
8. **Review Records**
   - `reviews/`
   - Plans, evidence, findings, lessons, and completion reports for specific
     PATCHes. Review records describe outcomes but do not create permanent
     architecture unless incorporated into an accepted governing document.

## Conflict Resolution

When two documents appear to conflict:

1. confirm that both statements apply to the same scope;
2. apply the higher-authority document;
3. check whether a later accepted ADR explicitly supersedes an earlier
   interpretation;
4. distinguish permanent governance from PATCH-specific evidence;
5. stop implementation and request architectural resolution if the conflict
   remains.

No contributor or AI agent may silently reconcile contradictory guidance.

## Mandatory Architectural Reading Order

Every future PATCH begins with:

```text
Product Bible v1.0
(begin with docs/README.md and docs/17_SATCO_Product_Blueprint.md)

↓

docs/00_Constitution.md

↓

docs/10_Engineering_Philosophy.md

↓

Relevant ADRs

↓

docs/01_Architecture.md

↓

docs/09_Codex_Guidelines.md

↓

docs/02_Roadmap.md

↓

Requested PATCH
```

This sequence is the mandatory architectural reading order. It begins with the
Product Bible entry point and master blueprint, then establishes constitutional
authority and the progressively narrower architectural and PATCH context.
Reading order does not change document authority: the Constitution remains the
highest governing authority.

The remaining Product Bible, workflow, coding, database, backend, and AI
documents must be read whenever their scope is affected.

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

1. Mandatory PATCH reading order.
2. `05_Coding_Standards.md`.
3. `06_Database_Blueprint.md` and `07_Backend_Blueprint.md`.
4. `08_AI_Development_Workflow.md`.
5. Relevant Product Bible documents, ADRs, and review history.

New developers should understand the product responsibility boundary before
learning implementation conventions.

### Architects

1. `00_Constitution.md`.
2. Full Product Bible: `10_Engineering_Philosophy.md` through
   `17_SATCO_Product_Blueprint.md`.
3. All accepted ADRs.
4. `01_Architecture.md`, `03_AI_Brain.md`, and domain blueprints.
5. `02_Roadmap.md` and relevant PATCH reviews.

Architects are responsible for resolving cross-document implications and
recording new architectural decisions explicitly.

### AI Agents

1. Mandatory PATCH reading order.
2. `13_AI_Behavior_Guide.md`.
3. `16_AI_Feature_Framework.md`.
4. `14_Engineering_Knowledge_Model.md`.
5. `15_User_Experience_Philosophy.md`.
6. Every scope-relevant technical blueprint and ADR.

AI agents must preserve Human Review, show uncertainty, and never interpret
their own output as engineering approval.

### Product Owners

1. `00_Constitution.md`.
2. `17_SATCO_Product_Blueprint.md`.
3. `11_Product_Vision.md` and `12_Product_Principles.md`.
4. `10_Engineering_Philosophy.md`.
5. `02_Roadmap.md`.
6. Relevant ADRs, PATCH definitions, and final reports.

Product decisions should be evaluated by engineering value, risk reduction,
coherence, and long-term product identity.

### Engineering Managers

1. `00_Constitution.md`.
2. `17_SATCO_Product_Blueprint.md`.
3. `10_Engineering_Philosophy.md`.
4. `11_Product_Vision.md`.
5. `14_Engineering_Knowledge_Model.md`.
6. `15_User_Experience_Philosophy.md`.
7. Relevant ADRs and workflow documents.

Engineering managers should focus on responsibility, Engineering Execution
Plan governance, Engineering Health, review, readiness, and organizational
learning.

### Codex

1. Follow the mandatory PATCH reading order exactly.
2. Read all documents named by the user.
3. Read every additional document whose scope may be changed.
4. Verify whether an ADR is required before implementation.
5. Follow `09_Codex_Guidelines.md` for approvals, validation, documentation,
   and Git operations.

Codex must not treat a PATCH as permission to exceed its declared scope.

### Future Contributors

1. Begin with this guide and the mandatory PATCH reading order.
2. Select the role path closest to the intended contribution.
3. Review the latest relevant ADRs and PATCH reports.
4. Preserve canonical terminology and documentation hierarchy.
5. Request clarification before introducing a conflicting interpretation.

## Design Rules for Documentation

- State a document’s purpose, scope, authority, and relationship to existing
  governance.
- Use canonical product terminology.
- Record architectural decisions in ADRs, not only in PATCH reports.
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
architectural process.
