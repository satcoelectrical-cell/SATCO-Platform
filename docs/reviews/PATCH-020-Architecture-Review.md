# PATCH-020 Architecture Review

## Review Status

Architecture Review Complete — Approval Recommended With Recorded Gates

## Review Scope

This review evaluates the architecture and domain design for PATCH-020 only.
It reviews no implementation because PATCH-020 authorizes no source code,
schema, migration, API, AI integration, or runtime change.

## Documents Reviewed

### Product Governance

- `docs/00_Constitution.md`
- `docs/17_SATCO_Product_Blueprint.md`
- `docs/10_Engineering_Philosophy.md`
- `docs/11_Product_Vision.md`
- `docs/12_Product_Principles.md`
- `docs/13_AI_Behavior_Guide.md`
- `docs/14_Engineering_Knowledge_Model.md`
- `docs/15_User_Experience_Philosophy.md`
- `docs/16_AI_Feature_Framework.md`
- `docs/adr/ADR-013-AI-Engineering-Copilot-Architecture.md`

### Platform Governance and Architecture

- `docs/01_Architecture.md`
- `docs/02_Roadmap.md`
- `docs/06_Database_Blueprint.md`
- `docs/07_Backend_Blueprint.md`
- `docs/09_Codex_Guidelines.md`
- ADR-008 through ADR-012 where relevant to RBAC, audit, Project Core, and
  Alembic ownership.

### Existing Implementation Inspected Read-Only

- Project model, enums, schemas, repository, service, router, and tests;
- User model and current `admin`/`engineer` roles;
- centralized Audit Service, repository, router, and audit schema;
- authenticated Universal Search repository, service, router, schema, and
  tests;
- Project permission tests and Project Code search behavior.

## Product Bible Alignment

| Product Bible rule | PATCH-020 response | Result |
|---|---|---|
| Engineering First | Workspace centers engineering context, risk, review, decisions, and readiness | Aligned |
| Engineers Decide | AI output is advisory and cannot approve or execute | Aligned |
| Context Before AI | Engineering Context is governed independently of prompts | Aligned |
| Workspace Before Conversation | Workspace is the primary operational environment | Aligned |
| AI Explains Before It Recommends | Engineering Reasoning and evidence are mandatory | Aligned |
| Never Invent Facts | Insufficient Information is preferred | Aligned |
| Never Hide Uncertainty | AI Confidence, missing data, conflict, and staleness are explicit | Aligned |
| Every Recommendation Traceable | Context, evidence, version, review, and supersession are retained | Aligned |
| Memory Follows Review | Only reviewed decisions/outcomes may become Engineering Memory | Aligned |
| Simplicity Over Premature Complexity | One Workspace per Project and Discipline; no nesting | Aligned |

No Product Bible conflict was found.

## Architecture Summary

The proposed architecture establishes:

1. Engineering Workspace as a Project child aggregate with discipline identity,
   accountable ownership, collaboration, lifecycle, and archival.
2. One Workspace per Project and Discipline.
3. Engineering Context as persisted typed relationships plus derived views and
   selective immutable evidence snapshots.
4. One Project-level Engineering Execution Plan with immutable versions and
   Workspace-linked phases/items.
5. Engineering Health as transparent component indicators.
6. Workspace Readiness as a derived, target-stage-specific condition.
7. AI Insights as persisted, reviewable, freshness-aware advisory records.
8. ENSE as an explainable recommendation capability, not task management.
9. Shared Human Review semantics implemented initially through
   subject-specific records.
10. Minimal Engineering Decision Log foundation before plan acceptance.
11. Audit, versioning, supersession, and archival as permanent history rules.

Together these boundaries extend SATCO as an Engineering Copilot while keeping
engineering authority entirely human.

## Primary User Story Validation

### Required Morning View

The proposed Workspace can conceptually expose:

- active Project and Discipline context;
- Workspace Status and target-stage readiness;
- missing and conflicting inputs;
- open engineering risks;
- unresolved Engineering Decision Log entries;
- pending Human Reviews;
- current Engineering Execution Plan position;
- current AI Insights;
- the Recommended Next Step with Engineering Reasoning and AI Confidence.

### Thirty-Second Test

**Pass, architecturally.**

The design defines a coherent summary contract rather than requiring navigation
through folders, documents, tasks, or conversations. Actual usability remains
an implementation and UX validation requirement for later PATCHes.

### Highest-Priority Work Test

**Pass, architecturally.**

Visible blockers, risks, reviews, plan dependencies, and explainable
Recommended Next Steps allow the engineer to identify priority. Search
relevance and AI novelty are explicitly prohibited from masquerading as
engineering priority.

## Engineering Value Review

Every accepted core concept provides direct engineering value:

- Workspace reduces context reconstruction.
- Engineering Context improves evidence quality.
- Plan versioning preserves engineering planning rationale.
- Engineering Health exposes readiness causes.
- AI Insights reveal gaps, conflicts, and implications.
- ENSE focuses attention on the next valuable review/action.
- Human Review preserves accountable judgment.
- The Engineering Decision Log preserves Engineering Reasoning, alternatives,
  reviewer decisions, historical evolution, and future learning.

Rejected concepts either prioritize software convenience or reproduce generic
project-management behavior without improving engineering decisions.

## AI Necessity Review

AI is justified for future:

- relationship-aware context analysis;
- detection of missing or conflicting information;
- multidisciplinary Engineering Impact Analysis;
- historical similarity with differences;
- standards/reference suggestion;
- uncertainty estimation;
- plan and next-step recommendation.

AI is not necessary for:

- Workspace identity;
- ownership;
- lifecycle;
- archival;
- permissions;
- audit;
- formal approval.

The architecture correctly separates non-AI domain foundations from future AI
assistance. No AI integration belongs in the first Workspace Core sub-patch.

## Domain Model Review

### Engineering Workspace

**Decision:** Accept one Workspace per Project and Discipline.

This model provides the clearest ownership and readiness boundary with minimal
complexity. Areas, Packages, Systems, Equipment, and Tags remain contextual
relationships and do not create hierarchy.

### Engineering Context

**Decision:** Accept combined persisted/derived architecture.

Authoritative relationships and missing/conflict findings require durable,
typed governance. Current views should be derived. Context snapshots are
justified only for evidence reproduction. Entirely JSON-based context is
rejected.

### Engineering Execution Plan

**Decision:** Accept one Project-level versioned aggregate.

This avoids duplicated multidisciplinary plans while allowing phases/items to
relate to Workspaces. Immutable versions, Human Review, and Engineering
Decision Log capture preserve accountability.

The plan is a living engineering hypothesis, not a contractual schedule. It
evolves as engineering knowledge grows and remains engineer-controlled.

### Engineering Health

**Decision:** Accept component indicators; reject universal score.

Indicators must expose source, freshness, uncertainty, and contributing
conditions. The design avoids formula and weight decisions.

### Workspace Readiness

**Decision:** Accept as derived and stage-specific.

Readiness is useful only when the target stage/review and blocking conditions
are explicit. It is neither status nor approval.

### AI Insights

**Decision:** Accept governed advisory records.

Persistence is required for review, expiry, supersession, evidence, and audit.
Chat history is insufficient.

Affected Engineering Objects support future Engineering Impact Analysis and may
include Equipment, Loop, Cable, Panel, Motor, Document, Calculation,
Engineering Decision Log entry, and Tag. They do not authorize automatic
propagation.

### ENSE

**Decision:** Accept as a later advisory domain.

Recommended Next Steps must state Engineering Value, Engineering Reasoning,
blockers, alternatives, and AI Confidence. ENSE must not assign tasks or
execute changes.

Every future recommendation must conceptually expose Recommendation, Reason,
Engineering Impact, Required Inputs, Blocking Dependencies, Confidence, and
Human Review. This remains an architectural output model only.

### Human Review

**Decision:** Accept shared semantics with subject-specific records.

This avoids duplicated meaning while preserving direct relationships. A
universal polymorphic review entity is deferred until multiple implemented
domains demonstrate compatible lifecycle and evidence needs.

### Engineering Decision Log

**Decision:** Require minimal shared foundation in PATCH-020.2.

Deferring all decision modeling would make plan acceptance and modification
untraceable. Building a complete universal Decision Log now would exceed
scope.

## Relationship Review

The aggregate boundaries are coherent:

- Project owns overall identity and the plan collection boundary.
- Workspace owns discipline operational state.
- Engineering Context references shared objects instead of copying them.
- Plan versions own phases/items and their plan-local dependencies.
- advisory objects preserve their own review and supersession.
- Engineering Decision Log entries remain human-owned and independent from AI
  output.
- Audit records actions but does not replace domain history.

The model prevents cascading deletion from destroying engineering evidence.

## Lifecycle Review

Workspace statuses have engineering-specific meanings:

- Draft;
- Active;
- On Hold;
- Under Review;
- Completed;
- Archived.

The review confirms clear separation among:

- Project Status;
- Workspace Status;
- Workspace Readiness;
- Engineering Health;
- Human Review state.

Controlled reopening of Completed or Archived Workspaces is preferable to
duplicating a same-Discipline Workspace.

## Human Review Boundary

The design passes the human-responsibility test:

- AI cannot review or accept its own output.
- Human Review identifies reviewer authority and subject version.
- Accepted by Engineer is not formal deliverable approval.
- rejection and requests for information remain governed outcomes.
- completed review evidence is immutable and superseded rather than edited.
- connected objects are not automatically approved.

Formal Project approval remains out of scope.

## Safety Review

Safe behavior is explicitly defined for:

- missing Engineering Context;
- conflicting data;
- unknown standards;
- absent historical analogues;
- low AI Confidence;
- conflicting recommendations;
- unclear Project stage;
- stale Insights;
- rejected AI guidance.

The preferred response is **Insufficient Information**, with explanation and
Human Review, rather than unsupported assumptions.

No silent mutation or propagation is permitted.

## Permissions Review

The preliminary capability model is appropriate but exposes an implementation
constraint:

- current persisted roles are only `admin` and `engineer`;
- Engineering Manager, Project Manager, Lead Engineer, Reviewer, and Viewer are
  architectural personas only;
- later implementation must map capabilities through current RBAC plus Project
  and Workspace ownership/assignment or obtain separate RBAC approval.

This avoids silently redesigning authentication or adding roles.

Permission checks must apply to:

- mutations;
- detail/list access;
- search;
- context assembly;
- Engineering Health;
- AI Insights;
- history and Engineering Memory.

## Audit and Traceability Review

The required audit coverage is sufficient for the proposed domain.

The architecture correctly distinguishes:

- generic audit events for actor/action/time;
- immutable domain history for plan versions, review evidence, decisions,
  context snapshots, and supersession.

The current centralized Audit Service can remain the integration point, though
future audit metadata filtering and richer querying may require a separate
approved improvement.

No AI Insight, recommendation, Human Review, Engineering Decision Log entry,
status change, plan change, or archival action may occur silently.

## Search Review

Future Universal Search extension is compatible with current architecture if:

- authentication remains mandatory;
- source queries apply authorization before returning records;
- Project Code exact/partial search remains unchanged;
- result types identify Workspace/Insight/Decision/plan context;
- archived and superseded state is visible;
- search relevance is not presented as engineering priority.

Search should not index inaccessible evidence into a result summary.

## Future API Implications

The proposed resource boundaries are coherent:

- Project Workspaces;
- Workspace Context;
- Engineering Execution Plans/Versions;
- Engineering Health/Readiness;
- AI Insights;
- Recommended Next Steps;
- Human Reviews;
- Engineering Decision Log.

Future API design must include:

- authorization at Project and Workspace scope;
- optimistic concurrency or equivalent version conflict protection;
- safe idempotency for retryable create/review actions;
- audit only after successful domain mutation;
- advisory AI language;
- evidence, AI Confidence, freshness, and supersession;
- complete OpenAPI examples.

Deferring endpoint paths is correct for an architecture-only phase.

## Future Database Implications

The likely persistence split is sound:

### Persist

- Workspace identity, ownership, collaborators, status, and archival;
- Discipline reference;
- typed Context relationships and missing/conflict findings;
- immutable plan versions, phases/items, and dependencies;
- subject-specific reviews;
- AI Insights and Recommended Next Steps;
- Engineering Decision Log entries;
- selective evidence snapshots.

### Derive

- current Engineering Context;
- Engineering Health;
- Workspace Readiness;
- current recommendation ranking.

Future persistence must prevent:

- duplicate same-Discipline Workspaces;
- orphaned Project/Workspace references;
- invalid lifecycle/review states;
- destructive cascade loss;
- mutation of immutable versions;
- supersession cycles.

Alembic remains the exclusive schema authority. No schema is approved by this
review.

## Multidisciplinary Example Review

The 160 kW process pump example validates the model without generating design
answers.

The Electrical Workspace can expose:

- missing Motor Datasheet;
- required Short-Circuit Level;
- plan dependency;
- open risk;
- insufficient readiness;
- missing-information AI Insight;
- Recommended Next Step;
- Human Review;
- potential impact of changed motor power.

The Instrumentation Workspace can reference the same pump and source documents
through Engineering Context without copying Electrical ownership or state.

This demonstrates cross-discipline connection without duplicate Workspaces.

## Alternatives and Rejected Designs

| Alternative | Advantage | Primary risk | Decision |
|---|---|---|---|
| Folder-tree Workspace | Familiar navigation | Document-first fragmentation | Rejected |
| Milestone Workspace | Familiar planning | Confuses schedule with discipline work | Rejected |
| One Workspace per Discipline | Clear ownership and readiness | May need future partitioning | Accepted |
| Multiple Workspaces per Discipline | Flexible scope partitioning | Duplicate context and ambiguous readiness | Rejected for foundation |
| Context entirely as JSON | Fast initial modeling | Weak integrity and traceability | Rejected |
| One Health score | Simple display | False precision and hidden causes | Rejected |
| ENSE as Tasks | Familiar workflow | Recommendation becomes assignment | Rejected |
| Insights only in chat | Low modeling effort | No durable review or evidence | Rejected |
| Independent review semantics | Direct local design | Inconsistent states | Rejected |
| Universal Human Review entity | One abstraction | Premature polymorphism | Deferred |

## Architectural Risks

### High

- Permission leakage through cross-Workspace context or search.
- Loss of history through Project deletion or cascade design.
- AI advisory output being treated as assigned or approved work.

### Medium

- Confusion among status, readiness, health, and review.
- Derived context becoming stale or competing with authoritative truth.
- Plan version and evidence growth.
- Current two-role RBAC limiting clean persona expression.
- Engineering Decision Log scope expanding into a universal workflow.

### Low but Material

- One-Workspace-per-Discipline becoming restrictive for very large Projects.
- Terminology drifting toward generic tasks, folders, or dashboards.

## Risk Controls

- implement through small bounded PATCHes;
- authorize every query by Project/Workspace scope;
- use archival and supersession, not destructive replacement;
- define freshness and evidence on derived output;
- test prohibited AI authority language and silent mutation;
- keep Engineering Health component-based;
- require a future ADR before relaxing Workspace cardinality;
- keep universal workflow abstractions out until evidence requires them.

## Open Questions

These questions are intentionally deferred to implementation planning and are
not blockers to ADR-014 approval:

1. Which controlled Discipline values are available at PATCH-020.1 launch, and
   who may administer them?
2. How should current `admin` and `engineer` roles map to the first Workspace
   capability set without prematurely adding roles?
3. What minimum collaborator membership roles are needed in Workspace Core?
4. Which Project lifecycle states allow Workspace creation, activation,
   completion, archival, or reopening?
5. What concurrency mechanism should protect Workspace status and review
   transitions?
6. Which context relationships belong in PATCH-020.2 versus later
   engineering-object PATCHes?
7. What retention period applies to context snapshots, AI evidence, and
   superseded recommendations?
8. Which Engineering Decision Log fields are mandatory in the minimal
   foundation?
9. What event threshold makes a Workspace Readiness change auditable without
   excessive noise?
10. How should Project deletion respond when governed Workspace history exists,
    while preserving compatibility for Projects without such history?
11. What initial search result types provide engineering value without
    over-expanding Universal Search?
12. What UX evidence will demonstrate the 30-second morning-understanding
    criterion?

## Recommended Sub-Patches

1. **PATCH-020.1 — Engineering Workspace Core**
2. **PATCH-020.2 — Engineering Context, Decision Log, and Human Review
   Foundation**
3. **PATCH-020.3 — Engineering Execution Plan Foundation**
4. **PATCH-020.4 — Engineering Health and Workspace Readiness**
5. **PATCH-020.5 — AI Insights Foundation**
6. **PATCH-020.6 — Recommended Next Step Engine Foundation**

Each sub-patch requires its own implementation plan, migration/API impact
review, permission model, audit design, tests, validation, and approval.

## Architecture Validation Answers

1. Engineer understands the situation within 30 seconds: **Yes,
   architecturally.**
2. Highest-priority work is visible: **Yes.**
3. AI explains each recommendation: **Required.**
4. Missing information is explicit: **Yes.**
5. Uncertainty is honest: **Yes.**
6. AI output is reviewable/rejectable/supersedable: **Yes.**
7. Engineering responsibility remains human: **Yes.**
8. Electrical and Instrumentation avoid duplication: **Yes, through shared
   Context relationships.**
9. Project history remains traceable: **Yes.**
10. Folder, task-board, and chatbot architectures are avoided: **Yes.**
11. Product Bible v1.0 alignment: **Yes.**

## Final Architecture Verdict

**APPROVAL RECOMMENDED FOR ARCHITECTURE ONLY**

ADR-014 and PATCH-020 define a coherent, engineer-first foundation. The model
supports the primary user story, preserves human responsibility, provides
future AI with governed Engineering Context, and remains compatible with the
existing Project, RBAC, Audit, Search, PostgreSQL, and Alembic foundations.

Implementation is not authorized. ADR-014 must be accepted and each proposed
sub-patch must receive separate planning and implementation approval.

## Architecture Guardian Verdict

**PASS**

The design helps engineers understand work, missing inputs, risks, reviews,
decisions, and next actions. It rejects software abstractions that do not
produce direct engineering value.

## Chief Engineering Architect Verdict

**PASS WITH IMPLEMENTATION GATES**

The architecture is sufficiently bounded and safe for independent approval.
The recommended decomposition should be retained so that context, review,
decision, health, and AI behavior mature in dependency order.
