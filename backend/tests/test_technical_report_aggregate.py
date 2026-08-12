"""PATCH-032 Batch 1 Technical Report Aggregate tests."""

from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest

from app.enums.technical_report import (
    TechnicalReportAvailabilityStatus,
    TechnicalReportIntegrityAlgorithm,
    TechnicalReportLifecycle,
    TechnicalReportPurpose,
    TechnicalReportSourceClass,
    TechnicalReportSourceType,
    TechnicalReportVerificationStatus,
)
from app.exceptions.technical_report import (
    TechnicalReportAcceptedImmutable,
    TechnicalReportAuthorizationDenied,
    TechnicalReportInvalidLifecycle,
    TechnicalReportValidationError,
    TechnicalReportVersionConflict,
)
from app.models.technical_report import TechnicalReport
from app.models.technical_report_command import (
    AcceptExactTechnicalReportDraft,
    AcceptanceConfirmation,
    CaptureHistoricalBasisV1,
    CreateTechnicalReportDraft,
    CreateTechnicalReportSuccessor,
    PreliminaryQualification,
    ReviseTechnicalReportDraft,
    TechnicalReportActor,
    TechnicalReportCommandMetadata,
    TechnicalReportContent,
    TechnicalReportDomainEvent,
    TechnicalReportProvenanceEntry,
    historical_basis_digest,
)


NOW = datetime(2026, 8, 9, 8, 0, tzinfo=timezone.utc)


def metadata(actor_id: int = 7, organization_id=None):
    return TechnicalReportCommandMetadata(
        actor=TechnicalReportActor(actor_id, organization_id or uuid4()),
        rationale="Human engineering rationale",
        correlation_id=uuid4(),
        idempotency_id=uuid4(),
        command_id=uuid4(),
    )


def content(text: str = "Engineering analysis") -> TechnicalReportContent:
    return TechnicalReportContent(
        engineering_scope="Motor control system",
        technical_content=text,
        assumptions=("Supply remains available",),
        uncertainty="Field measurement tolerance remains",
        limitations=("One operating state observed",),
        conclusions="The observed behavior is reproducible",
        recommendations=("Verify protection settings",),
    )


def material_entry(organization_id):
    basis = CaptureHistoricalBasisV1(
        basis_schema_version=1,
        source_category="universal_capture",
        capture_id=uuid4(),
        source_version=2,
        organization_id=organization_id,
        project_id=11,
        workspace_id=12,
        discipline="electrical",
        engineering_object_id=uuid4(),
        source_kind="observation",
        original_content="Measured contactor chatter",
        source_reference="field-note-7",
        creator_id=7,
        lifecycle="captured",
        created_at=NOW,
    )
    return TechnicalReportProvenanceEntry(
        entry_id=uuid4(),
        ordinal=0,
        source_class=TechnicalReportSourceClass.CANONICAL_MATERIAL,
        source_type=TechnicalReportSourceType.UNIVERSAL_CAPTURE,
        is_material=True,
        owning_capability="universal_capture",
        reliance_role="primary observation",
        verification_status=TechnicalReportVerificationStatus.VERIFIED,
        availability_status=TechnicalReportAvailabilityStatus.AVAILABLE,
        origin_attribution="Authenticated field engineer",
        limitations=(),
        locator=basis,
        integrity_algorithm=TechnicalReportIntegrityAlgorithm.SHA256,
        integrity_digest=historical_basis_digest(basis),
    )


def create_report(purpose=TechnicalReportPurpose.ENGINEERING_ANALYSIS):
    meta = metadata()
    command = CreateTechnicalReportDraft(
        metadata=meta,
        organization_id=meta.actor.organization_id,
        workspace_id=12,
        project_id=11,
        owner_id=meta.actor.actor_id,
        purpose=purpose,
        content=content(),
        qualification=PreliminaryQualification(False),
        provenance=(material_entry(meta.actor.organization_id),),
    )
    return TechnicalReport.create(command, NOW)[0]


@pytest.mark.parametrize("purpose", list(TechnicalReportPurpose))
def test_create_valid_draft_for_every_purpose(purpose):
    report = create_report(purpose)
    assert report.lifecycle == TechnicalReportLifecycle.DRAFT.value
    assert report.purpose == purpose.value
    assert report.version == 1
    assert report.owner_id == 7
    assert report.accepted_snapshot is None


def test_revise_draft_advances_version_and_revision_exactly_once():
    report = create_report()
    previous_revision = report.draft_revision_id
    meta = metadata(report.owner_id, report.organization_id)
    result = report.revise(
        ReviseTechnicalReportDraft(
            metadata=meta,
            report_id=report.id,
            expected_version=1,
            expected_draft_revision_id=previous_revision,
            content=content("Revised engineering analysis"),
            qualification=report.qualification,
            provenance=report.provenance,
        ),
        NOW + timedelta(minutes=1),
    )
    assert result.previous_version == 1
    assert report.version == 2
    assert report.draft_revision_id != previous_revision


def test_accept_exact_draft_creates_terminal_immutable_snapshot():
    report = create_report()
    meta = metadata(report.owner_id, report.organization_id)
    result = report.accept_exact_draft(
        AcceptExactTechnicalReportDraft(
            metadata=meta,
            report_id=report.id,
            confirmation=AcceptanceConfirmation(1, report.draft_revision_id, True),
        ),
        NOW + timedelta(minutes=2),
    )
    assert report.lifecycle == TechnicalReportLifecycle.ACCEPTED.value
    assert result.version == 2
    assert report.accepted_snapshot.content == report.content
    assert report.accepted_snapshot.organization_id == report.organization_id
    assert report.accepted_snapshot.workspace_id == report.workspace_id
    assert report.accepted_snapshot.project_id == report.project_id
    assert len(report.accepted_snapshot.integrity_digest) == 64
    assert report.accepted_snapshot.integrity_digest == report.accepted_snapshot.integrity_digest
    assert report.acceptance_record.accepted_by_id == report.owner_id
    with pytest.raises(TechnicalReportAcceptedImmutable):
        report.revise(
            ReviseTechnicalReportDraft(meta, report.id, 2, report.draft_revision_id, content("Forbidden"), report.qualification, report.provenance),
            NOW + timedelta(minutes=3),
        )
    with pytest.raises(AttributeError):
        report.accepted_snapshot.accepted_by_id = 99


def test_acceptance_requires_owner_exact_version_revision_and_confirmation():
    report = create_report()
    wrong_actor = metadata(8, report.organization_id)
    with pytest.raises(TechnicalReportAuthorizationDenied):
        report.accept_exact_draft(AcceptExactTechnicalReportDraft(wrong_actor, report.id, AcceptanceConfirmation(1, report.draft_revision_id, True)), NOW)
    owner = metadata(report.owner_id, report.organization_id)
    with pytest.raises(TechnicalReportVersionConflict):
        report.accept_exact_draft(AcceptExactTechnicalReportDraft(owner, report.id, AcceptanceConfirmation(2, report.draft_revision_id, True)), NOW)
    assert report.lifecycle == TechnicalReportLifecycle.DRAFT.value


def test_invalid_lifecycle_transition_is_rejected():
    report = create_report()
    with pytest.raises(AttributeError):
        report.lifecycle = "published"


@pytest.mark.parametrize(
    "field,value",
    [
        ("purpose", TechnicalReportPurpose.FIELD_EXPERIENCE),
        ("owner_id", 99),
        ("organization_id", uuid4()),
        ("workspace_id", 99),
        ("project_id", 99),
        ("draft_content", "bypass"),
        ("provenance", ()),
        ("draft_revision_id", uuid4()),
        ("version", 99),
        ("accepted_by_id", 99),
        ("accepted_snapshot", None),
    ],
)
@pytest.mark.parametrize("accepted", [False, True])
def test_aggregate_owned_state_has_no_public_assignment_boundary(field, value, accepted):
    report = create_report()
    if accepted:
        meta = metadata(report.owner_id, report.organization_id)
        report.accept_exact_draft(AcceptExactTechnicalReportDraft(meta, report.id, AcceptanceConfirmation(1, report.draft_revision_id, True)), NOW)
    with pytest.raises(AttributeError):
        setattr(report, field, value)


def test_successor_has_new_draft_identity_without_mutating_predecessor():
    predecessor = create_report()
    meta = metadata(predecessor.owner_id, predecessor.organization_id)
    predecessor.accept_exact_draft(AcceptExactTechnicalReportDraft(meta, predecessor.id, AcceptanceConfirmation(1, predecessor.draft_revision_id, True)), NOW)
    predecessor_state = (predecessor.id, predecessor.version, predecessor.lifecycle, predecessor.accepted_snapshot)
    successor, _ = predecessor.create_successor(
        CreateTechnicalReportSuccessor(
            metadata=meta,
            predecessor_report_id=predecessor.id,
            expected_predecessor_version=2,
            workspace_id=predecessor.workspace_id,
            project_id=predecessor.project_id,
            purpose=TechnicalReportPurpose.TECHNICAL_RECOMMENDATION,
            content=content("New successor analysis"),
            qualification=PreliminaryQualification(False),
            provenance=predecessor.provenance,
        ),
        NOW + timedelta(minutes=5),
    )
    assert successor.id != predecessor.id
    assert successor.predecessor_report_id == predecessor.id
    assert successor.lifecycle == TechnicalReportLifecycle.DRAFT.value
    assert successor.accepted_snapshot is None
    assert (predecessor.id, predecessor.version, predecessor.lifecycle, predecessor.accepted_snapshot) == predecessor_state
    assert not hasattr(successor, "supersede")


def test_no_generic_or_post_acceptance_commands_exist():
    report = create_report()
    for operation in ("update", "delete", "publish", "approve", "supersede", "archive"):
        assert not hasattr(report, operation)


def test_commands_return_minimal_typed_domain_events():
    meta = metadata()
    report, result = TechnicalReport.create(
        CreateTechnicalReportDraft(meta, meta.actor.organization_id, 12, 11, meta.actor.actor_id, TechnicalReportPurpose.ENGINEERING_ANALYSIS, content(), PreliminaryQualification(False), (material_entry(meta.actor.organization_id),)), NOW
    )
    assert len(result.events) == 1
    event = result.events[0]
    assert event.report_id == report.id
    assert event.aggregate_version == report.version
    assert event.organization_id == report.organization_id
    assert event.workspace_id == report.workspace_id
    assert event.project_id == report.project_id
    assert event.purpose == report.purpose
    assert event.lifecycle == report.lifecycle
    assert event.draft_revision_id == report.draft_revision_id
    assert event.actor_id == report.owner_id
    assert event.causation_id == meta.command_id
    assert event.predecessor_report_id is None
    assert event.source_entry_count == len(report.provenance)
    assert not hasattr(event, "technical_content")
    assert not hasattr(event, "provenance")


def test_all_command_events_are_scope_and_state_coherent():
    report = create_report()
    meta = metadata(report.owner_id, report.organization_id)
    revised = report.revise(
        ReviseTechnicalReportDraft(
            meta, report.id, 1, report.draft_revision_id,
            content("revised"), report.qualification, report.provenance,
        ), NOW + timedelta(minutes=1)
    ).events[0]
    assert (revised.lifecycle, revised.aggregate_version, revised.draft_revision_id) == (
        "draft", report.version, report.draft_revision_id
    )
    accepted = report.accept_exact_draft(
        AcceptExactTechnicalReportDraft(
            meta, report.id,
            AcceptanceConfirmation(report.version, report.draft_revision_id, True),
        ), NOW + timedelta(minutes=2)
    ).events[0]
    assert accepted.lifecycle == "accepted"
    successor, result = report.create_successor(
        CreateTechnicalReportSuccessor(
            meta, report.id, report.version, report.workspace_id, report.project_id,
            report.purpose, content("successor"), report.qualification,
            report.provenance,
        ), NOW + timedelta(minutes=3)
    )
    event = result.events[0]
    assert event.report_id == successor.id
    assert event.predecessor_report_id == report.id
    assert event.lifecycle == "draft"
    assert set(event.__dataclass_fields__) == {
        "event_id", "report_id", "aggregate_version", "event_type", "command_id",
        "correlation_id", "occurred_at", "organization_id", "workspace_id",
        "project_id", "purpose", "lifecycle", "draft_revision_id", "actor_id",
        "causation_id", "predecessor_report_id", "source_entry_count",
    }


def test_all_commands_emit_exact_closed_ids_event_types():
    meta = metadata()
    report, created_result = TechnicalReport.create(
        CreateTechnicalReportDraft(
            meta, meta.actor.organization_id, 12, 11, meta.actor.actor_id,
            TechnicalReportPurpose.ENGINEERING_ANALYSIS, content(),
            PreliminaryQualification(False),
            (material_entry(meta.actor.organization_id),),
        ),
        NOW,
    )
    revised = report.revise(
        ReviseTechnicalReportDraft(
            meta, report.id, report.version, report.draft_revision_id,
            content("Revised exact event contract"), report.qualification,
            report.provenance,
        ),
        NOW + timedelta(minutes=1),
    ).events[0]
    accepted = report.accept_exact_draft(
        AcceptExactTechnicalReportDraft(
            meta, report.id,
            AcceptanceConfirmation(report.version, report.draft_revision_id, True),
        ),
        NOW + timedelta(minutes=2),
    ).events[0]
    successor = report.create_successor(
        CreateTechnicalReportSuccessor(
            meta, report.id, report.version, report.workspace_id,
            report.project_id, report.purpose, content("Successor event"),
            report.qualification, report.provenance,
        ),
        NOW + timedelta(minutes=3),
    )[1].events[0]
    assert tuple(item.event_type for item in (
        created_result.events[0], revised, accepted, successor,
    )) == (
        "TechnicalReportDraftCreated",
        "TechnicalReportDraftRevised",
        "TechnicalReportAccepted",
        "TechnicalReportSuccessorCreated",
    )


def test_domain_event_rejects_noncanonical_event_type():
    report = create_report()
    event = report.revise(
        ReviseTechnicalReportDraft(
            metadata(report.owner_id, report.organization_id), report.id,
            report.version, report.draft_revision_id, content("changed"),
            report.qualification, report.provenance,
        ),
        NOW + timedelta(minutes=1),
    ).events[0]
    values = {field: getattr(event, field) for field in event.__dataclass_fields__}
    values["event_type"] = "technical_report_draft_revised"
    with pytest.raises(TechnicalReportValidationError, match="event_type"):
        TechnicalReportDomainEvent(**values)


def observable_state(report):
    return tuple(getattr(report, name) for name in (
        "id", "organization_id", "workspace_id", "project_id", "owner_id",
        "purpose", "content", "qualification", "provenance", "draft_revision",
        "lifecycle", "predecessor_report_id", "version", "accepted_snapshot",
        "acceptance_record", "created_at", "updated_at",
    ))


def test_failed_revise_event_validation_leaves_complete_state_unchanged():
    report = create_report(); before = observable_state(report)
    meta = metadata(report.owner_id, report.organization_id)
    command = ReviseTechnicalReportDraft(meta, report.id, report.version, report.draft_revision_id, content("candidate"), report.qualification, report.provenance)
    with pytest.raises(TechnicalReportValidationError):
        report.revise(command, datetime(2026, 8, 9, 8, 1))
    assert observable_state(report) == before


def test_failed_acceptance_and_successor_leave_predecessor_unchanged():
    report = create_report(); before = observable_state(report)
    meta = metadata(report.owner_id, report.organization_id)
    with pytest.raises(TechnicalReportValidationError):
        report.accept_exact_draft(AcceptExactTechnicalReportDraft(meta, report.id, AcceptanceConfirmation(1, report.draft_revision_id, True)), datetime(2026, 8, 9))
    assert observable_state(report) == before
    report.accept_exact_draft(AcceptExactTechnicalReportDraft(meta, report.id, AcceptanceConfirmation(1, report.draft_revision_id, True)), NOW)
    accepted = observable_state(report)
    command = CreateTechnicalReportSuccessor(meta, report.id, report.version, report.workspace_id, report.project_id, report.purpose, content("successor"), report.qualification, report.provenance)
    with pytest.raises(TechnicalReportValidationError):
        report.create_successor(command, datetime(2026, 8, 9))
    assert observable_state(report) == accepted


@pytest.mark.parametrize(
    "factory",
    [
        lambda: TechnicalReportActor(1, "not-a-uuid"),
        lambda: TechnicalReportCommandMetadata(TechnicalReportActor(1, uuid4()), "rationale", "bad", uuid4(), uuid4()),
        lambda: AcceptanceConfirmation(1, "bad", True),
        lambda: ReviseTechnicalReportDraft(metadata(), "bad", 1, uuid4(), content(), PreliminaryQualification(False), ()),
        lambda: AcceptExactTechnicalReportDraft(metadata(), "bad", AcceptanceConfirmation(1, uuid4(), True)),
        lambda: CreateTechnicalReportSuccessor(metadata(), "bad", 1, 1, None, TechnicalReportPurpose.ENGINEERING_ANALYSIS, content(), PreliminaryQualification(False), ()),
    ],
)
def test_frozen_contracts_reject_non_uuid_runtime_identities(factory):
    with pytest.raises(TechnicalReportValidationError):
        factory()
