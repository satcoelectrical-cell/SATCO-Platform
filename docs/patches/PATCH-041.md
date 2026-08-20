# PATCH-041 — First-Customer Organization & User Onboarding Administration

## Governance state

| Gate | State |
|---|---|
| Registration | REGISTERED |
| Architecture / QG-M1 | PASS / ACCEPTED |
| EDS-041 | ACCEPTED |
| IDS-041 | ACCEPTED |
| Implementation Plan | ACCEPTED |
| IRR-041 | PASS |
| Batches 1–4 | ACCEPTED / COMPLETE |
| Security review | PASS |
| Product / UX review | PASS |
| Independent Final Review | PASS |
| Human QG-11 | PASS |
| QG-12 | PASS |
| Delivery | PASS — `2baddc03ecd258bc91c2538315dc6f4ffd58843f` |
| Remote verification | PASS — divergence `0/0` |
| Closure | DONE / CLOSED |

Final status: **DONE / CLOSED**. Batches 1–4 are ACCEPTED / COMPLETE. All Critical/Major findings are resolved; the historical FAIL → remediation → re-review chains remain preserved in standalone review artifacts. Deferred enterprise IAM, cross-Organization administration/switching, email recovery, Evidence/document intake, AI authority, and PATCH-042 remain outside the delivered V1.

## Product boundary

PATCH-041 removes database/developer intervention from normal first-customer onboarding. A configuration-authorized Platform Operator may create one customer Organization and its initial administrator. A current Organization administrator may list and provision only current-Organization members, assign only `admin` or `engineer`, manage bounded membership/account state, and initiate single-use support resets. Provisioned users activate, establish a password, sign in, receive one server-derived selected Organization context, and continue to the existing Command Center.

Platform bootstrap authority is not an application role. Organization-admin authority always intersects the authenticated actor, active selected membership, active Organization, and operation. Public disconnected registration is disabled. Activation/reset credentials are high-entropy, expiring, single-use, digest-only at rest, disclosed only at initial authorized issuance, and never logged or audited in plaintext.

## Explicit exclusions

Enterprise IAM, SSO/SAML/OIDC, SCIM, LDAP, federation, broad MFA/policy work, cross-Organization administration or switching, Organization transfer/merge/sharing, billing, subscriptions, licensing, CRM/Contacts productization, email recovery, support desk, Evidence/documents, Context, Journal/Capture productization, Project expansion, AI authority, semantic/vector search, and PATCH-042 remain deferred.
