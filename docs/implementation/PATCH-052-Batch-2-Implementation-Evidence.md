# PATCH-052 Batch-2 Implementation Evidence

## Control

| Field | Value |
|---|---|
| Authority | **HUMAN PATCH-052 BATCH-2 IMPLEMENTATION AUTHORITY: GRANTED** |
| Migration creation/execution | granted for one linear migration and only the named disposable PostgreSQL database |
| Scope | Electrical V1 plus the accepted shared additive cutover |
| Disposable database | `satco_platform_patch02022_test` |
| Production/customer database | no authority; no mutation performed |
| PATCH-053 / Batch 3+ | not started / not authorized |
| Original independent review | **FAIL / NOT ACCEPTED / INCOMPLETE — B2-052-MAJ-01** |
| Authorized resumed fresh re-review | **PASS / ACCEPTED / COMPLETE — B2-052-MAJ-01 CLOSED** |

## Chronological recovery record

The first Batch-2 run and its continuation were interrupted only by Codex usage limits. Their valid source and database work was preserved. The recovered checkpoint included migration `e05200000001`, the shared additive schema, the Electrical vertical, ADR-025 Identifier persistence, the Capture route, corrected descriptor-digest comparison, 223 focused legacy/backend passes, 9/9 frontend focused passes, and 6/6 then-current PostgreSQL passes. The last pre-interrupt defect was a stale exact route manifest; its correction was present but not yet rerun.

Resume reconciliation found unstaged dirty and untracked work, no staged files, no modified historical migration, no `e05200000002`, and no temporary schemas. The named disposable database existed at `e05200000001`, had 91 public tables, no application rows, no active/prepared transaction, and only its Alembic version row. This is recovered state **D — clean base-to-head migration complete**. It was not blindly recreated again.

The corrected exact route-manifest test passed 1/1. The stale host credential observation remained reproducible, so all PostgreSQL proof used an ephemeral backend test container on the Docker network with the already configured schema-owner credential; the credential was neither printed nor changed.

## Migration integrity and proofs

| Check | Result |
|---|---|
| Revision | `e05200000001` |
| Down revision | `e05100000006` |
| Source graph | one linear head, `e05200000001` |
| Corrective revision | none; no `e05200000002` |
| Historical M1-M6 | unchanged in the worktree |
| Clean base-to-head | recovered complete at an empty 91-table head; schema guards verified |
| `e05100000006 -> e05200000001` | passed with bounded representative legacy Object, accepted V1 Report, and Organizational Memory |
| Safe downgrade/re-upgrade | `e05200000001 -> e05100000006 -> e05200000001` passed while only contract-permitted legacy rows existed |
| Limited downgrade | migration refuses downgrade when PATCH-052 rows exist |
| Legacy origin | all three origin columns remained `NULL` |
| Fabricated Identifier | zero |
| Fabricated provenance | zero |
| Accepted Report rewrite | none; exact complete row JSON remained equal |
| Organizational Memory rewrite | none; exact complete row JSON remained equal |

The final empty head exposes the three Identifier tables, four nullable owner-origin triples, Object-level Context subject reference, 29 Identifier constraints/foreign keys/constraint triggers, 14 relevant Identifier/origin/Context indexes, and nine PATCH-052 origin/Identifier/Context triggers. `satco_runtime` has Identifier `SELECT/INSERT/UPDATE` and no `DELETE`. The final database has no application rows, active sessions, prepared transactions, or temporary PATCH-052 schemas.

## Implemented acceptance surface

- Electrical exact catalogs: 8 Objects, 7 Relationships, 5 Context kinds, 9 engineering inputs, 4 Evidence requirements, 4 Deliverables, and 5 deterministic rules.
- Electrical Object creation atomically persists the Object, required primary Identifier, both outboxes, idempotency result, immutable origin, and Audit.
- Standalone Identifier create/replace/withdraw/reassign uses authorization-first owner scope, Object-before-Identifier locking, a 0..16 current bound, current uniqueness, retained lineage, physical-delete denial, Audit/outbox/idempotency in one UoW, and two fresh-UoW retries only for unique/serialization/deadlock SQLSTATEs.
- Idempotent replay returns the immutable originally committed response even after later Identifier lifecycle changes.
- Package-origin primary replacement/reassignment preserves the exact descriptor-required kind and matching origin; incompatible owner alternates fail closed.
- Relationship endpoint authorization precedes tuple resolution; Capture remains canonical provenance only; Deliverable carries exact immutable origin.
- Object-level Context, selected Evidence/readiness, Technical Report V2 Object/Capture/Relationship historical bases and complete Identifier snapshots are additive. V1 Report and Organizational Memory semantics remain byte-compatible.
- Only Electrical execution is available. Instrumentation and Control & Automation remain the inert compiled Batch-1 shells; no Batch-3/4/5 workflow was added.

## Defects and remediation chronology

1. Before this resume, descriptor digest wrapper identity and the absent Capture route were corrected; the exact route manifest remained to be rerun and then passed.
2. The first new migration-proof fixture used the wrong Organization for the repository test event; it failed visibly, was corrected, and the two migration proofs passed.
3. Two accidentally overlapping broad test containers produced invalid noisy failures. Both exited, their residue was removed only from the disposable database, and all subsequent suites ran serially in named containers.
4. Remediation cycle 1 fixed exact Engineering Knowledge Graph projection parity for the additive origin triple and updated the frozen Object-type expectation. Focused result: 31/31; serialized non-migration result: 1,822/1,822.
5. The first migration-aware full run produced 1,933/1,935. Its two failures were stale accepted-schema tests: Relationship columns omitted the origin triple, and the migration proof reinserted an existing shared test Organization. Both were corrected. A truthful current project-configuration head was also added to the fresh-session fixture after the commit-time Workspace binding guard exposed the prior savepoint weakness.
6. Remediation cycle 2 changed new Identifier/Object/Relationship/Capture idempotency to persist and replay immutable response snapshots. Focused result: 11/11.
7. Remediation cycle 3 enforced package-required primary kind/origin, corrected Object-before-Identifier lock order, and added bounded fresh-session retry for only `23505`, `40001`, and `40P01`. Focused result: 11/11.

No failed or interrupted evidence above has been erased.

## Validation matrix

| Validation | Final result |
|---|---|
| Corrected route manifest | **1 passed** |
| Real PostgreSQL consolidated Batch-2/migration/concurrency/plan set | **14 passed** |
| Focused cycle-1 compatibility | **31 passed** |
| Focused cycle-2/3 Identifier and concurrency | **11 passed** per cycle |
| Full backend, all migration tests included | **1,937 passed** |
| PATCH-052 Batch-1 plus PATCH-051 Registry/remediation | **32 passed** (4 + 28) |
| Frontend affected | **21 passed** |
| Frontend full | **93 passed** |
| TypeScript typecheck | **passed** |
| Frontend production build | **passed** |
| Python compileall/import through full collection | **passed** |
| Source Alembic head | **`e05200000001 (head)`** |
| `git diff --check` | **passed** |
| Staged files | **none** |

The full backend run emitted existing deprecation/serializer warnings but no test failure. No warning is treated as a production SLO claim.

## Concurrency, transaction, and query-plan evidence

Real independent Sessions started duplicate same-scope Identifier creation and same-predecessor replacement concurrently. Each race produced exactly one success and one protected conflict; the final set had one value winner, one primary, one successor, complete Audit/outbox/idempotency, and no partial writes. Forced Evidence-FK failure removed Object, Identifier, Audit, outbox, and idempotency together. Repositories expose no commit; the UoW owns commit/rollback and every retry opens a fresh UoW.

On bounded representative Electrical data, `ANALYZE` plus structural `EXPLAIN` proof selected:

- `uq_engineering_identifier_current_value` for current/scoped uniqueness lookup;
- `ix_engineering_identifier_current_set` for Object current set and Report Identifier snapshot;
- `ix_engineering_objects_origin` for Object provenance;
- `ix_engineering_context_subject_refs_object_id` for Object Context projection; and
- `ix_engineering_deliverables_origin` for Deliverable readiness.

This proves structural/index compatibility on bounded data. It does not claim a production latency SLO, and a tiny-fixture sequential scan without the structural planner setting would not itself be classified as a defect.

## Security and non-disclosure

The full and focused suites cover authenticated Organization derivation, Project/Workspace/Object authorization, foreign endpoint/object/Identifier/Context/Capture/Evidence/Deliverable/Report/package protected outcomes, no candidate count/value/catalog/provenance/rule-result leakage, signed actor/Object/project-bound Identifier cursors, and runtime no-delete grants. New package resolution occurs only after owner-scope authorization. No production/customer database, deployment, Registry activation, staging, commit, push, PATCH-053, or Batch-3+ implementation occurred.

## Implementation disposition

The evidence package is complete, but the subsequent fresh independent review did not accept the implementation. It found **B2-052-MAJ-01**, a blocking mismatch between the accepted package-mutation transaction contract and the actual Electrical Object/Relationship/Capture/Deliverable paths: configuration-first locking, post-lock fresh package authority, replay-after-authority, governed cross-aggregate UoW seams, and bounded fresh-session package retries are not all implemented or proven. The three authorized remediation cycles recorded above were already consumed, so no fourth implementation change was made.

The authoritative review is `docs/reviews/PATCH-052-Batch-2-Independent-Implementation-Review.md`. PATCH-052 remains registered/open; Batch 2 is not accepted; Batch 3 and PATCH-053 remain not started/not authorized. The next Human decision is whether to grant one additional bounded Batch-2 remediation cycle for B2-052-MAJ-01.

## Human-authorized additional remediation cycle — interrupted and resumed

Human granted one additional focused Batch-2 remediation cycle for
`B2-052-MAJ-01` and one fresh independent re-review. The first execution of
that additional cycle was interrupted only by the Codex usage limit. Repository
reconciliation on 2026-09-09 recovered two newly created but not yet integrated
files: `Patch052OperationUnitOfWork` and the package mutation lock/authority
guard. No remediation tests, evidence update, or re-review update had yet been
made. Resuming this work is continuation of that same additional cycle, not a
new cycle.

The resumed implementation made the recovered UoW the commit/rollback/Session
owner for Electrical Object, Relationship, Capture, rule-Audit, and package
Deliverable mutations. Each attempt now opens a fresh Session and transaction;
owner repositories and Audit/outbox staging do not commit. The governed lock
sequence is Registry/configuration authority first, then mutable actor/tenant
authority, Project, Workspace, target Object UUIDs in lexical order, and only
then idempotency/Audit. Current authority and Workspace binding are checked
after those locks and before replay or write. Completed replay uses the stored
immutable response snapshot only after current authority succeeds.

Only SQLSTATE `23505`, `40001`, and `40P01` receive two bounded retries. Every
retry opens a new UoW; authorization, protected-not-found, package-unavailable,
and deterministic validation outcomes do not retry. Package Deliverable now
uses the same outer UoW and stages root, revision, history, idempotency, both
Audits, and outbox before its single commit. Object creation likewise stages
Object, required primary Identifier, idempotency, Audit, and both outboxes in
one transaction.

## Resumed focused proof

The final focused PostgreSQL run passed **21/21**. It includes:

- configuration-change-wins and Workspace-rebind-wins fail-closed races;
- mutation-wins followed by the blocked configuration writer proceeding;
- concurrent user/auth-version revocation before post-lock authorization;
- retry-after-revocation with a distinct Session on retry;
- three-attempt retry exhaustion with three distinct Sessions;
- concurrent duplicate package mutation converging on one immutable result;
- replay denial after authority/configuration change;
- database rejection of a stale Project-head/Workspace binding at commit;
- Object plus required primary Identifier, Audit, idempotency, and both outboxes
  rolling back together;
- Deliverable root/revision/history, idempotency, both Audits, and outbox rolling
  back together; and
- the already-correct package-primary kind/origin and immutable replay proofs.

The smallest affected regression passed **57/57** across PATCH-052 Batch 1/2,
real-session concurrency, package API/transaction/service, and canonical
Deliverable contracts/service. An initial broad run used a backend-only mount;
it truthfully produced 1,929 passes and 18 failures, of which 17 were absent
repository-root operations/bootstrap fixtures and one exposed a minimal actor
test double without `auth_version`. The latter compatibility seam was repaired
without weakening real authenticated authority. The two targeted checks then
passed **2/2**. With the correct read-only repository-root mount, the final
serialized backend regression passed **1,947/1,947**.

Frontend source, public response DTOs, and frontend behavior were not changed
by this remediation. The previously recorded 93/93 frontend, typecheck, and
production-build results therefore remain the applicable accepted baseline and
were not redundantly rerun.

## Resumed final database and source state

The only accessed database was `satco_platform_patch02022_test`. Final direct
identity/cleanliness proof reported `e05200000001`, zero Object, Identifier,
Deliverable, and Registry rows, zero prepared transactions, zero temporary
schemas, and zero non-idle peer sessions. No production or customer database
was accessed or mutated. Source inspection reports exactly one Alembic head,
`e05200000001`; no `e05200000002` exists; no historical migration is modified.

## Final superseding disposition

The original FAIL and `B2-052-MAJ-01` record above remain historical facts.
The authorized resumed fresh re-review now supersedes the earlier open
disposition for current status:

`B2-052-MAJ-01`: **RESOLVED / CLOSED**

`PATCH-052 BATCH-2`: **IMPLEMENTATION ACCEPTED / COMPLETE**

`PATCH-052`: **REGISTERED / OPEN**

`PATCH-052 BATCH-3`: **ELIGIBLE FOR SEPARATE HUMAN AUTHORITY**

`BATCH-3 IMPLEMENTATION`: **NOT STARTED / NOT AUTHORIZED**
