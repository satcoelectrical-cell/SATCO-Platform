# ADR-013: AI Engineering Copilot Architecture

## Status

Accepted

## Date

2026-07-26

## Decision Scope

SATCO AI architecture and all future AI-assisted engineering capabilities.

## Supersedes

This ADR supersedes any previous interpretation that SATCO AI is primarily an
engineering document generator, an isolated chatbot, or an automatic
engineering decision system.

## Context

SATCO Platform requires a durable architectural definition for the role of AI
in engineering work.

Engineering projects contain interconnected technical context, decisions,
standards, equipment, tags, documents, revisions, calculations, risks, and
history. Useful engineering assistance requires reasoning across these
relationships throughout the complete engineering lifecycle.

An isolated conversational interface or document-generation workflow cannot
provide the required context awareness, traceability, readiness assessment, or
engineering risk analysis.

Engineering work also carries professional, commercial, operational, and
safety responsibilities. AI may assist engineering judgment, but it must never
replace the responsible engineer.

## Core Vision

SATCO is not:

- A CAD system
- A document generator
- A ChatGPT wrapper
- A generic project management system

SATCO is:

> An AI-powered Engineering Copilot Platform.

## Mission

SATCO assists engineers throughout the engineering lifecycle.

It accelerates engineering work by providing:

- Analysis
- Recommendations
- Validation
- Planning
- Context awareness
- Engineering knowledge

Engineering judgment always remains with the engineer.

AI never automatically replaces engineering decisions.

## Decision

SATCO will be designed and developed as an Engineering Copilot. Its AI
capabilities operate over structured engineering context and connected
engineering objects to help engineers understand problems, identify risks,
evaluate options, and decide what to do next.

Every future AI capability must comply with the principles below.

## Principle 1 — AI Suggests, Engineers Decide

AI outputs are recommendations for engineering review, not automatic
engineering results.

Approved user-facing language includes:

- Suggested
- Recommended
- Potential issue
- Needs review

AI output must not be presented as:

- Generated
- Final
- Approved

The system may internally compute, assemble, or prepare an output, but the
engineer-facing result must clearly communicate its advisory status.

AI recommendations must:

- Identify that engineer review is required.
- Preserve the responsible engineer's authority.
- Avoid implying certification, approval, or final engineering acceptance.
- Retain available context, assumptions, confidence, and reasoning.

No AI workflow may automatically approve a design, calculation, document,
engineering decision, or deliverable.

## Principle 2 — Engineering Workspaces

Projects are composed of Engineering Workspaces.

Initial workspace examples include:

- Electrical
- Instrumentation
- Control
- Mechanical
- Civil

An Engineering Workspace contains engineering information, state, context,
relationships, risks, reviews, and recommendations. It is not an AI
conversation container.

Conversations may provide an interaction surface, but they do not define or own
the engineering state. Workspace information remains available independently
of any individual conversation.

Each workspace must support its discipline while participating in the shared
Project context and cross-discipline engineering relationships.

## Principle 3 — Context-First AI

AI must understand the available engineering context before making
recommendations.

Required context dimensions include:

- Customer
- Plant
- Area
- Package
- Discipline
- Equipment
- Tag
- Document
- Revision
- Project Stage
- Previous Decisions

AI must not operate as an isolated chatbot.

Before producing a recommendation, the AI context process should:

1. Identify the relevant Project and Engineering Workspace.
2. Resolve related engineering objects.
3. Identify the current Project Stage.
4. Retrieve applicable decisions, revisions, standards, and history.
5. Detect missing or conflicting context.
6. State material assumptions and context limitations.
7. Provide a confidence level appropriate to the available information.

When essential context is missing, the AI should report missing information and
request engineer review instead of presenting a confident conclusion.

## Principle 4 — Engineering Knowledge Graph

Engineering objects become connected so AI can reason over relationships rather
than isolated text.

Conceptual relationship path:

```text
Project
    ↓
Customer
    ↓
Area
    ↓
Equipment
    ↓
Tag
    ↓
Documents
    ↓
Vendor
    ↓
Standards
    ↓
Calculations
    ↓
History
```

This diagram represents connected engineering knowledge, not a requirement that
every relationship be a single linear database hierarchy.

The Engineering Knowledge Graph must support:

- Relationship-aware context retrieval
- Engineering traceability
- Revision and decision history
- Cross-document and cross-discipline consistency checks
- Similar-project discovery
- Standards and vendor-context discovery
- Explanation of why a recommendation applies

The graph may be implemented incrementally. This ADR defines the architectural
relationship model and reasoning direction; it does not mandate a specific
graph database technology.

PostgreSQL remains the structured-data source of truth unless a future approved
ADR introduces a specialized complementary store.

## Principle 5 — Engineering Execution Plan

Immediately after Project creation, SATCO prepares a suggested Engineering
Execution Plan.

The Engineering Execution Plan is not a project schedule.

It is an evolving AI-assisted engineering roadmap based on:

- Project type
- Discipline
- Scope
- Similar historical projects
- Engineering standards
- Customer requirements

The plan continuously evolves during Project execution as context, decisions,
risks, reviews, and engineering information change.

The engineer-facing plan must be identified as suggested or recommended. It
must not be labeled final, approved, or automatically accepted.

The Engineering Execution Plan contains:

- Suggested engineering phases
- Required inputs
- Missing information
- Potential engineering risks
- Recommended next step
- Critical path
- Expected engineering deliverables
- Estimated engineering effort
- Suggested engineering team
- Confidence level
- Historical similar projects

Engineers review, change, accept, reject, or defer its recommendations.

The Engineering Execution Plan complements project scheduling but does not
replace schedule management, contractual planning, resource authorization, or
engineering leadership.

### Engineering Execution Plan Reasoning

The Engineering Execution Plan must explain:

- Why each phase is suggested
- Which Project inputs triggered it
- Which phases depend on others
- Which activities form the critical path
- Which information is missing
- Which risks affect the plan
- Which similar Projects influenced the recommendation
- Confidence levels for duration and effort estimates

The plan is advisory and dynamic.

Engineers and project managers may:

- Accept
- Modify
- Reorder
- Add
- Remove
- Reject

recommended phases and activities.

All manual changes must be preserved as Project decisions.

## Principle 6 — Engineering Health

Each Engineering Workspace exposes a continuously updated view of Engineering
Health.

Health dimensions include:

- Data Completeness
- Design Consistency
- Engineering Risks
- Open Reviews
- AI Confidence
- Missing Inputs
- Readiness for Client Review

Engineering Health is an advisory engineering-readiness assessment. It is not
an approval, certification, contractual acceptance, or substitute for Human
Review.

Every displayed Engineering Health indicator should provide:

- Contributing factors
- Missing or uncertain information
- Relevant open issues
- Calculation or assessment time
- Available supporting evidence
- AI Confidence where applicable

Engineering Health must be explainable. A single opaque number without
supporting factors is insufficient.

## Principle 7 — AI Responsibilities

SATCO AI is responsible for assisting engineers through:

- Analyze
- Recommend
- Validate
- Detect conflicts
- Suggest standards
- Suggest previous similar projects
- Explain engineering implications
- Estimate effort
- Track engineering readiness

SATCO AI must never automatically create approved engineering deliverables.

AI may prepare suggested content, identify expected deliverables, review draft
engineering information, or recommend changes. Approval and release remain
human responsibilities.

## Principle 8 — Future Roadmap Alignment

All future patches must follow this architecture.

The following planned patch families must explicitly build on Engineering
Workspace and Engineering Execution Plan concepts:

- PATCH-020
- PATCH-021
- PATCH-022
- PATCH-023
- PATCH-024
- PATCH-030

Before implementation, each of these patches must explain:

- Which Engineering Workspace capability it advances
- Which engineering context it requires
- Which knowledge relationships it creates or consumes
- How it affects the Engineering Execution Plan
- How it affects Engineering Health dimensions
- Where engineer review and decision authority remain explicit

A patch that treats AI as an isolated chatbot or automatic document approval
system conflicts with this ADR.

## Human Authority and Safety Boundary

The responsible engineer always retains authority for:

- Engineering design
- Calculations
- Safety decisions
- Standards interpretation
- Technical acceptance
- Document approval
- Client review readiness
- Construction and commissioning decisions
- Final deliverables

SATCO must communicate uncertainty, missing context, conflicts, and confidence.
It must not conceal uncertainty behind authoritative language.

## Architectural Implications

Future architecture should prioritize:

- Structured Engineering Workspace state
- Context assembly before model invocation
- Traceable engineering-object relationships
- Revision-aware information retrieval
- Decision and recommendation history
- Explainable recommendations
- Confidence and missing-input representation
- Human Review workflows
- Engineering readiness assessment
- Provider-independent AI orchestration

AI conversations, if present, are interaction mechanisms over this architecture
and not the primary data model.

## Engineering Reasoning

Every AI recommendation must be explainable.

SATCO must not present engineering suggestions as unexplained outputs. Every
recommendation should be capable of exposing:

- Why the recommendation was made
- Input data used
- Engineering assumptions
- Standards or rules referenced
- Similar historical Projects considered
- Constraints or risks detected
- Confidence level
- Items requiring engineer verification

Example:

```text
Suggested Breaker: 320 A

Reasoning:
- Motor power: 160 kW
- Voltage: 400 V
- Estimated full-load current
- Applicable engineering margin
- Protection philosophy
- Customer standard
- Similar approved historical selections
- Confidence: 93%
```

The system must support a future **Why?** or **Explain Recommendation**
capability.

AI explanations must be concise, traceable, and suitable for engineering
review.

## Context Quality Principle

The quality of SATCO AI output depends on the quality of engineering context.

AI Confidence must decrease when:

- Required data is missing
- Engineering relationships are incomplete
- Standards are unknown
- Project Stage is unclear
- Customer requirements are missing
- Historical references are weak
- Conflicting data exists

Low-confidence output must be clearly labeled.

The system must prefer:

> Insufficient information

over unsupported engineering assumptions.

## Engineering Memory

SATCO must preserve reusable engineering knowledge from completed Projects.

Engineering Memory includes:

- Project context
- Engineering decisions
- Alternatives considered
- Reasons for final decisions
- Detected issues
- Resolved conflicts
- Vendor selections
- Applicable standards
- Customer preferences
- Lessons learned
- Review outcomes
- Approved exceptions
- Final engineering results

Future Projects may use Engineering Memory to identify similar historical work
and provide recommendations.

Example:

```text
Similar Project: BIPC Utility Upgrade
Similarity: 91%

Relevant memory:
- Cable type selected
- Protection method used
- Customer-specific requirement
- Previous design conflict
- Final approved decision
- Lesson learned
```

Engineering Memory must never silently copy previous decisions into a new
Project.

Historical knowledge may only be presented as:

- Suggested reference
- Similar precedent
- Previous decision
- Potential lesson

The current engineer remains responsible for applicability.

## Engineering Impact Analysis

SATCO must identify the potential downstream effects of engineering changes.

Example change:

```text
Motor power:
160 kW -> 200 kW
```

Potentially affected objects include:

- Load List
- Breaker
- Cable sizing
- MCC feeder
- Protection settings
- Transformer loading
- Voltage drop calculation
- Short-circuit study
- Single Line Diagram
- Bill of Quantity
- Engineering reviews

Impact Analysis must:

- Identify connected engineering objects
- Explain why each item may be affected
- Distinguish direct and indirect impacts
- Indicate review priority
- Avoid automatic modification
- Require engineer confirmation

SATCO must never silently propagate engineering changes. It identifies impact
and recommends review.

## Traceability

Every AI insight, recommendation, warning, risk, estimate, or roadmap item must
be traceable to its origin.

Traceability may include:

- Project data
- Engineering object
- User input
- Standard
- Rule
- Historical Project
- Previous decision
- Calculation result
- Revision
- Timestamp
- AI model and version
- Confidence level

Future implementation must make AI output auditable.

## Human Review States

AI outputs must support explicit engineering review states:

- Suggested
- Under Review
- Accepted by Engineer
- Rejected by Engineer
- Superseded
- Needs More Information

**Accepted by Engineer** does not mean a formally approved engineering
deliverable unless the relevant Project approval workflow also confirms
approval.

## AI Safety Boundaries

SATCO AI must not:

- Sign or approve engineering documents
- Claim regulatory compliance without evidence
- Present assumptions as confirmed facts
- Modify engineering data silently
- Change approved decisions without review
- Replace qualified engineering judgment
- Hide uncertainty
- Invent standards, vendor data, or Project history
- Generate final engineering approval
- Treat historical precedent as universally applicable

## Alternatives Rejected

### SATCO as a Document Generator

Rejected because documents are outputs of engineering work, not the engineering
reasoning, context, relationships, decisions, and readiness state that SATCO
must assist.

### SATCO as a Generic Chatbot Wrapper

Rejected because isolated prompts lack persistent Project context,
relationship-aware knowledge, revision history, and engineering traceability.

### SATCO as an Autonomous Engineering System

Rejected because AI cannot assume professional engineering responsibility,
approve engineering decisions, or replace accountable engineers.

### SATCO as Generic Project Management Software

Rejected because schedules and task tracking alone do not provide
discipline-specific engineering analysis, knowledge, validation, or readiness
assessment.

### SATCO as a CAD System

Rejected because CAD authoring is not the platform's architectural mission.
SATCO may provide future engineering context or review assistance around design
artifacts without becoming the authoritative CAD authoring tool.

## Consequences

### Positive

- Establishes a clear, durable AI product identity.
- Preserves engineer authority and accountability.
- Prevents AI features from becoming disconnected chatbot functions.
- Makes engineering context and relationships first-class.
- Aligns future patches around shared Workspace and Execution Plan concepts.
- Supports explainable risks, readiness, confidence, and recommendations.
- Separates engineering assistance from automatic deliverable approval.

### Negative

- Requires more structured context and domain modeling before useful AI output.
- Increases traceability, revision, and relationship-management requirements.
- Makes simple prompt/response implementations architecturally insufficient.
- Requires explainability and confidence handling across future AI features.
- Engineering Execution Plans and Engineering Health must evolve with Project
  state.

## Implementation Constraints

This ADR does not itself authorize implementation.

Future implementation must:

- Follow documentation-first patch governance.
- Define domain models and workflows in separately approved patches.
- Preserve PostgreSQL as the structured source of truth.
- Maintain AI-provider independence.
- Keep user-facing AI output advisory.
- Require engineer review for engineering decisions and deliverables.
- Avoid introducing document-generation behavior as the core AI architecture.

## Definition

> SATCO is an Engineering Copilot.
>
> It helps engineers think better.
>
> It does not think instead of engineers.
