from uuid import UUID, uuid4

import pytest

from app.models.customer import Customer
from app.models.organization import Organization
from app.models.project import Project
from app.models.engineering_workspace import EngineeringWorkspace
from app.models.engineering_object_command import AuthenticatedActor
from app.enums import EngineeringDiscipline
from app.exceptions.engineering_object import EngineeringObjectValidationError
from app.exceptions.evidence import EvidenceValidationError
from app.repositories.engineering_context_repository import (
    EngineeringContextRepository,
)
from app.repositories.engineering_object_unit_of_work import (
    SqlAlchemyReferenceValidator,
)
from app.repositories.engineering_relationship_unit_of_work import (
    _workspace_access,
)
from app.repositories.evidence_unit_of_work import SqlAlchemyEvidenceValidator
from app.models.evidence_command import EvidenceActor


def test_foreign_organization_project_is_protected_and_not_searchable(
    client,
    db_session,
    engineer_headers,
):
    foreign_organization = Organization(id=uuid4(), is_active=True)
    customer = Customer(name="Foreign Organization Customer")
    db_session.add_all([foreign_organization, customer])
    db_session.flush()
    foreign_project = Project(
        organization_id=foreign_organization.id,
        project_code="SAT-PRJ-2099-9901",
        name="Foreign Tenant Secret Project",
        customer_id=customer.id,
        status="new",
        priority="medium",
        progress=0,
    )
    db_session.add(foreign_project)
    db_session.commit()

    detail = client.get(
        f"/projects/{foreign_project.id}",
        headers=engineer_headers,
    )
    assert detail.status_code == 404

    listing = client.get("/projects/", headers=engineer_headers)
    assert listing.status_code == 200
    assert foreign_project.id not in {
        item["id"] for item in listing.json()["items"]
    }

    search = client.get(
        "/search/",
        params={"q": "Foreign Tenant Secret", "type": "project"},
        headers=engineer_headers,
    )
    assert search.status_code == 200
    assert search.json()["total"] == 0
    assert search.json()["results"]["projects"] == []


def test_project_transport_rejects_client_organization_id(
    client,
    engineer_headers,
):
    response = client.post(
        "/projects/",
        json={
            "name": "Client Scoped Project",
            "customer_id": 1,
            "organization_id": str(uuid4()),
        },
        headers=engineer_headers,
    )

    assert response.status_code == 422


def test_all_dependent_project_lookups_enforce_organization_scope(
    client,
    db_session,
    engineer_user,
    engineer_headers,
):
    organization_id = UUID("02810000-0000-4000-8000-000000000001")
    foreign_organization = Organization(id=uuid4(), is_active=True)
    customer = Customer(name="Dependent Scope Customer")
    db_session.add_all([foreign_organization, customer])
    db_session.flush()
    same_project = Project(
        organization_id=organization_id,
        project_code="SAT-PRJ-2099-9911",
        name="Same Organization Project",
        customer_id=customer.id,
        owner_id=engineer_user.id,
    )
    foreign_project = Project(
        organization_id=foreign_organization.id,
        project_code="SAT-PRJ-2099-9912",
        name="Foreign Organization Project",
        customer_id=customer.id,
        owner_id=engineer_user.id,
    )
    db_session.add_all([same_project, foreign_project])
    db_session.flush()
    same_workspace = EngineeringWorkspace(
        project_id=same_project.id,
        discipline="electrical",
        status="active",
        owner_id=engineer_user.id,
        created_by_id=engineer_user.id,
        version=1,
    )
    foreign_workspace = EngineeringWorkspace(
        project_id=foreign_project.id,
        discipline="electrical",
        status="active",
        owner_id=engineer_user.id,
        created_by_id=engineer_user.id,
        version=1,
    )
    db_session.add_all([same_workspace, foreign_workspace])
    db_session.commit()

    assert client.get(
        f"/workspaces/{same_workspace.id}", headers=engineer_headers
    ).status_code == 200
    assert client.get(
        f"/workspaces/{foreign_workspace.id}", headers=engineer_headers
    ).status_code == 404

    contexts = EngineeringContextRepository(db_session)
    assert contexts.get_project(same_project.id, engineer_user) is not None
    assert contexts.get_project(foreign_project.id, engineer_user) is None

    actor = AuthenticatedActor(engineer_user.id, organization_id)
    object_validator = SqlAlchemyReferenceValidator(db_session)
    assert object_validator.validate_creation_references(
        actor=actor,
        project_id=same_project.id,
        steward_id=engineer_user.id,
        evidence_references=(),
        discipline=EngineeringDiscipline.ELECTRICAL,
    )["workspace_id"] == same_workspace.id
    with pytest.raises(EngineeringObjectValidationError):
        object_validator.validate_creation_references(
            actor=actor,
            project_id=foreign_project.id,
            steward_id=engineer_user.id,
            evidence_references=(),
            discipline=EngineeringDiscipline.ELECTRICAL,
        )

    assert _workspace_access(
        db_session, engineer_user.id, same_workspace.id, organization_id
    ) is True
    assert _workspace_access(
        db_session, engineer_user.id, foreign_workspace.id, organization_id
    ) is False

    evidence_validator = SqlAlchemyEvidenceValidator(db_session)
    evidence_actor = EvidenceActor(engineer_user.id, organization_id)
    evidence_validator.validate_scope(
        actor=evidence_actor,
        project_id=same_project.id,
        workspace_id=same_workspace.id,
    )
    with pytest.raises(EvidenceValidationError):
        evidence_validator.validate_scope(
            actor=evidence_actor,
            project_id=foreign_project.id,
            workspace_id=foreign_workspace.id,
        )
