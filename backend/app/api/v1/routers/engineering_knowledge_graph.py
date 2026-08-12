"""Thin transport for PATCH-033 executable Version 1."""

from fastapi import APIRouter, Depends
from pydantic import ValidationError

from app.dependencies.engineering_knowledge_graph import (
    EngineeringKnowledgeGraphApplication,
    get_engineering_knowledge_graph_application,
)
from app.schemas.engineering_knowledge_graph import (
    GraphNodeInvalidRequest,
    GraphNodeRequest,
    GraphNodeResult,
    GraphScope,
)


router = APIRouter(tags=["Engineering Knowledge Graph"])


@router.get(
    "/engineering-knowledge-graph/nodes/{node_id}",
    response_model=GraphNodeResult,
)
def get_engineering_knowledge_graph_node(
    node_id: str,
    project_id: int | None = None,
    workspace_id: int | None = None,
    application: EngineeringKnowledgeGraphApplication = Depends(
        get_engineering_knowledge_graph_application
    ),
) -> GraphNodeResult:
    """Serialize the single application-owned graph result."""

    try:
        request = GraphNodeRequest(node_id=node_id)
        scope = GraphScope(
            organization_id=application.actor.organization_id,
            project_id=project_id,
            workspace_id=workspace_id,
        )
    except ValidationError:
        return GraphNodeInvalidRequest()
    return application.service.get_node(
        actor=application.actor,
        scope=scope,
        request=request,
    )
