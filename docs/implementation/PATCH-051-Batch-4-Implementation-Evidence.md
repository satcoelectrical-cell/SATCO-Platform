# PATCH-051 Batch-4 Implementation Evidence

## Historical record

Initial Batch-4 implementation was materially complete enough for focused
validation, but the first independent review was **NOT ACCEPTED**. It recorded
three implementation-level Major findings: (1) the Workspace selector retained
a legacy static discipline authority, (2) readiness did not prove source
Registry-to-current-projection parity, and (3) tests did not materially cover
the accepted ten-route behavior/security surface. This record preserves that
initial result; it is not retrospectively represented as a pass.

## Remediation scope

This focused cycle remains within accepted Batch-4 ownership: API,
authorization, readiness/startup, Project/Workspace applicability reads and
the separately reconciled frontend integration. It adds no migration, no
Registry installer/activation behavior, no executable package content, and no
PATCH-052 capability.

## Major 1 — effective Workspace selection

`ProjectWorkspacePage` no longer contains an operational discipline option
list. It requests `GET /projects/{id}/effective-discipline-packages`, renders
all returned states, and enables `create_workspace` only when the server’s
`allowed_actions` explicitly contains that action. `FUTURE_UNAVAILABLE` and
`LEGACY_UNRESOLVED` remain represented as disabled options; absent server
items are never fabricated. The exact legacy `control` serialization remains a
non-authoritative compatibility translation for the existing Workspace create
DTO; availability itself remains server-derived. The component allow-list stays
source-controlled and returns `null` for every unknown key.

Focused frontend evidence: `frontend/src/test/workflows.test.tsx` proves
server-derived operational rendering, unavailable/legacy representation,
absence of stale literal Mechanical, and exact control serialization;
`frontend/src/test/discipline-packages.test.tsx` proves unknown component keys
fail closed.

## Major 2 — source/projection readiness parity

`validate_source_projection_parity()` performs no DML. It verifies exactly one
current release, source digest/release identity/core version/manifest equality,
current descriptor and membership sets/digests/JSON/standing, profile
membership and JSON, and exact combination-member provenance. Historical rows
outside the current release are not rejected. `core.operations._database_ready`
calls it only when Registry persistence is enabled, after the runtime-role
read-only boundary check. Any mismatch returns readiness false through the
existing non-disclosing readiness path.

Focused real PostgreSQL vectors in
`backend/tests/test_discipline_package_readiness.py` prove: valid core source
projection passes; immutable installed manifest drift fails closed; a missing
or wrong current pointer fails closed; and verifier invocation does not repair
or mutate Registry rows.

## Major 3 — ten-route coverage matrix

| API | Method/path | Authority/scope | Cursor | Guarded UoW | Compatibility | Evidence |
|---|---|---|---|---|---|---|
| supported packages | GET `/discipline-packages/supported` | active Organization member; no config disclosure | keyset, signed scope/tenant/release/limit | N/A | current membership only | API route vector; malformed-cursor vector |
| Organization configuration | GET `/organizations/current/discipline-package-configuration` | active admin, current Organization | N/A | N/A | current Registry provenance | API route vector; engineer denial |
| Organization replace | PUT same | active admin, server-derived Organization | N/A | yes | exact server-resolved descriptors | API route vector; injected identity rejection |
| Organization audit | GET `/organizations/current/discipline-package-configuration/audit` | active admin, Organization-only | signed scope/tenant/category/limit | N/A | N/A | API route vector |
| Project configuration | GET `/projects/{id}/discipline-package-configuration` | authorized reader, protected Project | N/A | N/A | immutable selection provenance | API route vector; protected foreign/non-owner reads |
| Project replace | PUT same | active admin or Project owner | N/A | yes | exact profile/selection evaluation | API route vector; strict DTO test |
| Project remove | DELETE same | active admin or Project owner | N/A | yes | rejects bound Workspace in service | API route vector |
| Project preflight | POST `/projects/{id}/discipline-package-configuration/preflight` | active admin or Project owner | N/A | N/A | deterministic persisted exact evaluator | API route vector |
| effective packages | GET `/projects/{id}/effective-discipline-packages` | authorized Project reader | N/A | N/A | derives configured/not-configured state only | API route vector; frontend effective-state test |
| Workspace applicability | GET `/workspaces/{id}/package-applicability` | authorized Workspace reader, established visibility predicate | N/A | N/A | exact revision-selection descriptor lookup | API route vector |

`backend/tests/test_discipline_package_api.py` uses real FastAPI routing,
authenticated contexts, real PostgreSQL projection rows and a savepoint-bound
fresh guarded service UoW. It covers all ten success paths, request DTO
provenance/tenant injection rejection, malformed cursors, cursor continuation,
admin/engineer restrictions, disabled User/membership behavior, cross-tenant
and non-owner protected 404 semantics, and authorization before disclosure.

## Migration and deployment boundaries

No migration was created or modified by this Batch-4 remediation. Source head
remains `e05100000003`; no M4 exists. Tests use only the isolated
`satco_platform_patch02022_test` database. No production/customer database was
mutated. Deployment qualification, runtime installation/activation and live
preflight evidence remain deferred under the accepted PATCH-060/EDS
observations.

## Validation record — focused remediation completion

- Frontend focused and full suite: **91 passed**; TypeScript typecheck: PASS;
  production build: PASS.
- Focused real PostgreSQL API/security/readiness vector: **8 passed**.
- Final focused API/readiness plus affected Batch-1–3 Workspace regressions:
  **67 passed**.
- Broader Registry/compatibility/service/migration/conformance/Workspace
  package regression set: **93 passed**.
- Python compile/import for the remediated API, dependency, Registry and
  operations modules: PASS.
- Alembic graph: sole source head `e05100000003`; precisely M1/M2/M3 found;
  no M4. `git diff --check`: PASS; staged files: 0.

The Docker test image mounts application code at `/app`; root-relative source
inspection tests that assume `/backend` or `/ops` cannot execute in that image.
Their relevant source paths were checked directly in the repository. This is a
test-container layout observation, not a product implementation failure.
