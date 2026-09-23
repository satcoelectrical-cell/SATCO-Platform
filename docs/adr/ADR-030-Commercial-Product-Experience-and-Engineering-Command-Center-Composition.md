# ADR-030 — Commercial Product Experience & Engineering Command Center Composition

## Status
**Proposed / Candidate — awaiting independent architecture review and Human ADR acceptance.**

This ADR authorizes no EDS, IDS, Implementation Plan, implementation, migration, staging, commit, push, deployment, or PATCH-058 work.

## Date
2026-09-22

## Context
PATCH-057 must turn completed Commercial V1 engineering capabilities into coherent paying-customer journeys. Existing domains already own Customer, Project, Workspace, packages, engineering entities, cross-discipline findings, standards, Evidence/retention, engineering performance, Reports and Memory. Current UI gaps include first-visible selection, bounded client slices, disconnected panels, raw internal identifiers and advisory actions without canonical owner routing.

## Decision
SATCO shall implement PATCH-057 as an authorized product-composition and navigation layer over existing canonical owners. It may compose authorized read projections, explicit product context, Human-readable selectors, population-completeness metadata and safe owner-route descriptors. It shall not acquire canonical engineering mutation authority.

## Decisions
1. Product context is explicit and Human-selectable; first-visible records are presentation suggestions only.
2. Server contracts distinguish complete, partial/bounded, indeterminate/unavailable and protected population states as permitted by source-owner semantics.
3. Ordinary Human journeys use authorized selectors or opaque owner handles instead of typed raw internal IDs.
4. Composed next actions navigate to canonical owner workflows; activation reauthorizes and does not itself mutate owner state.
5. Command Center is read/composition/navigation; canonical mutation remains in owner workflows.
6. Package-aware onboarding/navigation derives from effective package configuration but package enablement never becomes engineering-data authority.
7. A thin server composition layer is permitted where required for safe multi-owner views; exact API shape is deferred to EDS.
8. No new canonical PATCH-057 persistence is required by default. Any later projection/cache requires explicit EDS/IDS justification and remains non-authoritative/rebuildable.
9. Accessibility, responsive and RTL behavior are acceptance contracts across integrated E/I/C and supported single-discipline journeys.
10. AI remains optional, advisory and non-authoritative.

## Consequences
The product can eliminate raw-ID/backend-only steps and disconnected navigation while retaining existing domain ownership. Safe completeness and reauthorization add API/UI contract complexity. A bounded server composition layer may be needed to avoid unsafe client joins, but it cannot become an omnibus backend.

## Alternatives rejected
- New universal Command Center aggregate: duplicates canonical ownership.
- Client-only joins and totals: bounded slices and authorization can create false totals or inference leaks.
- First-visible Project/Workspace as implicit context: visibility order is not Human selection or authority.
- Direct mutation from advisory cards: owner workflows and Human gates remain controlling.
- New PATCH-057 workflow persistence by default: composition/navigation does not require new canonical state.
- Raw UUID/revision entry for ordinary users: violates the frozen Commercial V1 exit condition.
- Package enablement as data authorization: package applicability and canonical data authority are separate.

## Compatibility
Architecture-051/052 and ADR-024 package contracts remain authoritative. PATCH-053 cross-discipline authority, ADR-027 standards rights, ADR-028 Evidence/retention, ADR-029 engineering-performance intelligence, Technical Report Human acceptance and Organizational Memory Human admission remain unchanged. PATCH-058 authentication/session/release, PATCH-059 entitlements/seats and PATCH-060 deployment certification remain separate.

## EDS-deferred decisions
EDS-057 must define exact selection/completeness DTOs, pagination/continuation, selector and route-handle contracts, Command Center slices, navigation hierarchy, package-onboarding states, source adapters, server-composition endpoint need, no-persistence proof or justified projection, accessibility/RTL vectors, authorization/anti-inference rules, performance bounds and deterministic Commercial V1 journey tests.

## Governance disposition
ADR-030 candidate is COMPLETE / READY FOR INDEPENDENT ARCHITECTURE REVIEW. Human ADR acceptance is not implied.

ADR-030: CANDIDATE / READY FOR INDEPENDENT ARCHITECTURE REVIEW

## Human ADR Acceptance

- Human Architecture Authority decision: **PASS / ACCEPTED / COMPLETE**.
- Acceptance date: 2026-09-22.
- Accepted after Independent Architecture Review returned **PASS / READY FOR HUMAN ARCHITECTURE ACCEPTANCE** with Critical/Major/Minor = 0/0/0.
- The decision to use an authorized product-composition/navigation layer, explicit Human-selectable context, safe population-completeness contracts, owner-routed/re-authorized actions, and no new canonical PATCH-057 persistence by default is accepted.
- Existing canonical owners and Human decision boundaries remain controlling; AI remains advisory and non-authoritative.
- This acceptance authorizes progression to EDS-057 preparation and independent review only.
- It does not authorize IDS-057, an Implementation Plan, implementation, migrations, production-code changes, database mutation, deployment, PATCH-058 work, or any canonical semantic change.

ADR-030: HUMAN ACCEPTED / COMPLETE
