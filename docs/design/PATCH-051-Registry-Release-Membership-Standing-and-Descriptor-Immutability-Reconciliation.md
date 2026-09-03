# PATCH-051 Registry Release-Membership Standing and Descriptor Immutability Reconciliation

## Status and authority

| Field | Value |
|---|---|
| Scope | `WP051-MAJ-01` Registry-standing ownership and migration-history reconciliation only |
| Human authority | **HUMAN PATCH-051 WP051-MAJ-01 REGISTRY-STANDING DESIGN AND MIGRATION-HISTORY RECONCILIATION AUTHORITY: GRANTED** |
| Result | **PASS / ACCEPTED / COMPLETE** |
| Production implementation authority | NOT GRANTED |
| Migration creation/execution authority | NOT GRANTED |
| Current source Alembic head | `e05100000005` |
| Proposed correction | `e05100000006`, eligible only for separate Human authority |
| `WP051-MAJ-01` | OPEN; remediation path resolved only |
| PATCH-051 | OPEN / NOT CLOSED |
| QG-11 | NOT YET ELIGIBLE |

This append-only record preserves PATCH-051 registration, Architecture-051
and its acceptance, ADR-024, EDS-051 and its focused persistence
reconciliation, IDS-051, Implementation-Plan-051, Batch-1 through Batch-5
evidence and reviews, M1 through M5, and the Fresh Whole-PATCH Independent
Final Review. It creates or executes no migration, changes no production
implementation, accepts no remediation, and introduces no PATCH-052 scope.

## Independent derivation of accepted ownership

The authoritative artifacts are consistent and unambiguous. EDS-051 states
that standing belongs to a Registry-release membership, not the immutable
descriptor. Architecture-051 and ADR-024 require stable package-version
identity and retained historical interpretation. IDS-051 requires retained
source manifests and projected memberships, including their standings, to be
reconciled by exact Registry digest. The accepted closed values are:

- `EXECUTABLE_SUPPORTED`: the package version is a member of the current
  trusted release, has its static adapter, is Core-compatible, and may be
  newly selected or executed only after all other authorization predicates;
- `HISTORICAL_READ_ONLY`: that release membership remains available for
  authorized historical interpretation but is ineligible for new selection,
  reconfiguration, Workspace creation, package mutation, or execution.

The accepted owner is therefore the existing relation
`Registry release -> immutable PackageVersion descriptor`, represented in
source by one release registration and in the projection by
`discipline_package_registry_memberships`. No additional lifecycle subsystem
is required.

## Immutable descriptor boundary

An immutable `DisciplinePackageDescriptorV1` contains intrinsic package
content only: schema version, PackageKey, PackageVersion, primary Discipline,
supported Core-contract versions, display name, description, entitlement key,
static adapter identity, dependencies, conflicts, and declared
contributions. It does not contain release standing.

The descriptor identity is the typed SHA-256 digest of the complete canonical
intrinsic descriptor. For unchanged descriptor `P@1.0.0`:

```text
R1 membership: P@1.0.0 -> EXECUTABLE_SUPPORTED
R2 membership: P@1.0.0 -> HISTORICAL_READ_ONLY

descriptor bytes R1 == descriptor bytes R2
DescriptorDigest R1 == DescriptorDigest R2
RegistryDigest R1 != RegistryDigest R2
```

The standing transition is expressed only by assembling a new immutable
Registry release. Neither the prior release nor the descriptor is mutated.

## Source authority and projection

`DescriptorRegistrationV1` is the already-accepted source release-membership
structure. The minimum correction is to give each registration its closed
`standing` value while removing `standing` from
`DisciplinePackageDescriptorV1`. The explicit release modules remain the
sole source of Registry authority; static adapters remain source controlled;
no discovery, database-authored package, URL, executable expression, or
runtime plugin mechanism is introduced.

`TrustedDisciplinePackageRegistryV1` must retain an immutable standing map
keyed by exact `(package_key, package_version)` for that release. The database
continues to be a derived, append-only projection:

- `discipline_package_descriptors` stores intrinsic descriptor content and
  identity, without `standing`;
- `discipline_package_registry_memberships` stores `registry_digest`, exact
  package identity, and closed `standing`;
- current-release selection remains the only mutable Registry pointer.

The authoritative PATCH-051 Core release is explicitly empty. Its expected
Registry digest is therefore unaffected by moving the field between source
contract owners.

## Digest semantics

| Identity | Standing-only transition between releases |
|---|---|
| `DescriptorDigest` | MUST NOT change; standing is not intrinsic descriptor input |
| `RegistryDigest` | MUST change for a non-empty release because per-membership standing is canonical release state |
| `SelectedDescriptorSetDigest` | MUST NOT change for the same exact package/version/descriptor members |
| `CompatibilityProfileDigest` | MUST NOT change; it identifies canonical profile content and allowed exact combinations |
| `CompatibilityCombinationDigest` | MUST NOT change; it identifies the exact sorted descriptor member set |
| compatibility identity | Exact descriptor/profile/combination identities remain unchanged; eligibility result may change because the current release membership is historical-only |

A standing change is therefore a Registry-release state change, not a
descriptor, Project selection, profile, or combination identity change.

## Current implementation and M1 defects

The Whole-PATCH finding is independently confirmed:

1. `DisciplinePackageDescriptorV1` carries `standing`, while
   `DescriptorRegistrationV1` has no independent membership standing.
2. Descriptor canonicalization consequently includes standing and changes
   `DescriptorDigest` when lifecycle state changes.
3. Registry assembly, executable resource counting, compatibility, API
   filtering, and effective Workspace serialization read descriptor standing.
4. The installer copies descriptor standing into both the descriptor row and
   membership row; readiness/parity requires both copies to equal the source
   descriptor.
5. M1 added `standing` to both tables. The descriptor copy violates accepted
   ownership. The membership column, its closed check, FK identity, and
   immutability trigger are the correct accepted persistence location.
6. M1 omitted the accepted membership lookup index
   `(registry_digest, standing, package_key, package_version)`.

M1 through M5 are immutable historical records. Their current source hashes
and the linear graph ending at `e05100000005` were inspected during this
reconciliation. None may be rewritten to conceal the defect.

## Historical truth and isolated-state finding

Existing standing is not missing or inferential. Read-only inspection of the
authorized isolated database `satco_platform_patch02022_test` at
`e05100000005` found 145 release rows, 145 descriptor rows and 145 membership
rows. Every descriptor copy matched its membership standing, and every
membership matched the standing retained in its release manifest. There were
no current releases and no active non-idle sessions after inspection.
Standing is therefore truthfully recoverable from the accepted membership
rows and independently corroborated by durable release manifests; no default
or fabricated standing is permitted.

Those 145 `maj04-*` releases and 33 Project revisions are committed test
fixture residue, not retained authoritative source releases. They were made
under the defective descriptor-hash contract. Rehashing or rewriting them
would change historical descriptor, profile, combination, selected-set,
Registry, and Project provenance. A corrective migration must not do that.
The isolated database remains safe for read-only diagnosis, but it is not a
valid in-place M6 test target. Under separate test authority it must be
recreated at the intended starting revision before M6 execution; this
reconciliation performs no cleanup.

For a governed deployment, M6 must verify that the retained source catalog and
projection are the authoritative empty PATCH-051 release and that descriptor,
membership, profile/member, Organization selection, Project revision/
selection/head, Workspace package binding, and package Audit reference state
cannot require provenance rewrite. Any non-empty legacy state is a hard
abort/rollback and Human escalation, not an automatic backfill. This is a
safety precondition, not fabrication of an empty history.

## One-forward-migration decision

Exactly one bounded forward migration is feasible for the known governed
PATCH-051 state:

```text
revision:      e05100000006
down_revision: e05100000005
purpose:       restore release-membership standing ownership and intrinsic
               descriptor persistence
```

An authorized M6 upgrade may do only the following:

1. verify the exact source/DB preconditions above and fail transactionally on
   any non-empty or unrecognized legacy provenance;
2. verify that `discipline_package_registry_memberships.standing` exists,
   remains `NOT NULL`, has exactly the two accepted values, and remains under
   the existing immutable-membership trigger;
3. create the accepted index
   `(registry_digest, standing, package_key, package_version)` with one stable
   governed name;
4. drop only `discipline_package_descriptors.standing`; and
5. preserve every other table, row, digest, FK, trigger, function, grant,
   current pointer, configuration, Workspace binding, and Audit value.

No data backfill is needed in the accepted empty governed state. In any
non-empty state, truth exists in membership rows/manifests but intrinsic
descriptor digests cannot be corrected without rewriting immutable
provenance; M6 must therefore stop rather than backfill or rehash.

Downgrade may restore the exact M5 descriptor column and remove only the new
membership index when no post-M6 descriptor or membership data exists. If
post-M6 data exists, downgrade must fail closed because collapsing distinct
release membership standings into one descriptor value is not truthful.
Operational recovery after use remains forward-only unless that empty-state
precondition is proven.

A fresh M1-to-M6 install and an M5-to-M6 upgrade from the authoritative empty
state converge on the same final schema and unchanged empty Registry digest.
The current residue-bearing isolated database deliberately does not satisfy
upgrade preconditions and cannot be cited as convergence proof until it is
recreated under separate authority.

## Required bounded runtime remediation

If separately authorized, production remediation is limited to:

- remove `standing` from the descriptor contract and canonical descriptor
  bytes; add it to `DescriptorRegistrationV1`;
- assemble Registry payload/digest and executable-count bounds from
  registration standing; retain an immutable per-release standing map;
- persist membership standing from the registration, never the descriptor;
- reconcile source registrations to membership rows and release manifests,
  and remove descriptor-standing parity;
- make compatibility and current selection consult exact current-release
  membership standing;
- make historical/effective Workspace resolution consult the membership of
  the recorded `observed_registry_digest`, while current mutation eligibility
  consults the current release membership;
- filter and serialize supported packages and applicability from membership
  standing; and
- update focused unit, projection, readiness, API, migration, security, and
  cross-release conformance tests.

Readiness must recompute the exact source Registry release, compare the source
registration standing map with the DB membership map, verify descriptor bytes
and digests independently of standing, and fail closed on missing, extra, or
mismatched members. Runtime remains SELECT-only over Registry projection;
only the guarded installer may insert projection rows or change the current
pointer.

Frontend DTO fields and rendering semantics do not require redesign. They
continue to receive standing, but the backend must serialize it from the
appropriate Registry membership. Project exact pins, selected-set digests,
profile/combination identities, Organization configuration, Workspace binding
identity, and historical readability do not change.

## Security, authority, and downstream boundary

Standing is lifecycle eligibility only. It grants no tenant access,
engineering-data disclosure, entitlement, role, or Human authority.
Authorization-before-disclosure, active Organization isolation, installer
separation, runtime write restrictions, and entitlement checks remain
unchanged and independently required.

Architecture-051 and ADR-024 require no amendment: this correction restores
their already-accepted immutable identity and release lifecycle. EDS-051 and
IDS-051 require no semantic amendment or redesign; this append-only record is
the implementation/migration-history reconciliation that records how their
existing contract is restored. PATCH-052 operational package work remains
prohibited.

## Governance outcome

Accepted ownership is unambiguous, historical standing is present and
corroborated, immutable descriptor semantics can be restored without changing
governed data, and exactly one fail-closed forward correction is sufficient
for the authoritative empty PATCH-051 state. The current disposable fixture
database must be recreated before future migration proof; this is an
operational observation, not an unresolved design Major.

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
