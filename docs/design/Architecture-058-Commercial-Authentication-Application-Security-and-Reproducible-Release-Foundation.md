# Architecture-058 — Commercial Authentication, Application Security & Reproducible Release Foundation

**Date:** 2026-09-23
**Status:** CANDIDATE / READY FOR INDEPENDENT ARCHITECTURE REVIEW
**Authority:** PATCH-058 Discovery is Human accepted and PATCH-058 is registered/open; this candidate is not Human accepted and authorizes no EDS, IDS, Implementation Plan, implementation, migration, database mutation, deployment, PATCH-059 or PATCH-060 work.

## Purpose and invariants

PATCH-058 establishes the Commercial V1 authentication, session, tenant-security,
application-security and reproducible-release foundation.

Identity, Organization and membership owners remain canonical. Authentication
sessions and MFA factors may own only their bounded security lifecycle.
Engineering source owners and Human Engineering Authority remain unchanged.

Authentication and authorization are distinct. Possession of a valid session
does not grant Organization, membership, role or engineering authority.
Server-derived authorization is evaluated from current authoritative state
before protected disclosure or mutation.

Security failure must be fail-closed without creating account, Organization,
membership, role or resource-existence inference.

AI remains optional, advisory and non-authoritative. It cannot authenticate,
bypass MFA, recover credentials, grant authority, approve security exceptions,
sign artifacts or approve releases.

PATCH-059 entitlement/licensing authority and PATCH-060 deployment
qualification remain separate.

## Session architecture

Access credentials are short-lived bearer credentials and are not the durable
session authority.

Durable session authority is server-side and revocable. Refresh credentials
are represented server-side only by non-reversible verifier material and
bounded metadata required for lifecycle, lineage, security and Human-visible
session management.

Refresh rotation is one-time. Successful refresh invalidates the presented
refresh credential and issues a successor in the same session family.

Reuse of an already-rotated refresh credential is treated as a security event
and revokes the affected refresh family at minimum. EDS must freeze the exact
safe response and client behavior.

Logout revokes the current server-side session. The product must also support
revocation of all sessions for the current user and authorized administrative
revocation.

Password, MFA, account, membership, role and applicable Organization-security
changes must invalidate or re-evaluate affected sessions according to a
server-authoritative security-version contract.

JWT validation must not silently substitute a default security version when a
required claim is absent. Compatibility behavior, if any is required during
transition, must be explicit, bounded and removable.

## Browser authentication and CSRF architecture

The refresh credential shall use a Secure, HttpOnly, SameSite cookie and shall
not be readable by application JavaScript.

The short-lived access credential shall be held only in browser memory. It shall
not be persisted in localStorage or sessionStorage by the PATCH-058 target
architecture.

A full page reload may recover an authenticated browser session only through
the server-authoritative refresh flow.

Because refresh/logout/session-changing operations use cookie-carried
credentials, they require an explicit CSRF defense in addition to SameSite.
EDS must freeze the token/header and origin-validation contract.

Authentication secrets and one-time activation/reset/recovery material must be
removed from browser-visible URLs as early as technically possible and must not
be retained in browser history, analytics, logs or referrers beyond the minimum
entry transition.

Cross-tab behavior must converge safely after logout, revocation, expiry,
credential change or refresh-reuse detection without treating browser-local
coordination as authority.

## MFA architecture

Administrator MFA is mandatory.

The Commercial V1 minimum factor is TOTP with single-use recovery codes.
Recovery codes are stored only as non-reversible verifier material.

TOTP secrets require protected-at-rest storage separated from ordinary
application data exposure. Key ownership, rotation and operational recovery
must be frozen before implementation.

MFA enrollment is incomplete until the factor is verified. Mandatory-admin
policy must prevent a usable privileged session from bypassing required
enrollment.

Organization policy may require MFA for engineer/member accounts. Organization
policy cannot weaken mandatory platform-administrator MFA.

MFA reset and recovery are security-sensitive Human-controlled operations.
They must be attributable, bounded and invalidate affected authentication
state.

## Sensitive-operation reauthentication

Possession of an ordinary authenticated session is insufficient for selected
high-impact security operations.

Security-sensitive operations such as MFA reset, recovery administration,
session-wide revocation, applicable role/account security changes and release
security exceptions require recent authentication evidence or an equivalent
bounded step-up contract.

EDS must freeze the exact protected operations, acceptable evidence and
reauthentication window. Reauthentication grants no new role or Organization
authority.

## Authentication throttling

Authentication throttling/backoff is server-authoritative.

The throttle key must combine normalized credential identity with bounded
network context so that neither a single spoofable network identifier nor a
single account-wide counter becomes the sole security authority.

Client network identity may be derived from forwarding headers only through an
explicit trusted-proxy configuration. Untrusted forwarding headers are ignored.

Failure responses remain generic and do not disclose whether an account,
membership, MFA factor or recovery target exists.

EDS must freeze persistence, expiry, privacy/retention, concurrency and
distributed-consistency behavior. The Architecture does not require a specific
storage technology.

## Security Audit architecture

Security Audit is attributable operational/security evidence. It is not an
engineering source of truth and does not grant authority.

PATCH-058 security evidence must cover successful and security-relevant failed
authentication, threshold/backoff events, refresh rotation and reuse detection,
session creation/revocation, MFA enrollment/reset/recovery, account recovery
and authorized security-administration actions.

Audit payloads must not persist plaintext passwords, refresh credentials, TOTP
secrets, recovery codes or equivalent authentication secrets.

Organization-scoped security events are disclosed only through authorized
Organization context. Platform-level security events may require separately
authorized administrative visibility. A generic global Audit table cannot
become an implicit cross-Organization disclosure surface.

Existing Audit capability should be reused where it can satisfy attribution,
scope, retention and anti-disclosure requirements. A dedicated security-event
model is permitted only if EDS proves the existing owner insufficient.

## Tenant-isolation reconciliation

PATCH-058 closes known legacy Contact and Customer/Contact search isolation
gaps without redefining Customer or Contact domain ownership.

Contact authorization must derive through its canonical Customer/Organization
relationship or another already-authoritative Organization relationship.
PATCH-058 must not create a second Organization owner for Contact merely to
simplify authorization.

Customer-accessible lookup, search, list, detail and mutation routes must
authorize Organization scope before protected object disclosure.

Unauthorized, absent and cross-Organization targets must preserve the accepted
protected-not-found/anti-inference contract where required. Search totals,
pagination, ordering, timing-sensitive branches and empty states must not expose
hidden cross-Organization existence.

Legacy routes may be retained only when brought under the same authorization
and anti-inference guarantees as modern routes. Retirement, if preferable,
requires explicit EDS compatibility treatment.

## Bootstrap security

Bootstrap is an exceptional provisioning path, not a permanent alternate
authentication or administration channel.

Production bootstrap requires explicit enablement plus a bounded activation
window. Configuration must fail closed when required bootstrap controls are
missing, contradictory or expired.

Successful bootstrap completion must disable further use according to a
server-authoritative condition. Re-enablement is an explicit Human-controlled
operational action and must be attributable.

Bootstrap credentials and bootstrap state must not bypass mandatory
administrator MFA, current account security policy or later session controls.

Exact enablement, window, completion marker and safe re-enable mechanics are
deferred to EDS/IDS.

## Persistence architecture

PATCH-058 is expected to require persistence, but Architecture acceptance alone
does not authorize schema or migration creation.

The bounded persistence domains are:

- refresh-session and refresh-family lifecycle;
- MFA authenticator lifecycle;
- single-use recovery-code verifier state;
- Organization member-MFA policy;
- security-event state where existing Audit is insufficient;
- throttle state only if the accepted EDS selects durable database-backed
  throttling.

Refresh-session persistence owns session lifecycle only. It does not own User,
Organization, membership, role or engineering authority.

MFA persistence owns factor state only. Organization policy owns only the
bounded member-MFA requirement and cannot redefine membership or role.

TOTP secret material must be encrypted/protected at rest under explicit
application key-management authority. Recovery codes and refresh credentials
must use non-reversible verifier storage.

Security-event retention must be bounded and must separate useful security
metadata from unnecessary personal/network data.

Any schema change requires later accepted EDS, IDS and implementation authority
and must descend from sole Alembic head `e05600000008`.

## Security-version and invalidation contract

Current authoritative security state must remain able to terminate or constrain
previously issued authentication state.

Password reset/change, account disablement, MFA security changes and other
accepted identity-security changes must have deterministic invalidation
semantics.

Membership disablement/removal and role changes must not leave a stale session
with superseded Organization authority.

Organization member-MFA policy changes must have an explicit transition model
for already-authenticated members.

The implementation must not depend solely on waiting for bearer-token expiry
where the accepted security event requires immediate server-side revocation or
reauthorization.

EDS must define the security-version/session relationship and the exact
invalidation matrix without duplicating canonical identity or membership state.

## Reproducible release-security architecture

PATCH-058 extends the existing PATCH-042 production/release foundation rather
than replacing it.

A releasable SATCO revision must be attributable to a clean source revision and
a deterministic governed build process using repository-controlled dependency
locks and declared build inputs.

Backend, frontend, migration and other governed release artifacts must be bound
to immutable cryptographic digests. A mutable filename, tag or registry label
is not sufficient release identity.

Release qualification evidence must bind to the exact source revision and
artifact digests it qualifies. Evidence from another build or digest cannot be
silently inherited.

PATCH-058 produces release-security evidence and artifacts. It does not prove
that those artifacts have been deployed to a representative production
environment; that remains PATCH-060.

## CI quality and security gates

The release pipeline must execute deterministic automated gates appropriate to
the changed surface before an artifact becomes release-eligible.

The minimum governed families are:

- backend automated tests;
- frontend automated tests;
- static/type validation;
- production frontend build;
- migration graph/head validation;
- security-negative regression vectors;
- dependency vulnerability scanning;
- static application security analysis;
- secret scanning;
- container/image scanning where release images are produced;
- SBOM generation and validation;
- artifact digest and provenance generation;
- signature verification.

A failed mandatory gate prevents release eligibility unless an explicit
Human-governed exception exists under the accepted vulnerability/exception
contract.

CI execution is evidence-producing automation, not release approval authority.

## Vulnerability and exception governance

Scanner findings are inputs to Human security decisions and are not themselves
canonical approval or rejection authority.

EDS must freeze severity policy, applicability assessment, false-positive
handling, remediation expectations and release-blocking thresholds.

Any exception must be explicit, attributable, bounded in scope and time, and
bound to the affected revision/artifact/component or vulnerability identity as
appropriate.

An exception for one digest or component cannot silently authorize a different
artifact.

AI may summarize findings or propose remediation. AI may not approve,
self-authorize or inherit a vulnerability exception.

## SBOM and provenance

Each release candidate must have machine-verifiable software-component
inventory sufficient to identify governed direct and resolved dependencies for
the produced release artifacts.

The SBOM is evidence about the build composition; it is not an application
domain record.

Provenance must bind at minimum:

- source revision;
- build identity;
- relevant dependency-lock identity;
- produced artifact identities and digests;
- security/quality evidence references;
- SBOM identity;
- signing/attestation identity.

Exact formats and tooling are deferred to EDS/IDS, but evidence must be
machine-verifiable and reproducible enough to detect artifact substitution or
evidence mismatch.

## Artifact signing and trust

Release artifacts and/or their governed attestations must be cryptographically
signed under an explicit SATCO release trust model.

Signature verification must bind the approved artifact digest, not merely a
mutable artifact name or tag.

Signing authority is separate from application runtime authority and from AI.
A successful CI job alone does not constitute Human release approval.

EDS must freeze:

- signing mechanism;
- trust root;
- authorized signer model;
- key custody;
- key rotation and revocation;
- verification points;
- signer separation from ordinary build execution where required;
- handling of expired or revoked signing material.

Private signing material must never be committed to the repository or embedded
in release artifacts.

## Release dossier

A PATCH-058 release-security dossier binds the candidate release identity to
its evidence.

At minimum the dossier must reference:

- clean source revision;
- governed build identity;
- artifact identities and cryptographic digests;
- automated test and build results;
- migration graph/head evidence;
- security scan results;
- SBOM;
- provenance/attestation evidence;
- signature and verification evidence;
- explicit unresolved findings or Human-approved exceptions;
- Human release-security approval state.

The dossier must fail closed when mandatory evidence is absent, mismatched,
stale or bound to a different artifact/revision.

The dossier is not deployment certification. PATCH-060 consumes this
foundation and adds representative deployment and operational qualification.

## Independent security qualification

PATCH-058 closure requires independent security/threat review and
penetration-oriented negative evidence appropriate to the accepted attack
surface.

Qualification must include session theft/replay, refresh reuse, stale
authorization, credential stuffing, MFA/recovery abuse, tenant isolation,
anti-inference, bootstrap misuse, browser credential leakage and release
artifact/evidence substitution.

Qualification findings remain subject to Human disposition. Automated tools
and AI cannot self-close security findings.

## Accessibility and user security experience

MFA, recovery, session-management, expiry and security-error journeys must
remain keyboard operable, screen-reader understandable, responsive and
RTL-correct.

Security UX must not disclose protected account or Organization existence
through differentiated error content.

Mandatory security state must be explicit to the Human. The UI must not imply
that a local logout, hidden browser state or successful build is equivalent to
server revocation or release approval.

## Explicit non-scope

PATCH-058 does not own:

- commercial licensing, signed entitlements, seats, validity/grace/update or
  entitlement anti-rollback;
- representative production deployment or Commercial V1 Release Certification;
- DNS/certificate qualification, executed backup/restore, operational
  monitoring delivery, support exercises, capacity qualification or measured
  RPO/RTO/SLO;
- enterprise SSO/SAML/OIDC/SCIM;
- new IAM roles unrelated to the accepted Commercial V1 boundary;
- WebAuthn/passkeys beyond the accepted TOTP minimum;
- new engineering disciplines or reopened PATCH-051 through PATCH-057
  semantics;
- autonomous AI security, engineering or release authority.

## EDS-deferred decisions

EDS-058 must freeze exact:

- access-token lifetime and claim contract;
- refresh-cookie, CSRF and origin-validation contract;
- refresh-session/family state machine and reuse response;
- session listing and current/all/admin revocation contracts;
- security-version invalidation matrix;
- MFA enrollment/challenge/recovery state machines;
- Organization member-MFA policy transitions;
- sensitive-operation reauthentication set and window;
- throttle keys, persistence, limits, expiry, privacy and trusted-proxy rules;
- Security Audit event taxonomy, scope and retention;
- Contact/search tenant-isolation route reconciliation;
- bootstrap enablement/window/completion/re-enable contract;
- browser expiry, reload, logout and cross-tab behavior;
- CI gate matrix and release-blocking rules;
- vulnerability severity/exception/revalidation contract;
- SBOM and provenance formats;
- artifact identity/digest contract;
- signing/trust/key-rotation model;
- release dossier schema and verification rules;
- deterministic security-negative and release qualification vectors.

IDS-058 later freezes physical module/component topology, exact persistence
schema, migration sequence, encryption/key interfaces, route definitions,
middleware/dependency ordering, CI implementation topology, artifact/signature
tooling integration and implementation manifest.

## Governance disposition

This candidate is complete enough for independent Architecture Review.

Human Architecture Acceptance is not implied.

Architecture-058: CANDIDATE / READY FOR INDEPENDENT ARCHITECTURE REVIEW

## Human Architecture Acceptance

- Human Architecture Authority decision: **PASS / ACCEPTED / COMPLETE**.
- Acceptance date: 2026-09-23.
- Accepted after Independent Architecture Review returned **PASS / READY FOR HUMAN ARCHITECTURE ACCEPTANCE** with Critical/Major/Minor = 0/0/0 and one non-blocking Observation corrected before acceptance.
- The accepted architecture establishes server-authoritative rotating refresh sessions, short-lived memory-only access credentials, mandatory administrator TOTP MFA with single-use recovery codes, Organization-configurable member MFA, bounded reauthentication and recovery, credential-aware anti-enumeration throttling, Organization-aware security audit, authorization-before-lookup tenant isolation, bootstrap-window enforcement, and a reproducible signed release-security foundation.
- Existing canonical identity, membership, Organization and engineering authorities remain controlling. Human authority remains controlling for recovery, security administration, vulnerability exceptions, release approval/signing and engineering acceptance; AI remains advisory and non-authoritative.
- PATCH-059 entitlement/licensing authority and PATCH-060 deployment qualification/certification remain explicitly separate.
- This acceptance authorizes progression to the repository-consistent ADR preparation and independent review only.
- It does not authorize EDS-058, IDS-058, an Implementation Plan, implementation, migrations, production-code changes, database mutation, deployment, PATCH-059 or PATCH-060.

Architecture-058: HUMAN ACCEPTED / COMPLETE
