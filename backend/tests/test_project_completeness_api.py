from uuid import UUID

from app.api.v1.routers.project_completeness import (
    assess_project_completeness,
    router,
)
from app.dependencies.project_completeness import ProjectCompletenessApplication
from app.ports.project_completeness import CompletenessActor
from app.schemas.project_completeness import CompletenessInvalidRequest, CompletenessProtectedNotFound


class Service:
    def __init__(self):
        self.calls = []

    def assess(self, **kwargs):
        self.calls.append(kwargs)
        return CompletenessProtectedNotFound()


class User:
    id = 1


def _application():
    service = Service()
    app = ProjectCompletenessApplication(
        service=service,
        actor=CompletenessActor(1, UUID("00000000-0000-0000-0000-000000000001")),
        current_user=User(),
    )
    return app, service


def test_exact_single_completeness_route_is_declared():
    paths = {route.path for route in router.routes}
    assert paths == {"/projects/{project_id}/completeness"}


def test_invalid_path_or_workspace_is_payload_free_invalid_request():
    application, service = _application()
    for project_id, workspace_id in (("0", None), ("x", None), ("1", "0"), ("1", "x")):
        result = assess_project_completeness(project_id, workspace_id, application)
        assert isinstance(result, CompletenessInvalidRequest)
        assert result.model_dump() == {"status": "invalid_request"}
    assert service.calls == []


def test_valid_route_invokes_service_once_without_client_organization():
    application, service = _application()
    result = assess_project_completeness("1", "2", application)
    assert result.model_dump() == {"status": "protected_not_found"}
    assert len(service.calls) == 1
    request = service.calls[0]["request"]
    assert request.project_id == 1 and request.workspace_id == 2
