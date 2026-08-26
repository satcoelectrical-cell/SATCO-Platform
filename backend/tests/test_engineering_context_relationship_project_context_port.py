from datetime import datetime, timezone

from app.adapters.engineering_context_relationship_project_context import (
    EngineeringContextRelationshipProjectContextAdapter,
)
from app.exceptions.engineering_context_relationship import RelationshipForbidden
from app.schemas.project_context import (
    ContextNodeKind,
    ContextNodeSelector,
    GraphDirection,
    OwnerPage,
    OwnerProtected,
    OwnerUnavailable,
    ProjectContextActor,
    ProjectContextScope,
    SectionPageRequest,
)


class User:
    def __init__(self, user_id: int):
        self.id = user_id


def _record(project_id=7):
    return {
        "id": 21, "relationship_key": "rel-21", "project_id": project_id,
        "meaning": "requires", "lifecycle": "current", "version": 2,
        "purpose": "excluded", "steward_id": 90,
        "source_kind": "context", "source_context_id": 12,
        "source_project_id": None, "source_workspace_id": None,
        "target_kind": "workspace", "target_context_id": None,
        "target_project_id": None, "target_workspace_id": 9,
    }


class PublicRelationshipService:
    def __init__(self, result=None, error=None):
        self.result = result if result is not None else {"items": [_record()]}
        self.error = error
        self.calls = []

    def list_relationships(self, **kwargs):
        self.calls.append(kwargs)
        if self.error:
            raise self.error
        return self.result


def _actor():
    return ProjectContextActor(
        actor_id=3, organization_id="00000000-0000-0000-0000-000000000007"
    )


def _scope():
    return ProjectContextScope(project_id=7, workspace_id=9)


def test_relationship_adapter_uses_public_boundary_and_filters_incident_only():
    service = PublicRelationshipService()
    result = EngineeringContextRelationshipProjectContextAdapter(service).list_authorized_incident(
        actor=_actor(), scope=_scope(),
        selector=ContextNodeSelector(kind=ContextNodeKind.ENGINEERING_CONTEXT, value=12),
        direction=GraphDirection.OUTGOING, page=SectionPageRequest(page_size=100),
        current_user=User(3),
    )
    assert isinstance(result, OwnerPage)
    assert len(result.items) == 1
    assert result.items[0].meaning.value == "context_requires"
    assert service.calls[0]["size"] == 50
    dumped = result.items[0].model_dump()
    assert "purpose" not in dumped
    assert "steward_id" not in dumped


def test_relationship_adapter_preserves_protected_and_unavailable_results():
    protected = EngineeringContextRelationshipProjectContextAdapter(
        PublicRelationshipService(error=RelationshipForbidden())
    ).list_authorized_incident(
        actor=_actor(), scope=_scope(),
        selector=ContextNodeSelector(kind=ContextNodeKind.PROJECT, value=7),
        direction=GraphDirection.BOTH, page=SectionPageRequest(), current_user=User(3),
    )
    assert isinstance(protected, OwnerProtected)
    protected_scope = EngineeringContextRelationshipProjectContextAdapter(
        PublicRelationshipService(result={"items": [_record(project_id=8)]})
    ).list_authorized_incident(
        actor=_actor(), scope=_scope(),
        selector=ContextNodeSelector(kind=ContextNodeKind.PROJECT, value=7),
        direction=GraphDirection.BOTH, page=SectionPageRequest(), current_user=User(3),
    )
    assert isinstance(protected_scope, OwnerProtected)


def test_relationship_adapter_has_no_foreign_persistence_dependencies():
    source = open(
        "app/adapters/engineering_context_relationship_project_context.py",
        encoding="utf-8",
    ).read()
    for forbidden in ("sqlalchemy", "repository", "Session", "UnitOfWork"):
        assert forbidden not in source
