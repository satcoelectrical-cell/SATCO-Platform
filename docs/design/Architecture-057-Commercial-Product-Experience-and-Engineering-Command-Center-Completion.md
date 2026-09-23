# Architecture-057 — Commercial Product Experience & Engineering Command Center Completion

**Date:** 2026-09-22
**Status:** CANDIDATE / READY FOR INDEPENDENT ARCHITECTURE REVIEW
**Authority:** PATCH-057 Discovery is Human accepted; this candidate is not Human accepted and authorizes no EDS, IDS, implementation, migration, staging, commit, push, deployment, or PATCH-058 work.

## Purpose and invariants
PATCH-057 is the Commercial V1 product-composition boundary. Existing canonical domain owners remain the only writers of their facts and lifecycle. PATCH-057 composes authorized reads, context, navigation and Human intent; it never silently performs owner actions.

Server-derived Organization authority and owner authorization precede disclosure, aggregation, selection and drill-down. Customer, Project and Workspace context is explicit and Human-selectable; first-visible records are never authoritative selection. Ordinary commercial journeys do not require raw UUIDs, revision IDs or backend-only knowledge. Hidden or unauthorized records cannot be inferred through counts, totals, pagination, empty states, package state or derived summaries.

Human engineering authority remains controlling; AI remains optional, advisory and non-authoritative. Browser-local state is presentation/navigation preference only. PATCH-055 Evidence/retention and PATCH-056 derived-intelligence remain mandatory dependencies. PATCH-058 authentication/session/release, PATCH-059 entitlements/seats and PATCH-060 deployment certification remain separate.

## Product composition model
The product shell establishes authorized Organization context and exposes explicit Customer/Project/Workspace selection. Project experience composes domain summaries and owner-entry points. Discipline workspaces expose only capabilities applicable to effective package configuration. The Engineering Command Center is a cross-domain read/composition surface, not a second Project or workflow source of truth.

Composition may normalize presentation metadata such as labels, route targets, safe state categories and authorized opaque handles. It may not duplicate canonical engineering facts or lifecycle state.

## Selection and population contract
Selection is explicit, stable and context-preserving. A default may be suggested only as presentation convenience; it cannot silently become canonical selection or authority.

Every collection used for commercial totals, summaries or decisions must distinguish complete authorized population, bounded/partial authorized population, unavailable/indeterminate population, and protected/non-disclosable state where the owner contract permits such a neutral response. A client slice is never represented as a total population unless the server contract proves completeness. Pagination/continuation preserves authorization and cannot expose hidden global counts.

## Human-readable identity and owner routing
Internal identifiers remain valid transport/persistence identities but are not ordinary Human input. Journeys resolve choices through authorized selectors, existing canonical identity projections, or server-issued opaque navigation/action handles. A handle conveys no additional authority, is reauthorized at use time, and cannot encode hidden facts for client reconstruction.

Composed intelligence, Health factors, findings, standards state and Evidence state may expose an actionable next step only when it maps to an existing canonical owner workflow. PATCH-057 owns route/navigation composition, not the owner command. Stale, superseded, resolved, protected or no-longer-applicable targets fail safely. Deep links are navigation conveniences, not bearer authorization.

## Command Center and workspace responsibilities
The Command Center answers what authorized engineering context needs Human attention, why, and where the accountable owner workflow lives. It composes Project context, effective package state, cross-discipline intelligence, standards, Evidence availability/retention, Engineering Health/trends/next actions, Reports and Memory at a truthful scope.

Project and discipline workspaces answer what the Human can inspect or do within a specific owner/domain context. Canonical create/update/accept/dispose/verify/admit operations remain in existing owner workflows. This prevents an omnibus mutation UI while eliminating disconnected panel journeys.

## Package-aware onboarding and navigation
After authorized Project context, onboarding presents effective supported package configuration and available discipline workspaces using existing PATCH-051/052 package authority. Package enablement/configuration constrains what may be offered but never grants engineering-data access.

Integrated E/I/C and supported single-discipline configurations share the same composition contract. Navigation adapts to effective packages without inventing absent disciplines or leaking unavailable package/data state.

## Domain composition
PATCH-053 findings/dispositions, PATCH-054 standards/rights, PATCH-055 Evidence/retention and PATCH-056 performance/Health/next actions retain accepted semantics and authorization. PATCH-057 may compose safe summaries, selectors and navigation. It cannot bypass rights, accept Evidence/Reports, verify standards assertions, dispose findings, change retention, resolve engineering issues, admit Memory, or execute advisory next actions.

## Persistence and server composition
No new PATCH-057 canonical persistence is required by default. Product selection, composition and routing should reuse existing owner APIs and server-derived context.

EDS-057 must prove any proposed persistence necessary. A durable projection/cache, if justified, must be non-authoritative, Organization-scoped, source-watermarked, invalidatable/rebuildable and authorization-safe. Any schema/migration requires later explicit IDS and implementation authority.

A thin server composition/query layer is permitted where multiple authorized owner reads must be joined safely. It returns presentation-oriented projections and safe owner-route descriptors; it is not a writer. Exact endpoints, DTOs, pagination tokens and whether existing endpoints suffice are EDS decisions.

## Security, accessibility and AI
All source reads authorize independently before composition. Cross-Organization facts, hidden counts, graph shapes, existence signals and protected package/domain state are not exposed through derived UI. Aggregation carries population-completeness semantics and owner action activation reauthorizes. Authentication/session architecture remains PATCH-058.

Integrated navigation, selectors, composed states and owner routing must preserve keyboard operation, visible focus, semantic landmarks/headings, screen-reader names/status, reduced-motion behavior, responsive layouts and RTL correctness.

AI may explain already-authorized composed information or propose bounded navigation/next steps. It cannot change selection authority, completeness state, owner facts, Health calculations, findings, standards assertions, Evidence/retention, Reports, Memory or canonical lifecycle.

## Explicit non-scope
No generic Wizard/BPM/task engine; duplicate canonical state; fake totals or opaque score; employee ranking/surveillance; procurement; FAT/SAT/commissioning/closeout; autonomous mutation; authentication/session redesign; entitlement/seats work; deployment certification; or post-PATCH-060 ideas.

## EDS-deferred decisions
EDS-057 must freeze exact product context/selection state machine; population completeness/pagination; safe selectors and owner-route DTOs; Command Center composition slices/source adapters; integrated and discipline navigation; package onboarding states; owner-routing mappings; server-composition API necessity; persistence necessity with no-persistence as default; accessibility/responsive/RTL vectors; authorization/reauthorization/anti-inference/audit contracts; deterministic Commercial V1 journey vectors and performance limits.

IDS-057 later freezes physical component/module topology, exact query/authorization order, cache/schema details if any, route definitions, implementation manifest and migration/rollback details if explicitly required.

## Governance disposition
This candidate is complete enough for independent Architecture Review. Human Architecture Acceptance is not implied.

Architecture-057: CANDIDATE / READY FOR INDEPENDENT ARCHITECTURE REVIEW

## Human Architecture Acceptance

- Human Architecture Authority decision: **PASS / ACCEPTED / COMPLETE**.
- Acceptance date: 2026-09-22.
- Accepted after Independent Architecture Review returned **PASS / READY FOR HUMAN ARCHITECTURE ACCEPTANCE** with Critical/Major/Minor = 0/0/0.
- The accepted architecture preserves Human engineering authority, Organization isolation, canonical source-owner boundaries, mandatory PATCH-055/PATCH-056 dependencies, safe population-completeness semantics, owner-routed actions, no-raw-ID commercial journeys, and the PATCH-058+ separation.
- This acceptance authorizes progression to EDS-057 preparation and independent review only.
- It does not authorize IDS-057, an Implementation Plan, implementation, migrations, production-code changes, database mutation, deployment, PATCH-058 work, or any canonical semantic change.

Architecture-057: HUMAN ACCEPTED / COMPLETE
