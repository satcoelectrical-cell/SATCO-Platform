# EDS-054 — Rights-Aware Standards Registry and Standards-Aware Technical Report Intelligence

## 1. Status, authority, and normative force

| Field | Value |
|---|---|
| Date | 2026-09-12 |
| PATCH | PATCH-054 — Rights-Aware Standards Registry & Standards-Aware Technical Report Intelligence |
| Human EDS-054 design authority | **GRANTED** |
| PATCH-054 Discovery | **HUMAN ACCEPTED** |
| ADR-027 | **HUMAN ACCEPTED / AUTHORITATIVE** |
| EDS-054 candidate | **PASS / COMPLETE / AWAITING HUMAN EDS ACCEPTANCE** |
| EDS self-review | **PASS**; Critical/Major/Minor/Observation **0/0/0/0** |
| IDS-054 / Implementation Plan-054 | **NOT STARTED / NOT AUTHORIZED** |
| Production/tests/frontend/migrations | **NOT AUTHORIZED / NONE CHANGED** |
| PATCH-055+ | **NOT STARTED / NOT AUTHORIZED** |

This EDS translates ADR-027 into the exact, finite, testable Commercial V1
product contract. Normative **MUST**, **MUST NOT**, **SHALL**, **SHALL NOT**, and
**EXACTLY** language binds later IDS and implementation. This artifact does not
accept itself, reopen ADR-027, define SQL or implementation files, reserve a
migration revision, authorize downstream work, or claim that future
conformance vectors currently pass.

## 2. Authority hierarchy and canonical owners

Authority for a protected operation is the intersection of:

**authenticated actor AND active Organization membership AND Project authority
when Project-scoped AND operation-specific actor class AND catalog visibility
AND exact current rights binding AND source/provider permission AND current
resource integrity AND owning-capability authorization**.

Canonical owners are unchanged from ADR-027:

| Contract | Canonical owner |
|---|---|
| Standard identity, exact edition, standing observation | Standards Registry |
| Organization rights binding | Organization Standards Rights boundary |
| Project applicability declaration | Project Standards Applicability boundary |
| bounded retrieval snapshot or immutable handle | Standards Retrieval and Provenance boundary |
| derived assertion | Standards Knowledge boundary |
| advisory standards interaction | Standards Intelligence boundary |
| draft/accepted Report standards basis | Technical Report aggregate |
| Audit/outbox/idempotency | reliability records transactionally coupled to the initiating owner |

Project configuration, packages, clients, AI, Evidence, Context, Supporting
Files, and Technical Reports cannot mint canonical Standard identity, edition,
rights, or source provenance.

## 3. Shared machine conventions

- Domain IDs are opaque UUIDs serialized as lowercase RFC 4122 hyphenated
  strings. Existing integer actor, Project, and Workspace IDs remain positive
  integers.
- Machine tokens are lowercase ASCII matching
  `[a-z][a-z0-9]*(?:[._-][a-z0-9]+)*`. Display prose never drives behavior.
- Timestamps are timezone-aware UTC serialized with microseconds and **Z**.
- Digests are lowercase 64-character SHA-256 hexadecimal.
- Human prose is Unicode NFC. Comparison keys use the normalization contract in
  section 5 and are never displayed as authoritative source spelling.
- **standards.canonical_json.v1** is UTF-8 JSON with NFC strings, lexically
  sorted object keys, no insignificant whitespace, lowercase JSON literals,
  semantic array order defined by this EDS, no duplicate keys, and no
  binary-floating-point or unknown fields.
- A record digest is SHA-256 over its domain token, one zero byte, and canonical
  JSON excluding its own digest field.
- Unknown is an explicit vocabulary value, not null. Optional fields are null
  only where this EDS explicitly permits them.

## 4. Exact closed Commercial V1 vocabularies

| Vocabulary | Exact values | Meaning |
|---|---|---|
| **CatalogScope** | **global_trusted**, **organization_private** | platform-reviewed shared metadata or tenant-private identity |
| **StandardStanding** | **current**, **superseded**, **withdrawn**, **unknown** | latest attributable observation; never edition identity |
| **RightsBasis** | **metadata_only**, **customer_supplied_declared**, **organization_license**, **open_distribution**, **internally_authored**, **unknown** | asserted basis, not a legal conclusion |
| **RightsStatus** | **active**, **expired**, **revoked**, **unknown** | current binding usability |
| **AIProcessingPermission** | **prohibited**, **local_only**, **approved_processor** | AI egress class |
| **ProjectApplicabilityStatus** | **candidate_advisory**, **declared_applicable**, **declared_not_applicable**, **retired** | append-only applicability state |
| **ProjectApplicabilityRole** | **informative**, **design_basis**, **mandatory** | Project role; mandatory requires explicit Human provenance |
| **AssertionOrigin** | **human**, **deterministic**, **ai_assisted** | creator/method class, not authority |
| **AssertionVerificationStatus** | **unverified**, **human_verified**, **rejected**, **stale** | current assertion verification/use state |
| **AssertionKind** | **requirement_statement**, **defined_term**, **numeric_constraint**, **cross_reference** | smallest V1 derived-knowledge vocabulary |
| **StandardsBasisMateriality** | **reference_only**, **material_support** | bibliography versus claim-supporting material |
| **SourceAvailabilityStatus** | **available**, **temporarily_unavailable**, **permanently_unavailable**, **rights_restricted**, **integrity_failed** | current resolvability state |
| **StandardsIntelligenceResultStatus** | **completed_with_suggestions**, **completed_no_suggestions**, **not_permitted**, **unavailable**, **invalid_output** | terminal advisory interaction outcome |

The exact public operation outcomes are **success**, **invalid_request**,
**protected_not_found**, **conflict**, **not_permitted**, **unavailable**, and
**indeterminate**.

The exact internal failure/reason codes are:

- **NOT_FOUND**;
- **PROTECTED_NOT_FOUND**;
- **INVALID_REQUEST**;
- **RIGHTS_UNKNOWN**;
- **RIGHTS_EXPIRED**;
- **RIGHTS_REVOKED**;
- **CONTENT_UNAVAILABLE**;
- **EDITION_UNRESOLVED**;
- **SUPERSEDED**;
- **WITHDRAWN**;
- **AI_USE_NOT_PERMITTED**;
- **DISPLAY_NOT_PERMITTED**;
- **INDEXING_NOT_PERMITTED**;
- **SOURCE_INCOMPLETE**;
- **INDETERMINATE**;
- **STALE_ASSERTION**;
- **CONFLICT**;
- **VERSION_CONFLICT**;
- **IDEMPOTENCY_CONFLICT**;
- **INTEGRITY_FAILURE**;
- **RESOURCE_LIMIT_EXCEEDED**;
- **AI_UNAVAILABLE**;
- **INVALID_AI_OUTPUT**; and
- **LEGACY_STANDARD_LOCATOR_PROHIBITED**.

No other enum or result token is valid in Commercial V1 without a governed EDS
change.

## 5. Standard identity, edition, and standing workflow

### 5.1 Standard identity contract

A Standard identity has exactly these product fields:

1. **standard_id**;
2. **catalog_scope**;
3. **organization_id**, required only for **organization_private**;
4. **issuer_key** and issuer display name;
5. **designation** and normalized designation;
6. **title**;
7. optional public language/jurisdiction metadata;
8. **normalization_version**;
9. attributable metadata source reference;
10. **identity_digest**;
11. registering actor and registration time; and
12. immutable identity predecessor/correction reference when a mistaken
    registration is replaced.

Identity registration is:

**authorize scope administrator → normalize issuer/designation → search
authorized duplicate domain → validate attributable metadata → allocate
immutable identity → Audit/outbox atomically**.

Identity is never edited in place. A material correction creates a new identity
with explicit correction lineage and retires the mistaken identity from new
selection without altering historical references.

### 5.2 Exact duplicate normalization

**satco_standard_key_nfkc_casefold_v1** performs Unicode NFKC, maps Unicode dash
characters to ASCII hyphen, trims leading/trailing Unicode whitespace,
collapses internal Unicode whitespace to one ASCII space, and applies Unicode
casefold. It does not remove punctuation or issuer-significant separators.

Within **global_trusted**, duplicate identity is the pair
**normalized issuer_key + normalized designation**. Within
**organization_private**, Organization ID is prepended. Same request digest is
idempotent; a different representation resolving to the same key returns
**CONFLICT** with no duplicate creation and no cross-tenant detail.

### 5.3 Exact edition contract

An exact Standard edition has:

1. **standard_edition_id**;
2. parent **standard_id**;
3. issuer-authored **edition_designation** and normalized edition designation;
4. optional official publication identifier;
5. publication date;
6. optional effective date;
7. language;
8. jurisdiction/applicability metadata, explicitly non-authoritative;
9. attributable official metadata source reference;
10. optional predecessor edition ID;
11. **edition_digest**;
12. registering actor and registration time.

The edition workflow is:

**resolve authorized immutable identity → validate exact publication unit →
normalize edition designation → reject duplicate → allocate immutable edition
→ append initial standing observation → Audit/outbox atomically**.

A revision, consolidated publication, or amendment-composed publication is a
new edition whenever its issuer treats it as a separately citable publication
unit. Edition identity never changes. The duplicate key is parent Standard ID
plus normalized edition designation; when the issuer reuses a designation, the
official publication identifier or publication date is additionally required
to disambiguate. Ambiguity returns **EDITION_UNRESOLVED**.

### 5.4 Standing observation and historical retrieval

A standing observation has **observation_id**, edition ID, standing, observed
date/time, attributable source reference/digest, Human or trusted-system actor,
predecessor observation ID, and observation digest. Update means append a new
observation. The latest authorized valid observation supplies current standing;
the observation pinned by a historical basis supplies standing-at-use.

Search/detail returns only authorized metadata, deterministic ordering, and
safe pagination. Historical retrieval by opaque identity/edition/observation
handle returns the immutable record even after a later observation, subject to
catalog visibility. It never substitutes a newer edition.

## 6. Catalog-scope behavior

| Behavior | **global_trusted** | **organization_private** |
|---|---|---|
| discover metadata | any authenticated actor with product access, subject to safe policy | active member of owning Organization with Project-independent standards metadata access |
| register identity/edition | platform catalog administrator | Organization standards administrator |
| append standing observation | platform catalog administrator or trusted catalog ingestion actor | Organization standards administrator |
| disclose content-rights posture | never from catalog metadata | only through separately authorized rights operations |
| tenant boundary | shared safe metadata | Organization ID is mandatory and authorization precedes lookup/count |
| duplicate domain | platform-global normalized key | owning Organization plus normalized key |

Global metadata never implies global content, source, display, indexing,
derived-use, or AI rights. Organization-private absence and forbidden existence
are externally identical.

## 7. Organization rights binding

### 7.1 Exact attachment and fields

A rights binding attaches to the exact bounded tuple:

**organization_id + standard_edition_id + source_provider_id**.

There is no Project-scoped rights binding and no provider wildcard. The reserved
provider identity **registry_metadata** represents metadata-only catalog use.
Each protected source/provider requires its own binding.

A binding has:

1. **rights_binding_id**;
2. Organization, exact edition, and source/provider IDs;
3. RightsBasis and RightsStatus;
4. independent booleans for metadata visibility, content storage, indexing,
   excerpt/display, source retrieval, derived assertion retention, and derived
   assertion current use;
5. AIProcessingPermission and, only for **approved_processor**, a nonempty
   approved processor policy ID set;
6. effective-from and optional effective-until timestamps;
7. attributable rights authority reference and safe digest;
8. monotonically increasing product version;
9. predecessor binding ID;
10. creating/replacing/revoking Human actor, reason code, and time; and
11. **rights_digest**.

### 7.2 Workflow and version behavior

The workflow is:

**administrator creates configured binding → binding becomes usable only when
status active and effective → replacement appends version and closes prior
current head → effective-until produces expiry → explicit revocation appends
revoked head → all current protected use denies → safe history remains**.

Only one current head exists for the tuple. Bindings are append-only. Replacement
requires expected current version and never changes prior rights-at-use.
Scheduled expiry is derived deterministically at the effective-until instant
and records **standards.rights.expired** once. Revocation wins immediately at
its serialized effective time.

### 7.3 Exact rights capability matrix

**SCOPE** means CatalogScope visibility still applies. **CONFIG/DENY** means an
Organization standards administrator may explicitly enable a capability only
when attributable policy allows it; the stored default is deny. **DENY(code)**
is unconditional for the evaluated binding.

| RightsBasis | RightsStatus | metadata | storage | indexing | display | retrieval | derived retain | derived current use | AI |
|---|---|---|---|---|---|---|---|---|---|---|
| metadata_only | active | SCOPE and configured visibility | DENY | DENY | DENY | DENY | DENY | DENY | prohibited |
| customer_supplied_declared | active | SCOPE and configured visibility | CONFIG/DENY | CONFIG/DENY | CONFIG/DENY | CONFIG/DENY | CONFIG/DENY | CONFIG/DENY | configured mode, default prohibited |
| organization_license | active | SCOPE and configured visibility | CONFIG/DENY | CONFIG/DENY | CONFIG/DENY | CONFIG/DENY | CONFIG/DENY | CONFIG/DENY | configured mode, default prohibited |
| open_distribution | active | SCOPE and configured visibility | CONFIG/DENY | CONFIG/DENY | CONFIG/DENY | CONFIG/DENY | CONFIG/DENY | CONFIG/DENY | configured mode, default prohibited |
| internally_authored | active | SCOPE and configured visibility | CONFIG/DENY | CONFIG/DENY | CONFIG/DENY | CONFIG/DENY | CONFIG/DENY | CONFIG/DENY | configured mode, default prohibited |
| unknown | active | SCOPE only when independently safe | DENY(RIGHTS_UNKNOWN) | DENY(RIGHTS_UNKNOWN) | DENY(RIGHTS_UNKNOWN) | DENY(RIGHTS_UNKNOWN) | DENY(RIGHTS_UNKNOWN) | DENY(RIGHTS_UNKNOWN) | prohibited |
| any | expired | SCOPE only when independently safe | DENY(RIGHTS_EXPIRED) | DENY(RIGHTS_EXPIRED) | DENY(RIGHTS_EXPIRED) | DENY(RIGHTS_EXPIRED) | no new retention | DENY(RIGHTS_EXPIRED); a separate newer active binding may authorize retained use | prohibited |
| any | revoked | SCOPE only when independently safe | DENY(RIGHTS_REVOKED) | DENY(RIGHTS_REVOKED) | DENY(RIGHTS_REVOKED) | DENY(RIGHTS_REVOKED) | no new retention | DENY(RIGHTS_REVOKED); a separate newer active binding may authorize retained use | prohibited |
| any | unknown | SCOPE only when independently safe | DENY(RIGHTS_UNKNOWN) | DENY(RIGHTS_UNKNOWN) | DENY(RIGHTS_UNKNOWN) | DENY(RIGHTS_UNKNOWN) | DENY(RIGHTS_UNKNOWN) | DENY(RIGHTS_UNKNOWN) | prohibited |

Effective permission additionally requires correct Organization/source/edition,
effective time, fresh binding version, actor authority, source availability,
and the operation-specific capability. **local_only** permits only the approved
local processor class and forbids external egress. **approved_processor**
requires exact membership of the selected processor policy ID. No basis
auto-enables a protected capability and possession never supplies a missing
permission.

## 8. Project applicability and package candidates

### 8.1 Applicability record and workflow

A Project applicability record has **applicability_id**, Organization and
Project IDs, exact edition ID, status, role, rationale code and Human-readable
rationale, origin, source/candidate references, mandatory-source kind/reference
and digest when mandatory, expected predecessor revision, monotonically
increasing revision, predecessor/successor IDs, actor, time, and applicability
digest.

The exact workflow is:

**candidate_advisory → Human review → declared_applicable OR
declared_not_applicable → optional later declared_applicable with mandatory
role → retired → optional successor declaration**.

Review and every change append a record. No candidate changes Project state by
itself. An edition must resolve exactly before declaration. Rights are not
required to declare safe metadata applicability, and applicability never grants
rights.

The role **mandatory** is valid only with status **declared_applicable**, an
authenticated Project engineer, a nonempty rationale, and one source kind from
**contract**, **regulation**, **customer_requirement**, or **company_policy**,
plus an attributable reference and digest. AI, package hooks, source-provider
metadata, and licenses cannot supply mandatory authority.

At most one non-retired Human declaration head exists for a Project and exact
edition. Conflicting concurrent declarations return **VERSION_CONFLICT**.

### 8.2 Exact package candidate contract

A PATCH-052 hook candidate has exactly:

1. **candidate_id** and **candidate_digest**;
2. Organization, Project, and Workspace IDs;
3. package key and package version;
4. descriptor digest;
5. Project configuration revision;
6. hook ID;
7. candidate Standard designation key and optional family key;
8. optional already-resolved Standard identity/edition handle;
9. suggested role, limited to **informative** or **design_basis**;
10. closed advisory rationale code; and
11. emission time.

The candidate is static, bounded, non-authoritative data. It contains no
protected text, URL, source credentials, prompt, executable rule, provider
operation, or mandatory role. It cannot register standards, grant rights,
retrieve content, call AI, or declare Project applicability. Unresolved keys
remain candidates and never become canonical handles by string matching alone.

## 9. Authorized source retrieval and materiality

### 9.1 Retrieval workflow

The exact workflow is:

**Human/application request → authenticate and authorize actor/Organization/
Project → authorize protected lookup → resolve exact edition and provider →
load fresh current rights head → evaluate retrieval and intended-use
capabilities → validate standing and source availability → enforce byte/item
bounds → retrieve through an allowlisted adapter → validate integrity →
construct immutable snapshot/handle attestation → final rights-version check →
optionally display/create assertion/compose AI → Audit/outbox**.

No client URL is fetched. No general standards browser, scraping operation,
arbitrary provider query, directory listing, or unbounded search exists.

### 9.2 Source snapshot contract

A material Standard source snapshot/attestation has:

1. **source_snapshot_id**;
2. Organization, Standard identity, and exact edition IDs;
3. source/provider ID and adapter policy/version;
4. exact clause/section/page/provider location;
5. SourceAvailabilityStatus;
6. retrieval actor, request purpose, correlation, and time;
7. bounded byte length and content digest;
8. either a lawfully retained encrypted snapshot locator or an immutable
   provider handle, never both absent for material support;
9. provider immutable-version token/digest when handle-backed;
10. rights binding ID, version, digest, and evaluated capability set at use;
11. standing observation ID/digest at use;
12. source metadata digest;
13. integrity verification result/time; and
14. **snapshot_digest**.

Protected bytes are not part of Audit/outbox. A provider handle qualifies as
immutable only when the allowlisted adapter can re-resolve the same exact
publication/location and verify the same content/version digest. If that
guarantee cannot be made and no lawful snapshot is retained, the record is
**reference_only**, never **material_support**.

### 9.3 Materiality contract

| Materiality | Allowed basis | Report/AI behavior |
|---|---|---|
| **reference_only** | safe catalog identity, exact edition when known, bibliographic source metadata | may appear as visibly non-material bibliography; cannot substantiate a standards-backed claim or provide clause text to AI |
| **material_support** | available authorized immutable snapshot or qualifying provider handle with exact edition/location/integrity/rights provenance | may support a Human-selected Report claim and authorized AI context after all current checks |

API responses include materiality as a mandatory machine field. UI renders a
text label and semantic state, never color alone. Report attachment rejects a
materiality mismatch with **SOURCE_INCOMPLETE**. A reference-only basis cannot
be upgraded by client assertion.

## 10. StandardKnowledgeAssertion

### 10.1 Exact contract

An assertion has:

1. **assertion_id** and Organization ID;
2. exact edition ID and source snapshot/handle ID;
3. exact source location and source/content digest;
4. AssertionKind;
5. bounded canonical assertion representation;
6. AssertionOrigin;
7. extraction method ID/version/digest;
8. template/model interaction reference when AI-assisted;
9. AssertionVerificationStatus;
10. creating actor/time;
11. optional Human verifier, verification time, and rationale;
12. rights binding/version/digest at derivation;
13. current retained-derived-use eligibility and evaluated rights revision;
14. predecessor/successor assertion or verification record reference; and
15. **assertion_digest**.

Creation requires an authorized **material_support** source and active
permissions for the derivation operation and derived retention. The four kinds
mean only:

- **requirement_statement**: bounded attributable statement/paraphrase of a
  source requirement, not a compliance result;
- **defined_term**: one source-defined term and bounded definition;
- **numeric_constraint**: one bounded typed value/range/unit with source
  location; and
- **cross_reference**: one explicit source-to-source clause reference.

No general knowledge graph, applicability inference, compliance mapping, or
executable rule is created.

### 10.2 Verification, rejection, and staleness

New Human/deterministic/AI-assisted assertions start **unverified**. An
authorized Human may append **human_verified** only after current source display
and derived-use authorization and exact digest comparison. Verification means
faithful extraction only. It does not mean engineering approval, compliance,
applicability, mandatory applicability, or Report acceptance.

**rejected** is an attributable terminal decision for that assertion version.
Correction creates a successor assertion. **stale** means the source/handle
integrity can no longer be confirmed, a source correction invalidates the
extraction, or current rights prohibit current use. A later valid rights binding
may restore current-use eligibility only by a new evaluated eligibility record;
it does not erase the stale history.

### 10.3 Rights after expiry or revocation

After rights expiry/revocation:

- if a newer active binding for the same Organization/edition/provider
  expressly permits both retained derived assertion and current derived use,
  an unchanged **human_verified** assertion may remain eligible after fresh
  integrity and rights evaluation;
- otherwise its protected representation is masked, current eligibility is
  false, and current reasoning returns **STALE_ASSERTION** or
  **PROTECTED_NOT_FOUND** as disclosure policy requires; and
- accepted historical Reports retain the assertion ID, digest, status-at-use,
  rights-at-use, and Human selection without recomputation.

Unverified assertions never become current material support merely because
retained use is permitted.

## 11. Technical Report standards workflow

### 11.1 Candidate-to-acceptance workflow

The exact workflow is:

**current draft Report → Human requests standards candidates → deterministic
eligibility checks → optional Human-requested advisory standards intelligence
→ Human selects opaque basis handles → server resolves and composes basis →
new Report revision → final acceptance recheck → one atomic immutable accepted
snapshot**.

Candidate responses separate eligible, warning, reference-only, and unavailable
states without disclosing protected existence. AI output cannot attach a basis.
Only the Human selection command can request attachment, and only the Technical
Report owner creates the revision.

Clients never submit canonical raw Standard identity, edition, issuer, clause,
source, locator, protected text, rights facts, assertion text, or historical
basis fields. They submit opaque handles, requested materiality, Human
rationale, expected Report version, and idempotency identity.

### 11.2 Legacy StandardLocator cutover

The operational cutover behavior is exact:

- accepted historical snapshots containing legacy StandardLocator remain
  byte-for-byte readable and show **legacy_unattested_reference**; no rights,
  materiality, or content authority is inferred;
- a pre-cutover draft containing a legacy locator remains readable but is
  marked **legacy_conversion_required**;
- any post-cutover draft revision or acceptance must remove the locator or
  replace it through the canonical handle workflow;
- every new manual legacy locator submission returns **invalid_request /
  LEGACY_STANDARD_LOCATOR_PROHIBITED**;
- a successor Report does not copy legacy locators as new provenance; its Human
  author must select a current canonical reference-only or material basis; and
- migration records only the global cutover capability state and guards new
  writes. It never rewrites, parses, resolves, or backfills an accepted legacy
  snapshot.

### 11.3 Final acceptance recheck

The Technical Report acceptance operation atomically revalidates:

1. actor authentication, active Organization membership, Project/Report access,
   and Report-acceptor authority;
2. exact expected draft Report revision remains current and unaccepted;
3. every opaque basis handle still resolves in the same Organization;
4. exact Standard and edition identity/digest;
5. standing observation and required acknowledgement;
6. exact Project applicability record/revision where used;
7. rights binding ID/version/digest, status, effective time, provider, and every
   required capability;
8. snapshot/handle availability, immutable token, byte extent, and integrity
   digest;
9. materiality matches the source contract;
10. each used assertion digest, **human_verified** status when material, and
    current-use eligibility;
11. AI interaction metadata/digests when AI-assisted context was selected;
12. Report limits, duplicate/conflict rules, and total provenance limits; and
13. Audit/outbox readiness.

Any invalid material basis fails the whole acceptance with no partial accepted
Report, no acceptance Audit/outbox, and no mutation. Reference-only items that
become forbidden are also removed or corrected in a new revision before
acceptance; acceptance never silently drops a Human-selected basis.

### 11.4 StandardHistoricalBasisV1

Each accepted standards basis item freezes:

1. schema version **standard_historical_basis_v1**;
2. basis ID, materiality, and Human selection rationale;
3. Standard identity ID, scope-safe display metadata, and identity digest;
4. exact edition ID, designation, publication metadata, and edition digest;
5. standing observation ID/value/digest at use and acknowledgement when
   required;
6. source snapshot/provider-handle ID, exact location, provider identity,
   immutable token, availability-at-use, extent, and snapshot digest;
7. content digest when available, never required to disclose protected bytes;
8. rights binding ID/version/digest, basis/status, evaluated capabilities, and
   decision time;
9. Project applicability ID/revision/digest/status/role when present;
10. assertion ID/kind/digest/origin/verification status and verifier identity
    when present;
11. standards intelligence interaction ID, provider/model/template/input/output
    digests and processor decision when applicable;
12. selecting Human, selection time, and Report revision; and
13. accepted Report identity/version/time and basis-item digest.

Encoding and physical storage belong in IDS. Later standing, rights,
applicability, source, assertion, or provider change never mutates this contract.

### 11.5 Current access to historical Reports

An authorized Report reader always sees safe historical provenance and the
standing/rights/materiality state recorded at acceptance. Before showing any
protected excerpt or resolving a provider handle, the system evaluates current
Organization membership, Report access, display permission, current rights
head, source availability, and integrity.

When current display is denied, the UI/API returns a masked
**rights_restricted** or safe **CONTENT_UNAVAILABLE** presentation without
protected text, protected counts, storage locators, or cross-tenant detail. The
accepted Report meaning, source digest, rights-at-use fact, and Human selection
remain unchanged. Historical acceptance is never a present access grant.

## 12. Standing, supersession, and deterministic eligibility

### 12.1 Standing behavior

| Standing | Reference-only | New material reliance |
|---|---|---|
| **current** | allowed when metadata is visible | allowed when all rights/source/applicability checks pass |
| **superseded** | allowed with visible status | requires exact declared applicability plus Human acknowledgement of the standing observation and rationale |
| **withdrawn** | allowed with visible status | requires exact declared applicability, Human acknowledgement and rationale; otherwise blocked |
| **unknown** | visible only as unresolved safe metadata | blocked with **EDITION_UNRESOLVED** |

An acknowledgement records Human, time, Report revision, standing observation
ID/digest, and rationale. It does not declare compliance or mandatory
applicability. Mandatory status exists only through the independent Project
declaration contract. Existing accepted Reports are never rechecked or
rewritten merely because standing changes.

### 12.2 Deterministic standards intelligence

Before optional AI, the server evaluates exactly:

- identity and edition resolution;
- current standing and acknowledgement need;
- current rights status/effective time/provider/capabilities;
- actor, Organization, Project, and source-owner authorization;
- Project applicability status/role/revision;
- source availability, completeness, extent, and integrity;
- requested materiality validity;
- assertion kind, digest, verification, and current-use eligibility;
- duplicate handles, duplicate sources, and conflicting materiality; and
- all item/byte/provenance limits.

Deterministic output is a stable ordered set of at most 12 advisory candidates,
each with opaque handle, materiality, eligibility state, safe rationale/warning
codes, exact edition/standing, and source/assertion availability safe for the
actor. Order is material support before reference-only, then applicability role,
issuer key, designation, edition, source location, and handle UUID.

It never declares compliance, legal sufficiency, mandatory applicability,
engineering approval, or acceptance. Invalid/incomplete protected sources
produce no partial material candidate and no hidden count.

## 13. Standards-aware AI contract

### 13.1 Workflow

The exact workflow is:

**Human request → deterministic result → authorized handle selection → current
rights/processor decision → bounded context composition → one provider call →
closed-schema output validation → advisory result**.

There is exactly one provider call, a 30-second deadline, zero automatic AI
retries, no autonomous loop, no arbitrary tool, no client/provider-selected
retrieval, and no scraping. Deterministic results survive every AI outcome.

The server serializes retrieved text as untrusted delimited data. Retrieved
instructions have no authority. The provider receives no credentials, object
keys, arbitrary URLs, mutation tools, retrieval tools, or hidden tenant data.

### 13.2 Input and output

AI input contains only:

- the Human-selected advisory purpose and bounded question;
- opaque authorized handle IDs;
- server-selected authorized snapshot/assertion representations;
- safe edition, standing, applicability, and materiality metadata;
- explicit non-authority instructions; and
- template/limits identity.

The request is rejected before egress if any handle, permission, processor,
extent, or aggregate limit fails.

AI output is a closed object with StandardsIntelligenceResultStatus, zero to 12
suggestions, and bounded advisory text. Each suggestion may contain only a
known input source/assertion/basis handle ID, one safe rationale code, and
bounded explanatory text. Unknown IDs, invented Standards/editions/clauses,
non-input handles, compliance/applicability/approval claims, invalid schema, or
limit excess makes the entire AI output **invalid_output /
INVALID_AI_OUTPUT**. No partial suggestions are accepted.

When AI is prohibited, return **not_permitted / AI_USE_NOT_PERMITTED** without
a provider call. When allowed but unavailable, return **unavailable /
AI_UNAVAILABLE** while returning the deterministic result unchanged.

### 13.3 Retained AI provenance

Every dispatched interaction retains:

- interaction/request ID and Human actor;
- Organization, Project, Report/draft context, purpose, and correlation;
- provider, model, and provider version when available;
- template ID/version/digest;
- processor authorization policy ID, rights binding IDs/versions/digests, and
  decision;
- sorted authorized input-handle digest and aggregate input digest/byte count;
- output digest, validated suggestion-handle digest, and terminal status;
- requested, dispatched, completed/failed times and deadline; and
- explicit advisory/non-authoritative classification.

Protected source text, full protected prompts, licensed excerpts, credentials,
object keys, and unsafe provider diagnostics do not enter Audit/outbox.

## 14. Authorization and protected-not-found contract

Exact product actor classes are:

- **platform_catalog_administrator** for global catalog mutations;
- **organization_standards_administrator** for private catalog and rights
  mutations;
- **project_engineer** for applicability declarations and assertion
  verification;
- **report_author** for Report candidate and basis-revision operations;
- **report_acceptor** for the existing Human acceptance operation; and
- an authenticated active **organization_member** for reads explicitly granted
  by owner policy.

IDS maps these predicates to existing roles without broadening them.

Authorization precedes protected lookup, count, search result formation,
retrieval, display, assertion resolution/use, AI composition, and idempotency
replay. Project configuration and applicability are selectors only.

Internally **NOT_FOUND** and forbidden/wrong-tenant records are distinguished
for safe control flow. Externally every protected absent/forbidden/wrong-tenant
case is **protected_not_found / PROTECTED_NOT_FOUND** with identical body shape,
no target type, no count, no rights/provider hint, no retry disclosure, and
equivalent pagination behavior.

## 15. Exact Audit/outbox inventory

The exact Commercial V1 event names are:

1. **standards.identity.registered**;
2. **standards.edition.registered**;
3. **standards.edition.standing_observed**;
4. **standards.rights.created**;
5. **standards.rights.replaced**;
6. **standards.rights.expired**;
7. **standards.rights.revoked**;
8. **standards.applicability.candidate_recorded**;
9. **standards.applicability.declared**;
10. **standards.applicability.retired**;
11. **standards.source.retrieval_succeeded**;
12. **standards.source.retrieval_unavailable**;
13. **standards.source.snapshot_created**;
14. **standards.assertion.created**;
15. **standards.assertion.human_verified**;
16. **standards.assertion.rejected**;
17. **standards.assertion.stale**;
18. **standards.intelligence.requested**;
19. **standards.intelligence.completed**;
20. **standards.intelligence.unavailable**;
21. **technical_report.standards_basis.attached**; and
22. existing **technical_report.accepted**, extended only with safe basis IDs
    and aggregate digest under its existing owner.

State mutation, Audit, and outbox commit atomically or all roll back. Payloads
contain only event ID/type/version, owner IDs, safe scope IDs, record
IDs/versions/digests, state codes, actor, correlation/causation, and timestamps.
They never contain protected content, license documents, prompts/excerpts,
credentials, object keys, or unsafe diagnostics.

## 16. Failure and response mapping

| Internal condition | Authorized product result | Protected external result |
|---|---|---|
| absent public-safe metadata | **NOT_FOUND** | **NOT_FOUND** |
| absent/forbidden protected record | internal distinction only | **PROTECTED_NOT_FOUND** |
| invalid input after safe authorization | **INVALID_REQUEST** | **INVALID_REQUEST** without protected detail |
| unknown/expired/revoked rights | matching rights code | collapsed to **PROTECTED_NOT_FOUND** for existence-sensitive reads; matching not-permitted code only when actor already knows the binding |
| unavailable protected content | **CONTENT_UNAVAILABLE** | safe **unavailable**, no existence detail beyond already authorized basis |
| edition ambiguous/missing | **EDITION_UNRESOLVED** | safe result only after catalog visibility |
| superseded/withdrawn | matching warning/block code | visible only with authorized edition metadata |
| prohibited AI/display/index | matching code | **not_permitted** only after authorized known resource; otherwise protected-not-found |
| incomplete source/integrity/stale assertion | matching code | safe unavailable/indeterminate without protected bytes |
| version/idempotency conflict | matching conflict code | no winning state or protected digest disclosed |
| limit exceeded | **RESOURCE_LIMIT_EXCEEDED** | invalid/indeterminate as operation defines, no partial data |
| provider unavailable/invalid output | matching AI code | deterministic result retained, no unsafe diagnostic |

Exact HTTP status codes and transport envelopes belong in IDS.

## 17. Concurrency, linearization, retry, and idempotency

- Duplicate identity/edition registration with the same idempotency key and
  request digest returns the same authorized result. A different request or
  normalization collision returns conflict without duplicate creation.
- Rights create/replace/revoke uses expected current version. Exactly one
  concurrent head wins; losers receive **VERSION_CONFLICT** and must reread.
- Protected retrieval/AI dispatch and rights revocation are product-level
  serializable. If revocation linearizes first, no bytes are released. If
  dispatch linearizes first, rights-at-use is recorded; a later revocation
  still prevents display/use of a returned result after a final current check.
- Project applicability changes use expected revision and one effective head.
- Report basis revision requires the expected draft revision. Acceptance locks
  the exact current revision semantically; any concurrent revision or rights/
  applicability/source change causes complete acceptance failure.
- Assertion verification/rejection uses expected assertion/verification
  version; one conflicting decision wins and history is append-only.
- A duplicate standards-intelligence request with the same authorized actor,
  Organization, Project, idempotency key, and request digest returns the same
  terminal interaction. Different digest returns **IDEMPOTENCY_CONFLICT**.
- Authorization always precedes idempotency replay, so a former result cannot
  disclose current protected existence or bytes.
- Retryable transactional conflicts permit at most three fresh attempts. Each
  attempt reauthenticates current versions, rebuilds protected inputs, and
  discards prior attempt state. No AI provider call is transactionally retried.

Exact lock order, SQLSTATE handling, repository mechanics, and database
constraints belong in IDS.

## 18. Exact Commercial V1 resource limits

All Discovery candidate limits are accepted:

| Resource | Exact limit |
|---|---:|
| editions per Standard identity | 64 |
| current non-retired Human applicability declaration heads per Project | 64 |
| standards basis items per Report | 16 |
| all provenance entries per Report | 32 |
| retrieved fragments per request | 8 |
| UTF-8 bytes per fragment | 8 KiB = 8,192 bytes |
| aggregate retrieved or AI standards context | 32 KiB = 32,768 bytes |
| assertions per source snapshot | 32 |
| advisory suggestions per intelligence request | 12 |
| AI provider calls per Human request | 1 |
| AI deadline | 30 seconds |
| automatic AI retries | 0 |
| fresh database attempts for retryable transaction | 3 |
| metadata pagination | default 20, maximum 100 |
| protected candidate pagination | default 20, maximum 20 |

Counts and bytes are enforced before retrieval/egress and again after canonical
composition. Limits never truncate into a false successful material result:
the operation fails with **RESOURCE_LIMIT_EXCEEDED** or returns an explicitly
incomplete deterministic state. Collections have stable ordering and no
unlimited option.

## 19. Exact API operation inventory — 22 operations

Actor abbreviations: **PCA** platform catalog administrator; **OSA**
Organization standards administrator; **PE** Project engineer; **RA** Report
author; **RC** Report acceptor; **OM** authorized Organization member.

| ID | Purpose | Actor / scope | Kind | Protected/material behavior | Idempotency | Main results |
|---|---|---|---|---|---|---|
| CAT-01 | search visible catalog metadata | OM; global plus own Organization | read | authorizes before private filtering/count | no | success, protected_not_found, invalid_request |
| CAT-02 | get identity/edition/standing history | OM; authorized catalog scope | read | no rights posture/content included | no | success, NOT_FOUND or PROTECTED_NOT_FOUND |
| CAT-03 | register Standard identity | PCA global; OSA own Organization | mutate | metadata only; duplicate domain scoped | required | success, CONFLICT, invalid_request |
| CAT-04 | register exact edition | PCA global; OSA own Organization | mutate | parent authorized; immutable | required | success, CONFLICT, EDITION_UNRESOLVED |
| CAT-05 | append standing observation | PCA global; OSA own Organization | mutate | visible only inside catalog scope | required | success, VERSION_CONFLICT, protected_not_found |
| RGT-01 | list current/historical rights bindings | OSA; own Organization/edition/provider | read | authorization before existence/count | no | success, protected_not_found |
| RGT-02 | create or replace rights binding | OSA; own Organization | mutate | explicit capability configuration; expected version | required | success, VERSION_CONFLICT, invalid_request |
| RGT-03 | revoke current rights binding | OSA; own Organization | mutate | immediate serialized denial | required | success, VERSION_CONFLICT, protected_not_found |
| APP-01 | list Project applicability | PE/RA; own authorized Project | read | safe metadata only unless separately rights-authorized | no | success, protected_not_found |
| APP-02 | request deterministic/package candidates | PE/RA; own Project | read | no retrieval; protected counts suppressed | no | success, indeterminate, protected_not_found |
| APP-03 | declare applicable/not applicable/mandatory | PE; own Project | mutate | exact edition; mandatory Human provenance | required | success, VERSION_CONFLICT, EDITION_UNRESOLVED |
| APP-04 | retire and optionally identify successor | PE; own Project | mutate | expected revision; no historical rewrite | required | success, VERSION_CONFLICT, protected_not_found |
| SRC-01 | retrieve bounded source snapshot/handle | PE/RA; own Project and rights tuple | mutate | material/protected; all capabilities checked | required | success, rights code, CONTENT_UNAVAILABLE, SOURCE_INCOMPLETE |
| SRC-02 | display authorized snapshot/excerpt | OM with Project/Report access | read | fresh display rights and integrity every time | no | success, DISPLAY_NOT_PERMITTED or protected_not_found |
| AST-01 | create derived assertion | PE; authorized source | mutate | material source plus retain permission | required | success, STALE_ASSERTION, rights code |
| AST-02 | Human-verify assertion | PE; authorized source/assertion | mutate | display and current-use rights required | required | success, VERSION_CONFLICT, STALE_ASSERTION |
| AST-03 | reject assertion | PE; authorized assertion | mutate | append-only status; no source disclosure | required | success, VERSION_CONFLICT, protected_not_found |
| RPT-01 | list Report standards candidates | RA; exact draft Report/Project | read | deterministic eligibility; safe protected shape | no | success, indeterminate, protected_not_found |
| RPT-02 | attach selected basis handles via new revision | RA; exact draft version | mutate | server composes materiality/provenance | required | success, VERSION_CONFLICT, source/rights failure |
| RPT-03 | standards recheck inside Report acceptance | RC; exact draft version | mutate integration | all-or-nothing final reauthorization | existing acceptance idempotency | accepted, VERSION_CONFLICT, source/rights failure |
| INT-01 | request standards advisory intelligence | RA/PE; own Project/authorized handles | mutate | one rights-gated provider call; deterministic result retained | required | completed status, not_permitted, unavailable, invalid_output |
| INT-02 | get terminal intelligence result | requesting/authorized RA/PE | read | authorization before idempotency/result disclosure | no | success, protected_not_found, unavailable |

There is no generic file browser, arbitrary query, provider passthrough, URL
fetch, scraper, bulk export, or raw protected-text endpoint.

## 20. Frontend contract — exactly six surfaces

All surfaces preserve explicit Human/non-authority language, keyboard access,
visible focus, programmatic labels/status announcements, responsive reflow,
logical CSS properties for RTL, and **dir=ltr** isolation for issuer
designations, edition strings, clause locators, UUIDs, and digests.

| Surface | Exact Commercial V1 behavior |
|---|---|
| 1. Standards Registry metadata search/detail | scope-aware search, identity/edition separation, standing history, safe empty/protected states, no content-right implication |
| 2. Organization rights administration | edition/provider tuple, basis/status/capability matrix, AI processor mode, effective dates, expected-version conflicts, expiry/revocation warning and confirmation |
| 3. Project applicable standards | advisory candidates distinct from Human declarations; exact edition; role/status; mandatory provenance; retire/successor flow |
| 4. Technical Report standards-basis selector | reference-only versus material labels, eligibility/warnings, Human rationale, opaque selections, 16/32 limit feedback, legacy conversion state |
| 5. Standards-aware advisory intelligence | explicit Human request, deterministic result retained, advisory label, known-handle suggestions only, provider unavailable/not-permitted/invalid-output states |
| 6. Protected/unavailable/superseded presentation | masked content, safe historical provenance, rights-at-use versus current access, current/superseded/withdrawn/unknown labels and acknowledgement workflow |

Focus returns to the invoking control after dialogs; conflicts move focus to a
non-destructive reload/review alert; dynamic status is announced through an
appropriate live region without exposing protected text. Tables collapse to
labeled cards without changing semantic order. Color is never the only state
signal. Project/Organization switch or rights loss clears cached protected
content, selections, AI results, and counts before rendering the new scope.

## 21. PATCH-052 package integration and PATCH-053 seam

PATCH-052 hooks produce only the contract in section 8.2. They have no protected
content, mandatory authority, AI, runtime plugin, arbitrary URL/provider
execution, credential, prompt, or executable customer rule. IDS may define an
adapter signature but cannot expand the data or authority.

PATCH-053 integration is one-way and separate:

**authorized retained Finding/Report projection → standards candidate request
→ separately authorized standards context → optional Human Report selection**.

No protected Standard retrieval occurs during PATCH-053 deterministic
evaluation. Standard context never changes deterministic rule execution,
Finding identity/content, rule digest, snapshot/replay, Disposition, or
confirmed Project Change Impact authority.

## 22. Externally testable security contract

| Threat | Required product evidence |
|---|---|
| tenant leakage | wrong-Organization IDs, counts, searches, histories, idempotency keys, and timing return protected-equivalent results |
| forged handle/edition/source | only opaque server-minted handles resolve; raw/mismatched identity, edition, location, provider, digest, or Organization is rejected |
| stale rights | every protected use binds a fresh current rights version/digest; uncertain freshness denies |
| revocation | serialized revocation prevents later dispatch/retrieval/display/use; in-flight result is rechecked before release |
| AI egress bypass | no raw-text/provider path; exact processor policy and aggregate byte check occur before dispatch |
| prompt injection | source is delimited data, tools/credentials absent, output closed and handle-subset validated |
| malicious customer source | declared possession grants no right; content is quarantined/validated, bounded, non-executable, and cannot supply canonical metadata without owner validation |
| Audit leakage | Audit/outbox/log/metric/trace fixtures contain IDs/digests/states only and pass forbidden-field scans |
| idempotency isolation | authorization precedes key lookup; keys are bound to actor/Organization/Project/operation/request digest |
| database privilege bypass | runtime role cannot mutate immutable history, bypass tenant coherence, or write protected records outside owner operations; PostgreSQL evidence required |

Exact database triggers, grants, row constraints, lock order, encryption, and
adapter mechanics belong in IDS.

## 23. Migration lifecycle expectations

Two sequential additive migrations are required after accepted IDS and explicit
migration authority:

1. **Migration 1 — standards foundation:** identity, edition, standing, rights,
   applicability, source snapshot/handle, assertion, intelligence, Audit/outbox,
   and idempotency persistence with tenant, history, and privilege enforcement.
2. **Migration 2 — Technical Report integration:** canonical standards basis,
   accepted-snapshot immutability/security finalization, legacy read
   compatibility, new-legacy-write rejection, and acceptance guards.

Fresh install and upgrade must produce the same product contract. Existing
accepted legacy Report snapshots remain byte-for-byte unchanged. Existing
drafts expose **legacy_conversion_required**. No backfill invents identity,
edition, rights, snapshot, materiality, applicability, assertion, or AI
provenance. Recovery/downgrade must not silently discard retained standards or
accepted Report history. This EDS reserves no migration ID and specifies no SQL.

## 24. Exact 96-vector conformance contract

Every vector below is a future deterministic acceptance obligation. **PG**
means real PostgreSQL evidence is required. No vector is currently claimed
PASS.

### 24.1 Identity and edition — 8 vectors

| Stable ID | Scenario | Precondition | Operation | Expected result | Invariant proven |
|---|---|---|---|---|---|
| P054-ID-01 | global identity registration | PCA; attributable metadata; no normalized match | CAT-03 register | one immutable global identity and event | global owner, normalization, atomic creation |
| P054-ID-02 | private duplicate isolation | same normalized designation exists only in Organization A | OSA B registers private identity | success in B; neither side disclosed | tenant-scoped duplicate domain |
| P054-ID-03 | identity duplicate collision | authorized scope already has normalized key with different request | CAT-03 register spelling variant | CONFLICT; no second identity | exact NFKC/casefold duplicate rule |
| P054-ID-04 | exact edition registration | identity exists; 63 editions; unique edition key | CAT-04 register | immutable edition 64 created; identity unchanged | identity/edition separation and bound |
| P054-ID-05 | edition limit | identity already has 64 editions | CAT-04 register another | RESOURCE_LIMIT_EXCEEDED; no row/event | finite edition collection |
| P054-ID-06 | duplicate/ambiguous edition | normalized edition key reused without disambiguator | CAT-04 register | EDITION_UNRESOLVED or CONFLICT; no creation | exact publication-unit identity |
| P054-ID-07 | standing append | edition standing current at observation V1 | CAT-05 append superseded V2 | V1 immutable; V2 current head and event | temporal standing, no edition mutation |
| P054-ID-08 | historical exact retrieval | edition has later successor and standing observation | CAT-02 fetch historical handles | exact old identity/edition/observation returned | no latest-edition substitution |

### 24.2 Rights matrix — 12 vectors

| Stable ID | Scenario | Precondition | Operation | Expected result | Invariant proven |
|---|---|---|---|---|---|
| P054-RGT-01 | metadata-only active | active metadata_only binding | request each protected capability | all denied; safe metadata only | metadata never implies content rights |
| P054-RGT-02 | customer-supplied defaults | active customer_supplied_declared with no capability enabled | retrieve/display/index/derive/AI | denied; AI prohibited | possession/declaration grants nothing automatically |
| P054-RGT-03 | licensed independent grants | organization_license enables retrieval/display but not storage/index/derive/AI | exercise all capabilities | only retrieval/display succeed | capabilities are independent |
| P054-RGT-04 | open-distribution defaults | active open_distribution with unconfigured capabilities | protected retrieval and AI | denied | legal permission is not invented |
| P054-RGT-05 | internally authored configuration | active internally_authored enables storage/index/derive, AI local_only | storage/index/derive/local AI | configured operations only succeed | explicit policy drives rights |
| P054-RGT-06 | unknown basis | status active, basis unknown | protected operation | RIGHTS_UNKNOWN; no bytes/result | unknown basis fails closed |
| P054-RGT-07 | expired status | formerly active binding is past effective-until | retrieve/display/index/AI | RIGHTS_EXPIRED; safe history retained | expiry denies current use |
| P054-RGT-08 | revoked status | binding revoked before operation | retrieve/display/index/AI | RIGHTS_REVOKED; safe history retained | revocation denies current use |
| P054-RGT-09 | unknown status | otherwise configured binding has unknown status | protected operation | RIGHTS_UNKNOWN | unknown status fails closed |
| P054-RGT-10 | AI mode matrix | three active fixtures: prohibited, local_only, approved_processor | dispatch local and external processors | only exact permitted mode/processor dispatches | three-state AI permission |
| P054-RGT-11 | provider-bound permission | edition licensed for provider A only | resolve provider B handle | protected_not_found/not permitted; no B call | binding tuple includes exact provider |
| P054-RGT-12 | derived retain/use split | binding permits retention but denies current use | create then use retained assertion | retention succeeds; current reasoning denied | derived retention differs from current use |

### 24.3 Organization isolation and ACL — 10 vectors

| Stable ID | Scenario | Precondition | Operation | Expected result | Invariant proven |
|---|---|---|---|---|---|
| P054-AUTH-01 | private catalog search leakage | private identity exists in Organization A | Organization B searches exact designation | same empty/protected shape and count as absent | private existence nondisclosure |
| P054-AUTH-02 | private edition direct lookup | B knows A edition UUID | CAT-02 direct lookup | PROTECTED_NOT_FOUND | authorization before lookup |
| P054-AUTH-03 | rights count leakage | A has rights history; B knows edition | RGT-01 list/count | PROTECTED_NOT_FOUND; no count/page hint | protected count nondisclosure |
| P054-AUTH-04 | forged source handle | B submits A snapshot UUID | SRC-02 display | PROTECTED_NOT_FOUND; no bytes/metadata | tenant-bound source handles |
| P054-AUTH-05 | forged assertion handle | B submits A assertion UUID | AST read/use path | PROTECTED_NOT_FOUND | tenant-bound derived knowledge |
| P054-AUTH-06 | Report candidate leakage | B Report requests A protected candidate | RPT-01 candidates | candidate absent with no hidden count | owner intersection before candidate formation |
| P054-AUTH-07 | idempotency cross-tenant replay | B reuses A key/request digest | protected mutating operation | PROTECTED_NOT_FOUND; no replay result | authorize before idempotency lookup |
| P054-AUTH-08 | authorization ordering | unauthorized actor sends malformed protected UUID/payload | protected operation | protected-equivalent response, not validator oracle | authorization precedes protected validation |
| P054-AUTH-09 | configuration as false authority | Project config names edition without rights/access | retrieve or AI request | denied | Project configuration cannot grant data authority |
| P054-AUTH-10 | PG runtime privilege bypass | runtime DB role and cross-tenant/immutable target fixtures | direct unauthorized insert/update/delete | PostgreSQL rejects; history unchanged | DB privilege and tenant/immutability defense |

### 24.4 Project applicability — 8 vectors

| Stable ID | Scenario | Precondition | Operation | Expected result | Invariant proven |
|---|---|---|---|---|---|
| P054-APP-01 | package candidate | valid PATCH-052 descriptor/config/hook | APP-02 request candidates | bounded candidate with exact package provenance | package output is advisory only |
| P054-APP-02 | declare applicable | exact edition; PE; current expected revision | APP-03 design_basis declaration | append declared_applicable head and event | Human Project authority |
| P054-APP-03 | declare not applicable | advisory candidate exists | APP-03 declared_not_applicable | append decision; candidate/history preserved | candidate cannot override Human |
| P054-APP-04 | valid mandatory declaration | PE supplies allowed source kind/reference/digest/rationale | APP-03 mandatory | success with exact Human provenance | mandatory is attributable Human-only |
| P054-APP-05 | invalid mandatory inference | AI/package or Human missing mandatory source | APP-03 mandatory attempt | INVALID_REQUEST; no declaration/event | no inferred mandatory applicability |
| P054-APP-06 | unresolved edition | designation/family only, no exact edition | APP-03 declaration | EDITION_UNRESOLVED | applicability pins exact edition |
| P054-APP-07 | retire/successor | current declaration V2 exists | APP-04 retire then declare successor | append history; V2 unchanged; one new head | append-only applicability lineage |
| P054-APP-08 | concurrent declarations | two commands share expected revision | execute concurrently | exactly one succeeds; loser VERSION_CONFLICT | single effective head and optimistic authority |

### 24.5 Retrieval and content safety — 10 vectors

| Stable ID | Scenario | Precondition | Operation | Expected result | Invariant proven |
|---|---|---|---|---|---|
| P054-RET-01 | material snapshot success | exact edition; active retrieval/storage rights; available bounded source | SRC-01 retrieve material | immutable snapshot with extent/digests/rights-at-use | complete material provenance |
| P054-RET-02 | metadata reference | metadata visible; no protected rights | request reference_only | safe bibliographic handle; no text/material claim | reference-only boundary |
| P054-RET-03 | arbitrary URL | authorized user supplies unregistered URL | SRC-01 request | INVALID_REQUEST; no network/provider call | no arbitrary fetch/browser/scrape |
| P054-RET-04 | fragment aggregate bound | 9 fragments or more than 32 KiB requested | SRC-01 retrieve | RESOURCE_LIMIT_EXCEEDED; no partial success | finite pre-retrieval bounds |
| P054-RET-05 | immutable provider handle | allowlisted provider returns version token and digest | SRC-01 handle-backed retrieval | material handle attestation succeeds | provider-backed immutability |
| P054-RET-06 | nonimmutable provider handle | provider cannot prove exact stable version and no stored snapshot | request material_support | SOURCE_INCOMPLETE; may only become reference_only by new Human request | no false material support |
| P054-RET-07 | integrity mismatch | retrieved bytes differ from expected immutable digest | SRC-01/SRC-02 | INTEGRITY_FAILURE; no display/assertion/AI | content integrity fail closed |
| P054-RET-08 | display reauthorization | historical snapshot exists; current display permission absent | SRC-02 display | masked DISPLAY_NOT_PERMITTED; safe provenance only | historical basis not current access |
| P054-RET-09 | revocation race | retrieval and revocation target same rights version | concurrent operations | serialized result; no bytes after revocation wins | immediate revocation and final check |
| P054-RET-10 | incomplete source | clause/location or content digest absent for material request | SRC-01 or Report candidate formation | SOURCE_INCOMPLETE; zero partial material candidates | material completeness |

### 24.6 Assertions and Human verification — 8 vectors

| Stable ID | Scenario | Precondition | Operation | Expected result | Invariant proven |
|---|---|---|---|---|---|
| P054-AST-01 | four-kind creation | authorized material snapshot and retain permission | AST-01 once per closed kind | four valid bounded unverified assertions; fifth kind rejected | smallest closed taxonomy |
| P054-AST-02 | Human verification | unverified assertion; source/display/current-use authorized | AST-02 with exact digest/rationale | append human_verified state and actor | faithful-extraction Human boundary |
| P054-AST-03 | verification non-authority | human_verified assertion exists | request compliance/applicability/approval projection | no authority result; invalid request/advisory only | verification is not engineering authority |
| P054-AST-04 | AI-assisted origin | authorized AI extraction creates assertion | AST-01 | origin ai_assisted, status unverified | AI cannot self-verify |
| P054-AST-05 | rejection | current unverified/verified assertion and PE | AST-03 reject with expected version | append rejected; prior state immutable | rejection history |
| P054-AST-06 | rights loss without retained use | source rights revoked; no new derived-use permission | current assertion use | STALE_ASSERTION/masked; accepted Reports unchanged | current-use denial after rights loss |
| P054-AST-07 | retained derived use | newer active binding explicitly permits retain and current use | reevaluate unchanged human_verified assertion | eligible after fresh integrity/rights evaluation | lawful retained knowledge path |
| P054-AST-08 | source integrity loss | provider handle no longer verifies same digest | use/verify assertion | append/evaluate stale; no current material use | source-bound assertion integrity |

### 24.7 Technical Report lifecycle and history — 12 vectors

| Stable ID | Scenario | Precondition | Operation | Expected result | Invariant proven |
|---|---|---|---|---|---|
| P054-RPT-01 | deterministic candidates | current draft and mixed eligible/ineligible sources | RPT-01 | stable safe ordered candidates; no protected hidden count | deterministic-first candidate contract |
| P054-RPT-02 | opaque basis attachment | RA selects authorized reference/material handles | RPT-02 with expected Report revision | new revision with server-composed bases | clients cannot mint provenance |
| P054-RPT-03 | raw/legacy submission rejection | post-cutover request contains raw locator/text | RPT-02 | LEGACY_STANDARD_LOCATOR_PROHIBITED/INVALID_REQUEST | new legacy/manual provenance closed |
| P054-RPT-04 | accepted legacy read | pre-cutover accepted snapshot has StandardLocator | read Report | byte-identical legacy_unattested_reference display | historical legacy immutability |
| P054-RPT-05 | legacy draft conversion | pre-cutover draft has locator | revise or accept without replacement | legacy_conversion_required; no acceptance | safe cutover without backfill |
| P054-RPT-06 | acceptance success | exact current revision; all 13 rechecks pass | RPT-03 accept | one atomic accepted snapshot and safe events | ADR-023 Human acceptance boundary |
| P054-RPT-07 | material invalid before acceptance | selected material rights/source/assertion becomes invalid | RPT-03 accept | whole acceptance fails; draft/history unchanged | no partial accepted Report |
| P054-RPT-08 | Report revision race | revision and acceptance share expected version | execute concurrently | exactly one wins; loser VERSION_CONFLICT | exact-version acceptance |
| P054-RPT-09 | rights/applicability race | binding/applicability changes during final recheck | RPT-03 | conflict/fail closed; no accepted snapshot | current authority at acceptance |
| P054-RPT-10 | superseded/withdrawn reliance | material edition noncurrent | attach/accept without then with exact acknowledgement | first blocked; second allowed only with applicability and Human rationale | explicit noncurrent standing behavior |
| P054-RPT-11 | historical current-rights loss | accepted basis was lawful; current display revoked | read accepted Report/excerpt | meaning/provenance intact; excerpt masked | historical basis/current access duality |
| P054-RPT-12 | successor from legacy Report | accepted predecessor contains legacy locator | create successor revision | locator not copied as new provenance; new canonical selection required | no silent legacy upgrade |

### 24.8 AI boundary — 8 vectors

| Stable ID | Scenario | Precondition | Operation | Expected result | Invariant proven |
|---|---|---|---|---|---|
| P054-AI-01 | AI prohibited | selected binding mode prohibited | INT-01 request | not_permitted; provider call count zero | rights before egress |
| P054-AI-02 | local-only restriction | mode local_only; external provider selected | INT-01 request | AI_USE_NOT_PERMITTED; zero external calls | local-only means no external egress |
| P054-AI-03 | approved processor | exact processor policy permits selected provider/model | INT-01 request | one bounded call and validated advisory result | processor-specific authorization |
| P054-AI-04 | provider failure/no retry | deterministic candidates exist; provider times out | INT-01 | unavailable; exactly one call; deterministic result unchanged | one call, zero retry, AI optional |
| P054-AI-05 | input authorization/bounds | one handle unauthorized or context above 32 KiB | INT-01 | rejected before provider call | server-selected bounded input only |
| P054-AI-06 | invented output handle/clause | provider returns unknown ID or invented reference | validate output | entire result invalid_output; no suggestion accepted | closed handle-subset output |
| P054-AI-07 | authority-claim output | provider asserts compliance/mandatory/approval/acceptance | validate output | entire result invalid_output; no suggestion or authority state accepted | AI non-authority |
| P054-AI-08 | prompt-injection source | authorized fragment contains tool/secret/retrieval instructions | INT-01 | treated as data; no tool/secret/use; known-handle advisory only | prompt-injection containment |

### 24.9 Audit and outbox — 6 vectors

| Stable ID | Scenario | Precondition | Operation | Expected result | Invariant proven |
|---|---|---|---|---|---|
| P054-AUD-01 | identity/edition/standing events | successful CAT-03/04/05 | inspect committed event stream | exact event names, IDs/versions/digests; atomic ordering | catalog accountability |
| P054-AUD-02 | rights lifecycle events | create, replace, expire, revoke fixtures | inspect stream and rollback fault | exact four lifecycle families; mutation rolls back if event fails | rights history and atomicity |
| P054-AUD-03 | retrieval payload minimization | protected snapshot succeeds and unavailable fixture fails | inspect Audit/outbox/log fixture | exact retrieval/snapshot events; no text/key/unsafe diagnostic | copyright-safe observability |
| P054-AUD-04 | applicability/assertion events | candidate/declaration/retirement and assertion transitions | inspect stream | exact declared transitions and actor/digests | Human authority attribution |
| P054-AUD-05 | AI provenance events | permitted, prohibited, unavailable interactions | inspect events/interaction | requested plus correct terminal event; safe provider/digests only | AI decision reproducibility without content leak |
| P054-AUD-06 | Report integration | basis attached then Report accepted | inspect owner events | attachment event plus existing acceptance safe basis digest; no protected bytes | cross-owner historical accountability |

### 24.10 API, UI, accessibility, and RTL — 6 vectors

| Stable ID | Scenario | Precondition | Operation | Expected result | Invariant proven |
|---|---|---|---|---|---|
| P054-UX-01 | exact API inventory | contract fixture enumerates operations | compare exposed standards operations | exactly 22; no browser/scraper/raw-text/bulk endpoint | minimum bounded API surface |
| P054-UX-02 | registry and rights UI | global/private/active/expired fixtures | keyboard/search/detail/admin flows | correct scope/status/capabilities; focus and labels accessible | safe metadata and rights administration |
| P054-UX-03 | applicability and Report UI | candidate/mandatory/reference/material/legacy fixtures | keyboard declaration and basis selection | Human authority/materiality/cutover states explicit | no advisory/material authority confusion |
| P054-UX-04 | AI and protected state UI | prohibited/unavailable/invalid/masked fixtures | request/open/switch scope | deterministic result retained; no stale content/count | AI optionality and scope clearing |
| P054-UX-05 | accessibility semantics | all six surfaces and conflict/dialog/live updates | automated plus keyboard/screen-reader test | visible focus, names, status announcements, logical order | WCAG-oriented operability |
| P054-UX-06 | responsive RTL/LTR isolation | narrow viewport and RTL locale with identifiers | render/interact all surfaces | logical layout mirrors; identifiers/UUIDs remain LTR; no clipping | RTL and responsive product contract |

### 24.11 Resource limits — 4 vectors

| Stable ID | Scenario | Precondition | Operation | Expected result | Invariant proven |
|---|---|---|---|---|---|
| P054-LIM-01 | registry/applicability ceilings | fixtures at 64 editions and 64 active declaration heads | add one to each | both reject at 65; existing state unchanged | bounded registry/Project collections |
| P054-LIM-02 | Report/retrieval ceilings | 16 bases/32 provenance/8 fragments at limit and plus-one fixtures | attach/retrieve | at-limit succeeds; plus-one fails without truncation | bounded Report and retrieval sets |
| P054-LIM-03 | byte/assertion/suggestion ceilings | 8,192-byte fragment, 32,768 aggregate, 32 assertions, 12 suggestions and plus-one fixtures | retrieve/create/intelligence | exact limits accepted; plus-one rejected before unsafe use | aggregate and per-item bounds |
| P054-LIM-04 | call/time/retry/pagination ceilings | provider, retryable DB, metadata/protected listing fixtures | invoke boundary cases | 1 call/30 s/0 AI retry/3 DB attempts/20–100 pages enforced | finite execution and disclosure bounds |

### 24.12 Migration, concurrency, and idempotency — 4 vectors

| Stable ID | Scenario | Precondition | Operation | Expected result | Invariant proven |
|---|---|---|---|---|---|
| P054-DB-01 | PG Migration 1 lifecycle | empty and pre-PATCH-054 PostgreSQL databases | fresh install and upgrade through foundation migration | equivalent valid foundation; constraints/roles/events verified; no invented records | additive recoverable standards foundation |
| P054-DB-02 | PG Migration 2 legacy/immutability | legacy accepted Report and legacy draft fixtures | upgrade, read, attempt new locator write/update accepted bytes | accepted bytes unchanged/readable; draft conversion visible; new write/update rejected | legacy cutover and accepted immutability |
| P054-DB-03 | PG concurrency matrix | paired commands for rights, retrieval/revocation, applicability, assertion, Report revision/acceptance | execute real concurrent transactions | one serializable winner or safe conflict per section 17; no partial state/event | race-safe authority boundaries |
| P054-DB-04 | PG idempotency and bounded retry | same/different digest and transient-conflict fixtures | repeat/replay across actor/tenant and force retries | same authorized result once; mismatch conflict; cross-tenant hidden; max three fresh attempts; no AI retry | idempotency isolation and bounded transactions |

The authoritative total is **96**:

**8 identity/edition + 12 rights + 10 Organization isolation/ACL + 8 Project
applicability + 10 retrieval/content safety + 8 assertions + 12 Report
lifecycle/history + 8 AI + 6 Audit/outbox + 6 API/UI/accessibility/RTL + 4
resource limits + 4 migration/concurrency/idempotency = 96**.

No vector may be removed, merged, replaced by a count-only assertion, or marked
PASS without its stated precondition, operation, exact result, persistence/
event effects, authority checks, and required real PostgreSQL evidence.

## 25. Five implementation batches and vector ownership

This allocation is dependency ownership, not an implementation plan or file
manifest:

| Batch | Exact EDS capability ownership | Primary conformance ownership |
|---|---|---|
| 1 — identity/edition registry and rights foundation | §§3–7, shared authorization/reliability foundation | ID-01..08, RGT-01..12, AUTH-01..10, AUD-01..02, DB-01 = 33 |
| 2 — authorized retrieval and assertions | §§9–10, retrieval/assertion reliability | RET-01..10, AST-01..08, AUD-03 = 19 |
| 3 — Project applicability and package hooks | §8 and package portion of §21 | APP-01..08, AUD-04 = 9 |
| 4 — Technical Report integration and historical compatibility | §§11–12, Report portion of §21, Migration 2 contract | RPT-01..12, AUD-06, DB-02..03 = 15 |
| 5 — AI, frontend, cumulative security/performance | §§13,18–20,22 plus cumulative release proof | AI-01..08, UX-01..06, LIM-01..04, AUD-05, DB-04 = 20 |

The primary counts total exactly 96. Every batch reruns all previously owned
vectors and applicable existing regression. No batch starts without later
Human-accepted IDS, implementation plan, exact authorized manifest, and
implementation authority.

## 26. Commercial V1 exclusions

Explicitly excluded are:

- a whole-standard repository, bulk export, mirroring, or distribution;
- a standards marketplace, purchasing, procurement, or license negotiation;
- arbitrary standards scraping, URL fetching, or provider passthrough;
- a general EDMS or document browser;
- autonomous compliance certification, applicability determination, approval,
  Report acceptance, or publication/distribution governance;
- PATCH-055 Evidence Workbench;
- PATCH-056 Methods & Systems;
- PATCH-057 Command Center;
- PATCH-058 release/security completion;
- PATCH-059 commercial licensing, seats, or entitlements;
- PATCH-060 deployment qualification;
- runtime plugins or customer executable standards rules;
- autonomous AI loops/tools/retrieval; and
- any modification to PATCH-053 deterministic rules, digests, Findings,
  replay, Dispositions, or confirmed-impact authority.

## 27. Policy retained as configurable and fail closed

This EDS does not select or invent:

- commercially supported standards issuers or source providers;
- license terms or legal interpretations;
- an approved external AI provider/processor;
- customer-specific agreements or declarations;
- long-term deletion/retention beyond immutable PATCH-054 historical needs; or
- future enterprise standards-administration separation of duties.

Those choices populate the exact rights/provider/retention mechanisms defined
here. Missing policy produces denial, never implicit permission.

## 28. Traceability and downstream IDS obligations

| ADR-027 boundary | EDS contract |
|---|---|
| identity/edition/catalog | §§4–6 |
| rights/capabilities/revocation | §§7,10.3,17 |
| Project applicability/package candidates | §8 |
| retrieval/materiality/source snapshot | §9 |
| assertions | §10 |
| Technical Report/legacy/history/current access | §§11–12 |
| deterministic intelligence/AI/provenance | §§12–13 |
| authorization/Audit/failure/security | §§14–17,22 |
| limits/API/frontend | §§18–20 |
| PATCH-052/053 compatibility | §21 |
| migrations/conformance/batches | §§23–25 |
| exclusions/policy | §§26–27 |

IDS-054 must map these exact contracts to repository modules, ports, data
structures, database constraints/indexes/roles, provider/object-storage
adapters, API transports, frontend files, test fixtures, migration revisions,
lock order, and batch manifests without changing vocabulary, owner authority,
machine semantics, resource limits, operation count, event inventory,
conformance count/allocation, or roadmap scope.

## 29. Unresolved design questions and next gate

**Unresolved EDS design questions: NONE.**

Physical names, SQL types, DDL, indexes, triggers, runtime grants, lock order,
cache invalidation mechanics, encryption/key management, route paths, concrete
module/file layout, migration revision IDs, fixture implementation, and exact
batch file manifests belong to IDS/implementation planning. They may not reopen
this EDS or ADR-027.

The next gate is Human EDS-054 acceptance or rejection. Acceptance alone does
not authorize IDS, an implementation plan, code/tests/frontend changes,
migrations, database operations, staging, commit, or push.

## 30. EDS self-review

### 30.1 Review control

The completed candidate was reviewed afresh against the Human-accepted
PATCH-054 Discovery and ADR-027, ADR-023, ADR-024/025/026, closed
PATCH-051/052/053 boundaries, the frozen Commercial V1 roadmap, Human
engineering authority, AI non-authority, copyright/rights safety, Organization
isolation, historical reproducibility, accepted Report immutability, and
PATCH-055+ non-leakage.

One EDS-authority **Minor** reconciliation was applied during self-review: the
AI authority-claim conformance vector initially admitted two possible output
treatments. It now freezes one fail-closed result, **invalid_output**, consistent
with section 13.2. The finding is closed in the final candidate; this correction
changed no ADR-027 decision or downstream scope.

### 30.2 Challenge results

| Challenge | Result |
|---|---|
| incomplete/overbroad vocabulary | PASS — §4 freezes the smallest complete closed V1 sets; four assertion kinds create no general knowledge graph |
| identity and edition collapse | PASS — §5 freezes separate immutable contracts, normalization, duplicates, correction lineage, and historical retrieval |
| rights basis invents legal permission | PASS — §7 defaults every protected capability to deny until explicit policy and denies every unknown/nonactive state |
| provider or Project scope grants rights | PASS — exact Organization/edition/provider tuple; Project/configuration/applicability never grants access |
| metadata masquerades as material | PASS — §9 requires immutable content provenance for material support and explicit reference-only semantics everywhere |
| current rights rewrite history | PASS — §§10–12 preserve accepted safe basis while reauthorizing all current protected access |
| assertion becomes engineering authority | PASS — closed kinds, Human faithful-extraction meaning, non-authority, rights eligibility, staleness, and rejection are exact |
| legacy StandardLocator remains a write bypass | PASS — historical reads remain immutable; every new/revised/accepted path requires conversion or rejection |
| Report acceptance is partial or stale | PASS — §11.3 defines 13 all-or-nothing current checks with exact revision and authority |
| noncurrent edition silently relied upon | PASS — superseded/withdrawn material use requires exact applicability plus Human acknowledgement; unknown blocks |
| AI egress or authority creep | PASS — one call, no retries/tools/retrieval, exact processor rights, bounded handles, closed output, no compliance/applicability/approval |
| prompt injection | PASS — standards text is untrusted data, no credentials/tools, closed schema and input-handle subset validation |
| protected existence/count/idempotency leak | PASS — §14 authorizes first and collapses protected absence across response and pagination behavior |
| vague Audit/failure/concurrency contract | PASS — §§15–17 freeze 22 events, exact codes/disclosure, linearization, expected versions, and bounded fresh retries |
| missing finite limits/API/UI | PASS — §18 freezes every requested limit; §§19–20 freeze exactly 22 operations and six accessible RTL surfaces |
| fake/count-only conformance | PASS — §24 contains exactly 96 stable scenario/precondition/operation/result/invariant vectors with PG evidence |
| migration or implementation leakage | PASS — §§23,25,28 state lifecycle/ownership only and reserve no IDs, SQL, paths, or manifests |
| PATCH-051/052/053 regression | PASS — §21 preserves package and deterministic assessment owners and prohibits protected retrieval during PATCH-053 evaluation |
| PATCH-055+ scope creep | PASS — §26 expressly excludes PATCH-055 through PATCH-060 and all adjacent future capability |

### 30.3 Findings and verdict

Critical: **0**

Major: **0**

Minor: **0**

Observation: **0**

Blocking findings: **none**

Self-review verdict:

**PASS / ACCEPTED-CANDIDATE / READY FOR HUMAN EDS ACCEPTANCE**

This verdict does not constitute Human EDS acceptance.

## 31. Governance disposition

- ADR-027: **HUMAN ACCEPTED / AUTHORITATIVE**.
- EDS-054: **PASS / COMPLETE / AWAITING HUMAN EDS ACCEPTANCE**.
- EDS self-review: **PASS**, final **0/0/0/0**.
- IDS-054 / Implementation Plan-054: **NOT STARTED / NOT AUTHORIZED**.
- Production / tests / frontend / migrations / database / Git delivery:
  **NOT AUTHORIZED / NONE**.
- PATCH-055+: **NOT STARTED / NOT AUTHORIZED**.

The exact next Human decision is EDS-054 acceptance or rejection. No downstream
authority is implied.

## Status reconciliation — 2026-09-14

Human EDS acceptance is **PASS / ACCEPTED / AUTHORITATIVE**. The stale candidate/status table above is retained as historical pre-acceptance metadata and is superseded by this append-only reconciliation. No EDS semantics are changed.
