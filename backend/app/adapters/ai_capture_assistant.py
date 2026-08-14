"""Canonical Capture application adapter for PATCH-035."""

from app.enums.engineering_experience_capture import EngineeringExperienceCaptureLifecycle
from app.exceptions.ai_capture_assistant import AICaptureDependencyUnavailable, AICaptureSourceProtected
from app.exceptions.engineering_experience_capture import EngineeringExperienceCaptureProtectedNotFound
from app.models.engineering_experience_capture_command import EngineeringExperienceCaptureActor
from app.ports.ai_capture_assistant import AuthorizedCaptureContext, CopilotActor


class CanonicalCaptureAdviceSource:
    def __init__(self, capture_service) -> None:
        self._captures = capture_service

    def read_authorized(self, actor: CopilotActor, capture_id):
        try:
            value = self._captures.get(
                capture_id,
                EngineeringExperienceCaptureActor(actor.actor_id, actor.organization_id),
            )
        except EngineeringExperienceCaptureProtectedNotFound as exc:
            raise AICaptureSourceProtected() from exc
        except Exception as exc:
            raise AICaptureDependencyUnavailable() from exc
        if value.lifecycle is not EngineeringExperienceCaptureLifecycle.CAPTURED:
            raise AICaptureSourceProtected()
        return AuthorizedCaptureContext(
            capture_id=value.id, organization_id=value.organization_id,
            project_id=value.project_id, workspace_id=value.workspace_id,
            discipline=value.discipline, engineering_object_id=value.engineering_object_id,
            source_kind=value.source_kind, original_content=value.original_content,
            source_reference=value.source_reference, creator_id=value.creator_id,
            lifecycle="captured", version=value.version, updated_at=value.updated_at,
        )
