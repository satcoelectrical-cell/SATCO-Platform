# PATCH-059 Batch A Checkpoint

**Date:** 2026-09-30
**Batch:** A — persistence, canonicalization and cryptographic verification
**Candidate commit:** ed3460a6c0a2c729e3eb1f1c874ec385a83667f6
**Disposition:** PASS — implementation checkpoint, not delivery/release acceptance

## Baseline

Implementation lineage was reconciled before Batch A. The implementation branch descends directly from immutable accepted PATCH-058 candidate 8c37dcfa8235490408fb5d9c2c2d4e24857d149a through PATCH-059 accepted-governance baseline 2303f73dc51c28bbbad25ea9a6991a88a3a5e09f.

PATCH-058 candidate branch was not modified.

## Evidence

- Alembic sole head before Batch A: e05800000001.
- New migration: e05900000001, exact parent e05800000001.
- Disposable PostgreSQL only: container satco-p059-batch-a-pg at 127.0.0.1:55432, database satco_platform_patch02022_test.
- Real port 5432 was not used.
- Disposable upgrade to e05900000001: PASS.
- Disposable downgrade e05900000001 -> e05800000001 with empty PATCH-059 tables: PASS.
- Disposable re-upgrade to e05900000001: PASS.
- Runtime privilege probes: entitlement state SELECT/UPDATE true; activation INSERT true and UPDATE false; seat DELETE true as designed.
- PATCH-059 focused crypto/persistence tests: 17 PASS.
- Focused regression set including PATCH-058 auth persistence and discipline-package migration/registry: 53 PASS.
- Python compile: PASS.
- git diff --check: PASS.
- New unresolved Critical/Major/Minor findings: 0/0/0.

## Security properties established

Runtime contains Ed25519 verification only and no commercial private signing interface/material. Envelope and trust-store schemas are closed. Duplicate JSON members and noncanonical wire forms are rejected. Payload integers are bounded to I-JSON safe range. Package arrays require canonical sorted order. Signed payload digest is SHA-256 over bounded canonical bytes.

Persistence stores normalized entitlement state/digest and no raw entitlement/signature/private key. Activation history is append-oriented by service design and runtime grant excludes UPDATE. Migration downgrade refuses to discard populated PATCH-059 protected tables.

## Remaining work

This checkpoint does not implement entitlement activation services, anti-rollback locking, trusted-time recovery, seats service, package enforcement, API, frontend, release-sequence/recovery integration or final qualification. Those remain later batches.

**BATCH A: PASS / CHECKPOINT COMPLETE.**

This is not PATCH-059 delivery, release, closure or PATCH-060 authorization.
