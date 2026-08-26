from datetime import datetime, timezone
from uuid import UUID

from app.ports.project_completeness import CompletenessActor, CompletenessAssessmentRequest
from app.schemas.project_completeness import CompletenessProtectedNotFound, CompletenessUnavailable
from app.schemas.project_context import ProjectContextProtectedNotFound
from app.services.project_completeness_service import ProjectCompletenessService


class User:
    id = 1


class ProtectedObserver:
    def observe(self, **kwargs):
        return ProjectContextProtectedNotFound()


class ExplodingObserver:
    def observe(self, **kwargs):
        raise RuntimeError("private owner failure")


def _actor():
    return CompletenessActor(1, UUID("00000000-0000-0000-0000-000000000001"))


def test_protected_upstream_result_is_payload_free_and_does_not_disclose_scope():
    result = ProjectCompletenessService(ProtectedObserver()).assess(
        actor=_actor(),
        request=CompletenessAssessmentRequest(project_id=1, workspace_id=2),
        current_user=User(),
    )
    assert isinstance(result, CompletenessProtectedNotFound)
    assert result.model_dump() == {"status": "protected_not_found"}


def test_owner_exception_is_payload_free_unavailable_without_foreign_details():
    result = ProjectCompletenessService(ExplodingObserver()).assess(
        actor=_actor(),
        request=CompletenessAssessmentRequest(project_id=1),
        current_user=User(),
    )
    assert isinstance(result, CompletenessUnavailable)
    assert result.model_dump() == {"status": "unavailable"}


def test_trusted_request_contract_rejects_client_scope_shaping():
    for kwargs in (
        {"project_id": 0},
        {"project_id": 1, "workspace_id": 0},
        {"project_id": True},
    ):
        try:
            CompletenessAssessmentRequest(**kwargs)
        except ValueError:
            pass
        else:
            raise AssertionError("invalid trusted request was accepted")
