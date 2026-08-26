# PATCH-049 Batch 2 — Authorized File Manifest

## Governance and scope

PATCH-049 Architecture, EDS, IDS, Implementation Plan and IRR are accepted/PASS;
Batch 1 is **ACCEPTED / COMPLETE**. This manifest grants no implementation
authority. Batch 2 connects the accepted pure evaluator to exactly one fresh,
all-ten-section PATCH-048 Project Context observation and exposes only:

`GET /projects/{project_id}/completeness?workspace_id=<optional-positive-int>`

It is read-only: no redesign of Project Context, the 14-rule catalog or Batch
1 contracts is authorized.

## Exact authorized future implementation files

| Path | Action | Sole responsibility | Prohibited responsibility |
|---|---|---|---|
| `backend/app/ports/project_completeness.py` | CREATE | Stateless narrow typed protocol for one fresh Project Context observation. | Owner repository, ORM, Session, UoW, graph, AI, writes. |
| `backend/app/dependencies/project_completeness.py` | CREATE | Request-scoped composition over public `get_project_context_application`; bind trusted actor/current user and completeness service. | Client Organization input, policy duplication, persistence. |
| `backend/app/services/project_completeness_service.py` | MODIFY | Public orchestration only: one fresh all-ten-section `page_size=100`, no-continuation observation; translation, exactly-once evaluation, bounds and closed mapping. | Repository/ORM/Session/UoW, mutation, cache, Audit/outbox/idempotency, EKG, AI. |
| `backend/app/api/v1/routers/project_completeness.py` | CREATE | One thin authenticated GET route, strict input construction, dependency invocation and payload-safe closed-result serialization. | Authorization policy, owner calls, catalog/evaluator, persistence, extra routes. |
| `backend/app/main.py` | MODIFY | Import and register the router exactly once. | Unrelated router/configuration changes. |
| `backend/tests/test_project_completeness_service.py` | MODIFY | Focused real-public-boundary orchestration evidence. | Database broadening or frontend. |
| `backend/tests/test_project_completeness_security.py` | CREATE | Actor/scope/protected-result/non-disclosure/no-foreign-access/no-EKG evidence. | New authorization system or persistence tests. |
| `backend/tests/test_project_completeness_api.py` | CREATE | Authentication, strict parameter and closed serialization evidence. | Frontend or broad API regression. |

The exact Batch 2 boundary is eight files: five **CREATE**, three **MODIFY**.
IDS-049's overall initial map lists files by first creation; the service and
service test were created by Batch 1 and therefore are correctly Batch 2
MODIFY surfaces for their explicitly Plan-assigned integration work.

## Batch 1 reuse and application boundary

`backend/app/schemas/project_completeness.py` is reused unchanged as the sole
owner of strict DTOs and closed results. The existing service is modified only
to add its accepted public assessment operation; its immutable catalog, digest
and pure `evaluate_project_context` behavior remain unchanged.

The application service receives a trusted `CompletenessActor` and strict
`CompletenessAssessmentRequest`; Organization is never client input. It calls
only the public PATCH-048 application boundary, exactly once, with all ten
sections at page size 100 and no continuation. The dependency is the only
construction point and reuses `get_project_context_application`, including its
server-derived authenticated Organization, actor and current user. No router or
completeness service receives a database handle, repository, ORM, Session, UoW
or foreign owner collaborator.

## Results, bounds and non-disclosure

The orchestration service owns integration validation and mapping. It preserves
the source observation interval and `complete_within_bounds`/`partial` status;
all 14 evaluators run exactly once after valid context translation. It enforces
at most 1,000 recursively inspected visible inputs, 14 rules/findings/questions/
checklist items, 56 evidence references, zero EKG calls, zero AI/model/provider
calls, and at most 131,072 serialized response bytes.

Malformed request maps to payload-free `invalid_request`; protected upstream
output maps to payload-free `protected_not_found`; malformed public output,
structural/bound failure and unavailable upstream output map to payload-free
`unavailable`. Protected, unavailable or truncated data never becomes
`missing`. The router accepts no Organization, catalog/rule/section selector,
continuation, score, graph or AI option, and discloses no existence, source
state, count, finding, hidden total, Human identity, private storage identity,
denial reason or exception text.

## Focused and adjacent evidence

Focused Batch 2 tests are exactly:

- `backend/tests/test_project_completeness_service.py`
- `backend/tests/test_project_completeness_security.py`
- `backend/tests/test_project_completeness_api.py`

They must prove actual public Project Context composition; one fresh all-ten
request; actor, server-derived Organization, Project and optional Workspace
scope; cross-Organization protected outcomes; success/partial/invalid/
unavailable mapping; all 14 rules; exactly-once evaluation; observation
partiality; 1,000-input and 131,072-byte limits; zero EKG/AI; no persistence;
and authenticated route serialization.

Read-only adjacent PATCH-048 regressions, not authorized for modification:

- `backend/tests/test_project_context_contracts.py`
- `backend/tests/test_project_context_service.py`
- `backend/tests/test_project_context_security.py`
- `backend/tests/test_project_context_api.py`

## Exclusions, migration and collision assessment

No frontend, graph traversal, AI/model/provider, persistence, repository, ORM,
Session, UoW, mutation, Audit, outbox, idempotency, migration, assessment
history, score/percentage, recommendation, task/workflow or PATCH-050 work is
authorized. Stop if any is required, the public Project Context boundary cannot
be used, fresh authorization cannot be preserved, integration bounds cannot be
enforced, a governing design change is needed, or an unrelated dirty hunk would
be overwritten.

Batch 2 creates no migration; expected Alembic sole head remains
`e04700000001`. All five CREATE paths are absent. Targeted status/diff checks
found no unrelated content in the three MODIFY paths. All pre-existing
unrelated work remains unstaged and untouched.

## Authority state

This manifest is **ACCEPTED / COMPLETE** after its separately recorded
Independent Manifest Review PASS. Batch 2 is **ELIGIBLE FOR SEPARATE HUMAN
IMPLEMENTATION AUTHORITY ONLY**. It grants no implementation, Batch 3,
migration, delivery, closure or PATCH-050 authority.
