# PATCH-048 Batch 3 Independent Authorized File Manifest Review

## Verdict

**PASS.** Critical: 0. Major: 0. Minor: 0. The manifest is minimal for the
accepted bounded one-hop EKG read and is independently reviewable.

## Review findings

The review reconciled the accepted 18-node/closed-relation IDS matrices with
the current repository. Existing Batch 1 typed Engineering Context and Context
Relationship adapters are sufficient and remain unchanged. Existing public
canonical application services expose the owner read boundaries needed by
Batch 3; adapters may narrow and compose them but may not access foreign
persistence. The existing Project Context dependency root and router are the
correct request-scoped composition/transport extension points.

No migration, owner schema, repository, UoW, policy, AI or frontend surface is
required. The dirty Engineering Context Relationship service is explicitly
excluded; its accepted public adapter remains the only Batch 3 dependency.

The eleven-file allow-list is sufficient: six existing application files,
five focused test files (one new), and no new owner service or infrastructure
file. It closes all 18 nodes, exact relation vocabulary, authorization before
disclosure, target reauthorization, one-hop termination, 91/100/512KiB bounds,
authenticated continuation/truncation, and payload-free protected outcomes.

## Decision

`PATCH-048-Batch-3-Authorized-File-Manifest.md` is **ACCEPTED / COMPLETE**.
Batch 3 is eligible for implementation only under separately granted Human
authority. Batch 4 and PATCH-049 remain not started.

## Implementation-time prerequisite finding

**B3-CRIT-01 — STOP.** The independent manifest review's repository
reconciliation was incomplete. The current public canonical boundaries do not
provide the exact owner-specific single-node graph reads required by IDS-048:
Execution has no Activity/Milestone read; Project Control has no Change Impact
read; and the existing Project/Workspace graph-safe owner projections are not
available through the accepted Project Context composition seam. Deriving those
facts by scanning broad owner lists or accessing foreign repositories would
violate the accepted owner-specific authorization/non-disclosure contract.

No Batch 3 implementation was retained. Resolution requires a governed
manifest reconciliation that authorizes the minimum canonical owner-port/
application-service additions and their focused owner tests, followed by a new
independent manifest review. This record preserves the initial manifest PASS;
it does not retrospectively rewrite it.

## Focused prerequisite and manifest re-review

**PASS.** Critical: 0. Major: 0. Minor: 0. The reconciled eighteen-file
prerequisite addition is minimal and necessary. Each production change remains
inside the canonical owner: closed schema plus public application-service read.
Each test file is the smallest existing owner service/security surface capable
of proving exact lookup and protected disclosure.

The review confirms that Activity/Milestone and Change Impact retain their
existing UUID identity, owner UoW, lifecycle and authorization. Project and
Workspace retain existing identity and visibility semantics while returning a
narrow graph-safe DTO instead of broad ORM/dictionary data. No generic
resolver, list scan, foreign persistence, Human identity, Project Foundation
node, mutation, migration, Batch 4 or PATCH-049 capability is authorized.

The IDS/Plan additions are implementation-determinism clarifications only;
Architecture and EDS semantics remain unchanged. The exact reconciled boundary
is 29 production/test files. The added Execution repository port,
implementation and focused repository test are necessary because Activity
already has an exact selector but Milestone does not; this prevents prohibited
plan-child scanning while keeping persistence entirely owner-internal.
`B3-CRIT-01`: **RESOLVED**. Reconciled Batch 3
manifest acceptance readiness: **READY**.

## Focused independent re-review — B3-CRIT-02

**PASS.** Critical: 0. Major: 0. Minor: 0. The five-file addition is the
minimum coherent canonical-owner boundary for the accepted Deliverable
Revision node. The repository selector resolves an exact revision UUID under
Organization scope without list/history scanning; the canonical Deliverable
service remains the authorization and safe-projection boundary. Focused owner
contract/service evidence passed (7 tests), including protected foreign or
missing revisions, exact owner linkage, forbidden-field exclusion and no
mutation.

The final Batch 3 implementation/test boundary is exactly **34 files**.
Architecture/EDS authority and persistence remain unchanged. `B3-CRIT-02` is
**RESOLVED** and Batch 3 implementation may resume under standing Human
authority.

## Focused independent re-review — B3-MAJ-01

**PASS.** Critical: 0. Major: 0. Minor: 0. The ten additional files keep
Evidence/File and Technical Report provenance relationship facts inside their
canonical owners and expose only bounded, independently authorized safe link
DTOs. Deliverable representation and Project Control safe relation support use
already-authorized owner files. No foreign repository access, mutation,
persistence ownership transfer, Human identity, report content or hidden total
is exposed. The exact Batch 3 implementation/test boundary is **44 files**.
`B3-MAJ-01` is **RESOLVED**.
