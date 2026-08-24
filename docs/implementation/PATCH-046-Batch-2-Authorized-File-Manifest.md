# PATCH-046 Batch 2 — Authorized File Manifest

**Accepted / complete.** Canonical command/reliability layer only.

Authorized CREATE/MODIFY: Deliverable authorization adapter, UoW, service,
repository/port contract updates and focused service/security/transaction tests.
Responsibilities are trusted Project context, create/update/revision/transition,
expected-version locking, idempotency, Audit/outbox, rollback and canonical
Supporting File rechecks before linked-file mutation or disclosure. No broad
reads/pagination, router, UI, direct Supporting File repository access or
external authoring is authorized. Stop if current Project/Workspace authority
cannot be consumed through the established application boundary.
