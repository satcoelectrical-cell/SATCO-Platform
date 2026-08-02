# IDS-027 — Evidence Foundation

## Status

Approved

## Exact Authorized File Set

Modified:

- `backend/app/enums/__init__.py`
- `backend/app/models/__init__.py`
- `backend/app/schemas/__init__.py`
- `backend/app/main.py`
- `backend/migrations/env.py`

Created:

- `backend/app/enums/evidence.py`
- `backend/app/models/evidence.py`
- `backend/app/models/evidence_command.py`
- `backend/app/schemas/evidence.py`
- `backend/app/ports/evidence.py`
- `backend/app/repositories/evidence_repository.py`
- `backend/app/repositories/evidence_unit_of_work.py`
- `backend/app/services/evidence_service.py`
- `backend/app/exceptions/evidence.py`
- `backend/app/api/v1/routers/evidence.py`
- `backend/migrations/versions/e02700000001_evidence_foundation.py`
- `backend/tests/test_evidence_aggregate.py`
- `backend/tests/test_evidence_schemas.py`
- `backend/tests/test_evidence_repository.py`
- `backend/tests/test_evidence_service.py`
- `backend/tests/test_evidence_api.py`
- `backend/tests/test_evidence_transaction.py`
- `backend/tests/test_evidence_migration.py`
- `backend/tests/test_evidence_validator.py`

No other file is authorized.

## Migration Contract

Revision `e02700000001` has sole parent `e02500000001`. It creates only
`evidence`, `evidence_outbox`, and `evidence_idempotency` with EDS fields,
controlled checks, scope coherence check, positive version, RESTRICT foreign
keys to Organization/Project/Workspace/User and Evidence replacement, outbox
event uniqueness/version, idempotency uniqueness/status, and indexes for
Organization/Project/Workspace/lifecycle visibility. Downgrade removes only
these tables. Clean upgrade, downgrade, re-upgrade, and model/schema comparison
are mandatory.

## Implementation Contract

Pydantic v2 uses ConfigDict and extra=forbid. Repository supports add,
authorized-scope load/list and compare-and-change. EvidenceValidator returns a
stable validation result without content. Service invokes one aggregate command
and atomically stages Evidence, Audit, outbox, and idempotency result.

Creation has no expected version. Lifecycle transition requires positive
expected version and increments exactly once. Exact idempotent replay returns
the authorized snapshot; conflicting reuse returns conflict. Authorization
precedes disclosure.

## API and Errors

Only the four EDS endpoints are authorized. Responses expose scalar metadata
and deterministic allowed_actions. Stable codes use the `EVIDENCE_` prefix for
Validation, Authorization Denied, Not Found, Version Conflict, Idempotency
Conflict, Invalid Transition, and Internal Error.

## Stop Conditions

Stop for an unlisted field/file/table/endpoint, source content storage, file
handling, AI generation, semantic search, cross-Project relaxation, generic
update, physical delete, non-atomic mutation, authorization bypass, migration
drift, or regression failure.

## Approval

IDS-027 is approved subject to IRR-027 READY FOR IMPLEMENTATION.
