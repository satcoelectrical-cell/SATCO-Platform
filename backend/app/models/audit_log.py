
from sqlalchemy import Column, Integer, String, DateTime, JSON
from sqlalchemy.dialects.postgresql import UUID as PostgreSQLUUID
from datetime import datetime

from app.core.database import Base


class AuditLog(Base):

    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)

    user_id = Column(Integer, nullable=True)

    action = Column(String, nullable=False)

    entity = Column(String, nullable=False)

    entity_id = Column(Integer, nullable=True)

    entity_uuid = Column(PostgreSQLUUID(as_uuid=True), nullable=True)

    details = Column(JSON, nullable=True)

    created_at = Column(
        DateTime,
        default=datetime.utcnow
    )
