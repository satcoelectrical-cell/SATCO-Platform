# EDS-043 — Governed Supporting File Evidence Intake

## 1. Status and authority

**ACCEPTED / COMPLETE.** This EDS implements only the accepted PATCH-043
Architecture. It changes no accepted Evidence, Technical Report,
Organizational Memory or PATCH-042 operational authority. Exact implementation
mechanisms are delegated to IDS-043.

## 2. System context and ownership

Supporting File Asset is a dedicated canonical Aggregate Root. It owns file
identity and operational standing, not engineering truth. Its authoritative
state consists of:

- immutable Asset identity and positive version;
- trusted Organization and required Project, plus optional Workspace;
- immutable safe filename, verified media type, byte size and content digest;
- immutable opaque private object identity;
- uploader and upload/scan timestamps;
- zero-or-one predecessor identity;
- exact lifecycle and lifecycle-transition attribution.

PostgreSQL is authoritative for this state. The private object store is
authoritative only for exact immutable bytes under the opaque object identity.
Neither an object, bucket, key, scanner result, upload nor Asset standing is an
engineering fact, Evidence approval, Technical Report acceptance or Memory
admission.

Evidence remains the PATCH-027 metadata Aggregate. It may remain reference-
only. A bounded Evidence-owned association records that one exact proposed
Evidence version references one or more Assets. The association owns no bytes
and the Asset owns no Evidence meaning. Technical Report owns only its report-
specific reliance manifest and immutable accepted snapshot. Organizational
Memory owns only its accepted-Report projection and retains no file bytes.

## 3. Scope and authority

Organization is always derived from the authenticated server context. Project
is required and must be a current canonical Project in that Organization.
Workspace is optional; when present it must be a current canonical Workspace of
that Project. Browser values are selectors only and confer no authority.

The application reuses the existing Project/Workspace access semantics:
Organization admin, current Project owner/primary assignee and current
authorized Workspace owner/assignee/member as applicable. It does not infer
access from a filename, object key, Evidence reference, Report or URL.

Operation rules are:

| Operation | Additional rule after current scope authorization |
|---|---|
| reserve/upload/finalize | current scope participant; actor becomes immutable uploader |
| status/list/active download | current scope participant; lifecycle must permit the operation |
| link to Evidence | current scope participant with Evidence-create/edit authority; both resources pass exact scope compatibility |
| withdraw | uploader or Organization admin, still currently authorized to the Asset scope |
| replacement upload | ordinary upload authority; predecessor must be authorized, available or withdrawn, and exact-scope compatible |
| historical download | current authorization to the accepted Report and Asset scope, with exact accepted basis identity/digest match |
| scan completion | authenticated scanner technical principal for the exact reservation/Asset only |
| reconciliation | authenticated bounded reconciliation principal for technical repair only |

Authorization precedes Asset existence, filename, lifecycle, scan state/reason,
digest, size, count, linkage, uploader, object identity and content disclosure.
Replay reauthorizes current actor/scope. Protected denial is payload-free and
does not distinguish missing from forbidden. Application policy remains the
authority; transport and storage adapters do not decide access.

## 4. Identity, metadata and immutability

Asset UUID is generated server-side and never derived from business or file
metadata. Object identity is a separately generated high-entropy opaque value
that contains no Organization, Project, Workspace, Evidence, Report, user or
filename component. Object identity is protected internal state and never a
client locator.

The server sanitizes filename to a single safe display name, normalizes Unicode
deterministically, strips path components/control characters and keeps a
bounded extension only for display. It does not trust browser MIME. Media type
comes from bounded signature/type validation; unsupported or ambiguous content
is rejected before canonical finalization. Size and SHA-256 digest are computed
while streaming exact bytes. Filename, media type, size, digest, object identity,
uploader, upload time, scope and predecessor cannot change after Asset creation.

Bytes cannot be overwritten or edited. Replacement creates a distinct Asset
with its own bytes/digest and an optional predecessor. V1 predecessor
cardinality is zero or one. Successor creation does not withdraw its
predecessor. Branching successors are allowed only if the user deliberately
creates different replacements; lineage is navigation, not standing or
approval. No in-place versioning, merge or file checkout exists.

## 5. Upload and canonical finalization

Upload is a multi-resource saga, not a false distributed transaction.

1. The application authenticates, resolves trusted scope and authorizes.
2. It creates an idempotent, expiring upload reservation containing safe
   control metadata and an opaque temporary object identity. A reservation is
   not a Supporting File Asset and is never listable as engineering content.
3. The backend streams bytes to the private quarantine namespace while
   enforcing maximum bytes, calculating SHA-256 and validating type. Direct
   browser-to-object-store upload and public/presigned upload URLs are excluded
   from V1.
4. The application verifies exact object metadata using the known key and, in
   one database transaction, creates the complete quarantined Asset, consumes
   the reservation, records Audit/outbox/idempotency and requests scan.
5. Scanner processing is asynchronous. Only an exact authenticated result bound
   to Asset/object/digest/scan-attempt may transition the Asset.

Duplicate idempotency replay with an identical fingerprint returns the stable
authorized result; changed fingerprint returns conflict. Concurrent finalize,
scan, withdrawal and link operations use expected version and one-winner
semantics.

Failure behavior:

- client disconnect/stream/size/type failure aborts multipart transfer and
  expires the reservation without creating an Asset;
- object-write success/database failure creates an orphan candidate identified
  by the reservation; reconciliation verifies the exact unreferenced object
  before removal;
- database reservation/object failure marks or expires the reservation and
  aborts/removes only the exact partial object;
- finalization cannot succeed without exact key, size and digest agreement;
- reconciliation cannot create an Asset from an orphan or infer business
  metadata; the Human must retry upload;
- object-store unavailability returns payload-free unavailable and reveals no
  storage topology.

## 6. Safety scan and lifecycle

Lifecycle is closed:

`quarantined -> available | rejected`

`available -> withdrawn`

Rejected and withdrawn are terminal. A scan engine may report only a technical
safety disposition for the exact bytes: clean, unsafe or indeterminate/error.
Clean plus digest/object verification permits the explicit transition to
available. Unsafe permits rejected. Timeout, unavailable scanner, unknown
result, malformed callback, stale attempt, digest mismatch or object mismatch
leaves the Asset quarantined and schedules a bounded retry. No timeout or
operator default may promote an Asset.

External users see only generic authorized lifecycle. Malware family,
signature, engine diagnostics and retry details are protected operational
evidence. Scanner cannot alter scope, metadata, Evidence, Report, Memory or
Human authority. Retries are bounded; exhausted scans remain quarantined until
an attributable authorized technical retry succeeds or the reservation/object
is handled through incident procedure.

Available permits potential governed linkage/download only. Rejected is never
downloadable, linkable or historically relied upon. Withdrawn is excluded from
active lists, new links and new Report reliance. No lifecycle rollback exists.

## 7. Evidence linkage

An Asset link is permitted only when:

- Asset is available and currently authorized;
- Evidence is proposed, currently authorized and in the same Organization;
- Evidence Project equals Asset Project; Organization-wide Evidence cannot
  absorb a Project Asset;
- if Evidence is Workspace-scoped, Asset Workspace equals it;
- if Evidence is Project-scoped, Asset may be Project-wide or in a Workspace
  of that Project, and the linking actor must be authorized to both scopes;
- the exact set is bounded, unique and deterministically ordered;
- a final Asset authorization/state/digest recheck occurs immediately before
  persistence.

The link set is part of the Evidence version. Linking advances Evidence version
once and produces Evidence Audit/outbox/idempotency under its existing UoW.
Once Evidence becomes current, withdrawn, superseded or rejected, the link set
cannot be edited. Asset withdrawal does not silently mutate Evidence; it makes
the linked basis unavailable for new reliance and is shown only after
authorization.

## 8. Technical Report provenance and historical reliance

Technical Report may rely on a file only through canonical Evidence. File-only,
external path and object-key provenance are rejected. Draft composition may
select a current Evidence version with authorized available linked Assets.
Report acceptance performs its existing final Evidence reauthorization and,
for every linked material Asset, independently verifies current authorization,
same-scope compatibility, available standing, exact version, key-bound object
existence, size and digest immediately before commit.

For a Workspace-scoped Report, each relied-upon Asset must be Project-wide
(`workspace_id` null) or scoped to that exact Report Workspace. A Project-wide
Evidence record that links Assets from another Workspace is not an eligible
source for the Report. This check is all-or-nothing and prevents a broad
Evidence identity from laundering incompatible Workspace material.

The accepted snapshot uses a new closed, versioned Evidence historical basis
that contains the existing Evidence fields plus a deterministic ordered tuple
of file bases. Each file basis contains Asset identity/version, Organization,
Project/Workspace, safe filename, verified media type, byte size, SHA-256,
uploader, upload time and predecessor identity when present. It excludes object
keys, scan details, credentials, paths and file content. The accepted snapshot
digest binds the complete representation. Acceptance fails atomically and
non-disclosingly if any material Asset is no longer available, changed,
unauthorized, missing or unverifiable.

Later withdrawal changes no accepted snapshot and deletes no byte. Active Asset
reads and new reliance stop. Authorized historical download requires an exact
accepted Report context, current report/source scope authorization, exact Asset
identity and digest match and retained-object verification. It does not make
the Asset current or the old Report newly accepted. An accepted Report remains
intelligible even when ordinary current source access has changed; unauthorized
historical access remains protected.

Organizational Memory continues to authorize the exact accepted Report and its
provenance. It may disclose only safe provenance fields already governed by
Memory. Any file byte request leaves Memory and enters the historical file
authorization path; Memory never becomes an Asset repository.

## 9. Withdrawal, retention and physical deletion

Withdrawal requires an explicit Human rationale and expected version. It is a
terminal governance action that blocks active retrieval, new Evidence linkage
and new Report reliance. It does not imply that prior engineering work was
wrong, does not revoke a Technical Report and does not erase Audit/history.

All canonical available and withdrawn Asset bytes are retained in V1 and take
part in PATCH-042 recovery sets. No user, runtime endpoint or routine operator
may physically purge them. A future retention/purge capability needs a new
governed PATCH. Temporary incomplete objects and objects for rejected Assets
may be deleted only under bounded operational retention/reconciliation because
they can never be relied upon by an accepted Report; deletion records safe
identity/digest metadata and never content.

## 10. Audit, events and recovery

Shared `AuditLog` is reused. File events record actor/principal, operation,
Asset UUID where safely available, Organization, correlation/idempotency,
previous/new version and standing, safe reason/category code and outcome.
Audit never stores bytes, filenames, free-form file content, object keys,
credentials, malware signature detail or full exception text. Human withdrawal
rationale is bounded and protected.

Domain events/outbox cover reservation finalized, Asset quarantined, scan
requested, Asset available/rejected/withdrawn, Evidence linked and
reconciliation required/completed. Events contain opaque identities and bounded
state only. Publication is after commit; consumers have no authority to
promote or link an Asset.

PATCH-042 recovery-set manifests must include the database cutoff plus a
protected object inventory/cutoff digest. Restore is promotable only when every
database-referenced canonical Asset object is present with matching digest and
no inconsistent newer database/object pairing is selected. Orphan objects may
be quarantined for reconciliation; missing referenced objects block file reads
and production recovery promotion. Recovery never invents Asset state.

## 11. Protected results and availability

The application uses closed results: success, protected_not_found,
invalid_request, conflict and unavailable, with operation-specific success
payloads. Protected/invalid/unavailable outcomes carry no protected payload or
diagnostic. Quarantined/rejected/withdrawn standing is disclosed only inside an
authorized status success; rejected reason is not exposed. Download success is
a server-mediated attachment stream with safe headers, not an object URL.

Filename is emitted only in `Content-Disposition: attachment` using safe ASCII
fallback plus RFC 5987 encoding. No file is rendered inline in the SATCO origin.
`nosniff`, restrictive content security policy and cache controls are required.
Range support, if implemented, reauthorizes the complete request and preserves
the same limits.

## 12. Bounded query and resource controls

Lists are Project/optional-Workspace scoped, deterministically ordered, bounded
and authorization-filtered. They expose returned visible count only, no hidden
or global total. Continuations are opaque, authenticated, short-lived and bound
to actor, Organization, Project, Workspace, filter and last evaluated key.

Uploads have exact size/type/name limits selected by IDS. Concurrency, open
streams, scan retries, list pages and link cardinality are bounded. The server
terminates oversized streams without buffering whole files in process and
without reflecting file content in errors/logs.

## 13. UI behavioral contract

The Project page is the primary entry. After Project and optional Workspace
selection, authorized users see:

- a Supporting Evidence surface with real active/quarantined items;
- an accessible upload control with explicit scope, permitted type/size and
  non-authority explanation;
- progress and generic scan standing without technical scan disclosure;
- Evidence creation/linking from selected available Assets;
- current Evidence candidates in Technical Report authoring;
- safe file provenance on draft/accepted Report detail;
- active or historical download only when the corresponding protected service
  result succeeds.

Empty state says no authorized supporting files and offers upload only when the
actor is eligible. Protected state does not say whether files exist. Errors do
not invent demo content. Keyboard, labels, focus, status announcements, color-
independent standing, responsive stacking, filename wrapping and minimum touch
targets are mandatory. No global EDMS navigation or drag-and-drop-only flow is
introduced.

## 14. AI and Human authority

PATCH-043 contains no AI interpretation. Scanner classification is a safety
control, not AI engineering analysis. Files are not sent to the AI Capture
Assistant and no autonomous extraction, summary, Evidence creation, Report
text, acceptance or Memory admission occurs. Human engineering authority and
existing acceptance/admission operations remain unchanged.

## 15. Acceptance criteria

1. Dedicated Asset ownership and exact lifecycle are enforced.
2. Bytes and immutable metadata cannot be edited or overwritten.
3. Server-derived scope and authorization-before-disclosure apply everywhere.
4. Partial upload, orphan, scan and storage failures fail closed and reconcile
   without inventing canonical state.
5. Only available same-scope Assets link to proposed Evidence.
6. Reports rely on files only through Evidence and freeze exact digest-bound
   historical bases after acceptance-time final recheck.
7. Withdrawal blocks new use and preserves authorized accepted history.
8. No canonical available/withdrawn byte is physically deleted in V1.
9. Shared Audit/outbox/idempotency/concurrency and recovery-set integrity hold.
10. Download is server-mediated, attachment-only and non-disclosing.
11. UI is bounded, accessible, responsive and real-data-only.
12. No EDMS, OCR, search, AI interpretation or Product Completion scope leaks.

## 16. Traceability

| PATCH-043 concern | EDS sections |
|---|---|
| Aggregate/object ownership | 2, 4 |
| Organization/Project/Workspace authorization | 3 |
| upload/scan/failure/reconciliation | 5, 6 |
| Evidence and Report provenance | 7, 8 |
| withdrawal/retention/history | 8, 9 |
| Audit/recovery/security | 10–12 |
| UI/accessibility/real data | 13 |
| Human/AI/non-goals | 14, 17 |

## 17. Explicit non-goals and IDS obligations

Deferred scope is exactly the PATCH record's deferred list. IDS-043 must close
exact tables, constraints, roles, ports, request/result DTOs, object client,
prefix/key rules, credential grants, upload/type/size limits, scan protocol and
retry schedule, idempotency representation, reconciliation queries, exact
Evidence/Report schema versioning, routes, pagination token, UI files,
Content-Disposition, metrics/log fields, recovery manifest changes, migration
sequence and executable verification matrix.

IDS must not claim that a real external scanner, production object store,
external TLS, backup or monitoring evidence exists locally. If canonical
Project/Workspace/Evidence/Report application boundaries cannot supply a
required authorization or atomic extension point, IDS must name the exact
prerequisite rather than use direct foreign persistence or invent authority.
