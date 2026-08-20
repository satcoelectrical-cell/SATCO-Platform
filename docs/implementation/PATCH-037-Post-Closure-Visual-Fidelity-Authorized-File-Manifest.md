# PATCH-037 Post-Closure Visual Fidelity Authorized File Manifest

## Authority

Human authority is granted only for the presentation-only reconciliation
recorded in `docs/reviews/PATCH-037-Post-Closure-Visual-Fidelity-Reconciliation.md`.
PATCH-038 remains unregistered and unauthorized.

## Exact Authorized Boundary

| Action | File | Purpose | Prohibited responsibility |
|---|---|---|---|
| MODIFY | `frontend/src/pages/DashboardPage.tsx` | Give the existing five registered widgets semantic desktop composition regions while preserving their data/result contracts and customization controls. | New reads, data derivation, widget IDs, routes, authority, or domain semantics. |
| MODIFY | `frontend/src/styles.css` | Implement responsive full-width command-center proportions, first-viewport primary surfaces, AI rail, density, and accessible collapse. | Fake content, charts, analytics, notifications, or unsupported interaction. |
| MODIFY | `frontend/src/test/dashboard.test.tsx` | Prove truthful composition, region ordering, intentional empty states, and customization preservation. | Production fixture/data changes. |
| MODIFY | `frontend/src/test/responsive.test.ts` | Prove desktop rail and bounded responsive collapse without page overflow. | Browser-only evidence substitution. |
| CREATE | `docs/reviews/PATCH-037-Post-Closure-Visual-Fidelity-Reconciliation.md` | Preserve the accepted post-closure finding and authority without rewriting historical closure. | Rewriting earlier reviews. |
| CREATE | `docs/implementation/PATCH-037-Post-Closure-Visual-Fidelity-Authorized-File-Manifest.md` | Define this exact remediation boundary and validation gates. | Broader PATCH authority. |

`frontend/src/dashboard/layout.ts` and `frontend/src/components/AppShell.tsx`
are explicitly not authorized: the accepted widget registry, device-local
layout schema, and existing trusted command context are sufficient.

## Required Evidence

- focused dashboard and responsive tests, including customization recovery;
- typecheck and production build;
- no-fake-data / exact-scope / protected-disclosure checks;
- actual browser captures at 1920px, 1440px, and a narrower responsive width;
- independent visual/product re-review against the accepted reconciliation;
- `git diff --check` and exact allow-list review.

## Stop Conditions

Stop for any need for a backend change, new API read, widget-schema change,
client-derived authority, fake data, deferred capability, out-of-boundary file,
or unavailable actual visual evidence before delivery.
