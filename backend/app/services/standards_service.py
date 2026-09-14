"""Batch-1 catalog/rights commands with atomic Audit/outbox/idempotency effects."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
import hashlib
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.exc import DBAPIError, IntegrityError
from sqlalchemy.orm import Session

from app.models.audit_log import AuditLog
from app.models.organization import Organization, UserOrganizationMembership
from app.models.project import Project
from app.models.standards import OrganizationRightsBinding, ProjectStandardApplicability, StandardAssertionVerificationEvent, StandardEdition, StandardEditionStandingObservation, StandardIdentity, StandardIntelligenceRun, StandardKnowledgeAssertion, StandardSourceSnapshot, StandardsIdempotency, StandardsOutbox
from app.models.user import User
from app.repositories.standards_repository import StandardsRepository
from app.schemas.standards import ApplicabilityDeclaration, ApplicabilityRetirement, AssertionCreate, AssertionRejection, AssertionVerification, RightsBindingReplace, RightsRevocation, SourceSnapshotCreate, StandardEditionCreate, StandardIdentityCreate, StandingObservationCreate, StandardsIntelligenceRunCreate
from app.standards.canonical import NORMALIZATION_VERSION, canonical_digest, normalize_standard_key
from app.standards.handles import OpaqueAuthorizedHandleInvalid, issue_handle, open_provider_token, seal_provider_token, verify_handle
from app.ai.standards_intelligence import TEMPLATE_DIGEST, TEMPLATE_ID, TEMPLATE_VERSION, canonical_bytes, compose_envelope, validate_output


class StandardsError(RuntimeError):
    def __init__(self, code: str, status: int = 409) -> None:
        self.code, self.status = code, status
        super().__init__(code)


_RETRYABLE_DATABASE_STATES = frozenset({"40001", "40P01", "55P03"})


def run_bounded_database_attempts(session: Session, operation):
    """Run at most three fresh DB attempts; provider failures are never retried."""
    for attempt in range(3):
        try:
            return operation()
        except DBAPIError as error:
            sqlstate = getattr(error.orig, "sqlstate", None) or getattr(error.orig, "pgcode", None)
            session.rollback()
            session.expire_all()
            if sqlstate not in _RETRYABLE_DATABASE_STATES:
                raise
            if attempt == 2:
                raise StandardsError("VERSION_CONFLICT", 409) from error
    raise AssertionError("bounded database attempts exhausted")


class StandardsService:
    def __init__(self, session: Session, repository: StandardsRepository, *, providers=None, objects=None, candidates=None, intelligence_provider=None, intelligence_provider_id: str = "local", intelligence_provider_model: str = "local-safe-v1", intelligence_processor_policy_id: str = "local", before_intelligence_dispatch=None) -> None:
        self.session, self.repository, self.providers, self.objects, self.candidates = session, repository, providers or {}, objects, candidates
        self.intelligence_provider, self.intelligence_provider_id, self.intelligence_provider_model, self.intelligence_processor_policy_id = intelligence_provider, intelligence_provider_id, intelligence_provider_model, intelligence_processor_policy_id
        self.before_intelligence_dispatch = before_intelligence_dispatch

    @staticmethod
    def _identity_payload(row: StandardIdentity) -> dict:
        return {"standard_id": str(row.id), "catalog_scope": row.catalog_scope, "issuer": row.issuer_display, "designation": row.designation, "title": row.title, "language": row.language, "jurisdiction": row.jurisdiction, "identity_digest": row.identity_digest, "retired_from_new_selection": row.retired_from_new_selection}

    @staticmethod
    def _edition_payload(row: StandardEdition) -> dict:
        return {"edition_id": str(row.id), "standard_id": str(row.standard_identity_id), "edition_designation": row.edition_designation, "edition_disambiguator": row.edition_disambiguator, "official_publication_identifier": row.official_publication_identifier, "edition_digest": row.edition_digest}

    @staticmethod
    def _rights_payload(row: OrganizationRightsBinding) -> dict:
        return {"rights_binding_id": str(row.id), "edition_id": str(row.standard_edition_id), "source_provider_id": row.source_provider_id, "rights_basis": row.rights_basis, "rights_status": row.rights_status, "capabilities": {"metadata_visibility": row.allow_metadata_visibility, "content_storage": row.allow_content_storage, "indexing": row.allow_indexing, "excerpt_display": row.allow_excerpt_display, "source_retrieval": row.allow_source_retrieval, "derived_retention": row.allow_derived_retention, "derived_current_use": row.allow_derived_current_use}, "ai_processing_permission": row.ai_processing_permission, "approved_processor_policy_ids": row.approved_processor_policy_ids, "effective_from": row.effective_from.isoformat(), "effective_until": None if row.effective_until is None else row.effective_until.isoformat(), "version": row.version, "rights_digest": row.rights_digest}

    @staticmethod
    def _applicability_payload(row: ProjectStandardApplicability) -> dict:
        return {
            "applicability_id": str(row.id), "project_id": row.project_id,
            "edition_id": None if row.standard_edition_id is None else str(row.standard_edition_id),
            "candidate_designation_key": row.candidate_designation_key, "status": row.status,
            "applicability_role": row.applicability_role, "rationale_code": row.rationale_code,
            "rationale": row.rationale, "origin_reference": row.origin_reference,
            "source_candidate_reference": row.source_candidate_reference,
            "revision": row.revision, "is_current": row.is_current,
            "predecessor_id": None if row.predecessor_id is None else str(row.predecessor_id),
            "successor_id": None if row.successor_id is None else str(row.successor_id),
            "applicability_digest": row.applicability_digest,
        }

    def _stage_event(self, *, actor_id: int, organization_id: UUID | None, aggregate_type: str, aggregate_id: UUID, event_id: str, details: dict) -> None:
        safe = {"event_id": event_id, "aggregate_id": str(aggregate_id), "digest": details.get("digest"), "version": details.get("version")}
        self.session.add(AuditLog(user_id=actor_id, action=event_id, entity=aggregate_type, entity_uuid=aggregate_id, details=safe))
        self.session.add(StandardsOutbox(organization_id=organization_id, aggregate_type=aggregate_type, aggregate_id=aggregate_id, event_id=event_id, event_version=1, payload=safe))

    def _reserve(self, *, organization_id: UUID, actor_id: int, operation: str, key: str, fingerprint: dict):
        if not key or len(key) > 160:
            raise StandardsError("INVALID_REQUEST", 422)
        self.repository.lock_idempotency_tuple(organization_id, actor_id, operation, key)
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

    def _mark_stale_assertions(self, *, actor_id: int, organization_id: UUID,
                               rights: OrganizationRightsBinding, reason: str) -> None:
        """Keep immutable assertion meaning, while failing closed for current use.

        A current rights successor can still permit retained derived material;
        it never preserves a prior human-verification projection when current
        use is denied.  The projection update and event are in the same rights
        transaction, so consumers cannot observe an un-audited stale state.
        """
        if self.evaluate_capability(rights, "derived_current_use"):
            return
        retained = self.evaluate_capability(rights, "derived_retention")
        for assertion in self.repository.assertions_for_rights(
            organization_id, rights.standard_edition_id, rights.source_provider_id
        ):
            event = StandardAssertionVerificationEvent(
                assertion_id=assertion.id,
                event_kind="eligibility_evaluation",
                status="stale",
                reason=reason,
                source_rights_binding_id=rights.id,
                source_rights_binding_version=rights.version,
                source_rights_digest=rights.rights_digest,
                assertion_digest=assertion.assertion_digest,
                actor_kind="system",
                verified_by=None,
            )
            self.session.add(event)
            self.session.flush()
            assertion.current_verification_event_id = event.id
            assertion.verification_status = "stale"
            assertion.retained_derived_use_eligible = retained
            assertion.evaluated_rights_revision = rights.version
            assertion.version += 1
            self._stage_event(
                actor_id=actor_id,
                organization_id=organization_id,
                aggregate_type="standard_knowledge_assertion",
                aggregate_id=assertion.id,
                event_id="standards.assertion.stale",
                details={"digest": assertion.assertion_digest, "version": assertion.version},
            )

    def _complete(self, record, *, resource_type: str, resource_id: UUID, status: int, body: dict) -> dict:
        if record.state == "completed": return record.response_body
        record.state, record.resource_type, record.resource_id = "completed", resource_type, resource_id
        record.response_status, record.response_body, record.completed_at, record.version = status, body, datetime.now(timezone.utc), record.version + 1
        return body

    def list_applicability(self, *, organization_id: UUID, project_id: int, state: str | None, limit: int, before: UUID | None = None) -> list[ProjectStandardApplicability]:
        if self.repository.get_project(project_id, organization_id) is None:
            raise StandardsError("PROTECTED_NOT_FOUND", 404)
        return self.repository.list_applicability(organization_id, project_id, state=state, limit=limit, before=before)

    def package_candidates(self, *, organization_id: UUID, project_id: int, package_version: str | None = None) -> list[dict]:
        if self.repository.get_project(project_id, organization_id) is None:
            raise StandardsError("PROTECTED_NOT_FOUND", 404)
        if self.candidates is None:
            return []
        return self.candidates.candidates(organization_id=organization_id, project_id=project_id, package_version=package_version)

    def _candidate_reference(self, *, organization_id: UUID, project_id: int, candidate_id: UUID, candidate_digest: str) -> tuple[str, dict]:
        candidate = next((item for item in self.package_candidates(organization_id=organization_id, project_id=project_id)
                          if item["candidate_id"] == str(candidate_id) and item["candidate_digest"] == candidate_digest), None)
        if candidate is None:
            raise StandardsError("VERSION_CONFLICT")
        return f"{candidate_id}:{candidate_digest}", candidate

    def _append_candidate(self, *, actor_id: int, organization_id: UUID, project_id: int, reference: str, candidate: dict) -> ProjectStandardApplicability:
        existing = self.repository.candidate_by_reference(organization_id, project_id, reference)
        if existing is not None:
            return existing
        digest = canonical_digest({"candidate_reference": reference, "candidate_digest": candidate["candidate_digest"], "project_id": project_id})
        row = ProjectStandardApplicability(
            organization_id=organization_id, project_id=project_id,
            standard_edition_id=None, candidate_designation_key=candidate["designation_key"],
            status="candidate_advisory", applicability_role=candidate["suggested_role"],
            rationale_code=candidate["rationale_code"], rationale="Static discipline-package advisory candidate",
            origin_reference=f"package:{candidate['package_key']}@{candidate['package_version']}:{candidate['hook_id']}",
            source_candidate_reference=reference, expected_predecessor_revision=None,
            applicability_digest=digest, declared_by=actor_id,
        )
        self.session.add(row); self.session.flush()
        self._stage_event(actor_id=actor_id, organization_id=organization_id,
            aggregate_type="project_standard_applicability", aggregate_id=row.id,
            event_id="standards.applicability.candidate_recorded",
            details={"digest": digest, "version": row.revision})
        return row

    def declare_applicability(self, *, actor_id: int, organization_id: UUID, project_id: int, data: ApplicabilityDeclaration, idempotency_key: str) -> tuple[int, dict]:
        if self.repository.get_project(project_id, organization_id) is None:
            raise StandardsError("PROTECTED_NOT_FOUND", 404)
        edition = self.repository.get_edition(data.edition_id)
        if edition is None or self.repository.get_identity(edition.standard_identity_id, organization_id) is None:
            # An opaque edition identifier is a protected catalog lookup;
            # foreign/private and absent identities remain indistinguishable.
            raise StandardsError("PROTECTED_NOT_FOUND", 404)
        record, _ = self._reserve(organization_id=organization_id, actor_id=actor_id, operation="APP-03", key=idempotency_key,
            fingerprint={"project_id": project_id, **data.model_dump(mode="json")})
        if record.state == "completed":
            return record.response_status, record.response_body
        self.repository.lock_applicability_tuple(project_id, edition.id)
        candidate_reference, candidate = (None, None)
        if data.candidate_id is not None:
            candidate_reference, candidate = self._candidate_reference(organization_id=organization_id, project_id=project_id,
                candidate_id=data.candidate_id, candidate_digest=data.candidate_digest)
            self.repository.lock_candidate_reference(project_id, candidate_reference)
            self._append_candidate(actor_id=actor_id, organization_id=organization_id, project_id=project_id,
                reference=candidate_reference, candidate=candidate)
        previous = self.repository.current_applicability(organization_id, project_id, edition.id, lock=True)
        actual = 0 if previous is None else previous.revision
        if actual != data.expected_revision:
            raise StandardsError("VERSION_CONFLICT")
        row_id = uuid4()
        if previous is not None:
            previous.is_current, previous.successor_id, previous.revision = False, row_id, previous.revision + 1
        revision = 1 if previous is None else previous.revision
        digest = canonical_digest({"organization_id": organization_id, "project_id": project_id, "edition_id": edition.id,
            "status": data.status, "role": data.applicability_role, "rationale_code": data.rationale_code,
            "rationale": data.rationale, "mandatory_kind": data.mandatory_source_kind,
            "mandatory_reference": data.mandatory_source_reference, "mandatory_digest": data.mandatory_source_digest,
            "candidate_reference": candidate_reference, "predecessor_id": None if previous is None else previous.id,
            "revision": revision, "declared_by": actor_id})
        row = ProjectStandardApplicability(
            id=row_id, organization_id=organization_id, project_id=project_id, standard_edition_id=edition.id,
            status=data.status, applicability_role=data.applicability_role, rationale_code=data.rationale_code,
            rationale=data.rationale, origin_reference=f"human:{actor_id}", source_candidate_reference=candidate_reference,
            mandatory_source_kind=data.mandatory_source_kind, mandatory_source_reference=data.mandatory_source_reference,
            mandatory_source_digest=data.mandatory_source_digest, expected_predecessor_revision=None if previous is None else data.expected_revision,
            predecessor_id=None if previous is None else previous.id, revision=revision, applicability_digest=digest,
            declared_by=actor_id,
        )
        self.session.add(row); self.session.flush()
        self._stage_event(actor_id=actor_id, organization_id=organization_id,
            aggregate_type="project_standard_applicability", aggregate_id=row.id,
            event_id="standards.applicability.declared", details={"digest": digest, "version": revision})
        body = self._complete(record, resource_type="project_standard_applicability", resource_id=row.id,
            status=201, body=self._applicability_payload(row))
        self.session.commit()
        return 201, body

    def retire_applicability(self, *, actor_id: int, organization_id: UUID, project_id: int, applicability_id: UUID, data: ApplicabilityRetirement, idempotency_key: str) -> tuple[int, dict]:
        current = self.repository.applicability(applicability_id, organization_id, project_id)
        if current is None or not current.is_current or current.status == "candidate_advisory":
            raise StandardsError("PROTECTED_NOT_FOUND", 404)
        record, _ = self._reserve(organization_id=organization_id, actor_id=actor_id, operation="APP-04", key=idempotency_key,
            fingerprint={"project_id": project_id, "applicability_id": applicability_id, **data.model_dump(mode="json")})
        if record.state == "completed":
            return record.response_status, record.response_body
        self.repository.lock_applicability_tuple(project_id, current.standard_edition_id)
        current = self.repository.applicability(applicability_id, organization_id, project_id, lock=True)
        if current is None or not current.is_current or current.revision != data.expected_revision:
            raise StandardsError("VERSION_CONFLICT")
        successor_id, revision = uuid4(), current.revision + 1
        current.is_current, current.successor_id, current.revision = False, successor_id, revision
        role = "design_basis" if current.applicability_role == "mandatory" else current.applicability_role
        digest = canonical_digest({"retired": current.id, "reason": data.reason, "revision": revision,
            "predecessor_digest": current.applicability_digest, "actor": actor_id})
        row = ProjectStandardApplicability(
            id=successor_id, organization_id=organization_id, project_id=project_id,
            standard_edition_id=current.standard_edition_id, status="retired", applicability_role=role,
            rationale_code="retired", rationale=data.reason, origin_reference=f"human:{actor_id}",
            expected_predecessor_revision=data.expected_revision, predecessor_id=current.id,
            revision=revision, applicability_digest=digest, declared_by=actor_id,
        )
        self.session.add(row); self.session.flush()
        self._stage_event(actor_id=actor_id, organization_id=organization_id,
            aggregate_type="project_standard_applicability", aggregate_id=row.id,
            event_id="standards.applicability.retired", details={"digest": digest, "version": revision})
        body = self._complete(record, resource_type="project_standard_applicability", resource_id=row.id,
            status=201, body=self._applicability_payload(row))
        self.session.commit()
        return 201, body

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
        self._mark_stale_assertions(actor_id=actor_id, organization_id=organization_id, rights=row, reason="rights_replaced")
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
        self._mark_stale_assertions(actor_id=actor_id, organization_id=organization_id, rights=row, reason="rights_revoked")
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
        self._mark_stale_assertions(actor_id=actor_id, organization_id=organization_id, rights=row, reason="rights_expired")
        self._stage_event(actor_id=actor_id, organization_id=organization_id, aggregate_type="standard_rights_binding", aggregate_id=row.id, event_id="standards.rights.expired", details={"digest": digest, "version": row.version})
        return row

    @staticmethod
    def _capabilities(rights: OrganizationRightsBinding) -> dict[str, bool]:
        return {name: StandardsService.evaluate_capability(rights, name) for name in (
            "content_storage", "excerpt_display", "source_retrieval", "derived_retention", "derived_current_use",
        )}

    def _current_rights(self, *, organization_id: UUID, edition_id: UUID, provider_id: str, capability: str, lock: bool = False) -> OrganizationRightsBinding:
        rights = self.repository.get_current_rights(organization_id, edition_id, provider_id, lock=lock)
        if not self.evaluate_capability(rights, capability):
            raise StandardsError("RIGHTS_NOT_PERMITTED", 403)
        return rights

    @staticmethod
    def _snapshot_payload(row: StandardSourceSnapshot, *, actor_id: int) -> dict:
        payload = {
            "snapshot_id": str(row.id), "edition_id": str(row.standard_edition_id),
            "source_location": row.source_location, "availability_status": row.availability_status,
            "integrity_verified": row.integrity_verified, "snapshot_digest": row.snapshot_digest,
        }
        if row.availability_status == "available" and row.integrity_verified:
            payload["authorized_handle"] = issue_handle(actor_id=actor_id, organization_id=str(row.organization_id), project_id=row.project_id,
                operation="SRC-02", resource_id=str(row.id), edition_id=str(row.standard_edition_id),
                rights_binding_id=str(row.rights_binding_id), rights_version=row.rights_binding_version, rights_digest=row.rights_digest,
                purpose=row.request_purpose, provider_id=row.source_provider_id, source_location=row.source_location,
                integrity_digest=row.snapshot_digest)
        return payload

    @staticmethod
    def _assertion_payload(row: StandardKnowledgeAssertion, *, actor_id: int, provider_id: str) -> dict:
        """Return opaque decision capabilities, never source/provider material."""
        base = {
            "actor_id": actor_id,
            "organization_id": str(row.organization_id),
            "project_id": row.project_id,
            "resource_id": str(row.id),
            "edition_id": str(row.standard_edition_id),
            "rights_binding_id": str(row.rights_binding_id),
            "rights_version": row.rights_binding_version,
            "rights_digest": row.rights_digest,
            "purpose": "assertion_decision",
            "provider_id": provider_id,
            "source_location": row.source_location,
            "integrity_digest": row.source_content_digest,
        }
        return {
            "assertion_id": str(row.id),
            "assertion_kind": row.assertion_kind,
            "assertion_digest": row.assertion_digest,
            "verification_status": row.verification_status,
            "version": row.version,
            "verification_handle": issue_handle(operation="AST-02", **base),
            "rejection_handle": issue_handle(operation="AST-03", **base),
        }

    def create_source_snapshots(self, *, actor_id: int, organization_id: UUID, project_id: int, data: SourceSnapshotCreate, idempotency_key: str, correlation_id: UUID | None = None) -> tuple[int, dict]:
        """SRC-01: fixed, allowlisted fragments only; provider I/O precedes final persistence."""
        if self.repository.get_project(project_id, organization_id) is None:
            raise StandardsError("PROTECTED_NOT_FOUND", 404)
        edition = self.repository.get_edition(data.edition_id)
        identity = edition and self.repository.get_identity(edition.standard_identity_id, organization_id)
        provider = self.providers.get(data.provider_id)
        if edition is None or identity is None or provider is None:
            raise StandardsError("PROTECTED_NOT_FOUND", 404)
        required = "source_retrieval" if data.purpose == "material_support" else "metadata_visibility"
        rights = self._current_rights(organization_id=organization_id, edition_id=edition.id, provider_id=data.provider_id, capability=required)
        if data.purpose == "material_support" and not self.evaluate_capability(rights, "source_retrieval"):
            raise StandardsError("RIGHTS_NOT_PERMITTED", 403)
        record, _ = self._reserve(organization_id=organization_id, actor_id=actor_id, operation="SRC-01", key=idempotency_key,
            fingerprint={"project_id": project_id, **data.model_dump(mode="json")})
        if record.state == "completed": return record.response_status, record.response_body
        standing = self.repository.current_standing(edition.id)
        if standing is None or (data.purpose == "material_support" and standing.standing != "current"):
            raise StandardsError("EDITION_UNRESOLVED", 409)
        # Phase 1 completes the small intent/idempotency transaction before
        # provider/object I/O.  Phase 3 below obtains fresh rights under lock
        # and persists the immutable receipt atomically with Audit/outbox.
        self.session.commit()
        # Reference-only requests never retrieve bytes.  They retain only a
        # safe bibliographic/provenance receipt and cannot be upgraded into
        # material support by later code.
        if data.purpose == "reference_only":
            now, correlation_id = datetime.now(timezone.utc), correlation_id or uuid4()
            rows = []
            for requested in data.fragments:
                snapshot_id = uuid4()
                digest = canonical_digest({"id": snapshot_id, "edition": edition.id, "provider": data.provider_id,
                    "location": requested.location, "rights": rights.rights_digest, "purpose": "reference_only"})
                row = StandardSourceSnapshot(id=snapshot_id, organization_id=organization_id, project_id=project_id, standard_identity_id=edition.standard_identity_id,
                    standard_edition_id=edition.id, source_provider_id=data.provider_id, adapter_policy_id=provider.adapter_policy_id, adapter_policy_version=provider.adapter_policy_version,
                    source_location=requested.location, availability_status="rights_restricted", request_purpose="reference_only", correlation_id=correlation_id,
                    rights_binding_id=rights.id, rights_binding_version=rights.version, rights_digest=rights.rights_digest, evaluated_capabilities=self._capabilities(rights),
                    standing_observation_id=standing.id, standing_observation_digest=standing.observation_digest,
                    source_metadata_digest=canonical_digest({"location": requested.location, "provider": data.provider_id}), integrity_verified=False,
                    integrity_verified_at=now, snapshot_digest=digest, retrieved_at=now, retrieved_by=actor_id)
                self.session.add(row); rows.append(row)
            self.session.flush()
            for row in rows:
                self._stage_event(actor_id=actor_id, organization_id=organization_id, aggregate_type="standard_source_snapshot", aggregate_id=row.id, event_id="standards.source.retrieval_unavailable", details={"digest": row.snapshot_digest, "version": 1})
                self._stage_event(actor_id=actor_id, organization_id=organization_id, aggregate_type="standard_source_snapshot", aggregate_id=row.id, event_id="standards.source.snapshot_created", details={"digest": row.snapshot_digest, "version": 1})
            body = {"items": [self._snapshot_payload(row, actor_id=actor_id) for row in rows]}
            self._complete(record, resource_type="standard_source_snapshot", resource_id=rows[0].id, status=201, body=body)
            self.session.commit(); return 201, body
        # Provider retrieval intentionally has no URL, search, list or redirect input.
        fragments = []
        try:
            for requested in data.fragments:
                fragment = provider.retrieve(location=requested.location, purpose=data.purpose, provider_token=None)
                if fragment.location != requested.location or fragment.content is None or len(fragment.content) < 1:
                    raise ValueError("SOURCE_INCOMPLETE")
                if len(fragment.content) > 8192:
                    raise StandardsError("RESOURCE_LIMIT_EXCEEDED", 422)
                fragments.append(fragment)
        except LookupError as error:
            raise StandardsError("CONTENT_UNAVAILABLE", 503) from error
        except ValueError as error:
            raise StandardsError("INVALID_REQUEST", 422) from error
        if sum(len(item.content) for item in fragments) > 32768:
            raise StandardsError("RESOURCE_LIMIT_EXCEEDED", 422)
        now, correlation_id = datetime.now(timezone.utc), correlation_id or uuid4()
        rows: list[StandardSourceSnapshot] = []
        for fragment in fragments:
            snapshot_id = uuid4()
            use_object = self.evaluate_capability(rights, "content_storage")
            receipt = None
            sealed = None
            if use_object:
                if self.objects is None: raise StandardsError("CONTENT_UNAVAILABLE", 503)
                receipt = self.objects.put_private(organization_id=organization_id, project_id=project_id, snapshot_id=snapshot_id, content=fragment.content, media_type=fragment.media_type or "text/plain")
            else:
                if not fragment.provider_token or not fragment.version_digest or len(fragment.version_digest) != 64:
                    raise StandardsError("SOURCE_INCOMPLETE", 409)
                sealed = seal_provider_token(fragment.provider_token, provider_id=data.provider_id, organization_id=str(organization_id), project_id=project_id)
            content_sha = receipt.sha256 if receipt else None
            snapshot_digest = canonical_digest({"id": snapshot_id, "edition": edition.id, "provider": data.provider_id, "location": fragment.location,
                "object_digest": None if receipt is None else receipt.sha256, "provider_version_digest": None if receipt else fragment.version_digest,
                "rights": rights.rights_digest, "standing": standing.observation_digest, "purpose": data.purpose})
            row = StandardSourceSnapshot(id=snapshot_id, organization_id=organization_id, project_id=project_id, standard_identity_id=edition.standard_identity_id,
                standard_edition_id=edition.id, source_provider_id=data.provider_id, adapter_policy_id=provider.adapter_policy_id,
                adapter_policy_version=provider.adapter_policy_version, source_location=fragment.location, availability_status="available", request_purpose=data.purpose,
                correlation_id=correlation_id, object_key=None if receipt is None else receipt.key, object_version=None if receipt is None else receipt.version,
                provider_handle_ciphertext=sealed, provider_handle_key_version=None if sealed is None else "v1", provider_version_digest=None if receipt else fragment.version_digest,
                content_sha256=content_sha, byte_count=len(fragment.content), media_type=fragment.media_type or "text/plain", rights_binding_id=rights.id,
                rights_binding_version=rights.version, rights_digest=rights.rights_digest, evaluated_capabilities=self._capabilities(rights),
                standing_observation_id=standing.id, standing_observation_digest=standing.observation_digest,
                source_metadata_digest=canonical_digest({"location": fragment.location, "provider": data.provider_id}), integrity_verified=True,
                integrity_verified_at=now, snapshot_digest=snapshot_digest, retrieved_at=now, retrieved_by=actor_id)
            self.session.add(row); rows.append(row)
        try:
            self.session.flush()
            # The final in-transaction rights/version check closes the provider/revocation race.
            final = self._current_rights(organization_id=organization_id, edition_id=edition.id, provider_id=data.provider_id, capability=required, lock=True)
            if final.id != rights.id or final.version != rights.version or final.rights_digest != rights.rights_digest:
                raise StandardsError("RIGHTS_NOT_PERMITTED", 403)
            for row in rows:
                self._stage_event(actor_id=actor_id, organization_id=organization_id, aggregate_type="standard_source_snapshot", aggregate_id=row.id, event_id="standards.source.retrieval_succeeded", details={"digest": row.snapshot_digest, "version": 1})
                self._stage_event(actor_id=actor_id, organization_id=organization_id, aggregate_type="standard_source_snapshot", aggregate_id=row.id, event_id="standards.source.snapshot_created", details={"digest": row.snapshot_digest, "version": 1})
            body = {"items": [self._snapshot_payload(row, actor_id=actor_id) for row in rows]}
            self._complete(record, resource_type="standard_source_snapshot", resource_id=rows[0].id, status=201, body=body)
            self.session.commit(); return 201, body
        except Exception:
            self.session.rollback()
            if self.objects is not None:
                for row in rows:
                    if row.object_key and row.object_version:
                        try: self.objects.delete_exact(row.object_key, row.object_version)
                        except Exception: pass
            raise

    def display_source_snapshot(self, *, actor_id: int, organization_id: UUID, project_id: int,
                                snapshot_id: UUID, authorized_handle: str) -> dict:
        row = self.repository.snapshot(snapshot_id, organization_id, project_id)
        if row is None: raise StandardsError("PROTECTED_NOT_FOUND", 404)
        rights = self._current_rights(organization_id=organization_id, edition_id=row.standard_edition_id, provider_id=row.source_provider_id, capability="excerpt_display")
        if not row.integrity_verified or row.availability_status != "available" or rights.version != row.rights_binding_version or rights.rights_digest != row.rights_digest:
            raise StandardsError("DISPLAY_NOT_PERMITTED", 403)
        try:
            verify_handle(
                authorized_handle,
                actor_id=actor_id,
                organization_id=str(organization_id),
                project_id=project_id,
                operation="SRC-02",
                resource_id=str(row.id),
                edition_id=str(row.standard_edition_id),
                rights_binding_id=str(row.rights_binding_id),
                rights_version=row.rights_binding_version,
                rights_digest=row.rights_digest,
                purpose=row.request_purpose,
                provider_id=row.source_provider_id,
                source_location=row.source_location,
                integrity_digest=row.snapshot_digest,
            )
        except OpaqueAuthorizedHandleInvalid as error:
            raise StandardsError("PROTECTED_NOT_FOUND", 404) from error
        if row.object_key:
            receipt = self.objects.head_exact(row.object_key, row.object_version) if self.objects else None
            if receipt is None or receipt.sha256 != row.content_sha256 or receipt.byte_size != row.byte_count: raise StandardsError("INTEGRITY_FAILURE", 409)
            content = self.objects.open_exact(row.object_key, row.object_version).read(8193)
        else:
            sealed = self.repository.resolve_provider_handle(row.id, organization_id, actor_id, "display")
            if sealed is None: raise StandardsError("PROTECTED_NOT_FOUND", 404)
            token = open_provider_token(sealed, provider_id=row.source_provider_id, organization_id=str(organization_id), project_id=project_id)
            provider = self.providers.get(row.source_provider_id)
            if provider is None: raise StandardsError("CONTENT_UNAVAILABLE", 503)
            fragment = provider.retrieve(location=row.source_location, purpose="material_support", provider_token=token)
            if fragment.version_digest != row.provider_version_digest or fragment.content is None: raise StandardsError("INTEGRITY_FAILURE", 409)
            content = fragment.content
        if not 1 <= len(content) <= 8192: raise StandardsError("INTEGRITY_FAILURE", 409)
        return {"snapshot_id": str(row.id), "edition_id": str(row.standard_edition_id), "source_location": row.source_location,
                "content": content.decode("utf-8", errors="strict"), "content_sha256": row.content_sha256, "snapshot_digest": row.snapshot_digest}

    def create_assertion(self, *, actor_id: int, organization_id: UUID, project_id: int, data: AssertionCreate, idempotency_key: str) -> tuple[int, dict]:
        snapshot = self.repository.snapshot(data.snapshot_id, organization_id, project_id)
        if snapshot is None or snapshot.availability_status != "available" or not snapshot.integrity_verified or snapshot.request_purpose != "material_support": raise StandardsError("PROTECTED_NOT_FOUND", 404)
        if data.source_location != snapshot.source_location:
            raise StandardsError("SOURCE_INCOMPLETE", 409)
        rights = self._current_rights(organization_id=organization_id, edition_id=snapshot.standard_edition_id, provider_id=snapshot.source_provider_id, capability="derived_retention", lock=True)
        if rights.version != snapshot.rights_binding_version or rights.rights_digest != snapshot.rights_digest: raise StandardsError("STALE_ASSERTION", 409)
        record, _ = self._reserve(organization_id=organization_id, actor_id=actor_id, operation="AST-01", key=idempotency_key, fingerprint={"project_id": project_id, **data.model_dump(mode="json")})
        if record.state == "completed": return record.response_status, record.response_body
        digest = canonical_digest({"snapshot": snapshot.snapshot_digest, "location": data.source_location, "kind": data.assertion_kind, "representation": data.canonical_representation})
        row = StandardKnowledgeAssertion(organization_id=organization_id, project_id=project_id, standard_edition_id=snapshot.standard_edition_id, source_snapshot_id=snapshot.id,
            source_location=data.source_location, source_content_digest=snapshot.content_sha256 or snapshot.provider_version_digest, assertion_kind=data.assertion_kind,
            canonical_representation=data.canonical_representation, assertion_origin=data.origin, extraction_method_id="human_bounded_v1" if data.origin == "human" else "deterministic_bounded_v1",
            extraction_method_version="1", extraction_method_digest=canonical_digest({"origin": data.origin, "version": 1}), assertion_digest=digest,
            verification_status="unverified", rights_binding_id=rights.id, rights_binding_version=rights.version, rights_digest=rights.rights_digest,
            retained_derived_use_eligible=False, evaluated_rights_revision=rights.version, version=1, created_by=actor_id)
        self.session.add(row); self.session.flush(); self._stage_event(actor_id=actor_id, organization_id=organization_id, aggregate_type="standard_knowledge_assertion", aggregate_id=row.id, event_id="standards.assertion.created", details={"digest": digest, "version": 1})
        body = self._assertion_payload(row, actor_id=actor_id, provider_id=snapshot.source_provider_id)
        self._complete(record, resource_type="standard_knowledge_assertion", resource_id=row.id, status=201, body=body); self.session.commit(); return 201, body

    def decide_assertion(self, *, actor_id: int, organization_id: UUID, project_id: int, assertion_id: UUID,
                         data: AssertionVerification | AssertionRejection, approved: bool,
                         authorized_handle: str, idempotency_key: str) -> tuple[int, dict]:
        row = self.repository.assertion(assertion_id, organization_id, project_id, lock=True)
        if row is None: raise StandardsError("PROTECTED_NOT_FOUND", 404)
        snapshot = self.repository.snapshot(row.source_snapshot_id, organization_id, project_id)
        if snapshot is None or row.version != data.expected_version: raise StandardsError("VERSION_CONFLICT")
        capability = "derived_current_use" if approved else "derived_retention"
        rights = self._current_rights(organization_id=organization_id, edition_id=row.standard_edition_id, provider_id=snapshot.source_provider_id, capability=capability, lock=True)
        if approved and (not self.evaluate_capability(rights, "excerpt_display") or rights.version != row.rights_binding_version or rights.rights_digest != row.rights_digest): raise StandardsError("STALE_ASSERTION", 409)
        operation = "AST-02" if approved else "AST-03"
        try:
            verify_handle(
                authorized_handle,
                actor_id=actor_id,
                organization_id=str(organization_id),
                project_id=project_id,
                operation=operation,
                resource_id=str(row.id),
                edition_id=str(row.standard_edition_id),
                rights_binding_id=str(row.rights_binding_id),
                rights_version=row.rights_binding_version,
                rights_digest=row.rights_digest,
                purpose="assertion_decision",
                provider_id=snapshot.source_provider_id,
                source_location=row.source_location,
                integrity_digest=row.source_content_digest,
            )
        except OpaqueAuthorizedHandleInvalid as error:
            raise StandardsError("PROTECTED_NOT_FOUND", 404) from error
        record, _ = self._reserve(organization_id=organization_id, actor_id=actor_id, operation=operation, key=idempotency_key, fingerprint={"project_id": project_id, "assertion_id": assertion_id, "approved": approved, **data.model_dump(mode="json")})
        if record.state == "completed": return record.response_status, record.response_body
        status = "human_verified" if approved else "rejected"
        event = StandardAssertionVerificationEvent(assertion_id=row.id, event_kind="verification_decision", status=status, reason=data.reason,
            source_rights_binding_id=rights.id, source_rights_binding_version=rights.version, source_rights_digest=rights.rights_digest,
            assertion_digest=row.assertion_digest, actor_kind="human", verified_by=actor_id)
        self.session.add(event); self.session.flush()
        row.current_verification_event_id, row.verification_status, row.retained_derived_use_eligible, row.evaluated_rights_revision, row.version = event.id, status, approved, rights.version, row.version + 1
        event_id = "standards.assertion.human_verified" if approved else "standards.assertion.rejected"
        self._stage_event(actor_id=actor_id, organization_id=organization_id, aggregate_type="standard_knowledge_assertion", aggregate_id=row.id, event_id=event_id, details={"digest": row.assertion_digest, "version": row.version})
        body = self._assertion_payload(row, actor_id=actor_id, provider_id=snapshot.source_provider_id)
        self._complete(record, resource_type="standard_knowledge_assertion", resource_id=row.id, status=201, body=body); self.session.commit(); return 201, body

    @staticmethod
    def _intelligence_payload(row: StandardIntelligenceRun) -> dict:
        """Public result is deliberately digest/status based, never source text."""
        return {
            "run_id": str(row.id), "project_id": row.project_id, "request_kind": row.request_kind,
            "deterministic": row.deterministic_result, "deterministic_result_digest": row.deterministic_result_digest,
            "result_status": row.result_status, "phase_status": row.phase_status,
            "advisory": row.advisory_output, "failure_code": row.failure_code,
            "advisory_only": True, "human_authority_required": True,
            "created_at": row.created_at.isoformat() if row.created_at else None,
            "completed_at": row.completed_at.isoformat() if row.completed_at else None,
        }

    def _intelligence_context(self, *, organization_id: UUID, project_id: int, data: StandardsIntelligenceRunCreate, lock: bool = False):
        """Resolve only tenant-scoped canonical records into non-content context."""
        snapshots = []
        for snapshot_id in sorted(data.snapshot_ids, key=str):
            row = self.repository.snapshot(snapshot_id, organization_id, project_id, lock=lock)
            if row is None:
                raise StandardsError("PROTECTED_NOT_FOUND", 404)
            standing = self.repository.current_standing(row.standard_edition_id, lock=lock)
            rights = self.repository.get_current_rights(organization_id, row.standard_edition_id, row.source_provider_id, lock=lock)
            applicability = self.repository.current_applicability(organization_id, project_id, row.standard_edition_id, lock=lock)
            eligible = bool(
                row.availability_status == "available" and row.integrity_verified and standing is not None
                and standing.standing == "current" and applicability is not None
                and applicability.status == "declared_applicable"
                and self.evaluate_capability(rights, "derived_current_use")
            )
            handle = "stdh_" + canonical_digest({"snapshot": str(row.id), "digest": row.snapshot_digest, "rights": row.rights_digest})
            snapshots.append({"snapshot": row, "rights": rights, "eligible": eligible, "handle": handle,
                              "code": "eligible" if eligible else "deterministic_unavailable"})
        assertions = []
        for assertion_id in sorted(data.assertion_ids, key=str):
            assertion = self.repository.assertion(assertion_id, organization_id, project_id, lock=lock)
            if assertion is None or assertion.source_snapshot_id not in {item["snapshot"].id for item in snapshots}:
                raise StandardsError("PROTECTED_NOT_FOUND", 404)
            allowed = assertion.verification_status == "human_verified" and assertion.retained_derived_use_eligible
            assertions.append({"assertion": assertion, "eligible": allowed,
                               "handle": "asrh_" + canonical_digest({"assertion": str(assertion.id), "digest": assertion.assertion_digest}),
                               "code": "human_verified" if allowed else "assertion_ineligible"})
        deterministic = {
            "schema_version": 1,
            "edition_resolution": "pass" if all(item["eligible"] for item in snapshots) else "indeterminate",
            "standing": "pass" if all(item["eligible"] for item in snapshots) else "indeterminate",
            "rights_eligibility": "pass" if all(item["eligible"] for item in snapshots) else "denied",
            "authorization": "pass", "project_applicability": "pass" if all(item["eligible"] for item in snapshots) else "indeterminate",
            "source_availability": "pass" if all(item["eligible"] for item in snapshots) else "unavailable",
            "materiality": "advisory_only", "assertion_eligibility": "pass" if all(item["eligible"] for item in assertions) else "indeterminate",
            "integrity": "pass" if all(item["snapshot"].integrity_verified for item in snapshots) else "failed",
            "conflicts": "none_detected", "bounds": "pass",
        }
        return snapshots, assertions, deterministic

    @staticmethod
    def _rights_manifest(snapshots: list[dict]) -> list[dict]:
        return [{"binding_id": str(item["rights"].id) if item["rights"] else None,
                 "version": item["rights"].version if item["rights"] else None,
                 "digest": item["rights"].rights_digest if item["rights"] else None,
                 "permission": item["rights"].ai_processing_permission if item["rights"] else "prohibited"}
                for item in snapshots]

    def _ai_authorization(self, snapshots: list[dict], assertions: list[dict]) -> tuple[str | None, str | None]:
        if not all(item["eligible"] for item in snapshots + assertions):
            return "unavailable", "INDETERMINATE"
        if self.intelligence_provider is None:
            return "unavailable", "AI_UNAVAILABLE"
        for item in snapshots:
            rights = item["rights"]
            if rights is None or rights.ai_processing_permission == "prohibited":
                return "not_permitted", "AI_USE_NOT_PERMITTED"
            if rights.ai_processing_permission == "local_only":
                if self.intelligence_provider_id != "local":
                    return "not_permitted", "AI_USE_NOT_PERMITTED"
            elif rights.ai_processing_permission == "approved_processor":
                if self.intelligence_processor_policy_id not in (rights.approved_processor_policy_ids or []):
                    return "not_permitted", "AI_USE_NOT_PERMITTED"
            else:
                return "not_permitted", "AI_USE_NOT_PERMITTED"
        return None, None

    def _intelligence_actor_authorized(
        self,
        *,
        actor_id: int,
        organization_id: UUID,
        auth_version: int,
        project_id: int,
        lock: bool,
    ) -> bool:
        """Reload the mutable request authority in the accepted global order."""
        user_query = select(User).where(User.id == actor_id)
        organization_query = select(Organization).where(Organization.id == organization_id)
        membership_query = select(UserOrganizationMembership).where(
            UserOrganizationMembership.user_id == actor_id,
            UserOrganizationMembership.organization_id == organization_id,
        )
        project_query = select(Project).where(
            Project.id == project_id,
            Project.organization_id == organization_id,
        )
        if lock:
            user_query = user_query.with_for_update()
            organization_query = organization_query.with_for_update()
            membership_query = membership_query.with_for_update()
            project_query = project_query.with_for_update()
        user = self.session.scalar(user_query)
        organization = self.session.scalar(organization_query)
        membership = self.session.scalar(membership_query)
        project = self.session.scalar(project_query)
        return bool(
            user is not None
            and organization is not None
            and membership is not None
            and project is not None
            and user.is_active
            and not user.activation_pending
            and user.auth_version == auth_version
            and user.role in {"admin", "engineer"}
            and organization.is_active
            and membership.is_enabled
            and membership.is_selected
            and (
                user.role == "admin"
                or actor_id in {project.owner_id, project.primary_assignee_id}
            )
        )

    def _intelligence_provider_decision_is_current(
        self, run: StandardIntelligenceRun
    ) -> bool:
        """Bind egress to the exact enabled server-side processor decision."""
        return bool(
            self.intelligence_provider is not None
            and run.processor_policy_id == self.intelligence_processor_policy_id
            and run.provider_id == self.intelligence_provider_id
            and run.provider_model == self.intelligence_provider_model
        )

    def run_intelligence(self, *, actor_id: int, organization_id: UUID, auth_version: int = 1, project_id: int, data: StandardsIntelligenceRunCreate, idempotency_key: str, correlation_id: UUID | None = None) -> tuple[int, dict]:
        """INT-01: deterministic-first, three-phase, one-dispatch workflow."""
        if not self._intelligence_actor_authorized(
            actor_id=actor_id,
            organization_id=organization_id,
            auth_version=auth_version,
            project_id=project_id,
            lock=True,
        ):
            raise StandardsError("PROTECTED_NOT_FOUND", 404)
        record, request_digest = self._reserve(organization_id=organization_id, actor_id=actor_id, operation="INT-01", key=idempotency_key, fingerprint={"project_id": project_id, **data.model_dump(mode="json")})
        if record.state == "completed":
            return record.response_status, record.response_body
        snapshots, assertions, deterministic = self._intelligence_context(organization_id=organization_id, project_id=project_id, data=data)
        handles = tuple(item["handle"] for item in snapshots + assertions)
        codes = tuple(sorted({item["code"] for item in snapshots + assertions} | {"deterministic_unavailable", "human_verified"}))
        try:
            envelope = compose_envelope(handles=handles, rationale_codes=codes, purpose=data.purpose)
        except ValueError as error:
            raise StandardsError(str(error), 422) from error
        now = datetime.now(timezone.utc)
        run = StandardIntelligenceRun(
            organization_id=organization_id, project_id=project_id, request_kind="human_requested_advisory", purpose=data.purpose,
            correlation_id=correlation_id or uuid4(), request_digest=request_digest, deterministic_result=deterministic,
            deterministic_result_digest=canonical_digest(deterministic), template_id=TEMPLATE_ID, template_version=TEMPLATE_VERSION,
            template_digest=TEMPLATE_DIGEST, processor_policy_id=self.intelligence_processor_policy_id, provider_id=self.intelligence_provider_id,
            provider_model=self.intelligence_provider_model,
            rights_manifest=self._rights_manifest(snapshots),
            authorized_handle_digest=canonical_digest(handles), input_digest=hashlib.sha256(envelope).hexdigest(), input_byte_count=len(envelope),
            created_by=actor_id, deadline_at=now + timedelta(seconds=30),
        )
        self.session.add(run); self.session.flush()
        self._stage_event(actor_id=actor_id, organization_id=organization_id, aggregate_type="standard_intelligence_run", aggregate_id=run.id, event_id="standards.intelligence.requested", details={"digest": run.deterministic_result_digest, "version": run.version})
        # Intent and idempotency record are durable before any possible egress.
        self.session.commit()
        run_id = run.id
        if self.before_intelligence_dispatch is not None:
            self.before_intelligence_dispatch()

        # Phase 2: a fresh transaction and locked canonical state immediately
        # before CAS. No lock survives the commit preceding provider I/O.
        self.session.expire_all()
        authority_denied = not self._intelligence_actor_authorized(
            actor_id=actor_id,
            organization_id=organization_id,
            auth_version=auth_version,
            project_id=project_id,
            lock=True,
        )
        fresh_snapshots, fresh_assertions, _ = self._intelligence_context(organization_id=organization_id, project_id=project_id, data=data, lock=True)
        fresh_handles = tuple(item["handle"] for item in fresh_snapshots + fresh_assertions)
        run = self.repository.intelligence_run(run_id, organization_id, project_id, lock=True)
        if run is None or run.phase_status != "requested" or run.call_count != 0 or run.version != 1:
            self.session.rollback(); raise StandardsError("VERSION_CONFLICT")
        denial_status, failure = self._ai_authorization(fresh_snapshots, fresh_assertions)
        if authority_denied or not self._intelligence_provider_decision_is_current(run):
            denial_status, failure = "not_permitted", "AI_USE_NOT_PERMITTED"
        if self._rights_manifest(fresh_snapshots) != run.rights_manifest or canonical_digest(fresh_handles) != run.authorized_handle_digest:
            denial_status, failure = "not_permitted", "AI_USE_NOT_PERMITTED"
        if run.deadline_at <= datetime.now(timezone.utc):
            denial_status, failure = "unavailable", "AI_UNAVAILABLE"
        if denial_status is not None:
            run.phase_status, run.result_status, run.failure_code = "terminal", denial_status, failure
            run.completed_at, run.version = datetime.now(timezone.utc), run.version + 1
            self._stage_event(actor_id=actor_id, organization_id=organization_id, aggregate_type="standard_intelligence_run", aggregate_id=run.id, event_id="standards.intelligence.unavailable", details={"digest": run.deterministic_result_digest, "version": run.version})
            body = self._intelligence_payload(run)
            self._complete(record, resource_type="standard_intelligence_run", resource_id=run.id, status=200, body=body)
            self.session.commit()
            if authority_denied:
                raise StandardsError("PROTECTED_NOT_FOUND", 404)
            return 200, body
        dispatched_at = datetime.now(timezone.utc)
        run.phase_status, run.call_count, run.dispatched_at, run.version = "dispatched", 1, dispatched_at, run.version + 1
        self.session.commit()

        raw = None; failure = None
        try:
            raw = self.intelligence_provider.advise(envelope, timeout_seconds=30.0)
            if not isinstance(raw, (bytes, bytearray)): failure = "AI_UNAVAILABLE"
        except TimeoutError: failure = "AI_UNAVAILABLE"
        except Exception: failure = "AI_UNAVAILABLE"

        # Phase 3: fresh locked authorization. Any policy/context change causes
        # provider output to be discarded and never disclosed.
        self.session.expire_all()
        authority_denied = not self._intelligence_actor_authorized(
            actor_id=actor_id,
            organization_id=organization_id,
            auth_version=auth_version,
            project_id=project_id,
            lock=True,
        )
        final_snapshots, final_assertions, _ = self._intelligence_context(organization_id=organization_id, project_id=project_id, data=data, lock=True)
        final_handles = tuple(item["handle"] for item in final_snapshots + final_assertions)
        run = self.repository.intelligence_run(run_id, organization_id, project_id, lock=True)
        if run is None or run.phase_status != "dispatched" or run.call_count != 1 or run.version != 2:
            self.session.rollback(); raise StandardsError("VERSION_CONFLICT")
        denial_status, denial_code = self._ai_authorization(final_snapshots, final_assertions)
        if authority_denied or not self._intelligence_provider_decision_is_current(run):
            denial_status, denial_code = "not_permitted", "AI_USE_NOT_PERMITTED"
        if self._rights_manifest(final_snapshots) != run.rights_manifest or canonical_digest(final_handles) != run.authorized_handle_digest:
            denial_status, denial_code = "not_permitted", "AI_USE_NOT_PERMITTED"
        if denial_status is not None:
            raw, failure = None, denial_code
            run.result_status = denial_status
        elif failure is not None:
            run.result_status = "unavailable"
        else:
            try:
                advisory = validate_output(bytes(raw), known_handles=set(handles), known_codes=set(codes))
                suggestions = list(advisory.suggestions)
                run.advisory_output = {"suggestions": suggestions, "advisory_only": True, "human_authority_required": True}
                run.output_digest, run.suggestion_handle_digest = advisory.output_digest, canonical_digest(tuple(item["handle"] for item in suggestions))
                run.result_status = "completed_with_suggestions" if suggestions else "completed_no_suggestions"
            except ValueError:
                failure, run.result_status = "INVALID_AI_OUTPUT", "invalid_output"
        run.phase_status, run.failure_code, run.completed_at, run.version = "terminal", failure, datetime.now(timezone.utc), run.version + 1
        event = "standards.intelligence.completed" if run.result_status.startswith("completed_") else "standards.intelligence.unavailable"
        self._stage_event(actor_id=actor_id, organization_id=organization_id, aggregate_type="standard_intelligence_run", aggregate_id=run.id, event_id=event, details={"digest": run.output_digest or run.deterministic_result_digest, "version": run.version})
        body = self._intelligence_payload(run)
        self._complete(record, resource_type="standard_intelligence_run", resource_id=run.id, status=200, body=body)
        self.session.commit()
        if authority_denied:
            raise StandardsError("PROTECTED_NOT_FOUND", 404)
        return 200, body

    def get_intelligence_run(self, *, actor_id: int, organization_id: UUID, auth_version: int = 1, project_id: int, run_id: UUID) -> dict:
        if not self._intelligence_actor_authorized(
            actor_id=actor_id,
            organization_id=organization_id,
            auth_version=auth_version,
            project_id=project_id,
            lock=False,
        ):
            raise StandardsError("PROTECTED_NOT_FOUND", 404)
        row = self.repository.intelligence_run(run_id, organization_id, project_id)
        if row is None: raise StandardsError("PROTECTED_NOT_FOUND", 404)
        return self._intelligence_payload(row)

    @staticmethod
    def evaluate_capability(row: OrganizationRightsBinding | None, capability: str, now: datetime | None = None) -> bool:
        """Fail closed for all unknown, expired, revoked, malformed and inactive states."""
        if row is None or not row.is_current: return False
        now = now or datetime.now(timezone.utc)
        if row.rights_basis == "unknown" or row.rights_status != "active": return False
        if row.rights_basis == "metadata_only" and capability != "metadata_visibility": return False
        if row.effective_from > now or (row.effective_until is not None and row.effective_until <= now): return False
        mapping = {"metadata_visibility": row.allow_metadata_visibility, "content_storage": row.allow_content_storage, "indexing": row.allow_indexing, "excerpt_display": row.allow_excerpt_display, "source_retrieval": row.allow_source_retrieval, "derived_retention": row.allow_derived_retention, "derived_current_use": row.allow_derived_current_use}
        return mapping.get(capability, False)
