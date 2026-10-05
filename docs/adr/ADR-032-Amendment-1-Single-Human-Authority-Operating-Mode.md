# ADR-032 Amendment 1 — Single-Human-Authority Operating Mode

## Status

**ACCEPTED BY HUMAN ARCHITECTURE AUTHORITY — 2026-10-04**

The Human Architecture Authority accepted this amendment in chat on
2026-10-04 for SATCO's current pre-production organizational stage.
`samiphone651-sys`, GitHub user ID `301386823`, is the sole designated Human
Authority.

This acceptance authorizes preparation and independent review of a bounded
implementation-plan amendment only. It does not authorize workflow or code
changes, GitHub configuration changes, commit, push, workflow dispatch,
vulnerability-exception approval, OIDC/Cosign execution, release approval,
deployment, Human Acceptance, Checkpoint E closure or PATCH-060 action.

## Context

ADR-032 requires protected Human signing authorization, a distinct attributable
Human release-approval record and a separate protected finalization step. The
accepted PATCH-058 release foundation likewise distinguishes automated
qualification, Human signing authorization and Human release approval.

Those records require distinct purposes, decisions and evidence. The accepted
governance does not explicitly require the signing reviewer and final-release
reviewer to be different natural persons. SATCO currently has one designated
GitHub Human Authority account. Inventing a second account, shared account or
nominal reviewer would misrepresent personnel independence without adding a
real authority.

## Decision

For PATCH-059 pre-production qualification, one attributable Human Authority
may hold the Human security-exception, protected signing-authorization and
final-release-approval roles, provided that every decision remains a separate,
purpose-bound, fail-closed event with independently identifiable evidence.

In this operating mode, **distinct** means all of the following:

1. a different governed decision purpose;
2. a separate affirmative Human action;
3. a separate protected gate or decision record;
4. an attributable identity and decision timestamp;
5. exact binding to the candidate or signed evidence under review; and
6. rejection of substitution, replay, premature approval or inference from
   automation success.

Distinct does not mean different natural persons in this bounded mode. SATCO
shall not describe this mode as dual-human control, personnel independence,
two-person review or quorum approval.

## Authority and stage separation

The following stages remain separate even when the same Human holds more than
one role:

1. **Automated candidate qualification.** A clean, exact-source workflow
   produces qualification, artifact, scanner, SBOM and provenance evidence.
   Automation has no exception, signing, release, deployment or acceptance
   authority.
2. **Human security-exception decision.** Any permitted High-severity exception
   is a separate post-build decision bound to the exact candidate source,
   backend artifact digest, finding identities, evidence, expiry and retest.
3. **Protected signing authorization.** The Human explicitly authorizes entry
   into the OIDC/Cosign signing job through `patch058-protected-release`.
4. **Final release approval.** After signing succeeds and signed evidence is
   available, the Human performs a second explicit decision through
   `patch059-final-release-approval` over the exact manifest and signing
   authorization.
5. **Deployment authorization.** PATCH-060 owns a later, separate authorization
   over the release-ready evidence and target deployment. PATCH-059 final
   approval is not deployment authorization.
6. **Human Acceptance.** Checkpoint E/PATCH acceptance remains an explicit
   governance decision after required qualification and review. It is not
   inferred from exception approval, signing, final release approval or
   deployment evidence.

## Human identity

The sole Human reviewer authorized by this amendment is:

- login: `samiphone651-sys`;
- immutable GitHub user ID: `301386823`.

Both login and immutable ID must agree in live GitHub API evidence. A renamed
account with the same ID requires a documented identity reconciliation. A
different ID, even with a similar login, fails closed until separately accepted
by Human Architecture Authority.

## Dispatcher and self-review boundary

Both protected Environments shall retain `prevent_self_review: true`. The Human
reviewer therefore shall not dispatch or re-run the protected signing and
finalization workflow.

The protected workflow shall be dispatched only by a dedicated, least-privilege
non-Human GitHub App whose exact actor identity is frozen in reviewed policy.
The App is a mechanical dispatcher only. It is not a Human Authority, reviewer,
approver, independent party or substitute for Human judgment.

The dispatcher shall be scoped to the SATCO repository and the minimum GitHub
permission currently required to create the authorized workflow dispatch:
repository `Actions: write` with implicit metadata access only. That permission
is not endpoint-scoped; it does not by itself prove that the App can reach only
the PATCH-059 workflow. Future separately authorized operational configuration
must therefore constrain the App to the exact workflow/ref and review its
Actions-write reach across every dispatchable workflow. If that confinement
cannot be established with the available GitHub plan/capabilities, protected
execution remains blocked pending governance review.

The App shall have no contents-write, Environment-review, administration,
exception-approval, deployment or Human-Acceptance authority. Protected
workflow execution shall authenticate the run actor and triggering actor
through GitHub API evidence, require both to match the frozen login, immutable
ID and `Bot` actor type, require a first run attempt, and reject Human dispatch
or Human-triggered reruns. App registration, installation and token-custody
evidence shall be retained separately. This amendment intentionally does not
invent an App login, actor ID, App ID or installation ID; protected execution
remains impossible until live values are separately authorized, inspected and
frozen in reviewed policy.

If the dedicated dispatcher is unavailable or cannot be frozen and verified,
the protected workflow remains blocked. `prevent_self_review` shall not be
disabled as a substitute.

## Protected Environment requirements

`patch058-protected-release` and `patch059-final-release-approval` shall be
separate protected GitHub Environments. Each shall:

- name exactly one required Human reviewer: `samiphone651-sys` / `301386823`;
- prevent self-review;
- prohibit administrator bypass;
- restrict deployment branches to the exact accepted branch set;
- expose no broader secret or deployment authority than its stage requires;
- be verified from live API evidence before protected work is accepted; and
- fail closed when its policy differs from the accepted configuration.

The shared PATCH-058 signing Environment may allow only `patch-058` and
`patch-059-implementation`. The PATCH-059 final-approval Environment may allow
only `patch-059-implementation` and shall enforce its accepted 15-minute wait
timer in addition to the evidence-level elapsed-time check. Workflow identity
and OIDC verification shall remain restricted to the accepted repository,
exact workflow path and exact ref. This amendment does not authorize a generic
signer or arbitrary ref.

## Temporal and evidentiary separation

The existing PATCH-059 signer/finalizer workflow identity shall remain one
narrow OIDC identity. Its signing and finalization jobs shall remain ordered so
that final approval cannot become actionable until signing succeeds and a
signed-candidate handoff exists.

Signing authorization shall be purpose-bound to the exact release ID, source
SHA, candidate run ID/attempt, artifact digests and security-decision evidence.
Final approval shall be purpose-bound to the exact release ID, source SHA,
release sequence, signed manifest digest, signing-authorization digest and
signed-handoff digest.

The workflow shall require machine-validated, purpose-bound approval evidence
for both decisions. Approval history shall retain the Human login/ID, decision,
submitted time, Environment, workflow run/attempt, applicable job/deployment
context and canonical evidence digest.

A signed handoff created after successful signing shall bind the candidate,
manifest, signed subjects, signing authorization, workflow run/attempt and
creation time. Final approval shall occur no earlier than 15 minutes after that
handoff time. An early, missing, ambiguous, replayed or digest-mismatched final
approval fails closed and requires a fresh protected attempt.

Final approval and finalization shall cryptographically bind the signed handoff
and the two distinct Human decision records. No pending or rejected decision
may produce a release-ready bundle.

## Authentication and audit controls

The Human account shall use GitHub two-factor authentication with a secure,
preferably hardware-backed method. Recovery material, browser sessions,
personal access tokens and local devices remain Human-controlled security
boundaries.

GitHub Environment review does not provide repository-configurable,
machine-verifiable fresh reauthentication for every approval. Operational
reauthentication may be performed, but SATCO shall not claim per-decision
step-up evidence unless a future accepted mechanism actually produces it.

Environment policy, approval history, workflow-run identity and relevant audit
evidence shall be captured, digest-bound into the release evidence where
applicable and retained outside ordinary short-lived Actions logs. These
controls provide attribution and tamper evidence; they do not create personnel
independence.

## Candidate-specific vulnerability exception

The sole Human Authority may decide a permitted High-severity exception only as
a separate decision before protected signing. Every active record shall satisfy
the PATCH-058 exception contract and bind to the exact candidate source SHA,
backend artifact digest, scanner/finding identity, rationale, compensating
controls, bounded scope, approval time, expiry, retest evidence and active
status.

No PATCH-058 exception transfers to a rebuilt PATCH-059 candidate. The remaining
`ecdsa` advisory requires a new candidate-specific decision after clean build
and scan evidence exists. This amendment does not approve that exception.

## Threat and residual-risk disposition

Separate gates, immutable digests, structured evidence, temporal delay and
fail-closed verification reduce accidental double approval, stale evidence,
replay and artifact substitution. A least-privilege dispatcher can create a run
but cannot supply Human approval.

The sole Human account remains a concentration of authority. Compromise of that
account, its authenticated session or its repository-administration authority
can compromise all Human decisions and may permit attempted policy weakening.
Runtime policy checks, external evidence retention and audit alerts improve
detection but do not provide dual control. This residual risk is accepted only
for the current pre-production organizational stage.

The dispatcher App's minimum GitHub `Actions: write` permission can also create
spurious runs and perform other Actions operations allowed by GitHub's coarse
permission surface. Exact workflow/ref confinement, short-lived installation
tokens, first-attempt checks, protected Human gates and external evidence
custody reduce that exposure but do not turn the App into an independent Human
control or an endpoint-scoped credential.

## Transition and mandatory reassessment

This mode is transitional. PATCH-060 must reassess the single-account residual
risk before any production or customer deployment. PATCH-059 final approval
does not prejudge that decision.

Material changes to Human authority, dispatcher identity, repository ownership,
GitHub plan/capabilities, signing identity, Environment semantics or deployment
risk require governance review before continued use.

## Implementation authorization boundary

Implementation requires a separately reviewed, explicitly Human-authorized
implementation-plan amendment. GitHub App creation, branch/ruleset or
Environment configuration, actual exception approval and every protected run
remain separate Human operational boundaries.

**ADR-032 AMENDMENT 1: ACCEPTED BY HUMAN ARCHITECTURE AUTHORITY ON 2026-10-04. IMPLEMENTATION NOT YET AUTHORIZED.**
