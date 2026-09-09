# PATCH-052 Batch-3 Independent Implementation Review

## Verdict

**FAIL / NOT ACCEPTED / INCOMPLETE**

Critical: **0**

Major: **1**

Minor: **0**

Observation: **1**
Blocking findings: **B3-052-MAJ-01**

## Review method

The review compared the actual source and focused PostgreSQL/frontend evidence
against PATCH-052, Architecture-052, ADR-025, EDS-052, IDS-052,
Implementation-Plan-052, and the accepted Batch-1/2 evidence. It inspected
domain semantics, authority order, provenance, cross-Workspace behavior,
transaction ownership/retry/replay, resource limits, Report/Memory boundaries,
frontend authority, migration scope, and prohibited later capability.

## Passing findings

The exact 8/5/5/4/4/5 Instrumentation catalogs, primary-Identifier kinds,
Object Context mappings, Deliverable inputs/representations, relationship
tuples, and five static bounded rule identities match the accepted tables.
Instrumentation mutations use the Batch-2 UoW and configuration-first guard;
authority precedes replay disclosure; provenance is server-derived; only the
accepted retry SQLSTATEs are retained. Cross-Workspace I/O linking authorizes
both Workspaces before endpoint locking and rejects cross-Workspace loop/panel
targets. Control execution, AI authority, sizing/selection, document/code
generation, Memory writes, Batch 4/5, PATCH-053, and a new migration were not
introduced.

The compiled panel consumes only its server-supplied effective state and hides
actions for historical, unavailable, or indeterminate states. Generic Report
V2 construction/acceptance and Memory admission boundaries remain unchanged.

## B3-052-MAJ-01 — Context/Evidence declaration identity and API contract absent

**Classification: Major / blocking.**

The frozen contract requires direct authorized Context projections keyed to
exact declarations, exact selected Evidence per Deliverable, declaration-match
validation, same-revision Human-review Evidence, two named response DTOs, and a
closed transition request. The accepted artifacts never enumerate the fields
of those DTOs. The actual `engineering_contexts` and
`engineering_context_subject_references` tables store source kind and Object
subject, but no package `context_kind_id` or declaration binding. The
`evidence` table likewise has lifecycle/source metadata but no requirement or
declaration binding.

Using free-text `source_key`, `source_reference`, `supported_fact`, ordering,
or type-string inference as authority would violate the no-free-text-fallback,
no-fabricated-provenance, and exact-declaration requirements. Trusting a client
map without a server-verifiable binding would not meet "declaration match."
Adding a binding column/table could require `e05200000002`, which Batch-3 is
explicitly forbidden to create without separate authority.

Required resolution: reconcile Architecture/EDS/IDS with an exact DTO field
order and an authoritative declaration-binding representation. If the result
needs persistence beyond `e05200000001`, authorize and review the smallest
additive migration separately. Then complete Context/readiness/issue APIs,
PostgreSQL authorization/partiality/revision-binding/query-plan evidence, full
affected and broad regression, and a new independent review.

## Observation

`B3-052-OBS-01`: the long-running local backend container has an unrelated
stale runtime-role credential. Ephemeral tests against the positively verified
disposable database passed without changing or exposing credentials.

## Governance disposition

PATCH-052 Batch 3: **NOT ACCEPTED / INCOMPLETE**.

Batch 4: **NOT ELIGIBLE / NOT AUTHORIZED**.

PATCH-052: **REGISTERED / OPEN**.
PATCH-053: **NOT STARTED / NOT AUTHORIZED**.

The exact next Human decision is whether to authorize design/IDS
reconciliation of B3-052-MAJ-01. This review does not grant migration or Batch-4
authority.
