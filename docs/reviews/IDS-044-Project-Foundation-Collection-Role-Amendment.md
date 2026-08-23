# IDS-044 Focused Collection-Role Amendment

## Finding

**IDS044-IMPL-MAJ-01.** The initial IDS required atomic replacement of bounded
scope and completion-criterion collections, including cardinality reduction,
while its generic runtime-role wording denied DELETE on every table. The two
requirements could not both be implemented.

## Amendment

Runtime DELETE is allowed only for `project_scope_items` and
`project_completion_criteria`, the two replaceable current-state collections.
The Project Foundation root, required inputs and immutable stage history retain
DELETE denial. No tenant, history, role, product or deferred boundary changes.

## Focused independent re-review

**PASS. IDS044-IMPL-MAJ-01 RESOLVED.** The minimum privilege now matches the
accepted replace command; scope/criterion changes remain one-transaction,
versioned and Audit-backed. Direct SQL cannot delete roots, input history or
stage history. Architecture/EDS conformance remains PASS.
