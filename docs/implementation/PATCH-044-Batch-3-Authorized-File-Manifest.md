# PATCH-044 Batch 3 Authorized File Manifest

## Scope

Batch 3 — Thin API and bounded Project experience, S09–S12.

Backend CREATE:

- `backend/app/api/v1/routers/project_foundation.py` — eight authenticated thin
  routes and closed result serialization;
- `backend/tests/test_project_foundation_api.py` — route/auth/result evidence.

Backend MODIFY:

- `backend/app/main.py` — register router exactly once;
- `backend/tests/test_project_foundation_security.py` — transport injection and
  prohibited-route evidence.

Frontend CREATE:

- `frontend/src/components/ProjectFoundationPanel.tsx`;
- `frontend/src/test/project-foundation.test.tsx`.

Frontend MODIFY:

- `frontend/src/api/types.ts`;
- `frontend/src/api/client.ts`;
- `frontend/src/pages/ProjectsPage.tsx`;
- `frontend/src/styles.css`;
- `frontend/src/test/workflows.test.tsx` only for existing Project mock closure.

Router may parse, acquire request-scoped application, delegate once and
serialize. It may not import Session/repository/UoW/policy/foreign persistence.
UI may use selectors only, never raw Organization/actor/source-ID fields.

Evidence: all eight routes, auth/server context, protected discriminator only,
legacy/established UI, full foundation flow, current-source selectors,
readiness/Human transition, loading/error/protected/conflict, accessibility,
responsive and fake-data scan. Stop for contract change, new navigation,
router policy, client authority, fake data, Batch 4 or PATCH-045+ behavior.
