"""PATCH-033 Batch 1 contract and projection-foundation evidence."""

import ast
from datetime import datetime, timezone
from pathlib import Path
from typing import get_args, get_type_hints
from uuid import UUID, uuid4

import pytest
from pydantic import TypeAdapter, ValidationError

from app.enums import EngineeringAuthorityStanding
from app.enums import EngineeringDiscipline
from app.enums import EngineeringLifecycle
from app.enums import EngineeringObjectFamily
from app.enums import EngineeringObjectType
from app.ports.engineering_knowledge_graph import (
    CanonicalEngineeringObjectReadPort,
    GraphReadService,
    GraphScopeAuthorizationPort,
)
from app.schemas.engineering_knowledge_graph import (
    CanonicalEngineeringObjectProtected,
    CanonicalEngineeringObjectReadResult,
    CanonicalEngineeringObjectResolved,
    CanonicalEngineeringObjectUnavailable,
    GraphActor,
    GraphNodeInvalidRequest,
    GraphNodeProjection,
    GraphNodeProtectedNotFound,
    GraphNodeRequest,
    GraphNodeResult,
    GraphNodeSuccess,
    GraphNodeUnavailable,
    GraphScope,
    GraphScopeAuthorized,
    GraphScopeProtected,
    ScopeAuthorizationDecision,
)
from app.schemas.engineering_object import EngineeringObjectResponse


NOW = datetime(2026, 8, 12, tzinfo=timezone.utc)


def _canonical_response() -> EngineeringObjectResponse:
    return EngineeringObjectResponse(
        id=uuid4(),
        organization_id=uuid4(),
        customer_id=None,
        project_id=11,
        workspace_id=12,
        family=EngineeringObjectFamily.ELECTRICAL,
        discipline=EngineeringDiscipline.ELECTRICAL,
        object_type=EngineeringObjectType.MOTOR,
        subtype=None,
        lifecycle=EngineeringLifecycle.ACTIVE,
        authority_standing=EngineeringAuthorityStanding.APPROVED,
        version=3,
        creator_id=5,
        steward_id=6,
        created_at=NOW,
        updated_at=NOW,
    )


def _projection(
    response: EngineeringObjectResponse | None = None,
) -> GraphNodeProjection:
    response = response or _canonical_response()
    return GraphNodeProjection(
        node_id=response.id,
        **response.model_dump(exclude={"id"}),
    )


def test_actor_scope_and_request_are_exact_strict_immutable_products() -> None:
    organization_id = uuid4()
    actor = GraphActor(actor_id=1, organization_id=organization_id)
    scope = GraphScope(organization_id=organization_id)
    request = GraphNodeRequest(node_id=uuid4())

    assert set(type(actor).model_fields) == {"actor_id", "organization_id"}
    assert set(type(scope).model_fields) == {
        "organization_id", "project_id", "workspace_id"
    }
    assert set(type(request).model_fields) == {"node_id"}
    assert scope.project_id is None and scope.workspace_id is None

    for contract, values in (
        (GraphActor, {"actor_id": 1, "organization_id": organization_id}),
        (GraphScope, {"organization_id": organization_id}),
        (GraphNodeRequest, {"node_id": request.node_id}),
    ):
        with pytest.raises(ValidationError):
            contract(**values, unauthorized="value")

    with pytest.raises(ValidationError):
        actor.actor_id = 2


def test_projection_has_exact_canonical_parity_and_discriminator() -> None:
    response = _canonical_response()
    projection = _projection(response)
    canonical_fields = set(EngineeringObjectResponse.model_fields)

    assert set(GraphNodeProjection.model_fields) == {
        "node_type",
        "node_id",
        *(canonical_fields - {"id"}),
    }
    assert projection.node_type == "engineering_object"
    assert projection.node_id == response.id
    assert projection.model_dump(exclude={"node_type", "node_id"}) == (
        response.model_dump(exclude={"id"})
    )

    projection_hints = get_type_hints(GraphNodeProjection)
    response_hints = get_type_hints(EngineeringObjectResponse)
    assert projection_hints["node_id"] is response_hints["id"] is UUID
    for field_name in canonical_fields - {"id"}:
        assert projection_hints[field_name] == response_hints[field_name]


def test_projection_imposes_no_stronger_scalar_constraints() -> None:
    response = _canonical_response().model_copy(
        update={"version": 0, "creator_id": 0, "steward_id": 0}
    )
    projection = _projection(response)
    assert projection.version == 0
    assert projection.creator_id == 0
    assert projection.steward_id == 0


def test_graph_result_is_closed_to_four_exact_variants() -> None:
    projection = _projection()
    adapter = TypeAdapter(GraphNodeResult)
    variants = get_args(get_args(GraphNodeResult)[0])

    assert set(variants) == {
        GraphNodeSuccess,
        GraphNodeProtectedNotFound,
        GraphNodeInvalidRequest,
        GraphNodeUnavailable,
    }
    assert adapter.validate_python(
        {"status": "success", "node": projection}
    ).node == projection
    for status, expected in (
        ("protected_not_found", GraphNodeProtectedNotFound),
        ("invalid_request", GraphNodeInvalidRequest),
        ("unavailable", GraphNodeUnavailable),
    ):
        result = adapter.validate_python({"status": status})
        assert isinstance(result, expected)
        assert result.model_dump() == {"status": status}
        with pytest.raises(ValidationError):
            adapter.validate_python({"status": status, "detail": "secret"})


def test_canonical_read_and_scope_decisions_are_closed() -> None:
    canonical_adapter = TypeAdapter(CanonicalEngineeringObjectReadResult)
    scope_adapter = TypeAdapter(ScopeAuthorizationDecision)

    resolved = canonical_adapter.validate_python(
        {"status": "resolved", "response": _canonical_response()}
    )
    assert isinstance(resolved, CanonicalEngineeringObjectResolved)
    for status, expected in (
        ("protected", CanonicalEngineeringObjectProtected),
        ("unavailable", CanonicalEngineeringObjectUnavailable),
    ):
        result = canonical_adapter.validate_python({"status": status})
        assert isinstance(result, expected)
        assert result.model_dump() == {"status": status}

    assert isinstance(
        scope_adapter.validate_python({"status": "authorized"}),
        GraphScopeAuthorized,
    )
    protected = scope_adapter.validate_python({"status": "protected"})
    assert isinstance(protected, GraphScopeProtected)
    assert protected.model_dump() == {"status": "protected"}


def test_ports_declare_only_the_three_accepted_operations() -> None:
    public_methods = lambda protocol: {
        name
        for name, value in vars(protocol).items()
        if callable(value) and not name.startswith("_")
    }

    assert public_methods(GraphScopeAuthorizationPort) == {"authorize"}
    assert public_methods(CanonicalEngineeringObjectReadPort) == {
        "get_authorized"
    }
    assert public_methods(GraphReadService) == {"get_node"}


def test_s01_modules_contain_no_deferred_or_write_contracts() -> None:
    root = Path(__file__).parents[1]
    paths = (
        root / "app/schemas/engineering_knowledge_graph.py",
        root / "app/ports/engineering_knowledge_graph.py",
    )
    prohibited_names = {
        "GraphEdgeProjection",
        "GraphTraversalResult",
        "GraphProvenanceReference",
        "CanonicalNodeBatchResult",
        "ContinuationCodecPort",
        "Repository",
        "UnitOfWork",
    }
    prohibited_methods = {
        "list", "traverse", "paginate", "continue_traversal", "add",
        "update", "delete", "commit", "rollback",
    }

    for path in paths:
        tree = ast.parse(path.read_text())
        names = {
            node.name
            for node in ast.walk(tree)
            if isinstance(node, (ast.ClassDef, ast.FunctionDef))
        }
        assert names.isdisjoint(prohibited_names)
        assert names.isdisjoint(prohibited_methods)
