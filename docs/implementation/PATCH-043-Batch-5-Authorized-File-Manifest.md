# PATCH-043 Batch 5 Authorized File Manifest

## Authority and scope

Batch 4 is accepted. This manifest authorizes only S15–S16 bounded Supporting
Evidence UI using the accepted real APIs.

## Production boundary

CREATE:

- `frontend/src/components/SupportingEvidencePanel.tsx` — Project/Workspace
  upload, truthful lifecycle list, proposed-Evidence linkage and protected
  attachment actions; no authority or provenance construction.

MODIFY:

- `frontend/src/api/types.ts`, `frontend/src/api/client.ts` — exact closed
  Supporting File/Evidence-candidate DTOs, multipart upload, link and
  authenticated download calls only.
- `frontend/src/pages/ProjectsPage.tsx` — embed the panel in the current trusted
  Project/Workspace context.
- `frontend/src/pages/ReportPages.tsx` — select only server-composed Evidence
  provenance candidates and render accepted Evidence V2 file provenance with
  server-authorized historical download actions.
- `frontend/src/styles.css` — bounded responsive/accessibility styles only.

## Test boundary

CREATE `frontend/src/test/supporting-evidence.test.tsx`. MODIFY only focused
API/workflow/report/responsive tests when exact accepted behavior changes.

## Evidence and stop conditions

Evidence must prove real API calls, no fake Assets/counts, explicit labelled
file input, Human rationale, lifecycle/non-authority language, current proposed
Evidence selection, no client-authored canonical locator, protected/error/empty/
success states, keyboard/focus/live-region behavior, touch targets, long-name
wrapping and narrow layout without overflow. Stop for a global file manager,
inline unsafe rendering, client-derived Organization/internal IDs, fake data,
OCR/AI/search, new route, or any backend/design change.
