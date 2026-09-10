from datetime import datetime, timezone
from decimal import Decimal
import pytest
from app.discipline_packages.cross_discipline.canonical import canonical_decimal, canonical_json, finding_fingerprint, normalize_quantity, recurrence_key
from app.discipline_packages.cross_discipline.comparison import HANDLERS, equal, present, stale_after
from app.discipline_packages.cross_discipline.contracts import FindingIdentityInputV1, RangeV1, SourceIdentityV1
from app.discipline_packages.cross_discipline.graph import BoundedGraph, Edge, GraphLimitExceeded, Node

def _identity():
    return FindingIdentityInputV1("e","s","missing","x","r","1.0.0","a"*64,"i","1.0.0","b"*64,"o","selector",(SourceIdentityV1("object","1","version","1","c"*64),))

def test_decimal_and_canonical_bytes_are_stable():
    assert canonical_decimal("1.2300") == "1.23"
    assert canonical_json({"b": 1, "a": "e\u0301"}) == canonical_json({"a": "é", "b": 1})

def test_quantity_and_comparison_contracts():
    assert normalize_quantity("electric_potential", "0.4", "kV").canonical_magnitude == Decimal("400")
    assert equal(1, 1).outcome == "satisfied"
    assert present("absent", True).outcome == "violated"
    assert stale_after(datetime(2020,1,1,tzinfo=timezone.utc), datetime(2020,1,2,tzinfo=timezone.utc), 1).outcome == "violated"
    assert set(HANDLERS) == {"equal","not_equal","range_contains","range_overlaps","within_absolute_tolerance","enum_map_equal","set_contains","set_equal","present","stale_after","disagrees","applicable_if"}

def test_finding_identity_is_stable_and_recurrence_is_separate():
    identity = _identity(); assert finding_fingerprint(identity) == finding_fingerprint(identity)
    assert recurrence_key(identity) != finding_fingerprint(identity)

def test_graph_is_bounded_and_cycle_safe():
    graph=BoundedGraph(); a=Node("a","1"); b=Node("b","2")
    graph.add_edge(Edge("rel",a,b)); graph.add_edge(Edge("rel",b,a)); assert graph.path_exists(a,b,("rel",))
    for i in range(2,256): graph.add_node(Node("n",str(i)))
    with pytest.raises(GraphLimitExceeded): graph.add_node(Node("n","overflow"))
