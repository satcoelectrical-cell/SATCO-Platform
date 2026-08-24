from dataclasses import dataclass

from fastapi import Depends
from sqlalchemy.orm import Session

from app.adapters.engineering_execution_plan import ProjectFoundationApplicationAdapter, SqlAlchemyExecutionPlanAuthorization
from app.core.database import get_db
from app.dependencies.auth import AuthenticatedOrganizationContext, get_current_user_organization_context
from app.dependencies.project_foundation import get_project_foundation_application
from app.repositories.engineering_execution_plan_unit_of_work import SqlAlchemyEngineeringExecutionPlanUnitOfWork
from app.schemas.engineering_execution_plan import ExecutionActor
from app.services.engineering_execution_plan_service import EngineeringExecutionPlanService


@dataclass(frozen=True, slots=True)
class EngineeringExecutionPlanApplication:
    service: EngineeringExecutionPlanService
    actor: ExecutionActor


def get_engineering_execution_plan_application(
    db: Session = Depends(get_db),
    context: AuthenticatedOrganizationContext = Depends(get_current_user_organization_context),
    foundation_application=Depends(get_project_foundation_application),
):
    actor = ExecutionActor(actor_id=context.user.id, organization_id=context.organization_id)
    return EngineeringExecutionPlanApplication(
        service=EngineeringExecutionPlanService(
            uow_factory=lambda: SqlAlchemyEngineeringExecutionPlanUnitOfWork(db),
            authorization=SqlAlchemyExecutionPlanAuthorization(db),
            foundation=ProjectFoundationApplicationAdapter(foundation_application),
        ),
        actor=actor,
    )
