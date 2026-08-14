# EDS-036 — SATCO Web Application & Engineering Dashboard

## Architecture

V1 is a Vite-built React/TypeScript single-page application. It uses a small
typed HTTP boundary, route-scoped server state, explicit authentication state,
and local component/form state. No giant global engineering store exists.

## Application Shell and Navigation

Authenticated routes are Dashboard, Projects, Project Workspace, Engineering
Journal, Technical Reports, Organizational Memory, and AI Capture Assistant.
Unsupported settings, notifications, analytics, and future modules are not
shown. Navigation collapses to a drawer at narrow widths and preserves visible
focus and keyboard operation.

## Dashboard

The operational dashboard surfaces authorized Projects, engineering work,
Technical Reports, Organizational Memory, and AI Assistant entry. Loading,
empty, protected, invalid, and unavailable states are explicit without
revealing protected existence or counts.

Customize Dashboard changes only widget order, supported width, and visibility.
Native drag/drop is supplemented by keyboard-accessible move, resize, hide,
restore, and reset controls. Layout is device-local, schema-versioned, bounded,
allow-listed, and fail-safe. It contains no engineering or identity data.

## Engineering Workflows

Project Workspace contextualizes one currently authorized Project and its
Workspaces, Captures, Reports, and Memory links where corresponding APIs exist.
Technical Report and Memory screens render only accepted response fields. The
AI screen submits an explicit Human instruction for one authorized Capture and
visually separates advisory output, assumptions, uncertainty, limitations, and
attribution from canonical facts.

## Security and Ownership

The browser never supplies actor or Organization authority. It may supply
canonical Project/Workspace identifiers as resource selectors only; the backend
reauthorizes every request. Tokens are session-only and never written to local
storage. Protected backend outcomes map to one neutral non-disclosing state.

## Responsive and Accessible Behavior

Desktop is primary. The grid moves from 12 to 6 to 1 columns; tables gain
horizontal containment; navigation becomes a drawer; forms and AI panels stack.
Semantic landmarks, labels, focus visibility, keyboard alternatives, dialog
focus, reduced motion, and non-color status text are required.

## Deferred Boundary

No fake data, shadow canonical state, server preference persistence, semantic
search, graph traversal, autonomous AI, approval, notification, or unsupported
route is introduced.
