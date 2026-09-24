# PATCH-058 Checkpoint B Human Acceptance

Status: HUMAN ACCEPTED / COMPLETE
Acceptance date: 2026-09-24
Accepted by: Human Engineering Authority

## Accepted scope

The Human Engineering Authority accepts PATCH-058 Checkpoint B in full, comprising the previously accepted B1, B2, and B3 sub-slices plus the bounded final authority-hardening correction identified during Checkpoint B qualification.

Accepted capabilities include:

- mandatory administrator TOTP MFA and Organization-configurable engineer/member MFA;
- TOTP enrollment, verification and replay prevention;
- MFA recovery-code generation, single-use consumption and regeneration;
- Human-controlled account and MFA recovery;
- recent-authentication / step-up controls;
- current-session, all-session and administrator-authorized session revocation;
- safe session visibility and security-event attribution;
- Last-Administrator protections;
- Organization authority enforcement at the onboarding service boundary so caller-supplied role identity alone cannot exercise Organization security administration;
- qualification evidence that non-administrator/non-member authority cannot exercise Human security-recovery or Organization administration authority.

This acceptance does not authorize Checkpoint C, PATCH-059, or PATCH-060 implementation by itself.

## Final qualification evidence

- focused Checkpoint B security/authority qualification: 55 passed, 0 failed;
- full backend non-migration regression on fresh disposable PostgreSQL: 2117 passed, 0 failed;
- isolated migration-mutating qualification on fresh disposable PostgreSQL: 75 passed, 0 failed;
- Python compile qualification PASS;
- uv lock --check PASS;
- git diff --check PASS;
- Alembic sole repository head remains e05800000001;
- no new migration;
- unresolved Critical findings: 0;
- unresolved Major findings: 0.

## Corrective authority finding closure

Final Checkpoint B qualification identified a Major defense-in-depth authorization gap: OnboardingService.mutate_member trusted route-level Organization administration authority and did not independently require the actor to be an active administrator with enabled membership in the target Organization.

The accepted correction enforces that authority at the service boundary. The actor must be an active, non-activation-pending administrator with an enabled membership in the same Organization before member-authority mutation can proceed. The correction is bounded to this security administration boundary and introduces no migration.

## Human decision

After the corrective change and complete requalification, the Human Engineering Authority explicitly accepted Checkpoint B as complete.
