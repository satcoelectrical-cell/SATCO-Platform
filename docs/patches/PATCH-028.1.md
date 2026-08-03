# PATCH-028.1 — Project Organization Ownership

## 1. Document Control

| Field | Value |
|---|---|
| Document ID | PATCH-028.1 |
| Status | DONE / CLOSED |
| Classification | Bounded prerequisite for PATCH-028 Sprint 2 |
| Owner | SATCO Product Owner / Platform Architecture |
| Date | 2026-08-02 |

The accepted IDS, Implementation Plan, and IRR authorize the bounded source
implementation and isolated validation now present in the repository.
Development/deployment migration remains separately gated and unauthorized.
Bounded commit and push completed at
`f58b2ebcf0df4f143729c76e6d43349dc298b6c4`; remote verification and QG-12
pass. Development/deployment migration remains unauthorized and unexecuted.

## 2. Engineering and Security Problem

Project has no trusted Organization ownership. SATCO therefore cannot enforce
same-Organization Project context for Project-wide or Workspace-dependent
Engineering Intelligence capabilities. PATCH-028 cannot safely persist Capture
until the Project boundary is repaired.

## 3. Objective

Make Organization an immutable, non-null, server-derived Project invariant and
apply it consistently to Project persistence, creation, lookup, listing,
mutation, Search, Workspace/dependent reference validation, and protected
cross-Organization behavior.

## 4. Governing Documents

- Constitution and Engineering Intelligence Manifesto v1.0;
- proposed ADR-022 Project Organization Ownership;
- PATCH-025 Authenticated Organization Context;
- ADR-011 Project Core Domain;
- ADR-016 Dual-Use Platform Operating Model;
- Governance Model, Development Lifecycle, Framework v1.1, and QG-M1;
- PATCH-028 blocker record.

## 5. Manifesto Alignment Record

### Supported Principles

- Engineering Context Is Sacred;
- Evidence Before Assumption;
- Organizational Ownership;
- Continuous Evolution.

### Affected Principles

- Human Authority;
- Engineering Context Is Sacred;
- Evidence Before Assumption;
- Explainability;
- Organizational Ownership;
- Continuous Evolution.

### Preserved Principles

- Engineering First;
- Capture Once;
- Context Before Recommendation;
- Intelligence Before Automation;
- Provider Independence.

### Engineering Intelligence Contribution

The change makes Project context trustworthy across the Organization boundary,
so Engineering Knowledge cannot be attached to a Project in another tenant by
an independently valid identifier.

### Risks

- invented or ambiguous backfill ownership;
- cross-Organization disclosure through Project lookup/Search;
- breaking existing Project creation callers;
- inconsistent child records created before Project ownership;
- destructive downgrade after ownership becomes authoritative;
- silent scope expansion into Organization administration or Project transfer.

## 6. Architecture Scope

EDS-028.1 shall define:

- immutable Project `organization_id` aggregate invariant;
- server-side creation derivation from PATCH-025 context;
- complete existing Project Ownership Inventory contract;
- approved backfill/abort rules;
- final NOT NULL/FK/index constraints;
- Project repository/service/API and Search scoping;
- protected-not-found behavior;
- Workspace and dependent-domain compatibility validation;
- migration expand/backfill/constrain/downgrade/forward-repair behavior;
- Audit and accountability consequences;
- focused and full regression requirements.

## 7. Project Ownership Inventory

Before migration readiness, the repository/data authority shall produce a
reviewable inventory containing, for every existing Project:

- immutable Project ID and Project Code;
- candidate Organization UUID(s) and evidence;
- approved owning Organization UUID;
- approving Human authority and date;
- unresolved/conflicting state when no decision is available.

The inventory must be complete and contain exactly one approved active
Organization for every Project. Sensitive operational data shall not be
committed unless separately authorized; the inventory may be recorded as
review evidence or a secure migration input according to EDS/IDS.

## 8. Scope Boundaries

In scope:

- Project aggregate/model/schema/repository/service/API/search changes strictly
  required for Organization ownership;
- one or more explicitly designed additive migration stages;
- existing-data ownership resolution mechanism;
- affected Workspace/dependent reference validation;
- focused security/migration/regression tests.

Out of scope:

- Organization CRUD, invitation, selection UI, billing, or entitlements;
- Project transfer between Organizations;
- Customer Organization redesign;
- customer-specific code forks;
- PATCH-028 Capture persistence or continuation;
- broad Project feature redesign;
- frontend implementation;
- inferred/heuristic ownership without Human approval;
- production migration execution, commit, push, or deployment.

## 9. Dependencies

- PATCH-025 DONE;
- ADR-022 Accepted before EDS acceptance;
- approved preservation/default-Organization decision (complete);
- approved initial User membership decision before runtime readiness;
- current Alembic lineage verified at IRR;
- PATCH-028 remains blocked until PATCH-028.1 is DONE.

## 10. Acceptance Criteria

- every Project has exactly one immutable Organization;
- creation derives Organization from authenticated active membership;
- clients cannot set or change trusted Organization;
- every Project query/mutation/Search path is Organization-scoped;
- cross-Organization access returns protected behavior without identifiers or
  counts;
- every existing Project has an attributable approved mapping;
- missing/ambiguous/conflicting mappings stop migration;
- final schema enforces non-null/FK ownership;
- dependent Project references can validate Organization equality;
- existing same-Organization behavior remains compatible;
- migration and complete regression evidence pass;
- QG-M1 readiness and final gates pass.

## 11. Explicit Stop Conditions

- ADR-022 not Accepted;
- inventory incomplete or not Human-approved;
- any Project lacks exactly one owning Organization;
- migration would infer ownership from User/Customer/Workspace/Object alone;
- exact affected Project/Search/dependent file set is undefined;
- protected-not-found or backward compatibility is unresolved;
- implementation would require PATCH-028 Capture files.

## 12. Current Authorization

```text
Architecture technical review: PASS
Human architecture acceptance: ACCEPTED
Project Ownership Inventory: PASS — 7 Projects covered by approved rule
EDS-028.1 independent review: PASS WITH READINESS BLOCKER
Human EDS acceptance: ACCEPTED — 2026-08-02
Default Organization membership decision: ACCEPTED — admin@satco.com
IDS-028.1 independent review: PASS
Human IDS acceptance: ACCEPTED — 2026-08-02
Implementation Plan-028.1: ACCEPTED
IRR-028.1: READY FOR SCOPED IMPLEMENTATION
Manifesto Compliance: PASS
QG-M1 Readiness Result: PASS
Sprint 1: PASS — isolated migration and preservation harness
Sprint 2: PASS — Project and Search tenant boundary
Sprint 3: PASS — dependent loader closure
Full backend regression: PASS — 381 passed, 0 failed
QG-M1 Final Result: TECHNICAL PASS
IDS-028.1 Amendment 2 independent review: PASS
Human QG-11: PASS
Implementation: COMPLETE
QG-12 prerequisites: PASS
Commit: PASS — f58b2ebcf0df4f143729c76e6d43349dc298b6c4
Push: PASS
Remote verification: PASS
QG-12: PASS
PATCH-028.1 CLOSED/DONE: YES
Development/deployment migration: NOT AUTHORIZED / NOT EXECUTED
```

## 13. Revision History

| Version | Date | Description |
|---|---|---|
| 0.1 | 2026-08-02 | Initial bounded Project Organization ownership prerequisite. |
| 0.2 | 2026-08-02 | Recorded preservation decision and advanced to proposed EDS with access-bootstrap blocker. |
| 0.3 | 2026-08-02 | Recorded Human acceptance of EDS-028.1; implementation remains blocked. |
| 0.4 | 2026-08-02 | Registered approved bootstrap admin and proposed IDS-028.1; no migration executed. |
| 0.5 | 2026-08-02 | Accepted IDS-028.1 after independent PASS; implementation plan remains required. |
| 0.6 | 2026-08-02 | Proposed implementation plan and recorded IRR hold pending Human Plan acceptance. |
| 0.7 | 2026-08-02 | Accepted Plan and recorded focused IRR READY; development migration remains separately gated. |
| 0.8 | 2026-08-02 | Paused Sprint 2 for one-file shared test-fixture IDS amendment. |
| 0.9 | 2026-08-02 | Accepted Amendment 1 and resumed scoped implementation. |
| 1.0 | 2026-08-02 | Reconciled three completed implementation Sprints and 381-test regression evidence to PATCH-028.1; retained final-review, migration, and delivery gates. |
| 1.1 | 2026-08-03 | Human QG-11 recorded FAIL because five related runtime/test changes are absent from the exact IDS file set; formal closure withheld. |
| 1.2 | 2026-08-03 | Focused IDS Amendment 2 and independent review PASS reconciled exactly five files; repeated Human QG-11 PASS established implementation completion with QG-12 pending. |
| 1.3 | 2026-08-03 | Human authority granted bounded commit and push authorization; QG-12 and CLOSED/DONE remain pending execution evidence. Migration remains unauthorized. |
| 2.0 | 2026-08-03 | Recorded commit f58b2eb, push and remote verification PASS, QG-12 PASS, and formal DONE/CLOSED status; migration remains unauthorized and unexecuted. |
