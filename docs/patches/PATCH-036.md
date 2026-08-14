# PATCH-036 — SATCO Web Application & Engineering Dashboard

## Governance Status

Architecture/QG-M1, EDS, IDS, Implementation Plan, IRR, Batches 1–4,
Independent Final Review, and Human QG-11 are PASS / ACCEPTED / COMPLETE.
QG-12 bounded delivery is READY and pending execution. Delivery and closure
have not yet been performed.

## Capability Boundary

PATCH-036 provides the first real authenticated SATCO web application over
already accepted APIs: application shell, operational dashboard, authorized
Projects and Engineering Workspaces, Engineering Journal/Capture visibility,
Technical Reports, Organizational Memory, and the PATCH-035 AI Capture
Assistant. The frontend is never an authority boundary and owns no canonical
engineering state.

Dashboard customization is presentation-only. V1 stores a bounded, versioned
layout containing widget identifiers, order, visibility, and supported size in
browser local storage. It stores no token, engineering payload, identity,
scope, count, or authorization decision. Malformed or stale layouts fail to the
SATCO default; server-side per-user preferences remain an explicit extension.

## Deferred

Server-side user preferences, notifications, global search beyond accepted
Search APIs, cross-Organization views, semantic/vector search, graph expansion,
frontend approval automation, autonomous action, PLC/code generation, customer
communication, and every PATCH-037 capability are deferred.

## Dependencies

PATCH-028, PATCH-029, PATCH-032, PATCH-033, PATCH-034, PATCH-035, authenticated
Organization context, and their accepted HTTP contracts.

## Stop Conditions

Stop if a core workflow requires a new domain capability, client-derived
authority, protected-outcome disclosure, foreign persistence access, or an
unisolatable change outside this PATCH.
