# ADR-020 EKG Open Extension Principle

## Status

Accepted

## Context

SATCO Engineering starts with Electrical Engineering, Instrumentation
Engineering, and Industrial Automation.

Future product growth may introduce domains such as Maintenance, Methods and
Systems, HSE, Mechanical, Process, Reliability, Asset Integrity, and other
industrial capabilities.

Those future domains must be addable without redesigning the Engineering
Knowledge Graph foundation.

## Decision

The SATCO Engineering Knowledge Graph shall follow the EKG Open Extension
Principle.

The EKG Core shall remain stable.

A new domain may extend the platform by adding:

- governed Engineering Object types;
- governed relationship types;
- domain-specific rules;
- domain-specific validation;
- domain-specific services;
- domain-specific interfaces;
- module entitlement requirements.

A new domain shall not:

- fork the EKG Core;
- duplicate Core identity;
- replace shared Project or Workspace scope;
- bypass authorization or confidentiality;
- create a separate Knowledge Graph architecture;
- introduce customer-specific domain forks;
- redefine Human engineering authority;
- directly mutate Core contracts without a separately accepted ADR.

## Domain Extension Gate

Before a domain is accepted, it shall define:

1. Its Engineering Objects.
2. Its relationship vocabulary.
3. Its evidence sources.
4. Its lifecycle boundaries.
5. Its responsibility model.
6. Its authorization and confidentiality rules.
7. Its integration boundary with EKG Core.
8. Its module entitlement requirements.
9. Its Product Owner approval.
10. Its separately authorized implementation lifecycle.

## Product Doctrine

Build for SATCO, Scale for Industry.

SATCO Engineering is the first operational customer of SATCO Platform.

Capabilities shall first solve real engineering problems inside SATCO
Engineering before being generalized into optional commercial modules.

## Consequences

- Version 1 can remain focused on Electrical, Instrumentation, and Automation.
- Future domains can be introduced as controlled extensions.
- Commercial customers can activate selected modules.
- One shared architecture and codebase are preserved.
- Architectural readiness does not authorize premature implementation.

## Final Decision

SATCO shall keep the EKG Core stable and add future domains through governed
extensions rather than structural redesign.
