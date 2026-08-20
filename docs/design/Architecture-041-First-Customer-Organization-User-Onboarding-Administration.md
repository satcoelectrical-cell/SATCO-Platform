# Architecture 041 — First-Customer Organization & User Onboarding Administration

Status: ACCEPTED. Independent Architecture Review and QG-M1: PASS.

## Authority and ownership

`Organization`, `User`, and `UserOrganizationMembership` remain canonical Platform Core records. Platform bootstrap is a separate, narrowly configured outward trust boundary: a high-entropy deployment secret, compared in constant time and disabled when absent, authorizes only Organization plus initial-admin bootstrap and platform recovery reset. It is not a User role and grants no engineering-data read authority. An `admin` User may administer only the Organization resolved from their active selected membership. A global role string alone is never sufficient.

V1 preserves `admin` and `engineer`. Role or account changes are allowed only when the target has one Organization membership; multi-Organization authority remains deferred. The last active enabled administrator cannot be demoted, disabled, or have membership disabled. Self-demotion/self-disable is rejected. Organization inactivity immediately blocks context resolution.

## Identity, credentials, and lifecycle

Organization V1 identity is UUID plus normalized human-readable name and unique slug. The accepted legacy Organization `7e7c9d7a-7693-4f75-9bc5-3ef7bf528281` is backfilled as `SATCO Engineering` / `satco-engineering`; other legacy rows receive deterministic UUID-derived labels without ownership change.

Provisioned Users are inactive and activation-pending with an unusable random password hash. Activation or reset credentials contain at least 256 bits of entropy, are returned once to the authorized issuer, and persist only as SHA-256 digests. Each is purpose-bound, single-use, expires, and supersedes older unused credentials of the same purpose. Activation establishes the password and activates the account; reset changes the password. Both increment `auth_version`, invalidating prior JWT sessions. Authenticated password change verifies the current password and also increments `auth_version`.

Public `/auth/register` is disabled. Login remains generic and non-enumerating. Activation/reset failures return one payload-free invalid outcome. Audit stores safe operation/category/target IDs only and never credentials, token material, password hashes, email delivery state, or protected failure detail.

## Reliability and UX

Bootstrap, provisioning, state/role mutations, and reset issuance are transactional, idempotency-keyed where an authorized issuer exists, and concurrency-safe through row locks plus database uniqueness. Token consumption locks the credential and User. Rollback leaves no partial membership, account, Audit, or credential state.

Frontend routes provide bootstrap, activation, password change, and current-Organization member administration. Bootstrap/issued credentials are held only in component memory and shown once. End users never type an Organization UUID. Successful activation returns to login; successful login continues to the Command Center. UI is real-data-only, accessible, responsive, and neutral for protected states.
