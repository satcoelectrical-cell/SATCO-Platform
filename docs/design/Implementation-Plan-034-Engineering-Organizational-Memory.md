# Implementation-Plan-034 — Engineering Organizational Memory

## 1. Document Control

| Field | Value |
|---|---|
| Document ID | Implementation-Plan-034 |
| Related PATCH | PATCH-034 — Engineering Organizational Memory |
| Governing EDS | EDS-034 — ACCEPTED / COMPLETE |
| Governing IDS | IDS-034 — ACCEPTED / COMPLETE |
| Plan version | 1.0 |
| Status | ACCEPTED / COMPLETE |
| Human IDS-034 Acceptance | PASS |
| Planning authority | GRANTED |
| Independent Plan Review | PASS |
| Human Plan Acceptance | PASS |
| Implementation authority | NOT GRANTED |
| Commit / push authority | NOT GRANTED |
| Date | 2026-08-12 |

This plan translates only the accepted PATCH-034 V1 contracts into
dependency-ordered work. It is not an implementation authorization or file
manifest.

## 2. Executable V1 Boundary

V1 owns one canonical `OrganizationalMemory` Aggregate sourced only from an
exact Human-accepted Technical Report version. Its operations are `admit`,
`get_active`, `list_active`, `inspect_history`, `create_successor`, `withdraw`,
and `supersede`. Admission is a separate explicit Human authority operation.
Standing is exactly `active → withdrawn | superseded`; terminal history is
immutable; successor creation does not supersede its predecessor.

The implementation retains the exact non-transformative accepted-report
projection, digest-bound source/provenance manifest, one canonical memory per
Organization/report/version, authorization-before-disclosure, current source
reauthorization, protected linked-identity disclosure, and accepted IDS role,
transaction, concurrency, Audit, outbox, idempotency, and pagination contracts.

Organizational Memory never owns or mutates Technical Report, Capture,
Evidence, Engineering Object, or Engineering Relationship state. Canonical
integration uses their application services only. Direct foreign repository,
ORM, Session, UoW, table, or policy access is prohibited.

## 3. Deferred / Non-blocking Scope

The following create no V1 production surface, task, route, evidence gate, or
implicit prerequisite: admission from Journal, Capture, Evidence, EKG, AI, or
any source other than accepted Technical Report; multi-source synthesis;
cross-Organization sharing; publication; semantic/vector search, embeddings,
ranking, graph expansion, autonomous AI, enterprise approval boards,
frontend/UI, EDS-030, and EDS-031 behavior. Reports containing provenance
classes outside the accepted V1 authorizable set are ineligible; later support
requires separately accepted design.

## 4. Planned Repository Surfaces

Every batch requires a separately authorized exact-file manifest. These are
expected surfaces; discovery of an additional production, migration, test, or
configuration file is a stop condition until its manifest is reconciled.

### 4.1 Production and migration surfaces

| Expected path | Action | Purpose |
|---|---|---|
| `backend/app/enums/organizational_memory.py` | CREATE | Closed standing, operation, outcome, event, rejection, and provenance vocabularies |
| `backend/app/models/organizational_memory.py` | CREATE | Aggregate, immutable admitted state, standing transitions, lineage invariants |
| `backend/app/models/organizational_memory_command.py` | CREATE | Actor, scope, commands, metadata, events, history and stored replay value objects |
| `backend/app/schemas/organizational_memory.py` | CREATE | Strict request, projection, safe read/history/page, and closed result schemas |
| `backend/app/ports/organizational_memory.py` | CREATE | Exact repository, readers, provenance authorizer, UoW, Audit, outbox, idempotency and service ports |
| `backend/app/exceptions/organizational_memory.py` | CREATE | Internal domain/persistence exceptions translated to closed results; no transport detail |
| `backend/app/repositories/organizational_memory_repository.py` | CREATE | Root/history persistence, expected-version transitions, canonical-order candidate reads |
| `backend/app/repositories/organizational_memory_unit_of_work.py` | CREATE | Same-Session final recheck, Audit, outbox, idempotency, clock and transaction ownership |
| `backend/app/adapters/organizational_memory.py` | CREATE | Accepted-report adapter and four context-specific canonical provenance authorization adapters |
| `backend/app/services/organizational_memory_service.py` | CREATE | Seven-operation application orchestration and protected outcome mapping |
| `backend/app/dependencies/organizational_memory.py` | CREATE | Request-scoped trusted composition without transport-owned infrastructure |
| `backend/app/api/v1/routers/organizational_memory.py` | CREATE | Thin authenticated V1 transport only |
| `backend/app/main.py` | MODIFY | Register only the Organizational Memory router |
| `backend/app/core/database.py` | MODIFY | Extend existing fail-closed runtime/schema-owner verification to memory-owned objects |
| `backend/migrations/versions/e03400000001_organizational_memory.py` | CREATE after current-head verification | Tables, constraints, indexes, functions, triggers, grants and reversible downgrade |

The migration revision and parent must be reverified immediately before its
manifest is accepted. A changed repository head requires manifest correction;
parallel heads are prohibited.

### 4.2 Test and evidence surfaces

| Expected path | Action | Purpose |
|---|---|---|
| `backend/tests/test_organizational_memory_contracts.py` | CREATE | Closed types/results, serialization, digest and replay payloads |
| `backend/tests/test_organizational_memory_aggregate.py` | CREATE | Aggregate lifecycle, lineage, terminality and immutability |
| `backend/tests/test_organizational_memory_schemas.py` | CREATE | Strict request/response boundaries and plaintext exclusion |
| `backend/tests/test_organizational_memory_repository.py` | CREATE | Mapping, uniqueness, candidate ordering and optimistic persistence |
| `backend/tests/test_organizational_memory_migration.py` | CREATE | Schema, constraints, functions, triggers, direct-SQL bypass and Alembic head |
| `backend/tests/test_organizational_memory_database_roles.py` | CREATE | Runtime/schema-owner identity, grants, ownership and trigger bypass denial |
| `backend/tests/test_organizational_memory_transaction.py` | CREATE | Real-UoW success, rollback, Audit, history, outbox and idempotency atomicity |
| `backend/tests/test_organizational_memory_integration.py` | CREATE | Accepted-report and four provenance application-boundary integrations |
| `backend/tests/test_organizational_memory_service.py` | CREATE | Seven operations, replay, concurrency and protected outcomes |
| `backend/tests/test_organizational_memory_security.py` | CREATE | Authority, revocation, scope/audience, linked identity and non-disclosure |
| `backend/tests/test_organizational_memory_pagination.py` | CREATE | Last-evaluated anchor, denied candidates, bounds and token semantics |
| `backend/tests/test_organizational_memory_api.py` | CREATE | Real authentication/Organization context, thin transport and prohibited routes |
| `backend/tests/conftest.py` | MODIFY only if manifest proves required | Isolated schema-owner/runtime fixtures for new tables without weakening test DB guards |
| `docs/reviews/PATCH-034-Implementation-Validation-Evidence.md` | CREATE in final batch | Reproducible S18–S20-style evidence and QG-M1 traceability |
| `docs/reviews/FR-034-Engineering-Organizational-Memory.md` | CREATE in final batch | Independent Final Review candidate record; no Human promotion |
| `docs/patches/PATCH-034.md` | MODIFY in governed batches only | Batch status/evidence linkage without technical scope changes |

Existing canonical tests are regression inputs and are not modified unless a
separate manifest explicitly authorizes a proven compatibility correction.

## 5. Dependency-Ordered Workstreams and Steps

### Batch 1 — Contracts and Aggregate Foundation

#### S01 — Closed contracts and canonical representation

- **Purpose:** Implement enums, actor/scope/source identities, commands, exact
  operation results, standing-specific history DTOs, provenance request
  variants, four bounded stored replay variants, and strict schemas.
- **Production:** enums, command/value objects, schemas, ports, internal
  exceptions.
- **Tests:** contracts and schemas.
- **Dependencies:** accepted IDS-034 and current Technical Report snapshot/
  historical-basis contracts.
- **Security:** Organization remains server-derived; protected results are
  payload-free; linked identities use protected optional slots.
- **Evidence:** exact operation/discriminator map, <=1 KiB replay JSON,
  canonical JSON golden vectors, field/cardinality/unknown-key negatives.
- **Stop:** any DTO requires a deferred source, client authority, canonical
  contract change, or richer replay payload.

#### S02 — Aggregate lifecycle and digest foundation

- **Purpose:** Implement deterministic snapshot projection, manifest/digests,
  canonical uniqueness identity, active/terminal transitions and successor
  lineage without persistence.
- **Production:** Aggregate model and pure serialization/digest utilities in
  approved Batch-1 files only.
- **Tests:** Aggregate lifecycle, semantic parity, no paraphrase/omission,
  terminal immutability, successor-not-supersession and zero/one predecessor.
- **Dependencies:** S01.
- **Acceptance:** exact accepted snapshot parity; no mutation after admission;
  only active→withdrawn|superseded; no new technical meaning.
- **Stop:** source data cannot be projected without transformation or a new
  lifecycle/standing is required.

### Batch 2 — Credential and Persistence Foundation

#### S03 — Migration, schema and role boundary

- **Purpose:** Add root, standing-history, outbox, and idempotency tables in
  dependency order; exact columns/FKs/checks/indexes; canonical uniqueness;
  JSON validators/digests; lineage/root/history/side-record guards; restricted
  grants and ownership.
- **Production:** one verified-head Alembic revision and `core/database.py` role
  verification; no service behavior.
- **Tests:** migration and database-role suites; `conftest.py` only if required
  for existing isolated credential fixtures.
- **Dependencies:** Batch 1 accepted; current Alembic head; existing distinct
  `satco` schema-owner and `satco_runtime` runtime roles.
- **Evidence:** upgrade/downgrade/round-trip; exact head; table/function/trigger
  ownership; column grants; runtime cannot DDL/disable guards.
- **Stop:** credential roles coincide, parent revision changed, migration needs
  foreign-table mutation, or runtime must own protected objects.

#### S04 — Repository and direct-SQL invariants

- **Purpose:** Implement root/history mapping, expected-version persistence,
  candidate reads, last-evaluated ordering primitives, and exact DB guards.
- **Production:** repository only.
- **Tests:** repository plus direct-SQL invalid insert/update/delete matrix.
- **Dependencies:** S03.
- **Evidence:** Organization/Workspace/Project/audience predecessor coherence;
  active linked replacement; replacement reuse denial; terminal and history
  bypass denial; uniqueness race.
- **Stop:** an invariant can be bypassed by direct SQL or requires foreign
  ownership transfer.

### Batch 3 — Canonical Integration

#### S05 — Accepted Technical Report source adapter

- **Purpose:** Translate `MemoryActor` to the accepted Technical Report actor,
  perform the authorized read, require exact accepted version/digest/scope, and
  construct the deterministic admitted representation.
- **Production:** canonical adapter module only.
- **Tests:** integration tests against the actual Technical Report service.
- **Dependencies:** Batches 1–2 accepted; PATCH-032 service composition.
- **Evidence:** draft/wrong version/wrong digest/revoked/cross-scope/unavailable
  outcomes; no Technical Report repository/UoW/Session import.
- **Stop:** accepted snapshot is unavailable through the application service or
  direct Technical Report persistence becomes necessary.

#### S06 — Context-specific provenance authorization

- **Purpose:** Implement exact Capture, Evidence, Engineering Object, and
  Engineering Relationship request variants and their existing canonical read
  contexts; reject unsupported provenance admission.
- **Production:** same adapter surface and inward contracts already authorized.
- **Tests:** real application-boundary calls, context/response mismatch,
  batching (100/three/256), mixed denial, partial failure and no partial result.
- **Dependencies:** S05 and current canonical application services.
- **Security:** all-or-nothing disclosure; no foreign repository/UoW/policy;
  unsupported provenance is ineligible, never silently omitted.
- **Stop:** any retained identity cannot be authorized with its current
  application boundary or requires invented generic authority.

### Batch 4 — Unit of Work, Commands, and Reliability

#### S07 — UoW collaborators and atomic side records

- **Purpose:** Implement same-Session repository/final-recheck/success Audit/
  standing history/outbox/idempotency collaborators and separate bounded
  post-rollback rejection Audit.
- **Production:** memory UoW and repository surfaces.
- **Tests:** real PostgreSQL transaction tests and structural port conformance.
- **Dependencies:** Batches 1–3 and persistence accepted.
- **Evidence:** one commit; repository no-commit; failures after every stage
  restore exact pre-state; rejection Audit ordering/failure isolation; exact
  shared `AuditLog` mapping and non-plaintext event payload.
- **Stop:** collaborators require separate authoritative Sessions, shared Audit
  schema change, or failed commands leave a side record.

#### S08 — Admission and successor commands

- **Purpose:** Implement `admit` and `create_successor`, uniqueness, final
  source/provenance/authority rechecks, idempotency, Audit/outbox/history and
  protected duplicate behavior.
- **Production:** application service plus accepted UoW contracts.
- **Tests:** service/security/transaction integration.
- **Dependencies:** S07.
- **Evidence:** explicit Human authority, exact source, concurrent duplicate one
  winner, predecessor scope/audience, successor does not supersede, rollback.
- **Stop:** admission becomes implicit, candidate/draft state appears, or source
  ownership is transferred.

#### S09 — Withdrawal and explicit supersession

- **Purpose:** Implement terminal transitions with expected versions,
  deterministic UUID locking, exact linked replacement and stable results.
- **Production:** Aggregate/application/UoW surfaces already in manifest.
- **Tests:** simultaneous transitions, stale versions, invalid replacement,
  terminal retry, rollback and direct-SQL parity.
- **Dependencies:** S08.
- **Evidence:** exactly one winner; replacement remains active; history/Audit/
  outbox/idempotency commit atomically.
- **Stop:** reactivation, generic update/delete, implicit supersession, or a
  second predecessor is required.

#### S10 — Exact idempotency replay

- **Purpose:** Persist/reconstruct `admit→admit.v1`, `withdraw→withdraw.v1`,
  `create_successor→create_successor.v1`, and `supersede→supersede.v1` results.
- **Production:** service/UoW/idempotency surfaces only.
- **Tests:** all valid and cross-paired mappings, fingerprint conflict, pending,
  replay after later standing/version change, current revocation denial, no
  replay side effects and plaintext-free storage.
- **Dependencies:** S08–S09.
- **Stop:** replay requires current Aggregate state substitution or stores
  projection, provenance, rationale, audience, restrictions or diagnostics.

### Batch 5 — Reads, Pagination, and Protected Disclosure

#### S11 — Active reads and historical inspection

- **Purpose:** Implement `get_active` and `inspect_history`, current source and
  optional provenance reauthorization, standing-specific details, and protected
  predecessor/replacement slots.
- **Production:** application service and existing ports/adapters.
- **Tests:** active/withdrawn/superseded matrices; requested/absent/authorized/
  denied linked identity equivalence; source revocation and unavailable paths.
- **Dependencies:** Batch 4 accepted.
- **Stop:** retained snapshots become fallback authority or protected identity
  presence is distinguishable.

#### S12 — Active listing and continuation

- **Purpose:** Implement bounded canonical-order listing and authenticated
  continuation anchored to the last evaluated `(admitted_at, memory_id)`.
- **Production:** repository/application continuation support within approved
  files; no search engine or new infrastructure.
- **Tests:** filters before authorization, denied candidate between visible
  items, scan/call bounds, tamper/expiry/replay, no skips/duplicates, visible
  total only.
- **Dependencies:** S11.
- **Stop:** hidden/global totals, last-returned anchoring, unbounded scanning,
  semantic/vector/graph retrieval or provenance N+1 appears.

### Batch 6 — Transport Integration

#### S13 — Request-scoped composition

- **Purpose:** Compose trusted authentication/Organization context, canonical
  service adapters, memory UoW and service outside transport.
- **Production:** dependency module.
- **Tests:** real JWT/Organization context and collaborator-boundary evidence.
- **Dependencies:** Batches 1–5 accepted.
- **Stop:** router must construct Session/repository/UoW/policy or accept client
  Organization authority.

#### S14 — Thin API

- **Purpose:** Expose only seven accepted operations with strict DTOs and closed
  protected-result translation; register router.
- **Production:** router and `main.py`.
- **Tests:** API/security suites, stable payload-free outcomes, positive
  disclosure boundaries and prohibited route matrix.
- **Dependencies:** S13.
- **Stop:** transport owns authorization, lifecycle, digest, persistence or
  transaction behavior, or adds publication/search/UI/deferred endpoints.

### Batch 7 — Focused Verification and Final Evidence

#### S15 — Focused contract/application/security/database evidence

- **Purpose:** Run all PATCH-034 focused suites and close the IDS verification
  matrix.
- **Production:** none; remediation requires separate authority.
- **Evidence:** contracts, Aggregate, schemas, repository, migration, roles,
  transaction, canonical integration, service, security, pagination and API.
- **Dependencies:** Batches 1–6 Human accepted.
- **Stop:** any failed test, required code/design change, or unauthorized file.

#### S16 — Adjacent and full regression

- **Purpose:** Prove compatibility with Technical Report, Capture, Evidence,
  Engineering Object, Engineering Relationship, Journal, EKG, authentication/
  Organization, Project/Workspace, Audit and Alembic.
- **Evidence:** adjacent suites; complete backend regression; static/import
  validation; current single Alembic head/schema checks; role/security checks;
  prohibited-pattern and exact-scope scans; `git diff --check`.
- **Dependencies:** S15 PASS.
- **Stop:** any failure, unrelated work in boundary, or stale migration head.

#### S17 — QG-M1 and final-review package

- **Purpose:** Create reproducible validation evidence and FR-034 candidate,
  update PATCH-034 batch status, and establish Independent Final Implementation
  Review readiness without granting QG-11, delivery, or closure authority.
- **Docs:** only the three planned final evidence/governance files.
- **Dependencies:** S15–S16 PASS and all review histories preserved.
- **Acceptance:** commands/results, environment, exact file scope, historical
  finding traceability, exclusions and QG-M1 PASS are independently auditable.
- **Stop:** missing review/Human acceptance artifact, unresolved Critical/Major
  finding, evidence not reproducible, or authority wording promotes delivery.

## 6. Exact Expected Batch Surfaces

These action labels are planning expectations. The later Authorized File
Manifest is authoritative for execution and may narrow them; widening requires
Human manifest reconciliation.

| Batch | Production/migration | Tests/evidence/docs |
|---|---|---|
| 1 | CREATE `backend/app/enums/organizational_memory.py`; CREATE `backend/app/models/organizational_memory.py`; CREATE `backend/app/models/organizational_memory_command.py`; CREATE `backend/app/schemas/organizational_memory.py`; CREATE `backend/app/ports/organizational_memory.py`; CREATE `backend/app/exceptions/organizational_memory.py` | CREATE `backend/tests/test_organizational_memory_contracts.py`; CREATE `backend/tests/test_organizational_memory_aggregate.py`; CREATE `backend/tests/test_organizational_memory_schemas.py` |
| 2 | CREATE `backend/migrations/versions/e03400000001_organizational_memory.py` after head verification; CREATE `backend/app/repositories/organizational_memory_repository.py`; MODIFY `backend/app/core/database.py` | CREATE `backend/tests/test_organizational_memory_repository.py`; CREATE `backend/tests/test_organizational_memory_migration.py`; CREATE `backend/tests/test_organizational_memory_database_roles.py`; MODIFY `backend/tests/conftest.py` only if the accepted manifest verifies it is necessary |
| 3 | CREATE `backend/app/adapters/organizational_memory.py` | CREATE `backend/tests/test_organizational_memory_integration.py`; CREATE `backend/tests/test_organizational_memory_security.py` initially for adapter/non-disclosure evidence |
| 4 | CREATE `backend/app/repositories/organizational_memory_unit_of_work.py`; CREATE `backend/app/services/organizational_memory_service.py`; MODIFY Batch-1 model/command/port files only when required to implement their already-accepted contracts; MODIFY repository/adapter files only within their accepted responsibilities | CREATE `backend/tests/test_organizational_memory_transaction.py`; CREATE `backend/tests/test_organizational_memory_service.py`; MODIFY focused contract/aggregate/integration/security tests only for S07–S10 evidence |
| 5 | MODIFY `backend/app/services/organizational_memory_service.py`; MODIFY `backend/app/repositories/organizational_memory_repository.py`; MODIFY `backend/app/ports/organizational_memory.py` only for already-specified read/continuation contracts | CREATE `backend/tests/test_organizational_memory_pagination.py`; MODIFY service/security/integration tests for S11–S12 evidence |
| 6 | CREATE `backend/app/dependencies/organizational_memory.py`; CREATE `backend/app/api/v1/routers/organizational_memory.py`; MODIFY `backend/app/main.py` | CREATE `backend/tests/test_organizational_memory_api.py`; MODIFY `backend/tests/test_organizational_memory_security.py` for real HTTP/authentication evidence |
| 7 | NONE | CREATE `docs/reviews/PATCH-034-Implementation-Validation-Evidence.md`; CREATE `docs/reviews/FR-034-Engineering-Organizational-Memory.md`; MODIFY `docs/patches/PATCH-034.md` |

No batch expects modification of canonical Technical Report, Capture, Evidence,
Engineering Object, or Engineering Relationship production files.

## 7. Batch Review and Governance Gates

Each batch follows:

```text
Human preparation authority
→ exact Authorized File Manifest
→ Human batch implementation/execution authority
→ bounded execution
→ Independent Batch Review
→ focused remediation/re-review when required
→ Human Batch Acceptance
```

Later-batch preparation and implementation authority remain not granted until
the preceding batch is Human accepted. After Batch 7: Independent Final
Implementation Review → Human QG-11 → QG-12 bounded delivery authorization →
verified delivery → separately authorized governance closure. No step implies
commit, push, delivery, or closure authority.

## 8. Global Stop Conditions

Stop and return to governance if:

- accepted PATCH/EDS/IDS semantics must change;
- any canonical source/provenance read needs direct foreign persistence/UoW;
- a provenance class lacks its accepted application-level authorization path;
- source reauthorization or shared mutable authority cannot be rechecked safely;
- DB triggers/roles cannot protect direct SQL under restricted runtime;
- migration head differs from the verified parent or creates multiple heads;
- a failed command can leave root/history/Audit/outbox/idempotency state;
- replay cannot preserve the original bounded result after later state changes;
- protected denial leaks identity, existence, count, standing, lineage,
  provenance, plaintext, diagnostics or timing-dependent protected data;
- a deferred capability, new source, publication, AI authority, search, graph,
  UI, cross-Organization sharing, or unrelated module enters scope;
- work requires a file outside the accepted batch manifest.

## 9. Plan Acceptance Criteria

The plan is executable without changing accepted design when all planned
surfaces remain bounded, current canonical application services support the
four provenance authorization variants, the verified Alembic/role boundary is
available, and every batch can meet its evidence and stop conditions. Human
Plan Acceptance, IRR-034, batch authority, implementation, delivery, and
closure remain separate future governance decisions.

## 10. Governance State

```text
Implementation-Plan-034: ACCEPTED / COMPLETE
Human IDS-034 Acceptance: PASS
Independent Implementation Plan Review: PASS
Human Implementation Plan Acceptance: PASS
Permission for IRR-034: GRANTED / EXERCISED
IRR-034: FOCUSED RE-REVIEW PENDING AFTER GOVERNANCE RECONCILIATION
Implementation authority: NOT GRANTED
Commit / push authority: NOT GRANTED
```
