from sqlalchemy.orm import Session

from app.enums import ProjectStatus
from app.repositories.customer_repository import CustomerRepository
from app.repositories.project_repository import ProjectRepository
from app.schemas.project import ProjectCreate, ProjectUpdate
from app.services.audit_service import create_audit_log


class ProjectService:

    def __init__(self, db: Session):
        self.db = db
        self.repository = ProjectRepository(db)
        self.customer_repository = CustomerRepository(db)

    def get_all(
        self,
        page: int = 1,
        size: int = 20,
        customer_id: int | None = None,
        status: str | None = None,
        sort_by: str = "created_at",
        order: str = "desc",
    ):
        return self.repository.get_all(
            page,
            size,
            customer_id,
            status,
            sort_by,
            order,
        )

    def get_by_id(self, project_id: int):
        return self.repository.get_by_id(project_id)

    def create(
        self,
        project: ProjectCreate,
        user_id: int,
    ):
        self._validate_customer(project.customer_id)

        result = self.repository.create(project)

        create_audit_log(
            db=self.db,
            user_id=user_id,
            action="CREATE",
            entity="PROJECT",
            entity_id=result.id,
            details=self._audit_details(result),
        )

        return result

    def update(
        self,
        project_id: int,
        project_data: ProjectUpdate,
        user_id: int,
    ):
        project = self.repository.get_by_id(project_id)

        if project is None:
            return None

        if project_data.customer_id is not None:
            self._validate_customer(project_data.customer_id)

        changed_fields = list(
            project_data.model_dump(
                exclude_unset=True
            )
        )
        result = self.repository.update(
            project,
            project_data,
        )

        details = self._audit_details(result)
        details["changed_fields"] = changed_fields

        create_audit_log(
            db=self.db,
            user_id=user_id,
            action="UPDATE",
            entity="PROJECT",
            entity_id=result.id,
            details=details,
        )

        return result

    def delete(
        self,
        project_id: int,
        user_id: int,
    ) -> bool:
        project = self.repository.get_by_id(project_id)

        if project is None:
            return False

        details = self._audit_details(project)

        self.repository.delete(project)

        create_audit_log(
            db=self.db,
            user_id=user_id,
            action="DELETE",
            entity="PROJECT",
            entity_id=project_id,
            details=details,
        )

        return True

    def _validate_customer(self, customer_id: int) -> None:
        customer = self.customer_repository.get_by_id(
            customer_id
        )

        if customer is None:
            raise ValueError("Customer not found")

    @staticmethod
    def _audit_details(project) -> dict:
        status = project.status

        if isinstance(status, ProjectStatus):
            status = status.value

        return {
            "project_name": project.name,
            "customer_id": project.customer_id,
            "status": status,
        }
