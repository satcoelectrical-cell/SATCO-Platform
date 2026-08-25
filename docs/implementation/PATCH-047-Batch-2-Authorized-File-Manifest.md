# PATCH-047 Batch 2 — Authorized File Manifest

## Scope

Application/integration only for Project Risk, Project Issue, and Human
Decision. This is the second Plan-047 step, using the accepted Batch 1 root,
history, idempotency, outbox, repository, and UoW foundation.

## Authorized files

- MODIFY `backend/app/schemas/project_control.py` — closed command/read/result
  DTOs needed for Risk, Issue and Decision command handling.
- MODIFY `backend/app/repositories/project_control_repository.py` — scoped
  no-commit reads and locked root/idempotency access only.
- MODIFY `backend/app/repositories/project_control_unit_of_work.py` — one
  Session transaction, Audit and outbox staging; no policy/composition.
- CREATE `backend/app/services/project_control_service.py` — application
  behavior, authorization-before-disclosure, optimistic concurrency, history,
  idempotency, Audit/outbox staging and closed outcomes.
- CREATE `backend/tests/test_project_control_service.py` — focused Risk,
  Issue and Decision behavior, authorization, idempotency and history tests.
- CREATE `backend/tests/test_project_control_transaction.py` — real-UoW
  rollback, Audit/outbox/idempotency atomicity tests.
- CREATE `backend/tests/test_project_control_security.py` — protected
  cross-scope and Issue/blocker non-mutation evidence.
- CREATE `docs/reviews/PATCH-047-Batch-2-Implementation-Review.md` —
  independent review, findings and re-review chronology.
- CREATE `docs/reviews/PATCH-047-Batch-2-Human-Acceptance.md` — final Human
  acceptance record only after Critical/Major are zero.

## Explicit exclusions

No Change or Change Impact service behavior (Batch 3); no router, composition,
frontend, AI, canonical target adapter, foreign repository/ORM/Session access,
or PATCH-048 work. Issue behavior cannot create, clear, or mutate PATCH-045
blockers, Activities, Milestones, or Project state.

## Evidence and stop conditions

Focused service/security/transaction tests must prove authorized creation and
accepted transitions, exact and conflicting replay, history, cross-scope
protected outcomes, Issue blocker non-mutation, Decision successor immutability,
and rollback on Audit/outbox/idempotency failure. Stop for a required foreign
canonical contract, an accepted IDS/EDS change, an out-of-boundary file, or
any need to implement Change/Impact/transport behavior.
