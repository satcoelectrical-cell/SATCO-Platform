from datetime import datetime, timezone
from types import SimpleNamespace
from uuid import UUID, uuid4

import pytest

from app.adapters.project_foundation import CanonicalProjectInputSourceAdapter
from app.enums import ProjectInputSourceKind
from app.exceptions.evidence import EvidenceProtectedNotFound
from app.exceptions.project_foundation import ProjectFoundationProtectedNotFound
from app.models.evidence_command import EvidenceActor
from app.schemas.project_foundation import ProjectFoundationActor


ORG = UUID("02810000-0000-4000-8000-000000000001")


class EvidenceApplication:
    def get(self, source_id, actor: EvidenceActor):
        return SimpleNamespace(id=source_id, organization_id=actor.organization_id, project_id=7, workspace_id=9, lifecycle=SimpleNamespace(value="current"), version=3)
    def list(self, **_): return SimpleNamespace(items=[])


class SupportingApplication:
    def get_metadata(self, *, asset_id, scope, **_):
        return SimpleNamespace(id=asset_id, organization_id=scope.organization_id, project_id=scope.project_id, workspace_id=scope.workspace_id, lifecycle="available", version=2)
    def list_metadata(self, **_): return ([], None)


def test_exact_canonical_application_responses_preserve_scope_and_version():
    adapter = CanonicalProjectInputSourceAdapter(evidence_service=EvidenceApplication(), supporting_file_service=SupportingApplication())
    actor = ProjectFoundationActor(actor_id=4, organization_id=ORG)
    evidence = adapter.authorize_exact(actor=actor, project_id=7, kind=ProjectInputSourceKind.EVIDENCE, source_id=uuid4(), workspace_id=9)
    asset = adapter.authorize_exact(actor=actor, project_id=7, kind=ProjectInputSourceKind.SUPPORTING_FILE, source_id=uuid4(), workspace_id=9)
    assert (evidence.version, evidence.workspace_id) == (3, 9)
    assert (asset.version, asset.workspace_id) == (2, 9)


def test_cross_project_or_protected_canonical_result_fails_closed():
    class Wrong(EvidenceApplication):
        def get(self, source_id, actor):
            value = super().get(source_id, actor); value.project_id = 8; return value
    adapter = CanonicalProjectInputSourceAdapter(evidence_service=Wrong(), supporting_file_service=SupportingApplication())
    with pytest.raises(ProjectFoundationProtectedNotFound):
        adapter.authorize_exact(actor=ProjectFoundationActor(actor_id=4, organization_id=ORG), project_id=7, kind=ProjectInputSourceKind.EVIDENCE, source_id=uuid4(), workspace_id=9)
