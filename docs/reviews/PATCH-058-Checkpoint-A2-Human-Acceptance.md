# PATCH-058 Checkpoint A2 Human Acceptance

Status: HUMAN ACCEPTED / COMPLETE
Acceptance date: 2026-09-24
Accepted by: Human Engineering Authority

## Accepted bounded scope

Checkpoint A2 delivers the backend Authentication Token & Refresh-Session Foundation within accepted PATCH-058 Checkpoint A / IDS Batch B. It does not start PATCH-059 or PATCH-060 and does not expand into MFA enrollment/recovery, browser cookie/CSRF cutover, frontend memory-only auth, tenant-isolation remediation, bootstrap hardening, CI/security supply-chain work, or later session-administration UX.

Accepted implementation:

- short-lived HS256 access JWTs with the accepted 15-minute lifetime;
- mandatory access claims for subject, token type, issued-at, expiry, unique token ID, issuer, audience, User auth-version and server session binding;
- fail-closed access validation with no missing auth-version fallback;
- opaque refresh credentials using public selector plus high-entropy secret;
- dedicated HMAC-SHA-256 refresh verifier with no raw refresh secret persistence;
- server-authoritative refresh family/session creation;
- one-time transactional rotation with row locking and predecessor/successor lineage;
- consumed-credential reuse detection and family-wide revocation;
- current User, account, auth-version and selected/enabled Organization membership requalification;
- access invalidation through live bound refresh-session state;
- bounded security events for successful refresh rotation and refresh reuse detection;
- production validation for the dedicated refresh-verifier key;
- no new database migration.

## Qualification evidence

Final focused/regression qualification:

- 52 tests passed, 0 failed;
- Python compile qualification PASS;
- git diff check PASS;
- Alembic remained at sole head e05800000001;
- no legacy create_refresh_token caller remains;
- no silent payload.get("av", 1) fallback remains;
- Independent Review: Critical 0 / Major 0.

Warnings observed during qualification were existing deprecation warnings and were not classified as PATCH-058 A2 Critical or Major findings.

## Accepted candidate hashes

- backend/app/api/v1/routers/auth.py — 7e23a4873e600a9e08c4915c3632ec192dfdd6e8ae15b4e33fa6554aa2541ddd
- backend/app/core/config.py — a9248c1c12483d48fcfae565ccffa8fea423711604e8cbe04006e4eb4407446b
- backend/app/core/security.py — 07e48496d688ed14e86c26abfc465a4947a30a167aca01f62a983631428a3469
- backend/app/dependencies/auth.py — a4e9c48236b1b094810bd790ed85e3b000a56f42de00832dcb6713528599753c
- backend/app/schemas/token.py — f3939288bacd6311b37c4c61af7c609c4ba7b4c6337d81e441762b96f7b756d3
- backend/app/services/refresh_session_service.py — 7e48ce6a4e37540509d91971f6db761f8a403a4e47ac85e78167f6ff47c1d4fc
- backend/tests/test_auth.py — c7b7d5b484a98cecb3d9ae548e6999e883afe5e261661d777eab4f4e1942c8d9
- backend/tests/test_patch058_refresh_sessions.py — 26f140e54f16209427cff5e9d39db41e42b80e4a258bc70e440e056f2cd5e0ce
- backend/tests/test_operations_config.py — 61ee587215f66998595fe8e1a68ab4df8fa82f47b07fd99f85f4227ce5df853b

## Human decision

The Human Engineering Authority explicitly granted final A2 acceptance after the bounded implementation, correction of the security-event Major finding, rerun qualification, and Independent Review with no unresolved Critical or Major findings.

This acceptance authorizes closure delivery of exactly this A2 boundary. It does not authorize unrelated changes or later PATCH-058 checkpoints.
