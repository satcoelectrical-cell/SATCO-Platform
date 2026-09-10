import pytest

from app.discipline_packages.cross_discipline.contracts import (
    LIMITS, enforce_resource_limit,
)
from app.discipline_packages.cross_discipline.graph import BoundedGraph, Edge, GraphLimitExceeded, Node


@pytest.mark.parametrize("name,exact", tuple(LIMITS.items()))
def test_frozen_limits_have_normal_exact_and_one_over_boundaries(name, exact):
    assert LIMITS[name] == exact
    assert enforce_resource_limit(name, exact - 1) == exact - 1
    assert enforce_resource_limit(name, exact) == exact
    with pytest.raises(ValueError, match="resource_limit_exceeded"):
        enforce_resource_limit(name, exact + 1)


def test_graph_node_limit_accepts_exact_and_rejects_one_over():
    graph = BoundedGraph()
    for index in range(LIMITS["nodes"]):
        graph.add_node(Node("engineering_object", str(index)))
    assert len(graph.nodes) == LIMITS["nodes"]
    with pytest.raises(GraphLimitExceeded):
        graph.add_node(Node("engineering_object", "overflow"))
