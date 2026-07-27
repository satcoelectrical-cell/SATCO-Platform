from sqlalchemy import CheckConstraint
from sqlalchemy import Column
from sqlalchemy import DateTime
from sqlalchemy import ForeignKey
from sqlalchemy import Index
from sqlalchemy import Integer
from sqlalchemy import Numeric
from sqlalchemy import String
from sqlalchemy import Text
from sqlalchemy import UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base
from app.enums import ContextAuthority
from app.enums import ContextConfidentiality
from app.enums import ContextKind
from app.enums import ContextLifecycle
from app.enums import ContextScope
from app.enums import ContextSourceKind
from app.enums import ContextSubjectKind


def _values(enum_type) -> str:
    return ", ".join(f"'{item.value}'" for item in enum_type)


CONTEXT_KIND_VALUES = _values(ContextKind)
CONTEXT_SCOPE_VALUES = _values(ContextScope)
CONTEXT_AUTHORITY_VALUES = _values(ContextAuthority)
CONTEXT_LIFECYCLE_VALUES = _values(ContextLifecycle)
CONTEXT_SUBJECT_KIND_VALUES = _values(ContextSubjectKind)
CONTEXT_SOURCE_KIND_VALUES = _values(ContextSourceKind)
CONTEXT_CONFIDENTIALITY_VALUES = _values(ContextConfidentiality)


class EngineeringContext(Base):
    __tablename__ = "engineering_contexts"
    __table_args__ = (
        UniqueConstraint(
            "context_key",
            name="uq_engineering_contexts_context_key",
        ),
        CheckConstraint(
            f"kind IN ({CONTEXT_KIND_VALUES})",
            name="ck_engineering_contexts_kind",
        ),
        CheckConstraint(
            f"scope IN ({CONTEXT_SCOPE_VALUES})",
            name="ck_engineering_contexts_scope",
        ),
        CheckConstraint(
            f"authority IN ({CONTEXT_AUTHORITY_VALUES})",
            name="ck_engineering_contexts_authority",
        ),
        CheckConstraint(
            f"lifecycle IN ({CONTEXT_LIFECYCLE_VALUES})",
            name="ck_engineering_contexts_lifecycle",
        ),
        CheckConstraint(
            "(scope = 'project' AND workspace_id IS NULL) OR "
            "(scope = 'workspace' AND workspace_id IS NOT NULL)",
            name="ck_engineering_contexts_scope_workspace",
        ),
        CheckConstraint(
            "(kind = 'assumption' AND authority = 'assumption') OR "
            "(kind <> 'assumption' AND authority <> 'assumption')",
            name="ck_engineering_contexts_kind_authority",
        ),
        CheckConstraint(
            "(lifecycle = 'withdrawn' AND withdrawn_at IS NOT NULL "
            "AND withdrawal_reason IS NOT NULL) OR "
            "(lifecycle = 'current' AND withdrawn_at IS NULL "
            "AND withdrawal_reason IS NULL)",
            name="ck_engineering_contexts_lifecycle_state",
        ),
        CheckConstraint(
            "version >= 1",
            name="ck_engineering_contexts_version",
        ),
        Index(
            "ix_engineering_contexts_project_lifecycle",
            "project_id",
            "lifecycle",
        ),
        Index(
            "ix_engineering_contexts_workspace_lifecycle",
            "workspace_id",
            "lifecycle",
        ),
        Index(
            "ix_engineering_contexts_owner_id",
            "owner_id",
        ),
        Index(
            "ix_engineering_contexts_steward_id",
            "steward_id",
        ),
    )

    id = Column(Integer, primary_key=True)
    context_key = Column(String(36), nullable=False)
    kind = Column(String(48), nullable=False)
    scope = Column(String(16), nullable=False)
    project_id = Column(
        Integer,
        ForeignKey(
            "projects.id",
            name="fk_engineering_contexts_project_id_projects",
            ondelete="RESTRICT",
        ),
        nullable=False,
    )
    workspace_id = Column(
        Integer,
        ForeignKey(
            "engineering_workspaces.id",
            name=(
                "fk_engineering_contexts_workspace_id_"
                "engineering_workspaces"
            ),
            ondelete="RESTRICT",
        ),
        nullable=True,
    )
    owner_id = Column(
        Integer,
        ForeignKey(
            "users.id",
            name="fk_engineering_contexts_owner_id_users",
            ondelete="RESTRICT",
        ),
        nullable=False,
    )
    steward_id = Column(
        Integer,
        ForeignKey(
            "users.id",
            name="fk_engineering_contexts_steward_id_users",
            ondelete="RESTRICT",
        ),
        nullable=False,
    )
    created_by_id = Column(
        Integer,
        ForeignKey(
            "users.id",
            name="fk_engineering_contexts_created_by_id_users",
            ondelete="RESTRICT",
        ),
        nullable=False,
    )
    authority = Column(String(32), nullable=False)
    lifecycle = Column(
        String(16),
        nullable=False,
        default=ContextLifecycle.CURRENT.value,
        server_default=ContextLifecycle.CURRENT.value,
    )
    purpose = Column(String(500), nullable=True)
    version = Column(
        Integer,
        nullable=False,
        default=1,
        server_default="1",
    )
    withdrawal_reason = Column(Text, nullable=True)
    withdrawn_at = Column(DateTime(timezone=True), nullable=True)
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
    )

    project = relationship("Project")
    workspace = relationship("EngineeringWorkspace")
    owner = relationship("User", foreign_keys=[owner_id])
    steward = relationship("User", foreign_keys=[steward_id])
    created_by = relationship("User", foreign_keys=[created_by_id])
    facts = relationship(
        "EngineeringContextFact",
        back_populates="context",
        uselist=False,
    )
    engineering_value = relationship(
        "EngineeringContextValue",
        back_populates="context",
        uselist=False,
    )
    assumption = relationship(
        "EngineeringContextAssumption",
        back_populates="context",
        uselist=False,
    )
    subject_references = relationship(
        "EngineeringContextSubjectReference",
        back_populates="context",
    )
    source_references = relationship(
        "EngineeringContextSourceReference",
        back_populates="context",
    )


class EngineeringContextFact(Base):
    __tablename__ = "engineering_context_facts"

    context_id = Column(
        Integer,
        ForeignKey(
            "engineering_contexts.id",
            name="fk_engineering_context_facts_context_id_contexts",
            ondelete="RESTRICT",
        ),
        primary_key=True,
    )
    statement = Column(Text, nullable=False)
    uncertainty = Column(Text, nullable=True)

    context = relationship("EngineeringContext", back_populates="facts")


class EngineeringContextValue(Base):
    __tablename__ = "engineering_context_values"
    __table_args__ = (
        CheckConstraint(
            "tolerance_min IS NULL OR tolerance_max IS NULL "
            "OR tolerance_min <= tolerance_max",
            name="ck_engineering_context_values_tolerance_range",
        ),
        CheckConstraint(
            "range_min IS NULL OR range_max IS NULL "
            "OR range_min <= range_max",
            name="ck_engineering_context_values_value_range",
        ),
    )

    context_id = Column(
        Integer,
        ForeignKey(
            "engineering_contexts.id",
            name="fk_engineering_context_values_context_id_contexts",
            ondelete="RESTRICT",
        ),
        primary_key=True,
    )
    numeric_value = Column(Numeric(30, 10), nullable=False)
    unit = Column(String(64), nullable=False)
    quantity_type = Column(String(128), nullable=False)
    tolerance_min = Column(Numeric(30, 10), nullable=True)
    tolerance_max = Column(Numeric(30, 10), nullable=True)
    range_min = Column(Numeric(30, 10), nullable=True)
    range_max = Column(Numeric(30, 10), nullable=True)
    basis = Column(Text, nullable=False)
    condition_type = Column(String(32), nullable=False)
    condition = Column(Text, nullable=False)
    uncertainty = Column(Text, nullable=True)

    context = relationship(
        "EngineeringContext",
        back_populates="engineering_value",
    )


class EngineeringContextAssumption(Base):
    __tablename__ = "engineering_context_assumptions"

    context_id = Column(
        Integer,
        ForeignKey(
            "engineering_contexts.id",
            name="fk_engineering_context_assumptions_context_id_contexts",
            ondelete="RESTRICT",
        ),
        primary_key=True,
    )
    statement = Column(Text, nullable=False)
    reason = Column(Text, nullable=False)
    consequence = Column(Text, nullable=False)
    confirmation_condition = Column(Text, nullable=False)

    context = relationship(
        "EngineeringContext",
        back_populates="assumption",
    )


class EngineeringContextSubjectReference(Base):
    __tablename__ = "engineering_context_subject_references"
    __table_args__ = (
        CheckConstraint(
            f"subject_kind IN ({CONTEXT_SUBJECT_KIND_VALUES})",
            name="ck_engineering_context_subject_refs_kind",
        ),
        CheckConstraint(
            "(subject_kind = 'project' AND subject_project_id IS NOT NULL "
            "AND subject_workspace_id IS NULL AND discipline IS NULL) OR "
            "(subject_kind = 'workspace' AND subject_project_id IS NULL "
            "AND subject_workspace_id IS NOT NULL AND discipline IS NULL) "
            "OR (subject_kind = 'discipline' "
            "AND subject_project_id IS NULL "
            "AND subject_workspace_id IS NULL AND discipline IS NOT NULL)",
            name="ck_engineering_context_subject_refs_target",
        ),
        UniqueConstraint(
            "context_id",
            "subject_kind",
            "subject_project_id",
            "subject_workspace_id",
            "discipline",
            name="uq_engineering_context_subject_refs_identity",
        ),
        Index(
            "ix_engineering_context_subject_refs_project_id",
            "subject_project_id",
        ),
        Index(
            "ix_engineering_context_subject_refs_workspace_id",
            "subject_workspace_id",
        ),
    )

    id = Column(Integer, primary_key=True)
    context_id = Column(
        Integer,
        ForeignKey(
            "engineering_contexts.id",
            name="fk_engineering_context_subject_refs_context_id_contexts",
            ondelete="RESTRICT",
        ),
        nullable=False,
    )
    subject_kind = Column(String(32), nullable=False)
    subject_project_id = Column(
        Integer,
        ForeignKey(
            "projects.id",
            name="fk_engineering_context_subject_refs_project_id_projects",
            ondelete="RESTRICT",
        ),
        nullable=True,
    )
    subject_workspace_id = Column(
        Integer,
        ForeignKey(
            "engineering_workspaces.id",
            name=(
                "fk_engineering_context_subject_refs_workspace_id_"
                "workspaces"
            ),
            ondelete="RESTRICT",
        ),
        nullable=True,
    )
    discipline = Column(String(32), nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    context = relationship(
        "EngineeringContext",
        back_populates="subject_references",
    )


class EngineeringContextSourceReference(Base):
    __tablename__ = "engineering_context_source_references"
    __table_args__ = (
        CheckConstraint(
            f"source_kind IN ({CONTEXT_SOURCE_KIND_VALUES})",
            name="ck_engineering_context_source_refs_kind",
        ),
        CheckConstraint(
            f"confidentiality IN ({CONTEXT_CONFIDENTIALITY_VALUES})",
            name="ck_engineering_context_source_refs_confidentiality",
        ),
        CheckConstraint(
            "confidentiality <> 'restricted' "
            "OR source_owner_id IS NOT NULL",
            name="ck_engineering_context_source_refs_restricted_owner",
        ),
        UniqueConstraint(
            "context_id",
            "source_kind",
            "source_key",
            "revision",
            name="uq_engineering_context_source_refs_identity",
        ),
        Index(
            "ix_engineering_context_source_refs_source_key",
            "source_key",
        ),
        Index(
            "ix_engineering_context_source_refs_owner_id",
            "source_owner_id",
        ),
    )

    id = Column(Integer, primary_key=True)
    context_id = Column(
        Integer,
        ForeignKey(
            "engineering_contexts.id",
            name="fk_engineering_context_source_refs_context_id_contexts",
            ondelete="RESTRICT",
        ),
        nullable=False,
    )
    source_kind = Column(String(48), nullable=False)
    source_key = Column(String(255), nullable=False)
    source_owner_id = Column(
        Integer,
        ForeignKey(
            "users.id",
            name="fk_engineering_context_source_refs_owner_id_users",
            ondelete="RESTRICT",
        ),
        nullable=True,
    )
    revision = Column(
        String(128),
        nullable=False,
        default="unrevisioned",
        server_default="unrevisioned",
    )
    effective_at = Column(DateTime(timezone=True), nullable=True)
    observation_at = Column(DateTime(timezone=True), nullable=True)
    source_maturity = Column(String(128), nullable=True)
    confidentiality = Column(
        String(32),
        nullable=False,
        default=ContextConfidentiality.PROJECT.value,
        server_default=ContextConfidentiality.PROJECT.value,
    )
    applicability = Column(Text, nullable=False)
    limitations = Column(Text, nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    context = relationship(
        "EngineeringContext",
        back_populates="source_references",
    )
    source_owner = relationship("User", foreign_keys=[source_owner_id])
