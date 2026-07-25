from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.models.customer import Customer
from app.models.project import Project
from app.models.contact import Contact


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
):

    query = (
        db.query(Project)
        .filter(
            or_(
                Project.name.ilike(keyword),
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



def search_all(
    db: Session,
    query: str,
    search_type: str = "all",
    page: int = 1,
    size: int = 20,
):

    keyword = f"%{query}%"

    result = {
        "customers": [],
        "projects": [],
        "contacts": [],
    }

    totals = {
        "customers": 0,
        "projects": 0,
        "contacts": 0,
    }


    if search_type in ("all", "customer"):
        result["customers"], totals["customers"] = search_customers(
            db,
            keyword,
            page,
            size,
        )


    if search_type in ("all", "project"):
        result["projects"], totals["projects"] = search_projects(
            db,
            keyword,
            page,
            size,
        )


    if search_type in ("all", "contact"):
        result["contacts"], totals["contacts"] = search_contacts(
            db,
            keyword,
            page,
            size,
        )


    return result, totals
