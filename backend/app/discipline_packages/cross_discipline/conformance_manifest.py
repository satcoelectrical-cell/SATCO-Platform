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

BATCH_TWO_VECTOR_IDS = (
    "patch053.ei01.power_present", "patch053.ei02.power_missing",
    "patch053.ei03.voltage_equal", "patch053.ei04.voltage_mismatch",
    "patch053.ei05.cable_jb_complete", "patch053.ei06.cable_jb_gap",
    "patch053.ei07.handoff_complete", "patch053.ei08.handoff_incomplete",
)
BATCH_TWO_EXPECTED_RESULTS = {
    "patch053.ei01.power_present": "power rule satisfied; no Finding",
    "patch053.ei02.power_missing": "one missing/ei.instrument_power_required",
    "patch053.ei03.voltage_equal": "voltage rule satisfied; no Finding",
    "patch053.ei04.voltage_mismatch": "one inconsistent/ei.motor_instrument_voltage",
    "patch053.ei05.cable_jb_complete": "dependency rule satisfied; no Finding",
    "patch053.ei06.cable_jb_gap": "one dependency/ei.cable_jb_path",
    "patch053.ei07.handoff_complete": "handoff rule satisfied; no Finding",
    "patch053.ei08.handoff_incomplete": "one incomplete_handoff/ei.handoff_complete",
}
CUMULATIVE_BATCH_TWO_VECTOR_IDS = BATCH_ONE_VECTOR_IDS + BATCH_TWO_VECTOR_IDS

BATCH_THREE_VECTOR_IDS = (
    "patch053.ic01.signal_type_equal", "patch053.ic02.signal_type_mismatch",
    "patch053.ic03.range_contains", "patch053.ic04.range_mismatch",
    "patch053.ic05.valve_paths", "patch053.ic06.valve_feedback_gap",
    "patch053.ic07.commitment_fulfilled", "patch053.ic08.commitment_unfulfilled",
)
BATCH_THREE_EXPECTED_RESULTS = {
    "patch053.ic01.signal_type_equal": "signal type rule satisfied; no Finding",
    "patch053.ic02.signal_type_mismatch": "one inconsistent/ic.signal_type",
    "patch053.ic03.range_contains": "signal range rule satisfied; no Finding",
    "patch053.ic04.range_mismatch": "one inconsistent/ic.signal_range",
    "patch053.ic05.valve_paths": "valve command/feedback dependency satisfied; no Finding",
    "patch053.ic06.valve_feedback_gap": "one dependency/ic.valve_command_feedback",
    "patch053.ic07.commitment_fulfilled": "commitment fulfilment satisfied; no Finding",
    "patch053.ic08.commitment_unfulfilled": "one unfulfilled_commitment/ic.commitment_fulfilment",
}
CUMULATIVE_BATCH_THREE_VECTOR_IDS = CUMULATIVE_BATCH_TWO_VECTOR_IDS + BATCH_THREE_VECTOR_IDS

BATCH_FOUR_VECTOR_IDS = (
    "patch053.ec01.command_status_complete", "patch053.ec02.status_missing",
    "patch053.ec03.cabinet_power_complete", "patch053.ec04.cabinet_power_gap",
    "patch053.ec05.source_fresh", "patch053.ec06.source_stale",
    "patch053.ec07.no_dispute", "patch053.ec08.disputed",
)
BATCH_FOUR_EXPECTED_RESULTS = {
    "patch053.ec01.command_status_complete": "MCC command/status handoff satisfied; no Finding",
    "patch053.ec02.status_missing": "one incomplete_handoff/ec.mcc_command_status",
    "patch053.ec03.cabinet_power_complete": "cabinet power path satisfied; no Finding",
    "patch053.ec04.cabinet_power_gap": "one dependency/ec.cabinet_power_path",
    "patch053.ec05.source_fresh": "source freshness satisfied; no Finding",
    "patch053.ec06.source_stale": "one stale/ec.source_freshness",
    "patch053.ec07.no_dispute": "commitment is not disputed; no Finding",
    "patch053.ec08.disputed": "one disputed/ec.commitment_dispute",
}
CUMULATIVE_BATCH_FOUR_VECTOR_IDS = CUMULATIVE_BATCH_THREE_VECTOR_IDS + BATCH_FOUR_VECTOR_IDS

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


def build_batch_two_manifest(fixture_digests: dict[str, str]) -> tuple[ConformanceVectorV1, ...]:
    if set(fixture_digests) != set(CUMULATIVE_BATCH_TWO_VECTOR_IDS):
        raise ValueError("exact cumulative Batch-2 fixture set required")
    vectors = []
    for vector_id in CUMULATIVE_BATCH_TWO_VECTOR_IDS:
        body = {"schema_version": 1, "vector_id": vector_id, "fixture_id": vector_id,
                "fixture_digest": fixture_digests[vector_id],
                "owner": vector_id.split(".")[1], "postgres_required": True}
        vectors.append(ConformanceVectorV1(**body, vector_digest=digest(body)))
    validate_batch_two_manifest(tuple(vectors))
    return tuple(vectors)


def validate_batch_two_manifest(vectors: tuple[ConformanceVectorV1, ...]) -> None:
    if len(vectors) != 59 or tuple(item.vector_id for item in vectors) != CUMULATIVE_BATCH_TWO_VECTOR_IDS:
        raise ValueError("Batch-2 manifest must contain the exact ordered cumulative 59 vectors")
    if len({item.vector_id for item in vectors}) != 59 or not all(item.postgres_required for item in vectors):
        raise ValueError("invalid Batch-2 vector identity or PostgreSQL flag")


def build_batch_three_manifest(fixture_digests: dict[str, str]) -> tuple[ConformanceVectorV1, ...]:
    if set(fixture_digests) != set(CUMULATIVE_BATCH_THREE_VECTOR_IDS):
        raise ValueError("exact cumulative Batch-3 fixture set required")
    vectors = []
    for vector_id in CUMULATIVE_BATCH_THREE_VECTOR_IDS:
        body = {"schema_version": 1, "vector_id": vector_id, "fixture_id": vector_id,
                "fixture_digest": fixture_digests[vector_id],
                "owner": vector_id.split(".")[1], "postgres_required": True}
        vectors.append(ConformanceVectorV1(**body, vector_digest=digest(body)))
    validate_batch_three_manifest(tuple(vectors))
    return tuple(vectors)


def validate_batch_three_manifest(vectors: tuple[ConformanceVectorV1, ...]) -> None:
    if len(vectors) != 67 or tuple(item.vector_id for item in vectors) != CUMULATIVE_BATCH_THREE_VECTOR_IDS:
        raise ValueError("Batch-3 manifest must contain the exact ordered cumulative 67 vectors")
    if len({item.vector_id for item in vectors}) != 67 or not all(item.postgres_required for item in vectors):
        raise ValueError("invalid Batch-3 vector identity or PostgreSQL flag")


def build_batch_four_manifest(fixture_digests: dict[str, str]) -> tuple[ConformanceVectorV1, ...]:
    if set(fixture_digests) != set(CUMULATIVE_BATCH_FOUR_VECTOR_IDS):
        raise ValueError("exact cumulative Batch-4 fixture set required")
    vectors = []
    for vector_id in CUMULATIVE_BATCH_FOUR_VECTOR_IDS:
        body = {"schema_version": 1, "vector_id": vector_id, "fixture_id": vector_id,
                "fixture_digest": fixture_digests[vector_id],
                "owner": vector_id.split(".")[1], "postgres_required": True}
        vectors.append(ConformanceVectorV1(**body, vector_digest=digest(body)))
    validate_batch_four_manifest(tuple(vectors))
    return tuple(vectors)


def validate_batch_four_manifest(vectors: tuple[ConformanceVectorV1, ...]) -> None:
    if len(vectors) != 75 or tuple(item.vector_id for item in vectors) != CUMULATIVE_BATCH_FOUR_VECTOR_IDS:
        raise ValueError("Batch-4 manifest must contain the exact ordered cumulative 75 vectors")
    if len({item.vector_id for item in vectors}) != 75 or not all(item.postgres_required for item in vectors):
        raise ValueError("invalid Batch-4 vector identity or PostgreSQL flag")
