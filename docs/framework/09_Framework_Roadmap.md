# SATCO Implementation Framework v1.1 — Framework Roadmap

## 1. Purpose

This roadmap governs evolution of the implementation operating system. It does
not assign product PATCH numbers or modify the SATCO product roadmap.

## 2. Version 1.1 Baseline

Version 1.1 consolidates proven execution patterns from PATCH-023 through
PATCH-026:

- documentation-chain readiness;
- bounded prerequisite resolution;
- Foundation/Application-Persistence/Transport sprint sequencing;
- explicit Aggregate commands and inward-owned ports;
- repository/service/API separation;
- trusted Organization context and authorization-before-disclosure;
- Evidence validation and derived visibility;
- optimistic concurrency and idempotency;
- atomic state/Audit/outbox/idempotency Unit of Work;
- Alembic linear-head and clean-database validation;
- focused, dependency, security, and complete regression gates.

## 3. Adoption Phase

Required actions:

1. register Framework v1.1 through the certified Foundation governance flow;
2. use `Implement PATCH-XXX` as the standard runtime invocation after READY;
3. require new EDS/IDS/Plans/IRRs to supply Framework inputs;
4. measure prompt count, blocker recurrence, regression failures, and escaped
   scope changes;
5. preserve Human review and approval evidence.

## 4. Reusable Module Profiles

Framework v1.1 supports profiles without changing Core:

- Engineering: governed objects, relationships, Evidence, lifecycle, review;
- Maintenance: module-owned aggregates linked through approved EKG extensions;
- Technical Procurement: supplier/proposal workflows and accountable decisions;
- Methods & Systems: governed methods, procedures, controls, and evidence;
- Document Management: document identity/storage interfaces under a dedicated
  approved capability, not embedded into unrelated aggregates;
- AI: advisory outputs, traceability, confidence, Human Review, provider
  independence;
- Analytics: authorized read models, bounded aggregation, protected counts, and
  no mutation authority.

Profiles may add checklists only through approved Framework evolution. They may
not weaken universal gates or introduce domain-specific coupling into Core.

## 5. Version 1.x Candidates

Subject to a future documentation PATCH and review:

- machine-readable PATCH/EDS/IDS/IRR metadata;
- automated exact-file-scope validation;
- generated validation command manifests;
- migration-head and schema-drift preflight automation;
- coverage mapping from acceptance criteria to tests;
- standardized final review and validation report templates;
- module profile checklists;
- prompt-reduction and cycle-time telemetry.

These are candidates, not current implementation authority.

## 6. Version 2 Decision Threshold

A major version is required to change governance authority, mandatory states,
approval ownership, artifact types, quality gates, or the meaning of READY,
BLOCKED, DONE, Audit, Human Review, or modular Core extension.

## 7. Success Measures

- at least 75% fewer repetitive execution prompts after READY, measured by the
  protocol below;
- zero implementation starts without READY IRR;
- zero unauthorized file changes accepted;
- zero accidental Alembic branches;
- zero security disclosure regressions accepted;
- all PATCH completion claims backed by focused and full regression evidence;
- blocker resolution returns to the correct owning document;
- new modules integrate without Core forks.

### Prompt-Reduction Measurement Protocol

- Baseline: count Human execution prompts used by completed PATCH-023 through
  PATCH-026 from first implementation authorization through final delivery,
  excluding governance-authoring prompts and responses to external failures.
- Framework sample: use the next three comparable READY PATCHes executed under
  v1.1, counting prompts under the same boundaries.
- Unit: one Human-to-Codex execution instruction or corrective continuation is
  one prompt; automated commentary and tool calls are excluded.
- Result: compare median prompts per PATCH in the Framework sample with the
  baseline median and retain the underlying per-PATCH counts as review evidence.
- Acceptance: the reduction is verified only when it is at least 75% and no
  quality gate, approval, test, review, or delivery authorization was omitted.

## 8. Framework Review Cadence

Review after each three completed implementation PATCHes or after any material
governance, migration, security, or regression incident, whichever occurs
first. Lessons learned propose changes; they do not amend the Framework until
approved.

## 9. Revision History

| Version | Date | Description |
|---|---|---|
| 1.0 | 2026-08-02 | Initial roadmap for Framework adoption and governed evolution. |
| 1.1 | 2026-08-02 | Added governed adoption, runtime applicability, and verifiable prompt-reduction measurement. |
