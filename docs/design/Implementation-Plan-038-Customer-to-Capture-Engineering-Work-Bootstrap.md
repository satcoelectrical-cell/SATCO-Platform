# Implementation-Plan-038 — Customer-to-Capture Engineering Work Bootstrap

Status: **ACCEPTED / EXECUTABLE** after Independent Review and standing Human
Plan Acceptance. Implementation occurs only through exact batch manifests.

## Batch 1 — Customer Tenancy and Project Integrity

- S01: additive `e03800000001` Customer Organization migration, approved exact
  inventory, FK/index, immutability and Project/Customer DB guards, role/grant
  preservation, downgrade/re-upgrade.
- S02: scoped Customer model/schema/repository/service/router with atomic Audit,
  deterministic selector, protected outcomes and guarded compatibility delete.
- S03: Project create/update same-Organization Customer validation.

Evidence: migration/head, exact mapping/drift, direct SQL, runtime role,
Customer security/API, Project invariant, adjacent migration/Project tests.
Stop for any mapping contradiction, inferred ownership, cascade deletion,
client Organization authority, or accepted-contract change.

## Batch 2 — Customer and Project Initiation UI

- S04: typed Customer list/create/update and Project create/update API adapters.
- S05: actionable Customer/Project empty-state and initiation flow on Projects,
  canonical response/refetch, protected/error states, accessibility/responsive.

Evidence: API serialization, no Organization field, form validation,
Customer→Project positive/protected flows, keyboard/focus/responsive, no fake
data. Stop for broad CRM, raw authority fields, or new Project semantics.

## Batch 3 — Workspace, Capture, and Contextual AI Continuation

- S06: Workspace create/select inside Project detail.
- S07: Capture create/display inside selected Workspace.
- S08: contextual Assistant handoff, independent PATCH-035 reauthorization,
  return to Project/Command Center, no raw-ID normal flow.

Evidence: complete bootstrap journey, foreign hierarchy denial, accepted field
bounds, advisory separation, context tamper, navigation, accessibility and
responsive tests. Stop for Workspace administration, Capture correction,
AI persistence/authority, or backend contract redesign.

## Batch 4 — Integration and Final Evidence

- S09: focused backend/frontend, migration, security, adjacent and full
  regressions; frontend typecheck/build/static; exact scope/secrets/prohibited
  patterns; `git diff --check`; QG-M1 traceability.
- S10: reproducible validation evidence and final review readiness records.

No production/test remediation belongs to Batch 4 without a separately
recorded focused finding and bounded reconciliation.

## Dependency Order

Batch 1 → Batch 2 → Batch 3 → Batch 4. Each batch requires independent review
and standing Human acceptance before the next begins. Deferred EDS scope never
becomes a task.
