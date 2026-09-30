# PATCH-059 — Batch B Checkpoint

## 1. Checkpoint identity

PATCH: PATCH-059 — Commercial Package Configuration, Seats & Signed Entitlements

Batch: B — entitlement state, anti-rollback, trusted time and seats

Batch B implementation candidate:

`8411d8b6f469a5b59fdfb274cb1d0a9c94214cc7`

Implementation branch:

`patch-059-implementation`

Batch A checkpoint base:

`9e6b657d61c84768e49887774d14ab96939cbad3`

Batch B bounded implementation commits:

- `f8aa847fb454270f018e60b045eb06f1e98087d5` — commercial entitlement transaction foundation
- `6d610721c48f4a021e3e6f453224a0c0e0d00ee2` — entitlement activation and trusted time
- `8411d8b6f469a5b59fdfb274cb1d0a9c94214cc7` — commercial seat lifecycle

This checkpoint is implementation evidence only. It is not PATCH-059 release approval, closure, deployment authorization, or authorization to begin PATCH-060.

## 2. Authoritative Batch B scope

The accepted PATCH-059 Implementation Plan requires Batch B to implement:

- commercial entitlement state/service;
- validate preview and activate repeat-validation;
- monotonic revision/high-water behavior;
- equal-revision idempotency/conflict handling;
- deterministic state/advisory locking;
- injectable server UTC and trusted-time behavior;
- greater-than-five-minute rollback transition to TIME_UNTRUSTED;
- ASSIGNED / RESERVED / RETAINED named-seat lifecycle;
- capacity locking and deterministic over-capacity retained-set remediation;
- canonical membership re-read for authority.

Checkpoint B requires zero open Critical/Major findings and no concurrency ambiguity.

## 3. Transaction and concurrency foundation

Batch B uses one explicit SQLAlchemy Session/transaction per mutation attempt through the commercial entitlement Unit of Work.

Commercial state mutation is serialized by the Organization+deployment commercial-state row lock. Initial-state creation uses the deterministic PostgreSQL transaction-scoped advisory-lock contract established by PATCH-059.

Seat capacity count and seat mutation execute under the same commercial-state locking boundary.

Qualification covered:

- deterministic advisory-lock behavior;
- Unit-of-Work commit/rollback behavior;
- concurrent entitlement activation;
- concurrent last-seat assignment.

No process-local mutex is treated as authoritative.

## 4. Entitlement activation and trusted time

Qualification covered:

- initial activation;
- higher-revision successor activation;
- equal-revision idempotent activation;
- lower-revision rollback rejection;
- conflicting equal-revision rejection;
- durable activation/rejection history;
- concurrent successor activation;
- trusted-time persistence;
- greater-than-five-minute backward-clock detection;
- durable and sticky TIME_UNTRUSTED behavior.

Ordinary successor activation does not clear TIME_UNTRUSTED.

No ordinary application recovery/reset path for TIME_UNTRUSTED or revision high-water is introduced by Batch B.

## 5. Seat lifecycle

The Batch B seat service implements the accepted three-state lifecycle:

- ASSIGNED;
- RESERVED;
- RETAINED.

Canonical UserOrganizationMembership remains authoritative and is re-read for seat mutation/evaluation.

Qualification demonstrated:

- concurrent final-seat assignment admits exactly one winner at capacity;
- disabled membership becomes reserved-effective and non-executable;
- re-enabling a stored RESERVED seat does not automatically restore commercial execution;
- explicit accepted seat reassignment/reactivation is required;
- releasing a commercial seat does not delete or alter canonical membership.

## 6. Capacity reduction and retained remediation

Qualification demonstrated the accepted over-capacity behavior:

- capacity reduction below consuming-seat count preserves existing seat records;
- immediately after reduction, ordinary ASSIGNED seats are non-executable;
- explicit retained selection determines the executable subset;
- retained selection is an exact replacement set rather than an additive set;
- replacing retained set `{A}` with `{B}` demotes A and retains B deterministically;
- selected retained users require enabled canonical membership;
- non-selected disabled membership is represented RESERVED;
- while consuming count exceeds capacity, non-RETAINED seats remain non-executable;
- releasing seats may resolve OVER_CAPACITY once consuming count is within capacity.

An exact empty retained set is accepted because the frozen contract permits retained-set size less than or equal to capacity. It selects no runtime winner, remains fail-closed, reports remediation unresolved, and leaves all consuming seats non-executable while over capacity.

## 7. Qualification environment

Database qualification used only the disposable PATCH-059 PostgreSQL instance:

`127.0.0.1:55432`

Database:

`satco_platform_patch02022_test`

The real PostgreSQL service on port 5432 was not used.

Final Batch B targeted qualification result:

`43 passed, 12 warnings`

Final exit results:

- targeted tests: `0`
- Python compile: `0`
- git diff check: `0`
- staged-content check: `0`

The warnings were existing/non-blocking deprecation warnings from FastAPI `on_event` and SQLAlchemy/Python `datetime.utcnow()` behavior. No test failure resulted from those warnings.

## 8. Deterministic vectors covered

Batch B qualification includes the relevant accepted DB/service vectors for this batch:

- first-activation/advisory-lock foundation;
- concurrent activation;
- revision rollback/conflict behavior;
- trusted-time persistence;
- concurrent last-seat assignment;
- disabled/reserved membership;
- explicit seat reactivation;
- capacity reduction;
- exact retained-set remediation;
- empty retained-set fail-closed behavior;
- release isolation from canonical membership.

API/security administration, step-up enforcement, CSRF, protected-not-found behavior, package seam integration and public safe-reason exposure remain Batch C scope.

Release-sequence and recovery-anchor completion remain later PATCH-059 batch scope.

## 9. Findings

Independent bounded Batch B checkpoint review:

- Critical: 0 open
- Major: 0 open
- Minor: 0 open blocking findings

Concurrency ambiguity identified by the accepted Batch B gate: none open after qualification.

Deprecation warnings observed during qualification are non-blocking maintenance items and do not alter Batch B authority or runtime security semantics.

## 10. Checkpoint disposition

Batch B machine qualification: PASS.

Batch B checkpoint review: PASS.

The Batch B implementation boundary is ready for its bounded checkpoint-evidence commit.

This checkpoint does not constitute PATCH-059 Human implementation acceptance, release approval, deployment approval or closure.

Human authority remains controlling. AI remains advisory and non-authoritative.
