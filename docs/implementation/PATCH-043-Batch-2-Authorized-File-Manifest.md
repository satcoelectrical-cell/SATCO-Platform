# PATCH-043 Batch 2 Authorized File Manifest

## Authority and scope

Batch 1 is accepted. This manifest authorizes only object data-plane
implementation: reservation, private streaming/transfer abstraction, digest
verification, scanner disposition, reconciliation and withdrawal. It does
not authorize Evidence/Technical Report/Memory composition, read/download
routes or frontend.

## Authorized files

CREATE:

- `backend/app/adapters/supporting_file_object_store.py` — private
  S3-compatible exact-key adapter; no list, public URL or policy behavior.
- `backend/app/adapters/supporting_file_scanner.py` — exact-object scanner
  adapter with only clean/unsafe/indeterminate safety outcomes.
- `backend/app/services/supporting_file_service.py` — application operations,
  final scope rechecks, idempotency and failure/reconciliation rules.
- `backend/app/repositories/supporting_file_unit_of_work.py` — one Session
  transaction owner only.
- `backend/app/services/supporting_file_reconciliation_service.py` — bounded
  reservation/object mismatch reconciliation; never promotes a partial object.
- `backend/tests/test_supporting_file_service.py` — reservation/upload/scan,
  idempotency and withdrawal tests.
- `backend/tests/test_supporting_file_security.py` — protected denial,
  cross-scope, unsafe input and no-public-URL tests.
- `backend/tests/test_supporting_file_reconciliation.py` — object/DB partial
  failure and scanner unavailable/retry tests.
- `backend/tests/test_supporting_file_object_store.py` — exact-key/no-list/
  no-public-url and metadata binding tests.
- `backend/tests/test_supporting_file_scanner.py` — scanner contract tests.

MODIFY:

- `backend/app/ports/supporting_file.py` — exact storage/scanner/UoW service
  protocols only.
- `backend/app/exceptions/supporting_file.py` — closed scanner-unavailable
  outcome only; no transport exception detail.
- `backend/app/core/config.py` — protected, separate object-store/scanner
  settings only.
- `backend/pyproject.toml`, `backend/requirements.txt`,
  `backend/requirements.production.lock`, `backend/uv.lock`,
  `backend/Dockerfile.production`, `docker-compose.production.yml` and
  `.env.example` — reviewed S3 SDK/container configuration and separately
  mounted runtime/scanner/reconciler principal configuration only.
- `backend/tests/test_production_topology.py` — accept either documented
  hash-lock generator while retaining the exact hash-lock requirement.
- `backend/app/repositories/supporting_file_repository.py` — reservation and
  reconciliation persistence, never commit.
- `backend/tests/test_supporting_file_contracts.py` — closed collaborator
  contract validation.

`backend/app/adapters/supporting_file.py` is **not** authorized and is removed
before Batch 2 acceptance; it was an incomplete provisional layout exposed by
the manifest reconciliation.

## Required behavior

The service creates a random immutable object key, reserves only a trusted
Organization/Project/Workspace scope, verifies size/type/digest after private
write, asks the scanner only for safety disposition, and makes an asset
available only after a clean result. Scanner timeout/unavailability is
fail-closed: asset remains quarantined and cannot be linked or retrieved.
Replacement is a new asset with immutable predecessor. Withdrawal never moves
or renames bytes. Object/DB failures are tracked for bounded reconciliation;
no public URL or client-supplied tenant scope is accepted.

## Evidence and stops

Focused tests must prove idempotent reserve/replay, exactly scoped private
operations, digest mismatch/retry, scanner deny/unavailable, object-write and
DB failure recovery, withdrawal and immutable key. Stop for a required
foreign canonical persistence call, external deployment credential, new
schema/migration, direct object URL, accepted-contract change, or any Batch
3+ work. `git diff --check`, static import and exact path checks are mandatory.

## Focused reconciled scanner-security boundary

The implementation-time IDS reconciliation authorizes these additional Batch 2
modifications only:

- `backend/app/models/supporting_file.py` and
  `backend/migrations/versions/e04300000001_supporting_files.py` — durable,
  Organization-bound scan attempts, provider result identity, replay fields,
  maximum-three-attempt guards and Organization-scoped idempotency;
- `backend/app/repositories/supporting_file_unit_of_work.py` — preserve the one
  authoritative transaction while exposing no new authority;
- `backend/tests/test_supporting_file_migration.py` and
  `backend/tests/test_supporting_file_transaction.py` — real schema, replay,
  retry, concurrency and atomicity evidence;
- `backend/tests/test_operations_config.py`,
  `backend/tests/test_operations_health.py`,
  `backend/tests/test_operations_security.py` and
  `backend/tests/test_production_topology.py` — secret-file validation,
  rotation/revocation-safe configuration and topology evidence only.

The already authorized scanner adapter, port, service, repository, core
configuration and deployment surfaces may change only for the exact principal
verifier, provider attestation, result recording and retry contracts. The Batch
4 internal route remains excluded, as do Evidence, Report, Memory, download and
frontend behavior.
