
from app.models.audit_log import AuditLog


def create_audit_log(
    db,
    user_id,
    action,
    entity,
    entity_id=None,
    details=None
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

    return log
