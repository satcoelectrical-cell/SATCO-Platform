from unittest.mock import Mock

from app.repositories.project_foundation_repository import ProjectFoundationRepository
from app.repositories.project_foundation_unit_of_work import SqlAlchemyProjectFoundationUnitOfWork


def test_repository_and_uow_preserve_no_commit_boundary():
    session = Mock()
    repository = ProjectFoundationRepository(session)
    repository.add(object())
    session.add.assert_called_once()
    session.commit.assert_not_called()
    repository.flush()
    session.flush.assert_called_once()
    session.commit.assert_not_called()

    uow = SqlAlchemyProjectFoundationUnitOfWork(session)
    uow.commit()
    session.commit.assert_called_once()
    uow.rollback()
    session.rollback.assert_called_once()


def test_audit_staging_is_bounded_to_shared_audit_model_without_commit():
    session = Mock()
    uow = SqlAlchemyProjectFoundationUnitOfWork(session)
    uow.stage_audit(actor_id=4, project_id=7, operation="UPDATE", details={"operation": "put_basis", "version": 2})
    audit = session.add.call_args.args[0]
    assert audit.entity == "PROJECT_FOUNDATION" and audit.entity_id == 7
    assert audit.details == {"operation": "put_basis", "version": 2}
    session.commit.assert_not_called()
