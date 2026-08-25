# PATCH-047 Batch 4 — Independent Implementation Review

## Scope

This review covers only the accepted Batch 4 Transport/UI boundary. Batches
1–3 remain accepted. No migration, model, foreign persistence, generic
ticketing, AI, PATCH-048, final-validation, delivery or closure work is in
scope.

## Initial review findings and focused remediation

### B4-MAJ-01 — plural transport kind dispatch

**Initial disposition: FAIL.** The accepted mutation endpoints use plural
resource segments (`risks`, `issues`, `decisions`, `changes`), while the
generic transition dispatch initially derived a non-existent plural service
method. A valid accepted transition could therefore fail before application
delegation.

**Remediation:** The router now canonically normalizes only the accepted
singular/plural kind spellings before dispatch. Unsupported kinds remain the
closed payload-free `invalid_request` path.

**B4-MAJ-01: RESOLVED.**

### B4-MAJ-02 — manufactured Impact-confirmation rationale

**Initial disposition: FAIL.** The panel could submit an Impact confirmation
without an explicit Human-supplied rationale, which risked client manufacture
of accepted Human intent.

**Remediation:** The panel now requires a labelled, non-empty `Human
confirmation rationale` before enabling confirmation and sends that exact
value. Focused UI evidence verifies the disabled/explicit path.

**B4-MAJ-02: RESOLVED.**

### B4-MAJ-03 — mutation Project-path binding

**Initial disposition: FAIL.** Some transport mutation paths delegated an
accepted control identity without passing the URL Project selector into the
application-service recheck. The trusted actor/Organization was still
present, but a mismatched Project path was not independently closed before
the mutation.

**Remediation:** Every existing-control mutation now supplies the route
`project_id` to the service. The service checks that the resolved control,
successor, Change or Impact belongs to that Project before mutable-project
authorization or persistence; mismatch is payload-free
`protected_not_found`. Existing callers without a transport path retain the
accepted Batch 1–3 service contracts.

**B4-MAJ-03: RESOLVED.**

## Final independent verdict

**PASS.** Critical: 0. Major: 0. Minor: 0.

### Transport and composition

- `backend/app/dependencies/project_control.py` is the request-scoped
  composition root. It obtains actor and Organization solely from the
  established trusted authentication context and composes the existing Project
  Control UoW/service plus canonical target application services.
- `backend/app/api/v1/routers/project_controls.py` has no ORM, repository,
  Session, UoW or authorization-policy construction. It parses only accepted
  requests, delegates one-for-one and serializes closed results. Protected,
  invalid, conflict and unavailable outcomes contain only their discriminator.
- List, detail and immutable history reads are bounded to 100 and authorize
  Project scope before projection. Existing target authorization remains in
  the application/adapter boundary, before target disclosure or Impact write.

### Project control UI

- The Project-local panel presents separate Risk, Issue, Human Decision and
  Change meanings; an Issue remains distinct from an Activity blocker.
- Change Impact presentation makes `potential` explicitly non-authoritative;
  confirmation is a separately labelled Human action. It neither mutates the
  target nor renders Foundation as a target kind.
- Candidate selection uses existing authorized canonical responses. The panel
  has no generic raw UUID, Organization or Project identity entry, fabricated
  data, AI advice/approval, generic ticketing or new dashboard route.
- Loading, empty, protected, unavailable and success results are neutral and
  accessible. Semantic tabs, labelled fields/history, keyboard-native controls
  and narrow-layout rules are present; existing locale formatting remains used
  for historical timestamps.

## Evidence

- Focused backend transport/service/security and adjacent canonical subset:
  **27 passed**.
- Focused frontend component plus Project Foundation and Execution Plan
  adjacency: **14 passed**.
- Frontend typecheck: PASS. Production frontend build: PASS (1,822 modules).
- Static/import compilation: PASS. Alembic sole head:
  `e04700000001`.
- Router/composition scope inspection: PASS. The router contains no
  persistence or policy imports; the composition root is the allowed location
  for request-scoped infrastructure wiring.
- Protected outcome, Project-path mismatch, canonical target and no-raw-ID
  evidence: PASS. `git diff --check`: PASS.

Existing framework deprecation warnings in the backend focused run are not
Batch 4 behavior failures and contain no new PATCH-047 finding.
