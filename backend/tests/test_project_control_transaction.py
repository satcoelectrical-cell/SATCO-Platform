from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker

import pytest

from app.models.audit_log import AuditLog
from app.models.project_control import ProjectChangeImpact, ProjectControlIdempotency, ProjectControlOutbox, ProjectRisk
from app.repositories.project_control_unit_of_work import SqlAlchemyProjectControlUnitOfWork
from app.services.project_control_service import ProjectControlService
from tests.test_project_control_service import Authorization, Targets, change, domain, risk
from app.schemas.project_control import ChangeCommand, ConfirmImpactCommand, ImpactCommand
from app.core.database import engine
from uuid import uuid4


class FailingOutboxUow(SqlAlchemyProjectControlUnitOfWork):
    def stage_outbox(self, record): raise SQLAlchemyError("injected outbox failure")


class FailingAuditUow(SqlAlchemyProjectControlUnitOfWork):
    def stage_audit(self, **_): raise SQLAlchemyError("injected audit failure")


class FailingIdempotencyUow(SqlAlchemyProjectControlUnitOfWork):
    def stage_idempotency(self, record): raise SQLAlchemyError("injected idempotency failure")


def test_outbox_failure_rolls_back_root_history_audit_and_idempotency(db_session):
    _, actor, project = domain(db_session)
    project_id = project.id
    service = ProjectControlService(uow_factory=lambda: FailingOutboxUow(db_session), authorization=Authorization())
    assert service.create_risk(project_id=project_id, data=risk(), actor=actor, idempotency_key=uuid4()).outcome == "unavailable"
    assert db_session.query(ProjectRisk).filter_by(project_id=project_id).count() == 0
    assert db_session.query(ProjectControlOutbox).filter_by(project_id=project_id).count() == 0


@pytest.mark.parametrize("uow_type", (FailingAuditUow, FailingIdempotencyUow))
def test_audit_or_idempotency_failure_rolls_back_all_primary_facts(db_session, uow_type):
    _, actor, project = domain(db_session); project_id = project.id
    service = ProjectControlService(uow_factory=lambda: uow_type(db_session), authorization=Authorization())
    assert service.create_risk(project_id=project_id, data=risk(), actor=actor, idempotency_key=uuid4()).outcome == "unavailable"
    assert db_session.query(ProjectRisk).filter_by(project_id=project_id).count() == 0
    assert db_session.query(ProjectControlOutbox).filter_by(project_id=project_id).count() == 0
    assert db_session.query(ProjectControlIdempotency).filter_by(project_id=project_id).count() == 0
    assert db_session.query(AuditLog).filter_by(entity="PROJECT_CONTROL", entity_id=project_id).count() == 0


@pytest.mark.parametrize("uow_type", (FailingAuditUow, FailingOutboxUow, FailingIdempotencyUow))
def test_change_impact_reliability_failure_rolls_back_child_and_replay(db_session, uow_type):
    targets=Targets(); service, actor, project=domain(db_session,targets)
    change_result=service.create_change(project_id=project.id,data=change(),actor=actor,idempotency_key=uuid4())
    failing=ProjectControlService(uow_factory=lambda: uow_type(db_session),authorization=Authorization(),target_authorization=targets)
    outcome=failing.create_change_impact(data=ImpactCommand(change_id=change_result.id,target_kind="activity",target_id=uuid4(),statement="Activity may be affected",rationale="Human potential impact",expected_version=1),actor=actor,idempotency_key=uuid4())
    assert outcome.outcome=="unavailable"
    assert db_session.query(ProjectChangeImpact).filter_by(change_id=change_result.id).count()==0
    assert db_session.query(ProjectControlIdempotency).filter_by(project_id=project.id,operation="create_change_impact").count()==0


def test_real_postgresql_change_successor_impact_and_confirmation_races_have_one_winner(db_session):
    targets=Targets(); service, actor, project=domain(db_session,targets)
    predecessor=service.create_change(project_id=project.id,data=change(),actor=actor,idempotency_key=uuid4())
    db_session.connection().commit()
    factory=sessionmaker(bind=engine,expire_on_commit=False)
    def threaded_service(): return ProjectControlService(uow_factory=lambda: SqlAlchemyProjectControlUnitOfWork(factory()),authorization=Authorization(),target_authorization=targets)

    barrier=Barrier(2)
    def successor(_):
        barrier.wait()
        return threaded_service().create_change_successor(change_id=predecessor.id,data=ChangeCommand(statement="Corrected routing condition",rationale="Human correction",predecessor_id=predecessor.id),actor=actor,idempotency_key=uuid4()).outcome
    with ThreadPoolExecutor(max_workers=2) as pool: successor_outcomes=list(pool.map(successor,range(2)))
    assert sorted(successor_outcomes)==["success","version_conflict"]

    barrier=Barrier(2)
    # Separate UUIDs are distinct facts; a same target gives the actual duplicate race.
    duplicate_target=uuid4()
    def duplicate_impact(_):
        barrier.wait()
        return threaded_service().create_change_impact(data=ImpactCommand(change_id=predecessor.id,target_kind="activity",target_id=duplicate_target,statement="Activity may be affected",rationale="Human potential impact",expected_version=1),actor=actor,idempotency_key=uuid4()).outcome
    with ThreadPoolExecutor(max_workers=2) as pool: impact_outcomes=list(pool.map(duplicate_impact,range(2)))
    assert sorted(impact_outcomes)==["success","version_conflict"]
    with Session(engine) as verify:
        impact_id=verify.query(ProjectChangeImpact).filter_by(change_id=predecessor.id,target_id=duplicate_target).one().id
    barrier=Barrier(2)
    def confirm(_):
        barrier.wait()
        return threaded_service().confirm_change_impact(impact_id=impact_id,data=ConfirmImpactCommand(expected_change_version=1,rationale="Human confirms impact"),actor=actor,idempotency_key=uuid4()).outcome
    with ThreadPoolExecutor(max_workers=2) as pool: confirm_outcomes=list(pool.map(confirm,range(2)))
    assert sorted(confirm_outcomes)==["invalid_request","success"]
