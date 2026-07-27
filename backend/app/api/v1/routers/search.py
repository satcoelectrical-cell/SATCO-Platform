from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.services.search_service import SearchService


router = APIRouter(
    prefix="/search",
    tags=["Search"],
)


service = SearchService()

SEARCH_WORKSPACE_EXAMPLE = {
    "query": "electrical",
    "type": "workspace",
    "page": 1,
    "size": 20,
    "total": 1,
    "results": {
        "customers": [],
        "projects": [],
        "contacts": [],
        "workspaces": [
            {
                "id": 17,
                "type": "workspace",
                "title": "Electrical Engineering Workspace",
                "description": (
                    "SAT-PRJ-2026-0001 — PLC Modernization"
                ),
                "project_id": 42,
                "project_code": "SAT-PRJ-2026-0001",
                "discipline": "electrical",
                "status": "active",
            }
        ],
    },
}


@router.get(
    "/",
    responses={
        200: {
            "description": "Authorization-filtered Universal Search",
            "content": {
                "application/json": {
                    "example": SEARCH_WORKSPACE_EXAMPLE
                }
            },
        },
        401: {
            "description": "Authentication required",
            "content": {
                "application/json": {
                    "example": {"detail": "Not authenticated"}
                }
            },
        },
        422: {
            "description": "Search request validation failed",
            "content": {
                "application/json": {
                    "example": {
                        "detail": [
                            {
                                "loc": ["query", "q"],
                                "msg": "Field required",
                                "type": "missing",
                            }
                        ]
                    }
                }
            },
        },
    },
)
def search(
    q: str = Query(..., min_length=1),
    search_type: str = Query(
        "all",
        alias="type",
    ),
    page: int = Query(
        1,
        ge=1,
    ),
    size: int = Query(
        20,
        ge=1,
        le=100,
    ),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):

    return service.search(
        db,
        q,
        search_type,
        page,
        size,
        current_user,
    )
