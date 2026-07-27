# Engineering Context Object (ECO) Discovery

## Status

Domain Discovery — Awaiting Architectural Review

This document explores whether Engineering Context Object, abbreviated ECO,
should become a permanent SATCO architectural concept.

It is not a PATCH, ADR, EDS, implementation specification, database design, or
authorization to change product behavior.

## Documents Reviewed

- `docs/adr/ADR-015-Engineering-Context-Domain-Architecture.md`
- `docs/adr/ADR-014-Engineering-Workspace-Domain-Model.md`
- `docs/10_Engineering_Philosophy.md`
- `docs/14_Engineering_Knowledge_Model.md`
- `docs/17_SATCO_Product_Blueprint.md`
- `docs/discovery/PATCH-020.2-Engineering-Context-Discovery.md`
- `docs/reviews/PATCH-020.2-Discovery-Architecture-Review.md`

## Discovery Question

> Should Engineering Context Object become a permanent architectural concept
> inside SATCO?

The short answer is:

> ECO is useful explanatory terminology, but the current evidence does not
> justify it as a permanent architectural concept.

The reasons are developed below.

## Existing Canonical Concepts

SATCO already distinguishes:

- **Engineering object:** a meaningful entity in engineering work, such as
  equipment, a document, a calculation, a decision, or a risk;
- **Relationship:** a governed statement connecting engineering objects and
  explaining dependency, ownership, applicability, history, or impact;
- **Engineering Knowledge Graph:** the connected body of engineering objects,
  relationships, evidence, and history available for reasoning;
- **Engineering Context:** the bounded subset of connected knowledge relevant
  to a specific Project, Workspace, problem, lifecycle stage, review, or
  decision.

ADR-015 further establishes that Context is multidimensional. Authority,
derivation, temporality, review state, maturity, freshness, criticality,
confidentiality, source, and scope qualify contextual meaning without forcing
all information into one type.

Any ECO concept must add meaning beyond these established terms. A new name is
not justified merely because later design needs to refer to “something in
Context.”

## 1. What Is an Engineering Context Object?

As explanatory terminology, an ECO can mean:

> A context-bearing engineering subject, assertion, condition, relationship,
> or evidence reference considered within a bounded Project, Workspace,
> Discipline, question, review, or decision.

This wording is intentionally broad. It can help a discussion refer
collectively to things such as:

- an equipment item relevant to a Workspace;
- a sourced motor-power assertion;
- an applicable Customer requirement;
- a missing-input condition;
- a cross-discipline Interface Commitment;
- a reviewed calculation result;
- a historical source revision.

However, those examples do not share one native domain nature. Some are
entities, some are assertions, some are relationships, some are conditions,
and some are evidence.

ECO therefore describes participation in Engineering Context. It does not yet
define a coherent kind of engineering thing.

## 2. What Is Not an ECO?

ECO must not be used to rename or absorb:

- Project;
- Engineering Workspace;
- Customer;
- Discipline;
- an entire Engineering Context;
- Engineering Decision Log;
- Engineering Execution Plan;
- Engineering Health or Workspace Readiness;
- AI Insight or ENSE recommendation;
- Engineering Memory;
- Engineering Knowledge Graph;
- document repository;
- chat message;
- generic note;
- task or workflow item;
- database record;
- API payload;
- universal metadata envelope.

An engineering object is not automatically an ECO merely because it exists.
It becomes contextual only when its relevance and scope are established.

Likewise, a source document, risk, decision, or calculation retains its own
domain identity. Calling it an ECO must not erase that identity.

## 3. What Kind of Concept Is ECO?

Four possibilities were evaluated.

### Permanent architectural concept

A permanent concept would need one stable definition, domain responsibility,
identity rule, lifecycle boundary, ownership meaning, and relationship to
other accepted aggregates.

The evidence does not currently support that level of unity. The proposed ECO
examples have materially different identities and lifecycles.

### Domain pattern

ECO can describe a recurring pattern:

> Engineering meaning enters Context through a bounded subject, claim,
> condition, relationship, or evidence reference qualified by ADR-015
> dimensions.

This is useful, but it remains a pattern of contextual participation rather
than a new domain object.

### Implementation entity

ECO is not an implementation entity. This discovery neither requires nor
supports one universal entity for all Context information.

Turning the term directly into an implementation entity would risk recreating
the rejected single Context blob in a more fragmented form: one generic
record type containing everything and explaining little.

### Explanatory terminology

ECO is presently best understood as optional explanatory terminology. It can
help architecture discussions refer to a candidate unit of contextual meaning
without presuming how that meaning is represented.

This use must remain subordinate to the native domain terms.

## 4. Can Every Engineering Fact Be Represented as One or More ECOs?

If ECO is defined broadly enough, almost any engineering fact could be
described as one or more ECOs.

That possibility is not a sufficient reason to do so.

For example, “Motor M-101 rated power is 160 kW according to Vendor Datasheet
revision B” contains:

- a motor engineering object;
- a rated-power quantity;
- a value and unit;
- a claim or assertion;
- a vendor document source;
- a document revision;
- an applicability scope;
- potentially a review state and maturity.

Flattening all of that into “an ECO” does not necessarily improve the domain.
It may conceal the distinction between the motor, the claim about the motor,
and the evidence supporting the claim.

Every engineering fact can participate in Engineering Context. It does not
follow that every fact should be converted into a universal Context object.

## 5. Does ECO Have Identity?

There is no single defensible ECO identity rule.

- Equipment may have durable engineering identity.
- An Instrument Tag is itself a governed identifier.
- A document has controlled identity and revisions.
- A value assertion may need identity only for provenance and change history.
- Missing Information is identified by the required meaning and affected
  purpose.
- An Interface Commitment is identified through provider, consumer, required
  information, and scope.
- A historical reference retains the identity of its native source.

ECO can point to context-bearing identity, but it does not supply one universal
identity of its own.

Creating a new ECO identity in addition to native identity could produce
duplicate or competing identity.

## 6. Does ECO Have Lifecycle?

There is no universal ECO lifecycle.

ADR-015 explicitly rejects one lifecycle for all Context information.

- Equipment has an asset or engineering lifecycle.
- A document has revision and issue history.
- An assumption may be proposed, reviewed, confirmed, rejected, or superseded.
- Missing Information may be identified and later resolved.
- A risk may be open, treated, accepted, closed, or otherwise governed by its
  own future domain.
- A value assertion may become stale or superseded when its source changes.

ECO can carry lifecycle meaning from the native subject or contextual
condition. It should not impose a replacement lifecycle.

## 7. Does ECO Have Authority?

ECO does not possess authority merely by being called an ECO.

Authority belongs to the bounded information and the governed source or human
process supporting it.

An ECO-like item might be:

- source-authoritative;
- engineer-verified;
- an explicit assumption;
- a derived finding;
- an AI suggestion;
- a historical reference;
- an unresolved conflict;
- missing information.

Authority is a dimension of the contextual meaning, not an inherent status
granted by ECO identity.

Confidence never creates ECO authority. AI origin never creates ECO authority.

## 8. Does ECO Have History?

Contextual meaning may have history, but not all ECO-like things require the
same historical treatment.

History may belong to:

- the engineering object;
- its source revisions;
- assertions made about it;
- review outcomes;
- corrections;
- supersession;
- conflicts;
- snapshots;
- decisions that changed applicability.

Material history must remain traceable. Transient contextual selections may
expire without becoming engineering history.

ECO can be a way to discuss historical context-bearing meaning. It does not
define one historical model.

## 9. Does ECO Have Ownership?

There is no universal ECO owner.

Relevant responsibilities may include:

- information owner;
- source owner;
- engineering steward;
- Project owner;
- Workspace owner;
- primary assignee;
- reviewer;
- approver where a governed approval process exists.

The native subject and the contextual use may have different accountable
people. For example, Mechanical may steward motor data while Electrical is
accountable for its use in electrical work.

Calling both responsibilities ECO ownership would obscure cross-discipline
accountability. Ownership also remains distinct from competence.

## 10. Does ECO Have Source?

Every material contextual assertion, interpretation, condition, or reference
needs known provenance where a source is applicable.

Potential sources include:

- Customer or contract evidence;
- approved Project documents;
- vendor documents;
- site surveys;
- standards;
- calculations;
- engineer input;
- external references;
- historical Projects;
- AI-derived interpretation.

Some engineering objects are subjects rather than claims and therefore are not
“sourced” in the same way. Their attributes, relationships, and revisions still
require provenance.

ECO does not replace the native source or source-precedence rules.

## 11. Does ECO Have Review State?

An ECO-like contextual item may have a review state when review is meaningful.

Examples include:

- an AI-derived missing-input finding awaiting engineer review;
- a vendor value verified for bounded use;
- an assumption needing more information;
- a disputed source relationship;
- a rejected interpretation.

Other things, such as Project identity or a controlled document revision, may
expose the review state of their native domain rather than receive a second ECO
review state.

ECO therefore does not require one universal review state. Review attaches to
the defined subject, version, scope, and review question.

## 12. Does ECO Have Maturity?

Context-bearing information may have maturity, but maturity does not apply
uniformly.

- A vendor document may be preliminary.
- A calculation may be in development or verified.
- A design basis may be approved for use.
- A missing-input condition is not “preliminary” in the same sense.
- A historical reference may preserve the maturity it had at the time.

Maturity remains independent of authority, review, freshness, and formal
approval.

ECO does not justify one common maturity model across all native domains.

## 13. Does ECO Have Freshness?

Freshness applies to contextual use, not to the ECO label.

A source, value, interpretation, or relationship may be:

- current for one purpose;
- stale for another;
- superseded by revision;
- invalidated by a dependency change;
- expired by a governed condition;
- historical but still authentic.

Freshness depends on information type, source, Project stage, revision,
criticality, dependencies, and purpose.

An ECO abstraction must not create one universal age or expiry rule.

## 14. Does ECO Have Criticality?

Contextual information may have criticality based on the consequence of being
wrong, absent, stale, conflicted, misunderstood, or inaccessible.

Criticality can influence:

- review priority;
- visibility;
- freshness expectations;
- audit significance;
- AI caution;
- snapshot justification.

The criticality belongs to the contextual use and consequence. The same source
may have different criticality in different engineering questions.

ECO does not create one universal criticality score.

## 15. Is ECO Independent of Storage Technology?

Engineering meaning is independent of storage technology.

Equipment, requirements, assertions, conditions, evidence, and relationships
remain meaningful whether represented in structured data, controlled
documents, reviewed calculations, or future approved relationship
technologies.

ECO can therefore be discussed without choosing a database, schema, API, or
Knowledge Graph technology.

Technology independence alone does not make ECO a necessary architectural
concept. Existing Engineering Context and Engineering Knowledge Model concepts
already provide that independence.

## Relationship to Project

Project establishes shared identity, Customer, scope, lifecycle, common
requirements, and the collection boundary for Workspaces.

An ECO-like contextual item may be Project-scoped, but it does not duplicate
the Project. Project facts retain Project ownership and are referenced where
relevant.

ECO must not become a parallel Project metadata system.

## Relationship to Engineering Workspace

Workspace establishes Project/Discipline identity and accountable discipline
coordination.

An ECO-like item may appear in a Workspace because it is relevant to that
Discipline. Relevance does not transfer ownership of shared equipment,
documents, requirements, or other engineering objects to the Workspace.

The same source may participate in several Workspaces with different questions,
criticality, assumptions, and review needs.

## Relationship to Engineering Context

Engineering Context is the bounded body of relevant meaning.

ECO, if used explanatorily, refers to one candidate context-bearing subject,
assertion, condition, relationship, or evidence reference within that body.

Engineering Context is not simply a bag of ECOs. Relationships, boundaries,
source standing, missing meaning, and the question being considered are part
of Context itself.

## Relationship to Engineering Decision Log

The future Engineering Decision Log owns human decisions, rationale,
alternatives, evidence, authority, affected scope, and supersession.

A decision may be relevant Context. It does not become a generic ECO whose
native decision meaning is lost.

ECO must not mix raw input with the human conclusion drawn from that input.

## Relationship to Engineering Execution Plan

The future Engineering Execution Plan consumes Context and proposes phases,
activities, dependencies, deliverables, effort, roles, and next steps.

Plan items are not ECOs merely because they refer to Context. A required input
may be contextual; the proposed action to obtain it belongs to the plan.

ECO must not turn Context into planning or task state.

## Relationship to AI Insights

AI Insights are advisory findings linked to governed Context.

An AI-produced interpretation may be described as an ECO-like item for
discussion, but it remains an AI Insight or AI-generated Context with its own
provenance, uncertainty, review, freshness, and supersession.

ECO never grants AI output authority.

## Relationship to ENSE

ENSE uses Context to recommend possible next actions.

Recommended Next Steps are advisory records, not Context facts. Their evidence
may reference ECO-like contextual items, but the recommendation itself does
not become authoritative Context.

ECO must not become a generic action or task.

## Relationship to Engineering Memory

Engineering Memory preserves reviewed decisions, outcomes, revisions, and
lessons for governed reuse.

Historical ECO-like information is not automatically Memory. Memory requires
reviewed meaning, known original context, outcome, and reuse limits.

ECO must not become an AI memory dump or a shortcut around Memory governance.

## Relationship to Engineering Knowledge Graph

The Knowledge Graph connects engineering objects, relationships, evidence, and
history.

ECO could be used informally to describe something participating in those
relationships. It does not define a graph node, edge, property, or technology.

Making every graph participant an ECO would add a generic layer over the
existing Engineering Knowledge Model without demonstrated domain value.

## Relationship to Documents

Documents are controlled carriers of engineering information and evidence.

A Vendor Datasheet may be relevant Context, but the document remains a
Document with revisions, ownership, and applicability. Individual claims
derived from it must preserve that source.

ECO must not make Documents the primary Context model or duplicate document
identity.

## Example Evaluation

The evaluation asks two separate questions:

1. Can the example participate in Engineering Context?
2. Does it benefit from becoming a permanent ECO concept?

### Equipment

**Context participation:** Yes. Equipment is central to scope, requirements,
tags, documents, calculations, risks, and decisions.

**ECO assessment:** Equipment is already a canonical engineering object. It
does not need to become an ECO. Context should reference the equipment and
qualify its relevance.

### Instrument Tag

**Context participation:** Yes. A tag connects an engineering object across
Disciplines and records.

**ECO assessment:** A Tag is an existing canonical engineering object and
governed identifier. Calling it an ECO risks duplicate identity.

### Motor Rated Power

**Context participation:** Yes, when connected to the motor, value, unit,
quantity meaning, condition, source, revision, applicability, and review.

**ECO assessment:** This is a contextual assertion or qualified engineering
value, not the same kind of object as the motor. ECO is useful shorthand in
discussion but adds no proven permanent identity.

### Cable Size

**Context participation:** Yes, with cable identity, size meaning, material or
construction basis where relevant, source, calculation or selection basis,
revision, and review state.

**ECO assessment:** It is a qualified property or engineering selection about
a cable. It should not be confused with the cable engineering object itself.

### Vendor Datasheet

**Context participation:** Yes, as source and evidence with vendor, equipment,
revision, maturity, restrictions, and applicability.

**ECO assessment:** It remains a Document. ECO must not duplicate its
controlled identity or revision history.

### Customer Requirement

**Context participation:** Yes, with Customer, source, contractual standing,
scope, applicability, precedence, revision, and exceptions.

**ECO assessment:** It may eventually be a requirement object or governed
assertion. ECO does not determine that native domain.

### Engineering Assumption

**Context participation:** Yes. It must be explicit, bounded, human-owned,
reviewable, and connected to consequence and confirmation conditions.

**ECO assessment:** This is one of the strongest ECO-like examples because it
is a governed contextual condition. Even so, its assumption semantics are more
important than a generic ECO label.

### Engineering Risk

**Context participation:** Yes, where relevant to the question or Workspace.

**ECO assessment:** Risk is a canonical engineering object with ownership,
consequence, response, and review meaning. It should not be reduced to ECO.

### Missing Information

**Context participation:** Yes. ADR-015 makes it a first-class engineering
condition with requirement basis, scope, owner, criticality, consequence, and
resolution condition.

**ECO assessment:** It is ECO-like because it is contextual meaning rather than
a physical object. Its first-class Missing Information semantics must remain
visible.

### Interface Commitment

**Context participation:** Yes. It connects provider, consumer, required
information, due condition, status, source, criticality, review, and impact.

**ECO assessment:** It is a governed relationship or dependency, not merely an
object. A universal ECO model could conceal that relational meaning.

### Design Temperature

**Context participation:** Yes, with value, unit, quantity type, design basis,
reference condition, scope, source, revision, and uncertainty.

**ECO assessment:** It is a qualified engineering value or assertion.
Explanatory ECO terminology is possible but not necessary.

### Pressure

**Context participation:** Yes only when pressure type, value, unit, normal or
design condition, reference basis, location, time, source, revision, and
uncertainty are sufficiently clear.

**ECO assessment:** “Pressure” alone is not a complete Context object. This
example demonstrates why a generic ECO identity cannot substitute for
engineering semantics.

### Standard Reference

**Context participation:** Yes, with standard identity, edition, authority,
jurisdiction, Customer or contractual obligation, scope, applicability, and
exceptions.

**ECO assessment:** The Standard remains an engineering object or source; the
reference and applicability are relationships or governed assertions. ECO must
not collapse them.

### Calculation Result

**Context participation:** Yes, with calculation identity, inputs,
assumptions, method, value, unit, conditions, revision, uncertainty, and review
state.

**ECO assessment:** It remains a result of a Calculation and a qualified
assertion. ECO should not detach it from the calculation or create a parallel
result identity.

## Cross-example Finding

All listed examples can participate in Engineering Context.

They divide into materially different kinds:

- established engineering objects;
- qualified values or assertions;
- sources and evidence;
- governed conditions;
- governed relationships;
- historical or advisory interpretations.

That diversity is exactly why ECO is attractive as shorthand and dangerous as
a permanent universal object.

## Potential Benefits of ECO Terminology

Used carefully, ECO can:

- provide a neutral phrase during early Context discussions;
- remind reviewers that engineering meaning can be smaller than a complete
  document and broader than a raw value;
- emphasize that Context participants need source, scope, authority, time,
  review, maturity, freshness, criticality, and confidentiality where relevant;
- help compare candidate first-release Context concepts without deciding
  implementation.

## Risks of Permanent ECO Architecture

A permanent ECO concept could:

- create a universal meta-object over distinct native domains;
- duplicate identity for equipment, tags, documents, calculations, risks, and
  decisions;
- flatten relationships into object-like records;
- encourage every fact to become an isolated atom;
- obscure the difference between subject, assertion, source, and evidence;
- imply one lifecycle, ownership model, or review state despite ADR-015;
- turn Context into a generic property bag;
- make implementation shape the domain before the minimum Context boundary is
  understood;
- compete with the canonical Engineering Knowledge Model;
- invite premature Knowledge Graph node design.

## Criteria That Could Justify Reconsideration

ECO could be reconsidered as a permanent concept only if later domain work
demonstrates all of the following:

- a stable responsibility not already owned by engineering objects,
  relationships, Context conditions, sources, reviews, or decisions;
- a coherent identity rule;
- a coherent history and correction boundary;
- clear ownership and stewardship;
- clear distinction from native domain identity;
- improved engineering traceability or safety;
- usefulness across multiple Disciplines without flattening their meaning;
- compatibility with ADR-015 dimensions and non-universal lifecycles;
- clear Product Bible value beyond implementation convenience.

No such evidence currently exists.

## Conclusion

### Decision

**B. ECO should remain only explanatory terminology.**

### Reasoning

Engineering Context needs identifiable, traceable units of meaning, but those
units do not form one homogeneous domain object.

Some are engineering objects. Some are assertions about objects. Some are
sources, evidence, relationships, missing conditions, conflicts, assumptions,
or advisory interpretations. Their identity, lifecycle, ownership, authority,
history, review, maturity, freshness, and criticality come from their native
meaning and contextual use.

Creating ECO as a permanent architectural concept now would add a generic
abstraction without a unique domain responsibility. It could weaken the
distinctions ADR-015 was created to protect.

ECO may be used carefully in discussion to mean “a candidate context-bearing
unit of engineering meaning.” It must not appear as a canonical aggregate,
universal object, or implied implementation entity unless future evidence
passes a separate architecture review.

The preferred permanent language remains:

- engineering object;
- relationship;
- source or evidence;
- qualified assertion or value;
- governed Context condition;
- Engineering Context;
- Engineering Knowledge Graph.

No architecture or implementation change is authorized by this discovery.
