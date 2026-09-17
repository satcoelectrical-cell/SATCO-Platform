# PATCH-055 — Disposition Outbox Identity Reconciliation

Status: HUMAN-AUTHORIZED RECONCILIATION CANDIDATE
Scope: Checkpoint B only; no Checkpoint C/D expansion.

## Trigger

The DB-backed historical-idempotency test reproduced a PostgreSQL unique violation when a second Human disposition decision was recorded against the same current RetentionRecord.

The accepted IDS freezes `retention_outbox` uniqueness as `(aggregate_kind, aggregate_id, aggregate_version, event_type)`. Current implementation emits every `RETENTION_DISPOSITION_DECISION_RECORDED` event as aggregate kind `retention_record`, aggregate id = current RetentionRecord id, and aggregate version = current RetentionRecord version.

Because disposition decisions are append-only Human decision rows and do not replace/version the RetentionRecord, a second valid decision produces the same outbox uniqueness tuple.

## Frozen contracts preserved

- Do not weaken or drop `uq_retention_outbox_event`.
- Do not rewrite accepted RetentionRecord history.
- Do not add physical purge/disposal behavior.
- Keep Human disposition decisions append-only and attributable.
- Keep audit/outbox/idempotency in the same transaction.
- Keep safe-metadata-only outbox payloads.

## Reconciled interpretation

For `RETENTION_DISPOSITION_DECISION_RECORDED`, the event aggregate is the newly appended `RetentionDispositionDecision`, not the unchanged RetentionRecord head.

Therefore the event identity is:

- `aggregate_kind = retention_disposition_decision`
- `aggregate_id = RetentionDispositionDecision.id`
- `aggregate_version = 1`
- `event_type = RETENTION_DISPOSITION_DECISION_RECORDED`

The RetentionRecord remains referenced by the decision row and current state projection. Its own version is not synthetically incremented merely to manufacture outbox uniqueness.

This interpretation preserves the frozen outbox unique constraint while allowing multiple append-only Human decisions. It also aligns aggregate identity with the domain fact that actually came into existence in the transaction.

## Implementation boundary

Checkpoint-B correction is limited to the disposition event call in `backend/app/services/retention_service.py` plus focused tests. No migration/model/constraint change is required.

Historical idempotency replay must prove: Decision 1 succeeds; Decision 2 succeeds on the same RetentionRecord; replay of Decision 1 with the same key/digest returns its prior safe logical result after current authorization.

No stage, commit, push, deploy, production/customer DB mutation, Checkpoint C/D work, or PATCH-056 work is authorized by this reconciliation.

## Human acceptance

Human acceptance received explicitly in chat after review of the reconciled interpretation.

Accepted status: HUMAN ACCEPTED / COMPLETE.

Implementation may now apply only the bounded Checkpoint-B correction described above and qualify it on disposable PostgreSQL.
