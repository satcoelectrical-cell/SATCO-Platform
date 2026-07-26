# XDR-000: Experience Decision Record Governance

## Status

Accepted

## Version

1.0

## Foundation Role

Certified and Stable governance source within SATCO Foundation v1.0.

This status does not prevent governed evolution. It prevents routine PATCH work
from rewriting experience governance without an approved XDR and a subsequent
Foundation version.

## Date

2026-07-26

## Purpose

This record establishes Experience Decision Records as the permanent mechanism
for documenting durable SATCO experience decisions.

XDR-000 governs future records under `docs/xdr/`. It defines why XDRs exist,
their authority, relationship to other governance, required content, lifecycle,
and supersession behavior.

## Why XDR Exists

Architecture Decision Records govern durable domain, technical, security, data,
and infrastructure decisions. They do not always capture the experience
consequences that determine whether engineers can understand and safely use the
resulting platform.

PATCH documents define bounded change. They should not become the only record
of experience conventions intended to govern many future PATCHes.

XDRs exist to preserve decisions such as:

- how the Engineering Cockpit organizes attention;
- how Engineering Context is kept visible;
- how AI Insights appear beside engineering work;
- how Human Review differs from approval;
- how status, readiness, Engineering Health, and AI Confidence are presented;
- how navigation preserves context;
- how color, motion, typography, and accessibility communicate meaning.

An XDR makes experience rationale, alternatives, consequences, and authority
traceable beyond one implementation.

## Authority

The authority order relevant to XDRs is:

```text
Constitution

↓

Product Bible

↓

Accepted ADR

↓

Experience Bible

↓

Accepted XDR

↓

PATCH

↓

Implementation
```

An XDR cannot override any higher-level document.

## Relationship With the Constitution

The Constitution defines permanent mission and human-responsibility
boundaries.

An XDR must preserve:

- engineers as final decision-makers;
- AI as an Engineering Copilot;
- visible uncertainty;
- explainable and traceable recommendations;
- prohibition of silent change to approved engineering decisions.

Any conflicting XDR is invalid.

## Relationship With the Product Bible

The Product Bible defines what SATCO is and which product principles are
permanent.

An XDR translates Product Bible principles into durable experience decisions.
It may clarify how a principle is experienced, but it may not redefine
Engineering Workspace, Engineering Execution Plan, Engineering Context,
Engineering Health, AI behavior, Human Review, or other canonical concepts.

When Product Bible alignment is unclear, the XDR remains Proposed.

## Relationship With ADR

An ADR governs architecture. An XDR governs the durable experience of that
architecture.

Examples:

- An ADR may define Workspace Status semantics; an XDR may define how statuses
  remain distinguishable from Workspace Readiness.
- An ADR may define AI Insight evidence; an XDR may define the information
  hierarchy used to reveal that evidence.
- An ADR may define archival; an XDR may define how archived context is
  distinguished from current operational work.

An XDR must not:

- change aggregate boundaries;
- create data ownership;
- change authorization;
- define persistence;
- redefine lifecycle meaning;
- contradict architectural constraints.

If an experience proposal requires an architecture change, the ADR is proposed
or updated first.

## Relationship With the Experience Bible

The Experience Bible is permanent experience governance. XDRs apply it to
durable decisions.

An XDR must identify:

- the Experience Bible principles it advances;
- any tradeoff among experience principles;
- implications for Calm Engineering and Engineering Attention;
- accessibility consequences;
- consistency with the Engineering Cockpit and One Screen – One Question.

An XDR cannot establish a parallel experience philosophy.

## Relationship With PATCHes

A PATCH references applicable Accepted XDRs.

When a PATCH proposes a durable experience decision not already governed, it
must:

1. identify the experience decision;
2. determine whether the XDR threshold is met;
3. propose an XDR;
4. obtain acceptance before final implementation approval.

A PATCH may contain local experience acceptance criteria without an XDR when
the behavior follows existing governance and creates no precedent.

PATCH completion evidence may reveal that an XDR needs clarification, but the
PATCH report does not silently alter the XDR.

## XDR Decision Threshold

An XDR is required for a durable or cross-PATCH decision involving:

- Engineering Cockpit composition;
- global navigation or context preservation;
- information hierarchy;
- attention, priority, or interruption;
- AI presence and advisory presentation;
- Engineering Reasoning or AI Confidence presentation;
- Human Review interactions;
- status, readiness, or Engineering Health presentation;
- cross-discipline experience patterns;
- empty, loading, error, or stale-state conventions;
- motion, color, typography, or icon semantics;
- accessibility standards or exceptions.

An XDR is normally not required for:

- content changes following existing terminology;
- a local arrangement with no reusable precedent;
- implementation technology;
- database or API design;
- a temporary experiment that cannot affect engineering decisions and is
  clearly isolated from production.

If uncertainty exists, governance review decides before implementation.

## XDR Lifecycle

```text
Proposed
    ↓
Accepted
    ↓
Superseded

Accepted
    ↓
Deprecated
```

### Proposed

The decision is under review.

- It may be drafted, compared, and tested conceptually.
- It is not binding.
- It does not authorize implementation.
- Open conflicts or missing evidence remain visible.

### Accepted

The decision is approved and binding within its stated experience scope.

- Product Bible, ADR, and Experience Bible alignment is confirmed.
- Accessibility implications are reviewed.
- Affected PATCHes must follow it.

### Superseded

A newer Accepted XDR replaces the decision.

- The original record remains unchanged as history.
- The superseding XDR is identified.
- Existing implementations are assessed for transition through a PATCH.

### Deprecated

The decision remains historical but should not be used for new work.

- Deprecation states the reason.
- Existing use and transition expectations are documented.
- Deprecation alone does not authorize removal or implementation change.

## Status Rules

- Every XDR has exactly one current status.
- Only Accepted XDRs are binding.
- Proposed XDRs cannot override Accepted XDRs.
- Superseded and Deprecated XDRs remain in the repository.
- Status changes require an authorized governance decision.
- An XDR must not be deleted to hide a prior decision.

## Required XDR Content

Every future XDR should include:

1. Identifier and title
2. Status
3. Date
4. Decision scope
5. Engineering problem
6. Experience problem
7. Governing Product Bible and ADR context
8. Decision
9. Experience principles
10. Information hierarchy
11. Human Review and AI implications
12. Accessibility implications
13. Alternatives considered
14. Consequences
15. Risks
16. Compatibility
17. Validation expectations
18. Supersession or deprecation relationship
19. Related PATCHes
20. Approval requirement

Sections may be marked not applicable only with a reason. Incomplete template
content is not acceptable for an Accepted XDR.

## Decision Quality Rules

An XDR must answer:

- Which engineering question becomes easier to understand?
- How is engineering effort reduced without reducing quality?
- What receives attention and why?
- Which Engineering Context remains visible?
- How are evidence, uncertainty, and AI Confidence presented?
- Where does Human Review occur?
- How is accessibility preserved?
- What could mislead or surprise an engineer?
- Which alternatives were rejected?
- How will later PATCHes verify the decision?

An experience decision that cannot demonstrate engineering value must be
rejected even if it is visually attractive or technically convenient.

## Conflict Resolution

If an XDR conflicts with:

- the Constitution: the XDR is invalid;
- the Product Bible: the Product Bible prevails;
- an Accepted ADR: the ADR prevails in architectural scope;
- the Experience Bible: the Experience Bible prevails;
- another Accepted XDR: explicit supersession or scope clarification is
  required;
- a PATCH: the Accepted XDR prevails in experience scope;
- implementation: implementation must be corrected or separately governed.

Work stops when the conflict affects engineering understanding, safety,
authority, or review.

## Ownership and Review

The Experience Architect owns XDR integrity.

Required review depends on scope and may include:

- Product Owner;
- Architecture Guardian;
- affected engineering representatives;
- accessibility reviewer;
- security or domain architect;
- PATCH owner.

AI agents may assist with drafting and consistency checks. They cannot accept
an XDR or approve an engineering decision.

## Change and Supersession

Minor editorial corrections may clarify an XDR without changing its decision.

A change requires a new XDR when it materially changes:

- engineering attention;
- navigation;
- information hierarchy;
- AI authority perception;
- Human Review behavior;
- state semantics;
- accessibility obligation;
- cross-PATCH experience behavior.

The new XDR names the superseded record. Affected PATCHes and implementations
are reviewed separately.

When an Accepted XDR changes foundational experience governance, the affected
foundation documents are updated only through a new certified Foundation
version. Acceptance of the XDR establishes justification; it does not silently
rewrite the existing Foundation baseline.

## Validation

Before an XDR becomes Accepted, confirm:

- governing documents were reviewed;
- the engineering and experience problems are explicit;
- the decision reduces effort while preserving quality;
- alternatives and risks are credible;
- no architecture change is hidden;
- AI remains advisory;
- Human Review remains explicit;
- accessibility is addressed;
- terminology is canonical;
- validation criteria are observable;
- implementation is not authorized by the XDR alone.

## Consequences

### Positive

- Durable experience decisions become traceable.
- PATCHes do not need to rediscover global experience rules.
- ADR and experience responsibilities remain distinct.
- Accessibility and AI presentation are reviewed early.
- Engineers receive more consistent behavior across Workspaces.

### Negative

- Experience changes require more deliberate review.
- ADR/XDR boundary decisions may require clarification.
- Records must be maintained and superseded consistently.
- Local convenience may be rejected to preserve global coherence.

## Final Decision

SATCO adopts Experience Decision Records.

All future durable experience decisions must follow this governance and remain
subordinate to the Constitution, Product Bible, accepted ADRs, and Experience
Bible.
