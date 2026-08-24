# Architecture-046 — Engineering Deliverable Register & External-Tool Document Control

## Status

**ACCEPTED / COMPLETE.** QG-M1 is PASS. This architecture authorizes EDS-046
only and preserves the frozen Commercial V1 roadmap.

## Ownership decision

`EngineeringDeliverable` is a Project-subordinate canonical aggregate. It owns
the enduring engineering work-product control identity, immutable Organization
and Project scope, optional Workspace scope, classification, declared external
authoring authority, responsible Human, due date, current revision pointer and
current control standing. It never owns the underlying authored content, an
object-store object, Evidence fact, Technical Report or Engineering Execution
Plan state.

`EngineeringDeliverableRevision` is an immutable subordinate record. It owns a
monotonic system sequence, opaque bounded external revision label, review/issue
control facts, optional Supporting File representation and immutable source
reference snapshot. Sequence, not label syntax, determines ordering. A new
revision may supersede only the current revision under one authorized
transaction; labels such as Rev 0, A or vendor-specific strings are never
interpreted by SATCO.

## External-tool authority

The declared `external_authority` class (for example `cad`, `eplan`, `etap`,
`spreadsheet`, `document`, `vendor_tool` or `other`) states where authored
content remains authoritative. SATCO can register, classify, retain an optional
Supporting File representation and record review/issue facts. It cannot edit,
generate, certify, or claim authorship of the professional artifact.

## Relationships and truthful execution

One Deliverable may be related to zero or one same-Project Activity and zero or
one same-Project Milestone. The relationship is explanatory: an execution
Activity is not completed, blocked or progressed by a Deliverable state, and a
Deliverable does not become an execution-plan authority. Project completion
criteria may later consume Deliverable facts, but PATCH-046 adds no Project
completion transition.

Supporting File linkage is an optional immutable revision representation. Its
availability and current authorization are rechecked before disclosure; no
private object-store identity or URL is exposed. Evidence remains separately
owned and may be referenced only by a future explicit Evidence integration;
PATCH-046 neither promotes Evidence into document control nor invents a second
evidence lifecycle.

## Lifecycle and protection

Deliverable lifecycle is bounded and Human-governed. Revisions are append-only;
historical/superseded/withdrawn revisions cannot be edited. Human rationale and
expected versions are required for authoritative mutations. PostgreSQL enforces
scope, current-revision uniqueness, sequence, immutable revision history and
valid transition guards. Same-UoW Audit/idempotency and a bounded outbox follow
the established repository pattern. Protected outcomes disclose no identity,
count, revision, file metadata, authority reason or external-tool detail.

## UI boundary

The Project detail surface receives a responsive, accessible, real-data-only
Deliverable Register with truthful empty/loading/protected/error states. It
displays control facts and current-versus-historical revision distinction, and
does not solicit raw tenant/file/object identifiers. UI strings are localizable
and direction-neutral; English remains the current product language.

## Deferrals

No generic EDMS, document authoring, transmittal/correspondence, enterprise
approval board, generated discipline packs, semantic search, AI analysis,
notifications, procurement, FAT/SAT, closeout or PATCH-047+ work.
