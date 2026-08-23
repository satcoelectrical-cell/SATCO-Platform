# IDS-043 — Governed Supporting File Evidence Intake

## 1. Status, authority and repository baseline

**ACCEPTED / COMPLETE.** This IDS implements PATCH-043 and accepted EDS-043.
Implementation authority is not granted. Repository baseline is branch
`patch-022.3a-development-infrastructure`, HEAD
`3d17ce187a343f382d3bea393ad1642932168b28`, Alembic sole head
`e04100000001`.

Existing canonical integration must use application-owned ports and services.
Supporting File code may not query Project, Workspace, Evidence, Technical
Report or Memory tables directly except its own foreign-key/coherence guards in
the migration/repository. Evidence and Report integrations execute through
their owning application services with injected Supporting File collaborators.

## 2. Closed V1 vocabulary and limits

```text
SupportingFileLifecycle = quarantined | available | rejected | withdrawn
UploadReservationStatus = reserved | streaming | uploaded | consumed | failed | expired
ScanDisposition = clean | unsafe | indeterminate
DigestAlgorithm = sha256
StorageState = present | unavailable | missing | mismatch
```

Limits:

- maximum file size: 25 MiB (26,214,400 bytes), minimum one byte;
- filename: normalized display value 1–255 Unicode code points and safe ASCII
  fallback 1–120 bytes;
- media types: `application/pdf`, `text/plain`, `text/csv`, `image/png`,
  `image/jpeg`, OOXML Word and OOXML Spreadsheet;
- extensions are hints only; signature/container validation must match the
  selected media type; executables, macros, scripts, archives other than
  validated OOXML, HTML/SVG and polyglots are rejected;
- one active upload stream per reservation, maximum four concurrent streams
  per actor and sixteen per Organization;
- scan attempt timeout 120 seconds, three attempts with bounded exponential
  delay, never automatic promotion;
- maximum ten Assets per Evidence, unique and ordered by Asset UUID;
- list page 1–50, at most five repository scans and 100 evaluated rows;
- opaque continuation expiry 15 minutes;
- Audit rationale/details maximum 2 KiB canonical JSON and no file content.

## 3. Typed domain and result contracts

### 3.1 Trusted context and scope

`SupportingFileActor(actor_id: PositiveInt, organization_id: UUID,
role: admin|engineer)` is built from `AuthenticatedOrganizationContext` only.
`SupportingFileScope(organization_id, project_id: PositiveInt,
workspace_id: PositiveInt|None)` is server-verified. The Organization in a
request body is forbidden.

### 3.2 Asset and reservation identities

`SupportingFileAssetId`, `UploadReservationId`, `ScanAttemptId`,
`IdempotencyId`, `CorrelationId` and `EventId` are non-nil UUIDs. Object keys
are `OpaqueStorageKey` internal values of `objects/<64 lowercase hex>`; the hex
is 256 random bits and never derived from another identity. One exact object is
written once and is never moved or overwritten when lifecycle changes.
Quarantine/availability is canonical database state, not a mutable key prefix.
The key is absent from outward DTOs, Audit, logs and events.

`ContentDigest` is lowercase 64-hex SHA-256. `SupportingFileSummary` contains
asset_id, scope, safe filename, media type, byte size, digest algorithm/digest,
lifecycle, version, uploader_id, uploaded_at, scanned_at, predecessor_asset_id
and allowed_actions. It contains no key or scan diagnostic.

### 3.3 Commands

- `UploadSupportingFile(actor, scope, safe_filename, declared_media_type,
  predecessor_asset_id?, rationale, correlation_id, idempotency_id)` consumes
  one server-owned stream; bytes are never a command DTO field.
- `RecordSupportingFileScan(principal, asset_id, asset_version, attempt_id,
  object_fingerprint, disposition, engine_id, signature_set_id, observed_at,
  correlation_id)` is an internal authenticated contract.
- `WithdrawSupportingFile(actor, asset_id, expected_version, rationale,
  correlation_id, idempotency_id)`.
- `LinkEvidenceSupportingFiles(actor, evidence_id, expected_evidence_version,
  asset_ids[1..10], rationale, correlation_id, idempotency_id)` is owned by the
  Evidence application boundary.

### 3.4 Reads

- `GetSupportingFile(actor, asset_id)`;
- `ListSupportingFiles(actor, scope, lifecycle?, continuation?, page_size)`;
- `DownloadActiveSupportingFile(actor, asset_id)`;
- `DownloadHistoricalSupportingFile(actor, report_id, evidence_id, asset_id)`;
- `ResolveSupportingFileHistoricalBasis(actor, report_scope, evidence_id,
  evidence_version, asset_ids, operation)` for Technical Report composition.

### 3.5 Closed results

Each operation has one discriminated union. Success is operation-specific.
Non-success variants are exact payload-free records:

`protected_not_found`, `invalid_request`, `version_conflict`,
`idempotency_conflict`, `unavailable`.

Authorized upload success returns one quarantined summary. Authorized scan
status is disclosed only through summary. List success contains `items`,
`visible_count`, `continuation`; no total. Download success is an internal
`AuthorizedFileStream(asset_id, safe headers, content_length, stream_factory)`;
the transport never serializes it as JSON. No protected variant may include
IDs, filename, lifecycle, scan reason, count, error or retry state.

## 4. Persistence model and migration

One additive migration `e04300000001_supporting_files.py`, parent
`e04100000001`, creates:

### 4.1 `supporting_file_assets`

| Column | Type/nullability |
|---|---|
| `id` | UUID PK, non-null |
| `organization_id` | UUID FK organizations RESTRICT, non-null |
| `project_id` | integer FK projects RESTRICT, non-null |
| `workspace_id` | integer FK engineering_workspaces RESTRICT, nullable |
| `safe_filename` | varchar(255), non-null |
| `safe_ascii_filename` | varchar(120), non-null |
| `media_type` | varchar(128), non-null |
| `byte_size` | bigint, non-null, 1..26214400 |
| `digest_algorithm` | varchar(16), non-null, `sha256` |
| `content_digest` | char(64), non-null lowercase hex |
| `storage_key` | varchar(80), non-null, UNIQUE, exact opaque-key shape |
| `object_version` | varchar(160), non-null, protected provider version/etag token |
| `uploader_id` | integer FK users RESTRICT, non-null |
| `lifecycle` | varchar(16), non-null |
| `predecessor_asset_id` | UUID self FK RESTRICT, nullable |
| `version` | integer non-null >=1 |
| `uploaded_at` | timestamptz non-null |
| `scan_requested_at` | timestamptz non-null |
| `scanned_at` | timestamptz nullable |
| `withdrawn_at/by/reason_code` | terminal-only nullable group |
| `created_at/updated_at` | timestamptz non-null |

Unique exact byte identity is not global deduplication: distinct authorized
uploads may share a digest but retain distinct Asset identity/provenance.
Indexes cover `(organization_id, project_id, workspace_id, uploaded_at DESC,
id ASC)`, lifecycle, digest and predecessor.

Database function `satco_validate_supporting_file_scope()` locks Project and
Workspace rows and rejects cross-Organization Project, Workspace not in Project
and immutable scope drift. Function `satco_guard_supporting_file_transition()`
rejects every change except exact lifecycle/version/audit terminal fields:
quarantined→available|rejected and available→withdrawn. It checks one version
increment, required/forbidden timestamps, terminal immutability and
predecessor same Organization/Project/Workspace compatibility. An immutable-
field trigger rejects direct SQL changes to bytes metadata, key, scope,
uploader, upload time and predecessor. DELETE is denied.

The migration also adds nullable timestamptz
`evidence.supporting_file_links_sealed_at`. It is initially null for every
legacy/reference-only Evidence row. The Evidence transition persistence guard
sets it exactly once whenever proposed Evidence first leaves `proposed`,
including transition to current, withdrawn or rejected; later lifecycle
changes, including withdrawn→proposed, cannot clear it. Direct SQL cannot set
it back to null or change it. This durable marker, rather than current lifecycle
alone, proves that the link set has become immutable.

### 4.2 `supporting_file_upload_reservations`

UUID PK; actor/Organization/Project/Workspace; safe filename; declared media;
temporary opaque key UNIQUE; status; expected/max size; actual size/digest/type
nullable only until `uploaded`; provider upload/version tokens encrypted or
protected; expires_at; attempt_count; asset_id nullable unique FK; failure code
from a closed safe enum; idempotency key/fingerprint; timestamps. Checks enforce
status-specific field closure. No content or exception plaintext. Reservations
are mutable only through exact state transitions and may be purged after 24
hours when failed/expired/consumed and no referenced object remains.

### 4.3 `evidence_supporting_file_links`

`evidence_id` FK Evidence RESTRICT, `asset_id` FK Asset RESTRICT, Organization,
Project, Workspace, evidence_version, ordinal 0..9, linked_by/at. Composite PK
Evidence+Asset, unique Evidence+ordinal. A SECURITY DEFINER trigger owned by
schema owner locks both rows and rejects: non-proposed Evidence, Asset not
available, Organization/Project mismatch, incompatible Workspace, evidence
version mismatch, duplicate/over-limit set, non-null
`supporting_file_links_sealed_at`, or direct SQL mutation/deletion after the
link set has been sealed. The trigger can read only required scope/state
columns and exposes no outward data.

### 4.4 Scan/outbox/idempotency

`supporting_file_scan_attempts`: attempt UUID PK, Asset FK, expected version,
object fingerprint/digest, attempt number 1..3, state requested|completed|
failed, protected engine/signature references, safe disposition, timestamps;
unique Asset+attempt number and attempt UUID. Runtime cannot rewrite completed
attempts.

`supporting_file_outbox`: event UUID unique, aggregate UUID FK, positive
aggregate version, closed event type, canonical bounded JSONB payload, occurred/
published timestamps. JSON validation rejects unknown keys, keys/filenames/
content/credentials and >2 KiB payload.

`supporting_file_idempotency`: Organization, actor, unversioned operation,
idempotency UUID, SHA-256 fingerprint, pending|completed, Asset/reservation IDs,
closed versioned stored-success JSON <=1 KiB, timestamps; unique
Organization+actor+operation+key. Stored results contain only IDs, version,
lifecycle and immutable safe summary fields needed for replay; no key, scan
diagnostic, content or rationale. Replay reauthorizes before reconstruction.

### 4.5 Role separation

Migration/schema owner `satco` owns tables/functions/triggers. Runtime
`satco_runtime` receives only enumerated DML and function EXECUTE; no DDL,
TRIGGER, function replacement, ownership, role grant or row-security bypass.
Application object credential can create/abort exact quarantine objects, HEAD
exact known keys, and GET exact available keys through adapter policy; it has
no list-bucket, public ACL, policy change, broad delete or overwrite grant.
Scanner principal reads exact scan-request objects and attests the same exact
immutable object/version; it cannot move/overwrite it, list, or call application
APIs except the authenticated scan-result endpoint. Reconciler delete applies
only to exact
temporary/rejected keys after database recheck. Operational recovery principal
remains PATCH-042-owned and separate.

## 5. Storage, streaming and type verification

Add one inward `SupportingFileObjectStore` port:

```text
begin_quarantine(key, max_bytes) -> UploadHandle
write_chunk(handle, bytes) -> None
complete(handle, sha256, byte_size) -> ObjectReceipt(key, version, size, digest)
abort(handle) -> None
head_exact(key, version) -> ObjectObservation|unavailable|missing
open_exact(key, version, byte_range?) -> ByteStream|unavailable|missing
delete_temporary_exact(key, version) -> deleted|missing|unavailable
```

The S3-compatible adapter uses a reviewed pinned SDK dependency, path-style or
virtual-host addressing from protected configuration, TLS verification and
conditional create. It never lists. Provider ETag is not a content digest.
SHA-256 is calculated by the backend streaming pipeline and verified against
object metadata/receipt; scan completion re-verifies it. Keys are never logged.

Multipart threshold is 8 MiB with 8 MiB parts; the backend reads at most 1 MiB
per application chunk, never buffers the whole file, aborts on 25 MiB+1 and
uses request/body timeouts. Type validation uses magic/container inspection
and OOXML package allow-list; browser MIME and extension alone never pass.

No presigned/public URLs. Downloads are server-mediated from an exact key after
authorization and HEAD/digest check. Headers: attachment-only safe
Content-Disposition, exact validated Content-Type, Content-Length,
`X-Content-Type-Options: nosniff`, `Cache-Control: private, no-store`, no object
metadata. A mismatch raises unavailable and reconciliation/incident evidence.

## 6. Scanner protocol and reconciliation

`SupportingFileScanner.request(ScanRequestV1)` sends an authenticated internal
request containing attempt UUID, opaque retrieval handle, expected object
version/size/digest and callback nonce; no business scope/filename/Evidence or
Report identity. `ScanResultV1` is signed/mTLS authenticated and binds attempt,
object fingerprint, engine/signature IDs, disposition and observed time.

Clean is accepted only when engine/signature policy is current and exact object
digest matches. Unsafe transitions to rejected. Indeterminate, timeout,
dependency failure or malformed/stale result records a safe failed attempt and
retries up to three; lifecycle remains quarantined. Internal endpoint rate and
body are bounded. Ordinary authenticated users cannot call it.

`SupportingFileReconciler` scans database reservations, never bucket contents.
It may HEAD/delete only stored exact temporary keys. It resolves stale
reserved/streaming/uploaded records, consumes completed finalizations, removes
verified orphans and flags missing/mismatched canonical objects. It cannot
create/promote/withdraw/link Assets. Every action is idempotent and Audit-
recorded. A missing canonical object never changes Asset lifecycle; reads fail
unavailable and an incident is raised.

## 7. Application services and transaction sequencing

Repositories never commit or authorize. `SupportingFileUnitOfWork` exposes
assets, reservations, scan attempts, links-read support, Audit, outbox,
idempotency and one SQLAlchemy Session.

Upload uses reservation transaction → external stream → finalization
transaction. Finalization order: lock reservation; current scope reauthorize;
HEAD exact object; validate receipt/digest/type/size; reserve idempotency; create
quarantined Asset; consume reservation; persist Audit/outbox/scan attempt/stored
result; commit; publish scan request after commit. Publication failure leaves a
recoverable outbox item, not a promoted Asset.

Scan order: authenticate principal; lock attempt+Asset; verify expected
version/object; persist attempt outcome; apply exact Aggregate transition;
Audit/outbox; commit. Withdrawal: reserve idempotency; lock Asset; current
scope/uploader-or-admin reauthorization; expected-version check; transition;
Audit/outbox/stored result; commit. Version conflict is distinct from protected
denial and creates no rejection Audit. Failed transactions roll back fully;
post-rollback rejection Audit is separate, bounded and best-effort, and its
failure cannot resurrect primary state.

Evidence link is an Evidence command. EvidenceService reserves its own
idempotency, locks proposed Evidence, calls the canonical Supporting File
`authorize_and_lock_for_evidence` collaborator using the same Session, validates
the deterministic exact set, advances Evidence version, stages links plus
Evidence Audit/outbox/result and commits once.

Technical Report historical resolver is a canonical Supporting File application
collaborator composed with the Technical Report UoW Session. At draft source
composition it returns the closed basis. At acceptance it locks/rechecks each
Asset until Report commit. It does not mutate Assets and performs no bucket
listing. Withdrawal waits on those row locks; therefore either acceptance sees
available exact bytes and commits first or withdrawal wins and acceptance
fails. This closes the TOCTOU boundary without Technical Report importing a
file repository. Candidate composition and acceptance reject the entire
Evidence source unless every linked Asset has the Report's Project and has
either null Workspace or the exact Report Workspace.

## 8. Evidence and Technical Report schema evolution

Add `EvidenceHistoricalBasisV2`, selected only when file links are material.
It retains every V1 field unchanged and adds required
`supporting_files: tuple[SupportingFileHistoricalBasisV1, 1..10]`. V1 remains
valid for reference-only Evidence. The new basis uses literal schema version 2
and source category evidence; no optional ambiguous file field is added to V1.

`SupportingFileHistoricalBasisV1` exact fields:

`basis_schema_version=1`, `source_category=supporting_file`, asset UUID,
asset_version, Organization UUID, Project int, optional Workspace int,
safe_filename, media_type, byte_size, digest_algorithm=`sha256`, content_digest,
uploader_id, uploaded_at, predecessor_asset_id optional. Deterministic canonical
JSON uses sorted keys, UTF-8, NFC strings, lowercase UUID/digest, UTC `Z`
microsecond timestamps, decimal integers, no whitespace. File tuple is sorted
by Asset UUID. `historical_basis_digest` and accepted snapshot digest bind it.

Technical Report provenance remains source_type `evidence` and owning
capability Evidence; Supporting File is nested historical basis, not a fifth
direct Report source. The provenance persistence JSON validator accepts closed
Evidence V1 or V2 only. Acceptance final-recheck understands V2. Accepted V1
snapshots remain readable and byte-for-byte immutable.

Memory provenance authorization recognizes Evidence V2 only through the
accepted Technical Report adapter, independently authorizes each referenced
Asset identity through Supporting File application contracts, and preserves
all-or-nothing disclosure. Its admitted projection remains the exact accepted
Report snapshot; no Memory table change or file content is added.

## 9. HTTP transport

Authenticated routes are exactly:

- `POST /supporting-files/uploads` multipart (`file`, project_id,
  workspace_id?, predecessor_asset_id?, rationale), headers correlation and
  idempotency;
- `GET /projects/{project_id}/supporting-files` with optional workspace,
  lifecycle, page size and continuation;
- `GET /supporting-files/{asset_id}` safe metadata;
- `GET /supporting-files/{asset_id}/download` active attachment stream;
- `POST /supporting-files/{asset_id}/withdrawals` expected_version+rationale;
- `POST /evidence/{evidence_id}/supporting-files` exact link command;
- `GET /technical-reports/evidence-source-candidates` bounded server-composed
  Evidence provenance choices;
- `GET /technical-reports/{report_id}/evidence/{evidence_id}/supporting-files/{asset_id}/download`
  historical attachment stream;
- one private authenticated `/internal/supporting-files/scan-results` endpoint.

No generic update/delete, public URL, bucket/key, inline-view, search, folder,
OCR or AI route. Routers parse/serialize only and depend on request-scoped
application composition. Multipart validation failures translate to exact
payload-free invalid_request. Cross-scope/missing/denied translates to
protected_not_found. Storage/scanner failures translate to unavailable.

Continuation is encrypted and MAC-authenticated with a dedicated key, version
`supporting-file-list.v1`, issued/expiry, actor/Organization/Project/Workspace,
filters/page and last evaluated `(uploaded_at DESC, id ASC)` key. Decode verifies
canonical text, authentication, version/context/expiry before any repository
read. Denied rows count toward evaluated bound and advance the continuation;
no skip/duplicate or protected total results.

## 10. UI implementation design

Add typed API contracts/client methods and a `SupportingEvidencePanel` inside
the existing Project detail context. It receives server-authorized Project and
Workspace selectors, supports one explicit file input (not drag-only), reports
progress/status through ARIA live regions and refreshes real results. It shows
the non-authority notice and type/size rules.

Add proposed Evidence authoring/link selection in the same context, using only
server-returned available Assets. Technical Report authoring adds a separate
authorized Evidence candidate group; client cannot construct or edit its
provenance. Accepted Report detail renders safe Evidence/file provenance and
uses only server-authorized historical download links.

Protected state uses the existing generic ProtectedState; unavailable and
invalid are distinct. No placeholder/demonstration file objects. CSS stacks the
panel below primary Project surfaces at narrow widths, preserves focus order,
wraps long filenames and prevents horizontal overflow. Tests cover label,
keyboard, focus, live status, contrast/status text, 1440/wide/narrow layouts and
touch targets.

## 11. Audit, logging, metrics and recovery

Shared `AuditLog` mapping:

- `user_id`: Human actor ID, nullable only for authenticated scanner/reconciler;
- `action`: `SUPPORTING_FILE_UPLOAD_FINALIZED`, `SCAN_AVAILABLE`,
  `SCAN_REJECTED`, `SCAN_RETRY`, `WITHDRAWN`, `EVIDENCE_LINKED`,
  `HISTORICAL_DOWNLOAD`, `RECONCILIATION_REQUIRED|COMPLETED`;
- `entity`: `SUPPORTING_FILE_ASSET`;
- `entity_uuid`: Asset UUID when canonical; null for pre-Asset reservation
  rejection;
- `details`: Organization, correlation, versions, safe operation/category,
  byte-size bucket, digest prefix no longer than 12 hex only where operationally
  required, outcome and bounded rationale code. Never filename, bytes, key,
  full digest, credential, malware signature or exception.

Application logs/metrics use operation, outcome category, latency/size bucket,
retry number and opaque correlation only. Metrics include upload/scan/download
counts and latency, quarantined age buckets, mismatch/orphan counts and storage/
scanner availability; no customer identity/filename/key/content labels.

PATCH-042 `recovery-set.v1` changes object component from `verified_empty` to an
inventory/cutoff manifest digest covering every canonical object key hash,
provider version, size/digest and database cutoff, encrypted and visible only
to recovery operators. Restore verification compares the database and object
manifest without exposing it to runtime. This is a PATCH-042 integration point,
not a transfer of recovery authority.

### 11.1 Focused scanner-principal security reconciliation

The internal scan-result endpoint uses one dedicated service credential read
only from `SUPPORTING_FILE_SCANNER_TOKEN_FILE`. Production requires a distinct,
high-entropy value of at least 32 bytes delivered through the PATCH-042
read-only secret-file mechanism. The endpoint dependency reads the configured
value server-side and verifies the scanner header with constant-time comparison.
Missing, unreadable, weak, mismatched or revoked material fails closed before
attempt/Asset lookup. Rotation stages a new secret reference and restarts the
scanner/backend consumers before the old reference is revoked; no value or
header is logged, audited, returned or included in support evidence.

Successful verification creates the immutable application value
`SupportingFileScannerPrincipal(principal_id="supporting-file-scanner-v1")`.
It carries no Organization, user, role or customer authority. Organization is
resolved only from the durable attempt and Asset. Its sole permission is
`record_supporting_file_scan`; it cannot reserve/upload/read/download/withdraw,
link Evidence, accept Reports, admit Memory, enumerate objects or exercise
Human/engineering authority.

`RecordSupportingFileScan` is the only result-recording boundary. Its closed
request contains principal, Asset UUID/version, explicit attempt UUID, exact
lowercase SHA-256 object fingerprint, disposition, bounded provider-neutral
`engine_id` and `signature_set_id`, aware `observed_at`, and non-nil correlation
UUID. After principal verification, one UoW locks the exact attempt and Asset,
then checks attempt ownership, Organization derived from persistence, expected
Asset version, immutable digest, current attempt ordinal, eligible quarantined
lifecycle and requested state. Provider fields originate only from this
authenticated integration request and are never accepted from customer APIs.

The exact first result completes the requested attempt and atomically applies
only the permitted safety transition, Audit and outbox. Exact duplicate
delivery is idempotent when every result field matches. A conflicting duplicate,
wrong/stale attempt, wrong version/fingerprint, superseded ordinal, terminal
Asset, malformed/missing provider identity or revoked credential is rejected
without mutation or protected disclosure. Scanner Audit records only principal
ID, attempt/result/correlation IDs, safe disposition, versions and bounded
provider references; never key, filename, bytes, full digest, credential or
diagnostic plaintext.

Unavailable, timeout, indeterminate and dependency failure complete the attempt
as failed/retryable while the Asset remains quarantined. Retry orchestration
locks the Asset and latest attempt, permits only ordinals 1→2→3, creates one
new requested attempt bound to the same Asset version and immutable fingerprint.
The retry command supplies the expected currently failed attempt ordinal and
the locked latest ordinal must match; concurrent replay therefore has one
winner and cannot consume two retry ordinals. Each accepted retry publishes one
scan-request outbox event. Database uniqueness on
`(asset_id, attempt_number)` provides one-winner concurrency. Clean and unsafe
are non-retryable; three failed attempts are exhausted and no fourth attempt is
created. Previous attempts are immutable. Transaction, Audit or outbox failure
rolls back attempt/lifecycle/result changes completely.

This section is an implementation-mechanics amendment within the already
accepted EDS requirement for authenticated, attributable, bounded scanner-only
authority. It creates no new EDS authority or product capability.

## 12. Expected implementation surfaces

Production will require new Supporting File enum/model/schema/port/exception,
repository/UoW/service/adapter/dependency/router modules and one migration;
bounded changes to Evidence, Technical Report, Organizational Memory adapters/
contracts; configuration/dependency lock, production Compose secret mounts,
recovery scripts/manifests; frontend API/types/Project/Report components/styles.
No new generic storage framework, EDMS module, AI service or Memory persistence
is authorized.

## 13. Verification matrix

| Invariant | Executable evidence |
|---|---|
| migration/role/DB guards | clean upgrade/downgrade/re-upgrade; sole head; schema matrix; direct-SQL immutable/scope/lifecycle/link bypass; runtime DDL/trigger denial |
| streaming integrity | 0, exact max and max+1; disconnect/abort; digest/type/container mismatch; memory-bound streaming; conditional create/no overwrite |
| saga/reconciliation | object-first DB failure, DB-first object failure, orphan/missing/mismatch, idempotent reconciler, no fabricated Asset |
| scan safety | clean/unsafe/timeout/unavailable/stale/malformed/digest mismatch; retries; no default promotion; scanner has no domain authority |
| authorization | cross-Organization/Project/Workspace, disabled membership, protected fields/counts/scan reasons/key/errors; replay/current reauth |
| Evidence linkage | same-scope matrix, proposed-only, available-only, 10 limit/order/dedup, final lock/recheck, one Evidence version increment |
| Report/Memory | V1 regression, V2 canonical digest vectors, final Asset recheck/race, accepted immutability, withdrawal/new-reliance denial, historical authorized retrieval, Memory all-or-nothing provenance |
| concurrency/reliability | duplicate upload/finalize/scan/withdraw/link; one winner; version conflict; atomic Audit/outbox/idempotency; rollback injections |
| download security | no public/presigned URL/key, attachment/nosniff/no-store, filename injection, MIME confusion, range reauth, storage outage/missing object |
| pagination | order/tie, last-evaluated anchor, context/tamper/expiry binding, hidden denied rows, bounds/no totals/no skip/duplicate |
| UI | real API only; empty/loading/protected/error/success; upload/link/report flow; keyboard/labels/live status/focus; wide/reduced/narrow responsive |
| operations/recovery | principal IAM allow/deny, no list/public ACL, health and scanner separation, object-inclusive recovery-set consistency, external-evidence classification |
| regression/scope | Evidence/Report/Memory/Project/auth/Audit/PATCH-042 adjacent and full suites; static/type/build; secret/prohibited-pattern and fake-data scan; `git diff --check`; QG-M1 |

## 14. Stop conditions and unresolved questions

Stop implementation if current head is not `e04100000001`; canonical Project/
Workspace/Evidence/Report services cannot supply required current authorization;
same-Session final locking cannot be composed without direct foreign ownership;
object IAM cannot deny list/public/overwrite; scanner authentication cannot bind
exact object/digest; recovery cannot produce a consistent DB/object set; a
public/presigned URL is required; or accepted PATCH/EDS semantics must change.

There are no unresolved design questions. Deployment-specific object endpoint,
credentials, real scanner, TLS, backup target and monitoring remain named
external prerequisites and must be verified at their implementation/delivery
gates, not fabricated during local development.
