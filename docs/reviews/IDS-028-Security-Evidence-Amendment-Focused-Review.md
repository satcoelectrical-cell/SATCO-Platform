# IDS-028 Security-Evidence Amendment — Independent Focused Review

## Review Control

| Field | Value |
|---|---|
| Related PATCH | PATCH-028 |
| Review scope | Behavioral security/disclosure evidence only |
| Result | PASS |
| Date | 2026-08-03 |

## Authorized Test Boundary

- `backend/tests/test_engineering_experience_capture_security.py`;
- `backend/tests/test_engineering_experience_capture_service.py`;
- `backend/tests/test_engineering_experience_capture_transaction.py`;
- `backend/tests/test_engineering_experience_capture_api.py`.

## Conditional Runtime Boundary

Only a failing new behavioral test may justify a minimal correction in:

- `backend/app/services/engineering_experience_capture_service.py`;
- `backend/app/repositories/engineering_experience_capture_repository.py`;
- `backend/app/repositories/engineering_experience_capture_unit_of_work.py`;
- `backend/app/api/v1/routers/engineering_experience_captures.py`.

No other file is authorized by this amendment.

## Independent Findings

The Independent Final Review identified an evidence gap, not an approved
semantic change. The requested cases directly implement existing IDS-028
security requirements: deny-by-default scope, authorization before disclosure,
accurate authorized totals, replay reauthorization, and plaintext exclusion
from operational records and failures.

The conditional runtime boundary is appropriate because the files already own
application authorization orchestration, scoped persistence, policy/UoW
adapters, and HTTP mapping. Corrections remain subordinate to existing
contracts and may not introduce new behavior.

## Constraint Verification

```text
PATCH scope expansion: NONE
New endpoint: PROHIBITED
Schema/migration change: PROHIBITED
Aggregate contract change: PROHIBITED
Protected-not-found weakening: PROHIBITED
Repository commit ownership: PROHIBITED
Unit-of-Work transaction ownership: PRESERVED
Development/deployment migration: NOT AUTHORIZED
Commit/push: NOT AUTHORIZED
```

## Decision

**PASS.** The amendment is the smallest authorized path to replace incomplete
structural evidence with mandatory behavioral proof. Implementation may begin
inside the exact test boundary, with conditional runtime correction only after
a test demonstrates a defect.

```text
Manifesto Alignment Verified: YES
QG-M1 amendment result: PASS
Security-evidence remediation: AUTHORIZED
Human QG-11: NOT READY UNTIL VALIDATION AND REPEATED INDEPENDENT FINAL REVIEW
```
