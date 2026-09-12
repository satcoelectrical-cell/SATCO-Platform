"""Batch-1 catalog/rights commands with atomic Audit/outbox/idempotency effects."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.audit_log import AuditLog
from app.models.standards import OrganizationRightsBinding, StandardEdition, StandardEditionStandingObservation, StandardIdentity, StandardsIdempotency, StandardsOutbox
from app.repositories.standards_repository import StandardsRepository
from app.schemas.standards import RightsBindingReplace, RightsRevocation, StandardEditionCreate, StandardIdentityCreate, StandingObservationCreate
from app.standards.canonical import NORMALIZATION_VERSION, canonical_digest, normalize_standard_key


class StandardsError(RuntimeError):
    def __init__(self, code: str, status: int = 409) -> None:
        self.code, self.status = code, status
        super().__init__(code)


class StandardsService:
    def __init__(self, session: Session, repository: StandardsRepository) -> None:
        self.session, self.repository = session, repository

    @staticmethod
    def _identity_payload(row: StandardIdentity) -> dict:
        return {"standard_id": str(row.id), "catalog_scope": row.catalog_scope, "issuer": row.issuer_display, "designation": row.designation, "title": row.title, "language": row.language, "jurisdiction": row.jurisdiction, "identity_digest": row.identity_digest, "retired_from_new_selection": row.retired_from_new_selection}

    @staticmethod
    def _edition_payload(row: StandardEdition) -> dict:
        return {"edition_id": str(row.id), "standard_id": str(row.standard_identity_id), "edition_designation": row.edition_designation, "edition_disambiguator": row.edition_disambiguator, "official_publication_identifier": row.official_publication_identifier, "edition_digest": row.edition_digest}

    @staticmethod
    def _rights_payload(row: OrganizationRightsBinding) -> dict:
        return {"rights_binding_id": str(row.id), "edition_id": str(row.standard_edition_id), "source_provider_id": row.source_provider_id, "rights_basis": row.rights_basis, "rights_status": row.rights_status, "capabilities": {"metadata_visibility": row.allow_metadata_visibility, "content_storage": row.allow_content_storage, "indexing": row.allow_indexing, "excerpt_display": row.allow_excerpt_display, "source_retrieval": row.allow_source_retrieval, "derived_retention": row.allow_derived_retention, "derived_current_use": row.allow_derived_current_use}, "ai_processing_permission": row.ai_processing_permission, "approved_processor_policy_ids": row.approved_processor_policy_ids, "effective_from": row.effective_from.isoformat(), "effective_until": None if row.effective_until is None else row.effective_until.isoformat(), "version": row.version, "rights_digest": row.rights_digest}

    def _stage_event(self, *, actor_id: int, organization_id: UUID | None, aggregate_type: str, aggregate_id: UUID, event_id: str, details: dict) -> None:
        safe = {"event_id": event_id, "aggregate_id": str(aggregate_id), "digest": details.get("digest"), "version": details.get("version")}
        self.session.add(AuditLog(user_id=actor_id, action=event_id, entity=aggregate_type, entity_uuid=aggregate_id, details=safe))
        self.session.add(StandardsOutbox(organization_id=organization_id, aggregate_type=aggregate_type, aggregate_id=aggregate_id, event_id=event_id, event_version=1, payload=safe))

    def _reserve(self, *, organization_id: UUID, actor_id: int, operation: str, key: str, fingerprint: dict):
        if not key:
            raise StandardsError("INVALID_REQUEST", 422)
        digest = canonical_digest(fingerprint)
        row = self.repository.get_idempotency(organization_id, actor_id, operation, key, lock=True)
        if row:
            if row.request_digest != digest: raise StandardsError("IDEMPOTENCY_CONFLICT")
            if row.state == "completed": return row, digest
            raise StandardsError("VERSION_CONFLICT")
        row = StandardsIdempotency(organization_id=organization_id, actor_id=actor_id, operation=operation, idempotency_key=key, request_digest=digest, expires_at=datetime.now(timezone.utc) + timedelta(hours=24))
        self.session.add(row)
        self.session.flush()
        return row, digest

    def _complete(self, record, *, resource_type: str, resource_id: UUID, status: int, body: dict) -> dict:
        if record.state == "completed": return record.response_body
        record.state, record.resource_type, record.resource_id = "completed", resource_type, resource_id
        record.response_status, record.response_body, record.completed_at, record.version = status, body, datetime.now(timezone.utc), record.version + 1
        return body

    def register_identity(self, *, actor_id: int, organization_id: UUID, data: StandardIdentityCreate, idempotency_key: str) -> tuple[int, dict]:
        if data.catalog_scope.value == "global_trusted": scope_org = None
        else: scope_org = organization_id
        record, _ = self._reserve(organization_id=organization_id, actor_id=actor_id, operation="CAT-03", key=idempotency_key, fingerprint={"scope": data.catalog_scope.value, "organization": scope_org, **data.model_dump(mode="json")})
        if record.state == "completed": return record.response_status, record.response_body
        issuer_key, designation_key = normalize_standard_key(data.issuer_display), normalize_standard_key(data.designation)
        if self.repository.identity_by_key(data.catalog_scope.value, scope_org, issuer_key, designation_key): raise StandardsError("CONFLICT")
        digest = canonical_digest({"scope": data.catalog_scope.value, "organization_id": scope_org, "issuer_key": issuer_key, "designation_key": designation_key, "title": data.title, "language": data.language, "jurisdiction": data.jurisdiction, "source": data.metadata_source_reference})
        row = StandardIdentity(catalog_scope=data.catalog_scope.value, organization_id=scope_org, issuer_key=issuer_key, issuer_display=data.issuer_display, designation=data.designation, designation_key=designation_key, title=data.title, language=data.language, jurisdiction=data.jurisdiction, normalization_version=NORMALIZATION_VERSION, metadata_source_reference=data.metadata_source_reference, identity_digest=digest, created_by=actor_id)
        self.session.add(row); self.session.flush()
        self._stage_event(actor_id=actor_id, organization_id=scope_org, aggregate_type="standard_identity", aggregate_id=row.id, event_id="standards.identity.registered", details={"digest": digest, "version": 1})
        body = self._complete(record, resource_type="standard_identity", resource_id=row.id, status=201, body=self._identity_payload(row))
        self.session.commit(); return 201, body

    def create_edition(self, *, actor_id: int, organization_id: UUID, identity_id: UUID, data: StandardEditionCreate, idempotency_key: str) -> tuple[int, dict]:
        identity = self.repository.get_identity(identity_id, organization_id)
        if identity is None: raise StandardsError("PROTECTED_NOT_FOUND", 404)
        record, _ = self._reserve(organization_id=organization_id, actor_id=actor_id, operation="CAT-04", key=idempotency_key, fingerprint={"identity_id": identity_id, **data.model_dump(mode="json")})
        if record.state == "completed": return record.response_status, record.response_body
        if self.repository.edition_count(identity_id) >= 64: raise StandardsError("RESOURCE_LIMIT_EXCEEDED")
        edition_key = normalize_standard_key(data.edition_designation)
        if self.repository.edition_by_key(identity_id, edition_key, data.edition_disambiguator): raise StandardsError("CONFLICT")
        if data.superseded_by_edition_id and self.repository.get_edition(data.superseded_by_edition_id) is None: raise StandardsError("EDITION_UNRESOLVED", 422)
        digest = canonical_digest({"identity_id": identity_id, "edition_key": edition_key, "disambiguator": data.edition_disambiguator, "publication": data.official_publication_identifier, "source": data.metadata_source_reference})
        row = StandardEdition(standard_identity_id=identity_id, edition_designation=data.edition_designation, edition_key=edition_key, edition_disambiguator=data.edition_disambiguator, official_publication_identifier=data.official_publication_identifier, publication_date=data.publication_date, effective_date=data.effective_date, language=data.language, jurisdiction=data.jurisdiction, metadata_source_reference=data.metadata_source_reference, edition_digest=digest, created_by=actor_id)
        self.session.add(row); self.session.flush()
        observation = StandardEditionStandingObservation(standard_edition_id=row.id, standing=data.initial_standing.value, superseded_by_edition_id=data.superseded_by_edition_id, observed_effective_at=data.observed_effective_at, source_reference=data.standing_source_reference, source_digest=canonical_digest({"source": data.standing_source_reference}), created_by=actor_id, observation_digest=canonical_digest({"edition": row.id, "standing": data.initial_standing.value, "at": data.observed_effective_at}))
        self.session.add(observation); self.session.flush()
        self._stage_event(actor_id=actor_id, organization_id=identity.organization_id, aggregate_type="standard_edition", aggregate_id=row.id, event_id="standards.edition.registered", details={"digest": digest, "version": 1})
        self._stage_event(actor_id=actor_id, organization_id=identity.organization_id, aggregate_type="standard_edition_standing", aggregate_id=observation.id, event_id="standards.edition.standing_observed", details={"digest": observation.observation_digest, "version": 1})
        body = self._complete(record, resource_type="standard_edition", resource_id=row.id, status=201, body={**self._edition_payload(row), "standing_observation_id": str(observation.id), "standing": observation.standing})
        self.session.commit(); return 201, body

    def observe_standing(self, *, actor_id: int, organization_id: UUID, identity_id: UUID, edition_id: UUID, data: StandingObservationCreate, idempotency_key: str) -> tuple[int, dict]:
        if self.repository.get_identity(identity_id, organization_id) is None: raise StandardsError("PROTECTED_NOT_FOUND", 404)
        edition = self.repository.get_edition(edition_id)
        if edition is None or edition.standard_identity_id != identity_id: raise StandardsError("PROTECTED_NOT_FOUND", 404)
        record, _ = self._reserve(organization_id=organization_id, actor_id=actor_id, operation="CAT-05", key=idempotency_key, fingerprint={"identity_id": identity_id, "edition_id": edition_id, **data.model_dump(mode="json")})
        if record.state == "completed": return record.response_status, record.response_body
        previous = self.repository.current_standing(edition_id, lock=True)
        if previous is None or previous.version != data.expected_version: raise StandardsError("VERSION_CONFLICT")
        successor_version = previous.version + 1
        previous.is_current, previous.version = False, successor_version
        row = StandardEditionStandingObservation(standard_edition_id=edition_id, standing=data.standing.value, superseded_by_edition_id=data.superseded_by_edition_id, observed_effective_at=data.observed_effective_at, source_reference=data.source_reference, source_digest=canonical_digest({"source": data.source_reference}), created_by=actor_id, predecessor_id=previous.id, version=successor_version, observation_digest=canonical_digest({"edition": edition_id, "standing": data.standing.value, "predecessor": previous.id}))
        self.session.add(row); self.session.flush()
        self._stage_event(actor_id=actor_id, organization_id=organization_id, aggregate_type="standard_edition_standing", aggregate_id=row.id, event_id="standards.edition.standing_observed", details={"digest": row.observation_digest, "version": row.version})
        body = self._complete(record, resource_type="standard_edition_standing", resource_id=row.id, status=201, body={"standing_observation_id": str(row.id), "edition_id": str(edition_id), "standing": row.standing, "version": row.version})
        self.session.commit(); return 201, body

    def replace_rights(self, *, actor_id: int, organization_id: UUID, edition_id: UUID, provider_id: str, data: RightsBindingReplace, idempotency_key: str) -> tuple[int, dict]:
        if not provider_id or len(provider_id) > 80 or "\x00" in provider_id:
            raise StandardsError("INVALID_REQUEST", 422)
        edition = self.repository.get_edition(edition_id)
        if edition is None: raise StandardsError("PROTECTED_NOT_FOUND", 404)
        record, _ = self._reserve(organization_id=organization_id, actor_id=actor_id, operation="RGT-02", key=idempotency_key, fingerprint={"edition_id": edition_id, "provider_id": provider_id, **data.model_dump(mode="json")})
        if record.state == "completed": return record.response_status, record.response_body
        self.repository.lock_rights_tuple(organization_id, edition_id, provider_id)
        previous = self.repository.get_current_rights(organization_id, edition_id, provider_id, lock=True)
        actual = 0 if previous is None else previous.version
        if actual != data.expected_version: raise StandardsError("VERSION_CONFLICT")
        if previous is not None:
            successor_version = previous.version + 1
            previous.is_current, previous.version = False, successor_version
        else:
            successor_version = 1
        protected = (data.allow_content_storage, data.allow_indexing, data.allow_excerpt_display, data.allow_source_retrieval, data.allow_derived_retention, data.allow_derived_current_use)
        digest = canonical_digest({"organization_id": organization_id, "edition_id": edition_id, "provider_id": provider_id, "basis": data.rights_basis.value, "status": data.rights_status.value, "capabilities": protected, "ai": data.ai_processing_permission.value, "policies": data.approved_processor_policy_ids, "from": data.effective_from, "until": data.effective_until, "authority_digest": data.rights_authority_digest, "predecessor": None if previous is None else previous.id})
        row = OrganizationRightsBinding(organization_id=organization_id, standard_edition_id=edition_id, source_provider_id=provider_id, rights_basis=data.rights_basis.value, rights_status=data.rights_status.value, allow_metadata_visibility=data.allow_metadata_visibility, allow_content_storage=data.allow_content_storage, allow_indexing=data.allow_indexing, allow_excerpt_display=data.allow_excerpt_display, allow_source_retrieval=data.allow_source_retrieval, allow_derived_retention=data.allow_derived_retention, allow_derived_current_use=data.allow_derived_current_use, ai_processing_permission=data.ai_processing_permission.value, approved_processor_policy_ids=data.approved_processor_policy_ids, effective_from=data.effective_from, effective_until=data.effective_until, rights_authority_reference=data.rights_authority_reference, rights_authority_digest=data.rights_authority_digest, predecessor_id=None if previous is None else previous.id, reason_code=data.reason_code, reason=data.reason, version=successor_version, rights_digest=digest, created_by=actor_id)
        self.session.add(row); self.session.flush()
        event = "standards.rights.created" if previous is None else "standards.rights.replaced"
        self._stage_event(actor_id=actor_id, organization_id=organization_id, aggregate_type="standard_rights_binding", aggregate_id=row.id, event_id=event, details={"digest": digest, "version": row.version})
        body = self._complete(record, resource_type="standard_rights_binding", resource_id=row.id, status=200, body=self._rights_payload(row))
        self.session.commit(); return 200, body

    def revoke_rights(self, *, actor_id: int, organization_id: UUID, binding_id: UUID, data: RightsRevocation, idempotency_key: str) -> tuple[int, dict]:
        current = self.session.get(OrganizationRightsBinding, binding_id)
        if current is None or current.organization_id != organization_id or not current.is_current:
            raise StandardsError("PROTECTED_NOT_FOUND", 404)
        record, _ = self._reserve(organization_id=organization_id, actor_id=actor_id, operation="RGT-03", key=idempotency_key, fingerprint={"binding_id": binding_id, **data.model_dump(mode="json")})
        if record.state == "completed": return record.response_status, record.response_body
        self.repository.lock_rights_tuple(organization_id, current.standard_edition_id, current.source_provider_id)
        current = self.repository.get_current_rights(organization_id, current.standard_edition_id, current.source_provider_id, lock=True)
        if current is None or current.id != binding_id: raise StandardsError("PROTECTED_NOT_FOUND", 404)
        if current.version != data.expected_version: raise StandardsError("VERSION_CONFLICT")
        successor_version = current.version + 1
        current.is_current, current.version = False, successor_version
        digest = canonical_digest({"revoked": current.id, "predecessor_digest": current.rights_digest, "reason": data.reason})
        row = OrganizationRightsBinding(organization_id=organization_id, standard_edition_id=current.standard_edition_id, source_provider_id=current.source_provider_id, rights_basis=current.rights_basis, rights_status="revoked", allow_metadata_visibility=False, allow_content_storage=False, allow_indexing=False, allow_excerpt_display=False, allow_source_retrieval=False, allow_derived_retention=False, allow_derived_current_use=False, ai_processing_permission="prohibited", approved_processor_policy_ids=[], effective_from=datetime.now(timezone.utc), effective_until=None, rights_authority_reference=current.rights_authority_reference, rights_authority_digest=current.rights_authority_digest, predecessor_id=current.id, reason_code="revoked", reason=data.reason, version=successor_version, rights_digest=digest, created_by=actor_id)
        self.session.add(row); self.session.flush()
        self._stage_event(actor_id=actor_id, organization_id=organization_id, aggregate_type="standard_rights_binding", aggregate_id=row.id, event_id="standards.rights.revoked", details={"digest": digest, "version": row.version})
        body = self._complete(record, resource_type="standard_rights_binding", resource_id=row.id, status=201, body=self._rights_payload(row))
        self.session.commit(); return 201, body

    def materialize_expiry(self, *, actor_id: int, organization_id: UUID, edition_id: UUID, provider_id: str, now: datetime | None = None) -> OrganizationRightsBinding | None:
        """Append the one durable expiry successor when a live window crosses its end.

        Reads still fail closed without this maintenance action; this exists solely
        to preserve the accepted event-6 historical/audit trail.
        """
        now = now or datetime.now(timezone.utc)
        self.repository.lock_rights_tuple(organization_id, edition_id, provider_id)
        current = self.repository.get_current_rights(organization_id, edition_id, provider_id, lock=True)
        if current is None or current.rights_status != "active" or current.effective_until is None or current.effective_until > now:
            return None
        successor_version = current.version + 1
        current.is_current, current.version = False, successor_version
        digest = canonical_digest({"expired": current.id, "predecessor_digest": current.rights_digest, "effective_until": current.effective_until})
        row = OrganizationRightsBinding(organization_id=organization_id, standard_edition_id=edition_id, source_provider_id=provider_id, rights_basis=current.rights_basis, rights_status="expired", allow_metadata_visibility=False, allow_content_storage=False, allow_indexing=False, allow_excerpt_display=False, allow_source_retrieval=False, allow_derived_retention=False, allow_derived_current_use=False, ai_processing_permission="prohibited", approved_processor_policy_ids=[], effective_from=current.effective_from, effective_until=current.effective_until, rights_authority_reference=current.rights_authority_reference, rights_authority_digest=current.rights_authority_digest, predecessor_id=current.id, reason_code="expired", reason=None, version=successor_version, rights_digest=digest, created_by=actor_id)
        self.session.add(row); self.session.flush()
        self._stage_event(actor_id=actor_id, organization_id=organization_id, aggregate_type="standard_rights_binding", aggregate_id=row.id, event_id="standards.rights.expired", details={"digest": digest, "version": row.version})
        return row

    @staticmethod
    def evaluate_capability(row: OrganizationRightsBinding | None, capability: str, now: datetime | None = None) -> bool:
        """Fail closed for all unknown, expired, revoked, malformed and inactive states."""
        if row is None or not row.is_current: return False
        now = now or datetime.now(timezone.utc)
        if row.rights_basis in {"metadata_only", "unknown"} or row.rights_status != "active": return False
        if row.effective_from > now or (row.effective_until is not None and row.effective_until <= now): return False
        mapping = {"metadata_visibility": row.allow_metadata_visibility, "content_storage": row.allow_content_storage, "indexing": row.allow_indexing, "excerpt_display": row.allow_excerpt_display, "source_retrieval": row.allow_source_retrieval, "derived_retention": row.allow_derived_retention, "derived_current_use": row.allow_derived_current_use}
        return mapping.get(capability, False)
