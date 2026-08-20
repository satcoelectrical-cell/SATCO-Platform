# Implementation Plan 041 — First-Customer Organization & User Onboarding Administration

Status: ACCEPTED. Independent Review: PASS.

## Dependency-ordered batches

1. **Batch 1 — Persistence and credential foundation.** Organization profile, User activation/session version, account-action credentials, migration, models/schemas/security helpers, and migration/contract evidence.
2. **Batch 2 — Bootstrap and administration backend.** Repository/service/transport for bootstrap, activation/reset/change-password, member administration, Audit/idempotency/concurrency/last-admin, `/auth/me`, and public-registration closure.
3. **Batch 3 — Activation and authenticated account UX.** Client contracts, bootstrap and activation/reset/change-password flows, trusted profile/session composition, and continuation.
4. **Batch 4 — Organization member administration and final evidence.** Member UI, role/state/reset controls, security/UX/accessibility/responsive evidence, regressions, final review, and delivery packaging.

Each batch receives an exact manifest and independent review. Stop for a new role model, mandatory external identity/email service, cross-Organization administration, accepted auth replacement, insecure token storage, destructive migration, or unrelated-work isolation failure.
