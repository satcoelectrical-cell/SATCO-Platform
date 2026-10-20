"""PATCH-059 commercial entitlement persistence."""
from __future__ import annotations
import uuid
from sqlalchemy import BigInteger, CheckConstraint, Column, DateTime, ForeignKey, ForeignKeyConstraint, Index, Integer, String, func
from sqlalchemy.dialects.postgresql import JSONB, UUID as PostgreSQLUUID
from app.core.database import Base

class CommercialEntitlementState(Base):
    __tablename__ = "commercial_entitlement_states"
    __table_args__ = (
        CheckConstraint("accepted_revision >= 1", name="ck_commercial_entitlement_state_revision"),
        CheckConstraint("seat_capacity >= 1", name="ck_commercial_entitlement_state_capacity"),
        CheckConstraint("baseline_release_sequence >= 1 AND max_release_sequence >= baseline_release_sequence", name="ck_commercial_entitlement_state_release_range"),
        CheckConstraint("issued_at <= not_before AND not_before <= valid_until AND valid_until <= grace_until", name="ck_commercial_entitlement_state_time_order"),
        CheckConstraint("char_length(canonical_payload_digest) = 64", name="ck_commercial_entitlement_state_digest"),
        Index("ix_commercial_entitlement_state_entitlement", "entitlement_id", "accepted_revision"),
    )
    organization_id = Column(PostgreSQLUUID(as_uuid=True), ForeignKey("organizations.id", ondelete="RESTRICT"), primary_key=True)
    deployment_id = Column(String(200), primary_key=True)
    entitlement_id = Column(PostgreSQLUUID(as_uuid=True), nullable=False)
    accepted_revision = Column(BigInteger, nullable=False)
    canonical_payload_digest = Column(String(64), nullable=False)
    key_id = Column(String(120), nullable=False)
    issuer = Column(String(200), nullable=False)
    issued_at = Column(DateTime(timezone=True), nullable=False)
    not_before = Column(DateTime(timezone=True), nullable=False)
    valid_until = Column(DateTime(timezone=True), nullable=False)
    grace_until = Column(DateTime(timezone=True), nullable=False)
    support_until = Column(DateTime(timezone=True))
    package_keys = Column(JSONB, nullable=False)
    seat_capacity = Column(Integer, nullable=False)
    baseline_release_sequence = Column(BigInteger, nullable=False)
    max_release_sequence = Column(BigInteger, nullable=False)
    last_trusted_time = Column(DateTime(timezone=True), nullable=False)
    accepted_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    accepted_by_user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"))
    time_untrusted_at = Column(DateTime(timezone=True))
    version = Column(Integer, nullable=False, default=1, server_default="1")

class CommercialEntitlementActivation(Base):
    __tablename__ = "commercial_entitlement_activations"
    __table_args__ = (
        CheckConstraint("revision >= 1", name="ck_commercial_entitlement_activation_revision"),
        CheckConstraint("char_length(canonical_payload_digest) = 64", name="ck_commercial_entitlement_activation_digest"),
        Index("ix_commercial_entitlement_activation_org_time", "organization_id", "deployment_id", "accepted_at"),
    )
    id = Column(PostgreSQLUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(PostgreSQLUUID(as_uuid=True), ForeignKey("organizations.id", ondelete="RESTRICT"), nullable=False)
    deployment_id = Column(String(200), nullable=False)
    entitlement_id = Column(PostgreSQLUUID(as_uuid=True), nullable=False)
    revision = Column(BigInteger, nullable=False)
    canonical_payload_digest = Column(String(64), nullable=False)
    key_id = Column(String(120), nullable=False)
    outcome = Column(String(32), nullable=False)
    reason_code = Column(String(80))
    accepted_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    actor_user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"))
    correlation_id = Column(String(120))

class CommercialSeatAssignment(Base):
    __tablename__ = "commercial_seat_assignments"
    __table_args__ = (
        ForeignKeyConstraint(["user_id", "organization_id"], ["user_organization_memberships.user_id", "user_organization_memberships.organization_id"], name="fk_commercial_seat_membership", ondelete="RESTRICT"),
        CheckConstraint("state IN ('ASSIGNED','RESERVED','RETAINED')", name="ck_commercial_seat_state"),
        Index("ix_commercial_seat_org_state", "organization_id", "deployment_id", "state"),
    )
    organization_id = Column(PostgreSQLUUID(as_uuid=True), primary_key=True)
    deployment_id = Column(String(200), primary_key=True)
    user_id = Column(Integer, primary_key=True)
    state = Column(String(16), nullable=False)
    assigned_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    assigned_by_user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"))
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
    updated_by_user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"))


class CommercialPackageConfigurationProof(Base):
    """Durable current enablement-epoch proof used only for GRACE execution continuity."""

    __tablename__ = "commercial_package_configuration_proofs"
    __table_args__ = (
        CheckConstraint(
            "configured_before <= recorded_at",
            name="ck_commercial_package_configuration_proof_time_order",
        ),
        Index(
            "ix_commercial_package_configuration_proof_org_deployment",
            "organization_id",
            "deployment_id",
        ),
    )

    organization_id = Column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="RESTRICT"),
        primary_key=True,
    )
    deployment_id = Column(String(200), primary_key=True)
    package_key = Column(String(64), primary_key=True)
    configured_before = Column(DateTime(timezone=True), nullable=False)
    recorded_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
