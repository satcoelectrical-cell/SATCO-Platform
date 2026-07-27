# PATCH-020.2.2 Technical Review

## Review Status

Final technical review complete.

## Verdict

**FAIL**

PATCH-020.2.2 is not ready for staging. Migration mechanics, repository
hygiene, static validation, performance measurements, and complete regression
are satisfactory, but mandatory IDS behavioral evidence is absent and one
required fulfilment safeguard is not implemented.

## Reviewed Baseline

The review covered:

- accepted ADR-015;
- accepted EDS-020.2;
- accepted IDS-020.2.2;
- accepted Implementation Plan;
- the final IRR authorization;
- the operational Readiness Baseline;
- the complete approved implementation inventory;
- revision `b2022c0202f2`;
- all seven focused test modules;
- PostgreSQL migration and constraint evidence;
- deterministic performance evidence;
- complete regression evidence;
- the protected development fingerprint;
- repository and staged-state hygiene.

## Architecture, Product, and Scope Alignment

### Result

**PASS WITH IMPLEMENTATION BLOCKER**

The implementation remains within the authorized source inventory and adds no
router, schema, transport endpoint, frontend behavior, Search integration,
role, AI behavior, Derived Context, Missing Information, Conflict Engine,
Human Review implementation, Decision Log, Execution Plan, Engineering
Health, Knowledge Graph, workflow, task, notification, or schedule.

The finite relationship taxonomy, explicit endpoints, stable identities,
current-use withdrawal, Interface Commitment state vocabulary, provider and
consumer separation, optimistic version columns, and restrictive references
are directionally aligned with ADR-015, EDS-020.2, and the Product Bible's
Context-first, traceable, human-authority model.

The implementation does not create Human Review evidence, which preserves the
non-scope boundary. It does not, however, implement a way to determine when
external Human Review is mandatory, and fulfilment accepts absent
`external_review_evidence`. IDS-020.2.2 requires fulfilment to be rejected
when applicable Human Review evidence is absent. An optional evidence string
without a mandatory-review condition cannot enforce that contract.

## Domain and Lifecycle Review

### Relationship domain

The implementation provides:

- stable UUID relationship identity;
- one governing Project;
- four finite relationship meanings;
- explicit directional source and target representations;
- bounded purpose and applicability;
- creator and steward responsibility;
- current and withdrawn standing;
- reasoned withdrawal and restoration;
- positive versions and conditional updates;
- no ordinary delete surface.

### Interface Commitment domain

The implementation provides:

- stable commitment identity;
- explicit provider representations and consuming Workspace;
- required-information, intended-use, completeness, source-basis, condition,
  criticality, confidentiality, steward, and reviewer fields;
- the eight accepted states;
- current-use withdrawal distinct from state;
- supplied source and revision;
- reassessment standing;
- supersession reference;
- positive versioned mutation.

The transition map preserves provision, consumer review, and fulfilment as
different states. Focused tests do not exercise the complete permitted and
prohibited transition matrix, actor boundary for each transition, required
reason behavior, retained state through withdrawal/restoration, or prohibited
fulfilment without mandatory external review evidence.

## Authorization and Confidentiality

### Result

**FAIL**

The repository and service contain participation and confidentiality filters,
active-actor checks, provider-side actions, designated consumer-reviewer
actions, and same-Project validation on normal service creation paths.

The required focused authorization evidence is not present. The permission
module contains three tests:

- inactive actor rejection;
- a module-name equality assertion described as an administrator restriction
  test;
- absence of role-creation methods.

It does not execute the approved capability matrix for administrator, Project
owner and assignee, provider and consumer owners/assignees/collaborators,
steward, reviewer, restricted-source owner/non-owner, unrelated engineer, and
inactive User. It does not prove confidentiality denial, protected-identifier
non-disclosure, cross-Project denial, same-Project cross-Workspace least
privilege, authorization before totals/pagination/traversal, or absence of
transitive access.

The module-name assertion provides no evidence that an administrator is
denied restricted commitment visibility.

## Audit Atomicity and Rollback

### Result

**FAIL**

The service routes material operations through the centralized audit service
inside guarded exception/rollback blocks. This is a plausible atomic
implementation pattern, but the mandatory failure evidence is absent.

The audit module verifies only:

- the presence of named service methods;
- serialization of a small before/after dictionary;
- absence of a failure-audit method.

It does not force audit failure or persistence failure. It does not prove
rollback for relationship creation, commitment creation, lifecycle change,
responsibility change, supplied-information change, or reassessment change.
It does not compare domain state, version, endpoints, source state,
commitment state, and audit counts after failure. It does not verify complete
success audit evidence for all mandatory events.

## Optimistic Concurrency

### Result

**FAIL**

Repository updates use an identifier-and-expected-version predicate and
increment the version once, which is the correct basic mechanism.

The concurrency module verifies only:

- non-null model version columns;
- rejection of non-positive expected versions;
- HTTP status values of conflict exceptions.

It does not start synchronized independent transactions. It does not prove
one winner and one controlled conflict for relationship metadata, lifecycle,
provider, consumer, information provision, fulfilment, withdrawal, source
revision, or reassessment changes. It does not prove one audit event, no
stale-writer mutation, or unchanged linked Context and Workspace versions.

The measured performance conflict pair uses two sequential updates in one
session and one nested transaction. It is not a substitute for the mandated
independent-transaction concurrency validation.

## Migration and PostgreSQL Review

### Result

**PASS WITH INTEGRITY-EVIDENCE GAP**

Revision `b2022c0202f2`:

- has `c2021f0c0a01` as its immediate base;
- is the sole repository and validation-database head;
- is additive;
- creates only the two PATCH-owned tables and indexes;
- performs no existing-data backfill;
- uses restrictive native references;
- downgrades only PATCH-owned structures;
- reapplies successfully;
- matches SQLAlchemy metadata;
- leaves the protected development fingerprint unchanged.

Observed evidence:

- fresh upgrade from zero: pass;
- `current`, `heads`, `history`, and `check`: pass;
- downgrade to `c2021f0c0a01`: pass;
- PATCH table removal: pass;
- six Core Context and two Workspace tables retained: pass;
- re-upgrade: pass;
- direct rejection of invalid meaning, non-positive version, and invalid
  commitment state: pass.

The IDS additionally requires direct PostgreSQL rejection of invalid scope,
endpoint, identity, lifecycle, responsibility, and the complete required
commitment contract. The focused migration module inspects migration text and
model names but does not execute those direct rejection cases. That evidence
gap must be closed.

## Compatibility Review

### Result

**PASS**

- Core Context migration compatibility module: `12 passed`;
- PATCH-020.2.2 focused modules: `28 passed`;
- complete backend regression: `148 passed`, `0 failed`;
- application import, mapper configuration, and OpenAPI generation pass;
- no relationship endpoint was added to OpenAPI;
- downgrade retained Core Context and Workspace structures;
- development fingerprint remains byte-identical.

The approved Core Context compatibility correction derives the active guarded
database from `TEST_DATABASE_URL` and the single current head dynamically. It
retains the original Core Context schema, integrity, downgrade, and
reapplication assertions.

## Performance Review

### Result

**PASS WITH CLAIM LIMITATION**

The deterministic test uses:

- seed `202022`;
- 10,000 relationships;
- 2,500 Interface Commitments;
- five warm-ups;
- thirty measured samples;
- the approved Project, Workspace, lifecycle, state, confidentiality,
  criticality, and reassessment distributions.

All ten recorded p95 measurements pass their environment-specific limits.
The test reports p50, p95, maximum, declared query count, page size, actor,
and result.

The measurements execute direct SQLAlchemy statements and label query counts
as constants. They do not measure the service authorization/audit paths or
instrument actual query counts. The results therefore support persistence
operation performance only; they do not prove the IDS requirement that
authorization is applied before disclosure, totals, pagination, or traversal
without weakening confidentiality.

## Repository Hygiene

### Result

**PASS**

Inspection found:

- no TODO;
- no FIXME;
- no placeholder or unfinished marker;
- no debugger or breakpoint;
- no commented-out dead implementation;
- no generated Python or pytest cache;
- no `.pyc` or `.pyo`;
- no temporary implementation artifact;
- no staged file.

The performance reporter's `print` statement is required measurement output,
not debug residue.

`git diff --check` and `git diff --cached --check` pass.

## Inventory Review

All authorized implementation files are present:

- dedicated enum, model, exception, repository, and service modules;
- enum and model exports;
- migration metadata registration;
- focused test guard and model registration;
- all seven focused modules;
- exactly one additive PATCH-020.2.2 revision;
- lifecycle review documents.

The separately approved Core Context compatibility-test correction is also
present. No unauthorized production, API, schema, router, frontend, role,
Search, generic audit-infrastructure, or unrelated migration change was
found.

## Blocking Findings

1. Mandatory external Human Review evidence is not enforceable when required;
   fulfilment treats `external_review_evidence` as optional and has no
   applicable-review requirement.
2. The focused permission module does not validate the approved capability,
   confidentiality, non-disclosure, Project-isolation, or cross-Workspace
   matrix.
3. The focused audit module does not force failures or prove transactional
   rollback and audit completeness.
4. The focused concurrency module does not execute synchronized independent
   transactions or prove one-winner behavior and state/audit preservation.
5. Direct PostgreSQL rejection evidence is incomplete for invalid scope,
   endpoint, identity, lifecycle, responsibility, and commitment contracts.
6. Performance evidence bypasses service authorization and audit paths and
   does not instrument actual query counts.

These are implementation and validation defects, not repository-hygiene
issues. The review therefore made no source, migration, or test correction.

## Technical Recommendation

Return PATCH-020.2.2 to implementation and focused validation. Do not stage,
commit, or push until every blocking finding is corrected and the affected
focused, PostgreSQL, performance, and complete regression evidence is rerun.

## Defect Remediation Re-review

### Corrections verified

- Interface Commitments now record `external_review_required`.
- Fulfilment rejects missing evidence when that flag is true before any
  version, state, or audit mutation.
- Successful fulfilment retains the explicit evidence reference.
- PostgreSQL enforces required evidence for fulfilled commitments, fulfilment
  source/revision/use completeness, non-empty commitment meaning, distinct
  provider and consumer Workspaces, governed duplicate identity, active
  responsibility, and same-Project relationship/commitment scope.
- Permission tests now execute real same-Project, unrelated-user,
  cross-Project, cross-Customer, restricted-visibility, provider, consumer,
  and responsibility behavior.
- Audit tests now force creation, mutation, and persistence failures and
  compare domain and audit state.
- A synchronized independent-session metadata race proves one winner, one
  conflict, one version increment, and one mutation audit event.
- Direct PostgreSQL tests verify scope triggers and required-review evidence.
- Performance query counts are instrumented rather than declared.

### Remediation evidence

```text
focused modules: 32 passed
complete regression: 152 passed
validation audit rows after replay: 0
validation relationship rows after replay: 0
validation commitment rows after replay: 0
fresh chain: pass
downgrade to c2021f0c0a01: pass
re-upgrade to b2022c0202f2: pass
model/database parity: pass
development fingerprint: unchanged
```

### Remaining blocking evidence gaps

The remediation is material but incomplete against the explicit remediation
authorization:

1. Audit forced-failure coverage does not yet exercise every listed
   commitment mutation class: commitment creation, provider change, consumer
   change, responsibility change, provision, fulfilment, withdrawal,
   restoration, source revision, and reassessment.
2. Synchronized independent-session concurrency covers relationship metadata
   only. Relationship lifecycle and all nine required commitment race classes
   remain unexecuted.
3. The direct PostgreSQL suite proves cross-Project scope and review-evidence
   rejection but does not directly attempt every enumerated invalid lifecycle,
   endpoint, identity, provider, consumer, withdrawal, responsibility, and
   history-deletion case.
4. Performance query counts are measured, but measured operations still use
   direct SQLAlchemy statements rather than the authorized service boundary.

### Re-review verdict

**FAIL**

The external-review production defect and several database-integrity defects
are corrected, but staging remains blocked until the four evidence gaps above
are closed and the full ordered validation is repeated.
