# PATCH-058 Checkpoint B1 Human Acceptance

Status: HUMAN ACCEPTED / COMPLETE
Acceptance date: 2026-09-24
Accepted by: Human Engineering Authority

## Accepted bounded scope

Checkpoint B1 delivers the MFA Security Primitives & Authentication Throttling sub-slice within accepted PATCH-058 Checkpoint B / IDS Batch C-D. It does not declare the whole Checkpoint B complete and does not start PATCH-059 or PATCH-060.

Accepted implementation:

- RFC 6238 TOTP support using the accepted six-digit, 30-second, plus/minus one-window profile;
- AES-256-GCM protection of persisted TOTP secret material with explicit key identity/version and previous-key validation for controlled rotation;
- TOTP enrollment and verification with persisted replay prevention;
- ten high-entropy recovery codes with non-reversible HMAC verifiers and single-use consumption semantics;
- Organization MFA policy evaluation supporting mandatory administrator MFA and Organization-configurable engineer/member policy;
- PostgreSQL-backed authentication/MFA throttling using normalized credential identity and network context;
- safe threshold security-event emission;
- production configuration validation for TOTP encryption, recovery-code verifier and authentication-throttle key material;
- direct pyotp dependency and reproducible dependency-lock updates;
- bounded A2 test-harness corrections so protected API tests create a real server-side refresh session and session-bound access JWT rather than weakening accepted A2 authentication semantics;
- bounded production-readiness test configuration updates for the new B1 security keys;
- bounded historical migration-test corrections so PATCH-055/PATCH-056 boundary tests recognize the current e05800000001 repository head while still exercising their historical migration boundaries;
- no new database migration and no production-authentication weakening.

## Qualification evidence

Final qualification evidence:

- non-migration backend regression: 2091 passed, 0 failed;
- isolated migration-mutating suite: 75 passed, 0 failed;
- focused corrected readiness/MFA qualification: 31 passed, 0 failed;
- Technical Report real-auth plus B1 qualification: 14 passed, 0 failed;
- Python compile qualification PASS;
- uv lock --check PASS;
- git diff --check PASS;
- Alembic current repository head remains e05800000001;
- Independent implementation review findings corrected before final qualification; unresolved Critical 0 / Major 0.

Warnings observed during qualification were existing/deprecation or serializer warnings and were not classified as PATCH-058 B1 Critical or Major findings.

## Accepted candidate hashes

- backend/app/api/v1/routers/auth.py — d7571c400badaffd9b28b8ddb44f402db2ce241abc15cd6f9554d1ce178d2b52
- backend/app/core/config.py — 66e780a77a4bd2d59dee57d8a7059756cabf6a40a8e96d93fcd8acadcf96a0d8
- backend/pyproject.toml — dc9ba3d0d8f29516b236de3c14c1e2801bcf707f416cbee4afa296b0b7967a08
- backend/requirements.production.lock — cb5d2b557acd221c66a646445dedd9fbde1c22d2d5297b00ec2614a0b35c3d9d
- backend/requirements.txt — fbb7037079e8d2f698c44a604606a94a755bf14593d26685073acdc737bf5e6c
- backend/uv.lock — 937a9556b1280fba76f2e2a07a349b10ff3c7fce80099730ddf994478ebdc5b7
- backend/app/schemas/mfa.py — cf22cf8b2825fa99a1189232134a481ba7230a4e153b15c71ceb8948616124e6
- backend/app/services/auth_throttle_service.py — 25969d2fab2ba576c05851f5239ee897494863c088ad4583b2f2d9b480d2cd0c
- backend/app/services/mfa_service.py — ab745bedbd899cd3ecfd9aedcd729c0f84d97477a48b5ad58ba0c84b17b5bc00
- backend/tests/test_patch058_mfa_foundation.py — 91e8b376a29a652cca354c8fffd6a248ebf3297d2185587360b69b56126c33f0
- backend/tests/test_engineering_knowledge_graph_api.py — 65f0e1d27d0a1c07b858db7d98eda45c8c51f0aa9884d51ca6ff48b82b4da794
- backend/tests/test_onboarding_api.py — 59ef07b846d60a97c4315fd1430d58dd36adf4e5e87ad9941d7659dfbe2f75ad
- backend/tests/test_operations_config.py — 90ee25a069d1231622f7df51a32fa8149ab71c7dd4328412e1d5219030d11d4c
- backend/tests/test_operations_health.py — c96bde49f61fc06ca3f45995cf3d610c939651ab5e06f7bbc8c2c5a6d05b677e
- backend/tests/test_organizational_memory_api.py — edb62c52fe30fcb73935052f66cebc85c21b8cfd8510a0ed03295396b7a44962
- backend/tests/test_patch055_retention_migration.py — f868354bce5de5fbde56f3ab6d03be05ce93f3224a67f91bed4442f093937108
- backend/tests/test_patch056_engineering_performance_migration.py — 07fe982c26e533c9cbe9225b116c5c540af718ba343828f33c4c6a5c8d6ebead
- backend/tests/test_technical_report_api.py — 1e7c0e1afbde170ac8c405430484a571a5350da7f127988a2365e6baab5b85e3

## Human decision

The Human Engineering Authority explicitly accepted B1 after the bounded implementation, security corrections, A2-compatible harness corrections, full non-migration regression, isolated migration qualification, and final zero-failure checks.

This acceptance authorizes closure delivery of exactly this B1 boundary. It does not authorize unrelated changes, the remainder of Checkpoint B, PATCH-059, or PATCH-060.
