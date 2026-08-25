# PATCH-047 — Project Risks, Issues, Decisions & Change Impact

## Document control

| Field | Value |
|---|---|
| Status | FINAL REVIEW / QG-11 / QG-12 PASS; DELIVERY PENDING |
| Registered after | PATCH-046 DONE / CLOSED |
| Architecture / QG-M1 | PASS / ACCEPTED after focused B3 target-identity reconciliation |
| EDS-047 | ACCEPTED / COMPLETE after focused reconciliation |
| IDS-047 | ACCEPTED / COMPLETE after focused reconciliation |
| Implementation authority | Batch 1–4 and final validation exercised; bounded delivery pending |

## Bounded capability

PATCH-047 establishes separate Project-scoped canonical Risks, Issues,
Human Decisions, Changes and bounded Change Impacts. They are engineering
control facts, not generic tickets, tasks, ERM, BPM or autonomous AI facts.

- A Risk is uncertain future engineering impact.
- An Issue is an observed/current engineering problem.
- A Decision is an attributable Human-authoritative engineering/project choice.
- A Change is a Human-recorded or Human-confirmed project/engineering change.
- A Change Impact is a bounded potential or Human-confirmed relationship from
  a Change to an existing canonical Project fact.

PATCH-045 Activity blockers remain Engineering Execution-owned local state. An
Issue may be linked to an Activity but does not create, clear or complete a
blocker; a Risk never blocks an Activity before realization. No relationship
silently mutates Project Foundation, Execution, Deliverable, Evidence or
Supporting File ownership.

## Authority, isolation and exclusions

All operations require trusted Organization and authorized Project/Workspace
context before disclosure. Humans author, accept, resolve, supersede and
confirm according to the accepted design; AI has no decision or impact
authority. Supporting File/Evidence references are reauthorized through their
canonical applications and expose no object-store identity or public URL.

Excluded: PATCH-048 EKG/context expansion, AI inference/approval, generic
ticketing/change management, procurement, authoring of external documents,
semantic search, UI redesign, localization completion and PATCH-048+ work.

## B3-CRIT-01 focused design reconciliation — 2026-08-24

Implementation correctly stopped before Batch 3 manifest creation because the
accepted UUID-only target list included Project Foundation, while
Architecture-044 owns Foundation as a Project-keyed subordinate component with
no independent UUID. The finding is preserved in
`docs/reviews/PATCH-047-B3-Target-Identity-Reconciliation.md`.

The accepted correction removes Foundation as an independently persisted
Change Impact target. V1 supports exactly Activity, Milestone, Deliverable,
Deliverable Revision, Evidence and Supporting File UUID targets through their
canonical application services. Foundation-related change meaning remains in
the Project-scoped Human-authored Change statement/rationale. Architecture,
EDS, IDS and Plan focused re-reviews are PASS; their Human acceptance is
recorded. Existing Batch 1/2 behavior and migration `e04700000001` are
unchanged. Batch 3 is accepted and complete.

## Batch 4 transport and Project control panel acceptance — 2026-08-25

Batch 4 is **ACCEPTED / COMPLETE** after its independent implementation
review, focused remediation and focused re-review. It delivers a thin,
authenticated Project Control transport and one contextual Project panel for
Risks, Issues, Human Decisions, Changes and bounded Change Impacts. The
router obtains trusted actor and Organization context only through its
request-scoped composition root; it owns neither persistence nor policy.

The panel consumes closed results, carries explicit Human rationale for
mutations and Impact confirmation, distinguishes potential from confirmed
Impact, and uses canonical candidate presentation rather than raw internal-ID
entry. Project-path scope is bound again by the application service before a
mutation. Batch 4 introduces neither Foundation target behavior, AI, generic
ticketing, a migration nor PATCH-048 capability.

The focused evidence and preserved remediation chronology are recorded in
`docs/reviews/PATCH-047-Batch-4-Implementation-Review.md`; standing Human
acceptance is recorded in
`docs/reviews/PATCH-047-Batch-4-Human-Acceptance.md`.

## Final validation and delivery readiness — 2026-08-25

Final validation is PASS: the focused Project Control backend suite passed 38
tests; a correctly repository-rooted full backend run passed 1,266 tests and
its one stale runner-path assertion was focused-revalidated after correction;
the final aggregate backend evidence is 1,267 passing tests. The frontend
suite passed 73 tests, and typecheck, production build, static/import, scoped
security, migration upgrade/downgrade/re-upgrade and sole-head checks are PASS.

The final independent review, Human QG-11 and QG-12 delivery-readiness records
are PASS. The exact 70-file PATCH-047 boundary is ready for bounded delivery;
delivery and closure remain pending until their separately verified actions.
