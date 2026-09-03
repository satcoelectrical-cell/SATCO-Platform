# IRR-051 Focused Independent Implementation Readiness Re-review

## 1. Review control and verdict

| Field | Result |
|---|---|
| PATCH | PATCH-051 — Shared Multi-Discipline Core & Discipline Package Contract |
| Authority | **HUMAN FOCUSED INDEPENDENT IRR-051 RE-REVIEW AUTHORITY: GRANTED** |
| Scope | `IRR051-MAJ-01`, `IRR051-MAJ-02`, and directly affected consistency surfaces only |
| Historical IRR-051 | **FAIL / STOPPED**; preserved unchanged |
| Focused Plan remediation | **PASS / COMPLETE** |
| Verdict | **PASS / ACCEPTED / COMPLETE** |
| New Critical / Major / Minor / Observation | **0 / 0 / 0 / 0** |
| Implementation Plan-051 final review state | **ACCEPTED / IMPLEMENTATION-READY** |
| Implementation | **ELIGIBLE FOR SEPARATE HUMAN IMPLEMENTATION AUTHORITY / NOT AUTHORIZED** |
| Migration creation / execution | **NOT AUTHORIZED / NOT AUTHORIZED** |

**FOCUSED INDEPENDENT IRR-051 RE-REVIEW: PASS / ACCEPTED / COMPLETE.**

The focused remediation closes both historical blocking findings. The final
Plan now makes the accepted cross-process advisory serialization and the
installer-principal bootstrap/secret boundary executable without requiring an
implementation agent to choose a key, guard mode, protected operation, lock
order, retry policy, principal owner, secret-delivery path, privilege matrix,
service boundary, bootstrap order, or evidence owner.

This review does not amend or Human-accept the Plan, grant implementation or
migration authority, execute work, close PATCH-051, or begin PATCH-052.

## 2. Inputs and actual repository baseline

The re-review inspected only the remediated Plan, the two historical IRR
findings, directly affected accepted EDS/IDS provisions, and the actual paths
needed to determine executability:

- `postgres/init/001_satco_database_roles.sh` is the clean-database role
  bootstrap used by local Compose through `/docker-entrypoint-initdb.d`;
- `ops/scripts/preflight.sh` has an existing `before` phase, runs under the
  migration credential, and already creates or validates `satco_runtime` for
  deployed databases before Alembic;
- `docker-compose.yml` wires the local PostgreSQL init and migration/runtime
  roles;
- `docker-compose.production.yml` has separate backend, migration and database
  services, explicit per-service secret lists, and an established pattern for
  mounting deployment scripts into bounded jobs with Compose configs;
- `backend/app/core/database.py` supplies synchronous `SessionLocal` with
  `autocommit=False` and existing PostgreSQL privilege-readiness conventions;
- `backend/tests/conftest.py` uses a real PostgreSQL database and owner/runtime
  role bootstrap, providing an applicable test topology; and
- `backend/scripts/discipline_package_registry.py` is correctly a future
  Batch-2 CREATE path already fixed by accepted IDS-051. The authorized Compose
  job/config wiring can make that deployment CLI available without placing its
  secret in the ordinary backend service.

The historical IRR-051 artifact remains `FAIL / STOPPED` and is not rewritten.

## 3. IRR051-MAJ-01 — advisory guard

### 3.1 Exact identity, operations and coverage

The Plan fixes the immutable two-key identity **`(1396790339, 51)`** and
prohibits dynamically derived keys, process-local substitutes, and session-
lifetime advisory locks.

| Protected operation | Exact transaction-level operation | Result |
|---|---|---|
| Registry projection installation/reconciliation and current-release activation | `SELECT pg_advisory_xact_lock(1396790339, 51)` | **EXCLUSIVE; explicit** |
| Organization package-configuration replace | `SELECT pg_advisory_xact_lock_shared(1396790339, 51)` | **SHARED; explicit** |
| Project initial/replace/revision/rebind/removal | `SELECT pg_advisory_xact_lock_shared(1396790339, 51)` | **SHARED; explicit** |
| Workspace creation deriving applicability/binding and every PATCH-051 binding mutation | `SELECT pg_advisory_xact_lock_shared(1396790339, 51)` | **SHARED; explicit** |

The Plan declares that table to be the complete PATCH-051 set of runtime
mutations deriving committed state from current Registry/configuration and
requires any newly admitted such mutation to join it with SHARED mode. Search
found no accepted Registry-derived runtime mutation outside that coverage.

### 3.2 Order, affinity and timeout

The universal guarded order is exact and non-contradictory:

```text
advisory guard
-> User
-> membership
-> Organization
-> Registry/configuration
-> Project
-> Project head
-> Workspaces by ascending ID
-> writes
-> staged Audit
-> outer commit/rollback
```

Each attempt creates a fresh `SqlAlchemyDisciplinePackageUnitOfWork` from
`SessionLocal`, enters one caller-owned outer transaction, and uses that same
Session and checked-out PostgreSQL connection for the guard and all protected
work. The helper cannot create or switch a Session/connection, start or
complete the transaction, commit, roll back, or use autocommit.

After the outer transaction begins, the first SQL is exactly
`SET LOCAL lock_timeout = '5s'`; the advisory-lock statement is second. No
identity, authority, Registry, resource, compatibility, Audit, flush, or other
SQL may precede the timeout. Nothing in the planned fresh-UoW construction
requires protected SQL before this sequence.

### 3.3 Failure, retry and linearization

A lock timeout, deadlock, or accepted serialization failure escapes to the
outer UoW, rolls back the full transaction, retains no protected write or
success Audit, and never continues without the guard. Exhaustion maps to safe
`409 CONCURRENT_UPDATE`.

Where retry is accepted, there are at most two complete fresh attempts. Each
creates a new UoW, Session, connection and transaction; reissues the local
timeout; reacquires the advisory and authority/resource locks; and rereads all
Registry/configuration state. Registry activation has no internal retry and
requires a new installer UoW under deployment-orchestrator control.

Both required activation/runtime schedules are closed:

1. EXCLUSIVE activation first makes SHARED runtime work wait; after activation
   commits, runtime obtains SHARED and rereads the new current Registry.
2. SHARED runtime work first makes activation wait through runtime commit or
   rollback; activation then obtains EXCLUSIVE and proceeds.

No runtime transaction can validate against one current release and commit
Registry-derived state across activation of another release.

### 3.4 PostgreSQL evidence ownership

Batch 2 assigns `backend/tests/test_discipline_package_transaction.py` real-
PostgreSQL, two-Session/barrier evidence for the exact key, EXCLUSIVE and
SHARED acquisition, SHARED/SHARED coexistence, EXCLUSIVE/SHARED serialization
in both schedules, same-connection affinity, transaction-completion release,
the five-second timeout, timeout fail-closed, and retry reacquisition. SQLite
cannot substitute for these tests.

Batch 3 modifies that suite to prove the actual Organization configuration,
Project configuration/removal/rebind, guarded Workspace creation and PATCH-051
binding mutations take SHARED after the timeout and before authority/resource
locks, hold it through commit, and reacquire it on a fresh retry.

**IRR051-MAJ-01: RESOLVED / CLOSED.**

## 4. IRR051-MAJ-02 — installer principal, secret and bootstrap

### 4.1 Executable owners and role contracts

The Plan no longer relies on unspecified external provisioning. Batch 2
assigns:

- clean-database role bootstrap to
  `postgres/init/001_satco_database_roles.sh`;
- existing/deployed-database create-or-validate to the existing
  `ops/scripts/preflight.sh` `before` phase under the migration credential;
- production secret and bounded installer-job wiring to
  `docker-compose.production.yml`;
- equivalent local role/credential wiring to `docker-compose.yml`; and
- test bootstrap and PostgreSQL role evidence to `backend/tests/conftest.py`
  and `backend/tests/test_discipline_package_database_roles.py`.

Both bootstrap paths require `satco_registry_installer` before M1 with exact
`LOGIN NOINHERIT NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION
NOBYPASSRLS`, no unintended membership, schema CREATE, ownership or pre-M1
application/table authority. M1 retains ownership under the migration
principal, fails if either fixed role is missing, creates no login role,
revokes broad/PUBLIC rights, and grants only installer SELECT/INSERT on six
projection tables plus column-level `UPDATE(is_current)`. DELETE, TRUNCATE,
broad UPDATE, tenant-table authority, trigger-function execution and historical
mutation remain denied.

`satco_runtime` continues through the same existing init/preflight convention.
It receives projection SELECT only and retains only accepted tenant
configuration/Audit rights; projection INSERT/UPDATE/DELETE and activation are
denied.

### 4.2 Secret and service isolation

Production Compose owns the external
`SATCO_REGISTRY_INSTALLER_DB_PASSWORD_FILE` interface and the protected
`registry_installer_db_password` secret. It is mounted read-only only into the
migration bootstrap job and the new deployment-only `registry-installer` job,
which maps it to the CLI password-file input. The current production topology
uses explicit service secret lists rather than global injection, so the Plan's
isolation is directly enforceable.

The normal backend, frontend and operations services receive neither the
installer secret nor its environment variable. The CLI runs outside ordinary
HTTP runtime with its own installer Engine; no FastAPI path needs or loads the
credential. The password cannot enter source control, logs, frontend/runtime
configuration output, Registry projection, or Audit.

### 4.3 Order and fail-closed validation

The executable sequence is fixed:

```text
database/deployment bootstrap
-> create/validate satco_registry_installer and establish its secret
-> create/validate satco_runtime
-> before-phase role/preflight evidence
-> M1 and its GRANT/REVOKE matrix
-> installer privilege self-check
-> runtime privilege/readiness check
-> Registry projection installation
-> Registry activation
-> later runtime configuration
```

No check depends on a later privilege: role/secret establishment precedes M1;
object-level self-checks follow M1; and projection writes follow both identity/
privilege checks. A missing or invalid fixed role stops preflight, while M1's
required-role/grant operation also fails and rolls back. Alembic has no role-
creation fallback.

Before any write, the deployment CLI introspects `current_user`, `pg_roles`,
`pg_auth_members`, ownership/schema privileges, exact six-table SELECT/INSERT,
column-level activation UPDATE, DELETE/broad-UPDATE denial and tenant-table
denial. Wrong identity or privileges exit before lock or write. Runtime
readiness uses PostgreSQL introspection to prove its identity, Registry SELECT,
projection mutation denial and retained accepted tenant configuration access.

### 4.4 Evidence and PostgreSQL tests

The deployment preflight/review owner retains canonical secret-free evidence
at `artifacts/patch-051/roles/<deployment-id>-<db-fingerprint>.json`. It records
role existence, attributes, membership absence, privileges, installer/runtime
identity and secret-file presence—but never secret contents—and remains
implementation/review evidence rather than PATCH-060 certification.

`backend/tests/test_discipline_package_database_roles.py` owns real-PostgreSQL
evidence for missing-role M1 failure, attributes, membership/ownership/schema
denials, installer SELECT/INSERT and activation-column UPDATE, installer
DELETE/broad-UPDATE denial, runtime SELECT and projection mutation denial,
wrong-principal failure and secret non-disclosure. The production-topology and
operations tests are also explicitly modified to verify Compose/preflight
wiring. SQLite is not accepted for role/grant enforcement.

**IRR051-MAJ-02: RESOLVED / CLOSED.**

## 5. Direct consistency checks

| Surface | Focused result |
|---|---|
| Batch 2 | owns principal bootstrap, secret interface, M1 prerequisites/grants, CLI, guard foundation, privilege validation, evidence and PostgreSQL lock/role tests |
| Batch 3 | consumes the shared guard, timeout, retry and authority foundation without redefining key or mode; holds the guard through Audit/commit |
| Production manifest | matches actual init, preflight, Compose, database and accepted future CLI paths |
| Test manifest | matches the repository's real-PostgreSQL harness and topology/operations test seams |
| Batch 2 acceptance | requires reproducible bootstrap/grants, exact guard/timeout behavior, installer-only mutation, runtime read-only projection and secret isolation |
| Batch 3 acceptance | requires exact SHARED acquisition before authority/resource locks through commit, fresh retries and both activation schedules |
| Architecture-051 | no contradiction; remains **ACCEPTED / COMPLETE** |
| ADR-024 | no contradiction; remains **ACCEPTED** |
| EDS-051 | exact transaction guard and linearization preserved; remains **ACCEPTED / COMPLETE WITH FOCUSED PERSISTENCE RECONCILIATION** |
| IDS-051 | exact guard/UoW/role authority and future paths preserved; remains **ACCEPTED / COMPLETE** |
| PATCH-052 | no operational discipline package behavior introduced; remains **NOT STARTED** |
| PATCH-060 | production deployment qualification is explicitly excluded |

`IDS051-OBS-01` remains **OPEN / NON-BLOCKING / DOWNSTREAM IMPLEMENTATION /
DEPLOYMENT EVIDENCE OBLIGATION**. Planned evidence does not resolve or certify
it.

## 6. Finding register and disposition

| Finding | Final status |
|---|---|
| `IRR051-MAJ-01` | **RESOLVED / CLOSED** |
| `IRR051-MAJ-02` | **RESOLVED / CLOSED** |

| Classification | New count |
|---|---:|
| Critical | 0 |
| Major | 0 |
| Minor | 0 |
| Observation | 0 |
| Blocking findings | 0 |
| Non-blocking findings | 0 |

No further Plan amendment or upstream reconciliation is required. Previously
passed IRR areas were not broadly re-reviewed, and no regression directly
caused by the focused remediation was found.

## 7. Final governance state

Implementation Plan-051 is **ACCEPTED / IMPLEMENTATION-READY** and eligible
for a separate Human implementation-authority decision. Implementation remains
**NOT AUTHORIZED**. Migration creation remains **NOT AUTHORIZED** unless later
explicitly included in granted implementation authority. Migration execution
remains **NOT AUTHORIZED** and separately governed.

PATCH-051 remains **REGISTERED / OPEN**. PATCH-052 remains **NOT STARTED**.
The Commercial V1 roadmap remains **HUMAN-FROZEN / UNCHANGED**.

The exact next resume point is a separate Human decision on bounded PATCH-051
implementation authority and the Batch-1 authorized file manifest. No further
broad IRR or Plan review is required.
