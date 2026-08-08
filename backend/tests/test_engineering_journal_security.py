"""PATCH-029 Sprint 2 authorization and disclosure evidence."""

from uuid import uuid4

import pytest

from app.adapters.engineering_journal import (
    EngineeringJournalCapabilityAvailabilityAdapter,
    EngineeringJournalCaptureNavigationAdapter,
    EngineeringJournalCaptureReadAdapter,
    EngineeringJournalProjectSelectionAdapter,
    EngineeringJournalScopeAuthorizationAdapter,
)
from app.enums.engineering_experience_capture import EngineeringExperienceSourceKind
from app.enums.engineering_journal import EngineeringJournalView
from app.exceptions.engineering_experience_capture import (
    EngineeringExperienceCaptureProtectedNotFound,
)
from app.exceptions.engineering_journal import EngineeringJournalProtectedNotFound
from app.exceptions.project import ProjectForbiddenException
from app.models.engineering_experience_capture_command import (
    EngineeringExperienceCaptureActor,
)
from app.models.engineering_object import EngineeringObject
from app.models.organization import (
    Organization,
    UserOrganizationMembership,
)
from app.schemas.engineering_journal import (
    EngineeringJournalAuthenticatedActor,
    EngineeringJournalCaptureDetailDTO,
)
from app.schemas.engineering_experience_capture import (
    EngineeringExperienceCaptureCreate,
    SupersedeEngineeringExperienceCaptureRequest,
)
from app.schemas.project import ProjectSelectionActor
from app.services.project_service import ProjectService
from app.services.engineering_experience_capture_service import (
    EngineeringExperienceCaptureService,
)
from app.services.engineering_journal_service import EngineeringJournalService

from test_engineering_experience_capture_service import (
    SharedSessionCaptureUnitOfWork,
    _actor as capture_actor,
    _create as create_capture,
    _service as capture_service,
)


def _actor():
    return EngineeringJournalAuthenticatedActor(
        actor_id=7, organization_id=uuid4()
    )


def _scope_adapter(db_session):
    return EngineeringJournalScopeAuthorizationAdapter(
        uow_factory=lambda: SharedSessionCaptureUnitOfWork(db_session),
        project_service=ProjectService(db_session),
    )


def _journal_actor(domain, name="project_owner"):
    return EngineeringJournalAuthenticatedActor(
        actor_id=domain["actors"][name].id,
        organization_id=domain["project"].organization_id,
    )


def _assert_protected(call) -> tuple[int, str, str]:
    with pytest.raises(EngineeringJournalProtectedNotFound) as caught:
        call()
    assert caught.value.status_code == 404
    assert "organization" not in caught.value.message.lower()
    assert "membership" not in caught.value.message.lower()
    return caught.value.status_code, caught.value.code, caught.value.message


def test_projectless_scope_denies_inactive_user(
    db_session, relationship_domain
) -> None:
    domain = relationship_domain
    outcome = _assert_protected(
        lambda: _scope_adapter(db_session).authorize_scope(
            actor=_journal_actor(domain, "inactive"),
            project_id=None,
            workspace_id=None,
            engineering_object_id=None,
            view=EngineeringJournalView.INBOX,
        )
    )
    assert outcome == (404, "ENGINEERING_JOURNAL_NOT_FOUND", "Engineering Journal resource not found")


def test_projectless_scope_denies_disabled_membership(
    db_session, relationship_domain
) -> None:
    domain = relationship_domain
    owner = domain["actors"]["project_owner"]
    membership = db_session.get(
        UserOrganizationMembership,
        (owner.id, domain["project"].organization_id),
    )
    membership.is_selected = False
    membership.is_enabled = False
    db_session.flush()
    _assert_protected(
        lambda: _scope_adapter(db_session).authorize_scope(
            actor=_journal_actor(domain),
            project_id=None,
            workspace_id=None,
            engineering_object_id=None,
            view=EngineeringJournalView.INBOX,
        )
    )


def test_projectless_scope_denies_inactive_organization(
    db_session, relationship_domain
) -> None:
    domain = relationship_domain
    organization = db_session.get(Organization, domain["project"].organization_id)
    organization.is_active = False
    db_session.flush()
    _assert_protected(
        lambda: _scope_adapter(db_session).authorize_scope(
            actor=_journal_actor(domain),
            project_id=None,
            workspace_id=None,
            engineering_object_id=None,
            view=EngineeringJournalView.INBOX,
        )
    )


def test_projectless_scope_denies_nonmember(
    db_session, relationship_domain
) -> None:
    domain = relationship_domain
    owner = domain["actors"]["project_owner"]
    db_session.delete(
        db_session.get(
            UserOrganizationMembership,
            (owner.id, domain["project"].organization_id),
        )
    )
    db_session.flush()
    _assert_protected(
        lambda: _scope_adapter(db_session).authorize_scope(
            actor=_journal_actor(domain),
            project_id=None,
            workspace_id=None,
            engineering_object_id=None,
            view=EngineeringJournalView.INBOX,
        )
    )


def test_scope_denies_cross_organization_project(
    db_session, relationship_domain
) -> None:
    actor = _journal_actor(relationship_domain).model_copy(
        update={"organization_id": uuid4()}
    )
    _assert_protected(
        lambda: _scope_adapter(db_session).authorize_scope(
            actor=actor,
            project_id=relationship_domain["project"].id,
            workspace_id=None,
            engineering_object_id=None,
            view=EngineeringJournalView.INBOX,
        )
    )


def test_scope_denies_cross_project_workspace(
    db_session, relationship_domain
) -> None:
    domain = relationship_domain
    _assert_protected(
        lambda: _scope_adapter(db_session).authorize_scope(
            actor=_journal_actor(domain),
            project_id=domain["project"].id,
            workspace_id=domain["other_workspace"].id,
            engineering_object_id=None,
            view=EngineeringJournalView.INBOX,
        )
    )


def test_scope_denies_cross_workspace_engineering_object(
    db_session, relationship_domain
) -> None:
    domain = relationship_domain
    owner = domain["actors"]["project_owner"]
    object_record = EngineeringObject(
        id=uuid4(),
        organization_id=domain["project"].organization_id,
        project_id=domain["project"].id,
        workspace_id=domain["consumer_workspace"].id,
        family="electrical",
        discipline="electrical",
        object_type="motor",
        lifecycle="proposed",
        authority_standing="draft",
        version=1,
        creator_id=owner.id,
        steward_id=owner.id,
    )
    db_session.add(object_record)
    db_session.flush()
    _assert_protected(
        lambda: _scope_adapter(db_session).authorize_scope(
            actor=_journal_actor(domain),
            project_id=domain["project"].id,
            workspace_id=domain["provider_workspace"].id,
            engineering_object_id=object_record.id,
            view=EngineeringJournalView.INBOX,
        )
    )


def test_scope_reauthorizes_after_membership_revocation(
    db_session, relationship_domain
) -> None:
    domain = relationship_domain
    adapter = _scope_adapter(db_session)
    actor = _journal_actor(domain)
    assert adapter.authorize_scope(
        actor=actor,
        project_id=domain["project"].id,
        workspace_id=None,
        engineering_object_id=None,
        view=EngineeringJournalView.INBOX,
    ).project_id == domain["project"].id
    membership = db_session.get(
        UserOrganizationMembership,
        (actor.actor_id, actor.organization_id),
    )
    membership.is_selected = False
    membership.is_enabled = False
    db_session.flush()
    _assert_protected(
        lambda: adapter.authorize_scope(
            actor=actor,
            project_id=domain["project"].id,
            workspace_id=None,
            engineering_object_id=None,
            view=EngineeringJournalView.INBOX,
        )
    )


class DeniedProjectService:
    def list_authorized_selection(self, **values):
        raise ProjectForbiddenException("sensitive membership reason")


def test_project_selection_denial_hides_membership_diagnostics() -> None:
    adapter = EngineeringJournalProjectSelectionAdapter(DeniedProjectService())
    with pytest.raises(EngineeringJournalProtectedNotFound) as caught:
        adapter.list_authorized(actor=_actor(), page=1, size=20)
    assert "membership" not in caught.value.message.lower()


def test_projectless_scope_rejects_subordinate_client_context() -> None:
    adapter = EngineeringJournalScopeAuthorizationAdapter(
        uow_factory=lambda: None,
        project_service=DeniedProjectService(),
    )
    with pytest.raises(EngineeringJournalProtectedNotFound):
        adapter.authorize_scope(
            actor=_actor(),
            project_id=None,
            workspace_id=4,
            engineering_object_id=None,
            view=EngineeringJournalView.INBOX,
        )


def test_journal_actor_contains_only_trusted_minimum_context() -> None:
    assert set(EngineeringJournalAuthenticatedActor.model_fields) == {
        "actor_id",
        "organization_id",
    }


def test_protected_error_contains_no_plaintext_or_hidden_identifiers() -> None:
    error = EngineeringJournalProtectedNotFound()
    serialized = f"{error.code} {error.message}".lower()
    for forbidden in (
        "original_content",
        "source_reference",
        "rationale",
        "organization_id",
        "workspace_id",
        "engineering_object_id",
    ):
        assert forbidden not in serialized


def test_canonical_project_selection_applies_existing_actor_visibility(
    db_session, relationship_domain
) -> None:
    domain = relationship_domain
    consumer = domain["actors"]["consumer"]
    result = ProjectService(db_session).list_authorized_selection(
        actor=ProjectSelectionActor(
            actor_id=consumer.id,
            organization_id=domain["project"].organization_id,
        ),
        page=1,
        size=100,
    )
    identifiers = {item.project_id for item in result.items}
    assert domain["project"].id in identifiers
    assert domain["other_project"].id not in identifiers
    assert result.returned_count == len(result.items)
    assert "total" not in type(result).model_fields


def test_canonical_project_selection_reauthorizes_disabled_membership(
    db_session, relationship_domain
) -> None:
    domain = relationship_domain
    owner = domain["actors"]["project_owner"]
    membership = db_session.get(
        UserOrganizationMembership,
        (owner.id, domain["project"].organization_id),
    )
    membership.is_selected = False
    membership.is_enabled = False
    db_session.flush()
    with pytest.raises(ProjectForbiddenException):
        ProjectService(db_session).list_authorized_selection(
            actor=ProjectSelectionActor(
                actor_id=owner.id,
                organization_id=domain["project"].organization_id,
            ),
            page=1,
            size=20,
        )


def test_canonical_capture_read_and_detail_reauthorize_current_actor(
    db_session, relationship_domain
) -> None:
    service = capture_service(db_session)
    domain = relationship_domain
    actor = capture_actor(domain)
    created = create_capture(service, domain, actor)
    service.create(
        data=EngineeringExperienceCaptureCreate(
            project_id=domain["project"].id,
            workspace_id=domain["consumer_workspace"].id,
            source_kind=EngineeringExperienceSourceKind.QUESTION,
            original_content="A second authorized Capture.",
        ),
        actor=actor,
        correlation_id=uuid4(),
        idempotency_id=uuid4(),
    )
    page = service.read_authorized_page(
        actor=actor,
        project_id=domain["project"].id,
        workspace_id=domain["consumer_workspace"].id,
        engineering_object_id=None,
        lifecycle="captured",
        source_kind=EngineeringExperienceSourceKind.OBSERVATION,
        discipline=None,
        page=1,
        size=20,
    )
    assert page.authorized_total == 2
    assert page.filtered_total == 1
    assert page.visible_total == 1
    assert "original_content" not in type(page.items[0]).model_fields
    detail = service.read_authorized_detail(
        actor=actor,
        project_id=domain["project"].id,
        workspace_id=domain["consumer_workspace"].id,
        engineering_object_id=None,
        capture_id=created.id,
    )
    assert detail.original_content == created.original_content

    denied = EngineeringExperienceCaptureActor(
        domain["actors"]["unrelated"].id,
        domain["project"].organization_id,
    )
    with pytest.raises(EngineeringExperienceCaptureProtectedNotFound):
        service.read_authorized_detail(
            actor=denied,
            project_id=domain["project"].id,
            workspace_id=domain["consumer_workspace"].id,
            engineering_object_id=None,
            capture_id=created.id,
        )


def _create_scoped_capture(service, domain, actor, workspace, content):
    return service.create(
        data=EngineeringExperienceCaptureCreate(
            project_id=domain["project"].id,
            workspace_id=workspace.id,
            source_kind=EngineeringExperienceSourceKind.OBSERVATION,
            original_content=content,
        ),
        actor=actor,
        correlation_id=uuid4(),
        idempotency_id=uuid4(),
    )


def _supersede(service, original, replacement, actor):
    return service.supersede(
        original.id,
        SupersedeEngineeringExperienceCaptureRequest(
            expected_version=original.version,
            replacement_capture_id=replacement.id,
            rationale="Approved replacement",
        ),
        actor,
        uuid4(),
        uuid4(),
    )


def test_inaccessible_replacement_identity_is_omitted_without_disclosure(
    db_session, relationship_domain
) -> None:
    domain = relationship_domain
    service = capture_service(db_session)
    owner = capture_actor(domain)
    original = _create_scoped_capture(
        service, domain, owner, domain["consumer_workspace"], "Original"
    )
    replacement = _create_scoped_capture(
        service, domain, owner, domain["consumer_workspace"], "Protected replacement"
    )
    _supersede(service, original, replacement, owner)

    class ReplacementDeniedAuthorization:
        def __init__(self, delegate):
            self._delegate = delegate

        def authorize(self, **values):
            capture = values.get("capture")
            if capture is not None and capture.id == replacement.id:
                return False
            return self._delegate.authorize(**values)

        def project_list_workspace_scope(self, **values):
            return self._delegate.project_list_workspace_scope(**values)

    class ReplacementDeniedUnitOfWork(SharedSessionCaptureUnitOfWork):
        def __enter__(self):
            result = super().__enter__()
            self.authorization = ReplacementDeniedAuthorization(self.authorization)
            return result

    protected_service = EngineeringExperienceCaptureService(
        uow_factory=lambda: ReplacementDeniedUnitOfWork(db_session)
    )
    consumer = capture_actor(domain, "consumer")
    detail = protected_service.read_authorized_detail(
        actor=consumer,
        project_id=domain["project"].id,
        workspace_id=domain["consumer_workspace"].id,
        engineering_object_id=None,
        capture_id=original.id,
    )
    assert detail.superseded_by_capture_id is None
    assert str(replacement.id) not in detail.model_dump_json()


def test_independently_authorized_replacement_identity_is_disclosed(
    db_session, relationship_domain
) -> None:
    domain = relationship_domain
    service = capture_service(db_session)
    owner = capture_actor(domain)
    original = _create_scoped_capture(
        service, domain, owner, domain["consumer_workspace"], "Original"
    )
    replacement = _create_scoped_capture(
        service, domain, owner, domain["consumer_workspace"], "Visible replacement"
    )
    _supersede(service, original, replacement, owner)
    detail = service.read_authorized_detail(
        actor=capture_actor(domain, "consumer"),
        project_id=domain["project"].id,
        workspace_id=domain["consumer_workspace"].id,
        engineering_object_id=None,
        capture_id=original.id,
    )
    assert detail.superseded_by_capture_id == replacement.id


def test_journal_detail_exposes_no_unapproved_supersession_chain_identity() -> None:
    assert "supersession_chain" not in EngineeringJournalCaptureDetailDTO.model_fields
    assert "predecessor_capture_ids" not in EngineeringJournalCaptureDetailDTO.model_fields


def test_unauthorized_detail_and_navigation_are_protected(
    db_session, relationship_domain
) -> None:
    domain = relationship_domain
    canonical = capture_service(db_session)
    created = create_capture(canonical, domain)
    factory = lambda: SharedSessionCaptureUnitOfWork(db_session)
    service = EngineeringJournalService(
        scope_authorization=EngineeringJournalScopeAuthorizationAdapter(
            uow_factory=factory,
            project_service=ProjectService(db_session),
        ),
        project_selection=EngineeringJournalProjectSelectionAdapter(
            ProjectService(db_session)
        ),
        capture_read=EngineeringJournalCaptureReadAdapter(uow_factory=factory),
        capture_navigation=EngineeringJournalCaptureNavigationAdapter(),
        capability_availability=EngineeringJournalCapabilityAvailabilityAdapter(),
    )
    actor = _journal_actor(domain, "unrelated")
    for operation in (service.detail, service.capture_navigation):
        _assert_protected(
            lambda operation=operation: operation(
                actor=actor,
                capture_id=created.id,
                project_id=domain["project"].id,
                workspace_id=domain["consumer_workspace"].id,
            )
        )
