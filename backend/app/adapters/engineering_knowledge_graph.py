"""Canonical adapters for PATCH-033 executable Version 1."""

from uuid import UUID

from app.exceptions.engineering_object import (
    EngineeringObjectAuthorizationDenied,
    EngineeringObjectInternalServerError,
    EngineeringObjectProtectedNotFound,
)
from app.models.engineering_object_command import (
    AuthenticatedActor,
    AuthorizationContext,
)
from app.schemas.engineering_knowledge_graph import (
    CanonicalEngineeringObjectProtected,
    CanonicalEngineeringObjectReadResult,
    CanonicalEngineeringObjectResolved,
    CanonicalEngineeringObjectUnavailable,
    GraphActor,
    GraphScope,
    GraphScopeAuthorized,
    GraphScopeProtected,
    ScopeAuthorizationDecision,
)
from app.services.engineering_object_service import EngineeringObjectService


class TrustedGraphScopeAuthorizationAdapter:
    """Validate consistency of already trusted server-derived context."""

    def authorize(
        self,
        *,
        actor: GraphActor,
        scope: GraphScope,
    ) -> ScopeAuthorizationDecision:
        if actor.actor_id < 1 or actor.organization_id != scope.organization_id:
            return GraphScopeProtected()
        return GraphScopeAuthorized()


class CanonicalEngineeringObjectReadAdapter:
    """Adapt one canonical authorized Engineering Object application read."""

    def __init__(
        self,
        engineering_object_service: EngineeringObjectService,
    ) -> None:
        self._service = engineering_object_service

    def get_authorized(
        self,
        *,
        actor: GraphActor,
        scope: GraphScope,
        node_id: UUID,
    ) -> CanonicalEngineeringObjectReadResult:
        canonical_actor = AuthenticatedActor(
            actor_id=actor.actor_id,
            organization_id=actor.organization_id,
        )
        context = AuthorizationContext(
            operation="ReadEngineeringObject",
            scope={"object_id": node_id},
        )
        try:
            response = self._service.get(node_id, canonical_actor, context)
        except (
            EngineeringObjectAuthorizationDenied,
            EngineeringObjectProtectedNotFound,
        ):
            return CanonicalEngineeringObjectProtected()
        except EngineeringObjectInternalServerError:
            return CanonicalEngineeringObjectUnavailable()
        except Exception:
            # The canonical application boundary may surface infrastructure
            # failures directly. EKG exposes only its closed, payload-free
            # availability outcome and never forwards internal diagnostics.
            return CanonicalEngineeringObjectUnavailable()

        if response.organization_id != scope.organization_id:
            return CanonicalEngineeringObjectProtected()
        if scope.project_id is not None and response.project_id != scope.project_id:
            return CanonicalEngineeringObjectProtected()
        if (
            scope.workspace_id is not None
            and response.workspace_id != scope.workspace_id
        ):
            return CanonicalEngineeringObjectProtected()
        return CanonicalEngineeringObjectResolved(response=response)
