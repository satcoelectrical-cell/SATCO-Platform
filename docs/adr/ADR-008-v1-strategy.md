# ADR-008 — SATCO Platform V1 Strategy

## Status
Accepted

## Date
2026-07-29

## Context

During architectural planning, two development paths were considered:

1. Enterprise version for petrochemical companies
2. Internal production version for SATCO Engineering

Building both simultaneously would significantly increase development complexity,
slow down delivery, and postpone real-world validation.

The primary business objective is to deploy SATCO inside SATCO Engineering first,
use it in real engineering work, improve it through daily usage, and create a
proven case study before approaching industrial customers.

## Decision

SATCO V1 will target SATCO Engineering only.

The first production deployment will use:

- FastAPI
- PostgreSQL
- Docker
- OpenAI
- n8n

Enterprise-specific capabilities are intentionally postponed.

The only architectural requirement kept for future compatibility is introducing
an AI Gateway abstraction so that the Core Platform never depends directly on
OpenAI.

Current implementation:

SATCO Core
    ↓
AI Gateway
    ↓
OpenAI

Future implementations may replace OpenAI with:

- Local LLM
- Azure OpenAI
- Offline Provider
- Disabled Provider

without modifying SATCO Core.

## Deferred Features

The following items are explicitly out of scope for V1:

- Multi-Tenant Architecture
- Enterprise Deployment Profiles
- Offline Installation
- Local LLM
- GPU Acceleration
- Enterprise Licensing
- Enterprise Security Policies
- ERP Integrations
- SAP Integration
- Maximo Integration
- OPC UA Enterprise Connectors

These capabilities will be evaluated after SATCO V1 is successfully used in
real engineering projects.

## Consequences

Benefits:

- Faster MVP delivery
- Lower implementation complexity
- Earlier real-world validation
- Lower development cost
- Easier maintenance
- Stronger commercial demonstration

Risks:

- Enterprise deployment will be implemented later.

This trade-off is accepted because validated engineering experience is considered
more valuable than premature enterprise features.

