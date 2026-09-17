# IDS-055 Independent Review — Commercial Evidence Workbench & Minimum Retention Governance

Date: 2026-09-14
PATCH: PATCH-055
Review scope: QG-4 / IDS-055 only
Reviewer: independent ChatGPT architecture/contract review

## Authority boundary

This review assesses IDS-055 against accepted ADR-028, accepted EDS-055,
SATCO Quality Gates, and actual repository seams. It does not authorize or
perform implementation, migration creation/execution, database mutation,
staging, commit, push, deployment, or PATCH-056+ work.

## Evidence reviewed

- `docs/adr/ADR-028-Commercial-Evidence-Workbench-and-Minimum-Retention-Governance.md`
- `docs/design/EDS-055-Commercial-Evidence-Workbench-and-Minimum-Retention-Governance.md`
- `docs/design/IDS-055-Commercial-Evidence-Workbench-and-Minimum-Retention-Governance.md`
- `docs/framework/08_Quality_Gates.md`
- existing repository Audit, Technical Report and Organizational Memory
  idempotency/outbox/UoW seams
- prior repository-specific IDS-054 implementation-contract pattern

## Gate standard

QG-4 requires an exact implementation contract. READY criteria additionally
require exact file, model, API, migration, error, and test contracts.
## Findings

### P055-IDS-MAJ-01 — retention head contradicts accepted EDS exact record

EDS-055 section 5 says a retention-governance head has exactly thirteen
semantic elements, including hold status/active-hold reference, computed
eligibility, current disposition decision, predecessor, and deterministic
record digest.

IDS-055 `retention_records` omits hold status/active-hold reference, current
disposition decision, and deterministic record digest, and section 10 states
eligibility MUST NOT be stored as an independent source of truth. The latter
can be valid only if the persisted head still satisfies the accepted EDS
record contract through an explicit authoritative projection/materialization
contract. That mapping is not defined.

Result: MAJOR / QG-4 blocking until the physical representation is reconciled
without changing EDS semantics.

### P055-IDS-MAJ-02 — hold physical contract is incomplete versus EDS

EDS-055 section 6 requires hold_id, typed subject, status, reason_code,
rationale, authority_reference, placed/released actor/time and rationale,
version, predecessor, and digest.

IDS-055 section 8 specifies only row id, subject scope, status, free-text
reason, placement/release fields, release_reason, and version. It does not
freeze reason_code, authority_reference, predecessor, digest, or a clear
stable logical hold identity/revision representation.
Result: MAJOR / QG-4 blocking.

### P055-IDS-MAJ-03 — required repository-specific authorization/API contract is not exact

EDS-055 section 24 requires exact role predicates mapped to existing
authorization plus exact API routes, DTOs, errors, and idempotency headers.
IDS-055 defines general authorization ordering and routes, but does not freeze
role predicates against actual SATCO roles/project/workspace predicates, DTO
names, exact HTTP status mapping, or an exact idempotency-header contract.
`idempotency_key` is currently described as request-body data.

Result: MAJOR / QG-4 blocking.

### P055-IDS-MAJ-04 — storage/export/recovery implementation contract is incomplete

EDS-055 requires object-storage/export/recovery adapter contracts and
byte-stream bounds. IDS-055 correctly prohibits raw storage locators and
preserves authorization/integrity, but does not freeze the repository adapter
interfaces, exact storage seams, streaming bounds, export artifact handling,
or recovery resolver behavior sufficiently for implementation without new
design decisions.

Result: MAJOR / QG-4 blocking.

### P055-IDS-MAJ-05 — exact implementation/file/frontend manifest is missing

QG-4/READY and EDS-055 require exact file/model/API/migration contracts and
exact frontend files/components/state-machine behavior. IDS-055 describes
logical tables and UI behavior but does not identify the exact backend and
frontend files to create/modify or component/service/repository seams.
Result: MAJOR / QG-4 blocking.

### P055-IDS-MAJ-06 — 48-vector manifest lacks exact executable qualification contract

The 48 IDs and semantic grouping are preserved correctly. However EDS-055
requires exact fixtures, commands, and expected results at IDS level. IDS-055
explicitly defers exact test files, fixtures, and commands to implementation
planning. That is later than the accepted EDS permits.

Result: MAJOR / QG-4 blocking.

### P055-IDS-MAJ-07 — rollback and operational observability are not frozen

EDS-055 section 24 requires rollback and operational observability. Quality
Gates require executable rollback/forward-repair evidence. IDS-055 contains
historical migration qualification and safe outbox metadata, but no exact
application rollback boundary, migration downgrade/forward-repair decision,
feature/traffic disablement seam, operational metrics/logging, or alert-safe
redaction contract.

Result: MAJOR / QG-4 blocking.

### P055-IDS-MAJ-08 — outbox/idempotency physical choice needs repository-aware closure

The repository already uses capability-owned Technical Report and
Organizational Memory idempotency/outbox patterns and shared `audit_logs`.
A capability-owned PATCH-055 pair can therefore be consistent, but IDS-055
must explicitly map `retention_idempotency` and `retention_outbox` to those
existing patterns, including state columns, replay/result bounds, publication
semantics, allowed updates, uniqueness, and safe payload constraints.
Result: MAJOR / QG-4 blocking.

## Positive findings

- PATCH-055 scope and PATCH-056+ exclusion are preserved.
- Engineering Evidence lifecycle remains orthogonal to retention governance.
- scanner `disposition` is not overloaded.
- automatic physical purge remains excluded.
- accepted Technical Report/Memory historical provenance remains immutable.
- authorization-before-protected-disclosure is preserved.
- export post-boundary semantics correctly resolve A055-OBS-02.
- typed RetentionSubject and one-current-head intent resolve A055-OBS-01 at
  semantic level.
- legacy `not_established` behavior avoids fabricated retention history.
- 48/48 vector IDs and EDS grouping are preserved.
- QG-M1 principles are not contradicted by the candidate design.

## Finding count and verdict

Critical: 0
Major: 8
Minor: 0
Observation: 0

Blocking findings: 8.

Independent IDS-055 Review verdict:

**FAIL / RETURN TO IDS-055 CORRECTION**

QG-4: **NOT PASSED**.
Human IDS acceptance: **NOT READY**.
Implementation Plan / implementation / migration / staging / commit / push:
**NOT AUTHORIZED**.

# IDS-055 Independent Re-Review — after QG-4 correction addendum

Date: 2026-09-14
Scope: corrected IDS-055 sections 31.1–31.13 against accepted ADR-028, accepted EDS-055, first-review findings, repository seams, and QG-4 exactness requirements.

## Re-review boundary

This re-review is design review only. It does not authorize Implementation Plan, source/test/frontend changes, migration creation/execution, database mutation, stage, commit, push, deployment, or PATCH-056+.

## Prior finding closure

### P055-IDS-MAJ-01 — CLOSED

The corrected IDS now defines `RetentionGovernanceHeadV1` as the authoritative authorized projection satisfying the accepted EDS head semantics, adds deterministic `record_digest`, freezes predecessor mapping, and preserves eligibility as computed rather than client-authored. Repository-native key types and retain-until clock validation are explicit.

### P055-IDS-MAJ-02 — CLOSED

Hold persistence is now an exact append-only revision contract with stable logical hold identity, reason code, rationale, authority reference, placement/release facts, predecessor, digest, version, current marker, and partial uniqueness enforcing at most one active current hold per typed subject.

### P055-IDS-MAJ-03 — CLOSED

Roles are mapped to actual SATCO `admin`/`engineer` authorization seams and Project/Workspace predicates. Mutation authority is exact. DTO names, routes, `Idempotency-Key` header semantics, bounded fields, and exact HTTP outcome mapping are frozen.

### P055-IDS-MAJ-04 — CLOSED

The corrected IDS now freezes reuse of the existing Supporting File exact-key/version object-store seam, exact export/recovery ports, 1 MiB streaming chunks, existing 25 MiB per-file bound, aggregate export bound, private export artifact receipt persistence, integrity verification, and the exact protected export-content route. Recovery remains availability-only and cannot alter engineering authority.

### P055-IDS-MAJ-05 — CLOSED

Exact backend create/modify files, frontend create/modify files, router composition file, route mount file, and state-machine behavior are now frozen. Existing Evidence/Supporting File backend owners are consumed unchanged rather than left as an unspecified modification seam.

### P055-IDS-MAJ-06 — CLOSED

The exact 48-vector ownership remains 42 backend + 6 frontend. Exact test modules, canonical fixture inventory, focused commands, full-regression commands, manifest integrity assertions, and expected-result authority through the already-frozen section-27 row semantics are specified without changing EDS IDs or counts.

### P055-IDS-MAJ-07 — CLOSED

Application rollback, additive migration downgrade refusal/forward-repair behavior, sole-head condition, exact operational metric families, structured-log redaction, and readiness alert conditions are frozen. The migration design identifier is `e05500000001` with down-revision `e05400000006`, conditional on confirming that historical head before implementation.

### P055-IDS-MAJ-08 — CLOSED

The repository-aware choice is explicit: shared `audit_logs` plus capability-owned `retention_idempotency` and `retention_outbox`, matching existing SATCO capability patterns. Exact state columns, uniqueness, replay/result safety, publication bookkeeping, immutable payload behavior, event/audit codes, and redaction constraints are frozen.

## Re-review finding count and verdict

Critical: 0
Major: 0
Minor: 0
Observation: 0

The corrected IDS preserves PATCH-055 scope, Human authority, protected non-disclosure, immutable accepted Report/Memory provenance, scanner/retention separation, no automatic physical purge, and the exact 48-vector EDS boundary.

Independent IDS-055 re-review verdict:

**PASS / QG-4 SATISFIED / READY FOR HUMAN IDS ACCEPTANCE**

This PASS is not Human IDS acceptance. Implementation Plan, implementation, migration creation/execution, staging, commit, push, deployment, and PATCH-056+ remain unauthorized until the next explicit governance decision.
