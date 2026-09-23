# PATCH-058 Checkpoint A1 — Persistence Foundation Human Acceptance

**Date:** 2026-09-23

**PATCH:** PATCH-058 — Commercial Authentication, Application Security &
Reproducible Release Foundation

**Checkpoint:** A1 — Persistence Foundation

## Human decision

PATCH-058 Checkpoint A1 — Persistence Foundation is **HUMAN ACCEPTED /
COMPLETE**.

This acceptance follows the final independent A1 review verdict:

- PASS — READY FOR HUMAN A1 ACCEPTANCE;
- Critical: 0;
- Major: 0;
- Minor: 0;
- Observation: 1, pre-existing and non-blocking.

Human Authority remains controlling. AI remains advisory and
non-authoritative.

## Exact accepted implementation boundary

Acceptance applies only to these reviewed paths and exact SHA-256 identities:

| Path | SHA-256 |
| --- | --- |
| `backend/app/models/__init__.py` | `4247f30fa16ac56d63272c302dc509b8e49335ee61b516c16d9cfe0fb0d6d51d` |
| `backend/app/models/auth_security.py` | `859fb46de401e0b33d8aa2556bd106938037d18b21aedd7fdc2aeb7c410ee919` |
| `backend/migrations/versions/e05800000001_patch_058_auth_security_persistence.py` | `1934b2119daf29b1ccfc2efa8b44c77f44de82e9c83a10f05bf475d89e7b2688` |
| `backend/tests/test_patch058_auth_security_persistence.py` | `1eb2924600f5d4e27aaa120e5fc8d08165d2f2b0c7b4696c35a722ca2c58fda8` |

The accepted A1 boundary contains only:

- PATCH-058 security persistence models;
- model registration;
- the forward, non-destructive Alembic revision `e05800000001` directly from
  `e05600000008`;
- focused persistence and migration contract tests.

It introduces bounded persistence for refresh families/sessions, TOTP
authenticators, MFA recovery-code verifiers, authentication-recovery
credentials, Organization member-MFA policy, security events and
authentication throttle state. It creates no competing User, Organization,
membership, Customer, Contact or engineering authority.

## Accepted qualification basis

The accepted evidence records:

- bounded regression: 51 passed, 9 warnings, `TEST_RC=0`;
- Python compilation: `COMPILE_RC=0`;
- sole Alembic head/current revision: `e05800000001`;
- actual PostgreSQL constraint, index, privilege and no-raw-secret inspection;
- populated-state downgrade refusal with revision preserved;
- zero remaining disposable security rows;
- successful clean downgrade to `e05600000008` and re-upgrade to
  `e05800000001`;
- `git diff --check`: PASS;
- staging: empty before this acceptance record was prepared.

## Acknowledged baseline observation

The known `alembic check` metadata/import failure involving
`standard_source_snapshots` is acknowledged as a pre-existing PATCH-057
baseline limitation. It is not attributable to A1 and is not accepted into the
A1 implementation scope. No unrelated baseline file may be changed under A1
to address it.

## Authority boundary

This record captures the Human A1 acceptance decision only. It does not:

- alter the Human-accepted Discovery, Architecture-058, ADR-031, EDS-058,
  IDS-058 or Implementation Plan-058;
- authorize semantic changes to the accepted A1 implementation;
- authorize staging, commit or push without a subsequent explicit Human
  instruction;
- authorize A2 or any later PATCH-058 checkpoint work;
- authorize production/customer database access or deployment;
- authorize PATCH-059 or PATCH-060;
- grant AI authentication, security, recovery, signing, release or acceptance
  authority.

**PATCH-058 CHECKPOINT A1 — HUMAN ACCEPTED / COMPLETE.**
