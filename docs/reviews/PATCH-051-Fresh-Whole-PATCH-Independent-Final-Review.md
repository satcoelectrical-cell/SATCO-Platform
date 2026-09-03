# PATCH-051 Fresh Whole-PATCH Independent Final Review

## Review control

| Field | Result |
|---|---|
| Authority | HUMAN PATCH-051 FRESH WHOLE-PATCH INDEPENDENT FINAL REVIEW AUTHORITY: GRANTED |
| Mode | Review only |
| Worktree | Existing cumulative dirty/untracked PATCH-051 state preserved |
| Verdict | FAIL / STOPPED |
| Critical / Major / Minor / Observation | 0 / 1 / 0 / 0 |
| Implementation or migration action | None; not authorized |

This review is independent of the prior Batch reviews. It began from the
actual accepted Architecture-051, ADR-024, EDS-051 and focused persistence
reconciliation, IDS-051, Implementation-Plan-051, acceptance/review history,
final migration chain, and current production/test source. Historical FAIL and
STOPPED artifacts were not modified.

## Bounded fresh review method

The review first reconciled the worktree and authoritative artifacts, then
compared the final Core identity, descriptor, source Registry, lifecycle,
projection, compatibility, migration, and related test implementations against
the accepted contracts. `git diff --check` passed and the staged-file set was
empty at review start.

The mandatory stop rule was reached during the trusted Registry lifecycle
inspection. Remaining Whole-PATCH surfaces and the requested validation suite
were not given a fresh verdict after that point. Prior test evidence is not
substituted for the unfinished fresh validation.

## WP051-MAJ-01 — PackageVersion standing is attached to the immutable descriptor

**Major — package identity, Registry lifecycle, historical readability, and
source/projection convergence.**

The accepted EDS is explicit that `PackageVersionStanding` belongs to one
registry-release membership, not to the immutable package descriptor. A new
release must be able to retain the same exact `(PackageKey, PackageVersion,
DescriptorDigest)` while changing that release's membership from
`EXECUTABLE_SUPPORTED` to `HISTORICAL_READ_ONLY`. The accepted Registry digest
includes per-release membership standing, whereas the descriptor digest must
continue to identify only the unchanged descriptor.

The final implementation does the opposite:

- `DisciplinePackageDescriptorV1` contains `standing`, so standing is included
  in descriptor canonical bytes and `DescriptorDigest`;
- `DescriptorRegistrationV1` and `RegistryReleaseManifestV1` provide no
  independent release-membership standing;
- Registry assembly computes release standing from `descriptor.standing`;
- compatibility decides historical/executable behavior from
  `descriptor.standing`, not the current `RegistryMembership`;
- projection installation copies the descriptor standing into both the
  immutable descriptor row and the release-membership row;
- parity requires both stored values to equal the descriptor value; and
- M1 physically adds `standing` to
  `discipline_package_descriptors`, even though the accepted EDS locates that
  mutable-by-release fact only on
  `discipline_package_registry_memberships`.

Consequently, moving an unchanged package version from executable in release
R1 to historical-only in release R2 requires changing its descriptor bytes and
digest. The immutable descriptor table is keyed by package/version and the
installer reuses an existing row, so the R2 projection cannot converge to the
new source descriptor; parity fails closed. If the row were changed instead,
R1's immutable historical descriptor/provenance would be rewritten. Either
path violates the accepted lifecycle and historical-identity contract.

The existing R1/R2 test reuses one descriptor with one unchanged standing. It
does not exercise the mandatory executable-to-historical membership transition
and therefore does not detect this defect.

This is not optional hardening. It prevents a core lifecycle operation required
before PATCH-052 packages can be safely retired from execution while remaining
historically interpretable. Correcting the already-installed physical
descriptor schema may also require a new forward migration beyond current M5.
No source, test, schema, migration, or database remediation is authorized by
this review.

**WP051-MAJ-01: OPEN / BLOCKING.**

## Findings and verdict

Critical: **0**

Major: **1** — `WP051-MAJ-01`

Minor: **0**

Observation: **0**

PATCH-051 FRESH WHOLE-PATCH INDEPENDENT FINAL REVIEW:
**FAIL / STOPPED**

PATCH-051 IMPLEMENTATION:
**REVIEW BLOCKED BY FINAL-STATE MAJOR**

PATCH-051:
**OPEN / NOT CLOSED**

QG-11:
**NOT ELIGIBLE WHILE WP051-MAJ-01 IS OPEN**

The minimum next Human decision is whether to authorize a narrowly bounded
Registry-standing design/migration-history reconciliation. If that
reconciliation determines a forward migration is necessary, separate migration
creation and isolated execution authority will also be required. The present
review does not authorize remediation, M6, QG-11, QG-12, PATCH-051 closure, or
PATCH-052.
