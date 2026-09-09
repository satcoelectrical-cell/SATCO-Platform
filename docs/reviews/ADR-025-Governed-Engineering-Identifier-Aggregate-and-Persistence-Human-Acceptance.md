# ADR-025 Human Acceptance

## Human decision

**HUMAN ADR-025 ACCEPTANCE: PASS / ACCEPTED.**

**ADR-025: ACCEPTED.**

Date: 2026-09-04.

This append-only record accepts the reviewed decision in
`docs/adr/ADR-025-Governed-Engineering-Identifier-Aggregate-and-Persistence.md`.
It changes governance status only and does not silently alter the candidate,
its independent review, or its accepted semantics.

## Acceptance basis

| Governance evidence | State |
|---|---|
| ADR-025 candidate | PASS / ACCEPTED-CANDIDATE / READY FOR HUMAN ADR ACCEPTANCE |
| Independent ADR review | PASS |
| Critical / Major / Minor / Observation | `0 / 0 / 0 / 0` |
| Blocking findings | NONE |
| Human authority | HUMAN ADR-025 ACCEPTANCE: PASS / ACCEPTED |

## Accepted semantics

Human acceptance preserves these reviewed decisions:

- Engineering Identifier is a separately governed EKG-adjacent aggregate;
- one Identifier belongs to exactly one immutable Engineering Object UUID;
- one Object may have zero through sixteen current Identifiers;
- a package-origin Object requires exactly one current primary Identifier and
  may have no more than fifteen current alternates;
- current uniqueness is Organization + Project + issuing scope + kind +
  normalized value;
- lifecycle is `current`, `superseded`, or `withdrawn`;
- replacement lineage is same-scope, linear, acyclic, and historically
  preserved;
- physical deletion is prohibited;
- owner authorization precedes resolution and disclosure;
- package/configuration/entitlement state grants no Identifier data authority;
- accepted Object V2 Report snapshots contain the transactionally locked and
  rechecked complete current Identifier set and perform no live lookup; and
- Human review, approval, Report acceptance, and engineering authority remain
  unchanged.

Package descriptors may require only Core-owned Identifier kinds. They cannot
create Identifier classes, change uniqueness, approve Identifier standing,
resolve collisions, merge Objects, or become a data authority.

## Chronology preservation

The candidate ADR and independent review remain preserved. The independent
review's verdict and finding counts are not rewritten. This Human record is the
subsequent acceptance event.

## Authority boundary

This acceptance does not register PATCH-052 by itself and grants no EDS-052,
IDS-052, Implementation Plan, production/test implementation, migration,
deployment, staging, commit, push, or PATCH-053+ authority.

**ADR-025: ACCEPTED.**
