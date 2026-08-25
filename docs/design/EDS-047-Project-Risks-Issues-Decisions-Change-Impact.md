# EDS-047 — Project Risks, Issues, Decisions & Change Impact

## Domain rules

Each separate root holds bounded statement/context, optional owner, optional
same-Project Workspace and typed canonical links. Risks use bounded qualitative
likelihood/impact (`low|medium|high`) only; priority is a deterministic display
derivation, never false precision. Issues record observed context and explicit
resolution/disposition and may explicitly reopen. Decisions require Human
statement and rationale; acceptance and one-predecessor supersession preserve
immutable historical text. Changes require Human rationale; correction creates
a distinct successor and only explicit Human supersession changes predecessor
current standing. Impacts require a target, rationale and
`potential|confirmed` standing.

## Authority and reliability

Create/update needs Project mutation authority; accept/resolve/confirm/close
uses the same attributable authorized Human boundary, practical for a
one-person company. Each mutation uses expected-version, idempotency, Audit,
outbox, history and one transaction. Failures roll back atomically. Reads and
links reauthorize before disclosure and return closed protected outcomes.

## Integration and UI

Activity/Milestone/Deliverable/Evidence/Supporting File targets are references
only; no foreign repository access and no automatic mutation. Every target
must be same-Organization/same-Project and Workspace-compatible; unavailable or
unsupported targets fail closed. A Project panel
lists authorized current data and contextually creates/updates roots with
explicit rationale. It uses truthful empty/protected/loading/error states,
English presentation strings isolated from canonical semantics and responsive,
accessible structure.

## Deferred

No ticket engine, ERM, enterprise workflow, cross-Project sharing, AI authority
or inference, graph traversal/context assembly, automatic impact propagation,
procurement or PATCH-048 work.

## Focused target reconciliation — 2026-08-24

This append-only amendment resolves `B3-CRIT-01` under the accepted
Architecture-047 correction. The closed V1 Change Impact target kinds are now
exactly `activity`, `milestone`, `deliverable`, `deliverable_revision`,
`evidence`, and `supporting_file`. The same set applies to every PATCH-047 typed
canonical link. Each selector is that canonical fact's UUID; there is no
universal identity independent of target kind.

Authorization dispatch is target-specific and uses only current canonical
application responses:

- Activity and Milestone select exactly one UUID from the bounded, authorized
  Engineering Execution Plan response for the trusted Project.
- Deliverable uses the exact authorized Deliverable read; Deliverable Revision
  selects exactly one revision UUID from its protected canonical history read.
- Evidence uses the exact canonical Evidence read.
- Supporting File uses the exact scoped metadata read with trusted
  Organization/Project and compatible Workspace context.

Every successful response must prove the target's exact Organization and
Project; optional Workspace must be absent or compatible with the linking
Change. The adapter performs deterministic exact-identity selection and returns
no partial candidate, count, ordinal, or target payload. Missing or denied
supported targets are protected, canonical dependency failure is unavailable,
and an unsupported kind is invalid request, all without payload.

Potential impact means only an attributable Human-recorded concern; confirmed
impact requires an explicit authorized Human confirmation. Neither standing
mutates the target. Foundation is not an independently addressable target:
Foundation-related meaning stays in the Project-scoped Change statement and
rationale. The service must not call Foundation persistence, create a synthetic
identifier, or infer a typed Foundation link. Project/Foundation typed-aspect
modeling remains deferred.
