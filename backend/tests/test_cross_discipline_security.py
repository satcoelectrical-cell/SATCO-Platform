from types import SimpleNamespace
from uuid import uuid4
import pytest
from fastapi import HTTPException

from app.adapters.cross_discipline_sources import (
    AuthorizedScope, SqlAlchemyCrossDisciplineAuthorizer,
    validate_batch_four_selectors, validate_batch_three_selectors, validate_batch_two_selectors,
)
from app.api.v1.routers.cross_discipline_intelligence import (
    _assessment_guard, _protected,
)
from app.dependencies.cross_discipline_intelligence import (
    decode_cross_discipline_cursor, encode_cross_discipline_cursor,
)
from app.ports.cross_discipline_intelligence import ProtectedResourceError
from app.services.cross_discipline_service import CrossDisciplineService


class DeniedDatabase:
    def __init__(self):
        self.calls = 0

    def scalar(self, _statement):
        self.calls += 1
        return None


class ForbiddenRepository:
    def __init__(self):
        self.calls = 0

    def get_assessment(self, *_args, **_kwargs):
        self.calls += 1
        raise AssertionError("protected assessment lookup occurred before Project guard")


def test_project_authorization_precedes_assessment_lookup_and_collapses_output():
    database = DeniedDatabase()
    repository = ForbiddenRepository()
    application = SimpleNamespace(
        db=database, repository=repository,
        context=SimpleNamespace(
            organization_id=uuid4(),
            user=SimpleNamespace(id=3, role="engineer"),
        ),
    )
    assert _assessment_guard(application, 99, uuid4()) is None
    assert database.calls == 1
    assert repository.calls == 0
    response = _protected()
    assert response.status_code == 404
    assert response.body == b'{"outcome":"protected_not_found"}'
    assert all(token not in response.body for token in (b"id", b"count", b"cursor", b"evidence", b"source"))


def test_same_idempotency_uuid_is_scoped_by_tenant_project_actor_and_operation():
    key = uuid4()
    scopes = {
        (str(uuid4()), 1, 1, "create", key),
        (str(uuid4()), 1, 1, "create", key),
    }
    assert len(scopes) == 2
    assert CrossDisciplineService.safe_protected_result() == {"outcome": "protected_not_found"}


def test_real_source_owner_intersection_aborts_before_projection_lookup(db_session, relationship_domain):
    project = relationship_domain["project"]
    actor = relationship_domain["actors"]["project_owner"]
    workspaces = tuple(sorted((
        relationship_domain["provider_workspace"].id,
        relationship_domain["consumer_workspace"].id,
    )))
    authorizer = SqlAlchemyCrossDisciplineAuthorizer(db_session)
    with pytest.raises(ProtectedResourceError):
        authorizer.authorize_scope(
            actor_id=actor.id, role="engineer",
            organization_id=project.organization_id, project_id=project.id,
            workspace_ids=workspaces, mutate=False,
        )
    assert authorizer.source_lookup_calls == 0


def test_batch_two_selector_is_closed_and_checked_before_any_source_resolution():
    scope = AuthorizedScope(
        actor_id=7, organization_id=uuid4(), project_id=3, workspace_ids=(1, 2),
        mutate=False, authorization_scope_digest="a" * 64,
    )
    electrical = "00000000-0000-4000-8000-000000000001"
    instrumentation = "00000000-0000-4000-8000-000000000002"
    selected = validate_batch_two_selectors(authorized=scope, selectors=(
        f"xdi.sel.v1/electrical/engineering_object/{electrical}/power_endpoint",
        f"xdi.sel.v1/instrumentation/engineering_object/{instrumentation}/power_consumer",
    ))
    assert selected[0][0] == "electrical"
    with pytest.raises(ValueError, match="invalid_request"):
        validate_batch_two_selectors(authorized=scope, selectors=(
            f"xdi.sel.v1/electrical/engineering_object/{electrical}/power_*",
        ))


def test_batch_three_selector_requires_full_i_c_scope_before_any_source_resolution():
    scope = AuthorizedScope(
        actor_id=7, organization_id=uuid4(), project_id=3, workspace_ids=(1, 2),
        mutate=False, authorization_scope_digest="a" * 64,
    )
    instrumentation = "00000000-0000-4000-8000-000000000051"
    control = "00000000-0000-4000-8000-000000000052"
    selected = validate_batch_three_selectors(authorized=scope, selectors=(
        f"xdi.sel.v1/control_automation/engineering_object/{control}/io_channel",
        f"xdi.sel.v1/instrumentation/engineering_object/{instrumentation}/signal_endpoint",
    ))
    assert {item[0] for item in selected} == {"instrumentation", "control_automation"}
    with pytest.raises(ValueError, match="invalid_request"):
        validate_batch_three_selectors(authorized=scope, selectors=(
            f"xdi.sel.v1/control_automation/engineering_object/{control}/hidden_topology",
        ))


def test_batch_four_selector_is_closed_before_electrical_or_control_source_lookup():
    scope = AuthorizedScope(actor_id=7, organization_id=uuid4(), project_id=3, workspace_ids=(1, 2), mutate=False, authorization_scope_digest="a" * 64)
    electrical = "00000000-0000-4000-8000-000000000081"
    control = "00000000-0000-4000-8000-000000000082"
    selected = validate_batch_four_selectors(authorized=scope, selectors=(
        f"xdi.sel.v1/control_automation/engineering_object/{control}/mcc",
        f"xdi.sel.v1/electrical/engineering_object/{electrical}/power_endpoint",
    ))
    assert {item[0] for item in selected} == {"electrical", "control_automation"}
    with pytest.raises(ValueError, match="invalid_request"):
        validate_batch_four_selectors(authorized=scope, selectors=(f"xdi.sel.v1/electrical/engineering_object/{electrical}/power_*",))


def test_cursor_is_bound_to_exact_tenant_project_query_and_tamper_collapses():
    scope = {
        "kind": "assessments", "organization_id": str(uuid4()),
        "project_id": 7, "limit": 50,
    }
    cursor = encode_cross_discipline_cursor(
        scope=scope, position=["2026-09-10T00:00:00+00:00", str(uuid4())],
    )
    assert decode_cross_discipline_cursor(cursor, scope=scope)[0].startswith("2026-")
    with pytest.raises(HTTPException) as wrong_scope:
        decode_cross_discipline_cursor(cursor, scope={**scope, "project_id": 8})
    assert wrong_scope.value.status_code == 422
    with pytest.raises(HTTPException):
        decode_cross_discipline_cursor(cursor[:-1] + ("A" if cursor[-1] != "A" else "B"), scope=scope)
