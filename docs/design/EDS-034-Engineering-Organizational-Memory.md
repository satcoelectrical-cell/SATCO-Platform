# EDS-034 — Engineering Organizational Memory

## 1. Document Control

| Field | Value |
|---|---|
| Document ID | EDS-034 |
| Related PATCH | PATCH-034 — Engineering Organizational Memory |
| Status | ACCEPTED / COMPLETE |
| Architecture Review | PASS |
| Human Architecture Acceptance | PASS |
| QG-M1 | PASS |
| EDS design authority | GRANTED |
| Initial Independent EDS Review | FAIL — historical |
| Focused amendment | COMPLETE |
| Focused Independent EDS Re-review | PASS |
| Human EDS Acceptance | PASS |
| IDS-034 authority | GRANTED |
| IDS-034 | ACCEPTED / COMPLETE |
| Independent IDS Review | PASS after focused amendments and final re-review |
| Human IDS Acceptance | PASS |
| Implementation-Plan-034 | ACCEPTED / COMPLETE |
| Implementation authority | NOT GRANTED |
| Date | 2026-08-12 |

## 2. Governing Authorities

EDS-034 is governed by:

1. the SATCO Constitution and Engineering Intelligence Manifesto;
2. accepted ADR-021 Engineering Intelligence Core Business Capability;
3. accepted ADR-023 Human-Accepted AI-Assisted Technical Reports;
4. accepted PATCH-034 and its PASS Architecture Review/QG-M1 assessment;
5. completed PATCH-029 Engineering Journal;
6. completed PATCH-032 Technical Report;
7. completed PATCH-033 Engineering Knowledge Graph Integration;
8. current canonical authentication, Organization, Workspace, Project,
   authorization, Evidence, Audit, transaction, concurrency, idempotency,
   Domain Event, outbox, and PostgreSQL governance boundaries.

If this EDS conflicts with a higher authority, the higher authority prevails
and EDS-034 returns to architecture review. EDS-034 cannot expand PATCH-034.

## 3. Purpose and Architectural Boundary

Engineering Organizational Memory is the canonical capability through which an
authorized Human explicitly admits one exact Human-accepted Technical Report
version into durable, governed organizational reuse.

It is not a cache, index, Journal view, EKG projection, publication channel,
generic document store, or second Technical Report system. Admission creates a
new memory authority record while leaving every source Aggregate unchanged.

Version 1 supports only:

- eligibility resolution for one exact accepted Technical Report version;
- explicit Human admission;
- authorized bounded active-memory retrieval and listing;
- protected historical inspection;
- explicit Human withdrawal;
- successor creation and explicit Human supersession;
- attributable, scope-bound Human engineering reuse.

There is no persistent memory candidate or draft state.

## 4. Architectural Invariants

1. Only an exact Human-accepted Technical Report version is eligible.
2. Technical Report acceptance is neither publication nor memory admission.
3. Admission, withdrawal, and supersession require explicit accountable Human
   authority.
4. Silence, elapsed time, repeated use, publication, Journal membership, EKG
   visibility, AI output, or system processing never changes memory authority.
5. Organizational Memory owns only its Aggregate and memory-specific standing.
6. No memory operation mutates or transfers ownership of a source capability.
7. Admitted representation, admission evidence, source binding, provenance,
   limitations, and prior standing history are immutable.
8. Withdrawn and superseded memory is never current approved knowledge.
9. Lineage alone never means supersession.
10. Authorization precedes existence, identity, field, count, content,
    standing, lineage, replacement, provenance, and reuse disclosure.
11. Cross-Organization admission and reuse are prohibited.
12. Effective disclosure cannot exceed the intersection of memory authority
    and the source-derived confidentiality/scope authority.
13. AI is non-authoritative and cannot admit, withdraw, supersede, publish, or
    reuse memory autonomously.

## 5. Aggregate and Ownership Model

### 5.1 Aggregate Root

`OrganizationalMemory` is a dedicated canonical Aggregate Root. It owns:

- one opaque memory identity;
- Aggregate version for optimistic concurrency;
- Organization identity;
- Workspace identity and optional Project identity inherited from admission;
- the immutable admitted representation;
- exact Technical Report identity, accepted version, and accepted-snapshot
  integrity binding;
- admitting Human identity, admission time, rationale, limitations, audience,
  and authority evidence;
- an immutable source/provenance manifest;
- current memory standing;
- immutable standing-transition history;
- optional predecessor identity owned by the successor;
- optional replacement identity disclosed only through authorized resolution.

The Aggregate does not own Technical Report lifecycle, report content editing,
Evidence, Capture, Engineering Objects, Relationships, Journal state, EKG
projection, source confidentiality policy, or publication authority.

### 5.2 Identity and Version Responsibilities

Within one Organization, one exact Human-accepted Technical Report identity and
accepted version may correspond to at most one canonical OrganizationalMemory
Aggregate. The first successful admission creates that memory identity at
Aggregate version 1. Aggregate version changes only for memory-owned standing
transitions. It is not the Technical Report version and must never be used as
one.

Audience or scope variants never create additional memory Aggregates for the
same accepted source version. Audience and scope are immutable governed
constraints of the single canonical memory record and may narrow, but never
widen, source authority at admission. A repeated exact admission resolves
through idempotent replay or a stable protected existing-state outcome. It
cannot create a competing identity.

Withdrawal, successor linkage, supersession, current-standing queries, and
historical inspection operate on this single canonical memory identity. A
semantic successor necessarily relies on a separately Human-accepted Technical
Report version and therefore has a distinct source-version key and memory
identity.

An exact admitted representation is immutable for the life of that identity.
Any semantic correction or replacement creates a successor memory Aggregate
with a new identity and its own admission decision. No update command may
replace admitted knowledge in place.

### 5.3 Lineage Ownership

The successor owns zero or one predecessor reference. Multiple predecessors
are prohibited in Version 1. Reverse lineage is a derived authorized read.
Creating a successor does not mutate or supersede the predecessor and does not
imply that either record is current.

Explicit supersession is a distinct Human operation that verifies the active
predecessor and eligible active replacement and changes only memory-owned
standing. Replacement identity is protected independently before disclosure.

## 6. Admission Model

### 6.1 Eligibility

The admission source must be:

- a canonical Technical Report;
- in the canonical `accepted` lifecycle;
- bound to the exact Human-accepted report version and immutable accepted
  snapshot;
- visible to the current actor for the admission operation;
- in the same trusted Organization;
- compatible with the requested Workspace, optional Project, audience, and
  confidentiality scope;
- historically resolvable with a coherent accepted provenance manifest.

A draft, missing, inaccessible, inconsistent, or non-historically-resolvable
source is ineligible. Eligibility is not persisted as a memory candidate.

### 6.2 Explicit Human Authority

Admission requires an active authenticated Human, active trusted Organization,
active membership, source visibility, and an operation-specific memory-admit
permission. Client claims cannot establish Organization, membership, role,
source standing, or admission authority.

The Human explicitly confirms:

- the exact source/version;
- the immutable admitted representation;
- admission rationale;
- limitations and applicability;
- audience and scope;
- provenance basis;
- accountability for admission.

Exact role-to-permission mapping is an IDS-034 obligation. EDS-034 establishes
that ordinary source read or report acceptance authority alone is insufficient.

### 6.3 Admission Record

Successful admission atomically creates the Aggregate, admission authority
record, provenance/source manifest, success Audit, required Domain Event/outbox
record, and completed idempotency result. Failure commits none of them.

Security/authority rejection Audit behavior must follow existing accepted
platform rules: bounded, non-plaintext, post-rollback where required, and unable
to replace the original protected outcome if Audit persistence fails.

## 7. Retention Representation Decision

Version 1 retains an **immutable admitted snapshot/representation**, not merely
a live reference to the Technical Report.

The retained snapshot is a closed, deterministic, semantically
non-transformative projection of the exact immutable Human-accepted Technical
Report version. Every projected technical value comes directly from the
accepted snapshot under a closed field-selection rule. Projection may omit
unneeded fields but cannot paraphrase, summarize, infer, combine, reinterpret,
or otherwise change technical meaning.

The admitted snapshot cannot introduce a newly authored conclusion,
recommendation, qualification, rationale, limitation, assumption, or other
technical assertion. Admission rationale, audience, and reuse restrictions are
separately typed governance metadata; they may narrow applicability or reuse
but cannot revise or supplement the accepted technical content. Any new or
changed technical meaning requires a separately Human-accepted Technical Report
version before admission.

Permitted normalization is deterministic and non-semantic only, such as closed
enum encoding, canonical UUID/timestamp representation, Unicode normalization,
and field ordering defined by IDS-034. Normalization cannot change wording,
units, precision, applicability, authority, or interpretation. Memory admission
therefore creates no new engineering authority; it records governed reuse of
authority already established by the exact accepted source version.

The projection includes only the minimum attributable accepted content,
applicability, source-stated limitations, and source context required for
responsible reuse. It excludes unrelated report content, attachments, transient
presentation data, provider data, and source fields not authorized for memory.

The snapshot is bound to a historically resolvable minimized source manifest
containing the exact Technical Report identity/version, accepted-snapshot
identity/digest, admitted-projection digest, deterministic projection-contract
version, source scope, admission-time authority facts, and typed provenance
references/digests. Digest verification must prove that the admitted projection
was derived from that exact accepted source/version under the declared closed
projection contract. The manifest is evidence of origin; it does not transfer
ownership of source records.

This choice is required because a reference-only memory record would not be a
durable Organizational Memory authority and could silently change meaning or
become unusable when a source adapter is unavailable. A full source copy would
unnecessarily duplicate protected material and violate minimization. The
closed admitted snapshot plus minimized integrity manifest preserves the exact
Human admission decision, historical authority, Capture Once traceability, and
disclosure safety.

Snapshot fields, serialization, digest algorithms, maximum sizes, and database
constraints are deferred to IDS-034.

## 8. Standing, Withdrawal, and Supersession

### 8.1 Closed Standing Model

```text
admission → active
active → withdrawn
active → superseded
```

There is no candidate, draft, pending, review, published, archived, deleted, or
restored memory state in Version 1.

`active` is the only standing eligible for ordinary current-memory listing and
reuse. `withdrawn` and `superseded` are terminal for that exact admitted memory
identity and are available only through authorized historical inspection.

### 8.2 Withdrawal

Withdrawal is an explicit Human authority operation with reason and timestamp.
It changes standing only. It does not erase content, provenance, admission
authority, reuse history, or source identity and cannot reactivate a record.

### 8.3 Successor and Supersession

A semantic correction or replacement requires a separately Human-accepted
Technical Report version and a newly admitted successor with a new memory
identity. The successor may name zero or one authorized predecessor. Creating
it does not supersede the predecessor.

Explicit supersession verifies both records, their compatible Organization and
scope, the predecessor's current `active` standing, and operation-specific
Human authority in one coherent transaction. The replacement must itself be
active and independently authorized. Supersession does not mutate either
record's admitted snapshot.

### 8.4 Historical Preservation

All admitted snapshots, provenance manifests, Human decisions, standing
transitions, predecessor references, and Audit evidence are immutable history.
Physical deletion and in-place semantic correction are prohibited.

## 9. Authorization, Scope, and Revocation

### 9.1 Trusted Context

Actor identity and Organization context are server-derived. Client-provided
Organization, role, membership, audience, or source authority is never trusted.
Every operation reauthorizes current actor, Organization, membership, operation,
memory scope, and source-derived constraints.

### 9.2 Scope Inheritance and Intersection

Memory Organization must equal source Organization. Memory Workspace must equal
the accepted source Workspace. Memory Project is the source Project when one
exists; a Project-bound source cannot be widened to Workspace-only memory.

The admission audience may be narrower than source visibility but never wider.
Effective access is the intersection of:

- current trusted actor and Organization authority;
- current operation-specific memory authority;
- memory Organization/Workspace/Project scope and audience;
- source scope and confidentiality constraints frozen in the admitted
  manifest;
- current authorization to the exact source Technical Report version;
- authorization for each provenance, lineage, or replacement identity selected
  for disclosure.

Cross-Organization admission, retrieval, lineage, and reuse are prohibited.

### 9.3 Source-Access Revocation

Organizational Memory is not a backdoor around revoked source access. If an
actor no longer has current authorization to the exact source Technical Report,
the actor cannot receive the admitted snapshot, source identity, provenance,
lineage, replacement identity, counts, or standing through memory.

Revocation does not delete or mutate the memory Aggregate. It changes only what
the actor may currently disclose. An authorized governance/audit operation may
inspect protected history only under a separately defined operation-specific
permission that IDS-034 must map; it cannot infer ordinary reuse authority.

If the canonical source capability is temporarily unavailable, content-bearing
memory reads fail closed as payload-free unavailable. The retained snapshot may
not be used to bypass the source authorization check.

### 9.4 Protected Outcomes

Missing, inaccessible, cross-scope, revoked, or unauthorized records use stable
protected outcomes. Errors, logs, diagnostics, timing-sensitive branching,
counts, pagination, lineage, and provenance must not reveal protected identity,
existence, content, standing, or denial location.

## 10. Retrieval and Responsible Reuse

Version 1 provides bounded deterministic active-memory listing and exact-memory
retrieval for authorized Humans and separately governed application consumers.
Historical retrieval is a distinct protected operation.

Every disclosed memory representation carries:

- memory identity and version;
- current standing;
- exact source/version attribution;
- admitting Human and admission time when authorized;
- scope and audience;
- applicability and limitations;
- safe provenance references;
- authorized predecessor/replacement references when requested.

Reuse means using active memory as attributed context for Human engineering
work. It does not approve a new report, object, decision, recommendation, or
action. Consumers may not detach content from limitations, lower scope, edit the
memory, mutate the source, or turn a cached response into authority.

Withdrawn and superseded memory is excluded from active listing, active counts,
ordinary retrieval, recommendation inputs, and current approved knowledge.

## 11. Reliability, Transactions, and Accountability

### 11.1 Unit of Work and Atomicity

Memory commands use one explicit Organizational Memory Unit of Work and one
transaction for memory-owned state, provenance/manifest records, successful
Audit, required Domain Events/outbox, and idempotency completion. Repositories
do not commit independently.

Canonical Technical Report ownership is not transferred into this UoW. The
admission workflow uses typed canonical reads and same-request final authority,
version, accepted-snapshot, scope, and integrity rechecks before compare-and-
change and commit. A race or revocation causes full rollback.

### 11.2 Concurrency

Admission prevents duplicate authoritative admission under accepted uniqueness
rules defined by IDS-034. Withdrawal and supersession require expected memory
version and deterministic stale-version conflicts. Concurrent standing changes
have one winner and preserve immutable history.

### 11.3 Idempotency

Every command uses actor/Organization/operation/request-bound fingerprints.
Exact completed replay reauthorizes current access before returning a bounded,
versioned, plaintext-minimized result. Pending or different-fingerprint reuse
returns a stable conflict without protected disclosure.

### 11.4 Audit and Events

Successful admission, withdrawal, and supersession produce attributable Audit
and closed non-plaintext Domain Events in the authoritative transaction.
Events identify memory identity/version, Organization/Workspace/optional
Project, operation, standing, actor, time, causation, source reference, and
authorized predecessor/replacement where applicable. They contain no admitted
snapshot plaintext or protected provenance body.

Outbox ownership remains infrastructure delivery of memory-owned events; it is
not a second source of truth. No autonomous downstream mutation is authorized.

### 11.5 Immutability

The application and database boundaries must prevent update or deletion of the
admitted snapshot, admission evidence, source binding, provenance manifest, and
historical decisions. Only closed standing transitions and successor creation
are permitted. Exact enforcement mechanisms belong to IDS-034.

## 12. Failure and Degradation Semantics

- Protected denial is stable and payload-free.
- Invalid client criteria disclose no protected memory or source data.
- Canonical source unavailability is a non-disclosing unavailable outcome.
- No fallback, stale cache, snapshot-only bypass, EKG projection, Journal view,
  AI output, or provider state may substitute for canonical authorization.
- Partial provenance authorization reveals no partial protected chain.
- Failed commands leave memory, history, Audit, outbox, and idempotency state
  unchanged except separately authorized bounded rejection Audit.

## 13. Explicit Exclusions

EDS-034 does not authorize:

- admission from Capture, Journal, Evidence, Engineering Objects,
  Relationships, EKG projections, AI output, or any source other than exact
  Human-accepted Technical Report versions;
- multi-source synthesis;
- public or external publication;
- cross-Organization sharing;
- semantic/vector search, embeddings, similarity, ranking, or graph expansion;
- graph-database adoption;
- autonomous AI admission, withdrawal, supersession, publication, or reuse;
- enterprise boards, reviewer assignment, quorum, or voting;
- generic document, standards, or evidence repositories;
- retention schedules, legal holds, certification, bulk import, or export;
- frontend/UI;
- EDS-030 Technical Proposal Review behavior;
- EDS-031 Engineering Digital Twin behavior;
- source mutation, source ownership transfer, or additional source lifecycle.

## 14. Downstream IDS-034 Obligations

IDS-034 must define without expanding this EDS:

1. exact enums, value objects, commands, DTOs, outcomes, and strict schemas;
2. memory UUID/version, standing, lineage, source identity/version, admitted
   snapshot, limitation, audience, and provenance field contracts;
3. exact admitted representation schema, canonical serialization, digest,
   projection-contract version, size, deterministic non-semantic normalization,
   exact source-field parity, prohibited transformation, and source-snapshot
   coherence rules;
4. typed Technical Report eligibility, visibility, historical-resolution, and
   final-recheck ports;
5. actor, trusted Organization, membership, and operation-specific permission
   mapping for admit, read active, list active, inspect history, withdraw,
   create successor, supersede, and governance audit;
6. exact Workspace/Project/audience intersection and source-revocation matrix;
7. Repository and Unit of Work ports, persistence model, migrations, ownership,
   runtime/schema roles, indexes, constraints, and immutable-history controls;
8. transaction sequencing, lock order, compare-and-change predicates, rollback,
   and post-rollback rejection-Audit boundary;
9. idempotency fingerprint, replay result, reservation, conflict, expiry, and
   reauthorization semantics;
10. database/application uniqueness enforcing at most one canonical memory
    Aggregate per Organization and exact accepted Technical Report
    identity/version, including concurrent duplicate admission and protected
    existing-state behavior;
11. closed Domain Event/outbox payloads and dispatch ownership boundaries;
12. deterministic ordering, filters, page/query limits, protected totals, and
    bounded canonical read requirements;
13. stable protected-not-found, invalid, conflict, unavailable, and success
    transport-neutral outcomes;
14. plaintext exclusions for errors, logs, diagnostics, Audit, events,
    idempotency, counts, lineage, and provenance;
15. verification matrix covering domain invariants, projection/source semantic
    parity, prohibited transformations, duplicate/concurrent admission,
    zero-or-one predecessor enforcement, source races, authorization,
    cross-scope denial, source revocation, direct persistence bypass,
    immutability, transaction atomicity, concurrency, replay, security,
    performance, migration, roles, API absence/presence, and regressions.

IDS-034 must stop rather than guess if existing canonical Technical Report or
authorization contracts cannot support these requirements.

## 15. Acceptance Criteria

EDS-034 is ready for Human EDS acceptance only when independent review confirms:

- one dedicated non-source-owning Aggregate;
- exact accepted Technical Report version as the only V1 source;
- explicit Human admission distinct from acceptance and publication;
- immutable admitted snapshot plus minimized integrity/source manifest;
- closed active/withdrawn/superseded standing and explicit supersession;
- source revocation cannot be bypassed through retained memory;
- authorization and scope intersection precede every disclosure;
- responsible reuse preserves limitations, provenance, and current standing;
- Audit, transaction, concurrency, idempotency, event, and immutability
  obligations are enforceable downstream;
- all deferred capabilities remain excluded;
- QG-M1 remains PASS.

## 16. Unresolved Questions Reserved for IDS-034

- exact existing role names that map to each operation-specific permission;
- exact admitted snapshot field set and maximum size;
- exact canonical digest/serialization algorithm;
- exact historical governance/audit permission distinct from ordinary reuse;
- exact bounded pagination and count DTOs;
- exact storage and database immutability mechanisms.

These questions affect implementation contracts, not the accepted architecture
boundary. None authorizes additional sources, states, or capabilities.

## 17. Architecture Conflict Assessment

No conflict is identified with ADR-021, ADR-023, PATCH-029, PATCH-032, or
PATCH-033. The admitted snapshot is memory-owned authority with immutable source
attribution; it neither edits nor replaces the accepted Technical Report.
Source authorization remains mandatory, preventing memory from becoming a
disclosure bypass.

## 18. Governance State

```text
EDS-034: ACCEPTED / COMPLETE
Initial Independent EDS Review: FAIL — HISTORICAL
EDS034-MAJ-01: RESOLVED BY AMENDMENT
EDS034-MAJ-02: RESOLVED BY AMENDMENT
EDS034-MIN-01: RESOLVED BY AMENDMENT
Focused Independent EDS Re-review: PASS
Human EDS Acceptance: PASS
IDS-034 authority: GRANTED
IDS-034: ACCEPTED / COMPLETE
Independent IDS Review: PASS AFTER FOCUSED AMENDMENTS AND FINAL RE-REVIEW
Human IDS Acceptance: PASS
Implementation-Plan-034: ACCEPTED / COMPLETE
Implementation authority: NOT GRANTED
```
