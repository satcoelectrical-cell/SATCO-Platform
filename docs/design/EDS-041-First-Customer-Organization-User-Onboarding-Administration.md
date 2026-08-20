# EDS-041 — First-Customer Organization & User Onboarding Administration

Status: ACCEPTED. Independent Review: PASS.

## Accepted semantics

- Platform bootstrap requires configured `PLATFORM_BOOTSTRAP_KEY`; missing configuration fails closed. It creates a normalized unique Organization, one inactive activation-pending admin User, one enabled selected membership, Audit, and one activation credential atomically.
- Current-Organization administrators may list members and provision an inactive activation-pending member with `admin` or `engineer`. No self-assignment or cross-Organization target is accepted.
- Membership enable/disable and account enable/disable are distinct. Account/role mutation is accepted only for a single-membership V1 User. Last-admin and self-lockout guards apply under concurrency.
- Activation establishes the first password. Authenticated change requires the current password. Admin or platform reset issues a new reset credential without selecting a permanent password. Credential completion sets the new password and invalidates prior sessions.
- Exactly one selected enabled membership is created for each V1 provisioned account. The client never supplies Organization authority to Organization-admin operations.
- Member/user/Organization existence, failed credential reason, and token state are protected. Lists disclose only current-Organization members after authorization.
- Public disconnected registration is unavailable. Email delivery, self-service recovery, enterprise IAM, multiple selected Organizations, and new roles are deferred.

Audit, idempotency, optimistic concurrency, transaction rollback, non-disclosure, accessible responsive forms, one-time secret display, and Command Center continuation are mandatory.
