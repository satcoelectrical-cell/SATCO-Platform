# IDS-052 — Electrical, Instrumentation, and Control & Automation Discipline Packages V1

## 1. Control and verdict

| Field | Frozen value |
|---|---|
| PATCH | PATCH-052 — Electrical, Instrumentation, and Control & Automation Discipline Packages V1 |
| Status | **IDS ACCEPTED — Implementation-Plan-052 authorized for design only** |
| Authority | Accepted Architecture-052, ADR-024, ADR-025, and EDS-052 |
| Release | `patch-052.eic-v1`; Electrical, Instrumentation, Control & Automation `1.0.0` |
| Design verdict | Feasible as a bounded additive implementation; this document grants no implementation or migration authority. |

This document is an implementation design, not runtime code, a migration, a deployment plan, or an operational acceptance. It imports, without reinterpretation, the exact catalogs, tuple matrices, field orders, fixtures, resource ceilings, and 46-vector inventory in EDS-052. All dotted declaration IDs and ordinals below mean the literal EDS-052 values.

Pre-design reconciliation found branch `patch-022.3a-development-infrastructure`, HEAD `af82723df9717040591a9172639b6574f23c98c1`, empty staged state, PATCH-051 closed, and sole Alembic head `e05100000006`. There is no PATCH-052 migration or operational implementation. Unrelated dirty/untracked work is preserved and excluded.

## 2. Invariants and source boundary

- No dynamic import, customer-selected module, executable upload, `eval`/`exec`, remote registry, package script, SQL payload, or AI-selected rule execution is permitted.
- Registry source is static application code. Existing deployment-only exclusive-guard installation/activation remains the only writer of Registry projection.
- Package configuration supplies capability only; it never supplies authorization. Protected owner scope is authorized before any package, count, identifier, input, Evidence, result, or finding is disclosed.
- Legacy rows receive neither inferred provenance nor inferred Identifiers. Null provenance means `legacy_unattributed`.
- No migration revision is allocated. A later authorized migration is named only as `<future-linear-revision>_patch_052_operational_eic_schema.py`.

### 2.1 Exact implementation file boundaries

| Area | Create in a later authorized implementation |
|---|---|
| Static release | `backend/app/discipline_packages/descriptors/releases/release_052_eic_v1.py`; `backend/app/discipline_packages/descriptors/eic_v1.py`; `backend/app/discipline_packages/operational.py` |
| Conformance/readiness | `backend/app/discipline_packages/conformance_manifest.py`; `backend/app/discipline_packages/conformance_harness_052.py`; `backend/app/discipline_packages/readiness_052.py` |
| Operation boundary | `app/ports/discipline_package_operations.py`; `app/adapters/discipline_package_operations.py`; `app/services/discipline_package_operation_service.py`; `app/schemas/discipline_package_operations.py`; `app/dependencies/discipline_package_operations.py` |
| Identifier | `app/enums/engineering_identifier.py`; `app/models/engineering_identifier.py`; `app/models/engineering_identifier_command.py`; `app/ports/engineering_identifier.py`; `app/repositories/engineering_identifier_repository.py`; `app/repositories/engineering_identifier_unit_of_work.py`; `app/services/engineering_identifier_service.py`; `app/schemas/engineering_identifier.py`; `app/dependencies/engineering_identifier.py`; `app/exceptions/engineering_identifier.py`; `app/api/v1/routers/engineering_identifiers.py` |
| Frontend | `frontend/src/disciplinePackages/PackageWorkspaceShell.tsx`; `ElectricalPackagePanel.tsx`; `InstrumentationPackagePanel.tsx`; `ControlAutomationPackagePanel.tsx` |

Modify only these existing integration seams: release exports, `discipline_package_registry.py`, `conformance.py`, `main.py`, enum/model/schema/dependency exports; Object, Relationship, Capture, Context, Deliverable, Technical Report owner command/model/schema/repository/UoW/service/router files; the Evidence query boundary; and the current frontend package component map/API client/routes. Existing public owner routes retain meaning. The identifier router is included exactly once by `main.py`.

## 3. Static release, catalog, and effective state

`release_052_eic_v1.py` exports one zero-argument constructor for a `TrustedDisciplinePackageRegistryV1`, with literal registrations in lexical key order: `electrical/1.0.0`, `instrumentation/1.0.0`, and `control_automation/1.0.0`. Each `DescriptorRegistration` has its source-computed digest, static adapter ID, and `executable_supported` membership. `commercial_v1.eic/1.0.0` contains exactly the seven accepted singleton/pair/triple combinations.

`eic_v1.py` contains typed inert values for descriptors, finite endpoint tuples, input requirements, Evidence requirements, Deliverable rows, rules, and conformance selectors. `operational.py` has literal dictionaries from accepted `operation_id`/executor reference to precompiled function; unknown or mismatched content is rejected. No customer input is ever used as a module, class, function, URL, query, template, expression, or import target.

The existing `DisciplinePackageRegistryService` continues to install immutable source projection and activate it only under its exclusive guard. `validate_source_projection_parity` is called by readiness and fails closed unless source release/digest, descriptors, standing, profiles, and combinations exactly equal the current projection. HTTP operations resolve package effective state only through the existing organization/project configuration and workspace applicability services. Unknown, unavailable, historical-only, mismatched, or non-profile selection produces no operating capability.

## 4. Exact discipline translation

Every EDS declaration becomes one `OperationalDeclaration` containing exact declaration ID, package/version, ordinal, owner, canonical type, operation, origin declaration ID, rule hooks, and vector IDs. The implementation has no second catalog.

| Package | Object mapping | Relationship mapping | Context / Deliverable / Evidence / rules | UI |
|---|---|---|---|---|
| Electrical | 8 `EngineeringObjectType` rows; add only `ELECTRICAL_FEEDER` and `ELECTRICAL_POWER_SOURCE`, extend electrical family/check/schema validation | 7 literal EDS endpoint tuple sets, owned by `EngineeringRelationship` | exact 5 / 4 / 4 / 5 EDS declarations | `ElectricalPackagePanel` |
| Instrumentation | 8 existing canonical object values | 5 literal EDS tuple sets | exact 5 / 4 / 4 / 5 EDS declarations | `InstrumentationPackagePanel` |
| Control & Automation | 7 existing canonical object values | 13 literal EDS tuple sets | exact 5 / 5 / 4 / 5 EDS declarations | `ControlAutomationPackagePanel` |

Object rows are exactly `{package}.object.{object_type}`; each forces the EDS §5 primary Identifier kind. Relationship declarations expand only the EDS §6 finite source/target Cartesian pairs, direction, cardinality, and permitted cross-workspace condition. Owner relationship validation runs first, then the package tuple allow-list. Instrumentation and Control legacy translation is a literal source-controlled mapping from current enum values to one declaration: missing/ambiguous translation is `422 PACKAGE_DECLARATION_MISMATCH`. No graph traversal, inferred relation, calculation, vendor/procurement selection, code generation, or cross-package rule is created.

All EDS Context/Evidence/Deliverable/rule declarations retain exact dotted IDs/ordinals. The selected Deliverable row is authoritative: readiness uses exactly its Context IDs and first three Evidence IDs; its fourth Evidence ID is issue-only. The conformance manifest is exactly 46 `ConformanceVectorV1` values—39 package and 7 combination—in EDS §17's exact 18-field order:
`schema_version, vector_id, subject_kind, subject_id, release_id, package_selection, descriptor_digest_selector, scenario_purpose, fixture_id, setup_preconditions, authoritative_inputs, operation_id, executor_reference, expected_result, expected_provenance, authorization_expectation, tenant_expectation, historical_expectation, failure_expectation`.
The harness rejects a missing, extra, unordered, noncanonical, or executable field.

## 5. Engineering Identifier: ADR-025 implementation

`EngineeringIdentifier` is a UUID-rooted independent aggregate/table, never an Object child or package table. Its ordered durable field contract, normalizer, scope, lifecycle, standing, primary/alternate roles, 0..16 current cardinality, retention, and lineage are exactly ADR-025 and EDS §8. It has restrictive foreign keys to one Object, project/workspace, actor roles, predecessor/successor rows, Evidence handles, and the nullable origin triple in §6.

The server alone normalizes display input using Unicode NFKC, Unicode trim, internal Unicode-whitespace collapse to U+0020, and default Unicode casefold. It rejects empty/control/unassigned/over-128 output and records algorithm `satco_identifier_nfkc_casefold_v1`. DTOs cannot supply normalized value, algorithm, organization, derived issuing scope, version, origin, or Audit data.

Repository methods are query/stage only: authorized scoped lookup, locked complete-current-set, lineage read, and signed-cursor history. They never commit. The service authorizes Project/Workspace/Object before value/conflict/count/lineage/origin disclosure. It applies these later schema controls:

- partial unique current value index on `(organization_id, project_id, issuing_scope_kind, issuing_scope_value, identifier_kind, normalized_value)`;
- partial unique one-current-primary index by `engineering_object_id`;
- current-set index `(engineering_object_id, lifecycle, primary_role)` and scoped history index `(organization_id, project_id, workspace_id, created_at, identifier_id)`;
- checks for lifecycle, standing, role, scope coherence, version, and all-null/all-non-null origin;
- deferred transaction enforcement after Object-set locks: at most 16 current, exactly one current primary for package-origin Object, and nonbranching/nonmerging/acyclic same-Object/same-scope lineage.

Package object creation accepts only display value and permitted Evidence handles; adapter resolution forces its EDS primary kind. It stages Object and Identifier with matching server-derived origin then rechecks/commits atomically. Add/replace/withdraw/reassign locks Object then Identifier UUIDs lexically, reauthorizes after lock, and retries only serialization/deadlock/unique races twice with fresh sessions. Physical deletion is unavailable.

## 6. Durable origin and owner workflows

Add nullable `origin_package_key`, `origin_project_configuration_revision`, and `origin_declaration_id` to `engineering_objects`, `engineering_relationships`, `engineering_experience_captures`, `engineering_deliverables`, and `engineering_identifiers`. A check requires all null or all non-null. Non-null values have a restrictive composite reference to the exact historical project configuration revision/selected package and service validation against descriptor/version/project/workspace/declaration. An immutable-update guard rejects changes and backfilling an old null triple. Reconfiguration and Workspace rebind never change stored origin.

Object flow: authorize project/workspace; resolve effective package; validate declaration/type; stage canonical Object origin and required primary Identifier origin; run object/relationship integrity; stage Audit/outbox; commit. Relationship flow authorizes both endpoints before package fact resolution, validates owner rule plus literal tuple, stages exact relation origin/Audit, and commits. Capture flow is a canonical Capture with package affordance origin only and cannot itself satisfy an input. Deliverable creation carries its exact deliverable origin. Evidence remains an independent owner aggregate with no fabricated package provenance.

Centralized transaction Audit records at operation time: package key/version, descriptor digest, Registry digest as applicable, configuration revision, declaration/rule ID, aggregate ID/version, actor, correlation, causation when applicable, result digest, and outcome. Audit history uses those persisted values, never current Workspace selection.

## 7. Context, Evidence, Deliverables, and Reports

Add `ContextSubjectKind.ENGINEERING_OBJECT` and `subject_engineering_object_id`. The later schema gives it restrictive Object FK, exactly-one subject target by kind, project/workspace coherence, and Object/lifecycle/subject lookup index. Context evaluation authorizes its Object first, projects direct current rows keyed to exact declarations, and never traverses a relationship.

Hard limits are exact: 64 Objects, 128 Relationships, 32 Deliverables, 322 Context projections, 24 readiness Evidence projections, five hooks, 384 KiB serialized envelope, zero traversal, and no continuation/chunk escape. At 65 Objects or any other limit exceedance evaluation fails closed. Missing, withdrawn, unauthorized, stale, over-limit, or partially unavailable source maps to `INDETERMINATE` and leaks no protected identity/count.

Readiness receives an already authorized Deliverable revision and literal selected requirements. One bounded set query checks only selected Evidence IDs for current lifecycle, current source standing, Human verification, declaration match, and visibility. There is no universal Evidence gate. `draft -> ready_for_review` uses the Deliverable row's Context plus first three Evidence requirements. `reviewed -> issued` rechecks that exact revision and its fourth evidence: `source_kind=human_review`, lower-case deliverable UUID `source_reference`, and lower-case revision UUID `source_revision`. It cannot be reused across revisions.

Report V2 adds only Capture/Object/Relationship locator variants, exactly matching EDS §11.6 field order, nullability, closed keys, and canonical serialization. Object V2 locks/rechecks Object plus complete current Identifier set, captures 1..16 for package-origin Object ordered primary then kind/normalized/UUID, and does no live identifier lookup after Report acceptance. Acceptance reauthorizes and compares every ID/version and complete set. V1 branches, accepted bytes/digests, Human acceptance, successor behavior, and Organizational Memory admission remain byte-compatible. No new Report source type/FK or historical rewrite exists.

## 8. Rules, API, frontend, and readiness

The 15 EDS rules are literal `RuleSpec` values: exact IDs/hooks/declaration linkage/input projection/predicate/failure category/result digest/vector linkage; 50 ms and 256 KiB/16 findings for object-relationship integrity, 100 ms for specified other hooks. Rule inputs are bounded values, not executable content. AI never executes or decides a rule. Timeout/error/unknown produces audited, fail-closed `INDETERMINATE`.

Additive package routes live under `/projects/{project_id}/discipline-packages/`:

| Route | DTO / protection |
|---|---|
| `POST workspaces/{workspace_id}/operations/objects` | `PackageObjectCreateRequest`; client supplies declaration plus primary display/Evidence only |
| `POST workspaces/{workspace_id}/operations/relationships` | `PackageRelationshipCreateRequest`; source/target IDs plus declaration; both independently authorized |
| `POST workspaces/{workspace_id}/operations/captures` | `PackageCaptureCreateRequest`; provenance affordance only |
| `GET workspaces/{workspace_id}/context-evaluation` | `PackageContextEvaluationResponse`; max 64 requested Objects, no continuation |
| `GET deliverables/{deliverable_id}/revisions/{revision_id}/readiness` | `PackageReadinessResponse`; direct authorized sources only |
| `POST deliverables/{deliverable_id}/revisions/{revision_id}/package-transition` | closed transition request; owner service owns state transition |
| Identifier list/mutation routes | authorized object-scoped history, create, replace, withdraw, primary reassignment |

The existing supported catalog remains max 50 and one complete finite result (maximum 8 objects/13 relationships/9 inputs/5 deliverables/4 Evidence/5 rules). Identifier history cursor is signed, opaque, bound to object/project/actor scope, expiry-bound, default 50/max 100. Protected denial is owner-compatible 404; invalid input 422; stale/conflict 409; unavailable projection 503. Client cannot provide organization, digest, standing, effective state, configuration revision, origin, Audit, or Human approval.

The workspace shell reads server effective state and selects exactly three statically imported panels. Panels render descriptor-driven finite workflows/readiness/guidance, never grant capability. They expose accessible responsive/RTL-safe loading/error/empty/protected states; make `HISTORICAL_READ_ONLY` non-mutating; and show `INDETERMINATE` without repair/ready action. No dynamic component loading, legacy selector, hidden count, or autonomous approval is allowed.

Readiness is non-empty/read-only/non-repairing: source release/descriptors/digests, projection parity, standing/profile/seven combinations, adapters/catalog/rules/46 vectors, schema/Identifier/origin/Report validators, frontend map, and representative Evidence paths. Any missing/unknown component is not ready.

## 9. Future migration, UoW, performance evidence

The future additive migration: preflights head/data/roles/validators; adds two object enum/check values; Identifier root and dependencies; nullable origin triples/checks/restrictive FKs; Object Context subject; indexes/immutable guards; V1-or-V2 Report validation/read support; then verifies. It never backfills provenance/Identifier, rewrites V1 Report/Memory bytes, or infers package classification. Downgrade is prohibited once PATCH-052 rows exist; only an explicitly tested forward-recovery path is acceptable.

`Patch052OperationUnitOfWork` owns cross-aggregate package mutation with one Session: staging-only owner repositories, identifier repository, configuration resolver, Audit/outbox recorder, one commit. Owner services add narrow noncommitting `stage_package_*` methods; their existing public UoWs remain unchanged. Lock order: configuration revision, workspace, Object UUID(s) lexical order, Identifier UUIDs lexical order, Deliverable/revision, then idempotency/Audit. Fresh-state authorization occurs after lock; revocation/staleness rolls back. Repositories never hidden-commit.

Future PostgreSQL evidence must—not is claimed to—prove fresh/upgrade head, constraints/FKs/triggers/roles/grants, legacy-null reads/no rewrite, atomic rollback/no prepared transactions, Identifier race/lineage, Context history/coherence, V1/V2 golden parity, index plans, bounded query count/no N+1, ceilings/timeouts, tenant-negative/protected-not-found, role separation, Registry parity, and all seven combinations. `IDS051-OBS-01` remains an open non-blocking deployment-evidence obligation.

## 10. Frozen batches and acceptance boundary

| Batch | Objective / separately required authority | Scope and proof | Explicit exclusion |
|---|---|---|---|
| 1 Shared operational release | separate implementation authority | static release/catalog/adapter, read-only readiness/conformance, disabled shell wiring; parity/security/component review | no schema, mutation, activation, discipline delivery |
| 2 Electrical + shared cutover | explicit migration-create/execution and Batch-2 authority | additive schema, Identifier/origin/Context/V2 seams; Electrical 8/7/5/4/4/5; isolated PostgreSQL and Electrical vectors | no Instrumentation/Control/combined delivery |
| 3 Instrumentation | separate Batch-3 authority after Batch-2 acceptance | exact 8/5/5/4/4/5, translation/cross-workspace/accessibility evidence | no Control or combined acceptance |
| 4 Control & Automation | separate Batch-4 authority after Batch-3 acceptance | exact 7/13/5/5/4/5, finite tuples/no-code-generation evidence | no combined release/PATCH-053 |
| 5 Combined conformance | separate Batch-5 authority after B2–B4 acceptance | seven combinations, 46 vectors, history/security/performance/RTL evidence | no inference/calculation/new migration |

Later tests include `test_patch_052_descriptors.py`, `test_discipline_package_operations.py`, `test_engineering_identifier_{contracts,repository,service,api,security,performance}.py`, `test_patch_052_{electrical,instrumentation,control,report_v2,conformance,migration}.py`, and frontend `discipline-package-operational.test.tsx`, plus focused extensions to existing owner tests. No batch starts by authority of this IDS, its future Plan, a predecessor's result, or readiness itself.

## 11. Governance disposition

Independent review passed with Critical/Major/Minor 0/0/0 and Human IDS acceptance is recorded in `docs/reviews/IDS-052-Electrical-Instrumentation-and-Control-Automation-Discipline-Packages-V1-Human-Acceptance.md`. This IDS fixes a complete bounded implementation path and authorizes only Implementation-Plan-052 design. It does not authorize code, tests, migrations, deployment, staging, commit, push, PATCH-053, provenance fabrication, or any Human engineering decision.
