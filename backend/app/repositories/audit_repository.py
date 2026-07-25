from sqlalchemy.orm import Session

from app.models.audit_log import AuditLog


def get_audit_logs(
    db: Session,
    page: int = 1,
    size: int = 20,
):

    query = db.query(AuditLog)

    total = query.count()

    items = (
        query
        .order_by(AuditLog.created_at.desc())
        .offset((page - 1) * size)
        .limit(size)
        .all()
    )

    return {
        "items": items,
        "total": total,
        "page": page,
        "size": size,
    }
