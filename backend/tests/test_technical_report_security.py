"""Focused PATCH-032 Batch 5 authorization and Human/AI boundary evidence."""

from unittest.mock import Mock
from uuid import uuid4

import pytest

from app.ai.technical_report_assistant import ProviderNeutralTechnicalReportAssistant
from app.exceptions.technical_report import (
    TechnicalReportAcceptanceAuthorityDenied,
    TechnicalReportAcceptedImmutable,
    TechnicalReportAssistantUnavailable,
    TechnicalReportAuthorizationDenied,
    TechnicalReportValidationError,
)
from app.ports.technical_report import TechnicalReportAIRequest, TechnicalReportReadCriteria, TechnicalReportScope
from app.models.technical_report_command import AcceptExactTechnicalReportDraft, AcceptanceConfirmation, TechnicalReportCommandMetadata
from app.services.technical_report_service import TechnicalReportService
from test_technical_report_service import Assistant, Clock, Uow, command, content


def test_provider_adapter_receives_only_human_instruction_and_bounded_context():
    provider = Mock()
    provider.propose.return_value = ("Advisory proposal", "provider attribution")
    actor = command().metadata.actor
    adapter = ProviderNeutralTechnicalReportAssistant(provider)
    proposal = adapter.propose(
        TechnicalReportAIRequest(actor, uuid4(), ("Human instruction", "authorized excerpt"))
    )
    provider.propose.assert_called_once_with("Human instruction", ("authorized excerpt",))
    assert proposal.attribution == "provider attribution"


@pytest.mark.parametrize(
    "context",
    [(), ("   ",), ("instruction",)],
)
def test_ai_boundary_rejects_missing_instruction_or_authorized_source_context(context):
    adapter = ProviderNeutralTechnicalReportAssistant(Mock())
    with pytest.raises(TechnicalReportValidationError):
        adapter.propose(TechnicalReportAIRequest(command().metadata.actor, uuid4(), context))


def test_invalid_provider_output_is_not_promoted_to_engineering_authority():
    provider = Mock(); provider.propose.return_value = ("", "")
    adapter = ProviderNeutralTechnicalReportAssistant(provider)
    with pytest.raises(TechnicalReportAssistantUnavailable):
        adapter.propose(TechnicalReportAIRequest(command().metadata.actor, uuid4(), ("instruction", "context")))


def test_protected_report_denial_discloses_same_outcome_for_absent_and_cross_organization():
    create = command(); repository = type("Repo", (), {})()
    from test_technical_report_service import Repository
    repository = Repository(); uow = Uow(repository)
    service = TechnicalReportService(lambda: uow, Clock(), Assistant())
    created = service.create_draft(create); report = repository.reports[created.report_id]
    outsider = type(create.metadata.actor)(99, uuid4())
    outcomes = []
    for report_id, actor in ((uuid4(), create.metadata.actor), (report.id, outsider)):
        with pytest.raises(TechnicalReportAuthorizationDenied) as caught:
            service.get_report(actor, report_id)
        outcomes.append((type(caught.value), caught.value.code, str(caught.value)))
    assert outcomes[0] == outcomes[1]


def test_accepted_summary_requires_owner_authorization_before_safe_disclosure():
    from test_technical_report_service import Repository, Uow
    create = command(); repository = Repository(); uow = Uow(repository)
    service = TechnicalReportService(lambda: uow, Clock(), Assistant())
    created = service.create_draft(create); report = repository.reports[created.report_id]
    service.accept_exact_draft(AcceptExactTechnicalReportDraft(
        TechnicalReportCommandMetadata(create.metadata.actor, "accept", uuid4(), uuid4(), uuid4()),
        report.id, AcceptanceConfirmation(report.version, report.draft_revision_id, True),
    ))
    outsider = type(create.metadata.actor)(create.metadata.actor.actor_id, uuid4())
    uow.authorization.denied_operations.add("list_accepted_summaries")
    with pytest.raises(TechnicalReportAuthorizationDenied):
        service.list_accepted_summaries(outsider, TechnicalReportReadCriteria(
            TechnicalReportScope(outsider.organization_id, report.workspace_id, report.project_id), 1, 1,
        ))
    uow.authorization.denied_operations.clear()
    uow.authorization.denied_operations.add("list_accepted_summaries")
    with pytest.raises(TechnicalReportAuthorizationDenied):
        service.list_accepted_summaries(create.metadata.actor, TechnicalReportReadCriteria(
            TechnicalReportScope(report.organization_id, report.workspace_id, report.project_id), 1, 1,
        ))


def test_ai_request_reauthorizes_current_report_and_never_commits():
    create = command()
    from test_technical_report_service import Repository
    repository = Repository(); uow = Uow(repository)
    service = TechnicalReportService(lambda: uow, Clock(), Assistant())
    created = service.create_draft(create); report = repository.reports[created.report_id]
    commits = uow.commits
    service.request_ai_proposal(
        create.metadata.actor, report.id,
        expected_version=report.version,
        expected_draft_revision_id=report.draft_revision_id,
        human_instruction="instruction",
        selected_source_entry_ids=(report.provenance[0].entry_id,),
    )
    assert uow.authorization.requests[-1].operation == "request_ai_proposal"
    assert uow.commits == commits


def test_ai_request_rejects_untrusted_source_selection_without_calling_assistant():
    create = command()
    from test_technical_report_service import Repository
    repository = Repository(); uow = Uow(repository); assistant = Mock()
    service = TechnicalReportService(lambda: uow, Clock(), assistant)
    created = service.create_draft(create); report = repository.reports[created.report_id]
    with pytest.raises(TechnicalReportAuthorizationDenied):
        service.request_ai_proposal(
            create.metadata.actor, report.id,
            expected_version=report.version,
            expected_draft_revision_id=report.draft_revision_id,
            human_instruction="instruction",
            selected_source_entry_ids=(uuid4(),),
        )
    assistant.propose.assert_not_called()


def test_ai_selected_source_is_reauthorized_and_revocation_blocks_disclosure():
    create = command()
    from test_technical_report_service import Repository
    repository = Repository(); uow = Uow(repository); assistant = Mock()
    service = TechnicalReportService(lambda: uow, Clock(), assistant)
    created = service.create_draft(create); report = repository.reports[created.report_id]
    uow.historical.resolve = Mock(side_effect=TechnicalReportAuthorizationDenied())
    with pytest.raises(TechnicalReportAuthorizationDenied):
        service.request_ai_proposal(
            create.metadata.actor, report.id,
            expected_version=report.version,
            expected_draft_revision_id=report.draft_revision_id,
            human_instruction="instruction",
            selected_source_entry_ids=(report.provenance[0].entry_id,),
        )
    assistant.propose.assert_not_called()


def test_duplicate_ai_source_selection_is_rejected():
    create = command()
    from test_technical_report_service import Repository
    repository = Repository(); uow = Uow(repository); assistant = Mock()
    service = TechnicalReportService(lambda: uow, Clock(), assistant)
    created = service.create_draft(create); report = repository.reports[created.report_id]
    source_id = report.provenance[0].entry_id
    with pytest.raises(TechnicalReportAuthorizationDenied):
        service.request_ai_proposal(
            create.metadata.actor, report.id,
            expected_version=report.version,
            expected_draft_revision_id=report.draft_revision_id,
            human_instruction="instruction",
            selected_source_entry_ids=(source_id, source_id),
        )


def test_disabled_and_failed_assistant_have_same_stable_unavailable_outcome():
    create = command()
    from test_technical_report_service import Repository
    repository = Repository(); uow = Uow(repository)
    service = TechnicalReportService(lambda: uow, Clock())
    created = service.create_draft(create); report = repository.reports[created.report_id]
    with pytest.raises(TechnicalReportAssistantUnavailable):
        service.request_ai_proposal(
            create.metadata.actor, report.id,
            expected_version=report.version,
            expected_draft_revision_id=report.draft_revision_id,
            human_instruction="instruction",
        )
    provider = Mock(); provider.propose.side_effect = RuntimeError("secret provider detail")
    adapter = ProviderNeutralTechnicalReportAssistant(provider)
    with pytest.raises(TechnicalReportAssistantUnavailable) as caught:
        adapter.propose(TechnicalReportAIRequest(create.metadata.actor, report.id, ("instruction", "context")))
    assert "secret provider detail" not in str(caught.value)


def test_cross_organization_create_records_only_bounded_post_rollback_rejection():
    create = command()
    from test_technical_report_service import Repository
    repository = Repository(); uow = Uow(repository)
    service = TechnicalReportService(lambda: uow, Clock())
    cross_scope = type(create)(
        create.metadata, uuid4(), create.workspace_id, create.project_id,
        create.owner_id, create.purpose, create.content, create.qualification,
        create.provenance,
    )
    with pytest.raises(TechnicalReportAuthorizationDenied):
        service.create_draft(cross_scope)
    assert uow.rollbacks == 1
    assert len(uow.rejection_audit.values) == 1
    record = uow.rejection_audit.values[0]
    assert record.reason.value == "cross_organization"
    assert record.report_id is None
    assert "Measured chatter" not in repr(record)


def test_non_owner_acceptance_rejection_audit_failure_never_masks_original_denial():
    create = command()
    from test_technical_report_service import Repository
    repository = Repository(); uow = Uow(repository)
    service = TechnicalReportService(lambda: uow, Clock())
    created = service.create_draft(create); report = repository.reports[created.report_id]
    original_require = uow.authorization.require
    def deny_acceptance(request):
        if request.operation == "accept_exact_draft":
            raise TechnicalReportAcceptanceAuthorityDenied()
        original_require(request)
    uow.authorization.require = deny_acceptance
    uow.rejection_audit.fail = True
    from app.models.technical_report_command import AcceptExactTechnicalReportDraft, AcceptanceConfirmation, TechnicalReportCommandMetadata
    accept = AcceptExactTechnicalReportDraft(
        TechnicalReportCommandMetadata(create.metadata.actor, "Accept exact draft", uuid4(), uuid4(), uuid4()),
        report.id, AcceptanceConfirmation(report.version, report.draft_revision_id, True),
    )
    with pytest.raises(TechnicalReportAcceptanceAuthorityDenied):
        service.accept_exact_draft(accept)
    assert uow.rollbacks == 1


def test_accepted_state_mutation_is_audited_without_plaintext():
    create = command()
    from test_technical_report_service import Repository
    from app.models.technical_report_command import AcceptExactTechnicalReportDraft, AcceptanceConfirmation, ReviseTechnicalReportDraft, TechnicalReportCommandMetadata
    repository = Repository(); uow = Uow(repository)
    service = TechnicalReportService(lambda: uow, Clock())
    created = service.create_draft(create); report = repository.reports[created.report_id]
    service.accept_exact_draft(AcceptExactTechnicalReportDraft(
        TechnicalReportCommandMetadata(create.metadata.actor, "Accept", uuid4(), uuid4(), uuid4()),
        report.id, AcceptanceConfirmation(report.version, report.draft_revision_id, True),
    ))
    revise = ReviseTechnicalReportDraft(
        TechnicalReportCommandMetadata(create.metadata.actor, "Forbidden revision", uuid4(), uuid4(), uuid4()),
        report.id, report.version, report.draft_revision_id, content("Protected changed text"),
        report.qualification, report.provenance,
    )
    with pytest.raises(TechnicalReportAcceptedImmutable):
        service.revise_draft(revise)
    record = uow.rejection_audit.values[-1]
    assert record.reason.value == "accepted_state_mutation"
    assert "Protected changed text" not in repr(record)


def test_ai_adapter_exposes_no_acceptance_or_publication_authority():
    adapter = ProviderNeutralTechnicalReportAssistant(Mock())
    assert not hasattr(adapter, "accept")
    assert not hasattr(adapter, "publish")
    assert not hasattr(adapter, "revise")


def test_concrete_policy_enforces_operation_specific_owner_authority(
    db_session, relationship_domain
):
    from app.models.technical_report import TechnicalReportRecord
    from app.ports.technical_report import TechnicalReportAuthorizationRequest, TechnicalReportScope
    from app.repositories.technical_report_unit_of_work import SqlAlchemyTechnicalReportAuthorizationPolicy

    create = command()
    project = relationship_domain["project"]
    workspace = relationship_domain["consumer_workspace"]
    owner = relationship_domain["actors"]["project_owner"]
    non_owner = relationship_domain["actors"]["consumer"]
    report = TechnicalReportRecord(
        id=uuid4(), organization_id=project.organization_id,
        workspace_id=workspace.id, project_id=project.id, owner_id=non_owner.id,
        purpose="engineering_analysis", engineering_scope="Scope",
        draft_content="Draft", assumptions=[], uncertainty="Known",
        limitations=[], conclusions="Conclusion", recommendations=[],
        is_preliminary=False, evidence_deficiencies=[], unresolved_issues=[],
        follow_up_requirements=[], draft_revision_id=uuid4(),
        draft_revision_number=1, lifecycle="draft", version=1,
    )
    db_session.add(report); db_session.flush()
    actor = type(create.metadata.actor)(owner.id, project.organization_id)
    scope = TechnicalReportScope(project.organization_id, workspace.id, project.id)
    policy = SqlAlchemyTechnicalReportAuthorizationPolicy(db_session)
    for operation in ("create_draft", "list"):
        policy.require(TechnicalReportAuthorizationRequest(actor, operation, scope))
    for operation in ("get", "retrieve_lineage"):
        policy.require(TechnicalReportAuthorizationRequest(actor, operation, scope, report.id))
    for operation in (
        "revise_draft", "accept_exact_draft", "create_successor",
        "request_ai_proposal",
    ):
        with pytest.raises(TechnicalReportAuthorizationDenied):
            policy.require(TechnicalReportAuthorizationRequest(actor, operation, scope, report.id))
def test_graph_provenance_link_contract_excludes_human_and_report_content():
    from app.ports.technical_report import TechnicalReportGraphProvenanceLink
    assert set(TechnicalReportGraphProvenanceLink.__dataclass_fields__)=={"report_id","entry_id","source_kind","source_id","report_version","accepted_at"}
    assert not ({"accepted_by_id","owner_id","content","rationale","origin_attribution","limitations"}&set(TechnicalReportGraphProvenanceLink.__dataclass_fields__))
