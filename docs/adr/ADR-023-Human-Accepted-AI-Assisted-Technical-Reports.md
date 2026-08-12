# ADR-023 — Human-Accepted AI-Assisted Technical Reports as the SATCO V1 Engineering Authority Boundary

## Status

Accepted

## Date

2026-08-08

## Decision Owner

- Human Architecture Authority

## Approval Record

| Authority | Decision | Date |
|---|---|---|
| Independent ADR Review | PASS | 2026-08-08 |
| Focused ADR Re-review | PASS | 2026-08-08 |
| Human ADR Acceptance | PASS | 2026-08-08 |

Remaining findings: none.

This accepted decision establishes architectural authority within its scope. It
does not register a PATCH or authorize implementation.

## Context

SATCO Version 1 requires a practical Human authority boundary for transforming
captured Engineering Experience and advisory AI assistance into accountable
engineering output. The long-term architecture preserves Human Review as the
permanent trust boundary, but Version 1 is intentionally single-Human-first and
does not require enterprise separation between author, reviewer, and approver.

Universal Capture remains the canonical origin of Engineering Experience.
Engineering Journal remains a read-only, presentation-only workspace over that
canonical source. Neither capability owns an accepted engineering conclusion.
SATCO therefore requires a dedicated durable record whose accepted version
expresses the accountable Human engineering output without making AI,
presentation state, or contextual documentation authoritative.

## Decision

SATCO Version 1 shall use a dedicated persistent **Technical Report Aggregate**
as its bounded engineering authority record.

Engineering Review is a Human authority operation performed on an exact
Technical Report version. It is not a separate Aggregate in Version 1.
Self-review is valid: the same accountable Human may author, review, and accept
a Technical Report. Multi-user and enterprise Review governance are deferred.

AI may assist analysis, drafting, organization, and explanation. AI remains
advisory and non-authoritative. Only explicit Human acceptance establishes the
accepted engineering output.

## Version 1 Technical Report Purposes

The closed Version 1 purpose vocabulary is:

- `field_experience`;
- `troubleshooting`;
- `engineering_analysis`;
- `technical_recommendation`.

Preliminary Engineering Assessment is a qualification that may characterize a
Technical Report. It is neither a lifecycle state nor a Technical Report
purpose.

## Aggregate and Lifecycle Boundary

Technical Report is a dedicated persistent Aggregate with this Version 1
lifecycle:

```text
draft → accepted
```

Human acceptance applies to one exact report version. Acceptance-defining
technical content and the Human acceptance record become immutable when that
version is accepted.

An accepted Technical Report Aggregate is terminal for technical content. A
semantic or technical change requires a new successor Technical Report
Aggregate. Successor lineage preserves continuity but does not, by itself,
mean that the predecessor has been superseded or that its authority has been
withdrawn.

## Correction Boundary

Post-acceptance non-semantic corrections may be permitted only when they do not
alter acceptance-defining elements. A correction must not change technical
meaning, purpose, scope, conclusions, recommendations, relied-upon Evidence or
standards, accountable Human identity, accepted version, or acceptance record.

If a proposed correction could change engineering interpretation or the basis
of acceptance, it is semantic and requires a successor Technical Report
Aggregate.

## Canonical Context Boundary

Contextual documentation may reference and explain canonical Project,
Workspace, Engineering Object, Capture, Evidence, Relationship, or other
governed capability state. It shall not mutate, override, or silently
reclassify another canonical capability.

Evidence and standards materially relied upon by a Technical Report must remain
historically resolvable for the accepted report version. Later change to an
external or canonical source must not erase the accepted report's attributable
basis.

## Acceptance and Publication

Acceptance establishes accountable technical authority for the exact Technical
Report version. Acceptance is not publication. Distribution, publication,
audience, release, and Organizational Memory admission remain separately
governed concerns and receive no authority from this ADR.

## Human and AI Responsibilities

The accountable Human:

- determines whether the report is technically acceptable;
- owns the engineering judgment expressed by acceptance;
- may self-review in Version 1;
- accepts only an exact report version;
- cannot silently alter accepted technical content.

AI:

- may assist but cannot accept, approve, publish, or become accountable;
- cannot convert Capture, Evidence, contextual material, or a draft into
  accepted engineering authority;
- cannot change accepted content or acceptance history;
- remains replaceable and provider-independent.

## Deferred Governance

Version 1 does not establish enterprise Review governance. The following are
deferred to separately accepted architecture:

- mandatory separation of author, reviewer, and approver;
- multi-reviewer quorum or voting;
- role matrices for enterprise approval;
- delegated approval authority;
- staged review boards;
- publication and release governance;
- Organizational Memory admission.

Deferral shall not be interpreted as permission to add these behaviors within
a Version 1 Technical Report implementation PATCH.

## Consequences

### Positive

- SATCO V1 gains one explicit, accountable engineering authority boundary;
- single-Human-first delivery remains practical without weakening Human
  authority;
- AI assistance remains useful without becoming authoritative;
- accepted technical meaning and its basis remain historically traceable;
- Technical Report evolution preserves immutable accepted records;
- future enterprise Review governance can extend the architecture without
  redefining the V1 Aggregate.

### Constraints

- every acceptance must bind to an exact report version;
- accepted technical content cannot be edited in place;
- semantic change creates a successor Aggregate;
- lineage cannot silently express supersession;
- referenced Evidence and standards require historical resolvability;
- acceptance cannot be treated as publication or Organizational Memory
  admission.

## Alternatives Rejected

### Engineering Review as a separate Version 1 Aggregate

Rejected because Version 1 is single-Human-first and the durable authority
record is the accepted Technical Report. Review is the Human authority
operation that accepts its exact version.

### AI acceptance or automated technical authority

Rejected because AI is advisory and cannot assume accountable engineering
judgment.

### Editing an accepted report in place

Rejected because it would detach Human acceptance from the exact technical
content reviewed and accepted.

### Treating successor lineage as automatic supersession

Rejected because continuity and authority replacement are distinct decisions.

### Treating acceptance as publication

Rejected because technical authority and controlled distribution have separate
meanings and governance.

## Compatibility

This decision refines the accepted Phase 2 sequence without weakening:

- the Constitution and Engineering Intelligence Manifesto;
- ADR-013 provider-independent advisory AI;
- ADR-021 Engineering Intelligence ownership and Human trust boundary;
- Universal Capture as the canonical origin of Engineering Experience;
- Engineering Journal as read-only and presentation-only;
- existing Engineering Object, Relationship, Evidence, Context, Project,
  Workspace, and Organization authority boundaries.

For Version 1, the next conceptual bounded capability is **Technical Report**.
The previously conceptualized enterprise-style Engineering Review capability
is not independently registered; its V1 responsibility is the Human acceptance
operation governed by this ADR. Enterprise Review remains deferred.

## Explicit Non-Authorization

This ADR does not:

- register a PATCH or reserve a PATCH number;
- authorize backend or frontend implementation;
- define an EDS, IDS, implementation plan, API, schema, migration, or UI;
- authorize publication, Organizational Memory, Knowledge Graph expansion, or
  AI-provider integration;
- modify any completed PATCH or existing canonical capability.

Implementation requires a separately registered and approved PATCH, PASS
Architecture Review, accepted EDS and IDS, executable Implementation Plan, and
READY Implementation Readiness Review.

## Revision History

| Version | Date | Description |
|---|---|---|
| 1.0 | 2026-08-08 | Registered the Human-accepted decision after Independent ADR Review PASS, Focused ADR Re-review PASS, and Human ADR Acceptance PASS. |
