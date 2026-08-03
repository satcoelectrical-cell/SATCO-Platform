# AR-028 — Universal Engineering Capture Foundation Architecture Review

## 1. Review Control

| Field | Value |
|---|---|
| Review ID | AR-028 |
| Related PATCH | PATCH-028 v1.0 |
| Review status | COMPLETE |
| Architecture verdict | PASS FOR EDS |
| Manifesto Compliance | PASS |
| Implementation readiness | NOT READY |
| Reviewer | Codex, independent technical architecture reviewer |
| Human scope decision | Product Owner approved |
| Date | 2026-08-02 |

This review authorizes progression to EDS-028. It does not authorize source,
schema, migration, API, or runtime implementation and does not replace later
Human EDS/IDS/readiness approvals.

## 2. Sources Reviewed

- Constitution and Engineering Intelligence Manifesto v1.0;
- Product Bible and platform Architecture;
- accepted ADR-013 through ADR-021 where relevant;
- Engineering Intelligence Architecture v0.1 and its independent review;
- Governance Model, Development Lifecycle, and Framework v1.1 with QG-M1;
- completed PATCH-023 through PATCH-027 and their design/review records;
- current EngineeringObject, EngineeringRelationship, Evidence, Context,
  Workspace, Organization, port, repository, service, API, migration, and test
  boundaries;
- current repository and worktree state.

## 3. Architecture Findings

### Engineering problem and Version-1 value

**PASS**

One governed point of origin solves a real continuity problem: original
Engineering Experience can be preserved before later interpretation or review.
The scope is bounded to textual Human capture and does not introduce broad
knowledge-management or automation behavior.

### Aggregate boundary

**PASS FOR EDS**

An independent `EngineeringExperienceCapture` aggregate is compatible with the
existing EKG boundaries. It avoids placing mutable notes inside
EngineeringObject and avoids expanding PATCH-027 Evidence into source-content
storage. EDS must define the aggregate's exact lifecycle, commands, invariants,
and reference compatibility before implementation design.

### Capture versus authority

**PASS**

The PATCH distinguishes authenticity of capture from truth, Evidence,
recommendation, approval, knowledge, and memory. Immutable original content,
explicit correction/supersession, and Human provenance preserve this boundary.

### Context and security

**PASS WITH EDS REQUIREMENTS**

Trusted Organization and Creator derivation, optional bounded context,
deny-by-default authorization, protected disclosure, and cross-scope
prohibitions are architecturally correct. EDS must close the optional Project
rule, confidentiality derivation, reference visibility, and every operation's
authorization matrix.

### Data and transaction architecture

**PASS WITH EDS REQUIREMENTS**

PostgreSQL, Alembic, optimistic concurrency, explicit commands, one Unit of
Work, atomic Audit/Domain Events/idempotency, and logical history follow the
completed foundations. Exact schema and transaction contracts remain properly
deferred to EDS/IDS.

### Provider independence and AI boundary

**PASS**

PATCH-028 contains no AI/provider dependency and prohibits AI authority,
autonomous capture, authoring, review, and publishing. The captured record
therefore remains provider-neutral.

### Scope discipline

**PASS**

Files, OCR, connectors, Inbox UI, Human Review workflow, AI Author, publishing,
Organizational Memory, semantic/vector/graph technology, frontend, and unrelated
refactoring are explicitly excluded.

## 4. Manifesto Compliance

| Principle | Result | Architecture evidence |
|---|---|---|
| Engineering First | PASS | Preserves real Engineering Experience at its work origin. |
| Capture Once | PASS | One immutable original capture is enriched later. |
| Human Authority | PASS | Capture grants no truth or approval; Creator is Human. |
| Engineering Context Is Sacred | PASS | Provenance and governed scope remain attached. |
| Evidence Before Assumption | PASS | Capture is explicitly distinct from Evidence and fact. |
| Context Before Recommendation | PASS | Recommendations are outside scope; context precedes later use. |
| Intelligence Before Automation | PASS | No autonomous capture or automated action exists. |
| Explainability | PASS | Origin, source reference, scope, history, and limitations remain traceable. |
| Provider Independence | PASS | No AI provider owns or processes the canonical record. |
| Organizational Ownership | PASS | Capture is governed inside trusted Organization scope. |
| Continuous Evolution | PASS | Correction/supersession preserves original history. |

**Manifesto Compliance: PASS**

**Unresolved Manifesto conflict: NONE**

## 5. Required EDS Decisions

EDS-028 must define without delegation to code:

1. complete lifecycle and authority matrices;
2. creation and post-creation command set;
3. exact original-content and source-reference limits/normalization;
4. capture origin/type closed vocabulary;
5. whether Organization-wide capture is permitted and under which policy;
6. Project/Workspace/Discipline/EngineeringObject compatibility rules;
7. confidentiality model and constituent visibility intersection;
8. Creator/steward/responsibility rules;
9. correction, withdrawal, rejection, and supersession semantics;
10. duplicate/no-op behavior and idempotency scope;
11. Audit, Domain Event, transaction, and outbox requirements;
12. explicit command/query/API/error boundary;
13. migration, rollback, performance, security, and regression requirements;
14. QG-M1 principle-to-behavior evidence.

## 6. Open Gates

- EDS-028 does not yet exist;
- independent EDS Review has not passed;
- IDS-028 and Implementation Plan do not exist;
- IRR-028 has not issued READY;
- exact implementation file/schema/API/test boundary is undefined.

These are lifecycle gates, not architecture failures.

## 7. Verdict

**PASS — ARCHITECTURE APPROVED FOR EDS-028**

The proposed boundary is coherent, Manifesto-aligned, compatible with completed
foundations, and sufficiently bounded for engineering design.

```text
Manifesto Compliance: PASS
Manifesto Alignment Verified: NO
QG-M1 Readiness Result: PENDING
PATCH-028 implementation: NOT READY
```

## 8. Revision History

| Version | Date | Description |
|---|---|---|
| 1.0 | 2026-08-02 | Independent architecture review PASS for EDS progression. |
