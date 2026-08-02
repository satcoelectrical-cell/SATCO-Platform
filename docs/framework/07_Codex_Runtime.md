# SATCO Implementation Framework v1.1 — Codex Runtime

## 1. Purpose

The Codex Runtime defines the deterministic behavior activated by the prompt
`Implement PATCH-XXX`.

## 2. Runtime Input Resolution

Codex shall automatically resolve:

1. authoritative PATCH registry entry;
2. approved PATCH document;
3. governing Constitution/Product Bible/ADRs/XDRs/Blueprints;
4. Architecture Review;
5. accepted EDS and review;
6. approved IDS;
7. executable Implementation Plan;
8. READY IRR;
9. completed prerequisite PATCHes;
10. current repository implementation and tests.

Resolution uses the minimum deterministic source set. Codex reads the registry
entry, PATCH, its direct governing decisions and Blueprint, its EDS/IDS/plan,
their required reviews, its IRR, named dependencies, and materially affected
repository areas. It shall not rebuild a repository-wide governance inventory
when those sources resolve authority unambiguously.

### Engine Applicability Matrix

| Engine | Always load | Conditional trigger |
|---|---:|---|
| Framework Constitution | Yes | — |
| Implementation Workflow | Yes | — |
| Sprint Engine | Yes | — |
| Blocker Engine | No | Missing, conflicting, stale, or unauthorized requirement |
| Validation Engine | Yes | — |
| Testing Engine | Yes | — |
| Migration Engine | No | Schema, model, enum persistence, migration, or database bootstrap change |
| Quality Gates | Yes | — |
| Framework Roadmap | No | Framework evolution or prompt-reduction assessment |

The Governance Model owns policy authority, the Development Lifecycle owns
procedural gates, and the PATCH/EDS/IDS chain owns bounded change requirements.
Framework engines reference those rules and shall not reinterpret or duplicate
their authority. Conditional engines are loaded only when their trigger is
present. “Read the repository” authorizes scoped discovery, never unrelated
inspection or mutation.

## 3. Runtime Decision Procedure

### Automatic PATCH Selection

When asked to determine or execute the next PATCH without an explicit PATCH
identifier, Codex shall apply this algorithm exactly:

1. Load the authoritative PATCH Registry from the Governance Model.
2. Exclude every PATCH whose registry status is `DONE`, `CANCELLED`, or
   `SUPERSEDED`.
3. For each remaining PATCH, verify that every registered dependency is
   complete.
4. Verify implementation readiness through the mandatory approval chain and an
   IRR outcome of `READY FOR IMPLEMENTATION`.
5. Select the lowest-number executable PATCH from the remaining candidates.
6. If no executable PATCH exists, return exactly:
   `No executable PATCH available.`

Registry status is authoritative for selection. A lower-number PATCH that is
not ready, has incomplete dependencies, or has unresolved blockers is not
executable and does not prevent selection of the next lowest-number executable
PATCH. Codex shall not infer completion from source files, migrations, tests,
conversation history, roadmap wording, or an implementation report when the
authoritative registry has not recorded the terminal status.

An explicit instruction `Implement PATCH-XXX` resolves only the named PATCH and
does not invoke automatic selection.

```text
if no PATCH identifier was supplied: apply Automatic PATCH Selection
if no executable PATCH exists: return "No executable PATCH available."
if an explicit PATCH cannot be resolved uniquely: BLOCKED
if authority chain is incomplete/inconsistent: NOT READY
if IRR is not READY: NOT READY
if repository invalidates readiness assumptions: BLOCKED
if exact implementation boundary is executable: select earliest sprint
declare exact files
implement only that sprint
validate from focused to full
report IMPLEMENTATION COMPLETE, DELIVERY AUTHORIZATION PENDING, DONE, or BLOCKED
```

## 4. Prompt Minimization Contract

The Human need provide only `Implement PATCH-XXX` when all of the following are
already present:

- approved and registered PATCH;
- PASS Architecture Review;
- accepted EDS and PASS review;
- approved IDS with exact files/contracts;
- executable Implementation Plan with sprint/checkpoint sequence;
- READY IRR;
- completed dependencies;
- accessible validation environment.

Codex shall not request reconfirmation of decisions already explicit in those
documents. It asks only when a material choice is absent and cannot be resolved
from authority.

## 5. Runtime Scope Guard

- Announce the exact files before writing when required by IDS or request.
- Preserve dirty-worktree changes and never reset unrelated work.
- Use existing patterns only when compatible with approved authority.
- Reuse enums, ports, validators, adapters, fixtures, and stable errors; do not
  duplicate them.
- Never change documentation during implementation unless IDS or the completion
  policy authorizes it.
- Never commit, push, deploy, migrate protected environments, or perform
  destructive cleanup without explicit authority.

## 6. Tool and Execution Rules

- Prefer repository-native search and validation commands.
- Use scoped, non-destructive inspection before mutation.
- Use patch-based edits and explicit paths.
- Run independent safe validations in parallel only when outputs do not race.
- Use dedicated databases and existing containers according to environment
  standards.
- Restore disposable validation state to the approved condition.

## 7. Runtime Architecture Checklist

Before code:

- aggregate boundary and commands;
- lifecycle/authority matrices;
- validation ownership;
- authorization and visibility;
- repository/service/port responsibilities;
- Audit/event/idempotency/UoW requirements;
- optimistic concurrency;
- API/error/query bounds;
- migration scope;
- dependency direction and modular-extension boundary.

## 8. Runtime Reporting

Commentary gives concise progress and evidence during tool work. Final output is
self-contained and follows the PATCH-required format. Never claim a check ran
when it did not. Distinguish warnings from blockers and focused tests from full
regression.

## 9. Human Escalation

Escalate only for:

- missing authority or material choice;
- destructive action;
- protected/external state mutation;
- inaccessible dependency or environment;
- conflicting approved sources;
- scope expansion.

The escalation states the exact decision needed and the consequence of each
available governed path; it does not ask the Human to rediscover repository
facts Codex can inspect.

## 10. Runtime Safety

Secrets must not enter tool output, documentation, tests, or code. Client input
never defines trusted scope. Error mapping never exposes protected existence or
internal stack details. AI-generated conclusions remain subject to Human Review
where the Product Bible requires it.
