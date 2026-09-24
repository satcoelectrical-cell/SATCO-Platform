# PATCH-058 Checkpoint B3 Human Acceptance

Status: HUMAN ACCEPTED / COMPLETE
Acceptance date: 2026-09-24
Accepted by: Human Engineering Authority

## Accepted bounded scope

Checkpoint B3 delivers the Human-controlled account and MFA recovery sub-slice within accepted PATCH-058 Checkpoint B. It does not by itself declare the whole Checkpoint B complete and does not start PATCH-059 or PATCH-060.

Accepted implementation:

- recovery credentials may be issued only through authenticated administrator authority with recent authentication;
- recovery issuance is current-Organization scoped and authorization-before-lookup protected;
- account and MFA recovery credentials are purpose-bound, short-lived, single-use, selector-plus-secret credentials with only a non-reversible verifier persisted;
- a newly issued credential revokes an older unused credential for the same user, Organization and purpose;
- account recovery changes the password, advances auth_version, and revokes existing sessions;
- MFA recovery disables the active TOTP authenticator, invalidates unused MFA recovery codes, advances auth_version, and revokes existing sessions so re-enrollment is required;
- public recovery completion returns bounded generic invalid/expired failure semantics;
- recovery verification has dedicated PostgreSQL-backed throttling keyed without persisting the plaintext selector and includes network context;
- security events contain bounded attribution and no raw recovery credential;
- no new database migration and no weakening of accepted A2/B1/B2 authentication semantics.

## Qualification evidence

- focused B3/B2/B1/A2 security qualification: 43 passed, 0 failed;
- full backend non-migration regression on fresh disposable PostgreSQL: 2112 passed, 0 failed;
- isolated migration-mutating qualification on fresh disposable PostgreSQL: 75 passed, 0 failed;
- Python compile qualification PASS;
- uv lock --check PASS;
- git diff --check PASS;
- Alembic sole repository head remains e05800000001;
- credential/log/security-context leak review PASS;
- cross-Organization and missing-target anti-inference qualification PASS;
- unresolved Critical 0 / Major 0.

## Human decision

The Human Engineering Authority explicitly accepted B3 after implementation, endpoint-level authorization and anti-inference qualification, recovery-verification throttling correction, full backend regression, independent migration qualification, and final security review.

This acceptance authorizes closure delivery of exactly this B3 boundary. It does not authorize unrelated changes, PATCH-059, or PATCH-060.
