# SATCO Engineering Knowledge Model

## Purpose

This document defines the conceptual Engineering Knowledge Model of SATCO. It describes the engineering objects and relationships through which SATCO understands project context, supports reasoning, and preserves organizational memory.

## Scope

The model is a product-governance view of engineering knowledge. It defines meaning and relationships without prescribing database structures, schemas, APIs, or implementation technologies.

## Definitions

- **Engineering object:** A meaningful entity in engineering work, such as equipment, a document, a decision, or a risk.
- **Relationship:** A governed statement connecting engineering objects and explaining dependency, ownership, applicability, history, or impact.
- **Engineering Knowledge Graph:** The connected body of engineering objects, relationships, evidence, and history available for reasoning.
- **Engineering Context:** The subset of connected knowledge relevant to a specific problem, workspace, lifecycle stage, or decision.
- **Engineering Memory:** Reviewed and traceable knowledge retained for future use.

## Knowledge Philosophy

Engineering meaning rarely exists in an isolated item. A tag matters because it identifies equipment in a system and appears in documents, calculations, loops, panels, and decisions. A standard matters because it applies to a customer, location, discipline, package, or lifecycle stage. A decision matters because it resolves a question, has an owner and rationale, affects connected work, and may later be revised.

SATCO therefore treats relationships as first-class engineering meaning. The Knowledge Graph is not a collection of files or extracted text. It is a governed representation of how engineering work fits together.

## Core Engineering Objects

### Organizational and Project Context

- **Customer:** The organization whose requirements, standards, operating expectations, and acceptance processes shape the work.
- **Project:** The governed engineering undertaking that provides common scope, lifecycle, ownership, and objectives.
- **Plant:** The operating facility or industrial context in which engineered systems exist.
- **Area:** A meaningful physical, operational, or organizational subdivision of a plant or project.
- **Discipline:** A professional engineering domain responsible for particular analyses, decisions, and deliverables.
- **Engineering Workspace:** The discipline-oriented environment in which relevant project knowledge, work, risks, reviews, and decisions are brought together.

### Functional and Physical Context

- **System:** A set of interacting elements that performs an engineering function.
- **Equipment:** A physical or functional asset with engineering requirements and lifecycle significance.
- **Tag:** A governed identifier connecting an engineering object across disciplines and records.
- **Cable:** A connection whose characteristics and endpoints create electrical, control, installation, and documentation dependencies.
- **Panel:** An assembled engineering object that groups devices, interfaces, power, control, and documentation relationships.
- **IO:** An input or output point connecting field behavior, control functions, signals, equipment, and system logic.
- **Loop:** A functional chain linking measurement, control, equipment, IO, documents, and operational intent.

### Authority and Evidence

- **Vendor:** An external source of equipment, technical information, constraints, and revisions.
- **Standard:** A governed source of requirements or guidance whose applicability and edition must be established.
- **Document:** A controlled carrier of engineering information, evidence, communication, or deliverable content.
- **Calculation:** A reasoned engineering analysis with inputs, assumptions, method, result, revision, and review status.
- **Revision:** A defined state in the history of an engineering object or record.

### Governance and Learning

- **Decision:** A human-owned conclusion with rationale, evidence, scope, status, and consequences.
- **Risk:** An uncertain condition with potential engineering consequence, likelihood, ownership, and response.
- **Review:** A governed evaluation of engineering information, recommendations, or decisions.
- **Lesson Learned:** A reviewed conclusion from experience that may inform future work within stated boundaries.
- **Engineering Memory:** The durable, traceable body of reviewed decisions, outcomes, revisions, and lessons.
- **Engineering Execution Plan:** The evolving, AI-suggested engineering roadmap connecting scope, phases, inputs, risks, deliverables, effort, and next steps.

## Foundational Relationships

The model supports relationships such as:

- a Customer sponsors or governs Projects;
- a Project applies to a Plant and contains Areas;
- a Project includes discipline Engineering Workspaces;
- an Area contains Systems and Equipment;
- Equipment and other objects are identified by Tags;
- Systems connect Equipment, Cables, Panels, IO, and Loops;
- Vendors supply Equipment and Documents;
- Standards apply to Projects, Disciplines, Equipment, Documents, and Calculations;
- Documents describe, specify, verify, or revise engineering objects;
- Calculations evaluate requirements and support Decisions;
- Decisions resolve questions and affect connected objects;
- Risks arise from uncertainty, conflict, change, or missing information;
- Reviews evaluate Documents, Calculations, recommendations, and Decisions;
- Revisions supersede or modify prior states without erasing history;
- Lessons Learned derive from reviewed outcomes;
- Engineering Memory preserves governed knowledge for responsible reuse;
- the Engineering Execution Plan responds to current scope, readiness, risk, and decisions.

These relationships may be direct or mediated through other objects. Their authority, time, revision, and review status are part of their meaning.

## Why Relationships Matter

Relationships enable SATCO to:

- assemble relevant context before AI reasoning;
- trace a requirement from authority to affected engineering work;
- detect inconsistent values across documents and disciplines;
- estimate the possible impact of a change;
- identify missing inputs and unresolved reviews;
- distinguish current information from superseded information;
- explain why a historical project may or may not be comparable;
- connect decisions to their evidence and later consequences;
- evaluate workspace readiness and Engineering Health;
- preserve knowledge beyond individual people and projects.

Without relationships, AI can retrieve text but cannot reliably understand engineering consequence.

## Context and Boundaries

The Knowledge Graph must preserve boundaries. Information relevant to one customer, project stage, plant environment, standard edition, or equipment class must not be assumed applicable elsewhere.

Every use of connected knowledge should consider:

- project and customer applicability;
- discipline ownership;
- physical and functional scope;
- lifecycle stage;
- revision and effective time;
- authority and review status;
- known exceptions;
- missing or conflicting links.

## Engineering Memory

Engineering Memory is the governed learning layer of the Knowledge Graph. It should retain:

- what was decided;
- who owned the decision;
- why it was decided;
- which evidence and assumptions were used;
- what was affected;
- how the outcome was reviewed;
- what later happened;
- what lesson is safe to reuse;
- where that lesson does not apply.

Memory must preserve disagreement, supersession, and uncertainty where they are material. It must not convert repeated behavior into a rule without review.

## Engineering Execution Plan Relationships

The Engineering Execution Plan draws from the graph to suggest:

- phases appropriate to scope and discipline;
- required inputs and their availability;
- expected deliverables and dependencies;
- risks, reviews, and critical engineering paths;
- suitable historical comparisons;
- estimated effort, team needs, and confidence;
- the recommended next engineering step.

As decisions, revisions, risks, and readiness change, the plan should evolve while preserving its prior rationale.

## Design Rules

1. Represent engineering meaning through explicit relationships, not inferred proximity alone.
2. Preserve source, authority, revision, time, and review status.
3. Distinguish fact, inference, recommendation, decision, and lesson.
4. Do not erase superseded knowledge when it is needed to understand history.
5. Keep customer, project, discipline, and lifecycle boundaries visible.
6. Treat missing and conflicting relationships as engineering findings.
7. Require human governance before AI output becomes Engineering Memory.
8. Support multidisciplinary impact without removing discipline ownership.
9. Explain similarity and difference before historical reuse.
10. Make every material relationship traceable to evidence or accountable review.

## Examples

### Change Impact

A revised equipment requirement may relate to a calculation, cable selection, panel design, vendor document, control loop, and prior decision. SATCO should show known and potential impacts, identify unassessed areas, and recommend review rather than declaring the change complete.

### Standards Applicability

A standard may be associated with a customer and discipline, but its edition may differ from the project’s contractual basis. The relationship allows SATCO to expose the discrepancy and request confirmation rather than assume applicability.

### Historical Learning

A prior project may share equipment type and discipline but differ in plant environment and customer requirements. SATCO may suggest it as a partial analogue while clearly identifying the limits of comparison.

## Future Implications

Future product capabilities should strengthen the completeness, governance, and usefulness of these relationships. Expansion of the knowledge model must be driven by engineering value and remain consistent with context-first AI, traceability, human review, and the Engineering Copilot responsibility boundary.
