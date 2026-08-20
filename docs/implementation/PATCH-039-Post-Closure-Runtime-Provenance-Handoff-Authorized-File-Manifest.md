# PATCH-039 Post-Closure Runtime Provenance Handoff — Authorized File Manifest

Status: **ACCEPTED / BOUNDED** under standing Human post-closure reconciliation authority.

Historical PATCH-039 delivery `80d006e5232e154502a36baf46b9b40be7c3504c`
and closure `af4e86f6b62a2aad45a8a1956313b4474d9a7e5b` remain immutable.

## Exact boundary

- MODIFY `backend/tests/test_technical_report_api.py` — prove the static
  Capture-candidate route resolves before the UUID report-detail route and
  returns an authorized exact-scope candidate.
- MODIFY `frontend/src/test/reports.test.tsx` — prove contextual query state
  triggers the exact Project/Workspace candidate read, selects the Capture,
  and requires no raw-ID field.
- MODIFY `frontend/src/test/workflows.test.tsx` — prove the Capture-specific
  Project action carries Project, Workspace, and Capture context.
- CREATE `docs/implementation/PATCH-039-Post-Closure-Runtime-Provenance-Handoff-Authorized-File-Manifest.md`.
- CREATE/MODIFY `docs/reviews/PATCH-039-Post-Closure-Runtime-Provenance-Handoff-Reconciliation.md`
  — append-only reproduction, diagnosis, review, runtime evidence, delivery,
  and closure record.

No production source change is authorized or required: the delivered source
already contains the accepted route, adapter, frontend handoff, and protected
authorization behavior. Runtime restart/reload of the existing bind-mounted
backend is operational remediation, not a semantic or persistence change.

## Evidence and stop conditions

Require focused backend/frontend PASS, Technical Report and PATCH-038 adjacent
regression PASS, build/type/static and scope/fake-data PASS, independent
re-review PASS, and real browser runtime PASS. Stop before delivery if browser
runtime validation is unavailable. Prohibit raw-ID UI, hard-coded Human data,
authorization weakening, database edits, foreign persistence access,
PATCH-040, and unrelated files.
