# PATCH-058 Checkpoint B2 Human Acceptance

Status: HUMAN ACCEPTED / COMPLETE
Acceptance date: 2026-09-24
Accepted by: Human Engineering Authority

## Accepted bounded scope

Checkpoint B2 delivers the session lifecycle, recent-authentication/step-up, recovery-code lifecycle, and Organization-scoped administrator session-revocation sub-slice within accepted PATCH-058 Checkpoint B. It does not declare the whole Checkpoint B complete and does not start PATCH-059 or PATCH-060.

Accepted implementation:

- active-session visibility limited to safe metadata and current-user sessions;
- consumed refresh predecessors excluded from active-session visibility;
- current-session logout and immediate server-side invalidation;
- all-session revocation with family revocation;
- administrator-targeted session revocation gated by administrator authority, recent authentication, current Organization membership and authorization-before-lookup;
- protected cross-Organization/not-found behavior preventing target inference through the administrator revocation endpoint;
- ten-minute recent-authentication window based on initial family authentication or explicit successful step-up, without extension from ordinary refresh rotation;
- password step-up and TOTP step-up when MFA is active/required;
- single-use recovery-code consumption with non-reversible verifier matching and security-event attribution;
- recovery-code regeneration invalidating prior unused generation and returning new raw codes only at regeneration time;
- safe security-event attribution for revocation, step-up, TOTP verification, and recovery-code lifecycle;
- no new database migration and no weakening of accepted A2/B1 authentication semantics.

## Qualification evidence

- focused B2/B1/A2 security qualification: 35 passed, 0 failed;
- broader API/security qualification before full regression: 63 passed, 0 failed;
- full backend non-migration regression on fresh disposable PostgreSQL: 2104 passed, 0 failed;
- isolated migration-mutating qualification on fresh disposable PostgreSQL: 75 passed, 0 failed;
- Python compile qualification PASS;
- uv lock --check PASS;
- git diff --check PASS;
- Alembic sole repository head remains e05800000001;
- independent security review found and corrected active-session listing of consumed refresh predecessors before final qualification;
- unresolved Critical 0 / Major 0.

## Human decision

The Human Engineering Authority explicitly accepted B2 after the bounded implementation, authorization/anti-inference review, correction of the consumed-session visibility finding, focused security qualification, full backend regression, and independent migration qualification.

This acceptance authorizes closure delivery of exactly this B2 boundary. It does not authorize unrelated changes, the remainder of Checkpoint B, PATCH-059, or PATCH-060.
