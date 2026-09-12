"""Tenant-scoped SQLAlchemy repository; protected relations are never unscoped."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import func, select, text
from sqlalchemy.orm import Session

from app.models.standards import OrganizationRightsBinding, StandardEdition, StandardEditionStandingObservation, StandardIdentity, StandardsIdempotency


class StandardsRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def list_identities(self, organization_id: UUID, *, query: str | None, scope: str | None, limit: int, before: UUID | None = None):
        statement = select(StandardIdentity).where(
            (StandardIdentity.catalog_scope == "global_trusted") |
            ((StandardIdentity.catalog_scope == "organization_private") & (StandardIdentity.organization_id == organization_id))
        )
        if scope:
            statement = statement.where(StandardIdentity.catalog_scope == scope)
        if query:
            needle = f"%{query.casefold()}%"
            statement = statement.where((StandardIdentity.issuer_key.ilike(needle)) | (StandardIdentity.designation_key.ilike(needle)))
        if before:
            statement = statement.where(StandardIdentity.id < before)
        return list(self.session.scalars(statement.order_by(StandardIdentity.id).limit(limit + 1)))

    def get_identity(self, identity_id: UUID, organization_id: UUID | None = None):
        statement = select(StandardIdentity).where(StandardIdentity.id == identity_id)
        if organization_id is not None:
            statement = statement.where((StandardIdentity.catalog_scope == "global_trusted") | (StandardIdentity.organization_id == organization_id))
        return self.session.scalar(statement)

    def identity_by_key(self, scope: str, organization_id: UUID | None, issuer_key: str, designation_key: str):
        return self.session.scalar(select(StandardIdentity).where(StandardIdentity.catalog_scope == scope, StandardIdentity.organization_id.is_(organization_id) if organization_id is None else StandardIdentity.organization_id == organization_id, StandardIdentity.issuer_key == issuer_key, StandardIdentity.designation_key == designation_key))

    def get_edition(self, edition_id: UUID):
        return self.session.get(StandardEdition, edition_id)

    def edition_by_key(self, identity_id: UUID, edition_key: str, disambiguator: str):
        return self.session.scalar(select(StandardEdition).where(StandardEdition.standard_identity_id == identity_id, StandardEdition.edition_key == edition_key, StandardEdition.edition_disambiguator == disambiguator))

    def edition_count(self, identity_id: UUID) -> int:
        return int(self.session.scalar(select(func.count()).select_from(StandardEdition).where(StandardEdition.standard_identity_id == identity_id)) or 0)

    def current_standing(self, edition_id: UUID, *, lock: bool = False):
        statement = select(StandardEditionStandingObservation).where(StandardEditionStandingObservation.standard_edition_id == edition_id, StandardEditionStandingObservation.is_current.is_(True))
        if lock: statement = statement.with_for_update()
        return self.session.scalar(statement)

    def get_current_rights(self, organization_id: UUID, edition_id: UUID, provider_id: str, *, lock: bool = False):
        statement = select(OrganizationRightsBinding).where(OrganizationRightsBinding.organization_id == organization_id, OrganizationRightsBinding.standard_edition_id == edition_id, OrganizationRightsBinding.source_provider_id == provider_id, OrganizationRightsBinding.is_current.is_(True))
        if lock: statement = statement.with_for_update()
        return self.session.scalar(statement)

    def lock_rights_tuple(self, organization_id: UUID, edition_id: UUID, provider_id: str) -> None:
        key = f"standards-rights:{organization_id}:{edition_id}:{provider_id}"
        self.session.execute(text("SELECT pg_advisory_xact_lock(hashtextextended(:key, 0))"), {"key": key})

    def get_idempotency(self, organization_id: UUID, actor_id: int, operation: str, key: str, *, lock: bool = False):
        statement = select(StandardsIdempotency).where(StandardsIdempotency.organization_id == organization_id, StandardsIdempotency.actor_id == actor_id, StandardsIdempotency.operation == operation, StandardsIdempotency.idempotency_key == key)
        if lock: statement = statement.with_for_update()
        return self.session.scalar(statement)

    def list_rights(self, organization_id: UUID, *, provider_id: str | None, limit: int, before: UUID | None = None):
        statement = select(OrganizationRightsBinding).where(OrganizationRightsBinding.organization_id == organization_id, OrganizationRightsBinding.is_current.is_(True))
        if provider_id: statement = statement.where(OrganizationRightsBinding.source_provider_id == provider_id)
        if before: statement = statement.where(OrganizationRightsBinding.id < before)
        return list(self.session.scalars(statement.order_by(OrganizationRightsBinding.id).limit(limit + 1)))
