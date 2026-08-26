# PATCH-049 Batch 3 — Authorized File Manifest

## Governance and purpose

PATCH-049 Batches 1 and 2 are **ACCEPTED / COMPLETE**. Batch 3 is frontend
presentation and final focused frontend evidence only. This manifest grants no
implementation authority.

Batch 3 exposes the real read-only Batch 2 endpoint in the existing Project
Workspace. It neither changes backend capability nor recreates Project Context,
authorization, completeness classification, or the deterministic rule engine.

## Exact future implementation allow-list

| Path | Action | Sole responsibility | Prohibited responsibility |
|---|---|---|---|
| frontend/src/api/types.ts | MODIFY | Closed Project Completeness DTO/string-union types matching the server result exactly. | Client rule evaluation, score, hidden fields, identity/provenance expansion. |
| frontend/src/api/client.ts | MODIFY | One closed-status GET /projects/{project_id}/completeness call with optional workspace identifier. | Fake data, Organization input, graph/AI/options, retries that alter semantics. |
| frontend/src/components/ProjectCompletenessPanel.tsx | CREATE | Accessible read-only completeness panel with loading, result and safe closed-outcome rendering. | Mutation, task/checklist persistence, score, AI/chat, recommendation, frontend inference. |
| frontend/src/pages/ProjectsPage.tsx | MODIFY | Place the panel before Project Engineering Context in Project Workspace and supply current Project/Workspace scope. | Workspace/project ownership or authorization changes. |
| frontend/src/styles.css | MODIFY | Scoped responsive, direction-neutral completeness styles, safe text wrapping and focus treatment. | Whole-frontend redesign or unrelated style rewrite. |
| frontend/src/test/project-completeness.test.tsx | CREATE | Focused API-contract, state, non-disclosure, accessibility and responsive-class evidence. | Broad unrelated frontend regression. |

All four MODIFY paths are currently free of unrelated dirty hunks; both CREATE
paths are absent. No other frontend, backend, production, test, configuration,
persistence or migration file is authorized.

## Required product-state and security closure

The panel must issue the real API call on mount, explicit refresh, and
Project/Workspace scope change. It must preserve these states: loading,
available, no-applicable-rules, no-actionable-gaps, missing, indeterminate,
not-disclosed, partial, unavailable and truncated.

It renders the server’s five classifications exactly: PRESENT, MISSING,
INDETERMINATE, NOT_DISCLOSED and NOT_APPLICABLE. It may render only already
disclosed title/description, safe evidence, deterministic question/checklist,
observation/partiality, limitations, truncation and derived/advisory/
non-authoritative status. NOT_DISCLOSED is textually and visually distinct from
MISSING. Protected and unavailable states expose no existence, count, source,
Human identity, private-storage, provenance or exception details.

No completeness/health/progress percentage, traffic-light rating, ranking,
confidence score, AI/chat/prompt/provider UI, engineering recommendation,
solution, material/BOM/vendor/optimization direction, create/update/delete,
approval, task, workflow, assignee, due-date or checklist-completion control is
authorized. The client must not fabricate production results, infer missingness,
duplicate the evaluator or reconstruct inaccessible evidence.

## Accessibility, responsiveness and bounds

The panel/test must provide semantic headings and lists, keyboard-operable safe
links/disclosures where present, non-color status text, accessible loading/error
states, visible focus and polite safe status. It uses existing responsive and
CSS logical-property conventions: desktop and narrow layouts must remain
readable, bounded safe text must wrap, and structure remains RTL-ready.

The client honors existing server bounds (14 findings/questions/checklist items,
56 evidence references and 131,072-byte response); it adds no pagination or
hidden totals.

## Focused evidence and read-only adjacency

Focused implementation evidence is only:

- frontend/src/test/project-completeness.test.tsx

It must prove the real API call; successful rendering; five classifications;
no-applicable/no-actionable/partial/truncated; protected and unavailable
outcomes; safe evidence/question/checklist; derived/advisory labels; no score,
AI or mutation controls; Workspace placement; accessible semantics; and
responsive/direction-neutral class behavior.

Read-only adjacent regressions, never modification surfaces:

- frontend/src/test/api.test.ts
- frontend/src/test/project-context.test.tsx
- the smallest Project Workspace subset already exercised through ProjectsPage
  imports in project-completeness.test.tsx

## Boundaries, collision and authority

AI calls = 0. EKG calls = 0. Mutation = 0. Persistence/migration = 0; expected
Alembic head remains e04700000001. No backend production/test modification is
needed. Stop if any new backend contract, owner authorization, persistence,
migration, AI/graph, score, recommendation, fake data, PATCH-050 capability or
file outside this list is required.

This manifest is **ACCEPTED / COMPLETE** after separately recorded Independent
Manifest Review PASS. Batch 3 is eligible for separate Human implementation
authority only; it grants no implementation, delivery, closure or PATCH-050
authority.

## Append-only final-validation reconciliation

Final frontend validation discovered B3-049-MAJ-02: the existing Project
Workspace workflow regression mock omitted the accepted `api.projectCompleteness`
member, although `ProjectWorkspacePage` correctly mounts the accepted panel.
The manifest is reconciled to authorize exactly one additional **MODIFY** path:

| Path | Action | Sole responsibility | Prohibited responsibility |
|---|---|---|---|
| `frontend/src/test/workflows.test.tsx` | MODIFY | Add a contract-faithful closed `projectCompleteness` client mock to preserve real Project Workspace integration coverage. | Production behavior, panel bypass, assertions weakening, fake behavior, score, AI, EKG, task/workflow capability. |

The reconciled Batch 3 boundary is seven files. No other production/test path,
backend path, migration, persistence, AI, EKG or PATCH-050 capability is
authorized.
