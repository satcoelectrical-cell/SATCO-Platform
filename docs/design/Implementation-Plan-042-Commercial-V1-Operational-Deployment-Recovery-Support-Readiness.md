# Implementation Plan-042 — Commercial V1 Operational Deployment, Recovery & Support Readiness

Status: ACCEPTED / COMPLETE. Independent Plan Review: PASS.

Authority: PATCH-042 Architecture, EDS-042, and IDS-042 are accepted. This plan
does not grant implementation, delivery, certification, or PATCH-043 authority.

## Global controls

Every batch receives an exact authorized-file manifest, focused validation, an
independent review, and Human acceptance only after zero unresolved Critical or
Major findings. Preserve unrelated work by staging only manifest paths/hunks.
No batch may add Supporting File Asset, application object data-plane authority,
file lifecycle, customer/domain API semantics, business migration, customer-
specific fork, HA/multi-region, or Commercial V1 certification.

Production-like evidence uses isolated non-customer fixtures. External DNS,
certificate, object-store, backup target, scanner, and incident-recorder
credentials are prerequisites for final external validation; local production-
profile equivalents are clearly labelled as such and do not claim external
production evidence.

## Dependency-ordered batches

### Batch 1 — Production configuration, startup, release, and health

**Scope:** fail-closed production settings, secret-file loading, release-manifest
validation, startup preflight, generic liveness/readiness, protected operations
diagnostics, runtime/schema-owner verification reuse, and write-mode gate
interfaces.

**Expected surfaces:** MODIFY `backend/app/core/config.py`,
`backend/app/core/database.py`, `backend/app/main.py`, `backend/requirements.txt`,
`backend/pyproject.toml`; CREATE `backend/app/core/operations.py`,
`backend/app/api/v1/routers/operations.py`, `ops/release-manifest.v1.schema.json`,
`ops/release-manifest.example.v1.json`, and focused backend config/health/release
tests.

**Evidence:** unsafe/default/missing config; runtime-role collapse; manifest/head
mismatch; generic-vs-protected health; no secret/object/customer disclosure;
normal/read-only write-mode behavior; static/import checks.

**Stop:** a required setting needs a new EDS decision, health reveals protected
detail, production defaults remain permissive, or a business/domain migration is
required.

### Batch 2 — Production packaging, edge, TLS, and private networking

**Scope:** immutable backend/frontend build path, production Compose topology,
Nginx edge, headers/rate limits, TLS secret wiring, only-edge exposure,
non-root/read-only hardening, and release-digest reconciliation.

**Expected surfaces:** CREATE `docker-compose.production.yml`,
`backend/Dockerfile.production`, `frontend/Dockerfile.production`,
`ops/nginx/nginx.conf`, `ops/nginx/default.conf`, TLS/edge validation scripts and
tests; MODIFY `docker-compose.yml` only if development/prod split requires an
explicit harmless shared definition, and `frontend/package.json`/lock inputs
only for reproducible build commands.

**Evidence:** image/frontend build; no bind mounts/private port exposure; digest
mismatch denial; HTTPS redirect/headers/rate limits; certificate valid/expired
states; no internal topology in errors.

**Stop:** an external topology, customer data plane, or unreviewed public route
is needed; TLS cannot be mounted as a secret; a base-image/lock change is not
reproducible.

### Batch 3 — Migration, backup, recovery, upgrade, and rollback

**Scope:** one-shot migrate/preflight, off-host encrypted recovery-set scripts,
isolated restore verification, RPO monitor, `RECOVERY_PROTECTION_DEGRADED`, safe
read-only enforcement, upgrade/rollback orchestration, and recovery evidence.

**Expected surfaces:** CREATE `ops/scripts/preflight.sh`, `ops/scripts/backup.sh`,
`ops/scripts/restore-verify.sh`, `ops/scripts/set-ops-mode.sh`,
`ops/scripts/upgrade.sh`, `ops/scripts/rollback.sh`, recovery-set fixtures/tests,
and operational test harnesses; MODIFY Batch-1 operations/config code only for
the accepted dual write gate. `backend/migrations/versions/*` remains forbidden
unless a manifest documents the IDS conditional persistent-state prerequisite and
an IRR confirms its parent/head/role safety.

**Evidence:** single-head and expected-head checks; migration failure; sealed
set/digest/encryption/retention; inconsistent restore denial; <=4h normal,
>4h write block/read-only/unready behavior; restoration; compatible rollback and
restore route.

**Stop:** safe read-only cannot be independently enforced, recovery requires
schema stamping/direct DB repair, backup requires runtime credentials, or a new
migration is needed without explicit approved manifest.

### Batch 4 — Logs, monitoring, support, operator controls, and break glass

**Scope:** allow-listed JSON logging/redaction, private metrics, monitor and
manual fallback evidence, bounded diagnostics/support bundles, individual
operator/elevation controls, vulnerability exception validation, and primary/
alternate recorder handling.

**Expected surfaces:** MODIFY Batch-1 operations/config/main surfaces as needed;
CREATE `ops/scripts/ops-monitor.sh`, `ops/scripts/validate-high-exceptions.sh`,
`ops/scripts/record-break-glass.sh`, support-bundle/redaction helpers, exception
schema/template, and focused logging/monitoring/operator/security tests.

**Evidence:** plaintext redaction/drop; monitoring incident/hourly checks/four-
hour expiry; Human-only High approval and Critical block; operator expiry/revoke;
primary recorder, alternate WORM recorder, and both-unavailable denial; bounded
non-disclosure.

**Stop:** evidence recording is not independently attributable/immutable,
monitoring fallback can be silently extended, AI obtains approval power, or an
operator path gains business/engineering authority.

### Batch 5 — Runbooks, operational validation, final evidence

**Scope:** governed runbooks, reproducible production-profile harnesses,
security/supply-chain evidence, no-fake-data checks, final scope review, and
final implementation-review readiness. This batch creates no customer feature.

**Expected surfaces:** CREATE `ops/runbooks/` documents for all IDS-required
procedures, validation scripts/fixtures, and PATCH-042 review/evidence records;
MODIFY only PATCH-042 governance status artifacts allowed by its final manifest.

**Evidence:** all prior batches; backend/frontend regression/type/build/static;
image/Compose checks; migration; local production-profile deployment; external
prerequisite status; runbook walkthroughs; no secret/fake-production data;
security/non-disclosure; `git diff --check`; final independent review package.

**Stop:** required evidence would be fabricated, an external prerequisite is
missing for a claim being made, a deferred capability is necessary, or any
Critical/Major finding remains.

## Sequencing and rollback

Batch 1 precedes all service startup. Batch 2 provides the only public edge.
Batch 3 depends on Batches 1–2 and must verify recovery before upgrade. Batch 4
depends on Batches 1–3 because it observes their signals and evidence. Batch 5
depends on all prior batches. Every mutating operational step requires a
pre-action verified recovery set and a documented abort/recovery route. No
batch promotes a release without its predecessor acceptance.

## Delivery boundary

Batch manifests enumerate exact files and prohibited paths before each change.
Delivery requires final independent review, explicit Human QG-11/QG-12 and
delivery authority. PATCH-042 may become delivery-ready only; Commercial V1
Release Certification and PATCH-043 registration remain separate future gates.

Human Implementation Plan-042 Acceptance: PASS. IRR-042 Authority is GRANTED.
Implementation authority remains NOT GRANTED.
