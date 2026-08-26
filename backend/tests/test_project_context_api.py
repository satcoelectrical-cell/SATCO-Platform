def test_project_context_route_is_registered():
 from app.main import app
 from app.api.v1.routers.project_context import router
 assert any(route.path=="/projects/{project_id}/context" for route in router.routes)
 assert any(getattr(route, "original_router", None) is router for route in app.routes)


def test_graph_routes_are_exactly_registered_without_generic_graph_surface():
 from app.api.v1.routers.project_context import router
 paths={route.path for route in router.routes}
 assert "/projects/{project_id}/engineering-context/nodes/{node_kind}/{selector}" in paths
 assert "/projects/{project_id}/engineering-context/nodes/{node_kind}/{selector}/related" in paths
 assert not any("depth" in path or "traverse" in path or "graph" in path for path in paths)


def test_context_route_exposes_only_section_bound_continuation_controls():
 import inspect
 from app.api.v1.routers.project_context import assemble_project_context
 parameters=inspect.signature(assemble_project_context).parameters
 assert {"section","page_size","continuation"} <= set(parameters)
 assert "total" not in parameters and "offset" not in parameters
