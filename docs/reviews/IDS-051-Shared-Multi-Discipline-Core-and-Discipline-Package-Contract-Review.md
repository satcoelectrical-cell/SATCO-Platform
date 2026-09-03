# IDS-051 Independent Implementation Design Review

## 1. Review control and verdict

| Field | Result |
|---|---|
| Review target | `docs/design/IDS-051-Shared-Multi-Discipline-Core-and-Discipline-Package-Contract.md` |
| Human authority | **HUMAN INDEPENDENT IDS-051 REVIEW AUTHORITY: GRANTED** |
| Review mode | Independent IDS review only |
| Verdict | **FAIL / STOPPED** |
| Critical / Major / Minor / Observation | **0 / 3 / 1 / 1** |
| IDS-051 acceptance eligibility | **NOT ELIGIBLE** |

IDS-051 is substantially conformant and repository-aware, but it is not yet
safe to hand to an Implementation Plan. Three material decisions remain open:
cross-release compatibility-profile persistence, exact guarded Session/UoW
composition for Workspace creation, and database-role separation for Registry
projection mutation. No accepted document was amended and no implementation,
test or migration work was performed.

## 2. Accepted-basis conformance

IDS-051 faithfully preserves the accepted ADR-024, Architecture-051 and
EDS-051 decisions for separate typed Discipline/Package identities, source
Registry authority and derived projection, exact PackageVersions, Project
selection authority, derived Workspace binding, three Workspace states,
profile-member cardinality, atomic Project/Workspace rebinding, shared/exclusive
Registry serialization, Organization-scoped configuration Audit, historical
preservation, entitlement intersection and Human authority.

No PATCH-052 operational package or PATCH-053 through PATCH-060 behavior is
pulled forward. The three Major findings below do not authorize redesign during
this review. `IDS051-MAJ-01` also exposes a contradiction already present in
the accepted EDS persistence shape; it therefore requires governed upstream
reconciliation before IDS can conformantly close it.

## 3. Repository-fit, component and dependency review

The proposed backend root-layer placement, synchronous SQLAlchemy approach,
thin FastAPI router, Pydantic DTOs, source-controlled adapter table, frontend
typed client/component allow-list and capability-specific tests fit the
repository. The design does not introduce a generic plugin framework or a
parallel owner for Project, Workspace, Context, Objects, Relationships,
Interface Commitments, Evidence, Reports, Memory or Guidance.

Component responsibilities and the declared dependency direction are coherent
apart from the transaction/role boundaries identified below. Leaf identity and
contract modules remain ORM-free; repositories do not own policy; services own
algorithms; routers own transport; Registry source does not depend on its DB
projection. No unavoidable Python import cycle was found.

The actual repository facts relevant to the findings are:

- `get_current_user_organization_context` performs SQL through the request
  `Session`; SQLAlchemy therefore autobegins before a mutation service runs.
- `EngineeringWorkspaceService.create` currently queries Project, duplicate
  Workspace, owner, assignee and collaborators before its insert.
- its `_audit_and_commit` calls `create_audit_log`, whose implementation calls
  `db.commit()` directly.
- Alembic already separates migration and runtime connection roles and several
  existing protected capabilities specify/test exact grants.

## 4. Persistence and profile-cardinality review

The eleven-table ownership map, Organization/Project/Workspace composite keys,
immutable revision model, Workspace fields and accepted corrected member PK
`(profile_id, profile_digest, combination_digest, package_key)` are otherwise
SQLAlchemy/PostgreSQL implementable. The member PK supports multiple
combinations and different versions of one PackageKey across combinations;
grouped canonical reconstruction, duplicate PackageKey rejection and digest
verification are adequately specified.

Composite FKs provide DB-level tenant integrity: Project revision/head and
Audit Project scope bind to `(project_id, organization_id)`; Audit Workspace
scope binds to `(workspace_id, project_id)` and requires Project; Workspace
binding resolves an exact Project revision selection. Existing globally unique
integer Project/Workspace PKs can support the proposed additional composite
unique keys.

The profile parent projection is not cross-release implementable as written.
`discipline_package_compatibility_profiles` has PK
`(profile_id, profile_digest)` while also storing exactly one
`registry_digest`. An unchanged authoritative profile has the same profile ID
and digest in two Registry releases, so the second release cannot insert its
release/profile association. Reusing the old row instead makes the new
release/profile triple absent, breaks complete release projection
reconciliation and prevents the Project revision FK
`(observed_registry_digest, profile_id, profile_digest)` from resolving. The
accepted member PK is not the problem; the missing release-to-profile
cardinality is.

## 5. Workspace fields and tenant constraints

The four fields have safe transition nullability and truthful final states.
Raw `discipline` remains intact; exact `control -> control_automation` mapping
is source-qualified and case-sensitive; E/I/C migration backfill does not
fabricate an operational binding; Mechanical/Civil/Process remain
future-unavailable; unknowns remain unresolved or stop the census. Workspace
cannot select a PackageVersion independently.

The deferred Workspace/current-Project-head trigger is conceptually compatible
with the accepted atomic rebind because both Workspace pointers and the head
can reach their final state before deferred checks run. The complementary head
trigger is necessary and correctly delayed until M3. Exact SQL and forced-
immediate tests remain Implementation-Plan/implementation evidence, not a new
design blocker.

## 6. Migration graph, M1, M2 and M3

`backend/.venv/bin/alembic -c alembic.ini heads`, executed from `backend/`,
reports the sole actual head **`e04700000001`**. The proposed chain
`e05100000001 -> e05100000002 -> e05100000003` is a linear continuation.

- **M1:** correctly defers Workspace backfill, creates the eleven accepted
  tables, supporting composite keys, immutable/history controls, tenant Audit
  and Registry projection foundations. It is blocked by `IDS051-MAJ-01` and
  `IDS051-MAJ-03`.
- **M2:** the four nullable shadows, indexes and `NOT VALID` FK/check strategy
  preserve old-reader/writer compatibility and do not cut over prematurely.
- **M3:** exact six-value backfill, count/checksum assertions, unknown failure,
  constraint validation, final state checks and deferred consistency triggers
  are coherent. Writer drain before M3 and delayed writer restoration avoid
  old-writer violations.

Downgrade guidance is appropriately conservative: only unused/empty structures
may be destructively removed; used history requires forward recovery.

## 7. Live census, cutover and historical anchoring

The read-only `REPEATABLE READ, READ ONLY, DEFERRABLE` census, canonical JSON,
digest, DB/head binding, exact counts, unknown-value failure and migration-side
revalidation are implementable. No deployment census is falsely claimed.

The A/B choreography is coherent at the design level: compatibility app A,
writer drain, M1, projection install, M2, census revalidation/M3, app B,
readiness verification and writer restoration. The repository already has a
global governed read-only write gate, so the declared recovery state does not
require a parallel mechanism. Projection installation remains possible while
application readiness is false, avoiding a startup/projection dependency loop.

Historical resolution correctly anchors stored RegistryDigest to retained
immutable projection and retained source, never silently substituting the
current release. That guarantee is blocked in the repeated-profile case until
`IDS051-MAJ-01` is resolved.

## 8. Registry assembly, projection and advisory lock

The assembly order—manifest, strict descriptor validation, static adapter
validation, canonicalization/digests, compatibility/resource validation,
immutable Registry, projection reconciliation—is deterministic and bounded.
Dynamic discovery, runtime downloads and descriptor-provided executable code
are prohibited.

Install/reconcile/activate keeps source authoritative, compares complete row
sets, retains history, atomically changes the current release and keeps global
lifecycle evidence outside tenant Audit. The projection write-role boundary is
not closed; see `IDS051-MAJ-03`.

The two-key PostgreSQL transaction advisory lock `(1396790339, 51)`, shared and
exclusive calls, `SET LOCAL lock_timeout`, rollback release, no upgrade and
full-transaction retry rules are individually implementable with synchronous
SQLAlchemy. The gap is composition with the actual request Session and
Workspace helper, not PostgreSQL lock semantics; see `IDS051-MAJ-02`.

## 9. Transaction matrix, Project configuration and Workspace operations

Registry activation takes no tenant locks. Organization replacement locks no
Project/Workspace rows. Project and Workspace paths share Registry,
Organization, Project, head and ascending Workspace order. No inherent
deadlock cycle was found.

Initial Project configuration and revision replacement correctly specify exact
selections, immutable revisions, Organization enablement, standing/profile
validation, optimistic concurrency, Project head advancement and same-
transaction scoped Audit. Atomic rebind enumerates and locks all operational
Workspaces, validates all before authority writes, advances every provenance
pointer and the Project head, and rolls the whole transaction back if one row
or Audit insert fails.

Workspace creation derives E/I/C binding only from the Project head, leaves
future Disciplines unbound, preserves unresolved legacy semantics and accepts
no PackageVersion. Its concrete transaction composition is not closed against
the current repository; see `IDS051-MAJ-02`.

## 10. Legacy, compatibility, authorization and Audit

One exact translator owns all repository-discovered identities; no fuzzy,
case-folded or global replacement is introduced. The compatibility evaluator
is pure, deterministic, bounded and uses the accepted ordered checks and
closed reason codes without I/O, AI or tenant authority.

Authorization composes the existing authenticated active Organization,
Project/Workspace visibility and owner/admin rules before package disclosure.
Configuration and entitlement intersect with rather than grant engineering-
data access. `NOT_REQUIRED` is a PATCH-051 adapter behind an injectable port,
so PATCH-059 can replace it without changing callers.

The new package Audit schema is tenant-leading, bounded, append-only and
transactional, with actor/scope/provenance and no engineering payload or global
Registry lifecycle event. The package Audit design itself is sound. The
existing generic Workspace Audit commit path must be reconciled for bound
Workspace creation under `IDS051-MAJ-02`.

## 11. API, frontend, readiness, errors and bounds

The ten accepted root-style endpoints have explicit service ownership,
authorization, DTOs, pagination/bounds, protected 404 behavior and safe
409/422/503 translation. No additional API design is required apart from the
blocking transaction closure.

The frontend can implement the typed client, Organization/Project panels,
effective state, selector and Control & Automation reconciliation using its
existing structure. It uses precompiled component keys and performs no dynamic
descriptor execution.

Startup-fatal source/schema/digest/adapter failures, readiness-only projection
failure, historical-only read behavior and governed recovery mode are
distinguished. Bounds have concrete validation locations at source DTO,
canonical bytes, graph assembly, persistence checks, service/API lists,
queries, adapters and performance tests. Errors do not need to disclose
internal or foreign identities.

## 12. Conformance, tests, observations and batches

The conformance harness is sufficient for PATCH-052 to prove schema, digest,
bounds, collision, prohibited behavior, authorization/resource declarations,
migration declarations and compatibility vectors without changing Core.

The proposed test map covers tenant isolation, all migrations/backfill,
advisory races, atomic rebind/Audit rollback, drift, history, API disclosure,
frontend states, bounds, readiness and recovery. Focused remediation must add
direct vectors for repeated unchanged profiles across releases, the actual
request-session/UoW boundary, generic Workspace Audit non-commit staging, and
exact Registry/runtime role grants.

`EDS051-OBS-01..04` map to actual preflight, retained source resolver,
cutover/readiness sequence and composite FKs. Their deployment evidence remains
explicitly incomplete and non-blocking.

Batch dependency order is generally sound. Batch 2 cannot be authorized until
profile persistence and projection-role authority are closed; Batch 3 cannot
be authorized until Workspace transaction composition is closed. The five
batch boundaries need no broader redesign after those focused amendments.

## 13. Finding register

### IDS051-MAJ-01 — Registry releases cannot reuse an unchanged compatibility profile

**Classification:** MAJOR — persistence integrity, Registry authority,
historical interpretation and implementability.

The profile table's global `(profile_id, profile_digest)` PK conflicts with its
single `registry_digest` ownership and the release-qualified Project revision
FK. A normal later release that retains an unchanged profile cannot be fully
projected or selected under that release. The IDS cannot fix this by silently
inventing per-release profile IDs, changing canonical digests, changing the
accepted PK, adding a twelfth table or weakening projection reconciliation.

**Minimum required remediation:** under explicit Human authority, reconcile
the accepted EDS persistence cardinality and then amend IDS persistence,
migrations, ORM relationships, projection/historical algorithms and tests with
one exact release-to-profile representation. Preserve the accepted
compatibility-member semantics and source Registry authority.

### IDS051-MAJ-02 — Guarded Workspace creation has no closed Session/UoW and Audit integration

**Classification:** MAJOR — transaction correctness, Registry serialization
and atomic Audit.

IDS simultaneously states one request Session, guard-first transaction
acquisition, fresh Session retries, existing Workspace authorization, and one
commit containing Workspace plus generic and package Audit. In the repository,
the active-Organization dependency and Workspace service already query through
the request Session, and the Workspace Audit helper commits directly. The IDS
does not define where the guarded transaction begins, which Session is retried,
how trusted actor/scope values cross into it, or how the generic Audit row is
staged without the helper committing. Implementers would have to invent the
linearization boundary and could acquire the guard late or split retry/Audit
ownership.

**Minimum required IDS remediation:** specify the exact dependency/UoW factory
and Session lifecycle for every guarded operation; ensure the guarded Session's
first DB action is the required timeout/lock sequence; re-read and lock scope in
the frozen order; stage both Audit rows without an internal commit; and make
the UoW's single commit the only linearization point. Name the exact existing
helper call replaced in Workspace creation and add retry/rollback tests.

### IDS051-MAJ-03 — Registry projection mutation role and grant boundary is unresolved

**Classification:** MAJOR — Registry authority, least privilege and migration
safety.

M1 promises least privilege but only says the runtime receives
“service-required INSERT/UPDATE.” The Registry service/UoW does not identify a
deployment-only connection/role or another DB-enforced path for projection
install/activation. The actual repository distinguishes migration and runtime
roles and tests exact table/column/function grants. Granting the normal runtime
role enough authority to insert immutable projection rows and switch current
would weaken the accepted release-only authority; denying it leaves the
specified Registry service unable to operate.

**Minimum required IDS remediation:** freeze the exact deployment/runtime role
used by Registry install/activation, its connection/UoW construction and the
per-table/per-column/function grant/revoke matrix. Configuration runtime must
retain only the exact SELECT/INSERT/UPDATE/DELETE privileges required by the
accepted algorithms. Add startup/readiness or deployment preflight ownership-
and-grant validation plus database-role tests consistent with repository
conventions.

### IDS051-MIN-01 — Workspace-selectable Discipline count is inconsistent

**Classification:** MINOR — non-blocking contract precision.

The accepted Core catalog contains seven Disciplines only because
`shared_engineering` is a reserved non-Workspace classification. IDS calls the
effective response “seven canonical states” while the actual Workspace
selector and exact legacy vocabulary contain six values. This does not require
a redesign, but response bounds, audit cardinality comments and tests should
consistently state six Workspace-selectable Disciplines and keep
`shared_engineering` outside Workspace creation.

### IDS051-OBS-01 — Deployment evidence remains future evidence

The live census, real query plans/performance, DB-role introspection, writer
drain and cutover attestations remain future per-deployment evidence. IDS
correctly does not mark them complete.

## 14. Blocking and non-blocking disposition

Blocking findings: `IDS051-MAJ-01`, `IDS051-MAJ-02`, `IDS051-MAJ-03`.

Non-blocking findings: `IDS051-MIN-01`, `IDS051-OBS-01`.

No Critical finding exists. Because Major count is nonzero, IDS-051 cannot be
accepted and no Implementation Plan may begin.

## 15. Required amendments and deferred matters

Required amendments are limited to the minimum finding remediations above.
`IDS051-MAJ-01` requires governed EDS persistence reconciliation before the IDS
can conformantly change. `IDS051-MAJ-02` and `IDS051-MAJ-03` are focused IDS
closure work. No broad Architecture/EDS/IDS redesign is requested.

Implementation-Plan-deferred matters remain exact file sequencing, test-run
commands, deployment artifact locations, execution timing and evidence capture.
The Plan may not choose the missing profile cardinality, Session transaction
boundary or DB authority model.

## 16. Validation and repository impact

Validation performed:

- read PATCH-051, accepted ADR-024, accepted Architecture-051, accepted
  EDS-051, initial/focused Architecture and EDS review evidence, and Human
  Architecture/EDS acceptance records;
- inspected actual Project, Workspace, Organization, authorization, Audit,
  SQLAlchemy Session, readiness/write-gate, router, frontend and test patterns;
- ran Alembic graph verification from `backend/` and confirmed sole head
  `e04700000001`;
- reviewed all eleven tables, four Workspace fields, three proposed revisions,
  ten endpoints, five batches and EDS observation mapping;
- performed no migration execution and no production/test validation run.

Files created: this review artifact only.

Files modified: none.

Production files: **0**. Test files: **0**. Migration files: **0**.

## 17. Exact governance state and next action

| Governance item | State after this review |
|---|---|
| PATCH-051 | REGISTERED / OPEN |
| ADR-024 | ACCEPTED |
| Architecture-051 | ACCEPTED / COMPLETE |
| Architecture Gate | PASS / ACCEPTED |
| EDS-051 | ACCEPTED / COMPLETE; persistence reconciliation required by review finding |
| EDS Gate | PASS / ACCEPTED; unchanged by this review |
| Human EDS Acceptance | PASS / GRANTED; unchanged |
| Independent IDS-051 Review | **FAIL / STOPPED** |
| IDS-051 | PROPOSED / NOT ACCEPTED |
| Implementation Plan | NOT STARTED |
| Implementation | NOT AUTHORIZED |
| Migrations | NOT AUTHORIZED / NOT CREATED |
| PATCH-052 | NOT STARTED |
| Commercial V1 roadmap | HUMAN-FROZEN / UNCHANGED |

Exact next resume point: obtain explicit Human authority for the minimum
governed EDS persistence reconciliation required by `IDS051-MAJ-01`, followed
by focused IDS-051 remediation for all three Major findings and a focused
Independent IDS-051 re-review.

Recommended Human decision: **do not accept IDS-051 and do not authorize an
Implementation Plan yet. Authorize only the minimum focused reconciliation and
remediation described above.**
