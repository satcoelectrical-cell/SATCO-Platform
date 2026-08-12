# PATCH-032 — Batch 3 Authorized File Manifest

## 1. Document Control

| Field | Value |
|---|---|
| Document ID | PATCH-032-B3-MANIFEST |
| Related PATCH | PATCH-032 — Technical Report |
| Batch | Batch 3 — Repository and Historical Resolution |
| Status | RECONCILED / FOCUSED REMEDIATION AUTHORIZED |
| Human authority | GRANTED |
| Governing ADR | ADR-023 — ACCEPTED / AUTHORITATIVE |
| Governing EDS | EDS-032 — ACCEPTED / COMPLETE |
| Governing IDS | IDS-032 — ACCEPTED / COMPLETE |
| Governing plan | Implementation-Plan-032 — ACCEPTED / COMPLETE |
| Governing readiness review | IRR-032 — PASS / READY FOR IMPLEMENTATION |
| Batch 1 | ACCEPTED / COMPLETE |
| Batch 2 | ACCEPTED / COMPLETE |
| PATCH-032 overall | IN PROGRESS |
| Migration authority | NOT GRANTED / NOT REQUIRED |
| Commit / push authority | NOT GRANTED |
| Batch 4 authority | NOT GRANTED |
| Date | 2026-08-10 |

## 2. Authority Boundary

Human authority grants preparation and implementation of Batch 3 only. This
manifest is the exact file boundary for Implementation-Plan-032 steps S09 and
S10. It authorizes the no-commit Technical Report repository, typed mapping
between Batch 2 persistence records and Batch 1 contracts, session-bound
historical resolvers for the four approved canonical source categories, and
focused repository and historical-resolution evidence.

Batch 3 does not authorize application command orchestration, acceptance
transaction orchestration, Unit of Work ownership, Audit or durable rejection
Audit integration, outbox or idempotency application integration, AI workflow,
API transport, frontend work, migration changes, configuration changes,
unrelated refactoring, or Batch 4 and later work. Persistence-only outbox and
idempotency structures created in Batch 2 remain untouched.

This reconciliation corrects the manifest gap recorded as `B3-CRIT-01`. It is
not an architectural amendment. Accepted IDS-032 §§11–12.4 and accepted
Implementation-Plan-032 S10 already require governed authorization-before-
disclosure for historical resolution. This reconciled boundary authorizes only
the minimum inward request-contract surface needed to implement that existing
authority.

The filename `technical_report_unit_of_work.py` is reserved by the accepted
file map for the eventual primary Unit of Work and session-bound adapters. In
Batch 3, that file may contain only the S10 session-bound historical resolver
adapters. It shall not expose or implement a Technical Report Unit of Work,
commit, rollback, transaction coordination, Audit, outbox, idempotency,
rejection Audit, service, or application behavior. Those responsibilities
remain deferred to separately authorized batches.

## 3. Verified Repository Evidence

Repository inspection established:

- repository path: `/Users/mac/Projects/SATCO-Platform`;
- branch: `patch-022.3a-development-infrastructure`;
- inspected HEAD: `b7fb8d4412d6b7528365f19b1418926aaa716686`;
- Git metadata is functional and the working tree contains pre-existing,
  uncommitted PATCH-032 and unrelated changes that must be preserved;
- the Alembic graph has exactly one head: `e03200000001`;
- accepted Batch 1 Technical Report enums, exceptions, Aggregate, command and
  historical contracts, inward ports, schemas, and tests exist in the current
  working tree;
- accepted Batch 2 Technical Report root, provenance, persistence-only outbox
  and idempotency mappings, migration, role separation, constraints, triggers,
  grants, and focused tests exist in the current working tree;
- `TechnicalReportRepository` and `TechnicalReportHistoricalResolver` are
  already defined as persistence-independent inward ports;
- existing repositories use a caller-owned SQLAlchemy `Session` and do not own
  transaction commit;
- Universal Capture, Evidence, EngineeringObject, and Engineering Relationship
  each have an existing canonical persistence model with stable UUID identity,
  positive version, Organization scope, and capability-specific state;
- none of those canonical capabilities exposes a common immutable historical
  store that Technical Report may assume or own; and
- Implementation-Plan-032 assigns S09 and S10, and only S09 and S10, to Batch
  3. S11 begins Batch 4 transaction and Audit work.

No repository conflict blocks publication of this manifest.

## 4. Authorized Batch 3 Scope

Batch 3 authorizes only:

- Technical Report repository add, scoped get, scoped list, scoped successor
  list, provenance access, expected-version draft persistence, expected-version
  acceptance compare-and-change, predecessor validation, and lineage behavior;
- complete draft Aggregate reconstruction from Batch 2 root and provenance
  records;
- accepted Aggregate reconstruction exclusively from the immutable accepted
  snapshot and acceptance metadata;
- typed serialization, deserialization, lifecycle/version mapping, provenance
  ordering, and fail-closed persistence coherence checks;
- capability-local, session-bound historical resolution for Universal Capture,
  Evidence, EngineeringObject, and Engineering Relationship;
- current canonical lookup, scope and source-state verification needed by the
  approved historical contracts;
- use of an independently verified owner snapshot when one exists, otherwise
  construction and verification of the exact closed report-owned
  `*HistoricalBasisV1` fallback;
- deterministic canonical serialization and lowercase SHA-256 digest
  verification; and
- focused repository and historical-resolution tests.

## 5. Explicit Exclusions

Batch 3 does not authorize:

- application services, command orchestration, acceptance orchestration, or AI;
- Technical Report Unit of Work construction or transaction ownership;
- commit, rollback, Audit, rejection Audit, outbox emission or dispatch,
  idempotency orchestration, event publication, or background processing;
- API routers, dependency injection, transport DTO integration, or frontend;
- changes to canonical source models, repositories, services, ownership, or
  semantics;
- a generic canonical-source repository or untyped source mapping;
- direct disclosure of inaccessible canonical state;
- generic update, physical delete, or ORM-row exposure;
- new or rewritten migrations, tables, constraints, triggers, grants, roles,
  configuration, or infrastructure; or
- Batch 4 or later work.

## 6. Exact Production File Boundary

Exactly three production files are authorized: two new repository files and
one narrowly bounded modification to the existing inward port:

| Path | State | Requirement | Reason and plan traceability | IDS traceability |
|---|---|---|---|---|
| `backend/app/repositories/technical_report_repository.py` | NEW | Mandatory | Implement the no-commit SQLAlchemy repository, full reconstruction, expected-version persistence, accepted-snapshot reads, provenance access, predecessor validation, and lineage under Workstream F / S09. | IDS-032 §§7–9, 20–21 and the exact file map in §23 |
| `backend/app/repositories/technical_report_unit_of_work.py` | NEW | Mandatory, S10-only boundary | Implement only the four capability-local, session-bound historical resolver adapters under Workstream D / S10. The eventual Unit of Work and all transaction/Audit/outbox/idempotency behavior in this filename remain prohibited until Batch 4 authority. | IDS-032 §§10–12, especially §12, and the exact file map in §23 |
| `backend/app/ports/technical_report.py` | EXISTING / MODIFY | Mandatory, reconciliation-only | Extend only `TechnicalReportHistoricalRequest`, or its exact accepted equivalent, with governed `TechnicalReportScope` and closed typed operation context necessary for historical-source authorization-before-disclosure. No other port, protocol, request, response, or behavior may change. | IDS-032 §§11–12.4; Implementation-Plan-032 S10 |

No existing production file other than the narrowly authorized port above may
be modified. The port change may carry only mandatory Organization, Workspace,
optional Project, and closed typed operation context. It must use the existing
accepted `TechnicalReportScope` or its exact already-authorized typed
equivalent. It must not add an open operation string, arbitrary metadata map,
application orchestration, or authority-bearing behavior. If S09 or S10
requires any other Batch 1 contract, Batch 2 mapping, canonical capability
file, migration, configuration surface, or production file to change, Batch 3
must stop for an explicit authority decision.

The extension exists solely so the source-specific historical resolvers can
enforce active actor and membership authority, Organization compatibility,
Workspace compatibility, optional Project compatibility, operation-specific
disclosure, source-specific authorization, related-resource authorization, and
protected-not-found/non-disclosure semantics before returning protected
historical source state.

## 7. Exact Test File Boundary

Exactly one test file is authorized:

| Path | State | Requirement | Exact purpose and traceability |
|---|---|---|---|
| `backend/tests/test_technical_report_repository.py` | NEW | Mandatory | Repository add/get/list/successor/provenance behavior; complete draft reconstruction; immutable accepted-snapshot-only reconstruction; accepted digest verification; expected-version compare-and-change; fail-closed corrupt-state tests; four-source historical matrix, canonical lookup/version checks, source-specific fallback, integrity mismatch, missing/inaccessible/wrong/stale source cases, deterministic ordering, no commit, no generic source repository, and no Batch 4 leakage. Implementation-Plan-032 S09–S10 and IDS-032 §§7–12, 20–21, 24.2. |

No existing test file may be modified. The focused test may use local fakes and
fixtures contained in that file but may not create an additional helper or
fixture module.

## 8. Historical Resolver Matrix

| Source category | Canonical owner and model | Identity/version | Batch 1 contract | Exact Batch 3 adapter behavior | Fallback and integrity rule | Fail-closed outcome |
|---|---|---|---|---|---|---|
| Universal Capture | Universal Capture / `EngineeringExperienceCapture` | Capture UUID + positive `version` | `CaptureHistoricalBasisV1` | Session-bound capture resolver loads only Organization-scoped canonical capture state, verifies the requested identity/version, lifecycle and governed scope, and extracts only the approved basis fields. | Use an independently verified owner snapshot if available; otherwise produce the closed capture basis, canonical JSON, and lowercase SHA-256 digest. | Return the stable non-disclosing historical-resolution failure when the source is absent, inaccessible, changed, wrong-type, incoherent, or unreconstructable. |
| Evidence | Evidence Foundation / `Evidence` | Evidence UUID + positive `version` | `EvidenceHistoricalBasisV1` | Session-bound Evidence resolver verifies Organization and approved Project/Workspace compatibility, acceptable lifecycle/standing, identity/version, and approved metadata-only fields. | Use an independently verified owner snapshot if available; otherwise produce the closed Evidence basis and verify its canonical digest. | Fail without source disclosure when existence, visibility, scope, lifecycle/standing, version, completeness, or integrity cannot be proven. |
| EngineeringObject | EngineeringObject capability / `EngineeringObject` | EngineeringObject UUID + positive `version` | `EngineeringObjectHistoricalBasisV1` | Session-bound EngineeringObject resolver verifies scope, identity/version, lifecycle, authority standing, classification, and only the approved basis fields. | Use an independently verified owner snapshot if available; otherwise produce the closed EngineeringObject basis and verify its canonical digest. | Fail non-disclosingly on missing/inaccessible scope, stale version, invalid state, incomplete basis, or digest mismatch. |
| Engineering Relationship | Engineering Relationship capability / `EngineeringRelationship` | Relationship UUID + positive `version` | `EngineeringRelationshipHistoricalBasisV1` | Session-bound relationship resolver verifies Organization, Project/Workspace, identity/version, lifecycle, relationship family/type, protected endpoint identities, and Evidence identities without transferring authorization or ownership. | Use an independently verified owner snapshot if available; otherwise produce the closed relationship basis and verify canonical serialization/digest. | Fail non-disclosingly when the relationship or any protected required basis cannot be authorized, resolved, completed, or integrity-verified. |

Each adapter remains capability-local in behavior while sharing only the
Technical Report historical-resolver port. Family/type discrimination remains
explicit for Engineering Relationship. Resolver selection shall be closed and
typed; family or source type shall never be inferred from payload shape.

## 9. Accepted Snapshot-only Read Invariant

For lifecycle `accepted`, the repository must deserialize and verify the
immutable `accepted_snapshot` and its stored lowercase SHA-256 digest, then
reconstruct the accepted Aggregate and acceptance record from that accepted
representation. It must not reconstruct accepted technical content,
qualification, provenance/reliance, revision identity, or acceptance-defining
state from mutable working/draft columns or current canonical source state.

Any absent snapshot, digest mismatch, schema mismatch, lifecycle/acceptance
coherence defect, identity/version mismatch, or invalid nested historical basis
must fail closed. Tests shall prove that changes to working/draft columns do
not change an accepted read and that corrupt or incoherent accepted state is
never returned.

## 10. Persistence-to-Domain Mapping Boundary

The repository is responsible for:

- reconstructing draft Aggregate identity, trusted scope, Owner, purpose,
  content, qualification, ordered provenance, revision, predecessor, lifecycle,
  version, and timestamps from approved persistence mappings;
- reconstructing accepted Aggregates only through the accepted snapshot and
  acceptance metadata after canonical digest and coherence verification;
- mapping every provenance record to exactly one approved typed locator and,
  where present, exactly one closed historical-basis value object;
- preserving provenance ordinal order and rejecting gaps, duplicates,
  discriminator mismatches, incomplete locators, malformed nested values, or
  unapproved extra data;
- mapping lifecycle and purpose only through closed Batch 1 enums;
- returning persistence-independent Aggregates, provenance values, and read
  results, never ORM rows or untyped mappings;
- using compare-and-change persistence for draft and acceptance mutations
  without committing; and
- leaving authorization, business transition policy, event publication,
  idempotency, Audit, and transaction ownership outside the repository.

The historical resolvers may read canonical records through the caller-owned
Session, but they may neither mutate those records nor acquire canonical
repository ownership.

## 11. Dependency Confirmation

Batch 1 is `ACCEPTED / COMPLETE`. Its Aggregate, commands, closed historical
contracts, schemas, exceptions, enums, and inward ports satisfy S09–S10
contract dependencies.

Batch 2 is `ACCEPTED / COMPLETE`. Its root/provenance mappings, accepted
snapshot representation, database constraints, accepted-state immutability,
role separation, and sole migration head `e03200000001` satisfy S09–S10
persistence dependencies. Batch 3 does not modify them.

The four canonical source models required by IDS-032 exist. No generic source
repository, new canonical persistence capability, or migration is required.

## 12. Deferred Batch 1 Minor Traceability

`B1-MIN-01` and `B1-MIN-02` remain `ACCEPTED / DEFERRED — NON-BLOCKING` in the
Batch 1 Independent Review and Human Acceptance record. Batch 3 does not
naturally touch their authorized surfaces and does not authorize their
opportunistic resolution. Any need to change a Batch 1 file for either item is
a stop condition.

## 13. Batch 3 Stop Conditions

Implementation must stop if:

- any of the four approved canonical source capabilities is absent or cannot
  supply the exact IDS-032 source-specific current-state facts;
- canonical ownership would need to move to Technical Report;
- a generic or untyped source repository would be required;
- S09 or S10 cannot be completed without Batch 4 Unit of Work, transaction,
  Audit, outbox, idempotency, rejection Audit, or service behavior;
- accepted Batch 1 or Batch 2 contracts, mappings, migrations, constraints, or
  semantics would need redesign;
- an accepted report would need to be reconstructed from working/draft fields;
- historical integrity or completeness cannot be proven fail-closed;
- a new or amended migration, configuration change, or infrastructure change is
  required;
- implementation requires any file outside the exact manifest;
- the Alembic graph is no longer a single head at `e03200000001`; or
- repository reality contradicts ADR-023, EDS-032, IDS-032, the accepted plan,
  IRR-032, or an accepted prior batch.

## 14. Validation Requirements

Batch 3 validation shall include:

1. static compilation of the two production files and focused test file;
2. repository add, scoped get/list, successor/lineage, provenance ordering,
   expected-version, no-commit, no-authorization, and no-ORM-row tests;
3. draft and accepted reconstruction tests, including accepted-snapshot-only
   reads and digest/coherence corruption failures;
4. the complete four-source historical-resolution matrix, including canonical
   version/snapshot resolution, closed fallback reconstruction, missing,
   inaccessible, wrong-type, stale, incomplete, malformed, and digest-mismatch
   failures;
5. direct proof that no generic source repository or Batch 4 orchestration was
   introduced;
6. accepted Batch 1 and Batch 2 focused regressions;
7. relevant Capture, Evidence, EngineeringObject, Engineering Relationship,
   authentication, Organization, Project, and Workspace adjacent regressions;
8. prohibited-pattern scans for commit, rollback, UoW construction, Audit,
   outbox, idempotency, service, router, migration, and generic-source behavior;
9. exact authorized-file verification; and
10. `git diff --check`.

No development, staging, or production migration may be executed.

## 15. Batch 4 Authority Boundary

Batch 4 authority is not granted. After Batch 3 implementation and focused
validation, work must stop for an Independent PATCH-032 Batch 3 Review and
Human Batch 3 Acceptance. Batch 4 preparation or implementation requires a
separate explicit Human governance decision and a separately published exact
file manifest.

## 16. Focused Remediation Authority

Focused Batch 3 remediation authority is granted only for these findings and
only within the reconciled four-file boundary:

- `B3-CRIT-01`: extend the historical request contract as bounded above and
  enforce authorization-before-disclosure in source-specific resolvers;
- `B3-MAJ-01`: enforce source-specific lifecycle, standing, authority,
  governed-scope, Relationship endpoint, referenced Evidence, and protected
  non-disclosure rules;
- `B3-MAJ-02`: complete accepted root/snapshot/acceptance-record coherence
  validation;
- `B3-MAJ-03`: reconstruct persisted draft purpose through the accepted closed
  `TechnicalReportPurpose` enum contract; and
- `B3-MAJ-04`: add required focused and persistence-backed negative
  authorization, historical-resolution, mapping, fallback, and corrupted-state
  evidence only in `backend/tests/test_technical_report_repository.py`.

The complete reconciled implementation boundary is:

1. `backend/app/repositories/technical_report_repository.py`;
2. `backend/app/repositories/technical_report_unit_of_work.py`;
3. `backend/app/ports/technical_report.py`; and
4. `backend/tests/test_technical_report_repository.py`.

No other implementation or test file is authorized. Batch 4 transaction
orchestration, Audit, rejection Audit, outbox behavior, idempotency behavior,
application services, API, AI workflow, canonical ownership transfer, and a
generic source repository remain prohibited.

## 17. Historical Evidence and Reconciliation Record

The original three-file manifest, initial Batch 3 implementation, Independent
Batch 3 Review `FAIL`, `B3-CRIT-01`, `B3-MAJ-01` through `B3-MAJ-04`, and the
authority-boundary assessment classifying `B3-CRIT-01` as a manifest gap remain
authoritative historical evidence. This reconciliation does not represent the
original manifest as complete and does not amend EDS-032, IDS-032,
Implementation-Plan-032, or ADR-023.

| Version | Date | Description |
|---|---|---|
| 1.1 | 2026-08-10 | Reconciled the Batch 3 manifest gap by narrowly authorizing `backend/app/ports/technical_report.py` for governed historical-resolution scope and closed operation context; granted focused remediation authority for B3-CRIT-01 and B3-MAJ-01 through B3-MAJ-04 within the exact four-file boundary; preserved the initial FAIL and findings; Batch 4 remains not granted. |
| 1.0 | 2026-08-10 | Published the original exact three-file Batch 3 Repository and Historical Resolution implementation boundary. |
