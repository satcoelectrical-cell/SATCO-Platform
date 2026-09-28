# PATCH-058 — Commercial Authentication, Application Security & Reproducible Release Foundation

## Document control

| Field | Value |
|---|---|
| Registration authority | HUMAN PATCH-058 DISCOVERY ACCEPTANCE AND REGISTRATION AUTHORITY: GRANTED |
| Registration date | 2026-09-23 |
| Status | **OPEN — CHECKPOINT D HUMAN ACCEPTED / CHECKPOINT E IN PROGRESS** |
| Registered after | PATCH-057 DONE / CLOSED |
| Controlling boundary | Human-accepted Post-PATCH-057 Capability Discovery |
| Architecture / ADR | HUMAN ACCEPTED |
| EDS / IDS / Implementation Plan | HUMAN ACCEPTED |
| Implementation | CHECKPOINTS A-D HUMAN ACCEPTED / CHECKPOINT E IN PROGRESS |
| Migration | CREATED AND QUALIFIED IN DISPOSABLE POSTGRESQL ONLY |
| Alembic source head at registration | sole `e05600000008` |
| PATCH-059 / PATCH-060 | NOT STARTED / NOT AUTHORIZED |

## Registration verdict

Under explicit Human authority, **PATCH-058 — Commercial Authentication,
Application Security & Reproducible Release Foundation** is formally
**REGISTERED / OPEN — DISCOVERY ACCEPTED**.

Registration authorizes Architecture/ADR preparation and independent review
as the next governance stage only.

It does not accept an Architecture or ADR and does not authorize EDS, IDS,
Implementation Plan, implementation, migration, deployment, PATCH-059 or
PATCH-060.

This section records the historical registration decision. The current
governance state is controlled by the accepted Architecture, ADR, EDS, IDS,
Implementation Plan and checkpoint records summarized below.

## Current checkpoint state

- Checkpoints A, B, C and D: **HUMAN ACCEPTED / COMPLETE**.
- Checkpoint E: **IN PROGRESS / NOT YET HUMAN ACCEPTED**.
- Human-approved High-finding exception: bounded to the exact previously
  qualified backend artifact and its 30-day validity window; it does not
  transfer to any rebuilt artifact.
- Post-build security-decision architecture: **HUMAN GOVERNANCE APPROVED FOR
  BOUNDED IMPLEMENTATION / NOT YET COMMITTED OR QUALIFIED**. Candidate and
  decision revisions remain separate; ordinary push runs cannot inherit an
  external exception, and a manual replay must identify an exact decision
  commit reachable from `patch-058-security-decisions`.
- Current in-tree exception records remain historical/non-transferable and are
  not rebound by the architecture implementation.
- Privileged signing authorization: **NOT GRANTED / NOT EXECUTED**.
- Human release approval: **NOT GRANTED**.
- Integrated final qualification and independent final review: **NOT
  COMPLETE**.
- PATCH-058 closure: **NOT GRANTED**.

## Purpose

PATCH-058 closes Commercial V1 authentication/session, tenant-isolation,
application-security and reproducible-release foundation gaps after the stable
product experience delivered by PATCH-057.

## Registered capability boundary

Subject to later Human-accepted Architecture/ADR work, PATCH-058 owns:

- administrator MFA and Organization-configurable member MFA;
- server-authoritative refresh-session lifecycle and revocation;
- authentication throttling and recovery security;
- Organization-aware security Audit;
- legacy tenant-isolation reconciliation;
- browser authentication hardening;
- bootstrap security enforcement;
- CI quality/security gates;
- scanning and SBOM evidence;
- signed immutable artifacts and provenance;
- Human-governed release dossier and security exceptions.

## Explicit exclusions

PATCH-058 excludes:

- commercial entitlements/licensing/seats and anti-rollback — PATCH-059;
- representative deployment qualification and Commercial V1 Release
  Certification — PATCH-060;
- new engineering disciplines;
- reopening accepted PATCH-051 through PATCH-057 engineering semantics;
- enterprise SSO/SAML/OIDC/SCIM;
- autonomous AI security authority;
- production/customer database operations during PATCH implementation.

## Authority boundary

Canonical identity, Organization, membership and engineering source owners
remain controlling.

Human authority remains controlling for security recovery, administration,
vulnerability exceptions, release approval/signing and engineering acceptance.

AI remains optional, advisory and non-authoritative.

## Persistence boundary

The Human-accepted design and implementation checkpoints authorized and
delivered the bounded PATCH-058 security persistence migration. Qualification
uses disposable PostgreSQL only; production/customer database mutation remains
unauthorized.

The sole Alembic repository head is `e05800000001`.

## Next governed stage

Complete Checkpoint E release-manifest/dossier reconciliation, exact-source
artifact and evidence qualification, integrated security regression,
penetration-oriented negative qualification and independent checkpoint review.

Checkpoint E then requires explicit Human acceptance. Privileged signing,
Human release approval, integrated final qualification, independent final
review and the Human PATCH-058 closure decision remain separate later gates.

**PATCH-058: OPEN — CHECKPOINT E IN PROGRESS.**

**PATCH-058 CLOSURE: NOT GRANTED.**

**PATCH-059 / PATCH-060: NOT STARTED / NOT AUTHORIZED.**
