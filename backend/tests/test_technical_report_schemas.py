"""PATCH-032 Batch 1 schema, historical contract, and digest tests."""

from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest
from pydantic import TypeAdapter, ValidationError

from app.exceptions.technical_report import TechnicalReportIntegrityMismatch
from app.models.technical_report_command import canonical_historical_json, historical_basis_digest, verify_historical_basis_digest
from app.models.technical_report_command import (
    ContextualLocator,
    ExternalHumanLocator,
    StandardLocator,
    TechnicalReportProvenanceEntry,
    canonical_json,
)
from app.enums.technical_report import (
    TechnicalReportAvailabilityStatus,
    TechnicalReportIntegrityAlgorithm,
    TechnicalReportOwningCapability,
    TechnicalReportSourceClass,
    TechnicalReportSourceType,
    TechnicalReportVerificationStatus,
)
from app.schemas.technical_report import (
    CaptureHistoricalBasisSchema,
    EngineeringObjectHistoricalBasisSchema,
    EngineeringRelationshipHistoricalBasisSchema,
    EvidenceHistoricalBasisSchema,
    HistoricalBasisSchema,
    TechnicalReportAcceptRequest,
    TechnicalReportContentSchema,
    TechnicalReportCreateRequest,
    PreliminaryQualificationSchema,
    TechnicalReportProvenanceSchema,
    TechnicalReportSummary,
)


NOW = datetime(2026, 8, 9, 8, 0, tzinfo=timezone.utc)


def capture_payload():
    return dict(basis_schema_version=1, source_category="universal_capture", capture_id=uuid4(), source_version=1, organization_id=uuid4(), project_id=2, workspace_id=None, discipline=None, engineering_object_id=None, source_kind="observation", original_content="Café vibration observed", source_reference=None, creator_id=7, lifecycle="captured", created_at=NOW)


def evidence_payload():
    return dict(basis_schema_version=1, source_category="evidence", evidence_id=uuid4(), source_version=2, organization_id=uuid4(), project_id=2, workspace_id=3, lifecycle="current", source_kind="engineering_record", source_reference="record-1", source_revision="A", source_standing="current", effective_at=None, supported_fact="Measured current was 12 A", creator_id=7)


def object_payload():
    return dict(basis_schema_version=1, source_category="engineering_object", engineering_object_id=uuid4(), source_version=3, organization_id=uuid4(), customer_id=None, project_id=2, workspace_id=3, family="electrical", discipline="electrical", object_type="motor", subtype=None, lifecycle="active", authority_standing="approved", creator_id=7, steward_id=8)


def relationship_payload():
    return dict(basis_schema_version=1, source_category="engineering_relationship", engineering_relationship_id=uuid4(), source_version=4, organization_id=uuid4(), project_id=2, workspace_id=3, source_object_id=uuid4(), target_object_id=uuid4(), relationship_family="dependency", relationship_type="depends_on", lifecycle="current", authority_standing="approved", evidence_references=[uuid4(), uuid4()], creator_id=7, steward_id=8, reviewer_id=None, approver_id=9)


@pytest.mark.parametrize("schema,payload_factory", [(CaptureHistoricalBasisSchema, capture_payload), (EvidenceHistoricalBasisSchema, evidence_payload), (EngineeringObjectHistoricalBasisSchema, object_payload), (EngineeringRelationshipHistoricalBasisSchema, relationship_payload)])
def test_closed_historical_contract_accepts_exact_shape(schema, payload_factory):
    value = schema(**payload_factory())
    assert value.to_domain().basis_schema_version == 1


@pytest.mark.parametrize("schema,payload_factory", [(CaptureHistoricalBasisSchema, capture_payload), (EvidenceHistoricalBasisSchema, evidence_payload), (EngineeringObjectHistoricalBasisSchema, object_payload), (EngineeringRelationshipHistoricalBasisSchema, relationship_payload)])
def test_closed_historical_contract_rejects_missing_and_undeclared_fields(schema, payload_factory):
    payload = payload_factory()
    payload.pop("source_version")
    with pytest.raises(ValidationError):
        schema(**payload)
    payload = payload_factory()
    payload["diagnostics"] = "must not enter provenance"
    with pytest.raises(ValidationError):
        schema(**payload)


def test_discriminated_historical_contract_rejects_unknown_category():
    payload = capture_payload()
    payload["source_category"] = "arbitrary_source"
    with pytest.raises(ValidationError):
        TypeAdapter(HistoricalBasisSchema).validate_python(payload)


def test_canonical_serialization_and_digest_are_deterministic():
    payload = capture_payload()
    payload["original_content"] = "Cafe\u0301 vibration observed"
    first = CaptureHistoricalBasisSchema(**payload).to_domain()
    payload["original_content"] = "Café vibration observed"
    second = CaptureHistoricalBasisSchema(**payload).to_domain()
    assert canonical_historical_json(first) == canonical_historical_json(second)
    assert historical_basis_digest(first) == historical_basis_digest(second)
    assert len(historical_basis_digest(first)) == 64
    assert canonical_historical_json(first).decode().startswith('{"basis_schema_version":1')


def test_digest_changes_with_material_meaning_and_integrity_mismatch_fails():
    payload = evidence_payload()
    first = EvidenceHistoricalBasisSchema(**payload).to_domain()
    payload["supported_fact"] = "Measured current was 13 A"
    second = EvidenceHistoricalBasisSchema(**payload).to_domain()
    assert historical_basis_digest(first) != historical_basis_digest(second)
    with pytest.raises(TechnicalReportIntegrityMismatch):
        verify_historical_basis_digest(first, historical_basis_digest(second))


def test_relationship_evidence_references_are_unique_and_canonically_sorted():
    payload = relationship_payload()
    value = EngineeringRelationshipHistoricalBasisSchema(**payload).to_domain()
    assert list(value.evidence_references) == sorted(value.evidence_references, key=str)
    payload["evidence_references"] = [payload["evidence_references"][0]] * 2
    with pytest.raises(ValidationError):
        EngineeringRelationshipHistoricalBasisSchema(**payload)


def test_client_create_and_accept_contracts_reject_authoritative_fields():
    create = dict(workspace_id=3, project_id=2, purpose="engineering_analysis", content=TechnicalReportContentSchema(engineering_scope="Motor", technical_content="Analysis", assumptions=[], uncertainty="Tolerance remains", limitations=[], conclusions="Condition confirmed", recommendations=[]), qualification=PreliminaryQualificationSchema(is_preliminary=False), provenance=[])
    TechnicalReportCreateRequest(**create)
    for field, value in (("organization_id", uuid4()), ("owner_id", 7), ("lifecycle", "accepted"), ("accepted_by_id", 7), ("version", 1)):
        with pytest.raises(ValidationError):
            TechnicalReportCreateRequest(**create, **{field: value})
    with pytest.raises(ValidationError):
        TechnicalReportAcceptRequest(expected_version=1, exact_draft_revision_id=uuid4(), confirmed=False, rationale="accept")


@pytest.mark.parametrize(
    "payload_factory,field",
    [
        (capture_payload, "source_kind"),
        (capture_payload, "lifecycle"),
        (evidence_payload, "source_kind"),
        (evidence_payload, "source_standing"),
        (object_payload, "family"),
        (object_payload, "discipline"),
        (object_payload, "object_type"),
        (object_payload, "authority_standing"),
        (relationship_payload, "relationship_family"),
        (relationship_payload, "relationship_type"),
        (relationship_payload, "lifecycle"),
    ],
)
def test_closed_historical_vocabularies_reject_arbitrary_values(payload_factory, field):
    payload = payload_factory(); payload[field] = "arbitrary"
    with pytest.raises(ValidationError):
        TypeAdapter(HistoricalBasisSchema).validate_python(payload)


def test_capture_normalization_and_single_line_reference_rules():
    payload = capture_payload(); payload["original_content"] = "A\r\nB\rC"
    assert CaptureHistoricalBasisSchema(**payload).to_domain().original_content == "A\nB\nC"
    payload["original_content"] = "A\x01B"
    with pytest.raises(Exception):
        CaptureHistoricalBasisSchema(**payload).to_domain()
    payload = capture_payload(); payload["source_reference"] = "line one\nline two"
    with pytest.raises(Exception):
        CaptureHistoricalBasisSchema(**payload).to_domain()


def test_historical_timestamps_must_be_aware_at_schema_boundary():
    payload = capture_payload(); payload["created_at"] = datetime(2026, 1, 1)
    with pytest.raises(ValidationError):
        CaptureHistoricalBasisSchema(**payload)


def _entry(source_class, source_type, locator, material=True):
    digest = historical_basis_digest(locator) if hasattr(locator, "basis_schema_version") else __import__("hashlib").sha256(canonical_json(locator)).hexdigest()
    owners = {
        TechnicalReportSourceType.UNIVERSAL_CAPTURE: TechnicalReportOwningCapability.UNIVERSAL_CAPTURE,
        TechnicalReportSourceType.EVIDENCE: TechnicalReportOwningCapability.EVIDENCE,
        TechnicalReportSourceType.ENGINEERING_OBJECT: TechnicalReportOwningCapability.ENGINEERING_OBJECT,
        TechnicalReportSourceType.ENGINEERING_RELATIONSHIP: TechnicalReportOwningCapability.ENGINEERING_RELATIONSHIP,
    }
    return TechnicalReportProvenanceEntry(uuid4(), 0, source_class, source_type, material, owners.get(source_type), "basis", TechnicalReportVerificationStatus.VERIFIED, TechnicalReportAvailabilityStatus.AVAILABLE, "Human", (), locator, TechnicalReportIntegrityAlgorithm.SHA256 if material else None, digest if material else None)


def test_complete_provenance_union_and_coherence_matrix():
    capture = CaptureHistoricalBasisSchema(**capture_payload()).to_domain()
    assert _entry(TechnicalReportSourceClass.CANONICAL_MATERIAL, TechnicalReportSourceType.UNIVERSAL_CAPTURE, capture)
    external = ExternalHumanLocator(uuid4(), "field-note", 7, NOW, NOW, NOW, "relied-upon observation")
    assert _entry(TechnicalReportSourceClass.EXTERNAL_OR_HUMAN_MATERIAL, TechnicalReportSourceType.EXTERNAL_OR_HUMAN, external)
    standard = StandardLocator("IEC 1", "IEC", "2026", "4.2", "requirement", NOW)
    assert _entry(TechnicalReportSourceClass.STANDARDS_MATERIAL, TechnicalReportSourceType.STANDARD, standard)
    context = ContextualLocator(uuid4(), "workspace")
    assert _entry(TechnicalReportSourceClass.CONTEXTUAL_NON_MATERIAL, TechnicalReportSourceType.CONTEXTUAL, context, False)
    with pytest.raises(Exception):
        _entry(TechnicalReportSourceClass.CANONICAL_MATERIAL, TechnicalReportSourceType.EVIDENCE, capture)


def test_ports_have_typed_non_variadic_contracts():
    import inspect
    from app.ports import technical_report as ports
    for protocol_name in (
        "TechnicalReportRepository", "TechnicalReportAuthorizationPolicy",
        "TechnicalReportReferenceValidator", "TechnicalReportHistoricalResolver",
        "TechnicalReportDraftAssistant", "TechnicalReportAuditRecorder",
        "TechnicalReportRejectionAuditRecorder", "TechnicalReportDomainEventRecorder",
        "TechnicalReportIdempotencyStore", "TechnicalReportUnitOfWork",
    ):
        protocol = getattr(ports, protocol_name)
        for name, member in inspect.getmembers(protocol, inspect.isfunction):
            if name.startswith("_"):
                continue
            signature = inspect.signature(member)
            assert all(parameter.kind is not inspect.Parameter.VAR_KEYWORD for parameter in signature.parameters.values())
            assert signature.return_annotation is not inspect.Signature.empty


CANONICAL_CASES = (
    (TechnicalReportSourceType.UNIVERSAL_CAPTURE, TechnicalReportOwningCapability.UNIVERSAL_CAPTURE, CaptureHistoricalBasisSchema, capture_payload),
    (TechnicalReportSourceType.EVIDENCE, TechnicalReportOwningCapability.EVIDENCE, EvidenceHistoricalBasisSchema, evidence_payload),
    (TechnicalReportSourceType.ENGINEERING_OBJECT, TechnicalReportOwningCapability.ENGINEERING_OBJECT, EngineeringObjectHistoricalBasisSchema, object_payload),
    (TechnicalReportSourceType.ENGINEERING_RELATIONSHIP, TechnicalReportOwningCapability.ENGINEERING_RELATIONSHIP, EngineeringRelationshipHistoricalBasisSchema, relationship_payload),
)


def provenance_payload(source_type, owner, locator):
    return dict(entry_id=uuid4(), ordinal=0, source_class="canonical_material", source_type=source_type, is_material=True, owning_capability=owner, reliance_role="basis", verification_status="verified", availability_status="available", origin_attribution="Human", limitations=[], locator=locator, integrity_algorithm="sha256", integrity_digest="0" * 64)


@pytest.mark.parametrize("source_type,owner,schema,payload_factory", CANONICAL_CASES)
def test_pydantic_canonical_provenance_matrix_is_closed(source_type, owner, schema, payload_factory):
    payload = provenance_payload(source_type, owner, payload_factory())
    assert isinstance(TechnicalReportProvenanceSchema(**payload).locator, schema)
    wrong_owner = next(item for item in TechnicalReportOwningCapability if item is not owner)
    with pytest.raises(ValidationError): TechnicalReportProvenanceSchema(**(payload | {"owning_capability": wrong_owner}))
    with pytest.raises(ValidationError): TechnicalReportProvenanceSchema(**(payload | {"owning_capability": "arbitrary"}))
    wrong_locator = capture_payload() if source_type is not TechnicalReportSourceType.UNIVERSAL_CAPTURE else evidence_payload()
    with pytest.raises(ValidationError): TechnicalReportProvenanceSchema(**(payload | {"locator": wrong_locator}))
    with pytest.raises(ValidationError): TechnicalReportProvenanceSchema(**(payload | {"source_class": "standards_material"}))
    locator_extra = payload_factory() | {"canonical_only_extra": "forbidden"}
    with pytest.raises(ValidationError): TechnicalReportProvenanceSchema(**(payload | {"locator": locator_extra}))


def external_payload():
    return dict(locator_type="external_or_human", report_local_source_id=uuid4(), external_reference="field-note", submitted_by_id=7, observed_at=NOW, retrieved_at=NOW, submitted_at=NOW, minimal_representation="relied-upon observation")


def standard_payload():
    return dict(locator_type="standard", standard_identity="IEC 1", issuing_authority="IEC", edition="2026", clause_or_location="4.2", minimal_representation="requirement", retrieved_at=NOW)


def noncanonical_provenance(source_class, source_type, locator):
    return dict(entry_id=uuid4(), ordinal=0, source_class=source_class, source_type=source_type, is_material=True, owning_capability=None, reliance_role="basis", verification_status="verified", availability_status="available", origin_attribution="Human", limitations=[], locator=locator, integrity_algorithm="sha256", integrity_digest="0" * 64)


@pytest.mark.parametrize("missing", ["report_local_source_id", "external_reference", "minimal_representation"])
def test_external_human_provenance_required_and_forbidden_fields(missing):
    locator = external_payload(); locator.pop(missing)
    with pytest.raises(ValidationError): TechnicalReportProvenanceSchema(**noncanonical_provenance("external_or_human_material", "external_or_human", locator))


def test_external_human_provenance_rejects_owner_basis_extra_and_naive_time():
    payload = noncanonical_provenance("external_or_human_material", "external_or_human", external_payload())
    assert TechnicalReportProvenanceSchema(**payload)
    with pytest.raises(ValidationError): TechnicalReportProvenanceSchema(**(payload | {"owning_capability": "evidence"}))
    with pytest.raises(ValidationError): TechnicalReportProvenanceSchema(**(payload | {"locator": capture_payload()}))
    locator = external_payload() | {"historical_basis": capture_payload()}
    with pytest.raises(ValidationError): TechnicalReportProvenanceSchema(**(payload | {"locator": locator}))
    locator = external_payload() | {"observed_at": datetime(2026, 1, 1)}
    with pytest.raises(ValidationError): TechnicalReportProvenanceSchema(**(payload | {"locator": locator}))
    locator = external_payload() | {"observed_at": None, "retrieved_at": None, "submitted_at": None}
    with pytest.raises(ValidationError): TechnicalReportProvenanceSchema(**(payload | {"locator": locator}))
    with pytest.raises(ValidationError): TechnicalReportProvenanceSchema(**(payload | {"diagnostics": "forbidden"}))


@pytest.mark.parametrize("missing", ["standard_identity", "issuing_authority", "edition", "clause_or_location", "minimal_representation"])
def test_standards_provenance_required_and_forbidden_fields(missing):
    locator = standard_payload(); locator.pop(missing)
    with pytest.raises(ValidationError): TechnicalReportProvenanceSchema(**noncanonical_provenance("standards_material", "standard", locator))


def test_standards_provenance_rejects_owner_basis_extra_and_naive_time():
    payload = noncanonical_provenance("standards_material", "standard", standard_payload())
    assert TechnicalReportProvenanceSchema(**payload)
    with pytest.raises(ValidationError): TechnicalReportProvenanceSchema(**(payload | {"owning_capability": "engineering_object"}))
    with pytest.raises(ValidationError): TechnicalReportProvenanceSchema(**(payload | {"locator": object_payload()}))
    locator = standard_payload() | {"canonical_snapshot_id": str(uuid4())}
    with pytest.raises(ValidationError): TechnicalReportProvenanceSchema(**(payload | {"locator": locator}))
    locator = standard_payload() | {"retrieved_at": datetime(2026, 1, 1)}
    with pytest.raises(ValidationError): TechnicalReportProvenanceSchema(**(payload | {"locator": locator}))
    with pytest.raises(ValidationError): TechnicalReportProvenanceSchema(**(payload | {"diagnostics": "forbidden"}))


def test_contextual_provenance_is_non_material_closed_and_ownerless():
    locator = dict(locator_type="contextual", context_id=uuid4(), owning_context="workspace")
    payload = dict(entry_id=uuid4(), ordinal=0, source_class="contextual_non_material", source_type="contextual", is_material=False, owning_capability=None, reliance_role="navigation", verification_status="verified", availability_status="available", origin_attribution="Human", limitations=[], locator=locator, integrity_algorithm=None, integrity_digest=None)
    assert TechnicalReportProvenanceSchema(**payload)
    with pytest.raises(ValidationError): TechnicalReportProvenanceSchema(**(payload | {"is_material": True}))
    with pytest.raises(ValidationError): TechnicalReportProvenanceSchema(**(payload | {"owning_capability": "universal_capture"}))
    with pytest.raises(ValidationError): TechnicalReportProvenanceSchema(**(payload | {"locator": locator | {"historical_basis": capture_payload()}}))


def test_summary_read_boundary_requires_positive_values_and_utc_timestamps():
    payload = dict(id=uuid4(), organization_id=uuid4(), workspace_id=1, project_id=None, owner_id=1, purpose="engineering_analysis", lifecycle="draft", version=1, draft_revision_id=uuid4(), is_preliminary=False, predecessor_report_id=None, created_at=NOW, updated_at=NOW)
    assert TechnicalReportSummary(**payload)
    for field in ("workspace_id", "owner_id", "version"):
        with pytest.raises(ValidationError): TechnicalReportSummary(**(payload | {field: 0}))
        with pytest.raises(ValidationError): TechnicalReportSummary(**(payload | {field: -1}))
    with pytest.raises(ValidationError): TechnicalReportSummary(**(payload | {"created_at": datetime(2026, 1, 1)}))
    non_utc = datetime(2026, 1, 1, tzinfo=timezone(timedelta(hours=1)))
    with pytest.raises(ValidationError): TechnicalReportSummary(**(payload | {"updated_at": non_utc}))
