from datetime import datetime, timezone
from uuid import UUID, uuid4

from app.dependencies.project_foundation import SqlAlchemyProjectFoundationAuthorization
from app.enums import ProjectEngineeringStage, ProjectInputSourceKind
from app.models.customer import Customer
from app.models.project import Project
from app.models.evidence import Evidence
from app.repositories.project_foundation_unit_of_work import SqlAlchemyProjectFoundationUnitOfWork
from app.schemas.project_foundation import (
    CreateProjectInputRequest, ProjectFoundationActor, ProjectInputSafeSource,
    PutProjectFoundationRequest, TransitionProjectInputRequest, TransitionProjectStageRequest,
)
from app.services.project_foundation_service import ProjectFoundationService
from conftest import create_user
from app.permissions.roles import Role


ORG = UUID("02810000-0000-4000-8000-000000000001")


class Sources:
    def authorize_exact(self, *, kind, source_id, workspace_id, **_):
        return ProjectInputSafeSource(kind=kind, source_id=source_id, version=1, workspace_id=workspace_id)
    def list_authorized(self, **_): return ()


class UnavailableSources(Sources):
    def authorize_exact(self, **_):
        from app.exceptions.project_foundation import ProjectFoundationUnavailable
        raise ProjectFoundationUnavailable()


def domain(db_session):
    owner = create_user(db_session, username=f"foundation-{uuid4().hex[:8]}", role=Role.ENGINEER)
    customer = Customer(name=f"Foundation {uuid4().hex[:8]}", organization_id=ORG)
    db_session.add(customer); db_session.flush()
    project = Project(organization_id=ORG, project_code=f"SAT-PRJ-2098-{customer.id+4000:04d}", name="Foundation Project", customer_id=customer.id, owner_id=owner.id, status="new", priority="medium", progress=0)
    db_session.add(project); db_session.commit(); db_session.refresh(project)
    service = ProjectFoundationService(
        uow_factory=lambda: SqlAlchemyProjectFoundationUnitOfWork(db_session),
        authorization=SqlAlchemyProjectFoundationAuthorization(db_session), sources=Sources(),
    )
    return service, ProjectFoundationActor(actor_id=owner.id, organization_id=ORG), project


def basis(expected=0):
    return PutProjectFoundationRequest(
        expected_version=expected, purpose="Automate material handling safely",
        engineering_basis="Control, panel and field integration engineering",
        in_scope=("Control-system engineering",), out_of_scope=("Civil construction",),
        completion_criteria=("Recorded basis is ready for later completion assessment",),
        rationale="Human-defined Project basis",
    )


def test_legacy_project_is_truthful_then_establishes_versioned_basis(db_session):
    service, actor, project = domain(db_session)
    absent = service.get(project_id=project.id, actor=actor)
    assert absent.availability == "basis_not_established" and not hasattr(absent, "stage")
    result = service.put(project_id=project.id, data=basis(), actor=actor)
    assert result.availability == "established" and result.stage == "definition" and result.version == 1
    assert result.next_stage_readiness.state == "blocked"
    assert result.next_stage_readiness.blockers[0].code == "required_inputs_not_defined"


def test_input_lifecycle_and_human_stage_transition_are_explicit(db_session):
    service, actor, project = domain(db_session)
    foundation = service.put(project_id=project.id, data=basis(), actor=actor)
    created = service.create_input(project_id=project.id, actor=actor, data=CreateProjectInputRequest(
        expected_foundation_version=foundation.version, title="Customer requirements",
        description="Current issued requirements", ordinal=0, required_by_stage="preparation",
        rationale="Required before preparation",
    ))
    transitioned = service.transition_input(project_id=project.id, input_id=created.item.id, actor=actor, data=TransitionProjectInputRequest(
        expected_foundation_version=created.foundation_version, expected_input_version=created.item.version,
        target_standing="not_applicable", rationale="No separate requirements exist for this bounded Project",
    ))
    assert transitioned.item.standing == "not_applicable"
    read = service.get(project_id=project.id, actor=actor)
    assert read.stage == "definition" and read.next_stage_readiness.state == "ready"
    moved = service.transition_stage(project_id=project.id, actor=actor, data=TransitionProjectStageRequest(
        expected_foundation_version=read.version, target_stage=ProjectEngineeringStage.PREPARATION,
        rationale="Human confirms preparation may begin",
    ))
    assert moved.outcome == "success" and moved.stage == "preparation"


def test_stale_version_and_stage_skip_are_closed(db_session):
    service, actor, project = domain(db_session)
    foundation = service.put(project_id=project.id, data=basis(), actor=actor)
    assert service.put(project_id=project.id, data=basis(0), actor=actor).outcome == "version_conflict"
    result = service.transition_stage(project_id=project.id, actor=actor, data=TransitionProjectStageRequest(
        expected_foundation_version=foundation.version, target_stage="execution", rationale="Skip",
    ))
    assert result.outcome == "invalid_request"


def test_real_source_dependency_unavailability_is_not_a_readiness_or_invalid_result(db_session):
    service, actor, project = domain(db_session)
    foundation = service.put(project_id=project.id, data=basis(), actor=actor)
    created = service.create_input(project_id=project.id, actor=actor, data=CreateProjectInputRequest(
        expected_foundation_version=foundation.version, title="Current Evidence", description=None,
        ordinal=0, required_by_stage="preparation", rationale="Required source",
    ))
    source_id = uuid4()
    now = datetime.now(timezone.utc)
    db_session.add(Evidence(
        id=source_id, organization_id=ORG, project_id=project.id, workspace_id=None,
        lifecycle="current", source_kind="engineering_record", source_reference="authorized-ref",
        source_revision="1", source_standing="current", supported_fact="Authorized current basis",
        creator_id=actor.actor_id, version=1, created_at=now, updated_at=now,
    ))
    db_session.commit()
    received = service.transition_input(project_id=project.id, input_id=created.item.id, actor=actor, data=TransitionProjectInputRequest(
        expected_foundation_version=created.foundation_version, expected_input_version=created.item.version,
        target_standing="received", source_kind="evidence", source_id=source_id,
        source_workspace_id=None, rationale="Current source received",
    ))
    assert received.outcome == "success"
    service.sources = UnavailableSources()
    assert service.get(project_id=project.id, actor=actor).outcome == "unavailable"
    result = service.transition_stage(project_id=project.id, actor=actor, data=TransitionProjectStageRequest(
        expected_foundation_version=received.foundation_version, target_stage="preparation", rationale="Attempt",
    ))
    assert result.outcome == "unavailable"
