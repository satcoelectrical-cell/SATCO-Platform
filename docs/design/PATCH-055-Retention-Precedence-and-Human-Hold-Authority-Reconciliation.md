# PATCH-055 — Retention Precedence & Human Hold Authority Reconciliation

Status: HUMAN ACCEPTED / COMPLETE

## Purpose
Close only the Checkpoint-B qualification gaps P055-RET-04/05 and P055-HLD-06 without expanding PATCH-055 scope.

## Accepted-source facts
EDS-055 freezes effective precedence as `human_subject_override > organization_default > platform_default`; Commercial V1 platform default is `retain_indefinitely`.
IDS-055 freezes the same precedence and permits a legacy subject with no retention row to remain `not_established` until an authorized retention decision is first required, at which point the deterministic platform default may be materialized through the normal governed retention transaction.
ADR-028/EDS-055 freeze hold placement/release as Human-governed and explicitly deny that authority to AI/background expiry.

## Reconciliation — RET-04/05
No Organization-default persistence or configuration owner is frozen by accepted IDS-055, and Checkpoint A created no such store. Therefore Checkpoint B MUST NOT invent an Organization-default table, setting, or migration.

For Commercial V1 Checkpoint B:
1. Explicit Human subject policy remains the highest-precedence materialized subject decision.
2. Organization-default resolution is a reserved precedence tier; it is used only when a valid Organization-default provider/value exists under an accepted owner. No such owner exists in the current accepted implementation, so this tier is absent rather than fabricated.
3. When no valid Human subject override or Organization default exists and an authorized retention decision requires materialization, the effective fallback is exactly `policy_source=platform_default`, `retention_mode=retain_indefinitely`, `retention_until=null`.
4. Ordinary read of a legacy subject with no retention row remains `not_established`/unestablished projection and MUST NOT auto-create history.
5. Default materialization is a normal attributable/auditable/idempotent retention transaction, not migration backfill.
6. No automatic expiry, disposition approval, or physical purge authority is created.

## Reconciliation — HLD-06
Hold place/release authority is Human-only. Current User/Organization/Project authorization is necessary but is not sufficient evidence that a caller is Human when invoked by AI/background automation.

Checkpoint B freezes an explicit application-service authority context for hold mutations:
- `human` is the only authority context permitted to place/release a hold.
- `ai`, `background`, `system`, missing/unknown authority context cannot place/release a Human hold.
- actor authority context is server-composed and MUST NOT be accepted from an untrusted client request body/header.
- existing User/Organization/Project authorization still runs and remains mandatory; authority context does not grant access.
- retention policy apply and disposition behavior are not broadened by this reconciliation.

Implementation remains inside accepted Checkpoint-B service/dependency/port/UoW/test files. No schema/model/migration/router/frontend change is authorized by this reconciliation.

## Qualification
P055-RET-04/05 must prove deterministic fallback and no fabricated legacy history; Organization-default absence must not be represented as an invented policy.
P055-HLD-06 must prove AI/background/system/unknown context cannot place or release a hold while Human context plus existing mutation authorization can.
All existing Checkpoint-B tests must remain green on disposable PostgreSQL.

## Boundary
No Checkpoint C/D, stage, commit, push, deploy, production/customer DB mutation, or PATCH-056 work is authorized.

Human acceptance recorded in conversation after explicit review/authorization of this limited reconciliation.
