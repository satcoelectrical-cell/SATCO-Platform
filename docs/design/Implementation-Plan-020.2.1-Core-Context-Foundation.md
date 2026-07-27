# PATCH-020.2.1 Core Context Foundation Implementation Plan

## Status

Accepted

## Purpose

This plan translates accepted
`docs/design/IDS-020.2.1-Core-Context-Foundation.md` into an executable,
bounded implementation sequence.

It is a planning artifact only. It creates no implementation authority.
Implementation may begin only after this plan is approved and a repeated
Implementation Readiness Review returns **Ready for Implementation**.

## Governing Baseline

Implementation remains subordinate to:

1. `docs/20_Development_Lifecycle.md`;
2. accepted
   `docs/adr/ADR-014-Engineering-Workspace-Domain-Model.md`;
3. accepted
   `docs/adr/ADR-015-Engineering-Context-Domain-Architecture.md`;
4. accepted
   `docs/design/EDS-020.2-Engineering-Context-Foundation.md`;
5. accepted
   `docs/design/IDS-020.2.1-Core-Context-Foundation.md`;
6. PATCH-020.1 Workspace Core and the existing Project, User, authorization,
   audit, and PostgreSQL foundations.

If this plan conflicts with the accepted IDS or higher governance, the higher
artifact prevails and the affected work stops.

## Accountability

The accountable software-delivery roles are:

| Responsibility | Accountable role |
| --- | --- |
| Implementation Agent | Codex |
| Architecture and Product Reviewer | ChatGPT |
| Final Approval Authority | Repository Owner |
| Migration and Database Execution Authority | Repository Owner |
| Final Commit and Push Authority | Repository Owner |

These assignments govern software delivery only. They do not grant
professional engineering authority, engineering approval, technical
competence, or authority over Customer or Project engineering decisions.
Engineering judgment and engineering approval remain human responsibilities
under the Constitution, Product Bible, and SATCO governance.

Codex may implement only after a successful repeated IRR. ChatGPT reviews
architecture and product alignment but does not grant engineering approval.
The Repository Owner retains explicit authority for database execution, Final
Review approval, Commit, and Push.

## Repository Assessment

The current backend provides:

- Python, FastAPI, SQLAlchemy, Pydantic, PostgreSQL, and Alembic;
- explicit model, repository, service, exception, enum, and test layers;
- Project identity, ownership, assignment, lifecycle, and authorization;
- Engineering Workspace identity, Project and Discipline scope, owner,
  assignee, collaborators, archival behavior, and optimistic concurrency;
- centralized audit evidence;
- an additive Alembic chain whose current committed head is the PATCH-020.1
  Workspace Core revision;
- PostgreSQL-only tests protected by an explicit database-name and
  migration-head guard;
- savepoint-aware test transactions;
- existing Workspace core, permission, audit, migration, and search regression
  modules.

No Engineering Context implementation currently exists.

The existing centralized audit helper commits the active transaction.
PATCH-020.2.1 must preserve the proven Workspace pattern in which the Context
mutation and required success audit evidence succeed or roll back together.
Universal audit redesign remains outside scope.

## Operational Readiness Baseline

The pre-implementation baseline was captured without creating implementation,
tests, or a PATCH-020.2.1 migration.

### Repository migration baseline

- current repository Alembic head: `a20c1e0201f0`;
- expected PATCH-020.2.1 migration base: `a20c1e0201f0`;
- current development database revision: `d8271b8f1a29`;
- repository history: one head and one linear chain from base through seven
  revisions;
- no upgrade or downgrade was run during readiness closure.

PATCH-020.2.1 migration work begins from repository head
`a20c1e0201f0`, not from the older development database revision.

### Dedicated validation database

- exact name: `satco_platform_patch02021_test`;
- created empty and independently from `satco_platform`;
- public table count immediately after creation: `0`;
- `alembic_version` immediately after creation: absent;
- development data copied: none;
- migration run during creation: none;
- PostgreSQL volume change: none.

Every future migration or PostgreSQL test command must verify the active
database name before doing work.

### Pre-implementation regression baseline

The complete existing backend suite was run against the established isolated
`patch0201_validation` schema at repository head `a20c1e0201f0`.

- collected: `83`;
- passed: `83`;
- failed: `0`;
- skipped: `0`;
- warnings: `289`;
- duration: `21.89s`.

The warnings consist of one Starlette TestClient deprecation, two Pydantic
class-configuration deprecations, and 286 SQLAlchemy `datetime.utcnow`
deprecations emitted across existing tests. They are baseline warnings, not
PATCH-020.2.1 regressions.

The exact successful command is recorded in the Exact Validation Commands
section. An initial invocation against the prior isolated database’s default
public schema stopped during collection because its migration revision was
older than the required Workspace Core head. No test ran and no data changed
in that stopped invocation.

### Development database fingerprint baseline

The read-only baseline is:

| Item | Value |
| --- | --- |
| Database | `satco_platform` |
| Alembic revision | `d8271b8f1a29` |
| Public table count | `7` |
| `alembic_version` rows | `1` |
| `audit_logs` rows | `11` |
| `contacts` rows | `2` |
| `customers` rows | `5` |
| `project_code_sequences` rows | `0` |
| `projects` rows | `7` |
| `users` rows | `2` |
| Engineering Context tables | `0` |

The canonical fingerprint input is:

```text
database=satco_platform|revision=d8271b8f1a29|table_count=7|alembic_version=1|audit_logs=11|contacts=2|customers=5|project_code_sequences=0|projects=7|users=2|engineering_context_tables=0
```

Its SHA-256 hash is:

```text
a5c31884adf1faa73e638311ba437d7dcf3013857fca3aa9450c00abe2640b7d
```

The same read-only procedure is run after validation. Both the canonical
values and hash must match. Row contents are never read or exposed.

## Implementation Objectives

Implementation shall:

1. establish stable identity for each allowed Context kind;
2. preserve exactly one governing Project and an optional same-Project
   Workspace scope;
3. reference native subjects and sources without duplicating them;
4. implement Subject Reference, Qualified Fact, Qualified Engineering Value,
   Assumption, and Source and Evidence Reference only;
5. preserve information owner and active engineering steward responsibility
   without inferring competence;
6. preserve explicit, bounded authority standing without introducing an
   authority-promotion workflow;
7. support only applies-to, scoped-by, and evidenced-by relationship meanings;
8. implement current-use, withdrawal, version, and optimistic concurrency
   behavior;
9. enforce existing Project, Workspace, User, and source-access boundaries;
10. create atomic centralized audit evidence for successful material actions
    and no success evidence for failed actions;
11. preserve every PATCH-020.1 behavior;
12. add no interface endpoint, search behavior, AI behavior, or later
    PATCH-020.2 capability.

## Implementation Boundaries

The plan does not authorize:

- architecture redesign;
- scope reinterpretation;
- a universal Engineering Context Object;
- generic JSON Context;
- a new domain object beyond the accepted IDS;
- Project, Workspace, Customer, Discipline, User, or source duplication;
- new persisted roles;
- new interface endpoints or transport contracts;
- user-interface work;
- AI, AI Insights, or AI-generated Context;
- Derived Context;
- Missing Information or Conflict engines;
- Historical Context or snapshots;
- Context search;
- Human Review or authority-promotion workflows;
- source-precedence resolution;
- general or cross-Workspace relationship traversal;
- Interface Commitments;
- Engineering Decision Log;
- Engineering Execution Plan;
- Engineering Health or Workspace Readiness;
- Knowledge Graph;
- non-additive persistence changes;
- dependencies not already approved by the repository.

Any need beyond these boundaries returns to IDS governance.

## Planned File Set

The exact implementation file set is bounded as follows.

### New files

- `backend/app/enums/engineering_context.py`
  - contains the allow-listed Context kind, bounded authority standing,
    minimum relationship meaning, and current-use lifecycle values already
    approved by the IDS;
- `backend/app/models/engineering_context.py`
  - represents the accepted Context identity, scope, allowed typed meaning,
    responsibility, source reference, minimum relationship, lifecycle,
    version, and traceability responsibilities;
- `backend/app/exceptions/engineering_context.py`
  - provides bounded domain errors for absence, authorization, validation,
    lifecycle, and optimistic concurrency;
- `backend/app/repositories/engineering_context_repository.py`
  - performs scoped Context persistence, authorized retrieval, allow-listed
    linking, and compare-and-update behavior;
- `backend/app/services/engineering_context_service.py`
  - coordinates validation, authorization, atomic mutation, audit evidence,
    safe failure, and response-independent domain results;
- one additive revision file under `backend/migrations/versions/`
  - generated during implementation after the current committed head;
- `backend/tests/test_engineering_context_core.py`;
- `backend/tests/test_engineering_context_permissions.py`;
- `backend/tests/test_engineering_context_audit.py`;
- `backend/tests/test_engineering_context_migration.py`;
- `backend/tests/test_engineering_context_performance.py`.

### Existing files modified

- `backend/app/enums/__init__.py`
  - exports only the new accepted enum values;
- `backend/app/models/__init__.py`
  - registers the new model metadata;
- `backend/migrations/env.py`
  - registers the Core Context model metadata with the existing Alembic
    environment;
- `backend/tests/conftest.py`
  - imports the new model metadata and advances only the isolated-test
    migration-head guard after the new revision exists.

No router, search, frontend, or transport-contract file is created or
modified.

The file set may be narrowed if an export or exception file is unnecessary.
It may not be expanded without explicit Implementation Plan review.

## File Creation and Modification Sequence

### Step 1 — Confirm baseline

- record the current branch, HEAD, working-tree status, and migration head;
- record the protected development-database fingerprint;
- confirm the dedicated PATCH-020.2.1 PostgreSQL database name;
- confirm that its connection cannot resolve to the development database;
- record the existing full-regression baseline and warnings;
- confirm no dependency change is required.

### Step 2 — Add domain enum values

- create the bounded enum module;
- export its values;
- test exact allow-lists and rejection of unsupported values;
- keep all later Context kinds and states absent.

### Step 3 — Add Core Context persistence model

- create the Context model module using only IDS-approved objects and
  responsibilities;
- register it with model metadata;
- preserve native Project, Workspace, User, subject, and source identity;
- express integrity redundantly through domain validation and PostgreSQL where
  applicable;
- prevent generic JSON from carrying core engineering meaning.

### Step 4 — Add the additive migration

- generate one revision after the current committed head;
- inspect it against the approved model and planned file boundary;
- ensure it is additive and contains no unrelated alteration;
- validate forward application, complete chain replay, rollback or recovery,
  and reapplication in the isolated database;
- do not apply it to the development database.

### Step 5 — Add bounded exceptions

- add only errors required for Context absence, scope, authorization,
  validation, lifecycle, and version conflicts;
- preserve non-disclosure so inaccessible Context is not exposed through error
  distinctions.

### Step 6 — Add data-access behavior

- implement Project and optional Workspace scoping;
- retrieve native subjects and sources without copying them;
- enforce the minimum relationship allow-list;
- perform expected-version mutation atomically;
- make authorization filtering part of retrieval rather than a post-filter;
- avoid search, history, general traversal, and later-sub-patch behavior.

### Step 7 — Add orchestration behavior

- validate allowed kind, qualified meaning, responsibility, authority, source,
  scope, lifecycle, and expected version;
- evaluate existing role and Project or Workspace participation;
- enforce source confidentiality independently;
- coordinate Context mutation with centralized success audit evidence;
- roll back all state when audit, validation, authorization, or concurrency
  fails;
- expose no new endpoint.

### Step 8 — Add focused tests

- build deterministic fixtures in the dedicated PostgreSQL database;
- implement core, permission, audit, migration, and performance modules;
- cover every positive and negative IDS behavior assigned to PATCH-020.2.1;
- keep search, AI, later relationships, and future domains absent.

### Step 9 — Validate migration and direct integrity

- replay the full chain from zero in an isolated validation namespace;
- validate upgrade, rollback or safe recovery, and re-upgrade;
- compare model metadata with the migrated database;
- execute direct PostgreSQL rejection cases;
- prove the development fingerprint is unchanged.

### Step 10 — Run focused validation

- run the five PATCH-020.2.1 test modules;
- run direct PostgreSQL integrity cases;
- run permission and audit rollback subsets;
- run concurrency cases repeatedly;
- run syntax and formatting checks.

### Step 11 — Run complete regression

- run the complete backend suite against the isolated database at the expected
  head;
- compare results and warnings with the recorded baseline;
- resolve every new failure or unexplained warning within scope;
- repeat focused validation after any correction.

### Step 12 — Prepare Final Review evidence

- remove only generated test and language cache artifacts;
- confirm no development-data change;
- confirm only approved PATCH files changed;
- run diff integrity checks;
- report all required validation categories, warnings, issues, fingerprint,
  status, and change summary.

## Domain Implementation Order

The domain is implemented in this dependency order:

1. **Allow-lists**
   - Context kind, authority standing, relationship meaning, and lifecycle
     standing.
2. **Identity and Project scope**
   - stable Context identity and exactly one governing Project.
3. **Workspace scope**
   - optional existing Workspace whose Project and Discipline remain native.
4. **Subject Reference**
   - Project, Workspace, Discipline, and already governed native subjects.
5. **Source and Evidence Reference**
   - stable source reference, revision, applicability, access, and limitation.
6. **Qualified Fact**
   - bounded claim, subject, source support, authority, and responsibility.
7. **Qualified Engineering Value**
   - value plus every qualification required by its engineering meaning.
8. **Assumption**
   - explicit provisional human-owned basis, consequence, and later
     confirmation condition.
9. **Responsibility**
   - information owner and active engineering steward within explicit scope.
10. **Minimum relationships**
    - applies-to, scoped-by, and evidenced-by only.
11. **Lifecycle**
    - current-use and explicit withdrawal only.
12. **Optimistic concurrency**
    - expected version, exactly one successful advance, atomic conflict
      rejection.
13. **Authorization and confidentiality**
    - existing roles, participation, responsibility, and source restriction.
14. **Audit integration**
    - action-specific evidence committed atomically with material change.

Later items may depend on earlier items. Earlier items must not import behavior
from a later PATCH.

## Migration Strategy

### Additive-only rule

- create one new revision after the current committed head;
- add only structures required by accepted IDS objects and behaviors;
- do not rename, repurpose, drop, or reinterpret existing data;
- do not backfill speculative Context;
- do not alter Project or Workspace identity, lifecycle, ownership,
  assignment, membership, or uniqueness;
- do not create later-sub-patch structures;
- keep the migration chain linear;
- require explicit database connection configuration;
- prohibit application to the development database during implementation
  validation.

### Forward validation

- create an empty isolated validation namespace;
- apply the complete migration chain from zero;
- verify the new head is current;
- verify model metadata and migrated state agree;
- verify existing Project and Workspace data remains readable and unchanged;
- verify a database already at the Workspace Core head upgrades without
  destructive change;
- reapply after rollback or recovery validation;
- confirm no model-driven state creation is used.

### Rollback and recovery validation

The preferred proof is a downgrade to the immediate prior head followed by
re-upgrade, performed only in the isolated database.

If an exact downgrade cannot safely preserve data created under the new
foundation, recovery proof shall instead:

- capture a validated isolated backup before transition;
- apply the forward transition;
- restore the backup into a separate isolated namespace;
- confirm the prior head, row counts, and core fingerprint;
- record why downgrade was not the safe recovery mechanism.

In either case:

- prior Project and Workspace behavior must remain intact;
- failure must not reach the development database;
- no manual-only hidden state change is permitted;
- recovery evidence must be reproducible.

### Compatibility validation

- validate an empty database from zero;
- validate a database at the current Workspace Core head;
- preserve existing Project and Workspace rows;
- preserve authentication, CRM, Project, Workspace, audit, and existing search
  behavior;
- preserve the existing two-role model;
- verify no Context row is created merely because a Project or Workspace
  exists;
- verify Workspace archival does not destructively remove Context.

## Validation Strategy

Validation uses layered evidence:

1. enum and domain validation;
2. repository-level scoping and concurrency;
3. service-level authorization, confidentiality, atomic audit, and safe
   failure;
4. direct PostgreSQL integrity rejection;
5. migration replay, rollback or recovery, and compatibility;
6. focused PATCH-020.2.1 suite;
7. complete backend regression;
8. performance and security checks;
9. protected development-database fingerprint comparison;
10. syntax, formatting, cache, and diff integrity.

Every failure is investigated. Assertions are not weakened to obtain a pass.
A genuine defect is fixed only when it is within the accepted IDS; otherwise,
implementation stops for governance.

## Regression Strategy

### Baseline

Before implementation:

- run the complete backend suite in the isolated database at the current
  Workspace Core head;
- record total passed, skipped, failed, and warnings;
- record Python and PostgreSQL versions;
- record the migration head and dataset state;
- preserve the results in implementation evidence.

### During implementation

- run the affected focused module after each domain layer;
- run Workspace Core, Project, permission, audit, and migration regression
  after persistence, authorization, concurrency, or audit changes;
- repeat the complete focused suite after each material correction.

### Final regression

- migrate the isolated database to the new expected head;
- run the entire backend suite;
- compare against the baseline;
- permit no new failure;
- investigate and report every new warning;
- rerun the focused suite after any regression correction;
- confirm existing interface behavior and response contracts remain unchanged.

## Required Datasets

### Functional dataset

The deterministic functional dataset shall include:

- two Customers;
- three active Projects with distinct owners and primary assignees;
- one blocked-lifecycle Project;
- six Workspaces across at least three Disciplines;
- one archived Workspace;
- active and inactive Users covering every permission persona;
- Project owners and primary assignees;
- Workspace owners, primary assignees, and collaborators;
- designated information owners and engineering stewards;
- unrelated engineers and one administrator;
- native Project, Workspace, and Discipline subjects;
- authorized and restricted source references;
- each allowed Context kind;
- current and withdrawn Context;
- valid and stale versions.

### Direct-integrity dataset

The isolated direct PostgreSQL dataset shall exercise:

- valid baseline Context;
- unsupported Context kind;
- missing or invalid governing Project;
- Workspace and Project mismatch;
- invalid or missing required responsibility;
- invalid authority standing;
- invalid lifecycle standing;
- non-positive version;
- duplicate stable identity;
- unsupported relationship meaning;
- invalid or cross-Project subject reference;
- invalid or inaccessible source linkage where database enforcement applies.

### Concurrency dataset

The concurrency dataset shall support:

- two independent transactions reading the same version;
- one winning material change;
- one stale losing change;
- audit counts before, during, and after conflict;
- retry with the refreshed version.

### Performance dataset

The approved representative isolated dataset shall contain:

- 3 Projects;
- 6 Workspaces;
- 25 Users across all permission categories;
- 10,000 Context elements;
- all allowed kinds with no kind below 5 percent of the total;
- 60 percent Project-scoped and 40 percent Workspace-scoped Context;
- an average of 2 subject references per element;
- an average of 1.5 source references per source-supported element;
- 10 percent restricted-source Context;
- 10 percent withdrawn Context;
- one Project containing at least 5,000 Context elements;
- one Workspace containing at least 2,000 Context elements.

The dataset is synthetic, deterministic, and contains no production or
development data.

## Required Test Categories

### Core domain

- every allowed Context kind;
- rejection of unsupported kinds;
- stable identity;
- Project and Workspace scope;
- Workspace-to-Project consistency;
- native subject identity;
- no Project or Workspace duplication;
- Qualified Fact;
- Qualified Engineering Value qualifications;
- Assumption distinction and ownership;
- source reference traceability;
- minimum relationship allow-list;
- current-use and withdrawal behavior.

### Permissions and confidentiality

- administrator;
- Project owner;
- Project primary assignee;
- Workspace owner;
- Workspace primary assignee;
- Workspace collaborator;
- information owner;
- engineering steward;
- unrelated engineer;
- inactive or missing responsible User;
- restricted source;
- cross-Project denial;
- cross-Workspace traversal denial;
- non-disclosing not-found and forbidden behavior.

### Authority

- accepted bounded standing;
- insufficient evidence rejection;
- unsupported verified standing rejection;
- no promotion through owner, steward, role, recency, repetition, or
  confidence;
- Assumption cannot become fact through ordinary update;
- administrator is not technical authority.

### Concurrency

- expected-version success;
- stale-version atomic rejection;
- exactly one version advance;
- no partial relationship or responsibility change;
- deterministic two-transaction conflict;
- successful retry from refreshed state.

### Audit and rollback

- creation;
- material value change;
- source-link change;
- owner change;
- steward change;
- authority-standing change;
- withdrawal;
- authorized restoration to current use;
- action-specific before and after evidence;
- no success audit for every invalid, unauthorized, or conflicted attempt;
- Context and audit atomicity when audit creation fails.

### Migration and direct PostgreSQL integrity

- linear head;
- full replay from zero;
- current-head upgrade;
- rollback or recovery;
- re-upgrade;
- metadata agreement;
- direct rejection of every approved integrity violation;
- no implicit Context creation;
- existing Project and Workspace preservation;
- unchanged development fingerprint.

### Compatibility and regression

- Project Core;
- Workspace Core;
- Workspace permissions;
- Workspace audit;
- Workspace migration;
- existing authentication, Customer, Contact, audit-log, and search behavior;
- complete backend suite.

### Scope exclusion

Verify absence of:

- a generic Context blob;
- a universal Engineering Context Object;
- new endpoints;
- search integration;
- Derived Context;
- Missing Information or Conflict behavior;
- history or snapshots;
- Human Review or authority promotion;
- Decision Log, Plan, Health, Knowledge Graph, or AI behavior.

## Environment Assumptions

- work occurs on the current `main` branch without rebasing;
- no dependency installation is required;
- PostgreSQL 17 remains the database engine;
- the backend container remains the execution environment;
- the dedicated database is named
  `satco_platform_patch02021_test`;
- the test bootstrap rejects every other database name;
- the database begins from the current committed migration head;
- migration commands use an explicit isolated connection;
- no implementation or validation command targets `satco_platform`;
- the development database is read only for pre- and post-validation
  fingerprinting;
- tests remain transaction-isolated and savepoint-aware;
- performance data is synthetic and created only in the isolated database;
- network access is not required;
- generated cache artifacts are removed after validation;
- staging, commit, push, tag, and deployment remain separately prohibited.

If the dedicated database or current-head baseline is unavailable, IRR returns
the plan for correction rather than permitting use of the development
database.

## Mandatory Database-Name Guard

All PATCH-020.2.1 migration and PostgreSQL-specific test commands must begin
with a live database-name assertion.

The guard behavior is:

1. connect using the exact connection configuration intended for the
   subsequent command;
2. query PostgreSQL `current_database()` read-only;
3. compare the returned value byte-for-byte with
   `satco_platform_patch02021_test`;
4. exit nonzero before the migration or test command when the value is absent,
   different, ambiguous, or unavailable;
5. execute the guarded command only after an exact match.

The canonical shell assertion is:

```bash
test "$(docker exec satco-postgres psql -U satco -d satco_platform_patch02021_test -Atc 'SELECT current_database();')" = "satco_platform_patch02021_test"
```

For commands executed inside `satco-backend`, the guard additionally opens the
same `TEST_DATABASE_URL` or `ALEMBIC_DATABASE_URL` used by the command and
asserts `current_database()` before execution. A hard-coded label, environment
variable name, URL text, or database existence check is not a substitute for
the live assertion.

No guard may accept a prefix, suffix, pattern, alternate database, empty value,
or development database. Guard failure must leave both validation and
development databases unchanged.

Readiness closure validated both outcomes:

- exact live name `satco_platform_patch02021_test`: accepted;
- non-matching development name: rejected before any guarded action.

## Exact Validation Commands

The commands below are the approved command forms for implementation
validation. Commands referencing future PATCH-020.2.1 tests are executed only
after those files and the additive migration are separately authorized and
implemented.

### Python syntax validation

```bash
docker exec satco-backend python -m compileall -q app tests migrations
```

### Focused PATCH-020.2.1 tests

```bash
docker exec -e TEST_DATABASE_URL=postgresql://satco:satco_password@postgres:5432/satco_platform_patch02021_test satco-backend sh -lc 'python -c "import os; from sqlalchemy import create_engine, text; engine = create_engine(os.environ[\"TEST_DATABASE_URL\"]); connection = engine.connect(); actual = connection.execute(text(\"SELECT current_database()\" )).scalar_one(); connection.close(); engine.dispose(); assert actual == \"satco_platform_patch02021_test\", f\"database guard rejected {actual!r}\"" && python -m pytest -q tests/test_engineering_context_core.py tests/test_engineering_context_permissions.py tests/test_engineering_context_audit.py tests/test_engineering_context_migration.py tests/test_engineering_context_performance.py'
```

### Migration tests

```bash
docker exec -e TEST_DATABASE_URL=postgresql://satco:satco_password@postgres:5432/satco_platform_patch02021_test satco-backend sh -lc 'python -c "import os; from sqlalchemy import create_engine, text; engine = create_engine(os.environ[\"TEST_DATABASE_URL\"]); connection = engine.connect(); actual = connection.execute(text(\"SELECT current_database()\" )).scalar_one(); connection.close(); engine.dispose(); assert actual == \"satco_platform_patch02021_test\", f\"database guard rejected {actual!r}\"" && python -m pytest -q tests/test_engineering_context_migration.py'
```

### Direct PostgreSQL constraint tests

```bash
docker exec -e TEST_DATABASE_URL=postgresql://satco:satco_password@postgres:5432/satco_platform_patch02021_test satco-backend sh -lc 'python -c "import os; from sqlalchemy import create_engine, text; engine = create_engine(os.environ[\"TEST_DATABASE_URL\"]); connection = engine.connect(); actual = connection.execute(text(\"SELECT current_database()\" )).scalar_one(); connection.close(); engine.dispose(); assert actual == \"satco_platform_patch02021_test\", f\"database guard rejected {actual!r}\"" && python -m pytest -q tests/test_engineering_context_migration.py -k postgresql'
```

### Authorization tests

```bash
docker exec -e TEST_DATABASE_URL=postgresql://satco:satco_password@postgres:5432/satco_platform_patch02021_test satco-backend sh -lc 'python -c "import os; from sqlalchemy import create_engine, text; engine = create_engine(os.environ[\"TEST_DATABASE_URL\"]); connection = engine.connect(); actual = connection.execute(text(\"SELECT current_database()\" )).scalar_one(); connection.close(); engine.dispose(); assert actual == \"satco_platform_patch02021_test\", f\"database guard rejected {actual!r}\"" && python -m pytest -q tests/test_engineering_context_permissions.py'
```

### Audit rollback tests

```bash
docker exec -e TEST_DATABASE_URL=postgresql://satco:satco_password@postgres:5432/satco_platform_patch02021_test satco-backend sh -lc 'python -c "import os; from sqlalchemy import create_engine, text; engine = create_engine(os.environ[\"TEST_DATABASE_URL\"]); connection = engine.connect(); actual = connection.execute(text(\"SELECT current_database()\" )).scalar_one(); connection.close(); engine.dispose(); assert actual == \"satco_platform_patch02021_test\", f\"database guard rejected {actual!r}\"" && python -m pytest -q tests/test_engineering_context_audit.py -k rollback'
```

### Concurrency tests

```bash
docker exec -e TEST_DATABASE_URL=postgresql://satco:satco_password@postgres:5432/satco_platform_patch02021_test satco-backend sh -lc 'python -c "import os; from sqlalchemy import create_engine, text; engine = create_engine(os.environ[\"TEST_DATABASE_URL\"]); connection = engine.connect(); actual = connection.execute(text(\"SELECT current_database()\" )).scalar_one(); connection.close(); engine.dispose(); assert actual == \"satco_platform_patch02021_test\", f\"database guard rejected {actual!r}\"" && python -m pytest -q tests/test_engineering_context_core.py -k concurrency'
```

### Performance tests

```bash
docker exec -e TEST_DATABASE_URL=postgresql://satco:satco_password@postgres:5432/satco_platform_patch02021_test satco-backend sh -lc 'python -c "import os; from sqlalchemy import create_engine, text; engine = create_engine(os.environ[\"TEST_DATABASE_URL\"]); connection = engine.connect(); actual = connection.execute(text(\"SELECT current_database()\" )).scalar_one(); connection.close(); engine.dispose(); assert actual == \"satco_platform_patch02021_test\", f\"database guard rejected {actual!r}\"" && python -m pytest -q tests/test_engineering_context_performance.py'
```

### Complete backend regression

```bash
docker exec -e TEST_DATABASE_URL=postgresql://satco:satco_password@postgres:5432/satco_platform_patch02021_test satco-backend sh -lc 'python -c "import os; from sqlalchemy import create_engine, text; engine = create_engine(os.environ[\"TEST_DATABASE_URL\"]); connection = engine.connect(); actual = connection.execute(text(\"SELECT current_database()\" )).scalar_one(); connection.close(); engine.dispose(); assert actual == \"satco_platform_patch02021_test\", f\"database guard rejected {actual!r}\"" && python -m pytest -q'
```

### Pre-implementation regression baseline command

The readiness baseline used the existing isolated Workspace validation schema
because the new PATCH-020.2.1 database was required to remain empty and
unmigrated:

```bash
docker exec -e PGOPTIONS=-csearch_path=patch0201_validation -e TEST_DATABASE_URL=postgresql://satco:satco_password@postgres:5432/satco_platform_patch019_test satco-backend python -m pytest -q
```

### Alembic current

```bash
docker exec -e ALEMBIC_DATABASE_URL=postgresql://satco:satco_password@postgres:5432/satco_platform_patch02021_test satco-backend sh -lc 'python -c "import os; from sqlalchemy import create_engine, text; engine = create_engine(os.environ[\"ALEMBIC_DATABASE_URL\"]); connection = engine.connect(); actual = connection.execute(text(\"SELECT current_database()\" )).scalar_one(); connection.close(); engine.dispose(); assert actual == \"satco_platform_patch02021_test\", f\"database guard rejected {actual!r}\"" && alembic current'
```

### Alembic heads

```bash
docker exec satco-backend alembic heads
```

### Alembic history

```bash
docker exec satco-backend alembic history
```

### Alembic check

```bash
docker exec -e ALEMBIC_DATABASE_URL=postgresql://satco:satco_password@postgres:5432/satco_platform_patch02021_test satco-backend sh -lc 'python -c "import os; from sqlalchemy import create_engine, text; engine = create_engine(os.environ[\"ALEMBIC_DATABASE_URL\"]); connection = engine.connect(); actual = connection.execute(text(\"SELECT current_database()\" )).scalar_one(); connection.close(); engine.dispose(); assert actual == \"satco_platform_patch02021_test\", f\"database guard rejected {actual!r}\"" && alembic check'
```

### Development fingerprint capture and comparison

Capture the canonical value without reading row contents:

```bash
docker exec satco-postgres psql -U satco -d satco_platform -Atc "SELECT 'database='||current_database()||'|revision='||COALESCE((SELECT version_num FROM alembic_version LIMIT 1),'NONE')||'|table_count='||(SELECT count(*) FROM information_schema.tables WHERE table_schema='public')||'|alembic_version='||(SELECT count(*) FROM alembic_version)||'|audit_logs='||(SELECT count(*) FROM audit_logs)||'|contacts='||(SELECT count(*) FROM contacts)||'|customers='||(SELECT count(*) FROM customers)||'|project_code_sequences='||(SELECT count(*) FROM project_code_sequences)||'|projects='||(SELECT count(*) FROM projects)||'|users='||(SELECT count(*) FROM users)||'|engineering_context_tables='||(SELECT count(*) FROM information_schema.tables WHERE table_schema='public' AND table_name LIKE 'engineering_context%');"
```

Compare the SHA-256 hash:

```bash
test "$(docker exec satco-postgres psql -U satco -d satco_platform -Atc "SELECT 'database='||current_database()||'|revision='||COALESCE((SELECT version_num FROM alembic_version LIMIT 1),'NONE')||'|table_count='||(SELECT count(*) FROM information_schema.tables WHERE table_schema='public')||'|alembic_version='||(SELECT count(*) FROM alembic_version)||'|audit_logs='||(SELECT count(*) FROM audit_logs)||'|contacts='||(SELECT count(*) FROM contacts)||'|customers='||(SELECT count(*) FROM customers)||'|project_code_sequences='||(SELECT count(*) FROM project_code_sequences)||'|projects='||(SELECT count(*) FROM projects)||'|users='||(SELECT count(*) FROM users)||'|engineering_context_tables='||(SELECT count(*) FROM information_schema.tables WHERE table_schema='public' AND table_name LIKE 'engineering_context%');" | shasum -a 256 | awk '{print $1}')" = "a5c31884adf1faa73e638311ba437d7dcf3013857fca3aa9450c00abe2640b7d"
```

## Performance Baseline

Performance is measured in the backend container against the deterministic
10,000-element dataset after one warm-up pass and at least 30 measured
iterations per operation.

Required baseline targets:

- retrieve one authorized Context element with its bounded subject,
  responsibility, and source summary: p95 no greater than 150 ms;
- retrieve a bounded page of 100 authorized Project Context elements without
  source content: p95 no greater than 300 ms;
- retrieve a bounded page of 100 authorized Workspace Context elements without
  source content: p95 no greater than 300 ms;
- perform one successful versioned material update with audit evidence: p95 no
  greater than 250 ms;
- reject one stale versioned update without success audit evidence: p95 no
  greater than 250 ms;
- no operation traverses unbounded relationship or source collections;
- authorization is applied before materialization of unauthorized Context;
- repeated retrieval produces deterministic ordering.

Record the database state, iteration count, p50, p95, maximum, and query count
for each operation. A target failure blocks Final Review. Performance changes
must not weaken authorization, traceability, engineering meaning, audit, or
concurrency.

The repeatable performance command is the guarded Performance tests command in
the Exact Validation Commands section. Its result report must include:

- environment and PostgreSQL version;
- migration head;
- deterministic dataset seed and counts;
- operation category;
- iteration count;
- p50, p95, maximum, and query count;
- target and pass or fail result;
- warnings and limitations.

Results describe only the tested container, PostgreSQL version, dataset, and
operation. They are not a universal performance claim.

## Security Verification

Verify:

- authentication is required for every Context operation;
- Context identifiers do not disclose inaccessible existence;
- Project and Workspace scope is checked before read or mutation;
- source confidentiality is checked independently;
- relationship access does not grant access to the target;
- cross-Project links are rejected;
- cross-Workspace access cannot traverse beyond the actor’s participation;
- archived Workspace Context is excluded from current operational use;
- error details contain no protected source content;
- audit details contain no unnecessary sensitive source content;
- mass assignment cannot alter identity, Project, Workspace, native subject,
  actor, version, or audit fields;
- unsupported kinds and relationship meanings fail closed;
- administrator access does not imply engineering competence.

## Authorization Verification

For each material operation, build a complete allow-and-deny matrix across:

- administrator;
- Project owner;
- Project primary assignee;
- Workspace owner;
- Workspace primary assignee;
- Workspace collaborator;
- information owner;
- designated engineering steward;
- unrelated engineer;
- inactive User;
- missing User.

Operations include:

- record preliminary Context;
- view Project Context;
- view Workspace Context;
- change a Context value;
- link or unlink an allowed subject;
- link or unlink an allowed source;
- change information owner;
- change engineering steward;
- set eligible initial authority standing;
- withdraw from current use;
- restore to current use.

Verify separately that:

- Project participation does not imply Workspace stewardship;
- Workspace participation does not grant shared Project authority;
- ownership does not imply competence;
- contribution does not imply verification;
- administrator access does not imply technical authority;
- source restriction can deny access despite Context participation.

## Audit Verification

Required success audit actions cover:

- Context recorded;
- qualified value changed;
- source linked or unlinked;
- information owner changed;
- engineering steward changed;
- eligible authority standing changed;
- Context withdrawn;
- Context restored to current use.

Each successful action records actor, Context identity, Project and Workspace
scope, affected subject, reason, before and after meaning where material,
resulting version, time, and a non-sensitive source reference where applicable.

For every rejected validation, authorization, lifecycle, source-access,
relationship, and concurrency case:

- no success audit evidence exists;
- Context meaning is unchanged;
- links and responsibility are unchanged;
- version is unchanged;
- no partial state remains.

Simulate audit creation failure and prove the Context mutation rolls back.

## Rollback Strategy

### Mutation rollback

- all material Context mutations and success audit evidence share one
  transaction boundary;
- validation and authorization complete before mutation;
- persistence or audit failure rolls back the entire action;
- stale concurrency rejection does not alter version or links;
- tests compare before and after state and audit counts.

### Migration rollback or recovery

- validate immediate downgrade and re-upgrade in the isolated database when
  safe;
- otherwise execute the documented backup-and-restore recovery proof;
- preserve existing Project and Workspace data;
- confirm the prior migration head and core fingerprint after recovery;
- never test rollback against development or production.

### Code rollback

Before commit, source rollback is the bounded removal of PATCH-020.2.1
implementation files and reversal of its explicit import changes. No unrelated
file is reverted. After commit, rollback follows separate Git and deployment
approval.

## Deliverables

Implementation deliverables are limited to:

- Core Context enum definitions;
- Core Context domain persistence;
- bounded Context exceptions;
- scoped repository behavior;
- orchestration, authorization, concurrency, and audit behavior;
- one additive migration;
- five focused test modules;
- required model and enum registrations;
- isolated migration, rollback or recovery, direct PostgreSQL, focused,
  regression, performance, security, permission, audit, fingerprint, syntax,
  and diff evidence;
- the implementation report, validation report, and final review artifacts
  required by the Development Lifecycle.

No interface endpoint, frontend, search, AI, or future-domain deliverable is
included.

## Definition of Implementation Completion

Implementation is complete only when:

- every planned file is present or an approved narrowing is recorded;
- no unapproved file is changed;
- every IDS-required domain behavior is implemented;
- only allowed Context kinds and relationship meanings exist;
- Project and Workspace boundaries are preserved;
- native objects and sources are referenced rather than duplicated;
- responsibility and authority remain independent from competence;
- qualified values retain required engineering meaning;
- lifecycle and concurrency behavior passes;
- authorization and confidentiality matrices pass;
- successful audit and failed-mutation rollback pass;
- one additive migration passes forward, rollback or recovery, re-upgrade, and
  compatibility validation;
- direct PostgreSQL integrity rejection passes;
- the five focused modules pass;
- the complete backend regression suite passes;
- performance and security targets pass;
- the development fingerprint is unchanged;
- syntax and diff integrity pass;
- generated cache artifacts are removed;
- no out-of-scope capability or implementation artifact remains;
- Final Review returns PASS before Commit.

## Exit Criteria for IRR

This plan is ready for repeated IRR when:

- the plan is approved;
- the file set and implementation order are accepted;
- model, repository, service, audit, and test extension points are confirmed;
- the dedicated PostgreSQL database is available and protected by an exact-name
  guard;
- the current migration head and linear chain are confirmed;
- the development fingerprint procedure is approved;
- the additive migration strategy is accepted;
- rollback or recovery proof is accepted;
- focused and complete regression commands are confirmed;
- the deterministic functional, concurrency, direct-integrity, and performance
  datasets are approved;
- performance targets are approved;
- security, authorization, concurrency, audit, and scope-exclusion matrices are
  accepted;
- no new dependency is required;
- no unresolved issue requires IDS, EDS, or ADR change;
- implementation ownership and reviewers are assigned;
- IRR can return **Ready for Implementation** without inventing a missing
  decision.

Until every criterion is satisfied, implementation remains unauthorized.
