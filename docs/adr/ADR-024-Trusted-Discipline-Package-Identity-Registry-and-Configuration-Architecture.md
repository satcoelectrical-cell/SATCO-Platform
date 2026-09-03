# ADR-024 — Trusted Discipline Package Identity, Registry & Configuration Architecture

## Status

Accepted

## Date

2026-08-29

## Decision Owner

- Human Architecture Authority

## Approval Record

| Field | Value |
|---|---|
| ADR preparation | PASS / COMPLETE under HUMAN ADR-024 PREPARATION AUTHORITY: GRANTED |
| Independent ADR review | PASS / ACCEPTED; Critical/Major/Minor `0/0/0` |
| Human ADR acceptance | PASS / GRANTED on 2026-08-29 |
| Related PATCH | PATCH-051 — Shared Multi-Discipline Core & Discipline Package Contract |
| Architecture basis | Architecture-051 eligible for Human Architecture Acceptance; not yet Human-accepted |
| Focused Architecture re-review | PASS / ACCEPTED; `A051-MAJ-01` RESOLVED / CLOSED |
| Inherited observations | `A051-OBS-01`, `A051-OBS-02`, `A051-OBS-03` — non-blocking / EDS-deferred |
| EDS / IDS / implementation | NOT STARTED / NOT STARTED / NOT AUTHORIZED |

This accepted decision establishes architectural authority within its scope.
It does not Human-accept Architecture-051 and grants no implementation,
migration, EDS, IDS or PATCH-052 authority.

## Context

SATCO already has shared Organization, Project, single-Discipline Workspace,
Engineering Context, Engineering Knowledge Graph, Evidence, Technical Report,
Organizational Memory, Guidance, Audit and authorization foundations. Its
Discipline identity is nevertheless fragmented across Workspace and EKG enums,
explicit translation maps, free-text fields, accepted historical snapshots and
frontend literals.

Commercial V1 requires later operational Electrical, Instrumentation and
Control & Automation packages. The same platform must truthfully retain
Mechanical, Civil, Process and future Disciplines for which no operational
package exists. It must do so without Core forks, customer-authored execution,
commercial state redefining engineering meaning, or reinterpretation of
accepted history.

Architecture-051 defines a trusted modular package kernel and reconciles its
original package-cardinality defect. Its focused independent re-review is PASS,
with `A051-MAJ-01` closed and no new Critical or Major finding. This ADR is the
required durable decision record before final Human Architecture-051
Acceptance.

## Problem

Without one durable identity, registry, configuration and authority decision,
later package work could:

- conflate stable Discipline meaning with versioned package capability;
- normalize unrelated legacy strings into one false identity;
- make a database or runtime loader competing package authority;
- let Workspaces choose versions independently from their Projects;
- require fabricated package state for empty Projects or future Disciplines;
- confuse package configuration, data authorization and commercial
  entitlement;
- fork Core or canonical engineering aggregates by Discipline; or
- silently reinterpret Reports, Memory, Audit and raw legacy history.

The architecture needs governed extensibility without becoming a generic
plugin platform and exact compatibility without premature physical design.

## Decision Drivers

- stable professional-engineering meaning across product and package change;
- one product, one Core and no customer/source/database forks;
- exact historical preservation and rollback readability;
- Project-level reproducibility through exact version pinning;
- truthful support for empty Projects and unavailable future Disciplines;
- deterministic, release-governed package composition;
- authorization-before-disclosure and strict tenant isolation;
- finite, reviewable and conformant package contributions;
- existing canonical aggregate and Human authority preservation; and
- attachment of future signed entitlements without identity redesign.

## Decision

SATCO shall use a trusted, source-controlled, versioned Discipline Package
contract governed by the following decisions.

### 1. Discipline and Discipline Package are separate

A **Discipline** is a stable Core-governed professional-engineering
classification. It scopes engineering meaning, responsibility and Workspace
identity. It is independent of commercial packaging, package version,
configuration, entitlement and authorization.

A **Discipline Package** is a trusted SATCO-governed capability bundle with a
stable `PackageKey`, explicit `PackageVersion`, one declared primary Discipline
and bounded contributions under the Core contract. A package may be supported,
configured and exactly version-pinned.

The namespaces are separate even where initial string values coincide. A
Discipline may exist without an operational package. Package availability,
version or commercial state never changes Discipline meaning.

### 2. Canonical typed identities are Core-owned

Core owns distinct typed identities for:

- `DisciplineId`;
- `PackageKey`;
- `PackageVersion`;
- `CoreContractVersion`;
- `EntitlementKey`;
- compatibility-profile identity; and
- descriptor, selected-configuration/profile and release-registry provenance
  identities where required.

Machine identities are governed, bounded and not customer-editable display
labels. Equality is not inferred across typed namespaces. The descriptor
explicitly maps a package to its primary Discipline.

Digest roles remain semantically distinct: a release-wide registry digest
identifies the trusted registry release; a descriptor digest identifies one
package descriptor/version; selected descriptor-set and compatibility-profile
provenance identify a Project's reproducible selection. Physical types,
canonical bytes, exact algorithms and vectors remain EDS decisions.

### 3. Legacy semantics are reconciled exactly

Legacy identity is interpreted by source contract, never by global string
replacement:

- Workspace `control` may map exactly to canonical Discipline/package
  `control_automation`;
- EKG `industrial_automation` may map exactly to canonical Discipline/package
  `control_automation`;
- `automation` remains an Engineering Object/Relationship family identity;
- `automation_and_control` remains a Guidance/material category identity; and
- unknown or ambiguous free text remains `legacy_unresolved` until explicit
  Human reconciliation.

Exact canonical and exact legacy-alias mappings are allowed. Case folding,
substring or similarity matching, fuzzy reconciliation, fabricated
`PackageKey` assignment, silent reinterpretation and global semantic
replacement are prohibited. Raw historical identity is retained where needed
for truth and provenance.

### 4. The trusted Package Registry is source and release authority

The authoritative Discipline Package Registry is immutable,
source-controlled, version-controlled and release-bound. It consists of
Core-validated declarative descriptors plus explicitly registered,
SATCO-owned adapters.

A database representation may exist only as a derived installed-registry
projection for integrity, history, configuration linkage and bounded
operational lookup. It is not a customer-editable or competing package
authority. Code, release manifest and projection drift fails closed at startup
or readiness.

Historical descriptor retention supports authorized reading and provenance.
Retention alone does not make a version selectable or executable; exact
version standing remains an EDS obligation.

### 5. Extension is trusted and static, not a generic plugin model

Future packages use the same Core-owned contract, closed contribution
categories, explicit composition-root registration, conformance gate and
release provenance. They may extend governed catalogs and adapters without
forking Core, source architecture, database architecture or canonical
identity.

The following are prohibited:

- arbitrary runtime imports or unreviewed entry-point/directory discovery;
- customer-uploaded Python, JavaScript, WebAssembly or native code;
- executable descriptors, arbitrary scripts, shell commands or SQL;
- database-stored executable expressions;
- remote executable registries or runtime code download; and
- customer-supplied frontend bundles, components, import paths or scripts.

### 6. Project owns exact PackageVersion selection

`PackageVersion` has explicit immutable version identity. Registry-declared
compatibility, not version syntax alone, decides whether a version can be
selected or combined.

A Project pins each selected exact version. There is no implicit `latest`
selection or upgrade. Version change requires authorized preflight,
compatibility validation, explicit Human action, Audit and rollback evidence.

The Project is the sole package-version authority. A package-backed Workspace
inherits the applicable Project-selected key and exact version and cannot
independently select, pin, override or upgrade it. Workspace history may retain
derived effective provenance without becoming a second authority.

### 7. Project package configuration has explicit cardinality

A Project has one of two architecture states:

- **`NOT_CONFIGURED`:** zero selected packages and no compatibility profile;
  valid for a Project with zero Workspaces and for a Project containing only
  future-unavailable or unresolved Workspaces; or
- **`CONFIGURED`:** one or more compatible Organization-configured packages,
  each pinned to an exact version, with an applicable compatibility profile and
  selected-configuration provenance.

Project existence alone never fabricates package configuration. Configuration
may be established in advance, but becomes mandatory before creation of an
Electrical, Instrumentation or Control & Automation operational Workspace and
before execution of a package-owned operational capability.

### 8. Workspace package applicability has explicit states

Workspace identity remains one Project plus one governed Discipline under
ADR-014; no nested or multi-package Workspace is introduced. Package
applicability is represented by exactly one architecture state:

- **`OPERATIONAL_PACKAGE_BOUND`:** an E/I/C Workspace whose supported package
  is selected by its Project; key and exact version are inherited from the
  Project;
- **`FUTURE_UNAVAILABLE_UNBOUND`:** a recognized Discipline without an
  operational package, including current Mechanical, Civil and Process; no
  `PackageKey` is fabricated and no package-owned capability can execute; or
- **`LEGACY_UNRESOLVED`:** exact canonical mapping is impossible; raw identity
  remains historically readable under authorization, no package is fabricated
  and new package-dependent mutation fails closed pending Human resolution.

Future-unavailable Workspaces remain valid, Core-readable and
authorization-safe without pretending to be package-backed.

### 9. Configuration hierarchy and authority are separate

The effective package hierarchy is:

```text
trusted platform/deployment-supported package versions
-> Organization-configured packages
-> Project-selected exact package versions and compatibility profile
-> Workspace applicability and inherited binding
-> independently authorized package capability
```

Project configuration is optional until a package-dependent transition.
Package configuration is administrative product configuration. It is neither
engineering-data authorization nor commercial entitlement.

### 10. Authorization, configuration and entitlement are independent

Package-dependent operations compose separate ordered predicates for:

1. authentication and active Organization;
2. Project/Workspace/operation engineering-data authorization;
3. trusted deployment package support;
4. Organization package configuration;
5. exact Project package/version configuration and compatibility;
6. Workspace applicability or authorized Project-level applicability;
7. future commercial entitlement; and
8. authorization by the owner of every underlying engineering fact.

Authorization precedes package/configuration disclosure. Passing package or
entitlement predicates cannot grant engineering-data access. Package
configuration, versions, counts, failures and compatibility state are not
enumerable across tenants. Historical access to unbound or unresolved state is
authorized through its canonical owner rather than through a fabricated
package predicate.

### 11. Compatibility is explicit and fail-closed

Core performs deterministic compatibility evaluation over, where applicable:

- `CoreContractVersion` ranges;
- package-version support standing;
- declared dependencies and conflicts;
- supported pairwise and multi-package combinations;
- taxonomy and relationship-key collisions;
- read/write and migration prerequisites; and
- finite resource budgets.

Supported combinations are allow-listed and identified by a governed
compatibility profile. Unknown combinations fail closed. An integrated set is
not a new implicit super-package. Numeric ceilings and physical evaluation
mechanics remain EDS decisions.

### 12. Core and Package ownership remain bounded

Core owns:

- identity, version and provenance contracts;
- descriptor schema, registry assembly and validation;
- configuration resolution and compatibility evaluation;
- authorization composition and safe failure;
- closed integration ports and contribution categories;
- resource-bound enforcement and conformance framework;
- legacy classification/translation; and
- the future entitlement decision seam.

A Package may own bounded declarations and SATCO-reviewed implementations for:

- taxonomy, stable object types and relationship types;
- Context contributions, engineering inputs and deliverables;
- Evidence requirements and deterministic rule hooks;
- standards-applicability hooks and cross-discipline interfaces;
- references to Core-recognized role/authorization requirements;
- trusted frontend metadata and resource declarations;
- migration/read compatibility, entitlement key and conformance evidence.

Packages do not own or duplicate canonical Project, Workspace, Context,
Engineering Object, Relationship, Evidence, Technical Report, Organizational
Memory, Guidance, Audit or EKG authority. A declaration cannot extend RBAC or
bypass an owning capability.

### 13. Human authority remains the trust boundary

Packages and package outputs remain subordinate to existing explicit Human
workflows. A package cannot autonomously:

- approve professional engineering or design;
- accept or revise a Technical Report;
- admit, mutate or reinterpret Organizational Memory;
- approve Evidence standing;
- procure, purchase or select a vendor;
- create an authoritative BOM, MTO or BOQ;
- change Human decisions or Interface Commitment standing; or
- resolve engineering conflicts.

Advisory or derived output gains authority only through the existing owning
workflow's explicit Human operation.

### 14. Historical meaning is immutable

Adoption, upgrade, disablement or entitlement change must not rewrite or
reinterpret:

- accepted Technical Report snapshots, digests or exact legacy basis;
- Organizational Memory projections, manifests, source digests or meaning;
- historical Audit records or raw legacy identities; or
- other accepted engineering authority.

Authorized historical read/export and rollback readability are preserved even
when a version is no longer executable or a future Discipline remains unbound.
Migration reconciliation is additive, exact and attributable.

### 15. Entitlement attaches through a stable seam

Core exposes a stable entitlement-decision seam keyed by stable package
identity and `EntitlementKey`. This ADR and PATCH-051 do not implement signed
entitlement enforcement, seats, validity, grace, commercial activation,
billing or rollback-resistant verification.

PATCH-059 owns those decisions. Entitlement may restrict new commercial use,
but cannot grant engineering-data authorization, redefine Discipline/Package/
Project/Workspace identity, or erase authorized historical read/export.

### 16. Future PATCHes consume seams; they are not absorbed

This decision freezes only the shared seams required by:

- PATCH-052 for operational Electrical, Instrumentation and Control &
  Automation packages;
- PATCH-053 for authorized bounded cross-discipline interfaces;
- PATCH-054 for standards-applicability hooks;
- PATCH-055 for preserved Evidence ownership and package-declared
  requirements;
- PATCH-056 for Methods & Systems integration;
- PATCH-057 for truthful authorized commercial UX composition; and
- PATCH-059 for signed commercial entitlement decisions.

Those PATCHes retain their frozen capability ownership and must not be
implemented or pulled into ADR-024.

## Alternatives Considered

### Continue fragmented enums and free-text identities

Keep Workspace, EKG, Guidance, frontend and free-text terms independent and
translate them locally when needed.

### Hard-code Electrical, Instrumentation and Control directly into Core

Build three permanent Core branches with embedded taxonomy, rules, UI and
version behavior.

### Adopt a generic runtime plugin framework

Discover and execute packages dynamically from entry points, directories,
uploads or remote registries.

### Author dynamic package definitions in the database

Treat customer- or administrator-edited database descriptors, executable
expressions and frontend definitions as runtime package authority.

### Trusted source-controlled versioned package contract

Use Core-owned typed contracts, release-bound descriptors, explicit
SATCO-owned adapter registration, derived database projection, exact Project
pinning and bounded contributions.

## Rejected Alternatives

The first alternative is rejected because fragmented identity cannot provide
deterministic configuration, compatibility, provenance or safe migration and
would preserve current semantic ambiguity.

Hard-coded E/I/C Core branches are rejected because they fork shared behavior,
make future Disciplines require Core redesign and conflict with the open
extension and one-product decisions.

A generic runtime plugin framework is rejected because unreviewed execution,
dynamic imports and remote/customer code undermine release provenance,
conformance, resource bounds and tenant security.

Database-authored dynamic packages are rejected because the projection would
become competing authority and customer data could define executable or
security-sensitive behavior.

The trusted source-controlled versioned package contract is **selected**
because it provides governed extension, exact reproducibility and safe
configuration without Core or database forks.

## Consequences

### Positive

- Discipline meaning survives package availability, version and entitlement
  change.
- One Core contract supports E/I/C and later governed Disciplines.
- Exact Project pins and provenance make package-dependent behavior
  reproducible.
- Empty Projects and unavailable future Disciplines remain truthful.
- Static registration and conformance provide a reviewable security boundary.
- Canonical aggregates and accepted historical authority remain intact.
- PATCH-059 can attach without identity or authorization redesign.

### Costs and constraints

- Core must own additional identity, registry, configuration, compatibility,
  resource and conformance contracts.
- Releases must retain enough descriptor/provenance material for supported
  historical reads.
- Configuration and upgrade require explicit validation, impact analysis,
  Audit and Human action.
- Package combinations must be deliberately allow-listed and tested.
- Legacy compatibility requires additive transition and exact reconciliation.
- Future package authors are limited to closed contribution contracts and
  SATCO-reviewed adapters.

## Security Consequences

- Tenant scope remains server-derived; package configuration cannot supply an
  Organization authority.
- Authorization occurs before protected scope, package configuration, counts,
  versions, compatibility failures or underlying facts are disclosed.
- Package keys/versions and legacy identities are untrusted request data until
  parsed, bounded and resolved inside authorized scope.
- Package declarations cannot extend RBAC, access repositories/sessions of
  another owner, or infer hidden/truncated data as absent.
- Registry drift, unknown combinations, unresolved mapping and resource-limit
  violations fail closed.
- Static code registration, closed frontend contributions and the plugin ban
  reduce executable supply-chain and tenant-code risk.
- Package-configuration Audit requires an Organization-scoped persistence/read
  boundary; the current generic listing cannot be reused unchanged.

## Migration and Compatibility Consequences

Migration must follow a measured additive architecture:

```text
deployed-data preflight
-> trusted registry/configuration and canonical shadow state
-> exact controlled backfill
-> bounded compatibility contracts
-> validation
-> controlled cutover
-> separately governed legacy-write retirement
```

Only exact recognized E/I/C identities may receive canonical package binding,
and only through a compatible exact Project pin. Mechanical, Civil, Process
and other future-unavailable Disciplines remain explicitly unbound. Unknown
free text remains `legacy_unresolved`. No similarity matching, fabricated
package key or global replacement is permitted.

Existing API vocabularies may remain available through explicit boundary
translation during a governed compatibility period. Raw values and accepted
Report, Memory and Audit history remain unchanged. Pre-cutover rollback
preserves canonical shadow data; post-cutover downgrade requires explicit
registry/data compatibility preflight.

Exact migration batches, locks, transactions, constraints, dual-read/write
mechanics and retirement evidence belong to EDS/IDS and later authority.

## Human-Authority Consequences

Configuration, compatibility, package execution and future entitlement can
make a capability available; none can make its output accepted engineering
authority. Existing accountable Human review, Report acceptance, Evidence
standing, Memory admission, procurement and conflict-resolution boundaries
remain authoritative.

## Relationship to Existing Accepted ADRs

ADR-024 is additive and does not supersede an accepted ADR:

| Accepted ADR | Preserved relationship |
|---|---|
| ADR-010 — Universal Audit Integration | Audit remains a shared accountability boundary; package Audit must be minimized and correctly tenant-scoped. |
| ADR-012 — Alembic Schema Ownership and Historical Repair | Any later schema evolution remains migration-governed, additive and history-preserving. |
| ADR-014 — Engineering Workspace Domain Model | Preserves Project `0..N` Workspaces, at most one Workspace per Project/Discipline, no nesting, Workspace ownership and archival history. Package binding is applicability, not a new Workspace hierarchy. |
| ADR-015 — Engineering Context Domain Architecture | Context retains its owner and governed public boundary; packages contribute/consume only through typed ports. |
| ADR-016 — Dual-Use Platform Operating Model | Preserves one operator-neutral product, organizational isolation, no customer code forks and Human authority. |
| ADR-017 — Engineering Knowledge Graph Evolution | Engineering Object/EKG ownership remains canonical; packages declare bounded types and relationships without replacing the EKG. |
| ADR-017 — Modular Product Licensing Architecture | Preserves one product and no source/database forks. Package configuration is distinct from future commercial entitlement; the Commercial V1 reconciliation and PATCH-059 boundary remain intact. |
| ADR-020 — EKG Open Extension Principle | Formalizes governed package extension without Core forks or generic runtime plugins. |
| ADR-021 — Engineering Intelligence Core Business Capability | Packages are contributors/consumers, not parallel owners of knowledge, Evidence, provenance or Memory. |
| ADR-022 — Project Organization Ownership | Project configuration remains inside immutable server-derived Organization scope and cannot infer or grant tenant ownership. |
| ADR-023 — Human-Accepted AI-Assisted Technical Reports | Exact accepted Report versions, meaning and Human authority remain immutable across package change. |

Any conflict must stop downstream design for governed reconciliation; EDS may
not silently reinterpret an accepted ADR.

## Relationship to PATCH-051

PATCH-051 owns the shared Multi-Discipline Core and Discipline Package contract.
ADR-024 freezes its durable identity, registry, configuration, compatibility,
extension, authority and preservation decisions. It neither implements the
contract nor grants EDS-051 authority.

ADR-024 independent review and Human acceptance are complete. Architecture-051
remains eligible for Human Architecture Acceptance, which requires a separate
Human decision and is not granted by this ADR acceptance.

## Relationship to PATCH-052

PATCH-052 remains the exclusive later owner of operational Electrical,
Instrumentation and Control & Automation Discipline Packages V1. It must use
the same registry, configuration, inherited Project pin, conformance,
authorization and historical-preservation contract. ADR-024 supplies no
operational taxonomy, engineering rules, package adapter or implementation.

## Relationship to PATCH-059

PATCH-059 remains the exclusive later owner of signed commercial package
configuration/entitlement verification, seats, validity, grace, activation and
rollback-resistant enforcement. It attaches through `EntitlementKey` and the
Core decision seam without redefining identity or granting data access.

## Explicit Non-goals and EDS Boundary

This ADR does not decide or authorize:

- physical tables, columns, indexes, constraints or migration revisions;
- API routes, request/response shapes or transition mechanics;
- exact numeric resource limits;
- canonical serialization bytes, digest algorithms or test vectors beyond the
  distinct architectural identity roles;
- transaction, locking, batch, dual-read/write or rollback implementation;
- deployed-data census or Human resolution data;
- Audit schema, adapter or query implementation;
- conformance fixtures and exact test vectors;
- legacy API deprecation mechanics;
- frontend implementation or product experience;
- operational E/I/C package content;
- cross-discipline reasoning, standards intelligence, Evidence Workbench,
  Methods & Systems or Commercial UX behavior;
- commercial entitlement implementation; or
- EDS-051, IDS-051, implementation, migration or PATCH-052 authority.

EDS-051 must preserve these non-blocking obligations from Architecture review:

1. `A051-OBS-01`: distinguish executable/supported PackageVersions from
   historical-read-only versions; retained provenance is not execution
   authority.
2. `A051-OBS-02`: provide transactional Organization-scoped package-
   configuration Audit persistence/read behavior and do not reuse the current
   generic Audit listing unchanged.
3. `A051-OBS-03`: distinguish release-wide registry digest from selected
   package descriptor-set and compatibility-profile provenance.

## Supersession and Change Rule

ADR-024 does not supersede any accepted ADR. Changes to its separate typed
namespaces, registry authority, trusted extension model,
Project/Workspace package cardinality, Project-owned version authority,
configuration/authorization/entitlement separation, historical-preservation
or Human-authority boundaries require a new separately reviewed and Human-
accepted ADR that explicitly supersedes or amends this decision.

EDS, IDS, implementation, migration, customer configuration or a package
descriptor cannot change these durable decisions.

## Acceptance Gate

The ADR-024 acceptance gate is satisfied:

1. independent ADR review returned `PASS / ACCEPTED` with Critical/Major/Minor
   `0/0/0`;
2. no ADR amendment was required;
3. explicit Human ADR-024 Acceptance is `PASS / GRANTED`; and
4. no conflict with the accepted ADR chain or Human-frozen roadmap remains.

ADR-024 is therefore `Accepted`. The separate Human Architecture-051
Acceptance decision may now occur but is not performed by this operation.
EDS-051 requires separate authority after that governance chain.

## Exact Governance State

| Governance item | State |
|---|---|
| PATCH-050 | DONE / CLOSED |
| PATCH-051 | REGISTERED / OPEN |
| Architecture-051 focused re-review | PASS / ACCEPTED |
| `A051-MAJ-01` | RESOLVED / CLOSED |
| Architecture-051 | ELIGIBLE FOR HUMAN ARCHITECTURE ACCEPTANCE / ADR-024 DEPENDENCY SATISFIED / NOT YET HUMAN-ACCEPTED |
| ADR-024 independent review | PASS / ACCEPTED |
| ADR-024 | ACCEPTED |
| Human ADR-024 Acceptance | PASS / GRANTED |
| Human Architecture-051 Acceptance | NOT GRANTED |
| EDS-051 | NOT STARTED |
| IDS-051 | NOT STARTED |
| Implementation | NOT AUTHORIZED |
| Migration | NOT AUTHORIZED |
| PATCH-052 | NOT STARTED |
| Commercial V1 roadmap | HUMAN-FROZEN / UNCHANGED |

## Exact Next Resume Point

Separately authorized Human Architecture-051 Acceptance. Architecture-051 is
not Human-accepted through this operation. No EDS, IDS, implementation,
migration or PATCH-052 work begins through this accepted ADR record.

## Revision History

| Version | Date | Description |
|---|---|---|
| 0.1 | 2026-08-29 | Initial governed proposal prepared from Architecture-051 and its focused independent re-review. |
| 1.0 | 2026-08-29 | Accepted after independent ADR review PASS and explicit Human ADR-024 Acceptance PASS / GRANTED; Architecture-051 acceptance and EDS authority remain separate. |
