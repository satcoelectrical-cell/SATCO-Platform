# ADR-025 — Governed Engineering Identifier Aggregate and Persistence

## Status

**Accepted.**

The original candidate was produced under explicit Human PATCH-052 Engineering
Identifier ADR design authority and passed its separately recorded fresh
independent review. Human ADR-025 Acceptance is now `PASS / ACCEPTED` and is
recorded append-only in the approval record below and its companion Human
Acceptance artifact. Acceptance changes governance status only; it does not
change any reviewed decision semantics or authorize EDS, IDS, implementation,
tests, migrations, deployment, staging, commit, or push.

## Date

2026-09-04

## Decision owner and authority

- Decision owner: Human Architecture Authority.
- Candidate design authority: **GRANTED** for PATCH-052.
- Independent ADR review authority: **GRANTED** for PATCH-052.
- Human ADR acceptance: **PASS / ACCEPTED on 2026-09-04**.

## Approval record

| Governance event | State |
|---|---|
| ADR-025 candidate | PASS / ACCEPTED-CANDIDATE / READY FOR HUMAN ADR ACCEPTANCE |
| Fresh independent ADR review | PASS; Critical/Major/Minor/Observation `0/0/0/0` |
| Human ADR-025 Acceptance | **PASS / ACCEPTED on 2026-09-04** |
| Acceptance artifact | `docs/reviews/ADR-025-Governed-Engineering-Identifier-Aggregate-and-Persistence-Human-Acceptance.md` |
| Final ADR-025 state | **ACCEPTED** |
| Downstream authority | NONE GRANTED by ADR acceptance |

## Context

The accepted Engineering Object blueprint makes an internal Object UUID the
stable aggregate identity and explicitly leaves engineering identifiers outside
that aggregate. The current repository implements Engineering Objects and the
closed `EngineeringIdentifierKind` vocabulary, but it implements no owner,
lifecycle, uniqueness, persistence, authorization, Audit, or historical-report
contract for an Engineering Identifier.

PATCH-052 needs human-facing equipment, panel, cable, feeder, loop, tag, system,
and controlled-external identifiers. A package descriptor cannot become the
authority for those records, and embedding them in Engineering Object would
contradict the accepted Object boundary and make identifier correction change
Object identity/version. A free-text package catalog or a second generic Object
store would be equally unsafe.

## Decision

SATCO shall use a separate, persistent, EKG-adjacent **Engineering Identifier
Aggregate**. It identifies exactly one Engineering Object by immutable UUID and
is governed by its own lifecycle, standing, history, authorization, Audit, and
optimistic version.

### 1. Aggregate authority and root

`EngineeringIdentifier` is the aggregate root and sole writer of identifier
state. It is not an Engineering Object child, package record, descriptor row,
Context fact, Evidence record, or graph node identity. The owning application
service and repository/UoW are the mutation authority. Packages may request an
owner operation and declare a required Core-owned kind, but cannot create,
change, approve, normalize, resolve, or disclose an Identifier independently.

The immutable aggregate identity is `identifier_id: UUID`. It never replaces,
changes, or aliases `engineering_object_id: UUID`.

### 2. Tenant, Project, Workspace, and Object ownership

Every Identifier has non-null `organization_id`, `project_id`, `workspace_id`,
and `engineering_object_id`. Those values are immutable and must equal the
referenced Engineering Object's Organization, Project, and Workspace. The
database and service boundary both enforce that coherence. Organization is the
tenant boundary; Project is the identifier namespace owner; Workspace is a
scope/coherence selector, not a second authority boundary.

An Identifier cannot be moved between Organizations, Projects, Workspaces, or
Objects. A required move is a withdrawal/supersession followed by authorized
creation in the target scope. No cascade from Project, Workspace, package, or
Object physically deletes Identifier history.

### 3. Exact durable V1 contract

The aggregate has exactly these domain fields in order:

1. `identifier_id: UUID`;
2. `engineering_object_id: UUID`;
3. `organization_id: UUID`;
4. `project_id: int` (positive);
5. `workspace_id: int` (positive);
6. `identifier_kind: EngineeringIdentifierKind`;
7. `display_value: str` (1..128 Unicode scalar values);
8. `normalized_value: str` (1..128 Unicode scalar values);
9. `normalization_algorithm_version` fixed to
   `satco_identifier_nfkc_casefold_v1`;
10. `issuing_scope_kind` in
    `project|workspace|external_authority`;
11. `issuing_scope_value: str` (1..128 characters);
12. `lifecycle` in `current|superseded|withdrawn`;
13. `authority_standing` in
    `draft|proposed|reviewed|approved|disputed|rejected`;
14. `primary_role` in `primary|alternate`;
15. `evidence_references: tuple[UUID, ...]` (0..8, unique, UUID-lexical order);
16. `version: int` (positive);
17. `predecessor_identifier_id: UUID | None`;
18. `successor_identifier_id: UUID | None`;
19. `creator_id: int` (positive);
20. `steward_id: int` (positive);
21. `reviewer_id: int | None` (positive when present);
22. `approver_id: int | None` (positive when present);
23. `created_at: aware UTC datetime`;
24. `updated_at: aware UTC datetime`;
25. `origin_package_key: PackageKey | None`;
26. `origin_project_configuration_revision: int | None` (positive); and
27. `origin_declaration_id: str | None` (1..128 dotted lower-snake identifier).

The three origin fields are all null or all non-null, immutable, tenant-
coherent, and resolve through the immutable Project configuration revision.
They are present only when the owner creates the Identifier as part of a
package-mediated Object workflow. Package configuration is provenance and
eligibility, never Identifier data authority.

### 4. Normalization and value authority

The server computes `normalized_value` from `display_value`: Unicode NFKC;
strip leading/trailing Unicode whitespace; collapse every internal Unicode-
whitespace run to one U+0020 SPACE; then Unicode default casefold. Empty output,
control characters, unassigned code points, or output over 128 scalar values
is rejected. The display value is preserved exactly after basic validity
checks; a client- or package-supplied normalized value is not authoritative.

Kind, display value, normalized value, normalization version, issuing scope,
Object/scope ownership, creator, creation time, lineage, and package origin are
immutable. Correcting any of them creates a successor. Standing, steward,
Evidence references, and current primary-role assignment may change only by an
authorized versioned owner command.

### 5. Exact cardinality

The cardinality contract is:

- Engineering Object to current Identifiers: **zero through sixteen**;
- Engineering Object to historical Identifiers: **zero through unbounded over
  time**, returned only through bounded pages;
- Identifier aggregate to Engineering Object: **exactly one for its entire
  lifetime**;
- one Identifier aggregate can never identify multiple Objects;
- one current Object can have at most one `primary` Identifier and up to
  fifteen `alternate` Identifiers;
- a Core/legacy Object may have zero current Identifiers; and
- a PATCH-052 package-origin Object must atomically finish creation with
  exactly one current primary Identifier of the descriptor-required kind.

The sixteen-current limit is an invariant at both service and database
boundaries. Creation of a seventeenth current Identifier fails without partial
mutation. Superseded and withdrawn rows do not count toward the current limit.

Primary/alternate is preference for authorized human presentation and lookup;
it does not change UUID identity or engineering authority. Atomic primary-role
reassignment locks the Object's current Identifier set, demotes the previous
primary when present, promotes exactly one current candidate, increments every
changed Identifier version, and emits one correlation-linked Audit operation.
It cannot leave a package-origin Object with no current primary. It grants no
approval standing.

### 6. Exact uniqueness

For `lifecycle=current`, the uniqueness key is:

`(organization_id, project_id, issuing_scope_kind, issuing_scope_value,
identifier_kind, normalized_value)`.

Consequences are exact:

- the same normalized value under the same kind and issuing scope cannot
  currently identify two Objects or appear twice on one Object;
- duplicate normalized values **are allowed under different identifier
  kinds**;
- duplicate normalized values **are allowed under different issuing scopes**;
- duplicate normalized values **are allowed across Projects**, including in
  the same Organization;
- duplicate normalized values **are allowed across Organizations**; and
- historical superseded/withdrawn rows may retain the same values, but only one
  row for a uniqueness key may be current.

V1 package creation uses `issuing_scope_kind=project` and the canonical decimal
Project ID as `issuing_scope_value`. Workspace and external-authority issuing
scopes require a separately exposed owner-authorized workflow; a descriptor
cannot synthesize them.

### 7. Kinds and package-defined classes

Identifier kinds/classes are Core-owned controlled vocabulary. The current
closed `EngineeringIdentifierKind` remains authoritative. A package may select
one of those kinds as required for one declared Object type. It cannot define a
new kind, normalization algorithm, uniqueness rule, authority standing, or
issuing scope through descriptor data. Adding a kind is a governed Core/ADR
change, not package configuration.

PATCH-052 uses only the existing kinds and exact Object-to-required-kind map in
Architecture-052. A package rule may report visible duplicates or missing
required kinds over authorized projections; it cannot resolve collisions or
merge Objects.

### 8. Lifecycle, standing, lineage, and retirement

Creation produces a `current` Identifier with `draft` standing. Human-governed
standing follows the closed progression used by the owner contract; approval
is never inferred from being primary, current, package-origin, or unique.

Correction/replacement creates a new current aggregate, links predecessor and
successor in one transaction, and changes the predecessor to `superseded`.
Withdrawal changes a current Identifier to `withdrawn` with rationale. Lineage
is same-Organization, same-Project, same-Workspace, same-Object, acyclic, and
one-to-zero-or-one in both directions. A successor has exactly one predecessor;
branching and merging are prohibited in V1.

Physical deletion is prohibited once created. Object retirement/withdrawal,
Project closure, Workspace lifecycle change, package disablement, Registry
standing change, or user removal does not delete or rewrite Identifier history.
The owner disables current mutation where the existing parent boundary so
requires and retains authorized historical read.

### 9. Authorization and non-disclosure

Every create/read/list/history/resolve/mutate operation first authenticates the
actor and derives active Organization. It then authorizes Project, Workspace,
referenced Object, and the Identifier operation before resolving or disclosing
values, matches, counts, conflicts, lineage, package origin, or standing.

Resolution accepts a bounded typed selector and returns only owner-authorized
Objects/Identifiers. Cross-tenant, inaccessible, ambiguous, and nonexistent
selectors use the existing protected/not-found minimization and reveal no
candidate count or conflicting value. Package enablement, Project selection,
Workspace binding, entitlement, primary role, or approval standing never grants
data access. Human review/approval separation follows the existing owner policy
and cannot be relaxed by a package.

### 10. Audit and provenance

Every successful mutation is atomic with owner history/outbox and centralized
Audit. Audit records action/outcome, `identifier_id`, Object/scope selectors,
old/new aggregate version where applicable, lifecycle/standing/role transition,
actor, correlation and causation identity, and safe rationale/reason codes.
It does not record `display_value`, `normalized_value`, raw Evidence content, or
hidden collision candidates.

For package-mediated operations Audit additionally records exact `package_key`,
`package_version`, `descriptor_digest`, `registry_digest` where execution or
drift is Registry-relative, `origin_project_configuration_revision`,
`origin_declaration_id`, applicable rule/declaration identity, and canonical
result digest. These operation facts are captured at execution time and are not
reconstructed from mutable Workspace state. Aggregate origin remains the
minimal immutable triple; Audit provenance does not duplicate into aggregate
state merely because it is required on an event.

### 11. Technical Report snapshots

An Identifier is not a new top-level Technical Report source type. When a
Report uses the accepted package-origin Engineering Object V2 canonical source,
the resolver locks/rechecks the exact Object source version and its complete
current Identifier set in the Report operation's transaction. The Object
historical basis snapshots that observed set, never a preferred-only subset and
never a live lookup at read time. Report acceptance re-authorizes and rechecks
the Object version, Identifier IDs/versions, and complete-set equality; any
change makes the draft basis stale and prevents acceptance until rebuilt.

For PATCH-052 that set contains 1..16 snapshots, exactly one `primary`, with all
items `current`, ordered by primary before alternate, then identifier kind,
normalized value, and Identifier UUID. Each snapshot contains the exact fields
and order frozen by Architecture-052, including Identifier version, lineage,
standing, Evidence handles, and nullable/coherent package origin. The Report's
canonical bytes and SHA-256 digest cover the entire array. Accepted Report
snapshots remain immutable after Identifier correction, supersession,
withdrawal, role reassignment, package upgrade, or Registry change.

Core/legacy Object V1 locators remain byte-immutable and do not gain an
Identifier array. No backfill or string matching upgrades them to V2.

### 12. Persistence and transaction consequences

Later separately authorized design requires an additive Identifier root table,
append-only/versioned history, idempotency and transactional outbox/Audit
integration, restrictive Object/scope/Evidence/actor/lineage references, current
uniqueness and one-primary indexes, and an Object-scoped concurrency guard for
the current-count/primary invariant. Repository methods do not commit; one
service/UoW owns the transaction and final authorization/version recheck.

No migration is created or numbered by this ADR. There is no legacy backfill.
Any later adoption of a legacy value requires an explicit Human-authorized
Identifier command with evidence, rationale, and Audit; it cannot claim package
origin or rewrite the Object.

## Alternatives considered

### Store identifiers on Engineering Object

Rejected because it violates the accepted aggregate boundary, couples
identifier correction to Object version/identity, and makes independent
standing/history/authorization unsafe.

### Package-owned identifier records

Rejected because package configuration and descriptors are not data authority,
would fork identity by discipline, and would prevent shared governed lookup.

### Free-text aliases or a generic parallel Object store

Rejected because neither provides governed uniqueness, lifecycle, tenant
isolation, evidence, or immutable Object identity.

### One identifier per Object

Rejected because real engineering Objects require controlled customer, vendor,
equipment, panel, tag, loop, cable, feeder, system, and external references.
The bounded 0..16 / exactly-one-object contract provides multiplicity without
unbounded report or rule projections.

## Consequences

The decision adds one bounded aggregate and future additive persistence work.
It preserves Object UUID authority, supports multiple human-facing identifiers,
provides deterministic tenant-scoped uniqueness and immutable Report meaning,
and lets packages require existing kinds without becoming data authorities.

The cost is a cross-aggregate transaction for package-origin Object creation
and primary-role reassignment, explicit concurrency enforcement, snapshot
expansion in Object Report V2, and later migration/security/performance proof.

## Compatibility and impact

- Architecture-051: unchanged; this is the separately governed owner allowed
  by its runtime-data and package-boundary rules.
- ADR-024: unchanged; trusted package identity/configuration remains separate
  from engineering data authority.
- PATCH-051 Core: unchanged; descriptors select existing kinds only.
- ADR-023/Technical Report authority: unchanged; Human acceptance remains the
  authority and V2 is an additive historical locator.
- Commercial V1 roadmap: unchanged; no PATCH-053+ behavior is introduced.

## Human-authority boundary

Human ADR-025 Acceptance has moved this ADR from accepted-candidate to
Accepted. Acceptance grants no automatic Identifier review/approval, engineering
acceptance, Object merge, collision resolution, Report acceptance, Memory
admission, package registration, implementation, migration, or deployment
authority. AI and deterministic rules remain advisory/validation mechanisms
inside explicit owner operations.

## Acceptance gate and exact next decision

The fresh independent review reported Critical/Major/Minor `0/0/0`. Human
ADR-025 Acceptance subsequently recorded `PASS / ACCEPTED`. ADR-025 is now the
accepted Engineering Identifier basis for registered PATCH-052.

Acceptance grants no downstream design or implementation authority. The next
possible governed action is a separate Human decision on EDS-052 design
authority; EDS-052 remains not started and not authorized.
