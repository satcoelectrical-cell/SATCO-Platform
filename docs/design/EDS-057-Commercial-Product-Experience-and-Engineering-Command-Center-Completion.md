# EDS-057 — Commercial Product Experience & Engineering Command Center Completion

## 1. Status and authority
**Status:** CANDIDATE / READY FOR INDEPENDENT EDS REVIEW
**Date:** 2026-09-22

Upstream authority is the Human-accepted PATCH-057 Discovery, Architecture-057 and ADR-030. This EDS freezes Commercial V1 external behavior and logical contracts only. It authorizes no IDS, Implementation Plan, implementation, migration, staging, commit, push, deployment or PATCH-058 work.

## 2. Preserved canonical owners
Customer, Project, Workspace, package configuration/applicability, engineering Object/Identifier/Relationship/Context, Capture, Evidence/Supporting File, Deliverable, PATCH-053 cross-discipline intelligence, PATCH-054 standards, PATCH-055 retention, PATCH-056 performance/Health/actions, Technical Report and Organizational Memory retain canonical authority.

PATCH-057 owns only product context composition, authorized read projections, Human-readable selection/navigation, safe completeness presentation and routing to existing owner workflows.

## 3. Product context state machine
The product context tuple is Organization -> Customer? -> Project? -> Workspace?. Organization is server-derived. Customer is required only where the Project owner contract requires it; Project and Workspace are explicit Human selections.

Context states are exactly: unselected, loading, ready, empty, partial, protected, unavailable, stale. A first-visible record may be suggested but cannot silently transition context to ready. Changing a parent clears incompatible descendants.

Deep links request a context; server authorization and current owner state determine whether it becomes ready.

## 4. Population completeness contract
Every composed collection exposes a population state from: complete, partial, indeterminate, unavailable. Protected absence remains neutral and is never converted into a count.

A complete result may expose authorized total_count. A partial result exposes returned_count plus continuation availability but no claim of global total unless the source owner supplies an authorization-safe total. Indeterminate/unavailable results expose no fabricated denominator.

Client slice length is never a total. Pagination tokens are opaque, Organization-scoped, query-bound, expiring implementation details and confer no authority.

## 5. Human-readable selector contract
Commercial selectors expose authorized display identity, bounded descriptive context, safe state and an opaque selection handle. Ordinary users never type canonical UUIDs, revision IDs, snapshot IDs, provider IDs or internal configuration IDs to complete a core journey.

Selection handles are non-authoritative references. Server use reauthorizes Organization, parent context and target owner. A handle from another context returns the neutral protected/not-found contract.

## 6. Owner-route descriptor
An actionable composed item may return an owner-route descriptor containing: route_kind, safe display label, opaque target handle, parent context handle, source state/version token where required, and optional Human-readable reason.

Allowed route kinds are limited to existing owner journeys frozen by IDS from the actual route inventory. The descriptor never contains a mutation command or grants write authority.

Activation reauthorizes and re-resolves current owner state. Stale/superseded/resolved/protected targets fail safely or navigate to a read-only historical owner view where that owner supports it.

## 7. Command Center composition
The Command Center composes these logical slices when authorized and applicable: current Project/Workspace context; effective package availability; cross-discipline findings/attention; standards state; Evidence availability/retention attention; Engineering Health factors/trends/advisory next actions; Technical Report state; Organizational Memory availability.

Each slice independently reports loading, ready, empty, partial, protected, unavailable or stale. Failure of one slice does not fabricate failure/success for another. No overall opaque health/productivity score is introduced.

Every actionable card identifies why attention is suggested and routes to the canonical owner workflow.

## 8. Project and discipline navigation
Project navigation groups existing owner capabilities into coherent Human-readable destinations rather than one sequential omnibus page. Discipline navigation is derived from effective package configuration plus authorized Workspace applicability.

Integrated E/I/C exposes common Project context and applicable discipline destinations. Supported single-discipline configurations expose only applicable destinations. Package enablement never substitutes for engineering-data authorization.

Navigation may remember presentation preference locally, but current authorized context always comes from server-authorized owner state.

## 9. Package-aware onboarding
After account/Organization onboarding and authorized Project establishment, PATCH-057 onboarding presents effective package configuration, supported discipline availability, Workspace readiness and the next Human-owned setup destination.

States are: ready_to_enter, needs_project_configuration, needs_workspace, partial, protected, unavailable. These are composition states, not new canonical lifecycle facts.

Onboarding never enables packages, creates Workspaces or mutates engineering entities implicitly; it routes the Human to existing owner workflows.

## 10. Cross-domain routing mappings
PATCH-053 finding attention routes to finding/detail/disposition owner surfaces. PATCH-054 standards attention routes to rights/applicability/assertion/report-basis owner surfaces. PATCH-055 Evidence/retention attention routes to Evidence Workbench or governed retention owner surfaces. PATCH-056 next actions route to the owner identified by the accepted source handle/action contract.

Technical Report actions route to Report authoring/acceptance owners. Memory actions route to Human admission/reuse owners. Exact route names and component paths are IDS-057 obligations derived from the repository; EDS does not invent endpoints.

## 11. Server composition API decision
Commercial V1 uses a bounded server-composed read model for Command Center summary and product-context population metadata where client-only joins would risk false completeness, excessive fan-out or authorization inference.

This read model is non-authoritative and read-only. It invokes source-owner authorization before including each slice and returns only safe projections. Canonical mutations continue through existing owner APIs.

EDS freezes logical operations, not URLs: get_product_context_options, get_command_center_summary, resolve_owner_route. IDS decides whether existing endpoints satisfy an operation or a new read endpoint is required.

## 12. Persistence decision
PATCH-057 requires no new database persistence for Commercial V1. Composition is computed from current authorized owner facts and existing derived PATCH-056 state.

Browser-local storage may retain non-sensitive presentation preferences only; it cannot persist authority, canonical selection, hidden identifiers or engineering state.

Any later need for durable server projection/cache is a design change requiring explicit governance review before schema/migration work.

## 13. Authorization and anti-inference
Organization is server-derived. Every source adapter authorizes before disclosure. Composition never unions unauthorized rows then filters client-side.

No response reveals hidden Organization/Project/Workspace existence, hidden package availability, hidden graph shape or hidden global counts. Protected/not-found behavior remains neutral according to owner contracts.

Owner-route resolution and activation reauthorize against current context. Authorization failures cannot be distinguished through timing-sensitive rich error details beyond existing protected contracts.

## 14. Failure and stale-state contract
Logical failures are: invalid_context, stale_context, invalid_handle, stale_handle, owner_unavailable, partial_population, source_unavailable, protected_or_not_found, unsupported_route.

The UI maps them to Human-readable recovery without exposing internal identifiers. Retry never replays a mutation because PATCH-057 logical operations are read/resolve/navigation only.

## 15. Accessibility, responsive and RTL contract
Core journeys must be keyboard-completable with visible focus, semantic landmarks/headings, programmatic labels, announced loading/error/status changes and no color-only meaning.

Responsive layouts preserve action meaning and context on narrow viewports. RTL mode mirrors directional layout where semantically appropriate without reversing engineering notation, tag names, identifiers or numeric technical content.

No core journey may depend on hover, pointer precision or raw backend identifiers.

## 16. AI contract
AI may explain an already-authorized slice, summarize limitations or propose a Human next step. AI output carries advisory/non-authoritative presentation and cannot alter product context, completeness, owner route, Health calculation, canonical state or Human acceptance/disposition.

AI is not required to complete any core Commercial V1 journey.

## 17. Performance and fan-out limits
Command Center composition must use bounded source fan-out and deterministic timeouts. One unavailable source produces its own unavailable/partial slice rather than blocking truthful independent slices.

IDS-057 must set concrete request budgets from repository/runtime evidence. EDS forbids unbounded per-row owner calls and unbounded client pagination to manufacture totals.

## 18. Logical operation inventory
Exactly three PATCH-057 logical read/resolve operations are introduced: product-context options, Command Center summary, and owner-route resolution.

Existing owner mutations are reused unchanged. Project/discipline navigation and package-aware onboarding consume these logical reads plus existing owner APIs; they do not add mutation operations.

## 19. Commercial V1 journey conformance
Minimum deterministic journey families are:
1. explicit Organization-authorized Project/Workspace selection;
2. integrated E/I/C navigation;
3. each supported single-discipline navigation;
4. package-aware onboarding and missing-prerequisite routing;
5. Command Center composition with complete and partial populations;
6. cross-discipline finding to owner workflow;
7. standards attention to owner workflow;
8. Evidence/retention attention to owner workflow;
9. PATCH-056 next action to owner workflow;
10. Report and Memory owner routing;
11. protected/cross-Organization non-disclosure;
12. stale handle/context recovery;
13. no-raw-ID core journey;
14. keyboard/screen-reader/responsive/RTL journey.

IDS-057 must expand these into exact vectors and map each to implementation tests. Qualification must include real-data Human journeys; placeholder-only UI does not pass.

## 20. Audit and observability
PATCH-057 read composition does not create engineering audit events merely because a dashboard was viewed. Existing owner audit remains authoritative for owner actions.

Operational telemetry may record minimized route kind, safe state codes, latency, source adapter result class and correlation identifiers. It must not log unrestricted composed payloads, hidden counts, protected content, secrets or AI prompts containing protected engineering data.

## 21. Explicit non-scope
No generic Wizard/BPM/task engine; duplicate canonical state; employee ranking/productivity scoring; fake totals; procurement; FAT/SAT/commissioning/closeout; autonomous mutation; authentication/session redesign; signed entitlements/seats; deployment certification; post-PATCH-060 ideas; or new canonical PATCH-057 persistence.

## 22. IDS-057 obligations
IDS-057 must inspect the actual route/component/API inventory and freeze exact frontend information architecture, source adapters, DTOs, pagination tokens, selector/route-handle representation, query/authorization order, bounded fan-out/timeouts, protected error mapping, component/module manifest and exact conformance vectors.

IDS must preserve the no-persistence decision unless a governance-reviewed architecture amendment occurs. No migration is expected under this EDS.

## 23. EDS self-review
Traceability: PASS against accepted Discovery, Architecture-057 and ADR-030.
Human Authority: PASS.
AI non-authority: PASS.
Organization isolation/anti-inference: PASS.
Canonical source-owner preservation: PASS.
PATCH-055/PATCH-056 dependency preservation: PASS.
No-raw-ID commercial journey: PASS.
Population completeness/pagination: PASS.
Owner routing/reauthorization: PASS.
Accessibility/responsive/RTL: PASS.
Persistence decision: PASS — no new PATCH-057 persistence.
PATCH-058/059/060 separation: PASS.

## 24. Governance disposition
EDS-057 candidate is **COMPLETE / READY FOR INDEPENDENT EDS REVIEW**.

Human EDS acceptance is not implied. IDS-057, Implementation Plan, implementation, migration, staging, commit, push, deployment and PATCH-058 remain unauthorized.

EDS-057: CANDIDATE / READY FOR INDEPENDENT EDS REVIEW

## 25. Human EDS Acceptance

- Human Engineering Design Authority decision: **PASS / ACCEPTED / COMPLETE**.
- Acceptance date: 2026-09-22.
- Accepted after Independent EDS Review returned **PASS / READY FOR HUMAN EDS ACCEPTANCE** with Critical/Major/Minor = 0/0/0.
- Product-context selection, safe population completeness/pagination, Human-readable selectors, owner-route reauthorization, bounded Command Center composition, package-aware onboarding, accessibility/RTL and the no-new-persistence decision are accepted.
- Existing canonical source owners and Human decision boundaries remain controlling; AI remains advisory and non-authoritative.
- This acceptance authorizes progression to IDS-057 preparation and independent review only.
- It does not authorize an Implementation Plan, implementation, migration, production-code changes, database mutation, staging, commit, push, deployment, PATCH-058 work, or canonical semantic changes.

EDS-057: HUMAN ACCEPTED / COMPLETE
