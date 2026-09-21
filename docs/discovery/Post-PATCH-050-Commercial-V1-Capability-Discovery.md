# Post-PATCH-050 Commercial V1 Capability Discovery

Date: 2026-08-28
Mode: Discovery / architecture / capability-gap analysis / roadmap synthesis
Human discovery authority: GRANTED
Implementation authority: NOT GRANTED
PATCH-051 registration: NOT GRANTED

## 1. Executive verdict

SATCO has a substantial governed engineering platform and is beyond demo-only
software. The accepted implementation reaches from Organization, Customer and
Project setup through discipline Workspaces, Capture, Evidence, execution,
deliverables, Project controls, Context, deterministic completeness and
Guidance, Human-accepted Technical Reports and Organizational Memory. It also
has a credible repository-side dedicated-deployment operating profile.

SATCO is not yet Commercial-V1 sellable under the Human-confirmed product
direction. The current core is architecture-ready for multiple disciplines but
does not yet have a shared Discipline Package contract or three commercially
operational packages. Cross-discipline intelligence, Methods & Systems /
Engineering Performance Intelligence, retrieval-backed standards awareness,
the complete Evidence workbench, commercial packaging, immutable release
automation and real customer-environment qualification remain incomplete.

The minimum coherent recommended roadmap contains **20 proposed PATCH
boundaries, PATCH-051 through PATCH-070**. These identifiers are proposals
only. The earlier Human-frozen post-PATCH-043 boundaries remain governance
history until a separate Human roadmap review accepts or rejects this
re-baseline.

## 2. Repository and governance baseline

- PATCH-050 is **DONE / CLOSED** under its append-only final closure record.
- Fresh8, QG-11, QG-12 and Closure are PASS / ACCEPTED / COMPLETE; delivery is
  GRANTED / ACCEPTED; final Critical/Major is `0/0`.
- Accepted PATCH-050 evidence is backend `540/540`, frontend `88/88` across 19
  files, typecheck/build/static PASS, sole Alembic head `e04700000001`, and no
  PATCH-050 migration.
- The working tree is cumulative and dirty/untracked. The committed HEAD is
  `ae40f5d` (`PATCH-049: record delivery closure`), while the accepted PATCH-050
  implementation and records are present in the working tree. This is not a
  PATCH-050 closure defect, but a clean immutable release must reconcile it
  before Commercial V1 certification.
- The old Roadmap registry text lags later standalone PATCH records. Standalone
  PATCH-044 through PATCH-050 records and their accepted append-only
  chronologies are the current capability evidence.
- No production code, tests, migration, closed PATCH record, Roadmap or
  governance registry is modified by this discovery.

## 3. Capability classification

### Implemented

- authenticated Organization context, two application roles, onboarding,
  activation/reset and member administration;
- Organization-owned Customer, Project and discipline Workspace lifecycle;
- Project Foundation, scope, required inputs and engineering stage;
- Engineering Execution Plan, activities, milestones, dependencies, blockers
  and derived progress;
- Deliverable Register with external-tool authority and immutable revisions;
- Project Risks, Issues, Human Decisions, Changes and bounded Change Impacts;
- Universal Capture, Engineering Journal and optional advisory Capture AI;
- metadata Evidence Aggregate and Supporting File upload, quarantine, scanning,
  immutable private storage, linkage, current/historical download and Audit;
- Technical Report draft/revision, exact Human acceptance, lineage and frozen
  provenance;
- Human-admitted Organizational Memory with governed reuse;
- Engineering Object and Relationship primitives, Context relationships and
  Interface Commitments;
- Project Context assembly and bounded authorized one-hop contextual reads;
- deterministic Project Completeness and Engineering Guidance, including
  preliminary Candidate Material Requirements and optional bounded AI
  explanation;
- basic Command Center and contextual Project frontend surfaces;
- production Compose topology, reverse proxy/TLS policy, secret-file
  configuration, migration preflight, health/readiness/metrics, backup,
  restore-verification, upgrade/rollback controls, support bundle and runbooks.

### Partial

- multi-discipline behavior: Workspace labels and three Engineering Object
  families exist, but there is no package contract or operational package
  completeness;
- frontend discipline creation: Electrical and Instrumentation are offered,
  but Control is omitted while unimplemented Mechanical/Civil/Process choices
  are exposed;
- cross-discipline coordination: cross-Workspace relationships and Interface
  Commitments exist, but no package-aware interface model, consistency rules,
  conflict analysis or coordinated product view exists;
- Engineering Knowledge Graph: strong typed nodes/relationships and PATCH-048
  one-hop composition exist, but no general package-aware engineering read
  model or cross-discipline intelligence layer exists;
- Methods & Systems: execution, deliverable, control and completeness facts can
  feed indicators, but the current dashboard metrics are simple counts and
  recency, not Engineering Performance Intelligence;
- standards: Technical Report provenance can manually record identity,
  publisher, edition and clause/location, but SATCO cannot validate or retrieve
  them from a governed registry;
- Evidence experience: file intake/link/download is visible, but ordinary users
  cannot create and govern the full Evidence lifecycle from the same workbench;
  retention/legal-hold/purge policy administration is absent;
- operational readiness: repository contracts are credible, but real DNS/TLS,
  object storage, scanner, off-host recovery, external alerting and support
  rehearsal are not proven here;
- authentication/release security: security headers, edge rate limiting,
  password hashing, short access tokens and auth-version invalidation exist,
  but refresh rotation/session administration, MFA, dedicated auth throttling,
  CI release automation and continuous vulnerability evidence are absent;
- commercial packaging: ADR-016/017 define one product and Organization-scoped
  modularity, but package configuration and entitlement enforcement do not
  exist.

### Architecture-ready

- future discipline extension through stable Project/Workspace/Context,
  Engineering Intelligence ports, Object/Relationship semantics and EKG open
  extension principles;
- standards-aware Reports through existing standard provenance locators and
  immutable accepted snapshots;
- Engineering Performance trends through append-only activity, deliverable,
  Project-control, Context commitment and Audit histories;
- technical procurement through Candidate Material Requirements, Deliverables,
  Evidence and Human authority boundaries;
- FAT/SAT/commissioning through Execution, Deliverables, Evidence and Human
  acceptance primitives.

### Missing for Commercial V1

- a canonical shared Discipline Package architecture and package registry;
- real Electrical, Instrumentation and Control & Automation packages;
- package-aware cross-discipline interfaces, conflicts, impact and Guidance;
- discipline-neutral Methods & Systems / Engineering Performance Intelligence;
- standards registry, applicability, rights, retrieval and citation
  verification;
- standards-aware Technical Report enrichment and Memory reuse;
- complete Evidence authoring/review/lifecycle/retention experience;
- the remaining Human-frozen technical procurement and project-completion
  capabilities, bounded to engineering rather than ERP;
- final cross-product workflow/Command Center composition;
- secure commercial package configuration/entitlements;
- clean, immutable CI-built release evidence and representative deployment
  qualification.

## 4. Core architecture and multi-discipline assessment

The core can evolve to Multi-Discipline without replacing Project, Workspace,
Context, Evidence, Report, Memory, Audit or Human-authority foundations.
However, it cannot do so by adding more enum values. Today discipline meaning
is split across `Discipline.CONTROL`,
`EngineeringDiscipline.INDUSTRIAL_AUTOMATION`,
`EngineeringObjectFamily.AUTOMATION` and
`MaterialCategory.AUTOMATION_AND_CONTROL`. Workspace and Engineering Object
tables also embed closed enum-derived check constraints. Each added discipline
therefore requires core edits and migrations, which is not a modular package
architecture.

The required correction is an additive shared package kernel:

1. one stable `DisciplineId`/slug and display contract;
2. a code-owned, versioned, collision-checked `DisciplinePackageDescriptor`;
3. a startup registry of trusted built-in packages, not arbitrary runtime code
   upload;
4. Organization/project package configuration separate from commercial
   entitlement enforcement;
5. package-owned taxonomies, templates, rules and UI contribution descriptors;
6. shared owner ports for Context, Evidence, Reports, Memory, execution and
   cross-discipline reads;
7. package-version compatibility and migration rules;
8. stable package identities carried in Audit, evidence and accepted outputs;
9. deny-by-default authorization and disclosure behavior shared by every
   package;
10. contract and conformance suites that any future package must pass.

Existing records must map losslessly to the new stable discipline identities.
Disabling a package must never orphan, erase or silently hide historical
accepted engineering records; it may block new mutations while retaining
authorized read/export and audit access.

## 5. Discipline Package contract

Every package must declare and obey:

- package ID, semantic version, discipline ID, compatible core contract and
  dependency set;
- governed object types, identifiers, lifecycle/authority meanings and
  relationship vocabulary;
- Context subjects/sources, required-input templates, deliverable templates,
  Evidence expectations and report intents;
- deterministic completeness, validation and Guidance rules with versioned
  catalogs and safe evidence projections;
- cross-discipline interface types it provides, consumes and validates;
- standards-applicability hooks that return registry IDs, never invented text;
- explicit Human responsibility and review operations;
- operation-level roles, Project/Workspace scope, confidentiality and protected
  result behavior;
- resource limits, pagination, deterministic ordering, Audit, idempotency and
  concurrency requirements;
- frontend navigation/panel descriptors using shared states and accessibility
  rules;
- package migration, upgrade, rollback and backward-read compatibility;
- entitlement/configuration keys without embedding billing logic;
- unit, contract, isolation, negative-disclosure, performance, frontend and
  cross-package conformance tests.

Packages contribute governed domain behavior; they do not own parallel
Projects, Evidence, Reports, Memory, identity, tenancy, Audit or AI gateways.

## 6. Commercial V1 discipline boundaries

### Electrical

V1 covers motors, transformers, MCCs, switchgear, panels, electrical cables,
feeders/power sources, protection/isolating/earthing/UPS relationships,
electrical required-input and deliverable templates, deterministic
completeness/consistency checks and evidence-linked advisory Guidance. It must
support power/control interfaces to Instrumentation and Control. It does not
generate ETAP/EPLAN/CAD studies, settings, drawings, cable sizes or approved
designs.

### Instrumentation

V1 covers instruments, transmitters, analyzers, flowmeters, control valves,
loops, junction boxes and instrument panels; measurement, signal, calibration,
actuation and I/O relationships; loop/instrument deliverables; required-input
and evidence templates; deterministic completeness and consistency checks; and
advisory Guidance. It does not automatically select instruments, calculate
final sizing or produce approved datasheets/loop drawings.

### Control & Automation

V1 covers PLC/DCS/ESD controllers, control cabinets, I/O channels, HMI and
control-logic references; signal, command, alarm, trip, interlock, sequence and
implementation relationships; I/O, cause/effect and control-document
deliverable control; deterministic checks and advisory Guidance. It does not
generate PLC/DCS/SIS/ESD/HMI/SCADA code, safety logic, vendor configuration or
approved control narratives.

## 7. Cross-discipline intelligence boundary

V1 must provide a Human-governed interface contract joining canonical facts,
not a new universal engineering aggregate. Minimum interfaces are:

- Electrical -> Control: normal/emergency/UPS/control power, feeder/MCC status,
  start permissives and electrical trip/status signals;
- Instrumentation -> Control: tag/loop, measured variable, range/unit, signal
  type, I/O allocation, fail state, alarm/trip and valve command/feedback;
- Control -> Electrical: motor commands, run/available/fault feedback,
  interlocks, trips, ESD actions and restart constraints;
- Instrumentation -> Electrical: instrument/panel power, cable/segregation,
  earthing/shielding and hazardous-area evidence references where applicable;
- three-way: shared Project/system/equipment identity, cause-and-effect intent,
  interface responsibility, revision/applicability and evidence basis.

Mandatory outputs are missing-interface findings, inconsistent values,
unfulfilled Interface Commitments, dependency/change impact, cross-discipline
completeness and evidence-linked Guidance. The engine must distinguish absent,
protected, stale, disputed and genuinely conflicting information. It may
recommend review but cannot resolve a conflict, accept an interface or mutate a
discipline record.

Future Process, Piping, Mechanical, Civil/Structural and HSE/Process Safety
packages use the same contract. No V1 placeholder may pretend those disciplines
are implemented.

## 8. Methods & Systems / Engineering Performance Intelligence

The V1 layer is discipline-neutral and limited to engineering departments and
the engineering lifecycle. It consumes canonical events and read projections;
it does not own or rewrite execution, deliverable, control, report or Human
decision state.

Minimum indicators are required-input readiness/aging, blocked-work aging,
milestone predictability, deliverable review/issue cycle time, rework/revision
trend, risk/issue/change aging, Interface Commitment response/fulfilment,
completeness trend, report acceptance flow and Evidence availability. Every
indicator must expose numerator, denominator, time window, source cutoff,
scope, exclusions, missing-data limitations and drill-down to authorized facts.

Trend snapshots may be persisted as derived, reproducible analytical
projections with source-watermark/digest and recalculation semantics. They are
not engineering approval or employee performance ratings. Individual
surveillance, forced productivity scores, HR ranking, finance, payroll,
portfolio accounting and enterprise ERP/BPM remain excluded.

## 9. Standards-aware Technical Report architecture

### Registry and reference layer

The required registry stores standard identity, title, issuing body, edition,
publication/effective/withdrawal dates, supersession, jurisdiction, discipline
tags, applicability metadata, official source, content-availability class and
Organization rights/license reference. Applicability is a governed Human or
deterministic advisory assertion; it is not inferred authority.

The retrieval gateway accesses only public metadata, legally permitted
material or Organization-licensed content. Retrieved fragments are immutable
snapshots with source, edition, clause/location, retrieval time, digest and
rights basis. Wholesale copyrighted standards are not stored or embedded
unless explicitly licensed.

AI receives only registry-selected, retrieval-backed candidates. It may select
or explain known candidate handles; it cannot supply free-text identities,
editions or clause numbers. The application validates every returned handle
against the exact retrieval set and fails closed on mismatch.

### Report and Memory enrichment

The existing Human-authored Report remains canonical. Enrichment creates an
advisory, versioned suggestion set containing relevance rationale, exact
citation, applicability/rights status, evidence and limitations. A Human may
accept selected references into a new draft revision before exact Report
acceptance. The immutable accepted Report snapshot freezes citation identity
and permitted minimal representation.

Organizational Memory reuses the accepted Report and its standards provenance;
it does not copy or silently broaden licensed content. Current display/retrieval
must reauthorize Organization rights while preserving the historical citation
even if an edition is later superseded or access rights change.

## 10. Supporting-file Evidence assessment

The security-sensitive file pipeline is implemented and strong for its bounded
scope: private object storage, opaque keys, size/media/digest validation,
quarantine, fail-closed scanning, immutable bytes, scoped list/download,
withdrawal, Evidence linkage, accepted-Report historical basis, Audit and
recovery inventory.

Commercial V1 still needs one coherent ordinary-user Evidence workbench:
create proposed Evidence, select/link current safe files, review provenance,
transition Evidence standing, supersede/withdraw, inspect lineage and Report
reliance, and understand protected/unavailable states without raw IDs. It also
needs Organization retention classes, minimum-retention/legal-hold rules,
terminal purge eligibility, auditable disposal and customer export/closure
behavior. Physical deletion must never invalidate an accepted historical basis
without an explicit legal/governance policy.

Real object-store/scanner credentials, capacity, malware test corpus, outage
behavior and recovery restoration must be qualified in the representative
deployment gate.

## 11. Production, recovery, monitoring and support assessment

Repository-side readiness is **implemented but not externally qualified**.
Production Compose includes a TLS edge, isolated private network, read-only
containers, dropped capabilities, secret files, schema/runtime role separation,
release manifest validation and migration gating. Backup encrypts the database
and object inventory; restore verifies both against an isolated database.
Upgrade, compatible rollback/recovery, signed operations mode, monitoring,
diagnostics, support bundle and runbooks exist.

Commercial proof still requires one clean immutable build and a representative
customer-like environment with real DNS/TLS, object store/scanner, off-host
encrypted backup, isolated restore and promotion rehearsal, upgrade/rollback,
external alert delivery, storage/capacity tests, support/break-glass exercise,
RPO/RTO evidence and operator/user documentation. Repository scripts are not
substitutes for performed evidence.

## 12. Security and release-readiness assessment

Current strengths include server-derived Organization scope, authorization
before disclosure in modern verticals, protected-not-found behavior, Audit,
idempotency/concurrency, immutable histories, password hashing, auth-version
invalidation, TLS/security headers, edge rate limiting, non-root/read-only
containers and release-manifest/SBOM/scan evidence fields.

Remaining V1 work is to reconcile any exposed legacy Contact/search paths,
define dedicated login/credential throttling and lockout policy, implement
refresh rotation/session revocation or deliberately remove the unused refresh
token contract, add administrator MFA/recovery policy, review browser token and
CSRF/XSS threat boundaries, automate dependency/container/SAST/secret scanning,
create CI quality/release gates, sign immutable artifacts and run an independent
release threat/penetration review. Enterprise SSO/SCIM remains post-V1 unless a
first customer contract requires it.

## 13. Commercial packaging

One shared Core is mandatory. An Organization may enable the integrated
Electrical + Instrumentation + Control & Automation configuration or one or
more individual implemented packages. Core identity, Project, Evidence,
Reports, Memory, Audit and Human authority never vary by package.

Package configuration is an architectural prerequisite in PATCH-051;
commercial entitlement/seat/term enforcement belongs near the end, after the
package set stabilizes. Expiry must fail closed for new optional-module
mutations without erasing historical read/export access. Billing, invoicing and
advanced commercial analytics remain outside V1.

## 14. Explicit post-V1 deferrals

- operational Process, Piping, Mechanical, Civil/Structural, HSE/Process Safety
  and other Discipline Packages;
- deep PLC/DCS/SIS/ESD/HMI/SCADA or vendor-specific generation;
- autonomous engineering, approval, procurement award or workflow loops;
- advanced procurement optimization, accounting, ERP, payroll and broad CRM;
- generic EDMS, CAD/EPLAN replacement, Digital Twin and unrestricted graph or
  semantic/vector search;
- investor-engineer marketplace, cross-Organization knowledge sharing and
  customer-specific source forks;
- SaaS billing, advanced licensing analytics, enterprise SSO/SCIM, multi-region
  HA/Kubernetes and customer-managed deployment variants;
- broad proposal/contract automation, website/n8n automation and nonessential
  notifications unless separately restored to the Commercial V1 boundary by
  Human roadmap decision.

## 15. Dependency graph

```text
Accepted core through PATCH-050
  -> 051 Shared Multi-Discipline Core
       -> 052 Electrical Package
       -> 053 Instrumentation Package
       -> 054 Control & Automation Package
            -> 055 Cross-Discipline Intelligence
                 -> 059 Engineering Performance Intelligence
                 -> 064 Explainable Engineering Health
                 -> 065 FAT/SAT/Commissioning

Accepted Evidence/Report core -> 056 Evidence Workbench
051 + discipline packages -> 057 Standards Registry -> 058 Report/Memory Enrichment

050 + 051 -> 060 Vendor Registry -> 061 Requisitions -> 062 RFQ/Evaluation
  -> 063 Award/Order/Supply -> 064 Health and 066 Closeout

055 + 056 + 063 + 065 -> 066 Handover/Closeout
058 + 059 + 064 + 066 -> 067 Guided Lifecycle/Command Center
051..067 -> 068 Security/CI/Release Foundation -> 069 Packaging/Entitlements
  -> 070 Representative Deployment Qualification -> Commercial V1 Exit Gate
```

Security requirements apply continuously; PATCH-068 is the final integrated
hardening and release-evidence boundary, not permission to defer secure design
in earlier PATCHes.

## 16. Proposed roadmap — 20 remaining PATCHes

### PATCH-051 — Shared Multi-Discipline Core & Discipline Package Contract

- Purpose/boundary: normalize discipline identity and establish trusted,
  versioned package registration/configuration without implementing a package.
- Backend: descriptors/registry, compatibility, core ports, package config,
  legacy mapping, Audit and conformance harness.
- Frontend: package-aware navigation/workspace creation and truthful disabled/
  unavailable states.
- Persistence: migration expected for stable discipline/package identities and
  lossless existing-data mapping.
- Security: package enablement cannot grant Project/Workspace visibility;
  historical access survives disablement.
- Dependencies: PATCH-050 and accepted ADR-016/017/020/021.
- Exclusions: discipline rules, licensing enforcement, arbitrary plugins.
- Exit: one canonical vocabulary; built-in empty test package passes all
  contracts; no hard-coded future-discipline UI claims.

### PATCH-052 — Electrical Discipline Package V1

- Purpose/boundary: real Electrical workspace objects, templates, rules,
  evidence and Guidance within the shared package contract.
- Backend/frontend: Electrical taxonomy, relationships, inputs, deliverables,
  deterministic checks and dedicated workspace experience.
- Persistence: package-owned reference/config tables or migration likely; no
  duplicate Core facts.
- Security: Electrical scope/role matrix and protected evidence.
- Dependencies: 051.
- Exclusions: ETAP/EPLAN/CAD generation and final calculations/settings.
- Exit: representative electrical project completes package workflows using
  real data and traceable Human authority.

### PATCH-053 — Instrumentation Discipline Package V1

- Purpose/boundary: real Instrumentation package for instruments, loops,
  signals, valves, evidence, deliverables and checks.
- Backend/frontend: package taxonomy/rules and an operational Instrumentation
  workspace.
- Persistence: likely package reference/config migration.
- Security: discipline/workspace isolation and protected source handling.
- Dependencies: 051.
- Exclusions: final sizing/selection and automatic datasheet/loop generation.
- Exit: representative instrumentation workflow and package conformance pass.

### PATCH-054 — Control & Automation Discipline Package V1

- Purpose/boundary: real PLC/DCS/ESD/HMI/I/O/control-logic reference package.
- Backend/frontend: Automation taxonomy, signal/interlock/alarm/sequence
  relationships, controlled deliverables, checks and workspace UX.
- Persistence: likely package reference/config migration.
- Security: provider/tool payload minimization and discipline isolation.
- Dependencies: 051.
- Exclusions: code, safety-logic, HMI/SCADA and vendor-project generation.
- Exit: representative control project passes real operational workflow and
  conformance evidence.

### PATCH-055 — Cross-Discipline Interfaces, Consistency & Guidance

- Purpose/boundary: typed interfaces and advisory intelligence across the three
  packages without transferring source authority.
- Backend: interface schema/commitment extensions, cross-package rule catalogs,
  conflict/completeness/impact/Guidance composition.
- Frontend: interface matrix, missing/conflict views, evidence drill-down and
  Human review/disposition links.
- Persistence: migration expected for versioned interface records; findings may
  remain derived unless Human disposition is recorded canonically.
- Security: visibility intersection of every constituent source; no graph-shape
  leakage.
- Dependencies: 052–054 and existing Context/Relationship/Commitment core.
- Exclusions: autonomous resolution and multi-hop unbounded inference.
- Exit: required E/I/C interfaces detect seeded omissions/conflicts with exact
  evidence, limitations and no unauthorized disclosure.

### PATCH-056 — Commercial Evidence Workbench, Retention & Lifecycle

- Purpose/boundary: complete the Human Evidence experience and governed
  retention/disposal policy around existing file foundations.
- Backend/frontend: Evidence creation/review/transitions/lineage/reliance,
  retention/legal hold/purge eligibility and coherent workbench UX.
- Persistence: migration expected for retention/hold/disposition metadata.
- Security: fail-closed scan/storage, protected lifecycle, auditable disposal.
- Dependencies: PATCH-027/032/040/043.
- Exclusions: OCR, semantic extraction, generic EDMS and document collaboration.
- Exit: upload-to-accepted-Report-to-Memory and retained/historical recovery are
  usable end to end with policy tests.

### PATCH-057 — Standards Registry, Applicability, Rights & Retrieval

- Purpose/boundary: canonical standards metadata, editions, applicability,
  rights and retrieval-backed citation candidates.
- Backend: registry, edition/supersession, rights policy, connector gateway,
  immutable retrieval snapshots and citation validator.
- Frontend: standards administration/search/applicability/rights visibility.
- Persistence: new registry, edition, rights, applicability and retrieval
  metadata migrations expected.
- Security: Organization rights isolation; licensed content never crosses scope
  or provider boundaries.
- Dependencies: 051–054, Evidence and Context.
- Exclusions: wholesale copyrighted content, AI-invented clauses and generic
  vector search.
- Exit: known standards/editions/clauses resolve only through authorized,
  digest-backed references; withdrawn/superseded/rights-denied cases fail safe.

### PATCH-058 — Standards-Aware Technical Report & Memory Enrichment

- Purpose/boundary: advisory standards association and citations in Report
  drafting while preserving exact Human acceptance and Memory authority.
- Backend/frontend: bounded enrichment request, validated handles, Human
  selection, citation presentation, accepted snapshot and Memory reuse.
- Persistence: Report provenance/suggestion and accepted citation migration
  likely; no provider conversation store.
- Security: retrieval-set binding, content minimization, durable metadata Audit.
- Dependencies: 057, Technical Reports and Organizational Memory.
- Exclusions: automatic compliance declaration or acceptance.
- Exit: no unknown identity/edition/clause can enter an accepted Report;
  historical and current-rights behaviors are proven.

### PATCH-059 — Methods & Systems / Engineering Performance Intelligence

- Purpose/boundary: discipline-neutral, explainable engineering-unit process
  and KPI intelligence.
- Backend: indicator contracts, source adapters, time windows, data-quality
  limits, derived snapshots/trends and drill-down.
- Frontend: engineering performance dashboard by Project/discipline/time with
  factor and limitation disclosure.
- Persistence: derived analytical snapshots/watermarks migration expected.
- Security: minimum cohort/scope controls; prohibit hidden-data inference and
  individual surveillance/ranking.
- Dependencies: 055 plus execution/deliverable/control histories.
- Exclusions: ERP, HR appraisal, finance, payroll and enterprise BI.
- Exit: approved KPI catalog reproduces exact results and authorized drill-down
  from canonical source facts.

### PATCH-060 — Vendor & Panel Builder Registry

- Purpose/boundary: Organization-owned technical vendor identity,
  capabilities, qualification evidence and Project shortlist.
- Backend/frontend: canonical vendor aggregate, contacts/capabilities/status,
  Evidence and shortlist UX.
- Persistence: migration expected.
- Security: tenant isolation; qualification is Human-owned and evidence-based.
- Dependencies: 051 and Customer/Project/Evidence core.
- Exclusions: CRM, financial supplier management and autonomous selection.
- Exit: reusable qualified vendor/panel-builder records and protected Project
  shortlists work end to end.

### PATCH-061 — Material/Equipment Requirements & Procurement Requisitions

- Purpose/boundary: convert Human-adopted engineering need, not raw Guidance,
  into a governed technical requisition.
- Backend/frontend: requirements, line groups, revisions, source traceability,
  approvals and requisition workbench.
- Persistence: migration expected.
- Security: Human adoption/approval and separation from Guidance authority.
- Dependencies: 050, 052–054, 060, Deliverables/Evidence.
- Exclusions: PO/accounting, inventory and automatic BOM/quantity authority.
- Exit: every line traces to accepted Human requirements/evidence and remains
  distinct from preliminary Candidate Material Requirements.

### PATCH-062 — RFQ, Quotation & Technical Proposal Evaluation

- Purpose/boundary: bounded RFQ, vendor response, deviation and Human technical
  comparison.
- Backend/frontend: RFQ versions, response intake, compliance/deviation matrix,
  Evidence and Human recommendation UX.
- Persistence: migration expected.
- Security: vendor submissions isolated; no cross-vendor disclosure; Audit.
- Dependencies: 061 and revalidated EDS-030 direction.
- Exclusions: autonomous winner/award, contract and commercial accounting.
- Exit: multi-vendor technical evaluation is reproducible, evidence-linked and
  Human-authorized.

### PATCH-063 — Award Reference, Order & Supply Impact Tracking

- Purpose/boundary: Human award reference, ordered technical scope,
  promised/actual delivery and engineering impact.
- Backend/frontend: order/supply milestones, deviations, delay links and Project
  impact views.
- Persistence: migration expected.
- Security: protected commercial fields and explicit Human award authority.
- Dependencies: 062 and Project controls/execution.
- Exclusions: ERP purchasing, invoicing, payment and inventory.
- Exit: supply status affects engineering visibility through governed links,
  never silent source mutation.

### PATCH-064 — Explainable Engineering Health & Next Actions

- Purpose/boundary: cross-domain Project/discipline health and advisory next
  actions from canonical facts.
- Backend/frontend: factor model, time/limits/confidence, deterministic
  aggregation, drill-down and Command Center summaries.
- Persistence: derived snapshots optional/likely; no approval score.
- Security: factor visibility intersection and no inference from hidden counts.
- Dependencies: 055, 059 and 061–063.
- Exclusions: single opaque score, Project approval and autonomous task creation.
- Exit: every health state is factor-explainable, reproducible and
  authorization-safe.

### PATCH-065 — FAT/SAT/Commissioning & Punch Evidence

- Purpose/boundary: Human-controlled test/checklist/witness/finding/punch
  workflow across the three packages.
- Backend/frontend: plans, test items, revisions, outcomes, Evidence, witness
  identity, punch lifecycle and package templates.
- Persistence: migration expected.
- Security: Human witness/acceptance and immutable evidence; no fake results.
- Dependencies: 052–056, execution, deliverables and Project controls.
- Exclusions: automated plant control, test approval and vendor code generation.
- Exit: representative FAT and SAT scenarios preserve exact evidence, failed
  items and Human acceptance.

### PATCH-066 — Engineering Handover & Project Closeout

- Purpose/boundary: governed completion basis, handover package, unresolved-item
  disclosure, lessons and Human closeout.
- Backend/frontend: closeout readiness, package manifest, exceptions, accepted
  records and Memory handoff.
- Persistence: migration expected.
- Security: no closure from protected/indeterminate prerequisites.
- Dependencies: 056, 063, 065 and Project Foundation/Deliverables/Memory.
- Exclusions: contractual/legal acceptance and generic archive/EDMS.
- Exit: closeout cannot pass with unresolved mandatory governed prerequisites;
  exact Human authority and package are preserved.

### PATCH-067 — Guided Engineering Lifecycle & Commercial Command Center

- Purpose/boundary: orchestrate stable canonical workflows and compose the
  sellable product experience without owning duplicate domain state.
- Backend/frontend: bounded next-action projection, permission-aware navigation,
  integrated dashboards, empty/error/protected states, accessibility and
  responsive polish.
- Persistence: user presentation preferences only; no workflow truth store.
- Security: every card/action reauthorizes through its owner.
- Dependencies: 058, 059, 064–066.
- Exclusions: generic BPM/tasks, fake totals and autonomous action.
- Exit: representative integrated and single-discipline users complete core
  journeys without raw IDs or hidden backend-only steps.

### PATCH-068 — Commercial Application Security, CI & Release Foundation

- Purpose/boundary: integrated application threat hardening and immutable,
  automated release evidence.
- Backend/frontend/ops: session/refresh decision, MFA/admin recovery, auth
  throttling, legacy-surface reconciliation, CI tests/scans/SBOM/signing and
  release certification dossier generation.
- Persistence: session/MFA/recovery migration likely.
- Security: primary boundary; independent threat and penetration review.
- Dependencies: stable application through 067, while controls apply earlier.
- Exclusions: enterprise federation and multi-region infrastructure.
- Exit: clean source builds one traceable signed candidate; all security gates
  pass with no unresolved Critical/Major.

### PATCH-069 — Commercial Packaging, Discipline Configuration & Entitlements

- Purpose/boundary: sell integrated or discipline-specific configurations from
  one codebase/deployment.
- Backend/frontend: Organization package enablement, seats/term/grace/support
  entitlement, API/navigation enforcement and admin UX.
- Persistence: entitlement/license migration expected.
- Security: signed/server-managed license, anti-rollback, fail-closed mutation,
  historical read/export preservation.
- Dependencies: stable packages and 068 release identity.
- Exclusions: billing, invoicing and customer-specific builds.
- Exit: integrated and single-package license matrices pass API/UI/upgrade/
  expiry tests without source or database forks.

### PATCH-070 — Representative Customer Deployment Qualification

- Purpose/boundary: perform, record and independently review real operational
  evidence for one supported customer-like deployment.
- Backend/frontend/ops: no new product domain; environment manifests, DNS/TLS,
  storage/scanner, backup/restore, upgrade/rollback, monitoring, support,
  capacity, security and first-customer rehearsal.
- Persistence: no product migration expected; operational evidence only.
- Security: production secrets, break-glass, alerting and incident exercises.
- Dependencies: 068–069 and every frozen V1 capability.
- Exclusions: Kubernetes, HA/multi-region and unsupported deployment variants.
- Exit: signed release is reproducibly deployed/recovered/upgraded and supported
  within accepted RPO/RTO/SLO using real external dependencies.

## 17. Complexity, risk and commercial importance

| PATCH | Complexity | Architecture risk | Commercial importance |
|---|---|---|---|
| 051 | VERY HIGH | HIGH | CRITICAL |
| 052 | HIGH | MEDIUM | CRITICAL |
| 053 | HIGH | MEDIUM | CRITICAL |
| 054 | VERY HIGH | HIGH | CRITICAL |
| 055 | VERY HIGH | HIGH | CRITICAL |
| 056 | HIGH | MEDIUM | CRITICAL |
| 057 | VERY HIGH | HIGH | CRITICAL |
| 058 | VERY HIGH | HIGH | CRITICAL |
| 059 | VERY HIGH | HIGH | CRITICAL |
| 060 | HIGH | MEDIUM | IMPORTANT |
| 061 | HIGH | MEDIUM | CRITICAL |
| 062 | VERY HIGH | HIGH | CRITICAL |
| 063 | HIGH | MEDIUM | IMPORTANT |
| 064 | VERY HIGH | HIGH | CRITICAL |
| 065 | VERY HIGH | HIGH | CRITICAL |
| 066 | HIGH | MEDIUM | IMPORTANT |
| 067 | VERY HIGH | MEDIUM | CRITICAL |
| 068 | HIGH | HIGH | CRITICAL |
| 069 | HIGH | HIGH | CRITICAL |
| 070 | HIGH | HIGH | CRITICAL |

The critical path is `051 -> 052/053/054 -> 055 -> 059 -> 064`, with the
parallel `057 -> 058`, `060 -> 061 -> 062 -> 063`, and `056 -> 065 -> 066`
lanes joining at `067 -> 068 -> 069 -> 070`.

## 18. Commercial V1 sellable exit gate

Commercial V1 is **SELLABLE** only when all of the following are evidenced:

1. all frozen V1 PATCHes are DONE/CLOSED with no unresolved Critical/Major;
2. one shared Core runs the integrated and each allowed single-discipline
   configuration without forks;
3. Electrical, Instrumentation and Control & Automation each pass their package
   conformance and representative project scenarios;
4. cross-discipline interface, conflict, impact and completeness scenarios pass
   with protected-data negative evidence;
5. AI-off deterministic behavior and AI-on bounded/refusal/invention tests pass;
6. Human authority is explicit for Reports, standards selection, Evidence,
   procurement, tests and closeout;
7. unknown, wrong-edition or invented standards/clauses cannot enter accepted
   Reports; rights and copyright boundaries pass;
8. the Evidence workflow passes upload, quarantine, malware, outage, linkage,
   retention, historical retrieval and recovery tests;
9. security review, tenant/isolation matrix, auth/session/MFA policy,
   vulnerability scans and independent penetration evidence pass;
10. one clean revision produces signed immutable backend/frontend/migration
    artifacts, SBOM and complete release manifest through CI;
11. sole Alembic head, fresh install, upgrade, compatible rollback/recovery and
    migration role separation pass;
12. real DNS/TLS, object store/scanner, backup/restore, RPO/RTO, monitoring,
    alerting, support, break-glass and incident exercises pass;
13. integrated and single-discipline onboarding journeys pass with real data,
    accessible/responsive UI and no raw-ID-only step;
14. administrator, operator, support and user documentation are versioned and
    tested against the release;
15. commercial package/seat/term/expiry matrices pass without historical data
    loss or unauthorized module access;
16. capacity/SLO targets are measured for the supported deployment profile;
17. deferred functionality is absent or visibly unavailable, never represented
    by placeholders/fake data;
18. independent final Commercial V1 review, Human quality gates and explicit
    release certification are PASS / ACCEPTED / COMPLETE.

Until those criteria pass, SATCO may be pilot-capable but is not certified
sellable. The largest present sellable-vs-pilot gaps are real Discipline
Packages, cross-discipline/standards/performance intelligence, clean release
provenance and external operational qualification.

## 19. Critical architectural risks

1. **Discipline identity fragmentation:** four incompatible labels can corrupt
   package mapping and cross-discipline rules if not normalized first.
2. **Enum-as-plugin trap:** extending database check constraints and core enums
   for every discipline would keep the architecture nominally modular but
   operationally coupled.
3. **Authority collapse:** standards suggestions, Guidance, Candidate Materials
   or cross-discipline findings could be mistaken for accepted engineering or
   procurement facts.
4. **Copyright/licensing breach:** free-text AI standards citations or wholesale
   content storage could create legal and engineering-trust failures.
5. **Hidden-data inference:** cross-discipline, KPI and Health aggregation can
   leak protected facts through counts, scores or conflict existence.
6. **Analytics surveillance:** Methods & Systems can drift into individual
   productivity ranking or enterprise management/ERP.
7. **Release provenance:** a closed capability present only in a cumulative
   dirty/untracked tree cannot be the basis of a reproducible commercial
   artifact.
8. **Repository-evidence substitution:** passing scripts/tests cannot substitute
   for real external deployment and recovery exercises.

## 20. Open Human decisions

1. Accept or reject this 20-PATCH re-baseline of the earlier unregistered
   PATCH-051 through PATCH-065 candidates.
2. Confirm that basic technical procurement, FAT/SAT and closeout remain inside
   Commercial V1, while cost control, proposal/contract, notifications and n8n
   move post-V1.
3. Choose the commercial authentication floor: administrator MFA is
   recommended; enterprise SSO/SCIM is deferred unless contractually required.
4. Select supported standards sources and acquire/define content rights before
   standards design begins.
5. Set the supported deployment profile and measurable SLO/RPO/RTO/capacity
   targets for PATCH-070.
6. Decide whether first V1 licensing is a signed offline dedicated-deployment
   license, server-managed entitlement, or both; domain code must remain neutral.

## 21. Governance disposition

Discovery verdict: **COMPLETE / READY FOR HUMAN ARCHITECTURE AND ROADMAP
REVIEW**.

Recommended immediate next capability: shared Multi-Discipline Core and the
Discipline Package contract.

Proposed next title: **PATCH-051 — Shared Multi-Discipline Core & Discipline
Package Contract**.

PATCH-051 registration is recommended only after Human acceptance of this
discovery and roadmap re-baseline. It is not registered by this artifact. No
Architecture, EDS, IDS, Implementation Plan, IRR, implementation, migration,
delivery or future-PATCH authority is granted.

Exact next resume point: Human Architecture/Roadmap review of this discovery,
including the six open decisions. STOP before PATCH-051 registration.
