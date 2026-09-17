# ADR-028 — Commercial Evidence Workbench & Minimum Retention Governance

## Status

**Proposed / Candidate — awaiting independent architecture review and Human ADR acceptance.**

This candidate is not Accepted. It establishes no EDS, IDS, implementation, migration, frontend, deployment, staging, commit, push, or PATCH-056+ authority.

## Date

2026-09-14

## Decision owner and authority

- Decision owner: Human Architecture Authority.
- PATCH-055 Registry: **REGISTERED / OPEN**.
- Human PATCH-055 Discovery Acceptance: **PASS / ACCEPTED / COMPLETE**.
- ADR-028 preparation authority: **GRANTED**.
- Independent architecture review authority: **GRANTED**.
- Human ADR-028 acceptance: **NOT YET GRANTED**.

## Context

PATCH-055 is the Human-frozen Commercial V1 capability for a commercially operable Evidence Workbench and minimum retention governance. Existing SATCO capabilities already provide governed Evidence, secure Supporting File intake and scanning, accepted Technical Report provenance, and Human-admitted Organizational Memory. The remaining architecture problem is to make that chain operable for ordinary authorized users while adding minimum retention, hold, disposition eligibility, export, and historical recovery semantics without collapsing engineering authority or rewriting history.

The accepted Discovery establishes the target chain:

`upload -> scan -> Evidence -> accepted Technical Report -> Memory`


The chain must work without raw canonical-ID entry, cross-Organization leakage, automatic AI authority, or reinterpretation of accepted engineering history.

## Problem

Evidence engineering state and records-retention state answer different questions. `current`, `withdrawn`, `superseded`, and `rejected` describe engineering standing; retention, hold, disposition eligibility, export, and recovery describe custody and governed availability. Combining them would let administrative lifecycle events silently change engineering meaning or let engineering transitions imply deletion authority.

The existing Supporting File `disposition` term describes scanner disposition (`clean`, `unsafe`, `indeterminate`). PATCH-055 must not overload that term with retention disposition semantics.

A commercial workbench must also let an authorized user create and review Evidence, attach exact scanner-cleared Supporting Files, perform Human lifecycle decisions, understand lineage and reliance, and then use current Evidence as Technical Report provenance without typing raw internal identifiers.

## Decision

SATCO shall implement PATCH-055 around **orthogonal Engineering Evidence and Retention Governance lifecycles**.

Canonical ownership remains separated:

| Capability | Canonical responsibility |
|---|---|
| Evidence Aggregate | engineering Evidence identity, source meaning, lifecycle, lineage, replacement and reliance semantics |
| Supporting File Asset | private file intake, scan state, exact object identity, integrity and file availability |
| Technical Report | Human-accepted engineering conclusion and immutable exact relied-upon provenance |
| Organizational Memory | deliberate Human-admitted reuse of accepted Report knowledge |
| Retention Governance | retention basis, hold, disposition eligibility/decision, governed export and historical recovery against canonical Evidence/File identities |

Retention Governance is not a second Evidence aggregate and does not own engineering standing.

## Core invariants

1. Engineering lifecycle and retention lifecycle are independent dimensions.
2. Human engineering authority remains exclusively with existing Evidence/Report/Memory Human decision boundaries.
3. Retention events never make Evidence current, accepted, approved, authoritative, withdrawn, rejected, or superseded.
4. Engineering lifecycle events never by themselves authorize physical deletion.
5. A hold blocks a retention disposition from becoming actionable while the hold is effective.
6. Disposition eligibility is a deterministic governed fact; it is not deletion authority.
7. Automatic physical purge is outside PATCH-055.
8. Historical Technical Report and Memory provenance is immutable and is never rewritten by later Evidence, retention, rights, storage, export, or recovery events.
9. Recovery restores authorized access to retained historical material; it never restores engineering standing.
10. AI is advisory only and has no authority to accept Evidence, impose or release hold, approve disposition, authorize export or recovery, accept Reports, or admit Memory.

## Evidence Workbench boundary

The commercial workbench shall orchestrate existing domain authorities rather than create a new omnibus aggregate. It shall provide authorized selectors and server-composed commands for Evidence creation, file linkage, lifecycle review, lineage/replacement, reliance inspection, and Technical Report source selection.

Clients may express Human intent and select authorized opaque handles, but may not author canonical Organization, Project, Workspace, Evidence, Supporting File, lineage, reliance, or retention identity fields.

No workflow step may require ordinary users to type raw UUIDs or other internal canonical identifiers.

## Retention basis

Commercial V1 shall support a minimum explicit retention basis bound to canonical Evidence and/or Supporting File identities. The basis must be attributable, versioned, Organization-scoped, and capable of representing a default retained-until decision or an explicit indefinite-retention decision.

## Hold and disposition semantics

A hold is an explicit governed constraint with attributable authority, reason, effective state, and audit history. While active, it prevents disposition from becoming actionable for the affected retained material.

Disposition eligibility shall be computed from deterministic retention facts and hold state. It may indicate that material is eligible for a later Human disposition decision, but it shall not itself delete, purge, destroy, or make content inaccessible.

Commercial V1 may record Human disposition decisions and their rationale, but automatic physical purge is excluded. Any future destructive disposal requires a later explicitly governed capability and authority.

## Export semantics

A governed export creates an attributable copy from currently authorized retained material. Export does not alter the source Evidence lifecycle, retention basis, hold state, Report provenance, Memory provenance, or canonical ownership.

Every export of protected material must reauthorize the current actor and Organization/Project/Workspace scope before disclosure. Export records retain safe metadata sufficient to identify actor, source identities/versions, time, purpose or rationale where required, and resulting export identity or digest.

## Historical recovery semantics

Recovery restores authorized access to retained historical material whose engineering standing remains whatever its canonical owner records. Recovery never converts withdrawn, superseded, rejected, unavailable, or historical Evidence into current Evidence.
Recovery must preserve exact historical identity, integrity and lineage. Protected content access at recovery time is subject to current authorization and rights; safe provenance may remain resolvable even when bytes are not currently disclosable.

## Authorization, concurrency and audit

All protected lookup, content access, lifecycle action, retention action, export and recovery operations shall authorize before disclosure. Server-derived Organization scope is mandatory; protected absence and forbidden states must not create cross-Organization enumeration or count oracles.

Authority-relevant commands require optimistic or transactional concurrency protection so stale Evidence, file, hold, retention, or authorization state cannot be used to complete a conflicting action.
Audit/outbox payloads shall contain minimized identifiers, versions, state codes, digests, actors, correlations and timestamps. They shall not contain file bytes, unsafe scanner content, secrets, object-store keys, unrestricted exports, or AI prompts containing protected material.

Idempotency must be scoped after authorization to the relevant Organization, actor and request digest; a prior result from another authority boundary must never be replayed or disclosed.

## Historical reliance

Accepted Technical Reports retain the exact Evidence version and Supporting File historical basis used at Human acceptance. Later lifecycle, retention, hold, disposition, export, recovery, storage, rights, or access changes append new facts and never rewrite that accepted basis.

Organizational Memory admitted from an accepted Report retains the same historical provenance principle. Current reuse remains subject to current authorization and the Memory capability's existing Human authority rules.

## Explicit non-scope

PATCH-055 does not introduce OCR, semantic extraction, embeddings, generic EDMS folders/workflows, enterprise records schedules, arbitrary customer retention engines, automatic physical purge, autonomous AI disposition, PATCH-056 Methods & Systems, PATCH-057 Command Center completion, PATCH-058..060 commercial auth/release/seats/deployment, procurement/vendor workflows, or post-PATCH-060 ideas.

## Compatibility with prior architecture

ADR-023 remains authoritative for Human-accepted Technical Reports and immutable accepted snapshots. ADR-027 remains authoritative for standards rights and current-access versus historical-basis separation. Existing Evidence and Supporting File aggregates retain their owners and lifecycle meanings. Organizational Memory remains Human-admitted reuse of accepted Report knowledge.

No prior accepted ADR or closed PATCH is superseded or silently amended.

## Consequences

Positive consequences are a commercially operable Evidence journey, explicit Human lifecycle decisions, recoverable historical reliance, deterministic minimum retention governance, and a clear separation between engineering meaning and custody/disposition semantics.

Costs include additional retention records, authorization/concurrency checks, export/recovery audit, UI state complexity, and stronger regression/security requirements across Evidence, Supporting Files, Technical Reports and Memory.

## Alternatives rejected

- Reuse Evidence lifecycle states for retention: rejected because it collapses engineering meaning and custody.
- Reuse Supporting File scanner `disposition` for retention: rejected because it creates semantic ambiguity and unsafe coupling.
- Let retention expiry delete automatically: rejected because physical purge is outside the frozen scope and historical reliance must remain governable.
- Restore superseded/withdrawn Evidence to `current` during recovery: rejected because recovery is access restoration, not engineering authority.
- Build a generic EDMS/records-management platform: rejected as out of Commercial V1 scope.

## Migration and implementation direction

This ADR authorizes no migration or implementation. If later accepted EDS/IDS proves persistence additions necessary, they must be additive and preserve current Evidence, Supporting File, accepted Report and Memory history. No revision ID, table, column, endpoint, DTO or batch is frozen here.

## EDS-deferred decisions

EDS-055 must define the smallest closed retention/hold/disposition state vocabularies; exact fields and validation; policy/default precedence; effective-time rules; concurrency/version guards; API commands/results; protected error mapping; UI accessibility/RTL states; audit/outbox/idempotency contracts; export/recovery limits; migration necessity; and deterministic conformance vectors.

IDS-055 must later freeze physical schema, constraints/indexes, repository/UoW topology, transaction and lock order, storage adapter behavior, migration/rollback details, observability redaction, and exact file manifest.

## Manifesto alignment

ADR-028 preserves all eleven Manifesto principles. It particularly strengthens Human Authority, Engineering Context Is Sacred, Evidence Before Assumption, Intelligence Before Automation, Explainability, Organizational Ownership, and Continuous Evolution by keeping engineering decisions Human-governed and historical provenance immutable while allowing later governed retention events to append rather than rewrite history.

No principle is declared inapplicable.

## Governance disposition

ADR-028 candidate design is **COMPLETE / READY FOR INDEPENDENT ARCHITECTURE REVIEW**.

Human ADR acceptance is not implied. EDS-055, IDS-055, implementation, migration, staging, commit, push and PATCH-056+ remain not authorized by this ADR candidate.

## Human ADR acceptance

- Human Architecture Authority decision: **PASS / ACCEPTED / COMPLETE**.
- Acceptance date: 2026-09-14.
- Accepted after independent Architecture Review returned `PASS / READY FOR HUMAN ADR ACCEPTANCE` with `Critical/Major/Minor = 0/0/0` and two non-blocking EDS observations.
- The two observations remain mandatory inputs to EDS-055 and are not waived by this acceptance.
- This acceptance authorizes progression to EDS-055 preparation and review only.
- It does not authorize IDS-055, implementation, migrations, production-code changes, staging, commit, push, or PATCH-056+ work.

`ADR-028: HUMAN ACCEPTED / COMPLETE`
