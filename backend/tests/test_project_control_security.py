from app.models.engineering_execution_plan import EngineeringExecutionActivity
from app.adapters.project_control_targets import TargetInvalid
from app.schemas.project_control import ImpactCommand
from tests.test_project_control_service import Targets, change, domain, issue
from uuid import uuid4


def test_issue_command_never_creates_or_mutates_execution_blockers(db_session):
    service, actor, project = domain(db_session)
    before = db_session.query(EngineeringExecutionActivity).filter_by(project_id=project.id).count()
    assert service.create_issue(project_id=project.id, data=issue(), actor=actor, idempotency_key=uuid4()).outcome == "success"
    assert db_session.query(EngineeringExecutionActivity).filter_by(project_id=project.id).count() == before


def test_denied_change_target_is_payload_free_and_persists_no_impact(db_session):
    targets=Targets(denied=True); service,actor,project=domain(db_session,targets)
    recorded=service.create_change(project_id=project.id,data=change(),actor=actor,idempotency_key=uuid4())
    outcome=service.create_change_impact(data=ImpactCommand(change_id=recorded.id,target_kind="evidence",target_id=uuid4(),statement="Evidence may be affected",rationale="Human potential impact",expected_version=1),actor=actor,idempotency_key=uuid4())
    assert outcome.model_dump()=={"outcome":"protected_not_found"}


def test_unsupported_target_discriminator_is_payload_free_invalid_request(db_session):
    class UnsupportedTarget:
        def authorize_exact(self, **_):
            raise TargetInvalid()
    service,actor,project=domain(db_session,UnsupportedTarget())
    recorded=service.create_change(project_id=project.id,data=change(),actor=actor,idempotency_key=uuid4())
    outcome=service.create_change_impact(data=ImpactCommand(change_id=recorded.id,target_kind="activity",target_id=uuid4(),statement="Activity may be affected",rationale="Human potential impact",expected_version=1),actor=actor,idempotency_key=uuid4())
    assert outcome.model_dump()=={"outcome":"invalid_request"}
