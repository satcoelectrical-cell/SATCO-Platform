# PATCH-055 — Evidence Lineage / Workbench Corrective Reconciliation

Status: HUMAN ACCEPTED / COMPLETE
Date: 2026-09-17

Human acceptance recorded in conversation before implementation.

## 1. Confirmed contract conflict
EDS-055 owns Evidence lineage/replacement and requires supersession to identify a replacement Evidence, preserve predecessor/successor lineage, and render that lineage from canonical server-authorized relationships (`P055-EVW-06`). IDS-055 requires `GET /api/v1/projects/{project_id}/evidence-workbench` to compose lifecycle/lineage and safe reliance state.

Repository inspection confirms the existing Evidence transition accepts `replacement_evidence_id`, but the Evidence aggregate/persistence/read model does not retain that relationship. Therefore the accepted Workbench contract cannot be truthfully implemented from canonical server state without a bounded Evidence seam correction.

## 2. Normative correction
IDS-055 section 31.12 is narrowly superseded only for Evidence replacement-lineage persistence/read composition. PATCH-055 may modify the minimum existing Evidence files necessary to:

- persist the canonical replacement Evidence identity when an Evidence transition enters `superseded`;
- validate the replacement through the existing authorized Evidence scope before authoritative mutation;
- expose bounded, server-authorized predecessor/successor lineage for Workbench composition;
- preserve existing Evidence lifecycle authority, optimistic concurrency, audit/outbox, tenant isolation, and Technical Report/Memory provenance.

No Supporting File aggregate semantic change is authorized.

## 3. Persistence and migration boundary
Because canonical lineage must survive restart and be queryable, one additive forward-repair migration after `e05500000001` is authorized if required. It may add only the minimum Evidence replacement-lineage persistence needed by this reconciliation. It MUST NOT rewrite historical Evidence, infer/fabricate replacement identities for old rows, alter accepted Report/Memory provenance, or create a second Evidence lifecycle.

Historical Evidence without a persisted replacement remains truthfully `replacement not recorded`; it MUST NOT be guessed.

## 4. Workbench route
The already-accepted route remains unchanged:

`GET /api/v1/projects/{project_id}/evidence-workbench`

It MUST compose only currently authorized Project/Workspace data, including Evidence summaries, scanner-cleared Supporting File candidates, canonical lineage/replacement, safe accepted-Report reliance, and retention/hold/disposition state. Ordinary use requires no raw UUID entry. Protected/foreign data, hidden counts, storage locators, and unauthorized reliance are not disclosed.

## 5. Exact change boundary
Additional existing Evidence production files permitted only as needed for this correction:

- `backend/app/models/evidence.py`
- `backend/app/models/evidence_command.py`
- `backend/app/repositories/evidence_repository.py`
- `backend/app/services/evidence_service.py`
- `backend/app/schemas/evidence.py`

The existing PATCH-055 retention router/service/schema/repository files may compose the Workbench. The exact PATCH-055 test files may be extended. `backend/app/main.py` remains the router composition seam. No other existing production file is authorized without another reconciliation.

## 6. Qualification and invariants
`P055-EVW-01..10` MUST become executable behavioral qualification, especially `P055-EVW-06`. Qualification MUST prove canonical successor/predecessor truth, replacement authorization, stale-write protection, cross-Organization non-disclosure, no raw-ID ordinary workflow, no lifecycle/provenance rewrite, and truthful behavior for legacy rows lacking recorded replacement.

The frozen total remains 48 vectors. Existing RET/HLD/XRC/SEC/UX semantics remain unchanged. Full backend/frontend regression, typecheck, build, Alembic sole-head and disposable upgrade qualification remain required before final acceptance.

## 7. Explicit non-authority
This reconciliation does not authorize physical purge, production/customer database mutation, destructive migration, stage, commit, push, deploy, PATCH-056 work, or changes to accepted ADR-028 / EDS-055 product semantics.

## 8. Human acceptance
Human Architecture/Engineering Authority accepted this bounded corrective reconciliation on 2026-09-17. Implementation authority is limited to the exact boundary above and Checkpoint D qualification; no stage/commit/push/deploy authority is granted.
