# PATCH-053 — Batch 2 Authorized File Manifest

## 1. Authority header

| Field | Value |
|---|---|
| Document ID | `PATCH-053-B2-AUTHORIZED-FILE-MANIFEST` |
| PATCH / Batch | PATCH-053 / Batch 2 — Electrical ↔ Instrumentation |
| Manifest status | **CREATED / REVIEW PASS / COMPLETE / AWAITING HUMAN MANIFEST ACCEPTANCE** |
| ADR-026 | Human accepted / authoritative |
| Architecture-053 | Human accepted / authoritative |
| EDS-053 | Human accepted / authoritative |
| IDS-053 | Narrowly reconciled; Human re-accepted / authoritative |
| Implementation-Plan-053 | Narrowly synchronized; Human accepted / authoritative |
| Batch-1 baseline | `b51ab1efbef402ceebf31c19ef11449312a058d2` |
| Alembic sole head | `e05300000001` |
| Migration authority | **NONE** |
| Batch 3–5 / PATCH-054+ authority | **NONE** |

This manifest is the exact maximum file and semantic-hunk boundary for a later
Human-authorized PATCH-053 Batch-2 implementation and local delivery. A path's
presence in a table authorizes only the stated Electrical ↔ Instrumentation
purpose. It does not authorize whole-file replacement, unrelated cleanup, a
schema change, another rule family, or a future-batch placeholder. Any required
path or semantic change outside this exact boundary is a stop condition for
Human reconciliation.

## 2. Exact create allow-list

Exactly 13 paths may be created. No alternative filename or additional helper,
test, fixture, generated source, or governance artifact is implicit.

| Exact path | Purpose | Owning area | Requirement | Delivery classification |
|---|---|---|---|---|
| `docs/implementation/PATCH-053-Batch-2-Authorized-File-Manifest.md` | Accepted maximum delivery boundary | governance | required carry-in | governance |
| `docs/implementation/PATCH-053-Batch-2-Implementation-Evidence.md` | Record actual commands, results, digests, review and scope evidence without fabricated PASS | all four rules / EI01–EI08 | required at delivery | derived evidence |
| `frontend/src/components/crossDiscipline/CrossDisciplineSourceComparison.tsx` | Authorized typed Electrical/Instrumentation comparison; no hidden operands | power and voltage | required | frontend production |
| `frontend/src/components/crossDiscipline/CrossDisciplineCommitmentContext.tsx` | Authorized current-use commitment and closed declaration presence view | handoff completeness | required | frontend production |
| `frontend/src/components/crossDiscipline/CrossDisciplineDependencyView.tsx` | Persisted explicit bounded path/expected-gap view only | cable/JB path | required | frontend production |
| `backend/tests/fixtures/cross_discipline/patch053.ei01.power_present.fixture.v1.json` | Authoritative EI01 fixture | power presence | required | test fixture |
| `backend/tests/fixtures/cross_discipline/patch053.ei02.power_missing.fixture.v1.json` | Authoritative EI02 fixture | power presence | required | test fixture |
| `backend/tests/fixtures/cross_discipline/patch053.ei03.voltage_equal.fixture.v1.json` | Authoritative EI03 fixture | voltage consistency | required | test fixture |
| `backend/tests/fixtures/cross_discipline/patch053.ei04.voltage_mismatch.fixture.v1.json` | Authoritative EI04 fixture | voltage consistency | required | test fixture |
| `backend/tests/fixtures/cross_discipline/patch053.ei05.cable_jb_complete.fixture.v1.json` | Authoritative EI05 fixture | cable/JB path | required | test fixture |
| `backend/tests/fixtures/cross_discipline/patch053.ei06.cable_jb_gap.fixture.v1.json` | Authoritative EI06 fixture | cable/JB path | required | test fixture |
| `backend/tests/fixtures/cross_discipline/patch053.ei07.handoff_complete.fixture.v1.json` | Authoritative EI07 fixture | handoff completeness | required | test fixture |
| `backend/tests/fixtures/cross_discipline/patch053.ei08.handoff_incomplete.fixture.v1.json` | Authoritative EI08 fixture | handoff completeness | required | test fixture |

## 3. Exact modify allow-list

Exactly 17 existing paths may be modified. Every change must be an exact
Batch-2 hunk; conditional authority permits omission, never speculative edits.

| Exact path | Purpose | Expected Batch-2 change class | Shared/unrelated state | Staging rule |
|---|---|---|---|---|
| `backend/app/discipline_packages/cross_discipline/contracts.py` | Add only IDS-053 §16 nested interface/projection/schema/adapter/selector/completeness/grammar/rule contracts | additive frozen dataclasses/constants/validation | clean at manifest creation | exact path; hunk-only if later dirty |
| `backend/app/discipline_packages/cross_discipline/definitions/eic_v1.py` | Build and validate retained Batch-1 plus exact E↔I cumulative definitions and 59-vector gate | additive cumulative V1 definitions/digests | clean | exact path |
| `backend/app/discipline_packages/cross_discipline/rules/eic_v1.py` | Register exactly four E↔I deterministic handlers | additive four-rule dispatch/handlers | clean | exact path |
| `backend/app/discipline_packages/cross_discipline/evaluator.py` | Register/evaluate only the four trusted E↔I rules through the shared evaluator | additive typed registration/evaluation | clean | exact path |
| `backend/app/discipline_packages/cross_discipline/conformance_manifest.py` | Add exactly EI01–EI08 to the immutable cumulative manifest | additive eight vector declarations | clean | exact path |
| `backend/app/discipline_packages/cross_discipline/conformance_harness.py` | Execute EI01–EI08 through real rule/projection contracts | additive E↔I fixture adapters/assertions | clean | exact path |
| `backend/app/adapters/cross_discipline_sources.py` | Authorization-first minimal projections and completeness for five reconciled definitions | additive E↔I source projection behavior | clean | exact path |
| `backend/app/services/cross_discipline_service.py` | Route authorized E↔I assessment through the existing Batch-1 UoW/pipeline | additive pair orchestration only | clean | exact path |
| `frontend/src/api/types.ts` | Add exact E↔I presentation/provenance types only | additive DTO types | currently dirty with unrelated work | **mandatory hunk-only** |
| `frontend/src/api/client.ts` | Carry existing PATCH-053 responses needed by E↔I surfaces; no new operation | conditional additive mapping only | currently dirty with unrelated work | **mandatory hunk-only** |
| `frontend/src/components/CrossDisciplineIntelligencePanel.tsx` | Compose the three Batch-2 surfaces and preserve all shared states/cancellation | additive E↔I composition | clean | exact path; hunk-only if later dirty |
| `frontend/src/pages/ProjectsPage.tsx` | Pass only already-authorized Batch-2 state/selection if the mounted panel requires it | conditional integration hunk | currently dirty with unrelated work | **mandatory hunk-only** |
| `frontend/src/styles.css` | Add scoped accessible/RTL/responsive E↔I component styles | additive `.cross-discipline-*` rules only | currently dirty with unrelated work | **mandatory hunk-only** |
| `backend/tests/test_cross_discipline_service.py` | Four rules, projections, completeness, graph outcomes and accepted source/config/commitment retry races | additive Batch-2 tests | clean | exact path |
| `backend/tests/test_cross_discipline_security.py` | E/I owner intersection and selector/path/Context/Evidence/commitment nondisclosure | additive Batch-2 security tests | clean | exact path |
| `backend/tests/test_cross_discipline_conformance.py` | Exact EI01–EI08 assertions and cumulative 59/59 gate | additive Batch-2 conformance tests | clean | exact path |
| `frontend/src/test/cross-discipline-intelligence.test.tsx` | Batch-2 comparison/commitment/dependency, state, RTL, accessibility and stale-response tests | additive Batch-2 UI tests | clean | exact path |

## 4. Exact test allow-list

Exactly four test source files may be modified; no new test source file may be
created. The eight fixture files in §5 are counted separately.

| Exact path | State | Authorized coverage |
|---|---|---|
| `backend/tests/test_cross_discipline_service.py` | modify | power, voltage, cable/JB, handoff, projection/completeness, graph, source/config/commitment races, retry behavior |
| `backend/tests/test_cross_discipline_security.py` | modify | Organization/Project/Workspace/E/I owner intersection, protected selectors/edges/declarations, Context/Evidence/commitment and idempotency nondisclosure |
| `backend/tests/test_cross_discipline_conformance.py` | modify | EI01–EI08 real assertions, immutable fixture/result digests, cumulative 59-vector gate |
| `frontend/src/test/cross-discipline-intelligence.test.tsx` | modify | E↔I UI, protected/indeterminate/loading/empty/error, advisory labeling, authorized provenance, RTL, accessibility, cancellation |

The following Plan-owned Batch-1/5 tests may be executed unchanged as affected
regressions but are not authorized for Batch-2 modification or staging:
`backend/tests/test_cross_discipline_concurrency.py`,
`backend/tests/test_cross_discipline_api.py`,
`backend/tests/test_cross_discipline_contracts.py`,
`backend/tests/test_cross_discipline_database.py`,
`backend/tests/test_cross_discipline_migration.py`, and
`backend/tests/test_cross_discipline_performance.py`. API and generic
concurrency evidence must use their existing assertions plus Batch-2 assertions
in the four authorized files above. A required edit to an execution-only test is
a stop condition.

## 5. Fixture allow-list

Exactly these eight new fixture paths are authorized:

1. `backend/tests/fixtures/cross_discipline/patch053.ei01.power_present.fixture.v1.json`
2. `backend/tests/fixtures/cross_discipline/patch053.ei02.power_missing.fixture.v1.json`
3. `backend/tests/fixtures/cross_discipline/patch053.ei03.voltage_equal.fixture.v1.json`
4. `backend/tests/fixtures/cross_discipline/patch053.ei04.voltage_mismatch.fixture.v1.json`
5. `backend/tests/fixtures/cross_discipline/patch053.ei05.cable_jb_complete.fixture.v1.json`
6. `backend/tests/fixtures/cross_discipline/patch053.ei06.cable_jb_gap.fixture.v1.json`
7. `backend/tests/fixtures/cross_discipline/patch053.ei07.handoff_complete.fixture.v1.json`
8. `backend/tests/fixtures/cross_discipline/patch053.ei08.handoff_incomplete.fixture.v1.json`

The IDs, canonical request/result bytes and digests must match the accepted
96-vector manifest. Batch-3/4/5 fixtures and count-only placeholders are
forbidden.

## 6. Frontend allow-list

Exactly eight frontend production paths are permitted:

| Exact path | State | Boundary |
|---|---|---|
| `frontend/src/components/crossDiscipline/CrossDisciplineSourceComparison.tsx` | create | authorized typed E/I comparison only |
| `frontend/src/components/crossDiscipline/CrossDisciplineCommitmentContext.tsx` | create | authorized commitment/declaration context only |
| `frontend/src/components/crossDiscipline/CrossDisciplineDependencyView.tsx` | create | persisted explicit path/gap only |
| `frontend/src/api/types.ts` | modify / dirty shared | exact Batch-2 DTO hunk only |
| `frontend/src/api/client.ts` | conditional modify / dirty shared | response mapping only; no new operation |
| `frontend/src/components/CrossDisciplineIntelligencePanel.tsx` | modify | compose three surfaces; preserve shared state/cancellation |
| `frontend/src/pages/ProjectsPage.tsx` | conditional modify / dirty shared | only required panel state/selection handoff |
| `frontend/src/styles.css` | modify / dirty shared | scoped E↔I styles only |

The frontend test path is governed by §4 and is not included in this production
frontend count.

## 7. Shared dirty-file rules

At manifest creation, exactly four currently dirty shared paths intersect the
Batch-2 maximum boundary:

| Exact path | Authorized? | Exact permitted semantic hunk | Protection |
|---|---|---|---|
| `frontend/src/api/types.ts` | yes | additive E↔I comparison/path/commitment presentation types | stage only Batch-2 hunks; preserve all other changes unstaged |
| `frontend/src/api/client.ts` | conditional | additive mapping needed by existing PATCH-053 operations; no route or unrelated client change | stage only Batch-2 hunks; preserve all other changes unstaged |
| `frontend/src/pages/ProjectsPage.tsx` | conditional | minimal E↔I panel prop/state handoff only | stage only Batch-2 hunks; preserve all other changes unstaged |
| `frontend/src/styles.css` | yes | scoped `.cross-discipline-*` E↔I rules only | stage only Batch-2 hunks; preserve all other changes unstaged |

Whole-file replacement, whole-file staging, formatting unrelated regions, and
absorbing pre-existing hunks are prohibited for these four paths. Every other
path reported dirty at this manifest's creation is explicitly **OUTSIDE** the
Batch-2 allow-list and must remain unmodified by Batch 2 and unstaged. If any
otherwise clean authorized path acquires unrelated changes before delivery, it
automatically becomes hunk-only; inability to separate the hunks is a stop
condition.

## 8. Forbidden paths and scope

The exact tables above are closed. In particular, Batch 2 forbids:

- every `backend/migrations/` path and every existing migration rewrite;
- ADR-026, Architecture-053, EDS-053, IDS-053 and Implementation-Plan-053;
- all governance/review documents except the carry-in manifest and the exact
  Batch-2 implementation-evidence path in §2;
- Project Control Change Impact code, Technical Report integration and AI;
- I↔C, E↔C and integrated E+I+C definitions, handlers, projections, fixtures,
  UI, tests and placeholders;
- PATCH-054+ and Batch 3–5 work;
- procurement, FAT/SAT, commissioning, punch and future-discipline behavior;
- `backend/app/repositories/cross_discipline_repository.py`,
  `backend/app/repositories/cross_discipline_unit_of_work.py`, models, schemas,
  ports, dependencies, routers, `backend/app/main.py`, migration code and any
  new backend module; and
- any path not written literally in §2 or §3.

No directory wildcard, fuzzy path, generated-path pattern, or implicit adjacent
file is authorized.

## 9. Migration statement

**NO BATCH-2 MIGRATION IS AUTHORIZED.** The existing Batch-1 schema must be
used unchanged and `e05300000001` must remain the sole Alembic head. If later
implementation proves that any schema, model or migration change is necessary,
work must stop for Human reconciliation. No development, staging, production or
customer database migration is permitted.

## 10. Delivery staging contract

Delivery must:

1. stage only exact literal paths from §2 and §3;
2. use hunk-level staging for the four dirty shared paths in §7 and any clean
   authorized path that later contains unrelated changes;
3. never use `git add .` or `git add -A`;
4. inspect the complete `git diff --cached`;
5. run `git diff --cached --check`;
6. compare the staged path set for exact subset equality against §§2–3 and
   reject any semantic hunk outside its stated purpose; and
7. preserve every unrelated dirty or untracked path unstaged.

The final staged set may omit conditional paths that required no implementation
change. It may not contain an unlisted path. The manifest itself and evidence
file may be staged only with the later accepted Batch-2 delivery.

## 11. Delivery commit contract

Exactly one local Batch-2 delivery commit is permitted only after all accepted
Batch-2 gates pass: EI01–EI08 `8/8`, cumulative `59/59`, PostgreSQL, security,
completeness, graph, concurrency, frontend, regressions, independent review,
Critical/Major `0/0`, worktree and staged whitespace checks, and exact manifest
scope verification. The Batch-1 commit must not be amended. No push is
authorized. Batch 3 remains stopped pending separate Human acceptance and
authority.

## 12. Path-count summary

Counts use unique literal paths. Category counts intentionally overlap the
create/modify totals where a test or frontend path is also creatable/modifiable.

| Category | Exact count |
|---|---:|
| Permitted create paths | 13 |
| Permitted modify paths | 17 |
| Permitted test source paths | 4 |
| Permitted fixture paths | 8 |
| Permitted frontend production paths | 8 |
| Currently dirty shared hunk-only paths | 4 |

The closed delivery universe is 30 unique paths: 13 create plus 17 modify.

## 13. Rule-to-path matrix

Common trusted/pipeline paths for every rule are
`backend/app/discipline_packages/cross_discipline/contracts.py`,
`backend/app/discipline_packages/cross_discipline/definitions/eic_v1.py`,
`backend/app/discipline_packages/cross_discipline/rules/eic_v1.py`,
`backend/app/discipline_packages/cross_discipline/evaluator.py`,
`backend/app/discipline_packages/cross_discipline/conformance_manifest.py`,
`backend/app/discipline_packages/cross_discipline/conformance_harness.py`,
`backend/app/adapters/cross_discipline_sources.py`, and
`backend/app/services/cross_discipline_service.py`.

| Rule | Exact additional implementation/test/frontend paths | Exact fixture paths |
|---|---|---|
| `xdi.ei.instrument_power_required.v1` | `backend/tests/test_cross_discipline_service.py`; `backend/tests/test_cross_discipline_security.py`; `backend/tests/test_cross_discipline_conformance.py`; `frontend/src/components/crossDiscipline/CrossDisciplineSourceComparison.tsx`; `frontend/src/components/CrossDisciplineIntelligencePanel.tsx`; `frontend/src/test/cross-discipline-intelligence.test.tsx` | `backend/tests/fixtures/cross_discipline/patch053.ei01.power_present.fixture.v1.json`; `backend/tests/fixtures/cross_discipline/patch053.ei02.power_missing.fixture.v1.json` |
| `xdi.ei.motor_instrument_voltage.v1` | `backend/tests/test_cross_discipline_service.py`; `backend/tests/test_cross_discipline_security.py`; `backend/tests/test_cross_discipline_conformance.py`; `frontend/src/components/crossDiscipline/CrossDisciplineSourceComparison.tsx`; `frontend/src/components/CrossDisciplineIntelligencePanel.tsx`; `frontend/src/test/cross-discipline-intelligence.test.tsx` | `backend/tests/fixtures/cross_discipline/patch053.ei03.voltage_equal.fixture.v1.json`; `backend/tests/fixtures/cross_discipline/patch053.ei04.voltage_mismatch.fixture.v1.json` |
| `xdi.ei.cable_jb_path.v1` | `backend/tests/test_cross_discipline_service.py`; `backend/tests/test_cross_discipline_security.py`; `backend/tests/test_cross_discipline_conformance.py`; `frontend/src/components/crossDiscipline/CrossDisciplineDependencyView.tsx`; `frontend/src/components/CrossDisciplineIntelligencePanel.tsx`; `frontend/src/test/cross-discipline-intelligence.test.tsx` | `backend/tests/fixtures/cross_discipline/patch053.ei05.cable_jb_complete.fixture.v1.json`; `backend/tests/fixtures/cross_discipline/patch053.ei06.cable_jb_gap.fixture.v1.json` |
| `xdi.ei.handoff_complete.v1` | `backend/tests/test_cross_discipline_service.py`; `backend/tests/test_cross_discipline_security.py`; `backend/tests/test_cross_discipline_conformance.py`; `frontend/src/components/crossDiscipline/CrossDisciplineCommitmentContext.tsx`; `frontend/src/components/CrossDisciplineIntelligencePanel.tsx`; `frontend/src/test/cross-discipline-intelligence.test.tsx` | `backend/tests/fixtures/cross_discipline/patch053.ei07.handoff_complete.fixture.v1.json`; `backend/tests/fixtures/cross_discipline/patch053.ei08.handoff_incomplete.fixture.v1.json` |

## 14. Vector-to-path matrix

Every row uses the common trusted/pipeline paths named in §13, the exact fixture
shown below, `backend/tests/test_cross_discipline_conformance.py`, and
`frontend/src/test/cross-discipline-intelligence.test.tsx`.

| Vector | Exact rule-specific test/presentation paths | Exact fixture path |
|---|---|---|
| EI01 `patch053.ei01.power_present` | `backend/tests/test_cross_discipline_service.py`; `backend/tests/test_cross_discipline_security.py`; `frontend/src/components/crossDiscipline/CrossDisciplineSourceComparison.tsx` | `backend/tests/fixtures/cross_discipline/patch053.ei01.power_present.fixture.v1.json` |
| EI02 `patch053.ei02.power_missing` | `backend/tests/test_cross_discipline_service.py`; `backend/tests/test_cross_discipline_security.py`; `frontend/src/components/crossDiscipline/CrossDisciplineSourceComparison.tsx` | `backend/tests/fixtures/cross_discipline/patch053.ei02.power_missing.fixture.v1.json` |
| EI03 `patch053.ei03.voltage_equal` | `backend/tests/test_cross_discipline_service.py`; `backend/tests/test_cross_discipline_security.py`; `frontend/src/components/crossDiscipline/CrossDisciplineSourceComparison.tsx` | `backend/tests/fixtures/cross_discipline/patch053.ei03.voltage_equal.fixture.v1.json` |
| EI04 `patch053.ei04.voltage_mismatch` | `backend/tests/test_cross_discipline_service.py`; `backend/tests/test_cross_discipline_security.py`; `frontend/src/components/crossDiscipline/CrossDisciplineSourceComparison.tsx` | `backend/tests/fixtures/cross_discipline/patch053.ei04.voltage_mismatch.fixture.v1.json` |
| EI05 `patch053.ei05.cable_jb_complete` | `backend/tests/test_cross_discipline_service.py`; `backend/tests/test_cross_discipline_security.py`; `frontend/src/components/crossDiscipline/CrossDisciplineDependencyView.tsx` | `backend/tests/fixtures/cross_discipline/patch053.ei05.cable_jb_complete.fixture.v1.json` |
| EI06 `patch053.ei06.cable_jb_gap` | `backend/tests/test_cross_discipline_service.py`; `backend/tests/test_cross_discipline_security.py`; `frontend/src/components/crossDiscipline/CrossDisciplineDependencyView.tsx` | `backend/tests/fixtures/cross_discipline/patch053.ei06.cable_jb_gap.fixture.v1.json` |
| EI07 `patch053.ei07.handoff_complete` | `backend/tests/test_cross_discipline_service.py`; `backend/tests/test_cross_discipline_security.py`; `frontend/src/components/crossDiscipline/CrossDisciplineCommitmentContext.tsx` | `backend/tests/fixtures/cross_discipline/patch053.ei07.handoff_complete.fixture.v1.json` |
| EI08 `patch053.ei08.handoff_incomplete` | `backend/tests/test_cross_discipline_service.py`; `backend/tests/test_cross_discipline_security.py`; `frontend/src/components/crossDiscipline/CrossDisciplineCommitmentContext.tsx` | `backend/tests/fixtures/cross_discipline/patch053.ei08.handoff_incomplete.fixture.v1.json` |

## 15. Stop conditions and review disposition

Stop without workaround if a schema change, unlisted path, future-batch rule,
new operation, inferred relationship, fuzzy selector, source-of-truth copy,
authorization-after-resolution flow, or inseparable unrelated dirty hunk is
required. The same applies if any required gate cannot pass within this closed
boundary.

Fresh independent manifest review challenged broad/speculative paths, missing
required seams, future-batch and migration leakage, dirty-file safety, vector
mapping, wildcards and staging ambiguity. One documentation-only remediation
cycle replaced rule/vector shorthand with literal paths. Result: **PASS**;
Critical/Major/Minor/Observation `0/0/0/0`. Human manifest acceptance is
required before Batch-2 implementation authority resumes.
