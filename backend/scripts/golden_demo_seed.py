"""Create two additive, disposable Golden Demo project scopes.

The script refuses every database except the isolated qualification database
on loopback port 55433.  It never deletes or truncates existing records.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from urllib.parse import urlparse
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.database import engine
from app.core.security import hash_password, verify_password
from app.models.customer import Customer
from app.models.engineering_workspace import EngineeringWorkspace
from app.models.organization import Organization, UserOrganizationMembership
from app.models.project import Project
from app.models.user import User


EXPECTED_DATABASE = "satco_platform_patch02022_test"
EXPECTED_PORT = 55433
ORGANIZATION_ID = UUID("02810000-0000-4000-8000-00000000d001")
OUTSIDER_ORGANIZATION_ID = UUID("02810000-0000-4000-8000-00000000d002")
USERNAME = "golden-demo-engineer"
OUTSIDER_USERNAME = "golden-demo-outsider"
PROJECTS = (
    ("SAT-PRJ-2026-9001", "Golden Demo Rehearsal A"),
    ("SAT-PRJ-2026-9002", "Golden Demo Rehearsal B"),
)


def _guard_database() -> None:
    database_url = os.environ.get("GOLDEN_DEMO_DATABASE_URL", "")
    parsed = urlparse(database_url)
    if (
        parsed.scheme not in {"postgresql", "postgresql+psycopg2"}
        or parsed.hostname not in {"127.0.0.1", "localhost"}
        or parsed.port != EXPECTED_PORT
        or parsed.path != f"/{EXPECTED_DATABASE}"
    ):
        raise RuntimeError("Golden Demo database isolation guard rejected the target")
    configured = (
        os.environ.get("DATABASE_HOST"),
        int(os.environ.get("DATABASE_PORT", "0")),
        os.environ.get("DATABASE_NAME"),
    )
    if configured not in {
        ("127.0.0.1", EXPECTED_PORT, EXPECTED_DATABASE),
        ("localhost", EXPECTED_PORT, EXPECTED_DATABASE),
    }:
        raise RuntimeError("application database configuration is not isolated")


def _password() -> str:
    path = Path(os.environ.get("GOLDEN_DEMO_USER_PASSWORD_FILE", ""))
    value = path.read_text(encoding="utf-8").strip() if path.is_file() else ""
    if len(value) < 16:
        raise RuntimeError("Golden Demo user password file is missing or too short")
    return value


def main() -> None:
    _guard_database()
    password = _password()
    result: dict[str, object] = {"username": USERNAME, "projects": []}
    with Session(engine) as session:
        organization = session.get(Organization, ORGANIZATION_ID)
        if organization is None:
            organization = Organization(
                id=ORGANIZATION_ID,
                name="SATCO Golden Demo (Isolated)",
                slug="satco-golden-demo-isolated",
                is_active=True,
            )
            session.add(organization)

        outsider_organization = session.get(Organization, OUTSIDER_ORGANIZATION_ID)
        if outsider_organization is None:
            outsider_organization = Organization(
                id=OUTSIDER_ORGANIZATION_ID,
                name="SATCO Golden Demo Outsider (Isolated)",
                slug="satco-golden-demo-outsider-isolated",
                is_active=True,
            )
            session.add(outsider_organization)

        user = session.query(User).filter(User.username == USERNAME).one_or_none()
        if user is None:
            user = User(
                email="golden-demo-engineer@example.invalid",
                username=USERNAME,
                full_name="Golden Demo Engineer",
                role="engineer",
                is_active=True,
                activation_pending=False,
                auth_version=1,
                version=1,
                hashed_password=hash_password(password),
            )
            session.add(user)
            session.flush()
        else:
            if not verify_password(password, user.hashed_password):
                user.hashed_password = hash_password(password)
                user.auth_version += 1
            user.is_active = True
            user.activation_pending = False

        outsider = (
            session.query(User).filter(User.username == OUTSIDER_USERNAME).one_or_none()
        )
        if outsider is None:
            outsider = User(
                email="golden-demo-outsider@example.invalid",
                username=OUTSIDER_USERNAME,
                full_name="Golden Demo Outsider",
                role="engineer",
                is_active=True,
                activation_pending=False,
                auth_version=1,
                version=1,
                hashed_password=hash_password(password),
            )
            session.add(outsider)
            session.flush()
        elif not verify_password(password, outsider.hashed_password):
            outsider.hashed_password = hash_password(password)
            outsider.auth_version += 1
        outsider.is_active = True
        outsider.activation_pending = False

        outsider_membership = session.get(
            UserOrganizationMembership,
            (outsider.id, outsider_organization.id),
        )
        if outsider_membership is None:
            session.add(
                UserOrganizationMembership(
                    user_id=outsider.id,
                    organization_id=outsider_organization.id,
                    is_enabled=True,
                    is_selected=True,
                    version=1,
                )
            )
        else:
            outsider_membership.is_enabled = True
            outsider_membership.is_selected = True

        membership = session.get(
            UserOrganizationMembership, (user.id, organization.id)
        )
        if membership is None:
            session.add(
                UserOrganizationMembership(
                    user_id=user.id,
                    organization_id=organization.id,
                    is_enabled=True,
                    is_selected=True,
                    version=1,
                )
            )
        else:
            membership.is_enabled = True
            membership.is_selected = True

        customer = (
            session.query(Customer)
            .filter(
                Customer.organization_id == organization.id,
                Customer.name == "Golden Demo Synthetic Customer",
            )
            .one_or_none()
        )
        if customer is None:
            customer = Customer(
                organization_id=organization.id,
                name="Golden Demo Synthetic Customer",
                company="Isolated Qualification",
                email="demo-customer@example.invalid",
            )
            session.add(customer)
            session.flush()

        for project_code, project_name in PROJECTS:
            project = (
                session.query(Project)
                .filter(Project.project_code == project_code)
                .one_or_none()
            )
            if project is not None and project.organization_id != organization.id:
                raise RuntimeError("Golden Demo project code belongs to another organization")
            if project is None:
                project = Project(
                    organization_id=organization.id,
                    project_code=project_code,
                    name=project_name,
                    description="Disposable browser qualification scope; Human acceptance remains mandatory.",
                    customer_id=customer.id,
                    status="in_progress",
                    priority="high",
                    owner_id=user.id,
                    primary_assignee_id=user.id,
                    progress=0,
                )
                session.add(project)
                session.flush()
            workspace = (
                session.query(EngineeringWorkspace)
                .filter(
                    EngineeringWorkspace.project_id == project.id,
                    EngineeringWorkspace.discipline == "instrumentation",
                )
                .one_or_none()
            )
            if workspace is None:
                workspace = EngineeringWorkspace(
                    project_id=project.id,
                    discipline="instrumentation",
                    description="Golden Demo isolated Instrumentation workspace",
                    status="active",
                    owner_id=user.id,
                    primary_assignee_id=user.id,
                    created_by_id=user.id,
                    version=1,
                    canonical_discipline_id="instrumentation",
                    package_binding_state="FUTURE_UNAVAILABLE_UNBOUND",
                )
                session.add(workspace)
                session.flush()
            result["projects"].append(
                {
                    "project_id": project.id,
                    "project_code": project.project_code,
                    "workspace_id": workspace.id,
                }
            )
        session.commit()
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
