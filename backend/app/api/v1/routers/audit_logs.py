from fastapi import APIRouter


router = APIRouter(
    prefix="/audit-logs",
    tags=["Audit Logs"]
)


@router.get(
    "/",
    status_code=404,
)
def list_audit_logs():
    """Fail closed until canonical Organization ownership is available."""

    return {"outcome": "protected_not_found"}
