# PATCH-055 — Active Hold Version Projection Reconciliation

Status: HUMAN ACCEPTED / COMPLETE

## Conflict
The accepted Release Hold concurrency contract requires `ReleaseRetentionHoldRequestV1.expected_version` to equal the current active Hold revision version. The accepted retention-state projection exposes `active_hold_id` but not that revision version, so the Evidence Workbench cannot compose a correct Human release command without guessing or substituting the unrelated retention-record version.

## Required binding
Add optional `active_hold_version` to `RetentionGovernanceHeadV1` and `RetentionStateResponseV1`. When a current active Hold is present it MUST equal that Hold revision's positive `version`; otherwise it MUST be null.

The server composes this field from the already-authorized current Hold row. It is read-only projection data, not a new authority source. `ReleaseRetentionHoldRequestV1.expected_version` continues to mean exactly the current active Hold revision version.

The Evidence Workbench may enable Release Human Hold only when both `active_hold_id` and `active_hold_version` are present, and MUST send that exact version. Success still requires an authoritative reread; stale state remains conflict.

## Boundary
This reconciliation changes no Hold semantics, lifecycle, authorization, database schema, migration, retention-record version meaning, Evidence/Supporting File state, Report/Memory provenance, physical disposition, or purge behavior. No raw UUID entry is introduced.

Human acceptance recorded in conversation on 2026-09-17 before implementation.
