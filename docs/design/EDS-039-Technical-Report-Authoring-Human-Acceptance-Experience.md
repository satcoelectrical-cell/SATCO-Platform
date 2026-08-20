# EDS-039 — Technical Report Authoring & Human Acceptance Experience

## 1. Status and Authority

Status: **ACCEPTED / COMPLETE**. Independent EDS Review and standing Human EDS
Acceptance are PASS. IDS-039 design authority is granted. This EDS changes no
ADR-023 or PATCH-032 semantic and grants no implementation or PATCH-040
authority.

## 2. Product Boundary

PATCH-039 composes existing capabilities into one Human-led journey:

`authorized Capture → Report draft → draft revision → exact Human acceptance → immutable accepted detail → Project/Workspace/Command Center continuation`.

The Technical Report Aggregate remains the only authority for every Report
mutation. Project, Workspace, and Capture remain canonical dependencies.

## 3. Contextual Reads and Capture Provenance

The product resolves authorized Projects and Workspaces through their existing
APIs. One new read-only Report application boundary may list Capture source
candidates for exactly one positive Project and Workspace. Server-derived actor
and Organization are mandatory. The boundary delegates to the canonical
Capture application service, limits a page to 1–20, returns only `captured`
items, and preserves deterministic canonical Capture ordering.

Each candidate contains a display-safe preview and one ready-to-submit existing
`TechnicalReportProvenanceEntry`: `canonical_material`, `universal_capture`,
material, Universal Capture owner, verified, available, a complete
`CaptureHistoricalBasisV1`, SHA-256 integrity, deterministic entry identity,
bounded attribution, and no client-authored canonical fields. The candidate
count is authorized-only. Any context or dependency denial is protected before
identity, content, count, or digest disclosure.

The normal V1 UI uses one selected Capture entry. Existing PATCH-032 support
for other source classes is neither removed nor productized.

## 4. Authoring and Revision

Creation invokes the existing `CreateTechnicalReportDraft` path with trusted
Organization, selected Workspace/Project, Human-selected purpose, complete
typed content, coherent preliminary qualification, and selected server-composed
Capture provenance. Draft content includes engineering scope, technical
content, assumptions, uncertainty, limitations, conclusions, and
recommendations. Empty collections are valid only where the existing contract
permits them.

Revision is available only on a draft and submits the current expected
Aggregate version, exact current draft revision ID, the complete replacement
content/qualification/provenance, and an explicit Human rationale. It never
patches an accepted record. A conflict refreshes the current authorized detail
and asks the Human to review rather than silently overwriting.

## 5. Human Acceptance and Immutable Detail

Acceptance requires a dedicated review step displaying report identity,
purpose, exact version/revision, complete content, qualification, provenance,
attribution, and the effect of acceptance. The Human supplies an explicit
rationale and confirmation. The request binds expected version and exact draft
revision. The UI neither synthesizes confirmation nor accepts on AI's behalf.

Accepted detail renders only the immutable accepted snapshot and acceptance
record. Editing/revision controls are absent. Standing is communicated by text
and semantics, not color alone. Duplicate/stale acceptance receives the
existing protected/conflict result and never appears successful.

## 6. Authorization, Disclosure, and State

Authentication and active Organization context are server-derived. All
Project/Workspace/Capture/Report references are untrusted. Canonical services
authorize before reads, counts, source details, mutations, or acceptance.
Foreign, absent, and denied records collapse to protected presentation.

The UI supports loading, actionable empty, protected, invalid, conflict,
unavailable, draft, and accepted states. Protected results reveal no identity,
existence, count, source, provenance, ownership, revision, or denial reason.
Navigation/query state is context convenience only and cannot grant authority.

## 7. Continuation, UX, and Non-Functional Rules

Project Capture rows expose a contextual “Create report” action. Reports use
Project/Workspace selectors populated from authorized APIs, detail routes, and
return links. Command Center report rows deep-link to exact authorized details
and distinguish draft from accepted. No invented “awaiting review” state or
count is introduced because PATCH-032 has only draft/accepted lifecycle.

Forms have programmatic labels, validation summaries/status announcements,
keyboard operation, visible focus, and responsive layout. No hard-coded Report,
Capture, count, activity, or provenance appears in production. Reads are
bounded; no high-frequency polling or Organization-wide source search exists.

## 8. Reliability and Deferred Scope

PATCH-032 continues to own concurrency, idempotency, Audit, transactions,
accepted immutability, and error translation. No migration is required.
Report-AI proposals remain deferred unless separately proven fully composed;
Human authoring is complete without AI. Memory mutation, Context/Evidence
workbenches, broad provenance search, publication/export/templates, review
boards, autonomous AI, generic workflow, and PATCH-040 are deferred.

## 9. IDS Obligations

IDS-039 must close the candidate DTO/route, deterministic provenance
construction, bounds and protected mapping; frontend route/state/API/form
contracts; exact revision/acceptance calls; continuation; accessibility;
responsive behavior; performance; scope; and an executable verification matrix.
