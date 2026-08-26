# Architecture-048 — Governed Project Context Assembly & EKG Read Expansion

## 1. Status and roadmap authority

**ACCEPTED / COMPLETE.** Independent Architecture Review and QG-M1 are PASS.
Human Architecture Acceptance grants authority for EDS-048 design only.

The Human-frozen Commercial V1 roadmap fixes PATCH-048 as the P0, very-high-
complexity, Phase-1 capability **Governed Project Context Assembly & EKG Read
Expansion**. Its business boundary is bounded authorized context across
accepted capabilities, dependent on PATCH-044–047, with no new source ownership
and protected bounded retrieval.

## 2. Problem and current capability gap

After PATCH-047, SATCO has canonical Project basis, execution, deliverables,
controls and earlier Engineering Intelligence facts, but an engineer must visit
separate product surfaces to understand their authorized Project context.
PATCH-033's executable EKG supports only one authorized Engineering Object node
and no edge. Existing Engineering Context and Context Relationship services are
older concrete Session/repository services and do not yet expose the typed,
batch-safe, protected application read contracts needed by a cross-domain
composer.

PATCH-048 enables an authorized engineer to inspect one bounded Project Context
and navigate explicit related engineering facts without changing any source.
It does not calculate completeness, recommend actions or materials, or create
an AI answer; those remain PATCH-049+ concerns.

## 3. Architectural decision

PATCH-048 is a **read-only request-time composition capability**. It owns:

- the Project Context section taxonomy and composition request/result contracts;
- discriminated canonical selectors used only to ask owning applications for
  authorized projections;
- the distinction between contextual membership and authoritative graph edges;
- deterministic bounded one-hop EKG read orchestration;
- safe result, continuation and non-disclosure behavior;
- the Project-contextual frontend composition.

It owns no canonical engineering fact, aggregate, lifecycle, relationship,
Repository, Unit of Work, Session, table, migration, materialized snapshot,
cache of protected data, Audit domain, outbox event, idempotent command or
mutation. A returned composition is an ephemeral observation, not a globally
atomic Project snapshot and never a new source of truth.

## 4. Canonical ownership model

Canonical facts retain their accepted owners:

| Fact | Owner retained |
|---|---|
| Project identity/lifecycle/customer | Project |
| purpose, engineering basis, scope, completion basis, required inputs, stage/readiness | PATCH-044 Project Foundation subordinate component |
| Plan, revisions, Activities, Milestones, dependencies and local blockers | PATCH-045 Engineering Execution |
| Deliverables, immutable revisions, external authority and file representation link | PATCH-046 Engineering Deliverable |
| Risks, Issues, Human Decisions, Changes and Change Impacts | PATCH-047 Project Control |
| Engineering Objects and Engineering Relationships | their existing canonical capabilities |
| Engineering Context, Context Relationships and Interface Commitments | their existing canonical capabilities |
| Capture, Evidence, Supporting File, Technical Report and Organizational Memory | their existing canonical capabilities |
| Journal | presentation-only; no independent persistent node identity |

Project-context inclusion is a read grouping, not ownership transfer. Shared
Project or Workspace scope alone never creates an EKG edge. Source projection
DTOs cannot be reused as PATCH-048 write contracts.

## 5. Identity model

Every selector is discriminated by canonical kind and carries only the identity
the owning capability already recognizes:

| Kind | Canonical selector / identity rule |
|---|---|
| Project | positive integer `project_id` |
| Project Foundation | parent `project_id`; no independent UUID |
| Engineering Execution Plan | canonical Plan UUID; one Plan per Project |
| Activity / Milestone / execution dependency | canonical UUID owned by Engineering Execution |
| Deliverable / Deliverable Revision | canonical UUID |
| Risk / Issue / Human Decision / Change / Change Impact | canonical UUID |
| Engineering Object / Engineering Relationship | canonical UUID |
| Engineering Context | current owner-supported positive integer identity; its opaque `context_key` is not substituted as a selector without a canonical contract |
| Context Relationship / Interface Commitment | current owner-supported positive integer identity; opaque keys remain owner-governed metadata |
| Capture / Evidence / Supporting File / Technical Report / Organizational Memory | canonical UUID where an eligible explicit relation and authorized read exist |
| Workspace | positive integer `workspace_id`, always validated inside the Project and Organization |
| Journal | no node selector; navigation remains a view over canonical sources |

No synthetic Foundation UUID, universal graph UUID or stringified composite
identity is permitted. EDS/IDS must inventory each owner-supported read
selector and exclude any class that lacks a safe typed application boundary.

## 6. Project Context assembly

The minimum product operation is `assemble_project_context` for one trusted
Organization, one authorized Project and optional authorized Workspace filter.
The result is divided into typed sections for Project/Foundation, execution,
deliverables, Project controls and eligible earlier Engineering Intelligence
facts. Each item retains its canonical kind, selector, current safe projection,
source version/standing when authorized, and canonical navigation reference.

Section membership means only “this authorized canonical fact belongs to or is
explicitly scoped to this Project/Workspace under its owner contract.” It is
not a graph edge or engineering conclusion. Empty means no visible item; it
does not distinguish no item from an inaccessible item. Hidden/global totals,
denied counts and inaccessible section markers are prohibited.

The composer calls typed canonical application read ports. It never imports or
uses a foreign repository, ORM model, Session, UoW or transport router. Missing
safe owner contracts are explicit EDS/IDS prerequisites; direct persistence is
not a fallback.

## 7. EKG read expansion

PATCH-033's authorized `engineering_object/get_node` contract remains valid.
PATCH-048 may extend executable reads with:

1. a typed authorized node lookup for an EDS/IDS-approved closed node set; and
2. a deterministic, bounded **one-hop** `list_related` operation from one
   authorized start selector.

An edge is projected only when an accepted canonical owner already records and
authorizes its exact meaning. Eligible relationship sources are limited to:

- Engineering Relationship family/type edges;
- Engineering Context Relationship meanings;
- Engineering Execution Activity dependencies and Milestone–Activity links;
- Deliverable–Activity/Milestone and Revision–Supporting File links;
- PATCH-047 typed links, predecessor relationships and Change Impacts;
- canonical Evidence/Supporting File or report/provenance relationships only
  where the owning application expressly exposes them as a safe relationship.

Project membership, common scope, timestamps, similar text, provenance mere
co-occurrence, Journal navigation and AI output never imply an edge. Reverse
navigation reverses read direction only. No generic path query, arbitrary
depth, relationship creation, inferred vocabulary or graph editor is in V1.

Every edge and both endpoints are independently authorized. Denial removes the
edge and dependent destination without revealing the denied element or denial
location. EDS/IDS must define a closed node/edge allow-list from actual safe
owner ports; unsupported kinds return payload-free `invalid_request`.

## 8. Authority model

- **Human-authoritative:** source facts and accepted Human transitions remain
  authoritative only inside their owning capabilities.
- **External-tool-authoritative:** Deliverable authored content remains under
  its declared CAD/EPLAN/ETAP/document/vendor tool authority.
- **Derived:** execution progress and other owner-approved derived projections
  retain their source inputs, calculation meaning and limitations.
- **Contextual/advisory:** the assembly order, section grouping and graph
  navigation are non-authoritative presentation.
- **Historical:** superseded/withdrawn/history facts remain explicitly marked
  and are never substituted for current standing.
- **Future AI-consumable:** a later authorized intelligence capability may
  consume the same protected ports; PATCH-048 creates no AI inference or
  authority.

No read, repeated use or graph placement promotes a fact, changes standing,
accepts evidence, admits Organizational Memory or transfers Human authority.

## 9. Read, bounds and consistency

Reads are request-scoped and current-authorized. The architecture fixes these
invariants; EDS/IDS closes exact DTO fields and lower limits:

- one Organization and one Project per request;
- optional Workspace must be current, same-Project and independently visible;
- one-hop maximum for related expansion;
- hard maxima for evaluated candidates, returned nodes/edges, canonical calls,
  response size and execution time;
- deterministic ordering by canonical kind, stable encoded canonical selector,
  relationship source/semantic/direction and stable relationship identity;
- opaque, integrity-protected, expiring continuation bound to actor,
  Organization, Project, Workspace, query, ordering version and last evaluated
  key;
- authorization rechecked on every page; no skip/duplicate or hidden total;
- cycles cannot expand because V1 is one-hop; duplicate canonical edge keys are
  emitted at most once.

Each projection carries sufficient source version/standing and observation
time to avoid implying global transactional consistency. A later source change
does not mutate a past response, and a past response grants no future access.

## 10. Security and non-disclosure

Actor and Organization come only from trusted server authentication.
Authorization order is Organization → Project → optional Workspace → source
item/relationship → selected fields. Organization permission alone never
implies Project, Workspace, file, Evidence, report, memory or relationship
permission.

Cross-Organization composition/traversal is always prohibited. Cross-Project
and cross-Workspace edges are excluded in V1. Private storage keys, object-store
paths/URLs, file bodies, Evidence protected facts, Capture/report/memory body,
Human rationale, confidential context, raw ORM state and exception details are
not default context or graph fields.

Closed outcomes are `success`, payload-free `protected_not_found`, payload-free
`invalid_request` and payload-free `unavailable`. Specific denied reads reveal
no identity, existence, counts, path, policy, source class or denial reason.
List/assembly reads return only visible items and visible-item counts when a
count is required; they expose no hidden/global/authorized total.

## 11. Mutation, reliability and audit

PATCH-048 has no domain mutation, transaction spanning canonical owners,
idempotent command or outbox event. Source commands continue through their
owners with their existing expected-version, Audit, outbox, idempotency and UoW
rules. The composer cannot coordinate or partially commit source mutations.

Read access may use existing bounded security/operational logging when required
by governance, but logs must contain safe operation/scope categories and
correlation identifiers only—not protected payload, hidden identities, tokens,
denial detail or source content. Continuation signing/key rotation and failure
behavior are reliability/security obligations for EDS/IDS. Dependency failure
fails closed and never falls back to foreign persistence or stale cached truth.

## 12. Frontend and product experience

PATCH-048 adds one contextual Project “Engineering Context” surface that:

- presents Project basis, execution, deliverables and controls in clear typed
  sections with related-context navigation;
- uses canonical names and safe links rather than raw internal identifiers;
- distinguishes authoritative, derived, external-tool, historical and
  contextual/advisory facts;
- provides truthful empty, loading, protected, unavailable and success states;
- supports keyboard use, labelled controls, focus visibility and non-color-only
  standing distinctions;
- stacks responsively without horizontal overflow and uses direction-neutral
  layout primitives;
- displays real authorized API data only and never demo/fake production totals.

A decorative graph canvas, graph editing, AI chat, recommendations and
completeness scoring are excluded. English remains the current UI; strings are
isolated and contracts use locale-neutral codes and timestamps so future
English/Persian and Arabic-ready presentation is not blocked.

## 13. Backward compatibility and migration

No migration or backfill is justified by this read-composition architecture.
Legacy Projects with no Foundation, Plan, Deliverable or Control records show
truthful empty/not-established states. Existing canonical records are neither
rewritten nor fabricated. PATCH-033's single-node API remains compatible; any
new transport is additive and separately versioned/bounded in EDS/IDS.

## 14. Extension seams and exclusions

PATCH-049 may consume authorized context to identify missing information, but
must remain explainable, evidence-linked and Human-reviewed. PATCH-050 may add
advisory engineering/material direction. Neither authority exists here.

Deferred: completeness/health scoring, recommendations, material/BOM direction,
procurement, FAT/SAT, closeout, notifications, lifecycle wizard, broad command
center redesign, entitlements, graph persistence, graph database, embeddings,
semantic/vector search, multi-hop traversal, cross-Organization sharing,
autonomous AI, inferred or AI-authored relationships, generic PM/BPM/EDMS,
external-tool authoring, PLC/DCS/SIS/SCADA generation, translation completion
and PATCH-049+ implementation.

## 15. ADR/XDR assessment

No new ADR or XDR is required. This architecture applies ADR-015 Engineering
Context, ADR-017 EKG Evolution, ADR-020 Open Extension and ADR-021 Engineering
Intelligence Core without changing them. PostgreSQL remains SSOT; the existing
EKG Core is extended through governed application ports. A future graph store,
cross-Organization graph, inferred vocabulary, autonomous AI authority or
graph-owned mutation would require separate architecture and may require an
ADR/XDR.

## 16. EDS-048 obligations

EDS-048 must close the exact section/node/edge allow-lists against current
canonical application responses; typed owner-side read ports; safe field
projections; operation/result contracts; per-source failure behavior; hard
bounds, ordering and continuation; security/Audit logging; composition root;
thin transport; UI states; verification obligations; and any owner-side port
prerequisite. It must exclude a source rather than use direct persistence or
invent an identity/authority contract.
