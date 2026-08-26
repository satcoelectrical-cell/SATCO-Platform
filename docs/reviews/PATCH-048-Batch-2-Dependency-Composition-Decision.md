# PATCH-048 Batch 2 — Dependency Composition Decision

## Decision

**Option A — LOCAL DEPENDENCY-ROOT COMPOSITION AUTHORIZED.**

`B2-MAJ-03` is **RESOLVED**. Independent focused review: **PASS**. Critical:
0. Major: 0. Minor: 0.

## Repository evidence

- `dependencies/engineering_knowledge_graph.py` constructs the canonical
  `EngineeringObjectService` from its accepted UoW, authorization policy,
  reference validator and clock, then gives only that service to its adapter.
- `dependencies/organizational_memory.py` independently constructs canonical
  `EngineeringObjectService`, `EvidenceService` and `TechnicalReportService`
  instances from their established infrastructure collaborators.
- `EngineeringObjectService.list` authorizes the Project before querying and
  authorizes each returned object before projection.
- `EvidenceService.list` authorizes the Project/Workspace request and each
  visible Evidence result.
- `TechnicalReportService.list_reports` delegates scope authorization to the
  canonical Technical Report UoW authorization policy before its scoped read.

Thus local construction in `dependencies/project_context.py` is established
infrastructure composition, not Project Context foreign persistence access.
No new owner authority, business logic, repository, policy or canonical
implementation is introduced.

## Focused review

Canonical public services remain the sole owner boundaries. Infrastructure is
confined to the dependency root; adapters, composer and router may receive only
canonical service instances/public calls. Tenant/Project/Workspace checks
remain fail-closed in the canonical services. The reconciled ten-file boundary
already authorizes this dependency root, so no manifest expansion or IDS/Plan
amendment is required. No generic locator, Batch 3 EKG behavior, persistence,
migration or PATCH-049 behavior is authorized.

The current callback placeholders and unavailable-default dependency are
temporary, unaccepted scaffolding and must be replaced during resumed Batch 2
implementation.
