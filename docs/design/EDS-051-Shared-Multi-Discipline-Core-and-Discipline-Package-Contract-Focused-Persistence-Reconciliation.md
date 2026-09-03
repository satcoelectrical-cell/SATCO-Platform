# EDS-051 Focused Compatibility-Profile Persistence Reconciliation

## 1. Status and authority

| Field | State |
|---|---|
| PATCH | PATCH-051 — Shared Multi-Discipline Core & Discipline Package Contract |
| Authority | **HUMAN FOCUSED EDS-051 PERSISTENCE RECONCILIATION AUTHORITY: GRANTED** |
| Scope | `IDS051-MAJ-01` parent compatibility-profile persistence cardinality only |
| Verdict | **FOCUSED EDS-051 PERSISTENCE RECONCILIATION: PASS / COMPLETE** |
| Architecture-051 | **NO AMENDMENT REQUIRED** |
| ADR-024 | **NO AMENDMENT REQUIRED** |
| EDS-051 | **ACCEPTED / COMPLETE WITH FOCUSED RECONCILIATION** |

This is an append-only reconciliation of one physical persistence
contradiction discovered by the Independent IDS-051 Review. It does not reopen
the accepted EDS, invalidate Human EDS Acceptance, remediate another IDS
finding, authorize an Implementation Plan, authorize implementation or
migrations, or begin PATCH-052.

## 2. Root cause

The accepted semantic parent row used
`discipline_package_compatibility_profiles` PK
`(profile_id, profile_digest)` while the same row also carried one
`registry_digest`. The Project revision FK expected the release-qualified
triple `(observed_registry_digest, profile_id, profile_digest)`.

For releases R1 and R2 containing unchanged semantic profile P/D:

- inserting R2's profile row collides with R1's global semantic PK;
- reusing R1's row loses explicit R2 membership and cannot satisfy R2's
  release-qualified Project provenance FK; and
- overwriting R1's `registry_digest` destroys immutable historical membership.

The collision is in parent release membership, not in the accepted member PK
`(profile_id, profile_digest, combination_digest, package_key)`.

## 3. Alternatives evaluated

### A. Release-qualified profile projection identity

This shape would make `(registry_digest, profile_id, profile_digest)` the
profile-row PK and propagate `registry_digest` into every member FK/PK. It can
represent R1 and R2, but repeats identical semantic profile JSON and every
combination/member row per release, changes the accepted member key, and
conflates semantic content rows with release-membership rows. It is valid but
not the smallest correction in authority or relational meaning.

### B. Semantic profile plus Registry-release membership

This shape retains one immutable semantic profile and its accepted semantic
member rows, then adds one immutable association row for each Registry release
that contains the profile. It preserves the accepted member key, digest
semantics and normalized content while making release provenance explicit.
This is the chosen correction.

### C. Encoded or synthetic release-specific profile identity

Changing `profile_id` or `profile_digest` merely because a release changed
would make release provenance an artificial semantic input and would produce
false profile changes. It is rejected.

## 4. Reconciled relational model

### 4.1 Semantic profile

`discipline_package_compatibility_profiles` is the immutable semantic profile
projection:

- columns: `profile_id VARCHAR(64)`, `profile_digest CHAR(64)`,
  `profile_json JSONB NOT NULL`, `created_at TIMESTAMPTZ NOT NULL`;
- PK: `(profile_id, profile_digest)`;
- `profile_digest` is recomputed from the complete canonical semantic profile;
- `registry_digest` and all release-qualified unique constraints are removed
  from this table; and
- the row is inserted once and thereafter compared byte-for-byte and
  member-for-member. It is never updated to represent another release.

The semantic identity is `(profile_id, profile_digest)`. The digest remains
content-derived and does not include a Registry release identifier.

### 4.2 Registry-release profile membership

Create the derived immutable table
`discipline_package_registry_profile_memberships`:

- columns: `registry_digest CHAR(64)`, `profile_id VARCHAR(64)`,
  `profile_digest CHAR(64)`, `created_at TIMESTAMPTZ NOT NULL`;
- PK: `(registry_digest, profile_id)`;
- unique provenance key:
  `(registry_digest, profile_id, profile_digest)`;
- FK `registry_digest` to
  `discipline_package_registry_releases(registry_digest)` with
  `ON DELETE RESTRICT`;
- FK `(profile_id, profile_digest)` to
  `discipline_package_compatibility_profiles(profile_id, profile_digest)` with
  `ON DELETE RESTRICT`;
- index `(profile_id, profile_digest, registry_digest)` for historical reverse
  lookup; and
- no update or delete path.

The PK enforces at most one semantic digest for a profile ID in one release.
The unique triple is the exact release-qualified FK target for immutable
Project configuration provenance.

### 4.3 Compatibility members

`discipline_package_compatibility_members` remains semantic profile content:

- PK remains exactly
  `(profile_id, profile_digest, combination_digest, package_key)`;
- FK `(profile_id, profile_digest)` continues to reference the semantic
  profile table;
- the exact descriptor FK, combination/member indexes and digest checks remain
  unchanged; and
- no `registry_digest` is added.

This preserves multiple combinations, the same PackageKey at different exact
versions across different combinations, duplicate PackageKey rejection within
one combination, duplicate semantic-combination rejection and deterministic
combination/profile reconstruction.

### 4.4 Project configuration provenance

`project_package_configuration_revisions` continues to store
`observed_registry_digest`, `profile_id` and `profile_digest`. Its composite FK
`(observed_registry_digest, profile_id, profile_digest)` now references
`discipline_package_registry_profile_memberships(registry_digest, profile_id,
profile_digest)`. Its separate release FK remains valid but is redundant
defense in depth and is retained.

Organization configuration does not reference compatibility profiles and is
unchanged. Workspace provenance continues to resolve through its immutable
Project revision; no Workspace column or FK changes.

## 5. Digest and authority preservation

- `RegistryDigest` remains the digest of the complete release manifest,
  including its profile digests and other accepted release facts.
- `CompatibilityProfileDigest` remains the digest of canonical semantic
  profile content only.
- `CompatibilityCombinationDigest` remains one canonical allowed member set
  inside the semantic profile.
- `DescriptorDigest` remains one complete canonical descriptor.
- `SelectedDescriptorSetDigest` remains the Project's sorted exact descriptor
  selection set.

No digest receives a second meaning. Source-controlled Registry manifests
remain authority. All three profile-related tables are immutable derived
integrity projections. The membership table records provenance; it does not
authorize or define profile content.

## 6. Cross-release installation and drift behavior

For R1 containing P/D, projection installation validates/inserts the semantic
profile P/D and its member rows, then inserts membership `(R1,P,D)`.

For later R2 containing unchanged P/D, installation:

1. locates P/D by the semantic PK;
2. compares canonical `profile_json`, its recomputed digest and the complete
   reconstructed member/combination set;
3. inserts no duplicate semantic profile or member row;
4. inserts immutable membership `(R2,P,D)`; and
5. leaves `(R1,P,D)` and all R1 facts unchanged.

An existing semantic row with different bytes/members is drift/tampering and
stops installation. A missing, extra or wrong membership for a release is
release-projection drift even when the semantic profile exists globally. Drift
comparison therefore evaluates both:

- the release's exact expected set of membership triples; and
- each referenced semantic profile's exact canonical bytes and complete member
  set.

Current-release activation changes only the accepted current-release pointer.
It inserts, updates or deletes no profile membership, semantic profile or
member row.

## 7. Historical resolution proof

A historical Project revision resolves without consulting a newer current
release:

```text
observed RegistryDigest
  -> immutable Registry release row and retained source manifest
  -> exact (RegistryDigest, ProfileId, ProfileDigest) membership
  -> immutable semantic profile (ProfileId, ProfileDigest)
  -> immutable combination/member rows
```

R1 and R2 may both resolve P/D through separate membership rows. Installing or
activating R2 does not rewrite R1. There is no `latest` lookup or fallback to
the current Registry.

## 8. M1 and persistence-manifest reconciliation

Future `e05100000001_registry_configuration_audit` creates **twelve**, not
eleven, PATCH-051 tables. Registry projection tables become:

1. `discipline_package_registry_releases`;
2. `discipline_package_descriptors`;
3. `discipline_package_registry_memberships`;
4. `discipline_package_compatibility_profiles`;
5. `discipline_package_registry_profile_memberships`; and
6. `discipline_package_compatibility_members`.

The six accepted Organization/Project/Audit tables follow unchanged. M1 creates
the semantic profile before its release membership and members, and creates
the release membership before Project revisions that reference it. Its
immutability triggers, grants and projection reconciliation include the new
membership table. M1 postconditions require all twelve tables empty before the
separate projection installation step.

M2 and M3 have no direct profile FK and remain unchanged. No migration file is
created or executed by this reconciliation.

The later IDS-051 persistence map, M1 design, model/table counts, Registry
repository/service behavior, historical resolver, Project revision FK,
projection tests, migration tests and future manifests must adopt this exact
shape. No public request or response field changes: existing APIs already carry
RegistryDigest plus semantic profile ID/digest where provenance requires it.

## 9. Validation obligations

Focused IDS remediation and later tests must prove:

- R1/P/D followed by R2/P/D succeeds without semantic row duplication;
- both immutable membership rows exist and independently resolve;
- R2 installation never updates R1 membership or semantic profile/member rows;
- changed bytes under the same semantic digest fail as drift;
- missing/extra/wrong release membership fails exact projection comparison;
- Project revisions accept only a profile membership in their observed release;
- multiple combinations and cross-combination PackageVersion variation remain
  collision-free; and
- historical resolution does not read the current-release pointer.

## 10. Finding and governance disposition

`IDS051-MAJ-01`: **EDS ROOT CAUSE RESOLVED / READY FOR IDS REMEDIATION
RECONCILIATION**.

`IDS051-MAJ-02` and `IDS051-MAJ-03` remain **OPEN / BLOCKING** at IDS level.
`IDS051-MIN-01` and `IDS051-OBS-01` remain open and unchanged. This operation
creates no new Critical or Major finding and requires no further EDS amendment.

Human EDS Acceptance, the initial EDS review failure, prior focused
remediation/re-review and all accepted historical evidence remain intact.
EDS-051 remains **ACCEPTED / COMPLETE WITH FOCUSED RECONCILIATION**.

The exact next resume point is separately authorized focused IDS-051
remediation for `IDS051-MAJ-01`, `IDS051-MAJ-02` and `IDS051-MAJ-03`, plus the
non-blocking IDS findings as appropriate. This reconciliation grants no such
authority by itself.
