# PATCH-043 Batch 4 Authorized File Manifest

## Authority

Batch 3 is accepted. This manifest authorizes only S13–S14 request-scoped
composition, protected read/download application behavior and thin transport.

## Production boundary

CREATE:

- `backend/app/dependencies/supporting_file.py` — request-scoped composition of
  the accepted Supporting File UoW, object/scanner adapters, current-scope
  policy and trusted Human/scanner principals; no transport decisions.
- `backend/app/api/v1/routers/supporting_files.py` — thin authenticated upload,
  list, status, active/historical download, withdrawal and private scanner
  result translation only.

MODIFY:

- `backend/app/core/config.py`, `docker-compose.production.yml` — complete the
  already accepted secret-file object/scanner composition inputs only.
- `backend/app/ports/supporting_file.py`, `backend/app/schemas/supporting_file.py`,
  `backend/app/repositories/supporting_file_repository.py`,
  `backend/app/services/supporting_file_service.py` — bounded current reads,
  encrypted continuation, exact-object download, historical accepted-basis
  authorization, protected results and no-commit persistence support.
- `backend/app/api/v1/routers/evidence.py` — one Evidence-owned link route only.
- `backend/app/api/v1/routers/technical_reports.py` — one accepted-Report
  Evidence candidate and historical file download routes only; Report
  authorization remains canonical.
- `backend/app/schemas/technical_report.py` and CREATE
  `backend/app/adapters/technical_report_evidence_source.py` — exact Evidence
  V1/V2 HTTP serialization and server-composed current Evidence provenance;
  no client-authored canonical locator.
- `backend/app/main.py` — register the Supporting File router exactly once.

## Test boundary

CREATE `backend/tests/test_supporting_file_api.py`. MODIFY focused Supporting
File service/security/object/config/topology tests and exact Evidence/Report API
tests only where needed for all accepted routes, trusted context, token,
headers, protected failures and prohibited surfaces.

## Required evidence

All authenticated routes; server-derived Organization; exact Project/Workspace
intersection; list order and max 50 visible items; opaque authenticated
15-minute actor/scope/query-bound continuation anchored to last evaluated row;
current authorization before status/content; available-only active download;
accepted-basis plus current scope authorization for historical download;
private exact-object HEAD/open digest parity; attachment, `nosniff`, private
`no-store`; scanner credential constant-time authentication and scanner-only
authority; payload-free protected/invalid/unavailable outcomes; no totals,
storage key, full digest, uploader or exception leakage.

## Stop and exclusions

Stop for router-owned repository/Session/UoW/policy, direct object URL, bucket
listing, inline rendering, client-derived Organization/actor, unbounded reads,
new Evidence/Report/Memory authority, schema/migration change or Batch 5+ work.
Frontend/UI, AI/OCR/search, global file manager, mutable file bytes and every
deferred capability remain excluded.
