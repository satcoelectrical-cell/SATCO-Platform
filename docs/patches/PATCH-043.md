# PATCH-043 — Governed Supporting File Evidence Intake

## Document control

| Field | Value |
|---|---|
| Status | QG-12 PASS — exact bounded delivery authorized; not yet delivered or closed |
| Architecture / QG-M1 | PASS / ACCEPTED |
| EDS-043 | ACCEPTED / COMPLETE |
| IDS-043 | ACCEPTED / COMPLETE |
| Implementation Plan-043 | ACCEPTED / COMPLETE |
| IRR-043 | PASS |
| Implementation authority | COMPLETE — Batches 1–6 ACCEPTED / COMPLETE |
| Registered after | PATCH-042 DONE / CLOSED |

## Repository-grounded discovery

PATCH-027 owns a metadata-only Evidence Aggregate. It stores source citation,
revision, standing, supported fact, scope, lifecycle, creator and version; it
explicitly owns no source content, upload, file or document management. Evidence
may therefore exist without a stored file. It is scoped to one Organization,
optionally one Project and optionally one Workspace, with Workspace requiring
Project.

PATCH-032 owns Technical Reports and their report-specific provenance/reliance
manifest. An accepted Report freezes an integrity-protected immutable snapshot.
For Evidence it currently freezes `EvidenceHistoricalBasisV1`, the exact
accepted Evidence identity/version and a deterministic metadata-only basis.
Technical Report does not acquire ownership of Evidence or its source.
PATCH-039 productizes Capture-first authoring but does not prohibit later
authorized Evidence candidates. PATCH-040 admits only an exact accepted Report
version to Organizational Memory and retains that Report's protected provenance;
it does not create a file authority.

The repository has trusted authenticated Organization context, Organization-
filtered Project and Workspace services, project/workspace membership checks,
shared `AuditLog`, one-transaction UoW patterns, protected-result patterns and
the Vite Command Center. There is no Evidence or file-intake frontend today.
The sole Alembic head at registration is `e04100000001`.

PATCH-042 supplies the private object-storage, principal-separation,
health/capacity, recovery-set and scanner-foundation operational boundary. The
serving backend deliberately has no customer-object credential, SDK or data-
plane operation. PATCH-043 is the first authority to add a bounded application
data-plane adapter and credential. It does not reopen PATCH-042.

## Problem and purpose

Reference-only Evidence is insufficient for routine engineering work because
SATCO cannot preserve the material file basis later relied upon by an accepted
Technical Report. PATCH-043 allows real supporting engineering files to be
uploaded, safety-scanned, stored, authorized, retrieved, withdrawn and linked
to governed Evidence/provenance without turning SATCO into a generic EDMS and
without making file availability equivalent to engineering approval.

## Architecture boundary

`SupportingFileAsset` is a dedicated canonical Aggregate. It owns immutable
asset identity; Organization; required Project; optional Workspace; safe
original filename; verified media type; byte size; SHA-256 digest; opaque
private storage key; uploader; upload/scan times; version; optional predecessor;
and lifecycle. PostgreSQL owns business identity, scope, lifecycle, lineage and
authorization metadata. The private object store owns durable immutable bytes
under opaque keys and has no business or engineering authority.

Lifecycle is exactly:

`quarantined -> available | rejected`

`available -> withdrawn`

Rejected and withdrawn are terminal. File bytes are immutable. Replacement is
a new Asset with zero-or-one predecessor and never mutates the predecessor.
`available` means only that integrity and safety checks permit governed use; it
does not mean verified Evidence, accepted engineering, accepted Report or
Organizational Memory.

Temporary upload reservation is application workflow state, not an incomplete
canonical Asset. A canonical Asset is created only with complete immutable
metadata after the exact object, size, type and digest are known. Quarantine,
scan and reconciliation fail closed. Available/withdrawn bytes are not
physically purged in V1. Failed/rejected temporary objects may be removed only
by bounded operational reconciliation after database/object identity checks.

Evidence remains its own Aggregate. A governed Evidence-owned association may
link a proposed Evidence version to one or more authorized available Assets in
the same Organization and compatible Project/Workspace. Existing Evidence may
remain reference-only. Linkage transfers neither Asset nor Evidence ownership.
Only proposed Evidence may acquire file links in V1; current/terminal Evidence
link sets are immutable. File withdrawal prevents new linkage or Report
reliance but does not rewrite an existing Evidence version or accepted Report.

Technical Report acceptance reauthorizes Evidence and every linked Asset,
requires exact available state, verifies scope/version/digest and freezes a
closed file historical basis inside a new versioned Evidence historical basis.
The accepted Report still owns only its report-specific immutable provenance.
Later withdrawal cannot change that snapshot. Historical file retrieval is
permitted only through an authorized accepted-Report historical context whose
frozen identity and digest match the retained Asset; ordinary active retrieval
continues to require `available`.

Organizational Memory acquires no file operation. It continues to reuse the
accepted Report snapshot under PATCH-034/040 authorization. Safe provenance may
identify that a governed file basis exists, but bytes are retrieved only
through the Supporting File historical-read contract and never through Memory
storage ownership.

## Authorization and disclosure

Actor and Organization are trusted server-derived context. Project and optional
Workspace are resolved through existing canonical application boundaries.
The file policy reuses existing admin/project-owner/project-assignee/workspace-
member scope semantics; it is not a second tenancy system. Upload/link/list/read
require current applicable scope access. Withdrawal requires current applicable
scope plus uploader or Organization-admin authority. Scanner and reconciler
principals may report safety/integrity or repair technical workflow state only;
they gain no Human, Evidence, Report, Memory or Organization authority.

Every reserve, finalize, status, list, read, download, link, withdrawal and
historical retrieval operation authorizes before protected disclosure and
rechecks immediately before the governing action. Protected denial reveals no
existence, identity, filename, count, scan reason, object key, storage location,
linked identity or exception detail. Lists expose visible items only and no
hidden/global total. No public object URL or business-meaningful object key is
allowed.

## User experience

The bounded V1 home is the authorized Project/Workspace engineering context:
a Supporting Evidence panel uploads and lists safe metadata, shows generic
quarantined/available/rejected/withdrawn standing only after authorization,
and lets a Human create or enrich proposed Evidence with selected available
files. The Technical Report source selector may choose authorized current
Evidence and displays its protected file provenance. Accepted Report detail
may offer an authorized attachment download through historical context.

There is no global file library, folder tree or file-centric primary
navigation. Empty states are truthful and actionable. Loading, unavailable,
invalid and protected states are distinct without leakage. Controls are
keyboard operable, labelled, focus-visible and responsive; filenames wrap and
do not create horizontal overflow. Production surfaces contain no fake files,
counts, scan results or Evidence.

## Failure and reliability boundary

- interrupted upload: abort multipart write and retain/expire only a bounded
  non-disclosing reservation;
- object success followed by database-finalization failure: record a safe
  reconciliation obligation and delete the exact orphan only after recheck;
- reservation success followed by object failure: fail the reservation and
  clean any exact partial object;
- scanner timeout or unavailability: remain quarantined; never become
  available by timeout/default;
- malware/unsafe result: transition once to rejected with protected external
  result and bounded internal Audit detail;
- digest/size/type mismatch or missing object: remain or return to protected
  unavailable/quarantined handling; never disclose or link;
- object-storage outage: fail closed with payload-free unavailable and no
  metadata fallback that implies content availability;
- withdrawal after accepted reliance: block active/new reliance, preserve the
  immutable accepted basis and retained bytes for authorized historical use;
- every mutation uses idempotency, optimistic concurrency, Audit, outbox and
  deterministic compensation/reconciliation; no cross-system atomicity is
  claimed.

## In scope

- Supporting File Asset domain, persistence and migration;
- bounded application S3-compatible adapter and least-privilege credential;
- immutable streaming upload, digest/type/size enforcement and opaque keys;
- quarantine, scanner invocation, available/rejected/withdrawn lifecycle;
- retry and orphan/object/DB reconciliation;
- authorized list/status/download and historical retrieval;
- Evidence linking and versioned Technical Report file provenance;
- accepted-Report historical retention;
- shared Audit, outbox, idempotency, metrics and recovery-set participation;
- minimal Project/Workspace, Evidence and Report UI;
- security, accessibility, responsive and real-data-only validation.

## Explicitly deferred

Generic EDMS, folders, collaborative editing, checkout/check-in, in-place
replacement, OCR, semantic/vector search, automatic extraction/classification,
AI file interpretation, document templates/authoring, broad external EDMS
synchronization, customer-managed storage, cross-Organization sharing,
physical purge of available/withdrawn bytes, broad retention administration,
Procurement/Vendor/RFQ/Costing/Proposal/Contract/Project-Execution/Quality/FAT/
Commercial-Control workflows, Product Completion features, Commercial V1
Release Certification and PATCH-044 are excluded.

## Dependencies

- PATCH-025 trusted Organization context and current Organization membership;
- PATCH-027 Evidence Foundation;
- PATCH-032/039 Technical Report domain and experience;
- PATCH-034/040 Organizational Memory provenance/reuse boundary;
- PATCH-038/041 Project/Customer and Organization/User operational flows;
- PATCH-042 private object-storage/recovery/security foundation;
- ADR-012 migration/upgrade authority and current Alembic head verification.

## Governance reconciliation

PATCH-040 through PATCH-042 remain DONE / CLOSED and unchanged. The Roadmap and
Governance registry files contain unrelated Human worktree edits, so PATCH-043
registration uses this append-only authoritative PATCH record rather than
overwriting mixed hunks. A later bounded registry-only reconciliation may add a
pointer to this record; it cannot change this accepted boundary.

ADR/XDR threshold assessment: no new cross-platform ADR or experience XDR is
required. The canonical-ownership, private-storage, Human-authority and
Project/Workspace experience rules are bounded applications of accepted
governance and PATCH-042's explicit PATCH-043 delegation. Any later public
object access, generic document hierarchy, AI interpretation or cross-product
file platform would cross that threshold and requires separate governance.

## Authority

The independent Architecture Review and QG-M1 are PASS. The IDS initial FAIL,
focused amendments and re-review PASS are preserved. Standing Human
Architecture, EDS, IDS and Implementation Plan acceptances are recorded in
standalone artifacts. IRR-043 is PASS. Batches 1–6 are ACCEPTED / COMPLETE;
Independent Final Implementation Review, Human QG-11 and QG-12 are PASS. The
exact 120-file bounded delivery is authorized but not yet committed or pushed.
No closure, PATCH-044, Product Completion Reconciliation or Commercial V1
Release Certification authority is created by this record.
