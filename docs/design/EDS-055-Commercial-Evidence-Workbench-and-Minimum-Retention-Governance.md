# EDS-055 — Commercial Evidence Workbench & Minimum Retention Governance

## 1. Status, authority, and normative force

| Field | Value |
|---|---|
| Date | 2026-09-14 |
| PATCH | PATCH-055 — Commercial Evidence Workbench & Minimum Retention Governance |
| Discovery | **HUMAN ACCEPTED / COMPLETE** |
| ADR-028 | **HUMAN ACCEPTED / AUTHORITATIVE** |
| EDS-055 design authority | **GRANTED** |
| EDS-055 | **HUMAN ACCEPTED / AUTHORITATIVE** |
| IDS-055 | **ELIGIBLE FOR SEPARATE DESIGN AUTHORITY / NOT YET AUTHORIZED** |
| Implementation Plan | **NOT STARTED / NOT AUTHORIZED** |
| Production/tests/frontend/migrations | **NOT AUTHORIZED / NONE CHANGED BY THIS EDS** |
| PATCH-056+ | **NOT STARTED / NOT AUTHORIZED** |

This EDS translates ADR-028 into the exact, finite, testable Commercial V1 product contract. Normative MUST, MUST NOT, SHALL, SHALL NOT, and EXACTLY language binds later IDS and implementation. This EDS does not define SQL, reserve migration identifiers, authorize source changes, or accept itself.

## 2. Upstream authority and preserved owners

Canonical ownership remains:

- Evidence Aggregate: engineering identity, source meaning, lifecycle, lineage, replacement, reliance.
- Supporting File Asset: intake, quarantine, scanner state, object identity, integrity, current file availability.
- Technical Report: immutable Human-accepted relied-upon provenance.
- Organizational Memory: Human-admitted reuse of accepted Report knowledge.
- Retention Governance: retention basis, hold, disposition eligibility/decision, governed export and recovery.

Retention Governance SHALL NOT become a second Evidence lifecycle or file-scanner lifecycle.

## 3. Exact closed Commercial V1 vocabularies

| Vocabulary | Exact values |
|---|---|
| Evidence lifecycle | `proposed`, `current`, `withdrawn`, `superseded`, `rejected` |
| Source standing | `draft`, `current`, `withdrawn`, `superseded` |
| Retention mode | `retain_until`, `retain_indefinitely` |
| Retention policy source | `platform_default`, `organization_default`, `human_subject_override` |
| Hold status | `active`, `released` |
| Disposition eligibility | `not_eligible`, `eligible`, `blocked_by_hold`, `indeterminate` |
| Disposition decision | `none`, `retain`, `approve_disposition` |
| Recovery status | `not_required`, `available`, `temporarily_unavailable`, `recovered`, `unrecoverable` |
| Export status | `requested`, `completed`, `failed` |

The existing Supporting File scanner field `disposition` remains exclusively `clean`, `unsafe`, or `indeterminate`. Retention code MUST NOT reuse the unqualified term `disposition` as a scanner-state alias.

Public logical outcomes are exactly: `success`, `invalid_request`, `protected_not_found`, `conflict`, `not_permitted`, `unavailable`, and `indeterminate`.

## 4. Retention subject contract — resolves A055-OBS-01

Commercial V1 SHALL use one typed `RetentionSubject` contract:

`subject_kind + subject_id + organization_id + project_id + optional workspace_id`

`subject_kind` is exactly `evidence` or `supporting_file`.

Each canonical subject may have exactly one current retention-governance head. Evidence-level retention does not implicitly create or mutate file-level retention; file-level retention does not alter Evidence standing. A coordinated user action may create both heads in one application workflow, but each remains separately addressable and auditable.

Duplicate or conflicting current heads for the same typed subject are prohibited.

## 5. Exact retention-governance record

A retention-governance head has exactly:

1. retention_record_id;
2. typed RetentionSubject;
3. retention_mode;
4. retention_until, required only for `retain_until`;
5. policy_basis_code and bounded Human-readable basis/rationale;
6. source of policy/default decision;
7. hold_status plus optional active hold reference;
8. computed disposition_eligibility;
9. current disposition_decision;
10. monotonically increasing version;
11. predecessor record ID;
12. creating/replacing actor and time; and
13. deterministic record digest.

`retain_until` requires a timezone-aware future-or-present instant under the accepted policy. `retain_indefinitely` requires `retention_until = null`. Policy/default precedence is exactly: Human subject override -> Organization default -> platform default. The Commercial V1 platform default is `retain_indefinitely`. Missing or invalid higher-priority policy therefore never fabricates an expiry date and never creates purge authority.

## 6. Hold contract

A hold record has exactly: hold_id, typed subject, status, reason_code, rationale, authority_reference, placed_by, placed_at, optional released_by/released_at/release_rationale, version, predecessor, and digest.

Placing or releasing a hold is Human-governed. AI and background expiry logic cannot place or release a hold. An active hold forces `blocked_by_hold` regardless of elapsed retention date or prior eligibility.

Hold release does not approve disposition; eligibility is recomputed from current retention facts after release.

## 7. Deterministic disposition eligibility

Eligibility is computed, never client-authored.

- active hold => `blocked_by_hold`;
- invalid/missing retention basis or unresolved current subject state => `indeterminate`;
- `retain_indefinitely` without hold => `not_eligible`;
- `retain_until` with current time before retention_until => `not_eligible`;
- `retain_until` at/after retention_until and no hold => `eligible`.

`eligible` means only that the subject may be presented for a later Human disposition decision. It SHALL NOT delete, withdraw, purge, archive, revoke access, or change engineering standing.

`approve_disposition` records Human approval metadata only. Automatic physical purge is outside PATCH-055 and MUST NOT be triggered.

## 8. Evidence Workbench workflow

The exact ordinary-user journey is:

`authorized Project/Workspace -> upload Supporting File -> quarantine -> scanner-cleared available -> create proposed Evidence -> inspect/link exact available files -> Human review -> lifecycle decision -> lineage/reliance display -> select current Evidence for Technical Report -> Human Report acceptance -> optional Memory admission`.

The Workbench SHALL expose create, read, list, transition, link, lineage/replacement, reliance, retention, hold, export, and recovery actions through server-authorized selectors.

Users MUST NOT type raw Evidence, Supporting File, lineage, retention, Report, or Memory UUIDs to complete ordinary workflows. Opaque IDs may exist in transport and URLs but selection is through authorized result sets and UI controls.

## 9. Evidence lifecycle and lineage rules

Existing Evidence lifecycle transitions remain authoritative and are not redefined here. Promotion to `current` still requires current source standing; accepted prior transition and version rules remain in force.

A supersession workflow MUST identify the replacement Evidence through an authorized server-resolved selector. Historical predecessor/successor lineage remains visible to authorized users. Withdrawal, rejection, and supersession never erase prior versions, Supporting File basis, Audit, or accepted Report reliance.

Retention state SHALL NOT be used as a precondition to falsify or rewrite engineering lifecycle history. Current-use eligibility and historical-retention truth remain separately observable.

## 10. Technical Report and Memory reliance

Only Evidence eligible under the existing Technical Report Evidence-source contract may be selected for new Report provenance. The Workbench SHALL surface current eligibility, warnings, and historical reliance without duplicating Report authority.

Once a Report is Human accepted, exact Evidence version and Supporting File historical basis remain immutable. Later Evidence lifecycle, hold, retention, export, recovery, rights, or storage events append new facts only.

Memory admission remains a separate Human action over an accepted Report. PATCH-055 does not create direct Evidence-to-Memory admission.

## 11. Export contract — resolves A055-OBS-02

A governed export records the act of export and provenance of the emitted copy. SATCO does not claim continuing control over an exported copy after it leaves the governed platform boundary.

Export requires current actor authorization, current subject visibility, and current content-access permission. The export record retains export_id, actor, typed source subjects and exact versions, purpose/rationale, requested/completed time, format, aggregate digest, byte count, terminal status, and failure code where applicable.

Export SHALL NOT change Evidence lifecycle, file lifecycle, retention, hold, Report provenance, or Memory provenance. Export failure is non-destructive and records no false completed artifact.

## 12. Historical recovery contract

Recovery applies only to retained historical material whose canonical identity and integrity can still be established. Recovery status is separate from engineering standing.

Recovery workflow:

`authorize -> resolve retained subject -> verify historical identity/digest -> verify current access rights -> restore or re-resolve protected bytes/handle -> verify integrity -> mark recovered -> Audit/outbox`.

Recovery MUST NOT convert Evidence to `current`, reverse withdrawal/supersession/rejection, recreate deleted authority, or rewrite accepted Report/Memory provenance.

If historical safe metadata is resolvable but protected bytes cannot lawfully or technically be restored, status is `unrecoverable` or `temporarily_unavailable` as applicable; provenance remains visible within authorization.

## 13. Authorization and protected-not-found

Authorization precedes protected lookup, validation that could reveal existence, count formation, idempotency replay, content disclosure, export, recovery, hold and retention mutation.

Organization scope is server-derived. Project and Workspace coherence MUST be checked against canonical ownership. Wrong-Organization, forbidden, and protected-absent resources return indistinguishable protected results.

Configuration, retention state, hold state, or historical Report reliance never grants content access by itself.

## 14. Concurrency, atomicity, and idempotency

Evidence lifecycle/link commands retain existing expected-version semantics. Retention, hold, disposition-decision, export-request, and recovery-request mutations SHALL require expected current version where a mutable head exists.

Exactly one conflicting current-head mutation wins. Losers return `conflict` and must reread. No partial mutation, Audit, or outbox record may survive a failed transaction.

Idempotency lookup occurs only after authorization and is scoped to actor, Organization, operation, subject and canonical request digest. A key from another authority boundary cannot disclose or replay a protected result.

## 15. Audit and outbox inventory

The minimum PATCH-055 event inventory is:

- `evidence.created`, existing owner event where already present;
- `evidence.lifecycle_transitioned`, existing owner event where already present;
- `evidence.supporting_files_linked`, existing owner event where already present;
- `retention.policy_applied`;
- `retention.policy_replaced`;
- `retention.hold_placed`;
- `retention.hold_released`;
- `retention.eligibility_changed`;
- `retention.disposition_decision_recorded`;
- `retention.export_requested` / `retention.export_completed` / `retention.export_failed`;
- `retention.recovery_requested` / `retention.recovery_completed` / `retention.recovery_unavailable`.

Payloads contain safe IDs, versions, digests, state codes, actor, correlation/causation and timestamps; never file bytes, storage keys, unsafe scanner diagnostics, unrestricted exports, secrets, or protected prompts.

## 16. Exact logical API operation inventory

Existing Evidence/Supporting File operations remain and are reused. PATCH-055 adds/composes these logical operations:

| ID | Purpose | Actor | Mutation |
|---|---|---|---|
| EVW-01 | list Workbench Evidence/files with allowed actions | authorized Project/Workspace member | no |
| EVW-02 | create proposed Evidence | authorized Evidence creator | yes |
| EVW-03 | transition Evidence lifecycle | authorized Human reviewer | yes |
| EVW-04 | view Evidence lineage/reliance | authorized Project/Workspace member | no |
| RET-01 | read current retention state | authorized subject reader | no |
| RET-02 | apply/replace retention basis | authorized retention administrator | yes |
| RET-03 | place hold | authorized retention administrator | yes |
| RET-04 | release hold | authorized retention administrator | yes |
| RET-05 | record Human disposition decision | authorized retention administrator | yes |
| EXP-01 | request governed export | authorized subject reader/exporter | yes |
| EXP-02 | get export status/result metadata | requesting/authorized actor | no |
| REC-01 | request historical recovery | authorized subject reader/recovery actor | yes |
| REC-02 | get recovery status | requesting/authorized actor | no |

Exact HTTP routes, DTO names and status codes belong in IDS. No raw object-store route, generic file browser, bulk tenant export, automatic purge endpoint, or arbitrary recovery locator is allowed.

## 17. Frontend contract

Commercial V1 SHALL provide one coherent Evidence Workbench with these surfaces:

1. Supporting File intake/status/download;
2. proposed Evidence creation;
3. exact file linkage;
4. Evidence review/lifecycle decision;
5. lineage and accepted-Report reliance display;
6. retention/hold/disposition panel;
7. governed export/recovery panel.

The UI MUST preserve explicit Human-authority language. `available` file means scanner-cleared, not engineering-approved. `eligible` retention means disposition-eligible, not deletion-approved.

Selectors show authorized labels and status, never require raw IDs. Protected/not-found, stale/conflict, temporarily unavailable, and recovery states are explicit and non-destructive. Keyboard access, visible focus, responsive layout, semantic labels, live-region updates, and RTL-safe layout are required. Technical identifiers use isolated LTR rendering.

## 18. Exact Commercial V1 limits

| Resource | Exact limit |
|---|---:|
| Evidence page size | default 20, maximum 100 |
| Supporting Files linked to one Evidence | maximum 32 |
| active holds per RetentionSubject | exactly 0 or 1 |
| retention-governance current heads per typed subject | exactly 1 |
| historical retention revisions per page | maximum 100 |
| Evidence lineage depth returned per request | maximum 32 |
| export subjects per request | maximum 32 |
| aggregate export metadata entries | maximum 64 |
| recovery subjects per request | exactly 1 |
| mutation retry attempts for retryable transaction conflicts | maximum 3 |

Limits MUST fail without partial authoritative success. EDS does not set arbitrary maximum retained file bytes beyond existing Supporting File intake/storage policy; export/recovery byte-stream implementation bounds belong in IDS and operational policy.

## 19. Failure contract

Internal reasons include `INVALID_RETENTION_BASIS`, `RETENTION_NOT_EXPIRED`, `ACTIVE_HOLD`, `RETENTION_INDEFINITE`, `ELIGIBILITY_INDETERMINATE`, `VERSION_CONFLICT`, `IDEMPOTENCY_CONFLICT`, `CONTENT_UNAVAILABLE`, `INTEGRITY_FAILURE`, `EXPORT_UNAVAILABLE`, and `RECOVERY_UNAVAILABLE`.

Existence-sensitive failures collapse to `protected_not_found`. Authorized known-resource failures map to safe `conflict`, `not_permitted`, `unavailable`, or `indeterminate` outcomes. No response exposes foreign Organization identity, hidden count, object-store locator, or retention policy detail the caller is not authorized to see.

## 20. Security and historical integrity contract

The future implementation SHALL prove:

- wrong-Organization direct IDs disclose no existence or counts;
- authorization precedes validation, idempotency replay, export and recovery;
- forged Evidence/File/retention/hold handles fail safely;
- stale retention/hold versions cannot complete a conflicting decision;
- accepted Report/Memory historical basis remains byte/meaning immutable;
- current content-access denial does not erase safe historical provenance;
- export/recovery never bypass Supporting File integrity and authorization;
- runtime persistence cannot create duplicate current retention heads or two active holds for one subject;
- no automatic physical purge path exists.

## 21. Migration expectations

A migration is required only if accepted IDS proves new retention/export/recovery persistence is necessary. Any migration SHALL be additive, preserve existing Evidence/Supporting File/Report/Memory history, and perform no fabricated retention backfill that claims a policy decision not actually made.

For pre-existing subjects lacking retention governance, the truthful state is `not_established` at transport/UI level until a valid default or Human decision is applied. Existing accepted Reports and Memory records are never rewritten.

Fresh install, upgrade, downgrade/forward-repair, and historical recovery qualification are mandatory if persistence changes are introduced. This EDS reserves no Alembic revision.

## 22. Conformance manifest — 48 vectors

Future deterministic acceptance SHALL contain exactly 48 stable vectors in these groups:

- Evidence Workbench workflow: 10;
- retention subject/basis/versioning: 8;
- hold and disposition eligibility: 8;
- export and recovery: 8;
- Organization isolation/security/idempotency/concurrency: 8;
- UI/accessibility/RTL/historical Report-Memory integrity: 6.

The vector IDs SHALL be `P055-EVW-01..10`, `P055-RET-01..08`, `P055-HLD-01..08`, `P055-XRC-01..08`, `P055-SEC-01..08`, and `P055-UX-01..06`. IDS may assign exact fixtures and commands but MUST NOT alter counts or semantic group ownership without EDS reapproval.

## 23. Explicit exclusions

PATCH-055 SHALL NOT add OCR, semantic extraction/classification, embeddings, generic EDMS folders/workflows, enterprise records schedules, arbitrary customer retention engines, automatic physical purge, autonomous AI retention/disposition, procurement/vendor workflows, PATCH-056 Methods & Systems, PATCH-057 Command Center completion, PATCH-058..060 commercial auth/release/seats/deployment, or post-PATCH-060 capability.

## 24. IDS-055 obligations

IDS-055, only after separate authority, must freeze:

- exact physical persistence topology and constraints;
- typed RetentionSubject representation and uniqueness enforcement;
- repository/UoW boundaries and transaction order;
- exact role predicates mapped to existing authorization;
- API routes, DTOs, errors and idempotency headers;
- object-storage/export/recovery adapter contracts and byte-stream bounds;
- Audit/outbox schema and redaction;
- migration necessity, revision(s), upgrade/downgrade/forward-repair;
- exact frontend files/components and state-machine behavior;
- exact 48-vector fixtures, commands and expected results;
- rollback and operational observability.

## 25. EDS self-review

The candidate was checked against accepted ADR-028, the PATCH-055 Discovery, current Evidence lifecycle/API, Supporting File scanner semantics, Technical Report historical Evidence basis, Organizational Memory Human authority, Quality Gates, and Manifesto v1.0.

Both inherited Architecture observations are resolved at EDS level: `A055-OBS-01` by the typed RetentionSubject contract and one-head rule; `A055-OBS-02` by the explicit post-export boundary statement.

No new ADR-level decision is introduced. No implementation claim is made.

Self-review result: **PASS / COMPLETE**.

Critical/Major/Minor/Observation: **0 / 0 / 0 / 0**.

## 26. Governance disposition

`EDS-055: COMPLETE / READY FOR INDEPENDENT EDS REVIEW`

Human EDS acceptance is not implied. IDS-055, implementation, migration, staging, commit, push and PATCH-056+ remain unauthorized.
