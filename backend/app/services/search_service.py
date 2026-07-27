from sqlalchemy.orm import Session

from app.repositories.search_repository import search_all
from app.enums import Discipline
from app.models.user import User


class SearchService:

    def search(
        self,
        db: Session,
        query: str,
        search_type: str = "all",
        page: int = 1,
        size: int = 20,
        current_user: User | None = None,
    ):

        results, totals = search_all(
            db,
            query,
            search_type,
            page,
            size,
            current_user,
        )


        total = (
            totals["customers"]
            +
            totals["projects"]
            +
            totals["contacts"]
            +
            totals["workspaces"]
        )

        results["workspaces"] = [
            {
                "id": workspace.id,
                "type": "workspace",
                "title": Discipline(
                    workspace.discipline
                ).display_name,
                "description": (
                    f"{workspace.project.project_code} — "
                    f"{workspace.project.name}"
                ),
                "project_id": workspace.project_id,
                "project_code": workspace.project.project_code,
                "discipline": workspace.discipline,
                "status": workspace.status,
            }
            for workspace in results["workspaces"]
        ]


        return {
            "query": query,
            "type": search_type,
            "page": page,
            "size": size,
            "total": total,
            "results": results,
        }
