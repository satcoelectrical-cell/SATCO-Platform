# PATCH-059 Batch E — ADR-032 Amendment 1 Implementation-Plan Amendment

## Status and authority

**Status:** PROPOSED — AWAITING HUMAN IMPLEMENTATION AUTHORIZATION

**Architecture authority:** ADR-032 Amendment 1, Human accepted 2026-10-04

**Scope:** Single-Human-Authority evidence and enforcement for SEC-E-MAJ-05

This plan is prepared under the Human Architecture authorization granted on
2026-10-04. It has not been authorized for implementation.

Acceptance of this plan would authorize only the bounded repository changes and
local/non-authoritative qualification described below. It would not authorize
GitHub App creation or installation, repository/ruleset/branch/Environment or
Actions setting changes, commit, push, candidate dispatch, vulnerability
exception approval, protected workflow execution, OIDC/Cosign evidence, release
approval, deployment, Human Acceptance, Checkpoint E closure or PATCH-060.

## Objective

Implement the accepted Single-Human-Authority operating mode without pretending
personnel independence and without weakening the existing separation between:

1. automated candidate qualification;
2. Human security-exception decision;
3. protected signing authorization;
4. final release approval;
5. deployment authorization; and
6. Human Acceptance.

The implementation shall retain the narrow PATCH-059 signer workflow/ref and
its existing signing-then-finalization job ordering. It shall not add a second
OIDC signer identity, generic reusable signer or production deployment path.

## Workstream 1 — versioned authority and evidence contracts

Add closed, versioned contracts for:

- `satco.patch059-single-human-authority-policy/v1`;
- `satco.patch059-human-signing-authorization/v2`;
- `satco.patch059-signed-candidate-handoff/v1`;
- `satco.patch059-human-release-approval/v2`; and
- `satco.patch059-release-finalization/v2`.

The authority policy shall freeze:

- Human login `samiphone651-sys` and GitHub user ID `301386823`;
- signing and final-approval Environment names;
- accepted repository, branch and workflow/ref identities;
- minimum final-approval delay of 15 minutes;
- exact structured approval-evidence formats:
  `SIGN PATCH-059 release_id=<release-id> source_sha=<source-sha>
  candidate_run_id=<candidate-run-id>
  candidate_run_attempt=<candidate-run-attempt>` and
  `FINAL PATCH-059 release_id=<release-id> release_sequence=<release-sequence>
  source_sha=<source-sha>
  manifest_sha256=<sha256-digest>
  signing_authorization_sha256=<sha256-digest>
  signed_handoff_sha256=<sha256-digest>`; and
- the dedicated GitHub App dispatcher login, immutable actor ID, `Bot` actor
  type, registered App ID and repository installation ID after that App is
  separately authorized, created and inspected.

No production-authoritative policy may contain a placeholder, wildcard or
mutable unreviewed dispatcher identity. Until the App identity is available and
frozen in source, protected execution shall remain impossible.

The v2 signing-authorization record shall bind at minimum:

- operating-mode and policy digest;
- exact Human login/ID;
- purpose `protected-signing-authorization`;
- exact Environment;
- release ID and source SHA;
- candidate run ID/attempt and candidate identity digest;
- artifact digests and security-decision commit/digest;
- workflow run ID/attempt and signing job identity;
- dispatcher and triggering-actor identities;
- approval comment, submitted time and canonical approval-event digest; and
- immutable evidence/run references.

The signed-candidate handoff shall bind the v2 signing authorization, release
manifest, signed subjects, signature/attestation evidence, workflow
run/attempt, signing job result and creation time.

The v2 final approval shall bind at minimum:

- the same operating-mode and policy digest;
- exact Human login/ID;
- purpose `final-release-approval`;
- exact final-approval Environment;
- release ID, sequence and source SHA;
- exact manifest and signed-handoff digests;
- signing-authorization digest;
- artifacts, provenance, dossier, exception and security-decision digests;
- workflow run/attempt and finalization job identity;
- approval comment, submitted time and canonical approval-event digest; and
- evidence that the minimum delay elapsed.

Finalization v2 shall bind both Human decision digests and the signed handoff.
All schemas remain closed and reject unknown, missing, duplicate or
type-invalid fields.

## Workstream 2 — candidate and security-decision evidence

Amend `patch059-candidate-evidence.yml` and its verifier only as needed to:

- record API-authenticated run actor and triggering actor identities;
- retain run ID/attempt, workflow path/ref, repository/head repository, event,
  branch and exact source SHA;
- retain the exact post-build Human security-decision commit and evidence
  digest; and
- preserve that candidate qualification is automated and grants no Human
  approval.

Do not approve or fabricate the remaining `ecdsa` exception. The real exception
record can be created only after an authorized clean candidate produces its
exact source SHA, backend artifact digest and current scanner evidence.

When later presented for Human decision, the record shall identify
`samiphone651-sys` / `301386823`, be scoped to the exact candidate, expire no
later than 30 days after approval, and require retest on any relevant source,
artifact, dependency, advisory, algorithm, runtime-path, privilege, topology or
control change. Separate scanner/finding identities require separate records.

## Workstream 3 — protected workflow enforcement

Amend `patch059-sign-release.yml` while preserving its existing exact workflow
path/ref and its `sign-candidate` then `finalize` dependency.

Before accepting signing authorization, the workflow shall:

1. fetch and authenticate its own workflow-run API record;
2. require `workflow_dispatch`, the exact repository/workflow/ref/source and
   `run_attempt == 1`;
3. require both actor and triggering actor login, immutable ID and actor type to
   match the frozen dispatcher App and require the reviewed App/installation
   configuration evidence;
4. reject the Human Authority as dispatcher or triggering actor;
5. query and validate the live signing-Environment policy;
6. require exactly the accepted Human reviewer login/ID and `User` actor type,
   `prevent_self_review: true`, `can_admins_bypass: false` and custom branch
   restrictions naming only `patch-058` and `patch-059-implementation`;
7. require exactly one approved signing event for the signing Environment;
8. require the exact approval comment
   `SIGN PATCH-059 release_id=<release-id> source_sha=<source-sha>
   candidate_run_id=<candidate-run-id>
   candidate_run_attempt=<candidate-run-attempt>` as one ASCII line and match it
   to the release, source and exact candidate run attempt; and
9. create signing authorization v2 before obtaining OIDC signing authority.

After signing and verification, the workflow shall create and upload the closed
signed-candidate handoff and expose its exact manifest, signing-authorization
and handoff digests in the run summary for Human review.

The finalization job shall remain dependent on successful signing. Before final
approval is accepted, it shall:

1. revalidate source, workflow-run and dispatcher identity;
2. download the exact same-run signed-candidate artifact without fallback;
3. validate the signed handoff and every referenced digest;
4. query and validate the live final-approval Environment policy;
5. require exactly the accepted Human reviewer login/ID and `User` actor type,
   `prevent_self_review: true`, `can_admins_bypass: false`, a 15-minute wait
   timer and a custom branch restriction naming only
   `patch-059-implementation`;
6. require a distinct approved event for the final-approval Environment;
7. require the exact approval comment
   `FINAL PATCH-059 release_id=<release-id> release_sequence=<release-sequence>
   source_sha=<source-sha>
   manifest_sha256=<sha256-digest>
   signing_authorization_sha256=<sha256-digest>
   signed_handoff_sha256=<sha256-digest>` as one ASCII line and match it to the
   release ID, sequence, source, manifest, signing authorization and signed
   handoff;
8. require final approval time to be at least 15 minutes after signed-handoff
   creation; and
9. reject missing, early, replayed, ambiguous or mismatched evidence.

An invalid or premature approval shall fail the run. It shall not be repaired by
editing evidence or re-running a job; a new App-dispatched protected run and new
Human decisions are required.

## Workstream 4 — offline verification and custody

Extend `patch059-release-evidence.py` to authenticate:

- the closed Single-Human-Authority policy and its digest;
- exact dispatcher and triggering-actor login, immutable ID and `Bot` type plus
  the reviewed App/installation configuration evidence;
- signing authorization v2;
- the signed-candidate handoff;
- final approval v2;
- same-Human identity across the two distinct purposes;
- distinct Environments and approval events;
- workflow run/attempt and applicable job context;
- structured approval evidence and canonical event digests;
- temporal ordering and the 15-minute minimum; and
- finalization v2 binding both decisions and every release subject.

The verifier shall explicitly reject any claim of dual-human control or
personnel independence in Single-Human-Authority evidence.

Approval history, live Environment-policy snapshots, workflow-run identity and
the authority policy shall be included in the release-evidence custody contract
with exact digests. Ordinary Actions retention alone is not sufficient
production custody.

## Workstream 5 — documentation and findings

Update the release-evidence operations contract to distinguish:

- Human reviewer identity from workflow dispatcher identity;
- two purpose-distinct decisions by the same named Human from any claim that
  different people or personnel independence exist;
- GitHub self-review prevention from personnel independence;
- protected release approval from deployment authorization; and
- final release approval from Human Acceptance.

Update the PATCH-059 qualification/security record so SEC-E-MAJ-05 remains
partially remediated until all of the following exist and are independently
verified:

- accepted implementation authorization;
- implemented and reviewed v2 evidence contracts;
- exact dispatcher App identity;
- protected branch/ruleset and both Environment policies;
- current clean-runner candidate evidence;
- candidate-specific Human `ecdsa` decision;
- two real, purpose-distinct Human approval events;
- real OIDC/Cosign and offline-verification evidence; and
- immutable evidence custody.

No documentation may describe the two approvals as independent Human review,
dual control, two-person control or quorum.

## Workstream 6 — required tests

Add deterministic positive tests proving one exact Human login/ID may perform
both purpose-distinct approvals when every other invariant holds.

Add negative tests for at least:

- Human-dispatched protected workflow;
- wrong, missing or mutable dispatcher identity, non-`Bot` actor type or
  mismatched App/installation configuration;
- changed triggering actor or Human-triggered rerun;
- run attempt greater than one;
- wrong reviewer login or immutable ID;
- missing reviewer, self-review prevention or no-bypass control;
- broad or wrong Environment branch policy;
- wrong Environment or reused approval event;
- missing, malformed or purpose-confused approval evidence;
- wrong release, source, candidate run, manifest or authorization digest;
- wrong candidate run attempt or signed-handoff digest;
- final approval before signed handoff;
- final approval less than 15 minutes after handoff;
- changed signed artifact or handoff after approval;
- missing policy, approval history or policy snapshot;
- unsupported v1/v2 mixing or unknown fields;
- final approval treated as deployment authorization; and
- signing/final approval treated as Human Acceptance.

Retain all existing wrong repository, workflow/ref, event, branch, source,
artifact, sequence, exception, signature, dossier and post-approval-mutation
negatives.

Local tests shall use non-authoritative fixtures and signature doubles only.
They must not dispatch a workflow, request OIDC, change GitHub configuration or
create actual Human approval evidence.

## Proposed file delta

Subject to Human Implementation Authorization, the bounded implementation is
expected to modify:

- `.github/workflows/patch059-candidate-evidence.yml`;
- `.github/workflows/patch059-sign-release.yml`;
- `ops/scripts/patch059-candidate-evidence.py`;
- `ops/scripts/patch059-release-evidence.py`;
- `ops/patch059-single-human-authority-policy.v1.schema.json`;
- `ops/patch059-single-human-authority-policy.example.v1.json`;
- `ops/patch059-human-signing-authorization.v2.schema.json`;
- `ops/patch059-signed-candidate-handoff.v1.schema.json`;
- `ops/patch059-human-release-approval.v2.schema.json`;
- `ops/patch059-release-finalization.v2.schema.json`;
- `backend/tests/test_patch059_release_evidence.py`;
- `ops/tests/test_patch059_release_authority.py`;
- `docs/implementation/PATCH-059-Batch-E-Release-Evidence-Operations.md`; and
- `docs/reviews/PATCH-059-Batch-E-Qualification-Draft.md`.

No application-domain persistence, database migration, entitlement/runtime
semantics, Recovery Authority, production deployment workflow or PATCH-060
implementation is in scope.

## Operational configuration delta requiring separate future authorization

This plan does not authorize the following changes, but the implemented code
must fail closed until later Human operational authorization establishes them:

1. Create one dedicated GitHub App installed only on the SATCO repository, with
   repository `Actions: write` and implicit metadata access only. Grant no
   contents, administration, Environment, secret, deployment or member-write
   permission. Use short-lived installation tokens held outside repository and
   workflow content. Freeze the inspected App login, immutable actor ID, `Bot`
   type, registered App ID and repository installation ID in the authority
   policy before protected execution. No exact identity or configuration is
   asserted by this plan.
2. Configure `patch058-protected-release` with the sole required reviewer
   `samiphone651-sys` / `301386823`, `prevent_self_review: true`,
   `can_admins_bypass: false`, and custom deployment-branch policies permitting
   only `patch-058` and `patch-059-implementation`.
3. Configure `patch059-final-release-approval` with the same sole reviewer,
   `prevent_self_review: true`, `can_admins_bypass: false`, a 15-minute wait
   timer, and a custom deployment-branch policy permitting only
   `patch-059-implementation`. The wait timer supplements rather than replaces
   the evidence-level check that the approval itself occurred at least 15
   minutes after the signed handoff.
4. Activate branch/ruleset protection for `patch-059-implementation` and
   `patch-058-security-decisions` with no bypass actors, deletion and
   non-fast-forward updates blocked, and signed commits required. Any required
   status-check contexts shall be frozen by exact GitHub check name only after
   their registered identities have been observed and reviewed; no guessed or
   wildcard context is permitted.
5. Restrict protected workflow dispatch to the exact registered workflow path
   and accepted branch/ref. Because GitHub `Actions: write` is not
   endpoint-scoped, inspect every dispatchable workflow and apply an exact
   workflow-execution policy where the repository plan supports it. If the App
   can reach an unreviewed authority-bearing workflow, stop for governance
   review rather than treating least privilege as proved. Retain the current
   exact OIDC repository, workflow/ref and workflow-SHA verification; do not
   broaden trust to a branch wildcard or second finalization signer.
6. Configure evidence retention/export so API approval history, Environment
   policy snapshots, workflow-run identity, signed bundles and offline-verifier
   results are retained outside ordinary short-lived Actions logs.

Each item requires live post-configuration inspection before it may be treated
as satisfied. Workflow YAML assertions or this plan are not evidence of actual
GitHub policy.

## Qualification and review gates

Implementation qualification shall include YAML/JSON/schema validation, shell
syntax checks, focused release/security tests, affected backend/operations test
suites, offline-verifier positive/negative fixtures and `git diff --check`.

A fresh exact-worktree security review shall verify that the implementation:

- does not create a second Human identity;
- does not silently disable self-review or admin-bypass protection;
- does not broaden OIDC signer identity;
- fails closed until the exact dispatcher and live policies exist;
- preserves candidate, exception, signing, final approval, deployment and Human
  Acceptance boundaries; and
- states the sole-account residual risk accurately.

After local qualification, all GitHub settings, dispatcher creation, real
exception decision and protected execution remain separately authorized Human
operational steps.

## Human Implementation Authorization required

Implementation may begin only after the Human Authority explicitly accepts this
bounded plan. A later authorization must not be interpreted as permission to
change GitHub settings or perform a real protected run unless those operational
actions are also explicitly authorized.

**IMPLEMENTATION STATUS: NOT AUTHORIZED.**
