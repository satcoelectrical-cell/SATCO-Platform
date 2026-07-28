# PATCH-021.4 Engineering Knowledge Graph Rules

## Status

Accepted for Implementation Planning

## Purpose

Define the governing rules that preserve consistency, integrity, and
engineering meaning inside the SATCO Engineering Knowledge Graph (EKG).

Engineering Objects, Relationships, and Context shall always comply with
these rules.

## Vision

The Engineering Knowledge Graph is not merely a graph database.

It is a governed engineering knowledge system.

Every engineering fact shall satisfy explicit architectural rules before
becoming authoritative.

## Core Principles

The Engineering Knowledge Graph shall be:

- deterministic;
- consistent;
- governed;
- evidence-based;
- Human accountable;
- traceable;
- versioned;
- extensible.

## Rule Categories

Version 1 recognizes the following rule categories:

- Identity Rules
- Relationship Rules
- Context Rules
- Evidence Rules
- Responsibility Rules
- Authorization Rules
- Extension Rules
- Validation Rules

Future rule categories require Product Owner approval.

## Rule Hierarchy

Rules shall be evaluated in the following order:

1. Identity
2. Scope
3. Authorization
4. Relationship
5. Evidence
6. Context
7. Responsibility
8. Validation

A lower-level rule shall never bypass a higher-level rule.

## Rule Authority

Engineering Knowledge Graph Rules are mandatory.

No implementation, workflow, API, AI capability, or module may bypass them.

## Version-1 Boundary

PATCH-021.4 defines architectural rules only.

It does not authorize:

- database schema;
- APIs;
- repositories;
- services;
- graph engine implementation;
- AI reasoning;
- Digital Twin behavior.

## Identity Rules

Every Engineering Object, Relationship, and Context shall have a stable
governed identity.

Identity shall not depend solely on:

- display labels;
- file names;
- document titles;
- database row order;
- temporary Project terminology;
- Vendor-specific naming.

Identity collisions within an authorized scope shall be rejected.

Changing a tag, title, or external reference shall not silently create a new
Engineering Object.

## Scope Rules

Every Engineering Object, Relationship, Context, and Evidence reference shall
belong to an explicit authorized scope.

Version-1 scope may include:

- Organization;
- Customer;
- Project;
- Engineering Workspace;
- discipline;
- package;
- system;
- subsystem.

No record shall implicitly cross Project boundaries.

Cross-Project knowledge reuse shall require a governed reference and shall not
disclose confidential Project information.

## Authorization Rules

Authorization shall be enforced before:

- object disclosure;
- relationship disclosure;
- Context disclosure;
- count calculation;
- pagination totals;
- graph traversal;
- search results;
- AI retrieval;
- AI-generated output.

Unauthorized Users shall not infer protected information through identifiers,
counts, missing-result behavior, reverse traversal, or error details.

## Relationship Rules

Every governed Relationship shall:

- use an approved relationship type;
- have a valid source;
- have a valid target;
- preserve direction;
- remain inside an authorized scope;
- retain evidence when authoritative;
- preserve lifecycle and version;
- avoid invalid self-reference unless explicitly allowed.

A generic relationship shall not replace a more precise approved engineering
relationship.

Reverse navigation shall not create a second authoritative relationship unless
separate engineering meaning exists.

## Context Rules

Authoritative Engineering Context shall contain:

- governed Engineering Objects;
- approved Relationships;
- supporting Evidence;
- accountable Human responsibility;
- explicit scope;
- version information;
- authority standing.

Unresolved assumptions, disputed information, and AI suggestions shall remain
distinguishable from approved Engineering Context.

## Evidence Rules

Authoritative engineering knowledge shall be supported by governed evidence.

Evidence shall preserve:

- source identity;
- source type;
- source revision;
- Project scope;
- confidentiality;
- issuing authority;
- approval standing;
- effective date;
- traceability.

AI output, informal notes, and unverified assumptions shall not become
authoritative evidence.

Evidence withdrawal or supersession shall not silently erase historical
knowledge.

## Responsibility Rules

Every authoritative Engineering Object, Relationship, and Context shall retain
accountable Human responsibility.

Responsibility may include:

- creator;
- owner;
- steward;
- discipline owner;
- reviewer;
- approver;
- assignee;
- source authority.

Anonymous approval is prohibited.

AI shall never become an accountable engineering owner, reviewer, or approver.

## Versioning Rules

Material changes shall use explicit version control.

A material change includes:

- identity correction;
- classification change;
- relationship change;
- evidence replacement;
- scope change;
- responsibility change;
- lifecycle transition;
- authority-standing change.

Approved knowledge shall not be silently overwritten.

Version conflicts shall reject stale mutation rather than discard a newer
engineering state.

## Lifecycle Rules

Lifecycle transitions shall be finite and governed.

Withdrawal shall remain distinct from deletion.

Supersession shall preserve:

- predecessor identity;
- successor identity;
- reason;
- responsible actor;
- effective time;
- supporting evidence.

Ordinary deletion of authoritative engineering history is prohibited.

## Conflict Rules

Conflicting engineering claims shall remain visible to authorized Users.

The EKG shall preserve:

- each conflicting claim;
- supporting evidence;
- source authority;
- responsible parties;
- review standing;
- resolution decision;
- retained history.

The system shall not silently select one conflicting claim as truth.

## Audit Rules

Every authoritative mutation shall create an atomic Audit record.

Audit evidence shall include:

- actor;
- action;
- target identity;
- previous version;
- new version;
- reason;
- timestamp;
- scope;
- outcome.

A failed authoritative mutation shall not leave a successful Audit event.

A successful authoritative mutation shall not exist without its Audit event.

## Extension Rules

Future domains shall extend the stable EKG Core.

A domain extension may add:

- governed Engineering Object types;
- governed Relationship types;
- domain-specific validation;
- domain-specific evidence rules;
- domain-specific lifecycle rules;
- domain-specific services;
- module entitlement requirements.

A domain extension shall not:

- fork Core identity;
- duplicate Project or Workspace scope;
- bypass shared authorization;
- weaken confidentiality;
- redefine Human authority;
- alter Core contracts without an accepted ADR;
- create customer-specific EKG architectures.

Architectural extensibility does not authorize immediate implementation.

## Validation Rules

Every authoritative EKG mutation shall validate:

- actor eligibility;
- identity validity;
- scope compatibility;
- authorization;
- source validity;
- target validity;
- Relationship vocabulary;
- evidence requirements;
- lifecycle transition;
- expected version;
- responsibility;
- confidentiality;
- Audit atomicity.

Validation shall occur before authoritative disclosure or persistence.

Partial authoritative mutation is prohibited.

## Transaction Rules

A governed mutation and its Audit evidence shall succeed or fail together.

The transaction shall preserve:

- one authoritative outcome;
- one accepted version increment;
- no partial Relationship state;
- no orphaned Evidence reference;
- no misleading Audit success;
- no silent stale-writer overwrite.

Independent concurrent mutations shall produce deterministic one-winner
behavior when they target the same expected version.

## AI Rules

AI may:

- retrieve authorized knowledge;
- summarize governed Evidence;
- identify possible gaps;
- identify possible conflicts;
- propose Engineering Objects;
- propose Relationships;
- propose Context observations.

AI shall not:

- bypass authorization;
- approve authoritative knowledge;
- mutate approved knowledge autonomously;
- hide uncertainty;
- fabricate Evidence;
- become an accountable owner;
- override Human decisions.

AI proposals shall remain distinguishable from approved engineering knowledge.

## Performance Rules

EKG operations shall remain bounded and measurable.

Performance validation shall include:

- authorized Object lookup;
- authorized Relationship traversal;
- scoped Context retrieval;
- pagination;
- confidentiality-preserving totals;
- versioned mutation;
- concurrent conflict handling;
- actual query instrumentation.

Performance optimization shall not weaken authorization, confidentiality,
traceability, Evidence, or Audit requirements.

## Product Owner Decisions Required

Before physical data-model design begins, the Product Owner shall approve:

1. Rule categories.
2. Rule hierarchy.
3. Identity and scope invariants.
4. Authorization-before-disclosure behavior.
5. Evidence authority requirements.
6. Versioning and lifecycle invariants.
7. Conflict preservation.
8. Audit atomicity.
9. Domain extension restrictions.
10. AI authority boundaries.
11. Performance safety requirements.

## Success Criteria

PATCH-021.4 is ready for physical data-model design only when:

- all Core rule categories are approved;
- higher-order rules cannot be bypassed;
- authorization precedes disclosure;
- authoritative knowledge requires governed Evidence;
- Human responsibility remains mandatory;
- stale mutation is rejected;
- history cannot be silently deleted;
- conflict remains explicit;
- Audit is atomic;
- future domains extend rather than redesign Core;
- AI remains non-authoritative;
- Product Owner approval is recorded;
- implementation remains unauthorized.

## Final Direction

The EKG shall not accept knowledge merely because it can be stored.

Knowledge becomes authoritative only when identity, scope, authorization,
Evidence, responsibility, versioning, lifecycle, validation, and Audit rules
are satisfied.

Engineering integrity comes before convenience.

## Product Owner Approval

The Product Owner approves this design for Version 1.

Version 1 remains focused on:

- Electrical Engineering;
- Instrumentation Engineering;
- Industrial Automation;
- shared Engineering Objects required by those disciplines.

Maintenance, Methods and Systems, HSE, Mechanical, Process, Reliability,
Asset Integrity, and other future domains remain deferred.

This approval authorizes the next implementation-planning stage but does not
authorize uncontrolled implementation outside the accepted EKG architecture.
