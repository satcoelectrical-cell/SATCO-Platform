from datetime import datetime

from sqlalchemy import CheckConstraint
from sqlalchemy import Column
from sqlalchemy import Date
from sqlalchemy import DateTime
from sqlalchemy import ForeignKey
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy import Text
from sqlalchemy import UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base
from app.enums import ProjectPriority, ProjectStatus


class ProjectCodeSequence(Base):
    __tablename__ = "project_code_sequences"

    year = Column(
        Integer,
        primary_key=True,
    )
    last_value = Column(
        Integer,
        nullable=False,
    )


class Project(Base):
    __tablename__ = "projects"
    __table_args__ = (
        UniqueConstraint(
            "project_code",
            name="uq_projects_project_code",
        ),
        CheckConstraint(
            "project_code ~ '^SAT-PRJ-[0-9]{4}-[0-9]{4,}$'",
            name="ck_projects_project_code_format",
        ),
        CheckConstraint(
            "status IN "
            "('new', 'in_progress', 'on_hold', 'completed', 'cancelled')",
            name="ck_projects_status",
        ),
        CheckConstraint(
            "priority IN ('low', 'medium', 'high', 'critical')",
            name="ck_projects_priority",
        ),
        CheckConstraint(
            "progress BETWEEN 0 AND 100",
            name="ck_projects_progress",
        ),
    )

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )
    project_code = Column(
        String(32),
        nullable=False,
    )
    name = Column(
        String(200),
        nullable=False,
    )
    description = Column(
        Text,
        nullable=True,
    )
    customer_id = Column(
        Integer,
        ForeignKey("customers.id"),
        nullable=False,
        index=True,
    )
    status = Column(
        String(32),
        default=ProjectStatus.NEW.value,
        nullable=False,
        index=True,
    )
    priority = Column(
        String(16),
        default=ProjectPriority.MEDIUM.value,
        nullable=False,
        index=True,
    )
    owner_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=True,
        index=True,
    )
    primary_assignee_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=True,
        index=True,
    )
    start_date = Column(
        Date,
        nullable=True,
        index=True,
    )
    target_completion_date = Column(
        Date,
        nullable=True,
        index=True,
    )
    completed_at = Column(
        DateTime(timezone=True),
        nullable=True,
    )
    progress = Column(
        Integer,
        default=0,
        nullable=False,
    )
    created_at = Column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False,
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    customer = relationship(
        "Customer",
        back_populates="projects",
    )
    owner = relationship(
        "User",
        foreign_keys=[owner_id],
    )
    primary_assignee = relationship(
        "User",
        foreign_keys=[primary_assignee_id],
    )
