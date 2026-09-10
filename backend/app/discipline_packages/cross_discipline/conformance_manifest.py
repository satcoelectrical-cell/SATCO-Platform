"""Immutable Batch-1 slice of the authoritative PATCH-053 manifest."""

from __future__ import annotations

from dataclasses import dataclass

from .canonical import digest


KERNEL_VECTOR_IDS = tuple(f"patch053.k{i:02d}.{name}" for i, name in enumerate((
    "canonical_stable", "input_order", "unknown_field", "completed_empty",
    "completed_findings", "incomplete_scope", "artifact_missing",
    "missing_proven", "missing_unproven", "fingerprint_duplicate",
    "fingerprint_order", "recurrence", "cross_tenant", "revocation",
    "graph_cycle", "graph_bound", "payload_bound", "database_retry",
    "audit_minimized", "outbox_atomic", "source_race", "configuration_race",
    "commitment_race", "idempotent_replay", "idempotency_conflict",
    "retry_revoked", "query_budget", "runtime_budget",
), 1))
DISPOSITION_VECTOR_IDS = tuple(f"patch053.d{i:02d}.{name}" for i, name in enumerate((
    "acknowledge", "confirm", "reject", "accept_risk",
    "risk_without_decision", "resolution", "dispute",
    "require_and_supersede", "concurrent_forbidden",
), 1))
HISTORY_VECTOR_IDS = tuple(f"patch053.h{i:02d}.{name}" for i, name in enumerate((
    "replay_verified", "replay_digest_mismatch", "replay_artifact_missing",
    "replay_revoked", "configuration_upgrade", "reassessment_lineage",
    "lineage_cycle", "supersession_race",
), 1))
DATABASE_VECTOR_IDS = tuple(f"patch053.db{i:02d}.{name}" for i, name in enumerate((
    "fingerprint_unique", "tenant_coherence", "append_only",
    "migration_upgrade", "migration_downgrade", "migration_recovery",
), 1))
BATCH_ONE_VECTOR_IDS = (
    KERNEL_VECTOR_IDS + DISPOSITION_VECTOR_IDS + HISTORY_VECTOR_IDS
    + DATABASE_VECTOR_IDS
)

BATCH_ONE_EXPECTED_RESULTS = dict(zip(BATCH_ONE_VECTOR_IDS, (
    "identical snapshot/result digests",
    "canonical order; identical Findings/digest",
    "invalid request; no aggregate",
    "completed-no-findings; zero Findings",
    "completed-with-findings; exact set",
    "indeterminate/source-incomplete; zero Findings",
    "unavailable/artifact-unavailable",
    "one missing; attestation retained",
    "indeterminate; never missing/PASS",
    "invariant rejection; no commit",
    "identical fingerprint/order/result digest",
    "same recurrence; different fingerprint/IDs",
    "protected; no target counts/events",
    "rollback/protected; no source replay",
    "visit once; non-cycle rule indeterminate",
    "resource-limit; zero partial Findings",
    "indeterminate limit; no partial payload",
    "fresh UoW/auth; one aggregate within 3",
    "exact safe Audit; no raw/hidden data",
    "no partial aggregate/idempotency/Audit/outbox",
    "coherent retry success/indeterminate; never mixed",
    "retry then conflict/indeterminate; never mixed",
    "retry then exact state/indeterminate",
    "one aggregate; same ref after fresh auth",
    "conflict; no second root",
    "next attempt protected; no prior disclosure",
    "exact limit; no partial/replay substitution",
    "exact limit; atomic rollback/read-only replay",
    "append acknowledged; versions +1",
    "append confirmed; source unchanged",
    "rejected-not-applicable; Finding unchanged",
    "risk-accepted with accepted Decision ref",
    "invalid request; no event",
    "resolution-declared; not verified",
    "disputed; no selected truth",
    "required then superseded; history intact",
    "one winner; loser conflict; terminal enforced",
    "verified; same Findings/digest; no root",
    "mismatch/projection-digest-mismatch",
    "unavailable/artifact-missing; no latest",
    "protected-not-found",
    "old replay unchanged; reassessment new snapshot",
    "new root/reassessment edge; old immutable",
    "invalid/conflict; no edge",
    "one supersedes; other conflicts",
    "named uniqueness; no commit",
    "FK/check rejection",
    "update/delete rejected",
    "additive; old rows unchanged; no backfill",
    "empty-footprint downgrade restores parent",
    "failure rollback; one prior head",
), strict=True))


@dataclass(frozen=True, slots=True)
class ConformanceVectorV1:
    schema_version: int
    vector_id: str
    fixture_id: str
    fixture_digest: str
    owner: str
    postgres_required: bool
    vector_digest: str


def build_batch_one_manifest(fixture_digests: dict[str, str]) -> tuple[ConformanceVectorV1, ...]:
    if set(fixture_digests) != set(BATCH_ONE_VECTOR_IDS):
        raise ValueError("exact Batch-1 fixture set required")
    result = []
    for vector_id in BATCH_ONE_VECTOR_IDS:
        owner = vector_id.split(".")[1]
        body = {
            "schema_version": 1, "vector_id": vector_id,
            "fixture_id": vector_id, "fixture_digest": fixture_digests[vector_id],
            "owner": owner, "postgres_required": True,
        }
        result.append(ConformanceVectorV1(**body, vector_digest=digest(body)))
    return tuple(result)


def validate_batch_one_manifest(vectors: tuple[ConformanceVectorV1, ...]) -> None:
    if len(vectors) != 51 or tuple(v.vector_id for v in vectors) != BATCH_ONE_VECTOR_IDS:
        raise ValueError("Batch-1 manifest must contain the exact ordered 51 vectors")
    if len({v.vector_id for v in vectors}) != 51 or not all(v.postgres_required for v in vectors):
        raise ValueError("invalid Batch-1 vector identity or PostgreSQL flag")
    for vector in vectors:
        body = {
            "schema_version": vector.schema_version, "vector_id": vector.vector_id,
            "fixture_id": vector.fixture_id, "fixture_digest": vector.fixture_digest,
            "owner": vector.owner, "postgres_required": vector.postgres_required,
        }
        if vector.vector_digest != digest(body):
            raise ValueError(f"vector digest mismatch: {vector.vector_id}")
