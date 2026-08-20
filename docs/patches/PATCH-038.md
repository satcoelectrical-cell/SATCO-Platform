# PATCH-038 — Customer-to-Capture Engineering Work Bootstrap

## Governance Status

| Gate | Status |
|---|---|
| Human Discovery Acceptance | PASS |
| Registration | REGISTERED |
| Architecture Discovery | COMPLETE |
| Independent Architecture Review | PASS after Human mapping decision and focused re-review |
| QG-M1 | PASS |
| Human Architecture Acceptance | PASS |
| Architecture | ACCEPTED / COMPLETE |
| EDS-038 | ACCEPTED / COMPLETE — Independent Review and Human Acceptance PASS |
| IDS-038 | ACCEPTED / COMPLETE — Independent Review and Human Acceptance PASS |
| Implementation Plan / IRR | ACCEPTED / PASS |
| Batches 1–4 | ACCEPTED / COMPLETE |
| Independent Final Implementation Review | PASS |
| Human QG-11 | PASS |
| QG-12 / delivery | PASS — `b2b7b102be4e957d106b3138dd6f14b5488eb6ff` |
| PATCH status | DONE / CLOSED |

## Product Objective

Deliver the minimum secure real-data workflow that lets an authenticated
engineer progress through:

`Customer → Project → Engineering Workspace → Capture → optional contextual AI assistance → Project / Command Center continuation`.

The PATCH converts the existing predominantly read-oriented web surface into a
real engineering-data-producing workflow. AI remains optional, advisory,
non-authoritative, and subject to the PATCH-035 boundary.

## Registered Boundary

PATCH-038 may provide only:

- Organization-owned Customer listing/selection and creation;
- minimal Customer correction where the accepted operation authority permits;
- Project creation and essential editing using existing Project semantics;
- same-Organization Customer validation without deriving Project ownership
  from Customer;
- Workspace creation/list/selection within an authorized Project;
- Capture creation in trusted Project/Workspace context;
- contextual handoff from the created Capture to the existing AI Capture
  Assistant without manual entry of already-known internal identifiers;
- return/navigation continuity, truthful actionable empty states, protected
  states, accessibility, responsive behavior, and real-data verification.

The frontend is not an authority boundary. Organization and actor authority
remain server-derived, and every Customer, Project, Workspace, Capture, and AI
operation remains independently authorized by its canonical application
boundary.

## Architecture Authority

The governing architecture is
`docs/design/Architecture-038-Customer-to-Capture-Engineering-Work-Bootstrap.md`.
It establishes one explicit immutable owning Organization per Customer for V1,
while preserving independently authoritative Project Organization ownership.

The Human-approved legacy inventory assigns all five existing Customers to the
single active Organization `7e7c9d7a-7693-4f75-9bc5-3ef7bf528281`: Customer
IDs `1`, `2`, `3`, `4`, and `6`. The Human confirms that none requires
multi-Organization ownership. This explicit inventory, rather than Project
topology or database cardinality, is the authoritative migration input.
`AR038-CRIT-01` is resolved by focused Independent Architecture re-review.
Human Architecture Acceptance is PASS. Architecture, EDS, IDS, Implementation
Plan, IRR, Batches 1–4, Independent Final Implementation Review, and Human
QG-11 are accepted/complete or PASS. QG-12 bounded delivery, push, remote
verification, and divergence `0/0` are PASS at delivery commit
`b2b7b102be4e957d106b3138dd6f14b5488eb6ff`. PATCH-038 is DONE / CLOSED; no
later-PATCH authority follows.

## Implementation Delivery Boundary

The delivered V1 is limited to canonical Customer Organization ownership and
the real Customer-to-Capture workflow registered above. Alembic head is
`e03800000001`. Final validation reports 196 focused/adjacent backend tests,
1,078 full backend tests, 42 frontend tests, and PASS for build, typecheck,
security, scope, static/import, diff integrity, and QG-M1. Historical FAIL →
remediation → re-review evidence is retained in the standalone Batch records.
QG-12 delivered exactly 58 authorized files/hunks; remote HEAD equalled local
HEAD with divergence `0/0`, and unrelated local work remained excluded.

## Closure

QG-M1, Human QG-11, and QG-12 are PASS. Batches 1–4 are accepted/complete; all
Critical and Major findings are resolved. Customer transfer/sharing,
Organization administration, broad CRM, Report/Memory mutation UI, autonomous
or persistent AI, semantic/vector search, and all other registered deferments
remain undelivered. PATCH-038 is **DONE / CLOSED**. This closure grants no
authority to PATCH-039.

## Explicit Deferments

- Customer transfer or cross-Organization sharing;
- Customer deletion in the product UI and any new Customer lifecycle;
- Contacts, activities, sales pipeline, CRM automation, billing, or broad
  Customer administration;
- Organization invitation, selection, entitlement, or generic onboarding;
- full Workspace lifecycle/collaborator administration;
- Capture withdrawal/supersession productization;
- Technical Report authoring/revision/acceptance UI;
- Organizational Memory admission/lifecycle UI;
- broad Engineering Context, graph, Evidence, or document-analysis workbench;
- AI persistence, autonomous action, autonomous report creation, semantic or
  vector search, ERP/BPM/task engines, PLC generation, customer communication,
  PATCH-039, and every other unregistered capability.

## Dependencies

- PATCH-025 trusted authenticated Organization context;
- ADR-022 and PATCH-028.1 Project Organization ownership;
- PATCH-028 Capture, PATCH-035 AI Capture Assistant, PATCH-036 web application,
  and PATCH-037 Command Center, all DONE/CLOSED;
- accepted Project and Workspace contracts;
- the Human-accepted complete legacy Customer-to-Organization inventory
  recorded by this PATCH and its architecture artifact.

## Stop Conditions

Stop before EDS if legacy Customer ownership is not completely and explicitly
accepted, if a Customer legitimately requires multiple Organizations, or if
Project ownership would need to be inferred from Customer. Stop before
implementation for client-derived Organization authority, cross-Organization
enumeration, fake production data, direct foreign persistence access, a new
business workflow taxonomy, or any deferred capability.
