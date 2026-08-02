# EDS-025 — Authenticated Organization Context

## Status

Accepted

## Domain Design

`Organization` contains immutable UUID identity, active state, and controlled
timestamps. `UserOrganizationMembership` references one User and one
Organization and contains enabled state, selection state, and timestamps.

The relation enforces one membership per `(user_id, organization_id)` and a
partial unique index allowing at most one selected membership per User.
It also enforces that a disabled membership cannot remain selected. Selection
is valid only while both membership and Organization are active; Organization
active state is verified by the resolver because it is a cross-table rule.

## Application Contract

The resolver performs:

1. existing JWT verification;
2. existing active User lookup;
3. selected membership lookup by User;
4. enabled-membership and active-Organization validation;
5. construction of trusted User plus Organization UUID context.

Zero or non-unique valid selections produce
`ACTIVE_ORGANIZATION_CONTEXT_REQUIRED`. The resolver discloses no foreign
Organization identity.

## Security

Organization scope is server-derived on every protected request requiring it.
Request bodies, query parameters, and unsigned headers cannot select it.
Project and Workspace membership never implies Organization membership.

## Persistence

The migration is additive and creates only `organizations` and
`user_organization_memberships`, their keys, checks, foreign keys, uniqueness,
partial selected-membership index, and timestamps.

## Acceptance

EDS-025 is accepted. No authentication redesign or new role is required.
