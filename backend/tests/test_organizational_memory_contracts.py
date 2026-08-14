"""PATCH-034 Batch 1 contract evidence."""

from dataclasses import dataclass, fields
from datetime import datetime, timezone
from typing import get_args, get_type_hints
from uuid import UUID, uuid4

import pytest

from app.enums.organizational_memory import IDEMPOTENCY_RESULT_TYPES, MemoryOperation, MemoryProvenanceOperation
from app.exceptions.organizational_memory import OrganizationalMemoryValidationError
from app.models.organizational_memory_command import (
    AcceptedReportSource,
    AdmittedQualificationV1,
    AdmittedReportProjectionV1,
    AdmittedTechnicalContentV1,
    CaptureProvenanceAuthorization,
    EngineeringObjectProvenanceAuthorization,
    EngineeringRelationshipProvenanceAuthorization,
    EvidenceProvenanceAuthorization,
    MemoryActor,
    MemoryCommandMetadata,
    MemoryAuditRecord,
    MemoryDomainEvent,
    MemoryEventPayloadV1,
    GetActiveSuccess,
    MemoryIdempotencyCompleted,
    MemoryIdempotencyKey,
    MemoryStandingHistoryRecord,
    MemoryProvenanceAuthorizationRequest,
    MemoryScope,
    ProvenanceAuthorized,
    SafeAuthorizedProvenance,
    StoredAdmissionResultV1,
    StoredSuccessorResultV1,
    StoredSupersessionResultV1,
    StoredWithdrawalResultV1,
    canonical_json,
    canonical_digest,
    validate_stored_result,
    validate_provenance_success,
)
from app.ports.organizational_memory import OrganizationalMemoryService
from app.ports.organizational_memory import OrganizationalMemoryUnitOfWork
from app.repositories.organizational_memory_unit_of_work import SqlAlchemyOrganizationalMemoryUnitOfWork
from app.enums.technical_report import TechnicalReportPurpose


NOW = datetime(2026, 8, 12, 12, 0, tzinfo=timezone.utc)
DIGEST = "a" * 64


def test_actor_scope_metadata_are_closed_and_validate_trusted_identity():
    actor = MemoryActor(7, uuid4())
    scope = MemoryScope(actor.organization_id, 11, 13)
    metadata = MemoryCommandMetadata(actor, uuid4(), uuid4(), uuid4(), "Human admission")
    assert [field.name for field in fields(actor)] == ["actor_id", "organization_id"]
    assert [field.name for field in fields(scope)] == ["organization_id", "workspace_id", "project_id"]
    assert metadata.actor is actor
    with pytest.raises(OrganizationalMemoryValidationError): MemoryActor(True, uuid4())
    with pytest.raises(OrganizationalMemoryValidationError): MemoryScope(uuid4(), 0, None)


def test_canonical_projection_digest_golden_fixture():
    projection = AdmittedReportProjectionV1(
        "organizational_memory.accepted_report.v1",
        UUID("00000000-0000-0000-0000-000000000001"),
        TechnicalReportPurpose.ENGINEERING_ANALYSIS,
        UUID("00000000-0000-0000-0000-000000000002"), 3, 4,
        AdmittedTechnicalContentV1("Scope", "Content", ("A",), "U", ("L",), "C", ("R",)),
        AdmittedQualificationV1(False, (), (), ()),
        UUID("00000000-0000-0000-0000-000000000003"), 1, 2, 5, NOW, None,
    )
    assert canonical_digest(projection) == "f166e18922a94a170700c49382a25ef02ec54e586c9ec246a10032405237a2a6"


def _stored_results():
    memory_id, report_id, predecessor, replacement = uuid4(), uuid4(), uuid4(), uuid4()
    return {
        "admit": StoredAdmissionResultV1("admit.v1", memory_id, 1, "active", report_id, 4),
        "withdraw": StoredWithdrawalResultV1("withdraw.v1", memory_id, 2, "withdrawn", NOW),
        "create_successor": StoredSuccessorResultV1("create_successor.v1", memory_id, 1, "active", report_id, 5, predecessor),
        "supersede": StoredSupersessionResultV1("supersede.v1", predecessor, 3, "superseded", replacement, 1, "active", NOW),
    }


def test_exact_operation_to_stored_result_mapping_and_all_mismatches():
    results = _stored_results()
    assert IDEMPOTENCY_RESULT_TYPES == {
        "admit": "admit.v1", "withdraw": "withdraw.v1",
        "create_successor": "create_successor.v1", "supersede": "supersede.v1",
    }
    for operation, result in results.items():
        validate_stored_result(operation, result)
        assert len(canonical_json(result)) <= 1024
        for wrong_operation in results.keys() - {operation}:
            with pytest.raises(OrganizationalMemoryValidationError):
                validate_stored_result(wrong_operation, result)


def test_stored_replay_is_bounded_and_plaintext_free():
    prohibited = ("projection", "content", "manifest", "provenance", "rationale", "reason", "audience", "restriction", "diagnostic", "exception", "credential")
    for result in _stored_results().values():
        payload = canonical_json(result).decode()
        assert len(payload.encode()) <= 1024
        assert not any(term in payload.lower() for term in prohibited)


def test_malformed_results_replay_event_history_audit_and_idempotency_are_rejected():
    from app.enums.organizational_memory import MemoryEventType, MemoryStanding
    from app.models.organizational_memory_command import AdmissionSuccess
    source = AcceptedReportSource(uuid4(), 1, DIGEST)
    with pytest.raises(OrganizationalMemoryValidationError): AdmissionSuccess("success", "bad", 1, MemoryStanding.ACTIVE, source)
    with pytest.raises(OrganizationalMemoryValidationError): StoredAdmissionResultV1("admit.v1", "bad", 0, "withdrawn", "bad", -1)
    with pytest.raises(OrganizationalMemoryValidationError): MemoryStandingHistoryRecord(uuid4(), uuid4(), uuid4(), 1, MemoryStanding.ACTIVE, MemoryStanding.ACTIVE, 1, NOW, "bad", None)
    with pytest.raises(OrganizationalMemoryValidationError): MemoryDomainEvent(uuid4(), MemoryEventType.WITHDRAWN, 1, uuid4(), 1, uuid4(), 2, 3, MemoryStanding.ACTIVE, 1, NOW, uuid4(), uuid4(), uuid4(), uuid4(), 1, None, None, 1)
    with pytest.raises(OrganizationalMemoryValidationError): MemoryIdempotencyKey(uuid4(), 1, "get_active", uuid4())
    with pytest.raises(OrganizationalMemoryValidationError): MemoryIdempotencyCompleted("completed", "bad", 1, _stored_results()["admit"])
    with pytest.raises(OrganizationalMemoryValidationError): MemoryAuditRecord(MemoryOperation.ADMIT, 0, uuid4(), uuid4(), None, 1, MemoryStanding.ACTIVE, uuid4(), 1, uuid4(), uuid4(), uuid4(), NOW, None, None, 1)
    with pytest.raises(OrganizationalMemoryValidationError): GetActiveSuccess("success", object())


def test_four_context_specific_provenance_authorization_variants_are_closed():
    organization = uuid4(); entry = uuid4(); actor = MemoryActor(9, organization)
    variants = (
        CaptureProvenanceAuthorization(entry, 0, uuid4(), 1, organization, 2, 3, uuid4()),
        EvidenceProvenanceAuthorization(uuid4(), 1, uuid4(), 1, organization, 2, 3),
        EngineeringObjectProvenanceAuthorization(uuid4(), 2, uuid4(), 1, organization, 2, 3),
        EngineeringRelationshipProvenanceAuthorization(uuid4(), 3, uuid4(), 1, organization, 2, 3, uuid4(), uuid4()),
    )
    request = MemoryProvenanceAuthorizationRequest(
        actor, MemoryProvenanceOperation.ADMIT, MemoryScope(organization, 3, 2),
        AcceptedReportSource(uuid4(), 1, DIGEST), variants,
    )
    assert request.items == variants
    assert len({type(item) for item in variants}) == 4


def test_provenance_requests_are_bounded_ordered_unique_and_same_organization():
    organization = uuid4(); actor = MemoryActor(1, organization); source = AcceptedReportSource(uuid4(), 1, DIGEST); scope = MemoryScope(organization, 3, 2)
    item = EvidenceProvenanceAuthorization(uuid4(), 0, uuid4(), 1, organization, 2, 3)
    with pytest.raises(OrganizationalMemoryValidationError): MemoryProvenanceAuthorizationRequest(actor, MemoryProvenanceOperation.ADMIT, scope, source, ())
    with pytest.raises(OrganizationalMemoryValidationError): MemoryProvenanceAuthorizationRequest(actor, MemoryProvenanceOperation.ADMIT, scope, source, (item, item))
    wrong = EvidenceProvenanceAuthorization(uuid4(), 1, uuid4(), 1, uuid4(), 2, 3)
    with pytest.raises(OrganizationalMemoryValidationError): MemoryProvenanceAuthorizationRequest(actor, MemoryProvenanceOperation.ADMIT, scope, source, (item, wrong))


def test_provenance_rejects_synthetic_and_cross_scope_variants():
    @dataclass(frozen=True)
    class Synthetic:
        entry_id: object; ordinal: int; evidence_id: object; source_version: int; organization_id: object; project_id: int; workspace_id: int
    organization = uuid4(); actor = MemoryActor(1, organization); scope = MemoryScope(organization, 3, 2); source = AcceptedReportSource(uuid4(), 1, DIGEST)
    with pytest.raises(OrganizationalMemoryValidationError): MemoryProvenanceAuthorizationRequest(actor, MemoryProvenanceOperation.ADMIT, scope, source, (Synthetic(uuid4(), 0, uuid4(), 1, organization, 2, 3),))
    cross_project = EvidenceProvenanceAuthorization(uuid4(), 0, uuid4(), 1, organization, 99, 3)
    with pytest.raises(OrganizationalMemoryValidationError): MemoryProvenanceAuthorizationRequest(actor, MemoryProvenanceOperation.ADMIT, scope, source, (cross_project,))
    cross_workspace = EvidenceProvenanceAuthorization(uuid4(), 0, uuid4(), 1, organization, 2, 99)
    with pytest.raises(OrganizationalMemoryValidationError): MemoryProvenanceAuthorizationRequest(actor, MemoryProvenanceOperation.ADMIT, scope, source, (cross_workspace,))


def test_provenance_success_requires_exact_cardinality_identity_and_order():
    organization = uuid4(); actor = MemoryActor(1, organization); scope = MemoryScope(organization, 3, 2); source = AcceptedReportSource(uuid4(), 1, DIGEST)
    request_item = EvidenceProvenanceAuthorization(uuid4(), 0, uuid4(), 1, organization, 2, 3)
    request = MemoryProvenanceAuthorizationRequest(actor, MemoryProvenanceOperation.ADMIT, scope, source, (request_item,))
    safe = SafeAuthorizedProvenance(request_item.entry_id, 0, __import__("app.enums.technical_report", fromlist=["TechnicalReportSourceClass"]).TechnicalReportSourceClass.CANONICAL_MATERIAL, "evidence", "evidence", True, "basis", "a" * 64, "sha256", "b" * 64)
    validate_provenance_success(request, ProvenanceAuthorized("success", (safe,)))
    with pytest.raises(OrganizationalMemoryValidationError): validate_provenance_success(request, ProvenanceAuthorized("success", ()))
    wrong = SafeAuthorizedProvenance(uuid4(), 0, safe.source_class, safe.source_type, safe.owning_capability, True, safe.reliance_role, safe.locator_digest, "sha256", safe.source_integrity_digest)
    with pytest.raises(OrganizationalMemoryValidationError): validate_provenance_success(request, ProvenanceAuthorized("success", (wrong,)))


def test_service_protocol_exposes_exactly_seven_v1_operations():
    methods = {name for name, value in OrganizationalMemoryService.__dict__.items() if callable(value) and not name.startswith("_")}
    assert methods == {"admit", "get_active", "list_active", "inspect_history", "create_successor", "withdraw", "supersede"}
    assert {item.value for item in MemoryOperation} >= methods
    hints = {name: get_type_hints(getattr(OrganizationalMemoryService, name))["return"] for name in methods}
    assert all("Schema" not in str(result) for result in hints.values())
    assert {name: {item.__name__ for item in get_args(result)} for name, result in hints.items()} == {
        "admit": {"AdmissionSuccess", "MemoryProtectedNotFound", "MemoryInvalidRequest", "MemoryIdempotencyConflict", "MemoryDuplicateSource", "MemoryUnavailable"},
        "withdraw": {"WithdrawalSuccess", "MemoryProtectedNotFound", "MemoryInvalidRequest", "MemoryVersionConflict", "MemoryIdempotencyConflict", "MemoryInvalidStanding", "MemoryUnavailable"},
        "create_successor": {"CreateSuccessorSuccess", "MemoryProtectedNotFound", "MemoryInvalidRequest", "MemoryIdempotencyConflict", "MemoryDuplicateSource", "MemoryUnavailable"},
        "supersede": {"SupersessionSuccess", "MemoryProtectedNotFound", "MemoryInvalidRequest", "MemoryVersionConflict", "MemoryIdempotencyConflict", "MemoryInvalidStanding", "MemoryUnavailable"},
        "get_active": {"GetActiveSuccess", "MemoryProtectedNotFound", "MemoryInvalidRequest", "MemoryUnavailable"},
        "list_active": {"ListActiveSuccess", "MemoryProtectedNotFound", "MemoryInvalidRequest", "MemoryUnavailable"},
        "inspect_history": {"InspectHistorySuccess", "MemoryProtectedNotFound", "MemoryInvalidRequest", "MemoryUnavailable"},
    }


def test_batch4_concrete_uow_structurally_exposes_exact_atomic_collaborators():
    required = {"memories", "authorization", "final_recheck", "audit", "domain_events", "idempotency", "rejection_audit"}
    annotations = getattr(OrganizationalMemoryUnitOfWork, "__annotations__", {})
    assert required <= set(annotations)
    for method in ("__enter__", "__exit__", "flush", "commit", "rollback"):
        assert callable(getattr(SqlAlchemyOrganizationalMemoryUnitOfWork, method))
