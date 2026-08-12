# PATCH-032 — Batch 1 Authorized File Manifest

## 1. Manifest Control

| Field | Value |
|---|---|
| PATCH | PATCH-032 — Technical Report |
| Authorized batch | Batch 1 — Contracts and Domain Foundation |
| Governing plan | Implementation-Plan-032 — ACCEPTED / COMPLETE |
| IRR | IRR-032 — PASS / READY FOR IMPLEMENTATION |
| Manifest status | VERIFIED / READY |
| Implementation authority | GRANTED — BOUNDED TO ACCEPTED PLAN |
| Currently authorized implementation | BATCH 1 ONLY |
| Migration execution authority | NOT GRANTED |
| Commit / push authority | NOT GRANTED |
| Date | 2026-08-09 |

This artifact publishes the exact Batch 1 file boundary required by IRR-032.
It authorizes no implementation during its own creation and grants no Batch 2–7
authority.

## 2. Repository Verification

| Check | Evidence | Result |
|---|---|---|
| Repository path | `/Users/mac/Projects/SATCO-Platform` | VERIFIED |
| Git metadata | functional `.git` worktree | VERIFIED |
| Branch | `patch-022.3a-development-infrastructure` | VERIFIED |
| HEAD | `b7fb8d4412d6b7528365f19b1418926aaa716686` | VERIFIED |
| Working tree | accepted uncommitted governance artifacts and unrelated pre-existing changes present | VERIFIED / PRESERVE |
| Backend structure | `app/enums`, `models`, `ports`, `schemas`, `exceptions`, `tests` | VERIFIED |
| Aggregate convention | explicit command methods on capability SQLAlchemy Aggregate classes | VERIFIED |
| Command/value convention | capability-owned `*_command.py` dataclasses/value objects | VERIFIED |
| Enum convention | capability module plus collision-safe `app.enums` exports | VERIFIED |
| Schema convention | strict capability-owned Pydantic v2 module | VERIFIED |
| Exception convention | capability module; package initializer remains empty | VERIFIED |
| Port convention | typed Protocol module with selected package exports | VERIFIED |
| Test convention | focused `test_<capability>_aggregate.py` and `test_<capability>_schemas.py` | VERIFIED |

No Technical Report production or test file currently exists. The accepted NEW
paths do not overwrite another capability. Current canonical source fields match
the four closed IDS-032 historical-basis contracts.

## 3. Batch 1 Boundary

Batch 1 implements only:

- closed Technical Report vocabularies;
- persistence-independent commands, actor/metadata/result/event contracts;
- closed frozen historical-basis value objects;
- capability-local canonical serialization and SHA-256 digest contracts;
- stable domain errors;
- Technical Report Aggregate fields, invariants, draft commands, exact Human
  acceptance, accepted terminality, successor-owned lineage, and version/
  revision behavior;
- strict Pydantic contract schemas;
- interface-only inward ports required by accepted Step S05;
- focused Aggregate and schema/contract tests.

The Aggregate resides in `backend/app/models/technical_report.py` because SATCO
combines Aggregate behavior and SQLAlchemy declarative identity in capability
model modules. Batch 1 may declare only the accepted Aggregate fields and
domain operations needed for in-memory construction and tests. It does not
authorize database creation, migration DDL, triggers, grants, repository
queries, persistence adapters, Session behavior, or database-level immutability
claims.

`backend/app/models/technical_report_command.py` may contain only Batch 1
commands, metadata, results, events, historical values, canonical serialization,
and digest behavior. Durable outbox/idempotency ORM rows and their integration
are explicitly deferred.

## 4. Production Files Authorized for Batch 1

| Path | State | Purpose | Exact Batch 1 responsibility | Plan step | IDS traceability | Dependencies | Tests |
|---|---|---|---|---|---|---|---|
| `backend/app/enums/technical_report.py` | NEW | Technical Report vocabularies | Define only lifecycle, purpose, source category/class, verification, availability, qualification, and other closed values enumerated by IDS-032 | S02 | §§5–6, 12, 17 | Python `StrEnum` only | aggregate, schemas |
| `backend/app/exceptions/technical_report.py` | NEW | Domain/application error contracts | Define stable Technical Report domain errors needed by Aggregate and schema tests; no HTTP mapping | S02 | §§5, 19 | existing exception conventions | aggregate, schemas |
| `backend/app/models/technical_report_command.py` | NEW | Commands and immutable values | Actor/metadata, create/revise/accept/successor commands, results/events, four closed historical bases, canonical JSON serializer, SHA-256 digest and verification contract; no durable ORM command rows | S03 | §§5.2–5.3, 12.2–12.4, 13–16, 21 | enums, standard library dataclasses/JSON/hashlib | aggregate, schemas |
| `backend/app/models/technical_report.py` | NEW | Aggregate root | Declare approved fields and implement create/revise/accept/create-successor domain operations, exact version/revision checks, Human Owner invariant, accepted terminality, provenance ownership, preliminary qualification, and lineage without supersession; no repository/Session/DDL behavior | S04 | §§5, 7–8 domain portion, 13, 21 | enums, commands, SQLAlchemy Base convention | aggregate |
| `backend/app/schemas/technical_report.py` | NEW | Strict typed contracts | Pydantic v2 request, response, list/filter, command, provenance, historical-basis, acceptance, successor, and lineage contracts owned by IDS-032; forbid server-controlled and extra fields | S04 | §§12, 17–20 | enums, approved result/value types, common pagination where applicable | schemas |
| `backend/app/ports/technical_report.py` | NEW | Inward interface contracts | Define Protocols and typed collaborator boundaries accepted by IDS-032; interfaces only—no repository, resolver, UoW, Audit, AI, or persistence implementation | S05 | §§9–12, 15–16 | commands/results/schemas typing only | import/contract checks within focused tests |
| `backend/app/enums/__init__.py` | MODIFY | Public enum exports | Add only collision-safe Technical Report enum exports; preserve qualified relationship lifecycle exports and backward-compatible alias | S02 | §§6, 22.2 | new enum module | aggregate/schema import checks |
| `backend/app/models/__init__.py` | MODIFY | Model/package discovery | Add only the Technical Report Aggregate import if required for the established capability import convention; do not export or register durable command rows in Batch 1 | S04 | §22.2 | new Aggregate module | aggregate/import checks |
| `backend/app/ports/__init__.py` | MODIFY | Public port exports | Add only collision-safe Technical Report Protocol exports required by repository convention; no implementations | S05 | §§10, 22.2 | new port module | import/contract checks |

Production file count: **9**.

## 5. Test Files Authorized for Batch 1

| Path | State | Purpose | Exact coverage | Plan step | IDS traceability | Dependencies |
|---|---|---|---|---|---|---|
| `backend/tests/test_technical_report_aggregate.py` | NEW | Domain behavior | creation for all purposes; draft revision; exact `draft → accepted`; invalid transitions; Human Owner acceptance contract; stale version/revision; terminal accepted state; successor new identity/draft; predecessor non-mutation; no supersession; acceptance not inherited; preliminary qualification; provenance completeness at domain level | S04 / Batch 1 checkpoint | §§5–6, 12–14, 21, 24.1 | Batch 1 enums, commands, Aggregate, errors |
| `backend/tests/test_technical_report_schemas.py` | NEW | Schema/value/serialization behavior | strict requests; required/extra/server-field rejection; all four historical bases; explicit-null rules; field exclusions; canonical JSON determinism; UUID/enum/time/Unicode/set normalization; lowercase SHA-256 determinism; integrity mismatch; completeness and excessive-plaintext rejection | S03–S04 / Batch 1 checkpoint | §§12.2–12.4, 17, 24.1, 24.3 | Batch 1 enums, commands/value objects, schemas |

Test file count: **2**.

No existing test file may be modified. Database trigger, runtime-role,
migration, repository, resolver, UoW, transaction, Audit, service, API,
integration, and full-regression test implementation belongs to later batches.

## 6. Documentation and Governance Files

The only documentation file authorized and created by the manifest task is:

- `docs/implementation/PATCH-032-Batch-1-Authorized-File-Manifest.md` — NEW.

No documentation file is part of the subsequent Batch 1 source implementation
manifest unless separately authorized by governance.

## 7. Existing File Modification Verification

### `backend/app/enums/__init__.py`

The file exists and centrally exports capability enums. Batch 1 authorizes only
new Technical Report imports/exports. Renaming, removing, or changing existing
exports is prohibited.

### `backend/app/models/__init__.py`

The file exists and imports current Aggregate/mapping modules. Batch 1 permits
only the Technical Report Aggregate import if compilation/model-discovery
convention requires it. Command outbox/idempotency imports are deferred.

### `backend/app/ports/__init__.py`

The file exists and exports selected inward Protocols. Batch 1 permits only
Technical Report Protocol exports with domain-qualified names. Existing generic
EngineeringObject aliases remain unchanged.

No change to `schemas/__init__.py` or `exceptions/__init__.py` is authorized:
the accepted IDS file map does not permit those modifications, and direct
capability imports match current practice.

## 8. New File Convention Verification

Every production NEW path uses an existing capability directory and established
snake-case module naming. The two test paths use the existing focused Aggregate
and schema naming pattern. Separate shared serializer, digest, provenance,
domain, or value-object modules are prohibited because IDS-032 assigns those
contracts to `technical_report_command.py` and does not authorize a platform-
wide abstraction.

An existing file is not suitable because no current capability owns Technical
Report semantics, and placing the contracts in Capture, Evidence,
EngineeringObject, Engineering Relationship, or shared Core would transfer
ownership or create prohibited coupling.

## 9. Historical Contract Coverage

| Contract | Canonical fields verified | Batch 1 owner | Resolver/persistence status | Readiness |
|---|---|---|---|---|
| `CaptureHistoricalBasisV1` | identity, version, Organization/Project/optional Workspace, discipline, optional Object, source kind/content/reference, creator, lifecycle, creation time exist | `backend/app/models/technical_report_command.py` | DEFERRED TO BATCH 3 | READY |
| `EvidenceHistoricalBasisV1` | identity, version, optional Project/Workspace, lifecycle, source kind/reference/revision/standing, effective time, supported fact, creator exist | same | DEFERRED TO BATCH 3 | READY |
| `EngineeringObjectHistoricalBasisV1` | identity, version, Organization/customer/Project/Workspace, family, discipline, object type, null V1 subtype, lifecycle, authority, creator, steward exist | same | DEFERRED TO BATCH 3 | READY |
| `EngineeringRelationshipHistoricalBasisV1` | identity, version, Organization/Project/Workspace, ordered endpoints, family/type, lifecycle, authority, Evidence IDs, creator/steward/reviewer/approver exist | same | DEFERRED TO BATCH 3 | READY |

Batch 1 defines closed Technical Report-owned representations only. It neither
imports canonical repositories nor reads, modifies, or persists canonical
source state.

## 10. Canonical Serialization and Digest Ownership

Exact ownership is:

```text
backend/app/models/technical_report_command.py
```

The contract is capability-local as required by IDS-032 §12.3. It covers closed
field validation, deterministic normalization and JSON bytes, SHA-256 digest
generation, and integrity verification. No new shared/Core utility is
authorized.

## 11. Batch 1 Dependency Independence

Batch 1 compiles and runs focused tests using existing Python, Pydantic,
SQLAlchemy declarative, enum, datetime, UUID, JSON, and hashing dependencies.
It requires no database table, Alembic migration, repository, UoW, Audit,
outbox/idempotency persistence, application service, API, PostgreSQL role,
trigger, Docker/configuration change, or frontend artifact.

The SQLAlchemy Aggregate declaration does not claim that persistence exists.
Database constraint parity, trigger immutability, grants, repository behavior,
and accepted snapshot persistence are later-batch gates.

Dependency independence result: **PASS**.

## 12. Batch 1 Implementation Order

1. Create `backend/app/enums/technical_report.py`.
2. Add only approved exports to `backend/app/enums/__init__.py`.
3. Create `backend/app/exceptions/technical_report.py`.
4. Create `backend/app/models/technical_report_command.py` with commands,
   historical contracts, serializer, and digest—but no durable ORM rows.
5. Create `backend/app/models/technical_report.py` with Aggregate behavior and
   accepted field declarations—but no persistence adapter.
6. Modify `backend/app/models/__init__.py` only if required by established
   import convention.
7. Create `backend/app/schemas/technical_report.py`.
8. Create `backend/app/ports/technical_report.py` with interfaces only.
9. Add only approved exports to `backend/app/ports/__init__.py`.
10. Create the two focused test modules.
11. Run static compilation, focused Batch 1 tests, import checks, prohibited-
    pattern scans, exact-file verification, and `git diff --check`.

This order prevents imports from referring to modules or symbols that have not
yet been created.

## 13. Batch 1 Test Requirements

The two authorized test modules must collectively prove:

- valid creation for each approved purpose;
- normalization and invariant failures;
- material draft revision with exactly one draft-revision and Aggregate-version
  advancement;
- stale/no-op rejection without state change;
- exact Human Owner confirmation and exact version/revision acceptance;
- the only lifecycle transition is `draft → accepted`;
- accepted technical content, provenance, acceptance, and ownership are
  terminal at domain level;
- successor is a new draft with a new UUID and predecessor reference;
- predecessor remains unchanged, lineage is not supersession, and acceptance is
  not inherited;
- preliminary assessment remains a qualification rather than lifecycle/purpose;
- material provenance completeness requirements;
- exact required and explicit-null optional fields for all four historical
  basis contracts;
- undeclared-field and excluded-field rejection;
- deterministic canonical bytes and lowercase SHA-256 digest;
- normalization of UUID, enum, UTC timestamp, Unicode, null, integer, and
  set-like Evidence identities;
- integrity mismatch, incomplete basis, and excessive/unapproved plaintext
  rejection;
- absence of generic update/delete/supersede/publish/Review/AI-accept commands.

Batch 1 test coverage result: **PASS / SUFFICIENT FOR AUTHORIZED SCOPE**.

## 14. Prohibited Batch 1 Files and Behavior

Batch 1 must not create or modify:

- `backend/app/repositories/technical_report_repository.py`;
- `backend/app/repositories/technical_report_unit_of_work.py`;
- `backend/app/services/technical_report_service.py`;
- `backend/app/ai/technical_report_assistant.py`;
- `backend/app/api/v1/routers/technical_reports.py`;
- `backend/app/main.py`;
- `backend/app/core/config.py`;
- `backend/app/core/database.py`;
- `backend/migrations/env.py`;
- `backend/migrations/versions/e03200000001_technical_reports.py`;
- `backend/tests/conftest.py`;
- `postgres/init/001_satco_database_roles.sh`;
- `docker-compose.yml`;
- any canonical source module;
- any repository, UoW, resolver, Audit, outbox/idempotency persistence, service,
  router, migration, trigger, role, infrastructure, or frontend surface.

The Batch 1 command file must not define SQLAlchemy outbox/idempotency tables.
The port file must not implement any adapter. The Aggregate must not open a
Session, authorize through infrastructure, commit, publish, or query another
capability.

## 15. Stop Conditions

Stop Batch 1 before or during implementation if any accepted historical field
is absent or semantically different; a closed contract cannot be represented
without guessing; compilation requires a Batch 2+ implementation; repository
conventions require an unlisted file; the Aggregate requires persistence,
authorization infrastructure, a new lifecycle, supersession, publication,
Review workflow, autonomous AI, changed Human Owner semantics, canonical source
ownership, or new architecture; or any change falls outside the eleven-file
source/test manifest.

No stop condition may be resolved by pulling a later batch forward.

## 16. Manifest Decision

```text
PATCH-032 Batch 1 manifest: CREATED / VERIFIED
Repository assumptions: VERIFIED
Batch 1 scope: CONFIRMED
Production files authorized: 9
Test files authorized: 2
Existing files to modify: 3
New production/test files: 8
Historical contract coverage: READY
Canonical serialization/digest owner: backend/app/models/technical_report_command.py
Batch 1 dependency independence: PASS
Batch 1 test coverage: PASS
Batch 1 blockers: NONE
Batch 1 implementation readiness: READY
Implementation authority: GRANTED — BOUNDED TO ACCEPTED IMPLEMENTATION-PLAN-032
Currently authorized implementation: BATCH 1 ONLY
```

## 17. Integrity Record

This task creates only this manifest. It changes no production source, test,
migration, configuration, infrastructure, accepted design, governance authority,
or implementation state. It executes no test or implementation batch and
performs no commit or push.

## 18. Revision History

| Version | Date | Description |
|---|---|---|
| 1.0 | 2026-08-09 | Published the verified exact eleven-file Batch 1 production/test manifest; Batch 1 ready; no implementation performed. |
