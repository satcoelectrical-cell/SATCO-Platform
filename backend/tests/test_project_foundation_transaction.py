from unittest.mock import Mock

import pytest

from app.repositories.project_foundation_unit_of_work import SqlAlchemyProjectFoundationUnitOfWork


def test_primary_failure_rolls_back_and_audit_cannot_commit_independently():
    session = Mock()
    uow = SqlAlchemyProjectFoundationUnitOfWork(session)
    with pytest.raises(RuntimeError):
        with uow:
            uow.stage_audit(actor_id=1, project_id=7, operation="UPDATE", details={"operation": "transition_stage"})
            raise RuntimeError("injected")
    session.rollback.assert_called_once()
    session.commit.assert_not_called()
