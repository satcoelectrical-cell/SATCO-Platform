"""PATCH-054 Batch-1 persistence mappings for catalog and rights history."""

from __future__ import annotations

from uuid import uuid4

from sqlalchemy import BigInteger, Boolean, CheckConstraint, Column, DateTime, ForeignKey, Index, Integer, LargeBinary, String, Text, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID
from sqlalchemy.orm import deferred
from sqlalchemy.sql import func

from app.core.database import Base


class StandardIdentity(Base):
    __tablename__ = "standard_identities"
    __table_args__ = (
        CheckConstraint("catalog_scope IN ('global_trusted','organization_private')", name="ck_standard_identity_scope"),
        CheckConstraint("(catalog_scope='global_trusted' AND organization_id IS NULL) OR (catalog_scope='organization_private' AND organization_id IS NOT NULL)", name="ck_standard_identity_scope_org"),
        UniqueConstraint("catalog_scope", "organization_id", "issuer_key", "designation_key", name="uq_standard_identity_scope_key"),
        Index("ix_standard_identity_catalog", "catalog_scope", "organization_id", "issuer_key", "designation_key"),
    )
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    catalog_scope = Column(String(32), nullable=False)
    organization_id = Column(PGUUID(as_uuid=True), ForeignKey("organizations.id", ondelete="RESTRICT"))
    issuer_key = Column(String(240), nullable=False)
    issuer_display = Column(String(240), nullable=False)
    designation = Column(String(240), nullable=False)
    designation_key = Column(String(240), nullable=False)
    title = Column(String(500), nullable=False)
    language = Column(String(24))
    jurisdiction = Column(JSONB, nullable=False, server_default="'{}'::jsonb")
    normalization_version = Column(String(64), nullable=False)
    metadata_source_reference = Column(String(500), nullable=False)
    identity_digest = Column(String(64), nullable=False)
    predecessor_id = Column(PGUUID(as_uuid=True), ForeignKey("standard_identities.id", ondelete="RESTRICT"), unique=True)
    retired_from_new_selection = Column(Boolean, nullable=False, server_default="false")
    created_by = Column(Integer, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())


class StandardEdition(Base):
    __tablename__ = "standard_editions"
    __table_args__ = (
        UniqueConstraint("standard_identity_id", "edition_key", "edition_disambiguator", name="uq_standard_edition_identity_key"),
        Index("ix_standard_edition_identity", "standard_identity_id", "created_at"),
    )
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    standard_identity_id = Column(PGUUID(as_uuid=True), ForeignKey("standard_identities.id", ondelete="RESTRICT"), nullable=False)
    edition_designation = Column(String(240), nullable=False)
    edition_key = Column(String(240), nullable=False)
    edition_disambiguator = Column(String(120), nullable=False, server_default="")
    official_publication_identifier = Column(String(240))
    publication_date = Column(DateTime(timezone=True))
    effective_date = Column(DateTime(timezone=True))
    language = Column(String(24))
    jurisdiction = Column(JSONB, nullable=False, server_default="'{}'::jsonb")
    metadata_source_reference = Column(String(500), nullable=False)
    predecessor_id = Column(PGUUID(as_uuid=True), ForeignKey("standard_editions.id", ondelete="RESTRICT"), unique=True)
    edition_digest = Column(String(64), nullable=False)
    created_by = Column(Integer, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())


class StandardEditionStandingObservation(Base):
    __tablename__ = "standard_edition_standing_observations"
    __table_args__ = (
        UniqueConstraint("predecessor_id", name="uq_standard_standing_predecessor"),
        Index("uq_standard_standing_current", "standard_edition_id", unique=True, postgresql_where=text("is_current")),
        Index("ix_standard_standing_edition", "standard_edition_id", "observed_effective_at"),
    )
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    standard_edition_id = Column(PGUUID(as_uuid=True), ForeignKey("standard_editions.id", ondelete="RESTRICT"), nullable=False)
    standing = Column(String(16), nullable=False)
    superseded_by_edition_id = Column(PGUUID(as_uuid=True), ForeignKey("standard_editions.id", ondelete="RESTRICT"))
    observed_effective_at = Column(DateTime(timezone=True), nullable=False)
    source_reference = Column(String(500), nullable=False)
    source_digest = Column(String(64), nullable=False)
    actor_kind = Column(String(24), nullable=False, server_default="human")
    created_by = Column(Integer, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    predecessor_id = Column(PGUUID(as_uuid=True), ForeignKey("standard_edition_standing_observations.id", ondelete="RESTRICT"))
    observation_digest = Column(String(64), nullable=False)
    is_current = Column(Boolean, nullable=False, server_default="true")
    version = Column(BigInteger, nullable=False, server_default="1")
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())


class OrganizationRightsBinding(Base):
    __tablename__ = "standard_rights_bindings"
    __table_args__ = (
        UniqueConstraint("predecessor_id", name="uq_standard_rights_predecessor"),
        Index("uq_standard_rights_current", "organization_id", "standard_edition_id", "source_provider_id", unique=True, postgresql_where=text("is_current")),
        Index("ix_standard_rights_tuple", "organization_id", "standard_edition_id", "source_provider_id", "created_at"),
    )
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    organization_id = Column(PGUUID(as_uuid=True), ForeignKey("organizations.id", ondelete="RESTRICT"), nullable=False)
    standard_edition_id = Column(PGUUID(as_uuid=True), ForeignKey("standard_editions.id", ondelete="RESTRICT"), nullable=False)
    source_provider_id = Column(String(80), nullable=False)
    rights_basis = Column(String(40), nullable=False)
    rights_status = Column(String(16), nullable=False)
    allow_metadata_visibility = Column(Boolean, nullable=False, server_default="false")
    allow_content_storage = Column(Boolean, nullable=False, server_default="false")
    allow_indexing = Column(Boolean, nullable=False, server_default="false")
    allow_excerpt_display = Column(Boolean, nullable=False, server_default="false")
    allow_source_retrieval = Column(Boolean, nullable=False, server_default="false")
    allow_derived_retention = Column(Boolean, nullable=False, server_default="false")
    allow_derived_current_use = Column(Boolean, nullable=False, server_default="false")
    ai_processing_permission = Column(String(24), nullable=False, server_default="prohibited")
    approved_processor_policy_ids = Column(JSONB, nullable=False, server_default="'[]'::jsonb")
    effective_from = Column(DateTime(timezone=True), nullable=False)
    effective_until = Column(DateTime(timezone=True))
    rights_authority_reference = Column(String(500), nullable=False)
    rights_authority_digest = Column(String(64), nullable=False)
    predecessor_id = Column(PGUUID(as_uuid=True), ForeignKey("standard_rights_bindings.id", ondelete="RESTRICT"))
    reason_code = Column(String(80), nullable=False)
    reason = Column(String(500))
    is_current = Column(Boolean, nullable=False, server_default="true")
    version = Column(BigInteger, nullable=False, server_default="1")
    rights_digest = Column(String(64), nullable=False)
    created_by = Column(Integer, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())


class ProjectStandardApplicability(Base):
    """Append-only Project applicability decision history (PATCH-054 Batch 3)."""

    __tablename__ = "project_standard_applicability"
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    organization_id = Column(PGUUID(as_uuid=True), nullable=False)
    project_id = Column(Integer, nullable=False)
    standard_edition_id = Column(PGUUID(as_uuid=True))
    candidate_designation_key = Column(String(240))
    status = Column(String(32), nullable=False)
    applicability_role = Column(String(20), nullable=False)
    rationale_code = Column(String(80), nullable=False)
    rationale = Column(String(1000), nullable=False)
    origin_reference = Column(String(240), nullable=False)
    source_candidate_reference = Column(String(240))
    mandatory_source_kind = Column(String(32))
    mandatory_source_reference = Column(String(500))
    mandatory_source_digest = Column(String(64))
    expected_predecessor_revision = Column(BigInteger)
    predecessor_id = Column(PGUUID(as_uuid=True))
    successor_id = Column(PGUUID(as_uuid=True))
    is_current = Column(Boolean, nullable=False, server_default="true")
    revision = Column(BigInteger, nullable=False, server_default="1")
    applicability_digest = Column(String(64), nullable=False)
    declared_by = Column(Integer, nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())


class StandardSourceSnapshot(Base):
    __tablename__ = "standard_source_snapshots"
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    organization_id = Column(PGUUID(as_uuid=True), nullable=False)
    project_id = Column(Integer, nullable=False)
    standard_identity_id = Column(PGUUID(as_uuid=True), nullable=False)
    standard_edition_id = Column(PGUUID(as_uuid=True), nullable=False)
    source_provider_id = Column(String(80), nullable=False)
    adapter_policy_id = Column(String(80), nullable=False)
    adapter_policy_version = Column(String(40), nullable=False)
    source_location = Column(String(500), nullable=False)
    availability_status = Column(String(32), nullable=False)
    request_purpose = Column(String(80), nullable=False)
    correlation_id = Column(PGUUID(as_uuid=True), nullable=False)
    object_key = Column(String(500)); object_version = Column(String(240))
    # This column is deliberately deferred: ordinary runtime reads must use the
    # separately granted resolver, never a SELECT projection of ciphertext.
    provider_handle_ciphertext = deferred(Column("provider_handle_ciphertext", LargeBinary, nullable=True))
    provider_handle_key_version = Column(String(40)); provider_version_digest = Column(String(64))
    content_sha256 = Column(String(64)); byte_count = Column(Integer); media_type = Column(String(120))
    rights_binding_id = Column(PGUUID(as_uuid=True), nullable=False); rights_binding_version = Column(BigInteger, nullable=False)
    rights_digest = Column(String(64), nullable=False); evaluated_capabilities = Column(JSONB, nullable=False)
    standing_observation_id = Column(PGUUID(as_uuid=True), nullable=False)
    standing_observation_digest = Column(String(64), nullable=False)
    source_metadata_digest = Column(String(64), nullable=False)
    integrity_verified = Column(Boolean, nullable=False); integrity_verified_at = Column(DateTime(timezone=True), nullable=False)
    snapshot_digest = Column(String(64), nullable=False)
    retrieved_at = Column(DateTime(timezone=True), nullable=False)
    retrieved_by = Column(Integer, nullable=False); created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())


class StandardKnowledgeAssertion(Base):
    __tablename__ = "standard_knowledge_assertions"
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    organization_id = Column(PGUUID(as_uuid=True), nullable=False); project_id = Column(Integer, nullable=False)
    standard_edition_id = Column(PGUUID(as_uuid=True), nullable=False); source_snapshot_id = Column(PGUUID(as_uuid=True), nullable=False)
    source_location = Column(String(500), nullable=False); source_content_digest = Column(String(64), nullable=False)
    assertion_kind = Column(String(32), nullable=False); canonical_representation = Column(JSONB, nullable=False)
    assertion_origin = Column(String(20), nullable=False); extraction_method_id = Column(String(80), nullable=False)
    extraction_method_version = Column(String(40), nullable=False); extraction_method_digest = Column(String(64), nullable=False)
    intelligence_run_id = Column(PGUUID(as_uuid=True))
    assertion_digest = Column(String(64), nullable=False); verification_status = Column(String(24), nullable=False, server_default="unverified")
    current_verification_event_id = Column(PGUUID(as_uuid=True))
    rights_binding_id = Column(PGUUID(as_uuid=True), nullable=False); rights_binding_version = Column(BigInteger, nullable=False)
    rights_digest = Column(String(64), nullable=False); retained_derived_use_eligible = Column(Boolean, nullable=False)
    evaluated_rights_revision = Column(BigInteger, nullable=False); predecessor_assertion_id = Column(PGUUID(as_uuid=True)); successor_assertion_id = Column(PGUUID(as_uuid=True))
    version = Column(BigInteger, nullable=False, server_default="1"); created_by = Column(Integer, nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())


class StandardAssertionVerificationEvent(Base):
    __tablename__ = "standard_assertion_verification_events"
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    assertion_id = Column(PGUUID(as_uuid=True), nullable=False)
    event_kind = Column(String(32), nullable=False)
    status = Column(String(24), nullable=False)
    reason = Column(String(1000))
    source_rights_binding_id = Column(PGUUID(as_uuid=True), nullable=False)
    source_rights_binding_version = Column(BigInteger, nullable=False)
    source_rights_digest = Column(String(64), nullable=False)
    assertion_digest = Column(String(64), nullable=False)
    basis_human_verification_event_id = Column(PGUUID(as_uuid=True))
    actor_kind = Column(String(24), nullable=False)
    verified_by = Column(Integer)
    verified_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())


class StandardsIdempotency(Base):
    __tablename__ = "standards_idempotency"
    __table_args__ = (UniqueConstraint("organization_id", "actor_id", "operation", "idempotency_key", name="uq_standards_idempotency_key"),)
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    organization_id = Column(PGUUID(as_uuid=True), ForeignKey("organizations.id", ondelete="RESTRICT"), nullable=False)
    actor_id = Column(Integer, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    operation = Column(String(80), nullable=False)
    idempotency_key = Column(String(160), nullable=False)
    request_digest = Column(String(64), nullable=False)
    state = Column(String(16), nullable=False, server_default="pending")
    resource_type = Column(String(80))
    resource_id = Column(PGUUID(as_uuid=True))
    response_status = Column(Integer)
    response_body = Column(JSONB)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    completed_at = Column(DateTime(timezone=True))
    expires_at = Column(DateTime(timezone=True), nullable=False)
    version = Column(BigInteger, nullable=False, server_default="1")


class StandardsOutbox(Base):
    __tablename__ = "standards_outbox"
    __table_args__ = (UniqueConstraint("aggregate_type", "aggregate_id", "event_id", "event_version", name="uq_standards_outbox_event"),)
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    organization_id = Column(PGUUID(as_uuid=True), ForeignKey("organizations.id", ondelete="RESTRICT"))
    aggregate_type = Column(String(80), nullable=False)
    aggregate_id = Column(PGUUID(as_uuid=True), nullable=False)
    event_id = Column(String(80), nullable=False)
    event_version = Column(Integer, nullable=False, server_default="1")
    payload = Column(JSONB, nullable=False)
    occurred_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    published_at = Column(DateTime(timezone=True))
