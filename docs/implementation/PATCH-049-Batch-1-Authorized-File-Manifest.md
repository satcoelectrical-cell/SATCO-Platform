# PATCH-049 Batch 1 — Authorized File Manifest

## Governance state

PATCH-049 Architecture, EDS, IDS, Implementation Plan and IRR-049 are accepted/
PASS. This manifest authorizes **no implementation**. It defines the exact
future Batch 1 implementation boundary only. Batch 1 implementation requires
separate Human authority.

## Exact scope

Batch 1 establishes only strict contracts, immutable
`project_completeness.v1`, a pure deterministic evaluator and focused pure
tests. It consumes no live Project Context service; its evaluator accepts only
validated typed public context success data supplied later by Batch 2.

## Exact authorized future implementation files

| Path | Action | Sole responsibility | Dependencies | Prohibited responsibility |
|---|---|---|---|---|
| `backend/app/schemas/project_completeness.py` | CREATE | frozen extra-forbid enums, descriptor/observation/finding/evidence/question/checklist DTOs, closed result unions and pure bounds validators | accepted IDS-049 only | catalog behavior, source call, auth, transport, persistence |
| `backend/app/services/project_completeness_service.py` | CREATE | immutable 14-rule catalog, canonical serialization/digest, named pure evaluators, precedence, safe evidence, question/checklist rendering and Batch 1 bounds helpers | schema module and public Project Context types only | Project Context call, dependency/router, auth, ORM/Session/UoW, writes, EKG/AI |
| `backend/tests/test_project_completeness_contracts.py` | CREATE | strict schema/result/DTO/cardinality/extra-field and public contract tests | schema module | database, HTTP, integration, frontend |
| `backend/tests/test_project_completeness_catalog.py` | CREATE | 14-rule metadata/order/version/digest/template/firewall/zero-EKG tests | schema/service module | database, HTTP, integration, frontend |
| `backend/tests/test_project_completeness_service.py` | CREATE | pure evaluator vectors, five classifications, safe evidence, question/checklist, deterministic output and Batch 1 bounds tests | schema/service module and constructed typed context fixtures | live Project Context call, database, HTTP, frontend |

Exactly five files are authorized, all **CREATE**. No existing production,
test, frontend, migration, configuration or governance file is authorized for
Batch 1 implementation.

## Responsibility closure

- Contracts belong only in `schemas/project_completeness.py`.
- The catalog and evaluator belong only in
  `services/project_completeness_service.py`; evaluator input is explicitly
  supplied typed context, not an owner/service fetch.
- DTO contracts, catalog closure and evaluator behavior each have one focused
  test file. Shared fixtures must remain inside these test files; no global
  test configuration is authorized.

## Required focused evidence

The three test files must prove:

- catalog ID/version, exactly 14 rules, unique IDs/versions/ordinals and
  lexicographic ordering;
- stable canonical JSON bytes and SHA-256 digest;
- each accepted rule’s applicable classification vectors;
- `PRESENT`, `MISSING`, `INDETERMINATE`, `NOT_DISCLOSED` and
  `NOT_APPLICABLE` behavior;
- protected, unavailable, truncated, unsupported or insufficient input never
  becomes `MISSING`;
- safe evidence allow-list/order/dedup and maximum four per finding/56 total;
- deterministic question/checklist IDs, order and maximum one per eligible
  finding/14 total;
- deterministic repeated evaluation; 14 rule/finding limits and zero EKG;
- no engineering solution, material/BOM, vendor, optimization, score,
  percentage, AI/model, task/workflow or PATCH-050 language/behavior;
- strict extra-field/type/optionality/cardinality rejection.

## Read-only adjacent regression evidence

`backend/tests/test_project_context_contracts.py` is not an authorized modify
surface. Run it only as the smallest adjacent read-only regression after Batch
1 focused validation because the evaluator imports accepted public Project
Context DTO types. No other adjacent test is required for this pure batch.

## Explicit exclusions and stop conditions

Forbidden: all dependencies, ports, adapters, routers, `main.py`, Project
Context service modifications, auth, frontend, repository, ORM, Session, UoW,
database, migration, Audit, outbox, idempotency, EKG, AI/model/provider,
persistence, score/percentage, task/workflow, recommendation and PATCH-050
work.

Stop before or during implementation if any file outside the five-file list is
needed; a live/foreign source call, auth/dependency/transport, persistence or
migration is required; a catalog/rule/IDS change is necessary; protected or
insufficient data can become `MISSING`; or a dirty-worktree collision appears.

## Collision, migration and authority assessment

At preparation, all five paths are absent and have no unrelated local content.
Unrelated work remains unstaged and untouched. No schema/database/migration is
needed; Alembic is unchanged at expected sole head `e04700000001`.

Batch 1 is **ACCEPTED / COMPLETE as a manifest** and **ELIGIBLE FOR SEPARATE
IMPLEMENTATION AUTHORITY**. It does not grant that authority, Batch 2, delivery,
closure or PATCH-050.
