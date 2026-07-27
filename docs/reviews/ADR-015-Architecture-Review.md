# ADR-015 Architecture Review

## Status

Final Architecture Review Complete — Acceptance Recommended

## Review Objective

This document records the documentation-only Architecture Guardian and Chief
Engineering Architect review of:

`docs/adr/ADR-015-Engineering-Context-Domain-Architecture.md`

The review determines whether ADR-015 is ready to move from:

**Proposed — Awaiting Architecture Approval**

to:

**Accepted**

No EDS, implementation, database, API, schema, repository, service, migration,
or product behavior is defined or authorized by this review. ADR-015 was not
modified.

## Documents Reviewed

- `docs/00_Constitution.md`
- `docs/10_Engineering_Philosophy.md`
- `docs/13_AI_Behavior_Guide.md`
- `docs/14_Engineering_Knowledge_Model.md`
- `docs/17_SATCO_Product_Blueprint.md`
- `docs/18_Experience_Bible.md`
- `docs/19_Governance_Model.md`
- `docs/adr/ADR-013-AI-Engineering-Copilot-Architecture.md`
- `docs/adr/ADR-014-Engineering-Workspace-Domain-Model.md`
- `docs/patches/PATCH-020.md`
- `docs/discovery/PATCH-020.2-Engineering-Context-Discovery.md`
- `docs/reviews/PATCH-020.2-Discovery-Architecture-Review.md`
- `docs/adr/ADR-015-Engineering-Context-Domain-Architecture.md`

The implemented Project and Engineering Workspace boundaries were inspected
read-only where useful for compatibility assessment.

## Architecture Guardian Verdict

**PASS — ACCEPTANCE RECOMMENDED**

ADR-015 is a valid subordinate refinement of ADR-013 and ADR-014.

It:

- preserves Context-First AI;
- preserves the accepted Project and Engineering Workspace aggregate
  boundaries;
- does not redefine Workspace identity, ownership, membership, lifecycle, or
  archive semantics;
- does not transfer engineering authority to AI;
- preserves Human Review, traceability, conflict visibility, and history;
- establishes durable domain semantics without selecting implementation;
- provides sufficient architectural boundaries for EDS-020.2;
- does not absorb future decisions, plans, health, AI, memory, documents,
  tasks, workflow, or Knowledge Graph technology.

No conflict with higher governance was found.

## Chief Engineering Architect Verdict

**PASS — ENGINEERING DOMAIN SUFFICIENCY CONFIRMED**

ADR-015 reflects real multidisciplinary engineering conditions rather than a
generic information-management model.

It recognizes that:

- engineering values require units, quantity meaning, basis, conditions,
  source, revision, and uncertainty where material;
- authentic sources may disagree;
- source authority is bounded by purpose and applicability;
- ownership, stewardship, competence, review, and approval are different;
- missing, stale, disputed, superseded, and inaccessible information have
  distinct engineering meanings;
- cross-discipline dependencies require accountable providers and consumers;
- material correction must preserve what was originally used;
- AI can assist interpretation but cannot establish engineering truth.

The domain model safely applies to:

- Electrical engineering through supply basis, motor data, protection inputs,
  standards, calculations, and Mechanical interfaces;
- Instrumentation engineering through process conditions, measurement basis,
  vendor data, compensation evidence, and Process interfaces;
- Control engineering through functional requirements, IO, interfaces,
  equipment data, and Instrumentation commitments;
- Mechanical engineering through equipment duty, loads, vendor evidence,
  process requirements, and supplied interface data;
- Process engineering through fluid properties, operating and design
  conditions, process basis, and multidisciplinary input authority;
- Civil engineering through site conditions, equipment loads, layouts,
  geotechnical or structural evidence, and Mechanical interfaces.

No discipline-specific calculation or design rule is improperly introduced.

## Product Bible Alignment

ADR-015 complies with Product Bible v1.0.

| Product Bible requirement | ADR-015 response | Result |
|---|---|---|
| Engineering First | Defines Context around actual engineering meaning and consequence | Pass |
| Engineers Decide | Keeps verification, resolution, review, and approval human-owned | Pass |
| Context Before AI | Makes governed Context the prerequisite for AI assistance | Pass |
| Never Invent Facts | Makes Missing Information and safe failure explicit | Pass |
| Never Hide Uncertainty | Preserves conflicts, assumptions, staleness, and dispute | Pass |
| Confidence Must Be Earned | Separates confidence from authority | Pass |
| Standards Require Context | Requires applicability, edition, scope, and precedence review | Pass |
| Relationships Create Meaning | Defines Project, Workspace, source, object, and interface relationships | Pass |
| Workspace Before Conversation | Rejects chat history as Context ownership | Pass |
| Decisions Preserve Rationale | Keeps human decision evidence in the future Decision Log | Pass |
| Memory Follows Review | Excludes unreviewed Context and AI output from trusted Memory | Pass |
| Single Source of Truth | Rejects copied Project facts and silent source replacement | Pass |
| Continuous Improvement Is Governed | Preserves review, history, and reuse limits | Pass |

No Product Bible principle is weakened or reinterpreted.

## ADR-013 Alignment

ADR-015 directly supports ADR-013:

- AI identifies relevant Context before advising.
- Sources, standards, revisions, prior decisions, and history remain
  traceable.
- Missing or conflicting information reduces the permitted conclusion.
- AI output remains advisory, explainable, confidence-aware, and reviewable.
- Historical similarity remains evidence rather than equivalence.
- Engineering Impact is a review recommendation, not automatic propagation.
- Safe failure is preferred to unsupported inference.

ADR-015 does not alter ADR-013’s human authority or AI safety boundary.

## ADR-014 Alignment

ADR-015 refines ADR-014’s Engineering Context boundary without changing it.

It retains:

- Project as owner of shared Project identity and scope;
- Workspace as owner of Project/Discipline identity and local accountability;
- Context as a governed aggregate view that resolves rather than duplicates
  authoritative objects;
- derived views and selective immutable snapshots;
- future Decision Log ownership of human judgment evidence;
- future Execution Plan ownership of proposed engineering movement;
- domain history distinct from generic audit evidence.

ADR-015’s dimension model clarifies ADR-014’s authoritative, governed,
derived, and snapshot concepts. It does not contradict them.

## Domain-Boundary Review

### Engineering Context

Owns no universal source of engineering truth. It connects and qualifies
relevant meaning across sources, scope, time, authority, maturity, review,
freshness, criticality, confidentiality, and derivation.

### Engineering Decision Log

Owns why a human decision was made, who made it, alternatives, rationale,
evidence, uncertainty, affected scope, and supersession. Context exposes
decision relevance but does not become the decision.

### Engineering Execution Plan

Consumes Context as planning input. Proposed phases, activities, dependencies,
deliverables, effort, roles, and next steps remain plan hypotheses, not Context
truth.

### Engineering Health and Workspace Readiness

Derive explainable indicators and blockers from Context. They do not replace
Context or represent approval.

### AI Insights

Produce advisory findings linked to the Context considered. They neither own
nor modify Context.

### ENSE

Consumes Context to recommend next actions. It neither executes action nor
converts recommendations into tasks, decisions, or facts.

### Engineering Memory

Owns governed reuse of reviewed outcomes and lessons. Historical Context alone
is not trusted Memory.

### Engineering Knowledge Graph

Expresses connected engineering meaning conceptually. ADR-015 makes no graph
technology decision.

### Documents

Remain governed sources and evidence carriers. They do not become the Context
model.

### Tasks and workflow

Remain outside Context. Interface Commitments describe engineering dependency
and accountability without defining assignments, notifications, schedules, or
workflow execution.

All reviewed boundaries are clear.

## Authority and AI Safety Review

ADR-015 defines authority as governed standing for a bounded purpose. It
correctly rejects:

- confidence as authority;
- AI origin as authority;
- source existence as universal applicability;
- ownership as technical competence;
- recency alone as truth;
- historical frequency as a rule.

AI may summarize, compare, identify possible missing information, detect
potential conflicts, suggest relationships, identify historical similarity,
propose questions, estimate confidence, and recommend review.

AI may not:

- create authoritative facts;
- modify approved Context;
- resolve source conflict;
- promote maturity or approval;
- invent standards, sources, vendor data, or history;
- hide uncertainty;
- erase historical evidence;
- bypass access control.

Human engineering responsibility remains complete and explicit.

## Ownership and Competence Review

ADR-015 distinguishes:

- information owner;
- engineering steward;
- reviewer;
- approver where applicable;
- source owner;
- Workspace responsibility;
- Project responsibility.

The distinction is sufficient and durable:

- an information owner maintains controlled information;
- a steward is competent for its engineering meaning;
- a reviewer evaluates within authorized competence;
- an approver has separately governed authority for a specific subject;
- Project and Workspace owners coordinate scope without becoming universal
  technical authorities.

Current roles do not by themselves prove competence. The future EDS must map a
bounded capability model without inventing unauthorized persisted roles.

## Source Precedence Review

ADR-015 rejects one universal source hierarchy.

Precedence is explicitly:

- domain-sensitive;
- purpose- and scope-sensitive;
- reviewable;
- traceable;
- capable of preserving unresolved conflict.

Contract, Customer direction, approved Project basis, qualified engineering
evidence, standard applicability, revision, and effective time may each matter
without one hidden ordering applying to every question.

A higher-precedence source may govern current use but does not erase authentic
lower-precedence evidence. Human resolution remains required.

This is sufficient durable architecture. Specialized precedence rules that
would govern future source domains require separate approval.

## Value and Unit Review

ADR-015 makes semantic completeness mandatory.

A meaningful value may require:

- value and unit;
- quantity type;
- tolerance or range;
- calculation or measurement basis;
- reference, normal, design, minimum, or maximum condition;
- source and revision;
- effective or observation time;
- uncertainty.

The ADR deliberately avoids a universal measurement design. It establishes the
correct durable requirement: engineering values cannot be detached from their
units and engineering meaning.

## Maturity Review

Maturity is correctly independent from:

- authority;
- review state;
- confidence;
- formal document approval;
- freshness.

The conceptual maturity vocabulary is illustrative rather than a prematurely
fixed implementation enumeration. AI cannot self-promote maturity. Material
maturity changes remain traceable and human- or source-governed.

Maturity may differ across Disciplines for the same shared information because
fitness for use depends on purpose.

## Criticality Review

Criticality is correctly defined by the consequence of information being
incorrect, missing, stale, conflicting, misunderstood, or inaccessible.

It affects:

- review priority;
- visibility;
- freshness expectations;
- audit significance;
- snapshot justification;
- AI caution.

ADR-015 avoids one universal score or formula. Criticality does not create
authority or truth.

## Freshness Review

ADR-015 distinguishes freshness, review-by date, expiry, stale state, revision
supersession, event-triggered invalidation, and context-dependent validity.

This is necessary because:

- vendor data may change by revision;
- site and process conditions may change by event;
- calculations may become stale when inputs change;
- standards applicability may change by edition or obligation;
- human decisions may remain historically valid while no longer governing
  current work.

There is no universal expiry rule. Stale information remains visible and
historically traceable.

## Correction and History Review

ADR-015 distinguishes:

- correctable metadata;
- immutable historical evidence;
- superseding records;
- withdrawn information;
- corrected information;
- disputed information.

Material correction preserves original value, corrected value, reason, actor,
timestamp, source, affected objects, and review outcome.

This prevents silent rewriting while allowing genuine error correction.
Historical Context remains labeled and cannot silently return as current.

## Snapshot Review

Snapshots are selective evidence frames justified by material events such as:

- formal review;
- engineering decision;
- Execution Plan generation basis;
- material AI recommendation;
- milestone or stage transition;
- audit or dispute resolution.

ADR-015 rejects snapshot-after-every-change. A snapshot requires a bounded
purpose, decisive evidence, authorization, confidentiality treatment, and
retention governance.

This balances reproducibility against duplication, confidentiality, and
uncontrolled growth.

## Confidentiality Review

Context access may be constrained by Project authorization, Workspace
membership, role or capability, source confidentiality, commercial
sensitivity, personal data, vendor restrictions, Customer restrictions, and
historical reuse limits.

Least privilege applies across Workspaces. Restrictions remain attached to
derived views, snapshots, search, AI retrieval, history, and reuse.

ADR-015 explicitly prevents summaries, counts, AI, or search from revealing
inaccessible source information. It does not create a new RBAC model.

## Cross-discipline Accountability Review

ADR-015 supports shared engineering meaning without uncontrolled copying.

It preserves:

- source Workspace or authority;
- consuming Workspace;
- provider and consumer;
- information owner and engineering steward;
- reviewer and competence boundary;
- Interface Commitment;
- revision and supersession;
- confidentiality;
- change impact;
- unresolved conflict.

Consumers may interpret shared information within their Discipline but may not
alter the source or declare another Discipline’s commitment fulfilled.

This model supports Electrical, Instrumentation, Control, Mechanical, Process,
and Civil coordination while retaining accountable Discipline ownership.

## Scenario Validation

### Electrical — New 160 kW Process Pump

| Required concept | Evidence in ADR-015 | Result |
|---|---|---|
| Project-level Context | Customer, plant, area, scope, supply basis, requirements, stage | Pass |
| Workspace-level Context | Motor identity, power, voltage basis, duty, starting data, short-circuit need, standards | Pass |
| Sources | Motor schedule, Mechanical revision, vendor datasheet, Customer standard, Project basis | Pass |
| Units and meaning | 160 kW and qualified voltage/short-circuit bases require source and conditions | Pass |
| Missing information | Missing vendor datasheet and unestablished short-circuit source | Pass |
| Conflicts | Customer standard versus approved Project basis remains visible | Pass |
| Criticality | Missing and changed inputs constrain dependent electrical work and invoke Context criticality rules | Pass |
| Freshness | New Mechanical revision makes prior derivations stale | Pass |
| Human Review | Electrical engineer verifies governing sources and bounded use | Pass |
| AI boundary | AI flags gaps and impacts but cannot verify, select, or approve | Pass |
| Correction and supersession | Error correction differs from legitimate design revision | Pass |
| Historical preservation | Both revisions and prior dependent meaning remain traceable | Pass |
| Cross-discipline dependency | Mechanical provides confirmed motor information to Electrical | Pass |

No engineering calculation is performed.

### Instrumentation — Compensated Flowmeter

| Required concept | Evidence in ADR-015 | Result |
|---|---|---|
| Project-level Context | Customer, plant, unit, basis, requirements, stage | Pass |
| Workspace-level Context | Service, purpose, tag, process conditions, accuracy, interfaces, vendor evidence | Pass |
| Sources | Process data, vendor data, compensation reference, Customer requirements | Pass |
| Units and meaning | Pressure, temperature, flow, conditions, references, revision, and uncertainty stay connected | Pass |
| Missing information | Missing reference condition is a blocking condition, not null | Pass |
| Conflicts | Competing operating-pressure values remain visible | Pass |
| Criticality | Incorrect or stale compensation inputs are identified as potentially high impact | Pass |
| Freshness | Process and vendor revision changes make dependent interpretation stale | Pass |
| Human Review | Qualified Process and Instrumentation engineers establish bounded basis | Pass |
| AI boundary | AI warns and summarizes but cannot invent, merge, select, or approve | Pass |
| Correction and supersession | Later governed evidence supersedes current use without erasing prior evidence | Pass |
| Historical preservation | Prior process/vendor revisions, warnings, and review remain historical | Pass |
| Cross-discipline dependency | Process provides confirmed conditions to Instrumentation | Pass |

No engineering calculation is performed.

Both scenarios demonstrate the required domain behavior.

## Anti-pattern Validation

| Anti-pattern | ADR-015 decision | Validation |
|---|---|---|
| One large JSON Context blob | Rejected | Pass |
| Document-only Context | Rejected | Pass |
| Chat-history Context | Rejected | Pass |
| AI-managed authority | Rejected | Pass |
| One universal lifecycle | Rejected | Pass |
| One universal freshness rule | Rejected | Pass |
| Hidden source precedence | Rejected | Pass |
| Snapshot after every change | Rejected | Pass |
| Project facts copied into every Workspace | Rejected | Pass |
| Premature Knowledge Graph technology | Rejected | Pass |
| Null treated as Missing Information | Rejected | Pass |
| Confidence treated as authority | Rejected | Pass |
| Ownership treated as competence | Rejected | Pass |

All mandatory anti-patterns are explicitly and coherently rejected.

## Open-question Classification

ADR-015 contains nine open architectural questions. Each is classified below.

| # | Open question | Classification | Rationale |
|---|---|---|---|
| 1 | Minimum coherent Project-, Workspace-, interface-, and object-level Context concepts | **2 — Must be resolved in EDS-020.2** | ADR defines the boundaries; EDS must select the bounded first release |
| 2 | Domain-specific source-precedence rules and competent authority | **4 — Requires a future ADR or XDR** | ADR-015 rejects universal precedence; any durable specialized hierarchy requires explicit governance rather than EDS invention |
| 3 | Mapping current `admin` and `engineer` roles to stewardship, review, and decision responsibility | **2 — Must be resolved in EDS-020.2** | Initial capabilities and authorization behavior are necessary for a bounded implementation |
| 4 | Criticality assessments requiring independent Human Review | **2 — Must be resolved in EDS-020.2** | EDS must define the initial review boundary without creating a universal formula |
| 5 | Dependency changes that make each initial Context kind stale | **2 — Must be resolved in EDS-020.2** | Initial freshness behavior must be explicit and testable |
| 6 | Snapshot-triggering events and sufficient decisive evidence | **2 — Must be resolved in EDS-020.2** | The first release must bound snapshot use and avoid indiscriminate capture |
| 7 | Retention and confidentiality for snapshots, disputes, withdrawal, and cross-Customer reuse | **4 — Requires a future ADR or XDR** | Durable retention and cross-Customer reuse policy is cross-cutting governance; EDS-020.2 must remain within existing restrictions |
| 8 | Minimum Human Review and Decision Log foundation for conflict resolution and governed derived findings | **2 — Must be resolved in EDS-020.2** | PATCH-020.2 explicitly depends on these minimum semantics |
| 9 | Interface Commitments included in the first release without workflow behavior | **2 — Must be resolved in EDS-020.2** | Release scope must identify the minimum useful dependency behavior |

Classification summary:

- Category 1 — Must be resolved before ADR acceptance: **0**
- Category 2 — Must be resolved in EDS-020.2: **7**
- Category 3 — May be deferred to a later PATCH: **0**
- Category 4 — Requires a future ADR or XDR: **2**

No Category 1 question remains. The open questions are properly downstream of
the durable architecture and do not block ADR acceptance.

## Blocking Issues

**None.**

No architectural contradiction, missing safety boundary, Product Bible
conflict, ADR conflict, unresolved domain definition, or premature
implementation decision blocks acceptance.

ADR-015 does not require correction before status approval.

## Non-blocking Risks

- EDS-020.2 may accidentally treat multidimensional characteristics as one
  exclusive state.
- Capability mapping may imply competence from role or ownership.
- Initial source behavior may hide precedence if conflict presentation is not
  explicit.
- Freshness behavior may become one generic time threshold.
- Snapshot selection may capture too much restricted information or too little
  decisive evidence.
- Derived findings may be treated as facts after review without an explicit
  governed standing.
- Interface Commitments may drift into tasks, notifications, or workflow.
- Cross-Workspace search, summaries, or AI retrieval may leak restricted
  source meaning.
- Later historical reuse may ignore Customer, vendor, or commercial
  restrictions.
- Criticality language may drift into an unexplained universal score.

These risks require EDS exclusions, traceable acceptance criteria, and negative
validation. They do not require ADR-015 changes.

## EDS Readiness

**READY AFTER ADR-015 STATUS APPROVAL**

ADR-015 provides sufficient durable architecture for EDS-020.2 to define a
bounded first implementation.

The EDS must:

- resolve all Category 2 questions;
- exclude Category 4 policy decisions unless separately approved;
- preserve all domain dimensions rather than collapsing them;
- map authorization without adding roles or equating ownership with competence;
- define explicit conflict, missing-information, staleness, correction,
  history, and safe-failure behavior for the selected scope;
- define only the minimum Decision Log and Human Review foundation authorized
  by PATCH-020.2;
- prevent Context from absorbing planning, health, AI, memory, documents,
  tasks, workflow, or graph technology;
- include scenario-based and negative validation.

An EDS must not begin until ADR-015 is formally Accepted.

## ADR Status Recommendation

Change ADR-015 status from:

**Proposed — Awaiting Architecture Approval**

to:

**Accepted**

This review recommends the status change but does not perform it.

## Final Verdict

**PASS — ADR-015 IS READY FOR ACCEPTANCE**

Architecture Guardian verdict: **PASS**

Chief Engineering Architect verdict: **PASS**

Blocking issues: **None**

Open Category 1 questions: **None**

Product Bible, ADR-013, and ADR-014 alignment: **Confirmed**

EDS readiness: **Ready after formal ADR acceptance**

ADR-015 remains unchanged and Proposed pending separate approval to update its
status.
