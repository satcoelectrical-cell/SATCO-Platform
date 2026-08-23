# Focused Independent IDS-043 Re-review — Governed Supporting File Evidence Intake

## Verdict

**PASS. IDS043-MAJ-01: RESOLVED. New Critical/Major/Minor: 0/0/0.**

## Independent review

The amended migration design is parented from the verified current head and provides exact
types, state checks, cross-row scope/link guards, immutability triggers and
runtime/schema-owner separation. Direct SQL cannot create incomplete Assets,
promote uncertain scans, mutate bytes metadata or link incompatible resources.
The durable Evidence link-sealed timestamp prevents the existing
withdrawn→proposed transition from reopening a previously sealed file-link set.

The upload saga closes all partial-state paths without pretending object-store
and PostgreSQL atomicity. Reservations are explicitly noncanonical; object
success/DB failure and DB reservation/object failure are recoverable. Storage
keys are unpredictable, private and absent from every public/log/Audit shape.
Conditional create, one immutable `objects/<random>` identity and role grants
prevent lifecycle key mutation, overwrite/list/public access.

The scanner protocol binds attempt, exact object version and digest. Timeout,
unavailability, stale result and mismatch cannot promote. The scanner has no
engineering authority. The reconciler walks database reservations, not object
listings, and cannot create or promote Assets.

Evidence owns the link command and version increment. Technical Report uses a
canonical application collaborator and same-Session lock for the final Asset
recheck, not direct repository ownership. Evidence V2 is closed and leaves V1
immutable/readable. Supporting File is nested under Evidence provenance rather
than becoming an unauthorized fifth Report source. Memory gains no byte store.

Authorization, protected results, bounded last-evaluated pagination,
attachment-only streaming, filename/MIME protections and UI real-data rules are
exact and executable. Available/withdrawn bytes have no V1 purge path, so the
accepted-report historical basis cannot be erased by an ungoverned retention
operation.

## Preserved initial-review disposition

The historical Initial Independent Review remains FAIL. IDS043-MAJ-01 is
resolved by the immutable single object identity and durable one-way Evidence
link-sealed marker. No accepted architecture/EDS semantic changed.

## Remaining finding

- **IDS043-MIN-01 — external integration evidence.** Local repository truth has
  no production object-store data-plane credential or malware scanner. Fake
  adapters and protocol tests can establish implementation conformance, while
  IAM, TLS, real scan and object-inclusive recovery evidence must remain
  conditional external gates. **Disposition: RESOLVED in the verification
  matrix and IRR prerequisite classification.**

No implementation must invent a material database, security, transaction,
authorization, pagination, UI or recovery semantic. Architecture/EDS
conformance: **PASS**. Acceptance readiness: **READY**.
