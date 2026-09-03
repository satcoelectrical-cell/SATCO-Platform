# IDS-051 Second Focused Independent Implementation Design Re-review

## 1. Review control and verdict

| Field | Result |
|---|---|
| PATCH | PATCH-051 — Shared Multi-Discipline Core & Discipline Package Contract |
| Authority | **HUMAN SECOND FOCUSED INDEPENDENT IDS-051 RE-REVIEW AUTHORITY: GRANTED** |
| Scope | `IDS051-MAJ-02`, `IDS051-FRR-MAJ-01` and directly affected consistency only |
| Verdict | **PASS / ACCEPTED** |
| New Critical / Major / Minor / Observation | **0 / 0 / 0 / 0** |
| IDS-051 Human acceptance eligibility | **ELIGIBLE FOR HUMAN IDS ACCEPTANCE** |

**SECOND FOCUSED INDEPENDENT IDS-051 RE-REVIEW: PASS / ACCEPTED.**

The remediated IDS now guarantees commit-stable mutation authorization for
PATCH-051 guarded writes. It carries identity rather than permission across
the request/guarded Session boundary, locks and rereads the actual mutable
authority rows, stabilizes Project owner/scope on the already-required Project
lock, defines compatible revocation ordering and preserves one outer
transaction through Audit and commit. No stale-authority commit, tenant defect,
authorization-before-disclosure defect, transaction-completion ambiguity or
concrete scoped deadlock remains.

The historical Independent IDS Review and first Focused Independent IDS
Re-review remain `FAIL / STOPPED`. This review neither rewrites those records
nor Human-accepts IDS-051.

## 2. Actual repository authorization model

Independent inspection confirms every remediated authority fact maps to an
actual repository row and column:

| Authority | Actual repository evidence | Review result |
|---|---|---|
| User | `backend/app/models/user.py`: `users.id`, `is_active`, `role`, `auth_version`, `version` | exact mutable account/role/credential row; lockable |
| Membership | `backend/app/models/organization.py`: composite PK `(user_id, organization_id)`, `is_enabled`, `is_selected`, `version` | exact active-scope row; lockable |
| Organization | `backend/app/models/organization.py`: `organizations.id`, `is_active` | active state is mutable and lockable; no production disable service exists |
| Project | `backend/app/models/project.py`: `organization_id`, `owner_id` | tenant/owner authority is on the Project row |
| Workspace | `backend/app/models/engineering_workspace.py`: `project_id`, `owner_id`, assignment/member relationships | resource state only for the reviewed mutations; not configuration authority |
| Authentication | `backend/app/dependencies/auth.py` and `backend/app/core/security.py` | access tokens carry `av`; request authentication compares it to `User.auth_version` |
| Revocation | `backend/app/services/onboarding_service.py` and `repositories/onboarding_repository.py` | supported account, membership and role changes use ORM rows and row locks; planned ordering adaptation is manifest-bound |
| Project owner transfer | `ProjectUpdate.owner_id`, `ProjectService.update()`, `ProjectRepository.update()` | supported transfer emits an UPDATE of the same Project row |
| Audit | `backend/app/services/audit_service.py` | current helper commits; IDS correctly prohibits it and specifies non-completing staging for guarded work |
| Session | `backend/app/core/database.py` | synchronous `SessionLocal`, `autocommit=False`; request dependency closes its Session without owning guarded writes |

Role is stored only on `users.role`. Repository model/permission inspection
found no role-assignment table, role membership row or independent permission
record that could evade the User row lock.

## 3. Stable request identity and auth-version review

The frozen request DTO is correctly bounded to actor ID, requested
Organization ID, the verified credential `auth_version` claim and optional
request/correlation ID. Role, permission outcomes, active-account outcome,
membership enable/selection/version and source-owner decisions are explicitly
prohibited as authoritative DTO fields. No request-bound ORM object or Session
enters the guarded service.

The `auth_version` rule is coherent with the actual token model:

- `create_access_token()` writes the supplied version as JWT claim `av`;
- `get_current_user()` rejects when token `av` differs from current
  `User.auth_version`;
- after the request check, the claim/equal verified value is stable request
  credential context; and
- the guarded loader locks the User row and compares that request credential
  version again with the current locked `users.auth_version`.

Therefore a password/reset/account action that increments `auth_version`
between request authentication and guarded execution invalidates the guarded
mutation. The IDS does not redesign authentication and leaves no material
implementation choice about the comparison.

## 4. Guarded authority lock set and current predicates

`GuardedDisciplinePackageAuthorityLoader` in the planned
`backend/app/repositories/discipline_package_unit_of_work.py` receives the
already-open guarded Session. Immediately after the shared advisory guard it
performs separate `SELECT ... FOR UPDATE` reads of:

1. exact `User.id == actor_id`;
2. exact membership PK `(actor_id, requested_organization_id)`; and
3. exact `Organization.id == requested_organization_id`.

From those locked rows it requires current User activity, credential-version
equality, an operation-permitted live role, enabled and selected membership,
and active Organization. The returned context is transaction-local and is
invalid after UoW completion. The helper never opens, begins, commits or rolls
back a Session.

This is the minimum sufficient actor/scope lock set. Membership version and
User version remain current transaction evidence rather than frozen permission
claims; the row locks stabilize all relevant row state through completion.

## 5. Project and source-owner authority

Organization configuration is admin-only. Project configuration, removal,
rebind and guarded Workspace creation authorize from current locked User role
or `projects.owner_id == actor_id` after locking the tenant-scoped Project
`FOR UPDATE`. The same Project row also stabilizes `organization_id`.

No separate mutable source-owner row applies to these PATCH-051 operations.
Workspace ownership/membership does not authorize Organization or Project
configuration, Project rebind, or creation of a not-yet-existing Workspace.
Ascending Workspace locks in rebind stabilize affected resource/binding state,
not actor authority. The lock set neither omits a real authority source nor
adds speculative authorization data.

## 6. Deterministic lock order and revocation-path compatibility

The final universal guarded order is:

```text
Registry advisory guard
-> actor User FOR UPDATE
-> exact actor/Organization membership FOR UPDATE
-> Organization FOR UPDATE
-> Registry projection/configuration state
-> Project FOR UPDATE
-> Project head FOR UPDATE
-> affected Workspaces FOR UPDATE by ascending ID
-> writes
-> Audit staging
-> outer UoW commit
```

Operations omit unused suffixes and never invert the prefix. Organization
replacement takes no Project/Workspace locks. Project and Workspace operations
use the same prefix and resource order. Two guarded operations for one actor or
Organization serialize on an early row rather than holding later rows while
requesting earlier ones.

The current repository is pre-implementation: `mutate_member()` and
`issue_reset()` presently take membership before User. The IDS does not assume
otherwise. It explicitly adds both onboarding repository/service files to the
future production manifest and Batch 3, requiring User-before-membership and
one ascending-User-ID lock set for the target plus active admins before any
membership lock. `complete_credential()` already uses the relevant User,
membership, Organization order; User-only password change is a compatible
subset.

For two admin-removal operations, each future path obtains the same applicable
User set in ascending ID order. Neither can hold a higher User while waiting
for a lower User, and membership is not acquired until the User set is held.
The actual application exposes no supported multi-membership mutation that
requires an additional membership-set order.

## 7. Concurrent revocation and linearization review

PostgreSQL UPDATE/DELETE of a row conflicts with the guarded `FOR UPDATE` lock.
The design therefore permits exactly two correct schedules:

### Revocation wins

User disable, role change or membership disable/deselect locks and updates the
same authority row first. The guarded loader waits, then reads the committed
inactive, changed-version, downgraded, disabled or deselected state and denies
before protected writes. For User disable, both `is_active` and incremented
`auth_version` fail current authority. No stale request result is consulted.

### Guarded mutation wins

The guarded mutation locks the authority row first, validates current state,
performs all protected work and commits while the revocation blocks. The
revocation proceeds afterward. The mutation was authorized at its database
linearization point; this is explicitly accepted and is not a security defect.

Role change is covered by the User lock because role has no separate row.
Membership disable sets `is_enabled` and, in the supported member-mutation
path, also sets `is_selected`; the same composite membership row serializes
both predicates. A deselect-only test may use a direct test fixture because no
separate production deselection service exists.

Organization activity is still correctly locked because it is mutable
authorization state even though no production Organization-disable service is
present. The IDS does not invent such a service.

## 8. Project owner transfer and update escape-hatch review

The supported Project transfer path accepts `ProjectUpdate.owner_id`, assigns
the ORM attribute and commits an UPDATE of the same `projects` row. PostgreSQL
acquires a conflicting row lock for that UPDATE even though the legacy service
does not preselect `FOR UPDATE`:

- if transfer UPDATE executes first, guarded Project acquisition waits and
  then rereads the new owner, denying a stale old-owner decision; or
- if the guarded Project lock executes first, transfer waits until the guarded
  mutation commits and becomes the later valid change.

Inspection found no supported application bulk/direct UPDATE escape for
`users.is_active`, `users.role`, `users.auth_version`, membership enable/
selection, `organizations.is_active` or Project owner. Onboarding changes use
loaded ORM rows; password/credential paths lock User; Project owner uses normal
ORM update. `revoke_live_credentials()` bulk-updates account-action credential
rows, not any reviewed authority fact. Arbitrary DBA/manual SQL is outside the
review, and even ordinary direct PostgreSQL UPDATE of a reviewed row would
still conflict with its guarded `FOR UPDATE` lock.

## 9. Request/guarded Session and retry races

If the request Session authenticates valid authority and a change commits
before the guarded Session begins, the guarded loader locks current rows and
rejects the changed authority. It cannot reuse request-time role or membership
decisions.

If authority changes after the guarded locks, the changer blocks until guarded
commit and becomes the accepted later linearization. The authority locks are
transaction locks and therefore remain held through the outer UoW completion.

If an authorized first attempt rolls back because of an accepted timeout,
deadlock or serialization conflict, the retry loop closes it and creates a new
Session/UoW. The retry reacquires the advisory guard, authority locks, current
authority, Registry/configuration state and resource locks. Revocation between
attempts is observed and denies attempt two. No transaction-local authority
context crosses the attempt boundary.

## 10. Guarded mutation atomicity and Audit

Organization configuration holds the three authority locks through Registry
validation, Organization head/selection updates, package Audit staging and the
single outer commit. No helper may complete the transaction.

Project configuration/rebind holds them through Organization configuration,
Project/head and ascending Workspace locks, immutable revision/selections,
binding updates, package Audit staging and one final commit.

Workspace creation holds them through Project authority, binding derivation,
Workspace/member inserts, generic Audit staging, package Audit staging and one
final commit. It explicitly cannot call the current committing
`create_audit_log()`/`_audit_and_commit()` seam.

Authorization failure occurs before protected writes. Any later failure after
staging rolls back the same transaction, including all success Audit rows.
Denied/revoked operations cannot commit a success Audit, and no new security
Audit subsystem is required.

## 11. Scoped deadlock review

No concrete lock cycle remains for the required pairs:

| Pair | Result |
|---|---|
| User disable vs Organization configuration | both contend on User first; winner determines valid linearization |
| membership disable vs Project configuration | supported revocation takes User then the same membership; guarded path uses the same order |
| role change vs Workspace creation | same User row and order; no later reverse authority acquisition |
| Project owner transfer vs Project rebind | same Project row; transfer acquires no package lock afterward |
| two guarded Project operations | common advisory mode, then User/membership/Organization prefix and same Project/head/Workspace order |
| admin multi-User mutation vs guarded mutation | ascending User set before membership; guarded path holding one User can proceed to an unheld membership rather than wait on a membership held by the admin path |

Organization configuration is never acquired before Organization authority,
and no guarded operation acquires User/membership after Project or Workspace.
The design's contention is conservative—Organization `FOR UPDATE` serializes
same-Organization guarded writes—but it is correct and not a deadlock.

## 12. Future test-vector sufficiency

The IDS now requires real two-Session PostgreSQL/barrier tests, not only mocks,
for User-disable wins, guarded-mutation wins, membership disable/deselect,
role removal, stale request context, retry after revocation, Workspace creation,
Project rebind, Organization configuration and Project owner transfer. Each
denial vector asserts absence of configuration, revision, binding, Workspace,
member and success-Audit effects as applicable. Mutation-first vectors prove
the revocation UPDATE blocks until guarded commit.

The transaction suite also retains same-Session/connection guard affinity,
authority-lock lifetime, exact global order, non-completing helper enforcement,
fresh retries and full Audit rollback. These vectors are sufficiently precise
for an Implementation Plan; tests need not exist during IDS review.

## 13. Closed-finding and governing-design regression check

The authorization amendment does not alter semantic profile/release
membership persistence, Registry projection privileges or Discipline counts.
Therefore:

| Item | Disposition |
|---|---|
| `IDS051-MAJ-01` | **RESOLVED / CLOSED; preserved** |
| `IDS051-MAJ-03` | **RESOLVED / CLOSED; preserved** |
| `IDS051-MIN-01` | **RESOLVED / CLOSED; six Workspace-selectable Disciplines preserved** |
| `IDS051-OBS-01` | **OPEN / NON-BLOCKING** |
| Architecture-051 | **CONFORMS / NO AMENDMENT** |
| ADR-024 | **CONFORMS / NO AMENDMENT** |
| EDS-051 | **CONFORMS / NO AMENDMENT** |
| PATCH boundary | **PASS; no PATCH-052 through PATCH-060 behavior introduced** |

## 14. Finding register and Implementation Plan readiness

| Finding | Second focused re-review disposition |
|---|---|
| `IDS051-MAJ-02` | **RESOLVED / CLOSED** |
| `IDS051-FRR-MAJ-01` | **RESOLVED / CLOSED** |
| new Critical | **0** |
| new Major | **0** |
| new Minor | **0** |
| new Observation | **0** |

Blocking findings: **NONE**.

Non-blocking findings: `IDS051-OBS-01` only.

Required further IDS amendment: **NONE**.

Implementation Plan readiness: **YES**. A future Plan can sequence execution
without inventing stable/mutable authority classification, lock set, lock
order, request/guarded Session boundary, revocation or Project-owner
serialization, retry authority, Audit rollback or concurrency tests.

IDS-051 is **ELIGIBLE FOR HUMAN IDS ACCEPTANCE**. This review does not itself
grant that acceptance and does not authorize an Implementation Plan.

## 15. Validation and repository impact

Validation performed:

- re-inspected actual User, Organization, membership, Project and Workspace
  models and exact authority columns;
- re-inspected token `av`, request authentication and active Organization
  derivation;
- re-inspected onboarding account/membership/role/credential mutation paths,
  Project owner update, Workspace create, generic Audit and Session lifecycle;
- searched supported production paths for direct/bulk updates of reviewed
  authority fields and for independent role persistence;
- traced revocation-first, mutation-first, request/guarded, post-lock, retry,
  owner-transfer and required deadlock schedules;
- checked transaction matrix, test vectors, Batch 3 and exact future manifests;
- performed only this review documentation action; and
- created no production/test/migration file and executed no migration.

Files created: this second focused re-review artifact only.

Files modified: none.

Production files: **0**. Test files: **0**. Migration files: **0**.

## 16. Exact governance state and next action

| Governance item | State after second focused re-review |
|---|---|
| PATCH-051 | REGISTERED / OPEN |
| Architecture-051 | ACCEPTED / COMPLETE |
| ADR-024 | ACCEPTED |
| EDS-051 | ACCEPTED / COMPLETE WITH FOCUSED PERSISTENCE RECONCILIATION |
| Historical Independent IDS Review | FAIL / STOPPED; preserved |
| Historical first Focused Independent IDS Re-review | FAIL / STOPPED; preserved |
| Second Focused Independent IDS Re-review | **PASS / ACCEPTED** |
| `IDS051-MAJ-02` / `IDS051-FRR-MAJ-01` | **RESOLVED / CLOSED** |
| IDS-051 | PROPOSED / SECOND FOCUSED RE-REVIEW PASS / ELIGIBLE FOR HUMAN IDS ACCEPTANCE |
| Human IDS Acceptance | NOT YET GRANTED |
| Implementation Plan | NOT STARTED |
| Implementation | NOT AUTHORIZED |
| Migrations | NOT AUTHORIZED / NOT CREATED |
| PATCH-052 | NOT STARTED |

Exact next resume point: separately governed Human IDS-051 Acceptance review.

Recommended Human decision: review and, if satisfied, Human-accept IDS-051.
Do not begin an Implementation Plan until that separate acceptance is granted.
