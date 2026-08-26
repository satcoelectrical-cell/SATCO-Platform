# Implementation-Plan-049 — Project Completeness & Missing-Information Intelligence

## 1. Status, purpose and immutable boundary

**ACCEPTED / COMPLETE.** This plan sequences only accepted IDS-049 work. It
implements deterministic, request-time, read-only Project completeness
intelligence over one fresh authorized PATCH-048 Project Context observation.

It does not alter PATCH-048, owner capabilities, Architecture/EDS/IDS rule
semantics, production data or migrations. It introduces no AI/model call, EKG
call, persistence, UoW, transaction, Audit, outbox, idempotency, score,
percentage, task/workflow, recommendation or PATCH-050 behavior.

## 2. Repository file reconciliation

The accepted IDS map reconciles directly with repository conventions:

| Surface | Existing pattern | Plan decision |
|---|---|---|
| strict backend DTOs | `backend/app/schemas/project_context.py` | CREATE completeness schema module |
| public inward port | `backend/app/ports/project_context.py` | CREATE narrow Project Context assessment port |
| pure read service | `backend/app/services/project_context_service.py` | CREATE completeness service |
| request composition | `backend/app/dependencies/project_context.py` | CREATE completeness dependency |
| thin authenticated router | `backend/app/api/v1/routers/project_context.py` | CREATE completeness router |
| router registration | `backend/app/main.py` | MODIFY once |
| API types/client | `frontend/src/api/types.ts`, `frontend/src/api/client.ts` | MODIFY only exact DTOs/method |
| Project surface | `ProjectEngineeringContextPanel.tsx`, `ProjectsPage.tsx` | CREATE panel; MODIFY placement |
| styles/tests | existing scoped CSS and Vitest files | CREATE focused panel test; MODIFY scoped CSS only |

No accepted file is unnecessary and no additional production/test surface is
required. Proposed paths are those closed in IDS-049: twelve CREATE files and
five MODIFY files. All new test files are adjacent to their production layers;
no broad test-framework or configuration file changes are planned.

## 3. Dependency graph and three-batch structure

```text
Batch 1: schemas + immutable catalog + evaluators
    -> Batch 2: fresh PATCH-048 composition + service + route/security
        -> Batch 3: frontend + final focused evidence
            -> final validation -> final review -> QG-11 -> QG-12
```

Each batch has a separate Authorized File Manifest, independent manifest
review, Human implementation authority, implementation, focused validation,
smallest meaningful adjacent regression, independent implementation review,
remediation/re-review if required, and Human acceptance. No later batch begins
until the earlier batch is accepted.

## 4. Batch 1 — Contracts, immutable catalog and deterministic evaluator

### Objective

Create the pure, dependency-free foundation. It must accept only typed
Project Context success projections supplied by a future service; it must not
call Project Context or any other dependency.

### Authorized production surfaces for a later manifest

| Path | CREATE/MODIFY | Exact responsibility |
|---|---|---|
| `backend/app/schemas/project_completeness.py` | CREATE | frozen closed enums, DTOs, descriptor/result unions and validators |
| `backend/app/services/project_completeness_service.py` | CREATE | immutable `project_completeness.v1`, canonical digest, explicit evaluators, safe evidence, questions/checklists, response-size helper |

The service file must not receive composition, HTTP, persistence or frontend
responsibilities in Batch 1. It may expose a pure `evaluate_context` helper
whose input is a validated `ProjectContextSuccess`; the public assessment
operation is Batch 2.

### Exact work

1. Implement strict `extra="forbid"`, frozen enums/DTOs and all closed result
   discriminators from IDS-049.
2. Materialize exactly 14 lexicographically ordered descriptors, with fixed
   ordinals, rule/version IDs, titles/descriptions, codes, section matrix,
   templates and `graph_requirement=null`.
3. Canonically serialize source-controlled descriptors and expose the golden
   SHA-256 digest fixture.
4. Implement named evaluator functions only; no dynamic dispatch or expression
   interpreter.
5. Enforce classification precedence, recursively inspected input count,
   14/14/14/14/56 output limits and 131,072-byte result limit.
6. Project only safe evidence; render fixed advisory question/checklist text;
   prohibit all PATCH-050 solution language.

### Explicit exclusions

No `ProjectContextAssessmentSource`, dependency, router, `main.py`, API call,
frontend code, repository, Session, UoW, migration, Audit, outbox, idempotency,
EKG or AI import.

### Focused validation

| Test path | Required evidence |
|---|---|
| `backend/tests/test_project_completeness_contracts.py` | strict DTO closure, result unions, field/cardinality/extra-field rejection |
| `backend/tests/test_project_completeness_catalog.py` | exactly 14 rules, unique IDs/ordinals, lexicographic order, canonical bytes/digest, fixed metadata/templates, no graph/AI/PATCH-050 phrases |
| `backend/tests/test_project_completeness_service.py` | each relevant five-state vector, precedence, all-item truncation, evidence filtering/order, questions/checklists, all bounds and deterministic repeated output |

Use only these focused tests plus the smallest applicable Project Context schema
contract subset if an imported public type needs regression protection. Do not
run backend-wide tests.

### Batch 1 independent review gate

Review exact catalog closure/digest, every evaluator, missingness safety,
safe evidence, deterministic output, bounds, no foreign dependency and no
PATCH-050/AI/write leakage. Acceptance requires zero Critical/Major findings
and all Batch 1 focused evidence PASS.

## 5. Batch 2 — Assessment service, PATCH-048 composition and authenticated transport

### Objective

Wire the accepted pure evaluator to exactly one fresh public PATCH-048 Project
Context observation and expose one thin authenticated read route.

### Authorized production surfaces for a later manifest

| Path | CREATE/MODIFY | Exact responsibility |
|---|---|---|
| `backend/app/ports/project_completeness.py` | CREATE | narrow observe-only Project Context Protocol |
| `backend/app/dependencies/project_completeness.py` | CREATE | request-scoped trusted composition over public Project Context application |
| `backend/app/services/project_completeness_service.py` | MODIFY | public assessment orchestration only |
| `backend/app/api/v1/routers/project_completeness.py` | CREATE | one authenticated GET route and payload-safe translation |
| `backend/app/main.py` | MODIFY | register router exactly once |

### Exact flow

```text
authenticated request
 -> trusted actor + server-derived Organization
 -> strict Project/optional Workspace request
 -> one fresh all-ten-section PATCH-048 request (page_size=100, no continuation)
 -> protected/invalid/unavailable upstream translation
 -> typed context/scope and <=1,000-input validation
 -> all 14 evaluators exactly once
 -> safe evidence/questions/checklists + partiality
 -> <=131,072-byte validation
 -> closed result
```

The adapter calls only `ProjectContextService.assemble_project_context` through
the existing application boundary. It has no graph interface and makes zero
EKG calls. The router owns neither authorization policy, repository, ORM,
Session, UoW nor catalog/evaluator.

### Security and failure semantics

- actor mismatch, cross-Organization/Project/Workspace scope and malformed
  foreign public output fail closed as specified by IDS-049;
- protected, invalid and unavailable results have discriminator only;
- no client Organization, source context, catalog choice, continuation or
  arbitrary options are accepted;
- no source/protected count, Human identity, private storage or exception
  detail is logged or serialized;
- no write means no rollback, Audit/outbox/idempotency or partial canonical
  mutation seam exists;
- response/bound/catalog structural failure returns payload-free unavailable.

### Focused validation

| Test path | Required evidence |
|---|---|
| `backend/tests/test_project_completeness_service.py` | one fresh all-ten request, actor/scope binding, upstream mapping, exactly-once evaluation, input/response bounds, partiality |
| `backend/tests/test_project_completeness_security.py` | actor mismatch, cross Organization/Project/Workspace, protected non-disclosure, no protected/unavailable/truncated-to-missing, safe logs/no foreign access/no EKG |
| `backend/tests/test_project_completeness_api.py` | authentication, one route, strict parameter validation, closed serialization, payload-free outcomes |

### Smallest adjacent regression

Run `test_project_context_contracts.py`, `test_project_context_service.py`,
`test_project_context_security.py` and `test_project_context_api.py` only.
They prove the reused public boundary and its authenticated/non-disclosure
behavior without a broad backend run.

### Batch 2 independent review gate

Review real public-boundary use, one-fresh-call rule, authorization-before-
disclosure, scope/actor binding, exact closed result mapping, no persistence or
foreign access, all 14 rules exactly once and transport thinness. Acceptance
requires zero Critical/Major findings and all focused/adjacent evidence PASS.

## 6. Batch 3 — Frontend integration and final focused evidence

### Objective

Expose the accepted read-only result in the existing Project Workspace without
creating fake data, authority leakage or new product semantics.

### Authorized production surfaces for a later manifest

| Path | CREATE/MODIFY | Exact responsibility |
|---|---|---|
| `frontend/src/api/types.ts` | MODIFY | exact completeness DTO/string unions only |
| `frontend/src/api/client.ts` | MODIFY | one `projectCompleteness` closed-status call only |
| `frontend/src/components/ProjectCompletenessPanel.tsx` | CREATE | accessible read-only Project surface |
| `frontend/src/pages/ProjectsPage.tsx` | MODIFY | place panel before Project Engineering Context only |
| `frontend/src/styles.css` | MODIFY | scoped responsive/direction-neutral styles only |
| `frontend/src/test/project-completeness.test.tsx` | CREATE | focused UI and accessibility tests |

### Required presentation behavior

The panel makes a fresh on-demand request at mount, explicit refresh and
Project/Workspace scope change. It must render loading; complete/partial
available result; all five classifications; no-applicable-rules;
no-actionable-gaps; limitations/truncation; payload-safe protected/invalid/
unavailable states; safe evidence; advisory questions; and read-only checklist
prompts. `MISSING` is visibly and textually distinct from `INDETERMINATE` and
`NOT_DISCLOSED`.

Use semantic heading/category/list structures, non-color labels, keyboard
operable reauthorized links, focus return after refresh, safe polite status,
responsive single-column stacking and CSS logical properties. Do not expose raw
selectors or render score, percentage, progress, AI/chat branding, editable
tasks, workflow buttons, recommendations or sample/demo data.

### Focused frontend validation

`frontend/src/test/project-completeness.test.tsx` proves the API call contract,
all result/classification states, safe evidence, question/checklist display,
no-applicable/no-actionable/partial coexistence, non-disclosure, no fake data,
accessibility and responsive/direction-neutral class behavior. `api.test.ts`,
`project-context.test.tsx` and the smallest Project Workspace test subset are
the adjacent regression. Run frontend typecheck/build/static checks affected by
the files, not the full suite during ordinary Batch 3 work.

### Batch 3 independent review gate

Review exact real-data behavior, client result handling, safe rendering,
classification distinction, accessibility, responsive layout, no score/AI/task/
PATCH-050 leakage and no frontend authority recreation. Acceptance requires
zero Critical/Major findings and all focused/adjacent frontend/backend evidence
PASS.

## 7. Manifest strategy

No manifest is created in this run. For each batch, prepare an allow-list that
states CREATE/MODIFY, precise responsibility, dependencies, prohibited work,
focused tests, adjacent tests, stop conditions and dirty-file collision checks.
The allow-list must not silently add a file beyond this plan. Any need for a
new owner contract, persistence/migration, EKG, AI, score, recommendation or
PATCH-050 surface stops the batch for governed reconciliation.

## 8. Validation and test-environment strategy

Per batch: first pure/unit tests, then affected service/API/UI integration,
then the stated smallest adjacent regression, then static/import/typecheck only
for affected language surfaces. Rerun only failures and their direct
dependencies. Full backend/frontend suites belong solely to the final PATCH-049
validation gate after all accepted batches.

Where backend tests need a database, use only the established governed
`TEST_DATABASE_URL` test database pattern and never print credentials. No
runtime/configuration alteration is allowed to satisfy tests. Environment
failures are recorded separately from implementation failures and never
remediated by weakening a test or redirecting to production data.

## 9. Security review plan

Every batch must prove its applicable portion of: trusted actor, server-derived
Organization, Project/Workspace isolation, authorization-before-disclosure,
payload-free protected outcomes, no Human/private-storage/hidden-count leak,
safe logs, public-boundary-only integration, no foreign persistence, zero EKG,
zero AI/model import/call and the PATCH-050 firewall. Batch 3 also proves that
the UI does not recreate authority or fabricate real-data claims.

## 10. Failure, rollback and recovery model

PATCH-049 performs no canonical write. There is no domain rollback, retry,
idempotency, outbox or recovery record. Dependency/validation/bound failures
return their closed safe outcomes, and frontend failure alters no canonical
state. A partial assessment remains an explicit observation, not a retryable
write or cached result.

## 11. Migration assessment

No migration, schema change or data backfill is planned. Alembic remains at
sole head `e04700000001`. If any implementation requires persistence or a
migration, stop: it is a design conflict rather than a planning exception.

## 12. Final validation, review and governance path

After Batch 1–3 acceptance, execute the separately authorized final gate:

```text
focused PATCH-049 suites
-> full backend + frontend suites
-> frontend typecheck/build/static
-> static/import/security/non-disclosure/no-AI/no-EKG/no-write checks
-> no-migration and sole Alembic-head verification
-> final independent implementation review
-> Human QG-11
-> QG-12 exact delivery readiness
```

QG-12 establishes an exact delivery allow-list, excludes unrelated dirty work,
verifies staged scope/checks, then requires explicit Human delivery authority
before commit/push. Delivery verification precedes append-only closure records,
whose isolated commit/push requires separate authority. PATCH-049 becomes
DONE/CLOSED only after both delivery and closure verification pass. PATCH-050
remains not started throughout.

## 13. Implementation stop conditions

Stop an implementation batch and report the exact prerequisite if it requires:
an accepted contract change; foreign repository/ORM/Session/UoW access;
caller-supplied Organization/context; unprotected disclosure; a missing owner
field/port; EKG; persistence/migration; AI/model/provider; dynamic rules;
score/percentage; task/workflow; solution recommendation; an unlisted file; or
PATCH-050 behavior.
