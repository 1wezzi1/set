from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class Edge:
    debtor_id: UUID
    creditor_id: UUID
    weight: int


class DebtGraph:
    """Направленный граф долгов. Рёбра агрегируются."""

    def __init__(self, edges: list[Edge]) -> None:
        self._adj: dict[UUID, dict[UUID, int]] = defaultdict(dict)
        self._nodes: set[UUID] = set()
        for e in edges:
            if e.weight <= 0:
                continue
            self._nodes.add(e.debtor_id)
            self._nodes.add(e.creditor_id)
            self._adj[e.debtor_id][e.creditor_id] = (
                self._adj[e.debtor_id].get(e.creditor_id, 0) + e.weight
            )

    @property
    def nodes(self) -> set[UUID]:
        return set(self._nodes)

    def successors(self, u: UUID) -> list[UUID]:
        return list(self._adj.get(u, {}).keys())

    def weight(self, u: UUID, v: UUID) -> int:
        return self._adj.get(u, {}).get(v, 0)

    def edges(self) -> list[Edge]:
        return [
            Edge(u, v, w)
            for u, nbrs in self._adj.items()
            for v, w in nbrs.items()
            if w > 0
        ]


class CycleFinder:
    """Алгоритм Джонсона — все простые циклы."""

    @staticmethod
    def find_all_cycles(graph: DebtGraph) -> list[list[UUID]]:
        nodes = sorted(graph.nodes, key=str)
        index = {u: i for i, u in enumerate(nodes)}
        n = len(nodes)
        if n == 0:
            return []

        adj: list[list[int]] = [[] for _ in range(n)]
        for u in nodes:
            for v in graph.successors(u):
                adj[index[u]].append(index[v])

        cycles: list[list[UUID]] = []

        for s in range(n):
            blocked = [False] * n
            blocked_map: list[set[int]] = [set() for _ in range(n)]
            stack: list[int] = []

            def unblock(u: int) -> None:
                blocked[u] = False
                for w in list(blocked_map[u]):
                    blocked_map[u].discard(w)
                    if blocked[w]:
                        unblock(w)

            def circuit(v: int, start: int) -> bool:
                found = False
                stack.append(v)
                blocked[v] = True
                for w in adj[v]:
                    if w < start:
                        continue
                    if w == start:
                        cycles.append([nodes[i] for i in stack])
                        found = True
                    elif not blocked[w]:
                        if circuit(w, start):
                            found = True
                if found:
                    unblock(v)
                else:
                    for w in adj[v]:
                        if w >= start:
                            blocked_map[w].add(v)
                stack.pop()
                return found

            circuit(s, s)

        return cycles


class CycleCanceller:
    """Находит все циклы и «вычёркивает» их (min по циклу)."""

    @dataclass(frozen=True)
    class Cancellation:
        cycle: tuple[UUID, ...]
        amount: int

    @staticmethod
    def cancel_all(
        graph: DebtGraph,
    ) -> tuple[list[Edge], list["CycleCanceller.Cancellation"]]:
        raw = [(e.debtor_id, e.creditor_id) for e in graph.edges()]
        assert len(raw) == len(set(raw)), "graph.edges() must be aggregated"

        weights: dict[tuple[UUID, UUID], int] = {
            (e.debtor_id, e.creditor_id): e.weight for e in graph.edges()
        }

        def build_graph() -> DebtGraph:
            return DebtGraph(
                [Edge(u, v, w) for (u, v), w in weights.items() if w > 0]
            )

        cancellations: list[CycleCanceller.Cancellation] = []

        while True:
            current = build_graph()
            cycles = CycleFinder.find_all_cycles(current)
            if not cycles:
                break

            progress = False
            for cyc in cycles:
                cycle_edges: list[tuple[UUID, UUID]] = []
                valid = True
                for i in range(len(cyc)):
                    u = cyc[i]
                    v = cyc[(i + 1) % len(cyc)]
                    if weights.get((u, v), 0) <= 0:
                        valid = False
                        break
                    cycle_edges.append((u, v))
                if not valid:
                    continue
                delta = min(weights[e] for e in cycle_edges)
                if delta <= 0:
                    continue
                for e in cycle_edges:
                    weights[e] -= delta
                cancellations.append(
                    CycleCanceller.Cancellation(cycle=tuple(cyc), amount=delta)
                )
                progress = True

            if not progress:
                break

        remaining = [Edge(u, v, w) for (u, v), w in weights.items() if w > 0]
        return remaining, cancellations