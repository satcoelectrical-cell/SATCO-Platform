# IDS-056 — Methods & Systems Engineering Performance, Health & Next-Action Intelligence

## 1. Control and authority
Date: 2026-09-19. Discovery, ADR-029 and EDS-056 are HUMAN ACCEPTED / AUTHORITATIVE. IDS design/review authority is GRANTED. Implementation Plan and implementation remain NOT AUTHORIZED.

## 2. Topology and ownership
Implement a bounded engineering-performance module that reads existing authorized repositories/projections through typed adapters. It MUST NOT create a second Project, Execution, Deliverable, Interface, Evidence or Report authority.

Backend seams: indicator registry, authorized source adapters, calculation service, Health composer, next-action projector, trend/snapshot repository, router and DTOs. Frontend seams: project Engineering Performance summary, indicator/trend detail, five-factor Health, advisory Next Actions and authorized drill-down.

## 3. Persistence decision
Current observations and Health are calculated. Persist only derived reproducibility snapshots and next-action projection lifecycle needed for trend continuity, first/last-seen, deduplication and supersession.

Add exactly two logical tables: engineering_performance_snapshots and engineering_next_action_projections. No canonical owner table is repurposed. One additive migration is preferred; no revision ID is reserved here.

Snapshot rows contain scope, indicator/version, window, observed_at, source cutoff/digest, calculation version, observation state, typed safe value, limitations, safely retainable eligibility/count fields and timestamps. Changed source digest or method creates a new reproducible snapshot.

Next-action rows contain scope, stable action_key, rule/version, title/rationale codes, safe support handles, limitations, first/last seen, absent recalculation count, status, optional successor key, source digest/version and timestamps. Status is exactly active, stale, superseded, or resolved_by_source_state.

## 4. Calculators and adapters
Each of the ten EDS families has a stable versioned calculator. Calculators consume typed adapter results, not unrelated ORM objects. Adapters authorize Organization/Project/Workspace before returning facts and preserve visible/missing/not-applicable/indeterminate states.

Cross-domain calculation orchestrates independently authorized adapters; it does not bypass authorization with raw cross-domain SQL.

## 5. Safe aggregation
Cohort statistics enforce minimum visible population 5 after authorization and eligibility filtering. Suppressed results return insufficient_safe_population without the hidden count.

No endpoint accepts actor/user as a grouping, ranking, comparison or trend dimension. Actor identity may appear only in direct authorized provenance drill-down.

## 6. Health and next actions
Health emits exactly readiness, flow, coordination, quality_rework and evidence_acceptance using deterministic versioned rules. Each factor includes state, rule version, supporting indicators, rationale and limitations. No overall numeric score exists.

Next-action rules are deterministic/versioned and AI is not in their execution path. Stable action keys derive from rule/version + scope + stable subject basis. Concurrent recalculation cannot create duplicate active projections. Optional AI explanation is downstream and receives only authorized projected context.

## 7. API boundary
Route family: /api/v1/projects/{project_id}/engineering-performance.

Logical GET operations: catalog, indicators, health, trends, next-actions, drill-down. Optional workspace, supported window and indicator filters are query parameters. Organization is server-derived.

Response DTOs use closed EDS enums. Indicator values are discriminated typed structures, not arbitrary API JSON. Safe outcomes are success, partial, indeterminate, not_applicable, protected_not_found, insufficient_safe_population, method_changed, conflict, unavailable.

## 8. Transactions and reproducibility
Reads use a bounded source cutoff. Snapshot/action writes happen only after successful authorized calculation. Snapshot insertion is idempotent on reproducibility identity. Action projection update locks the scoped current key.

Canonical source transactions are never held while analytical projections are written. Failed calculations leave no partial analytical authority.

## 9. Frontend
Add a project-level Engineering Performance surface through centralized API/types. Show summary indicators, five Health factors, trends, advisory actions and authorized drill-down.

Always expose derived/advisory/non-authoritative status, window, cutoff, method and limitations. Distinguish partial, indeterminate, suppressed, stale and method_changed. No employee leaderboard/productivity comparison. Keyboard, visible focus, semantic labels, live status, responsive layout and RTL-safe Persian are mandatory.

## 10. Migration and rollback
One additive migration may create only the two derived tables plus constraints/indexes. No fabricated historical backfill and no canonical table changes. Upgrade/downgrade must qualify against the pre-PATCH-056 head. Exact Alembic ID is allocated only during authorized implementation.

## 11. Observability/performance
Logs/metrics may include indicator/version, safe scope correlation, duration, outcome and safe limitation/suppression classes; never protected source payloads, hidden exact counts or AI prompts. Implementation Plan freezes query budgets/indexes after repository inspection. Silent truncation is prohibited.

## 12. Executable manifest
P056-IND-01..10 cover ten indicators. P056-HLT-01..05 cover Health. P056-ACT-01..04 cover dedup, stale/resolved, supersession and AI non-authority. P056-SEC-01..05 cover authorization, wrong-org, suppression, cross-workspace and no personnel ranking. P056-DAT-01..04 cover denominator safety, partial/indeterminate, method segmentation and watermark reproducibility. P056-OWN-01..02 cover canonical non-mutation/derived persistence. P056-UX-01..04 cover explainability, advisory labeling, RTL/accessibility and drill-down.

Exact test files/fixtures belong to Implementation Plan. No vector is claimed PASS here.

## 13. Shared-file and stop boundary
Expected new files stay under engineering-performance backend/frontend modules plus focused tests and migration if required. Existing domain files receive only minimal adapter/export/router registration.

Known shared dirty files such as backend/app/main.py require fresh ownership inspection and surgical edits only. Preserve all unrelated working-tree content.

STOP if accepted EDS semantics need change, a required fact lacks an authorized canonical seam, safe aggregation cannot avoid inference, persistence requires destructive/canonical changes, Alembic is not single-head, or unrelated dirty work cannot be isolated.

## 14. Disposition
IDS-056 is COMPLETE / READY FOR INDEPENDENT IDS REVIEW.

No Implementation Plan, implementation, migration creation/execution, source mutation, database mutation, staging, commit, push, deployment or PATCH-057+ authority is granted.
## 15. Human IDS acceptance

- Human Implementation Design Authority: **PASS / ACCEPTED / COMPLETE**.
- Acceptance date: 2026-09-19.
- Accepted after Independent IDS Review returned `PASS / ACCEPTED-CANDIDATE / READY FOR HUMAN IDS ACCEPTANCE` with `Critical/Major/Minor/Observation = 0/0/0/0`.
- IDS-056 is now the authoritative repository-specific implementation design for PATCH-056.
- This acceptance authorizes progression to Implementation Plan-056 preparation and independent review only.
- It does not authorize implementation, migration creation/execution, production/test/frontend changes, database mutation, staging, commit, push, deployment or PATCH-057+ work.

`IDS-056: HUMAN ACCEPTED / AUTHORITATIVE / COMPLETE`