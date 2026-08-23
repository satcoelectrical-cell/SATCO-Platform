from uuid import UUID

from app.enums.project_foundation import ProjectInputSourceKind
from app.exceptions.evidence import EvidenceProtectedNotFound
from app.exceptions.project_foundation import ProjectFoundationProtectedNotFound, ProjectFoundationUnavailable
from app.exceptions.supporting_file import SupportingFileProtectedNotFound
from app.models.evidence_command import EvidenceActor
from app.models.supporting_file_command import SupportingFileScope
from app.schemas.evidence import EvidenceFilter
from app.schemas.project_foundation import ProjectFoundationActor, ProjectInputSafeSource, ProjectInputSourceCandidate


class CanonicalProjectInputSourceAdapter:
    """Calls only canonical application services; owns no foreign persistence."""

    def __init__(self, *, evidence_service, supporting_file_service):
        self.evidence_service = evidence_service
        self.supporting_file_service = supporting_file_service

    def authorize_exact(self, *, actor: ProjectFoundationActor, project_id: int, kind: ProjectInputSourceKind, source_id: UUID, workspace_id: int | None):
        try:
            if kind is ProjectInputSourceKind.EVIDENCE:
                item = self.evidence_service.get(source_id, EvidenceActor(actor.actor_id, actor.organization_id))
                if item.project_id != project_id or item.workspace_id != workspace_id or item.lifecycle.value != "current":
                    raise ProjectFoundationProtectedNotFound()
                return ProjectInputSafeSource(kind=kind, source_id=item.id, version=item.version, workspace_id=item.workspace_id)
            scope = SupportingFileScope(actor.organization_id, project_id, workspace_id)
            item = self.supporting_file_service.get_metadata(actor_id=actor.actor_id, scope=scope, asset_id=source_id)
            if item.project_id != project_id or item.workspace_id != workspace_id or item.lifecycle != "available":
                raise ProjectFoundationProtectedNotFound()
            return ProjectInputSafeSource(kind=kind, source_id=item.id, version=item.version, workspace_id=item.workspace_id)
        except (EvidenceProtectedNotFound, SupportingFileProtectedNotFound, ProjectFoundationProtectedNotFound):
            raise ProjectFoundationProtectedNotFound() from None
        except Exception:
            raise ProjectFoundationUnavailable() from None

    def list_authorized(self, *, actor: ProjectFoundationActor, project_id: int, kind: ProjectInputSourceKind, workspace_id: int | None, limit: int):
        try:
            if kind is ProjectInputSourceKind.EVIDENCE:
                page = self.evidence_service.list(
                    project_id=project_id, filters=EvidenceFilter(workspace_id=workspace_id, lifecycle="current"),
                    page=1, size=limit, actor=EvidenceActor(actor.actor_id, actor.organization_id),
                )
                values = [ProjectInputSourceCandidate(
                    kind=kind, source_id=item.id, version=item.version, workspace_id=item.workspace_id,
                    display_label=f"{item.source_kind.value.replace('_', ' ')} · revision {item.source_revision}",
                ) for item in page.items if item.lifecycle.value == "current"]
            else:
                values_raw, _ = self.supporting_file_service.list_metadata(
                    actor_id=actor.actor_id, scope=SupportingFileScope(actor.organization_id, project_id, workspace_id),
                    lifecycle="available", limit=limit, continuation=None,
                )
                values = [ProjectInputSourceCandidate(
                    kind=kind, source_id=item.id, version=item.version, workspace_id=item.workspace_id,
                    display_label=item.safe_filename,
                ) for item in values_raw if item.lifecycle == "available"]
            return tuple(sorted(values, key=lambda item: (item.display_label.casefold(), str(item.source_id)))[:limit])
        except (EvidenceProtectedNotFound, SupportingFileProtectedNotFound):
            raise ProjectFoundationProtectedNotFound() from None
        except Exception:
            raise ProjectFoundationUnavailable() from None
