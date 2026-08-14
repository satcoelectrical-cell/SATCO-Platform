# Implementation-Plan-035 — AI Capture Assistant

Status: ACCEPTED

## Batch 1 — Contracts and Provider Boundary (S01–S03)

Create strict enums, DTOs, result unions, ports, exceptions, canonical JSON,
provider-neutral HTTPS adapter, Capture source adapter, and focused contract /
provider/security tests. Stop on canonical field mismatch, direct foreign
persistence, unbounded data, or authority semantics requiring redesign.

Expected surfaces: `app/enums`, `app/schemas`, `app/ports`, `app/exceptions`,
`app/ai`, `app/adapters`, and focused tests only.

## Batch 2 — Application, Audit, Composition, and Transport (S04–S07)

Implement the advisory service, shared Audit adapter, request-scoped dependency,
thin seven-free single-operation router, configuration, main registration, and
service/security/API tests. Preserve one authorized Capture read, one provider
call, payload-free outcomes, no persistence, and no frontend.

## Batch 3 — Final Validation and Evidence (S08–S10)

Run focused suites, adjacent Capture/Technical Report/security regressions,
full backend, import/static, exact-scope/prohibited-pattern/secret checks,
`git diff --check`, and QG-M1. Create reproducible validation evidence and the
Final Review artifact; update PATCH status only to review readiness.

Every batch requires an exact Authorized File Manifest, independent review,
focused remediation if required, and Human acceptance. No future-batch or
deferred capability may be implemented early.
