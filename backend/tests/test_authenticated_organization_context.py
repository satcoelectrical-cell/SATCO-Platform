"""Focused trusted Organization-context prerequisite tests."""

from types import SimpleNamespace
from unittest.mock import MagicMock
from uuid import uuid4

import pytest

from app.dependencies.auth import get_current_user_organization_context
from app.exceptions.organization_context import ActiveOrganizationContextRequired
from app.models.organization import UserOrganizationMembership


def _database_with(rows):
    database = MagicMock()
    query = database.query.return_value
    query.join.return_value.filter.return_value.limit.return_value.all.return_value = (
        rows
    )
    return database


def test_valid_active_organization_context_is_server_derived() -> None:
    organization_id = uuid4()
    user = SimpleNamespace(id=7)
    context = get_current_user_organization_context(
        current_user=user,
        db=_database_with([
            SimpleNamespace(organization_id=organization_id)
        ]),
    )

    assert context.user is user
    assert context.organization_id == organization_id


@pytest.mark.parametrize(
    "case",
    ["missing", "disabled", "inactive", "inaccessible", "cross_org"],
)
def test_invalid_or_inaccessible_context_is_rejected(case: str) -> None:
    with pytest.raises(ActiveOrganizationContextRequired) as error:
        get_current_user_organization_context(
            current_user=SimpleNamespace(id=7),
            db=_database_with([]),
        )

    assert error.value.code == "ACTIVE_ORGANIZATION_CONTEXT_REQUIRED"
    assert error.value.status_code == 403


def test_ambiguous_context_is_rejected() -> None:
    with pytest.raises(ActiveOrganizationContextRequired):
        get_current_user_organization_context(
            current_user=SimpleNamespace(id=7),
            db=_database_with([
                SimpleNamespace(organization_id=uuid4()),
                SimpleNamespace(organization_id=uuid4()),
            ]),
        )


def test_client_cannot_supply_trusted_organization_scope() -> None:
    with pytest.raises(TypeError):
        get_current_user_organization_context(
            current_user=SimpleNamespace(id=7),
            db=_database_with([]),
            organization_id=uuid4(),
        )


def test_membership_model_enforces_selected_membership_rules() -> None:
    table = UserOrganizationMembership.__table__
    check_names = {
        constraint.name for constraint in table.constraints
        if constraint.__class__.__name__ == "CheckConstraint"
    }
    assert "ck_user_org_memberships_selected_enabled" in check_names
    assert {
        index.name for index in table.indexes
    } == {"uq_user_org_memberships_selected_user"}
