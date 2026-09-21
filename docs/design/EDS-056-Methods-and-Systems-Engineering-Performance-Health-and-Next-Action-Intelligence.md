# EDS-056 — Methods & Systems Engineering Performance, Health & Next-Action Intelligence

## 1. Status and authority

Date: 2026-09-19. PATCH-056 Discovery and ADR-029 are HUMAN ACCEPTED. EDS design authority is GRANTED. EDS-056 is PROPOSED / READY FOR INDEPENDENT REVIEW. IDS, Implementation Plan and implementation remain NOT AUTHORIZED.

This EDS defines the finite Commercial V1 engineering-performance contract. It does not define SQL, reserve migration IDs, authorize source changes, or accept itself.

## 2. Preserved canonical owners

PATCH-056 consumes authorized facts but SHALL NOT own or rewrite Project, Workspace, Execution, Deliverable, Project Control, Completeness, Interface Commitment, Evidence, Technical Report, Audit or Human-decision state.

Its owned outputs are derived indicator observations, transparent Engineering Health factors, trends, and advisory next-action projections.

## 3. Exact indicator families

Commercial V1 SHALL expose exactly these ten families: input readiness/aging; blocked-work aging; milestone predictability; deliverable review/issue cycle; rework/revision trend; risk/issue/change aging; Interface Commitment fulfilment; completeness trend; Technical Report acceptance flow; Evidence availability.

Each observation MUST contain indicator/version, Organization/Project scope, optional Workspace scope, observation time, time window, source cutoff/watermark, calculation method/version, eligible population, numerator/denominator where applicable, value/unit, limitation state/codes, source digest, and authorized drill-down handles.

## 4. Eligibility and denominator semantics — resolves A056-OBS-01

Every ratio/cycle indicator SHALL define an explicit eligible population before calculation. Not-applicable, protected/not-visible, structurally missing and invalid facts MUST NOT silently enter the denominator as zero or success.

Observation states are exactly complete, partial, indeterminate, or not_applicable. Partial requires explicit missing/excluded counts where safely disclosable. Indeterminate is required when missing/protected data can materially change the conclusion and cannot safely be quantified.

Cycle-time clocks use timezone-aware canonical event instants and named start/stop event types. Open cycles are reported separately from completed-cycle statistics.

## 5. Safe aggregation — resolves A056-OBS-02

Authorization SHALL precede source selection and aggregation. Results include only facts the caller is currently authorized to observe.

Cohort-style breakdowns with fewer than 5 eligible visible items SHALL be suppressed unless the result is a direct authorized drill-down list. Suppressed buckets return insufficient_safe_population without revealing the hidden count.

No PATCH-056 surface may group, rank, compare, score or trend individual employees. Actor identity may appear only as already-authorized provenance of an underlying canonical engineering fact.

## 6. Engineering Health contract

Engineering Health is a set of named factors, not one opaque score. Exact V1 factors are readiness, flow, coordination, quality_rework, and evidence_acceptance.

Each factor is healthy, attention, constrained, indeterminate, or not_applicable, with supporting indicator IDs, deterministic rule version, rationale codes and limitations. Overall presentation SHALL show the factor set and MUST NOT collapse it into a personnel/project grade, leaderboard or unexplained percentage.

## 7. Advisory next-action contract — resolves A056-OBS-03

Each advisory action has stable action_key, rule/version, scope, title, rationale codes, supporting indicator/source handles, limitation codes, first_seen_at, last_seen_at, status, and optional superseded_by key.

Statuses are exactly active, stale, superseded, resolved_by_source_state. PATCH-056 does not create a canonical task or Human decision record.

The same rule/scope/subject basis MUST deduplicate to one active action key. Recalculation refreshes last_seen_at. If the triggering condition is absent for two consecutive recalculations or more than 24 hours, whichever is later, the projection becomes resolved_by_source_state. A materially replaced recommendation becomes superseded and points to its successor.

## 8. Trend and reproducibility

Persisted snapshots, if later selected by IDS, are derived and reproducible and carry source watermark/digest, calculation version and recomputation reason. Trend comparisons require compatible calculation versions. Incompatible versions are labeled method_changed and are segmented rather than presented as continuous comparable trends.

## 9. Minimum calculation semantics

Readiness classifies eligible required inputs and ages unresolved requirements. Blocked-work aging runs from canonical blocked-state start to unblock/current cutoff. Milestone predictability uses accepted target dates and canonical forecast/actual evidence, never AI-invented dates.

Deliverable review cycle uses canonical review-open through accepted/closed events with open cycles separate. Rework/revision uses revision/reopen events. Risk/issue/change aging preserves unlike source types. Interface fulfilment uses eligible commitment due/fulfilled/open/overdue state. Completeness trend uses versioned authorized completeness observations. Report acceptance uses canonical draft/review/accepted events. Evidence availability uses authorized current standing/availability and never treats hidden data as absent.

## 10. Logical API and limits

Required logical reads: indicator catalog, calculate/read observations, Health factors, trend series, advisory next actions, and authorized drill-down. Exact HTTP routes/DTOs belong to IDS.

Default window is 30 days; supported windows are 7, 30, 90 and 180 days. Trend maximum is 180 daily or 26 weekly points per indicator. One request may select at most 10 indicator families. Drill-down defaults to 20 and maxes at 100 visible items. Silent truncation represented as complete is prohibited.

## 11. UI, audit and AI

UI shows indicator name, state/value, window, cutoff, limitations and plain-language calculation explanation. Health shows five factors separately. Next actions are explicitly advisory and link to authorized facts. Protected/suppressed, partial, indeterminate, stale and method_changed states are distinct. Keyboard, focus, semantic labels, responsive and RTL-safe presentation are mandatory.

Persisted analytical events contain safe scope IDs, indicator/rule versions, digest/watermark and timestamps, never unrestricted source payloads or protected AI prompts. AI receives only authorized bounded analytical context and cannot alter calculations, Health state, action lifecycle, canonical state or Human decisions.

## 12. Failure, security, persistence

Logical outcomes include success, partial, indeterminate, not_applicable, protected_not_found, insufficient_safe_population, method_changed, conflict, and unavailable.

Wrong-Organization or forbidden IDs disclose no existence, count or trend. Authorization precedes validation that could create an oracle. Low-cardinality suppression cannot reveal the suppressed count. Cross-Workspace composition requires authority to every included source scope or safe exclusion with explicit limitations.

Persistence is not required merely to calculate current indicators. IDS decides whether reproducible snapshots/action projections need additive persistence. If not necessary, no migration is created. Any persistence is derived-only and does not repurpose canonical owner tables.

## 13. Conformance manifest

IDS shall create stable P056 vector IDs covering all 10 indicator families, all 5 Health factors, action dedup/stale/supersession, authorization-before-aggregation, wrong-Organization non-disclosure, low-cardinality suppression, denominator safety, partial/indeterminate behavior, method-version segmentation, source-watermark reproducibility, AI non-authority, canonical-state non-mutation, and RTL/accessibility rendering.

## 14. Explicit non-scope and disposition

Excluded: employee ranking/productivity scoring/surveillance, HR appraisal, payroll, finance/accounting, Project Cost Baseline, invoicing, portfolio accounting, enterprise ERP/BPM, autonomous workflow mutation, new disciplines, PATCH-057 Command Center, PATCH-058 auth/release, PATCH-059 entitlements, PATCH-060 deployment certification and post-PATCH-060 ideas.

A056-OBS-01, A056-OBS-02 and A056-OBS-03 are resolved by Sections 4, 5 and 7, subject to independent EDS review.

**EDS-056: PROPOSED / COMPLETE / READY FOR INDEPENDENT EDS REVIEW.**

No IDS, Implementation Plan, source/test/frontend change, migration, database mutation, staging, commit, push, deployment or PATCH-057+ authority is granted.
## 15. Human EDS acceptance

- Human Engineering Design Authority: **PASS / ACCEPTED / COMPLETE**.
- Acceptance date: 2026-09-19.
- Accepted after Independent EDS Review returned `PASS / ACCEPTED-CANDIDATE / READY FOR HUMAN EDS ACCEPTANCE` with `Critical/Major/Minor/Observation = 0/0/0/0`.
- `A056-OBS-01`, `A056-OBS-02`, and `A056-OBS-03` are **RESOLVED / CLOSED** by this accepted EDS contract.
- This acceptance makes EDS-056 authoritative and authorizes progression to IDS-056 preparation and independent review only.
- It does not authorize Implementation Plan, implementation, migrations, production/test/frontend changes, database mutation, staging, commit, push, deployment, or PATCH-057+ work.

`EDS-056: HUMAN ACCEPTED / AUTHORITATIVE / COMPLETE`