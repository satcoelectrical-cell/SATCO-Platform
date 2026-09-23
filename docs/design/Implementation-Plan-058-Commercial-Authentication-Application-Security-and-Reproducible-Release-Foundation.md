# PATCH-058 — Implementation Plan
## Commercial Authentication, Application Security & Reproducible Release Foundation

## 1. Status and authority

This document is the candidate Implementation Plan for PATCH-058.

It is subordinate to the Human-accepted PATCH-058 Discovery, Architecture-058, ADR-031, EDS-058 and IDS-058.

This plan does not alter accepted product, engineering, security, tenant-ownership or Human-authority semantics.

Implementation is not authorized by creation of this candidate. Independent Implementation Plan review and explicit Human Implementation Plan acceptance are required before any implementation batch begins.

No production/customer database access, deployment, PATCH-059 work or PATCH-060 qualification is authorized.

## 2. Readiness and repository isolation

Implementation baseline:

- branch: `patch-058`;
- accepted IDS checkpoint: `e5e0b2b5a7fbc4d7f69e0aa84064027cab122270`;
- accepted sole Alembic head: `e05600000008`;
- PATCH-058 worktree shall remain isolated from the protected original worktree;
- unrelated work shall not be staged, rewritten, reset, cleaned or incorporated.

Before every implementation checkpoint:

1. verify branch and HEAD lineage;
2. inspect worktree and staging state;
3. verify sole Alembic head;
4. preserve unrelated work;
5. verify no production/customer database target;
6. stop on any accepted-governance contradiction.

## 3. Frozen implementation bindings

PATCH-058 implementation shall use the following frozen bindings unless a STOP condition requires return to governance.

### 3.1 Access token

- access credential remains a signed JWT;
- algorithm: `HS256`;
- access-token lifetime: 15 minutes;
- required claims: `sub`, `type`, `iat`, `exp`, `jti`, `iss`, `aud`, `av`, and server-session binding identifier;
- `type` shall identify an access token explicitly;
- issuer: `satco-platform`;
- audience: `satco-web`;
- missing or malformed security-version/session claims fail closed;
- current `payload.get("av", 1)` compatibility fallback shall not remain in steady-state PATCH-058 authentication;
- browser access token shall exist in memory only.

The existing `SECRET_KEY`/secret-file production boundary is retained and strengthened by configuration validation. No signing secret is committed to the repository.

### 3.2 Refresh credential

Refresh credentials shall no longer be JWT bearer credentials.

The refresh credential shall contain:

- a public random selector of at least 128 bits;
- a cryptographically random secret of at least 256 bits.

Only the raw browser credential may contain the secret.

The server shall persist a keyed `HMAC-SHA-256` verifier of the secret using a dedicated refresh-verifier key supplied through the production secret boundary.

Raw refresh secrets shall never be persisted or logged.

Refresh lifetime remains seven days initially, subject to server-side expiry, rotation, revocation, security-version invalidation and family reuse detection.

### 3.3 TOTP

PATCH-058 shall add an RFC 6238 compatible TOTP dependency.

Frozen parameters:

- SHA-1 for standard authenticator interoperability;
- 6 digits;
- 30-second period;
- verification window: current step plus one adjacent step in either direction;
- last successfully accepted counter shall be persisted and a counter shall not be accepted twice;
- enrollment secret entropy shall be at least 160 bits.

The selected Python implementation dependency shall be `pyotp`.

### 3.4 TOTP secret encryption

TOTP secrets shall be protected at rest using authenticated encryption.

Implementation binding:

- library: `cryptography`;
- primitive: AES-256-GCM;
- each encrypted secret uses a unique random nonce;
- persisted representation records ciphertext and key version/identifier;
- production key material comes from a dedicated file/secret configuration boundary and never from the database or repository;
- decryption failure or unavailable active key fails closed.

Key rotation shall support decrypting an accepted bounded set of previous key versions while new writes use the active version.

### 3.5 Recovery codes

Administrator/user recovery-code generation shall create ten single-use codes.

Each code shall contain at least 128 bits of cryptographic randomness.

Only non-reversible keyed `HMAC-SHA-256` verifiers shall be persisted.

A newly generated recovery-code set invalidates all unused codes in the previous set.

Consumption is atomic and single-use.

### 3.6 Browser refresh cookie

The refresh credential shall be transported in a cookie with:

- name: `satco_refresh`;
- `HttpOnly`;
- `Secure` in production;
- `SameSite=Lax`;
- path restricted to the authentication refresh/logout surface;
- no broad parent-domain configuration by default;
- Max-Age/expiry consistent with the server refresh-session expiry.

The raw refresh credential shall not be returned in normal JSON response bodies after PATCH-058 cutover.

### 3.7 CSRF

State-changing cookie-authenticated authentication operations shall require both:

1. allowed-origin validation; and
2. a double-submit anti-CSRF value.

The non-HttpOnly CSRF cookie shall be named `satco_csrf`.

The request header shall be `X-CSRF-Token`.

The value shall be generated with cryptographically secure randomness, compared in constant time and rotated with the refresh-session lifecycle.

Allowed origins remain server configuration controlled through the existing SATCO allowed-origin boundary.

### 3.8 Security-version strategy

`User.auth_version` remains the principal-wide monotonic security version.

It shall increment for principal-wide security changes including password reset/change/recovery, security-relevant MFA reset and account-security invalidation.

Refresh sessions shall bind the principal security version present at authentication/rotation.

Organization membership, membership role, membership enabled state, Organization active state and Organization MFA policy shall be revalidated from current canonical server state for Organization-authorized continuation.

PATCH-058 shall not create a second canonical identity or Organization authority.

A separate membership security-version column shall not be introduced unless implementation proves that the accepted IDS invariant cannot be satisfied without it; that condition requires STOP and governance review before expansion.

## 4. Persistence and Alembic migration

PATCH-058 shall introduce one forward migration lineage from verified sole head `e05600000008`.

The migration shall remain non-destructive and reconcilable.

Planned bounded persistence includes:

1. refresh-session/family state;
2. MFA authenticator state;
3. recovery-code verifiers;
4. Organization member-MFA policy;
5. dedicated security events;
6. authentication-throttle state where required.

Exact SQLAlchemy definitions and migration constraints shall be implemented from the accepted IDS physical model and verified before migration acceptance.

Required integrity constraints include:

- unique refresh selector;
- at most one successor for a consumed refresh session;
- indexed user/family/session lookup;
- indexed expiry/revocation cleanup paths;
- unique recovery-code verifier within its generation boundary;
- replay-protection state for TOTP;
- Organization MFA policy constrained to accepted policy values;
- bounded/indexed throttle keys and expiry;
- security-event indexes for actor, Organization, event type and time where applicable.

No migration may modify accepted engineering-domain ownership.

## 5. Authentication throttling

Throttle state shall be PostgreSQL-backed for PATCH-058.

Credential identity shall be normalized and converted to a non-reversible keyed identifier before persistence.

Network context shall be derived only from the directly trusted peer or explicitly configured trusted proxy chain.

Initial configuration:

- five failed authentication attempts in a five-minute window trigger delay;
- repeated failure increases bounded backoff;
- maximum backoff is fifteen minutes;
- successful authentication clears applicable credential failure state without exposing whether an account existed;
- stale throttle rows are eligible for bounded cleanup.

Thresholds shall be configuration controlled, validated and security tested.

External responses remain generic and shall not reveal account existence, MFA enrollment, recovery eligibility or throttle-key composition.

## 6. Security-event implementation

PATCH-058 shall introduce a dedicated security-event persistence model rather than overloading engineering Audit as the sole security record.

Minimum event taxonomy shall cover:

- login success/failure;
- throttle threshold/backoff;
- refresh rotation;
- refresh reuse detection;
- current/all/admin session revocation;
- MFA enrollment/verification/reset;
- recovery-code generation/use;
- account/MFA recovery;
- password/security-version invalidation;
- Organization MFA-policy change;
- role/membership/account security administration;
- bootstrap security events;
- vulnerability exception and release-security approval references where application attribution is appropriate.

Security events shall contain bounded attributable metadata only.

Passwords, raw tokens, refresh secrets, TOTP secrets, recovery codes, CSRF values and encryption keys shall never be recorded.

Default retention shall be configuration controlled with an initial target of 365 days, with bounded cleanup and no silent deletion of evidence required by an active release/security investigation.

Organization-visible security-event queries shall be Organization-scoped and authorization-before-lookup.

## 7. Organization MFA policy

The existing Organization remains canonical for Organization-level security policy.

PATCH-058 shall add an explicit member-MFA policy representation with accepted values equivalent to:

- optional;
- required.

Platform administrators remain subject to mandatory MFA regardless of Organization policy.

An Organization policy may strengthen engineer/member MFA requirements but may not weaken mandatory administrator MFA.

Policy changes are Human administrative actions, security-event attributable and immediately affect subsequent authorization/refresh qualification according to current canonical state.

## 8. Account, MFA and recovery lifecycle

Administrator MFA enrollment is mandatory before normal privileged continuation.

Engineer/member MFA follows current Organization policy.

Enrollment, verification, recovery, reset and disable flows shall preserve the IDS state machines and Human-control boundary.

Account/MFA recovery shall use purpose-bound, expiring, one-time server records or credentials and generic external responses.

Successful security recovery shall:

- update required credential/factor state atomically;
- increment applicable principal security version;
- revoke applicable existing refresh sessions;
- prevent reuse of consumed recovery material;
- create attributable security evidence.

Last-administrator protections remain mandatory.

AI shall not enroll, verify, reset, recover or bypass MFA and shall not exercise Human security authority.

## 9. Contact, Customer and search tenant-isolation reconciliation

PATCH-058 shall reconcile the existing Contact/Customer/search path without creating a duplicate Contact Organization owner.

Canonical authorization path:

`Contact -> Customer -> Organization`

The implementation change surface includes the existing Contact repository/service/router path and the centralized search repository/service path.

Required behavior:

- Contact list/detail/create/update/delete operations derive Organization authority through the canonical Customer relationship;
- Customer and Contact search functions receive explicit Organization scope before database retrieval;
- `search_all` shall propagate Organization scope into both Customer and Contact branches;
- result rows, totals, pagination metadata, ordering behavior, filters, empty states and errors shall not disclose cross-Organization existence;
- authorization occurs before protected-object disclosure;
- guessed identifiers and cross-Organization identifiers produce non-inferential protected outcomes;
- existing Project/workspace Organization protections remain unchanged.

No migration is authorized solely to duplicate `organization_id` onto Contact.

## 10. Authentication API surface

PATCH-058 shall reconcile the current authentication router into a server-session/MFA-aware API surface.

The accepted implementation surface shall provide operations equivalent to:

- password login and initial assurance evaluation;
- MFA challenge completion;
- refresh rotation;
- current-session logout;
- all-session logout/revocation;
- current-user session listing;
- administrator session revocation;
- TOTP enrollment start;
- TOTP enrollment verification;
- recovery-code regeneration;
- account/MFA recovery initiation and completion;
- recent-authentication/step-up challenge where required.

Final route names shall remain under the existing versioned authentication API namespace and shall not create a parallel authentication authority.

DTOs shall never return raw persisted refresh verifiers, TOTP encryption material, recovery-code verifiers or security-event secrets.

Login shall not return the refresh credential in its steady-state JSON response.

Compatibility with the existing access-token response shall be bounded to the frontend cutover and removed from obsolete refresh-token DTO fields within PATCH-058.

## 11. Sensitive-operation reauthentication

Sensitive security administration requires recent Human authentication.

The server shall record trusted authentication time/assurance in server-verifiable session state.

Initial recent-authentication window: ten minutes.

Operations requiring recent authentication include at minimum:

- password/security-credential change;
- MFA reset/removal;
- recovery-code regeneration;
- all-session revocation;
- administrator revocation of another user's sessions;
- Organization MFA-policy change;
- high-impact account/role/membership security administration where the existing authority permits it.

Expired recent-authentication state requires a fresh password/MFA step appropriate to the account assurance level.

Frontend state alone shall never satisfy reauthentication.

## 12. Frontend authentication cutover

Primary implementation surfaces include:

- `frontend/src/api/client.ts`;
- `frontend/src/auth/AuthProvider.tsx`;
- `frontend/src/pages/LoginPage.tsx`;
- `frontend/src/pages/OnboardingPages.tsx`;
- associated route/application composition and tests.

Required cutover:

- remove access-token persistence from `sessionStorage`;
- do not move authentication credentials to `localStorage` or IndexedDB;
- hold the access token in runtime memory only;
- use the HttpOnly refresh cookie for bounded session restoration/rotation;
- send credentials only on the bounded API operations requiring the refresh cookie;
- attach the in-memory access bearer to protected API requests;
- on access expiry, perform bounded refresh coordination and retry only where safe;
- on refresh failure/revocation/reuse/security invalidation, clear local authentication state and require appropriate authentication;
- logout shall invoke server revocation before local state is discarded where communication is possible;
- server authority remains controlling if local logout communication fails.

Existing `sessionStorage` authentication tests shall be replaced with tests proving no durable access-token persistence.

Presentation-only `localStorage` usage such as dashboard layout is outside the authentication credential prohibition and shall remain non-authoritative.

## 13. Cross-tab and stale-session behavior

Cross-tab coordination may communicate only non-secret state such as:

- session-invalidated;
- logout;
- authentication-required;
- refresh-in-progress coordination where no credential is exposed.

No access token, refresh credential, TOTP secret, recovery code or CSRF secret shall be propagated through browser storage or cross-tab messaging.

A tab receiving invalidation shall clear in-memory authority and shall not reconstruct authority from stale UI state.

Concurrent refresh attempts shall be coordinated client-side where practical, but server-side one-time rotation remains the security authority.

## 14. Activation, reset and URL-secret handling

Existing onboarding/activation/reset flows shall be reconciled so that purpose-bound secrets are removed from browser-visible URLs as early as practical.

Required controls:

- no activation/reset/recovery credential is persisted in localStorage/sessionStorage;
- secret-bearing query parameters are consumed once and removed from the visible URL using history replacement before normal navigation;
- secret-bearing values are not included in analytics, application logs or referrer-bearing navigation;
- purpose, expiry, single-use and consumed-state checks remain server authoritative;
- completion invalidates the credential atomically;
- external error behavior remains non-enumerating.

Existing first-login continuation to the Commercial V1 experience shall be preserved.

## 15. Bootstrap enforcement

Existing configuration boundaries:

- `SATCO_BOOTSTRAP_ENABLED`;
- `SATCO_BOOTSTRAP_WINDOW_END`;
- platform bootstrap secret/file boundary;

shall be enforced by one server-authoritative bootstrap service path.

Authorization requires all of:

1. explicit bootstrap enabled state;
2. valid bounded server time window;
3. valid bootstrap secret;
4. bootstrap eligibility/current system state;
5. accepted last-admin and onboarding invariants.

Successful bootstrap completion shall create durable server-side completion state sufficient to prevent reuse after the intended first-customer bootstrap has completed.

Configuration alone shall not silently re-open a completed bootstrap.

Human-authorized re-enable requires an explicit bounded administrative/operational procedure and attributable security evidence.

The current router behavior that checks only bootstrap-key material shall not remain the complete authorization decision.

## 16. Configuration additions

PATCH-058 may add bounded security configuration for:

- access issuer/audience and lifetime;
- refresh verifier key file;
- refresh lifetime;
- TOTP encryption active key and accepted previous-key files/identifiers;
- trusted proxy/network-context policy;
- authentication throttle thresholds;
- security-event retention;
- CSRF/cookie settings;
- recent-authentication window;
- release/security tooling configuration where repository-controlled policy is appropriate.

Production security configuration shall fail closed for missing, placeholder, malformed or unsafe mandatory values.

Secrets shall use the existing production secret-file pattern where applicable.

No production secret value shall be committed.

## 17. Compatibility and cutover rules

PATCH-058 is a bounded security cutover, not a permanent dual-stack authentication system.

During implementation:

- existing password hashes remain valid;
- existing User identity and `auth_version` remain canonical;
- existing stateless refresh JWT issuance is replaced by server-backed refresh sessions;
- existing browser `sessionStorage` access-token persistence is removed;
- old refresh JWTs shall not silently become valid server sessions;
- missing new security/session claims fail closed after cutover;
- legacy API fields required only for the old refresh-token model are removed or bounded through an explicitly tested transition;
- Organization membership and role authority continue to come from current canonical state;
- accepted onboarding behavior remains available after security qualification.

No indefinite compatibility fallback may weaken the accepted PATCH-058 security model.

## 18. Authorization and anti-inference qualification

Implementation qualification shall include negative evidence for:

- cross-Organization Contact list/detail/mutation;
- cross-Organization Customer/Contact search;
- guessed Contact/Customer/session identifiers;
- disabled account;
- disabled/removed membership;
- stale role;
- tightened Organization MFA policy;
- missing/stale security version;
- expired/revoked refresh session;
- refresh reuse;
- MFA replay;
- recovery-code replay;
- recovery enumeration;
- throttle enumeration;
- CSRF absence/mismatch;
- disallowed Origin;
- stale browser session;
- bootstrap outside window/after completion;
- unauthorized session revocation;
- last-admin security operations.

Protected failures shall not disclose whether inaccessible protected resources exist.

## 19. Backend implementation surface

Expected backend change surface is bounded primarily to:

- authentication/security configuration and helpers;
- authentication dependencies;
- User/Organization security integration;
- new bounded security/session/MFA/throttle/security-event models;
- corresponding schemas/repositories/services;
- authentication router;
- onboarding/bootstrap integration;
- Contact/Customer/search repositories and services;
- security/audit integration;
- PATCH-058 migration;
- focused and regression tests.

Existing engineering-domain services shall not be semantically rewritten merely to accommodate PATCH-058.

Any required change outside this bounded surface that alters accepted canonical engineering behavior triggers STOP and governance review.

## 20. Frontend implementation surface

Expected frontend change surface is bounded primarily to:

- API authentication client;
- AuthProvider/session lifecycle;
- login/MFA challenge experience;
- TOTP enrollment;
- recovery-code presentation/regeneration;
- account/MFA recovery;
- stale/revoked-session handling;
- onboarding/activation/reset secret handling;
- Organization MFA-policy administration where existing Human administration authority permits it;
- session listing/revocation administration;
- focused authentication/security tests.

All new security UI shall preserve keyboard accessibility, responsive behavior and existing RTL/LTR support.

Security UI shall explain state and required Human action without granting AI authority.

## 21. CI provider and workflow topology

PATCH-058 shall introduce repository-controlled GitHub Actions workflows under `.github/workflows/`.

The CI design shall separate ordinary qualification from privileged release/signing activity.

Required workflow responsibilities:

1. backend deterministic test and static qualification;
2. frontend typecheck, test and production build;
3. Alembic graph/head validation;
4. security-negative qualification;
5. dependency scanning;
6. SAST;
7. secret scanning;
8. container scanning;
9. SBOM generation;
10. provenance/attestation generation;
11. artifact digest verification;
12. vulnerability-gate evaluation;
13. controlled signing;
14. release-dossier assembly and verification.

Pull-request and ordinary branch qualification shall not receive release-signing authority.

Privileged release/signing jobs shall require protected Human authorization through a GitHub protected Environment or equivalent repository-controlled Human approval boundary.

CI is evidence-producing automation and is not Human release authority.

## 22. Deterministic quality gates

The release-candidate workflow shall fail closed unless all mandatory gates complete successfully.

Backend qualification shall use the repository's accepted Python environment and pytest suite.

Frontend qualification shall use the committed package lock and at minimum:

- `npm run typecheck`;
- `npm run test:run`;
- `npm run build`.

Migration qualification shall verify:

- exactly one Alembic head;
- expected lineage from the accepted PATCH-058 migration;
- clean upgrade on a disposable PostgreSQL database;
- bounded migration/security regression evidence.

No production/customer database is permitted as a CI or implementation qualification target.

Build evidence shall bind to the exact full Git commit and dependency-lock digests.

## 23. Security scanning toolchain

PATCH-058 shall bind the initial release-security toolchain as follows:

- Python dependency vulnerabilities: `pip-audit`;
- JavaScript dependency vulnerabilities: `npm audit`;
- SAST: `Semgrep`;
- repository secret scanning: `gitleaks`;
- container/image vulnerability scanning: `Trivy`.

Scanner versions shall be pinned or otherwise deterministically controlled in the release workflow.

Unavailable mandatory scan evidence is a failed gate, not a PASS.

Scanner findings are evidence only. Scanners and AI cannot approve vulnerability exceptions.

Critical findings block the release candidate.

High findings require the accepted bounded Human exception process where an exception is permitted.

## 24. Vulnerability exception binding

The existing `ops/high-vulnerability-exceptions.v1.schema.json` remains the baseline Human-governed High-severity exception contract.

PATCH-058 shall reconcile validation so an active exception is accepted only when it binds to:

- exact finding identifier;
- scanner/source;
- exact artifact digest;
- rationale;
- compensating controls;
- bounded scope;
- attributable Human approver;
- approval time;
- expiry;
- retest condition/reference/result;
- active status.

An exception for one artifact digest shall not transfer to a rebuilt or different artifact.

Expired, revoked, failed-retest, malformed or mismatched exceptions fail closed.

No Critical vulnerability exception is introduced by PATCH-058.

## 25. SBOM

PATCH-058 shall generate machine-readable CycloneDX JSON SBOM evidence.

Tool: `Syft`.

At minimum, SBOM generation shall cover the release backend container and the frontend/release dependency surface represented by the candidate.

The SBOM shall be bound to:

- exact release candidate;
- exact artifact digest;
- source revision;
- generation tool/version;
- generation timestamp.

The SBOM digest/reference shall be incorporated into release provenance and the release dossier.

A missing or digest-mismatched mandatory SBOM fails release qualification.

## 26. Provenance and attestation

PATCH-058 shall produce an in-toto/SLSA-compatible provenance statement for release artifacts.

The provenance shall bind at minimum:

- full source revision;
- repository identity;
- build workflow identity;
- dependency/lock inputs;
- migration artifact identity;
- backend/frontend artifact digests;
- SBOM digest/reference;
- mandatory scan-evidence references;
- build/qualification result references.

The initial implementation shall use `cosign attest` for cryptographically bound attestation of the provenance predicate.

The predicate shall be machine-readable and retained with the release evidence.

Provenance mismatch or unverifiable attestation fails closed.

## 27. Artifact signing and trust

PATCH-058 shall use `cosign` for release artifact signature/verification.

Signing execution may be automated only after the protected Human authorization gate has been satisfied.

The initial trust model shall use GitHub Actions OIDC/keyless signing for the controlled release workflow, with verification constrained to the accepted SATCO repository/workflow identity and protected release environment.

No long-lived signing private key shall be stored in:

- source control;
- application database;
- release artifact;
- ordinary CI variables accessible to unprivileged jobs.

Verification shall bind the signature to the exact SHA-256 artifact digest and accepted signer/workflow identity.

A signature on a different digest, repository, workflow identity or unauthorized environment is invalid.

Human authorization to enter the privileged signing/release stage remains distinct from cryptographic signing execution.

AI and ordinary CI jobs have no independent signing authorization.

## 28. Container and artifact identity

Existing production Dockerfiles and Compose/release foundations from PATCH-042 shall be reused and reconciled rather than replaced by a competing deployment architecture.

Release identity shall use immutable SHA-256 digests.

Mutable image tags, filenames or branch names are not sufficient release identity.

The release evidence shall bind at minimum:

- backend image digest;
- frontend artifact/asset digest;
- migration artifact digest;
- dependency lock digest;
- frontend package-lock digest;
- SBOM digest/reference;
- provenance/attestation;
- scan evidence;
- signature verification evidence.

PATCH-058 does not perform representative production deployment qualification; that remains PATCH-060.

## 29. Release-manifest reconciliation

`ops/release-manifest.v1.schema.json` remains the existing release-manifest authority and shall be extended/reconciled rather than replaced.

PATCH-058 reconciliation shall preserve its existing bindings including:

- release ID;
- Git commit;
- backend image digest;
- frontend asset digest;
- expected Alembic head;
- configuration schema version;
- migration artifact digest;
- dependency lock digest;
- package-lock digest;
- SBOM reference;
- scan-evidence reference;
- signing-approver evidence reference;
- creation time.

The reconciled contract shall additionally bind the PATCH-058 provenance/attestation and cryptographic signature-verification evidence required by the accepted architecture/EDS/IDS.

Schema and example manifest shall evolve together.

Manifest validation is mandatory before a release candidate may proceed to Human approval.

## 30. Release dossier

PATCH-058 shall introduce a versioned machine-readable release-dossier schema under `ops/`.

The dossier shall index, directly or by immutable digest-bound reference:

- clean source revision evidence;
- dependency/build-input evidence;
- backend/frontend/migration artifact digests;
- backend/frontend qualification;
- migration graph and disposable-DB qualification;
- security-negative results;
- dependency/SAST/secret/container scan evidence;
- vulnerability findings and applicable Human exceptions;
- SBOM;
- provenance/attestation;
- signature and verification evidence;
- Human signing-authorization evidence;
- Human release-approval evidence.

Release-dossier evidence shall be stored as release artifacts/evidence, not application-domain database truth.

A dossier with missing mandatory evidence, mismatched digest, unresolved blocking finding or invalid approval evidence fails closed.

The PATCH-058 dossier establishes release-candidate security evidence. It is not PATCH-060 Commercial V1 deployment certification.

## 31. Human authorization and release approval

Three concepts remain distinct:

1. automated qualification evidence;
2. Human authorization for privileged signing execution;
3. Human release approval.

GitHub protected Environment approval or an equivalently attributable protected mechanism shall gate privileged signing execution.

Final release approval shall be separately attributable to the accepted Human release authority and represented in the release dossier.

Scanner PASS, CI success, cryptographic signature or AI analysis shall not substitute for Human approval.

Vulnerability exceptions likewise require attributable Human approval and cannot be created or approved autonomously by AI/CI.

## 32. Release evidence safety

Release evidence shall not contain:

- application passwords;
- raw access/refresh credentials;
- TOTP secrets;
- recovery codes;
- CSRF values;
- signing private keys;
- production application secrets;
- unrestricted customer data.

Logs and evidence shall be minimized while retaining sufficient identity, digest, timestamp, workflow and Human-approval attribution for verification.

Release evidence references shall be immutable or digest-bound wherever the underlying storage permits.

## 33. Supply-chain negative qualification

At minimum, qualification shall prove failure for:

- dirty/unbound source identity;
- changed dependency lock;
- changed frontend package lock;
- multiple/unexpected Alembic heads;
- missing mandatory scan;
- Critical vulnerability;
- High vulnerability without valid Human exception;
- exception bound to another artifact digest;
- expired/revoked/failed-retest exception;
- missing/mismatched SBOM;
- provenance bound to another revision/artifact;
- unsigned mandatory artifact;
- invalid signer/workflow identity;
- signature bound to another digest;
- signing job without protected Human authorization;
- missing Human release approval;
- release dossier with missing or inconsistent mandatory evidence.

No test may convert unavailable mandatory evidence into a synthetic PASS.

## 34. Test and disposable-database harness

PATCH-058 qualification shall use the repository's existing test frameworks and a PATCH-specific disposable PostgreSQL instance for database-backed qualification.

The harness shall:

- never target production/customer databases;
- never use host port 5432;
- use an isolated database/container identity;
- verify the intended connection target before migration/test execution;
- start from the accepted migration lineage;
- apply the PATCH-058 migration through Alembic;
- run focused security/database vectors;
- run bounded regression;
- dispose of PATCH-specific database state after qualification when safe.

Mandatory qualification includes:

- backend focused authentication/MFA/session/security tests;
- tenant-isolation and anti-inference tests;
- concurrency tests for refresh rotation/reuse;
- recovery-code/TOTP replay tests;
- throttle and recovery anti-enumeration tests;
- bootstrap lifecycle tests;
- frontend auth/session/MFA/recovery tests;
- frontend typecheck;
- frontend production build;
- migration graph/head qualification;
- security-negative vectors;
- supply-chain negative vectors;
- full or appropriately bounded backend/frontend regression before closure.

Exact commands shall use repository-native pytest/npm/Alembic tooling and shall be recorded in checkpoint evidence.

## 35. Checkpoint A — persistence and authentication foundation

Checkpoint A implements only the bounded security persistence and core authentication/session foundation.

Expected work includes:

- PATCH-058 forward Alembic migration;
- refresh family/session persistence;
- MFA authenticator/recovery-code persistence;
- Organization MFA-policy persistence;
- throttle/security-event persistence;
- required security configuration;
- access-token claim hardening;
- refresh credential verifier;
- atomic refresh rotation;
- expiry/revocation/reuse detection;
- security-version integration.

Checkpoint A acceptance requires focused migration, transaction, concurrency, session, invalidation and secret-handling evidence.

No frontend cutover or release-pipeline acceptance is implied by Checkpoint A.

Human checkpoint acceptance is required before Checkpoint B.

## 36. Checkpoint B — MFA, recovery and security administration

Checkpoint B implements:

- mandatory administrator TOTP;
- Organization-configurable engineer/member MFA;
- TOTP enrollment/verification/replay prevention;
- recovery-code generation/consumption/regeneration;
- account/MFA recovery;
- recent-authentication/step-up;
- current/all/admin session revocation;
- session visibility;
- security-event attribution for these flows;
- last-administrator protections.

Checkpoint B acceptance requires focused positive and negative assurance/recovery/reauthentication tests and proof that AI/CI cannot exercise Human security authority.

Human checkpoint acceptance is required before Checkpoint C.

## 37. Checkpoint C — tenant isolation, bootstrap and browser-auth cutover

Checkpoint C implements:

- Contact authorization through Customer/Organization;
- Customer/Contact search Organization scoping;
- authorization-before-lookup reconciliation;
- bootstrap enable/window/completion enforcement;
- refresh-cookie transport;
- CSRF/origin protection;
- frontend memory-only access token;
- bounded refresh coordination;
- logout/revocation UX;
- stale-session/cross-tab behavior;
- activation/reset URL-secret handling;
- MFA/recovery/security administration UI required by accepted scope.

Checkpoint C acceptance requires anti-inference, CSRF, browser-storage, stale-session, bootstrap and accessibility/RTL/responsive evidence.

Human checkpoint acceptance is required before Checkpoint D.

## 38. Checkpoint D — CI and software-supply-chain security

Checkpoint D implements:

- GitHub Actions qualification workflows;
- deterministic quality/migration gates;
- `pip-audit`;
- `npm audit`;
- `Semgrep`;
- `gitleaks`;
- `Trivy`;
- Syft CycloneDX JSON SBOM generation;
- provenance generation;
- cosign attestation/signature verification topology;
- vulnerability-gate validation;
- Human-protected signing authorization.

Checkpoint D acceptance requires both successful-path evidence and the supply-chain negative vectors defined by this plan.

Human checkpoint acceptance is required before Checkpoint E.

## 39. Checkpoint E — release dossier and integrated security qualification

Checkpoint E completes:

- release-manifest reconciliation;
- release-dossier schema and validation;
- Human exception/signing-authorization/release-approval evidence binding;
- integrated security regression;
- independent threat/security review;
- penetration-oriented negative qualification;
- final artifact/SBOM/provenance/signature/dossier consistency qualification.

Checkpoint E does not perform PATCH-060 representative production deployment or Commercial V1 release certification.

Human checkpoint acceptance is required before PATCH-058 final closure review.

## 40. Checkpoint isolation rules

Each checkpoint shall:

1. begin from the accepted prior checkpoint;
2. inspect branch, HEAD, worktree and staging;
3. preserve unrelated work;
4. modify only the accepted checkpoint surface;
5. run focused qualification before staging;
6. undergo independent checkpoint review;
7. resolve all Critical/Major findings before Human acceptance;
8. receive explicit Human acceptance before progression;
9. be committed and remote-backed as an independently verifiable checkpoint where governance requires.

A later checkpoint shall not silently repair an unaccepted earlier checkpoint.

## 41. Rollback and recovery rules

Before PATCH-058 closure, rollback means repository/application rollback within the accepted development/qualification environment, not production rollback qualification.

Migration changes shall be forward/reconcilable from `e05600000008`.

No destructive rollback against production/customer data is authorized.

Security schema changes shall avoid irreversible destruction of accepted canonical identity/Organization/engineering data.

If a checkpoint cannot be safely reconciled without weakening an accepted invariant, implementation stops and returns to governance.

Operational upgrade/rollback qualification against a representative deployment remains PATCH-060.

## 42. Stop conditions

STOP and return to governance if:

- accepted Discovery/Architecture/ADR/EDS/IDS semantics would need modification;
- a Critical or Major independent-review finding remains unresolved;
- deterministic tenant isolation cannot be preserved;
- refresh rotation/reuse cannot be concurrency safe;
- administrator MFA would require weakening accepted Human authority;
- TOTP encryption/key custody cannot satisfy the accepted boundary;
- recovery/throttle behavior materially enables enumeration or bypass;
- browser credential/CSRF handling cannot satisfy accepted production security;
- migration cannot remain forward/reconcilable from `e05600000008`;
- implementation produces multiple/unexpected Alembic heads;
- mandatory release evidence cannot bind to exact artifact digests;
- CI/AI would obtain independent signing/release/exception authority;
- mandatory scan/SBOM/provenance/signature evidence cannot be produced truthfully;
- production/customer DB access would be required;
- PATCH-059 entitlement/licensing scope would be required;
- PATCH-060 deployment/certification scope would be required;
- unrelated dirty work cannot be isolated.

No STOP condition may be converted into a documented exception merely to continue implementation.

## 43. Human checkpoint model

Human authority is required for:

- Implementation Plan acceptance;
- each implementation checkpoint acceptance;
- MFA/recovery/security administrative authority where applicable;
- vulnerability exceptions;
- privileged signing authorization;
- final release approval evidence;
- final PATCH-058 closure.

AI may assist with implementation, analysis, tests, evidence assembly and review preparation.

AI does not approve its own checkpoint, vulnerability exception, signing authority, release or PATCH closure.

## 44. Obligation traceability

The IDS-058 Implementation Plan obligations are bound as follows:

1. repository files/modules — Sections 19, 20 and checkpoint surfaces;
2. current auth/token/frontend storage — Sections 3, 10, 12 and 17;
3. access JWT claims/lifetime/configuration — Section 3.1;
4. refresh encoding/verifier — Section 3.2;
5. refresh tables/constraints/index direction — Sections 4 and 35;
6. security-version fields/invalidation — Section 3.8;
7. TOTP library/parameters/replay — Sections 3.3 and 36;
8. authenticated encryption/key source — Section 3.4;
9. recovery-code format/verifier — Section 3.5;
10. throttle storage/threshold/cleanup — Section 5;
11. security-event schema/taxonomy/retention — Section 6;
12. Organization MFA policy — Section 7;
13. Contact/Customer/search reconciliation — Section 9;
14. CSRF derivation/origins — Section 3.7;
15. cookie identity/attributes — Section 3.6;
16. bootstrap completion/enforcement — Section 15;
17. frontend state/routes/storage cutover — Sections 12-14 and 20;
18. API/DTO compatibility — Sections 10 and 17;
19. Alembic migration — Sections 4, 34 and 35;
20. CI provider/workflows — Section 21;
21. scanners — Section 23;
22. SBOM format/tool — Section 25;
23. provenance/attestation — Section 26;
24. signing/trust/key custody — Section 27;
25. release-manifest reconciliation — Section 29;
26. release-dossier schema/storage — Section 30;
27. Human exception/signing/release evidence — Sections 24 and 31;
28. test commands/DB harness/negative vectors — Sections 18, 22, 33 and 34;
29. implementation batches/rollback/STOP — Sections 35-42.

Any independent-review finding that an obligation remains materially unfrozen shall be resolved before Human Implementation Plan acceptance.

## 45. Regression and closure qualification

Before PATCH-058 final closure review, qualification shall demonstrate:

- accepted authentication and onboarding journeys remain functional;
- administrator MFA is enforced;
- Organization member-MFA policy behaves as accepted;
- refresh rotation/reuse/revocation is concurrency safe;
- password/MFA/account/membership/role security changes invalidate stale authority as designed;
- Contact/Customer/search tenant isolation passes;
- browser durable credential storage is removed;
- CSRF/origin controls pass;
- bootstrap lifecycle passes;
- security-event evidence is bounded and attributable;
- backend and frontend regressions pass;
- migration graph is singular and accepted;
- mandatory scans complete;
- blocking vulnerabilities are absent or governed exactly as accepted;
- SBOM/provenance/signatures verify against exact artifacts;
- release dossier is internally consistent;
- Human exception/signing/release authority remains preserved;
- AI remains advisory/non-authoritative;
- PATCH-059 and PATCH-060 remain unopened.

Independent final security review is required before PATCH-058 closure.

## 46. Delivery and closure sequence

The governed sequence is:

1. Independent Implementation Plan Review;
2. Human Implementation Plan Acceptance;
3. Checkpoint A implementation, qualification, independent review and Human acceptance;
4. Checkpoint B implementation, qualification, independent review and Human acceptance;
5. Checkpoint C implementation, qualification, independent review and Human acceptance;
6. Checkpoint D implementation, qualification, independent review and Human acceptance;
7. Checkpoint E implementation, qualification, independent review and Human acceptance;
8. integrated PATCH-058 security qualification;
9. independent final PATCH-058 review;
10. Human PATCH-058 closure decision;
11. closure commit/tag/remote verification according to governance.

PATCH-059 shall not begin before PATCH-058 is formally DONE/CLOSED.

## 47. Implementation Plan self-review

This candidate has been checked against all 29 IDS-058 Implementation Plan obligations.

It freezes:

- authentication/session/MFA/recovery implementation bindings;
- bounded persistence/migration direction;
- tenant-isolation remediation;
- browser credential/CSRF cutover;
- bootstrap enforcement;
- CI/scanner/SBOM/provenance/signing toolchain;
- release-manifest/dossier evidence;
- Human authority boundaries;
- implementation checkpoints;
- test/DB harness;
- rollback and STOP boundaries.

It does not authorize implementation by itself.

No PATCH-059 entitlement/licensing semantics or PATCH-060 deployment/certification work is introduced.

## 48. Governance disposition

Implementation Plan-058 candidate is COMPLETE / READY FOR INDEPENDENT IMPLEMENTATION PLAN REVIEW.

Human Implementation Plan acceptance is not implied.

No implementation batch, production-code change, migration creation/execution, database mutation, deployment, PATCH-059 or PATCH-060 work is authorized until the required independent review and explicit Human acceptance.

Implementation Plan-058: CANDIDATE / READY FOR INDEPENDENT IMPLEMENTATION PLAN REVIEW

## 49. Independent Implementation Plan Review

Independent Implementation Plan Review verdict:

**PASS / READY FOR HUMAN IMPLEMENTATION PLAN ACCEPTANCE**

Findings:

- Critical: 0
- Major: 0
- Minor: 0

The review verified that the Implementation Plan remains subordinate to the Human-accepted PATCH-058 Discovery, Architecture-058, ADR-031, EDS-058 and IDS-058.

The concrete Implementation Plan bindings for access-token lifetime, refresh credential/verifier, TOTP, authenticated encryption, recovery codes, throttling, security-event retention, browser cookie/CSRF behavior, recent-authentication window, CI provider, security scanners, SBOM, provenance and signing tooling are within decisions explicitly delegated by IDS-058 to the accepted Implementation Plan boundary.

The GitHub Actions OIDC/keyless cosign model is acceptable only under the already-defined Human-governed signer boundary: privileged signing execution shall remain gated by protected Human authorization, signer trust shall remain constrained to the accepted repository/workflow/environment identity, CI configuration alone shall not broaden signing authority, and Human release approval shall remain distinct from cryptographic signing and CI success.

Non-blocking Observation:

During implementation and qualification, the exact GitHub OIDC identity/trust policy shall be demonstrated to bind the accepted repository, controlled release workflow and protected Human-authorized environment. Ordinary CI or unprotected workflow execution shall not obtain equivalent signing authority.

No accepted Architecture/ADR/EDS/IDS semantic change is required.

No implementation, migration creation/execution, database mutation, deployment, PATCH-059 or PATCH-060 work is authorized by this independent review.

Implementation Plan-058 Independent Review: PASS / READY FOR HUMAN IMPLEMENTATION PLAN ACCEPTANCE

## 50. Human Implementation Plan Acceptance

- Human Implementation Plan Authority decision: **PASS / ACCEPTED / COMPLETE**.
- Acceptance date: **2026-09-23**.
- Accepted after Independent Implementation Plan Review returned **PASS / READY FOR HUMAN IMPLEMENTATION PLAN ACCEPTANCE** with Critical/Major/Minor = **0/0/0**.
- The non-blocking signing Observation remains an implementation qualification obligation: GitHub OIDC/keyless signing authority shall be constrained to the accepted repository, controlled release workflow and protected Human-authorized environment; ordinary CI shall not acquire equivalent signing authority.
- The frozen authentication, session, MFA, recovery, tenant-isolation, browser-security, CI, scanning, SBOM, provenance, signing, release-dossier, test-harness and checkpoint boundaries are accepted for PATCH-058 implementation.
- Human security, recovery, vulnerability-exception, signing-authorization, release-approval and PATCH-gate authority remains controlling.
- AI remains advisory and non-authoritative.
- This acceptance authorizes progression to **PATCH-058 Checkpoint A implementation preparation and execution under the accepted checkpoint controls only**.
- It does not authorize production/customer database access, deployment, PATCH-059 or PATCH-060 work.

Implementation Plan-058: HUMAN ACCEPTED / COMPLETE
