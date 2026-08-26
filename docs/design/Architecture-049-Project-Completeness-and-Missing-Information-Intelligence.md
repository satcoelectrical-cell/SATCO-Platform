# Architecture-049 — Project Completeness & Missing-Information Intelligence

## 1. Status and roadmap authority

**ACCEPTED / COMPLETE.** Independent Architecture Review and QG-M1 are PASS.
Human Architecture Acceptance grants EDS-049 design authority only.

The Human-frozen Commercial V1 roadmap fixes PATCH-049 as the P0, high-
complexity, Phase-2 capability **Project Completeness & Missing-Information
Intelligence**. It depends on PATCH-044 through PATCH-048; PATCH-048 is its
immediate protected input seam. PATCH-050 remains the separately governed owner
of Engineering Guidance and Preliminary Material Direction.

## 2. Purpose and current capability gap

PATCH-048 can assemble a bounded authorized Project Context and navigate
explicit one-hop relationships, but SATCO cannot yet explain which required
information is visibly present, safely absent, indeterminate or not disclosed.
Engineers must manually cross-check Project basis, execution, deliverables,
controls and engineering-intelligence facts without one governed completeness
view.

PATCH-049 closes only that gap. It derives bounded, explainable questions and
checklist items from deterministic rules. It does not declare a Project
complete, approve engineering work or recommend an engineering solution.

## 3. Architectural decision and ownership

PATCH-049 is a **read-only request-time derived-intelligence capability**. It
owns:

- a closed, version-controlled V1 completeness rule catalog;
- rule applicability and deterministic evaluation semantics;
- safe classification, explainability and partiality contracts;
- derived finding, clarification-question and checklist projections;
- protected result behavior and the Project-level Completeness experience.

It owns no Project or Workspace fact, source identity, engineering standing,
aggregate, database, Repository, Unit of Work, Session, transaction, Audit
domain, outbox, idempotent command, task, accepted knowledge or graph edge.
Canonical sources retain their accepted owners. A completeness result is an
ephemeral observation, not a new System of Record.

## 4. Canonical input model

The primary input is one freshly authorized PATCH-048 typed
`ProjectContextResult` for a trusted actor, server-derived Organization, one
authorized Project and optional authorized Workspace. PATCH-049 consumes that
application contract, not its router and not any foreign persistence.

Eligible facts remain owned by:

| Input family | Canonical owner |
|---|---|
| Project basis, scope, inputs, lifecycle and completion basis | Project / PATCH-044 Project Foundation |
| Plan, Activities, Milestones and dependencies | PATCH-045 Engineering Execution |
| Deliverables and revisions | PATCH-046 Engineering Deliverable |
| Risks, Issues, Human Decisions, Changes and impacts | PATCH-047 Project Control |
| Context, Objects and explicit Relationships | existing Engineering Intelligence owners |
| Evidence, Supporting Files, Reports and Memory | their existing canonical capabilities |

Only safe projections already authorized by PATCH-048 may enter evaluation.
No raw repository model, ORM entity, Session, UoW, storage key, private URL,
Human identity or protected continuation may cross this boundary.

## 5. Derived output model

The application exposes a closed result union with at least `success`,
`protected_not_found`, `invalid_request` and `unavailable`. Protected outcomes
are payload-free.

A success contains:

- rule-catalog identity, version and digest;
- trusted scope and a bounded observation interval;
- `complete_within_observable_bounds` or `partial` observation status, never a
  Project approval or overall-completeness declaration;
- deterministically ordered findings;
- bounded clarification questions and checklist items;
- visible evidence references only;
- limitations and explicit upstream/output truncation indicators.

No global, hidden or authorized total is disclosed. “No visible findings within
bounds” is permitted; “the Project is complete” is not.

## 6. Completeness classification semantics

Every evaluated applicable rule has exactly one safe classification:

| Classification | Meaning |
|---|---|
| `PRESENT` | All required predicates are established by visible, authorized and sufficiently complete observations. |
| `MISSING` | Applicability is established and the owning boundary safely establishes absence within a complete observable scope. |
| `INDETERMINATE` | Applicability or presence cannot be decided because observation is unavailable, partial, stale-in-use, inconsistent, truncated or otherwise insufficient. |
| `NOT_DISCLOSED` | A required source or reference is protected/not disclosed; no existence, identity, count or denial reason is revealed. |
| `NOT_APPLICABLE` | A deterministic applicability predicate is false using visible facts only. It is not presented as a gap. |

`NOT_APPLICABLE` is justified because applicability is separate from
completeness. Unknown applicability is `INDETERMINATE`, never
`NOT_APPLICABLE`.

A rule may return `MISSING` only when all inputs needed to establish both its
applicability and safe absence are visible and untruncated. An explicit
owner-returned `not_established` state may establish absence where the rule
requires that capability. Empty but protected, unavailable or truncated input
cannot. `NOT_DISCLOSED` and `INDETERMINATE` never contribute to a missing count
or implied failure.

## 7. Deterministic rule architecture

V1 uses a static, source-controlled, application-owned rule catalog. There is
no database rule table, runtime rule authoring, tenant override, uploaded rule
script or provider-generated rule.

Each rule declares a closed definition containing:

- stable namespaced `rule_id` and positive immutable `rule_version`;
- category and safe Human-readable purpose;
- typed applicability predicates;
- typed required observable facts and presence predicates;
- optional explicit one-hop evidence requirement;
- safe finding, question and checklist templates;
- limitations and evidence-reference policy.

Changing meaning creates a new rule version. A catalog version and canonical
digest bind the exact ordered definitions evaluated. Catalog validation occurs
before service availability and rejects duplicate IDs/versions, unsupported
selectors, unsafe templates, unbounded multiplicity or limits exceeding the
IDS contract.

For identical authorized input projections, catalog version and evaluation
parameters, classification and rendered content are deterministic. Observation
timestamps are attribution, not rule input unless a rule explicitly uses a
visible canonical temporal field.

## 8. Rule applicability model

Applicability may use only closed typed facts expressly visible in Project
Context, such as Project stage, declared discipline, Workspace scope or an
explicit canonical source kind. It may not infer applicability from free text,
co-occurrence, similarity, hidden counts, Organization convention, repeated
use or model output.

Discipline-specific rules apply only when discipline is explicitly visible and
matches the closed rule predicate. Missing or protected applicability facts
yield `INDETERMINATE` or `NOT_DISCLOSED`. V1 has no customer-configurable rule
builder, arbitrary expressions or rule code supplied through transport.

## 9. Evaluation sequence

The service executes one fixed sequence:

1. acquire trusted actor and server-derived scope;
2. request a fresh authorized Project Context observation;
3. fail closed on protected/invalid/unavailable root outcomes;
4. validate catalog identity and deterministic rule order;
5. evaluate applicability from visible facts;
6. request optional bounded one-hop evidence only for an applicable rule that
   declares that dependency and has an already authorized visible seed;
7. classify using the conservative truth table in Section 6;
8. attach visible evidence, questions, checklist items and limitations;
9. enforce all bounds before transport serialization.

Rules are evaluated in stable `(rule_id, rule_version)` order. Evaluation does
not dynamically discover rules or recurse over findings.

## 10. Evidence and reference model

Evidence is an authorized reference to a visible canonical projection; it is
not a copied source body and never becomes PATCH-049-owned evidence. Each safe
reference identifies the canonical kind, an owner-recognized opaque navigation
reference or selector, source version/standing when already disclosed, and the
specific predicate it supports.

The transport/frontend must not display raw internal IDs. Exact safe link and
selector DTOs are EDS/IDS obligations and must reuse existing protected
navigation patterns. No Human identity, private storage key/URL, inaccessible
provenance or hidden relationship endpoint is emitted. Evidence absence is
never manufactured.

## 11. Explainability model

Every returned finding carries:

- `rule_id`, `rule_version` and catalog version/digest;
- explicit applicability basis using only disclosed facts;
- classification and bounded safe rationale code/text;
- zero or more visible evidence references;
- observation start/completion timestamps;
- upstream partiality and relevant limitations;
- evidence/output truncation state.

Explanations are deterministic templates, not model prose. They distinguish
“not observed within authorized bounds” from “missing.”

## 12. Clarification-question model

Questions are deterministic bounded templates owned by the rule definition.
They ask a Human to establish or verify information through the appropriate
canonical workflow; they do not answer the question, recommend a solution or
create a task.

Template substitution accepts only closed, already disclosed safe fields.
Unknown/protected values remain generic and cannot be interpolated. Duplicate
questions are deterministically deduplicated and ordered. Exact template
grammar, length and cardinality are IDS obligations.

## 13. Checklist model

Checklist items are ephemeral verification prompts derived from rules. They may
express satisfied, outstanding or indeterminate observable conditions, but
they are not persistent tasks, milestones, approvals or manually stored check
states. Each item retains its originating rule/version and classification.

The checklist cannot assign a Human, due date, owner, standing or completion
percentage. Acting on an item occurs separately through the canonical owning
capability under its normal Human authority.

## 14. Authority classification

All PATCH-049 output is **derived, advisory and non-authoritative**. It cannot:

- approve or certify a Project;
- change a canonical standing, lifecycle, readiness or progress value;
- become accepted Engineering Knowledge or Organizational Memory;
- create an Engineering Relationship, Evidence claim or source fact;
- constitute an engineering decision, recommendation or professional result.

The catalog defines evaluation policy, not engineering truth. Canonical source
facts and accountable Human decisions remain authoritative.

## 15. Human authority boundary

An authenticated authorized Human explicitly requests and reviews the result.
Viewing, refreshing, exporting or referencing it does not accept it. Humans may
respond only through existing owner workflows—for example, establishing a
Project input, revising a Deliverable or recording a Risk. PATCH-049 never
performs those commands on their behalf.

No “accept assessment” operation exists in V1. Any future persisted review or
adoption lifecycle requires separate architecture and Human authority.

## 16. Read-only and reliability boundary

PATCH-049 has no command, transaction, optimistic concurrency, idempotency,
outbox or domain-event requirement. It may use request-local immutable values
and bounded memoization only; no protected result survives the request.

Existing access/security audit policy may record the operation and bounded safe
metadata/digests, but not assessment content, hidden identities or source
bodies. PATCH-049 introduces no new Audit schema or persistence owner.

## 17. Project Context integration

PATCH-048 remains the only cross-owner composition seam. PATCH-049 invokes its
application service with a fresh trusted actor/scope; it does not reuse an old
client-supplied result or continuation, call its transport endpoint internally,
or bypass owner authorization.

Section availability, partiality, source standing, authority classification,
temporal attribution and truncation remain attached. PATCH-049 cannot broaden
fields or reinterpret `not_disclosed` as empty.

## 18. Optional EKG integration

One-hop EKG input is optional and rule-declared. It may be requested only after
the seed node is visible and authorized through PATCH-048. PATCH-048 continues
to enforce its closed node/relationship allow-list, start/edge/target
authorization, scope, bounds and protected outcomes.

PATCH-049 performs no generic traversal, relationship inference, second hop,
neighbor enrichment, semantic expansion or continuation reuse. An unavailable,
protected or truncated optional graph result can only preserve `PRESENT` where
sufficient visible evidence already exists; absence-based conclusions become
`INDETERMINATE` or `NOT_DISCLOSED`.

## 19. Non-atomic observation semantics

Project Context is assembled from independently authorized owner reads and is
not a distributed transaction. PATCH-049 therefore describes an observation
interval, not a globally atomic Project snapshot.

The result carries observation start/completion times, catalog version and
partiality. It may state that facts were observed during that interval. It may
not state that the Project was globally complete at an instant or that sources
could not have changed between reads. A refresh is a new assessment, not a
revision of persisted state.

## 20. Partiality semantics

| Input condition | Safe behavior |
|---|---|
| complete visible input within bounds | evaluate applicable rules normally |
| available and explicitly empty/unestablished input | permit `MISSING` only when rule applicability and absence are safely established |
| partial or truncated input | preserve visible `PRESENT`; absence-dependent results become `INDETERMINATE` |
| unavailable dependency | root failure if primary context is unavailable; otherwise affected rules become `INDETERMINATE` |
| not-disclosed/protected dependency | affected rules become payload-safe `NOT_DISCLOSED` |
| optional EKG unavailable | continue only where the rule remains decidable without it; otherwise `INDETERMINATE` |

Overall observation status is partial whenever any evaluated applicable rule
is indeterminate/not disclosed or any relevant input/output is truncated. It
is not a Project completeness status.

## 21. Security and non-disclosure

- Actor identity comes only from trusted authentication; Organization is
  server-derived.
- Project and Workspace authorization precede analysis and disclosure.
- Every optional EKG seed, edge, target and reference remains independently
  authorized by PATCH-048.
- Cross-Organization and cross-Project analysis is prohibited.
- Protected results expose only their discriminator.
- Findings expose no hidden/global/authorized totals, denied counts, Human
  identities, denial reasons, source bodies, storage keys/URLs or inaccessible
  provenance.
- Rule wording must not reveal that a protected object exists. A static expected
  information category may be named; hidden instances, counts and states may
  not.
- Transport errors, logs and metrics contain no protected assessment payload.

Because V1 uses no model-backed AI, authorized Project data is not transmitted
to an AI provider.

## 22. Bounds and truncation

EDS/IDS must close finite numeric limits for:

- catalog/rule count and predicates per rule;
- findings, questions and checklist items;
- evidence references per finding and in total;
- optional EKG operations, candidates and owner calls;
- template and rendered text lengths;
- evaluation time and serialized response size.

The source-controlled catalog must validate within those limits as a whole; V1
does not silently skip catalog rules at runtime. Findings and sub-items use
stable ordering and deterministic deduplication. If evidence or a source is
truncated, affected absence-based conclusions become `INDETERMINATE`; no hidden
remainder total is exposed.

V1 requires no result pagination or PATCH-048 continuation reuse. If IDS proves
a single bounded response cannot be safe, it must stop for Architecture review
rather than invent a persisted or cross-observation cursor.

## 23. Persistence and migration assessment

Request-time evaluation is sufficient for the frozen V1 purpose. The catalog is
version-controlled code/data shipped with the application; results are not
saved. Therefore PATCH-049 owns no table, assessment history, rule store,
cache, search index or background job and requires **no migration**.

Persisted assessments, configurable catalogs, Human review history, customer
rule builders or analytics require a separately accepted future boundary. No
legacy backfill or fabricated assessment is permitted.

## 24. Backward compatibility

PATCH-049 is additive. PATCH-048 Project Context/node/one-hop contracts remain
independently usable and unchanged. Canonical source schemas, ownership,
lifecycle and commands remain unchanged. Existing Capture and Technical Report
AI/provider-neutral seams remain unchanged and unused by PATCH-049.

Projects with sparse data receive truthful missing/indeterminate results within
observable bounds; no synthetic data is created to make the feature appear
complete.

## 25. Frontend and product experience

The minimum product surface is one Project-level **Completeness** experience
integrated with the existing Project Engineering Context surface. A Human can
request/refresh an assessment and inspect grouped findings, distinctly styled
missing/indeterminate/not-disclosed states, clarification questions, checklist
items, visible evidence/context links, observation time, partiality,
limitations and truncation.

The surface provides truthful loading, empty, protected, invalid and unavailable
states. It contains no generic chat, recommendation composer, score, percentage,
fake total or fake production record. “No visible gaps within bounds” is
visually distinct from Project approval.

## 26. Accessibility, responsive and RTL readiness

Findings use semantic headings, lists and status text rather than color alone.
All controls are keyboard operable with visible focus, protected/live results
use appropriate announcements without repeated noise, and evidence links have
descriptive accessible names. Layout is direction-neutral, resilient under text
expansion and usable at narrow and desktop widths. No interaction creates a new
durable cross-PATCH navigation or experience convention.

## 27. Track-B and external-tool boundary

Professional engineering tools remain authoritative for native artifacts.
PATCH-049 evaluates only SATCO-visible governed facts and safe external-tool
references already represented by canonical owners. It neither opens nor
interprets inaccessible external document bodies, nor claims their content is
complete, nor authors/changes CAD, EPLAN or other professional deliverables.

## 28. PATCH-050 boundary and explicit exclusions

PATCH-050 owns future project-specific Engineering Guidance and Preliminary
Material Direction, including solution-oriented recommendations and preliminary
material/BOM direction. PATCH-049 may ask what required information is absent;
it may not tell the engineer which technical solution or material to select.

Also excluded: Project-health scoring, procurement, licensing/anti-copy, AI/
provider routing, RAG, embeddings/vector/semantic search, generic chat,
autonomous engineering/workflow, automatic tasks, graph persistence/database,
multi-hop traversal, configurable customer rules, persisted assessment/review
history, cross-Organization analysis and PATCH-050 implementation.

## 29. Future extension seams

- PATCH-050 may consume a freshly authorized PATCH-049 result through a typed
  advisory port; it cannot treat the result as canonical truth.
- A later health capability may reuse classifications only after fresh source
  authorization and its own accepted design.
- Persisted Human review, configurable discipline packs and saved assessments
  require separate architecture and migration authority.
- If future model-backed phrasing or reasoning is approved, the domain/
  application contract must remain provider-neutral and use a narrow outward
  port. Existing providers remain replaceable; provider conversation state is
  never authority.

## 30. Architecture invariants and EDS obligations

Architecture invariants:

1. Input is freshly authorized PATCH-048 Project Context; optional graph input
   is PATCH-048-authorized one hop only.
2. Protected/unavailable/truncated information is never classified missing.
3. Every finding is deterministic, rule-versioned, evidence-linked where
   visible, limitation-aware and Human-reviewable.
4. Output is derived/advisory and never mutates or approves canonical state.
5. No overall score/percentage, hidden total, Human/private-storage identity,
   model-backed AI or provider data egress exists.
6. No persistence, migration, background job, graph store or source ownership
   exists.
7. PATCH-050 recommendations/material direction remain excluded.

EDS-049/IDS-049 must close exact typed request/result unions, catalog/rule
schema and canonical digest, classification truth table, applicability grammar,
safe reference projections, templates, deterministic ordering/deduplication,
numeric bounds, partiality mapping, optional graph call matrix, authorization
matrix, transport/frontend states, logging/audit safety and an executable
negative/security/limit verification matrix. Any requirement for persistence,
model-backed AI, a generic provider runtime or broader source access is an
Architecture stop condition.

## 31. ADR/XDR assessment

No new ADR is required. This capability applies accepted ADR-018 Engineering
Intelligence Product Vision and ADR-021 Engineering Intelligence Core authority,
plus existing Context/EKG, open-extension, Human-authority and provider-
replaceability decisions. It creates no new durable cross-PATCH source,
provider, persistence or authority architecture.

No new XDR is required because the Completeness panel is a local additive
presentation following the accepted Project Engineering Context navigation,
status, accessibility and responsive conventions. EDS must stop for XDR review
if it discovers a new durable cockpit hierarchy, navigation, interaction or
cross-PATCH experience convention.
