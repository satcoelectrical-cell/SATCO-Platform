from sqlalchemy.orm import Session
from sqlalchemy import or_
from uuid import UUID

from app.models.customer import Customer
from app.models.project import Project
from app.models.contact import Contact
from app.models.engineering_workspace import EngineeringWorkspace
from app.models.engineering_workspace import EngineeringWorkspaceMember
from app.models.user import User
from app.enums import WorkspaceStatus


def paginate(query, page: int, size: int):
    return (
        query
        .offset((page - 1) * size)
        .limit(size)
        .all()
    )


def search_customers(
    db: Session,
    keyword: str,
    page: int,
    size: int,
):

    query = (
        db.query(Customer)
        .filter(
            or_(
                Customer.name.ilike(keyword),
                Customer.company.ilike(keyword),
                Customer.email.ilike(keyword),
                Customer.phone.ilike(keyword),
            )
        )
    )

    total = query.count()

    return paginate(query, page, size), total



def search_projects(
    db: Session,
    keyword: str,
    page: int,
    size: int,
    organization_id: UUID,
):

    query = (
        db.query(Project)
        .filter(
            Project.organization_id == organization_id,
            or_(
                Project.name.ilike(keyword),
                Project.project_code.ilike(keyword),
                Project.status.ilike(keyword),
            )
        )
    )

    total = query.count()

    return paginate(query, page, size), total



def search_contacts(
    db: Session,
    keyword: str,
    page: int,
    size: int,
):

    query = (
        db.query(Contact)
        .filter(
            or_(
                Contact.first_name.ilike(keyword),
                Contact.last_name.ilike(keyword),
                Contact.email.ilike(keyword),
                Contact.mobile.ilike(keyword),
            )
        )
    )

    total = query.count()

    return paginate(query, page, size), total


def search_workspaces(
    db: Session,
    keyword: str,
    page: int,
    size: int,
    current_user: User,
    organization_id: UUID,
):
    owner = db.query(User).subquery()
    assignee = db.query(User).subquery()
    query = (
        db.query(EngineeringWorkspace)
        .join(Project, Project.id == EngineeringWorkspace.project_id)
        .outerjoin(owner, owner.c.id == EngineeringWorkspace.owner_id)
        .outerjoin(
            assignee,
            assignee.c.id
            == EngineeringWorkspace.primary_assignee_id,
        )
        .filter(
            EngineeringWorkspace.status
            != WorkspaceStatus.ARCHIVED.value,
            Project.organization_id == organization_id,
            or_(
                EngineeringWorkspace.discipline.ilike(keyword),
                (
                    EngineeringWorkspace.discipline
                    + " engineering workspace"
                ).ilike(keyword),
                Project.name.ilike(keyword),
                Project.project_code.ilike(keyword),
                EngineeringWorkspace.status.ilike(keyword),
                owner.c.username.ilike(keyword),
                owner.c.full_name.ilike(keyword),
                assignee.c.username.ilike(keyword),
                assignee.c.full_name.ilike(keyword),
            ),
        )
    )
    if current_user.role != "admin":
        query = query.filter(
            or_(
                Project.owner_id == current_user.id,
                Project.primary_assignee_id == current_user.id,
                EngineeringWorkspace.owner_id == current_user.id,
                EngineeringWorkspace.primary_assignee_id
                == current_user.id,
                EngineeringWorkspace.memberships.any(
                    EngineeringWorkspaceMember.user_id
                    == current_user.id
                ),
            )
        )
    query = query.order_by(
        EngineeringWorkspace.updated_at.desc(),
        EngineeringWorkspace.id.desc(),
    )
    total = query.count()
    return paginate(query, page, size), total



def search_all(
    db: Session,
    query: str,
    search_type: str = "all",
    page: int = 1,
    size: int = 20,
    current_user: User | None = None,
    organization_id: UUID | None = None,
):

    keyword = f"%{query}%"

    result = {
        "customers": [],
        "projects": [],
        "contacts": [],
        "workspaces": [],
    }

    totals = {
        "customers": 0,
        "projects": 0,
        "contacts": 0,
        "workspaces": 0,
    }


    if search_type in ("all", "customer"):
        result["customers"], totals["customers"] = search_customers(
            db,
            keyword,
            page,
            size,
        )


    if search_type in ("all", "project"):
        if organization_id is None:
            raise ValueError("Organization context is required for Project search")
        result["projects"], totals["projects"] = search_projects(
            db,
            keyword,
            page,
            size,
            organization_id,
        )


    if search_type in ("all", "contact"):
        result["contacts"], totals["contacts"] = search_contacts(
            db,
            keyword,
            page,
            size,
        )

    if search_type in ("all", "workspace") and current_user is not None:
        if organization_id is None:
            raise ValueError("Organization context is required for Workspace search")
        result["workspaces"], totals["workspaces"] = search_workspaces(
            db,
            keyword,
            page,
            size,
            current_user,
            organization_id,
        )


    return result, totals
