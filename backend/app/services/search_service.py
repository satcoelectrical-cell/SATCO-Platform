from sqlalchemy.orm import Session

from app.repositories.search_repository import search_all


class SearchService:

    def search(
        self,
        db: Session,
        query: str,
        search_type: str = "all",
        page: int = 1,
        size: int = 20,
    ):

        results, totals = search_all(
            db,
            query,
            search_type,
            page,
            size,
        )


        total = (
            totals["customers"]
            +
            totals["projects"]
            +
            totals["contacts"]
        )


        return {
            "query": query,
            "type": search_type,
            "page": page,
            "size": size,
            "total": total,
            "results": results,
        }
