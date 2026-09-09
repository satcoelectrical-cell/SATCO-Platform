"""Immutable PATCH-052 Context/Evidence declaration-binding associations."""

from sqlalchemy import BigInteger, CheckConstraint, Column, DateTime, ForeignKey
from sqlalchemy import ForeignKeyConstraint, Index, Integer, PrimaryKeyConstraint, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from app.core.database import Base


_DECLARATION_CHECK = (
    "project_configuration_revision >= 1 AND {version} >= 1 "
    "AND char_length(package_key) BETWEEN 1 AND 64 "
    "AND input_declaration_id ~ '^[a-z][a-z0-9_.-]*$'"
)


class EngineeringContextPackageInputBinding(Base):
    __tablename__ = "engineering_context_package_input_bindings"
    __table_args__ = (
        PrimaryKeyConstraint(
            "context_subject_reference_id", "context_version", "project_id",
            "project_configuration_revision", "package_key", "input_declaration_id",
            name="pk_engineering_context_package_input_bindings",
        ),
        ForeignKeyConstraint(
            ["project_id", "project_configuration_revision", "package_key"],
            ["project_package_configuration_selections.project_id",
             "project_package_configuration_selections.configuration_revision",
             "project_package_configuration_selections.package_key"],
            name="fk_context_input_binding_selection", ondelete="RESTRICT",
        ),
        CheckConstraint(
            _DECLARATION_CHECK.format(version="context_version"),
            name="ck_context_input_binding_values",
        ),
        Index(
            "ix_context_input_binding_readiness", "project_id",
            "project_configuration_revision", "package_key", "input_declaration_id",
            "context_subject_reference_id", "context_version",
        ),
    )

    context_subject_reference_id = Column(
        Integer,
        ForeignKey("engineering_context_subject_references.id",
                   name="fk_context_input_binding_subject", ondelete="RESTRICT"),
        nullable=False,
    )
    context_version = Column(Integer, nullable=False)
    project_id = Column(Integer, nullable=False)
    project_configuration_revision = Column(BigInteger, nullable=False)
    package_key = Column(String(64), nullable=False)
    input_declaration_id = Column(String(128), nullable=False)
    bound_by_id = Column(
        Integer,
        ForeignKey("users.id", name="fk_context_input_binding_actor", ondelete="RESTRICT"),
        nullable=False,
    )
    bound_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())


class EvidencePackageInputBinding(Base):
    __tablename__ = "evidence_package_input_bindings"
    __table_args__ = (
        PrimaryKeyConstraint(
            "evidence_id", "evidence_version", "project_id",
            "project_configuration_revision", "package_key", "input_declaration_id",
            name="pk_evidence_package_input_bindings",
        ),
        ForeignKeyConstraint(
            ["project_id", "project_configuration_revision", "package_key"],
            ["project_package_configuration_selections.project_id",
             "project_package_configuration_selections.configuration_revision",
             "project_package_configuration_selections.package_key"],
            name="fk_evidence_input_binding_selection", ondelete="RESTRICT",
        ),
        CheckConstraint(
            _DECLARATION_CHECK.format(version="evidence_version"),
            name="ck_evidence_input_binding_values",
        ),
        Index(
            "ix_evidence_input_binding_readiness", "project_id",
            "project_configuration_revision", "package_key", "input_declaration_id",
            "evidence_id", "evidence_version",
        ),
    )

    evidence_id = Column(
        UUID(as_uuid=True),
        ForeignKey("evidence.id", name="fk_evidence_input_binding_evidence",
                   ondelete="RESTRICT"),
        nullable=False,
    )
    evidence_version = Column(Integer, nullable=False)
    project_id = Column(Integer, nullable=False)
    project_configuration_revision = Column(BigInteger, nullable=False)
    package_key = Column(String(64), nullable=False)
    input_declaration_id = Column(String(128), nullable=False)
    bound_by_id = Column(
        Integer,
        ForeignKey("users.id", name="fk_evidence_input_binding_actor", ondelete="RESTRICT"),
        nullable=False,
    )
    bound_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
