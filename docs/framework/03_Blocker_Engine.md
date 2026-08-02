# SATCO Implementation Framework v1.1 — Blocker Engine

## 1. Purpose

The Blocker Engine converts ambiguity and inconsistency into a controlled
governance action. It prevents Codex or any implementer from guessing.

## 2. Blocker Classes

### Governance Blocker

Examples: unregistered PATCH, conflicting document status, missing approval,
non-binding Proposed ADR used as authority, or IRR not READY.

Owner: Governance or the named document owner.

### Architecture Blocker

Examples: unclear aggregate ownership, undefined lifecycle, conflicting
dependency direction, absent security policy, or a durable decision meeting the
ADR threshold without an Accepted ADR.

Owner: Human Architect and Architecture Guardian.

### Contract Blocker

Examples: missing field semantics, command mismatch, unclear validation owner,
undefined error outcome, or EDS/IDS disagreement.

Owner: PATCH/EDS/IDS owner, reviewed by architecture.

### Dependency Blocker

Examples: prerequisite PATCH incomplete, required table absent, incompatible
enum scopes, unavailable Evidence capability, or missing trusted identity scope.

Owner: prerequisite PATCH owner.

### Repository Blocker

Examples: current code contradicts approved design, dirty overlapping changes,
multiple migration heads, broken test bootstrap, or unavailable execution
environment.

Owner: implementation owner or repository maintainer.

### Validation Blocker

Examples: focused test failure, migration drift, security regression, incomplete
coverage of acceptance criteria, or full regression failure.

Owner: implementation owner until independent review.

## 3. Detection Sequence

At every checkpoint ask:

1. Is authority explicit and approved?
2. Are dependencies present and at the required status/version?
3. Are domain terms, lifecycle, commands, responsibilities, and errors exact?
4. Can every required behavior be implemented using the authorized file set?
5. Is security deterministic and deny-by-default?
6. Can persistence and migration match the approved model without invention?
7. Can acceptance criteria be tested reproducibly?
8. Does current repository state still satisfy readiness assumptions?

Any “no” or material “unknown” creates a blocker candidate.

## 4. BLOCKED Criteria

Return `BLOCKED` when safe progress within existing authority is impossible,
including:

- a higher-authority contradiction;
- a missing decision that changes behavior or data semantics;
- an unapproved file, table, endpoint, enum, dependency, or migration;
- a required security or confidentiality rule that cannot be derived;
- a migration that cannot exactly match approved state;
- repeated test/regression failure attributable to the PATCH;
- a destructive/external action lacking explicit authorization;
- inability to preserve unrelated user work.

Difficulty, time, or implementation complexity alone is not a blocker.

## 5. Stop Protocol

When blocked:

1. Stop before the unauthorized action.
2. Preserve the current repository state.
3. Identify the earliest affected governance gate.
4. State one precise blocker, its evidence, affected documents/files, and the
   minimum decision needed.
5. Do not propose implementation as a substitute for the decision.
6. If authorized, create a bounded prerequisite PATCH chain.
7. Resume only after the corrected chain reaches READY.

## 6. Blocker Deduplication

Root causes govern reporting. Merge duplicates, remove consequences of a
higher-level issue, and avoid cosmetic or historical cleanup unless it blocks
the active PATCH.

Priority:

- P0: must resolve before implementation or completion;
- P1: must resolve before release but may not block the current isolated step;
- P2: governed future improvement.

## 7. Bounded Prerequisite Pattern

When a dependency is genuinely absent:

```text
Registry confirmation
→ bounded prerequisite PATCH
→ Architecture Review
→ accepted EDS and review
→ approved IDS
→ executable Implementation Plan
→ IRR READY
→ prerequisite implementation and validation
→ consumer PATCH focused re-review
```

The prerequisite implements only the missing capability. It shall not become a
vehicle for repository-wide cleanup or redesign.

## 8. Closure Evidence

A blocker closes only when its owning authoritative document records the
decision, affected downstream contracts are reconciled, review passes, IRR is
updated when readiness changed, and a focused verification proves implementers
no longer need to guess.
