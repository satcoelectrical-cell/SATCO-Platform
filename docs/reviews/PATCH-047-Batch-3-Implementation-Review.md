# PATCH-047 Batch 3 — Independent Implementation Review

## Scope

This review covers only Batch 3 Change and Change Impact implementation after
the accepted `B3-CRIT-01` Foundation-target reconciliation. Batch 1–2 remain
accepted. Batch 4, transport/UI, PATCH-048, migration changes and foreign
persistence access are outside this review.

## Initial review finding

### B3-MAJ-01 — closed unsupported-target outcome

**Initial disposition: FAIL.** The target adapter originally translated an
unsupported direct discriminator (including `foundation`) to
`protected_not_found`. IDS-047 requires a payload-free `invalid_request` for
an unsupported kind and reserves `protected_not_found` for a supported target
that is missing, denied or scope-mismatched.

### Focused remediation and re-review

The adapter now raises the closed `TargetInvalid` boundary signal for an
unsupported kind and the application service translates it to the payload-free
`Invalid` result. `TargetProtected` remains the sole translation for an
inaccessible supported target; `TargetUnavailable` remains payload-free
`Unavailable`. Focused integration and security evidence proves both branches.

**B3-MAJ-01: RESOLVED.**

## Final independent verdict

**PASS.** Critical: 0. Major: 0. Minor: 0.

### Change and Impact behavior

- Change identity, Organization/Project ownership, Human attribution,
  append-only history, correction-as-successor and explicit supersession are
  preserved. Successor creation does not rewrite or supersede its predecessor.
- Potential Change Impact creation remains non-authoritative and has no target,
  execution, Deliverable, Evidence, Supporting File or Foundation mutation.
  Confirmation is an explicit Human operation.
- Same-UoW persistence stages Change history, idempotency, Audit and outbox;
  injected Audit/outbox/idempotency failures roll back primary facts. Row locks,
  expected version checks and deterministic UUID lock ordering provide a single
  winner for the focused successor, duplicate-impact and confirmation races.

### Canonical target boundary and non-disclosure

Only `activity`, `milestone`, `deliverable`, `deliverable_revision`, `evidence`
and `supporting_file` are accepted. The adapter uses only their owning
application-service calls, constructs the trusted actor/scope DTOs required by
those boundaries, and performs no foreign repository, ORM, Session or UoW
access. Target selection is exact and project/Organization/workspace compatible
before an Impact is persisted. Unsupported kinds are `invalid_request`;
missing, denied and scope-mismatched supported targets are payload-free
`protected_not_found`; dependency failure is payload-free `unavailable`.

### Evidence

- Focused Batch 3 suite: **28 passed** — contracts, service, transaction,
  security and six-kind integration evidence.
- Adjacent bounded regression: **15 passed** — Project Control repository and
  migration plus Execution, Deliverable, Evidence and Supporting File service
  suites.
- Static/import compilation: PASS.
- Alembic sole head: `e04700000001`.
- Scope and prohibited-pattern inspection: PASS. No router, transport,
  frontend, AI, Foundation target, generic resolver, migration or foreign
  persistence leakage was found.
- `git diff --check`: PASS.

The test run retains existing framework deprecation warnings and the known
fixture cleanup warning from the real PostgreSQL concurrency probe; neither is
a Batch 3 behavioral failure or changes production semantics.
