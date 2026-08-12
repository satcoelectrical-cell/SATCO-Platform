# PATCH-032 — Batch 5 Authorized File Manifest

## 1. Document Control

| Field | Value |
|---|---|
| Document ID | PATCH-032-B5-MANIFEST |
| Related PATCH | PATCH-032 — Technical Report |
| Batch | Batch 5 — Application and AI Boundary |
| Implementation steps | S13–S14 only |
| Status | RECONCILED / FOCUSED REMEDIATION AUTHORIZED |
| Human preparation authority | GRANTED |
| Human implementation authority | GRANTED — BATCH 5 FOCUSED REMEDIATION ONLY |
| Governing ADR | ADR-023 — ACCEPTED / AUTHORITATIVE |
| Governing EDS | EDS-032 — ACCEPTED / COMPLETE |
| Governing IDS | IDS-032 — ACCEPTED / COMPLETE |
| Governing plan | Implementation-Plan-032 — ACCEPTED / COMPLETE |
| Governing readiness review | IRR-032 — PASS / READY FOR IMPLEMENTATION |
| Batches 1–4 | ACCEPTED / COMPLETE |
| PATCH-032 overall | IN PROGRESS |
| Migration authority | NOT GRANTED / NOT REQUIRED |
| Commit / push authority | NOT GRANTED |
| Later Batch authority | NOT GRANTED |
| Date | 2026-08-11 |

## 2. Bounded Scope

This manifest defines the exact prospective implementation boundary for
Implementation-Plan-032 steps S13 and S14. It does not grant implementation
authority.

- **S13 — Application service:** authorized orchestration for create draft,
  revise draft, authorized get and list, accept an exact draft, create a
  successor, retrieve lineage, and request an advisory AI proposal.
- **S14 — Advisory AI adapter:** a provider-neutral, advisory-only adapter that
  accepts bounded authorized input and returns an attributable proposal.

The application service must obtain trusted actor context, authorize before
disclosure, validate scope and references, invoke exactly one Aggregate command
per mutation, apply expected-version and idempotency contracts where required,
coordinate the accepted Technical Report Unit of Work, and return stable typed
outcomes. It must not duplicate Aggregate policy.

The AI adapter cannot construct a trusted actor, mutate or persist a Technical
Report, accept a report, change lifecycle, become provenance authority, or
exercise Human engineering judgment. Incorporation of an AI proposal requires
a later Human-directed Aggregate revision through the application service.

## 3. Repository Reality and Prerequisites

Repository inspection confirms that the four Batch 5 implementation files now
exist and that the accepted Batch 1–4 contracts, persistence, repository,
historical resolution, Unit of Work, Audit, outbox, idempotency, authorization,
reference, and Aggregate surfaces required by S13–S14 exist in the current
workspace.

Batch 5 depends on:

1. ADR-023, EDS-032, IDS-032, Implementation-Plan-032, and IRR-032;
2. Batch 1 typed commands, results, exceptions, Aggregate behavior, and inward
   ports;
3. Batch 2 restricted persistence, immutability, outbox, and idempotency
   structures;
4. Batch 3 no-commit repository and four-source historical resolution;
5. Batch 4 one-session Unit of Work, final recheck, successful Audit/outbox/
   idempotency atomicity, and bounded post-rollback rejection Audit; and
6. the accepted provider-neutral `TechnicalReportAIRequest`,
   `TechnicalReportAIProposal`, and AI port contracts.

These preparation prerequisites are satisfied. Their acceptance history and
all prior FAIL, remediation, re-review, and Human acceptance evidence remain
unchanged.

## 4. Exact Reconciled Production File Boundary

Exactly six production files are authorized for the focused remediation:

| Path | State | Step | Exact purpose |
|---|---|---|---|
| `backend/app/services/technical_report_service.py` | CREATE | S13 | Implement the authorized Technical Report application use cases, authorization-before-disclosure, reference validation, one-command mutation orchestration, expected-version and idempotency handling, accepted UoW coordination, protected outcomes, and typed result mapping. |
| `backend/app/ai/technical_report_assistant.py` | CREATE | S14 | Implement only the provider-neutral advisory adapter over the accepted AI port, with bounded authorized input, attributable output, non-authority enforcement, and no persistence or mutation capability. |
| `backend/app/ports/technical_report.py` | MODIFY | S13–S14 remediation | Add only the typed AI historical-authority, UoW rejection-Audit, and bounded scoped-lineage contracts required by B5-CRIT-01, B5-MAJ-01, and B5-MAJ-03. |
| `backend/app/exceptions/technical_report.py` | MODIFY | S14 remediation | Add only the stable assistant-unavailable application outcome required by B5-MAJ-02. |
| `backend/app/repositories/technical_report_unit_of_work.py` | MODIFY | S13 remediation | Enforce operation-specific authority and support current AI-source reauthorization through the existing same-Session collaborators. |
| `backend/app/repositories/technical_report_repository.py` | MODIFY | S13 remediation | Implement bounded deterministic successor queries within the already-authorized report scope so protected totals are correct. |

No other production file may be created or modified.

## 5. Exact Authorized Test File Boundary

Exactly two test files are authorized:

| Path | State | Step | Exact purpose |
|---|---|---|---|
| `backend/tests/test_technical_report_service.py` | CREATE | S13 and S14 | Prove every authorized application use case, typed orchestration, expected-version and idempotency behavior, history and lineage behavior, transaction/rollback integration, AI proposal orchestration, deterministic outcomes, and preservation of Aggregate ownership. |
| `backend/tests/test_technical_report_security.py` | CREATE | S13 and S14 | Prove authorization-before-disclosure, protected-not-found equivalence, cross-scope denial, acceptance authority, Human/AI authority separation, bounded AI input/output, attribution, plaintext exclusion, and negative governance cases. |

No other test file is authorized for modification. Test helpers must remain
local to these two files.

## 6. S13–S14 Traceability

| Step | Production surface | Test evidence | Checkpoint |
|---|---|---|---|
| S13 — Application service | `backend/app/services/technical_report_service.py` | `backend/tests/test_technical_report_service.py`; `backend/tests/test_technical_report_security.py` | All approved create, revise, read, list, exact-version acceptance, successor, lineage, and AI-request use cases pass with authorization, concurrency, idempotency, rollback, and protected-disclosure guarantees. |
| S14 — Advisory AI adapter | `backend/app/ai/technical_report_assistant.py` | `backend/tests/test_technical_report_service.py`; `backend/tests/test_technical_report_security.py` | Advisory proposal attribution and bounded input pass; AI mutation, acceptance, trusted-actor construction, provenance authority, and autonomous action are rejected. |

## 7. Explicitly Prohibited Work

Batch 5 does not authorize:

- any file outside the exact eight-file boundary;
- modification of commands, Aggregate, schemas, persistence models, migration,
  role, configuration, or prior Batch tests;
- API schemas, router, dependency injection, application registration, route
  exposure, or other Batch 6 behavior;
- migration execution or schema, trigger, grant, credential, or role changes;
- provider-specific SDK coupling, provider credentials, autonomous AI action,
  AI acceptance, or AI-authored trusted provenance;
- direct service or AI access to SQLAlchemy, ORM rows, repositories outside the
  accepted ports, transaction commit/rollback, Audit tables, outbox tables, or
  idempotency tables;
- outbox dispatch, workers, background processing, frontend work, generic
  update, physical delete, or unrelated refactoring;
- modification or erasure of Batch 1–4 governance and review history; or
- Batch 6, Batch 7, commit, push, deployment, or delivery authority.

## 8. Stop Conditions

Implementation must stop and report the exact conflict if:

- S13 or S14 remediation requires any file outside the eight-file boundary;
- an accepted inward port, command, result, exception, Aggregate, repository, or
  UoW contract is missing, contradictory, or requires semantic redesign;
- a provider-specific dependency, credential, configuration change, transport
  surface, route, migration, schema change, or canonical-capability change is
  required;
- authorization-before-disclosure, protected-not-found, exact-version
  acceptance, accepted immutability, one-command mutation, or historical
  resolvability cannot be preserved;
- the application service would need to duplicate Aggregate rules, directly
  access persistence, or own transaction internals;
- the AI adapter would receive unbounded or unauthorized context, disclose
  protected plaintext, mutate state, construct authority, or act without Human
  direction;
- focused tests expose an accepted design conflict rather than a bounded Batch
  5 implementation defect; or
- focused, prior-Batch, adjacent, full-regression, static, exact-scope,
  prohibited-pattern, or whitespace validation fails and cannot be corrected
  within this manifest.

## 9. Required Implementation Evidence

A separately authorized Batch 5 implementation must run and record:

1. the two focused Batch 5 test modules;
2. all Technical Report Batch 1–4 regressions;
3. relevant authentication, Organization, Workspace, Project, Evidence,
   EngineeringObject, EngineeringRelationship, Capture, and Audit regressions;
4. the complete backend regression suite;
5. static compilation and import validation;
6. scans proving no direct persistence, transaction ownership, provider
   authority, transport, migration, or later-Batch leakage;
7. exact eight-file scope verification; and
8. `git diff --check`.

No migration is required or authorized for Batch 5 validation.

## 10. Readiness and Authority Decision

The exact reconciled S13–S14 boundary is defined and its prerequisites are
satisfied. Human authority permits focused remediation of `B5-CRIT-01`,
`B5-MAJ-01` through `B5-MAJ-06`, and `B5-MIN-01` only.

- Batch 5 focused remediation authority: **GRANTED**.
- Later Batch authority: **NOT GRANTED**.
- Exact next action: complete the focused remediation within these eight files,
  run every required validation gate, and perform an independent Batch 5
  re-review.
