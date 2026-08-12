# Independent PATCH-032 Batch 1 Implementation Review

## 1. Review Identity

| Field | Value |
|---|---|
| Review | PATCH-032 Batch 1 — Contracts and Domain Foundation |
| Authorized manifest | `docs/implementation/PATCH-032-Batch-1-Authorized-File-Manifest.md` |
| Review type | Independent Software Architecture and Implementation Review |
| Status | COMPLETE |
| Overall verdict | FAIL |
| Date | 2026-08-09 |
| Batch 2 authority | NOT GRANTED |

## 2. Artifacts Inspected

The review inspected ADR-023, PATCH-032, accepted EDS-032, accepted IDS-032,
accepted Implementation-Plan-032, IRR-032, the authorized Batch 1 manifest, all
nine production files, both focused test files, the complete relevant working-
tree diff, package exports, and comparable Aggregate/schema/port patterns.

Independent validation used the current working tree rather than committed HEAD.
No implementation or test file was modified by this review.

## 3. Authorized File Boundary Assessment

**PASS.** Batch 1 changes are restricted to the exact eleven authorized
production/test files. Earlier governance/documentation changes and the
pre-existing `docker-compose.yml` worktree change are not attributed to Batch 1.

The file boundary passes, but semantic content inside that boundary exceeds the
authorized Batch 1 persistence scope as recorded in finding `B1-MAJ-01`.

## 4. Findings Summary

| Severity | Count | IDs |
|---|---:|---|
| Critical | 1 | B1-CRIT-01 |
| Major | 7 | B1-MAJ-01, B1-MAJ-02, B1-MAJ-03, B1-MAJ-04, B1-MAJ-05, B1-MAJ-06, B1-MAJ-07 |
| Minor | 2 | B1-MIN-01, B1-MIN-02 |
| Observation | 0 | NONE |

## 5. Critical Finding

### B1-CRIT-01 — Accepted Aggregate state is directly mutable

- **Severity:** CRITICAL
- **Surface:** `backend/app/models/technical_report.py:39-66, 68-71, 94-100,
  187-194, 228-240`
- **Authoritative source:** ADR-023 accepted-content immutability; IDS-032
  §§5.4, 8, and 13; Batch 1 manifest §§3, 13, and 14 require accepted
  terminality and an empty post-acceptance semantic mutation allow-list at the
  domain/object-contract level.
- **Exact issue:** Public SQLAlchemy attributes permit callers to assign
  `lifecycle`, `purpose`, owner/scope, draft content, assumptions, conclusions,
  recommendations, qualification, provenance backing state, acceptance fields,
  version, and timestamps without invoking an Aggregate command. After
  `accept_exact_draft`, assignments such as `report.draft_content = ...`,
  `report.lifecycle = "draft"`, or `report.accepted_by_id = ...` are accepted by
  the object. The existing test itself assigns an unauthorized `published`
  lifecycle directly before testing a later method.
- **Risk:** Accepted technical content and Human acceptance can be altered or
  reopened at the domain level, defeating the core authority boundary before
  database triggers are introduced. This is a fundamental accepted-content
  integrity violation.
- **Required correction:** Make Aggregate-owned semantic, lifecycle, ownership,
  provenance, version, and acceptance state non-publicly mutable through the
  domain contract. Permit mutation only inside the approved Aggregate command
  methods while draft, and prove direct assignment/bypass rejection for every
  acceptance-defining field. Preserve later database-trigger enforcement as a
  separate defense-in-depth batch.

## 6. Major Findings

### B1-MAJ-01 — SQLAlchemy persistence mapping was pulled into Batch 1

- **Severity:** MAJOR
- **Surface:** `backend/app/models/technical_report.py:6-9, 34-66` and
  `backend/app/models/__init__.py`
- **Authoritative source:** Authorized manifest §§3, 11, and 14; review scope
  expressly prohibits SQLAlchemy Technical Report persistence in Batch 1;
  Implementation-Plan-032 places persistence schema in Batch 2.
- **Exact issue:** The Batch 1 file declares the full `technical_reports`
  SQLAlchemy table mapping, PostgreSQL UUID columns, foreign keys, JSON fields,
  accepted snapshot column, and acceptance persistence fields, and registers
  the model through `app.models`.
- **Risk:** Importing the model changes SQLAlchemy metadata before the authorized
  migration/schema/constraint review and conflates domain acceptance with an
  incomplete persistence design lacking the accepted checks, provenance table,
  triggers, grants, and role boundary.
- **Required correction:** Remove Batch 2 persistence mapping and metadata
  registration from Batch 1. Retain a persistence-independent Aggregate/domain
  contract within the authorized file boundary, or return to governance if the
  accepted combined-file plan cannot be executed without persistence scope.

### B1-MAJ-02 — Historical contracts do not enforce canonical closed vocabularies or normalization

- **Severity:** MAJOR
- **Surface:** `backend/app/models/technical_report_command.py:109-247` and
  `backend/app/schemas/technical_report.py:78-173`
- **Authoritative source:** IDS-032 §§12.2.1–12.3 require actual canonical enum
  types/stored values and owning-model normalization for every historical
  field.
- **Exact issue:** Source kind, lifecycle, standing, family, discipline, object
  type, authority, relationship family/type, and related fields are unrestricted
  strings in both domain and Pydantic contracts. Arbitrary non-empty values are
  accepted. Capture content normalization does not reproduce the canonical
  owner's CRLF/control-character rules, and Capture source reference does not
  enforce the canonical safe single-line rule.
- **Risk:** A report can hash and accept a historical representation that could
  never be canonical source state, breaking repository alignment, deterministic
  reconstruction, and historical authority.
- **Required correction:** Type every accepted enum field with the actual
  canonical enum or an exact validated equivalent, apply the owner-defined
  normalization and control-character rules, and add negative tests for invalid
  values for each of the four contracts.

### B1-MAJ-03 — Provenance contract is incomplete and permits incoherent source shapes

- **Severity:** MAJOR
- **Surface:** `backend/app/models/technical_report_command.py:280-315` and
  `backend/app/schemas/technical_report.py:182-205`
- **Authoritative source:** IDS-032 §§7.2, 7.2.1, 12.1, and 12.4 require closed
  canonical, external/Human, standards, and contextual locator shapes and
  source-class/type coherence.
- **Exact issue:** `TechnicalReportProvenanceEntry` lacks accepted external/
  Human locators, standards identity/authority/edition/clause fields,
  observation/retrieval/submission times, attribution distinctions, and the
  corresponding closed minimum representation contracts. It validates only a
  subset of canonical-material and contextual behavior. It does not require the
  historical basis discriminator to match `source_type`; for example, an
  Evidence source type can carry a Capture basis.
- **Risk:** Later acceptance code would need to invent provenance fields and
  coherence rules, while current contracts permit ambiguous or falsely typed
  provenance.
- **Required correction:** Implement the complete closed provenance union and
  exact locator/coherence matrix authorized by IDS-032, including source-class/
  type/basis matching and all required/forbidden field combinations, without an
  open payload mapping.

### B1-MAJ-04 — Accepted snapshot contract is not the complete integrity-protected accepted representation

- **Severity:** MAJOR
- **Surface:** `backend/app/models/technical_report_command.py:317-343` and
  `backend/app/schemas/technical_report.py:276-293`
- **Authoritative source:** IDS-032 §§7.2.2, 8.4, and 14 require a typed,
  integrity-protected accepted representation binding report identity, purpose,
  scope, exact content, qualification, material-source manifest, source
  versions/snapshots/digests, exact revision/version, accepting Human, and time.
- **Exact issue:** The snapshot does not bind trusted Organization, mandatory
  Workspace, or optional Project scope and defines no canonical snapshot
  serialization/integrity digest contract. Its provenance is also incomplete as
  described by `B1-MAJ-03`. `_accepted_snapshot_data` is never populated, while
  a separate transient object is treated as the accepted snapshot.
- **Risk:** Later accepted reads and persistence cannot rely on one complete,
  deterministic acceptance representation without redesign or divergent state.
- **Required correction:** Define the complete frozen accepted snapshot and its
  capability-local canonical integrity contract exactly as accepted, including
  trusted scope and complete provenance, while keeping persistence mechanics in
  their authorized later batch.

### B1-MAJ-05 — Inward ports are not exact typed contracts

- **Severity:** MAJOR
- **Surface:** `backend/app/ports/technical_report.py:11-71`
- **Authoritative source:** IDS-032 §§9–12 and Implementation-Plan-032 Step S05
  require typed inward contracts that prevent implementation improvisation.
- **Exact issue:** Repository list/provenance returns, authorization, reference
  validation, historical resolution, assistant, both Audit paths, and
  idempotency use untyped `**values` or omit return types. Domain event recording
  accepts `tuple[object, ...]`. Unit-of-Work context methods are untyped.
- **Risk:** Later batches can implement incompatible call shapes, leak ORM or
  protected data, split authority semantics, or require contract changes during
  implementation.
- **Required correction:** Replace untyped variadic boundaries with the exact
  actor, operation, scope, command, result, read-page, historical, Audit,
  idempotency, and context-manager types specified by IDS-032. Keep ports
  implementation-free.

### B1-MAJ-06 — Required Domain Event and draft-revision contracts are absent

- **Severity:** MAJOR
- **Surface:** `backend/app/models/technical_report_command.py:345-409` and
  `backend/app/ports/technical_report.py:45-52`
- **Authoritative source:** IDS-032 §§5.2, 5.3, 15, and 21; Batch 1 manifest §4
  assigns results/events and `TechnicalReportDraftRevision` to the contract
  foundation.
- **Exact issue:** No `TechnicalReportDomainEvent` contract exists,
  `TechnicalReportCommandResult` carries no events, and the event recorder uses
  opaque objects. No `TechnicalReportDraftRevision` value object exists; the
  implementation substitutes only a raw UUID.
- **Risk:** Later Audit/outbox/UoW work cannot consume stable domain outcomes and
  would need to redesign Batch 1 contracts or fabricate events outside the
  Aggregate.
- **Required correction:** Add the exact frozen draft-revision and protected-
  minimal Domain Event contracts, have each Aggregate command return its
  authorized event tuple, and type the event port accordingly. Do not add
  durable outbox persistence in Batch 1.

### B1-MAJ-07 — Focused tests materially overstate Batch 1 guarantees

- **Severity:** MAJOR
- **Surface:** `backend/tests/test_technical_report_aggregate.py` and
  `backend/tests/test_technical_report_schemas.py`
- **Authoritative source:** Authorized manifest §13 and review requirement §17.
- **Exact issue:** Tests verify command-method rejection after acceptance but do
  not test direct field mutation; the invalid-lifecycle test creates the illegal
  state by direct assignment. Per-source tests do not exercise invalid enum/
  vocabulary values, naive timestamps, prohibited Capture controls/reference
  newlines, source-type/basis mismatch, provenance-shape coherence, incomplete
  external/standards contracts, snapshot scope/integrity, command events, or
  typed ports. The shared missing/extra-field test is not evidence for the
  required invalid-value matrix.
- **Risk:** The reported 23-pass suite is green while Critical and Major
  contracts remain violated, creating false acceptance evidence.
- **Required correction:** Add negative behavioral tests that first fail for
  every corrected invariant, especially direct accepted-state mutation,
  lifecycle assignment, canonical enum/normalization rules, provenance union
  coherence, complete snapshot integrity, Domain Events, and typed ports.

## 7. Minor Findings

### B1-MIN-01 — Frozen command/value contracts lack complete construction validation

- **Severity:** MINOR
- **Surface:** `backend/app/models/technical_report_command.py:345-409`
- **Authoritative source:** IDS-032 §§5.2–5.4 and 21 require positive versions,
  coherent identities, and explicit Human confirmation at contract boundaries.
- **Exact issue:** Several dataclasses accept invalid runtime values until an
  Aggregate method happens to inspect them; `AcceptanceConfirmation` does not
  validate positive version or a strict boolean, and the acceptance-record
  value object has no construction validation.
- **Risk:** Invalid domain contracts can circulate before reaching the
  Aggregate, weakening type-boundary guarantees.
- **Required correction:** Add complete `__post_init__` validation to every
  frozen command/value contract and focused negative tests.

### B1-MIN-02 — Timezone and positive read fields are not consistently strict in schemas

- **Severity:** MINOR
- **Surface:** `backend/app/schemas/technical_report.py:78-173, 254-300`
- **Authoritative source:** IDS-032 §§12.3 and 17 require aware UTC historical
  timestamps, positive identifiers/versions, and strict typed DTOs.
- **Exact issue:** Pydantic historical timestamp fields accept naive datetimes
  until optional conversion to the domain object, and several response IDs/
  versions use unconstrained integers.
- **Risk:** Invalid DTOs can be constructed at the declared schema boundary.
- **Required correction:** Enforce aware timestamps and positive identifiers/
  versions consistently in the Pydantic models.

## 8. Domain and Authority Assessment

- **Lifecycle / Aggregate:** FAIL due `B1-CRIT-01` and incomplete domain
  contracts.
- **Human authority boundary:** FAIL because acceptance-defining owner and Human
  fields remain directly assignable despite owner checks inside commands.
- **Accepted snapshot:** FAIL due `B1-CRIT-01` and `B1-MAJ-04`.
- **Successor / lineage command behavior:** PASS. The method creates a new draft,
  keeps the accepted predecessor unchanged during the command, records an
  explicit predecessor UUID, inherits no acceptance, and introduces no
  supersession state or command. Direct field mutability remains covered by the
  Critical finding.

The enum module contains exactly `draft` and `accepted`; no extra Technical
Report lifecycle enum state was introduced.

## 9. Historical, Serialization, and Digest Assessment

- **Historical contracts:** FAIL due unrestricted canonical vocabularies,
  normalization mismatch, and incomplete provenance coherence.
- **Canonical serialization:** FAIL. Key ordering, UTF-8, explicit nulls,
  booleans, integers, UUIDs, aware UTC timestamp formatting, NFC, set-like
  Evidence sorting, and float rejection are implemented, but the serializer
  receives historical values that were not normalized/validated exactly as the
  canonical owner requires.
- **SHA-256 digest:** PASS for the implemented input contract. It hashes the
  exact canonical UTF-8 bytes, emits lowercase hexadecimal, and uses constant-
  time comparison without HMAC, signing, encryption, or key management. This
  does not cure the invalid canonical input contract.

## 10. Schema, Port, Exception, and Export Assessment

- **Schemas:** FAIL due open canonical vocabulary strings, incomplete provenance
  union, and strictness gaps.
- **Ports:** FAIL due untyped variadic collaborator contracts and missing typed
  event contract. No adapter, DB query, network call, or concrete transaction is
  implemented in the port module.
- **Exceptions:** FAIL for Batch 1 layering. Domain/contract exceptions directly
  embed numeric HTTP mappings through `SatcoException`, despite Batch 1's
  explicit prohibition on transport/HTTP mapping. Stable codes/messages follow
  existing application-exception convention, but domain errors need a
  transport-neutral boundary or an explicitly reconciled accepted convention.
- **Exports:** PASS. Only authorized Technical Report imports were added, and no
  unrelated export was reordered or removed. Import/static execution succeeds.

## 11. Test Evidence

Focused command:

```text
docker exec -e TEST_DATABASE_URL=postgresql://satco:satco_password@postgres:5432/satco_platform_patch02022_test satco-backend python -m pytest -q tests/test_technical_report_aggregate.py tests/test_technical_report_schemas.py
```

Result: **23 passed, 0 failed**; two unrelated pre-existing Pydantic deprecation
warnings.

Adjacent regression command:

```text
docker exec -e TEST_DATABASE_URL=postgresql://satco:satco_password@postgres:5432/satco_platform_patch02022_test satco-backend python -m pytest -q tests/test_engineering_object_aggregate_commands.py tests/test_engineering_object_schemas.py tests/test_engineering_relationship_aggregate.py tests/test_engineering_relationship_schemas.py tests/test_engineering_experience_capture_aggregate.py tests/test_engineering_experience_capture_schemas.py tests/test_evidence_aggregate.py tests/test_evidence_schemas.py tests/test_relationship_lifecycle_exports.py
```

Result: **57 passed, 0 failed**; two unrelated pre-existing Pydantic deprecation
warnings.

Syntax compilation and imports pass. Test execution success does not override
the untested Critical and Major violations.

## 12. Scope-Control Assessment

**FAIL.** No migration, PostgreSQL role, trigger, repository implementation,
UoW implementation, Audit implementation, outbox/idempotency persistence,
service, router, AI workflow, frontend, or configuration change was introduced.
However, the full SQLAlchemy Technical Report root-table mapping and model
metadata registration are Batch 2 persistence work pulled into Batch 1.

## 13. Overall Verdict

```text
Independent PATCH-032 Batch 1 Review: COMPLETE
Overall verdict: FAIL
Critical findings: 1 — B1-CRIT-01
Major findings: 7 — B1-MAJ-01 through B1-MAJ-07
Minor findings: 2 — B1-MIN-01 / B1-MIN-02
Observations: 0
Authorized file boundary: PASS
Lifecycle / Aggregate: FAIL
Human authority boundary: FAIL
Accepted snapshot: FAIL
Successor / Lineage: PASS
Historical contracts: FAIL
Canonical serialization: FAIL
SHA-256 digest: PASS
Schemas: FAIL
Ports / Exceptions / Exports: FAIL
Scope control: FAIL
Batch 1 acceptance readiness: BLOCKED
Batch 2 authority: NOT GRANTED
```

## 14. Required Next Governance Action

Authorize and perform a focused Batch 1 remediation limited to the existing
eleven-file manifest. Resolve every Critical and Major finding, add the required
negative tests, rerun focused and adjacent validation, then repeat this
Independent Batch 1 Review. If removing SQLAlchemy persistence while preserving
the accepted combined model file requires a design/file-boundary change, stop
and return to IDS/Implementation Plan governance rather than improvising.

## 15. Integrity Record

This review creates only
`docs/reviews/PATCH-032-Batch-1-Implementation-Review.md`. It modifies no
production code, tests, migration, configuration, infrastructure, accepted
design, or governance authority; executes no Batch 2 work; and performs no
commit or push.

`git diff --check`: PASS.

## 16. Revision History

| Version | Date | Description |
|---|---|---|
| 1.0 | 2026-08-09 | Independent Batch 1 review FAIL: one Critical, seven Major, and two Minor findings; Batch 1 acceptance blocked. |

---

## 17. Focused Independent Batch 1 Re-review

### 17.1 Review Identity

| Field | Value |
|---|---|
| Review | Focused Independent PATCH-032 Batch 1 Re-review |
| Date | 2026-08-09 |
| Scope | Resolution of B1-CRIT-01, B1-MAJ-01 through B1-MAJ-07, B1-MIN-01, and B1-MIN-02 only |
| Historical review | Section 5 through Section 16 preserved unchanged |
| Focused verdict | FAIL |
| Batch 1 acceptance readiness | BLOCKED |
| Batch 2 authority | NOT GRANTED |

### 17.2 Remediation and Evidence Reviewed

The re-review inspected the accepted IDS-032, accepted
Implementation-Plan-032, the authorized eleven-file Batch 1 manifest, the
initial independent review, all remediated files within that manifest, focused
tests, adjacent canonical regressions, compile/import behavior, prohibited
patterns, and the current repository diff.

### 17.3 Resolution Status

| Finding | Status | Independent evidence |
|---|---|---|
| B1-CRIT-01 | RESOLVED | The Aggregate is persistence-independent, exposes read-only public properties, has no instance dictionary, and direct public assignment is rejected before and after acceptance. Authorized methods enforce accepted terminality. |
| B1-MAJ-01 | RESOLVED | `TechnicalReport` has no SQLAlchemy inheritance, mapping, columns, foreign keys, PostgreSQL types, table metadata, or `__tablename__`; `app.models` exports only the domain Aggregate. |
| B1-MAJ-02 | RESOLVED | Historical bases use the canonical Capture, Evidence, EngineeringObject, and EngineeringRelationship enums. Capture CRLF, control-character, and safe single-line rules align with the canonical owner, and arbitrary vocabulary values are rejected. |
| B1-MAJ-03 | NOT RESOLVED | Locator/source-class/source-type/basis matching is present, but canonical `owning_capability` remains an arbitrary optional string and is not required or matched to the selected canonical source owner. A Universal Capture locator can therefore declare an Evidence or arbitrary owning capability. The accepted source-class/type/owner coherence matrix remains incomplete. |
| B1-MAJ-04 | RESOLVED | The frozen snapshot binds identity, revision, version, purpose, trusted scope, semantic content, qualification, provenance, acceptance, and predecessor lineage. One read-only snapshot is retained, and deterministic canonical bytes plus SHA-256 cover the complete dataclass representation. |
| B1-MAJ-05 | RESOLVED | Port methods have explicit parameter and return annotations, typed request/result/page/event contracts, typed context-manager surfaces, and no variadic `**values`, ORM, Session, row, or opaque event tuple boundary. Ports remain interfaces only. |
| B1-MAJ-06 | RESOLVED | Frozen draft-revision and protected-minimal Domain Event contracts exist; command results contain typed event tuples; create, revise, accept, and successor commands produce one non-plaintext event. |
| B1-MAJ-07 | NOT RESOLVED | Tests now cover direct mutation, vocabularies, Capture normalization, one source/basis mismatch, snapshot scope/integrity, events, and typed ports. They do not prove canonical owning-capability coherence, missing/forbidden external and standards locator combinations, provenance Pydantic-union extra-field rejection, or the full mismatch matrix required by the remediation. The test evidence therefore still overstates complete provenance enforcement. |
| B1-MIN-01 | NOT RESOLVED | Positive versions and strict confirmation are improved, but UUID identity annotations in frozen dataclasses are not validated at construction, several command wrappers rely only on nested values, and not every required identity/coherence invariant is enforced directly. |
| B1-MIN-02 | NOT RESOLVED | Historical timestamps are aware at the Pydantic boundary and acceptance confirmation is strict, but summary/read DTO timestamps remain unconstrained `datetime`, and summary/read identifiers and versions still use unconstrained integers. UTC/positive strictness is not consistent across all schemas. |

### 17.4 New Finding

#### B1-RR-MAJ-01 — Failed draft revision can leave mutated Aggregate state

- **Severity:** MAJOR
- **Surface:** `backend/app/models/technical_report.py`, `revise()` and
  `_result()`
- **Authoritative source:** IDS-032 §§5.3–5.4 and 21 require coherent command
  rejection, exactly one successful version/revision advancement, and no state
  change on command failure.
- **Exact issue:** `revise()` mutates content, qualification, provenance,
  revision, version, and `updated_at` before `_result()` constructs and validates
  `TechnicalReportDomainEvent`. An invalid command occurrence time, such as a
  naive `now`, causes event construction to raise after the Aggregate has
  already changed.
- **Risk:** A rejected command can leave an in-memory Aggregate in a partially
  successful state and later persistence code could save a mutation for which
  no valid result or event exists.
- **Required correction:** Validate command time and all result/event inputs
  before Aggregate mutation, or construct the complete next state and event
  atomically before applying it. Add a negative test proving every failed
  command leaves all Aggregate state unchanged.

### 17.5 Focused Assessments

| Assessment | Result |
|---|---|
| Authorized file boundary | PASS |
| Lifecycle / Aggregate public mutation protection | PASS |
| Human authority boundary | PASS |
| Accepted snapshot | PASS |
| Successor / lineage | PASS |
| Historical contracts | PASS |
| Provenance union / coherence | FAIL |
| Canonical serialization | PASS |
| SHA-256 digest | PASS |
| Typed ports | PASS |
| Draft revision / Domain Events | FAIL — new atomicity finding |
| Schemas | FAIL |
| Scope control | PASS |

### 17.6 Independent Validation Evidence

Focused command:

```text
docker exec -e TEST_DATABASE_URL=postgresql://satco:satco_password@postgres:5432/satco_platform_patch02022_test satco-backend python -m pytest -q tests/test_technical_report_aggregate.py tests/test_technical_report_schemas.py
```

Result: **61 passed, 0 failed**; two unrelated existing Pydantic deprecation
warnings.

Adjacent regression command:

```text
docker exec -e TEST_DATABASE_URL=postgresql://satco:satco_password@postgres:5432/satco_platform_patch02022_test satco-backend python -m pytest -q tests/test_engineering_object_aggregate_commands.py tests/test_engineering_object_schemas.py tests/test_engineering_relationship_aggregate.py tests/test_engineering_relationship_schemas.py tests/test_engineering_experience_capture_aggregate.py tests/test_engineering_experience_capture_schemas.py tests/test_evidence_aggregate.py tests/test_evidence_schemas.py tests/test_relationship_lifecycle_exports.py
```

Result: **57 passed, 0 failed**; two unrelated existing Pydantic deprecation
warnings.

Static/import commands:

```text
docker exec satco-backend python -m compileall -q app/enums/technical_report.py app/exceptions/technical_report.py app/models/technical_report_command.py app/models/technical_report.py app/schemas/technical_report.py app/ports/technical_report.py tests/test_technical_report_aggregate.py tests/test_technical_report_schemas.py
docker exec satco-backend python -c "from app.models import TechnicalReport; from app.ports import TechnicalReportRepository; assert not hasattr(TechnicalReport, '__tablename__')"
```

Result: **PASS**. No import cycle or Technical Report persistence metadata was
observed. Prohibited SQLAlchemy mapping and variadic port scans passed.

### 17.7 Focused Verdict and Next Governance Action

Focused re-review verdict: **FAIL**.

Batch 1 remains **BLOCKED** because B1-MAJ-03 and B1-MAJ-07 remain unresolved
and B1-RR-MAJ-01 is a new Major finding. B1-MIN-01 and B1-MIN-02 also remain.
Batch 2 authority remains **NOT GRANTED**.

The next governance action is to authorize a second focused Batch 1 remediation
within the existing eleven-file manifest for the unresolved provenance-owner
coherence, complete negative test matrix, failed-command atomicity, and the two
remaining Minor strictness findings, followed by another focused independent
re-review.

### 17.8 Focused Re-review Integrity

The re-review modified only this review artifact. It modified no production
code, test, migration, configuration, accepted design, manifest, or governance
authority; began no Batch 2 work; and performed no commit or push.

---

## 18. Second Focused Independent Batch 1 Re-review

### 18.1 Review Identity

| Field | Value |
|---|---|
| Review | Second Focused Independent PATCH-032 Batch 1 Re-review |
| Date | 2026-08-09 |
| Scope | B1-MAJ-03, B1-MAJ-07, B1-RR-MAJ-01, B1-MIN-01, B1-MIN-02, plus preservation of previously resolved Critical/Major findings |
| Historical evidence | Original FAIL and first focused re-review FAIL preserved unchanged |
| Verdict | PASS |
| Batch 1 acceptance readiness | READY |
| Batch 2 authority | NOT GRANTED |

### 18.2 Resolution Evidence

| Finding | Status | Independent evidence |
|---|---|---|
| B1-MAJ-03 | RESOLVED | `TechnicalReportOwningCapability` closes the four canonical owner tokens. Domain and Pydantic contracts enforce source class, source type, exact owner, locator schema, and historical-basis type as one matrix. External/Human, standards, and contextual variants prohibit canonical ownership and reject cross-variant locators and extra fields. |
| B1-MAJ-07 | RESOLVED | Parameterized tests cover every canonical source with valid and wrong/arbitrary owner, wrong basis/locator, incompatible class, and extra-field cases. External/Human, standards, contextual, discriminator, timestamp, and Pydantic-union rejection cases are exercised directly. |
| B1-RR-MAJ-01 | RESOLVED | `now` and other failure-prone inputs are validated before mutation. Draft revision constructs its next revision, event, and command result before applying state. Acceptance constructs its snapshot, record, event, and result before applying state. Failure tests compare the complete observable state before and after rejected revise, accept, and successor commands. |
| B1-MIN-01 | NOT RESOLVED | UUID, positive version/revision, strict confirmation, UTC time, digest, enum, nested contract, and wrapper validation are materially strengthened. Frozen dataclasses still accept mutable list values for some tuple-annotated fields such as provenance/events, so every frozen contract does not yet enforce its declared immutable container shape at construction. |
| B1-MIN-02 | NOT RESOLVED | Read/summary timestamps require aware UTC values and identifier/version fields require positive values. Pydantic numeric fields remain coercive rather than strict—for example a numeric string may be converted to an integer—so the requested strict boundary-type behavior is not complete. |

### 18.3 Preservation Check

| Finding | Result |
|---|---|
| B1-CRIT-01 — direct mutation protection | PRESERVED RESOLVED |
| B1-MAJ-01 — persistence scope removed | PRESERVED RESOLVED |
| B1-MAJ-02 — canonical vocabularies and Capture normalization | PRESERVED RESOLVED |
| B1-MAJ-04 — accepted snapshot completeness and integrity | PRESERVED RESOLVED |
| B1-MAJ-05 — typed ports | PRESERVED RESOLVED |
| B1-MAJ-06 — draft revision and protected-minimal Domain Events | PRESERVED RESOLVED |

### 18.4 New Findings

No new Critical, Major, Minor, or Observation finding was identified. The two
strictness gaps above remain classified under the existing B1-MIN-01 and
B1-MIN-02 findings and do not create a new finding.

### 18.5 Scope and Boundary Assessment

| Assessment | Result |
|---|---|
| Authorized eleven-file boundary | PASS |
| Canonical owner coherence | PASS |
| Complete provenance matrix | PASS |
| Pydantic provenance union | PASS |
| Failed-command atomicity | PASS |
| Frozen contract strictness | FAIL — existing Minor finding only |
| Read/summary schema strictness | FAIL — existing Minor finding only |
| Persistence independence | PASS |
| Prohibited Batch 2 behavior | ABSENT |
| Scope control | PASS |

No Technical Report persistence mapping, migration, DB trigger, DB role,
repository implementation, Unit of Work implementation, Audit implementation,
outbox implementation, application service, API/router, frontend, or other
Batch 2 behavior was introduced.

### 18.6 Independent Validation

Focused command:

```text
docker exec -e TEST_DATABASE_URL=postgresql://satco:satco_password@postgres:5432/satco_platform_patch02022_test satco-backend python -m pytest -q tests/test_technical_report_aggregate.py tests/test_technical_report_schemas.py
```

Result: **85 passed, 0 failed**; two unrelated existing Pydantic deprecation
warnings.

Adjacent regression command:

```text
docker exec -e TEST_DATABASE_URL=postgresql://satco:satco_password@postgres:5432/satco_platform_patch02022_test satco-backend python -m pytest -q tests/test_engineering_object_aggregate_commands.py tests/test_engineering_object_schemas.py tests/test_engineering_relationship_aggregate.py tests/test_engineering_relationship_schemas.py tests/test_engineering_experience_capture_aggregate.py tests/test_engineering_experience_capture_schemas.py tests/test_evidence_aggregate.py tests/test_evidence_schemas.py tests/test_relationship_lifecycle_exports.py
```

Result: **57 passed, 0 failed**; two unrelated existing Pydantic deprecation
warnings.

Static/import commands:

```text
docker exec satco-backend python -m compileall -q app/enums/technical_report.py app/exceptions/technical_report.py app/models/technical_report_command.py app/models/technical_report.py app/schemas/technical_report.py app/ports/technical_report.py tests/test_technical_report_aggregate.py tests/test_technical_report_schemas.py
docker exec satco-backend python -c "from app.enums import TechnicalReportOwningCapability; from app.models import TechnicalReport; from app.ports import TechnicalReportRepository; assert not hasattr(TechnicalReport, '__tablename__')"
```

Result: **PASS**. Prohibited persistence and variadic-port scans passed. The
only variadic signature found was the Aggregate's private `_build(**state)`
factory, not an inward port or externally callable mutation contract.

`git diff --check`: **PASS**.

### 18.7 Verdict and Required Next Governance Action

Second focused re-review verdict: **PASS**.

All blocking Critical and Major findings are resolved, all previously resolved
Critical/Major findings remain resolved, focused and adjacent tests pass, and
scope control passes. Batch 1 is **READY** for the Human Batch 1 acceptance
decision. B1-MIN-01 and B1-MIN-02 remain non-blocking and must be tracked for a
later bounded correction or explicitly accepted as residual findings by the
Human authority.

Batch 2 authority remains **NOT GRANTED**. The exact next governance action is
Human Batch 1 acceptance, including disposition of the two non-blocking Minor
findings; Batch 2 may begin only through a separate explicit authority grant.

### 18.8 Integrity Record

This re-review modified only
`docs/reviews/PATCH-032-Batch-1-Implementation-Review.md`. It modified no
production code, test, migration, configuration, accepted design, manifest, or
governance authority; began no Batch 2 work; and performed no commit or push.
