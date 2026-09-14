# Implementation Plan-054 — Rights-Aware Standards Registry and Standards-Aware Technical Report Intelligence

## 1. Status and authority

| Field | Value |
|---|---|
| Date | 2026-09-12 |
| PATCH | PATCH-054 — Rights-Aware Standards Registry and Standards-Aware Technical Report Intelligence |
| Plan state | DRAFT / COMPLETE / AWAITING HUMAN ACCEPTANCE |
| Discovery | HUMAN ACCEPTED |
| ADR-027 | HUMAN ACCEPTED / AUTHORITATIVE |
| EDS-054 | HUMAN ACCEPTED / AUTHORITATIVE |
| IDS-054 | HUMAN ACCEPTED / AUTHORITATIVE |
| IDS review | PASS; Critical/Major/Minor/Observation = 0/0/0/2; observations nonblocking |
| Implementation | NOT STARTED / NOT AUTHORIZED |
| PATCH-055+ | NOT STARTED / NOT AUTHORIZED |

This Plan is executable sequencing only. It does not redesign accepted authority, implement code, create or execute migrations, modify tests or frontend, stage, commit, push, or authorize a future batch. Every prospective implementation change requires separate Human implementation authority and its exact authorized manifest.

## 2. Verified baseline and preservation control

Verified HEAD: c3dc7bf9a32e43c1edfbc51ca4d49ad146b64c60 — PATCH-053: close assessment orchestration remediation, dated 2026-09-12T05:13:28+03:30.

Verified sole Alembic head: e05300000002. The current repository contains the accepted PATCH-054 Discovery/ADR/EDS/IDS documentation and no prospective PATCH-054 implementation paths listed in section 3. The worktree contains unrelated modified and untracked work, including dirty backend, frontend, and governance paths. It is not part of PATCH-054 and must remain untouched. This Plan adds only itself.

All later batch work must start by recording the then-current HEAD, checking the sole Alembic head, comparing the authorized manifest to section 3, and integrating only authorized hunks in any unrelated dirty shared path. A changed head or multiple Alembic heads is a stop condition for that batch until Human direction or an authorized reconciliation.

## 3. Authoritative 71-path future manifest

The IDS identified 71 unique future implementation paths. This Plan reconciles each against the current repository, assigns exactly one primary batch owner, and records unavoidable shared-batch touchpoints. Classifications are prospective: no listed implementation path is created or modified by this Plan.

| # | Class | Primary | Shared batches | Exact path |
|---:|---|---|---|---|
| 1 | NEW | B1 | — | backend/app/enums/standards.py |
| 2 | NEW | B1 | B2, B3 | backend/app/schemas/standards.py |
| 3 | NEW | B1 | B2, B3, B5 | backend/app/models/standards.py |
| 4 | NEW | B1 | B2, B3, B5 | backend/app/models/standards_command.py |
| 5 | NEW | B1 | B2, B3, B5 | backend/app/ports/standards.py |
| 6 | NEW | B1 | B2, B3, B5 | backend/app/repositories/standards_repository.py |
| 7 | NEW | B1 | B2, B3, B5 | backend/app/repositories/standards_unit_of_work.py |
| 8 | NEW | B1 | B2, B3, B5 | backend/app/services/standards_service.py |
| 9 | NEW | B1 | B2, B3, B5 | backend/app/dependencies/standards.py |
| 10 | NEW | B1 | B2, B3, B5 | backend/app/api/v1/routers/standards.py |
| 11 | NEW | B1 | — | backend/app/standards/__init__.py |
| 12 | NEW | B1 | — | backend/app/standards/canonical.py |
| 13 | NEW | B1 | B4, B5 | backend/app/standards/handles.py |
| 14 | NEW | B1 | B2, B5 | backend/app/standards/providers.py |
| 15 | NEW | B2 | — | backend/app/adapters/standard_source_object_store.py |
| 16 | NEW | B2 | — | backend/app/adapters/standard_source_providers.py |
| 17 | NEW | B3 | — | backend/app/adapters/standards_package_candidates.py |
| 18 | NEW | B5 | — | backend/app/adapters/standards_cross_discipline.py |
| 19 | NEW | B5 | — | backend/app/ai/standards_intelligence.py |
| 20 | MODIFY | B1 | B2, B5 | backend/app/core/config.py |
| 21 | MODIFY | B1 | — | backend/app/main.py |
| 22 | MODIFY | B4 | B5 | backend/app/ai/technical_report_assistant.py |
| 23 | MODIFY | B4 | — | backend/app/models/technical_report_command.py |
| 24 | MODIFY | B4 | — | backend/app/models/technical_report.py |
| 25 | MODIFY | B4 | — | backend/app/ports/technical_report.py |
| 26 | MODIFY | B4 | — | backend/app/repositories/technical_report_repository.py |
| 27 | MODIFY | B4 | — | backend/app/repositories/technical_report_unit_of_work.py |
| 28 | MODIFY | B4 | — | backend/app/services/technical_report_service.py |
| 29 | MODIFY | B4 | — | backend/app/schemas/technical_report.py |
| 30 | MODIFY | B4 | — | backend/app/api/v1/routers/technical_reports.py |
| 31 | MODIFY | B3 | — | backend/app/discipline_packages/contributions.py |
| 32 | MODIFY | B3 | — | backend/app/discipline_packages/descriptors/eic_v1.py |
| 33 | MIGRATION | B1 | — | backend/migrations/versions/<UNASSIGNED_M1>_patch_054_standards_foundation.py |
| 34 | MIGRATION | B4 | — | backend/migrations/versions/<UNASSIGNED_M2>_patch_054_technical_report_standards.py |
| 35 | TEST | B1 | — | backend/tests/test_standards_contracts.py |
| 36 | TEST | B1 | B2, B3 | backend/tests/test_standards_service.py |
| 37 | TEST | B1 | B2, B3 | backend/tests/test_standards_repository.py |
| 38 | TEST | B1 | B2, B4, B5 | backend/tests/test_standards_security.py |
| 39 | TEST | B1 | B2, B3, B5 | backend/tests/test_standards_api.py |
| 40 | TEST | B2 | — | backend/tests/test_standards_retrieval.py |
| 41 | TEST | B2 | — | backend/tests/test_standards_assertions.py |
| 42 | TEST | B5 | — | backend/tests/test_standards_ai.py |
| 43 | TEST | B5 | — | backend/tests/test_standards_conformance.py |
| 44 | TEST | B1 | B4 | backend/tests/test_standards_migrations.py |
| 45 | TEST | B4 | — | backend/tests/test_technical_report_standards.py |
| 46 | TEST | B3 | — | backend/tests/test_standards_package_integration.py |
| 47 | TEST | B5 | — | backend/tests/test_standards_performance.py |
| 48 | FRONTEND | B5 | — | frontend/src/api/types.ts |
| 49 | FRONTEND | B5 | — | frontend/src/api/client.ts |
| 50 | FRONTEND | B5 | — | frontend/src/App.tsx |
| 51 | FRONTEND | B5 | — | frontend/src/components/AppShell.tsx |
| 52 | FRONTEND | B5 | — | frontend/src/pages/StandardsPages.tsx |
| 53 | FRONTEND | B5 | — | frontend/src/pages/OrganizationAdminPage.tsx |
| 54 | FRONTEND | B5 | — | frontend/src/pages/ProjectsPage.tsx |
| 55 | FRONTEND | B5 | — | frontend/src/pages/ReportPages.tsx |
| 56 | FRONTEND | B5 | — | frontend/src/components/StandardsRegistryPanel.tsx |
| 57 | FRONTEND | B5 | — | frontend/src/components/OrganizationStandardsRightsPanel.tsx |
| 58 | FRONTEND | B5 | — | frontend/src/components/ProjectStandardsPanel.tsx |
| 59 | FRONTEND | B5 | — | frontend/src/components/TechnicalReportStandardsBasisPanel.tsx |
| 60 | FRONTEND | B5 | — | frontend/src/components/StandardsIntelligencePanel.tsx |
| 61 | FRONTEND | B5 | — | frontend/src/components/StandardsStatePresentation.tsx |
| 62 | FRONTEND | B5 | — | frontend/src/styles.css |
| 63 | TEST | B5 | — | frontend/src/test/standards-registry.test.tsx |
| 64 | TEST | B5 | — | frontend/src/test/standards-rights.test.tsx |
| 65 | TEST | B5 | — | frontend/src/test/project-standards.test.tsx |
| 66 | TEST | B5 | — | frontend/src/test/report-standards.test.tsx |
| 67 | TEST | B5 | — | frontend/src/test/standards-intelligence.test.tsx |
| 68 | TEST | B5 | — | frontend/src/test/standards-accessibility-rtl.test.tsx |
| 69 | TEST | B5 | — | frontend/src/test/api-client-standards-states.test.ts |
| 70 | GOVERNANCE | B1 | B5 | docs/patches/PATCH-054.md |
| 71 | GOVERNANCE | B5 | — | docs/19_Governance_Model.md |

Primary ownership count: B1=24, B2=4, B3=4, B4=11, B5=28; total=71. Shared files may receive only the owner-specific additions described below. They never authorize opportunistic refactoring or another batch’s behavior.

## 4. Revision-ID disposition

No revision identifier is assigned by this Plan. Repository precedent keeps an IDS/Plan migration path UNASSIGNED until separately Human-authorized implementation, when the actual sole head is checked again. Batch 1 will allocate one new revision whose down_revision is then-current sole head; on this verified baseline it would descend from e05300000002. Batch 4 will allocate its own revision only as the linear successor of the actual Batch-1 revision. Neither revision is created, reserved, or executed by this Plan.

## 5. Shared execution and evidence rules

Future implementation follows this immutable sequence for each batch:

1. Reconfirm authority, HEAD, sole Alembic head, manifest, and unrelated worktree baseline.
2. Implement only the accepted batch and its authorized shared-file hunks.
3. Run the required focused evidence levels; record commands/results without fabricating PASS.
4. Execute the batch’s owned conformance vectors and applicable earlier regression.
5. Obtain an independent implementation review.
6. Obtain Human acceptance before the next batch.

Test levels are: Level A focused unit/schema/service tests; Level B API/UoW integration; Level C real PostgreSQL, migration, role, trigger, lock, and concurrency evidence; Level D cumulative backend/frontend regression and qualification. No test is run during Plan preparation.

Each future implementation batch must receive one separately Human-authorized bounded manifest at docs/implementation/PATCH-054-Batch-<1..5>-Authorized-File-Manifest.md and retain evidence under the matching PATCH-054 Batch implementation/review workflow. Those future governance records are implementation-control artifacts, not prospective code paths in the IDS 71-path count; they do not expand the 71-path implementation manifest.

## 6. Batch 1 — Canonical Standards Registry, Editions and Rights Foundation

Primary paths (24): 1–14, 20–21, 33, 35–39, 44, and 70. Shared future additions in paths 2–10, 13–14, 20, and 36–39 remain owned by their later batches.

Entry criteria: Human implementation authorization with a Batch-1 exact manifest; unchanged accepted governance; one Alembic head; clean/stated index; a recorded unrelated-work baseline; no PATCH-054 production implementation; chosen current migration parent.

Implementation sequence:

1. Add the closed standards vocabularies, canonical JSON/digests, Unicode identity normalization, exact value objects, and catalog/routing DTOs.
2. Create StandardIdentity, immutable StandardEdition, append-only standing observations, OrganizationRightsBinding, standards idempotency/outbox models, scoped ports/repository/UoW/service/dependencies/router, and static platform-admin/provider policy seams.
3. Implement global_trusted versus organization_private catalog scope; identity/edition duplicate domains; 64-edition bound; append-only standing; Organization/edition/provider rights tuple; independent capability booleans; AI processing permission; time expiry/revocation; authorization-before-protected lookup.
4. Implement CAT-01..05 and RGT-01..03 only, shared AuditLog staging, standards outbox, and standards idempotency for these mutations.
5. Create only the authorized Batch-1 migration after allocating its then-correct successor revision. It creates the 11-table foundation portions owned by Batch 1, indexes, checks, history/single-head triggers, role grants/revocations, and no seed data.

Primary vectors (33): P054-ID-01, P054-ID-02, P054-ID-03, P054-ID-04, P054-ID-05, P054-ID-06, P054-ID-07, P054-ID-08; P054-RGT-01, P054-RGT-02, P054-RGT-03, P054-RGT-04, P054-RGT-05, P054-RGT-06, P054-RGT-07, P054-RGT-08, P054-RGT-09, P054-RGT-10, P054-RGT-11, P054-RGT-12; P054-AUTH-01, P054-AUTH-02, P054-AUTH-03, P054-AUTH-04, P054-AUTH-05, P054-AUTH-06, P054-AUTH-07, P054-AUTH-08, P054-AUTH-09, P054-AUTH-10; P054-AUD-01, P054-AUD-02; P054-DB-01.

Required evidence: Levels A, B, and C. Level C uses real PostgreSQL for clean install/upgrade from e05300000002, sole-head check, runtime role grants, installer denial, immutable edition/standing/right rows, no prohibited DELETE, partial unique heads, rights tuple isolation, and identical absent/forbidden protected responses.

Completion criteria: all 33 owned vectors pass; CAT/RGT contract tests pass; rights matrix and duplicate normalization evidence pass; M1 clean/upgrade and grants/trigger evidence pass; Audit/outbox/idempotency atomicity passes; no tenant/count disclosure exists; independent Batch-1 review has no Critical or genuine Major blocker.

Batch-1 gate: Human acceptance of the evidence and review is required before Batch 2. Compilation alone, migration creation alone, or partial vector success does not open Batch 2.

## 7. Batch 2 — Authorized Retrieval, Source Snapshots and Standard Knowledge Assertions

Primary paths (4): 15–16, 40–41. Authorized shared hunks: paths 2–10, 14, 20, and 36–39.

Entry criteria: accepted Batch 1, active M1 foundation, passing B1 regression, unchanged sole head, and a separate Batch-2 manifest.

Implementation sequence:

1. Add the AuthorizedStandardSourceProvider contract implementation, static provider registry bindings, and narrow StandardSourceObjectStore adapter over existing exact-key private object storage.
2. Implement SRC-01 as an all-or-nothing 1..8 fragment request with 8-KiB item and 32-KiB aggregate checks, no arbitrary URL/browser/scraper behavior, private retention only when authorized, and qualifying immutable provider-handle attestation otherwise.
3. Implement signed opaque handles, provider/source integrity checks, compensation, fresh display authorization, and source snapshot receipts without public URLs, object keys, or raw generic file access.
4. Add the four assertion kinds, closed canonical representation, unverified creation, Human verification/rejection, eligibility/stale history, retention/current-use split, and rights/expiry/integrity propagation.
5. Implement SRC-01..02 and AST-01..03 only. Treat source text as untrusted bounded data; establish the prompt-injection-safe representation boundary but do not call AI.

Primary vectors (19): P054-RET-01, P054-RET-02, P054-RET-03, P054-RET-04, P054-RET-05, P054-RET-06, P054-RET-07, P054-RET-08, P054-RET-09, P054-RET-10; P054-AST-01, P054-AST-02, P054-AST-03, P054-AST-04, P054-AST-05, P054-AST-06, P054-AST-07, P054-AST-08; P054-AUD-03.

Required evidence: Levels A, B, and C. Level C requires real PostgreSQL and object-store test double evidence for atomic snapshot/rights transition, revocation race, immutable receipts/events, direct privilege denial, and cross-Organization object/snapshot isolation.

Security matrix: forged/expired handles; wrong actor/Organization/Project/operation; rights version mismatch; post-issuance revocation; provider mismatch; integrity mismatch; cross-Organization object reuse; malicious source instructions; unauthorized display/retrieval; and derived-use revocation all fail closed without unsafe content or hints.

Completion criteria: all 19 owned vectors pass; exact 8/8192/32768 bounds pass; provider handle/snapshot immutability is proven; no arbitrary network request occurs; assertions cannot self-verify; no protected source text enters logs/Audit/outbox; independent Batch-2 review has no Critical or genuine Major blocker.

Batch-2 gate: Human acceptance of focused A/B/C evidence and independent review is required before Batch 3.

## 8. Batch 3 — Project Applicability and Discipline-Package Standards Candidates

Primary paths (4): 17, 31–32, and 46. Authorized shared hunks: paths 2–10 and 36–39.

Entry criteria: accepted Batches 1–2, protected source/assertion behavior stable, and a separate Batch-3 manifest.

Implementation sequence:

1. Add ProjectStandardApplicability records with exact edition pinning, advisory candidate state, Human declaration, informative/design_basis/mandatory role, mandatory provenance, expected revision, retirement/successor linkage, and 64-head enforcement.
2. Implement the PATCH-052 StandardsApplicabilityHookV1 adapter and EIC v1 descriptor contribution. It emits exact package/configuration provenance, deterministic bounded candidates, and no protected text, rights, AI, or authority.
3. Implement APP-01..04. APP-02 remains a deterministic read. A referenced previously-unrecorded package candidate is persisted atomically with the Human APP-03 declaration and its candidate-recorded/declared events; package output alone never mutates Project state.
4. Defer all final frontend delivery to B5. B3 exposes stable API DTOs only; it does not introduce partial UI behavior.

Primary vectors (9): P054-APP-01, P054-APP-02, P054-APP-03, P054-APP-04, P054-APP-05, P054-APP-06, P054-APP-07, P054-APP-08; P054-AUD-04.

Required evidence: Levels A, B, and C. Level C verifies Project/Organization constraints, current-head/expected-revision races, candidate/event atomicity, and package descriptor provenance against real PostgreSQL.

Completion criteria: all nine owned vectors pass; mandatory requires allowed Human provenance; candidate cannot grant access or mandatory authority; exact package/version/configuration provenance is retained; stale configuration is safe; concurrent declarations yield one winner; independent Batch-3 review has no Critical or genuine Major blocker.

Batch-3 gate: Human acceptance and independent review are required before Batch 4.

## 9. Batch 4 — Technical Report Standards Provenance and Historical Compatibility

Primary paths (11): 22–30, 34, and 45. Authorized shared hunks: paths 13, 38, and 44.

Entry criteria: accepted Batches 1–3, all prior regression green, current Technical Report authority re-inspected against its exact delivered state, and a separate Batch-4 manifest.

Implementation sequence:

1. Add StandardHistoricalBasisV1 to existing Technical Report command/schema/model/repository/service layers. Basis construction is server-side from opaque selections and includes frozen identity, edition, standing, rights, applicability, source/handle, assertion, AI, Human, Report, and digest provenance.
2. Extend existing Report revision UoW for RPT-01 candidate formation and RPT-02 new revision creation; preserve existing Report ownership, idempotency, locks, audit/outbox, and optimistic version behavior.
3. Extend RPT-03 acceptance with all 13 accepted final rechecks. No client handle or raw provenance becomes proof; acceptance is all-or-nothing.
4. Apply the strict StandardLocator cutover: accepted snapshots remain byte-identical and render legacy_unattested_reference; a legacy-bearing draft requires conversion; no post-cutover revision or acceptance may retain it; successors must select canonical basis.
5. Allocate and create M2 only under implementation authority, as M1’s linear successor. It adds the accepted nullable provenance columns/FKs, basis validators, cutover guards, Report-count guards, accepted-snapshot validation, and immutability protections without rewriting history.
6. Update the existing Technical Report assistant only to replace raw legacy standards context with authorized safe handles/representations; no standards AI provider is introduced until B5.

Primary vectors (15): P054-RPT-01, P054-RPT-02, P054-RPT-03, P054-RPT-04, P054-RPT-05, P054-RPT-06, P054-RPT-07, P054-RPT-08, P054-RPT-09, P054-RPT-10, P054-RPT-11, P054-RPT-12; P054-AUD-06; P054-DB-02, P054-DB-03.

Required evidence: Levels A, B, and C. Real PostgreSQL is mandatory for M2 clean/upgrade behavior, legacy accepted-byte preservation, draft conversion guard, accepted immutability, Report revision/acceptance races, and final rights/applicability/source/assertion rechecks.

High-risk evidence: accepted legacy bytes unchanged; new legacy locator rejected; existing draft conversion required; successor canonical selection; revoke before revision/acceptance; applicability/source/assertion change before acceptance; revision/acceptance race; superseded/withdrawn acknowledgement; and current denied rights masking protected historical content while preserving meaning.

Completion criteria: all 15 owned vectors pass; M2 succeeds from M1 and preserves legacy accepted fixtures; the 13 rechecks execute in the Report UoW; no historical rewrite occurs; independent Batch-4 review is PASS with no Critical/Major blocker.

Batch-4 gate: Batch 5 is prohibited until Human accepts the historical compatibility evidence and independent review.

## 10. Batch 5 — Standards-Aware AI, Frontend Completion and Cumulative Qualification

Primary paths (28): 18–19, 42–43, 47–69, and 71. Authorized shared hunks: paths 3–10, 13–14, 20, 22, 38–39, and 70.

Entry criteria: accepted Batches 1–4, stable Report historical behavior, accepted batch manifests/evidence, and separate Batch-5 implementation authority.

Implementation sequence:

1. Complete deterministic standards intelligence and its safe PATCH-053 projection; PATCH-053 remains read-only and never retrieves protected standards content inside its deterministic transaction.
2. Implement Human-requested standards AI: rights/processor authorization, safe context composition, three phase transaction, one provider call, 30-second deadline, zero automatic retries, no tools/autonomous retrieval, closed output validation, safe persisted advisory result, and terminal interaction provenance.
3. Implement INT-01..02 and the remaining cumulative API/client DTO behavior.
4. Deliver exactly six frontend surfaces: registry metadata search/detail; organization rights administration; Project applicability/source/assertion presentation; Report standards-basis selector/history; advisory intelligence; protected/unavailable/superseded state presentation. Use accessible keyboard/focus/live-status semantics, logical CSS/RTL, LTR identifier isolation, non-color states, and explicit Human-authority/reference-only/material-support messages.
5. Run the cumulative 96-vector qualification, full security/role/concurrency/resource evidence, frontend suites/build/type/static checks, full backend regression, migration/head reconciliation, and whole-PATCH review preparation.

Primary vectors (20): P054-AI-01, P054-AI-02, P054-AI-03, P054-AI-04, P054-AI-05, P054-AI-06, P054-AI-07, P054-AI-08; P054-UX-01, P054-UX-02, P054-UX-03, P054-UX-04, P054-UX-05, P054-UX-06; P054-LIM-01, P054-LIM-02, P054-LIM-03, P054-LIM-04; P054-AUD-05; P054-DB-04.

Required evidence: Levels A, B, C, and D. Level C covers provider/rights/revocation/idempotency races, migration-role security, and resource boundaries. Level D covers all six UI surfaces, keyboard/screen reader/RTL/responsive evidence, full backend/frontend regression, and 96/96 conformance.

AI failure/race evidence: prohibited/local-only/approved processor; wrong provider; unavailable/timeout; invented handle/clause; authority claim; rights revoked before dispatch/during call/before persistence; duplicate request/replay; no duplicate dispatch; deterministic result survives failure.

Completion criteria: all 20 primary vectors and cumulative 96/96 pass; all six frontend surfaces qualify; no AI egress without exact permission; one-call/no-retry proof holds; full resource limits hold; QG-11/QG-12 and Whole-PATCH independent review are ready for Human assessment.

Batch-5 gate: completion may be recommended for Whole-PATCH qualification only after Human accepts Batch 5. It does not itself close PATCH-054.

### 10.1 Exact six frontend-surface mapping

| Surface | B5 paths | Qualification evidence |
|---|---|---|
| 1. Registry metadata search/detail | 52, 56, 48–49, 63 | visible global_trusted/organization_private metadata; keyboard search/detail; no rights posture leakage |
| 2. Organization rights administration | 53, 57, 48–49, 64 | admin capability matrix, replace/revoke, expired/revoked states, focus and labels |
| 3. Project applicability | 54, 58, 48–49, 65 | package advisory versus Human declaration, mandatory provenance, exact edition, 64-head state |
| 4. Report standards-basis selector | 55, 59, 48–49, 66 | reference_only/material_support, standing acknowledgement, legacy conversion, historical masking |
| 5. Advisory standards intelligence | 55, 60, 48–49, 67 | Human-requested/non-authoritative output, terminal state, no automatic action |
| 6. Protected/unavailable/superseded presentation | 61–62, 48–49, 68–69 | protected/restricted/unavailable/indeterminate states, no color-only status, responsive RTL/LTR isolation |

## 11. Exact Audit/outbox event ownership

| Batch | Exact accepted events |
|---|---|
| B1 | 1 standards.identity.registered; 2 standards.edition.registered; 3 standards.edition.standing_observed; 4 standards.rights.created; 5 standards.rights.replaced; 6 standards.rights.expired; 7 standards.rights.revoked |
| B2 | 11 standards.source.retrieval_succeeded; 12 standards.source.retrieval_unavailable; 13 standards.source.snapshot_created; 14 standards.assertion.created; 15 standards.assertion.human_verified; 16 standards.assertion.rejected; 17 standards.assertion.stale |
| B3 | 8 standards.applicability.candidate_recorded; 9 standards.applicability.declared; 10 standards.applicability.retired |
| B4 | 21 technical_report.standards_basis.attached; 22 technical_report.accepted |
| B5 | 18 standards.intelligence.requested; 19 standards.intelligence.completed; 20 standards.intelligence.unavailable |

Each owning batch proves that authoritative domain mutation, AuditLog, capability-owned outbox, and idempotency completion/replay where required commit atomically or roll back together. Payload tests forbid protected content, source/provider handles, object keys, license terms, credentials, prompts, excerpts, and unsafe diagnostics.

## 12. Exact API operation ownership

| Batch | Exact operations |
|---|---|
| B1 | CAT-01 GET /standards; CAT-02 GET /standards/{standard_id}; CAT-03 POST /standards; CAT-04 POST /standards/{standard_id}/editions; CAT-05 POST /standards/{standard_id}/editions/{edition_id}/standing-observations; RGT-01 GET /organizations/current/standard-rights; RGT-02 PUT /organizations/current/standard-rights/{edition_id}/{source_provider_id}; RGT-03 POST /organizations/current/standard-rights/{rights_binding_id}/revocations |
| B2 | SRC-01 POST /projects/{project_id}/standards/source-snapshots; SRC-02 GET /projects/{project_id}/standards/source-snapshots/{snapshot_id}/display; AST-01 POST /projects/{project_id}/standards/assertions; AST-02 POST /projects/{project_id}/standards/assertions/{assertion_id}/verifications; AST-03 POST /projects/{project_id}/standards/assertions/{assertion_id}/rejections |
| B3 | APP-01 GET /projects/{project_id}/standards/applicability; APP-02 GET /projects/{project_id}/standards/candidates; APP-03 POST /projects/{project_id}/standards/applicability; APP-04 POST /projects/{project_id}/standards/applicability/{applicability_id}/retirements |
| B4 | RPT-01 GET /technical-reports/{report_id}/standards/candidates; RPT-02 POST /technical-reports/{report_id}/standards-basis-revisions; RPT-03 POST /technical-reports/{report_id}/acceptance |
| B5 | INT-01 POST /projects/{project_id}/standards/intelligence-runs; INT-02 GET /projects/{project_id}/standards/intelligence-runs/{run_id} |

No batch adds a browser, raw protected-text endpoint, arbitrary URL fetcher, scraper, bulk export, provider passthrough, or other operation.

## 13. Qualification plans

### 13.1 Migration and PostgreSQL

Future evidence must cover clean install; upgrade from e05300000002 through M1 then M2; sole-head validation; M2 linearity; runtime-role grants; installer/migration-owner separation; immutable triggers; history/single-head constraints; accepted legacy preservation; and fail-closed downgrade guards. Downgrade may proceed only when no retained PATCH-054 data/basis would be lost; otherwise it refuses without destructive conversion. All migration/role/concurrency assertions require real PostgreSQL, never SQLite substitution.

### 13.2 Security and authority

Every batch executes its authorization-before-protected-lookup tests. The cumulative suite proves Organization/project/report isolation; identical absent/forbidden shape; capability-specific rights; provider/handle binding; expiry/revocation final checks; no prohibited database mutation; no outbox leakage; no public object access; and Report historical/current-access separation.

### 13.3 Resource limits

Boundary fixtures prove 64 editions, 64 active applicability heads, 16 Report bases, 32 Report provenance rows, 8 fragments, 8192 bytes per fragment, 32768 aggregate context, 32 assertions, 12 suggestions, one provider call, 30 seconds, zero AI retries, three database attempts, metadata 20/100 pagination, and protected 20/20 pagination. Plus-one behavior is explicit bounded failure, never silent truncation.

### 13.4 Whole-PATCH qualification

After all five Human-accepted batches: cumulative 96/96; focused standards suite; full backend regression; frontend test/build/type/static checks; migration/head/clean-upgrade evidence; runtime role/security; rights/revocation; Report historical correctness; AI egress; resource bounds; manifest reconciliation; QG-11; QG-12; and one Whole-PATCH independent review.

## 14. Future delivery and closure controls

Recommend one governed implementation commit per Human-accepted batch, after its evidence and review pass. Split only when an independently reviewable migration atomic boundary makes that necessary. Each commit must contain only its authorized manifest paths and must not absorb unrelated dirty work. No commit or push is authorized by this Plan.

Governance-fatigue discipline: Critical findings always remediate. Genuine Major findings affecting security, tenant isolation, data integrity, authority/audit, historical correctness, rights enforcement, or core behavior remediate before Human acceptance. Nonblocking Minor findings and Observations are recorded/deferred without unnecessary fresh-review loops.

PATCH-054 may be recommended DONE/CLOSED only after all five batches are Human accepted; cumulative 96/96 passes; there is no Critical or unresolved genuine Major; migrations and sole head qualify; Technical Report authority, rights enforcement, Organization isolation, AI egress, historical reproducibility, frontend qualification, full regression, QG-11, QG-12, and final manifest reconciliation pass.

Explicit exclusions remain: general Evidence Workbench; broad retention governance; Methods & Systems; Command Center completion; commercial authentication/release work; seat/license enforcement; deployment qualification; whole-standard repository; standards marketplace; arbitrary retrieval; autonomous AI loops/tools; and every PATCH-055+ concern.

## 15. Plan self-review

Independent Plan review compared this document with accepted Discovery, ADR-027, EDS-054, IDS-054, current repository baseline, all 71 manifest paths, 96 vectors, 22 events, 22 API operations, six frontend surfaces, two migrations, five batch boundaries, and Commercial V1 exclusions.

| Severity | Count | Result |
|---|---:|---|
| Critical | 0 | None. |
| Major | 0 | None. |
| Minor | 0 | None. |
| Observation | 1 | Revision IDs remain intentionally UNASSIGNED until separately authorized implementation because the sole head must be rechecked immediately before allocation. This follows repository convention and is nonblocking. |

Reconciliation performed: the plan assigns each of the IDS 71 paths exactly one primary owner while retaining IDS-required shared-batch hunks; it assigns the EDS primary vector allocation exactly 33/19/9/15/20, without duplication; and it keeps all frontend delivery in B5 so B3 does not introduce partial UI scope. No accepted design changed.

Verdict: PASS WITH OBSERVATION. Unresolved planning questions: none. ADR/EDS/IDS reopening required: NO.

## 16. Stop condition

This Plan ends PATCH-054 Implementation Plan preparation. It does not authorize Batch 1, migrations, tests, production/frontend edits, staging, commits, pushes, or PATCH-055+.

## Status reconciliation — 2026-09-14

Human Implementation Plan acceptance is **PASS / ACCEPTED / AUTHORITATIVE**. All five implementation batches were subsequently Human gated and accepted. The opening pre-implementation status table remains historical evidence and is superseded for current governance state by this append-only reconciliation. No plan semantics are changed and no PATCH-055 authority is granted.
