# PATCH-038 Batch 2 Authorized File Manifest

Batch: Customer and Project Initiation UI — S04–S05.

Authorized files:

- MODIFY `frontend/src/api/types.ts`
- MODIFY `frontend/src/api/client.ts`
- MODIFY `frontend/src/pages/ProjectsPage.tsx`
- MODIFY `frontend/src/styles.css`
- MODIFY `frontend/src/test/api.test.ts`
- MODIFY `frontend/src/test/workflows.test.tsx`

Only typed Customer list/create/update, Project create, actionable initiation,
canonical refetch/result states, accessibility and responsive behavior are
allowed. No Workspace/Capture/AI implementation, broad CRM, Organization
administration, backend change, fake data, or deferred capability.

Acceptance requires focused UI/API/workflow/security/accessibility/responsive
tests, frontend typecheck/build, Batch 1 regression, prohibited patterns and
`git diff --check`.
