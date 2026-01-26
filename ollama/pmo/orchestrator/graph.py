"""Dependency graph utilities for orchestrator."""
from typing import Dict, List, Set


class DependencyGraph:
    """Simple directed dependency graph with topological sort.

    Nodes are arbitrary hashable identifiers (e.g., repo names). Edges are
    directed: A -> B means A depends on B (B must be applied before A).
    """

    def __init__(self) -> None:
        self._edges: Dict[object, Set[object]] = {}

    def add_node(self, node: object) -> None:
        self._edges.setdefault(node, set())

    def add_edge(self, node: object, depends_on: object) -> None:
        self.add_node(node)
        self.add_node(depends_on)
        self._edges[node].add(depends_on)

    def nodes(self) -> List[object]:
        return list(self._edges.keys())

    def _visit(self, node: object, temp: Set[object], perm: Set[object], result: List[object]) -> None:
        if node in perm:
            return
        if node in temp:
            raise ValueError("Cycle detected in dependency graph")
        temp.add(node)
        for dep in self._edges.get(node, []):
            self._visit(dep, temp, perm, result)
        temp.remove(node)
        perm.add(node)
        result.append(node)

    def topological_sort(self) -> List[object]:
        """Return nodes in an order that satisfies dependencies (dep before node).

        Raises ValueError on cycles.
        """
        temp: Set[object] = set()
        perm: Set[object] = set()
        result: List[object] = []
        for n in list(self._edges.keys()):
            if n not in perm:
                self._visit(n, temp, perm, result)
        return result
