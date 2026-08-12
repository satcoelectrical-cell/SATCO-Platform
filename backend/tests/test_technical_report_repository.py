"""PATCH-032 Batch 3 repository and historical-resolution evidence."""

from datetime import datetime, timezone
from copy import deepcopy
from dataclasses import replace
import hashlib
from uuid import uuid4

import pytest

from app.enums.technical_report import (
    TechnicalReportIntegrityAlgorithm,
    TechnicalReportLifecycle,
    TechnicalReportPurpose,
)
from app.exceptions.technical_report import (
    TechnicalReportHistoricalBasisIncomplete,
    TechnicalReportIntegrityMismatch,
    TechnicalReportValidationError,
)
from app.models.engineering_experience_capture import EngineeringExperienceCapture
from app.models.engineering_object import EngineeringObject
from app.models.engineering_relationship import EngineeringRelationship
from app.models.evidence import Evidence
from app.models.organization import UserOrganizationMembership
from app.models.technical_report import (
    TechnicalReport,
    TechnicalReportProvenanceRecord,
    TechnicalReportRecord,
)
from app.models.technical_report_command import (
    AcceptExactTechnicalReportDraft,
    AcceptanceConfirmation,
    CaptureHistoricalBasisV1,
    CreateTechnicalReportDraft,
    PreliminaryQualification,
    TechnicalReportActor,
    TechnicalReportCommandMetadata,
    TechnicalReportContent,
    TechnicalReportProvenanceEntry,
    canonical_json,
    historical_basis_digest,
)
from app.ports.technical_report import (
    AcceptExactDraftHistoricalAuthority,
    CreateDraftHistoricalAuthority,
    CreateSuccessorHistoricalAuthority,
    ReviseDraftHistoricalAuthority,
    TechnicalReportHistoricalRequest,
    TechnicalReportReadCriteria,
    TechnicalReportScope,
)
from app.repositories.technical_report_repository import SqlAlchemyTechnicalReportRepository
from app.repositories.technical_report_unit_of_work import (
    SqlAlchemyTechnicalReportHistoricalResolver,
)


NOW = datetime(2026, 8, 10, 9, 0, tzinfo=timezone.utc)


def _report(domain, historical_basis=None) -> TechnicalReport:
    actor = domain["actors"]["project_owner"]
    workspace = domain["consumer_workspace"]
    organization_id = domain["project"].organization_id
    metadata = TechnicalReportCommandMetadata(
        TechnicalReportActor(actor.id, organization_id),
        "Engineering rationale", uuid4(), uuid4(), uuid4(),
    )
    basis = historical_basis or CaptureHistoricalBasisV1(
        1, "universal_capture", uuid4(), 1, organization_id,
        domain["project"].id, workspace.id, "electrical", uuid4(),
        "observation", "Observed stable process response", "field-note-1",
        actor.id, "captured", NOW,
    )
    provenance = TechnicalReportProvenanceEntry(
        uuid4(), 0, "canonical_material", "universal_capture", True,
        "universal_capture", "primary observation", "verified", "available",
        "Authenticated engineer", (), basis, TechnicalReportIntegrityAlgorithm.SHA256,
        historical_basis_digest(basis),
    )
    command = CreateTechnicalReportDraft(
        metadata, organization_id, workspace.id, domain["project"].id, actor.id,
        "engineering_analysis",
        TechnicalReportContent(
            "Control system", "Stable engineering analysis", (),
            "Known measurement tolerance", (), "Response is repeatable", (),
        ),
        PreliminaryQualification(False),
        (provenance,),
    )
    return TechnicalReport.create(command, NOW)[0]


def _accept(report: TechnicalReport) -> None:
    metadata = TechnicalReportCommandMetadata(
        TechnicalReportActor(report.owner_id, report.organization_id),
        "Accept exact report", uuid4(), uuid4(), uuid4(),
    )
    report.accept_exact_draft(
        AcceptExactTechnicalReportDraft(
            metadata, report.id,
            AcceptanceConfirmation(report.version, report.draft_revision_id, True),
        ),
        NOW,
    )


def test_repository_add_get_list_and_no_commit(db_session, relationship_domain):
    report = _report(relationship_domain)
    repository = SqlAlchemyTechnicalReportRepository(db_session)
    repository.add(report)
    assert db_session.in_transaction()

    loaded = repository.get_scoped(report.id, report.organization_id)
    assert loaded is not None
    assert loaded.id == report.id
    assert loaded.content == report.content
    assert loaded.provenance == report.provenance
    assert loaded.lifecycle is TechnicalReportLifecycle.DRAFT
    assert loaded.purpose is TechnicalReportPurpose.ENGINEERING_ANALYSIS
    assert type(loaded.purpose) is type(report.purpose)
    assert type(loaded.draft_revision) is type(report.draft_revision)
    assert type(loaded.organization_id) is type(report.organization_id)

    page = repository.list_scoped(TechnicalReportReadCriteria(
        TechnicalReportScope(report.organization_id, report.workspace_id, report.project_id),
        1, 20,
    ))
    assert page.total == 1
    assert page.items[0].report_id == report.id


def test_expected_version_draft_write_is_compare_and_change(db_session, relationship_domain):
    report = _report(relationship_domain)
    repository = SqlAlchemyTechnicalReportRepository(db_session)
    repository.add(report)
    assert repository.persist_draft_expected_version(report, 99) is False
    assert repository.persist_draft_expected_version(report, 1) is True


def test_accepted_read_uses_only_verified_snapshot(db_session, relationship_domain):
    report = _report(relationship_domain)
    repository = SqlAlchemyTechnicalReportRepository(db_session)
    repository.add(report)
    _accept(report)
    assert repository.persist_acceptance_expected_version(report, 1) is True

    root = db_session.get(TechnicalReportRecord, report.id)
    root.draft_content = "A mutable working value that must never be disclosed"
    loaded = repository._accepted(root)
    assert loaded.content.technical_content == "Stable engineering analysis"
    assert loaded.accepted_snapshot == report.accepted_snapshot


def test_accepted_snapshot_digest_and_root_coherence_fail_closed(db_session, relationship_domain):
    report = _report(relationship_domain)
    repository = SqlAlchemyTechnicalReportRepository(db_session)
    repository.add(report)
    _accept(report)
    assert repository.persist_acceptance_expected_version(report, 1)
    root = db_session.get(TechnicalReportRecord, report.id)

    original_digest = root.accepted_snapshot_digest
    root.accepted_snapshot_digest = "0" * 64
    with pytest.raises(TechnicalReportIntegrityMismatch):
        repository._accepted(root)
    root.accepted_snapshot_digest = original_digest
    root.accepted_by_id += 1
    with pytest.raises(TechnicalReportValidationError):
        repository._accepted(root)


def test_draft_corruption_fails_closed(db_session, relationship_domain):
    report = _report(relationship_domain)
    repository = SqlAlchemyTechnicalReportRepository(db_session)
    repository.add(report)
    root = db_session.get(TechnicalReportRecord, report.id)
    root.accepted_snapshot_digest = "0" * 64
    with pytest.raises(TechnicalReportValidationError):
        repository._aggregate(root)


def test_malformed_and_mismatched_provenance_fail_closed(
    db_session, relationship_domain
):
    report = _report(relationship_domain)
    repository = SqlAlchemyTechnicalReportRepository(db_session)
    repository.add(report)
    row = db_session.query(TechnicalReportProvenanceRecord).filter_by(
        technical_report_id=report.id
    ).one()
    row.minimal_historical_representation = {"schema_version": 1}
    with db_session.no_autoflush:
        with pytest.raises(TechnicalReportValidationError):
            repository.provenance_for_report(report.id)
    row.minimal_historical_representation = deepcopy(
        report.provenance[0].locator.__dict__
        if hasattr(report.provenance[0].locator, "__dict__") else {}
    )
    row.source_type = "evidence"
    with db_session.no_autoflush:
        with pytest.raises(TechnicalReportValidationError):
            repository.provenance_for_report(report.id)


def test_invalid_persisted_draft_purpose_fails_closed(db_session, relationship_domain):
    report = _report(relationship_domain)
    repository = SqlAlchemyTechnicalReportRepository(db_session)
    repository.add(report)
    root = db_session.get(TechnicalReportRecord, report.id)
    root.purpose = "invented"
    with db_session.no_autoflush:
        with pytest.raises(ValueError):
            repository._aggregate(root)


@pytest.mark.parametrize("corruption", [
    "report_id", "revision_id", "revision_number", "root_version",
    "root_accepted_version", "snapshot_version", "accepted_by", "accepted_at",
    "malformed_snapshot", "missing_snapshot", "digest", "incomplete_state",
])
def test_complete_accepted_root_snapshot_coherence_fails_closed(
    db_session, relationship_domain, corruption
):
    report = _report(relationship_domain)
    repository = SqlAlchemyTechnicalReportRepository(db_session)
    repository.add(report)
    _accept(report)
    assert repository.persist_acceptance_expected_version(report, 1)
    root = db_session.get(TechnicalReportRecord, report.id)
    payload = deepcopy(root.accepted_snapshot)
    if corruption == "report_id": payload["report_id"] = str(uuid4())
    elif corruption == "revision_id":
        payload["accepted_draft_revision"]["revision_id"] = str(uuid4())
    elif corruption == "revision_number":
        payload["accepted_draft_revision"]["revision_number"] += 1
    elif corruption == "root_version": root.version += 1
    elif corruption == "root_accepted_version": root.accepted_aggregate_version += 1
    elif corruption == "snapshot_version": payload["accepted_aggregate_version"] += 1
    elif corruption == "accepted_by": root.accepted_by_id += 1
    elif corruption == "accepted_at": root.accepted_at = root.accepted_at.replace(year=2025)
    elif corruption == "malformed_snapshot": payload = {"schema_version": 1}
    elif corruption == "missing_snapshot": root.accepted_snapshot = None
    elif corruption == "digest": root.accepted_snapshot_digest = "0" * 64
    elif corruption == "incomplete_state": root.accepted_aggregate_version = None
    if corruption in {
        "report_id", "revision_id", "revision_number", "snapshot_version",
        "malformed_snapshot",
    }:
        root.accepted_snapshot = payload
        root.accepted_snapshot_digest = hashlib.sha256(
            canonical_json(payload)
        ).hexdigest()
    with pytest.raises((TechnicalReportValidationError, TechnicalReportIntegrityMismatch)):
        repository._accepted(root)


def _canonical_sources(db_session, domain):
    org = domain["project"].organization_id
    project = domain["project"]
    workspace = domain["consumer_workspace"]
    actor = domain["actors"]["project_owner"]
    source = EngineeringObject(
        id=uuid4(), organization_id=org, customer_id=project.customer_id,
        project_id=project.id, workspace_id=workspace.id, family="electrical",
        discipline="electrical", object_type="motor", subtype=None,
        lifecycle="active", authority_standing="approved", version=1,
        creator_id=actor.id, steward_id=actor.id,
    )
    target = EngineeringObject(
        id=uuid4(), organization_id=org, customer_id=project.customer_id,
        project_id=project.id, workspace_id=workspace.id, family="electrical",
        discipline="electrical", object_type="motor", subtype=None,
        lifecycle="active", authority_standing="approved", version=1,
        creator_id=actor.id, steward_id=actor.id,
    )
    capture = EngineeringExperienceCapture(
        id=uuid4(), organization_id=org, project_id=project.id,
        workspace_id=workspace.id, discipline="electrical",
        engineering_object_id=source.id, source_kind="observation",
        original_content="Observed condition", source_reference="field-1",
        creator_id=actor.id, lifecycle="captured", version=1,
    )
    evidence = Evidence(
        id=uuid4(), organization_id=org, project_id=project.id,
        workspace_id=workspace.id, lifecycle="current",
        source_kind="engineering_record", source_reference="EV-1",
        source_revision="A", source_standing="current", effective_at=NOW,
        supported_fact="Verified condition", creator_id=actor.id, version=1,
    )
    relationship = EngineeringRelationship(
        id=uuid4(), organization_id=org, project_id=project.id,
        workspace_id=workspace.id, source_object_id=source.id,
        target_object_id=target.id, relationship_family="dependency",
        relationship_type="depends_on", lifecycle="current",
        authority_standing="approved", evidence_references=[str(evidence.id)],
        version=1, creator_id=actor.id, steward_id=actor.id,
    )
    db_session.add_all([source, target, evidence])
    db_session.flush()
    db_session.add_all([capture, relationship])
    db_session.flush()
    return {
        "universal_capture": capture, "evidence": evidence,
        "engineering_object": source, "engineering_relationship": relationship,
        "target": target,
    }


def _historical_request(domain, source_type, item, *, actor_name="project_owner",
                        workspace=None, project_id="default", version=None,
                        authority=None):
    workspace = workspace or domain["consumer_workspace"]
    if project_id == "default":
        project_id = domain["project"].id
    actor = domain["actors"][actor_name]
    organization_id = domain["project"].organization_id
    return TechnicalReportHistoricalRequest(
        TechnicalReportActor(actor.id, organization_id),
        TechnicalReportScope(organization_id, workspace.id, project_id),
        authority or CreateDraftHistoricalAuthority(),
        source_type, item.id if item is not None else uuid4(),
        (item.version if version is None and item is not None else version or 1),
    )


def _persist_report_for_capture(db_session, domain, sources, *, accepted=False):
    resolver = SqlAlchemyTechnicalReportHistoricalResolver(db_session)
    basis = resolver.resolve(_historical_request(
        domain, "universal_capture", sources["universal_capture"]
    ))
    report = _report(domain, basis)
    repository = SqlAlchemyTechnicalReportRepository(db_session)
    repository.add(report)
    if accepted:
        _accept(report)
        assert repository.persist_acceptance_expected_version(report, 1)
    return report


@pytest.mark.parametrize("source_type,result_type", [
    ("universal_capture", "CaptureHistoricalBasisV1"),
    ("evidence", "EvidenceHistoricalBasisV1"),
    ("engineering_object", "EngineeringObjectHistoricalBasisV1"),
    ("engineering_relationship", "EngineeringRelationshipHistoricalBasisV1"),
])
def test_four_closed_historical_resolvers_use_real_scoped_queries(
    db_session, relationship_domain, source_type, result_type
):
    sources = _canonical_sources(db_session, relationship_domain)
    resolver = SqlAlchemyTechnicalReportHistoricalResolver(db_session)
    result = resolver.resolve(_historical_request(
        relationship_domain, source_type, sources[source_type]
    ))
    assert type(result).__name__ == result_type
    assert result.source_version == 1


def test_create_draft_operation_policy_positive_and_negative(
    db_session, relationship_domain
):
    sources = _canonical_sources(db_session, relationship_domain)
    resolver = SqlAlchemyTechnicalReportHistoricalResolver(db_session)
    allowed = _historical_request(
        relationship_domain, "evidence", sources["evidence"],
        authority=CreateDraftHistoricalAuthority(),
    )
    assert resolver.resolve(allowed)
    denied = replace(
        allowed,
        actor=TechnicalReportActor(
            relationship_domain["actors"]["unrelated"].id,
            allowed.actor.organization_id,
        ),
    )
    with pytest.raises(TechnicalReportHistoricalBasisIncomplete) as error:
        resolver.resolve(denied)
    assert error.value.code == "TECHNICAL_REPORT_HISTORICAL_BASIS_INCOMPLETE"


@pytest.mark.parametrize("authority_type", [
    ReviseDraftHistoricalAuthority,
    AcceptExactDraftHistoricalAuthority,
])
def test_owner_only_operation_policy_verifies_target_persistence(
    db_session, relationship_domain, authority_type
):
    sources = _canonical_sources(db_session, relationship_domain)
    report = _persist_report_for_capture(db_session, relationship_domain, sources)
    resolver = SqlAlchemyTechnicalReportHistoricalResolver(db_session)
    authority = authority_type(report.id, report.owner_id)
    allowed = _historical_request(
        relationship_domain, "universal_capture", sources["universal_capture"],
        authority=authority,
    )
    assert resolver.resolve(allowed)
    for actor_name in ("consumer", "admin"):
        denied = _historical_request(
            relationship_domain, "universal_capture",
            sources["universal_capture"], actor_name=actor_name,
            authority=authority,
        )
        with pytest.raises(TechnicalReportHistoricalBasisIncomplete) as error:
            resolver.resolve(denied)
        assert error.value.code == "TECHNICAL_REPORT_HISTORICAL_BASIS_INCOMPLETE"
    mismatched_owner = _historical_request(
        relationship_domain, "universal_capture", sources["universal_capture"],
        authority=authority_type(
            report.id, relationship_domain["actors"]["consumer"].id
        ),
    )
    with pytest.raises(TechnicalReportHistoricalBasisIncomplete):
        resolver.resolve(mismatched_owner)
    missing_target = replace(
        allowed, authority=authority_type(uuid4(), report.owner_id)
    )
    with pytest.raises(TechnicalReportHistoricalBasisIncomplete):
        resolver.resolve(missing_target)


def test_successor_policy_verifies_predecessor_and_each_copied_input(
    db_session, relationship_domain
):
    sources = _canonical_sources(db_session, relationship_domain)
    predecessor = _persist_report_for_capture(
        db_session, relationship_domain, sources, accepted=True
    )
    resolver = SqlAlchemyTechnicalReportHistoricalResolver(db_session)
    authority = CreateSuccessorHistoricalAuthority(predecessor.id, True)
    allowed = _historical_request(
        relationship_domain, "universal_capture", sources["universal_capture"],
        authority=authority,
    )
    assert resolver.resolve(allowed)
    hidden_predecessor = replace(
        allowed, authority=CreateSuccessorHistoricalAuthority(uuid4(), True)
    )
    with pytest.raises(TechnicalReportHistoricalBasisIncomplete):
        resolver.resolve(hidden_predecessor)
    uncopied_input = _historical_request(
        relationship_domain, "evidence", sources["evidence"], authority=authority
    )
    with pytest.raises(TechnicalReportHistoricalBasisIncomplete):
        resolver.resolve(uncopied_input)
    no_copy_authority = replace(
        allowed,
        authority=CreateSuccessorHistoricalAuthority(predecessor.id, False),
    )
    with pytest.raises(TechnicalReportHistoricalBasisIncomplete):
        resolver.resolve(no_copy_authority)
    unauthorized_actor = replace(
        allowed,
        actor=TechnicalReportActor(
            relationship_domain["actors"]["unrelated"].id,
            allowed.actor.organization_id,
        ),
    )
    with pytest.raises(TechnicalReportHistoricalBasisIncomplete):
        resolver.resolve(unauthorized_actor)


@pytest.mark.parametrize("source_type", [
    "universal_capture", "evidence", "engineering_object",
    "engineering_relationship",
])
@pytest.mark.parametrize("denial", [
    "inactive", "unauthorized", "cross_workspace", "cross_project", "stale",
])
def test_historical_resolution_denial_matrix_is_non_disclosing(
    db_session, relationship_domain, source_type, denial
):
    sources = _canonical_sources(db_session, relationship_domain)
    item = sources[source_type]
    values = {}
    if denial == "inactive": values["actor_name"] = "inactive"
    elif denial == "unauthorized": values["actor_name"] = "unrelated"
    elif denial == "cross_workspace": values["workspace"] = relationship_domain["unrelated_workspace"]
    elif denial == "cross_project": values["project_id"] = relationship_domain["other_project"].id
    elif denial == "stale": values["version"] = item.version + 1
    request = _historical_request(relationship_domain, source_type, item, **values)
    resolver = SqlAlchemyTechnicalReportHistoricalResolver(db_session)
    with pytest.raises(TechnicalReportHistoricalBasisIncomplete) as error:
        resolver.resolve(request)
    assert error.value.code == "TECHNICAL_REPORT_HISTORICAL_BASIS_INCOMPLETE"


def test_disabled_membership_and_cross_organization_are_non_disclosing(
    db_session, relationship_domain
):
    sources = _canonical_sources(db_session, relationship_domain)
    request = _historical_request(
        relationship_domain, "universal_capture", sources["universal_capture"]
    )
    membership = db_session.get(
        UserOrganizationMembership,
        (request.actor.actor_id, request.actor.organization_id),
    )
    membership.is_enabled = False
    membership.is_selected = False
    db_session.flush()
    resolver = SqlAlchemyTechnicalReportHistoricalResolver(db_session)
    with pytest.raises(TechnicalReportHistoricalBasisIncomplete):
        resolver.resolve(request)
    cross = TechnicalReportHistoricalRequest(
        request.actor, TechnicalReportScope(uuid4(), request.scope.workspace_id, request.scope.project_id),
        request.authority, request.source_type, request.source_id, request.source_version,
    )
    with pytest.raises(TechnicalReportHistoricalBasisIncomplete):
        resolver.resolve(cross)


@pytest.mark.parametrize("source_type,state_field,bad_value", [
    ("universal_capture", "lifecycle", "withdrawn"),
    ("universal_capture", "lifecycle", "superseded"),
    ("evidence", "lifecycle", "proposed"),
    ("evidence", "source_standing", "draft"),
    ("engineering_object", "lifecycle", "withdrawn"),
    ("engineering_object", "authority_standing", "reviewed"),
    ("engineering_relationship", "lifecycle", "withdrawn"),
    ("engineering_relationship", "authority_standing", "reviewed"),
])
def test_historical_resolution_rejects_unacceptable_source_state(
    db_session, relationship_domain, source_type, state_field, bad_value
):
    sources = _canonical_sources(db_session, relationship_domain)
    item = sources[source_type]
    if source_type == "universal_capture" and bad_value == "superseded":
        replacement = EngineeringExperienceCapture(
            id=uuid4(), organization_id=item.organization_id,
            project_id=item.project_id, workspace_id=item.workspace_id,
            discipline=item.discipline,
            engineering_object_id=item.engineering_object_id,
            source_kind=item.source_kind, original_content="Replacement",
            source_reference="field-2", creator_id=item.creator_id,
            lifecycle="captured", version=1,
        )
        db_session.add(replacement)
        db_session.flush()
        item.superseded_by_capture_id = replacement.id
    setattr(item, state_field, bad_value)
    db_session.flush()
    with pytest.raises(TechnicalReportHistoricalBasisIncomplete):
        SqlAlchemyTechnicalReportHistoricalResolver(db_session).resolve(
            _historical_request(relationship_domain, source_type, item)
        )


def test_relationship_related_resources_are_independently_authorized(
    db_session, relationship_domain
):
    sources = _canonical_sources(db_session, relationship_domain)
    resolver = SqlAlchemyTechnicalReportHistoricalResolver(db_session)
    request = _historical_request(
        relationship_domain, "engineering_relationship",
        sources["engineering_relationship"],
    )
    assert resolver.resolve(request).source_object_id == sources["engineering_object"].id
    sources["target"].workspace_id = relationship_domain["unrelated_workspace"].id
    db_session.flush()
    with pytest.raises(TechnicalReportHistoricalBasisIncomplete):
        resolver.resolve(request)


def test_relationship_evidence_reference_is_independently_authorized(
    db_session, relationship_domain
):
    sources = _canonical_sources(db_session, relationship_domain)
    resolver = SqlAlchemyTechnicalReportHistoricalResolver(db_session)
    request = _historical_request(
        relationship_domain, "engineering_relationship",
        sources["engineering_relationship"],
    )
    assert resolver.resolve(request)
    evidence = sources["evidence"]
    evidence.lifecycle = "withdrawn"
    db_session.flush()
    with pytest.raises(TechnicalReportHistoricalBasisIncomplete):
        resolver.resolve(request)


def test_historical_fallback_matrix_and_integrity(db_session, relationship_domain):
    sources = _canonical_sources(db_session, relationship_domain)
    resolver = SqlAlchemyTechnicalReportHistoricalResolver(db_session)
    for source_type, item in list(sources.items())[:4]:
        request = _historical_request(relationship_domain, source_type, item)
        basis = resolver.resolve(request)
        assert resolver.resolve_with_fallback(
            request, basis, historical_basis_digest(basis)
        ) == basis
        with pytest.raises(TechnicalReportIntegrityMismatch):
            resolver.resolve_with_fallback(request, basis, "0" * 64)
    request = _historical_request(
        relationship_domain, "universal_capture", sources["universal_capture"]
    )
    wrong = resolver.resolve(_historical_request(
        relationship_domain, "evidence", sources["evidence"]
    ))
    with pytest.raises(TechnicalReportHistoricalBasisIncomplete):
        resolver.resolve_with_fallback(request, wrong, historical_basis_digest(wrong))


@pytest.mark.parametrize(
    "family,relationship_type,allowed",
    [
        ("dependency", "depends_on", True),
        ("physical", "connected_to", True),
        ("dependency", "connected_to", False),
        ("physical", "depends_on", False),
    ],
)
def test_relationship_fallback_family_type_coherence(
    db_session, relationship_domain, family, relationship_type, allowed
):
    sources = _canonical_sources(db_session, relationship_domain)
    resolver = SqlAlchemyTechnicalReportHistoricalResolver(db_session)
    request = _historical_request(
        relationship_domain, "engineering_relationship",
        sources["engineering_relationship"],
    )
    basis = resolver.resolve(request)
    fallback = replace(
        basis, relationship_family=family, relationship_type=relationship_type
    )
    digest = historical_basis_digest(fallback)
    if allowed:
        assert resolver.resolve_with_fallback(request, fallback, digest) == fallback
    else:
        with pytest.raises(TechnicalReportHistoricalBasisIncomplete):
            resolver.resolve_with_fallback(request, fallback, digest)


@pytest.mark.parametrize("source_type", [
    "universal_capture", "evidence", "engineering_object",
    "engineering_relationship",
])
def test_incomplete_fallback_is_rejected_without_partial_disclosure(
    db_session, relationship_domain, source_type
):
    sources = _canonical_sources(db_session, relationship_domain)
    resolver = SqlAlchemyTechnicalReportHistoricalResolver(db_session)
    request = _historical_request(
        relationship_domain, source_type, sources[source_type]
    )
    with pytest.raises(TechnicalReportHistoricalBasisIncomplete) as error:
        resolver.resolve_with_fallback(request, None, "0" * 64)
    assert error.value.code == "TECHNICAL_REPORT_HISTORICAL_BASIS_INCOMPLETE"


def test_missing_canonical_source_uses_only_valid_authorized_fallbacks(
    db_session, relationship_domain
):
    sources = _canonical_sources(db_session, relationship_domain)
    resolver = SqlAlchemyTechnicalReportHistoricalResolver(db_session)
    identity_fields = {
        "universal_capture": "capture_id",
        "evidence": "evidence_id",
        "engineering_object": "engineering_object_id",
        "engineering_relationship": "engineering_relationship_id",
    }
    for source_type, item in list(sources.items())[:4]:
        basis = resolver.resolve(_historical_request(
            relationship_domain, source_type, item
        ))
        missing_id = uuid4()
        fallback = replace(basis, **{identity_fields[source_type]: missing_id})
        request = TechnicalReportHistoricalRequest(
            _historical_request(relationship_domain, source_type, item).actor,
            _historical_request(relationship_domain, source_type, item).scope,
            CreateDraftHistoricalAuthority(),
            source_type, missing_id, basis.source_version,
        )
        with pytest.raises(TechnicalReportHistoricalBasisIncomplete):
            resolver.resolve(request)
        assert resolver.resolve_with_fallback(
            request, fallback, historical_basis_digest(fallback)
        ) == fallback
        denied = replace(request, actor=TechnicalReportActor(
            relationship_domain["actors"]["unrelated"].id,
            request.actor.organization_id,
        ))
        with pytest.raises(TechnicalReportHistoricalBasisIncomplete):
            resolver.resolve_with_fallback(
                denied, fallback, historical_basis_digest(fallback)
            )


def test_missing_wrong_type_and_invalid_operation_fail_closed(
    db_session, relationship_domain
):
    sources = _canonical_sources(db_session, relationship_domain)
    resolver = SqlAlchemyTechnicalReportHistoricalResolver(db_session)
    missing = _historical_request(relationship_domain, "universal_capture", None)
    with pytest.raises(TechnicalReportHistoricalBasisIncomplete):
        resolver.resolve(missing)
    wrong = _historical_request(
        relationship_domain, "evidence", sources["universal_capture"]
    )
    with pytest.raises(TechnicalReportHistoricalBasisIncomplete):
        resolver.resolve(wrong)
    with pytest.raises(TypeError):
        TechnicalReportHistoricalRequest(
            missing.actor, missing.scope, "arbitrary_operation",
            missing.source_type, missing.source_id, missing.source_version,
        )


def test_batch_three_surface_has_no_transaction_or_application_behavior():
    import app.repositories.technical_report_repository as repository_module
    import app.repositories.technical_report_unit_of_work as resolver_module

    prohibited = {"commit", "rollback", "audit", "outbox", "idempotency", "service", "router"}
    names = {name.lower() for name in vars(repository_module)} | {
        name.lower() for name in vars(resolver_module)
    }
    assert not prohibited.intersection(names)
