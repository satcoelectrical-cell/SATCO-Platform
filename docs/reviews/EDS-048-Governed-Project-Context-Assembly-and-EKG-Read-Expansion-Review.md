# EDS-048 Independent Engineering Design Review

## Initial review

**FAIL.** The source-section design, non-atomic observation model, partiality,
closed source/node/relationship allow-lists, one-hop limit, tenant isolation,
provenance and deferred boundaries are coherent. Two Major and one Minor
finding remain before EDS acceptance.

### EDS048-MAJ-01 — graph owner-port closure

The EDS names source-section list ports and one Context Relationship port, but
does not define owner-specific authorized single-node and incident-edge read
ports for every permitted node/relationship family. An IDS could otherwise
invent a generic resolver or reach foreign repositories to implement
`expand_one_hop`.

Required: an exact owner-port matrix covering Project/Workspace, Execution,
Deliverable, Project Control, Engineering Object/Relationship, Engineering
Context/Relationship, Evidence/Supporting File, Technical Report provenance
and Organizational Memory provenance. Every port must have typed closed results
and deterministic call responsibility.

### EDS048-MAJ-02 — node disclosure closure

The phrase “minimum safe owner-approved fields” does not close the node DTO by
kind. It could permit future source DTO growth to leak Human identity,
rationale, body content, private file metadata or other protected fields.

Required: a closed node-projection field matrix. A node projection must not
inherit newly added canonical fields automatically.

### EDS048-MIN-01 — optional Human identity projection

Project Control projection conditionally permits Human attribution through an
undefined safe identity projection. Current PATCH-048 does not require Human
identity nodes or a new identity-authorization source.

Required: exclude Human identity fields from default Context/node/edge
projections; owner detail APIs retain their accepted behavior.

## Initial finding count

Critical: **0**. Major: **2**. Minor: **1**. Initial verdict: **FAIL**.
QG-M1 remains PASS at Architecture level; EDS acceptance is **BLOCKED** pending
focused amendment and re-review.

## Focused amendment

The EDS was amended without changing Architecture-048:

- §5.11 now provides a closed owner-specific EKG port matrix for every node and
  relationship source, including explicit single-node and incident-edge
  responsibilities, closed typed results and no generic resolver;
- §6.1 now fixes the exact safe fields for every node kind and prevents future
  canonical DTO growth from automatically widening graph disclosure;
- default section/node/edge projections now exclude every raw Human identity;
  owner detail APIs retain their accepted attribution behavior.

## Focused independent re-review

**PASS.** `EDS048-MAJ-01`, `EDS048-MAJ-02` and `EDS048-MIN-01` are
**RESOLVED**. The amended EDS gives IDS no permission to invent a generic
resolver, synthetic selector, foreign persistence access or open-ended field
projection. Context/Relationship owner-port prerequisites remain explicit and
fail closed until implemented and verified.

The re-review also confirms:

- ten and only ten Project Context source sections;
- eighteen and only eighteen discriminated node kinds;
- exact canonical relationship families/types and cross-capability edge kinds;
- no Foundation node, Capture/Journal/Interface Commitment node or wildcard;
- truthful non-atomic observation and partial/empty/not-established/
  not-disclosed/unavailable semantics;
- one-hop only, no hidden second-hop, no hidden totals and mandatory bounded
  continuation;
- authorization-before-disclosure and no cross-Organization/Project traversal;
- provenance and Human/external/evidence/derived/contextual/historical
  distinctions;
- no AI, PATCH-049, graph persistence or Track-B authority leakage.

Final findings: Critical **0**, Major **0**, Minor **0**. Observations: the
Architecture observations are closed as explicit EDS/IDS prerequisites, not
implementation assumptions.

## Final verdict

**PASS. EDS Acceptance readiness: READY.** Human EDS Acceptance may grant
IDS-048 design authority only. Implementation, migration and PATCH-049
authority remain ungranted.
