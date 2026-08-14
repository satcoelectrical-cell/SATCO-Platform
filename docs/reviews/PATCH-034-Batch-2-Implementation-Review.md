# PATCH-034 — Independent Batch 2 Implementation Review

## Review Control

| Field | Value |
|---|---|
| Batch | Batch 2 — Credential and Persistence Foundation |
| Steps | S03–S04 |
| Initial review | FAIL |
| Initial findings | `B2-MAJ-01..05`, `B2-MIN-01` |
| First focused remediation/re-review | FAIL — validator/evidence gaps remained |
| Second validator remediation/re-review | FAIL — nested provenance gap remained |
| Final nested-provenance remediation/re-review | PASS |
| Final verdict | PASS |
| Traceability record | Reconciled 2026-08-14; no new review performed |

## Preserved Findings

- `B2-MAJ-01`: JSON/outbox/idempotency validators did not reject every invalid
  timestamp, UUID, discriminator, type/nullability, oversize, and prohibited
  payload using strict SQL Boolean semantics.
- `B2-MAJ-02`: terminal root/history actor, time, reason, standing, and version
  parity was not fully DB-enforced.
- `B2-MAJ-03`: deterministic UUID lock ordering for supersession was missing.
- `B2-MAJ-04`: runtime role verification did not fail closed on schema,
  signature, trigger/table, owner, grant, or denial drift.
- `B2-MAJ-05`: schema, direct-SQL, concurrency, reuse, locking, role-drift, and
  downgrade/re-upgrade evidence was incomplete.
- `B2-MIN-01`: ORM integer/FK/nullability/index/constraint metadata did not
  completely match the DB contract.

## Preserved Remediation and Re-review Sequence

The first remediation closed DB coherence, locking, role drift, and ORM parity,
but `B2-MAJ-01` and `B2-MAJ-05` remained open for strict-Boolean/timestamp and
evidence completeness. The next remediation added calendar-valid timestamps,
required-field NULL rejection, and the schema/constraint matrix. Its re-review
identified the remaining nested `provenance_entries[]` SQL three-valued-logic
path and evidence whose digest mismatch could mask validator behavior.

The final remediation made every required nested provenance predicate strict
Boolean and recomputed digest-coherent malformed manifests. Final evidence:

```text
Targeted nested validator: 1 passed
Batch 2 focused: 34 passed
Alembic head: e03400000001
B2-MAJ-01: RESOLVED
B2-MAJ-02: RESOLVED
B2-MAJ-03: RESOLVED
B2-MAJ-04: RESOLVED
B2-MAJ-05: RESOLVED
B2-MIN-01: RESOLVED
Final verdict: PASS
```

## Final Decision

Batch 2 Independent Review: PASS after the preserved FAIL/remediation/re-review
chain. No foreign persistence or Batch 3 behavior entered the boundary.
Established Human Acceptance is recorded in
`docs/reviews/PATCH-034-Batch-2-Human-Acceptance.md`.
