"""PATCH-034 Batch 3 canonical application-boundary integration evidence."""

from datetime import datetime, timezone
from dataclasses import replace
from hashlib import sha256
from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.adapters.organizational_memory import (
    CanonicalMemoryProvenanceAuthorizer,
    TechnicalReportAcceptedSourceAdapter,
)
from app.exceptions.organizational_memory import OrganizationalMemoryValidationError
from app.enums import (
    EngineeringAuthorityStanding,
    EngineeringDiscipline,
    EngineeringExperienceCaptureLifecycle,
    EngineeringExperienceSourceKind,
    EngineeringLifecycle,
    EngineeringObjectFamily,
    EngineeringObjectType,
    EngineeringRelationshipLifecycle,
    EvidenceLifecycle,
    EvidenceSourceKind,
    EvidenceSourceStanding,
    RelationshipFamily,
    RelationshipType,
    TechnicalReportAvailabilityStatus,
    TechnicalReportIntegrityAlgorithm,
    TechnicalReportLifecycle,
    TechnicalReportOwningCapability,
    TechnicalReportPurpose,
    TechnicalReportSourceClass,
    TechnicalReportSourceType,
    TechnicalReportVerificationStatus,
)
from app.models.organizational_memory_command import (
    AcceptedReportProjection,
    AcceptedReportSource,
    CaptureProvenanceAuthorization,
    EngineeringObjectProvenanceAuthorization,
    EngineeringRelationshipProvenanceAuthorization,
    EvidenceProvenanceAuthorization,
    MemoryActor,
    MemoryProvenanceAuthorizationRequest,
    MemoryScope,
    ProvenanceAuthorized,
    admission_material_from_snapshot,
    canonical_json as memory_canonical_json,
)
from app.enums.organizational_memory import MemoryProvenanceOperation
from app.models.technical_report_command import (
    CaptureHistoricalBasisV1,
    EngineeringObjectHistoricalBasisV1,
    EngineeringRelationshipHistoricalBasisV1,
    EvidenceHistoricalBasisV1,
    PreliminaryQualification,
    TechnicalReportAcceptedSnapshot,
    TechnicalReportContent,
    TechnicalReportDraftRevision,
    TechnicalReportProvenanceEntry,
    ExternalHumanLocator,
    canonical_json,
)
from app.services.technical_report_service import TechnicalReportService
from app.services.engineering_experience_capture_service import (
    EngineeringExperienceCaptureService,
)
from app.services.evidence_service import EvidenceService
from app.services.engineering_object_service import EngineeringObjectService
from app.services.engineering_relationship_service import EngineeringRelationshipService
from app.ports.organizational_memory import MemoryProvenanceAuthorizer
from app.models.engineering_experience_capture import EngineeringExperienceCapture
from app.models.evidence import Evidence
from app.models.engineering_object import EngineeringObject
from app.models.engineering_relationship import EngineeringRelationship
from app.models.engineering_experience_capture_command import (
    EngineeringExperienceCaptureActor,
)
from app.models.engineering_object_command import AuthenticatedActor, AuthorizationContext
from app.models.engineering_relationship_command import (
    AuthenticatedRelationshipActor,
    RelationshipAuthorizationContext,
)
from app.models.evidence_command import EvidenceActor


NOW = datetime(2026, 8, 13, 8, 0, tzinfo=timezone.utc)


class RecordingService:
    def __init__(self, response=None, failure=None):
        self.response = response
        self.failure = failure
        self.calls = []

    def _call(self, *args, **kwargs):
        self.calls.append((args, kwargs))
        if self.failure is not None:
            raise self.failure
        return self.response

    def get_report(self, *args): return self._call(*args)
    def read_authorized_detail(self, **kwargs): return self._call(**kwargs)
    def get(self, *args): return self._call(*args)


def _entry(locator, ordinal, source_type, owner):
    return TechnicalReportProvenanceEntry(
        uuid4(), ordinal, TechnicalReportSourceClass.CANONICAL_MATERIAL,
        source_type, True, owner, "accepted basis",
        TechnicalReportVerificationStatus.VERIFIED,
        TechnicalReportAvailabilityStatus.AVAILABLE, "Human", (), locator,
        TechnicalReportIntegrityAlgorithm.SHA256,
        sha256(canonical_json(locator)).hexdigest(),
    )


def accepted_fixture():
    organization = uuid4(); report_id = uuid4(); object_id = uuid4()
    other_object_id = uuid4()
    capture = CaptureHistoricalBasisV1(
        1, "universal_capture", uuid4(), 2, organization, 11, 12,
        EngineeringDiscipline.INSTRUMENTATION, object_id,
        EngineeringExperienceSourceKind.OBSERVATION, "source body", None, 7,
        EngineeringExperienceCaptureLifecycle.CAPTURED, NOW,
    )
    evidence = EvidenceHistoricalBasisV1(
        1, "evidence", uuid4(), 3, organization, 11, 12,
        EvidenceLifecycle.CURRENT, EvidenceSourceKind.ENGINEERING_RECORD,
        "REF", "A", EvidenceSourceStanding.CURRENT, NOW, "supported fact", 7,
    )
    engineering_object = EngineeringObjectHistoricalBasisV1(
        1, "engineering_object", object_id, 4, organization, None, 11, 12,
        EngineeringObjectFamily.INSTRUMENTATION,
        EngineeringDiscipline.INSTRUMENTATION,
        EngineeringObjectType.INSTRUMENT, None, EngineeringLifecycle.ACTIVE,
        EngineeringAuthorityStanding.APPROVED, 7, 8,
    )
    relationship = EngineeringRelationshipHistoricalBasisV1(
        1, "engineering_relationship", uuid4(), 5, organization, 11, 12,
        object_id, other_object_id, RelationshipFamily.PHYSICAL,
        RelationshipType.CONNECTED_TO, EngineeringRelationshipLifecycle.CURRENT,
        EngineeringAuthorityStanding.APPROVED, (), 7, 8, None, None,
    )
    provenance = (
        _entry(capture, 0, TechnicalReportSourceType.UNIVERSAL_CAPTURE,
               TechnicalReportOwningCapability.UNIVERSAL_CAPTURE),
        _entry(evidence, 1, TechnicalReportSourceType.EVIDENCE,
               TechnicalReportOwningCapability.EVIDENCE),
        _entry(engineering_object, 2, TechnicalReportSourceType.ENGINEERING_OBJECT,
               TechnicalReportOwningCapability.ENGINEERING_OBJECT),
        _entry(relationship, 3, TechnicalReportSourceType.ENGINEERING_RELATIONSHIP,
               TechnicalReportOwningCapability.ENGINEERING_RELATIONSHIP),
    )
    snapshot = TechnicalReportAcceptedSnapshot(
        report_id, TechnicalReportPurpose.ENGINEERING_ANALYSIS, organization,
        12, 11,
        TechnicalReportContent(
            "scope", "technical content", ("assumption",), "uncertainty",
            ("limitation",), "conclusion", ("recommendation",),
        ), PreliminaryQualification(False), provenance,
        TechnicalReportDraftRevision(uuid4(), 2), 6, 7, NOW, None,
    )
    return snapshot, (capture, evidence, engineering_object, relationship)


def source_reader(snapshot):
    view = SimpleNamespace(
        id=snapshot.report_id, organization_id=snapshot.organization_id,
        workspace_id=snapshot.workspace_id, project_id=snapshot.project_id,
        owner_id=7, lifecycle=TechnicalReportLifecycle.ACCEPTED,
        version=snapshot.accepted_aggregate_version,
        accepted_snapshot=snapshot,
    )
    service = RecordingService(view)
    return TechnicalReportAcceptedSourceAdapter(service), service


def provenance_request(snapshot, locators):
    capture, evidence, engineering_object, relationship = locators
    entries = snapshot.provenance
    items = (
        CaptureProvenanceAuthorization(
            entries[0].entry_id, 0, capture.capture_id, capture.source_version,
            capture.organization_id, capture.project_id, capture.workspace_id,
            capture.engineering_object_id,
        ),
        EvidenceProvenanceAuthorization(
            entries[1].entry_id, 1, evidence.evidence_id,
            evidence.source_version, evidence.organization_id,
            evidence.project_id, evidence.workspace_id,
        ),
        EngineeringObjectProvenanceAuthorization(
            entries[2].entry_id, 2, engineering_object.engineering_object_id,
            engineering_object.source_version, engineering_object.organization_id,
            engineering_object.project_id, engineering_object.workspace_id,
        ),
        EngineeringRelationshipProvenanceAuthorization(
            entries[3].entry_id, 3,
            relationship.engineering_relationship_id,
            relationship.source_version, relationship.organization_id,
            relationship.project_id, relationship.workspace_id,
            relationship.source_object_id, relationship.target_object_id,
        ),
    )
    return MemoryProvenanceAuthorizationRequest(
        MemoryActor(9, snapshot.organization_id), MemoryProvenanceOperation.ADMIT,
        MemoryScope(snapshot.organization_id, 12, 11),
        AcceptedReportSource(
            snapshot.report_id, snapshot.accepted_aggregate_version,
            snapshot.integrity_digest,
        ), items,
    )


def canonical_services(locators):
    capture, evidence, engineering_object, relationship = locators
    return (
        RecordingService(SimpleNamespace(
            id=capture.capture_id, project_id=11, workspace_id=12,
            engineering_object_id=capture.engineering_object_id,
        )),
        RecordingService(SimpleNamespace(
            id=evidence.evidence_id, organization_id=evidence.organization_id,
            project_id=11, workspace_id=12,
        )),
        RecordingService(SimpleNamespace(
            id=engineering_object.engineering_object_id,
            organization_id=engineering_object.organization_id,
            project_id=11, workspace_id=12,
        )),
        RecordingService(SimpleNamespace(
            id=relationship.engineering_relationship_id,
            organization_id=relationship.organization_id,
            project_id=11, workspace_id=12,
            source_object_id=relationship.source_object_id,
            target_object_id=relationship.target_object_id,
        )),
    )


def authorizer(snapshot, locators, services=None):
    reader, report_service = source_reader(snapshot)
    services = services or canonical_services(locators)
    return CanonicalMemoryProvenanceAuthorizer(
        accepted_reports=reader, captures=services[0], evidence=services[1],
        engineering_objects=services[2],
        engineering_relationships=services[3],
    ), report_service, services


def test_accepted_source_preserves_exact_identity_scope_version_and_digests():
    snapshot, _ = accepted_fixture(); reader, service = source_reader(snapshot)
    source = AcceptedReportSource(
        snapshot.report_id, snapshot.accepted_aggregate_version,
        snapshot.integrity_digest,
    )
    result = reader.read_authorized_accepted(
        MemoryActor(9, snapshot.organization_id), source,
    )
    assert isinstance(result, AcceptedReportProjection)
    assert result.source == source
    assert result.scope == MemoryScope(snapshot.organization_id, 12, 11)
    projection, manifest = admission_material_from_snapshot(result.snapshot)
    assert manifest.source_snapshot_digest == snapshot.integrity_digest
    assert manifest.admitted_projection_digest == sha256(
        memory_canonical_json(projection)
    ).hexdigest()
    assert len(service.calls) == 1


def test_source_adapter_calls_the_actual_technical_report_application_service():
    snapshot, _ = accepted_fixture()
    report = SimpleNamespace(
        id=snapshot.report_id, organization_id=snapshot.organization_id,
        workspace_id=snapshot.workspace_id, project_id=snapshot.project_id,
        owner_id=7, lifecycle=TechnicalReportLifecycle.ACCEPTED,
        version=snapshot.accepted_aggregate_version,
        accepted_snapshot=snapshot,
    )

    class Repository:
        def get_scoped(self, report_id, organization_id):
            if report_id == report.id and organization_id == report.organization_id:
                return report
            return None

    class Authorization:
        def __init__(self): self.requests = []
        def require(self, request): self.requests.append(request)

    class Uow:
        technical_reports = Repository()
        authorization = Authorization()
        def __enter__(self): return self
        def __exit__(self, *_): return None

    class Clock:
        def now(self): return NOW

    canonical_service = TechnicalReportService(lambda: Uow(), Clock())
    adapter = TechnicalReportAcceptedSourceAdapter(canonical_service)
    result = adapter.read_authorized_accepted(
        MemoryActor(9, snapshot.organization_id),
        AcceptedReportSource(
            snapshot.report_id, snapshot.accepted_aggregate_version,
            snapshot.integrity_digest,
        ),
    )
    assert isinstance(result, AcceptedReportProjection)
    assert [request.operation for request in Uow.authorization.requests] == [
        "get", "create_successor",
    ]


def test_all_four_provenance_classes_use_exact_canonical_service_calls():
    snapshot, locators = accepted_fixture(); request = provenance_request(snapshot, locators)
    adapter, report_service, services = authorizer(snapshot, locators)
    result = adapter.authorize_and_resolve(request)
    assert isinstance(result, ProvenanceAuthorized)
    assert [(item.entry_id, item.ordinal) for item in result.items] == [
        (item.entry_id, item.ordinal) for item in request.items
    ]
    assert len(report_service.calls) == 1
    assert [len(service.calls) for service in services] == [1, 1, 1, 1]
    capture_call = services[0].calls[0][1]
    assert capture_call["project_id"] == 11 and capture_call["workspace_id"] == 12
    assert capture_call["engineering_object_id"] == locators[0].engineering_object_id
    assert isinstance(capture_call["actor"], EngineeringExperienceCaptureActor)
    for service, identity in zip(services[1:], (
        locators[1].evidence_id, locators[2].engineering_object_id,
        locators[3].engineering_relationship_id,
    )):
        assert service.calls[0][0][0] == identity
    assert isinstance(services[1].calls[0][0][1], EvidenceActor)
    assert isinstance(services[2].calls[0][0][1], AuthenticatedActor)
    assert services[2].calls[0][0][2] == AuthorizationContext(
        "ReadEngineeringObject", {"object_id": locators[2].engineering_object_id},
    )
    assert isinstance(
        services[3].calls[0][0][1], AuthenticatedRelationshipActor,
    )
    assert services[3].calls[0][0][2] == RelationshipAuthorizationContext(
        "ReadEngineeringRelationship",
        {"relationship_id": locators[3].engineering_relationship_id},
    )


def test_resolved_provenance_is_digest_only_and_deterministically_ordered():
    snapshot, locators = accepted_fixture(); request = provenance_request(snapshot, locators)
    adapter, _, _ = authorizer(snapshot, locators)
    result = adapter.authorize_and_resolve(request)
    assert isinstance(result, ProvenanceAuthorized)
    assert tuple(item.ordinal for item in result.items) == (0, 1, 2, 3)
    assert all(item.locator_digest for item in result.items)
    representation = repr(result)
    assert "source body" not in representation
    assert "supported fact" not in representation
    assert "technical content" not in representation


class EchoCaptureService(RecordingService):
    def read_authorized_detail(self, **kwargs):
        self.calls.append(((), kwargs))
        return SimpleNamespace(
            id=kwargs["capture_id"], project_id=kwargs["project_id"],
            workspace_id=kwargs["workspace_id"],
            engineering_object_id=kwargs["engineering_object_id"],
        )


def capture_only_fixture(count):
    organization = uuid4(); report_id = uuid4(); entries = []; locators = []
    for ordinal in range(count):
        locator = CaptureHistoricalBasisV1(
            1, "universal_capture", uuid4(), 1, organization, 11, 12,
            EngineeringDiscipline.INSTRUMENTATION, None,
            EngineeringExperienceSourceKind.OBSERVATION, "source", None, 7,
            EngineeringExperienceCaptureLifecycle.CAPTURED, NOW,
        )
        locators.append(locator)
        entries.append(_entry(
            locator, ordinal, TechnicalReportSourceType.UNIVERSAL_CAPTURE,
            TechnicalReportOwningCapability.UNIVERSAL_CAPTURE,
        ))
    snapshot = TechnicalReportAcceptedSnapshot(
        report_id, TechnicalReportPurpose.ENGINEERING_ANALYSIS, organization,
        12, 11, TechnicalReportContent(
            "scope", "technical content", (), "uncertainty", (),
            "conclusion", (),
        ), PreliminaryQualification(False), tuple(entries),
        TechnicalReportDraftRevision(uuid4(), 1), 2, 7, NOW, None,
    )
    items = tuple(
        CaptureProvenanceAuthorization(
            entry.entry_id, ordinal, locator.capture_id, locator.source_version,
            organization, 11, 12, None,
        )
        for ordinal, (entry, locator) in enumerate(zip(entries, locators, strict=True))
    )
    return snapshot, items


def request_batches(snapshot, items, sizes):
    actor = MemoryActor(9, snapshot.organization_id)
    scope = MemoryScope(snapshot.organization_id, 12, 11)
    source = AcceptedReportSource(
        snapshot.report_id, snapshot.accepted_aggregate_version,
        snapshot.integrity_digest,
    )
    batches = []; offset = 0
    for size in sizes:
        batches.append(MemoryProvenanceAuthorizationRequest(
            actor, MemoryProvenanceOperation.ADMIT, scope, source,
            items[offset:offset + size],
        ))
        offset += size
    return tuple(batches)


def capture_only_authorizer(snapshot):
    reader, _ = source_reader(snapshot); captures = EchoCaptureService()
    unused = RecordingService()
    adapter = CanonicalMemoryProvenanceAuthorizer(
        accepted_reports=reader, captures=captures, evidence=unused,
        engineering_objects=unused, engineering_relationships=unused,
    )
    return adapter, captures


def test_logical_operation_accepts_256_in_three_batches_in_canonical_order():
    snapshot, items = capture_only_fixture(256)
    requests = request_batches(snapshot, items, (100, 100, 56))
    adapter, captures = capture_only_authorizer(snapshot)
    result = adapter.authorize_logical_operation(requests)
    assert isinstance(result, ProvenanceAuthorized)
    assert tuple(item.ordinal for item in result.items) == tuple(range(256))
    assert len(captures.calls) == 256


def test_logical_operation_rejects_257_or_a_fourth_request_before_reads():
    snapshot, items = capture_only_fixture(257)
    requests = request_batches(snapshot, items, (100, 100, 57))
    adapter, captures = capture_only_authorizer(snapshot)
    from app.models.organizational_memory_command import ProvenanceProtectedNotFound
    assert isinstance(
        adapter.authorize_logical_operation(requests),
        ProvenanceProtectedNotFound,
    )
    assert not captures.calls

    snapshot, items = capture_only_fixture(1)
    one = request_batches(snapshot, items, (1,))[0]
    adapter, captures = capture_only_authorizer(snapshot)
    assert isinstance(
        adapter.authorize_logical_operation((one, one, one, one)),
        ProvenanceProtectedNotFound,
    )
    assert not captures.calls


def test_logical_operation_deduplicates_across_requests_and_keeps_order():
    snapshot, items = capture_only_fixture(100)
    first = request_batches(snapshot, items, (100,))[0]
    duplicate = request_batches(snapshot, items[:1], (1,))[0]
    adapter, captures = capture_only_authorizer(snapshot)
    result = adapter.authorize_logical_operation((duplicate, first))
    assert isinstance(result, ProvenanceAuthorized)
    assert tuple(item.ordinal for item in result.items) == tuple(range(100))
    assert len(captures.calls) == 100


def test_per_request_limit_is_exactly_100():
    snapshot, items = capture_only_fixture(101)
    request_batches(snapshot, items[:100], (100,))
    with pytest.raises(OrganizationalMemoryValidationError):
        request_batches(snapshot, items, (101,))


def test_accepted_but_unsupported_provenance_is_admission_ineligible():
    snapshot, _ = accepted_fixture()
    locator = ExternalHumanLocator(
        uuid4(), "external-reference", 7, NOW, None, None, "external body",
    )
    unsupported = TechnicalReportProvenanceEntry(
        uuid4(), 0, TechnicalReportSourceClass.EXTERNAL_OR_HUMAN_MATERIAL,
        TechnicalReportSourceType.EXTERNAL_OR_HUMAN, True, None,
        "external basis", TechnicalReportVerificationStatus.VERIFIED,
        TechnicalReportAvailabilityStatus.AVAILABLE, "Human", (), locator,
        TechnicalReportIntegrityAlgorithm.SHA256,
        sha256(canonical_json(locator)).hexdigest(),
    )
    snapshot = replace(snapshot, provenance=(unsupported,))
    reader, _ = source_reader(snapshot)
    with pytest.raises(OrganizationalMemoryValidationError):
        reader.read_authorized_accepted(
            MemoryActor(9, snapshot.organization_id),
            AcceptedReportSource(
                snapshot.report_id, snapshot.accepted_aggregate_version,
                snapshot.integrity_digest,
            ),
        )


class ActualPolicy:
    def __init__(self, allowed=True): self.allowed = allowed; self.calls = []
    def authorize(self, **kwargs):
        self.calls.append(kwargs)
        return self.allowed
    def project_list_workspace_scope(self, **kwargs):
        self.calls.append(kwargs)
        return (12,) if self.allowed else ()


class ActualContext:
    def __init__(self): self.calls = []
    def validate(self, **kwargs):
        self.calls.append(kwargs)
        return SimpleNamespace(**kwargs)


class ActualReadRepository:
    def __init__(self, item): self.item = item; self.calls = []
    def get_scoped(self, identity, organization_id):
        self.calls.append((identity, organization_id))
        return self.item if (
            identity == self.item.id
            and organization_id == self.item.organization_id
        ) else None
    def get_authorized(self, identity, organization_id):
        return self.get_scoped(identity, organization_id)


class ActualReadUow:
    def __init__(self, attribute, item, *, policy=None, context=None):
        setattr(self, attribute, ActualReadRepository(item))
        if policy is not None: self.authorization = policy
        if context is not None: self.context = context
    def __enter__(self): return self
    def __exit__(self, *_): return None


def actual_canonical_services(locators, *, denied=None):
    capture, evidence, engineering_object, relationship = locators
    capture_row = EngineeringExperienceCapture(
        id=capture.capture_id, organization_id=capture.organization_id,
        project_id=capture.project_id, workspace_id=capture.workspace_id,
        discipline=capture.discipline.value,
        engineering_object_id=capture.engineering_object_id,
        source_kind=capture.source_kind.value, original_content="source body",
        source_reference=None, creator_id=7, lifecycle="captured",
        superseded_by_capture_id=None, version=9, created_at=NOW, updated_at=NOW,
    )
    evidence_row = Evidence(
        id=evidence.evidence_id, organization_id=evidence.organization_id,
        project_id=evidence.project_id, workspace_id=evidence.workspace_id,
        lifecycle=evidence.lifecycle.value, source_kind=evidence.source_kind.value,
        source_reference=evidence.source_reference,
        source_revision=evidence.source_revision,
        source_standing=evidence.source_standing.value,
        effective_at=evidence.effective_at, supported_fact=evidence.supported_fact,
        creator_id=evidence.creator_id, version=9, created_at=NOW, updated_at=NOW,
    )
    object_row = EngineeringObject(
        id=engineering_object.engineering_object_id,
        organization_id=engineering_object.organization_id,
        customer_id=engineering_object.customer_id,
        project_id=engineering_object.project_id,
        workspace_id=engineering_object.workspace_id,
        family=engineering_object.family.value,
        discipline=engineering_object.discipline.value,
        object_type=engineering_object.object_type.value, subtype=None,
        lifecycle=engineering_object.lifecycle.value,
        authority_standing=engineering_object.authority_standing.value,
        version=9, creator_id=engineering_object.creator_id,
        steward_id=engineering_object.steward_id,
        created_at=NOW, updated_at=NOW,
    )
    relationship_row = EngineeringRelationship(
        id=relationship.engineering_relationship_id,
        organization_id=relationship.organization_id,
        project_id=relationship.project_id,
        workspace_id=relationship.workspace_id,
        source_object_id=relationship.source_object_id,
        target_object_id=relationship.target_object_id,
        relationship_family=relationship.relationship_family.value,
        relationship_type=relationship.relationship_type.value,
        lifecycle=relationship.lifecycle.value,
        authority_standing=relationship.authority_standing.value,
        evidence_references=[], version=9, creator_id=relationship.creator_id,
        steward_id=relationship.steward_id, reviewer_id=None, approver_id=None,
        created_at=NOW, updated_at=NOW,
    )
    policies = {
        name: ActualPolicy(allowed=name != denied)
        for name in ("capture", "evidence", "object", "relationship")
    }
    context = ActualContext()
    capture_service = EngineeringExperienceCaptureService(
        uow_factory=lambda: ActualReadUow(
            "captures", capture_row, policy=policies["capture"], context=context,
        ),
    )
    evidence_service = EvidenceService(
        uow_factory=lambda: ActualReadUow("evidence", evidence_row),
        authorization=policies["evidence"], validator=SimpleNamespace(),
        clock=SimpleNamespace(),
    )
    object_service = EngineeringObjectService(
        uow_factory=lambda: ActualReadUow("engineering_objects", object_row),
        authorization=policies["object"], references=SimpleNamespace(),
        clock=SimpleNamespace(),
    )
    relationship_service = EngineeringRelationshipService(
        uow_factory=lambda: ActualReadUow(
            "engineering_relationships", relationship_row,
        ), authorization=policies["relationship"],
        validator=SimpleNamespace(), clock=SimpleNamespace(),
    )
    return (
        capture_service, evidence_service, object_service, relationship_service,
    ), policies, context


def test_actual_four_canonical_application_services_authorize_exact_contexts():
    snapshot, locators = accepted_fixture()
    services, policies, context = actual_canonical_services(locators)
    adapter, _, _ = authorizer(snapshot, locators, services)
    result = adapter.authorize_and_resolve(provenance_request(snapshot, locators))
    assert isinstance(result, ProvenanceAuthorized)
    assert context.calls[0]["project_id"] == 11
    assert context.calls[0]["workspace_id"] == 12
    assert any(call.get("operation") == "read" for call in policies["capture"].calls)
    assert policies["evidence"].calls[0]["operation"] == "ReadEvidence"
    assert policies["evidence"].calls[0]["actor"].organization_id == snapshot.organization_id
    assert policies["evidence"].calls[0]["project_id"] == 11
    assert policies["evidence"].calls[0]["workspace_id"] == 12
    assert policies["object"].calls[0]["context"].operation == "ReadEngineeringObject"
    assert policies["object"].calls[0]["actor"].organization_id == snapshot.organization_id
    assert policies["object"].calls[0]["current_state"].workspace_id == 12
    assert (
        policies["relationship"].calls[0]["context"].operation
        == "ReadEngineeringRelationship"
    )
    assert (
        policies["relationship"].calls[0]["actor"].organization_id
        == snapshot.organization_id
    )
    assert policies["relationship"].calls[0]["current_state"].project_id == 11


def test_inward_port_preserves_single_request_and_adds_stateless_logical_operation():
    methods = {
        name for name, value in MemoryProvenanceAuthorizer.__dict__.items()
        if callable(value) and not name.startswith("_")
    }
    assert methods == {"authorize_and_resolve", "authorize_logical_operation"}


def test_memory_reads_continue_to_use_only_canonical_application_adapters():
    from app.models.organizational_memory_command import GetActiveMemory
    from test_organizational_memory_service import admit_command, setup
    service, _, _, snapshot = setup(); actor = MemoryActor(9, snapshot.organization_id)
    admitted = service.admit(admit_command(snapshot))
    calls_before = len(service.accepted_reports._technical_reports.calls)
    result = service.get_active(actor, GetActiveMemory(admitted.memory_id, True))
    assert result.outcome == "success"
    assert len(service.accepted_reports._technical_reports.calls) == calls_before + 1
    assert result.item.safe_provenance
