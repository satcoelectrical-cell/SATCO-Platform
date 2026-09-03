from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4

from sqlalchemy import select, text
import pytest

from app.models.audit_log import AuditLog
from app.models.discipline_package import PackageConfigurationAuditEvent
from app.models.engineering_workspace import EngineeringWorkspace


def test_known_time_query_shapes_render_explicit_nulls_last():
    from app.api.v1.routers.discipline_packages import _known_time_audit_ordering

    organization_id = UUID("02810000-0000-4000-8000-000000000001")
    organization_query = select(PackageConfigurationAuditEvent.event_id).where(
        PackageConfigurationAuditEvent.organization_id == organization_id,
        PackageConfigurationAuditEvent.occurred_at.is_not(None),
    ).order_by(*_known_time_audit_ordering())
    project_query = organization_query.where(
        PackageConfigurationAuditEvent.project_id == 1
    )
    for query in (organization_query, project_query):
        rendered = str(query.compile(compile_kwargs={"literal_binds": True}))
        assert "ORDER BY package_configuration_audit_events.occurred_at DESC NULLS LAST" in rendered
        assert "package_configuration_audit_events.event_id DESC" in rendered


def test_guarded_workspace_creation_stages_generic_and_package_audit(db_session, engineer_user):
    from test_discipline_package_service import _factory, _project, _seed_configurable_registry
    from app.schemas.engineering_workspace import EngineeringWorkspaceCreate
    from app.services.engineering_workspace_service import EngineeringWorkspaceService

    _seed_configurable_registry(db_session)
    project = _project(db_session, engineer_user)
    result = EngineeringWorkspaceService(db_session, project.organization_id, package_uow_factory=_factory(db_session)).create(project.id, EngineeringWorkspaceCreate(discipline="civil"), engineer_user)
    workspace_id = result["id"]
    assert db_session.scalar(select(AuditLog).where(AuditLog.entity == "ENGINEERING_WORKSPACE", AuditLog.entity_id == workspace_id, AuditLog.action == "workspace_created")) is not None
    event = db_session.scalar(select(PackageConfigurationAuditEvent).where(PackageConfigurationAuditEvent.workspace_id == workspace_id, PackageConfigurationAuditEvent.category == "WORKSPACE_BINDING"))
    assert event is not None
    assert db_session.get(EngineeringWorkspace, workspace_id).package_binding_state == "FUTURE_UNAVAILABLE_UNBOUND"


def test_workspace_audit_failure_rolls_back_workspace_and_every_staged_audit(
    db_session, engineer_user, monkeypatch
):
    """The guarded UoW has one completion owner for write and both Audits."""
    from test_discipline_package_service import _factory, _project, _seed_configurable_registry
    from app.schemas.engineering_workspace import EngineeringWorkspaceCreate
    from app.services.engineering_workspace_service import EngineeringWorkspaceService
    import app.services.discipline_package_service as package_service

    _seed_configurable_registry(db_session)
    project = _project(db_session, engineer_user)

    def reject_generic_audit(*args, **kwargs):
        raise RuntimeError("forced staged Audit failure")

    monkeypatch.setattr(package_service, "stage_audit_log", reject_generic_audit)
    with pytest.raises(RuntimeError, match="forced staged Audit failure"):
        EngineeringWorkspaceService(
            db_session, project.organization_id, package_uow_factory=_factory(db_session)
        ).create(project.id, EngineeringWorkspaceCreate(discipline="civil"), engineer_user)

    assert db_session.scalar(select(EngineeringWorkspace.id).where(
        EngineeringWorkspace.project_id == project.id
    )) is None
    assert db_session.scalar(select(AuditLog.id).where(
        AuditLog.entity == "ENGINEERING_WORKSPACE"
    )) is None
    assert db_session.scalar(select(PackageConfigurationAuditEvent.event_id).where(
        PackageConfigurationAuditEvent.project_id == project.id
    )) is None


def test_audit_cursor_orders_known_time_then_historical_unknown_without_gaps(
    client, db_session, admin_user, admin_headers,
):
    """The explicit segment cursor preserves every tenant event exactly once."""
    organization_id = UUID("02810000-0000-4000-8000-000000000001")
    now = datetime.now(timezone.utc).replace(microsecond=0)
    known_events = [uuid4() for _ in range(3)]
    historical_events = [uuid4() for _ in range(3)]
    for offset, event_id in enumerate(known_events):
        db_session.add(PackageConfigurationAuditEvent(
            event_id=event_id,
            organization_id=organization_id,
            actor_user_id=admin_user.id,
            category="ORG_CONFIGURATION",
            action="replace",
            metadata_json={},
            occurred_at=now - timedelta(minutes=offset),
            correlation_id=uuid4(),
        ))
    db_session.flush()

    # Only the schema-owner fixture can construct legacy M3-shaped rows.  The
    # trigger is restored before any route executes, so this does not broaden
    # the runtime role or production permission model.
    connection = db_session.connection()
    connection.execute(text(
        "ALTER TABLE package_configuration_audit_events "
        "DISABLE TRIGGER trg_dp_audit_current_insert_guard"
    ))
    try:
        for event_id in historical_events:
            db_session.add(PackageConfigurationAuditEvent(
                event_id=event_id,
                organization_id=organization_id,
                actor_user_id=admin_user.id,
                category="ORG_CONFIGURATION",
                action="replace",
                metadata_json={},
                occurred_at=None,
                correlation_id=None,
            ))
        db_session.flush()
    finally:
        connection.execute(text(
            "ALTER TABLE package_configuration_audit_events "
            "ENABLE TRIGGER trg_dp_audit_current_insert_guard"
        ))

    seen: list[dict[str, object]] = []
    cursor = None
    while True:
        suffix = "" if cursor is None else f"&cursor={cursor}"
        response = client.get(
            f"/organizations/current/discipline-package-configuration/audit?limit=2{suffix}",
            headers=admin_headers,
        )
        assert response.status_code == 200
        payload = response.json()
        seen.extend(payload["items"])
        cursor = payload["next_cursor"]
        if cursor is None:
            break

    assert [item["event_id"] for item in seen] == [
        str(event_id) for event_id in known_events
    ] + [str(event_id) for event_id in sorted(historical_events, reverse=True)]
    assert [item["occurred_at"] for item in seen[:3]] == [
        (now - timedelta(minutes=offset)).isoformat() for offset in range(3)
    ]
    assert all(item["occurred_at"] is None for item in seen[3:])
    assert len({item["event_id"] for item in seen}) == 6

    # Cursors are bound to every effective query state and cannot cross the
    # category filter boundary.
    first_page = client.get(
        "/organizations/current/discipline-package-configuration/audit?limit=1",
        headers=admin_headers,
    ).json()
    assert first_page["next_cursor"]
    assert client.get(
        "/organizations/current/discipline-package-configuration/audit"
        f"?limit=1&category=WORKSPACE_BINDING&cursor={first_page['next_cursor']}",
        headers=admin_headers,
    ).status_code == 422
