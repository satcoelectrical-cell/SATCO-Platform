# PATCH-048 Batch 4 Authorized File Manifest — Project Engineering Context UX

## Scope

Batch 4 exposes only the accepted real-data Project Engineering Context view
over the Batch 2 assembly and Batch 3 get-node/one-hop APIs. It adds no backend,
persistence, migration, mutation, AI, graph-editor, semantic-search or
PATCH-049 capability.

## Exact allow-list

| Path | State | Responsibility |
|---|---|---|
| `frontend/src/api/types.ts` | MODIFY | Closed Project Context section/node/edge/result/state/classification types. |
| `frontend/src/api/client.ts` | MODIFY | Typed assembly, get-node and bounded one-hop GET calls with protected result translation. |
| `frontend/src/components/ProjectEngineeringContextPanel.tsx` | CREATE | Ten-section real-data surface, truthful states, authority/temporal labels, continuation and bounded related-context navigation. |
| `frontend/src/pages/ProjectsPage.tsx` | MODIFY | Mount the context surface inside the authorized Project workspace and pass selected Workspace context. |
| `frontend/src/styles.css` | MODIFY | Direction-neutral responsive, focus-visible and status styling for the bounded surface. |
| `frontend/src/test/project-context.test.tsx` | CREATE | API/component state, accessibility, keyboard, continuation, related-node and no-fake-data evidence. |
| `frontend/src/test/api.test.ts` | MODIFY | Exact Project Context client paths/result handling and no raw-ID-body evidence. |
| `frontend/src/test/responsive.test.ts` | MODIFY | Direction-neutral stacking and narrow-layout evidence. |
| `frontend/src/test/workflows.test.tsx` | MODIFY | Preserve existing Project/Workspace/Capture workflow mocks after mounting the new read-only context surface. |

## Boundaries and evidence

The UI renders the canonical ten sections in server order and only data returned
by the API. Available, empty, not-established, not-disclosed, unavailable,
partial, truncated, loading, error and protected states are distinct. Visible
counts are displayed only when returned; no total/completeness inference exists.
Related navigation begins from a rendered typed selector, is one-hop only, has
no depth/arbitrary traversal, and offers only server continuation. It never asks
for a raw UUID or integer selector.

Evidence must prove semantic headings/landmarks/live states, keyboard controls,
focus visibility, responsive stacking, RTL-ready direction-neutral CSS, no fake
records/totals, no Human/private-storage fields, protected result silence, and
no graph editor, AI or PATCH-049 surface.

Independent manifest review: **PASS**. Critical: 0. Major: 0. Minor: 0. The
Nine-file boundary is the minimum coherent frontend/API/test surface and is
**ACCEPTED / COMPLETE** under standing Human governance authority.

## Append-only transport/evidence reconciliation

Implementation integration proved that the accepted section continuation could
not be exercised through the existing assembly route. The following two Batch
3-owned files are added narrowly to Batch 4 integration evidence:

| Path | State | Responsibility |
|---|---|---|
| `backend/app/api/v1/routers/project_context.py` | MODIFY | Add typed single-section page/continuation query parsing to the existing thin read route. |
| `backend/tests/test_project_context_api.py` | MODIFY | Prove the continuation remains section-bound and exposes no total/offset surface. |

This eleven-file reconciled boundary changes no domain, owner, authorization,
persistence or migration semantics. Focused independent manifest re-review:
**PASS**. Critical: 0. Major: 0. Minor: 0.
