# EDS-033 — Engineering Knowledge Graph Integration

## 1. Document Control

| Field | Value |
|---|---|
| Document ID | EDS-033 |
| Related PATCH | PATCH-033 — Engineering Knowledge Graph Integration |
| Status | ACCEPTED / COMPLETE |
| Architecture Review | PASS after focused amendment and re-review |
| Human Architecture Acceptance | PASS |
| QG-M1 | PASS |
| EDS design authority | GRANTED |
| Independent EDS Review | PASS |
| Human EDS Acceptance | PASS |
| IDS authority | GRANTED |
| IDS-033 | ACCEPTED / COMPLETE |
| Independent IDS Review | PASS after focused amendments and final re-review |
| Human IDS Acceptance | PASS |
| Implementation-Plan-033 | ACCEPTED / COMPLETE |
| Implementation authority | NOT GRANTED |
| Date | 2026-08-12 |

## 2. Governing Authorities

EDS-033 is governed by:

1. the SATCO Constitution and Engineering Intelligence Manifesto;
2. accepted PATCH-033 and its Architecture Review findings disposition;
3. PATCH-021 and PATCH-021.1 through PATCH-021.5;
4. ADR-017 Engineering Knowledge Graph Evolution;
5. ADR-020 EKG Open Extension Principle;
6. completed PATCH-023 through PATCH-029;
7. accepted ADR-023 and completed PATCH-032;
8. the current canonical Organization, Workspace, Project, authentication,
   authorization, Audit, transaction, concurrency, idempotency, and outbox
   boundaries.

If this EDS conflicts with a higher authority, the higher authority prevails
and EDS-033 returns to review. EDS-033 cannot expand PATCH-033.

## 3. Purpose and Architectural Boundary

EDS-033 defines a read-only application projection that allows authorized
actors to inspect bounded, governed connections among existing canonical
engineering identities. It does not define a second system of record.

The EKG integration owns only composition behavior for a read request. It owns
no authoritative node, edge, engineering fact, lifecycle, approval, evidence,
or relationship. It creates no graph Aggregate, Repository, Unit of Work,
table, migration, outbox record, idempotency record, command, or mutation.

Canonical capabilities remain authoritative for identity, state, scope,
visibility, lifecycle, relationship meaning, provenance, evidence, and Human
authority. A projection is valid only for the duration of the authorized read
that produced it. Cached or previously returned projections never become
authority.

Any future graph-owned state or mutation requires a separately accepted
architecture decision and PATCH. IDS-033 cannot introduce it.

## 4. Architectural Assumptions

- Organization context and authenticated actor identity are trusted and
  server-derived.
- Canonical capabilities can expose read contracts that authorize before
  returning protected identities or fields.
- Existing canonical relationship vocabularies remain the only source of edge
  meaning.
- PostgreSQL remains the Version-1 System of Record; no graph database is
  required.
- Canonical capabilities may change independently, so each traversal request
  must reauthorize and resolve current state.
- A missing canonical read contract means the identity or relationship is not
  eligible for projection; EKG does not compensate through direct persistence
  access.

## 5. Architectural Invariants

1. EKG projection is read-only and non-authoritative.
2. Every node maps to one authorized canonical identity.
3. Every edge maps to one approved canonical relationship semantic and source.
4. Absence of approved relationship authority means absence of an edge.
5. Authorization precedes node, edge, path, field, count, total, and
   continuation disclosure.
6. Cross-Organization traversal is prohibited without exception.
7. Effective path authority is the intersection of all canonical authorities
   involved in the path.
8. Cross-Workspace and cross-Project traversal are denied unless every
   canonical authority explicitly permits the exact composition.
9. A denial at any path element makes that element and dependent path
   non-disclosable.
10. Traversal is deterministic and bounded.
11. Projection never mutates or bypasses a canonical capability.
12. Protected outcomes do not reveal existence, identity, counts, denial
    location, or inaccessible continuation state.

## 6. Node Projection Model

### 6.1 Eligible Node Classes

The following canonical identity classes are eligible only when their owning
capability supplies an approved, actor-authorized read projection:

| Node class | Canonical owner | Eligibility boundary |
|---|---|---|
| Engineering Object | EngineeringObject capability | Authorized canonical UUID and minimum approved projection |
| Engineering Context | Engineering Context capability | Authorized canonical identity and current scope |
| Engineering Relationship | Engineering Relationship capability | Authorized relationship identity; normally represented as an edge, but may be addressable for traceability when its canonical contract permits |
| Evidence | Evidence capability | Authorized Evidence UUID and minimum lifecycle/authority metadata |
| Engineering Experience Capture | Universal Capture | Eligible only where an approved canonical relationship contract connects it; Journal presentation does not create eligibility |
| Engineering Journal | Engineering Journal | No independent canonical node by default because Journal is presentation-only and nonpersistent |
| Technical Report | Technical Report capability | Authorized report UUID and minimum lifecycle/purpose projection; eligibility as a connected node still requires an approved relationship contract |
| Workspace and Project scope identities | Their canonical capabilities | Scope/navigation projection only when the governing relationship contract requires them |

Eligibility does not require that every class appear in Version 1. An EDS/IDS
may include only the subset for which current canonical ports and approved
relationship semantics are sufficient.

### 6.2 Minimum Node Disclosure

A node projection contains only:

- canonical node class;
- canonical opaque identity;
- minimum display fields expressly approved by the canonical read contract;
- current lifecycle or authority indicator only when required to interpret an
  approved edge;
- canonical navigation reference that grants no access by itself.

Protected content, evidence bodies, Capture plaintext, report technical
content, rationale, source material, confidential fields, and ORM state are
excluded unless a separately authorized detail operation from the canonical
owner permits disclosure. EKG DTOs are not canonical DTOs and cannot be reused
as write contracts.

## 7. Relationship and Edge Model

### 7.1 Edge Eligibility

An edge is eligible only when all conditions hold:

1. an accepted canonical capability defines the exact relationship semantic;
2. the canonical source exposes the relationship through an authorized read
   contract;
3. both endpoints are independently authorized and eligible;
4. direction, lifecycle, family/type discrimination, scope, and evidence rules
   are valid under the canonical relationship owner;
5. composite path authorization permits disclosure.

Current eligible semantics originate only from approved Engineering
Relationship and Engineering Context relationship contracts, including their
approved vocabularies and family/type discrimination. Evidence or provenance
references may be projected as traceability links only where their canonical
contract expressly defines that relationship; mere reliance metadata does not
automatically become a graph edge.

### 7.2 No Inferred Vocabulary

EKG shall not infer edges from:

- shared Organization, Project, Workspace, discipline, owner, or steward;
- common timestamps or identifiers;
- Journal navigation;
- Capture provenance or supersession alone;
- Technical Report predecessor, reliance, or contextual documentation unless
  an approved canonical contract defines it as a projectable relationship;
- Evidence attachment, similarity, co-occurrence, or textual reference;
- AI output, semantic similarity, or recommendation.

When no approved relationship exists, the deterministic result is no edge.
New cross-capability vocabulary requires separate governance and acceptance
before EDS-033 can be amended to recognize it.

### 7.3 Edge Projection

An authorized edge projection contains only its canonical relationship source,
opaque identity when one exists, approved semantic discriminator, direction,
minimum lifecycle/authority standing, endpoint identities, and safe traceability
reference. Reverse navigation reverses traversal direction only; it does not
create a second authoritative relationship.

## 8. Scope and Authorization Model

### 8.1 Trusted Context

Organization identity is derived from trusted authentication context and is
never accepted as authority from a client field, filter, route parameter, or
continuation token. Project and Workspace selection must be validated through
their canonical authorization boundaries.

### 8.2 Path-Authority Intersection

For a path containing nodes and edges, the actor must be authorized by every
canonical authority governing:

- the start node;
- each traversed relationship;
- every intermediate and destination node;
- Evidence or provenance metadata selected for disclosure;
- Organization, Workspace, and Project composition;
- the requested projection fields and navigation destination.

The effective authority is the intersection of those decisions. One denial
removes the protected element and every dependent path. EKG cannot substitute
its own policy, infer access from another endpoint, or disclose a partial path
that reveals the denied element.

### 8.3 Scope Rules

- Cross-Organization traversal is always denied.
- Cross-Workspace traversal is denied unless every canonical authority on the
  exact path explicitly permits it.
- Cross-Project traversal is denied unless every canonical authority on the
  exact path explicitly permits it.
- Organization permission alone does not imply Workspace or Project
  permission.
- A continuation request repeats authentication, scope validation, and path
  authorization and cannot widen its original scope.

## 9. Traversal Contract

### 9.1 Determinism

Traversal results use a total deterministic ordering based on stable canonical
class, canonical identity, approved edge discriminator, direction, and a final
stable tie-breaker. Database row order, display labels, and mutable timestamps
cannot be sole ordering authorities.

### 9.2 Bounds

Every operation has explicit maximum depth, maximum expansion per node,
maximum returned nodes, maximum returned edges, maximum page size, and maximum
execution budget. Defaults and hard maxima are mandatory IDS obligations.
Unbounded traversal is invalid rather than truncated silently.

### 9.3 Cycles

Traversal tracks canonical visited node-and-edge identity. It never follows the
same authorized directed edge twice within one traversal. Encountering a cycle
does not mutate or invalidate the canonical relationship; traversal stops that
branch deterministically and may expose only a safe cycle indicator if IDS-033
proves that it cannot leak protected identity.

### 9.4 Pagination and Continuation

Continuation is opaque, integrity-protected, bounded, and bound to actor,
Organization, authorized scope, query shape, ordering version, and expiry. It
contains no protected plaintext or global totals. Each request reauthorizes all
material scope and current canonical elements before disclosure.

If a previously accessible node or edge becomes inaccessible, the next request
omits the protected element and dependent paths without revealing why. A token
that cannot be safely continued returns a stable protected or invalid-
continuation outcome; it never falls back to broader traversal.

## 10. Evidence and Provenance

EKG exposes traceability, not source ownership. Every projected provenance or
Evidence reference retains its canonical UUID, owning capability, current
authorized visibility, lifecycle/authority standing when required, and safe
source-version reference.

The projection does not copy Evidence bodies, Technical Report accepted
snapshots, Capture plaintext, standards content, or source metadata merely to
make traversal convenient. Detail disclosure remains with the canonical owner.

If provenance is inaccessible, the projection must not disclose its identity,
count, type, source, absence, or position in a path. Historical references may
be represented only through the canonical historical-resolution contract that
owns them.

## 11. Integration Boundaries

EKG depends inward on capability-neutral read ports. Adapters invoke existing
canonical application services or approved read contracts. EKG shall not:

- access another capability's ORM model, table, Session, Repository, or Unit of
  Work directly;
- coordinate, commit, or roll back canonical transactions;
- publish canonical events or write Audit/outbox/idempotency records;
- become an authorization authority for another capability;
- use a prior projection, cache, or continuation as current authority;
- call transport layers to obtain canonical data.

Canonical owners retain their Audit, Unit of Work, concurrency, idempotency,
outbox, lifecycle, and transaction behavior. Read-side observability may record
bounded operational telemetry only if it contains no protected engineering
content and creates no engineering authority.

## 12. Security and Failure Semantics

The capability fails closed. Stable outcome categories must distinguish valid
request errors from protected absence without distinguishing unauthorized,
nonexistent, inactive, cross-scope, or newly inaccessible protected resources.

No response, count, total, path length, ordering gap, timing diagnostic,
continuation metadata, log, trace, metric, or error may disclose protected
identity or existence. Counts and totals, if later authorized, are calculated
only after all applicable authorization and filtering.

Dependency degradation cannot create fallback authority. The capability may
return a stable unavailable outcome or a strictly complete authorized subset
only if IDS-033 defines deterministic semantics that cannot imply inaccessible
elements. It shall never fabricate nodes, infer edges, or reuse stale access.

## 13. Explicit Exclusions

EDS-033 does not authorize:

- EDS-030 Technical Proposal Review or PATCH-030 registration;
- EDS-031 Engineering Digital Twin or PATCH-031 registration;
- graph-owned state or mutation;
- a graph database or replacement of PostgreSQL;
- arbitrary or inferred edges;
- cross-Organization traversal;
- semantic search, vector search, or embeddings;
- Organizational Memory publication or retention authority;
- autonomous or advisory AI behavior;
- frontend or UI work;
- generic document management;
- changes to canonical Aggregate ownership;
- implementation, APIs, persistence, migrations, or configuration.

## 14. Downstream IDS-033 Obligations

IDS-033 must specify, without weakening this EDS:

1. the exact eligible node classes supported by current canonical ports;
2. the exact allow-list of canonical edge semantics and authoritative owners;
3. typed node, edge, path, page, continuation, and protected-outcome DTOs;
4. exact application read ports and adapter dependency direction;
5. actor and trusted Organization-context projection;
6. operation-specific authorization and field-disclosure matrices;
7. Workspace/Project composition and cross-scope denial matrices;
8. deterministic ordering keys and stable tie-breakers;
9. hard depth, breadth, node, edge, page, time, and continuation bounds;
10. cycle detection and safe response behavior;
11. continuation integrity, scope binding, expiry, and reauthorization;
12. canonical-state-change and revocation behavior between pages;
13. provenance and historical-resolution field boundaries;
14. stable errors, protected-not-found equivalence, and degradation outcomes;
15. logging, diagnostics, telemetry, and plaintext-exclusion rules;
16. performance query budgets and N+1 prohibitions;
17. request-scoped composition and absence of EKG transaction ownership;
18. exact authorized files, prohibited files, tests, and regression gates only
    after Implementation Plan authority is granted.

IDS-033 may not design a graph write model, persistence model, migration,
Aggregate, Repository, Unit of Work, command, or new relationship vocabulary.

## 15. Acceptance Criteria

EDS-033 is acceptable only if independent and Human review confirm:

- the capability is projection/traversal only;
- canonical identity, relationship, Evidence, scope, and Human authority remain
  with their owners;
- the eligible-edge rule cannot invent cross-capability semantics;
- authorization intersection and deny-by-default scope rules are complete;
- traversal, cycles, pagination, and continuation are deterministically bounded;
- protected outcomes prevent identity, count, path, and provenance leakage;
- integration uses canonical application boundaries without persistence access;
- all PATCH-033 exclusions remain intact;
- QG-M1 Manifesto alignment is `PASS`;
- no unresolved blocking question remains.

## 16. Traceability

| EDS decision | Authority |
|---|---|
| Projection/traversal only | PATCH-033 §§2–6; focused Architecture Re-review |
| Canonical Engineering Object ownership | ADR-017; EngineeringObject Blueprint; PATCH-023/024 |
| Approved relationship semantics only | PATCH-021.2 and PATCH-021.4; PATCH-026 |
| Evidence authority preserved | PATCH-021.4; PATCH-027 |
| Trusted Organization and composite scope | PATCH-021.4; PATCH-025; PATCH-033 §6.3 |
| Stable Core and modular extension | ADR-020 |
| Human authority and provider independence | Manifesto; ADR-023; PATCH-032 |
| Digital Twin, semantic/vector search, and AI excluded | PATCH-021; PATCH-033 |

## 17. Unresolved Questions

No architecture-blocking question remains.

IDS-033 must determine the implementable Version-1 subset of node classes and
the exact existing canonical edge allow-list from repository contracts. If no
current canonical port can expose an eligible identity or relationship without
direct persistence access or authority duplication, that class or edge must be
excluded from Version 1 rather than worked around.

## 18. EDS Decision

```text
EDS-033 design: COMPLETE
EDS-033 status: ACCEPTED / COMPLETE
PATCH-033 alignment: PASS
Architecture Review alignment: PASS
QG-M1 design alignment: PASS
Blocking architecture conflicts: NONE
Independent EDS Review: PASS
Human EDS Acceptance: PASS
IDS-033: ACCEPTED / COMPLETE
Human IDS Acceptance: PASS
Implementation-Plan-033: ACCEPTED / COMPLETE
Implementation authority: NOT GRANTED
```
