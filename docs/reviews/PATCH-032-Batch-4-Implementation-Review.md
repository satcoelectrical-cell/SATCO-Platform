# Independent PATCH-032 Batch 4 Review — Transaction and Audit

## 1. Review Information

| Field | Value |
|---|---|
| Related PATCH | PATCH-032 — Technical Report |
| Batch | Batch 4 — Transaction and Audit |
| Work steps | S11–S12 only |
| Review type | Independent implementation review |
| Review date | 2026-08-10 |
| Review status | COMPLETE |
| Verdict | FAIL |
| Batch 4 acceptance readiness | BLOCKED |
| Later Batch authority | NOT GRANTED |

## 2. Authoritative Sources

- ADR-023 — Human-Accepted AI-Assisted Technical Reports
- EDS-032 — Technical Report
- IDS-032 — Technical Report Implementation Design, especially §§14–15
- Implementation-Plan-032, S11–S12 and §§9–10
- `docs/implementation/PATCH-032-Batch-4-Authorized-File-Manifest.md`
- accepted Batch 1–3 implementation and review evidence
- existing SATCO Audit and Unit of Work conventions

## 3. Scope and File Boundary

The Batch 4 implementation remains inside the exact authorized two-file
boundary:

- modified `backend/app/repositories/technical_report_unit_of_work.py`; and
- created `backend/tests/test_technical_report_transaction.py`.

No Batch 5 service, AI, API, router, frontend, migration, configuration,
canonical-capability, or background-processing behavior was introduced. Scope
control is **PASS**.

## 4. Findings Summary

| Severity | Count | IDs |
|---|---:|---|
| Critical | 1 | `B4-CRIT-01` |
| Major | 5 | `B4-MAJ-01`, `B4-MAJ-02`, `B4-MAJ-03`, `B4-MAJ-04`, `B4-MAJ-05` |
| Minor | 0 | None |

## 5. Critical Finding

### B4-CRIT-01 — Acceptance-critical authority and source predicates are not locked or rechecked by the UoW

- **Severity:** CRITICAL
- **Implementation surface:** `backend/app/repositories/technical_report_unit_of_work.py:309-336` and the absence of any `with_for_update`, final predicate-recheck, UoW-bound authorization policy, or UoW-bound reference validator in the module
- **Authoritative source:** IDS-032 §§14.1–14.2; Implementation-Plan-032 S11 and §10; Batch 4 Manifest §§5, 9, and 12
- **Repository evidence:** `SqlAlchemyTechnicalReportUnitOfWork.__enter__` composes the repository, historical resolver, Audit, outbox, and idempotency adapters, but does not compose the `authorization` or `references` collaborators required by `TechnicalReportUnitOfWork`. It exposes no lock/recheck operation for active User, Organization, selected membership, Workspace, optional Project, Human Owner, exact draft revision, or mutable canonical-source identity/version/state. The Batch 3 historical resolver performs ordinary reads and does not lock mutable acceptance predicates.
- **Exact issue:** The accepted design requires every mutable acceptance-authority, context, source, version, and availability predicate to be locked or rechecked immediately before acceptance compare-and-change and commit. The Batch 4 UoW provides no enforceable mechanism for that final check.
- **Risk:** Authority, membership, scope, ownership, source state, or source version may change after disclosure validation but before commit, allowing an accepted report to be committed against revoked authority or stale historical meaning.
- **Required correction:** Within explicitly reconciled authority, implement typed UoW-bound authorization/reference and final mutable-predicate lock/recheck behavior using the same authoritative Session, then prove membership, owner, Workspace/Project, source-version/state, draft-version/revision, and acceptance race failures roll back all state. If the accepted port/file boundary cannot express this behavior, stop and reconcile that contract before remediation.

## 6. Major Findings

### B4-MAJ-01 — Atomicity tests do not exercise report or provenance mutation through the real UoW

- **Severity:** MAJOR
- **Implementation surface:** `backend/tests/test_technical_report_transaction.py:108-180`
- **Authoritative source:** IDS-032 §§14–15 and §28; Implementation-Plan-032 S11 and §§9–10; Batch 4 Manifest §§6, 9, and 13
- **Repository evidence:** The UoW success/rollback tests use a `MagicMock` Session. The PostgreSQL success test directly calls the three side-record adapters on `db_session`; it does not use `SqlAlchemyTechnicalReportUnitOfWork`. The rollback test creates and flushes the report before opening its savepoint, stages only Audit/outbox/idempotency inside the savepoint, and adds no provenance or report mutation.
- **Exact issue:** Passing evidence proves that three side records can share a Session and that a savepoint removes those side records. It does not prove atomic report/provenance/Audit/outbox/idempotency success, acceptance compare-and-change, or rollback after each staged failure.
- **Risk:** Partial acceptance or misleading success accountability can survive defects that the current tests cannot detect.
- **Required correction:** Add real PostgreSQL tests using the actual UoW that stage report and provenance mutation with Audit, outbox, and idempotency, commit once, and inject failure before and after each staged component to prove every authoritative row remains unchanged after rollback. Include acceptance-state and draft-state cases without beginning Batch 5 orchestration.

### B4-MAJ-02 — Rejection Audit cannot represent or enforce the accepted bounded record

- **Severity:** MAJOR
- **Implementation surface:** `backend/app/repositories/technical_report_unit_of_work.py:278-306`, `backend/app/ports/technical_report.py:152-160`, and `backend/tests/test_technical_report_transaction.py:231-275`
- **Authoritative source:** IDS-032 §15.2; Implementation-Plan-032 S12 and §10; Batch 4 Manifest §10
- **Repository evidence:** The rejection recorder stores outcome, Organization, command ID, and correlation ID, but has no distinct stable reason category/code. The test embeds `authorization_denied` into the operation string. `TechnicalReportAuditRecord.report_id` is mandatory, so the adapter cannot omit a protected or not-safely-known target. The adapter itself accepts every record category and the tests do not prove it runs only after authoritative rollback or that ordinary failures produce no rejection row.
- **Exact issue:** The persisted rejection shape and call boundary do not implement the accepted minimum/maximum disclosure contract or category restriction.
- **Risk:** Rejection Audit may lose accountability meaning, disclose a protected target identity, or become an existence oracle/routine validation log.
- **Required correction:** Provide a closed typed rejection-Audit record with a stable reason code and optional safely-known target identity, restrict it to the four accepted security/authority categories after rollback, and add database-backed category, omission, plaintext, ordinary-failure, ordering, and failure-isolation tests. Preserve the original protected error regardless of Audit failure.

### B4-MAJ-03 — Idempotency cannot detect a reused key with a different request fingerprint

- **Severity:** MAJOR
- **Implementation surface:** `backend/app/repositories/technical_report_unit_of_work.py:216-275`, `backend/app/ports/technical_report.py:207-212`, and `backend/tests/test_technical_report_transaction.py:210-228`
- **Authoritative source:** IDS-032 §§14.2, 20, and 25; Implementation-Plan-032 §§9–10; Batch 4 Manifest §§6 and 9
- **Repository evidence:** `reserve` persists a fingerprint, but `find` accepts only a key and returns a completed result without comparing the current request fingerprint. A duplicate pending or completed reservation is left to a raw uniqueness failure. Tests cover malformed digest text and missing reservation only; they do not cover exact replay or different-fingerprint conflict.
- **Exact issue:** The accepted exact-replay/fingerprint-conflict rule is not enforceable through the implemented store contract.
- **Risk:** A different command payload can reuse an idempotency key and receive an unrelated stored result, or expose a database exception instead of the stable idempotency-conflict outcome.
- **Required correction:** Reconcile the typed idempotency lookup contract to require the current fingerprint, compare it in the persistence adapter, map pending/different fingerprints to the stable conflict, preserve exact completed replay, and add concurrent reservation, exact replay, different-fingerprint, rollback, and plaintext-free result tests.

### B4-MAJ-04 — Outbox payload omits required accepted event accountability fields

- **Severity:** MAJOR
- **Implementation surface:** `backend/app/repositories/technical_report_unit_of_work.py:129-153` and `backend/app/models/technical_report_command.py:612-618`
- **Authoritative source:** IDS-032 §15; Implementation-Plan-032 Workstreams G/L and S11; Batch 4 Manifest §§5 and 9
- **Repository evidence:** The outbox payload contains only report ID, aggregate version, command ID, correlation ID, and occurrence time. It cannot contain Organization, Workspace, optional Project, purpose, lifecycle, draft revision ID, actor ID, causation ID, authorized predecessor ID, or source-entry count because the accepted event contract currently exposes none of those values.
- **Exact issue:** The persisted Domain Event does not meet the minimum event contract recorded by IDS-032.
- **Risk:** Downstream processing lacks the stable scope, authority, lifecycle, revision, and causation context required for accountable event interpretation.
- **Required correction:** Reconcile and implement the closed typed event contract with every IDS-required non-plaintext field, persist that exact payload atomically, and add per-event positive, closed-shape, coherence, and plaintext-exclusion tests. Do not add dispatch or Batch 5 behavior.

### B4-MAJ-05 — The concrete UoW does not satisfy the accepted inward UoW contract

- **Severity:** MAJOR
- **Implementation surface:** `backend/app/repositories/technical_report_unit_of_work.py:309-336` versus `backend/app/ports/technical_report.py:218-231`
- **Authoritative source:** IDS-032 §§10–14; Implementation-Plan-032 Workstream G and S11; Batch 4 Manifest §§5 and 9
- **Repository evidence:** The inward `TechnicalReportUnitOfWork` requires `technical_reports`, `authorization`, `references`, `historical`, `audit`, `domain_events`, and `idempotency`. The concrete UoW never defines `authorization` or `references`. No structural conformance test exists.
- **Exact issue:** A later accepted service cannot use the concrete object through the accepted Unit of Work port without missing collaborators or bypassing the authoritative Session.
- **Risk:** Batch 5 would be forced to widen scope, use independently scoped collaborators, or bypass the accepted authorization-before-disclosure transaction design.
- **Required correction:** Add the accepted same-Session typed collaborators within reconciled authority and add static/runtime structural conformance evidence. Do not implement application use cases.

## 7. Preserved Boundaries

- Repository no-commit: **PASS**. No commit call exists in
  `technical_report_repository.py`; the sole authoritative success commit is
  exposed by the UoW.
- Accepted-state immutability: existing Batch 1–3 implementation and regression
  evidence remain passing; Batch 4 introduces no direct accepted-state bypass.
- Authorization-before-disclosure: Batch 3 resolver behavior remains unchanged,
  but final transaction-time authority/source preservation is **FAIL** under
  `B4-CRIT-01`.
- Scope control: **PASS**. No Batch 5 or later implementation was introduced.

## 8. Independent Validation Evidence

- `docker exec -e TEST_DATABASE_URL=postgresql://satco:satco_password@postgres:5432/satco_platform_patch02022_test satco-backend python -m pytest -q tests/test_technical_report_transaction.py` — **9 passed**.
- `docker exec -e TEST_DATABASE_URL=postgresql://satco:satco_password@postgres:5432/satco_platform_patch02022_test satco-backend python -m pytest -q tests/test_technical_report_repository.py tests/test_technical_report_migration.py tests/test_technical_report_database_roles.py tests/test_technical_report_aggregate.py tests/test_technical_report_schemas.py` — **320 passed**.
- `docker exec -e TEST_DATABASE_URL=postgresql://satco:satco_password@postgres:5432/satco_platform_patch02022_test satco-backend python -m pytest -q --disable-warnings` — **829 passed, 0 failed**.
- Static compilation of the Batch 4 production and test files — **PASS**.
- Direct import of the UoW and rejection-Audit adapter — **PASS**.
- Repository no-commit scan — **PASS**.
- Exact Batch 4 implementation file boundary — **PASS**.
- `git diff --check` before creating this review artifact — **PASS**.

Passing tests do not override the unimplemented transaction-time authority
recheck or the material evidence gaps recorded above.

## 9. Verdict

```text
Independent PATCH-032 Batch 4 Review: COMPLETE
Review verdict: FAIL
Critical findings: 1 — B4-CRIT-01
Major findings: 5 — B4-MAJ-01 through B4-MAJ-05
Minor findings: 0
Transaction boundary: FAIL
Rollback atomicity: FAIL
Audit semantics: FAIL
Repository no-commit rule: PASS
Authorization/immutability preservation: FAIL
Scope control: PASS
Batch 4 acceptance readiness: BLOCKED
Later Batch authority: NOT GRANTED
```

## 10. Required Next Action

Perform a focused Batch 4 authority/contract reconciliation for the accepted
UoW authorization/reference, rejection-Audit, idempotency-fingerprint, and
Domain Event shapes where the current two-file boundary is insufficient. Then
authorize and implement focused Batch 4 remediation for `B4-CRIT-01` and
`B4-MAJ-01` through `B4-MAJ-05`, followed by a focused Independent Batch 4
re-review. Do not begin Batch 5.

## 11. Focused Independent Batch 4 Re-review

### 11.1 Review record

| Field | Result |
|---|---|
| Review date | 2026-08-11 |
| Review scope | `B4-CRIT-01`, `B4-MAJ-01` through `B4-MAJ-05` |
| Reconciled implementation boundary | Seven authorized files |
| Re-review status | COMPLETE |
| Verdict | FAIL |
| Batch 4 acceptance readiness | BLOCKED |
| Batch 5 authority | NOT GRANTED |

The original review and its FAIL evidence remain authoritative history. This
section records only the focused assessment of the subsequent remediation.

### 11.2 Remediated-finding assessment

#### B4-CRIT-01 — NOT RESOLVED

The concrete UoW now composes authorization, reference, historical-resolution,
and final-recheck collaborators over the same SQLAlchemy Session, and the
final-recheck path locks the report and top-level canonical source row. The
accepted final predicate boundary is nevertheless incomplete:

- `SqlAlchemyTechnicalReportAuthorizationPolicy.require` locks the Workspace
  but does not validate its active status;
- the optional Project comparison is performed, but the focused tests do not
  prove Workspace-status or Workspace/Project-binding revocation races;
- Engineering Relationship historical resolution rechecks related Engineering
  Objects and Evidence using ordinary reads rather than locking those mutable
  acceptance predicates; and
- the focused source-race evidence exercises only Engineering Object version,
  not the complete four-source mutable state/version matrix required by
  IDS-032.

The same-Session composition is a material improvement, but it does not yet
prove that every mutable authority, context, and historical-source predicate is
locked or rechecked immediately before compare-and-change and commit.

#### B4-MAJ-01 — NOT RESOLVED

The new PostgreSQL tests use the actual UoW and prove that a direct draft-field
mutation, one provenance insert, Audit, outbox, and idempotency can commit or
roll back together at each staged failure point. They do not exercise the
repository expected-version compare-and-change contract, a coherent
`draft -> accepted` mutation, accepted-snapshot persistence, or acceptance
provenance finalization. The required acceptance-state atomicity case therefore
remains unproved.

#### B4-MAJ-02 — NOT RESOLVED

The remediation adds a closed typed rejection record, four stable reason
categories, an optional safely-known report identifier, plaintext-minimal
payloads, and failure isolation. The tests invoke the rejection recorder in
isolation; they do not prove that it is invoked only after the authoritative
UoW has rolled back, that an ordinary validation/version/business failure
creates no rejection row, or that Audit failure preserves the original
protected application error through the actual failure path. The required
ordering and category-boundary evidence remains absent.

#### B4-MAJ-03 — NOT RESOLVED

The idempotency lookup is now fingerprint-aware, exact completed replay works,
and pending/different-fingerprint states map to the stable conflict exception.
The focused tests use one Session and do not execute a genuine concurrent
two-transaction reservation race. Consequently the accepted concurrent
reservation behavior and stable conflict mapping are not yet materially
proved.

#### B4-MAJ-04 — NOT RESOLVED

The closed event and outbox payload now contain the required non-plaintext
scope, lifecycle, revision, actor, causation, predecessor, and source-count
fields. Aggregate event names remain lowercase snake case
(`technical_report_draft_created`, `technical_report_draft_revised`,
`technical_report_accepted`, and `technical_report_successor_created`) rather
than the exact closed IDS-032 event types (`TechnicalReportDraftCreated`,
`TechnicalReportDraftRevised`, `TechnicalReportAccepted`, and
`TechnicalReportSuccessorCreated`). The persisted payload therefore does not
yet match the accepted event contract exactly.

#### B4-MAJ-05 — RESOLVED

The concrete UoW now exposes the repository, same-Session authorization,
same-Session references, historical resolver, Audit, Domain Event,
idempotency, and final-recheck collaborators required by the accepted inward
contract. Focused structural/runtime evidence verifies these collaborators,
and no Batch 5 use-case surface has been added.

### 11.3 New findings

No new Critical, Major, or Minor finding is raised. The remaining defects are
continuations of the original findings listed above.

### 11.4 Validation evidence

- Focused Batch 4 and affected aggregate tests: **BLOCKED BY ENVIRONMENT**.
  Docker was unavailable at
  `unix:///Users/mac/.docker/run/docker.sock`; the repository virtual
  environment could not connect to the isolated PostgreSQL test database.
- Relevant Technical Report regressions: **BLOCKED BY ENVIRONMENT** for the
  same reason.
- Full backend regression: **BLOCKED BY ENVIRONMENT** for the same reason.
- Static compilation of the seven authorized production/test files: **PASS**.
- Direct imports of the UoW, rejection recorder, inward UoW port, and final
  recheck port: **PASS**.
- `git diff --check`: **PASS**.
- Previously accepted Batch 1–3 code remains outside this remediation's
  implementation changes, and no Batch 5 service, API, AI, dispatch, or
  background behavior was introduced.

Historical passing test reports are not substituted for the required current
independent execution. The unresolved contract and evidence findings already
require a FAIL verdict independently of the unavailable database runner.

### 11.5 Focused verdict

```text
Focused Independent PATCH-032 Batch 4 Re-review: COMPLETE
B4-CRIT-01: NOT RESOLVED
B4-MAJ-01: NOT RESOLVED
B4-MAJ-02: NOT RESOLVED
B4-MAJ-03: NOT RESOLVED
B4-MAJ-04: NOT RESOLVED
B4-MAJ-05: RESOLVED
New Critical findings: 0
New Major findings: 0
New Minor findings: 0
Final recheck/locking: FAIL
Transaction atomicity: FAIL
Rejection Audit: FAIL
Idempotency semantics: FAIL
Domain Event/outbox: FAIL
UoW conformance: PASS
Verdict: FAIL
Batch 4 acceptance readiness: BLOCKED
Batch 5 authority: NOT GRANTED
```

### 11.6 Required next action

Perform a second focused Batch 4 remediation for `B4-CRIT-01` and
`B4-MAJ-01` through `B4-MAJ-04`, preserving the resolved `B4-MAJ-05` contract,
then repeat the focused Independent Batch 4 re-review. Do not begin Batch 5.

## 12. Second Focused Independent Batch 4 Re-review

### 12.1 Review Control

| Field | Result |
|---|---|
| Review date | 2026-08-11 |
| Review scope | Latest focused remediation of `B4-CRIT-01` and `B4-MAJ-01` through `B4-MAJ-04`; preservation of `B4-MAJ-05` |
| Re-review status | COMPLETE |
| Verdict | PASS |
| Batch 4 acceptance readiness | READY |
| Batch 5 authority | NOT GRANTED |

The original Independent Review `FAIL` and first focused re-review `FAIL`
remain preserved above as historical evidence. This section records the final
focused re-review after the second remediation.

### 12.2 Final Finding Disposition

| Finding | Final status |
|---|---|
| `B4-CRIT-01` | RESOLVED |
| `B4-MAJ-01` | RESOLVED |
| `B4-MAJ-02` | RESOLVED |
| `B4-MAJ-03` | RESOLVED |
| `B4-MAJ-04` | RESOLVED |
| `B4-MAJ-05` | RESOLVED / PRESERVED |

No new Critical, Major, or Minor findings were identified.

### 12.3 Verified Outcomes

- same-Session final authority/reference recheck and locking: **PASS**;
- real Unit of Work atomic success and rollback across report, provenance,
  Audit, outbox, and idempotency: **PASS**;
- closed bounded post-rollback rejection Audit: **PASS**;
- fingerprint-aware exact replay, conflict, and concurrent reservation
  semantics: **PASS**;
- exact closed non-plaintext IDS Domain Event/outbox contract: **PASS**;
- concrete UoW inward-contract conformance: **PASS**;
- accepted Batch 1–3 behavior preservation: **PASS**; and
- absence of Batch 5 behavior: **PASS**.

### 12.4 Validation Evidence

| Validation | Result |
|---|---|
| Focused Batch 4 transaction and Aggregate tests | 75 passed, 0 failed |
| Relevant Technical Report regression | 354 passed, 0 failed |
| Full backend regression | 854 passed, 0 failed |
| Static/import validation | PASS |
| `git diff --check` | PASS |

### 12.5 Final Verdict

```text
Second Focused Independent PATCH-032 Batch 4 Re-review: COMPLETE
Verdict: PASS
Critical findings: 0
Major findings: 0
Minor findings: 0
Batch 4 acceptance readiness: READY
Batch 5 authority: NOT GRANTED
```

The exact next governance action is Human PATCH-032 Batch 4 Acceptance and
Closure. This re-review grants no Batch 5 authority.
