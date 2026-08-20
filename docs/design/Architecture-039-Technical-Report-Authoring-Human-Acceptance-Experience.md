# Architecture-039 — Technical Report Authoring & Human Acceptance Experience

## Status

Architecture discovery and Independent Architecture Review are complete.
QG-M1 and Human Architecture Acceptance are PASS. Architecture is ACCEPTED /
COMPLETE. EDS-039 authority is granted; implementation and PATCH-040 authority
are not implied.

## Problem and Bounded Outcome

PATCH-038 ends at an authorized Capture. PATCH-032 already owns the complete
Technical Report Aggregate, but the product exposes only summary reads and
manual Project/Workspace identifiers. PATCH-039 productizes, without
redesigning, the complete Human workflow from Capture through exact acceptance.

## Canonical Ownership

The existing Technical Report Aggregate exclusively owns draft content,
purpose, qualification, provenance, revision, lifecycle, concurrency,
acceptance, immutable accepted snapshot, lineage, Audit, and idempotency.
Capture remains owned by Universal Engineering Capture. Project and Workspace
retain their existing ownership. The frontend owns no engineering state or
authority.

## Capture Provenance Composition

The normal workflow uses only currently authorized `captured` Capture sources.
A bounded application-owned composition read lists at most 20 Captures in an
exact authorized Project/Workspace and returns a complete canonical
`canonical_material` / `universal_capture` provenance entry. The server derives
Organization, historical Capture basis, deterministic entry identity,
integrity digest, verification/availability, and attribution. The browser
selects the result; it does not author canonical history or integrity data.

Authorization precedes candidate identity, count, content, digest, and
provenance disclosure. Foreign, absent, withdrawn, superseded, or scope-
mismatched Captures fail closed. The Report service retains its existing final
historical-basis authorization/integrity checks on create, revise, and accept.

## Human Workflow and Authority

The engineer selects a real Project, Workspace, and Capture; supplies purpose,
content, preliminary qualification, and required Human rationales; creates and
revises a draft; reviews exact version/revision/content/qualification/
provenance; and explicitly confirms acceptance. Acceptance invokes the
existing exact-version command. Stale version/revision conflicts are visible
without disclosing protected resources. Accepted content is read-only and
unmistakably authoritative and immutable.

AI remains optional and advisory. Incomplete production Report-AI composition
is deferred and does not block Human authoring.

## Product Composition and Quality

The Reports surface resolves authorized Project and Workspace choices rather
than accepting manually typed IDs. Contextual links from Project Captures and
Command Center reports retain navigation context but confer no authority.
Loading, empty, protected, unavailable, conflict, draft, and accepted states
are truthful and API-backed. Forms are semantic, keyboard-operable, labelled,
responsive, and announce errors. Candidate/list reads are bounded and no
polling or fake production state is introduced.

Memory mutation, broad provenance search, Context/Evidence workbenches,
publication/export/templates, approval boards, autonomous AI, and PATCH-040
remain deferred.
