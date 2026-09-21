# ADR-029 — Methods & Systems Engineering Performance, Health & Next-Action Intelligence

## Status

**Proposed / Candidate — awaiting independent architecture review and Human ADR acceptance.**

This candidate is not Accepted. It establishes no EDS, IDS, implementation, migration, frontend, deployment, staging, commit, push, or PATCH-057+ authority.

## Date

2026-09-19

## Decision owner and authority

- Decision owner: Human Architecture Authority.
- PATCH-056 Registry: **REGISTERED / OPEN**.
- Human PATCH-056 Discovery Acceptance: **PASS / ACCEPTED / COMPLETE**.
- ADR-029 preparation and independent review: authorized as the next Docs-First gate.
- Human ADR-029 acceptance: **NOT YET GRANTED**.

## Context

PATCH-056 is the Human-frozen Commercial V1 Methods & Systems capability. It is discipline-neutral and limited to engineering departments and the engineering lifecycle. Existing SATCO domains already own canonical Project/Workspace authorization, Execution, Deliverables, Project Control, Completeness, Interface Commitments, Evidence, Technical Reports, Audit and Human decisions.

The architecture problem is to derive explainable engineering-process intelligence from those facts without creating a competing source of truth, personnel-surveillance system, opaque score, or autonomous workflow authority.
## Decision

SATCO shall implement PATCH-056 as a **read/derived Engineering Performance Intelligence layer** over authorized canonical engineering facts.

Canonical operational domains retain ownership of their state. PATCH-056 owns indicator definitions, reproducible derived observations/trends, transparent Engineering Health factor composition, and advisory next-action projections. It does not own or rewrite the underlying engineering workflow state.

## Core invariants

1. Canonical engineering domains remain the source of truth.
2. Every indicator exposes scope, calculation basis, time window, source cutoff, exclusions, missing-data limitations and authorized drill-down.
3. Aggregation must not disclose protected facts through counts, trends, factors, existence signals or drill-down.
4. Missing, unavailable, not-disclosed and genuinely absent data remain distinguishable where source contracts permit.
5. Engineering Health is a transparent factor composition, not an opaque personnel or project score.
6. Advisory next actions are evidence-linked and explainable; they do not mutate canonical state or imply approval.
7. AI may explain or propose but may not approve, rank personnel, close work, alter facts or create management authority.
8. Derived snapshots, if persisted, are reproducible projections with source watermark/digest and recalculation semantics.
9. Human engineering authority remains explicit at all existing acceptance/disposition boundaries.
10. Individual productivity ranking, employee surveillance and HR appraisal are prohibited PATCH-056 purposes.
## Indicator boundary

Commercial V1 shall cover at minimum: required-input readiness/aging, blocked-work aging, milestone predictability, deliverable review/issue cycle time, rework/revision trend, risk/issue/change aging, Interface Commitment response/fulfilment, completeness trend, Technical Report acceptance flow and Evidence availability.

EDS-056 must define deterministic contracts for each included indicator family and may narrow implementation to the minimum coherent set needed to satisfy the frozen capability, but may not silently replace required families with a generic score.

## Engineering Health and next actions

Engineering Health shall be composed from named, separately inspectable factors. A factor must retain its source basis and limitation state. No single unexplained numeric score may stand in for the underlying engineering facts.

Next actions are advisory projections from visible engineering conditions. Each action must identify why it is suggested, the supporting authorized facts, limitations, and the Human-owned operation or domain to which it refers. PATCH-056 does not execute that operation automatically.

## Authorization and anti-inference

Authorization is applied before aggregation and before drill-down. A caller may only receive an aggregate that can be safely derived from facts visible within the caller's current Organization / Project / Workspace authority.

The design must fail closed where aggregation could become a count oracle or reveal hidden cross-discipline state. Audit/observability must minimize protected content and avoid logging unrestricted indicator source payloads or AI prompts containing protected material.
## Explicit non-scope

PATCH-056 does not introduce employee ranking, individual productivity scores, surveillance, HR appraisal, payroll, finance/accounting, Project Cost Baseline, invoicing, portfolio accounting, enterprise ERP/BPM, autonomous workflow mutation, new engineering disciplines, Command Center completion (PATCH-057), commercial authentication/release (PATCH-058), signed entitlements/seats (PATCH-059), deployment certification (PATCH-060), or post-PATCH-060 ideas.

## Compatibility with prior architecture

ADR-024 package identity/configuration seams remain authoritative. PATCH-052 operational E/I/C packages retain domain ownership. ADR-026 and PATCH-053 retain cross-discipline finding/Human-disposition authority. ADR-027 retains standards rights/retrieval authority. ADR-028 retains Evidence/retention authority. Existing Completeness remains an advisory bounded capability and is an input where authorized, not the canonical owner of Engineering Performance.

No prior accepted ADR or CLOSED PATCH is superseded by this decision.

## Consequences

Positive consequences are a discipline-neutral Methods & Systems layer, explainable engineering-process visibility, trend and bottleneck awareness, auditable next-action advice, and reuse of existing canonical facts without duplicating workflow ownership.

Costs include typed indicator contracts, safe temporal calculations, source-watermark/recalculation behavior, anti-inference authorization, data-quality/limitation states, drill-down composition and regression/security testing across multiple source domains.
## Alternatives rejected

- Build a new workflow/BPM source of truth: rejected because PATCH-056 is derived intelligence, not canonical execution ownership.
- Use one opaque health/productivity score: rejected because it weakens explainability and can drift into personnel evaluation.
- Rank engineers or teams: rejected as outside the Human-frozen Commercial V1 boundary.
- Let AI execute next actions: rejected because AI remains advisory and non-authoritative.
- Treat missing protected data as zero/healthy: rejected because it creates false engineering conclusions and authorization leakage.
- Pull Project Cost/finance into PATCH-056: rejected because the later Human-frozen Post-PATCH-050 re-baseline controls current PATCH-056 scope.

## EDS-deferred decisions

EDS-056 must freeze indicator vocabularies and formulas, source adapters/projections, temporal/window semantics, source cutoff/watermark, missing-data states, Health factor composition, next-action contract, authorization/drill-down rules, concurrency/recalculation behavior, API/UI contracts, audit/observability redaction, accessibility/RTL behavior, persistence necessity and deterministic conformance vectors.

IDS-056 must later freeze exact schema/projection storage if any, indexes/constraints, repository/UoW topology, query and authorization order, API DTOs, frontend composition, migration/rollback details, performance limits and exact implementation manifest.

## Manifesto alignment

ADR-029 preserves Human Authority, Engineering Context Is Sacred, Evidence Before Assumption, Intelligence Before Automation, Explainability, Organizational Ownership and Continuous Evolution by deriving transparent advisory intelligence from governed facts without rewriting their authority.

## Governance disposition

ADR-029 candidate design is **COMPLETE / READY FOR INDEPENDENT ARCHITECTURE REVIEW**.

Human ADR acceptance is not implied. EDS-056, IDS-056, implementation, migration, staging, commit, push, deployment and PATCH-057+ remain not authorized by this ADR candidate.
## Human ADR acceptance

- Human Architecture Authority decision: **PASS / ACCEPTED / COMPLETE**.
- Acceptance date: 2026-09-19.
- Accepted after Independent Architecture Review returned `PASS / READY FOR HUMAN ADR ACCEPTANCE` with `Critical/Major/Minor = 0/0/0` and three non-blocking EDS observations.
- `A056-OBS-01`, `A056-OBS-02` and `A056-OBS-03` remain mandatory EDS-056 inputs and are not waived by this acceptance.
- This acceptance authorizes progression to EDS-056 preparation and independent review only.
- It does not authorize IDS-056, Implementation Plan, implementation, migrations, production-code changes, database mutation, staging, commit, push, deployment or PATCH-057+ work.

`ADR-029: HUMAN ACCEPTED / COMPLETE`