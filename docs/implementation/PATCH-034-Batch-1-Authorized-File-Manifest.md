# PATCH-034 — Batch 1 Authorized File Manifest

## 1. Manifest Control

| Field | Value |
|---|---|
| Related PATCH | PATCH-034 — Engineering Organizational Memory |
| Authorized batch | Batch 1 — Contracts and Aggregate Foundation |
| Implementation steps | S01–S02 only |
| Governing EDS | EDS-034 — ACCEPTED / COMPLETE |
| Governing IDS | IDS-034 — ACCEPTED / COMPLETE |
| Governing plan | Implementation-Plan-034 — ACCEPTED / COMPLETE |
| IRR-034 | PASS / Batch 1 READY |
| Human Batch 1 preparation authority | GRANTED |
| Manifest status | COMPLETE / READY FOR HUMAN IMPLEMENTATION AUTHORITY |
| Batch 1 implementation authority | NOT GRANTED |
| Batch 2 authority | NOT GRANTED |
| Later Batch authority | NOT GRANTED |
| Migration authority | NOT REQUIRED / NOT GRANTED |
| Commit / push authority | NOT GRANTED |
| Date | 2026-08-12 |

This manifest is the exact prospective S01–S02 file boundary. Creating it does
not authorize implementation.

## 2. Batch Boundary

### 2.1 S01 — Closed Contracts and Canonical Representation

S01 may define only the accepted closed vocabularies, immutable value objects,
actor and trusted scope, exact source and provenance identities, seven command/
query request families, closed results, standing-specific history DTOs,
operation-specific provenance authorization contracts, canonical snapshot and
digest contracts, four bounded idempotency stored-result variants, inward/outward
Protocols, and internal non-transport exceptions required by IDS-034.

S01 includes pure canonical serialization and digest helpers only where their
placement in an authorized Batch-1 module is necessary to make the accepted
contract executable and independently testable.

### 2.2 S02 — Aggregate Lifecycle and Digest Foundation

S02 may implement only the pure Organizational Memory Aggregate and accepted
domain invariants: one canonical Organization/source/version identity,
deterministic semantically non-transformative admitted projection, immutable
admitted state, exact digest coherence, `active -> withdrawn | superseded`,
terminal standing, zero-or-one predecessor, successor creation distinct from
supersession, and closed non-plaintext Domain Event construction.

S02 owns no persistence, transaction, authorization implementation, canonical
adapter, service orchestration, transport, or database behavior.

## 3. Exact Authorized Production Files

| Path | State | Step | Allowed responsibility |
|---|---|---|---|
| `backend/app/enums/organizational_memory.py` | CREATE | S01 | Define only IDS-034 closed standing, operation, outcome, provenance-class, event, Audit/rejection, and idempotency discriminator vocabularies. No database or transport enums. |
| `backend/app/models/organizational_memory_command.py` | CREATE | S01 | Define frozen actor/scope, exact Technical Report source identity/version, command/query metadata and requests, provenance authorization request/results, safe history/value records, non-plaintext events, and the four exact bounded stored replay representations. No orchestration or I/O. |
| `backend/app/schemas/organizational_memory.py` | CREATE | S01 | Define strict external/application DTOs for seven operations, snapshot/provenance-safe projections, lifecycle-specific history detail, active listing/page contracts, protected optional links, and closed payload-free protected outcomes. Reject unknown fields and preserve IDS types/optionality/cardinality. |
| `backend/app/ports/organizational_memory.py` | CREATE | S01 | Define Protocols and exact signatures only for accepted source/provenance readers, repository/query records, authorization/final recheck, idempotency, Audit, outbox, clock, UoW, and seven-operation service boundary. No implementation, Session, SQLAlchemy, or commit behavior. |
| `backend/app/exceptions/organizational_memory.py` | CREATE | S01–S02 | Define only closed internal domain/contract errors needed for aggregate invariant enforcement and later translation to accepted results. No HTTP status, response body, infrastructure detail, or protected plaintext. |
| `backend/app/models/organizational_memory.py` | CREATE | S02 | Implement the pure Aggregate, exact admitted projection/manifest serialization and digest coherence, immutable accepted state, uniqueness identity, lifecycle transitions, lineage invariants, and closed event construction. No ORM mapping, repository, Session, persistence, or authorization decisions. |

Production file count: **6**.

All six proposed production surfaces are required by accepted S01–S02. None can
be removed without either combining unrelated schema/domain/port responsibilities
or leaving an accepted IDS contract or Aggregate invariant without an owned
implementation surface.

No existing production file is authorized for modification. Package
initializers remain unchanged; direct module imports are sufficient.

## 4. Exact Authorized Test Files

| Path | State | Step | Allowed responsibility |
|---|---|---|---|
| `backend/tests/test_organizational_memory_contracts.py` | CREATE | S01 | Prove enum/value-object/port/result closure, exact operation-to-`*.v1` stored-result mapping, fingerprint/schema/size/plaintext rules, provenance request variants, cardinality, optionality, and strict serialization. |
| `backend/tests/test_organizational_memory_schemas.py` | CREATE | S01 | Prove request/result discriminators, payload-free protected outcomes, lifecycle-specific history shapes, protected optional links, unknown-field rejection, bounds, and no transport/infrastructure leakage. |
| `backend/tests/test_organizational_memory_aggregate.py` | CREATE | S02 | Prove projection and digest golden vectors, semantic parity, canonical identity, lifecycle/terminal immutability, zero-or-one predecessor, successor-not-supersession, explicit supersession, event coherence, and failure atomicity of pure transitions. |

Test file count: **3**.

Test fixtures/helpers must remain local to these files. No existing test file or
shared fixture is authorized for modification.

## 5. Exact Nine-file Boundary

```text
CREATE backend/app/enums/organizational_memory.py
CREATE backend/app/models/organizational_memory.py
CREATE backend/app/models/organizational_memory_command.py
CREATE backend/app/schemas/organizational_memory.py
CREATE backend/app/ports/organizational_memory.py
CREATE backend/app/exceptions/organizational_memory.py
CREATE backend/tests/test_organizational_memory_contracts.py
CREATE backend/tests/test_organizational_memory_aggregate.py
CREATE backend/tests/test_organizational_memory_schemas.py
```

After separate Human Batch 1 implementation authority, implementation may
create exactly these nine files and may not modify any other path.

## 6. Prerequisites and Dependencies

| Prerequisite | Evidence | Status |
|---|---|---|
| PATCH-034 Architecture / QG-M1 | Accepted / PASS | SATISFIED |
| EDS-034 | ACCEPTED / COMPLETE; focused re-review PASS; Human Acceptance PASS | SATISFIED |
| IDS-034 | ACCEPTED / COMPLETE; final focused re-review PASS; Human Acceptance PASS | SATISFIED |
| Implementation-Plan-034 | ACCEPTED / COMPLETE; Independent Review PASS; Human Acceptance PASS | SATISFIED |
| IRR-034 | PASS; Batch 1 prerequisites satisfied; Batch 1 READY | SATISFIED |
| Technical Report source contracts | Accepted exact Human-accepted snapshot/historical-basis identities and typed application boundary exist | SATISFIED |
| Provenance identity contracts | Current Capture, Evidence, Engineering Object, and Engineering Relationship identities/enums exist for typed contract references | SATISFIED |
| Shared reliability contracts | Current Audit/outbox/idempotency/UoW conventions are reference inputs only; no implementation is required in Batch 1 | SATISFIED |
| Database/migration | Not required by S01–S02 | SATISFIED |

S02 depends on completed S01 types. Neither step depends on a memory table,
migration, repository implementation, canonical adapter, application service,
router, runtime role, or later-batch test fixture.

## 7. Focused Evidence Expectations

A separately authorized implementation must provide, within the three exact
test files:

1. exact closed enums and operation/result discriminators;
2. exact actor, trusted Organization scope, source/version, audience, lineage,
   provenance, command, query, result, history, event, Audit, and stored-replay
   field types, nullability, cardinality, and bounds;
3. canonical JSON determinism and digest golden vectors for admitted snapshot,
   provenance manifest, and projection binding;
4. proof that normalization is non-semantic and that paraphrase, omission,
   synthesis, inference, translation, or new technical meaning is rejected;
5. exact mapping `admit -> admit.v1`, `withdraw -> withdraw.v1`,
   `create_successor -> create_successor.v1`, and
   `supersede -> supersede.v1`, including every mismatched-pair negative;
6. stored replay canonical JSON at or below 1 KiB, version/fingerprint binding,
   deterministic reconstruction fields, and exclusion of content, rationale,
   provenance bodies, diagnostics, credentials, and exception text;
7. operation-specific provenance request shapes for Capture, Evidence,
   Engineering Object, and Engineering Relationship, including deterministic
   bounds and all-or-nothing result contracts without implementing adapters;
8. strict closed result variants and payload-free protected failure outcomes;
9. active, withdrawn, and superseded history DTO optionality, including
   protected predecessor/replacement slots;
10. Aggregate admission, withdrawal, successor, and supersession positives and
    invalid/terminal/version/lineage negatives;
11. immutable admitted content and history, exact active-to-terminal transition
    matrix, zero-or-one predecessor, and successor creation not implying
    supersession;
12. exact non-plaintext event construction and deterministic timestamps/version
    behavior supplied through accepted command values; and
13. static/import and exact-scope checks proving no later-batch capability.

Required validation after separately authorized implementation:

```text
python -m pytest -q tests/test_organizational_memory_contracts.py tests/test_organizational_memory_schemas.py tests/test_organizational_memory_aggregate.py
python -m compileall -q app/enums/organizational_memory.py app/models/organizational_memory.py app/models/organizational_memory_command.py app/schemas/organizational_memory.py app/ports/organizational_memory.py app/exceptions/organizational_memory.py
git diff --check
```

Relevant adjacent schema/aggregate regressions may be run read-only, but their
files are not authorized for modification.

## 8. Prohibited Patterns and Work

Batch 1 prohibits:

- SQLAlchemy, `Session`, `SessionLocal`, SQL, table metadata, ORM mappings,
  repository implementations, commits, flushes, or database access;
- migration files, Alembic changes, triggers, functions, indexes, grants,
  credentials, runtime/schema-owner configuration, or role tests;
- canonical Technical Report or provenance-capability repository/UoW access;
- implementation of source/provenance adapters, authorization policy, final
  recheck, idempotency store, Audit recorder, outbox recorder, clock, UoW, or
  application service;
- FastAPI/APIRouter, HTTP status/detail, dependency composition, router
  registration, or modification of `backend/app/main.py`;
- graph, semantic/vector search, embeddings, ranking, AI admission/reuse,
  multi-source synthesis, other source classes, persistent candidate/draft
  memory, cross-Organization sharing, frontend/UI, EDS-030, or EDS-031 work;
- creation of a second canonical memory identity for audience/scope variants;
- implicit admission, source mutation/ownership transfer, source acceptance as
  admission, or successor creation as supersession;
- plaintext source content, rationale, provenance body, diagnostics,
  credentials, or exception details in events, stored replay, protected
  results, or exception messages; and
- any Batch 2–7 production, migration, configuration, test, evidence, review,
  delivery, or closure work.

## 9. Stop Conditions

Implementation must stop and report `BLOCKED` if:

- any file outside the exact nine-file boundary is required;
- an accepted IDS type, operation, projection, digest, lifecycle, lineage,
  result, port, event, Audit, or replay contract is contradictory or requires
  design invention;
- exact accepted Technical Report snapshot parity cannot be represented without
  semantic transformation or a canonical contract change;
- a provenance class requires a generic/invented authority shape or direct
  foreign persistence access;
- an Aggregate invariant requires persistence, database locking, role grants,
  or application orchestration to be testable in S01–S02;
- a result or exception requires protected plaintext, identity, count,
  diagnostics, or authority facts beyond the accepted closed contract;
- an additional source, lifecycle state, operation, identity variant, or
  deferred capability becomes necessary;
- focused tests, relevant adjacent regressions, import/static validation,
  prohibited-pattern checks, exact-file scope, or `git diff --check` fails and
  cannot be corrected within the nine authorized files; or
- Batch 1 implementation authority, Batch 2 authority, or another required
  governance gate is absent.

## 10. Explicit Exclusion of Batches 2–7

- **Batch 2 / S03–S04:** no migration, schema/roles, repository, database
  invariants, or direct-SQL evidence.
- **Batch 3 / S05–S06:** no Technical Report adapter or provenance authorization
  adapter/integration evidence.
- **Batch 4 / S07–S10:** no concrete UoW, service commands, Audit/outbox/
  idempotency persistence, transaction, concurrency, or rollback integration.
- **Batch 5 / S11–S12:** no active/history service reads, pagination,
  continuation execution, or protected listing implementation.
- **Batch 6 / S13–S14:** no composition dependency, API router, authentication
  transport, or main registration.
- **Batch 7 / S15–S17:** no final validation package, final review artifact,
  PATCH status promotion, delivery, or closure.

Definitions of already accepted future-facing Protocols/DTOs required by S01
do not authorize any corresponding later-batch implementation.

## 11. Readiness and Authority Decision

Repository assumptions and S01–S02 dependencies are satisfied. The proposed
nine files are all required and form the minimum coherent boundary.

```text
Batch 1 manifest: COMPLETE
Batch 1 implementation readiness: READY
Batch 1 implementation authority: NOT GRANTED
Batch 2 authority: NOT GRANTED
Later Batch authority: NOT GRANTED
Migration authority: NOT REQUIRED / NOT GRANTED
Commit / push authority: NOT GRANTED
```

The exact next action is Human review and an explicit bounded Batch 1
implementation-authority decision for this nine-file manifest.
