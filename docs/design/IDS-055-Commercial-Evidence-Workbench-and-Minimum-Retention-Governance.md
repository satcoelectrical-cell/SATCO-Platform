# IDS-055 — Commercial Evidence Workbench & Minimum Retention Governance

## 1. Control, authority, and stop boundary

| Field | Value |
|---|---|
| Date | 2026-09-14 |
| PATCH | PATCH-055 — Commercial Evidence Workbench & Minimum Retention Governance |
| Discovery | HUMAN ACCEPTED / COMPLETE |
| ADR-028 | HUMAN ACCEPTED / AUTHORITATIVE |
| EDS-055 | HUMAN ACCEPTED / AUTHORITATIVE |
| IDS-055 design authority | GRANTED by explicit Human continuation |
| IDS-055 candidate | DRAFT / UNDER INDEPENDENT REVIEW |
| Implementation Plan / implementation | NOT STARTED / NOT AUTHORIZED |
| Migration creation/execution | NOT AUTHORIZED |
| Stage / commit / push | NOT AUTHORIZED |
| PATCH-056+ | NOT STARTED / NOT AUTHORIZED |

This IDS freezes repository-specific implementation design only.

Precedence:

Discovery -> ADR-028 -> EDS-055 -> IDS-055

It may select physical names, DTOs, routes, tables, transactions, tests, and
frontend seams, but it cannot change accepted product semantics.

## 2. Preserved canonical owners

Evidence remains the owner of engineering meaning, engineering lifecycle,
source standing, and lineage.

Supporting File remains the owner of secure intake, quarantine/scanning,
object identity, and current file availability.

Technical Report remains the owner of Human-accepted immutable conclusions
and exact historical Evidence / Supporting File provenance.

Organizational Memory remains the owner of deliberate Human admission of
accepted Technical Report knowledge.

PATCH-055 Minimum Retention Governance owns only:

- retention policy heads;
- retention basis and effective retention requirement;
- Human/governed holds;
- deterministic disposition eligibility;
- Human disposition decisions;
- governed export records;
- governed recovery records.

Retention Governance MUST NOT become a second Evidence lifecycle.

The existing Supporting File scan `disposition` field MUST NOT be reused or
overloaded for retention disposition semantics.


## 3. Repository seams to reuse

The implementation MUST reuse existing SATCO owners and seams rather than
create parallel authorities.

| Concern | Required repository seam |
|---|---|
| Evidence aggregate/API | existing Evidence models, repository, service, router, lifecycle and expected-version transitions |
| Supporting File pipeline | existing secure upload, quarantine, scanner, object-store and exact-key access contracts |
| Technical Report reliance | existing Evidence-source adapter, Report provenance and immutable accepted snapshot |
| Organizational Memory | existing Human admission from accepted Report only |
| Tenant/auth | selected active Organization context plus Project/Workspace authorization |
| Audit | existing append-only Audit infrastructure |
| Frontend | centralized API client/types plus existing Projects/Report composition patterns |

PATCH-055 MUST NOT bypass these seams merely to simplify retention workflow.

The existing Evidence API already supplies canonical create, read, list,
lifecycle-transition and Supporting-File-link behavior.

The commercial Workbench composes and exposes those operations; it does not
replace their domain authority.

## 4. Closed implementation vocabularies

Persistence uses VARCHAR plus explicit CHECK constraints. PostgreSQL native enum
types MUST NOT be introduced for PATCH-055.

Exact values:

- `RetentionSubjectKind`: `evidence`, `supporting_file`
- `RetentionMode`: `retain_until`, `retain_indefinitely`
- `RetentionPolicySource`: `platform_default`, `organization_default`,
  `human_subject_override`
- `HoldStatus`: `active`, `released`
- `DispositionEligibility`: `not_eligible`, `eligible`, `blocked_by_hold`,
  `indeterminate`
- `DispositionDecision`: `none`, `retain`, `approve_disposition`
- `RecoveryStatus`: `not_required`, `available`, `temporarily_unavailable`,
  `recovered`, `unrecoverable`
- `ExportStatus`: `requested`, `completed`, `failed`

The existing Supporting File scanner vocabulary remains separate and unchanged.

`disposition` on Supporting File means scanner disposition only.

Retention implementation uses the explicit names
`disposition_eligibility` and `disposition_decision`.

## 5. RetentionSubject physical representation

`RetentionSubjectV1` is the sole PATCH-055 subject identity:

- `subject_kind`
- `subject_id`
- `organization_id`
- `project_id`
- optional `workspace_id`

`subject_id` is the canonical UUID of either Evidence or Supporting File.

The implementation MUST resolve and authorize the canonical owner before a
RetentionSubject can be persisted.

A subject row MUST NOT become an authorization substitute.

The tuple:

`organization_id + subject_kind + subject_id`

is the canonical retention-subject key.

Project and Workspace columns are retained as denormalized scope guards and MUST
be validated against the canonical Evidence or Supporting File owner.

Evidence retention never implicitly creates Supporting File retention.

Supporting File retention never changes Evidence lifecycle or source standing.

## 6. Physical persistence topology

PATCH-055 requires additive retention persistence.

The IDS selects exactly these new logical tables:

1. `retention_records`
2. `retention_holds`
3. `retention_disposition_decisions`
4. `retention_exports`
5. `retention_export_subjects`
6. `retention_recoveries`
7. `retention_idempotency`
8. `retention_outbox`

Existing Evidence, Supporting File, Technical Report, Organizational Memory and
Audit tables are reused and MUST NOT be duplicated.

One additive PATCH-055 migration is preferred unless implementation planning
proves that a safe deployable intermediate compatibility boundary requires a
split.

No migration revision ID is allocated by this IDS.


## 7. retention_records contract

`retention_records` stores the versioned effective retention requirement for
one canonical RetentionSubject.

Required columns:

- `id` UUID primary key
- `organization_id` UUID not null
- `project_id` UUID not null
- `workspace_id` UUID nullable
- `subject_kind` VARCHAR not null
- `subject_id` UUID not null
- `version` integer not null
- `is_current` boolean not null
- `mode` VARCHAR not null
- `retain_until` timestamptz nullable
- `policy_source` VARCHAR not null
- `basis_code` VARCHAR not null
- `rationale` text nullable
- `created_by_user_id` UUID not null
- `created_at` timestamptz not null
- `supersedes_id` UUID nullable
- `request_digest` VARCHAR not null

Constraints:

- `version >= 1`
- `retain_until` is required only for `retain_until`
- `retain_until` MUST be null for `retain_indefinitely`
- `supersedes_id` references a prior record for the same subject
- a partial unique index permits only one `is_current = true` row per canonical
  retention-subject key
- `(organization_id, subject_kind, subject_id, version)` is unique

History is append-only. Updating an effective retention requirement creates a
new version and closes the previous current head in the same transaction.

The platform default resolves to:

`platform_default + retain_indefinitely`

when no valid higher-precedence policy exists.

Effective precedence is:

`human_subject_override > organization_default > platform_default`

Ambiguous, invalid, or conflicting policy resolution MUST fail safe toward
retention and MUST NOT produce disposition eligibility.

## 8. retention_holds contract

`retention_holds` is append-preserving Human/governed hold history.

Required columns:

- `id` UUID primary key
- canonical RetentionSubject scope fields
- `status` VARCHAR not null
- `reason` text not null
- `placed_by_user_id` UUID not null
- `placed_at` timestamptz not null
- `released_by_user_id` UUID nullable
- `released_at` timestamptz nullable
- `release_reason` text nullable
- `version` integer not null

An active hold MUST have no release actor/time.

A released hold MUST retain the original placement facts plus release facts.

Hold release never performs disposition and never changes Evidence standing.

A subject is blocked when at least one authorized current hold is active.

## 9. retention_disposition_decisions contract

`retention_disposition_decisions` records Human disposition decisions only.

Required columns:

- `id` UUID primary key
- canonical RetentionSubject scope fields
- `retention_record_id` UUID not null
- `eligibility_snapshot` VARCHAR not null
- `decision` VARCHAR not null
- `reason` text not null
- `decided_by_user_id` UUID not null
- `decided_at` timestamptz not null
- `subject_version_snapshot` integer not null
- `request_digest` VARCHAR not null

`approve_disposition` means a governed Human decision against an eligible
snapshot. It DOES NOT delete bytes and DOES NOT authorize automatic purge.

A stale retention head, new hold, scope change, or failed authorization makes a
previous eligibility snapshot non-actionable.


## 10. Deterministic disposition eligibility

Disposition eligibility is a derived fact and MUST NOT be stored as an
independent source of truth.

The service evaluates the authorized current RetentionSubject state in this
order:

1. unresolved or unauthorized subject -> protected failure, not eligibility
2. missing, invalid or ambiguous retention basis -> `indeterminate`
3. active hold -> `blocked_by_hold`
4. `retain_indefinitely` -> `not_eligible`
5. `retain_until` with current time before `retain_until` -> `not_eligible`
6. `retain_until` at or after `retain_until`, with no active hold -> `eligible`

`eligible` MUST NOT:

- delete or purge bytes
- withdraw Evidence
- supersede Evidence
- revoke Supporting File access
- alter Technical Report provenance
- alter Organizational Memory
- create an automatic disposition command

Eligibility MUST be recomputed at the authority-relevant transaction boundary.

## 11. Governed export persistence

`retention_exports` records one governed export operation.

Required columns:

- `id` UUID primary key
- `organization_id` UUID not null
- `project_id` UUID not null
- `workspace_id` UUID nullable
- `requested_by_user_id` UUID not null
- `purpose` text not null
- `status` VARCHAR not null
- `format` VARCHAR not null
- `requested_at` timestamptz not null
- `completed_at` timestamptz nullable
- `aggregate_digest` VARCHAR nullable
- `byte_count` bigint nullable
- `failure_code` VARCHAR nullable
- `request_digest` VARCHAR not null

`retention_export_subjects` binds each export to exact authorized subjects.

Required subject binding includes:

- `export_id`
- canonical RetentionSubject identity
- exact subject version where versioned
- exact provenance/content digest when available
- deterministic ordinal

One export accepts at most 32 requested subjects and at most 64 aggregate
metadata entries, as frozen by EDS-055.

Export MUST reauthorize current access before protected content is read.

A completed export records what SATCO exported and its provenance.

SATCO does not claim continuing governance or control over a copy after that
copy leaves the governed platform boundary.

Export MUST NOT mutate Evidence lifecycle, source standing, retention state,
hold state, Technical Report provenance or Organizational Memory.

## 12. Governed recovery persistence

`retention_recoveries` records recovery of one retained historical subject.

Required columns:

- `id` UUID primary key
- canonical RetentionSubject scope fields
- `requested_by_user_id` UUID not null
- `status` VARCHAR not null
- `requested_at` timestamptz not null
- `completed_at` timestamptz nullable
- `expected_digest` VARCHAR nullable
- `verified_digest` VARCHAR nullable
- `failure_code` VARCHAR nullable
- `request_digest` VARCHAR not null

A recovery request contains exactly one subject.

Recovery processing MUST:

1. authorize the caller and canonical subject
2. resolve the retained historical identity
3. verify current content-access rights
4. resolve or restore the protected byte/handle when recoverable
5. verify integrity against historical identity/digest where available
6. record terminal recovery state

Recovery restores availability only.

Recovery MUST NOT make withdrawn or superseded Evidence current.

Recovery MUST NOT rewrite accepted Technical Report or Organizational Memory
provenance.

If protected bytes cannot be restored, safe historical metadata and digests
remain valid provenance and recovery ends as `temporarily_unavailable` or
`unrecoverable`.


## 13. Authorization and protected-disclosure contract

Every protected PATCH-055 operation MUST authorize before:

- canonical subject lookup disclosure
- existence or count disclosure
- validation that can act as an identifier oracle
- idempotency replay
- retention-state disclosure
- hold-state disclosure
- export content resolution
- recovery content resolution

Organization scope is server-derived from the authenticated active context.

Client-supplied Organization identity MUST NOT grant or widen authority.

Project and optional Workspace scope MUST be coherent with the canonical
Evidence or Supporting File owner.

Wrong-Organization, forbidden and protected-absent subjects collapse to the
existing protected-not-found convention where repository policy requires
non-disclosure.

Retention state, historical reliance and provenance MUST NOT grant content
access by themselves.

## 14. Concurrency contract

Authority-relevant mutations require an expected version or equivalent current
state token.

This includes:

- retention-head replacement
- hold placement
- hold release
- disposition decision
- export request creation
- recovery request creation

For retention-head replacement, one concurrent writer wins.

A stale writer receives `conflict`, rereads current state and may retry only
through a new explicit request.

Mutation retry attempts are bounded to 3.

A transaction MUST NOT silently merge conflicting Human decisions.

## 15. Idempotency contract

`retention_idempotency` stores safe replay metadata for mutation operations.

The canonical idempotency scope is:

`organization_id + actor_user_id + operation + idempotency_key`

The persisted request digest MUST bind all authority-relevant request fields.

Idempotency lookup occurs only after authentication and authorization sufficient
to establish the protected operation scope.

Same key plus same digest returns the prior safe logical result.

Same key plus different digest returns `conflict`.

An idempotency replay MUST NOT disclose a protected result to a caller who no
longer has current authority.

## 16. Unit-of-work and transaction boundaries

Retention policy replacement is one transaction:

1. authorize subject
2. lock/read current retention head
3. verify expected version
4. resolve policy basis
5. close previous head
6. insert new current head
7. recompute eligibility
8. append audit/outbox metadata
9. persist idempotency result
10. commit

Hold placement/release and disposition decisions follow the same ordering:
authorization -> current-state verification -> mutation -> derived-state
recalculation -> audit/outbox -> idempotency -> commit.

No domain event or success response may be published before durable commit.

Export and recovery request creation persist governed request state atomically.

Protected byte streaming or restoration MAY occur after request commit, but its
terminal status transition MUST be a separately atomic authorized transaction.

## 17. Audit and transactional outbox

`retention_outbox` carries safe metadata only.

PATCH-055 event families are:

- retention policy applied/replaced
- retention hold placed/released
- disposition eligibility changed
- disposition decision recorded
- export requested/completed/failed
- recovery requested/completed/unavailable

Audit/outbox payloads MUST NOT contain:

- protected file bytes
- object-store credentials or storage keys
- secrets or tokens
- unrestricted user-supplied document content

Events identify canonical subject, safe scope, actor, operation, version/digest
and timestamp sufficient for attributable governance.


## 18. HTTP API composition

PATCH-055 extends the existing `/api/v1` surface.

Existing Evidence create/read/list/lifecycle/link routes remain authoritative
and MUST be reused by the Workbench.

New PATCH-055 routes are:

### Workbench

`GET /api/v1/projects/{project_id}/evidence-workbench`

Returns one authorized composition containing:

- Evidence summary page
- scanner-cleared Supporting File candidates
- lifecycle/lineage summary
- current retention summary when established
- active-hold summary
- disposition eligibility
- safe Technical Report reliance summary

Query parameters:

- optional `workspace_id`
- `limit`, default 20, maximum 100
- opaque pagination cursor where required by existing repository convention

The response MUST NOT require raw UUID entry by an ordinary user.

### Retention state

`GET /api/v1/retention/{subject_kind}/{subject_id}`

Returns:

- canonical authorized subject summary
- retention state or `not_established`
- current retention version
- policy source/basis
- hold summary
- computed disposition eligibility
- latest Human disposition decision when authorized

### Apply or replace retention basis

`POST /api/v1/retention/{subject_kind}/{subject_id}/policy`

Request:

- `retention_mode`
- optional `retain_until`
- `policy_source`
- `basis_code`
- optional bounded `rationale`
- `expected_version`
- `idempotency_key`

The server derives Organization/Project/Workspace scope.

### Place hold

`POST /api/v1/retention/{subject_kind}/{subject_id}/holds`

Request:

- `reason`
- `expected_version`
- `idempotency_key`

At most one active hold exists per subject.

### Release hold

`POST /api/v1/retention/{subject_kind}/{subject_id}/holds/{hold_id}/release`

Request:

- `release_reason`
- `expected_version`
- `idempotency_key`

Release MUST NOT imply disposition.

### Record disposition decision

`POST /api/v1/retention/{subject_kind}/{subject_id}/disposition-decisions`

Request:

- `decision`
- `reason`
- `retention_record_id`
- `subject_version_snapshot`
- `expected_version`
- `idempotency_key`

`approve_disposition` is accepted only against currently recomputed `eligible`
state.

No route in PATCH-055 performs physical purge.

## 19. Export API

`POST /api/v1/retention-exports`

Request:

- authorized project context
- optional workspace context
- `purpose`
- `format`
- 1..32 authorized subject handles
- `idempotency_key`

Response returns an opaque `export_id` and governed status.

`GET /api/v1/retention-exports/{export_id}` returns safe authorized status and
metadata.

A separate protected download capability MAY be bound to a completed export
using the repository's existing authorized-download pattern.

The download route MUST reauthorize current access and MUST NOT expose an
object-store key.

## 20. Recovery API

`POST /api/v1/retention-recoveries`

Request:

- exactly one authorized subject handle
- `idempotency_key`

Response returns opaque `recovery_id` and governed status.

`GET /api/v1/retention-recoveries/{recovery_id}` returns authorized recovery
status only.

No recovery endpoint accepts an arbitrary storage locator, filesystem path or
object-store key.

## 21. Transport outcomes

PATCH-055 public logical outcomes are exactly:

- `success`
- `invalid_request`
- `protected_not_found`
- `conflict`
- `not_permitted`
- `unavailable`
- `indeterminate`

HTTP status mapping follows existing SATCO API conventions.

Protected absence and forbidden identity MUST NOT be separated when doing so
would create an existence oracle.

`conflict` covers stale expected version and idempotency digest mismatch.

`unavailable` covers currently inaccessible protected content where existence
may safely be acknowledged.

`indeterminate` is used when retention/disposition truth cannot safely be
computed and MUST fail toward retention.


## 22. Frontend Evidence Workbench contract

PATCH-055 provides one coherent ordinary-user Evidence Workbench within the
authorized Project/Workspace experience.

The Workbench MUST compose:

1. Supporting File intake and scanner status
2. scanner-cleared file selection
3. proposed Evidence creation
4. Supporting File linkage
5. Evidence review and lifecycle transition
6. lineage/replacement presentation
7. Technical Report reliance presentation
8. retention state and policy basis
9. active hold placement/release
10. disposition eligibility and Human decision
11. governed export status/action
12. governed recovery status/action

The UI MUST explicitly distinguish:

- scanner `available` from engineering-approved Evidence
- Evidence `current` from historical Report reliance
- `eligible` from deletion/disposition execution
- recovery availability from Evidence currentness
- retention governance from engineering lifecycle

Ordinary workflows MUST use authorized selectors and opaque handles.

The UI MUST NOT require users to type:

- Evidence UUIDs
- Supporting File UUIDs
- retention record UUIDs
- storage keys
- arbitrary recovery locators

Technical identifiers may be shown only where operationally justified and MUST
be visually isolated from RTL human-readable content.

## 23. Frontend state and failure behavior

The Workbench MUST render explicit states for:

- loading
- empty
- scanner quarantine/pending
- scanner rejected/unsafe
- retention `not_established`
- active hold
- stale conflict
- protected-not-found
- not permitted
- unavailable content
- indeterminate eligibility
- recovery pending/completed/unavailable
- export requested/completed/failed

A conflict response MUST trigger a fresh authorized reread before the user can
submit another authority-relevant decision.

The frontend MUST NOT infer successful retention, hold, disposition, export or
recovery state from optimistic local state alone.

Accessibility requirements include keyboard operability, visible focus,
semantic labels, appropriate live-region announcements and responsive behavior.

RTL presentation is required for Persian human-readable content.

## 24. Migration design

PATCH-055 requires durable persistence for retention heads, holds, Human
disposition decisions, exports, recoveries, idempotency and transactional
outbox records.

Therefore an additive database migration is REQUIRED during implementation.

The migration MUST:

- create only PATCH-055 additive persistence
- preserve all existing Evidence and Supporting File rows
- preserve accepted Technical Report snapshots
- preserve Organizational Memory
- avoid destructive column/table rewrites
- add indexes and constraints required by this IDS
- maintain one Alembic head
- support fresh-install migration from base to new head
- support upgrade from the pre-PATCH-055 head
- support governed downgrade/forward-repair qualification according to SATCO
  migration policy

This IDS does not allocate the Alembic revision identifier and does not
authorize migration creation or execution.

## 25. Legacy subject semantics

Existing Evidence and Supporting File subjects MUST NOT receive fabricated
retention history during migration.

For a legacy subject with no retention record, transport/UI state is:

`not_established`

When an authorized retention decision is first required, the service may
materialize the deterministic effective default:

`platform_default + retain_indefinitely`

through the normal governed retention transaction.

That creation is attributable and auditable; it is not migration backfill.

No legacy accepted Technical Report or Organizational Memory provenance may be
rewritten merely to establish retention governance.

## 26. Historical recovery qualification

PATCH-055 implementation qualification MUST prove:

- pre-PATCH-055 schema upgrades without data loss
- existing Evidence remains readable under current authorization
- existing Supporting File provenance remains resolvable
- accepted Technical Report historical Evidence/File references remain intact
- Organizational Memory provenance remains intact
- legacy subjects truthfully surface `not_established`
- newly governed retention does not rewrite historical engineering standing
- recovery failure preserves safe provenance metadata
- fresh install reaches the sole intended Alembic head
- downgrade/forward-repair path does not fabricate retention decisions

Historical qualification MUST use disposable infrastructure and MUST NOT mutate
production/customer databases.


## 27. Frozen conformance manifest mapping

EDS-055 freezes exactly 48 conformance vectors.

IDS-055 preserves the exact count and semantic grouping.

### 27.1 Evidence Workbench — 10 vectors

| Vector | IDS implementation obligation |
|---|---|
| P055-EVW-01 | Authorized Project/Workspace Workbench composes Evidence and Supporting File state without raw-ID entry |
| P055-EVW-02 | Ordinary user can create proposed Evidence through governed Evidence API |
| P055-EVW-03 | Only authorized scanner-cleared Supporting Files are selectable for Evidence linkage |
| P055-EVW-04 | Supporting File linkage preserves canonical scope and does not imply engineering acceptance |
| P055-EVW-05 | Human lifecycle transition uses existing Evidence lifecycle authority and concurrency rules |
| P055-EVW-06 | Evidence lineage and replacement are rendered from canonical server-authorized relationships |
| P055-EVW-07 | Current engineering standing is visibly distinct from historical accepted Report reliance |
| P055-EVW-08 | Current Evidence can be selected for Technical Report provenance without bypassing Report acceptance |
| P055-EVW-09 | Workbench exposes retention/hold/export/recovery state without creating a second Evidence lifecycle |
| P055-EVW-10 | Protected Workbench discovery does not leak cross-Organization existence, counts or identifiers |

### 27.2 Retention governance — 8 vectors

| Vector | IDS implementation obligation |
|---|---|
| P055-RET-01 | Canonical typed RetentionSubject resolves Evidence or Supporting File under server-derived scope |
| P055-RET-02 | Exactly one current retention head exists per canonical typed subject |
| P055-RET-03 | `retain_until` validates timezone-aware required expiry and `retain_indefinitely` requires null expiry |
| P055-RET-04 | Policy precedence is Human subject override > Organization default > platform default |
| P055-RET-05 | Platform fallback is deterministically `retain_indefinitely` |
| P055-RET-06 | Legacy subject without governed state reports `not_established` and receives no fabricated migration history |
| P055-RET-07 | Retention replacement is append-preserving, versioned, attributable and stale-write protected |
| P055-RET-08 | Eligibility is deterministic and never itself performs deletion, purge, withdrawal or engineering-state mutation |

### 27.3 Hold governance — 8 vectors

| Vector | IDS implementation obligation |
|---|---|
| P055-HLD-01 | Authorized Human/governed actor can place a hold with reason and attributable metadata |
| P055-HLD-02 | At most one active hold exists per canonical typed subject |
| P055-HLD-03 | Active hold deterministically produces `blocked_by_hold` |
| P055-HLD-04 | Hold release preserves original placement history and records release authority |
| P055-HLD-05 | Hold release recomputes eligibility but does not dispose content |
| P055-HLD-06 | AI/background expiry cannot place or release a Human hold |
| P055-HLD-07 | Concurrent/stale hold mutation fails with conflict and requires reread |
| P055-HLD-08 | Hold state never changes Evidence lifecycle, source standing, Report provenance or Memory provenance |

### 27.4 Export and recovery — 8 vectors

| Vector | IDS implementation obligation |
|---|---|
| P055-XRC-01 | Export request accepts 1..32 authorized subjects and reauthorizes current protected access |
| P055-XRC-02 | Export binds exact subject/version/provenance metadata and never exposes object-store keys |
| P055-XRC-03 | Export completion records attributable digest/status while preserving all engineering and retention state |
| P055-XRC-04 | SATCO records export provenance but claims no continuing control after copy exits governed boundary |
| P055-XRC-05 | Recovery request accepts exactly one authorized canonical subject and no arbitrary locator |
| P055-XRC-06 | Recovery verifies historical identity/digest and current content-access authority |
| P055-XRC-07 | Recovery restores availability only and cannot revive withdrawn/superseded Evidence |
| P055-XRC-08 | Unrecoverable bytes preserve safe historical metadata/digests and never rewrite Report/Memory provenance |

### 27.5 Security and concurrency — 8 vectors

| Vector | IDS implementation obligation |
|---|---|
| P055-SEC-01 | Authentication/authorization precedes protected subject lookup and disclosure |
| P055-SEC-02 | Wrong-Organization, forbidden and protected-absent identity collapse to protected non-disclosure convention |
| P055-SEC-03 | Retention state or historical reliance never grants content access |
| P055-SEC-04 | Expected-version/current-state protection prevents stale authority-relevant mutation |
| P055-SEC-05 | Idempotency is scoped by Organization + actor + operation + key and binds request digest |
| P055-SEC-06 | Idempotency replay occurs only after current authorization and cannot leak a prior protected result |
| P055-SEC-07 | Mutation, audit/outbox and idempotency success state commit atomically |
| P055-SEC-08 | No PATCH-055 route or background path performs automatic physical purge |

### 27.6 UX and historical integrity — 6 vectors

| Vector | IDS implementation obligation |
|---|---|
| P055-UX-01 | Ordinary Workbench journey requires no raw UUID typing |
| P055-UX-02 | UI explicitly distinguishes scanner availability, Evidence currentness, historical reliance and disposition eligibility |
| P055-UX-03 | Conflict forces authorized reread before another authority-relevant decision |
| P055-UX-04 | Keyboard, focus, semantic labeling, live-region, responsive and RTL requirements are preserved |
| P055-UX-05 | Historical upgrade preserves Evidence/File/Report/Memory provenance and truthfully exposes legacy `not_established` retention |
| P055-UX-06 | Fresh install, upgrade and downgrade/forward-repair qualification preserve one intended Alembic head and no fabricated retention decisions |

Manifest total:

- EVW: 10
- RET: 8
- HLD: 8
- XRC: 8
- SEC: 8
- UX: 6

Total: **48 / 48**

Implementation planning may assign exact test files, fixtures and commands.

It MUST NOT change the vector count or semantic grouping without EDS-055
reapproval.

## 28. QG-M1 IDS alignment

IDS-055 was checked against the active Engineering Intelligence Manifesto.

Affected principles:

1. Engineering First — retention remains subordinate to engineering truth.
2. Capture Once — existing Evidence and Supporting File identities are reused.
3. Human Authority — Evidence acceptance, hold and disposition decisions remain Human-governed.
4. Engineering Context Is Sacred — Project/Workspace scope is preserved.
5. Evidence Before Assumption — retention and recovery operate on canonical attributable subjects.
6. Context Before Recommendation — current authorization and engineering standing precede protected action.
7. Intelligence Before Automation — eligibility is computed, but physical purge is not automated.
8. Explainability — basis, version, actor, rationale, digest and lineage are retained.
9. Provider Independence — no retention authority depends on an external AI provider.
10. Organizational Ownership — Organization isolation and server-derived scope remain mandatory.
11. Continuous Evolution — persistence is additive and preserves historical compatibility.

QG-M1 IDS result:

**PASS**

No Manifesto principle requires an exception for IDS-055.

## 29. IDS self-review

Self-review checks:

- accepted Discovery boundary preserved — PASS
- ADR-028 architecture preserved — PASS
- EDS-055 semantics preserved — PASS
- A055-OBS-01 typed RetentionSubject resolved — PASS
- A055-OBS-02 export-boundary control resolved — PASS
- scanner `disposition` collision avoided — PASS
- one-current-retention-head rule frozen — PASS
- active-hold maximum frozen — PASS
- fail-safe default frozen — PASS
- no fabricated migration backfill — PASS
- no automatic physical purge — PASS
- immutable accepted Report/Memory provenance preserved — PASS
- authorization-before-disclosure preserved — PASS
- concurrency/idempotency contract frozen — PASS
- frontend ordinary-user journey frozen — PASS
- migration necessity justified as additive persistence — PASS
- historical recovery qualification frozen — PASS
- exact 48-vector manifest preserved — PASS
- PATCH-056+ excluded — PASS

Self-review findings:

- Critical: 0
- Major: 0
- Minor: 0
- Observation: 0

IDS-055 self-review verdict:

**PASS / COMPLETE / READY FOR INDEPENDENT IDS REVIEW**

## 30. Stop boundary

IDS-055 is a design artifact only.

Completion of this IDS does NOT authorize:

- Implementation Plan
- production code modification
- test implementation
- frontend implementation
- migration creation or execution
- database mutation
- deployment
- staging
- commit
- push
- PATCH-056+

Independent IDS review and explicit Human IDS acceptance remain separate gates.


## 31. QG-4 correction addendum — normative precedence

This addendum is normative and supersedes any less-specific or conflicting wording in sections 6–29. It exists only to close the eight blocking findings from the first independent IDS review; it does not expand PATCH-055 scope or authorize implementation.

### 31.1 Retention head exact projection contract — closes P055-IDS-MAJ-01

The accepted EDS thirteen-element retention-governance head is implemented as one authoritative server-side projection named `RetentionGovernanceHeadV1`. The projection is assembled only after authorization from the current `retention_records` row plus current hold and disposition facts; it is the only DTO/service representation called a retention-governance head.

`RetentionGovernanceHeadV1` contains exactly: `retention_record_id`, typed `RetentionSubject`, `retention_mode`, `retention_until`, `policy_basis_code`, `basis_rationale`, `policy_source`, `hold_status`, optional `active_hold_id`, computed `disposition_eligibility`, current `disposition_decision`, `version`, optional `predecessor_record_id`, `created_by_user_id`, `created_at`, and `record_digest`.

The physical `retention_records` row MUST additionally persist `record_digest CHAR(64) NOT NULL`; `supersedes_id` is the physical predecessor field. `record_digest` is SHA-256 over canonical JSON of all immutable retention-row semantic fields excluding database surrogate ordering and `is_current`; lowercase hexadecimal only.

`hold_status`, `active_hold_id`, computed eligibility, and current disposition decision are authoritative projection fields derived inside the same authorized transaction/read boundary. They MUST NOT be client-authored or independently mutable columns on `retention_records`. This explicit projection satisfies the EDS head contract while preserving deterministic eligibility as a derived fact.

`retain_until` validation is exact: timezone-aware instant required for `retain_until`; after UTC normalization it MUST be greater than or equal to the authoritative transaction clock at creation/replacement. `retain_indefinitely` requires null `retain_until`.

### 31.2 Hold physical/revision contract — closes P055-IDS-MAJ-02

`retention_holds` is an append-only revision table. Required physical columns are: `row_id UUID PK`, stable logical `hold_id UUID NOT NULL`, canonical RetentionSubject scope fields, `status`, `reason_code VARCHAR(64)`, `rationale VARCHAR(2000)`, `authority_reference VARCHAR(512)`, `placed_by_user_id`, `placed_at`, optional `released_by_user_id`, `released_at`, `release_rationale VARCHAR(2000)`, `version`, optional `predecessor_row_id`, `digest CHAR(64)`, and `is_current`.

Placement creates version 1 / active. Release creates a new released revision with the same stable `hold_id`, predecessor reference to the active revision, preserved placement facts, and new release facts; the active revision is closed in the same transaction. No in-place semantic rewrite is permitted.

A partial unique index on the canonical typed subject permits at most one current row with `status='active'`. `(hold_id, version)` is unique. `digest` is canonical SHA-256 over immutable hold-revision semantic fields. `reason_code` is machine-bounded; rationale and authority reference are Human/governance context, not authorization substitutes.

### 31.3 Exact authorization predicates — closes authorization part of P055-IDS-MAJ-03

Roles are exactly existing SATCO `admin` and `engineer`; no new PATCH-055 role is introduced.

Read predicate: active User + enabled Organization membership + active Organization + canonical Organization match, then either `admin`, Project owner/primary assignee, or authorized Workspace owner/primary assignee/member for workspace-scoped subjects. Project-level reads follow the existing Project Foundation readable-scope predicate.

Evidence/Supporting File creation and ordinary Workbench actions reuse their existing authorization policies. Retention policy apply/replace, hold place/release, and disposition decision require `admin` OR Project owner OR Project primary assignee; a Workspace-only member/assignee without Project mutation authority cannot perform these governance mutations. Export/recovery request requires the read predicate plus current content-access authorization for every selected protected subject. Status reads require the same current read/content predicate as the request subject.

Authorization MUST occur before protected existence validation, idempotency lookup/replay, counts, retention details, object resolution, export bytes, or recovery bytes. Foreign/forbidden/protected-absent identities collapse to `protected_not_found`.

### 31.4 Exact HTTP/DTO/idempotency contract — closes remaining P055-IDS-MAJ-03

All mutation requests use HTTP header `Idempotency-Key: <UUID>`; body-level `idempotency_key` fields described earlier are superseded and MUST NOT be accepted. Expected-version remains in the request DTO where applicable.

Exact DTO names: `EvidenceWorkbenchResponseV1`, `RetentionStateResponseV1`, `ApplyRetentionPolicyRequestV1`, `PlaceRetentionHoldRequestV1`, `ReleaseRetentionHoldRequestV1`, `RecordDispositionDecisionRequestV1`, `RetentionMutationResponseV1`, `CreateRetentionExportRequestV1`, `RetentionExportResponseV1`, `CreateRetentionRecoveryRequestV1`, `RetentionRecoveryResponseV1`, and `ProtectedOutcomeV1`.

Exact routes remain those frozen in sections 18–20. Status mapping is: successful GET `200`; synchronous successful governance mutation `200`; export/recovery request accepted `202`; invalid request/schema/domain input `422`; protected-not-found `404`; known authorized but not-permitted action `403`; stale version/idempotency digest conflict `409`; protected dependency/content unavailable `503`. `indeterminate` eligibility is a successful `200` state representation, never a purge authorization. Authentication failure remains existing `401` behavior.

Bounded text limits are exact: `basis_code` and `reason_code` 1..64 lower-case code characters `[a-z0-9_.-]`; Human rationale/reason/release rationale 1..2000 characters when required and max 2000 when optional; `authority_reference` 1..512; export `purpose` 1..1000; export `format` is exactly `zip_v1` in Commercial V1. Unknown enum/code values fail `422`.

### 31.5 Storage, export and recovery adapters — closes P055-IDS-MAJ-04

PATCH-055 reuses `SupportingFileObjectStore` / `S3PrivateSupportingFileObjectStore` exact-key/version semantics and MUST NOT introduce bucket listing, public URL, presigned URL, or raw locator APIs. Protected file resolution is by canonical Supporting File identity -> authorized asset -> internal `storage_key + object_version`; these storage coordinates never leave the service boundary.

New port `RetentionExportStore` exposes only `put_private(export_id, stream, media_type) -> receipt`, `head_exact(export_id, version)`, and `open_exact(export_id, version)`. New port `RetentionRecoveryResolver` exposes only `resolve_authorized(subject, expected_digest) -> stream/status`; it delegates Supporting File byte resolution to the existing authorized exact-key object-store seam and may return unavailable without exposing locator details.

Streaming is bounded in 1 MiB chunks. Any individual Supporting File remains bounded by existing `MAX_FILE_BYTES = 26,214,400` bytes. Export accepts at most 32 subjects and rejects aggregate protected payload above `32 * MAX_FILE_BYTES = 838,860,800` bytes before completed status; metadata entries remain max 64. No export/recovery operation buffers the aggregate artifact wholly in application memory. Recovery handles exactly one subject and therefore inherits the 26,214,400-byte Supporting File bound when bytes are file-backed.

Completed export artifact bytes are private, immutable-by-version, digest-verified, and downloadable only through a reauthorized application route; failed or incomplete export state never exposes a download handle. Recovery never creates a new engineering identity or lifecycle version.

### 31.6 Exact implementation/file manifest — closes P055-IDS-MAJ-05

Backend files to create are exactly: `backend/app/enums/retention.py`, `backend/app/models/retention.py`, `backend/app/models/retention_command.py`, `backend/app/schemas/retention.py`, `backend/app/ports/retention.py`, `backend/app/repositories/retention_repository.py`, `backend/app/repositories/retention_unit_of_work.py`, `backend/app/services/retention_service.py`, `backend/app/dependencies/retention.py`, `backend/app/api/v1/routers/retention.py`, and one additive Alembic revision allocated only during authorized implementation.

Backend files permitted to modify are exactly: `backend/app/main.py`, `backend/app/models/__init__.py`, and the minimum existing Evidence/Supporting File composition seam needed to compose the Workbench without redefining their aggregates. No other backend file is in-scope without Implementation Plan amendment and review.

Frontend files to create are exactly: `frontend/src/components/EvidenceWorkbench.tsx`, `frontend/src/components/RetentionGovernancePanel.tsx`, `frontend/src/components/EvidenceLineageReliancePanel.tsx`, `frontend/src/components/RetentionExportRecoveryPanel.tsx`, and `frontend/src/services/retentionApi.ts`.

Frontend files permitted to modify are exactly: `frontend/src/components/SupportingEvidencePanel.tsx` and the existing Project/Workspace route composition file that currently mounts `SupportingEvidencePanel`; implementation planning MUST name that one concrete route file after repository confirmation and before readiness. Test files are frozen below.

State-machine behavior is server-authoritative: initial/loading -> authorized loaded or protected failure; mutation pending disables duplicate authority action; success -> mandatory authorized reread; conflict -> stale banner + mandatory reread before resubmit; unavailable/indeterminate never optimistic-success; export/recovery polling/status updates never alter Evidence/retention authority locally. Raw UUID entry is prohibited in ordinary controls.

### 31.7 Capability-owned idempotency/outbox contract — closes P055-IDS-MAJ-08

Repository inspection confirms SATCO has shared `audit_logs` but capability-owned idempotency/outbox tables for Technical Report, Organizational Memory, Evidence, Supporting File, and Standards. PATCH-055 therefore owns `retention_idempotency` and `retention_outbox`; this is deliberate repository alignment, not a new shared infrastructure pattern.

`retention_idempotency` columns are exactly: `organization_id`, `actor_user_id`, `operation`, `idempotency_key UUID`, `request_digest CHAR(64)`, `status` in `pending|completed`, nullable bounded `safe_result JSONB`, `created_at`, `updated_at`, nullable `completed_at`. Unique key: `(organization_id, actor_user_id, operation, idempotency_key)`. Pending requires null result/completed_at; completed requires non-null safe result/completed_at. Safe result stores only logical outcome, opaque aggregate/request ID, version/status codes and correlation ID; never protected content or storage locator.

`retention_outbox` columns are exactly: `event_id UUID PK`, `organization_id`, nullable `project_id/workspace_id`, `aggregate_kind`, `aggregate_id`, `aggregate_version`, `event_type`, `payload_schema_version=1`, safe `payload JSONB`, `occurred_at`, `created_at`, nullable `published_at`, `attempt_count >= 0`, nullable bounded `last_error_category`. Unique `(aggregate_kind, aggregate_id, aggregate_version, event_type)`. Publication may update only publication bookkeeping; domain payload is immutable after commit.

### 31.8 Exact 48-vector executable qualification contract — closes P055-IDS-MAJ-06

The 48 EDS vector IDs remain unchanged. Exact backend test file is `backend/tests/test_patch055_commercial_evidence_retention.py`; exact frontend test file is `frontend/src/test/evidence-workbench-retention.test.tsx`; migration/recovery qualification file is `backend/tests/test_patch055_retention_migration.py`.

The backend test module MUST expose one parametrized manifest named `PATCH055_BACKEND_VECTORS` containing exactly P055-EVW-01..10, P055-RET-01..08, P055-HLD-01..08, P055-XRC-01..08, and P055-SEC-01..08 = 42 unique vectors. The frontend module MUST expose exactly P055-UX-01..06 = 6 unique vectors. No duplicate ID may satisfy two cases.

Canonical fixtures are exactly: `org_a_admin`, `org_a_engineer`, `org_a_project_owner`, `org_a_workspace_member`, `org_b_admin`, `project_a`, `workspace_a`, `evidence_a_proposed`, `evidence_a_current`, `supporting_file_a_available`, `supporting_file_a_quarantined`, `accepted_report_a`, `memory_a`, `retention_subject_evidence_a`, `retention_subject_file_a`, `frozen_clock`, and private in-memory object-store/export/recovery test doubles implementing the production ports.

Expected result for each vector is the semantic obligation already frozen in section 27, strengthened by this addendum's exact contracts. Every vector MUST assert both the positive state transition/read result and relevant negative invariant where section 27 names one; protected vectors MUST assert no foreign identifier/count/detail leakage.

Exact focused commands are:
`cd backend && pytest -q tests/test_patch055_commercial_evidence_retention.py tests/test_patch055_retention_migration.py`
and
`cd frontend && npm run test:run -- src/test/evidence-workbench-retention.test.tsx && npm run typecheck && npm run build`.

Manifest integrity command is:
`python -m pytest -q backend/tests/test_patch055_commercial_evidence_retention.py --collect-only`
plus deterministic static assertion inside the test module that the backend set is exactly 42 IDs and frontend test assertion that the UI set is exactly 6 IDs; combined acceptance is exactly 48/48.

Full regression commands required before QG-11 are `cd backend && pytest -q` and `cd frontend && npm run test:run && npm run typecheck && npm run build`.

### 31.9 Rollback, forward-repair, and operational observability — closes P055-IDS-MAJ-07

Application rollback boundary: PATCH-055 routes/UI can be disabled at composition/router exposure without deleting or mutating PATCH-055 persistence. Rollback MUST NOT drop retention tables in a live/customer database merely to revert application code. Older application code MUST ignore additive PATCH-055 tables.

Migration downgrade is schema-only and permitted only on disposable qualification infrastructure after proving PATCH-055 tables contain no data that would be destroyed; otherwise downgrade MUST refuse and forward-repair is the governed production recovery path. Forward-repair uses a new additive migration and never rewrites accepted Evidence/File/Report/Memory history. One Alembic head is mandatory before and after repair qualification.

Operational metrics are exact capability counters/gauges: request count/latency/error by operation and safe outcome; idempotency conflict count; retention conflict count; active-hold count; eligibility-indeterminate count; export requested/completed/failed count and bytes; recovery requested/completed/unavailable count; outbox unpublished count/oldest age/publication attempts. Metrics MUST NOT label by subject UUID, filename, rationale, user-supplied text, storage key, or document content.

Structured logs contain correlation ID, operation, safe outcome, duration, server-derived organization/project/workspace surrogate where existing logging policy permits, and opaque aggregate/request ID only after authorization. Logs MUST redact rationale, authority reference, file names/content, object keys, credentials, tokens, export payloads, and scanner diagnostics.

Alert conditions for readiness are: sustained outbox oldest-age breach, repeated export/recovery failure, integrity failure, unexpected `indeterminate` growth, and migration/head mismatch. Threshold values remain deployment/runbook operational configuration and do not change engineering semantics.

### 31.10 Corrected IDS self-review and gate state

Section 29's pre-review claim of zero findings is superseded. The first independent review found 0 Critical / 8 Major / 0 Minor / 0 Observation and returned QG-4 FAIL.

This correction addendum addresses: MAJ-01 exact retention-head projection/digest; MAJ-02 exact hold revisions; MAJ-03 role/API/DTO/status/idempotency header; MAJ-04 adapters/stream bounds; MAJ-05 file/frontend manifest; MAJ-06 executable 48-vector contract; MAJ-07 rollback/observability; MAJ-08 capability-owned idempotency/outbox closure.

Corrected candidate state is therefore `READY FOR INDEPENDENT IDS RE-REVIEW`, not Human accepted and not implementation-authorized. QG-4 remains NOT PASSED until an independent re-review returns PASS and explicit Human IDS acceptance remains a separate gate.

All stop-boundary prohibitions in section 30 remain in force: no Implementation Plan, code/test/frontend implementation, migration creation/execution, database mutation, stage, commit, push, deployment, or PATCH-056+ work is authorized by this addendum.

### 31.11 Repository-key type and route-file reconciliation

Repository-native key types are frozen exactly: `organization_id UUID`; `project_id INTEGER`; `workspace_id INTEGER NULL`; all `*_user_id` actor/owner fields INTEGER; Evidence and Supporting File `subject_id` UUID. Any earlier section 7/8/9/11/12 wording that called Project, Workspace, or User identifiers UUID is superseded by this subsection.

Foreign keys MUST reference existing canonical owners with `ON DELETE RESTRICT` where the current owner model uses restricted history semantics. Typed subject identity keeps UUID `subject_id` because both current Evidence and Supporting File identities are UUID-backed.

The exact existing frontend route composition file permitted to modify is `frontend/src/pages/ProjectsPage.tsx`; it currently mounts `SupportingEvidencePanel`. Section 31.6's placeholder wording about naming that route later is superseded: the PATCH-055 Workbench is mounted through `ProjectsPage.tsx` in the current repository shape.

The exact backend router composition file is `backend/app/main.py`; authorized implementation may add `retention_router` import/include there and nowhere else merely to expose PATCH-055 routes.

### 31.12 Final exactness reconciliation before re-review

Section 31.6 is tightened: no existing Evidence or Supporting File backend file requires modification for PATCH-055 composition. Existing APIs/services are consumed unchanged. Existing backend files permitted to modify are exactly `backend/app/main.py` and `backend/app/models/__init__.py`; all other backend production additions are the new PATCH-055 files listed in section 31.6 plus the single migration.

The migration contract is one additive revision with frozen design identifier `e05500000001`, down-revision `e05400000006`, creating only the eight PATCH-055 tables frozen in section 6 as corrected by this addendum. Implementation MUST first prove `e05400000006` is still the sole repository head; if it is not, implementation stops and IDS/Plan reconciliation is required rather than inventing a merge revision.

Current disposition projection is exact: select the latest authorized `retention_disposition_decisions` row for the current `retention_record_id`; if none exists, project `none`. A retention-policy replacement creates a new retention record and therefore projects `none` until a Human decision is recorded against that new record. Hold placement/release changes eligibility but does not erase an attributable prior disposition-decision record.

Shared `audit_logs` is reused. Exact PATCH-055 audit action codes are `RETENTION_POLICY_APPLIED`, `RETENTION_POLICY_REPLACED`, `RETENTION_HOLD_PLACED`, `RETENTION_HOLD_RELEASED`, `RETENTION_DISPOSITION_DECISION_RECORDED`, `RETENTION_EXPORT_REQUESTED`, `RETENTION_EXPORT_COMPLETED`, `RETENTION_EXPORT_FAILED`, `RETENTION_RECOVERY_REQUESTED`, `RETENTION_RECOVERY_COMPLETED`, and `RETENTION_RECOVERY_UNAVAILABLE`. Audit metadata obeys the same safe-payload/redaction contract as `retention_outbox`.

### 31.13 Exact export artifact handling

`retention_exports` additionally persists private operational fields `artifact_storage_key VARCHAR(80) NULL` and `artifact_object_version VARCHAR(128) NULL`. They are null unless status is `completed`; completed status requires both plus `aggregate_digest` and `byte_count`. These private coordinates are never serialized into public DTOs, Audit, metrics, or outbox payloads.

`RetentionExportStore.put_private` generates the opaque private key internally and returns key/version/byte_count/SHA-256 receipt; service verifies the receipt, persists the private coordinates and public-safe digest/count, then marks completed atomically. Failure before that transaction leaves status failed/requested as applicable and no false completed artifact.

The exact completed-artifact route is `GET /api/v1/retention-exports/{export_id}/content`. It reauthenticates/re-authorizes the actor and every bound export subject, resolves only the persisted private receipt server-side, verifies digest/byte count, and streams in 1 MiB chunks. It returns `404 protected_not_found`, `403 not_permitted`, or `503 unavailable` under the section 31.4 mapping and never redirects to or exposes object storage.

## 32. Human IDS acceptance

Human Architecture/Engineering Authority decision: **PASS / ACCEPTED / COMPLETE**.

Acceptance date: 2026-09-14.

Acceptance basis:
- independent IDS re-review returned 0 Critical / 0 Major / 0 Minor / 0 Observation;
- QG-4 is satisfied;
- the QG-4 correction addendum in sections 31.1–31.13 is normative;
- PATCH-055 scope and the accepted ADR-028 / EDS-055 authority remain unchanged.

Authority granted by this acceptance is limited to preparation and independent review of the PATCH-055 Implementation Plan / Readiness artifacts.

This Human IDS acceptance does **not** authorize production/test/frontend implementation, migration creation or execution, database mutation, stage, commit, push, deployment, or PATCH-056+ work.

**IDS-055: HUMAN ACCEPTED / COMPLETE**
