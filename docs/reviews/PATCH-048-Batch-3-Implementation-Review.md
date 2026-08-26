# PATCH-048 Batch 3 Independent Implementation Review

## Initial review — FAIL

The independent implementation review inspected the accepted 44-file
reconciled boundary against Architecture-048, EDS-048, IDS-048 and
Implementation-Plan-048. `B3-CRIT-01`, `B3-CRIT-02` and `B3-MAJ-01` remained
resolved. Evidence/Supporting File and Technical Report provenance incidence
were owned, bounded, authorization-preserving reads; no foreign persistence or
migration was introduced.

### B3-MAJ-02 — relation selection and applicable-owner dispatch were incomplete

The one-hop request omitted the accepted closed relationship selection and the
composer invoked all eight relation-owner seams even when the authorized start
kind could not participate in those families. This did not create an observed
disclosure, but it violated the closed request contract, exact cursor binding
and the requirement to probe only applicable canonical owners.

Required remediation: add a typed, distinct, canonically ordered relationship
selection; bind it into the AES-GCM continuation; select only owner readers
applicable to the start kind and requested relation families; preserve the
fixed owner order, target reauthorization and hard bounds.

Initial verdict: **FAIL**. Critical: 0. Major: 1. Minor: 0.

## Focused remediation and independent re-review — PASS

`ExpandOneHopRequest.relationship_kinds` is now a closed tuple of accepted
context relations or validated Engineering Relationship family/type pairs.
Duplicate and noncanonical selections fail as payload-free invalid requests.
The selection is bound into the authenticated continuation. The service uses a
fixed start-kind/owner matrix, filters requested families, and never probes an
inapplicable owner. No depth, recursion, second-hop enrichment, inferred edge,
generic resolver, persistence, migration, mutation, AI or PATCH-049 behavior
was introduced.

Evidence:

- focused Batch 3 and affected canonical-owner suite: **82 passed**;
- adjacent Engineering Object/Relationship, Context Relationship, Execution,
  Workspace, Project and Project Control suite: **69 passed**;
- static/import validation: **PASS**;
- prohibited-pattern/scope validation: **PASS**;
- `git diff --check`: **PASS**;
- Alembic change: **NONE**; sole governed head remains `e04700000001`.

The 18-node dispatch, closed relationship vocabulary, authorized start read,
owner-authorized edge reads, exact target reauthorization, one-hop stop,
deterministic order, 91 candidate/edge/node limits, 100-call ceiling, 512 KiB
response guard, canonical 15-minute continuation and payload-free protected
outcomes remain intact. The Evidence/File reconciliation exposes no storage
key, private URL, Human identity, hidden total or unrestricted provenance.

`B3-MAJ-02`: **RESOLVED**.

Final verdict: **PASS**. Critical: 0. Major: 0. Minor: 0. Batch 3 acceptance
readiness: **READY**.

## Final conformance review — FAIL (`B3-MAJ-03`)

Before final PATCH review, static and behavioral inspection found that four
relation adapters still derived incident candidates from broad canonical list
operations: Execution plan children, Deliverables, Project Controls and reverse
Organizational Memory/source-report incidence. This did not authorize foreign
persistence or create an observed disclosure, but it violated the accepted
owner-specific incident-read contract and could omit a reverse relation beyond
a generic list boundary.

Required remediation: reconcile the manifest append-only; add exact typed,
bounded, owner-authorized incident reads; preserve canonical ownership and
current source reauthorization; prove the adapter never calls generic list
operations for those relations.

Verdict: **FAIL**. `B3-MAJ-03`; Critical: 0. Major: 1. Minor: 0.

## Final focused remediation and independent re-review — PASS

Execution, Deliverable and Project Control now expose typed owner-side incident
pages backed by exact plan/endpoint, FK, predecessor and impact selectors.
Organizational Memory exposes an exact active source-report incidence read and
reauthorizes Memory visibility and the current accepted source before returning
each link. The Project Context adapter calls only those public canonical service
methods; it has no repository, ORM, Session or UoW dependency.

Evidence:

- targeted owner-safe incident slice: **41 passed**;
- complete Batch 3 plus affected owner suite: **110 passed**;
- canonical imports and `git diff --check`: **PASS**;
- migration changes: **NONE**; head remains `e04700000001`.

Generic owner list methods are actively configured to fail in adapter evidence,
while exact typed incident reads succeed. Start authorization, relation
selection, per-target reauthorization, one-hop stop, protected outcomes and all
numeric/cursor bounds remain unchanged. Batch 4 focused behavior remains
applicable.

`B3-MAJ-03`: **RESOLVED**. Final verdict: **PASS**. Critical: 0. Major: 0.
Minor: 0. Batch 3 acceptance readiness: **READY**.
