# PATCH-051 Batch-3 implementation evidence

## Scope and result

Batch 3 completes the accepted configuration, binding, guarded-authority and
M3 cutover implementation.  It does not start Batch 4, PATCH-052 or an
independent review, and it creates no migration beyond the authorized M3
revision `e05100000003`.

## Production seams

- Organization configuration uses exact executable descriptors, immutable
  version progression, enabled/disabled selection state and one package Audit
  event in the guarded outer UoW.
- Project configuration validates the organization enablement, exact Registry
  profile and compatible combination; it appends immutable revisions, advances
  the Project head and rebinds affected operational Workspaces atomically.
- The real Workspace create route injects a fresh guarded UoW factory.  It
  uses a fresh Session per attempt, acquires the fixed shared advisory guard,
  locks and revalidates User, membership and Organization, and stages generic
  and package Audit records before the sole outer commit.
- Executable Electrical, Instrumentation and Control Workspaces require an
  exact current Project pin.  Mechanical, Civil and Process are represented as
  canonical `FUTURE_UNAVAILABLE_UNBOUND` Workspaces; no operational capability
  or PATCH-052 behavior is implied.
- The guarded authority order is User, membership, Organization, then Registry
  and scoped resource locks.  A stale `auth_version`, disabled/deselected
  membership, role change, inactive user or inactive Organization fails before
  protected writes and success Audit.  The onboarding member-mutation and
  reset paths use the matching mutable-authority lock order.
- Retryable PostgreSQL timeout/deadlock/serialization errors are bounded to
  two full attempts.  Each attempt constructs a new Session/UoW, re-acquires
  the guard and repeats reads; exhaustion becomes a conflict.
- M3 remains the sole cutover migration, from `e05100000002`, with required
  PASS preflight input, exact six-value mapping, no fabricated package binding,
  non-null binding state and deferred Workspace/Project consistency triggers.

## Isolated PostgreSQL validation

All mutation commands used only the repository-enforced isolated database
`satco_platform_patch02022_test`.  Read-only identity/head checks after the
run reported `satco_platform_patch02022_test|e05100000003`.  The local
application database was queried read-only only and remained at
`satco_platform|e03800000001`; no customer or production database command was
issued.

The focused Batch-3 command passed 58 tests:

```text
python -m pytest -q \
  tests/test_engineering_workspace_core.py \
  tests/test_engineering_workspace_permissions.py \
  tests/test_engineering_workspace_migration.py \
  tests/test_discipline_package_service.py \
  tests/test_discipline_package_audit.py \
  tests/test_discipline_package_projection.py \
  tests/test_discipline_package_migration.py \
  tests/test_discipline_package_preflight.py \
  tests/test_discipline_package_transaction.py
```

The real PostgreSQL guard tests use two independent connections.  They prove
the fixed `(1396790339, 51)` shared guard, `SET LOCAL lock_timeout = '5s'`
before the advisory lock, shared/shared coexistence, distinct database
connections and a distinct Session for a later UoW attempt.

The guarded configuration tests prove the path
configuration → immutable Project revision → operational Workspace binding →
atomic rebind.  They also prove future-unbound behavior, stale-authority
rejection with no Project revision/Audit, cross-Organization non-disclosure,
and Audit failure rollback of Workspace plus generic/package Audit rows.

Batch-1 contract/registry/conformance and Batch-2 projection/migration/
preflight/transaction regression tests were also rerun with the onboarding
integration suite after the M3 head update.  They pass in the final command
recorded with this implementation run.

## Recovery and remaining operational obligation

History and cutover values remain forward-only after use.  The existing
`IDS051-OBS-01` deployment qualification/preflight evidence obligation remains
open; it is not a Batch-3 implementation blocker.  This artifact records
implementation evidence only and intentionally does not perform or claim the
Fresh Independent Batch-3 Review.

## Focused remediation addendum — MAJ-051-B3-01 through MAJ-051-B3-03

This addendum preserves the preceding implementation record and records only
the subsequently authorized focused remediation work.  All validation again
used `satco_platform_patch02022_test`; no customer or production database was
mutated.

- **MAJ-01:** Project-configuration removal now locks candidate operational
  Workspaces by ascending `engineering_workspaces.id`, rather than applying
  `FOR UPDATE` to an aggregate (which PostgreSQL rejects).  The regression
  verifies successful removal, package Audit emission and cross-tenant denial.
- **MAJ-02:** both Project configuration and Workspace binding now rebuild the
  immutable persisted Registry manifest through the Batch-1 typed JSON
  boundary and call `evaluate_package_compatibility` on full exact
  `(key, version, descriptor digest)` selections.  Registry/profile digest and
  organization enablement must also agree; unavailable or malformed source is
  fail-closed.  The former key-only SQL compatibility path is not used.
- **MAJ-03:** M3 now requires a matching M2-head PASS artifact containing the
  Workspace value census, total count, ordered ID checksum, orphan/duplicate/
  null checks and historical-source availability.  It establishes local lock
  and statement timeouts, locks migration scope, processes ordered locked ID
  chunks, asserts chunk and total affected counts, validates the M2 exact
  selection FK and forces deferred consistency checks before completion.

Focused validation after these changes:

```text
tests/test_discipline_package_service.py
tests/test_discipline_package_audit.py
tests/test_discipline_package_migration.py
tests/test_discipline_package_preflight.py
tests/test_discipline_package_transaction.py
tests/test_engineering_workspace_migration.py
```

Result: **20 passed**.  Python compilation for the changed services, M3 and
preflight script and `git diff --check` also passed.

## Resume completion — MAJ-04 and corrected-M3 proof

The earlier stopped/failing review record is preserved. The following
authorized completion evidence was obtained solely against
`satco_platform_patch02022_test`.

- Schema-owner and restricted-runtime connections were separately proved for
  that exact database. Existing local credentials were passed only to child
  test processes; they were never printed, persisted, committed or used to
  elevate the runtime role.
- The independent two-session **REVOCATION-WINS** vector passed twice
  deterministically: Session B committed revocation before Session A's
  authority validation, Session A failed closed, and no protected head or
  success package Audit row committed.
- A genuine M3 production defect was found: the guard's ambiguous
  `current_revision` reference prevented valid operational Workspace inserts
  from committing. The minimal sole correction is
  `head.current_revision INTO current_revision` in existing M3; no M4 exists.
- Source and installed PostgreSQL proof both report `e05100000003`.
  `pg_get_functiondef` for the installed guard contains that qualified
  correction, and Alembic reports the exact `e05100000002 -> e05100000003`
  edge.
- `test_corrected_m3_guard_commits_valid_operational_workspace_and_rejects_invalid_binding`
  commits a valid direct operational Workspace insert under an exact Project
  pin, then proves the installed deferred guard rejects an invalid bound
  `FUTURE_UNAVAILABLE_UNBOUND` state. The valid commit fails under the former
  ambiguous function definition.
- The real MAJ-04 independent-session matrix passed: mutation-wins;
  retry-after-revocation with a fresh Session/UoW; maximum-two-attempt and
  SQLSTATE retry classification; atomic multi-Workspace rebind rollback;
  ascending Workspace-ID lock order; and cross-tenant non-disclosure while a
  foreign Project is locked. Each vector records distinct backend PIDs,
  event/lock synchronization, outcome, final committed state and Audit state.
- The injected second-rebind failure proves head/version remain `(1, 1)`, no
  revision-2 state or success Audit commits, all affected Workspaces retain
  revision 1, and observed production locking orders Workspace IDs ascending.
- One test-only fixture fix was needed: the legacy independent-session
  Workspace uniqueness test now durably seeds its shared test Organization
  rather than relying on a rollback-only fixture transaction. No production
  behavior changed.

Final affected PostgreSQL result: **109 passed** across Batch-3 configuration,
M3, Audit, transaction and Workspace suites plus relevant Batch-1
contract/registry/compatibility/conformance and Batch-2
projection/preflight/remediation/migration suites. Compile/import, Alembic
head/history and `git diff --check` passed. A read-only local application DB
check reported `satco_platform|e03800000001`; it was not migrated or mutated.
