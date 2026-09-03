"""Batch-2 derived Registry projection and package-configuration persistence."""

from uuid import uuid4

from sqlalchemy import BigInteger, Boolean, CheckConstraint, Column, DateTime, ForeignKey, ForeignKeyConstraint, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID

from app.core.database import Base


class RegistryRelease(Base):
    __tablename__ = "discipline_package_registry_releases"
    registry_digest = Column(String(64), primary_key=True)
    release_id = Column(String(64), unique=True, nullable=False)
    core_contract_version = Column(Integer, nullable=False)
    is_current = Column(Boolean, nullable=False, default=False)
    manifest_json = Column(JSONB, nullable=False)
    __table_args__ = (CheckConstraint("length(registry_digest)=64", name="ck_dp_release_digest"), Index("uq_dp_release_current", "is_current", unique=True, postgresql_where="is_current"))


class PackageDescriptor(Base):
    __tablename__ = "discipline_package_descriptors"
    package_key = Column(String(64), primary_key=True)
    package_version = Column(String(32), primary_key=True)
    descriptor_digest = Column(String(64), unique=True, nullable=False)
    primary_discipline_id = Column(String(64), nullable=False)
    adapter_id = Column(String(128), nullable=False)
    descriptor_json = Column(JSONB, nullable=False)


class RegistryMembership(Base):
    __tablename__ = "discipline_package_registry_memberships"
    registry_digest = Column(String(64), ForeignKey("discipline_package_registry_releases.registry_digest", ondelete="RESTRICT"), primary_key=True)
    package_key = Column(String(64), primary_key=True)
    package_version = Column(String(32), primary_key=True)
    standing = Column(String(40), nullable=False)
    __table_args__ = (ForeignKeyConstraint(["package_key", "package_version"], ["discipline_package_descriptors.package_key", "discipline_package_descriptors.package_version"], ondelete="RESTRICT"), CheckConstraint("standing IN ('executable_supported','historical_read_only')", name="ck_dp_membership_standing"), Index("ix_dp_membership_release_standing", "registry_digest", "standing", "package_key", "package_version"))


class CompatibilityProfile(Base):
    __tablename__ = "discipline_package_compatibility_profiles"
    profile_id = Column(String(64), primary_key=True)
    profile_digest = Column(String(64), primary_key=True)
    profile_json = Column(JSONB, nullable=False)


class RegistryProfileMembership(Base):
    __tablename__ = "discipline_package_registry_profile_memberships"
    registry_digest = Column(String(64), ForeignKey("discipline_package_registry_releases.registry_digest", ondelete="RESTRICT"), primary_key=True)
    profile_id = Column(String(64), primary_key=True)
    profile_digest = Column(String(64), nullable=False)
    __table_args__ = (ForeignKeyConstraint(["profile_id", "profile_digest"], ["discipline_package_compatibility_profiles.profile_id", "discipline_package_compatibility_profiles.profile_digest"], ondelete="RESTRICT"), UniqueConstraint("registry_digest", "profile_id", "profile_digest", name="uq_dp_release_profile_digest"), Index("ix_dp_profile_release", "profile_id", "profile_digest", "registry_digest"))


class CompatibilityMember(Base):
    __tablename__ = "discipline_package_compatibility_members"
    profile_id = Column(String(64), primary_key=True)
    profile_digest = Column(String(64), primary_key=True)
    combination_digest = Column(String(64), primary_key=True)
    package_key = Column(String(64), primary_key=True)
    package_version = Column(String(32), nullable=False)
    descriptor_digest = Column(String(64), nullable=False)
    __table_args__ = (ForeignKeyConstraint(["profile_id", "profile_digest"], ["discipline_package_compatibility_profiles.profile_id", "discipline_package_compatibility_profiles.profile_digest"], ondelete="RESTRICT"), ForeignKeyConstraint(["package_key", "package_version"], ["discipline_package_descriptors.package_key", "discipline_package_descriptors.package_version"], ondelete="RESTRICT"))


class OrganizationPackageConfigurationHead(Base):
    __tablename__ = "organization_package_configuration_heads"
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="RESTRICT"), primary_key=True)
    configuration_version = Column(BigInteger, nullable=False, default=0)
    __table_args__ = (CheckConstraint("configuration_version >= 0", name="ck_dp_org_head_version"),)


class OrganizationPackageSelection(Base):
    __tablename__ = "organization_package_selections"
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="RESTRICT"), primary_key=True)
    package_key = Column(String(64), primary_key=True)
    package_version = Column(String(32), primary_key=True)
    state = Column(String(16), nullable=False)
    configuration_version = Column(BigInteger, nullable=False)
    __table_args__ = (ForeignKeyConstraint(["package_key", "package_version"], ["discipline_package_descriptors.package_key", "discipline_package_descriptors.package_version"], ondelete="RESTRICT"), CheckConstraint("state IN ('enabled','disabled')", name="ck_dp_org_selection_state"))


class ProjectPackageConfigurationRevision(Base):
    __tablename__ = "project_package_configuration_revisions"
    project_id = Column(Integer, primary_key=True)
    configuration_revision = Column(BigInteger, primary_key=True)
    organization_id = Column(UUID(as_uuid=True), nullable=False)
    observed_registry_digest = Column(String(64), nullable=False)
    profile_id = Column(String(64), nullable=False)
    profile_digest = Column(String(64), nullable=False)
    rationale = Column(String(2000), nullable=False)
    __table_args__ = (ForeignKeyConstraint(["project_id", "organization_id"], ["projects.id", "projects.organization_id"], ondelete="RESTRICT"), ForeignKeyConstraint(["observed_registry_digest", "profile_id", "profile_digest"], ["discipline_package_registry_profile_memberships.registry_digest", "discipline_package_registry_profile_memberships.profile_id", "discipline_package_registry_profile_memberships.profile_digest"], ondelete="RESTRICT"), UniqueConstraint("project_id", "organization_id", "configuration_revision", name="uq_dp_project_revision_tenant"), CheckConstraint("configuration_revision >= 1", name="ck_dp_project_revision"))


class ProjectPackageConfigurationSelection(Base):
    __tablename__ = "project_package_configuration_selections"
    project_id = Column(Integer, primary_key=True)
    configuration_revision = Column(BigInteger, primary_key=True)
    package_key = Column(String(64), primary_key=True)
    package_version = Column(String(32), nullable=False)
    descriptor_digest = Column(String(64), nullable=False)
    __table_args__ = (ForeignKeyConstraint(["project_id", "configuration_revision"], ["project_package_configuration_revisions.project_id", "project_package_configuration_revisions.configuration_revision"], ondelete="RESTRICT"), ForeignKeyConstraint(["package_key", "package_version"], ["discipline_package_descriptors.package_key", "discipline_package_descriptors.package_version"], ondelete="RESTRICT"))


class ProjectPackageConfigurationHead(Base):
    __tablename__ = "project_package_configuration_heads"
    project_id = Column(Integer, primary_key=True)
    organization_id = Column(UUID(as_uuid=True), nullable=False)
    current_revision = Column(BigInteger, nullable=False)
    configuration_version = Column(BigInteger, nullable=False, default=0)
    __table_args__ = (ForeignKeyConstraint(["project_id", "organization_id", "current_revision"], ["project_package_configuration_revisions.project_id", "project_package_configuration_revisions.organization_id", "project_package_configuration_revisions.configuration_revision"], ondelete="RESTRICT"), CheckConstraint("configuration_version >= 0", name="ck_dp_project_head_version"))


class PackageConfigurationAuditEvent(Base):
    __tablename__ = "package_configuration_audit_events"
    event_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="RESTRICT"), nullable=False, index=True)
    project_id = Column(Integer, nullable=True)
    workspace_id = Column(Integer, nullable=True)
    actor_user_id = Column(Integer, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    category = Column(String(32), nullable=False)
    action = Column(String(32), nullable=False)
    # Nullable only for pre-M4 history whose durable event time/correlation is
    # truthfully unknown.  M4's insert guard requires both for new rows.
    occurred_at = Column(DateTime(timezone=True), nullable=True)
    correlation_id = Column(UUID(as_uuid=True), nullable=True)
    metadata_json = Column(JSONB, nullable=False, default=dict)
    __table_args__ = (ForeignKeyConstraint(["project_id", "organization_id"], ["projects.id", "projects.organization_id"], ondelete="RESTRICT"), ForeignKeyConstraint(["workspace_id", "project_id"], ["engineering_workspaces.id", "engineering_workspaces.project_id"], ondelete="RESTRICT"), CheckConstraint("workspace_id IS NULL OR project_id IS NOT NULL", name="ck_dp_audit_workspace_project"))
