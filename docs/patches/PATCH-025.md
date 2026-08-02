# PATCH-025 — Authenticated Organization Context

## Status

Approved — implementation requires IRR-025.

## Purpose

Add the minimum tenant-membership foundation required to derive an authenticated
actor's active Organization scope server-side.

## Scope

- minimal Organization identity and active state;
- User–Organization membership with enabled/disabled state;
- at most one selected active membership per User;
- a trusted authentication dependency that resolves the selected membership;
- a stable missing/disabled/ambiguous-context error;
- migration and focused authentication/isolation tests.

## Trusted Derivation Rule

After JWT verification and active User loading, the server shall resolve exactly
one selected, enabled User–Organization membership whose Organization is active.
Its Organization UUID becomes `AuthenticatedActor.organization_id`.

The Organization UUID is never read from an EngineeringObject request body,
query parameter, unsigned header, or unverified token claim. A signed claim may
only identify a candidate after the same live membership and Organization checks;
PATCH-025 does not require such a claim.

Zero, multiple, disabled, or inaccessible selected memberships return
`ACTIVE_ORGANIZATION_CONTEXT_REQUIRED` without exposing another Organization.
Every repository and policy scope remains deny-by-default across Organizations.

## Non-Scope

- login redesign;
- organization administration APIs;
- invitation, billing, entitlement, or customer-domain behavior;
- changing existing User identifiers or roles;
- implicit membership from Project or Workspace participation;
- client-controlled trusted Organization selection;
- PATCH-023 router implementation.

## Deliverables

- Organization and UserOrganizationMembership persistence models;
- one additive migration parented to the current Alembic head at implementation;
- trusted active-Organization resolver and stable exception;
- focused tests.

## Acceptance Criteria

- Organization identity is UUID and immutable;
- membership is unique per User and Organization;
- only enabled membership in an active Organization can be selected;
- no User has more than one selected membership;
- missing or invalid context fails before protected application service calls;
- cross-Organization access is denied;
- existing authentication behavior remains compatible for endpoints that do not
  require Organization context;
- migration and regressions pass.

## Authorization

Implementation is authorized only by IDS-025 and IRR-025.

