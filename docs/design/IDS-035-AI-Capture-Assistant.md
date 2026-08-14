# IDS-035 — AI Capture Assistant

Status: ACCEPTED

## Executable Contract

```text
CopilotActor { actor_id: int>0, organization_id: UUID }
CopilotScope { organization_id: UUID, project_id: int>0,
               workspace_id: int>0 | None }
CaptureAdviceRequest { capture_id: UUID,
  output_kind: Literal["capture_refinement"],
  human_instruction: trimmed str[1..2000] }
advise_capture(actor, scope, request) -> CaptureAdviceResult
```

`CaptureAdviceResult` is exactly one of:

- `success { proposal: CaptureAdviceProposal }`;
- `refused { refusal_code: unsafe_authority_request | insufficient_context,
  recommended_next_step: str[1..1000] }`;
- payload-free `protected_not_found`;
- payload-free `invalid_request`;
- payload-free `disabled`;
- payload-free `unavailable`.

No outcome contains diagnostics, exception text, hidden counts, or protected
identity other than the authorized success attribution.

## Authorized Source Projection

`AuthorizedCaptureContext` is sourced only from the canonical authorized
`EngineeringExperienceCaptureResponse`:

```text
capture_id UUID                 <- id
organization_id UUID            <- organization_id
project_id int                  <- project_id
workspace_id int | None         <- workspace_id
discipline str | None           <- discipline
engineering_object_id UUID|None <- engineering_object_id
source_kind canonical enum      <- source_kind
original_content str[1..10000]  <- original_content
source_reference str|None       <- source_reference
creator_id int                  <- creator_id
lifecycle canonical enum        <- lifecycle
version int>0                   <- version
updated_at aware datetime       <- updated_at
```

Only `captured` lifecycle is eligible. Superseded/withdrawn/missing/inaccessible
sources return `protected_not_found`. Request Organization must equal actor and
source Organization; Project/Workspace must exactly equal the authorized
source. The Capture application service is called once; direct Capture
repository/ORM/UoW access is forbidden.

## Provider Request and Response

`ProviderCaptureAdviceRequest` contains schema version `1`, request UUID,
output kind, Human instruction, the authorized source projection, and fixed
safety instructions. Canonical JSON uses UTF-8, sorted keys, compact separators,
UUID strings, UTC RFC3339 timestamps, and enum values. Maximum serialized
request is 16 KiB. The provider port is called exactly once.

`ProviderCaptureAdviceResponseV1` is strict and contains:

```text
status: success | refused
suggested_text: str[1..10000] | absent on refused
observations/assumptions/missing_information: ordered tuple[str[1..512], <=10]
confidence: low | medium | high
confidence_rationale: str[1..1000]
limitations: ordered tuple[str[1..512], 1..10]
recommended_next_step: str[1..1000]
refusal_code: accepted enum | absent on success
provider_id/model_id/model_version: str[1..128]
```

Unknown fields, invalid cardinality, unbounded text, authority claims in any
provider-returned textual field, empty limitations, and malformed types make
the provider result unavailable. The adapter rejects provider text containing
a case-insensitive standalone claim
of `approved`, `certified`, `final`, or `automatically accepted`. Provider
errors are never disclosed.

## Success Projection

`CaptureAdviceProposal` repeats the structured provider result, adds
`advisory: Literal[True]`, `generated_at` UTC datetime, and exactly one
`CaptureAttribution { capture_id, version, project_id, workspace_id,
source_kind, updated_at }` plus provider/model/version attribution. Ordering is
provider order after whitespace normalization; duplicates are rejected.

## Human Control and Refusal

`CopilotControl.enabled` is server configuration. Disabled is checked before
canonical reads and provider calls. Explicit unsafe authority instructions
(approve, certify, accept a report, admit memory, send communication, mutate or
execute autonomously) are refused locally using the closed refusal code, with
zero provider calls and zero source disclosure. No Human instruction is
defaulted or rewritten.

## Audit Contract

`CopilotAuditRecorder.record(CopilotAuditRecord) -> None` uses existing
`AuditLog` fields: `user_id=actor_id`, `action` one of
`AI_CAPTURE_ADVICE_REQUESTED|COMPLETED|REFUSED|FAILED`,
`entity="AI_CAPTURE_ASSISTANT"`, `entity_uuid=request_id`, `entity_id=NULL`,
and bounded JSON details containing only schema version, outcome, provider/model
identifiers when known, scope-presence booleans, and SHA-256 digests of
instruction/context/output. No instruction, Capture content/reference,
proposal, rationale, limitation, source identity, provider secret, exception,
or policy reason is stored. Details canonical JSON is <=1 KiB.

The requested record succeeds before provider invocation. The terminal record
is attempted for every subsequent outcome. Initial Audit failure returns
`unavailable` with zero provider calls; terminal Audit failure also returns
`unavailable` and persists no AI output.

## Ports

```text
CaptureAdviceSource.read_authorized(actor, capture_id)
  -> AuthorizedCaptureContext | protected_not_found | unavailable
CaptureAdviceProvider.propose(request) -> ProviderCaptureAdviceResponseV1
CopilotAuditRecorder.record(record) -> None
CopilotClock.now() -> aware datetime
CaptureAdviceService.advise_capture(actor, scope, request) -> CaptureAdviceResult
```

Ports are application-owned. The source adapter uses only the canonical Capture
service. The provider adapter may use HTTPS but no SATCO persistence. Transport
obtains trusted actor/Organization server-side and performs only parsing,
dependency acquisition, invocation, and closed-result serialization.

## Limits and Non-disclosure

- zero Capture/provider calls for invalid, disabled, or locally refused input;
- one Capture read and zero/one provider call otherwise;
- request <=16 KiB; response <=32 KiB; timeout 30 seconds maximum;
- no retries in V1;
- payload-free protected/invalid/disabled/unavailable outcomes;
- no timing equality promise; implementation must not intentionally vary
  protected diagnostics, counts, paths, or response bodies by hidden state.

## Verification Matrix

Evidence must cover exact type closure; canonical field parity; trusted context;
cross-Organization and scope mismatch; authorization before provider call;
revocation; lifecycle ineligibility; unsafe-authority refusal; disabled mode;
one-read/one-call bounds; deterministic canonical JSON; request/response size;
malformed provider output; authority-claim rejection; timeout/error mapping;
metadata-only Audit and Audit failure; attribution; uncertainty/limitations;
payload-free outcomes; thin transport; prohibited routes/imports; Capture and
Technical Report adjacent regressions; full backend regression; static/import;
scope scan; secret scan; and `git diff --check`.

No persistence, migration, idempotency, concurrency, outbox, continuation,
pagination, conversation, learning, frontend, semantic/vector, EKG expansion,
Memory admission, or autonomous behavior is executable V1 scope.
