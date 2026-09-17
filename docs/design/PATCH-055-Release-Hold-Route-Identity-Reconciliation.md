# PATCH-055 — Release Hold Route Identity Reconciliation

Status: HUMAN ACCEPTED / COMPLETE

## Conflict
IDS-055 exposes `POST /retention/{subject_kind}/{subject_id}/holds/{hold_id}/release`.
The accepted Hold Expected-Version Reconciliation freezes release concurrency against the current active Hold revision version, but the Checkpoint-B service signature does not receive the route `hold_id`.

## Required binding
The route `hold_id` is a protected stable aggregate identity and MUST be bound inside the governed service transaction, not inferred after mutation.

For `ReleaseRetentionHold`:
- add `hold_id: UUID` to the service command boundary;
- include `hold_id` in the idempotency request digest;
- after authorization and before idempotency replay/current mutation, require the referenced stable Hold identity to belong to the authorized subject;
- on current mutation require `active.hold_id == hold_id` AND `active.version == expected_version`;
- on replay require the safe historical released revision stable Hold identity equals the requested `hold_id`;
- mismatch is `conflict` only after the subject has already passed protected authorization;
- no lookup may disclose a foreign/forbidden Hold before subject authorization.

## Boundary
This is a narrow Checkpoint-C transport-to-service binding correction. No schema/model/migration/frontend change, no physical disposition, and no weakening of the previously accepted Hold version semantics is permitted.

Human acceptance recorded in conversation before implementation.
