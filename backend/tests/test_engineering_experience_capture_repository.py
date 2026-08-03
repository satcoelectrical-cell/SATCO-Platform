from datetime import datetime, timezone
from uuid import uuid4

from app.models.engineering_experience_capture import EngineeringExperienceCapture
from app.repositories.engineering_experience_capture_repository import (
    SqlAlchemyEngineeringExperienceCaptureRepository,
)


def _capture(domain, *, creator_id, organization_id, content="captured experience"):
    workspace = domain["consumer_workspace"]
    return EngineeringExperienceCapture(
        id=uuid4(), organization_id=organization_id,
        project_id=domain["project"].id, workspace_id=workspace.id,
        discipline="electrical", engineering_object_id=None,
        source_kind="observation", original_content=content,
        creator_id=creator_id, lifecycle="captured", version=1,
        created_at=datetime.now(timezone.utc), updated_at=datetime.now(timezone.utc),
    )


def test_repository_scopes_load_and_lists_deterministically(db_session, relationship_domain):
    actor = relationship_domain["actors"]["project_owner"]
    capture = _capture(relationship_domain, creator_id=actor.id,
                       organization_id=relationship_domain["project"].organization_id)
    repository = SqlAlchemyEngineeringExperienceCaptureRepository(db_session)
    repository.add(capture)

    assert repository.get_scoped(capture.id, capture.organization_id) is capture
    assert repository.get_scoped(capture.id, uuid4()) is None
    items, total = repository.list_workspace_scoped(
        organization_id=capture.organization_id, project_id=capture.project_id,
        workspace_id=capture.workspace_id, filters={"source_kind": "observation"},
        page=1, size=100,
    )
    assert total == 1
    assert [item.id for item in items] == [capture.id]


def test_repository_expected_version_is_compare_and_change(db_session, relationship_domain):
    actor = relationship_domain["actors"]["project_owner"]
    capture = _capture(relationship_domain, creator_id=actor.id,
                       organization_id=relationship_domain["project"].organization_id)
    repository = SqlAlchemyEngineeringExperienceCaptureRepository(db_session)
    repository.add(capture)
    capture.lifecycle = "withdrawn"
    capture.version = 2
    assert repository.persist_expected_version(capture, 1) is True
    assert repository.persist_expected_version(capture, 1) is False


def test_repository_never_owns_commit():
    assert "commit" not in SqlAlchemyEngineeringExperienceCaptureRepository.__dict__
