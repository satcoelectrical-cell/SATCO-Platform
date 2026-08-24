# PATCH-046 — Engineering Deliverable Register & External-Tool Document Control

## Document control

| Field | Value |
|---|---|
| Status | QG-12 DELIVERY READINESS PENDING |
| Architecture / QG-M1 | PASS / ACCEPTED |
| EDS-046 | ACCEPTED / COMPLETE |
| IDS-046 | ACCEPTED / COMPLETE |
| Implementation plan | ACCEPTED / COMPLETE |
| IRR-046 | PASS |
| Registered after | PATCH-045 DONE / CLOSED |

## Purpose

PATCH-046 creates the bounded canonical engineering-deliverable control layer
for a Project. It records deliverable identity, immutable revision history,
truthful current standing, responsible Human, target date, optional same-Project
execution relationship, and an optional governed Supporting File representation.
It does not author CAD, EPLAN, PLC, DCS, spreadsheet, word-processing or other
external-tool content.

## Accepted boundary

- A Deliverable is a Project-owned engineering work-product control record, not
  a file, Evidence record, Technical Report, generic EDMS item or task.
- A Deliverable Revision is immutable. It has a system-ordered sequence and a
  bounded Human-authored external revision label; labels are not parsed or used
  as universal revision ordering.
- External professional tools retain authoring authority. SATCO records only
  the declared external authoring authority and governed control facts.
- Current revision changes only through an authorized Human next-revision
  operation. The previous revision becomes historical/superseded. Existing
  revision facts and Supporting File references remain preserved.
- Deliverables are Organization/Project scoped, optionally Workspace scoped,
  and may reference a same-Project Activity or Milestone. These references do
  not change execution-plan authority or complete an Activity/Project.
- A Supporting File is only an optional governed representation. It is never
  silently promoted to a Deliverable, and a Deliverable never owns file storage.
  Evidence is not a document-control substitute and is not promoted implicitly.
- Reads and mutations require trusted actor/Organization context, current
  Project visibility, authorization before disclosure, and payload-free
  protected outcomes.

## Lifecycle and authority

Deliverable standing is `planned`, `in_preparation`, `ready_for_review`,
`reviewed`, `issued`, `withdrawn` or `cancelled`. A revision standing is
`draft`, `ready_for_review`, `reviewed`, `issued`, `superseded` or `withdrawn`.
The exact allowed transitions, Human rationale, expected-version and audit
requirements are defined by EDS-046/IDS-046. A review or issue record is a
bounded control fact, not an enterprise approval chain, contractual acceptance
or external transmittal system.

## Exclusions

No generic EDMS, file storage, CAD/EPLAN replacement, transmittal/correspondence,
PATCH-047 risks/issues/decisions, authoring/acceptance of Technical Reports,
Organizational Memory mutation, AI approval, semantic/vector search, frontend
dashboard redesign, localization completion, procurement, FAT/SAT or PATCH-047+
capability is introduced.

## Governance trail

Architecture and QG-M1, EDS, IDS, implementation-plan and IRR independent
review/acceptance records are in `docs/reviews/`. Batches remain subject to
their individual manifests, review and Human acceptance before the next batch.

## Final implementation readiness

Batch 1–3 are accepted/complete. B046-ENV-01 is resolved: the original
performance failure was reproduced only in the unrelated dirty worktree and
passed in the clean PATCH-045-plus-PATCH-046 isolation environment. Final
validation, independent final review and Human QG-11 are PASS. Delivery is
pending QG-12; PATCH-046 is neither delivered nor closed by this record.
