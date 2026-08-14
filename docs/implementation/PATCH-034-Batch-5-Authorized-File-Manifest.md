# PATCH-034 Batch 5 Authorized File Manifest

## 1. Authority and Scope

| Item | State |
|---|---|
| PATCH | PATCH-034 — Engineering Organizational Memory |
| Batch | Batch 5 — Reads, Pagination, and Protected Disclosure |
| Steps | S11–S12 only |
| Batches 1–4 | HUMAN ACCEPTED / COMPLETE |
| Human Batch 5 preparation authority | GRANTED |
| Batch 5 implementation authority | NOT GRANTED |
| Batch 6 and later authority | NOT GRANTED |

This manifest is the complete and exclusive Batch 5 implementation boundary.
It authorizes no implementation until separate Human Batch 5 implementation
authority is granted.

## 2. Repository and Dependency Assessment

Accepted Batch 1 already provides the exact read requests, standing-specific
DTOs, protected result unions, ordering anchor, candidate criteria/page, and
service/repository protocols required by S11–S12. Accepted Batch 2 provides the
canonical ordered candidate query. Accepted Batch 3 provides the authorized
Technical Report and provenance application adapters. Accepted Batch 4 provides
the application service, same-Session memory authorization policy, and no-commit
repository boundary.

No new schema, model, port, exception, adapter, migration, configuration,
credential, UoW, or canonical-capability production surface is required.
Continuation support is application-owned and may use the existing application
secret without changing configuration. Discovery of a need to modify any such
surface is a stop condition and requires separate Human manifest reconciliation.

## 3. Exact Authorized File Boundary

### 3.1 Production

| File | Action | Step | Authorized responsibility | Why required | Prohibited responsibility |
|---|---|---|---|---|---|
| `backend/app/services/organizational_memory_service.py` | MODIFY | S11–S12 | Implement `get_active`, `inspect_history`, and `list_active`; authorize before DTO construction; perform current accepted-source reads; request provenance only when required; independently protect requested predecessor/replacement links; construct exact standing-specific results; validate/create opaque authenticated versioned 15-minute continuations; enforce last-evaluated anchoring, page/candidate/canonical-call bounds, and payload-free protected outcomes. | The accepted application service owns read orchestration, disclosure ordering, continuation binding, and closed-result mapping. | No router/API/composition; no persistence or transaction ownership; no canonical repository/ORM/Session/UoW access; no retained-snapshot fallback authority; no hidden totals; no mutation behavior change; no semantic/vector/relevance/graph search. |
| `backend/app/repositories/organizational_memory_repository.py` | MODIFY | S11–S12 | Complete only accepted scoped read/history and canonical active-candidate operations needed by the service; apply required Workspace and optional Project/purpose filters before candidate return; preserve strict `(admitted_at DESC, memory_id ASC)` order, strict post-anchor predicate, and bounded `candidate_limit + 1` look-ahead. | S11 needs scoped root/history retrieval; S12 needs deterministic bounded candidate pages without totals. | No authorization/disclosure policy; no continuation signing; no canonical foreign reads; no commit/rollback; no mutation/UoW expansion; no aggregate count/global total query; no search/ranking. |
| `backend/app/repositories/organizational_memory_unit_of_work.py` | MODIFY | S11–S12 | Extend the existing memory authorization policy only for accepted `get_active`, `list_active`, and `inspect_history` operation rows, using active trusted actor/Organization/membership, exact Workspace/Project scope, audience, Workspace membership/assignment, and admitting-Human history authority. Preserve every mutation branch unchanged. | The concrete policy previously rejected all read operations, so the accepted read authorization matrix could not be represented inside the original boundary. | No new role or authority; no service/read DTO construction; no canonical foreign persistence; no mutation-policy widening/strengthening; no Batch 6 composition. |

### 3.2 Tests

| File | Action | Step | Authorized responsibility | Why required | Prohibited responsibility |
|---|---|---|---|---|---|
| `backend/tests/test_organizational_memory_pagination.py` | CREATE | S12 | Prove canonical ordering, page sizes 1/100, strict last-evaluated continuation anchor, denied candidates between visible items, candidate/round/canonical-call bounds, tamper/expiry/actor/Organization/scope/filter/page-size binding, no skips/duplicates, and `visible_total == len(items)` only. | The accepted Plan assigns focused continuation and bounded-query evidence to this file. | No HTTP/router tests, migration changes, semantic/vector/relevance search, or hidden-total assertions. |
| `backend/tests/test_organizational_memory_service.py` | MODIFY | S11–S12 | Add exact service evidence for active reads, listing, history standing variants, protected results, source revocation/unavailability, optional provenance, protected linked identities, authorization-before-DTO construction, and preservation of S08–S10. | Existing service tests are the focused application evidence surface. | No transport/authentication fixture, Batch 6 composition, or accepted command-contract weakening. |
| `backend/tests/test_organizational_memory_security.py` | MODIFY | S11–S12 | Add protected equivalence and non-disclosure evidence for nonexistent/inaccessible/revoked records, audience/scope denial, hidden candidate/count/lineage/provenance omission, tampered/expired/mismatched continuations, and plaintext/diagnostic exclusion. | S11–S12 require material security evidence beyond happy-path service tests. | No router/API behavior, canonical policy modification, privileged source-revocation bypass, or timing-equality promise. |
| `backend/tests/test_organizational_memory_integration.py` | MODIFY | S11–S12 | Prove reads use current canonical Technical Report application boundaries and context-specific provenance authorization, including revocation and all-or-nothing provenance disclosure, without foreign persistence access. | Current-source and requested-provenance disclosure must be proven against the accepted Batch 3 integrations. | No canonical implementation modification; no direct foreign repository/ORM/Session/UoW; no mutation orchestration or Batch 6 behavior. |

The exact Batch 5 implementation boundary is:

```text
MODIFY backend/app/services/organizational_memory_service.py
MODIFY backend/app/repositories/organizational_memory_repository.py
MODIFY backend/app/repositories/organizational_memory_unit_of_work.py
CREATE backend/tests/test_organizational_memory_pagination.py
MODIFY backend/tests/test_organizational_memory_service.py
MODIFY backend/tests/test_organizational_memory_security.py
MODIFY backend/tests/test_organizational_memory_integration.py
```

No other production, test, migration, configuration, or documentation file is
authorized for Batch 5 implementation.

## 4. S11 and S12 Mapping

### S11 — Active Reads and Historical Inspection

- `get_active` returns exactly one active detail only after trusted actor/scope,
  memory operation, current canonical source, and requested provenance checks.
- `inspect_history` returns exactly the accepted active, withdrawn, or
  superseded DTO. Transition fields exist only for their standing.
- Predecessor/replacement links are independently authorized when requested.
  `None` is the indistinguishable representation of absent, unrequested, or
  protected linked identity.
- Retained projection is never fallback authority after source revocation or
  canonical unavailability.
- Provenance is empty unless requested and wholly authorized. Partial
  authorization never yields a partial identity, count, ordinal, or locator.

### S12 — Active Listing and Continuation

- Only active roots participate. Required exact Workspace and optional exact
  Project/purpose filters precede candidate authorization and page assembly.
- Canonical order is `(admitted_at DESC, memory_id ASC)`.
- Page size is 1–100, default 50. A repository round returns at most
  `candidate_limit + 1` rows; a request evaluates at most 10 rounds and 100
  canonical candidates/calls, never more than one source read per candidate.
- The continuation anchor is the last evaluated candidate key, including a
  denied candidate or the candidate at which the scan/call bound is reached.
  It is never the last returned item.
- The strict next predicate is `admitted_at < anchor.admitted_at OR
  (admitted_at = anchor.admitted_at AND memory_id > anchor.memory_id)`.
- Continuation is opaque, authenticated, versioned, expires after 15 minutes,
  and binds actor, Organization, scope, filters, page size, anchor, and query
  fingerprint. Tamper, expiry, mismatch, or unsupported version returns the
  payload-free `invalid_request` result; replay reauthorizes candidates.
- `visible_total` equals only `len(items)`. No hidden, authorized, filtered,
  global, historical, or candidate total is calculated or disclosed.
- Listing does not resolve provenance and exposes no hidden candidate identity,
  count, standing, source, lineage, or denial diagnostic.

## 5. Prerequisites and Dependencies

1. PATCH-034 Architecture, EDS-034, IDS-034, Implementation-Plan-034, and
   IRR-034 remain accepted and unchanged.
2. Batches 1–4 remain Human ACCEPTED / COMPLETE, including resolution of all
   Batch 1–4 Critical/Major findings.
3. Batch 1 closed read/history/page/result contracts remain authoritative.
4. Batch 2 ordered repository and DB guards remain intact; repository ownership
   remains no-commit.
5. Batch 3 accepted-report/provenance adapters remain the only canonical
   application integration boundary.
6. Batch 4 authorization/UoW/command/reliability behavior remains preserved.
7. Existing application secret and cryptographic dependency are usable for the
   accepted continuation contract without configuration modification.

## 6. Required Read and Security Evidence

Evidence must materially prove:

1. exact active detail and all three standing-specific history shapes;
2. authorization before projection, source, standing, lineage, provenance, or
   identity disclosure;
3. current source revocation/unavailability never serves retained content;
4. predecessor/replacement requested, absent, authorized, and denied matrices,
   with absent/denied indistinguishable as `None`;
5. provenance omitted unless requested and returned only all-or-nothing after
   context-specific current authorization;
6. nonexistent, inaccessible, revoked, wrong-scope, and audience-denied cases
   have stable payload-free protected outcomes without plaintext or diagnostics;
7. listing includes only authorized active summaries and discloses no hidden
   candidate identities, counts, standings, lineage, or provenance; and
8. Batches 1–4 focused contract, persistence, integration, command, replay,
   transaction, and non-disclosure regressions remain passing.

## 7. Required Pagination and Bounded-Query Evidence

Evidence must materially prove:

1. exact filter-before-authorization behavior and canonical ordering, including
   equal timestamps ordered by ascending UUID;
2. page-size boundaries 1 and 100 and rejection outside 1–100;
3. continuation uses the last evaluated key when a denied candidate lies
   between visible candidates and when the scan/call bound terminates work;
4. successive pages have no skipped or duplicate authorized item;
5. denied candidates are neither revisited nor disclosed;
6. authenticated token tamper, expiry, version, actor, Organization, Workspace,
   Project, purpose, page-size, and fingerprint mismatch fail payload-free;
7. at most 10 candidate rounds, 100 evaluated candidates, 100 canonical source
   calls, one source call per candidate, and bounded repository look-ahead;
8. listing performs no provenance N+1 and no projection-field read expansion;
9. `visible_total == len(items)` and no query computes a hidden/global/
   authorized/historical total; and
10. continuation contains no plaintext identity/count and grants no authority.

## 8. Explicit Exclusions and Scope Control

Batch 5 may not implement or test as a Batch 5 deliverable:

- dependency composition, router/API, `main.py` registration, HTTP/JWT transport
  evidence, or transport serialization (Batch 6);
- final full-suite/QG-M1/final-review packaging (Batch 7);
- any new schema, migration, table, index, role, credential, configuration,
  repository commit, transaction boundary, Audit/outbox/idempotency behavior,
  command mutation, or canonical capability change;
- direct Technical Report, Capture, Evidence, Engineering Object, or Engineering
  Relationship repository/ORM/Session/UoW access;
- frontend/UI, AI/Copilot, semantic/vector/similarity/relevance search,
  embeddings, graph expansion/ranking, additional admission sources,
  multi-source synthesis, cross-Organization sharing, autonomous reuse,
  enterprise boards, EDS-030/031 behavior, or any deferred capability.

Scope validation must confirm that only Section 3 files change, imports preserve
dependency direction, no prohibited production route/configuration/migration is
added, and no totals/count/search/backdoor-disclosure pattern is introduced.

## 9. Stop Conditions

Stop Batch 5 immediately and report BLOCKED if:

1. an accepted PATCH/EDS/IDS/Plan contract must change;
2. a file outside Section 3 is required;
3. direct foreign canonical persistence or policy implementation is required;
4. any DTO is constructed before all applicable authorization succeeds;
5. retained memory becomes fallback authority after source denial/revocation;
6. a linked identity's absent and protected states become distinguishable;
7. provenance can be partially disclosed;
8. hidden/global/authorized/historical totals or hidden-candidate counts are
   computed or disclosed;
9. continuation uses the last returned rather than last evaluated candidate;
10. scanning exceeds 10 rounds, 100 candidates/canonical calls, one canonical
    source read per candidate, or repository bounded look-ahead;
11. token authenticity, 15-minute expiry, or complete binding cannot be proven;
12. repository commit/UoW ownership or Batch 1–4 behavior is weakened;
13. Batch 6+, frontend, AI, search, or deferred behavior becomes necessary; or
14. any required focused/regression/static/import/prohibited-pattern/scope/
    `git diff --check` gate fails.

## 10. Readiness and Authority

The accepted read contracts and Batches 1–4 dependencies support S11–S12 within
the reconciled exact seven-file implementation boundary above.

Batch 5 implementation readiness: READY

Batch 5 implementation authority: NOT GRANTED

Batch 6 authority: NOT GRANTED

Exact next governance action: implement S11–S12 only after explicit Human Batch
5 implementation authority for the reconciled exact seven-file boundary.
