# PATCH-059 C2 Checkpoint

**Date:** 2026-10-01
**Batch:** C2 — commercial entitlement and seat administration APIs
**Branch:** `patch-059-implementation`
**Accepted implementation parent:** `a6775d58dfb9de5f04f6f12af8174c8ddd95dac5`
**Disposition:** PASS — Human C2 Implementation Acceptance APPROVED

The formal checkpoint commit containing this record atomically preserves the
accepted C2 implementation and its evidence. This checkpoint is not PATCH-059
release approval, deployment approval, closure, tag authorization, push
authorization, or authorization to begin PATCH-060.

## Implemented scope

C2 provides the bounded current-Organization commercial administration API:

- `GET /organizations/current/commercial-entitlement`
- `POST /organizations/current/commercial-entitlement/validate`
- `POST /organizations/current/commercial-entitlement/activate`
- `GET /organizations/current/commercial-seats`
- `POST /organizations/current/commercial-seats/{user_id}`
- `DELETE /organizations/current/commercial-seats/{user_id}`
- `PUT /organizations/current/commercial-seats/retained`

The entitlement Validate API consumes the direct raw entitlement envelope body.
It passes the original bytes through the canonical parser, so duplicate JSON
members and other wire-format violations remain detectable. It is read-only and
does not call the activation service.

The Activate API repeats canonical parsing, signature/trust, binding, temporal,
revision and trusted-time validation server-side. Accepted and idempotent
activation commit. Rollback, same-revision conflict and TIME_UNTRUSTED rejection
commit their required durable security evidence. Pre-transaction cryptographic,
binding and not-before rejection cannot create false activation success.

The commercial-seat API reuses the accepted seat service and
`CommercialEntitlementUnitOfWork`. It does not reimplement seat-domain rules in
the router. List evaluation and single-seat/runtime evaluation share the same
canonical domain evaluator. Assign, explicit RESERVED reactivation, release and
exact retained-set replacement preserve the accepted ASSIGNED, RESERVED and
RETAINED semantics. Release deletes only the commercial seat and never changes
canonical Organization membership.

## Authorization and tenant boundary

All routes derive Organization scope from the canonical authenticated current
Organization context. No Organization identifier is accepted from the browser.

Commercial seat reads require canonical current-Organization administrator
authority. Entitlement Validate/Activate and all seat mutations additionally
require:

- PATCH-058 browser CSRF protection; and
- explicit `has_recent_step_up(auth.session, minutes=10)` assurance.

A fresh login without explicit successful step-up is insufficient. The
authenticated session identity must match the current-Organization identity.
Role, session-identity and target membership/seat mismatches preserve bounded
protected-not-found behavior. Seat/user lookup remains scoped to the current
Organization and deployment, preventing cross-Organization inference.

## State, time and response contracts

Effective commercial entitlement state is evaluated through one shared
canonical helper rather than independent router and seat-service algorithms.

Validate preview applies the accepted trusted-time evaluator without mutating
state. Sticky TIME_UNTRUSTED and observations more than five minutes behind the
durable checkpoint are reported fail-closed. Tolerated backward skew never
lowers the effective trusted time.

Response state, validation effect, package, seat-state and reason vocabularies
are bounded. Seat release uses a dedicated mutation response whose state may be
null, matching the accepted domain result instead of forcing a non-null seat
state after deletion. Request and response models prohibit extra members.

Runtime trust-store configuration uses the accepted setting:

`SATCO_COMMERCIAL_ENTITLEMENT_TRUST_STORE_FILE`

No commercial signing/private-key interface or browser-side verification
authority is introduced.

## Transaction and audit behavior

Activation and seat mutation use the commercial Unit of Work and established
PostgreSQL commercial-state locking boundary.

Accepted activation and durable rollback/conflict/TIME_UNTRUSTED rejection stage
canonical audit evidence inside the same commercial transaction. A failure to
stage audit prevents mutation commit. Cryptographic/binding/not-before rejection
first rolls back the mutation Unit of Work and then records only a bounded
rejection audit through repository-consistent post-rollback handling.

Seat assign, release and retained-set mutation stage canonical audit evidence in
the same transaction as the seat mutation. Retained-set resolution records the
bounded over-capacity resolution event. Higher-revision activation records entry
into over-capacity when consuming seats exceed the new signed capacity.

Audit metadata is limited to safe Organization/deployment identifiers,
entitlement identifier, revision, digest prefix, bounded outcome/reason,
capacity/count and target user identifier where applicable. Audit data excludes
the raw envelope, raw signature, key material, password/session secrets, CSRF
tokens and engineering content.

## Batch E dependency

`GET /organizations/current/commercial-update-eligibility` is intentionally not
implemented in C2. The accepted PATCH-059 design assigns governed server-verified
release-sequence integration to Batch E. C2 does not accept a client-supplied
release sequence, hard-code a sequence, or create a second release authority.
PATCH-058 Release Manifest authority remains unchanged.

## Qualification evidence

Integrated PATCH-059 qualification command:

```text
env PYTHONPYCACHEPREFIX=/tmp/p059-pycache \
  TEST_DATABASE_URL=postgresql+psycopg2://satco:***@127.0.0.1:55432/satco_platform_patch02022_test \
  .venv/bin/python -m pytest -p no:cacheprovider -q tests/test_patch059_*.py
```

Result:

- 165 passed
- 0 failed
- 18 warnings

PATCH-058 security/session/tenant regression command covered:

- `tests/test_patch058_c3_browser_auth.py`
- `tests/test_patch058_refresh_sessions.py`
- `tests/test_patch058_c1_tenant_isolation.py`

Result:

- 23 passed
- 0 failed
- 19 warnings

Warnings were non-blocking existing FastAPI lifespan and SQLAlchemy/Python
`datetime.utcnow()` deprecation warnings. No warning was waived as a security or
tenant finding.

Additional guards:

- Python `py_compile`: PASS
- `git diff --check`: PASS
- sole Alembic head: `e05900000002`

Database qualification used only the disposable PATCH-059 PostgreSQL instance:

- host/port: `127.0.0.1:55432`
- database: `satco_platform_patch02022_test`

The real PostgreSQL service on port 5432 was not touched.

## Independent review

The final independent security, tenant, transaction and ordering review covered:

- authorization ordering and protected-not-found behavior;
- tenant isolation and Organization/deployment scoping;
- CSRF and explicit recent step-up;
- direct raw-envelope canonical parsing;
- secret and sensitive-artifact exclusion;
- mutation transaction and rollback behavior;
- activation and seat audit consistency;
- seat concurrency and over-capacity semantics;
- trusted-time fail-closed behavior;
- production no-fail-open behavior; and
- absence of a second entitlement or release-sequence authority.

Findings:

- Critical: 0
- Major: 0
- open security/tenant findings: 0

## Human decision and checkpoint boundary

Human C2 Implementation Acceptance: **APPROVED**.

C2 implementation qualification: PASS.

C2 checkpoint finalization is authorized. No push or tag is authorized. This
checkpoint does not claim PATCH-059 closed and does not authorize PATCH-060 or
automatic progression into the next implementation batch.
