# PATCH-020.1 Future Recommendations

## Purpose

These recommendations record possible later work discovered during
PATCH-020.1. They do not authorize implementation and are not part of the
current scope.

## Governance Rule

Future work must follow ADR-014, PATCH-020 decomposition, the Product Bible,
Experience Bible, and applicable approval gates.

## Recommended Follow-Up

### Proceed in Approved Dependency Order

The next domain work should remain PATCH-020.2: Engineering Context,
Engineering Decision Log, and Human Review foundation. Engineering Execution
Plan, Engineering Health, AI Insights, and ENSE should not bypass that
dependency.

### Preserve the Current Discipline Boundary

Do not add Discipline administration, customer-specific Disciplines, or
multiple Workspaces per Project and Discipline without separately approved
architecture and migration planning.

### Revisit Roles Only With Proven Capability Needs

Future Engineering Manager, Project Manager, Lead Engineer, Reviewer, and
Viewer personas should be introduced through explicit RBAC governance, not by
overloading collaborator membership.

### Keep Archived Search Explicit

If archived Workspace discovery becomes necessary, add an explicit governed
filter and preserve authorization. Do not silently include archived history in
normal search.

### Address Existing Deprecation Warnings Separately

Future maintenance may address:

- Starlette/HTTPX `TestClient` compatibility;
- legacy Pydantic class configuration;
- timezone-aware replacements for `datetime.utcnow()`.

These are existing cross-cutting maintenance concerns and should not expand
PATCH-020.1.

The final PATCH-020.1 regression reports only these known warning families; no
new functional warning or unresolved validation issue was introduced.

### Add Automated Migration Identifier Validation

A future infrastructure improvement may check PostgreSQL identifier lengths
and Alembic naming conventions before migration execution.

### Validate Development Upgrade Separately

The development database remains at `d8271b8f1a29`, with the final validation
fingerprint unchanged and both Workspace tables absent. Before any approved
development upgrade, perform backup, preflight, and explicit review because
the upgrade would apply both `f18a1c0e2026` and `a20c1e0201f0`.

## Excluded Recommendations

No recommendation here authorizes:

- automatic Workspace creation;
- expanded role persistence;
- nested Workspaces;
- AI behavior;
- frontend behavior;
- physical history deletion;
- migration execution against development.
