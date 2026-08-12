# Independent IDS-032 Review — Technical Report

## 1. Review Identity

| Field | Value |
|---|---|
| Review ID | IDS-032 Independent Review |
| Reviewed artifact | `docs/design/IDS-032-Technical-Report.md` |
| Related PATCH | PATCH-032 — Technical Report |
| Review type | Independent Architecture and Implementation Design Review |
| Date | 2026-08-09 |
| Overall verdict | FAIL |
| Critical findings | 0 |
| Major findings | 4 |
| Minor findings | 0 |
| Observations | 2 |
| Human IDS Acceptance | NOT PERMITTED |
| Implementation authority | NOT GRANTED |

## 2. Authoritative Sources

The review used the current working tree and inspected:

- SATCO Constitution and Engineering Intelligence Manifesto;
- accepted platform Architecture, Backend Blueprint, Database Blueprint, and
  Coding Standards;
- ADR-023;
- PATCH-032 and its recorded Architecture Review, Human Architecture
  Acceptance, and QG-M1 decisions;
- EDS-032, its preserved initial review failure, focused amendment, Focused
  Independent Re-review PASS, Human EDS Acceptance PASS, and governance
  reconciliation;
- Governance Model and Roadmaps;
- EngineeringObject, Engineering Relationship, Evidence, Universal Capture,
  Engineering Journal, Project, Workspace, Organization, and authentication
  authorities.

No standalone Technical Report Architecture Discovery or PATCH-032 Architecture
Review artifact was found; the accepted decisions were inspected through
ADR-023, PATCH-032, EDS-032, Roadmap, and Governance Model as those documents
explicitly record.

## 3. Repository Evidence Inspected

The review independently inspected current implementations and tests for:

- SQLAlchemy aggregate models and command contracts;
- repository expected-version compare-and-change;
- capability-owned Unit of Work patterns;
- Audit, Domain Event outbox, and idempotency adapters;
- Pydantic v2 schemas;
- FastAPI request-scoped composition;
- authenticated Organization context;
- Workspace/Project visibility and membership;
- protected-not-found behavior;
- Capture, Evidence, EngineeringObject, and Relationship reference behavior;
- Alembic revision structure and model/migration tests.

Repository reality confirms that current SQLAlchemy entities are mutable ORM
objects, repositories avoid commits, Unit of Work owns transaction commit and
rollback, and policy/reference adapters are not consistently bound to the same
session as the command Unit of Work. Existing canonical sources also do not
share one universal immutable historical-snapshot contract.

## 4. Review Methodology

The Board traced every significant IDS decision to ADR-023, PATCH-032,
EDS-032, or necessary current infrastructure. It then attempted to implement
the design conceptually through the declared file map and tested for authority,
immutability, concurrency, source-history, transaction, mass-assignment,
direct-ORM, AI, lineage, and disclosure bypasses.

Ambiguous wording was treated as permitting the least safe conforming
implementation. A finding was recorded whenever implementation would require a
new architectural choice or could satisfy the IDS while violating accepted
authority.

## 5. Findings

### IDS032-MAJ-01 — Accepted-state immutability is not enforceable against declared persistence bypasses

- **Severity:** MAJOR
- **IDS section:** 7, 8, 9, 17, 21, 24
- **Authoritative evidence:** EDS-032 §§5.3, 9.3, 12, and 23 require the accepted
  Aggregate to be terminal and mutation-free, with an empty post-acceptance
  mutation allow-list.
- **Repository evidence:** current SQLAlchemy Aggregate objects and sessions
  permit ordinary attribute mutation and flush; current database conventions
  do not automatically make accepted rows immutable.
- **Exact issue:** IDS-032 relies on Aggregate methods, absence of service and
  repository commands, update predicates, and coherence checks, while
  explicitly rejecting a database enforcement mechanism. Its checks require
  acceptance fields to remain mutually coherent but do not prevent a direct
  ORM or SQL update that changes draft columns, provenance children, and the
  accepted snapshot together. The IDS also does not require accepted reads to
  derive exclusively from the immutable snapshot rather than mutable working
  columns or provenance rows.
- **Risk:** an internal service, maintenance path, future repository method, or
  direct ORM use can silently rewrite the exact content and basis to which Human
  acceptance applies while all declared database checks remain valid.
- **Required correction:** define one enforceable persistence invariant that
  prevents every update to an accepted report and its Aggregate-owned
  provenance through normal application credentials, or define an immutable
  accepted-record structure that has no update path and make accepted reads use
  it exclusively. Specify how ORM flush bypass is prevented, the allowed
  database enforcement compatible with repository architecture, and direct
  negative tests at the session/persistence boundary.

### IDS032-MAJ-02 — Acceptance-basis validation is not transaction-consistent

- **Severity:** MAJOR
- **IDS section:** 10, 12, 14, 21, 22
- **Authoritative evidence:** EDS-032 §§9.3, 12, 16–18, 21, and 28 require stale
  acceptance to fail atomically and every material source to be authorized and
  historically resolvable at acceptance.
- **Repository evidence:** existing relationship and Capture composition can
  construct authorization/reference adapters with a request session while a
  capability Unit of Work opens a separate `SessionLocal` transaction. Current
  patterns therefore do not prove one shared acceptance snapshot automatically.
- **Exact issue:** IDS-032 calls policy, reference, and historical resolver
  objects “service collaborators” outside transaction ownership but does not
  require them to be bound to the same Unit of Work session or define source
  locking/version predicates. A source, Workspace membership, or source
  availability can change after validation and before acceptance commit.
- **Risk:** acceptance may commit against a material basis or authorization
  state different from the state actually validated, defeating exact-version
  Human acceptance and authorization-at-acceptance requirements.
- **Required correction:** define request-scoped construction in which
  acceptance authorization, context validation, historical resolution,
  Aggregate compare-and-change, Audit, outbox, and idempotency execute against
  one explicit transactional consistency strategy. For each mutable canonical
  source, specify version/snapshot verification or necessary row-lock behavior
  and how a changed dependency forces rollback without disclosure.

### IDS032-MAJ-03 — Canonical historical-resolvability persistence remains underspecified

- **Severity:** MAJOR
- **IDS section:** 7.2, 12, 13, 17, 22
- **Authoritative evidence:** amended EDS-032 §§15–18 deterministically require
  a material canonical source to have an immutable source version, immutable
  snapshot identity, or integrity-protected historical representation sufficient
  to resolve the relied-upon state.
- **Repository evidence:** Capture, Evidence, EngineeringObject, and Engineering
  Relationship do not expose one common immutable historical representation;
  some retain mutable lifecycle/version state without a general version-history
  store. The IDS prohibits changes to those canonical modules.
- **Exact issue:** the provenance table specifies only an “applicable locator”
  and generic historical/integrity fields. It does not define the typed locator
  columns, constraints, source-version capture, minimum canonical representation,
  or deterministic fallback for each approved canonical source. The accepted
  snapshot is said to contain the manifest, but the IDS does not establish
  whether it contains enough source state to reconstruct material meaning when
  the canonical row later changes.
- **Risk:** an implementer must invent per-source history semantics, reject valid
  reports indefinitely, or store arbitrary protected plaintext. Any choice can
  violate canonical ownership, Capture Once, or accepted-report reproducibility.
- **Required correction:** provide an exact per-source compatibility matrix for
  Universal Capture, Evidence, EngineeringObject, Engineering Relationship, and
  any other approved canonical source. Name the stable identity/version or
  integrity representation used, the exact report-owned acceptance-time fields,
  typed persistence columns and checks, and the failure rule when the source
  cannot satisfy historical reconstruction. Preserve the prohibition on a
  generic source repository.

### IDS032-MAJ-04 — Durable rejected-operation Audit semantics are unresolved

- **Severity:** MAJOR
- **IDS section:** 10, 14, 15, 24
- **Authoritative evidence:** EDS-032 §§22 and 25 preserve independently required
  Audit accountability while prohibiting Audit as alternate plaintext storage.
  IDS-032 itself requires rejected authoritative operations to be audited where
  existing governance requires it.
- **Repository evidence:** current capability Audit recorders share the command
  Unit of Work session. A command rollback also rolls back an Audit row staged
  in that transaction.
- **Exact issue:** IDS-032 defines one atomic transaction for successful report,
  Audit, outbox, and idempotency writes but never defines how a rejected
  acceptance or authority violation produces durable required Audit evidence
  after that transaction rolls back. The test plan requests rejected-operation
  accountability without naming the boundary that can persist it safely.
- **Risk:** required security/accountability evidence is silently lost, or an
  implementer invents an independent transaction that leaks protected report or
  source information and conflicts with Unit of Work ownership.
- **Required correction:** distinguish successful command Audit inside the
  atomic Unit of Work from required rejection Audit. Define the approved durable
  rejection-recording boundary, minimal non-sensitive payload, failure behavior,
  and transaction ownership using existing Audit infrastructure or explicitly
  mark the requirement as not applicable when governance does not require a
  durable rejection record. Add rollback and plaintext-exclusion tests.

## 6. Observations

### IDS032-OBS-01 — AI adapter directory is architecture-compatible but new in repository reality

- **Severity:** OBSERVATION
- **IDS section:** 16, 22
- **Evidence:** Backend Blueprint reserves `app/ai/`; the current backend has no
  implemented `app/ai/` source package.
- **Issue:** the proposed provider-neutral path is compatible with documented
  architecture but is not reuse of an existing concrete module pattern.
- **Risk:** none if the later plan keeps provider isolation and does not broaden
  PATCH-032.
- **Required correction:** none; Implementation Plan review should verify the
  bounded package initialization/file manifest.

### IDS032-OBS-02 — Migration parent must remain an execution gate

- **Severity:** OBSERVATION
- **IDS section:** 3, 22, 27
- **Evidence:** revision files currently indicate `e02800000001` as head, while
  the local shell does not expose an `alembic` executable for independent CLI
  confirmation.
- **Issue:** IDS correctly makes parent verification an implementation-time
  precondition.
- **Risk:** a later concurrent migration could invalidate the proposed parent.
- **Required correction:** none in IDS beyond retaining the explicit stop gate.

## 7. Traceability Assessment

**FAIL.** The primary lifecycle, Human authority, lineage, AI, and scope
decisions trace correctly. Historical-resolvability and rejection-Audit
implementation decisions do not trace to an executable repository contract,
and the declared accepted-immutability enforcement is weaker than EDS-032.

## 8. Repository-Alignment Assessment

**FAIL.** Folder, schema, repository no-commit, UoW, exception, router, outbox,
idempotency, and authentication patterns are substantially aligned. However,
the IDS assumes transaction-consistent collaborators and enforceable accepted
immutability that current patterns do not provide automatically, without
specifying the necessary bounded adaptation.

## 9. Authority-Boundary Assessment

**PASS.** Human Owner identity is server-derived, self-review is preserved, AI
is non-authoritative, transport cannot set acceptance metadata, and no
publication, Review Aggregate, enterprise workflow, or supersession authority
is introduced.

## 10. Aggregate and Lifecycle Assessment

**PASS.** One `TechnicalReport` Aggregate is preserved; lifecycle remains
exactly `draft → accepted`; successor identity is new; predecessor mutation and
acceptance inheritance are prohibited.

## 11. Accepted-Immutability Assessment

**FAIL.** The application and repository command surface is appropriately
closed, but the declared persistence design leaves a credible direct ORM/SQL
mutation bypass and does not make accepted-read authority exclusive to an
immutable representation.

## 12. Concurrency and Transaction Assessment

**FAIL.** Aggregate optimistic locking and atomic state/Audit/outbox/idempotency
commit are well directed, but material-source and authorization validation are
not tied to a defined transactional consistency mechanism. Rejected Audit
durability is also unresolved.

## 13. Persistence and Repository Assessment

**FAIL.** Repository no-commit/no-authority/no-generic-update rules pass.
Persistence fails review because accepted immutability and typed per-source
historical reconstruction remain incomplete.

## 14. Application, API, and DTO Assessment

**PASS.** Authorized operations are bounded and transport remains thin. Server
fields are protected, exact acceptance inputs are explicit, list/detail
disclosure is separated, and prohibited routes are named.

## 15. Successor and Lineage Assessment

**PASS.** The successor exclusively owns the predecessor reference, lineage-only
creation is supported, copied inputs require fresh authorization, atomic copy
failure is non-disclosing, and no supersession meaning is introduced.

## 16. AI and Abandoned-Draft Assessment

**PASS.** AI proposal generation is non-authoritative and non-mutating.
Abandonment remains outside lifecycle and does not create permanent domain
retention or plaintext Audit storage.

## 17. Error-Model Assessment

**PASS.** Stable categories cover protected not found, authorization, lifecycle,
immutability, concurrency, idempotency, context, source history, lineage, AI,
and internal failures without exposing persistence details.

## 18. Test-Design Assessment

**FAIL.** Positive and negative governance coverage is broad, including all
mandated Human/AI/lifecycle/lineage cases. It lacks exact tests proving the
missing persistence-level immutability mechanism, same-transaction mutable
source validation, per-source historical reconstruction, and durable rejected
Audit behavior.

## 19. Scope-Control Assessment

**PASS.** No unauthorized lifecycle, Review, publication, Organizational
Memory, Knowledge Graph, Document Management, deletion, archival, or
supersession capability is introduced.

## 20. Overall Verdict

```text
Independent IDS-032 Review: COMPLETE
Overall verdict: FAIL
Critical findings: 0
Major findings: 4
Minor findings: 0
Observations: 2
Permission for Human IDS Acceptance: NOT GRANTED
Permission for Implementation Plan: NOT GRANTED
Implementation authority: NOT GRANTED
```

## 21. Required Next Governance Action

Perform one focused IDS-032 amendment resolving IDS032-MAJ-01 through
IDS032-MAJ-04. Preserve this failed review as historical evidence. After the
amendment, conduct a Focused Independent IDS-032 Re-review. Human IDS Acceptance
may be considered only after that re-review records `PASS` with no Critical or
Major finding.

## 22. Integrity Record

This review created only this artifact. IDS-032, EDS-032, PATCH-032, governance
documents, source code, migrations, and implementation-plan records were not
modified. No implementation, migration, commit, or push authority was granted.

## 23. Revision History

| Version | Date | Description |
|---|---|---|
| 1.0 | 2026-08-09 | Independent IDS-032 review completed with FAIL, four Major Findings, and two non-blocking observations. |

## 24. Focused Independent IDS-032 Re-review

### 24.1 Re-review identity and scope

| Field | Value |
|---|---|
| Review type | Focused Independent IDS Re-review |
| Date | 2026-08-09 |
| Amended artifact | `docs/design/IDS-032-Technical-Report.md`, revision 0.2 |
| Historical predecessor | Initial Independent IDS-032 Review — FAIL |
| Scope | `IDS032-MAJ-01` through `IDS032-MAJ-04` only, plus amendment-induced Critical/Major contradictions |
| Focused verdict | FAIL |
| Critical findings | 0 |
| Previous Major findings resolved | 2 |
| Previous Major findings not resolved | 2 |
| New Major findings | 0 |
| Minor findings | 0 |
| Observations | 2 retained |
| Human IDS Acceptance | NOT PERMITTED |
| Implementation authority | NOT GRANTED |

The historical chain is:

```text
Initial Independent IDS Review — FAIL
→ Focused IDS Amendment
→ Focused Independent IDS Re-review — FAIL
```

### 24.2 Evidence inspected

The Board inspected the amended IDS, this preserved initial review, EDS-032,
PATCH-032, ADR-023, ADR-010, the EngineeringObject Blueprint Audit distinction,
the active Docker/PostgreSQL configuration, SQLAlchemy engine and SessionLocal,
existing capability Unit of Work implementations, Audit model/adapters,
canonical Capture, Evidence, EngineeringObject, and Engineering Relationship
models, repository contracts, migration conventions, and the amended test and
file maps.

Repository evidence material to the focused decision is:

- current UoWs prove that policy, reference, repository, Audit, outbox, and
  idempotency adapters can share one capability-owned SQLAlchemy Session;
- all four named canonical engineering source models expose stable UUID identity
  and positive optimistic version;
- the current `audit_logs` model accepts a UUID entity identity and bounded JSON
  details, so a separate minimal post-rollback recorder can reuse it without an
  Audit schema change;
- `docker-compose.yml` uses `POSTGRES_USER=satco`, and the backend uses the same
  `satco` credential; PostgreSQL initializes that user as the database superuser
  and owner rather than a privilege-separated non-bypass application role;
- no existing source model provides the universal immutable historical snapshot
  assumed as an optional alternative, so the report-owned fallback must be exact
  for each source type.

### 24.3 Major-finding resolution

#### IDS032-MAJ-01 — NOT RESOLVED

The amendment correctly specifies root and provenance triggers, parent-row
serialization, accepted-snapshot-only reads, privileged-operation separation,
successor isolation, and direct ORM/SQL negative tests. Ordinary ORM mutation
and flush would invoke those triggers.

The claimed privilege invariant is not implementable through the declared file
map against current repository reality. The backend and Alembic currently use
the same `satco` PostgreSQL superuser/owner credential. That role can bypass or
disable ordinary user triggers, while IDS §8 claims the application role has no
trigger-bypass or trigger-disable privilege. IDS §22 neither authorizes a
privilege-separated runtime role/configuration surface nor defines a PostgreSQL
mechanism that remains enforced for the current application credential. The
design therefore still does not prove that accepted root and provenance state
cannot be mutated through normal configured application credentials.

Required correction remains: define the exact repository-compatible database
role/ownership and migration/runtime credential boundary that makes the trigger
invariant non-bypassable by the runtime application role, include its exact
authorized configuration/migration surfaces, and test both permitted acceptance
and denied post-acceptance writes using the actual restricted runtime role.

#### IDS032-MAJ-02 — RESOLVED

IDS §§10 and 14 now require one Technical Report UoW Session for every mutable
acceptance-critical read and write. They explicitly exclude an unrelated request
Session, lock the report and mutable authority/context basis, require source
lock or identity/version recheck, bind provenance/Audit/outbox/idempotency to the
same transaction, roll back on every changed dependency, and define
non-disclosing failure semantics. The race-test design covers membership,
context, source, and report changes. This is compatible with current
PostgreSQL/SQLAlchemy UoW construction and introduces no distributed
transaction.

#### IDS032-MAJ-03 — NOT RESOLVED

The amendment adds typed discriminator/locator columns, positive versions,
integrity algorithm/digest, per-source ownership, acceptance validation, failure
rules, accepted-snapshot contents, and an explicit prohibition on a generic
source repository or ownership transfer.

The decisive fallback remains underspecified. For each canonical source the
matrix names only a “minimal relied-upon representation,” “accepted fact/source
basis,” “classification/lifecycle/authority/scope context actually relied
upon,” or relationship state “actually relied upon.” It does not define the
closed typed fields or schema of those JSON representations. The design therefore
still permits materially different implementations to omit acceptance-relevant
source state or persist excessive protected plaintext. Because current canonical
modules do not provide immutable snapshots, this fallback is the expected path,
not an exceptional detail. The proposed tests repeat the categories but cannot
prove completeness without an exact per-source representation contract.

Required correction remains: define a closed typed minimum historical
representation for Capture, Evidence, EngineeringObject, and Engineering
Relationship, naming every accepted field and exclusion for each, its canonical
serialization/digest input, and source-specific completeness tests. If an exact
minimum cannot be derived from EDS authority, record an IDS blocker rather than
leaving implementation discretion.

#### IDS032-MAJ-04 — RESOLVED

IDS §§10 and 15 now separate successful-command Audit inside the authoritative
UoW from a bounded rejection/security Audit after rollback. The latter has an
explicit separate transaction owner, a closed set of required security/authority
categories, minimal actor/operation/safe-identifier/reason/time/correlation
metadata, plaintext and sensitive-provenance prohibitions, no Technical Report
mutation access, deterministic isolated failure behavior, and no ability to
convert rejection into success. Tests cover success-Audit rollback, durable
required rejection evidence, excluded content, non-required failures, and
recorder failure isolation. The existing Audit table can represent the bounded
record without becoming report-content persistence.

### 24.4 New findings and observations

No new Critical or Major finding was introduced. The two original observations
remain non-blocking and unchanged:

- `IDS032-OBS-01` — verify the bounded new `app/ai/` package during later plan
  review;
- `IDS032-OBS-02` — reverify the Alembic parent immediately before migration
  design/execution.

### 24.5 Cross-finding, traceability, and authority assessment

The resolved transaction and Audit amendments are mutually consistent.
Rejection Audit cannot mutate report state; acceptance and successful side
records share one transaction; lifecycle remains only `draft → accepted`;
successor creation does not mutate the predecessor; no supersession semantics
or new workflow exists; AI remains non-authoritative; and the Human Owner remains
the acceptance authority.

Traceability remains **FAIL** because the still-open accepted-state enforcement
and historical-representation contracts do not yet provide executable mappings
from EDS-032 terminality and historical-resolvability requirements. Authority
boundaries otherwise remain **PASS**, and PATCH-032 semantic scope remains
unchanged.

Repository alignment remains **FAIL** because the trigger privilege assumption
conflicts with the configured PostgreSQL role and the per-source fallback schemas
remain incomplete against source-model reality.

### 24.6 Focused verdict

```text
Focused Independent IDS-032 Re-review: COMPLETE
Focused verdict: FAIL
IDS032-MAJ-01: NOT RESOLVED
IDS032-MAJ-02: RESOLVED
IDS032-MAJ-03: NOT RESOLVED
IDS032-MAJ-04: RESOLVED
New Critical findings: 0
New Major findings: 0
Minor findings: 0
Observations: 2 retained
Traceability: FAIL
Repository alignment: FAIL
Authority boundaries: PASS
Accepted immutability: FAIL
Concurrency / transaction consistency: PASS
Historical resolvability: FAIL
Audit accountability: PASS
Permission for Human IDS Acceptance: NOT GRANTED
Implementation authority: NOT GRANTED
```

### 24.7 Required next governance action

Perform a second focused IDS-032 amendment limited to `IDS032-MAJ-01` and
`IDS032-MAJ-03`, then repeat the focused Independent IDS re-review. Human IDS
Acceptance remains blocked until both findings are resolved with no Critical or
Major finding.

### 24.8 Re-review integrity record

This focused re-review appends only to
`docs/reviews/IDS-032-Technical-Report-Review.md`. It does not modify IDS-032,
EDS-032, PATCH-032, source code, migrations, or an Implementation Plan. It grants
no implementation, migration, commit, or push authority.

## 25. Review Revision History

| Version | Date | Description |
|---|---|---|
| 1.1 | 2026-08-09 | Focused Independent IDS-032 Re-review completed with FAIL; MAJ-02 and MAJ-04 resolved; MAJ-01 and MAJ-03 remain blocking. |

## 26. Second Focused Independent IDS-032 Re-review

### 26.1 Re-review identity and scope

| Field | Value |
|---|---|
| Review type | Second Focused Independent IDS Re-review |
| Date | 2026-08-09 |
| Amended artifact | `docs/design/IDS-032-Technical-Report.md`, revision 0.3 |
| Scope | `IDS032-MAJ-01` and `IDS032-MAJ-03`, plus preservation of resolved `IDS032-MAJ-02` and `IDS032-MAJ-04` |
| Second focused verdict | PASS |
| Critical findings | 0 |
| Major findings | 0 |
| Minor findings | 0 |
| Observations | 2 retained |
| Human IDS Acceptance | PERMITTED AS NEXT GOVERNANCE ACTION |
| Implementation authority | NOT GRANTED |

The complete historical chain remains:

```text
Initial Independent IDS Review — FAIL
→ Focused IDS Amendment
→ First Focused Independent IDS Re-review — FAIL
→ Second Focused IDS Amendment
→ Second Focused Independent IDS Re-review — PASS
```

### 26.2 Evidence inspected

The Board inspected IDS-032 revision 0.3, all prior review findings and verdicts,
EDS-032, PATCH-032, ADR-023, current SQLAlchemy engine/SessionLocal and UoW
patterns, `backend/app/core/config.py`, `backend/app/core/database.py`,
`backend/migrations/env.py`, `docker-compose.yml`, PostgreSQL role/ownership and
trigger semantics, migration trigger conventions, test database bootstrap, and
the current Capture, Evidence, EngineeringObject, and Engineering Relationship
models, commands, schemas, enums, authorization adapters, and version behavior.

The repository still uses the same `satco` PostgreSQL superuser/owner credential
for runtime and migration today. The amended IDS correctly treats that as a
pre-implementation deployment blocker and names the bounded future repository
surfaces required to replace it. The canonical source field mappings were
checked against actual model and schema fields rather than inferred names.

### 26.3 IDS032-MAJ-01 — RESOLVED

The amended IDS defines an exact migration/runtime privilege boundary:

- migration uses explicit `ALEMBIC_DATABASE_URL` and a schema-owner credential
  that owns Technical Report tables, functions, and triggers;
- normal backend runtime uses the separate `DATABASE_*` credential and the
  repository-managed `satco_runtime` role;
- runtime is `NOSUPERUSER`, `NOBYPASSRLS`, `NOCREATEDB`, `NOCREATEROLE`, is not
  a schema-owner member, owns no protected object, and has no trigger-management,
  ownership-changing, schema-creation, or trigger-bypass setting authority;
- root and provenance DML grants are bounded to legitimate draft and acceptance
  behavior, while trigger functions remain schema-owner-owned with direct
  execution revoked;
- root/provenance triggers serialize against the parent and reject every
  post-acceptance write through the restricted role, including ORM flush and
  direct SQL;
- current privileged runtime reality is explicitly acknowledged rather than
  treated as compliant;
- startup and deployment fail closed for identical credentials, privileged or
  owning runtime identity, or missing/disabled enforcement;
- schema-owner/DBA authority is correctly outside the claimed normal-runtime
  protection boundary.

The authorized future file map covers runtime configuration, startup preflight,
Alembic identity enforcement, Docker/local role provisioning, migration grants
and triggers, isolated role fixtures, and dedicated role tests. The role-init
surface is compatible with the existing repository-managed PostgreSQL container;
existing databases require equivalent owner-operated provisioning rather than
relying on initialization replay.

The test design proves permitted draft and acceptance operations and denies
accepted root/provenance mutation, trigger/function alteration, trigger disable
or drop, ownership change, privilege escalation, ORM flush bypass, direct SQL
bypass, and same-role deployment. The invariant is enforceable against the
defined normal runtime role and makes no claim against a malicious PostgreSQL
superuser.

### 26.4 IDS032-MAJ-03 — RESOLVED

The amended IDS defines four named, closed historical contracts:

- `CaptureHistoricalBasisV1`;
- `EvidenceHistoricalBasisV1`;
- `EngineeringObjectHistoricalBasisV1`;
- `EngineeringRelationshipHistoricalBasisV1`.

Each contract names every required or explicit-null optional field, maps it to
an actual canonical model field and type, defines normalization and
acceptance relevance, includes every declared field in serialization/digest,
rejects undeclared fields, and provides an explicit exclusion list.

The Capture basis uses the actual bounded normalized `original_content`, source
reference, source kind, scope, creator, lifecycle, version, and creation time
needed to reconstruct captured material meaning. It excludes attachments,
unrelated payload, replacement navigation, diagnostics, secrets, and transient
state. EDS-032 authorizes the bounded acceptance-time historical representation;
Universal Capture retains live identity and lifecycle authority.

The Evidence basis maps the current metadata-only Evidence Aggregate without
inventing file or document payload. The EngineeringObject basis maps approved
scope, classification, lifecycle, authority, and accountability fields without
nested Aggregate content. The Engineering Relationship basis preserves stable
identity, ordered endpoint direction, family/type discriminator, lifecycle,
authority, scope, Evidence identities, and accountability without copying
endpoint or Evidence content. Material reliance on referenced Evidence requires
a separate authorized Evidence basis.

Engineering Journal is correctly excluded as a canonical source identity.
External/Human and standards material remain under their distinct EDS source
contracts. No generic source repository, alternate canonical owner, unrestricted
archive, or additional source capability is introduced.

The capability-local canonical JSON contract deterministically defines closed
field validation, lexicographic nested key ordering, explicit nulls, UTF-8,
RFC 8259 escaping, NFC strings, lowercase canonical UUIDs, enum values, integers,
booleans, UTC timestamps, array semantics, and undeclared-field rejection. The
digest is lowercase hexadecimal SHA-256 over the exact canonical UTF-8 bytes,
including source category, identity, version, scope, state, and explicit nulls.

The completeness predicate fails acceptance when native immutable history or a
complete typed fallback cannot be authorized, resolved, serialized, digested,
stored, and reverified at the same version. The test matrix covers complete and
missing bases, extra fields, normalization, serialization, digest stability,
integrity mismatch, source-version change, unavailable meaning, excessive
plaintext, and bounded semantic reconstruction for every canonical category.

### 26.5 Preservation of prior resolutions

`IDS032-MAJ-02` is **PRESERVED**. Acceptance-critical mutable state remains bound
to one Technical Report UoW Session with explicit locking/version/snapshot
checks, atomic compare-and-change, and rollback on changed authority, context,
source, or report state.

`IDS032-MAJ-04` is **PRESERVED**. Successful-command Audit remains inside the
authoritative command UoW. Only bounded required security/authority rejection
Audit uses the separate post-rollback transaction, minimal non-sensitive
payload, isolated failure behavior, and no Technical Report mutation path.

### 26.6 Traceability, repository alignment, and authority

Traceability is **PASS**. Terminal accepted immutability and the empty mutation
allow-list trace to EDS-032 and ADR-023; PostgreSQL role separation is correctly
identified as an implementation mechanism. Closed historical bases trace to
EDS-032 source intake, provenance, Evidence, standards, and context boundaries,
while capability-local serialization implements integrity without adding
product semantics. Capture Once and canonical ownership remain intact.

Repository alignment is **PASS**. The proposed role split uses existing runtime
`DATABASE_*` and migration `ALEMBIC_DATABASE_URL` configuration paths, existing
Alembic ownership, PostgreSQL trigger migrations, SQLAlchemy UoW/session patterns,
strict Pydantic contracts, and current canonical source fields. Required new
role provisioning and verification surfaces are explicitly bounded rather than
assumed to exist.

Authority boundaries are **PASS**. Lifecycle remains exactly
`draft → accepted`; the Human Owner remains the only Version 1 acceptance
authority; AI remains advisory and non-authoritative; accepted content and
provenance become immutable; successor lineage does not mutate or supersede the
predecessor; and PATCH-032 scope is unchanged.

### 26.7 Second focused verdict

```text
Second Focused Independent IDS-032 Re-review: COMPLETE
Second focused verdict: PASS
IDS032-MAJ-01: RESOLVED
Runtime DB role boundary: PASS
Runtime immutability enforcement: PASS
IDS032-MAJ-03: RESOLVED
Closed historical contracts: PASS
Canonical serialization: PASS
Historical completeness: PASS
IDS032-MAJ-02 preservation: PRESERVED
IDS032-MAJ-04 preservation: PRESERVED
New Critical findings: 0
New Major findings: 0
Minor findings: 0
Observations: 2 retained
Traceability: PASS
Repository alignment: PASS
Authority boundary: PASS
Accepted immutability: PASS
Concurrency / transaction: PASS
Historical resolvability: PASS
Audit accountability: PASS
Permission for Human IDS Acceptance: GRANTED
Implementation authority: NOT GRANTED
```

### 26.8 Required next governance action

Perform Human IDS-032 Acceptance against the complete IDS and preserved review
history. Do not create an Implementation Plan or grant implementation authority
before that Human gate passes and governance is reconciled.

### 26.9 Integrity record

This second focused re-review appends only to
`docs/reviews/IDS-032-Technical-Report-Review.md`. IDS-032, EDS-032, PATCH-032,
source code, migrations, and implementation-plan records were not modified. No
implementation, migration, commit, or push authority was granted.

## 27. Review Revision History

| Version | Date | Description |
|---|---|---|
| 1.2 | 2026-08-09 | Second Focused Independent IDS-032 Re-review completed with PASS; MAJ-01 and MAJ-03 resolved; MAJ-02 and MAJ-04 preserved. |
