# PATCH-051 Batch 1 — Independent Implementation Review

## Control and verdict

| Field | Result |
|---|---|
| PATCH | PATCH-051 — Shared Multi-Discipline Core & Discipline Package Contract |
| Authority | **HUMAN PATCH-051 BATCH-1 INDEPENDENT REVIEW AUTHORITY: GRANTED** |
| Baseline reviewed | Architecture-051 accepted; ADR-024 accepted; EDS-051 and IDS-051 accepted; Implementation Plan-051 accepted; focused IRR accepted |
| Reviewed implementation state | Batch 1 implemented / ready for independent review |
| Verdict | **FAIL / STOPPED** |
| Critical / Major / Minor / Observation | **0 / 4 / 0 / 1** |
| Batch 1 state after this review | **IMPLEMENTED / NOT ACCEPTED / REMEDIATION REQUIRED** |
| Batch 2 | not eligible for authority while the Major findings remain open; not authorized |
| Migrations | none created or executed; creation and execution remain unauthorized |

The review independently inspected the actual Batch-1 source, four focused
test modules, implementation evidence and accepted design records.  It does
not change production code, tests, migration history, acceptance state or
future Batch authority.

The pure-Core boundary is well contained and much of the foundation is sound:
the intentional empty release assembles deterministically, static adapter
registration has no plugin loading path, the focused tests pass, and no
persistence/API/frontend/operational-package behavior was pulled forward.
Batch 1 nevertheless cannot be accepted because its canonical provenance,
digest-field typing, contribution contract, and compatibility implementation
do not meet the accepted Core contract.

## Manifest and boundary reality

The inspected Batch-1 implementation matches the authorized physical manifest:

* 16 new production files: the nine `discipline_packages` Core modules; two
  descriptor/release table modules; one release module; the enum, port,
  adapter and exception modules.
* `backend/app/enums/__init__.py` is the one Batch-1 production modification.
* Four new focused test modules are present.
* No PATCH-051 migration, model, repository/UoW, projection, configuration,
  Workspace binding, API router, frontend artifact, operational E/I/C package,
  standards intelligence, cross-discipline engine or commercial entitlement
  behavior was found.

The empty `release_051_core_v1` source manifest is intentional and its
assembled digest is deterministic.  The source Registry is in explicit Python
release tables, is independent of the database, uses frozen data/mapping
proxies after assembly, and has no dynamic import, entry-point, filesystem,
network, `eval`, or `exec` loading path.  The entitlement seam returns only
`NOT_REQUIRED`; standards, interface and frontend structures are declarative
only; and legacy translation is exact/source-qualified.

## Independent validation

| Validation | Command / outcome |
|---|---|
| Focused Batch-1 tests | `docker exec satco-backend python -m pytest --noconftest -q tests/test_discipline_package_contracts.py tests/test_discipline_package_registry.py tests/test_discipline_package_compatibility.py tests/test_discipline_package_conformance.py` — **13 passed in 1.21s** |
| Compile validation | `docker exec satco-backend python -m compileall -q app/discipline_packages app/adapters/discipline_package_registry.py app/ports/discipline_package.py app/enums/discipline_package.py app/exceptions/discipline_package.py` — **passed** |
| Import / enum-Core regression check | `docker exec satco-backend python -c 'import app.enums; import app.discipline_packages; import app.discipline_packages.registry; import app.discipline_packages.compatibility; print("imports-ok")'` — **imports-ok**. The existing Workspace regression suite needs the global database fixture and was not collectible for the reason below. |
| Alembic | `docker exec satco-backend alembic heads` — **`e04700000001 (head)`** |
| Standard focused pytest path | With the repository test URL, pytest failed while importing `tests/conftest.py`, before collection, with PostgreSQL `FATAL: password authentication failed for user "satco"`. |
| Diff / index | `git diff --check` — **passed**; staged files — **0**. |

The PostgreSQL failure is reproducible and occurs in the global fixture's
`bootstrap_engine.begin()` path before any Batch-1 test or implementation
module is collected.  The reviewed Batch-1 surface is database-independent,
and no database credentials, database code or migration was changed in its
manifest.  It is therefore not attributed to this Batch-1 implementation and
does not fabricate a full-suite PASS.  The database-independent focused suite
provides reliable evidence for the code it actually exercises.

## Review matrix

| Area | Result | Independent assessment |
|---|---|---|
| Discipline model | PASS | `DisciplineId`, `PackageKey` and package version are distinct frozen types.  The six selectable disciplines are explicit; `shared_engineering` is Core-only and descriptors reject it as a primary Workspace discipline.  A Discipline does not create an operational package. |
| Package/version identity | PASS | Strict SemVer accepts MAJOR.MINOR.PATCH and bounded prerelease syntax, rejects malformed/negative/leading-zero/build metadata values, and has stable value equality/hash behavior.  There is no latest/upgrade behavior. |
| Digest type separation | FAIL | See `B1-051-MAJ-02`. Wrapper classes exist but contract-facing fields reduce them to `str`. |
| Canonicalization and descriptor digest | FAIL | See `B1-051-MAJ-01`. Object keys/UTF-8/NFC/floats are handled, but accepted unordered descriptor/contribution collections are neither rejected nor canonicalized. |
| Registry digest and source authority | FAIL | Empty release and registration ordering are deterministic, but Registry provenance inherits the descriptor canonicalization defect in `B1-051-MAJ-01`. |
| Selected-set digest | PARTIAL / FAIL | The selected-set helper sorts members correctly and is distinct from Registry digest; its contract/evaluation provenance is nevertheless loose string data (`B1-051-MAJ-02`). |
| Profile/combination digest | PARTIAL / FAIL | Combination members are canonicalized and profile digest is Registry-independent, preserving R1/R2 semantic reuse.  Typed provenance is lost at contract/evaluation boundaries and profile-declared set fields are not fully canonicalized (`B1-051-MAJ-01`, `B1-051-MAJ-02`). |
| Static adapter security | PASS | Explicit static table only; no dynamic discovery or executable descriptor content. |
| Contribution contract | FAIL | See `B1-051-MAJ-03`. Generic declarations do not represent the accepted closed per-section semantics. |
| Immutability | PASS | Pydantic models are frozen and Registry maps are `MappingProxyType`; no mutable default or mutable global Registry was found. |
| Compatibility / reason codes | FAIL | See `B1-051-MAJ-04`. Enums are closed/safe, but evaluator behavior is incomplete and malformed registry input raises rather than producing the accepted unavailable outcome. |
| Dependency graph | PARTIAL / FAIL | Assembly detects missing nodes/cycles and applies bounds, but edge traversal is source-order dependent rather than the accepted key/version order. This is encompassed by `B1-051-MAJ-01`/`B1-051-MAJ-04`. |
| Resource bounds | PARTIAL / FAIL | Declared maxima and byte caps are mostly present and overflow rejects. Required aggregate counters and contribution collision namespaces cannot be correctly evaluated with the incomplete contribution model. |
| Legacy translation | PASS | Exact accepted mappings for `control`, `industrial_automation`, `automation`, and `automation_and_control`; unknown/case/whitespace variants remain unresolved. |
| Entitlement / standards / cross-discipline / frontend seams | PASS | Closed declarations only, `NOT_REQUIRED` entitlement behavior only, and no downstream execution/reasoning/frontend implementation. |
| Human authority and Batch firewall | PASS | No approval/procurement/BOM/aggregate-mutation authority, Batch-2 persistence, PATCH-052, API, or operational content was introduced. |
| Code quality | FAIL | The four Major contract defects are material. No separate stylistic finding is recorded. |

## Findings

### B1-051-MAJ-01 — Descriptor and contribution provenance is order-sensitive where the accepted contract defines sets

| Field | Detail |
|---|---|
| Severity | Major |
| Affected files | `backend/app/discipline_packages/canonical.py`; `contracts.py`; `contributions.py`; `registry.py` |
| Exact behavior | `_normalise()` preserves every list/tuple order. `descriptor_digest()` hashes a descriptor directly. Dependencies, conflicts, contribution collections and profile interface IDs accept unsorted tuple representations; only selected-combination members receive a special sort. An independent probe created otherwise identical descriptors with reversed dependency order and produced `61266e…afd4b` versus `c47551…92c92`, so semantic-equivalent source order changes `DescriptorDigest` and consequently Registry provenance. |
| Accepted requirement | IDS-051 requires canonicalization to reject unordered set representations and serialize documented array identities; EDS-051 §17 requires declaration collections to be duplicate-free and sorted. EDS-051 §13 requires key/version-sorted dependency traversal. |
| Why it matters | Source-file order can silently produce different canonical bytes and trusted provenance for the same dependency/contribution semantics. This defeats deterministic release/review identity, allows inconsistent source representations, and makes error/traversal ordering process/source dependent. |
| Minimum remediation | Define the documented identity and order for every unordered descriptor, contribution and profile collection; enforce sorted/unique representation at schema admission (or canonicalize exactly once before hashing and assembly); sort dependency traversal by `(package_key, package_version)`; add ordering-permutation and rejection vectors. |

### B1-051-MAJ-02 — Digest wrapper types are bypassed by `str` provenance fields

| Field | Detail |
|---|---|
| Severity | Major |
| Affected files | `backend/app/discipline_packages/contracts.py`; `compatibility.py` |
| Exact behavior | `ExactPackageSelectionV1.descriptor_digest`, `RegistryReleaseManifestV1.expected_registry_digest`, and all `CompatibilityEvaluationV1` digest values are `str`/`str | None`, not their respective digest wrappers. An independent probe supplied `str(RegistryDigest("a" * 64))` as both descriptor and Registry expected digest; both models accepted it and retained `str` values. |
| Accepted requirement | IDS-051 defines distinct immutable wrapper types and explicit serializers; EDS-051 §12 reserves Registry, Descriptor, SelectedDescriptorSet and Profile digest roles and forbids using a different digest as a substitute. Batch-1 Plan §4 requires non-interchangeable provenance types. |
| Why it matters | A correct-looking SHA-256 from a semantically different provenance domain crosses selection, manifest and evaluation boundaries without a type-level barrier. The unit test proves wrapper instances compare unequal but does not exercise these actual contract fields. |
| Minimum remediation | Use the exact typed digest wrapper in every in-memory contract/evaluation field, preserve explicit external serialization only at transport/storage seams, validate field/domain ownership, and add substitution-negative tests for every provenance pair. |

### B1-051-MAJ-03 — Contribution schemas do not implement the accepted closed per-section declarations

| Field | Detail |
|---|---|
| Severity | Major |
| Affected files | `backend/app/discipline_packages/contributions.py` |
| Exact behavior | Nearly every contribution section is `tuple[DeclarationV1, ...]`, whose only common content is ID, ordinal, display name and description. It lacks the accepted typed fields for taxonomy ownership/namespace, object family/lifecycle/context/authority, relationship source/target/cardinality, Context/input/deliverable/Evidence requirements, rule-hook schemas/bounds, role/authorization composition, migration from/to/direction/guard/reversibility and conformance vector data. Generic declaration uniqueness does not make the absent semantics closed. |
| Accepted requirement | EDS-051 §17 gives closed minimum fields for each section and explicit collision namespaces; IDS-051 assigns this file bounded schemas for every listed contribution domain; Plan §4 requires strict rejection of unsupported taxonomy/migration/resource declarations and collision vectors. |
| Why it matters | Future descriptors cannot state or validate the accepted semantics, so Registry admission and compatibility cannot enforce collision, migration, resource or conformance obligations. This is a missing Batch-1 contract, not optional hardening. |
| Minimum remediation | Replace generic declarations with strict frozen section-specific schemas carrying the accepted minimum fields and typed identities; enforce duplicate-free sorted collections and collision namespaces; update resource/collision validation and focused negative/boundary vectors. |

### B1-051-MAJ-04 — Compatibility evaluation omits required closed checks and does not return `UNAVAILABLE` for invalid registry state

| Field | Detail |
|---|---|
| Severity | Major |
| Affected files | `backend/app/discipline_packages/compatibility.py`; `registry.py` |
| Exact behavior | The evaluator checks basic selection lookup, standing, Core membership, enablement, direct dependency/conflict, a Boolean `migration_ready`, object-type-only budget and profile membership. It does not evaluate taxonomy/contribution collisions, `MIGRATION_INCOMPATIBLE`, the accepted migration facts/existing selection, all aggregate resource counters, profile Core-version compatibility, required interface declarations, or ordered bounded dependency traversal. Passing an invalid registry object raises `AttributeError: 'object' object has no attribute 'digest'` instead of returning `UNAVAILABLE` with a closed safe code. |
| Accepted requirement | EDS-051 §13 fixes the evaluation order and requires taxonomy/contribution collision, migration compatibility, aggregate resource budgets, all four provenance digests, closed reasons, and `UNAVAILABLE` for invalid registry state. IDS-051 requires a pure ordered closed evaluator. |
| Why it matters | A prospective configuration can be accepted without required source compatibility checks, while unavailable trusted state produces an uncontrolled exception rather than the defined safe decision. This violates a core Batch-1 correctness boundary. |
| Minimum remediation | Model the accepted bounded input facts and contribution semantics; implement the full fixed evaluation sequence, all closed reason outcomes and sorted traversal; catch/represent invalid trusted registry state as `UNAVAILABLE` without exception text; add negative vectors for collision, migration-required/incompatible, profile/Core/interfaces, all budgets, graph bounds and invalid registry. |

### B1-051-OBS-01 — Repository PostgreSQL test bootstrap is unavailable

| Field | Detail |
|---|---|
| Severity | Observation (non-blocking to this pure-Core review) |
| Exact behavior | Normal pytest imports the repository global `conftest.py` and fails PostgreSQL authentication before collection. |
| Attribution | Reproducible, pre-collection, outside the pure Batch-1 source manifest; Batch-1 neither changes database code nor credentials. |
| Follow-up | Resolve under separately authorized test-environment/infrastructure work. Do not record a full-suite PASS until that environment can collect and run it. |

## Focused-test quality assessment

The four tests genuinely cover the empty release digest, static adapter matching,
basic strict fields, selected-set/combination helper distinction, direct
dependency/profile handling, entitlement `NOT_REQUIRED`, conformance adapter
matching, and exact legacy strings. They do not cover the defects above:
descriptor/contribution ordering permutations and Unicode rejection; typed
digest substitution at actual DTO fields; the required closed contribution
schemas; taxonomy/contribution collision and migration-incompatible evaluation;
invalid Registry `UNAVAILABLE`; full aggregate budgets; sorted graph traversal;
or mutation/provenance negative cases. These gaps support the Major defects but
are not counted as a separate test-only finding.

## Required remediation and governance state

Required remediation is limited to the four Major findings above, still within
the accepted Batch-1 Core boundary. It must not add persistence, migrations,
API/frontend, operational E/I/C behavior, commercial entitlement enforcement,
Batch 2, or PATCH-052 work. No accepted Architecture/ADR/EDS/IDS/Plan
reconciliation is required: the implementation deviates from already accepted
requirements.

| Governance item | State after review |
|---|---|
| Batch 1 acceptance eligibility | **not eligible** until all Major findings are remediated and independently re-reviewed |
| Batch 2 eligibility / authority | **not eligible / not authorized** |
| Migration creation / execution | **not authorized / not authorized** |
| IDS051-OBS-01 | **OPEN / NON-BLOCKING / downstream implementation and deployment evidence obligation** |
| PATCH-051 | **REGISTERED / OPEN** |
| PATCH-052 | **not started / not authorized** |
| Commercial V1 roadmap | unchanged; no implementation authority granted |
| Next resume point | Human-authorized, focused Batch-1 remediation for `B1-051-MAJ-01` through `B1-051-MAJ-04`, followed by a fresh independent Batch-1 review |

This review does not Human-accept Batch 1, start Batch 2, create/execute a
migration, begin PATCH-052, close PATCH-051, stage, commit, push, or alter
historical implementation evidence.
