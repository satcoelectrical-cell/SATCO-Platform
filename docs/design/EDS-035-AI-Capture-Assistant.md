# EDS-035 — AI Capture Assistant

Status: ACCEPTED

## Architecture

The AI Capture Assistant is an application capability, not a canonical
engineering Aggregate. It performs a read-only composition of a trusted actor,
one canonical authorized Capture read, a minimized provider request, and a
structured advisory response. Outputs are ephemeral and acquire no authority
through generation, display, repetition, or later Human use.

## Authority and Context

Only a trusted authenticated actor in a server-derived Organization may call
the operation. The actor must have current canonical read access to the exact
Capture, and supplied Project/Workspace scope must equal the authorized Capture
projection. Authorization and scope equality occur before provider invocation.
The provider has no actor, policy, repository, Session, UoW, mutation, Audit,
or canonical service authority.

## Human Control

The Human supplies the instruction. SATCO never synthesizes intent, approval,
rationale, or acceptance. Trusted server configuration can disable the
capability for the deployment; finer-grained policy is deferred. Output is
labeled advisory and requires separate Human review;
there is no accept/apply operation in V1.

## Provider Boundary

The outward provider port is provider-neutral and accepts only a canonical,
bounded request containing the Human instruction and authorized Capture
projection. It returns structured fields, provider/model/version attribution,
and uncertainty. Provider errors, malformed output, timeout, or missing
configuration fail closed without exception detail.

## Data and Audit

No prompt, source body, or provider output is persisted. Shared Audit records
contain only bounded operation/outcome metadata and digests plus a generated
request identity; they never contain protected plaintext or provider secrets.
Provider calls occur only after an initial Audit attempt can be recorded; a
completion outcome is separately recorded. Audit failure prevents or safely
terminates the request.

## Reliability and Security

Each request permits at most one canonical Capture read and one provider call.
Input/output and arrays are bounded. Protected denial reveals no Capture
existence, identity, scope, content, policy reason, or provider detail. Scope
revocation takes effect on every call. There is no transaction spanning an
external provider and no canonical write.

## Deferred

All PATCH-035 deferred items in the PATCH record remain excluded. IDS-035 owns
exact DTOs, limits, ports, Audit mapping, provider wire format, outcomes,
transport mapping, and verification evidence.
