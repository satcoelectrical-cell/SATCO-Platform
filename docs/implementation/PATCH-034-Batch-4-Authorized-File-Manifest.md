# PATCH-034 — Batch 4 Authorized File Manifest

## 1. Governance State

| Item | State |
|---|---|
| PATCH | PATCH-034 — Engineering Organizational Memory |
| Batch | Batch 4 — Unit of Work, Commands, and Reliability |
| Steps | S07–S10 only |
| Batches 1–3 | HUMAN ACCEPTED / COMPLETE |
| Human Batch 4 preparation authority | GRANTED |
| Batch 4 implementation authority | NOT GRANTED |
| Batch 5 and later authority | NOT GRANTED |

This document is the complete and exclusive Batch 4 implementation boundary.
It authorizes no implementation until separate Human Batch 4 implementation
authority is granted.

## 2. Repository and Dependency Assessment

The accepted Batch 1 contracts already provide the four mutation commands,
closed outward results, Audit and rejection-Audit records, Domain Event/outbox
payloads, idempotency keys/lookups/stored results, final-recheck request, and
the inward service/UoW protocols. The accepted Aggregate already owns admit,
successor, withdrawal, supersession, immutability, audience and lineage rules.

Batch 2 provides the no-commit root/history repository, root/history/outbox/
idempotency records, DB uniqueness and transition guards, immutable history,
optimistic standing persistence, deterministic database constraints, and role
separation. Batch 3 provides only canonical application adapters for accepted
Technical Reports and four provenance classes. No foreign canonical
repository, ORM, Session, or UoW is needed.

The minimum Batch 4 work is therefore a same-Session Organizational Memory UoW,
the four-command portion of the application service, narrowly required lock/
persistence operations on the existing repository, and focused transaction,
service, integration, and security evidence. Existing Aggregate and command
types are not authorized for amendment: any discovered contract gap is a stop
condition, not permission to redesign them.

## 3. Exact Authorized File Boundary

### 3.1 Production

| File | Action | Step | Authorized responsibility | Why required | Prohibited responsibility |
|---|---|---|---|---|---|
| `backend/app/repositories/organizational_memory_unit_of_work.py` | CREATE | S07, S09–S10 | Implement the concrete request-scoped same-Session UoW; memory authorization and locking final recheck; success `AuditLog` mapping; capability outbox staging; exact idempotency reservation/find/result persistence; bounded post-rollback rejection Audit; flush/commit/rollback; deterministic UUID-ordered root locking for supersession. | S07 requires concrete collaborators and one transaction boundary; S09 requires ordered locks; S10 requires exact persisted replay. | No canonical Technical Report/provenance persistence; no commit by repositories/recorders; no dispatch; no Batch 5 reads; no transport/composition. |
| `backend/app/services/organizational_memory_service.py` | CREATE | S08–S10 | Implement only `admit`, `create_successor`, `withdraw`, and `supersede`; trusted preauthorization; exact canonical source/provenance reads and final repeats; deterministic projection/manifest; UoW sequencing; expected versions; uniqueness/concurrency translation; exact Audit/history/outbox/idempotency staging; rollback-before-rejection-Audit; stable replay reconstruction with current reauthorization. | The accepted service port needs orchestration for the four Batch 4 mutations. | No `get_active`, `list_active`, `inspect_history`, pagination/continuation, transport, persistence ownership, implicit admission/supersession, or retained-snapshot fallback authority. |
| `backend/app/repositories/organizational_memory_repository.py` | MODIFY | S07, S09 | Add only repository-owned operations required by accepted command sequencing: bounded scoped/expected-version row locks, deterministic UUID-ordered pair locking, atomic side-record mappings where the accepted repository responsibility requires them, and conflict/uniqueness translation inputs. Preserve no-commit ownership and existing reads. | Existing repository does not expose the exact row-lock operations required for deterministic supersession and same-transaction compare/change. | No canonical foreign reads, authorization policy, service orchestration, commit/rollback, Batch 5 query expansion, pagination behavior, or schema redesign. |
| `backend/app/ports/organizational_memory.py` | MODIFY | S07–S10 | Make only already-accepted implementation-facing UoW/repository collaborators structurally explicit where concrete conformance requires it, including rejection-Audit association and deterministic root-lock signatures. Preserve all Batch 1–3 types and the Batch 3 logical provenance contract. | Current port omits the associated rejection recorder and exact lock surface needed to type the accepted sequencing. | No new business outcome, permission, read/pagination contract, canonical authority, or Batch 5+ operation. |

### 3.2 Tests

| File | Action | Step | Authorized responsibility | Why required | Prohibited responsibility |
|---|---|---|---|---|---|
| `backend/tests/test_organizational_memory_transaction.py` | CREATE | S07–S10 | Real PostgreSQL/UoW atomicity, structural conformance, repository no-commit, staged failure rollback, success side records, post-rollback rejection Audit, final recheck/locking, concurrency, duplicate admission/supersession, and exact persisted replay evidence. | Required by the accepted Plan and IDS reliability matrix. | No API, pagination, dispatch, migration redesign, or fake-only transaction proof. |
| `backend/tests/test_organizational_memory_service.py` | CREATE | S08–S10 | Four command semantics, Human/operation authority, lifecycle/lineage rules, expected-version conflicts, idempotency mapping/replay/conflict, revocation before replay, later-state replay stability, and prohibited side-effect evidence. | Required application-level evidence for the four mutations. | No Batch 5 read operations or Batch 6 transport behavior. |
| `backend/tests/test_organizational_memory_contracts.py` | MODIFY | S07, S10 | Add only structural/runtime conformance evidence for the amended inward UoW/repository signatures and preservation of exact stored-result mappings. | The accepted Batch 1 port is modified and must remain materially protected. | No contract redesign or weakening of Batch 1 evidence. |
| `backend/tests/test_organizational_memory_integration.py` | MODIFY | S08–S10 | Prove initial and immediately-pre-commit repeated accepted-source/provenance reads, exact projection/digest preservation, replay reauthorization, and canonical failure propagation through service orchestration. | Required to prove final canonical rechecks use Batch 3 application adapters without foreign persistence. | No modification of canonical capability implementation; no Batch 5 reuse/read behavior. |
| `backend/tests/test_organizational_memory_security.py` | MODIFY | S07–S10 | Operation-specific authority, current membership/scope/audience final recheck, revocation races, protected duplicate/authority outcomes, bounded rejection Audit, plaintext exclusion, and Audit-failure isolation. | Required by the IDS security and failure-ordering matrix. | No HTTP authentication tests, pagination, hidden counts, or later-batch behavior. |

The exact Batch 4 implementation boundary is:

```text
CREATE backend/app/repositories/organizational_memory_unit_of_work.py
CREATE backend/app/services/organizational_memory_service.py
MODIFY backend/app/repositories/organizational_memory_repository.py
MODIFY backend/app/ports/organizational_memory.py
CREATE backend/tests/test_organizational_memory_transaction.py
CREATE backend/tests/test_organizational_memory_service.py
MODIFY backend/tests/test_organizational_memory_contracts.py
MODIFY backend/tests/test_organizational_memory_integration.py
MODIFY backend/tests/test_organizational_memory_security.py
```

No other production, test, migration, configuration, design, or governance
file is authorized for Batch 4 implementation.

## 4. S07–S10 Mapping

### S07 — UoW Collaborators and Atomic Side Records

- One request-scoped memory Session owns repository, final-recheck, success
  Audit, standing history, outbox, and idempotency staging.
- Repository/recorders may flush or stage but never commit.
- The associated rejection recorder is usable only after authoritative rollback
  and has its own bounded transaction; its failure never replaces the original
  protected exception/result.
- Runtime implementation must structurally satisfy the accepted UoW port.

### S08 — Admission and Successor Commands

- Implement explicit Human `admit` and `create_successor` only.
- Perform trusted preauthorization, exact accepted-source and provenance reads,
  deterministic projection construction, then repeat source/provenance checks
  before final shared-authority locking and mutation.
- Enforce canonical source uniqueness, audience/scope compatibility, zero-or-one
  predecessor, and successor creation without implicit supersession.
- Commit root/history/Audit/outbox/idempotency exactly once or roll all back.

### S09 — Withdrawal and Explicit Supersession

- Implement only active-to-withdrawn and explicit active-to-superseded Human
  transitions.
- Enforce expected versions and terminal immutability.
- For supersession, authorize both identities, lock roots by ascending UUID,
  repeat both canonical source reads, validate replacement/predecessor
  compatibility, and mutate only the predecessor.
- Exactly one concurrent command may win; the replacement remains active.

### S10 — Exact Idempotency Replay

- Preserve the mapping `admit→admit.v1`, `withdraw→withdraw.v1`,
  `create_successor→create_successor.v1`, `supersede→supersede.v1`.
- Persist only the accepted versioned, bounded (≤1 KiB), plaintext-free safe
  result atomically with the mutation.
- Reauthorize current actor/source/subject before every completed replay.
- Reconstruct the original operation result without substituting later
  Aggregate standing/version; mismatched fingerprints and pending reservations
  return the accepted stable conflict outcome.
- Denied replay produces no mutation, history, success Audit, outbox, or new
  idempotency result.

## 5. Prerequisites and Dependencies

| Dependency | Status |
|---|---|
| PATCH/Architecture/QG-M1/EDS/IDS/Plan/IRR chain | SATISFIED |
| Batches 1–3 Human accepted and complete | SATISFIED |
| Pure Aggregate and closed mutation/result contracts | SATISFIED |
| PostgreSQL schema, DB guards, role separation and no-commit repository | SATISFIED |
| Accepted-report and four provenance application adapters | SATISFIED |
| Existing shared `AuditLog` schema supports accepted mapping | SATISFIED |
| Capability-owned outbox/idempotency/history tables | SATISFIED |
| Foreign canonical persistence access | NOT REQUIRED / PROHIBITED |

Implementation must start from current sole Alembic head `e03400000001`; Batch
4 creates no migration and may not alter schema or roles.

## 6. Transaction and Reliability Evidence Expectations

Independent review must have executable evidence for:

1. Concrete UoW structural/runtime conformance and same-Session identity for
   repository, final recheck, success Audit, outbox, and idempotency.
2. Atomic successful admission/successor/withdrawal/supersession including root,
   standing history, shared Audit, outbox, and completed idempotency row.
3. Injected failure after reservation, root mutation, history, Audit, outbox,
   idempotency result, flush, and before commit restores exact pre-state.
4. Rejection Audit is closed, bounded, plaintext-free, permitted only after
   rollback, and failure-isolated.
5. Final source/provenance/operation authority and mutable User/Organization/
   membership/Workspace/Project/audience predicates are rechecked and locked at
   the accepted point immediately before compare-and-change/commit.
6. Concurrent duplicate admission has one canonical winner; concurrent stale
   transitions and supersession have one winner; UUID lock ordering is stable.
7. Exact idempotency pairs, 1 KiB limit, schema/fingerprint binding, pending and
   mismatch conflict, later-state replay stability, revocation denial, and no
   replay side effects/plaintext.
8. Repository no-commit and DB direct-SQL guards from Batch 2 remain preserved.
9. Batch 1 contracts, Batch 2 persistence, and Batch 3 canonical integrations
   remain passing.

Required execution gates are focused Batch 4 service/transaction/security/
integration tests, affected Batch 1–3 Organizational Memory regressions,
relevant Technical Report/provenance and persistence regressions, static/import
validation, exact-scope/prohibited-pattern validation, and `git diff --check`.

## 7. Explicit Exclusions and Scope Control

Batch 4 may not implement or test as a Batch 4 deliverable:

- `get_active`, `list_active`, `inspect_history`, linked historical disclosure,
  active listing, filters, totals, pagination, continuation, or reuse (Batch 5);
- dependency composition, router, API, main registration, HTTP authentication,
  or transport serialization (Batch 6);
- new migration/schema/role/configuration behavior;
- canonical foreign repository/ORM/Session/UoW access or canonical mutation;
- outbox dispatch, frontend/UI, AI/Copilot, semantic/vector/graph retrieval,
  other source classes, synthesis, cross-Organization sharing, autonomous
  admission/reuse, enterprise boards, or any deferred capability.

Scope validation must compare the Batch 4 changed-path set exactly with Section
3, scan production code for foreign persistence and later-batch imports, and
confirm unrelated worktree changes remain untouched.

## 8. Stop Conditions

Stop and report BLOCKED if:

1. accepted contracts require an IDS/EDS/PATCH semantic change;
2. any foreign canonical repository, ORM, Session, UoW, policy implementation,
   direct SQL, or mutation is needed;
3. final source/provenance or shared mutable authority cannot be repeated and
   locked at the accepted sequencing point;
4. concrete collaborators require different authoritative Sessions;
5. shared `AuditLog`, migration, schema, database role, or configuration must
   change;
6. repository or recorder must commit independently;
7. rollback leaves any root/history/Audit/outbox/idempotency success side record;
8. rejection Audit can precede rollback or replace the original protected result;
9. exact replay needs current-state substitution or protected plaintext storage;
10. deterministic one-winner concurrency or UUID lock ordering cannot be proven;
11. a file outside Section 3 is required;
12. Batch 5+ or deferred behavior becomes necessary; or
13. any required focused/regression/static/scope/`git diff --check` gate fails.

## 9. Readiness and Authority

All accepted S07–S10 contracts, persistence foundations, and canonical
application boundaries exist. The nine-file implementation boundary is
coherent and minimal.

Batch 4 implementation readiness: READY

Batch 4 implementation authority: NOT GRANTED

Batch 5 authority: NOT GRANTED

Exact next governance action: obtain explicit Human Batch 4 implementation
authority for the exact nine-file boundary, then implement S07–S10 only.
