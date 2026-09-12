"""Deterministic PATCH-052 package advisory candidates; no I/O or authority."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID, uuid5

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.discipline_packages.descriptors.eic_v1 import DESCRIPTORS_V1, DESCRIPTOR_DIGESTS_V1
from app.models.discipline_package import (
    ProjectPackageConfigurationHead,
    ProjectPackageConfigurationSelection,
)
from app.models.engineering_workspace import EngineeringWorkspace
from app.standards.canonical import canonical_digest


_CANDIDATE_NAMESPACE = UUID("bdfe0c23-8262-59e2-8ff9-4c4b7a21cc6b")


class StandardsPackageCandidateAdapter:
    """Read frozen descriptors selected by the exact current Project revision."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def candidates(self, *, organization_id: UUID, project_id: int, package_version: str | None = None) -> list[dict]:
        head = self.session.get(ProjectPackageConfigurationHead, project_id)
        if head is None or head.organization_id != organization_id:
            return []
        workspaces = list(self.session.scalars(select(EngineeringWorkspace).where(
            EngineeringWorkspace.project_id == project_id,
            EngineeringWorkspace.bound_project_configuration_revision == head.current_revision,
        ).order_by(EngineeringWorkspace.id)))
        if not workspaces:
            return []
        selections = list(self.session.scalars(select(ProjectPackageConfigurationSelection).where(
            ProjectPackageConfigurationSelection.project_id == project_id,
            ProjectPackageConfigurationSelection.configuration_revision == head.current_revision,
        ).order_by(ProjectPackageConfigurationSelection.package_key)))
        descriptors = {(item.package_key, item.package_version): item for item in DESCRIPTORS_V1}
        emitted_at = datetime.now(timezone.utc).isoformat()
        output: list[dict] = []
        for selection in selections:
            if package_version is not None and selection.package_version != package_version:
                continue
            descriptor = descriptors.get((selection.package_key, selection.package_version))
            if descriptor is None or DESCRIPTOR_DIGESTS_V1.get(selection.package_key) != selection.descriptor_digest:
                continue
            for hook in descriptor.contributions.standards_hooks:
                for static in hook.candidates:
                    for workspace in workspaces:
                        semantic = {
                            "organization_id": str(organization_id), "project_id": project_id,
                            "workspace_id": workspace.id, "package_key": selection.package_key,
                            "package_version": selection.package_version,
                            "descriptor_digest": selection.descriptor_digest,
                            "configuration_revision": head.current_revision, "hook_id": hook.hook_id,
                            "designation_key": static.designation_key, "family_key": static.family_key,
                            "suggested_role": static.suggested_role, "rationale_code": static.rationale_code,
                        }
                        candidate_id = uuid5(_CANDIDATE_NAMESPACE, canonical_digest(semantic))
                        candidate_digest = canonical_digest({"candidate_id": candidate_id, **semantic})
                        output.append({
                            "candidate_id": str(candidate_id), "candidate_digest": candidate_digest,
                            **semantic, "standard_identity_id": None, "standard_edition_id": None,
                            "emitted_at": emitted_at,
                        })
                        if len(output) >= min(hook.max_results, 64):
                            return output
        return output
