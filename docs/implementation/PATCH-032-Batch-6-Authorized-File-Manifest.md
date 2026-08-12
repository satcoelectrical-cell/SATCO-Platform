# PATCH-032 — Batch 6 Authorized File Manifest

## Document Control

- **PATCH:** PATCH-032 — Technical Report
- **Batch:** Batch 6 — Transport Integration
- **Steps:** S15–S17
- **Preparation Authority:** GRANTED
- **Implementation Authority:** NOT GRANTED
- **Batch 7 Authority:** NOT GRANTED
- **Status:** PREPARATION COMPLETE — READY FOR SEPARATE HUMAN IMPLEMENTATION AUTHORITY
- **Governing Sources:** ADR-023, accepted EDS-032, accepted IDS-032, accepted Implementation-Plan-032, IRR-032, and accepted Batches 1–5

## Authorized Boundary

Only the following fourteen production and test files may be created or modified during Batch 6 under the granted Human implementation authority.

| Action | Path | Authorized purpose |
|---|---|---|
| MODIFY | `backend/app/schemas/technical_report.py` | Complete only the strict transport request, filter, pagination, response, and stable outcome mappings required by IDS-032. |
| CREATE | `backend/app/api/v1/routers/technical_reports.py` | Implement the thin Technical Report transport boundary and request-scoped composition for approved endpoints only. |
| MODIFY | `backend/app/main.py` | Import and register only the Technical Report router. |
| MODIFY | `backend/app/services/technical_report_service.py` | Return lifecycle-specific authorized application read results after successful commands so transport can map a compliant response with one service invocation; no new business behavior. |
| MODIFY | `backend/app/ports/technical_report.py` | Extend `TechnicalReportReadCriteria` only with the accepted lifecycle and purpose filters. |
| MODIFY | `backend/app/repositories/technical_report_repository.py` | Apply accepted lifecycle/purpose filters before deterministic ordering, pagination, and authorized-total calculation. |
| MODIFY | `backend/app/models/technical_report_command.py` | Carry selected successor-copy references and expose the closed non-plaintext replay-result facts required for deterministic response reconstruction. |
| MODIFY | `backend/app/repositories/technical_report_unit_of_work.py` | Version and validate the persisted bounded non-plaintext safe replay result; no response plaintext. |
| MODIFY | `backend/tests/test_technical_report_service.py` | Prove successor-copy authorization and replay semantics after later Aggregate changes. |
| CREATE | `backend/tests/test_technical_report_api.py` | Prove approved routes, request/response mapping, authentication, protected outcomes, stable errors, pagination, and prohibited-route absence. |
| MODIFY | `backend/tests/test_technical_report_security.py` | Add only S16 transport-integrated denial, disclosure, plaintext-exclusion, Human-authority, and advisory-AI security evidence. |
| MODIFY | `backend/tests/test_technical_report_database_roles.py` | Add only S16 focused runtime-role, ownership, grant, trigger, and bypass-prevention validation evidence. |
| MODIFY | `backend/tests/test_technical_report_migration.py` | Add only S17 isolated upgrade, downgrade, clean-creation, single-head, schema/model parity, constraint, trigger, and drift evidence. |
| MODIFY | `backend/tests/test_technical_report_transaction.py` | Add only S17 concurrency, atomic transaction, failure rollback, Audit/outbox/idempotency, and accepted-immutability validation evidence. |

No other production, test, migration, configuration, infrastructure, or canonical-capability file is authorized.

## S15 — Schemas, Router, and Registration

S15 is limited to:

- completing transport-facing schemas without changing Domain or application contracts;
- creating a thin router that delegates all authorization, invariants, transaction ownership, idempotency, Audit, outbox, and AI authority decisions to the accepted inward boundaries;
- composing dependencies per request without introducing a separate dependency-injection module;
- registering only the Technical Report router in the application;
- adding API evidence for the accepted create draft, revise draft, accept exact draft, create successor, get, list, lineage, and advisory-AI operations;
- preserving protected-not-found, stable outcome mapping, bounded pagination, trusted server-derived Organization context, and explicit Human acceptance;
- proving that generic update, delete, publish, approve, Review, supersede, archive, and autonomous-AI routes do not exist.

S15 does not authorize persistence queries, ORM exposure, transaction control, duplicated authorization policy, Aggregate rules, provider-specific AI integration, or new endpoints in transport.

## S16 — Focused Security and Database-Role Validation

S16 is validation and test-evidence work only. It may extend the authorized security and database-role test files to prove:

- authentication and active trusted Organization context;
- operation-specific authorization before disclosure;
- owner and non-owner behavior, cross-scope denial, and protected-not-found equivalence;
- field, count, lineage, source, and AI-input disclosure boundaries;
- Human acceptance authority and advisory-only, attributable, disableable AI behavior;
- no protected plaintext in errors, logs, Audit, outbox, idempotency, or AI diagnostics;
- distinct schema-owner and restricted runtime PostgreSQL identities;
- runtime non-ownership, least privilege, enabled owner-controlled immutability triggers, and denial of bypass or privilege escalation.

S16 does not authorize changes to credentials, configuration, role provisioning, migrations, production authorization logic, or accepted persistence semantics. Any defect requiring such a change is a stop condition and requires manifest reconciliation.

## S17 — Migration, Concurrency, Transaction, Rollback, and Schema Validation

S17 is validation and test-evidence work only. It may extend the authorized migration and transaction test files to prove:

- isolated Alembic upgrade, downgrade, clean database creation, current single head, and restoration of disposable test state;
- exact migration/model/schema parity, constraints, indexes, foreign keys, grants, triggers, enum handling, and accepted-state immutability;
- stale Aggregate version, stale draft revision, simultaneous acceptance, duplicate acceptance, source-version race, authority/context race, idempotent replay, and fingerprint-conflict behavior;
- one-transaction success for report, provenance, Audit, outbox, and idempotency state;
- complete rollback after every staged failure and bounded post-rollback rejection Audit where required;
- repository no-commit and Unit of Work transaction ownership.

Batch 6 may execute accepted migration validation only against isolated disposable test databases. It does not authorize editing migration history, creating a migration, or executing a development, staging, deployment, or production migration.

## Prerequisites and Dependencies

- ADR-023 is accepted and authoritative.
- EDS-032 and IDS-032 are accepted and complete.
- Implementation-Plan-032 is accepted and executable.
- IRR-032 passed and established the bounded implementation sequence.
- Batches 1–4 are accepted and complete.
- Batch 5 is Human accepted and complete.
- S13 application-service behavior and S14 advisory AI boundary are therefore available to S15.
- S06 role separation, S07–S08 persistence/migration protections, and S09–S12 repository/UoW/Audit foundations are complete for S16–S17 validation.
- Current repository reality contains the Technical Report schemas and S16/S17 test surfaces; the Technical Report router and API test are not yet present.

The prerequisites are **SATISFIED** for preparation. Implementation remains subject to a separate Human Batch 6 implementation-authority grant.

## Preserved Boundaries

- Universal Human authority and exact-version acceptance remain unchanged.
- AI remains advisory, attributable, disableable, provider-neutral, and non-authoritative.
- The Aggregate owns lifecycle and invariant decisions.
- The application service owns orchestration; the router remains thin.
- Authorization occurs before disclosure.
- The repository never commits or authorizes.
- The Unit of Work remains the sole transaction boundary.
- Accepted content, acceptance facts, and governed provenance remain immutable.
- Batches 1–5 and their historical FAIL, remediation, re-review, and acceptance evidence remain unchanged.

## Prohibited Work

Batch 6 does not authorize:

- changes outside the exact eight-file boundary;
- changes to ADR-023, EDS-032, IDS-032, Implementation-Plan-032, or IRR-032;
- changes to Technical Report Domain, service, repository, Unit of Work, AI adapter, migration, database-role provisioning, configuration, or fixtures;
- new persistence, tables, migrations, lifecycle states, purposes, commands, services, workers, dispatch behavior, or provider integration;
- publication, enterprise Review, supersession workflow, Organizational Memory, Knowledge Graph, frontend/UI, or unrelated capability work;
- Batch 7 regression packaging or final-review evidence;
- commit, push, deployment, or non-test migration execution.

## Stop Conditions

Stop Batch 6 and report **BLOCKED** if:

- any required change falls outside the exact eight-file boundary;
- repository reality conflicts with accepted ADR-023, EDS-032, IDS-032, or Implementation-Plan-032;
- a transport requirement would duplicate application authorization, Domain policy, persistence access, or transaction ownership;
- request-scoped composition cannot use the accepted service, UoW factory, authorization, resolver, clock, and advisory-AI boundaries without changing them;
- a security or database-role failure requires production, migration, configuration, credential, role-provisioning, or fixture changes;
- migration validation would require rewriting history or using a non-disposable database;
- an accepted Batch 1–5 behavior regresses;
- protected data is disclosed through responses, errors, logs, counts, lineage, Audit, outbox, idempotency, or AI diagnostics;
- any unapproved route or later-Batch behavior is required;
- focused validation, static/import validation, exact-scope verification, prohibited-pattern checks, or `git diff --check` fails.

## Readiness Decision

- **Manifest:** COMPLETE
- **Repository Assumptions:** VERIFIED
- **Prerequisites:** SATISFIED
- **Batch 6 Implementation Readiness:** READY FOR SEPARATE HUMAN AUTHORITY
- **Batch 6 Implementation Authority:** NOT GRANTED
- **Batch 7 Authority:** NOT GRANTED
- **Required Next Action:** Human review of this manifest and an explicit bounded Batch 6 implementation-authority decision.

## Deferred Non-Blocking Debt

- **B6-MIN-01:** bounded per-item detail loading in list and lineage composition is deferred as non-blocking performance debt. Page size remains capped at 100. No authorization, correctness, persistence, or transaction rule is relaxed. Resolution requires a separately authorized performance-focused change.
