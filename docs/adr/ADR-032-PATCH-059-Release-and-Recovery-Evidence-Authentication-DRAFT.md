# ADR-032 — PATCH-059 Release-Sequence and Recovery-Set Evidence Authentication

## Status

**ACCEPTED BY HUMAN ARCHITECTURE AUTHORITY — 2026-10-03**

The Human Architecture Authority explicitly accepted all six decisions in this ADR on 2026-10-03. This architectural acceptance does not authorize workflow edits, signing, release approval, recovery-set schema implementation, deployment, release, PATCH-059 closure or PATCH-060. A separately reviewed implementation-plan amendment must be approved before implementation.

## Date

2026-10-03

## Context

The independent PATCH-059 Batch E security review identified two Major gaps:

- SEC-E-MAJ-05: the local release-sequence manifest is structurally checked,
  but is not cryptographically bound to PATCH-058 protected signing and final
  Human release approval for the PATCH-059 candidate;
- SEC-E-MAJ-06: the recovery-set manifest contains ordinary hashes but is not
  authenticated, so a backup-storage writer can replace artifacts and rewrite
  their hashes while preserving the separately signed commercial Recovery
  Anchor state.

The accepted architecture already supplies the governing authorities:

- ADR-031 and PATCH-058 own immutable release identity, protected signing,
  signature verification, the release dossier and distinct Human release
  approval;
- Architecture/EDS/IDS-059 require `release_sequence` to come from
  server-verified PATCH-058-compatible evidence;
- IDS-059 and the Batch E recovery operations design establish a separate
  Ed25519 Recovery Authority, public recovery trust store, revocation behavior
  and a domain-separated signed Recovery Anchor.

The current physical implementations do not close those contracts. The only
reviewed signing workflow is hard-bound to `refs/heads/patch-058`, its signer
identity names that workflow/ref, and it deliberately produces a pending
dossier rather than final release approval. The recovery-set JSON is not
signed. Extending either signed evidence surface crosses the Governance Model
ADR threshold because it changes durable security and release/recovery rules.

## Proposed decision 1 — reuse PATCH-058 release authority

PATCH-059 shall not create a new release signer or approval authority. It shall
extend the accepted PATCH-058 foundation through a PATCH-059-specific protected
workflow and versioned evidence contract.

The protected flow shall:

1. build and qualify a clean exact PATCH-059 source revision and immutable
   backend, frontend and migration artifacts;
2. create a closed versioned release manifest containing a positive
   `release_sequence`, exact source SHA, artifact digests, Alembic head,
   configuration-schema identity and exact dossier/provenance references;
3. include that release manifest as a designated artifact/subject in
   provenance, signature and verification evidence;
4. execute signing only under the existing Human-controlled release-signing
   policy and protected GitHub Environment, with a workflow/ref identity
   explicitly allowlisted for PATCH-059;
5. produce a distinct attributable Human release-approval record bound to the
   exact release ID, source SHA, release-manifest digest, artifact digests,
   `release_sequence`, exceptions and decision time;
6. run a separate protected finalization step after that approval to verify the
   full dossier and cryptographically bind the final approval plus release
   manifest; pending approval can never produce a release-ready bundle;
7. provide an offline deployment-verification bundle. A pinned verifier shall
   check the expected repository, OIDC issuer, exact authorized workflow/ref,
   source SHA, artifact subjects, manifest digest, sequence and final approval
   before deployment. Runtime shall hash the exact verified manifest and
   require its separately deployed expected digest; a shape-valid local file
   alone is never authority.

The workflow shall be narrowly PATCH-059-bound. A generic arbitrary-ref signer
is prohibited unless separately reviewed and Human accepted, because it would
broaden signer policy beyond the current authority.

### Release alternatives

1. **Recommended: PATCH-059-specific extension using the existing protected
   signer and dossier authority.** This minimizes authority change while making
   branch/workflow identity and `release_sequence` explicit.
2. Convert the PATCH-058 workflow into a reusable multi-release workflow.
   Potentially maintainable, but rejected for this remediation unless separately
   approved because parameterized refs/artifacts can broaden signer authority.
3. Trust a deployment environment variable plus hash-shaped references.
   Rejected: it is the current vulnerability and is not Human approval.
4. Sign release sequence with the entitlement issuer or Recovery Authority.
   Rejected: both are the wrong authority and violate accepted separation.

## Proposed decision 2 — authenticate the recovery set with existing Recovery Authority

The recovery-set manifest shall use the existing dedicated Recovery Authority;
no release key, entitlement issuer key or new shared-secret MAC authority shall
be introduced.

Define `satco.commercial-recovery-set/v1` as a closed Ed25519 envelope:

```json
{
  "schema": "satco.commercial-recovery-set/v1",
  "algorithm": "Ed25519",
  "key_id": "recovery-2026-a",
  "payload": {
    "set_id": "uuid",
    "deployment_id": "deployment-a",
    "release_sequence": 1,
    "alembic_head": "e05900000001",
    "started_at": "UTC timestamp",
    "finished_at": "UTC timestamp",
    "artifacts": [],
    "anchor": {"filename": "basename", "sha256": "lowercase hex"},
    "object_cutoff": "UTC timestamp",
    "object_count": 0,
    "configuration_schema": "bounded identity"
  },
  "signature": "unpadded-base64url"
}
```

Each artifact entry shall bind a closed role, safe basename, SHA-256 and byte
length. Roles shall be unique and must include the encrypted database dump,
sealed object inventory/object archive as applicable, and archived Recovery
Anchor. Names containing path separators, `.`/`..`, absolute paths, NUL or
noncanonical basename forms are invalid.

Signed bytes shall be:

```text
ASCII("SATCO-COMMERCIAL-RECOVERY-SET-V1\0") || RFC8785_JCS(unsigned_envelope)
```

The recovery environment shall use the same hash-pinned RFC 8785 implementation
reviewed for PATCH-059 and the existing recovery public trust store/key
lifecycle. The manifest signature and revocation status shall be verified
before `age`, `psql`, `pg_restore`, database inspection or any target mutation.
All later digest, deployment, sequence, head, cutoff, Anchor and exact-state
checks remain mandatory; authentication does not replace them.

Backup ordering remains: lock state -> dump/inventory -> construct candidate
Anchor -> construct and sign recovery-set envelope -> archive/immutably retain
the complete set -> promote the candidate Anchor. The final signed envelope is
immutable. Any changed artifact requires a new set ID and signature.

Existing unsigned recovery sets are not silently grandfathered. Human recovery
authority must choose either to re-seal a verified historical set during an
attributable offline ceremony or to mark it ineligible for production restore.

### Recovery alternatives

1. **Recommended: sign the recovery-set envelope with the existing Recovery
   Authority.** This preserves separation and creates no new trust root.
2. Add all backup digests to Recovery Anchor v2. Rejected for this remediation:
   it couples runtime anti-rollback state to backup inventory and requires a
   more disruptive Anchor migration.
3. Use a new independently custodied MAC. Rejected: it creates a shared-secret
   authority and distribution/revocation problem without an accepted basis.
4. Use PATCH-058 release signing. Rejected: backup creation is an operational
   recovery action, not a software release.

## Dependencies, migration and operations

- No database migration is proposed.
- Release implementation requires a PATCH-059-specific protected signing and
  finalization workflow, versioned manifest/dossier schema evolution, pinned
  offline verification tooling and protected-environment policy evidence.
- Recovery implementation requires `rfc8785==0.1.4` in the isolated recovery
  tool environment and the existing `cryptography` Ed25519 dependency.
- Production requires named Human signing/release approvers and the already
  pending recovery custody, quorum, retention, rotation and compromise choices.
- Rollout is fail closed: old unsigned recovery sets and pending/unbound release
  dossiers are not production-authoritative.

## Required qualification

Release negatives shall reject forged/self-consistent manifests, wrong source,
artifact, dossier, sequence, signer, repository, workflow/ref, pending/rejected
approval, stale exception and post-approval mutation. One protected-workflow
fixture with final approval must pass offline verification.

Recovery negatives shall reject payload/signature mutation, artifact or digest
substitution, mixed-set splicing, wrong deployment/sequence/head/cutoff,
unknown/revoked key, duplicate/unknown fields, unsafe filenames and target
mutation before verification. A complete signed set must restore and reconcile
on disposable PostgreSQL `127.0.0.1:55432` only.

## Human decisions required

Human Architecture Authority must explicitly accept, reject or amend:

1. reuse of the PATCH-058 protected release signer/approval authority for the
   PATCH-059-specific workflow and exact signer identity;
2. the separate final Human approval/finalization evidence path;
3. the versioned release-manifest/dossier binding of `release_sequence`;
4. reuse of the dedicated Recovery Authority for the recovery-set signature;
5. the recovery-set schema, RFC 8785 canonicalization and domain separator;
6. the disposition of existing unsigned recovery sets.

Only after explicit acceptance may a separately reviewed implementation-plan
amendment authorize code/workflow/schema changes for SEC-E-MAJ-05 and
SEC-E-MAJ-06.

## Governance disposition

This accepted decision reuses the two already separated authorities and rejects
new keys, shared secrets and generic signer broadening. Human architectural
acceptance occurred first; the separately governed bounded implementation-plan
amendment was subsequently Human authorized on 2026-10-03. Neither approval is
release approval or Checkpoint E acceptance.

**ADR-032: ACCEPTED BY HUMAN ARCHITECTURE AUTHORITY ON 2026-10-03. BOUNDED IMPLEMENTATION AMENDMENT AUTHORIZED ON 2026-10-03.**

## Amendment history

- **Amendment 1 — Single-Human-Authority Operating Mode:** accepted by Human
  Architecture Authority on 2026-10-04 for SATCO's current pre-production
  organizational stage. It clarifies that one named Human may perform the
  candidate-specific security-exception, protected signing-authorization and
  final-release-approval roles only as separate purpose-bound decisions and
  evidence records; distinct roles do not mean different natural persons in
  this mode. It preserves separate protected Environments,
  `prevent_self_review`, no administrator bypass, least-privilege non-Human
  dispatch, immutable evidence binding, a minimum 15-minute interval before
  final approval, separate deployment authorization and separate Human
  Acceptance. See
  `ADR-032-Amendment-1-Single-Human-Authority-Operating-Mode.md`. Implementation
  remains subject to a separately reviewed and explicitly Human-authorized
  implementation-plan amendment.
