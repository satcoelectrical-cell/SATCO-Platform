"""Focused PATCH-032 Batch 5 application-service evidence."""

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
from app.exceptions.technical_report import TechnicalReportVersionConflict
from app.models.technical_report_command import (
    AcceptExactTechnicalReportDraft,
    AcceptanceConfirmation,
    CaptureHistoricalBasisV1,
    ContextualLocator,
    CreateTechnicalReportDraft,
    CreateTechnicalReportSuccessor,
    PreliminaryQualification,
    ReviseTechnicalReportDraft,
    TechnicalReportActor,
    TechnicalReportCommandMetadata,
    TechnicalReportContent,
    TechnicalReportProvenanceEntry,
    historical_basis_digest,
)
from app.ports.technical_report import (
    TechnicalReportAIProposal,
    TechnicalReportAIRequest,
    TechnicalReportReadCriteria,
    TechnicalReportReadItem,
    TechnicalReportReadPage,
    AcceptedTechnicalReportSummaryPage,
    TechnicalReportScope,
)
from app.services.technical_report_service import TechnicalReportService


NOW = datetime(2026, 8, 11, 10, 0, tzinfo=timezone.utc)


class Clock:
    def now(self):
        return NOW


class Recorder:
    def __init__(self): self.values = []
    def record(self, value): self.values.extend(value if isinstance(value, tuple) else (value,))


class Idempotency:
    def __init__(self): self.results = {}; self.reservations = {}
    def find(self, key, fingerprint):
        current = self.results.get(key) or self.reservations.get(key)
        if current is None: return None
        if current[0] != fingerprint:
            from app.exceptions.technical_report import TechnicalReportIdempotencyConflict
            raise TechnicalReportIdempotencyConflict()
        return None if len(current) == 1 else current[1]
    def reserve(self, key, fingerprint):
        if key in self.results or key in self.reservations:
            from app.exceptions.technical_report import TechnicalReportIdempotencyConflict
            raise TechnicalReportIdempotencyConflict()
        self.reservations[key] = (fingerprint,)
    def record_result(self, key, result):
        fingerprint = self.reservations.pop(key)[0]
        self.results[key] = (fingerprint, result)


class Repository:
    def __init__(self): self.reports = {}; self.fail_cas = False
    def add(self, report): self.reports[report.id] = report
    def get_scoped(self, report_id, organization_id):
        report = self.reports.get(report_id)
        return report if report is not None and report.organization_id == organization_id else None
    def persist_draft_expected_version(self, report, expected_version): return not self.fail_cas
    def persist_acceptance_expected_version(self, report, expected_version): return not self.fail_cas
    def list_scoped(self, criteria):
        reports = [
            r for r in self.reports.values()
            if r.organization_id == criteria.scope.organization_id
            and r.workspace_id == criteria.scope.workspace_id
            and (criteria.scope.project_id is None or r.project_id == criteria.scope.project_id)
            and (criteria.lifecycle is None or r.lifecycle == criteria.lifecycle)
        ]
        items = tuple(TechnicalReportReadItem(r.id, r.version) for r in reports)
        return TechnicalReportReadPage(items, len(items), criteria.page, criteria.size)
    def list_successors_scoped(self, predecessor_id, criteria):
        reports = [
            r for r in self.reports.values()
            if r.predecessor_report_id == predecessor_id
            and r.organization_id == criteria.scope.organization_id
            and r.workspace_id == criteria.scope.workspace_id
            and r.project_id == criteria.scope.project_id
        ]
        items = tuple(TechnicalReportReadItem(r.id, r.version) for r in reports)
        return TechnicalReportReadPage(items, len(items), criteria.page, criteria.size)
    def provenance_for_report(self, report_id): return self.reports[report_id].provenance


class Policy:
    def __init__(self): self.requests = []; self.denied_operations = set()
    def require(self, request):
        self.requests.append(request)
        if request.operation in self.denied_operations:
            from app.exceptions.technical_report import TechnicalReportAuthorizationDenied
            raise TechnicalReportAuthorizationDenied()


class References:
    def __init__(self): self.requests = []
    def validate(self, request): self.requests.append(request)


class Historical:
    def __init__(self): self.requests = []
    def resolve(self, request):
        self.requests.append(request)
        return BASIS_BY_ID[request.source_id]


class FinalRecheck:
    def __init__(self): self.requests = []
    def require_current(self, request): self.requests.append(request)


class RejectionAudit:
    def __init__(self): self.values = []; self.fail = False
    def record_rejection(self, value):
        if self.fail: raise RuntimeError("audit unavailable")
        self.values.append(value)


class Uow:
    def __init__(self, repository):
        self.technical_reports = repository
        self.authorization = Policy()
        self.references = References()
        self.historical = Historical()
        self.audit = Recorder()
        self.domain_events = Recorder()
        self.idempotency = Idempotency()
        self.final_recheck = FinalRecheck()
        self.rejection_audit = RejectionAudit()
        self.commits = 0; self.rollbacks = 0
    def __enter__(self): return self
    def __exit__(self, exc_type, *_):
        if exc_type: self.rollback()
    def commit(self): self.commits += 1
    def rollback(self): self.rollbacks += 1


class Assistant:
    def propose(self, request): return TechnicalReportAIProposal("Advisory draft", "provider-neutral")


BASIS_BY_ID = {}


def content(text="Engineering analysis"):
    return TechnicalReportContent(
        "Motor control", text, ("Supply available",), "Known uncertainty",
        ("One state observed",), "Observed condition confirmed", ("Verify settings",),
    )


def command():
    actor = TechnicalReportActor(7, uuid4())
    metadata = TechnicalReportCommandMetadata(actor, "Human rationale", uuid4(), uuid4(), uuid4())
    basis = CaptureHistoricalBasisV1(
        1, "universal_capture", uuid4(), 2, actor.organization_id, 11, 12,
        "electrical", uuid4(), "observation", "Measured chatter", "field-7",
        actor.actor_id, "captured", NOW,
    )
    BASIS_BY_ID[basis.capture_id] = basis
    provenance = TechnicalReportProvenanceEntry(
        uuid4(), 0, TechnicalReportSourceClass.CANONICAL_MATERIAL,
        TechnicalReportSourceType.UNIVERSAL_CAPTURE, True, "universal_capture",
        "primary observation", TechnicalReportVerificationStatus.VERIFIED,
        TechnicalReportAvailabilityStatus.AVAILABLE, "Authenticated engineer", (),
        basis, TechnicalReportIntegrityAlgorithm.SHA256, historical_basis_digest(basis),
    )
    return CreateTechnicalReportDraft(
        metadata, actor.organization_id, 12, 11, actor.actor_id,
        TechnicalReportPurpose.ENGINEERING_ANALYSIS, content(),
        PreliminaryQualification(False), (provenance,),
    )


def setup_service(assistant=None):
    repository = Repository(); uow = Uow(repository)
    return TechnicalReportService(lambda: uow, Clock(), assistant), uow


def test_create_replay_and_side_records_are_coordinated_once():
    service, uow = setup_service(); create = command()
    first = service.create_draft(create)
    second = service.create_draft(create)
    assert second.report_id == first.report_id
    assert second.version == first.version
    assert second.report.content == first.report.content
    assert uow.commits == 1
    assert len(uow.audit.values) == 1
    assert len(uow.domain_events.values) == 1
    assert len(uow.references.requests) == 2  # replay is reauthorized and revalidated


def test_revise_invokes_one_aggregate_command_and_compare_and_change():
    service, uow = setup_service(); create = command()
    created = service.create_draft(create); report = uow.technical_reports.reports[created.report_id]
    revise = ReviseTechnicalReportDraft(
        TechnicalReportCommandMetadata(create.metadata.actor, "Revision rationale", uuid4(), uuid4(), uuid4()),
        report.id, report.version, report.draft_revision_id, content("Revised analysis"),
        report.qualification, report.provenance,
    )
    result = service.revise_draft(revise)
    assert result.version == 2 and report.version == 2
    assert uow.commits == 2


def test_stale_compare_and_change_rolls_back_and_never_commits_success():
    service, uow = setup_service(); create = command()
    created = service.create_draft(create); report = uow.technical_reports.reports[created.report_id]
    uow.technical_reports.fail_cas = True
    revise = ReviseTechnicalReportDraft(
        TechnicalReportCommandMetadata(create.metadata.actor, "Revision rationale", uuid4(), uuid4(), uuid4()),
        report.id, report.version, report.draft_revision_id, content("Changed analysis"),
        report.qualification, report.provenance,
    )
    with pytest.raises(TechnicalReportVersionConflict): service.revise_draft(revise)
    assert uow.rollbacks == 1 and uow.commits == 1


def test_acceptance_runs_same_uow_final_recheck_before_commit():
    service, uow = setup_service(); create = command()
    created = service.create_draft(create); report = uow.technical_reports.reports[created.report_id]
    accept = AcceptExactTechnicalReportDraft(
        TechnicalReportCommandMetadata(create.metadata.actor, "Accept exact draft", uuid4(), uuid4(), uuid4()),
        report.id, AcceptanceConfirmation(report.version, report.draft_revision_id, True),
    )
    result = service.accept_exact_draft(accept)
    assert result.version == 2
    assert len(uow.final_recheck.requests) == 1
    assert uow.commits == 2


def test_authorized_get_list_and_ai_proposal_are_read_only():
    service, uow = setup_service(Assistant()); create = command()
    result = service.create_draft(create); report = uow.technical_reports.reports[result.report_id]
    commits = uow.commits
    assert service.get_report(create.metadata.actor, report.id).id == report.id
    page = service.list_reports(create.metadata.actor, TechnicalReportReadCriteria(
        TechnicalReportScope(report.organization_id, report.workspace_id, report.project_id), 1, 20
    ))
    proposal = service.request_ai_proposal(
        create.metadata.actor, report.id,
        expected_version=report.version,
        expected_draft_revision_id=report.draft_revision_id,
        human_instruction="Improve clarity",
        selected_source_entry_ids=(report.provenance[0].entry_id,),
    )
    assert page.total == 1 and proposal.proposal_text == "Advisory draft"
    assert uow.commits == commits


def test_accepted_summary_is_owner_scoped_bounded_and_safe():
    service, uow = setup_service(); create = command()
    created = service.create_draft(create); report = uow.technical_reports.reports[created.report_id]
    service.accept_exact_draft(AcceptExactTechnicalReportDraft(
        TechnicalReportCommandMetadata(create.metadata.actor, "accept", uuid4(), uuid4(), uuid4()),
        report.id, AcceptanceConfirmation(report.version, report.draft_revision_id, True),
    ))
    summary = service.list_accepted_summaries(create.metadata.actor, TechnicalReportReadCriteria(
        TechnicalReportScope(report.organization_id, report.workspace_id, report.project_id), 1, 1,
    ))
    assert isinstance(summary, AcceptedTechnicalReportSummaryPage)
    assert len(summary.items) == 1
    item = summary.items[0]
    assert (item.report_id, item.workspace_id, item.project_id, item.version) == (report.id, report.workspace_id, report.project_id, report.version)
    assert item.accepted_digest == report.acceptance_record.snapshot_digest
    assert set(item.__dataclass_fields__) == {"report_id", "workspace_id", "project_id", "version", "accepted_digest", "accepted_at", "purpose"}
    assert uow.authorization.requests[-1].operation == "list_accepted_summaries"


def test_successor_and_lineage_preserve_predecessor_and_authorized_total():
    service, uow = setup_service(); create = command()
    created = service.create_draft(create); report = uow.technical_reports.reports[created.report_id]
    accept = AcceptExactTechnicalReportDraft(
        TechnicalReportCommandMetadata(create.metadata.actor, "Accept exact draft", uuid4(), uuid4(), uuid4()),
        report.id, AcceptanceConfirmation(report.version, report.draft_revision_id, True),
    )
    service.accept_exact_draft(accept)
    successor = CreateTechnicalReportSuccessor(
        TechnicalReportCommandMetadata(create.metadata.actor, "Successor rationale", uuid4(), uuid4(), uuid4()),
        report.id, report.version, report.workspace_id, report.project_id, report.purpose,
        content("Successor analysis"), PreliminaryQualification(False), report.provenance,
    )
    result = service.create_successor(successor)
    lineage = service.retrieve_lineage(create.metadata.actor, report.id)
    assert result.report_id != report.id
    assert lineage.successors.total == 1
    assert lineage.successors.items[0].report_id == result.report_id


def test_different_fingerprint_with_same_idempotency_key_is_rejected():
    from app.exceptions.technical_report import TechnicalReportIdempotencyConflict
    service, _ = setup_service(); create = command(); service.create_draft(create)
    conflicting = CreateTechnicalReportDraft(
        create.metadata, create.organization_id, create.workspace_id, create.project_id,
        create.owner_id, create.purpose, content("Different request"),
        create.qualification, create.provenance,
    )
    with pytest.raises(TechnicalReportIdempotencyConflict):
        service.create_draft(conflicting)


def test_create_replay_preserves_original_draft_response_after_later_revision():
    service, uow = setup_service(); create = command()
    first = service.create_draft(create); report = uow.technical_reports.reports[first.report_id]
    original_content = report.content
    service.revise_draft(ReviseTechnicalReportDraft(
        TechnicalReportCommandMetadata(create.metadata.actor, "Revision", uuid4(), uuid4(), uuid4()),
        report.id, report.version, report.draft_revision_id,
        content("Later revision"), report.qualification, report.provenance,
    ))
    replay = service.create_draft(create)
    assert replay.version == 1
    assert replay.report.lifecycle.value == "draft"
    assert replay.report.content == original_content
    assert replay.report.content != report.content


def test_server_controlled_allowed_actions_follow_current_lifecycle_and_authority():
    service, uow = setup_service(Assistant()); create = command()
    draft = service.create_draft(create).report
    assert draft.allowed_actions == ("revise", "accept", "request_ai_proposal")
    uow.authorization.denied_operations.add("request_ai_proposal")
    assert service.get_report(create.metadata.actor, draft.id).allowed_actions == ("revise", "accept")
    uow.authorization.denied_operations.clear()
    accepted = service.accept_exact_draft(AcceptExactTechnicalReportDraft(
        TechnicalReportCommandMetadata(create.metadata.actor, "Accept", uuid4(), uuid4(), uuid4()),
        draft.id, AcceptanceConfirmation(draft.version, draft.draft_revision_id, True),
    )).report
    assert accepted.allowed_actions == ("create_successor",)
    uow.authorization.denied_operations.add("create_successor")
    assert service.get_report(create.metadata.actor, draft.id).allowed_actions == ()


def test_every_mutation_replay_reauthorizes_and_preserves_original_response():
    from app.exceptions.technical_report import TechnicalReportAuthorizationDenied

    service, uow = setup_service(); create = command()
    created = service.create_draft(create); report = uow.technical_reports.reports[created.report_id]
    revise = ReviseTechnicalReportDraft(
        TechnicalReportCommandMetadata(create.metadata.actor, "Revision", uuid4(), uuid4(), uuid4()),
        report.id, report.version, report.draft_revision_id, content("Revision one"),
        report.qualification, report.provenance,
    )
    revised = service.revise_draft(revise)
    accept = AcceptExactTechnicalReportDraft(
        TechnicalReportCommandMetadata(create.metadata.actor, "Accept", uuid4(), uuid4(), uuid4()),
        report.id, AcceptanceConfirmation(report.version, report.draft_revision_id, True),
    )
    accepted = service.accept_exact_draft(accept)
    successor = CreateTechnicalReportSuccessor(
        TechnicalReportCommandMetadata(create.metadata.actor, "Successor", uuid4(), uuid4(), uuid4()),
        report.id, report.version, report.workspace_id, report.project_id, report.purpose,
        content("Successor one"), PreliminaryQualification(False), report.provenance,
    )
    successor_result = service.create_successor(successor)
    successor_report = uow.technical_reports.reports[successor_result.report_id]
    original_successor_content = successor_report.content
    service.revise_draft(ReviseTechnicalReportDraft(
        TechnicalReportCommandMetadata(create.metadata.actor, "Later successor revision", uuid4(), uuid4(), uuid4()),
        successor_report.id, successor_report.version, successor_report.draft_revision_id,
        content("Successor later"), successor_report.qualification, successor_report.provenance,
    ))

    assert service.create_draft(create).version == created.version
    assert service.revise_draft(revise).report.content == revised.report.content
    assert service.accept_exact_draft(accept).version == accepted.version
    replayed_successor = service.create_successor(successor)
    assert replayed_successor.version == successor_result.version
    assert replayed_successor.report.content == original_successor_content

    replay_cases = (
        ("create_draft", lambda: service.create_draft(create)),
        ("revise_draft", lambda: service.revise_draft(revise)),
        ("accept_exact_draft", lambda: service.accept_exact_draft(accept)),
        ("create_successor", lambda: service.create_successor(successor)),
    )
    baseline = (uow.commits, len(uow.audit.values), len(uow.domain_events.values))
    for operation, replay in replay_cases:
        uow.authorization.denied_operations.add(operation)
        with pytest.raises(TechnicalReportAuthorizationDenied):
            replay()
        uow.authorization.denied_operations.clear()
    assert (uow.commits, len(uow.audit.values), len(uow.domain_events.values)) == baseline


def test_successor_selected_copy_is_reauthorized_and_owned_by_new_draft():
    service, uow = setup_service(); create = command()
    created = service.create_draft(create); predecessor = uow.technical_reports.reports[created.report_id]
    service.accept_exact_draft(AcceptExactTechnicalReportDraft(
        TechnicalReportCommandMetadata(create.metadata.actor, "Accept", uuid4(), uuid4(), uuid4()),
        predecessor.id, AcceptanceConfirmation(predecessor.version, predecessor.draft_revision_id, True),
    ))
    successor = CreateTechnicalReportSuccessor(
        TechnicalReportCommandMetadata(create.metadata.actor, "Successor", uuid4(), uuid4(), uuid4()),
        predecessor.id, predecessor.version, predecessor.workspace_id,
        predecessor.project_id, predecessor.purpose, content("Successor"),
        PreliminaryQualification(False), (), (predecessor.provenance[0].entry_id,),
    )
    result = service.create_successor(successor)
    assert result.report.lifecycle.value == "draft"
    assert result.report.accepted_snapshot is None
    assert result.report.provenance[0].entry_id == predecessor.provenance[0].entry_id
    assert any(request.source_id == predecessor.provenance[0].locator.capture_id
               and request.authority.operation.value == "create_successor"
               for request in uow.historical.requests)


def test_successor_unknown_selected_copy_fails_without_commit():
    service, uow = setup_service(); create = command()
    created = service.create_draft(create); predecessor = uow.technical_reports.reports[created.report_id]
    service.accept_exact_draft(AcceptExactTechnicalReportDraft(
        TechnicalReportCommandMetadata(create.metadata.actor, "Accept", uuid4(), uuid4(), uuid4()),
        predecessor.id, AcceptanceConfirmation(predecessor.version, predecessor.draft_revision_id, True),
    ))
    commits = uow.commits
    invalid = CreateTechnicalReportSuccessor(
        TechnicalReportCommandMetadata(create.metadata.actor, "Successor", uuid4(), uuid4(), uuid4()),
        predecessor.id, predecessor.version, predecessor.workspace_id,
        predecessor.project_id, predecessor.purpose, content("Successor"),
        PreliminaryQualification(False), (), (uuid4(),),
    )
    from app.exceptions.technical_report import TechnicalReportAuthorizationDenied
    with pytest.raises(TechnicalReportAuthorizationDenied): service.create_successor(invalid)
    assert uow.commits == commits


def test_real_uow_success_and_failure_are_atomic(db_session, relationship_domain):
    from sqlalchemy.orm import sessionmaker
    from app.models.audit_log import AuditLog
    from app.models.engineering_experience_capture import EngineeringExperienceCapture
    from app.models.technical_report import TechnicalReportRecord
    from app.models.technical_report import TechnicalReportProvenanceRecord
    from app.models.technical_report_command import TechnicalReportIdempotencyRecord, TechnicalReportOutboxRecord
    from app.repositories.technical_report_unit_of_work import SqlAlchemyTechnicalReportUnitOfWork

    actor_row = relationship_domain["actors"]["project_owner"]
    project = relationship_domain["project"]
    workspace = relationship_domain["consumer_workspace"]
    actor = TechnicalReportActor(actor_row.id, project.organization_id)
    factory = sessionmaker(
        bind=db_session.get_bind(), expire_on_commit=False,
        join_transaction_mode="create_savepoint",
    )

    def make(text, project_id=project.id, purpose=TechnicalReportPurpose.ENGINEERING_ANALYSIS):
        contextual = TechnicalReportProvenanceEntry(
            uuid4(), 0, TechnicalReportSourceClass.CONTEXTUAL_NON_MATERIAL,
            TechnicalReportSourceType.CONTEXTUAL, False, None, "context only",
            TechnicalReportVerificationStatus.UNVERIFIED,
            TechnicalReportAvailabilityStatus.AVAILABLE, "Human context", (),
            ContextualLocator(uuid4(), "engineering_context"), None, None,
        )
        return CreateTechnicalReportDraft(
            TechnicalReportCommandMetadata(actor, "Human rationale", uuid4(), uuid4(), uuid4()),
            project.organization_id, workspace.id, project_id, actor.actor_id,
            purpose, content(text),
            PreliminaryQualification(False), (contextual,),
        )

    successful = make("Atomic success")
    result = TechnicalReportService(lambda: SqlAlchemyTechnicalReportUnitOfWork(factory), Clock()).create_draft(successful)
    assert db_session.get(TechnicalReportRecord, result.report_id) is not None
    assert db_session.query(TechnicalReportProvenanceRecord).filter_by(technical_report_id=result.report_id).count() == 1
    assert db_session.query(AuditLog).filter_by(entity_uuid=result.report_id).count() == 1
    assert db_session.query(TechnicalReportOutboxRecord).filter_by(aggregate_id=result.report_id).count() == 1
    assert db_session.query(TechnicalReportIdempotencyRecord).filter_by(aggregate_id=result.report_id).count() == 1

    projectless = make(
        "Workspace-wide result", None,
        TechnicalReportPurpose.TECHNICAL_RECOMMENDATION,
    )
    TechnicalReportService(
        lambda: SqlAlchemyTechnicalReportUnitOfWork(factory), Clock()
    ).create_draft(projectless)
    from app.repositories.technical_report_repository import SqlAlchemyTechnicalReportRepository
    repository = SqlAlchemyTechnicalReportRepository(db_session)
    workspace_page = repository.list_scoped(TechnicalReportReadCriteria(
        TechnicalReportScope(project.organization_id, workspace.id, None), 1, 100,
    ))
    assert workspace_page.total == 2
    filtered_page = repository.list_scoped(TechnicalReportReadCriteria(
        TechnicalReportScope(project.organization_id, workspace.id, None), 1, 100,
        TechnicalReportPurpose.TECHNICAL_RECOMMENDATION,
        TechnicalReportLifecycle.DRAFT,
    ))
    assert filtered_page.total == 1

    class FailingRecorder:
        def record(self, _events): raise RuntimeError("injected outbox failure")
    class FailingUow(SqlAlchemyTechnicalReportUnitOfWork):
        def __enter__(self):
            value = super().__enter__(); self.domain_events = FailingRecorder(); return value
    failed = make("Atomic rollback")
    with pytest.raises(RuntimeError, match="injected outbox failure"):
        TechnicalReportService(lambda: FailingUow(factory), Clock()).create_draft(failed)
    assert db_session.query(TechnicalReportRecord).filter_by(draft_content="Atomic rollback").count() == 0
    failed_ids = db_session.query(TechnicalReportRecord.id).filter_by(draft_content="Atomic rollback").subquery()
    assert db_session.query(TechnicalReportProvenanceRecord).filter(
        TechnicalReportProvenanceRecord.technical_report_id.in_(failed_ids)
    ).count() == 0
    assert db_session.query(AuditLog).filter(
        AuditLog.details["command_id"].as_string() == str(failed.metadata.command_id)
    ).count() == 0
    assert db_session.query(TechnicalReportIdempotencyRecord).filter_by(idempotency_id=failed.metadata.idempotency_id).count() == 0


def test_real_uow_persisted_replay_matrix_reauthorizes_and_has_no_side_effects(
    db_session, relationship_domain,
):
    import json
    from dataclasses import replace
    from sqlalchemy.orm import sessionmaker
    from app.exceptions.technical_report import (
        TechnicalReportAuthorizationDenied, TechnicalReportIdempotencyConflict,
    )
    from app.models.audit_log import AuditLog
    from app.models.engineering_experience_capture import EngineeringExperienceCapture
    from app.models.organization import UserOrganizationMembership
    from app.models.technical_report import TechnicalReportRecord, TechnicalReportProvenanceRecord
    from app.models.technical_report_command import TechnicalReportIdempotencyRecord, TechnicalReportOutboxRecord
    from app.repositories.technical_report_unit_of_work import SqlAlchemyTechnicalReportUnitOfWork

    actor_row = relationship_domain["actors"]["project_owner"]
    project = relationship_domain["project"]
    workspace = relationship_domain["consumer_workspace"]
    actor = TechnicalReportActor(actor_row.id, project.organization_id)
    factory = sessionmaker(
        bind=db_session.get_bind(), expire_on_commit=False,
        join_transaction_mode="create_savepoint",
    )
    service = TechnicalReportService(
        lambda: SqlAlchemyTechnicalReportUnitOfWork(factory), Clock()
    )

    def metadata(rationale):
        return TechnicalReportCommandMetadata(actor, rationale, uuid4(), uuid4(), uuid4())

    capture = EngineeringExperienceCapture(
        id=uuid4(), organization_id=project.organization_id,
        project_id=project.id, workspace_id=workspace.id,
        discipline="electrical", engineering_object_id=None,
        source_kind="observation", original_content="Replay source basis",
        source_reference="replay-source", creator_id=actor.actor_id,
        lifecycle="captured", version=1, created_at=NOW, updated_at=NOW,
    )
    db_session.add(capture); db_session.flush()
    basis = CaptureHistoricalBasisV1(
        1, "universal_capture", capture.id, 1, project.organization_id,
        project.id, workspace.id, "electrical", None, "observation",
        "Replay source basis", "replay-source", actor.actor_id, "captured", NOW,
    )
    provenance = (TechnicalReportProvenanceEntry(
        uuid4(), 0, TechnicalReportSourceClass.CANONICAL_MATERIAL,
        TechnicalReportSourceType.UNIVERSAL_CAPTURE, True, "universal_capture",
        "material basis", TechnicalReportVerificationStatus.VERIFIED,
        TechnicalReportAvailabilityStatus.AVAILABLE, "Human source", (), basis,
        TechnicalReportIntegrityAlgorithm.SHA256, historical_basis_digest(basis),
    ),)
    secret_values = (
        "PERSISTED-CREATE-PLAINTEXT", "PERSISTED-REVISE-PLAINTEXT",
        "PERSISTED-SUCCESSOR-PLAINTEXT", "PERSISTED-LATER-PLAINTEXT",
    )
    create = CreateTechnicalReportDraft(
        metadata("Create replay evidence"), project.organization_id,
        workspace.id, project.id, actor.actor_id,
        TechnicalReportPurpose.ENGINEERING_ANALYSIS, content(secret_values[0]),
        PreliminaryQualification(False), provenance,
    )
    created = service.create_draft(create)
    report = service.get_report(actor, created.report_id)
    revise = ReviseTechnicalReportDraft(
        metadata("Revise replay evidence"), report.id, report.version,
        report.draft_revision_id, content(secret_values[1]),
        report.qualification, report.provenance,
    )
    revised = service.revise_draft(revise)
    accept = AcceptExactTechnicalReportDraft(
        metadata("Accept replay evidence"), report.id,
        AcceptanceConfirmation(revised.version, revised.report.draft_revision_id, True),
    )
    accepted = service.accept_exact_draft(accept)
    successor_provenance = (replace(provenance[0], entry_id=uuid4()),)
    successor = CreateTechnicalReportSuccessor(
        metadata("Successor replay evidence"), report.id, accepted.version,
        report.workspace_id, report.project_id, report.purpose,
        content(secret_values[2]), PreliminaryQualification(False), successor_provenance,
    )
    successor_created = service.create_successor(successor)
    successor_report = service.get_report(actor, successor_created.report_id)
    service.revise_draft(ReviseTechnicalReportDraft(
        metadata("Later successor change"), successor_report.id,
        successor_report.version, successor_report.draft_revision_id,
        content(secret_values[3]), successor_report.qualification,
        successor_report.provenance,
    ))

    # Every replay returns the original endpoint-compatible lifecycle/version facts.
    assert service.create_draft(create).report.lifecycle is TechnicalReportLifecycle.DRAFT
    assert service.create_draft(create).version == created.version
    assert service.revise_draft(revise).version == revised.version
    assert service.revise_draft(revise).report.content.technical_content == secret_values[1]
    assert service.accept_exact_draft(accept).report.lifecycle is TechnicalReportLifecycle.ACCEPTED
    assert service.accept_exact_draft(accept).version == accepted.version
    assert service.create_successor(successor).version == successor_created.version
    assert service.create_successor(successor).report.content.technical_content == secret_values[2]

    conflicts = (
        lambda: service.create_draft(replace(create, content=content("conflicting create"))),
        lambda: service.revise_draft(replace(revise, content=content("conflicting revise"))),
        lambda: service.accept_exact_draft(replace(
            accept, confirmation=AcceptanceConfirmation(1, accept.confirmation.exact_draft_revision_id, True)
        )),
        lambda: service.create_successor(replace(successor, content=content("conflicting successor"))),
    )
    for conflicting_call in conflicts:
        with pytest.raises(TechnicalReportIdempotencyConflict):
            conflicting_call()

    rows = db_session.query(TechnicalReportIdempotencyRecord).filter(
        TechnicalReportIdempotencyRecord.idempotency_id.in_([
            create.metadata.idempotency_id, revise.metadata.idempotency_id,
            accept.metadata.idempotency_id, successor.metadata.idempotency_id,
        ])
    ).all()
    assert len(rows) == 4
    expected_keys = {
        "safe_result_schema_version", "report_id", "previous_version", "version",
        "draft_revision", "command_type", "correlation_id", "events",
    }
    for row in rows:
        assert row.status == "completed"
        assert set(row.result) == expected_keys
        assert row.result["safe_result_schema_version"] == 1
        encoded = json.dumps(row.result, sort_keys=True)
        assert len(encoded) < 16_384
        assert not any(value in encoded for value in secret_values)

    report_ids = (created.report_id, successor_created.report_id)
    def authoritative_counts():
        return (
            db_session.query(TechnicalReportRecord).filter(TechnicalReportRecord.id.in_(report_ids)).count(),
            db_session.query(TechnicalReportProvenanceRecord).filter(
                TechnicalReportProvenanceRecord.technical_report_id.in_(report_ids)
            ).count(),
            db_session.query(AuditLog).filter(AuditLog.entity_uuid.in_(report_ids)).count(),
            db_session.query(TechnicalReportOutboxRecord).filter(
                TechnicalReportOutboxRecord.aggregate_id.in_(report_ids)
            ).count(),
            db_session.query(TechnicalReportIdempotencyRecord).filter(
                TechnicalReportIdempotencyRecord.idempotency_id.in_([
                    create.metadata.idempotency_id, revise.metadata.idempotency_id,
                    accept.metadata.idempotency_id, successor.metadata.idempotency_id,
                ])
            ).count(),
        )

    baseline = authoritative_counts()
    membership = db_session.get(
        UserOrganizationMembership, (actor.actor_id, actor.organization_id)
    )
    membership.is_enabled = False
    membership.is_selected = False
    db_session.flush()
    for replay in (
        lambda: service.create_draft(create), lambda: service.revise_draft(revise),
        lambda: service.accept_exact_draft(accept), lambda: service.create_successor(successor),
    ):
        with pytest.raises(TechnicalReportAuthorizationDenied):
            replay()
    assert authoritative_counts() == baseline


def test_real_uow_canonical_accepted_mutations_rollback_then_audit_once(
    db_session, relationship_domain
):
    from sqlalchemy.orm import sessionmaker
    from app.models.audit_log import AuditLog
    from app.models.engineering_experience_capture import EngineeringExperienceCapture
    from app.models.technical_report import TechnicalReportRecord
    from app.models.technical_report_command import TechnicalReportIdempotencyRecord, TechnicalReportOutboxRecord
    from app.repositories.technical_report_unit_of_work import SqlAlchemyTechnicalReportUnitOfWork
    from app.exceptions.technical_report import TechnicalReportAcceptedImmutable

    actor_row = relationship_domain["actors"]["project_owner"]
    project = relationship_domain["project"]
    workspace = relationship_domain["consumer_workspace"]
    actor = TechnicalReportActor(actor_row.id, project.organization_id)
    capture = EngineeringExperienceCapture(
        id=uuid4(), organization_id=project.organization_id,
        project_id=project.id, workspace_id=workspace.id,
        discipline="electrical", engineering_object_id=None,
        source_kind="observation", original_content="Canonical protected source",
        source_reference="field-canonical", creator_id=actor.actor_id,
        lifecycle="captured", version=1, created_at=NOW, updated_at=NOW,
    )
    db_session.add(capture); db_session.flush()
    basis = CaptureHistoricalBasisV1(
        1, "universal_capture", capture.id, 1, project.organization_id,
        project.id, workspace.id, "electrical", None, "observation",
        "Canonical protected source", "field-canonical", actor.actor_id,
        "captured", NOW,
    )
    provenance = TechnicalReportProvenanceEntry(
        uuid4(), 0, TechnicalReportSourceClass.CANONICAL_MATERIAL,
        TechnicalReportSourceType.UNIVERSAL_CAPTURE, True, "universal_capture",
        "material basis", TechnicalReportVerificationStatus.VERIFIED,
        TechnicalReportAvailabilityStatus.AVAILABLE, "Human source", (), basis,
        TechnicalReportIntegrityAlgorithm.SHA256, historical_basis_digest(basis),
    )
    factory = sessionmaker(
        bind=db_session.get_bind(), expire_on_commit=False,
        join_transaction_mode="create_savepoint",
    )
    service = TechnicalReportService(
        lambda: SqlAlchemyTechnicalReportUnitOfWork(factory), Clock()
    )
    create = CreateTechnicalReportDraft(
        TechnicalReportCommandMetadata(actor, "Create", uuid4(), uuid4(), uuid4()),
        project.organization_id, workspace.id, project.id, actor.actor_id,
        TechnicalReportPurpose.ENGINEERING_ANALYSIS, content("Accepted analysis"),
        PreliminaryQualification(False), (provenance,),
    )
    created = service.create_draft(create)
    report = service.get_report(actor, created.report_id)
    service.accept_exact_draft(AcceptExactTechnicalReportDraft(
        TechnicalReportCommandMetadata(actor, "Accept", uuid4(), uuid4(), uuid4()),
        report.id, AcceptanceConfirmation(report.version, report.draft_revision_id, True),
    ))
    accepted = service.get_report(actor, report.id)
    baseline_version = accepted.version
    baseline_outbox = db_session.query(TechnicalReportOutboxRecord).filter_by(aggregate_id=report.id).count()
    baseline_idempotency = db_session.query(TechnicalReportIdempotencyRecord).filter_by(aggregate_id=report.id).count()

    revise = ReviseTechnicalReportDraft(
        TechnicalReportCommandMetadata(actor, "Forbidden revision", uuid4(), uuid4(), uuid4()),
        accepted.id, accepted.version, accepted.draft_revision_id,
        content("Forbidden accepted change"), accepted.qualification,
        accepted.provenance,
    )
    with pytest.raises(TechnicalReportAcceptedImmutable):
        service.revise_draft(revise)
    duplicate_accept = AcceptExactTechnicalReportDraft(
        TechnicalReportCommandMetadata(actor, "Duplicate acceptance", uuid4(), uuid4(), uuid4()),
        accepted.id, AcceptanceConfirmation(accepted.version, accepted.draft_revision_id, True),
    )
    with pytest.raises(TechnicalReportAcceptedImmutable):
        service.accept_exact_draft(duplicate_accept)

    db_session.expire_all()
    persisted = db_session.get(TechnicalReportRecord, report.id)
    assert persisted.version == baseline_version and persisted.lifecycle == "accepted"
    assert db_session.query(TechnicalReportOutboxRecord).filter_by(aggregate_id=report.id).count() == baseline_outbox
    assert db_session.query(TechnicalReportIdempotencyRecord).filter_by(aggregate_id=report.id).count() == baseline_idempotency
    rejected = [
        row for row in db_session.query(AuditLog).filter_by(entity_uuid=report.id).all()
        if row.details.get("outcome") == "rejected"
    ]
    assert len(rejected) == 2
    assert {row.details["reason"] for row in rejected} == {"accepted_state_mutation"}
    assert all("Canonical protected source" not in repr(row.details) for row in rejected)

    class FailingRejection:
        def _permit_after_authoritative_rollback(self): pass
        def record_rejection(self, _record): raise RuntimeError("rejection audit unavailable")
    class FailingAuditUow(SqlAlchemyTechnicalReportUnitOfWork):
        def __init__(self):
            super().__init__(factory); self.rejection_audit = FailingRejection()
    with pytest.raises(TechnicalReportAcceptedImmutable):
        TechnicalReportService(lambda: FailingAuditUow(), Clock()).revise_draft(revise)
def test_project_context_graph_provenance_read_is_bounded_owner_authorized_and_read_only():
    from pathlib import Path
    source=Path("app/services/technical_report_service.py").read_text()
    block=source[source.index("def list_authorized_graph_provenance"):source.index("def list_report_details")]
    assert "TechnicalReportAuthorizationRequest(actor,\"list\",scope)" in block
    assert "limit=91" in block and "_protected_report" in block
    assert ".commit(" not in block and ".add(" not in block
