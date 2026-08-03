# Implementation Plan 028.1 — Project Organization Ownership

## 1. Document Control

| Field | Value |
|---|---|
| Related PATCH | PATCH-028.1 |
| Related IDS | IDS-028.1 v1.0 Accepted |
| Version | 0.1 |
| Status | ACCEPTED — EXECUTABLE IN ISOLATED ENVIRONMENT |
| Date | 2026-08-02 |

The plan authorizes no database execution. Development migration requires a
separate explicit go/no-go after implementation and isolated validation.

### Approval Record

| Authority | Decision | Date |
|---|---|---|
| Product Owner / Human Authority | Accepted | 2026-08-02 |

## 2. Verified Baseline

```text
Branch: patch-022.3a-development-infrastructure
Commit: 86c034664f9db35d9817814964af42648365c36c
Repository Alembic head: e02600000001 (single head)
Development database: satco_platform
Development revision: d8271b8f1a29
Development Projects: 7
Development Users: 2
Approved bootstrap user: admin@satco.com (admin)
Protected user: engineer@satco.com (engineer)
```

The worktree also contains authorized, unfinished PATCH-028 Sprint 1 files.
They must be preserved and excluded from PATCH-028.1 scope accounting. No
commit, push, reset, or cleanup is authorized by this plan.

## 3. Global Boundaries

- only files listed in IDS-028.1 Section 3 may change;
- no Capture persistence file may be created or modified;
- no User may be created or mutated;
- engineer User and memberships remain unchanged;
- Project rows, IDs, values, and foreign references remain unchanged except the
  new `organization_id` value;
- no migration runs against `satco_platform` during implementation;
- destructive reset, cleanup, table recreation, or data deletion is forbidden.

## 4. Sprint 1 — Migration Source and Preservation Harness

### Objective

Implement the additive revision and isolated migration tests without executing
it against the development database.

### Files

- create `backend/migrations/versions/e02810000001_project_organization_ownership.py`;
- create `backend/tests/test_patch_028_1_migration.py`;
- modify `backend/app/models/project.py`;
- modify only migration/model test files expressly listed by IDS as required.

### Order

1. reconfirm sole head `e02600000001`;
2. add the Project Organization model field;
3. implement transactional expand/bootstrap/backfill/validate/constrain logic;
4. implement conditional lookup of `admin@satco.com` only when legacy rows
   require backfill;
5. snapshot and verify engineer/User/Project preservation;
6. implement non-destructive downgrade;
7. run static migration checks and isolated fixture tests only.

### Exit

- seven-row fixture preserved exactly except new ownership;
- approved admin membership enabled and selected;
- engineer and User count unchanged;
- clean no-user/no-Project chain succeeds;
- failures roll back fully;
- migration never executed against `satco_platform`;
- QG-M1 checkpoint PASS.

## 5. Sprint 2 — Project and Search Tenant Boundary

### Objective

Make Project creation, CRUD, listing, counts, and Search derive and enforce the
authenticated Organization context.

### Files

Use only the Project/Search runtime and test files listed in IDS-028.1.

### Order

1. require Organization UUID in Project repository base queries;
2. derive Organization on create and prohibit transport ownership input;
3. scope get/list/update/delete/history checks before business authorization;
4. move Project and Search routes to PATCH-025 Organization context;
5. filter Project and Workspace Search before count and pagination;
6. preserve response compatibility and existing role rules;
7. run Project, Search, auth-context, and migration regressions.

### Exit

- no protected global Project lookup remains in these paths;
- cross-Organization IDs return protected not found;
- foreign Projects do not affect totals or pagination;
- same-Organization legacy behavior passes;
- QG-M1 checkpoint PASS.

## 6. Sprint 3 — Dependent Loader Closure

### Objective

Close Organization equality across Workspace, Context, Object, Relationship,
and Evidence Project loaders.

### Files

Use only the dependent runtime and exact test files listed in IDS-028.1.

### Order

1. inventory every remaining Project loader with a static search;
2. pass trusted Organization UUID through authorized application boundaries;
3. replace global Project loads with `(organization_id, project_id)` queries;
4. require equality where child rows store Organization UUID;
5. test protected-not-found and non-disclosure in each domain;
6. repeat static search and complete regression.

### Exit

- zero protected unscoped Project loaders remain;
- dependent domains reject cross-Organization references;
- all focused and complete backend tests pass;
- exact diff stays within IDS;
- QG-M1 final comparison PASS.

## 7. Validation Ladder

1. source compilation and imports;
2. one-head and revision-parent checks;
3. migration SQL/static contract checks;
4. isolated seven-Project migration tests;
5. clean-chain and mixed-state tests;
6. migration downgrade/re-upgrade without destructive row removal;
7. Project and Search focused suites;
8. dependent-domain focused suites;
9. authentication/Organization-context regressions;
10. complete backend suite;
11. prohibited global-loader and unauthorized-file searches;
12. `git diff --check` and Manifesto/QG-M1 review.

Migration tests must use an isolated database whose identity guard excludes
`satco_platform`. Test fixtures may reproduce the seven-row shape but must not
copy secrets or alter the development database.

## 8. Development Deployment Gate

After code implementation is complete, stop. Before running Alembic against
`satco_platform`, require all of:

- implementation evidence PASS and final review;
- a current backup and demonstrated restore procedure;
- read-only preflight showing revision, 7 Projects, both expected Users, and
  exact bootstrap admin state;
- dry-run or isolated clone evidence using the same preflight shape;
- explicit Human command approving migration of database `satco_platform`;
- post-migration read-only proof of 7 preserved Projects, 2 preserved Users,
  unchanged engineer, and selected admin membership.

Without this separate approval, the terminal state is implementation complete
with development migration pending.

## 9. Rollback

Source rollback removes only PATCH-028.1 changes and preserves unrelated
PATCH-028 Sprint 1 work. Isolated database downgrade follows IDS and retains
Projects, Users, Organization, and memberships. Development rollback uses the
approved backup/forward-repair procedure; destructive cleanup is prohibited.

## 10. Checkpoint Report

Each Sprint reports exact files, tests/pass counts, warnings, database identity
and revision, preservation evidence, QG-M1 result, and stop/continue decision.

## 11. Readiness

```text
Plan technical completeness: PASS
Human Plan acceptance: ACCEPTED — 2026-08-02
IRR-028.1: READY FOR IMPLEMENTATION
Implementation: AUTHORIZED WITHIN IDS FILE SCOPE
Development migration: NOT AUTHORIZED
```

## 12. Revision History

| Version | Date | Description |
|---|---|---|
| 0.1 | 2026-08-02 | Proposed three-Sprint implementation and separate development-deployment gate. |
| 1.0 | 2026-08-02 | Accepted for scoped implementation and isolated validation; development migration remains unauthorized. |
