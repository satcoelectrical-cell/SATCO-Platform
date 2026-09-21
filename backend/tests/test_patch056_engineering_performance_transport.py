import inspect
from app.api.v1.routers import engineering_performance as transport

def test_p056_own_01_transport_is_read_only():
    methods={m for route in transport.router.routes for m in route.methods}
    assert methods=={"GET"}

def test_p056_own_02_transport_never_accepts_organization_from_request():
    source=inspect.getsource(transport)
    assert "organization_id: " not in source
    assert "get_current_user_organization_context" in source

def test_p056_transport_route_family_and_required_operations():
    paths={route.path for route in transport.router.routes}
    base="/api/v1/projects/{project_id}/engineering-performance"
    assert paths=={base+"/catalog",base+"/indicators",base+"/health",base+"/next-actions",base+"/trends",base+"/drill-down"}

def test_p056_transport_explicit_non_authority_markers():
    source=inspect.getsource(transport)
    assert source.count('"authoritative":False')>=6
    assert source.count('"advisory":True')>=6

def test_p056_transport_bounds_window_and_drilldown():
    source=inspect.getsource(transport)
    assert "{7,30,90,180}" in source
    assert "le=100" in source and "Query(20" in source

def test_p056_transport_persists_and_reads_real_trends():
    source=inspect.getsource(transport)
    assert "no_persisted_trend_points" not in source
    assert ".persist_observations(" in source
    assert ".reconcile_actions(" in source
    assert ".trends(" in source
    assert "historical_handles" in source
