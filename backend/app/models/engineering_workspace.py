from sqlalchemy import CheckConstraint
from sqlalchemy import Column
from sqlalchemy import DateTime
from sqlalchemy import ForeignKey
from sqlalchemy import Index
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy import Text
from sqlalchemy import UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base
from app.enums import Discipline, WorkspaceStatus


DISCIPLINE_VALUES = ", ".join(
    f"'{discipline.value}'" for discipline in Discipline
)
STATUS_VALUES = ", ".join(
    f"'{status.value}'" for status in WorkspaceStatus
)


class EngineeringWorkspace(Base):
    __tablename__ = "engineering_workspaces"
    __table_args__ = (
        UniqueConstraint(
            "project_id",
            "discipline",
            name="uq_engineering_workspaces_project_discipline",
        ),
        CheckConstraint(
            f"discipline IN ({DISCIPLINE_VALUES})",
            name="ck_engineering_workspaces_discipline",
        ),
        CheckConstraint(
            f"status IN ({STATUS_VALUES})",
            name="ck_engineering_workspaces_status",
        ),
        CheckConstraint(
            "version >= 1",
            name="ck_engineering_workspaces_version",
        ),
        CheckConstraint(
            "(status = 'archived' AND archived_at IS NOT NULL) OR "
            "(status <> 'archived' AND archived_at IS NULL)",
            name="ck_engineering_workspaces_archive_state",
        ),
        Index(
            "ix_engineering_workspaces_project_status",
            "project_id",
            "status",
        ),
    )

    id = Column(Integer, primary_key=True)
    project_id = Column(
        Integer,
        ForeignKey(
            "projects.id",
            name="fk_engineering_workspaces_project_id_projects",
            ondelete="RESTRICT",
        ),
        nullable=False,
    )
    discipline = Column(String(32), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(
        String(32),
        nullable=False,
        default=WorkspaceStatus.DRAFT.value,
        server_default=WorkspaceStatus.DRAFT.value,
        index=True,
    )
    owner_id = Column(
        Integer,
        ForeignKey(
            "users.id",
            name="fk_engineering_workspaces_owner_id_users",
            ondelete="RESTRICT",
        ),
        nullable=False,
        index=True,
    )
    primary_assignee_id = Column(
        Integer,
        ForeignKey(
            "users.id",
            name="fk_engineering_workspaces_primary_assignee_id_users",
            ondelete="RESTRICT",
        ),
        nullable=True,
        index=True,
    )
    created_by_id = Column(
        Integer,
        ForeignKey(
            "users.id",
            name="fk_engineering_workspaces_created_by_id_users",
            ondelete="RESTRICT",
        ),
        nullable=False,
    )
    version = Column(
        Integer,
        nullable=False,
        default=1,
        server_default="1",
    )
    archived_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
        index=True,
    )

    project = relationship("Project")
    owner = relationship("User", foreign_keys=[owner_id])
    primary_assignee = relationship(
        "User",
        foreign_keys=[primary_assignee_id],
    )
    created_by = relationship("User", foreign_keys=[created_by_id])
    memberships = relationship(
        "EngineeringWorkspaceMember",
        back_populates="workspace",
    )

    @property
    def display_name(self) -> str:
        return Discipline(self.discipline).display_name


class EngineeringWorkspaceMember(Base):
    __tablename__ = "engineering_workspace_members"

    workspace_id = Column(
        Integer,
        ForeignKey(
            "engineering_workspaces.id",
            name="fk_ew_members_workspace_id_workspaces",
            ondelete="RESTRICT",
        ),
        primary_key=True,
    )
    user_id = Column(
        Integer,
        ForeignKey(
            "users.id",
            name="fk_engineering_workspace_members_user_id_users",
            ondelete="RESTRICT",
        ),
        primary_key=True,
        index=True,
    )
    added_by_id = Column(
        Integer,
        ForeignKey(
            "users.id",
            name="fk_engineering_workspace_members_added_by_id_users",
            ondelete="RESTRICT",
        ),
        nullable=False,
        index=True,
    )
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    workspace = relationship(
        "EngineeringWorkspace",
        back_populates="memberships",
    )
    user = relationship("User", foreign_keys=[user_id])
    added_by = relationship("User", foreign_keys=[added_by_id])
