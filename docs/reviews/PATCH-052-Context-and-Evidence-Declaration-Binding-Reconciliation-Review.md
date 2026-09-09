# PATCH-052 Context and Evidence Declaration-Binding Reconciliation — Fresh Independent Review

## Review authority and boundary

This review independently evaluates the focused, documentation-only
reconciliation of `B3-052-MAJ-01` against Architecture-052, ADR-025, EDS-052,
IDS-052, Implementation-Plan-052, IRR-052, retained Project configuration and
descriptor identity, Context/Evidence owner models, the `e05200000001` schema,
Batch-2 accepted evidence, and the preserved Batch-3 failure/review.

It does not implement or accept the remediation, create/execute a migration,
change production/tests, rewrite historical evidence, start Batch 4, begin
PATCH-053, stage, commit, or push.

## Independent design verification

The reconciliation identifies the missing fact correctly. The retained
Project selection already gives an immutable reference to exact PackageKey,
PackageVersion, DescriptorDigest, Registry release, and descriptor content,
but neither Context nor Evidence stores which descriptor input it satisfies.
Owner text/type/source fields and current Workspace binding cannot supply that
identity.

Storing only a declaration string would lose descriptor version. Putting an
origin triple directly on Context/Evidence would contradict the accepted rule
that consumption does not give those independent facts package origin. The two
immutable owner-side association relations are therefore the minimum
non-duplicative solution.

The target `(project_id, configuration_revision, package_key,
input_declaration_id)` is exact. The selection FK derives package version and
descriptor digest; the retained revision derives Registry/profile identity;
the retained descriptor maps a Context input to one Context contribution or
an Evidence input to one Evidence requirement. No duplicate package fact
store or copied digest is introduced.

Binding Context at `EngineeringContextSubjectReference` granularity is
necessary because one Context may have multiple subjects and PATCH-052 forbids
one Object satisfying another. Recording the Context version prevents a later
in-place owner update from silently inheriting an old binding. Binding an
Evidence version through a relation preserves general Evidence and supports
explicit many-to-many use without overloading Evidence source metadata.

## Persistence and history verification

The current schema has neither association. One additive migration with two
empty tables, restrictive retained-selection/source FKs, coherence and
immutability guards, two readiness indexes, and least-privilege grants is
sufficient. It need not alter any owner row or retained descriptor. The
proposed `e05200000002` is linear from the current sole source head
`e05200000001`.

No backfill is truthful. The required empty post-upgrade state preserves all
legacy/general Context and Evidence as explicitly unbound. The migration
forbids inference from type, label, free text, source references, current
configuration, Workspace binding, or Deliverable proximity.

Append-only source-version bindings preserve which retained declaration was
asserted. Reconfiguration, Workspace rebind, Registry release/standing change,
and package upgrade do not mutate the assertion. Current readiness uses only
the locked current selection and matching current source versions; historical
interpretation resolves the old selection/descriptor and never substitutes
current state. Missing retained material fails closed.

## DTO, authorization, and readiness verification

The binding requests accept only source handles, exact input selector,
optimistic source/configuration versions, and rationale. Package, tenant,
standing, version, digests, authorization, Human verification, actor, and
provenance remain server-derived. The exact Context/readiness response fields
close the DTO omission that caused the Batch-3 stop without changing owner
authority.

The server order authorizes Project, Workspace, and every owner source before
package/declaration resolution or disclosure, then uses the accepted
configuration-first lock order and shared PATCH-052 UoW. Protected resources
cannot reveal declaration existence, IDs, counts, package state, or readiness.
Replay remains after fresh authority.

Readiness is deterministic: it starts from the exact Deliverable
`required_input_ids`, follows only exact immutable binding rows, compares
source versions/scopes/states, and produces stable bounded rows. Visible
missing/stale/mismatched data becomes findings; hidden, partial, incoherent, or
unresolvable material becomes indeterminate. No free-text, fuzzy, type-only,
order-based, or current-Workspace reconstruction exists.

The accepted selected-Evidence rule is preserved. Only Evidence inputs named
by the evaluated Deliverable control ready-for-review. The fourth Human-review
requirement remains isolated to issue of its canonical exact reviewed
revision. No universal Evidence floor or package approval authority appears.

## Upstream and scope verification

ADR-025 does not govern these associations and needs no change.
Architecture-052 and EDS-052 already require retained-selection derivation,
independent Context/Evidence ownership, exact declarations, selected Evidence,
and historical fail-closed behavior; the reconciliation implements their
implication rather than amending it. IDS-052 named but did not enumerate the
DTOs or persistence representation; this append-only detail closes that
implementation gap without semantic amendment. Implementation-Plan-052 needs
only a later authorized remediation addendum, not an upstream redesign.

The correction is shared PATCH-052 infrastructure delivered once in Batch 3
and reused later. Batch 4 and PATCH-053 remain untouched and unauthorized.
Human Evidence/Deliverable authority, owner lifecycle, and tenant isolation
are not weakened.

## Ten-point acceptance review

| # | Required verification | Result |
|---:|---|---|
| 1 | Context maps to exact declaration identity | PASS — subject/version binding to exact retained input and derived Context declaration |
| 2 | Evidence maps to exact requirement identity | PASS — item/version binding to exact retained input and derived Evidence requirement |
| 3 | Historical interpretation survives reconfiguration/rebind | PASS — retained Project selection/descriptor, never current Workspace reconstruction |
| 4 | No fabricated legacy provenance | PASS — empty tables; legacy/general rows remain unbound; no backfill |
| 5 | Readiness is deterministic | PASS — exact Deliverable inputs, exact bindings, versions, stable order/bounds/closed outcomes |
| 6 | Authorization-before-disclosure remains intact | PASS — owner scopes precede package/declaration resolution and all protected output |
| 7 | No duplicate package fact store | PASS — associations store only source/version plus minimum retained declaration reference |
| 8 | No PATCH-053 behavior | PASS |
| 9 | One migration is sufficient | PASS — two additive relations and guards in linear `e05200000002` |
| 10 | No Human authority is weakened | PASS — packages neither approve Context/Evidence nor manufacture review/issue state |

## Findings and verdict

Critical: **0**

Major: **0**

Minor: **0**

Blocking Minor: **0**

Observation: **0**

Documentation remediation cycles used: **1 of 2**. The first review pass found
that the correct migration categories were frozen but SQL types and stable
constraint/index/guard names were not explicit enough. Cycle 1 added those
details without changing the selected design, persistence verdict, or scope.
The corrected artifact was re-reviewed with no remaining finding.

PATCH-052 CONTEXT / EVIDENCE DECLARATION-BINDING RECONCILIATION:
**PASS / ACCEPTED / COMPLETE**

B3-052-MAJ-01:
**OPEN / REMEDIATION PATH RESOLVED**

CORRECTIVE `e05200000002`:
**ELIGIBLE FOR SEPARATE HUMAN AUTHORITY**

PATCH-052 BATCH-3:
**INCOMPLETE / NOT YET ACCEPTED**

PATCH-052 BATCH-4:
**NOT STARTED / NOT AUTHORIZED**

PATCH-053:
**NOT STARTED / NOT AUTHORIZED**
