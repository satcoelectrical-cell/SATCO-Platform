# PATCH-020.2 Engineering Context Discovery

## Status

Architecture Discovery — Awaiting Architectural Review

This document is a domain-discovery record. It is not an EDS, architecture
decision, implementation plan, PATCH implementation, or authorization to
change software or data.

## Discovery Question

> What is Engineering Context inside SATCO?

Engineering Context is the bounded, traceable body of information that gives
engineering work its meaning at a particular time.

It tells an engineer:

- what is being engineered;
- for which Customer, Project, plant, unit, area, system, and Discipline;
- which requirements, evidence, revisions, and prior human decisions apply;
- which inputs are available, missing, uncertain, stale, or conflicting;
- which assumptions, constraints, dependencies, risks, and open questions
  shape the work;
- which outputs are expected or already exist;
- who is accountable for the sources, interpretations, and decisions;
- what changed, when it changed, and what may need review.

Engineering Context is therefore not merely a set of facts. It is facts and
evidence together with their relationships, authority, applicability,
revision, time, uncertainty, and human ownership.

## Basis of Discovery

This discovery is governed by:

- the SATCO Platform Constitution;
- Product Bible v1.0;
- the SATCO Engineering Philosophy;
- the SATCO Experience Bible;
- the SATCO Governance Model;
- accepted ADR-013;
- accepted ADR-014;
- PATCH-020;
- the completed PATCH-020.1 Engineering Workspace Core;
- EDS-020.1.

The current Project, Engineering Workspace, Search, Audit, RBAC, database,
model, repository, and service behavior was also inspected to identify
existing boundaries. That inspection informs this domain description but does
not make any implementation decision.

## Why Engineering Context Exists

Engineering work becomes unsafe and inefficient when engineers must repeatedly
reconstruct meaning from disconnected files, conversations, memory, and
unqualified data.

Engineering Context exists to reduce that reconstruction burden without
reducing human responsibility. It enables an engineer to:

- understand scope before acting;
- distinguish current evidence from superseded evidence;
- identify the authority behind a requirement or value;
- determine whether information applies to the present work;
- see missing inputs and unresolved conflicts rather than inherit silent
  assumptions;
- understand cross-discipline interfaces and dependencies;
- trace conclusions back to sources, revisions, calculations, and decisions;
- assess the potential impact of change;
- review AI assistance with the same evidence the AI used;
- preserve enough meaning for future engineers to understand what happened.

Context supports engineering judgment. It does not replace it.

## What Engineering Context Is Not

Engineering Context is not:

- a prompt or a collection of prompt text;
- an AI conversation or chat history;
- an editable summary that replaces its sources;
- a document repository or folder tree;
- a generic metadata bag;
- the Engineering Workspace itself;
- the Project itself;
- an Engineering Execution Plan;
- a task list, schedule, or Gantt model;
- an AI recommendation, confidence score, or Engineering Health result;
- an Engineering Decision Log entry;
- a generic audit trail;
- Engineering Memory;
- formal document approval or a claim of compliance;
- an automatic mechanism for propagating engineering changes.

Project, Workspace, source records, decisions, plans, reviews, and history
retain their own meanings. Engineering Context makes their relevant
relationships understandable without taking ownership of them.

## The Engineer’s Contextual Questions

Engineering Context is useful when it can answer questions such as:

### Position

- Which Project and Discipline am I working in?
- What plant, unit, area, package, system, or equipment is in scope?
- What lifecycle stage or review target is relevant now?
- What is explicitly outside the current scope?

### Authority

- Which Customer requirement governs this work?
- Which specification, standard, revision, vendor source, calculation, or
  decision supports this statement?
- Is the source approved, reviewed, provisional, superseded, or unknown?
- Who owns the source and who is qualified to resolve disagreement?

### Applicability

- Does this requirement apply to this Project, Discipline, location, equipment
  class, operating condition, and lifecycle stage?
- Which edition or effective period applies?
- Is an exception or Customer-specific interpretation in force?
- Is historical precedent genuinely comparable or merely similar?

### Completeness and uncertainty

- Which required inputs are present?
- Which inputs are missing?
- Which values conflict across sources?
- Which statements are facts, assumptions, interpretations, or AI inferences?
- What is stale or awaiting confirmation?
- What cannot yet be concluded safely?

### Relationships and consequence

- Which equipment, tags, documents, calculations, interfaces, and decisions
  are connected?
- Which other Disciplines depend on this information?
- What may be affected if an input or revision changes?
- Which open question, risk, or dependency blocks responsible progress?

### Responsibility and history

- Who is accountable for the current engineering interpretation?
- Which person reviewed or decided the issue?
- What changed since the prior state?
- Why was a prior conclusion accepted, rejected, or superseded?

## Information Engineers Need

The following inventory describes engineering meaning, not a future data
model. An item may be relevant at Project level, Workspace level, or both,
depending on its scope.

### Business and Project setting

- Customer identity and Customer-specific requirements;
- Project identity, purpose, scope, exclusions, status, and priority;
- contractual or operating boundaries relevant to engineering;
- Project owner, primary assignee, stakeholders, and responsible authorities;
- applicable location, plant, unit, area, and package;
- Project stage and current review target.

### Discipline and scope

- governed Discipline;
- Workspace ownership, assignment, collaborators, and lifecycle state;
- Discipline scope, interfaces, and exclusions;
- relevant systems, equipment, tags, cables, panels, IO, loops, and other
  engineering objects;
- cross-discipline ownership and handoff boundaries.

### Requirements and constraints

- Customer standards and specifications;
- legal, regulatory, industry, company, and Project requirements;
- applicable standard edition and the basis of applicability;
- design criteria and operating conditions;
- environmental, safety, physical, functional, commercial, schedule, vendor,
  and interface constraints;
- approved exceptions and their limits.

### Evidence

- controlled documents and their revisions;
- Customer and vendor data;
- equipment and tag information;
- calculations, methods, inputs, assumptions, results, and review state;
- surveys, studies, correspondence, and other qualified source material;
- provenance, issue date, effective date, revision, review, and supersession.

### Work conditions

- required inputs and whether they are available;
- missing information;
- assumptions and their owners;
- open questions and expected responders;
- known conflicts and competing sources;
- risks, dependencies, interfaces, and blockers;
- information freshness and known limitations.

### Expected engineering movement

- inputs consumed by the Discipline;
- outputs expected from the Discipline;
- output maturity or review state;
- dependencies between inputs and outputs;
- review points and decisions needed before responsible progression.

This last group describes the work’s contextual conditions. Ordered work,
recommended activities, effort, sequencing, and planned deliverables belong to
the future Engineering Execution Plan rather than becoming contextual truth.

## Context Classes

The classes below distinguish kinds of engineering meaning. They do not decide
how any class will be represented.

### Authoritative Context

Authoritative Context is information accepted as a governed source for the
current purpose.

Examples include:

- current Project and Customer facts;
- governed Project and Workspace identity and accountability;
- confirmed plant, area, system, equipment, and tag relationships;
- controlled document revisions;
- verified Customer or vendor data;
- reviewed calculation results;
- applicable standards and specifications, including edition and scope;
- human-owned decisions, approved exceptions, and completed review outcomes.

Authority is contextual, not universal. A document can be authoritative for
one purpose and inapplicable to another. A standard is not authoritative merely
because it exists; its applicability and edition must be established.

Authoritative Context must remain distinguishable from summaries,
interpretations, assumptions, and AI output.

### Derived Context

Derived Context is an interpretation or view assembled from available sources.

Examples include:

- current-scope summaries;
- relationship-based relevance;
- identified missing inputs;
- detected inconsistencies;
- potential change impacts;
- similarity to historical work;
- completeness or readiness observations;
- freshness assessments;
- a bounded view prepared for a question or review.

Derived Context must identify its basis and assessment time. It does not
silently become authoritative because it is useful or repeatedly shown.

A derived missing-information or conflict finding may become a governed
observation after responsible human review. That review does not alter the
underlying sources by itself.

### Snapshot Context

Snapshot Context is a frozen evidence frame showing what relevant context was
available for an important event.

It exists to help future reviewers reproduce the basis of:

- a material Human Review;
- a human Engineering Decision;
- an important AI Insight or recommendation;
- a version of the future Engineering Execution Plan.

A snapshot is historical evidence. It does not compete with current truth and
must not silently refresh when its sources change.

### AI-generated Context

AI-generated Context is machine-produced interpretation, extraction,
classification, comparison, assumption, or relevance assessment.

AI may identify candidate relationships, suspected conflicts, missing
information, possible applicability, historical similarity, or potential
impacts. These remain explicitly AI-generated and advisory until an authorized
person evaluates them.

AI-generated Context:

- is never authoritative merely because confidence is high;
- must expose sources, assumptions, uncertainty, and limitations;
- must state **Insufficient Information** when essential context is absent;
- cannot resolve conflicts or declare applicability on its own;
- cannot become Engineering Memory without governed human review.

### Historical Context

Historical Context is context that no longer describes the current state but
remains necessary to understand engineering evolution.

Examples include:

- superseded document and data revisions;
- prior applicability conclusions;
- resolved or superseded assumptions;
- closed questions and conflicts;
- earlier risk states;
- prior Human Reviews;
- superseded decisions and their rationale;
- evidence snapshots;
- past Project and Workspace conditions;
- reviewed outcomes and lessons with known reuse boundaries.

Historical Context preserves what was known, believed, disputed, and decided
at the time. It is not automatically applicable to current work.

### Transient Context

Transient Context exists only to support a short-lived act of navigation,
exploration, or reasoning.

Examples include:

- the current screen or search focus;
- a temporary selection of engineering objects;
- an exploratory comparison;
- an unsubmitted working note;
- a provisional filter or question;
- intermediate reasoning that has no durable engineering significance.

Transient Context expires when its immediate purpose ends. If it becomes
material to a recommendation, review, decision, assumption, conflict, or
engineering outcome, it is no longer safely transient and requires governed,
traceable treatment.

## Authority Is More Than Source Type

For an engineer to rely on information, context must answer more than “where
did this come from?”

Material information may need:

- source identity;
- source owner;
- revision or version;
- issue and effective time;
- review or approval state;
- applicability scope;
- known exceptions;
- freshness;
- conflict state;
- confidence in extraction or interpretation;
- access boundary;
- supersession state.

Two sources may both be authentic and still conflict. Engineering Context must
preserve the conflict; it must not silently choose whichever source is newer,
more convenient, or easier for AI to read.

## Ownership and Stewardship

Engineering Context has distributed ownership because its sources have
different authorities.

### Project accountability

The Project owner is accountable for shared Project context: Customer and
Project scope, common boundaries, Project-stage meaning, shared requirements,
and cross-discipline conditions.

This accountability does not make the Project owner the technical authority
for every Discipline or source.

### Workspace accountability

The Workspace owner is accountable for the relevance, completeness, and
discipline interpretation of context used within that Workspace.

The primary assignee maintains the working understanding within delegated
scope. Collaborators contribute evidence and interpretation within their
authorized participation. Their participation does not make every contribution
authoritative.

### Source authority

The qualified owner of a document, calculation, equipment record, standard
applicability conclusion, vendor submission, risk, or other engineering object
remains responsible for that source’s technical meaning.

Engineering Context references that authority; it does not transfer it.

### Review and decision authority

Reviewers evaluate evidence within their competence and authorization.
Accountable engineers make or record decisions. Human Review confirms,
rejects, qualifies, or requests more information; it does not silently approve
connected objects.

### Organizational stewardship

SATCO owns and governs its accumulated engineering knowledge. Customer,
Project, authorization, confidentiality, and retention boundaries still
control who may use particular information.

## Who Updates Context

Authorized people update the engineering meaning for which they are
accountable:

- Project owners or delegated Project participants maintain shared Project
  conditions;
- Workspace owners and assigned engineers maintain discipline-local
  interpretation and working conditions;
- qualified source owners revise the engineering objects they control;
- collaborators contribute within scope;
- reviewers record review outcomes;
- accountable engineers resolve decision-worthy questions.

AI may propose, extract, compare, flag, and summarize. AI does not perform an
authoritative update.

## What AI May Read

AI may read only context that:

- the current actor is authorized to access;
- is relevant to the bounded Project, Workspace, engineering object, question,
  or review;
- retains its source, revision, applicability, freshness, and review meaning;
- can be distinguished as authoritative, derived, historical, transient, or
  AI-generated;
- is used within Customer, Project, Discipline, lifecycle, and revision
  boundaries.

Relevant readable context may include current and historical sources,
relationships, missing-input observations, conflicts, assumptions, risks,
reviews, decisions, and reviewed Engineering Memory.

Historical material must be presented as precedent or evidence, not instruction.

## What AI May Never Modify

AI may never autonomously:

- alter Project, Workspace, Customer, plant, area, equipment, tag, document,
  revision, vendor, standard, or calculation facts;
- change source authority, applicability, review state, or effective period;
- resolve a conflict between sources;
- convert an assumption into a confirmed fact;
- declare a required input satisfied;
- approve an exception or claim standards compliance;
- create or revise a human Engineering Decision;
- accept its own recommendation or Human Review;
- overwrite rejection, disagreement, supersession, or history;
- propagate a potential impact into connected engineering objects;
- turn historical precedent into a current rule;
- hide missing information, staleness, uncertainty, or inaccessible evidence.

Human authorization of a later action remains distinct from the AI suggestion
that prompted it.

## Information That Requires Human Review

Human Review is required when engineering meaning, authority, or consequence
cannot be established by direct governed fact alone. Material examples include:

- conflicting sources;
- missing information that affects progress, safety, selection, or review;
- material assumptions;
- standard, specification, or revision applicability;
- Customer-specific interpretations and exceptions;
- unverified vendor data;
- AI-extracted facts or candidate relationships used for engineering;
- AI-generated comparisons, impacts, risks, or missing-input findings;
- cross-discipline interface interpretations;
- stale information proposed for continued use;
- historical precedent proposed as relevant to current work;
- a proposed resolution that changes engineering direction;
- evidence that supports a human decision or plan acceptance.

Routine display of already governed facts does not create a new review need.
Review depth must follow consequence, uncertainty, competence, and existing
approval authority.

## Freshness, Expiry, and Supersession

Not all context ages in the same way.

### Information that may expire

- transient selections and exploratory views;
- AI-generated relevance and similarity assessments;
- derived summaries and completeness assessments;
- vendor offers, provisional data, and time-limited confirmations;
- temporary assumptions;
- stage-dependent applicability;
- working risk assessments;
- information with an explicit validity period.

### Information that becomes stale rather than disappearing

- a derived view after any decisive source changes;
- an AI finding after its source revisions change;
- a missing-input finding after the input arrives;
- a conflict finding after responsible resolution;
- an applicability conclusion after scope, edition, or conditions change;
- a historical comparison when current scope diverges.

### Information that becomes historical

- superseded source revisions;
- prior governed observations;
- reviewed assumptions and their resolution;
- completed or superseded reviews;
- human decisions and later supersession;
- context snapshots;
- prior Project or Workspace conditions material to engineering history.

Expiry does not authorize erasure of material evidence. A record may cease to
be current while remaining necessary for traceability.

## Project, Workspace, Decision, and Plan Boundaries

The following allocation is a semantic boundary for discovery. It does not
define technical ownership or storage.

### Information belonging to Project

Project-level meaning is shared across Disciplines:

- Project and Customer identity;
- common scope, purpose, exclusions, lifecycle, and review stage;
- plant, site, unit, area, and package boundaries shared by the Project;
- common Customer requirements and Project-wide constraints;
- Project-wide source applicability;
- common stakeholders and accountability;
- cross-discipline interfaces;
- shared changes, risks, and questions;
- the authoritative collection boundary for discipline Workspaces;
- current Project conditions relevant to all engineering work.

Project context must not be copied into every Workspace as independent truth.

### Information belonging to Engineering Workspace

Workspace-level meaning is the discipline-bounded view of engineering work:

- governed Discipline and Workspace accountability;
- discipline scope, exclusions, and interpretation;
- relevant systems, equipment, tags, documents, calculations, standards, and
  shared Project relationships;
- discipline-owned inputs and outputs;
- required and missing inputs;
- discipline assumptions, constraints, risks, dependencies, conflicts, and
  open questions;
- cross-discipline interfaces as understood by the accountable Discipline;
- local review needs and current contextual limitations.

The Workspace presents shared engineering objects but does not own or delete
them. Two Workspaces may reference the same object while preserving distinct
discipline responsibility.

### Information belonging to the future Engineering Decision Log

The future Engineering Decision Log owns human judgment evidence:

- what was decided;
- who was accountable for the decision;
- the question or conflict being resolved;
- rationale and Engineering Reasoning;
- alternatives considered;
- evidence, assumptions, requirements, standards, and risks considered;
- affected engineering objects and Workspaces;
- uncertainty and reviewer outcomes;
- effective scope;
- later revision or supersession.

A decision may change which context is applicable, but the Context boundary
must not impersonate the decision or erase the alternatives and prior state.

### Information belonging to the future Engineering Execution Plan

The future Engineering Execution Plan owns the engineer-controlled hypothesis
about how engineering work may proceed:

- suggested phases and activities;
- ordering and dependencies;
- required inputs as plan prerequisites;
- expected deliverables;
- review points;
- potential critical engineering path;
- estimated effort and suggested team roles;
- recommended next actions;
- plan rationale, confidence, review state, versions, and supersession.

Context supplies the plan’s evidence and conditions. The plan interprets those
conditions into proposed movement. A plan item is not an authoritative fact,
and a missing input does not become “planned away.”

## Cross-Discipline Context

Shared context must connect Disciplines without dissolving accountability.

For example, a pump and its Motor Datasheet may be relevant to Process,
Mechanical, Electrical, Instrumentation, and Control Workspaces. The shared
equipment and document remain the same engineering objects. Each Discipline
may have different:

- questions;
- required attributes;
- assumptions;
- dependencies;
- calculations;
- risks;
- outputs;
- review authority.

An interpretation in one Workspace is not automatically authoritative in
another. Cross-discipline changes require visible impact and responsible review,
not silent propagation.

## Context and Engineering Memory

Engineering Context concerns the meaning needed for current or historical work.
Engineering Memory is the governed organizational learning that may be reused
after decisions and outcomes have been reviewed.

Context may read reviewed Memory as bounded precedent. It must preserve:

- the original Customer, Project, plant, Discipline, equipment, and lifecycle
  conditions;
- what was decided and why;
- what later happened;
- review status;
- known exceptions and reuse limits;
- differences from the current situation.

Frequency does not create authority. A repeated historical choice does not
become a rule without governance.

## Context Quality

High-quality Engineering Context is:

- relevant to the current question;
- bounded to the correct Customer, Project, Workspace, Discipline, lifecycle,
  and revision;
- sourced and attributable;
- current enough for its purpose;
- explicit about applicability;
- complete enough to support the claimed conclusion;
- honest about missing information and conflict;
- accessible to the current actor;
- traceable through changes and decisions;
- proportionate, so relevant evidence is visible without burying the engineer.

More information is not necessarily better context. Unbounded retrieval can
reduce safety by mixing customers, revisions, disciplines, stages, or
historical situations.

## Current Domain Baseline

The implemented platform currently establishes:

- Project identity, Customer relationship, lifecycle, ownership, primary
  assignment, priority, dates, and progress;
- one Engineering Workspace identity per Project and governed Discipline;
- Workspace ownership, primary assignment, collaborators, lifecycle,
  archival state, and optimistic concurrency;
- authorization-filtered Project and Workspace discovery;
- centralized audit evidence for current Project and Workspace mutations;
- only the persisted roles `admin` and `engineer`.

The current Workspace Core intentionally does not contain Engineering Context,
Engineering Decision Log, Human Review, Engineering Execution Plan,
Engineering Health, Workspace Readiness, AI Insight, or Engineering Memory
behavior.

This discovery does not change that baseline.

## Domain Tensions Requiring Architectural Review

The governing documents establish principles but leave domain questions that
must be resolved before design. This discovery does not answer them.

1. What minimum set of engineering object kinds is necessary for the first
   useful Context foundation?
2. What makes a contextual relationship authoritative rather than proposed or
   observed?
3. Which missing-input and conflict observations require durable governance,
   and which remain derived?
4. Who may establish standards applicability, Customer interpretations, and
   cross-discipline interface meaning under the current `admin` and `engineer`
   roles?
5. Where is the boundary between an assumption, an open question, a risk, and a
   decision requiring the future Engineering Decision Log?
6. What consequence threshold requires Human Review?
7. When must a context snapshot be preserved, and what is the minimum evidence
   needed for reproducibility?
8. How is freshness judged for different source types without implying false
   precision?
9. How should conflicting but differently authoritative sources remain visible
   without presenting a silent winner?
10. How can cross-Workspace relationships be shared without duplicating truth
    or weakening Discipline accountability?
11. Which historical context is eligible to become reviewed Engineering
    Memory?
12. What context is sufficient before a future Engineering Execution Plan may
    responsibly be proposed?

These questions belong to later architectural analysis and approval.

## Discovery Conclusion

Inside SATCO, Engineering Context is the engineer’s governed frame of meaning.
It connects current work to the right scope, evidence, authority, relationships,
time, uncertainty, and human decisions.

Its purpose is not to make engineering automatic. Its purpose is to make the
basis of engineering work visible, reviewable, traceable, and reusable without
confusing facts with assumptions, current truth with history, AI interpretation
with human authority, or a proposed plan with permission to act.

No implementation or architecture decision is authorized by this discovery.
