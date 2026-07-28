# EDS-030 Technical Proposal Review

## Status

Draft

## Purpose

Define the product and engineering design direction for the SATCO Technical
Proposal Review capability.

The capability shall assist authorized Human engineers in reviewing technical
proposals, identifying missing information, deviations, ambiguities,
inconsistencies, risks, and clarification requirements.

The capability shall support both:

1. SATCO Engineering while delivering engineering services to its Customers.
2. External engineering organizations using SATCO Platform for their own
   internal technical evaluations.

The capability shall remain operator-neutral and shall not require separate
internal and commercial implementations.

## Product Vision

Technical Proposal Review shall become a governed engineering-review
capability operating over authorized, traceable, Project-scoped Engineering
Context.

The capability shall help engineering teams answer questions such as:

- Does the proposal satisfy the stated technical requirements?
- Which requirements have not been answered?
- Which Vendor statements differ from the approved Project basis?
- Which assumptions require clarification?
- Which deviations may affect design, procurement, installation, operation,
  maintenance, safety, reliability, or lifecycle cost?
- Which supporting documents, calculations, drawings, certificates, or
  references are missing?
- Which findings require Human engineering review before acceptance?

Technical Proposal Review shall provide evidence and recommendations. It shall
not autonomously approve, reject, purchase, award, or technically accept a
proposal.

## Operating Models

### SATCO Engineering

SATCO Engineering may use the capability to:

- receive Customer technical-review requests;
- organize Project requirements;
- review Vendor or Contractor proposals;
- prepare technical findings;
- prepare clarification questions;
- support Technical Bid Evaluation;
- issue governed engineering-review outputs after Human approval.

### External Engineering Organizations

External organizations may use the same capability to:

- review EPC, Contractor, Supplier, or Vendor proposals;
- coordinate multiple engineering disciplines;
- identify proposal deviations and missing responses;
- manage technical clarifications;
- compare proposals;
- support internal approval workflows;
- preserve review evidence and accountability.

Both operating models shall use the same domain, service, authorization, audit,
review, and traceability architecture.

## Inputs

The capability may consume authorized Project information including:

- Purchase Requisition;
- Material Requisition;
- Indent;
- technical inquiry;
- Scope of Work;
- Design Basis;
- equipment or package Datasheet;
- Project Specification;
- engineering standard;
- Client requirement;
- Vendor Technical Proposal;
- Contractor Technical Proposal;
- compliance statement;
- deviation list;
- exclusion list;
- clarification response;
- drawing;
- calculation;
- catalogue;
- certificate;
- test report;
- technical correspondence;
- approved Engineering Context;
- Interface Commitment;
- Human Review evidence.

Input support shall be introduced through separately approved implementation
PATCHes. This EDS does not authorize document ingestion or AI extraction.

## Review Subjects

Technical Proposal Review may evaluate subjects such as:

- equipment;
- package;
- instrument;
- electrical system;
- control system;
- mechanical system;
- process system;
- material;
- service;
- engineering deliverable;
- Vendor commitment;
- Contractor commitment;
- interface;
- installation requirement;
- commissioning requirement;
- operation and maintenance requirement.

Future domain expansion shall remain bounded and separately approved.

## Core Review Concepts

### Requirement

A Requirement is an authorized, traceable technical expectation derived from
an approved Project source.

A Requirement shall retain:

- identity;
- Project scope;
- source reference;
- subject;
- discipline;
- requirement statement;
- authority level;
- applicability;
- revision;
- lifecycle;
- confidentiality;
- traceability.

### Proposal Response

A Proposal Response represents how a Vendor or Contractor addresses a governed
Requirement.

A Proposal Response may indicate:

- explicit compliance;
- partial compliance;
- deviation;
- alternative solution;
- exclusion;
- assumption;
- clarification;
- unanswered requirement;
- unsupported claim;
- conflicting response.

### Review Finding

A Review Finding is a governed observation requiring Human assessment.

Potential finding classifications include:

- compliant;
- partially compliant;
- non-compliant;
- missing information;
- deviation;
- ambiguity;
- contradiction;
- clarification required;
- unsupported statement;
- insufficient evidence;
- interface risk;
- lifecycle risk;
- safety concern;
- operability concern;
- maintainability concern;
- constructability concern;
- document inconsistency;
- alternative proposed;
- Human Review required.

Final classification vocabularies shall be defined through an accepted IDS.

### Evidence

Every material finding shall reference the evidence used to produce it.

Evidence may include:

- source document;
- document revision;
- page or section;
- requirement identity;
- proposal response;
- approved Context;
- applicable standard;
- calculation;
- drawing reference;
- Human note;
- review decision.

No finding shall be treated as approved engineering truth solely because it was
generated by AI.

### Clarification

A Clarification is a governed question or response intended to resolve missing,
ambiguous, contradictory, or technically insufficient information.

Clarifications shall retain traceability to:

- Proposal;
- Requirement;
- Review Finding;
- discipline;
- responsible party;
- status;
- response;
- Human reviewer;
- final resolution.

### Technical Evaluation

A Technical Evaluation is a governed Human-approved review outcome constructed
from Requirements, Proposal Responses, Findings, Evidence, Clarifications, and
authorized engineering judgment.

## Intended Outputs

Future approved implementation may produce:

- compliance matrix;
- requirement-response matrix;
- deviation register;
- missing-information register;
- clarification list;
- technical risk register;
- discipline review summary;
- Vendor comparison;
- technical evaluation draft;
- recommendation draft;
- evidence package;
- review history;
- Human-approved Technical Bid Evaluation output.

Outputs shall clearly distinguish:

- source facts;
- Vendor statements;
- deterministic validation;
- AI-generated suggestions;
- Human-reviewed findings;
- approved engineering decisions.

## Human Review Boundary

Human engineering authority is mandatory.

The capability shall not:

- approve a proposal autonomously;
- reject a proposal autonomously;
- select a Vendor autonomously;
- issue final engineering acceptance;
- replace accountable discipline review;
- promote an AI finding into an approved decision without Human action;
- conceal uncertainty or missing evidence;
- mutate approved Project Context without authorization.

AI-generated findings shall remain suggestions until explicitly reviewed and
accepted by an authorized Human engineer.

## AI Role

Future AI capabilities may assist with:

- extracting candidate requirements;
- locating proposal responses;
- matching requirements and responses;
- identifying unanswered requirements;
- identifying candidate deviations;
- identifying inconsistencies;
- proposing clarification questions;
- summarizing technical risk;
- comparing multiple proposals;
- drafting review commentary;
- suggesting evidence references.

AI shall operate only through an authorized Context read boundary and approved
AI execution architecture.

AI shall not bypass confidentiality, Project isolation, Workspace isolation,
authority, audit, Human Review, or source-traceability controls.

## Context Integration

Technical Proposal Review shall consume governed Engineering Context rather
than creating an independent source of truth.

The capability shall integrate with future approved capabilities including:

- Core Context;
- Context Relationships;
- Interface Commitments;
- Derived Context;
- Missing Information;
- Conflict Detection;
- Engineering Memory;
- Decision Log;
- Human Review;
- authorized AI Context retrieval.

Technical Proposal Review shall not silently mutate those domains.

## Multidiscipline Support

The capability shall be discipline-neutral at the platform level.

Initial or future discipline support may include:

- process;
- mechanical;
- piping;
- electrical;
- instrumentation;
- control;
- civil;
- structural;
- safety;
- QA/QC;
- document control;
- procurement engineering.

Discipline-specific rules, templates, standards, and review logic shall be
introduced through separately governed extensions.

## Proposal Comparison

Future implementation may compare multiple proposals against the same
Requirement set.

Comparison may include:

- compliance coverage;
- deviations;
- exclusions;
- unanswered requirements;
- evidence quality;
- technical risks;
- alternative solutions;
- interface impacts;
- maintainability;
- operability;
- lifecycle considerations.

Commercial price comparison is outside this EDS unless separately approved.

## Authorization and Confidentiality

The capability shall preserve:

- Project isolation;
- organization isolation;
- Workspace scope;
- discipline responsibility;
- restricted-document confidentiality;
- reviewer authority;
- source non-disclosure;
- protected identifiers;
- least-privilege access;
- auditability.

Unauthorized Users shall not infer protected information through:

- result counts;
- pagination totals;
- finding identifiers;
- document references;
- proposal existence;
- comparison results;
- clarification status;
- AI output.

## Audit and Traceability

Governed actions shall be auditable.

Future audit obligations may include:

- proposal registration;
- requirement set creation;
- response mapping;
- finding creation;
- finding revision;
- finding acceptance;
- finding rejection;
- clarification creation;
- clarification response;
- review assignment;
- Human decision;
- evaluation revision;
- final approval;
- withdrawal;
- supersession.

Audit events and domain mutations shall remain transactionally consistent.

## Lifecycle Direction

Future implementation shall define explicit lifecycles for:

- Proposal;
- Requirement;
- Proposal Response;
- Review Finding;
- Clarification;
- Technical Evaluation.

Lifecycle states shall be finite, auditable, and protected by optimistic
concurrency.

No lifecycle vocabulary is authorized by this EDS alone.

## Non-Scope

This EDS does not authorize implementation of:

- document upload;
- OCR;
- document parsing;
- AI extraction;
- AI finding creation;
- Requirement storage;
- Proposal storage;
- Review Finding storage;
- clarification workflow;
- Technical Bid Evaluation generation;
- Vendor scoring;
- commercial evaluation;
- procurement award;
- autonomous approval;
- frontend screens;
- API endpoints;
- database migrations;
- notification;
- task scheduling;
- email integration;
- ERP integration;
- document-management integration;
- Knowledge Graph implementation;
- Human Review implementation;
- AI Workforce implementation.

Each capability requires its own accepted IDS, Implementation Plan, IRR, and
implementation authorization.

## Architectural Principles

### Operator Neutrality

The capability shall support SATCO Engineering and external engineering
organizations through the same product architecture.

### Context First

Review shall be based on governed Project Context and traceable evidence.

### Human Authority

Human engineers remain responsible for engineering judgment and approval.

### Evidence Before Conclusion

Material findings shall retain supporting evidence and source references.

### No Silent Promotion

AI or automated findings shall not become approved engineering decisions
without explicit Human Review.

### Bounded Scope

Every future implementation PATCH shall define a narrow capability boundary.

### No Code Forks

SATCO-internal and external-customer usage shall not require separate
implementations.

## Success Criteria for Future Delivery

The capability shall eventually be considered product-ready only when:

- authorized requirements can be established;
- proposal responses can be traced to requirements;
- missing responses can be detected;
- deviations can be represented;
- findings retain evidence;
- clarifications retain lifecycle and responsibility;
- confidentiality is enforced;
- cross-Project access is denied;
- Human Review is explicit;
- AI output is distinguishable from approved decisions;
- audit is complete and atomic;
- optimistic concurrency is enforced;
- regression and performance requirements pass;
- SATCO Engineering and external operators can use the same capability.

## Commercial Importance

Technical Proposal Review is a candidate flagship capability of SATCO
Platform.

It may create value by:

- reducing manual review effort;
- improving requirement coverage;
- identifying missing or contradictory responses;
- improving clarification quality;
- preserving review knowledge;
- improving traceability;
- supporting multidiscipline coordination;
- reducing procurement and engineering risk;
- enabling repeatable technical-evaluation practices.

Commercial importance does not override engineering safety, Human authority,
confidentiality, or evidence requirements.

## Dependencies

Potential future dependencies include:

- completed Engineering Context foundations;
- authorized document intelligence;
- Missing Information capability;
- Conflict Detection capability;
- Human Review capability;
- governed Engineering Memory;
- authorized AI Context read layer;
- AI safety and traceability controls.

Dependency existence does not authorize implementation.

## Delivery Direction

Technical Proposal Review shall be delivered through separately approved,
bounded PATCHes.

A possible future sequence may include:

1. Proposal and Requirement foundations.
2. Requirement-response mapping.
3. Deterministic missing-response detection.
4. Finding and evidence foundations.
5. Clarification lifecycle.
6. Human Review integration.
7. Multi-proposal comparison.
8. Authorized AI-assisted review.
9. Technical Evaluation output.
10. Product interface and reporting.

This sequence is directional only and does not replace future lifecycle
approval.

## Alignment

This EDS aligns with:

- ADR-015 Engineering Context Domain Architecture;
- ADR-016 Dual-Use Platform Operating Model;
- Context-first architecture;
- PostgreSQL as governed system of record;
- Human engineering authority;
- operator-neutral product architecture;
- AI assistance without autonomous engineering approval;
- documentation-first governance.

## Final Direction

SATCO Technical Proposal Review shall be designed as an operator-neutral,
Context-first, evidence-driven engineering-review capability that assists
Human engineers in evaluating technical proposals for both SATCO Engineering
and external engineering organizations.

Implementation remains deferred until separately approved through the SATCO
Development Lifecycle.
