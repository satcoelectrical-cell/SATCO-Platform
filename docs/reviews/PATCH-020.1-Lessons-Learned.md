# PATCH-020.1 Lessons Learned

## Purpose

This document records implementation and validation lessons from Engineering
Workspace Core without changing its architecture.

## Lessons

### Permanent Identity Simplifies History

One Workspace per Project and Discipline avoids replacement semantics,
ambiguous restoration, and fragmented engineering ownership. Archive and
restore can preserve the same identity.

### Derived Naming Prevents Duplicate Identity

Deriving the display name from Discipline keeps user-facing clarity without
introducing an editable value that competes with the governed identity.

### Current Roles Can Support a Safe Foundation

Project and Workspace ownership, assignment, and membership provide a bounded
authorization model without prematurely expanding persisted RBAC roles.

### Concurrency Must Cover Membership

Collaborator changes affect authorization and therefore increment the same
Workspace version as metadata and lifecycle changes. This prevents silent
overlap between access and engineering-state updates.

### Archive Is Both State and Evidence

Using `archived` as the lifecycle state and `archived_at` as its coupled
timestamp avoids competing representations. A database check makes invalid
combinations impossible.

### Audit Must Follow Domain Meaning

Separate actions for ownership, assignment, membership, lifecycle, archive,
and restore produce clearer evidence than one generic update event.

### Search Authorization Belongs in the Query

Filtering before totals and pagination prevents both record and count leakage.
Post-filtering application results would not be sufficient.

### PostgreSQL Identifier Limits Need Early Validation

The first isolated migration replay identified one foreign-key name longer
than PostgreSQL's 63-character limit. Transactional DDL rolled back the chain,
and a bounded rename resolved the issue without schema change.

Future migration reviews should validate identifier lengths before execution.

### Fresh-Chain Replay Remains Essential

Static syntax and revision inspection cannot replace a complete migration
replay. Fresh-chain validation confirmed ordering, historical compatibility,
metadata parity, and final constraints together.

### Coverage Matrices Expose Boundary Interactions

Enumerating every lifecycle edge and every required persona prevented
representative happy paths from standing in for the full contract. The same
final pass also showed why authorization, totals, pagination, concurrency, and
audit rollback must be asserted together rather than reviewed independently.

### Constraint Tests Must Exercise PostgreSQL Directly

Service validation improves error quality, but it cannot prove authoritative
data integrity. Direct invalid inserts and concurrent creation confirmed that
PostgreSQL independently protects governed values, archive consistency,
positive versions, permanent Workspace identity, and membership identity.

## Closing Lesson

A small domain core still requires identity, authorization, concurrency,
history, audit, and search to agree. Deferring those concerns would increase
future engineering effort rather than reduce it.
