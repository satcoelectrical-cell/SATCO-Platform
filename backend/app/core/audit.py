from sqlalchemy.orm import Session

from app.services.audit_service import create_audit_log


def audit_event(
    db: Session,
    user_id: int,
    action: str,
    entity: str,
    entity_id: int,
    name: str,
):
    create_audit_log(
        db=db,
        user_id=user_id,
        action=action,
        entity=entity,
        entity_id=entity_id,
        details={
            "name": name
        },
    )
