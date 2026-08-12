"""Closed, immutable contracts for PATCH-033 executable Version 1."""

from datetime import datetime
from typing import Annotated, Literal, TypeAlias
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.enums import EngineeringAuthorityStanding
from app.enums import EngineeringDiscipline
from app.enums import EngineeringLifecycle
from app.enums import EngineeringObjectFamily
from app.enums import EngineeringObjectType
from app.schemas.engineering_object import EngineeringObjectResponse


class EngineeringKnowledgeGraphDTO(BaseModel):
    """Strict immutable base for executable V1 application contracts."""

    model_config = ConfigDict(extra="forbid", frozen=True)


class GraphActor(EngineeringKnowledgeGraphDTO):
    """Trusted authenticated Human and server-derived Organization context."""

    actor_id: int
    organization_id: UUID


class GraphScope(EngineeringKnowledgeGraphDTO):
    """Optional scope criteria checked against an authorized canonical node."""

    organization_id: UUID
    project_id: int | None = None
    workspace_id: int | None = None


class GraphNodeRequest(EngineeringKnowledgeGraphDTO):
    """The only executable V1 graph request."""

    node_id: UUID


class GraphNodeProjection(EngineeringKnowledgeGraphDTO):
    """Exact authorized EngineeringObjectResponse parity plus a discriminator."""

    node_type: Literal["engineering_object"] = "engineering_object"
    node_id: UUID
    organization_id: UUID
    customer_id: int | None
    project_id: int
    workspace_id: int
    family: EngineeringObjectFamily
    discipline: EngineeringDiscipline
    object_type: EngineeringObjectType
    subtype: str | None
    lifecycle: EngineeringLifecycle
    authority_standing: EngineeringAuthorityStanding
    version: int
    creator_id: int
    steward_id: int
    created_at: datetime
    updated_at: datetime

class GraphNodeSuccess(EngineeringKnowledgeGraphDTO):
    """Successful one-node projection."""

    status: Literal["success"] = "success"
    node: GraphNodeProjection


class GraphNodeProtectedNotFound(EngineeringKnowledgeGraphDTO):
    """Payload-free protected outcome."""

    status: Literal["protected_not_found"] = "protected_not_found"


class GraphNodeInvalidRequest(EngineeringKnowledgeGraphDTO):
    """Payload-free invalid-request outcome."""

    status: Literal["invalid_request"] = "invalid_request"


class GraphNodeUnavailable(EngineeringKnowledgeGraphDTO):
    """Payload-free canonical-capability-unavailable outcome."""

    status: Literal["unavailable"] = "unavailable"


GraphNodeResult: TypeAlias = Annotated[
    GraphNodeSuccess
    | GraphNodeProtectedNotFound
    | GraphNodeInvalidRequest
    | GraphNodeUnavailable,
    Field(discriminator="status"),
]


class CanonicalEngineeringObjectResolved(EngineeringKnowledgeGraphDTO):
    """One authorized canonical Engineering Object response."""

    status: Literal["resolved"] = "resolved"
    response: EngineeringObjectResponse


class CanonicalEngineeringObjectProtected(EngineeringKnowledgeGraphDTO):
    """Payload-free canonical protected result."""

    status: Literal["protected"] = "protected"


class CanonicalEngineeringObjectUnavailable(EngineeringKnowledgeGraphDTO):
    """Payload-free canonical availability result."""

    status: Literal["unavailable"] = "unavailable"


CanonicalEngineeringObjectReadResult: TypeAlias = Annotated[
    CanonicalEngineeringObjectResolved
    | CanonicalEngineeringObjectProtected
    | CanonicalEngineeringObjectUnavailable,
    Field(discriminator="status"),
]


class GraphScopeAuthorized(EngineeringKnowledgeGraphDTO):
    """Trusted actor and Organization context may proceed to canonical read."""

    status: Literal["authorized"] = "authorized"


class GraphScopeProtected(EngineeringKnowledgeGraphDTO):
    """Payload-free trusted-context denial."""

    status: Literal["protected"] = "protected"


ScopeAuthorizationDecision: TypeAlias = Annotated[
    GraphScopeAuthorized | GraphScopeProtected,
    Field(discriminator="status"),
]
