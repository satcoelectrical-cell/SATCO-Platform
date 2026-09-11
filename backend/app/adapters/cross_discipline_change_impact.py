"""Public Project Control boundary for the second Batch-5 handoff phase."""

from __future__ import annotations

from app.enums.project_control import ImpactTargetKind
from app.schemas.project_control import ImpactCommand


class ProjectControlChangeImpactAdapter:
    """Calls the owner service only; it never shares the caller's XDI UoW."""

    def __init__(self, *, service=None, actor=None, application_factory=None):
        self.service = service
        self.actor = actor
        self.application_factory = application_factory

    def create_potential(
        self, *, project_id, workspace_id, change_id, change_version, target_kind,
        target_id, rationale, idempotency_key,
    ):
        try:
            kind = ImpactTargetKind(target_kind)
        except ValueError:
            return {"outcome": "invalid_request"}
        cleanup = None
        service, actor = self.service, self.actor
        if self.application_factory is not None:
            application, cleanup = self.application_factory()
            service, actor = application.service, application.actor
        if service is None or actor is None:
            return {"outcome": "unavailable"}
        try:
            result = service.create_change_impact(
                project_id=project_id,
                actor=actor,
                idempotency_key=idempotency_key,
                data=ImpactCommand(
                    workspace_id=workspace_id, rationale=rationale,
                    expected_version=change_version, change_id=change_id,
                    target_kind=kind, target_id=target_id,
                    statement="Cross-discipline advisory potential impact",
                ),
            )
            return result.model_dump() if hasattr(result, "model_dump") else result
        finally:
            if cleanup is not None:
                cleanup()
