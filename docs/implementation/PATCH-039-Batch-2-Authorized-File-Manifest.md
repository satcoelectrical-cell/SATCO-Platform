# PATCH-039 Batch 2 Authorized File Manifest

Batch: Report Creation, Authoring, and Revision (S03–S05). Preparation,
manifest acceptance, and implementation authority are granted under standing
Human authority.

## Exact Authorized Boundary

- MODIFY `frontend/src/api/types.ts` — strict Report candidate/detail types.
- MODIFY `frontend/src/api/client.ts` — existing Report calls plus candidate read.
- CREATE `frontend/src/pages/ReportPages.tsx` — authorized contextual list,
  creation, detail, and revision experience.
- MODIFY `frontend/src/pages/KnowledgePages.tsx` — remove the superseded
  manual-ID-only Report surface while preserving Journal and Memory.
- MODIFY `frontend/src/App.tsx` — exact Reports list/detail routes.
- MODIFY `frontend/src/pages/ProjectsPage.tsx` — contextual Capture→Report link.
- MODIFY `frontend/src/dashboard/commandCenter.ts` — preserve closed source
  state typing after explicit Report conflict support.
- MODIFY `frontend/src/styles.css` — bounded responsive authoring/detail styles.
- CREATE `frontend/src/test/reports.test.tsx` — authoring/revision/security UX.
- MODIFY `frontend/src/test/workflows.test.tsx` — preserve prior workflow and
  replace obsolete manual-ID Report evidence.
- MODIFY `frontend/src/test/dashboard.test.tsx` — maintain exact Report summary
  fixture parity after the accepted frontend type closure.

No backend mutation, migration, persistence, acceptance implementation,
Command Center change, AI, Memory, broad provenance, or Batch 3+ behavior is
authorized. Acceptance requires no manual IDs, server-composed provenance,
explicit revision rationale, stale conflict state, labels/live feedback,
responsive layout, real API data, frontend focused/regression tests,
typecheck/build, scope checks, and `git diff --check`.
