from uuid import uuid4
from domain.graph import CycleCanceller, CycleFinder, DebtGraph, Edge

def make_graph(edges):
    return DebtGraph([Edge(a, b, w) for a, b, w in edges])

def test_no_cycles():
    a, b, c = uuid4(), uuid4(), uuid4()
    g = make_graph([(a, b, 100), (b, c, 100)])
    assert CycleFinder.find_all_cycles(g) == []

def test_simple_triangle_cycle():
    a, b, c = uuid4(), uuid4(), uuid4()
    g = make_graph([(a, b, 100), (b, c, 100), (c, a, 100)])
    cycles = CycleFinder.find_all_cycles(g)
    assert len(cycles) == 1

def test_cancel_full_cycle():
    a, b, c = uuid4(), uuid4(), uuid4()
    g = make_graph([(a, b, 100), (b, c, 100), (c, a, 100)])
    remaining, cancellations = CycleCanceller.cancel_all(g)
    assert len(remaining) == 0
    assert len(cancellations) == 1
    assert cancellations[0].amount == 100