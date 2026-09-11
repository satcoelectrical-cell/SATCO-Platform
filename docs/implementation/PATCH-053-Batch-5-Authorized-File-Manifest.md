# PATCH-053 — Batch 5 Authorized File Manifest

## A. Authority Header

| Field | Value |
|---|---|
| Document ID | `PATCH-053-B5-AUTHORIZED-FILE-MANIFEST` |
| PATCH / Batch | PATCH-053 / Batch 5 — Integrated E+I+C, Impact, Report, AI and release completion |
| Manifest status | **NARROWLY RECONCILED / REVIEW PASS / COMPLETE / AWAITING HUMAN RE-ACCEPTANCE** |
| Upstream authorities | ADR-026, Architecture-053, EDS-053 and IDS-053: Human accepted / authoritative / unchanged; narrowly reconciled Implementation-Plan-053: Human re-accepted / authoritative |
| Batch-1/2/3/4 state | **HUMAN ACCEPTED / COMPLETE** |
| Batch-4 baseline | `7f8b3b1f95dc736c78d81aee700aa07d93fe8ce1` |
| Alembic sole head | `e05300000002` |
| Successor migration | `e05300000002` is the authoritative current sole head; parent `e05300000001` |
| Remaining / cumulative vectors | exactly `21`; final target `96/96` |
| Batch-5 implementation | **PAUSED / NOT RESUMED BY THIS MANIFEST-ONLY RECONCILIATION / PENDING HUMAN RE-ACCEPTANCE; SEPARATE IMPLEMENTATION AUTHORITY ALREADY GRANTED** |
| PATCH-054+ | **NOT STARTED / NOT AUTHORIZED** |

This manifest is the exact maximum path and semantic-hunk boundary for a later,
separately Human-authorized Batch-5 implementation. Path presence never grants
whole-file replacement, unrelated cleanup, alternate layout, or authority to
implement before this manifest is Human accepted. Any required path or semantic
change outside this closed boundary is a stop condition for Human governance
reconciliation.

The accepted integrated machine scope is version `1.0.0`, combination
`cross.eic.v1`, interface `cross.interface.eic.change_path.v1`, path
`xdi.path.eic.change.v1`, projection `xdi.proj.change_seed.v1`, and rule
`xdi.eic.explicit_change_path.v1`. All Batch-1–4 identities remain unchanged.

## B. Exact Create Allow-List

Exactly 32 literal paths may be created during the governed Batch-5 lifecycle.
This manifest is the only path created by the present operation. Every other
path below remains prospective until separate implementation authority.

| Exact path | Purpose | Classification |
|---|---|---|
| `docs/implementation/PATCH-053-Batch-5-Authorized-File-Manifest.md` | Accepted maximum Batch-5 boundary | governance carry-in |
| `docs/implementation/PATCH-053-Batch-5-Implementation-Evidence.md` | Actual commands, results, digests, failures, scope and review evidence | derived evidence |
| `docs/implementation/PATCH-053-Batch-5-Performance-Evidence.md` | Actual query plans, budgets and timing evidence | derived evidence |
| `backend/migrations/versions/e05300000002_patch_053_prerequisite_completion.py` | One additive successor from `e05300000001` for the reconciled prerequisite boundary only | migration |
| `backend/app/adapters/cross_discipline_change_impact.py` | Invoke the public Project Control owner boundary between separate PATCH-053 UoWs | backend production |
| `backend/app/ai/cross_discipline_intelligence.py` | Optional provider-neutral, bounded, single-call advisory adapter | backend production |
| `backend/tests/test_cross_discipline_report.py` | Assessment projection, acceptance race, immutability and Report-authority evidence | backend test |
| `backend/tests/test_cross_discipline_ai.py` | Disabled, protected, bounds, one-call/zero-retry and non-authority evidence | backend test |
| `backend/tests/test_cross_discipline_impact_handoff.py` | Three-UoW handoff, retry, interruption, duplicate and revocation evidence | backend test |
| `frontend/src/components/crossDiscipline/CrossDisciplinePotentialImpactView.tsx` | Truthful pending/reconciled advisory Impact presentation | frontend production |
| `frontend/src/components/crossDiscipline/CrossDisciplineAIExplanation.tsx` | Explicit, separate and non-authoritative AI presentation | frontend production |
| `backend/tests/fixtures/cross_discipline/patch053.int01.change_path.fixture.v1.json` | INT01 exact fixture | fixture |
| `backend/tests/fixtures/cross_discipline/patch053.int02.no_change.fixture.v1.json` | INT02 exact fixture | fixture |
| `backend/tests/fixtures/cross_discipline/patch053.int03.no_path.fixture.v1.json` | INT03 exact fixture | fixture |
| `backend/tests/fixtures/cross_discipline/patch053.int04.hidden_hop.fixture.v1.json` | INT04 exact fixture | fixture |
| `backend/tests/fixtures/cross_discipline/patch053.int05.impact_handoff.fixture.v1.json` | INT05 exact fixture | fixture |
| `backend/tests/fixtures/cross_discipline/patch053.int06.no_auto_confirm.fixture.v1.json` | INT06 exact fixture | fixture |
| `backend/tests/fixtures/cross_discipline/patch053.rpt01.snapshot.fixture.v1.json` | RPT01 exact fixture | fixture |
| `backend/tests/fixtures/cross_discipline/patch053.rpt02.acceptance_race.fixture.v1.json` | RPT02 exact fixture | fixture |
| `backend/tests/fixtures/cross_discipline/patch053.rpt03.accepted_immutable.fixture.v1.json` | RPT03 exact fixture | fixture |
| `backend/tests/fixtures/cross_discipline/patch053.rpt04.authority.fixture.v1.json` | RPT04 exact fixture | fixture |
| `backend/tests/fixtures/cross_discipline/patch053.ai01.explain.fixture.v1.json` | AI01 exact fixture | fixture |
| `backend/tests/fixtures/cross_discipline/patch053.ai02.unavailable.fixture.v1.json` | AI02 exact fixture | fixture |
| `backend/tests/fixtures/cross_discipline/patch053.ai03.protected.fixture.v1.json` | AI03 exact fixture | fixture |
| `backend/tests/fixtures/cross_discipline/patch053.ai04.authority.fixture.v1.json` | AI04 exact fixture | fixture |
| `backend/tests/fixtures/cross_discipline/patch053.ai05.bounds.fixture.v1.json` | AI05 exact fixture | fixture |
| `backend/tests/fixtures/cross_discipline/patch053.ui01.matrix.fixture.v1.json` | UI01 exact fixture | fixture |
| `backend/tests/fixtures/cross_discipline/patch053.ui02.queue_detail.fixture.v1.json` | UI02 exact fixture | fixture |
| `backend/tests/fixtures/cross_discipline/patch053.ui03.indeterminate.fixture.v1.json` | UI03 exact fixture | fixture |
| `backend/tests/fixtures/cross_discipline/patch053.ui04.disposition_conflict.fixture.v1.json` | UI04 exact fixture | fixture |
| `backend/tests/fixtures/cross_discipline/patch053.ui05.project_switch.fixture.v1.json` | UI05 exact fixture | fixture |
| `backend/tests/fixtures/cross_discipline/patch053.ui06.accessibility_rtl.fixture.v1.json` | UI06 exact fixture | fixture |

No alternate migration, adapter, AI module, view, evidence document, test file,
fixture name, helper or generated source is implicit.

## C. Exact Modify Allow-List

Exactly 51 existing paths may receive only the stated Batch-5 semantic hunks.
Conditional authority permits omission, never speculative edits.

| Exact path | Exact Batch-5 purpose | Editing rule |
|---|---|---|
| `backend/app/schemas/cross_discipline_intelligence.py` | Add only accepted Impact, Potential Impact, Report projection and AI DTO/value contracts | hunk-only; preserve Batch-1–4 DTOs |
| `backend/app/models/cross_discipline_intelligence.py` | Map only durable handoff identities/result state and named coherence constraints | hunk-only; preserve retained schema semantics |
| `backend/app/ports/cross_discipline_intelligence.py` | Add only Project Control handoff/resolution, Report resolver and optional AI protocol seams | hunk-only |
| `backend/app/discipline_packages/cross_discipline/definitions/eic_v1.py` | Add the integrated interface/projection/rule declaration and final 96-vector release digest | hunk-only; retain all pair definitions |
| `backend/app/discipline_packages/cross_discipline/rules/eic_v1.py` | Add exactly `xdi.eic.explicit_change_path.v1` | hunk-only; no dynamic rule authority |
| `backend/app/discipline_packages/cross_discipline/evaluator.py` | Register/evaluate only the accepted integrated rule through the shared pipeline | hunk-only |
| `backend/app/discipline_packages/cross_discipline/conformance_manifest.py` | Add exactly the 21 remaining vector identities/digests and final 96 gate | hunk-only |
| `backend/app/discipline_packages/cross_discipline/conformance_harness.py` | Execute the 21 fixtures through real contracts | hunk-only |
| `backend/app/discipline_packages/readiness_052.py` | Replace only the three exact-live-head equality gates with one deterministic internal Alembic-lineage containment check that accepts `e05200000002` and known descendants while retaining every existing PATCH-052 table/function/source/descriptor/adapter/component/conformance check | hunk-only; no readiness redesign, lexical/numeric comparison, arbitrary-newer acceptance, repair, migration, or fail-open behavior |
| `backend/app/adapters/cross_discipline_sources.py` | Add authorization-first `xdi.proj.change_seed.v1` and integrated path source acquisition | hunk-only |
| `backend/app/repositories/cross_discipline_repository.py` | Add only durable intent/result lookup, lock and reconciliation operations; never commit | hunk-only |
| `backend/app/services/cross_discipline_service.py` | Integrated assessment, recoverable handoff, Report projection and bounded AI orchestration | hunk-only; three UoWs remain separate |
| `backend/app/dependencies/cross_discipline_intelligence.py` | Wire Project Control adapter and optional AI provider using existing patterns | hunk-only |
| `backend/app/api/v1/routers/cross_discipline_intelligence.py` | Complete only the accepted Impact, Report and AI operations within the 19-operation contract | hunk-only |
| `backend/app/core/config.py` | Add false-by-default PATCH-053 AI settings only | mandatory dirty-file hunk isolation |
| `backend/app/enums/technical_report.py` | Add only `CROSS_DISCIPLINE_ASSESSMENT` source/owner kind | hunk-only |
| `backend/app/models/technical_report.py` | Add only assessment provenance locator/source and owner-coherence constraints | hunk-only; accepted immutability unchanged |
| `backend/app/models/technical_report_command.py` | Add only `CrossDisciplineAssessmentHistoricalBasisV1` and canonical parsing | hunk-only |
| `backend/app/schemas/technical_report.py` | Add the corresponding strict closed basis schema/union | hunk-only |
| `backend/app/ports/technical_report.py` | Add only the authorized assessment resolver seam | hunk-only |
| `backend/app/repositories/technical_report_repository.py` | Encode/decode only the new historical-basis variant | hunk-only |
| `backend/app/repositories/technical_report_unit_of_work.py` | Recognize, route, resolve and validate only `CROSS_DISCIPLINE_ASSESSMENT` in the closed historical-source resolver while preserving existing sources | hunk-only; no resolver redesign, unrelated persistence change, accepted-byte mutation or authorization weakening |
| `backend/app/services/technical_report_service.py` | Freshly authorize/lock assessment, Findings and dispositions at authoring and acceptance | hunk-only; Human authority unchanged |
| `backend/app/api/v1/routers/technical_reports.py` | Additive DTO mapping/validation for the assessment basis only | hunk-only |
| `frontend/src/api/types.ts` | Add exact Impact, Report and AI presentation DTOs | mandatory dirty-file hunk isolation |
| `frontend/src/api/client.ts` | Add only the remaining accepted PATCH-053 operations | mandatory dirty-file hunk isolation |
| `frontend/src/components/CrossDisciplineIntelligencePanel.tsx` | Compose final integrated, Impact and AI surfaces with retained cancellation/state rules | hunk-only |
| `frontend/src/pages/ProjectsPage.tsx` | Minimal final panel state/selection integration if required | mandatory dirty-file hunk isolation |
| `frontend/src/styles.css` | Scoped `.cross-discipline-*` Impact/AI/accessibility/RTL/responsive additions only | mandatory dirty-file hunk isolation |
| `backend/tests/test_cross_discipline_service.py` | Integrated rule, projection, Report/AI orchestration and affected service regression | hunk-only |
| `backend/tests/test_cross_discipline_security.py` | Full owner intersection, protected equivalence, revocation and AI zero-call checks | hunk-only |
| `backend/tests/test_cross_discipline_concurrency.py` | Durable handoff arbitration, interruption and reconciliation races | hunk-only |
| `backend/tests/test_cross_discipline_api.py` | Complete all 19 operations and exact safe outcome contracts | hunk-only |
| `backend/tests/test_cross_discipline_migration.py` | Successor empty/populated upgrade, failure rollback, downgrade refusal and sole-head checks | hunk-only |
| `backend/tests/test_project_control_migration.py` | Update only the stale global Alembic sole-head expectation from `e05200000002` to `e05300000002`; preserve the Project Control revision/parent invariant unchanged | hunk-only; one literal global-head assertion update only |
| `backend/tests/test_customer_organization_migration.py` | Update only the stale global Alembic heads assertion and cleanup/current-revision guard from `e05200000002` to `e05300000002`; preserve every Customer/Organization historical, schema, ownership and data-preservation assertion unchanged | hunk-only; exactly two global-head literal updates only |
| `backend/tests/test_patch_052_batch_2.py` | Retain the existing line-204-only global-head bookkeeping authorization; add only Electrical readiness successor-compatibility coverage for equality/known-descendant acceptance and older/unknown/divergent fail-closed rejection, while preserving line 231's `e05200000002` equality/floor case and every package/schema assertion | hunk-only; line 204 remains one literal global-head update; line 231's historical/schema-era invariant must not be replaced or weakened |
| `backend/tests/test_patch_052_batch_3.py` | Add only Instrumentation readiness compatibility assertions for a legitimate current descendant of `e05200000002`; preserve every package, rule, schema, source and migration-era invariant | hunk-only; readiness compatibility assertions only |
| `backend/tests/test_patch_052_batch_4.py` | Add only Control Automation readiness compatibility assertions for a legitimate current descendant of `e05200000002`; preserve every package, rule, schema, source and migration-era invariant | hunk-only; readiness compatibility assertions only |
| `backend/tests/test_patch_052_migration.py` | Add only lifecycle/setup/teardown compatibility that enters the immutable PATCH-052 migration boundary from the current repository head, executes the existing historical assertions, and restores `TEST_DATABASE_REVISION` afterward | hunk-only; `PATCH_052_HEAD = "e05200000002"`, parentage, migration assertions, downgrade guards and retained-row/data-preservation semantics immutable |
| `backend/tests/test_execution_plan_migration.py` | Update only the stale repository-global Alembic sole-head expectation from `e05200000002` to `e05300000002`; preserve the Execution Plan revision/parent invariant unchanged | hunk-only; one literal global-head assertion update only |
| `backend/tests/test_engineering_deliverable_migration.py` | Update only the stale repository-global Alembic sole-head expectation from `e05200000002` to `e05300000002`; preserve the Engineering Deliverable revision/parent invariant and migration-source assertions unchanged | hunk-only; one literal global-head assertion update only |
| `backend/tests/test_onboarding_migration.py` | Update only the stale repository-global `script.get_heads()` expectation and `TEST_DATABASE_REVISION` bookkeeping literal from `e05200000002` to `e05300000002`; preserve the Onboarding revision/parent invariant and all schema/data semantics unchanged | hunk-only; exactly two literal global-head bookkeeping updates only |
| `backend/tests/test_organizational_memory_migration.py` | Update only the stale repository-global `TEST_DATABASE_REVISION` bookkeeping literal and `script.get_heads()` expectation from `e05200000002` to `e05300000002`; preserve the Organizational Memory revision/parent invariant and all schema/data semantics unchanged | hunk-only; exactly two literal global-head bookkeeping updates only |
| `backend/tests/test_project_foundation_migration.py` | Update only the stale repository-global `script.get_heads()` expectation and `TEST_DATABASE_REVISION` bookkeeping literal from `e05200000002` to `e05300000002`; preserve the Project Foundation revision/parent invariant and all schema/data semantics unchanged | hunk-only; exactly two literal global-head bookkeeping updates only |
| `backend/tests/test_supporting_file_migration.py` | Update only the stale repository-global `script.get_heads()` expectation and `TEST_DATABASE_REVISION` bookkeeping literal from `e05200000002` to `e05300000002`; preserve the Supporting File revision/parent invariant and all schema/data semantics unchanged | hunk-only; exactly two literal global-head bookkeeping updates only |
| `backend/tests/test_technical_report_migration.py` | Update only the stale repository-global `TEST_DATABASE_REVISION` bookkeeping literal and `script.get_heads()` expectation from `e05200000002` to `e05300000002`; preserve the Technical Report revision/parent invariant, downgrade behavior and all schema/data semantics unchanged | hunk-only; exactly two literal global-head bookkeeping updates only |
| `backend/tests/test_cross_discipline_database.py` | Handoff nullability/uniqueness/coherence and Report SQL acceptance/rejection | hunk-only |
| `backend/tests/test_cross_discipline_performance.py` | Final seven plans/resource budgets and full-scope timing evidence | hunk-only |
| `backend/tests/test_cross_discipline_conformance.py` | Exact 21-vector assertions and final cumulative `96/96` gate | hunk-only |
| `frontend/src/test/cross-discipline-intelligence.test.tsx` | UI01–UI06, all seven states, conflict, cancellation, accessibility and RTL | hunk-only |

The public Project Control service and its model/repository/UoW/router paths are
integration dependencies to execute unchanged. They are not modify-authorized.
Likewise, no package initializer, `backend/app/main.py`, Technical Report test,
or other adjacent path is authorized. A proven need is a stop condition.

Across the authorized handoff paths, eligible Finding presentation states are
exactly `open|acknowledged|disputed`; no confirmed-Finding prerequisite exists.
The required sequence is exactly: (1) a PATCH-053 UoW freshly authorizes,
locks, and commits a durable intent containing the `handoff_key`, stored Project
Control idempotency key and accepted correlation identity, without emitting
linkage success; (2) the adapter invokes the public Project Control service,
which freshly authorizes and commits its own canonical `potential` Impact,
idempotency, Audit and outbox UoW; and (3) a fresh PATCH-053 UoW reauthorizes,
rechecks and durably records the Impact ID/snapshot digest, one `confirm`
disposition, safe result, linkage Audit and outbox. Only the third commit permits
API success. Owner failure leaves truthful incomplete intent; owner success
followed by reconciliation failure returns
`unavailable/handoff_link_pending`; retry reuses the stored Project Control key
and resolves the same Impact; authorization revocation remains
`protected_not_found`. No Session, authorization decision, ORM object, or outer
transaction crosses an owner boundary.

## D. Exact Migration Allow-List

Exactly one future migration path is authorized:

`backend/migrations/versions/e05300000002_patch_053_prerequisite_completion.py`

Its revision is `e05300000002` and its sole `down_revision` must be
`e05300000001`. It may only:

- add nullable `handoff_key char(64)`, native-UUID
  `project_control_idempotency_key`, `project_control_correlation_id`, and
  `project_control_impact_id`, plus nullable
  `project_control_impact_snapshot_digest char(64)` to
  `cross_discipline_idempotency`;
- add `uq_xdi_idempotency_handoff_key`,
  `ck_xdi_idempotency_handoff_key_digest`,
  `ck_xdi_idempotency_impact_snapshot_digest`,
  `ck_xdi_idempotency_handoff_identity`, and
  `ck_xdi_idempotency_handoff_result`, preserving
  `ck_xdi_idempotency_completion`;
- add only the required Technical Report assessment provenance/source/locator
  and owner-coherence constraints; and
- add the closed cross-discipline assessment branch to
  `technical_report_historical_basis_valid(text,jsonb)` while retaining every
  existing basis branch and accepted-report immutability rule.

Migration `backend/migrations/versions/e05300000001_cross_discipline_kernel.py`
is immutable and forbidden to modify. There is no backfill, fabricated state,
history rewrite, second migration, unrelated index, cleanup or schema redesign.
The authorized successor is not created or executed by this manifest.

## E. Exact Test Allow-List

Exactly 25 test source paths are authorized: three creates and twenty-two hunk-only
modifications.

| Exact path | State | Authorized coverage |
|---|---|---|
| `backend/tests/test_cross_discipline_report.py` | create | RPT01–RPT04, historical projection, acceptance race, immutability and authority |
| `backend/tests/test_cross_discipline_ai.py` | create | AI01–AI05, disabled/protected/bounds, one call, zero retry and no authority |
| `backend/tests/test_cross_discipline_impact_handoff.py` | create | eligible states, three UoWs, owner failure, retry, interruption, revocation and duplicate arbitration |
| `backend/tests/test_cross_discipline_service.py` | modify | INT01–INT06 and integrated/Report/AI service regression |
| `backend/tests/test_cross_discipline_security.py` | modify | authorization intersection and nondisclosure across integrated/Impact/Report/AI |
| `backend/tests/test_cross_discipline_concurrency.py` | modify | handoff/reconciliation races, same/different duplicate and recovery |
| `backend/tests/test_cross_discipline_api.py` | modify | all 19 operation contracts and truthful pending/protected results |
| `backend/tests/test_cross_discipline_migration.py` | modify | successor lifecycle, rollback, downgrade/refusal and sole head |
| `backend/tests/test_project_control_migration.py` | modify | change only the expected global Alembic sole head from `e05200000002` to `e05300000002`; retain the Project Control revision `e04700000001` and parent `e04600000001` assertion exactly |
| `backend/tests/test_customer_organization_migration.py` | modify | change only the two global-head literals from `e05200000002` to `e05300000002`: the `script.get_heads()` assertion and cleanup/current-revision guard; retain all Customer/Organization parentage, schema, upgrade/downgrade, data and ownership assertions exactly |
| `backend/tests/test_patch_052_batch_2.py` | modify | retain the existing authorization to change only line 204's direct repository-global `alembic_version` literal from `e05200000002` to `e05300000002`; additionally authorize only Electrical readiness lineage coverage: positive `e05200000002`, `e05300000001`, `e05300000002`; negative `e05200000001`, unknown revision and divergent revision; preserve line 231's `e05200000002` equality/floor invariant rather than replacing it |
| `backend/tests/test_patch_052_batch_3.py` | modify | Instrumentation readiness only: prove a legitimate current descendant remains ready and reports the governed observed revision; no package/schema-era assertion change |
| `backend/tests/test_patch_052_batch_4.py` | modify | Control Automation readiness only: prove a legitimate current descendant remains ready and reports the governed observed revision; no package/schema-era assertion change |
| `backend/tests/test_patch_052_migration.py` | modify | lifecycle/setup/teardown only: preserve `PATCH_052_HEAD = "e05200000002"`, enter that historical boundary from the current head, run the existing PATCH-052 migration assertions, and restore `TEST_DATABASE_REVISION` in guaranteed teardown; no migration/history/downgrade/data assertion change |
| `backend/tests/test_execution_plan_migration.py` | modify | change only line 11's repository-global `script.get_heads()` literal from `e05200000002` to `e05300000002`; retain revision `e04500000001`, parent `e04400000001`, and every migration-source assertion exactly |
| `backend/tests/test_engineering_deliverable_migration.py` | modify | change only line 8's repository-global `script.get_heads()` literal from `e05200000002` to `e05300000002`; retain revision `e04600000001`, parent `e04500000001`, and every migration-source assertion exactly |
| `backend/tests/test_onboarding_migration.py` | modify | change only lines 11 and 13's repository-global `script.get_heads()` and `TEST_DATABASE_REVISION` literals from `e05200000002` to `e05300000002`; retain revision `e04100000001`, parent `e03800000001`, and all schema/data assertions exactly |
| `backend/tests/test_organizational_memory_migration.py` | modify | change only lines 45 and 46's repository-global `TEST_DATABASE_REVISION` and `script.get_heads()` literals from `e05200000002` to `e05300000002`; retain revision `e03800000001`, parent `e03400000001`, and all downgrade/schema/data assertions exactly |
| `backend/tests/test_project_foundation_migration.py` | modify | change only lines 17 and 19's repository-global `script.get_heads()` and `TEST_DATABASE_REVISION` literals from `e05200000002` to `e05300000002`; retain revision `e04400000001`, parent `e04300000001`, and all schema/data assertions exactly |
| `backend/tests/test_supporting_file_migration.py` | modify | change only lines 10 and 12's repository-global `script.get_heads()` and `TEST_DATABASE_REVISION` literals from `e05200000002` to `e05300000002`; retain revision `e04300000001`, parent `e04100000001`, and all schema/data assertions exactly |
| `backend/tests/test_technical_report_migration.py` | modify | change only lines 25 and 26's repository-global `TEST_DATABASE_REVISION` and `script.get_heads()` literals from `e05200000002` to `e05300000002`; retain revision `e03400000001`, parent `e03200000001`, and all downgrade/schema/data assertions exactly |
| `backend/tests/test_cross_discipline_database.py` | modify | exact new constraints and Report historical-basis SQL validation |
| `backend/tests/test_cross_discipline_performance.py` | modify | seven query plans, resource ceilings and final budgets |
| `backend/tests/test_cross_discipline_conformance.py` | modify | remaining 21 and cumulative 96-vector gate |
| `frontend/src/test/cross-discipline-intelligence.test.tsx` | modify | UI01–UI06 and full frontend regression states |

For each historical-capability migration test listed above, authority is limited
to the enumerated literal repository-global head bookkeeping replacements. No
test name, neighboring assertion, migration-under-test identity or parentage,
downgrade target/behavior, schema/data expectation, cleanup operation, or other
line is authorized. All other Technical Report, Batch-1–4, package,
Project/Workspace, Object/Relationship, Context/Commitment, Evidence, Audit and
frontend tests may be executed unchanged for affected regression evidence but
may not be modified or staged under this manifest.

The PATCH-052 readiness compatibility authority is equally hunk-limited. The
production hunk may only replace the three exact-head gates with source-graph
ancestry containment and must combine that result with all retained capability
checks. Tests may prove only the enumerated lineage outcomes and historical-test
lifecycle restoration. They may not change `PATCH_052_HEAD`, accept a revision
by lexical/numeric ordering, synthesize migration history, weaken downgrade or
retained-row guards, or redesign PATCH-052 readiness.

## F. Exact Fixture Allow-List

Exactly 21 fixtures may be created, with no rename or substitute:

1. `backend/tests/fixtures/cross_discipline/patch053.int01.change_path.fixture.v1.json`
2. `backend/tests/fixtures/cross_discipline/patch053.int02.no_change.fixture.v1.json`
3. `backend/tests/fixtures/cross_discipline/patch053.int03.no_path.fixture.v1.json`
4. `backend/tests/fixtures/cross_discipline/patch053.int04.hidden_hop.fixture.v1.json`
5. `backend/tests/fixtures/cross_discipline/patch053.int05.impact_handoff.fixture.v1.json`
6. `backend/tests/fixtures/cross_discipline/patch053.int06.no_auto_confirm.fixture.v1.json`
7. `backend/tests/fixtures/cross_discipline/patch053.rpt01.snapshot.fixture.v1.json`
8. `backend/tests/fixtures/cross_discipline/patch053.rpt02.acceptance_race.fixture.v1.json`
9. `backend/tests/fixtures/cross_discipline/patch053.rpt03.accepted_immutable.fixture.v1.json`
10. `backend/tests/fixtures/cross_discipline/patch053.rpt04.authority.fixture.v1.json`
11. `backend/tests/fixtures/cross_discipline/patch053.ai01.explain.fixture.v1.json`
12. `backend/tests/fixtures/cross_discipline/patch053.ai02.unavailable.fixture.v1.json`
13. `backend/tests/fixtures/cross_discipline/patch053.ai03.protected.fixture.v1.json`
14. `backend/tests/fixtures/cross_discipline/patch053.ai04.authority.fixture.v1.json`
15. `backend/tests/fixtures/cross_discipline/patch053.ai05.bounds.fixture.v1.json`
16. `backend/tests/fixtures/cross_discipline/patch053.ui01.matrix.fixture.v1.json`
17. `backend/tests/fixtures/cross_discipline/patch053.ui02.queue_detail.fixture.v1.json`
18. `backend/tests/fixtures/cross_discipline/patch053.ui03.indeterminate.fixture.v1.json`
19. `backend/tests/fixtures/cross_discipline/patch053.ui04.disposition_conflict.fixture.v1.json`
20. `backend/tests/fixtures/cross_discipline/patch053.ui05.project_switch.fixture.v1.json`
21. `backend/tests/fixtures/cross_discipline/patch053.ui06.accessibility_rtl.fixture.v1.json`

The existing 75 fixtures, including DB04–DB06, are read-only inputs to the
cumulative gate. Final acceptance requires exact `96/96`; count-only or mock
success is forbidden.

## G. Exact Frontend Allow-List

Exactly seven frontend production paths are authorized: two creates and five
modifications.

| Exact path | State | Boundary |
|---|---|---|
| `frontend/src/components/crossDiscipline/CrossDisciplinePotentialImpactView.tsx` | create | pending/reconciled advisory Impact only; no optimistic success |
| `frontend/src/components/crossDiscipline/CrossDisciplineAIExplanation.tsx` | create | explicitly labeled non-authoritative AI result only |
| `frontend/src/api/types.ts` | modify / dirty shared | exact accepted Impact, Report and AI DTOs only |
| `frontend/src/api/client.ts` | modify / dirty shared | remaining accepted PATCH-053 calls only |
| `frontend/src/components/CrossDisciplineIntelligencePanel.tsx` | modify | compose final surfaces; preserve cancellation and protected clearing |
| `frontend/src/pages/ProjectsPage.tsx` | modify / dirty shared / conditional | minimal final panel state/selection integration |
| `frontend/src/styles.css` | modify / dirty shared / conditional | scoped Impact/AI/accessibility/RTL/responsive styles |

Existing overview, queue, detail, provenance, disposition, history, comparison,
commitment and dependency components are executed unchanged. The frontend test
path is governed by §E and excluded from the production count.

## H. Shared Dirty File Contract

Exactly five currently dirty paths intersect this maximum boundary:

| Exact path | Permitted Batch-5 hunk | Mandatory protection |
|---|---|---|
| `backend/app/core/config.py` | false-by-default PATCH-053 AI settings | preserve unrelated Guidance settings unstaged |
| `frontend/src/api/types.ts` | additive Impact/Report/AI DTO types | preserve unrelated PATCH-050 Guidance types unstaged |
| `frontend/src/api/client.ts` | additive PATCH-053 operations | preserve unrelated Guidance client changes unstaged |
| `frontend/src/pages/ProjectsPage.tsx` | minimal final panel integration | preserve unrelated Guidance UI integration unstaged |
| `frontend/src/styles.css` | scoped `.cross-discipline-*` additions | preserve unrelated `.engineering-guidance*` changes unstaged |

Record pre-edit hashes/patches for all five paths. Stage only accepted Batch-5
hunks interactively and verify both cached and remaining unstaged diffs. Every
other dirty or untracked path is outside this manifest and must remain unchanged
and unstaged. Any future unrelated change to another authorized path makes that
path mandatory hunk-only as well.

## I. Forbidden Scope

The allow-lists are closed. Batch 5 explicitly forbids:

- modifying `e05300000001`, rewriting migration history, creating a second
  successor, backfilling/fabricating handoff or Report state, or unrelated
  schema/index cleanup;
- modifying ADR-026, Architecture-053, EDS-053, IDS-053,
  Implementation-Plan-053, prior manifests/evidence, or any governance document
  except the two exact new Batch-5 evidence paths;
- modifying Project Control owner model/repository/UoW/service/router behavior;
- a confirmed-Finding prerequisite, a cross-owner outer transaction, premature
  linkage/API success, new Impact owner, or automatic Impact confirmation;
- redesigning Technical Report, weakening ADR-023/Human acceptance, changing
  accepted bytes, live reinterpretation of accepted basis, or bypassing the
  assessment/Finding/disposition authorization intersection;
- AI creation/resolution of Findings, dispositions or canonical Impact state;
  AI source/accepted-Report mutation; autonomous loops; more than 20 Findings;
  more than 65,536 input bytes; more than one provider call; or any retry;
- changing Batch-1 shared kernel/persistence, Batch-2 E↔I, Batch-3 I↔C, Batch-4
  E↔C, machine identities, occurrence identity, Finding fingerprints,
  recurrence, history/replay/reassessment, source ownership, Human authority,
  authorization/nondisclosure, Audit/outbox or idempotency semantics;
- PATCH-054+, standards work, procurement, maintenance, future disciplines,
  FAT/SAT, commissioning, punch, or unrelated architectural cleanup; and
- every path not written literally in §§B–G.

No wildcard, directory grant, alternate file or adjacent-path authority is
implicit.

## J. Delivery Staging Contract

A later separately authorized delivery must:

1. stage only literal paths from §§B–G;
2. use hunk-level staging for every modified/shared path and especially §H;
3. stage the migration only at its one exact path and verify revision/parent;
4. never use `git add .` or `git add -A`;
5. inspect `git diff --cached --name-status`, the complete cached diff, and
   `git diff --cached --check`;
6. prove every staged semantic hunk against this manifest;
7. prove the 21 fixture identities and cumulative 96-vector set exactly; and
8. preserve all unrelated dirty/untracked work unstaged.

Conditional paths may be omitted. No unlisted path or whole unrelated existing
hunk may be staged.

## K. Delivery Commit Contract

This manifest grants no commit or push authority. A later single governed local
PATCH-053 delivery commit may occur only after separate Human implementation and
delivery authority; Batch-5 implementation/evidence/review; INT01–INT06,
RPT01–RPT04, AI01–AI05 and UI01–UI06 `21/21`; cumulative `96/96`; real
PostgreSQL migration/database evidence; security, concurrency, history,
performance, frontend, typecheck/build/static and full affected regressions;
Critical/Major `0/0`; all five Human batch acceptances; QG-11 and QG-12. Prior
batch commits must not be amended. Push and PATCH closure remain separately
authorized operations.

## L. Exact Path Count Summary

Counts use unique literal paths. Category counts intentionally overlap the
create/modify totals.

| Category | Exact count |
|---|---:|
| Permitted create paths | 32 |
| Permitted modify paths | 51 |
| Permitted migration paths | 1 |
| Permitted test source paths | 25 |
| Permitted fixture paths | 21 |
| Permitted backend production paths | 26 |
| Permitted frontend production paths | 7 |
| Permitted total production paths | 33 |
| Currently dirty shared hunk-only paths | 5 |
| Closed delivery universe | 83 |

## M. Capability-to-Path Matrix

| Capability | Exact implementation paths | Exact validation/presentation paths |
|---|---|---|
| Integrated E+I+C rule/interface/path/change projection | `backend/app/discipline_packages/cross_discipline/definitions/eic_v1.py`; `backend/app/discipline_packages/cross_discipline/rules/eic_v1.py`; `backend/app/discipline_packages/cross_discipline/evaluator.py`; `backend/app/adapters/cross_discipline_sources.py`; `backend/app/services/cross_discipline_service.py` | `backend/tests/test_cross_discipline_service.py`; `backend/tests/test_cross_discipline_security.py`; `backend/tests/test_cross_discipline_conformance.py` |
| Final conformance release | `backend/app/discipline_packages/cross_discipline/conformance_manifest.py`; `backend/app/discipline_packages/cross_discipline/conformance_harness.py`; `backend/app/discipline_packages/cross_discipline/definitions/eic_v1.py` | `backend/tests/test_cross_discipline_conformance.py`; `docs/implementation/PATCH-053-Batch-5-Implementation-Evidence.md` |
| Durable Change Impact handoff | `backend/app/models/cross_discipline_intelligence.py`; `backend/app/schemas/cross_discipline_intelligence.py`; `backend/app/ports/cross_discipline_intelligence.py`; `backend/app/adapters/cross_discipline_change_impact.py`; `backend/app/repositories/cross_discipline_repository.py`; `backend/app/services/cross_discipline_service.py`; `backend/app/dependencies/cross_discipline_intelligence.py`; `backend/app/api/v1/routers/cross_discipline_intelligence.py` | `backend/tests/test_cross_discipline_impact_handoff.py`; `backend/tests/test_cross_discipline_concurrency.py`; `backend/tests/test_cross_discipline_api.py`; `backend/tests/test_cross_discipline_security.py`; `frontend/src/components/crossDiscipline/CrossDisciplinePotentialImpactView.tsx` |
| Project Control integration | `backend/app/adapters/cross_discipline_change_impact.py`; `backend/app/ports/cross_discipline_intelligence.py`; `backend/app/dependencies/cross_discipline_intelligence.py`; `backend/app/services/cross_discipline_service.py` | `backend/tests/test_cross_discipline_impact_handoff.py`; `backend/tests/test_cross_discipline_concurrency.py`; `backend/tests/test_cross_discipline_security.py`; `backend/tests/test_project_control_migration.py` (global-head freshness hunk only) |
| Customer/Organization migration regression | No Batch-5 production or historical-migration edit; retained Customer/Organization behavior only | `backend/tests/test_customer_organization_migration.py` (exactly two global-head freshness hunks only) |
| PATCH-052 shared-schema current-head bookkeeping | No PATCH-052 migration or schema edit; retained package/schema behavior only | `backend/tests/test_patch_052_batch_2.py` line 204 (the previously authorized direct global-head freshness hunk only); the separately authorized readiness compatibility hunks are mapped in the next row |
| PATCH-052 readiness successor compatibility | `backend/app/discipline_packages/readiness_052.py` (three gates to one deterministic `e05200000002` ancestry-containment rule only; every capability check retained) | `backend/tests/test_patch_052_batch_2.py` (existing line-204 authority plus enumerated Electrical lineage cases; line 231 floor case preserved); `backend/tests/test_patch_052_batch_3.py` (Instrumentation descendant case only); `backend/tests/test_patch_052_batch_4.py` (Control Automation descendant case only) |
| PATCH-052 historical migration lifecycle under a successor head | No production or migration edit; immutable PATCH-052 boundary exercised from and restored to the current repository head | `backend/tests/test_patch_052_migration.py` (setup/teardown lifecycle compatibility only; `PATCH_052_HEAD`, parentage, downgrade and retained-row/data assertions immutable) |
| Historical-capability migration regression | No Batch-5 production or historical-migration edit; retained Execution Plan, Engineering Deliverable, Onboarding, Organizational Memory, Project Foundation, Supporting File and Technical Report behavior only | `backend/tests/test_execution_plan_migration.py` (one global-head freshness hunk only); `backend/tests/test_engineering_deliverable_migration.py` (one global-head freshness hunk only); `backend/tests/test_onboarding_migration.py` (exactly two global-head bookkeeping hunks only); `backend/tests/test_organizational_memory_migration.py` (exactly two global-head bookkeeping hunks only); `backend/tests/test_project_foundation_migration.py` (exactly two global-head bookkeeping hunks only); `backend/tests/test_supporting_file_migration.py` (exactly two global-head bookkeeping hunks only); `backend/tests/test_technical_report_migration.py` (exactly two global-head bookkeeping hunks only) |
| Technical Report advisory historical basis | `backend/app/enums/technical_report.py`; `backend/app/models/technical_report.py`; `backend/app/models/technical_report_command.py`; `backend/app/schemas/technical_report.py`; `backend/app/ports/technical_report.py`; `backend/app/repositories/technical_report_repository.py`; `backend/app/repositories/technical_report_unit_of_work.py`; `backend/app/services/technical_report_service.py`; `backend/app/api/v1/routers/technical_reports.py`; `backend/app/schemas/cross_discipline_intelligence.py`; `backend/app/ports/cross_discipline_intelligence.py`; `backend/app/services/cross_discipline_service.py` | `backend/tests/test_cross_discipline_report.py`; `backend/tests/test_cross_discipline_database.py`; `backend/tests/test_cross_discipline_migration.py` |
| Optional AI explain/summarize/draft-next-action | `backend/app/schemas/cross_discipline_intelligence.py`; `backend/app/ports/cross_discipline_intelligence.py`; `backend/app/ai/cross_discipline_intelligence.py`; `backend/app/services/cross_discipline_service.py`; `backend/app/dependencies/cross_discipline_intelligence.py`; `backend/app/api/v1/routers/cross_discipline_intelligence.py`; `backend/app/core/config.py` | `backend/tests/test_cross_discipline_ai.py`; `backend/tests/test_cross_discipline_api.py`; `backend/tests/test_cross_discipline_security.py`; `frontend/src/components/crossDiscipline/CrossDisciplineAIExplanation.tsx` |
| Final frontend | `frontend/src/api/types.ts`; `frontend/src/api/client.ts`; `frontend/src/components/CrossDisciplineIntelligencePanel.tsx`; `frontend/src/components/crossDiscipline/CrossDisciplinePotentialImpactView.tsx`; `frontend/src/components/crossDiscipline/CrossDisciplineAIExplanation.tsx`; `frontend/src/pages/ProjectsPage.tsx`; `frontend/src/styles.css` | `frontend/src/test/cross-discipline-intelligence.test.tsx` |
| Migration/database | `backend/migrations/versions/e05300000002_patch_053_prerequisite_completion.py`; `backend/app/models/cross_discipline_intelligence.py`; `backend/app/models/technical_report.py`; `backend/app/discipline_packages/readiness_052.py` (read-only lineage containment only) | `backend/tests/test_cross_discipline_migration.py`; `backend/tests/test_project_control_migration.py` (global-head freshness hunk only); `backend/tests/test_customer_organization_migration.py` (exactly two global-head freshness hunks only); `backend/tests/test_patch_052_batch_2.py` (line 204 plus enumerated readiness lineage hunks only); `backend/tests/test_patch_052_batch_3.py` and `backend/tests/test_patch_052_batch_4.py` (descendant readiness only); `backend/tests/test_patch_052_migration.py` (historical lifecycle setup/teardown only); `backend/tests/test_execution_plan_migration.py`; `backend/tests/test_engineering_deliverable_migration.py`; `backend/tests/test_onboarding_migration.py`; `backend/tests/test_organizational_memory_migration.py`; `backend/tests/test_project_foundation_migration.py`; `backend/tests/test_supporting_file_migration.py`; `backend/tests/test_technical_report_migration.py` (all seven preceding historical-capability paths: enumerated global-head bookkeeping hunks only); `backend/tests/test_cross_discipline_database.py`; `docs/implementation/PATCH-053-Batch-5-Implementation-Evidence.md` |
| Security/concurrency/performance/release evidence | `backend/app/services/cross_discipline_service.py`; `backend/app/repositories/cross_discipline_repository.py`; `backend/app/api/v1/routers/cross_discipline_intelligence.py` | `backend/tests/test_cross_discipline_security.py`; `backend/tests/test_cross_discipline_concurrency.py`; `backend/tests/test_cross_discipline_performance.py`; `docs/implementation/PATCH-053-Batch-5-Performance-Evidence.md`; `docs/implementation/PATCH-053-Batch-5-Implementation-Evidence.md` |

## N. Vector-to-Path Matrix

Every vector uses its exact fixture in §F plus
`backend/app/discipline_packages/cross_discipline/conformance_manifest.py`,
`backend/app/discipline_packages/cross_discipline/conformance_harness.py`, and
`backend/tests/test_cross_discipline_conformance.py`. Additional literal paths
are mapped below.

| Vector | Exact additional implementation/test/frontend paths | Exact fixture path |
|---|---|---|
| `patch053.int01.change_path` | `backend/app/discipline_packages/cross_discipline/definitions/eic_v1.py`; `backend/app/discipline_packages/cross_discipline/rules/eic_v1.py`; `backend/app/discipline_packages/cross_discipline/evaluator.py`; `backend/app/adapters/cross_discipline_sources.py`; `backend/app/services/cross_discipline_service.py`; `backend/tests/test_cross_discipline_service.py` | `backend/tests/fixtures/cross_discipline/patch053.int01.change_path.fixture.v1.json` |
| `patch053.int02.no_change` | `backend/app/schemas/cross_discipline_intelligence.py`; `backend/app/services/cross_discipline_service.py`; `backend/app/api/v1/routers/cross_discipline_intelligence.py`; `backend/tests/test_cross_discipline_service.py`; `backend/tests/test_cross_discipline_api.py` | `backend/tests/fixtures/cross_discipline/patch053.int02.no_change.fixture.v1.json` |
| `patch053.int03.no_path` | `backend/app/discipline_packages/cross_discipline/rules/eic_v1.py`; `backend/app/discipline_packages/cross_discipline/evaluator.py`; `backend/app/adapters/cross_discipline_sources.py`; `backend/app/services/cross_discipline_service.py`; `backend/tests/test_cross_discipline_service.py` | `backend/tests/fixtures/cross_discipline/patch053.int03.no_path.fixture.v1.json` |
| `patch053.int04.hidden_hop` | `backend/app/adapters/cross_discipline_sources.py`; `backend/app/services/cross_discipline_service.py`; `backend/tests/test_cross_discipline_security.py`; `frontend/src/components/CrossDisciplineIntelligencePanel.tsx` | `backend/tests/fixtures/cross_discipline/patch053.int04.hidden_hop.fixture.v1.json` |
| `patch053.int05.impact_handoff` | `backend/app/models/cross_discipline_intelligence.py`; `backend/app/schemas/cross_discipline_intelligence.py`; `backend/app/ports/cross_discipline_intelligence.py`; `backend/app/adapters/cross_discipline_change_impact.py`; `backend/app/repositories/cross_discipline_repository.py`; `backend/app/services/cross_discipline_service.py`; `backend/tests/test_cross_discipline_impact_handoff.py`; `backend/tests/test_cross_discipline_concurrency.py`; `frontend/src/components/crossDiscipline/CrossDisciplinePotentialImpactView.tsx` | `backend/tests/fixtures/cross_discipline/patch053.int05.impact_handoff.fixture.v1.json` |
| `patch053.int06.no_auto_confirm` | `backend/app/adapters/cross_discipline_change_impact.py`; `backend/app/services/cross_discipline_service.py`; `backend/tests/test_cross_discipline_impact_handoff.py`; `frontend/src/components/crossDiscipline/CrossDisciplinePotentialImpactView.tsx` | `backend/tests/fixtures/cross_discipline/patch053.int06.no_auto_confirm.fixture.v1.json` |
| `patch053.rpt01.snapshot` | `backend/app/models/technical_report_command.py`; `backend/app/schemas/technical_report.py`; `backend/app/ports/technical_report.py`; `backend/app/repositories/technical_report_repository.py`; `backend/app/repositories/technical_report_unit_of_work.py`; `backend/app/services/technical_report_service.py`; `backend/tests/test_cross_discipline_report.py` | `backend/tests/fixtures/cross_discipline/patch053.rpt01.snapshot.fixture.v1.json` |
| `patch053.rpt02.acceptance_race` | `backend/app/repositories/technical_report_unit_of_work.py`; `backend/app/services/technical_report_service.py`; `backend/app/api/v1/routers/technical_reports.py`; `backend/tests/test_cross_discipline_report.py`; `backend/tests/test_cross_discipline_concurrency.py` | `backend/tests/fixtures/cross_discipline/patch053.rpt02.acceptance_race.fixture.v1.json` |
| `patch053.rpt03.accepted_immutable` | `backend/app/models/technical_report.py`; `backend/app/repositories/technical_report_repository.py`; `backend/app/services/technical_report_service.py`; `backend/tests/test_cross_discipline_report.py`; `backend/tests/test_cross_discipline_database.py` | `backend/tests/fixtures/cross_discipline/patch053.rpt03.accepted_immutable.fixture.v1.json` |
| `patch053.rpt04.authority` | `backend/app/schemas/cross_discipline_intelligence.py`; `backend/app/repositories/technical_report_unit_of_work.py`; `backend/app/services/cross_discipline_service.py`; `backend/app/services/technical_report_service.py`; `backend/tests/test_cross_discipline_report.py` | `backend/tests/fixtures/cross_discipline/patch053.rpt04.authority.fixture.v1.json` |
| `patch053.ai01.explain` | `backend/app/ports/cross_discipline_intelligence.py`; `backend/app/ai/cross_discipline_intelligence.py`; `backend/app/services/cross_discipline_service.py`; `backend/app/api/v1/routers/cross_discipline_intelligence.py`; `backend/tests/test_cross_discipline_ai.py`; `frontend/src/components/crossDiscipline/CrossDisciplineAIExplanation.tsx` | `backend/tests/fixtures/cross_discipline/patch053.ai01.explain.fixture.v1.json` |
| `patch053.ai02.unavailable` | `backend/app/core/config.py`; `backend/app/dependencies/cross_discipline_intelligence.py`; `backend/app/ai/cross_discipline_intelligence.py`; `backend/tests/test_cross_discipline_ai.py`; `frontend/src/components/crossDiscipline/CrossDisciplineAIExplanation.tsx` | `backend/tests/fixtures/cross_discipline/patch053.ai02.unavailable.fixture.v1.json` |
| `patch053.ai03.protected` | `backend/app/services/cross_discipline_service.py`; `backend/app/api/v1/routers/cross_discipline_intelligence.py`; `backend/tests/test_cross_discipline_ai.py`; `backend/tests/test_cross_discipline_security.py` | `backend/tests/fixtures/cross_discipline/patch053.ai03.protected.fixture.v1.json` |
| `patch053.ai04.authority` | `backend/app/schemas/cross_discipline_intelligence.py`; `backend/app/ai/cross_discipline_intelligence.py`; `backend/app/services/cross_discipline_service.py`; `backend/tests/test_cross_discipline_ai.py` | `backend/tests/fixtures/cross_discipline/patch053.ai04.authority.fixture.v1.json` |
| `patch053.ai05.bounds` | `backend/app/schemas/cross_discipline_intelligence.py`; `backend/app/ai/cross_discipline_intelligence.py`; `backend/app/services/cross_discipline_service.py`; `backend/tests/test_cross_discipline_ai.py`; `backend/tests/test_cross_discipline_performance.py` | `backend/tests/fixtures/cross_discipline/patch053.ai05.bounds.fixture.v1.json` |
| `patch053.ui01.matrix` | `frontend/src/api/types.ts`; `frontend/src/api/client.ts`; `frontend/src/components/CrossDisciplineIntelligencePanel.tsx`; `frontend/src/test/cross-discipline-intelligence.test.tsx` | `backend/tests/fixtures/cross_discipline/patch053.ui01.matrix.fixture.v1.json` |
| `patch053.ui02.queue_detail` | `frontend/src/api/types.ts`; `frontend/src/api/client.ts`; `frontend/src/components/CrossDisciplineIntelligencePanel.tsx`; `frontend/src/test/cross-discipline-intelligence.test.tsx` | `backend/tests/fixtures/cross_discipline/patch053.ui02.queue_detail.fixture.v1.json` |
| `patch053.ui03.indeterminate` | `frontend/src/api/types.ts`; `frontend/src/components/CrossDisciplineIntelligencePanel.tsx`; `frontend/src/components/crossDiscipline/CrossDisciplinePotentialImpactView.tsx`; `frontend/src/components/crossDiscipline/CrossDisciplineAIExplanation.tsx`; `frontend/src/test/cross-discipline-intelligence.test.tsx` | `backend/tests/fixtures/cross_discipline/patch053.ui03.indeterminate.fixture.v1.json` |
| `patch053.ui04.disposition_conflict` | `frontend/src/api/client.ts`; `frontend/src/components/CrossDisciplineIntelligencePanel.tsx`; `frontend/src/components/crossDiscipline/CrossDisciplinePotentialImpactView.tsx`; `frontend/src/test/cross-discipline-intelligence.test.tsx` | `backend/tests/fixtures/cross_discipline/patch053.ui04.disposition_conflict.fixture.v1.json` |
| `patch053.ui05.project_switch` | `frontend/src/components/CrossDisciplineIntelligencePanel.tsx`; `frontend/src/pages/ProjectsPage.tsx`; `frontend/src/test/cross-discipline-intelligence.test.tsx` | `backend/tests/fixtures/cross_discipline/patch053.ui05.project_switch.fixture.v1.json` |
| `patch053.ui06.accessibility_rtl` | `frontend/src/components/crossDiscipline/CrossDisciplinePotentialImpactView.tsx`; `frontend/src/components/crossDiscipline/CrossDisciplineAIExplanation.tsx`; `frontend/src/styles.css`; `frontend/src/test/cross-discipline-intelligence.test.tsx` | `backend/tests/fixtures/cross_discipline/patch053.ui06.accessibility_rtl.fixture.v1.json` |

## O. Migration-to-Requirement Matrix

The sole migration implementation path for every row is
`backend/migrations/versions/e05300000002_patch_053_prerequisite_completion.py`.
No row authorizes another migration.

| Requirement | Exact model/service dependency | Exact validation/evidence path |
|---|---|---|
| Empty-database full-chain upgrade | `backend/app/models/cross_discipline_intelligence.py`; `backend/app/models/technical_report.py` | `backend/tests/test_cross_discipline_migration.py`; `docs/implementation/PATCH-053-Batch-5-Implementation-Evidence.md` |
| Populated upgrade from `e05300000001` | retained Batch-1–4 model/data contract | `backend/tests/test_cross_discipline_migration.py`; `backend/tests/test_cross_discipline_database.py` |
| Batch-1–4 retained data/bytes/behavior | `backend/app/models/cross_discipline_intelligence.py`; `backend/app/discipline_packages/cross_discipline/definitions/eic_v1.py` | `backend/tests/test_cross_discipline_migration.py`; `backend/tests/test_cross_discipline_conformance.py` |
| Zero destructive/fabricated backfill | successor migration only | `backend/tests/test_cross_discipline_migration.py` |
| Nullable `handoff_key` | `backend/app/models/cross_discipline_intelligence.py` | `backend/tests/test_cross_discipline_database.py` |
| Unique handoff arbiter and digest shape | `backend/app/models/cross_discipline_intelligence.py`; `backend/app/repositories/cross_discipline_repository.py` | `backend/tests/test_cross_discipline_database.py`; `backend/tests/test_cross_discipline_concurrency.py` |
| Project Control idempotency/correlation persistence | `backend/app/models/cross_discipline_intelligence.py`; `backend/app/adapters/cross_discipline_change_impact.py` | `backend/tests/test_cross_discipline_database.py`; `backend/tests/test_cross_discipline_impact_handoff.py` |
| Impact result/reference coherence | `backend/app/models/cross_discipline_intelligence.py`; `backend/app/repositories/cross_discipline_repository.py` | `backend/tests/test_cross_discipline_database.py`; `backend/tests/test_cross_discipline_impact_handoff.py` |
| Technical Report assessment-basis acceptance | `backend/app/models/technical_report.py`; `backend/app/models/technical_report_command.py`; `backend/app/schemas/technical_report.py`; `backend/app/repositories/technical_report_unit_of_work.py` | `backend/tests/test_cross_discipline_database.py`; `backend/tests/test_cross_discipline_report.py` |
| Technical Report invalid-basis rejection and existing-basis regression | `backend/app/models/technical_report.py`; `backend/app/repositories/technical_report_repository.py`; `backend/app/repositories/technical_report_unit_of_work.py` | `backend/tests/test_cross_discipline_database.py`; `backend/tests/test_cross_discipline_report.py` |
| Injected migration failure rollback | successor migration only | `backend/tests/test_cross_discipline_migration.py` |
| Sole-head validation | revision `e05300000002`, parent `e05300000001`; all historical migration identities, parentage, downgrade semantics and schema/data invariants retained | `backend/tests/test_cross_discipline_migration.py`; `backend/tests/test_project_control_migration.py` (one global-head freshness hunk only); `backend/tests/test_customer_organization_migration.py` (exactly two global-head freshness hunks only); `backend/tests/test_patch_052_batch_2.py` line 204 (one global-head freshness hunk only; line 231 remains the separately preserved floor case); `backend/tests/test_execution_plan_migration.py` (one global-head freshness hunk only); `backend/tests/test_engineering_deliverable_migration.py` (one global-head freshness hunk only); `backend/tests/test_onboarding_migration.py`; `backend/tests/test_organizational_memory_migration.py`; `backend/tests/test_project_foundation_migration.py`; `backend/tests/test_supporting_file_migration.py`; `backend/tests/test_technical_report_migration.py` (all five preceding paths: exactly two global-head bookkeeping hunks only); `docs/implementation/PATCH-053-Batch-5-Implementation-Evidence.md` |
| PATCH-052 capability floor at current head | observed revision is `e05200000002` or a known Alembic descendant containing it in source-graph ancestry; required PATCH-052 tables/functions/artifacts still independently validate; all resolution errors fail closed | `backend/app/discipline_packages/readiness_052.py`; `backend/tests/test_patch_052_batch_2.py`; `backend/tests/test_patch_052_batch_3.py`; `backend/tests/test_patch_052_batch_4.py` |
| PATCH-052 historical migration test lifecycle | `PATCH_052_HEAD = "e05200000002"` and all migration files/parentage remain immutable; test-only setup enters the boundary and guaranteed teardown restores `TEST_DATABASE_REVISION` | `backend/tests/test_patch_052_migration.py` |
| Safe downgrade refusal with retained handoff or assessment Report basis | `backend/app/models/cross_discipline_intelligence.py`; `backend/app/models/technical_report.py` | `backend/tests/test_cross_discipline_migration.py`; `backend/tests/test_cross_discipline_database.py` |
| Empty-footprint safe downgrade to `e05300000001` | successor migration only | `backend/tests/test_cross_discipline_migration.py` |
| Real PostgreSQL evidence | `backend/app/models/cross_discipline_intelligence.py`; `backend/app/models/technical_report.py`; `backend/app/repositories/cross_discipline_repository.py`; `backend/app/repositories/technical_report_repository.py` | `backend/tests/test_cross_discipline_migration.py`; `backend/tests/test_cross_discipline_database.py`; `docs/implementation/PATCH-053-Batch-5-Implementation-Evidence.md` |

## Independent Manifest Review

The fresh review challenged path breadth and completeness, speculative helpers,
all 21 vector identities/mappings, integrated machine identities, migration
scope/parent/validation/downgrade, historical rewrite, durable handoff state,
Project Control ownership, cross-owner transaction collapse, false success,
Report and AI authority, Batch-1–4 compatibility, dirty-file isolation and
PATCH-054+ leakage.

Result after the narrow resolver-path reconciliation: **PASS**.
Critical/Major/Minor/Observation: `0/0/0/0`. The added authority is limited to
the `CROSS_DISCIPLINE_ASSESSMENT` admission, routing, resolution, fallback and
validation hunks in the existing closed resolver; it grants no resolver redesign,
Report-authority change, accepted-byte mutation, or unrelated persistence work.
No unresolved manifest-path blocker remains. Batch-5 implementation remains
paused pending Human re-acceptance of this reconciliation; its separate
implementation authority is already granted, and PATCH-053 remains open.

The fresh Project Control regression-path reconciliation review separately
challenged whether the newly authorized test hunk could conceal a Project
Control migration defect. It cannot: the hunk may change only the global-head
literal `e05200000002` to the authoritative successor `e05300000002`; the
Project Control revision `e04700000001`, its parent `e04600000001`, all
historical migrations and every Project Control production path remain
immutable. No PATCH-054+ path or semantic authority is introduced. Review
result: **PASS**; Critical/Major/Minor/Observation: `0/0/0/0`.

The fresh Customer/Organization regression-path reconciliation review
separately challenged both newly authorized literals. The `script.get_heads()`
assertion and the cleanup/current-revision guard track only the repository-wide
Alembic head; neither defines Customer/Organization migration history. The
historical parentage assertions `e04100000001` / `e03800000001` and
`e03800000001` / `e03400000001`, all schema and ownership checks, the full
upgrade/downgrade and data-preservation behavior, and every historical migration
remain immutable. Authority is limited to replacing exactly those two
`e05200000002` literals with `e05300000002`; no PATCH-054+ path or behavior is
introduced. Review result: **PASS**; Critical/Major/Minor/Observation:
`0/0/0/0`.

The fresh bounded stale-global-head reconciliation searched only
`backend/tests/**` for the exact literal `e05200000002` and reviewed all 17
occurrences. Thirteen occurrences in eight newly allow-listed paths are proven
repository-global head bookkeeping; four PATCH-052 occurrences remain
intentionally unauthorized because they encode PATCH-052 readiness or
migration-under-test identity. No occurrence is ambiguous. Three readiness
assertions also expose an out-of-scope production regression signal: the
PATCH-052 readiness implementation compares the live database revision for
exact equality with `e05200000002`, so it reports unavailable at the
authoritative successor head. This reconciliation neither changes nor conceals
that contract defect. The
manifest review challenged accidental historical-revision conversion, lineage and
downgrade weakening, schema/data weakening, whole-file authorization, hidden
production semantics, historical migration rewrite and PATCH-054+ leakage.
Only the thirteen enumerated literal substitutions may occur later after Human
re-acceptance; every neighboring assertion and all production and migration
paths remain unchanged. Review result: **PASS**;
Critical/Major/Minor/Observation: `0/0/0/1`. The observation is the separately
governed PATCH-052 readiness regression signal and does not weaken or block this
manifest-only reconciliation.

The focused PATCH-052 readiness compatibility manifest review accepted the
defect as **PRE-EXISTING PATCH-052 FORWARD-COMPATIBILITY DEFECT DISCOVERED BY
PATCH-053** and challenged arbitrary-newer acceptance, lexical/numeric ordering,
unknown or divergent revision acceptance, malformed/multi-row/missing-script/
graph-error handling, loss of existing capability checks, mutation of
`PATCH_052_HEAD`, migration-history or downgrade weakening, schema/data drift,
path breadth and PATCH-054+ leakage. The four added paths and one widened path
authorize only deterministic source-graph ancestry containment, the enumerated
positive/negative readiness cases, and historical-test lifecycle restoration.
Every error remains fail-closed; the historical equality/floor case remains;
all migration files and schema/data semantics remain immutable. Review result:
**PASS**; Critical/Major/Minor/Observation: `0/0/0/0`.
