# PATCH-051 WP051-MAJ-01 remediation implementation evidence

## Scope and interruption record

This evidence covers only the accepted correction that moves standing from an immutable descriptor to an exact Registry-release membership. The preceding run was manually interrupted during execution. That was an execution interruption, not a governance failure; its surviving source and database state were inspected before this remediation resumed.

No production, customer, or governed operational database was accessed. The only database recreated and exercised was the authorized disposable `satco_platform_patch02022_test` database.

## Resumed checkpoint

At resumption, the worktree contained the bounded runtime correction, M6, and focused tests. `git diff --check` was clean and no files were staged. The source graph was linear, with M6 as the only successor of M5. M1--M5 remained present with their established revisions and M4 retained the prior recorded SHA-256 `19e4c2729c5151dab9c989c38aa8d55de5ce7edbe0850c75bb459e7bc4e5daad`.

The surviving test database was read-only inspected first. It was already at `e05100000006`, had no descriptor `standing` column, had the exact `ix_dp_membership_release_standing` index, and had the membership standing check constraint. It also contained durable fixture/provenance rows (24 releases/descriptors/memberships and bound Workspaces), so it was correctly unsafe for an in-place downgrade or replay. There were no prepared transactions, non-idle sessions, or relevant Registry locks.

| Work item | Resumed classification | Final result |
|---|---|---|
| Descriptor contract, Registry source, canonicalization, DescriptorDigest | COMPLETE | verified |
| RegistryDigest; SelectedSet/Profile/Combination digest boundaries | COMPLETE | verified |
| Compatibility standing, installer, reconciliation, readiness | COMPLETE | verified |
| API, Workspace/effective state, frontend integration | COMPLETE | verified |
| M6 source and fail-closed guards | COMPLETE | verified |
| Migration tests and semantic digest tests | NEEDS VERIFICATION | passed |
| Isolated database recreation and M6 execution | NEEDS VERIFICATION | passed |
| Downgrade/re-upgrade convergence | NEEDS VERIFICATION | passed |
| Functional and regression suites | NEEDS VERIFICATION | passed except documented mount-only source-test harness limitation |
| Evidence and fresh focused re-review | NOT STARTED | complete |

## Corrected contract and migration result

`DescriptorRegistrationV1` owns `standing`; the immutable `DisciplinePackageDescriptorV1` does not. Descriptor canonical bytes and `DescriptorDigest` therefore exclude standing. Registry assembly retains a per-release membership-standing mapping and includes it in `RegistryDigest`. The selected descriptor-set, compatibility profile, and combination digests continue to use exact descriptor selections only.

The installer writes standing only to `discipline_package_registry_memberships`; source/projection parity and readiness compare it there. Compatibility, selection, supported-package API, and effective Workspace state resolve standing from the appropriate release membership. Project exact-version pins, Workspace binding identity, and the read-only runtime projection are unchanged. Standing remains eligibility state only: it grants no tenant access, disclosure, entitlement, engineering, or Human authority.

M6 is exactly `e05100000006` with parent `e05100000005`. It verifies empty, unreferenced provenance and the immutable membership-standing contract; adds `(registry_digest, standing, package_key, package_version)`; and removes only `discipline_package_descriptors.standing`. It performs no backfill, descriptor rehash, provenance rewrite, unrelated schema change, or M7.

## Isolated PostgreSQL proof

After the read-only checkpoint, only the authorized disposable database was recreated. Its fresh bootstrap executed the canonical chain:

```text
base -> e04700000001 -> e05100000001 -> e05100000002 -> e05100000003
     -> e05100000004 -> e05100000005 -> e05100000006
```

The initial post-bootstrap collection exposed only local harness credentials: the backend container supplied a restricted runtime login while the test harness requires a migration-capable owner. A temporary local test owner and the documented test-only runtime password were used without printing any credential. This did not change production state.

`tests/test_discipline_package_migration.py` then passed **10 tests**. It executes actual M6 operations on isolated schemas and proves empty M5 upgrade, empty M6 downgrade, re-upgrade convergence, unsafe non-empty upgrade and downgrade failure, and membership-contract failure. Final direct catalog inspection reported `e05100000006`, no descriptor standing, the exact membership constraint/index, and zero prepared transactions.

## Validation

| Validation | Result |
|---|---|
| M6 migration suite | 10 passed |
| Registry/API/security/runtime/Workspace PostgreSQL suite | 122 passed |
| Role-bootstrap source test in backend container | harness-limited: `/app` does not mount repository `postgres/`; direct source inspection passed |
| Frontend | 20 files, 91 tests passed |
| TypeScript typecheck and production build | passed |
| Python compilation | passed |
| Alembic heads/current | sole/current `e05100000006` |
| `git diff --check` and staged diff check | passed; no staged files |

The one container test limitation is pre-existing and environment-only: its test requests `SATCO_REPOSITORY_ROOT`, but the backend image exposes only `/app`. Direct inspection of `postgres/init/001_satco_database_roles.sh` and M1 verified the same fixed installer/runtime-role assertions. It is not an M6, privilege, or production defect.

## Outcome

The bounded correction and its migration proof are complete. The separate fresh focused re-review is recorded in `docs/reviews/PATCH-051-WP051-MAJ-01-Focused-Independent-Re-review.md`.

WP051-MAJ-01:
RESOLVED / CLOSED

PATCH-051 REGISTRY-STANDING REMEDIATION:
PASS / ACCEPTED / COMPLETE
