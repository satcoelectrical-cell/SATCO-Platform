# EDS-059 — Commercial Package Configuration, Seats & Signed Entitlements

**Date:** 2026-09-30
**Status:** HUMAN ACCEPTED
**Authority:** Architecture-059 and EDS-059 are Human accepted. This acceptance authorizes progression to a separately governed IDS-059 candidate; it does not authorize migration, implementation, deployment, release, closure or PATCH-060 work.

## 1. Purpose and authority boundaries

EDS-059 freezes executable design contracts for the PATCH-059 signed-offline commercial entitlement capability.

The PATCH-051 EntitlementDecisionPort remains the only package-commercial decision seam. Commercial entitlement is restrictive only and never grants identity, membership, role, resource, engineering, package-compatibility, Human-acceptance or release authority.

Backend/server state is authoritative. Frontend surfaces status and administration only.

## 2. Signed entitlement envelope

Commercial entitlement format is SATCO Commercial Entitlement v1.

The persisted/imported artifact is a UTF-8 JSON envelope with exactly:
- schema = satco.commercial-entitlement/v1;
- key_id;
- payload: JSON object;
- signature: unpadded base64url Ed25519 signature over canonical payload bytes.

The signed bytes are RFC 8785 JSON Canonicalization Scheme (JCS) bytes of payload only. Duplicate JSON member names, non-I-JSON values, unknown top-level envelope members and malformed UTF-8 are rejected before verification.

Payload has closed fields: entitlement_id UUID, revision positive integer, organization_id UUID, deployment_id bounded string, issued_at UTC, not_before UTC, valid_until UTC, grace_until UTC, package_keys closed set, seat_capacity positive integer, support_until UTC/null, baseline_release_sequence positive integer, max_release_sequence positive integer, issuer string and schema_version = 1. max_release_sequence must be greater than or equal to baseline_release_sequence.

Unknown payload fields fail closed in V1. Package keys are only the accepted E/I/C commercial keys; Core is implicit shared foundation and is not a bypassable package flag.

## 3. Signature and trust

Algorithm is Ed25519 using the existing Python cryptography dependency. No runtime private signing key exists in the customer deployment.

Production has a source-controlled or deployment-governed verification trust store containing key_id, Ed25519 public key, activation bound and optional revocation bound/status. Private keys are prohibited.

Unknown/revoked/not-yet-valid verification key, invalid signature or key/payload mismatch yields INVALID_OR_UNAVAILABLE.

Key rotation permits overlapping verification keys for already-issued artifacts within explicit bounds. Revocation is fail closed for CONFIGURE/EXECUTE. IDS shall freeze trust-store file/config representation and operational replacement procedure.

Commercial issuer trust is independent from PATCH-058 release signing trust.## 4. Binding and temporal validation

organization_id must exactly equal the canonical selected Organization under current authenticated authority. deployment_id must exactly equal validated SATCO_DEPLOYMENT_ID.

issued_at <= not_before <= valid_until <= grace_until is mandatory. All values are timezone-aware UTC.

Grace duration is 30 days in Commercial V1. An artifact whose grace_until exceeds valid_until + 30 days is invalid. EDS-059 intentionally does not allow customer-configurable extension beyond 30 days.

Current effective state:
- before not_before: INVALID_OR_UNAVAILABLE for commercial execution;
- not_before through valid_until inclusive: ACTIVE;
- after valid_until through grace_until inclusive: GRACE;
- after grace_until: EXPIRED.

Boundary comparison uses server UTC and the trusted-time rules below.

## 5. Durable entitlement state

Server persistence owns one current accepted commercial state per Organization+deployment and immutable activation history.

Current state stores organization_id, deployment_id, entitlement_id, accepted_revision, canonical_payload_digest SHA-256, key_id, temporal bounds, seat_capacity, package rights, support/update bounds, last_trusted_time, accepted_at and bounded actor/correlation provenance.

Raw entitlement envelope may be retained in protected bounded storage for verification/support evidence, but normalized state must always retain its canonical payload digest and signature/key reference.

Activation is transactional. A new entitlement becomes current only after complete parse, canonicalization, signature/trust, binding, temporal, package, revision and capacity validation succeeds.

## 6. Revision and anti-rollback

revision is strictly monotonic per Organization+deployment.

revision lower than accepted_revision is rejected as ROLLBACK_DETECTED. Equal revision is idempotently acceptable only if canonical payload digest and entitlement_id equal the accepted state; any same-revision conflict is rejected.

Higher revision activation atomically advances current entitlement and durable high-water revision.

Ordinary administrators have no API to lower/reset revision.

The database high-water state is necessary but not sufficient for disaster recovery. Backup/recovery evidence must include the accepted revision and payload digest. After restore, commercial CONFIGURE/EXECUTE remains blocked until recovery reconciliation proves the restored state is not older than the governed recovery anchor. PATCH-060 must qualify this path.

IDS shall freeze the exact recovery-anchor artifact and locking SQL.## 7. Trusted time

Server UTC is the only runtime time source. Browser/client timestamps are ignored for authority.

Each successful entitlement-sensitive authoritative evaluation advances last_trusted_time to max(previous last_trusted_time, observed server UTC) within the same durable commercial state boundary when a persistence update is required.

A server UTC observation more than 5 minutes behind last_trusted_time enters TIME_UNTRUSTED. CONFIGURE/EXECUTE fail closed. Moving the clock forward does not permit later backward movement to regain grace.

A backward difference of 5 minutes or less is tolerated as operational skew but never lowers last_trusted_time.

TIME_UNTRUSTED recovery requires an attributable privileged operational procedure; ordinary entitlement/seat admin cannot clear it. IDS must bind recovery to deployment/recovery evidence.

## 8. Named seats

A seat assignment is keyed by Organization+user and references a canonical UserOrganizationMembership. Exactly one active/reserved assignment per Organization+user is permitted.

Both admin and engineer application users consume a seat when using commercial CONFIGURE/EXECUTE capability. Roles do not create seat exemptions.

Seat assignment requires an enabled canonical Organization membership at assignment time, available capacity, ACTIVE entitlement state, recent reauthentication and administrator authority.

Disabling/removing a membership makes its seat non-executable but the assignment remains RESERVED and continues consuming capacity until an administrator explicitly releases it. This avoids accidental seat recycling during temporary identity suspension.

Seat release requires administrator authority and recent reauthentication. Releasing a seat grants no access and does not alter membership.

Concurrent assignment is serialized under an Organization+deployment commercial-state lock. Capacity is checked under the same transaction.

## 9. Capacity reduction and OVER_CAPACITY

A successor entitlement may reduce seat_capacity below assigned+reserved seat count. Activation is allowed so a legitimate commercial reduction cannot be blocked by local assignments.

The resulting condition is OVER_CAPACITY. Existing assignments remain recorded; no assignment is auto-deleted.

While OVER_CAPACITY:
- no new seat assignment;
- no package expansion;
- no new commercial package configuration;
- ACTIVE/GRACE execution is allowed only for the deterministic subset of assignments designated retained by explicit administrator remediation.

To avoid arbitrary runtime winner selection, immediately after a capacity-reducing activation below assignment count, CONFIGURE/EXECUTE is blocked for all assigned users until an administrator explicitly marks at most seat_capacity assignments as retained or releases assignments.

IDS must freeze the retained-assignment transition and locking contract.## 10. Package operation matrix

ACTIVE:
- HISTORICAL_READ: allowed only after all canonical authorization gates;
- EXECUTE: permitted for entitled package and executable assigned seat;
- CONFIGURE: permitted for entitled package and executable assigned seat.

GRACE:
- HISTORICAL_READ: canonical authorization only;
- EXECUTE: permitted only for packages already configured before valid_until and users with executable seat assignments;
- CONFIGURE: denied when it would add/enable a package, create a new package binding, expand seats or otherwise expand commercial capability;
- bounded non-expanding repair/admin actions are limited to seat release, retained-seat remediation and entitlement replacement.

EXPIRED / INVALID_OR_UNAVAILABLE / TIME_UNTRUSTED:
- CONFIGURE and EXECUTE denied;
- HISTORICAL_READ remains subject to canonical authorization and historical-read rules.

A package removed by successor entitlement is denied for new CONFIGURE/EXECUTE from successor activation onward. Historical read remains possible under canonical authorization.

The commercial evaluator never returns PERMITTED before existing data/resource authorization and package configuration/compatibility gates have succeeded.

## 11. Historical read/export

HISTORICAL_READ does not require a current commercial seat when the user otherwise has current canonical authorization to the historical record.

It permits retrieval/interpretation/export of existing canonical facts only. It cannot create new engineering facts, recompute-and-persist package outputs, mutate configurations, advance workflow/deliverable state or invoke package execution with durable side effects.

Existing Evidence, Technical Report, standards-rights, tenant and resource authorization remain authoritative. Entitlement cannot widen them.

## 12. Support entitlement

support_until is informational/commercial eligibility. Expiry may surface support-ineligible status but cannot weaken security or historical access and cannot disable emergency security protections.

No automated external support service is introduced.

## 13. Update entitlement and release sequence

PATCH-058 remains authoritative for release identity, artifact signatures, security evidence and Human release approval.

Commercial update eligibility uses max_release_sequence. Every PATCH-059-aware releasable build intended for commercial update comparison must expose an immutable positive SATCO release_sequence inside governed release metadata bound by PATCH-058 release evidence.

A deployment may install/use a candidate sequence only when the release is independently valid under PATCH-058 and baseline_release_sequence <= candidate_release_sequence <= max_release_sequence. Both bounds are explicit signed positive integers; V1 has no null/unlimited update-right semantic.

Mutable image tags, filenames, semantic-version text and local install time are prohibited as update authority. IDS must freeze release-sequence extraction/verification and activation behavior when the currently installed release is outside the newly presented signed range.## 14. Sensitive administration and reauthentication

Entitlement install/replace, seat assign/release/retain and commercial recovery-sensitive actions require canonical administrator authority plus PATCH-058 recent-authentication/step-up assurance.

EDS-059 reuses PATCH-058 reauthentication; it does not create a second credential/challenge system. The exact recent-authentication window already frozen by IDS-058 is consumed as-is.

Entitlement replacement cannot bypass signature, revision, binding or time validation even with successful reauthentication.

## 15. API contract families

IDS shall define exact routes under the existing versioned API, covering:
- read bounded commercial entitlement/status;
- validate/activate signed entitlement;
- list seat capacity and bounded assignments;
- assign/release/retain seats;
- read package commercial decision/status;
- bounded support/update eligibility.

Mutation routes are admin-only, reauthenticated and CSRF-protected where cookie-carried browser credentials apply.

Responses never return private key material, password/session secrets or unnecessary raw entitlement signatures. Error mapping preserves tenant/resource anti-inference and distinguishes safe commercial reason codes only after canonical authorization.

## 16. Admin UX

Admin UX displays Organization/deployment binding status, entitlement/revision/digest prefix, ACTIVE/GRACE/EXPIRED/INVALID/TIME_UNTRUSTED, package rights, seat capacity/assigned/reserved/retained state, over-capacity remediation, support status and update eligibility.

UX cannot locally override backend decisions. Expiry/grace clocks shown to users are server-derived.

Entitlement upload requires explicit confirmation and displays the safe effect summary before activation: revision, packages, seat capacity, validity/grace and support/update bounds.

## 17. Audit contract

Commercial audit vocabulary must include entitlement_validation_failed, entitlement_activated, entitlement_rejected, rollback_detected, time_untrusted, seat_assigned, seat_reserved, seat_released, seat_retained, over_capacity_entered/resolved and commercial_operation_denied.

Events record Organization, safe deployment reference, actor when applicable, correlation ID, entitlement/revision/digest prefix, outcome, reason code and server time. Automated transitions use system attribution.

Raw entitlement bodies, full signatures, public/private key material and engineering content are excluded from ordinary audit.

Security-significant signature/rollback/time failures may additionally emit bounded PATCH-058 AuthSecurityEvent-compatible evidence without redefining authentication ownership.## 18. Production readiness and failure matrix

Production commercial profile requires SATCO_DEPLOYMENT_ID, verification trust configuration and a valid bound entitlement state.

Missing/malformed security-critical static trust/deployment configuration is startup-fatal.

A syntactically present but invalid/untrusted entitlement, runtime corruption, rollback detection or time-untrusted condition prevents commercial readiness for CONFIGURE/EXECUTE but the application may remain available in bounded safe mode for authorized historical read/export and remediation.

No production fallback to NonCommercialEntitlementAdapter/NOT_REQUIRED is allowed.

Development/test may use explicit synthetic fixtures only when SATCO_ENVIRONMENT is non-production. Such fixtures are never deployment/release evidence.

## 19. Persistence and concurrency requirements

IDS shall specify bounded tables for current commercial entitlement state, immutable activation history and seat assignments/retention state.

All rows are explicitly Organization/deployment scoped. Foreign keys bind seats to canonical memberships without transferring membership ownership.

Entitlement activation, seat assignment/release/retain, capacity checks, high-water update and trusted-time security transitions use database transactions and deterministic row/advisory locking. Process-local mutexes are prohibited as cross-process authority.

Commercial persistence does not duplicate Registry, Organization, User, membership, engineering facts or PATCH-058 release dossier content.

## 20. Migration and cutover

PATCH-059 migration adds commercial state without rewriting historical engineering/package facts.

Production cutover requires a valid initial signed entitlement bound to the deployment before commercial enforcement is enabled. The initial entitlement revision is positive and establishes the first high-water mark.

There is no automatic conversion of NOT_REQUIRED into PERMITTED. During cutover, absence of accepted entitlement means commercial CONFIGURE/EXECUTE is unavailable.

Rollback of application/schema must not permit entitlement-revision rollback or bypass enforcement. Exact expand/contract sequencing and downgrade prohibition belong to IDS.## 21. Deterministic qualification vectors

IDS/implementation qualification must include:
1. Ed25519/JCS golden valid vector and malformed/duplicate/unknown-field negatives;
2. unknown/revoked key and signature mutation;
3. Organization/deployment mismatch;
4. lower revision and conflicting equal revision;
5. all seven supported E/I/C combinations plus package removal;
6. ACTIVE boundary, GRACE boundaries and EXPIRED;
7. >30-day grace rejection;
8. clock rollback at 5 minutes and beyond 5 minutes;
9. seat assignment at capacity and concurrent race;
10. admin and engineer both consuming seats;
11. disabled membership remaining reserved;
12. capacity reduction entering deterministic OVER_CAPACITY block and retained-seat remediation;
13. GRACE continuity versus expansion denial;
14. historical read/export without current seat while canonical authorization remains valid;
15. tenant/role/resource denial cannot be overridden by entitlement;
16. release update below/at/above purchased sequence;
17. restore/recovery high-water mismatch;
18. reauthentication required for mutations;
19. safe audit/redaction and protected-not-found behavior;
20. production cannot fall back to NOT_REQUIRED;
21. frontend/backend status parity with backend authoritative.

## 22. Explicit exclusions

Billing/payment processing, subscription automation, usage metering, advanced licensing analytics, online license servers, SaaS orchestration, floating/concurrent-use seats, customer source forks, new Discipline Packages, enterprise federation and PATCH-060 deployment certification remain excluded.

## 23. IDS obligations

IDS-059 must freeze exact Pydantic/schema definitions, JCS implementation and golden bytes, Ed25519 verification calls, trust-store representation, SQL tables/constraints/indexes/locks, entitlement/seat services and repositories, route/request/response schemas, reason codes, retained-seat algorithm, release-sequence extraction/range enforcement, trusted-time persistence/recovery, migration graph, frontend components/state handling, audit integration, test fixtures and qualification harness.

## 24. Governance disposition

Independent EDS Review completed with Critical 0 / Major 0 / Minor 0.

On 2026-09-30, the Human Authority explicitly accepted EDS-059. This acceptance authorizes progression to a separately governed IDS-059 candidate only. It does not authorize migration, implementation, deployment, release, closure or PATCH-060.

Human authority remains controlling. AI remains advisory and non-authoritative.

**EDS-059: HUMAN ACCEPTED.**