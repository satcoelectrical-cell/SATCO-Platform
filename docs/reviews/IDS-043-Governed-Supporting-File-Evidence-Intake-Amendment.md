# Focused IDS-043 Amendment — IDS043-MAJ-01

Amendment: **COMPLETE**.

- Object identity is now exactly `objects/<256-bit-random-hex>`, written once,
  never moved/overwritten and independent of lifecycle.
- Quarantine/availability is canonical database state, not an object prefix.
- Evidence receives immutable nullable `supporting_file_links_sealed_at`, set
  once on first departure from proposed and never clearable, including after
  withdrawn→proposed.
- Link triggers reject any change when the marker is non-null.
- Migration/aggregate/direct-SQL/withdrawn→proposed evidence is added to the
  implementation plan and verification obligations.

Accepted PATCH/EDS semantics and deferred boundaries are unchanged.
Focused IDS re-review readiness: **READY**.
