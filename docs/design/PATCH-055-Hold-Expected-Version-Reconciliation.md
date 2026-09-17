# PATCH-055 — Hold Expected-Version Reconciliation

Status: HUMAN ACCEPTED / IMPLEMENTATION-AUTHORIZED
Date: 2026-09-14

## 1. Purpose

This reconciliation closes one implementation-blocking ambiguity in the
Human-accepted PATCH-055 retention-governance contract.

It does not expand PATCH-055 scope and does not alter the accepted Evidence,
Supporting File, Technical Report, Organizational Memory, retention, export,
recovery, authorization, or Human-authority boundaries.

## 2. Authority

Authoritative baseline remains:

- ADR-028 — accepted;
- EDS-055 — accepted;
- IDS-055 — accepted, including sections 31.1–31.13;
- Implementation Plan 055 — accepted;
- PATCH-055 Checkpoint B — Human authorized.

The Human Authority explicitly approved this bounded reconciliation on
2026-09-14.

## 3. Ambiguity

Both `PlaceRetentionHoldRequestV1` and
`ReleaseRetentionHoldRequestV1` carry `expected_version`.

The accepted contract requires stale/concurrent hold mutations to fail with
`conflict`, while Hold history is independently append-only and revisioned.

The accepted documents did not explicitly bind each DTO's `expected_version`
to one authoritative concurrency token.

## 4. Exact reconciliation

### 4.1 Hold placement

For `PlaceRetentionHoldRequestV1`:

`expected_version` means the version of the current RetentionRecord head for
the canonical authorized subject.

A Hold may be placed only when a current RetentionRecord exists.

The request succeeds only when:

- the caller passes the PATCH-055 governance-mutation authorization predicate;
- the canonical subject remains authorized;
- the current retention head exists;
- its version equals `expected_version`;
- no current active Hold already exists.

A successful placement creates:

- a new stable `hold_id`;
- Hold revision `version = 1`;
- `status = active`;
- `predecessor_row_id = NULL`.

### 4.2 Hold release

For `ReleaseRetentionHoldRequestV1`:

`expected_version` means the version of the current active Hold revision.

The request succeeds only when:

- the caller passes the PATCH-055 governance-mutation authorization predicate;
- the canonical subject remains authorized;
- a current active Hold exists;
- its Hold revision version equals `expected_version`.

A successful release:

- closes the active revision in the same transaction;
- creates a new revision using the same stable `hold_id`;
- increments the Hold revision version by exactly one;
- references the active revision through `predecessor_row_id`;
- preserves original placement facts;
- records release actor, time, and release rationale;
- sets the successor status to `released`.

## 5. Concurrency semantics

Placement concurrency is protected by both:

- current retention-head expected-version verification; and
- the existing partial unique active-Hold constraint.

Release concurrency is protected by the current active Hold revision version.

A stale or concurrent losing mutation returns the existing PATCH-055
`conflict` outcome and requires an authorized reread before a new request.

No mutation silently merges Human governance decisions.

## 6. Invariants

This reconciliation does not authorize:

- byte deletion or purge;
- Evidence lifecycle mutation;
- Supporting File standing mutation;
- Technical Report provenance mutation;
- Organizational Memory provenance mutation;
- automatic Hold placement or release by AI/background expiry;
- route/frontend/Checkpoint-C implementation;
- stage, commit, push, deployment, or production/customer DB mutation.

Hold placement produces `blocked_by_hold`.

Hold release recomputes eligibility from the authoritative current retention
head and does not itself approve disposition.

## 7. Implementation authority

Checkpoint B implementation may now use the exact semantics in section 4.

This authority is limited to the already Human-approved Checkpoint B boundary.

**PATCH-055 Hold Expected-Version Reconciliation: HUMAN ACCEPTED / COMPLETE**
