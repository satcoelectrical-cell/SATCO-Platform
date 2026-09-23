# IDS-057 — Commercial Product Experience & Engineering Command Center Completion

## 1. Control and authority
**Status:** CANDIDATE / READY FOR INDEPENDENT IDS REVIEW
**Date:** 2026-09-22

Authority: Human-accepted PATCH-057 Discovery, Architecture-057, ADR-030 and EDS-057. This IDS freezes implementation design only. It authorizes no Implementation Plan, production-code change, migration, staging, commit, push, deployment or PATCH-058 work.

## 2. Repository baseline and reuse
The current frontend already provides AppShell/React Router routes for dashboard, standards, Projects, Project workspace, Reports, Memory, Assistant, account and Organization administration. ProjectsPage already exposes authorized Project cards and ProjectWorkspacePage exposes existing domain panels/workspaces.

The current Command Center loader in frontend/src/dashboard/commandCenter.ts uses the first visible Project, first visible Workspace and fixed client slices. PATCH-057 replaces those product-context assumptions; it does not replace canonical owner services.

Backend owner routers already exist for Projects, Workspaces, discipline packages, cross-discipline intelligence, standards, Evidence/retention, engineering performance, Reports, Memory and related engineering owners.

## 3. No-persistence / no-migration implementation
PATCH-057 adds no model, table, column, Alembic revision or canonical repository. Alembic remains at the pre-PATCH-057 sole head.

Product context is held in URL/navigation state plus React presentation state and re-resolved against server-authorized data. Non-sensitive layout preferences may use existing browser preference mechanisms only.

## 4. Frontend information architecture
Existing top-level routes remain stable. The dashboard becomes the Engineering Command Center. /projects remains explicit Project selection. /projects/:projectId remains Project context and gains coherent section navigation rather than a new parallel route tree.

Project workspace section keys are presentation identifiers only: overview, disciplines, cross-discipline, standards, evidence, performance, reports-memory. A selected Workspace is represented through an authorized selector and URL/query presentation state where needed; canonical UUIDs may exist in transport but are never typed by the Human.

Discipline destinations are generated from effective package configuration and authorized Workspace applicability. Unsupported or unauthorized destinations are not synthesized.

## 5. Product context implementation
Introduce a frontend ProductContextController responsible for explicit Project/Workspace selection, parent-child clearing, deep-link resolution and stale recovery. It consumes server-authorized options and never treats array position as authority.

No global browser-stored canonical selection is introduced. A deep-linked projectId/workspace handle is validated through owner reads before the ready state is rendered.

## 6. Backend composition topology
Add a bounded read-only product_experience router/service layer under the existing v1 API topology only if implementation inspection confirms existing endpoints cannot satisfy EDS-057 safely.

Logical operations map to:
- product-context options;
- Command Center summary;
- owner-route resolution.

The service composes existing owner application/dependency seams and returns presentation DTOs. It owns no repositories/UoW for canonical mutation. Source authorization occurs before inclusion in each slice.

## 7. DTO contract
ProductContextOptionsResponse contains safe Project options, selected-context validation outcome, Workspace options scoped to an authorized Project, effective package/navigation descriptors, and population metadata.

CommandCenterSummaryResponse contains independently stateful slices for context, packages, cross-discipline, standards, Evidence/retention, engineering performance/Health/actions, Reports and Memory. Each slice carries state and completeness; payload is absent when protected/unavailable.

OwnerRouteResolutionResponse contains route_kind, safe label, destination template/key, opaque target reference where required, parent context and stale/current result. It contains no mutation command.

Exact field spelling may follow existing schema conventions during implementation, but semantics and closed states from EDS-057 may not change.

## 8. Completeness and pagination
Reuse source-owner pagination metadata where trustworthy and authorization-safe. Where a source cannot prove total completeness, adapter output is partial or indeterminate; the frontend must not infer a total from items.length.

Continuation tokens remain opaque and are passed only to the source/composition endpoint that issued them. No client loop may exhaust pages merely to manufacture dashboard totals.

## 9. Selector and no-raw-ID implementation
Create reusable authorized selector presentation for Project, Workspace, engineering Object/Context/Evidence/Deliverable and standards resources where core PATCH-057 journeys currently require manual internal IDs.

Selectors show Human-readable canonical labels plus bounded context. Submitted transport IDs come from selected authorized records, not free-text UUID fields. Existing owner APIs remain the mutation destination.

Compatibility-profile selection must use trusted compatible-profile descriptors rather than manual profile ID entry in the normal commercial journey.

## 10. Owner-route registry
Implement a closed frontend/server route registry derived from actual owner surfaces. Initial route families are project_context, discipline_workspace, cross_discipline_finding, standards, evidence_workbench, retention, engineering_performance_source, technical_report and organizational_memory.

The registry maps safe route kinds to existing UI destinations. Unknown route kinds fail closed as unsupported_route. Route resolution never calls a mutation endpoint.

PATCH-056 action_key/source handles are translated only through an explicit adapter mapping; free-form AI text never selects a route.

## 11. Command Center source adapters
The Command Center composition adapter set is bounded to: Projects/context, effective packages, PATCH-053 cross-discipline, PATCH-054 standards, PATCH-055 Evidence/retention, PATCH-056 performance/Health/actions, Technical Reports and Organizational Memory.

Adapters expose normalized state/completeness plus minimal presentation data. They do not reinterpret canonical lifecycle values. One adapter timeout/failure yields its slice state and does not erase successful independent slices.

## 12. Project workspace composition
Refactor ProjectsPage/ProjectWorkspacePage presentation into navigable sections while reusing existing domain panels. No panel gains authority from its new location.

Electrical and Instrumentation journeys reuse canonical owner selectors/actions to close current frontend gaps. Control & Automation raw-ID forms are replaced in core journeys by selectors while preserving owner command contracts.

Cross-discipline informational/placeholder components must be connected only to already-authorized PATCH-053 reads/actions; placeholder data cannot satisfy qualification.

## 13. Package-aware onboarding
Compose existing onboarding, Project package configuration and Workspace owner flows. The PATCH-057 surface diagnoses needs_project_configuration or needs_workspace and routes the Human to the owner surface.

It does not auto-enable packages, create Workspaces or change applicability. Integrated E/I/C and each supported single-discipline configuration are tested separately.

## 14. Authorization order
For every composed request: authenticate/current Organization -> authorize Project -> authorize optional Workspace -> resolve effective package/applicability where needed -> invoke each source-owner authorized read -> normalize safe projection -> return.

Owner-route activation repeats current Organization/Project/Workspace and target authorization. Client-supplied Organization identity is ignored/rejected according to existing conventions.

## 15. Protected and stale outcomes
Map source outcomes to EDS states without revealing whether a protected target exists. protected_or_not_found uses the existing neutral owner contract.

Stale Project/Workspace selection clears dependent UI and requests Human reselection. Stale action targets do not execute; they may show a safe historical/read-only destination only if the canonical owner supports it.

## 16. Frontend component manifest
Expected PATCH-057 frontend implementation boundary:
- frontend/src/App.tsx — preserve route shell; add only required stable navigation composition;
- frontend/src/components/AppShell.tsx — integrated navigation presentation;
- frontend/src/dashboard/commandCenter.ts — replace first-visible/fixed-slice assumptions;
- frontend/src/pages/ProjectsPage.tsx — explicit context and section navigation;
- new bounded product-experience context/selector/route components under frontend/src/components or frontend/src/productExperience;
- existing CrossDisciplineIntelligencePanel, standards panels, EvidenceWorkbench and EngineeringPerformancePanel reused rather than duplicated;
- frontend/src/api/client.ts and frontend/src/api/types.ts for safe read DTOs;
- focused tests under frontend/src/test.

Exact new filenames may be finalized by the Implementation Plan, but no new product framework or parallel application shell is permitted.

## 17. Backend implementation manifest
Expected backend boundary, only where existing owner APIs are insufficient:
- backend/app/api/v1/routers/product_experience.py;
- backend/app/services/product_experience.py or repository-consistent equivalent;
- backend/app/schemas/product_experience.py;
- existing router registration file;
- focused backend tests.

No PATCH-057 model/repository/migration file is permitted under the accepted no-persistence design. Existing owner services/repositories are reused and remain authoritative.

## 18. Transactions and concurrency
PATCH-057 composition operations are read-only and create no multi-owner transaction. Each owner read uses its existing transaction/authorization semantics.

Route resolution may carry source version/state tokens for stale detection but mutation concurrency remains the owner command's responsibility.

## 19. Performance budgets
Implementation Plan must establish repository-backed numeric budgets before qualification. Design constraints are: bounded parallel adapter fan-out; no N+1 per displayed row; no unbounded page exhaustion; per-slice timeout/failure isolation; cancellation of obsolete context requests where frontend infrastructure supports it.

Performance optimization may not weaken authorization or completeness semantics.

## 20. Accessibility / RTL implementation
Section navigation uses semantic nav/landmarks and keyboard-reachable controls. Selectors have labels, descriptions and announced loading/error/empty states. Focus moves predictably after context changes and stale recovery.

RTL layout follows existing application directionality. Engineering tags, IDs, units and technical notation retain appropriate LTR/bidi isolation inside RTL UI.

## 21. Observability
Composition telemetry records correlation, route kind, slice state, completeness class and latency only as needed. No unrestricted payload, hidden total, protected resource identity, secret or AI prompt is logged.

Existing canonical owner audit/outbox remains unchanged because viewing/routing is not an engineering mutation.

## 22. Test and conformance map
Implementation must provide focused vectors for all 14 EDS journey families. Minimum security regressions include cross-Organization Project/Workspace handles, protected route targets, hidden population counts and package/data-authority separation.

Frontend tests cover explicit selection, no first-visible authority, partial/indeterminate populations, stale recovery, owner routing, integrated E/I/C, each supported single-discipline mode, no-raw-ID core paths, keyboard/accessibility, responsive and RTL.

Backend tests, if the composition API is added, cover authorization order, slice isolation, safe completeness, route resolution and zero mutation side effects.

## 23. Implementation batching direction
Implementation Plan should use bounded batches:
1. product-context/completeness contracts and selectors;
2. Command Center server/read composition and frontend integration;
3. Project/discipline navigation and package-aware onboarding;
4. owner routing plus raw-ID journey removal across domains;
5. integrated accessibility/RTL/security/regression qualification.

Batch boundaries may be refined without changing accepted semantics.

## 24. Stop boundary
STOP for any required canonical semantic change, new persistence/migration need, cross-Organization disclosure risk, need to weaken an owner authorization contract, need to reopen PATCH-053/054/055/056 accepted semantics, or scope that belongs to PATCH-058+.

Any such condition returns to governance before implementation.

## 25. IDS self-review
Traceability to EDS-057: PASS.
No persistence/migration: PASS.
Existing route/owner reuse: PASS.
Canonical ownership/Human Authority: PASS.
Organization isolation/anti-inference: PASS.
No first-visible authority: PASS.
No-raw-ID core journey: PASS.
PATCH-055/PATCH-056 composition: PASS.
Accessibility/responsive/RTL: PASS.
PATCH-058/059/060 separation: PASS.

## 26. Governance disposition
IDS-057 candidate is **COMPLETE / READY FOR INDEPENDENT IDS REVIEW**.

Human IDS acceptance is not implied. Implementation Plan, implementation, migration, staging, commit, push, deployment and PATCH-058 remain unauthorized.

IDS-057: CANDIDATE / READY FOR INDEPENDENT IDS REVIEW

## 27. Human IDS Acceptance

- Human Implementation Design Authority decision: **PASS / ACCEPTED / COMPLETE**.
- Acceptance date: 2026-09-22.
- Accepted after Independent IDS Review returned **PASS / READY FOR HUMAN IDS ACCEPTANCE** with Critical/Major/Minor = 0/0/0.
- The repository-aligned product-context, bounded composition, selector, owner-routing, frontend information architecture, authorization order, test boundaries and no-persistence/no-migration implementation design are accepted.
- Existing canonical source owners and Human decision boundaries remain controlling; AI remains advisory and non-authoritative.
- This acceptance authorizes progression to PATCH-057 Implementation Plan preparation and independent review only.
- It does not authorize production-code implementation, migration, database mutation, staging, commit, push, deployment, PATCH-058 work, or canonical semantic changes.

IDS-057: HUMAN ACCEPTED / COMPLETE
