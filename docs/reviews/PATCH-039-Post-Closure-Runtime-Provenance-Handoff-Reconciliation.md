# PATCH-039 Post-Closure Runtime Provenance Handoff Reconciliation

Status: **PASS / DELIVERED / CLOSED**.

This append-only record does not alter PATCH-039's original `DONE / CLOSED`
history, delivery `80d006e5232e154502a36baf46b9b40be7c3504c`, or governance closure
`af4e86f6b62a2aad45a8a1956313b4474d9a7e5b`.

## Human reproduction and persisted evidence

On 2026-08-20, Human browser validation followed Project
`SAT-PRJ-2026-0007` (`project_id=11`) to Electrical Engineering Workspace
`workspace_id=1`, created captured observation
`1d1b2b20-4ce2-4568-821b-1f935d92eaa2`, and selected its contextual Create
report action. Project and Workspace initialized correctly, but Capture
provenance showed a neutral error and zero attached server-authorized sources.

Read-only database inspection confirmed the Capture is `captured`, version 1,
and its Organization/Project/Workspace are
`7e7c9d7a-7693-4f75-9bc5-3ef7bf528281` / `11` / `1`. Project 11 belongs to
that Organization, Workspace 1 belongs to Project 11, and creator/current User
1 has one enabled selected membership in that active Organization. No row was
edited.

## Root cause and remediation

The frontend produced the accepted URL
`/reports?project_id=11&workspace_id=1&capture_id=1d1b2b20-4ce2-4568-821b-1f935d92eaa2`
and requested
`GET /technical-reports/capture-source-candidates?project_id=11&workspace_id=1&page=1&size=20`.
The live response was payload-protected `422 TECHNICAL_REPORT_VALIDATION_ERROR`.
The live backend OpenAPI did not contain the delivered static candidate route,
although the checked-in/bind-mounted source did. The stale process therefore
routed `capture-source-candidates` through `/{report_id}` UUID validation.

Classification: **stale runtime/build process**. This was not a frontend
handoff, data-integrity, authorization, API-contract, or source-composition
defect. The delivered adapter independently succeeded against the exact real
Capture row.

The bounded remediation restarted only `satco-backend`, loading the already-
delivered route. Live OpenAPI then included the candidate endpoint and the
same authenticated request returned HTTP 200 with exactly the real Capture,
server-composed canonical provenance, and coherent integrity digest. No
database, backend production, frontend production, architecture, or accepted
authority semantics changed.

## Validation and independent re-review

Validation after the bounded remediation:

- live backend OpenAPI route presence: PASS;
- authenticated live candidate request for Project 11 / Workspace 1: HTTP 200,
  one exact Capture, server-composed provenance, coherent SHA-256 digest;
- focused/adjacent Technical Report and Capture backend: **185 passed**;
- focused contextual frontend subset: **14 passed**;
- full frontend: **47 passed** across 9 files;
- frontend typecheck/build: PASS; 1,815 modules transformed;
- changed backend import/compile: PASS;
- `git diff --check`: PASS.

Independent re-review: **PASS** for root-cause resolution, accepted authority,
exact Organization/Project/Workspace/Capture intersection, static-route
precedence, contextual navigation, generic Report entry preservation,
protected denial, no raw-ID UI, no foreign persistence access, no production
fake data, and historical preservation. Critical: 0; Major: 0; Minor: 0.

No production file changed. The test-only additions use fixed synthetic
contract identifiers except for the Human-reproduced Capture identifier in the
route-precedence evidence; production code contains neither that identifier
nor its content. Original validation accurately recorded that live browser
rendering was unavailable; this later Human-discovered runtime failure is not
rewritten.

## Delivery and closure

### Human runtime revalidation — PASS

The Human revalidated the remediated workflow in Safari after rebuilding and
restarting the current backend:

`Projects → AUDIT FINAL DELETE TEST → Recent Captures → observation → Create report`.

The rendered Report page preserved Project `SAT-PRJ-2026-0007 — AUDIT FINAL
DELETE TEST` and `Electrical Engineering Workspace`; rendered the actual
authorized `observation` Capture and its content as `Version 1 · verified
canonical Capture`; stated `1 server-authorized Capture source attached.
Canonical provenance cannot be edited here.`; and enabled `Create Human-authored
draft`. No Capture UUID, Project ID, Workspace ID, Organization ID, or
canonical provenance payload required manual entry.

Human Runtime Revalidation: **PASS**. The existing Independent Re-review PASS
remains valid with this runtime evidence. The exact manifest remains unchanged.
Focused/adjacent tests, build/type/static, authorization/non-disclosure,
fake-production-data, scope, and diff-integrity results remain PASS.

Bounded remediation/evidence delivery is authorized. The separate append-only
closure entry will record its commit and remote verification without changing
the original PATCH-039 `DONE / CLOSED` history.

### Append-only reconciliation closure

Human Runtime Revalidation, Independent Re-review, focused and adjacent
validation, build/type/static, authorization/non-disclosure, fake-production-
data, exact scope, and delivery-boundary checks are PASS. The bounded five-file
remediation/evidence commit is
`1135ba11024dd76ca0bd542ba495dc125ac74392`; push and remote verification are
PASS with divergence 0/0. Unauthorized committed files: none. Original
PATCH-039 delivery and closure remain immutable, unrelated local work remains
unstaged, deferred boundaries remain preserved, and PATCH-040 is not begun or
authorized.
