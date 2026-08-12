# IDS-033 — Engineering Knowledge Graph Integration

## 1. Document Control

| Field | Value |
|---|---|
| Document ID | IDS-033 |
| Related PATCH | PATCH-033 — Engineering Knowledge Graph Integration |
| Governing EDS | EDS-033 — ACCEPTED / COMPLETE |
| Status | ACCEPTED / COMPLETE |
| Human EDS Acceptance | PASS |
| IDS design authority | GRANTED |
| Independent IDS Review | PASS after focused amendments and final re-review |
| Human IDS Acceptance | PASS |
| Implementation Plan authority | GRANTED |
| Implementation-Plan-033 | ACCEPTED / COMPLETE |
| Implementation authority | NOT GRANTED |
| Date | 2026-08-12 |

## 2. Implementation Boundary

IDS-033 specifies a read-only, request-scoped application composition over
canonical read authorities. Executable V1 owns only single-node projection
orchestration; future traversal remains in the non-executable deferred annex.
EKG owns no Aggregate, lifecycle, authoritative relationship, Repository,
Unit of Work, Session, table, migration, command, transaction, Audit record,
outbox record, idempotency record, cache of protected content, or mutation.

Canonical capabilities retain identity, relationship meaning, state,
authorization, scope, evidence, provenance, concurrency, Audit, transaction,
idempotency, and outbox ownership. Missing safe canonical read support excludes
a projection from executable Version 1.

## 3. Closed Version-1 Node Allow-List

### 3.1 Node Types

| Discriminator | Stable identity | Canonical owner | Safe default fields |
|---|---|---|---|
| `engineering_object` | canonical UUID | EngineeringObject | discriminator, UUID, Organization UUID, Customer ID, Project ID, Workspace ID, family, discipline, object type, subtype, lifecycle, authority standing, version, creator ID, steward ID, created-at, updated-at |
| — | — | — | No other node type is enabled in Version 1 |

The final Version-1 node allow-list contains only `engineering_object`.
Engineering Context, Project, Workspace, discipline, and external source are
deferred because their current application boundaries do not expose the exact
typed, batch-safe node-resolution contract required by this IDS. Relationship
identities are never nodes. Evidence, Universal Capture, Engineering Journal,
and Technical Report remain excluded because no approved graph relationship
contract safely connects them; Journal additionally owns no persistent
identity.

### 3.2 Node Contract

`GraphNodeProjection` is the closed immutable product type:

- `node_type: Literal["engineering_object"]`;
- `node_id: UUID`, copied directly from `EngineeringObjectResponse.id`;
- `organization_id: UUID` from trusted canonical resolution;
- `customer_id: int | None` exactly as canonically returned;
- `project_id: int` and `workspace_id: int` exactly as canonically returned;
- `family: EngineeringObjectFamily`;
- `discipline: EngineeringDiscipline`;
- `object_type: EngineeringObjectType`;
- `subtype: str | None` exactly as canonically returned;
- `lifecycle: EngineeringLifecycle`;
- `authority_standing: EngineeringAuthorityStanding`;
- `version: int`;
- `creator_id: int` and `steward_id: int`;
- `created_at: datetime` and `updated_at: datetime`.

There is no `SafeNodeDisplay` product in Version 1. No title, engineering
identifier, label, summary, derived display value, or synthetic value may be
added. Every projection field is copied from
an already authorized `EngineeringObjectResponse`, except the closed
`node_type` contract discriminator. The discriminator is not canonical
Engineering Object data and adds no engineering value. `node_id` retains the
exact UUID value and type of `EngineeringObjectResponse.id`.

No body, rationale, protected canonical content, ORM object, or internal
diagnostic is permitted.

## 4. NON-EXECUTABLE / NON-BLOCKING Deferred Edge Annex

### 4.1 Final Version-1 Decision

No edge contract exists in executable Version 1. Everything in this section is
deferred, non-executable, non-blocking traceability and grants no current
implementation or acceptance authority. PATCH-033 and EDS-033 may permit
approved canonical edges only after a separately governed safe read
prerequisite and focused IDS amendment are accepted.

### 4.2 Deferred Engineering Relationship Edges

The approved vocabulary below remains a deferred eligibility inventory, not a
Version-1 allow-list. Canonical owner: Engineering Relationship capability. Endpoints are
`engineering_object -> engineering_object`. Direction is the stored source to
target direction. Every eligible discriminator is the exact pair
`relationship_family + relationship_type`; family is never inferred.

| Family | Allowed types |
|---|---|
| `structural` | `part_of`, `belongs_to_system`, `belongs_to_subsystem`, `belongs_to_package`, `grouped_with`, `installed_in`, `located_in` |
| `physical` | `connected_to`, `mounted_on`, `connected_through`, `mechanically_coupled_to`, `terminated_at`, `routed_through`, `shares_enclosure_with` |
| `electrical` | `powered_by`, `protected_by`, `isolated_by`, `earthed_through`, `connected_to_busbar`, `controlled_by_feeder`, `backed_up_by_ups` |
| `instrumentation` | `measures`, `transmits_to`, `receives_process_input_from`, `connected_to_loop`, `connected_to_io_channel`, `actuates`, `positioned_by`, `monitored_by`, `provides_feedback_to`, `compensated_by`, `calibrated_against` |
| `automation` | `controlled_by`, `commands`, `receives_signal_from`, `sends_signal_to`, `implemented_in`, `interlocked_with`, `trips`, `initiates`, `inhibits`, `participates_in_sequence`, `monitored_by`, `generates_alarm_for`, `executes_logic_for` |
| `dependency` | `depends_on`, `affects`, `enables`, `prevents`, `constrains`, `replaces`, `supersedes`, `derived_from` |

Future safe metadata may include canonical relationship UUID, family, type, direction, lifecycle,
authority standing, Organization UUID, Project ID, Workspace ID, version, and
authorized Evidence UUID references only after separate Evidence authorization.
Creator/steward/reviewer/approver identities are excluded from default graph
projection.

Current Engineering Relationship reads expand repository results before
complete endpoint and composite-path authorization and expose neither the
required independently authorized batch endpoint resolution nor secure
continuation. PATCH-033 shall not adapt around that boundary.

### 4.3 Deferred Engineering Context Relationship Edges

Engineering Context Relationship edges are removed from Version 1. Their
approved meanings remain `requires`, `provided_by`, `consumed_by`, and
`potentially_affects`, but the current service returns untyped mappings,
directly owns its repository, and provides no typed, authorization-aware,
batch-capable frontier read contract. No Context endpoint node is enabled.

Canonical owner remains Engineering Context Relationship capability. Exact meanings:
`requires`, `provided_by`, `consumed_by`, `potentially_affects`. Direction is
the stored source endpoint to target endpoint. Source and target types may be
only `engineering_context`, `project`, `workspace`, `discipline`, or
`external_source`, matching their canonical endpoint kinds.

Safe metadata: canonical relationship key/opaque ID, meaning, source and target
kind, direction, current/withdrawn lifecycle when expressly requested, Project
scope, version, source role, and target role. Purpose, applicability,
withdrawal rationale, commitments, Human identities, and protected external
source text are excluded by default.

### 4.4 Edge Eligibility and Absence

Each edge requires current canonical relationship authorization plus independent
authorization of both endpoints and all selected metadata. Withdrawn or other
non-current edges are excluded by default and may be requested only through an
explicit authorized lifecycle criterion. Reverse traversal changes navigation
direction only and never synthesizes an edge.

No edge is enabled in Version 1. Absence of an enabled canonical
contract deterministically means no edge. Shared scope, provenance, temporal
order, predecessor identity, navigation, Evidence reliance, or textual
similarity never synthesizes an edge.

## 5. Typed Application Contracts

The complete inward implementation-neutral executable V1 contracts are:

- `GraphActor {actor_id: int, organization_id: UUID}`. `actor_id` is the
  trusted authenticated Human identifier. `organization_id` is trusted,
  server-derived Organization context and is never accepted from graph input;
- `GraphScope {organization_id: UUID, project_id: int | None, workspace_id:
  int | None}`. Its Organization must equal the actor's trusted Organization.
  A supplied Project or Workspace is independently authorized and must equal
  the corresponding value on the resolved Engineering Object;
- `GraphNodeProjection`: the exact closed product in §3.2, with one canonical
  source and no optional projection fields beyond `customer_id` and `subtype`;
- `GraphNodeRequest {node_id: UUID}`;
- `GraphNodeResult`: closed union of
  `success(node: GraphNodeProjection)`, `protected_not_found`,
  `invalid_request`, and `unavailable`;
- `CanonicalEngineeringObjectReadPort.get_authorized(actor: GraphActor, scope:
  GraphScope, node_id: UUID) -> CanonicalEngineeringObjectReadResult`;
- `CanonicalEngineeringObjectReadResult`: closed union of
  `resolved(response: EngineeringObjectResponse)`, `protected`, and
  `unavailable`. `protected` and `unavailable` are payload-free;
- `GraphScopeAuthorizationPort.authorize(actor: GraphActor, scope: GraphScope)
  -> ScopeAuthorizationDecision`, where the closed decision is `authorized` or
  payload-free `protected`;
- `GraphReadService.get_node(actor: GraphActor, scope: GraphScope, request:
  GraphNodeRequest) -> GraphNodeResult`.

`get_node` is the only executable V1 operation and performs exactly one
authorized canonical Engineering Object read. Missing, inaccessible,
cross-scope, inactive, or authority-revoked nodes produce the same
`protected_not_found` result.

For V1 success, `GraphNodeResult` contains exactly one `GraphNodeProjection`.
`protected_not_found`, `invalid_request`, and `unavailable` are closed tagged
variants with no payload: they contain no node, identity, count, diagnostic,
denial source, or partial field. No batch request, result, or port exists in
executable V1.

Ports return typed DTOs, never ORM rows or untyped mappings. Adapters may call
canonical application services/read boundaries only. EKG cannot access their
repositories, Sessions, UoWs, or transport routers.

## 6. Authorization Matrix

| Operation | Mandatory authorization before disclosure |
|---|---|
| Node retrieval | active actor, active trusted Organization membership, requested scope, canonical node existence/visibility, requested fields |

No other operation exists in executable V1.

Organization is server-derived and never trusted from request parameters or
token payload as authorization. The requested Organization must equal the
actor's trusted Organization. When supplied, Project and Workspace scope must
be canonically authorized and must match the resolved Engineering Object.
Scope authorization and the single canonical object authorization complete
before any projection field is constructed or disclosed. Every denial returns
the payload-free `protected_not_found` result.

## 7. Executable V1 Operation and Deferred Traversal Annex

### 7.1 Executable V1 Bound

Executable V1 resolves exactly one requested Engineering Object node through
`get_node`. The request contains only `node_id: UUID`; success contains exactly
one authorized projection and every non-success variant is payload-free.

### 7.2 NON-EXECUTABLE / NON-BLOCKING Deferred Traversal Bounds

- maximum requested depth: `5`, default `1`;
- maximum expanded outgoing/incoming edges per node: `100`;
- maximum returned nodes: `100`;
- maximum returned edges: `100`;
- maximum page size: `100`, default `20`;
- maximum continuation token length: `2048` bytes;
- continuation expiry: `15` minutes;
- maximum canonical batch resolution size: `100` keys per call;
- maximum canonical read rounds: `1 + requested_depth` per edge-source adapter.

These are architectural maxima for the future prerequisite-enabled traversal.
The narrowed executable Version-1 contract fixes depth to `0`, returns at most
one node and zero edges, accepts no continuation, and performs no frontier
expansion. Enabling the wider maxima requires focused IDS review after the
canonical-read prerequisites are accepted.

### 7.3 NON-EXECUTABLE / NON-BLOCKING Deferred Ordering and Expansion

Breadth-first traversal remains the future algorithm contract. Version 1 has
only depth-zero node retrieval. The future total edge order is:

1. source node type;
2. stable encoded source identity;
3. canonical edge source (`engineering_relationship` before
   `engineering_context_relationship`);
4. semantic discriminator (family then type, or meaning);
5. stored direction;
6. stable encoded target identity;
7. stable canonical edge identity.

Nodes use node type then stable encoded identity. Mutable display values,
timestamps, and database row order are never tie-breakers.

### 7.4 NON-EXECUTABLE / NON-BLOCKING Deferred Cycles and Duplicates

A future directed canonical edge key is expanded at most once. A node may appear once
in the returned node set. Multiple distinct canonical edges between the same
nodes remain distinct. Encountering an already-expanded edge stops that branch.
No cycle marker is returned in Version 1 because it could reveal hidden path
shape. Authorization removal of an intermediate element removes every
dependent terminal/path element before pagination.

## 8. NON-EXECUTABLE / NON-BLOCKING Deferred Continuation Annex

Continuation is outside the executable V1 DTO, port, operation, outcome, and
verification boundary. The following remains traceability for a future focused
IDS amendment and grants no current implementation authority:

The continuation token is opaque and authenticated with an integrity-protected
server secret. Its versioned plaintext-before-encoding structure contains only:

- contract version;
- actor ID digest and trusted Organization UUID;
- canonical Project/Workspace scope digests;
- normalized query-shape digest;
- ordering version;
- authorized cursor position expressed as safe stable keys;
- issued-at and expiry;
- nonce.

It contains no display text, protected plaintext, hidden identity, global
count, denied-path state, authorization decision, or access grant. Tampering,
unsupported version, expiry, actor mismatch, Organization mismatch, scope
mismatch, or query mismatch returns `GRAPH_INVALID_CONTINUATION` without token
diagnostics. Every continuation request reauthorizes current actor, scope,
nodes, edges, and fields; token replay cannot preserve revoked access.

## 9. Protected Outcomes and Disclosure

Stable application categories are:

- `GRAPH_PROTECTED_NOT_FOUND`: nonexistent, inaccessible, inactive,
  cross-scope, or authority-revoked Engineering Object;
- `GRAPH_INVALID_REQUEST`: malformed node request or identity;
- `GRAPH_UNAVAILABLE`: required canonical read capability unavailable;
- success.

Protected cases share status, body shape, and diagnostic policy. Exact response
time equality is neither promised nor tested. Executable V1 must not branch
into intentionally data-dependent protected diagnostics, counts, sleep/delay
behavior, or additional canonical queries after a protected decision. Tests
compare response schema, status/category, side effects, query classes/count
bounds, and absence of protected values across representative nonexistent and
inaccessible cases.
Responses, logs, traces, metrics, and exceptions contain no protected
identity, body, rationale, source reference, hidden count, denial source, SQL,
or stack detail. No global total is exposed.

## 10. NON-EXECUTABLE / NON-BLOCKING Deferred Provenance Annex

Provenance and Evidence are outside every executable V1 DTO, port, operation,
outcome, and verification gate. The rules below remain future traceability and
grant no current implementation authority.

`GraphProvenanceReference` is a navigation-safe reference to a canonical owner;
it never embeds a source body. It may disclose canonical owner discriminator,
opaque UUID/key, safe version/lifecycle, and navigation reference only after
current independent authorization. Inaccessible provenance is omitted together
with dependent graph material without revealing its existence or count.

Evidence UUIDs on Engineering Relationships are not automatically disclosed.
They require current Evidence authorization, acceptable lifecycle, same
Organization, and exact Project/Workspace compatibility. EKG copies no Evidence
body, Capture plaintext, Technical Report snapshot, standard content, or
historical fallback.

## 11. Ownership and Transaction Integration

EKG read orchestration is request-scoped and owns no transaction. Canonical
adapters may privately use their existing read infrastructure or UoW factories,
but EKG cannot coordinate, commit, roll back, or retain them. Reads create no
engineering Audit, outbox, idempotency, Domain Event, version increment, or
canonical mutation.

Canonical optimistic concurrency remains relevant only as current-state
resolution: a changed canonical version is re-read/re-authorized or the
protected element is omitted. EKG creates no expected-version contract.
Operational telemetry is bounded, plaintext-free, and non-authoritative.

## 12. Performance and Query Obligations

### 12.1 Executable V1 Budget

For executable Version 1, one node request performs exactly one bounded scope-
authorization decision and at most one authorized canonical Engineering
Object read. A protected scope decision performs no object read. No other
canonical capability is called.

### 12.2 NON-EXECUTABLE / NON-BLOCKING Deferred Query Budgets

The following budgets become applicable only after accepted canonical-read
prerequisites enable traversal:

- no per-edge or per-node N+1 canonical lookup;
- use bounded batch resolution up to 100 keys;
- at most `1 + depth` bounded edge-page rounds per edge-source adapter;
- at most one bounded node-resolution batch per frontier and node type;
- authorization filtering occurs before totals, pagination output, and
  continuation creation;
- no unbounded in-memory graph construction;
- no hidden/global count query;
- unavailable or unsupported node types trigger no unrelated canonical query;
- Project/Workspace denial stops subordinate edge/node queries;
- tests must instrument canonical call counts and prove bounds at depth 1 and 5
  with fan-out above 100.

Wall-clock latency is environment-dependent and is not an authority contract;
query/call budgets and result bounds are deterministic acceptance gates.

## 13. Executable V1 Security Invariants

Prohibited:

- accepting client-controlled Organization authority;
- direct canonical persistence or ORM access;
- graph-owned state, mutation, lifecycle, UoW, Repository, table, migration,
  Audit, event, outbox, or idempotency behavior;
- cross-Organization identity or state inference;
- accepting Project or Workspace scope without canonical authorization and an
  exact match to the resolved Engineering Object;
- authorization after identity or projection-field disclosure;
- counts/totals over inaccessible records;
- plaintext persistence, caching, token inclusion, logs, diagnostics, metrics,
  or errors;
- graph database, semantic/vector search, Organizational Memory, AI, Digital
  Twin, frontend, Technical Proposal Review, or new relationship vocabulary.

## 14. Verification Matrices

### 14.1 Executable Version-1 Acceptance Evidence

Only this table is a current implementation acceptance gate.

| V1 contract | Required executable evidence |
|---|---|
| Single operation | `get_node` is the only application operation; its request contains exactly `node_id: UUID` |
| Exact projection parity | field-by-field equality with one authorized `EngineeringObjectResponse`; `node_id` remains UUID; `node_type` is only the closed contract discriminator; no strengthened, synthetic, or extra canonical field |
| Canonical node authorization | active actor/trusted Organization success; inactive actor, disabled/nonmember Organization, cross-Organization, cross-Project, cross-Workspace, nonexistent, and inaccessible equivalence |
| Scope matching | supplied Project/Workspace scope is independently authorized and equals the authorized canonical response before projection |
| Protected outcomes | identical stable category/body schema and no identity, count, diagnostic, SQL, stack, plaintext, or partial projection across representative protected cases |
| Measurable side-channel policy | no intentionally protected-state-dependent diagnostic, count, delay, or post-denial query; bounded query-class/count comparison |
| Read-only ownership | before/after authoritative state equality; no EKG model, Repository, UoW, table, migration, Audit, outbox, idempotency, event, version, or canonical write |
| Performance | exactly one bounded scope decision and at most one authorized Engineering Object read; denied scope causes zero object reads; no unrelated canonical call |
| Scope/exclusions | static prohibited-pattern/import/file checks and adjacent/full regression |

### 14.2 NON-EXECUTABLE / NON-BLOCKING Deferred Prerequisite-Enabled Evidence

This table is traceability for a future focused IDS amendment. It is not a V1
implementation blocker, acceptance gate, authorized test scope, or authority to
create prerequisite contracts.

| Deferred contract | Evidence required only after prerequisite acceptance |
|---|---|
| Engineering Relationship frontier | vocabulary parity, endpoint and composite-scope authorization before expansion, batch behavior, deterministic order, secure continuation |
| Context Relationship frontier | four-meaning parity, endpoint-kind combinations, typed batch results, protected endpoint resolution, deterministic order |
| Additional node types | positive typed/batched Context, Project, Workspace, discipline, and external-source projection plus protected denial matrices |
| Path authorization intersection | denial at start, edge, intermediate, terminal, field, provenance, Workspace, and Project with dependent-path removal |
| Cross-scope traversal | cross-Organization prohibition and explicit all-authority permission for cross-Workspace/Project paths |
| Traversal maxima | depth 1–5, fan-out/node/edge/page maxima, over-bound validation, bounded call instrumentation |
| Deterministic pagination | shuffled-source equivalence, stable tie-breakers, page/continuation consistency |
| Cycles and duplicates | directed cycles, parallel edges, repeated endpoints, hidden-intermediate removal |
| Continuation | authenticated round trip, tamper, expiry, actor/scope/query mismatch, revocation, version mismatch, plaintext exclusion |
| Provenance/Evidence | authorized safe reference, lifecycle/scope/visibility denial, body/plaintext exclusion |

Independent IDS review must verify every §14.1 row is implementable from the
current Engineering Object boundary. Section 14.2 remains non-executable until
separate prerequisites and a focused IDS amendment are accepted.

## 15. Downstream Separation

IDS-033 fully decides the executable V1 actor, scope, single-node request,
single authorized Engineering Object read, exact projection, result variants,
authorization, protected outcomes, query budget, and prohibited patterns.
Everything in the deferred annexes is non-executable, non-blocking, and absent
from current V1 DTOs, ports, outcomes, acceptance criteria, and evidence.

An authorized Implementation Plan may inventory repository reality, name exact
files, sequence contract/adapters/service/transport/tests, define commands and
evidence collection, and stop on missing canonical ports. It cannot change
these semantics.

Implementation must prove the verification matrix, canonical adapter behavior,
request-scoped composition, plaintext exclusion, exact file scope, adjacent
regressions, and full regression. It may not create EKG persistence or writes.

Explicitly out of scope remain EDS-030/PATCH-030, EDS-031/PATCH-031, graph
database adoption, arbitrary edges, semantic/vector search, Organizational
Memory, AI, frontend, canonical ownership changes, and all mutation.

## 16. Deferred Canonical-Read Prerequisites

No prerequisite is implemented or designed by PATCH-033. Future expansion
requires separately governed canonical owners to provide:

1. Engineering Relationship: typed, batch-capable, authorization-before-
   expansion frontier reads; independent endpoint authorization; composite
   Workspace/Project scope decisions; deterministic authorized ordering; and
   secure bounded continuation.
2. Engineering Context Relationship: inward typed DTO/port rather than
   mappings; authorization-aware batch frontier reads; independently authorized
   endpoint projections; composite scope decisions; deterministic ordering;
   and no direct EKG repository access.
3. Engineering Context, Project, and Workspace: typed batch node-resolution
   results with one protected outcome per requested key and safe fields.
4. Discipline and external source: canonical scoped identity and authorization
   contracts suitable for protected node resolution.

Until those prerequisites complete separate governance, their nodes and edges
remain excluded. No implementation workaround is permitted.

## 17. Focused Review Findings Disposition

```text
IDS033-MAJ-01: RESOLVED — CONTEXT RELATIONSHIP EDGES REMOVED FROM V1
IDS033-MAJ-02: RESOLVED — V1 NODE ALLOW-LIST NARROWED TO ENGINEERING OBJECT
IDS033-MAJ-03: RESOLVED — TYPES, SIGNATURES, CARDINALITY, ORDERING, AND OUTCOMES CLOSED
IDS033-MAJ-04: RESOLVED — ENGINEERING RELATIONSHIP EDGES DEFERRED PENDING SAFE CANONICAL READS
IDS033-MIN-01: RESOLVED — MEASURABLE NON-DISCLOSURE POLICY REPLACES TIMING EQUALITY
IDS033-RR-MAJ-01: RESOLVED — V1 AND DEFERRED EVIDENCE MATRICES SEPARATED
IDS033-RR-MAJ-02: RESOLVED — PROJECTION FIELDS MATCH CANONICAL RESPONSE EXACTLY
IDS033-RR-MIN-01: RESOLVED — SPECULATIVE EDGE-ORIENTED FIELDS REMOVED
IDS033-RR2-MAJ-01: RESOLVED — DEFERRED TYPES REMOVED FROM EXECUTABLE V1
IDS033-RR2-MAJ-02: RESOLVED — SYNTHETIC NAVIGATION FIELD REMOVED
```

## 18. IDS Decision

```text
IDS-033 design: COMPLETE
IDS-033 status: ACCEPTED / COMPLETE
PATCH-033 alignment: PASS
EDS-033 alignment: PASS
Graph-owned state/mutation: PROHIBITED
Independent IDS Review: PASS AFTER FOCUSED AMENDMENTS AND FINAL RE-REVIEW
Human IDS Acceptance: PASS
Implementation-Plan-033: ACCEPTED / COMPLETE
Implementation authority: NOT GRANTED
```
