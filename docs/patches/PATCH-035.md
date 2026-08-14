# PATCH-035 — AI Capture Assistant

## Governance Status

| Gate | Status |
|---|---|
| Registration | ACCEPTED |
| Architecture Review / QG-M1 | PASS |
| Human Architecture Acceptance | PASS |
| EDS-035 | ACCEPTED |
| IDS-035 | ACCEPTED |
| Implementation Plan | ACCEPTED |
| IRR-035 | PASS |
| Batches 1–3 | ACCEPTED / COMPLETE |
| Independent Final Review | PASS after focused remediation/re-review |
| Human QG-11 | PASS |
| QG-12 readiness | READY |
| Delivery / closure | NOT YET PERFORMED |

## Capability Boundary

PATCH-035 delivers the minimum provider-neutral AI Capture Assistant. A trusted
authenticated Human may request one ephemeral advisory refinement of one
currently authorized Engineering Experience Capture. The assistant receives a
bounded, minimized projection only after canonical authorization and returns a
structured, attributable, uncertainty-aware proposal for Human review.

The assistant owns no engineering truth, Capture mutation, acceptance,
publication, Technical Report acceptance, Organizational Memory admission,
customer communication, task execution, or autonomous decision authority. A
Human may separately use ordinary governed workflows after reviewing output.

## V1

- one operation: `advise_capture`;
- one exact authorized Capture source;
- one provider call per request;
- ephemeral output; no AI-output database aggregate or conversation history;
- explicit Human instruction and server-trusted actor/Organization context;
- provider-neutral bounded adapter;
- structured observation, assumptions, missing information, confidence,
  limitations, next step, and Capture/provider attribution;
- disablement, refusal, unavailable, invalid, and protected outcomes;
- metadata-only shared Audit records with no prompt, Capture body, or output.

## Deferred

Multiple sources, EKG/Memory context expansion, semantic/vector retrieval,
conversation state, output review/persistence, learning, external/public
publication, customer communications, cross-Organization sharing, autonomous
actions, PLC/code generation, and PATCH-036 Frontend/Dashboard are deferred.

## Dependencies

PATCH-028 Capture, PATCH-029 Journal, PATCH-032 Technical Report, PATCH-033 EKG,
PATCH-034 Organizational Memory, ADR-013, ADR-021, ADR-023, authenticated
Organization context, shared Audit, and current canonical Capture reads.

## Stop Conditions

No accepted source authorization may be bypassed; no provider receives context
before authorization; no implementation may require foreign persistence access
or new engineering authority; no provider credential is committed.
