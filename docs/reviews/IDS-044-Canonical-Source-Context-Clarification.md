# IDS-044 Canonical Source Context Clarification

Implementation inspection confirmed the accepted Supporting File application
service requires Project plus optional Workspace selector context before it can
authorize exact metadata. The transition DTO therefore carries optional
`source_workspace_id`; it is an untrusted selector that must equal the
canonical authorized response. Evidence behavior and all accepted semantics are
unchanged. Focused independent re-review: **PASS**; no foreign persistence or
new authority is introduced.
