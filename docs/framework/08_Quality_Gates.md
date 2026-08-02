# SATCO Implementation Framework v1.1 — Quality Gates

## 1. Purpose

Quality Gates are cumulative, mandatory evidence gates. A failed gate returns
work to the earliest affected lifecycle phase.

## 2. Gate Matrix

| Gate | Required evidence | Passing outcome |
|---|---|---|
| QG-0 Problem | bounded problem, value, scope | Problem accepted |
| QG-1 Governance | hierarchy/status/dependency check | Authority coherent |
| QG-2 Architecture | ADR/XDR assessment and Architecture Review | PASS |
| QG-3 EDS | complete engineering design and review | Accepted/PASS |
| QG-4 IDS | exact implementation contract | Approved |
| QG-5 Readiness | executable plan, environment, dependencies | IRR READY |
| QG-6 Foundation | domain/contracts/unit tests | Sprint gate PASS |
| QG-7 Persistence | repository/UoW/migration/atomicity | Persistence PASS |
| QG-8 Application | service/security/concurrency/idempotency | Application PASS |
| QG-9 Transport | API/DI/errors/endpoint tests | Integration PASS |
| QG-10 Regression | dependency and complete suites | Zero failures |
| QG-11 Final Review | scope, diff, security, docs, rollback | Review PASS |
| QG-12 Delivery | approved commit/push evidence | Governed delivery |

Conditional technical gates are marked not applicable only by reviewed design,
never by implementer convenience.

### QG-M1 — Manifesto Alignment

QG-M1 is a cumulative evidence gate that supplements, and does not renumber or
replace, QG-0 through QG-12 or required Human approval.

| State | Meaning |
|---|---|
| PENDING | Required principle-level evidence or Human decision is incomplete. |
| PASS | All eleven principles were reviewed, affected principles have evidence, and no unresolved conflict remains. |
| FAIL | A conflict, evidence gap, weakened principle, or false authority claim exists. |

QG-M1 is evaluated before readiness and again during Final Review. All eleven
Manifesto principles remain binding; reviewed design may distinguish affected
from preserved principles but may not declare a principle inapplicable.

## 3. READY FOR IMPLEMENTATION Criteria

READY requires all of:

- PATCH registered, approved, bounded, and dependency-complete;
- durable decisions covered by Accepted ADRs/XDRs;
- Architecture Review PASS;
- EDS accepted and EDS Review PASS;
- IDS approved with exact file, model, API, migration, error, and test contracts;
- Implementation Plan executable with checkpoints, rollback, validation, and
  stop conditions;
- environment and repository assumptions verified;
- IRR explicitly states `READY FOR IMPLEMENTATION`;
- no unresolved P0 blocker.
- `Manifesto Alignment Verified: YES` and `QG-M1 Readiness Result: PASS`.

No other status phrase is equivalent.

## 4. BLOCKED Criteria

BLOCKED applies when work cannot progress safely under current authority. It
requires the Blocker Engine record and return to the earliest affected gate.
Partial implementation does not convert BLOCKED to PASS.
QG-M1 FAIL returns work to the earliest affected Foundation, Architecture, EDS,
IDS, readiness, Sprint, validation, or Final Review phase.

## 5. DONE Criteria

A PATCH is `IMPLEMENTATION COMPLETE` only when QG-1 through QG-11 pass and:

- every approved deliverable and acceptance criterion is satisfied;
- all sprints/checkpoints pass;
- exact files and no unrelated files changed;
- architecture and modularity remain conformant;
- security, visibility, protected-not-found, and stable errors pass;
- optimistic concurrency, idempotency, Audit, Domain Events, and atomicity pass
  where applicable;
- migrations pass upgrade, downgrade, re-upgrade, clean-chain, and drift checks
  where applicable;
- focused, dependency, adjacent, authentication, and full regression suites
  have zero failures;
- rollback/forward-repair strategy is executable;
- documentation and review artifacts required by the lifecycle are updated;
- final independent review passes;
- `QG-M1 Final Result: PASS` against the actual final diff and evidence;
- warnings and deferred recommendations are recorded;
- delivery actions remain pending until their own authorization is granted.

A PATCH is `DONE` only when it is already `IMPLEMENTATION COMPLETE`, the
Development Lifecycle's separately authorized Commit and Push gates have both
completed, and QG-12 has passed with repository and remote-state evidence.
Absent Commit or Push authority, the PATCH remains `IMPLEMENTATION COMPLETE —
DELIVERY AUTHORIZATION PENDING`; it is neither BLOCKED nor DONE.

Code compilation alone is never DONE.

## 6. Review Workflow

1. Implementer self-check against IDS and tests.
2. Codex technical review: repository, tests, migration, diff, security.
3. ChatGPT/architecture review: contract, scope, modularity, governance.
4. Human Reviewer validates evidence and issues PASS/FAIL.
5. PATCH owner resolves findings or records a governed blocker.
6. Final authority approves completion/delivery according to Governance Model.

AI reviews support and do not replace required Human approval.

## 7. Documentation Update Policy

During implementation, approved architecture documents are immutable unless a
blocker returns work to documentation. Implementation may update only artifacts
explicitly authorized by IDS or lifecycle completion records.

After validation, create or update required validation, regression, final
review, lessons learned, and future recommendation artifacts. Reviews record
evidence; semantic changes must be incorporated into the owning PATCH/ADR/XDR/
EDS/IDS and reapproved.

## 8. Rollback Gate

Before delivery prove:

- application rollback boundary;
- database downgrade or data-preserving forward-repair decision;
- backup/restore prerequisites;
- feature/traffic disablement where applicable;
- pre-PATCH regression restoration;
- no physical deletion of governed history without explicit authority.

## 9. Gate Evidence Integrity

Evidence must be reproducible and attributable. Counts, commands, revision IDs,
environment identity, dates, reviewer verdicts, and limitations are recorded.
Fabricated, stale, partial, or scope-mismatched evidence invalidates the gate.
QG-M1 evidence names the Manifesto version, affected principles, source
artifacts, reviewer, date, result, and limitations.
