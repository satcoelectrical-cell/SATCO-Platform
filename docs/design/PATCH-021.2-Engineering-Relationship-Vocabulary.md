# PATCH-021.2 Engineering Relationship Vocabulary

## Status

Accepted for Implementation Planning

## Purpose

Define the governed relationship vocabulary for the SATCO Engineering
Knowledge Graph (EKG).

Engineering Objects become valuable only when their relationships are
explicit, governed, directional, and traceable.

## Core Principles

Relationships shall:

- represent engineering meaning;
- be governed;
- be directional;
- be traceable;
- be versioned;
- belong to an authorized scope;
- preserve Human accountability.

Relationships shall never be arbitrary free text.

## Required Relationship Metadata

Every governed relationship shall define:

- source Engineering Object;
- target Engineering Object;
- relationship type;
- engineering direction;
- Project scope;
- Workspace scope;
- supporting evidence;
- responsible Human role;
- lifecycle state;
- version.

## Relationship Direction

Relationships are directional.

Example:

```text
Motor
    powered by
MCC Feeder
```

The reverse meaning shall not automatically become another governed
relationship.

Navigation may expose reverse traversal.

Governance shall preserve the original engineering direction.

## Relationship Categories

Version 1 shall classify relationships into:

- Structural
- Physical
- Electrical
- Instrumentation
- Automation
- Evidence
- Dependency
- Governance

This document defines only the vocabulary foundation.

Detailed semantics remain subject to Product Owner approval.

## Structural Relationships

Candidate structural relationships include:

- part of;
- contains;
- belongs to system;
- belongs to subsystem;
- belongs to package;
- grouped with;
- installed in;
- located in.

Structural relationships describe composition, containment, and engineering
placement.

They shall not represent electrical supply, automation logic, signal flow,
or physical connectivity.

## Physical Relationships

Candidate physical relationships include:

- connected to;
- mounted on;
- connected through;
- mechanically coupled to;
- terminated at;
- routed through;
- shares enclosure with.

Physical relationships describe real physical connectivity.

A physical relationship alone shall not imply electrical or automation
behavior.

## Electrical Relationships

Candidate electrical relationships include:

- powered by;
- feeds;
- supplied from;
- protected by;
- isolated by;
- earthed through;
- connected to busbar;
- controlled by feeder;
- backed up by UPS.

Electrical relationships preserve engineering direction.

Example:

Motor
    powered by
MCC Feeder

Reverse navigation may later display:

MCC Feeder
    powers
Motor

The reverse view is navigation only.

The governed relationship remains the original engineering relationship.

## Instrumentation Relationships

Candidate instrumentation relationships include:

- measures;
- measured by;
- transmits to;
- receives process input from;
- connected to loop;
- connected to I/O channel;
- actuates;
- positioned by;
- monitored by;
- provides feedback to;
- compensated by;
- calibrated against.

Instrumentation relationships shall distinguish:

- process measurement;
- signal transmission;
- control action;
- feedback;
- compensation;
- calibration evidence.

Example:

Flow Transmitter
    transmits to
DCS I/O Channel

## Automation Relationships

Candidate automation relationships include:

- controlled by;
- commands;
- receives signal from;
- sends signal to;
- implemented in;
- interlocked with;
- trips;
- initiates;
- inhibits;
- participates in sequence;
- monitored by;
- generates alarm for;
- executes logic for.

Automation relationships shall preserve the difference between:

- signal flow;
- control authority;
- interlock behavior;
- trip behavior;
- alarm behavior;
- sequence participation.

Example:

ESD Logic
    trips
Shutdown Valve

## Evidence Relationships

Candidate evidence relationships include:

- documented by;
- specified by;
- required by;
- justified by;
- verified by;
- tested by;
- reviewed by;
- approved by;
- derived from;
- superseded by;
- clarified by;
- supported by decision.

Evidence relationships shall connect Engineering Objects to governed sources.

Material relationship facts shall remain traceable to evidence.

AI-generated output alone shall not become authoritative relationship
evidence.

## Dependency Relationships

Candidate dependency relationships include:

- depends on;
- required by;
- affects;
- affected by;
- enables;
- prevents;
- constrains;
- replaces;
- supersedes;
- derived from.

Dependency relationships shall describe engineering impact and reliance.

They shall not be used as vague substitutes for more precise structural,
electrical, instrumentation, automation, or evidence relationships.

## Governance Relationships

Candidate governance relationships include:

- owned by;
- stewarded by;
- reviewed by;
- approved by;
- assigned to;
- governed by;
- restricted to;
- visible to.

Governance relationships shall preserve Human accountability,
authorization, confidentiality, and traceability.

## Relationship Lifecycle

A governed relationship may later support lifecycle states such as:

- proposed;
- current;
- superseded;
- withdrawn;
- rejected.

This document does not authorize the final lifecycle vocabulary.

Lifecycle design requires a separately approved IDS.

## Relationship Evidence

Every material relationship shall retain supporting evidence.

Possible evidence includes:

- approved drawing;
- Datasheet;
- specification;
- standard;
- Vendor document;
- calculation;
- technical decision;
- Human Review;
- inspection record;
- commissioning record;
- approved Engineering Context.

A relationship without adequate evidence may remain proposed but shall not
become authoritative.

## Canonical Vocabulary Discrimination

The canonical Version 1 relationship identifier is the ordered pair:

```text
(relationship_family, relationship_type)
```

Relationship type is not globally unique. Where the same type token appears in
more than one approved family, including `monitored_by`, the family supplies
the engineering semantic namespace. Therefore:

- (`instrumentation`, `monitored_by`) means instrumentation monitoring;
- (`automation`, `monitored_by`) means automation-system monitoring.

Every command, persisted relationship, response, filter, uniqueness check,
duplicate check, cycle check, Audit record, Domain Event, and idempotency
fingerprint shall carry and evaluate both values. A type without its family is
invalid and shall never be inferred from the type token alone.

This paired identifier provides backward-compatible extension: a future
approved family may reuse an existing type token only with explicitly approved
family-scoped semantics, while existing family/type pairs retain their stored
values and meaning. An existing pair shall never be reinterpreted. No duplicate
command is created; the same explicit EngineeringRelationship command consumes
the canonical pair.

## Version-1 Boundary

PATCH-021.2 defines relationship vocabulary only.

It shall not implement:

- database models;
- migrations;
- repositories;
- services;
- APIs;
- graph traversal endpoints;
- AI reasoning;
- semantic search;
- Digital Twin behavior;
- frontend visualization.

## Product Owner Decisions Required

Before detailed implementation design begins, the Product Owner shall approve:

1. Mandatory relationship families.
2. Mandatory relationship types.
3. Direction rules.
4. Reverse-navigation rules.
5. Evidence requirements.
6. Lifecycle scope.
7. Responsibility roles.
8. Cross-Project relationship policy.
9. Confidentiality behavior.
10. Extension rules for future domains.

## Success Criteria

PATCH-021.2 is ready for detailed design only when:

- relationship families are approved;
- relationship semantics are unambiguous;
- direction rules are accepted;
- evidence requirements are accepted;
- governance boundaries are accepted;
- future-domain extension remains compatible with ADR-020;
- Product Owner approval is recorded;
- implementation remains explicitly unauthorized.

## Final Direction

SATCO shall use a finite, governed, directional relationship vocabulary.

Relationships shall represent engineering meaning.

Engineering Objects define identity.

Relationships define engineering context.

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
