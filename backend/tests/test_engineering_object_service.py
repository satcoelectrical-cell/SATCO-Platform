"""Focused service, policy, visibility, and compatibility tests."""

from unittest.mock import MagicMock
from uuid import uuid4

import pytest

from app.enums import EngineeringDiscipline
from app.exceptions.engineering_object import EngineeringObjectProtectedNotFound
from app.models.engineering_object_command import AuthenticatedActor
from app.models.engineering_object_command import AuthorizationContext
from app.repositories.engineering_object_unit_of_work import (
    SqlAlchemyReferenceValidator,
)
from app.services.engineering_object_service import EngineeringObjectService


class MissingRepository:
    def get_authorized(self, object_id, organization_id):
        return None


class FakeUow:
    def __enter__(self):
        self.engineering_objects = MissingRepository()
        return self

    def __exit__(self, *args):
        return None


def test_read_uses_protected_not_found_without_policy_disclosure() -> None:
    policy = MagicMock()
    service = EngineeringObjectService(
        uow_factory=FakeUow, authorization=policy,
        references=MagicMock(), clock=MagicMock(),
    )
    actor = AuthenticatedActor(1, uuid4())
    context = AuthorizationContext("read", {})

    with pytest.raises(EngineeringObjectProtectedNotFound):
        service.get(uuid4(), actor, context)
    policy.authorize.assert_not_called()


def test_approved_workspace_compatibility_matrix_is_closed() -> None:
    assert SqlAlchemyReferenceValidator.COMPATIBILITY == {
        EngineeringDiscipline.INSTRUMENTATION: "instrumentation",
        EngineeringDiscipline.ELECTRICAL: "electrical",
        EngineeringDiscipline.INDUSTRIAL_AUTOMATION: "control",
    }
    assert EngineeringDiscipline.SHARED_ENGINEERING not in (
        SqlAlchemyReferenceValidator.COMPATIBILITY
    )

