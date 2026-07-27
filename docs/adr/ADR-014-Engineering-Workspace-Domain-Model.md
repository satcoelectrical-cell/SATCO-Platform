# ADR-014: Engineering Workspace Domain Model

## Status

Accepted

## Date

2026-07-26

## Related PATCH

PATCH-020 — Engineering Workspace Foundation

## Decision Scope

This ADR defines the permanent domain boundaries and conceptual model for the
Engineering Workspace foundation. It authorizes no implementation, schema,
migration, API, or AI integration.

## Context

SATCO Product Bible v1.0 establishes Engineering Workspace as the primary
operational environment for discipline engineering inside a Project.

The existing platform has a stable Project core with Customer, owner, primary
assignee, lifecycle, permissions, audit, and search foundations. It does not
yet represent discipline work, structured Engineering Context, Engineering
Execution Plans, Engineering Health, AI Insights, Recommended Next Steps, or
Human Review of AI-assisted objects.

Traditional folder, task-board, schedule, and chatbot models do not answer the
engineer’s primary question:

> What engineering work requires my attention now, why does it matter, and
> what evidence supports that conclusion?

The new domain must support Electrical, Instrumentation, Control, Mechanical,
Civil, and Process engineering without becoming generic project management.
It extends SATCO as an Engineering Copilot and does not create an autonomous
engineering system.

## Problem

SATCO needs a stable domain model that:

- gives engineers an immediate view of current engineering work;
- makes missing inputs, risks, decisions, and reviews visible;
- connects discipline work to Project context;
- supports explainable, traceable, non-authoritative AI assistance;
- preserves human ownership and review;
- supports multidisciplinary relationships without duplicating Project state;
- preserves history when records are superseded or archived;
- remains compatible with current Project, User, RBAC, Audit, and Search
  architecture;
- avoids premature workflow-engine, folder-tree, and universal-entity
  complexity.

Without a clear aggregate model, future PATCHes could create disconnected
tables, inconsistent review semantics, opaque readiness scores, or AI output
without durable Engineering Context.

## Decision

### 1. Engineering Workspace Is the Primary Operational Aggregate

Engineering Workspace is the digital operational environment where engineering
work is understood, planned, reviewed, explained, and continuously improved.

It is not a document repository.

It is not a task board.

It is not a project folder.

It is the engineer's operational home inside SATCO.

It brings together:

- current Engineering Context;
- required and missing inputs;
- relevant engineering objects and relationships;
- Engineering Execution Plan position;
- risks, decisions, and pending Human Reviews;
- Engineering Health and Workspace Readiness;
- AI Insights and Recommended Next Steps;
- ownership, collaboration, lifecycle, and traceability.

Additional architectural exclusions:

- a folder;
- a document collection;
- a Project milestone;
- a generic task board;
- a schedule;
- a chat session;
- a discipline label without owned state.

The Workspace is an aggregate root for its identity, discipline, accountable
ownership, collaborator access, lifecycle, and archival state. It does not own
the lifecycle of shared Project, Customer, User, Document, or future
Engineering Knowledge Graph objects.

### 2. One Workspace per Project and Discipline

The initial governed cardinality is:

```text
Project 1 ─── 0..N Engineering Workspaces
Discipline 1 ─── 0..N Engineering Workspaces
Project + Discipline ─── at most 1 active historical Workspace identity
```

Each Project may have one Engineering Workspace for each governed Discipline.
Examples include Electrical, Instrumentation, Control, Mechanical, Civil, and
Process.

Multiple Workspaces for the same Discipline and Project are rejected for the
foundation because they create unclear ownership, fragmented readiness, and
folder-like partitioning. Nested Workspaces are also rejected.

Packages, Areas, Systems, or other scope segments belong in Engineering
Context and relationships. They do not create a Workspace tree.

If a future proven engineering need requires multiple independent discipline
Workspaces, a new ADR must define the partitioning rule, ownership, readiness
aggregation, and migration path.

### 3. Workspace Identity and Accountability

Each Engineering Workspace has:

- one Project;
- one governed Discipline;
- one accountable owner;
- zero or one primary assignee;
- zero or more collaborators;
- one lifecycle status;
- created, updated, and archived timestamps;
- immutable historical identity;
- traceable status and ownership history.

The Workspace owner is accountable for its coordination and review state. This
does not make the owner the sole engineering approver and does not transfer
professional responsibility away from the engineers making specific
decisions.

Project ownership does not silently substitute for Workspace ownership.
Project owners and authorized managers may establish or change Workspace
ownership through explicit, audited actions.

### 4. Workspace Lifecycle

The governed Workspace statuses are:

- **Draft:** Identity, discipline, scope, and ownership are being established.
  Engineering work is not yet declared active.
- **Active:** The Workspace is available for current discipline engineering
  work.
- **On Hold:** Work is intentionally paused. The reason, owner, and unresolved
  conditions remain visible.
- **Under Review:** The Workspace as a whole is being assessed for a defined
  engineering stage or review boundary. This does not replace Human Review
  states on individual objects.
- **Completed:** The current Workspace scope has met its recorded completion
  conditions. Completion is not formal approval of every deliverable.
- **Archived:** The Workspace is retained as historical evidence and is no
  longer operational.

Expected transition direction:

```text
Draft → Active
Draft → Archived
Active ↔ On Hold
Active ↔ Under Review
Under Review → Completed
Completed → Active, only through explicit controlled reopening
Completed → Archived
On Hold → Archived
Archived → Active, only through authorized restoration with rationale
```

Exact transition permissions belong to an approved implementation PATCH.
Every transition requires actor, timestamp, previous state, next state, and
rationale where consequence is material.

Workspace Status is distinct from:

- Project Status, which governs the Project lifecycle;
- Workspace Readiness, which indicates ability to proceed;
- Engineering Health, which exposes multiple decision-support conditions;
- Human Review state, which governs review of a specific reviewable object.

### 5. Engineering Context Is a Governed Aggregate View

Engineering Context is the structured, traceable context used by engineers and
future AI capabilities to understand current engineering work.

It is a combination of:

1. **Persisted authoritative relationships**, such as Project, Customer,
   Discipline, Area, Package, System, Equipment, Tag, Document, Revision,
   Standard, Vendor, Decision, Risk, and review relationships.
2. **Persisted governed observations**, such as required inputs, missing
   information, known conflicts, applicability decisions, and ownership.
3. **Derived contextual views**, assembled for a Workspace, question, review,
   or recommendation from current authoritative records.
4. **Immutable context snapshots**, retained only when necessary to reproduce
   an important AI Insight, Human Review, Engineering Decision Log entry, or
   Engineering Execution Plan version.

Engineering Context is not one unstructured JSON document and is not owned by
a prompt. Flexible evidence metadata may supplement typed relationships, but
must not replace them.

Every contextual element must preserve, where relevant:

- authoritative source;
- ownership;
- revision or effective period;
- freshness;
- applicability;
- conflict state;
- missing-data state;
- access boundary;
- traceability to the originating engineering object.

Conflicting sources remain visible. SATCO does not silently select a winner.
Missing essential context produces **Insufficient Information**, lower AI
Confidence, and a recommended Human Review where appropriate.

### 6. Engineering Execution Plan Is a Project-Level Versioned Aggregate

One current Engineering Execution Plan belongs to a Project and may address
multiple Engineering Workspaces.

The Engineering Execution Plan is a living engineering hypothesis.

It is not a contractual schedule. It evolves as engineering knowledge grows
and always remains engineer-controlled.

The plan is:

- AI-assisted;
- suggested;
- engineer-controlled;
- versioned;
- explainable;
- traceable;
- non-authoritative;
- distinct from the contractual Project schedule.

Each immutable plan version may contain ordered phases and items with:

- Workspace and Discipline relevance;
- required inputs and missing information;
- expected engineering deliverables;
- dependencies and suggested critical engineering path;
- review points and potential risks;
- estimated effort and suggested team roles;
- Recommended Next Step;
- Engineering Reasoning;
- AI Confidence;
- similar historical references.

Plan lifecycle states are:

- **Proposed Draft**
- **Under Review**
- **Accepted for Engineering Use**
- **Rejected**
- **Superseded**

Acceptance means the plan may guide engineering work. It is not contractual
approval or automatic authorization.

Modification, reordering, addition, removal, acceptance, and rejection create
traceable human actions. A changed accepted plan creates a new version; prior
versions remain immutable.

Every material plan response must be preservable as an
Engineering Decision Log entry. No scheduling algorithm, Gantt behavior, or
committed duration is decided by this ADR.

### 7. Engineering Health Is a Set of Explainable Indicators

Engineering Health is a collection of contextual decision-support indicators,
not one universal score.

Initial indicator categories may include:

- Engineering Readiness;
- Data Completeness;
- Decision Completeness;
- Missing Inputs;
- Open Reviews;
- Engineering Risks;
- Standards Coverage;
- AI Confidence;
- Review Readiness;
- Documentation Readiness;
- Engineering Execution Plan Readiness.

Each indicator must expose:

- meaning and affected scope;
- source evidence;
- assessment time and freshness;
- whether it is derived or human-recorded;
- uncertainty and missing inputs;
- contributing conditions;
- Human Review implication;
- traceability.

Current indicator values are normally derived. Historical assessment snapshots
may be retained when needed for audit, review, or trend explanation.

No scoring formula, weight, or universal aggregate score is approved. Lack of
data lowers AI Confidence and produces an explainable insufficient-information
condition rather than false certainty.

### 8. Workspace Readiness Is Derived and Stage-Specific

Workspace Readiness indicates whether the Workspace has sufficient information,
resolved decisions, and completed reviews to proceed to a stated next
engineering stage or review.

It is:

- derived from visible conditions;
- specific to a target stage or review;
- explainable;
- time-sensitive;
- non-authoritative.

Workspace Readiness must identify:

- target stage or review;
- blocking missing inputs;
- unresolved decisions and risks;
- required Human Reviews;
- relevant Engineering Execution Plan dependencies;
- uncertainty and assessment time.

Readiness is one Engineering Health dimension. It is not Workspace Status and
does not approve engineering work.

### 9. AI Insight Is a Governed Advisory Record

An AI Insight is a persisted, explainable, traceable, reviewable recommendation
or warning linked to Engineering Context.

Supported conceptual types include:

- Missing Information;
- Potential Engineering Conflict;
- Suggested Review;
- Engineering Implication;
- Historical Similarity;
- Suggested Standard;
- Suggested Reference;
- Suggested Next Action;
- Potential Risk;
- Context Conflict;
- Insufficient Information.

An AI Insight preserves:

- type, title, and concise explanation;
- Engineering Reasoning;
- input and source references;
- assumptions;
- Affected Engineering Objects;
- relevant standards or historical references;
- AI Confidence and its basis;
- priority or potential consequence without false certainty;
- creation and freshness information;
- Human Review state;
- superseding relationship;
- future model and version traceability.

An AI Insight is never a final decision, formal approval, accepted engineering
change, or untraceable chat response.

Affected Engineering Objects may include:

- Equipment;
- Loop;
- Cable;
- Panel;
- Motor;
- Document;
- Calculation;
- Engineering Decision Log entry;
- Tag.

This relationship exists to support future Engineering Impact Analysis. It
does not authorize automatic propagation or modification.

### 10. Recommended Next Step Engine Is Advisory

The Recommended Next Step Engine, abbreviated **ENSE**, is a future
decision-support capability that answers:

> What should the engineer review or do next?

ENSE evaluates current Engineering Context, Workspace state, Engineering
Health, the Engineering Execution Plan, Human Review states, missing inputs,
risks, unresolved decisions, dependencies, Engineering Memory, and AI
Confidence.

Every future ENSE recommendation must conceptually include this standard
architectural output model:

- **Recommendation:** The review or action suggested for consideration.
- **Reason:** The Engineering Reasoning explaining why it is suggested.
- **Engineering Impact:** The potential consequence or value of acting, not
  acting, or delaying review.
- **Required Inputs:** Information needed to evaluate or perform the
  recommendation responsibly.
- **Blocking Dependencies:** Conditions that prevent or constrain the
  recommendation.
- **Confidence:** AI Confidence with its evidence basis and limitations.
- **Human Review:** The required review state and accountable human boundary.

A Recommended Next Step may additionally identify priority, affected
Workspace or engineering object, traceability, alternatives, freshness,
expiry, and supersession. These additions must not replace or obscure the
standard output model.

This is an architectural output model only. It defines no algorithm, API,
schema, or implementation.

Ranking must be explainable at the architectural level. Engineering consequence,
blocked dependencies, safety relevance, unresolved risk, and readiness impact
may inform priority. Engagement, novelty, or arbitrary urgency must not.

ENSE does not execute recommendations, assign generic tasks, modify engineering
data, or become a workflow engine.

### 11. Human Review Uses Shared Semantics With Subject-Specific Records

The reusable Human Review states are:

- Suggested
- Under Review
- Accepted by Engineer
- Rejected by Engineer
- Needs More Information
- Superseded

**Accepted by Engineer** means an accountable engineer accepts the advisory
item for its stated engineering use. It does not mean formal approval of an
engineering deliverable.

Human Review is a shared domain contract. The foundation should use
subject-specific review records or relationships for Engineering Execution
Plan versions/items, AI Insights, and Recommended Next Steps. A universal
polymorphic review table is not approved because it would weaken referential
integrity and over-generalize before review behavior across domains is proven.

Every review must preserve:

- subject identity and version;
- reviewer identity and authority;
- state;
- comments and rationale;
- requested information;
- timestamp;
- superseding behavior;
- immutable review evidence;
- audit event.

Formal Project approval workflows remain a separate future domain.

### 12. Engineering Decision Log Is a Shared Foundation Dependency

The Engineering Decision Log is the governed, human-owned history of
engineering decisions and their evolution. Each entry may capture:

- what was decided;
- alternatives considered;
- rationale;
- input data and Engineering Context;
- applicable standard or Customer requirement;
- reviewer or decision owner;
- uncertainty;
- affected engineering objects;
- superseding Engineering Decision Log entry;
- timestamp.

The Engineering Decision Log preserves Engineering Reasoning, alternatives,
reviewer decisions, and historical evolution.

The Engineering Decision Log is not implemented by PATCH-020. Its minimal
shared foundation must precede or accompany Engineering Execution Plan
acceptance so plan changes can be preserved as Project decision history.

Engineering Decision Log entries become part of future Engineering Memory only
after appropriate Human Review and contextual governance.

## Chosen Model

The chosen model is:

- one Engineering Workspace per Project and governed Discipline;
- no nested Workspaces;
- structured Engineering Context combining authoritative relationships,
  governed findings, derived views, and selective evidence snapshots;
- one Project-level Engineering Execution Plan with immutable versions;
- Engineering Health as explainable component indicators;
- Workspace Readiness as a derived, target-stage-specific condition;
- AI Insights and Recommended Next Steps as persisted advisory records;
- shared Human Review semantics with subject-specific records;
- minimal Engineering Decision Log foundation before plan acceptance;
- archival and supersession instead of destructive history replacement.

This model is the minimum coherent foundation that supports the primary user
story without introducing folder, task, schedule, chatbot, or workflow-engine
architecture.

## Domain Boundaries

### Project Aggregate

Owns Project identity, Customer, Project lifecycle, Project owner, primary
assignee, and the collection boundary for Workspaces and the current
Engineering Execution Plan.

### Engineering Workspace Aggregate

Owns Workspace identity, Discipline, accountable owner, primary assignee,
collaborator membership, status, archival state, and Workspace-local
coordination.

### Engineering Context Boundary

Resolves governed relationships across Project, Workspace, and engineering
objects. It does not duplicate authoritative objects.

### Engineering Execution Plan Aggregate

Owns plan identity, immutable versions, phases/items, dependencies, review
state, and supersession.

### Advisory Intelligence Boundary

Owns AI Insights and Recommended Next Steps as non-authoritative, versioned,
reviewable advisory records.

### Engineering Decision Log Boundary

Owns human decision evidence, Engineering Reasoning, alternatives, reviewer
decisions, historical evolution, and supersession. It is independent from AI
output and formal deliverable approval.

### Audit Boundary

Records who did what and when. Domain version/history records preserve
engineering meaning; the generic audit log does not replace them.

## AI and Human Responsibility

SATCO remains an Engineering Copilot.

AI may analyze governed Engineering Context, identify missing information and
potential conflicts, explain implications, suggest references, estimate AI
Confidence, propose plan items, and recommend next reviews or actions.

AI may not:

- approve or certify engineering work;
- accept its own recommendations;
- create authoritative Engineering Decision Log entries;
- silently change Engineering Context or engineering objects;
- silently propagate an Engineering Impact Analysis result;
- claim standards compliance without evidence;
- present assumptions as facts;
- conceal uncertainty or staleness.

Human engineers retain responsibility for applicability, technical decisions,
review, approval, safety, and final deliverables. Human Review of an advisory
record does not transfer that responsibility to SATCO.

## Relationship and Cardinality Summary

- Customer has many Projects.
- Project has zero or more Engineering Workspaces.
- Project has at most one Workspace identity per Discipline.
- Workspace belongs to exactly one Project and one Discipline.
- Workspace has one owner, zero or one primary assignee, and zero or more
  collaborators.
- Project has one current Engineering Execution Plan and many immutable plan
  versions over time.
- Plan versions have one or more phases/items; items may relate to multiple
  Workspaces and engineering objects.
- Workspace exposes many contextual relationships, Engineering Health
  indicators, AI Insights, Recommended Next Steps, risks,
  Engineering Decision Log entries, and Human Reviews.
- AI Insights and Recommended Next Steps may supersede earlier records.
- Engineering Decision Log entries may supersede earlier entries while
  preserving history.
- Documents and Revisions remain separately governed objects referenced by
  context; the Workspace does not own or delete them.

## Ownership, Deletion, and Historical Preservation

- Engineering Workspaces are archived, not hard-deleted through ordinary
  product behavior.
- Archived Workspaces retain context, decisions, plan relationships, reviews,
  insights, and audit history.
- Child history must not cascade-delete when a Workspace is archived.
- Once a Project contains governed Workspace history, destructive Project
  deletion must be blocked or replaced by a separately approved archival
  process.
- Existing Project deletion behavior may remain for Projects without governed
  Workspace history until a future implementation PATCH introduces the
  compatibility guard.
- Shared engineering objects are referenced, not owned, by a Workspace.
- Superseded records remain queryable according to authorization and retention
  policy.

## Permissions

The future permission model uses capabilities, scoped to Project and Workspace,
while remaining compatible with current RBAC.

Conceptual responsibilities:

| Capability | Admin | Engineering Manager | Project Manager | Lead Engineer | Engineer | Reviewer | Viewer |
|---|---|---|---|---|---|---|---|
| Create Workspace | Yes | Yes | Yes | Conditional | No | No | No |
| Activate/archive Workspace | Yes | Yes | Conditional | Conditional | No | No | No |
| Change Workspace owner | Yes | Yes | Conditional | No | No | No | No |
| Edit governed Context | Yes | Yes | Conditional | Yes | Assigned scope | Review comments | No |
| Accept/reject plan recommendations | Yes | Yes | Conditional | Discipline scope | Assigned scope where delegated | Review only | No |
| Review AI Insights | Yes | Yes | Yes | Yes | Assigned scope | Yes | No |
| Record Engineering Decision Log entry | Yes | Yes | Conditional | Yes | Assigned scope | Recommend/comment | No |
| Change Workspace Status | Yes | Yes | Conditional | Yes | Limited | No | No |
| View Engineering Health | Authorized | Authorized | Authorized | Authorized | Authorized | Authorized | Authorized |
| Access Engineering Memory | Governed | Governed | Governed | Governed | Governed | Governed | Read-only governed |

Only `admin` and `engineer` exist today. Future role names in this matrix are
architectural personas, not authorization to add persisted roles. Initial
implementation must map capabilities through current roles plus Project and
Workspace ownership/assignment, or obtain separate RBAC approval.

Permissions are evaluated before state changes. Unauthorized records must not
leak through search, health, insight, or history views.

## Audit and Traceability

Future implementation must audit at least:

- Workspace created;
- Workspace ownership or assignment changed;
- Workspace status changed;
- Workspace archived or restored;
- Engineering Context updated;
- context conflict identified or resolved;
- critical missing input identified;
- Engineering Execution Plan proposed;
- plan version modified, accepted, rejected, or superseded;
- AI Insight created, reviewed, expired, or superseded;
- Recommended Next Step accepted, rejected, expired, or superseded;
- Engineering Decision Log entry recorded or superseded;
- Workspace Readiness materially changed.

Every audit event identifies actor, action, entity, entity identifier,
timestamp, Project and Workspace context, and non-sensitive change details.

AI records additionally preserve future provider/model/version, evidence
references, assumptions, Engineering Reasoning, AI Confidence, and source
context version.

No silent mutation is permitted.

## Failure and Uncertainty Behavior

When required context is missing, sources conflict, standards are unknown,
Project stage is unclear, or historical similarity is weak:

- state **Insufficient Information**;
- identify the missing or conflicting condition;
- reduce AI Confidence;
- avoid unsupported assumptions;
- preserve the limitation with the recommendation;
- request Human Review where consequence is material.

When recommendations conflict, both remain visible with their evidence and
scope until reviewed or superseded.

When an Insight or recommendation becomes stale, it is marked stale or
superseded; it is not silently rewritten.

Engineer rejection is a governed outcome. It does not train an automatic rule
without reviewed rationale and learning governance.

## Future API Implications

Future resource boundaries may include:

- Project Workspaces;
- Workspace Context;
- Engineering Execution Plans and versions;
- Engineering Health;
- AI Insights;
- Recommended Next Steps;
- subject-specific Human Reviews;
- Engineering Decision Log.

Each API area must:

- enforce Project/Workspace authorization;
- support safe retry or idempotency for creation and review actions;
- preserve optimistic concurrency or equivalent version protection for
  reviewable records;
- emit audit events only after successful domain changes;
- include OpenAPI examples for success, validation, authentication,
  authorization, conflict, staleness, and missing context;
- label AI responses as advisory;
- expose evidence, AI Confidence, review state, and supersession;
- avoid final endpoint paths until its implementation PATCH is approved.

## Future Database Implications

Likely persisted concepts include:

- governed Disciplines;
- Engineering Workspaces and collaborator membership;
- required/missing input records and typed contextual relationships;
- Engineering Execution Plan identities, immutable versions, phases/items, and
  dependencies;
- subject-specific Human Review records;
- AI Insights and Recommended Next Steps;
- Engineering Decision Log entries and superseding relationships;
- historical assessment/context snapshots where evidence reproduction
  requires them.

Likely derived concepts include:

- current Engineering Context views;
- Engineering Health indicators;
- Workspace Readiness;
- current recommendation ranking.

Future persistence must use explicit relationships, foreign keys, status
constraints, uniqueness for Project/Discipline Workspace identity, timestamps,
indexes for ownership/status/review/search, and archival semantics. It must not
use one oversized table or unstructured JSON as the domain model.

Alembic remains the exclusive schema authority.

## Future Search Implications

Authenticated Universal Search may later discover:

- Workspace name and Discipline;
- Project Code;
- Engineering stage;
- missing inputs;
- risks and Engineering Decision Log entries;
- AI Insights;
- Engineering Execution Plan items;
- Human Review state;
- Workspace Status.

Search must:

- preserve existing Project Code behavior;
- filter by Project and Workspace authorization before returning results;
- distinguish current, archived, and superseded records;
- identify result type and context;
- avoid treating relevance ranking as engineering priority;
- link results back to the authoritative Workspace or object.

## Alternatives Considered

### Engineering Workspace as a Folder Tree

**Advantages:** Familiar navigation and simple containment.

**Risks:** Encourages document-first behavior, arbitrary nesting, duplicated
context, and unclear engineering ownership.

**Product Bible alignment:** Conflicts with workspace-first,
engineering-work-oriented UX.

**Decision:** Rejected.

### Engineering Workspace as a Project Milestone

**Advantages:** Reuses a familiar planning concept.

**Risks:** Confuses discipline accountability with schedule checkpoints and
cannot represent continuous context, decisions, or multidisciplinary impact.

**Product Bible alignment:** Conflicts with the Engineering Workspace and
Engineering Execution Plan separation.

**Decision:** Rejected.

### One Workspace per Discipline

**Advantages:** Clear ownership, readiness, search, and predictable navigation;
minimal complexity.

**Risks:** Large disciplines may later need governed scope partitioning.

**Product Bible alignment:** Strong.

**Decision:** Accepted for the foundation.

### Multiple Workspaces per Discipline

**Advantages:** Flexible package, area, or team partitioning.

**Risks:** Fragmented context and readiness, ambiguous ownership, duplicate
insights, and folder-tree behavior.

**Product Bible alignment:** Possible only with a proven engineering boundary.

**Decision:** Rejected for the foundation; requires a future ADR if needed.

### Engineering Context Stored Entirely as JSON

**Advantages:** Fast initial modeling and flexible shape.

**Risks:** Weak integrity, unclear authority, poor relationship reasoning,
unreliable search, and ungoverned duplication.

**Product Bible alignment:** Conflicts with traceable Engineering Context and
Engineering Knowledge Graph principles.

**Decision:** Rejected.

### Engineering Health as One Universal Score

**Advantages:** Simple presentation and comparison.

**Risks:** False precision, hidden causes, incentives to optimize the number,
and confusion with approval.

**Product Bible alignment:** Conflicts with explainability and uncertainty.

**Decision:** Rejected.

### ENSE Implemented as Generic Tasks

**Advantages:** Familiar assignment and completion workflow.

**Risks:** Converts recommendations into work orders, loses evidence and
confidence, and implies execution authority.

**Product Bible alignment:** Conflicts with advisory AI behavior.

**Decision:** Rejected.

### AI Insights Stored Only as Chat History

**Advantages:** Minimal domain modeling.

**Risks:** Ephemeral context, poor authorization, no supersession, no durable
review, and weak traceability.

**Product Bible alignment:** Directly conflicts with workspace-first AI.

**Decision:** Rejected.

### Human Review Embedded Independently in Every Entity

**Advantages:** Strong direct foreign keys and local simplicity.

**Risks:** Duplicated states and inconsistent semantics.

**Product Bible alignment:** Partially aligned but difficult to govern.

**Decision:** Rejected as a semantic approach. Subject-specific records must
implement one shared Human Review contract.

### Universal Shared Human Review Entity

**Advantages:** One workflow and consistent reporting.

**Risks:** Premature generalization, polymorphic references, weak referential
integrity, and pressure to force unlike approval domains together.

**Product Bible alignment:** Potentially aligned if later evidence supports it.

**Decision:** Deferred. Not approved for the foundation.

## Consequences

### Positive

- Gives engineers a stable operational environment.
- Establishes clear discipline ownership without a folder hierarchy.
- Makes Engineering Context richer than prompts.
- Preserves explainability, Human Review, and AI Confidence.
- Enables multidisciplinary relationships while keeping Project boundaries.
- Protects engineering history through versioning and archival.
- Provides coherent foundations for Engineering Health, AI Insights, and ENSE.
- Supports incremental implementation through bounded PATCHes.

### Negative

- Requires multiple explicit domain records and relationships.
- Requires careful authorization across Project and Workspace scope.
- Derived context and health require freshness and evidence policies.
- Plan versioning and review evidence add lifecycle complexity.
- Existing Project hard deletion needs a compatibility guard once Workspace
  history exists.
- Current two-role RBAC cannot express every future persona directly.

## Engineering Time Principle

Every future SATCO capability shall reduce engineering effort while preserving
engineering quality.

Features that increase software complexity without improving engineering
decision-making shall not become part of SATCO.

This principle governs future evaluation of the Engineering Workspace
foundation and its dependent capabilities. Reduced effort must not be achieved
by hiding uncertainty, bypassing Human Review, weakening traceability, or
transferring engineering responsibility to AI.

## Risks

- **Domain overreach:** Too many concepts could be implemented before the
  Workspace core proves value.
- **Context duplication:** Derived context could be persisted as competing
  truth.
- **Permission ambiguity:** Project and Workspace ownership may conflict.
- **Status confusion:** Workspace Status, readiness, health, Project Status,
  and Human Review could be presented as interchangeable.
- **AI authority drift:** Recommended Next Steps could be treated as assigned
  work.
- **History growth:** Immutable versions and evidence require retention and
  query strategies.
- **Staleness:** Derived indicators and recommendations may outlive their
  sources.
- **Search leakage:** New sensitive objects could appear outside authorization.
- **Premature universality:** Human Review or context abstractions could become
  generic frameworks without proven engineering value.

Mitigation requires small PATCHes, explicit acceptance boundaries, permission
tests, audit evidence, and rejection of unneeded abstraction.

## Compatibility

- Project remains the parent business aggregate and retains its current integer
  route identity and immutable Project Code.
- Customer, owner, and primary assignee semantics remain unchanged.
- Existing Project statuses and progress are not redefined.
- Current `admin` and `engineer` roles remain the implemented RBAC foundation.
- The centralized Audit Service remains the audit integration point.
- Universal Search remains authenticated and retains existing Project Code
  search behavior.
- PostgreSQL remains the structured source of truth.
- Alembic remains the exclusive schema authority.
- No existing endpoint, schema, migration, or behavior changes through this
  architecture-only ADR.

## Future Evolution

Recommended implementation sequence:

1. Engineering Workspace Core and governed Discipline reference.
2. Engineering Context, minimal Engineering Decision Log, and shared Human
   Review semantics.
3. Versioned Engineering Execution Plan.
4. Engineering Health and Workspace Readiness.
5. AI Insights using the established Human Review contract.
6. ENSE and Recommended Next Steps.

### Engineering Objective

**Status:** Future Evolution Only

Engineering Objective is a possible future domain concept representing a
high-level engineering goal from which future Engineering Execution Plans may
be derived.

Examples:

- Complete LV Distribution Design
- Complete Instrument Index
- Complete Protection Coordination

Engineering Objective is not part of PATCH-020 implementation, its proposed
sub-patches, or the current domain foundation. It defines no entity, lifecycle,
relationship, API, schema, migration, or behavior. Adoption requires a
separately approved future architecture decision demonstrating engineering
value and compatibility with the living-hypothesis nature of the Engineering
Execution Plan.

Future ADRs are required for:

- multiple Workspaces per Project and Discipline;
- nested Workspace structures;
- a universal Human Review entity;
- formal engineering approval workflows;
- Knowledge Graph technology beyond PostgreSQL;
- autonomous execution of recommendations, which conflicts with current
  Product Bible governance and would require constitutional resolution.

## Approval Requirement

ADR-014 must be independently reviewed and accepted before any PATCH-020
implementation planning, domain model creation, migration, API, or source-code
change begins.

## Architecture Guardian Decision

The chosen model is acceptable because it improves an engineer’s ability to
understand context, missing information, risks, reviews, and next actions
without transferring engineering judgment to software or AI.

## Chief Engineering Architect Decision

The domain is sufficiently bounded for staged implementation. Approval is
recommended only for the architecture. Implementation remains separately
gated.
