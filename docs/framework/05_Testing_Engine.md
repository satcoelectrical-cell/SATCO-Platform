# SATCO Implementation Framework v1.1 — Testing Engine

## 1. Purpose

The Testing Engine maps PATCH risks and contracts to mandatory automated and
review evidence.

## 2. Test Pyramid

### Contract and Unit

- controlled enum vocabulary and namespace collisions;
- strict Pydantic v2 schemas, `ConfigDict`, extra-field rejection;
- Aggregate commands, invariants, lifecycle/authority matrices, no-ops;
- stable exceptions and error codes;
- pure policy and mapping behavior.

### Persistence and Application

- complete rehydration and scope queries;
- create and expected-version compare-and-change;
- duplicate/cycle/reference rules;
- authorization ordering and protected-not-found;
- service orchestration with exactly one aggregate command;
- deterministic authorized response mapping.

### Integration

- real PostgreSQL constraints and model/schema agreement;
- atomic Unit of Work rollback and commit;
- Audit/outbox/idempotency rows;
- concurrent stale writes and uniqueness races;
- authentication and trusted Organization context;
- derived visibility across all required constituents.

### API

- every approved route and HTTP method;
- request headers, body/query/path validation;
- filtering, pagination, bounded traversal, stable errors;
- authentication, authorization, disclosure protection;
- proof prohibited PUT/PATCH/DELETE/bulk/unbounded routes do not exist.

### Regression

- active PATCH suite;
- prerequisite PATCH suites;
- adjacent domain and shared-contract suites;
- authentication/security suite;
- complete backend or affected product suite.

## 3. Mandatory Risk Coverage

When applicable, test:

- happy path and every prohibited transition;
- boundary values and malformed values;
- missing, inactive, disabled, inaccessible, wrong-Organization, wrong-Project,
  and wrong-Workspace references;
- self-link, duplicate, reciprocal/direction, and cycle policies;
- empty and excessive Evidence;
- exact replay and conflicting idempotency key;
- current and stale expected version;
- each transaction failure point;
- pagination limits, traversal depth/result caps, and cycle safety;
- absence of protected counts and metadata.

## 4. Test Quality Rules

- Assert behavior and durable outcomes, not only source text.
- Structural tests may supplement but never replace behavioral tests for
  security, transaction, concurrency, or migration guarantees.
- Use approved real PostgreSQL for database behavior.
- Tests must be deterministic, isolated, repeatable, and clean up disposable
  resources.
- No production database, implicit `create_all`, or unapproved database name.
- Existing tests may not be deleted, skipped, broadened, or weakened to pass a
  new PATCH without explicit authorization.

## 5. Fixtures and Data

Fixtures must create only valid governed states unless a test explicitly proves
rejection. Trusted actor and Organization context are constructed through the
approved authentication boundary or faithful test adapters, never from the API
payload under test.

## 6. Concurrency Testing

Use independent transactions/sessions. Prove one compare-and-change succeeds,
stale contenders receive the stable version conflict, the successful mutation
increments once, and losing transactions leave no Audit/outbox/idempotency
side effects.

## 7. Security Testing

For reads, lists, totals, traversal, and mutations prove authorization occurs
before disclosure. Test same-scope access and deny-by-default isolation across
Organization, Project, Workspace, membership state, lifecycle, and visibility
constituents. `allowed_actions` must not grant permission.

## 8. Regression Acceptance

Full regression must report zero failures. Known pre-existing failures require
documented evidence and governance disposition; they cannot be silently
accepted for DONE. Warnings are reported and classified but are blocking only
when security, correctness, compatibility, or governing standards require it.

## 9. Test Completion Evidence

The final report records each suite, exact pass/fail/skip count, environment,
database revision where relevant, and remaining warnings or blockers.
