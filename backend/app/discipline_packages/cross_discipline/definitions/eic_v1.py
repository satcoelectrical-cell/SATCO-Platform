from __future__ import annotations

from ..canonical import digest
from ..conformance_manifest import BATCH_ONE_VECTOR_IDS
from ..contracts import (
    CANONICALIZATION_ID, DEFINITION_SET_ID, DefinitionSetV1, LIMITS,
    PROFILE_ID, REGISTRY_RELEASE_ID, RELEASE_ID,
)


COMPARISON_IDS = (
    "applicable_if", "disagrees", "enum_map_equal", "equal", "not_equal",
    "present", "range_contains", "range_overlaps", "set_contains",
    "set_equal", "stale_after", "within_absolute_tolerance",
)
SUPPORTED_COMBINATIONS = ("cross.ec.v1", "cross.ei.v1", "cross.eic.v1", "cross.ic.v1")


def load_batch_one_definition_set() -> DefinitionSetV1:
    # Pair/integrated production rules remain absent until Batches 2-5.
    body = {
        "schema_version": 1, "definition_set_id": DEFINITION_SET_ID,
        "version": "1.0.0", "release_id": RELEASE_ID,
        "registry_release_id": REGISTRY_RELEASE_ID, "profile_id": PROFILE_ID,
        "canonicalization_id": CANONICALIZATION_ID,
        "limits_profile": dict(LIMITS),
        "supported_combinations": SUPPORTED_COMBINATIONS,
        "comparison_ids": COMPARISON_IDS, "rule_ids": (),
        "conformance_vector_ids": BATCH_ONE_VECTOR_IDS,
    }
    return DefinitionSetV1(**body, digest=digest(body))


def validate_batch_one_definition_set(definition: DefinitionSetV1) -> None:
    if definition != load_batch_one_definition_set():
        raise ValueError("untrusted or modified cross-discipline definition set")
    if definition.rule_ids:
        raise ValueError("Batch-1 must not register pair or integrated rules")
