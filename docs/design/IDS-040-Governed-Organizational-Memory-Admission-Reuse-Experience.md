# IDS-040 — Governed Organizational Memory Admission & Reuse Experience

Status: ACCEPTED.

## Exact contracts

PATCH-040 reuses the accepted PATCH-039 `TechnicalReportAccepted` response and PATCH-034 endpoints without modification:

- `POST /organizational-memory/admissions` with exact report UUID, accepted aggregate version, accepted snapshot digest, Workspace, optional Project, non-empty Human admission rationale, non-empty Human authority rationale, empty `audience_actor_ids`, and zero-to-32 normalized reuse restrictions. Correlation and idempotency UUID headers are generated per explicit submission.
- `GET /organizational-memory` with server-authorized selected Workspace/Project, page size 20, and accepted bounded active-list semantics.
- `GET /organizational-memory/{memory_id}?include_provenance=true&reuse_intent=true` for deliberate consultation.

The frontend models exact active summary, admitted projection, qualification/content, safe provenance, rationale, restrictions, and closed outcomes. `protected_not_found` maps to one neutral protected state; `invalid_request` to neutral invalid state; `unavailable` to neutral unavailable state; duplicate/idempotency/version/standing outcomes to conflict without internal detail.

Normal workflow contains selectors and links, never editable Project/Workspace/Organization IDs, Report UUID, Memory UUID, canonical provenance, source digest, or idempotency payload.

## Trust and verification matrix

Evidence must prove: draft Reports cannot expose admission; exact accepted response fields bind admission; both Human rationales and confirmation are required; empty audience is fixed; no automatic admission; protected/foreign/revoked source collapses safely; active lists use selected authorized context; exact detail requests provenance plus reuse intent; limitations/restrictions/source attribution remain attached; dashboard deep-links exact Memory; no lifecycle/AI/Evidence routes; accessibility, responsive layout, no fake production data, focused and adjacent regressions, build/typecheck, secrets/scope checks, and diff integrity pass.

No migration or backend domain change is authorized.
