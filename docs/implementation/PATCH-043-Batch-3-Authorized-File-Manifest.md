# PATCH-043 Batch 3 Authorized File Manifest

## Authority and boundary

Batch 2 is accepted. This manifest authorizes only S09-S12 canonical Evidence,
Technical Report, Organizational Memory authorization and recovery-set
integration. It excludes read/download transport, frontend and later batches.

## Authorized production files

MODIFY:

- `backend/app/models/evidence_command.py`, `backend/app/ports/evidence.py`,
  `backend/app/schemas/evidence.py`, `backend/app/repositories/evidence_repository.py`,
  `backend/app/repositories/evidence_unit_of_work.py`,
  `backend/app/services/evidence_service.py` — exact proposed-Evidence link
  command, same-Session Supporting File lock/recheck, sealed deterministic links,
  version/Audit/outbox/idempotency behavior only.
- `backend/app/models/technical_report_command.py`,
  `backend/app/ports/technical_report.py`,
  `backend/app/repositories/technical_report_unit_of_work.py`,
  `backend/app/services/technical_report_service.py` — closed
  `EvidenceHistoricalBasisV2`, canonical digest/serialization, linked-Asset
  composition and acceptance final recheck using the caller-owned Session.
- `backend/app/ports/supporting_file.py`,
  `backend/app/repositories/supporting_file_repository.py`,
  `backend/app/services/supporting_file_service.py` — canonical same-Session
  Evidence/Report/Memory authorization collaborators only; no transport/read API.
- `backend/app/adapters/organizational_memory.py` and
  `backend/app/services/organizational_memory_service.py` — recognize Evidence
  V2 and authorize every nested Asset all-or-nothing without byte ownership.
- `ops/scripts/backup.sh`, `ops/scripts/restore-verify.sh` — deterministic
  object-inclusive recovery-set manifest verification only; no object listing by
  application runtime and no claim of external backup proof.
- `backend/migrations/versions/e04300000001_supporting_files.py` — focused
  reconciliation of the accepted Workspace-compatibility guard only: a
  Project-scoped Asset (null Workspace) is compatible with Workspace-scoped
  Evidence in that Project. No table, lifecycle or migration-head expansion.

## Authorized tests

MODIFY existing focused Evidence, Technical Report, Organizational Memory and
operations recovery contract/service/transaction/security tests. CREATE
`backend/tests/test_supporting_file_canonical_integration.py` for same-Session
link, V1/V2, acceptance/withdrawal race, Memory authorization and recovery
consistency evidence. MODIFY `backend/tests/test_supporting_file_migration.py`
only for direct-SQL evidence of the reconciled compatibility rule.

## Evidence and stop conditions

Evidence must prove proposed-only/available-only exact 1..10 links, scope and
version checks, deterministic UUID order, one Evidence version/event/Audit,
permanent seal, V1 regression, V2 digest, Report final Asset recheck and
withdrawal race, Memory all-or-nothing current and historical authorization,
and object-inclusive recovery mismatch denial. No direct foreign repository or
second Session is permitted. Stop for any change to accepted Evidence lifecycle,
Report acceptance authority, Memory admission/Human authority, PATCH-042
recovery ownership, any migration/schema change beyond the exact compatibility
correction above, or Batch 4+ surface.
