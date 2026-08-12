# PATCH-032 — Batch 4 Authorized File Manifest

## 1. Document Control

| Field | Value |
|---|---|
| Document ID | PATCH-032-B4-MANIFEST |
| Related PATCH | PATCH-032 — Technical Report |
| Batch | Batch 4 — Transaction and Audit |
| Status | RECONCILED / FOCUSED REMEDIATION AUTHORIZED |
| Human preparation authority | GRANTED |
| Human implementation authority | GRANTED |
| Governing ADR | ADR-023 — ACCEPTED / AUTHORITATIVE |
| Governing EDS | EDS-032 — ACCEPTED / COMPLETE |
| Governing IDS | IDS-032 — ACCEPTED / COMPLETE |
| Governing plan | Implementation-Plan-032 — ACCEPTED / COMPLETE |
| Governing readiness review | IRR-032 — PASS / READY FOR IMPLEMENTATION |
| Batch 1 | ACCEPTED / COMPLETE |
| Batch 2 | ACCEPTED / COMPLETE |
| Batch 3 | ACCEPTED / COMPLETE |
| PATCH-032 overall | IN PROGRESS |
| Migration authority | NOT GRANTED / NOT REQUIRED |
| Commit / push authority | NOT GRANTED |
| Later Batch authority | NOT GRANTED |
| Date | 2026-08-10 |

## 2. Authority and Scope

Human authority grants preparation and implementation of Batch 4 only. This
manifest is the exact file boundary for Implementation-Plan-032 steps S11 and
S12: Transaction and Audit.

Batch 4 shall complete the primary Technical Report Unit of Work in the
existing Batch 3 module, using one caller-owned SQLAlchemy Session and one
authoritative transaction for report/provenance persistence, successful Audit,
Domain Event outbox, and idempotency result. It shall also implement the
separate bounded post-rollback rejection-Audit adapter required by IDS-032.

Batch 4 does not authorize application services, AI behavior, API transport,
router registration, migration or configuration changes, canonical-capability
changes, frontend work, unrelated refactoring, or any later batch.

The initial Independent Batch 4 Review `FAIL` and findings `B4-CRIT-01` and
`B4-MAJ-01` through `B4-MAJ-05` remain preserved at
`docs/reviews/PATCH-032-Batch-4-Implementation-Review.md`. This reconciliation
authorizes only the minimum contract, Aggregate-event, UoW, exception, and test
surfaces required to remediate those six findings. It does not expand S11–S12.

## 3. Verified Repository Assumptions

Repository inspection confirms:

- accepted Batch 1 contracts define the Technical Report repository, Audit,
  rejection-Audit, Domain Event, idempotency, and Unit of Work ports;
- accepted Batch 2 persistence contains Technical Report root, provenance,
  persistence-only outbox and idempotency mappings, database constraints,
  immutability enforcement, and restricted runtime-role grants;
- accepted Batch 3 contains the no-commit Technical Report repository and the
  four session-bound historical resolvers in
  `backend/app/repositories/technical_report_unit_of_work.py`;
- the current Alembic graph has one head, `e03200000001`, and Batch 4 requires
  no schema change;
- the accepted plan assigns only S11 and S12 to Batch 4; and
- existing capability UoW patterns may be consulted for repository convention,
  but Technical Report authority, accepted immutability, rejection-Audit, and
  transaction semantics remain governed exclusively by IDS-032.

No repository mismatch blocks Batch 4 implementation within this manifest.

## 4. Dependencies

Batch 4 depends on:

1. ADR-023, EDS-032, IDS-032, Implementation-Plan-032, and IRR-032;
2. Batch 1 `ACCEPTED / COMPLETE` contracts and Aggregate behavior;
3. Batch 2 `ACCEPTED / COMPLETE` persistence, role separation, outbox and
   idempotency structures, triggers, grants, and database tests;
4. Batch 3 `ACCEPTED / COMPLETE` repository and historical resolvers;
5. the existing shared Audit persistence model without transferring Technical
   Report ownership to another capability; and
6. an isolated test database using the restricted runtime identity for runtime
   transaction evidence.

All entry dependencies are satisfied. B1-MIN-01 and B1-MIN-02 remain accepted,
deferred, non-blocking observations and are not opportunistically changed.

## 5. Exact Authorized Production File Boundary

Exactly five production files are authorized:

| Path | State | Exact authorized purpose |
|---|---|---|
| `backend/app/repositories/technical_report_unit_of_work.py` | EXISTING / MODIFY | Preserve the accepted Batch 3 historical resolvers and add the primary Technical Report UoW, repository composition, successful Audit recorder, Domain Event outbox recorder, idempotency store, one-session commit/rollback ownership, mutable-predicate lock/recheck support required by the UoW boundary, and the separate bounded post-rollback rejection-Audit adapter under S11–S12. |
| `backend/app/ports/technical_report.py` | EXISTING / MODIFY | Add only the typed same-Session final authority/reference recheck contract, closed rejection-Audit record with stable reason and optional safely-known target, fingerprint-aware idempotency lookup, and concrete UoW conformance surfaces required by `B4-CRIT-01`, `B4-MAJ-02`, `B4-MAJ-03`, and `B4-MAJ-05`. |
| `backend/app/exceptions/technical_report.py` | EXISTING / MODIFY | Add only the stable IDS-defined Technical Report idempotency-conflict outcome required by `B4-MAJ-03`. |
| `backend/app/models/technical_report_command.py` | EXISTING / MODIFY | Complete only the closed non-plaintext Domain Event contract with the IDS-required accountability fields for `B4-MAJ-04`; no command, persistence schema, or Batch 5 behavior may be added. |
| `backend/app/models/technical_report.py` | EXISTING / MODIFY | Construct the IDS-complete coherent Domain Events from Aggregate-owned state for `B4-MAJ-04`; preserve lifecycle, accepted immutability, command semantics, fields, and invariants. |

No other production file may be created or modified. The changes above are
finding-specific contract completion under already accepted IDS-032 semantics.
A need to alter any other file is a stop condition.

## 6. Exact Authorized Test File Boundary

Exactly two test files are authorized:

| Path | State | Exact authorized purpose |
|---|---|---|
| `backend/tests/test_technical_report_transaction.py` | EXISTING / MODIFY | Prove one-session atomic success; rollback of report/provenance/Audit/outbox/idempotency on every injected failure; repository no-commit preservation; fingerprint-aware exact replay/conflict; mutable-predicate lock/recheck and races; bounded durable rejection Audit after rollback; ordinary-failure exclusion; event/Audit/idempotency plaintext exclusion; concrete UoW conformance; and no Batch 5 behavior. |
| `backend/tests/test_technical_report_aggregate.py` | EXISTING / MODIFY | Prove each Aggregate command constructs the exact closed IDS-complete non-plaintext Domain Event shape and preserves event/Aggregate coherence, accepted immutability, and existing Batch 1 behavior for `B4-MAJ-04`. |

No existing test file may be modified. Local test helpers may exist only inside
this authorized test file.

## 7. Exact Seven-File Remediation Boundary

- `backend/app/repositories/technical_report_unit_of_work.py`
- `backend/tests/test_technical_report_transaction.py`
- `backend/app/ports/technical_report.py`
- `backend/app/exceptions/technical_report.py`
- `backend/app/models/technical_report_command.py`
- `backend/app/models/technical_report.py`
- `backend/tests/test_technical_report_aggregate.py`

All seven files exist in the current workspace. Focused remediation may modify
only these files; no additional implementation or test file may be created.
No migration, configuration, environment, infrastructure, service, AI, API,
router, dispatch, or additional implementation file is authorized.

## 9. Transaction and Successful Side-Record Boundary

The primary UoW shall:

- create one SQLAlchemy Session on entry and compose the accepted Technical
  Report repository and session-bound collaborators around that Session;
- keep canonical historical resolution, authorization/reference checks,
  Aggregate persistence, provenance finalization, successful Audit, Domain
  Event outbox, and idempotency persistence within the same transaction when
  invoked by a later authorized application service;
- commit exactly once only through the UoW and roll back the whole transaction
  on failure;
- preserve repository no-commit behavior;
- use the Batch 2 capability-owned outbox and idempotency mappings without
  dispatch, workers, transport, or background processing; and
- exclude report/source plaintext, historical representations, credentials,
  and sensitive provenance from Audit, outbox, idempotency, errors, and
  diagnostics.

Batch 4 provides transaction infrastructure only. It does not invoke Aggregate
commands or implement application use cases.

## 10. Durable Rejection-Audit Boundary

The rejection-Audit adapter is separate from the authoritative UoW. It may run
only after the authoritative UoW has rolled back and only for IDS-032 security
or authority rejection categories. It shall persist the bounded accountability
fields defined by IDS-032 in an isolated transaction and shall never receive a
repository, Aggregate, outbox recorder, idempotency store, historical basis,
or Technical Report mutation surface.

Ordinary syntax, reference, version, lifecycle, idempotency, and business-rule
failures do not create rejection Audit. Rejection-Audit failure preserves the
original rejection and cannot mutate Technical Report state or disclose
protected information.

## 11. Prohibited and Out-of-Scope Work

Batch 4 prohibits:

- application service or command-use-case orchestration;
- AI adapter or provider behavior;
- API schemas, routers, dependency injection, route registration, or frontend;
- migration, schema, trigger, grant, role, configuration, environment, or
  infrastructure changes;
- changes to Batch 1 Aggregate/command/port contracts except the exact typed
  completion authorized for `B4-CRIT-01`, `B4-MAJ-02` through `B4-MAJ-05`;
- changes to the Batch 3 repository or historical-request contracts;
- changes to Universal Capture, Evidence, EngineeringObject, Engineering
  Relationship, Workspace, Project, Organization, authentication, or shared
  Audit models;
- outbox dispatch, event workers, background processing, or external publish;
- generic update, physical delete, direct repository commit, or ORM exposure;
- Audit of protected plaintext or acceptance-defining content;
- using rejection Audit as part of the successful mutation transaction;
- resolving B1-MIN-01 or B1-MIN-02 outside a separately authorized surface;
- Batch 5 application/AI work or any later-batch behavior; and
- commit, push, deployment, or migration execution.

## 12. Stop Conditions

Implementation shall stop and report the exact conflict if:

- S11 or S12 remediation requires any file outside the seven-file boundary;
- an accepted port or Batch 2 mapping is insufficient or contradictory;
- one-session atomicity cannot include report/provenance, successful Audit,
  outbox, and idempotency persistence;
- a repository commit or a second success-path transaction is required;
- durable rejection Audit cannot be isolated until after authoritative
  rollback or would mask the original rejection;
- runtime-role grants cannot exercise the accepted transaction safely;
- any migration, schema, configuration, canonical-capability, service, API, AI,
  or later-batch change appears necessary;
- focused tests expose an accepted architecture conflict rather than a bounded
  Batch 4 defect; or
- any focused, Batch 1–3, adjacent, static, exact-scope, or whitespace gate
  fails and cannot be corrected inside this manifest.

## 13. Required Batch 4 Validation

Batch 4 implementation evidence shall include:

1. `backend/tests/test_technical_report_transaction.py`;
2. Batch 3 repository/historical-resolution regression;
3. Batch 2 migration and database-role regression;
4. Batch 1 Aggregate and schema regression;
5. atomic-success and injected-failure rollback evidence;
6. durable rejection-Audit, plaintext-exclusion, and failure-isolation evidence;
7. repository no-commit and single-UoW transaction-boundary scans;
8. exact seven-file Batch 4 remediation-scope verification;
9. static compilation and `git diff --check`; and
10. an Independent PATCH-032 Batch 4 Review before Human Batch 4 Acceptance.

## 14. Later Batch Authority Boundary

Batch 5 and every later batch remain `NOT GRANTED`. A successful Batch 4
implementation does not authorize application services, AI, transport,
regression packaging, commit, or push. Work must stop after focused validation
for an Independent PATCH-032 Batch 4 Review and Human Batch 4 Acceptance.

## 15. Revision History

| Version | Date | Description |
|---|---|---|
| 1.1 | 2026-08-10 | Reconciled the initial Independent Batch 4 Review findings and authorized focused remediation of B4-CRIT-01 and B4-MAJ-01 through B4-MAJ-05 within the exact seven-file boundary; preserved S11–S12 and withheld Batch 5 and later authority. |
| 1.0 | 2026-08-10 | Published the exact Batch 4 Transaction and Audit two-file implementation boundary and recorded bounded Human preparation/implementation authority; later batches remain not granted. |
