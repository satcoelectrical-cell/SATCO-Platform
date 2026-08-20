from sqlalchemy.orm import Session
from uuid import UUID

from app.permissions.roles import Role
from app.repositories.customer_repository import CustomerRepository
from app.schemas.customer import CustomerCreate
from app.services.audit_service import create_audit_log


class CustomerService:

    def __init__(self, db: Session):
        self.db = db
        self.repository = CustomerRepository(db)


    def get_all(
        self,
        *,
        organization_id: UUID,
        page: int = 1,
        size: int = 20,
        search: str | None = None,
    ):
        return self.repository.list_scoped(
            organization_id=organization_id,
            page=page,
            size=size,
            search=search,
        )


    def get_by_id(
        self,
        customer_id: int,
        *,
        organization_id: UUID,
    ):
        return self.repository.get_scoped(
            customer_id,
            organization_id=organization_id,
        )


    def create(
        self,
        customer: CustomerCreate,
        *,
        current_user,
        organization_id: UUID,
    ):

        self._require_editor(current_user)
        try:
            result = self.repository.create(
                customer,
                organization_id=organization_id,
            )

            create_audit_log(
                db=self.db,
                user_id=current_user.id,
                action="CREATE",
                entity="CUSTOMER",
                entity_id=result.id,
                details={"operation": "customer.create"},
            )
        except Exception:
            self.db.rollback()
            raise

        return result


    def update(
        self,
        customer_id: int,
        customer_data,
        *,
        current_user,
        organization_id: UUID,
    ):

        self._require_editor(current_user)
        customer = self.repository.get_scoped(
            customer_id,
            organization_id=organization_id,
        )

        if not customer:
            return None


        update_data = customer_data.model_dump(exclude_unset=True)
        if not update_data:
            raise ValueError("At least one Customer field is required")
        try:
            result = self.repository.update(customer, update_data)


            create_audit_log(
                db=self.db,
                user_id=current_user.id,
                action="UPDATE",
                entity="CUSTOMER",
                entity_id=result.id,
                details={
                    "operation": "customer.update",
                    "changed_fields": sorted(update_data),
                },
            )
        except Exception:
            self.db.rollback()
            raise


        return result



    def delete(
        self,
        customer_id: int,
        *,
        current_user,
        organization_id: UUID,
    ):

        if current_user.role != Role.ADMIN.value:
            return False
        customer = self.repository.get_scoped(
            customer_id,
            organization_id=organization_id,
        )

        if not customer:
            return False


        if self.repository.has_governed_references(customer_id):
            return False
        try:
            self.repository.delete(customer)


            create_audit_log(
                db=self.db,
                user_id=current_user.id,
                action="DELETE",
                entity="CUSTOMER",
                entity_id=customer_id,
                details={"operation": "customer.delete"},
            )
        except Exception:
            self.db.rollback()
            raise


        return True


    def get_detail(
        self,
        customer_id: int,
        *,
        organization_id: UUID | None = None,
    ):
        """Deprecated internal helper retained for future customer detail API."""
        detail = self.repository.get_detail(
            customer_id,
            organization_id=organization_id,
        )

        if detail is None:
            return None

        customer, contacts = detail

        return {
            "customer": customer,
            "contacts": contacts,
            "contact_count": len(contacts),
        }

    @staticmethod
    def _require_editor(current_user) -> None:
        if current_user.role not in {
            Role.ADMIN.value,
            Role.ENGINEER.value,
        }:
            raise PermissionError("Customer operation forbidden")
