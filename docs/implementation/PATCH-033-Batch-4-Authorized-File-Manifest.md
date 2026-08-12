# PATCH-033 — Batch 4 Authorized File Manifest

## 1. Document Control

| Field | Value |
|---|---|
| PATCH | PATCH-033 — Engineering Knowledge Graph Integration |
| Batch | Batch 4 — Regression and Final Evidence |
| Steps | S06–S07 |
| Batches 1–3 | ACCEPTED / COMPLETE |
| Preparation authority | GRANTED |
| Batch 4 execution authority | NOT GRANTED |
| Delivery authority | NOT GRANTED |
| PATCH closure authority | NOT GRANTED |
| Manifest status | COMPLETE — READY FOR HUMAN BATCH 4 EXECUTION AUTHORITY |

This manifest authorizes no validation execution, final review, delivery, or
closure. It defines the exact documentation-only mutation boundary for a later
separately authorized Batch 4 run.

## 2. Exact Authorized File Boundary

| Operation | Exact path | Step | Exact purpose |
|---|---|---|---|
| CREATE | `docs/reviews/PATCH-033-Implementation-Validation-Evidence.md` | S06–S07 | Record reproducible commands, environment, exact results/counts, full regression, static/security/scope evidence, historical finding dispositions, deferred exclusions, and final QG-M1 assessment. |
| CREATE | `docs/reviews/FR-033-Engineering-Knowledge-Graph-Integration.md` | S07 | Package the bounded implementation manifest, accepted governance chain, Batch 1–3 review history, validation-evidence references, unresolved findings/debt, and readiness questions for an Independent Final Implementation Review. It must remain a review package and must not record an unperformed final-review verdict or Human authority. |
| MODIFY | `docs/patches/PATCH-033.md` | S07 | Record Batch 1–3 as ACCEPTED / COMPLETE, Batch 4 S06–S07 execution results when actually authorized and complete, validation-package references, and final-review readiness only. Preserve all historical review/remediation transitions and retain delivery/closure authority as NOT GRANTED. |

No production, test, migration, configuration, accepted ADR/EDS/IDS/plan,
manifest from an earlier batch, or prior review artifact may be modified.

## 3. Exact S06 Scope — Regression, Static, and Scope Evidence

An authorized S06 run must execute and record all of the following with zero
failures.

### 3.1 Focused executable-V1 regression

- `backend/tests/test_engineering_knowledge_graph_contracts.py`;
- `backend/tests/test_engineering_knowledge_graph_service.py`;
- `backend/tests/test_engineering_knowledge_graph_security.py`;
- `backend/tests/test_engineering_knowledge_graph_api.py`.

Evidence must prove exact `EngineeringObjectResponse` projection parity,
discriminator-only `node_type`, one-node success, four closed outcomes,
payload-free failures, authorization-before-disclosure, zero/one canonical-read
bounds, optional scope equality, read-only behavior, real authenticated
Organization context, request-scoped composition, and the single-route surface.

### 3.2 Adjacent canonical regressions

Run the current repository suites covering:

1. authentication and authenticated Organization context;
2. Project Organization scope and Project application behavior;
3. Engineering Workspace authorization and scope;
4. Engineering Object schemas, service, API, repository, transaction, and
   aggregate behavior;
5. Engineering Relationship service/API/repository/transaction behavior;
6. Evidence service/API/repository/transaction behavior;
7. Engineering Experience Capture contracts/service/security/API/repository/
   transaction behavior;
8. Engineering Journal contracts/service/security/API/performance behavior;
9. Technical Report aggregate/schema/repository/transaction/service/security/
   API/migration/database-role behavior;
10. Audit service/API and protected-record behavior.

Exact commands must use files that exist at execution time. A missing or
renamed suite is investigated and recorded; it does not authorize creating,
editing, skipping, or weakening a test.

### 3.3 Full backend regression

Run the complete backend suite in the repository-supported PostgreSQL test
environment:

```text
python -m pytest -q --disable-warnings
```

Record the exact passed/failed/skipped count, elapsed time, database identity,
and repository head. Zero failures are required. Tests may not be deselected,
marked, weakened, or retried selectively to claim the full gate.

### 3.4 Static and import validation

- compile every PATCH-033 production and focused-test module;
- import the registered application and generate OpenAPI successfully;
- verify the only EKG route is
  `GET /engineering-knowledge-graph/nodes/{node_id}`;
- verify Batch 1 inward contracts, Batch 2 adapters/service, Batch 3 composition
  dependency/router, and `main.py` import without cycles;
- record any warnings separately without converting failures to passes.

### 3.5 Authentication, authorization, and security validation

Verify materially that:

- missing/invalid credentials and inactive User fail before canonical reads;
- disabled, inactive, missing, ambiguous, and nonmember Organization context
  fail before canonical reads;
- Organization is server-derived and cannot be supplied as client authority;
- nonexistent, inaccessible, revoked, and cross-scope objects use stable
  protected outcomes;
- optional Project/Workspace mismatch is checked only against an authorized
  canonical response and exposes no projection;
- success discloses exactly the authorized canonical projection;
- protected results, errors, logs, diagnostics, OpenAPI, and route metadata do
  not disclose protected identities, fields, denial causes, SQL, stack detail,
  plaintext, hidden totals, or path information;
- all graph reads leave authoritative state and write-side tables unchanged.

### 3.6 Exact-scope and prohibited-pattern checks

Verify the cumulative PATCH-033 implementation contains only these eleven
unique production/test paths:

1. `backend/app/schemas/engineering_knowledge_graph.py`;
2. `backend/app/ports/engineering_knowledge_graph.py`;
3. `backend/tests/test_engineering_knowledge_graph_contracts.py`;
4. `backend/app/adapters/engineering_knowledge_graph.py`;
5. `backend/app/services/engineering_knowledge_graph_service.py`;
6. `backend/tests/test_engineering_knowledge_graph_service.py`;
7. `backend/tests/test_engineering_knowledge_graph_security.py`;
8. `backend/app/dependencies/engineering_knowledge_graph.py`;
9. `backend/app/api/v1/routers/engineering_knowledge_graph.py`;
10. `backend/app/main.py`;
11. `backend/tests/test_engineering_knowledge_graph_api.py`.

The composition dependency may privately construct existing canonical
infrastructure. All other EKG production layers must be free of direct ORM,
repository, Session, UoW, migration, transaction, Audit, idempotency, outbox,
cache, worker, or write ownership. The router must import none of those
implementations.

Scan all PATCH-033 production, tests, OpenAPI routes, and changed-file lists for
unauthorized:

- graph persistence, models, repositories, UoWs, migrations, state, lifecycle,
  writes, or transactions;
- additional node types or batch reads;
- edges, relationship frontiers, traversal, paths, depth/fan-out/cycles,
  pagination, continuation, or provenance;
- list, search, mutation, import, dispatch, or background routes;
- graph database, semantic/vector search, Organizational Memory, autonomous
  AI, frontend, EDS-030, or EDS-031 behavior;
- client-trusted Organization authority or separate inferred Project/Workspace
  authority;
- modification of canonical Engineering Object contracts or ownership.

### 3.7 Repository integrity and QG-M1

- run `git diff --check` against all tracked changes;
- whitespace-check every relevant untracked PATCH-033 file explicitly because
  ordinary `git diff --check` does not inspect untracked files;
- distinguish PATCH-033 files from unrelated local work and prove unrelated
  changes were untouched;
- complete final Manifesto/QG-M1 traceability against Human-first authority,
  canonical ownership, authorization-before-disclosure, modularity,
  reversibility/read-only behavior, bounded scope, and deferred-capability
  discipline.

## 4. Exact S07 Scope — Independent Review and Human Gate Package

After S06 passes, S07 may only:

1. finalize `PATCH-033-Implementation-Validation-Evidence.md` with exact
   commands/results, environment, file boundary, route boundary, finding
   disposition, deferred exclusions, remaining findings, and QG-M1 result;
2. create `FR-033-Engineering-Knowledge-Graph-Integration.md` as an evidence
   index for the later Independent Final Implementation Review;
3. update `PATCH-033.md` status metadata and detailed history to record Batches
   1–3 accepted, Batch 4 validation complete, and final-review readiness;
4. preserve the full FAIL → remediation → re-review history for Batch 2
   `B2-MAJ-01` and Batch 3 `B3-MAJ-01`;
5. preserve every deferred capability as non-executable and non-blocking;
6. leave Independent Final Review, Human quality gates, delivery authorization,
   commit, push, deployment, and closure unperformed and ungranted.

S07 may not promote PATCH-033 to implementation accepted, delivery authorized,
done, or closed.

## 5. Prerequisites and Dependencies

1. Batches 1–3 are Human ACCEPTED / COMPLETE and independently reviewable.
2. S01–S05 implementation remains unchanged after the accepted Batch 3
   focused re-review.
3. `B2-MAJ-01` and `B3-MAJ-01` remain resolved with preserved evidence.
4. The repository-supported PostgreSQL test environment is available and
   identifies the guarded test database correctly.
5. Current migrations are already at repository head; PATCH-033 requires and
   authorizes no migration execution or schema change.
6. Unrelated worktree changes can be isolated without modification, staging,
   stash, reset, clean, or deletion.
7. S07 may begin only after every S06 gate passes.

## 6. Stop Conditions

Stop Batch 4 and report BLOCKED without remediation if:

1. any focused, adjacent, full-regression, static/import, security, route,
   exact-scope, prohibited-pattern, whitespace, or QG-M1 gate fails;
2. any implementation, test, migration, configuration, accepted design, prior
   manifest, or prior review file would need modification;
3. an unauthorized or deferred route, DTO, operation, dependency, capability,
   persistence surface, write effect, or ownership transfer is found;
4. the current implementation differs from the independently reviewed Batch
   1–3 boundary;
5. historical FAIL/remediation/re-review evidence is missing or inconsistent;
6. the full suite cannot run in the guarded repository-supported environment;
7. validation evidence would contain credentials or protected engineering
   content;
8. unrelated work cannot be isolated and left untouched;
9. an Independent Final Review verdict or Human/delivery/closure authority
   would have to be inferred or promoted during evidence packaging.

No remediation is authorized in Batch 4. A failed gate requires a separately
governed focused remediation boundary.

## 7. Execution and Authority Decision

Batch 4 execution readiness: READY

Batch 4 execution authority: NOT GRANTED

Delivery authority: NOT GRANTED

PATCH closure authority: NOT GRANTED

The exact next action is a separate Human Batch 4 Execution Authority decision
against this manifest.
