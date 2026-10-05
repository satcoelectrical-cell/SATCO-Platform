# PATCH-059 Batch E — Authenticated Release Evidence Operations

**Status:** ADR-032 Amendment 1 implementation prepared. The repository-side
dispatcher and Environment configuration remains unresolved, so the release
workflow intentionally fails closed before either protected Environment. No
workflow has been dispatched and no signing, release, deployment, or Human
Acceptance event has occurred.

## Authority model

The sole designated Human Authority is GitHub user `samiphone651-sys`, user ID
`301386823`, type `User`. Under Single-Human-Authority Operating Mode v1, that
same Human may make three separate, purpose-bound, attributable decisions:

1. the candidate-specific PATCH-058 `ecdsa` security exception;
2. protected signing authorization in `patch058-protected-release`; and
3. final release approval in `patch059-final-release-approval`.

These are separate events even though the Human identity is the same. This
mode makes no claim of personnel independence, dual-Human control, or quorum.
It does not merge the events and does not allow one event to be replayed for
another purpose. The transitional mode must be reassessed in PATCH-060.

Both protected Environments must designate exactly that Human, retain
`prevent_self_review:true`, disable administrator bypass, and apply the exact
branch restrictions recorded in the policy. The final Environment must also
retain its 15-minute wait timer. The evidence verifier additionally requires
at least 900 seconds between creation of the signed-candidate handoff and the
final approval event.

## Dispatcher configuration boundary

The signing workflow must be dispatched by an allowlisted non-Human GitHub App
installation actor. Both the API-authenticated `actor` and `triggering_actor`
must equal the configured `Bot` identity, and the protected run must be attempt
1 of the exact workflow, repository, branch, and source SHA.

GitHub Configuration Authorization resolved and verified the dedicated App
identity as `satco-patch-059-dispatcher[bot]` (Bot ID `337981151`), App ID
`5193746`, installation ID `168045928`, installed only on
`satcoelectrical-cell/SATCO-Platform` with `Actions: write` and mandatory
`Metadata: read`. `ops/patch059-single-human-authority-policy.example.v1.json`
remains the fail-closed `UNRESOLVED` documentation example. Protected execution
uses the distinct `ops/patch059-single-human-authority-policy.v1.json`, whose
dispatcher is `CONFIGURED` with those exact immutable values. The unprotected
`preflight` job validates that configured policy against the API-authenticated
run before `sign-candidate` requests Environment approval; any actor, triggering
actor, run-attempt, repository, workflow, branch, source-SHA, or configured
dispatcher mismatch fails closed.

## Candidate evidence

The sole candidate producer is the dispatch-only workflow
`.github/workflows/patch059-candidate-evidence.yml` at
`refs/heads/patch-059-implementation`. Its closed
`satco.patch059-candidate-evidence/v2` identity binds:

- repository, workflow path/ref, event, branch, source SHA, and release ID;
- API-authenticated run ID, run attempt, run URL, actor, and triggering actor;
- candidate-specific security-decision commit; and
- SHA-256 of the exact security-decision document.

The consumer fetches the run from the GitHub API and reconciles every field.
Candidate, artifact, provenance, exception, and security-decision mismatch is
fail closed.

## Protected signing event and signed handoff

After preflight, `sign-candidate` enters `patch058-protected-release`. The
workflow captures the authenticated run, Environment, branch-policy, and
approval-history API responses. It requires one approval by the sole Human
with this exact purpose-bound comment:

`SIGN PATCH-059 release_id=<id> source_sha=<sha> candidate_run_id=<id> candidate_run_attempt=<attempt>`

`satco.patch059-human-signing-authorization/v2` binds the policy digest, Human,
configured dispatcher, candidate run/attempt and identity digest, artifacts,
security decision, protected run/attempt, Environment-policy snapshot, exact
comment, submission time, and canonical approval-event digest.

The signer then creates the existing closed manifest, release provenance,
artifact signatures, and manifest attestation. The new
`satco.patch059-signed-candidate-handoff/v1` freezes the manifest, signing
authorization, candidate, artifact, release-provenance, and signature-summary
digests together with signing run ID/attempt and creation time. This immutable
handoff starts the minimum final-approval separation interval.

## Protected final approval and finalization

The separate `finalize` job enters `patch059-final-release-approval`, captures
fresh API evidence, and requires one approval by the same sole Human with an
exact comment binding the release ID, sequence, source SHA, manifest digest,
signing-authorization digest, and signed-handoff digest. It rejects approval
before the 900-second minimum and rejects reuse of the signing approval-event
digest.

`satco.patch059-human-release-approval/v2` binds all preceding evidence, the
final Environment-policy snapshot, protected run identity, exact comment, and
distinct final approval-event digest.
`satco.patch059-release-finalization/v2` then binds the policy, candidate,
artifacts, manifest, dossier, signing authorization, signed handoff, final
approval, and both distinct approval-event digests. Approval and finalization
are separately signed with the pinned signer identity.

## Offline verification and fail-closed controls

`ops/scripts/patch059-release-evidence.py` parses duplicate-member-free JSON
and verifies only bundle-local regular, single-link subjects. It checks closed
contracts, exact digests, candidate and release provenance, exception
freshness, sole-Human identity, configured non-Human dispatcher, attempt-1
protected run, Environment controls, distinct purpose-bound events, 15-minute
separation, handoff/finalization custody, and every cross-document binding.
It then invokes pinned Cosign v2.6.0 in offline mode for the artifact,
manifest, approval, and finalization signatures and the manifest attestation.

The unresolved example policy is valid documentation but invalid execution
policy. A self-consistent forged bundle, Human-dispatched protected run, wrong
actor, rerun attempt, wrong reviewer, self-review-enabled Environment,
administrator bypass, branch-policy drift, missing timer, early final approval,
event reuse, or any digest substitution is rejected.

## Explicit exclusions and next authorization boundary

This implementation does not modify GitHub repository, ruleset, Environment,
App, or Actions settings. It does not authorize workflow dispatch, the
candidate-specific vulnerability exception, real OIDC/Cosign evidence,
release, deployment, or Human Acceptance. Deployment authorization and Human
Acceptance remain separate later events. Application persistence, migrations,
entitlement/runtime semantics, Recovery Authority, deployment workflows, and
PATCH-060 implementation are unchanged.

The next boundary is a separate Human GitHub Configuration Authorization for
the real least-privilege dispatcher and exact repository/Environment controls.
