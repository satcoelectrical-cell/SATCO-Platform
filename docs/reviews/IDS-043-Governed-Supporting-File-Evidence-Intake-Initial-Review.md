# Initial Independent IDS-043 Review — Historical FAIL

## Verdict

**FAIL. Critical/Major/Minor: 0/1/1.**

## Finding preserved

- **IDS043-MAJ-01 — immutable object/link closure.** The initial draft used
  lifecycle-specific `quarantine/` and `available/` object-key shapes while
  also declaring storage identity immutable, without defining a safe move or
  second identity. It also guarded Evidence link immutability by current
  lifecycle alone even though accepted PATCH-027 permits withdrawn→proposed,
  which could reopen a formerly sealed link set. Implementation would have had
  to invent key mutation and historical-link semantics. **Initial disposition:
  BLOCKING.**

- **IDS043-MIN-01 — external integration evidence.** Real production object
  data-plane/scanner evidence is unavailable locally and must be classified as
  an external prerequisite. **Initial disposition: downstream obligation.**

## Required amendment

Use one immutable opaque object identity across lifecycle and introduce a
durable one-way Evidence link-sealing marker that cannot be cleared by later
lifecycle transitions or direct SQL. Update the plan and verification matrix.

IDS acceptance was **BLOCKED** at this initial review.
