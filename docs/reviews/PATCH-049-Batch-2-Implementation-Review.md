# PATCH-049 Batch 2 — Independent Implementation Review

## Reviewed boundary

- backend/app/ports/project_completeness.py
- backend/app/dependencies/project_completeness.py
- backend/app/services/project_completeness_service.py
- backend/app/api/v1/routers/project_completeness.py
- backend/app/main.py
- backend/tests/test_project_completeness_service.py
- backend/tests/test_project_completeness_security.py
- backend/tests/test_project_completeness_api.py

Evidence reviewed: focused Batch 2 validation **18 passed**; read-only PATCH-048
adjacent regression **18 passed**; manifest compliance PASS; static migration
graph e04700000001 → e04600000001.

## Independent findings

### Major

- **B2-049-MAJ-01 — response-byte bound is not enforced over the complete
  serialized closed result.** ProjectCompletenessService.assess serializes
  only CompletenessObservationV1 before wrapping it in
  CompletenessSuccess/CompletenessPartialSuccess. The accepted <=131,072-byte
  limit applies to the transport-visible response, so an observation at the
  limit can yield an over-limit successful response after wrapper/discriminator
  serialization. The implementation must validate the exact outward closed
  result's UTF-8 canonical JSON before return and add focused boundary evidence.
  No leak is established, but the accepted bounded response contract is not
  presently proven.

### Observations

- **B2-049-OBS-01** — the focused and adjacent suites provide real composition,
  scope and closed-outcome coverage, but the response-byte boundary requires
  the Major remediation evidence above.

Critical: **0**. Major: **1**. Minor: **0**.

## Verification status

| Review area | Result |
|---|---|
| public fresh Project Context boundary, all ten sections and one call | PASS |
| trusted actor, server-derived Organization and Project/Workspace boundary | PASS |
| reuse of deterministic 14-rule evaluator and five classifications | PASS |
| missingness safety and partial non-atomic observation | PASS |
| closed outcomes and payload-safe protected/unavailable mapping | PASS |
| router surface and thin registration | PASS |
| AI/EKG = 0; no graph/model dependency | PASS |
| read-only/no persistence/migration/Audit/outbox/idempotency boundary | PASS |
| PATCH-050 firewall | PASS |
| manifest boundary | PASS |
| visible-input, rule/finding/question/checklist/evidence bounds | PASS |
| complete outward response <=131,072 bytes | **FAIL — B2-049-MAJ-01** |

## Verdict

Independent Batch 2 Review: **FAIL**. Batch 2 is not accepted. No Human Batch
2 Acceptance or Batch 3 manifest-preparation authority is granted. Resume only
with governed remediation of B2-049-MAJ-01 inside the accepted Batch 2
boundary, followed by focused validation and independent re-review.

## Append-only remediation and focused independent re-review

B2-049-MAJ-01 remediation changed only the authorized service and focused
service test. The service now constructs the closed
CompletenessSuccess/CompletenessPartialSuccess result first and measures its
complete canonical JSON UTF-8 representation, including the discriminator and
every outward observation field, before returning it. An oversize result maps
to the existing payload-free unavailable outcome.

Focused evidence:

- targeted complete-outward-result vectors: **2 passed**;
- full Batch 2 focused suite: **20 passed**;
- prior PATCH-048 adjacent regression: **18 passed**, still applicable because
  the remediation is downstream result-size enforcement only.

Focused Independent Re-review of B2-049-MAJ-01: **PASS**.

| Re-review verification | Result |
|---|---|
| complete outward success/partial result, not only source observation, is measured | PASS |
| canonical UTF-8 JSON includes discriminator and all outward fields | PASS |
| <=131,072-byte invariant fails closed as unavailable | PASS |
| below/exact boundary behavior is deterministic | PASS |
| protected non-disclosure, exactly-once evaluation and zero AI/EKG remain preserved | PASS |
| no persistence, mutation, migration or boundary expansion | PASS |

B2-049-MAJ-01: **RESOLVED**. B2-049-OBS-01 remains an Observation and is
preserved. Re-review findings: Critical **0**, Major **0**, Minor **0**.

Final Batch 2 Independent Review verdict: **PASS**.
