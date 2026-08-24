from dataclasses import dataclass

from fastapi import Depends
from sqlalchemy.orm import Session

from app.adapters.engineering_deliverable import SqlAlchemyDeliverableAuthorization, SupportingFileApplicationAdapter
from app.core.database import get_db
from app.dependencies.auth import AuthenticatedOrganizationContext, get_current_user_organization_context
from app.dependencies.supporting_file import get_supporting_file_application
from app.repositories.engineering_deliverable_unit_of_work import SqlAlchemyEngineeringDeliverableUnitOfWork
from app.schemas.engineering_deliverable import DeliverableActor
from app.services.engineering_deliverable_service import EngineeringDeliverableService


@dataclass(frozen=True, slots=True)
class EngineeringDeliverableApplication:
    service: EngineeringDeliverableService
    actor: DeliverableActor


def get_engineering_deliverable_application(db: Session=Depends(get_db), context: AuthenticatedOrganizationContext=Depends(get_current_user_organization_context), supporting_file_application=Depends(get_supporting_file_application)):
    actor=DeliverableActor(actor_id=context.user.id,organization_id=context.organization_id)
    return EngineeringDeliverableApplication(service=EngineeringDeliverableService(uow_factory=lambda:SqlAlchemyEngineeringDeliverableUnitOfWork(db),authorization=SqlAlchemyDeliverableAuthorization(db),supporting_files=SupportingFileApplicationAdapter(supporting_file_application)),actor=actor)
