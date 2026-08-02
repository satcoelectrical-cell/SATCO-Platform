# EDS-027 — Evidence Foundation

## Status

Accepted

## Architecture

Evidence is a separate Aggregate Root. Domain owns identity, lifecycle,
version, Creator immutability, metadata invariants, transitions, and Domain
Events. Application owns trusted scope derivation, authorization, reference
validation, Unit of Work, idempotency, and authorized mapping. Ports are
inward-owned; PostgreSQL is authoritative; FastAPI is transport only.

## Aggregate Fields

- id UUID;
- organization_id UUID;
- project_id nullable positive integer;
- workspace_id nullable positive integer;
- lifecycle controlled as PATCH-027;
- source_kind controlled as PATCH-027;
- source_reference non-empty, maximum 512 characters;
- source_revision non-empty, maximum 128 characters;
- source_standing: `draft`, `current`, `withdrawn`, or `superseded`;
- effective_at nullable timezone-aware timestamp;
- supported_fact non-empty, maximum 2000 characters;
- creator_id positive integer and immutable;
- version positive integer;
- created_at and updated_at timezone-aware timestamps.

Workspace without Project is invalid. Current lifecycle requires current source
standing. Supersession requires a distinct replacement Evidence UUID with
compatible scope. Physical delete and generic mutation are prohibited.

## Commands

- `CreateEvidence`
- `TransitionEvidenceLifecycle`

Creation accepts client source metadata and optional Project/Workspace IDs;
Organization and Creator are trusted context. Transition requires expected
version, rationale, correlation UUID, idempotency UUID, target lifecycle, and
replacement UUID only for supersession.

## Ports and Persistence

Required ports are EvidenceRepository, EvidenceValidator, AuthorizationPolicy,
UnitOfWork, AuditRecorder, DomainEventRecorder, IdempotencyStore, and Clock.

One migration creates `evidence`, `evidence_outbox`, and
`evidence_idempotency`. Audit schema is reused unchanged. Repository never
authorizes, commits, publishes, performs generic update, or deletes.

## Authorization and Compatibility

Organization comes only from PATCH-025. Authorization is deny-by-default and
precedes any identifier, metadata, count, or lifecycle disclosure. Project and
Workspace Evidence requires actor access to that scope. Protected inaccessible
Evidence returns Not Found.

Validator acceptance for PATCH-026 requires existence, visibility, current
lifecycle/source standing, same Organization and: Organization-wide Evidence
for any authorized same-Organization relationship; Project-wide Evidence for
that Project; Workspace Evidence only when its Workspace is one endpoint
Workspace. Cross-Project use is denied.

## API

- `POST /evidence`
- `GET /evidence/{evidence_id}`
- `GET /projects/{project_id}/evidence`
- `POST /evidence/{evidence_id}/lifecycle-transitions`

No PUT, generic PATCH, DELETE, upload, content, or search endpoint is allowed.

## Errors

Stable categories are Validation Error, Authorization Denied, Protected Not
Found, Version Conflict, Idempotency Conflict, Invalid Transition, and Internal
Server Error.

## Acceptance

Aggregate/schema/repository/service/API/migration/security/atomicity/
concurrency/idempotency/validator and full regression tests pass. EDS-027 is
accepted subject to its PASS review and IDS-027.
