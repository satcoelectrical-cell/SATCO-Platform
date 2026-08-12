# EDS-032 — Technical Report

## 1. Document Control

| Field | Value |
|---|---|
| Document ID | EDS-032 |
| Title | Technical Report |
| Related PATCH | PATCH-032 — Technical Report |
| Governing ADR | ADR-023 — Human-Accepted AI-Assisted Technical Reports as the SATCO V1 Engineering Authority Boundary |
| Status | ACCEPTED / COMPLETE |
| Owner | SATCO Product Owner / Platform Architecture |
| Architecture style | Docs-First Architecture |
| Technical Report Architecture Review | PASS |
| Human Architecture Acceptance | PASS |
| QG-M1 Manifesto Compliance | PASS |
| EDS design authority | GRANTED |
| Independent EDS Review | PASS after amendment and focused re-review |
| Focused Independent EDS-032 Re-review | PASS |
| Human EDS acceptance | PASS |
| Remaining findings | NONE |
| Governance reconciliation | PASS |
| Permission for IDS-032 design | GRANTED |
| IDS authority | GRANTED |
| Implementation authority | NOT GRANTED |
| Date | 2026-08-08 |

## 2. Purpose and Design Authority

This Engineering Design Specification defines the bounded domain and
application architecture of the SATCO Version 1 Technical Report capability.
It translates ADR-023 and PATCH-032 into a complete engineering design without
defining implementation, transport, persistence technology, or user-interface
details.

Technical Report is the durable Human engineering-authority boundary for an
exact accepted report revision. It receives authorized engineering context,
supports Human-directed and AI-assisted draft preparation, and preserves the
basis on which the Human accepts the result. It does not acquire ownership of
the canonical resources on which the report relies.

This EDS is subordinate to the Constitution, Engineering Intelligence
Manifesto, accepted Architecture and ADRs, ADR-023, and PATCH-032. A later IDS
may refine interfaces and implementation contracts only within this design.

## 3. Governing Sources and Traceability

The design is governed by:

- SATCO Platform Constitution;
- SATCO Engineering Intelligence Manifesto v1.0;
- accepted SATCO Architecture and ADRs;
- ADR-023 — Human-Accepted AI-Assisted Technical Reports as the SATCO V1
  Engineering Authority Boundary;
- PATCH-032 — Technical Report;
- PATCH-032 Architecture Review `PASS` as recorded by the authoritative
  governance state;
- Human Architecture Acceptance `PASS`;
- QG-M1 Manifesto Compliance `PASS`;
- the accepted Technical Report Architecture Discovery conceptual authority;
- existing Organization, Project, Engineering Workspace, EngineeringObject,
  Engineering Relationship, Evidence, Universal Capture, and Engineering
  Journal authorities.

No standalone repository artifact for the Technical Report Architecture
Discovery or PATCH-032 Architecture Review is asserted by this EDS. Their
accepted decisions are traced through ADR-023, PATCH-032, the Roadmap, and the
Governance Model.

## 4. Design Scope

This EDS defines:

- the `TechnicalReport` Aggregate and its consistency boundary;
- draft and accepted lifecycle semantics;
- draft revision and Aggregate concurrency semantics;
- exact-revision Human acceptance;
- immutable accepted snapshots;
- successor and predecessor traceability;
- report purpose and preliminary qualification semantics;
- authorized source intake and provenance/reliance ownership;
- Evidence, standards, engineering-context, and canonical capability
  boundaries;
- Organization, Workspace, and optional direct Project context;
- abandoned-draft semantics and the empty Version 1 post-acceptance mutation
  allow-list;
- advisory AI boundaries;
- domain failures and domain-significant outcomes;
- authorization-before-disclosure and operation-time authorization principles.

This EDS does not define APIs, DTOs, schemas, database structures, migrations,
repositories, provider integrations, user interfaces, or implementation
sequence.

## 5. Technical Report Aggregate

### 5.1 Aggregate Root

`TechnicalReport` is one dedicated persistent Aggregate Root. It is the sole
consistency boundary for the working draft, its exact revision, acceptance of
that revision, and report-owned provenance and contextual records.

The Aggregate owns:

- immutable Technical Report identity;
- Organization scope;
- Workspace scope;
- optional direct Project context;
- one Version 1 report purpose;
- engineering scope;
- mutable working-draft content while lifecycle is `draft`;
- exact draft revision identity;
- Aggregate concurrency version;
- preliminary qualification;
- assumptions;
- uncertainty;
- limitations;
- conclusions;
- recommendations;
- report-owned source, provenance, and reliance manifest;
- Evidence references and report-owned reliance context;
- standards references and report-owned reliance context;
- relevant EngineeringObject references;
- relevant Engineering Relationship references;
- report-owned contextual reference;
- lifecycle state;
- optional predecessor Technical Report reference;
- immutable accepted snapshot;
- Human acceptance record.

### 5.2 Aggregate Boundary

The Aggregate protects the coherence of its identity, scope, purpose, draft,
revision, acceptance basis, accepted snapshot, and lineage.
Changes to Aggregate-owned state occur only through explicit domain operations.
Generic field mutation is prohibited.

Referenced Organization, Workspace, Project, EngineeringObject, Engineering
Relationship, Evidence, Universal Capture, Engineering Journal, standards, and
external sources remain owned by their originating capabilities or authorities.
The Technical Report stores only its own governed reference and reliance
meaning.

### 5.3 Aggregate Invariants

At all times:

1. one Technical Report has exactly one immutable identity;
2. one Technical Report belongs to exactly one Organization and one Workspace;
3. optional direct Project context cannot contradict the Workspace's canonical
   Project relationship;
4. purpose belongs to the closed Version 1 vocabulary;
5. lifecycle is only `draft` or `accepted`;
6. only a draft may undergo material technical revision;
7. every material draft modification advances draft revision identity;
8. acceptance binds to the current draft revision and expected pre-acceptance
   Aggregate concurrency version;
9. an accepted snapshot and its Human acceptance record are immutable;
10. accepted technical content cannot be changed in place;
11. the successor exclusively owns its direct predecessor reference, and
    predecessor lineage cannot imply supersession or withdrawn authority;
12. materially relied-upon sources must satisfy the historical-resolvability
    requirements before acceptance;
13. AI never performs an authority-bearing operation;
14. another canonical capability is never mutated through this Aggregate;
15. an accepted Technical Report Aggregate is terminal and mutation-free.

## 6. Identity, Scope, and Ownership

Technical Report identity is stable for the lifetime of the Aggregate. It is
not derived from purpose, Project, Workspace, source identity, predecessor, or
accepted revision.

Organization scope is mandatory and trusted. Workspace scope is mandatory and
must belong to that Organization under the canonical Workspace and Project
ownership rules. Technical Report cannot infer, accept, or widen Organization
scope from AI input, source material, or an untrusted caller value.

Project is an optional direct Technical Report context. The Project identifier
and its relationship to Workspace are represented exactly as defined by the
canonical Project and Workspace capabilities. When a direct Project reference
is present, it must identify the Workspace's canonical Project and be
authorized for the Human. When absent, Technical Report creates no independent
Project identity or alternative Project association; the Workspace's canonical
relationship remains unchanged.

Technical Report owns its report content and reliance statements. It does not
own the entities, records, or source material to which those statements refer.

## 7. Report Purpose

The closed Version 1 purpose vocabulary is:

- `field_experience`;
- `troubleshooting`;
- `engineering_analysis`;
- `technical_recommendation`.

Purpose expresses the architectural meaning of the report. It is not a
template selector, presentation choice, lifecycle state, Review state, or
authorization shortcut.

Purpose is acceptance-defining. Changing purpose after acceptance is semantic
and requires a successor Technical Report Aggregate.

## 8. Lifecycle

The complete Version 1 lifecycle is:

```text
draft → accepted
```

`draft` means the report remains working technical material without accepted
engineering authority. Draft content may be revised through explicit Human
direction, including Human-directed AI assistance.

`accepted` means an authorized Human explicitly accepted one exact current
draft revision and the Aggregate preserved the resulting immutable snapshot
and acceptance record atomically.

The following are not Technical Report lifecycle states:

- submitted;
- in review;
- revision requested;
- rejected;
- withdrawn;
- approved;
- published;
- superseded;
- archived.

Revision is a draft operation. Engineering Review is the Human acceptance
operation. Acceptance is not publication. An accepted Aggregate cannot return
to draft.

## 9. Draft Revision and Aggregate Concurrency

### 9.1 Separate Identities

Aggregate concurrency version and draft revision identity have separate
meanings.

The Aggregate concurrency version protects compare-and-change consistency for
all governed Aggregate mutations. It detects whether the Aggregate state used
by a command is stale.

Draft revision identity identifies the exact technical draft reviewed by the
Human. It changes whenever technical meaning, content, purpose, engineering
scope, preliminary qualification, assumptions, uncertainty, limitations,
conclusions, recommendations, or the material reliance basis changes.

### 9.2 Revision Rules

Every material technical draft modification advances the draft revision
exactly once for that successful mutation. Transient AI proposals that are not
adopted into the working draft do not become draft revisions.

Administrative activity that changes neither technical meaning nor the draft's
acceptance basis must not manufacture a material draft revision. Before
acceptance, the Aggregate concurrency version may still advance for a governed
non-material mutation while draft revision remains unchanged; the operation
must preserve this distinction explicitly.

### 9.3 Acceptance Concurrency

Acceptance requires both:

- the expected pre-acceptance Aggregate concurrency version; and
- the exact current draft revision identity explicitly confirmed by the Human.

If either is stale, acceptance fails atomically. The lifecycle, accepted
snapshot, Human acceptance record, draft revision, and Aggregate state remain
unchanged. A failed stale acceptance cannot be retried as an implicit acceptance
of a newer draft.

Successful acceptance is itself one Aggregate mutation. It produces a new
post-acceptance Aggregate concurrency version while preserving the exact
accepted draft revision as a separate identity. The accepted snapshot records
both the exact accepted draft revision and the resulting post-acceptance
Aggregate concurrency version.

Because the Version 1 post-acceptance mutation allow-list is empty, the
resulting post-acceptance Aggregate concurrency version is terminal. No later
Technical-Report-owned operation may advance it.

## 10. Draft Operations

The Aggregate supports only bounded, intention-revealing draft behavior:

- create a Technical Report draft within authorized scope;
- revise the current draft under explicit Human direction;
- record or revise preliminary qualification and its disclosed limitations;
- maintain the report-owned provenance and reliance manifest;
- maintain authorized contextual references;
- create a new successor draft with optional predecessor lineage;
- accept the exact current draft through `accept_exact_draft`.

These behaviors do not authorize generic update, physical deletion,
publication, enterprise Review, or mutation of referenced capabilities.

## 11. Human Acceptance Authority

### 11.1 Protected Operation

`accept_exact_draft` is the explicit Human authority operation. It may be
performed only by an authenticated Human who is authorized at operation time
for the Organization, Workspace, optional Project context, Technical Report,
all protected acceptance-basis disclosures, and the acceptance operation.

Authorization must precede disclosure and must be re-evaluated when acceptance
is attempted. Prior access, authorship, AI interaction, or draft editing does
not itself grant acceptance authority.

### 11.2 Single-Human-First Model

The same Human may originate material, create the report, edit it, request an
AI-assisted revision, review the result, and accept it. Self-review is valid in
Version 1.

This design introduces no reviewer assignment, author-reviewer separation,
approval chain, voting, quorum, staged review, or enterprise Review Aggregate.

### 11.3 Explicit Confirmation

Acceptance requires an explicit Human confirmation attributable to the
authenticated Human and tied to the exact draft revision and expected
pre-acceptance Aggregate concurrency version. Absence, ambiguity, stale
confirmation, or AI-originated confirmation is invalid.

AI cannot hold identity as the accepting actor, invoke acceptance under its own
authority, or transform a recommendation into Human confirmation.

## 12. Immutable Accepted Snapshot

Successful acceptance creates one immutable accepted snapshot containing at
minimum:

- Technical Report identity;
- resulting post-acceptance Aggregate concurrency version;
- accepted draft revision identity;
- report purpose;
- engineering scope;
- accepted technical content;
- preliminary qualification;
- assumptions;
- uncertainty;
- limitations;
- conclusions;
- recommendations;
- complete accepted source/provenance manifest;
- accepted Evidence reliance records;
- accepted standards reliance records;
- Organization scope;
- Workspace scope;
- optional direct Project context;
- relevant EngineeringObject references;
- relevant Engineering Relationship references;
- report-owned contextual reference;
- predecessor reference when present;
- accepting Human identity;
- acceptance timestamp;
- explicit Human acceptance attribution.

The snapshot preserves the exact technical meaning and attributable basis that
the Human accepted. Later source changes, access changes, requested changes,
successors, or provider changes cannot rewrite it.

Acceptance must establish the accepted snapshot, lifecycle transition, Human
acceptance record, accountability record, and domain-significant acceptance
outcome as one governed success. Partial acceptance is prohibited.

## 13. Successor and Lineage Model

An accepted Technical Report is terminal for technical content and cannot
return to draft. Any semantic or technical change requires:

- a new Technical Report Aggregate;
- a new Technical Report identity;
- lifecycle `draft`;
- a new draft revision history;
- optional reference to the predecessor Technical Report.

The successor does not inherit acceptance. It must independently satisfy every
acceptance requirement.

Predecessor lineage provides traceability only. It does not automatically mean
supersession, withdrawal, invalidation, replacement, obsolescence, or selection
as the current authoritative report. SATCO Version 1 defines no supersession
workflow.

The successor Technical Report Aggregate exclusively owns its direct
predecessor reference. Successor creation never mutates the accepted
predecessor. The predecessor has no canonical successor field populated by
successor creation, no reciprocal canonical lineage write occurs, and lineage
creation requires neither cross-Aggregate mutation nor a cross-Aggregate
transaction. The predecessor's accepted state and content remain unchanged.

Reverse navigation from a predecessor to its successors may exist only as an
authorization-filtered, non-authoritative, reconstructible query or projection
over successor-owned predecessor references. It owns no independent engineering
fact, mutates neither Aggregate, and cannot establish supersession, withdrawal,
invalidation, replacement, or a current-authoritative report.

Lineage authorization is not content-copy authorization. Creating a successor
with a predecessor reference does not authorize copying predecessor content.
Every protected predecessor-derived input requested for reproduction in the
successor requires fresh current authorization through its governing report or
source authority before disclosure or reproduction. This includes technical
content fragments, source references, provenance records, reliance records,
contextual references, Evidence references, standards references, protected
Human attribution, and protected source-native content.

Prior access, previous authorization, cached plaintext, and the predecessor's
accepted status are insufficient. Authorized copied material becomes new draft
input; its provenance and reliance must be evaluated again for the successor,
and predecessor acceptance is never inherited.

If any protected input requested as part of one atomic successor-copy operation
is inaccessible, none of the requested protected inputs is copied or disclosed
and the operation fails atomically without revealing which input exists or is
inaccessible. A Human may instead create a lineage-only successor without
copying protected predecessor content when the Human is authorized to disclose
and reference the predecessor identity.

Lineage and copied inputs must preserve Organization and Workspace boundaries
and the optional direct Project-context rules. A lineage conflict cannot be
resolved by silently rewriting either Aggregate.

## 14. Preliminary Engineering Assessment Qualification

Preliminary Engineering Assessment is an evidentiary and reliance
qualification. It is not a lifecycle state, report purpose, Review state,
separate Aggregate, or lesser form of Human acceptance.

A preliminary Technical Report may be accepted when the Human explicitly
accepts the exact draft with its limitations visible. The accepted snapshot
must preserve:

- evidence deficiencies;
- assumptions;
- uncertainty;
- unresolved issues;
- reliance limitations;
- applicable follow-up requirements.

Preliminary acceptance is invalid when required limitations are missing,
material uncertainty is concealed, or the preserved basis would falsely imply
completeness. Acceptance does not convert preliminary material into final,
certified, or regulator-approved work.

## 15. Authorized Source Intake

Technical Report may consume authorized references from:

- Universal Capture;
- Engineering Journal navigation to canonical resources;
- EngineeringObject;
- Engineering Relationships;
- Evidence Foundation;
- standards and external source material;
- Human-provided context.

Every source is resolved through its owning authority before disclosure or use.
Engineering Journal presentation never becomes a canonical source identity;
Universal Capture retains ownership of captured Engineering Experience.

For acceptance purposes every source reference is classified as exactly one of:

1. canonical material source;
2. external or Human-provided material;
3. standards material;
4. contextual or non-material reference.

Material reliance means that source content materially contributes to or
constrains accepted reasoning, assumptions, uncertainty, limitations,
conclusions, or recommendations. Classification is determined from the
report's actual reliance, not its source label. A contextual source that becomes
material must satisfy the applicable material-source contract before
acceptance.

Source intake grants no authority to mutate, validate, approve, or reclassify
the originating resource.

## 16. Provenance and Reliance Manifest

The Aggregate owns a provenance and reliance manifest describing how the
Technical Report used its sources. The manifest belongs to Technical Report;
the referenced source does not. It records each source's class and whether the
source is materially relied upon.

### 16.1 Canonical Material Sources

For every materially relied-upon canonical source, acceptance requires:

- stable canonical source identity;
- canonical owning capability;
- an immutable source version, immutable snapshot identity, or
  integrity-protected historical representation sufficient to resolve the
  exact relied-upon state;
- provenance or origin;
- reliance role;
- authorization at use and acceptance time as required by the owning
  authority;
- verification status when the governing source defines verification;
- availability status at acceptance;
- known limitations.

Technical Report owns only its reference, report-specific reliance meaning,
report-specific provenance attribution, and acceptance-time
historical-resolution information. Canonical source ownership remains external.

### 16.2 External or Human-Provided Material

Material external or Human-provided content must use an authorized canonical
immutable historical representation when one exists. If none exists, Technical
Report may own a minimal integrity-protected provenance representation solely
to establish what material the accepted report relied upon.

That representation requires:

- stable report-local identity;
- origin and provenance attribution;
- integrity protection through an immutable digest or immutable snapshot
  identity;
- reliance role;
- observation, retrieval, or submission time when relevant to the relied-upon
  meaning;
- verification status;
- availability status;
- known limitations;
- the minimum content or representation necessary to reconstruct the relied-upon
  basis.

When identity and integrity metadata cannot reconstruct the relied-upon
meaning, the minimum necessary immutable representation of the material is
preserved inside the report's provenance boundary. Preservation exists only
for reproducibility of the accepted report.

The representation is not canonical Evidence, a Universal Capture substitute,
a generic document store, a source repository, an unrestricted plaintext
archive, or independent engineering authority. It does not automatically
create Evidence, Capture, EngineeringObject, or Engineering Relationship
records.

### 16.3 Standards Material

For every materially relied-upon standard, acceptance requires the following
information to the extent the source actually provides it:

- standard identity;
- issuing authority;
- edition or version;
- clause or location;
- source and provenance;
- verification status;
- availability status;
- reliance role;
- stable historical or integrity reference;
- uncertainty and limitations;
- explicit separation of standard-native material, Human interpretation, and
  AI-assisted interpretation.

An unavailable or unverified edition, clause, or source characteristic must be
recorded explicitly and cannot be inferred. If its absence prevents historical
reconstruction of material reliance, acceptance fails as an unresolved
historical reference.

### 16.4 Contextual or Non-Material References

A contextual or non-material reference does not require the material-source
historical reconstruction contract. It must still preserve:

- source or reference identity;
- owning capability, external origin, or governing context;
- authorization appropriate to its disclosure and use;
- an explicit contextual or non-material role.

If its content contributes to or constrains reasoning, assumptions,
uncertainty, limitations, conclusions, or recommendations, it is material and
must satisfy the applicable canonical, external/Human, or standards contract
before acceptance.

The manifest must distinguish material reliance from contextual mention.
Material reliance affects the acceptance basis and cannot be removed or altered
after acceptance. Contextual mention cannot be presented as verified reliance.

Historical reconstruction must be possible without treating a live mutable
source as if it were the exact source state reviewed at acceptance.

## 17. Evidence Boundary

Evidence Foundation retains canonical ownership of Evidence identity,
lifecycle, scope, visibility, provenance, and integrity. Technical Report does
not create a second Evidence repository or redefine Evidence status.

For materially relied-upon Evidence, Technical Report preserves within its
reliance manifest:

- Evidence identity;
- historical version, snapshot, or integrity reference;
- reliance role;
- verification status at the relevant time;
- availability status at the relevant time;
- limitations;
- provenance.

Material Evidence must exist, be authorized, be in an acceptable canonical
standing, be scope-compatible, and remain historically resolvable before
acceptance. Later loss of ordinary access does not authorize disclosure, but it
must not erase the accepted report's historically attributable basis.

Acceptance does not certify Evidence, elevate its lifecycle, or make the
Technical Report its canonical owner.

## 18. Standards Boundary

Technical Report may record standards reliance under the deterministic
standards-material contract in Section 16.3 without creating or implying a
standards repository.

The report must distinguish:

1. standard or source material;
2. Human interpretation and engineering judgment;
3. AI-assisted interpretation.

AI interpretation cannot be presented as source-native text or Human judgment.
Human acceptance establishes accountability for the report's exact technical
content; it does not establish regulatory compliance, certification, or formal
approval by an issuing authority.

## 19. Engineering Context References

Relevant EngineeringObject and Engineering Relationship references provide
authorized context. Their identity, scope, classification, lifecycle,
authority, evidence, direction, and invariants remain owned by their canonical
capabilities.

Technical Report may describe why a referenced object or relationship matters
to the report and preserve the historical reference relied upon. It cannot
create, validate, reclassify, transition, retire, or otherwise mutate those
resources.

Relationship presence does not prove technical truth. EngineeringObject
authority standing does not substitute for the report's acceptance basis.

## 20. Contextual Documentation Boundary

Acceptance may establish only:

- a Technical-Report-owned contextual reference; and/or
- information eligible for an independently authorized derived projection.

Acceptance must not automatically:

- mutate an EngineeringObject;
- create or validate an Engineering Relationship;
- create Evidence;
- modify Universal Capture;
- mutate canonical Engineering Journal state;
- change Project or Workspace state;
- publish to Organizational Memory;
- create Knowledge Graph authority;
- execute another capability's lifecycle transition.

Any canonical change in another capability requires that capability's own
authorized command, policy, transaction, and audit boundary. Contextual
documentation cannot be used as a backdoor command.

## 21. Authorization and Disclosure

Authorization is deny-by-default, Organization-scoped, operation-specific, and
evaluated before disclosure. It applies independently to:

- Technical Report scope and existence;
- draft and accepted content;
- purpose and qualification;
- provenance and reliance records;
- Evidence and standards references;
- EngineeringObject and Engineering Relationship references;
- predecessor lineage;
- Human identity and acceptance attribution;
- creation, revision, acceptance, and successor creation.

Access to a Technical Report does not automatically grant access to every live
referenced resource. Access to a source does not automatically grant access to
the Technical Report. Disclosures must respect both the report policy and the
owning capability's policy where live canonical information is resolved.

Protected resources use protected-not-found semantics where required by the
governing authorization contracts. Neither existence, hidden counts, lineage,
source identity, reliance status, nor denial reason may leak through an
unauthorized outcome.

AI receives only the information already authorized for the authenticated
Human and the requested operation. AI has no independent identity, membership,
scope, discovery right, or authorization grant.

## 22. Abandoned Draft Semantics

An abandoned, unaccepted draft has no engineering authority. It is not
accepted, rejected, withdrawn, published, superseded, or converted into a
successor solely because work stopped.

Permanent preservation of every abandoned revision is not required. Transient
AI proposals and superseded unaccepted draft text may be discarded according
to applicable retention governance. Disposition must not make an abandoned
draft appear accepted or affect another Aggregate.

When Audit governance independently requires accountability, only the required
audit facts are retained, such as actor, action, scope, time, outcome, and
non-sensitive identifiers. Audit must not become an alternative plaintext
Technical Report repository or preserve discarded draft content unless an
authoritative governance rule explicitly requires it.

An abandoned-draft disposition becomes a domain-significant outcome only when
Audit or retention governance requires that fact to be recorded.

## 23. Post-Acceptance Mutation Boundary

The Version 1 post-acceptance correction allow-list is empty. After Human
acceptance, no field owned by the Technical Report Aggregate may be corrected
or mutated. Technical Report Version 1 defines no administrative metadata
correction operation.

The prohibition includes technical content and every report-owned
presentation, indexing, clerical, locator, reference, contextual, provenance,
lineage, identity, acceptance, and other metadata field. The immutable accepted
snapshot remains the sole engineering authority, and the accepted Aggregate is
terminal and mutation-free.

Any requested post-acceptance change requires a new successor Technical Report
Aggregate. Uncertainty about whether a requested change affects meaning also
requires a successor. No later design may create a Technical-Report-owned
post-acceptance mutation without separately accepted architecture that changes
the Version 1 boundary.

## 24. AI Authority Boundary

AI may:

- analyze authorized inputs;
- structure draft content;
- propose technical reasoning;
- compare authorized Evidence;
- identify gaps, conflicts, assumptions, and uncertainty;
- assist standards analysis;
- propose conclusions and recommendations;
- revise the working draft under explicit Human direction.

AI may not:

- accept, approve, certify, or publish;
- become the accountable actor;
- expand authorization or discover unauthorized material;
- issue valid Human confirmation;
- alter accepted content or acceptance history;
- impersonate Human judgment;
- mutate another capability;
- promote provider state or output to domain authority.

AI-originated material remains attributable and distinguishable from source
material and Human interpretation. The Human decides whether proposed material
enters the working draft. Provider replacement must not alter Technical Report
identity, revision, acceptance, provenance, or historical meaning.

## 25. Accountability, Audit, and Domain-Significant Outcomes

Technical Report requires accountable records for governed actions without
using Audit as report-content persistence. Audit and domain-significant
outcomes have distinct purposes: Audit records who attempted or completed an
action and its governed result; outcomes communicate accepted domain facts.

Minimum domain-significant outcomes are:

- Technical Report draft created;
- draft revision changed;
- Technical Report accepted by an identified Human for an exact revision;
- successor Technical Report created with predecessor lineage;
- abandoned-draft disposition recorded only when independently required by
  Audit or retention governance.

These outcomes do not require event sourcing. They do not replace Aggregate
state, acceptance history, or Audit accountability. Payloads must exclude
unnecessary protected plaintext and cannot grant authorization.

## 26. Failure and Conflict Semantics

The design defines stable domain-level failure categories without assigning
transport status codes:

| Failure | Meaning and required outcome |
|---|---|
| Invalid lifecycle operation | The requested behavior is not permitted from the current `draft` or `accepted` state; state remains unchanged. |
| Stale draft revision | The operation targets a draft revision other than the exact current revision; no mutation or acceptance occurs. |
| Aggregate concurrency conflict | The expected pre-mutation Aggregate concurrency version is stale; compare-and-change fails atomically. |
| Unauthorized operation | The Human lacks current operation-specific authority; no protected state is disclosed or changed. |
| Protected resource | The resource or required scope cannot be disclosed; protected-not-found semantics apply without existence leakage. |
| Inaccessible source | A required source cannot be resolved within the Human's authorized scope; it is not disclosed or used. |
| Incompatible context | Organization, Workspace, optional Project, or referenced engineering context is inconsistent; state remains unchanged. |
| Invalid preliminary acceptance | Preliminary qualification does not expose the deficiencies, uncertainty, limitations, or unresolved basis required for accountable acceptance. |
| Unresolved historical reference | A materially relied-upon source cannot be reconstructed or integrity-bound for acceptance. |
| Incomplete acceptance basis | Required purpose, scope, content, reliance, qualification, or attributable Human decision information is absent. |
| Invalid Human confirmation | Confirmation is absent, ambiguous, stale, AI-originated, or not attributable to the authenticated authorized Human. |
| Attempted accepted-content mutation | A command would alter acceptance-defining content of an accepted Aggregate; a successor is required. |
| Attempted post-acceptance mutation | Any Technical-Report-owned field mutation is requested after acceptance; the accepted Aggregate remains unchanged and a successor is required. |
| AI authority violation | AI attempts or is represented as performing an authority-bearing operation. |
| Lineage conflict | A predecessor reference is inaccessible, incompatible, self-referential, contradictory, or represented as automatic supersession. |

Failures are deterministic within the same authorized state and input. No
failure may produce a partial lifecycle transition, partial accepted snapshot,
or partial Human acceptance record.

## 27. Security and Confidentiality Principles

Technical Report visibility derives from trusted Organization and Workspace
scope, optional direct Project context, operation policy, report state, and the
field being disclosed. The existence of a report does not grant visibility to
its content or reliance basis.

Acceptance must reauthorize the Human and every material protected dependency
required for the acceptance decision. Revoked or stale access cannot be
recovered from cached presentation, AI conversation, Journal navigation, or a
prior successful read.

Protected technical plaintext must not be copied into errors, diagnostics,
Audit records, domain-event payloads, identifiers, or unauthorized projections.
Historical resolvability is not unrestricted visibility; reconstruction remains
governed by applicable authority.

## 28. Transactional Consistency Requirements

A successful governed Aggregate operation is indivisible at the design level.
Acceptance must not expose `accepted` lifecycle without its exact immutable
snapshot and attributable Human acceptance record. A draft revision must not
advance without its corresponding accepted draft change.

Successor creation writes the direct predecessor reference only within the new
successor Aggregate. It performs no reciprocal write to the predecessor,
requires no cross-Aggregate mutation or transaction, and cannot delegate
lineage ownership to a later IDS. Reverse navigation is derived exclusively
from successor-owned predecessor references.

Concurrency conflict, authorization failure, invalid reliance, or any other
failed invariant leaves authoritative state unchanged. This design does not
select a transaction technology or persistence mechanism; those decisions
belong to later accepted design stages.

## 29. Dependency Direction and Modularity

Technical Report depends on canonical application contracts supplied by the
capabilities it references. It does not depend on their persistence models,
transport representations, or implementation internals.

Canonical capabilities do not depend on Technical Report merely because a
report references them. Any future projection from accepted reports into
another capability requires a separately authorized outward integration owned
by the receiving capability or an approved neutral boundary.

AI providers, presentation layers, persistence technologies, and transport
frameworks remain replaceable outer concerns. None may define domain identity,
purpose, lifecycle, draft revision, acceptance, lineage, or Human authority.

## 30. Explicit Non-Scope

This EDS does not authorize or define:

- a separate Engineering Review Aggregate or capability;
- enterprise approval workflow;
- reviewer assignment or mandatory role separation;
- multi-reviewer governance, approval chains, voting, or quorum;
- submitted, in-review, revision-requested, rejected, withdrawn, approved,
  published, superseded, or archived report lifecycle states;
- supersession or current-authoritative-selection workflow;
- Organizational Memory publication or admission;
- Knowledge Graph authority;
- autonomous or authority-bearing AI;
- automatic mutation of EngineeringObject, Engineering Relationships,
  Evidence, Universal Capture, Engineering Journal, Project, or Workspace;
- generic document management;
- a standards repository;
- a second Evidence repository;
- regulatory certification;
- purpose-specific UI or templates;
- generic update, physical deletion, or any post-acceptance Aggregate mutation;
- ORM classes, SQL tables, migrations, repository implementation, API
  endpoints, HTTP schemas, frontend components, UI flows, prompts,
  provider-specific AI implementation, deployment, or implementation sequence.

## 31. Manifesto Alignment

| Manifesto principle | EDS-032 design consequence |
|---|---|
| Engineering First | Technical Report preserves engineering scope, reasoning, uncertainty, conclusions, and reliance rather than treating a report as generic content. |
| Capture Once | Universal Capture remains canonical; Technical Report references and enriches authorized source material without duplicating its ownership. |
| Human Authority | Only an authenticated and authorized Human can accept the exact current draft. |
| Engineering Context Is Sacred | Organization, Workspace, optional Project, engineering references, provenance, limitations, and historical basis remain explicit. |
| Evidence Before Assumption | Evidence and assumptions are distinguished, attributable, and preserved in the accepted basis. |
| Context Before Recommendation | Recommendations remain bound to engineering scope, relied-upon sources, assumptions, uncertainty, and limitations. |
| Intelligence Before Automation | AI assists draft preparation but cannot accept, publish, mutate canonical resources, or become authoritative. |
| Explainability | The accepted snapshot preserves the exact revision, Human attribution, provenance, reliance, and limitations. |
| Provider Independence | Provider state is never domain authority and providers may change without altering report meaning or acceptance. |
| Organizational Ownership | Technical Reports are governed within trusted Organization and Workspace scope. |
| Continuous Evolution | Semantic change creates a traceable successor without rewriting accepted history or implying supersession. |

## 32. Design Acceptance Criteria

EDS-032 is complete for independent review only when reviewers confirm that:

1. `TechnicalReport` is one dedicated Aggregate Root;
2. lifecycle is exactly `draft → accepted`;
3. draft revision and Aggregate concurrency version are distinct;
4. `accept_exact_draft` binds explicit Human confirmation to both the expected
   pre-acceptance Aggregate concurrency version and exact current draft
   revision, and successful acceptance records the resulting post-acceptance
   Aggregate concurrency version;
5. self-review remains valid and no enterprise Review workflow exists;
6. accepted technical content and acceptance are immutable;
7. semantic change creates a new Aggregate with optional predecessor lineage;
8. lineage does not imply supersession, withdrawal, invalidation, replacement,
   or current-authoritative selection;
9. Preliminary Engineering Assessment remains a qualification only;
10. the four deterministic source classes and their material-reliance rules
    make every materially relied-upon source historically resolvable;
11. Evidence and standards ownership remain external and canonical;
12. contextual documentation cannot mutate another capability;
13. abandoned drafts have no authority and Audit is not alternate report
    plaintext storage;
14. successor-owned predecessor references are the exclusive canonical lineage
    record, reverse navigation is derived, and content copying requires fresh
    authorization independently of lineage authorization;
15. the Version 1 post-acceptance mutation allow-list is empty and every later
    change requires a successor Aggregate;
16. AI remains advisory, attributable, provider-independent, and
    non-authoritative;
17. authorization occurs before disclosure and at operation time;
18. domain failures are stable and transport-neutral;
19. no implementation-level design or unauthorized capability is introduced;
20. ADR-023, PATCH-032, Architecture Review, Human Architecture Acceptance,
    and QG-M1 traceability is explicit.

## 33. EDS Decision

```text
EDS-032 design: COMPLETE
EDS-032 status: ACCEPTED / COMPLETE
ADR-023 alignment: PASS
PATCH-032 alignment: PASS
Technical Report Architecture Review traceability: PASS
Human Architecture Acceptance traceability: PASS
QG-M1 Manifesto Compliance: PASS
Enterprise Review workflow introduced: NO
Engineering Review authority: accept_exact_draft only
Initial Independent EDS Review: FAIL / HISTORICAL
Focused Independent EDS-032 Re-review: PASS
Human EDS acceptance: PASS
Remaining findings: NONE
Governance reconciliation: PASS
Permission for IDS-032 design: GRANTED
IDS authority: GRANTED
Implementation authority: NOT GRANTED
```

## 34. Revision History

| Version | Date | Description |
|---|---|---|
| 1.0 | 2026-08-09 | Recorded Focused Independent EDS-032 Re-review PASS, Human EDS Acceptance PASS, EDS-032 ACCEPTED / COMPLETE, governance reconciliation PASS, and IDS-032 design authority GRANTED; implementation authority remains not granted. |
| 0.2 | 2026-08-09 | Resolved independent-review findings by closing post-acceptance mutation, defining deterministic historical-resolvability source classes, requiring fresh authorization for successor-copied inputs, and assigning direct predecessor-reference ownership exclusively to the successor. |
| 0.1 | 2026-08-08 | Complete proposed Engineering Design Specification for PATCH-032, ready for independent EDS review. |
