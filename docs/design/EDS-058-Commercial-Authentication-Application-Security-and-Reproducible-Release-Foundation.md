# EDS-058 — Commercial Authentication, Application Security & Reproducible Release Foundation

## 1. Status and authority

Status: **Proposed / Candidate — awaiting independent EDS review and Human EDS acceptance.**

Date: 2026-09-23.

This EDS derives from the Human-accepted PATCH-058 Discovery, Architecture-058 and ADR-031.

It defines engineering-design contracts for PATCH-058 only. It does not authorize IDS-058, an Implementation Plan, implementation, migrations, production-code changes, database mutation, deployment, PATCH-059 or PATCH-060.

Human authority remains controlling for account/MFA recovery, security administration, role and membership administration, vulnerability exceptions, signing authorization, release approval and all PATCH acceptance gates. AI remains advisory and non-authoritative.

## 2. Preserved canonical owners

PATCH-058 shall not create competing ownership for existing canonical entities.

- User remains canonical for identity, password hash, account state, platform role and security-version state.
- Organization and UserOrganizationMembership remain canonical for tenant membership and Organization-scoped authority.
- Customer remains the canonical Organization-bearing owner through which Contact authorization is derived.
- Contact shall not receive a second independent Organization owner solely for PATCH-058 authorization.
- Existing engineering Evidence, Technical Report, standards, Memory and discipline-domain owners remain unchanged.
- Refresh-session state owns session lifecycle only and shall not become identity or membership authority.
- MFA/recovery state owns factor and recovery lifecycle only and shall not become account authority.
- Security-event records are operational/security evidence and shall not become authorization or engineering truth.
- Release manifests, SBOMs, provenance, attestations, signatures and vulnerability evidence are release-pipeline evidence and shall not become application-domain or engineering records.

Where authorization depends on canonical state, current canonical state is authoritative over stale session claims.

## 3. Authentication assurance model

PATCH-058 shall use a server-authoritative authentication model composed of:

1. a short-lived access credential;
2. a server-tracked refresh session/family;
3. current User security-version state;
4. current account, Organization-membership and role authority;
5. MFA assurance where policy requires it;
6. recent-authentication/step-up assurance for designated sensitive operations.

Possession of a syntactically valid access or refresh credential alone shall not grant authority when server-authoritative security state has invalidated that authority.

Missing required security-version or session-binding claims shall fail closed after the compatibility boundary defined by the accepted implementation plan. Silent fallback to an assumed current version is not permitted as the steady-state PATCH-058 contract.

## 4. Access credential contract

The access credential shall:

- be short-lived;
- be issued only after successful authentication or refresh qualification;
- carry the minimum claims required to bind the authenticated principal and security/session context;
- be validated for signature, expiry and all EDS/IDS-designated mandatory security claims;
- be rejected when its security/session context is no longer current;
- never act as the canonical source for mutable role, membership or account authority.

For the browser client, the access credential shall be held only in browser memory.

The browser client shall not persist the access credential in `localStorage`, `sessionStorage`, IndexedDB or another durable browser-accessible credential store.

Exact access lifetime, claim names, issuer/audience policy, token identifier requirements and cryptographic configuration shall be frozen by IDS-058 consistently with this EDS.

## 5. Refresh session and family state machine

A refresh credential shall correspond to server-side refresh-session state and shall never be accepted solely as a self-contained bearer assertion.

The server shall persist only a non-reversible verifier for the refresh secret. Raw refresh secrets shall not be persisted in application storage, audit records or logs.

The logical refresh-family lifecycle is:

`ACTIVE -> ROTATED -> ACTIVE_SUCCESSOR`

with terminal or security states including:

`EXPIRED`, `REVOKED`, `REUSE_DETECTED`.

Each successful refresh shall:

1. validate the presented refresh credential and server-side verifier;
2. validate expiry and revocation state;
3. validate current User/account/security authority;
4. validate applicable Organization-membership authority;
5. atomically consume/rotate the presented refresh state;
6. create or activate exactly one valid successor;
7. issue the next short-lived access credential;
8. return the replacement refresh credential through the accepted protected browser transport.

A consumed/rotated refresh credential shall not be reusable.

Reuse of a consumed or otherwise invalidated credential shall be treated as a security event and shall revoke at least the affected refresh family.

Concurrent refresh attempts shall not result in multiple independently valid successors from the same predecessor.

Exact persistence constraints, transaction/locking mechanics and race-handling implementation belong to IDS-058.

## 6. Session expiry and revocation contract

Refresh sessions shall have explicit creation, expiry and revocation semantics.

The platform shall support at minimum:

- logout of the current session;
- revocation of all sessions belonging to the current User;
- authorized administrator revocation where permitted by canonical authority;
- family revocation after refresh reuse detection;
- invalidation caused by security-relevant account changes.

Client-side deletion alone is not sufficient logout.

A server-side session that has been revoked or expired shall not regain validity through possession of an older credential.

Session-listing surfaces, if exposed, shall reveal only bounded safe metadata required for Human recognition and administration. Raw credentials, verifiers and sensitive network/device fingerprints shall never be returned.

## 7. Security-version invalidation matrix

PATCH-058 shall use deterministic invalidation for security-relevant changes.

At minimum, the following events shall invalidate previously issued authentication authority as specified below:

| Event | Existing access authority | Refresh sessions | Required outcome |
|---|---|---|---|
| Password change/reset/recovery | invalidated | revoked | reauthentication required |
| MFA reset/removal affecting required assurance | invalidated | revoked | required MFA enrollment/authentication before protected continuation |
| Account disable | invalidated | revoked | authentication denied |
| Account re-enable | old authority remains invalid | old sessions remain revoked | fresh authentication required |
| Platform role change | stale authority invalidated | requalified or revoked according to IDS contract | current role enforced |
| Organization membership disable/removal | stale Organization authority invalidated | affected Organization authority must not continue | authorization denied |
| Organization membership role change | stale role authority invalidated | affected authority requalified or revoked | current role enforced |
| Organization MFA-policy tightening | insufficient assurance invalidated for protected continuation | session may not bypass new requirement | MFA requirement enforced |
| Administrator security revocation | invalidated as targeted | targeted session/family/all sessions revoked | fresh qualification required |

IDS-058 shall define the physical security-version/session-version mechanism and whether invalidation uses one or more monotonic/versioned values.

The mechanism shall be deterministic, race-safe and based on current server-authoritative state.

## 8. MFA policy contract

Administrator MFA is mandatory.

The minimum accepted administrator factor for PATCH-058 is TOTP, with single-use recovery codes.

An Organization may require MFA for its engineer/member population according to Organization-scoped policy.

The platform shall not make member MFA globally mandatory by default.

An Organization policy may strengthen member MFA requirements but shall not weaken mandatory platform administrator MFA.

A User subject to mandatory MFA shall not receive the protected authenticated assurance required for normal privileged continuation until the required MFA state is satisfied.

Policy evaluation shall use current canonical role/membership/Organization state rather than stale client state.

## 9. TOTP enrollment and verification state machine

The logical TOTP lifecycle shall include at minimum:

`NOT_ENROLLED -> ENROLLMENT_PENDING -> VERIFIED/ACTIVE`

and controlled transitions for:

`RESET_REQUIRED`, `DISABLED` where policy permits, and replacement/re-enrollment.

Enrollment shall require proof that the User can successfully generate a valid TOTP before the factor becomes ACTIVE.

TOTP secrets shall be protected at rest under an explicit application key-management boundary.

TOTP secrets shall not be written to logs, audit events, URLs, analytics, client persistence or release evidence.

Verification shall enforce bounded replay resistance and accepted clock-skew policy.

Exact secret protection, key identifiers, rotation strategy, TOTP parameters, replay-state mechanism and clock-skew limits belong to IDS-058.

## 10. Recovery-code contract

Recovery codes shall:

- be generated using a cryptographically secure mechanism;
- be presented to the Human only through the bounded enrollment/regeneration flow;
- be persisted only as non-reversible verifiers;
- be single-use;
- be invalid after successful consumption;
- be replaced as a governed set when regenerated;
- never be logged, audited in raw form or exposed through later read APIs.

Recovery-code use shall be a security event.

Recovery-code regeneration shall require current authenticated authority and the reauthentication/step-up assurance designated by this EDS.

Administrator recovery codes shall not weaken mandatory administrator MFA policy; they are a bounded recovery factor, not a permanent MFA bypass.

## 11. Account and MFA recovery contract

Account and MFA recovery shall remain Human-controlled, bounded and attributable.

Recovery shall not be performed autonomously by AI, scanners, background automation or unauthenticated client logic.

Where recovery requires a temporary credential or recovery artifact, it shall be purpose-bound, expiring and one-time.

Recovery responses shall avoid account enumeration.

A successful password or MFA recovery shall invalidate stale authentication authority according to the security-version matrix.

Administrative recovery actions shall require current authorized Human authority and shall create safe attributable security evidence.

The recovery design shall preserve last-administrator protections and shall not create a path to silently replace Organization or platform authority.

## 12. Sensitive-operation reauthentication

PATCH-058 shall require recent authentication and/or step-up assurance for security-sensitive operations.

The designated set shall include at minimum operations capable of materially changing authentication or security authority, including:

- password/security-credential changes;
- MFA reset or regeneration;
- recovery-code regeneration;
- revocation of all sessions where applicable;
- high-impact role/account/membership security administration;
- Organization MFA-policy changes;
- security/vulnerability exception approval where performed through the application boundary.

Reauthentication shall not rely solely on the existence of a long-lived client session.

The exact recent-authentication window, required assurance level per operation and challenge behavior shall be frozen by IDS-058.

## 13. Authentication throttling and anti-enumeration

Authentication, MFA and recovery entry points shall implement bounded abuse controls.

Throttling shall consider both:

- normalized credential identity or equivalent non-enumerating principal key; and
- trusted network context.

Network context shall be derived only through explicitly trusted proxy boundaries. Untrusted forwarding headers shall not become authoritative client identity.

Controls shall resist credential stuffing, brute-force attempts, MFA guessing and recovery abuse without exposing whether an account exists.

Authentication and recovery responses shall use generic externally observable behavior where distinction would create enumeration risk.

Throttle state may use PostgreSQL or a bounded external security store. The physical persistence choice belongs to IDS-058.

EDS-level requirements apply regardless of that physical choice:

- deterministic bounded counters/windows/backoff;
- safe concurrency;
- explicit expiry/retention;
- no raw password/OTP/recovery secret storage;
- no cross-Organization disclosure through administrative visibility;
- safe audit of meaningful threshold/security events.

## 14. Security event and audit contract

Security evidence shall cover at minimum:

- authentication success/failure where appropriate;
- meaningful throttle threshold events;
- refresh rotation/reuse/revocation;
- logout and session revocation;
- MFA enrollment/reset/recovery-code lifecycle events;
- account/password/MFA recovery;
- security-relevant account, role and membership administration;
- Organization MFA-policy changes;
- bootstrap security events;
- vulnerability-exception and release-security approval events where application-owned.

Security evidence shall never contain passwords, raw refresh credentials, TOTP secrets or raw recovery codes.

Organization-scoped events shall be visible only under current Organization authorization. Platform-wide security evidence shall require separate platform authority.

The existing generic Audit model may be extended if it can satisfy these semantics without weakening its current contracts. A dedicated security-event model shall be introduced only if later design proves the generic model insufficient.

Security-event evidence is attributable operational evidence; it is not engineering truth and does not independently grant authority.


## 15. Tenant isolation and authorization-before-lookup

PATCH-058 shall reconcile legacy Contact and Customer/Contact search paths with the established Organization authorization model.

Contact authorization shall be derived through its canonical Customer relationship and the Customer's canonical Organization ownership.

PATCH-058 shall not introduce a second independent Organization owner on Contact solely to solve authorization.

For every customer-accessible lookup, list, search, detail and mutation surface involving Organization-owned or Organization-derived data:

1. current authenticated authority shall be established;
2. current Organization context shall be established where required;
3. authorization shall be applied before protected resource disclosure;
4. inaccessible resources shall not be distinguishable from protected non-existence where such distinction would disclose tenant information.

Direct object lookup followed by authorization is acceptable only where the implementation guarantees that no protected existence, attributes, timing distinction or side effect is disclosed before authorization.

Authorization shall use current canonical membership/account/role state rather than trusting stale client claims.

## 16. Search, count and pagination anti-inference contract

Tenant isolation applies to search metadata as well as returned objects.

Customer/Contact search shall not leak cross-Organization information through:

- result rows;
- total counts;
- page counts;
- pagination boundaries;
- ordering artifacts;
- empty/non-empty distinctions;
- filter metadata;
- identifiers;
- error distinctions;
- timing behavior that creates a practical protected-existence oracle.

Organization authorization shall therefore be applied before the protected result population is counted, paginated or exposed.

Combined/global search shall preserve the same Organization boundary independently for every included resource class.

Legacy search or Contact routes may remain only where they satisfy the same authorization and anti-inference contract. Route retirement or compatibility mechanics belong to IDS-058 and the later accepted Implementation Plan.

## 17. Browser authentication transport and CSRF contract

The browser shall keep the short-lived access credential only in memory.

The refresh credential shall be transported using a server-issued cookie that is at minimum:

- `HttpOnly`;
- `Secure` in production;
- bounded to the narrowest practical Path/Domain scope;
- governed by an explicit SameSite policy.

Because browser cookie transport can create ambient credential authority, refresh/logout/session-changing endpoints shall use explicit CSRF defenses appropriate to the selected transport.

SameSite behavior alone shall not be treated as the complete CSRF contract.

The accepted design shall include server-side origin/request validation and/or a bounded anti-CSRF mechanism such that a third-party origin cannot exercise refresh-session authority merely because the browser carries the refresh cookie.

CORS, trusted-host and trusted-proxy configuration shall remain fail-closed production security boundaries.

Exact cookie names, Path/Domain, SameSite value, CSRF token/header mechanism, origin policy and cross-origin development exceptions belong to IDS-058.

## 18. Browser credential and stale-session lifecycle

The frontend authentication lifecycle shall handle at minimum:

- initial authentication;
- MFA-required continuation;
- access expiry;
- refresh success and rotation;
- refresh expiry/revocation;
- reuse/security invalidation response;
- current-session logout;
- logout-all completion;
- password/account/MFA invalidation;
- membership/role authority changes;
- Organization MFA-policy changes;
- first-login continuation;
- stale or unauthorized protected navigation.

A stale authenticated UI shall not be treated as security authority.

When server authority rejects the current authentication context, the client shall remove in-memory access authority and transition to the appropriate safe authentication/recovery state.

Cross-tab behavior shall not restore revoked authority from browser persistence.

Credentials, activation secrets, reset secrets and recovery artifacts shall be removed from browser-visible URLs as early as safely possible and shall not be propagated into navigation history, analytics or unrelated requests.

Security UX shall preserve accessibility, responsive behavior and RTL support.

## 19. Bootstrap lifecycle contract

Production bootstrap is an exceptional bounded provisioning mechanism, not a permanent alternate authentication or administration path.

Bootstrap use shall require all applicable conditions:

1. explicit server-side enablement;
2. a valid bounded bootstrap window;
3. valid bootstrap authentication/secret qualification;
4. server-authoritative confirmation that bootstrap remains eligible.

If enablement is absent, the window is absent/expired, or bootstrap eligibility has ended, the operation shall fail closed.

Successful completion of the intended bootstrap shall disable further bootstrap use server-authoritatively.

Re-enabling bootstrap after completion shall require an explicit attributable Human administrative action under the later accepted operational contract.

Bootstrap shall not become a mechanism for bypassing mandatory administrator MFA, current account policy or normal server-authoritative session controls after initial provisioning.

Bootstrap secrets shall not be logged or returned through diagnostic surfaces.

## 20. Bounded PATCH-058 persistence decision

PATCH-058 is expected to require bounded new security persistence.

Permitted logical persistence domains are limited to what is necessary for:

- refresh sessions/families and rotation/revocation lineage;
- MFA authenticator state;
- hashed single-use recovery-code state;
- Organization member-MFA policy;
- security-event evidence where the existing Audit model is insufficient;
- authentication-throttle state if the accepted physical design selects database persistence.

This EDS does not authorize a schema or migration.

It does not authorize duplication of canonical User, Organization, membership, Customer, Contact or engineering ownership.

Any later migration shall be forward-only from the repository's sole accepted Alembic head at implementation time and shall require accepted IDS-058 and Implementation Plan authority before creation.

Physical tables, columns, constraints, indexes, encryption fields, retention mechanics and migration identifiers belong to IDS-058.

## 21. Reproducible release qualification contract

PATCH-058 shall extend, not replace, the accepted PATCH-042 operational/release foundation.

A PATCH-058 release candidate shall be attributable to a clean source revision and deterministic governed build inputs.

Release eligibility shall bind the exact source revision to the exact artifacts and evidence being approved.

At minimum, governed release qualification shall cover:

- deterministic backend tests;
- deterministic frontend tests;
- frontend type/static qualification;
- production frontend build;
- migration-graph qualification;
- security-negative regression vectors;
- dependency vulnerability scanning;
- SAST;
- secret scanning;
- container/image scanning where an image is a governed release artifact;
- SBOM generation;
- provenance/attestation generation;
- cryptographic artifact/signature verification;
- release-dossier validation.

A required failed gate shall block release eligibility unless an applicable Human-approved vulnerability/security exception exists under the exception contract.

CI, scanners and AI may produce or summarize evidence. They shall not independently approve failed gates, vulnerability exceptions or release eligibility.

## 22. Immutable artifact identity

Governed backend, frontend, migration and other designated release artifacts shall be identified by cryptographic digest.

Mutable names, tags, filenames or registry labels alone are insufficient release identity.

Evidence referring to an artifact shall bind to the exact artifact digest to which that evidence applies.

Replacement of artifact content without a corresponding digest/evidence change shall invalidate release qualification.

The release dossier shall detect and fail closed on mismatches between source revision, artifact digest, scan/SBOM/provenance/signature evidence and the candidate being approved.

Exact digest algorithms and artifact packaging conventions belong to IDS-058, subject to current accepted cryptographic practice and repository/tooling compatibility.

## 23. Vulnerability-gate and exception contract

Security findings shall be evaluated under a deterministic governed severity/gate policy.

The exact blocking matrix shall be frozen by IDS-058, preserving the accepted PATCH-042 security floor and Human exception authority.

A vulnerability/security exception shall be:

- explicitly Human-approved;
- attributable;
- scoped to the exact affected revision/artifact/component/finding as applicable;
- bound to artifact digest where artifact identity exists;
- justified;
- time-bounded;
- accompanied by compensating controls where required;
- subject to expiry and revalidation/retest.

An exception for one artifact digest shall not silently authorize a replacement artifact with a different digest.

An expired, revoked or mismatched exception shall not satisfy a release gate.

AI, scanners, CI and automated policy engines shall not possess independent exception-approval authority.

## 24. SBOM contract

Each designated release artifact shall have a machine-readable SBOM or an explicitly governed release-level SBOM that unambiguously binds included artifacts/components.

The SBOM shall identify resolved components and dependency versions sufficiently to support vulnerability qualification and release traceability.

SBOM evidence shall bind to the release candidate/artifact set for which it was generated.

An SBOM reference that cannot be verified against the governed release candidate shall not satisfy the release gate.

Exact SBOM format, generator, normalization and storage conventions belong to IDS-058.

## 25. Provenance and attestation contract

Release provenance shall provide machine-verifiable evidence binding at minimum:

- source revision;
- governed build inputs;
- dependency/lock identities;
- resulting artifact digests;
- relevant qualification evidence;
- SBOM identity/reference;
- signing/trust evidence.

Provenance shall not become application-domain or engineering truth.

Provenance generation may be automated, but automated generation does not confer Human release approval.

The accepted implementation shall prevent a provenance record for one artifact/revision from being reused as evidence for a different artifact/revision.

Exact attestation format, builder identity and verification mechanism belong to IDS-058.

## 26. Cryptographic signing and trust contract

Designated backend, frontend, migration and release artifacts shall be cryptographically authenticated through signatures that bind the exact governed artifact digests.

The signing design shall define:

- trust root;
- authorized signer identity;
- key custody boundary;
- signing authorization boundary;
- verification procedure;
- key rotation;
- key revocation;
- handling of expired/revoked signing authority;
- failure behavior when trust evidence cannot be verified.

Private signing keys shall not be committed to the repository or embedded in release artifacts.

Human authority controls release approval and signing authorization.

Cryptographic signing execution may be automated only within an explicitly Human-authorized signing policy and controlled signer boundary.

CI, AI or other automation shall not independently create its own signing authority, broaden signer policy or convert successful signing into Human release approval.

## 27. Release dossier contract

Every release candidate qualified under PATCH-058 shall have a release dossier binding at minimum:

- clean source revision identity;
- governed build-input identity;
- backend/frontend/migration and other designated artifact digests;
- required test/type/build evidence;
- migration-graph evidence;
- security-negative evidence;
- dependency/SAST/secret/container scan evidence as applicable;
- SBOM identity/reference;
- provenance/attestation identity/reference;
- signature and trust-verification evidence;
- unresolved security findings;
- applicable Human-approved exceptions;
- attributable Human release-security approval evidence.

The dossier shall fail closed when required evidence is absent, mismatched, expired or bound to a different candidate/artifact.

The dossier is release-security evidence. It is not PATCH-060 production deployment certification.

PATCH-060 may consume a valid PATCH-058 dossier as an input to representative deployment qualification, but shall independently establish its own deployment/operational evidence.

## 28. CI authority and deterministic gate behavior

CI is an evidence-producing and policy-enforcement mechanism, not a Human authority.

Required gates shall be deterministic from the governed source revision, configured policy and referenced evidence.

A CI success result shall not override:

- failed or missing mandatory evidence;
- an invalid signature;
- a mismatched artifact digest;
- an expired/mismatched vulnerability exception;
- required Human approval;
- PATCH governance gates.

CI definitions and security-gate configuration shall themselves be version-controlled and attributable to the source/release process.

The exact CI provider and physical workflow topology belong to IDS-058.

## 29. Independent security qualification contract

Before PATCH-058 closure, independent security qualification shall include threat/security review and penetration-oriented negative evidence.

Qualification shall cover at minimum:

- access/refresh credential theft scenarios;
- refresh replay and reuse detection;
- concurrent refresh race behavior;
- stale security-version/role/membership authority;
- password and MFA brute-force/credential stuffing;
- MFA enrollment/reset/recovery abuse;
- recovery-code replay;
- account enumeration;
- Contact and Customer/Contact cross-Organization disclosure;
- authorization-before-lookup and anti-inference;
- bootstrap outside the allowed lifecycle;
- browser credential leakage and CSRF boundaries;
- privilege/security-administration misuse;
- session revocation/logout behavior;
- release artifact substitution;
- digest/evidence mismatch;
- SBOM/provenance mismatch;
- signature/trust verification failure;
- vulnerability-exception scope/expiry/digest mismatch.

AI and automation may assist qualification but shall not independently accept security findings or the PATCH gate.


## 30. Failure and fail-closed semantics

Security-sensitive ambiguity shall fail closed.

At minimum:

- missing/invalid/expired access authority shall not silently become authenticated authority;
- invalid/revoked/expired/reused refresh credentials shall not create a new valid session;
- missing required security-version/session claims shall not silently default to an assumed current value in steady state;
- insufficient MFA assurance shall not bypass a required MFA policy;
- failed reauthentication shall not execute the sensitive operation;
- unavailable or indeterminate Organization authority shall not disclose protected resources;
- bootstrap uncertainty shall not enable bootstrap;
- missing/mismatched release evidence shall not satisfy a release gate;
- unverifiable signatures/trust evidence shall not qualify an artifact;
- expired/mismatched security exceptions shall not satisfy a blocking gate.

Externally observable failures shall avoid unnecessary account, tenant or protected-resource disclosure.

Internal diagnostics may retain bounded safe reason classification where access to those diagnostics is independently authorized.

## 31. Privacy, retention and sensitive-data minimization

PATCH-058 security state shall follow data-minimization principles.

Only information required for security qualification, attribution, investigation, bounded administration or release traceability shall be retained.

Raw passwords, refresh secrets, TOTP secrets, raw recovery codes and private signing keys shall never be placed in audit/security-event evidence.

Network/device metadata used for session recognition, throttling or investigation shall be bounded and shall not become an unrestricted tracking profile.

Retention shall be explicit for:

- refresh-session/family state;
- throttle state;
- security events;
- recovery state;
- release-security evidence;
- vulnerability exceptions.

Exact retention periods and deletion/archival mechanics belong to IDS-058 or later accepted operational policy where appropriate.

Deletion or expiry of operational evidence shall not silently mutate accepted engineering records.

## 32. Concurrency and atomicity requirements

Security state transitions that could otherwise create duplicate authority or bypass revocation shall be atomic at the logical contract level.

This includes at minimum:

- refresh rotation;
- refresh reuse detection and family revocation;
- recovery-code consumption;
- MFA activation/reset transitions;
- security-version changes;
- last-administrator protections affected by security administration;
- vulnerability-exception state transitions where application-managed.

Concurrent requests shall not produce multiple valid successors from a single-use credential or recovery artifact.

Physical locking, transaction isolation, uniqueness constraints and retry mechanics belong to IDS-058.

## 33. Logical operation inventory

PATCH-058 shall support the following logical operation families where applicable:

Authentication:
- primary sign-in;
- MFA challenge completion;
- refresh;
- current-session logout;
- all-session logout/revocation;
- current-session/security-context inspection.

MFA and recovery:
- begin TOTP enrollment;
- verify/activate TOTP;
- regenerate recovery codes;
- consume a recovery code;
- authorized MFA reset/recovery;
- account/password recovery under existing onboarding/account authority.

Session administration:
- list bounded recognizable sessions where exposed;
- revoke a selected authorized session;
- administrator session revocation under current authority.

Organization security:
- read member-MFA policy;
- change member-MFA policy under authorized Human administration.

Security evidence:
- authorized Organization-scoped security-event review;
- authorized platform security-event review where applicable.

Bootstrap:
- bounded bootstrap eligibility and execution under the bootstrap lifecycle contract.

Release security:
- generate/validate qualification evidence;
- generate/validate SBOM;
- generate/validate provenance;
- sign/verify governed artifacts under authorized signing policy;
- evaluate vulnerability gates;
- record/validate Human-approved exceptions;
- assemble/validate the release dossier.

This inventory is logical. Endpoint paths, method names, modules and physical service boundaries belong to IDS-058.

## 34. Authorization and Human-control matrix

At minimum, authorization shall preserve these boundaries:

| Capability | Required authority |
|---|---|
| Normal authentication/MFA completion | subject User under applicable policy |
| Current-session logout | authenticated subject/session context |
| Revoke own sessions | authenticated subject with required reauthentication where designated |
| Reset another User's MFA | explicitly authorized Human administrator |
| Administrative account recovery | explicitly authorized Human administrator |
| Change Organization member-MFA policy | authorized Organization security/admin authority |
| Change platform administrator security state | authorized platform Human authority |
| View Organization security evidence | current authorized Organization authority |
| View platform-wide security evidence | separate platform authority |
| Approve vulnerability/security exception | authorized Human security authority |
| Authorize release signing | authorized Human release/security authority |
| Approve release eligibility | authorized Human release authority |

AI, scanners and CI have no independent authority in this matrix.

Exact role/action mapping shall be frozen by IDS-058 using existing canonical role/membership authority unless an accepted design explicitly requires otherwise.

## 35. Performance and boundedness

Security controls shall remain commercially usable without weakening their guarantees.

Design shall avoid unbounded:

- session-family traversal;
- security-event fan-out;
- search before Organization scoping;
- throttle-state growth;
- release-evidence scanning during ordinary application requests;
- synchronous external security-tool dependencies in normal authenticated request paths.

Session/security-version validation shall use bounded access patterns suitable for normal authenticated traffic.

Search authorization shall scope the population before count/pagination.

Release qualification may be asynchronous/offline relative to ordinary application runtime, but its resulting evidence shall remain deterministic and attributable.

Exact indexes, cache strategy, query plans, batch sizes and performance budgets belong to IDS-058/Implementation Plan.

## 36. Observability and operational safety

PATCH-058 shall expose sufficient safe observability to diagnose authentication/session/security and release-gate failures without exposing secrets.

Observability shall distinguish bounded categories such as:

- authentication rejection;
- MFA requirement/failure;
- refresh expiry/revocation/reuse;
- throttle enforcement;
- authorization denial;
- bootstrap denial;
- release-gate failure;
- signature/trust verification failure;
- evidence mismatch.

Logs/metrics shall not include raw credentials or secrets.

Operational observability does not create authorization or release-approval authority.

PATCH-060 remains responsible for representative production monitoring/alert-delivery qualification and operational certification.

## 37. Compatibility and migration behavior

PATCH-058 shall preserve accepted account/onboarding behavior from PATCH-041 except where stronger security requirements explicitly require a controlled transition.

Existing password hashes and canonical User/account identity remain valid inputs to the strengthened authentication model.

Existing `auth_version` semantics may be strengthened or generalized into the accepted security-version mechanism, but missing required security-version claims shall not remain silently equivalent to a current value in steady state.

Legacy refresh JWT behavior shall transition to server-authoritative refresh sessions under a bounded compatibility/cutover plan.

Legacy browser credential persistence shall transition to the accepted memory-only access model.

Legacy Contact/search behavior shall be reconciled to current Organization authorization without redefining Contact ownership.

PATCH-042 release manifest, digest, exception, configuration and operational foundations shall be extended/reconciled rather than duplicated with competing release authority.

Exact cutover sequencing belongs to IDS-058 and the accepted Implementation Plan.

## 38. Security-negative qualification vectors

The implementation qualification plan shall include deterministic negative vectors proving at minimum:

1. reused refresh credential cannot create valid successor authority;
2. concurrent refresh cannot create multiple valid successors;
3. revoked/expired session cannot refresh;
4. password/security-version change invalidates stale authority;
5. disabled account cannot continue through stale credentials;
6. removed/disabled membership cannot disclose Organization data;
7. stale role cannot preserve removed privilege;
8. mandatory administrator MFA cannot be bypassed;
9. Organization member-MFA tightening cannot be bypassed by an existing insufficient-assurance session;
10. recovery code cannot be reused;
11. recovery flow does not enumerate accounts;
12. throttling does not create a credential-existence oracle;
13. Contact lookup cannot disclose another Organization's Contact;
14. Customer/Contact search totals/pagination cannot disclose another Organization's population;
15. bootstrap fails outside enable/window/eligibility boundary;
16. third-party origin cannot exercise refresh authority through ambient cookie state;
17. browser logout/revocation cannot be reversed using stale client state;
18. mismatched artifact digest cannot inherit scan/SBOM/provenance/signature evidence;
19. expired/mismatched vulnerability exception cannot satisfy a gate;
20. invalid/revoked signing trust cannot qualify a release artifact.

IDS-058 may add vectors but shall not remove these guarantees without a new Human-approved design decision.

## 39. PATCH-059 and PATCH-060 separation

PATCH-058 shall not implement or define commercial entitlement authority.

The following remain PATCH-059 concerns:

- signed commercial entitlements/licenses;
- package-access enforcement;
- seat limits;
- entitlement validity/grace;
- entitlement update;
- entitlement anti-rollback;
- entitlement administration UX.

The following remain PATCH-060 concerns:

- representative production deployment;
- DNS/certificate deployment evidence;
- executed backup/restore qualification;
- monitoring/alert-delivery qualification;
- support exercise;
- rollback/upgrade operational qualification;
- capacity qualification;
- measured RPO/RTO/SLO evidence;
- final Commercial V1 deployment/release certification.

PATCH-058 release-security evidence may be consumed by PATCH-060 but does not itself certify a production deployment.

## 40. Explicit non-scope

PATCH-058 does not include:

- SSO/SAML/OIDC/SCIM;
- WebAuthn/passkeys beyond the accepted TOTP minimum;
- new IAM role families unless separately Human-approved;
- billing, finance, ERP, BPM, CRM or contract automation;
- HA/Kubernetes/multi-region/SaaS orchestration;
- customer-managed deployment architecture;
- new engineering disciplines;
- reopening accepted PATCH-051 through PATCH-057 engineering semantics;
- autonomous AI security administration;
- autonomous AI vulnerability-exception approval;
- autonomous AI release approval/signing authority;
- production/customer database operations during implementation qualification;
- PATCH-059 entitlement implementation;
- PATCH-060 production deployment/certification.

## 41. IDS-058 obligations

IDS-058 shall freeze the physical design required to implement this EDS, including at minimum:

1. access-token lifetime, mandatory claims, issuer/audience/token/session/security-version binding and cryptographic configuration;
2. refresh-session/family physical state, verifier design, rotation transaction, expiry, revocation, reuse detection and concurrency controls;
3. cookie attributes and CSRF/origin-defense mechanics;
4. session listing/revocation APIs and safe metadata;
5. security-version physical mechanism and invalidation integration points;
6. MFA/TOTP physical state, secret protection/key-management interfaces, replay handling and clock-skew policy;
7. recovery-code representation/verification and lifecycle;
8. Organization member-MFA policy representation and transition behavior;
9. sensitive-operation reauthentication set, assurance levels and recent-auth window;
10. throttle persistence, key derivation, trusted-network handling, windows/backoff, retention and privacy;
11. security-event model/taxonomy, persistence choice, visibility and retention;
12. Contact and Customer/Contact query/repository/service authorization reconciliation;
13. bootstrap enforcement integration and server-authoritative completion/re-enable mechanics;
14. database schema/index/constraint design and forward migration strategy if persistence is required;
15. frontend auth/MFA/recovery/session state and credential-removal mechanics;
16. CI workflow topology and deterministic quality/security gate matrix;
17. vulnerability severity/blocking/revalidation and exception-validation mechanics;
18. SBOM format/tooling/storage/reference verification;
19. provenance/attestation format, builder identity and verification;
20. artifact packaging, immutable identity and digest algorithms;
21. signing technology, trust root, signer boundary, key lifecycle and verification tooling;
22. release-dossier schema, assembly and validation;
23. security-negative qualification implementation mapping;
24. observability surfaces and secret-redaction requirements.

IDS-058 shall not weaken the Human/AI authority boundary or move PATCH-059/PATCH-060 scope into PATCH-058.

## 42. Traceability matrix

| Accepted source decision | EDS-058 contract |
|---|---|
| Server-authoritative rotating refresh sessions | §§3-7 |
| Memory-only short-lived browser access credential | §§4, 17-18 |
| Mandatory administrator TOTP MFA | §§8-12 |
| Organization-configurable member MFA | §§8, 34 |
| Human-controlled recovery | §§10-12, 34 |
| Reauthentication for sensitive operations | §12 |
| Credential/network-aware anti-enumeration throttling | §13 |
| Safe attributable security audit | §14 |
| Contact/search tenant-isolation reconciliation | §§15-16 |
| Browser transport/CSRF hardening | §§17-18 |
| Bounded bootstrap lifecycle | §19 |
| Bounded security persistence | §20 |
| Deterministic CI/security qualification | §§21, 28-29 |
| Immutable artifact digests | §22 |
| Human-governed vulnerability exceptions | §23 |
| SBOM | §24 |
| Provenance/attestation | §25 |
| Cryptographic signing/trust | §26 |
| Release dossier | §27 |
| Fail-closed security semantics | §30 |
| Human authority / AI non-authority | §§1, 34 |
| PATCH-059/PATCH-060 separation | §§39-40 |

## 43. EDS self-review

Traceability against accepted PATCH-058 Discovery: PASS.

Traceability against Human-accepted Architecture-058: PASS.

Traceability against Human-accepted ADR-031: PASS.

Human Authority: PASS.

AI non-authority: PASS.

Canonical source-owner preservation: PASS.

Server-authoritative session/revocation semantics: PASS.

Mandatory administrator MFA and bounded member-MFA policy: PASS.

Recovery and reauthentication boundaries: PASS.

Tenant isolation/authorization-before-lookup/anti-inference: PASS.

Browser credential/CSRF security contract: PASS.

Bootstrap lifecycle: PASS.

Bounded persistence decision: PASS — likely security persistence required, but no schema or migration is authorized by this EDS.

PATCH-042 release-foundation preservation: PASS.

CI/security gates, vulnerability exceptions, SBOM, provenance, signing trust and release dossier: PASS.

PATCH-059/PATCH-060 separation: PASS.

No implementation, migration, deployment or production/customer DB operation is authorized: PASS.

## 44. Governance disposition

EDS-058 candidate is **COMPLETE / READY FOR INDEPENDENT EDS REVIEW**.

Human EDS acceptance is not implied.

IDS-058, Implementation Plan, implementation, migration, production-code changes, database mutation, staging, commit, push, deployment, PATCH-059 and PATCH-060 remain unauthorized.

EDS-058: CANDIDATE / READY FOR INDEPENDENT EDS REVIEW

## 45. Human EDS Acceptance

- Human Engineering Design Authority decision: **PASS / ACCEPTED / COMPLETE**.
- Acceptance date: 2026-09-23.
- Accepted after Independent EDS Review returned **PASS / READY FOR HUMAN EDS ACCEPTANCE** with Critical/Major/Minor = 0/0/0.
- Server-authoritative session and refresh-family semantics, deterministic security invalidation, mandatory administrator TOTP MFA, Organization-configurable member MFA, bounded Human-controlled recovery and reauthentication, authentication throttling, security-event evidence, tenant isolation and authorization-before-lookup, browser credential and CSRF security, bootstrap lifecycle, and bounded PATCH-058 security persistence are accepted.
- Reproducible release qualification, immutable artifact identity, Human-governed vulnerability exceptions, SBOM, provenance/attestation, cryptographic signing/trust, release dossier and independent security qualification contracts are accepted.
- Existing canonical identity, Organization, membership, Customer, Contact and engineering authorities remain controlling. Human authority remains controlling for recovery, security administration, vulnerability exceptions, signing authorization, release approval and PATCH acceptance; AI remains advisory and non-authoritative.
- PATCH-042 release foundations shall be extended/reconciled rather than replaced with competing release authority.
- PATCH-059 entitlement/licensing authority and PATCH-060 deployment qualification/Commercial V1 certification remain explicitly separate.
- This acceptance authorizes progression to IDS-058 preparation and independent review only.
- It does not authorize an Implementation Plan, implementation, migrations, production-code changes, database mutation, deployment, PATCH-059 or PATCH-060.

EDS-058: HUMAN ACCEPTED / COMPLETE
