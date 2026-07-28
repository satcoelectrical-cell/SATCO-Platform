# ADR-017 Modular Product Licensing Architecture

## Status

Accepted

## Context

SATCO Platform is developed first as the operational platform of
SATCO Engineering.

The first production deployment is intended to support the daily work of
SATCO Engineering in:

- Electrical Engineering
- Instrumentation Engineering
- Industrial Automation
- Technical Procurement
- Engineering Context
- Engineering Intelligence

Future commercial customers may require only a subset of the available
modules.

The platform must therefore support commercial modularity without creating
multiple products or multiple codebases.

## Decision

SATCO Platform shall remain one product.

Capabilities shall be enabled through Organization-scoped Module
Entitlements.

There shall never be:

- customer-specific source-code forks;
- edition-specific databases;
- duplicated domain models;
- deployment-specific business logic.

Commercial differentiation shall be achieved only through module activation.

## Product Structure

SATCO Platform

├── Core Platform
├── Engineering Module
├── Technical Procurement Module
├── Maintenance Module
├── Methods & Systems Module
├── Document Management Module
├── AI Assistant
└── Analytics

Core Platform is mandatory.

Every optional module depends on Core Platform.

## Version 1

Version 1 activates only the capabilities required by SATCO Engineering.

Future customers may activate any supported module independently.

## Consequences

Advantages

- One architecture
- One codebase
- One deployment model
- Simple maintenance
- Simple upgrades
- Modular commercial strategy

Trade-offs

- Licensing infrastructure becomes part of Core Platform.
- Authorization must become module-aware.
- Navigation becomes entitlement-aware.

## Related Documents

ADR-016 Dual-Use Platform Operating Model

EDS-030 Technical Proposal Review
