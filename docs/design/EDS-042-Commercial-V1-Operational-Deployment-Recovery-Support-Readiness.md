# EDS-042 — Commercial V1 Operational Deployment, Recovery & Support Readiness

Status: ACCEPTED / COMPLETE. Initial Independent Review: FAIL (historical).
Focused Independent Re-review: PASS.

Authority: Human PATCH-042 Architecture Acceptance PASS; EDS-042 Design
Authority GRANTED. IDS-042, Implementation Plan, and implementation authority
are NOT GRANTED.

## 1. Purpose, scope, and non-goals

This EDS defines the product and engineering behavior of the single supported
Commercial V1 operating profile: a SATCO-managed, dedicated, single-customer
deployment of one fixed all-in SATCO product and codebase.

It governs production packaging, the TLS edge, private service networking,
configuration and secrets, release identity, migration and upgrade operation,
backup and recovery, health, bounded telemetry, operator support, incident
response, and production-security validation. It also governs a private
object-storage operational foundation needed by the expected PATCH-043.

PATCH-042 does not create Supporting File Asset identity, upload/download
authorization, Evidence/file relationships, quarantine or user-file lifecycle,
file provenance, or any other supporting-file domain behavior. Those remain
subject to PATCH-043. It does not provide customer-managed/on-premises
deployment, Kubernetes, high availability, multi-region operation, module
entitlements, billing, CRM, Business Network, finance, contract automation,
Company-OS, generic EDMS behavior, or Modular Platform Architecture.

Commercial V1 Release Certification remains a later cross-PATCH
milestone/review. PATCH-042 produces evidence for that milestone but cannot
declare the product commercially certified.

## 2. Deployment profile

The sole supported profile is logically:

```text
Internet
  -> TLS edge / reverse proxy
       -> versioned frontend static assets
       -> same-origin API proxy
            -> private backend
                 -> private PostgreSQL
                 -> private object-storage foundation

private monitoring/alert integration
private one-shot migration task
encrypted off-host backup target
```

Only the edge is publicly reachable. Dedicated deployment does not weaken
application-level authentication, Organization scope, authorization, protected
outcomes, or Human authority.

| Component | Exposure | Persistent state | Dependencies | Startup/readiness role | Owner |
|---|---|---|---|---|---|
| TLS edge/reverse proxy | Public HTTPS; optional HTTP redirect only | Certificates and bounded edge configuration | Frontend assets, backend route, trusted configuration | Starts only with valid edge configuration; readiness covers certificate, frontend, and API routing | SATCO operator |
| Frontend | Served only through edge | Immutable versioned assets, not business state | Release manifest | Asset digest must match the release; edge availability is required | SATCO operator |
| Backend | Private network only | No authoritative local filesystem state | Runtime configuration, PostgreSQL, mandatory object-storage foundation | Static validation is startup-fatal; downstream checks govern readiness | SATCO operator |
| Migration task | Private, one-shot, non-serving | Migration evidence only | Schema-owner credential, release manifest, backup, database | Must succeed before the corresponding backend becomes ready | Authorized deployment operator |
| PostgreSQL | Private network only | Canonical structured business state | Durable volume, schema-owner/runtime role separation | Connectivity, expected head, roles, and persistence guards are readiness requirements | SATCO operator; application remains domain authority |
| Object storage | Private network only | Encrypted opaque operational objects; no business authority | Durable storage, credentials, recovery configuration | Mandatory configuration is startup-fatal; availability is a readiness dependency | SATCO operator |
| Monitoring/alerting | Private or outbound-only integration | Operational telemetry and incident notifications only | Safe metrics/log signals and notification destination | Failure creates operational degradation/alert; it creates no business authority | SATCO operations |
| Off-host backup target | Private/outbound-only | Encrypted recovery material and manifests | Independent failure domain and encryption authority | Configuration is startup/preflight-fatal; freshness is continuously monitored | Authorized recovery operator |

No component may infer Customer or Organization authority from deployment
identity. No local container filesystem may become authoritative persistent
state.

## 3. Environment modes

The supported modes are:

- **development** — local convenience, debug tooling, bind mounts, and exposed
  service ports may be used. It is never production evidence.
- **test** — isolated deterministic resources and synthetic test data only.
  Test credentials and databases must be unmistakably non-production.
- **production** — explicitly declared through a required environment-mode
  setting. Production is never inferred from hostname, missing configuration,
  convenience defaults, or an image tag.

Production requires TLS edge termination, trusted host/origin restrictions,
private backend/database/object storage, immutable release identity, fail-closed
secret validation, schema/runtime role separation, backup configuration,
bounded logs, monitoring/alerts, operator identity controls, production debug
disabled, and validated runbooks.

An artifact may be technically identical across environments, but production
behavior is selected only by explicit validated configuration. A production
declaration with any mandatory safeguard absent must fail closed.

## 4. Production configuration contract

IDS-042 shall map these logical settings to exact names and schemas.

| Category | Production rule | Secret | Validation and failure | Redaction |
|---|---|---:|---|---|
| Environment identity | Required; exactly the production mode and deployment identity | No | Invalid/missing is startup-fatal | Safe bounded value |
| Release identity | Required immutable release manifest reference | No | Missing, malformed, or artifact mismatch is startup-fatal | Safe release label/digest prefix only on protected diagnostics |
| Public URL | Required canonical HTTPS origin | No | Non-HTTPS or malformed is startup-fatal | Safe |
| Trusted hosts | Required explicit non-wildcard set | No | Empty, wildcard, or URL inconsistency is startup-fatal | Safe category; full list protected |
| Allowed origins | Required exact same-origin policy unless explicitly enumerated | No | Wildcard/invalid origin is startup-fatal | Safe category; full list protected |
| JWT/signing secret | Required, high entropy, unique, not a known default | Yes | Missing/weak/default is startup-fatal | Never emitted |
| Bootstrap enablement | Required explicit boolean; disabled after bounded use | No | Ambiguous value is startup-fatal | Safe state only |
| Bootstrap secret | Required only while bootstrap is enabled; high entropy and distinct | Yes | Enabled with absent/weak/default secret is startup-fatal | Never emitted |
| Runtime DB credential | Required restricted role | Yes | Missing/malformed or same authority as migration role is startup-fatal; connection failure affects readiness | Never emit URL/password |
| Migration DB credential | Required only for migration/preflight processes and unavailable to backend runtime | Yes | Missing for deployment is preflight-fatal; role collapse is fatal | Never emitted |
| Expected Alembic head | Required and bound to release identity | No | Missing/malformed is startup-fatal; actual mismatch fails readiness/deployment | Protected diagnostic only |
| Persistence/authority guards | Required explicit guard set/version | No | Missing/unsupported setting is startup-fatal; actual guard drift fails readiness | Safe category only |
| AI enabled flag | Required explicit boolean | No | Invalid value is startup-fatal | Safe |
| AI provider settings | Required only when AI is enabled | API key and provider credential are secret | Enabled with incomplete configuration is startup-fatal; provider outage is an optional-capability degradation, not core readiness failure | Never emit prompts, responses, keys, or endpoint credentials |
| Object-storage endpoint/namespace | Required private target and dedicated namespace; backend receives no data-plane credential | Separate non-content health credential/reference may be secret | Missing/unsafe configuration, a backend data-plane grant, or collapsed operational principals is startup-fatal; non-content availability failure fails readiness | Namespace/endpoint/credential details protected |
| Backup target/encryption | Required independent target, encryption key reference, retention policy | Credentials/key material yes | Missing/unsafe configuration is deployment/startup-fatal; freshness failure alerts and may remove operational readiness | Never emit credentials or keys |
| Logging | Required structured format, level allow-list, bounds, sink, and redaction policy | Sink credential may be secret | Invalid/unsafe policy is startup-fatal | Credentials/content never emitted |
| Support/operator | Required identity provider, role mapping, session/elevation policy, and incident destination | Authentication credentials secret | Missing/shared/unsafe configuration is startup-fatal for support interfaces | Identity is attributable but protected |
| TLS/edge | Required certificate/key references, redirect policy, and edge identity | Private key secret | Invalid/missing/expired material prevents public serving | Private key never emitted |

Configuration parsing must reject unknown security-critical values rather than
silently substituting production defaults. The effective configuration may be
reported only as bounded categories such as configured/not-configured,
enabled/disabled, and valid/invalid.

Bootstrap availability is the conjunction of configuration enablement, a valid
bootstrap credential, every PATCH-041 application eligibility rule, and the
accepted Organization/admin safety rules. Configuration enablement is never
sufficient by itself and conveys no Organization or business authority.

## 5. Startup, liveness, and readiness matrix

| Condition | Startup | Liveness | Readiness | Customer traffic |
|---|---|---|---|---|
| Weak/default signing secret | Refuse start | Not applicable | Not ready | Prohibited |
| Missing release/environment identity | Refuse start | Not applicable | Not ready | Prohibited |
| Invalid host/origin/public URL | Refuse start | Not applicable | Not ready | Prohibited |
| Runtime and migration authority collapse | Refuse start/deployment | Not applicable | Not ready | Prohibited |
| Required guard configuration absent | Refuse start | Not applicable | Not ready | Prohibited |
| Bootstrap enabled without valid secret | Refuse start | Not applicable | Not ready | Prohibited |
| AI enabled with incomplete configuration | Refuse start | Not applicable | Not ready | Prohibited until corrected |
| AI disabled | Start | Alive | AI excluded from core readiness | Permitted |
| Optional enabled AI provider unavailable | Continue | Alive | Core ready; AI capability degraded/closed | Core traffic permitted |
| Mandatory object/backup configuration absent | Refuse start/deployment | Not applicable | Not ready | Prohibited |
| Database temporarily unavailable | Continue retrying | Alive | Not ready | Prohibited through edge routing |
| Object storage unavailable | Continue retrying | Alive | Not ready | Prohibited while it is a mandatory deployment dependency |
| Schema head/guard mismatch | Process may remain alive for diagnostics | Alive | Not ready | Prohibited |
| Monitoring delivery temporarily unavailable | Continue | Alive | Operationally degraded during a Human-authorized manual fallback of at most four hours | Reads/writes permitted only during that recorded fallback while all other guards pass; at expiry, writes are blocked and reads require safely enforced read-only mode |
| Backup target temporarily unavailable, verified recovery freshness <= 4 hours | Continue | Alive | Ready only if all other readiness conditions pass; degradation is alerted | Normal reads/writes may continue |
| Verified recovery freshness > 4 hours | Continue for protected diagnosis | Alive | `RECOVERY_PROTECTION_DEGRADED`; not write-ready | New governed writes blocked; reads only through safely enforced read-only mode, otherwise all customer traffic blocked |

Liveness proves only that the process and event loop can respond. It must not
query downstream dependencies. Readiness is fail-closed for request-path and
authority-critical dependencies. Public health responses reveal only generic
alive/ready state; detailed component state is operator-protected.

This closes AR042-MIN-03.

## 6. Secret lifecycle

Production secrets are provisioned through a SATCO-approved secret delivery
boundary, injected at runtime or one-shot task execution, and never baked into
images, frontend assets, source control, release manifests, logs, Audit details,
diagnostic bundles, or support tickets.

Every secret has an owner, purpose, deployment scope, creation time, rotation
policy, revocation path, and reference identifier that does not reveal secret
material. Runtime, migration, backup-encryption, object-storage, TLS, bootstrap,
operator, and optional AI credentials remain separated.

Rotation must support overlap only when the relevant protocol requires it,
record the operator and change evidence, verify the new credential, revoke the
old credential, and detect stale consumers. Revocation is immediate for
suspected compromise.

Bootstrap is disabled by default after first-customer initialization.
Re-enablement requires an attributable elevated operator, explicit incident or
maintenance authorization, a new single-purpose secret, a bounded time window,
and automatic/manual revocation verified at completion.

An operator may enable, disable, or rotate only the bootstrap configuration and
credential. Re-enablement does not authorize Organization creation, override
PATCH-041 application eligibility, or permit a second customer Organization.
Each attempt must independently satisfy the PATCH-041 eligibility and accepted
Organization/admin safety checks. An ineligible attempt is denied with a
bounded, non-disclosing Audit/operational event even when configuration and
credential are valid. Operator configuration authority never becomes
Organization or business authority.

Shared operator credentials and plaintext production-secret files are
prohibited. Secret-access failure is non-disclosing and must not fall back to a
default.

## 7. Edge, TLS, and network contract

The edge is the only public network surface. HTTPS is mandatory. If HTTP is
exposed, it performs only a bounded redirect to the canonical HTTPS origin and
serves no application content.

The edge serves immutable versioned frontend assets and proxies API traffic
same-origin. It must preserve safe correlation data while stripping or
rejecting untrusted forwarding/host headers according to an explicit trust
boundary.

Backend, migration task, PostgreSQL, object storage, monitoring collectors, and
backup control endpoints are private. Database and object-storage ports must
not be host/public exposed in the production profile.

Certificates require automated or governed renewal, expiry monitoring, and
alerts sufficiently early to avoid expiry. Invalid or expired TLS prevents
serving. Production debug, stack traces, development servers, live source bind
mounts, directory listing, and public internal API documentation are disabled
unless a later protected operator contract explicitly permits documentation.

The edge applies testable security headers, bounded request/body/time limits,
and rate-limiting classes. Exact header values and limits belong to IDS-042.

## 8. Database role and migration contract

ADR-012 remains authoritative. Alembic is the exclusive schema authority.

The migration task uses a short-lived schema-owner credential unavailable to
the backend runtime. The backend uses the restricted runtime role. Production
preflight verifies the release-declared current/target head, a single linear
repository head, database starting head, role separation, privilege/ownership
matrix, required extensions, capacity, connectivity, and compatibility.

The sequence is:

```text
preflight -> verified recovery set -> write drain/stop
-> one-shot schema-owner migration -> head/guard verification
-> backend deployment -> readiness/smoke -> reopen
```

Migration failure leaves the backend not ready and customer traffic closed.
The failed task cannot be retried blindly; an operator must inspect bounded
evidence and choose a documented retry, compatible application rollback, or
restore route.

`alembic stamp` is prohibited as failure recovery. Production downgrade is not
assumed safe. Schema reversal uses an explicitly validated downgrade only when
the release contract permits it; otherwise recovery uses the verified
pre-upgrade recovery set and compatible application artifact.

PATCH-042 does not modify or reinterpret application-domain migration
semantics. IDS-042 must define exact preflight/guard inputs, commands, and
evidence formats.

## 9. Release identity and supply-chain contract

Every deployable release has one immutable manifest containing:

- product release tag/version;
- exact Git commit;
- backend artifact/image digest;
- frontend asset-set digest;
- expected Alembic head;
- configuration-schema version;
- migration artifact digest;
- dependency manifest/SBOM identity;
- dependency and container scan evidence identifiers;
- build provenance and creation time.

Production must deploy artifacts by immutable digest, not mutable tag alone.
Frontend and backend artifacts must match the same approved release manifest.
The running release, schema, and configuration schema must reconcile before
readiness.

An artifact is deployable only when built reproducibly from the declared commit
in an approved clean build context, its digests and provenance verify, required
tests pass, scans complete, Critical vulnerabilities are absent, and each High
finding is resolved or covered by an active exception approved by an
attributable Human Security Approver. AI and scanning tools may detect, classify,
and report findings, but cannot approve an exception.

Critical vulnerabilities are non-waivable for a deployable Commercial V1
artifact unless later explicit governance changes this policy. A High finding
blocks deployability unless its exception records the exact finding
ID/CVE/advisory identity where applicable, affected artifact and immutable
digest, severity and source, rationale, compensating controls, bounded scope,
Human approver identity, approval timestamp, expiry, required retest or
revalidation condition, status, and eventual revocation or closure. Exceptions
cannot be open-ended or inherited by a different artifact digest. An expired,
revoked, unresolved, or failed-revalidation exception makes the artifact
non-deployable for a new deployment or upgrade. If that artifact is already
active, expiration or revocation creates an operational/security incident and
mandatory Human review; it is never silently accepted.

Exact build tools, signing/attestation formats, scanners, SBOM format, and
vulnerability-policy representation belong to IDS-042. This addresses
AR042-OBS-02.

## 10. Object-storage operational foundation

PATCH-042 provides one private, deployment-scoped namespace or bucket for
future supporting-file use. It requires durable storage, encryption in transit
and at rest, least-privilege credentials, network isolation, capacity
monitoring, health/readiness, backup participation, and recovery-set
participation.

The PATCH-042 backend application principal has no object data-plane authority:
no customer-object read, list, write, delete, presigned/customer-object URL
generation, or customer-object metadata retrieval. It receives no
future-compatible data-plane credential. Any readiness check uses a separate,
bounded monitoring/health mechanism that proves service and configured-namespace
availability without reading, listing, enumerating, or exposing customer
objects.

Provisioning, backup/recovery, monitoring/health, and scanner-foundation
principals are conceptually separate, least-privileged, and unavailable to the
backend runtime. No principal receives broader authority for convenience.
PATCH-043 alone may explicitly introduce future application data-plane
permission. Objects and keys have no Customer, Evidence, provenance,
acceptance, or authorization meaning in PATCH-042.

A private malware-scanner service or invocation hook may be provisioned only as
an operational dependency with signature/engine health. PATCH-042 cannot decide
whether a user file is accepted, quarantined, downloadable, evidence, or
technically valid. Invocation, semantic result mapping, quarantine state, and
file lifecycle belong to PATCH-043.

## 11. Backup contract

A recovery point must be created often enough that the latest successful
recoverable state is no more than four hours old. Backups are encrypted before
or during transfer to an off-host target in an independent failure domain.
Application runtime credentials cannot create, delete, restore, or decrypt
backups.

Before PATCH-043, each recovery set includes PostgreSQL, the release/config
identities, and an explicit object component marked not-applicable or verified
empty. PATCH-043 may add governed object inventories without changing the
recovery-set abstraction.

Minimum retention is:

- every sealed recovery set for at least seven rolling days;
- at least one verified daily recovery set for thirty days;
- each pre-upgrade recovery set for thirty days and until the upgrade is
  explicitly accepted, whichever is longer.

Each backup records safe inventory metadata, encrypted artifact identity,
creation/finish time, source deployment, release, schema head, sizes, integrity
digests, encryption-key reference (never key material), status, and operator or
automation identity. Integrity is checked at creation and by scheduled isolated
verification. Failure or age approaching the RPO creates an alert and incident
as defined below.

Verified recovery freshness at or below four hours permits normal read/write
service only when every other readiness condition passes. Once it exceeds four
hours, the deployment enters `RECOVERY_PROTECTION_DEGRADED`, creates a mandatory
operational incident/alert, and blocks all new governed writes. Read-only
customer access may continue only when database/application integrity is
healthy, schema/release guards pass, no other readiness blocker exists, and
read-only enforcement is technically verified. If safe read-only enforcement
is unavailable, readiness fails and all customer traffic is blocked. Human
Operations cannot waive the RPO threshold or reopen writes. Writes resume only
after a newly created and verified recovery point restores freshness to at most
four hours, all required health and guards pass, and Human Operations records
restoration confirmation. Public health reports only generic not-ready or
degraded state; protected diagnostics may expose the bounded state and freshness
category but not recovery identities or protected details.

RPO <= 4 hours and RTO <= 8 hours within the support window assume bounded
Commercial V1 data volume, available off-host backups, documented runbooks,
reachable authorized operators, replacement infrastructure capacity, and no
external catastrophe beyond the dedicated deployment recovery design.

## 12. Consistent recovery-set contract

A recovery set is the only promotable recovery unit. It has:

- globally unique recovery-set identity;
- source deployment and creation interval;
- database backup identity, cutoff/time, digest, and status;
- object-storage cutoff and inventory reference/digest when applicable;
- explicit object component state: not-applicable, verified-empty, or present;
- release identity and artifact digests;
- Alembic head and configuration-schema version;
- encryption-key references;
- integrity metadata;
- lifecycle: building, sealed, verified, failed, or superseded;
- verification identity/time and immutable verification result.

Only sealed and verified recovery sets may be proposed for production
promotion. Independently selected database and object backups are not a
recovery set.

Before PATCH-043 the object component must be not-applicable or verified empty.
After PATCH-043, its future authorized reconciliation contract must prove that
database metadata and the bounded object inventory belong to the same recovery
cutoff. Missing required objects, digest/inventory mismatch, unaccounted
pre-cutoff objects, or inability to establish the cutoff is irreconcilable.
Newer-than-cutoff objects are excluded from the restored promotion candidate
and retained only in isolated recovery handling; they cannot silently enter the
promoted namespace.

An irreconcilable set remains isolated, is marked failed, generates an incident,
and cannot serve customer traffic. No operator override may relabel it verified
without a separately governed repair that produces a new verification record.

This closes AR042-MIN-01 without defining file-domain semantics.

## 13. Restore and recovery contract

Restore always begins in an isolated, non-serving environment. The operator
selects one sealed recovery set, verifies authorization and manifests, restores
all applicable components, and validates artifact digests, schema head,
persistence guards, database integrity, object inventory state, configuration
schema, application readiness, and bounded smoke checks.

Production promotion requires an attributable Human recovery operator, incident
or maintenance record, successful verification, confirmation of the recovery
point and expected data-loss window, and a recorded promotion decision.
Promotion replaces or isolates the failed environment; it never merges
unverified live state.

Destructive recovery requires explicit confirmation of target deployment,
pre-action preservation where feasible, two-person or equivalent independent
authorization selected by IDS-042, and a rollback/abort point. Recovery actions
and evidence are recorded without customer content or secrets.

Customer communication is owned by the designated Human incident lead under
the support process. This EDS does not create contractual notice times or an
SLA. Recovery is never an unattended autonomous production mutation.

## 14. Upgrade and rollback contract

The normative upgrade sequence is:

```text
Human maintenance authorization
-> release/config/preflight verification
-> sealed and verified pre-upgrade recovery set
-> write drain or application stop
-> one-shot migration
-> schema/role/guard verification
-> deploy matching immutable release
-> readiness and bounded smoke validation
-> Human reopen decision
```

At every gate, failure leaves traffic closed or the prior known-good release
serving only when schema compatibility is proven.

A compatible application rollback redeploys the previous immutable artifact
without reversing schema only when its release manifest declares compatibility
with the current head. An incompatible schema requires restoration from the
pre-upgrade recovery set. Partial frontend/backend deployment is a release
mismatch and cannot become ready.

Upgrade evidence contains release identities, preflight result, recovery-set
identity, migration output summary, schema/guard result, readiness/smoke result,
operator identities, timestamps, and final disposition. It contains no secrets
or engineering content.

## 15. Health contract

Liveness reports only a generic alive state and does not inspect dependencies.
Public readiness reports only ready/not-ready. Detailed component health is
available solely through an authenticated operator surface.

Readiness verifies:

- validated production configuration;
- database connectivity;
- exact release-declared Alembic head;
- runtime/schema-owner separation and required persistence guards;
- a separately bounded, non-content object-storage health assertion proving
  service/configured-namespace availability without backend object data-plane
  authority or customer-object enumeration;
- frontend/backend release match;
- required request-path edge behavior.

Safe operator detail may contain categorical component name, state, safe reason
code, observation time, and release/config reference. It must not expose
credentials, endpoints containing credentials, database names when
unnecessary, Organization/customer identity, schema internals beyond the
approved head, stack traces, file names, object keys, or engineering content.
The protected surface may report `RECOVERY_PROTECTION_DEGRADED` and monitoring-
fallback categories; the public surface remains only ready/not-ready and never
reveals recovery age, incident identity, or the dependency that failed.

## 16. Logging contract

Production logs are structured, bounded, timestamped, and redacted. Permitted
fields are severity, safe event category/code, request/correlation ID, release
ID, deployment-local component, bounded outcome/status, duration, and
attributable operator identity where operationally required.

Tokens, passwords, secrets, cookies, authorization headers, raw database URLs,
TLS/backup/object credentials, bootstrap material, engineering text, file
contents, object keys, unnecessary protected identifiers, AI prompts/responses
containing customer content, stack traces exposed to customers, and arbitrary
request/response bodies are prohibited.

Each field has length/cardinality bounds. Unknown objects are not serialized
wholesale. Redaction failure drops the unsafe field or event and emits a safe
redaction-failure counter; it never falls back to plaintext logging. Log sink
failure must not leak content or silently block the application indefinitely.

Retention, access, transport security, and deletion are governed operational
settings defined exactly by IDS-042.

## 17. Monitoring and alerting contract

Mandatory signals cover edge/frontend/API availability, API error and latency
classes, database connectivity and capacity, host/container CPU/memory/disk,
object-storage health/capacity, backup age/failure, TLS expiry, schema/release
mismatch, readiness failure, migration result, and monitoring pipeline health.

Alert classes are:

- **P1** — active unavailability, confirmed security compromise, irreconcilable
  restore, or unrecoverable authority-boundary failure;
- **P2** — imminent RPO/TLS/capacity risk, repeated readiness failure, failed
  upgrade, or material security degradation;
- **P3** — bounded degradation requiring scheduled operator correction;
- **P4** — informational maintenance or trend requiring review.

Every alert has a Human owner, deployment, safe event code, detection time,
acknowledgement/disposition, and incident link where applicable. Customer
content and unbounded labels are prohibited. Full APM, SIEM, distributed
tracing, and autonomous remediation are deferred.

Loss of automated monitoring creates an incident/operational-degradation record
and does not automatically authorize continued operation. An attributable Human
Operations authority may approve manual fallback for at most four hours. During
that window, evidence must record at least hourly checks of edge/frontend
availability, backend readiness, database state/capacity, disk/storage capacity,
backup freshness, TLS status, and release/schema state. At four hours, if
automated monitoring is not restored, new governed writes are blocked. Reads may
continue only under the same verified safe read-only conditions defined for
`RECOVERY_PROTECTION_DEGRADED`; otherwise readiness fails and all customer
traffic is blocked. A Human cannot extend or silently renew the four-hour window.

## 18. Support diagnostics

The safe diagnostic report may include release and configuration-schema
identity, expected/actual schema-head category, component health categories,
role/guard verification state, dependency state, bounded correlation IDs,
resource-capacity categories, backup freshness/verification state, TLS-expiry
category, and monitoring delivery state.

It excludes all secrets, credentials, raw environment values, customer
engineering content, file contents/names/keys, AI content, cross-Organization
data, raw database URLs, session material, and unbounded exception details.

Diagnostics are read-only by default. Report generation is attributable,
rate-limited, access-controlled, and itself logged safely. A diagnostic report
cannot execute a repair, migration, restore, account mutation, or domain
operation.

## 19. Operator identity and access model

Every SATCO operator uses an individually attributable identity with strong
authentication, including a second factor or equivalent phishing-resistant
control selected by IDS-042. Shared credentials are prohibited.

The **normal support role** may view bounded health, diagnostics, alert, release,
backup-freshness, and incident information. It cannot read customer engineering
content, obtain production secrets, execute migrations, restore data, or mutate
application state.

The **elevated operational role** may perform specifically authorized
deployment, secret rotation, backup, restore, and recovery actions within an
approved maintenance/incident scope. Elevation requires purpose, target
deployment, authorizing Human, start/expiry time, allowed action set, and
recording. It expires automatically and can be revoked immediately.

Operator access does not grant Organization business authority, Technical
Report acceptance, Memory admission, engineering approval, or any application
Human role. Application authorization cannot be bypassed for convenience.

This closes AR042-MIN-02 together with the break-glass contract.

## 20. Break-glass contract

Break-glass access is permitted only for an exceptional P1/P2 incident or
approved recovery when normal operational paths cannot restore safety.

It requires:

- an active incident identifier;
- explicit attributable Human authorization;
- exact deployment, duration, and action scope;
- pre-action backup/recovery safeguard where feasible;
- short-lived unique credentials;
- complete safe action recording;
- continuous expiry/revocation enforcement;
- post-action verification and independent review;
- immediate credential revocation at completion.

Normal direct database mutation is prohibited. Break glass does not authorize
engineering-content edits, acceptance, Memory admission, destruction of Audit
or history, disabling Organization controls, schema stamping, concealment of
actions, or copying customer data to uncontrolled systems. Any exceptional data
repair requires separate data-owner/governance authority and a validated,
history-preserving procedure.

Authentication failure denies access without revealing account, incident, or
system details and creates a bounded security event. The primary evidence path
is the canonical protected operational/incident recording system. The sole
alternate evidence path must be preconfigured before an incident, access-
controlled, independently attributable, timestamped, and immutable/append-only
or equivalently protected so it remains available when the primary recorder
fails.

The alternate may be used only when the primary recorder is unavailable, an
active incident exists, and attributable Human break-glass authorization is
recorded through that alternate. If neither primary nor approved alternate
recording is available, elevation is denied. Improvised, verbal-only,
local-text-file, and unrecorded emergency paths are prohibited. After primary
restoration, references to alternate evidence are reconciled into canonical
incident history without deleting, replacing, or rewriting the original
alternate record.

## 21. Incident model

Each incident has an immutable identifier, severity P1-P4, affected deployment,
safe detection source/time, Human incident lead, bounded technical context,
containment actions, recovery decision, customer-communication owner, evidence
links, closure decision, and post-incident review state.

The lifecycle is detected → triaged → contained → recovered → verified →
closed → reviewed. Severity may change with attributable rationale; prior
values remain historical.

Incident records must not duplicate customer engineering content or secrets.
The Human incident lead owns customer communication and promotion/reopen
decisions. This EDS creates no contractual response time or SLA.

## 22. Security control contract

Production validation must prove:

- approved TLS versions/ciphers and certificate validity;
- exact trusted hosts/origins and same-origin API behavior;
- required security headers;
- private backend, database, object storage, migration, and monitoring surfaces;
- bounded rate limits and request/body/time limits with non-disclosing failures;
- production debug and development surfaces disabled;
- non-root/least-privilege runtime and read-only/minimal filesystems where
  compatible;
- immutable artifacts and dependency/container/configuration scans;
- absence of Critical vulnerabilities and exact active Human-approved High
  exception contracts;
- encrypted backup transport/storage and separated decryption authority;
- strong operator authentication and bounded elevation;
- diagnostic/log redaction;
- secret rotation/revocation;
- runtime/schema-owner separation and guard verification.

File-content malware disposition, quarantine, and authorization are deferred to
PATCH-043. Security control failure is never converted into application
engineering authority or a permissive fallback.

## 23. Required runbook set

Every runbook identifies prerequisites, required Human authority, exact target,
safe inputs, ordered procedure, stop/abort conditions, output evidence,
rollback/recovery route, non-disclosure requirements, and owner/review date.

| Runbook | Required output/evidence |
|---|---|
| Deployment | Release/config identities, preflight, deployed digests, readiness, operator decision |
| Configuration | Validated configuration report and protected secret references |
| Bootstrap | Authorization, bounded enablement, result, disablement and secret revocation |
| Startup/shutdown | Drain/stop/start/readiness evidence |
| Migration | Starting/target head, recovery set, one-shot result, guard verification |
| Upgrade | Full sequence and reopen decision |
| Backup | Recovery-set identity, integrity, off-host result, freshness |
| Restore | Isolated target, restored components, verification result |
| Recovery | Incident/maintenance authority, promotion decision, recovery record |
| Rollback | Compatibility decision or restore route and final state |
| Health/diagnostics | Safe collection, interpretation, escalation, disposal |
| Operator access | Identity, role, elevation, expiry, revocation |
| Incident | Detection through post-incident review |
| Secret rotation | New/old references, verification, consumer update, revocation |
| TLS certificate lifecycle | Issuance and renewal authority, certificate references, expiry warning, failed-renewal escalation, emergency replacement, verification, and evidence |
| Monitoring outage/manual fallback | Outage trigger, Human Operations approval, hourly minimum checks, evidence, four-hour expiry, write/traffic restriction, and monitoring-restoration verification |
| Vulnerability disposition | Finding intake, non-waivable Critical block, High exception request and Human Security Approval, compensating controls, expiry/retest, revocation/closure, and artifact deployability result |
| Unsupported-environment reconciliation | Detection, traffic closure, preservation, approved route back to supported profile |

Runbooks are governed release artifacts. Unverified personal notes or shell
history are not supported procedures.

## 24. Operational validation contract

PATCH-042 acceptance requires reproducible production-like evidence for:

- a fresh production-profile deployment from immutable artifacts;
- rejection of every unsafe/missing configuration class;
- only-edge public exposure;
- frontend/API same-origin behavior;
- one-shot migration from the supported starting head;
- release/head/role/guard preflight and drift rejection;
- upgrade success and injected migration/partial-deployment failure;
- encrypted off-host backup and age/failure alerting;
- isolated restore and consistent recovery-set verification;
- supported application rollback and incompatible-schema restore;
- liveness/readiness separation;
- backend object data-plane denial; separate least-privilege
  provisioning/backup-recovery/monitoring/scanner principals; non-content
  storage readiness; object-storage privacy, encryption, capacity, and outage
  behavior;
- structured-log and diagnostic redaction;
- representative alert delivery and a Human-authorized, evidenced, hourly,
  four-hour manual-monitoring fallback that restricts writes at expiry;
- normal/elevated operator authorization and revocation;
- bootstrap configuration/credential control independently combined with
  PATCH-041 application eligibility, including denial of a second Organization;
- break-glass lifecycle, primary-recorder failure, preconfigured alternate
  evidence, both-recorders-unavailable denial, reconciliation, and
  prohibited-action denial;
- TLS, headers, rate limits, private networking, debug restrictions, least
  privilege, Critical blocking, and complete Human-approved High exception
  lifecycle;
- exact RPO threshold transition, write denial, safe read-only continuation,
  and verified recovery-point restoration;
- reproducible build, artifact digest, frontend/backend release match, SBOM,
  provenance, and scan evidence;
- no fake production data and no customer-specific fork.

Validation uses isolated non-customer fixtures unless an explicitly governed
production check is non-mutating and non-disclosing. PATCH-042 evidence is an
input to, not a substitute for, Commercial V1 Release Certification.

## 25. Failure semantics

| Failure | Detection/system state | Health/traffic | Operator action and record | Recovery route |
|---|---|---|---|---|
| Invalid secret/configuration | Static validation; process refuses start | Not alive/not ready; no traffic | Correct configuration; deployment evidence, incident if live service affected | Restart with valid configuration |
| Database unavailable | Readiness probe; process stays alive | Alive/not ready; traffic removed | Investigate dependency; incident by duration/severity | Restore connectivity or approved DB recovery |
| Schema/guard mismatch | Preflight/readiness | Alive/not ready; no traffic | Preserve evidence; no stamp | Correct deployment/migration or restore |
| Migration failure | One-shot task fails; new release remains closed | Backend not ready; no reopen | Incident/maintenance record and bounded diagnosis | Approved retry, compatible rollback, or recovery-set restore |
| Object storage unavailable | Readiness/capacity probe | Alive/not ready while mandatory; no traffic | Restore service; record incident by severity | Service/storage recovery |
| Backend object credential has data-plane authority | Startup/preflight least-privilege verification | Not ready; no customer traffic | P1/P2 security incident; operator cannot waive or reuse credential | Remove/revoke credential, prove backend has zero object data-plane authority, and revalidate separate principals |
| Bootstrap application eligibility fails | PATCH-041 application check after configuration and credential checks | Attempt denied; existing service unchanged | Bounded non-disclosing Audit/operational event; operator cannot override or create business authority | Correct application eligibility or keep bootstrap disabled; no second Organization created |
| Critical vulnerability present | Artifact scan/release gate | Artifact non-deployable; active environment handled as security incident if newly detected | Human Security review; no routine waiver | Remediate and rebuild/rescan a new immutable artifact |
| High vulnerability lacks active valid exception | Artifact scan/exception validator | Artifact non-deployable for deployment/upgrade; active environment enters operational/security review on expiry/revocation | Human Security Approver may approve only the bounded contract; AI/tooling cannot approve | Remediate or establish/revalidate an exact unexpired exception |
| Backup failure with verified recovery freshness <= 4 hours | Backup verification/freshness alert | Alive; reads/writes may continue only while all other readiness guards pass | Incident/alert and Human Operations repair ownership | Repair target and create/verify new set before threshold |
| Verified recovery freshness > 4 hours | Freshness guard enters `RECOVERY_PROTECTION_DEGRADED` | Alive; writes blocked; reads only in verified safe read-only mode, otherwise not ready/no traffic | Mandatory incident/alert; Human Operations cannot waive threshold | Create/verify a fresh point <= 4 hours, pass guards, record Human restoration confirmation |
| Restore verification failure | Isolated verifier marks set failed | Production unchanged; candidate cannot serve | Incident and alternate-set selection | Restore another verified set or governed repair |
| TLS expiry risk/expiry | Certificate monitor/edge handshake | Risk alert before expiry; expired edge serves no application traffic | Renew/replace under runbook | Verify certificate and reopen |
| Monitoring unavailable within fallback window | Pipeline self-health plus incident timer | Alive; reads/writes only during explicitly approved fallback while other guards pass | Human Operations authorizes once for <= 4 hours; record at least hourly mandatory checks | Repair integration and verify alert delivery before expiry |
| Monitoring fallback expired | Four-hour incident timer | Writes blocked; reads only in verified safe read-only mode, otherwise not ready/no traffic | Human Operations cannot extend the window | Restore/verify automated monitoring, then record restoration |
| Release/artifact mismatch | Startup/readiness manifest check | Not ready; no traffic | Correct artifacts; record deployment failure | Redeploy matching immutable set |
| Operator authentication/elevation failure | Identity/access control | Customer service unchanged | Deny, bounded security event, investigate | Restore identity service or use governed break glass |
| Break-glass primary recorder unavailable, alternate healthy | Recorder precheck and active incident | Customer traffic unchanged unless incident requires restriction; elevation remains closed until alternate records authorization | Human break-glass authority uses only preconfigured protected alternate | Reconcile references after primary restoration; preserve original alternate evidence |
| Break-glass primary and alternate recorders unavailable | Recorder precheck | Elevation denied; customer traffic follows underlying incident safety state | Incident escalation only; no verbal/local/unrecorded override | Restore an approved recorder before elevation |

No failure path falls back to unsafe defaults, public dependencies, direct
domain mutation, unverified restore, or disclosure-rich errors.

## 26. Data and authority boundaries

- PostgreSQL remains the sole live authority for structured business/domain
  state.
- Object storage contains opaque operational objects and has no business,
  authorization, provenance, or acceptance authority.
- Logs, metrics, monitoring, alerts, diagnostics, release manifests, and
  incident systems contain operational evidence only and have no business
  authority.
- Backups are immutable recovery material, never an alternate live source of
  truth.
- Recovery promotion creates a restored instance of the governed sources; it
  does not merge or invent authority.
- Operator and break-glass access create no engineering, Organization-business,
  Technical Report, Memory, or AI authority.
- AI remains optional/advisory. Disabled AI does not govern core readiness; an
  enabled provider cannot become a source of business truth.
- Dedicated deployment does not replace or bypass Organization authorization.

## 27. Security and non-disclosure

Public health and error surfaces expose only generic states. Detailed health,
metrics, diagnostics, support tools, recovery inventories, release metadata,
operator records, and incident evidence require operation-specific
authorization.

No operational surface may reveal customer engineering content, cross-
Organization identity, protected existence/count, file/object identity,
provenance, credentials, topology details useful for attack, or internal
exception detail. Denial and unavailable outcomes are bounded and do not reveal
which protected component or identity exists.

Metrics labels and log fields use bounded vocabularies and cannot contain
customer-provided strings. Diagnostic and recovery evidence uses safe opaque
references. Access to protected operational evidence is attributable and
reviewable.

## 28. EDS acceptance criteria

- **AC-01:** Exactly one SATCO-managed dedicated production profile is defined;
  only its edge is public.
- **AC-02:** Development/test conveniences cannot be interpreted as production
  or production evidence.
- **AC-03:** One fixed product/codebase is preserved with no customer-specific
  code/database fork.
- **AC-04:** Every production configuration category has requiredness,
  secrecy, validation, failure, and redaction semantics.
- **AC-05:** Static unsafe configuration fails startup; dependency failures
  affect readiness without redefining liveness.
- **AC-06:** Disabled optional AI does not block core readiness or gain
  authority; enabled AI/scanners remain evidence-only and cannot approve
  vulnerability exceptions or operational authority.
- **AC-07:** Secret provisioning, rotation, revocation, bootstrap control, and
  non-disclosure are closed; bootstrap requires configuration, credential,
  PATCH-041 application eligibility, and Organization/admin safety
  independently, and operator enablement grants no business authority.
- **AC-08:** TLS, same-origin routing, trusted hosts/origins, private services,
  and production debug restrictions are mandatory.
- **AC-09:** ADR-012 one-shot migration, role separation, preflight, expected
  head, backup, and no-stamp recovery rules are preserved.
- **AC-10:** Release identity binds source commit, backend/frontend digests,
  schema head, configuration schema, migrations, provenance, SBOM, and scans;
  Critical findings are non-waivable and each High exception is attributable,
  artifact-bound, scoped, compensated, expiring, retested, and revocable.
- **AC-11:** The backend has zero object data-plane authority, including no
  read/list/write/delete, URL generation, or metadata retrieval; non-content
  health and provisioning/backup-recovery/monitoring/scanner principals are
  separate, and object storage owns no Supporting File domain semantics.
- **AC-12:** A verified recoverable point no older than four hours and the
  stated encrypted off-host retention baseline are required; exceeding four
  hours blocks writes, permits reads only under verified safe read-only
  enforcement, and cannot be waived by Human Operations.
- **AC-13:** Only a sealed, verified, internally consistent recovery set may be
  promoted; independent multi-store restore fails closed.
- **AC-14:** Restore is isolated and Human-authorized before production
  promotion; RTO assumptions are explicit.
- **AC-15:** Upgrade, partial-failure, compatible rollback, and restore routes
  are deterministic and evidence-producing.
- **AC-16:** Public liveness/readiness is generic; protected detail is bounded
  and authorization-controlled.
- **AC-17:** Logs are structured, bounded, redacted, and drop unsafe fields
  rather than exposing plaintext.
- **AC-18:** Mandatory operational signals, alert classes, and Human ownership
  are defined without full APM/SIEM scope; monitoring loss permits only one
  explicitly Human-authorized, evidenced fallback of at most four hours with
  at least hourly mandatory checks and fail-closed write behavior at expiry.
- **AC-19:** Diagnostics are read-only, attributable, bounded, and contain no
  secrets or customer content.
- **AC-20:** Normal and elevated operator roles are individually attributable,
  strongly authenticated, least-privileged, expiring, and revocable.
- **AC-21:** Break glass requires Human authority and an incident and records
  through the primary or one preconfigured immutable attributable alternate;
  if neither is available elevation is denied, and reconciliation preserves
  original evidence and cannot mutate engineering authority or history.
- **AC-22:** Incident lifecycle and customer-communication ownership are defined
  without creating an SLA.
- **AC-23:** Production security controls, non-waivable Critical blocking, and
  complete Human Security Approval/expiry/retest/revocation of High exceptions
  are testable; AI approval and file quarantine semantics remain excluded.
- **AC-24:** Every required runbook has authority, inputs, procedure, stop
  conditions, evidence, and recovery route, including explicit TLS lifecycle,
  monitoring-outage/manual-fallback, and vulnerability-disposition runbooks.
- **AC-25:** PATCH-042 operational validation is reproducible and explicitly
  stops short of Commercial V1 Release Certification.
- **AC-26:** Every major failure has detection, liveness/readiness and
  read/write traffic state, bounded Human response, incident/evidence, and a
  deterministic fail-closed recovery route, including RPO breach, monitoring
  fallback expiry, bootstrap denial, over-privileged object credentials,
  vulnerability gates, and unavailable break-glass recorders.
- **AC-27:** PostgreSQL, object storage, telemetry, backups, operators, and AI
  retain the stated non-competing authority boundaries.
- **AC-28:** Operational surfaces cannot disclose protected engineering,
  Organization, credential, topology, or object information.
- **AC-29:** PATCH-043, customer-managed hosting, HA/Kubernetes, entitlements,
  Company-OS, Modular Platform Architecture, and Release Certification remain
  excluded.
- **AC-30:** IDS-042 can select exact technologies, DTOs/config keys, commands,
  thresholds, schemas, and evidence formats without changing these behaviors.

## 29. Traceability matrix

| Authority/source | EDS realization | Acceptance criteria |
|---|---|---|
| PATCH-042 production packaging/topology | Sections 2, 3, 7, 9 | AC-01–03, AC-08, AC-10 |
| Configuration/secrets | Sections 4–6 | AC-04–07 |
| ADR-012 migration/upgrade authority | Sections 8 and 14 | AC-09, AC-15 |
| Backup/restore/recovery | Sections 11–14 | AC-12–15 |
| Health/logging/monitoring | Sections 15–17 | AC-16–18 |
| Support/incident/runbooks | Sections 18–23 | AC-19–24 |
| Production security/validation | Sections 22 and 24 | AC-23, AC-25 |
| AR042-MIN-01 | Section 12 consistent recovery set | AC-13 |
| AR042-MIN-02 | Sections 19–21 operator/break-glass/incident | AC-20–22 |
| AR042-MIN-03 | Sections 4–5 configuration/startup/readiness | AC-04–06 |
| AR042-OBS-02 | Section 9 supply-chain contract | AC-10 |
| Organization/Human/AI authority | Sections 2, 19, 20, 26, 27 | AC-03, AC-20–22, AC-27–28 |
| Expected PATCH-043 separation | Sections 1, 10–12, 22 | AC-11, AC-13, AC-23, AC-29 |
| Release Certification separation | Sections 1 and 24 | AC-25, AC-29 |

Focused Independent EDS Review traceability is closed as follows:

| Finding | Amended design and failure semantics | Acceptance criteria | Future IDS-042 responsibility (technology/mechanism only) |
|---|---|---|---|
| EDS042-MAJ-01 | Sections 4, 10, 24–27; over-privileged object credential row in Section 25 | AC-11, AC-26–29 | Exact zero-data-plane policy tests, separate principal definitions, and non-content health mechanism |
| EDS042-MAJ-02 | Sections 4–6 and 24–26; bootstrap eligibility failure row in Section 25 | AC-07, AC-26–28 | Exact config/credential schema, PATCH-041 application-service integration, bounded event shape, and verification tests |
| EDS042-MAJ-03 | Sections 9, 22, 24–25; Critical and High failure rows in Section 25 | AC-06, AC-10, AC-23–26 | Exact Human Security Approver role mapping, exception schema/storage, scan integration, and expiry/retest enforcement |
| EDS042-MAJ-04 | Sections 20, 23–25; both break-glass recorder rows in Section 25 | AC-21, AC-24, AC-26 | Exact primary/alternate technologies, protected append-only evidence schema, availability precheck, and reconciliation procedure |
| EDS042-MAJ-05 | Sections 5, 11, 15, 17 and 25; recovery-freshness rows in Section 25 | AC-12, AC-16, AC-18, AC-26 | Exact freshness guard, write-block/read-only enforcement, protected health representation, and restoration verification |
| EDS042-MIN-01 | Sections 5, 17, 23–25; monitoring fallback rows in Section 25 | AC-18, AC-24, AC-26 | Exact monitoring technology, fallback evidence schema/timer, manual-check mechanism, and traffic enforcement |
| EDS042-MIN-02 | Section 23 explicit TLS, monitoring-fallback, and vulnerability runbooks | AC-24 | Exact governed paths/templates and executable runbook verification matrix |

## 30. Findings and open questions

The initial Independent EDS Review reported zero Critical, five Major, and two
Minor findings. This focused amendment preserves that FAIL history and resolves:

- EDS042-MAJ-01 through the zero object-data-plane backend contract and separate
  principals;
- EDS042-MAJ-02 through the bootstrap configuration/application-authority
  conjunction;
- EDS042-MAJ-03 through the non-waivable Critical and bounded Human-approved
  High exception contract;
- EDS042-MAJ-04 through the one preconfigured alternate immutable evidence path
  and denial when neither recorder is available;
- EDS042-MAJ-05 through deterministic `RECOVERY_PROTECTION_DEGRADED`, write
  denial, conditional read-only service, and verified restoration;
- EDS042-MIN-01 through the Human-authorized four-hour manual-monitoring limit;
- EDS042-MIN-02 through the three explicit governed runbook requirements.

No Critical, Major, or Minor EDS ambiguity remains after this amendment,
subject to focused Independent EDS re-review.

AR042-MIN-01 is closed by the recovery-set identity, component/cutoff manifest,
verification lifecycle, and fail-closed promotion contract.

AR042-MIN-02 is closed by the attributable normal/elevated operator,
break-glass, expiration/revocation, incident, prohibited-action, and
non-engineering-authority contracts.

AR042-MIN-03 is closed by the normative configuration and
startup/liveness/readiness matrices.

AR042-OBS-02 is addressed by the immutable release manifest, artifact digests,
provenance, SBOM, scanning, and deployability gates.

IDS-042 must select, without changing EDS semantics:

- exact production configuration keys and validation schemas;
- edge, object-storage, monitoring, backup, and secret-delivery technologies;
- health/diagnostic API schemas and authentication mechanisms;
- release-manifest, SBOM, provenance, signing, and scan formats;
- backup formats, encryption mechanisms, inventory/cutoff representation, and
  recovery verification commands;
- exact rate limits, header values, subordinate timeouts, capacity thresholds,
  alert-delivery timing, and retention implementation, without changing the
  fixed four-hour RPO or monitoring-fallback limits and their traffic semantics;
- operator identity provider, second-factor mechanism, role mappings, and
  evidence persistence;
- Human Security Approver role mapping and exact bounded High-exception schema,
  without creating a Critical-exception path;
- exact zero-data-plane backend object policy and distinct operational-principal
  definitions, without granting PATCH-043 application permissions;
- primary and preconfigured alternate break-glass evidence technologies and
  reconciliation schema, without an improvised fallback;
- exact mechanisms that enforce RPO/monitoring write blocking, safe read-only
  service, protected health categories, fixed timers, and restoration checks;
- runbook paths/templates and executable verification matrix.

These are IDS decisions, not unresolved architecture or product questions.

## 31. EDS verdict

EDS-042: ACCEPTED / COMPLETE. The initial Independent EDS Review remains
recorded as FAIL; this document does not retrospectively promote it. The focused
Independent EDS re-review passed and Human EDS acceptance is PASS.

## 32. Authority state

- PATCH-042 Architecture: ACCEPTED.
- QG-M1: PASS.
- EDS-042 Design Authority: consumed for this design.
- Human EDS-042 Acceptance: PASS.
- IDS-042 Design Authority: GRANTED.
- Implementation Plan Authority: NOT GRANTED.
- Implementation Authority: NOT GRANTED.

## 33. Recommended next governed action

Create IDS-042 from this accepted EDS-042. IDS must choose exact
implementation mechanisms without changing the fixed object-authority,
bootstrap, vulnerability, break-glass, RPO, monitoring, or PATCH-043
boundaries.
