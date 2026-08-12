"""Request-scoped composition root for PATCH-033 executable Version 1."""

from dataclasses import dataclass

from fastapi import Depends
from sqlalchemy.orm import Session

from app.adapters.engineering_knowledge_graph import (
    CanonicalEngineeringObjectReadAdapter,
    TrustedGraphScopeAuthorizationAdapter,
)
from app.core.database import SessionLocal, get_db
from app.dependencies.auth import (
    AuthenticatedOrganizationContext,
    get_current_user_organization_context,
)
from app.repositories.engineering_object_unit_of_work import (
    SqlAlchemyAuthorizationPolicy,
    SqlAlchemyEngineeringObjectUnitOfWork,
    SqlAlchemyReferenceValidator,
    UtcClock,
)
from app.schemas.engineering_knowledge_graph import GraphActor
from app.services.engineering_knowledge_graph_service import (
    EngineeringKnowledgeGraphService,
)
from app.services.engineering_object_service import EngineeringObjectService


def get_engineering_object_read_service(
    db: Session = Depends(get_db),
) -> EngineeringObjectService:
    """Construct the existing canonical read boundary per request."""

    return EngineeringObjectService(
        uow_factory=lambda: SqlAlchemyEngineeringObjectUnitOfWork(SessionLocal),
        authorization=SqlAlchemyAuthorizationPolicy(db),
        references=SqlAlchemyReferenceValidator(db),
        clock=UtcClock(),
    )


@dataclass(frozen=True, slots=True)
class EngineeringKnowledgeGraphApplication:
    """Composed node-only service and server-trusted actor."""

    service: EngineeringKnowledgeGraphService
    actor: GraphActor


def get_engineering_knowledge_graph_application(
    organization: AuthenticatedOrganizationContext = Depends(
        get_current_user_organization_context
    ),
    engineering_objects: EngineeringObjectService = Depends(
        get_engineering_object_read_service
    ),
) -> EngineeringKnowledgeGraphApplication:
    actor = GraphActor(
        actor_id=organization.user.id,
        organization_id=organization.organization_id,
    )
    return EngineeringKnowledgeGraphApplication(
        service=EngineeringKnowledgeGraphService(
            scope_authorization=TrustedGraphScopeAuthorizationAdapter(),
            engineering_objects=CanonicalEngineeringObjectReadAdapter(
                engineering_objects
            ),
        ),
        actor=actor,
    )
