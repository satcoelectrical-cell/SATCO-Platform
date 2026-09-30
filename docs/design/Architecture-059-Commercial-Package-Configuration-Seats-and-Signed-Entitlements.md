# Architecture-059 — Commercial Package Configuration, Seats & Signed Entitlements

**Date:** 2026-09-30
**Status:** HUMAN ACCEPTED
**Authority:** PATCH-059 Discovery and Architecture are Human accepted. This acceptance authorizes progression to a separately governed EDS-059 candidate; it does not accept or authorize IDS, migration, implementation, deployment, release, closure or PATCH-060 work.

## Purpose and invariants

PATCH-059 establishes Commercial V1 signed offline entitlement, package, seat, validity/grace, support/update and enforcement architecture for the supported dedicated single-customer deployment profile.

The architecture extends the accepted PATCH-051 entitlement seam. It does not create a second package registry, Organization authority, identity/membership owner, engineering authorization model or customer-specific source fork.

Commercial entitlement is restrictive only. It can deny or constrain commercial capability but can never grant authentication, Organization membership, role, resource access, package compatibility, engineering authority, Human acceptance or release approval.

Canonical engineering records survive commercial state changes. Expiry, package disabling or seat loss cannot erase accepted historical engineering information.

Human authority remains controlling. AI remains optional, advisory and non-authoritative.

## Commercial entitlement trust boundary

Commercial V1 uses a signed offline entitlement document. The document is immutable after issuance; commercial changes produce a successor entitlement with a higher revision.

The entitlement issuer uses asymmetric signing. Customer deployments contain verification trust material only. Commercial private signing authority is prohibited from ordinary application runtime, customer database, source repository and release artifacts.

Commercial entitlement signing authority is distinct from PATCH-058 release signing/release approval authority. A valid release signature does not issue a commercial entitlement, and a valid entitlement signature does not approve a software release.

The signed canonical payload binds at minimum entitlement schema/version, entitlement identity, issuer/key identity, Organization identity, trusted deployment identity, monotonic revision, package rights, seat capacity, validity/grace bounds, support/update rights and the bounded release/update constraint.

Unknown schema, unsupported algorithm, unknown/revoked key, malformed canonical payload, invalid signature or binding mismatch yields unavailable/invalid commercial state and fails closed for CONFIGURE and EXECUTE.

Exact algorithm, canonical serialization, key identifiers, rotation/revocation representation and custody mechanism are EDS/IDS decisions.## Organization and deployment binding

The entitlement binds exactly one canonical Organization identity and one trusted deployment identity.

The deployment identity is the existing validated operational identity represented by SATCO_DEPLOYMENT_ID; PATCH-059 does not introduce a competing deployment identity.

Organization identity is derived from canonical Organization state, never from hostname, UI selection, customer-provided free text or entitlement content alone.

An Organization or deployment mismatch cannot be administratively overridden by ordinary application roles. Replacement requires a correctly issued successor entitlement or a separately governed recovery procedure.

## Commercial package rights

Core remains the shared product foundation. Commercial package rights cover the supported Electrical, Instrumentation and Control & Automation package keys and their accepted combinations.

Entitlement package rights do not alter Registry membership, package descriptors, compatibility profiles or Organization/Project configuration. Effective executable package capability requires all of those existing predicates plus commercial entitlement.

No commercial package combination may enable a package/version that is not executable-supported by the current trusted Registry and accepted compatibility profile.

Package removal in a successor entitlement prevents new CONFIGURE and EXECUTE for that package after the applicable state transition, but historical interpretation remains governed separately.

## Enforcement composition and order

The existing PATCH-051 entitlement decision port remains the commercial seam. PATCH-059 replaces the non-commercial adapter with a server-authoritative commercial evaluator.

Evaluation remains after canonical data/resource authorization and accepted package configuration as required by PATCH-051, preserving protected-not-found and tenant anti-inference behavior.

Effective package operation is an intersection of current authentication/membership/role authority, owner/resource authorization, Registry standing, exact package compatibility, Organization/Project package configuration and commercial entitlement.

PERMITTED is never a permission grant. DENIED blocks commercial CONFIGURE/EXECUTE. UNAVAILABLE fails closed for CONFIGURE/EXECUTE with bounded safe status. Authorized HISTORICAL_READ remains separately evaluated and cannot mutate state.

Backend/API is authoritative. Frontend state is explanatory and must not become an enforcement authority.## Named-seat architecture

Commercial V1 uses named seats assigned explicitly to canonical enabled Organization memberships.

A seat is not a browser session, concurrent connection, Workspace membership, Project assignment, engineering role invocation or activity counter. One assigned user consumes one seat for that Organization regardless of Project/Workspace count.

Administrators and engineers who use the commercial application consume seats. V1 has no privileged-user seat exemption; this prevents an administrative role from becoming a licensing bypass.

A seat assignment never grants membership, role or engineering authorization. Assignment to a disabled/removed membership is non-executable.

Seat assignment/release and capacity changes are server-authoritative, attributable and concurrency-safe. Capacity enforcement linearizes against a durable Organization-bound entitlement/seat state so concurrent assignments cannot exceed the accepted capacity.

A lower successor seat capacity does not arbitrarily delete existing assignments. If existing assignments exceed the new capacity, the Organization enters a deterministic OVER_CAPACITY commercial state: no new assignments and no commercial expansion are allowed until Human administration returns assignments within capacity. Existing assigned users do not gain new rights from this state.

EDS must freeze whether disabled membership automatically releases a seat or leaves a reserved assignment, and the exact remediation UX.

## Validity and grace state machine

Commercial entitlement has server-derived effective states at minimum ACTIVE, GRACE, EXPIRED and INVALID_OR_UNAVAILABLE. OVER_CAPACITY is an orthogonal seat condition.

ACTIVE permits entitled CONFIGURE/EXECUTE subject to every other authority gate.

GRACE is continuity-only. Already configured, already entitled package execution by valid assigned users may continue for the bounded grace period. GRACE prohibits commercial expansion: no newly enabled package, new seat assignment, seat-capacity increase, new package configuration that expands commercial capability, or newly activated update right.

EXPIRED blocks commercial CONFIGURE and EXECUTE. INVALID_OR_UNAVAILABLE fails closed in the same operations.

HISTORICAL_READ/authorized export is not converted into execution by any state. Exact grace duration, allowed non-expanding administrative repairs and boundary-time behavior are EDS decisions.## Historical read and export

Historical access is an explicit compatibility/safety property, not a licensing bypass.

After expiry, package removal, seat loss or over-capacity, authorized users may read/export existing canonical records only when canonical tenant, membership, owner/resource, Evidence/Report/standards-rights and export authorization independently permit it.

Historical access never restores package mutation, rule execution that creates new durable facts, package configuration, deliverable transition authority or other commercial execution.

No entitlement transition deletes or rewrites canonical engineering records merely to enforce commercial status.

## Anti-rollback architecture

Every entitlement has a strictly increasing revision within its Organization+deployment binding. The runtime persists the highest accepted revision as server-authoritative durable anti-rollback state.

An entitlement below the accepted high-water revision is rejected even when its signature and dates are otherwise valid. Equal revision is accepted only when its canonical entitlement digest matches the already accepted revision; conflicting same-revision material is invalid.

High-water state updates and entitlement activation are transactional and concurrency-safe. A failed activation cannot partially advance commercial rights.

Backup/restore cannot silently lower the effective high-water revision. Restore reconciliation must compare restored state with separately governed recovery/deployment evidence or another accepted durable anchor before commercial CONFIGURE/EXECUTE resumes.

Exact persistence topology and recovery anchor belong to EDS/IDS and later PATCH-060 qualification. Ordinary administrators cannot reset anti-rollback state.

## Offline time architecture

Entitlement validity is evaluated in server-authoritative UTC. Client/browser clocks are never authority.

Because the system is offline, wall clock alone is insufficient. Runtime maintains a durable last-trusted-time/high-water observation associated with entitlement state. A material backward clock movement relative to that accepted observation produces a safe time-untrusted condition and blocks CONFIGURE/EXECUTE until the accepted recovery path resolves it.

Small operational clock skew may be tolerated only within an EDS-frozen bound. Grace cannot be extended by moving the clock backward.

The design claims no secure hardware clock and no online licensing service.## Support and update entitlement

Support status and update entitlement are separate commercial attributes.

Support expiry does not weaken authentication, security, tenant isolation, data integrity or historical access. It may change Human-visible support eligibility only.

Update entitlement controls commercial eligibility to install/use a later release; it does not determine whether that release is secure or approved. PATCH-058 immutable release identity, signature/trust evidence and Human release approval remain authoritative.

Architecture requires the update right to bind to immutable release metadata under SATCO control rather than mutable filenames, image tags or UI version strings. EDS must freeze the exact release sequence/date/channel attribute and comparison rule.

A commercially eligible update still requires all PATCH-058 release-security evidence and later PATCH-060 deployment qualification where applicable.

## Persistence ownership

PATCH-059 may introduce bounded commercial persistence for accepted entitlement state, entitlement revision/digest metadata, trusted-time observation, seat assignments and commercial audit.

This persistence does not own Organization, User, membership, role, Registry descriptor, Project package configuration, Workspace, engineering records or release-security evidence.

Raw private signing keys are never persisted by the deployment. Raw entitlement material is retained only if required by the accepted verification/audit contract and must be bounded/protected; normalized authoritative state must remain verifiable against the signed source.

Commercial state must use explicit Organization/deployment binding and database constraints/locking sufficient to prevent cross-tenant assignment and capacity races.

Exact tables, constraints, migration sequence and indexes are EDS/IDS decisions.

## Administration and security

Only canonical authorized administrators may install/replace entitlement material and administer seats. These operations require recent reauthentication using the accepted PATCH-058 sensitive-operation mechanism.

Entitlement administration cannot alter canonical membership/role or release approval.

Admin UX exposes bounded status: entitlement identity/digest prefix, Organization/deployment binding status, package rights, seat capacity/usage/over-capacity, validity/grace, support/update status, trust/signature status and safe remediation guidance.

Secrets, private keys and unnecessary raw signed payloads are not exposed through ordinary UI, logs or audit.## Audit and observability

Commercial events are attributable and bounded: entitlement install/accept/reject, revision transition, signature/trust failure category, rollback detection, clock rollback/time-untrusted transition, seat assignment/release, capacity/over-capacity transition, validity/grace/expiry transition and update eligibility decisions where operationally material.

Audit records identify actor when an actor exists, Organization, deployment-safe identity/reference, correlation, bounded entitlement/revision/digest identity, action/result and time. They do not duplicate engineering content or private signing material.

Automated expiry/time transitions are system-attributable, not falsely attributed to a Human.

## Failure behavior

Invalid/missing/untrusted commercial state does not erase data, weaken security or disclose protected resource existence.

For production commercial operation, entitlement material/configuration required to establish a verifiable bound commercial state is a readiness prerequisite. A structurally missing or unverifiable entitlement prevents commercial readiness; EDS must distinguish startup-fatal configuration defects from runtime loss/corruption that enters a bounded degraded/read-only-safe condition.

Runtime inability to establish trusted commercial state blocks CONFIGURE/EXECUTE while preserving independently authorized historical read/export.

No fallback to NOT_REQUIRED is permitted in the commercial production profile.

## Compatibility and migration

PATCH-059 must preserve existing PATCH-051/052 historical package provenance and configuration. Migration to commercial enforcement must not rewrite historical engineering facts or fabricate past seat/entitlement state.

The transition from NonCommercialEntitlementAdapter to commercial evaluation must be explicit and production-fail-closed. Development/test behavior may use separately explicit non-production fixtures but cannot become production evidence.

No customer-specific source fork is permitted.

## Qualification obligations

Qualification must cover signature/trust negatives, Organization/deployment mismatch, all supported E/I/C combinations, package removal, ACTIVE/GRACE/EXPIRED/INVALID transitions, named-seat capacity and concurrency, admin/engineer seat consumption, membership/role changes, over-capacity remediation, entitlement rollback/same-revision conflict, clock rollback/skew, backup/restore rollback, support/update eligibility, historical read/export preservation, tenant anti-inference, admin reauthentication/audit, backend/frontend consistency and migration/regression.

The accepted qualification must also prove that commercial PERMITTED cannot override any existing canonical authorization denial.## Explicit non-scope

Billing/payment processing, subscription automation, usage metering, advanced licensing analytics, online licensing services, SaaS orchestration, floating/concurrent-use seats, customer source forks, new Discipline Packages, enterprise federation and PATCH-060 deployment certification are excluded.

## EDS-deferred decisions

EDS must freeze at minimum:

- entitlement canonical schema/serialization and exact cryptographic algorithm;
- trust-store/key rotation/revocation contract;
- exact entitlement key/package/update fields and bounds;
- seat assignment lifecycle including disabled-membership reservation/release;
- exact grace duration and permitted continuity/repair operation matrix;
- anti-rollback tables/locks/recovery anchor and same-revision handling details;
- trusted-time/skew thresholds and recovery;
- exact update-right immutable release attribute/comparison;
- startup/readiness/runtime degraded-state matrix;
- audit event vocabulary/bounds/retention references;
- admin API/UX contracts and reauthentication window reuse;
- migration/cutover contract and deterministic qualification vectors.

## Governance disposition

Independent Architecture Review completed with Critical 0 / Major 0 / Minor 0.

On 2026-09-30, the Human Authority explicitly accepted Architecture-059. This acceptance authorizes progression to a separately governed EDS-059 candidate only. It does not accept EDS/IDS or authorize migration, implementation, deployment, release, closure or PATCH-060.

PATCH-060 remains NOT STARTED / NOT AUTHORIZED.

Human authority remains controlling. AI remains advisory and non-authoritative.

**ARCHITECTURE-059: HUMAN ACCEPTED.**
