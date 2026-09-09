"""Request-scoped Identifier composition."""

from dataclasses import dataclass

from fastapi import Depends

from app.core.database import SessionLocal
from app.dependencies.auth import AuthenticatedOrganizationContext, get_current_user_organization_context
from app.repositories.engineering_identifier_unit_of_work import SqlAlchemyEngineeringIdentifierUnitOfWork
from app.services.engineering_identifier_service import EngineeringIdentifierService


@dataclass(frozen=True)
class EngineeringIdentifierApplication:
    service: EngineeringIdentifierService
    context: AuthenticatedOrganizationContext


def get_engineering_identifier_application(
    context: AuthenticatedOrganizationContext = Depends(get_current_user_organization_context),
) -> EngineeringIdentifierApplication:
    return EngineeringIdentifierApplication(
        EngineeringIdentifierService(lambda: SqlAlchemyEngineeringIdentifierUnitOfWork(SessionLocal)),
        context,
    )
