# IDS-037 — SATCO Engineering Command Center Productization

Status: ACCEPTED.

## Exact Read Contract

`loadCommandCenter(now) -> Promise<CommandCenterResult>` performs exactly one
bounded `projects` call (page 1, size 20). On success it retains at most eight
visible Projects. If at least one exists, it performs one each of `workspaces`,
`captures`, and `journal` for the first canonical Project. If one visible
Workspace exists it performs one each of `reports` and `memory`. Maximum calls:
six; no retry, polling, pagination traversal, or fallback.

`CommandCenterResult` is `success(data) | protected | invalid | unavailable |
error`. Nested protected/error sources are recorded only as their closed state;
no rejected payload is retained.

## Derived View Contract

- visible Projects: maximum eight; canonical Project ordering from API;
- high-priority count: visible `priority in {high, critical}` only;
- recent-update count/activity: visible `updated_at >= now - 7 days` only;
- Capture-context count: visible returned Capture items only;
- status distribution: visible Project canonical status values only;
- Active Projects table: maximum six rows; exact name/code/customer, priority,
  status, progress, and updated time;
- Engineering Work: maximum five Project/Capture records, deterministic order;
- Reports/Memory: maximum three visible records per surface;
- AI panel: latest visible Capture context and Human-request CTA only.

No result exposes API `total` as a KPI. No deadline/review/AI-result inference,
synthetic row, fictional chart, or generic activity claim is permitted.

## UI and Layout

Existing widget IDs remain closed: `projects`, `engineering-work`, `reports`,
`memory`, `assistant`. Layout schema remains V1 and backward compatible. The
Command Summary is fixed context, while every product surface remains within a
registered customizable widget. Desktop 12-column, tablet six-column, narrow
single-column behavior is required.

## Verification Matrix

Evidence must prove six-call bound, no downstream calls after protected Project
read, visible-only KPI semantics, exact ordering/limits, empty/protected/error
states, no fake production data, AI advisory wording, table semantics,
customization persistence/recovery, keyboard/accessibility, responsive CSS,
frontend build/type/tests, adjacent/full backend regression, secret/prohibited
patterns, QG-M1, and `git diff --check`.
