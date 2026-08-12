"""PATCH-033 Batch 2 application and canonical-adapter evidence."""

from datetime import datetime, timezone
from uuid import uuid4

from app.adapters.engineering_knowledge_graph import (
    CanonicalEngineeringObjectReadAdapter,
    TrustedGraphScopeAuthorizationAdapter,
)
from app.enums import EngineeringAuthorityStanding
from app.enums import EngineeringDiscipline
from app.enums import EngineeringLifecycle
from app.enums import EngineeringObjectFamily
from app.enums import EngineeringObjectType
from app.exceptions.engineering_object import (
    EngineeringObjectInternalServerError,
    EngineeringObjectProtectedNotFound,
)
from app.schemas.engineering_knowledge_graph import (
    CanonicalEngineeringObjectProtected,
    CanonicalEngineeringObjectResolved,
    CanonicalEngineeringObjectUnavailable,
    GraphActor,
    GraphNodeInvalidRequest,
    GraphNodeProtectedNotFound,
    GraphNodeRequest,
    GraphNodeSuccess,
    GraphNodeUnavailable,
    GraphScope,
    GraphScopeAuthorized,
    GraphScopeProtected,
)
from app.schemas.engineering_object import EngineeringObjectResponse
from app.services.engineering_knowledge_graph_service import (
    EngineeringKnowledgeGraphService,
)
from app.services.engineering_object_service import EngineeringObjectService


NOW = datetime(2026, 8, 12, tzinfo=timezone.utc)


def _response(*, organization_id=None, project_id=11, workspace_id=12):
    return EngineeringObjectResponse(
        id=uuid4(),
        organization_id=organization_id or uuid4(),
        customer_id=None,
        project_id=project_id,
        workspace_id=workspace_id,
        family=EngineeringObjectFamily.ELECTRICAL,
        discipline=EngineeringDiscipline.ELECTRICAL,
        object_type=EngineeringObjectType.MOTOR,
        subtype=None,
        lifecycle=EngineeringLifecycle.ACTIVE,
        authority_standing=EngineeringAuthorityStanding.APPROVED,
        version=3,
        creator_id=5,
        steward_id=6,
        created_at=NOW,
        updated_at=NOW,
    )


class _Scope:
    def __init__(self, decision=None):
        self.decision = decision or GraphScopeAuthorized()
        self.calls = 0

    def authorize(self, *, actor, scope):
        self.calls += 1
        return self.decision


class _Objects:
    def __init__(self, result):
        self.result = result
        self.calls = 0

    def get_authorized(self, *, actor, scope, node_id):
        self.calls += 1
        return self.result


class _CanonicalService:
    def __init__(self, outcome):
        self.outcome = outcome
        self.calls = []

    def get(self, object_id, actor, context):
        self.calls.append((object_id, actor, context))
        if isinstance(self.outcome, BaseException):
            raise self.outcome
        return self.outcome


def _context(response=None, *, scope_decision=None, canonical_result=None):
    response = response or _response()
    actor = GraphActor(actor_id=7, organization_id=response.organization_id)
    scope = GraphScope(organization_id=response.organization_id)
    request = GraphNodeRequest(node_id=response.id)
    scope_port = _Scope(scope_decision)
    object_port = _Objects(
        canonical_result or CanonicalEngineeringObjectResolved(response=response)
    )
    service = EngineeringKnowledgeGraphService(
        scope_authorization=scope_port,
        engineering_objects=object_port,
    )
    return service, actor, scope, request, scope_port, object_port


def test_get_node_returns_exact_one_node_projection_after_authorization():
    response = _response()
    service, actor, scope, request, scope_port, object_port = _context(response)

    result = service.get_node(actor=actor, scope=scope, request=request)

    assert isinstance(result, GraphNodeSuccess)
    assert result.node.node_type == "engineering_object"
    assert result.node.node_id == response.id
    assert result.node.model_dump(exclude={"node_type", "node_id"}) == (
        response.model_dump(exclude={"id"})
    )
    assert scope_port.calls == 1
    assert object_port.calls == 1


def test_invalid_request_returns_payload_free_result_without_any_call():
    service, actor, scope, _, scope_port, object_port = _context()

    result = service.get_node(actor=actor, scope=scope, request=object())

    assert isinstance(result, GraphNodeInvalidRequest)
    assert result.model_dump() == {"status": "invalid_request"}
    assert scope_port.calls == 0
    assert object_port.calls == 0


def test_scope_denial_returns_payload_free_result_and_zero_object_reads():
    service, actor, scope, request, scope_port, object_port = _context(
        scope_decision=GraphScopeProtected()
    )

    result = service.get_node(actor=actor, scope=scope, request=request)

    assert isinstance(result, GraphNodeProtectedNotFound)
    assert result.model_dump() == {"status": "protected_not_found"}
    assert scope_port.calls == 1
    assert object_port.calls == 0


def test_canonical_protected_and_unavailable_results_remain_payload_free():
    for canonical, expected, status in (
        (
            CanonicalEngineeringObjectProtected(),
            GraphNodeProtectedNotFound,
            "protected_not_found",
        ),
        (
            CanonicalEngineeringObjectUnavailable(),
            GraphNodeUnavailable,
            "unavailable",
        ),
    ):
        service, actor, scope, request, _, object_port = _context(
            canonical_result=canonical
        )
        result = service.get_node(actor=actor, scope=scope, request=request)
        assert isinstance(result, expected)
        assert result.model_dump() == {"status": status}
        assert object_port.calls == 1


def test_trusted_scope_adapter_accepts_only_matching_positive_context():
    organization_id = uuid4()
    adapter = TrustedGraphScopeAuthorizationAdapter()
    actor = GraphActor(actor_id=1, organization_id=organization_id)

    assert isinstance(
        adapter.authorize(
            actor=actor,
            scope=GraphScope(organization_id=organization_id),
        ),
        GraphScopeAuthorized,
    )
    assert isinstance(
        adapter.authorize(
            actor=actor,
            scope=GraphScope(organization_id=uuid4()),
        ),
        GraphScopeProtected,
    )


def test_canonical_adapter_translates_actor_context_and_exact_scope():
    response = _response(project_id=21, workspace_id=22)
    canonical = _CanonicalService(response)
    adapter = CanonicalEngineeringObjectReadAdapter(canonical)
    actor = GraphActor(actor_id=9, organization_id=response.organization_id)
    scope = GraphScope(
        organization_id=response.organization_id,
        project_id=21,
        workspace_id=22,
    )

    result = adapter.get_authorized(actor=actor, scope=scope, node_id=response.id)

    assert isinstance(result, CanonicalEngineeringObjectResolved)
    assert result.response == response
    assert len(canonical.calls) == 1
    _, canonical_actor, context = canonical.calls[0]
    assert canonical_actor.actor_id == actor.actor_id
    assert canonical_actor.organization_id == actor.organization_id
    assert context.operation == "ReadEngineeringObject"
    assert context.scope == {"object_id": response.id}


def test_canonical_adapter_maps_scope_mismatch_and_canonical_failures():
    response = _response(project_id=21, workspace_id=22)
    actor = GraphActor(actor_id=9, organization_id=response.organization_id)
    mismatches = (
        GraphScope(organization_id=uuid4()),
        GraphScope(organization_id=response.organization_id, project_id=99),
        GraphScope(organization_id=response.organization_id, workspace_id=99),
    )
    for scope in mismatches:
        canonical = _CanonicalService(response)
        result = CanonicalEngineeringObjectReadAdapter(canonical).get_authorized(
            actor=actor,
            scope=scope,
            node_id=response.id,
        )
        assert isinstance(result, CanonicalEngineeringObjectProtected)
        assert result.model_dump() == {"status": "protected"}
        assert len(canonical.calls) == 1

    for failure, expected in (
        (EngineeringObjectProtectedNotFound(response.id), CanonicalEngineeringObjectProtected),
        (EngineeringObjectInternalServerError(), CanonicalEngineeringObjectUnavailable),
    ):
        canonical = _CanonicalService(failure)
        result = CanonicalEngineeringObjectReadAdapter(canonical).get_authorized(
            actor=actor,
            scope=GraphScope(organization_id=response.organization_id),
            node_id=response.id,
        )
        assert isinstance(result, expected)
        assert len(canonical.calls) == 1


def test_real_canonical_uow_failure_maps_to_payload_free_unavailable():
    """Exercise the actual canonical service path, not a synthetic exception."""

    class _FailingUowFactory:
        def __call__(self):
            raise RuntimeError("database host and protected diagnostics")

    class _UnusedAuthorization:
        def authorize(self, **kwargs):
            raise AssertionError("authorization is unreachable")

    class _UnusedReferences:
        pass

    class _UnusedClock:
        def now(self):
            raise AssertionError("clock is unreachable")

    organization_id = uuid4()
    actor = GraphActor(actor_id=9, organization_id=organization_id)
    scope = GraphScope(organization_id=organization_id)
    canonical_service = EngineeringObjectService(
        uow_factory=_FailingUowFactory(),
        authorization=_UnusedAuthorization(),
        references=_UnusedReferences(),
        clock=_UnusedClock(),
    )
    adapter = CanonicalEngineeringObjectReadAdapter(canonical_service)

    result = adapter.get_authorized(
        actor=actor,
        scope=scope,
        node_id=uuid4(),
    )

    assert isinstance(result, CanonicalEngineeringObjectUnavailable)
    assert result.model_dump() == {"status": "unavailable"}
