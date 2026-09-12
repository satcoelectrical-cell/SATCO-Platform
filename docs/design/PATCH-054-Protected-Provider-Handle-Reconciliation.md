# PATCH-054 Protected Provider Handle Reconciliation

Status: **GOVERNED BOUNDED CORRECTIVE IMPLEMENTATION**

Baseline commit: `6f61bb218021097e89290fe606b504a1e45fd805`

Protected migrations retained unchanged: `e05400000001`, `e05400000002`

Additive corrective migration: `e05400000003`

Corrective parent: `e05400000002`

## Confirmed blockers

`B2-054-MAJ-01` — the accepted IDS requires the runtime role to have no direct
SELECT on `standard_source_snapshots.provider_handle_ciphertext` and identifies
one sole exception: a narrowly granted
`resolve_standard_provider_handle(snapshot_id, organization_id, actor_id,
purpose)` SECURITY DEFINER function.  The first corrective migration correctly
removed direct ciphertext access but did not create that resolver, leaving no
safe Batch-2 resolution path.

`B2-054-MAJ-02` — accepted Batch-2 behavior requires signed opaque handles, but
the frozen ownership row and resulting original Batch-2 manifest omitted
`backend/app/standards/handles.py`.  No substitute location can own that codec
without contradicting the accepted module boundary.

Both are implementation/manifest partitioning defects.  Accepted semantics are
complete; ADR-027, EDS-054, and IDS-054 do not require reopening.

## Narrowest safe database correction

The accepted physical migration sequence is now:

```text
e05400000001 (immutable foundation)
  -> e05400000002 (immutable foundation correction)
  -> e05400000003 (protected provider-handle resolver correction)
  -> future Batch-4 Technical Report integration migration (unassigned)
```

`e05400000003` creates only the accepted fixed-search-path, schema-qualified,
non-dynamic-SQL resolver.  It returns one `bytea` sealed handle or SQL NULL.  It
does not decrypt, deserialize, log, or expose the key version, provider token,
source metadata, object receipt, rights terms, identifiers, counts, or failure
reason.

Resolution requires all of the following in one database statement:

- exact snapshot and Organization match;
- enabled membership plus active actor and Organization;
- available, integrity-verified, handle-backed snapshot shape;
- the snapshot's exact rights binding remains the current tuple head with the
  same version and digest;
- active and currently effective rights; and
- closed `display` or `retrieval` purpose with both the current capability and
  recorded at-use capability true.

The function remains unavailable to PUBLIC and `satco_registry_installer`.
Only `satco_runtime` receives EXECUTE; it still has no direct ciphertext SELECT.
Unauthorized, stale, malformed-purpose, cross-Organization, unavailable, or
integrity-failed inputs return indistinguishable SQL NULL.

The downgrade removes only this access seam and refuses while any protected
provider ciphertext is retained.  It never rewrites or deletes standards data.

## Existing encryption/decryption boundary

The repository already uses application-side AES-GCM with purpose-specific key
derivation and authenticated associated data for opaque encrypted tokens, while
configuration resolves secrets from server-side secret files.  PostgreSQL is
therefore the authorization gate for the stored sealed provider handle, not a
new cryptographic key owner.  Future authorized Batch-2 code in
`backend/app/standards/handles.py` may implement the accepted signed/encrypted
codec; this reconciliation deliberately does not add that HMAC/AES behavior.

## Exact corrective file scope

- `backend/migrations/versions/e05400000003_patch_054_protected_provider_handle_resolver.py`
- `backend/tests/test_standards_migrations.py`
- `docs/design/PATCH-054-Protected-Provider-Handle-Reconciliation.md`
- `docs/implementation/PATCH-054-Batch-2-Authorized-File-Manifest.md`
- focused independent review records created for this reconciliation

No Batch-2 provider, retrieval, object-store, handle-codec, assertion,
service/API, or vector implementation is included.  Batch 3, Batch 4, PATCH-055,
frontend, deployment, and push remain outside authority.

## Reopen and gate disposition

- ADR reopen required: **NO**
- EDS reopen required: **NO**
- IDS reopen required: **NO**
- Accepted historical migrations modified: **NO**
- Additive corrective migration required: **YES — `e05400000003`**
- Batch-2 manifest reconciliation required: **YES — append-only one-path add**
- Full Batch-2 implementation authorized by this record: **NO**
- Next gate: focused Level-C validation and independent reconciliation review
