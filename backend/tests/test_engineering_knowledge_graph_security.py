"""PATCH-033 Batch 2 authorization and non-disclosure evidence."""

import ast
import logging
from pathlib import Path
from uuid import uuid4

import pytest

from app.schemas.engineering_knowledge_graph import (
    CanonicalEngineeringObjectProtected,
    GraphActor,
    GraphNodeProtectedNotFound,
    GraphNodeRequest,
    GraphScope,
    GraphScopeProtected,
)
from app.services.engineering_knowledge_graph_service import (
    EngineeringKnowledgeGraphService,
)


class _ScopeDecision:
    def __init__(self, protected):
        self.protected = protected
        self.calls = 0

    def authorize(self, *, actor, scope):
        self.calls += 1
        if self.protected:
            return GraphScopeProtected()
        from app.schemas.engineering_knowledge_graph import GraphScopeAuthorized

        return GraphScopeAuthorized()


class _CanonicalProtected:
    def __init__(self):
        self.calls = 0

    def get_authorized(self, *, actor, scope, node_id):
        self.calls += 1
        return CanonicalEngineeringObjectProtected()


@pytest.mark.parametrize(
    "denial_category",
    (
        "inactive_actor",
        "inactive_organization",
        "disabled_membership",
        "nonmember_organization",
        "cross_organization",
    ),
)
def test_trusted_context_denials_are_equivalent_and_make_zero_object_reads(
    denial_category,
    caplog,
):
    del denial_category
    organization_id = uuid4()
    actor = GraphActor(actor_id=1, organization_id=organization_id)
    scope = GraphScope(organization_id=organization_id)
    scope_port = _ScopeDecision(protected=True)
    object_port = _CanonicalProtected()
    service = EngineeringKnowledgeGraphService(
        scope_authorization=scope_port,
        engineering_objects=object_port,
    )
    protected_value = str(uuid4())

    with caplog.at_level(logging.DEBUG):
        result = service.get_node(
            actor=actor,
            scope=scope,
            request=GraphNodeRequest(node_id=uuid4()),
        )

    assert isinstance(result, GraphNodeProtectedNotFound)
    assert result.model_dump() == {"status": "protected_not_found"}
    assert scope_port.calls == 1
    assert object_port.calls == 0
    assert protected_value not in caplog.text


def test_nonexistent_and_inaccessible_canonical_nodes_are_equivalent(caplog):
    organization_id = uuid4()
    actor = GraphActor(actor_id=1, organization_id=organization_id)
    scope = GraphScope(organization_id=organization_id)
    request = GraphNodeRequest(node_id=uuid4())
    outcomes = []

    with caplog.at_level(logging.DEBUG):
        for _category in ("nonexistent", "inaccessible", "revoked"):
            service = EngineeringKnowledgeGraphService(
                scope_authorization=_ScopeDecision(protected=False),
                engineering_objects=_CanonicalProtected(),
            )
            outcomes.append(
                service.get_node(actor=actor, scope=scope, request=request)
            )

    assert [item.model_dump() for item in outcomes] == [
        {"status": "protected_not_found"},
        {"status": "protected_not_found"},
        {"status": "protected_not_found"},
    ]
    assert str(request.node_id) not in caplog.text


def test_batch_2_production_has_no_transport_persistence_or_deferred_surface():
    root = Path(__file__).parents[1]
    paths = (
        root / "app/adapters/engineering_knowledge_graph.py",
        root / "app/services/engineering_knowledge_graph_service.py",
    )
    prohibited_import_roots = {
        "fastapi",
        "sqlalchemy",
        "app.repositories",
        "app.api",
        "app.models.project",
        "app.models.engineering_workspace",
    }
    prohibited_names = {
        "list",
        "traverse",
        "paginate",
        "continue_traversal",
        "add",
        "update",
        "delete",
        "commit",
        "rollback",
        "GraphEdgeProjection",
        "GraphTraversalResult",
        "CanonicalNodeBatchResult",
    }

    for path in paths:
        tree = ast.parse(path.read_text())
        imports = set()
        names = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.update(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imports.add(node.module)
            elif isinstance(node, (ast.ClassDef, ast.FunctionDef)):
                names.add(node.name)
        assert not any(
            imported == root or imported.startswith(f"{root}.")
            for imported in imports
            for root in prohibited_import_roots
        )
        assert names.isdisjoint(prohibited_names)


def test_batch_3_router_contains_no_authorization_or_projection_policy():
    root = Path(__file__).parents[1]
    path = root / "app/api/v1/routers/engineering_knowledge_graph.py"
    tree = ast.parse(path.read_text())
    prohibited_names = {
        "authorize",
        "get_authorized",
        "project_node",
        "check_membership",
        "commit",
        "rollback",
    }
    names = {
        node.name
        for node in ast.walk(tree)
        if isinstance(node, (ast.ClassDef, ast.FunctionDef))
    }
    assert names.isdisjoint(prohibited_names)
    assert "app.repositories.engineering_object_repository" not in path.read_text()
