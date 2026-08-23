"""PATCH-043 Batch 3 canonical Evidence/Report/Memory integration evidence."""

from dataclasses import asdict
from datetime import datetime, timezone
from types import SimpleNamespace
from uuid import uuid4

import pytest
from sqlalchemy.orm import sessionmaker

from app.enums import EvidenceLifecycle, EvidenceSourceKind, EvidenceSourceStanding
from app.enums.supporting_file import SupportingFileMediaType
from app.exceptions.evidence import EvidenceProtectedNotFound
from app.exceptions.technical_report import TechnicalReportHistoricalBasisIncomplete
from app.models.evidence import Evidence
from app.models.evidence_command import EvidenceActor
from app.models.organization import UserOrganizationMembership
from app.models.supporting_file import EvidenceSupportingFileLink, SupportingFileAsset
from app.models.supporting_file_command import SupportingFileHistoricalBasisV1, canonical_digest
from app.models.technical_report_command import (
    EvidenceHistoricalBasisV1,
    EvidenceHistoricalBasisV2,
    TechnicalReportActor,
    historical_basis_digest,
    historical_basis_from_payload,
)
from app.ports.technical_report import (
    CreateDraftHistoricalAuthority,
    TechnicalReportHistoricalRequest,
    TechnicalReportScope,
)
from app.repositories.evidence_unit_of_work import SqlAlchemyEvidenceUnitOfWork
from app.repositories.technical_report_unit_of_work import SqlAlchemyTechnicalReportHistoricalResolver
from app.schemas.evidence import LinkEvidenceSupportingFilesRequest
from app.services.evidence_service import EvidenceService
from app.services.supporting_file_service import SqlAlchemySupportingFileEvidenceCollaborator
from app.adapters.technical_report_evidence_source import TechnicalReportEvidenceSourceAdapter


NOW = datetime(2026, 8, 23, 12, 30, tzinfo=timezone.utc)


def _file_basis(*, organization_id, project_id, workspace_id, asset_id=None):
    return SupportingFileHistoricalBasisV1(
        1, "supporting_file", asset_id or uuid4(), 2, organization_id,
        project_id, workspace_id, "calculation.pdf",
        SupportingFileMediaType.PDF, 512, "sha256", "a" * 64, 7, NOW, None,
    )


def _evidence_v2(*, organization_id, project_id, workspace_id, files):
    return EvidenceHistoricalBasisV2(
        2, "evidence", uuid4(), 3, organization_id, project_id, workspace_id,
        EvidenceLifecycle.CURRENT, EvidenceSourceKind.ENGINEERING_RECORD, "field record",
        "rev-1", EvidenceSourceStanding.CURRENT, NOW,
        "Bounded supported engineering fact", 7, files,
    )


def test_evidence_v2_is_closed_deterministic_and_v1_remains_unchanged():
    organization_id = uuid4(); project_id = 31; workspace_id = 41
    files = tuple(sorted((
        _file_basis(organization_id=organization_id, project_id=project_id,
                    workspace_id=None),
        _file_basis(organization_id=organization_id, project_id=project_id,
                    workspace_id=workspace_id),
    ), key=lambda item: str(item.asset_id)))
    basis = _evidence_v2(
        organization_id=organization_id, project_id=project_id,
        workspace_id=workspace_id, files=files,
    )
    payload = asdict(basis)
    payload["evidence_id"] = str(basis.evidence_id)
    payload["organization_id"] = str(basis.organization_id)
    payload["effective_at"] = "2026-08-23T12:30:00.000000Z"
    payload["lifecycle"] = basis.lifecycle.value
    payload["source_kind"] = basis.source_kind.value
    payload["source_standing"] = basis.source_standing.value
    payload["supporting_files"] = list(payload["supporting_files"])
    for raw, item in zip(payload["supporting_files"], files, strict=True):
        raw["asset_id"] = str(item.asset_id)
        raw["organization_id"] = str(item.organization_id)
        raw["uploaded_at"] = "2026-08-23T12:30:00.000000Z"
        raw["media_type"] = item.media_type.value
    rebuilt = historical_basis_from_payload(payload, "evidence")
    assert rebuilt == basis
    assert historical_basis_digest(rebuilt) == historical_basis_digest(basis)
    assert canonical_digest(files) == canonical_digest(tuple(files))

    v1 = EvidenceHistoricalBasisV1(
        1, "evidence", uuid4(), 1, organization_id, project_id, workspace_id,
        EvidenceLifecycle.CURRENT, EvidenceSourceKind.ENGINEERING_RECORD, "legacy", "v1",
        EvidenceSourceStanding.CURRENT, None, "Reference-only fact", 7,
    )
    assert v1.basis_schema_version == 1 and not hasattr(v1, "supporting_files")


def test_server_composes_file_backed_evidence_candidate_without_client_locator():
    organization_id = uuid4(); project_id = 31; workspace_id = 41
    evidence = SimpleNamespace(
        id=uuid4(), version=3, organization_id=organization_id,
        project_id=project_id, workspace_id=workspace_id,
        lifecycle=EvidenceLifecycle.CURRENT,
        source_kind=EvidenceSourceKind.ENGINEERING_RECORD,
        source_reference="field record", source_revision="rev-1",
        source_standing=EvidenceSourceStanding.CURRENT,
        effective_at=NOW, supported_fact="Authorized supported fact",
        creator_id=7, updated_at=NOW,
    )
    files = (_file_basis(
        organization_id=organization_id, project_id=project_id,
        workspace_id=workspace_id,
    ),)
    service = SimpleNamespace(list=lambda **_: SimpleNamespace(
        items=(evidence,), total=1, page=1, size=20,
    ))
    collaborator = SimpleNamespace(resolve_for_evidence=lambda **_: files)
    result = TechnicalReportEvidenceSourceAdapter(
        evidence_service=service, supporting_files=collaborator,
        actor=EvidenceActor(7, organization_id),
    ).list_candidates(
        project_id=project_id, workspace_id=workspace_id, page=1, size=20,
    )
    candidate = result.items[0]
    assert candidate.evidence_id == evidence.id
    assert candidate.supporting_file_count == 1
    assert candidate.provenance.locator.basis_schema_version == 2
    assert candidate.provenance.locator.supporting_files[0].asset_id == files[0].asset_id
    assert candidate.provenance.integrity_digest == historical_basis_digest(
        candidate.provenance.locator.to_domain()
    )


def test_evidence_v2_rejects_open_or_semantically_incoherent_nested_basis():
    organization_id = uuid4(); file_basis = _file_basis(
        organization_id=organization_id, project_id=31, workspace_id=None,
    )
    basis = _evidence_v2(
        organization_id=organization_id, project_id=31,
        workspace_id=41, files=(file_basis,),
    )
    payload = asdict(basis)
    payload.update(
        evidence_id=str(basis.evidence_id), organization_id=str(organization_id),
        effective_at="2026-08-23T12:30:00.000000Z",
        lifecycle="current", source_kind="engineering_record", source_standing="current",
    )
    payload["supporting_files"] = list(payload["supporting_files"])
    raw = payload["supporting_files"][0]
    raw.update(
        asset_id=str(file_basis.asset_id), organization_id=str(organization_id),
        uploaded_at="2026-08-23T12:30:00.000000Z", media_type="application/pdf",
        invented_authority="denied",
    )
    with pytest.raises(TechnicalReportHistoricalBasisIncomplete):
        historical_basis_from_payload(payload, "evidence")


class _AllowEvidence:
    def authorize(self, **_):
        return True


class _Clock:
    def now(self):
        return NOW


def _seed_linkable(db_session, relationship_domain, *, asset_workspace):
    actor = relationship_domain["actors"]["project_owner"]
    project = relationship_domain["project"]
    workspace = relationship_domain["consumer_workspace"]
    evidence = Evidence(
        id=uuid4(), organization_id=project.organization_id,
        project_id=project.id, workspace_id=workspace.id,
        lifecycle="proposed", source_kind="engineering_record", source_reference="field",
        source_revision="r1", source_standing="current", effective_at=NOW,
        supported_fact="Observed condition", creator_id=actor.id, version=1,
        created_at=NOW, updated_at=NOW,
    )
    asset = SupportingFileAsset(
        id=uuid4(), organization_id=project.organization_id,
        project_id=project.id, workspace_id=asset_workspace,
        safe_filename="calculation.pdf", safe_ascii_filename="calculation.pdf",
        media_type="application/pdf", byte_size=512, digest_algorithm="sha256",
        content_digest="b" * 64, storage_key="objects/" + "c" * 64,
        object_version="object-v1", uploader_id=actor.id,
        lifecycle="available", version=2, uploaded_at=NOW,
        scan_requested_at=NOW, scanned_at=NOW, created_at=NOW, updated_at=NOW,
    )
    db_session.add_all((evidence, asset)); db_session.flush()
    return actor, project, workspace, evidence, asset


def test_same_session_link_accepts_project_scoped_asset_and_is_exact(db_session, relationship_domain):
    actor, project, workspace, evidence, asset = _seed_linkable(
        db_session, relationship_domain, asset_workspace=None,
    )
    factory = sessionmaker(
        bind=db_session.connection(), expire_on_commit=False,
        join_transaction_mode="create_savepoint",
    )
    service = EvidenceService(
        uow_factory=lambda: SqlAlchemyEvidenceUnitOfWork(factory),
        authorization=_AllowEvidence(), validator=object(), clock=_Clock(),
    )
    response = service.link_supporting_files(
        evidence.id,
        LinkEvidenceSupportingFilesRequest(
            expected_version=1, asset_ids=(asset.id,), rationale="Human link",
        ),
        EvidenceActor(actor.id, project.organization_id), uuid4(), uuid4(),
    )
    db_session.expire_all()
    link = db_session.query(EvidenceSupportingFileLink).filter_by(
        evidence_id=evidence.id,
    ).one()
    assert response.version == 2
    assert link.asset_id == asset.id and link.evidence_version == 2
    assert link.workspace_id == workspace.id


def test_memory_nested_history_authorization_is_exact_all_or_nothing(db_session, relationship_domain):
    actor, project, workspace, evidence, asset = _seed_linkable(
        db_session, relationship_domain,
        asset_workspace=relationship_domain["consumer_workspace"].id,
    )
    evidence.version = 2
    db_session.add(EvidenceSupportingFileLink(
        evidence_id=evidence.id, asset_id=asset.id,
        organization_id=project.organization_id, project_id=project.id,
        workspace_id=workspace.id, evidence_version=2, ordinal=0,
        linked_by_id=actor.id, linked_at=NOW,
    ))
    db_session.flush()
    collaborator = SqlAlchemySupportingFileEvidenceCollaborator(db_session)
    exact = _file_basis(
        organization_id=project.organization_id, project_id=project.id,
        workspace_id=workspace.id, asset_id=asset.id,
    )
    # Match the persisted canonical fields rather than test-vector fields.
    actual = collaborator.authorize_and_lock_for_evidence(
        actor_id=actor.id, organization_id=project.organization_id,
        project_id=project.id, workspace_id=workspace.id, asset_ids=(asset.id,),
    )
    assert collaborator.authorize_historical_for_evidence(
        actor_id=actor.id, evidence_id=evidence.id,
        organization_id=project.organization_id, project_id=project.id,
        workspace_id=workspace.id, historical=actual,
    ) == actual
    with pytest.raises(Exception):
        collaborator.authorize_historical_for_evidence(
            actor_id=actor.id, evidence_id=evidence.id,
            organization_id=project.organization_id, project_id=project.id,
            workspace_id=workspace.id, historical=(exact,),
        )


def test_technical_report_resolver_selects_v2_and_rechecks_current_files(db_session, relationship_domain):
    actor, project, workspace, evidence, asset = _seed_linkable(
        db_session, relationship_domain, asset_workspace=None,
    )
    membership = db_session.get(
        UserOrganizationMembership, (actor.id, project.organization_id),
    )
    if membership is None:
        db_session.add(UserOrganizationMembership(
            user_id=actor.id, organization_id=project.organization_id,
            is_enabled=True, is_selected=True,
        ))
    evidence.version = 2
    db_session.add(EvidenceSupportingFileLink(
        evidence_id=evidence.id, asset_id=asset.id,
        organization_id=project.organization_id, project_id=project.id,
        workspace_id=workspace.id, evidence_version=2, ordinal=0,
        linked_by_id=actor.id, linked_at=NOW,
    ))
    db_session.flush()
    evidence.lifecycle = "current"; evidence.version = 3; evidence.updated_at = NOW
    db_session.flush()
    resolver = SqlAlchemyTechnicalReportHistoricalResolver(db_session)
    request = TechnicalReportHistoricalRequest(
        TechnicalReportActor(actor.id, project.organization_id),
        TechnicalReportScope(project.organization_id, workspace.id, project.id),
        CreateDraftHistoricalAuthority(), "evidence", evidence.id, 3,
    )
    basis = resolver.resolve(request)
    assert isinstance(basis, EvidenceHistoricalBasisV2)
    assert tuple(item.asset_id for item in basis.supporting_files) == (asset.id,)

    asset.lifecycle = "withdrawn"; asset.version = 3
    asset.withdrawn_at = NOW; asset.withdrawn_by_id = actor.id
    asset.withdrawal_reason_code = "obsolete"; asset.updated_at = NOW
    db_session.flush()
    with pytest.raises(TechnicalReportHistoricalBasisIncomplete):
        resolver.resolve(request)
