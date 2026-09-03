# PATCH-051 Registry Release-Membership Standing and Descriptor Immutability Reconciliation — Focused Independent Review

## Review authority and boundary

This is the focused independent review of the design/migration-history-only
reconciliation for `WP051-MAJ-01`. It independently inspected the controlling
PATCH-051 architecture, ADR, EDS/IDS and implementation plan; chronological
Batch evidence/reviews and Whole-PATCH finding; source Registry contracts,
assembly and digest code; persistence, installer, parity/readiness,
compatibility, API/frontend consumers, tests; M1 through M5; and the read-only
isolated database evidence.

It creates or executes no migration, changes no implementation, rewrites no
historical revision, accepts no remediation, performs no Whole-PATCH or
quality-gate review, and introduces no PATCH-052 scope.

## Independent semantic verification

The accepted owner is unambiguous. `EXECUTABLE_SUPPORTED` and
`HISTORICAL_READ_ONLY` describe the relationship between an exact immutable
PackageVersion and a particular Registry release. They are not intrinsic
descriptor content. The existing source `DescriptorRegistrationV1` and DB
`discipline_package_registry_memberships` relation are the correct owners; no
new lifecycle model is needed.

Removing standing from canonical descriptor content proves the required
cross-release case: unchanged `P@1.0.0` has one stable DescriptorDigest in R1
and R2, while its registration standing changes and therefore produces a new
RegistryDigest. Exact selected-set, profile, and combination identities do
not change. Compatibility eligibility may change without fabricating a new
identity.

Source-controlled explicit release modules remain authoritative. The DB
remains a derived, immutable projection. Historical resolution remains
anchored to the Project revision's exact observed Registry digest and its
retained membership, rather than substituting current release state.

## Historical and migration-history verification

The current code and M1 independently confirm `WP051-MAJ-01`: standing is
embedded in descriptor canonical bytes, duplicated into descriptor and
membership rows, and read from both by runtime/parity paths. M1 also omitted
the accepted membership-standing lookup index. M1 through M5 remain unchanged
and form one linear source graph ending at `e05100000005`; no M6 exists.

The isolated DB evidence proves every observed membership standing matches
both its descriptor copy and durable manifest. Historical standing therefore
does not need to be guessed. It also proves a crucial limit: the 145
`maj04-*` fixture projections and 33 Project revisions use the defective
descriptor hashes. Rehashing those records would rewrite history. The
reconciliation correctly requires M6 to fail closed on such non-empty legacy
state rather than fabricate or cascade identities.

The authoritative PATCH-051 source release is empty. On that governed state,
one forward `e05100000006` from `e05100000005` can transactionally enforce
empty/unreferenced preconditions, add the accepted membership index, and drop
only descriptor-scoped standing. No row, digest, pin, profile, Workspace,
Audit value, role, trigger, or grant changes. Fresh M1-to-M6 and empty
M5-to-M6 paths converge. A downgrade is truthful only while the post-M6
Registry remains empty; otherwise it must fail closed.

The current isolated database is safe for diagnosis but is not a valid
in-place M6 target. Recreating it is required before separately authorized M6
execution/testing. No cleanup is authorized or performed by this review.

## Runtime, readiness, and security verification

The bounded runtime changes are sufficient: registration owns standing;
descriptor digest excludes it; Registry digest includes it; installer and
readiness compare source registration membership to projected membership;
compatibility, supported-package API, selection, and effective/historical
Workspace paths resolve the appropriate membership. Frontend behavior and
Project/Workspace/configuration identities require no redesign.

Readiness can remain fail closed by independently validating intrinsic
descriptor bytes/digests and exact source-versus-projection membership
standings. The runtime role remains SELECT-only over Registry tables; the
installer boundary remains exclusive. Standing remains an eligibility input
and grants no engineering-data access, tenant visibility, entitlement, role,
or Human authority.

No Architecture or ADR amendment is required. EDS/IDS semantics remain
unchanged; the focused append-only reconciliation records implementation and
migration-history recovery. No PATCH-052 capability is introduced.

## Fifteen-point independent review

| # | Required verification | Result |
|---:|---|---|
| 1 | Descriptor identity remains immutable | PASS |
| 2 | Standing varies across releases without descriptor identity change | PASS |
| 3 | Source Registry remains authoritative | PASS |
| 4 | DB remains derived projection | PASS |
| 5 | Historical standing is truthfully recoverable | PASS — membership and manifest agree; no fabricated default |
| 6 | Historical releases remain readable | PASS — exact observed release membership is retained |
| 7 | No Project/Workspace identity is fabricated | PASS |
| 8 | Digest semantics match accepted design | PASS |
| 9 | Readiness can reconcile source/projection correctly | PASS |
| 10 | Runtime role cannot mutate Registry projection | PASS |
| 11 | Standing grants no engineering-data authority | PASS |
| 12 | No PATCH-052 scope is introduced | PASS |
| 13 | One forward migration is sufficient | PASS — for the authoritative empty state, with fail-closed preflight |
| 14 | M1–M5 remain historically unchanged | PASS |
| 15 | No implementation occurred during reconciliation | PASS |

## Findings

Critical: **0**

Major: **0**

Minor: **0**

Observation: **1** — the disposable isolated DB contains committed legacy
test-fixture projections and must be recreated under separate authority before
M6 execution proof; it must not be migrated or cleaned in this task.

## Verdict

The accepted lifecycle owner, digest boundaries, historical truth, bounded
runtime corrections, and one-forward-migration recovery are sufficiently
precise. The fail-closed non-empty-state rule prevents historical provenance
rewrite, while the authoritative empty PATCH-051 release permits exact fresh
and upgrade convergence without Architecture/ADR redesign.

PATCH-051 REGISTRY STANDING / DESCRIPTOR IMMUTABILITY RECONCILIATION:
PASS / ACCEPTED / COMPLETE

WP051-MAJ-01:
OPEN / REMEDIATION PATH RESOLVED

Corrective M6:
ELIGIBLE FOR SEPARATE HUMAN AUTHORITY

PATCH-051:
OPEN / NOT CLOSED

QG-11:
NOT YET ELIGIBLE
