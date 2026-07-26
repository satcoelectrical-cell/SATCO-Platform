# SATCO Experience Bible

**Version:** 1.0

**Status:** Certified and Stable

## Purpose

The SATCO Experience Bible defines the permanent experience philosophy of
SATCO Platform. It governs how engineers should perceive, understand, navigate,
review, and act within SATCO.

It translates the Constitution, Product Bible, and accepted Architecture
Decision Records into experience principles. It does not specify screens,
components, visual assets, frontend technology, APIs, or implementation.

## Scope

This document governs:

- experience structure;
- presentation priorities;
- navigation behavior;
- AI presence;
- information hierarchy;
- interaction character;
- feedback and system states;
- motion, color, typography, and accessibility philosophy;
- future Experience Decision Records.

It applies to every future SATCO experience without authorizing a product
feature or implementation.

As a Foundation v1.0 document, this Experience Bible is stable governance.
Routine PATCH work must not rewrite it directly. A material change requires an
approved XDR, confirmation of architectural compatibility through an ADR when
applicable, and release through a new Foundation version.

Stable does not prevent governed experience evolution. It prevents
uncontrolled modification of the governing baseline.

## Definitions

- **Engineering Experience:** The complete way an engineer understands and
  interacts with engineering work through SATCO.
- **Engineering Cockpit:** The coherent operational view through which an
  engineer understands current Engineering Context, attention, readiness,
  risks, reviews, and Recommended Next Steps.
- **Calm Engineering:** An experience philosophy that reduces unnecessary
  cognitive pressure while keeping important engineering conditions visible.
- **Engineering Attention:** The limited human focus that SATCO must protect
  and direct toward consequential engineering work.
- **Engineering Focus Mode:** A context-preserving experience that reduces
  unrelated information while an engineer examines one question or review.
- **XDR:** An Experience Decision Record governing a durable experience
  decision within the boundaries of this Experience Bible.

## Experience Philosophy

SATCO should help engineers understand engineering work before asking them to
interact with software.

The experience must be:

- engineer-first;
- problem-oriented;
- Workspace-first;
- context-first;
- explain-first;
- review-first;
- calm;
- predictable;
- traceable;
- accessible;
- human-controlled.

The experience must never use apparent intelligence, visual urgency, or reduced
friction to hide uncertainty, weaken Human Review, or imply engineering
authority.

Every future SATCO capability shall reduce engineering effort while preserving
engineering quality. Experience simplicity is valuable only when it improves
engineering understanding or action.

## Engineering Cockpit

The Engineering Cockpit is the experience expression of the Engineering
Workspace.

Engineering Workspace is the digital operational environment where engineering
work is understood, planned, reviewed, explained, and continuously improved.

It is not a document repository.

It is not a task board.

It is not a project folder.

It is the engineer's operational home inside SATCO.

The Engineering Cockpit should allow an engineer to recognize, without
reconstructing Project history:

- active Project and Discipline;
- current Engineering Context;
- Workspace Status and Workspace Readiness;
- Engineering Health conditions;
- missing and conflicting inputs;
- engineering risks;
- unresolved Engineering Decision Log entries;
- pending Human Reviews;
- current Engineering Execution Plan position;
- AI Insights;
- Recommended Next Steps and their AI Confidence.

The Cockpit is not a generic dashboard, a command center for automation, or a
collection of activity metrics. Its purpose is engineering orientation and
responsible attention.

## Calm Engineering

SATCO must communicate engineering consequence without producing avoidable
alarm, noise, or competition for attention.

Calm Engineering requires:

- stable placement of essential context;
- restrained use of emphasis;
- clear priority without artificial urgency;
- visible uncertainty without visual panic;
- summaries that lead to evidence;
- predictable states and language;
- deliberate interruption only for material engineering conditions.

Calm does not mean passive. Critical risks and blockers must remain prominent.
The experience should be proportionate to consequence and confidence.

## Engineering Attention

Engineering Attention is a protected product resource.

SATCO should direct attention according to:

- potential engineering consequence;
- unresolved risk;
- blocking dependency;
- missing required information;
- pending Human Review;
- readiness impact;
- change affecting connected engineering objects;
- staleness of evidence or recommendation.

SATCO must not prioritize content because it is new, conversational, popular,
engaging, or AI-generated.

Every attention signal should answer:

1. What needs attention?
2. Why does it matter?
3. What is affected?
4. What evidence supports it?
5. What is uncertain?
6. What Human Review or action is recommended?

## One Screen – One Question

Each primary experience should answer one dominant engineering question.

Examples:

- What requires my attention today?
- Why is this Workspace not ready?
- What changed in this Revision?
- Which inputs are missing?
- Why was this next step recommended?
- What must I review before proceeding?

Supporting information may remain accessible through progressive disclosure,
but it must not compete with the primary question.

One Screen – One Question does not require one physical display or forbid
complex engineering information. It requires a clear cognitive purpose.

## Navigation Philosophy

Navigation follows engineering context, not software modules.

Preferred movement:

```text
Project
    ↓
Engineering Workspace
    ↓
Engineering question or condition
    ↓
Evidence and relationships
    ↓
Human Review or Engineering Decision Log
```

Navigation must:

- preserve active Project, Workspace, Discipline, and Revision context;
- make context changes unmistakable;
- provide a clear path back to the operational question;
- expose cross-discipline relationships without changing ownership silently;
- avoid deep arbitrary folder structures;
- avoid forcing engineers to remember where information is stored;
- allow summaries to resolve into authoritative evidence.

Navigation history is not engineering history. Durable decisions and reviews
must exist independently of browsing behavior.

## AI Presence

AI appears beside engineering work and never becomes the organizing experience.

AI presence must be:

- contextual;
- clearly identified;
- advisory;
- explainable;
- confidence-aware;
- reviewable;
- dismissible without losing engineering state;
- subordinate to evidence and human decisions.

AI must not occupy the primary experience merely to demonstrate that SATCO
contains AI.

Every material AI output should present:

- recommendation or finding;
- reason;
- Engineering Impact;
- required inputs;
- blocking dependencies;
- AI Confidence;
- Human Review requirement;
- evidence and affected engineering objects.

Chat may support exploration. It must not own Engineering Context, Human
Review, Engineering Decision Log history, or the Engineering Workspace.

## Information Hierarchy

Information should appear in this order when relevant:

1. **Active Engineering Context**
2. **Primary Engineering Question**
3. **Material Risk, Blocker, or Missing Information**
4. **Recommended Next Step**
5. **Reason and Engineering Impact**
6. **AI Confidence and Uncertainty**
7. **Required Human Review**
8. **Evidence and Affected Engineering Objects**
9. **History, Alternatives, and Supporting Detail**

The hierarchy may adapt to the engineering problem, but facts, AI output,
Human Review, and approved records must remain visually and conceptually
distinct.

Metadata must not dominate engineering meaning. Activity volume must not be
presented as engineering progress.

## Engineering Focus Mode

Engineering Focus Mode supports concentrated review of one engineering question
while preserving the surrounding Engineering Context.

It should:

- reduce unrelated navigation and signals;
- keep Project, Workspace, Discipline, and Revision visible;
- preserve access to evidence, assumptions, and affected objects;
- show unresolved conflicts and AI Confidence;
- retain a clear exit to the Engineering Cockpit;
- avoid changing or hiding authoritative state.

Focus Mode must not create a private or detached version of engineering truth.
Comments, reviews, and decisions remain governed and traceable.

## Empty States

An empty state is an engineering communication, not unused space.

It must distinguish:

- no applicable information exists;
- information has not yet been provided;
- information exists but is not accessible;
- a search found no result;
- the system has not completed an assessment;
- available context is insufficient;
- a condition has been resolved.

Empty states should state:

- what is absent;
- why the absence may matter;
- whether the absence blocks work;
- who may provide or review the information;
- a safe next step when one exists.

SATCO must not fill empty states with invented examples that could be mistaken
for Project facts.

## Loading States

Loading must communicate what SATCO is doing without implying a result before
it exists.

Loading states should:

- preserve the user’s active Engineering Context;
- identify whether current information is available but an assessment is
  pending;
- distinguish retrieval, analysis, and submission;
- avoid fake precision;
- allow safe cancellation where the operation is advisory;
- prevent duplicate consequential actions;
- explain failures and recovery paths.

Previous valid information may remain visible when clearly labeled with its
assessment time and staleness. A loading indicator must not hide a known risk
or missing input.

## Interaction Principles

1. **Understand before acting.** Evidence and consequence precede material
   actions.
2. **Preserve context.** Interactions do not silently change Project,
   Workspace, Discipline, or Revision.
3. **Make consequence visible.** Material changes disclose affected scope.
4. **Separate advice from decisions.** AI recommendations and human decisions
   use distinct states and language.
5. **Support reversal through governance.** Corrective actions supersede
   history rather than erasing it.
6. **Prevent accidental authority.** Acceptance of advice does not appear to
   approve a deliverable.
7. **Prefer directness.** Common engineering actions should not require
   unnecessary navigation.
8. **Protect against repetition.** Retryable actions should not create duplicate
   reviews, decisions, or recommendations.
9. **Explain refusal.** Blocked or unavailable actions state the governing
   reason.
10. **Never surprise engineers.** Changes, scope, defaults, and assumptions are
    explicit.

## Motion Principles

Motion supports orientation and state change; it does not decorate engineering
work.

Motion should:

- show relationship between origin and destination;
- clarify expansion, collapse, update, and supersession;
- remain subtle and brief;
- respect reduced-motion preferences;
- never be the only signal of state or priority;
- avoid continuous animation around unresolved risks;
- avoid implying that analysis is complete before evidence is available.

Critical information must remain understandable without motion.

## Color Philosophy

Color communicates category and consequence with restraint.

Color must:

- support, not replace, text and symbols;
- distinguish risk, warning, information, success, review, and uncertainty;
- avoid using one color for both confidence and severity;
- avoid presenting AI output as approved through authoritative colors;
- maintain sufficient contrast;
- remain meaningful for common color-vision differences;
- be consistent across Workspaces and lifecycle states.

Green must not imply formal engineering approval unless an authorized approval
state explicitly exists. Red must be reserved for material conditions, not
routine attention.

## Typography Principles

Typography should make engineering information scannable, comparable, and
calm.

Principles:

- use a clear hierarchy with few levels;
- prioritize readable body text and labels;
- keep identifiers, units, revisions, and technical values unambiguous;
- preserve meaningful capitalization of canonical SATCO terms;
- avoid decorative typography;
- use emphasis sparingly;
- support dense evidence without reducing legibility;
- distinguish labels, values, explanations, and statuses consistently.

Typography must not make AI language appear more authoritative than source
evidence or Human Review.

## Accessibility Principles

Accessibility is an engineering quality requirement.

SATCO experiences must be capable of supporting:

- keyboard operation;
- assistive technologies;
- clear focus order and visible focus;
- sufficient contrast;
- scalable text and usable reflow;
- non-color state communication;
- reduced motion;
- understandable labels and instructions;
- clear validation and error recovery;
- adequate target size;
- time-independent review where safety permits;
- localization without loss of technical meaning.

Accessibility must be considered when an XDR is proposed, not added after an
experience is otherwise approved.

## Experience Decision Rules

An XDR is required when a decision establishes or changes a durable experience
rule involving:

- Engineering Cockpit structure;
- navigation;
- attention and priority;
- AI presence;
- information hierarchy;
- Human Review presentation;
- lifecycle or status meaning;
- visual semantics;
- accessibility;
- cross-Workspace experience behavior.

An XDR may not override the Constitution, Product Bible, an accepted ADR, or
this Experience Bible.

## Future Experience Evolution

Future experience evolution may deepen:

- multidisciplinary Engineering Cockpits;
- role-appropriate attention views;
- traceable Engineering Impact Analysis;
- contextual Engineering Focus Modes;
- accessible visualization of Engineering Knowledge Graph relationships;
- historical comparison and Engineering Memory;
- calm coordination across devices and work settings;
- regional, language, unit, and standards context.

Evolution must occur through approved XDRs and PATCHes. New interaction
patterns must demonstrate reduced engineering effort, preserved engineering
quality, and compatibility with human-controlled Engineering Reasoning.

## Permanent Experience Statement

SATCO should feel like a disciplined engineering environment: calm enough for
careful thought, clear enough for rapid orientation, and honest enough to show
what is unknown.
