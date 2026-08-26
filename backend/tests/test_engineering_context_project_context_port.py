from datetime import datetime, timezone

from app.adapters.engineering_context_project_context import (
    EngineeringContextProjectContextAdapter,
)
from app.exceptions.engineering_context import ContextForbidden
from app.schemas.project_context import (
    ContextNodeKind,
    ContextNodeSelector,
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


def _item(project_id=7, workspace_id=9):
    now = datetime.now(timezone.utc)
    return {
        "id": 12, "context_key": "ctx-12", "project_id": project_id,
        "workspace_id": workspace_id, "kind": "qualified_fact",
        "authority": "authoritative_fact", "lifecycle": "current",
        "purpose": "Electrical basis", "version": 3,
        "payload": {"statement": "Supply is 400 V.", "uncertainty": None},
        "owner_id": 99, "steward_id": 98, "created_by_id": 97,
        "sources": [{"source_key": "private-key"}],
        "created_at": now, "updated_at": now,
    }


class PublicContextService:
    def __init__(self, result=None, error=None):
        self.result = result if result is not None else {"items": [_item()]}
        self.error = error
        self.calls = []

    def list_for_scope(self, **kwargs):
        self.calls.append(("list_for_scope", kwargs))
        if self.error:
            raise self.error
        return self.result

    def get(self, context_id, current_user):
        self.calls.append(("get", context_id, current_user.id))
        if self.error:
            raise self.error
        return _item()


def _actor():
    return ProjectContextActor(
        actor_id=3, organization_id="00000000-0000-0000-0000-000000000007"
    )


def _scope():
    return ProjectContextScope(project_id=7, workspace_id=9)


def test_context_adapter_uses_public_boundary_and_projects_typed_safe_fields():
    service = PublicContextService()
    adapter = EngineeringContextProjectContextAdapter(service)
    result = adapter.list_authorized_current(
        actor=_actor(), scope=_scope(), page=SectionPageRequest(page_size=10),
        current_user=User(3),
    )
    assert isinstance(result, OwnerPage)
    assert service.calls[0][0] == "list_for_scope"
    item = result.items[0]
    assert item.context_id == 12
    assert item.project_id == 7
    assert item.payload.payload_kind == "qualified_fact"
    dumped = item.model_dump()
    assert "owner_id" not in dumped
    assert "steward_id" not in dumped
    assert "created_by_id" not in dumped
    assert "sources" not in dumped


def test_context_adapter_preserves_protected_and_unavailable_without_disclosure():
    protected = EngineeringContextProjectContextAdapter(
        PublicContextService(error=ContextForbidden())
    ).list_authorized_current(
        actor=_actor(), scope=_scope(), page=SectionPageRequest(), current_user=User(3)
    )
    assert isinstance(protected, OwnerProtected)
    unavailable = EngineeringContextProjectContextAdapter(
        PublicContextService(result={"items": [{"id": "bad"}]})
    ).list_authorized_current(
        actor=_actor(), scope=_scope(), page=SectionPageRequest(), current_user=User(3)
    )
    assert isinstance(unavailable, OwnerUnavailable)


def test_context_adapter_rejects_mismatched_trusted_actor_before_owner_read():
    service = PublicContextService()
    result = EngineeringContextProjectContextAdapter(service).get_authorized_context(
        actor=_actor(), scope=_scope(),
        selector=ContextNodeSelector(kind=ContextNodeKind.ENGINEERING_CONTEXT, value=12),
        current_user=User(4),
    )
    assert isinstance(result, OwnerProtected)
    assert service.calls == []
