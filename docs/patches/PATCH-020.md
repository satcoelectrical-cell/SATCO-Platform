# PATCH-020 — Engineering Workspace Foundation

## Status

Architecture and Domain Design Complete — Awaiting Approval

## Classification

Product-domain architecture only

## Purpose

PATCH-020 defines the permanent Engineering Workspace Foundation for SATCO
Platform. It establishes the domain architecture required to make Engineering
Workspace the engineer’s primary operational environment within a Project.

This PATCH does not authorize implementation.

## Primary User Story

As an Electrical or Instrumentation Engineer, when I open SATCO in the morning,
I want to immediately understand:

- the most important engineering work today;
- missing engineering information;
- current engineering risks;
- decisions requiring attention;
- pending Human Reviews;
- what AI recommends I examine next;
- why each recommendation exists;
- the AI Confidence associated with it;

so that I can continue engineering work without searching unrelated documents,
folders, chats, or Project data.

The architecture succeeds only if this situation can be understood
conceptually within 30 seconds.

## Engineering Problem

Folder-oriented, document-oriented, task-board-oriented, schedule-oriented,
and chat-oriented products require engineers to reconstruct engineering meaning
from disconnected records.

SATCO must instead begin with:

- current Engineering Context;
- Engineering Workspace state;
- Engineering Health;
- missing inputs;
- open risks;
- pending Human Reviews;
- Engineering Execution Plan position;
- explainable AI Insights;
- Recommended Next Steps.

The engineering problem is not insufficient task tracking. It is insufficient
context, fragmented evidence, hidden dependencies, unclear readiness, and loss
of decision rationale.

## Why AI Is Needed

Future AI is justified where connected Engineering Context is too broad,
dynamic, or multidisciplinary for efficient manual reconstruction.

AI may eventually help:

- identify missing or conflicting information;
- explain engineering implications;
- prioritize Human Reviews;
- suggest relevant standards and historical references;
- estimate uncertainty;
- propose Engineering Execution Plan activities;
- recommend the next engineering review or action.

AI is not needed to replace engineering judgment, approve work, silently change
records, or generate authoritative deliverables.

PATCH-020 creates the governed domain foundation for future AI assistance. It
includes no AI model, prompt execution, algorithm, or provider integration.

## Product Bible Alignment

PATCH-020 applies Product Bible v1.0 as follows:

- **Engineering First:** Every entity must improve engineering understanding,
  readiness, review, risk detection, or decision quality.
- **Engineers Decide:** AI Insights and Recommended Next Steps remain advisory.
- **Context Before AI:** Engineering Context exists independently of prompts
  and model output.
- **Workspace Before Conversation:** Engineering Workspace, not chat, is the
  primary product environment.
- **AI Explains Before It Recommends:** Engineering Reasoning and evidence are
  required.
- **Never Hide Uncertainty:** AI Confidence, missing inputs, conflicts, and
  staleness remain visible.
- **Every Recommendation Must Be Traceable:** Inputs, context, versions,
  reviewer actions, and supersession are preserved.
- **Memory Follows Review:** Only reviewed decisions and outcomes may become
  Engineering Memory.
- **Product Simplicity:** One Workspace per Project and Discipline avoids
  premature hierarchy.

The design conforms to the Constitution, Engineering Philosophy, Product
Vision, Product Principles, AI Behavior Guide, Engineering Knowledge Model,
User Experience Philosophy, AI Feature Framework, and ADR-013.
It advances SATCO as an Engineering Copilot without expanding AI authority.

## Scope

In scope:

- Engineering Workspace domain architecture;
- Engineering Context architecture;
- Engineering Execution Plan architecture;
- Engineering Health and Workspace Readiness;
- AI Insight architecture;
- Recommended Next Step Engine architecture;
- shared Human Review semantics;
- Engineering Decision Log integration;
- relationships and aggregate boundaries;
- lifecycle and state models;
- ownership and preliminary permissions;
- audit and traceability requirements;
- future API, database, and search implications;
- failure and uncertainty behavior;
- implementation decomposition.

## Out of Scope

- backend or frontend source code;
- database schema or migrations;
- API endpoints;
- AI models, prompts, or provider calls;
- vector database or embeddings;
- Knowledge Graph technology;
- workflow engine;
- generic task management;
- calendar, notifications, or Gantt behavior;
- file management or dashboard implementation;
- engineering calculations;
- automatic document generation;
- formal deliverable approval;
- roadmap changes;
- dependency changes;
- production database changes.

## Governing Architecture Decision

The domain model is defined by:

```text
ADR-014 — Engineering Workspace Domain Model
```

ADR-014 remains Proposed until independently approved. No implementation may
begin before its acceptance.

## Domain Definitions

### Engineering Workspace

The canonical definition is established identically in the Engineering
Philosophy, SATCO Product Blueprint, and ADR-014. PATCH-020 adopts that
definition without alteration.

### Engineering Context

The governed combination of authoritative relationships, recorded observations,
derived views, and evidence snapshots needed to understand engineering work.

### Engineering Execution Plan

The Project-level, AI-assisted, engineer-controlled, versioned engineering
roadmap. It is not the Project schedule or an authority to execute work.

### Engineering Health

A set of explainable decision-support indicators describing completeness,
consistency, risk, review, confidence, and readiness.

### Workspace Readiness

A derived, stage-specific indication of whether a Workspace can proceed to a
stated engineering stage or review, including visible blockers and uncertainty.

### AI Insight

A persisted, explainable, traceable, reviewable, and supersedable advisory
recommendation or warning linked to Engineering Context.

### Recommended Next Step

A governed advisory record describing what an engineer should consider
reviewing or doing next, why it matters, its dependencies, alternatives, and AI
Confidence.

### Recommended Next Step Engine

ENSE is the future decision-support capability that creates and ranks
Recommended Next Steps without executing them.

### Human Review

The reusable review lifecycle through which accountable people evaluate
AI-assisted or other reviewable engineering objects.

### Engineering Decision Log

A human-owned, traceable history preserving what was decided, Engineering
Reasoning, alternatives, reviewer decisions, historical evolution, uncertainty,
and affected engineering objects.

## Entity Responsibilities

### Project

- Remains the parent business aggregate.
- Owns Project identity, Customer, lifecycle, owner, and primary assignee.
- Contains discipline Workspaces.
- Owns the current Project-level Engineering Execution Plan.
- Does not duplicate Workspace state.

### Discipline

- Provides a governed engineering-domain identity.
- Supports Electrical, Instrumentation, Control, Mechanical, Civil, Process,
  and future approved disciplines.
- Is not a free-form folder label.

### Engineering Workspace

- Owns Project/Discipline identity.
- Owns accountable owner, primary assignee, and collaborators.
- Owns Workspace Status and archival state.
- Presents connected context, health, readiness, risk, reviews, decisions,
  insights, and plan position.
- Does not own shared engineering objects or formal approval.

### Engineering Context

- Resolves authoritative sources and relationships.
- Exposes freshness, revision, conflicts, and missing data.
- Provides reproducible context for important advice and decisions.
- Avoids duplicating source-of-truth business data.

### Engineering Execution Plan

- Owns immutable versions.
- Owns phases/items and their dependencies.
- Records Human Review and human modifications.
- Links items to relevant Workspaces and engineering objects.
- Preserves superseded history.

### Engineering Health

- Derives transparent indicators.
- Identifies contributing evidence, missing inputs, uncertainty, and freshness.
- Does not declare approval.

### AI Insight

- Preserves advisory content, evidence, assumptions, Engineering Reasoning, AI
  Confidence, review, freshness, and supersession.
- Never mutates authoritative engineering data automatically.

### Recommended Next Step

- States suggested review/action, Engineering Value, blockers, alternatives,
  affected scope, and AI Confidence.
- Records acceptance, rejection, expiry, and supersession.
- Does not become a generic assigned task.

### Human Review

- Applies shared states and evidence requirements.
- Preserves reviewer, authority, comments, rationale, timestamp, and subject
  version.
- Remains distinct from formal Project approval.

### Engineering Decision Log

- Preserves human judgment, Engineering Reasoning, alternatives, reviewer
  decisions, and historical evolution.
- Links to applicable evidence, requirements, standards, risks, and affected
  objects.
- Supports supersession without destructive overwrite.

## Relationships and Aggregate Boundaries

```text
Customer
    └── Project
          ├── Engineering Workspace: Electrical
          ├── Engineering Workspace: Instrumentation
          ├── Engineering Workspace: Control
          ├── Engineering Execution Plan
          │     └── Immutable Versions
          │           └── Phases and Items
          └── Engineering Decision Log

Engineering Workspace
    ├── Engineering Context relationships
    ├── Engineering Health indicators
    ├── Workspace Readiness
    ├── Risks and Engineering Decision Log entries
    ├── AI Insights
    ├── Recommended Next Steps
    └── Human Reviews
```

Cardinality decisions:

- A Project has zero or more Workspaces.
- A Project has at most one Workspace identity per Discipline.
- A Workspace belongs to exactly one Project and one Discipline.
- A Workspace has one owner, zero or one primary assignee, and zero or more
  collaborators.
- A Project has one current Engineering Execution Plan and many historical
  versions.
- Plan items may relate to multiple Workspaces.
- AI Insights and Recommended Next Steps belong to a Project/Workspace context
  and may reference multiple engineering objects.
- Human Review records are subject-specific but follow one shared contract.

Transaction boundaries should align with aggregate ownership. Cross-aggregate
updates require explicit orchestration and audit; no silent cascade is
permitted.

## Workspace Structure Decision

Chosen structure:

> One Engineering Workspace per Project and governed Discipline, with no nested
> Workspaces.

Area, Package, System, Equipment, and Tag scope is represented through
Engineering Context relationships rather than additional Workspaces.

This provides the simplest coherent morning view, preserves discipline
accountability, and prevents folder-tree fragmentation.

## Lifecycle and State Models

### Workspace Status

| Status | Engineering meaning |
|---|---|
| Draft | Identity, scope, ownership, and minimum context are being established |
| Active | Current discipline engineering work is underway |
| On Hold | Work is paused with a recorded reason and unresolved conditions |
| Under Review | Workspace readiness or stage transition is being reviewed |
| Completed | Recorded scope has met its completion conditions |
| Archived | Historical Workspace is retained but no longer operational |

Workspace Status does not summarize Engineering Health or Human Review.

### Human Review State

```text
Suggested
    → Under Review
        → Accepted by Engineer
        → Rejected by Engineer
        → Needs More Information
Any non-final/current state → Superseded
```

Accepted by Engineer is not formal deliverable approval.

### Engineering Execution Plan State

```text
Proposed Draft
    → Under Review
        → Accepted for Engineering Use
        → Rejected
Accepted or Draft Version → Superseded by a newer Version
```

### AI Insight and Recommendation State

An AI Insight or Recommended Next Step is created as Suggested, may enter Human
Review, may be accepted or rejected, may require more information, may expire,
and may be superseded. Its original evidence remains immutable.

## Workspace Readiness Model

Workspace Readiness is derived for an explicit target stage or review.

It considers:

- required and missing inputs;
- unresolved Engineering Decision Log entries;
- open engineering risks;
- required Human Reviews;
- relevant Engineering Execution Plan dependencies;
- current Engineering Context freshness and conflict state;
- AI Confidence where AI-derived evidence contributes.

It must report:

- ready, not ready, or insufficient information in context-appropriate
  language;
- blocking and contributing conditions;
- assessment time;
- source references;
- uncertainty.

No formula or approval meaning is defined.

## Engineering Context Model

### Authoritative Sources

Authoritative context originates from governed Project, Customer, User,
Document, Revision, Standard, Vendor, engineering-object,
Engineering Decision Log, Risk, and review records.

### Derived Information

Current summaries, health indicators, readiness, recommendation ranking, and
similarity findings are derived and must identify their sources and assessment
time.

### Context Snapshots

Snapshots are retained when necessary to reproduce:

- an important AI Insight;
- a Recommended Next Step;
- a Human Review;
- an Engineering Decision Log entry;
- an Engineering Execution Plan version.

Snapshots are evidence, not a competing source of current truth.

### Conflict and Missing Data

Conflicts remain explicit until resolved through Human Review or an
Engineering Decision Log entry. Missing required information is represented
directly. Both reduce AI Confidence and may block readiness.

### Access Boundaries

Context assembly may include only records the current actor is authorized to
use. Derived results must not reveal inaccessible source information.

## Engineering Execution Plan Model

The Engineering Execution Plan is created after sufficient Project context
exists. If essential context is absent, SATCO proposes missing-input actions
instead of fabricating a complete plan.

The Engineering Execution Plan is a living engineering hypothesis. It is not a
contractual schedule. It evolves as engineering knowledge grows and always
remains engineer-controlled.

The plan may represent:

- suggested phases and engineering activities;
- dependencies;
- required inputs and missing information;
- expected deliverables;
- potential risks;
- review points;
- suggested critical engineering path;
- estimated effort;
- suggested team roles;
- Recommended Next Step;
- Engineering Reasoning and AI Confidence;
- historical references.

Duration and effort are estimates, not commitments. No scheduling algorithm or
Gantt logic is part of PATCH-020.

Every accepted, modified, reordered, rejected, added, or removed material item
must be preservable as an Engineering Decision Log entry.

## Engineering Health Model

Initial conceptual indicators:

| Indicator | Meaning | Primary source character |
|---|---|---|
| Engineering Readiness | Ability to proceed toward a stated stage | Derived |
| Data Completeness | Availability of required governed information | Derived |
| Decision Completeness | Required decisions resolved or still open | Derived |
| Missing Inputs | Required information absent or unusable | Persisted findings plus derived view |
| Open Reviews | Required Human Reviews not resolved | Derived |
| Engineering Risks | Current risk exposure requiring attention | Governed records plus derived view |
| Standards Coverage | Known applicability/evidence gaps | Derived with reviewed applicability |
| AI Confidence | Adequacy of context supporting AI output | Derived per AI output |
| Review Readiness | Preparation for a specified review | Derived |
| Documentation Readiness | Required document evidence status | Derived |
| Execution Plan Readiness | Ability to progress through plan dependencies | Derived |

Every indicator requires meaning, evidence, freshness, uncertainty, and Human
Review implications. No universal score or weight is authorized.

Common governance applies to every indicator category:

- the Workspace owner is accountable for ensuring that the indicator’s
  underlying conditions receive appropriate engineering attention;
- authoritative source owners remain responsible for their source records;
- derived values identify assessment time and become stale when material source
  context changes;
- persisted snapshots are evidence only and never replace the current derived
  view;
- uncertainty and missing inputs are displayed with the indicator;
- each indicator links to its contributing and blocking conditions;
- Human Review is required when an indicator informs a consequential stage or
  review decision;
- presentation uses component conditions and explanations, never approval
  language or false precision.

## ENSE Model

ENSE receives governed inputs including:

- Engineering Context;
- Workspace Status and Workspace Readiness;
- Engineering Health;
- Engineering Execution Plan;
- Engineering Knowledge Graph relationships;
- Engineering Memory;
- Human Review states;
- missing inputs and open risks;
- unresolved Engineering Decision Log entries;
- dependencies and Project stage;
- AI Confidence and historical similarity.

Standard conceptual output:

- **Recommendation**
- **Reason**
- **Engineering Impact**
- **Required Inputs**
- **Blocking Dependencies**
- **Confidence**
- **Human Review**

The output may additionally expose Engineering Value, priority, affected
Workspace/object, traceability, alternative next steps, expiry, and
supersession. This is an architectural output model only.

Ranking must remain explainable. ENSE never executes, assigns, approves, or
silently changes engineering work.

## AI Insight Model

Required characteristics:

- typed;
- concise;
- explainable;
- evidence-linked;
- assumption-visible;
- Engineering Context-linked;
- confidence-calibrated;
- reviewable;
- freshness-aware;
- supersedable;
- future provider/model/version traceable.

AI Insights identify Affected Engineering Objects for future Engineering Impact
Analysis. Examples include Equipment, Loop, Cable, Panel, Motor, Document,
Calculation, Engineering Decision Log entry, and Tag. This relationship does
not authorize automatic propagation.

AI Insight priority communicates potential engineering consequence, not
certainty. Severity and AI Confidence remain separate.

## Ownership and Permissions

The preliminary capability model includes Admin, Engineering Manager, Project
Manager, Lead Engineer, Engineer, Reviewer, and Viewer personas.

Current compatibility rule:

- only `admin` and `engineer` exist in implemented RBAC;
- future personas do not authorize new roles in PATCH-020;
- implementation must map initial capabilities through current roles plus
  Project/Workspace ownership and assignment, or obtain separate RBAC approval.

Architectural permission summary:

- Workspace creation: Admin, Engineering Manager, Project Manager, or delegated
  Lead Engineer.
- Activation/archive: Admin or accountable management/lead capability.
- Context editing: authorized owner, assignee, collaborator, or reviewer within
  defined scope.
- Plan recommendation acceptance/rejection: accountable Project/discipline
  authority.
- AI Insight review: authorized engineer or reviewer with subject competence.
- Engineering Decision Log recording: authorized accountable engineer.
- Workspace Status change: owner/lead/manager within transition authority.
- Engineering Health viewing: any actor authorized for the Workspace.
- Engineering Memory access: separately governed by Project, Customer, and
  organizational boundaries.

Permission checks occur before mutation and before search/result disclosure.

## Human Review Boundaries

- AI cannot accept its own output.
- Human Review must identify reviewer authority and subject version.
- Acceptance does not equal formal deliverable approval.
- Review evidence is immutable after completion; corrections supersede it.
- Rejection is preserved with rationale.
- Needs More Information identifies the missing condition.
- Review of one object does not approve connected objects automatically.
- Formal approval workflows remain out of scope.

## AI Interaction Boundaries

Future AI may:

- analyze governed Engineering Context;
- detect missing information and potential conflicts;
- explain implications;
- suggest standards, references, historical similarities, plan items, and next
  steps;
- estimate effort and AI Confidence;
- support Engineering Impact Analysis.

Future AI must not:

- approve engineering work;
- invent facts, standards, vendor data, or Project history;
- silently mutate context or engineering records;
- silently propagate change;
- claim compliance without evidence;
- hide uncertainty;
- treat historical similarity as equivalence;
- turn acceptance into automatic execution.

## Audit and Traceability Requirements

Required future events:

- Workspace created;
- Workspace ownership/assignment changed;
- Workspace Status changed;
- Workspace archived/restored;
- Engineering Context updated;
- context conflict detected/resolved;
- critical missing input detected;
- Engineering Execution Plan proposed;
- plan version modified/accepted/rejected/superseded;
- AI Insight created/reviewed/expired/superseded;
- Recommended Next Step accepted/rejected/expired/superseded;
- Engineering Decision Log entry recorded/superseded;
- material Workspace Readiness change.

The existing centralized Audit Service remains the integration point.
Domain-specific immutable history remains necessary because generic audit
events alone cannot reconstruct plan versions or review evidence.

## Historical Preservation and Deletion

- Workspace archival is preferred over deletion.
- No Workspace history, plan version, review, decision, or AI evidence may be
  cascade-deleted through ordinary Project operations.
- Project hard deletion must be blocked after governed Workspace history
  exists, unless a separately approved destructive retention process applies.
- Existing Project deletion remains unchanged during this architecture phase.
- Superseded records remain available to authorized history views.

## Future API Implications

Potential resource areas:

- Project Workspaces;
- Workspace Context;
- Engineering Execution Plans and Versions;
- Engineering Health and Workspace Readiness;
- AI Insights;
- Recommended Next Steps;
- Human Reviews;
- Engineering Decision Log.

Future APIs require:

- Project/Workspace authorization;
- version conflict protection;
- idempotent creation/review behavior where retry is possible;
- audit after successful domain mutation;
- explicit advisory labels;
- evidence, AI Confidence, freshness, and supersession;
- OpenAPI examples for success and all material failure conditions.

Endpoint paths are intentionally deferred.

## Future Database Implications

Likely persisted entities:

- Discipline reference;
- Engineering Workspace;
- Workspace collaborator membership;
- typed Context relationships and missing-input findings;
- Engineering Execution Plan and immutable versions;
- plan phases/items and dependencies;
- subject-specific Human Review records;
- AI Insights;
- Recommended Next Steps;
- Engineering Decision Log entries;
- evidence snapshots where reproducibility requires them.

Likely derived views:

- current Engineering Context;
- Engineering Health;
- Workspace Readiness;
- current recommendation ranking.

Future design requires foreign keys, uniqueness for Project/Discipline
Workspace identity, lifecycle constraints, timestamps, archival behavior,
version/supersession integrity, and authorization-oriented indexes.

No SQL, schema, table definition, or migration is authorized.

## Future Search Implications

Universal Search may later include:

- Workspace name;
- Discipline;
- Project Code;
- engineering stage;
- missing input;
- risk;
- Engineering Decision Log entry;
- AI Insight;
- Engineering Execution Plan item;
- Human Review state;
- Workspace Status.

Search must remain authenticated, authorization-filtered, type-aware, and
compatible with exact/partial Project Code search. Search relevance must not be
presented as engineering priority.

## Engineering Decision Log Integration

Decision:

> A minimal Engineering Decision Log foundation is required before or with the
> first accepted Engineering Execution Plan version.

The full Engineering Decision Log is a shared future domain, not entirely part
of Workspace Core. PATCH-020.2 should establish the minimum record and
supersession semantics needed for Context and plan decisions.

Rationale:

- plan acceptance and modification must be human-owned;
- decisions need evidence and affected-object relationships;
- embedding decisions only inside plan history would prevent reuse by risks,
  reviews, and Engineering Memory;
- delaying all decision modeling would violate ADR-013 traceability.

## Multidisciplinary Example

### Scenario

A Project includes a new 160 kW process pump. No engineering calculation or
final selection is produced by this example.

### Electrical Engineering Workspace

The Electrical Workspace shows:

- missing Motor Datasheet;
- required Short-Circuit Level;
- a plan item to confirm motor/load inputs before dependent electrical
  selection work;
- an open risk that incomplete source data may affect downstream decisions;
- Workspace Readiness as not ready for the next stated review, with explicit
  blockers;
- an AI Insight labeled **Missing Information — Needs Review**;
- a Recommended Next Step to obtain and verify the Motor Datasheet and
  Short-Circuit Level;
- Engineering Reasoning explaining which downstream objects may depend on
  those inputs;
- low or insufficient AI Confidence for any equipment recommendation.

### Human Review

The responsible Electrical Engineer reviews the Insight. The engineer may:

- accept the missing-input finding;
- reject it with evidence that the input already exists;
- request more information;
- supersede it when a newer revision becomes authoritative.

Acceptance does not approve a breaker, cable, protection setting, or
deliverable.

### Potential Change

If motor power later changes, Engineering Impact Analysis may identify
potential effects on load information, feeder selection, cable sizing,
protection, transformer loading, calculations, documents, and reviews.

SATCO does not update those objects. It creates explainable review
recommendations for the appropriate Workspaces.

### Multidisciplinary Extension

The Instrumentation Workspace may reference the same pump and Motor Datasheet
for control, monitoring, and interface context without copying the Electrical
Workspace. Shared objects connect through Engineering Context while discipline
ownership remains separate.

## Failure and Uncertainty Behavior

| Condition | Safe behavior |
|---|---|
| Required context missing | State Insufficient Information; identify blocker |
| Data conflict | Preserve both sources; request Human Review |
| No similar Project | State no governed analogue found |
| Standards unknown | Do not claim applicability or compliance |
| AI Confidence low | Label clearly and narrow recommendation |
| Recommendations conflict | Show alternatives, evidence, and uncertainty |
| Project stage unclear | Block stage-dependent readiness/recommendation |
| Insight stale | Mark stale or superseded; preserve original |
| Engineer rejects guidance | Preserve rejection and rationale; do not execute |

## Risks

- Implementing too many concepts before Workspace Core proves value.
- Treating derived Engineering Context as duplicated truth.
- Confusing Project and Workspace ownership.
- Confusing status, readiness, health, and review.
- Allowing AI priority to appear authoritative.
- Weak referential integrity from premature universal abstractions.
- Search leakage across Project or Workspace authorization.
- Stale health or recommendation views.
- Unbounded version/history growth.
- Breaking current Project deletion behavior without a controlled transition.

## Alternatives Considered

The following alternatives were evaluated in ADR-014:

1. Workspace as folder tree — rejected.
2. Workspace as Project milestone — rejected.
3. One Workspace per Discipline — accepted.
4. Multiple Workspaces per Discipline — rejected for foundation.
5. Engineering Context entirely as JSON — rejected.
6. Engineering Health as universal score — rejected.
7. ENSE as generic Tasks — rejected.
8. AI Insights only in chat history — rejected.
9. Independent embedded review semantics — rejected.
10. Universal shared Human Review entity — deferred.

## Rejected Designs

PATCH-020 explicitly rejects:

- folder hierarchies as Engineering Workspace;
- task-board or milestone substitution;
- nested Workspaces;
- multiple same-Discipline Workspaces without future ADR;
- one opaque Engineering Health score;
- authoritative or automatically executed AI recommendations;
- chat history as engineering state;
- unstructured JSON as the Engineering Context model;
- automatic cascade deletion of engineering history;
- a generic workflow engine;
- premature universal Human Review infrastructure.

## Rollback and Evolution Strategy

PATCH-020 creates documentation only. Rollback consists of reverting the three
architecture documents before approval.

After approval, evolution must occur through small additive PATCHes. Each
sub-patch must:

- preserve previous API and Project behavior unless explicitly approved;
- use Alembic for schema evolution;
- retain historical records during model changes;
- provide an upgrade and rollback strategy;
- avoid destructive migration of governed engineering evidence;
- update ADR-014 if a foundational decision changes.

## Recommended Implementation Decomposition

### PATCH-020.1 — Engineering Workspace Core

**Purpose:** Workspace identity, governed Discipline, one-per-Project/Discipline
rule, ownership, collaborators, lifecycle, archival, permissions, audit, and
basic authenticated discovery.

**Dependencies:** Project Core, User/RBAC, Audit Service, Alembic.

**Exclusions:** Context intelligence, plan, health, AI, recommendations.

**Migration impact:** New additive Workspace/Discipline/membership persistence.

**API impact:** Conceptual Workspace management and listing.

**Test impact:** Lifecycle, uniqueness, permissions, audit, archival, Project
compatibility, search isolation.

**Acceptance boundary:** An authorized engineer can enter a stable discipline
Workspace with accountable ownership and no folder-tree semantics.

### PATCH-020.2 — Engineering Context, Decision Log, and Human Review Foundation

**Purpose:** Typed contextual relationships, required/missing inputs, conflict
and freshness semantics, minimal Engineering Decision Log entries, and shared
Human Review contract with subject-specific records.

**Dependencies:** PATCH-020.1.

**Exclusions:** AI generation, health formulas, full approval workflow.

**Migration impact:** Additive context, decision, and review persistence.

**API impact:** Context maintenance, missing-input visibility, decisions, and
review actions.

**Test impact:** authority, revision, conflicts, missing data, permissions,
supersession, audit, history.

**Acceptance boundary:** Engineering Context is richer than a prompt and every
human decision/review is traceable.

### PATCH-020.3 — Engineering Execution Plan Foundation

**Purpose:** Project-level plan identity, immutable versions, phases/items,
dependencies, Workspace links, Human Review, and Engineering Decision Log
capture.

**Dependencies:** PATCH-020.2.

**Exclusions:** scheduling algorithms, Gantt, automatic planning model.

**Migration impact:** Versioned plan persistence.

**API impact:** propose, inspect, review, modify through new version, reject,
and supersede.

**Test impact:** version immutability, transitions, authorization, decision
capture, concurrency, audit.

**Acceptance boundary:** A suggested plan can be reviewed and changed without
losing its evidence or becoming authoritative.

### PATCH-020.4 — Engineering Health and Workspace Readiness

**Purpose:** Explainable component indicators and target-stage readiness.

**Dependencies:** PATCH-020.2 and plan inputs from PATCH-020.3 where relevant.

**Exclusions:** universal score, formulas without separate approval, dashboard.

**Migration impact:** Prefer derived views; persist only assessment evidence
required for history.

**API impact:** Read-only health/readiness views plus traceable evidence.

**Test impact:** completeness, freshness, insufficient information,
authorization, non-approval language.

**Acceptance boundary:** An engineer sees why a Workspace is or is not ready.

### PATCH-020.5 — AI Insights Foundation

**Purpose:** Governed AI Insight records using established Context, Human
Review, Engineering Reasoning, AI Confidence, freshness, and supersession.

**Dependencies:** PATCH-020.2 and PATCH-020.4.

**Exclusions:** autonomous changes, generic chatbot, final decisions.

**Migration impact:** Versioned advisory records and evidence references.

**API impact:** inspect, review, reject, request information, expire, supersede.

**Test impact:** traceability, missing context, confidence, model metadata,
permissions, safety language, audit.

**Acceptance boundary:** Every AI Insight is explainable, reviewable, and
non-authoritative.

### PATCH-020.6 — Recommended Next Step Engine Foundation

**Purpose:** Create and rank explainable Recommended Next Steps from governed
Workspace conditions.

**Dependencies:** PATCH-020.3 through PATCH-020.5.

**Exclusions:** task assignment, workflow execution, notifications, scheduling.

**Migration impact:** Advisory recommendation, alternative, expiry, and
supersession persistence.

**API impact:** inspect and review recommendations with evidence and
alternatives.

**Test impact:** ranking explanation, conflicts, staleness, rejection,
authorization, audit, no silent execution.

**Acceptance boundary:** An engineer can identify the highest-value next review
or action and understand why it was recommended.

## Approval Gates

1. Approve ADR-014.
2. Approve PATCH-020 architecture and Architecture Review.
3. Approve each sub-patch implementation plan independently.
4. Approve each migration and database execution separately.
5. Approve dependency or RBAC expansion separately.
6. Complete security, audit, search, API, migration, and PostgreSQL regression
   validation per sub-patch.
7. Do not stage, commit, or push without explicit approval.

## Acceptance Criteria

PATCH-020 architecture is acceptable when:

1. An engineer can conceptually understand current engineering conditions
   within 30 seconds.
2. Highest-priority engineering attention is immediately visible.
3. Every future AI recommendation can expose Engineering Reasoning.
4. Missing engineering information is represented explicitly.
5. Risks and Human Review states remain visible.
6. Engineering Decision Log entries remain human-controlled.
7. Engineering Context is the foundation of AI behavior.
8. Engineering Workspace is the primary product experience.
9. Multidisciplinary Projects are supported without context duplication.
10. Historical evidence cannot be silently destroyed.
11. Existing Project, User, RBAC, Audit, Search, PostgreSQL, and Alembic
    architecture remains compatible.
12. Product Bible v1.0 is satisfied.

## Architecture Validation Questions

| Question | Result |
|---|---|
| Can an engineer understand the situation within 30 seconds? | Yes, through the Workspace summary contract |
| Can highest-priority work be identified? | Yes, through visible blockers, risks, reviews, and Recommended Next Steps |
| Can AI explain every recommendation? | Yes, Engineering Reasoning and evidence are mandatory |
| Can missing information be exposed? | Yes, as governed contextual findings |
| Can uncertainty be shown honestly? | Yes, through AI Confidence and Insufficient Information |
| Can AI output be reviewed, rejected, and superseded? | Yes |
| Does responsibility remain human? | Yes |
| Are Electrical and Instrumentation Workspaces non-duplicative? | Yes, shared objects are related through Context |
| Is Project history traceable? | Yes, through versions, decisions, reviews, and audit |
| Does the design avoid folder/task/chat architecture? | Yes |
| Is every concept Product Bible aligned? | Yes |

## Definition of Done

PATCH-020 architecture and domain design is complete when:

- this PATCH document is complete;
- ADR-014 records the proposed permanent decision;
- the Architecture Review independently tests the design;
- all required concepts, relationships, lifecycles, permissions, boundaries,
  implications, alternatives, risks, and decomposition are documented;
- documentation consistency and `git diff --check` pass;
- no source, database, migration, API, test, roadmap, or Product Bible file is
  modified;
- approval is requested before implementation planning.

## PATCH Status

**ARCHITECTURE COMPLETE — IMPLEMENTATION NOT AUTHORIZED**
