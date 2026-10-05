# ADR-032 Amendment 2 — Zero-Cost Human Decision-Time Evidence

Status: HUMAN AUTHORIZED FOR PATCH-059 IMPLEMENTATION
Authority: Human Architecture/Governance
Scope: PATCH-059 release evidence only

## Decision

PATCH-059 preserves the accepted substantive control that the final Human Authority decision occurs no earlier than 900 seconds after the signed release handoff. GitHub Environment review history remains mandatory execution authorization, but it is not used as the Human-decision clock because the review-history API does not expose a Human review timestamp.

The authoritative Human Authority Decision Record is a canonical SSH-signed GitHub issue comment named `FINAL_APPROVAL`. Its GitHub server `created_at` is the authoritative decision timestamp. The temporal baseline is a canonical `HANDOFF_MARKER` issue comment created by the protected signing workflow only after the signed handoff has been assembled and verified. Its GitHub server `created_at` is the baseline timestamp.

The recorded interval MUST be at least 905 seconds. The five-second margin is deliberate; it preserves the accepted 900-second minimum while avoiding boundary ambiguity.

## Authority and binding

The sole Human Authority remains `samiphone651-sys`, immutable GitHub user ID `301386823`. The Human decision payload MUST be SSH-signed with the already pinned Human Authority signing key and namespace `satco-patch059-final-approval-v1`.

The marker and decision bind the repository numeric identity and full name, release ID and sequence, exact source SHA, candidate run ID/attempt, release manifest digest, signing authorization digest, signed handoff digest, marker comment ID/node ID/body digest/server timestamp, and a fresh 256-bit nonce.

Runner-local time, commit author/committer time, Environment job start time, deployment status time, and inferred review time MUST NOT substitute for the GitHub server comment timestamps.

## Separate execution authorization

After the Human decision record passes verification, the existing least-privilege PATCH-059 Dispatcher App may dispatch a distinct final protected workflow run. That run MUST be App-dispatched, run attempt 1, and enter `patch059-final-release-approval`.

The Human Authority MUST then separately approve that Environment with the exact purpose-bound comment that references the verified FINAL_APPROVAL comment ID and decision/body digests. Environment approval authenticates execution authorization; it does not establish the Human-decision timestamp.

## Fail-closed mutation and replay rules

The verifier MUST fail closed on missing, edited, deleted, duplicate, ambiguous, stale, replayed, or mismatched marker/approval evidence; API failure or pagination ambiguity; wrong repository/actor/source/run; invalid SSH signature; nonce reuse; or an already-consumed decision.

For decision comments, `created_at == updated_at` is required. The live GitHub objects are re-fetched immediately before finalization and must reproduce the previously verified decision evidence byte-for-byte.

A verified decision is single-use. The final workflow records consumption before irreversible finalization. A failed finalization after consumption requires a fresh Human decision.

## Workflow topology

1. Protected App-dispatched signing run receives the existing signing Environment authorization.
2. Candidate artifacts are signed and the signed handoff is assembled.
3. The signing run creates and revalidates the HANDOFF_MARKER and uploads the signed-candidate bundle.
4. Human waits until at least 905 recorded seconds after marker `created_at`.
5. Human prepares the exact FINAL_APPROVAL payload, signs it with the pinned SSH key, and posts it to the dedicated governance issue.
6. The `issue_comment.created` decision workflow verifies identity, SSH signature, live marker, exact bindings, uniqueness, and the 905-second interval; it publishes immutable decision evidence.
7. Only then may the Dispatcher App start the distinct final protected run.
8. Human separately approves the final Environment with the exact decision-bound comment.
9. Final run re-fetches and revalidates all live decision evidence, records single-use consumption, finalizes, signs final records, and runs offline verification.

## Cost and privilege constraint

This amendment requires no paid GitHub plan or external timestamp service. The Dispatcher App permissions are not broadened. GitHub Actions uses only job-scoped repository permissions required for reading evidence and writing the marker/consumption comments.

## Evidence-chain consequence

Any source-changing implementation of this amendment invalidates the previous PATCH-059 source-bound release chain for authorization purposes. Previous runs remain historical evidence only. A fresh pre-decision candidate, Human security decision, post-decision candidate, protected signing run, Human final decision, and final protected run are required.

## Non-claims

This amendment does not create personnel independence, dual-Human control, deployment authorization, or Human Acceptance. SEC-E-MAJ-05 remains open until the complete fresh release evidence chain succeeds and is independently reviewed.

## Schema lineage

The amended signing authorization and final release approval records use `satco.patch059-human-signing-authorization/v3` and `satco.patch059-human-release-approval/v3`. The v2 schemas remain unchanged as historical contracts and MUST NOT be used for the fresh Amendment 2 release chain.
