# PATCH-028 — Sprint 2 Project/Organization Scope Blocker

## 1. Blocker Control

| Field | Value |
|---|---|
| Related PATCH | PATCH-028 |
| Detected at | Sprint 2 preflight — Persistence and Atomicity |
| Blocker class | Architecture, security, dependency, and repository blocker |
| Severity | P0 for Sprint 2 and later implementation |
| Status | CLOSED — PATCH-028.1 DONE |
| Date | 2026-08-02 |

## 2. Blocking Condition

EDS-028 and IDS-028 require every Capture Project to belong to the authenticated
actor's active Organization. Current repository state cannot prove or enforce
that invariant:

- `backend/app/models/project.py` contains no `organization_id` or equivalent
  tenant ownership field;
- the `projects` table migration chain contains no Project-to-Organization
  foreign key;
- `EngineeringWorkspace` references Project but has no independent
  Organization ownership;
- existing Project authorization is based on User ownership/assignment, not an
  active Organization-scoped Project identity;
- PATCH-025 supplies active Organization membership for the actor but does not
  associate Projects with Organizations.

Adding both `organization_id` and `project_id` to a Capture table would store
two independently valid identifiers. It would not prove that they belong to
the same tenant. A validator could therefore accept or disclose a Capture with
cross-Organization Project context, especially when the same User has multiple
Organization memberships or owns a Project outside the selected context.

## 3. Evidence

Repository inspection confirmed:

- `Project` fields include customer, owner, primary assignee, status, priority,
  dates, progress, and timestamps, but no Organization identity;
- `EngineeringWorkspace` owns `project_id` and discipline, but no Organization
  identity;
- `EngineeringObject` has both Organization and Project fields, but that does
  not establish Organization ownership for a Project-wide Capture without an
  Engineering Object reference;
- current Alembic head is `e02600000001`; no historical revision provides the
  missing Project ownership relationship.

## 4. Violated Contracts if Work Continued

Continuing Sprint 2 would violate:

- EDS-028 Project requirement and cross-Organization prohibition;
- IDS-028 context validator and authorization contracts;
- PATCH-025 trusted active Organization boundary;
- deny-by-default authorization-before-disclosure;
- Engineering Context Is Sacred;
- Organizational Ownership;
- Security Before Disclosure;
- Framework No Invention and No Silent Expansion rules.

## 5. Rejected Workarounds

### Trust Project owner/assignee membership

Rejected. A User identity or assignment is not Project Organization ownership,
and one User may participate in more than one Organization.

### Infer Organization from Workspace or Engineering Object

Rejected. Project-wide Capture has no required Workspace/Object, and inference
would make optional context the tenant authority.

### Store independent Organization and Project IDs on Capture

Rejected. Separate foreign keys do not enforce compatible tenant ownership.

### Make Project optional or Organization-wide

Rejected. This reverses the accepted EDS and weakens context rather than closing
the missing ownership contract.

### Add Project organization_id inside PATCH-028

Rejected as unauthorized scope expansion. It changes Project Core, existing
data/migrations, authorization, APIs, and regressions outside IDS-028.

## 6. Required Bounded Prerequisite

A separately registered and approved prerequisite—recommended identifier
`PATCH-028.1 — Project Organization Ownership`—must define and implement:

1. immutable trusted Organization ownership for every Project;
2. migration/backfill policy for existing Projects with no invented tenant;
3. Project creation derivation from authenticated active Organization;
4. Organization-scoped Project repository/service/API authorization;
5. Workspace and dependent-domain compatibility;
6. cross-Organization protected-not-found behavior;
7. migration rollback/forward-repair and complete regression evidence;
8. impact on EngineeringObject, Evidence, Relationship, Context, Search, and
   existing Project consumers;
9. QG-M1 alignment and its own PATCH/AR/EDS/IDS/plan/IRR chain.

The prerequisite identifier is a recommendation only until accepted in the
authoritative PATCH registry.

## 7. Effect on Current Work

- Sprint 1 Domain and Contracts remains PASS; it contains no persistence or
  tenant lookup implementation.
- Sprint 2 is BLOCKED before any repository, Unit of Work, migration, security,
  transaction, or performance file was created.
- Sprint 3 remains blocked by Sprint 2.
- IRR-028 READY assumptions are invalidated by repository reality and must be
  re-reviewed after the prerequisite is DONE.
- no unsafe partial persistence implementation exists.

## 8. Closure Evidence

This blocker closes only when:

- the prerequisite is registered and reaches DONE;
- Project Organization ownership is present in model, schema, migration, and
  authorization behavior;
- existing Project data has an approved, evidence-backed ownership resolution;
- PATCH-028 EDS/IDS assumptions are revalidated against the new baseline;
- Alembic head and exact dependency are updated in IDS/IRR;
- focused IRR-028 re-review restores QG-M1 Readiness PASS and
  `READY FOR IMPLEMENTATION`.

## 9. Current Decision

```text
Sprint 1: PASS
PATCH-028.1 implementation Sprints 1-3: PASS
PATCH-028.1 full backend regression: PASS — 381 passed, 0 failed
PATCH-028.1 Human QG-11 review: PASS — after focused IDS Amendment 2 independent review
PATCH-028.1 development/deployment migration: NOT AUTHORIZED / NOT EXECUTED
Manifesto Alignment Verified for PATCH-028.1 implementation: YES
PATCH-028.1 commit/push/remote verification/QG-12: PASS — f58b2ebcf0df4f143729c76e6d43349dc298b6c4
Project Organization ownership blocker: CLOSED
PATCH-028 Sprint 2: NOT READY for separate migration-lineage amendment identified by focused IRR-028
PATCH-028: BLOCKED
```

## 10. Revision History

| Version | Date | Description |
|---|---|---|
| 1.0 | 2026-08-02 | Recorded missing Project Organization ownership at Sprint 2 preflight. |
| 1.1 | 2026-08-02 | Reconciled validated PATCH-028.1 implementation evidence; retained PATCH-028 block pending prerequisite final review and focused readiness restoration. |
| 2.0 | 2026-08-03 | Closed the Project Organization ownership blocker after PATCH-028.1 QG-12 PASS and DONE/CLOSED; recorded the separate PATCH-028 migration-lineage readiness finding. |
