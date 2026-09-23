# PATCH-058 — Commercial Authentication, Application Security & Reproducible Release Foundation

## Document control

| Field | Value |
|---|---|
| Registration authority | HUMAN PATCH-058 DISCOVERY ACCEPTANCE AND REGISTRATION AUTHORITY: GRANTED |
| Registration date | 2026-09-23 |
| Status | **REGISTERED / OPEN — DISCOVERY ACCEPTED** |
| Registered after | PATCH-057 DONE / CLOSED |
| Controlling boundary | Human-accepted Post-PATCH-057 Capability Discovery |
| Architecture / ADR | NEXT AUTHORIZED GOVERNANCE STAGE / NOT YET HUMAN ACCEPTED |
| EDS / IDS / Implementation Plan | NOT STARTED / NOT AUTHORIZED |
| Implementation | NOT STARTED / NOT AUTHORIZED |
| Migration | NOT CREATED / NOT AUTHORIZED |
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

The accepted Discovery indicates that persistence/migration is likely required,
but no schema or migration is authorized by registration.

The sole Alembic head remains `e05600000008`.

## Next governed stage

Architecture-058 and the next repository-consistent ADR may now be prepared
and independently reviewed.

They require explicit Human acceptance before EDS/IDS work.

**PATCH-058: REGISTERED / OPEN — DISCOVERY ACCEPTED.**

**PATCH-058 IMPLEMENTATION: NOT STARTED / NOT AUTHORIZED.**

**PATCH-059 / PATCH-060: NOT STARTED / NOT AUTHORIZED.**
