# IDS-032 — Technical Report

## 1. Document Control

| Field | Value |
|---|---|
| Document ID | IDS-032 |
| Title | Technical Report Implementation Design |
| Related PATCH | PATCH-032 — Technical Report |
| Governing ADR | ADR-023 — Human-Accepted AI-Assisted Technical Reports as the SATCO V1 Engineering Authority Boundary |
| Governing EDS | EDS-032 — Technical Report — ACCEPTED / COMPLETE |
| Status | ACCEPTED / COMPLETE |
| Owner | SATCO Product Owner / Platform Architecture |
| Architecture style | Docs-First / Clean Architecture |
| IDS-032 design authority | GRANTED |
| Human IDS acceptance | PASS |
| Implementation Plan authority | GRANTED |
| Implementation authority | NOT GRANTED |
| Date | 2026-08-09 |

## 2. Purpose and Authority Boundary

This IDS maps the accepted Technical Report design to the current SATCO backend
architecture. It defines implementation contracts, persistence shape, ports,
application use cases, transport behavior, security, atomicity, file boundaries,
and verification requirements. It does not implement them.

ADR-023, PATCH-032, and EDS-032 remain authoritative. The initial Independent
EDS Review failure remains historical; the focused amendment, Focused
Independent EDS-032 Re-review `PASS`, Human EDS Acceptance `PASS`, and
governance reconciliation `PASS` establish the accepted input to this IDS.

Implementation, migration execution, commit, push, and deployment authority
remain `NOT GRANTED`.

## 3. Repository Pattern Baseline

IDS-032 uses these verified repository conventions:

- FastAPI routers under `backend/app/api/v1/routers/` remain thin;
- Pydantic v2 schemas use `ConfigDict` and reject unapproved fields;
- public aggregate identities use PostgreSQL UUIDs;
- User, Workspace, and Project identifiers remain positive integers;
- Organization identity is a UUID derived from trusted active membership;
- SQLAlchemy models are aggregate-aware and expose explicit command methods;
- command contracts are framework-independent immutable dataclasses;
- inward ports use `Protocol` contracts;
- repositories load and persist but never authorize, commit, or publish events;
- application services authorize before disclosure and invoke aggregate behavior;
- a capability-owned Unit of Work owns one SQLAlchemy transaction;
- Audit, outbox events, idempotency result, and aggregate changes commit atomically;
- post-creation mutation uses expected-version compare-and-change;
- stable `SatcoException` subclasses map application outcomes to transport;
- routers construct request-scoped dependencies from
  `AuthenticatedOrganizationContext`;
- Alembic exclusively owns schema evolution.

The current migration graph identifies `e02800000001` as the repository head by
revision evidence. A future implementation must reverify the single head before
creating a migration; this IDS does not execute Alembic.

## 4. Bounded Context and Dependency Direction

The Technical Report capability owns its Aggregate, command contracts,
application ports, persistence adapters, application service, and transport
adapter. Dependency direction is:

```text
Technical Report domain and command contracts
↓
Technical Report application ports and schemas
↓
Technical Report application service
↓
SQLAlchemy / canonical-capability adapters
↓
FastAPI transport composition
```

The domain and application layers do not depend on FastAPI, HTTP, ORM sessions,
or provider-specific AI clients. Canonical Project, Workspace, Capture,
Evidence, EngineeringObject, and Engineering Relationship capabilities do not
depend on Technical Report.

## 5. Domain Model Mapping

### 5.1 Aggregate Root

`TechnicalReport` is the only Technical Report Aggregate Root. No Review,
lineage, provenance, acceptance, or AI Aggregate is introduced.

The root owns:

- UUID `id`;
- trusted `organization_id`;
- mandatory positive `workspace_id`;
- optional positive direct `project_id`;
- immutable positive `owner_id`, set to the authenticated creating Human;
- `purpose` from the closed V1 vocabulary;
- `engineering_scope`;
- working draft fields;
- UUID `draft_revision_id`;
- positive integer Aggregate `version`;
- preliminary qualification and disclosed deficiencies;
- report-owned provenance/reliance entries;
- lifecycle `draft` or `accepted`;
- optional successor-owned `predecessor_report_id`;
- immutable accepted snapshot and Human acceptance record.

`owner_id` is the V1 accountable Human Owner reference required by the accepted
single-Human-first boundary. It is server-controlled, immutable, and never
accepted from a client. Self-review follows because that same Human may create,
revise, direct AI assistance, review, and accept.

### 5.2 Value Objects

Framework-independent frozen value objects are:

- `TechnicalReportActor(actor_id, organization_id)`;
- `TechnicalReportPurpose`;
- `TechnicalReportLifecycle`;
- `TechnicalReportDraftRevision`;
- `PreliminaryQualification`;
- `TechnicalReportContent` containing scope, technical content, assumptions,
  uncertainty, limitations, conclusions, and recommendations;
- `ProvenanceEntry` with one deterministic EDS-032 source class;
- `AcceptanceConfirmation` containing expected pre-acceptance version, exact
  draft revision, and explicit Human confirmation;
- `TechnicalReportAcceptedSnapshot`;
- `TechnicalReportAcceptanceRecord`;
- `TechnicalReportCommandMetadata` containing trusted actor, rationale,
  correlation ID, idempotency ID, and command ID.

These are domain/application contracts, not transport or ORM representations.

### 5.3 Aggregate Commands

Only these state-changing commands are authorized:

- `CreateTechnicalReportDraft`;
- `ReviseTechnicalReportDraft`;
- `AcceptExactTechnicalReportDraft`;
- `CreateTechnicalReportSuccessor`.

`RequestTechnicalReportAIDraftProposal` is an application request, not an
Aggregate command. It produces a non-authoritative proposal and no Aggregate
mutation. A Human must submit a separate `ReviseTechnicalReportDraft` command
to incorporate any proposal.

There is no generic update, delete, abandon, archive, publish, approve,
supersede, metadata-correction, or post-acceptance mutation command.

### 5.4 Invariant Ownership

| Layer | Exclusive responsibility |
|---|---|
| Domain | lifecycle, purpose, exact draft-revision advancement, accepted terminality, acceptance binding, immutable snapshot creation, successor-owned lineage, no inherited acceptance, preliminary qualification coherence, post-acceptance mutation rejection |
| Application | trusted actor construction, operation authorization, canonical reference resolution, historical-resolvability validation, idempotency, protected-not-found, atomic coordination, response disclosure |
| Persistence | FK integrity, nullability, closed stored vocabularies, positive versions, lifecycle/acceptance-column coherence, uniqueness, expected-version compare-and-change, transaction durability |
| Transport | syntax, types, required headers, body coherence, bounded pagination, stable error mapping |

Business policy is not duplicated across layers. Database constraints defend
stored coherence but do not become the source of lifecycle authority.

## 6. Closed Vocabularies

`TechnicalReportLifecycle` contains exactly:

- `draft`;
- `accepted`.

`TechnicalReportPurpose` contains exactly:

- `field_experience`;
- `troubleshooting`;
- `engineering_analysis`;
- `technical_recommendation`.

`TechnicalReportSourceClass` contains exactly:

- `canonical_material`;
- `external_or_human_material`;
- `standards_material`;
- `contextual_non_material`.

Verification and availability are explicit recorded facts, not authority
states. They use closed values defined in the Technical Report enum module and
must include `verified`/`unverified` and `available`/`unavailable` without
silently inferring missing information.

## 7. Persistence Model

### 7.1 `technical_reports`

| Column | Type / rule | Ownership |
|---|---|---|
| `id` | UUID PK | server-created immutable identity |
| `organization_id` | UUID FK `organizations.id`, RESTRICT, not null | trusted scope |
| `workspace_id` | integer FK `engineering_workspaces.id`, RESTRICT, not null | authorized scope |
| `project_id` | integer FK `projects.id`, RESTRICT, nullable | optional direct context |
| `owner_id` | integer FK `users.id`, RESTRICT, not null | authenticated creating Human |
| `purpose` | varchar, not null, closed check | Aggregate |
| `engineering_scope` | text, not null | draft/accepted content |
| `draft_content` | text, not null | mutable only while draft |
| `assumptions` | JSON, not null | typed string collection |
| `uncertainty` | text, not null | explicit content |
| `limitations` | JSON, not null | typed string collection |
| `conclusions` | text, not null | draft/accepted content |
| `recommendations` | JSON, not null | typed string collection |
| `is_preliminary` | boolean, not null | qualification flag |
| `evidence_deficiencies` | JSON, not null | typed string collection |
| `unresolved_issues` | JSON, not null | typed string collection |
| `follow_up_requirements` | JSON, not null | typed string collection |
| `draft_revision_id` | UUID, not null | exact current draft revision |
| `lifecycle` | varchar, default `draft`, closed check | Aggregate state |
| `predecessor_report_id` | UUID self-FK, RESTRICT, nullable | owned exclusively by successor |
| `version` | integer, not null, `>= 1` | concurrency version |
| `accepted_snapshot` | JSON, nullable | typed immutable snapshot serialization |
| `accepted_by_id` | integer FK `users.id`, nullable | accepting Human |
| `accepted_at` | timezone timestamp, nullable | server clock |
| `accepted_draft_revision_id` | UUID, nullable | exact accepted revision |
| `accepted_aggregate_version` | integer, nullable | resulting post-acceptance version |
| `created_at` | timezone timestamp, not null | server-controlled |
| `updated_at` | timezone timestamp, not null | server-controlled |

The JSON fields serialize named typed value objects; untyped arbitrary mappings
are prohibited at schema and command boundaries. JSON is used consistently with
existing outbox/idempotency patterns and avoids creating unrelated document or
standards repositories.

Required checks include:

- lifecycle and purpose closed values;
- positive `version` and accepted version;
- predecessor differs from report identity;
- `accepted` if and only if accepted snapshot, accepting Human, acceptance
  timestamp, accepted draft revision, and accepted Aggregate version are all
  present;
- accepted Aggregate version equals stored current version;
- draft rows contain none of the acceptance columns;
- preliminary rows preserve non-empty limitation/basis information required by
  the domain command before acceptance.

### 7.2 `technical_report_provenance_entries`

Each row is an Aggregate-owned manifest entry:

- UUID `id` and UUID FK `technical_report_id` with RESTRICT;
- deterministic `ordinal`, unique per report;
- closed `source_class` and `source_type`;
- `is_material`;
- canonical owning capability;
- exactly one applicable locator: canonical UUID, external/report-local
  identity, or standards identity;
- immutable version/snapshot/integrity reference for material sources;
- origin/provenance attribution;
- reliance role;
- verification and availability status;
- limitations;
- source-native, Human, and AI-assisted interpretation attribution;
- observation/retrieval/submission time where relevant;
- integrity digest and minimal immutable representation for canonical,
  external/Human, or standards material when an owner-provided immutable
  snapshot/locator alone cannot reconstruct relied-upon meaning;
- creation and update timestamps.

Check constraints enforce source-class locator coherence. Material canonical
entries require owning capability and historical-resolution information.
Material external/Human entries require integrity identity and, when needed,
the minimum representation. Material standards entries preserve all information
actually supplied and explicitly record unavailable/unverified characteristics.
Contextual entries cannot be marked material without satisfying the relevant
material-source contract.

Canonical UUIDs remain references; Technical Report does not own the referenced
rows. The minimal external/Human representation is bounded to accepted-report
reproducibility and is not a generic source store.

#### 7.2.1 Typed locator and historical-basis columns

The provenance table uses a closed source discriminator and typed nullable
locator columns. A material entry must satisfy exactly one applicable locator
shape; an untyped locator mapping is prohibited.

Common columns are `source_class`, `source_type`, `owning_capability`,
`is_material`, `reliance_role`, `verification_status`, `availability_status`,
`origin_attribution`, `limitations`, `observed_at`, `retrieved_at`,
`integrity_algorithm`, `integrity_digest`, and a typed
`minimal_historical_representation` JSON value when the matrix below requires
one. The digest algorithm for Version 1 is SHA-256 over a deterministic
canonical serialization of the stored historical representation.

Canonical locator columns are:

- `capture_id` UUID and `capture_version` positive integer;
- `evidence_id` UUID and `evidence_version` positive integer;
- `engineering_object_id` UUID and `engineering_object_version` positive
  integer;
- `engineering_relationship_id` UUID and
  `engineering_relationship_version` positive integer;
- optional `canonical_snapshot_id` UUID only when the owning capability
  actually exposes an immutable snapshot identity.

External/Human locator columns are `report_local_source_id` UUID,
`external_reference` text, `submitted_by_id` positive integer when applicable,
and the applicable observation, retrieval, or submission timestamp. Standards
locator columns are `standard_identity`, `issuing_authority`, `edition`, and
`clause_or_location`. Check constraints require the applicable fields, prohibit
locator fields belonging to another source shape, require positive canonical
versions, and require both digest and minimal historical representation when
the accepted matrix below uses the report-owned fallback.

#### 7.2.2 Accepted representation

`accepted_snapshot` is a typed, integrity-protected serialization containing
the exact accepted report semantic content, preliminary qualification,
material-source manifest, source identities, typed source version/snapshot
locators, integrity metadata, and only the minimal historical representations
authorized by Section 12. It also binds the report UUID, purpose, scope,
accepted draft revision, resulting Aggregate version, accepting Human, and
acceptance time.

The accepted snapshot is sufficient to reproduce the accepted report and its
material reliance basis without treating a later live canonical row as the
accepted source state. It is not a generic archive and contains no unrelated
source content.

#### 7.2.3 Closed historical-basis logical schemas

The physical JSON value is not an open mapping. It must validate against exactly
one frozen, capability-owned value object named in Section 12.2, with
`extra="forbid"` at any Pydantic boundary. Every declared field, including an
explicit `null` optional field, participates in canonical serialization and the
integrity digest. No undeclared field is accepted or persisted.

### 7.3 Outbox and Idempotency

`technical_report_outbox` follows the capability-owned outbox pattern with UUID
event ID, aggregate UUID/version, event type, schema version, protected-minimal
JSON payload, occurrence time, publication time, and uniqueness on event ID and
aggregate-version/event type.

`technical_report_idempotency` follows Organization/actor/command/idempotency
uniqueness with request fingerprint, pending/completed status, aggregate ID,
authorized scalar result, and timestamps. Stored results exclude report
plaintext, source-native content, assumptions, conclusions, recommendations,
minimal provenance representations, and acceptance basis.

Audit uses the existing `audit_logs` table and `entity_uuid`; no Technical
Report audit table is created.

#### 7.3.1 Batch 2 authority clarification

For Implementation-Plan-032 Batch 2, Section 7.3 authorizes persistence
structure only. The Technical Report outbox and idempotency tables, SQLAlchemy
mappings, migration fields, constraints, indexes, ownership/grants, and
database-level persistence tests belong to the Credential and Persistence
Foundation.

Batch 2 does not authorize emitting outbox messages from application commands,
dispatch or worker behavior, application-layer event publication, idempotency
request orchestration or command handling, Unit of Work coordination, service
usage, API integration, or background processing. Those behavioral and
application integrations remain assigned to their later accepted workstreams
and batches. This clarification resolves batch allocation only and changes no
IDS-032 architecture or persistence semantics.

### 7.4 Indexes

Required indexes support only approved access paths:

- Organization/Workspace/lifecycle/updated ordering;
- Organization/optional Project/lifecycle ordering;
- Organization/owner/lifecycle;
- predecessor report ID for derived reverse lineage;
- provenance report ID/ordinal;
- provenance canonical source identity where present.

No full-text, vector, semantic-search, publication, or current-authority index is
authorized.

## 8. Accepted Immutability Enforcement

### 8.1 Current credential reality

Current repository configuration does not yet satisfy the immutability trust
boundary. `docker-compose.yml` initializes PostgreSQL with
`POSTGRES_USER=satco`; the backend uses that same `satco` credential through
`DATABASE_USER`; and Alembic falls back from `ALEMBIC_DATABASE_URL` to the same
`DATABASE_*` values. The initialized `satco` role is therefore the current
PostgreSQL superuser/schema owner and runtime application credential.

The Technical Report capability is not deployable under that arrangement. The
role split below is a mandatory implementation and deployment prerequisite.

### 8.2 PostgreSQL role and ownership contract

SATCO shall use two non-interchangeable credential classes:

**Migration/schema-owner credential.** The controlled migration connection uses
the existing `ALEMBIC_DATABASE_URL` and authenticates as the deployment-managed
schema-owner role. For the current local topology that privileged role may remain
the existing `satco` owner during transition. It owns Technical Report tables,
sequences, trigger functions, and triggers and may execute Alembic DDL. It is
never supplied to the running backend process.

**Runtime application credential.** The backend `DATABASE_*` connection uses a
distinct login role, `satco_runtime` in the repository-managed local/test
topology. That role is `NOSUPERUSER`, `NOBYPASSRLS`, `NOCREATEDB`,
`NOCREATEROLE`, and does not own the database, schema, Technical Report tables,
sequences, or trigger functions. It is not a member of the schema-owner role.
It receives no schema `CREATE`, table `TRUNCATE`, or ownership-changing
authority and no ability to `ALTER TABLE`, `DISABLE TRIGGER`, `DROP TRIGGER`,
`ALTER FUNCTION`, `DROP FUNCTION`, `ALTER ... OWNER`, or grant itself further
privileges. It is not granted `SET` authority for
`session_replication_role` or any equivalent trigger-bypass setting.

The schema owner revokes `PUBLIC` privileges that could alter the Technical
Report schema boundary, then grants `satco_runtime` only:

- schema `USAGE`;
- Technical Report root `SELECT` and `INSERT`, plus column-level `UPDATE` only
  for working content, qualification, draft revision, lifecycle, version,
  acceptance snapshot/record, and `updated_at` required by draft revision and
  the authorized draft-to-accepted transition; identity, scope, purpose, owner,
  predecessor, creation time, and primary key are not runtime-updatable;
- Technical Report provenance `SELECT`, `INSERT`, `UPDATE`, and `DELETE` needed
  to replace the manifest while the root remains draft; the parent-state trigger
  rejects every such write after acceptance;
- Technical Report outbox/idempotency `SELECT`, `INSERT`, and required
  status/result `UPDATE`;
- required sequence `USAGE` only where a non-UUID sequence exists;
- bounded `INSERT` access to existing Audit persistence through its approved
  recorder contract.

The Technical Report root grants no runtime `DELETE`; Version 1 exposes no
physical Aggregate deletion. PostgreSQL ordinary row triggers enforce the
invariant under this restricted non-owner, non-superuser runtime role. Trigger
functions are owned by the schema owner, have a fixed safe `search_path`, and
are not alterable by `satco_runtime`. The runtime role cannot disable user
triggers because it does not own the protected tables and has no superuser
authority. The schema owner revokes direct function `EXECUTE` from `PUBLIC` and
the runtime role; PostgreSQL invokes the functions only through their installed
triggers.

Database superuser and schema-owner operations are administrative authority
outside normal SATCO application authority. The invariant protects against the
normal configured application credential; it does not claim protection against
a malicious infrastructure superuser or authorized DBA using privileged
credentials.

### 8.3 Credential and deployment wiring

Runtime continues to use the repository's existing `DATABASE_HOST`,
`DATABASE_PORT`, `DATABASE_USER`, `DATABASE_PASSWORD`, and `DATABASE_NAME`
inputs, but `DATABASE_USER` must resolve to the restricted runtime login.
Migrations must use an explicit `ALEMBIC_DATABASE_URL` containing the
schema-owner credential; PATCH-032 deployment must not use Alembic's current
fallback to runtime `DATABASE_*` values.

For the repository-managed Docker topology, a new
`postgres/init/001_satco_database_roles.sh` provisions the restricted local/test
runtime login from a deployment-supplied secret and grants no ownership. The
Technical Report migration, executed by the schema owner, owns the protected
objects and applies exact revokes/grants after creating them. Existing databases
require equivalent schema-owner-operated role provisioning before upgrade; the
container initialization script is not a migration substitute.

Migration downgrade revokes Technical Report object grants and removes only the
Technical Report triggers, functions, and tables in reverse dependency order.
It does not drop the shared runtime login or alter privileges owned by another
capability.

The role-provisioning manifest must also enumerate the least DML/sequence
privileges required by already approved backend capabilities so the credential
split does not redesign or disable them. It must not use an unrestricted future
`GRANT ... ON ALL TABLES`, transfer ownership, or create default privileges that
silently authorize later capabilities. PATCH-032's migration grants only the
Technical Report and bounded existing-Audit privileges named in Section 8.2.

`backend/app/core/database.py` performs a fail-closed startup preflight: runtime
`current_user` must be distinct from the configured migration owner, must not be
superuser or `BYPASSRLS`, and must not own the protected Technical Report tables
or trigger functions. `backend/migrations/env.py` requires explicit
`ALEMBIC_DATABASE_URL` for PATCH-032 migration execution and rejects the runtime
role as migration identity. Secret values remain deployment inputs and are not
committed.

Deployment order is schema-owner migration and grant verification, restricted
runtime startup/preflight, then API health validation. Deployment fails closed
if runtime and migration resolve to the same role, the runtime role is
privileged or owns protected objects, required triggers are missing/disabled,
or the backend still uses `satco`/another schema-owner or superuser credential.

### 8.4 Enforceable accepted-state invariant

The enforceable persistence invariant is: once the stored root row's old
`lifecycle` is `accepted`, normal SATCO application database credentials cannot
update or delete that root row or update, insert, or delete any Aggregate-owned
provenance row for that report.

Immutability is enforced cumulatively:

1. the Aggregate rejects every mutation when lifecycle is `accepted`;
2. the service exposes no post-acceptance command;
3. repository compare-and-change for draft revision includes
   `lifecycle = 'draft'` and expected version;
4. acceptance persistence changes only a draft at the expected version;
5. repository exposes no generic save/update method;
6. accepted snapshot and manifest are never updated by an approved repository
   operation;
7. database checks enforce complete accepted-state coherence;
8. the bounded Technical Report migration creates a PostgreSQL trigger function
   and triggers owned by the Technical Report schema boundary;
9. a `BEFORE UPDATE OR DELETE` trigger on `technical_reports` rejects the
   operation when `OLD.lifecycle = 'accepted'`;
10. `BEFORE INSERT OR UPDATE OR DELETE` provenance triggers reject a write when
    the owning report is already `accepted`; the trigger locks the parent root
    row before deciding so a concurrent acceptance and provenance write are
    serialized;
11. the restricted runtime role defined in Section 8.2 receives no trigger
    bypass, ownership, DDL, or trigger-management authority; therefore direct
    SQLAlchemy attribute mutation, bulk update, direct SQL, and flush under the
    configured runtime credentials fail at the database boundary;
12. tests exercise both approved repository paths and deliberate persistence
    bypass attempts.

The invariant activates atomically when acceptance changes the root from
`draft` to `accepted`. The acceptance transaction finalizes provenance before
that lifecycle transition and writes the immutable accepted snapshot in the
same compare-and-change. The trigger permits this single draft-to-accepted
transition only when all acceptance-coherence checks are satisfied; later
root or manifest mutation is rejected. Physical deletion remains prohibited
for both lifecycle states by the application contract.

Privileged migration and DBA operations are outside normal application
authority and remain governed operational actions; they are not a Technical
Report mutation API. Migration downgrade may remove the trigger only as part
of an explicitly authorized schema rollback.

Accepted reads are constructed exclusively from `accepted_snapshot` and the
immutable acceptance record. Mutable draft/working columns and live canonical
source rows are not authoritative inputs to an accepted read. They may not be
used to repair, replace, or supplement accepted semantic content.

## 9. Repository Contract

`TechnicalReportRepository` owns database access only. Authorized methods are:

- `add(report)`;
- `get_scoped(report_id, organization_id)`;
- `persist_draft_expected_version(report, expected_version) -> bool`;
- `persist_acceptance_expected_version(report, expected_version) -> bool`;
- `list_scoped(...) -> TechnicalReportReadPage`;
- `list_successors_scoped(predecessor_id, organization_id, page, size)`;
- `provenance_for_report(report_id)` as complete Aggregate rehydration support.

`get_scoped` and list queries apply Organization scope before returning a row.
They do not decide actor authorization. Aggregate loads fully rehydrate the
root and provenance entries needed by the command.

The repository must not:

- authorize or disclose;
- commit or roll back;
- publish events or write Audit/idempotency;
- perform generic update;
- mutate lifecycle directly;
- update an accepted Aggregate;
- write the predecessor during successor creation;
- infer supersession, replacement, or current authority;
- return ORM rows outside the persistence/application boundary.

## 10. Ports and Unit of Work

Inward-owned protocols in `app/ports/technical_report.py` are:

- `TechnicalReportRepository`;
- `TechnicalReportUnitOfWork`;
- `TechnicalReportAuthorizationPolicy`;
- `TechnicalReportReferenceValidator`;
- `TechnicalReportHistoricalResolver`;
- `TechnicalReportDraftAssistant`;
- `TechnicalReportAuditRecorder`;
- `TechnicalReportRejectionAuditRecorder`;
- `TechnicalReportDomainEventRecorder`;
- `TechnicalReportIdempotencyStore`;
- `TechnicalReportClock`.

The Unit of Work exposes repository, successful-command Audit recorder, event
recorder, idempotency store, UoW-bound authorization/reference/historical
resolution collaborators, and one transaction. Only it commits or rolls back.
The UoW-bound collaborators share the same SQLAlchemy `Session` whenever they
read mutable acceptance-relevant state. AI assistance remains outside the
authoritative acceptance transaction.

`TechnicalReportRejectionAuditRecorder` is a separate application port backed
by the existing centralized `audit_logs` infrastructure. It is invoked only
after the authoritative UoW has rolled back and owns a separate short-lived
post-rollback transaction. It cannot access or mutate the Technical Report
repository, outbox, idempotency store, or Aggregate state.

## 11. Authorization Design

The trusted actor is constructed only from
`get_current_user_organization_context`. Client Organization, owner, creator,
accepting Human, or role claims are ignored and rejected when supplied.

All operations require:

- active authenticated User;
- one selected enabled membership in an active Organization;
- report Organization equality;
- authorized access to the mandatory Workspace;
- optional Project equality with the Workspace's canonical Project when a
  direct Project context is present;
- operation-specific policy.

The Human Owner is the immutable authenticated creator. `accept_exact_draft`
requires actor ID equality with `owner_id` plus current scope authorization.
Admin role alone does not silently substitute another accepting Human in V1.
Future delegated or enterprise acceptance requires separate architecture.

Authorization occurs before report existence, content, provenance, lineage,
counts, owner identity, or acceptance state is disclosed. Inaccessible reports,
predecessors, successors, and protected sources use the same protected-not-found
outcome.

AI is never an actor. It receives a least-privilege authorized context prepared
for the current Human request and cannot call policy or repository ports.

## 12. Reference and Historical Validation

`TechnicalReportReferenceValidator` verifies current visibility and scope for
Workspace, optional Project, Capture, Evidence, EngineeringObject, Engineering
Relationship, predecessor report, and Human identity through their canonical
application/policy boundaries. It never mutates those capabilities.

`TechnicalReportHistoricalResolver` validates the four EDS source contracts:

- canonical material: stable identity, owner, immutable source version/snapshot
  or integrity-protected historical representation, provenance, role,
  authorization, status, and limitations;
- external/Human material: canonical immutable representation when available,
  otherwise the report-owned minimal integrity-protected representation;
- standards material: supplied identity/authority/edition/clause, provenance,
  status, role, historical/integrity reference, limitations, and attribution;
- contextual/non-material: identity, ownership/context, authorization, and
  explicit non-material role.

Acceptance revalidates every material entry. A contextual entry that contributes
to accepted reasoning or conclusions is rejected until reclassified and made
historically resolvable.

### 12.1 Canonical historical-resolvability matrix

All four current canonical engineering source types expose stable UUID identity
and positive optimistic version in repository reality, but none supplies a
common immutable historical store that Technical Report may assume. Therefore
Version 1 records the typed identity/version and an integrity-protected minimum
acceptance-time representation for each materially relied-upon canonical source,
unless that owning capability later supplies an independently verified immutable
snapshot identity before Implementation Plan acceptance.

| Canonical source | Canonical owner | Stable identity and mutable version | Acceptance-time locator and exact report-owned provenance | Historical reconstruction rule | Acceptance validation and failure |
|---|---|---|---|---|---|
| Universal Capture | Universal Capture / Engineering Experience Capture | Capture UUID + positive `version` | `capture_id`, `capture_version`, optional canonical snapshot UUID, and exactly one `CaptureHistoricalBasisV1` | Use owner-provided immutable snapshot when verified; otherwise reconstruct only the closed basis in Section 12.2.1 | Reauthorize scope and disclosure; compare identity, version, lifecycle, scope, and digest. Fail non-disclosingly if changed, unavailable, or unreconstructable. |
| Evidence | Evidence Foundation | Evidence UUID + positive `version` | `evidence_id`, `evidence_version`, optional canonical snapshot UUID, and exactly one `EvidenceHistoricalBasisV1` | Use owner-provided immutable snapshot when verified; otherwise reconstruct only the closed basis in Section 12.2.2 | Reauthorize and validate acceptable lifecycle/standing, Organization and Project/Workspace compatibility, identity, version, and digest. Fail if any requirement is unresolved. |
| EngineeringObject | EngineeringObject capability | EngineeringObject UUID + positive `version` | `engineering_object_id`, `engineering_object_version`, optional canonical snapshot UUID, and exactly one `EngineeringObjectHistoricalBasisV1` | Use owner-provided immutable snapshot when verified; otherwise reconstruct only the closed basis in Section 12.2.3 | Reauthorize and compare scope, identity, version, lifecycle, authority standing, and digest. Fail if the relied-upon state cannot be fixed historically. |
| Engineering Relationship | Engineering Relationship capability | Relationship UUID + positive `version` | `engineering_relationship_id`, `engineering_relationship_version`, optional canonical snapshot UUID, and exactly one `EngineeringRelationshipHistoricalBasisV1` | Use owner-provided immutable snapshot when verified; otherwise reconstruct only the closed basis in Section 12.2.4 | Reauthorize the relationship and protected endpoints/Evidence; compare identity, version, lifecycle, scope, and digest. Fail if any protected basis or historical state cannot be resolved. |

Engineering Journal is an authorized navigation surface, not a canonical source
identity. When Journal navigation selects Capture or another canonical resource,
the manifest records the selected canonical owner and locator, never a Journal
locator.

External/Human material uses its report-local UUID, attributed origin, relevant
time, deterministic SHA-256 digest, and minimum relied-upon representation when
no authorized immutable canonical representation exists. Standards material
uses standard identity, issuing authority, edition/version, clause/location,
provenance, verification and availability, reliance role, limitations, and a
stable historical locator or integrity-protected minimum representation.
Contextual/non-material references record identity, owner/context, authorization,
and explicit non-material role; if they become material, acceptance applies the
appropriate row above or the external/standards contract.

Technical Report never queries a generic source repository and never becomes
canonical owner of source state. If identity, version/snapshot, integrity, or
the minimum authorized historical representation cannot guarantee the exact
material basis, acceptance deterministically returns
`TECHNICAL_REPORT_HISTORICAL_BASIS_INCOMPLETE` and rolls back.

### 12.2 Closed canonical historical-basis contracts

The four schemas below are the complete fallback contracts for canonical
sources that do not expose an independently verified immutable snapshot. Every
row is required unless marked optional. Optional keys are always serialized and
use explicit JSON `null` when the canonical value is absent. Every field is
included in canonical serialization and the SHA-256 digest. Strings use the
already normalized canonical model value; enums serialize as their lowercase
stored value; identifiers remain references and transfer no ownership.

#### 12.2.1 `CaptureHistoricalBasisV1`

| Field | Canonical source / type / cardinality | Normalization | Acceptance relevance |
|---|---|---|---|
| `basis_schema_version` | literal integer `1`, required | decimal `1` | fixes the closed representation version |
| `source_category` | literal string `universal_capture`, required | exact literal | prevents discriminator ambiguity |
| `capture_id` | `EngineeringExperienceCapture.id`, UUID, required | lowercase canonical UUID | stable source identity |
| `source_version` | `.version`, positive integer, required | base-10 integer | binds the mutable canonical state validated at acceptance |
| `organization_id` | `.organization_id`, UUID, required | lowercase canonical UUID | trusted Organization scope |
| `project_id` | `.project_id`, positive integer, required | base-10 integer | canonical Project context |
| `workspace_id` | `.workspace_id`, positive integer or null, optional | integer or explicit null | canonical Workspace context |
| `discipline` | `.discipline`, closed string or null, optional | canonical enum/string or null | Workspace discipline context actually carried by Capture |
| `engineering_object_id` | `.engineering_object_id`, UUID or null, optional | lowercase UUID or null | canonical object attachment actually carried by Capture |
| `source_kind` | `.source_kind`, `EngineeringExperienceSourceKind`, required | enum value | classifies captured engineering experience |
| `original_content` | `.original_content`, string `1..10000`, required | canonical Capture whitespace normalization; no summarization | exact material meaning relied upon; EDS-032 §16.2 authorizes the minimum content necessary for reconstruction |
| `source_reference` | `.source_reference`, string `1..512` or null, optional | canonical single-line normalization or null | preserves the attributed reference when present |
| `creator_id` | `.creator_id`, positive integer, required | base-10 integer | source provenance/Human origin |
| `lifecycle` | `.lifecycle`, `EngineeringExperienceCaptureLifecycle`, required | enum value | acceptance-time availability/standing |
| `created_at` | `.created_at`, aware timestamp, required | UTC timestamp rule in §12.3 | observation/provenance time represented by Capture creation |

Excluded fields are `updated_at`, `superseded_by_capture_id`, `allowed_actions`,
transport totals, attachments, request rationale, logs, diagnostics, transient
processing data, secrets, and any content outside `original_content` and the
optional normalized `source_reference`. Replacement identity is live protected
navigation, not necessary to reproduce the captured meaning.

#### 12.2.2 `EvidenceHistoricalBasisV1`

| Field | Canonical source / type / cardinality | Normalization | Acceptance relevance |
|---|---|---|---|
| `basis_schema_version` | literal integer `1`, required | decimal `1` | fixes the closed representation version |
| `source_category` | literal string `evidence`, required | exact literal | prevents discriminator ambiguity |
| `evidence_id` | `Evidence.id`, UUID, required | lowercase canonical UUID | stable Evidence identity |
| `source_version` | `.version`, positive integer, required | base-10 integer | binds validated mutable Evidence state |
| `organization_id` | `.organization_id`, UUID, required | lowercase canonical UUID | trusted Organization scope |
| `project_id` | `.project_id`, positive integer or null, optional | integer or explicit null | canonical optional Project scope |
| `workspace_id` | `.workspace_id`, positive integer or null, optional | integer or explicit null | canonical optional Workspace scope |
| `lifecycle` | `.lifecycle`, `EvidenceLifecycle`, required | enum value | acceptance-time Evidence lifecycle |
| `source_kind` | `.source_kind`, `EvidenceSourceKind`, required | enum value | authoritative Evidence classification |
| `source_reference` | `.source_reference`, string `1..512`, required | trimmed canonical value | identifies the Evidence source/basis |
| `source_revision` | `.source_revision`, string `1..128`, required | trimmed canonical value | source revision relied upon |
| `source_standing` | `.source_standing`, `EvidenceSourceStanding`, required | enum value | acceptance-time source standing |
| `effective_at` | `.effective_at`, aware timestamp or null, optional | UTC timestamp or explicit null | preserves temporal applicability when supplied |
| `supported_fact` | `.supported_fact`, string `1..2000`, required | trimmed canonical value; no summarization | exact metadata-only fact materially relied upon |
| `creator_id` | `.creator_id`, positive integer, required | base-10 integer | source provenance/Human origin |

Excluded fields are `created_at`, `updated_at`, `allowed_actions`, request
rationale, replacement command identity, transport totals, files/attachments,
unmodeled source payload, logs, diagnostics, and secrets. This representation is
the closed metadata-only Evidence basis; it is not a duplicate Evidence
repository.

#### 12.2.3 `EngineeringObjectHistoricalBasisV1`

| Field | Canonical source / type / cardinality | Normalization | Acceptance relevance |
|---|---|---|---|
| `basis_schema_version` | literal integer `1`, required | decimal `1` | fixes the closed representation version |
| `source_category` | literal string `engineering_object`, required | exact literal | prevents discriminator ambiguity |
| `engineering_object_id` | `EngineeringObject.id`, UUID, required | lowercase canonical UUID | stable object identity |
| `source_version` | `.version`, positive integer, required | base-10 integer | binds validated mutable object state |
| `organization_id` | `.organization_id`, UUID, required | lowercase canonical UUID | trusted Organization scope |
| `customer_id` | `.customer_id`, positive integer or null, optional | integer or explicit null | preserves approved internal/customer scope distinction |
| `project_id` | `.project_id`, positive integer, required | base-10 integer | canonical Project scope |
| `workspace_id` | `.workspace_id`, positive integer, required | base-10 integer | canonical Workspace scope |
| `family` | `.family`, `EngineeringObjectFamily`, required | enum value | approved classification |
| `discipline` | `.discipline`, `EngineeringDiscipline`, required | enum value | approved discipline classification |
| `object_type` | `.object_type`, `EngineeringObjectType`, required | enum value | approved object classification |
| `subtype` | `.subtype`, null in Version 1, required key | explicit null | proves no unapproved subtype was relied upon |
| `lifecycle` | `.lifecycle`, `EngineeringLifecycle`, required | enum value | acceptance-time object state |
| `authority_standing` | `.authority_standing`, `EngineeringAuthorityStanding`, required | enum value | acceptance-time engineering authority context |
| `creator_id` | `.creator_id`, positive integer, required | base-10 integer | canonical creation provenance |
| `steward_id` | `.steward_id`, positive integer, required | base-10 integer | accountable current responsibility at acceptance |

Excluded fields are ORM relationships, customer/project/workspace nested
objects, timestamps, `allowed_actions`, Evidence request references, command
rationale, replacement identity, labels or names not owned by EngineeringObject,
logs, diagnostics, and secrets. No endpoint or related Aggregate content is
copied.

#### 12.2.4 `EngineeringRelationshipHistoricalBasisV1`

| Field | Canonical source / type / cardinality | Normalization | Acceptance relevance |
|---|---|---|---|
| `basis_schema_version` | literal integer `1`, required | decimal `1` | fixes the closed representation version |
| `source_category` | literal string `engineering_relationship`, required | exact literal | prevents discriminator ambiguity |
| `engineering_relationship_id` | `EngineeringRelationship.id`, UUID, required | lowercase canonical UUID | stable relationship identity |
| `source_version` | `.version`, positive integer, required | base-10 integer | binds validated mutable relationship state |
| `organization_id` | `.organization_id`, UUID, required | lowercase canonical UUID | trusted Organization scope |
| `project_id` | `.project_id`, positive integer, required | base-10 integer | canonical Project scope |
| `workspace_id` | `.workspace_id`, positive integer, required | base-10 integer | canonical Workspace scope |
| `source_object_id` | `.source_object_id`, UUID, required | lowercase canonical UUID | directed source endpoint identity |
| `target_object_id` | `.target_object_id`, UUID, required | lowercase canonical UUID | directed target endpoint identity |
| `relationship_family` | `.relationship_family`, `RelationshipFamily`, required | enum value | first half of the authoritative family/type discriminator |
| `relationship_type` | `.relationship_type`, `RelationshipType`, required | enum value | second half of the authoritative family/type discriminator |
| `lifecycle` | `.lifecycle`, `EngineeringRelationshipLifecycle`, required | enum value | acceptance-time relationship state |
| `authority_standing` | `.authority_standing`, `EngineeringAuthorityStanding`, required | enum value | acceptance-time authority context |
| `evidence_references` | `.evidence_references`, unique UUID array, required | ascending lowercase UUID array | canonical Evidence identities on which relationship governance relies |
| `creator_id` | `.creator_id`, positive integer, required | base-10 integer | relationship creation provenance |
| `steward_id` | `.steward_id`, positive integer, required | base-10 integer | accountable current responsibility |
| `reviewer_id` | `.reviewer_id`, positive integer or null, optional | integer or explicit null | recorded review accountability when present |
| `approver_id` | `.approver_id`, positive integer or null, optional | integer or explicit null | recorded approval accountability when present |

Direction is represented exclusively by the ordered source/target UUIDs; no
derived direction label is stored. Excluded fields are endpoint Aggregate
content, Evidence content, ORM relationships, timestamps, `allowed_actions`,
traversal/navigation state, cycle-analysis results, command rationale,
replacement relationship identity, logs, diagnostics, and secrets.

The `evidence_references` array proves only which Evidence identities governed
the canonical relationship. If Technical Report materially relies upon any
referenced Evidence meaning, that Evidence must also appear as a separate
authorized `EvidenceHistoricalBasisV1`; the relationship basis never embeds or
substitutes Evidence content.

Engineering Journal is not an additional canonical source category. External/
Human and standards materials remain the separately typed EDS-032 §16.2/§16.3
contracts already defined in Sections 7.2.1 and 12.1; they are not canonical
source fallbacks and do not create another canonical module.

These representations are acceptance-time enrichment of an already captured
canonical source, not a second intake or authoring path. They preserve Capture
Once by retaining only the closed historical basis required to reproduce one
accepted report's reliance, while identity, lifecycle, commands, and live source
authority remain with the canonical owner.

### 12.3 Canonical serialization and digest

PATCH-032 uses a capability-local deterministic JSON serialization; it does not
establish a platform-wide serialization capability. The serializer:

1. validates exactly one frozen `*HistoricalBasisV1` value object and rejects
   missing required or undeclared fields;
2. emits every schema key, including optional keys with explicit JSON `null`;
3. orders object keys lexicographically by Unicode code point at every level;
4. encodes UTF-8 JSON without byte-order mark or insignificant whitespace;
5. emits booleans only as `true`/`false`, null only as `null`, and integers as
   base-10 digits without leading zeros; floating-point values are prohibited;
6. emits UUIDs as lowercase hyphenated canonical strings;
7. emits enums as their exact stored lowercase string value;
8. emits strings after the owning model's approved normalization and Unicode
   NFC normalization, with RFC 8259 escaping;
9. emits aware timestamps in UTC as `YYYY-MM-DDTHH:MM:SS.ffffffZ`, always with
   six fractional digits; naive timestamps are rejected;
10. preserves semantically ordered arrays and lexicographically sorts only the
    `evidence_references` set-like UUID array after uniqueness validation.

The digest is:

```text
integrity_algorithm = "sha256"
integrity_digest = lowercase_hex(
    SHA-256(UTF-8(canonical_json(typed_historical_basis)))
)
```

The hashed value includes schema version, category discriminator, source
identity, source version, scope, material source state, and every explicit null.
No field is appended outside the hashed representation. Acceptance recomputes
the serialization from the UoW-bound canonical read, compares it to the stored
representation and digest using exact bytes, and fails on any mismatch. No key
management or signature authority is introduced.

### 12.4 Historical completeness predicates

For each canonical source, acceptance succeeds only when either the owning
capability provides a verified immutable snapshot identity whose contents meet
the same closed `*HistoricalBasisV1` meaning, or all fields of that source's
closed fallback schema can be resolved, authorized, normalized, serialized,
digested, stored in the report-owned acceptance basis, and immediately
reverified at the same source version inside the acceptance UoW.

Acceptance fails atomically with
`TECHNICAL_REPORT_HISTORICAL_BASIS_INCOMPLETE` when a required field is absent,
an optional field cannot be distinguished from null, an undeclared field is
supplied, source version or authority changes, serialization or digest cannot
be produced, digest verification fails, the source becomes inaccessible, or
the necessary representation would exceed EDS-032 authority. There is no
best-effort acceptance, partial provenance, generic source fallback, or
substitution of current live state after acceptance.

## 13. Application Service Use Cases

### 13.1 Create Draft

Input: create schema, trusted actor, correlation ID, idempotency ID.

Sequence: authorize scope; validate Workspace/optional Project; normalize typed
content and manifest; derive Organization and owner; reserve idempotency;
construct `CreateTechnicalReportDraft`; create Aggregate at version 1 and a new
draft revision UUID; add it; stage Audit/outbox/idempotency; commit once.

Result: authorized draft response. Failure leaves no report or side record.

### 13.2 Revise Draft

Input: report UUID, expected version, exact expected draft revision, complete
replacement draft value object and manifest, rationale, trusted metadata.

Sequence: protected load; authorize owner operation; validate references and
scope; check idempotency; invoke one Aggregate revision; advance draft revision
once for material change and Aggregate version once; compare-and-change;
stage Audit/outbox/idempotency; commit once.

No partial field patch is exposed. A semantic no-op is rejected. Accepted
reports reject revision.

### 13.3 Get and List

Get performs Organization-scoped load, then current operation authorization,
then maps an authorized detail DTO. List requires an authorized Workspace and
optional canonical Project context before querying, applies lifecycle/purpose
filters, stable `updated_at DESC, id DESC` ordering, page size `1..100`, and
returns only authorized totals and items. Hidden rows never influence disclosed
counts.

### 13.4 Accept Exact Draft

Input: report UUID, positive expected pre-acceptance version, exact draft
revision UUID, explicit confirmation boolean equal to true, non-empty rationale,
correlation ID, and idempotency ID.

The exact sequence is defined in Section 14.

### 13.5 Create Successor

Input: authorized predecessor UUID, new draft content/manifest, optional explicit
set of predecessor-derived inputs requested for copying, rationale, correlation
ID, and idempotency ID.

The predecessor must be accepted, Organization/Workspace compatible, and
authorized for lineage disclosure. The service creates a new UUID Aggregate in
`draft` with version 1 and new draft revision. Only the successor stores
`predecessor_report_id`; predecessor state is untouched.

Lineage-only creation is valid. For requested copied inputs, current authorization
is independently evaluated for every item before disclosure or reproduction.
If one requested item fails, the entire operation fails non-disclosingly before
the successor is added. Copied content becomes new draft input with newly
evaluated provenance/reliance and inherits no acceptance.

### 13.6 Retrieve Lineage

The service authorizes the subject report, then separately authorizes a
predecessor before disclosure. Reverse successors are derived from
successor-owned predecessor references and filtered before totals or identities
are returned. The response states traceability only and contains no
supersession/current-authority meaning.

### 13.7 Request AI Draft Proposal

Input: authorized draft UUID, expected current version/revision, explicit Human
instruction, and selected authorized source references.

The service authorizes the Human and draft, resolves only authorized inputs,
and invokes `TechnicalReportDraftAssistant`. The result is an attributable,
non-authoritative proposal DTO. It writes no Aggregate, Audit authority outcome,
outbox event, idempotency authority result, or lifecycle state. Provider failure
returns a stable assistant-unavailable outcome without altering the draft. The
Human may incorporate a proposal only through a later revision command.

## 14. Atomic Human Acceptance Sequence

### 14.1 Transaction-consistency strategy

Human acceptance uses one PostgreSQL transaction and one coherent SQLAlchemy
Session owned by `TechnicalReportUnitOfWork`. Every acceptance-relevant adapter
that reads mutable database state is constructed from that UoW Session; the
independent FastAPI request Session, if present for transport composition, must
not perform acceptance-critical authorization, membership, context, source, or
historical-resolution reads.

Within that transaction:

- the Technical Report root is loaded with a row lock and the final write uses
  UUID, Organization, `lifecycle='draft'`, expected Aggregate version, and exact
  draft revision predicates;
- active User, active Organization, selected enabled membership, Workspace,
  and optional Project rows used for acceptance authority/context are read and
  locked through UoW-bound policy/reference adapters;
- each mutable canonical source is resolved through its owning adapter using
  the same Session and either locked for the transaction or protected by an
  identity-and-version predicate rechecked immediately before acceptance
  persistence;
- a canonical immutable snapshot is verified by immutable snapshot identity
  and digest rather than locked as mutable state;
- external/Human and standards representations are validated against the typed
  locator and deterministic digest that will enter the accepted snapshot;
- provenance finalization, acceptance compare-and-change, successful-command
  Audit, outbox, idempotency result, and commit occur in that same UoW.

The owning capability remains authoritative for interpreting each canonical
version and status. These UoW-bound adapters do not mutate canonical resources,
and no distributed transaction is introduced.

If the Human Owner basis, active User/Organization/membership, Workspace or
Project context, material-source availability/authorization, canonical source
identity/version/snapshot/digest, or Technical Report draft version/revision
changes between validation and commit, acceptance fails and the whole
authoritative transaction rolls back. The result uses protected-not-found when
the changed fact is protected; otherwise it uses the stable version, source,
context, or historical-basis category without disclosing the changed row or
source.

### 14.2 Ordered acceptance operation

One request-scoped service operation performs:

1. authenticate the User;
2. resolve trusted active Organization context;
3. open one Technical Report Unit of Work and construct all mutable-state
   acceptance collaborators from its Session;
4. load the report by UUID and Organization scope;
5. apply protected-not-found if absent or inaccessible;
6. verify actor is the immutable Human Owner and currently authorized;
7. calculate the request fingerprint and look up idempotency; an exact completed
   replay reauthorizes current disclosure and returns its safe result;
8. verify lifecycle is exactly `draft` for a new command;
9. verify expected pre-acceptance Aggregate version;
10. verify exact current draft revision;
11. require explicit Human confirmation and rationale;
12. lock and validate the active authority basis, Workspace, and optional
    Project binding;
13. reauthorize and validate every material source using the matrix and
    consistency controls in Sections 12.1 and 14.1;
14. verify deterministic historical reconstruction, integrity digests,
    per-source versions/snapshots, and preliminary basis;
15. reserve the new idempotency command;
16. invoke `accept_exact_draft` once;
17. construct the immutable accepted snapshot;
18. advance Aggregate version exactly once to the resulting post-acceptance
    version while preserving the accepted draft revision;
19. recheck every mutable acceptance predicate, then persist with
    compare-and-change requiring prior version, exact draft revision, and
    `draft` state;
20. stage minimal Audit accountability, accepted Domain Event outbox row, and
    idempotency result;
21. commit once;
22. map an authorized accepted response after successful commit.

Any failure rolls back report, Audit, outbox, and idempotency state together.
No response represents acceptance before commit.

Duplicate exact idempotent replay reauthorizes the actor and report before
returning a safe current result. A different fingerprint for the same key is an
idempotency conflict. Acceptance attempted with a different key against an
already accepted report is an invalid lifecycle/duplicate-acceptance conflict.
Stale version or revision is a version conflict; concurrent draft revision or
acceptance produces the same stable conflict without partial state.

## 15. Domain Events and Audit

Minimum outbox events are:

- `TechnicalReportDraftCreated`;
- `TechnicalReportDraftRevised`;
- `TechnicalReportAccepted`;
- `TechnicalReportSuccessorCreated`.

Event payloads contain identifiers, scope IDs, purpose, lifecycle, versions,
revision IDs, actor ID, timestamps, correlation/causation IDs, predecessor ID
when authorized for the operation, and source-entry counts. They exclude report
content, conclusions, recommendations, source-native text, minimal external
representations, and protected reliance details.

### 15.1 Successful-command Audit

Audit for a successful authoritative command is staged inside the primary
Technical Report Unit of Work and commits atomically with Aggregate state,
outbox, and idempotency result. A rollback removes that staged success Audit so
no failed operation can leave a misleading success record.

### 15.2 Durable rejection/security Audit

ADR-010 requires business Audit after successful operations and does not make
ordinary syntax, reference, version, lifecycle, idempotency, or business-rule
validation failures independently durable. EDS-032 requires accountability for
attempted governed actions without declaring every failure auditable. For
PATCH-032, durable rejection Audit is therefore required only for these
security/authority-bearing attempts:

- an authenticated Human attempts acceptance without being the Human Owner or
  without current acceptance authority;
- an authenticated actor attempts disclosure or mutation across an
  Organization boundary;
- an AI/provider path attempts to perform or impersonate Human acceptance or
  another authority-bearing command;
- an authenticated actor attempts a Technical-Report-owned mutation after
  acceptance.

Protected resource misses, ordinary validation failures, stale versions,
inaccessible canonical sources, and unresolved historical bases produce no
separate durable rejection row unless one of the security/authority categories
above also applies. This avoids turning Audit into an existence oracle or a
record of routine malformed input.

The ordered rejection path is:

1. begin the authoritative Technical Report UoW;
2. detect a failure and classify it without disclosing protected facts;
3. roll back the authoritative UoW, including any staged success Audit, outbox,
   and idempotency changes;
4. if the category is listed above, invoke
   `TechnicalReportRejectionAuditRecorder` after rollback;
5. the recorder opens and owns a separate short-lived transaction against the
   existing centralized Audit infrastructure and writes only the bounded
   accountability record;
6. return the original stable non-disclosing failure regardless of Audit
   persistence outcome.

The rejection record contains only authenticated actor ID, trusted Organization
ID, operation type, Technical Report UUID only when already safely known in the
actor's authorized scope, stable reason category/code, outcome `rejected`,
server timestamp, correlation/request ID, and command ID when available. It
contains no report plaintext, canonical source plaintext, source identity when
protected, minimal historical representation, sensitive provenance, denial
detail, stack trace, or idempotency result.

The rejection recorder cannot receive a Technical Report repository or UoW and
cannot mutate Technical Report, provenance, outbox, or idempotency state. If its
write fails, it rolls back its own transaction, emits only a non-sensitive
operational failure signal, and still returns the original rejection. It must
never convert rejection to success or replace the original protected error with
Audit infrastructure detail.

AI proposal generation may produce operational telemetry, but it is not an
authoritative Domain Event.

Abandonment is not a lifecycle or command. Existing retention/Audit governance
may retain independently required metadata, but no abandoned Technical Report
state, archival subsystem, delete workflow, or plaintext Audit repository is
created.

## 16. AI Integration Boundary

`TechnicalReportDraftAssistant` accepts an immutable authorized assistant input
containing Human instruction, report purpose/scope, current draft revision, and
only selected authorized source representations. It returns proposal content,
identified assumptions/gaps, attribution metadata, and provider-neutral
diagnostics.

The concrete adapter belongs under `app/ai/` as permitted by the Backend
Blueprint and depends on an injected provider client. No provider identifier,
conversation state, prompt, or model response becomes Aggregate authority.
Provider-specific behavior is isolated behind the port.

AI cannot accept, set lifecycle, persist a revision, construct trusted actor
context, widen scope, retrieve repositories, copy inaccessible material, or
emit authoritative Audit/outbox results. Logs and errors exclude protected
inputs and outputs.

## 17. Pydantic and DTO Contracts

All transport models use Pydantic v2 `ConfigDict(extra="forbid")`. Read DTOs
use `from_attributes=True` only at the controlled mapping boundary.

Required contracts are:

- `TechnicalReportCreateRequest`: workspace ID, optional Project ID, purpose,
  content value, preliminary qualification, provenance entries;
- `TechnicalReportReviseDraftRequest`: expected version, expected draft
  revision, complete content/provenance replacement, rationale;
- `TechnicalReportAcceptRequest`: expected version, exact draft revision,
  explicit confirmation, rationale;
- `TechnicalReportCreateSuccessorRequest`: new draft values, explicitly selected
  copy references, rationale;
- `TechnicalReportAIProposalRequest`: expected version/revision, Human
  instruction, selected source references;
- `TechnicalReportFilter` and bounded pagination;
- summary, draft detail, accepted detail, provenance, acceptance, lineage,
  AI-proposal, and paginated response DTOs.

Client-controlled fields are draft technical values, optional direct Project
context, source declarations, rationale, explicit acceptance confirmation, and
expected concurrency/revision values.

Server-controlled/read-only fields are report and revision identities,
Organization, owner, lifecycle, Aggregate version, accepted snapshot,
accepting Human, acceptance timestamp, accepted versions, timestamps, derived
lineage direction, authorization outcomes, and allowed actions. Clients cannot
set canonical verification results, accepted state, acceptance identity/time,
or predecessor authority outside the successor command.

List responses exclude technical plaintext, provenance representations,
assumptions, uncertainty, limitations, conclusions, recommendations, and Human
acceptance details. Detail and provenance disclosure require separate current
authorization.

## 18. API Contract

| Method and route | Request / response | Service | Success |
|---|---|---|---|
| `POST /technical-reports` | create request / draft detail | `create_draft` | 201 |
| `GET /technical-reports/{report_id}` | path UUID / authorized lifecycle-specific detail | `get` | 200 |
| `GET /technical-reports` | required workspace, optional Project/purpose/lifecycle, page/size / page | `list` | 200 |
| `POST /technical-reports/{report_id}/draft-revisions` | revise request / draft detail | `revise_draft` | 200 |
| `POST /technical-reports/{report_id}/acceptance` | acceptance request / accepted detail | `accept_exact_draft` | 200 |
| `POST /technical-reports/{report_id}/successors` | successor request / new draft detail | `create_successor` | 201 |
| `GET /technical-reports/{report_id}/lineage` | bounded page / lineage response | `get_lineage` | 200 |
| `POST /technical-reports/{report_id}/ai-draft-proposals` | AI proposal request / advisory proposal | `request_ai_proposal` | 200 |

Mutations require `X-Correlation-ID` and `Idempotency-Key` UUID headers except
AI proposal generation, which is non-authoritative and non-mutating. Every
route requires trusted authentication/Organization dependency.

No `PUT`, generic `PATCH`, delete, publish, approve, supersede, archive, Review,
or autonomous-AI route is permitted. Routers perform transport validation,
invoke one service operation, and map stable outcomes only.

## 19. Stable Error Contract

| Application category | Stable code | HTTP mapping |
|---|---|---|
| validation failure | `TECHNICAL_REPORT_VALIDATION_ERROR` | 422 |
| protected resource | `TECHNICAL_REPORT_NOT_FOUND` | 404 |
| unauthorized acceptance | protected not found for protected report; otherwise `TECHNICAL_REPORT_AUTHORIZATION_DENIED` | 404/403 |
| invalid lifecycle / duplicate acceptance | `TECHNICAL_REPORT_INVALID_LIFECYCLE` | 409 |
| accepted mutation attempt | `TECHNICAL_REPORT_ACCEPTED_IMMUTABLE` | 409 |
| stale Aggregate or draft revision | `TECHNICAL_REPORT_VERSION_CONFLICT` | 409 |
| idempotency conflict | `TECHNICAL_REPORT_IDEMPOTENCY_CONFLICT` | 409 |
| incompatible scope/context | protected not found when protected; otherwise `TECHNICAL_REPORT_INVALID_CONTEXT` | 404/422 |
| inaccessible source | `TECHNICAL_REPORT_SOURCE_UNAVAILABLE` without source existence detail | 422 |
| unresolved historical basis | `TECHNICAL_REPORT_HISTORICAL_BASIS_INCOMPLETE` | 422 |
| invalid predecessor/lineage | protected not found or `TECHNICAL_REPORT_INVALID_LINEAGE` | 404/409 |
| AI authority attempt | `TECHNICAL_REPORT_AI_AUTHORITY_VIOLATION` | 409 |
| assistant unavailable | `TECHNICAL_REPORT_ASSISTANT_UNAVAILABLE` | 503 |
| unexpected failure | `TECHNICAL_REPORT_INTERNAL_SERVER_ERROR` | 500 |

Internal SQL, constraint, provider, and stack details are never disclosed.

## 20. Read and Lineage Queries

Queries are bounded, Organization-first, and authorization-filtered. Draft and
accepted filters expose canonical lifecycle only. Counts are computed after
scope and visibility filtering. Stable ordering uses `updated_at DESC, id DESC`.

Accepted detail includes the immutable accepted snapshot and Human acceptance
metadata only when authorized. Draft detail includes current draft and revision
but no fabricated acceptance fields.

Lineage returns an optional authorized predecessor and a bounded page of
authorized successor summaries derived from successor rows. Hidden lineage
members do not affect disclosed counts. Lineage never labels a report current,
replacement, invalid, withdrawn, or superseded.

## 21. Concurrency and Idempotency

Draft revision uses an atomic update predicate on report UUID, Organization,
`lifecycle='draft'`, and expected version. Acceptance adds exact draft revision
to that predicate. One affected row means success; zero means stable version or
lifecycle conflict after protected reload.

Successful material revision advances draft revision once and Aggregate version
once. Successful acceptance advances Aggregate version once, preserves the
accepted draft revision, and creates no later mutable version. Successor creation
does not lock or update the predecessor after current authorization and state
validation; it inserts one new Aggregate with a successor-owned reference.

All authoritative commands are idempotent within Organization, actor, command
type, and idempotency UUID. Replays reauthorize before returning safe results.
Stored idempotency diagnostics contain no protected plaintext.

## 22. File-Level Implementation Map

### 22.1 New files

| Path | Purpose |
|---|---|
| `backend/app/enums/technical_report.py` | closed lifecycle, purpose, source-class, verification, and availability vocabularies |
| `backend/app/models/technical_report.py` | Aggregate root and SQLAlchemy mappings |
| `backend/app/models/technical_report_command.py` | commands, closed frozen historical-basis value objects, capability-local canonical serializer/digest, events, and outbox/idempotency mappings |
| `backend/app/ports/technical_report.py` | inward Protocol contracts |
| `backend/app/schemas/technical_report.py` | strict Pydantic v2 transport/read DTOs |
| `backend/app/exceptions/technical_report.py` | stable application exception hierarchy |
| `backend/app/repositories/technical_report_repository.py` | SQLAlchemy repository; no commit or authorization |
| `backend/app/repositories/technical_report_unit_of_work.py` | UoW; same-Session acceptance policy/reference/history adapters; successful Audit/outbox/idempotency coordination; separate rejection-Audit adapter boundary |
| `backend/app/services/technical_report_service.py` | application orchestration |
| `backend/app/ai/technical_report_assistant.py` | provider-neutral concrete assistant adapter boundary |
| `backend/app/api/v1/routers/technical_reports.py` | thin transport and request-scoped composition |
| `backend/migrations/versions/e03200000001_technical_reports.py` | bounded tables, typed provenance checks, accepted-state trigger function/triggers, upgrade/downgrade; parent must be reverified as current head |
| `postgres/init/001_satco_database_roles.sh` | clean local/test database provisioning of the restricted `satco_runtime` login from deployment secret; no schema migration behavior |
| `backend/tests/test_technical_report_aggregate.py` | domain behavior |
| `backend/tests/test_technical_report_schemas.py` | contract validation |
| `backend/tests/test_technical_report_repository.py` | persistence, optimistic concurrency, trigger-enforced immutability, typed source matrix, and accepted-read authority |
| `backend/tests/test_technical_report_service.py` | application use cases, authorization, historical resolvability, and acceptance races |
| `backend/tests/test_technical_report_transaction.py` | coherent acceptance transaction; success Audit/outbox/idempotency atomicity; durable rejection Audit and rollback |
| `backend/tests/test_technical_report_security.py` | protected disclosure and AI/Human authority |
| `backend/tests/test_technical_report_api.py` | endpoints and stable errors |
| `backend/tests/test_technical_report_migration.py` | isolated upgrade/downgrade and model drift |
| `backend/tests/test_technical_report_database_roles.py` | distinct credential, ownership/grant, trigger-bypass denial, runtime DML, and fail-closed deployment verification |

### 22.2 Existing files permitted to modify

| Path | Exact change |
|---|---|
| `backend/app/enums/__init__.py` | export Technical Report enums without collisions |
| `backend/app/models/__init__.py` | import mappings only if required by current Alembic/model discovery |
| `backend/app/ports/__init__.py` | export Technical Report ports if repository convention requires it |
| `backend/app/main.py` | register only the Technical Report router |
| `backend/app/core/config.py` | declare and validate runtime database configuration without accepting migration credentials as runtime settings |
| `backend/app/core/database.py` | use runtime `DATABASE_*` credential and perform restricted-role/ownership/trigger preflight before capability availability |
| `backend/migrations/env.py` | require explicit schema-owner `ALEMBIC_DATABASE_URL` and reject the runtime role for PATCH-032 migration execution |
| `backend/tests/conftest.py` | provide isolated restricted-runtime and schema-owner database fixtures without weakening the dedicated-test-database guard |
| `docker-compose.yml` | inject distinct runtime and migration credentials, mount the role-init script for clean local/test databases, and stop supplying `satco` as backend runtime user |

### 22.3 No change expected

Authentication dependencies, existing canonical models, repositories,
services, migrations, and routers remain unchanged. In particular, Technical
Report must not modify Universal Capture, Engineering Journal, Evidence,
EngineeringObject, Engineering Relationship, Project, Workspace, Organization,
User, Audit, or their migrations to acquire authority.

Any future implementation need outside this exact map is a stop condition for
Implementation Plan review, not implied authorization.

The trigger function and triggers are created and removed only by the bounded
Technical Report migration above. The existing Audit table and service contract
are reused; the separate post-rollback adapter does not require an Audit schema
change. If implementation proves either statement false, work stops and returns
to IDS governance rather than modifying an unlisted canonical capability.

## 23. Architectural Dependency Order

The implementation dependency order is:

```text
enums and framework-independent value/command contracts
→ Aggregate and persistence mappings
→ inward ports and strict schemas
→ bounded Alembic migration design
→ repository and Unit of Work adapters
→ authorization/reference/historical-resolution adapters
→ application service and provider-neutral AI adapter
→ thin API router and registration
→ domain/schema tests
→ migration/repository/transaction tests
→ application/security/AI-boundary tests
→ API and regression tests
```

This is dependency ordering only, not sprint planning or execution authority.

## 24. Test Design

### 24.1 Domain and schema

- create each purpose in valid scope;
- reject every unauthorized lifecycle value;
- distinguish Aggregate version from draft revision;
- advance material draft revision exactly once;
- reject no-op and stale revisions;
- bind acceptance to exact version/revision and explicit Human confirmation;
- preserve preliminary limitations;
- create immutable accepted snapshot;
- reject every accepted mutation;
- create lineage-only successor with new identity/draft/no acceptance;
- reject self/incompatible predecessor;
- reject client-controlled server fields and extra fields.

### 24.2 Persistence and migration

- upgrade from verified head and downgrade in isolated database;
- reproduce schema from clean database;
- model/migration constraint and index parity;
- full Aggregate/provenance rehydration;
- expected-version update affects exactly one row;
- accepted root ORM mutation and flush fail under application credentials;
- accepted root direct SQL update/delete fail under application credentials;
- accepted provenance insert/update/delete and ORM flush fail under application
  credentials;
- attempted bypass leaves accepted snapshot, acceptance record, lineage, and
  provenance unchanged;
- accepted reads derive exclusively from the immutable accepted snapshot and
  remain unchanged after every attempted mutation;
- database trigger activation permits only the coherent draft-to-accepted
  transition and blocks all later Aggregate-owned writes;
- restricted runtime role can create and revise a draft through approved paths;
- restricted runtime role can execute the legitimate draft-to-accepted
  transition while triggers are active;
- restricted runtime role cannot mutate accepted semantic content or provenance
  through ORM flush, bulk update, or direct SQL;
- restricted runtime role cannot disable, drop, replace, or alter either
  immutability trigger and cannot alter/drop its schema-owner-owned function;
- restricted runtime role cannot change ownership of protected tables,
  sequences, functions, or triggers and cannot grant itself privileges;
- runtime and Alembic connections resolve to distinct roles; runtime is
  non-superuser/non-owner without `BYPASSRLS`, while migration uses the declared
  schema owner;
- backend startup and deployment fail closed for identical roles, privileged
  runtime role, protected-object ownership, or missing/disabled triggers;
- accepted reads remain snapshot-only under the restricted runtime credential;
- successor inserts without predecessor update;
- reverse lineage derives from successor references;
- FK, nullability, lifecycle/acceptance coherence, and unique constraints;
- typed locator/check-constraint coverage for Capture, Evidence,
  EngineeringObject, Engineering Relationship, external/Human, standards, and
  contextual source shapes.

### 24.3 Application and security

- active owner create/revise/accept;
- inactive User, disabled membership, nonmember, cross-Organization,
  cross-Project, cross-Workspace, and revoked access denial;
- non-owner acceptance denial even when otherwise visible;
- authorization before report, content, provenance, owner, acceptance, and
  lineage disclosure;
- protected-not-found equivalence;
- missing/unresolvable material provenance rejection;
- atomic acceptance with Audit/outbox/idempotency;
- rollback on each staged failure;
- Human Owner or membership change during acceptance rolls back;
- active Organization, Workspace, or Project authority change during
  acceptance rolls back non-disclosingly;
- each canonical source version change after validation is detected before
  commit and rolls back;
- a canonical source becoming unavailable or unauthorized before commit rolls
  back without source disclosure;
- concurrent Technical Report draft version/revision change produces the stable
  version conflict;
- canonical reference change during acceptance cannot produce a mixed-basis
  accepted snapshot;
- immutable canonical snapshot identity/digest mismatch fails acceptance;
- Capture, Evidence, EngineeringObject, and Engineering Relationship material
  entries each validate their typed locator, version/snapshot, integrity,
  authorization, and historical representation;
- `CaptureHistoricalBasisV1` accepts exactly the Section 12.2.1 field set,
  round-trips the authorized captured meaning, and rejects missing content,
  missing scope/version, undeclared fields, attachments, transient data, and
  excessive/unapproved plaintext;
- `EvidenceHistoricalBasisV1` accepts exactly the Section 12.2.2 metadata-only
  field set, round-trips the supported fact/source basis, and rejects missing
  lifecycle/standing/reference/revision/fact, undeclared fields, source payload,
  attachments, and excessive/unapproved plaintext;
- `EngineeringObjectHistoricalBasisV1` accepts exactly the Section 12.2.3
  classification/scope/authority field set, round-trips only that context, and
  rejects missing classification/version/scope, undeclared fields, nested ORM
  objects, labels, related Aggregate content, and excessive plaintext;
- `EngineeringRelationshipHistoricalBasisV1` accepts exactly the Section
  12.2.4 identity/direction/vocabulary/authority field set, round-trips only the
  relationship meaning, and rejects missing endpoints/family/type/version,
  undeclared fields, endpoint or Evidence content, traversal state, and
  excessive plaintext;
- every historical-basis schema rejects additional fields and distinguishes
  required values from explicit-null optional values;
- repeated construction with semantically identical values produces identical
  canonical UTF-8 bytes and lowercase SHA-256 digest for every source type;
- UUID, enum, timestamp, Unicode, null, integer, and set-like Evidence-reference
  normalization follow Section 12.3 deterministically;
- external/Human and standards material validate their respective typed
  locator and integrity contracts;
- invalid locator, changed version, missing historical representation, and
  integrity mismatch deterministically reject acceptance;
- if one material source cannot be historically reconstructed, no report,
  provenance, acceptance, success Audit, outbox, or idempotency change commits;
- rollback removes every staged success-path Audit record;
- each required security/authority rejection produces one durable minimal
  rejection Audit after authoritative rollback;
- non-required ordinary validation failures produce no rejection Audit;
- rejection Audit excludes report plaintext, canonical source plaintext,
  minimal historical representations, and sensitive provenance;
- rejection-Audit persistence failure rolls back only its own transaction,
  preserves the original rejection, and cannot mutate Technical Report state;
- idempotent replay reauthorization and conflict behavior;
- duplicate/stale/concurrent acceptance;
- lineage-only creation;
- fresh authorization for every copied predecessor input;
- atomic non-disclosing failure when one copied input is inaccessible;
- no inherited acceptance or supersession;
- abandoned draft creates no lifecycle/retention behavior;
- AI proposal is advisory, non-mutating, attributable, and scope-limited;
- AI cannot accept, construct trusted actor, or expose protected plaintext.

### 24.4 API and negative governance

- every approved route, method, status, and schema;
- authentication headers and trusted Organization derivation;
- pagination/filter limits and protected totals;
- lifecycle/version/error mappings;
- absence of PUT, PATCH, DELETE, publish, approve, Review, supersede, archive,
  and autonomous-AI routes;
- client cannot set accepted state, owner, accepting Human, timestamps,
  accepted versions, or authoritative lineage;
- router contains no SQL, domain policy, or transaction control;
- Audit, outbox, idempotency, logs, errors, and AI diagnostics contain no report
  plaintext or minimal protected source representation;
- full existing backend regression and Alembic single-head check.

## 25. Traceability Matrix

| IDS decision | EDS-032 source | PATCH/ADR constraint | Surface | Verification |
|---|---|---|---|---|
| one Aggregate | §§5, 30 | PATCH §4; ADR Aggregate boundary | model/commands | aggregate tests |
| lifecycle only draft→accepted | §§8, 30 | PATCH §6; ADR lifecycle | enum/model/schema | closed-state tests |
| version/revision separation | §9 | exact-version ADR acceptance | commands/repository | concurrency tests |
| Human Owner exact acceptance | §§11–12 | PATCH §8; ADR Human authority | service/policy | owner/acceptance tests |
| immutable accepted snapshot | §§12, 23 | ADR terminality | model/repository/DB checks | mutation-negative tests |
| trigger-enforced accepted Aggregate immutability | §§12, 23 | PATCH terminal accepted boundary; ADR exact-version terminality | migration/root/provenance persistence | ORM/direct-SQL/flush negative tests |
| restricted runtime/schema-owner role split | §§12, 23 | implementation mechanism for accepted terminality; no new product semantics | runtime config/Alembic/role provisioning/grants | role identity/privilege/ownership/deployment tests |
| empty post-acceptance allow-list | §23 | amended EDS authority | commands/API | prohibited operation tests |
| four provenance classes | §§15–18 | PATCH historical basis | value objects/table/validator | source-class tests |
| typed per-source historical basis | §§15–19 | PATCH authorized intake; ADR historical resolvability | provenance columns/checks/resolver/accepted snapshot | per-source locator/version/digest/failure tests |
| closed historical schemas and deterministic serialization | §§15–19 | implementation mechanism for EDS historical resolvability, canonical ownership, and Manifesto Capture Once | frozen value objects/strict schemas/capability-local serializer | exact-field/additional-field/round-trip/canonical-byte tests |
| Evidence stays canonical | §17 | PATCH §7 | validator/reference only | no ownership-transfer tests |
| successor owns predecessor ref | §13 | ADR lineage-only | model/repository | no predecessor-write tests |
| fresh copy authorization | §13 | EDS amendment | service/policy | atomic denial matrix |
| lineage is not supersession | §13 | ADR successor boundary | query DTO/API | semantic/prohibited-route tests |
| Organization/Workspace/Project scope | §§6, 21 | PATCH §§4, 10 | auth/policy/FKs | cross-scope tests |
| AI advisory only | §24 | PATCH §8; ADR AI boundary | port/adapter/service | authority-negative tests |
| atomic Audit/outbox/idempotency | §§25, 28 | PATCH §4 Audit direction | UoW | rollback/atomicity tests |
| one coherent acceptance transaction | §§12, 16, 21, 26, 28 | PATCH exact-version acceptance; ADR Human authority | UoW-bound policy/reference/history adapters | membership/source/draft race tests |
| durable bounded rejection Audit | §§22, 25–26 | PATCH Audit/accountability; ADR-010 successful Audit baseline | post-rollback rejection-Audit port/adapter | durability/plaintext/failure-isolation tests |
| abandonment is not lifecycle | §22 | PATCH/ADR non-scope | no command/route/table | prohibited-pattern tests |
| no publication/Memory mutation | §§20, 30 | ADR acceptance≠publication | absence across layers | route/event scans |

## 26. Scope-Control Verification

IDS-032 introduces no publication workflow, approval workflow beyond exact
Human acceptance, Review lifecycle/Aggregate, supersession, deletion, archival,
autonomous AI authority, new Organization role, extra report lifecycle state,
Document Management, Organizational Memory admission, Knowledge Graph
authority, or Project-management behavior.

Engineering Review remains only the Human operation implemented as
`accept_exact_draft`. Acceptance remains distinct from publication.

## 27. IDS Blocker Assessment

No implementation-blocking governance question remains at IDS design time.

The focused amendment closes the Independent IDS Review findings as follows:

| Finding | Resolution |
|---|---|
| `IDS032-MAJ-01` | PostgreSQL triggers protect accepted root/provenance state; a distinct non-owner/non-superuser runtime role cannot disable or alter them; migration ownership and credentials are separate; deployment fails closed; accepted reads use only the immutable accepted representation. |
| `IDS032-MAJ-02` | Acceptance-critical mutable reads, validation, compare-and-change, side records, and commit share one UoW Session and explicit lock/version/snapshot predicates. |
| `IDS032-MAJ-03` | The provenance model defines typed per-source locators and four closed `*HistoricalBasisV1` schemas with exact fields/exclusions, deterministic canonical serialization/digest, completeness predicates, accepted-snapshot contents, and source-specific failure tests. |
| `IDS032-MAJ-04` | Successful Audit remains atomic in the authoritative UoW; only defined security/authority rejections use a minimal separate post-rollback Audit transaction with isolated failure behavior. |

These decisions work together without changing the accepted lifecycle or
authority model. Acceptance freezes the report and its finalized provenance;
successor creation inserts a new draft and never mutates the predecessor;
rejection Audit cannot access Technical Report mutation surfaces; and no source
ownership, supersession, Review Aggregate, publication, or additional workflow
is introduced.

The first focused re-review left `IDS032-MAJ-01` and `IDS032-MAJ-03` open. This
second focused amendment addresses their exact remaining issues through Sections
8.1–8.4 and 12.2–12.4. It does not alter the already resolved one-UoW acceptance
strategy or bounded rejection-Audit strategy. Independent confirmation was
completed by the Second Focused Independent IDS-032 Re-review `PASS`. Human IDS
Acceptance subsequently recorded `PASS`. Neither decision grants implementation
authority.

The exact Alembic parent must be reverified immediately before migration
creation because repository head can change; current repository revision
evidence indicates `e02800000001`. This is an execution precondition, not an IDS
architecture ambiguity.

Provider selection and credentials are deployment/configuration concerns behind
the approved provider-neutral AI port. They cannot delay implementation of the
domain boundary and cannot grant AI authority.

## 28. IDS Decision

```text
IDS-032 design: COMPLETE
IDS-032 status: ACCEPTED / COMPLETE
ADR-023 alignment: PASS
PATCH-032 alignment: PASS
EDS-032 alignment: PASS
Repository pattern alignment: PASS
Traceability: PASS
Scope control: PASS
IDS blockers: NONE
Independent IDS Review final status: PASS AFTER FOCUSED AMENDMENTS AND SECOND FOCUSED RE-REVIEW
Human IDS acceptance: PASS
Remaining blocking IDS findings: NONE
Non-blocking observations: IDS032-OBS-01 / IDS032-OBS-02 PRESERVED
Implementation Plan authority: GRANTED
Implementation authority: NOT GRANTED
```

## 29. Revision History

| Version | Date | Description |
|---|---|---|
| 1.0 | 2026-08-09 | Human IDS Acceptance PASS; IDS-032 accepted and complete; Implementation Plan design authorized while implementation authority remains withheld. |
| 0.1 | 2026-08-09 | Complete proposed implementation design for PATCH-032, ready for independent IDS review. |
| 0.2 | 2026-08-09 | Focused amendment resolving IDS032-MAJ-01 through IDS032-MAJ-04: enforceable accepted-state persistence, coherent acceptance transaction, typed historical-basis matrix, and bounded durable rejection Audit. |
| 0.3 | 2026-08-09 | Second focused amendment resolving the remaining MAJ-01 runtime/schema-owner privilege boundary and MAJ-03 closed source-specific historical representations, serialization, completeness, and tests. |
