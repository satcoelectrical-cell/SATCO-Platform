# PATCH-021.1 Engineering Object Model

## Status

Accepted for Detailed Design

## Purpose

Define the foundational Engineering Object model for the SATCO Engineering
Knowledge Graph (EKG).

Engineering Objects become the primary engineering entities inside SATCO.

Documents support Engineering Objects.

Documents do not define Engineering Objects.

## Core Principle

SATCO shall be Engineering Object-Centric.

Every future Engineering Intelligence capability shall first identify:

- which Engineering Objects it uses;
- which Engineering Objects it creates;
- which Engineering Objects it changes;
- which Engineering Objects it connects.

## Engineering Object Definition

An Engineering Object is a governed engineering entity with:

- identity;
- lifecycle;
- responsibility;
- traceability;
- engineering meaning.

Engineering Objects may represent:

- physical equipment;
- instrumentation;
- electrical equipment;
- automation equipment;
- engineering systems;
- project engineering entities;
- governed engineering concepts.

## Version-1 Object Families

### Instrumentation

- Instrument
- Transmitter
- Analyzer
- Flowmeter
- Control Valve
- Instrument Loop
- Junction Box
- Instrument Panel

### Electrical

- Motor
- Transformer
- MCC
- Switchgear
- Electrical Panel
- Electrical Cable

### Automation

- PLC
- DCS Controller
- ESD Controller
- Control Cabinet
- I/O Channel
- HMI
- Control Logic

### Shared

- Project
- Vendor
- Requirement
- Standard
- Datasheet
- Drawing
- Technical Decision

## Object Identity

Every Engineering Object shall have a stable internal identity.

Identity shall not depend only on:

- file name;
- document title;
- temporary label;
- database row order;
- Vendor terminology;
- user-interface wording.

Future implementation may combine:

- internal UUID;
- Project-scoped object key;
- tag number;
- equipment number;
- loop number;
- cable number;
- panel number;
- system identifier;
- controlled external reference.

The final identity contract requires a separately approved IDS.

## Object Scope

Every Engineering Object shall belong to an authorized scope.

Possible scope levels include:

- Organization;
- Customer;
- Project;
- Engineering Workspace;
- discipline;
- package;
- system;
- subsystem.

Cross-Project similarity shall not automatically create shared identity or
permit confidential information disclosure.

## Object Classification

Engineering Object classification shall be governed and extensible.

Classification shall support:

- object family;
- object type;
- discipline;
- subtype;
- Project-specific classification;
- controlled future extensions.

Arbitrary free text alone shall not define an Engineering Object type.

## Object Evidence

Material facts about an Engineering Object shall remain traceable to evidence.

Evidence may include:

- approved Datasheet;
- drawing;
- calculation;
- specification;
- standard;
- Vendor proposal;
- technical correspondence;
- Human engineering decision;
- inspection record;
- commissioning record;
- approved Engineering Context.

AI output alone shall not become authoritative engineering evidence.

## Object Responsibility

Engineering Objects shall preserve accountable Human responsibility.

Future responsibility roles may include:

- creator;
- owner;
- discipline owner;
- steward;
- reviewer;
- approver;
- assignee;
- source authority.

The final responsibility and authorization contract requires a separately
approved IDS.

## Object Lifecycle

Engineering Objects may later support governed lifecycle states such as:

- proposed;
- identified;
- under review;
- approved;
- active;
- superseded;
- withdrawn;
- retired.

This document does not authorize the final lifecycle vocabulary.

Lifecycle design shall be bounded and approved separately.

## Object Relationships

Engineering Objects become useful through governed relationships.

Candidate relationships include:

- part of;
- connected to;
- supplied by;
- manufactured by;
- controlled by;
- measured by;
- powered by;
- protected by;
- located in;
- documented by;
- governed by;
- required by;
- affects;
- depends on;
- replaces;
- derived from;
- reviewed by.

These relationship names are candidates only.

The accepted relationship vocabulary shall be defined in a separate bounded
PATCH and approved by the Product Owner.

## Version-1 Boundary

PATCH-021.1 defines the Engineering Object model only.

It shall not implement:

- Engineering Digital Twin;
- live operational state;
- real-time telemetry;
- AI reasoning;
- semantic search;
- vector database;
- Maintenance domain;
- Methods and Systems domain;
- HSE domain;
- generic enterprise assets;
- frontend graph visualization.

## Product Owner Decisions Required

Before implementation planning begins, the Product Owner shall approve:

1. Version-1 Engineering Object families.
2. Mandatory Version-1 object types.
3. Project-scoped and Organization-scoped identities.
4. Objects permitted without tag numbers.
5. Objects permitted without supporting documents.
6. Objects shared across engineering disciplines.
7. Mandatory relationship types.
8. Facts requiring explicit Human approval.
9. Lifecycle scope for the first implementation.
10. Responsibility roles for the first implementation.

## Success Criteria

PATCH-021.1 becomes ready for implementation planning only when:

- Version-1 object families are approved;
- identity principles are accepted;
- scope boundaries are accepted;
- classification principles are accepted;
- evidence requirements are accepted;
- lifecycle is separately approved or explicitly deferred;
- responsibility boundaries are accepted;
- relationship vocabulary is separately scheduled;
- Product Owner approval is recorded.

## Related Documents

- ADR-015 Engineering Context Domain Architecture
- ADR-016 Dual-Use Platform Operating Model
- ADR-018 Engineering Intelligence Product Vision
- ADR-019 Version-1 Product Scope Policy
- PATCH-021 Engineering Knowledge Graph Foundation
- EDS-031 Engineering Digital Twin Vision

## Final Direction

SATCO shall model engineering reality through governed Engineering Objects.

Documents, requirements, Vendors, decisions, and technical evidence shall
connect to those objects through the Engineering Knowledge Graph.

Engineering Objects are the foundation.

Engineering Intelligence comes later.

## Product Owner Approval

The Product Owner approves the Version-1 boundary as follows:

- Instrumentation;
- Electrical Engineering;
- Industrial Automation;
- shared Engineering Objects required by those disciplines.

The following domains remain deferred:

- Maintenance;
- Methods and Systems;
- HSE;
- Mechanical;
- Process;
- Reliability;
- Asset Integrity;
- other organizational modules.

Deferred domains shall later extend the stable EKG Core through governed
Engineering Objects, relationships, evidence, rules, and module entitlements.

They shall not require customer-specific forks or fundamental redesign of the
EKG Core.
