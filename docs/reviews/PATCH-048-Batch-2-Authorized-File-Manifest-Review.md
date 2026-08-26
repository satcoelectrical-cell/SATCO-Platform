# PATCH-048 Batch 2 Independent Authorized File Manifest Review

## Verdict

Initial review: **FAIL** — Critical: 0. Major: 1. Minor: 0. Focused re-review:
**PASS** — Critical: 0. Major: 0. Minor: 0. The ten-file allow-list is minimal
and sufficient for accepted Project Context composition plus one thin read route.

## Findings

| Finding | Initial review | Amendment / re-review | Disposition |
|---|---|---|---|
| B2-MAJ-01 | The first draft restated the IDS call-budget phrase as one gate plus nine non-control reads plus four controls, which could be read as fourteen calls. | The manifest now states that the Project/Workspace gate is the Project Basis slot; nine non-control slots (including that gate) plus four controls equals the accepted 13-call maximum. | RESOLVED |
| B2-MAJ-02 | Implementation preflight found that the manifest said eight remaining owner paths even though Context composition needs nine; the Batch 1 Context Relationship adapter had been incorrectly counted as a composition source. | The single authorized `project_context.py` adapter module now explicitly maps nine separately typed named adapters to their public canonical service boundaries. Engineering Context remains the Batch 1 prerequisite; Context Relationship is explicitly excluded from composition. | RESOLVED |
| B2-MAJ-03 | Partial implementation paused because Engineering Object, Evidence and Technical Report services were composed from private infrastructure in other feature dependency roots rather than exposed through three reusable dependency factories. | Targeted review confirmed accepted precedent: EKG locally constructs Engineering Object; Organizational Memory locally constructs Engineering Object, Evidence and Technical Report. The Batch 2 dependency root may perform the same infrastructure wiring while all owner authorization/business logic remains in canonical services and no infrastructure escapes to adapters/composer/router. | RESOLVED |

The corrected manifest modifies only the Batch 1 schema/port prerequisites,
creates one fixed named-adapter module rather than a universal source loader,
and keeps composition in an application service, dependency composition root
and thin router. It includes focused service/security/API evidence and the
smallest cursor-precedent regression.

It excludes EKG one-hop expansion, target reauthorization, persistence,
migration, UoW, cache, UI, AI and PATCH-049. No proposed modified file collides
with unrelated local work; the unrelated dirty Context Relationship service is
explicitly excluded.

## Decision

PATCH-048 Batch 2 Manifest: **ACCEPTED / COMPLETE — RECONCILED**. Batch 2 is
**ELIGIBLE FOR IMPLEMENTATION** under separate authority only.

## Prerequisite reconciliation acceptance

The focused Technical Report safe-summary prerequisite was independently
reviewed PASS and Human accepted. The owner retains authorization and produces
the accepted-only bounded summary; Project Context receives no persistence
access. The accepted manifest adds only the four Technical Report
port/service/service-test/security-test files. Existing in-memory private
Supporting File store use is test-only and does not alter production private
object-store composition. Critical/Major/Minor: 0/0/0.
