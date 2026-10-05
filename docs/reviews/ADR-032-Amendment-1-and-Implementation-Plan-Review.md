# ADR-032 Amendment 1 and Implementation-Plan Amendment Review

## Review status

**PASS — READY FOR HUMAN IMPLEMENTATION AUTHORIZATION CONSIDERATION**

Review date: 2026-10-04

Review scope: ADR-032 Amendment 1 and its proposed bounded implementation-plan
amendment only

This is a separate adversarial document-review pass. It is independent of any
implementation execution because no workflow, code, GitHub configuration,
exception, signing, release or deployment action was performed. It is an AI
review and does not claim a second Human reviewer or personnel independence.

## Sources reviewed

- Constitution and Governance Model;
- ADR-031, accepted ADR-032 and accepted ADR-033;
- PATCH-058 EDS, IDS and Implementation Plan release/security authority;
- ADR-032's existing bounded implementation amendment;
- PATCH-059 candidate and signing/finalization workflows;
- PATCH-059 release-evidence operations and qualification records;
- current release-evidence verifier and tests; and
- GitHub Environment self-review, required-reviewer and workflow-dispatch
  semantics.

## Governance determination

The accepted source documents require separate automated qualification, Human
signing authorization, Human release approval, deployment authorization and
Human Acceptance. They require a distinct attributable release-approval record,
but do not explicitly require signing and release approval to be performed by
different natural persons.

ADR-032 Amendment 1 is therefore a legitimate bounded governance clarification,
not a contradiction of ADR-031/032/033. It correctly requires explicit Human
Architecture acceptance instead of silently changing the meaning of
"distinct."

## Requirements traceability

| Accepted requirement | Amendment/plan disposition | Review |
| --- | --- | --- |
| One real Human Authority; no fictitious identity | Exact login/immutable ID; explicit prohibition on dual-control claims | PASS |
| Automated candidate qualification remains non-authoritative | Separate candidate stage and evidence | PASS |
| Human security exception remains separate | Exact post-build decision, no exception granted by the amendment | PASS |
| Protected Human signing authorization | First protected Environment and v2 authorization evidence | PASS |
| Distinct final Human release approval | Second Environment, second action, different purpose/evidence | PASS |
| Final approval occurs only after signing evidence | Existing job dependency plus signed handoff | PASS |
| Temporal separation | Minimum 15 minutes after handoff, fail-closed on early approval | PASS |
| `prevent_self_review: true` retained | Dedicated non-Human App dispatcher; Human dispatch/re-run rejected | PASS |
| Dispatcher is not represented as Human independence | Explicitly mechanical and non-authoritative | PASS |
| Dispatcher identity is not invented | Live login/ID/type/App/installation values remain unset until separate authorization and inspection | PASS |
| No administrator bypass and exact restrictions | Required policy assertions and evidence snapshots | PASS |
| Immutable source/artifact/release binding | Candidate, manifest, handoff and approval digests | PASS |
| Separate deployment authorization | Explicit PATCH-060 boundary | PASS |
| Human Acceptance remains separate | Explicit non-inference rule | PASS |
| PATCH-060 reassessment before production/customer deployment | Mandatory transition condition | PASS |

## Adversarial review

### Sole-account compromise

The amendment correctly identifies the sole Human account as a concentration of
authority. Two approval clicks do not stop an attacker who controls that account
and repository administration. The proposed controls improve sequencing,
attribution, artifact integrity and detection; they do not manufacture dual
control. Residual risk is accurately limited to the current pre-production
stage and made subject to PATCH-060 reassessment.

### Accidental double approval

Separate Environments alone would be insufficient. The plan adds the necessary
job dependency, signed handoff, exact purpose/digest evidence and 15-minute
minimum. Requiring a fresh App-dispatched run after early or invalid approval
prevents repair-by-rerun and stale approval reuse.

### Dispatcher compromise

The dispatcher cannot approve an Environment and receives no contents-write or
administration permission. GitHub nevertheless exposes workflow dispatch
through coarse repository `Actions: write`, not an endpoint-scoped permission.
Exact workflow/ref controls, a review of every dispatchable workflow,
short-lived installation tokens, frozen actor/App/installation identity and
rejection of reruns are therefore required. If those controls cannot confine
the App with the repository's available plan/capabilities, execution remains
blocked; the review does not describe least privilege as already configured.

### Policy weakening

Live Environment-policy validation, no-bypass requirements and captured policy
snapshots detect ordinary misconfiguration. They cannot fully resist a
compromised sole administrator who changes both repository policy and reviewed
source. The amendment discloses rather than conceals this residual risk.

### Evidence substitution and replay

Versioned closed schemas, canonical approval-event digests, exact run/attempt,
candidate, manifest, signing-authorization and handoff bindings provide a
coherent fail-closed design. Requiring a new run after any invalid protected
decision avoids ambiguous approval-history reuse.

### Reauthentication

The documents do not claim a GitHub capability that is unavailable or
unverifiable. Secure account-level 2FA is required, while per-approval step-up is
described as procedural unless a future accepted mechanism produces verifiable
evidence.

## Review observations incorporated into the plan

1. Preserve the existing single PATCH-059 OIDC workflow identity instead of
   creating another signer identity for finalization.
2. Use one ordered workflow run with two protected jobs; distinguish the Human
   decisions by purpose, Environment, time and digest-bound event evidence.
3. Measure the 15-minute interval from creation of the signed-candidate handoff,
   not merely from the earlier signing approval.
4. Reject job reruns and require a fresh App dispatch after invalid or premature
   approval.
5. Freeze the dispatcher App identity in reviewed source before any protected
   execution; no placeholder or mutable wildcard is production-authoritative.
6. Keep actual GitHub policy configuration and the candidate-specific `ecdsa`
   decision outside implementation authority.
7. Freeze exact purpose-bound approval comment formats so an ordinary approval
   click cannot be reinterpreted after the fact.
8. Keep required status-check names unresolved until GitHub has registered and
   exposed their exact identities; guessed or wildcard contexts are prohibited.
9. Bind signing approval to the exact candidate run attempt, and bind final
   approval to release sequence, source SHA and the signed-handoff digest.
10. Name `patch-058` explicitly wherever the shared signing Environment branch
    policy is specified.

## Documentation defects corrected during final review

1. Replaced wording that could imply “different people” with an explicit
   same-Human, purpose-distinct decision boundary.
2. Completed the approval-comment bindings for candidate attempt and signed
   handoff, preventing a Human approval event from being reinterpreted across
   reruns or handoffs.
3. Replaced the ambiguous “accepted PATCH-058 branch” label with exact branch
   `patch-058`.
4. Recorded the non-endpoint-scoped nature of GitHub `Actions: write`, required
   dispatchable-workflow reach review, and preserved fail-closed behavior when
   exact confinement cannot be established.
5. Replaced conditional/vague implementation file descriptions with an exact
   proposed schema and test-file delta.

## Findings

- Open Critical: 0
- Open Major: 0
- Open Minor: 0
- Documentation defects found in final review: 5, all corrected in this
  package
- Residual security risks: documented and intentionally retained for Human
  decision; no risk is silently treated as remediated.

The document set is internally consistent with the accepted Single-Human-
Authority decision and preserves the superior governance boundaries.

## Review conclusion and boundary

ADR-032 Amendment 1 is properly recorded as Human accepted. The corresponding
implementation-plan amendment is sufficiently bounded, testable and fail-closed
to be presented for explicit Human Implementation Authorization.

This PASS is a document-review result only. It does not authorize implementation
or GitHub changes and does not close SEC-E-MAJ-05, Checkpoint E or PATCH-059.
