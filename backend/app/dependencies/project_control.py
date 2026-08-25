"""Request-scoped composition for PATCH-047 Project Controls."""
from dataclasses import dataclass

from fastapi import Depends
from sqlalchemy.orm import Session

from app.adapters.engineering_deliverable import SqlAlchemyDeliverableAuthorization
from app.adapters.engineering_execution_plan import ProjectFoundationApplicationAdapter, SqlAlchemyExecutionPlanAuthorization
from app.adapters.project_control_targets import CanonicalProjectControlTargetAdapter
from app.core.database import SessionLocal, get_db
from app.dependencies.auth import AuthenticatedOrganizationContext, get_current_user_organization_context
from app.dependencies.project_foundation import SqlAlchemyProjectFoundationAuthorization, get_project_foundation_application
from app.dependencies.supporting_file import _service as supporting_file_service
from app.repositories.engineering_deliverable_unit_of_work import SqlAlchemyEngineeringDeliverableUnitOfWork
from app.repositories.engineering_execution_plan_unit_of_work import SqlAlchemyEngineeringExecutionPlanUnitOfWork
from app.repositories.evidence_unit_of_work import SqlAlchemyEvidenceAuthorizationPolicy, SqlAlchemyEvidenceUnitOfWork, SqlAlchemyEvidenceValidator, UtcEvidenceClock
from app.repositories.project_control_unit_of_work import SqlAlchemyProjectControlUnitOfWork
from app.schemas.project_control import ControlActor
from app.services.engineering_deliverable_service import EngineeringDeliverableService
from app.services.engineering_execution_plan_service import EngineeringExecutionPlanService
from app.services.evidence_service import EvidenceService
from app.services.project_control_service import ProjectControlService


@dataclass(frozen=True, slots=True)
class ProjectControlApplication:
    service: ProjectControlService
    actor: ControlActor


def get_project_control_application(
    db: Session = Depends(get_db),
    context: AuthenticatedOrganizationContext = Depends(get_current_user_organization_context),
):
    actor = ControlActor(actor_id=context.user.id, organization_id=context.organization_id)
    foundation = get_project_foundation_application(db, context)
    targets = CanonicalProjectControlTargetAdapter(
        execution=EngineeringExecutionPlanService(
            uow_factory=lambda: SqlAlchemyEngineeringExecutionPlanUnitOfWork(db),
            authorization=SqlAlchemyExecutionPlanAuthorization(db),
            foundation=ProjectFoundationApplicationAdapter(foundation),
        ),
        deliverables=EngineeringDeliverableService(
            uow_factory=lambda: SqlAlchemyEngineeringDeliverableUnitOfWork(db),
            authorization=SqlAlchemyDeliverableAuthorization(db),
            supporting_files=supporting_file_service(db),
        ),
        evidence=EvidenceService(
            uow_factory=lambda: SqlAlchemyEvidenceUnitOfWork(SessionLocal),
            authorization=SqlAlchemyEvidenceAuthorizationPolicy(db),
            validator=SqlAlchemyEvidenceValidator(db), clock=UtcEvidenceClock(),
        ),
        supporting_files=supporting_file_service(db),
    )
    return ProjectControlApplication(
        service=ProjectControlService(
            uow_factory=lambda: SqlAlchemyProjectControlUnitOfWork(db),
            authorization=SqlAlchemyProjectFoundationAuthorization(db),
            target_authorization=targets,
        ), actor=actor,
    )
