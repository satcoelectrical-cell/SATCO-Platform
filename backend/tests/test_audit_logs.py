from uuid import uuid4

from sqlalchemy import event

from app.core.security import create_access_token
from app.models.audit_log import AuditLog
from app.models.organization import Organization, UserOrganizationMembership
from app.permissions.roles import Role
from conftest import create_user


PROTECTED_OUTCOME = {"outcome": "protected_not_found"}


def _assert_disabled(response):
    assert response.status_code == 404
    assert response.json() == PROTECTED_OUTCOME
    assert "items" not in response.json()
    assert "total" not in response.json()
    assert "page" not in response.json()
    assert "size" not in response.json()


def test_audit_logs_are_fail_closed_for_every_caller(
    client,
    engineer_headers,
    admin_headers,
):
    _assert_disabled(client.get("/audit-logs/"))
    _assert_disabled(client.get("/audit-logs/", headers=engineer_headers))
    _assert_disabled(client.get("/audit-logs/", headers=admin_headers))


def test_audit_logs_disclose_no_two_tenant_rows_counts_or_pagination(
    client,
    db_session,
    admin_user,
    admin_headers,
):
    other_organization = Organization(id=uuid4(), is_active=True)
    db_session.add(other_organization)
    other_admin = create_user(
        db_session,
        username=f"other-audit-admin-{uuid4().hex[:8]}",
        role=Role.ADMIN,
    )
    default_membership = (
        db_session.query(UserOrganizationMembership)
        .filter_by(user_id=other_admin.id)
        .one()
    )
    default_membership.is_enabled = False
    default_membership.is_selected = False
    db_session.add(
        UserOrganizationMembership(
            user_id=other_admin.id,
            organization_id=other_organization.id,
            is_enabled=True,
            is_selected=True,
        )
    )
    db_session.add_all(
        [
            AuditLog(
                user_id=admin_user.id,
                action="TENANT_A_EVENT",
                entity="CUSTOMER",
                entity_id=101,
            ),
            AuditLog(
                user_id=other_admin.id,
                action="TENANT_B_EVENT",
                entity="CUSTOMER",
                entity_id=202,
            ),
        ]
    )
    db_session.commit()
    other_headers = {
        "Authorization": "Bearer "
        + create_access_token(other_admin.id, other_admin.auth_version)
    }

    audit_selects = []

    def observe_audit_query(connection, cursor, statement, parameters, context, executemany):
        if "audit_logs" in statement.lower():
            audit_selects.append(statement)

    bind = db_session.get_bind()
    event.listen(bind, "before_cursor_execute", observe_audit_query)
    try:
        for headers in (admin_headers, other_headers):
            _assert_disabled(
                client.get(
                    "/audit-logs/",
                    headers=headers,
                    params={"page": 999, "size": 1},
                )
            )
    finally:
        event.remove(bind, "before_cursor_execute", observe_audit_query)

    assert audit_selects == []


def test_audit_logs_stay_disabled_after_admin_membership_becomes_stale(
    client,
    db_session,
    admin_user,
    admin_headers,
):
    membership = (
        db_session.query(UserOrganizationMembership)
        .filter_by(user_id=admin_user.id)
        .one()
    )
    membership.is_enabled = False
    membership.is_selected = False
    db_session.commit()

    _assert_disabled(client.get("/audit-logs/", headers=admin_headers))
