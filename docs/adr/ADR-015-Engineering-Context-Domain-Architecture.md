# ADR-015: Engineering Context Domain Architecture

## Status

Accepted

## Date

2026-07-27

## Context

SATCO is an Engineering Copilot. Its usefulness and safety depend on whether
engineers and future AI capabilities can understand the correct Customer,
Project, Workspace, Discipline, engineering objects, evidence, revisions,
requirements, assumptions, decisions, uncertainty, and history for the work at
hand.

The Constitution requires human engineering responsibility, advisory AI,
visible uncertainty, traceability, and PostgreSQL as the primary structured
source of truth. The Product Bible requires Context before AI, facts distinct
from assumptions, standards with applicability, reviewed decisions distinct
from recommendations, and relationships that preserve engineering meaning.

ADR-013 establishes Context-First AI. ADR-014 establishes Engineering Context
as a governed aggregate view across authoritative relationships, governed
observations, derived views, and selective evidence snapshots. PATCH-020.2
discovery and its architecture review found that durable domain decisions are
still required before an EDS can responsibly define implementation.

This ADR is subordinate to ADR-013 and ADR-014. It refines the Engineering
Context domain without changing the Project or Engineering Workspace decisions
already accepted.

## Problem

Engineering information cannot be understood safely from content alone.

A value without a unit, basis, revision, operating condition, or source may be
misleading. A genuine document may be inapplicable. A high-confidence
interpretation may still lack authority. A prior decision may be authentic
history but unsafe precedent. Shared information may be relevant to several
Disciplines while remaining owned by one qualified source.

Without an explicit domain architecture, later design could:

- force Context into one unstructured object;
- duplicate Project truth in every Workspace;
- mistake ownership for competence;
- mistake confidence for authority;
- hide conflicting sources behind an implicit ranking;
- present stale information as current;
- make AI interpretation authoritative;
- mix raw inputs, decisions, plans, and health indicators;
- capture either too little evidence for traceability or uncontrolled
  snapshots of everything.

The domain needs stable semantic boundaries before technical design begins.

## Decision

Engineering Context is a governed, traceable, multidimensional body of
information needed to understand and perform engineering work inside a Project
and Engineering Workspace.

Context connects authoritative engineering information, reviewed and derived
understanding, historical evidence, unresolved conditions, and reviewable
AI-assisted interpretation. It preserves source, scope, meaning, authority,
time, maturity, uncertainty, access, and human accountability.

Engineering Context does not transfer engineering authority to AI.

The following are binding domain decisions:

1. Context characteristics are dimensions, not one mutually exclusive
   classification.
2. Project Context is shared; Workspace Context is discipline-bounded;
   cross-Workspace Context preserves source and consumer accountability.
3. Authority derives from governed sources and responsible human processes,
   never from confidence or AI origin.
4. Maintenance ownership, technical stewardship, review competence, and
   approval authority are distinct.
5. Source precedence is explicit, contextual, reviewable, and conflict-aware;
   there is no hidden universal ranking.
6. Engineering values remain inseparable from their units, conditions, basis,
   provenance, and uncertainty where those are material.
7. Maturity, review state, and authority are independent meanings.
8. Criticality describes consequence and affects caution without becoming one
   universal score.
9. Freshness is purpose- and source-sensitive; stale evidence remains visible.
10. Material corrections preserve the original and the correction.
11. Snapshots are selective evidence for material events, not routine copies
    after every change.
12. Missing information and conflicts are first-class engineering conditions.
13. Derived and AI-generated Context remain explainable, traceable, and
    non-authoritative unless a governed human process establishes a different
    standing.
14. Interface Commitments express governed dependencies without becoming tasks
    or workflow.
15. In incomplete, stale, conflicted, inaccessible, or unsupported conditions,
    SATCO fails safely and visibly.

## Canonical Definition

> Engineering Context is the governed, traceable, multidimensional body of
> information needed to understand and perform engineering work inside a
> Project and Engineering Workspace.

It connects facts, evidence, relationships, conditions, assumptions, missing
information, conflicts, maturity, history, and reviewable interpretation while
preserving human engineering authority.

Engineering Context is not:

- a single JSON blob;
- a notes field;
- a document repository;
- chat history;
- an AI memory dump;
- a task list;
- an Engineering Execution Plan;
- an Engineering Decision Log;
- an Engineering Health score;
- a Knowledge Graph technology decision.

## Domain Boundaries

### Project

The Project owns shared business and engineering scope: Project identity,
Customer, lifecycle, common accountability, and the collection boundary for
discipline Workspaces. Engineering Context does not duplicate the Project.

### Engineering Workspace

The Workspace owns Project/Discipline identity, accountable ownership,
assignment, collaboration, lifecycle, and archival state. Workspace Context
presents discipline-relevant meaning but does not own shared engineering
objects.

### Engineering Context

Engineering Context resolves and qualifies relevant information across
Project, Workspace, sources, engineering objects, reviews, decisions, and
history. It does not replace those objects or become their universal owner.

### Human decision

Human judgment, rationale, alternatives, resolution, and supersession belong
to the future Engineering Decision Log. Context may expose a decision and its
applicability but does not impersonate it.

### Planning and advisory intelligence

The future Engineering Execution Plan, Engineering Health, Workspace
Readiness, AI Insights, and ENSE consume Context. Their proposals, indicators,
and recommendations are not Context truth.

### History and memory

Historical Context preserves prior engineering understanding. Engineering
Memory is the separately governed reuse of reviewed decisions, outcomes, and
lessons. History does not automatically become Memory.

## Context Dimensions

Context is described across independent dimensions. A single item may occupy
several dimensions simultaneously.

### Authority

Describes why information may be relied upon for a bounded purpose: source
authority, human verification, accepted assumption, unresolved status, or
advisory standing.

### Derivation

Describes whether information comes directly from a source, is calculated or
derived from inputs, or is an AI-assisted interpretation.

### Temporality

Describes whether information is current, future-effective, expired,
superseded, withdrawn, or historical.

### Review state

Describes whether information is unreviewed, needs more information, verified,
rejected, disputed, or superseded for the relevant review purpose.

### Maturity

Describes the development standing of information independently from its
authority or formal approval.

### Freshness

Describes whether information remains sufficiently current for a specific
purpose, stage, dependency state, and criticality.

### Criticality

Describes the consequence of incorrect, missing, stale, or conflicting
information.

### Confidentiality

Describes access and reuse restrictions arising from Project authorization,
Customer or vendor restriction, commercial sensitivity, personal data, or
other governed limits.

### Source

Describes the origin, owner, revision, and evidence from which the information
comes.

### Scope

Describes the Customer, Project, Workspace, Discipline, location, system,
equipment, lifecycle stage, purpose, and other applicability boundaries.

For example, a vendor datasheet value may simultaneously be vendor-authoritative
for supplied performance, engineer-verified for a bounded use, high criticality,
restricted, stale after a revision, and historical after supersession.

No dimension silently determines another.

## Scope Boundaries

### Project Context

Project Context contains meaning shared across Workspaces, including:

- Customer;
- plant, site, unit, and area;
- Project scope and exclusions;
- shared Project stage;
- Customer requirements;
- Project-wide standards applicability;
- common operating or design basis;
- global constraints;
- shared risks, changes, and cross-discipline conditions.

Project facts are referenced by Workspaces rather than copied as independent
truth.

### Engineering Workspace Context

Workspace Context contains discipline-bounded meaning, including:

- discipline inputs and outputs;
- discipline scope and exclusions;
- assumptions and open questions;
- standards application within the Discipline;
- missing information and conflicts;
- interface commitments;
- discipline risks and dependencies;
- discipline-specific vendor evidence;
- discipline maturity and review conditions.

### Cross-Workspace Context

Cross-Workspace Context connects shared objects and commitments while
preserving:

- source Workspace or source authority;
- consuming Workspace;
- steward and reviewer;
- original source and revision;
- visibility;
- supersession;
- unresolved conflict;
- change impact.

Cross-Workspace relevance does not transfer technical ownership.

### Future object-level Context

Future engineering objects may have their own bounded Context, such as an
equipment item, tag, document revision, calculation, or interface. This ADR
recognizes the domain need but does not decide the first implementation set.

### Historical Context

Historical Context preserves prior understanding with its original scope,
authority, time, source, review, and supersession meaning. It is never displayed
as current without explicit historical labeling.

## Authority Model

Authority is the governed standing that permits information to support
engineering work for a defined scope and purpose. Authority is not confidence,
fluency, recency alone, ownership alone, or frequency in historical data.

### Authoritative Fact

A fact supported by a governed source or responsible process for the stated
scope. Its authority may be limited to source, purpose, revision, condition,
and effective period.

### Engineer-Verified Fact

Information a qualified, authorized engineer has checked against suitable
evidence for bounded engineering use. Verification does not necessarily equal
formal document approval.

### Assumption

An explicit provisional basis adopted by a human for a bounded purpose.
Assumptions identify owner, scope, consequence, evidence gap, review need, and
conditions for confirmation or rejection.

### Derived Finding

An explainable conclusion produced from identified inputs. It remains
non-authoritative unless an authorized human process explicitly establishes
its governed standing.

### AI Suggestion

Advisory machine-generated interpretation. AI origin never supplies
engineering authority.

### Historical Reference

Authentic prior evidence presented with its original context and reuse limits.
It may inform but does not govern current work automatically.

### Unresolved Conflict

Two or more materially inconsistent governed claims preserved together until
responsible review or decision resolves their current applicability.

### Missing Information

An engineering condition stating that required meaning is absent, incomplete,
unknown, inaccessible, or unreviewed.

Only governed human or source-based processes may elevate authority. Review and
authority changes remain traceable.

## Ownership and Stewardship

### Information owner

Accountable for maintenance, availability, and controlled change of the
information. Maintenance ownership is not proof of technical competence.

### Engineering steward

Qualified for the engineering meaning, applicability, completeness, and
quality of information within a defined scope.

### Reviewer

Evaluates information and evidence within authorized competence and records a
review outcome.

### Approver

Where a separate governed approval process applies, the person or authority
permitted to approve that specific subject. Approval of one subject does not
approve connected subjects.

### Source owner

Owns the originating source and its revision or issue process. Source ownership
does not guarantee applicability to every Project or purpose.

### Workspace responsibility

The Workspace owner is accountable for discipline Context relevance and
coordination. The primary assignee maintains working understanding within
delegated scope. Collaborators contribute within authorization.

### Project responsibility

The Project owner is accountable for shared Project Context and
cross-discipline coordination, without becoming technical authority for every
Discipline.

Competence, authorization, ownership, stewardship, review, and approval are
separate. Future capability mapping must preserve those distinctions while
remaining compatible with current roles.

## Source and Precedence

Potential source kinds include:

- Customer document;
- contract;
- approved Project document;
- vendor document;
- site survey;
- standard;
- calculation;
- engineer input;
- external reference;
- historical Project;
- AI-derived interpretation.

Source kind alone does not establish universal precedence.

Precedence is:

- explicit;
- domain-sensitive;
- purpose- and scope-sensitive;
- reviewable;
- traceable;
- capable of representing unresolved conflict.

Contractual precedence, Customer direction, approved Project basis, technical
competence, standard applicability, revision, and effective time may all
matter. Their meaning varies by engineering question.

A higher-precedence source does not erase a lower-precedence source. Competing
claims remain visible with their scope and evidence until responsible human
resolution. No hidden ranking may silently select a winner.

## Value and Unit Semantics

An engineering value is meaningful only with the semantic information required
to interpret it safely.

Depending on the quantity and purpose, that information may include:

- value;
- unit;
- quantity type;
- tolerance;
- acceptable or observed range;
- calculation or measurement basis;
- reference condition;
- normal, design, minimum, or maximum condition;
- source and source owner;
- revision;
- observation or effective timestamp;
- uncertainty.

Voltage, pressure, temperature, flow, motor power, cable size, design
temperature, and operating pressure cannot be detached from their engineering
meaning.

This ADR does not define a universal measurement representation. It establishes
the architectural requirement that Context must not reduce engineering values
to unqualified numbers.

## Information Maturity

Maturity describes how developed and ready information is for its intended use.
It is independent from authority, review state, and formal approval.

Conceptual maturity language may include:

- Preliminary;
- In Development;
- Verified;
- Approved for Use;
- Superseded;
- Historical.

These terms establish meaning, not implementation enums or one mandatory
lifecycle.

A preliminary source may still be authentically vendor-supplied. A mature
calculation may be inapplicable after its input changes. Verified information
may not be formally approved. Approved information may later be superseded.

AI cannot promote maturity. Material maturity transitions require human or
governed source authority and traceability. Maturity may differ across
Disciplines because one shared input may be sufficient for one purpose and
incomplete for another.

## Criticality

Context criticality is the consequence of information being incorrect,
missing, stale, conflicting, misunderstood, or inaccessible.

Conceptual levels may include:

- Informational;
- Important;
- High Impact;
- Safety Critical.

Criticality affects review priority, visibility, freshness expectations, audit
significance, snapshot justification, and AI caution.

Criticality does not authorize AI, does not determine truth, and is not one
universal score. Its assessment must be explainable and sensitive to scope,
purpose, lifecycle, and affected engineering work.

## Freshness and Staleness

### Freshness

Whether information is current enough for its specific source type, purpose,
Project stage, revision, criticality, and dependent work.

### Review-by date

A human-governed time by which continued use requires review. It is not
appropriate or required for every Context item.

### Expiry

A known point or condition after which information may no longer support its
intended current use without renewed authority.

### Stale state

A visible condition indicating that the current-use basis is no longer
sufficient or has not been reassessed after a material trigger.

### Revision supersession

A later governed revision replaces an earlier revision for stated current use
while preserving the earlier revision as history.

### Event-triggered invalidation

A change in a dependency, Project stage, operating condition, governing
requirement, interface commitment, or decision can invalidate a Context
conclusion even when no time limit has elapsed.

### Context-dependent validity

The same evidence may remain valid for one purpose and stale for another.

There is no universal expiry duration. Stale information remains visible with
its source, prior use, and reason for staleness. It is never silently deleted
or presented as current.

## Correction Semantics

Corrections preserve truth and history without treating every change alike.

### Correctable metadata

Non-material descriptive errors may be corrected under governed change control
when the correction does not alter engineering meaning. The fact and actor of
correction remain traceable where needed.

### Immutable historical evidence

Evidence of what was issued, reviewed, decided, or used at a material time is
not rewritten.

### Superseding record

A new governed state replaces an earlier state for current use while preserving
the earlier state and its original meaning.

### Withdrawn information

Information deliberately removed from current reliance, with reason and
authority preserved.

### Corrected information

A stated replacement for erroneous information. Material corrections preserve:

- original value;
- corrected value;
- reason;
- actor;
- timestamp;
- source;
- affected objects;
- review outcome.

### Disputed information

Information whose correctness, interpretation, or applicability remains
contested. Dispute is visible and does not imply a chosen winner.

Engineering history is never silently rewritten.

## Snapshot Semantics

A Context snapshot is a selective, immutable evidence frame used to reproduce
the basis of a material event.

Snapshots may be justified for:

- formal review;
- engineering decision evidence;
- Engineering Execution Plan generation basis;
- a material AI recommendation;
- milestone or stage transition;
- audit or dispute resolution.

A snapshot preserves only the decisive or required evidence, its relationships,
scope, revisions, known missing information, conflicts, and assessment time.

Snapshotting after every change is rejected. Snapshots require an explainable
trigger, bounded purpose, authorization, confidentiality treatment, and
retention governance. They are historical evidence, not a competing current
source and not a mechanism for uncontrolled copying.

## Historical Context

Historical Context is preserved evidence of prior engineering understanding.

It may include:

- superseded facts;
- previous revisions;
- prior assumptions;
- resolved conflicts;
- previous Customer requirements;
- past vendor data;
- previous AI suggestions;
- prior engineer decisions;
- reviewed lessons learned references.

Historical Context retains original source, scope, maturity, review, authority,
time, and supersession. It must never be presented as current without clear
labeling.

History may support comparison, audit, dispute resolution, Engineering Memory,
or explanation. Reuse requires current applicability review.

## Derived Context

Derived Context is information produced from identified authoritative or
reviewed inputs.

Examples include:

- detected missing input;
- identified conflict;
- readiness implication;
- cross-discipline dependency;
- stale-data warning;
- calculated relationship;
- review priority.

Derived Context is:

- explainable;
- traceable to inputs;
- reproducible where possible;
- explicit about method and assumptions where material;
- freshness-aware;
- scoped;
- non-authoritative unless reviewed and explicitly given a governed standing.

When an input changes, the derivation is reassessed or marked stale. A reviewed
derived finding does not silently change its sources.

## AI-generated Context

AI-generated Context is advisory interpretation produced with AI assistance.

AI may:

- identify possible missing information;
- summarize sources;
- detect potential conflicts;
- suggest relationships;
- identify historical similarity;
- propose questions;
- estimate confidence;
- recommend review.

AI must not:

- silently create authoritative facts;
- change approved Context;
- hide uncertainty;
- invent sources, standards, vendor data, or Project history;
- merge conflicting information without review;
- promote maturity, authority, or approval state;
- erase historical evidence;
- expose inaccessible source information through derived output.

AI-generated Context identifies the evidence, scope, assumptions, limitations,
confidence basis, model provenance where material, and assessment time.

Human Review is required wherever the output may affect engineering action.
Review may accept a finding for bounded use, but it does not make AI the owner
or authority.

## Interface Commitments

An Interface Commitment is a governed cross-discipline or external dependency
in which one party must provide information needed by another.

Examples include:

- Electrical requires confirmed motor power from Mechanical;
- Instrumentation requires process conditions from Process;
- Civil requires equipment loads from Mechanical;
- Control requires final IO count from Instrumentation;
- verified vendor data is required before protection settings are finalized.

An Interface Commitment conceptually identifies:

- provider;
- consumer;
- required information and semantic completeness;
- due condition or engineering stage;
- status;
- source;
- criticality;
- steward and review responsibility;
- change impact.

An Interface Commitment is not a task, workflow, notification, schedule, or
automatic transfer of authority. Fulfilment means suitable governed information
was provided; it does not approve the consumer’s engineering conclusion.

## Confidentiality

Context access and reuse may depend on:

- Project authorization;
- Workspace membership;
- current role and capability;
- source confidentiality;
- commercial sensitivity;
- personal data;
- vendor restrictions;
- Customer restrictions;
- historical reuse constraints.

Cross-Workspace access follows least privilege. Source restrictions remain
attached to derived views, snapshots, AI retrieval, historical Context, search,
and reuse.

Search, AI, summaries, counts, and derived findings must not reveal inaccessible
source information. This ADR does not create a new RBAC system.

## Human Review

Context review evaluates a defined subject, evidence basis, version, scope, and
review question through authorized human competence.

Conceptual outcomes may include:

- Unreviewed;
- Needs More Information;
- Verified by Engineer;
- Rejected;
- Superseded;
- Disputed.

These outcomes align with ADR-014’s shared Human Review semantics but do not
define a universal review entity.

Review standing is distinct from maturity, authority, confidence, and formal
deliverable approval. A review of one Context item does not approve connected
items automatically.

AI cannot review or accept its own output. Completed review evidence remains
attributed and historically preserved; later correction or reconsideration
supersedes rather than silently rewrites it.

## Conflict Handling

A Context conflict exists when governed sources, facts, interpretations, or
applicability claims disagree materially for the same engineering purpose.

A conflict preserves:

- all competing values or claims;
- source references and revisions;
- affected scope and objects;
- criticality;
- owner and steward;
- review state;
- current limitations;
- resolution when reached;
- future Engineering Decision Log reference where material;
- historical evidence.

Source precedence may inform review but never resolves a conflict silently.
Until resolved, SATCO states **Conflict Requires Review** and limits dependent
conclusions appropriately.

Resolution is human-owned. It may establish current applicability without
erasing authentic competing evidence.

## Missing Information

Missing Information is a first-class engineering condition stating that
required information is absent or unusable for an identified purpose.

It may include:

- required input absent;
- source unavailable;
- value incomplete;
- unit or reference condition missing;
- revision unknown;
- owner unknown;
- review incomplete;
- interface commitment unmet;
- inaccessible evidence;
- required applicability not established.

Missing Information is not equivalent to a null value. It has a requirement
basis, affected scope, owner where known, criticality, consequence, review
need, and condition for resolution.

Missing Information may block later work. SATCO identifies the blockage rather
than inventing or silently defaulting the missing meaning.

## Lifecycle

Different Context types follow different lifecycle subsets. No universal
lifecycle is imposed.

Conceptual lifecycle meanings include:

- **Identified:** recognized as potentially relevant;
- **Recorded:** captured with source and scope;
- **Reviewed:** evaluated by an authorized reviewer;
- **Verified:** accepted by a qualified engineer for bounded use;
- **Superseded:** replaced for current use by a later governed state;
- **Archived:** retained outside normal current work;
- **Disputed:** actively contested;
- **Withdrawn:** deliberately removed from current reliance.

Maturity, review, authority, freshness, correction, and temporality remain
separate dimensions even when lifecycle language references them.

Transitions that materially change engineering meaning are human- or
source-governed and traceable. AI cannot self-transition Context into verified,
approved, or authoritative standing.

## Audit and Traceability

Every material Context change is attributable and reconstructable.

Material events may include:

- Context created;
- value changed;
- source changed;
- maturity changed;
- review completed;
- conflict identified or resolved;
- information superseded;
- correction recorded;
- confidentiality changed;
- AI suggestion created or reviewed;
- snapshot captured.

Traceability identifies actor, time, Project and Workspace scope, subject,
source, before and after meaning where applicable, rationale, review outcome,
and affected objects without exposing restricted content unnecessarily.

No silent mutation is permitted. Generic audit evidence does not replace
domain-specific revision, correction, review, snapshot, or decision history.

## Cross-discipline Accountability

Shared information remains singular in engineering meaning while its use is
visible across Workspaces.

Cross-discipline Context preserves:

- originating source or source Workspace;
- consuming Workspace;
- information owner;
- engineering steward;
- reviewer and competence boundary;
- Interface Commitment;
- visibility and confidentiality;
- current and superseded revisions;
- change impact;
- unresolved conflict.

A consumer may interpret shared information for its Discipline but cannot
silently alter the source or declare another Discipline’s commitment fulfilled.
Changes do not copy automatically across Workspaces. They create visible
reassessment and review needs.

## Relationship to Future Domains

### Engineering Decision Log

Records why a human decision was made, by whom, from which evidence,
assumptions, alternatives, uncertainty, and affected scope. Context exposes
decisions as relevant evidence but does not replace the Log.

### Engineering Execution Plan

Uses Context as planning input. Suggested phases, activities, dependencies,
deliverables, effort, roles, and next steps remain plan hypotheses rather than
Context facts.

### Engineering Health and Workspace Readiness

Derive explainable indicators and blockers from Context. They do not replace
Context, declare formal approval, or become authoritative evidence about their
own inputs.

### AI Insights

Produce advisory findings linked to the exact Context considered. Insights do
not own or modify source Context.

### ENSE

Uses Context to recommend possible next actions. It does not execute those
actions or convert recommendations into facts, decisions, or tasks.

### Engineering Memory

Preserves reusable reviewed experience with original context, outcomes,
authority, and reuse limits. Unreviewed Context and AI output do not become
trusted Memory.

### Engineering Knowledge Graph

Connects Context relationships conceptually. This ADR requires relationship
meaning but neither requires graph technology nor places Knowledge Graph
implementation inside PATCH-020.2.

### Documents

Act as sources and evidence. Documents and revisions remain governed objects;
they are not the Context model itself.

## Safe Failure Behavior

When Context is incomplete, conflicted, stale, inaccessible, unsupported, or
outside the actor’s authorization, SATCO prefers explicit bounded outcomes:

- **Insufficient Information**
- **Conflict Requires Review**
- **Source Not Available**
- **Context Is Stale**
- **Access Restricted**

SATCO narrows or refuses conclusions rather than:

- inventing information;
- silently choosing a source;
- substituting history for current evidence;
- carrying assumptions across scope;
- hiding access limitations;
- presenting advice as approval.

Safe failure identifies the limiting condition, affected scope, consequence,
and responsible review or information need where known.

## Electrical Scenario

A Project introduces a new 160 kW process pump. No engineering calculation or
equipment selection is made here.

### Project Context

The Customer, plant, area, common Project scope, overall supply basis, shared
Customer requirements, and Project stage are Project Context.

### Electrical Workspace Context

The Electrical Workspace needs the pump and motor identity, confirmed motor
power source, voltage basis, operating duty, starting information,
short-circuit-level requirement, Customer electrical standard, installation
conditions, and related electrical evidence.

### Interface and missing information

Mechanical is the provider and Electrical the consumer of confirmed motor
power and motor datasheet information. This is an Interface Commitment, not a
task.

The vendor datasheet is missing. The short-circuit level is a required input
whose current source must be established. SATCO reports **Insufficient
Information** rather than inventing either.

### Revision, staleness, and conflict

An earlier motor schedule lists 160 kW, but a newer Mechanical revision changes
the value. The earlier revision becomes historical and any dependent
Electrical derivation is marked stale. Both revisions remain traceable.

If a Customer standard and approved Project basis appear to conflict, both
remain visible until qualified review establishes applicability.

### AI and human authority

AI may flag the missing datasheet, stale derivations, source conflict, and
potentially affected electrical work. It may suggest review questions.

The Electrical engineer verifies the governing voltage and short-circuit
source and records bounded engineering use. AI cannot verify these facts,
select equipment, claim compliance, or fulfil the Mechanical commitment.

### Correction and supersession

If the motor value was recorded incorrectly rather than revised by design, the
correction preserves original value, corrected value, reason, actor, source,
time, affected objects, and review. If the design legitimately changed, the
new revision supersedes the old for current use instead of rewriting history.

## Instrumentation Scenario

A Project requires a flowmeter with pressure and temperature compensation. No
calculation, sizing, or equipment selection is made here.

### Project and Workspace Context

Project Context includes Customer, plant, process unit, shared Project basis,
Customer requirements, and stage. Instrumentation Workspace Context includes
measurement purpose, process fluid, tag, operating and design conditions,
required accuracy, interfaces, vendor evidence, and discipline review state.

### Sources and value meaning

Process supplies fluid identity, operating pressure, operating temperature,
design conditions, and reference basis. Each value requires its unit,
condition, source, revision, timestamp where material, and uncertainty.

Vendor meter data is authoritative only for the vendor’s stated product and
conditions. The compensation-equation reference is evidence whose
applicability requires qualified review.

### Missing and conflicting Context

The reference condition is missing. Two governed sources provide materially
different operating pressure values. Missing reference condition is not a null;
it is a blocking engineering condition. The pressure conflict retains both
values, sources, revisions, scope, and criticality.

### Criticality and Interface Commitments

Process is provider and Instrumentation is consumer for confirmed fluid and
operating conditions. The importance of compensation makes incorrect or stale
conditions potentially high impact, increasing review priority and AI caution
without invoking a universal score.

### AI and Human Review

AI may warn that the reference condition is missing, identify the pressure
conflict, summarize vendor limits, and recommend Process and Instrumentation
review. It may not invent a reference condition, merge the pressure values,
choose a meter, or claim performance.

Qualified engineers review the sources, establish the accepted bounded basis,
and preserve any material resolution through future decision evidence.

### Historical preservation

Superseded process revisions, vendor data, prior AI warnings, review evidence,
and the resolved conflict remain historical. They are clearly labeled and do
not appear as current Context.

## Alternatives Considered

### One large Context JSON object

**Advantages:** Flexible, initially quick to collect, easy to pass as one
payload.

**Risks:** Hides authority and relationships, weakens validation and conflict
semantics, encourages duplication, and makes history difficult to govern.

**Product Bible alignment:** Conflicts with traceability, governed
relationships, and Context before AI.

**Decision:** Rejected.

### Document-only Context

**Advantages:** Familiar to engineers and reuses existing evidence.

**Risks:** Makes files the domain model, obscures cross-document meaning, and
cannot represent missing information, interfaces, decisions, or applicability
reliably.

**Product Bible alignment:** Conflicts with relationship-first knowledge.

**Decision:** Rejected.

### Chat-history Context

**Advantages:** Captures conversational flow and is simple for AI interaction.

**Risks:** Ephemeral, user-dependent, ungoverned, incomplete, and detached from
authoritative engineering state.

**Product Bible alignment:** Conflicts with Workspace Before Conversation.

**Decision:** Rejected.

### AI-managed Context

**Advantages:** Reduces manual curation and can surface relationships quickly.

**Risks:** Transfers authority to AI, permits silent mutation, and may invent
or conceal uncertainty.

**Product Bible alignment:** Directly conflicts with human responsibility.

**Decision:** Rejected. AI assistance remains advisory.

### One universal lifecycle

**Advantages:** Consistent labels and simpler administration.

**Risks:** Conflates source, review, maturity, temporality, and dispute
semantics across unlike information.

**Product Bible alignment:** Apparent simplicity would hide engineering
meaning.

**Decision:** Rejected. Context types use appropriate lifecycle subsets.

### One universal freshness rule

**Advantages:** Easy to understand and enforce.

**Risks:** Treats durable decisions and volatile vendor or operating data as if
they age identically.

**Product Bible alignment:** Conflicts with context-sensitive engineering.

**Decision:** Rejected.

### Hidden source precedence

**Advantages:** Produces one answer with less review effort.

**Risks:** Suppresses legitimate conflict, hides assumptions, and makes the
result untraceable.

**Product Bible alignment:** Conflicts with Never Hide Uncertainty.

**Decision:** Rejected. Precedence is explicit and reviewable.

### Full snapshot after every change

**Advantages:** Maximum apparent reproducibility.

**Risks:** Uncontrolled duplication, confidentiality exposure, storage growth,
and ambiguity about decisive evidence.

**Product Bible alignment:** Traceability is served, but proportionality and
governance are not.

**Decision:** Rejected. Snapshots are selective and justified.

### Copying Project facts into every Workspace

**Advantages:** Local convenience and independent Workspace views.

**Risks:** Divergent truth, stale copies, unclear ownership, and
cross-discipline inconsistency.

**Product Bible alignment:** Conflicts with single source of truth.

**Decision:** Rejected.

### Premature Knowledge Graph implementation

**Advantages:** May provide sophisticated relationship traversal early.

**Risks:** Selects technology before domain meaning and minimum value are
approved.

**Product Bible alignment:** Relationship meaning aligns; premature technology
does not.

**Decision:** Rejected for PATCH-020.2 architecture. Relationships remain
technology-independent.

### Treating NULL as Missing Information

**Advantages:** Minimal conceptual overhead.

**Risks:** Cannot express requirement basis, consequence, owner, criticality,
or resolution.

**Product Bible alignment:** Conflicts with Missing Information Is a Result.

**Decision:** Rejected.

### Treating confidence as authority

**Advantages:** Allows fast automatic acceptance of apparently reliable output.

**Risks:** Confuses statistical certainty with evidence, competence,
applicability, and approval.

**Product Bible alignment:** Direct conflict.

**Decision:** Rejected.

### Treating ownership as engineering competence

**Advantages:** Simple permission and responsibility model.

**Risks:** Allows maintenance responsibility to be mistaken for qualified
technical authority.

**Product Bible alignment:** Conflicts with permanent human engineering
responsibility.

**Decision:** Rejected.

## Consequences

### Positive

- Context retains engineering meaning across source, scope, time, maturity,
  review, and history.
- Project and Workspace truth are not duplicated.
- AI can assist without gaining authority.
- Conflicts and missing information remain visible.
- Engineering values remain semantically qualified.
- Cross-discipline dependencies become explicit without becoming workflows.
- Future decisions, plans, health, insights, and memory receive a stable input
  boundary.
- History supports reproducibility without requiring indiscriminate snapshots.

### Negative

- Context is more complex than a notes field or one document collection.
- Human stewardship and review remain necessary.
- Different Context types cannot share one simplistic lifecycle or expiry rule.
- Source conflicts may remain unresolved rather than yielding an immediate
  single answer.
- Selective snapshots require judgment and governance.
- Later implementation will need careful authorization and traceability
  validation.

## Risks

- Dimension combinations may become inconsistent without a later coherent
  domain contract.
- Excessive Context collection may create noise and distract engineering
  attention.
- Under-qualified owners may be treated as approvers despite this ADR.
- Source precedence rules may become hidden inside later behavior.
- Criticality labels may drift into unexplained scoring.
- Staleness may be ignored if dependency changes are not recognized.
- Snapshot boundaries may either omit decisive evidence or retain excessive
  restricted information.
- Cross-Workspace visibility may leak Customer, vendor, commercial, or
  discipline-restricted information.
- Derived findings may be treated as facts merely because they were reviewed.
- Interface Commitments may drift into task or workflow management.
- Historical similarity may be mistaken for current applicability.

Mitigation requires explicit EDS traceability back to this ADR, negative
authorization and AI-boundary tests, Architecture Guardian review, and
preservation of unresolved uncertainty.

## Open Architectural Questions

This ADR resolves the durable semantic model. The following bounded questions
remain for approved downstream design and must not be answered silently:

1. Which Project-, Workspace-, interface-, and object-level Context concepts
   form the minimum coherent PATCH-020.2 implementation boundary?
2. Which domain-specific source-precedence rules require separate approval,
   and who is competent to apply them?
3. How will current `admin` and `engineer` roles express stewardship, review,
   and decision responsibility without implying competence from role alone?
4. Which criticality assessments require independent Human Review?
5. Which dependency changes make each Context kind stale?
6. Which material events require a snapshot, and what decisive evidence is
   sufficient for each?
7. Which retention and confidentiality rules apply to snapshots, disputes,
   withdrawn information, and cross-Customer historical reuse?
8. What minimum Human Review and Engineering Decision Log foundations are
   required for conflict resolution and governed promotion of derived findings?
9. Which Interface Commitments belong to the first bounded release without
   introducing workflow or task behavior?

These questions may be narrowed by a future EDS only after ADR-015 is accepted
and PATCH scope is separately approved.

## Compatibility

This decision is compatible with:

- the Constitution and Product Bible;
- accepted ADR-013 Context-First AI;
- accepted ADR-014 aggregate boundaries;
- PATCH-020 decomposition;
- PATCH-020.1 Project/Discipline Workspace identity, accountability,
  lifecycle, authorization, search, audit, and history;
- current `admin` and `engineer` roles.

It does not add roles, alter Project or Workspace ownership, authorize a
database change, or modify existing behavior.

## Future Evolution

Future approved architecture may extend Context to additional engineering
objects, formal source taxonomies, richer multidisciplinary interfaces,
Engineering Memory reuse, and governed impact analysis.

Evolution must preserve:

- multidimensional meaning;
- source and scope boundaries;
- human authority;
- explicit conflict and missing information;
- historical preservation;
- least-privilege access;
- technology independence at the domain level.

Any future Knowledge Graph technology, measurement architecture, workflow,
approval process, or specialized role model requires its own applicable
governance and cannot be inferred from this ADR.

## Approval Requirement

ADR-015 is Proposed and does not authorize implementation.

Before an EDS or implementation may proceed:

1. Architecture Guardian review must confirm Foundation v1.0, ADR-013, and
   ADR-014 alignment.
2. Chief Engineering Architect review must confirm real engineering
   sufficiency, human competence boundaries, value semantics, source conflict,
   and cross-discipline accountability.
3. Product governance must confirm that the domain remains Workspace-first,
   Context-first, reviewable, and bounded.
4. Any unresolved conflict with higher governance must be resolved explicitly.
5. ADR-015 must be accepted through the SATCO governance process.

No source code, database, migration, API, schema, repository, service, EDS, or
PATCH implementation is authorized by this Proposed decision.
