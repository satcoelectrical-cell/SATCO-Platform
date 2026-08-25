# PATCH-047 Batch 4 — Authorized File Manifest

## Authority and scope

Batch 4 implements only the accepted Transport/UI step in
Implementation-Plan-047. Batches 1–3 are accepted and unchanged. No migration,
model, foreign persistence access, AI, PATCH-048, final validation, delivery or
closure work is authorized.

## Exact authorized boundary

| Path | Action | Batch 4 responsibility | Prohibited responsibility |
|---|---|---|---|
| `backend/app/schemas/project_control.py` | MODIFY | Closed bounded list/history read DTOs and result unions. | New domain semantics or transport-only authority. |
| `backend/app/repositories/project_control_repository.py` | MODIFY | Scoped, deterministic no-commit current/history queries. | Foreign reads or commits. |
| `backend/app/services/project_control_service.py` | MODIFY | Authorized read composition and existing command delegation only. | New lifecycle/authority or direct canonical persistence. |
| `backend/app/dependencies/project_control.py` | CREATE | Request-scoped Project Control composition, trusted actor/Organization and canonical target services. | Router policy or client-derived authority. |
| `backend/app/api/v1/routers/project_controls.py` | CREATE | Thin authenticated Project Control routes and closed-result translation. | ORM/Session/repository/UoW construction or domain policy. |
| `backend/app/main.py` | MODIFY | Register this router once. | Unrelated application behavior. |
| `backend/tests/test_project_control_service.py` | MODIFY | Read/history behavior and closed result evidence. | Broad regression. |
| `backend/tests/test_project_control_security.py` | MODIFY | Protected read/link non-disclosure evidence. | UI/API implementation. |
| `backend/tests/test_project_control_api.py` | CREATE | Transport, authentication, scope and payload-free-outcome evidence. | Full backend regression. |
| `frontend/src/api/types.ts` | MODIFY | Closed Project Control presentation contracts. | Authority-bearing client contracts. |
| `frontend/src/api/client.ts` | MODIFY | API calls and client-only closed-result translation. | Authorization or target resolution. |
| `frontend/src/components/ProjectControlsPanel.tsx` | CREATE | Accessible, responsive Project-level Risk/Issue/Decision/Change/Impact panel. | Fake data, AI, generic ticketing or client authority. |
| `frontend/src/pages/ProjectsPage.tsx` | MODIFY | Place the panel in existing trusted Project context. | New route or unrelated workspace workflow. |
| `frontend/src/styles.css` | MODIFY | Component-local responsive and RTL-safe structural styles. | Dashboard redesign. |
| `frontend/src/test/project-controls.test.tsx` | CREATE | Focused real-data, status, authority, protected/error and accessibility UI evidence. | Broad frontend suite. |
| `docs/implementation/PATCH-047-Batch-4-Authorized-File-Manifest.md` | CREATE | This boundary. | Implementation acceptance. |
| `docs/reviews/PATCH-047-Batch-4-Manifest-Review.md` | CREATE | Independent manifest review. | Implementation acceptance. |
| `docs/reviews/PATCH-047-Batch-4-Implementation-Review.md` | CREATE | Independent implementation/re-review chronology. | Final review. |
| `docs/reviews/PATCH-047-Batch-4-Human-Acceptance.md` | CREATE | Human Batch 4 acceptance after zero Critical/Major. | Batch 5 authority. |
| `docs/patches/PATCH-047.md` | MODIFY | Record Batch 4 status only after acceptance. | Delivery or closure. |

## Dependencies and evidence

The authoritative migration remains `e04700000001`; it is not modified.
The API obtains its actor and Organization only through the established request
composition pattern. Canonical target reauthorization remains inside the
Project Control service/adapter. The frontend consumes closed responses only
and never receives a generic target UUID entry field.

Focused evidence must cover Project-scoped list/detail/history, all five fact
classes, the potential/confirmed Impact distinction, payload-free protected,
invalid and unavailable outcomes, cross-Organization and cross-Project denial,
unsupported target rejection, no target mutation, and API delegation. Frontend
evidence must cover truthful loading/empty/protected/error states, explicit
Human authority wording, keyboard-label semantics, responsive structural
classes, and absence of fake data, AI and Foundation targets. The only adjacent
backend regression is the bounded existing Project Control and canonical target
subset; the only frontend validation is the focused component test plus
typecheck/build.

## Stop conditions and scope control

Stop for an accepted-contract change; any router-owned Session, repository,
UoW, policy or canonical persistence access; client-derived actor/Organization;
target disclosure before service reauthorization; a new migration/model;
Foundation target behavior; generic ticketing; AI; PATCH-048; a new dashboard
or unrelated route; unbounded reads; or an out-of-boundary file. Batch 5/final
validation, QG-11, QG-12, delivery and closure remain explicitly excluded.
