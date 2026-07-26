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


@router.get("/")
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
    )
