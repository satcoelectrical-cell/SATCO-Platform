# IDS-058 — Commercial Authentication, Application Security & Reproducible Release Foundation

## 1. Control and authority

Status: **Proposed / Candidate — awaiting independent IDS review and Human IDS acceptance.**

Date: 2026-09-23.

This IDS implements the physical design obligations of the Human-accepted EDS-058 and remains subordinate to the Human-accepted PATCH-058 Discovery, Architecture-058 and ADR-031.

It defines implementation design only.

It does not authorize an Implementation Plan, production-code implementation, migration creation/execution, database mutation, staging, commit, push, deployment, PATCH-059 or PATCH-060.

Human authority remains controlling for recovery, security administration, vulnerability exceptions, signing authorization, release approval and PATCH gates. AI remains advisory and non-authoritative.

## 2. Repository baseline and preserved authority

The accepted implementation baseline for IDS-058 is PATCH-058 commit:

`10b9137efdaa577a595d5ef791a2ba80a606753d`

The implementation shall reuse and extend existing repository authorities rather than create competing identity/domain ownership.

Preserved authorities include:

- existing User identity/password/account/role authority;
- Organization and UserOrganizationMembership tenant authority;
- Customer Organization ownership;
- Contact ownership derived through Customer;
- existing authenticated dependency/role/action-credential patterns;
- existing audit facilities where sufficient;
- PATCH-041 onboarding/account lifecycle;
- PATCH-042 release-manifest, digest, vulnerability-exception, configuration and operational foundations;
- existing engineering Evidence/Technical Report/standards/Memory/domain authorities.

The accepted Alembic head before PATCH-058 persistence work is `e05600000008`.

Any future PATCH-058 migration shall descend forward from the sole repository head verified at implementation-plan/preflight time. This IDS does not create or authorize that migration.

## 3. Physical security-state topology

PATCH-058 shall introduce only bounded security persistence required by EDS-058.

The physical design shall use these logical persistence groups:

1. refresh session/family state;
2. MFA authenticator state;
3. recovery-code verifier state;
4. Organization member-MFA policy;
5. security-event state only where existing Audit cannot safely satisfy the required taxonomy/visibility;
6. throttle state according to the storage decision in this IDS.

No PATCH-058 table becomes canonical identity, Organization, membership, Customer, Contact or engineering ownership.

Foreign-key relationships shall reference existing canonical owners rather than duplicate their mutable authority fields.

Security records shall use repository-consistent opaque identifiers and timestamps.

Raw refresh credentials, raw recovery codes and plaintext TOTP secrets shall never be persisted.

## 4. Security-version physical strategy

PATCH-058 shall use layered invalidation rather than a single global version for every security change.

The physical strategy is:

- `User.auth_version` remains the principal-wide authentication-security version;
- refresh sessions carry/bind the User auth-version observed at qualification;
- Organization membership authority is revalidated from current UserOrganizationMembership state for Organization-scoped protected operations;
- refresh qualification revalidates current membership/role/policy rather than treating stale token membership claims as canonical;
- access credentials carry only the bounded security/session references required for efficient rejection and shall not become canonical membership state.

Principal-wide security events shall increment/change `User.auth_version` and revoke applicable refresh sessions.

Principal-wide events include at minimum:

- password reset/change where security policy requires global invalidation;
- account recovery;
- administrator MFA reset/removal;
- account disable;
- explicit all-session/security revocation.

Organization membership disable/removal/role change shall be enforced from current membership state and shall not require global invalidation of unrelated Organization memberships unless the implementation cannot safely isolate the affected authority.

Organization MFA-policy tightening shall be enforced from current policy/assurance state and shall not be bypassable by an older session.

If implementation analysis proves current membership records cannot support deterministic stale-authority rejection without a membership security version, a bounded monotonic membership-security version may be added, but only through the accepted Implementation Plan/migration boundary. It shall not replace canonical membership ownership.

Missing mandatory auth/security-version claims shall fail closed after the controlled compatibility cutover.

## 5. Access-token physical contract

Access tokens shall remain signed short-lived bearer JWTs for PATCH-058.

IDS-058 freezes the following minimum claims:

- subject/User identifier;
- token type identifying access use;
- issued-at time;
- expiry time;
- unique token identifier;
- issuer;
- audience;
- User auth-version;
- refresh-session identifier or equivalent session-binding identifier.

Mutable Organization membership/role state in an access token, if retained for compatibility, shall not be accepted as canonical authorization without current server-side qualification where EDS-058 requires current authority.

Production validation shall require:

- accepted signature algorithm;
- expected issuer;
- expected audience;
- expiry;
- token type;
- mandatory security/session claims.

The steady-state validator shall not use silent defaults for missing mandatory claims.

The exact access-token lifetime shall be short and configuration-controlled. The accepted Implementation Plan shall freeze the initial value after regression/UX qualification; changing it shall not weaken the short-lived-token requirement.

Browser access tokens shall remain memory-only.

## 6. Refresh credential representation

A refresh credential shall contain:

- an opaque public session/credential selector sufficient to locate candidate server state; and
- a cryptographically random secret verifier input.

The raw secret shall be returned only to the authenticated client through the protected refresh-cookie transport.

Server persistence shall store a non-reversible cryptographic verifier of the secret, never the raw secret.

The verifier design shall use a repository-approved password/secret hashing primitive or a dedicated keyed/hash construction appropriate for high-entropy random secrets.

Verifier comparison shall use constant-time or library-safe verification semantics.

Refresh credentials shall not encode authoritative role/membership state.

A database leak of refresh-session rows alone shall not reveal immediately reusable raw refresh credentials.

## 7. Refresh family/session physical model

The persistence model shall distinguish refresh family lineage from individual rotating credentials/sessions either through:

- a dedicated family record plus child session/token records; or
- an equivalent normalized representation that preserves family identity, predecessor/successor lineage and family-wide revocation.

The physical state shall support at minimum:

- record identifier;
- family identifier;
- User identifier;
- non-reversible refresh verifier;
- predecessor identifier where applicable;
- successor identifier where applicable;
- creation time;
- absolute expiry time;
- consumed/rotated time;
- revoked time;
- revocation reason/category;
- reuse-detected time where applicable;
- User auth-version observed at qualification;
- bounded safe session-recognition metadata where accepted.

The design shall support efficient queries for:

- current presented refresh record;
- active sessions for a User;
- all members of a family for revocation;
- targeted session revocation;
- expiry cleanup.

Raw IP addresses, full user-agent histories or unrestricted fingerprint profiles shall not be required for refresh validity.

## 8. Atomic refresh rotation

Refresh rotation shall execute in one database transaction.

The transaction shall:

1. locate the presented refresh record using its opaque selector;
2. acquire a row-level lock or equivalent serialization boundary;
3. verify the presented secret against the stored verifier;
4. reject expiry/revocation/reuse/consumed state;
5. load and validate current User/account/auth-version authority;
6. validate required current membership/MFA policy authority for continuation;
7. mark the predecessor consumed/rotated;
8. create exactly one successor with a new random secret/verifier;
9. bind predecessor and successor lineage;
10. commit before the successor is treated as authoritative.

A uniqueness/constraint strategy shall prevent multiple valid successors from the same predecessor.

If two requests race on the same predecessor, at most one may complete normal rotation.

A later presentation of the consumed predecessor shall enter reuse handling rather than normal refresh.

No access/refresh credential shall be returned as successfully established authority if the rotation transaction fails to commit.

## 9. Refresh reuse and family revocation

Presentation of a correctly formed refresh credential whose server record proves it was already consumed/rotated shall be treated as suspected reuse.

Reuse handling shall:

- record a bounded security event;
- revoke at least the entire affected refresh family;
- reject issuance of new authenticated authority from that family;
- preserve sufficient safe evidence for investigation.

Family revocation shall be transactionally safe against concurrent refresh.

The implementation shall not reveal externally whether rejection resulted from an unknown selector, bad secret, expired credential, consumed credential or revoked family beyond the bounded client state needed to restart authentication.

Invalid random credentials that do not verify against a known session shall not permit an attacker to revoke arbitrary families.

## 10. Session expiry and revocation implementation

Refresh sessions shall have an absolute server-side expiry.

The implementation shall support:

- current-session revocation;
- all-session revocation for a User;
- authorized targeted administrative revocation;
- family revocation after reuse;
- revocation triggered by principal-wide security invalidation.

Logout shall revoke server-side refresh authority before or together with clearing the refresh cookie.

Cookie deletion without server revocation is not sufficient.

All-session revocation shall operate under bounded transactional semantics and shall ensure previously issued refresh credentials cannot recreate authority.

Expired/revoked rows may be retained temporarily for bounded reuse/security evidence according to retention policy, then safely purged.

## 11. MFA authenticator physical model

TOTP authenticator state shall be bound to the canonical User.

The physical state shall support at minimum:

- authenticator identifier;
- User identifier;
- factor type;
- lifecycle state;
- encrypted/protected TOTP secret material;
- encryption key identifier/version;
- enrollment creation time;
- verification/activation time;
- reset/disable time where applicable;
- bounded replay-prevention state where required.

Only the minimum active factor state required by the accepted MFA policy shall be exposed to application services.

TOTP secret plaintext shall exist only within the bounded enrollment/verification cryptographic operation and shall not be logged or serialized into audit/security events.

## 12. TOTP secret protection and key lifecycle

TOTP secrets shall be encrypted at rest using an application cryptographic boundary separate from ordinary database confidentiality.

The design shall use authenticated encryption.

Ciphertext persistence shall bind:

- encrypted secret;
- key identifier/version;
- algorithm/version metadata required for controlled decryption/rotation.

Production key material shall come from an external secret/key-management boundary and shall not be stored in repository source, migration files or database rows alongside ciphertext.

The implementation shall support key rotation through versioned key identifiers.

Rotation may use controlled re-encryption on access or an explicit governed rotation operation, but old key retirement shall not occur until all required active ciphertext has been safely migrated or invalidated.

Failure to access the required decryption key shall fail closed for MFA verification and shall not silently disable MFA.

Exact provider integration may remain environment-specific, but the application-facing encryption/decryption interface shall be deterministic and testable with non-production test keys.

## 13. TOTP verification and replay control

TOTP verification shall use accepted standard TOTP semantics with configuration-controlled period/digits and a bounded clock-skew window.

The implementation shall prevent practical replay of the same accepted TOTP step for the same authenticator where the operation would otherwise permit duplicate security authority.

Successful enrollment requires verification of a valid code generated from the newly issued secret before the authenticator becomes ACTIVE.

Failed verification shall participate in MFA throttling.

TOTP comparison and validation shall use established cryptographic library behavior rather than custom cryptographic algorithms.

Server clock correctness is an operational dependency; PATCH-060 shall qualify production operational monitoring where applicable.

## 14. Recovery-code physical model

Recovery codes shall be high-entropy randomly generated values.

Only non-reversible verifiers shall be persisted.

Each code record shall support at minimum:

- owning User;
- verifier;
- generation-set/version identifier;
- creation time;
- consumed time;
- invalidated time where applicable.

Consumption shall be atomic.

A successful code use shall mark exactly that code consumed before protected continuation is established.

A consumed code shall never verify successfully again.

Regenerating a recovery-code set shall invalidate all prior unconsumed codes for that factor/User.

Raw codes shall be displayed only during the bounded generation/regeneration response and shall not be retrievable later.

## 15. MFA assurance and Organization policy evaluation

The authenticated security context shall carry sufficient server-derived assurance state to distinguish:

- primary authentication only;
- MFA-qualified authentication;
- recent reauthentication/step-up where required.

Administrator access shall require current MFA-qualified assurance.

Organization member MFA shall be evaluated from current Organization policy and current membership/role state.

A session established before policy tightening shall not bypass the new requirement.

Where current assurance is insufficient, the server shall return a bounded MFA-required outcome rather than silently granting the protected operation.

Disabling or resetting a required factor shall trigger the EDS-058 invalidation behavior and shall not leave a stale MFA-qualified session authoritative.


## 16. Account and MFA recovery implementation

Recovery shall reuse existing canonical account/onboarding authority where compatible and shall not create a parallel identity system.

Administrative recovery shall require an authenticated, currently authorized Human administrator and the designated recent-authentication assurance.

Any temporary recovery credential shall be represented by:

- an opaque selector where lookup is required;
- a high-entropy random secret;
- a non-reversible persisted verifier;
- explicit purpose;
- subject User;
- creation and expiry times;
- single-use/consumed state;
- attributable issuing authority.

Recovery verification and consumption shall be atomic.

Successful password/account recovery shall increment the principal security version and revoke applicable refresh sessions.

Successful MFA reset/recovery shall invalidate stale MFA-qualified authority and require the applicable enrollment/authentication path before protected continuation.

Externally observable recovery behavior shall remain non-enumerating.

## 17. Recent-authentication and step-up implementation

The authenticated server context shall retain or derive a trusted authentication time and assurance level.

Sensitive operations shall evaluate:

- current authenticated User;
- current canonical authorization;
- current MFA requirement;
- current assurance level;
- age of the relevant authentication/step-up event.

The initial recent-authentication window shall be configuration-controlled and shall be frozen in the accepted Implementation Plan after security/UX qualification.

The window shall not be extended by ordinary API activity.

A successful designated reauthentication/step-up may establish a new bounded trusted authentication time.

Client-provided timestamps shall not establish recent-authentication authority.

## 18. Authentication throttling storage and keying

PATCH-058 shall use PostgreSQL-backed throttle state for Commercial V1 rather than introduce a new external runtime dependency solely for throttling.

Throttle state shall be bounded and purpose-specific.

Logical keys shall combine, as applicable:

- normalized credential identity transformed into a non-reversible keyed identifier; and
- trusted network-context key.

The database shall not persist plaintext passwords, OTPs, recovery codes or unnecessary raw credential identifiers in throttle records.

Network identity shall use the direct peer unless the request traverses an explicitly configured trusted proxy boundary.

Forwarded client-address headers from untrusted peers shall be ignored.

Throttle records shall support:

- operation/category;
- keyed subject/network identity;
- window start/expiry;
- attempt count;
- backoff/blocked-until state where applicable;
- bounded update timestamps.

Expired throttle state shall be eligible for bounded cleanup.

## 19. Throttle concurrency and response behavior

Throttle evaluation/update shall be atomic enough to prevent concurrent attempts from bypassing configured limits.

The implementation may use transactional row locking, atomic upsert/update semantics or equivalent database guarantees.

Throttle policy shall distinguish operation classes such as:

- primary authentication;
- MFA verification;
- recovery verification;
- bootstrap authentication where applicable.

Exact thresholds/windows/backoff values shall be configuration/policy controlled and frozen by the accepted Implementation Plan.

Externally observable responses shall not reveal whether throttling was keyed to an existing or nonexistent account.

Where `Retry-After` or equivalent retry guidance is exposed, it shall not create a practical credential-existence oracle.

Meaningful threshold/security events shall be auditable without logging submitted secrets.

## 20. Security-event persistence decision

PATCH-058 shall introduce a dedicated security-event persistence model rather than overload the existing engineering/general Audit model with authentication-specific lifecycle semantics.

The dedicated model is operational/security evidence only.

It shall support at minimum:

- event identifier;
- event type/category;
- event timestamp;
- subject User where known;
- acting User/Human administrator where applicable;
- Organization identifier where the event is Organization-scoped;
- refresh session/family identifier where safely applicable;
- outcome/classification;
- bounded reason/category;
- safe request/correlation identifier;
- bounded safe metadata;
- creation/source context.

The model shall not store passwords, raw tokens, refresh secrets, TOTP secrets, raw recovery codes, private signing keys or unrestricted request bodies.

Platform-wide events may have no Organization identifier but shall require platform authority for review.

## 21. Security-event visibility and retention

Security-event query authorization shall be applied before protected event disclosure.

Organization-scoped event queries shall require current Organization authority and shall scope by Organization before count/pagination.

Platform-wide event review shall require separate platform Human authority.

A User-facing session/security surface, if provided, shall expose only the subset of safe information required for the User's own session/security understanding.

Retention shall be configuration/policy controlled and shall preserve bounded investigation needs without creating indefinite unrestricted tracking history.

Security-event deletion/retention operations shall not mutate accepted engineering evidence.

## 22. Contact authorization implementation topology

Contact authorization shall be enforced through the canonical relationship:

`Contact -> Customer -> Organization`

Repository/service queries that retrieve Contact data for customer-accessible operations shall join or otherwise constrain through Customer Organization ownership before disclosure.

Direct Contact lookup by identifier shall not return a protected Contact to application response logic before current Organization authorization is established.

Where repository conventions require fetching before authorization, the service boundary shall ensure that no existence/attribute distinction escapes and shall return the established protected-not-found outcome.

PATCH-058 shall not add an independent `organization_id` owner to Contact solely for authorization.

Mutation operations shall qualify both current Organization authority and the Contact's canonical Customer relationship before mutation.

## 23. Customer and Contact search implementation

Customer and Contact search functions used by customer-accessible/global search shall accept an explicit current Organization scope or an equivalent server-derived authorization context.

The database query shall apply Organization restriction before:

- matching result exposure;
- total count;
- pagination;
- ordering;
- aggregate metadata.

Combined search shall pass the same current Organization authority independently into Customer and Contact search adapters.

A global/unscoped Customer or Contact search helper shall not be used by customer-facing protected routes unless the caller has separately authorized platform-wide authority and the route explicitly represents that authority.

Regression tests shall prove that another Organization's matching Customer/Contact cannot affect returned rows, totals or pagination.

## 24. Authorization-before-lookup service order

Protected resource operations shall follow this logical order:

1. authenticate current principal;
2. resolve current server-authoritative security/session state;
3. establish current Organization context where required;
4. establish current role/membership/action authority;
5. perform Organization-scoped protected lookup/query;
6. perform operation-specific validation;
7. disclose or mutate the resource.

Identifier possession is not authorization.

Where a resource identifier is invalid, nonexistent or belongs to another inaccessible Organization, externally visible behavior shall follow the established protected-not-found/anti-inference contract.

The implementation shall avoid authorization decisions based solely on client-provided Organization identifiers.

## 25. Refresh-cookie implementation

The refresh credential shall be issued as a server-managed browser cookie.

Production cookie requirements are:

- `HttpOnly = true`;
- `Secure = true`;
- `SameSite = Lax` as the default Commercial V1 policy unless an accepted implementation constraint proves a stricter/alternate value is required;
- Path restricted to the narrowest refresh/session route scope that supports the accepted flow;
- no unnecessary broad Domain attribute;
- expiry/max-age consistent with server-side refresh expiry.

The cookie value shall contain only the opaque refresh credential representation and shall not contain authoritative role/membership data.

Logout/revocation responses shall clear the cookie using attributes compatible with those used to set it.

Development exceptions shall be explicit configuration and shall fail closed in production validation.

## 26. CSRF and origin-defense implementation

Cookie-authenticated refresh/session-changing operations shall require explicit request-origin protection.

Commercial V1 shall use a combined design:

1. server validation of `Origin` for browser state-changing refresh/session endpoints when the header is present/required by browser context;
2. strict configured allowed application origins;
3. an anti-CSRF value bound to the browser/session flow and supplied through a non-cookie request channel/header for designated cookie-authenticated state-changing operations.

The anti-CSRF secret/value shall not itself grant authentication authority.

Cross-site requests that carry the refresh cookie but lack valid origin/CSRF qualification shall fail before refresh/session mutation.

CORS shall allow credentialed browser requests only from explicitly configured trusted application origins.

Wildcard credentialed origins are forbidden.

Trusted-host/proxy configuration remains independent and fail-closed.

Exact header/cookie names and token derivation belong to the accepted Implementation Plan, but shall preserve this dual origin + anti-CSRF contract.

## 27. Frontend authentication state machine

The frontend shall implement explicit bounded authentication states including at minimum:

`UNAUTHENTICATED`

`PRIMARY_AUTH_PENDING`

`MFA_REQUIRED`

`AUTHENTICATED`

`REFRESHING`

`REAUTH_REQUIRED`

`RECOVERY_REQUIRED` where applicable

`SESSION_INVALID`

Transitions shall be driven by server outcomes, not inferred solely from presence of client data.

The access credential shall exist only in application memory.

On full page reload, the client may attempt bounded refresh qualification using the protected refresh-cookie flow; it shall not restore an access credential from durable browser storage.

Refresh failure/revocation/reuse/security invalidation shall clear in-memory authority and transition to the appropriate safe state.

## 28. Frontend refresh coordination and cross-tab behavior

The frontend shall prevent uncontrolled refresh storms.

Within one application instance, concurrent requests encountering access expiry shall share or serialize a bounded refresh attempt rather than independently rotate the same refresh credential.

Because refresh credentials are single-use, cross-tab races shall be treated as a security-sensitive condition.

The implementation shall not persist bearer access credentials for cross-tab sharing.

Cross-tab coordination may use a non-secret browser coordination mechanism only to signal authentication-state changes such as logout/session-invalidated and to reduce avoidable refresh races.

Such coordination shall not transmit raw access/refresh credentials.

Server-side rotation/reuse protection remains authoritative even if browser coordination fails.

## 29. Activation, reset and URL-secret handling

Existing activation/reset flows that receive one-time credentials through URLs shall remove sensitive query/fragment material from the visible browser URL as early as safely possible after capture.

The secret shall not be copied into:

- analytics;
- application logs;
- unrelated navigation;
- referrer-bearing external requests;
- durable browser credential storage.

One-time activation/reset credentials shall retain their existing bounded server-side purpose/expiry semantics and shall be reconciled with PATCH-058 invalidation requirements.

The frontend shall not display raw internal identifiers as the normal Human-facing recovery/security journey.

## 30. Bootstrap implementation topology

Bootstrap authorization shall be centralized in a server-side bootstrap security service/dependency rather than implemented as route-local secret comparison alone.

Qualification shall verify:

- production/environment bootstrap policy;
- explicit enablement;
- configured window start/end semantics where applicable;
- current server time;
- valid bootstrap secret qualification;
- current bootstrap eligibility/completion state.

Successful completion shall persist or otherwise establish server-authoritative completion state that prevents subsequent bootstrap reuse.

Re-enable shall require an explicit Human-controlled operational action and shall be attributable.

Bootstrap qualification shall participate in throttle/security-event controls.

Bootstrap shall not issue a permanent alternate authentication mode.

## 31. Bootstrap failure and production configuration

Production startup/preflight shall fail closed for unsafe bootstrap configuration.

At minimum, production validation shall reject:

- enabled bootstrap without required bounded window semantics;
- missing/weak required bootstrap secret where bootstrap is enabled;
- malformed/expired bootstrap window configuration;
- configurations that unintentionally leave bootstrap permanently enabled.

After bootstrap completion, ordinary administrator authentication shall follow the accepted MFA/session model.

Bootstrap secrets shall use the existing secret/configuration boundary and shall not be committed to repository configuration examples as real secrets.

## 32. Backend module/service boundaries

The implementation should preserve existing repository layering and introduce bounded security modules rather than a monolithic authentication service.

Expected logical boundaries include:

- token/access validation;
- refresh-session repository/service;
- MFA/TOTP service;
- recovery-code/recovery service;
- throttle service;
- security-event repository/service;
- reauthentication/assurance service;
- Organization security-policy service;
- bootstrap security service;
- Contact/search authorization reconciliation.

Existing canonical User/Organization/membership repositories/services remain authoritative.

Physical filenames/class names may be adjusted to repository conventions in the accepted Implementation Plan, but the authority separation in this IDS shall remain.

## 33. API surface direction

PATCH-058 may add bounded authenticated API surfaces for:

- refresh;
- current-session logout;
- all-session revocation;
- session listing/targeted revocation where accepted;
- TOTP enrollment/verification;
- recovery-code regeneration/use;
- MFA reset/recovery administration;
- Organization member-MFA policy;
- bounded security-event review;
- recent-authentication/step-up.

Existing login, activation, password-change/reset, onboarding and administrative account routes shall be integrated rather than duplicated where they already own the canonical operation.

Exact paths, HTTP methods, DTO names and compatibility redirects belong to the accepted Implementation Plan.

API responses shall not expose raw verifiers, TOTP secrets after enrollment presentation, stored recovery-code values or internal cryptographic material.


## 34. Release-pipeline topology

PATCH-058 shall add a version-controlled CI/release-security pipeline that extends the existing PATCH-042 release foundation.

The logical pipeline shall execute these stages in dependency order:

1. source/revision qualification;
2. deterministic dependency installation from governed lock inputs;
3. backend/frontend quality gates;
4. migration-graph qualification;
5. security-negative qualification;
6. dependency/SAST/secret/container scanning as applicable;
7. artifact construction;
8. artifact digest calculation;
9. SBOM generation;
10. provenance/attestation generation;
11. vulnerability-gate evaluation;
12. cryptographic signing under authorized signer policy;
13. signature/trust verification;
14. release-dossier assembly and validation;
15. Human release-security approval.

A downstream stage shall not convert a failed required upstream gate into PASS.

CI may automate evidence production and fail-closed enforcement but shall not possess Human exception or release-approval authority.

## 35. Source and build identity

A release candidate shall originate from a clean attributable Git revision.

The pipeline shall record at minimum:

- full commit SHA;
- repository/ref context where applicable;
- dirty/clean qualification result;
- governed dependency-lock digests;
- migration-set identity;
- build/toolchain identity required for reproducibility.

Release artifacts shall not be qualified from an unrecorded dirty working tree.

If an authorized process intentionally builds from generated inputs, those inputs shall themselves be attributable and bound into provenance.

Mutable branch names alone are not release identity.

## 36. Quality and migration gates

The pipeline shall include deterministic repository-appropriate gates for:

- backend tests;
- frontend tests;
- frontend type/static checks;
- production frontend build;
- Python/static syntax qualification as applicable;
- migration graph/head validation;
- PATCH-058 security-negative regression.

Migration qualification shall prove that the release candidate references the expected migration graph/head.

A migration mismatch, multiple unexpected heads or failure to reconcile the expected schema identity shall block release qualification.

Actual representative production migration execution remains outside PATCH-058 and belongs to PATCH-060.

## 37. Security scanning topology

PATCH-058 shall establish automated scanning classes for:

- dependency vulnerabilities;
- static application security analysis;
- secret detection;
- container/image vulnerabilities where container images are release artifacts.

Scanner versions/configuration or their governed identities shall be attributable to the evidence they produce.

Raw scanner success alone is not release approval.

Findings shall be normalized sufficiently to bind:

- scanner/source;
- finding identity;
- affected component/artifact;
- severity;
- evidence timestamp/revision;
- disposition;
- applicable Human exception reference.

Scanner unavailability shall not silently produce PASS for a mandatory gate.

## 38. Vulnerability gate implementation

A version-controlled release-security policy shall map finding classes/severity to gate outcomes.

The policy shall preserve the accepted PATCH-042 floor, including blocking Critical findings and requiring governed Human handling for blocking High findings according to accepted policy.

Gate evaluation shall produce deterministic evidence identifying:

- evaluated candidate/artifact digest;
- policy version;
- findings considered;
- blocking findings;
- accepted applicable exceptions;
- final machine gate result.

An exception shall qualify only if all bound scope/digest/finding/expiry requirements match.

Machine gate PASS does not replace Human release approval.

## 39. Vulnerability-exception physical representation

The existing PATCH-042 vulnerability-exception schema shall be reused/extended rather than replaced.

An accepted exception record shall bind at minimum:

- finding identifier;
- affected component/artifact;
- exact artifact digest where available;
- rationale;
- compensating controls;
- scope;
- Human approver identity/evidence;
- approval time;
- expiry;
- retest/revalidation requirement;
- status.

Validation shall fail closed when:

- required fields are absent;
- the artifact digest differs;
- the exception is expired/revoked;
- the finding/scope does not match;
- Human approval evidence is invalid/missing.

Exceptions shall be versioned/attributable release evidence.

## 40. Artifact construction and digest identity

Governed release artifacts shall be constructed before final release-security evidence is bound.

Each designated artifact shall receive a cryptographic digest calculated from the exact bytes being qualified.

PATCH-058 shall use SHA-256 at minimum for artifact identity unless an accepted stronger repository standard supersedes it.

The release pipeline shall not rely on mutable image tags, filenames or branch names as artifact identity.

Where container images are produced, digest-pinned image identity shall be captured.

Migration release content shall have a deterministic digest/identity covering the exact migration set included in the candidate.

Any post-digest mutation creates a different artifact and invalidates evidence bound to the prior digest.

## 41. SBOM physical format and binding

PATCH-058 shall generate machine-readable SBOM evidence using an industry-standard format supported by the selected tooling.

CycloneDX JSON or SPDX JSON are acceptable physical formats; the accepted Implementation Plan shall select one primary format based on repository/toolchain support.

The selected format shall identify at minimum:

- release/artifact identity;
- components/packages;
- resolved versions;
- package identifiers where available;
- dependency relationships where supported;
- generator/tool identity;
- generation timestamp or attributable build context.

The SBOM file itself shall receive a cryptographic digest.

The release dossier shall bind the SBOM digest/reference to the exact candidate/artifact set.

## 42. Provenance and attestation representation

PATCH-058 provenance shall use a machine-readable signed/verifiable attestation representation compatible with the selected build/signing tooling.

The provenance payload shall bind at minimum:

- source commit SHA;
- build invocation/builder identity;
- governed dependency-lock identities;
- designated artifact digests;
- SBOM digest/reference;
- relevant gate/evidence references;
- release identity.

The provenance artifact itself shall be immutable/digest-addressable.

The accepted Implementation Plan shall select the concrete attestation format/tooling, preferring a standard representation such as an in-toto/SLSA-compatible statement where practical.

A provenance statement whose subject digest does not match the release artifact shall fail verification.

## 43. Signing technology boundary

PATCH-058 shall use asymmetric cryptographic signing or an equivalent modern artifact-signing mechanism that provides independently verifiable signer/trust evidence.

The concrete tool/provider shall be selected by the accepted Implementation Plan based on deployment/repository constraints.

The design shall support:

- signing exact artifact digests;
- verification without trusting mutable artifact names;
- identifiable authorized signer/trust root;
- key/signer rotation;
- signer/key revocation;
- verification failure on untrusted/revoked authority.

Private signing material shall remain outside repository source and release artifacts.

A local developer key shall not become production release authority merely because it can technically create a valid cryptographic signature.

## 44. Signing authorization and key custody

Human release/security authority controls which signer policy is authorized for a release process.

Signing execution may be automated only through a controlled signer boundary whose authority has been explicitly established by Human governance.

Production signing credentials shall be held in an appropriate external secret/key/signing service boundary or equivalent protected CI secret facility with least privilege.

The application database shall not become the custody location for production private signing keys.

Key/signer rotation shall preserve verifiability of required historical release evidence according to retention policy.

Revoked signer authority shall prevent new release qualification under that signer.

CI configuration alone shall not be allowed to silently broaden signing authority.

## 45. Signature verification gate

Every designated signed release artifact shall be verified after signing and before release-dossier qualification.

Verification shall bind:

- exact artifact digest;
- signature;
- authorized signer identity;
- accepted trust root/policy;
- current revocation/trust status.

Verification failure, unknown signer, digest mismatch or revoked/untrusted signing authority shall block the release gate.

The pipeline shall retain bounded verification evidence for the release dossier.

Successful cryptographic verification proves artifact/signature trust under policy; it does not itself constitute Human release approval.

## 46. Release-manifest reconciliation

The existing PATCH-042 release-manifest schema shall remain the base release manifest authority and shall be extended/reconciled only where PATCH-058 evidence requires additional explicit fields.

Existing concepts including:

- release identity;
- Git commit;
- backend/frontend digests;
- expected Alembic head;
- configuration-schema identity;
- migration digest;
- lock digests;
- SBOM reference;
- scan-evidence reference;
- signing-approver evidence;
- creation time

shall not be duplicated into a competing manifest authority.

PATCH-058 may add explicit provenance/signature/trust/dossier references where the existing schema cannot represent them unambiguously.

Schema evolution shall remain versioned and fail closed.

## 47. Release-dossier physical structure

The release dossier shall be a machine-readable, versioned evidence index plus the referenced immutable evidence artifacts.

The dossier index shall bind at minimum:

- dossier schema version;
- release identifier;
- source commit SHA;
- build-input/lock identities;
- artifact names/types and exact digests;
- migration identity/head/digest;
- test/build evidence references;
- security-negative evidence reference;
- scanner evidence references;
- vulnerability-gate result;
- applicable exception references;
- SBOM digest/reference;
- provenance digest/reference;
- signature/trust-verification evidence;
- Human release-security approval evidence.

Every referenced evidence artifact shall be digest-addressable or otherwise cryptographically bound where practical.

Dossier validation shall reject missing, mismatched, expired or candidate-inconsistent evidence.

## 48. Human release approval evidence

Human release approval shall be a distinct attributable record/evidence item and shall not be inferred from CI success, signature existence or dossier assembly.

The evidence shall identify at minimum:

- release candidate/release identifier;
- exact source/artifact context being approved;
- Human approver identity/authority;
- decision;
- decision time;
- applicable exception references.

The approval mechanism shall not expose or require private signing-key material.

A materially changed artifact/digest after approval requires requalification/reapproval.

PATCH-060 may consume this evidence but shall independently approve production deployment/certification.

## 49. Release-evidence storage boundary

Release-security evidence may reside in repository-backed release records, CI artifact storage or another governed immutable evidence store selected by the accepted Implementation Plan.

Regardless of physical storage:

- evidence references shall be attributable;
- exact digests shall be retained where applicable;
- mutable URLs/names alone shall not establish identity;
- access to sensitive evidence shall be bounded;
- secrets/private keys shall not be embedded;
- retention shall support Commercial V1 release traceability.

Application-domain PostgreSQL shall not become the default storage for large SBOM/scanner/provenance artifacts unless a later accepted design explicitly requires it.

## 50. CI workflow and privilege separation

CI workflow definitions shall be version-controlled.

Quality/scanning jobs shall operate with the minimum permissions required.

Untrusted build/test steps shall not automatically receive production signing credentials.

Signing shall occur only after required upstream qualification and within the controlled signer boundary.

Human exception/approval evidence shall not be forgeable merely by editing ordinary CI output.

Where repository-hosted environment protection or equivalent approval gates are used, the accepted Implementation Plan shall document how they map to Human authority.

## 51. Supply-chain negative qualification

The release-security implementation shall include deterministic negative tests/evidence for at least:

- artifact bytes changed after digest;
- SBOM subject/reference mismatch;
- provenance subject mismatch;
- signature over a different digest;
- unknown signer;
- revoked/untrusted signer;
- expired vulnerability exception;
- exception bound to another artifact digest;
- missing mandatory scan evidence;
- scanner execution failure represented as PASS;
- release manifest/dossier source-revision mismatch;
- unsigned designated artifact;
- attempted release approval without attributable Human evidence.

These vectors shall fail release qualification.


## 52. Transaction and concurrency boundaries

PATCH-058 shall preserve explicit atomic boundaries for security-sensitive state transitions.

At minimum, these operations require transactional or equivalent concurrency-safe semantics:

- refresh rotation and predecessor/successor creation;
- refresh reuse detection and family revocation;
- current/all/targeted session revocation;
- recovery-code consumption;
- recovery-code set replacement;
- MFA enrollment activation/reset transitions;
- principal security-version change with required session invalidation;
- Organization security-policy changes where stale assurance must be rejected;
- throttle counter/backoff updates;
- last-administrator-sensitive security administration;
- vulnerability-exception lifecycle where repository tooling maintains mutable status.

Retries shall be safe and shall not create duplicate active successors, duplicate recovery-code consumption, duplicate factor activation or weakened revocation.

Database constraints shall enforce invariants that must survive concurrent application processes rather than relying only on in-process checks.

## 53. Persistence and migration direction

PATCH-058 implementation is expected to require a forward Alembic migration from the sole accepted head verified at implementation preflight.

The migration design may introduce bounded structures for:

- refresh session/family persistence;
- MFA authenticator persistence;
- recovery-code verifier persistence;
- Organization member-MFA policy;
- dedicated security-event persistence;
- PostgreSQL-backed throttle persistence;
- additional bounded security-version fields only if required by the accepted implementation design.

The migration shall not duplicate canonical User, Organization, membership, Customer or Contact ownership.

Migration naming, exact columns, indexes, constraints, upgrade/downgrade behavior and compatibility sequencing shall be frozen in the accepted Implementation Plan before migration creation.

No migration is authorized by this IDS.

## 54. Index and query direction

Security persistence shall include indexes/constraints supporting bounded lookup paths without broad scans.

Expected indexed dimensions include, where physically represented:

- refresh opaque selector;
- refresh User;
- refresh family;
- refresh expiry/revocation state;
- MFA User/factor state;
- recovery-code User/set state;
- security-event Organization/time;
- security-event subject/time;
- throttle key/category/expiry.

Sensitive secret verifiers shall not be used as Human-readable lookup identifiers.

Contact/Customer protected search shall retain Organization-scoped query plans before count/pagination.

The accepted Implementation Plan shall validate exact indexes against actual repository model/query conventions.

## 55. Performance and boundedness

PATCH-058 security checks shall remain bounded for normal authenticated request paths.

Access-token validation shall not trigger unnecessary broad database scans.

Current canonical security/membership qualification shall use indexed primary/foreign-key paths.

Refresh rotation shall touch only the presented session/family and required current authority state.

Session listing shall be bounded/paginated where the number of retained sessions can grow.

Security-event review shall be bounded/paginated and time/order indexed.

Throttle cleanup and expired security-state cleanup shall not execute as unbounded synchronous work on ordinary login requests.

Release scanning/SBOM/signing/dossier operations are asynchronous/offline release qualification and are not normal request-path latency requirements.

## 56. Observability and safe logging

PATCH-058 shall emit operationally useful but secret-safe diagnostics.

Logs may include bounded identifiers/correlation references required to diagnose:

- authentication failure class;
- refresh/session lifecycle failure;
- MFA/recovery failure category;
- throttle activation;
- bootstrap rejection;
- Contact/search authorization denial;
- release-gate/scanner/signature/dossier failure.

Logs shall not include:

- passwords;
- raw access tokens;
- raw refresh credentials;
- raw TOTP secrets;
- submitted TOTP values;
- raw recovery codes;
- private signing keys;
- unrestricted sensitive request bodies.

Security events and ordinary application logs are complementary; logs shall not become canonical security authority.

## 57. Failure and fail-closed behavior

Security-sensitive ambiguity shall fail closed.

Examples include:

- missing mandatory access-token security/session claims;
- unknown or invalid refresh credential;
- unavailable required MFA key material;
- stale User/account/security version;
- insufficient current Organization authority;
- stale MFA assurance after policy tightening;
- invalid CSRF/origin qualification;
- unsafe bootstrap state;
- mandatory scanner unavailable;
- SBOM/provenance/signature/digest mismatch;
- missing Human vulnerability-exception evidence;
- missing Human release-approval evidence.

Failure shall not silently downgrade to legacy weaker behavior.

User-facing errors shall remain bounded and shall avoid unnecessary identity/resource inference.

## 58. Compatibility transition

PATCH-058 shall provide a controlled transition from the current stateless-refresh/browser-token behavior to the accepted session model.

The transition shall account for:

- currently issued legacy refresh JWTs;
- existing access JWTs using current claim conventions;
- current `auth_version` behavior;
- current browser token persistence;
- existing login/activation/reset flows;
- existing PATCH-041 account/onboarding flows.

Legacy refresh credentials shall not receive indefinite compatibility.

The accepted Implementation Plan shall define a bounded cutover strategy after which only server-backed rotating refresh credentials are accepted.

The frontend shall remove durable browser bearer-token persistence as part of the same governed cutover.

Missing security-version claims shall not retain silent steady-state fallback after cutover.

## 59. Authorization and Human-control matrix

Implementation shall preserve these authority boundaries:

| Operation | Automated system role | Required Human authority |
| --- | --- | --- |
| ordinary authentication | verify policy/credentials | User authenticates |
| MFA enrollment | generate/verify bounded factor flow | User completes enrollment |
| recovery-code generation | generate and persist verifiers | User controls resulting codes |
| account/MFA administrative recovery | enforce workflow/evidence | authorized Human administrator |
| session revocation | enforce requested revocation | User or authorized administrator |
| Organization member-MFA policy | enforce policy | authorized Organization administrator |
| security-event review | scope/query evidence | authorized Human viewer |
| vulnerability finding | detect/classify evidence | no automated exception authority |
| vulnerability exception | validate bound exception | authorized Human security approver |
| artifact signing execution | execute within controlled signer policy | Human-authorized signer policy |
| release approval | assemble/validate evidence | authorized Human release authority |
| engineering evidence/report acceptance | no new authority | existing Human engineering authority |

AI may explain, summarize, identify risk and assemble non-authoritative evidence.

AI shall not authenticate, bypass MFA, recover credentials, grant/revoke roles, approve vulnerability exceptions, establish signing authority, approve a release or accept canonical engineering outputs.

## 60. Security-negative conformance map

PATCH-058 implementation qualification shall include at minimum these application-security vectors:

1. access token missing mandatory security-version claim fails after cutover;
2. stale principal security version fails;
3. disabled account cannot continue through refresh;
4. revoked refresh session cannot rotate;
5. consumed refresh credential triggers reuse handling;
6. concurrent refresh cannot create two valid successors;
7. family reuse revocation prevents successor continuation;
8. logout invalidates server refresh authority;
9. all-session revocation prevents old refresh continuation;
10. administrator route rejects non-MFA-qualified assurance;
11. Organization MFA tightening blocks stale insufficient assurance;
12. consumed recovery code cannot be reused;
13. regenerated recovery-code set invalidates old unused codes;
14. TOTP enrollment is not ACTIVE before verification;
15. invalid/untrusted forwarded network identity cannot bypass throttle;
16. auth/recovery responses do not disclose account existence through designed response semantics;
17. cross-Organization Contact direct lookup does not disclose;
18. cross-Organization Contact/Customer search does not affect rows/count/pagination;
19. refresh/session mutation fails invalid CSRF/origin qualification;
20. bootstrap fails when disabled/outside window/completed;
21. URL credential is not retained in durable browser auth storage;
22. revoked/stale browser state cannot restore authority through cross-tab coordination.

Supply-chain negative vectors defined in Section 51 are also mandatory release-security qualification.

## 61. Test and conformance topology

Implementation qualification shall include layered tests rather than relying on one end-to-end surface.

Expected layers include:

- unit tests for token/session/MFA/recovery/throttle/security-policy logic;
- repository/service tests for persistence constraints and Organization scoping;
- DB-backed concurrency tests for refresh/recovery/throttle invariants;
- route/API tests for authentication/authorization/anti-enumeration outcomes;
- frontend tests for memory-only access state, refresh coordination, MFA/recovery and stale-session UX;
- security-negative tests from Section 60;
- migration qualification from accepted pre-PATCH-058 head to new head;
- release-pipeline policy/schema tests;
- supply-chain negative tests from Section 51;
- production frontend build/type/static qualification;
- bounded backend regression;
- bounded frontend regression.

Test fixtures shall not require production/customer credentials or production databases.

## 62. Independent security qualification

Before PATCH-058 closure, evidence shall include an independent security review against the accepted threat model and implementation.

The qualification shall be penetration-oriented and shall actively attempt at minimum:

- cross-tenant inference;
- token/session replay;
- refresh concurrency/reuse;
- MFA/recovery bypass;
- throttling bypass;
- CSRF/origin bypass;
- bootstrap misuse;
- privilege/stale-authority continuation;
- release-evidence substitution;
- exception/digest mismatch;
- signer/trust mismatch.

Independent review findings shall be classified under the governed Critical/Major/Minor process.

Unresolved blocking findings return to governance/remediation before closure.

## 63. Frontend implementation manifest direction

Expected frontend implementation impact includes bounded changes/additions for:

- AuthProvider/auth state;
- API client access-token injection;
- refresh coordination;
- login MFA challenge;
- TOTP enrollment;
- recovery-code presentation/use;
- reauthentication/step-up;
- session expiry/revocation UX;
- session-management surface where accepted;
- Organization member-MFA policy administration;
- administrative recovery/MFA-reset flow;
- activation/reset URL-secret cleanup;
- logout/all-session behavior;
- cross-tab safe state signaling;
- accessible RTL/responsive security journeys.

Exact file/component names shall follow actual repository conventions frozen in the Implementation Plan.

No raw internal identifier shall become the normal Human-facing navigation mechanism.

## 64. Backend implementation manifest direction

Expected backend implementation impact includes bounded changes/additions for:

- security/token configuration;
- access-token validation;
- refresh persistence/repository/service/routes;
- MFA authenticator persistence/service/routes;
- recovery-code persistence/service/routes;
- security-version invalidation integration;
- Organization MFA policy;
- reauthentication assurance;
- PostgreSQL throttle persistence/service;
- dedicated security-event persistence/service;
- bootstrap enforcement;
- Contact/Customer search Organization scoping;
- authorization-before-lookup reconciliation;
- migration/schema qualification;
- release-security schemas/scripts/workflows/evidence validators.

Existing canonical User/Organization/membership/Customer/Contact authorities shall be extended only where required and shall not be replaced.

## 65. Implementation batching direction

The future PATCH-058 Implementation Plan should preserve small independently reviewable batches.

A suitable dependency direction is:

- Batch A — persistence/security primitives and migration;
- Batch B — refresh/session rotation, revocation and security-version integration;
- Batch C — MFA, recovery, reauthentication and Organization MFA policy;
- Batch D — throttling, security events, bootstrap and tenant-isolation reconciliation;
- Batch E — frontend browser-auth/MFA/session/recovery hardening;
- Batch F — CI/security scanning/SBOM/provenance/signing/release dossier;
- Batch G — integrated security-negative, regression and independent qualification.

The accepted Implementation Plan may refine boundaries based on actual repository dependencies.

No batch is authorized for implementation by this IDS.

## 66. PATCH-059 and PATCH-060 separation

PATCH-058 shall stop at the accepted security and reproducible-release foundation.

PATCH-059 remains authoritative for:

- commercial package configuration;
- signed offline entitlements/licensing;
- seats;
- validity/grace/update;
- entitlement anti-rollback;
- entitlement backend enforcement/admin UX.

PATCH-060 remains authoritative for:

- representative production deployment qualification;
- DNS/certificate deployment evidence;
- executed backup/restore/recovery;
- monitoring/alert-delivery qualification;
- support exercise;
- upgrade/rollback operational qualification;
- capacity qualification;
- measured RPO/RTO/SLO;
- final Commercial V1 Release Certification.

PATCH-058 release dossier is an input to later certification, not PATCH-060 certification itself.

## 67. Explicit non-scope

IDS-058 does not authorize or design:

- SSO/SAML/OIDC/SCIM;
- WebAuthn/passkeys;
- new IAM role families;
- Kubernetes/HA/multi-region/SaaS orchestration;
- billing/finance/ERP/BPM/CRM;
- new engineering disciplines;
- autonomous AI security authority;
- autonomous vulnerability exceptions;
- autonomous release approval;
- production/customer database operations;
- representative production deployment;
- PATCH-059 entitlement implementation;
- PATCH-060 certification execution.

## 68. Implementation Plan obligations

The future PATCH-058 Implementation Plan shall, before implementation, freeze and verify at minimum:

1. actual repository files/modules to change;
2. actual current auth/token/frontend-storage implementation;
3. exact access JWT claims/lifetime/configuration;
4. exact refresh credential encoding and verifier primitive;
5. exact refresh tables/columns/indexes/constraints;
6. exact security-version fields and invalidation operations;
7. exact TOTP library/parameters/replay handling;
8. exact authenticated-encryption library/interface and production key source;
9. exact recovery-code format/verifier;
10. exact throttle schema/threshold configuration/cleanup;
11. exact security-event schema/taxonomy/retention;
12. exact Organization MFA-policy representation;
13. exact Contact/Customer repository/service queries requiring reconciliation;
14. exact CSRF header/value derivation and allowed-origin configuration;
15. exact cookie name/path/lifetime attributes;
16. exact bootstrap completion/enforcement persistence;
17. exact frontend state/components/routes and legacy-storage cutover;
18. exact API paths/DTOs and compatibility behavior;
19. exact Alembic migration from verified sole head;
20. exact CI provider/workflow files;
21. exact dependency/SAST/secret/container scanners;
22. exact SBOM format/tool;
23. exact provenance/attestation format/tool;
24. exact signing provider/tool/trust/key-custody interface;
25. exact release-manifest/schema reconciliation;
26. exact release-dossier schema/storage;
27. exact Human exception/signing-authorization/release-approval evidence mechanism;
28. exact test commands, DB harness and negative vectors;
29. exact implementation batches and rollback/stop boundaries.

Any material inability to satisfy an accepted IDS invariant shall return to governance before implementation rather than silently weaken the design.

## 69. Stop boundary

STOP and return to governance before implementation if any of the following occurs:

- accepted Discovery/Architecture/ADR/EDS semantics would need to change;
- a Critical or Major independent-review finding remains unresolved;
- deterministic tenant isolation cannot be achieved inside the accepted ownership model;
- refresh rotation/reuse cannot be made concurrency safe;
- mandatory administrator MFA would require weakening accepted authority;
- secure TOTP key custody cannot be established;
- recovery/throttling behavior creates material enumeration or bypass;
- production-safe CSRF/browser credential handling cannot be established;
- required migration cannot remain forward/reconcilable from the accepted sole head;
- release evidence cannot be cryptographically bound to exact candidate artifacts;
- signing authority would be controlled by CI/AI rather than accepted Human governance;
- mandatory security scanning would require false PASS on unavailable evidence;
- implementation would require production/customer DB access;
- PATCH-059/060 scope would need to be pulled into PATCH-058;
- unrelated dirty work cannot be isolated.

Any such condition returns to governance before implementation.

## 70. IDS self-review

Traceability to EDS-058: PASS.

Canonical identity/Organization/membership ownership preserved: PASS.

Layered security-version strategy defined: PASS.

Server-backed rotating refresh design defined: PASS.

Atomic rotation/reuse/revocation defined: PASS.

Mandatory administrator MFA and Organization member-MFA policy preserved: PASS.

TOTP protection/key lifecycle defined: PASS.

Recovery-code single-use verifier design defined: PASS.

Human-controlled recovery/reauth preserved: PASS.

PostgreSQL-backed bounded throttling defined: PASS.

Dedicated safe security-event model defined: PASS.

Contact/Customer Organization isolation defined: PASS.

Authorization-before-lookup/anti-inference preserved: PASS.

Memory-only browser access-token model preserved: PASS.

HttpOnly refresh cookie plus explicit CSRF/origin defense defined: PASS.

Bootstrap server-authoritative lifecycle defined: PASS.

CI/security scanning/vulnerability gates defined: PASS.

SBOM/provenance/digest/signature/dossier binding defined: PASS.

Human vulnerability/signing/release authority preserved: PASS.

Security-negative and independent qualification defined: PASS.

PATCH-059/PATCH-060 separation: PASS.

No migration/code/deployment authorized by IDS: PASS.

## 71. Governance disposition

IDS-058 candidate is **COMPLETE / READY FOR INDEPENDENT IDS REVIEW**.

Human IDS acceptance is not implied.

Implementation Plan, production-code implementation, migration creation/execution, database mutation, staging, commit, push, deployment, PATCH-059 and PATCH-060 remain unauthorized.

IDS-058: CANDIDATE / READY FOR INDEPENDENT IDS REVIEW

## 72. Human IDS Acceptance

- Human Implementation Design Authority decision: **PASS / ACCEPTED / COMPLETE**.
- Acceptance date: 2026-09-23.
- Accepted after Independent IDS Review returned **PASS / READY FOR HUMAN IDS ACCEPTANCE** with Critical/Major/Minor = 0/0/0.
- The layered security-version strategy, server-backed rotating refresh-session design, MFA/recovery/reauthentication design, bounded PostgreSQL throttling, dedicated security-event model, tenant-isolation enforcement, browser credential/CSRF model, bootstrap lifecycle, release-security pipeline, SBOM/provenance/signature trust boundaries and release-dossier implementation design are accepted.
- Existing canonical identity, Organization, membership, Customer, Contact and engineering authorities remain controlling; Human security/recovery/signing/release authority is preserved; AI remains advisory and non-authoritative.
- The Independent IDS Review recorded one non-blocking Observation: concrete supply-chain tooling selections remain intentionally bound to the Implementation Plan while the IDS-level security invariants and trust boundaries remain fixed.
- This acceptance authorizes progression to PATCH-058 Implementation Plan preparation and independent review only.
- It does not authorize production-code implementation, migration creation/execution, database mutation, deployment, PATCH-059, PATCH-060, or canonical semantic changes.

IDS-058: HUMAN ACCEPTED / COMPLETE
