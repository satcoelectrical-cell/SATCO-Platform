from sqlalchemy import event

from app.core.database import engine
from app.repositories.engineering_experience_capture_repository import (
    SqlAlchemyEngineeringExperienceCaptureRepository,
)


def test_bounded_capture_list_uses_count_and_page_queries(db_session, relationship_domain):
    statements = []

    def record(_connection, _cursor, statement, _parameters, _context, _many):
        if "engineering_experience_captures" in statement:
            statements.append(statement)

    event.listen(engine, "before_cursor_execute", record)
    try:
        project = relationship_domain["project"]
        SqlAlchemyEngineeringExperienceCaptureRepository(db_session).list_project_scoped(
            organization_id=project.organization_id, project_id=project.id,
            filters={}, page=1, size=100,
        )
    finally:
        event.remove(engine, "before_cursor_execute", record)
    assert len(statements) <= 2


def test_predecessor_traversal_is_hard_bounded(db_session):
    repository = SqlAlchemyEngineeringExperienceCaptureRepository(db_session)
    assert repository.predecessor_chain(__import__("uuid").uuid4(), maximum_depth=20) == ()
