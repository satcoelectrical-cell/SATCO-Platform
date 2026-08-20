# PATCH-039 Batch 1 Authorized File Manifest

Batch: Contextual Capture Provenance Foundation (S01–S02). Preparation,
manifest acceptance, and implementation authority are granted under standing
Human authority.

## Exact Authorized Boundary

- MODIFY `backend/app/schemas/technical_report.py` — strict candidate DTO/list.
- CREATE `backend/app/adapters/technical_report_capture_source.py` — bounded
  application adapter over canonical Capture service; deterministic provenance.
- MODIFY `backend/app/api/v1/routers/technical_reports.py` — one authenticated
  thin candidate route and protected translation.
- CREATE `backend/tests/test_technical_report_productization.py` — contract,
  canonical-boundary, scope, lifecycle, digest, bounds, and route evidence.
- MODIFY `backend/tests/test_technical_report_api.py` — reconcile the exact
  PATCH-032 route allow-list with the single accepted PATCH-039 read route.

No migration, model, repository, UoW, Report mutation, Capture persistence,
frontend, Memory, AI, Context/Evidence, or later-batch surface is authorized.

Prerequisites are accepted IDS-039 and existing PATCH-028/PATCH-032 services.
Acceptance requires deterministic exact provenance, one bounded canonical list
call, no foreign persistence import, protected all-or-nothing failure, focused
tests, adjacent Capture/Report regressions, static/import/scope checks, and
`git diff --check`. Stop for any accepted contract change, migration, direct
Capture persistence, partial disclosure, or out-of-boundary production file.
