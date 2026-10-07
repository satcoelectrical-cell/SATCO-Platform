# PATCH-059 Batch E — Qualification Evidence (DRAFT)

**Status:** ADR-032 AUTHORIZED REMEDIATION IMPLEMENTED 2026-10-03; Critical 0 open, Major 7 identified (all 7 have worktree remediation, including MAJ-05/06, pending fresh independent re-review), Minor 3 identified (2 have worktree remediation, 1 remains outside this bounded amendment). SECURITY GATE STOPPED; not ready for Human Checkpoint E acceptance and not a checkpoint closure.
**Branch:** `patch-059-implementation`
**HEAD:** `a1918c89bc547d814a0f176ef20688b03fd99997`
**Working tree:** dirty; preserve all existing Batch E and historical-test edits.
**Database:** disposable `satco-p059-batch-e-pg`, `127.0.0.1:55432`, `satco_platform_patch02022_test`; real port 5432 not used.
**Alembic:** sole head/current revision `e05900000002`.

## Current verified qualification

- Fresh full backend suite on the exact final authorized worktree: **2519 passed, 4427 warnings**, zero failures, 231.57 seconds.
- Full frontend suite: **217 passed**, 37 files.
- Frontend TypeScript and production build: PASS; pre-existing chunk-size advisory.
- Expanded PATCH-059 security/recovery qualification: **235 passed, 30 warnings**.
- Final ADR-032 release/recovery/configuration focused rerun: **99 passed, 2 warnings**; the preceding release-only hardening rerun was **14 passed, 2 warnings**.
- Focused Batch E recovery test file before this continuation: **22 passed**, 2 warnings.
- Complete operations unit suite: **46 passed** (including **22** PATCH-058 release-dossier tests).
- `git diff --check`, Python compilation, `bash -n` of backup/preflight/restore scripts: PASS.
- No Commit, Push, Tag, release, or Batch F execution.

## Security review gate — OPEN

Ed25519 Recovery Anchor, public-only Runtime trust, separately governed expected Anchor SHA-256, replay rejection, operation-path reconciliation, and backup/restore controls have implementation and test evidence. The Codex review reported Critical replay and Major findings remediated, but its post-remediation independent re-review result was not delivered before usage limits. **Do not assert Critical/Major = 0 until a new independent review explicitly verifies the final worktree.**
## Remaining acceptance prerequisites

1. Independent security/implementation review of the final changed worktree, including replay, signer custody, digest deployment, operation-path denial, backup atomicity and restore reconciliation; record explicit Critical/Major/Minor findings and disposition.
2. Verify the operational dependency on PATCH-058 release-signature/provenance validation and Human release approval. Local manifest shape and SHA-256 reference checks alone are not cryptographic proof of release authorization.
3. Classify warnings relevant to Batch E; existing FastAPI/SQLAlchemy deprecations and React act/build advisories are recorded but not silently dismissed.
4. Confirm production recovery custodian, key custody, digest deployment, archival and dual-control arrangements with Human Authority before any real deployment.
5. Only after zero open Critical/Major findings, prepare the actual Checkpoint E for explicit Human Acceptance. No Batch F before that gate.

**Historical test correction:** the Batch E CLI `promote` test now supplies the required `--expected-anchor-sha256`; production verification remains mandatory.

## Follow-up code inspection (non-independent)

- Reviewed `recovery.py`, `commercial_entitlement.py`, `runtime_entitlement.py`, `operations.py`, `release.py`, `backup.sh`, `restore-verify.sh`, and production Compose wiring. Runtime verifier loads a separately pinned Anchor digest and Ed25519 public trust; recovery signing remains in the separate CLI/backup path.
- Confirmed targeted negative tests for old valid Anchor replay, revoked recovery key, exact restore mismatch, and recovery private-key custody. These tests passed within the recorded suites.
- Inspected PATCH-058 release manifest consumption and preflight: local code checks closed manifest structure, reference/digest shapes, sequence and migration head. The examined code does **not** itself cryptographically verify the release signature or independently establish the referenced Human release approval. This is an **open release-authority evidence dependency**; verify a trusted external PATCH-058 release gate and immutable artifact custody before production acceptance. Do not silently treat SHA-256-shaped evidence references as verified approvals.
- This inspection is by the implementation/qualification assistant, **not an independent security reviewer**. Critical/Major closure remains unasserted pending an independent final-worktree review.

## PATCH-058 authority reconciliation

- The immutable `patch-058-closed` tag exists at `a15daa0` and establishes PATCH-058 **foundation closure**, not that any particular PATCH-059 commercial deployment has already been signed or approved.
- `.github/workflows/patch058-sign-release.yml` defines a protected Human-reviewed GitHub Environment, exact-source/evidence checks, and a protected signing workflow. The presence of this workflow is **design/implementation evidence only**, not proof of a successful signing run for the present release.
- Historical PATCH-058 Checkpoint E implementation-status documents recorded signing/approval as pending at that time; do not misread them as current PATCH-058 closure status.
- Before a real commercial release, the exact candidate must have an independently verifiable successful protected signing run, signature-verification evidence, attributable Human release approval, immutable release dossier and deployed manifest binding. Runtime's shape checks are not a replacement.
- **Disposition:** Batch E qualification can be recorded without claiming that a real production release has been authorized; production release readiness remains conditional on per-release evidence. Independent security review and Human Checkpoint E acceptance remain pending.

## Preliminary security finding — restore verification order (OPEN)

**Observation:** `ops/scripts/restore-verify.sh` checks the archived Anchor's SHA-256 before database restore, but runs the Ed25519/trust-store verification of the live Anchor via `patch059-commercial-recovery.py verify` **after** `patch059-libpq.py restore`. Thus a digest-pinned but otherwise invalid/revoked Anchor may cause an isolated restore target to be modified before the cryptographic/trust failure is reported. The script does require an empty, isolated restore database, and the later verification fails closed; this does not establish a production bypass.

**Required remediation:** verify the archived/live Anchor's signature, trust-store status, deployment and release binding, and separately governed expected SHA-256 **before** database mutation; retain exact database-state reconciliation after restore. Add a negative test proving an invalid/revoked Anchor causes no restore attempt and no target DB mutation. Independently review the change and determine severity before closure.

**Status:** preliminary implementation-review finding; independent security assessment, severity, fix, and negative qualification pending. Do not assert zero open Major/Critical findings.

## Restore pre-verification remediation (implemented; negative test pending)

- Added recovery CLI `verify-anchor` action: verifies pinned SHA-256, Ed25519 signature, trust-store revocation, deployment and release binding **without opening a database connection**.
- `ops/scripts/restore-verify.sh` invokes `verify-anchor` before decryption, empty-database check and `pg_restore`; post-restore `verify` still performs exact database-state reconciliation.
- `bash -n` of restore script, Python compilation of CLI and `git diff --check`: PASS. Existing focused Batch E suite: **22 passed, 2 pre-existing deprecation warnings** on disposable database port 55432.
- A dedicated shell-level negative test proving an invalid/revoked Anchor causes zero database mutation has **not yet been added or executed**. Independent security re-review is still pending. Earlier preliminary finding is mitigated in code but cannot be marked closed until negative qualification and independent review.

## Negative qualification update

- Added two parametrized negative CLI tests for a revoked signing key and tampered Anchor, each with a nonexistent database URL file, plus an ordering assertion that `verify-anchor` precedes `restore` in the shell script. Both reject the invalid Anchor without opening the database URL file.
- Focused Batch E suite now **24 passed, 2 existing FastAPI deprecation warnings**; `bash -n`, Python compilation and `git diff --check` PASS.
- **Limit:** these tests validate the isolated preflight CLI and script ordering; they do not instrument a complete shell-level restore to prove zero database mutations under all failure modes. The latter remains a desirable additional integration negative test, and independent security review remains OPEN.
- No Commit, Push, Tag, production DB use, or Batch F execution.

## Additional preflight qualification

- Added a positive `verify-anchor` CLI test proving a valid, pinned Anchor succeeds even when the supplied database URL file does not exist. Combined with the two negative tests, this verifies separation of signature/trust preflight from database access in both accept and reject paths.
- Focused Batch E suite: **25 passed, 2 existing deprecation warnings**. `bash -n`, Python compilation and `git diff --check` PASS.
- Full shell-level restore mutation-sentinel integration test, full-suite rerun after recent changes, and independent security review remain pending. Checkpoint E remains OPEN.

## Full frontend requalification after preflight change

- Frontend Vitest: **217 passed / 37 files**. TypeScript and Vite production build: PASS; existing React `act(...)` test advisories and >500 kB chunk-size advisory remain.
- Full backend rerun launched against disposable PostgreSQL on 127.0.0.1:55432; final result must be recorded separately after completion.
- Full shell-level restore mutation-sentinel integration test and independent security review remain pending.

## Full backend rerun — performance gate interruption

- Full backend suite rerun on disposable PostgreSQL 127.0.0.1:55432 stopped at **461 passed, 1 failed, 1404 warnings** (`-x`). `test_approved_performance_conditions` measured `commitment_scoped_list` p95 **303.981 ms** against the approved **200 ms** limit. Do not claim full backend suite PASS after recent changes.
- Immediate isolated rerun of `tests/test_engineering_context_relationship_performance.py`: **2 passed, 153 warnings** in 16.10s. This is evidence of run-to-run variation, not proof that the full-suite performance gate is stable or that the first failure can be dismissed.
- Full backend requalification remains pending; investigate reproducibility under representative test load and rerun the suite without relaxing the performance threshold. Independent security review and full restore mutation-sentinel integration test remain OPEN.

## Full backend rerun — transient performance failure

- Full backend rerun after recent preflight changes stopped at **461 passed / 1 failed** due solely to `test_engineering_context_relationship_performance.py::test_approved_performance_conditions`; measured `commitment_scoped_list` p50 ~289 ms / p95 ~304 ms in that run.
- Immediate isolated rerun of the exact failed performance test on the same disposable database: **1 passed** (153 warnings) in 16.52s. This indicates a timing/performance flake under suite load, not yet a deterministic functional regression.
- Full backend suite still requires a clean complete rerun before Checkpoint E. Do not overwrite the earlier 2465-pass baseline or claim the current worktree fully qualified yet.

## Full backend requalification — clean rerun

- Full backend suite on disposable PostgreSQL `127.0.0.1:55432`: **2468 passed, 4415 warnings, zero failures**, in 224.68 seconds; process exit 0. The earlier suite-load performance failure did not recur in this complete rerun; its isolated rerun also passed. Preserve the earlier failure as recorded transient evidence rather than erasing it.
- Full frontend suite after latest preflight changes: **217 passed / 37 files**; TypeScript and Vite production build PASS.
- Focused Batch E recovery suite: **25 passed, 2 existing deprecation warnings**.
- Remaining gates: full shell-level negative Restore mutation-sentinel integration test; independent final-worktree security review with explicit finding disposition; Human Checkpoint E acceptance. No Commit, Push, Tag, or Batch F.

## Shell-level negative restore qualification

- Added two end-to-end shell-entry negative tests invoking `ops/scripts/restore-verify.sh` with fully formed, digest-consistent recovery artifacts and either a revoked Ed25519 trust key or a tampered Anchor with recalculated SHA-256. Stubbed `age`, `pg_restore`, and `psql` commands provide a mutation-attempt sentinel; each test confirms a nonzero exit, no invocation of `age`/`pg_restore`, and no modification of the sealed manifest. A deliberately unusable database URL prevents access to a real database.
- Both shell-level negative tests PASS. Focused Batch E suite now **27 passed, 2 existing FastAPI deprecation warnings**. Shell syntax, Python compilation, and `git diff --check` PASS.
- These tests prove the pre-restore rejection path with instrumented external commands, not a real PostgreSQL restore under every possible failure condition. The full backend suite of **2468 passed** preceded addition of these two tests; rerun the full suite if final-worktree qualification requires it.
- Independent security review and explicit Human Checkpoint E acceptance remain OPEN; no Commit, Push, Tag, production release, or Batch F.

## Final-worktree backend suite after shell-level negative tests

- Complete backend suite rerun against disposable PostgreSQL `127.0.0.1:55432` after adding both shell-level negative restore tests: **2470 passed, 4415 warnings, zero failures** in 222.64 seconds; exit code 0.
- Focused Batch E recovery tests: **27 passed**. Frontend: **217 passed / 37 files** and production build PASS (earlier run, frontend unchanged in this qualification step).
- This establishes a passing backend test baseline for the current test additions. It does not substitute for independent security review or Human Checkpoint E acceptance. Those gates remain OPEN. No Commit, Push, Tag, or Batch F.

## Human acknowledgement and independent-review gate

- User acknowledged the passing qualification evidence on 2026-10-02. This acknowledgement does not waive the explicitly required independent final-worktree security review or certify zero open Critical/Major findings.
- Latest full backend rerun: **2470 passed, 4415 warnings, zero failures**. Focused Batch E: **27 passed**; frontend: **217 passed / 37 files**, build PASS.
- Review handoff was not accepted; independent reviewer output is unavailable. Local `codex` CLI was not found in PATH at this checkpoint. Do not misrepresent implementation-assistant inspection as independent review.
- Gate remains OPEN pending independently attributable findings and explicit disposition. Preserve dirty worktree and do not Commit, Push, Tag, release, or start Batch F.

## Independent final-worktree security review — 2026-10-03

This section is the independent review requested after the preceding implementation-assistant inspections. Earlier qualification failures and reruns above are preserved as historical evidence. The reviewer inspected the accepted PATCH-059 Discovery, Architecture, EDS, IDS and Implementation Plan; prior Batch A-D/C1/C2 checkpoints; PATCH-058 release authority and protected signing workflow; the complete incoming PATCH-059 code delta from `8c37dcfa8235490408fb5d9c2c2d4e24857d149a`; and the dirty Batch E backend, frontend, operations, recovery, release-metadata, deployment and test changes.

The earlier Critical old-Anchor replay finding is verified remediated: Runtime hashes the exact Anchor bytes and requires the separately deployed digest (`backend/app/commercial_entitlements/recovery.py:77-87`, `backend/app/adapters/commercial_entitlement.py:67-86`), and `test_runtime_rejects_replay_of_older_valid_anchor_by_deployed_digest` covers the negative. The earlier restore-order finding is also verified remediated: public-key/trust/deployment/release/digest verification runs before decryption, database inspection or `pg_restore` (`ops/scripts/restore-verify.sh:38-57`), with revoked-key and tampered-Anchor shell mutation-sentinel negatives.

### Finding summary

- Critical: **0 open / 0 identified**.
- Major: **4 open / 7 identified**. Three narrowly scoped findings were remediated during this review; four remain stop conditions.
- Minor: **3 open**.
- Informational/operational prerequisites: production recovery custody, dual control, immutable archive retention, digest deployment, real per-release Human approval and compromise procedures remain Human-controlled prerequisites.

### Major findings remediated during review

#### SEC-E-MAJ-01 — accepted entitlements survived issuer-key revocation — RESOLVED

- References: `backend/app/adapters/commercial_entitlement.py:95-129`; runtime wiring at `backend/app/adapters/runtime_entitlement.py:40-50`; regression at `backend/tests/test_patch059_commercial_entitlement_adapter.py:304`.
- Invariant: IDS-059 requires a revoked verification key to reject CONFIGURE/EXECUTE at authoritative evaluation time (`IDS-059:87-91`).
- Scenario: an entitlement was validly activated, its issuer key was later revoked in the deployed trust store, but Runtime evaluated only normalized database state and continued permitting the entitlement.
- Severity: Major because post-compromise revocation did not terminate already-accepted commercial execution.
- Remediation: Runtime now loads the configured public trust store, resolves the persisted `key_id`, and fails closed for unknown, not-yet-valid or revoked keys before package/seat permission.
- Evidence: the new revoked-current-state regression passes within the 87-test focused suite and the full backend suite.

#### SEC-E-MAJ-02 — stale RETAINED winners survived a later capacity reduction — RESOLVED

- References: `backend/app/services/commercial_entitlement_service.py:452-529`; regression at `backend/tests/test_patch059_commercial_activation_transaction.py:230`.
- Invariant: after a capacity-reducing successor leaves the Organization over capacity, all execution must stop until a new explicit retained set of at most the new capacity is selected (EDS-059:105-117).
- Scenario: five previously RETAINED seats could remain executable when a later entitlement reduced capacity to two, because old retention markers were not invalidated.
- Severity: Major because it directly exceeded the signed named-seat limit.
- Remediation: a successor capacity reduction that leaves consuming seats above the new limit atomically demotes every prior RETAINED row to ASSIGNED or RESERVED under the same locks, requiring a fresh explicit selection.
- Evidence: the new transactional regression proves two stale retained winners become non-retained after a reduction to capacity one; focused and full suites pass.

#### SEC-E-MAJ-03 — expired higher revision could advance anti-rollback high-water — RESOLVED

- References: `backend/app/services/commercial_entitlement_service.py:395-421`; regression at `backend/tests/test_patch059_commercial_activation_transaction.py:199`.
- Invariant: activation repeats complete temporal validation and only a higher **valid** revision advances current state (IDS-059:153-160).
- Scenario: an administrator could activate an issuer-signed but already expired higher revision. It denied subsequent execution but irreversibly advanced the revision high-water, preventing activation of a lower still-usable successor and causing a durable commercial denial of service.
- Severity: Major because a stale signed artifact could permanently lock forward entitlement administration.
- Remediation: activation now rejects EXPIRED after trusted-time evaluation, records rejected history, and does not create or advance current state.
- Evidence: the new regression proves no current state is created by an expired revision; focused and full suites pass.

### Major findings still open — checkpoint stop conditions

#### SEC-E-MAJ-04 — RFC 8785/JCS contract is not implemented — OPEN

- References: `backend/app/commercial_entitlements/canonical.py:126-127`; contrary accepted requirements at `docs/implementation/PATCH-059-Implementation-Plan.md:51-59` and `docs/design/IDS-059-Commercial-Package-Configuration-Seats-and-Signed-Entitlements.md:69-81`.
- Invariant: entitlement signatures and SHA-256 digests use proven RFC 8785 JCS bytes, with a reviewed/pinned implementation decision.
- Scenario: an external issuer implementing the accepted RFC 8785 contract and Runtime using a locally reconstructed `json.dumps(sort_keys=True)` subset can disagree on canonical bytes for an allowed or future-compatible string representation; the resulting valid entitlement fails verification, or an unreviewed subset silently becomes the real wire contract.
- Severity: Major because this is the signed authority boundary and the Implementation Plan explicitly states the present technique is not an acceptable substitute.
- Required remediation: stop and perform the mandated bounded dependency/security review, pin a proven RFC 8785 implementation or obtain Human acceptance for a rigorously specified restricted canonical subset, and add independent published/cross-implementation golden vectors plus Unicode/I-JSON negatives.
- Required tests: RFC 8785 published vectors, cross-language signer/verifier vectors, invalid surrogate/non-I-JSON cases and stable digest/signature fixtures.

#### SEC-E-MAJ-05 — release sequence is shape-checked, not bound to PATCH-059 release authority — OPEN

- References: `backend/app/commercial_entitlements/release.py:35-90`; `ops/scripts/preflight.sh:14-28`; `.github/workflows/patch058-sign-release.yml:48-58,187-230,290-344`; accepted contract at IDS-059:238-244.
- Invariant: installed/candidate sequence must come from server-verified PATCH-058-compatible evidence with attributable Human release approval.
- Scenario: Runtime accepts a local manifest when its strings look like SHA-256 references and its sequence equals a separately mutable environment value. It does not verify the referenced dossier/signatures/approval. The only protected workflow reviewed is pinned to `refs/heads/patch-058`, signs PATCH-058 artifacts, emits a dossier with Human release approval explicitly pending, and does not bind a PATCH-059 release-sequence manifest for the current candidate.
- Severity: Major because commercial update eligibility and Recovery Anchor release binding rest on an authority that the current production path cannot independently establish.
- Required remediation: Human-accept a PATCH-059-compatible extension of the PATCH-058 protected release workflow that signs/attests the exact PATCH-059 artifacts and immutable `release_sequence`, produces final Human approval evidence, and provides a runtime/deployment-verifiable binding. Do not treat hash-shaped references as approvals.
- Required tests: reject forged/self-consistent manifests, wrong source/artifact/sequence, pending approval and wrong signer/workflow identity; accept only a real protected-workflow fixture with final approval.

#### SEC-E-MAJ-06 — recovery-set manifest is not authenticated — OPEN

- References: manifest creation at `ops/scripts/backup.sh:91-137`; restore consumption at `ops/scripts/restore-verify.sh:17-39,51-68`.
- Invariant: recovery artifacts, database/object digests, deployment/release/head/cutoff metadata and the signed commercial Anchor must form one attributable, tamper-evident recovery set.
- Scenario: a writer to backup storage can replace the age-encrypted database/object artifacts, recompute their ordinary SHA-256 values and rewrite the unsigned recovery-set JSON. Because age recipient encryption is not sender authentication and the commercial Anchor signs only normalized entitlement state, a forged dump containing the exact anchored commercial rows but altered engineering/application data can pass the current hash checks and post-restore commercial reconciliation.
- Severity: Major because the documented “sealed recovery-set manifest” is only self-consistent, not authenticated, so artifact integrity is not established against storage tampering.
- Required remediation: define and Human-accept an authenticated recovery-set envelope (offline recovery signature or independently custodied MAC) binding every artifact digest, deployment/release sequence, Alembic head, cutoff, Anchor digest and manifest schema; verify it before decryption or database access. Also constrain artifact names to safe basenames under the recovery directory.
- Required tests: manifest/digest/artifact substitution, path traversal, mixed-set splicing, wrong deployment/release/head and revoked manifest signer must all fail before `age`, `psql` or `pg_restore`.

#### SEC-E-MAJ-07 — seat assignment bypasses trusted-time rollback transition — OPEN

- References: `backend/app/services/commercial_seat_service.py:140-157`; trusted-time contract at IDS-059:165-175 and seat contract at EDS-059:91-103.
- Invariant: entitlement-sensitive authoritative mutations use monotonic trusted time; a clock more than five minutes behind durable high-water atomically enters sticky TIME_UNTRUSTED before any commercial expansion.
- Scenario: after entering GRACE, an administrator rolls the server clock back into ACTIVE, assigns a new seat, then restores the clock. `assign_seat` uses wall time via `effective_entitlement_state` without comparing `last_trusted_time`, so no sticky TIME_UNTRUSTED transition is recorded and the newly assigned user may execute an already-configured package during GRACE—contrary to continuity-only semantics.
- Severity: Major because clock rollback enables a prohibited GRACE seat expansion and persists it.
- Required remediation: apply the same locked `evaluate_trusted_time` transition to seat assignment/reactivation, commit sticky TIME_UNTRUSTED plus bounded audit even when the mutation is denied, and keep release/retained non-expanding repair semantics explicit.
- Required tests: `>5m` rollback assignment/reactivation persists TIME_UNTRUSTED and makes no seat change; exactly `5m` does not lower the checkpoint; forward time checkpoints monotonically; GRACE cannot acquire a seat through rollback.

### Minor findings still open

#### SEC-E-MIN-01 — admin status can contradict runtime enforcement

`backend/app/api/v1/routers/commercial_entitlements.py:151-196` derives `available` from database timestamps only. A revoked issuer key, invalid/missing Recovery Anchor or out-of-range installed release can therefore be shown as available while the runtime adapter correctly returns UNAVAILABLE. This is not an authorization bypass, but it impairs safe remediation. Reuse a non-mutating shared runtime-status evaluator and add revoked-key/Anchor/release mismatch response tests.

#### SEC-E-MIN-02 — restore validation relies on optimizable assertions and unconstrained manifest filenames

`ops/scripts/restore-verify.sh:17-35,71-83` uses Python `assert` for security checks and shell word-splitting for manifest-provided artifact names. `PYTHONOPTIMIZE=1` can remove assertions, while non-basename names can escape the intended directory. Replace assertions with explicit exceptions, parse a closed schema without shell word-splitting, resolve each filename beneath the recovery root, and test optimized-Python and traversal negatives. This hardening remains required even after manifest authentication.

#### SEC-E-MIN-03 — post-restore verification failure leaves a populated target

`ops/scripts/restore-verify.sh:54-83` restores atomically at the PostgreSQL transaction level, but later head/Anchor/object reconciliation failure leaves the isolated target populated and unsuitable for retry. The script fails closed and does not establish a production bypass, but the runbook must quarantine/drop-and-recreate the failed target or produce an explicit cleanup marker. Add a real disposable-PostgreSQL negative proving a post-restore mismatch cannot be mistaken for a verified target.

### Review remediation and test evidence

- Changed: runtime entitlement trust-store wiring/revocation enforcement; expired activation rejection; retained-seat reset on successor capacity reduction; three regressions and one runtime-factory fixture assertion.
- First expanded focused run: **86 passed, 1 failed** because the existing runtime-factory `SimpleNamespace` omitted the newly required trust-store path. The fixture was corrected; this failure is preserved here rather than erased.
- Focused security/recovery rerun on disposable PostgreSQL `127.0.0.1:55432`: **87 passed, 16 warnings**.
- Full backend suite after all review remediations: **2473 passed, 4417 warnings, zero failures** in 241.20 seconds.
- `git diff --check`: PASS. Python compilation: PASS after the initial sandbox-only `__pycache__` write denial was rerun with worktree permission. `bash -n` for backup/preflight/restore scripts: PASS.
- Earlier frontend evidence remains **217 passed / 37 files** with production build PASS; no frontend source changed during this review.
- No real port-5432 database was accessed. No Commit, Push, Tag, production release, Batch F work or PATCH-059 closure occurred.

### Security-gate disposition

**NOT READY FOR HUMAN ACCEPTANCE.** Critical replay and restore-preflight ordering are verified remediated, and three newly identified Major findings were corrected, but SEC-E-MAJ-04 through SEC-E-MAJ-07 remain open. The accepted Implementation Plan makes any open Major a stop condition. Checkpoint E must not be presented for Human Acceptance until those findings receive architecture-consistent remediation, regression evidence and an independent re-review.

**Exact next action:** return the four open Major findings to Human/design review. First authorize the RFC 8785 implementation decision and the PATCH-059-compatible protected release/recovery-manifest authority changes; then implement those accepted decisions plus the bounded seat trusted-time correction, run the relevant focused/full qualification, and commission a fresh independent re-review. Do not start Batch F.

## Major security architecture and remediation continuation — 2026-10-03

This section records work performed after the independent review above. The
original findings and earlier failure evidence are retained unchanged. The
dispositions below supersede the earlier four-Major-open count, but are not an
independent re-review and do not accept Checkpoint E.

### SEC-E-MAJ-04 — prohibited ad-hoc RFC 8785/JCS canonicalization

**Invariant and trace.** Signed entitlement bytes must be the exact RFC 8785
JCS representation of the closed payload. The former implementation in
`backend/app/commercial_entitlements/canonical.py` used Python
`json.dumps(sort_keys=True)`, which neither implements ECMAScript number
serialization nor UTF-16 property-name ordering and therefore could produce
non-interoperable signed bytes.

**Architectural basis.** Architecture/EDS/IDS-059 already freeze RFC 8785, and
the accepted Implementation Plan expressly rejects `json.dumps(sort_keys=True)`
as a substitute while authorizing a bounded dependency review and exact pin.
This remediation implements an existing contract; it does not introduce a new
canonicalization authority or require a new Human architecture decision.

**Options and dependency decision.** `rfc8785==0.1.4` from Trail of Bits was
selected over a non-RFC canonical JSON library, a locally maintained copy of
the RFC reference code, and retention of the prohibited subset. It is pure
Python, Apache-2.0, Python >=3.8, has no transitive dependencies, and is pinned
in `pyproject.toml`, both requirements/production-lock surfaces and `uv.lock`.
The governed hashes are recorded in
`PATCH-059-RFC8785-Dependency-Security-Review.md`. There is no database
migration or new signing authority. Signatures created with the old ad-hoc
encoder must not be assumed interoperable; the exact candidate must be
qualified with the governed package artifact before release.

**Implementation and regressions.** Canonical byte generation now delegates
to `rfc8785.dumps`. Regressions cover the RFC published primitive-number and
UTF-16 ordering vectors, lone-surrogate rejection, exact Unicode entitlement
bytes, and the existing digest/signature/non-I-JSON behavior.

**Disposition:** **REMEDIATED IN THE WORKTREE / PENDING FRESH INDEPENDENT
SECURITY RE-REVIEW.** The terminal could not resolve `files.pythonhosted.org`;
tests used the exact reviewed official v0.1.4 source from a disposable `/tmp`
snapshot via `PYTHONPATH`. A clean networked runner must install and verify the
recorded distribution hash and rerun qualification before acceptance. That
remaining acquisition evidence does not reopen the architecture decision, but
it is a release-qualification prerequisite.

### SEC-E-MAJ-05 — release sequence lacks protected signing/final approval binding

**Invariant and trace.** A positive `release_sequence` is authoritative only
when it is cryptographically bound to the exact source and artifacts, the
protected signer identity, immutable release dossier and a distinct
attributable final Human release approval. The current local manifest/preflight
path validates a closed shape and hash-shaped references but cannot establish
those facts. The reviewed PATCH-058 workflow is hard-bound to the PATCH-058
branch and deliberately emits a pending dossier, so its existence is not proof
that this PATCH-059 candidate was signed or approved.

**Architectural basis and options.** ADR-031 and PATCH-058 own signing,
provenance, dossier and Human release-approval authority; Architecture/EDS/
IDS-059 require PATCH-058-compatible server-verified evidence. Reusing those
authorities is required and avoids a new trust root, but extending protected
workflow identity, the signed manifest subject and finalization contract is a
durable release/security change under the Governance Model ADR threshold.
Environment variables, self-consistent hashes, an arbitrary-ref generic signer,
the entitlement issuer and the Recovery Authority are not acceptable
substitutes.

**Recommended Human decision.** Accept the PATCH-059-specific protected
workflow and evidence/finalization contract proposed in draft
`ADR-032-PATCH-059-Release-and-Recovery-Evidence-Authentication-DRAFT.md`:
reuse the existing PATCH-058 signing and approval authority; bind the closed
release manifest, `release_sequence`, source, artifacts and dossier; require a
separate final Human approval and protected finalization; and provide pinned
offline verification plus runtime binding to the exact verified manifest.

**Dependencies and release implications.** This requires an allowlisted
PATCH-059 workflow/ref identity, versioned evidence schemas, protected Human
environment policy, final approval/finalization evidence and offline verifier.
It requires no database migration. It directly affects release signing and
therefore cannot be implemented under inferred authority.

**Disposition:** **OPEN / HUMAN ARCHITECTURE DECISION REQUIRED.** No workflow,
signing contract or runtime authority was implemented. ADR-032 remains
`PROPOSED`; after Human acceptance it also requires an accepted implementation-
plan amendment and full negative/protected-workflow qualification.

### SEC-E-MAJ-06 — unauthenticated recovery-set manifest

**Invariant and trace.** Before decryption, restore or target mutation, the
complete recovery set must be authenticated by the correct recovery authority.
The current recovery-set manifest binds artifact hashes but has no signature;
a storage writer can replace artifacts and rewrite those hashes while leaving
the separately signed Recovery Anchor internally valid.

**Architectural basis and options.** IDS-059 and the Batch E recovery design
already establish a separate Ed25519 Recovery Authority, public trust store,
revocation model and domain-separated signing pattern. Reusing it preserves
authority separation and is preferable to a new MAC/key, release signer misuse
or coupling backup inventory into Recovery Anchor v2. Nevertheless, a new
closed signed-envelope schema, domain separator, ordering and legacy-set policy
are durable trust-contract decisions and cross the Human ADR boundary.

**Recommended Human decision.** Accept ADR-032's closed
`satco.commercial-recovery-set/v1` Ed25519 envelope using the existing Recovery
Authority, RFC 8785, the dedicated domain
`SATCO-COMMERCIAL-RECOVERY-SET-V1\0`, exact artifact roles/safe basenames/
digests/sizes and deployment/sequence/head/cutoff/Anchor binding. Verify the
signature and key status before `age`, `psql`, `pg_restore` or any target
mutation. Existing unsigned sets must be Human re-sealed through an attributable
offline ceremony or declared ineligible, never silently grandfathered.

**Dependencies and operations.** No database migration is required. The
isolated recovery tool requires the same hash-pinned RFC 8785 implementation
and existing Ed25519 dependency/trust lifecycle. Backup ordering, immutable-set
retention, custodian/quorum/rotation decisions and negative restore tests must
be updated after approval.

**Disposition:** **OPEN / HUMAN ARCHITECTURE DECISION REQUIRED.** No recovery-
set signing contract was implemented. ADR-032 remains `PROPOSED`; Human
acceptance and an accepted implementation-plan amendment are required first.

### SEC-E-MAJ-07 — seat assignment/reactivation bypasses durable trusted time

**Invariant and trace.** Every state-changing seat acquisition must evaluate
trusted time while the entitlement state is locked. A rollback greater than
five minutes must atomically persist sticky `time_untrusted_at`, emit bounded
audit, deny acquisition and never lower `last_trusted_time`; ordinary failures
must not commit partial seat state. The prior assignment path checked wall-clock
status directly and could acquire/reactivate a seat without invoking this
transition.

**Architectural basis.** Architecture/EDS/IDS-059 already define the five-
minute rollback threshold, sticky durable transition, active-only acquisition,
monotonic trusted-time checkpoint and transactional ordering. No new trust
model, dependency or database migration is required.

**Implementation and regressions.** `CommercialSeatService.assign_seat`
evaluates trusted time under the locked entitlement state, persists a new
sticky transition and rejects rollback, advances the trusted checkpoint only
forward, and evaluates ACTIVE status at effective trusted time. The API stages
bounded `time_untrusted` audit and commits only the durable transition; if
audit staging fails, the transaction rolls back. Regressions prove rollback
denial/no seat, durable audit, audit-failure rollback, exact five-minute
acceptance without lowering the checkpoint, forward monotonic advancement,
reactivation denial leaving RESERVED state, and GRACE denial through rollback.

**Disposition:** **REMEDIATED IN THE WORKTREE / PENDING FRESH INDEPENDENT
SECURITY RE-REVIEW.** Focused and full qualification are green.

### Open Minor findings

- **SEC-E-MIN-01 — OPEN.** Operational status still overstates
  `release_signature_verified`/approval relative to what runtime actually
  verifies. Resolve with a shared non-mutating verifier/result contract after
  MAJ-05's evidence schema is Human accepted; do not invent that contract
  prematurely.
- **SEC-E-MIN-02 — REMEDIATED IN THE WORKTREE / PENDING RE-REVIEW.** Restore
  manifest/object validation no longer relies on optimization-removable Python
  `assert`; it enforces an exact closed legacy schema, SHA-256 syntax, safe
  basenames and regular non-symlink files contained by the recovery root.
  Negative tests run with `PYTHONOPTIMIZE=1` and reject revoked, tampered and
  traversal manifests before the sentinel restore command.
- **SEC-E-MIN-03 — OPEN.** A failure after transactional restore can leave a
  populated isolated target. A cleanup/quarantine/drop-and-recreate policy and
  disposable-PostgreSQL negative remain required. This does not create a
  production bypass, but the target must never be represented as verified.

### Continuation qualification evidence

- Initial trusted-time focused run: **28 passed, 24 warnings**.
- Combined JCS/trusted-time run: **44 passed, 24 warnings**.
- Expanded PATCH-059 security/recovery run: **235 passed, 30 warnings**.
- Final JCS/seat/recovery-verifier focused run after the audit-failure and
  optimized-Python path tests: **42 passed, 2 warnings**; `bash -n` PASS.
- Fresh complete backend suite after every authorized correction:
  **2486 passed, 4427 warnings, zero failures** in 261.67 seconds against only
  disposable PostgreSQL `127.0.0.1:55432`.
- `uv lock --check --offline`: PASS, 59 packages.
- Earlier frontend evidence remains **217 passed / 37 files** and production
  build PASS. No frontend behavior or shared frontend contract changed in this
  continuation, so it was not rerun.
- The earlier 86-pass/1-failure fixture evidence and all prior qualification
  results above remain part of the record; they were not overwritten.
- No production PostgreSQL on port 5432, Commit, Push, Tag, production release,
  Batch F work or Checkpoint E acceptance occurred.
- The disposable `satco-p059-batch-e-pg` container was confirmed bound only to
  host `127.0.0.1:55432` and returned to its original stopped state after the
  qualification run.

### Exact gate and next step

**SECURITY GATE STOPPED — NOT READY FOR HUMAN CHECKPOINT E ACCEPTANCE.** The
current count is Critical 0 open; Major 7 identified, 5 remediated in the
worktree and **2 open** (SEC-E-MAJ-05 and SEC-E-MAJ-06); Minor 3 identified, 1
remediated in the worktree and **2 open**. Worktree remediation is not finding
closure until a fresh independent reviewer verifies it. ADR-032 is proposed,
not accepted.

**Exact next step:** Human Architecture Authority independently reviews
ADR-032 and explicitly accepts, rejects or amends each listed release and
recovery decision. If accepted, prepare and obtain acceptance of the bounded
implementation-plan amendment; implement only that authority; qualify the
protected release/final-approval and authenticated recovery-set paths,
including installation of the hash-pinned JCS artifact on a clean runner; run
the complete qualification suite; then commission a fresh independent security
re-review of the exact final worktree covering all seven Major and three Minor
dispositions. Do not present Checkpoint E or start Batch F before that result.

## ADR-032 Human architectural acceptance — 2026-10-03

- The Human Architecture Authority explicitly accepted all six decisions in ADR-032. The ADR status was updated to ACCEPTED; the filename retains `-DRAFT` as a historical locator, not the current decision status.
- Prepared `docs/implementation/PATCH-059-Batch-E-ADR-032-Implementation-Amendment-DRAFT.md` covering the bounded SEC-E-MAJ-05 release-signing/final-approval and SEC-E-MAJ-06 signed recovery-set workstreams, negative qualification, operational prerequisites and independent re-review.
- **Separate Human implementation-plan amendment approval remains pending.** No code, workflow, schema, Commit, Push, Tag, release, Checkpoint E closure or Batch F authorized by architectural acceptance alone. Both Major findings remain OPEN.

## ADR-032 bounded implementation authorization — 2026-10-03

- The Human Architecture Authority explicitly approved
  `PATCH-059-Batch-E-ADR-032-Implementation-Amendment-DRAFT.md` on 2026-10-03.
  The filename retains `-DRAFT` as a historical locator; its status now records
  Human implementation authorization.
- Authorized scope is limited to SEC-E-MAJ-05 authenticated PATCH-059 release
  evidence and SEC-E-MAJ-06 authenticated recovery-set evidence, including
  bounded workflow/schema/tooling changes and qualification.
- Actual privileged signing, attributable final Human release approval,
  production recovery/re-sealing ceremony, deployment, production release,
  Commit, Push, Tag, Checkpoint E closure and Batch F remain unauthorized.
- Implementation evidence produced below is not evidence that a real protected
  signing workflow or Human release/recovery ceremony occurred.

## ADR-032 authorized implementation result — 2026-10-03

This section supersedes the earlier MAJ-05/MAJ-06 implementation status while
preserving every earlier review finding and qualification result above.

### SEC-E-MAJ-05 — authenticated release sequence

**Worktree remediation implemented.** The closed
`satco.patch059-release-manifest/v1` contract binds release ID, positive
sequence, source SHA, backend/frontend/migration subjects, Alembic head,
configuration schema, candidate provenance and dossier. Runtime now requires
the exact manifest bytes to match separately governed
`SATCO_RELEASE_MANIFEST_SHA256`, opens without following symlinks, and rejects
non-regular/multiply-linked files, digest mismatch, sequence mismatch and head
mismatch.

The new PATCH-059-only protected workflow is fixed to
`patch059-sign-release.yml@refs/heads/patch-059-implementation`. It reuses the
existing `patch058-protected-release` Environment, signs all three artifacts
and the manifest with pinned Cosign v2.6.0, and attests the manifest as a
release-provenance subject. A separate
`patch059-final-release-approval` Environment supplies an attributable review
record. Only then are the exact Human approval and finalization records created
and signed.

The pinned offline verifier checks the expected repository, issuer,
workflow/ref, workflow source SHA, release identity/sequence, all subjects,
manifest deployment digest, candidate/release provenance, pending dossier,
security decision, exception freshness, final approval, finalization, every
Cosign blob signature and the manifest attestation. Tests explicitly identify
their positive evidence as fixtures and reject source, sequence, artifact,
repository, workflow, pending/rejected approval, stale exception,
post-approval modification and unauthenticated self-consistent evidence.

No protected workflow was run and no Human approval or release evidence was
fabricated. Operational prerequisites remain: configure both Human-reviewed
Environments, approve the exact candidate-evidence producer and retention
policy, execute on a trusted clean runner, perform a real attributable final
approval only when authorized, retain the release-ready bundle immutably and
deploy the separately governed manifest digest.

**Disposition:** REMEDIATED IN THE WORKTREE / PENDING FRESH INDEPENDENT
SECURITY RE-REVIEW AND REAL OPERATIONAL POLICY EVIDENCE.

### SEC-E-MAJ-06 — authenticated recovery set

**Worktree remediation implemented.** Backup creates the closed
`satco.commercial-recovery-set/v1` RFC 8785/Ed25519 envelope using the existing
Recovery Authority, verifies the complete set, durably archives regular
single-link members, then promotes the candidate Anchor. The signed payload
binds deployment, release sequence, head, schema, UTC cutoff/count, encrypted
database, sealed object inventory and archived Anchor.

Restore authenticates the set and absolute key-revocation state before
decryption or database inspection. It rejects unsafe names, symlinks,
hardlinks, mixed or changed artifacts, wrong deployment/sequence/head and
digest/length mismatch. The verifier now snapshots each archive member from
the same verified open file descriptor into a private restore directory;
source replacement after verification cannot change restore bytes. The
immutable set is never rewritten. Success and failure are recorded separately.
A post-restore failure creates a quarantine marker requiring drop-and-recreate
of the isolated target before retry, so a partially populated target cannot be
represented as verified.

Positive signing/verification, tampering, mixed identity, revoked key,
unsafe-path, manifest link, artifact link, replacement and failure/quarantine
paths are covered. No production backup, restore, recovery signing or
historical-set re-sealing occurred.

**Disposition:** REMEDIATED IN THE WORKTREE / PENDING FRESH INDEPENDENT
SECURITY RE-REVIEW AND HUMAN RECOVERY-CUSTODY/RETENTION POLICY EVIDENCE.

### Remaining findings and authorization boundary

- SEC-E-MIN-01 remains open: the ordinary administrative status response can
  still be less conservative than the complete Runtime decision under revoked
  issuer trust or recovery/release mismatch. Resolving it changes the API
  status-evaluation contract and is not included in the MAJ-05/MAJ-06-only
  amendment; Human authority must explicitly authorize the shared,
  non-mutating Runtime-status contract before implementation.
- SEC-E-MIN-02 remains remediated in the worktree and pending re-review.
- SEC-E-MIN-03 now has worktree remediation through create-once quarantine
  evidence and mandatory isolated-target drop/recreate policy, with an
  instrumented post-restore failure test; it remains pending independent
  severity/disposition review.
- All seven Major findings now have worktree remediation, but none is declared
  closed by this implementation assistant. Fresh independent security review
  must explicitly verify all seven Major and three Minor dispositions.

### Final qualification evidence

- Network acquisition into the local venv: `rfc8785==0.1.4` installed
  successfully. `uv lock --check --offline && uv sync --frozen --offline`:
  PASS, 59 resolved packages / 56 checked packages. A trusted clean release
  runner must still prove installation from the governed distribution hashes.
- Focused ADR-032 release/recovery/configuration suite: **99 passed, 2
  warnings**, including explicit mixed-set and unknown-key negatives. The
  preceding release-verifier/runtime-manifest hardening rerun was **14 passed,
  2 warnings**.
- Exact final full backend suite on disposable PostgreSQL
  `127.0.0.1:55432`: **2519 passed, 4427 warnings, zero failures** in
  **231.57 seconds**.
- Earlier full runs in this continuation passed **2515 tests** in 228.54
  seconds and **2517 tests** in 227.22 seconds before the last security-negative
  additions; they are preserved rather than overwritten.
- Complete operations unit suite: **46 passed** in 2.532 seconds.
- Frontend TypeScript: PASS. Vitest: **217 passed / 37 files**. Production
  build: PASS; the existing >500 kB chunk advisory remains.
- Alembic sole head: `e05900000002 (head)`. The first `alembic current`
  command omitted required runtime database environment fields and failed
  before connecting; the corrected disposable-only command passed with
  `e05900000002 (head)`.
- `git diff --check`, Python source compilation, shell syntax for
  backup/preflight/restore, and workflow YAML parsing: PASS.

### Gate

**READY FOR FRESH INDEPENDENT SECURITY RE-REVIEW, NOT HUMAN CHECKPOINT E
ACCEPTANCE.** Required next steps are independent exact-worktree review,
explicit finding disposition, clean-runner hash-pinned dependency evidence and
Human confirmation of signing/final-approval/recovery custody and retention
policies. No protected signing run, real Human release approval, production
backup/restore, deployment, Commit, Push, Tag, release, Checkpoint E closure,
Batch F or PATCH-060 occurred.

## Independent security re-review continuation — 2026-10-04

This is the independent exact-worktree continuation requested after the prior
review was interrupted. It reviewed HEAD
`a1918c89bc547d814a0f176ef20688b03fd99997` on
`patch-059-implementation`, inventorying every modified and untracked file and
tracing the security-relevant implementation, workflow and tests. The incoming
dirty worktree was preserved. No implementation or test file was changed; this
report is the only review artifact updated.

### Final disposition of the original findings

| Finding | Disposition | Independent result |
|---|---|---|
| SEC-E-MAJ-01 | **REMEDIATED** | Runtime re-resolves the persisted issuer `key_id` through the deployed public trust store and denies unknown/not-yet-valid/revoked authority before package or seat execution. Revoked-current-state negatives pass. |
| SEC-E-MAJ-02 | **REMEDIATED** | A capacity-reducing successor locks the consuming set and demotes stale `RETAINED` rows when the new limit is exceeded, forcing a fresh explicit retained set. Transactional regression passes. |
| SEC-E-MAJ-03 | **REMEDIATED** | Expired signed successors are rejected after locked trusted-time evaluation without creating or advancing current state. Anti-rollback high-water regression passes. |
| SEC-E-MAJ-04 | **REMEDIATED** | Entitlement canonicalization uses pinned `rfc8785==0.1.4`; dependency locks contain the governed hashes; RFC number, UTF-16 ordering, Unicode and invalid-surrogate vectors pass. `uv lock --check --offline` resolved 59 packages successfully. |
| SEC-E-MAJ-05 | **PARTIALLY REMEDIATED** | Manifest, final approval/finalization, exact-subject signatures, offline identity checks and runtime digest pinning are implemented and their local negative fixtures pass. The protected signing workflow does **not** authenticate the supplied `candidate_run_id` to an allowlisted candidate workflow ID/path: it checks only `head_sha`, `conclusion` and `head_branch`. The only workflow containing `patch059-release-candidate-${source_sha}` is the consumer itself; no candidate producer exists in this worktree. Therefore an exact clean/qualified candidate provenance chain is neither implemented nor independently exercisable, and all Cosign tests use a test double rather than real bundles. |
| SEC-E-MAJ-06 | **REMEDIATED** | The recovery set is a closed RFC-8785/Ed25519 envelope under the separate Recovery Authority. Signature/trust/deployment/sequence/head/schema and exact artifacts are verified before decryption or DB access; safe basenames, no-follow/single-link reads and same-file-descriptor snapshots close substitution races. Tamper, mixed-set, wrong identity, unknown/revoked key, unsafe name/link and pre-mutation sentinel negatives pass. |
| SEC-E-MAJ-07 | **REMEDIATED** | Seat acquisition/reactivation evaluates trusted time under the locked entitlement state, persists the sticky rollback transition and bounded audit atomically, denies mutation, and advances checkpoints only monotonically. Boundary, rollback, reactivation, GRACE and audit-failure regressions pass. |
| SEC-E-MIN-01 | **OPEN** | Both ordinary entitlement status and update eligibility remain timestamp/database-derived and do not run the complete Runtime issuer-trust, Recovery Anchor and release-authority decision. They can report availability/eligibility while Runtime denies execution. |
| SEC-E-MIN-02 | **REMEDIATED** | Restore-side security decisions use explicit failures, a closed signed schema, safe basenames, no-follow/single-link reads and private snapshots. The `PYTHONOPTIMIZE=1` traversal/revocation/tamper shell negatives reject before `age`, `psql` or `pg_restore`. |
| SEC-E-MIN-03 | **REMEDIATED** | Any failure after restore start creates a create-once quarantine record, omits verified evidence and makes retry fail until the isolated target is dropped and recreated. The mutation-sentinel/post-restore-failure negative passes. |

### Residual MAJ-05 evidence-chain defect

`.github/workflows/patch059-sign-release.yml:82-104` accepts the user-supplied
candidate run after checking only its source SHA, success conclusion and branch,
then downloads an artifact by predictable name. It does not check the run's
workflow ID/path, event, attempt, or an accepted candidate-producer identity.
Repository search finds no PATCH-059 producer for that artifact name. The
existing protected signing review is important but does not replace machine-
verified producer provenance: a wrong or later-added workflow at the same
source/branch boundary could supply self-consistent artifacts for the protected
signer to re-sign, and the current worktree cannot produce the required positive
protected-workflow fixture at all.

Required remediation is to add or designate the exact clean candidate workflow,
pin its workflow ID/path and event in the signing workflow, verify those fields
from the candidate-run API before download, bind them into provenance/final
evidence, and exercise a real protected fixture with actual Cosign bundles. A
local `FixtureCosign` success is useful unit evidence but is not that gate.

### New finding

#### SEC-E-RR-MIN-01 — backup object-inventory validation disappears under Python optimization — OPEN

`ops/scripts/backup.sh:48-60` performs all object-inventory schema, digest,
size and canonical-order checks with Python `assert`. Running the validator
under `PYTHONOPTIMIZE=1` removes those checks; a payload whose schema is
`attacker-controlled` was accepted by the same assertion pattern, while the
ordinary interpreter rejected it with `AssertionError`. The resulting invalid
inventory can be encrypted and bound into an otherwise correctly signed
recovery-set envelope. Restore eventually rejects the inventory after database
mutation and quarantines the target, so this is not an integrity-bypass path,
but it allows creation and promotion of a signed recovery set that cannot
complete recovery.

Replace every backup-side assertion with explicit closed-schema exceptions,
reject duplicate/non-I-JSON input, and add a `PYTHONOPTIMIZE=1` backup negative
proving that no signed set is emitted and the candidate Anchor is not promoted.

No other distinct new vulnerability was reproduced. Production key custody,
dual control, immutable archive retention, protected Environment configuration,
clean-runner dependency acquisition and an actual attributable release approval
remain operational prerequisites rather than evidence fabricated by this review.

### Tests performed by this independent continuation

- Focused original-finding and ADR-032 suite against only disposable PostgreSQL
  `127.0.0.1:55432/satco_platform_patch02022_test`: **152 passed, 26 warnings**.
  This covered issuer revocation, capacity reduction, expired successor,
  canonicalization, trusted-time seat mutation, release manifest/runtime,
  signed recovery set, restore ordering/quarantine and operations configuration.
- MAJ-05/06 non-database negative suites with repository `conftest` disabled:
  **60 passed** (**31** release/recovery-set tests plus **29** Batch-E tests; one
  PostgreSQL test intentionally deselected in the latter run).
- PostgreSQL-backed recovery lock/anchor consistency test: **1 passed, 2
  warnings**. The database identity was positively checked as
  `satco_platform_patch02022_test|satco`; production port 5432 was never used.
- `uv lock --check --offline` with a disposable cache: **PASS, 59 packages**.
- Python-optimization probe: malformed object-inventory schema accepted under
  `PYTHONOPTIMIZE=1` and rejected without optimization, reproducing
  SEC-E-RR-MIN-01.
- The existing disposable PostgreSQL container was returned to its original
  stopped state after testing.

The earlier exact final full-backend result (**2519 passed, 4427 warnings**),
frontend result (**217 passed / 37 files**, TypeScript/build PASS), operations
suite (**46 passed**) and shell/YAML/diff checks remain valid historical
qualification evidence for the unchanged implementation. This continuation did
not rerun the entire backend/frontend suites because it made no implementation
change.

### Independent security-gate decision

**NOT READY FOR HUMAN ACCEPTANCE.** The original disposition is now Major 7
identified: 6 REMEDIATED and 1 PARTIALLY REMEDIATED (SEC-E-MAJ-05); Minor 3
identified: 2 REMEDIATED and 1 OPEN (SEC-E-MIN-01). One new Minor,
SEC-E-RR-MIN-01, is OPEN. No Critical finding is open.

The exact blocking remediation is:

1. close SEC-E-MAJ-05 by implementing and allowlisting the exact candidate-
   evidence producer, binding its workflow identity, and passing a real
   protected Cosign/final-approval fixture;
2. obtain the already-required clean-runner and Human-controlled protected-
   Environment/release-approval evidence for the exact candidate;
3. remediate SEC-E-MIN-01 with the separately authorized shared non-mutating
   Runtime-status evaluator; and
4. replace backup-side assertions and add the optimized-Python negative for
   SEC-E-RR-MIN-01.

After those changes, rerun the focused negative suite, a real signed-set restore
and reconciliation on `127.0.0.1:55432`, the complete qualification suite, and
commission a final exact-worktree independent re-review. This review does not
grant Human Acceptance, close Checkpoint E, or authorize Commit, Push, Tag,
signing, release, deployment or Batch F.

## Security remediation Round 2 — 2026-10-04

This section records implementation and qualification performed after the
independent re-review above. HEAD remained
`a1918c89bc547d814a0f176ef20688b03fd99997` on
`patch-059-implementation`; the incoming modified and untracked worktree was
preserved. No Commit, Push, Tag, protected workflow, release, deployment,
production recovery, Human Acceptance, Checkpoint E closure or Batch F action
occurred.

### Finding disposition after Round 2

| Finding | Disposition | Round 2 result |
|---|---|---|
| SEC-E-MAJ-05 | **PARTIALLY REMEDIATED** | The code-level evidence-chain defect is remediated. A dispatch-only `.github/workflows/patch059-candidate-evidence.yml` now produces the exact candidate, and `patch059-candidate-evidence.py` authenticates the candidate run's repository/head repository, workflow path/ref, event, branch, source SHA, release ID, run ID/attempt, successful completion and run URL. The protected signer verifies that API identity before signing. The closed candidate identity digest is in the signed manifest, the full identity is in release provenance, and its digest is repeated in final Human approval and finalization. Positive and unauthorized-workflow/event/branch/source/repository/run-attempt negatives pass. The finding remains partial only because no trusted clean-runner candidate, real OIDC/Cosign bundle, protected signing approval or distinct final Human approval was executed; that is an operational Human boundary. |
| SEC-E-MIN-01 | **OPEN — AUTHORIZATION PENDING** | Proposed ADR-033 and its proposed implementation amendment define a shared, read-only runtime/status evaluation contract covering issuer revocation, authenticated release-range authority, signed Recovery Anchor validity and fail-closed reasons while preserving separately authorized historical read/export. Both documents explicitly prohibit implementation until Human Architecture acceptance and Human Implementation Authorization are recorded. No MIN-01 implementation was performed in this round. |
| SEC-E-RR-MIN-01 | **REMEDIATED** | Backup object-inventory validation moved to `patch059-object-inventory.py`, which uses explicit exceptions, a closed schema, duplicate-member/non-I-JSON rejection, safe file handling, strict timestamp/digest/size/order validation and canonical output. `backup.sh` invokes it before database snapshot, signing or Anchor promotion. Under `PYTHONOPTIMIZE=1`, wrong schema, extra entry fields, duplicate members and `NaN` all fail while preserving the output; the shell negative proves malformed evidence causes no `pg_dump`/`age` attempt, no signed set and no Anchor change. |

No additional distinct security weakness was reproduced during Round 2.

### Protected signing fixture and operational boundary

The exact fixture is now executable as:

1. dispatch `patch059-candidate-evidence.yml` on
   `refs/heads/patch-059-implementation` with exact source SHA, immutable
   release ID and exact accepted Human security-decision commit;
2. retain its run ID/attempt and candidate artifact;
3. dispatch `patch059-sign-release.yml` with that run ID, the same release ID
   and source SHA, positive release sequence, `e05900000002` and configuration
   schema `v1`;
4. obtain the existing `patch058-protected-release` Environment review from an
   attributable non-self reviewer;
5. after artifact/manifest signing, obtain a distinct attributable review for
   `patch059-final-release-approval`; and
6. retain the release-ready artifact, final manifest digest, approval history
   and pinned offline-verifier output.

The trusted clean runner, protected Environment configuration, branch policy,
artifact retention/custody and authorization to create real OIDC/Cosign and
Human approval evidence must be confirmed operationally. This session did not
fabricate or execute those authorities. PATCH-058's protected signing workflow
and authority were not changed.

### Qualification results

- Final full Backend suite on disposable PostgreSQL only at
  `127.0.0.1:55432/satco_platform_patch02022_test`: **2540 passed, 4427
  warnings, zero failures** in **246.18 seconds**. An earlier Round 2 run found
  one static contract-marker failure after validator extraction; the marker was
  restored without weakening the check, its focused rerun passed, and the
  quoted final full run is post-fix and includes all new negatives.
- Focused release/recovery/security and operations-dossier run: **83 passed**.
  The final full suite additionally contains the two duplicate/non-I-JSON
  optimized-interpreter cases added afterward.
- Complete operations suite: **46 passed, 7 subtests passed** in **2.98
  seconds**.
- Frontend: TypeScript PASS; Vitest **217 passed / 37 files**; production build
  PASS. The existing >500 kB chunk advisory remains non-blocking.
- Dependency lock: `uv lock --check --offline` PASS, **59 packages**.
- Alembic: sole head and disposable database current revision both
  `e05900000002 (head)`.
- Static checks: `git diff --check`, Python compilation, shell syntax,
  PATCH-059 workflow YAML parsing and release JSON parsing all PASS.
- Signed-set backup/restore: PASS using the disposable source database and an
  isolated `satco_patch059_restore_e2e` target, both through host port 55432.
  The test created and verified a real qualification-only Ed25519 Recovery
  Anchor and signed-set envelope, used PostgreSQL 16 `pg_dump`/`pg_restore`,
  restored `e05900000002`, reconciled zero commercial states and zero object
  rows, and emitted `satco.commercial-recovery-verification/v1` with signed-set
  SHA-256
  `046e61d1b40e5f131d24feb426f2f178e9d588ad8afbcce998348bb223bc4163`.
  Because `age` is absent on this host, only the encryption transport was a
  reversible qualification copy; signature, trust, artifact-digest, immutable
  snapshot, database restore, head, Anchor and object reconciliation paths were
  real. No host connection to production port 5432 occurred.

### Round 2 gate

**READY FOR ANOTHER INDEPENDENT SECURITY REVIEW. NOT READY FOR HUMAN
ACCEPTANCE.** The exact remaining blockers are:

1. SEC-E-MIN-01 needs explicit Human Architecture acceptance of proposed
   ADR-033 and explicit Human Implementation Authorization, followed by the
   bounded implementation, parity/security tests and independent review.
2. SEC-E-MAJ-05 needs operational authorization and execution of the exact
   clean-runner candidate/protected-signing/distinct-final-approval fixture,
   producing real pinned Cosign evidence and attributable Human approvals.
3. Human-controlled runner trust, protected Environment policies, key/evidence
   custody and immutable retention must be verified for the exact candidate.
4. A fresh independent reviewer must verify this exact dirty worktree and the
   real protected evidence before Human Acceptance can be considered.

SEC-E-RR-MIN-01 has no remaining code blocker. This section does not grant
Human Acceptance or authorize release activity.


## ADR-033 / SEC-E-MIN-01 bounded implementation — 2026-10-04

Human Architecture Acceptance of ADR-033 and bounded Human Implementation Authorization
were explicitly granted by Saman Dehdashti on 2026-10-04 and recorded in the ADR
and MIN-01 amendment. These decisions do **not** grant implementation acceptance,
release authorization, or Checkpoint E closure.

The inherited interrupted Codex worktree already contained the shared read-only
`CommercialRuntimeStatusEvaluation` service and its consumers in the runtime
adapter, administrative entitlement status and update eligibility. Remote Desktop
Commander continuation preserved the worktree and added
`backend/tests/test_patch059_shared_runtime_status.py` with twelve focused
parity, historical-access, invalid-evidence, missing-entitlement and release/Anchor
negative tests. Existing status-response and update-eligibility tests were
re-scoped to test response mapping using explicit shared-evaluation fixtures;
the real evaluator's fail-closed behavior is tested separately. The existing
transaction-order test uses an explicitly authenticated-result fixture to isolate
checkpoint/seat transaction behavior.

Qualification evidence:
- Initial focused adapter/API/factory suite: 45 passed, 2 warnings.
- New ADR-033 test module: 12 passed, 2 warnings.
- Changed focused status, transaction and parity tests: 22 passed, 33 deselected.
- Initial full Backend run: 2531 passed, 9 failed, 4322 warnings. Eight failures
  reflected pre-ADR-033 fixture/response expectations; one unrelated performance
  threshold was exceeded under concurrent qualification load. All eight
  affected focused cases passed after their fixture/contract corrections;
  the unrelated performance test passed on isolated rerun (1 passed).
- Full Frontend first run: 216 passed, 1 unrelated intermittent UI test failed;
  the isolated test passed (11 passed), and the final complete Frontend rerun
  passed: **217 passed / 37 files**. TypeScript and production build passed.
- The complete Backend rerun is recorded separately when it finishes.
- `git diff --check` passed before the final qualification rerun.

**Disposition remains implementation candidate, pending complete Backend
qualification and fresh independent security re-review.** MAJ-05 still requires
actual authorized protected candidate/signing/final-approval evidence from a
trusted clean runner. No commit, push, tag, deployment, Human Acceptance,
Checkpoint E closure, or Batch F was authorized.


### ADR-033 final local qualification result (same 2026-10-04 worktree)

The final full Backend rerun, including the twelve new ADR-033 tests,
completed with **2,552 passed, 4,427 warnings, 0 failures** in 294.93 seconds.
The final full Frontend rerun completed with **217 passed across 37 files**.
TypeScript validation, the Vite production build, Python syntax checks and
`git diff --check` passed. The disposable PostgreSQL target was limited to
`127.0.0.1:55432` and stopped after qualification.

These are implementation-author qualification results, **not independent
security re-review or Human Acceptance**. SEC-E-MIN-01 is an implemented,
locally qualified remediation candidate. The protected clean-runner/Cosign/
attributable final-approval evidence for MAJ-05 and a fresh independent
review of the exact final worktree remain outstanding. Checkpoint E stays OPEN.


## Independent security re-review and bounded remediation — 2026-10-04

This continuation independently reviewed the exact dirty worktree at HEAD
`a1918c89bc547d814a0f176ef20688b03fd99997`. It preserved all incoming changes
and performed no Commit, Push, Tag, protected workflow, signing, deployment,
production recovery, Human Acceptance, Checkpoint E closure or Batch F action.

### Repository-policy result

The GitHub branch API reported remote `patch-059-implementation` at
`9e6b657d61c84768e49887774d14ab96939cbad3` with `protected: false`; the
repository ruleset endpoint returned an empty list. The available integration
could not access Environment configuration, so required reviewers,
prevent-self-review and deployment-branch rules for
`patch058-protected-release` and `patch059-final-release-approval` remain
**UNVERIFIED**. The remote branch also does not contain this local candidate.
These facts preserve SEC-E-MAJ-05 as **PARTIALLY REMEDIATED** and prohibit a
real candidate/signing run.

### New findings and remediation

| Finding | Disposition | Result |
|---|---|---|
| SEC-E-RR2-MIN-01 — production readiness duplicated only part of the commercial decision | **REMEDIATED** | `_commercial_runtime_ready` now retains exact Anchor organization-set checking and delegates each state to the ADR-033 shared evaluator. Invalid persisted digests, untrusted/revoked issuer keys, release evidence, trusted time, release range and Anchor state therefore fail readiness exactly as they fail runtime/admin evaluation. |
| SEC-E-RR2-MIN-02 — entitlement/recovery trust inputs allowed links, special files and unbounded reads | **REMEDIATED** | Recovery Anchor/trust and entitlement trust-store loaders now use no-follow descriptors, require regular single-link files, cap inputs at 1 MiB and parse the bytes read from the validated descriptor. Symlink, hardlink and oversize negatives pass. |
| SEC-E-RR2-MIN-03 — offline verification did not bind every pending-dossier evidence file | **REMEDIATED** | Dossier creation now emits bundle-local basenames. The offline verifier requires exact closed descriptor sets and validates every artifact, governed build input, qualification result, scanner result, SBOM, exception file, provenance file, signature summary and signing authorization by exact filename and digest. Missing scanner evidence now fails closed. |

Dependency review found fixable advisories in `urllib3 2.7.0` and the dev-only
`undici 8.10.0`. The locks now resolve `urllib3 2.8.0` and `undici 8.11.2`;
the refreshed npm audit reports zero findings. `pip-audit 2.9.0` now reports
only PYSEC-2026-1325 / CVE-2024-23342 in transitive `ecdsa 0.19.2`, for which
no fixed release exists. The candidate still requires a new exact-source,
exact-artifact, non-expired Human security decision/exception; the PATCH-058
decision is explicitly non-transferable and was not reused or fabricated.

### Independent qualification

- Focused PATCH-059 readiness/recovery/release/shared-status set: **84 passed**.
- Full Backend suite against only the verified disposable
  `127.0.0.1:55432/satco_platform_patch02022_test`: **2,556 passed, 4,427
  warnings, 0 failures** in **228.69 seconds**.
- Frontend exact-lock install/audit: PASS, zero npm vulnerabilities.
- Frontend TypeScript: PASS; Vitest: **217 passed / 37 files**; production
  build: PASS. The existing >500 kB chunk advisory remains non-blocking.
- Backend dependency audit: the three fixable `urllib3` advisories are absent;
  only the governed no-fix `ecdsa` finding remains.
- Python compilation and `git diff --check`: PASS.

### Independent gate decision

The locally reproducible code findings are remediated and independently
qualified. **Checkpoint E remains OPEN and the candidate is NOT READY FOR
HUMAN ACCEPTANCE or release.** Remaining external prerequisites are exact
branch protection, independently verified protected-Environment policies,
trusted clean-runner execution, a candidate-specific Human High-finding
decision, real OIDC/Cosign evidence, distinct attributable final approval,
immutable evidence custody and final Human Acceptance. None was exercised or
claimed by this continuation.


## PATCH-059 post-build security-decision handoff remediation — 2026-10-05

GitHub candidate run `37287240052` qualified and built source
`5f99fbd89045fe24d9f62fb74a3060921d5f0500`, and its pinned Trivy execution
scanned the exact runner-built OCI subject. The run then failed in
`validate-high-exceptions.sh` because the supplied Human exception was bound to
a different, locally produced OCI archive digest. This was an exception-binding
failure before the vulnerability gate completed, not a vulnerability-gate
rejection.

### Gap analysis

The workflow required a security-decision commit at dispatch, before its clean
runner built the authoritative artifact or produced current scanner evidence.
That order contradicted the already accepted Workstream 2 requirement that the
real exception may be created only after those exact facts exist. Reproducing a
GitHub runner's OCI archive digest on another host is not an authority or
custody mechanism. The former single-run sequence therefore could not provide
the documented post-build Human-decision boundary without guessing a digest or
weakening exception validation; neither is permitted.

### Bounded remediation

The dispatch-only candidate workflow now has two mutually exclusive phases.
`pre-decision` performs qualification, builds the artifacts once, runs the
pinned scanners, binds SBOMs, emits closed
`satco.patch059-pre-decision-evidence/v1`, and uploads the exact archive while
publishing its run ID/attempt, artifact ID/API digest and backend digest for
Human review. It accepts no security-decision commit and grants no approval.

After a separate Human security decision, `post-decision` must name all of
those exact identities. It API-authenticates the prior run and artifact,
downloads by immutable artifact ID, verifies the GitHub-reported archive
digest, rejects unsafe or unexpected archive members, reconciles every
artifact/input/qualification/scanner/SBOM digest, validates the exact decision,
and runs the vulnerability gate on the retained evidence. It contains no build,
dependency-install, qualification or scanner step. The original archive,
closed `satco.patch059-pre-decision-artifact/v1` binding and API snapshots are
retained in candidate provenance and revalidated by protected signing and the
offline release verifier.

Focused local qualification passed **113 tests plus 7 subtests** across the
PATCH-059 release-evidence, PATCH-058 supply-chain/dossier and PATCH-059 release
authority suites. Negative coverage includes wrong source, artifact digest,
pre-decision run, run attempt, repository, workflow, branch/event, artifact ID,
expired/substituted archive, substituted scanner evidence, wrong Human
authority and stale/mismatched security decision. Python syntax compilation,
workflow YAML parsing and `git diff --check` passed. The focused test command
used `--noconftest` because these evidence tests require no database; no
PostgreSQL instance, protected workflow, signing authority or release boundary
was exercised.

This remediation changes the candidate source and therefore requires a new
source commit followed by a new authorized clean-runner `pre-decision` run. The
old decision commit cannot be transferred to the new runner artifact. After
reviewing that exact pre-decision bundle, the sole Human Security Authority
must make a new candidate-specific exception decision before a post-decision
run may be dispatched. SEC-E-MAJ-05 remains **PARTIALLY REMEDIATED**; protected
signing, final release approval, deployment and Human Acceptance remain
separate and unauthorized.


## Protected release-chain closure reconciliation — 2026-10-07

This section records fresh exact-source operational evidence after the earlier review sections. Historical FAIL/OPEN/PARTIAL dispositions above remain preserved as chronology. This section supersedes the remaining operational disposition for SEC-E-MAJ-05 only. It does not grant Human Checkpoint E/PATCH acceptance or authorize PATCH-060.

### Exact governed custody chain

- Governed source: `af9b3704edcee0a8c0831508fd97a5a4e5e70f6e`.
- Human Security Decision: `9bfe6af2ce4fd0c012cb6913006e6e6591fbf06a`.
- Pre-decision: run `37582653424`, attempt `1`, artifact `11465656478`, digest `sha256:ce188028d9a296d1150e7d47d7cf3cbb67092999d93ae79fb66e41787600180c`.
- Post-decision candidate: run `37584815792`, attempt `1`, artifact `11465619588`, digest `sha256:5a461b191dd67d3529649af13ef1699aab181f57d55d1b17ad633a58991e3534`.
- Protected signing: run `37585349660`, attempt `1`, artifact `11465824006`, digest `sha256:c08f0ff65bbc38ad449f7619213365005f76749cf15bb77e137d26394d6aed14`.
- Human `FINAL_APPROVAL`: Issue #1 comment `6033396409`; decision run `37589221337`, attempt `1`, artifact `11466839591`, digest `sha256:9e237ed848c883c3680760d394e94264f038ff83cfb06f3b75725593da3e747b`.
- Protected finalization: run `37589807929`, attempt `1`, SUCCESS. Live Human decision and final Environment approval were revalidated; real Sigstore/Cosign OIDC bundles were created; the pinned offline verifier emitted `PATCH059_VERIFY_VERIFIED`.
- Release-ready artifact: `11469375241`, `patch059-release-ready-af9b3704edcee0a8c0831508fd97a5a4e5e70f6e`, digest `sha256:32698be8120d8c59ac7df359556d09219dc86bff91ec37ba95d68dad0c57b3d6`.

### Final finding reconciliation

| Finding | Current disposition | Closure basis |
|---|---|---|
| SEC-E-MAJ-05 | **REMEDIATED / OPERATIONALLY VERIFIED** | Exact-source clean-runner evidence, provenance binding, protected signing approval, real OIDC/Cosign evidence, distinct attributable Human final approval, protected finalization and pinned offline verification all completed successfully. |
| SEC-E-MIN-01 | **REMEDIATED / QUALIFIED** | Human Architecture Acceptance and bounded implementation authorization were recorded on 2026-10-04; the shared evaluator was implemented and qualified, and the subsequent independent re-review found no remaining locally reproducible code blocker. |
| SEC-E-RR-MIN-01 | **REMEDIATED / INDEPENDENTLY QUALIFIED** | Explicit fail-closed object-inventory validation and optimized-interpreter negatives were independently re-reviewed with no remaining code blocker. |

No Critical or Major finding remains open in the recorded Batch E finding set. Protected-chain success does not imply deployment authorization or Human Checkpoint E/PATCH acceptance.

### Closure gate

**READY FOR EXPLICIT HUMAN CHECKPOINT E / PATCH-059 ACCEPTANCE.**

This is evidence reconciliation, not acceptance. Until Human Authority separately accepts Checkpoint E and PATCH-059 closure, PATCH-059 remains OPEN, no deployment authority is inferred, and PATCH-060 remains NOT STARTED / NOT AUTHORIZED.
