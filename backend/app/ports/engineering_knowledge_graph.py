"""Inward-owned protocols for PATCH-033 executable Version 1."""

from typing import Protocol
from uuid import UUID

from app.schemas.engineering_knowledge_graph import (
    CanonicalEngineeringObjectReadResult,
    GraphActor,
    GraphNodeRequest,
    GraphNodeResult,
    GraphScope,
    ScopeAuthorizationDecision,
)


class GraphScopeAuthorizationPort(Protocol):
    """Validate trusted actor and server-derived Organization context."""

    def authorize(
        self,
        *,
        actor: GraphActor,
        scope: GraphScope,
    ) -> ScopeAuthorizationDecision: ...


class CanonicalEngineeringObjectReadPort(Protocol):
    """Resolve one authorized canonical Engineering Object only."""

    def get_authorized(
        self,
        *,
        actor: GraphActor,
        scope: GraphScope,
        node_id: UUID,
    ) -> CanonicalEngineeringObjectReadResult: ...


class GraphReadService(Protocol):
    """The complete executable V1 EKG application boundary."""

    def get_node(
        self,
        *,
        actor: GraphActor,
        scope: GraphScope,
        request: GraphNodeRequest,
    ) -> GraphNodeResult: ...
