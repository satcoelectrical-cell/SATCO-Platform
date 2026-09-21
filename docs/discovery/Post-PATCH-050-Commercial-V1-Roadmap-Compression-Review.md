# Post-PATCH-050 Commercial V1 Roadmap Compression Review

Date: 2026-08-28
Mode: Architecture / roadmap decision review only
Human roadmap review authority: GRANTED
PATCH-051 registration: NOT GRANTED
Implementation authority: NOT GRANTED

## 1. Review verdict

**PASS / COMPLETE / READY FOR HUMAN ROADMAP FREEZE DECISION.**

The original 20-PATCH proposal is technically coherent but is not the minimum
roadmap needed for SATCO's first paid Commercial V1 sale. It includes six
valuable EPC-lifecycle capabilities that are not required to deliver the
Human-confirmed first-sale promise. It also separates three groups whose
architecture, validation and rollback boundaries can remain governable inside
three carefully batched PATCHes.

The minimum responsible recommendation is **10 additional proposed PATCHes,
PATCH-051 through PATCH-060**. This reduces governance boundaries by 50%
without removing shared Multi-Discipline architecture; operational Electrical,
Instrumentation and Control & Automation packages; Cross-Discipline
Intelligence; Methods & Systems / Engineering Performance; rights-aware
standards intelligence; ordinary-user Evidence; security/release capability;
commercial package entitlements; or representative deployment qualification.

This review does not freeze the roadmap, register PATCH-051, modify a CLOSED
PATCH or grant design/implementation authority.

## 2. Commercial-V1 minimum principle

A capability remains in first-sale V1 only if its absence on the sale date
would make SATCO materially unsellable, unsafe, misleading, operationally
unsupported or unable to deliver its advertised AI-assisted Engineering
Intelligence promise.

Commercial V1 is not required to execute the whole EPC lifecycle. A coherent
V1 can support engineering work, evidence, reports, knowledge, standards,
discipline intelligence and engineering-performance visibility while external
commercial/procurement and field-execution systems retain their authority.

## 3. Original 20-PATCH classification

| Original | Classification | Compression disposition | First-sale basis |
|---|---|---|---|
| 051 Shared Multi-Discipline Core | KEEP V1 | Remains new 051 | Mandatory architectural prerequisite |
| 052 Electrical Package | KEEP V1 | Merge into new 052 | Mandatory operational package |
| 053 Instrumentation Package | KEEP V1 | Merge into new 052 | Mandatory operational package |
| 054 Control & Automation Package | KEEP V1 | Merge into new 052 | Mandatory operational package |
| 055 Cross-Discipline Intelligence | KEEP V1 | Becomes new 053 | Core advertised differentiator |
| 056 Evidence Workbench/Retention | REDUCE | Becomes new 055 | Ordinary-user workflow required; advanced disposal deferred |
| 057 Standards Registry/Retrieval | KEEP V1 | Merge into new 054 | Required only as end-to-end Report intelligence foundation |
| 058 Standards-Aware Reports/Memory | KEEP V1 | Merge into new 054 | Mandatory advertised standards capability |
| 059 Engineering Performance | KEEP V1 | Merge into new 056 | Mandatory Methods & Systems layer |
| 060 Vendor Registry | DEFER V1.1 | No V1 PATCH | Useful adjacent workflow, not product promise |
| 061 Requirements/Requisitions | DEFER V1.1 | No V1 PATCH | Human-adopted procurement workflow can follow first sale |
| 062 RFQ/Proposal Evaluation | DEFER V2+ | No V1 PATCH | High-risk procurement expansion |
| 063 Award/Order/Supply | DEFER V2+ | No V1 PATCH | ERP-adjacent and not required for Engineering Intelligence sale |
| 064 Engineering Health | KEEP V1 | Merge into new 056 | Same source/derived-intelligence boundary as performance |
| 065 FAT/SAT/Commissioning | DEFER V1.1 | No V1 PATCH | Existing Evidence/Deliverables/Reports can record sources without workflow |
| 066 Handover/Closeout | DEFER V1.1 | No V1 PATCH | Existing completion basis/Reports/Memory support first-sale engineering use |
| 067 Guided Lifecycle/Command Center | REDUCE | Becomes new 057 | Product coherence required; full lifecycle Wizard is not |
| 068 Security/CI/Release | KEEP V1 | Becomes new 058 | Paying-customer safety and reproducibility |
| 069 Packaging/Entitlements | KEEP V1 | Becomes new 059 | Required to sell package combinations |
| 070 Deployment Qualification | KEEP V1 | Becomes new 060 | Required to prove supported operation |

## 4. Procurement, FAT/SAT and closeout decisions

### Vendor & Panel Builder Registry — C / MOVE TO V1.1

SATCO can sell its Engineering Intelligence product without owning reusable
vendor master data. Supporting Files, Evidence, Deliverables and Reports can
retain vendor-originated engineering material without creating a vendor
business aggregate. The registry is a coherent V1.1 precursor to procurement.

### Material/Equipment Requirements & Requisitions — C / MOVE TO V1.1

PATCH-050 already makes Candidate Material Requirements explicitly preliminary,
non-BOM and non-procurement. Commercial V1 remains truthful by stopping there.
A separately Human-adopted requirements/requisition lifecycle is valuable but
not necessary to sell discipline intelligence.

### RFQ, Quotation & Technical Proposal Evaluation — D / MOVE TO V2+

This introduces vendor-confidential comparison, deviation, communication and
selection risk. It is a distinct technical-procurement product lane and should
follow a proven Vendor/Requisition V1.1 foundation.

### Award, Order & Supply Impact — D / MOVE TO V2+

Award/order/supply crosses into purchasing and ERP-adjacent responsibility. It
does not belong in the minimum Engineering Intelligence release.

### FAT/SAT/Commissioning — C / MOVE TO V1.1

Commercial V1 Evidence, Deliverables and Technical Reports can capture and
govern test artifacts without SATCO owning a test/punch workflow. Dedicated
plans, witnesses, findings and punch authority are a coherent V1.1 product
extension, especially for automation customers, but are not a first-sale
blocker.

### Handover & Closeout — C / MOVE TO V1.1

Project Foundation completion criteria, Deliverables, accepted Reports and
Memory provide sufficient first-sale completion records. A formal handover
package and closeout gate can follow FAT/SAT and procurement in V1.1.

## 5. Safe and unsafe mergers

### Safe mergers

1. **Electrical + Instrumentation + Control & Automation packages.** They share
   the accepted package contract, are all mandatory, and can be delivered as
   three separately gated implementation batches plus one integrated
   conformance batch. Package-specific contracts/tests and independent Human
   acceptance remain separate inside the PATCH.
2. **Standards registry + Report/Memory enrichment.** The minimum registry has
   no independent V1 product purpose beyond retrieval-backed standards-aware
   reporting. One end-to-end PATCH makes rights, retrieval, citation validation,
   Human selection and accepted provenance reviewable together.
3. **Methods & Systems / Engineering Performance + Engineering Health.** Both
   are derived, explainable intelligence over the same canonical histories and
   share time-window, source-watermark, data-quality, aggregation and
   hidden-data safeguards. One PATCH avoids two competing indicator systems.

### Unsafe mergers

- **Package kernel + operational packages:** kernel identity, compatibility and
  legacy mapping must be accepted before three domain implementations depend on
  it.
- **Evidence + FAT/SAT:** Evidence is shared infrastructure; FAT/SAT is a
  discipline/project workflow with Human witness and punch authority.
- **Security/release + entitlements:** application identity/session/supply-chain
  security and commercial license enforcement have different threat models and
  rollback boundaries.
- **Entitlements + deployment qualification:** qualification must exercise an
  already accepted, immutable entitlement-enabled release.
- **Standards + Evidence:** both involve source material, but standards rights,
  applicability and citation authority are not the Evidence lifecycle.

## 6. Minimum Commercial-V1 floors

### Authentication and security

- administrator MFA is mandatory; TOTP plus single-use recovery codes is the
  minimum, while WebAuthn and enterprise federation may follow;
- short access tokens plus server-side, hashed, rotating refresh sessions with
  reuse detection, explicit logout/revocation and auth-version invalidation;
- generic-failure login throttling keyed safely by account and network source,
  bounded backoff/lockout and no account-existence leakage;
- current admin-mediated single-use account recovery retained and integrated
  with MFA recovery; email self-service recovery is not mandatory;
- safe authentication/security Audit for login, failure threshold, session,
  MFA, recovery and administrative security operations;
- current server-derived Organization context and operation-specific tenant
  isolation retained with complete negative tests;
- no SSO/SAML/OIDC/SCIM requirement for the initial dedicated-customer profile.

The current unused refresh-token response must not survive ambiguously: V1 must
either implement the governed rotating session above or remove refresh issuance
and document mandatory reauthentication. The recommended floor is rotation and
revocation because it supports a usable paying-customer session lifecycle.

### Standards

V1 requires standard identity, publisher and edition; applicability metadata;
supersession/current standing; Organization rights metadata; one governed
retrieval adapter contract; immutable source snapshot/digest; exact citation
handle; Human selection; fail-closed validation; and provider output bound to
retrieved handles. Unknown identities, editions or clauses cannot enter an
accepted Report.

Deferred are a broad standards-library product, wholesale copyrighted content,
OCR, embeddings/vector search, automated compliance declarations, clause-wide
knowledge graphs and many publisher connectors. V1 may begin with a small
curated metadata catalog and one legally authorized retrieval source.

### Supporting-file Evidence

V1 requires ordinary-user Evidence creation, file selection/linking, provenance
review, standing transition, supersession/withdrawal, lineage, Report reliance
and protected/unavailable states. It also requires one default Organization
retention rule, hold flag, auditable disposition eligibility and export/recovery
behavior. Advanced retention schedules, automated physical purge and generic
records management are deferred.

### Methods & Systems / Engineering Performance

V1 uses a small frozen indicator catalog: required-input aging, blocked-work
aging, milestone predictability, deliverable review cycle, risk/issue/change
aging, Interface Commitment fulfilment, completeness trend and accepted-Report
flow. Every indicator exposes calculation, time window, source watermark,
denominator, limitations and authorized drill-down. Engineering Health is the
same factor model presented at Project/discipline level; there is no employee
score, enterprise data warehouse, forecasting ML or ERP/HR analytics.

### Operations

The sole supported first-release profile is one SATCO-managed, dedicated
single-customer deployment using the repository's production Compose topology:
TLS reverse proxy, frontend, FastAPI backend, PostgreSQL, private S3-compatible
object storage and malware scanner, with secret files and separated runtime /
migration / backup principals.

It requires one clean signed release; release manifest/SBOM/scans; real DNS and
TLS; encrypted off-host backup; isolated restore; upgrade and recovery/rollback
rehearsal; health/readiness/metrics; external alert delivery; safe support
bundle; incident/break-glass exercise; capacity evidence; and Human-approved
RPO/RTO/SLO. HA, multi-region, Kubernetes, SaaS orchestration and enterprise
federation are excluded.

### Entitlements

V1 requires one signed offline entitlement/license document suitable for the
supported dedicated profile. It binds Organization/deployment, Core, enabled
discipline packages and combinations, named or active seat limit, validity,
bounded grace, support/update entitlement, issue identity and signature. The
backend verifies it fail-closed and the frontend only reflects backend
decisions. Anti-rollback state and Audit prevent simple replacement with an old
license. Expiry blocks new optional-package mutations but preserves authorized
historical read/export. Billing, metering, subscription automation and advanced
license analytics are excluded.

## 7. Recommended compressed roadmap — 10 PATCHes

### PATCH-051 — Shared Multi-Discipline Core & Discipline Package Contract

- Scope: normalized stable discipline identity; trusted versioned package
  descriptors/registry; compatibility; Organization/project configuration;
  legacy mapping; shared ports; Audit identity; conformance harness; truthful
  package-aware navigation.
- Why before sale: every mandatory package and package combination depends on
  it; enum-based extension would not be a credible modular product.
- Dependencies: PATCH-050; ADR-016/017/020/021.
- Exclusions: discipline domain rules, arbitrary plugins, entitlement
  enforcement and billing.
- Complexity/risk: VERY HIGH / HIGH.
- Exit: existing discipline data maps losslessly, one canonical vocabulary is
  enforced, package enable/disable is scope-safe, and a reference test package
  passes all core conformance contracts.

### PATCH-052 — Electrical, Instrumentation, and Control & Automation Discipline Packages V1

- Scope: three real packages, each with package-specific objects,
  relationships, inputs, deliverables, Evidence expectations, deterministic
  completeness/Guidance rules and operational workspace UI; integrated package
  conformance.
- Why before sale: the Human-confirmed product cannot be sold on labels or
  placeholders; all three advertised packages must be operational.
- Dependencies: 051.
- Exclusions: ETAP/EPLAN/CAD, instrument sizing, PLC/DCS/SIS/HMI/SCADA code,
  final design/approval and future disciplines.
- Complexity/risk: VERY HIGH / HIGH.
- Exit: separate representative Electrical, Instrumentation and Control
  projects and one integrated project pass package contracts, security,
  performance and Human-authority evidence.

### PATCH-053 — Cross-Discipline Interfaces, Consistency & Engineering Intelligence

- Scope: versioned E/I/C interfaces, Interface Commitment integration, missing
  and inconsistent information, dependency/change impact, cross-discipline
  completeness and evidence-linked Guidance with Human review links.
- Why before sale: meaningful cross-discipline intelligence is a mandatory
  differentiator of the integrated package.
- Dependencies: 052 and current Context/Relationship/EKG foundations.
- Exclusions: autonomous conflict resolution, unbounded traversal and source
  mutation.
- Complexity/risk: VERY HIGH / HIGH.
- Exit: representative power/control, signal/I/O, interlock/trip and shared
  equipment scenarios detect omissions/conflicts without hidden-data leakage.

### PATCH-054 — Rights-Aware Standards Registry & Standards-Aware Technical Report Intelligence

- Scope: minimum standards/edition/applicability/rights registry, one retrieval
  contract, immutable citation handles, AI handle selection, Human acceptance
  into Report revisions and accepted Report/Memory provenance.
- Why before sale: standards-aware, retrieval-backed reporting is mandatory and
  unsafe if registry and enrichment are reviewed separately.
- Dependencies: 051–052, Evidence, Technical Reports and Memory.
- Exclusions: wholesale content, broad library management, OCR/vector search,
  invented clauses and compliance approval.
- Complexity/risk: VERY HIGH / HIGH.
- Exit: only authorized retrieved identities/editions/clauses can enter an
  accepted Report; rights loss and supersession retain truthful history and
  fail closed for current content display.

### PATCH-055 — Commercial Evidence Workbench & Minimum Retention Governance

- Scope: Evidence create/review/lifecycle/lineage/reliance UX; existing secure
  file pipeline integration; default retention, hold, disposition eligibility,
  export and recovery semantics.
- Why before sale: ordinary engineering users need a coherent evidence workflow
  rather than backend-only Evidence creation and fragmented file linkage.
- Dependencies: PATCH-027/032/040/043 and current Supporting File UI.
- Exclusions: OCR, semantic extraction, generic EDMS, complex records schedules
  and automatic physical purge.
- Complexity/risk: HIGH / MEDIUM.
- Exit: real upload -> scan -> Evidence -> accepted Report -> Memory and
  historical recovery works without raw IDs, leakage or authority collapse.

### PATCH-056 — Methods & Systems Engineering Performance, Health & Next-Action Intelligence

- Scope: frozen discipline-neutral KPI catalog, reproducible source-watermarked
  trends, Project/discipline Engineering Health factors, authorized drill-down
  and advisory next actions.
- Why before sale: Methods & Systems / Engineering Performance is mandatory;
  Health is its Project-facing expression and should not become a second
  analytics architecture.
- Dependencies: 053 plus execution, deliverable, control, completeness and
  Report histories.
- Exclusions: employee ranking, enterprise BI/ERP/HR, opaque score, ML
  forecasting, approval and automatic task creation.
- Complexity/risk: VERY HIGH / HIGH.
- Exit: every metric/health factor is reproducible, limitation-visible,
  time-bounded and safe against hidden-count inference.

### PATCH-057 — Commercial Product Experience & Engineering Command Center Completion

- Scope: integrated and discipline-specific navigation, package-aware onboarding,
  coherent Project/discipline workspaces, cross-discipline/standards/Evidence/
  performance composition, actionable owner-routed next steps, accessibility
  and responsive polish.
- Why before sale: mandatory capabilities must be usable by paying customers,
  not isolated backend panels.
- Dependencies: 052–056.
- Exclusions: generic lifecycle Wizard/BPM, duplicate domain state, fake totals,
  procurement and FAT/SAT workflow.
- Complexity/risk: HIGH / MEDIUM.
- Exit: integrated and each single-discipline configuration completes its core
  Human journeys with real data and no raw-ID/backend-only step.

### PATCH-058 — Commercial Authentication, Application Security & Reproducible Release Foundation

- Scope: administrator MFA/recovery, rotating/revocable sessions, authentication
  throttling, legacy exposure reconciliation, security Audit, CI quality and
  security scans, SBOM, signed immutable artifacts and release dossier.
- Why before sale: customer credentials, tenant data and release supply chain
  must be supportable and reproducible.
- Dependencies: stable product surface through 057; secure requirements apply
  throughout earlier PATCHes.
- Exclusions: SSO/SAML/OIDC/SCIM, HA, SaaS orchestration and entitlement logic.
- Complexity/risk: VERY HIGH / HIGH.
- Exit: a clean revision creates one signed traceable release; auth/session/MFA,
  tenant, vulnerability and independent security gates pass with no unresolved
  Critical/Major.

### PATCH-059 — Commercial Package Configuration, Seats & Signed Entitlements

- Scope: signed offline dedicated-deployment license, Core + any supported E/I/C
  combination, seats, validity/grace, support/update entitlement, anti-rollback,
  backend/API enforcement, admin UX and historical-read preservation.
- Why before sale: SATCO must sell integrated and discipline-specific packages
  without source forks or trivial unauthorized activation.
- Dependencies: 051–052 and immutable release identity from 058.
- Exclusions: billing, subscription automation, usage metering and advanced
  licensing analytics.
- Complexity/risk: HIGH / HIGH.
- Exit: all package/seat/expiry/upgrade matrices pass API and UI enforcement;
  disabling/expiry cannot erase or expose historical records.

### PATCH-060 — Representative Commercial Deployment Qualification & V1 Release Certification

- Scope: perform one real supported deployment using release 058 and entitlement
  059; DNS/TLS, secrets, database, storage/scanner, backup/restore,
  upgrade/recovery, monitoring/alerts, support, break-glass, capacity, RPO/RTO,
  documentation and first-customer rehearsal; final certification evidence.
- Why before sale: repository contracts alone do not prove that a paying
  customer's system is deployable, recoverable and supportable.
- Dependencies: all frozen V1 capability PATCHes, especially 058–059.
- Exclusions: new product domains, HA, multi-region, Kubernetes, customer-managed
  variants and enterprise federation.
- Complexity/risk: HIGH / HIGH.
- Exit: the signed release is reproducibly installed, operated, recovered and
  upgraded in the supported profile; independent final review and Human
  Commercial V1 certification are PASS / ACCEPTED / COMPLETE.

## 8. Dependency graph and critical path

```text
PATCH-050 accepted core
  -> 051 Multi-Discipline package kernel
      -> 052 E/I/C operational packages
          -> 053 Cross-Discipline Intelligence
              -> 056 Performance/Health Intelligence

      -> 054 Standards Registry + Report Intelligence ----+
Current Evidence core -> 055 Evidence Workbench ----------+-> 057 Product UX
                                                           -> 058 Security/Release
                                                           -> 059 Entitlements
                                                           -> 060 Qualification/Certification
```

The true first-sale critical path is:

`051 -> 052 -> 053 -> 056 -> 057 -> 058 -> 059 -> 060`.

PATCH-054 and PATCH-055 are mandatory parallel lanes that must join before
PATCH-057 completes.

## 9. Commercial V1 exit gate

Commercial V1 is sellable only when:

1. PATCH-051 through PATCH-060, if Human-frozen and later registered, are each
   DONE/CLOSED with no unresolved Critical/Major;
2. Core + Electrical, Core + Instrumentation, Core + Control & Automation,
   every supported combination and integrated E/I/C run without source or
   database forks;
3. each package and the integrated configuration pass representative project,
   authority, isolation, resource and conformance scenarios;
4. cross-discipline omissions/conflicts/impact are evidence-linked,
   limitation-visible and never autonomously resolved;
5. standards citations are registry-known, exact-edition, retrieval-backed,
   rights-authorized and Human-selected; invented identities/clauses fail;
6. ordinary users can complete the Evidence lifecycle and accepted historical
   provenance survives retention/recovery behavior;
7. Methods & Systems indicators and Engineering Health are reproducible,
   explainable and protected against surveillance/hidden-data inference;
8. administrator MFA, governed session lifecycle, throttling, recovery,
   security Audit and tenant negative tests pass;
9. one clean revision builds signed immutable artifacts, SBOM, scans, migration
   set and release manifest through CI;
10. package/seat/expiry/upgrade entitlement matrices pass without unauthorized
    activation or historical-data loss;
11. the one supported deployment profile passes real TLS, secrets, object
    storage/scanner, backup/restore, upgrade/recovery, monitoring, support,
    incident, capacity and RPO/RTO exercises;
12. administrator/operator/support/user documentation and integrated/single-
    discipline customer journeys are verified against the release;
13. independent final review and explicit Human Commercial V1 Release
    Certification are PASS / ACCEPTED / COMPLETE.

## 10. Complexity and risk comparison

| Measure | Original | Compressed | Change |
|---|---:|---:|---:|
| Proposed first-sale PATCH boundaries | 20 | 10 | -50% |
| Deferred first-sale boundaries | 0 | 6 | 4 to V1.1; 2 to V2+ |
| Safe merger reductions | 0 | 4 | Three package groups |
| True sequential critical-path PATCHes | approximately 15 | 8 | materially shorter |

This is a governance/dependency reduction, not a claim that mandatory
discipline, standards or security implementation is small. The compressed
roadmap remains technically ambitious. Its principal risks are concentrated in
PATCH-051 discipline identity/migration, PATCH-052 three-package delivery,
PATCH-053 hidden-data-safe cross-discipline analysis, PATCH-054 standards rights,
PATCH-056 safe analytics, PATCH-058 identity/supply-chain security and PATCH-059
entitlement anti-rollback.

Commercial risk decreases because the first release focuses on SATCO's actual
Engineering Intelligence promise and reaches qualification sooner. The
remaining commercial risk is scope depth: package exit criteria must represent
real engineering work, not token catalogs or attractive UI. Deferring
procurement/FAT/closeout is commercially safe only if marketing, contracts and
product UI make those exclusions explicit.

## 11. Human-freeze readiness and remaining decisions

The architecture and dependency boundaries are sufficiently understood for a
Human to freeze the compressed 10-PATCH Commercial V1 roadmap. A freeze is not
created by this review.

The Human freeze should record four configuration decisions without changing
the proposed PATCH count:

1. exact standards publishers/sources and legal rights for the first supported
   catalog;
2. whether engineer MFA is mandatory or optional while administrator MFA
   remains mandatory;
3. exact supported deployment platform plus SLO/RPO/RTO/capacity targets;
4. acceptance of the recommended signed offline entitlement model for the
   dedicated-deployment V1 profile.

It should also explicitly approve moving PATCH-060/061/065/066 concepts to
V1.1 and PATCH-062/063 concepts to V2+, superseding only their unregistered
future-roadmap placement, not any historical governance record.

## 12. Governance disposition

Recommended immediate candidate:

**PATCH-051 — Shared Multi-Discipline Core & Discipline Package Contract.**

PATCH-051 remains the correct immediate next capability because all mandatory
packages, package combinations, standards applicability hooks and entitlements
depend on canonical discipline/package identity.

PATCH-051 registration is recommended only after a separate explicit Human
Commercial V1 roadmap freeze. It remains **NOT REGISTERED**. No Architecture,
EDS, IDS, Implementation Plan, IRR, implementation, migration, delivery or
release authority is granted.

Exact next resume point: Human review and freeze decision for this compressed
roadmap and its four configuration decisions. STOP before PATCH-051
registration.
