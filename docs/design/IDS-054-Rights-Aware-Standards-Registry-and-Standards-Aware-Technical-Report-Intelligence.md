# IDS-054 — Rights-Aware Standards Registry and Standards-Aware Technical Report Intelligence

Status: DRAFT — GOVERNED IMPLEMENTATION DESIGN COMPLETE; HUMAN ACCEPTANCE REQUIRED
Patch: PATCH-054
Date: 2026-09-12
Authority: HUMAN-ACCEPTED PATCH-054 Discovery, ADR-027, and EDS-054
Scope: implementation design and independent IDS review only

## 1. Purpose and authority

This IDS freezes the implementation contracts for PATCH-054. It translates the accepted Discovery, ADR-027, and EDS-054 into repository-specific types, persistence, transactions, routes, UI seams, migrations, evidence, and an exact implementation manifest. It does not implement the feature, allocate Alembic revision identifiers, create an Implementation Plan, or authorize PATCH-055 or later work.

Authoritative inputs:

- PATCH-054 Discovery: HUMAN ACCEPTED.
- ADR-027 — Rights-Aware Standards Registry and Standards-Aware Technical Report Intelligence: HUMAN ACCEPTED and authoritative.
- EDS-054 — Rights-Aware Standards Registry and Standards-Aware Technical Report Intelligence: HUMAN ACCEPTED and authoritative.
- Existing Technical Report authority and accepted PATCH-053 implementation are preserved.

Precedence is Discovery → ADR-027 → EDS-054 → this IDS. This IDS resolves implementation detail only. No contradiction requiring an ADR or EDS change was found.

## 2. Recovery and repository baseline

The interrupted session ended because the Codex usage limit was reached. Recovery inspection found no partially created or modified IDS-054 artifact. The Git index is empty. HEAD remains c3dc7bf9a32e43c1edfbc51ca4d49ad146b64c60 (PATCH-053: close assessment orchestration remediation). No production code, tests, migrations, frontend production code, staging, commits, or pushes were performed by the interrupted IDS task. All unrelated dirty and untracked work is outside this IDS and is preserved.

The verified Alembic head is e05300000002. Consistent with repository IDS practice, this IDS does not allocate revision IDs.

## 3. Reused repository seams

The implementation MUST reuse these real seams rather than create parallel foundations:

| Concern | Repository seam | Required reuse |
|---|---|---|
| authenticated tenant | backend/app/dependencies/auth.py: AuthenticatedOrganizationContext and get_current_user_organization_context | active user, active organization, exactly one selected enabled membership |
| roles | backend/app/permissions/roles.py: Role | existing admin and engineer roles only |
| project/workspace ownership | backend/app/models/project.py; backend/app/models/engineering_workspace.py | organization-scoped project, owner, assignee, and workspace membership predicates |
| report aggregate | backend/app/models/technical_report.py; backend/app/models/technical_report_command.py | existing root/revision/acceptance/provenance model |
| report UoW | backend/app/repositories/technical_report_unit_of_work.py | lock ordering, authorization, idempotency, audit/outbox staging, final recheck |
| report repository/service/API | backend/app/repositories/technical_report_repository.py; backend/app/services/technical_report_service.py; backend/app/api/v1/routers/technical_reports.py | extend in place; no second report authority |
| audit | backend/app/models/audit_log.py; backend/app/services/audit_service.py | shared append-only audit_logs table and metadata-only payloads |
| private objects | backend/app/ports/supporting_file.py; backend/app/adapters/supporting_file_object_store.py | exact-key private object operations and receipts; no listing or public URL |
| AI safety | backend/app/ai/engineering_guidance.py; backend/app/ports/engineering_guidance.py; backend/app/ai/technical_report_assistant.py | versioned prompt envelope, strict schema, bounded I/O, provider-neutral port, and existing Report assistant integration |
| opaque signing | backend/app/dependencies/cross_discipline_intelligence.py | canonical payload, domain-separated HMAC-SHA256, constant-time verification |
| package hooks | backend/app/discipline_packages/contributions.py; backend/app/discipline_packages/descriptors/eic_v1.py | StandardsApplicabilityHookV1 and static descriptor registration |
| PATCH-053 projection | backend/app/models/cross_discipline_intelligence.py and its repository/service | read-only, bounded standards projection; no ownership transfer |
| frontend API state | frontend/src/api/client.ts; frontend/src/api/types.ts | centralized ApiResult and protected-not-found behavior |
| frontend composition | frontend/src/App.tsx; frontend/src/components/AppShell.tsx; existing pages and panels | existing routing, navigation, state, accessibility, and RTL patterns |

Shared AuditLog is reused. Standards receives capability-owned standards_idempotency and standards_outbox tables because the repository has no shared authoritative idempotency/outbox table and existing capabilities own their respective tables.

## 4. Exact enum and value-object contracts

All behavior-vocabulary values are the exact lowercase strings below; failure/reason codes are the exact uppercase strings below. They persist in VARCHAR columns with explicit CHECK constraints. PostgreSQL native enum types MUST NOT be used. Python definitions live in backend/app/enums/standards.py as str, Enum values and Pydantic schemas reject unknown values.

Machine tokens match [a-z][a-z0-9]*(?:[._-][a-z0-9]+)*. Human prose is Unicode NFC; timestamps are aware UTC serialized with microseconds and Z; digests are lowercase 64-character SHA-256 hexadecimal. standards.canonical_json.v1 is UTF-8 JSON with NFC strings, lexically sorted object keys, no insignificant whitespace, lowercase JSON literals, semantically ordered arrays, no duplicate/unknown keys, and no binary floating point. A record digest is SHA-256(domain token + one zero byte + canonical JSON excluding its digest). Unknown is an explicit enum value, never an accidental NULL.

| Type | Exact values |
|---|---|
| CatalogScope | global_trusted, organization_private |
| StandardStanding | current, superseded, withdrawn, unknown |
| RightsBasis | metadata_only, customer_supplied_declared, organization_license, open_distribution, internally_authored, unknown |
| RightsStatus | active, expired, revoked, unknown |
| AIProcessingPermission | prohibited, local_only, approved_processor |
| ProjectApplicabilityStatus | candidate_advisory, declared_applicable, declared_not_applicable, retired |
| ProjectApplicabilityRole | informative, design_basis, mandatory |
| AssertionOrigin | human, deterministic, ai_assisted |
| AssertionVerificationStatus | unverified, human_verified, rejected, stale |
| AssertionKind | requirement_statement, defined_term, numeric_constraint, cross_reference |
| StandardsBasisMateriality | reference_only, material_support |
| SourceAvailabilityStatus | available, temporarily_unavailable, permanently_unavailable, rights_restricted, integrity_failed |
| StandardsIntelligenceResultStatus | completed_with_suggestions, completed_no_suggestions, not_permitted, unavailable, invalid_output |
| PublicOperationOutcome | success, invalid_request, protected_not_found, conflict, not_permitted, unavailable, indeterminate |
| StandardsFailureCode | NOT_FOUND, PROTECTED_NOT_FOUND, INVALID_REQUEST, RIGHTS_UNKNOWN, RIGHTS_EXPIRED, RIGHTS_REVOKED, CONTENT_UNAVAILABLE, EDITION_UNRESOLVED, SUPERSEDED, WITHDRAWN, AI_USE_NOT_PERMITTED, DISPLAY_NOT_PERMITTED, INDEXING_NOT_PERMITTED, SOURCE_INCOMPLETE, INDETERMINATE, STALE_ASSERTION, CONFLICT, VERSION_CONFLICT, IDEMPOTENCY_CONFLICT, INTEGRITY_FAILURE, RESOURCE_LIMIT_EXCEEDED, AI_UNAVAILABLE, INVALID_AI_OUTPUT, LEGACY_STANDARD_LOCATOR_PROHIBITED |

Closed value objects:

- StandardIdentityKeyV1: issuer_key 1..120, designation 1..120, normalized_issuer_key, normalized_designation. satco_standard_key_nfkc_casefold_v1 applies Unicode NFKC, maps Unicode dash characters to ASCII hyphen, trims, collapses internal Unicode whitespace to one ASCII space, then Unicode casefold. Punctuation and issuer-significant separators are preserved. The normalized pair is the identity key.
- EditionDesignationV1: edition_designation 1..120, normalized_edition_designation, publication_date, optional official_publication_identifier, optional effective_date, language, and explicitly non-authoritative jurisdiction/applicability metadata. Ambiguous issuer reuse of a designation without the official identifier or publication date returns EDITION_UNRESOLVED.
- ClauseLocatorV1: locator 1..240. It is an opaque human-readable locator; it is not parsed into a query language.
- ContentDigestV1: algorithm fixed sha256 and lowercase_hex exactly 64 hexadecimal characters.
- EffectiveRightsWindowV1: effective_from required aware UTC timestamp, effective_until optional aware UTC timestamp, with effective_from < effective_until when present.
- OpaqueAuthorizedHandleV1: a signed token described in section 12; it is never accepted as proof without live rights revalidation.
- PaginationV1: page_size default 20, range 1..100; protected collections fix page_size at 20. Cursor is opaque and scope-bound.
- NumericConstraintPayloadV1: operator eq, lt, lte, gt, gte, or closed_range; decimal values are canonical decimal strings; unit is 1..32 characters; single-value operators require value and prohibit bounds; closed_range requires lower and upper with lower <= upper and prohibits value.
- RequirementStatementPayloadV1: statement 1..2000.
- DefinedTermPayloadV1: term 1..200 and definition 1..2000.
- CrossReferencePayloadV1: target_standard_edition_id UUID, target_location 1..240, relationship normative_reference or informative_reference.

## 5. Actor capabilities and authorization predicates

No new user role or commercial authorization feature is introduced.

| EDS actor | Exact predicate |
|---|---|
| Platform catalog administrator | active authenticated user whose existing Role is admin and whose UUID occurs in the deployment setting STANDARDS_PLATFORM_CATALOG_ADMIN_USER_IDS; the default set is empty and malformed configuration fails startup |
| Organization standards administrator | active selected membership in the target organization and existing Role admin |
| Project engineer | active selected organization, project belongs to it, and user is project owner, primary assignee, or member of its engineering workspace |
| Report author | project engineer plus report owner for mutations |
| Report acceptor | existing Technical Report owner-only Human acceptance predicate |
| Organization member | active selected membership plus the existing owner-specific Project/Report read predicate required by the route |

The platform-admin allowlist is exposed through a StandardCatalogAdministrationPolicy protocol. Organization admin alone never grants global catalog mutation. This is an IDS-local fail-closed mapping of the EDS capability to existing authentication; it does not alter Role, membership, onboarding, licensing, or PATCH-058 scope.

Every operation applies this order:

1. Enforce only transport media type and total request-size bounds; protected identifiers remain opaque strings and no protected field/domain validation occurs yet.
2. Authenticate user and resolve one active selected organization membership; then safely parse the minimum scope identifier needed for a protected owner lookup.
3. Resolve organization/project/workspace/report through existing protected lookup; unauthorized existence is 404.
4. Evaluate actor capability.
5. Resolve catalog metadata needed for the operation.
6. Evaluate current rights, validity window, provider configuration, edition standing, applicability, and materiality.
7. Return 403 only when the actor is authorized to know the resource but the requested use is not permitted; otherwise preserve protected 404.
8. Perform domain validation, locking, and mutation.
9. Recheck authorization/rights inside the final transaction before disclosive reads or commits.

## 6. Aggregate inventory and ownership

There are seven new aggregate roots and one reused integration aggregate, eight boundaries total.

| Aggregate root | Owned records | Invariants |
|---|---|---|
| StandardIdentity | identity only | normalized authority/designation uniqueness within scope; immutable identity key |
| StandardEdition | edition plus standing observations | edition metadata immutable; standing is append-only history with one current head |
| OrganizationRightsBinding | binding versions | organization/edition/provider scoped only; one current head per tuple; no Project binding, wildcard, or widening by replacement |
| ProjectStandardApplicability | applicability versions | one current head per project/edition; bounded active set; candidate is not applicable |
| StandardSourceSnapshot | immutable object receipt and protected fragment metadata | project-bound, exact bytes/digest, no mutable source content |
| StandardKnowledgeAssertion | assertion plus verification events/current projection | typed bounded payload; human verification only; revocation/staleness propagates |
| StandardsIntelligenceRun | request/disposition/advisory result | one provider call maximum; no protected content in stored advisory output |
| TechnicalReport (existing) | revision, provenance, acceptance snapshot | standards basis is server-composed, historically immutable, and rechecked at acceptance |

Cross-aggregate references are UUID foreign keys with ON DELETE RESTRICT. There is no cascading delete of history.

## 7. Physical table inventory

Migration 1 creates exactly 11 tables. Migration 2 modifies two existing Technical Report tables. The PATCH-054 physical scope is therefore 13 tables: 11 new and 2 modified.

Common rules for every new table: UUID IDs are application-generated and have no database default; created_at/observed_at timestamps are TIMESTAMPTZ in UTC; actor IDs reference users(id) ON DELETE RESTRICT; organization/project/report/catalog foreign keys use ON DELETE RESTRICT; mutable projections carry version BIGINT NOT NULL DEFAULT 1 CHECK (version > 0). Tenant-scoped rows always contain organization_id and, where project-scoped, project_id.

### 7.1 standard_identities

Columns: id UUID PK; catalog_scope VARCHAR(24) NOT NULL; organization_id UUID NULL FK organizations(id); issuer_key VARCHAR(120) NOT NULL; issuer_display_name VARCHAR(200) NOT NULL; designation VARCHAR(120) NOT NULL; title VARCHAR(500) NOT NULL; normalized_issuer_key VARCHAR(160) NOT NULL; normalized_designation VARCHAR(160) NOT NULL; language VARCHAR(20) NULL; jurisdiction_metadata JSONB NULL; normalization_version VARCHAR(64) NOT NULL; metadata_source_reference VARCHAR(500) NOT NULL; identity_digest CHAR(64) NOT NULL; predecessor_identity_id UUID NULL FK self; retired_from_new_selection BOOLEAN NOT NULL DEFAULT false; registered_by UUID NOT NULL FK users(id); registered_at TIMESTAMPTZ NOT NULL DEFAULT now().

Checks: exact scope vocabulary; global_trusted requires organization_id NULL, organization_private requires non-NULL; normalization_version fixed satco_standard_key_nfkc_casefold_v1; safe metadata object <=4096 bytes; digest format. Unique indexes: global normalized pair WHERE catalog_scope='global_trusted'; organization_id plus normalized pair WHERE catalog_scope='organization_private'. Runtime may change only retired_from_new_selection from false to true when a correction successor references the row. Identity fields never update and DELETE is denied.

### 7.2 standard_editions

Columns: id UUID PK; standard_identity_id UUID NOT NULL FK standard_identities(id); edition_designation VARCHAR(120) NOT NULL; normalized_edition_designation VARCHAR(160) NOT NULL; official_publication_identifier VARCHAR(160) NULL; publication_date DATE NOT NULL; effective_date DATE NULL; language VARCHAR(20) NOT NULL; jurisdiction_metadata JSONB NOT NULL DEFAULT '{}'; metadata_source_reference VARCHAR(500) NOT NULL; predecessor_edition_id UUID NULL FK self; edition_digest CHAR(64) NOT NULL; registered_by UUID NOT NULL FK users(id); registered_at TIMESTAMPTZ NOT NULL DEFAULT now().

Checks: metadata is an object <=4096 bytes; language/source non-empty; digest format; predecessor belongs to the same identity. A database validator first treats parent identity plus normalized edition designation as the duplicate domain, and permits a reused issuer designation only when an official publication identifier or publication date explicitly disambiguates the publication unit. The enforcing unique expression is identity, normalized designation, normalized/coalesced official identifier, and publication date. Ambiguity returns EDITION_UNRESOLVED; an exact collision returns CONFLICT. Immutable after insert. Registration atomically appends the initial standing observation.

### 7.3 standard_edition_standing_observations

Columns: id UUID PK; standard_edition_id UUID NOT NULL FK standard_editions(id); standing VARCHAR(20) NOT NULL; superseded_by_edition_id UUID NULL FK standard_editions(id); observed_effective_at TIMESTAMPTZ NOT NULL; attributable_source_reference VARCHAR(500) NOT NULL; attributable_source_digest CHAR(64) NOT NULL; actor_kind VARCHAR(24) NOT NULL; observed_by UUID NULL FK users(id); predecessor_observation_id UUID NULL FK self; observation_digest CHAR(64) NOT NULL; is_current BOOLEAN NOT NULL DEFAULT true; version BIGINT NOT NULL DEFAULT 1; observed_at TIMESTAMPTZ NOT NULL DEFAULT now().

Checks: exact StandardStanding vocabulary; superseded requires superseded_by_edition_id, all other states prohibit it; actor_kind human or trusted_system and human requires observed_by; an edition cannot supersede itself; digest formats. Partial unique index on standard_edition_id WHERE is_current and unique non-NULL predecessor_observation_id. Trigger permits only current true→false and version increment on an existing row; all other fields are immutable. New current row and retirement of old head occur atomically.

### 7.4 standard_rights_bindings

Columns: id UUID PK; organization_id UUID NOT NULL FK organizations(id); standard_edition_id UUID NOT NULL FK standard_editions(id); source_provider_id VARCHAR(80) NOT NULL; rights_basis VARCHAR(40) NOT NULL; rights_status VARCHAR(16) NOT NULL; allow_metadata_visibility BOOLEAN NOT NULL DEFAULT false; allow_content_storage BOOLEAN NOT NULL DEFAULT false; allow_indexing BOOLEAN NOT NULL DEFAULT false; allow_excerpt_display BOOLEAN NOT NULL DEFAULT false; allow_source_retrieval BOOLEAN NOT NULL DEFAULT false; allow_derived_retention BOOLEAN NOT NULL DEFAULT false; allow_derived_current_use BOOLEAN NOT NULL DEFAULT false; ai_processing_permission VARCHAR(24) NOT NULL DEFAULT 'prohibited'; approved_processor_policy_ids JSONB NOT NULL DEFAULT '[]'; effective_from TIMESTAMPTZ NOT NULL; effective_until TIMESTAMPTZ NULL; rights_authority_reference VARCHAR(500) NOT NULL; rights_authority_digest CHAR(64) NOT NULL; predecessor_id UUID NULL FK self; reason_code VARCHAR(80) NOT NULL; reason VARCHAR(500) NULL; is_current BOOLEAN NOT NULL DEFAULT true; version BIGINT NOT NULL DEFAULT 1; rights_digest CHAR(64) NOT NULL; created_by UUID NOT NULL FK users(id); created_at TIMESTAMPTZ NOT NULL DEFAULT now().

Checks: exact RightsBasis, RightsStatus and AIProcessingPermission vocabularies; source_provider_id non-empty; approved processor IDs are a sorted unique token array and are nonempty only for approved_processor; effective_from < effective_until when present; metadata_only and unknown deny every protected capability; expired/revoked/unknown deny all new protected use; each capability defaults false and is enabled only by attributable provider policy; digest formats. One partial unique index establishes the sole current head for (organization_id, standard_edition_id, source_provider_id), and non-NULL predecessor_id is unique. There is no Project-scoped rights binding and no provider wildcard. registry_metadata is the reserved metadata-only provider ID.

Only true→false is_current/version update is allowed on an old row. Replacement inserts a complete new binding. Effective state becomes expired when valid_until is reached without rewriting history; explicit revoke creates a revoked successor. Rights evaluation returns indeterminate on ambiguity, invalid clocks, malformed provider policy, or concurrent change.

### 7.5 project_standard_applicability

Columns: id UUID PK; organization_id UUID NOT NULL FK organizations(id); project_id UUID NOT NULL FK projects(id); standard_edition_id UUID NULL FK standard_editions(id); candidate_designation_key VARCHAR(240) NULL; status VARCHAR(32) NOT NULL; applicability_role VARCHAR(20) NOT NULL; rationale_code VARCHAR(80) NOT NULL; rationale VARCHAR(1000) NOT NULL; origin_reference VARCHAR(240) NOT NULL; source_candidate_reference VARCHAR(240) NULL; mandatory_source_kind VARCHAR(32) NULL; mandatory_source_reference VARCHAR(500) NULL; mandatory_source_digest CHAR(64) NULL; expected_predecessor_revision BIGINT NULL; predecessor_id UUID NULL FK self; successor_id UUID NULL FK self; is_current BOOLEAN NOT NULL DEFAULT true; revision BIGINT NOT NULL DEFAULT 1; applicability_digest CHAR(64) NOT NULL; declared_by UUID NOT NULL FK users(id); created_at TIMESTAMPTZ NOT NULL DEFAULT now().

Checks: project/organization consistency; exact ProjectApplicabilityStatus and ProjectApplicabilityRole; origin_reference is attributable provenance, not a new behavior enum; candidate_advisory may retain an unresolved designation key but declarations require exact edition; mandatory is valid only with declared_applicable, Human actor, nonempty rationale, and mandatory source kind contract, regulation, customer_requirement, or company_policy plus reference/digest. Partial unique index on project_id, standard_edition_id for current non-retired Human declaration heads and unique non-NULL predecessor_id. Trigger allows only current true→false/successor/version linkage. Database constraint trigger rejects more than 64 current non-retired Human declaration heads per project. Candidates do not count and never change Project state.

### 7.6 standard_source_snapshots

Columns: id UUID PK; organization_id UUID NOT NULL FK organizations(id); project_id UUID NOT NULL FK projects(id); standard_identity_id UUID NOT NULL FK standard_identities(id); standard_edition_id UUID NOT NULL FK standard_editions(id); source_provider_id VARCHAR(80) NOT NULL; adapter_policy_id VARCHAR(80) NOT NULL; adapter_policy_version VARCHAR(40) NOT NULL; source_location VARCHAR(500) NOT NULL; availability_status VARCHAR(32) NOT NULL; request_purpose VARCHAR(80) NOT NULL; correlation_id UUID NOT NULL; object_key VARCHAR(500) NULL; object_version VARCHAR(240) NULL; provider_handle_ciphertext BYTEA NULL; provider_handle_key_version VARCHAR(40) NULL; provider_version_digest CHAR(64) NULL; content_sha256 CHAR(64) NULL; byte_count INTEGER NULL; media_type VARCHAR(120) NULL; rights_binding_id UUID NOT NULL FK standard_rights_bindings(id); rights_binding_version BIGINT NOT NULL; rights_digest CHAR(64) NOT NULL; evaluated_capabilities JSONB NOT NULL; standing_observation_id UUID NOT NULL FK standard_edition_standing_observations(id); standing_observation_digest CHAR(64) NOT NULL; source_metadata_digest CHAR(64) NOT NULL; integrity_verified BOOLEAN NOT NULL; integrity_verified_at TIMESTAMPTZ NOT NULL; snapshot_digest CHAR(64) NOT NULL; retrieved_at TIMESTAMPTZ NOT NULL; retrieved_by UUID NOT NULL FK users(id); created_at TIMESTAMPTZ NOT NULL DEFAULT now().

Checks: project/organization and identity/edition consistency; exact SourceAvailabilityStatus; available requires byte_count 1..8192, media type, integrity true, and exactly one of a lawfully retained private object receipt or an envelope-encrypted immutable provider handle; a provider handle additionally requires key version, provider_version_digest, and adapter re-resolution guarantees; retained bytes require content digest; non-available states prohibit object/provider receipt fields and protected bytes. evaluated capabilities are a sorted exact boolean decision object; all digests have SHA-256 format. Unique receipt: project_id, edition_id, source_provider_id, source_location, snapshot_digest. Rows are immutable. A source that lacks both lawful retention and a verifiable immutable provider handle is reference_only and cannot become material_support. Runtime SELECT of provider_handle_ciphertext is confined to the repository’s separately granted protected-resolution column path and no DTO includes it.

### 7.7 standard_knowledge_assertions

Columns: id UUID PK; organization_id UUID NOT NULL FK organizations(id); project_id UUID NOT NULL FK projects(id); standard_edition_id UUID NOT NULL FK standard_editions(id); source_snapshot_id UUID NOT NULL FK standard_source_snapshots(id); source_location VARCHAR(500) NOT NULL; source_content_digest CHAR(64) NOT NULL; assertion_kind VARCHAR(32) NOT NULL; canonical_representation JSONB NOT NULL; assertion_origin VARCHAR(20) NOT NULL; extraction_method_id VARCHAR(80) NOT NULL; extraction_method_version VARCHAR(40) NOT NULL; extraction_method_digest CHAR(64) NOT NULL; intelligence_run_id UUID NULL FK standard_intelligence_runs(id); assertion_digest CHAR(64) NOT NULL; verification_status VARCHAR(24) NOT NULL DEFAULT 'unverified'; current_verification_event_id UUID NULL; rights_binding_id UUID NOT NULL FK standard_rights_bindings(id); rights_binding_version BIGINT NOT NULL; rights_digest CHAR(64) NOT NULL; retained_derived_use_eligible BOOLEAN NOT NULL DEFAULT false; evaluated_rights_revision BIGINT NOT NULL; predecessor_assertion_id UUID NULL FK self; successor_assertion_id UUID NULL FK self; version BIGINT NOT NULL DEFAULT 1; created_by UUID NOT NULL FK users(id); created_at TIMESTAMPTZ NOT NULL DEFAULT now().

Checks: tenant/project/edition agree with snapshot; exact AssertionKind and AssertionOrigin; exact kind-specific representation; JSON object <=8192 bytes; digest formats; ai_assisted requires intelligence_run_id and other origins prohibit it; every new human, deterministic, or ai_assisted assertion starts unverified and current material eligibility requires human_verified, current retained-derived-use permission, confirmed source integrity, and a non-stale current evaluation. Unique: project_id, source_snapshot_id, source_location, assertion_kind, assertion_digest. Constraint trigger caps 32 assertions per snapshot. Runtime UPDATE is restricted to current_verification_event_id, verification_status, retained_derived_use_eligible, evaluated_rights_revision, successor linkage, and version; content fields are immutable.

### 7.8 standard_assertion_verification_events

Columns: id UUID PK; assertion_id UUID NOT NULL FK standard_knowledge_assertions(id); event_kind VARCHAR(32) NOT NULL; status VARCHAR(24) NOT NULL; reason VARCHAR(1000) NULL; source_rights_binding_id UUID NOT NULL FK standard_rights_bindings(id); source_rights_binding_version BIGINT NOT NULL; source_rights_digest CHAR(64) NOT NULL; assertion_digest CHAR(64) NOT NULL; basis_human_verification_event_id UUID NULL FK self; actor_kind VARCHAR(24) NOT NULL; verified_by UUID NULL FK users(id); verified_at TIMESTAMPTZ NOT NULL DEFAULT now().

Checks: event_kind verification_decision or eligibility_evaluation; status is human_verified, rejected, or stale; rejected/stale require reason; a human_verified verification_decision requires actor_kind human, an authorized verified_by user, current display plus derived-use rights, and exact digest comparison. An eligibility_evaluation may restore the projection to human_verified only by referencing a prior human_verified decision for the unchanged assertion digest and proving a newer active right permits retained derived assertion and current derived use. Immutable; unique assertion_id, id. A deferred FK from assertion.current_verification_event_id to this table is added after table creation.

### 7.9 standard_intelligence_runs

Columns: id UUID PK; organization_id UUID NOT NULL FK organizations(id); project_id UUID NOT NULL FK projects(id); report_id UUID NULL FK technical_reports(id); request_kind VARCHAR(40) NOT NULL; purpose VARCHAR(500) NOT NULL; correlation_id UUID NOT NULL; request_digest CHAR(64) NOT NULL; deterministic_result JSONB NOT NULL; deterministic_result_digest CHAR(64) NOT NULL; template_id VARCHAR(80) NOT NULL; template_version VARCHAR(40) NOT NULL; template_digest CHAR(64) NOT NULL; processor_policy_id VARCHAR(80) NOT NULL; provider_id VARCHAR(80) NOT NULL; provider_model VARCHAR(120) NOT NULL; provider_version VARCHAR(80) NULL; result_status VARCHAR(40) NULL; phase_status VARCHAR(24) NOT NULL DEFAULT 'requested'; call_count SMALLINT NOT NULL DEFAULT 0; rights_manifest JSONB NOT NULL; authorized_handle_digest CHAR(64) NOT NULL; input_digest CHAR(64) NOT NULL; input_byte_count INTEGER NOT NULL; advisory_output JSONB NULL; output_digest CHAR(64) NULL; suggestion_handle_digest CHAR(64) NULL; failure_code VARCHAR(64) NULL; created_by UUID NOT NULL FK users(id); created_at TIMESTAMPTZ NOT NULL DEFAULT now(); dispatched_at TIMESTAMPTZ NULL; completed_at TIMESTAMPTZ NULL; deadline_at TIMESTAMPTZ NOT NULL; version BIGINT NOT NULL DEFAULT 1.

Checks: deterministic_result is stable ordered safe metadata with at most 12 candidates and <=16384 bytes and survives every AI outcome; terminal result uses exact StandardsIntelligenceResultStatus; internal phase status is requested, dispatched, or terminal and is not a public vocabulary; call_count 0..1; input byte count <=32768; rights manifest contains only processor decision and sorted binding IDs/versions/digests; advisory output object <=16384 bytes, at most 12 suggestions, each suggestion text <=2000 characters, and no protected source fragments; terminal field consistency. Unique: organization_id, project_id, created_by, request_digest. Controlled CAS updates only. No report authority is stored here.

### 7.10 standards_idempotency

Columns: id UUID PK; organization_id UUID NOT NULL FK organizations(id); actor_id UUID NOT NULL FK users(id); operation VARCHAR(80) NOT NULL; idempotency_key VARCHAR(160) NOT NULL; request_digest CHAR(64) NOT NULL; state VARCHAR(16) NOT NULL DEFAULT 'pending'; resource_type VARCHAR(80) NULL; resource_id UUID NULL; response_status SMALLINT NULL; response_body JSONB NULL; created_at TIMESTAMPTZ NOT NULL DEFAULT now(); completed_at TIMESTAMPTZ NULL; expires_at TIMESTAMPTZ NOT NULL; version BIGINT NOT NULL DEFAULT 1.

Checks: state pending or completed; response body <= 16384 bytes and contains no protected source content; expiry after creation. Unique: organization_id, actor_id, operation, idempotency_key. Same key/different digest is 409. Pending rows are locked. Completed rows replay the same non-secret result. AI dispatched rows never cause another provider call.

### 7.11 standards_outbox

Columns: id UUID PK; organization_id UUID NULL FK organizations(id); aggregate_type VARCHAR(80) NOT NULL; aggregate_id UUID NOT NULL; event_id VARCHAR(100) NOT NULL; event_version SMALLINT NOT NULL DEFAULT 1; payload JSONB NOT NULL; occurred_at TIMESTAMPTZ NOT NULL DEFAULT now(); published_at TIMESTAMPTZ NULL.

Checks: event_id is one of standards events 1..20 in section 24; payload object <= 16384 bytes and metadata only; event_version=1. Unique: aggregate_type, aggregate_id, event_id, event_version; repeated lifecycle events use the immutable successor/verification/interaction record as aggregate_id. Runtime may update published_at only. Outbox publication is at-least-once; event consumers use outbox id as deduplication key.

### 7.12 Modified Technical Report tables

technical_report_provenance_entries gains: standard_basis_schema_version VARCHAR(40) NULL; standard_basis JSONB NULL; standard_basis_digest CHAR(64) NULL; standards_basis_materiality VARCHAR(24) NULL; standard_edition_id UUID NULL FK standard_editions(id) ON DELETE RESTRICT; standard_source_snapshot_id UUID NULL FK standard_source_snapshots(id) ON DELETE RESTRICT; standard_assertion_id UUID NULL FK standard_knowledge_assertions(id) ON DELETE RESTRICT; standard_intelligence_run_id UUID NULL FK standard_intelligence_runs(id) ON DELETE RESTRICT.

Legacy standards rows retain standard_identity, issuing_authority, edition, and clause_or_location and have all new standard-basis fields NULL. New standards rows have legacy locator fields NULL and a complete StandardHistoricalBasisV1. A CHECK and database validator enforce this exclusive-or. technical_reports is not given new columns; its accepted_snapshot JSON validator and immutable trigger are extended to understand StandardHistoricalBasisV1.

## 8. Index and query contract

In addition to PK/unique indexes, Migration 1 creates:

- standard_editions(standard_identity_id, publication_date DESC, id);
- standing observations(standard_edition_id, observed_at DESC, id);
- rights(organization_id, standard_edition_id, source_provider_id, created_at DESC);
- applicability(organization_id, project_id, state, created_at DESC);
- snapshots(organization_id, project_id, standard_edition_id, retrieved_at DESC);
- assertions(organization_id, project_id, standard_edition_id, verification_status, created_at DESC);
- assertion events(assertion_id, verified_at DESC);
- intelligence runs(organization_id, project_id, created_at DESC);
- idempotency(expires_at) and outbox(published_at, occurred_at) partial indexes.

All protected list queries lead with organization_id and project_id where applicable, apply stable ordering (created_at DESC, id DESC), fetch limit+1, and return a scope-bound opaque cursor. Search uses normalized exact/prefix matching with escaped LIKE patterns; no source-content full-text index is created.

## 9. Identity and edition lifecycle

Identity registration computes normalization server-side and repeats it in database generated validation functions. Conflicting normalized keys return 409 without revealing an organization-scoped identity to another tenant. Global reads are available only through authorized standards operations; organization identities require tenant scope.

Edition rows never change. Current/superseded/withdrawn/unknown standing is represented by a new observation while the previous head is retired in one transaction. Superseded or withdrawn editions remain readable historically. New material_support reliance requires exact declared applicability plus an attributable Human acknowledgement of the pinned standing observation and rationale; absent that acknowledgement it returns SUPERSEDED or WITHDRAWN. Unknown standing blocks material support with EDITION_UNRESOLVED. Existing accepted reports are never rewritten.

## 10. Rights evaluation and single-head mechanism

Rights attach only to organization_id + standard_edition_id + source_provider_id. There is no Project override, provider wildcard, inheritance union, or possession-based grant. The evaluator requires one current head, status active, effective time, the independent boolean capability for the requested operation, matching Organization/edition/provider, and a configured provider policy. AI additionally requires local_only with the approved local processor class or approved_processor with the selected processor policy ID. A missing, ambiguous, expired, revoked, unknown, malformed, or concurrently changing binding fails closed with the accepted failure mapping.

Create/replace/revoke UoW:

1. Lock user, organization, selected membership, and optional project.
2. Authorize organization standards administrator.
3. Lock the Organization/edition/provider current-rights tuple with SELECT FOR UPDATE, including an advisory transaction lock keyed by that exact tuple to serialize the first insert.
4. Validate every capability boolean, AI processing permission, approved processor policy set, attributable authority, and prevent widening beyond configured provider policy.
5. Insert the successor, set the prior row is_current=false with version CAS, and compute canonical rights_digest.
6. Mark affected current assertions unusable/stale in deterministic UUID order and emit events.
7. Stage shared AuditLog and standards_outbox in the same transaction.
8. Commit; a uniqueness/CAS race is retried up to the global three-attempt limit, then VERSION_CONFLICT/409.

Time expiry is evaluated on every use. When an active current head first crosses effective_until, the rights evaluator under the tuple lock appends one expired successor and standards.rights.expired event, protected by predecessor uniqueness and idempotent event identity. A bounded maintenance command may materialize the same transition proactively, but correctness never depends on scheduling and no operation remains permitted after the instant.

## 11. Authorized retrieval port and source snapshots

backend/app/ports/standards.py defines:

    class AuthorizedStandardSourceProvider(Protocol):
        provider_id: str
        adapter_policy_id: str
        adapter_policy_version: str
        async def retrieve_fragment(self, request: AuthorizedFragmentRequestV1) -> AuthorizedFragmentResultV1: ...

AuthorizedFragmentRequestV1 contains identity and exact edition IDs, exact source location, maximum_bytes fixed at 8192, request purpose, provider-specific opaque locator, correlation ID, and an internal one-use authorization context carrying the evaluated storage/retrieval/display/derived-use decision. It contains no bearer secret in logs. The closed result union is AvailableFragmentV1(bytes or immutable_provider_handle, media_type, provider_request_id, provider_version, integrity_digest), RightsRestrictedV1, TemporarilyUnavailableV1, PermanentlyUnavailableV1, or IntegrityFailedV1. Providers MUST NOT expose list, bulk export, whole-document retrieval, public URLs, arbitrary URLs, redirects to unapproved hosts, or a generic search API.

The service authenticates and authorizes before provider selection. One SRC-01 request contains 1..8 exact fragment requests; their declared/composed aggregate is at most 32768 bytes. Each provider read accepts at most 8193 bytes and fails RESOURCE_LIMIT_EXCEEDED if the sentinel byte exists; the aggregate is checked again after retrieval before persistence. No partial success is persisted. Customer uploads must already have a clean existing scan disposition before the adapter reads an exact object key. When retention is permitted, a successful fragment is written through StandardSourceObjectStore, a narrow wrapper over SupportingFileObjectStore, under a random opaque standards/{organization_uuid}/{project_uuid}/{snapshot_uuid} key. put_private, head_exact, open_exact, and delete_exact-for-compensation are the only operations. Server-side encryption, private ACL, content digest, version receipt, and exact size are required. When retention is not permitted, an allowlisted provider may instead return an immutable handle only if it can later re-resolve the exact publication/location and verify the same version/content digest. No object key, provider handle, or presigned URL is returned by API.

The database snapshot is inserted only after object receipt verification. A failed database insert invokes best-effort exact-key compensation; orphan cleanup operates only on recorded compensation keys. SRC-02 display reauthorizes, reevaluates rights, checks the receipt/digest, reads at most 8192 bytes, returns only the purpose-bound bounded excerpt representation, emits no cacheable public URL, and sets private/no-store response headers.

SRC-01 uses three bounded phases: (1) authenticate/authorize, lock the exact rights head, reserve idempotency, and persist a safe retrieval intent, then commit; (2) perform allowlisted provider/object work with no database transaction or lock; (3) open a fresh transaction, reauthenticate, lock idempotency plus the same rights/standing/applicability tuple, verify versions/digests/limits/receipts, insert all snapshots and audit/outbox rows, complete idempotency, and commit. If revocation linearized first, phase 3 rejects, exact-key compensates retained objects, and releases neither bytes nor handles. If retrieval linearized first, rights-at-use is frozen, but every later SRC-02/assertion/Report/AI use still rechecks current rights.

## 12. Opaque authorized handles

OpaqueAuthorizedHandleV1 is a signed, short-lived, non-persisted capability reference, not a bearer grant. It uses canonical JSON plus domain-separated HMAC-SHA256 derived from settings.resolved_secret_key(), URL-safe base64 without padding, key version 1, and constant-time signature comparison.

Exact signed payload: version=1; type=standards_authorized_handle; actor_id; organization_id; project_id; report_id nullable; report_revision nullable; operation; standard_identity_id and identity_digest; standard_edition_id and edition_digest; standing_observation_id/value/digest and acknowledgement_required; applicability_id/revision/digest/status/role nullable; source_snapshot_id or provider-attestation ID nullable plus snapshot_digest/location digest; assertion_id/digest/verification status nullable; rights_binding_id/version/digest/status plus evaluated capability digest; materiality; intelligence_run_id nullable; issued_at; expires_at; nonce UUID. It contains no source text, object key, provider handle/token, license term, credential, or raw assertion representation. Lifetime is at most 15 minutes. Every consumer validates signature, version, expiry, actor, tenant, project, report/revision, operation, referenced IDs/digests, current rights head/provider policy, and current resource state. A handle cannot cross actors, tenants, projects, reports, operations, or resources. Token errors collapse to protected 404 unless the caller is independently authorized to know the referenced resource. Acceptance never trusts a client handle; it resolves persisted server-composed report provenance and performs a fresh recheck.

## 13. Assertion creation and verification

Assertion creation requires an authorized material_support source and active source retrieval/derived-retention capabilities. The server selects the closed canonical representation by AssertionKind, calculates assertion_digest, and inserts an unverified, currently ineligible assertion regardless of human, deterministic, or ai_assisted origin. AI output may propose an assertion but cannot insert or verify it.

Human verification transaction:

1. Resolve authentication and protected project scope.
2. Require project engineer; AI/provider identities are rejected.
3. Lock idempotency, edition/current standing, current rights head, snapshot, and assertion in the global order.
4. Revalidate snapshot or immutable-handle receipt, digest, edition, location, typed representation, live excerpt/display and derived-current-use capabilities, and version CAS.
5. Insert immutable human_verified event, set the assertion projection to human_verified/retained_derived_use_eligible=true/current event/version+1, and stage Audit/outbox atomically.
6. On rejection, insert rejected event and set unusable. On rights/standing/source invalidation, insert stale event and set unusable. History remains readable to authorized historical consumers.

## 14. Revocation and staleness propagation

Rights expiry/revocation makes current derived-use eligibility false immediately through live evaluation. Directly locked affected assertions receive immutable stale eligibility events; an organization-wide binding may span more projects than one bounded transaction, so the rights event is the durable propagation marker and every read/use still fails closed before the bounded worker records remaining stale events. A newer active binding may restore an unchanged human_verified assertion only through a fresh integrity/rights evaluation event referencing the original Human verification; stale history is retained. Edition/source integrity invalidation follows the same pattern. Report draft bases become visibly stale but are not rewritten. Accepted report snapshots remain immutable and render historical status plus current-access unavailability without exposing source content.

## 15. Technical Report standards provenance

backend/app/models/technical_report_command.py adds StandardHistoricalBasisV1 to the provenance union. It freezes exactly:

- schema_version fixed standard_historical_basis_v1, basis_id, StandardsBasisMateriality, Human selection rationale, selecting Human/time, and Report revision;
- standard identity ID, scope-safe issuer/designation/title, and identity_digest;
- exact edition ID, edition designation, publication metadata, and edition_digest;
- standing observation ID, StandardStanding, observation_digest at use, and Human acknowledgement/rationale when required;
- source snapshot/provider-handle ID, exact location, provider identity, an envelope-encrypted immutable token plus its digest/key version when handle-backed, SourceAvailabilityStatus at use, byte extent, snapshot_digest, and content digest when available—never protected bytes;
- rights binding ID/version/digest, RightsBasis, RightsStatus, evaluated capability booleans, AI processor decision when applicable, and decision time;
- applicability ID/revision/digest/status/role when present;
- assertion ID/kind/digest/origin/verification status, Human verifier identity, and current-use evaluation when present;
- intelligence interaction ID, provider/model/template/input/output digests and processor decision when AI-assisted context was selected;
- accepted Report identity/version/time when accepted; and
- basis_digest over the canonical object excluding basis_digest.

reference_only may cite safe catalog identity, exact edition when known, and bibliographic metadata, but cannot substantiate a standards-backed claim or provide clause text to AI. material_support requires an available authorized immutable snapshot or qualifying provider handle with exact edition/location/integrity/rights provenance. If an assertion is used for material support it must be human_verified and currently eligible; an assertion is not mandatory when the authoritative basis is the qualifying source itself. Superseded/withdrawn material support additionally requires exact declared applicability and Human standing acknowledgement. At most 16 standards bases and 32 total provenance entries are permitted.

New provenance rows reuse source_type standard, source_class standards_material, and owning_capability NULL to preserve the existing Technical Report enum and owner contract. StandardsBasisMateriality and the new basis validator distinguish reference_only (is_material=false) from material_support (is_material=true); legacy StandardLocator remains standards_material/is_material=true. No new Technical Report enum token is invented. Accepted snapshots copy the full object, not a live join. The persistence representation may contain the sealed provider token required for future exact re-resolution; API/report render serializers always omit it and expose only its digest after current authorization.

### Legacy StandardLocator guard

Accepted historical StandardLocator payloads remain byte-for-byte parseable and render as legacy_unattested_reference. They are never backfilled, normalized, enriched, or reinterpreted. A pre-cutover draft remains readable but is marked legacy_conversion_required. After the cutover, every new manual locator returns invalid_request / LEGACY_STANDARD_LOCATOR_PROHIBITED, and any draft revision or acceptance must remove it or replace it through the canonical handle workflow. A successor Report does not copy it as new provenance. Migration records only the cutover guard; it never parses or rewrites a legacy payload.

## 16. Report revision and acceptance units of work

Report standards-basis revision extends the existing draft-revision flow; it does not create a second report command path:

1. Parse only bounded opaque handles, requested materiality, Human rationale, expected Report version, and idempotency identity; reject client-supplied raw catalog/source/assertion/provenance facts.
2. Existing TechnicalReportUnitOfWork locks/authenticates user, organization, membership, workspace, project, then report.
3. Lock report idempotency and standards references in global order.
4. Require report owner and mutable lifecycle.
5. Resolve current applicability, standing/acknowledgement, rights capability booleans, snapshots or qualifying immutable provider handles, and any used verified assertions server-side; client-supplied provenance objects are rejected.
6. Compose and hash no more than 16 StandardHistoricalBasisV1 entries and no more than 32 total provenance entries.
7. Persist a new report revision with optimistic version check.
8. Stage technical_report.standards_basis.attached and existing revision audit metadata in technical_report_outbox/shared audit in the same commit.

Acceptance extends the existing POST /technical-reports/{report_id}/acceptance flow:

1. Use existing authorization and owner-only acceptance predicate.
2. Lock report/idempotency and all referenced edition, rights, applicability, snapshot, and assertion rows in sorted order.
3. Recompute each basis digest and live eligibility. Every item checks exact identity/edition/standing, required acknowledgement, applicability revision where used, rights head/status/time/provider/all required capabilities, snapshot or immutable-handle availability and integrity, materiality, and any used assertion/AI provenance. A used material assertion must be human_verified and currently eligible. No client handle alone is trusted.
4. On revoked/expired/not-permitted rights return authorized 403; unavailable source returns 503; stale assertion or lifecycle/version race returns 409; unauthorized existence stays 404.
5. Freeze the full provenance in accepted_snapshot, apply existing accepted immutability triggers, emit technical_report.accepted exactly once, and commit atomically.

Historical reads return the frozen identity, edition, standing, rights-at-use decision, materiality, source location, Human selection, and digests from accepted_snapshot. They may add a separately labelled current availability/status projection after fresh authorization. Protected display or handle resolution always rechecks current membership, Report access, display permission, rights head, source availability, and integrity. Denial is a masked rights_restricted or safe CONTENT_UNAVAILABLE presentation. Historical meaning is unchanged; object keys, provider handles, and protected bytes remain hidden.

## 17. Standards intelligence services

Deterministic StandardsIntelligenceService is authoritative for: identity/edition resolution; package candidate expansion; current applicability status/role/revision; rights status/time/provider/capability booleans; standing and acknowledgement need; source availability/completeness/integrity; requested materiality; assertion verification/current-use eligibility; duplicates/conflicts; and all limits. It produces a stable ordered set of at most 12 advisory candidates with opaque handle, materiality, eligibility, safe rationale/warning codes, exact edition/standing, and actor-safe availability. AI cannot override this result.

backend/app/ai/standards_intelligence.py defines a StandardsAdvisoryProvider protocol and immutable prompt contract with template ID, version, template digest, input schema digest, output schema digest, provider/model/version, 30-second deadline, one call, and zero retries. The authorized input composer includes the Human-selected bounded purpose/question, opaque authorized handle IDs, server-selected authorized snapshot/assertion representations, safe edition/standing/applicability/materiality metadata, explicit non-authority instructions, and template/limit identity. Credentials, object keys, arbitrary URLs, unauthorized source text, license terms, unverified assertion text, and hidden provider errors are excluded.

Retrieved source text is always data, never instructions. It is delimited in a typed content field, stripped of control characters, bounded before composition, and accompanied by a fixed instruction that content cannot alter policy, tools, output schema, or authorization. Output is a closed object with exact StandardsIntelligenceResultStatus, zero to 12 suggestions, and bounded advisory text. Each suggestion contains only one known input source/assertion/basis handle ID, one safe rationale code, and explanatory text <=2000 characters. Unknown keys/IDs, invented standards/editions/clauses, URLs, executable markup, non-input handles, or compliance/applicability/approval claims reject the entire output as invalid_output / INVALID_AI_OUTPUT; no partial suggestions survive.

Provider authorization is per operation: the adapter must be statically registered, enabled, and HTTPS-only. prohibited returns not_permitted / AI_USE_NOT_PERMITTED; local_only permits only the configured local processor class; approved_processor requires exact membership of the selected processor policy ID. Provider credentials remain server-side and are never placed in handles, audit, outbox, or persisted request manifests.

Validated advisory output is persisted in standard_intelligence_runs because INT-02 is a durable retrieval contract. It contains no protected excerpt and is bounded to 16 KiB. The run also retains the accepted EDS interaction provenance: Human/tenant/project/report/purpose/correlation; provider/model/version; template identity; processor policy and rights references; sorted handle/input digests and byte count; output/suggestion-handle digests; timestamps/deadline; and advisory classification. Audit/outbox store IDs, digests, status, timing, and counts only. Advisory output never becomes a verified assertion or report provenance without a separate Human-governed command.

## 18. Multi-phase AI transaction boundary

Phase 1 — authorize and reserve, one short transaction: perform deterministic authorization/rights checks; validate handles; reserve standards_idempotency; create requested run with safe input manifest; stage standards.intelligence.requested audit/outbox; commit.

Phase 2 — dispatch without database locks: a short CAS transaction changes requested→dispatched and call_count 0→1, records dispatched_at, then commits. Only then may the external call begin. No database transaction or row lock spans network I/O. Deadline 30 seconds; retry count zero.

Phase 3 — reauthorize and finalize, one fresh transaction: reauthenticate, lock the run and referenced state in global order, reevaluate rights/provider/resource state, validate the closed output, then persist completed_with_suggestions, completed_no_suggestions, invalid_output, unavailable, or not_permitted as applicable, complete idempotency, and stage one terminal completed/unavailable audit/outbox event. If rights changed, provider output is discarded and not disclosed while the deterministic result remains.

A crash after dispatch is never automatically retried. A repeated idempotency key returns the existing run; if dispatch completion is unknowable, the run resolves unavailable with AI_UNAVAILABLE rather than making a second provider call. Thus one logical request causes no more than one external call.

## 19. Global lock order and retry contract

Transactions acquire only applicable rows, always in this order:

1. package-registry shared guard when package candidates are read;
2. User, Organization, selected membership, Project, EngineeringWorkspace, each stable UUID ascending;
3. TechnicalReport when present;
4. idempotency row;
5. StandardIdentity then StandardEdition, UUID ascending;
6. current rights tuple(s), tuple key ascending;
7. current applicability head(s), edition UUID ascending;
8. StandardSourceSnapshot, UUID ascending;
9. StandardKnowledgeAssertion then verification event, UUID ascending;
10. StandardsIntelligenceRun;
11. append AuditLog/outbox rows.

Standards-only commands do not lock a report. Report commands use the existing TechnicalReport UoW and add standards locks after the report. Provider/object reads and AI calls occur outside locked transactions; their receipts are revalidated in a fresh transaction. Serialization/deadlock/CAS failures use at most three total database attempts with bounded jitter. The third failure returns VERSION_CONFLICT/409. Idempotency prevents duplicate semantic effects across attempts.

## 20. Exact API contract — 22 operations

All routes use JSON UTF-8, UUID path parameters, centralized authentication, structured ErrorResponse, request ID, and no-store for protected results. Mutations require Idempotency-Key except pure retirement/revocation aliases still use it. Unknown/unauthorized protected resources return 404; authorized not-permitted is 403; invalid shape is 422; state/version/idempotency conflict is 409; provider/object/AI outage is 503. List responses use {items, next_cursor}; page_size default 20/max 100 except protected content lists fixed at 20.

| ID | Method and route | Request / response and bounds | Authorization and result |
|---|---|---|---|
| CAT-01 | GET /standards | q<=120, scope, cursor, page_size; identity summaries | authenticated member; global_trusted plus own organization_private; 200/404 |
| CAT-02 | GET /standards/{standard_id} | include_editions, cursor; identity, <=20 editions/standing heads | authenticated member with visible scope; 200/404 |
| CAT-03 | POST /standards | StandardIdentityCreateV1; identity | platform catalog admin for global_trusted, organization standards admin for own organization_private; idempotent; 201/409/422 |
| CAT-04 | POST /standards/{standard_id}/editions | StandardEditionCreateV1; immutable edition | matching catalog administrator; idempotent; 201/404/409/422 |
| CAT-05 | POST /standards/{standard_id}/editions/{edition_id}/standing-observations | StandingObservationCreateV1; new head | matching catalog administrator; idempotent; 201/404/409/422 |
| RGT-01 | GET /organizations/current/standard-rights | cursor/page_size/filter; effective bindings without secrets | organization standards admin; 200 |
| RGT-02 | PUT /organizations/current/standard-rights/{edition_id}/{source_provider_id} | complete RightsBindingReplaceV1 with basis/status, seven independent capability booleans, AI permission/policies, authority, effective time, expected version; new binding/version | organization standards admin; own Organization only, never Project-scoped; idempotent; 200/403/404/409/422 |
| RGT-03 | POST /organizations/current/standard-rights/{rights_binding_id}/revocations | reason<=500; revoked successor | organization standards admin; idempotent; 201/404/409 |
| APP-01 | GET /projects/{project_id}/standards/applicability | state/cursor/page_size; applicability heads | project engineer; 200/404 |
| APP-02 | GET /projects/{project_id}/standards/candidates | package_version optional; <=64 bounded candidates | project engineer; deterministic read; 200/404/409 |
| APP-03 | POST /projects/{project_id}/standards/applicability | edition_id, status, role, rationale code/text, expected revision; mandatory source kind/reference/digest when role mandatory; head | project engineer; Human declaration; idempotent; 201/404/409/422 |
| APP-04 | POST /projects/{project_id}/standards/applicability/{applicability_id}/retirements | reason<=1000; retired head | project engineer; idempotent; 201/404/409 |
| SRC-01 | POST /projects/{project_id}/standards/source-snapshots | edition_id, provider_id, purpose, 1..8 exact location/authorized-handle fragment requests, <=32768 bytes; 1..8 safe snapshot/immutable-handle metadata items, all-or-nothing | project engineer or report author plus fresh retrieval/intended-use capability booleans for every item; idempotent; 201/403/404/409/422/503 |
| SRC-02 | GET /projects/{project_id}/standards/source-snapshots/{snapshot_id}/display | no body; purpose-bound bounded excerpt representation with private/no-store headers | authorized organization member with Project/Report access plus fresh display rights/integrity; 200/403/404/409/503; never returns object/provider handle or generic raw-file access |
| AST-01 | POST /projects/{project_id}/standards/assertions | snapshot_id, location, kind, closed representation, origin; unverified assertion | project engineer plus active derivation and derived-retention capabilities; idempotent; 201/403/404/409/422 |
| AST-02 | POST /projects/{project_id}/standards/assertions/{assertion_id}/verifications | expected version, reason optional<=1000; verified assertion | project engineer Human actor plus fresh display and derived-current-use rights; idempotent; 201/403/404/409/422 |
| AST-03 | POST /projects/{project_id}/standards/assertions/{assertion_id}/rejections | reason required<=1000; rejected assertion | project engineer; idempotent; 201/404/409/422 |
| RPT-01 | GET /technical-reports/{report_id}/standards/candidates | materiality/cursor; <=20 authorized basis candidates with opaque handles | report author for the exact draft plus Project scope; 200/404; protected candidates/counts are suppressed |
| RPT-02 | POST /technical-reports/{report_id}/standards-basis-revisions | base_version, <=16 candidate handles, revision metadata; new draft report revision | report author/owner; server composes basis; report idempotency; 201/403/404/409/422/503 |
| RPT-03 | POST /technical-reports/{report_id}/acceptance | existing acceptance request unchanged; accepted report | existing owner-only acceptance plus fresh standards recheck; existing report idempotency; 200/403/404/409/422/503 |
| INT-01 | POST /projects/{project_id}/standards/intelligence-runs | purpose/question, <=16 handles but <=8 fragments/32768 bytes, optional report_id; deterministic result plus interaction | project engineer/report author plus exact AIProcessingPermission/processor policy; idempotent; 202 requested or 200 terminal replay; not_permitted/unavailable/invalid_output mappings |
| INT-02 | GET /projects/{project_id}/standards/intelligence-runs/{run_id} | no body; bounded status/advisory result | original actor or authorized project engineer with current rights; 200/403/404/503 |

RGT-01 is deliberately admin-only because rights metadata can disclose commercial relationships. CAT reads expose only catalog metadata. INT-02 returns not_permitted after revoked rights and suppresses prior advisory text.

Transport envelopes are closed. StandardsSuccessV1 contains operation_id, outcome=success, request_id, resource, and optional next_cursor. StandardsDomainResultV1 contains operation_id, one of not_permitted/unavailable/indeterminate, one accepted reason_code, request_id, and safe details containing only already-authorized IDs/states. StandardsErrorV1 contains operation_id, outcome invalid_request/protected_not_found/conflict, accepted reason_code, request_id, and a safe message; field_errors appear only after authorization and never echo protected input. HTTP mapping is success 200/201/202 as the route defines; invalid_request 422; protected_not_found 404; conflict 409; not_permitted 403 only for an already-known authorized resource; unavailable 503; indeterminate 200. Public-safe missing global catalog metadata may use 404/NOT_FOUND. Cursors use the same domain-separated HMAC construction as handles and bind actor/organization/filter/order/expiry.

Mutation bodies set extra=forbid, cap every string/array/JSON object before repository access, require expected version/revision wherever a mutable head exists, and require Idempotency-Key. Read DTOs omit storage locators, immutable provider tokens, rights authority text, protected counts, content, prompts, credentials, and unsafe diagnostics.

## 21. Frontend contract — exactly six surfaces

| Surface | Location and behavior |
|---|---|
| 1. Standards Registry | StandardsPages plus StandardsRegistryPanel: search/browse identity, edition and standing; global_trusted/organization_private badge; admin create controls only when allowed |
| 2. Organization Standards Rights | OrganizationAdminPage plus OrganizationStandardsRightsPanel: current binding, permitted operations, dates/provider, replace/revoke dialog, explicit restricted/expired/revoked/indeterminate states |
| 3. Project Standards Applicability | ProjectsPage plus ProjectStandardsPanel: package candidates separated from Human declarations; informative/design_basis/mandatory roles; mandatory provenance; applicable/not-applicable/retired actions; 64-head limit visible |
| 4. Source and Assertion Workspace | ProjectStandardsPanel assertion/source subview: retrieve one bounded fragment or qualifying immutable provider attestation, create one of four typed assertions, Human verify/reject; never displays object/provider handles or whole documents |
| 5. Technical Report Standards Basis | ReportPages plus TechnicalReportStandardsBasisPanel: eligible basis selection, reference_only/material_support distinction, standing acknowledgement, legacy conversion state, historical snapshot, acceptance preflight |
| 6. Standards Intelligence | StandardsIntelligencePanel: explicit advisory request, status, <=12 suggestions, source-handle references, no automatic application |

frontend/src/api/client.ts adds authorized-known restricted to ApiResult without weakening protected behavior. Mapping is: 401→unauthenticated; protected 403/404→not_found unless the route and authenticated response body provide a validated accepted failure code proving the actor is authorized to know it; DISPLAY_NOT_PERMITTED/AI_USE_NOT_PERMITTED or an already-known rights binding may map to restricted; 409→conflict; 422→invalid; 503→unavailable; success with domain outcome indeterminate→indeterminate; empty authorized collection→empty; loading and success remain distinct. Error text never includes provider bodies, rights terms, object keys, provider handles, or hidden IDs.

All six surfaces provide keyboard operation, programmatic labels, focus restoration after dialogs, aria-live polite status, table/list semantics, error summaries, and non-color state icons/text. Logical CSS properties support RTL; icon direction is mirrored only when semantic; mixed identifiers use dir=ltr or bdi; dates/numbers remain locale-formatted. Destructive-looking revoke/retire actions require confirmation. Advisory content is labelled non-authoritative and cannot be accepted by a single click.

## 22. Package and PATCH-053 adapters

StandardsPackageCandidateAdapter implements the existing StandardsApplicabilityHookV1. It reads only the frozen static package descriptor and emits the exact package candidate contract: candidate_id/digest; Organization, Project, Workspace IDs; package key/version; descriptor digest; Project configuration revision; hook ID; candidate Standard designation key and optional family key; optional already-resolved identity/edition handle; suggested role limited to informative or design_basis; closed advisory rationale code; and emission time. max_results is 64, timeout_ms is a deterministic local bound, and no network/provider call occurs. EIC v1 descriptor is updated from the placeholder zero-result hook to an explicit bounded candidate set. Candidates contain no protected text, URL, credential, prompt, executable rule, provider operation, or mandatory role and cannot create applicability or rights.

APP-02 is a side-effect-free deterministic read. standards.applicability.candidate_recorded is emitted only when APP-03 references a package candidate that has not yet been persisted: the service inserts its immutable candidate_advisory provenance row and event, then appends the Human declaration and standards.applicability.declared in the same transaction. Direct Human declarations without a package candidate emit only the declared event. Candidate identity/digest uniqueness prevents duplicate recorded events.

StandardsCrossDisciplineProjectionAdapter exposes only identity/edition IDs, applicability state, standing, materiality, verification status, basis digest, and safe labels to the accepted PATCH-053 read-only projection. It never returns source bytes, assertion payloads, object keys, provider terms, handles, or advisory text. PATCH-053 remains owner of its deterministic assessment transaction and never performs protected standards retrieval while holding that transaction.

## 23. PostgreSQL security contract

All PATCH-054 tables/functions are owned by satco. Migration 1 and 2:

- REVOKE ALL ON every new table, sequence, function, and trigger function FROM PUBLIC;
- REVOKE ALL FROM satco_registry_installer; the installer role receives no standards data privilege;
- grant satco_runtime SELECT/INSERT on identities, editions, standing observations, rights, applicability, assertions, and verification events; grant snapshot SELECT by an explicit safe-column list that excludes provider_handle_ciphertext, and snapshot INSERT by the exact creation-column list;
- grant satco_runtime only the listed projection UPDATE columns: identity retired_from_new_selection; standing/right/applicability is_current, version/revision, and successor linkage; assertion current_verification_event_id, verification_status, retained_derived_use_eligible, evaluated_rights_revision, successor linkage, and version; intelligence phase_status/result_status/call_count/timestamps/output digests/failure/version; idempotency completion fields/version; outbox published_at;
- grant no runtime DELETE and no UPDATE of immutable source, identity, edition, provenance, event, tenant, actor, digest, or object receipt columns;
- revoke direct EXECUTE on SECURITY DEFINER validators and trigger functions from PUBLIC and runtime; triggers invoke them under fixed search_path pg_catalog, public. The sole exception is a narrowly granted resolve_standard_provider_handle(snapshot_id, organization_id, actor_id, purpose) SECURITY DEFINER function: fixed search_path, no dynamic SQL, verifies active membership, matching snapshot/rights head, display/retrieval purpose, effective time, integrity, and returns only the sealed handle. PUBLIC and satco_registry_installer have no EXECUTE;
- validate caller-supplied JSON types, byte sizes, digest syntax, tenant/project consistency, single heads, counts, and accepted-report immutability in database functions;
- use explicit schema-qualified objects and no dynamic SQL.

The application service account can perform only designed transitions. It cannot overwrite historical identity/edition/source/verification/provenance rows or delete them. Database constraints are the final guard; application checks provide clearer errors.

## 24. Exact Audit/outbox events — 22

Every event is staged atomically with its authoritative mutation. Shared audit_logs receives the same event ID with actor, tenant, request ID, target IDs, before/after digests/status, and no protected content. Events 1..20 use standards_outbox; events 21..22 use the existing technical_report_outbox.

1. standards.identity.registered
2. standards.edition.registered
3. standards.edition.standing_observed
4. standards.rights.created
5. standards.rights.replaced
6. standards.rights.expired
7. standards.rights.revoked
8. standards.applicability.candidate_recorded
9. standards.applicability.declared
10. standards.applicability.retired
11. standards.source.retrieval_succeeded
12. standards.source.retrieval_unavailable
13. standards.source.snapshot_created
14. standards.assertion.created
15. standards.assertion.human_verified
16. standards.assertion.rejected
17. standards.assertion.stale
18. standards.intelligence.requested
19. standards.intelligence.completed
20. standards.intelligence.unavailable
21. technical_report.standards_basis.attached
22. technical_report.accepted

Rights expiry event 6 is emitted only when an explicit expiry transition is materialized; live time evaluation remains authoritative. Event 22 retains its existing identifier and gains only backward-compatible standards summary metadata.

## 25. Idempotency and outcome replay

Every new mutation hashes canonical method, route identity, scoped actor/tenant, and validated body. A key is scoped by organization, actor, and operation. The first request reserves pending under lock; same key/same digest returns the existing terminal result or resource; same key/different digest returns 409. Failed authorization is not persisted. Provider-safe unavailable terminal outcomes are replayable. Pending non-AI work may be recovered only after proving no side effect; dispatched AI is never called again. TTL is at least 24 hours and cleanup is an operational concern outside the request transaction. Report mutations continue using technical_report_idempotency so one aggregate has one idempotency authority.

## 26. Resource enforcement map

| Limit | Exact enforcement |
|---|---|
| 64 editions per identity | request/service count under identity lock; database constraint trigger; 422/RESOURCE_LIMIT_EXCEEDED; UI disables add with count |
| 64 active declared applicability heads per project | service count under project/head locks; database constraint trigger; 409; UI count |
| 16 standards bases and 32 total report provenance entries | Pydantic schema, report service, database provenance validator/accepted snapshot validator, UI selector |
| 8 fragments per retrieval or intelligence request | SRC/INT request schemas, composer, run input manifest validator; no silent truncation |
| 8192 bytes per fragment | provider read 8193 sentinel, object receipt check, snapshot CHECK, download stream guard |
| 32768 aggregate fragment bytes | composer sum before provider call and run manifest DB validator |
| 32 assertions per snapshot | service count under snapshot lock and DB constraint trigger |
| 12 AI suggestions | output schema, service validator, run JSONB validator, frontend renderer |
| 2000 characters per suggestion | output schema/service/database JSON validator/frontend defensive bound |
| one AI call, 30 seconds, zero retries | run call_count CHECK/CAS, provider adapter deadline, no retry loop |
| three database attempts | service transaction runner only; bounded retryable SQL states; idempotency replay |
| pagination 20 default/100 max | query schemas and repository limit+1; protected content fixed 20; UI cursor pager |

No layer silently truncates a semantically meaningful engineering set. It rejects with an explicit bounded failure before mutation or provider egress.

## 27. Migration contracts

### Migration 1 — UNASSIGNED_patch_054_standards_foundation

Creates the 11 standards tables, deferred cross-table FKs, CHECK/unique/partial/query indexes, immutable-history and single-head triggers, tenant/project consistency functions, resource-count functions, JSON/digest validators, grants/revocations, and runtime column privileges described above. It seeds no catalog, rights, source, assertion, or provider data. Its down_revision MUST be the verified Alembic head at implementation-plan authorization time; currently that head is e05300000002.

### Migration 2 — UNASSIGNED_patch_054_technical_report_standards

Is the linear successor of Migration 1. It adds the eight nullable standards-basis columns and FKs to technical_report_provenance_entries; extends the existing standard-source coherence check so canonical reference_only may be non-material while legacy locators remain material; installs the legacy/new exclusive-or and post-cutover new-legacy-write guard; extends provenance count, accepted_snapshot, historical basis, draft-revision/acceptance cutover, and accepted immutability validators; and applies exact runtime column grants. It adds no Technical Report enum value and does not rewrite any legacy StandardLocator or accepted report. A legacy-bearing draft remains readable but cannot be revised or accepted until the locator is removed or canonically replaced.

Revision IDs remain UNASSIGNED because repository IDS practice allocates them during authorized implementation planning/implementation, not IDS. The two revisions must be linear and may not branch from e05300000002.

Upgrade safety: both migrations are transactional; nullable report columns precede constraints; NOT VALID cross-table constraints are validated before commit where PostgreSQL permits; locks use bounded lock_timeout and statement_timeout; functions are replaced atomically; clean install and upgrade yield identical schema/grants. Downgrade is fail-closed: Migration 2 aborts if any new standards basis exists; Migration 1 aborts if any standards table is non-empty or referenced. No destructive automatic conversion/drop of retained data is permitted. Rollback of application code before Migration 2 is prohibited once new provenance exists.

## 28. Exact 96-vector implementation map

Evidence abbreviations in this table are exact manifest paths from section 29: enums means backend/app/enums/standards.py; schemas means backend/app/schemas/standards.py; models means backend/app/models/standards.py and standards_command.py; service means backend/app/services/standards_service.py; UoW means backend/app/repositories/standards_unit_of_work.py; repository means backend/app/repositories/standards_repository.py; API means standards dependency/router; report means the listed Technical Report modifications; AI means backend/app/ai/standards_intelligence.py; FE means the PATCH-054 frontend files; M1/M2 mean the two unassigned migration paths. Each vector requires both the named implementation seam and the named test evidence; no range is accepted by inference alone.

### Identity and edition — 8

| Vector | Implementation evidence | Test evidence |
|---|---|---|
| P054-ID-01 | global identity registration: policy, canonical key, immutable row/event | contracts/service/API test global success and atomic fault |
| P054-ID-02 | organization_private uniqueness includes organization_id | repository/API test same key succeeds independently without disclosure |
| P054-ID-03 | exact dash/NFKC/whitespace/casefold collision | contracts/repository test variant returns CONFLICT and no row |
| P054-ID-04 | exact edition creation plus initial standing under identity lock | service/repository test edition 64 succeeds and identity is unchanged |
| P054-ID-05 | service plus M1 64-edition guard | performance/migration test edition 65 returns RESOURCE_LIMIT_EXCEEDED |
| P054-ID-06 | edition disambiguator and duplicate rules | contracts/service test EDITION_UNRESOLVED or CONFLICT |
| P054-ID-07 | append-only standing/single-head UoW and event | service/migration test V1 immutable and V2 current |
| P054-ID-08 | CAT-02 exact historical identity/edition/observation lookup | API/repository test no latest-edition substitution |

### Rights — 12

| Vector | Implementation evidence | Test evidence |
|---|---|---|
| P054-RGT-01 | metadata_only capability validator denies protected use | contracts/security test safe metadata only |
| P054-RGT-02 | customer_supplied_declared all-false defaults | service/security test possession grants nothing and AI prohibited |
| P054-RGT-03 | seven independent organization_license booleans | service test only retrieval/display succeed in fixture |
| P054-RGT-04 | open_distribution all-false defaults | service test no inferred legal permission |
| P054-RGT-05 | internally_authored explicit capabilities plus local_only | service/AI test configured operations and local processor only |
| P054-RGT-06 | unknown RightsBasis fail-closed evaluator | security test RIGHTS_UNKNOWN and no bytes/result |
| P054-RGT-07 | effective_until and expired successor | service test RIGHTS_EXPIRED and retained safe history |
| P054-RGT-08 | serialized revoked successor/live recheck | security test RIGHTS_REVOKED across retrieval/display/index/AI |
| P054-RGT-09 | unknown RightsStatus fail closed | service test RIGHTS_UNKNOWN |
| P054-RGT-10 | prohibited/local_only/approved_processor matrix | AI test exact permitted processor and zero denied calls |
| P054-RGT-11 | sole Organization/edition/provider tuple | retrieval/security test provider B cannot use provider A right |
| P054-RGT-12 | separate derived retention/current-use booleans | assertion test retention succeeds and current reasoning is denied |

### Authorization and tenancy — 10

| Vector | Implementation evidence | Test evidence |
|---|---|---|
| P054-AUTH-01 | private catalog filtering before search/count | security/API test Organization B sees absent-equivalent shape/count |
| P054-AUTH-02 | scoped CAT-02 direct lookup | security test foreign private edition returns PROTECTED_NOT_FOUND |
| P054-AUTH-03 | RGT-01 authorization before count/page | security/API test no foreign rights count hint |
| P054-AUTH-04 | signed tenant/project source handle and protected lookup | security test forged foreign snapshot yields no bytes/metadata |
| P054-AUTH-05 | signed/scoped assertion lookup | security test foreign assertion returns PROTECTED_NOT_FOUND |
| P054-AUTH-06 | report-owner intersection before candidate formation | report/security test foreign protected candidate and count absent |
| P054-AUTH-07 | authorization before standards/report idempotency replay | API/security test cross-tenant key returns no prior result |
| P054-AUTH-08 | auth before protected identifier/body validation | API test malformed foreign request is no validator oracle |
| P054-AUTH-09 | configuration/applicability are selectors only | security test configured edition without rights cannot retrieve/AI |
| P054-AUTH-10 | M1/M2 runtime grants and DB tenant/immutability guards | real PostgreSQL security test rejects direct bypass |

### Applicability — 8

| Vector | Implementation evidence | Test evidence |
|---|---|---|
| P054-APP-01 | package hook exact candidate/provenance adapter | package integration test bounded advisory-only output |
| P054-APP-02 | APP-03 design_basis Human declaration UoW | service/API test append head/event with expected revision |
| P054-APP-03 | declared_not_applicable append path | service test candidate/history preserved and Human wins |
| P054-APP-04 | mandatory role/source schema and Human predicate | contracts/service test valid attributable mandatory declaration |
| P054-APP-05 | mandatory no-inference validator | service test AI/package/missing source returns INVALID_REQUEST/no event |
| P054-APP-06 | exact-edition requirement | API test designation-only declaration returns EDITION_UNRESOLVED |
| P054-APP-07 | retire then successor append lineage | service/migration test prior row unchanged and one new head |
| P054-APP-08 | expected revision plus single-head lock/CAS | repository concurrency test one winner/one VERSION_CONFLICT |

### Retrieval and source — 10

| Vector | Implementation evidence | Test evidence |
|---|---|---|
| P054-RET-01 | SRC-01 active retrieval/storage path and immutable snapshot | retrieval test material receipt/digests/rights-at-use |
| P054-RET-02 | reference_only safe metadata handle path | retrieval/API test no text or material claim without protected rights |
| P054-RET-03 | static provider registry and no client URL port | retrieval test INVALID_REQUEST and zero network calls |
| P054-RET-04 | request count plus 32768 aggregate precheck | retrieval test 9th fragment/plus-one byte fails with no partial result |
| P054-RET-05 | provider immutable token/digest attestation | retrieval test exact re-resolution qualifies material_support |
| P054-RET-06 | snapshot-or-qualifying-handle exclusive rule | retrieval test SOURCE_INCOMPLETE; no silent materiality downgrade |
| P054-RET-07 | digest verification before persist/display | retrieval test INTEGRITY_FAILURE blocks display/assertion/AI |
| P054-RET-08 | SRC-02 fresh display authorization | API/security test masked DISPLAY_NOT_PERMITTED with safe provenance |
| P054-RET-09 | rights/retrieval tuple locking and final check | real concurrent test releases no bytes when revocation wins |
| P054-RET-10 | material exact location/content completeness checks | retrieval/report test SOURCE_INCOMPLETE and zero partial candidates |

### Assertions — 8

| Vector | Implementation evidence | Test evidence |
|---|---|---|
| P054-AST-01 | four closed assertion representations and no fifth kind | contracts/assertion test all create unverified under retain right |
| P054-AST-02 | Human verification UoW with exact digest/rationale | assertion test append actor-attributed human_verified state |
| P054-AST-03 | assertion API/domain has no compliance/applicability/approval projection | assertion test rejects authority query or returns advisory only |
| P054-AST-04 | AssertionOrigin ai_assisted plus unverified invariant | AI/assertion test AI cannot self-verify |
| P054-AST-05 | expected-version append-only rejection | assertion/migration test prior state immutable and rejected successor |
| P054-AST-06 | rights-loss live evaluation and stale event | assertion/report test masked STALE_ASSERTION; accepted Report unchanged |
| P054-AST-07 | newer active retain/current-use eligibility evaluation | assertion test unchanged human_verified digest can regain current eligibility |
| P054-AST-08 | provider-handle digest revalidation | assertion test integrity loss appends/evaluates stale and blocks material use |

### Technical Report — 12

| Vector | Implementation evidence | Test evidence |
|---|---|---|
| P054-RPT-01 | deterministic stable safe RPT-01 candidates | report test mixed eligibility and hidden-count suppression |
| P054-RPT-02 | RPT-02 opaque selection/server composition | report test new revision and forged raw provenance rejection |
| P054-RPT-03 | schema/service/DB post-cutover locator guard | report/API test LEGACY_STANDARD_LOCATOR_PROHIBITED/INVALID_REQUEST |
| P054-RPT-04 | unchanged accepted legacy snapshot read | migration/report test byte-identical legacy_unattested_reference |
| P054-RPT-05 | legacy-bearing draft conversion guard | report test revise/accept fails legacy_conversion_required |
| P054-RPT-06 | all 13 acceptance rechecks and atomic snapshot/events | report test single successful ADR-023 acceptance boundary |
| P054-RPT-07 | final material validity all-or-nothing | report test revoked/source/assertion failure leaves draft/history unchanged |
| P054-RPT-08 | expected revision and Report lock | real concurrency test revision vs acceptance has one winner |
| P054-RPT-09 | final rights/applicability version recheck | report concurrency test changes fail closed with no snapshot |
| P054-RPT-10 | noncurrent standing acknowledgement/applicability rules | report test first blocked then attributable Human path allowed |
| P054-RPT-11 | frozen historical/current-access split | report/API/UI test lawful basis remains and excerpt is masked |
| P054-RPT-12 | successor provenance copy guard | report test legacy locator is not copied and canonical selection required |

### AI — 8

| Vector | Implementation evidence | Test evidence |
|---|---|---|
| P054-AI-01 | prohibited decision before dispatch | AI test not_permitted and provider call count zero |
| P054-AI-02 | local_only processor-class check | AI test external selection returns AI_USE_NOT_PERMITTED/zero calls |
| P054-AI-03 | approved_processor exact policy membership | AI test one bounded permitted provider/model call |
| P054-AI-04 | deterministic result persisted independently of provider | AI test timeout returns unavailable, unchanged deterministic result, one call |
| P054-AI-05 | scoped handles and 32768-byte pre-egress check | AI test unauthorized/oversize input causes zero calls |
| P054-AI-06 | closed known-handle/clause subset output | AI test invented ID rejects entire result as invalid_output |
| P054-AI-07 | authority-claim rejection | AI test compliance/mandatory/approval/acceptance claim rejects all suggestions |
| P054-AI-08 | untrusted-data delimiter and no tools/secrets | adversarial injection test yields known-handle advisory only |

### Audit and idempotency — 6

| Vector | Implementation evidence | Test evidence |
|---|---|---|
| P054-AUD-01 | catalog commands stage exact identity/edition/standing events | conformance/service test names, versions, digests, order, atomic fault |
| P054-AUD-02 | rights UoWs stage exact create/replace/expire/revoke families | conformance/service rollback test preserves mutation/event atomicity |
| P054-AUD-03 | retrieval metadata-only payload builder | security test success/unavailable/snapshot events contain no text/key/diagnostic |
| P054-AUD-04 | applicability/assertion event builders | conformance test exact transitions, actors, digests |
| P054-AUD-05 | requested plus terminal AI events and retained interaction | AI/security test safe provider/digests only for all outcomes |
| P054-AUD-06 | report-owned attachment/acceptance events | report test safe basis aggregate digest and no protected bytes |

### UX — 6

| Vector | Implementation evidence | Test evidence |
|---|---|---|
| P054-UX-01 | router contract exposes exactly 22 bounded operations | conformance/API test no browser/scraper/raw-text/bulk endpoint |
| P054-UX-02 | registry and rights surfaces | registry/rights tests keyboard flows and exact scope/status/capabilities |
| P054-UX-03 | applicability and Report surfaces | project/report tests make Human authority/materiality/legacy states explicit |
| P054-UX-04 | AI and protected-state presentation | intelligence/API-state tests retain deterministic result and clear masked data |
| P054-UX-05 | all six surface semantics | accessibility test names/focus/live status/logical order |
| P054-UX-06 | responsive RTL/LTR isolation | RTL test logical mirror, LTR identifiers, narrow viewport/no clipping |

### Limits — 4

| Vector | Implementation evidence | Test evidence |
|---|---|---|
| P054-LIM-01 | 64 editions and 64 current declaration heads | performance/migration tests at limit and reject 65 without mutation |
| P054-LIM-02 | 16 bases, 32 provenance, 8 fragments | report/retrieval tests at limit and reject plus-one without truncation |
| P054-LIM-03 | 8192/32768 bytes, 32 assertions, 12 suggestions | retrieval/assertion/AI plus-one tests reject before unsafe use |
| P054-LIM-04 | 1 call/30s/0 AI retry/3 DB attempts/20–100 pages | AI/API/performance instrumentation tests every boundary |

### Database — 4

| Vector | Implementation evidence | Test evidence |
|---|---|---|
| P054-DB-01 | M1 lifecycle and exact security/schema contract | real PostgreSQL clean/install upgrade equivalence with no invented rows |
| P054-DB-02 | M2 legacy cutover/accepted immutability | PG fixtures preserve accepted bytes, expose draft conversion, reject new/update |
| P054-DB-03 | global lock/CAS/final-check matrix | real paired rights/retrieval/applicability/assertion/report concurrency tests |
| P054-DB-04 | auth-before-replay, digest conflict, three attempts, no AI retry | PG/API idempotency and forced transient-conflict tests |

Vector count is exactly 96: 8 + 12 + 10 + 8 + 10 + 8 + 12 + 8 + 6 + 6 + 4 + 4.

## 29. Exact implementation file manifest — 71 unique paths

This is discovery and ownership only. None of these implementation paths is modified by this IDS. UNASSIGNED is a placeholder, not a revision allocation.

| # | Classification | Batch | Exact path | Reuse/new purpose |
|---:|---|---|---|---|
| 1 | NEW | B1 | backend/app/enums/standards.py | closed PATCH-054 vocabularies |
| 2 | NEW | B1/B2/B3 | backend/app/schemas/standards.py | API/domain contracts |
| 3 | NEW | B1/B2/B3/B5 | backend/app/models/standards.py | ORM projections and reads |
| 4 | NEW | B1/B2/B3/B5 | backend/app/models/standards_command.py | immutable commands/value objects |
| 5 | NEW | B1/B2/B3/B5 | backend/app/ports/standards.py | repository/UoW/provider/AI ports |
| 6 | NEW | B1/B2/B3/B5 | backend/app/repositories/standards_repository.py | scoped persistence |
| 7 | NEW | B1/B2/B3/B5 | backend/app/repositories/standards_unit_of_work.py | transactions/locks/audit/outbox |
| 8 | NEW | B1/B2/B3/B5 | backend/app/services/standards_service.py | deterministic application service |
| 9 | NEW | B1/B2/B3/B5 | backend/app/dependencies/standards.py | composition/auth policy/handles |
| 10 | NEW | B1/B2/B3/B5 | backend/app/api/v1/routers/standards.py | 19 new standards operations |
| 11 | NEW | B1 | backend/app/standards/__init__.py | package boundary |
| 12 | NEW | B1 | backend/app/standards/canonical.py | normalization/canonical digest |
| 13 | NEW | B1/B4/B5 | backend/app/standards/handles.py | signed opaque handles |
| 14 | NEW | B1/B2/B5 | backend/app/standards/providers.py | static provider/admin policy registry |
| 15 | NEW | B2 | backend/app/adapters/standard_source_object_store.py | private exact-key object wrapper |
| 16 | NEW | B2 | backend/app/adapters/standard_source_providers.py | official/licensed/customer adapters |
| 17 | NEW | B3 | backend/app/adapters/standards_package_candidates.py | package-hook adapter |
| 18 | NEW | B5 | backend/app/adapters/standards_cross_discipline.py | PATCH-053 safe projection |
| 19 | NEW | B5 | backend/app/ai/standards_intelligence.py | safe AI port implementation |
| 20 | MODIFY | B1/B2/B5 | backend/app/core/config.py | allowlist/provider/object/AI settings |
| 21 | MODIFY | B1 | backend/app/main.py | router and dependency composition |
| 22 | MODIFY | B4/B5 | backend/app/ai/technical_report_assistant.py | replace raw legacy standards context with authorized safe handles |
| 23 | MODIFY | B4 | backend/app/models/technical_report_command.py | StandardHistoricalBasisV1 |
| 24 | MODIFY | B4 | backend/app/models/technical_report.py | aggregate validation/serialization |
| 25 | MODIFY | B4 | backend/app/ports/technical_report.py | standards lookup/final-check ports |
| 26 | MODIFY | B4 | backend/app/repositories/technical_report_repository.py | new provenance persistence |
| 27 | MODIFY | B4 | backend/app/repositories/technical_report_unit_of_work.py | locks/rechecks/events |
| 28 | MODIFY | B4 | backend/app/services/technical_report_service.py | revision/acceptance integration |
| 29 | MODIFY | B4 | backend/app/schemas/technical_report.py | public basis schemas/legacy guard |
| 30 | MODIFY | B4 | backend/app/api/v1/routers/technical_reports.py | RPT-01/RPT-02 and RPT-03 extension |
| 31 | MODIFY | B3 | backend/app/discipline_packages/contributions.py | bounded hook validation |
| 32 | MODIFY | B3 | backend/app/discipline_packages/descriptors/eic_v1.py | deterministic standards candidates |
| 33 | MIGRATION | B1 | backend/migrations/versions/<UNASSIGNED_M1>_patch_054_standards_foundation.py | 11-table foundation/security |
| 34 | MIGRATION | B4 | backend/migrations/versions/<UNASSIGNED_M2>_patch_054_technical_report_standards.py | report provenance integration |
| 35 | TEST | B1 | backend/tests/test_standards_contracts.py | enums/value objects/normalization |
| 36 | TEST | B1/B2/B3 | backend/tests/test_standards_service.py | deterministic rules/UoWs |
| 37 | TEST | B1/B2/B3 | backend/tests/test_standards_repository.py | scope/locking/idempotency/outbox |
| 38 | TEST | B1/B2/B4/B5 | backend/tests/test_standards_security.py | tenant/rights/DB/egress attacks |
| 39 | TEST | B1/B2/B3/B5 | backend/tests/test_standards_api.py | exact route/status contracts |
| 40 | TEST | B2 | backend/tests/test_standards_retrieval.py | provider/object/limit behavior |
| 41 | TEST | B2 | backend/tests/test_standards_assertions.py | assertion lifecycle/propagation |
| 42 | TEST | B5 | backend/tests/test_standards_ai.py | composition/provider/phases |
| 43 | TEST | B5 | backend/tests/test_standards_conformance.py | exact 96-vector inventory |
| 44 | TEST | B1/B4 | backend/tests/test_standards_migrations.py | clean/upgrade/grants/downgrade |
| 45 | TEST | B4 | backend/tests/test_technical_report_standards.py | legacy/revision/acceptance/history |
| 46 | TEST | B3 | backend/tests/test_standards_package_integration.py | hook and descriptor integration |
| 47 | TEST | B5 | backend/tests/test_standards_performance.py | bounded queries/resources/concurrency |
| 48 | FRONTEND | B5 | frontend/src/api/types.ts | standards DTOs and ApiResult state |
| 49 | FRONTEND | B5 | frontend/src/api/client.ts | 403 restricted/protected mapping |
| 50 | FRONTEND | B5 | frontend/src/App.tsx | routes |
| 51 | FRONTEND | B5 | frontend/src/components/AppShell.tsx | navigation/permission presentation |
| 52 | FRONTEND | B5 | frontend/src/pages/StandardsPages.tsx | registry page composition |
| 53 | FRONTEND | B5 | frontend/src/pages/OrganizationAdminPage.tsx | rights surface integration |
| 54 | FRONTEND | B5 | frontend/src/pages/ProjectsPage.tsx | applicability/source/assertion integration |
| 55 | FRONTEND | B5 | frontend/src/pages/ReportPages.tsx | report basis/intelligence integration |
| 56 | FRONTEND | B5 | frontend/src/components/StandardsRegistryPanel.tsx | surface 1 |
| 57 | FRONTEND | B5 | frontend/src/components/OrganizationStandardsRightsPanel.tsx | surface 2 |
| 58 | FRONTEND | B5 | frontend/src/components/ProjectStandardsPanel.tsx | surfaces 3 and 4 |
| 59 | FRONTEND | B5 | frontend/src/components/TechnicalReportStandardsBasisPanel.tsx | surface 5 |
| 60 | FRONTEND | B5 | frontend/src/components/StandardsIntelligencePanel.tsx | surface 6 |
| 61 | FRONTEND | B5 | frontend/src/components/StandardsStatePresentation.tsx | shared safe state/a11y rendering |
| 62 | FRONTEND | B5 | frontend/src/styles.css | logical properties/RTL/state styling |
| 63 | TEST | B5 | frontend/src/test/standards-registry.test.tsx | registry contract |
| 64 | TEST | B5 | frontend/src/test/standards-rights.test.tsx | rights contract |
| 65 | TEST | B5 | frontend/src/test/project-standards.test.tsx | applicability/source/assertion contract |
| 66 | TEST | B5 | frontend/src/test/report-standards.test.tsx | report basis/historical contract |
| 67 | TEST | B5 | frontend/src/test/standards-intelligence.test.tsx | advisory contract |
| 68 | TEST | B5 | frontend/src/test/standards-accessibility-rtl.test.tsx | keyboard/screen reader/RTL |
| 69 | TEST | B5 | frontend/src/test/api-client-standards-states.test.ts | protected/restricted state mapping |
| 70 | GOVERNANCE | B1/B5 | docs/patches/PATCH-054.md | patch evidence/status only |
| 71 | GOVERNANCE | B5 | docs/19_Governance_Model.md | register governed capability after evidence |

Manifest rules: paths are the complete expected maximum scope. A future authorized implementation plan may narrow a batch but may not add a path without Human-approved manifest amendment. Existing unrelated dirty files are not absorbed. The IDS file itself is not an implementation path and is not counted.

## 30. Five-batch technical ownership

### Batch 1 — registry, edition, and rights foundation

Owns core contracts/composition, catalog and rights commands/queries, M1, shared standards UoW/idempotency/outbox/audit, PostgreSQL grants, and foundation tests. Depends only on accepted authority and current Alembic head. Acceptance evidence: CAT/RGT contract tests; Unicode uniqueness; single-head concurrency; time-window/precedence matrices; direct SQL immutability/grant tests; exact M1 schema; no tenant disclosure.

### Batch 2 — authorized retrieval and assertions

Owns provider/object adapters, bounded retrieval, immutable snapshots, typed assertions, human verification, revocation/stale propagation, and SRC/AST evidence. Depends on Batch 1 rights and persistence. Acceptance evidence: 8192/8193 and clean-scan boundaries; exact-key/no-public-URL tests; cross-project denial; closed assertion payloads; human-only verification; 32/33 limit; revocation during use; audit/outbox atomicity.

### Batch 3 — project applicability and package integration

Owns APP routes/transactions, candidate/declaration separation, package adapter and EIC descriptor contribution. Depends on Batch 1 catalog and rights; it does not depend on retrieval. Acceptance evidence: deterministic package candidates; no automatic applicability; one-head and 64-head races; tenant/project authorization; package version/registration failure behavior.

### Batch 4 — Technical Report provenance and historical compatibility

Owns all Technical Report modifications and M2. Depends on Batches 1–3 and the existing Report authority. Acceptance evidence: byte-identical accepted legacy reads; legacy-bearing draft conversion requirement; rejection of new legacy locators and acceptance without conversion; reference_only/material_support matrix; forged handle/basis rejection; revocation between revision and acceptance; accepted immutability; exact 16/32 limits; migration upgrade/downgrade safety.

### Batch 5 — AI, frontend, cumulative validation, security, and performance

Owns AI adapter/phases, PATCH-053 projection, all six frontend surfaces, 96-vector conformance, cumulative adversarial security, concurrency/resource/performance evidence, and governance closure. Depends on Batches 1–4. Acceptance evidence: injection and egress denial; one-call/30-second/zero-retry proof; no DB lock across network; current-rights finalization; protected/restricted UI matrix; keyboard/RTL checks; exact events/routes/vectors; query bounds; full backend/frontend suites. Governance may move to accepted/implemented only after Human-authorized implementation and review.

## 31. PATCH-055+ boundary

This IDS introduces no general Evidence Workbench, broad retention governance, Methods & Systems, Command Center completion, commercial authentication/release work, seat or license enforcement, deployment qualification, generalized provider marketplace, generic document ingestion, or whole-standard repository. It does not alter PATCH-053 ownership. PATCH-055 and later remain NOT STARTED and NOT AUTHORIZED.

## 32. Independent implementation-design review

Review method: after the implementation design was drafted, a separate requirements-to-design pass compared it against the accepted Discovery, ADR-027, EDS-054, actual repository seams, current Alembic head, Technical Report authority, rights/copyright and tenant boundaries, PostgreSQL privileges, AI egress/transactions, historical immutability, concurrency, migrations, resource ceilings, all 96 vectors, all five batches, and PATCH-055+ exclusions.

### Findings

| Severity | Count | Finding and disposition |
|---|---:|---|
| Critical | 0 | None. |
| Major | 0 | None. |
| Minor | 0 | None unresolved. |
| Observation | 2 | OBS-01: the repository has no platform-admin role. Reconciled locally with an existing-admin plus deployment allowlist policy that defaults empty; no Role/auth scope expansion. OBS-02: migration IDs remain unassigned under repository IDS practice; linear dependency and current verified head are frozen. |

IDS-local reconciliation log: the review copied the EDS closed vocabularies and failure codes verbatim, removed an initially considered but unauthorized Project-scoped rights override so the only tuple is Organization/edition/provider, and enforced the accepted strict legacy cutover (legacy drafts are readable but cannot be revised or accepted without conversion). These corrections change no accepted authority and leave no open finding.

Review checks:

- Authority: no Discovery/ADR/EDS semantics changed; no reopen required.
- Repository fit: existing auth, project/workspace, report, object-store, audit, package, AI, cursor, and frontend seams are reused.
- Rights/copyright: no public URL, bulk retrieval, raw-source AI egress, content in audit/outbox, or rights bypass exists.
- Tenant isolation: organization/project filters precede domain disclosure and are rechecked in final transactions.
- Database security: immutable history, restricted runtime columns, no DELETE, fixed search_path, and direct SQL tests are explicit.
- Historical safety: legacy locators and accepted reports are unchanged; new bases are frozen snapshots.
- Concurrency: single heads, global lock order, version CAS, at most three DB attempts, and no lock across network I/O are frozen.
- AI: one call, 30 seconds, zero retries, strict I/O, prompt-injection boundary, and revoked-rights output suppression are explicit.
- Traceability: exactly 22 events, 22 API operations, six surfaces, two migrations, 96 vectors, and 71 manifest paths are enumerated.
- Scope: five batches are technically separated and PATCH-055+ is untouched.

Verdict: PASS WITH OBSERVATIONS. IDS-054 is implementation-ready as a design artifact, subject to Human acceptance and a separately authorized Implementation Plan. Unresolved implementation-design questions: none. ADR/EDS reopen required: NO.

## 33. Stop condition

This artifact ends IDS-054. It authorizes no implementation, migration creation, staging, commit, push, Implementation Plan, or PATCH-055+ activity.

## Status reconciliation — 2026-09-14

Human IDS acceptance is **PASS / ACCEPTED / AUTHORITATIVE**. The opening draft wording is retained as historical pre-acceptance metadata and is superseded by this append-only reconciliation. No implementation-design semantics are changed.
