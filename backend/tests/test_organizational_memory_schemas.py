"""PATCH-034 Batch 1 strict schema evidence."""

from datetime import datetime, timezone
from uuid import uuid4

import pytest
from pydantic import TypeAdapter, ValidationError

from app.schemas.organizational_memory import (
    ActiveMemoryPageSchema,
    AdmitAcceptedReportSchema,
    AdmitResultSchema,
    InspectHistoryResultSchema,
    MemoryInvalidRequestSchema,
    MemoryProtectedNotFoundSchema,
    MemoryUnavailableSchema,
    MemoryVersionConflictSchema,
    SupersedeMemorySchema,
    SafeAuthorizedProvenanceSchema,
    WithdrawResultSchema,
)


NOW = datetime(2026, 8, 12, 12, 0, tzinfo=timezone.utc)


def _admission_payload():
    organization = uuid4()
    return {
        "metadata": {"actor": {"actor_id": 1, "organization_id": organization}, "correlation_id": uuid4(), "command_id": uuid4(), "idempotency_id": uuid4(), "rationale": "admit"},
        "source": {"report_id": uuid4(), "accepted_aggregate_version": 2, "accepted_snapshot_digest": "a" * 64},
        "scope": {"organization_id": organization, "workspace_id": 3, "project_id": 4},
        "audience_actor_ids": (1, 2), "reuse_restrictions": ("Validate applicability",), "admission_rationale": "Approved reuse",
    }


def test_admission_schema_is_strict_and_trusted_scope_bound():
    value = AdmitAcceptedReportSchema.model_validate(_admission_payload())
    assert value.scope.organization_id == value.metadata.actor.organization_id
    payload = _admission_payload(); payload["unexpected"] = True
    with pytest.raises(ValidationError): AdmitAcceptedReportSchema.model_validate(payload)
    payload = _admission_payload(); payload["scope"]["organization_id"] = uuid4()
    with pytest.raises(ValidationError): AdmitAcceptedReportSchema.model_validate(payload)


def test_payload_free_results_have_only_the_discriminator():
    for result in (MemoryProtectedNotFoundSchema(), MemoryInvalidRequestSchema(), MemoryUnavailableSchema(), MemoryVersionConflictSchema()):
        assert result.model_dump() == {"outcome": result.outcome}
        with pytest.raises(ValidationError): type(result).model_validate({"outcome": result.outcome, "detail": "secret"})


def test_operation_result_unions_reject_variants_not_declared_for_operation():
    admit = TypeAdapter(AdmitResultSchema)
    withdraw = TypeAdapter(WithdrawResultSchema)
    history = TypeAdapter(InspectHistoryResultSchema)
    assert admit.validate_python({"outcome": "protected_not_found"}).outcome == "protected_not_found"
    assert withdraw.validate_python({"outcome": "version_conflict"}).outcome == "version_conflict"
    with pytest.raises(ValidationError): admit.validate_python({"outcome": "version_conflict"})
    with pytest.raises(ValidationError): history.validate_python({"outcome": "invalid_standing"})


def test_supersession_schema_rejects_same_identity_and_non_strict_versions():
    identity = uuid4(); metadata = _admission_payload()["metadata"]
    with pytest.raises(ValidationError): SupersedeMemorySchema.model_validate({"metadata": metadata, "predecessor_memory_id": identity, "replacement_memory_id": identity, "expected_predecessor_version": 1, "expected_replacement_version": 1, "reason": "replace"})
    with pytest.raises(ValidationError): SupersedeMemorySchema.model_validate({"metadata": metadata, "predecessor_memory_id": uuid4(), "replacement_memory_id": uuid4(), "expected_predecessor_version": True, "expected_replacement_version": 1, "reason": "replace"})


def test_active_page_discloses_only_returned_count():
    page = ActiveMemoryPageSchema(items=(), visible_total=0, next_continuation=None)
    assert page.visible_total == len(page.items)
    with pytest.raises(ValidationError): ActiveMemoryPageSchema(items=(), visible_total=1, next_continuation=None)


def test_safe_provenance_rejects_incoherent_source_owner_pair():
    payload = {
        "entry_id": uuid4(), "ordinal": 0,
        "source_class": "canonical_material", "source_type": "evidence",
        "owning_capability": "engineering_object", "is_material": True,
        "reliance_role": "basis", "locator_digest": "a" * 64,
        "source_integrity_algorithm": "sha256", "source_integrity_digest": "b" * 64,
    }
    with pytest.raises(ValidationError): SafeAuthorizedProvenanceSchema.model_validate(payload)
