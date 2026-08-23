# PATCH-044 Batch 4 Authorized File Manifest

## Authority and scope

Batch 4 — Regression and final evidence, S13–S15. Batches 1–3 are ACCEPTED /
COMPLETE. This manifest authorizes validation and the three documentation
surfaces below; it does not authorize production, test, migration or design
semantic changes.

## Exact file boundary

- CREATE `docs/reviews/PATCH-044-Implementation-Validation-Evidence.md` — S13
  reproducible commands/results and S14 consolidated evidence/history.
- CREATE
  `docs/reviews/FR-044-Project-Definition-Scope-Inputs-Lifecycle-Foundation.md`
  — S15 Independent Final Implementation Review and final-review readiness.
- MODIFY `docs/patches/PATCH-044.md` — S15 readiness/status and evidence links
  only; no accepted semantics.

Batch 4 review/acceptance, QG-11, QG-12 and closure records may subsequently be
created under their explicit standing governance steps, but are not
implementation-validation surfaces and may not alter technical evidence.

## S13 validation

- all focused Project Foundation backend and frontend tests;
- adjacent Project, Workspace, Evidence, Supporting File, authentication,
  Audit and migration regressions;
- full backend and frontend regression;
- sole Alembic head `e04400000001` and migration/role evidence;
- Python compile/import, TypeScript and production frontend build;
- authentication, tenant isolation, source revocation, protected outcome and
  no-manual-authority checks;
- accessibility/responsive structural evidence;
- exact cumulative scope, prohibited foreign persistence, deferred capability,
  secret and fake-production-data scans;
- `git diff --check` and QG-M1 traceability.

## S14–S15 evidence

Record exact environment, commands, pass counts, migration head, findings and
FAIL → remediation → focused re-review → PASS chains without rewriting initial
failures. Final review must independently compare repository state to accepted
PATCH/EDS/IDS/Plan/IRR and all manifests. It may mark only final-review/QG-11
readiness; delivery and closure remain pending.

## Stop conditions

Stop on any failed gate, migration divergence, unresolved Critical/Major,
unrepeatable evidence, secret/fake production record, scope contamination or
need to change production/test/design semantics. Reopen the owning accepted
batch rather than widening this manifest. Exclude PATCH-045+, completion
execution, generic workflow, tasks, milestones, deliverables, risks, change
management, AI decisions, source content copy and unrelated worktree changes.
