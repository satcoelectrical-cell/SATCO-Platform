# Post-PATCH-057 Capability Discovery

## PATCH-058 — Commercial Authentication, Application Security & Reproducible Release Foundation

**Status:** HUMAN ACCEPTED / COMPLETE
**Human acceptance date:** 2026-09-23
**Independent review:** Critical 0 / Major 0 / Minor 0

## 1. Purpose

PATCH-058 closes the Commercial V1 identity, session, tenant-isolation,
application-security and software-supply-chain gaps remaining after the stable
product experience delivered by PATCH-057.

It establishes the secure and reproducible release foundation consumed by
PATCH-059 entitlement work and PATCH-060 deployment qualification.

## 2. Controlling dependency

The accepted Commercial V1 sequence is:

`PATCH-057 -> PATCH-058 -> PATCH-059 -> PATCH-060`

PATCH-057 is DONE / CLOSED at:

`368e238c94f694ba34f7f187968bfcabd8991170`

with closure tag:

`patch-057-closed`

The sole Alembic head at Discovery acceptance is:

`e05600000008`

## 3. Accepted capability boundary

PATCH-058 governs:

1. mandatory administrator MFA using at minimum TOTP and single-use recovery codes;
2. Organization-configurable engineer/member MFA;
3. short-lived access tokens and server-authoritative rotating refresh sessions;
4. refresh-family rotation, reuse detection, expiry and revocation;
5. coherent invalidation across password, MFA, account, membership, role and Organization-security changes;
6. authentication throttling/backoff with generic anti-enumeration behavior;
7. bounded Human-controlled account and MFA recovery;
8. safe Organization-aware authentication/security Audit;
9. closure of legacy Contact and Customer/Contact search tenant-isolation gaps;
10. authorization-before-lookup and anti-inference review across customer-accessible routes;
11. browser authentication hardening and transport/CSRF/XSS reconciliation;
12. bootstrap enable/window enforcement;
13. deterministic CI quality/security gates;
14. dependency, container, SAST and secret scanning;
15. SBOM generation;
16. signed immutable backend, frontend, migration and release artifacts with verifiable provenance;
17. a release dossier binding revision, digests, tests, scans, SBOM, signatures, exceptions and approval evidence;
18. independent threat/security and penetration-oriented qualification evidence.

## 4. Existing capability assessment

Repository evidence establishes a mixed baseline:

- password hashing: IMPLEMENTED;
- access JWT: PARTIAL;
- refresh token lifecycle: PARTIAL;
- auth_version invalidation: IMPLEMENTED;
- logout: PARTIAL;
- MFA: ABSENT;
- authentication throttling: ABSENT;
- public registration closure: IMPLEMENTED;
- activation/reset credentials: IMPLEMENTED;
- account/membership administration: IMPLEMENTED;
- server-derived Organization context: IMPLEMENTED;
- modern tenant isolation: IMPLEMENTED;
- legacy Contact isolation: PARTIAL;
- global Customer/Contact search isolation: PARTIAL;
- authentication/security Audit: PARTIAL;
- browser token handling: PARTIAL;
- production configuration guards: IMPLEMENTED;
- dependency locks: IMPLEMENTED;
- release manifest: PARTIAL;
- automated CI/security gates: ABSENT;
- automated security scanning: ABSENT;
- SBOM generation: ABSENT;
- signed immutable release artifacts: ABSENT.

## 5. Explicit exclusions

PATCH-058 excludes:

- signed entitlements, licensing, seats, validity/grace/update rules and license anti-rollback — PATCH-059;
- representative production deployment and Commercial V1 Release Certification — PATCH-060;
- real DNS/TLS, backup/restore execution, monitoring delivery, support exercises, capacity validation, measured RPO/RTO/SLO and deployment rollback/upgrade qualification — PATCH-060;
- enterprise SSO/SAML/OIDC/SCIM;
- new IAM roles outside the accepted Commercial V1 boundary;
- Kubernetes, multi-region and unrelated SaaS orchestration;
- billing, ERP/BPM, finance or CRM expansion;
- new engineering disciplines;
- reopening PATCH-051 through PATCH-057 engineering semantics;
- autonomous AI security authority;
- production/customer database operations during implementation qualification.

## 6. Source-owner boundary

User remains canonical for account identity, password hash, role, active state
and authentication version.

Organization and UserOrganizationMembership remain canonical for tenant
membership and Organization authority.

Refresh-session state may own authentication-session lifecycle only.

MFA state may own authentication-factor lifecycle only.

Security events are security/audit evidence only.

Release manifests, SBOMs, attestations, signatures and vulnerability evidence
are release-pipeline evidence only.

Existing engineering canonical owners remain unchanged.

## 7. Human Authority and AI non-authority

Human authority remains controlling for:

- MFA recovery/reset;
- account recovery;
- administrative session revocation;
- Organization MFA policy;
- account, membership and role administration;
- vulnerability exceptions;
- release approval and signing authority;
- final security and PATCH acceptance.

AI may explain, summarize, identify possible security conditions, propose
remediation and assist with evidence assembly.

AI may not authenticate, bypass MFA, recover credentials, grant/revoke roles,
approve security exceptions, sign or approve releases, become session or tenant
authority, or alter canonical engineering decisions.

## 8. Persistence assessment

A PATCH-058 migration is likely required, subject to accepted Architecture,
EDS and IDS.

Likely state includes:

- refresh sessions/families;
- MFA authenticators;
- single-use recovery codes;
- Organization member-MFA policy;
- security-event state where existing Audit is insufficient;
- persistent throttle state if the later architecture selects it.

No migration is created or authorized by this Discovery.

Any future migration must descend from sole head `e05600000008`.

## 9. Required Architecture decisions

Architecture/ADR must resolve at minimum:

- access/refresh session architecture;
- browser token transport and CSRF model;
- administrator/member MFA policy;
- sensitive-operation reauthentication;
- throttling authority;
- security Audit authority;
- tenant-isolation reconciliation;
- bootstrap enforcement;
- release-security pipeline;
- signing/trust model;
- CI qualification boundary;
- persistence ownership.

## 10. PATCH-059 / PATCH-060 separation

PATCH-058 owns authentication, application security and reproducible-release
foundation.

PATCH-059 owns commercial entitlements, licensing, seats, validity/grace and
anti-rollback.

PATCH-060 owns representative deployment qualification and Commercial V1
Release Certification using real operational evidence.

Generating secure artifacts in PATCH-058 does not prove production deployment.

## 11. Qualification families

Future qualification must cover, as applicable:

- unit;
- service;
- API;
- integration;
- frontend;
- security/negative;
- migration;
- release/security pipeline;
- independent threat/security review.

## 12. Discovery verdict

Repository evidence establishes PATCH-058 identity, scope, exclusions,
dependencies, likely persistence requirements, threat boundary and qualification
boundary.

The Human accepts this Discovery on 2026-09-23.

Discovery acceptance authorizes governed PATCH-058 registration and subsequent
Architecture/ADR preparation as a separately reviewed stage only.

It does not authorize EDS, IDS, Implementation Plan, implementation, migration,
deployment, PATCH-059 or PATCH-060.

**PATCH-058 DISCOVERY: HUMAN ACCEPTED / COMPLETE.**

**Independent Review: Critical 0 / Major 0 / Minor 0.**
