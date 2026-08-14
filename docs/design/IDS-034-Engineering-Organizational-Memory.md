# IDS-034 — Engineering Organizational Memory

## 1. Document Control

| Field | Value |
|---|---|
| Document ID | IDS-034 |
| Related PATCH | PATCH-034 — Engineering Organizational Memory |
| Related EDS | EDS-034 — Engineering Organizational Memory |
| Status | ACCEPTED / COMPLETE |
| Human EDS-034 Acceptance | PASS |
| IDS design authority | GRANTED |
| Independent IDS Review | PASS after focused amendments and final re-review; prior FAIL history preserved |
| Human IDS Acceptance | PASS |
| Implementation Plan authority | GRANTED / EXERCISED |
| Implementation-Plan-034 | ACCEPTED / COMPLETE |
| Implementation authority | NOT GRANTED |
| Date | 2026-08-12 |

## 2. Authority and Scope

This IDS is subordinate to the Constitution, Engineering Intelligence
Manifesto, ADR-021, ADR-023, accepted PATCH-034, and accepted EDS-034. It uses
the current repository contracts delivered by PATCH-032 without transferring
Technical Report ownership.

Executable Version 1 is limited to one source class:

```text
exact Human-accepted Technical Report version
    → explicit Human Organizational Memory admission
    → active
    → withdrawn | superseded
```

No other source, state, publication workflow, search mechanism, AI authority,
graph expansion, or UI is part of IDS-034.

## 3. Repository Alignment

The repository currently provides:

- `TechnicalReportActor { actor_id: int, organization_id: UUID }`;
- `TechnicalReportService.get_report(actor, report_id)` with canonical
  authorization-before-disclosure;
- immutable `TechnicalReportAcceptedSnapshot` and lowercase SHA-256 integrity
  digest validation;
- accepted report Organization, Workspace, optional Project, owner, lifecycle,
  aggregate version, accepted revision, provenance, and acceptance record;
- active User, Organization, membership, Workspace, Project, and Workspace
  membership persistence used by the canonical authorization policy;
- shared Audit infrastructure and established UoW, idempotency, outbox, runtime
  role, migration, and protected-error conventions.

The Organizational Memory adapter may privately invoke the canonical Technical
Report application service through its request-scoped UoW factory. It must not
receive a Technical Report repository, Session, ORM row, or canonical UoW.

No new Technical Report operation or contract is assumed. The accepted report
is immutable. Memory final recheck re-invokes the canonical authorized read and
then locks/rechecks the shared active User, Organization, membership,
Workspace, Project, and operation-authority predicates in the memory UoW before
commit. If implementation proves a current visibility predicate cannot be
rechecked without direct Technical Report persistence access, work stops and
returns to IDS governance.

## 4. Closed Vocabulary

```python
class MemoryStanding(StrEnum):
    ACTIVE = "active"
    WITHDRAWN = "withdrawn"
    SUPERSEDED = "superseded"

class MemoryOperation(StrEnum):
    ADMIT = "admit"
    GET_ACTIVE = "get_active"
    LIST_ACTIVE = "list_active"
    INSPECT_HISTORY = "inspect_history"
    CREATE_SUCCESSOR = "create_successor"
    WITHDRAW = "withdraw"
    SUPERSEDE = "supersede"
    GOVERNANCE_AUDIT = "governance_audit"

class MemoryOutcomeCode(StrEnum):
    SUCCESS = "success"
    PROTECTED_NOT_FOUND = "protected_not_found"
    INVALID_REQUEST = "invalid_request"
    VERSION_CONFLICT = "version_conflict"
    IDEMPOTENCY_CONFLICT = "idempotency_conflict"
    INVALID_STANDING = "invalid_standing"
    DUPLICATE_SOURCE = "duplicate_source"
    UNAVAILABLE = "unavailable"
```

No alias, unknown enum value, client-controlled standing, or additional
operation is accepted.

## 5. Typed Identity, Actor, and Scope Contracts

```python
@dataclass(frozen=True, slots=True)
class MemoryActor:
    actor_id: int                    # positive, non-bool
    organization_id: UUID           # trusted server-derived Organization

@dataclass(frozen=True, slots=True)
class MemoryScope:
    organization_id: UUID
    workspace_id: int               # positive, non-bool
    project_id: int | None           # positive when present

@dataclass(frozen=True, slots=True)
class MemoryId:
    value: UUID

@dataclass(frozen=True, slots=True)
class MemoryVersion:
    value: int                       # positive, non-bool

@dataclass(frozen=True, slots=True)
class AcceptedReportSource:
    report_id: UUID
    accepted_aggregate_version: int  # positive; exact canonical accepted version
    accepted_snapshot_digest: str    # lowercase SHA-256
```

Organization is never supplied as client authority. Transport obtains it from
the existing authenticated Organization context and rejects any conflicting
client scope before application execution.

## 6. Exact Admitted Snapshot Contract

### 6.1 Projection Version

The only V1 projection contract is:

```text
projection_contract = "organizational_memory.accepted_report.v1"
```

The admitted snapshot contains exactly:

```python
@dataclass(frozen=True, slots=True)
class AdmittedTechnicalContentV1:
    engineering_scope: str
    technical_content: str
    assumptions: tuple[str, ...]
    uncertainty: str
    limitations: tuple[str, ...]
    conclusions: str
    recommendations: tuple[str, ...]

@dataclass(frozen=True, slots=True)
class AdmittedQualificationV1:
    is_preliminary: bool
    evidence_deficiencies: tuple[str, ...]
    unresolved_issues: tuple[str, ...]
    follow_up_requirements: tuple[str, ...]

@dataclass(frozen=True, slots=True)
class AdmittedReportProjectionV1:
    projection_contract: Literal["organizational_memory.accepted_report.v1"]
    report_id: UUID
    purpose: TechnicalReportPurpose
    organization_id: UUID
    workspace_id: int
    project_id: int | None
    content: AdmittedTechnicalContentV1
    qualification: AdmittedQualificationV1
    accepted_draft_revision_id: UUID
    accepted_draft_revision_number: int
    accepted_aggregate_version: int
    accepted_by_id: int
    accepted_at: datetime
    predecessor_report_id: UUID | None
```

Every value except `projection_contract` is copied exactly from the validated
canonical `TechnicalReportAcceptedSnapshot`. All seven content fields and all
four qualification fields are mandatory. No selective omission within these
closed groups is permitted because omission may alter technical meaning.

Admission rationale, audience, and reuse restrictions are separate memory
governance metadata. They are not fields of the technical projection and may
not add or alter technical assertions.

### 6.2 Provenance Manifest

The memory source manifest contains:

```python
@dataclass(frozen=True, slots=True)
class MemoryProvenanceDigestEntry:
    entry_id: UUID
    ordinal: int                     # zero-based, contiguous
    source_class: TechnicalReportSourceClass
    source_type: str
    owning_capability: str
    is_material: bool
    reliance_role: str
    locator_digest: str              # lowercase SHA-256
    source_integrity_algorithm: Literal["sha256"]
    source_integrity_digest: str     # lowercase SHA-256

@dataclass(frozen=True, slots=True)
class MemorySourceManifestV1:
    source: AcceptedReportSource
    source_snapshot_digest: str
    projection_contract: Literal["organizational_memory.accepted_report.v1"]
    admitted_projection_digest: str
    provenance_digest: str
    provenance_entries: tuple[MemoryProvenanceDigestEntry, ...]
```

The manifest copies no provenance plaintext, locator body, Evidence body,
Capture content, external representation, attachment, or protected source
description. Entries preserve canonical accepted-snapshot order.

### 6.2.1 Memory-Specific Provenance Authorization and Resolution

Technical Report visibility does not authorize disclosure of a referenced
canonical identity. Memory uses this closed contract before admitting,
retrieving, historically inspecting, or reusing provenance-bearing content:

```python
class MemoryProvenanceOperation(StrEnum):
    ADMIT = "admit"
    GET_ACTIVE = "get_active"
    INSPECT_HISTORY = "inspect_history"
    REUSE = "reuse"

@dataclass(frozen=True, slots=True)
class CaptureProvenanceAuthorization:
    entry_id: UUID
    ordinal: int
    capture_id: UUID
    source_version: int
    organization_id: UUID
    project_id: int
    workspace_id: int | None
    engineering_object_id: UUID | None

@dataclass(frozen=True, slots=True)
class EvidenceProvenanceAuthorization:
    entry_id: UUID
    ordinal: int
    evidence_id: UUID
    source_version: int
    organization_id: UUID
    project_id: int | None
    workspace_id: int | None

@dataclass(frozen=True, slots=True)
class EngineeringObjectProvenanceAuthorization:
    entry_id: UUID
    ordinal: int
    engineering_object_id: UUID
    source_version: int
    organization_id: UUID
    project_id: int
    workspace_id: int

@dataclass(frozen=True, slots=True)
class EngineeringRelationshipProvenanceAuthorization:
    entry_id: UUID
    ordinal: int
    engineering_relationship_id: UUID
    source_version: int
    organization_id: UUID
    project_id: int
    workspace_id: int
    source_object_id: UUID
    target_object_id: UUID

CanonicalProvenanceAuthorization = (
    CaptureProvenanceAuthorization | EvidenceProvenanceAuthorization |
    EngineeringObjectProvenanceAuthorization |
    EngineeringRelationshipProvenanceAuthorization
)

@dataclass(frozen=True, slots=True)
class MemoryProvenanceAuthorizationRequest:
    actor: MemoryActor
    operation: MemoryProvenanceOperation
    memory_scope: MemoryScope
    source: AcceptedReportSource
    items: tuple[CanonicalProvenanceAuthorization, ...]  # 1..100 unique identities

@dataclass(frozen=True, slots=True)
class SafeAuthorizedProvenance:
    entry_id: UUID
    ordinal: int
    source_class: TechnicalReportSourceClass
    source_type: str
    owning_capability: str
    is_material: bool
    reliance_role: str
    locator_digest: str
    source_integrity_algorithm: Literal["sha256"]
    source_integrity_digest: str

@dataclass(frozen=True, slots=True)
class ProvenanceAuthorized:
    outcome: Literal["success"]
    items: tuple[SafeAuthorizedProvenance, ...]

@dataclass(frozen=True, slots=True)
class ProvenanceProtectedNotFound:
    outcome: Literal["protected_not_found"]

@dataclass(frozen=True, slots=True)
class ProvenanceUnavailable:
    outcome: Literal["unavailable"]

MemoryProvenanceAuthorizationResult = (
    ProvenanceAuthorized | ProvenanceProtectedNotFound | ProvenanceUnavailable
)

class MemoryProvenanceAuthorizer(Protocol):
    def authorize_and_resolve(
        self, request: MemoryProvenanceAuthorizationRequest
    ) -> MemoryProvenanceAuthorizationResult: ...
```

The adapter derives every request field from the accepted snapshot's closed
historical-basis union; clients cannot provide or override it. Before any call,
the item's Organization must equal actor, report, and memory Organization, and
its Project/Workspace must be compatible with the admitted memory scope. It
then invokes exactly the following current application boundary:

| Variant | Exact canonical call and trusted context | Required response check |
|---|---|---|
| Capture | `EngineeringExperienceCaptureService.read_authorized_detail(actor=EngineeringExperienceCaptureActor(actor_id, organization_id), project_id=item.project_id, workspace_id=item.workspace_id, engineering_object_id=item.engineering_object_id, capture_id=item.capture_id)` | returned `id`, Project, Workspace, optional Engineering Object, and Organization authority established by the service match the accepted basis |
| Evidence | `EvidenceService.get(item.evidence_id, EvidenceActor(actor_id, organization_id))`; the service performs `ReadEvidence` authorization | returned ID, Organization, optional Project, and optional Workspace match the accepted basis |
| Engineering Object | `EngineeringObjectService.get(item.engineering_object_id, AuthenticatedActor(actor_id, organization_id), AuthorizationContext(operation="ReadEngineeringObject", scope={"object_id": item.engineering_object_id}))` | returned ID, Organization, Project, and Workspace match the accepted basis |
| Engineering Relationship | `EngineeringRelationshipService.get(item.engineering_relationship_id, AuthenticatedRelationshipActor(actor_id, organization_id), RelationshipAuthorizationContext(operation="ReadEngineeringRelationship", scope={"relationship_id": item.engineering_relationship_id}))` | returned ID, Organization, Project, Workspace, source Object, and target Object match the accepted basis |

These are read operations owned by the canonical services; the memory operation
selects whether their safe result may be used for admission, active retrieval,
history, or reuse but never substitutes a different canonical operation string.
The adapter receives no canonical repository, Session, validator, policy, or
UoW. Dependency composition uses the same request-scoped factories as the
canonical API/application boundary.
Requests are deduplicated by `(identity type, identity, source_version)`, retain
accepted-snapshot ordinal order, and contain at most 100 unique canonical
identities. An operation may issue at most three ordered requests and resolve at
most 256 unique identities total, with at most one owning-service read per
unique identity. All batches form one logical all-or-nothing authorization;
results are disclosed only after every batch succeeds. Returned current versions need not equal the recorded
historical version; current authorization establishes disclosure authority,
while the accepted immutable historical basis and digest establish historical
meaning.

Resolution is all-or-nothing. Any missing, inaccessible, cross-scope,
wrong-Organization, response-context mismatch, or malformed canonical identity returns the
payload-free protected result for the whole provenance-bearing operation; any
dependency failure returns payload-free unavailable. No partial items,
cardinality, failing ordinal, identity, or source family is disclosed. Success
has exactly one result per requested item in ordinal order and fields exactly
equal to its retained digest entry.

The final V1 admitted provenance identity classes are exactly Capture,
Evidence, Engineering Object, and Engineering Relationship. External-human,
standards, and contextual locators have no current authorization-aware
application read and therefore are not retained by Organizational Memory V1.
An otherwise accepted report containing any such provenance class is not V1-
admissible and returns payload-free `invalid_request` after report authorization;
memory does not persist a partial manifest or silently omit an accepted entry.
Supporting those classes requires a later accepted canonical authorization
contract and IDS amendment; Technical Report visibility is never substituted.

Admission runs this contract for every canonical material entry before the
projection is persisted. `get_active` and reuse run it when returning safe
provenance; `inspect_history` runs it only when `include_provenance` is true.
`list_active` never returns provenance and makes no provenance calls. Current
source and memory authorization must also pass independently in every case.

### 6.3 Normalization and Serialization

Canonical serialization is UTF-8 JSON with:

- Unicode NFC;
- UUID as canonical lowercase hyphenated text;
- enums as exact string values;
- timezone-aware UTC timestamps as `YYYY-MM-DDTHH:MM:SS.ffffffZ`;
- integers as JSON integers, never booleans or floats;
- tuples as arrays preserving source order;
- object keys sorted lexicographically;
- separators `,` and `:` with no insignificant whitespace;
- `ensure_ascii=false`, `allow_nan=false`;
- explicit `null` for optional values;
- no undeclared fields.

Strings must already equal the corresponding validated accepted-snapshot
value after canonical Technical Report normalization. Memory may not strip,
rewrite line endings, alter case, units, precision, wording, or list order.

Digests are lowercase hexadecimal SHA-256:

```text
source_snapshot_digest
  = canonical Technical Report accepted_snapshot_digest

admitted_projection_digest
  = sha256(canonical_json(AdmittedReportProjectionV1))

provenance_digest
  = sha256(canonical_json(tuple[MemoryProvenanceDigestEntry]))
```

Admission succeeds only when the canonical accepted snapshot independently
validates its source digest, all projected values equal that snapshot, every
manifest entry corresponds by identity/order/digest to accepted provenance,
and recomputation matches all stored digests.

Paraphrase, summary, inference, synthesis, translation, generated text, field
omission, reordered semantic lists, or new conclusion, recommendation,
qualification, rationale, limitation, assumption, or assertion is invalid.

### 6.4 Size Limits

- canonical admitted projection bytes: maximum 256 KiB;
- source manifest canonical bytes: maximum 128 KiB;
- provenance entries: 1–256, matching the canonical accepted snapshot exactly;
- admission rationale: 1–2,000 Unicode code points after NFC/trim;
- reuse restriction text: 0–2,000 code points per item, maximum 32 items;
- audience identifiers: maximum 100, unique positive integers, sorted.

If the exact projection exceeds the limit, admission returns `invalid_request`;
content is not truncated or summarized.

## 7. Aggregate State Contract

```python
@dataclass(frozen=True, slots=True)
class OrganizationalMemory:
    id: UUID
    organization_id: UUID
    workspace_id: int
    project_id: int | None
    version: int
    standing: MemoryStanding
    source: AcceptedReportSource
    projection: AdmittedReportProjectionV1
    manifest: MemorySourceManifestV1
    admitted_by_id: int
    admitted_at: datetime
    admission_rationale: str
    audience_actor_ids: tuple[int, ...]
    reuse_restrictions: tuple[str, ...]
    predecessor_memory_id: UUID | None
    withdrawn_by_id: int | None
    withdrawn_at: datetime | None
    withdrawal_reason: str | None
    superseded_by_id: int | None
    superseded_at: datetime | None
    supersession_reason: str | None
    replacement_memory_id: UUID | None
    created_at: datetime
    updated_at: datetime

@dataclass(frozen=True, slots=True)
class MemoryStandingHistoryRecord:
    event_id: UUID
    memory_id: UUID
    organization_id: UUID
    aggregate_version: int
    from_standing: MemoryStanding | None
    to_standing: MemoryStanding
    actor_id: int
    occurred_at: datetime
    reason: str
    replacement_memory_id: UUID | None
```

Only the coherent shapes below are valid:

- `active`: all withdrawal/supersession fields null;
- `withdrawn`: withdrawal triplet non-null; supersession/replacement null;
- `superseded`: supersession triplet and replacement non-null; withdrawal null.

Projection, manifest, source, scope, admission, audience, restrictions,
predecessor, and created time never change. A standing transition increments
version exactly once and sets only its closed transition fields and updated
time. Withdrawn and superseded are terminal.

## 8. Commands and Closed Results

### 8.1 Command Metadata

```python
class MemoryCommandMetadata:
    actor: MemoryActor
    correlation_id: UUID
    command_id: UUID
    idempotency_id: UUID
    rationale: str                   # 1..2000
```

### 8.2 Admission

```python
class AdmitAcceptedReport:
    metadata: MemoryCommandMetadata
    source: AcceptedReportSource
    scope: MemoryScope
    audience_actor_ids: tuple[int, ...]
    reuse_restrictions: tuple[str, ...]
    admission_rationale: str

class AdmissionSuccess:
    outcome: Literal["success"]
    memory_id: UUID
    version: Literal[1]
    standing: Literal[MemoryStanding.ACTIVE]
    source: AcceptedReportSource
```

The client cannot provide projection, manifest, digests other than the expected
source digest, standing, admitted actor/time, or lifecycle fields. Application
resolution constructs all server-owned values.

### 8.3 Withdrawal

```python
class WithdrawMemory:
    metadata: MemoryCommandMetadata
    memory_id: UUID
    expected_version: int
    reason: str                      # 1..2000
```

Only active memory may transition. Success returns memory ID, resulting version,
and `withdrawn`; no snapshot plaintext enters the command result.

```python
class WithdrawalSuccess:
    outcome: Literal["success"]
    memory_id: UUID
    version: int
    standing: Literal[MemoryStanding.WITHDRAWN]
    withdrawn_at: datetime
```

### 8.4 Successor Creation

```python
class CreateMemorySuccessor:
    metadata: MemoryCommandMetadata
    source: AcceptedReportSource
    scope: MemoryScope
    audience_actor_ids: tuple[int, ...]
    reuse_restrictions: tuple[str, ...]
    admission_rationale: str
    predecessor_memory_id: UUID
```

Successor creation uses the same projection rules as admission but requires a
`predecessor_memory_id`. The new source
must be a different exact accepted Technical Report version, source scope must
be compatible, predecessor must be independently authorized, and predecessor
cardinality is zero or one. Creation leaves predecessor standing unchanged.

```python
class CreateSuccessorSuccess:
    outcome: Literal["success"]
    memory_id: UUID
    version: Literal[1]
    standing: Literal[MemoryStanding.ACTIVE]
    source: AcceptedReportSource
    predecessor_memory_id: UUID
```

### 8.5 Explicit Supersession

```python
class SupersedeMemory:
    metadata: MemoryCommandMetadata
    predecessor_memory_id: UUID
    replacement_memory_id: UUID
    expected_predecessor_version: int
    expected_replacement_version: int
    reason: str
```

Both records must be active, same Organization, compatible scope, independently
authorized, distinct, and linked by `replacement.predecessor_memory_id ==
predecessor.id`. One transaction changes only predecessor standing to
superseded and records the replacement identity. Replacement remains active.

```python
class SupersessionSuccess:
    outcome: Literal["success"]
    predecessor_memory_id: UUID
    predecessor_version: int
    predecessor_standing: Literal[MemoryStanding.SUPERSEDED]
    replacement_memory_id: UUID
    replacement_version: int
    replacement_standing: Literal[MemoryStanding.ACTIVE]
    superseded_at: datetime
```

### 8.6 Read Requests

```python
class GetActiveMemory:
    memory_id: UUID
    include_provenance: bool = False
    reuse_intent: bool = False

class InspectMemoryHistory:
    memory_id: UUID
    include_predecessor: bool = False
    include_replacement: bool = False
    include_provenance: bool = False

class ListActiveMemory:
    scope: MemoryScope
    page_size: int                   # 1..100
    continuation: str | None
```

### 8.7 Closed Outcomes

All non-success results are payload-free discriminated records:

```python
class MemoryProtectedNotFound:
    outcome: Literal["protected_not_found"]
class MemoryInvalidRequest:
    outcome: Literal["invalid_request"]
class MemoryVersionConflict:
    outcome: Literal["version_conflict"]
class MemoryIdempotencyConflict:
    outcome: Literal["idempotency_conflict"]
class MemoryInvalidStanding:
    outcome: Literal["invalid_standing"]
class MemoryDuplicateSource:
    outcome: Literal["duplicate_source"]
class MemoryUnavailable:
    outcome: Literal["unavailable"]
```

The exact unions, after the success DTOs in §9 are defined, are:

```python
AdmitResult = AdmissionSuccess | MemoryProtectedNotFound | MemoryInvalidRequest | MemoryIdempotencyConflict | MemoryDuplicateSource | MemoryUnavailable
WithdrawResult = WithdrawalSuccess | MemoryProtectedNotFound | MemoryInvalidRequest | MemoryVersionConflict | MemoryIdempotencyConflict | MemoryInvalidStanding | MemoryUnavailable
CreateSuccessorResult = CreateSuccessorSuccess | MemoryProtectedNotFound | MemoryInvalidRequest | MemoryIdempotencyConflict | MemoryDuplicateSource | MemoryUnavailable
SupersedeResult = SupersessionSuccess | MemoryProtectedNotFound | MemoryInvalidRequest | MemoryVersionConflict | MemoryIdempotencyConflict | MemoryInvalidStanding | MemoryUnavailable
GetActiveResult = GetActiveSuccess | MemoryProtectedNotFound | MemoryInvalidRequest | MemoryUnavailable
ListActiveResult = ListActiveSuccess | MemoryProtectedNotFound | MemoryInvalidRequest | MemoryUnavailable
InspectHistoryResult = InspectHistorySuccess | MemoryProtectedNotFound | MemoryInvalidRequest | MemoryUnavailable
```

`duplicate_source` is exposed only after both source and existing memory are
authorized; `invalid_standing` only after subject authorization. An operation
may not return a variant absent from its declared union.

No protected outcome includes identifiers, counts, standing, lineage,
provenance, plaintext, diagnostics, denial reason, or dependency identity.

## 9. Read DTOs

```python
class ActiveMemorySummary:
    memory_id: UUID
    version: int
    standing: Literal[MemoryStanding.ACTIVE]
    source_report_id: UUID
    source_accepted_version: int
    purpose: TechnicalReportPurpose
    organization_id: UUID
    workspace_id: int
    project_id: int | None
    admitted_by_id: int
    admitted_at: datetime
    updated_at: datetime

class ActiveMemoryDetail:
    summary: ActiveMemorySummary
    projection: AdmittedReportProjectionV1
    admission_rationale: str
    reuse_restrictions: tuple[str, ...]
    safe_provenance: tuple[SafeAuthorizedProvenance, ...]  # empty unless requested and wholly authorized

class AuthorizedMemoryLink:
    memory_id: UUID

class ActiveMemoryHistory:
    memory_id: UUID
    version: int
    standing: Literal[MemoryStanding.ACTIVE]
    source: AcceptedReportSource
    projection: AdmittedReportProjectionV1
    admitted_by_id: int
    admitted_at: datetime
    predecessor: AuthorizedMemoryLink | None
    safe_provenance: tuple[SafeAuthorizedProvenance, ...]

class WithdrawnMemoryHistory:
    memory_id: UUID
    version: int
    standing: Literal[MemoryStanding.WITHDRAWN]
    source: AcceptedReportSource
    projection: AdmittedReportProjectionV1
    admitted_by_id: int
    admitted_at: datetime
    withdrawn_by_id: int
    withdrawn_at: datetime
    withdrawal_reason: str
    predecessor: AuthorizedMemoryLink | None
    safe_provenance: tuple[SafeAuthorizedProvenance, ...]

class SupersededMemoryHistory:
    memory_id: UUID
    version: int
    standing: Literal[MemoryStanding.SUPERSEDED]
    source: AcceptedReportSource
    projection: AdmittedReportProjectionV1
    admitted_by_id: int
    admitted_at: datetime
    superseded_by_id: int
    superseded_at: datetime
    supersession_reason: str
    predecessor: AuthorizedMemoryLink | None
    replacement: AuthorizedMemoryLink | None
    safe_provenance: tuple[SafeAuthorizedProvenance, ...]

HistoricalMemoryDetail = ActiveMemoryHistory | WithdrawnMemoryHistory | SupersededMemoryHistory

class GetActiveSuccess:
    outcome: Literal["success"]
    item: ActiveMemoryDetail

class ListActiveSuccess:
    outcome: Literal["success"]
    page: ActiveMemoryPage

class InspectHistorySuccess:
    outcome: Literal["success"]
    item: HistoricalMemoryDetail
```

Active history has admission fields only and no withdrawal, supersession, or
replacement field. Withdrawn history requires exactly the withdrawal triplet
and has no supersession/replacement field. Superseded history requires exactly
the supersession triplet and has a `replacement` disclosure slot.

`predecessor` and `replacement` are `AuthorizedMemoryLink | None`: a UUID is
present only when the corresponding include flag is true and the linked memory
is independently authorized under `INSPECT_HISTORY`. `None` deliberately means
either no link, not requested, or protected omission; those states are not
distinguished. Thus the DTO never forces disclosure of a linked identity. Safe
provenance is empty unless requested and wholly authorized. Required source,
admitting-Human, and transition-Human identities are all-or-nothing: denial
protects the complete historical result.

## 10. Canonical Uniqueness and Idempotency

The database enforces:

```text
UNIQUE (organization_id, source_report_id, source_accepted_version)
```

Application admission resolves idempotency before insert but treats the unique
constraint as authoritative under races.

- same actor/Organization/operation/idempotency ID and same canonical request
  fingerprint with completed result: reauthorize source and memory, then replay
  the bounded stored result;
- same key pending or different fingerprint: idempotency conflict;
- new key for an already admitted source: return duplicate-source only if both
  source and existing memory are authorized, otherwise protected-not-found;
- concurrent different keys: exactly one insert wins; loser follows the same
  protected duplicate rule after rollback;
- rollback removes reservation and all success-side effects;
- idempotency result contains only the exact operation-specific fields declared
  by `MemoryStoredResultV1`; row metadata carries schema version and completion
  time—never projection or provenance plaintext.

The persistence representation is exactly `MemoryStoredResultV1` in §15.1,
serialized as a closed JSON object with its `result_type` discriminator and no
unknown keys. Its canonical UTF-8 JSON is at most 1 KiB. The idempotency key and
table `operation` column store only the unversioned command operation. The JSON
discriminator is separately versioned. The exact mapping is:

| `operation` column/key | `safe_result.result_type` |
|---|---|
| `admit` | `admit.v1` |
| `withdraw` | `withdraw.v1` |
| `create_successor` | `create_successor.v1` |
| `supersede` | `supersede.v1` |

The operation column is never compared for textual equality with the versioned
discriminator. Instead, persistence validation applies this closed mapping and
rejects every other operation/discriminator pair. `result_schema_version` is
exactly 1.
The row fingerprint is the lowercase SHA-256 of the canonical request described
above and is immutable after reservation.

Reconstruction is mechanical and uses no current Aggregate representation:

- `StoredAdmissionResultV1` reconstructs `AdmissionSuccess`, rebuilding
  `AcceptedReportSource` only from stored report/version plus the source digest
  reauthorized from the canonical accepted report;
- `StoredWithdrawalResultV1` reconstructs `WithdrawalSuccess` field-for-field;
- `StoredSuccessorResultV1` reconstructs `CreateSuccessorSuccess`, rebuilding
  its source as above;
- `StoredSupersessionResultV1` reconstructs `SupersessionSuccess` field-for-
  field using the replacement version/standing observed by the original command.

Before completed replay, the service repeats current operation-specific memory,
source, scope, audience, predecessor/replacement, and provenance authorization.
It then returns the original stored result even if the affected memory has since
made a legal later terminal transition or another Aggregate version has
advanced; current state is never substituted into the replay. Revoked authority
returns the protected result and produces no side effect. A different
fingerprint or operation for the same key returns idempotency-conflict; a
pending row also conflicts. Stored results prohibit projection/content,
manifest/provenance, rationale/reason, audience, restrictions, Audit/event data,
diagnostics, exception text, credentials, and authorization facts.

Request fingerprints are SHA-256 of canonical closed command input excluding
server timestamps and including actor, Organization, operation, scope, source,
predecessor/replacement, expected versions, audience, restrictions, and reason.

## 11. Authorization Matrix

Current V1 role vocabulary is `admin` and `engineer`. Every row additionally
requires active User, active Organization, enabled selected membership, same
Organization, active Workspace, owning Project, exact source visibility, and
scope match.

| Operation | Additional authority |
|---|---|
| admit | `admin`, or `engineer` who is accepted report owner and Project/Workspace owner or primary assignee |
| get active | `admin`, or authorized Workspace member/owner/assignee within audience when audience is non-empty |
| list active | same as get active; only authorized items contribute to totals |
| inspect history | `admin`, or admitting Human who still satisfies current source and Workspace/Project authority |
| create successor | admit authority for replacement plus inspect-history authority for predecessor |
| withdraw | `admin`, or admitting Human who still has admit authority for the source scope |
| supersede | admit authority for replacement and withdraw authority for predecessor |
| governance audit | `admin` only, plus current source visibility; grants no ordinary reuse |

Technical Report acceptance alone, read visibility alone, membership alone, or
client role claims never authorize admission.

Audience is an optional immutable allow-list of actor IDs. Empty means all
otherwise-authorized actors in scope. Every listed actor must have active same-
Organization membership and source-compatible scope at admission. Audience can
only narrow authorization and never grants access independently.

```python
@dataclass(frozen=True, slots=True)
class MemoryAuthorizationRequest:
    actor: MemoryActor
    operation: MemoryOperation
    scope: MemoryScope
    memory_id: UUID | None
    source: AcceptedReportSource | None
    predecessor_memory_id: UUID | None
    replacement_memory_id: UUID | None
    audience_actor_ids: tuple[int, ...]

@dataclass(frozen=True, slots=True)
class MemoryFinalRecheckRequest:
    authorization: MemoryAuthorizationRequest
    expected_memory_version: int | None
    expected_predecessor_version: int | None
    expected_replacement_version: int | None
    expected_source_snapshot_digest: str | None
```

Fields not applicable to the selected operation must be null/empty; required
operation subjects must be present. The policy rejects incoherent shapes before
lookup and evaluates only the selected operation's matrix row. It cannot infer
authority from another operation.

## 12. Source Visibility and Final Recheck

The canonical adapter exposes:

```python
class AcceptedReportProjection:
    source: AcceptedReportSource
    owner_id: int
    scope: MemoryScope
    snapshot: TechnicalReportAcceptedSnapshot

class AcceptedReportReader(Protocol):
    def read_authorized_accepted(
        self, actor: MemoryActor, source: AcceptedReportSource
    ) -> AcceptedReportProjection | ProtectedNotFound | Unavailable: ...
```

It privately translates `MemoryActor` to `TechnicalReportActor`, calls the
canonical application service, requires lifecycle accepted, exact aggregate
version and snapshot digest, and maps canonical authorization denial to
protected-not-found. It does not expose the canonical UoW.

Immediately before a memory command compare-and-change/insert, application
repeats this canonical read. Within the memory UoW Session, the final-recheck
policy locks and validates current User, Organization, membership, Workspace,
Project, Workspace membership/ownership/assignment, operation authority,
audience actors, and memory rows. The returned immutable accepted snapshot must
equal the earlier source identity/version/digest and projected digest.

Any mismatch, revocation, unavailability, version change, digest change, or
scope change causes complete rollback. Accepted Technical Report immutability
means its content cannot change after the canonical digest check; shared mutable
authority predicates are locked in the memory transaction.

## 13. Source Revocation and Protected Disclosure

Every read, replay, lineage resolution, count, and command requires a current
canonical source read plus memory authorization. If source access is revoked or
the canonical service is unavailable:

- active content and summary are not returned;
- the retained snapshot cannot act as fallback authority;
- the item contributes to no visible item or disclosed count;
- lineage, source, replacement, actor, and provenance identities are omitted;
- ordinary denial is protected-not-found;
- dependency failure is payload-free unavailable only where distinguishing it
  cannot reveal protected existence.

Governance-audit access does not bypass current source visibility. There is no
V1 privileged disclosure path around source revocation.

## 14. Query and Pagination Contract

Only active memory is available through ordinary listing.

- page size: 1–100, default 50;
- canonical order: `(admitted_at DESC, memory_id ASC)`;
- filters: exact Workspace required; optional exact Project and purpose;
- filters apply before candidate authorization, visible-page construction, and
  pagination;
- no full-text, semantic, vector, similarity, relevance, graph, provenance-body,
  or arbitrary metadata filter;
- repository page reads at most `page_size + 1` candidate rows per bounded
  continuation round;
- current repository reality provides only the canonical single-report
  authorized read, so application may perform at most 100 such reads per
  request and never more than one per candidate memory identity;
- no additional read occurs per projection field or provenance entry;
- at most 10 candidate rounds per request and at most 100 total candidate rows;
  reaching either bound returns the safe page accumulated so far with an
  authenticated continuation rather than scanning further;
- hidden/global totals are prohibited.

The continuation anchor is the canonical ordering key of the **last evaluated
candidate**, `(admitted_at, memory_id)`, whether that candidate was returned or
omitted after current authorization. It is never the last returned item. For
descending-time/ascending-ID order, the next repository predicate is strictly:

```text
admitted_at < anchor.admitted_at
OR (admitted_at = anchor.admitted_at AND id > anchor.memory_id)
```

The application advances the anchor once, only after the candidate's complete
authorization decision. If a candidate is denied it still advances the anchor;
if the scan/call bound is reached, the continuation encodes that last evaluated
key. Thus omitted candidates cannot be revisited, returned candidates cannot be
duplicated, and candidates after the anchor cannot be skipped. If no candidate
was evaluated there is no new continuation. A repository page may overlap only
for internal look-ahead; the strict predicate prevents overlap from entering a
later application page.

Continuation is opaque, authenticated, versioned, expires after 15 minutes,
and binds actor, Organization, scope, filters, page size, the last-evaluated
ordering anchor, and query fingerprint. Replay reauthorizes everything. Tamper, expiry, actor/scope
mismatch, or unsupported version returns payload-free invalid-request.

```python
class ActiveMemoryPage:
    items: tuple[ActiveMemorySummary, ...]
    visible_total: int
    next_continuation: str | None
```

`visible_total == len(items)`. V1 calculates and discloses no authorized,
filtered, hidden-candidate, global, or historical total. Continuation indicates
only that bounded processing may continue; it contains no count and grants no
access.

## 15. Ports and Dependency Direction

### 15.1 Inward Ports

```python
@dataclass(frozen=True, slots=True)
class MemoryOrderingAnchor:
    admitted_at: datetime
    memory_id: UUID

@dataclass(frozen=True, slots=True)
class ActiveMemoryCriteria:
    organization_id: UUID
    workspace_id: int
    project_id: int | None
    purpose: TechnicalReportPurpose | None
    anchor: MemoryOrderingAnchor | None
    candidate_limit: int             # 1..101

@dataclass(frozen=True, slots=True)
class MemoryCandidatePage:
    items: tuple[OrganizationalMemory, ...]  # 0..candidate_limit, canonical order
    has_more: bool

@dataclass(frozen=True, slots=True)
class MemoryIdempotencyKey:
    organization_id: UUID
    actor_id: int
    operation: Literal["admit", "withdraw", "create_successor", "supersede"]
    idempotency_id: UUID

@dataclass(frozen=True, slots=True)
class StoredAdmissionResultV1:
    result_type: Literal["admit.v1"]
    memory_id: UUID
    version: Literal[1]
    standing: Literal["active"]
    source_report_id: UUID
    source_accepted_version: int

@dataclass(frozen=True, slots=True)
class StoredWithdrawalResultV1:
    result_type: Literal["withdraw.v1"]
    memory_id: UUID
    result_version: int
    standing: Literal["withdrawn"]
    withdrawn_at: datetime

@dataclass(frozen=True, slots=True)
class StoredSuccessorResultV1:
    result_type: Literal["create_successor.v1"]
    memory_id: UUID
    version: Literal[1]
    standing: Literal["active"]
    source_report_id: UUID
    source_accepted_version: int
    predecessor_memory_id: UUID

@dataclass(frozen=True, slots=True)
class StoredSupersessionResultV1:
    result_type: Literal["supersede.v1"]
    predecessor_memory_id: UUID
    predecessor_result_version: int
    predecessor_standing: Literal["superseded"]
    replacement_memory_id: UUID
    replacement_version_at_command: int
    replacement_standing: Literal["active"]
    superseded_at: datetime

MemoryStoredResultV1 = (
    StoredAdmissionResultV1 | StoredWithdrawalResultV1 |
    StoredSuccessorResultV1 | StoredSupersessionResultV1
)

@dataclass(frozen=True, slots=True)
class MemoryIdempotencyMiss:
    state: Literal["missing"]

@dataclass(frozen=True, slots=True)
class MemoryIdempotencyPending:
    state: Literal["pending"]

@dataclass(frozen=True, slots=True)
class MemoryIdempotencyCompleted:
    state: Literal["completed"]
    request_fingerprint: str
    result_schema_version: Literal[1]
    result: MemoryStoredResultV1

MemoryIdempotencyLookup = MemoryIdempotencyMiss | MemoryIdempotencyPending | MemoryIdempotencyCompleted

@dataclass(frozen=True, slots=True)
class MemoryEventPayloadV1:
    memory_id: UUID
    aggregate_version: int
    organization_id: UUID
    workspace_id: int
    project_id: int | None
    standing: MemoryStanding
    actor_id: int
    occurred_at: datetime
    command_id: UUID
    correlation_id: UUID
    causation_id: UUID
    source_report_id: UUID
    source_accepted_version: int
    predecessor_memory_id: UUID | None
    replacement_memory_id: UUID | None
    provenance_entry_count: int

@dataclass(frozen=True, slots=True)
class MemoryOutboxRecord:
    event_id: UUID
    memory_id: UUID
    aggregate_version: int
    event_type: Literal["ORGANIZATIONAL_MEMORY_ADMITTED", "ORGANIZATIONAL_MEMORY_WITHDRAWN", "ORGANIZATIONAL_MEMORY_SUPERSEDED"]
    payload_schema_version: Literal[1]
    payload: MemoryEventPayloadV1
    occurred_at: datetime
    created_at: datetime

class OrganizationalMemoryRepository(Protocol):
    def add(self, memory: OrganizationalMemory) -> None: ...
    def get_scoped(self, memory_id: UUID, organization_id: UUID) -> OrganizationalMemory | None: ...
    def get_by_source(self, source: AcceptedReportSource, organization_id: UUID) -> OrganizationalMemory | None: ...
    def persist_standing_expected_version(self, memory: OrganizationalMemory, expected_version: int) -> bool: ...
    def list_active(self, criteria: ActiveMemoryCriteria) -> MemoryCandidatePage: ...
    def append_history(self, record: MemoryStandingHistoryRecord) -> None: ...

class MemoryAuthorizationPolicy(Protocol):
    def require(self, request: MemoryAuthorizationRequest) -> None: ...  # raises closed denial

class MemoryFinalRecheckPolicy(Protocol):
    def require_current(self, request: MemoryFinalRecheckRequest) -> None: ...  # locks shared predicates

class MemoryAuditRecorder(Protocol):
    def record(self, record: MemoryAuditRecord) -> None: ...
class MemoryRejectionAuditRecorder(Protocol):
    def permit_after_authoritative_rollback(self) -> None: ...
    def record_rejection(self, record: MemoryRejectionAuditRecord) -> None: ...
class MemoryDomainEventRecorder(Protocol):
    def record(self, records: tuple[MemoryOutboxRecord, ...]) -> None: ...
class MemoryIdempotencyStore(Protocol):
    def find(self, key: MemoryIdempotencyKey) -> MemoryIdempotencyLookup: ...
    def reserve(self, key: MemoryIdempotencyKey, request_fingerprint: str) -> None: ...
    def record_result(self, key: MemoryIdempotencyKey, request_fingerprint: str, result: MemoryStoredResultV1) -> None: ...
class MemoryClock(Protocol):
    def now(self) -> datetime: ...

class OrganizationalMemoryUnitOfWork(Protocol):
    memories: OrganizationalMemoryRepository
    authorization: MemoryAuthorizationPolicy
    final_recheck: MemoryFinalRecheckPolicy
    audit: MemoryAuditRecorder
    domain_events: MemoryDomainEventRecorder
    idempotency: MemoryIdempotencyStore
    def __enter__(self) -> OrganizationalMemoryUnitOfWork: ...
    def __exit__(self, exc_type, exc_value, traceback) -> bool | None: ...
    def flush(self) -> None: ...
    def commit(self) -> None: ...
    def rollback(self) -> None: ...
```

Root repository, final-recheck policy, success Audit, standing history, outbox,
and idempotency collaborators share exactly the memory UoW Session.
Repositories/recorders flush or stage but never commit. The rejection-Audit
recorder is deliberately outside this UoW and may open its bounded transaction
only after `rollback()` completes. Canonical reads remain outside ownership of
the memory UoW and enter through the declared application adapters only.

### 15.2 Application Service

```python
class OrganizationalMemoryService(Protocol):
    def admit(self, command: AdmitAcceptedReport) -> AdmitResult: ...
    def get_active(self, actor: MemoryActor, request: GetActiveMemory) -> GetActiveResult: ...
    def list_active(self, actor: MemoryActor, request: ListActiveMemory) -> ListActiveResult: ...
    def inspect_history(self, actor: MemoryActor, request: InspectMemoryHistory) -> InspectHistoryResult: ...
    def create_successor(self, command: CreateMemorySuccessor) -> CreateSuccessorResult: ...
    def withdraw(self, command: WithdrawMemory) -> WithdrawResult: ...
    def supersede(self, command: SupersedeMemory) -> SupersedeResult: ...
```

The application service owns orchestration order, not Aggregate invariants or
transport mapping. Authorization precedes source/memory disclosure. Commands
perform final recheck immediately before persistence and commit.
Its request-scoped composition contains exactly an `AcceptedReportReader`,
`MemoryProvenanceAuthorizer`, memory-UoW factory, and associated post-rollback
rejection-Audit recorder. Canonical readers finish their own read-only UoWs;
they never participate in or commit the memory transaction.

### 15.3 Transport

Transport authenticates, derives Organization context, validates strict request
shape and bounds, obtains request-scoped application composition, invokes one
service method, and serializes the closed result. It contains no SQL,
authorization rule, snapshot projection, standing transition, transaction,
digest, or idempotency logic.

Exact HTTP methods/routes/status mappings remain an Implementation Plan/API
surface decision within these closed outcomes; no DELETE or generic update
route is permitted.

## 16. Persistence Contract

### 16.1 Exact Tables

`organizational_memories`:

| Column | PostgreSQL type | Null/default | Constraint |
|---|---|---|---|
| `id` | `uuid` | NOT NULL / no DB default | primary key |
| `organization_id` | `uuid` | NOT NULL | FK `organizations.id` RESTRICT |
| `workspace_id` | `bigint` | NOT NULL | positive; FK `workspaces.id` RESTRICT |
| `project_id` | `bigint` | NULL | positive; FK `projects.id` RESTRICT |
| `version` | `bigint` | NOT NULL / `1` | positive |
| `standing` | `varchar(16)` | NOT NULL / `'active'` | closed standing check |
| `source_report_id` | `uuid` | NOT NULL | FK `technical_reports.id` RESTRICT |
| `source_accepted_version` | `bigint` | NOT NULL | positive |
| `source_snapshot_digest` | `char(64)` | NOT NULL | lowercase hex SHA-256 |
| `projection_contract` | `varchar(64)` | NOT NULL | exact V1 literal |
| `projection` | `jsonb` | NOT NULL | closed V1 object, <=256 KiB |
| `projection_digest` | `char(64)` | NOT NULL | lowercase hex SHA-256 |
| `manifest` | `jsonb` | NOT NULL | closed V1 object, <=128 KiB |
| `provenance_digest` | `char(64)` | NOT NULL | lowercase hex SHA-256 |
| `admitted_by_id` | `bigint` | NOT NULL | positive; FK `users.id` RESTRICT |
| `admitted_at` | `timestamptz` | NOT NULL | UTC instant |
| `admission_rationale` | `varchar(2000)` | NOT NULL | normalized, nonblank, no forbidden controls |
| `audience_actor_ids` | `bigint[]` | NOT NULL / `'{}'` | <=100, positive, sorted, unique |
| `reuse_restrictions` | `jsonb` | NOT NULL / `'[]'` | string array <=32, item <=2000 |
| `predecessor_memory_id` | `uuid` | NULL | self-FK RESTRICT, not self |
| `withdrawn_by_id` | `bigint` | NULL | positive; FK `users.id` RESTRICT |
| `withdrawn_at` | `timestamptz` | NULL | coherent withdrawn triplet |
| `withdrawal_reason` | `varchar(2000)` | NULL | normalized/nonblank when present |
| `superseded_by_id` | `bigint` | NULL | positive; FK `users.id` RESTRICT |
| `superseded_at` | `timestamptz` | NULL | coherent superseded triplet |
| `supersession_reason` | `varchar(2000)` | NULL | normalized/nonblank when present |
| `replacement_memory_id` | `uuid` | NULL | self-FK RESTRICT, not self |
| `created_at` | `timestamptz` | NOT NULL | equals admission time |
| `updated_at` | `timestamptz` | NOT NULL | >= created time |

All root columns have no database default unless the table states one.

`organizational_memory_standing_history` is append-only: `event_id uuid` NOT
NULL PK/no default, `memory_id uuid` NOT NULL FK RESTRICT, `organization_id uuid`
NOT NULL FK RESTRICT, `aggregate_version bigint` NOT NULL positive,
`from_standing varchar(16) NULL`, `to_standing varchar(16) NOT NULL`, `actor_id
bigint` NOT NULL positive FK `users.id` RESTRICT, `occurred_at timestamptz` NOT
NULL, `reason varchar(2000)` NOT NULL normalized/nonblank, and
`replacement_memory_id uuid NULL` self-FK RESTRICT. No column has a default.
Unique `(memory_id, aggregate_version)`;
version 1 is `NULL→active`, later rows are exactly `active→withdrawn` or
`active→superseded`. Runtime may INSERT but never UPDATE/DELETE.

`organizational_memory_events_outbox`: `event_id uuid` NOT NULL PK/no default,
`memory_id uuid` NOT NULL FK RESTRICT, `aggregate_version bigint` NOT NULL
positive, `event_type varchar(64)` NOT NULL closed enum,
`payload_schema_version smallint` NOT NULL default 1/check 1, `payload jsonb` NOT
NULL, `occurred_at timestamptz` NOT NULL, `created_at timestamptz` NOT NULL,
`published_at timestamptz NULL`, `attempt_count integer` NOT NULL default 0/check
nonnegative, and `last_error_category varchar(64) NULL` closed operational code.
Unique `(memory_id, aggregate_version, event_type)`; payload is a closed object,
<=8 KiB, and contains only §18 fields. Runtime may INSERT and update only
delivery columns; no dispatch behavior is owned here.

`organizational_memory_idempotency`: `organization_id uuid` NOT NULL FK
RESTRICT, `actor_id bigint` NOT NULL positive FK RESTRICT, `operation
varchar(32)` NOT NULL closed command operation, `idempotency_id uuid` NOT NULL,
`request_fingerprint char(64)` NOT NULL lowercase SHA-256, `status varchar(16)`
NOT NULL default `pending` (`pending|completed`), `result_schema_version
smallint` NOT NULL default 1/check 1, `safe_result jsonb NULL`, `created_at
timestamptz` NOT NULL, `updated_at timestamptz` NOT NULL, `completed_at
timestamptz NULL`; composite PK `(organization_id,
actor_id, operation, idempotency_id)`. Pending requires null result/completion;
completed requires the closed <=1 KiB plaintext-free `MemoryStoredResultV1`
whose discriminator matches `operation` and whose canonical request fingerprint
equals the immutable reservation fingerprint.

Audit uses existing `audit_logs`. Success record shape is operation, actor ID,
Organization, memory ID, previous/result version, standing, source report
ID/version, correlation/command/idempotency IDs, occurred-at, optional safe
predecessor/replacement ID, and provenance-entry count. Rejection Audit is the
closed §18 reason, actor/Organization, operation, correlation/command IDs,
occurred-at, and optional safely-known memory ID only.

### 16.2 Constraints and Indexes

Schema-owner functions validate exact JSON keys/types/nullability, UTF-8 byte
limits, NFC/trim equality, prohibited controls, enum literals, positive non-bool
integers, UTC timestamp strings, contiguous provenance ordinals, manifest count,
projection/source/scope/version equality, and canonical SHA-256 recomputation.
Unknown or missing keys fail. Source/projection/manifest digests must match.

The immutable SQL function boundary is closed as:

```text
organizational_memory_projection_v1_valid(jsonb) -> boolean
organizational_memory_manifest_v1_valid(jsonb) -> boolean
organizational_memory_event_payload_v1_valid(text, jsonb) -> boolean
organizational_memory_idempotency_result_v1_valid(text, jsonb) -> boolean
organizational_memory_canonical_json(jsonb) -> text
organizational_memory_lineage_guard() -> trigger
organizational_memory_root_guard() -> trigger
organizational_memory_history_guard() -> trigger
organizational_memory_side_record_guard() -> trigger
```

Root CHECK constraints invoke projection/manifest validators and compare
`encode(digest(convert_to(canonical_json, 'UTF8'),'sha256'),'hex')` with stored
digests. Outbox/idempotency CHECK constraints invoke their operation/event-
specific closed validators. These functions reject JSON numbers for identifier
fields when non-integral/nonpositive, unknown enum/event/result values, and all
unknown or missing keys; they are schema-owner-owned and not executable or
alterable by runtime.

`organizational_memory_idempotency_result_v1_valid(operation, safe_result)`
accepts an unversioned operation and enforces exactly: `admit→admit.v1`,
`withdraw→withdraw.v1`, `create_successor→create_successor.v1`, and
`supersede→supersede.v1`. It does not compare the two strings directly. A null
or unknown operation, unknown discriminator, cross-paired discriminator,
unknown/missing result key, or result shape not belonging to the mapped variant
returns false and violates the completed-row CHECK constraint.

Unique `(organization_id, source_report_id, source_accepted_version)` is the
canonical admission key. Indexes are active order `(organization_id,
workspace_id, project_id, standing, admitted_at DESC, id ASC)`, predecessor,
replacement, history `(memory_id, aggregate_version)`, pending outbox
`(published_at, created_at, event_id) WHERE published_at IS NULL`, and the
idempotency PK. A partial unique index on `replacement_memory_id WHERE
replacement_memory_id IS NOT NULL` prevents one replacement from superseding
multiple predecessors. FKs never cascade-delete canonical or memory history.

### 16.3 Trigger Predicates and Role Boundary

Schema-owner-owned `organizational_memory_lineage_guard()` is installed as
`a_organizational_memory_lineage_guard BEFORE INSERT OR UPDATE` on the root;
the alphabetic name makes it run before
`b_organizational_memory_root_guard`. On INSERT it validates source Organization/Workspace/
Project against the closed projection and, when a predecessor is present,
locks that row `FOR KEY SHARE` and requires: distinct identity; same
Organization, Workspace, and null-safe Project; different exact source
report/version; and successor audience no broader than predecessor audience
(`predecessor audience = {}` permits any narrower audience; otherwise successor
must be nonempty and an array subset). The single nullable predecessor column
is the only V1 predecessor representation, so each successor has cardinality
zero or one. Because predecessor is immutable after INSERT, points only to an
already-existing distinct row, and new IDs are application-generated, a cycle
cannot be inserted or formed later.

On an `active→superseded` UPDATE the function locks predecessor and proposed
replacement in UUID order `FOR UPDATE` and requires: predecessor `OLD.id` is
currently active; replacement exists and is active; identities differ;
`replacement.predecessor_memory_id = OLD.id`; same Organization, Workspace,
null-safe Project, and audience-not-broader rule; different source report/
version; and no other root names that replacement as superseding replacement.
Withdrawal requires replacement null. Missing, terminal, cross-Organization,
cross-scope, audience-widening, wrongly linked, reused, or self replacements
raise and abort the statement/transaction.

Schema-owner-owned `organizational_memory_root_guard()` is installed as
`b_organizational_memory_root_guard BEFORE INSERT OR UPDATE OR DELETE` and rejects DELETE and every
UPDATE except one row transition satisfying: old standing active; new standing
withdrawn or superseded; version exactly old+1; all immutable columns bytewise
unchanged; old transition fields all null; only the applicable terminal fields
become non-null; incompatible terminal fields remain null; replacement is
required only for superseded; `updated_at > old.updated_at`. Terminal rows are
never updateable. Both triggers apply to direct SQL, so it has no weaker path.

For INSERT the root guard requires version 1, standing active, every transition/
replacement field null, `created_at = updated_at = admitted_at`, closed source/
projection/manifest coherence, and the lineage-guard result. Consequently a
direct INSERT cannot manufacture withdrawn/superseded state or bypass successor
scope/audience rules.

`organizational_memory_history_guard()` is installed `BEFORE INSERT OR UPDATE
OR DELETE` and rejects all history UPDATE/DELETE. On
INSERT it locks the referenced root `FOR KEY SHARE`, requires identical
Organization/version/current standing, requires `NULL→active` only at version
1, requires the applicable `active→withdrawn|superseded` record at the root's
current terminal version, and requires replacement null except for superseded,
where it equals the root replacement. Arbitrary or out-of-order history cannot
be inserted. `organizational_memory_side_record_guard()` prevents mutation of
outbox payload/identity and completed idempotency identity/fingerprint/result;
only declared delivery fields may change.

Migration/schema ownership uses `ALEMBIC_DATABASE_URL` and role `satco` in the
current topology; runtime uses `DATABASE_*` and `satco_runtime`. They must be
distinct. `satco_runtime` is non-owner, non-superuser, `NOCREATEDB`,
`NOCREATEROLE`, `NOINHERIT`, `NOBYPASSRLS`; it receives schema USAGE, root
SELECT/INSERT plus UPDATE only of version/standing/applicable transition fields/
updated_at, history INSERT/SELECT, outbox INSERT/SELECT plus delivery-column
UPDATE, idempotency INSERT/SELECT plus status/result/update timestamps UPDATE,
and shared Audit INSERT/SELECT. It receives no DELETE, DDL, ownership, trigger
disable, or function alteration/execution grant. Deployment/startup fails if
roles coincide, grants/ownership differ, or required triggers are absent or
disabled. Direct SQL, ORM bulk operations, repositories, and normal flushes are
subject to identical guards.

## 17. Transaction Sequencing

### 17.1 Admission/Successor

1. validate closed input;
2. trusted actor/Organization and operation authority precheck;
3. canonical authorized accepted-report read;
4. authorize/resolve every canonical material provenance identity through
   `MemoryProvenanceAuthorizer`; any denial/failure ends the whole operation;
5. construct deterministic projection/manifest and verify digests/limits;
6. protected predecessor resolution when supplied;
7. enter memory UoW;
8. recheck operation authority and source-compatible shared scope;
9. idempotency lookup/reservation;
10. protected uniqueness lookup;
11. repeat canonical source and provenance authorization reads;
12. lock/final-recheck shared mutable predicates and predecessor;
13. construct/add Aggregate and append standing-history admission row;
14. construct the operation-specific `MemoryStoredResultV1`; stage success
    Audit, Domain Event/outbox, and that exact idempotency result;
15. flush constraints and commit once.

Any failure rolls back steps 9–14. Unique races are translated only after
rollback and protected reauthorization.

### 17.2 Withdrawal

Authorize and resolve subject; enter UoW; reauthorize; idempotency; lock subject;
repeat source authorization; final shared-authority recheck; compare expected
version; transition Aggregate; append history; stage success Audit, outbox, and
completed idempotency result; flush; commit once.
The standing-history row is appended in the same transaction.

### 17.3 Supersession

Authorize predecessor and replacement independently; enter UoW; reauthorize;
idempotency; lock records by UUID ascending; repeat both source reads; final
shared-authority/scope/lineage recheck; compare both expected versions; change
predecessor only; append history; stage success Audit, outbox, and completed
idempotency result; flush; commit once.
The predecessor standing-history row is appended in the same transaction.

### 17.4 Reads and Failure Ordering

`get_active`/reuse and `inspect_history` perform trusted actor/Organization
precheck, scoped memory lookup, memory operation authorization, current source
read, optional linked-memory authorization, then the context-specific
provenance authorization batches when requested. Only after every required
check succeeds is a DTO constructed. `list_active` evaluates each candidate in
canonical order using memory authorization then current source read and advances
the last-evaluated anchor after that decision; it never reads provenance.

Every command exception triggers UoW rollback before unique/conflict translation
or rejection Audit. No success Audit/outbox/idempotency/history record survives
rollback. Only a closed security/authority rejection permits the associated
post-rollback recorder; validation, version, idempotency, dependency, digest,
and database failures do not. Rejection-Audit failure preserves the original
protected result.

For a completed idempotency lookup, no mutation path runs. The application
validates fingerprint equality, reauthorizes every identity required by the
original operation using current source/provenance/memory/lineage authority,
then mechanically reconstructs the outward success from the stored V1 payload.
Denial returns protected-not-found without Audit/outbox/history/idempotency
mutation; mismatch/pending returns idempotency-conflict. Later legal Aggregate
state/version changes do not alter the original replay payload.

## 18. Audit, Events, and Rollback

Success Audit and outbox are atomic with authoritative memory changes. Closed
event types are:

- `ORGANIZATIONAL_MEMORY_ADMITTED`;
- `ORGANIZATIONAL_MEMORY_WITHDRAWN`;
- `ORGANIZATIONAL_MEMORY_SUPERSEDED`.

```python
@dataclass(frozen=True, slots=True)
class MemoryAuditRecord:
    operation: MemoryOperation
    actor_id: int
    organization_id: UUID
    memory_id: UUID
    previous_version: int | None
    result_version: int
    standing: MemoryStanding
    source_report_id: UUID
    source_accepted_version: int
    correlation_id: UUID
    command_id: UUID
    idempotency_id: UUID
    occurred_at: datetime
    predecessor_memory_id: UUID | None
    replacement_memory_id: UUID | None
    provenance_entry_count: int

class MemoryRejectionReason(StrEnum):
    INACTIVE_ACTOR = "inactive_actor"
    INACTIVE_ORGANIZATION = "inactive_organization"
    MEMBERSHIP_DENIED = "membership_denied"
    CROSS_ORGANIZATION = "cross_organization"
    SCOPE_DENIED = "scope_denied"
    SOURCE_DENIED = "source_denied"
    PROVENANCE_DENIED = "provenance_denied"
    OPERATION_DENIED = "operation_denied"
    AUDIENCE_DENIED = "audience_denied"
    REVOKED_AUTHORITY = "revoked_authority"
    PROTECTED_LINEAGE_DENIED = "protected_lineage_denied"
    ACCEPTED_STATE_INTEGRITY_FAILURE = "accepted_state_integrity_failure"

@dataclass(frozen=True, slots=True)
class MemoryRejectionAuditRecord:
    operation: MemoryOperation
    reason: MemoryRejectionReason
    actor_id: int
    organization_id: UUID
    correlation_id: UUID
    command_id: UUID
    occurred_at: datetime
    memory_id: UUID | None

@dataclass(frozen=True, slots=True)
class MemoryDomainEvent:
    event_id: UUID
    event_type: Literal["ORGANIZATIONAL_MEMORY_ADMITTED", "ORGANIZATIONAL_MEMORY_WITHDRAWN", "ORGANIZATIONAL_MEMORY_SUPERSEDED"]
    payload_schema_version: Literal[1]
    memory_id: UUID
    aggregate_version: int
    organization_id: UUID
    workspace_id: int
    project_id: int | None
    standing: MemoryStanding
    actor_id: int
    occurred_at: datetime
    command_id: UUID
    correlation_id: UUID
    causation_id: UUID
    source_report_id: UUID
    source_accepted_version: int
    predecessor_memory_id: UUID | None
    replacement_memory_id: UUID | None
    provenance_entry_count: int
```

### 18.1 Exact Shared Audit Mapping

Organizational Memory creates no Audit table or incompatible Audit model. Its
recorder stages the existing `app.models.audit_log.AuditLog` fields exactly:

| Existing field | Successful command value | Post-rollback rejection value |
|---|---|---|
| `user_id` | `record.actor_id` | `record.actor_id` |
| `action` | exact `MemoryOperation.value` | exact `MemoryOperation.value` |
| `entity` | `"ORGANIZATIONAL_MEMORY"` | `"ORGANIZATIONAL_MEMORY"` |
| `entity_id` | `NULL` | `NULL` |
| `entity_uuid` | `record.memory_id` | safely-known `record.memory_id`, otherwise `NULL` |
| `details` | closed success object below | closed rejection object below |
| `created_at` | `record.occurred_at` | `record.occurred_at` |

Success `details` has exactly: `outcome="succeeded"`, `organization_id` as
canonical UUID text, `previous_version`, `result_version`, `standing`,
`source_report_id` as UUID text, `source_accepted_version`, `command_id`,
`correlation_id`, `idempotency_id`, optional safely-authorized predecessor and
replacement UUID text, and `provenance_entry_count`. Rejection `details` has
exactly: `outcome="rejected"`, closed `MemoryRejectionReason.value`,
`organization_id`, `command_id`, and `correlation_id`.

Audit never stores projection/content text, provenance/locator body, admission
or transition rationale, reuse restrictions, audience, source descriptions,
denial diagnostics, exception text, credentials, or dependency state. Success
Audit is staged in the authoritative memory UoW and any insert failure rolls
back root/history/outbox/idempotency together. Rejection processing first calls
the associated recorder's rollback permit only after authoritative rollback,
then inserts and commits one `AuditLog` in its own Session. It records exactly
one closed security/authority rejection. If that insert/commit fails, it rolls
back/closes its Session and returns the original protected result unchanged;
Audit failure is never substituted or exposed.

Payload fields are event schema version, memory ID/version, Organization,
Workspace, optional Project, standing, actor, occurred-at, command/correlation/
causation IDs, source report ID/version, optional predecessor/replacement ID,
and provenance-entry count. No projection, rationale, restrictions, source
plaintext, provenance body, or protected audience enters events.

Only authorization/security rejections use a separate post-authoritative-
rollback Audit transaction with closed reasons: inactive actor, inactive
Organization, membership denied, cross-Organization, scope denied, source
denied, provenance denied, operation denied, audience denied, revoked authority, protected lineage
denied, and accepted-state integrity failure. Optional memory ID is recorded
only when safely known. Rejection-Audit failure preserves the original result.

## 19. Failure Semantics

- Validation precedes persistence but never reveals protected existence.
- Authorization failure rolls back before bounded rejection Audit.
- Version conflict changes nothing.
- Unique conflict changes nothing and is protected before translation.
- Source unavailable creates no memory side effect.
- Digest or projection mismatch creates no memory side effect.
- Audit/outbox/idempotency failure rolls back the command.
- No failed command may leave Aggregate, outbox, idempotency, success Audit, or
  partial transition state.
- Logs and diagnostics use correlation/command IDs and stable categories only.

## 20. Verification Matrix

| Invariant | Required executable evidence |
|---|---|
| exact source class | draft/non-report/unsupported source rejection |
| acceptance distinct from admission | accepted report absent from memory until explicit command |
| projection parity | every field equals canonical snapshot; mutation/paraphrase/omission/reorder negative cases |
| provenance authority | exact Capture arguments; Evidence `ReadEvidence`; Object `ReadEngineeringObject`; Relationship `ReadEngineeringRelationship`; response-context mismatch negatives; noncanonical-class admission rejection; 100-item/three-batch/256-total bounds |
| provenance all-or-nothing | mixed allowed/denied, missing, cross-scope, dependency failure, partial-batch failure; no partial identity/cardinality disclosure |
| normalization/digest | canonical bytes golden vectors, Unicode/UUID/time/enum/null/list vectors, digest mismatch |
| size/cardinality | exact boundaries and over-limit rollback |
| canonical uniqueness | sequential duplicate, concurrent different-key race, cross-Organization independence |
| stored replay shapes | each valid `admit→admit.v1`, `withdraw→withdraw.v1`, `create_successor→create_successor.v1`, `supersede→supersede.v1` pair succeeds; every cross-pair/unknown pair fails; persistence and replay use the same map; closed JSON golden/negative vectors, <=1 KiB, plaintext exclusions, and previously resolved replay/DB/UoW regressions |
| idempotency | exact reconstruction for all mutations; replay after later lifecycle/version change; current-authority denial; pending/different fingerprint; rollback reservation |
| standing | active-only commands; terminal withdrawal/supersession; prohibited restore/update/delete |
| lineage | zero/one predecessor, self/cross-scope denial, successor does not supersede |
| database lineage guard | direct-SQL self/missing/cross-Organization/cross-Workspace/cross-Project/audience-widening/cycle-forming predecessor INSERT rejection |
| database replacement guard | direct-SQL unlinked, reused, cross-scope, terminal, self, wrong-predecessor replacement and terminal UPDATE rejection |
| supersession | both active/authorized, explicit Human command, deterministic lock order, one winner |
| source revocation | admission/read/list/history/replay/withdraw/supersede denial after revocation |
| scope | inactive User/Organization/membership, cross-Organization, Workspace/Project mismatch, audience denial |
| protected outcomes | nonexistent/inaccessible/revoked equivalence; no identity/count/content/standing/timing diagnostic leak |
| operation unions | every operation emits only its declared success/protected variants; payload/cardinality/optionality validation |
| standing-specific history DTOs | active admission-only; withdrawn fields only withdrawn; supersession fields only superseded |
| protected history links | predecessor/replacement requested/absent/authorized/denied matrices; denied and absent both serialize `null` |
| active listing | filters before authorization, deterministic order, continuation tamper/expiry; denied candidate between visible items |
| continuation anchor | last evaluated—not last returned—key at denial and scan bound; strict next predicate proves no skip/duplicate |
| bounded reads | page/candidate rounds/canonical calls bounded; no provenance N+1 |
| snapshot fallback prohibition | source unavailable never serves retained content |
| transaction atomicity | real PostgreSQL failure injection after root/history/Audit/outbox/stored-idempotency stages; exact pre-state restored |
| UoW conformance | every exact repository/idempotency/outbox/Audit method and DTO structurally satisfied; one Session and one commit |
| exact persistence | columns/defaults/nullability/FKs/indexes/closed JSON/array/type/length/control checks and digest coherence |
| optimistic concurrency | stale version and simultaneous withdrawal/supersession one-winner tests |
| shared Audit mapping | exact `AuditLog` user/action/entity/entity_id/entity_uuid/details/created_at mapping for every command and rejection |
| rejection Audit | rollback permit precedes separate insert; closed reason, optional safe target, no plaintext, failure isolation |
| immutability | domain/ORM/direct-SQL update/delete and trigger-disable negative tests |
| standing history | admission and terminal transition append atomically; UPDATE/DELETE denied |
| role separation | schema-owner/runtime identity, grants, ownership, startup fail-closed |
| event contract | exact closed non-plaintext payload and no dispatch authority |
| transport | actual authentication/Organization context, strict DTOs, protected mappings, prohibited routes |
| ownership | no Technical Report repository/Session/UoW exposed to memory service/transport |
| exclusions | prohibited-pattern scans for AI, semantic/vector/graph, alternate sources, publication, UI |
| regression | Technical Report, Journal, EKG, Evidence, auth/Organization, Audit, migration, full backend |

Every material invariant must map to at least one positive and one negative
test where a negative state exists. Concurrency, role, trigger, transaction,
and direct-SQL evidence requires real PostgreSQL.

## 21. Explicitly Prohibited Implementation

- direct Organizational Memory access to Technical Report ORM/repository/table;
- Technical Report mutation or canonical UoW ownership transfer;
- source types other than accepted Technical Report;
- multiple memory Aggregates for one Organization/source/version;
- candidate/draft/published/archived/restored states;
- generic update or physical delete;
- implicit admission, automated admission, or AI authority;
- public publication or cross-Organization sharing;
- semantic/vector search, embeddings, ranking, graph traversal/expansion;
- multi-source synthesis;
- frontend/UI;
- EDS-030 or EDS-031 behavior.

## 22. Repository-Alignment Blocker Assessment

No current blocker is identified for focused re-review:

- canonical authorized report detail supplies exact accepted snapshot and
  integrity data;
- accepted Technical Report content is immutable;
- shared actor/Organization/Workspace/Project predicates can be rechecked and
  locked by the memory-owned authorization policy;
- a private adapter can invoke the canonical service without exposing its
  persistence or UoW.
- existing authorized application-service reads exist for Capture, Evidence,
  Engineering Object, and Engineering Relationship canonical provenance;
  reports containing noncanonical locator provenance are deliberately
  ineligible for V1 admission rather than partially retained or disclosed.

Mandatory implementation stop condition: if canonical `get_report` cannot be
composed request-scoped or cannot return the accepted snapshot/version/digest
without direct repository access, or if any accepted source-visibility
predicate is neither immutable nor safely recheckable through existing shared
authority, Implementation-Plan-034 must return to IDS governance before code.

## 23. Unresolved Questions

None at architecture or implementation-contract level. Concrete module/file
names, migration revision ID, route paths, batch boundaries, and execution
commands belong to Implementation-Plan-034 and authorized manifests; they may
not change these contracts.

## 24. Architecture and EDS Conformance

IDS-034 preserves:

- one dedicated non-source-owning Aggregate;
- exact accepted Technical Report as the sole V1 source;
- explicit Human admission distinct from acceptance/publication;
- deterministic non-transformative snapshot projection;
- one canonical identity per Organization/source/version;
- active→withdrawn|superseded terminal standing;
- zero-or-one predecessor and explicit supersession;
- current source reauthorization and fail-closed revocation;
- immutable history and responsible reuse;
- all PATCH/EDS exclusions.

## 25. Governance State

```text
IDS-034: ACCEPTED / COMPLETE
Initial Independent IDS Review: FAIL — HISTORICAL
First Focused Independent IDS Re-review: FAIL — HISTORICAL
Second Focused Independent IDS Re-review: FAIL — HISTORICAL
Third Focused Independent IDS Re-review: FAIL — HISTORICAL
IDS034-MAJ-01: RESOLVED IN SECOND FOCUSED RE-REVIEW
IDS034-MAJ-02: RESOLVED IN SECOND FOCUSED RE-REVIEW
IDS034-MAJ-03: RESOLVED IN THIRD FOCUSED RE-REVIEW
IDS034-RR-MAJ-01: RESOLVED IN SECOND FOCUSED RE-REVIEW
IDS034-RR-MAJ-02: RESOLVED IN SECOND FOCUSED RE-REVIEW
IDS034-RR-MAJ-03: RESOLVED IN THIRD FOCUSED RE-REVIEW
IDS034-RR2-MAJ-01: RESOLVED IN THIRD FOCUSED RE-REVIEW
IDS034-RR2-MAJ-02: RESOLVED IN FINAL FOCUSED RE-REVIEW
IDS034-RR3-MAJ-01: RESOLVED IN FINAL FOCUSED RE-REVIEW
IDS034-MIN-01: RESOLVED IN FIRST FOCUSED RE-REVIEW
Final Focused Independent IDS Re-review: PASS
Remaining blocking findings: NONE
Human IDS Acceptance: PASS
Implementation Plan authority: GRANTED / EXERCISED
Implementation-Plan-034: ACCEPTED / COMPLETE
Implementation authority: NOT GRANTED
```
