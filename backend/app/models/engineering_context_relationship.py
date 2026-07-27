from sqlalchemy import Boolean
from sqlalchemy import CheckConstraint
from sqlalchemy import Column
from sqlalchemy import DateTime
from sqlalchemy import ForeignKey
from sqlalchemy import Index
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy import Text
from sqlalchemy import UniqueConstraint
from sqlalchemy import text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base
from app.enums import CommitmentCriticality
from app.enums import CommitmentProviderKind
from app.enums import ContextConfidentiality
from app.enums import ContextRelationshipMeaning
from app.enums import InterfaceCommitmentState
from app.enums import RelationshipEndpointKind
from app.enums import RelationshipLifecycle


def _values(enum_type) -> str:
    return ", ".join(f"'{item.value}'" for item in enum_type)


class EngineeringContextRelationship(Base):
    __tablename__ = "engineering_context_relationships"
    __table_args__ = (
        CheckConstraint(
            f"meaning IN ({_values(ContextRelationshipMeaning)})",
            name="ck_context_relationships_meaning",
        ),
        CheckConstraint(
            f"lifecycle IN ({_values(RelationshipLifecycle)})",
            name="ck_context_relationships_lifecycle",
        ),
        CheckConstraint(
            f"source_kind IN ({_values(RelationshipEndpointKind)})",
            name="ck_context_relationships_source_kind",
        ),
        CheckConstraint(
            f"target_kind IN ({_values(RelationshipEndpointKind)})",
            name="ck_context_relationships_target_kind",
        ),
        CheckConstraint(
            "num_nonnulls(source_context_id, source_project_id, "
            "source_workspace_id, source_discipline, source_external_key) = 1",
            name="ck_context_relationships_source_target",
        ),
        CheckConstraint(
            "(source_kind = 'context' AND source_context_id IS NOT NULL) OR "
            "(source_kind = 'project' AND source_project_id IS NOT NULL) OR "
            "(source_kind = 'workspace' AND source_workspace_id IS NOT NULL) "
            "OR (source_kind = 'discipline' "
            "AND source_discipline IS NOT NULL) OR "
            "(source_kind = 'external_source' "
            "AND source_external_key IS NOT NULL)",
            name="ck_context_relationships_source_kind_target",
        ),
        CheckConstraint(
            "num_nonnulls(target_context_id, target_project_id, "
            "target_workspace_id, target_discipline, target_external_key) = 1",
            name="ck_context_relationships_target_target",
        ),
        CheckConstraint(
            "(target_kind = 'context' AND target_context_id IS NOT NULL) OR "
            "(target_kind = 'project' AND target_project_id IS NOT NULL) OR "
            "(target_kind = 'workspace' AND target_workspace_id IS NOT NULL) "
            "OR (target_kind = 'discipline' "
            "AND target_discipline IS NOT NULL) OR "
            "(target_kind = 'external_source' "
            "AND target_external_key IS NOT NULL)",
            name="ck_context_relationships_target_kind_target",
        ),
        CheckConstraint(
            "source_kind <> target_kind OR "
            "COALESCE(source_context_id, source_project_id, "
            "source_workspace_id, -1) <> "
            "COALESCE(target_context_id, target_project_id, "
            "target_workspace_id, -1) OR "
            "COALESCE(source_discipline, '') <> "
            "COALESCE(target_discipline, '') OR "
            "COALESCE(source_external_key, '') <> "
            "COALESCE(target_external_key, '')",
            name="ck_context_relationships_no_self_reference",
        ),
        CheckConstraint(
            "version >= 1",
            name="ck_context_relationships_version",
        ),
        CheckConstraint(
            "(lifecycle = 'current' AND withdrawn_at IS NULL "
            "AND withdrawal_reason IS NULL) OR "
            "(lifecycle = 'withdrawn' AND withdrawn_at IS NOT NULL "
            "AND withdrawal_reason IS NOT NULL)",
            name="ck_context_relationships_withdrawal",
        ),
        UniqueConstraint(
            "relationship_key",
            name="uq_context_relationships_key",
        ),
        Index(
            "ix_context_relationships_project_lifecycle",
            "project_id",
            "lifecycle",
        ),
        Index(
            "ix_context_relationships_source_workspace",
            "source_workspace_id",
        ),
        Index(
            "ix_context_relationships_target_workspace",
            "target_workspace_id",
        ),
        Index(
            "uq_context_relationships_governed_current",
            "project_id",
            "meaning",
            "purpose",
            "source_kind",
            "source_context_id",
            "source_project_id",
            "source_workspace_id",
            "source_discipline",
            "source_external_key",
            "target_kind",
            "target_context_id",
            "target_project_id",
            "target_workspace_id",
            "target_discipline",
            "target_external_key",
            unique=True,
            postgresql_where=text("lifecycle = 'current'"),
            postgresql_nulls_not_distinct=True,
        ),
    )

    id = Column(Integer, primary_key=True)
    relationship_key = Column(String(36), nullable=False)
    project_id = Column(
        Integer,
        ForeignKey("projects.id", ondelete="RESTRICT"),
        nullable=False,
    )
    meaning = Column(String(32), nullable=False)
    purpose = Column(String(500), nullable=False)
    applicability = Column(Text, nullable=True)
    source_role = Column(String(64), nullable=False)
    target_role = Column(String(64), nullable=False)
    source_kind = Column(String(32), nullable=False)
    source_context_id = Column(
        Integer,
        ForeignKey("engineering_contexts.id", ondelete="RESTRICT"),
    )
    source_project_id = Column(
        Integer,
        ForeignKey("projects.id", ondelete="RESTRICT"),
    )
    source_workspace_id = Column(
        Integer,
        ForeignKey("engineering_workspaces.id", ondelete="RESTRICT"),
    )
    source_discipline = Column(String(32))
    source_external_key = Column(String(255))
    target_kind = Column(String(32), nullable=False)
    target_context_id = Column(
        Integer,
        ForeignKey("engineering_contexts.id", ondelete="RESTRICT"),
    )
    target_project_id = Column(
        Integer,
        ForeignKey("projects.id", ondelete="RESTRICT"),
    )
    target_workspace_id = Column(
        Integer,
        ForeignKey("engineering_workspaces.id", ondelete="RESTRICT"),
    )
    target_discipline = Column(String(32))
    target_external_key = Column(String(255))
    steward_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )
    created_by_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )
    lifecycle = Column(
        String(16),
        nullable=False,
        default=RelationshipLifecycle.CURRENT.value,
        server_default=RelationshipLifecycle.CURRENT.value,
    )
    version = Column(Integer, nullable=False, default=1, server_default="1")
    withdrawal_reason = Column(Text)
    withdrawn_at = Column(DateTime(timezone=True))
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

    project = relationship("Project", foreign_keys=[project_id])
    source_context = relationship(
        "EngineeringContext",
        foreign_keys=[source_context_id],
    )
    target_context = relationship(
        "EngineeringContext",
        foreign_keys=[target_context_id],
    )
    source_workspace = relationship(
        "EngineeringWorkspace",
        foreign_keys=[source_workspace_id],
    )
    target_workspace = relationship(
        "EngineeringWorkspace",
        foreign_keys=[target_workspace_id],
    )
    steward = relationship("User", foreign_keys=[steward_id])
    created_by = relationship("User", foreign_keys=[created_by_id])
    commitment = relationship(
        "InterfaceCommitment",
        back_populates="relationship_record",
        uselist=False,
    )


class InterfaceCommitment(Base):
    __tablename__ = "interface_commitments"
    __table_args__ = (
        UniqueConstraint(
            "commitment_key",
            name="uq_interface_commitments_key",
        ),
        UniqueConstraint(
            "relationship_id",
            name="uq_interface_commitments_relationship",
        ),
        CheckConstraint(
            f"provider_kind IN ({_values(CommitmentProviderKind)})",
            name="ck_interface_commitments_provider_kind",
        ),
        CheckConstraint(
            "num_nonnulls(provider_user_id, provider_workspace_id, "
            "provider_external_key) = 1",
            name="ck_interface_commitments_provider_target",
        ),
        CheckConstraint(
            "(provider_kind = 'user' AND provider_user_id IS NOT NULL) OR "
            "(provider_kind = 'workspace' "
            "AND provider_workspace_id IS NOT NULL) OR "
            "(provider_kind = 'external_source' "
            "AND provider_external_key IS NOT NULL)",
            name="ck_interface_commitments_provider_kind_target",
        ),
        CheckConstraint(
            f"state IN ({_values(InterfaceCommitmentState)})",
            name="ck_interface_commitments_state",
        ),
        CheckConstraint(
            f"criticality IN ({_values(CommitmentCriticality)})",
            name="ck_interface_commitments_criticality",
        ),
        CheckConstraint(
            f"confidentiality IN ({_values(ContextConfidentiality)})",
            name="ck_interface_commitments_confidentiality",
        ),
        CheckConstraint(
            "version >= 1",
            name="ck_interface_commitments_version",
        ),
        CheckConstraint(
            "(current_use = true AND withdrawn_at IS NULL "
            "AND withdrawal_reason IS NULL) OR "
            "(current_use = false AND withdrawn_at IS NOT NULL "
            "AND withdrawal_reason IS NOT NULL)",
            name="ck_interface_commitments_withdrawal",
        ),
        CheckConstraint(
            "(reassessment_needed = false AND reassessment_reason IS NULL "
            "AND reassessment_trigger IS NULL) OR "
            "(reassessment_needed = true AND reassessment_reason IS NOT NULL "
            "AND reassessment_trigger IS NOT NULL)",
            name="ck_interface_commitments_reassessment",
        ),
        CheckConstraint(
            "state <> 'fulfilled_for_stated_use' "
            "OR (supplied_source_key IS NOT NULL "
            "AND supplied_revision IS NOT NULL "
            "AND fulfilment_use IS NOT NULL)",
            name="ck_interface_commitments_fulfilment",
        ),
        CheckConstraint(
            "state <> 'fulfilled_for_stated_use' "
            "OR external_review_required = false "
            "OR external_review_evidence IS NOT NULL",
            name="ck_interface_commitments_review_evidence",
        ),
        CheckConstraint(
            "btrim(required_information) <> '' "
            "AND btrim(intended_use) <> '' "
            "AND btrim(completeness_expectation) <> '' "
            "AND btrim(expected_source_basis) <> '' "
            "AND btrim(stage_or_due_condition) <> ''",
            name="ck_interface_commitments_required_contract",
        ),
        CheckConstraint(
            "provider_workspace_id IS NULL "
            "OR provider_workspace_id <> consumer_workspace_id",
            name="ck_interface_commitments_distinct_workspaces",
        ),
        Index(
            "ix_interface_commitments_project_state",
            "project_id",
            "state",
        ),
        Index(
            "ix_interface_commitments_consumer_workspace",
            "consumer_workspace_id",
        ),
        Index(
            "ix_interface_commitments_provider_workspace",
            "provider_workspace_id",
        ),
    )

    id = Column(Integer, primary_key=True)
    commitment_key = Column(String(36), nullable=False)
    relationship_id = Column(
        Integer,
        ForeignKey(
            "engineering_context_relationships.id",
            ondelete="RESTRICT",
        ),
        nullable=False,
    )
    project_id = Column(
        Integer,
        ForeignKey("projects.id", ondelete="RESTRICT"),
        nullable=False,
    )
    provider_kind = Column(String(32), nullable=False)
    provider_user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="RESTRICT"),
    )
    provider_workspace_id = Column(
        Integer,
        ForeignKey("engineering_workspaces.id", ondelete="RESTRICT"),
    )
    provider_external_key = Column(String(255))
    consumer_workspace_id = Column(
        Integer,
        ForeignKey("engineering_workspaces.id", ondelete="RESTRICT"),
        nullable=False,
    )
    required_information = Column(Text, nullable=False)
    intended_use = Column(Text, nullable=False)
    completeness_expectation = Column(Text, nullable=False)
    expected_source_basis = Column(Text, nullable=False)
    stage_or_due_condition = Column(Text, nullable=False)
    criticality = Column(String(16), nullable=False)
    confidentiality = Column(String(32), nullable=False)
    steward_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )
    consumer_reviewer_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )
    state = Column(
        String(40),
        nullable=False,
        default=InterfaceCommitmentState.IDENTIFIED.value,
        server_default=InterfaceCommitmentState.IDENTIFIED.value,
    )
    supplied_source_key = Column(String(255))
    supplied_revision = Column(String(128))
    fulfilment_use = Column(Text)
    external_review_evidence = Column(String(255))
    external_review_required = Column(
        Boolean,
        nullable=False,
        default=False,
        server_default="false",
    )
    successor_commitment_id = Column(
        Integer,
        ForeignKey("interface_commitments.id", ondelete="RESTRICT"),
    )
    current_use = Column(
        Boolean,
        nullable=False,
        default=True,
        server_default="true",
    )
    withdrawal_reason = Column(Text)
    withdrawn_at = Column(DateTime(timezone=True))
    reassessment_needed = Column(
        Boolean,
        nullable=False,
        default=False,
        server_default="false",
    )
    reassessment_trigger = Column(String(255))
    reassessment_reason = Column(Text)
    version = Column(Integer, nullable=False, default=1, server_default="1")
    created_by_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )
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

    relationship_record = relationship(
        "EngineeringContextRelationship",
        back_populates="commitment",
    )
    project = relationship("Project", foreign_keys=[project_id])
    provider_user = relationship("User", foreign_keys=[provider_user_id])
    provider_workspace = relationship(
        "EngineeringWorkspace",
        foreign_keys=[provider_workspace_id],
    )
    consumer_workspace = relationship(
        "EngineeringWorkspace",
        foreign_keys=[consumer_workspace_id],
    )
    steward = relationship("User", foreign_keys=[steward_id])
    consumer_reviewer = relationship(
        "User",
        foreign_keys=[consumer_reviewer_id],
    )
    created_by = relationship("User", foreign_keys=[created_by_id])
    successor = relationship(
        "InterfaceCommitment",
        remote_side=[id],
        foreign_keys=[successor_commitment_id],
    )
