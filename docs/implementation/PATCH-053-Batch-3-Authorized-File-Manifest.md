# PATCH-053 — Batch 3 Authorized File Manifest

## A. Authority header

| Field | Value |
|---|---|
| Document ID | `PATCH-053-B3-AUTHORIZED-FILE-MANIFEST` |
| PATCH / Batch | PATCH-053 / Batch 3 — Instrumentation ↔ Control & Automation |
| Manifest status | **CREATED / REVIEW PASS / COMPLETE / AWAITING HUMAN MANIFEST ACCEPTANCE** |
| Upstream authorities | ADR-026, Architecture-053, EDS-053, IDS-053 and Implementation-Plan-053: Human accepted / authoritative |
| Batch-1 state | Human accepted / complete |
| Batch-2 state | Human accepted / complete |
| Batch-2 baseline | `b1993ed4b7d9d02422b39380f70528692f3c22d9` |
| Alembic sole head | `e05300000001` |
| Migration authority | **NONE** |
| Batch 4–5 / PATCH-054+ authority | **NONE** |

This manifest is the exact maximum file and semantic-hunk boundary for a later
Human-authorized PATCH-053 Batch-3 implementation and local delivery. A path's
presence authorizes only its stated I↔C purpose. It does not authorize whole-
file replacement, unrelated cleanup, a schema change, an alternative layout,
or later-batch behavior. A required change outside this closed boundary is a
stop condition for Human reconciliation.

The accepted machine scope is version `1.0.0`, interface
`cross.interface.ic.signal_control.v1`, projections
`xdi.proj.i.signal.v1`, `xdi.proj.c.io.v1`,
`xdi.proj.c.command_status.v1` and `xdi.proj.commitment.v1`, path
`xdi.path.ic.valve_feedback.v1`, and exactly these rules:

1. `xdi.ic.signal_type.v1`;
2. `xdi.ic.signal_range.v1`;
3. `xdi.ic.valve_command_feedback.v1`; and
4. `xdi.ic.commitment_fulfilment.v1`.

## B. Exact create allow-list

Exactly 10 paths may be created. No alternative filename, helper, generated
source or future-vector placeholder is implicit.

| Exact path | Purpose | Owning area | Requirement | Delivery classification |
|---|---|---|---|---|
| `docs/implementation/PATCH-053-Batch-3-Authorized-File-Manifest.md` | Accepted maximum delivery boundary | governance | required carry-in | governance |
| `docs/implementation/PATCH-053-Batch-3-Implementation-Evidence.md` | Actual commands, results, review and scope evidence without fabricated PASS | all four rules / IC01–IC08 | required at delivery | derived evidence |
| `backend/tests/fixtures/cross_discipline/patch053.ic01.signal_type_equal.fixture.v1.json` | Authoritative IC01 fixture | signal type | required | test fixture |
| `backend/tests/fixtures/cross_discipline/patch053.ic02.signal_type_mismatch.fixture.v1.json` | Authoritative IC02 fixture | signal type | required | test fixture |
| `backend/tests/fixtures/cross_discipline/patch053.ic03.range_contains.fixture.v1.json` | Authoritative IC03 fixture | signal range | required | test fixture |
| `backend/tests/fixtures/cross_discipline/patch053.ic04.range_mismatch.fixture.v1.json` | Authoritative IC04 fixture | signal range | required | test fixture |
| `backend/tests/fixtures/cross_discipline/patch053.ic05.valve_paths.fixture.v1.json` | Authoritative IC05 fixture | valve command/feedback | required | test fixture |
| `backend/tests/fixtures/cross_discipline/patch053.ic06.valve_feedback_gap.fixture.v1.json` | Authoritative IC06 fixture | valve command/feedback | required | test fixture |
| `backend/tests/fixtures/cross_discipline/patch053.ic07.commitment_fulfilled.fixture.v1.json` | Authoritative IC07 fixture | commitment fulfilment | required | test fixture |
| `backend/tests/fixtures/cross_discipline/patch053.ic08.commitment_unfulfilled.fixture.v1.json` | Authoritative IC08 fixture | commitment fulfilment | required | test fixture |

## C. Exact modify allow-list

Exactly 19 existing paths may be modified. Conditional authority permits
omission, never speculative edits.

| Exact path | Purpose | Expected Batch-3 change class | Shared state | Editing/staging rule |
|---|---|---|---|---|
| `backend/app/discipline_packages/cross_discipline/definitions/eic_v1.py` | Add the cumulative I↔C interface/projection/rule declarations and 67-vector definition digest | additive trusted definitions only | Batch-1/2 shared | hunk-only; retain prior artifacts |
| `backend/app/discipline_packages/cross_discipline/rules/eic_v1.py` | Register exactly four deterministic I↔C handlers | additive four-rule dispatch/handlers | Batch-2 shared | hunk-only |
| `backend/app/discipline_packages/cross_discipline/evaluator.py` | Register/evaluate only the four I↔C rules through the shared evaluator | additive typed registration | Batch-1/2 shared | hunk-only |
| `backend/app/discipline_packages/cross_discipline/conformance_manifest.py` | Add exactly IC01–IC08 to the cumulative immutable manifest | additive eight-vector declarations | Batch-1/2 shared | hunk-only |
| `backend/app/discipline_packages/cross_discipline/conformance_harness.py` | Execute IC01–IC08 through real rule/projection contracts | additive cumulative fixture adapters/assertions | Batch-1/2 shared | hunk-only |
| `backend/app/adapters/cross_discipline_sources.py` | Authorization-first minimal Instrumentation, C&A and commitment projections/completeness | additive I↔C source branches only | Batch-1/2 shared | hunk-only |
| `backend/app/services/cross_discipline_service.py` | Route authorized I↔C assessment through the existing UoW/persistence pipeline | additive I↔C orchestration only | Batch-1/2 shared | hunk-only |
| `frontend/src/api/types.ts` | Add exact I↔C presentation/provenance DTO types | additive DTO hunk only | currently dirty, unrelated PATCH-050 work | **mandatory hunk-only** |
| `frontend/src/api/client.ts` | Carry existing PATCH-053 responses needed by I↔C surfaces; no new operation | conditional response mapping only | currently dirty, unrelated PATCH-050 work | **mandatory hunk-only** |
| `frontend/src/components/CrossDisciplineIntelligencePanel.tsx` | Compose I↔C data into existing surfaces and preserve state/cancellation | additive composition only | Batch-1/2 shared | hunk-only |
| `frontend/src/components/crossDiscipline/CrossDisciplineSourceComparison.tsx` | Present authorized signal-type and range comparisons without hidden operands | additive I↔C branches only | Batch-2 shared | hunk-only |
| `frontend/src/components/crossDiscipline/CrossDisciplineCommitmentContext.tsx` | Present current commitment fulfilment state/provenance | additive I↔C branch only | Batch-2 shared | hunk-only |
| `frontend/src/components/crossDiscipline/CrossDisciplineDependencyView.tsx` | Present persisted valve command/feedback paths or gaps only | additive I↔C branch only | Batch-2 shared | hunk-only |
| `frontend/src/pages/ProjectsPage.tsx` | Pass already-authorized I↔C panel state/selection only if required | conditional integration hunk | currently dirty, unrelated PATCH-050 work | **mandatory hunk-only** |
| `frontend/src/styles.css` | Add scoped accessible/RTL/responsive I↔C surface styles | conditional `.cross-discipline-*` additions only | currently dirty, unrelated PATCH-050 work | **mandatory hunk-only** |
| `backend/tests/test_cross_discipline_service.py` | Four rules, projections, completeness, persistence and accepted source/config/binding/commitment races | additive Batch-3 tests | Batch-1 shared | hunk-only |
| `backend/tests/test_cross_discipline_security.py` | I/C owner intersection and Context/Evidence/commitment nondisclosure | additive Batch-3 security tests | Batch-1/2 shared | hunk-only |
| `backend/tests/test_cross_discipline_conformance.py` | Exact IC01–IC08 assertions and cumulative 67/67 gate | additive Batch-3 conformance tests | Batch-1/2 shared | hunk-only |
| `frontend/src/test/cross-discipline-intelligence.test.tsx` | I↔C UI outcomes, protected/indeterminate/error, RTL, accessibility and cancellation | additive Batch-3 UI tests | Batch-1/2 shared | hunk-only |

`backend/app/discipline_packages/cross_discipline/contracts.py` is not in this
allow-list. The Plan's narrow contracts expansion was Batch-2-specific; Batch 3
must express its already accepted identities through the cumulative definition,
rule, evaluator and adapter seams. If a new frozen contract hunk is proven
necessary, implementation stops for Human Plan/manifest reconciliation.

## D. Exact test allow-list

Exactly four test source paths may be modified; no new test source file may be
created.

| Exact path | Authorized Batch-3 coverage |
|---|---|
| `backend/tests/test_cross_discipline_service.py` | Signal type/range, valve paths, commitment fulfilment, minimal projections, completeness, persistence, configuration/binding/source/commitment retry races |
| `backend/tests/test_cross_discipline_security.py` | Organization/Project/Workspace/I/C owner intersection, protected sources, Context/Evidence/commitment and idempotency nondisclosure |
| `backend/tests/test_cross_discipline_conformance.py` | IC01–IC08 real mapped assertions, immutable fixture/result digests, cumulative 67-vector gate |
| `frontend/src/test/cross-discipline-intelligence.test.tsx` | I↔C presentation, advisory/provenance, protected/indeterminate/loading/empty/error, RTL, accessibility and stale-response cancellation |

The following existing tests may be executed unchanged as regressions but are
not authorized for Batch-3 modification or staging:
`backend/tests/test_cross_discipline_contracts.py`,
`backend/tests/test_cross_discipline_concurrency.py`,
`backend/tests/test_cross_discipline_api.py`,
`backend/tests/test_cross_discipline_dispositions.py`,
`backend/tests/test_cross_discipline_history.py`,
`backend/tests/test_cross_discipline_database.py`,
`backend/tests/test_cross_discipline_migration.py`, and
`backend/tests/test_cross_discipline_performance.py`. Relevant concurrency and
API evidence must use those retained assertions plus Batch-3 assertions in the
four authorized paths. A required edit to an execution-only test is a stop
condition.

## E. Fixture allow-list

Exactly these eight new fixtures are authorized:

1. `backend/tests/fixtures/cross_discipline/patch053.ic01.signal_type_equal.fixture.v1.json`
2. `backend/tests/fixtures/cross_discipline/patch053.ic02.signal_type_mismatch.fixture.v1.json`
3. `backend/tests/fixtures/cross_discipline/patch053.ic03.range_contains.fixture.v1.json`
4. `backend/tests/fixtures/cross_discipline/patch053.ic04.range_mismatch.fixture.v1.json`
5. `backend/tests/fixtures/cross_discipline/patch053.ic05.valve_paths.fixture.v1.json`
6. `backend/tests/fixtures/cross_discipline/patch053.ic06.valve_feedback_gap.fixture.v1.json`
7. `backend/tests/fixtures/cross_discipline/patch053.ic07.commitment_fulfilled.fixture.v1.json`
8. `backend/tests/fixtures/cross_discipline/patch053.ic08.commitment_unfulfilled.fixture.v1.json`

The IDs, canonical request/result bytes and digests must match the accepted
96-vector manifest. The cumulative Batch-3 gate is exactly 67; the global total
remains 96. Batch-4/5 fixtures and count-only placeholders are forbidden.

## F. Frontend allow-list

No new Batch-3-specific frontend production file is authorized. Batch 3 must
extend these exact existing surfaces:

| Exact path | State | Boundary |
|---|---|---|
| `frontend/src/api/types.ts` | existing / dirty shared | additive I↔C presentation and provenance types only |
| `frontend/src/api/client.ts` | existing / dirty shared / conditional | existing PATCH-053 response mapping only; no operation |
| `frontend/src/components/CrossDisciplineIntelligencePanel.tsx` | existing shared | compose authorized I↔C state; preserve cancellation |
| `frontend/src/components/crossDiscipline/CrossDisciplineSourceComparison.tsx` | existing Batch-2 surface | signal-type/range presentation only |
| `frontend/src/components/crossDiscipline/CrossDisciplineCommitmentContext.tsx` | existing Batch-2 surface | commitment fulfilment presentation only |
| `frontend/src/components/crossDiscipline/CrossDisciplineDependencyView.tsx` | existing Batch-2 surface | persisted valve branch/path presentation only |
| `frontend/src/pages/ProjectsPage.tsx` | existing / dirty shared / conditional | minimal state/selection handoff only |
| `frontend/src/styles.css` | existing / dirty shared / conditional | scoped `.cross-discipline-*` I↔C styles only |

The frontend test path is governed by §D and is not included in the production
frontend count.

## G. Shared dirty-file rules

Exactly four currently dirty files intersect the Batch-3 maximum boundary:

| Exact path | Authorized? | Exact permitted semantic hunk | Protection |
|---|---|---|---|
| `frontend/src/api/types.ts` | yes | additive I↔C comparison/path/commitment presentation types | stage only Batch-3 hunks; preserve PATCH-050 guidance types unstaged |
| `frontend/src/api/client.ts` | conditional | additive mapping for existing PATCH-053 operations; no route or guidance-client change | stage only Batch-3 hunks; preserve PATCH-050 guidance client work unstaged |
| `frontend/src/pages/ProjectsPage.tsx` | conditional | minimal I↔C panel prop/state handoff | stage only Batch-3 hunks; preserve guidance integration and unrelated formatting unstaged |
| `frontend/src/styles.css` | conditional | scoped `.cross-discipline-*` I↔C additions | stage only Batch-3 hunks; preserve `.engineering-guidance*` additions unstaged |

Every other currently dirty or untracked path is **OUTSIDE** the Batch-3
allow-list and must remain unmodified by Batch 3 and unstaged. Whole-file
replacement, whole-file staging, unrelated formatting and absorption of
pre-existing hunks are prohibited. If another authorized path later acquires
unrelated changes, it automatically becomes hunk-only; inability to isolate the
Batch-3 hunk is a stop condition.

## H. Forbidden paths and scope

The allow-lists are closed. Batch 3 explicitly forbids:

- every `backend/migrations/` path and every migration rewrite;
- all ADR files, Architecture-053, EDS-053, IDS-053 and
  Implementation-Plan-053;
- every governance/review document except this accepted carry-in manifest and
  the exact Batch-3 implementation-evidence path in §B;
- `backend/app/discipline_packages/cross_discipline/contracts.py` absent Human
  reconciliation;
- dependency assembly, routers, request schemas, models, repositories,
  `backend/app/main.py` and any new backend module;
- E↔C, integrated E+I+C, Project Control Change Impact, Technical Report and AI;
- Batch 4, Batch 5, PATCH-054+, procurement, FAT/SAT, commissioning, punch and
  future-discipline behavior; and
- every path not written literally in §B or §C.

No wildcard, directory grant, alternate layout or adjacent-file authority is
implicit. Batch 3 extends the Batch-1/2 shared kernel and may not replace
canonicalization, Finding fingerprints, recurrence, persistence, API,
authorization/non-disclosure, history/replay, Audit/outbox or idempotency.

## I. Migration statement

**NO BATCH-3 MIGRATION AUTHORIZED.** The existing Batch-1 schema must be used
unchanged and `e05300000001` must remain the sole Alembic head. If later
implementation proves that a schema, model or migration change is necessary,
work must stop for Human reconciliation. No development, staging, production or
customer database migration is permitted.

## J. Delivery staging contract

Delivery must:

1. stage only exact literal paths from §§B–C;
2. use hunk-level staging for the four dirty shared paths in §G and every other
   authorized shared path;
3. never use `git add .` or `git add -A`;
4. inspect the complete `git diff --cached`;
5. run `git diff --cached --check`;
6. compare every staged path and semantic hunk against this manifest; and
7. preserve all unrelated dirty/untracked work unstaged.

Conditional paths may be omitted. No unlisted path may be staged.

## K. Delivery commit contract

Exactly one local Batch-3 delivery commit is permitted only after IC01–IC08
`8/8`, cumulative `67/67`, real PostgreSQL, security, concurrency, frontend and
affected Batch-1/2/I/C regressions pass, and independent review reports
Critical/Major `0/0`. Batch 2 must not be amended. No push is authorized. Batch
4 remains stopped pending separate Human acceptance and authority.

## L. Path-count summary

Counts use unique literal paths; category counts intentionally overlap create
and modify totals.

| Category | Exact count |
|---|---:|
| Permitted create paths | 10 |
| Permitted modify paths | 19 |
| Permitted test source paths | 4 |
| Permitted fixture paths | 8 |
| Permitted frontend production paths | 8 |
| Currently dirty shared hunk-only paths | 4 |
| Closed delivery universe | 29 |

## M. Rule-to-path matrix

The common implementation paths for every rule are:
`backend/app/discipline_packages/cross_discipline/definitions/eic_v1.py`,
`backend/app/discipline_packages/cross_discipline/rules/eic_v1.py`,
`backend/app/discipline_packages/cross_discipline/evaluator.py`,
`backend/app/discipline_packages/cross_discipline/conformance_manifest.py`,
`backend/app/discipline_packages/cross_discipline/conformance_harness.py`,
`backend/app/adapters/cross_discipline_sources.py`, and
`backend/app/services/cross_discipline_service.py`. Every row also uses
`backend/tests/test_cross_discipline_conformance.py` and the shared composition
and DTO seams authorized in §§C/F when necessary.

| Rule | Exact rule-specific test/frontend paths | Exact fixture paths |
|---|---|---|
| `xdi.ic.signal_type.v1` | `backend/tests/test_cross_discipline_service.py`; `backend/tests/test_cross_discipline_security.py`; `frontend/src/components/crossDiscipline/CrossDisciplineSourceComparison.tsx`; `frontend/src/test/cross-discipline-intelligence.test.tsx` | `backend/tests/fixtures/cross_discipline/patch053.ic01.signal_type_equal.fixture.v1.json`; `backend/tests/fixtures/cross_discipline/patch053.ic02.signal_type_mismatch.fixture.v1.json` |
| `xdi.ic.signal_range.v1` | `backend/tests/test_cross_discipline_service.py`; `backend/tests/test_cross_discipline_security.py`; `frontend/src/components/crossDiscipline/CrossDisciplineSourceComparison.tsx`; `frontend/src/test/cross-discipline-intelligence.test.tsx` | `backend/tests/fixtures/cross_discipline/patch053.ic03.range_contains.fixture.v1.json`; `backend/tests/fixtures/cross_discipline/patch053.ic04.range_mismatch.fixture.v1.json` |
| `xdi.ic.valve_command_feedback.v1` | `backend/tests/test_cross_discipline_service.py`; `backend/tests/test_cross_discipline_security.py`; `frontend/src/components/crossDiscipline/CrossDisciplineDependencyView.tsx`; `frontend/src/test/cross-discipline-intelligence.test.tsx` | `backend/tests/fixtures/cross_discipline/patch053.ic05.valve_paths.fixture.v1.json`; `backend/tests/fixtures/cross_discipline/patch053.ic06.valve_feedback_gap.fixture.v1.json` |
| `xdi.ic.commitment_fulfilment.v1` | `backend/tests/test_cross_discipline_service.py`; `backend/tests/test_cross_discipline_security.py`; `frontend/src/components/crossDiscipline/CrossDisciplineCommitmentContext.tsx`; `frontend/src/test/cross-discipline-intelligence.test.tsx` | `backend/tests/fixtures/cross_discipline/patch053.ic07.commitment_fulfilled.fixture.v1.json`; `backend/tests/fixtures/cross_discipline/patch053.ic08.commitment_unfulfilled.fixture.v1.json` |

## N. Vector-to-path matrix

Every row uses the seven common implementation paths named in §M,
`backend/tests/test_cross_discipline_conformance.py`, and the exact fixture
shown below. The cumulative Batch-3 gate remains 67 and the authoritative
global total remains 96.

| Vector | Exact additional test/frontend paths | Exact fixture path |
|---|---|---|
| IC01 `patch053.ic01.signal_type_equal` | `backend/tests/test_cross_discipline_service.py`; `frontend/src/components/crossDiscipline/CrossDisciplineSourceComparison.tsx`; `frontend/src/test/cross-discipline-intelligence.test.tsx` | `backend/tests/fixtures/cross_discipline/patch053.ic01.signal_type_equal.fixture.v1.json` |
| IC02 `patch053.ic02.signal_type_mismatch` | `backend/tests/test_cross_discipline_service.py`; `backend/tests/test_cross_discipline_security.py`; `frontend/src/components/crossDiscipline/CrossDisciplineSourceComparison.tsx`; `frontend/src/test/cross-discipline-intelligence.test.tsx` | `backend/tests/fixtures/cross_discipline/patch053.ic02.signal_type_mismatch.fixture.v1.json` |
| IC03 `patch053.ic03.range_contains` | `backend/tests/test_cross_discipline_service.py`; `frontend/src/components/crossDiscipline/CrossDisciplineSourceComparison.tsx`; `frontend/src/test/cross-discipline-intelligence.test.tsx` | `backend/tests/fixtures/cross_discipline/patch053.ic03.range_contains.fixture.v1.json` |
| IC04 `patch053.ic04.range_mismatch` | `backend/tests/test_cross_discipline_service.py`; `backend/tests/test_cross_discipline_security.py`; `frontend/src/components/crossDiscipline/CrossDisciplineSourceComparison.tsx`; `frontend/src/test/cross-discipline-intelligence.test.tsx` | `backend/tests/fixtures/cross_discipline/patch053.ic04.range_mismatch.fixture.v1.json` |
| IC05 `patch053.ic05.valve_paths` | `backend/tests/test_cross_discipline_service.py`; `frontend/src/components/crossDiscipline/CrossDisciplineDependencyView.tsx`; `frontend/src/test/cross-discipline-intelligence.test.tsx` | `backend/tests/fixtures/cross_discipline/patch053.ic05.valve_paths.fixture.v1.json` |
| IC06 `patch053.ic06.valve_feedback_gap` | `backend/tests/test_cross_discipline_service.py`; `backend/tests/test_cross_discipline_security.py`; `frontend/src/components/crossDiscipline/CrossDisciplineDependencyView.tsx`; `frontend/src/test/cross-discipline-intelligence.test.tsx` | `backend/tests/fixtures/cross_discipline/patch053.ic06.valve_feedback_gap.fixture.v1.json` |
| IC07 `patch053.ic07.commitment_fulfilled` | `backend/tests/test_cross_discipline_service.py`; `backend/tests/test_cross_discipline_security.py`; `frontend/src/components/crossDiscipline/CrossDisciplineCommitmentContext.tsx`; `frontend/src/test/cross-discipline-intelligence.test.tsx` | `backend/tests/fixtures/cross_discipline/patch053.ic07.commitment_fulfilled.fixture.v1.json` |
| IC08 `patch053.ic08.commitment_unfulfilled` | `backend/tests/test_cross_discipline_service.py`; `backend/tests/test_cross_discipline_security.py`; `frontend/src/components/crossDiscipline/CrossDisciplineCommitmentContext.tsx`; `frontend/src/test/cross-discipline-intelligence.test.tsx` | `backend/tests/fixtures/cross_discipline/patch053.ic08.commitment_unfulfilled.fixture.v1.json` |

## Independent manifest review

The review challenged broad or missing paths, speculative helpers, migration or
governance leakage, unsafe dirty-file handling, missing hunk isolation, rule and
vector identity drift, wildcards, E↔C/integrated/Impact/Report/AI/PATCH-054+
leakage, and replacement of Batch-1/2 architecture. The closed 29-path universe
is derived from the Plan's literal cumulative paths and the current Batch-2
layout. No alternate layout remains equally valid.

Result: **PASS**. Critical/Major/Minor/Observation: `0/0/0/0`. Documentation-
only remediation cycles: `0`.

Human manifest acceptance is required before Batch-3 implementation authority
may resume. Batch 3 remains not started.
