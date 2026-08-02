"""Focused repository tests for PATCH-023 Sprint-2."""

from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import MagicMock
from uuid import uuid4

from app.repositories.engineering_object_repository import (
    SqlAlchemyEngineeringObjectRepository,
)


def test_expected_version_persistence_never_commits() -> None:
    session = MagicMock()
    session.execute.return_value.rowcount = 1
    repository = SqlAlchemyEngineeringObjectRepository(session)
    aggregate = SimpleNamespace(
        id=uuid4(), organization_id=uuid4(), family="electrical",
        discipline="electrical", object_type="motor", subtype=None,
        lifecycle="active", authority_standing="draft", steward_id=7,
        version=2, updated_at=datetime.now(timezone.utc),
    )

    assert repository.persist_expected_version(aggregate, 1) is True
    session.execute.assert_called_once()
    session.flush.assert_called_once()
    session.commit.assert_not_called()


def test_repository_add_stages_without_commit() -> None:
    session = MagicMock()
    repository = SqlAlchemyEngineeringObjectRepository(session)
    aggregate = object()

    repository.add(aggregate)

    session.add.assert_called_once_with(aggregate)
    session.flush.assert_called_once()
    session.commit.assert_not_called()

