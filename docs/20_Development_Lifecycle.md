# SATCO Development Lifecycle

**Version:** 1.0

**Status:** Proposed

## Purpose

This document defines the mandatory development lifecycle for every SATCO
implementation PATCH. It establishes the evidence, approvals, and exit
conditions required to move from an engineering problem to a pushed change.

The lifecycle exists to keep implementation traceable, bounded, reviewable,
and consistent with SATCO governance. It does not modify the Constitution,
Product Bible, Foundation, accepted architecture, experience governance, or
professional engineering authority.

## Authority and Applicability

This is a supporting development-governance standard under the authority
defined by the SATCO Governance Model. It applies to every future PATCH and
sub-PATCH that authorizes implementation.

All work remains subordinate to:

1. the Constitution;
2. the Product Bible;
3. accepted ADRs;
4. the Experience Bible and accepted XDRs where applicable;
5. the approved PATCH;
6. the accepted EDS;
7. the approved IDS;
8. the Ready for Implementation IRR outcome.

A lower-level artifact may narrow a higher-level artifact but may not broaden,
reinterpret, or override it. Approval at one lifecycle phase does not imply
approval at another. If requirements are incomplete, contradictory, or beyond
approved authority, affected work stops for resolution in the proper governing
document.

The PATCH is the bounded authorization for implementation. Its scope,
exclusions, acceptance criteria, risks, rollback expectations, and required
governance must be approved before an IDS can be approved.
The IDS defines the implementation contract; implementation begins only after
IRR confirms readiness.

## Mandatory Lifecycle

Every implementation follows this sequence:

```text
Problem Discovery
    ↓
Architecture Discovery (when required)
    ↓
ADR (when required)
    ↓
Architecture Review
    ↓
EDS (Engineering Design Specification)
    ↓
EDS Review
    ↓
IDS (Implementation Design Specification)
    ↓
Implementation Readiness Review (IRR)
    ↓
Implementation
    ↓
Migration (if applicable)
    ↓
Validation
    ↓
Regression
    ↓
Final Review
    ↓
Commit
    ↓
Push
```

Conditional phases may be declared not applicable only through an explicit,
reviewed determination. They may not be skipped silently. Rework returns to
the earliest affected phase and invalidates downstream approval where its
inputs or scope have materially changed.

## No Skipped Gates

No PATCH may bypass an approved lifecycle gate. Every mandatory gate must
complete successfully before the next gate begins.

Prohibited flows include:

- ADR directly to Implementation;
- EDS directly to Commit;
- Implementation directly to Push;
- Validation directly to Push;
- Regression directly to Push.

A conditional phase is omitted only after its applicability has been assessed
and the not-applicable determination has been reviewed. Failure, rejection, or
materially changed inputs return work to the earliest affected gate. Urgency,
technical simplicity, prior informal agreement, automation, or partial success
does not authorize a skipped gate.

## Every Gate Produces an Artifact

Every lifecycle gate produces durable evidence of its work, decision, or
outcome.

| Gate | Required Artifact |
| --- | --- |
| Problem Discovery | Discovery Notes, if applicable |
| Architecture Discovery | Discovery Document |
| ADR | ADR Document |
| Architecture Review | Architecture Review |
| EDS | Engineering Design Specification |
| EDS Review | Design Review |
| IDS | Implementation Design Specification |
| Implementation Readiness Review | Implementation Readiness Review |
| Implementation | Source Code |
| Migration | Alembic Migration, if applicable |
| Validation | Validation Report |
| Regression | Regression Report |
| Final Review | Final Review Report |
| Commit | Git Commit |
| Push | Git Push |

For a conditional gate that is not applicable, the required trace is the
reviewed applicability determination. Artifacts must identify their governing
scope, relevant inputs, outcome, and authority where applicable. Repository
history alone does not replace required design, review, validation, or
governance evidence.

Every important engineering decision must leave a permanent, attributable
trace. The trace preserves why the decision was made, what scope it governs,
which evidence supported it, who or what produced it, and which accountable
authority reviewed or approved it. AI assistance does not remove the Human
Review or attribution requirement.

## Lifecycle Phases

### 1. Problem Discovery

**Purpose**

Establish the real engineering or product problem before proposing a solution.

**Required inputs**

- observed need, defect, risk, opportunity, or governance request;
- relevant repository and operational evidence;
- applicable Constitution and Product Bible principles;
- known affected domains and stakeholders.

**Required outputs**

- clear problem statement and engineering value;
- evidence, constraints, assumptions, and unknowns;
- affected governance and domain boundaries;
- initial PATCH boundary or recommendation that no implementation is needed;
- assessment of whether architecture or experience discovery is required.

**Approval gate**

The PATCH owner and relevant product or domain authority confirm that the
problem is valid, bounded, and worth progressing.

**Exit criteria**

- the problem is stated independently of a preferred implementation;
- expected engineering value and risk reduction are explicit;
- affected governance is identified;
- unresolved discovery questions are visible;
- the next required governance phase is identified.

### 2. Architecture Discovery

This phase is required when domain meaning, ownership, lifecycle, authority,
integration boundaries, or durable technical constraints are not sufficiently
understood. A reviewed not-applicable determination is sufficient when existing
accepted architecture fully governs the change.

**Purpose**

Discover the domain and architectural problem without selecting implementation
technology or prematurely making a durable decision.

**Required inputs**

- approved problem discovery;
- relevant Foundation and Product Bible documents;
- existing ADRs, XDRs, PATCHes, implementation, and domain evidence;
- identified architectural uncertainties.

**Required outputs**

- discovery record describing domain meaning, boundaries, actors, authority,
  relationships, constraints, risks, and open questions;
- assessment against the ADR and XDR decision thresholds;
- recommendation to create, amend through governance, confirm, or omit a
  decision record.

**Approval gate**

Relevant architecture authority confirms that discovery is sufficient to
assess durable decisions.

**Exit criteria**

- implementation design has not leaked into discovery;
- domain boundaries and unresolved questions are explicit;
- applicable existing decisions are identified;
- the need for an ADR or XDR is recorded.

### 3. ADR

This phase is required when the Governance Model’s ADR threshold is met.
Otherwise, the applicable accepted ADRs and the reason no new ADR is required
must be recorded.

**Purpose**

Make and preserve a durable architectural decision, including rationale,
alternatives, consequences, compatibility, and evolution constraints.

**Required inputs**

- approved discovery evidence where required;
- affected accepted ADRs and higher governance;
- architecture options, risks, and consequences;
- ADR-threshold assessment.

**Required outputs**

- a Proposed ADR, or a recorded confirmation that accepted architecture
  already governs the change;
- explicit compatibility with the Constitution and Product Bible;
- consequences, rejected alternatives, and future constraints.

**Approval gate**

An independent architecture review and authorized architecture governance
accept the ADR. A Proposed ADR never authorizes implementation.

**Exit criteria**

- every required ADR is Accepted;
- supersession and compatibility are explicit;
- no unresolved conflict with higher governance remains;
- the implementing PATCH can reference the decision.

### 4. Architecture Review

**Purpose**

Independently verify that the discovered domain and proposed or existing
architecture support the PATCH without hidden architectural change.

**Required inputs**

- problem and architecture discovery records;
- proposed or accepted ADRs;
- relevant Product Bible, Foundation, XDR, and PATCH material;
- known constraints and open questions.

**Required outputs**

- architecture review record;
- alignment and conflict findings;
- required corrections;
- recommendation to accept, accept with bounded corrections, or reject;
- confirmation when no new ADR is required.

**Approval gate**

The Architecture Guardian or authorized architecture reviewer accepts the
architectural basis.

**Exit criteria**

- required corrections are resolved or explicitly block progress;
- all required ADRs are Accepted;
- domain and ownership boundaries are coherent;
- no undocumented architectural decision is delegated to implementation.

### 5. EDS — Engineering Design Specification

**Purpose**

Translate the approved PATCH and architecture into a complete,
implementation-ready engineering design without implementing code.

**Required inputs**

- approved PATCH scope;
- accepted governing ADRs and XDRs;
- architecture-review outcome;
- relevant Foundation, Product Bible, domain, security, audit, search,
  compatibility, and experience requirements.

**Required outputs**

- an EDS defining objectives, scope, non-scope, domain behavior, ownership,
  authorization, audit, traceability, failure behavior, compatibility,
  validation expectations, and bounded implementation decomposition;
- explicit open questions that must be resolved before implementation design.

**Approval gate**

The EDS remains Proposed until independent design review and authorized design
approval are complete.

**Exit criteria**

- the design is complete enough to constrain implementation;
- no implementation leakage or technology choice exceeds its purpose;
- PATCH and accepted architecture alignment are traceable;
- material ambiguity is resolved or blocks progression.

### 6. EDS Review

**Purpose**

Test the EDS for completeness, consistency, scope discipline, safety, human
authority, and compatibility before implementation planning.

**Required inputs**

- proposed EDS;
- approved PATCH;
- governing Foundation, Product Bible, ADRs, and XDRs;
- architecture-review findings.

**Required outputs**

- independent EDS review;
- completeness, alignment, risk, and ambiguity findings;
- required corrections;
- readiness recommendation.

**Approval gate**

Authorized design governance accepts the EDS after required corrections.

**Exit criteria**

- the EDS status is Accepted;
- no unresolved scope or architectural conflict remains;
- human authority and AI boundaries are intact;
- implementation can be decomposed without inventing design.

### 7. IDS — Implementation Design Specification

**Purpose**

Define the mandatory, bounded implementation contract for one PATCH or
sub-PATCH before source code, database, API, migration, or test changes begin.

**Required inputs**

- approved PATCH;
- accepted EDS;
- accepted ADRs and XDRs;
- relevant repository state and technical standards;
- approved dependencies and environmental constraints.

**Required outputs**

- an IDS containing every mandatory section defined by this standard;
- exact implementation boundaries and dependency sequencing;
- validation, regression, migration, rollback, and completion evidence
  requirements.

**Approval gate**

The PATCH owner and relevant technical reviewers approve the IDS. Security,
database, architecture, experience, or domain reviewers participate when their
areas are affected.

**Exit criteria**

- the IDS is approved;
- every intended change is inside the PATCH and EDS;
- forbidden behavior and non-scope are testable;
- implementation and validation work can proceed without hidden design;
- unresolved scope expansion has returned to EDS or ADR governance.

### 8. Implementation Readiness Review

**Purpose**

Verify that the approved implementation design is complete, feasible,
sequenced, and ready to begin before any implementation change is made.

**Required inputs**

- approved IDS;
- confirmed implementation and environmental dependencies;
- planned implementation sequencing;
- migration plan where applicable;
- validation and regression strategies;
- performance and security considerations;
- rollback or recovery strategy where applicable.

**Required outputs**

- an Implementation Readiness Review artifact;
- one explicit outcome: **Ready for Implementation** or **Return to IDS**;
- findings, constraints, and required corrections;
- confirmation of the implementation baseline and authorized scope.

**Approval gate**

The PATCH owner and relevant technical reviewers issue **Ready for
Implementation** only when implementation can proceed without inventing scope,
design, dependencies, sequencing, or validation behavior.

**Exit criteria**

- the IDS is approved and matches PATCH and EDS scope;
- dependencies are complete and available;
- implementation order and ownership are explicit;
- migration readiness is confirmed where applicable;
- validation and regression strategies are executable;
- material performance and security considerations are addressed;
- rollback or recovery is ready where applicable;
- unresolved findings produce **Return to IDS** and block implementation.

### 9. Implementation

**Purpose**

Realize exactly the approved IDS while preserving higher governance and
existing supported behavior.

**Required inputs**

- approved IDS;
- Ready for Implementation IRR outcome;
- cleanly identified repository baseline;
- applicable coding, security, audit, authorization, and testing standards;
- approved implementation environment.

**Required outputs**

- bounded source and test changes;
- required documentation explicitly authorized by the IDS;
- traceable evidence of implementation decisions;
- identified migration work where applicable.

**Approval gate**

Implementation may begin only after IDS approval and a **Ready for
Implementation** IRR outcome. Material deviations require review before they
are made.

**Exit criteria**

- IDS-required behavior and tests are implemented;
- prohibited and non-scope behavior is absent;
- no hidden API, migration, database, architecture, or dependency change
  exists;
- no debug code, temporary artifact, unfinished stub, or unrelated modification
  remains;
- discovered genuine defects or scope conflicts are governed explicitly.

### 10. Migration

This phase applies whenever persisted data, database structure, indexes,
constraints, ownership, compatibility, or another deployed state must change.

**Purpose**

Deliver an explicit, reviewable, reversible or safely recoverable transition
between supported states.

**Required inputs**

- approved migration scope in the IDS;
- database and deployment standards;
- current and target-state evidence;
- data safety, compatibility, rollback, and recovery requirements.

**Required outputs**

- migration artifacts authorized by the IDS;
- upgrade, downgrade or recovery strategy as applicable;
- isolated-environment validation evidence;
- confirmation that unauthorized environments were not modified.

**Approval gate**

The responsible database or deployment reviewer approves migration safety and
evidence before release progression.

**Exit criteria**

- forward migration is deterministic and validated;
- rollback or recovery behavior is documented and validated where required;
- constraints, data preservation, and compatibility pass;
- no hidden or manual-only database change exists;
- protected development and production data remain unchanged unless explicitly
  authorized.

### 11. Validation

**Purpose**

Prove that the PATCH satisfies its approved behavior, safety, authorization,
audit, migration, and failure contracts.

**Required inputs**

- implemented PATCH;
- IDS validation requirements;
- EDS acceptance expectations;
- approved isolated validation environment and baseline fingerprints.

**Required outputs**

- focused functional and negative test results;
- database and migration evidence where applicable;
- authorization, audit, concurrency, search, safety, and rollback results where
  applicable;
- syntax, static, formatting, and repository-integrity results;
- documented warnings and failures.

**Approval gate**

The PATCH’s required technical reviewers accept the validation evidence.

**Exit criteria**

- Definition of Done and required focused tests pass;
- failures create no false success evidence;
- protected environments remain unchanged unless explicitly authorized;
- warnings and limitations are visible;
- unresolved failures block progression.

### 12. Regression

**Purpose**

Demonstrate that the bounded change has not broken supported behavior outside
its focused scope.

**Required inputs**

- validated implementation;
- complete applicable regression suites;
- known baseline warnings and compatibility requirements.

**Required outputs**

- full regression results;
- comparison with the approved baseline;
- investigation and disposition of new failures or warnings.

**Approval gate**

Relevant technical reviewers accept the regression evidence and any explicitly
approved limitations.

**Exit criteria**

- all required regression suites pass;
- no unexplained regression or warning remains;
- compatibility obligations are satisfied;
- any required correction returns to implementation and repeats validation and
  regression.

### 13. Final Review

**Purpose**

Perform the release-candidate review of scope, implementation, evidence,
repository hygiene, governance alignment, and readiness to commit.

**Required inputs**

- final working-tree changes;
- approved PATCH, EDS, IDS, ADRs, and XDRs;
- validation, migration, and regression results;
- review and correction history.

**Required outputs**

- final verdict;
- exact approved file set;
- remaining warnings and issues;
- confirmation of repository cleanliness and diff integrity;
- authorization or refusal to commit.

**Approval gate**

The authorized final reviewer returns PASS before any implementation commit.

**Exit criteria**

- only approved PATCH files are present;
- no unrelated change or temporary artifact remains;
- no debug code, commented-out code, unfinished stub, unresolved marker, or
  accidental whitespace change remains;
- required checks and reviews pass;
- the exact commit scope and message are approved.

### 14. Commit

**Purpose**

Create an immutable local repository record of the approved release candidate.

**Required inputs**

- passing final review;
- explicitly approved file set and commit message;
- clean staging plan.

**Required outputs**

- one or more explicitly authorized local commits;
- commit hash and commit-stat evidence;
- post-commit repository status.

**Approval gate**

Explicit Git approval is required. Final Review PASS does not silently grant
authority to stage or commit unless the approval says so.

**Exit criteria**

- only approved files are committed;
- commit content matches the reviewed release candidate;
- no amendment, rebase, tag, or additional commit occurs without authority;
- local repository status is reported.

### 15. Push

**Purpose**

Publish the approved local commit history to the authorized remote and branch.

**Required inputs**

- explicit push approval;
- verified branch, remote, working-tree state, and expected local/remote
  relationship;
- approved commit hashes.

**Required outputs**

- push result;
- local and remote HEAD verification;
- post-push repository status;
- synchronization confirmation or precise failure report.

**Approval gate**

Push requires separate explicit authority. Commit approval does not imply push
approval.

**Exit criteria**

- only the approved branch and commits are pushed;
- no force-push, tag, rebase, amendment, or unrelated remote mutation occurs
  unless separately authorized;
- local and remote state is verified and reported;
- any push failure leaves repository history unchanged and is reported.

## IDS Standard

The Implementation Design Specification is the mandatory implementation
contract. It is narrower than the EDS and PATCH and may not create product,
domain, architectural, experience, security, authorization, API, database, or
migration authority.

Every IDS shall contain:

### Purpose

State the bounded implementation outcome and the engineering value it realizes.

### Scope

List the exact behaviors, layers, files or file responsibilities, data
transitions, and validation work authorized for the implementation.

### Explicit Non-Scope

List adjacent behavior and tempting extensions that are not authorized.

### Dependencies

Identify governing documents, prior PATCHes, runtime or build dependencies,
environmental prerequisites, and required implementation ordering.

### Required Domain Objects

Identify the approved domain concepts the implementation must realize or
reference, their ownership boundaries, and their governing EDS definitions.
The IDS does not invent new domain architecture.

### Required Behaviors

Define observable success, failure, authorization, audit, concurrency,
compatibility, and lifecycle behavior in implementation-ready terms.

### Forbidden Behaviors

Define actions and outcomes that must never occur, including scope leakage,
authority escalation, data disclosure, silent mutation, false audit success,
and any prohibited AI behavior relevant to the PATCH.

### Definition of Done

Provide a finite checklist covering implementation, tests, migration evidence,
documentation authorized by scope, compatibility, repository hygiene, and
review readiness.

### Validation Requirements

Identify focused tests, negative tests, database-specific checks, migration
checks, authorization and audit checks, regression suites, static or syntax
checks, environmental fingerprints, and required result reporting.

### Exit Criteria

State the evidence and approvals required before the implementation may enter
Final Review.

An IDS must also identify:

- its governing PATCH, EDS, ADRs, and XDRs;
- assumptions and resolved open questions;
- exact migration and rollback obligations where applicable;
- compatibility and protected-environment requirements;
- expected warnings and prohibited unresolved issues;
- the approval state and reviewers required to authorize implementation.

## Scope Governance

No implementation may exceed its approved IDS scope.

Implementation convenience, discovered opportunity, available tooling, or AI
suggestion does not authorize expansion. A proposed addition must be classified
before work proceeds:

- if it changes implementation detail while remaining fully inside the
  accepted EDS and PATCH, update and reapprove the IDS;
- if it expands or changes the approved engineering design, update and
  reapprove the EDS and then the IDS;
- if it establishes or changes durable architecture, create or update the
  appropriate ADR through governance, obtain acceptance, update affected lower
  documents, and reapprove the EDS and IDS;
- if it changes PATCH authorization, update and reapprove the PATCH before
  downstream documents;
- if it changes Foundation or Product Bible meaning, stop and follow the
  Foundation governance process.

Scope expansion therefore requires an updated EDS or an approved ADR as
applicable, plus revalidation of all affected lower-level artifacts. An ADR
does not itself expand PATCH authorization.

Sub-PATCHes may narrow and sequence parent scope. They may not broaden it.
Unrelated defects and improvements are reported and deferred unless separately
authorized. A test that exposes a genuine defect does not automatically
authorize a fix beyond the IDS.

## Implementation Rules

Every implementation shall satisfy these rules:

- no hidden implementation;
- no hidden migrations or manual-only deployed-state changes;
- no undocumented architecture;
- no undocumented APIs, events, commands, or externally observable contracts;
- no undocumented database, constraint, index, ownership, or data changes;
- no undocumented dependencies or provider coupling;
- no silent reinterpretation of ambiguous requirements;
- no change to protected environments without explicit authorization;
- no weakening of assertions, authorization, audit, safety, or traceability to
  make validation pass;
- no AI-generated architectural decision without Human Review and acceptance
  by the authorized architecture governance;
- no AI approval of engineering, product, architecture, experience, PATCH,
  EDS, IDS, final-review, commit, or push decisions;
- no implementation artifact may present AI output as authoritative merely
  because it is generated, confident, or technically valid.

AI may assist discovery, drafting, implementation, validation, and review.
Its contributions remain attributable, reviewable, subordinate to governing
documents, and subject to accountable human approval.

## Review Policy

Every PATCH must pass all of the following before Commit:

1. **Design Review:** Architecture Review where applicable, EDS Review, and IDS
   approval establish the reviewed design and implementation contract.
2. **Validation:** Focused evidence proves the PATCH’s approved positive and
   negative behavior.
3. **Regression:** Complete applicable suites demonstrate compatibility with
   supported behavior.
4. **Final Review:** An authorized reviewer confirms scope, evidence,
   governance alignment, repository hygiene, and commit readiness.

A failure at any gate blocks progression. Corrections repeat all affected
downstream checks. Review findings are evidence and do not silently amend the
governing design; required changes must be incorporated into the proper
artifact and reapproved.

## Certification

Certification is a separate governance act used to declare that a large,
coherent milestone satisfies its governing baseline as a whole.

Certification may be required for:

- a new or materially changed Foundation version;
- a major architectural milestone spanning multiple domains or PATCHes;
- a platform release that establishes a new stable governance baseline;
- a material change to product identity, authority, safety, security, or
  professional responsibility boundaries;
- another milestone explicitly designated by authorized governance.

Certification should assess the coherent document and implementation set,
cross-domain compatibility, unresolved risks, evidence completeness, and the
authority required to declare the milestone stable.

Routine implementation PATCHes and sub-PATCHes do not require certification
unless their governing scope explicitly requires it. They still require every
applicable lifecycle gate in this standard. A passing PATCH review is not
Foundation or product certification, and certification does not replace PATCH
validation or Final Review.

## Lifecycle Governance

- Evidence must be reproducible and attributable.
- Approvals must identify the artifact, scope, and status being approved.
- Conditional phases require an explicit applicability decision.
- Material input changes invalidate dependent approvals.
- Rejected work preserves review evidence and returns to the appropriate phase.
- Emergency exceptions follow the Governance Model and do not permanently
  waive this lifecycle.
- Automated checks may verify evidence but may not grant human authority.
- Commit and Push remain separately authorized repository actions.

## Readiness Criteria

This standard is ready for adoption when:

- its lifecycle matches the Governance Model’s authority hierarchy;
- every mandatory phase defines purpose, inputs, outputs, approval gate, and
  exit criteria;
- the IDS contract is complete and bounded;
- scope expansion returns to the proper governing level;
- conditional phases cannot be skipped silently;
- implementation, migration, review, Commit, and Push authorities are
  explicit;
- certification remains proportional;
- Constitution, Product Bible, Foundation, and accepted ADR authority remain
  unchanged.
