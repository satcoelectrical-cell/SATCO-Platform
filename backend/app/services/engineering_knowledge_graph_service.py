"""Node-only application service for PATCH-033 executable Version 1."""

from app.ports.engineering_knowledge_graph import (
    CanonicalEngineeringObjectReadPort,
    GraphScopeAuthorizationPort,
)
from app.schemas.engineering_knowledge_graph import (
    CanonicalEngineeringObjectProtected,
    CanonicalEngineeringObjectResolved,
    GraphActor,
    GraphNodeInvalidRequest,
    GraphNodeProjection,
    GraphNodeProtectedNotFound,
    GraphNodeRequest,
    GraphNodeResult,
    GraphNodeSuccess,
    GraphNodeUnavailable,
    GraphScope,
    GraphScopeProtected,
)


class EngineeringKnowledgeGraphService:
    """Orchestrate the single accepted, read-only graph operation."""

    def __init__(
        self,
        *,
        scope_authorization: GraphScopeAuthorizationPort,
        engineering_objects: CanonicalEngineeringObjectReadPort,
    ) -> None:
        self._scope_authorization = scope_authorization
        self._engineering_objects = engineering_objects

    def get_node(
        self,
        *,
        actor: GraphActor,
        scope: GraphScope,
        request: GraphNodeRequest,
    ) -> GraphNodeResult:
        if not isinstance(request, GraphNodeRequest):
            return GraphNodeInvalidRequest()

        scope_decision = self._scope_authorization.authorize(
            actor=actor,
            scope=scope,
        )
        if isinstance(scope_decision, GraphScopeProtected):
            return GraphNodeProtectedNotFound()

        canonical = self._engineering_objects.get_authorized(
            actor=actor,
            scope=scope,
            node_id=request.node_id,
        )
        if isinstance(canonical, CanonicalEngineeringObjectProtected):
            return GraphNodeProtectedNotFound()
        if not isinstance(canonical, CanonicalEngineeringObjectResolved):
            return GraphNodeUnavailable()

        response = canonical.response
        projection = GraphNodeProjection(
            node_id=response.id,
            **response.model_dump(exclude={"id"}),
        )
        return GraphNodeSuccess(node=projection)
