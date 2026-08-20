# IDS-039 — Technical Report Authoring & Human Acceptance Experience

## 1. Status

Status: **ACCEPTED / COMPLETE** after Independent IDS Review PASS and standing
Human acceptance. Implementation Plan authority is granted. ADR-023,
PATCH-032, Architecture-039, and EDS-039 remain authoritative.

## 2. Reused Canonical Operations

PATCH-039 reuses without semantic change:

- `GET /technical-reports`, `GET /technical-reports/{report_id}`;
- `POST /technical-reports`;
- `POST /technical-reports/{report_id}/draft-revisions`;
- `POST /technical-reports/{report_id}/acceptance`.

Existing strict PATCH-032 request/detail/summary/provenance schemas are the
contract. Mutation calls carry fresh UUID `X-Correlation-ID` and
`Idempotency-Key`. HTTP 401/403/404 map to protected, 400/422 invalid, 409
conflict, and 503/network unavailable; protected/invalid presentation contains
no backend message or identity.

## 3. Capture Source Candidate Contract

Add one authenticated read:

`GET /technical-reports/capture-source-candidates?project_id={positive int}&workspace_id={positive int}&page={1+}&size={1..20}`

Success is `TechnicalReportCaptureSourceCandidateList { items, total, page,
size }`, where `total >= 0` is the authorized canonical Capture total in the
exact scope. Each item is:

`{ capture_id: UUID, project_id: int, workspace_id: int, source_kind,
version: positive int, created_at: datetime, preview: str[1..240], provenance:
TechnicalReportProvenanceSchema }`.

Only current `captured` Captures are eligible. Ordering equals canonical
Capture list ordering. Size is at most 20 and the adapter makes one bounded
canonical list call; it must not query Capture persistence directly.

Provenance is exact:

- deterministic UUIDv5 entry identity bound to Capture identity/version;
- ordinal `0`;
- `canonical_material`, `universal_capture`, `is_material=true`;
- owning capability `universal_capture`;
- fixed `reliance_role="source_capture"`;
- `verified`, `available`;
- bounded origin attribution `Universal Engineering Capture`;
- empty limitations;
- exact `CaptureHistoricalBasisV1` projection, including trusted Organization;
- `sha256` and digest from PATCH-032 canonical historical serialization.

The adapter accepts only the canonical Capture application service response,
checks exact Project/Workspace and lifecycle again, and fails protected before
returning partial items. No direct Capture repository/ORM/Session/UoW access.

## 4. Frontend Routes and State

- `/reports` resolves authorized Project and Workspace selectors;
- `/reports?project_id=&workspace_id=&capture_id=` opens contextual creation;
- `/reports/{report_id}` loads one authorized detail.

URL values are hints only. APIs reauthorize all values. The page supports
`loading | empty | protected | invalid | conflict | unavailable | draft |
accepted`. It never asks the Human to type internal IDs.

Creation requires purpose, all four required content strings, coherent list
fields, qualification, and one selected server-composed candidate. Draft
revision submits the full existing draft with expected version, expected
revision, and explicit rationale. Acceptance uses a separate confirmation form
with explicit rationale, `confirmed=true`, expected version, and exact revision.

Accepted detail renders `accepted_snapshot` rather than mutable draft fields
and has no edit/accept controls. Provenance displays source kind, attribution,
version, standing, and integrity status without presenting internal digest as
an editable field.

## 5. Continuation and Command Center

Project Capture rows link to contextual report creation. Report lists/details
link back to the selected Project and Workspace context. Command Center Report
rows link to `/reports/{id}` with authorized context query parameters. It may
show only real lifecycle and version values; no synthetic review queue exists.

## 6. Accessibility, Responsive, Performance, and Scope

Every control has a label; status/error changes use accessible live regions;
acceptance has a labelled confirmation region; standing is textual; focus is
visible. At narrow width, forms and detail/provenance panels stack without
horizontal page overflow. Candidate page ≤20, Report page ≤20, and no polling
or broad source search is permitted.

Production code contains no Report/Capture/provenance fixture or fake count.
No migration, Memory mutation, AI acceptance, Report AI wiring, Context/
Evidence workbench, publication, template, generic task, or PATCH-040 behavior.

## 7. Verification Matrix

| Invariant | Required evidence |
|---|---|
| candidate authorization and scope | authorized success plus foreign Project/Workspace/Capture protected cases |
| canonical provenance | exact field parity, deterministic UUID/digest, lifecycle rejection, no direct persistence imports |
| create/revise | valid requests, typed invalid states, explicit rationale, stale conflict |
| exact Human acceptance | exact revision/version/confirmation/rationale and duplicate/stale rejection |
| immutable accepted UI | accepted snapshot rendering and absence of mutation controls |
| navigation | Capture→create, Report→Project, Command Center→detail without manual IDs |
| security | client Organization spoofing impossible; protected payload does not leak |
| UX | loading/empty/protected/error/conflict and real-data-only tests |
| accessibility/responsive | labels/live status/keyboard/semantic review and narrow layout checks |
| regression | PATCH-032/034/035/036/037/038, full backend, frontend tests/build/typecheck |
| delivery | scope/secrets/prohibited patterns and `git diff --check` |
