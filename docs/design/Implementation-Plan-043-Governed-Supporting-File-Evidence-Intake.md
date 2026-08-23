# Implementation Plan-043 — Governed Supporting File Evidence Intake

## 1. Status and execution rule

**ACCEPTED / COMPLETE.** Six dependency-ordered batches implement the accepted
PATCH/EDS/IDS. Every batch requires a separately prepared exact Authorized File
Manifest, explicit Human implementation authority, focused implementation,
Independent Review and Human acceptance. No batch authority is granted here.

The worktree is dirty with unrelated work. Manifests must use path and hunk
allow-lists, never clean/reset/stash those changes and stop on overlap that
cannot be isolated. All migrations start from verified sole head
`e04100000001`.

## 2. Batch 1 — Contracts, Aggregate and persistence foundation (S01–S04)

### Scope

- **S01:** closed enums, value objects, command/read/result DTOs, ports,
  canonical serialization/digest and safe filename/type/size validation;
- **S02:** pure Supporting File Asset lifecycle/lineage Aggregate;
- **S03:** migration, tables, exact constraints/functions/triggers, role grants,
  ORM mappings and Alembic-head reconciliation;
- **S04:** no-commit repositories and bounded deterministic queries.

### Expected production surfaces

CREATE `backend/app/enums/supporting_file.py`,
`backend/app/models/supporting_file.py`,
`backend/app/models/supporting_file_command.py`,
`backend/app/schemas/supporting_file.py`,
`backend/app/ports/supporting_file.py`,
`backend/app/exceptions/supporting_file.py`,
`backend/app/repositories/supporting_file_repository.py`,
`backend/migrations/versions/e04300000001_supporting_files.py`.
MODIFY `backend/app/models/evidence.py` and focused Evidence aggregate tests
only to add the durable one-way file-link sealing marker on first departure
from proposed; modify model/enums package exports only if imports require them and
`backend/migrations/env.py` only if metadata discovery requires it.

### Expected tests

CREATE focused contract, aggregate, schema, migration, database-role,
repository and direct-SQL guard suites. MODIFY only exact existing migration-
head assertions whose authoritative repository-head expectation changes to
`e04300000001`; preserve every e041 historical parent assertion.

### Evidence and stop

Canonical digest vectors; malformed/oversize/type/name/plaintext negative
tests; lifecycle/terminal/lineage; exact schema matrix; clean upgrade,
downgrade, re-upgrade; sole head; direct-SQL cross-scope/link/immutability/
transition bypass, including withdrawn→proposed Evidence remaining link-sealed;
runtime DDL/trigger/function denial; repository ordering and
bounds; adjacent migration regression; static/import and diff checks.

Stop for head drift, a required EDS/IDS change, ungoverned shared-schema/role
change, foreign repository access or a later-batch dependency.

## 3. Batch 2 — Object data plane, upload, scan, withdrawal and reconciliation (S05–S08)

### Scope

- **S05:** reviewed SDK/type-inspection dependencies, protected configuration,
  S3-compatible exact-key adapter and scanner adapter;
- **S06:** upload reservation, streaming/finalization and idempotency;
- **S07:** scan retry/completion and explicit withdrawal;
- **S08:** reconciler, Audit/outbox, rollback/failure and concurrency.

### Expected production surfaces

CREATE `backend/app/adapters/supporting_file_object_store.py`,
`backend/app/adapters/supporting_file_scanner.py`,
`backend/app/repositories/supporting_file_unit_of_work.py`,
`backend/app/services/supporting_file_service.py`,
`backend/app/services/supporting_file_reconciliation_service.py`.
MODIFY `backend/app/core/config.py`, `backend/pyproject.toml`,
`backend/requirements.txt`, `backend/requirements.production.lock`,
`backend/uv.lock`, `backend/Dockerfile.production`,
`docker-compose.production.yml`, `.env.example` if present, and the Batch-1
repository/port files only for accepted collaborator closure. No router.

### Expected tests

CREATE storage-adapter, scanner, upload/service, transaction, reconciliation,
security and concurrency suites. MODIFY operations configuration/topology/
security tests only for the new separately mounted application/scanner/
reconciler principals and preserved PATCH-042 separation.

### Evidence and stop

Stream boundaries; digest/type/container verification; conditional create;
IAM/no-list/no-public/no-overwrite static policy; object/DB failure matrix;
clean/unsafe/timeout/unavailable/stale scan; retry; idempotent replay;
one-winner finalize/scan/withdraw; Audit/outbox rollback; orphan/missing object;
no protected logs/keys/content.

Stop if an object-store SDK/credential cannot be separately bounded, public or
presigned access becomes necessary, scanner cannot bind exact digest, object
listing is required, or a real external dependency is falsely represented as
locally proven.

## 4. Batch 3 — Evidence, Report, Memory and recovery integration (S09–S12)

### Scope

- **S09:** proposed-Evidence link command, same-scope final lock/recheck and
  Evidence version/Audit/outbox behavior;
- **S10:** EvidenceHistoricalBasisV2, file historical basis serialization,
  candidate composition and Report acceptance final recheck/race;
- **S11:** Memory provenance authorization compatibility and historical
  download authorization without byte ownership;
- **S12:** PATCH-042 object-inclusive recovery-set manifest/restore consistency.

### Expected production surfaces

MODIFY exact Evidence enum/model/command/schema/port/repository/UoW/service files;
Technical Report command/model/schema/port/service/repository/UoW and router
candidate-adapter surfaces; Organizational Memory adapter/port/service only as
required for Evidence V2 provenance authorization; Supporting File port/service/
repository for same-Session collaborators; `ops/scripts/backup.sh`,
`ops/scripts/restore-verify.sh`, recovery manifest schema/example and production
configuration only for consistent object participation. CREATE a bounded
Technical Report Evidence-source adapter if current composition cannot remain
thin without it.

### Expected tests

MODIFY/add Evidence contract/service/transaction/security/API tests; Technical
Report contract/service/transaction/security/API/migration tests; Memory
integration/security tests; recovery/operations tests. Add V1 regression and
V2 digest vectors, same-scope matrix, link concurrency, acceptance/withdrawal
race, accepted snapshot immutability, historical retrieval and inconsistent
restore denial.

### Evidence and stop

No direct foreign repository/UoW import; one Session during Evidence mutation
or Report acceptance; exact available final check; Evidence V1 unchanged;
Supporting File is nested only in Evidence V2; accepted Report and Memory
regressions; object-inclusive recovery set. Stop if Technical Report authority,
Evidence lifecycle, Memory admission semantics or PATCH-042 recovery authority
must change.

## 5. Batch 4 — Read/API/composition and protected delivery (S13–S14)

### Scope

- **S13:** request-scoped composition, list/status/active/historical download,
  bounded pagination and trusted scope;
- **S14:** thin authenticated routes, scan internal route, exact protected
  translation and router registration.

### Expected production surfaces

CREATE `backend/app/dependencies/supporting_file.py`,
`backend/app/api/v1/routers/supporting_files.py` and focused API/composition
tests. MODIFY `backend/app/main.py`, Supporting File service/repository/schema,
Evidence router and Technical Report router only for accepted routes. Modify
edge/Nginx limits only if needed to enforce the accepted 25 MiB + protocol
overhead without exposing direct object access.

### Evidence and stop

All exact routes; request-scoped one-UoW composition; server-derived actor/
Organization; cross-scope injection; protected discriminator-only errors;
attachment/nosniff/no-store/filename/MIME/range; continuation tamper/context/
expiry/last-evaluated behavior; no totals; max rounds/evaluated rows; internal
scanner authentication; prohibited route scan.

Stop for router-owned repository/Session/policy, unbounded scanning, direct
object URL, unsafe inline rendering, or a new transport/domain semantic.

## 6. Batch 5 — Bounded product UI (S15–S16)

### Scope

- **S15:** typed API client and Project/Workspace Supporting Evidence upload,
  list/status, Evidence linkage and truthful states;
- **S16:** Report Evidence candidates, safe file provenance/historical download,
  accessibility and responsive behavior.

### Expected production surfaces

MODIFY `frontend/src/api/types.ts`, `frontend/src/api/client.ts`,
`frontend/src/pages/ProjectsPage.tsx`, `frontend/src/pages/ReportPages.tsx`,
`frontend/src/styles.css`; CREATE `frontend/src/components/SupportingEvidencePanel.tsx`.
Modify focused Project/workflow/report/API/responsive tests and add one
supporting-evidence UI/security test. `App.tsx`/AppShell must remain unchanged
unless an exact non-global route is demonstrably required; no file navigation
item is planned.

### Evidence and stop

Real API only; no fake production Assets/counts/results; authorized selectors;
upload progress/status; proposed Evidence link; server-composed provenance;
protected/loading/invalid/unavailable/empty/success; keyboard/labels/live region/
focus/touch/contrast; wide/reduced/narrow; long filename/no overflow; existing
Command Center/report behavior regression.

Stop for global file manager, client-authored scope/provenance, inline unsafe
rendering, fake data, AI/OCR/search or accepted Experience-boundary change.

## 7. Batch 6 — Regression, operations evidence and final review package (S17–S19)

### Scope

- **S17:** all focused suites, adjacent Evidence/Report/Memory/Project/auth/Audit/
  operations regressions, full backend/frontend, migration, static/type/build,
  security/scope/secrets/fake-data and QG-M1;
- **S18:** deployment-conditional object IAM/scanner/recovery evidence with local
  versus external results explicitly separated;
- **S19:** reproducible validation and Independent Final Review artifacts;
  PATCH status advances only to final-review readiness.

### Expected docs/evidence surfaces

CREATE `docs/reviews/PATCH-043-Implementation-Validation-Evidence.md` and
`docs/reviews/FR-043-Governed-Supporting-File-Evidence-Intake.md`; MODIFY only
`docs/patches/PATCH-043.md` for readiness metadata. Exact manifests and batch
review/Human-acceptance records are append-only governance surfaces. No
production/test remediation is authorized by Batch 6; a technical failure
stops for separately bounded authority.

### Evidence and stop

Commands/counts/environment/revision are reproducible; all historical FAIL →
remediation → re-review chains are preserved; external IAM/scanner/TLS/backup
proof is not fabricated. Stop on any failed gate, unresolved Critical/Major,
scope leakage, missing migration guard, recovery inconsistency or external
deployment prerequisite required for the claimed review state.

## 8. Dependency and review gates

Batch 1 precedes all code. Batch 2 depends on its contracts/persistence. Batch
3 depends on real Asset operations and completes canonical provenance before
transport/UI. Batch 4 depends on application and integration behavior. Batch 5
depends on stable APIs. Batch 6 depends on Human acceptance of Batches 1–5.

Each manifest must re-read current head/worktree, minimize exact files, list
CREATE/MODIFY responsibility, tests, prohibited patterns and stop conditions.
Each implementation stops on any out-of-manifest requirement. Each Independent
Review is review-only. No later batch starts before Human acceptance of the
previous batch.

## 9. Deferred-boundary control

All PATCH-043 deferred capabilities remain excluded from every batch. In
particular, no EDMS hierarchy/editing, OCR, semantic/vector search, AI file
analysis, customer external storage, broad retention/purge administration,
Procurement/Product Completion feature or Commercial V1 Release Certification
is a dependency or deliverable.

## 10. Focused scanner-security reconciliation

The accepted IDS scanner-security amendment closes implementation mechanics
already required by S05-S08. Batch 2 additionally implements a dedicated
secret-file scanner credential verifier, the server-created scanner-only
principal, provider-neutral result identity, authenticated result recording,
durable replay protection and the accepted maximum-three-attempt retry
orchestration. The token follows PATCH-042 secret-file rotation/revocation;
no customer, Organization, engineering or object-store authority is conferred.

This clarification does not change batch order or scope. It reconciles Batch 2
to include the existing Supporting File model/migration, repository/UoW,
configuration/topology and focused migration/transaction/security tests needed
to enforce the amended contract. Batch 4 still owns the thin internal route and
request-scoped composition. Architecture and EDS semantics are unchanged.
