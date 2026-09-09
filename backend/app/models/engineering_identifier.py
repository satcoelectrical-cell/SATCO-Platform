"""ADR-025 governed Engineering Identifier aggregate persistence."""

from __future__ import annotations

from datetime import datetime
import re
import unicodedata
from uuid import UUID, uuid4

from sqlalchemy import CheckConstraint, Column, DateTime, ForeignKey, ForeignKeyConstraint
from sqlalchemy import BigInteger, Index, Integer, String, text
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID
from sqlalchemy.orm import validates
from sqlalchemy.sql import func

from app.core.database import Base
from app.enums.engineering_identifier import NORMALIZATION_ALGORITHM_VERSION
from app.enums.engineering_knowledge import EngineeringIdentifierKind


def normalize_engineering_identifier(value: str) -> str:
    """Apply the exact server-owned ADR-025 normalization algorithm."""

    if not isinstance(value, str) or not 1 <= len(value) <= 128:
        raise ValueError("display_value must contain 1..128 Unicode scalar values")
    if any(unicodedata.category(character) in {"Cc", "Cn"} for character in value):
        raise ValueError("display_value contains a control or unassigned code point")
    normalized = unicodedata.normalize("NFKC", value)
    normalized = re.sub(r"\s+", " ", normalized.strip()).casefold()
    if not 1 <= len(normalized) <= 128:
        raise ValueError("normalized_value must contain 1..128 Unicode scalar values")
    if any(unicodedata.category(character) in {"Cc", "Cn"} for character in normalized):
        raise ValueError("normalized_value contains a control or unassigned code point")
    return normalized


class EngineeringIdentifier(Base):
    __tablename__ = "engineering_identifiers"
    __table_args__ = (
        CheckConstraint(
            "identifier_kind IN ('tag_number','equipment_number','loop_number','cable_number',"
            "'panel_number','feeder_number','system_identifier','subsystem_identifier',"
            "'vendor_reference','manufacturer_model_reference','controlled_external_key')",
            name="ck_engineering_identifier_kind",
        ),
        CheckConstraint("char_length(display_value) BETWEEN 1 AND 128", name="ck_engineering_identifier_display"),
        CheckConstraint("char_length(normalized_value) BETWEEN 1 AND 128", name="ck_engineering_identifier_normalized"),
        CheckConstraint(
            "normalization_algorithm_version = 'satco_identifier_nfkc_casefold_v1'",
            name="ck_engineering_identifier_normalizer",
        ),
        CheckConstraint(
            "issuing_scope_kind IN ('project','workspace','external_authority')",
            name="ck_engineering_identifier_scope_kind",
        ),
        CheckConstraint("char_length(issuing_scope_value) BETWEEN 1 AND 128", name="ck_engineering_identifier_scope_value"),
        CheckConstraint("lifecycle IN ('current','superseded','withdrawn')", name="ck_engineering_identifier_lifecycle"),
        CheckConstraint(
            "authority_standing IN ('draft','proposed','reviewed','approved','disputed','rejected')",
            name="ck_engineering_identifier_authority",
        ),
        CheckConstraint("primary_role IN ('primary','alternate')", name="ck_engineering_identifier_primary_role"),
        CheckConstraint("version >= 1", name="ck_engineering_identifier_version"),
        CheckConstraint("updated_at >= created_at", name="ck_engineering_identifier_time_order"),
        CheckConstraint("predecessor_identifier_id IS NULL OR predecessor_identifier_id <> identifier_id", name="ck_engineering_identifier_predecessor_self"),
        CheckConstraint("successor_identifier_id IS NULL OR successor_identifier_id <> identifier_id", name="ck_engineering_identifier_successor_self"),
        CheckConstraint(
            "(origin_package_key IS NULL AND origin_project_configuration_revision IS NULL AND origin_declaration_id IS NULL) OR "
            "(origin_package_key IS NOT NULL AND origin_project_configuration_revision IS NOT NULL AND origin_declaration_id IS NOT NULL)",
            name="ck_engineering_identifier_origin_all_or_none",
        ),
        ForeignKeyConstraint(
            ["project_id", "origin_project_configuration_revision", "origin_package_key"],
            ["project_package_configuration_selections.project_id", "project_package_configuration_selections.configuration_revision", "project_package_configuration_selections.package_key"],
            name="fk_engineering_identifier_origin_selection",
            ondelete="RESTRICT",
        ),
        Index(
            "uq_engineering_identifier_current_value",
            "organization_id", "project_id", "issuing_scope_kind", "issuing_scope_value",
            "identifier_kind", "normalized_value", unique=True,
            postgresql_where=text("lifecycle = 'current'"),
        ),
        Index(
            "uq_engineering_identifier_current_primary",
            "engineering_object_id", unique=True,
            postgresql_where=text("lifecycle = 'current' AND primary_role = 'primary'"),
        ),
        Index("ix_engineering_identifier_current_set", "engineering_object_id", "lifecycle", "primary_role"),
        Index("ix_engineering_identifier_scope_history", "organization_id", "project_id", "workspace_id", text("created_at DESC"), text("identifier_id DESC")),
    )

    identifier_id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    engineering_object_id = Column(PGUUID(as_uuid=True), ForeignKey("engineering_objects.id", ondelete="RESTRICT"), nullable=False)
    organization_id = Column(PGUUID(as_uuid=True), ForeignKey("organizations.id", ondelete="RESTRICT"), nullable=False)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="RESTRICT"), nullable=False)
    workspace_id = Column(Integer, ForeignKey("engineering_workspaces.id", ondelete="RESTRICT"), nullable=False)
    identifier_kind = Column(String(64), nullable=False)
    display_value = Column(String(128), nullable=False)
    normalized_value = Column(String(128), nullable=False)
    normalization_algorithm_version = Column(String(64), nullable=False, default=NORMALIZATION_ALGORITHM_VERSION, server_default=NORMALIZATION_ALGORITHM_VERSION)
    issuing_scope_kind = Column(String(32), nullable=False)
    issuing_scope_value = Column(String(128), nullable=False)
    lifecycle = Column(String(16), nullable=False, default="current", server_default="current")
    authority_standing = Column(String(16), nullable=False, default="draft", server_default="draft")
    primary_role = Column(String(16), nullable=False, default="alternate", server_default="alternate")
    evidence_references = Column(JSONB, nullable=False, default=list, server_default=text("'[]'::jsonb"))
    version = Column(Integer, nullable=False, default=1, server_default="1")
    predecessor_identifier_id = Column(PGUUID(as_uuid=True), ForeignKey("engineering_identifiers.identifier_id", ondelete="RESTRICT"), unique=True)
    successor_identifier_id = Column(PGUUID(as_uuid=True), ForeignKey("engineering_identifiers.identifier_id", ondelete="RESTRICT"), unique=True)
    creator_id = Column(Integer, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    steward_id = Column(Integer, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    reviewer_id = Column(Integer, ForeignKey("users.id", ondelete="RESTRICT"))
    approver_id = Column(Integer, ForeignKey("users.id", ondelete="RESTRICT"))
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    origin_package_key = Column(String(64))
    origin_project_configuration_revision = Column(BigInteger)
    origin_declaration_id = Column(String(128))

    def __init__(self, **values):
        values.setdefault("identifier_id", uuid4())
        values.setdefault("normalized_value", normalize_engineering_identifier(values.get("display_value")))
        values.setdefault("normalization_algorithm_version", NORMALIZATION_ALGORITHM_VERSION)
        values.setdefault("lifecycle", "current")
        values.setdefault("authority_standing", "draft")
        values.setdefault("primary_role", "alternate")
        values.setdefault("evidence_references", [])
        values.setdefault("version", 1)
        super().__init__(**values)

    @validates("display_value")
    def _validate_display(self, _key: str, value: str) -> str:
        normalize_engineering_identifier(value)
        current = self.__dict__.get("display_value")
        if current is not None and current != value:
            raise ValueError("display_value is immutable; create a successor")
        return value

    @validates("evidence_references")
    def _validate_evidence(self, _key: str, value):
        values = [str(UUID(str(item))) for item in value]
        if len(values) > 8 or len(values) != len(set(values)) or values != sorted(values):
            raise ValueError("evidence_references must contain 0..8 unique lexical UUIDs")
        return values

    @property
    def id(self) -> UUID:
        return self.identifier_id
