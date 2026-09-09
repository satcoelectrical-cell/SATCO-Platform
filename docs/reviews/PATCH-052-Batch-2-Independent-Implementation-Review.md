# PATCH-052 Batch-2 Independent Implementation Review

## Review control

| Field | Result |
|---|---|
| Target | Actual final Batch-2 repository, migration, disposable-database evidence, tests, API, and frontend |
| Review mode | One fresh independent implementation review after the recorded implementation/remediation work |
| Original verdict | **FAIL / NOT ACCEPTED / INCOMPLETE** |
| Current authorized fresh re-review | **PASS / ACCEPTED / COMPLETE** |
| Current Critical / Major / Minor / Observation | **0 / 0 / 0 / 2** |
| Cycle accounting | **three original cycles plus the same Human-authorized additional cycle resumed after interruption** |
| Current blocking findings | **0** |

## Actual-result review

The review inspected migration `e05200000001`, its downgrade guard, the final database inventory, the ADR-025 Identifier model/repository/UoW/service/API, immutable origin triples, the Electrical descriptor and operational rules, Object/Relationship/Capture/Context/Evidence/Deliverable/Report V2 integrations, Audit/outbox/idempotency records, readiness/conformance code, static frontend wiring, authorization/tenant tests, real-PostgreSQL concurrency/query-plan tests, and the final validation results. It also independently compared the mutation implementation with the accepted IDS and Implementation Plan instead of relying on the implementation evidence as a conclusion.

The migration remains a single additive revision from `e05100000006`; no corrective revision or historical migration edit exists. The clean/upgrade/downgrade proofs, legacy-null/no-fabrication preservation, accepted Report/Memory preservation, schema constraints/indexes/triggers/grants, Identifier races, query plans, full backend/frontend results, and Batch-1/PATCH-051 regressions are credible and passing. No Instrumentation, Control & Automation, combined Batch-5, PATCH-053, production/customer database, staging, commit, or push action was introduced by this Batch-2 continuation.

## Blocking finding

### B2-052-MAJ-01 — Package mutation transaction, lock, retry, and fresh-authority contract is incomplete

**Classification:** Major / blocking.

The accepted IDS requires `Patch052OperationUnitOfWork` to own every cross-aggregate package mutation, with staging-only owner repositories, exactly one commit, configuration-revision-first lock order, fresh authorization after locking, rollback on revocation/staleness, and bounded fresh-session retry. The universal Plan likewise requires idempotency, post-lock fresh authority, prescribed lock order, transactional Audit/outbox, and two fresh-session retries for every mutation.

The actual implementation does not fully implement that boundary:

- `ElectricalPackageService._scope` locks Project and Workspace before configuration; `_origin` then reads the configuration selection, current Registry release, and membership without row locks.
- Electrical Relationship creation locks Object endpoints before resolving configuration, the reverse of the prescribed configuration → Workspace → Object order.
- Electrical Object creation reads and returns a completed idempotency replay before `_origin`, so a replay does not recheck current package selection/Registry standing.
- Package Deliverable creation uses the existing Deliverable `_mutate` wrapper, whose idempotency replay occurs before its package handler checks Workspace binding, selection, Registry release, and membership. Those package-authority reads are also not locked.
- Electrical package mutations use direct Sessions/existing owner UoWs and have no governed fresh-session retry wrapper for unique/serialization/deadlock races. There is no implemented `Patch052OperationUnitOfWork` or the specified staging-only `stage_package_*` owner seam.

Consequently, the green tests prove atomic happy paths and two Identifier races, but do not prove the accepted cross-aggregate package lock/revocation/retry semantics. Static inspection shows that a completed Object or Deliverable replay can return before current package authority is revalidated, and concurrent Registry/configuration authority cannot be shown to be serialized according to the frozen lock order. This is an implementation defect inside the accepted Batch-2 contract, not an architecture ambiguity.

**Required remediation:** under renewed Batch-2 remediation authority, implement the frozen `Patch052OperationUnitOfWork`/staging seams or an exactly equivalent contract-preserving structure; lock configuration authority before Workspace/Object/Identifier/Deliverable rows; reauthorize after locks and before replay/commit; add the two allowed fresh-session retries; and add real-PostgreSQL revocation, replay-after-revocation, lock-order, package duplicate-create, and rollback tests. Then rerun focused, affected, migration-aware full backend, and fresh independent review.

No fourth remediation cycle was attempted because the granted maximum of three is already recorded as consumed.

## Non-blocking observations

1. **B2-052-OBS-01 — local credential path.** The long-lived local backend/host credential remains stale. Isolated PostgreSQL proofs succeeded through the authorized disposable container path without printing or changing the credential.
2. **B2-052-OBS-02 — existing warnings.** The definitive backend run passed with existing Pydantic/FastAPI/serializer deprecation warnings. They are non-blocking and are not performance/SLO evidence.

## Validation assessment

The recorded validation remains: route manifest 1/1; consolidated real PostgreSQL 14/14; final focused Identifier/concurrency 11/11; full backend 1,937/1,937; Batch-1 4/4; PATCH-051 28/28; frontend affected 21/21 and full 93/93; typecheck, production build, compileall, Alembic-head, and `git diff --check` pass. These results do not waive the unimplemented mandatory package-mutation concurrency/authority contract.

## Disposition

PATCH-052 BATCH-2 INDEPENDENT IMPLEMENTATION REVIEW:
FAIL / NOT ACCEPTED / INCOMPLETE

PATCH-052 BATCH-2:
IMPLEMENTATION NOT ACCEPTED / INCOMPLETE

PATCH-052:
REGISTERED / OPEN

PATCH-052 BATCH-3:
NOT ELIGIBLE WHILE BATCH-2 IS INCOMPLETE

BATCH-3 IMPLEMENTATION:
NOT STARTED / NOT AUTHORIZED

PATCH-053:
NOT STARTED / NOT AUTHORIZED

The exact next Human decision is whether to grant one additional, separately bounded PATCH-052 Batch-2 remediation cycle for B2-052-MAJ-01. Batch-3 authority is not the next eligible decision.

## Authorized resumed fresh independent re-review — 2026-09-09

This section preserves the original FAIL above and records the separately
authorized fresh re-review of the final resumed implementation. The reviewer
re-read the frozen IDS transaction section and actively attempted to falsify
UoW ownership, lock ordering, configuration-first locking, post-lock authority,
replay authority and immutability, retry classification/freshness, atomicity,
and revocation/configuration/Workspace races.

### Falsification results

- **UoW ownership:** PASS. `Patch052OperationUnitOfWork` opens one explicit
  outer transaction per attempt, owns the sole commit/rollback, and closes the
  Session. Object/Identifier and Deliverable repositories remain staging-only;
  Audit and outbox creation only call `Session.add`.
- **Lock ordering/configuration first:** PASS. The shared Registry guard and
  current Registry, Organization configuration, Project head/revision/selection,
  profile, descriptor, and membership rows are locked before actor/tenant,
  Project, Workspace, Object, Identifier, Deliverable, and idempotency rows.
  Relationship endpoint UUIDs are selected in deterministic lexical order.
- **Post-lock authority/non-disclosure:** PASS. Active User/auth-version,
  selected enabled Organization membership, active Organization, Project scope,
  role/assignment/Workspace membership, package standing, configuration head,
  and Workspace binding are re-read under transaction locks. Revoked or stale
  callers fail before idempotency replay is read.
- **Replay:** PASS. Object, Relationship, Capture, Identifier, and Deliverable
  commands persist immutable response JSON. Replay occurs after current
  authority and returns that JSON rather than reconstructing mutable rows.
  Replay after auth-version revocation and configuration disablement is denied;
  replay after later Identifier supersession still returns the original
  committed primary-Identifier response.
- **Retry:** PASS. Only unique, serialization, and deadlock SQLSTATEs (`23505`,
  `40001`, `40P01`) are retried, at most twice. Focused proof observed three
  distinct Sessions at exhaustion and a distinct second Session whose fresh
  authority check rejected an intervening revocation. Protected, unavailable,
  and deterministic validation results do not enter the retry branch.
- **Cross-aggregate atomicity:** PASS. Forced failure proves Object, required
  primary Identifier, Audit, idempotency, and both outboxes roll back together.
  A separate commit-boundary failure proves Deliverable root, revision, history,
  idempotency, both Audits, and outbox roll back together.
- **Race behavior:** PASS. Real independent PostgreSQL Sessions prove
  configuration-change-wins, mutation-wins, user revocation-wins,
  retry-after-revocation, Workspace-rebind-wins, concurrent duplicate package
  convergence, and database rejection of a stale head/Workspace binding.
- **Primary-Identifier invariant:** PASS. Existing database cardinality guards
  enforce one current primary for a package Object, while service replacement,
  withdrawal, and reassignment preserve the descriptor-required kind and exact
  package origin.

### Validation reviewed

- focused final PostgreSQL transaction/concurrency: **21/21 passed**;
- affected package/Deliverable regression: **57/57 passed**;
- targeted broad-run compatibility/migration follow-up: **2/2 passed**;
- correctly mounted final full backend: **1,947/1,947 passed**;
- Python compileall: **passed**;
- Alembic source and database head: **`e05200000001`**;
- frontend 93/93, typecheck, and build: reused accepted baseline because no
  frontend or public response-contract behavior changed.

The final disposable database was empty of Object, Identifier, Deliverable, and
Registry application rows, with zero prepared transactions, temporary schemas,
or non-idle peer sessions. No production/customer database was accessed. No
new or historical migration was created or modified.

### Fresh verdict

Critical: **0**
Major: **0**
Blocking Minor: **0**
Observation: **2** (the unchanged local credential-path and warning observations)

`B2-052-MAJ-01`: **RESOLVED / CLOSED**

`PATCH-052 BATCH-2`: **IMPLEMENTATION ACCEPTED / COMPLETE**

`PATCH-052`: **REGISTERED / OPEN**

`PATCH-052 BATCH-3`: **ELIGIBLE FOR SEPARATE HUMAN AUTHORITY**

`BATCH-3 IMPLEMENTATION`: **NOT STARTED / NOT AUTHORIZED**
