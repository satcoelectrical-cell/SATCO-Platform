from uuid import uuid4

import pytest

from app.enums.engineering_experience_capture import EngineeringExperienceSourceKind
from app.exceptions.engineering_experience_capture import (
    EngineeringExperienceCaptureProtectedNotFound,
    EngineeringExperienceCaptureVersionConflict,
)
from app.models.engineering_experience_capture_command import EngineeringExperienceCaptureActor
from app.models.engineering_workspace import EngineeringWorkspace
from app.repositories.engineering_experience_capture_repository import (
    SqlAlchemyEngineeringExperienceCaptureRepository,
)
from app.repositories.engineering_experience_capture_unit_of_work import (
    SqlAlchemyCaptureAuditRecorder,
    SqlAlchemyCaptureAuthorizationPolicy,
    SqlAlchemyCaptureContextValidator,
    SqlAlchemyCaptureDomainEventRecorder,
    SqlAlchemyCaptureIdempotencyStore,
    SqlAlchemyCaptureSupersessionValidator,
    UtcCaptureClock,
)
from app.schemas.engineering_experience_capture import (
    EngineeringExperienceCaptureCreate,
    EngineeringExperienceCaptureFilter,
    WithdrawEngineeringExperienceCaptureRequest,
    SupersedeEngineeringExperienceCaptureRequest,
)
from app.services.engineering_experience_capture_service import (
    EngineeringExperienceCaptureService,
)


class SharedSessionCaptureUnitOfWork:
    def __init__(self, session):
        self.session = session

    def __enter__(self):
        self.transaction = self.session.begin_nested()
        self.captures = SqlAlchemyEngineeringExperienceCaptureRepository(self.session)
        self.authorization = SqlAlchemyCaptureAuthorizationPolicy(self.session)
        self.context = SqlAlchemyCaptureContextValidator(self.session)
        self.supersession = SqlAlchemyCaptureSupersessionValidator(self.session, self.captures)
        self.audit = SqlAlchemyCaptureAuditRecorder(self.session)
        self.domain_events = SqlAlchemyCaptureDomainEventRecorder(self.session)
        self.idempotency = SqlAlchemyCaptureIdempotencyStore(self.session)
        self.clock = UtcCaptureClock()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if exc_type is not None and self.transaction.is_active:
            self.transaction.rollback()

    def commit(self):
        self.session.flush()
        self.transaction.commit()

    def rollback(self):
        if self.transaction.is_active:
            self.transaction.rollback()


def _service(db_session):
    return EngineeringExperienceCaptureService(
        uow_factory=lambda: SharedSessionCaptureUnitOfWork(db_session)
    )


def _actor(domain, name="project_owner"):
    user = domain["actors"][name]
    return EngineeringExperienceCaptureActor(user.id, domain["project"].organization_id)


def _create(service, domain, actor=None):
    actor = actor or _actor(domain)
    return service.create(
        data=EngineeringExperienceCaptureCreate(
            project_id=domain["project"].id,
            workspace_id=domain["consumer_workspace"].id,
            source_kind=EngineeringExperienceSourceKind.OBSERVATION,
            original_content="  A bounded engineering observation.  ",
        ),
        actor=actor, correlation_id=uuid4(), idempotency_id=uuid4(),
    )


def test_service_create_read_list_and_withdraw(db_session, relationship_domain):
    service = _service(db_session)
    actor = _actor(relationship_domain)
    created = _create(service, relationship_domain, actor)
    assert created.original_content == "A bounded engineering observation."
    assert created.allowed_actions == ("withdraw", "supersede")
    assert service.get(created.id, actor).id == created.id
    listed = service.list_workspace(
        created.workspace_id, EngineeringExperienceCaptureFilter(), 1, 20, actor
    )
    assert listed.total == 1
    assert listed.items[0].id == created.id
    withdrawn = service.withdraw(
        created.id,
        WithdrawEngineeringExperienceCaptureRequest(expected_version=1, rationale="No longer current"),
        actor, uuid4(), uuid4(),
    )
    assert withdrawn.lifecycle.value == "withdrawn"
    assert withdrawn.version == 2
    assert withdrawn.allowed_actions == ()


def test_service_returns_version_conflict_without_state_change(db_session, relationship_domain):
    service = _service(db_session)
    actor = _actor(relationship_domain)
    created = _create(service, relationship_domain, actor)
    with pytest.raises(EngineeringExperienceCaptureVersionConflict):
        service.withdraw(
            created.id,
            WithdrawEngineeringExperienceCaptureRequest(expected_version=2, rationale="Stale"),
            actor, uuid4(), uuid4(),
        )
    assert service.get(created.id, actor).version == 1


def test_service_authorizes_before_disclosure(db_session, relationship_domain):
    service = _service(db_session)
    created = _create(service, relationship_domain)
    with pytest.raises(EngineeringExperienceCaptureProtectedNotFound):
        service.get(created.id, _actor(relationship_domain, "unrelated"))


@pytest.mark.parametrize("operation", ["get", "withdraw", "supersede", "chain"])
def test_protected_not_found_for_every_single_capture_operation(
    db_session, relationship_domain, operation
):
    service = _service(db_session)
    created = _create(service, relationship_domain)
    unauthorized = _actor(relationship_domain, "unrelated")
    with pytest.raises(EngineeringExperienceCaptureProtectedNotFound):
        if operation == "get":
            service.get(created.id, unauthorized)
        elif operation == "withdraw":
            service.withdraw(
                created.id,
                WithdrawEngineeringExperienceCaptureRequest(expected_version=1, rationale="secret rationale"),
                unauthorized, uuid4(), uuid4(),
            )
        elif operation == "supersede":
            service.supersede(
                created.id,
                SupersedeEngineeringExperienceCaptureRequest(
                    expected_version=1, rationale="secret rationale",
                    replacement_capture_id=uuid4(),
                ), unauthorized, uuid4(), uuid4(),
            )
        else:
            service.supersession_chain(created.id, unauthorized)


def test_project_list_omits_unauthorized_workspace_rows_and_has_accurate_total(
    db_session, relationship_domain
):
    service = _service(db_session)
    owner = _actor(relationship_domain)
    visible_actor = _actor(relationship_domain, "consumer")
    visible = _create(service, relationship_domain, owner)
    provider_workspace = EngineeringWorkspace(
        project_id=relationship_domain["project"].id,
        discipline="control", status="active",
        owner_id=relationship_domain["actors"]["provider"].id,
        created_by_id=relationship_domain["actors"]["project_owner"].id,
        version=1,
    )
    db_session.add(provider_workspace)
    db_session.flush()
    service.create(
        data=EngineeringExperienceCaptureCreate(
            project_id=relationship_domain["project"].id,
            workspace_id=provider_workspace.id,
            source_kind=EngineeringExperienceSourceKind.QUESTION,
            original_content="Provider-only experience",
        ), actor=owner, correlation_id=uuid4(), idempotency_id=uuid4(),
    )
    result = service.list_project(
        relationship_domain["project"].id, EngineeringExperienceCaptureFilter(),
        1, 20, visible_actor,
    )
    assert [item.id for item in result.items] == [visible.id]
    assert result.total == 1


def test_exact_replay_reauthorizes_and_revocation_discloses_no_stored_content(
    db_session, relationship_domain
):
    service = _service(db_session)
    actor = _actor(relationship_domain)
    idempotency_id = uuid4()
    data = EngineeringExperienceCaptureCreate(
        project_id=relationship_domain["project"].id,
        workspace_id=relationship_domain["consumer_workspace"].id,
        source_kind=EngineeringExperienceSourceKind.OBSERVATION,
        original_content="REVOKED-CONTENT-SECRET",
        source_reference="REVOKED-REFERENCE-SECRET",
    )
    service.create(data=data, actor=actor, correlation_id=uuid4(), idempotency_id=idempotency_id)
    relationship_domain["project"].owner_id = None
    relationship_domain["project"].primary_assignee_id = None
    db_session.flush()
    with pytest.raises(EngineeringExperienceCaptureProtectedNotFound) as failure:
        service.create(data=data, actor=actor, correlation_id=uuid4(), idempotency_id=idempotency_id)
    rendered = str(failure.value)
    assert "REVOKED-CONTENT-SECRET" not in rendered
    assert "REVOKED-REFERENCE-SECRET" not in rendered


def test_exact_replay_returns_authorized_result_after_reauthorization(
    db_session, relationship_domain
):
    service = _service(db_session)
    actor = _actor(relationship_domain)
    idempotency_id = uuid4()
    data = EngineeringExperienceCaptureCreate(
        project_id=relationship_domain["project"].id,
        workspace_id=relationship_domain["consumer_workspace"].id,
        source_kind=EngineeringExperienceSourceKind.OBSERVATION,
        original_content="Authorized replay content",
        source_reference="Authorized replay reference",
    )
    first = service.create(
        data=data, actor=actor, correlation_id=uuid4(), idempotency_id=idempotency_id
    )
    replay = service.create(
        data=data, actor=actor, correlation_id=uuid4(), idempotency_id=idempotency_id
    )
    assert replay.id == first.id
    assert replay.original_content == first.original_content
    assert replay.source_reference == first.source_reference
