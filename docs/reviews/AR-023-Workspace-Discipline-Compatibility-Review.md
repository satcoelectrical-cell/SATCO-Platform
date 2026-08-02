# AR-023 — Workspace-Discipline Compatibility Focused Review

## Status

PASS

## Scope

This focused review covers only EngineeringObject-to-Workspace discipline
compatibility required by PATCH-023 ReferenceValidator.

## Sources Reviewed

- EngineeringObject Blueprint v1.0;
- PATCH-023 and PATCH-023.1;
- EDS-023 and IDS-023;
- current `EngineeringDiscipline` enum;
- current Workspace `Discipline` enum and validation;
- ADR-014 Engineering Workspace Domain Model;
- EDS-020.1 Engineering Workspace Core;
- applicable Engineering Context governance.

## Findings

### Industrial Automation

The existing Workspace vocabulary uses `control` for the operational Workspace
that corresponds to the EKG classification `industrial_automation`. Recording
this explicit compatibility changes neither enum and preserves the Workspace's
single-discipline invariant.

### Shared Engineering

The Blueprint permits shared EngineeringObjects but requires one coherent,
mandatory Workspace scope. The current persistence model stores one
`workspace_id`; the Workspace model provides one discipline per Workspace and
no shared discipline. Membership in multiple Workspaces is authorization for
each independent Workspace, not a representable shared scope.

Implicit selection of one discipline Workspace or union of memberships would
weaken scope validation and create unauthorized cross-discipline access.
Creation and reclassification to `shared_engineering` must therefore remain
deferred until a dedicated shared-workspace capability is approved.

## Approved Compatibility Matrix

| EngineeringObject discipline | Workspace discipline | Decision |
|---|---|---|
| `instrumentation` | `instrumentation` | Compatible |
| `electrical` | `electrical` | Compatible |
| `industrial_automation` | `control` | Compatible |
| `shared_engineering` | None | Creation and reclassification deferred |

## ReferenceValidator Decision

ReferenceValidator can implement the closed matrix without guessing. It shall
resolve exactly one authorized Workspace for the first three rows and reject
the fourth. It shall never create a Workspace, infer shared scope, combine
memberships, or broaden access.

## Verdict

**PASS — WORKSPACE-DISCIPLINE COMPATIBILITY BLOCKER CLOSED**

Decision date: 2026-08-01.
