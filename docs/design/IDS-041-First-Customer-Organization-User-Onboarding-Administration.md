# IDS-041 — First-Customer Organization & User Onboarding Administration

Status: ACCEPTED. Independent Review: PASS.

## Persistence contracts

Migration `e04100000001`, parent `e03800000001`, adds legacy-compatible `organizations.name` and `organizations.slug`, unique case-insensitive non-null indexes for populated profiles, and deterministic accepted legacy backfill. `users` gains non-null `activation_pending` default false and `auth_version` default 1. `account_action_credentials` stores UUID identity, Organization/User FKs, `activation|reset` purpose, unique 64-character SHA-256 digest, timezone-aware expiry, nullable used/revoked timestamps, optional issuing User, and timestamps. A partial unique index permits one live credential per User/purpose. Runtime receives only required DML; schema ownership remains migration-owned.

## Application and transport contracts

- `POST /platform/bootstrap/organizations`: bootstrap header plus idempotency UUID; normalized Organization profile and initial-admin identity; returns success with Organization summary, member summary, and one-time activation token.
- `POST /auth/activate` and `POST /auth/reset`: token plus policy-valid new password; closed success or payload-free invalid result.
- `POST /auth/change-password`: authenticated current/new passwords; closed success/invalid/protected result.
- `GET|POST /organization-admin/members`: current-Organization admin list/provision.
- `PATCH /organization-admin/members/{user_id}`: expected version plus exactly one role/membership/account change.
- `POST /organization-admin/members/{user_id}/reset`: authorized one-time reset issuance.
- `POST /platform/bootstrap/resets`: platform recovery reset using Organization slug and username with protected mismatch.
- `POST /auth/register`: disabled with neutral protected response.
- `GET /auth/me`: identity, role, and server-derived Organization summary.

All issuer mutations use `Idempotency-Key`; replay returns a safe completed discriminator without replaying credential plaintext. A lost issuance response is recovered through a new explicit reset. JWT access tokens bind `auth_version`; password change/reset invalidates earlier tokens. Passwords reuse the accepted hasher.

## Verification matrix

Evidence covers migration/head/backfill/constraints; bootstrap configuration and replay; case-conflicting identities; initial admin and engineer activation; expiry/replay/revocation; password change/reset/session invalidation; inactive User/membership/Organization; role and state changes; last-admin/self-lockout/concurrency; cross-Organization and account enumeration; Audit secret exclusion and rollback; public-registration closure; frontend workflows; accessibility/responsive/no fake data; adjacent/full regressions; build/type/static; secrets/scope; and git checks.
