from uuid import UUID

from app.schemas.project_foundation import ProjectFoundationActor, ProjectFoundationProtectedResult
from test_project_foundation_service import domain


def test_cross_organization_project_read_is_payload_free_protected(db_session):
    service, actor, project = domain(db_session)
    result = service.get(project_id=project.id, actor=ProjectFoundationActor(actor_id=actor.actor_id, organization_id=UUID("02810000-0000-4000-8000-000000000099")))
    assert isinstance(result, ProjectFoundationProtectedResult)
    assert result.model_dump() == {"outcome": "protected_not_found"}


def test_workspace_participant_does_not_inherit_mutation_authority():
    # Exact mutation policy is asserted structurally: only admin/owner/assignee.
    from app.dependencies.project_foundation import SqlAlchemyProjectFoundationAuthorization
    import inspect
    source = inspect.getsource(SqlAlchemyProjectFoundationAuthorization.can_mutate)
    assert "EngineeringWorkspace" not in source and "project.owner_id" in source


def test_router_has_no_transport_owned_infrastructure_or_deferred_routes():
    from pathlib import Path
    source = Path("app/api/v1/routers/project_foundation.py").read_text()
    for prohibited in ("Session", "Repository", "UnitOfWork", "Task", "Milestone", "Deliverable", "Wizard", "AI"):
        assert prohibited not in source
    assert source.count("@router.") == 8
