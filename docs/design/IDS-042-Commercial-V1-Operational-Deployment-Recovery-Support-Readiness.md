# IDS-042 — Commercial V1 Operational Deployment, Recovery & Support Readiness

Status: ACCEPTED / COMPLETE. Independent IDS Review: PASS.

Authority: EDS-042 is ACCEPTED. This specification selects implementation
mechanisms only; it grants no implementation, deployment, certification, or
PATCH-043 authority.

## 1. Fixed implementation boundary

This IDS implements the accepted single SATCO-managed, dedicated,
single-customer Commercial V1 production profile. PostgreSQL remains the sole
structured business authority. Operational object storage, metrics, logs,
backups, release artifacts, and incident evidence have no business authority.

No Supporting File Asset, customer-object data plane, upload/download,
Evidence/file relationship, quarantine, PATCH-043 behavior, customer-managed
hosting, HA/multi-region, entitlement, billing, CRM, or Release Certification
is implemented or implied.

## 2. Production topology and packaging

The implementation creates a production-only Compose profile with four private
networks/services: `edge` (Nginx 1.27-alpine, the only public service),
`frontend` (immutable Vite build served by Nginx), `backend` (FastAPI/Uvicorn,
non-root), and `postgres` (PostgreSQL 17). A one-shot `migrate` service runs
before backend readiness. PostgreSQL and backend have no published host ports;
only `edge` publishes 443 and optional port 80 redirect. Internal names are not
exposed through public error or health responses.

Production images use dedicated Dockerfiles, pinned base-image digest variables
in the release manifest, multi-stage builds, `npm ci`, Python requirements
locked to hashes before delivery, no bind mounts, read-only root filesystems
where compatible, dropped Linux capabilities, `no-new-privileges`, explicit
non-root UID/GID, writable tmpfs only where needed, and immutable image tags
only as labels—not deployment selectors. Deployment selects backend and
frontend images by digest from one release manifest.

Nginx terminates TLS, redirects HTTP to the canonical HTTPS origin, serves only
the versioned frontend asset set, proxies the exact `/api/v1/` and generic
health paths, enforces request/body/time limits, security headers, and
rate-limits public unauthenticated paths. It denies all other internal paths.
Trusted Host, CORS/same-origin, proxy forwarding, and public URL settings are
validated by the backend; wildcard values are rejected.

## 3. Configuration and secret contract

`app.core.config.Settings` gains a production validation method invoked before
application serving. The production configuration is explicit and rejects
unknown security-critical values, unsafe defaults, missing secrets, invalid
URLs, wildcard hosts/origins, role collapse, or release/guard mismatch.

| Logical setting | Exact environment/secret input | Validation |
|---|---|---|
| Mode/release | `SATCO_ENVIRONMENT=production`, `SATCO_RELEASE_MANIFEST_PATH` | exact production enum; manifest digest/signature/schema valid |
| Public edge | `SATCO_PUBLIC_URL`, `SATCO_TRUSTED_HOSTS`, `SATCO_ALLOWED_ORIGINS` | HTTPS canonical origin and explicit same-origin/allow-list only |
| Runtime DB | `DATABASE_HOST`, `DATABASE_PORT`, `DATABASE_NAME`, `DATABASE_USER=satco_runtime`, `DATABASE_PASSWORD_FILE` | password read from `/run/secrets`; role differs from owner |
| Migration DB | `ALEMBIC_DATABASE_URL_FILE`, `MIGRATION_DATABASE_ROLE=satco` | available only to migrate/preflight service |
| Secrets | `SECRET_KEY_FILE`, `PLATFORM_BOOTSTRAP_KEY_FILE`, optional provider secret files | non-default, high entropy, unique, never logged |
| Bootstrap | `SATCO_BOOTSTRAP_ENABLED`, `SATCO_BOOTSTRAP_WINDOW_END` | explicit boolean/window; configuration is not business authority |
| Expected state | `SATCO_EXPECTED_ALEMBIC_HEAD`, `SATCO_PERSISTENCE_GUARD_VERSION` | equal release manifest and actual verified state |
| Object health | `SATCO_OBJECT_HEALTH_URL`, `SATCO_OBJECT_HEALTH_CA_FILE` | private non-content health assertion only; no object credential in backend |
| Backup/monitoring | `SATCO_BACKUP_POLICY_ID`, `SATCO_MONITORING_POLICY_ID`, `SATCO_OPS_MODE_FILE` | protected references; policy/ops-mode format valid |
| TLS | `SATCO_TLS_CERT_FILE`, `SATCO_TLS_KEY_FILE`, `SATCO_TLS_CHAIN_FILE` available only to edge | non-expired certificate matching canonical hostname |

Docker Compose secrets mount the `*_FILE` values read-only at `/run/secrets`.
Plaintext `.env`, image `ENV`, source control, frontend assets, diagnostics,
and logs cannot contain production secret values. Rotation is a staged secret
mount change: validate new reference, restart only affected service, verify,
revoke old reference, and record protected operator evidence.

Bootstrap is usable only when `SATCO_BOOTSTRAP_ENABLED=true`, its secret and
window are valid, and the existing PATCH-041 application eligibility and
Organization/admin safety checks pass. Operators can alter only the first three
configuration conditions. A failed application eligibility check returns the
existing protected denial, records bounded Audit/operations evidence, and never
creates another Organization.

## 4. Migration, database roles, and release preflight

`migrate` is the only service holding `satco` schema-owner credentials. It
executes `alembic upgrade <SATCO_EXPECTED_ALEMBIC_HEAD>` exactly once after:
release-manifest validation, a sealed pre-upgrade recovery point, expected-head
graph validation, and runtime/schema role separation validation. The backend
never imports Alembic or owns migration credentials.

Preflight fails closed if `alembic heads` is not one head, the release-declared
head is not that head, the live revision differs after migration, or existing
runtime guard validation detects ownership/grant/function/trigger drift.
`alembic stamp` is prohibited for deployment recovery. The current repository
head is `e04100000001`; PATCH-042 introduces a migration only if a narrowly
needed operational-state/Audit persistence guard cannot be implemented as
deployment configuration. Such a migration must be separately listed in the
accepted implementation manifest, have parent `e04100000001`, and preserve
ADR-012 role separation.

`satco_runtime` has only existing necessary DML and no schema ownership,
role-membership, DDL, trigger/function alteration, backup, restore, or migration
authority. `satco` owns schema changes only and is not mounted in backend.

## 5. Release identity, reproducibility, and vulnerability gate

`ops/release-manifest.v1.json` is canonical JSON with: release identifier,
Git commit, backend image digest, frontend asset-set digest, expected Alembic
head, configuration-schema version, migration-artifact digest, Python lockfile
digest, `package-lock.json` digest, SBOM identifiers, scan-evidence identifiers,
creation timestamp, and signing/approver evidence reference. Deployers verify
the manifest before pulling immutable digests and the backend verifies its own
mounted manifest at startup.

`pip-compile --generate-hashes` produces a reviewed production lock; frontend
uses the committed `package-lock.json` through `npm ci`. SBOMs are generated
with Syft for both images; Trivy scans the immutable images and dependency
artifacts. Reports are protected evidence and must be redacted of secrets.

Critical finding => non-deployable, with no routine exception. High finding
=> non-deployable unless the release includes a canonical
`ops/high-vulnerability-exceptions.v1.json` record for that artifact digest.
Each record contains finding identity, severity/source, artifact digest,
rationale, compensating controls, bounded scope, Human Security Approver
identity/time, expiry, retest condition/result reference, and
`active|revoked|closed` status. A validator rejects duplicate/incomplete,
expired, revoked, wrong-digest, or failed-retest records. It stores no customer
content. AI/scanners create evidence only and cannot sign/approve records.

## 6. Object storage and operational principals

PATCH-042 uses one private S3-compatible namespace. The backend receives no
S3 endpoint credential, SDK data-plane dependency, or application permission:
it cannot read, list, write, delete, generate presigned URLs, or retrieve
customer-object metadata. The backend readiness path calls only a private
`SATCO_OBJECT_HEALTH_URL` supplied by monitoring; it returns canonical
`available|unavailable` and observation time, signed/mTLS-authenticated by a
monitoring principal, with no object identity, count, or metadata.

Separate credentials are provisioned for: infrastructure provisioning;
backup/recovery of encrypted recovery material; monitoring health (at most
bucket/service `HEAD`-style non-enumerating probe); and future scanner
foundation. They are mounted only in their corresponding one-purpose job. No
principal is shared for convenience. PATCH-043 must explicitly add any
application data-plane capability.

## 7. Backup, recovery, RPO, and safe degraded operation

A scheduled `satco-backup` job uses the PostgreSQL 17 client to produce a
custom-format `pg_dump`, computes SHA-256, encrypts it with the recovery-only
age recipient, and uploads it with a recovery-only credential to an independent
off-host target. It creates one canonical `recovery-set.v1.json` containing
set UUID, start/finish, deployment/release/config identities, Alembic head,
database artifact digest/cutoff/status, object component
`not_applicable|verified_empty`, encrypted artifact identity, key reference,
integrity verification, and safe actor/job identity. A separate scheduled
isolated restore verifier runs `pg_restore --list` and a disposable PostgreSQL
restore before marking a set verified.

The scheduler runs at least hourly. Retention is enforced by the backup
principal: every sealed set seven days, one verified daily set thirty days, and
pre-upgrade sets thirty days and through upgrade acceptance. Runtime cannot
create/delete/restore/decrypt backups.

Freshness is computed from the most recent verified set finish time. At <=4h,
normal service remains possible. At >4h, the operations controller atomically
writes signed `RECOVERY_PROTECTION_DEGRADED` into the read-only ops-mode mount,
opens an incident, and blocks governed writes through both Nginx unsafe-method
policy and backend request middleware. Read-only service is permitted only when
both gates are verified, DB/application/release/schema guards pass, and no other
readiness blocker exists. Otherwise generic readiness is false and the edge
blocks customer traffic. Human Operations cannot alter the gate to re-enable
writes. A new verified <=4h recovery set, all guard checks, and attributable
Human restoration confirmation are required to return `normal` mode.

Restores occur only in an isolated non-serving Compose project, are verified
against the recovery manifest, and require attributable Human recovery
authorization for promotion. Upgrade runs preflight -> sealed verified backup ->
write drain/ops mode -> one-shot migrate -> guard verification -> immutable
release deploy -> readiness/smoke -> Human reopen. Compatible rollback is
allowed only where release compatibility declares it; otherwise restore the
pre-upgrade recovery set. No schema stamp or destructive repair bypass exists.

## 8. Health, logs, metrics, alerts, and diagnostics

`GET /health/live` returns generic `alive` and never opens dependencies.
`GET /health/ready` returns only generic `ready|not_ready`, evaluates config,
DB, head/guard, release match, non-content object health, ops mode, and required
edge condition, and never emits component detail. Authenticated operations
diagnostics return bounded safe categories, correlation IDs, release/config/head
references, recovery freshness category, TLS category, and monitoring state;
they exclude secret, object, customer, Organization, raw endpoint, stack, and
engineering data.

Python JSON logging uses an allow-listed formatter and redaction filter before
emission. Allowed fields are timestamp, severity, bounded event code,
correlation ID, deployment component, release ID, duration, safe outcome, and
attributable operational actor where required. Unknown object serialization,
request/response bodies, tokens, credentials, object keys, customer text, and
unbounded exception detail are dropped.

A private `GET /operations/metrics` Prometheus-text endpoint is available only
to the monitoring principal. A minimal `satco-ops-monitor` scheduled job reads
edge/backend readiness, database capacity, disk, non-content storage health,
backup freshness, TLS expiry, release/head, and monitor self-health; it sends
bounded P1–P4 events to the primary incident recorder. No APM/SIEM, tracing, or
autonomous remediation is introduced.

Monitoring loss opens an incident. A Human Operations approver may enter a
single manual fallback for <=4h. Evidence contains at least hourly edge,
backend readiness, DB capacity, disk/storage, backup freshness, TLS, and
release/schema checks. At expiry, the same dual safe-read-only gates apply;
writes remain blocked until monitoring health is restored and recorded.

## 9. TLS, access, break glass, and support

Nginx receives certificate/key only through read-only secrets. `certbot` runs as
a one-shot, non-serving renewal job using a dedicated ACME credential; it writes
a new staged secret reference, performs hostname/chain/expiry verification, and
the edge reloads only after validation. Expiry warning and failed-renewal events
are P2; an expired certificate removes public traffic until emergency
certificate replacement is verified.

Normal support uses individually attributable strong-authentication identities
and can read only protected bounded operations diagnostics. Elevated operations
uses a short-lived, scoped, expiring/revocable credential with Human approver,
target, purpose, action allow-list, start/end, and primary incident evidence.
It cannot acquire engineering, Organization-business, Technical Report, Memory,
or AI authority.

The primary recorder is the protected canonical incident system. One alternate
is an operations-only S3 Object-Lock/WORM evidence namespace with a dedicated
write-only recorder credential, immutable event envelope (incident ID, Human
authorization identity, time, target, action scope, safe outcome), protected
read access, and no customer content. Alternate entry requires primary
unavailability plus active incident plus Human authorization. If either required
authorization or both recorders are unavailable, elevation is denied. Reconcile
alternate envelope references into the primary record after restoration without
deleting/replacing the original WORM record.

Support bundles are generated from allow-listed diagnostics/log windows and
release/incident references, encrypted for the authorized recipient, bounded,
attributable, and never contain secrets or customer engineering content.

## 10. Runbooks and validation contract

Version-controlled Markdown runbooks under `ops/runbooks/` are required for
deployment, configuration/secrets, bootstrap, startup/shutdown, migration,
upgrade, backup, restore, recovery, rollback, health/diagnostics, operator
access, incident, secret rotation, TLS lifecycle, monitoring/manual fallback,
vulnerability disposition, and unsupported-environment reconciliation. Each
has trigger, Human authority, safe inputs, ordered actions, evidence, abort and
escalation route, recovery, owner, and review date.

Validation must use isolated, non-customer fixtures except a governed
non-mutating production check. It proves image/asset digest reconciliation,
production config fail-closed cases, only-edge exposure, TLS/headers/rate limits,
runtime-vs-schema role separation, one-shot migrations, backup/restore/recovery
set consistency, RPO write block/read-only mode, health/non-disclosure,
redaction, monitoring fallback expiry, Human bootstrap eligibility, security
finding gates, break-glass recorder conditions, no backend object data-plane,
runbook execution evidence, no fake production data, and scope/PATCH-043
exclusion.

## 11. Anticipated implementation boundary and migration decision

Expected production surfaces are production Compose and Dockerfiles, Nginx and
health/monitor scripts, backend configuration/startup/health/logging middleware,
an operations diagnostics router, deployment/backup/recovery scripts and
runbooks, dependency lock/build tooling, and focused backend/frontend/ops tests.
No frontend product feature, domain API, object/file model, customer data-plane,
or business migration is anticipated.

| Surface | Anticipated file boundary |
|---|---|
| Compose/images/edge | MODIFY `docker-compose.yml` only to preserve development parity; CREATE `docker-compose.production.yml`, `backend/Dockerfile.production`, `frontend/Dockerfile.production`, `ops/nginx/nginx.conf`, and `ops/nginx/default.conf` |
| Backend operational gate | MODIFY `backend/app/core/config.py`, `backend/app/core/database.py`, and `backend/app/main.py`; CREATE `backend/app/core/operations.py`, `backend/app/api/v1/routers/operations.py`, and focused operational schemas/tests only |
| Build/release security | MODIFY `backend/requirements.txt`, `backend/pyproject.toml`, `frontend/package.json`, and committed lock inputs only when the selected tool requires it; CREATE `ops/release-manifest.v1.schema.json`, release/scan scripts, and templates |
| Backup/monitor/operations | CREATE `ops/scripts/backup.sh`, `restore-verify.sh`, `ops-monitor.sh`, `preflight.sh`, `set-ops-mode.sh`, and their non-customer fixture tests |
| Runbooks/evidence | CREATE only `ops/runbooks/*.md`, validation harnesses, and `docs/reviews` evidence artifacts required by accepted batch manifests |

Neither direct foreign persistence access nor a business-domain migration is in
scope. `backend/migrations/versions/*` remains excluded unless a later manifest
proves the narrow persistent-state prerequisite described below.

The preferred implementation is configuration/files/scripts plus targeted
application health and write-mode guards. A new Alembic migration is not
authorized by this IDS unless an accepted implementation manifest demonstrates
that persistent, schema-owner protected operational-state evidence is essential
to enforce the EDS contract. Any such migration is an explicit later-batch
decision and cannot be smuggled in with application work.

## 12. Verification matrix

| Invariant | Required evidence |
|---|---|
| Packaging/topology | Production image build, Compose network/port inspection, non-root/read-only filesystem checks, immutable digest deployment simulation |
| Config/secrets/bootstrap | Every missing/unsafe/default value fails before serving; config enablement cannot bypass PATCH-041 eligibility or create another Organization |
| DB/migration | One head, expected-head mismatch denial, role/guard drift denial, migration failure/rollback/recovery paths |
| Release/security | Reproducible lock/build, manifest/asset/image digest mismatch denial, SBOM/scans, Critical block, High exception active/expired/revoked/retest cases |
| Object boundary | Backend lacks object credentials/SDK data-plane calls; monitor health reveals no objects; principal separation verified |
| Backup/recovery | Hourly set, encryption, retention, manifest digest, isolated restore, inconsistent set denial, >4h traffic/write behavior and restoration |
| Health/log/monitor | Generic public health, protected bounded diagnostics, redaction rejection, signal/alert paths, manual fallback hourly evidence/expiry closure |
| TLS/operator/break glass | TLS renewal/expiry/replacement, individual attribution, elevation expiry/revocation, primary/alternate/both-recorder cases and immutable reconciliation |
| Scope | No fake production data, no customer-object domain/data plane, PATCH-043 exclusion, adjacent/full regression, static/import/type/build, `git diff --check` |

## 13. IDS verdict and authority

IDS-042 is ACCEPTED / COMPLETE. It selects mechanisms but asserts no deployment,
backup, recovery, external certificate, vulnerability scan, or production-runtime
evidence. Implementation Plan-042 Design Authority is GRANTED; implementation
authority remains NOT GRANTED.
