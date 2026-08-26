# IDS-048 Independent Implementation Design Review

Reviewed IDS-048 against accepted PATCH-048, Architecture-048 and EDS-048 using
targeted current owner-service, schema, router/composition and cursor contracts.
No implementation, test, migration or runtime validation was performed.

## Initial review

**FAIL.** Two Major findings were found before IDS acceptance:

- IDS048-MAJ-01 — typed projection closure: the first draft referred to the
  accepted EDS node-field matrix but did not state exact closed implementation
  DTO fields/optionality for every section and node. That could allow a later
  adapter to leak new owner DTO fields.
- IDS048-MAJ-02 — Engineering Relationship vocabulary closure: the first draft
  named families but did not enumerate every permitted family/type pair in the
  IDS itself. That could lead a later implementation to create an unintended
  wildcard or ambiguous family match.

Critical: 0. Major: 2. Minor: 0. Initial verdict: **FAIL**.

## Focused amendment and re-review

IDS section Focused amendment now closes exact owner result signatures, all
section item DTO fields, all eighteen node DTO fields/optionality and every
Engineering Relationship family/type member. It does not alter Architecture or
EDS semantics.

All ten sources map to named application-service boundaries or an explicit
smallest typed owner-side port. Engineering Context and Engineering Context
Relationship are correctly treated as required typed owner-port additions because
their existing concrete dict/Session services cannot be cross-domain composition
boundaries. No foreign persistence fallback is allowed.

The design closes DTOs/results, states, non-atomic observation, 18 node kinds,
Foundation exclusion, edge owners, one-hop, numeric bounds, last-evaluated
authenticated continuation, authorization-before-projection, cross-scope
non-disclosure, provenance and Human identity exclusion. It introduces no generic
resolver/graph loader, persistence/migration, router authority, AI,
Capture/Journal/Interface Commitment or PATCH-049 behavior.

IDS048-MAJ-01: **RESOLVED**. IDS048-MAJ-02: **RESOLVED**.

Critical: 0. Major: 0. Minor: 0. Observation: 0.

Focused independent re-review verdict: **PASS**. Human IDS Acceptance may grant Implementation Plan-048
preparation only. IRR, implementation, migration and PATCH-049 remain
unauthorized.
