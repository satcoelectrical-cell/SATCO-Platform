# Post-PATCH-058 Commercial Package, Seats & Signed Entitlements Capability Discovery

Status: DISCOVERY ACCEPTED / COMPLETE — HUMAN ACCEPTED

Date: 2026-09-30

## Purpose and inherited facts

PATCH-059 must turn the accepted PATCH-051 non-commercial entitlement seam into a commercial signed-offline entitlement capability without creating a second package registry, Organization authority, customer source fork, or parallel engineering authorization model.

The accepted Core already defines an entitlement request seam containing trusted Organization identity, trusted deployment identity, package key, entitlement key and CONFIGURE / EXECUTE / HISTORICAL_READ operations. Its current adapter is explicitly non-commercial and returns NOT_REQUIRED.

The package model already owns immutable descriptors, Registry release identity, executable-supported versus historical-read-only standing, Organization package configuration, exact Project package configuration and configuration audit. The operational profile already provides SATCO_DEPLOYMENT_ID; PATCH-059 should consume it rather than invent a competing deployment identity.

Canonical Organization membership remains the identity/authorization source. Workspace membership, Project assignment and package configuration are not commercial seat ownership. PATCH-058 supplies immutable release identity and signed release-security evidence; entitlement may constrain commercial update rights but cannot redefine or approve a release.

## Required capability and trust direction

A valid entitlement must bind schema/version, unique entitlement identity, issuer/key identity, Organization, deployment, enabled commercial packages, seat capacity/assignments, validity/grace, support/update rights, signature, and a monotonic revision or equivalent rollback-resistant value.

Recommended Architecture candidate: asymmetric offline signatures. The dedicated deployment receives verification material only; the commercial private signing key must not be present in customer deployment or ordinary runtime. Verification covers canonical entitlement bytes and fails closed on unknown schema/key/algorithm, malformed payload, binding mismatch or invalid signature.

Key rotation/revocation and the concrete algorithm/key-storage product remain later Architecture/EDS decisions.## Anti-rollback and seats

A previously valid signed entitlement must not be able to re-enable removed packages, seats or update rights. Recommended candidate: a strictly monotonic Organization+deployment-bound entitlement revision with a server-authoritative durable high-water mark. Lower revisions fail closed for CONFIGURE and EXECUTE even when cryptographically valid.

Backup/restore must not silently reset the high-water mark. Exact durable storage, locking, restore reconciliation and break-glass behavior remain Architecture/EDS decisions and PATCH-060 must later exercise the accepted recovery contract.

Recommended V1 seat model: named seats explicitly assigned to enabled Organization memberships. One assigned person consumes one Organization seat regardless of Project/Workspace count. Seats are not inferred from sessions, activity, Workspace membership or Project assignment.

Membership disable/removal makes the seat non-executable. Whether the assignment is automatically released or remains reserved is deferred. Administrator seat treatment is also an explicit later Human decision; Discovery does not silently exempt privileged users.

Capacity changes must be concurrency-safe and auditable. Reducing capacity below assignments must not arbitrarily delete assignments; later design must define deterministic over-capacity behavior.

## Enforcement composition

Commercial entitlement is an additional restrictive predicate, never a permission grant. Effective package permission remains the intersection of canonical authentication/membership/role authority, owner/resource authorization, Registry standing and compatibility, accepted Organization/Project package configuration, and PATCH-059 entitlement.

A PERMITTED entitlement cannot make an otherwise-forbidden action authorized. Unknown/unavailable entitlement state fails closed for commercial CONFIGURE and EXECUTE. PATCH-059 should wire the existing PATCH-051 entitlement seam rather than create a competing package-authorization subsystem.

## Expiry, grace and historical access

The frozen product promise requires validity and grace. Conceptual states may include ACTIVE, GRACE, EXPIRED and INVALID/UNAVAILABLE, but exact vocabulary is deferred.

ACTIVE may permit purchased CONFIGURE/EXECUTE subject to all other gates. During GRACE, Discovery recommends preserving bounded already-entitled engineering continuity while blocking commercial expansion such as adding packages, increasing seats or activating update rights; exact grace duration and operation matrix require later Human acceptance.

After EXPIRED, new commercial CONFIGURE/EXECUTE fails closed. Expiry never erases canonical engineering records.HISTORICAL_READ is distinct from CONFIGURE and EXECUTE. Package disabling, seat loss, update-right expiry or entitlement expiry must preserve authorized read/export of existing canonical records according to owner authorization and retention/export rules.

Historical preservation never bypasses tenant, membership, resource, Evidence, Report, standards-rights or other canonical authorization; it cannot expose data merely because an entitlement once existed and cannot mutate engineering facts.

## Support/update and offline time

Support and update entitlements are commercial rights, not PATCH-058 release-security approval. PATCH-058 remains authoritative for valid release identity/signature. PATCH-059 may determine whether the deployment is commercially entitled to install/use a later supported release.

Recommended candidate: encode update rights against an immutable release-compatible attribute rather than mutable filenames/UI versions. Exact encoding must resist rollback and clock manipulation.

Because verification is offline, local wall-clock time alone is insufficient anti-rollback evidence. Later design must define server-authoritative UTC handling, bounded skew, trusted-time/last-seen-time behavior and restore reconciliation. No online licensing service or secure-hardware clock is assumed.

## Administration, audit and failure posture

Only appropriately authorized administrators may install/replace entitlement material or manage seats. Sensitive operations should reuse PATCH-058 reauthentication/session-security mechanisms where appropriate.

Admin UX should expose bounded non-secret binding, package, seat, validity/grace, support/update and trust status. Install/replacement/rejection, seat changes, over-capacity, expiry/grace transitions and relevant enforcement failures require bounded attributable audit without indiscriminately storing raw entitlement/signature material.

Malformed, unsigned, untrusted, Organization-mismatched, deployment-mismatched, rolled-back or unavailable entitlement state fails closed for commercial CONFIGURE/EXECUTE while preserving authorized historical read/export. Startup-fatal versus runtime-degraded handling remains a later decision.

## Required qualification matrix

Later qualification must cover all supported E/I/C combinations; package absent/disabled/expired/grace; seat below/at/over capacity and concurrency; membership/role changes; Organization/deployment mismatch; malformed/unknown-key/invalid-signature input; entitlement rollback and restore rollback; clock skew/rollback; update/support behavior; historical access after disable/seat loss/expiry; tenant-negative behavior; admin reauthentication/audit; and frontend/backend consistency with backend authority.## Explicit non-scope

Billing, payment processing, subscription automation, usage metering, advanced licensing analytics, online license servers, SaaS orchestration, new Discipline Packages, customer source forks, enterprise federation and PATCH-060 deployment certification remain outside PATCH-059.

## Discovery decisions proposed for Human acceptance

1. Reuse the PATCH-051 entitlement seam rather than create a parallel gate.
2. Use signed offline asymmetric entitlements with verification-only material in the dedicated deployment.
3. Bind entitlement to canonical Organization and trusted deployment identity.
4. Use explicit named Organization-member seats rather than concurrent-use/session/workspace seats.
5. Compose entitlement as a restrictive intersection with existing authority.
6. Use monotonic entitlement revision plus durable rollback detection.
7. Preserve authorized historical read/export after disabling/expiry without preserving CONFIGURE/EXECUTE.
8. Keep support/update rights distinct from PATCH-058 release approval.
9. Treat clock rollback and backup/restore rollback as explicit security cases.
10. Keep backend/server state authoritative; frontend is explanatory/admin UX.

The exact cryptographic algorithm, key lifecycle, administrator seat treatment, grace duration/operation matrix, durable anti-rollback storage, trusted-time algorithm, update-right encoding, startup behavior and persistence schema are deferred to separately authorized Architecture/EDS decisions.

## Governance disposition

PATCH-059 remains REGISTERED / OPEN — DISCOVERY AUTHORIZED. This Discovery candidate grants no Architecture, ADR, EDS, IDS, migration, implementation, deployment, release, closure or PATCH-060 authority.

Human authority remains controlling. AI remains advisory and non-authoritative.

## Human Discovery Acceptance

On 2026-09-30, the Human Authority explicitly accepted this PATCH-059 Discovery direction. This acceptance closes Discovery only and authorizes progression to a separately governed Architecture-059 candidate. It does not itself accept any future Architecture, ADR, EDS, IDS, migration or implementation.

Human authority remains controlling. AI remains advisory and non-authoritative.

**PATCH-059 DISCOVERY: ACCEPTED / COMPLETE.**
