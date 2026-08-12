# PATCH-032 — Batch 7 Authorized File Manifest

## Document Control

- **PATCH:** PATCH-032 — Technical Report
- **Batch:** Batch 7 — Regression and Final Evidence
- **Steps:** S18–S20
- **Preparation Authority:** GRANTED
- **Execution Authority:** NOT GRANTED
- **Delivery Authority:** NOT GRANTED
- **PATCH Closure Authority:** NOT GRANTED
- **Status:** PREPARATION COMPLETE — READY FOR SEPARATE HUMAN EXECUTION AUTHORITY
- **Governing Sources:** ADR-023, accepted EDS-032, accepted IDS-032,
  accepted Implementation-Plan-032, IRR-032, and Human-accepted Batches 1–6

## Exact S18–S20 Scope

### S18 — Adjacent Canonical Regressions

S18 executes, without modifying them, the existing adjacent regression suites
for Universal Capture, Evidence, Engineering Object, Engineering Relationship,
authentication and trusted Organization context, and Audit. It verifies that
PATCH-032 has not transferred canonical ownership, weakened protected
disclosure, changed trusted scope derivation, or altered Audit behavior.

S18 records exact commands, collected/passed/failed counts, and any warnings or
environment limitations in the Batch 7 validation-evidence artifact. Any
failure is a stop condition; Batch 7 may not remediate implementation under
this manifest.

### S19 — Full Backend, Static, and Exact-Scope Validation

S19 executes the complete backend regression suite once against the guarded
isolated PostgreSQL test database. It also performs:

- static compilation/import validation of PATCH-032 production and test files;
- Alembic single-head and current-head verification;
- final Technical Report migration, role, transaction, concurrency, rollback,
  authorization, plaintext-exclusion, and schema/model-parity validation;
- exact authorized-file and repository-diff inspection;
- prohibited-pattern and prohibited-route scans;
- `git diff --check`;
- final ADR/EDS/IDS/Implementation-Plan traceability and QG-M1 assessment.

S19 is validation only. It authorizes no source, test, migration,
configuration, infrastructure, or accepted-design change.

### S20 — Independent Review Evidence Package

S20 packages the immutable evidence required for a separate Independent Final
Implementation Review and later Human QG-11 decision. The package records:

- exact implementation and governance diff/file scope;
- Batch 1–6 Human acceptance and preserved historical review sequence;
- S18 and S19 commands and results;
- migration head, upgrade/downgrade, schema parity, role separation,
  transaction, concurrency, rollback, security, Audit, outbox, idempotency,
  and plaintext-exclusion evidence;
- prohibited capability/route/file evidence;
- QG-M1 final assessment;
- `B6-MIN-01` as `DEFERRED / NON-BLOCKING` performance debt;
- all remaining findings and environmental limitations, without suppressing or
  reclassifying them.

S20 may prepare the final-review record, but it may not mark the Independent
Final Review, Human QG-11, QG-12, delivery, push, deployment, or PATCH closure
as passed or authorized.

## Authorized File Boundary

No production, test, migration, configuration, infrastructure, ADR, EDS, IDS,
or Implementation Plan file may be created or modified in Batch 7.

| Action | Path | Authorized purpose |
|---|---|---|
| CREATE | `docs/reviews/PATCH-032-Batch-7-Validation-Evidence.md` | Record exact S18–S19 commands, results, scope checks, deferred debt, traceability, and stop-condition evidence. |
| CREATE | `docs/reviews/FR-032-Technical-Report.md` | Prepare the S20 independent-final-review evidence package with every decision gate explicitly pending. |
| MODIFY | `docs/patches/PATCH-032.md` | After successful S20 packaging only, record Batch 7 execution evidence as complete and Independent Final Review/Human QG-11/QG-12/delivery/closure as pending and unauthorized. No scope or architectural text may change. |

These three documentation files are the complete Batch 7 boundary. The
manifest itself records preparation authority and is not an execution output.

## Prerequisites and Dependencies

- ADR-023 is accepted and authoritative.
- EDS-032 and IDS-032 are accepted and complete.
- Implementation-Plan-032 is accepted and executable.
- IRR-032 is PASS / READY FOR IMPLEMENTATION.
- Batches 1–6 are Human accepted and complete.
- Batch 6 focused independent re-review is PASS, including B6-MAJ-03 and
  B6-MAJ-04 closure.
- S16 security/role evidence and S17 migration/transaction evidence are
  available for final validation.
- `B6-MIN-01` remains explicitly traceable as deferred, non-blocking bounded
  per-item detail-loading performance debt.

The prerequisites are **SATISFIED FOR PREPARATION**. Execution requires a
separate explicit Human Batch 7 authority grant.

## Preserved Evidence and Boundaries

- Every historical FAIL, remediation, re-review, and Human acceptance record
  remains unchanged and reachable.
- Batches 1–6 implementation and acceptance evidence remain unchanged.
- `B6-MIN-01` remains `DEFERRED / NON-BLOCKING`; Batch 7 may neither erase nor
  opportunistically remediate it.
- No production implementation, test rewrite, migration, configuration,
  credential, role, or infrastructure change is authorized.
- No delivery commit, push, migration execution outside isolated validation,
  deployment, QG-11, QG-12, or PATCH closure is authorized.

## Stop Conditions

Stop Batch 7 and report **BLOCKED** if:

- any S18 adjacent regression fails;
- the full backend suite, static/import check, migration/role/schema check,
  exact-scope check, prohibited-pattern scan, or `git diff --check` fails;
- repository state differs from the reviewed Batch 1–6 boundaries;
- a missing or stale acceptance artifact prevents evidence traceability;
- a required correction would modify any production, test, migration,
  configuration, infrastructure, ADR, EDS, IDS, or Implementation Plan file;
- any protected plaintext, authorization, canonical ownership, transaction,
  accepted-immutability, Human-authority, or advisory-AI guarantee regresses;
- a new Critical or Major finding remains open;
- completing S20 would require asserting an independent or Human decision that
  has not occurred;
- delivery, push, deployment, or closure would be required.

No stop condition may be waived or repaired within Batch 7. It returns to a
separately authorized focused remediation or governance gate.

## Readiness Decision

- **Manifest:** COMPLETE
- **S18–S20 Scope:** DEFINED
- **Prerequisites:** SATISFIED FOR PREPARATION
- **Batch 7 Execution Readiness:** READY FOR SEPARATE HUMAN AUTHORITY
- **Batch 7 Execution Authority:** NOT GRANTED
- **Delivery Authority:** NOT GRANTED
- **PATCH Closure Authority:** NOT GRANTED
- **Exact Next Action:** Human review of this manifest and an explicit bounded
  Batch 7 execution-authority decision.
