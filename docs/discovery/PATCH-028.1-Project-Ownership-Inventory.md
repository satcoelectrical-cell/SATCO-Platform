# PATCH-028.1 — Project Ownership Inventory Discovery

## 1. Discovery Control

| Field | Value |
|---|---|
| Related PATCH | PATCH-028.1 |
| Environment inspected | Current backend-configured database |
| Database identity | `satco_platform` |
| Inspection mode | Read-only SQL |
| Date | 2026-08-02 |
| Inventory status | OWNERSHIP DECISION COMPLETE — MIGRATION NOT EXECUTED |

No data, schema, migration state, or configuration was changed.

## 2. Repository Baseline

The repository's current Alembic script head is `e02600000001`, whose ancestry
includes PATCH-025 Organization context and PATCH-027 Evidence.

The backend-configured database is not at that baseline.

## 3. Environment Evidence

Read-only inspection returned:

```text
database: satco_platform
alembic revision: d8271b8f1a29
public tables:
  alembic_version
  audit_logs
  contacts
  customers
  project_code_sequences
  projects
  users
```

The environment has no:

- `organizations` table;
- `user_organization_memberships` table;
- Engineering Workspace tables;
- Engineering Object, Relationship, or Evidence tables;
- PATCH-025+ tenant baseline.

The legacy `projects` relation contains seven rows and only these columns:

```text
id
name
status
created_at
customer_id
```

It has no Project Code, owner, primary assignee, or Organization evidence from
which an ownership candidate could be reviewed.

## 4. Discovery Result

Discovery could not infer an Organization because the environment contains no
Organization identities or membership evidence. The Repository/Data Owner has
subsequently made an explicit decision: preserve all seven development Projects
and map them to one migration-owned default Organization.

```text
Projects discovered: 7
Projects covered by approved mapping rule: 7
Projects unresolved: 0
Inventory ownership decision: PASS
Migration execution: NOT PERFORMED
```

The default mapping is authorized by Human decision, not inferred from the
database. Deletion, reset, recreation, and identifier replacement are expressly
prohibited.

## 5. Environment Drift Finding

The configured development database is substantially behind repository
migration head. Upgrading it is not authorized by this discovery and could
transform existing data. The environment must not be used as PATCH-028.1
migration-readiness evidence until its upgrade/data plan is separately reviewed.

The guarded isolated test database remains appropriate for migration and
regression validation, but it cannot supply ownership decisions for the seven
legacy development Projects.

## 6. Recorded Human/Data Decision

On 2026-08-02, the Repository/Data Owner selected preservation and authorized a
safe default-Organization migration when required. EDS-028.1 defines that
mechanism. This decision authorizes design only; it does not authorize database
upgrade or migration execution.

## 7. Blocker Effect

- ADR-022 architecture may be accepted independently.
- EDS-028.1 may proceed to Human acceptance and detailed design.
- Runtime readiness remains blocked until an initial approved User membership
  for the default Organization is identified and designed.
- PATCH-028.1 migration remains NOT READY.
- PATCH-028 Sprint 2 remains BLOCKED.

## 8. Closure Evidence

Inventory closes only when:

- every target environment is named and inspected at an approved baseline;
- every Project has exactly one approved active Organization UUID or an
  explicitly governed non-migration disposition;
- approvals are attributable to the Repository/Data Owner;
- no conflict or missing mapping remains;
- EDS/IDS encode the selected non-inventive data mechanism.

## 9. Revision History

| Version | Date | Description |
|---|---|---|
| 1.0 | 2026-08-02 | Read-only discovery found seven unresolved legacy Projects and no Organization baseline. |
| 1.1 | 2026-08-02 | Recorded Human decision to preserve and map all seven Projects to a safe default Organization. |
