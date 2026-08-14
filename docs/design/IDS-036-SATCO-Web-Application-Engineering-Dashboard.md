# IDS-036 — SATCO Web Application & Engineering Dashboard

## Stack and Routes

React 19, TypeScript, Vite, React Router, Vitest, Testing Library, and CSS
custom properties. Routes: `/login`, `/`, `/projects`, `/projects/:projectId`,
`/journal`, `/reports`, `/memory`, and `/assistant`.

## Authentication and API Contract

`AuthSession { accessToken: string }` is memory/session-storage state only.
`POST /auth/login` uses form encoding; `/auth/me` validates the session. Every
other request sends `Authorization: Bearer`. The API client maps 401 to signed
out, 403/404 protected cases to `protected`, 400/422 to `invalid`, 503 to
`unavailable`, and other failures to a generic recoverable error without raw
details. Actor and Organization are never request fields.

The client uses only documented Project, Workspace, Journal/Capture, Technical
Report, Organizational Memory, and AI Capture Assistant fields. Lists request
at most 20 records unless a backend continuation contract governs the page.

## Component Boundaries

`AppShell` owns navigation and route outlet. `PageHeader`, `Surface`, `Status`,
`EmptyState`, `LoadingState`, and `ErrorState` are shared primitives. Screens
own only their route query/form state. `api.ts` owns transport and result
translation; `types.ts` owns closed frontend projections.

## Dashboard Registry and Layout

Closed widget IDs: `projects`, `engineering-work`, `reports`, `memory`,
`assistant`. Closed sizes: `compact | standard | wide`, mapped to 3/6/12 desktop
columns. Default order is the registry order.

`DashboardLayoutV1 { version: 1; widgets: Array<{id; size; hidden}> }` contains
exactly one entry per registry ID, at most five entries, no extras, and no other
fields. Persistence key is `satco.dashboard.layout.v1`. Parse, version, shape,
duplicate, missing-ID, or size failure resets to default. Drag/drop reorders;
keyboard buttons provide equivalent movement. Reset removes the key.

## Query and Cache Rules

Requests are route-scoped, abortable, and refreshed on navigation or explicit
retry. No authorization result is persisted. Layout preferences are the only
local-storage data. Tokens use session storage. No response is cached as an
authority decision.

## Responsive and Accessibility Contracts

At >=1200px use 12 columns; 760–1199px use 6; below 760px use one column.
Navigation drawer is modal on narrow screens. All controls have names, visible
focus, semantic elements, keyboard operation, and text status. Motion respects
`prefers-reduced-motion`.

## Validation Matrix

Evidence must cover login/session clearing, protected mapping, API path/query
construction, widget validation/recovery/reorder/resize/hide/restore/reset,
route navigation, loading/empty/error states, AI advisory distinction,
responsive CSS, keyboard controls, accessibility checks, production build,
type/lint checks, backend integration regression, prohibited patterns, secrets,
scope, and `git diff --check`.
