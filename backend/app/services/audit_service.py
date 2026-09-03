from app.models.audit_log import AuditLog
from app.repositories import audit_repository


def stage_audit_log(db, user_id, action, entity, entity_id=None, details=None):
    """Stage existing generic Audit data without transaction completion."""

    log = AuditLog(
        user_id=user_id,
        action=action,
        entity=entity,
        entity_id=entity_id,
        details=details,
    )
    db.add(log)
    return log


def create_audit_log(
    db,
    user_id,
    action,
    entity,
    entity_id=None,
    details=None,
):

    log = AuditLog(
        user_id=user_id,
        action=action,
        entity=entity,
        entity_id=entity_id,
        details=details,
    )

    db.add(log)
    db.commit()
    db.refresh(log)

    return log



def get_audit_logs(
    db,
    page=1,
    size=20,
):

    return audit_repository.get_audit_logs(
        db,
        page,
        size,
    )
