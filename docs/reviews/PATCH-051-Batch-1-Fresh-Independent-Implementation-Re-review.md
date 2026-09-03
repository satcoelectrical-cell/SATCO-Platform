# PATCH-051 Batch 1 — Fresh Independent Implementation Re-review

## Control and verdict

| Field | Result |
|---|---|
| PATCH | PATCH-051 — Shared Multi-Discipline Core & Discipline Package Contract |
| Human re-review authority | **HUMAN PATCH-051 BATCH-1 FRESH INDEPENDENT RE-REVIEW AUTHORITY: GRANTED** |
| Historical independent review | **FAIL / STOPPED** with `B1-051-MAJ-01` through `B1-051-MAJ-04` open at that time |
| Focused remediation state | COMPLETE / READY FOR FRESH INDEPENDENT RE-REVIEW |
| Fresh verdict | **FAIL / STOPPED** |
| Critical / Major / Minor / Observation | **0 / 3 / 0 / 1** |
| Batch 1 state | **IMPLEMENTED / NOT ACCEPTED / REMEDIATION REQUIRED** |
| Batch 2 | not eligible for implementation authority; not authorized |
| Migration creation / execution | not authorized / not authorized |

This is an independent inspection of the current production Core and its
tests. It does not rely on the remediation evidence as proof and does not
modify production code, tests, migrations, or the historical review.

## Finding register

### B1-051-MAJ-01 — RESOLVED / CLOSED

`contracts.py` canonicalizes all reviewed semantic sets at admission:
dependencies, conflicts, Core versions, manifest descriptors/profiles,
profile combinations/member lists/interface IDs, and each contribution section
and frontend-key collection. Duplicate identities reject. `registry.py` and
`compatibility.py` traverse dependency edges in `(package_key,
package_version)` order. The sort keys include the full accepted identities
(the selected-member key also includes `descriptor_digest`).

Independent executable probes established equal relevant digests for reversed
dependencies, conflicts, taxonomy contribution members, descriptor
registrations, profile members, and combination members. A semantic dependency
change changed the descriptor digest. NFC strings serialize stably; non-NFC
input is rejected by the strict NFC canonical boundary, consistent with the
IDS prohibition on permissive normalization. No accepted ordered semantic
array was found in this Batch-1 Core; `ordinal` is declaration metadata and
does not make contribution collection order semantic.

### B1-051-MAJ-02 — OPEN / BLOCKING

The Pydantic input contracts correctly reject raw strings and wrong digest
domains for `ExactPackageSelectionV1.descriptor_digest` and
`RegistryReleaseManifestV1.expected_registry_digest`, and their serializers
emit only the canonical hexadecimal value. Registry assembly and evaluator
returns also produce correctly typed values.

However, `CompatibilityEvaluationV1` is a frozen standard dataclass, not a
validating contract. Its public constructor accepts `DescriptorDigest` in its
`registry_digest` and `profile_digest` fields, `CombinationDigest` in its
`selected_descriptor_set_digest` field, and raw `str` in all three fields.
Python annotations alone do not enforce the accepted non-interchangeable
digest domains.

| Field | Detail |
|---|---|
| Affected files | `backend/app/discipline_packages/compatibility.py` |
| Exact behavior | `CompatibilityEvaluationV1(COMPATIBLE, selections, DescriptorDigest(...), CombinationDigest(...), DescriptorDigest(...), ())` constructs successfully; the same construction with raw strings also succeeds. |
| Accepted requirement | EDS-051 §§3–4 and 13; IDS-051 §7 require distinct digest wrappers at all internal/public provenance boundaries and reject cross-domain substitution. |
| Why it matters | A caller can construct a valid-looking compatibility result carrying semantically wrong or loose provenance; this defeats the required boundary guarantee. |
| Minimum remediation | Make the evaluation result a strict validating/frozen contract, or add exact constructor validation for Registry, SelectedDescriptorSet and Profile digest domains and raw strings; add direct result-boundary negative vectors. |

### B1-051-MAJ-03 — OPEN / BLOCKING

The generic contribution payload has been replaced by frozen, closed,
section-specific models for all 17 accepted declaration spaces. Required
fields, unknown fields, ID patterns, executable/import payload rejection,
collection cardinality, immutable models, section sorting and resource-count
matching are present. No arbitrary nested JSON or executable authority field
is accepted.

One accepted field constraint remains absent: `ContributionDeclarationV1`
enforces only `ordinal >= 1`, while EDS-051 §17 requires every ordinal to be
within its section limit. For example,
`TaxonomyFamilyDeclarationV1(..., ordinal=33)` is accepted despite the
taxonomy section limit of 32. This is a direct closed-contract/resource-bound
violation, not a style observation.

| Field | Detail |
|---|---|
| Affected files | `backend/app/discipline_packages/contributions.py` |
| Exact behavior | An out-of-range ordinal is admitted and can enter descriptor provenance. |
| Accepted requirement | EDS-051 §17: each contributed item has ordinal `1..section limit`; IDS-051 requires bounded strict contribution schemas. |
| Why it matters | A trusted-source declaration can violate an explicitly accepted per-section bound while passing schema admission. |
| Minimum remediation | Enforce the appropriate maximum ordinal for every section (or remove ordinal where the accepted schema does not use it) and add boundary tests. |

### B1-051-MAJ-04 — OPEN / BLOCKING

The evaluator now covers core version, dependency traversal, conflicts,
profile combination matching, collisions, migration declarations and aggregate
resource totals, and returns sorted closed reasons for the exercised paths.
It still fails the accepted Organization-enable and invalid-registry safe
boundaries.

| Field | Detail |
|---|---|
| Affected files | `backend/app/discipline_packages/compatibility.py`; `backend/app/exceptions/discipline_package.py` |
| Exact behavior | When a selected package is absent from `enabled_package_keys`, evaluation raises `AttributeError: type object 'DisciplinePackageReasonCode' has no attribute 'ORGANIZATION_DISABLED'`; the required enum member is missing. A tampered `TrustedDisciplinePackageRegistryV1` with `descriptor_digests=object()` passes the initial class check then raises `AttributeError: 'object' object has no attribute 'values'`, rather than returning `UNAVAILABLE` / `REGISTRY_UNAVAILABLE`. |
| Accepted requirement | EDS-051 §13 and IDS-051 §7 require fixed Organization-enable evaluation with the closed `ORGANIZATION_DISABLED` code and safe `UNAVAILABLE` for invalid Registry state, without raw exception text. |
| Why it matters | A normal rejection path is uncontrolled, and a malformed trusted Registry leaks a programmer exception instead of the defined fail-closed decision. |
| Minimum remediation | Add the closed reason code; validate Registry structural invariants defensively before evaluation and return only the accepted unavailable result for invalid state; add direct probes for disabled packages and structurally malformed registry instances. |

## Independent verification

| Area | Result |
|---|---|
| Dependency/conflict/contribution reversal | PASS: equal DescriptorDigest after reversal; changed semantic input changes digest |
| Registry/profile/combination ordering | PASS: reversed registrations, profile members and combination members produce equal relevant digest |
| Unicode canonicalization | PASS: NFC representation is stable; non-NFC input rejects at strict canonical boundary |
| Typed input digest boundaries | PASS: Registry-to-Descriptor, raw string and other wrong-domain inputs reject in Pydantic contracts; canonical serialization is stable hex only |
| Compatibility-result digest boundary | FAIL: raw/cross-domain values construct in `CompatibilityEvaluationV1` |
| Contributions | PARTIAL / FAIL: closed section-specific shapes and collection bounds are present, but ordinal upper bounds are absent |
| Compatibility order / reasons | PARTIAL / FAIL: implementation order is 1–10, but Organization-enable raises due to a missing closed reason code; malformed typed Registry is not safely unavailable |
| Taxonomy collision | PASS in exercised malformed-registry probe: deterministic `TAXONOMY_COLLISION` |
| Migration requirement | PASS: unsatisfied matching guard yields `MIGRATION_INCOMPATIBLE`; satisfied matching guard does not fail the rule; no migration executes |
| Resource budget | PASS in exercised probe: deterministic aggregate counter overrun yields `RESOURCE_LIMIT_EXCEEDED` |
| Graph determinism | PASS by inspection/probe: sorted traversal, cycle/missing-node/depth/visit handling; no unbounded recursion |
| Static adapter security | PASS: explicit source table; no entry-point, importlib, filesystem, network, eval or exec loading |
| Legacy translation / entitlement / standards / interface seams | PASS: exact legacy mapping; `NOT_REQUIRED` only; declaration-only seams |
| Batch boundary | PASS: no persistence, DB projection, configuration, Workspace binding, API, frontend, installer, standards/cross-discipline intelligence, commercial enforcement, or operational Electrical/Instrumentation/Control package |
| Migration / Alembic head | PASS: no PATCH-051 revision found; `e04700000001 (head)` |

## Test and regression evidence

| Validation | Result |
|---|---|
| Focused test command | `docker exec satco-backend python -m pytest --noconftest -q tests/test_discipline_package_contracts.py tests/test_discipline_package_registry.py tests/test_discipline_package_compatibility.py tests/test_discipline_package_conformance.py tests/test_discipline_package_remediation.py` |
| Focused result | **20 passed in 1.42s** |
| Test-quality verdict | PARTIAL: production behavior is exercised, but the suite misses the three blocking paths above and therefore is not acceptance proof |
| Targeted regression | `compileall` passed; Core/enum imports reported `imports-ok` |
| Standard pytest | blocked before collection: `RuntimeError: PATCH-020.2.2 tests require TEST_DATABASE_URL to target satco_platform_patch02022_test` |
| PostgreSQL observation | `B1-051-OBS-01` remains **OPEN / NON-BLOCKING / ENVIRONMENT** |
| Attribution | unrelated test-environment configuration; no Batch-1 database credential, persistence, or migration change was found |

## Conformance and governance

Architecture-051, ADR-024, EDS-051, IDS-051 and Implementation Plan-051
remain accepted and internally consistent. No upstream reconciliation is
required; the remaining deviations are implementation defects. `IDS051-OBS-01`
remains open as a downstream implementation/deployment obligation.

| Governance item | State |
|---|---|
| New Critical / Major / Minor / Observation | 0 / 0 / 0 / 0; the three blocking items retain their historical IDs |
| Blocking findings | `B1-051-MAJ-02`, `B1-051-MAJ-03`, `B1-051-MAJ-04` |
| Non-blocking findings | `B1-051-OBS-01` only |
| Required further remediation | the minimum remediations stated in the three finding records only |
| Batch-1 final review / acceptance | **FAIL / STOPPED** / **NOT ACCEPTED** |
| Batch-2 eligibility / authority | not eligible / not authorized |
| PATCH-051 | REGISTERED / OPEN |
| PATCH-052 | NOT STARTED / NOT AUTHORIZED |
| Commercial V1 roadmap | unchanged |
| Exact next resume point | separately Human-authorized focused Batch-1 remediation of `B1-051-MAJ-02` through `B1-051-MAJ-04`, then a fresh independent re-review |
| Recommended next governed action | obtain focused remediation authority only; do not begin Batch 2, PATCH-052, or migration work |

## Repository hygiene

This review creates only this artifact. No production, test, migration, or
historical review file was modified. `git diff --check` passed; staged files:
**0**. The repository contained unrelated pre-existing local modifications,
which were preserved.
