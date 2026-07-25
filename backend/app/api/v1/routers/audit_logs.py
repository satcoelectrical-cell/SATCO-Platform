from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.audit import AuditLogListResponse
from app.services.audit_service import get_audit_logs
from app.dependencies.auth import require_role


router = APIRouter(
    prefix="/audit-logs",
    tags=["Audit Logs"]
)


@router.get(
    "/",
    response_model=AuditLogListResponse,
)
def list_audit_logs(
    page: int = 1,
    size: int = 20,
    db: Session = Depends(get_db),
    current_user=Depends(require_role("admin")),
):

    return get_audit_logs(
        db,
        page,
        size,
    )
