# IDS-051 Focused Independent Implementation Design Re-review

## 1. Review control and verdict

| Field | Result |
|---|---|
| PATCH | PATCH-051 — Shared Multi-Discipline Core & Discipline Package Contract |
| Authority | **HUMAN FOCUSED INDEPENDENT IDS-051 RE-REVIEW AUTHORITY: GRANTED** |
| Scope | `IDS051-MAJ-01`, `IDS051-MAJ-02`, `IDS051-MAJ-03`, `IDS051-MIN-01` and direct consistency only |
| Verdict | **FAIL / STOPPED** |
| New Critical / Major / Minor / Observation | **0 / 1 / 0 / 0** |
| IDS-051 Human acceptance eligibility | **NOT ELIGIBLE** |

The persistence, database-authority and Workspace-count remediations pass.
The guarded UoW owns one Session/transaction and correctly excludes committing
Audit helpers, but mutable authorization is only reread and is not held stable
through commit. A concurrent account, membership or role revocation can commit
after the guarded reread and before the package mutation commits. The required
concurrent-revocation tests are also absent. `IDS051-MAJ-02` therefore remains
open and blocks IDS acceptance.

This re-review changes no IDS, EDS, Architecture, ADR, production, test or
migration file.

## 2. IDS051-MAJ-01 — resolved / closed

The remediated model exactly consumes the accepted EDS persistence
reconciliation:

- semantic profile PK `(profile_id, profile_digest)`;
- immutable Registry-release/profile membership PK
  `(registry_digest, profile_id)` carrying `profile_digest`;
- unique/FK target `(registry_digest, profile_id, profile_digest)`;
- unchanged semantic member PK
  `(profile_id, profile_digest, combination_digest, package_key)`; and
- Project revision FK `(observed_registry_digest, profile_id, profile_digest)`
  to the exact release membership.

R1/P/D and R2/P/D reuse one immutable semantic row/member set and insert two
membership rows. R2 never overwrites R1. ProfileDigest remains semantic-content
derived; RegistryDigest remains release-derived. Historical resolution follows
stored release digest to retained source/release, exact membership, semantic
profile and members without consulting the current pointer. Drift comparison
checks both exact per-release memberships and referenced semantic content.

The ORM keys and composite FK are implementable in SQLAlchemy/PostgreSQL. M1
consistently creates twelve tables: six Registry projection tables and six
tenant configuration/Audit tables. No implementation-critical eleven-table
statement remains in IDS-051.

## 3. Direct M1 and migration consistency

M1 includes release, descriptor and package membership; semantic profile;
release/profile membership; semantic members; six tenant tables; exact keys,
reverse membership index, immutable triggers and Project triple-FK. Historical
memberships/content cannot be updated or deleted. M2 retains only nullable
Workspace shadows and is unaffected. M3 retains exact backfill/cutover and
deferred binding consistency and is unaffected.

M1 also defines deterministic role prerequisites and grants. The migration
principal retains ownership; `PUBLIC` is revoked; runtime receives projection
SELECT only; installer receives projection SELECT/INSERT and column-level
release-current UPDATE only. This is coherent with the reconciled table shape.

## 4. IDS051-MAJ-02 — not resolved

### 4.1 Passing transaction ownership surfaces

The separate Session design is compatible with the actual synchronous
SQLAlchemy repository:

- the request Session authenticates and derives initial Organization context;
- each guarded attempt creates a fresh `SessionLocal` Session/UoW;
- the explicit transaction, advisory guard, repositories, row locks, writes
  and Audit staging share that Session/connection;
- only the UoW commits or rolls back;
- repositories and staging helpers may add/flush/raise but not complete the
  transaction;
- failed transactions are closed and a new UoW/Session is created for each
  retry; and
- exhausted retries map safely without partial mutation.

The proposed `stage_audit_log()` is a valid minimum adaptation of the actual
Audit service: the current `create_audit_log()` calls `db.commit()` and is
correctly prohibited inside guarded UoWs, while the new staging function adds
and optionally flushes without begin/commit/rollback. Package Audit and generic
Workspace Audit can therefore share the guarded transaction.

Workspace creation and Project rebind correctly place Registry validation,
configuration, binding/revision/head writes and both Audit kinds before one
outer commit. One helper/flush/Audit/commit failure rolls the full attempt
back. Advisory transaction-lock affinity and lifetime are explicit.

### 4.2 Blocking request-to-guarded authorization race

The actual mutable authorization facts live in `users`,
`user_organization_memberships`, `organizations` and Project/Workspace rows:

- `User.is_active`, `User.role` and `User.auth_version` can change;
- membership `is_enabled`, `is_selected` and `version` can change;
- `Organization.is_active` can change; and
- Project/Workspace ownership and other source-owner policy state can change.

IDS section 11.1 freezes actor ID, Organization ID **and role claim** from the
request Session. It says guarded attempts “revalidate” actor/scope, and the
algorithms/matrix contain `actor/org revalidation`, but they do not lock or
version-check the User, membership or Organization authorization rows through
commit. Project is locked later, which stabilizes its owner, but the preceding
account/membership/role predicates remain point-in-time reads.

Under PostgreSQL READ COMMITTED, the following execution remains possible:

1. request Session authenticates an active admin with enabled selected
   membership;
2. guarded Session rereads those values without a retaining row lock;
3. a concurrent administrator disables membership, deactivates the account,
   increments `auth_version` or downgrades the role and commits; and
4. the guarded Session continues using its earlier result/frozen role claim and
   commits the package mutation.

This violates the required authorization-before-disclosure/commit invariant.
Rereading inside the transaction is necessary but insufficient when the
authorization fact can change again before the linearization point. Freezing a
role claim also blurs stable identity with mutable authority.

### 4.3 Test-map insufficiency

The test map covers authorization order, cross-tenant negatives, guard
connection affinity, inner-commit prohibition, Audit rollback and fresh retry
Sessions. It does not require concurrent account deactivation, membership
disable/deselect, role downgrade/auth-version invalidation or stale request-
context tests. It therefore cannot detect the race above.

### 4.4 Minimum required IDS remediation

Amend only the MAJ-02 authorization boundary:

1. freeze only stable request identity/correlation facts; a request-time role
   may be diagnostic but must not authorize the guarded mutation;
2. after acquiring the advisory guard, use the guarded Session to select the
   exact User, selected membership and Organization authorization rows with
   retaining `FOR SHARE` locks in one deterministic order; revalidate account
   active/auth-version, role, membership enabled/selected/version and
   Organization active from those locked rows;
3. retain existing `FOR UPDATE` Project/head and ordered Workspace locks so
   owner/scope facts remain stable; lock or version-check any additional
   mutable source-owner authority used by a guarded operation;
4. add these authorization locks to every affected transaction/lock-matrix row
   and ensure authority-changing flows acquire compatible row locks; and
5. add concurrent revocation tests proving either revocation commits first and
   the mutation is denied, or the guarded mutation locks/linearizes first and
   revocation waits—never a mutation authorized by already-revoked state.

This is a focused IDS correction. It requires no Architecture, ADR or EDS
change and does not alter the accepted advisory identity or UoW ownership.

## 5. IDS051-MAJ-03 — resolved / closed

The authority matrix cleanly distinguishes:

- source-controlled Registry content authority;
- existing Alembic migration/schema owner;
- externally provisioned deployment-only `satco_registry_installer`; and
- ordinary `satco_runtime`.

Runtime has exact SELECT-only privileges on releases, descriptors, package
memberships, semantic profiles, release/profile memberships and profile
members. INSERT/UPDATE/DELETE are absent. Installer has SELECT/INSERT on those
six tables and PostgreSQL column-level `UPDATE (is_current)` on releases only;
it has no broad table UPDATE, DELETE or tenant-table authority. The immutable
triggers prevent historical mutation, and activation changes only current
flags under the exclusive advisory guard in one installer UoW.

External deployment provisioning creates the fixed login role and secret; M1
requires both fixed roles to exist and fails before schema/grant completion if
they do not. M1 owns reproducible REVOKE/GRANT and object ownership. Runtime and
installer are distinct, receive no role membership/inheritance, schema CREATE,
ownership or broad PostgreSQL flags, and the FastAPI process never receives the
installer credential. The migration-owner credential is not used for normal
Registry installation.

Runtime can acquire shared advisory locks, read the projection and mutate only
the accepted tenant configuration/Audit tables. Readiness/runtime-boundary
validation and installer preflight cover owner/role/grant assumptions;
database-role tests cover runtime SELECT success, projection INSERT/UPDATE/
DELETE denial, installer controlled insertion/activation, absence of historical
UPDATE/DELETE authority and runtime configuration compatibility.

## 6. IDS051-MIN-01 — resolved / closed

IDS consistently uses six Workspace-selectable Disciplines: Electrical,
Instrumentation, Control & Automation, Mechanical, Civil and Process. The raw
legacy values and frontend outbound values remain the existing six-value set.
Reserved Core classification `shared_engineering` is explicitly excluded from
Workspace selection, effective response cardinality and Workspace Audit/rebind
cardinality. No backend/API/frontend/test inconsistency remains in the scoped
design.

## 7. IDS051-OBS-01

`IDS051-OBS-01` remains **OPEN / NON-BLOCKING**. Live census, representative
query plans/performance, deployed role introspection, writer-drain and cutover
attestations remain future environment-specific evidence. The remediation did
not make this obligation false and did not fabricate evidence.

## 8. Matrices, manifests and batches

The transaction matrix consistently identifies principal, outer UoW, guard,
row-lock sequence, staging policy, retry owner and one commit/linearization
point for projection install/activation, Organization configuration, Project
initial/update configuration and Workspace creation. Its authorization rows
remain incomplete only as stated in `IDS051-FRR-MAJ-01` below.

The source/migration/installer/runtime authority matrix is coherent. Production
manifest covers normalized models, UoW, advisory helper, non-committing Audit
staging, Registry installer CLI and runtime/readiness validation. Test manifest
covers MAJ-01 and MAJ-03 and most MAJ-02 transaction surfaces, but lacks the
concurrent authorization-revocation vectors.

Batch 2 correctly establishes twelve-table persistence, release memberships,
M1/M2, installer/runtime grants, UoW/guard and readiness foundations before
Batch 3 configuration/Audit/Workspace/M3 work. Batch 3 must not proceed until
the focused authorization-lock remediation is accepted and its test vectors
are included; no batch redesign is otherwise required.

## 9. Finding register and disposition

### IDS051-FRR-MAJ-01 — mutable authorization is not held stable through guarded commit

**Classification:** MAJOR — authorization-before-disclosure, transaction
atomicity and implementation-plan readiness.

This is the unresolved direct remainder of `IDS051-MAJ-02`. Guarded
revalidation does not lock/version mutable User/membership/Organization
authority through commit, freezes a mutable role claim, and omits concurrent
revocation tests. Minimum remediation is limited to section 4.4.

| Historical/scoped finding | Focused re-review disposition |
|---|---|
| `IDS051-MAJ-01` | **RESOLVED / CLOSED** |
| `IDS051-MAJ-02` | **NOT RESOLVED / OPEN / BLOCKING** |
| `IDS051-MAJ-03` | **RESOLVED / CLOSED** |
| `IDS051-MIN-01` | **RESOLVED / CLOSED** |
| `IDS051-OBS-01` | **OPEN / NON-BLOCKING** |
| `IDS051-FRR-MAJ-01` | **OPEN / BLOCKING** |

Blocking findings: `IDS051-MAJ-02` / `IDS051-FRR-MAJ-01` (one underlying
authorization-transaction blocker).

Non-blocking findings: `IDS051-OBS-01` only.

No further amendment is required for MAJ-01, MAJ-03 or MIN-01. No broad IDS
review or redesign is requested.

## 10. Conformance, readiness and governance

Architecture-051: **CONFORMS / NO AMENDMENT**.

ADR-024: **CONFORMS / NO AMENDMENT**.

EDS-051 including focused persistence reconciliation: **CONFORMS / NO FURTHER
AMENDMENT**.

PATCH boundary: **PASS**. No PATCH-052 through PATCH-060 operational behavior
was introduced.

Implementation Plan readiness: **NO**. The Plan would still have to invent the
commit-stable authorization revalidation/locking boundary and its concurrency
tests. IDS-051 is not eligible for Human IDS Acceptance.

The Independent IDS Review `FAIL / STOPPED` and this focused re-review failure
remain historical evidence. Focused remediation is not acceptance. No
Implementation Plan, implementation, migration or PATCH-052 authority exists.

## 11. Validation and repository impact

Validation performed:

- re-read the accepted EDS focused persistence reconciliation and remediated
  IDS profile/M1/projection surfaces;
- re-inspected actual synchronous `SessionLocal`, request authentication,
  `User`, `UserOrganizationMembership`, `Organization`, Project/Workspace and
  committing generic Audit behavior;
- exercised the request/guarded Session authorization race mentally under
  PostgreSQL READ COMMITTED and the stated lock matrix;
- reviewed exact role provisioning, ownership, column grants, readiness,
  projection activation, manifests, test vectors and Batch 2/3 ordering;
- verified M2/M3 and PATCH boundaries remain unchanged; and
- created no production/test/migration file and executed no migration.

Files created: this focused re-review artifact only.

Files modified: none.

Production files: **0**. Test files: **0**. Migration files: **0**.

## 12. Exact governance state and next action

| Governance item | State after focused re-review |
|---|---|
| PATCH-051 | REGISTERED / OPEN |
| ADR-024 | ACCEPTED |
| Architecture-051 | ACCEPTED / COMPLETE |
| EDS-051 | ACCEPTED / COMPLETE WITH FOCUSED PERSISTENCE RECONCILIATION |
| Human EDS Acceptance | PASS / GRANTED / PRESERVED |
| Original Independent IDS Review | FAIL / STOPPED; historical |
| Focused IDS remediation | PASS / COMPLETE; historical remediation record |
| Focused Independent IDS Re-review | **FAIL / STOPPED** |
| IDS-051 | PROPOSED / NOT ACCEPTED / FOCUSED AUTHORIZATION REMEDIATION REQUIRED |
| Human IDS Acceptance eligibility | NOT ELIGIBLE |
| Implementation Plan | NOT STARTED |
| Implementation | NOT AUTHORIZED |
| Migrations | NOT AUTHORIZED / NOT CREATED |
| PATCH-052 | NOT STARTED |
| Commercial V1 roadmap | HUMAN-FROZEN / UNCHANGED |

Exact next resume point: separately granted Human authority for minimum focused
IDS-051 authorization-lock/test remediation of `IDS051-MAJ-02` /
`IDS051-FRR-MAJ-01`, followed by another focused Independent IDS re-review.

Recommended Human decision: do not accept IDS-051 and do not authorize an
Implementation Plan. Authorize only the minimum focused remediation stated in
section 4.4.
