# PATCH-051 Batch-5 Final Conformance Evidence

## Scope and method

Batch 5 is the implementation-plan reconciliation/readiness/regression gate.
It does not create a deployment, execute a migration, close PATCH-051, or
start PATCH-052.  This evidence inspects the accepted Architecture-051,
ADR-024, EDS-051, focused persistence reconciliation, IDS-051,
Implementation-Plan-051, the Batch-4/5 frontend boundary reconciliation, and
the Batch-1 through Batch-4 evidence and reviews against the current dirty
worktree.

The exact reconciled Plan manifest is: run the named package contract,
Registry, projection, compatibility, service, transaction, Audit, API,
security, migration, preflight, conformance, performance and database-role
tests; run Workspace core/migration/permission and specified frontend
regressions; then verify source/projection readiness, conformance, resource
bounds, query plans/performance gates, sole Alembic head/exact-three-file
topology, static/import/diff/type/build evidence.  Its scope is conformance,
readiness, regression and reconciliation only; it expressly excludes a new
migration, deployment, PATCH-051 closure and PATCH-052.

## Accepted-invariant matrix

| Accepted invariant | Result | Current evidence |
|---|---|---|
| 1. Discipline is distinct from Package | IMPLEMENTED + PROVEN | contracts/conformance/legacy vectors |
| 2. Typed identity and provenance | IMPLEMENTED + PROVEN | contracts/remediation/compatibility vectors |
| 3. Trusted source Registry | IMPLEMENTED + PROVEN | static release/adapter/registry vectors |
| 4. Derived DB projection | IMPLEMENTED + PROVEN | projection/readiness parity vectors |
| 5. Exact package/version pins | IMPLEMENTED + PROVEN | service/API/preflight vectors |
| 6. Deterministic compatibility | IMPLEMENTED + PROVEN | compatibility/remediation vectors |
| 7. Organization configuration | IMPLEMENTED + PROVEN | service/transaction/API vectors |
| 8. Project selection/revision | IMPLEMENTED + PROVEN | service/migration/API vectors |
| 9. Workspace binding/state | IMPLEMENTED + PROVEN | Workspace/service/migration vectors |
| 10. Exact legacy translation | IMPLEMENTED + PROVEN | conformance and frontend workflow vectors |
| 11. Guarded authorization | IMPLEMENTED + PROVEN | transaction/API/Workspace permission vectors |
| 12. Concurrency | IMPLEMENTED + PROVEN | transaction/service PostgreSQL vectors |
| 13. Retry policy | IMPLEMENTED + PROVEN | transaction/service PostgreSQL vectors |
| 14. Audit | NOT IMPLEMENTED / NOT PROVEN | B5-MAJ-01 below |
| 15. APIs | IMPLEMENTED + PROVEN | ten-route API/security vectors |
| 16. Frontend integration | IMPLEMENTED + PROVEN | 91 frontend tests/type/build |
| 17. Readiness | IMPLEMENTED + PROVEN | source/current projection parity vectors |
| 18. Entitlement seam | IMPLEMENTED + PROVEN | contract adapter/vector (`NOT_REQUIRED`) |
| 19. Resource limits | IMPLEMENTED + PROVEN | strict schema/contract/remediation/API bound vectors |
| 20. Human engineering authority | IMPLEMENTED + PROVEN | contract prohibitions/no operational Package behavior |

## Proven conformance surface

The following accepted areas are implemented and have current regression
evidence: typed identity and exact source-qualified legacy translation;
immutable static Registry assembly and canonical digests; source/current
projection parity and fail-closed readiness; exact profile reconstruction and
compatibility; bounded resources; guarded Organization/Project configuration;
Workspace binding/rebind and historical state; retry/revocation/Audit
atomicity; strict DTOs and the ten accepted API routes; authorization-before-
disclosure and cursor binding; non-commercial entitlement seam; all three
PATCH-051 migrations and M3 cutover; frontend server-derived effective state,
Control transport mapping, future/unresolved rendering and unknown-component
fail-closed behavior.

The isolated PostgreSQL suite below passed 117 tests:

```
tests/test_discipline_package_{contracts,registry,projection,compatibility,
conformance,remediation,service,transaction,audit,api,readiness,migration,
preflight}.py
tests/test_engineering_workspace_{core,migration,permissions}.py
```

Frontend validation passed: 20 files / 91 tests, TypeScript typecheck and
production build.  Python compilation of the PATCH-051 modules passed.
`git diff --check` passed, staged files were empty, the source contains exactly
M1/M2/M3, and `alembic heads` reported the sole head `e05100000003`.

No production/customer/governed operational database was touched.  PostgreSQL
tests used only the isolated `satco_platform_patch02022_test` database.

The plan names separate `test_discipline_package_security.py` and
`test_discipline_package_performance.py` files.  The former is absent but its
route/authentication/cursor negatives are in `test_discipline_package_api.py`.
The latter is absent and its required performance/query-plan evidence is not
present; it is not represented as a passed gate.  The existing root-relative
database-role source-inspection test cannot run in the `/app` Docker mount;
the scoped role/bootstrap/migration sources were inspected directly.

## Blocking Major — audit persistence and pagination contract

**B5-MAJ-01: the audited persistence shape and ordering do not conform to the
accepted EDS/IDS contract.**

EDS-051 section 16 requires `correlation_id` and a server UTC `occurred_at`,
with indexes `(organization_id, occurred_at DESC, event_id DESC)` and
`(organization_id, project_id, occurred_at DESC, event_id DESC)`.  IDS-051
section 15 further requires the audit endpoint and signed cursor to use the
first of those timestamp-leading keys.

The current `PackageConfigurationAuditEvent` model and M1 migration omit both
`occurred_at` and `correlation_id`; M1 creates only
`ix_dp_audit_organization`; the route orders and cursors solely by UUID
`event_id`.  Consequently the specified 100-event audit query plan and p95
gate cannot be proven, and UUID ordering is not the accepted chronological
Audit contract.

Remediation requires adding persisted columns and indexes and changing the
cursor/order contract.  That is a migration/API contract change, expressly
outside Batch-5 authority.  No production remediation, migration, test-only
substitution, deployment action, or PATCH closure was performed.

## Result

Critical: 0

Major: 1 (B5-MAJ-01)

Minor: 0

Observation: 2 (absent dedicated performance file; Docker root-relative
source-inspection harness limitation)

Batch 5 cannot declare implementation complete or accepted while B5-MAJ-01
remains.  The next decision is whether to grant a separately governed
migration/API remediation or to revise the accepted EDS/IDS contract through
the required governance process.

## Corrective M4 resume evidence — 2026-09-01

The authorized B5-MAJ-01 corrective M4 was re-inspected in the preserved dirty
worktree.  It remains the sole source successor of M3 (`e05100000004` →
`e05100000003`) and adds nullable truthful historical fields, extracts only
canonical UUID text from minimized metadata, retains absent/malformed legacy
correlations as `NULL`, installs the current-insert guard, and retains the
existing immutable-Audit trigger.  The route separates known-time and
historical-unknown cursor segments; focused route vectors prove the transition,
state-bound cursor rejection, no duplicate/no skip behavior, and no runtime
permission broadening in the legacy-row fixture.

The isolated PostgreSQL M3→M4 exercise uses a transactional disposable schema
and executes the actual M4 upgrade, historical conversion, null guard,
immutability rejection, safe historical-only downgrade and re-upgrade.  It
also verifies the named physical Organization and Organization/Project index
definitions.  The schema transaction is rolled back; no production, customer,
or governed operational database was touched.

**New blocking Major — B5-MAJ-02: required Audit query-plan evidence fails.**

On a 10,103-row, multi-tenant isolated Audit corpus (100 known-time rows in
the requested tenant and a bounded `LIMIT 100` request), PostgreSQL produced a
sequential scan plus sort for the accepted known-time query shape rather than
`ix_dp_audit_organization_occurred_event`.  The exact physical indexes exist,
but the required tenant-scoped timestamp-leading query-plan/performance gate
is therefore not proven.  Correcting that outcome would require further
index/query-design work and potentially another migration.  That is outside
the granted corrective M4 authority, so validation stopped here.  No fresh
Batch-5 independent re-review was started.

Current corrective-resume result:

```
Critical: 0
Major: 2 (B5-MAJ-01 unresolved; B5-MAJ-02 new)
PATCH-051 BATCH-5: NOT ACCEPTED / INCOMPLETE
PATCH-051 IMPLEMENTATION: NOT COMPLETE
PATCH-051: OPEN / NOT CLOSED
```

## Corrective M5 B5-MAJ-02 remediation and validation — 2026-09-02

Under the separately granted corrective authority, exactly one forward
migration was added: `e05100000005` with `down_revision = "e05100000004"`.
M4 remains byte-for-byte unchanged
(`sha256: 19e4c2729c5151dab9c989c38aa8d55de5ce7edbe0850c75bb459e7bc4e5daad`).
M5 changes only the two accepted Audit access paths, retaining their names:

```text
(organization_id, occurred_at DESC NULLS LAST, event_id DESC)
(organization_id, project_id, occurred_at DESC NULLS LAST, event_id DESC)
```

Before execution, the authorized disposable database identified itself as
`satco_platform_patch02022_test`, role `satco`, revision `e05100000004`.
The actual pre-M5 index catalog already carried `NULLS LAST`, recording the
previously observed installed-M4 divergence. M5 was executed only against
that isolated database and it now reports `e05100000005`; no production,
customer, or governed operational database was touched.

The actual M4 and M5 modules are exercised in two independent disposable
schemas. Path A starts with an M3-shaped table, executes M4 then M5, and
proves the exact final catalog definitions. It also proves M5 downgrade
restores the historical M4 source definitions (`occurred_at DESC`, hence
descending `NULLS FIRST`) and re-upgrade restores `NULLS LAST`, with row
snapshots unchanged. Path B establishes the observed divergent M4 physical
state (the two same-named `NULLS LAST` indexes), then executes M5 and proves
the exact final definitions. No Audit row, timestamp, correlation, metadata,
column, trigger, guard, or unrelated object is changed by M5.

The production known-time Audit ordering is now explicit:
`occurred_at DESC NULLS LAST, event_id DESC`. A compiled-query vector covers
the Organization and Organization-plus-Project shapes. Historical-unknown
ordering remains `event_id DESC`; the signed cursor state machine is unchanged.

The plan vector builds a committed, unique, disposable schema with 200,100
Audit rows (100 selective target-organization rows across two Projects and
200,000 other-tenant rows), runs fresh `VACUUM (ANALYZE)`, and uses
`EXPLAIN (ANALYZE, BUFFERS, COSTS OFF)`. Both production-shaped known-time
queries use their intended respective indexes without a `Sort`; sequential
scans were not disabled. The schema is always dropped in `finally`. This is
physical-access-path evidence, not a production latency or SLO claim.

Focused M4/M5 plus Audit vectors passed (`10 passed`). The complete isolated
PostgreSQL Batch-1 through Batch-5 surface passed (`123 passed`): the thirteen
discipline-package files from the prior accepted manifest plus Workspace core,
migration, and permissions. The corrective test-harness updates retain the
production contract: service fixtures now provide UUID correlation IDs, and
Workspace helper-generated authenticated requests include `X-Correlation-ID`.
They do not broaden production privileges or weaken Audit/Registry controls.

Frontend validation passed (`20 files, 91 tests`), as did TypeScript typecheck
and production build. Python compilation passed. `alembic heads` reports the
one head `e05100000005`; history confirms
`e04700000001 → e05100000001 → e05100000002 → e05100000003 → e05100000004 →
e05100000005`; no M6 exists. `git diff --check` and the untracked-file
whitespace check pass; staged files remain empty.

Final isolated-catalog inspection confirms both exact index definitions, the
nullable truthful historical columns, the current-insert guard, and immutable
Audit trigger. There are no prepared transactions, non-idle sessions, or
residual `patch051_m5_plan_*` schemas. The disposable shared test database
does retain committed test-fixture rows (94 Audit rows total, including 24
from this run) but no transactional residue; that non-pristine fixture corpus
does not affect the unique-schema M5 proof. No cleanup is required for this
authorized disposable environment; a future pristine-baseline run would need
separate reset/recreation authority.

The root-relative database-role source-inspection test remains non-runnable in
the backend image's `/app` mount because the repository `postgres/` path is
not mounted. Direct source inspection remains the applicable evidence. This
is an existing Docker harness observation, not an M5 or privilege defect.
