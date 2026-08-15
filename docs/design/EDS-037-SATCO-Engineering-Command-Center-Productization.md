# EDS-037 — SATCO Engineering Command Center Productization

Status: ACCEPTED.

## Product Semantics

The Command Center is an authorized presentation composition, not a new domain.
It provides: a visible-item KPI strip; prioritized Engineering Work from exact
Project priority/update and Capture context; a professional Active Projects
table; an AI advisory entry panel; scoped Reports and active Memory; canonical
Project-update activity; and exact visible Project-status distribution.

No KPI may use an API hidden/global total. “High priority” is the canonical
Project priority literal; “recently updated” is a deterministic seven-day
display window over `updated_at`; “Capture available” is not AI output. Project
updates are labelled as such and never imply Audit/activity ownership.

## Integration and Protection

One Project list read precedes at most five context reads: Workspaces, Captures,
Journal, Reports, and Memory. Reports/Memory are read only when an authorized
Workspace exists. Protected outcomes disclose neither identities nor counts.
No client actor/Organization authority or foreign persistence exists.

## Experience

The first viewport contains command context, KPI strip, Engineering Work,
Active Projects, and AI intelligence. Existing layout customization remains
versioned, allow-listed, device-local, keyboard accessible, resettable, and
presentation-only. Desktop uses a 12-column command grid; tablet uses six;
narrow view uses one. Semantic tables, focus, non-color status, reduced motion,
loading/empty/protected/unavailable states are required.

## Deferred

Global search, notifications, overdue/review workflow, generic activity/Audit
feed, semantic/vector retrieval, autonomous actions, and unsupported analytics.
