# Implementation-Plan-056 — Methods & Systems Engineering Performance, Health & Next-Action Intelligence

## 1. Status and authority
Date: 2026-09-19. PATCH-056 is REGISTERED / OPEN. ADR-029, EDS-056 and IDS-056 are HUMAN ACCEPTED / AUTHORITATIVE. Plan candidate is COMPLETE / UNDER INDEPENDENT REVIEW. Implementation is NOT AUTHORIZED.

Repository preflight: HEAD 4608c6671976021cdcbd9191d51d0e2cdce96ba4; branch patch-022.3a-development-infrastructure; 149 dirty/untracked paths preserved. Executable Alembic preflight reports sole head e05500000002.

## 2. Readiness and isolation
Before each implementation checkpoint, record HEAD/branch/status, sole Alembic head and shared-file diffs. Preserve all unrelated dirty work. Never use git add dot/all, reset, clean, stash, checkout-overwrite or destructive database commands.

Only disposable PATCH-056 PostgreSQL may be used for migration/DB qualification. Production/customer databases and the real local PostgreSQL service are forbidden.

## 3. Bounded change surface
Create bounded engineering-performance backend modules for models/projections, schemas, authorized adapters, calculators, Health composer, next-action projector, repository/service/router and focused tests. Add one additive migration only if the accepted IDS persistence is implemented.

Frontend changes are bounded to centralized API/types, project Engineering Performance components/composition and focused tests.

Existing domain-owner files may receive only minimal adapter exports/router registration. Shared dirty files, especially backend/app/main.py, require surgical hunk isolation after fresh diff inspection.

## 4. Checkpoint A — derived domain and persistence
Implement closed vocabularies, typed indicator/result contracts, Health factors, next-action projection contract, source digest/watermark semantics and the two derived persistence tables selected by IDS.

Migration parent MUST be the executable sole head e05500000002 unless fresh preflight proves otherwise; any drift is STOP. Allocate the PATCH-056 revision only during implementation.

Exit evidence: fresh install, upgrade from parent, constraints/indexes, idempotent snapshot identity, unique scoped action projection behavior, downgrade/re-upgrade, sole head, and proof no canonical owner table/history is mutated.

## 5. Checkpoint B — authorized adapters and ten indicators
Implement typed authorized adapters over existing canonical seams, then all ten calculators: input readiness/aging; blocked-work aging; milestone predictability; deliverable review cycle; rework/revision trend; risk/issue/change aging; Interface Commitment fulfilment; completeness trend; Technical Report acceptance flow; Evidence availability.

Authorization precedes source selection. Missing/not-applicable/protected/indeterminate states and denominator eligibility are explicit. Cohort statistics suppress visible populations below five without returning hidden counts.

Exit evidence: P056-IND-01..10, P056-DAT-01..04 and relevant P056-SEC vectors pass.

## 6. Checkpoint C — Health, advisory actions and transport
Implement five deterministic Health factors and deterministic next-action rules/lifecycle. AI remains outside calculation/rule execution and may only explain authorized projections.

Expose the accepted project-scoped engineering-performance route family for catalog, indicators, health, trends, next-actions and drill-down. Organization remains server-derived.

Exit evidence: P056-HLT-01..05, P056-ACT-01..04, P056-SEC-01..05 and P056-OWN-01..02 pass, including wrong-Organization nondisclosure, cross-workspace safety, no personnel ranking and canonical-state non-mutation.

## 7. Checkpoint D — frontend experience
Implement project Engineering Performance summary, indicator/trend details, five-factor Health, advisory Next Actions and authorized drill-down through centralized API/types.

UI must show derived/advisory/non-authoritative status, window, cutoff, method and limitations; distinguish partial, indeterminate, suppressed, stale and method_changed; prohibit employee leaderboards/productivity comparison; preserve responsive, keyboard, focus, semantic-label and RTL behavior.

Exit evidence: P056-UX-01..04 pass.

## 8. Qualification and regression
Frozen manifest contains 30 vectors: 10 IND + 5 HLT + 4 ACT + 5 SEC + 4 DAT + 2 OWN + 4 UX = 34 vectors. This arithmetic correction is authoritative for the Plan: exact manifest count is 34, preserving every IDS vector and dropping none.

After focused PASS, run bounded affected-domain regressions, full backend suite, full frontend Vitest, typecheck and build. Migration qualification uses disposable PostgreSQL only. Record commands, environment, revision/head, counts, exit codes, failures and limitations. Never infer PASS.

## 9. Operational and rollback rules
Metrics/logs use safe indicator/version/outcome/limitation classes only; no protected payload, hidden exact count, user ranking, AI prompt or foreign scope metadata.

Application rollback disables PATCH-056 routes/UI without altering canonical history. Schema rollback affects only empty/safely disposable derived PATCH-056 tables after compatibility is restored; populated customer data requires governed forward-repair rather than destructive rollback.

## 10. Stop conditions
STOP on Alembic drift; need to alter accepted ADR/EDS/IDS semantics; missing authorized canonical source seam; unsafe protected inference; destructive/canonical schema requirement; unresolved Critical/Major finding; cross-Organization disclosure; personnel ranking/surveillance behavior; AI/canonical mutation; or unrelated dirty-work collision that cannot be isolated.

## 11. Human checkpoint model
After independent Plan review, explicit Human Plan acceptance is required. Then QG-5 Implementation Readiness Review must independently return exactly READY FOR IMPLEMENTATION with QG-M1 Readiness PASS before implementation authority can be requested.

Implementation proceeds A through D with evidence/review at each checkpoint. Completion of one checkpoint does not automatically authorize the next. Staging, commit, push, QG-11/QG-12 and PATCH closure remain separate future gates.

## 12. Disposition
Implementation-Plan-056 is COMPLETE / READY FOR INDEPENDENT PLAN REVIEW.

No implementation, migration creation/execution, source/test/frontend mutation, database mutation, staging, commit, push, deployment or PATCH-057+ authority is granted.
## 13. Human Plan acceptance

- Human Plan Authority: **PASS / ACCEPTED / COMPLETE**.
- Acceptance date: 2026-09-19.
- Accepted after Independent Plan Review returned `PASS / PLAN COMPLETE / READY FOR HUMAN PLAN ACCEPTANCE` with `Critical/Major/Minor/Observation = 0/0/0/0`.
- The corrected frozen conformance manifest contains exactly **34 P056 vectors**.
- This acceptance authorizes preparation and independent execution of the PATCH-056 QG-5 Implementation Readiness Review only.
- It does not authorize implementation, migration creation/execution, source/test/frontend changes, database mutation, staging, commit, push, deployment or PATCH-057+ work.

`Implementation-Plan-056: HUMAN ACCEPTED / COMPLETE`