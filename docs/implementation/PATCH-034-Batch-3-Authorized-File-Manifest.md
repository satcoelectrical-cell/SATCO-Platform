# PATCH-034 — Batch 3 Authorized File Manifest

## 1. Governance State

| Item | State |
|---|---|
| PATCH | PATCH-034 — Engineering Organizational Memory |
| Batch | Batch 3 — Canonical Integration |
| Steps | S05–S06 only |
| Batch 1 | ACCEPTED / COMPLETE |
| Batch 2 | ACCEPTED / COMPLETE |
| Human Batch 3 preparation authority | GRANTED |
| Batch 3 implementation authority | GRANTED for S05–S06 and focused remediation of B3-MAJ-01..03 |
| Batch 4 and later authority | NOT GRANTED |

This reconciled manifest is the complete and exclusive Batch 3 implementation
boundary. Human authority is limited to S05–S06 and focused remediation of
B3-MAJ-01..03; it grants no Batch 4 or later authority.

## 2. Verified Repository Assumptions

The accepted Technical Report application service exposes
`TechnicalReportService.get_report(TechnicalReportActor, report_id)` and returns
an authorization-filtered view carrying the immutable accepted snapshot,
lifecycle, scope, owner, and version needed by `AcceptedReportReader`. The
adapter can therefore require the exact accepted lifecycle, accepted aggregate
version, accepted snapshot digest, Organization, Workspace, optional Project,
and requested source identity without importing Technical Report persistence.

The current canonical provenance application boundaries are present:

- Capture:
  `EngineeringExperienceCaptureService.read_authorized_detail(...)`;
- Evidence: `EvidenceService.get(evidence_id, EvidenceActor(...))` with
  `ReadEvidence` authorization;
- Engineering Object:
  `EngineeringObjectService.get(..., AuthorizationContext("ReadEngineeringObject", ...))`;
- Engineering Relationship:
  `EngineeringRelationshipService.get(...,
  RelationshipAuthorizationContext("ReadEngineeringRelationship", ...))`.

Their authorized response contracts expose the identity, version, Organization,
Project/Workspace, and variant-specific object/endpoint fields required by
IDS-034. The accepted Batch 1 inward ports and typed requests already define
`AcceptedReportReader` and `MemoryProvenanceAuthorizer`; no port amendment is
required. Current canonical application services remain the sole owners of
their authorization and read transactions.

## 3. Exact Authorized File Boundary

### 3.1 Production

| File | Action | Step | Authorized responsibility | Necessity and dependencies | Prohibited responsibility |
|---|---|---|---|---|---|
| `backend/app/ports/organizational_memory.py` | MODIFY | S06 | Preserve the accepted single-request method and add the explicit stateless logical-operation method over one-to-three typed provenance requests, returning the existing closed result union. | Required to express the already-accepted three-request/256-identity logical-operation bound without hidden adapter state or Batch 4 orchestration. | No command/UoW/service behavior; no new result vocabulary; no persistence or deferred capability. |
| `backend/app/adapters/organizational_memory.py` | CREATE/MODIFY | S05–S06 | Implement the accepted `AcceptedReportReader` adapter over `TechnicalReportService.get_report`; translate `MemoryActor` to `TechnicalReportActor`; require the exact accepted source version/digest and matching Organization/Workspace/Project scope; construct only the deterministic admitted representation already defined by Batch 1. Implement both accepted single-request and explicit stateless logical-operation provenance authorization over four context-specific canonical service collaborators; deduplicate and order deterministically; enforce 1–100 items per request, at most three ordered requests and 256 unique identities overall; validate every returned identity/version-independent current visibility and exact contextual scope; return only the closed success/protected/unavailable results and disclose nothing until every item succeeds. | Required by accepted Plan S05–S06. Depends on accepted Batch 1 models/ports, immutable Technical Report snapshot contracts, and the five existing canonical application-service boundaries. | No canonical repository, ORM record, SQLAlchemy `Session`, canonical UoW, authorization-policy or reference-validator implementation import; no foreign mutation; no memory repository/UoW/transaction/Audit/outbox/idempotency behavior; no service orchestration, reads/pagination, API/composition, persistence, dispatch, AI, frontend, or deferred source class. |

### 3.2 Tests

| File | Action | Step | Authorized responsibility | Necessity and dependencies | Prohibited responsibility |
|---|---|---|---|---|---|
| `backend/tests/test_organizational_memory_integration.py` | CREATE | S05–S06 | Exercise the real canonical application-service method boundaries with bounded in-memory/request-scoped collaborators: exact accepted Technical Report success and deterministic projection; draft/wrong version/wrong digest/cross-scope/revoked/missing/unavailable outcomes; exact Capture, Evidence, Engineering Object, and Engineering Relationship request arguments and response-context checks; deterministic deduplication/order/call bounds; unsupported provenance ineligibility. | Required Plan integration evidence for both steps. Depends on the new adapter, accepted Batch 1 contracts, and current canonical service APIs and DTOs. | No direct foreign repository/Session/UoW fixture as the adapter dependency; no Batch 4 transaction orchestration or side-record assertions; no modification of canonical tests or implementation. |
| `backend/tests/test_organizational_memory_security.py` | CREATE | S05–S06 | Prove authorization-before-disclosure, trusted Organization/Workspace/Project context, all-or-nothing mixed denial, partial dependency failure, response-context mismatch, payload-free protected/unavailable outcomes, no partial identity/count/ordinal/family disclosure, prohibited plaintext exclusion, and static import/scope boundaries. | Required by the accepted Plan’s initial adapter/non-disclosure evidence surface and IDS-034 security matrix. | No memory command/UoW, read pagination, transport/authentication HTTP, router, database-role, migration, UI, AI, or deferred-capability evidence. |

The exact authorized boundary is therefore:

```text
MODIFY backend/app/ports/organizational_memory.py
CREATE/MODIFY backend/app/adapters/organizational_memory.py
CREATE/MODIFY backend/tests/test_organizational_memory_integration.py
CREATE/MODIFY backend/tests/test_organizational_memory_security.py
```

No other production, test, migration, configuration, or governance file may be
created or modified under Batch 3 implementation authority.

## 4. S05 / S06 Mapping

### S05 — Accepted Technical Report Source Adapter

S05 is limited to:

1. translate trusted `MemoryActor` identity to `TechnicalReportActor` without
   accepting client-controlled Organization context;
2. invoke exactly one authorized canonical Technical Report `get_report` read
   for one requested source;
3. require the canonical report to be Human-accepted and to expose an immutable
   accepted snapshot;
4. compare report identity, accepted aggregate version, accepted snapshot
   digest, Organization, Workspace, and optional Project exactly;
5. construct the existing deterministic Batch 1 admitted projection/manifest
   contract without paraphrase, inference, omission, synthesis, or ownership
   transfer; and
6. translate canonical protected/dependency failures only to the accepted
   payload-free results.

S05 owns no Technical Report read authorization, persistence, UoW, acceptance,
publication, mutation, or transaction.

### S06 — Context-Specific Canonical Provenance Authorization

S06 is limited to:

1. the exact four V1 variants: Capture, Evidence, Engineering Object, and
   Engineering Relationship;
2. each variant’s accepted current application-service call and its own typed
   actor/authorization context;
3. pre-call Organization and scope compatibility checks followed by post-call
   exact response identity/context checks;
4. deterministic deduplication by identity type, identity, and source version;
5. accepted order and cardinality bounds: 1–100 unique identities per request,
   no more than three ordered requests, no more than 256 unique identities in
   the complete logical operation, and no more than one owning-service read per
   unique identity;
6. all-or-nothing safe result construction in accepted-snapshot ordinal order;
7. unsupported/noncanonical provenance as admission-ineligible, never silently
   omitted; and
8. reusable recheck entry points through the same inward contract for later
   Batch 4 composition, without implementing Batch 4 transaction sequencing.

S06 does not create a generic authorization vocabulary, infer authorization
from Technical Report visibility, or expose partial results.

## 5. Prerequisites and Dependencies

| Prerequisite | Repository evidence | Status |
|---|---|---|
| Accepted PATCH/EDS/IDS/Implementation Plan and IRR-034 | Governance chain established | SATISFIED |
| Batch 1 typed source/provenance/result contracts and ports | Accepted nine-file Batch 1 | SATISFIED |
| Batch 2 persistence foundation | Accepted S03–S04; not imported by Batch 3 adapters | SATISFIED |
| Immutable accepted Technical Report snapshot and authorized read | `TechnicalReportService.get_report` and accepted snapshot contracts | SATISFIED |
| Capture authorized detail boundary | `read_authorized_detail` | SATISFIED |
| Evidence authorized read boundary | `EvidenceService.get` / `ReadEvidence` | SATISFIED |
| Engineering Object authorized read boundary | `EngineeringObjectService.get` / `ReadEngineeringObject` | SATISFIED |
| Engineering Relationship authorized read boundary | `EngineeringRelationshipService.get` / `ReadEngineeringRelationship` | SATISFIED |
| Direct foreign persistence access | Not required or authorized | SATISFIED |

## 6. Canonical-Boundary Evidence Expectations

Implementation review must materially prove:

1. S05 invokes only the canonical Technical Report application service and
   never imports a Technical Report repository, ORM row, Session, UoW, policy,
   or validator implementation.
2. Exact accepted source success preserves every accepted snapshot field and
   digest; draft, absent snapshot, wrong source version, wrong digest,
   Organization/Workspace/Project mismatch, revoked/inaccessible source, and
   dependency failure produce only the declared closed result.
3. Each S06 variant calls its exact canonical service with the actor and context
   stated in IDS-034; tests assert every argument and response field used for
   contextual coherence.
4. Current authorization is independently performed for every unique retained
   provenance identity; Technical Report visibility never substitutes for it.
5. Duplicate identities are read once, results are restored to deterministic
   accepted ordinal order, and exact 100/three/256 bounds fail closed.
6. No adapter mutates or commits canonical or memory state, and no canonical
   ownership moves into Organizational Memory.
7. Static/prohibited-pattern checks cover foreign repositories, ORM models,
   SQLAlchemy Session, canonical UoWs, direct SQL, commits, and later-batch
   modules/behaviors.

## 7. Authorization and Non-Disclosure Expectations

Evidence must prove:

- trusted actor Organization equals the requested source, memory scope, and
  every provenance identity Organization before canonical calls;
- optional Project/Workspace and variant-specific Engineering Object or
  Relationship endpoint contexts match both the accepted basis and authorized
  canonical response;
- any missing, inaccessible, malformed, cross-Organization, cross-scope,
  mismatched, revoked, unsupported, or partially denied item yields one
  payload-free protected outcome for the logical operation;
- dependency failure yields one payload-free unavailable outcome;
- no partial item, identity, count, ordinal, source family, contextual field,
  canonical exception detail, content, locator body, Capture text, Evidence
  body, report plaintext, or protected provenance plaintext is disclosed;
- successful safe provenance contains exactly one authorized safe digest entry
  per requested item in deterministic ordinal order; and
- denial equivalence is stable regardless of which canonical identity failed.

## 8. Explicit Exclusions and Scope Control

Batch 3 prohibits:

- modification of Technical Report, Capture, Evidence, Engineering Object, or
  Engineering Relationship production/test contracts;
- direct access to any foreign table, repository, ORM record, Session, UoW,
  transaction, policy implementation, or reference-validator implementation;
- Organizational Memory UoW, command orchestration, mutation execution, Audit,
  outbox, idempotency, rollback, concurrency, or final-commit sequencing
  assigned to Batch 4;
- active/history read orchestration, protected listing, pagination,
  continuation, or count behavior assigned to Batch 5;
- dependency composition, router, API, or main registration assigned to Batch
  6;
- migration/schema/role changes, frontend/UI, AI/Copilot, semantic/vector
  retrieval, graph expansion, other admission sources, multi-source synthesis,
  cross-Organization sharing, autonomous admission/reuse, enterprise boards,
  or any deferred PATCH-034 capability; and
- Batch 4–7 implementation, validation packaging, delivery, or closure work.

Scope validation must compare the changed path set exactly with Section 3 and
scan the production adapter for prohibited imports and transaction/persistence
patterns.

## 9. Stop Conditions

Batch 3 implementation must stop and report BLOCKED if:

1. the accepted Technical Report snapshot/version/digest/scope cannot be
   obtained and rechecked through `TechnicalReportService.get_report`;
2. any retained provenance class cannot be independently authorized through
   its current canonical application-service boundary and exact typed context;
3. implementation requires a canonical repository, ORM record, Session, UoW,
   policy/validator implementation, direct SQL, or canonical production-file
   modification;
4. a canonical response lacks a required identity, Organization, Project,
   Workspace, version, or variant-specific context field;
5. all-or-nothing protected disclosure or deterministic 100/three/256 bounds
   cannot be enforced through the accepted inward contracts;
6. implementing final recheck requires Batch 4 transaction/UoW behavior rather
   than a reusable S05/S06 adapter call;
7. any accepted PATCH/EDS/IDS contract must change or an unsupported authority
   must be invented;
8. any file outside Section 3 is required;
9. any focused integration/security, adjacent canonical regression,
   static/import, prohibited-pattern/scope, or `git diff --check` gate fails; or
10. Batch 4 or deferred behavior becomes necessary.

## 10. Required Validation Before Independent Review

The later authorized implementation run must execute:

- focused `test_organizational_memory_integration.py` and
  `test_organizational_memory_security.py`;
- relevant existing Technical Report, Capture, Evidence, Engineering Object,
  and Engineering Relationship service/security regressions;
- accepted Batch 1 contract/schema regression and Batch 2 focused persistence
  regression sufficient to prove preservation;
- static/import validation;
- exact changed-path and prohibited-pattern checks; and
- `git diff --check`.

No Batch 4 implementation or final PATCH evidence is part of this validation.

## 11. Readiness and Authority

All S05–S06 canonical application boundaries and accepted inward contracts are
present. The exact three-file implementation boundary is coherent and minimal.

Batch 3 implementation readiness: READY

Batch 3 implementation authority: GRANTED and exercised within this boundary

Batch 4 authority: NOT GRANTED

Exact next governance action: obtain explicit Human Batch 3 implementation
authority for this exact three-file boundary, then implement S05–S06 only.
