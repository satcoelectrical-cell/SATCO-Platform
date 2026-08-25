# Architecture-047 — Project Risks, Issues, Decisions & Change Impact

## Decision

PATCH-047 owns four distinct Project-scoped aggregates: `ProjectRisk`,
`ProjectIssue`, `ProjectDecision` and `ProjectChange`; `ChangeImpact` is an
immutable child fact of a Change. Every root has immutable UUID identity,
Organization/Project scope, optional same-Project Workspace scope, versioned
current standing, append-only history, attributable Human actor and Audit.
No aggregate transfers authority from its linked canonical fact.

## Lifecycle and authority

Risks move `open → treated | accepted | closed`; Issues move
`open → resolved | closed`; Decisions move `draft → accepted | superseded`;
Changes move `recorded → confirmed | withdrawn`. Only a trusted authorized
Human may make authoritative transitions. A successor Decision is explicit and
does not rewrite the predecessor. A corrected Change is a new root with one
optional predecessor; explicit Human supersession, not successor creation,
withdraws the predecessor from current standing. Risk reopening and Issue
reopening are explicit attributable transitions. An impact is either
`potential` (Human recorded) or `confirmed` (Human confirmed); AI cannot
persist either.

## Relationship boundary

Typed bounded links may reference same-Project Foundation facts, Activities,
Milestones, Deliverables/Revisions, Evidence and Supporting Files only through
their canonical application boundaries. Link creation/retrieval reauthorizes
the target before disclosure. A target must have the linking root's exact
Organization and Project; optional Workspace scope must match or be absent on
the target. Unsupported, inaccessible, cross-Project or cross-Organization
targets fail closed. PATCH-045 retains all blocker state: Issue links are
informational only. PATCH-048 remains responsible for graph/context read
expansion and reasoning.

## Change and impact model

A first-class Change is required: a Decision alone cannot distinguish a
decision from a recorded changed condition. Change Impact contains target kind,
canonical target identity, Human rationale, and potential/confirmed standing;
it makes no automatic downstream mutation. At most 100 deterministic target
links per Change; duplicate target/kind facts are rejected.

## Security and compatibility

Authorization precedes existence, counts, content, history and linked identity
disclosure; inaccessible data returns payload-free protected outcomes. Legacy
Projects receive no fabricated records. Mutations use one UoW, expected version,
idempotency, Audit/outbox and rollback patterns already accepted by PATCH-045/
046. UI is Project-contextual, real-data-only, accessible and structurally
RTL-ready.

## Focused target-identity reconciliation — 2026-08-24

Implementation-time finding `B3-CRIT-01` proved that the earlier relationship
wording incorrectly treated Project Foundation as an independently addressable
UUID target. Architecture-044 remains unchanged: Foundation is a versioned,
one-to-one, Project-owned subordinate component whose canonical selector is the
integer `project_id`; it has no independent canonical UUID identity.

PATCH-047 therefore retains a homogeneous Change Impact target model and
narrows V1 target kinds to independently addressable canonical UUID facts:
`activity`, `milestone`, `deliverable`, `deliverable_revision`, `evidence`, and
`supporting_file`. The target UUID is meaningful only together with its target
kind and the enclosing root's trusted Organization/Project context. This same
closed set governs every PATCH-047 typed canonical link, including
informational Risk/Issue/Decision links; it is not limited to Change Impact.
Each target remains owned and authorized by its canonical application service.

`foundation` and `project` are not V1 Change Impact target kinds. A
Foundation-affecting change remains fully recordable as a Project-scoped
`ProjectChange` with Human-authored statement and rationale. Its Foundation
aspect may be described in that bounded Project-owned narrative, but PATCH-047
does not persist or disclose a synthetic Foundation link, infer a Foundation
identity, or claim an independently authorized Foundation target. If a
specific supported canonical fact is affected, a separate Change Impact may
reference that fact.

For every supported target, authorization precedes persistence and disclosure,
the authorized canonical response must match the Change's exact Organization
and Project, and optional Workspace context must be compatible. A link never
mutates or transfers authority over its target. Unsupported kinds are rejected
as payload-free `invalid_request`; missing, inaccessible, or cross-scope
supported targets remain payload-free protected outcomes; canonical dependency
failure remains payload-free unavailable.

Typed Project/Foundation-aspect links, heterogeneous target selectors, generic
cross-aggregate resolution, graph/context expansion, and broader impact
reasoning remain deferred to PATCH-048 or another separately governed
capability. No new Foundation identity is authorized.
