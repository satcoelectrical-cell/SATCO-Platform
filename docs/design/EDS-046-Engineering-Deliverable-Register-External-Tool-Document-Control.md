# EDS-046 — Engineering Deliverable Register & External-Tool Document Control

## Status

**ACCEPTED / COMPLETE.** This EDS implements Architecture-046 without adding
external authoring or generic EDMS authority.

## Domain model

An `EngineeringDeliverable` has immutable `id`, `organization_id`, `project_id`
and creation identity; mutable bounded metadata is title, code, discipline,
type, purpose, responsible Human, target date, optional Workspace, optional
Activity/Milestone link, declared external authority, current revision sequence
and standing. Code is unique case-insensitively per Project. Workspace and
execution references must belong to the same Project and Organization.

A `DeliverableRevision` has immutable id, deliverable id, sequence, external
label, source tool reference, optional available Supporting File asset id,
review standing, issue standing, actor, timestamp and Human rationale. Its
source-file reference is historical and is never a storage key or URL. One
current revision exists per Deliverable; next revision is created with expected
Deliverable/current-revision versions and atomically supersedes its predecessor.

## Operations

V1 operations are `create_deliverable`, `update_deliverable`, `create_revision`,
`transition_revision`, `get_deliverable`, `list_deliverables` and
`list_revision_history`. Mutations use trusted actor, current Project mutation
authority, expected version, bounded Human rationale and idempotency. Reads use
current Project read authority before any lookup disclosure.

Revision transition is deliberately bounded: `draft -> ready_for_review ->
reviewed -> issued`; a current nonterminal revision may be withdrawn; creating
a successor supersedes the previous current revision. `issued` is a controlled
SATCO issue fact, not contractual delivery, external-tool acceptance or a
correspondence/transmittal workflow. Self-review is permitted when the current
Project mutation authority permits it; no enterprise approval chain is implied.

## Reliability and disclosure

The persistence/UoW boundary atomically persists the aggregate mutation,
immutable revision history, AuditLog and idempotency replay record. A minimal
outbox is retained only for the canonical deliverable control event seam.
Mismatched idempotency fingerprint returns closed conflict; replay performs
current authorization before reconstructed success. Version conflicts are
distinct from protected absence and produce no rejection disclosure.

Supporting File authorization is rechecked through its canonical application
boundary. No direct foreign repository/Session access is permitted. An absent,
unavailable or unauthorized representation yields the relevant protected result
without fall back to object storage. Evidence is not linked in V1 because no
accepted canonical Evidence read contract supplies an equivalent immutable
document-control representation; this is an explicit future seam, not a gap.

## UX

The Project Deliverable Register shows only authorized canonical facts. Empty
state says that no deliverables are registered; it does not infer documents
from files. Mutations require explicit Human rationale. No UI manufactures
authority, revision label or external authoring claim.

## IDS obligations

IDS-046 closes DTO fields, enums, field limits, result unions, migration/DB
guards, idempotency payload, audit/outbox shapes, exact canonical Supporting
File adapter, route mapping, pagination bounds and verification matrix.
