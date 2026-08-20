# SATCO Governance Model

**Version:** 1.2

**Status:** Certified and Stable

## Purpose

This document defines how SATCO governs permanent principles, architecture,
experience, PATCH scope, and implementation. It establishes authority,
decision flow, ownership, conflict resolution, and controlled change.

## Scope

The Governance Model applies to all future SATCO documentation and development.
It does not create product behavior, technical architecture, experience design,
or implementation.

## Governance Philosophy

SATCO governance exists to protect engineering purpose across change.

Governance must ensure that:

- engineering value precedes software activity;
- human engineering responsibility remains permanent;
- architectural decisions are explicit;
- experience decisions are consistent and traceable;
- PATCHes remain bounded;
- implementation follows approved intent;
- disagreement and supersession are recorded rather than hidden;
- no lower-level document silently changes a higher-level rule.

Governance is not documentation volume. It is a clear chain from enduring
purpose to controlled implementation.

## Governance First Principle

No implementation decision is valid merely because it is technically possible.

Before implementation, SATCO must establish:

1. constitutional permission;
2. Engineering Intelligence Manifesto alignment;
3. Product Bible alignment;
4. architectural compatibility;
5. experience compatibility where users are affected;
6. bounded PATCH authorization;
7. validation and approval expectations.

When governance is incomplete, implementation pauses.

## Mandatory Governance Hierarchy

```text
Constitution

↓

Engineering Intelligence Manifesto

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

This hierarchy defines authority. A lower level applies and narrows higher
levels; it does not override them.

## Document Hierarchy

### 1. Constitution

**Authority:** Highest.

**Purpose:** Defines SATCO’s mission, permanent responsibility boundaries, and
non-negotiable principles.

No document may override the Constitution.

### 2. Engineering Intelligence Manifesto

**Authority:** Permanent philosophical and product-direction authority
subordinate only to the Constitution.

**Purpose:** Defines Engineering Intelligence as SATCO's enduring long-term
vision and establishes the principles governing Human responsibility, context,
evidence, relationships, explanation, Engineering Memory, and modular
evolution.

The Manifesto does not prescribe implementation or override the Constitution.
Changes require Foundation review, approval, versioning, and certification.

### 3. Product Bible

**Authority:** Permanent product governance subordinate to the Constitution
and Engineering Intelligence Manifesto.

**Purpose:** Defines product identity, Engineering Philosophy, Product Vision,
Product Principles, AI behavior, knowledge model, user-experience philosophy,
AI feature framework, and master Product Blueprint.

Product Bible changes require explicit governance review and recertification
when material.

### 4. Architecture Decision Record

**Authority:** Binding within its accepted architectural scope and subordinate
to the Constitution, Engineering Intelligence Manifesto, and Product Bible.

**Purpose:** Records why a durable technical or domain architecture decision
was made, alternatives, consequences, compatibility, and evolution.

Only Accepted ADRs are binding. A Proposed ADR does not authorize
implementation.

### 5. Experience Bible

**Authority:** Permanent experience governance subordinate to the Constitution,
Engineering Intelligence Manifesto, Product Bible, and accepted ADRs.

**Purpose:** Defines how SATCO should be experienced across navigation,
attention, interaction, AI presence, visual semantics, and accessibility.

The Experience Bible does not redesign architecture.

### 6. Experience Decision Record

**Authority:** Binding within its Accepted experience scope and subordinate to
all higher levels.

**Purpose:** Records a durable experience decision, alternatives, rationale,
accessibility, and consequences.

An XDR may interpret an accepted ADR for experience but may not change its
domain or technical decision.

### 7. PATCH

**Authority:** Bounded authorization for a specific change.

**Purpose:** Defines scope, exclusions, risks, acceptance criteria, validation,
and approval gates.

A PATCH does not create permanent governance by implication. Durable
architecture requires an ADR; durable experience behavior requires an XDR.

### 8. Implementation

**Authority:** Execution of approved decisions.

**Purpose:** Realizes the approved PATCH within all higher governance.

Implementation cannot reinterpret missing requirements silently. If approved
documents are insufficient or contradictory, work stops for resolution.

## Supporting Documentation

Supporting documents include:

- platform and technical blueprints;
- coding and workflow standards;
- roadmap;
- implementation plans;
- technical reviews;
- final reports;
- lessons learned;
- future recommendations.

These documents provide context, evidence, process, and sequencing. They do not
override the mandatory governance hierarchy.

The roadmap establishes planned direction, not architectural authority.
Review reports record evidence, not permanent decisions unless that decision is
incorporated into the proper governing document.

### Official Development Procedure

`docs/20_Development_Lifecycle.md` is the formally adopted official
procedural standard for SATCO implementation delivery. It operates under this
Governance Model and may define mandatory delivery gates, evidence, and exit
criteria, but it may not change policy authority, document precedence, or
approval ownership established by this Governance Model.

The minimum binding workflow before implementation begins is:

```text
Approved PATCH
    ↓
Architecture Review
    ↓
Accepted EDS
    ↓
Approved IDS
    ↓
IRR — READY FOR IMPLEMENTATION
```

The Development Lifecycle remains subordinate to this Governance Model. If
the two documents conflict, this Governance Model governs and the procedural
standard must be corrected before affected work continues.

### Official Implementation Execution Standard

`docs/framework/00_Framework_Constitution.md` and the SATCO Implementation
Framework v1.1 documents under `docs/framework/` are the mandatory execution
standard for implementing a PATCH after the Development Lifecycle has produced
an IRR outcome of `READY FOR IMPLEMENTATION`.

The Framework consolidates existing execution, sprint, blocker, validation,
testing, migration, Codex-runtime, and quality-gate rules. It is subordinate to
this Governance Model and to the Development Lifecycle procedure. It may not
create product or architecture authority, skip a lifecycle gate, change
approval ownership, or broaden an approved PATCH. If a conflict exists, this
Governance Model governs and affected work stops for correction.

## Foundation Documents

SATCO Foundation v1.2 consists of:

### Constitutional Foundation

- `docs/00_Constitution.md`

### Engineering Intelligence Manifesto Foundation

- `docs/Engineering_Intelligence_Manifesto.md`

### Product Foundation

- `docs/10_Engineering_Philosophy.md`
- `docs/11_Product_Vision.md`
- `docs/12_Product_Principles.md`
- `docs/13_AI_Behavior_Guide.md`
- `docs/14_Engineering_Knowledge_Model.md`
- `docs/15_User_Experience_Philosophy.md`
- `docs/16_AI_Feature_Framework.md`
- `docs/17_SATCO_Product_Blueprint.md`

### Architectural Foundation

- `docs/01_Architecture.md`
- accepted records under `docs/adr/`

### Experience Foundation

- `docs/18_Experience_Bible.md`
- accepted records under `docs/xdr/`

### Governance Foundation

- `docs/19_Governance_Model.md`
- `docs/README.md`
- `docs/09_Codex_Guidelines.md`
- `docs/framework/00_Framework_Constitution.md` through
  `docs/framework/09_Framework_Roadmap.md`

### Delivery Governance

- `docs/02_Roadmap.md`
- PATCH definitions under `docs/patches/`
- review evidence under `docs/reviews/`

Foundation status does not imply that future product capabilities are
implemented.

SATCO Foundation v1.2 is the governing baseline for feature development.
Routine PATCH work must not directly rewrite its foundational documents.

A foundational change must first be justified by the governing record
appropriate to the decision. Durable architecture requires an accepted ADR;
durable experience behavior requires an accepted XDR. A governance-only
procedural change that alters neither may be approved and recorded directly in
the Governance Model through the complete Foundation approval flow, provided
the ADR/XDR threshold assessment is explicitly recorded. After approval,
affected foundation documents are released through a new Foundation version.

### Foundation v1.1 Certification Record

| Field | Decision |
|---|---|
| Proposal | Framework Review Resolution — SATCO Implementation Framework v1.1 |
| Scope | Governance execution procedure and supporting documentation only |
| ADR threshold | Not applicable: no durable product, domain, or technical architecture decision changes |
| XDR threshold | Not applicable: no experience behavior or interaction decision changes |
| Architecture Guardian review | Approved |
| Product Owner review | Approved |
| Conflict and consequence assessment | PASS; authority hierarchy preserved and procedural gates clarified |
| Certification | SATCO Foundation v1.1 — Certified and Stable |
| Decision date | 2026-08-02 |

### Foundation v1.2 Certification Record

| Field | Decision |
|---|---|
| Proposal | SATCO Engineering Intelligence Manifesto v1.0 |
| Scope | Additive permanent philosophical Foundation layer immediately below the Constitution |
| Architecture review | `docs/reviews/Engineering_Intelligence_Manifesto_Architecture_Review.md` — PASS |
| Architecture Guardian review | Approved |
| Product Owner approval | Approved |
| ADR threshold | Not applicable: the Manifesto preserves accepted architecture and delegates technical decisions to ADRs |
| XDR threshold | Not applicable: the Manifesto creates no interaction or experience behavior |
| Conflict and consequence assessment | PASS; Constitution remains supreme and existing Foundation meaning is preserved |
| Certification | SATCO Foundation v1.2 — Certified and Stable |
| Decision date | 2026-08-02 |

Stable does not prohibit governed evolution. It prohibits uncontrolled
modification.

## Decision Flow

Every proposed change follows:

```text
Engineering problem
    ↓
Constitution review
    ↓
Engineering Intelligence Manifesto alignment
    ↓
Product Bible review
    ↓
Architecture impact assessment
    ↓
ADR creation or confirmation
    ↓
Experience impact assessment
    ↓
XDR creation or confirmation
    ↓
PATCH scope and acceptance definition
    ↓
Implementation plan
    ↓
Approved implementation
    ↓
Validation and review
    ↓
Governed completion
```

ADR or XDR creation is required only when the change meets the respective
decision threshold. The assessment itself is always required.

## ADR Decision Threshold

An ADR is required when a change establishes or modifies a durable:

- domain boundary;
- data ownership rule;
- architecture pattern;
- security or authorization model;
- integration boundary;
- provider strategy;
- infrastructure or deployment rule;
- lifecycle or state model;
- cross-PATCH technical constraint.

An ADR is not a substitute for a PATCH.

## XDR Decision Threshold

An XDR is required when a change establishes or modifies a durable:

- Engineering Cockpit structure;
- navigation model;
- information hierarchy;
- attention or priority presentation;
- AI presence pattern;
- Human Review interaction;
- status or lifecycle presentation;
- visual semantic;
- motion behavior;
- accessibility rule;
- cross-PATCH experience convention.

An XDR is not required for a local presentation detail that follows an existing
Accepted XDR and does not create precedent.

## Approval Flow

### Foundation or Product Governance

1. Proposal.
2. Architecture Guardian review.
3. Product-owner review.
4. Conflict and consequence assessment.
5. Explicit approval.
6. Version update and certification when material.

### ADR

1. Proposed.
2. Independent architecture review.
3. Product Bible and compatibility validation.
4. Accepted or rejected by authorized architecture governance.
5. Referenced by the implementing PATCH.

### XDR

1. Proposed.
2. Experience and accessibility review.
3. ADR and Experience Bible validation.
4. Accepted or rejected by authorized experience governance.
5. Referenced by the implementing PATCH.

### PATCH

1. Repository and governance review.
2. Plan or architecture review.
3. Scope approval.
4. Approved implementation.
5. Validation.
6. Final review.
7. Git approval.

Approval at one level does not imply approval at another.

## Conflict Resolution

When documents conflict:

1. confirm that both statements apply to the same decision and scope;
2. identify each document’s hierarchy level and status;
3. apply the higher-level governing rule;
4. apply explicit, valid supersession within the same record type;
5. stop affected work if the conflict remains;
6. resolve the conflict in the proper governing document;
7. record the resolution and affected lower-level updates.

Special rules:

- Constitution always prevails.
- Engineering Intelligence Manifesto prevails over Product Bible, ADR,
  Experience Bible, XDR, PATCH, and implementation.
- Product Bible prevails over ADR, Experience Bible, XDR, PATCH, and
  implementation.
- Accepted ADRs prevail over the Experience Bible and XDRs in their
  architectural scope.
- Experience Bible prevails over XDRs.
- Accepted XDRs prevail over PATCH experience choices.
- PATCH scope prevails over implementation convenience.
- Newer does not automatically mean higher authority.
- Proposed records do not override Accepted records.

No person or AI agent may silently choose a convenient interpretation.

## Document Ownership

| Document type | Primary owner | Required reviewers |
|---|---|---|
| Constitution | Product Owner | Architecture Guardian and engineering authority |
| Engineering Intelligence Manifesto | Product Owner | Architecture Guardian, engineering authority, and product governance |
| Product Bible | Product Owner | Architecture Guardian and product governance |
| ADR | Software/Domain Architect | Architecture Guardian and affected technical owners |
| Experience Bible | Product Owner | Experience governance, Architecture Guardian, accessibility reviewer |
| XDR | Experience Architect | Product owner, affected engineering representatives, accessibility reviewer |
| PATCH | PATCH owner | Architecture/technical reviewers and affected domain owners |
| Implementation Plan | Implementation owner | Technical reviewer |
| Review Report | Independent reviewer | PATCH owner and relevant authority |

Ownership means responsibility for integrity and review. It does not permit an
owner to bypass higher governance or professional engineering authority.

AI agents may draft and review documentation. They do not own or approve
engineering decisions.

## Change Management

Every governed change must:

- state the problem and engineering value;
- identify affected governing documents;
- preserve scope;
- identify whether an ADR or XDR is required;
- record alternatives and consequences;
- state compatibility and migration implications where applicable;
- define approval and validation;
- update lower-level documents after higher-level approval;
- preserve superseded history;
- avoid silent semantic changes.

Routine PATCH work applies foundational governance and must not modify it as an
incidental implementation step. If PATCH work reveals a necessary foundational
change, the PATCH pauses that portion of work until:

1. the governing record appropriate to the decision justifies and approves the
   change, including an ADR or XDR when its threshold is met;
2. affected foundational documents are reviewed as one coherent set;
3. a new Foundation version is declared and certified;
4. dependent PATCH scope is revalidated.

Changes should be additive when possible. Rewriting historical records without
explicit supersession is prohibited.

Emergency implementation does not permanently waive governance. Any emergency
exception requires recorded authority, bounded duration, risk, and subsequent
governance review.

## Versioning Strategy

### Foundation Versions

Foundation versions represent a certified coherent set of constitutional,
product, architecture, experience, and governance documents.

Version 1.0 establishes the initial permanent foundation.

Foundation v1.2 is Certified and Stable. A future Foundation version is
required for approved changes to foundational meaning. Stable describes change
control, not an inability to evolve.

Version 1.1 certifies the governance-aligned adoption of SATCO Implementation
Framework v1.1 without changing product, domain, technical architecture, or
experience authority.

Version 1.2 certifies SATCO Engineering Intelligence Manifesto v1.0 as the
second permanent Foundation layer, subordinate only to the Constitution and
governing all lower layers without changing approved implementation contracts.

### Document Versions

Permanent foundation documents state a version when certified. Version changes
follow:

- **Patch version:** Clarification without changing meaning.
- **Minor version:** Additive governance or a new compatible permanent concept.
- **Major version:** Material change to product identity, authority, or
  responsibility boundaries.

### ADR and XDR Versions

ADR and XDR identifiers remain stable. Their status and superseding
relationships preserve decision history. Materially different decisions use a
new record rather than rewriting an Accepted record silently.

### PATCH Versions

PATCH identifiers define bounded delivery units. Sub-PATCHes may decompose
approved work but may not broaden the parent scope.

### PATCH Registry and Numbering

The PATCH registry in this section is the authoritative source for PATCH
number allocation, reservation, scope, status, and supersession. The
Governance Model owns the numbering policy. A PATCH number may be allocated,
released, reassigned, or retired only through an approved governance change
accepted by the Architecture Guardian and Repository Owner.

Authoritative PATCH records reside under `docs/patches/`. Records under
`docs/design/` may define subordinate design contracts but do not independently
authorize implementation.

| Identifier | Registered scope | Authoritative record | Registry status |
|---|---|---|---|
| PATCH-022 | EKG Backend Foundation | `docs/patches/PATCH-022.md` | Draft |
| PATCH-022.1 | Core Enumerations and Contracts | `docs/design/PATCH-022.1-Core-Enumerations-and-Contracts.md` | Delivered stage |
| PATCH-022.2 | Engineering Foundation | `docs/design/PATCH-022.2-Engineering-Foundation.md` | Delivered stage |
| PATCH-022.3 | Engineering Object Aggregate | `docs/design/PATCH-022.3-Engineering-Object-Aggregate.md` | Registered stage |
| PATCH-022.3A | Development Environment Standardization | `docs/design/PATCH-022.3A-Development-Environment-Standardization.md` | Approval status unresolved |
| PATCH-023 | EngineeringObject Application Layer | `docs/patches/PATCH-023.md` | DONE |
| PATCH-023.1 | EngineeringObject API Contract | `docs/design/PATCH-023.1-EngineeringObject-API-Contract.md` | Draft; not authorized |
| PATCH-024 | EngineeringObject Persistence Migration | `docs/patches/PATCH-024.md` | DONE |
| PATCH-025 | Authenticated Organization Context | `docs/patches/PATCH-025.md` | DONE |
| PATCH-026 | Engineering Relationship Engine | `docs/patches/PATCH-026.md` | DONE |
| PATCH-027 | Evidence Foundation | `docs/patches/PATCH-027.md` | DONE |
| PATCH-028.0 | Manifesto Governance Integration | `docs/patches/PATCH-028.0.md` | DONE |
| PATCH-028 | Universal Engineering Capture Foundation | `docs/patches/PATCH-028.md` | DELIVERY AUTHORIZED — Commit and push execution pending |
| PATCH-028.1 | Project Organization Ownership | `docs/patches/PATCH-028.1.md` | DONE / CLOSED |
| PATCH-029 | Engineering Journal | `docs/patches/PATCH-029.md` | DONE / CLOSED — commit `b7fb8d4412d6b7528365f19b1418926aaa716686`; push and remote verification PASS; divergence 0/0; migration not required and not executed |
| PATCH-032 | Technical Report | `docs/patches/PATCH-032.md` | DONE / CLOSED — implementation delivery `26b67727e364c7929747f581c2360ab418cbbdb3`; governance closure `3611fc5c0b8651e604278a70a23d9acf3f076913`; QG-M1, QG-11, QG-12, push, and remote verification PASS |
| PATCH-034 | Engineering Organizational Memory | `docs/patches/PATCH-034.md` | DONE / CLOSED — delivery `5d657a77bc3826498d2ae5db602283bbfc1f95df`; governance closure `18f0bb19a51c20edb0d99e78481af8df02668f79`; QG-M1/QG-11/QG-12 and remote verification PASS |
| PATCH-035 | AI Capture Assistant | `docs/patches/PATCH-035.md` | DONE / CLOSED — delivery `ec8a0bc92c63d18d0d8d4831e6fa3814ac5118fe`; governance closure `01fb002186297eb5bcaa5e6d0ee835402616ee33`; QG-M1/QG-11/QG-12 and remote verification PASS |
| PATCH-036 | SATCO Web Application & Engineering Dashboard | `docs/patches/PATCH-036.md` | DONE / CLOSED — delivery `9e2749f1534bca21131d0fd38fe6b963e41f38de`; QG-M1/QG-11/QG-12, push, and remote verification PASS; divergence 0/0 |
| PATCH-037 | SATCO Engineering Command Center Productization | `docs/patches/PATCH-037.md` | DONE / CLOSED — delivery `8062d49e497f22fef44f4f96b08068683ac3a9bc`; QG-M1/QG-11/QG-12, push, and remote verification PASS; divergence 0/0 |
| PATCH-038 | Customer-to-Capture Engineering Work Bootstrap | `docs/patches/PATCH-038.md` | DONE / CLOSED — delivery `b2b7b102be4e957d106b3138dd6f14b5488eb6ff`; governance closure `b5bf1e1c22f262b1aa3cf0be3a12a70e6413e998`; QG-M1/QG-11/QG-12 and remote verification PASS |
| PATCH-039 | Technical Report Authoring & Human Acceptance Experience | `docs/patches/PATCH-039.md` | DONE / CLOSED — delivery `80d006e5232e154502a36baf46b9b40be7c3504c`; QG-M1/QG-11/QG-12 and remote verification PASS |

PATCH-030 and PATCH-031 are intentionally unregistered PATCH identifiers. The
repository contains the separate Draft
`docs/design/EDS-030-Technical-Proposal-Review.md` and the historically
referenced deferred architectural target
`docs/design/EDS-031-Engineering-Digital-Twin-Vision.md`. Their EDS numbers
do not register, reserve, or authorize PATCH-030 or PATCH-031.

PATCH identifiers and EDS identifiers are not interchangeable registrations.
The Technical Report governance chain was deliberately aligned at PATCH-032
and is now `DONE / CLOSED`. PATCH-033 subsequently completed and is `DONE /
CLOSED`. PATCH-034, PATCH-035, and PATCH-036 are `DONE / CLOSED`. PATCH-036
Architecture, EDS, IDS, Implementation Plan, IRR, Batches 1–4, Independent
Final Review, Human QG-11, and bounded QG-12 delivery are PASS / COMPLETE.

### Current Roadmap Position After PATCH-036 Closure

PATCH-029 Engineering Journal, PATCH-032 Technical Report, PATCH-033
Engineering Knowledge Graph Integration, PATCH-034 Engineering Organizational
Memory, and PATCH-035 AI Capture Assistant are `DONE / CLOSED`. PATCH-036 is
the first authenticated SATCO Web Application & Engineering Dashboard over
those accepted APIs. It owns presentation and bounded device-local layout
preferences only; it owns no canonical engineering or authorization state.
Architecture, EDS, IDS, Plan, IRR, implementation, Independent Final Review,
Human QG-11, QG-12 delivery, push, and remote verification are PASS; PATCH-036
is `DONE / CLOSED`. PATCH-037 Engineering Command Center Productization is
also `DONE / CLOSED`; QG-M1, Human QG-11, QG-12, push, and remote verification
are PASS. PATCH-038 Customer-to-Capture Engineering Work Bootstrap has PASS
Architecture, EDS, IDS, Plan, IRR, Batches 1–4, Independent Final
Implementation Review, Human QG-11, and QG-M1. Implementation is complete at
Alembic head `e03800000001`; QG-12 delivery and closure remain pending.

The former PATCH-022.2 through PATCH-022.10 reservations in the Draft
PATCH-022 sequence are superseded. PATCH-022.4 through PATCH-022.10 are
released and unassigned. Repository, service, and API work for
EngineeringObject is governed by PATCH-023 and its approved sub-PATCHes.

### Implementation Versions

Implementation versions and commits must reference the governing PATCH and
applicable ADR/XDR decisions through project documentation and review.

## Governance Validation

Before implementation begins, reviewers confirm:

- hierarchy was followed;
- required documents were read;
- the certified Engineering Intelligence Manifesto version is referenced;
- a Manifesto Alignment Record identifies supported, affected, and preserved
  principles, contribution, risks, and evidence;
- the Architecture Review records `Manifesto Compliance: PASS`;
- the IRR records `Manifesto Alignment Verified: YES` and
  `QG-M1 Readiness Result: PASS`;
- ADR/XDR thresholds were assessed;
- all governing records are in an appropriate status;
- no unresolved conflict remains;
- PATCH scope is explicit;
- validation and rollback expectations are defined;
- no lower-level artifact expands higher-level authority.

`QG-M1 — Manifesto Alignment` is a mandatory cumulative execution-evidence
gate. It supplements existing quality gates and Human approval; it does not
create a new authority layer. QG-M1 is evaluated before implementation
readiness and again during Final Review against the actual diff and evidence.
A PENDING or FAIL result cannot support READY, IMPLEMENTATION COMPLETE, or
DONE.

QG-M1 applies prospectively to PATCH-028.0 and later PATCHes after adoption.
Completed PATCH-023 through PATCH-027 remain governed by their recorded
completion evidence and are not retroactively reopened. A later material
change to those capabilities proceeds through a new PATCH under QG-M1.

## Future Governance Evolution

Governance may evolve through an explicitly approved update to this document
and affected higher-level governance.

Future evolution may define:

- formal approval authorities;
- document templates;
- automated consistency checks;
- governance indexes;
- review cadences;
- certified Foundation releases.

Automation may verify governance evidence. It must not become an authority that
approves engineering or architectural decisions by itself.

## Final Governance Statement

SATCO governs before it implements.

Every implementation must be traceable upward to an approved PATCH, experience
decision where applicable, architectural decision where applicable, Product
Bible principle, and constitutional purpose.
