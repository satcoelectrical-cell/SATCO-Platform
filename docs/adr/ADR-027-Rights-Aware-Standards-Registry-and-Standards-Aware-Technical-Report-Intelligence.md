# ADR-027 — Rights-Aware Standards Registry and Standards-Aware Technical Report Intelligence

## Status

**Proposed / Candidate — independent review PASS / awaiting Human ADR
acceptance.**

This candidate is not Accepted. It establishes no EDS, IDS, implementation,
migration, frontend, deployment, staging, commit, push, or PATCH-055 authority.

## Date

2026-09-12

## Decision owner and authority

- Decision owner: Human Architecture Authority.
- Human PATCH-054 Discovery Acceptance: **PASS / ACCEPTED**.
- ADR-027 preparation authority: **GRANTED**.
- Independent ADR review authority: **GRANTED**.
- Human ADR-027 acceptance: **NOT YET GRANTED**.

## Approval record

| Governance event | State |
|---|---|
| PATCH-054 Discovery | HUMAN ACCEPTED — PASS / ARCHITECTURE-CANDIDATE |
| ADR-027 candidate design | PASS / COMPLETE |
| Independent ADR review | PASS; Critical/Major/Minor/Observation `0/0/0/0` |
| Human ADR-027 acceptance | PENDING / NOT GRANTED |
| EDS-054 / IDS-054 / implementation plan | NOT STARTED / NOT AUTHORIZED |
| Production/tests/frontend/migrations | NOT AUTHORIZED |
| PATCH-055+ | NOT STARTED / NOT AUTHORIZED |

## Context

SATCO's accepted Commercial V1 roadmap assigns PATCH-054 the minimum
standards, edition, applicability, rights, retrieval, immutable citation, and
Human-accepted Technical Report integration needed for rights-aware
standards-backed engineering work. The Human-accepted PATCH-054 Discovery
found no contradiction with accepted architecture and classified the candidate
as `PASS / ARCHITECTURE-CANDIDATE`.

The Discovery identified two expected PATCH-054 capability gaps:

- `DISC-054-MAJ-01`: current standards provenance is client-composed,
  non-canonical, and not governed by rights, exact edition, Project
  applicability, or source-owner validation; and
- `DISC-054-MAJ-02`: current Technical Report AI composition can include
  selected standards locators without a standards rights/egress decision, an
  aggregate protected-context bound, or a retained provider/model interaction
  record.

ADR-023 already establishes the Technical Report as SATCO V1's Human-accepted
engineering authority boundary. It requires historically resolvable relied-upon
standards while preserving the `draft → accepted` lifecycle, immutable accepted
content, successor lineage, acceptance distinct from publication, and AI
non-authority. PATCH-051 through PATCH-053 are closed and remain authoritative.
PATCH-054 must fill the standards boundary without redefining any of them.

## Problem

A standard designation alone is not enough to establish what publication was
used, whether an Organization could lawfully retrieve or process its content,
whether a Project considered it applicable, what clause or bounded source was
observed, or what a Human actually selected for an accepted Technical Report.
Those are different facts with different owners and lifecycles.

Treating a client-supplied locator as canonical permits forged identities,
editions, clauses, and source descriptions. Treating possession as permission
can disclose licensed material across Organizations or send it to an
unapproved AI processor. Re-resolving an accepted Report against a newer
edition or current registry state silently changes its historical meaning.
Conversely, preserving protected content without honoring current rights makes
historical acceptance an improper perpetual access grant.

SATCO therefore needs a rights-aware standards boundary that can preserve safe,
immutable historical provenance while independently enforcing current access
rights for every protected operation.

## Decision

SATCO shall establish a shared **Rights-Aware Standards Registry** and integrate
it with Technical Reports through a canonical, server-composed standards basis.
The governing architecture is:

```text
StandardIdentity
    + immutable StandardEdition
    + versioned OrganizationRightsBinding
    + explicit ProjectStandardApplicability
    + authorized bounded StandardSourceSnapshot
    + optional governed StandardKnowledgeAssertion
    + server-composed TechnicalReportStandardsBasis
    + optional bounded advisory AI
```

The architecture is governed by these core rules:

1. Standard identity and exact edition are distinct immutable identities.
2. Catalog existence, Organization content rights, Project applicability,
   Report reliance, and mandatory applicability are distinct facts.
3. Possession of content never implies permission to store, index, display,
   derive from, retain derived knowledge from, or send that content to AI.
4. Protected operations are authorized against a current, Organization-scoped,
   versioned rights binding and fail closed when permission is absent,
   ambiguous, stale, expired, or revoked.
5. PATCH-054 is not a wholesale standards repository. Material support requires
   an authorized bounded immutable snapshot or provider-backed immutable handle;
   metadata alone is never material support.
6. Technical Report standards provenance is composed and attested by the
   server from canonical handles. Raw client identity, edition, clause, source,
   or protected text is not trusted provenance.
7. Accepted Reports freeze the exact historical standards basis and Human
   selection. Later registry, edition, applicability, or rights changes do not
   reinterpret it.
8. Historical provenance does not grant present or future protected-content
   access. Current retrieval, display, indexing, derived use, and AI use are
   reauthorized against current rights.
9. Derived standard knowledge is bounded, attributable, and non-authoritative.
   Human verification confirms faithful extraction, not autonomous engineering
   truth.
10. AI is optional, Human-requested, bounded, rights-gated, provider-neutral,
    and advisory. It cannot determine compliance, mandatory applicability,
    engineering approval, or Report acceptance.
11. Authorization precedes protected lookup and disclosure, including count,
    existence, idempotency, error, and timing-sensitive behavior.
12. Audit and outbox records contain minimized identifiers, versions, digests,
    state codes, actors, correlations, and timestamps, never protected content
    or secrets.

## Canonical ownership model

Canonical ownership is divided deliberately; no Project configuration, package,
client, AI provider, Evidence record, Supporting File, or Technical Report may
collapse these boundaries.

| Concept | Canonical owner | Authority boundary |
|---|---|---|
| `StandardIdentity` | Standards Registry | Stable catalog identity, global-trusted or Organization-private scope, and immutable identity lineage |
| `StandardEdition` | Standards Registry | Exact publication/edition/revision identity and immutable relationship to its Standard identity |
| edition standing observation/correction | Standards Registry | Versioned observation of current, superseded, withdrawn, or unknown standing without mutating an edition |
| `OrganizationRightsBinding` | Organization Standards Rights boundary | Organization-scoped rights basis, status, capability permissions, effective version, and processor restrictions |
| `ProjectStandardApplicability` | Project Standards Applicability boundary | Append-only Human declarations and advisory candidates pinning an exact edition for one Project |
| `StandardSourceSnapshot` | Standards Retrieval and Provenance boundary | Immutable bounded source/handle provenance, retrieval facts, content digest when available, and rights-at-use attestation |
| `StandardKnowledgeAssertion` | Standards Knowledge boundary | Bounded derived assertion, exact source provenance, origin, method, digest, verification, and current-use eligibility |
| standards intelligence interaction | Standards Intelligence boundary | One bounded advisory run, authorized input-handle digest, processor decision, provider/model metadata, and output digest |
| draft Report standards basis | Technical Report aggregate, using Standards Registry attestation | Human-selected, server-composed reference incorporated into an exact draft Report version |
| accepted Report standards basis | immutable accepted Technical Report snapshot | Historical copy of the exact standards basis relied upon at Human acceptance |
| Audit/outbox/idempotency | shared reliability infrastructure under the initiating owner | Transactional accountability and delivery metadata, never canonical standards content |

The Standards Registry is a shared Core capability. Global-trusted metadata is
platform-governed. Organization-private catalog records, rights bindings,
snapshots, assertions, and protected interactions remain isolated by immutable
server-derived Organization scope. The Technical Report does not become the
canonical owner of standards content; it owns only its immutable accepted
historical basis.

## Standard identity and edition

`StandardIdentity` represents the stable identity of a standard family or
designation. `StandardEdition` represents one exact publication unit, including
an edition, revision, amendment-composed publication, or other issuer-defined
unit that must be cited and reproduced independently.

The identities are immutable. A new edition creates a new `StandardEdition` and
never edits, replaces, aliases, or recycles the identity of an older edition.
Historical consumers pin the exact edition identity. Corrections to catalog
observations and changes in standing are versioned observations; they do not
rewrite the edition that a historical consumer used.

Organization rights and Project applicability are not attributes of canonical
Standard identity or edition. They are separate, time-sensitive bindings.

## Catalog scope

The catalog has two explicit ownership scopes:

- **Global trusted metadata** contains platform-reviewed public/catalog
  metadata appropriate for reuse across Organizations. Global existence is
  discoverability only and grants no protected-content rights.
- **Organization-private identity** contains internal, customer-specific, or
  private standards metadata. Its identity and even its existence are protected
  by Organization isolation and must not leak across Organizations.

Project scope is never the canonical owner of a Standard identity or edition.
A Project may bind applicability only to an edition that the authorized
Standards Registry resolves in the caller's permitted catalog scope.

## Rights architecture

### Rights basis and status

Rights basis describes why a capability might be permitted. Rights status
describes whether the binding is currently usable. They are separate values.

The closed architecture-level rights basis vocabulary is:

- `metadata_only`;
- `customer_supplied_declared`;
- `organization_license`;
- `open_distribution`;
- `internally_authored`; and
- `unknown`.

The closed architecture-level rights status vocabulary is:

- `active`;
- `expired`;
- `revoked`; and
- `unknown`.

These values classify asserted rights; they do not invent or adjudicate legal
permission. The binding must retain attributable authority, effective version,
and the policy/configuration basis needed for a later implementation to prove
which decision was applied.

### Permission capabilities

Each rights binding independently governs at least:

- protected-content storage;
- indexing/search processing;
- display or excerpt presentation;
- derived-fact creation and retention/current use; and
- AI processing.

AI processing has at least these architecture-level modes:

- `prohibited`;
- `local_only`; and
- `approved_processor`.

An `approved_processor` decision is specific to the configured processor policy;
it is not permission for every external provider. One allowed capability does
not imply another. Metadata visibility does not imply protected-content
visibility. Customer upload, object-storage presence, prior retrieval, prior
Report acceptance, or prior AI processing does not imply continuing permission.

The default for missing, ambiguous, unsupported, stale, or conflicting rights
is denial.

### Policy versus architecture

This ADR does not select standards issuers, negotiate commercial licenses,
approve legal terms, or approve an AI provider. Those are configurable Human
policy and commercial decisions expressed through the fail-closed capability
model. The architecture remains valid for public, licensed, customer-supplied,
internally authored, metadata-only, and unknown sources without assuming that
any particular use is lawful.

## Project applicability

SATCO shall keep these facts distinct:

```text
standard exists
    ≠ Organization may access protected content
    ≠ Project uses the standard
    ≠ Technical Report relies on the standard
    ≠ standard is legally or contractually mandatory
```

`ProjectStandardApplicability` is an append-only, versioned Project-scoped
record that pins an exact `StandardEdition`. It may represent an advisory
candidate, a Human declaration that the edition is applicable, a Human
declaration that it is not applicable, or retirement of a prior declaration.
The later EDS shall define the smallest closed state vocabulary and exact
transition contract consistent with those meanings.

Only an explicit, attributable Human declaration with a recorded rationale and
source may establish mandatory applicability. A package, AI interaction,
registry default, Organization license, or presence in a Report can suggest or
reference applicability but cannot declare it mandatory. A license grants no
Project applicability, and Project applicability grants no content right.

## Content boundary

PATCH-054 recognizes five different representations:

1. **Standard metadata**: identity, issuer, designation, edition, standing, and
   other catalog facts that can be exposed only within their catalog policy.
2. **Protected Standard content**: licensed, customer-supplied, private, or
   otherwise restricted source material.
3. **Bounded immutable source snapshot or provider-backed immutable handle**:
   the exact, rights-authorized material observed for a governed use.
4. **Derived Standard knowledge/assertion**: a bounded attributable extraction
   or typed fact derived from an authorized source.
5. **Technical Report provenance reference**: the server-composed historical
   standards basis incorporated into one Report version.

Whole-standard storage, browsing, mirroring, scraping, or binary ingestion is
outside PATCH-054. A later lawful source adapter may use private object-storage
infrastructure for bounded protected snapshots, but infrastructure possession
does not change the standards domain owner or rights decision.

## Standard source snapshot

`StandardSourceSnapshot` is an immutable provenance record for one authorized,
bounded observation. It identifies enough of the following architecture-level
facts to make the observation attributable:

- exact Standard identity and edition;
- exact clause, section, page, provider locator, or other source location;
- source/provider identity and immutable provider-handle identity where used;
- retrieval time and correlation;
- content digest and bounded extent when content was lawfully available;
- rights binding version/digest and permission decision at use; and
- snapshot/handle availability and integrity state.

A provider-backed handle is acceptable only when the adapter can establish
stable identity and immutable resolution semantics suitable for the intended
historical use. Otherwise SATCO must retain a lawful bounded immutable snapshot
or must not represent the material as reproducible content-backed support.

The snapshot preserves rights-at-use history. Current retrieval, display,
indexing, derived use, and AI processing re-evaluate current rights. Later
rights or registry changes append new state and never rewrite the snapshot.

## Derived standard knowledge

SATCO may persist a minimal governed `StandardKnowledgeAssertion`. It is a
bounded derived record, not a replacement standard and not an autonomous
engineering rule. It preserves:

- the exact source snapshot/handle and edition provenance;
- origin, distinguishing Human, deterministic, and AI-assisted derivation;
- extraction method and relevant template/model provenance when applicable;
- assertion digest and bounded representation;
- verification state;
- attributable Human verifier and rationale when Human-verified; and
- rights-at-derivation plus current retained-derived-use eligibility.

Human verification means that an accountable Human confirmed faithful
extraction from the cited source. It does not establish compliance, legal
applicability, mandatory applicability, engineering approval, or universal
truth. AI-generated or otherwise unverified assertions remain non-authoritative.
If current rights do not permit retained derived use, the assertion becomes
unavailable for current reasoning while safe historical metadata remains.

This ADR does not freeze a broad assertion taxonomy. The EDS must choose the
smallest closed assertion-kind vocabulary required by Commercial V1.

## Technical Report integration

ADR-023 remains authoritative and unchanged. PATCH-054 introduces a canonical
server-composed `TechnicalReportStandardsBasis` for new Report provenance; the
name is architectural and does not prescribe a DTO or table name.

A client may submit only opaque candidate/selection handles and Human intent.
The server must authorize and resolve each handle, establish exact identity,
edition, source snapshot, rights-at-use, Project applicability, and assertion
provenance, and compose the canonical basis. Client-submitted raw identity,
edition, clause, source, issuer, minimal representation, or protected text is
untrusted input and cannot become canonical provenance by echoing it into a
Report.

The server reauthorizes the standards basis when it is attached to or revised
in a draft, before protected standards context is composed for AI, and at Human
acceptance. Acceptance binds the exact Report version and freezes the selected
standards basis in the immutable accepted snapshot. It does not publish the
Report or grant future source access.

The standards capability is upstream/supporting context only. It cannot accept,
approve, publish, or change a Report; those authorities remain exclusively in
the Technical Report aggregate and accountable Human acceptance operation.

## Legacy `StandardLocator`

Existing accepted Technical Report snapshots containing legacy
`StandardLocator` values are immutable historical contracts. They remain
readable and are never rewritten, backfilled, silently upgraded, or represented
as newly rights-attested material.

For new writes after PATCH-054 becomes operational, **manual legacy
`StandardLocator` submission is prohibited**. This is alternative A from the
accepted Discovery question and is safer for Commercial V1 because a bounded
compatibility period would continue the forged-provenance and ambiguous
materiality path that PATCH-054 exists to close.

If a user needs a metadata-only citation, it must be created through the new
server-composed, explicitly non-material reference path. If material support is
claimed, it must use an authorized source snapshot/immutable provider handle.
Legacy records retain their original historical meaning and are not upgraded by
inference.

## Metadata-only references and material support

Metadata-only standards may appear in a Technical Report as explicitly
**non-material bibliographic/reference provenance**. This supports useful
citation without pretending that SATCO retrieved or verified protected content.

Metadata-only provenance must be visibly and semantically distinguishable from
material support. It cannot support a standards-backed engineering claim,
cannot be sent as protected clause context to AI, and cannot satisfy a source
requirement that needs content-backed evidence.

A standards-backed material Report claim requires a current authorized bounded
source snapshot or provider-backed immutable handle with exact edition/location,
integrity, rights-at-use, and source provenance. If those conditions cannot be
established, the source is incomplete and the material claim must fail closed.

## Historical reproducibility

An accepted Technical Report standards basis retains sufficient immutable,
safe information to reconstruct what the Human selected and what SATCO
authorized at acceptance, including as applicable:

- exact Standard identity and exact edition;
- observed edition standing;
- snapshot or immutable provider-handle identity;
- exact source location and source/content digest where available;
- rights-at-use binding version/digest and capability decision;
- Project applicability record/version;
- derived assertion identity, digest, origin, and verification state;
- standards-aware AI interaction metadata;
- Human selection and acceptance attribution; and
- the immutable accepted Report snapshot and successor lineage.

A new edition, supersession, withdrawal, rights expiry/revocation, registry
correction, or Project applicability change does not reinterpret or mutate an
accepted Report. Current analysis against changed sources creates new governed
state and, where Report meaning changes, a successor Technical Report under
ADR-023.

Historical reproducibility means exact attributable identity, integrity, and
decision reconstruction. It does not override current law or rights to reveal
protected bytes. If current rights prohibit display, the safe historical
metadata and digests remain while protected content is unavailable.

## Current rights versus historical basis

The architecture has two independent time views:

- **Historical basis** is the immutable evidence of the exact source identity,
  rights decision, applicability, derived assertion, AI participation, and
  Human selection used at the time of Report acceptance.
- **Current access** is the authorization decision made now whenever protected
  content is retrieved, counted, displayed, indexed, used to derive current
  knowledge, or sent to AI.

Historical acceptance never grants current access. Revocation or expiry may
make historical protected content unavailable today without erasing the safe
fact that it was lawfully/authorizedly used and accepted earlier. A current
rights change cannot falsify, reclassify, or rewrite the historical decision.

## AI egress

Standards-aware AI is optional and follows a deterministic-first,
Human-requested flow. The server, not the client or provider, selects the exact
authorized bounded context from canonical handles after current rights and
processor-policy evaluation.

The following are prohibited:

- raw client-selected protected text bypassing the rights gateway;
- arbitrary Standard, edition, clause, or source invention as trusted input;
- autonomous standards retrieval or protected-content scraping;
- provider calls when rights prohibit AI, require local-only processing, or do
  not approve the selected processor;
- provider tools or retrieved content causing source retrieval, mutation, or
  authority operations; and
- AI declarations of compliance, legal or mandatory applicability,
  engineering approval, Technical Report acceptance, or publication.

Retrieved standards content is data, never trusted instructions. The server
must isolate/delimit it, treat embedded instructions as untrusted, provide no
autonomous tools or credentials, constrain outputs to opaque authorized handles,
validate every returned handle as a subset of the authorized input set, and
discard or mark unavailable any nonconforming output.

Commercial V1 permits one bounded provider interaction for one explicit Human
request, with no automatic retry. Exact byte, item, output, and timeout limits
belong in EDS, but they must be finite, aggregate, deterministic, and enforced
before provider composition.

## AI provenance

When standards context participates in AI composition, the owning standards
intelligence interaction retains safe metadata sufficient to establish:

- provider, model, and version identity;
- prompt/template identity and digest;
- rights binding/processor decision and its version/digest;
- deterministic digest of authorized input handles and bounded composition;
- output digest and validated advisory result identity;
- timing, correlation, actor request, and terminal status; and
- the fact that output is advisory and requires Human selection.

The Technical Report accepted snapshot incorporates the interaction identity
and safe digest metadata when the Human relies on AI-assisted standards
selection or explanation. Protected excerpts, prompts containing protected
content, provider diagnostics containing protected content, credentials, and
object-storage keys never enter Audit/outbox payloads.

## Authorization and Organization isolation

Authorization occurs before protected lookup. The service establishes the
actor's active Organization, Project, Workspace where applicable, role, and
source-owner permissions before resolving or disclosing protected identity,
existence, count, edition, rights, source, assertion, or interaction state.

Rights evaluation occurs before retrieval, display, indexing, derived use, and
AI composition. Project configuration and Project applicability are selectors,
not data authority. A package hook is a candidate source, not authorization.

Organization A must not learn whether Organization B possesses, licenses,
indexes, cites, or stores a protected standard. Protected absent and forbidden
results are externally indistinguishable. Pagination, counts, validation order,
idempotency behavior, error shapes, correlations, and timing must not create a
cross-Organization existence oracle.

## Rights revocation and expiry

When a rights binding becomes expired, revoked, unknown, or otherwise invalid,
future/current protected retrieval, display, indexing, and AI use are denied
immediately at the governing application boundary. Cached decisions are keyed
to rights version/digest, short-lived or invalidated, and never accepted when
freshness is uncertain.

Derived knowledge remains available for current reasoning only if the active
rights capability expressly permits retained derived use. Otherwise its
protected representation is unavailable. Safe historical identifiers, digests,
state transitions, acceptance facts, and minimized Audit remain.

Revocation racing Report attachment, AI composition, or acceptance must be
resolved through a current rights-version check at the protected operation and
a transactional/optimistic guard at the final authority boundary. A stale
successful check cannot be reused to complete an operation after a conflicting
rights change.

Exact deletion, quarantine, retention, cache, and object-lifecycle mechanics
belong in EDS/IDS and later retention governance; they may not weaken immediate
current-use denial or immutable safe history.

## Discipline package integration

PATCH-052 discipline packages may provide finite, static,
non-authoritative standards applicability candidates. Exact candidate
provenance retains package key, package version, descriptor digest, Project
configuration revision, and hook identity.

Packages never contain protected standards text, arbitrary external URLs,
provider credentials, prompts, runtime connectors, executable customer rules,
or compliance determinations. A package suggestion cannot grant rights, create
canonical Standard identity, retrieve content, declare mandatory applicability,
or become material Report support without the respective owner operations.

The trusted source-controlled package release model under ADR-024 remains
authoritative. Standards are externally evolving and rights/time-sensitive, so
the Standards Registry must not mechanically reuse the package registry's
release semantics and must not introduce runtime plugins.

## PATCH-053 boundary

PATCH-053 remains authoritative and unchanged. Standards-aware context may
explain or support later Human interpretation of a retained Finding and may be
selected independently as Technical Report support. It must not modify:

- deterministic rule definitions or rule digests;
- source snapshots or Finding outcomes;
- historical replay or current reassessment semantics;
- Human Dispositions; or
- confirmed Project Change Impact authority.

Standards context is a separate advisory/report-support layer. A later standard,
rights, or applicability change cannot rewrite a PATCH-053 assessment or
Finding.

## Storage architecture

Existing private object-storage adapters and integrity patterns may be reused
as infrastructure for lawfully retained bounded snapshots. `SupportingFileAsset`
does not become the standards aggregate because it does not own canonical
edition, rights, source, applicability, assertion, or historical Report
semantics.

Evidence and Supporting Files may retain their existing roles and may be
referenced when independently authorized. Neither becomes a shortcut around
Standards Registry ownership or content rights. Whole-standard binary ingestion
is outside this ADR.

## Audit, outbox, and idempotency

Security- and authority-relevant standards operations require transactional
Audit and outbox coupling with the canonical state transition. At minimum this
includes identity/edition registration and standing changes, rights grant or
status change, applicability declaration/retirement, source retrieval outcome,
assertion creation/verification/rejection/current-use change, standards
intelligence request/outcome, Report-basis attachment, and the existing Report
acceptance event.

Payloads are minimized to identifiers, versions, digests, state codes, actor,
correlation, and timestamps. They never include protected clause text, licensed
excerpts, license documents, credentials, object-storage keys, full prompts, or
provider diagnostics containing protected content.

Idempotency is scoped and authorized before prior-result resolution. A key from
another Organization, Project, actor boundary, or materially different request
cannot disclose or replay a protected result. Request digests bind all
authority-relevant inputs.

## Failure semantics

The architecture requires fail-closed domain categories sufficient to
distinguish internally:

- protected not found;
- rights unknown;
- rights expired;
- rights revoked;
- content unavailable;
- edition unresolved;
- superseded;
- AI use not permitted;
- display not permitted;
- indexing not permitted;
- source incomplete; and
- indeterminate.

Supersession is an explicit standing condition, not silent replacement; policy
may require warning and attributable Human acknowledgement before current use.
Externally, protected absence and forbidden states are mapped to an
indistinguishable response. Exact HTTP/status mappings, retryability, and UI
copy belong in EDS/IDS.

## Registry semantics

The Standards Registry uses a hybrid temporal model:

- immutable Standard identities;
- immutable exact editions;
- versioned or append-only standing observations and corrections;
- versioned Organization rights bindings;
- append-only Project applicability declarations;
- immutable source snapshots/provider-handle attestations;
- governed assertions and intelligence interactions; and
- a deterministic observed registry revision/digest for consumers.

Corrections and new observations append attributable state. They do not mutate
historical consumer meaning. Registry revision/digest identifies the exact
observed registry projection and does not itself grant rights or applicability.
No runtime plugin, customer executable rule, or arbitrary connector is part of
the registry.

## Security invariants

The following threats and controls are architecture invariants:

| Threat | Required control |
|---|---|
| Cross-Organization leakage | Server-derived immutable Organization scope, authorization-before-lookup, protected count/absence equivalence, and tenant-scoped constraints |
| Forged Standard identity or edition | Opaque handles resolved by the Standards Registry; clients cannot author canonical identity or edition fields |
| Forged clause/source provenance | Server composition from an authorized immutable snapshot/provider handle with source identity and integrity digest |
| Stale rights cache | Rights-version/digest-bound decisions, invalidation/freshness enforcement, and denial when freshness is uncertain |
| Revocation race | Current rights check plus transactional or optimistic rights-version guard at retrieval, egress, attachment, and acceptance boundaries |
| Report acceptance race | Exact expected Report version, locked/atomic acceptance, current source/right validation, and immutable accepted snapshot |
| AI egress bypass | One server composer and rights gateway; no raw-text client path, autonomous retrieval, arbitrary tools, or unapproved processor |
| Malicious customer-supplied content | Quarantine/validation where applicable, bounded decoding, content treated as data, and no implicit rights or authority |
| Prompt injection in retrieved text | Strong data delimitation, no instruction trust, no tools/credentials, constrained handle output, and post-response subset validation |
| Idempotency disclosure | Authorization before lookup, tenant/actor/request-digest scoping, and protected response equivalence |
| Audit/outbox leakage | Allowlisted metadata-only payloads and redaction of content, secrets, storage keys, prompts, and unsafe diagnostics |
| Database privilege bypass | Least-privilege runtime roles, tenant/coherence/immutability constraints, migration-owned elevated changes, and database enforcement of terminal history where applicable |

All safe failure paths preserve the same authority order. Logging, metrics,
tracing, and provider error handling are subject to the same content-minimizing
rules as Audit.

## Migration direction

The accepted architectural direction is two sequential additive migrations
after the then-current PATCH-053 head, without reserving revision identifiers or
freezing SQL:

1. establish the standards identity/edition, temporal standing, Organization
   rights, Project applicability, source snapshot, assertion, interaction, and
   reliability foundation; then
2. add Technical Report standards-basis integration, legacy read
   compatibility, and database guards needed for new provenance and immutable
   accepted snapshots.

The split keeps the new canonical owner independently recoverable before Report
foreign references and acceptance guards depend on it. It permits the registry
foundation to be validated and rolled forward safely, preserves legacy
`StandardLocator` reads, and isolates the higher-risk immutable Report
compatibility change. Both migrations require later EDS/IDS and explicit
migration authority. This ADR creates neither migration and fixes no revision
ID, table, column, index, trigger, or downgrade procedure.

## Implementation batch direction

The architecture confirms five high-level implementation batches inside
PATCH-054:

1. identity/edition registry and rights foundation;
2. authorized retrieval and governed assertions;
3. Project applicability and static package candidate hooks;
4. Technical Report integration and historical legacy compatibility; and
5. advisory AI, frontend experience, and full conformance/security/performance
   proof.

This is dependency sequencing, not an implementation plan or authorized-file
manifest. A later accepted EDS/IDS and separately authorized implementation
plan may refine work within these boundaries but may not weaken them or create
new roadmap PATCHes.

## Conformance direction

Exactly **96 deterministic conformance vectors** is accepted as the
architecture-level PATCH-054 target. The suite must collectively prove identity
and edition immutability, rights capabilities and revocation, Organization
isolation, Project applicability, authorized retrieval, assertion governance,
Report history, AI egress/provenance, Audit minimization, failure semantics,
resource bounds, concurrency, idempotency, database enforcement, and accessible
RTL-capable frontend behavior.

The exact vector catalog, allocation, fixtures, limits, test ownership, and
acceptance commands belong in EDS. The number is a deterministic target, not
authority to create tests in this ADR phase.

## Decisions deferred to policy, EDS, and IDS

The following commercial/policy choices do not block ADR acceptance:

- first-sale standards issuers and source providers;
- issuer-specific or customer-specific commercial license terms;
- approval of any specific AI provider or processor;
- customer declarations and supporting legal documents;
- retention periods where law and contract permit configuration; and
- Organization-specific administrators or approval assignments within the
  future governed role model.

EDS must freeze the minimum executable semantic contract, including:

- exact aggregate fields, closed transition vocabularies, validation, and
  normalization/digest algorithms;
- the smallest closed assertion-kind vocabulary and verification transitions;
- exact rights capability representation, precedence, effective-time,
  freshness, revocation, and processor-decision rules;
- exact applicability states, mandatory-declaration evidence, supersession
  acknowledgement, and Human authority rules;
- exact snapshot/handle completeness and material/non-material validation;
- finite item, byte, page, timeout, output, pagination, and provider-call
  limits;
- owner ports, API commands/results, protected error mapping, accessibility,
  RTL, and UI semantics;
- exact 96-vector conformance ownership; and
- transaction, concurrency, idempotency, Audit/outbox, and operational
  acceptance rules.

IDS must later define approved persistence topology, schema/constraint/index
details, object-storage/provider adapter protocols, cryptographic and key
handling, cache invalidation, transaction/lock order, migrations and rollback,
observability redaction, and deployment/runtime privilege enforcement.

No unresolved architecture question remains. Later policy may choose among
fail-closed configurations without changing this decision.

## Consequences

### Positive

- standards provenance becomes canonical and resistant to forged client
  locators;
- exact editions, rights-at-use, Project applicability, and Human selection are
  historically reproducible;
- current protected access and AI egress fail closed under Organization-scoped
  rights;
- metadata-only bibliography remains useful without masquerading as material
  engineering support;
- accepted Technical Reports retain immutable meaning across supersession,
  withdrawal, registry change, and rights change;
- Organization-private standards and licensing posture do not leak;
- derived knowledge remains attributable and explicitly non-authoritative;
- AI remains provider-neutral and replaceable; and
- future source/provider policy can evolve without redefining the domain
  boundary.

### Costs and constraints

- SATCO gains additional domain aggregates and temporal relationships;
- Organizations require explicit rights administration and current-state
  revocation handling;
- source/provider adapters require immutable-handle, integrity, availability,
  and rights-aware behavior;
- every protected operation carries more complex authorization and
  non-disclosure requirements;
- historical basis and current access must be presented and tested as separate
  truths;
- Technical Report attachment, AI composition, and acceptance require
  cross-capability validation and concurrency protection;
- Audit, cache, idempotency, database privilege, prompt-injection, security, and
  performance testing burden increases; and
- protected historical content may be intentionally unavailable even though
  its safe provenance remains intact.

## Alternatives rejected

### A. Keep client-composed `StandardLocator` as the canonical source

Rejected. It permits forged or inconsistent identity, edition, clause, source,
and materiality, and bypasses canonical owner and rights validation.

### B. Store whole standards directly in Technical Report provenance

Rejected. It creates an unbounded shadow repository, couples Report retention
to protected-content rights, increases leakage, and makes the Report the wrong
content owner.

### C. Use Evidence or `SupportingFileAsset` as the standards aggregate

Rejected. Those capabilities do not own canonical edition, temporal rights,
Project applicability, provider retrieval, derived assertions, or standards
history. Their infrastructure may be reused only behind the standards owner.

### D. Let Project configuration imply access rights

Rejected. Configuration selects applicability and behavior; it cannot grant
Organization content authority or processor permission.

### E. Send customer-supplied standards content directly to AI

Rejected. Possession does not imply AI-processing rights, and a raw client path
bypasses processor policy, bounds, provenance, prompt-injection controls, and
the server rights gateway.

### F. Hardcode standard clauses into discipline packages

Rejected. It embeds protected/evolving material into trusted releases, bypasses
rights and source provenance, and makes package code an unauthorized standards
repository and rule authority.

### G. Reinterpret historical Reports against current standards

Rejected. It detaches Human acceptance from the exact reviewed basis and
violates ADR-023 immutability. Current reevaluation requires new governed state
and, for changed Report meaning, a successor Report.

### H. Allow metadata-only references to act as material support

Rejected. Catalog metadata proves neither source content nor clause meaning.
Metadata-only citations are permitted solely as explicit non-material
bibliographic references.

### I. Make AI compliance determination authoritative

Rejected. AI cannot own legal applicability, mandatory applicability,
compliance, engineering judgment, or Report acceptance. Its output remains
advisory under Human authority.

## Compatibility with prior architecture

### ADR-023 — Human-Accepted AI-Assisted Technical Reports

ADR-023 remains authoritative and unchanged. ADR-027 supplies the canonical
standards provenance and rights boundary required by ADR-023's historical
resolvability rule. It preserves `draft → accepted`, exact Human acceptance,
immutable accepted content, successor lineage, acceptance distinct from
publication, and AI non-authority.

### PATCH-051 and ADR-024 — trusted discipline packages

Package identity, trusted source-controlled releases, configuration,
compatibility, and non-executable static contributions remain unchanged.
Packages may suggest bounded candidates with exact package provenance but do
not own standards, rights, content, applicability authority, or runtime
connectors. The Standards Registry deliberately uses temporal rights semantics
rather than copying package-release mechanics.

### PATCH-052 and ADR-025 — discipline packages and Engineering Identifiers

Discipline packages and Engineering Identifiers retain their accepted owners.
Standards candidates may refer to authorized Project/Workspace context but do
not change Object or Identifier identity, package configuration, or package
authority.

### PATCH-053 and ADR-026 — cross-discipline Engineering Intelligence

Assessments, Findings, source manifests, Human Dispositions, rule digests,
historical replay, and confirmed-impact authority remain unchanged. Standards
provide only a separately authorized advisory/report-support layer.

### Engineering Guidance

Engineering Guidance remains deterministic-first, bounded, provider-neutral,
Human-selected advisory assistance. ADR-027 applies the stronger standards
rights, immutable handle, egress, and provenance controls whenever protected
standards context participates. Guidance does not become standards, compliance,
applicability, or Report acceptance authority.

### Evidence and Context

Evidence and Context retain their canonical owners and authorization seams.
They may reference safe standards identities or receive authorized derived
context, but cannot mint rights, canonical editions, source snapshots, or
material standards support. Project Context does not grant data authority.

### Supporting Files

Supporting Files retain file, scan, integrity, and private-storage semantics.
Infrastructure patterns may be reused, but `SupportingFileAsset` is not the
canonical standards aggregate and file possession grants no standards right.

### Future PATCH-055

PATCH-055 is not started and not authorized. This ADR creates no normalized
engineering authoring, graph expansion, workflow, Memory, portfolio, or later
roadmap behavior. A future PATCH-055 design may consume only authorized public
standards contracts and may not bypass or reinterpret ADR-027.

No accepted prior ADR or closed PATCH is superseded or silently amended by
ADR-027.

## Explicit non-authorization and roadmap boundary

This ADR does not:

- create EDS-054, IDS-054, an implementation plan, or file manifest;
- define SQL, migration revision IDs, endpoints, DTOs, UI layouts, concrete
  numeric resource limits, provider integrations, or legal policy;
- authorize production, test, frontend, migration, deployment, staging,
  commit, or push changes;
- ingest, store, scrape, reproduce, or distribute a whole standard;
- approve an issuer, source provider, license, processor, or AI provider;
- establish Report publication or Organizational Memory admission;
- alter PATCH-051, PATCH-052, PATCH-053, or their accepted architecture; or
- start or authorize PATCH-055 or any later roadmap capability.

## Independent ADR review

### Review control

The candidate was reviewed afresh at architecture level against the
Human-accepted PATCH-054 Discovery, SATCO Governance Model, frozen Commercial V1
roadmap, ADR-023, PATCH-051/052/053 boundaries, Human engineering authority, AI
non-authority, Organization isolation, rights/copyright safety, historical
reproducibility, accepted Technical Report immutability, and PATCH-055+
non-leakage. The review is recorded here so ADR preparation creates one
governance artifact only.

### Challenge results

| Challenge | Result |
|---|---|
| Canonical identity and exact edition collapse | PASS — separate immutable identities; rights and applicability remain external bindings |
| Global metadata grants protected content rights | PASS — catalog existence is explicitly non-authorizing |
| Organization-private identity/existence leakage | PASS — authorization precedes protected lookup/count/error/idempotency behavior |
| Project applicability grants rights or mandatory standing | PASS — applicability, access, Report reliance, and mandatory declaration are distinct; only attributable Human declaration can make mandatory |
| Metadata-only citation masquerades as material support | PASS — allowed only as explicit non-material bibliography; material use needs authorized immutable source provenance |
| Client forges identity, edition, clause, or source | PASS — new provenance accepts opaque handles and is composed by the server from canonical owners |
| Legacy history is rewritten | PASS — accepted legacy `StandardLocator` remains readable and immutable; new manual legacy submission is prohibited |
| Rights expiry/revocation rewrites history or grants perpetual access | PASS — immutable safe rights-at-use basis is separate from current rights reauthorization |
| Revocation or acceptance race uses stale authority | PASS — final current-version checks and transactional/optimistic guards are mandatory |
| Whole-standard repository pulled into PATCH-054 | PASS — only bounded lawful snapshots/immutable handles; whole-standard ingestion is excluded |
| Derived assertion becomes authoritative rule | PASS — bounded attribution and verification mean faithful extraction only; current use remains rights-gated |
| AI receives unauthorized or unbounded text | PASS — server-only composition after processor rights, finite aggregate EDS limits, one call, zero automatic retries |
| Prompt injection creates tools or authority | PASS — retrieved content is data, no tools/credentials, handle-constrained output, subset validation |
| AI declares compliance/applicability/acceptance | PASS — all remain expressly outside AI authority |
| Audit/outbox leaks protected material | PASS — allowlisted safe metadata only |
| Package embeds protected clauses or runtime connectors | PASS — static candidate hooks only with exact package/configuration provenance |
| PATCH-053 findings/rules are reinterpreted | PASS — standards remain a separate advisory/report-support layer |
| ADR-023 Report lifecycle/immutability is weakened | PASS — lifecycle and Human acceptance stay authoritative and unchanged |
| Migration direction freezes implementation detail | PASS — two logical additive phases are accepted without IDs, SQL, or authorization |
| EDS/IDS/implementation/PATCH-055 is pulled forward | PASS — each remains expressly not started and not authorized |

### Review findings

Critical: **0**

Major: **0**

Minor: **0**

Observation: **0**

Blocking findings: **none**

Unresolved architecture questions: **none**

Independent ADR review verdict:

**PASS / ACCEPTED-CANDIDATE / READY FOR HUMAN ADR ACCEPTANCE**

This review verdict does not constitute Human ADR acceptance.

## Governance disposition

ADR-027 design verdict:

**PASS / COMPLETE / REVIEW PASS / AWAITING HUMAN ADR ACCEPTANCE**

The exact next governed action is Human acceptance or rejection of ADR-027.
Only after explicit Human ADR-027 acceptance may separate authority be
considered for EDS-054. No downstream authority is implied. PATCH-055+ remains
not started and not authorized.

## Revision history

| Version | Date | Description |
|---|---|---|
| 0.1 | 2026-09-12 | Proposed candidate prepared from the Human-accepted PATCH-054 Discovery; independent ADR review PASS; awaiting Human ADR acceptance. |

## Status reconciliation — 2026-09-14

The Human Architecture Authority confirms **ADR-027 PASS / ACCEPTED / AUTHORITATIVE**. The earlier candidate wording above is preserved as the historical pre-acceptance state and is superseded for current governance purposes by this append-only record. All downstream PATCH-054 design and implementation authority already recognized ADR-027 as Human accepted. PATCH-055 remains outside this authority.
