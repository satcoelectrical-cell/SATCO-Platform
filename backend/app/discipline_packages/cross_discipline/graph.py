from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from typing import Literal

from .contracts import LIMITS


@dataclass(frozen=True, order=True)
class Node:
    kind: str
    identity: str


@dataclass(frozen=True, order=True)
class Edge:
    kind: str
    source: Node
    target: Node


class GraphLimitExceeded(ValueError): pass


@dataclass(frozen=True, slots=True)
class PathResult:
    outcome: Literal["satisfied", "violated", "indeterminate"]
    path: tuple[Edge, ...] = ()
    reason: str | None = None


class BoundedGraph:
    def __init__(self) -> None:
        self.nodes: set[Node] = set(); self.edges: set[Edge] = set()

    def add_node(self, node: Node) -> None:
        if node not in self.nodes and len(self.nodes) >= LIMITS["nodes"]: raise GraphLimitExceeded("resource_limit_exceeded")
        self.nodes.add(node)

    def add_edge(self, edge: Edge) -> None:
        self.add_node(edge.source); self.add_node(edge.target)
        if edge not in self.edges and len(self.edges) >= LIMITS["edges"]: raise GraphLimitExceeded("resource_limit_exceeded")
        self.edges.add(edge)

    def path_exists(self, start: Node, target: Node, allowed_kinds: tuple[str, ...]) -> bool:
        return self.evaluate_path(start, target, allowed_kinds).outcome == "satisfied"

    def evaluate_path(self, start: Node, target: Node, allowed_kinds: tuple[str, ...]) -> PathResult:
        queue = deque([(start, tuple())]); visited = {start}
        cycle = False
        while queue:
            node, path = queue.popleft()
            if node == target: return PathResult("satisfied", path)
            outgoing = sorted(edge for edge in self.edges if edge.source == node and edge.kind in allowed_kinds)
            if len(outgoing) > LIMITS["fanout"]: raise GraphLimitExceeded("resource_limit_exceeded")
            for edge in outgoing:
                if edge.target in visited:
                    cycle = True
                    continue
                if len(path) >= LIMITS["depth"]:
                    raise GraphLimitExceeded("resource_limit_exceeded")
                visited.add(edge.target); queue.append((edge.target, path + (edge,)))
        if cycle:
            return PathResult("indeterminate", reason="source_ambiguous")
        return PathResult("violated")
