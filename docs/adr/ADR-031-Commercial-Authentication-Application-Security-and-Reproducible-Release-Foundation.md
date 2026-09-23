# ADR-031 — Commercial Authentication, Application Security & Reproducible Release Foundation

## Status

**Proposed / Candidate — awaiting independent architecture review and Human ADR acceptance.**

## Date

2026-09-23

## Context

PATCH-058 follows the Human-accepted Commercial V1 product experience completed
by PATCH-057.

The Human-accepted PATCH-058 Discovery identifies remaining Commercial V1 gaps
in authentication, session lifecycle, administrator and member MFA,
authentication recovery, tenant isolation, browser authentication, bootstrap
control, security audit and reproducible release security.

Architecture-058 is Human accepted and establishes the controlling architecture
for closing those gaps.

The current implementation already provides password hashing, access and
refresh JWT issuance, auth-version invalidation, Organization membership and
role enforcement, protected onboarding credentials, production configuration
guards, dependency locks, release-manifest foundations and operational
runbooks.

However, the current refresh token is not a server-authoritative rotating
session, logout is not sufficient server-side revocation, MFA and authentication
throttling are absent, legacy Contact and Customer/Contact search paths require
tenant-isolation reconciliation, bootstrap runtime enforcement is incomplete,
and the existing release foundation does not yet provide the complete
PATCH-058 CI/security/SBOM/signing/provenance qualification contract.

PATCH-058 must close these gaps without redefining canonical User,
Organization, membership or engineering-domain ownership, without granting AI
security authority, and without absorbing PATCH-059 entitlement or PATCH-060
deployment-certification responsibilities.

## Decision

SATCO will use a server-authoritative Commercial V1 authentication and
release-security architecture in which durable authentication sessions,
authentication factors and release qualification evidence are independently
verifiable and revocable while canonical identity, tenant authority and
engineering authority remain with their existing owners.

Browser authentication will use short-lived access credentials held only in
browser memory and rotating server-authoritative refresh sessions whose
refresh credential is transported through a Secure, HttpOnly, SameSite cookie
with explicit CSRF protection.

Administrator MFA is mandatory using at minimum TOTP with single-use recovery
codes. Organizations may require MFA for engineer/member users but cannot
weaken mandatory administrator MFA.

Security-sensitive recovery, administration, vulnerability exceptions and
release approval/signing remain attributable Human-authority operations.

PATCH-058 release eligibility will be bound to a clean source revision,
immutable artifact digests, deterministic quality/security evidence, SBOM,
provenance and cryptographic release trust evidence.

## Decisions

### 1. Server-authoritative session lifecycle

Access credentials are short-lived and are not durable session authority.

Durable authentication state is represented by server-side refresh-session
state with non-reversible refresh verifiers, bounded metadata, expiry,
revocation and refresh-family lineage.

Successful refresh rotates the credential. Reuse of an invalidated predecessor
is treated as a security event and revokes at least the affected refresh
family.

Logout revokes the current server session. Current-session, all-session and
authorized administrative revocation are required capabilities.

Password, MFA, account, membership, role and applicable Organization-security
changes must invalidate or re-evaluate stale authentication state according to
a deterministic security-version contract.

Required token security claims may not silently fall back to legacy defaults.

### 2. Browser credential transport

The access credential is held only in browser memory and is not persisted in
localStorage or sessionStorage.

The refresh credential is unavailable to JavaScript and is transported using a
Secure, HttpOnly, SameSite cookie.

Cookie-authenticated refresh, logout and other session-changing operations use
an explicit CSRF defense.

Browser reload may recover an eligible session only through the
server-authoritative refresh path.

Logout, expiry, revocation, credential changes and refresh-reuse events must
converge safely across browser tabs.

One-time activation, reset and recovery secrets must be removed from visible
browser URLs as early as practical and must not become durable browser,
analytics or referrer state.

### 3. MFA and recovery authority

Administrator MFA is mandatory.

The minimum accepted factor is TOTP with single-use recovery codes.

TOTP secrets must be protected at rest under an explicit key-management
boundary. Recovery-code verifiers are stored non-reversibly and are consumed
once.

MFA enrollment is incomplete until factor verification succeeds.

An Organization may require MFA for engineer/member users. The platform does
not make member MFA globally mandatory by default.

Account and MFA recovery are bounded, attributable Human-controlled operations
using purpose-bound, expiring, one-time credentials where credentials are
required.

Recovery or MFA reset must not silently preserve authentication state that
should have been invalidated.

### 4. Sensitive-operation reauthentication

Possession of an ordinary authenticated session is not sufficient evidence for
selected high-impact security operations.

MFA reset/recovery, administrative recovery, broad session revocation,
applicable account/role security changes and security exception operations
require recent authentication or an equivalent bounded step-up according to
the later EDS contract.

Reauthentication does not grant a new role, Organization membership or
engineering authority.

### 5. Authentication throttling and anti-enumeration

Authentication throttling is server-authoritative.

Throttle decisions combine normalized credential identity with bounded network
context and do not rely solely on either a spoofable client-network value or a
single account-wide counter.

Forwarded network identity is trusted only through explicitly configured
trusted proxies.

Login, recovery, MFA and throttling outcomes must preserve generic
anti-enumeration behavior.

Exact persistence, limits, expiry, privacy and distributed-concurrency
contracts are frozen by EDS-058.


### 6. Security audit authority

Authentication and security events are operational/security evidence and do
not become canonical engineering truth or authorization authority.

Security evidence must cover security-relevant authentication outcomes,
throttle thresholds, session creation/rotation/revocation/reuse, MFA
enrollment/reset/recovery, account recovery and attributable security
administration.

Passwords, raw refresh credentials, TOTP secrets and recovery secrets must
never be recorded in security audit evidence.

Organization-scoped security events are disclosed only through current
Organization authorization. Platform-level security evidence requires
separate platform authority.

The existing Audit capability may be extended where it satisfies these
contracts. A dedicated security-event persistence model is introduced only if
EDS-058 demonstrates that the existing owner is insufficient.

### 7. Tenant isolation and authorization-before-lookup

Legacy Contact and Customer/Contact search paths must be reconciled with the
existing Organization authority model.

Contact authorization is derived through its canonical Customer relationship
and that Customer's authoritative Organization ownership. PATCH-058 does not
introduce a second Organization owner on Contact.

Customer-accessible lookup, list, search, detail and mutation paths must
authorize current Organization access before protected information is
disclosed.

Absent, unauthorized and cross-Organization resources preserve the established
protected-not-found and anti-inference behavior.

Search totals, pagination, ordering, empty-state behavior and related response
metadata must not disclose the existence or population of another
Organization's data.

Legacy routes may remain only if they satisfy the same authorization and
anti-inference contracts. Compatibility retirement, if required, is specified
by EDS-058.

### 8. Bootstrap is an exceptional bounded authority

Platform bootstrap is an exceptional provisioning path, not a permanent
alternate authentication or administration mechanism.

Production bootstrap requires explicit enablement, a bounded activation
window and valid bootstrap authorization. Missing, expired or inconsistent
configuration fails closed.

Successful bootstrap completion disables further bootstrap use through a
server-authoritative mechanism.

Any later re-enablement is an attributable Human-controlled operational action.

Bootstrap cannot bypass mandatory administrator MFA, current account policy or
the normal server-authoritative session architecture after initial
provisioning.

### 9. Bounded authentication persistence

PATCH-058 may introduce persistence only for the bounded security state required
by the accepted Architecture.

Expected persistence domains are:

- refresh sessions and refresh-family lineage;
- MFA authenticators;
- single-use recovery-code verifiers;
- Organization member-MFA policy;
- security-event state if the existing Audit model is insufficient;
- throttle state only if the accepted EDS selects durable database persistence.

Refresh-session state does not own User identity, Organization membership,
role or engineering authority.

MFA state owns factor lifecycle only.

Organization MFA policy owns only the bounded member-MFA requirement.

No schema or migration is authorized by this ADR. Any later migration requires
accepted EDS/IDS/Implementation Plan authority and must descend from the
repository's sole accepted Alembic head.

### 10. Reproducible release qualification

PATCH-058 extends the existing PATCH-042 operational/release foundation rather
than replacing it.

A release candidate is eligible for PATCH-058 release-security qualification
only when it is bound to a clean source revision and governed deterministic
build inputs.

Backend, frontend, migration and other governed release artifacts are
identified by immutable cryptographic digests. Mutable names, tags or paths are
not sufficient release identity.

Quality and security evidence must bind to the exact source revision and
artifact identities being qualified.

Required automated gates include the applicable backend and frontend tests,
static/type checks, production frontend build, migration graph/head
validation, security-negative qualification, dependency vulnerability
analysis, SAST, secret scanning, applicable container/image scanning, SBOM
generation, provenance generation and cryptographic signature verification.

A mandatory failed gate blocks release eligibility unless an explicit
Human-governed exception satisfies the accepted vulnerability-exception
contract.

CI execution and scanner output are evidence. They are not Human release
approval.

### 11. Vulnerability exception governance

Security scanner findings are qualification inputs and are not themselves
decision authority.

Any accepted vulnerability exception must be explicit, attributable,
scope-bounded, time-bounded and bound to the exact applicable revision,
artifact/component identity and vulnerability finding.

An exception accepted for one artifact digest cannot silently authorize a
different artifact digest.

AI, scanners and ordinary CI execution cannot approve, extend or inherit a
security exception.

### 12. SBOM, provenance and immutable artifact identity

The release foundation must generate a machine-verifiable SBOM covering the
governed component inventory and resolved dependency identity required for
qualification.

Release provenance binds the source revision, build identity, dependency-lock
identity, governed artifact digests, qualification evidence references, SBOM
identity and release trust/signature evidence.

SBOM and provenance are release-security evidence and do not become
application-domain or engineering-domain records.

The exact machine-readable formats and tooling are specified by EDS/IDS while
preserving these authority and verification contracts.

### 13. Cryptographic signing and release trust

Backend, frontend, migration and governed release artifacts must be
cryptographically authenticated through signatures that bind their exact
immutable digests.

The signing/trust model must define the SATCO trust root, authorized signer
boundary, key custody, rotation, revocation, verification behavior and handling
of expired or revoked signing authority.

Private signing material must not be stored in the source repository or
release artifacts.

Cryptographic signing execution may be automated only within a
Human-authorized signing policy and controlled signer boundary. Automation,
CI or AI does not acquire independent release-signing authority.

Human authority remains controlling for release approval and signing
authorization.

### 14. Release dossier

PATCH-058 produces a governed release-security dossier binding the release
candidate to:

- clean source revision;
- build identity and governed inputs;
- backend, frontend, migration and other governed artifact digests;
- deterministic test and migration qualification evidence;
- vulnerability, SAST, secret and applicable container scan evidence;
- SBOM and provenance;
- cryptographic signature and verification evidence;
- unresolved findings and any valid Human-approved exceptions;
- attributable Human release-security approval evidence.

Missing, stale, mismatched or differently bound evidence fails closed.

The PATCH-058 dossier is not representative production deployment
certification. PATCH-060 consumes this foundation for deployment
qualification and Commercial V1 Release Certification.

### 15. Independent security qualification

PATCH-058 closure requires independent threat/security review and
penetration-oriented negative evidence.

Qualification must cover at minimum session theft/replay and refresh reuse,
stale authorization, credential stuffing, MFA/recovery abuse, tenant
isolation, authorization-before-lookup, anti-inference, bootstrap misuse,
browser credential leakage, privilege/security-administration boundaries and
release artifact/evidence substitution.

Automated evidence and AI analysis may assist review but cannot accept findings
or close the security gate.

## Consequences

PATCH-058 will require substantial authentication and release-security work and
will likely require new persistence and a forward Alembic migration after the
later governance gates are accepted.

Existing stateless refresh JWT behavior and client-only logout cannot remain
the Commercial V1 target architecture.

Legacy Contact and Customer/Contact search behavior must be reconciled before
PATCH-058 can close.

The existing PATCH-042 release-manifest, operational scripts, vulnerability
exception structure and production guards remain reusable foundations, but
PATCH-058 must bind them to executable CI/security/SBOM/provenance/signature
qualification rather than relying on evidence references alone.

The stronger session and release-security model increases implementation and
operational complexity in exchange for revocability, tenant safety,
traceability and reproducible release qualification.

## Alternatives rejected

### Keep stateless refresh JWTs without server-side session state

Rejected because rotation, reuse detection, logout revocation and
administrative session revocation cannot be enforced with the required
server-authoritative guarantees.

### Persist browser bearer credentials in localStorage or sessionStorage

Rejected because the accepted browser-security architecture requires
short-lived access credentials to remain memory-only and durable session
authority to remain server-side.

### Make MFA optional for administrators

Rejected because mandatory administrator MFA is part of the Human-accepted
PATCH-058 security boundary.

### Add direct Organization ownership to Contact

Rejected because Contact authorization can be derived from its canonical
Customer ownership and duplicate ownership would create competing tenant
authority.

### Treat CI/scanner success as release approval

Rejected because automated systems produce evidence but Human authority remains
controlling for security exceptions, signing authorization and release
approval.

### Move entitlement or deployment certification into PATCH-058

Rejected because commercial entitlement authority belongs to PATCH-059 and
representative deployment qualification/Commercial V1 certification belongs
to PATCH-060.

## Compatibility

Existing User, Organization, UserOrganizationMembership and engineering-domain
owners remain canonical.

Existing auth-version invalidation is retained and strengthened through the
accepted server-authoritative session/security-version contract.

Existing protected-not-found and Organization-context patterns remain the
baseline for tenant-isolation reconciliation.

Existing PATCH-041 onboarding and one-time credential patterns are reused where
compatible with the stronger MFA/recovery/session contracts.

Existing PATCH-042 release-manifest, digest, vulnerability-exception,
production-configuration and operational foundations are extended rather than
replaced.

No accepted PATCH-051 through PATCH-057 engineering semantics are reopened.

## EDS-deferred decisions

EDS-058 must freeze the detailed contracts for:

- access-token lifetime, required claims and session/security-version binding;
- refresh-session/family state machine, rotation, expiry and reuse response;
- refresh-cookie, CSRF and origin-validation behavior;
- session listing, current/all-session and administrative revocation;
- password/MFA/account/membership/role/Organization-security invalidation matrix;
- TOTP enrollment, verification, reset and recovery state machines;
- Organization member-MFA default/policy transitions;
- sensitive-operation reauthentication set and validity window;
- throttle limits, persistence, retention, privacy and trusted-network rules;
- security-event taxonomy, retention and Organization/platform visibility;
- legacy Contact/search reconciliation and compatibility treatment;
- bootstrap enablement, window, shutdown and Human re-enable behavior;
- deterministic CI quality/security gate matrix;
- vulnerability severity, blocking, revalidation and exception contracts;
- SBOM and provenance formats;
- immutable artifact identity and digest contracts;
- signing technology, trust root, signer separation, key lifecycle and verification;
- release-dossier schema and evidence-binding rules;
- deterministic security-negative and release-security qualification vectors.

IDS-058 may later define physical modules, schemas, migration sequence,
encryption/key interfaces, route definitions, middleware/dependency ordering,
CI implementation topology and artifact/signature tooling integration.

## Governance disposition

ADR-031 candidate is COMPLETE / READY FOR INDEPENDENT ARCHITECTURE REVIEW.

Human ADR acceptance is not implied.

ADR-031: CANDIDATE / READY FOR INDEPENDENT ARCHITECTURE REVIEW

## Human ADR Acceptance

- Human Architecture Authority decision: **PASS / ACCEPTED / COMPLETE**.
- Acceptance date: 2026-09-23.
- Accepted after Independent ADR Review returned **PASS / READY FOR HUMAN ADR ACCEPTANCE** with Critical/Major/Minor = 0/0/0.
- The decision to use server-authoritative rotating refresh sessions, memory-only short-lived access credentials, mandatory administrator TOTP MFA with single-use recovery codes, Organization-configurable member MFA, bounded Human-controlled recovery and reauthentication, credential-aware anti-enumeration throttling, authorization-before-lookup tenant isolation, bounded bootstrap authority, and reproducible release-security qualification is accepted.
- Release qualification must bind clean source identity, immutable artifact digests, deterministic quality/security evidence, SBOM, provenance and cryptographic release trust evidence.
- Existing canonical identity, Organization, membership and engineering authorities remain controlling. Human authority remains controlling for recovery, security administration, vulnerability exceptions, signing authorization and release approval; AI remains advisory and non-authoritative.
- PATCH-059 entitlement/licensing authority and PATCH-060 deployment qualification/Commercial V1 certification remain explicitly separate.
- This acceptance authorizes progression to EDS-058 preparation and independent review only.
- It does not authorize IDS-058, an Implementation Plan, implementation, migrations, production-code changes, database mutation, deployment, PATCH-059 or PATCH-060.

ADR-031: HUMAN ACCEPTED / COMPLETE
