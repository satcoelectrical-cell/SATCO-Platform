# PATCH-058 Checkpoint D Implementation Status

Status: IMPLEMENTATION ADVANCED / BLOCKED PENDING MANDATORY TRIVY EVIDENCE AND HUMAN HIGH-FINDING DECISION
Date: 2026-09-26

## Implemented boundary

- repository-controlled ordinary qualification workflow;
- separate security-evidence workflow;
- separate protected signing workflow with OIDC permission only in the Human-protected job;
- pinned security-tool version contract;
- vulnerability-gate implementation;
- machine-readable in-toto/SLSA-compatible provenance generator;
- supply-chain negative tests;
- dependency remediation for fixable findings discovered during D qualification.

## Qualification completed

- workflow YAML parse: PASS;
- supply-chain focused tests: 15 passed, 0 failed;
- frontend typecheck: PASS;
- `uv lock --check`: PASS;
- `git diff --check`: PASS;
- staging: EMPTY;
- ordinary workflows have no OIDC write authority; protected signing workflow alone has `id-token: write`;
- backend production image build: PASS (`sha256:5f9258ad9330bfa951d4d567d76892c39da524fcc336772da3a3f16c19a4b503`).
## Security-scan findings and blockers

After bounded Vitest remediation, `npm audit --audit-level=high` reports 0 findings at every severity.

Initial `pip-audit` identified fixable findings in `cryptography==49.0.0` and test-only `httpx2==2.9.1` / `httpcore2==2.9.1`. The D implementation reconciled the lock to `cryptography>=50.0.0` (resolved 50.0.1) and test-only `httpx2==2.12.0`.

After remediation, `pip-audit` reports one remaining finding: `ecdsa==0.19.2`, `PYSEC-2026-1325`. External advisory evidence classifies it High and reports no fixed release. Repository inspection confirms SATCO JWT configuration is HS256 and no ECDSA signing/ECDH path is present in the application surface. Under the accepted PATCH-058 plan this remains a High finding and therefore cannot be silently accepted by AI; any exception must use the Human-governed, exact-artifact-digest-bound exception process.

The pinned Trivy image is locally available, but Trivy vulnerability-DB retrieval is blocked by registry HTTP 403/network behavior in the local environment. The workflow now supplies explicit GHCR and public-ECR DB repositories; CI evidence is still required. Syft generated a CycloneDX backend SBOM successfully (2,940 components). Semgrep 1.178.0 scanned 434 application targets with 0 findings and 0 parser errors. Gitleaks 8.28.0 scanned 147 commits; its sole initial match was the already-reviewed PATCH-051 prose false positive recorded by exact fingerprint in `.gitleaksignore`, after which the governed full-history scan passed with 0 leaks. Cosign remains intentionally reserved for the Human-protected signing workflow and has not been exercised as signing authorization has not been granted.

## Governance disposition

Checkpoint D is NOT READY for Human acceptance yet. No exception, signing authorization, release approval, Checkpoint E progression, commit, push, deployment, PATCH-059 or PATCH-060 progression is implied by this status.
## Qualification update — 2026-09-27 Human High-exception decision

Human Authority explicitly approved a bounded 30-day exception for the unresolved High findings of the exact backend candidate artifact `sha256:e0bb4511435f35994948517b5048e50568d7f7b93f141a3ba02f0d45c7bf40a0`.

The governed exception file contains 10 distinct source/finding identities: one `pip-audit` PYSEC identity and nine Trivy CVE identities. Approval timestamp is `2026-09-27T07:58:25Z`; expiry is `2026-10-27T07:58:25Z`. The exception is exact-artifact-bound and does not transfer to a rebuild or changed artifact.

The security workflow was reconciled to validate the governed exception file and pass it explicitly to the fail-closed vulnerability gate. Exception evidence is also included in provenance inputs and uploaded security evidence.

Local exception validation: PASS. Supply-chain focused/negative tests: 15 passed, 0 failed. Vulnerability gate with the Human-approved exception set: PASS, 164 total findings, 0 blocking findings, 46 accepted finding occurrences mapping to 10 distinct approved identities. No Critical exception exists.
Semgrep 1.178.0 rescanned 434 application targets with 0 findings and 0 parser errors. Gitleaks 8.28.0 full-history qualification scanned 147 commits with 0 leaks; the local linked-worktree harness required read-only mounting of the parent Git metadata so the container could resolve the worktree pointer. This is a local harness detail and is not needed by the normal GitHub Actions checkout topology.

Syft-generated backend and frontend CycloneDX evidence was bound and independently verified against the exact artifacts. Evidence digests are backend SBOM `sha256:b4662368a09c645c52f08cc99181a33b4d3d7d20ed29341e789e74506fe53f5c`, frontend SBOM `sha256:02e78204f49003c2051fddc87e3b76a464cdbe89e353697e826620ef574c9a3e`, and locally generated/verified provenance `sha256:7f751a8d451f056cbaaeea670b204277eb4271e6964bc83050ecb4483a8db724`.

Security workflow YAML parse: PASS using the host Ruby YAML parser. `git diff --check`: PASS. Staging remains empty.

Checkpoint D has not received Human checkpoint acceptance. Privileged signing authorization remains separate and has not been granted. No signing, release approval, Checkpoint E progression, commit, push, deployment, PATCH-059 or PATCH-060 progression is implied by this update.
## Independent D review follow-up

Independent review found and resolved two exception-evidence continuity defects before checkpoint acceptance: the protected signing workflow did not initially include the Human exception file in provenance re-verification, and it did not revalidate exception digest/active-time status at signing time. Both paths are now fail-closed and exact-artifact-bound.

A regression test now asserts exception binding in both the security-evidence and protected-signing workflows. Updated supply-chain focused/negative suite: 16 passed, 0 failed. All three D workflow YAML files parse successfully. No mutable-tag GitHub Action reference was found; action references are commit-SHA pinned. OIDC `id-token: write` remains isolated to the Human-protected signing job.

This supersedes the earlier 15-test count only for the latest D qualification state. Checkpoint D still requires explicit Human checkpoint acceptance before any Checkpoint E progression.
## Signing-authorization negative qualification — 2026-09-27

Static negative qualification of the protected signing topology is complete without exercising privileged signing authority. The signing workflow has no `push` or `pull_request` trigger, requires `workflow_dispatch`, and is bound to the `patch058-protected-release` Environment. OIDC `id-token: write` appears only once and only inside that protected signing job.

Negative contract checks confirm fail-closed bindings for exact source revision, exact backend artifact digest, active Human High-exception validation, provenance binding of the exception evidence, signer certificate identity, GitHub OIDC issuer, repository and workflow SHA. Supply-chain regression tests remain 16/16 PASS after strengthening these signing assertions; all three D workflow YAML files parse successfully.

No real cosign signing or attestation was executed because privileged signing authorization is a separate Human authority under Implementation Plan §43. This qualification therefore proves the repository-side authorization/identity/digest protections without impersonating or consuming that Human authority.

Checkpoint D remains pending explicit Human checkpoint acceptance. Signing authorization, release approval and Checkpoint E progression remain ungranted.