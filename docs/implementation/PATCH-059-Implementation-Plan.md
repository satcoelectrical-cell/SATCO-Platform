# PATCH-059 — Implementation Plan

**Date:** 2026-09-30
**Status:** HUMAN ACCEPTED
**Accepted design baseline:** Discovery-059, Architecture-059, EDS-059 and IDS-059 are Human accepted.
**Repository baseline at authoring:** origin/main = 3484fa91b199050dafe9536684e7bc4721ad848f

This plan authorizes nothing by itself. No migration, product-code edit, database mutation, deployment, release, PATCH-059 closure or PATCH-060 work may begin until this Implementation Plan is independently reviewed and explicitly Human accepted.

## 1. Execution principles

Implementation shall use a new isolated worktree/branch from freshly verified origin/main. The existing dirty SATCO worktree and historical PATCH-058 worktree are not implementation surfaces.

Suggested implementation worktree: /Users/mac/Projects/SATCO-Platform-p059-implementation
Suggested branch: patch-059-implementation

Before any edit:
- fetch and verify current origin/main;
- verify accepted PATCH-059 design artifacts exist at that baseline;
- verify git status clean in the new worktree;
- determine the sole Alembic head from Alembic/repository graph, not filename sorting;
- verify expected current head is e05800000001 or stop and reconcile;
- verify real production-like satco-postgres on port 5432 is not used;
- reserve disposable PostgreSQL at 127.0.0.1:55432 only after confirming it is disposable/free or an approved PATCH test instance.

No reset/clean/stash/destructive operation may touch unrelated work.

## 2. Batch gates

Execution is sequential:
A. persistence + canonical entitlement + cryptographic verification;
B. entitlement state/service + trusted time + seats;
C. existing package seam integration + API/security administration;
D. frontend administration/status;
E. release-sequence, recovery and operational readiness;
F. deterministic integrated qualification and independent final implementation review.

Each batch requires targeted tests, static checks and review before the next batch. Critical/Major findings stop progression.

No batch may broaden frozen PATCH-059 scope.

## 3. Batch A — persistence, canonicalization and crypto

Planned new files include commercial_entitlements canonical/crypto/state modules, commercial entitlement model/repository/UoW/schema, and migration e05900000001 only if preflight confirms e05800000001 remains sole parent.

Batch A deliverables:
- three bounded tables from IDS;
- constraints/FKs/indexes;
- strict closed envelope/payload schemas;
- duplicate-key rejection;
- RFC 8785 JCS implementation/dependency decision;
- Ed25519 verification only;
- trust-store parser/validator;
- digest and golden vectors;
- migration upgrade/downgrade qualification on disposable DB.

If no existing dependency provides proven RFC 8785 semantics, stop before adding a package, perform bounded dependency/security review, pin the selected dependency, and record rationale/evidence. json.dumps(sort_keys=True) is not an acceptable substitute.

Batch A tests cover valid golden signature, mutation, duplicate/unknown fields, invalid UTF-8/I-JSON, key lifecycle, DB constraints, migration from sole head and sole-head verification.

Checkpoint A requires zero open Critical/Major findings.
## 4. Batch B — entitlement state, anti-rollback, time and seats

Implement commercial_entitlement_service.py, commercial_seat_service.py and dependency wiring.

Implement validate preview plus activate repeat-validation; monotonic revision/high-water; equal-revision idempotency/conflict; current state and activation history; deterministic row/advisory locking; injectable server UTC; last_trusted_time bounded persistence; greater-than-5-minute rollback to TIME_UNTRUSTED; ASSIGNED/RESERVED/RETAINED seats; capacity locking and over-capacity retained-set remediation.

Membership remains canonical and is re-read for authority. No ordinary API clears TIME_UNTRUSTED or revision high-water.

Tests include concurrent last-seat assignment, concurrent activation, rollback/conflict, 5-minute clock boundary, disabled/re-enabled membership, capacity reduction and retained remediation.

Checkpoint B requires zero open Critical/Major findings and no concurrency ambiguity.

## 5. Batch C — package seam, API and security administration

Implement CommercialEntitlementAdapter against existing EntitlementDecisionPort. Do not change EntitlementRequest shape unless an accepted blocker proves impossible; any such blocker returns to Human design review.

Production commercial wiring prohibits NonCommercialEntitlementAdapter/NOT_REQUIRED.

Add bounded current-Organization entitlement status/validate/activate, seat list/assign/release/retain and update-eligibility routes.

Sensitive mutations require canonical admin authority and has_recent_step_up(auth.session, minutes=10). Fresh login alone is insufficient. Reuse PATCH-058 CSRF/browser-auth/security patterns.

Qualification covers tenant/role negatives, protected-not-found, step-up, CSRF, safe reason codes, no secret leakage, all E/I/C combinations, GRACE expansion denial and historical-read behavior.

Checkpoint C requires zero open Critical/Major security/tenant findings.

## 6. Batch D — frontend administration

Add CommercialEntitlementPanel and CommercialSeatsPanel under existing OrganizationAdminPage.

Implement server-derived status; safe binding/revision/digest/package/term/support/update display; upload -> validate preview -> explicit activation; existing step-up UX; seat capacity/states; assign/release; over-capacity retained selection; backend package denial/status.

Frontend must not verify signatures, calculate authoritative expiry, decide seat capacity or override backend denial.

Checkpoint D requires frontend suite PASS and no authority duplicated in browser.

## 7. Batch E — release sequence, recovery and readiness

Extend governed release metadata with immutable positive SATCO release sequence compatible with PATCH-058 evidence.

Enforce baseline_release_sequence <= installed/candidate sequence <= max_release_sequence from server-verified release evidence.

Implement production entitlement enable/trust-store settings, release sequence source, trusted-time checkpoint if needed, startup-fatal malformed static trust/deployment configuration, and bounded safe mode for invalid runtime entitlement.

Define and test restore reconciliation anchor/procedure before claiming anti-rollback recovery complete. Ordinary admin cannot clear it.

Update backup/recovery/operations evidence where PATCH-059 state becomes recovery-critical.

Checkpoint E requires deterministic recovery/update/readiness evidence and zero open Critical/Major findings.

## 8. Batch F — integrated qualification

Run backend full suite, frontend full suite, Alembic sole-head/current-head checks, fresh disposable DB upgrade, PATCH-059 deterministic vectors, canonical static checks, git diff --check, secret/redaction inspection, production negative configuration, tenant isolation, concurrency, recovery/clock/rollback and release-sequence vectors.

Real port 5432 database is prohibited.

Qualification record captures exact candidate SHA, commands/results, disposable DB identity/port, migration head, lock/dependency changes, findings and unresolved items.

Implementation is not DONE merely because tests pass. Independent implementation/security review and Human implementation acceptance remain required.
## 9. Commit strategy

Prefer bounded commits aligned with batches: persistence/canonical crypto; state/seats; package/API enforcement; admin UX; release/recovery/readiness; qualification/remediation.

Do not push a partially failing batch as a delivery candidate. No force push to main or immutable prior PATCH branches/tags.

Final candidate branch remains distinct from origin/main until Human-governed acceptance/merge sequence.

## 10. Expected file-change boundary

Backend scope is restricted to commercial entitlement modules, bounded package entitlement integration, configuration/readiness/release metadata, API registration and tests.

Frontend scope is restricted to Organization commercial administration/status and package denial/status presentation.

Operations/docs scope is restricted to entitlement trust configuration, recovery anchor, readiness/backup evidence and PATCH-059 qualification.

Unrelated refactors, package framework redesign, identity rewrite, billing, metering, SaaS, new disciplines and PATCH-060 certification are prohibited.

Any need outside this boundary is a STOP/REVIEW condition.

## 11. Security stop conditions

Stop and return to Human/design review if:
- Ed25519/JCS cannot be deterministic under accepted dependency policy;
- trusted deployment identity is unavailable at enforcement point;
- package seam requires authorization reordering/leakage;
- GRACE pre-valid_until configuration cannot be proven without material history redesign;
- durable anti-rollback cannot survive accepted recovery model;
- release sequence cannot bind to PATCH-058 evidence without changing release authority;
- migration graph is not single-head;
- production could reach NOT_REQUIRED;
- seat concurrency cannot serialize deterministically;
- any Critical/Major security or tenant-isolation finding remains.

Do not paper over a stop condition with fallback behavior.

## 12. Evidence artifacts

Create governed evidence for preflight/baseline, dependency review if applicable, migration qualification, Batch A-E checkpoints, deterministic qualification, security review, final implementation review and explicit Human acceptance when given.

Evidence must distinguish machine PASS from Human acceptance. No evidence may claim PATCH-059 closure before its separate closure gate.

## 13. Acceptance sequence after implementation

Future sequence:
Implementation Plan Human acceptance -> implementation batches/checkpoints -> integrated qualification -> independent implementation/security review -> Human implementation acceptance -> release/closure evidence required by roadmap -> explicit PATCH-059 closure.

PATCH-060 starts only after PATCH-059 is formally DONE/CLOSED and dependency gate is satisfied.

## 14. Governance disposition

Independent Implementation Plan Review completed with Critical 0 / Major 0 / Minor 0.

On 2026-09-30, the Human Authority explicitly accepted Implementation Plan-059. This acceptance authorizes bounded PATCH-059 implementation batches under the Plan checkpoints. It does not authorize deployment, release, PATCH-059 closure or PATCH-060.

Human authority remains controlling. AI remains advisory and non-authoritative.

**PATCH-059 IMPLEMENTATION PLAN: HUMAN ACCEPTED.**